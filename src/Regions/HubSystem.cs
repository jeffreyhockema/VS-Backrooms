using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Map;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;

namespace Backrooms.Regions;

/// <summary>
/// The Hub's rules (docs/design/new-levels/hub-plan.md):
/// <list type="bullet">
/// <item><b>Level Keys</b> (<c>backrooms:hub-key-&lt;tag&gt;</c>): each found only in its own level, in a cache broken open
/// there, likelier in a den, behind a forced door and in the level's worst places. In the Hub a key opens its level's
/// carved door once and is used up (<see cref="ThresholdSystem.UseHubDoor"/>).</item>
/// <item><b>Resonance</b>: in the Hub, a key held in the hand rings every few seconds, from the direction of its door,
/// louder as you near it; close by, it rings from the door itself, you are told so, and the door goes on your map.</item>
/// <item><b>A door that wasn't there</b>: now and then, far from home, a grey door with the Hub's sigil over it stands in a
/// wall near someone who is not looking. It leads one way into the Hub, and after a few minutes it is gone.</item>
/// </list>
/// </summary>
public partial class HubSystem : ModSystem
{
    private const string KeyPrefix = "hub-key-";
    /// <summary>The code of the Tower's ornate doors up the stair and round the hall, which never open.</summary>
    public const string ForbiddenDoorPrefix = "hub-ornatedoor-forbidden-";
    private const string ManifestSaveKey = "backrooms-hub-manifest";
    private const int ResonanceEveryMs = 4000, ManifestCheckMs = 60_000, ManifestLastsMs = 5 * 60_000;
    /// <summary>The chance a player far from home meets a door that wasn't there, per minute: about once in ten in-game days.</summary>
    private const double ManifestChancePerMinute = 1 / 480.0;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private readonly HashSet<int> caches = new();
    private readonly Dictionary<string, long> nextChime = new();
    /// <summary>Players who have been told their key rings close by (until they are well away from its door again).</summary>
    private readonly HashSet<string> keyNear = new();
    /// <summary>The tick listeners this system (and its Tower half) registered, taken off again in <see cref="Dispose"/>.</summary>
    private readonly List<long> ticks = new();
    /// <summary>The doors that weren't there: their lower block's position, when they go, and the blocks they stand in for.</summary>
    private readonly List<Manifested> manifested = new();

    private sealed class Manifested
    {
        public int X, Y, Z;
        public long Until;
        public int[] Was = new int[3];
    }

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsHubDoor", typeof(BlockBehaviorHubDoor));
        api.RegisterBlockBehaviorClass("BackroomsHubRegister", typeof(BlockBehaviorHubRegister));
        api.RegisterEntity("BackroomsKeymaster", typeof(EntityKeymaster));
    }

    /// <summary>
    /// The carved doors need to know who uses them: whatever plain threshold behaviour their blocktypes carry is swapped
    /// for <see cref="BlockBehaviorHubDoor"/> (on both sides, since block behaviours added now are not sent to clients).
    /// The Tower's doors (its ten ways in and its forbidden ones) are swapped the same way; the door register and Camp
    /// Amber's sign are given a way to be read.
    /// </summary>
    public override void AssetsFinalize(ICoreAPI api)
    {
        // The Keymaster is our own kind of entity: he cannot be hurt, and asking him for a key is ours to answer
        foreach (EntityProperties type in api.World.EntityTypes)
            if (type?.Code?.Domain == "backrooms" && type.Code.Path == "hub-keymaster") type.Class = "BackroomsKeymaster";
        foreach (Block block in api.World.Blocks)
        {
            string path = block?.Code?.Path;
            if (block?.Code?.Domain != "backrooms" || path == null) continue;
            // The door register: reading it marks the Hub's known doors on your map
            if (path.StartsWith("hub-whiteboard-") && !block.HasBehavior<BlockBehaviorHubRegister>())
            {
                block.BlockBehaviors = (block.BlockBehaviors ?? Array.Empty<BlockBehavior>()).Append(new BlockBehaviorHubRegister(block)).ToArray();
                continue;
            }
            // Camp Amber's painted board: reading it
            if (path.StartsWith("hub-ambersign-") && !block.HasBehavior<BlockBehaviorHubSign>())
            {
                block.BlockBehaviors = (block.BlockBehaviors ?? Array.Empty<BlockBehavior>()).Append(new BlockBehaviorHubSign(block)).ToArray();
                continue;
            }
            // (The Tower's forbidden doors too, so that they can say they are forbidden: UseHubDoor refuses them by their code)
            if (!(path.StartsWith("hub-door-") || path.StartsWith("hub-pinkdoor-") || path.StartsWith("hub-ornatedoor-entrance-")
                  || path.StartsWith(ForbiddenDoorPrefix))) continue;
            if (block.HasBehavior<BlockBehaviorHubDoor>()) continue;
            var door = new BlockBehaviorHubDoor(block);
            bool swapped = false;
            BlockBehavior[] behaviors = block.BlockBehaviors ?? Array.Empty<BlockBehavior>();
            for (int i = 0; i < behaviors.Length; i++)
                if (behaviors[i] is BlockBehaviorThreshold) { behaviors[i] = door; swapped = true; }
            block.BlockBehaviors = swapped ? behaviors : behaviors.Append(door).ToArray();
            CollectibleBehavior[] collectible = block.CollectibleBehaviors ?? Array.Empty<CollectibleBehavior>();
            bool inCollectible = false;
            for (int i = 0; i < collectible.Length; i++)
                if (collectible[i] is BlockBehaviorThreshold) { collectible[i] = door; inCollectible = true; }
            if (inCollectible) block.CollectibleBehaviors = collectible;
        }
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        // (Static: the doors of the last world loaded in this process must not stand in this one)
        ThresholdNetwork.ManifestDoors.Clear();
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            foreach (Block block in api.World.Blocks)
                if (block?.Code?.Domain == "backrooms" && block.Drops != null && Array.Exists(block.Drops, IsLoot)) caches.Add(block.BlockId);
            api.Event.DidBreakBlock += OnBrokeBlock;
            ticks.Add(api.Event.RegisterGameTickListener(OnResonance, 500));
            ticks.Add(api.Event.RegisterGameTickListener(OnManifestTick, 5000, 3000));
            RestoreLeftovers();
            api.Event.GameWorldSave += SaveManifested;
            StartTower(api);
        });
    }

    public override void Dispose()
    {
        if (sapi == null || layout == null) return;
        foreach (long id in ticks) sapi.Event.UnregisterGameTickListener(id);
        ticks.Clear();
        sapi.Event.DidBreakBlock -= OnBrokeBlock;
        sapi.Event.GameWorldSave -= SaveManifested;
        StopTower(sapi);
    }

    // ================= Keys =================

    /// <summary>The tag of a level's key (<c>hub-key-l5</c>, <c>hub-key-run</c>), or null if its door needs none (or it has no door).</summary>
    public static string KeyTag(int level) => level switch
    {
        0 or (>= 2 and <= 10) => "l" + level,
        WorldLayout.Poolrooms => "l37",
        WorldLayout.Motion => "l94",
        WorldLayout.RunLevel => "run",
        WorldLayout.FunLevel => "fun",
        WorldLayout.TheEnd => "end",
        WorldLayout.Level3999 => "l3999",
        _ => null,
    };

    /// <summary>
    /// Each Level Key's item code path (<c>hub-key-l5</c>) to its level. (Made on first use: <see cref="KeyedLevels"/> is
    /// in the other half of this partial class, and the order of static initialisers across files is not defined.)
    /// </summary>
    private static Dictionary<string, int> keyPaths;

    /// <summary>The level a key belongs to, by its item code, or -1 if it is not a Level Key. (Asked of every slot a player has.)</summary>
    public static int KeyLevel(ItemStack stack)
    {
        AssetLocation code = stack?.Collectible?.Code;
        if (code == null || code.Domain != "backrooms" || !code.Path.StartsWith(KeyPrefix)) return -1;
        keyPaths ??= KeyedLevels.ToDictionary(l => KeyPrefix + KeyTag(l));
        return keyPaths.TryGetValue(code.Path, out int level) ? level : -1;
    }

    /// <summary>The slot holding a player's key to a level (the one in their hand first), or null. A level of -1 finds any Level Key.</summary>
    public static ItemSlot FindKey(IPlayer player, int level)
    {
        if (player.InventoryManager == null) return null;
        ItemSlot held = player.InventoryManager.ActiveHotbarSlot;
        if (IsKeyTo(held?.Itemstack, level)) return held;
        foreach (IInventory inventory in player.InventoryManager.Inventories.Values)
        {
            if (inventory == null || inventory.ClassName is "creative" or "ground") continue;
            foreach (ItemSlot slot in inventory)
                if (IsKeyTo(slot?.Itemstack, level)) return slot;
        }
        return null;
    }

    private static bool IsKeyTo(ItemStack stack, int level)
    {
        int of = KeyLevel(stack);
        return of >= 0 && (level < 0 || of == level);
    }

    /// <summary>Whether someone carries something cute (the pink door to Level 974 opens only for them): Level 974's own test.</summary>
    public static bool CarriesSomethingCute(IPlayer player) => L974.CarriesCute(player);

    private static bool IsLoot(BlockDropItemStack drop)
    {
        AssetLocation code = drop?.Code;
        if (code == null) return false;
        string p = code.Path;
        if (code.Domain == "backrooms") return p is "almondwater" or "crackers" or "cannedbeans" or "chips" or "candybar" or "soda" or "waterbottle";
        return p.StartsWith("fruit-") || p.StartsWith("cheese-") || p.StartsWith("bandage");
    }

    /// <summary>
    /// A cache broken open in a level may hold that level's key: one in twenty-five at the heart of a den, one in seventy
    /// behind a door nobody had opened, one in twelve in the level's worst places, and otherwise very rarely.
    /// </summary>
    private void OnBrokeBlock(IServerPlayer byPlayer, int oldblockId, BlockSelection blockSel)
    {
        OnTowerBreak(byPlayer, blockSel.Position);
        if (byPlayer?.WorldData.CurrentGameMode != EnumGameMode.Survival || !caches.Contains(oldblockId) || layout == null) return;
        BlockPos pos = blockSel.Position;
        int mx = WorldLayout.MacroOf(pos.X), mz = WorldLayout.MacroOf(pos.Z);
        int level = layout.LevelAt(mx, mz);
        if (level == 6 && layout.IsSnackrooms(mx, mz)) return;
        string tag = KeyTag(level);
        if (tag == null || level is WorldLayout.RunLevel or WorldLayout.FunLevel or WorldLayout.TheEnd) return; // (those levels place their own)
        Tile tile = layout.TileAt(pos.X, pos.Z);
        double chance = WorstPlace(level, pos) ? 0.08 : layout.DenAt(mx, mz) != DenKind.None ? 0.04 : tile.Sealed ? 0.015 : 0.002;
        if (sapi.World.Rand.NextDouble() >= chance) return;
        Item key = sapi.World.GetItem(new AssetLocation("backrooms:" + KeyPrefix + tag));
        if (key == null) return;
        KeyTurnedUp(sapi.World, byPlayer, new ItemStack(key), pos);
        sapi.Logger.Notification("[backrooms] a Level Key ({0}) turned up at {1}", tag, pos);
    }

    /// <summary>
    /// A Level Key turns up in something broken open (a cache here, The End's desks and catalogues, Level Fun's gifts):
    /// it is dropped there, and whoever broke it open is told it hums.
    /// </summary>
    public static void KeyTurnedUp(IWorldAccessor world, IPlayer byPlayer, ItemStack key, BlockPos pos)
    {
        world.SpawnItemEntity(key, pos.ToVec3d().Add(0.5, 0.5, 0.5));
        (byPlayer as IServerPlayer)?.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:hub-key-found"), EnumChatType.Notification);
    }

    /// <summary>Where a level hides its key best: its most dangerous places.</summary>
    private bool WorstPlace(int level, BlockPos pos)
    {
        int mx = WorldLayout.MacroOf(pos.X), mz = WorldLayout.MacroOf(pos.Z);
        return level switch
        {
            0 => layout.IsRedRoom(mx, mz),
            3 => layout.IsSanctum(mx, mz) || pos.Y < geometry.FloorFor(3),
            WorldLayout.Poolrooms => layout.IsReservoirAt(pos.X, pos.Z),
            WorldLayout.Motion => layout.InCastle(pos.X, pos.Z),
            _ => false,
        };
    }

    // ================= Resonance =================

    private void OnResonance(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } entity } player) continue;
            int level = KeyLevel(player.InventoryManager.ActiveHotbarSlot?.Itemstack);
            if (level < 0) continue;
            if (layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z))) != WorldLayout.Hub) continue;
            if (layout.HubDoorOf(level) is not { } door) continue;
            double dx = door.X + 0.5 - entity.Pos.X, dz = door.Z + 0.5 - entity.Pos.Z, d = Math.Sqrt(dx * dx + dz * dz);
            bool close = d < 8;
            // (Told once each time they come close: not again until they have been twice as far off)
            if (!close && d > 16) keyNear.Remove(player.PlayerUID);
            if (nextChime.TryGetValue(player.PlayerUID, out long next) && now < next) continue;
            nextChime[player.PlayerUID] = now + (close ? ResonanceEveryMs / 2 : ResonanceEveryMs);
            double y = entity.Pos.Y + 1.2;
            var chime = new AssetLocation("backrooms:sounds/effect/hub/keychime");
            if (close)
            {
                if (keyNear.Add(player.PlayerUID))
                    player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:hub-key-near"), EnumChatType.Notification);
                sapi.World.PlaySoundAt(chime, door.X + 0.5, geometry.FloorFor(WorldLayout.Hub) + 2.5, door.Z + 0.5, null, false, 24, 1f);
                MapMarks.Add(sapi, player, new Vec3d(door.X + 0.5, geometry.FloorFor(WorldLayout.Hub) + 1.5, door.Z + 0.5),
                    Lang.Get("backrooms:waypoint-hubdoor", LevelName(level)), "spiral", MapMarks.WayColor, 6);
                continue;
            }
            // From its door's direction, louder the nearer
            float volume = (float)(0.3 + 0.7 * Math.Clamp(1 - d / 1500, 0, 1));
            sapi.World.PlaySoundAt(chime, entity.Pos.X + dx / d * 6, y, entity.Pos.Z + dz / d * 6, null, false, 16, volume);
        }
    }

    /// <summary>A level's name as the waypoints and messages give it.</summary>
    public static string LevelName(int level) => level switch
    {
        WorldLayout.HubSnackroomsDoor => Lang.Get("backrooms:levelname-6.1"),
        >= WorldLayout.RunLevel and <= WorldLayout.Level188 => Lang.Get("backrooms:levelname-" + level),
        _ => Lang.Get("backrooms:levelname", WorldLayout.DisplayNumber(level)),
    };

    // ================= A door that wasn't there =================

    private long lastManifestCheck;

    private void OnManifestTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        // The doors that have stood their time go
        for (int i = manifested.Count - 1; i >= 0; i--)
        {
            if (now < manifested[i].Until) continue;
            // It leads nowhere from now on; but blocks can only be put back while their chunk is loaded (SetBlock does
            // nothing otherwise), so a door whose chunk is not waits until it is
            ThresholdNetwork.ManifestDoors.TryRemove((manifested[i].X, manifested[i].Z), out _);
            if (sapi.World.BlockAccessor.GetChunkAtBlockPos(new BlockPos(manifested[i].X, manifested[i].Y, manifested[i].Z)) == null) continue;
            Remove(manifested[i]);
            manifested.RemoveAt(i);
        }
        if (now - lastManifestCheck < ManifestCheckMs) return;
        lastManifestCheck = now;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { Alive: true } } player || player.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
            if (sapi.World.Rand.NextDouble() >= ManifestChancePerMinute) continue;
            TryManifest(player);
        }
    }

    /// <summary>
    /// Puts a door that wasn't there in a wall 10-24 blocks from a player, somewhere they are not looking: never in the Hub,
    /// never within 48 blocks of where they wake, never in a sanctuary. Returns whether one was put down.
    /// </summary>
    public bool TryManifest(IServerPlayer player, bool force = false)
    {
        if (layout == null || player.Entity == null) return false;
        EntityPosLike pos = new(player.Entity.Pos.X, player.Entity.Pos.Y, player.Entity.Pos.Z);
        int px = (int)Math.Floor(pos.X), pz = (int)Math.Floor(pos.Z), y = (int)Math.Floor(pos.Y + 0.05);
        int level = layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz));
        if (level == WorldLayout.Hub || !force && layout.IsSanctuary(px, pz, level)) return false;
        if (!force && player.GetSpawnPosition(false) is { } home && Math.Abs(home.X - pos.X) + Math.Abs(home.Z - pos.Z) < 48) return false;
        // Somewhere behind them
        Vec3f view = player.Entity.Pos.GetViewVector();
        double lookLength = Math.Max(1e-6, Math.Sqrt(view.X * view.X + view.Z * view.Z));
        double lookX = view.X / lookLength, lookZ = view.Z / lookLength;
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        Random rand = sapi.World.Rand;
        for (int attempt = 0; attempt < 400; attempt++)
        {
            int x = px + rand.Next(-24, 25), z = pz + rand.Next(-24, 25);
            double dx = x + 0.5 - pos.X, dz = z + 0.5 - pos.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d < 10 || d > 24 || (dx * lookX + dz * lookZ) / d > -0.2) continue;
            foreach (BlockFacing face in BlockFacing.HORIZONTALS)
            {
                // A solid wall three high, open floor in front of it
                if (!Solid(blocks, x, y, z) || !Solid(blocks, x, y + 1, z) || !Solid(blocks, x, y + 2, z)) continue;
                int fx = x + face.Normali.X, fz = z + face.Normali.Z;
                if (!Air(blocks, fx, y, fz) || !Air(blocks, fx, y + 1, fz) || !Solid(blocks, fx, y - 1, fz)) continue;
                if (!Solid(blocks, x - face.Normali.Z, y, z + face.Normali.X) && !Solid(blocks, x + face.Normali.Z, y, z - face.Normali.X)) continue;
                return Place(x, y, z, face);
            }
        }
        return false;
    }

    private readonly record struct EntityPosLike(double X, double Y, double Z);

    private static bool Solid(IBlockAccessor blocks, int x, int y, int z)
    {
        Block b = blocks.GetBlock(new BlockPos(x, y, z));
        return b.BlockId != 0 && b.SideSolid.All && b.Replaceable < 5000 && !b.HasBehavior<BlockBehaviorThreshold>();
    }

    private static bool Air(IBlockAccessor blocks, int x, int y, int z) => blocks.GetBlock(new BlockPos(x, y, z)).Replaceable >= 5000 || blocks.GetBlock(new BlockPos(x, y, z)).BlockId == 0;

    private bool Place(int x, int y, int z, BlockFacing face)
    {
        string side = face.Code;
        Block lower = sapi.World.GetBlock(new AssetLocation("backrooms:hub-servicedoor-lower-" + side));
        Block upper = sapi.World.GetBlock(new AssetLocation("backrooms:hub-servicedoor-upper-" + side));
        Block sigil = sapi.World.GetBlock(new AssetLocation("backrooms:hub-sigil-0-" + side));
        if (lower == null || upper == null) return false;
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        var door = new Manifested { X = x, Y = y, Z = z, Until = sapi.World.ElapsedMilliseconds + ManifestLastsMs };
        for (int i = 0; i < 3; i++) door.Was[i] = blocks.GetBlock(new BlockPos(x, y + i, z)).BlockId;
        blocks.SetBlock(lower.BlockId, new BlockPos(x, y, z));
        blocks.SetBlock(upper.BlockId, new BlockPos(x, y + 1, z));
        if (sigil != null) blocks.SetBlock(sigil.BlockId, new BlockPos(x, y + 2, z));
        manifested.Add(door);
        ThresholdNetwork.ManifestDoors[(x, z)] = true;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/hub/manifest"), x + 0.5, y + 1, z + 0.5, null, false, 24, 0.8f);
        sapi.Logger.Notification("[backrooms] a door that wasn't there stands at {0},{1},{2}", x, y, z);
        return true;
    }

    private void Remove(Manifested door)
    {
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        for (int i = 0; i < 3; i++) blocks.SetBlock(door.Was[i], new BlockPos(door.X, door.Y + i, door.Z));
        ThresholdNetwork.ManifestDoors.TryRemove((door.X, door.Z), out _);
    }

    /// <summary>Doors left standing when the server last stopped go at once (what they stood in for comes back).</summary>
    private void RestoreLeftovers()
    {
        byte[] data = sapi.WorldManager.SaveGame.GetData(ManifestSaveKey);
        if (data == null || data.Length == 0) return;
        try
        {
            int[] values = SerializerUtil.Deserialize<int[]>(data);
            for (int i = 0; i + 5 < values.Length; i += 6)
            {
                // (Taken away by the tick once its chunk is loaded: now it almost never is)
                manifested.Add(new Manifested { X = values[i], Y = values[i + 1], Z = values[i + 2], Until = 0, Was = new[] { values[i + 3], values[i + 4], values[i + 5] } });
            }
        }
        catch (Exception e) { sapi.Logger.Warning("[backrooms] could not read the Hub's leftover doors: {0}", e.Message); }
        sapi.WorldManager.SaveGame.StoreData(ManifestSaveKey, Array.Empty<byte>());
    }

    private void SaveManifested()
    {
        var values = new List<int>();
        foreach (Manifested door in manifested) values.AddRange(new[] { door.X, door.Y, door.Z, door.Was[0], door.Was[1], door.Was[2] });
        sapi.WorldManager.SaveGame.StoreData(ManifestSaveKey, SerializerUtil.Serialize(values.ToArray()));
    }
}

/// <summary>
/// A carved door of the Hub's: using it asks <see cref="ThresholdSystem.UseHubDoor"/>, which needs to know who is using it
/// (and what they carry), so it is not a plain threshold.
/// </summary>
public class BlockBehaviorHubDoor : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorHubDoor(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-hubdoor", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player)
            sapi.ModLoader.GetModSystem<ThresholdSystem>().UseHubDoor(player, blockSel.Position);
        return true;
    }
}

/// <summary>Camp Amber's painted board by the Level 1 door: right-click to read it.</summary>
public class BlockBehaviorHubSign : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorHubSign(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-hubsign", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:hub-camp-sign"), EnumChatType.Notification);
        return true;
    }
}
