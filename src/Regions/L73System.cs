using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// Level 73, "The Redlands" (experimental, kept as level 21): the rules of the island and of the Silver Castle
/// (docs/design/experimental-levels/73-plan.md, after the Wikidot page by Kitty Rika).
/// <list type="bullet">
/// <item><b>The hordes.</b> Everywhere outside the castle's walls is the edge of the level (<see cref="BandAt"/>): the
/// director sends its packs there, as the page has it; within the walls nothing hostile comes.</item>
/// <item><b>No light.</b> "DO NOT use an artificial light source": a light carried outside the walls is a noise the
/// hordes come to, every few seconds, from far off (<see cref="LightNoise"/>); the first time, a warning.</item>
/// <item><b>The door.</b> "Bang on the door as loud as possible, and you will be safe": it opens to a hard knocking from
/// outside (<see cref="Knocks"/> blows in <see cref="KnockMs"/>), to a single touch from inside, and shuts itself again.
/// The attic's doors never open: "CORAN has declared the attic off-limits".</item>
/// <item><b>The table of plenty.</b> A place set at the mahogany table feeds and waters whoever sits to it, and is set
/// again a few hours later (<see cref="BlockEntityL73Table"/>); the bathrooms' barrels of warm water wash and warm, and
/// fill a bottle (<see cref="BlockL73Bath"/>).</item>
/// <item><b>CORAN.</b> One, while anyone is in the level: blind, chained, never hostile to a human, he walks the hill
/// round the castle and kills whatever hostile thing he hears outside its walls (<see cref="AiTaskL73Coran"/>).</item>
/// </list>
/// </summary>
public partial class L73System : ModSystem
{
    /// <summary>How many blows on the door from outside open it, within how long; how long it stays open.</summary>
    public const int Knocks = 4, KnockMs = 3500, OpenMs = 6000;

    /// <summary>How often, and how loud, a light carried outside the walls calls the hordes (MenaceSystem's noise scale).</summary>
    public const double LightNoiseSeconds = 4, LightNoise = 0.7;

    /// <summary>How long a place at the table takes to be set again (game hours).</summary>
    public const double RefillHours = 4;

    /// <summary>Balance fixes 2026-11: the table feeds each wanderer once, then not again for this many game hours (the lore's one meal).</summary>
    public const double MealEveryHours = 12;

    /// <summary>The player's watched attribute holding the game hour of their last meal at the table (per player, saved with them).</summary>
    public const string LastMealKey = "backrooms:l73lastmeal";

    /// <summary>What a place at the table gives: satiety (a stew of Hound meat and bread), and hydration (a glass of water).</summary>
    public const float MealSatiety = 600, MealHydration = 700;

    /// <summary>The server's instance, for the blocks and Coran's task.</summary>
    public static L73System Server { get; private set; }

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private MenaceSystem menace;
    private long tickListener = -1;

    private long coranId = -1, lastPlayerMs, doorCloseAtMs = -1, nextDummyLookMs;
    private bool dummyAbout;
    private bool doorOpen, doorChecked;
    private readonly Dictionary<string, List<long>> knocks = new();
    private readonly Dictionary<string, long> nextLightNoiseMs = new(), warnedLight = new(), nextKnockHintMs = new();

    public WorldLayout Layout => layout;
    public WorldGeometry Geometry => geometry;

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockClass("BackroomsL73Door", typeof(BlockL73Door));
        api.RegisterBlockClass("BackroomsL73Table", typeof(BlockL73Table));
        api.RegisterBlockClass("BackroomsL73Lectern", typeof(BlockL73Lectern)); // (round 4: the visitors' book)
        api.RegisterBlockEntityClass("BackroomsL73Table", typeof(BlockEntityL73Table));
        api.RegisterBlockClass("BackroomsL73Bath", typeof(BlockL73Bath));
        api.RegisterEntity("BackroomsCoran", typeof(EntityCoran));
        AiTaskRegistry.Register<AiTaskL73Coran>("backrooms-l73coran");
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            menace = api.ModLoader.GetModSystem<MenaceSystem>();
            Server = this;
            tickListener = api.Event.RegisterGameTickListener(OnTick, 1000);
            api.ChatCommands.Get("backrooms")?
                .BeginSubCommand("l73coran")
                    .WithDescription("Level 73 (review shots): puts Coran down at x z facing a compass heading (default 180, south), standing still for 30 s")
                    .WithArgs(api.ChatCommands.Parsers.Double("x"), api.ChatCommands.Parsers.Double("z"), api.ChatCommands.Parsers.OptionalDouble("heading"))
                    .RequiresPrivilege(Privilege.controlserver)
                    .HandleWith(OnCoranCommand)
                .EndSubCommand();
            RegisterLinkCommands(api);
            api.Logger.Notification("[backrooms] Level 73: the castle's gate at {0},{1}, its door at {2},{3}, the plateau at y {4}", layout.L73Gate.X, layout.L73Gate.Z,
                layout.L73Door.X, layout.L73Door.Z, geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau);
        });
    }

    /// <summary>
    /// <c>/backrooms l73coran x z [heading]</c> (review screenshots): Coran is put down at x, z on the ground (put about first if
    /// he is not), facing the given compass heading (0 north, 90 east; default south), and stands there listening for half a
    /// minute before he goes back to his round.
    /// </summary>
    private TextCommandResult OnCoranCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        double x = (double)args[0], z = (double)args[1];
        double heading = args.Parsers[2].IsMissing ? 180 : (double)args[2];
        int gx = (int)Math.Floor(x), gz = (int)Math.Floor(z);
        if (!InLevel(x, z)) return TextCommandResult.Error("That is not in Level 73");
        Entity coran = Coran;
        if (coran == null)
        {
            lastPlayerMs = sapi.World.ElapsedMilliseconds;
            KeepCoran(true, lastPlayerMs);
            coran = Coran;
        }
        if (coran == null) return TextCommandResult.Error("Coran could not be put down (is the gate's ground loaded?)");
        double y = GroundAt(gx, gz) ?? geometry.FloorFor(WorldLayout.Level73) + layout.TileAt(gx, gz).Height + 1;
        // A player looks along (sin yaw, cos yaw): heading h (clockwise from north) is yaw 180 - h
        float yaw = (float)((180 - heading) * Math.PI / 180);
        coran.TeleportToDouble(x, y, z);
        coran.Pos.Yaw = coran.ServerPos.Yaw = yaw;
        CoranHoldUntilMs = sapi.World.ElapsedMilliseconds + 30_000;
        CoranHoldYaw = yaw;
        return TextCommandResult.Success($"Coran stands at {x:0.#},{y:0},{z:0.#}");
    }

    /// <summary>Until when Coran stands still where /backrooms l73coran put him, and the way he faces.</summary>
    public long CoranHoldUntilMs { get; private set; } = -1;
    public float CoranHoldYaw { get; private set; }

    public override void Dispose()
    {
        if (sapi != null && tickListener >= 0) sapi.Event.UnregisterGameTickListener(tickListener);
        if (Server == this) Server = null;
    }

    /// <summary>
    /// The director's band in the level at a block position: none of it within the castle's walls (its courtyard, the keep,
    /// the walls themselves), the edge of the level everywhere else.
    /// </summary>
    public static MenaceBand BandAt(WorldLayout layout, int gx, int gz) =>
        layout.TileAt(gx, gz).Zone is WorldLayout.L73Court or WorldLayout.L73Keep or WorldLayout.L73Walls ? MenaceBand.Safe : MenaceBand.Threshold;

    /// <summary>Whether a block position is in the level, outside the castle's walls.</summary>
    public bool Outside(double x, double z)
    {
        int gx = (int)Math.Floor(x), gz = (int)Math.Floor(z);
        if (layout.LevelAt(WorldLayout.MacroOf(gx), WorldLayout.MacroOf(gz)) != WorldLayout.Level73) return false;
        return BandAt(layout, gx, gz) != MenaceBand.Safe;
    }

    /// <summary>Whether a block position is in the level at all.</summary>
    public bool InLevel(double x, double z) => layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z))) == WorldLayout.Level73;

    /// <summary>The castle's middle, in blocks, on its plateau.</summary>
    public Vec3d CastleMiddle => new(layout.L73IslandX + 0.5, geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau + 1, layout.L73IslandZ + 0.5);

    /// <summary>The ground to stand on at a block column on the island (null in the sea, on the rim, or in the castle).</summary>
    public double? GroundAt(int gx, int gz)
    {
        Tile t = layout.TileAt(gx, gz);
        if (t.Level != WorldLayout.Level73 || t.Zone != WorldLayout.L73Land || t.Variant != 0) return null;
        return geometry.FloorFor(WorldLayout.Level73) + t.Height + 1;
    }

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        bool anyone = false;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity is not { Alive: true } entity) continue;
            if (!InLevel(entity.Pos.X, entity.Pos.Z)) continue;
            anyone = true;
            LightRule(player, entity, now);
        }
        // (Headless tests: a straw dummy standing in for a player keeps Coran about too)
        if (!anyone && now >= nextDummyLookMs)
        {
            nextDummyLookMs = now + 5000;
            anyone = sapi.World.LoadedEntities.Values.Any(e => e.Alive && Senses.IsTestTarget(e) && InLevel(e.Pos.X, e.Pos.Z));
            dummyAbout = anyone;
        }
        else if (!anyone) anyone = dummyAbout;
        if (anyone) lastPlayerMs = now;
        KeepCoran(anyone, now);
        DoorTick(now);
        // The ways in and out (L73System.Links.cs): the Gloom and Level 6's deepest dark, a night's rest, Coran's lead, the north door
        LinksTick(now);
    }

    // ================= No light =================

    /// <summary>A light in the hand outside the walls: a noise the hordes come to, and once a warning.</summary>
    private void LightRule(IServerPlayer player, EntityPlayer entity, long now)
    {
        if (player.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator) return;
        if (Senses.HeldLight(entity) < Senses.LitLevel || !Outside(entity.Pos.X, entity.Pos.Z)) return;
        string uid = player.PlayerUID;
        if (!warnedLight.ContainsKey(uid))
        {
            warnedLight[uid] = now;
            player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:l73-light-warning"), EnumChatType.Notification);
        }
        if (nextLightNoiseMs.TryGetValue(uid, out long next) && now < next) return;
        nextLightNoiseMs[uid] = now + (long)(LightNoiseSeconds * 1000);
        menace?.RaiseNoise(entity.Pos.XYZ, LightNoise, "l73light", entity);
    }

    // ================= CORAN =================

    /// <summary>The one Coran, if he is about.</summary>
    public Entity Coran => coranId < 0 ? null : sapi.World.GetEntityById(coranId) is { Alive: true } e ? e : null;

    /// <summary>
    /// Coran is about while anyone is in the level: put down outside the gate when the ground there is loaded, and gone a
    /// minute after the last wanderer has left (he is not saved with the world: StoreWithChunk is off).
    /// </summary>
    private void KeepCoran(bool anyone, long now)
    {
        Entity coran = Coran;
        if (coran == null) coranId = -1;
        if (!anyone)
        {
            if (coran != null && now - lastPlayerMs > 60_000)
            {
                coran.Die(EnumDespawnReason.Removed);
                coranId = -1;
            }
            return;
        }
        if (coran != null) return;
        // (One may be about already, from before a restart of this system)
        Entity found = sapi.World.LoadedEntities.Values.FirstOrDefault(e => e.Alive && e.Code?.Path == "l73-coran");
        if (found != null)
        {
            coranId = found.EntityId;
            return;
        }
        var (gx, gz) = layout.L73Gate;
        int sx = gx, sz = gz + 6;
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(new BlockPos(sx, geometry.FloorFor(WorldLayout.Level73), sz)) == null) return;
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation("backrooms:l73-coran"));
        if (type == null) return;
        Entity spawned = sapi.World.ClassRegistry.CreateEntity(type);
        double y = GroundAt(sx, sz) ?? geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau + 1;
        spawned.Pos.SetPos(sx + 0.5, y, sz + 0.5);
        spawned.Pos.Yaw = 0;
        spawned.AlwaysActive = true;
        sapi.World.SpawnEntity(spawned);
        coranId = spawned.EntityId;
        sapi.Logger.Notification("[backrooms] Level 73: Coran put down at {0},{1:0},{2}", sx, y, sz);
    }

    /// <summary>A line of Coran's to one wanderer (his voice is heard by all near him).</summary>
    public void CoranSays(Entity coran, IServerPlayer player, string key)
    {
        player.SendMessage(GlobalConstants.GeneralChatGroup, "<i>" + Say.T(player, "backrooms:l73-coran-name") + "</i>: " + Say.T(player, key), EnumChatType.Notification);
        sapi.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/entity/73/coran/voice{1 + sapi.World.Rand.Next(3)}"), coran, null, randomizePitch: true, range: 24, volume: 0.9f);
    }

    /// <summary>Coran struck (by a player, most likely): it does nothing, and he says so, now and then.</summary>
    public void OnCoranHurt(Entity coran, DamageSource source)
    {
        if (source?.SourceEntity is EntityPlayer { Player: IServerPlayer player } && sapi.World.Rand.NextDouble() < 0.5)
            CoranSays(coran, player, "backrooms:l73-coran-struck");
    }

    // ================= The door =================

    private BlockPos DoorPos(int leaf, int up) =>
        new(layout.L73Door.X + leaf, geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau + 1 + up, layout.L73Door.Z);

    /// <summary>A right-click on one of the castle's doors.</summary>
    public void Knock(IServerPlayer player, BlockPos pos, string door)
    {
        long now = sapi.World.ElapsedMilliseconds;
        if (door == "postern")
        {
            KnockPostern(player, pos);
            return;
        }
        if (door == "attic")
        {
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/chestclose"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 12, 0.5f);
            player.SendIngameError("l73attic", Say.T(player, "backrooms:l73-attic-locked"));
            return;
        }
        if (doorOpen) return;
        bool inside = player.Entity.Pos.Z < layout.L73Door.Z + 0.5;
        if (inside)
        {
            OpenDoor(now);
            return;
        }
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/knock"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 32, 1f);
        string uid = player.PlayerUID;
        if (!knocks.TryGetValue(uid, out List<long> blows)) knocks[uid] = blows = new List<long>();
        blows.RemoveAll(t => now - t > KnockMs);
        blows.Add(now);
        if (blows.Count >= Knocks)
        {
            blows.Clear();
            OpenDoor(now);
            player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:l73-door-opened"), EnumChatType.Notification);
            return;
        }
        if (!nextKnockHintMs.TryGetValue(uid, out long hint) || now >= hint)
        {
            nextKnockHintMs[uid] = now + 20_000;
            player.SendIngameError("l73knock", Say.T(player, "backrooms:l73-door-knock"));
        }
    }

    private void SetDoor(bool open)
    {
        string[] parts = { "lb", "rb", "lm", "rm", "lt", "rt" };
        for (int up = 0; up < 3; up++)
            for (int leaf = 0; leaf < 2; leaf++)
            {
                Block block = sapi.World.GetBlock(new AssetLocation($"backrooms:l73-door-{(open ? "open" : "shut")}-{parts[leaf + 2 * up]}"));
                BlockPos pos = DoorPos(leaf, up);
                if (block == null || !sapi.World.BlockAccessor.GetBlock(pos).Code.Path.StartsWith("l73-door-")) continue;
                sapi.World.BlockAccessor.ExchangeBlock(block.BlockId, pos);
                sapi.World.BlockAccessor.MarkBlockDirty(pos);
            }
        doorOpen = open;
    }

    private void OpenDoor(long now)
    {
        SetDoor(true);
        doorCloseAtMs = now + OpenMs;
        BlockPos at = DoorPos(0, 1);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/largedoor-open"), at.X + 1, at.Y, at.Z + 0.5, null, true, 32, 1f);
    }

    private void DoorTick(long now)
    {
        BlockPos at = DoorPos(0, 0);
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(at) == null)
        {
            doorChecked = false;
            return;
        }
        if (!doorChecked)
        {
            // (A door left open when the world last stopped is shut again a little after its ground is loaded)
            doorChecked = true;
            doorOpen = sapi.World.BlockAccessor.GetBlock(at).Code?.Path.StartsWith("l73-door-open") == true;
            if (doorOpen) doorCloseAtMs = now + OpenMs;
        }
        if (!doorOpen || now < doorCloseAtMs) return;
        // Not on anyone standing in the doorway (or just inside it, where the leaves swing)
        var box = new Cuboidd(at.X, at.Y, at.Z - 1, at.X + 2, at.Y + 3, at.Z + 1);
        bool blocked = sapi.World.GetEntitiesAround(new Vec3d(at.X + 1, at.Y + 1.5, at.Z), 4, 4, e => e.Alive && e.CollisionBox != null)
            .Any(e => box.IntersectsOrTouches(e.CollisionBox.ToDouble().Translate(e.Pos.X, e.Pos.Y, e.Pos.Z)));
        if (blocked)
        {
            doorCloseAtMs = now + 1000;
            return;
        }
        SetDoor(false);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/largedoor-close"), at.X + 1, at.Y + 1, at.Z + 0.5, null, true, 32, 1f);
    }
}

/// <summary>The castle's doors (the keep's, and the attic's that never open): a right-click knocks (L73System.Knock).</summary>
public class BlockL73Door : Block
{
    private WorldInteraction[] help;

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            L73System.Server?.Knock(player, blockSel.Position, Attributes?["l73Door"].AsString("keep") ?? "keep");
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer) =>
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l73-knock", MouseButton = EnumMouseButton.Right } };
}

/// <summary>A place at the mahogany table: right-click to eat and drink what is set there; it is set again later.</summary>
public class BlockL73Table : Block
{
    private WorldInteraction[] help;

    public bool IsSet => Variant?["state"] == "set";

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side != EnumAppSide.Server || byPlayer is not IServerPlayer player) return true;
        if (world.BlockAccessor.GetBlockEntity(blockSel.Position) is not BlockEntityL73Table place)
        {
            // (A table put down by hand has no place kept at it until now)
            world.BlockAccessor.SpawnBlockEntity("BackroomsL73Table", blockSel.Position);
            place = world.BlockAccessor.GetBlockEntity(blockSel.Position) as BlockEntityL73Table;
        }
        place?.Eat(player);
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer) =>
        IsSet ? help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l73-eat", MouseButton = EnumMouseButton.Right } }
            : Array.Empty<WorldInteraction>();
}

/// <summary>The lectern in the main hall with the castle's visitors' book (round 4): reading it turns to one of its pages.</summary>
public class BlockL73Lectern : Block
{
    private const int Pages = 4;
    private WorldInteraction[] help;

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side != EnumAppSide.Server || byPlayer is not IServerPlayer player) return true;
        // (a page by the hour, so reading again later may find another)
        int page = (int)(Math.Abs((long)Math.Floor(world.Calendar.TotalHours) + blockSel.Position.X + blockSel.Position.Z) % Pages) + 1;
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:l73-book-" + page), EnumChatType.Notification);
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer) =>
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l73-read", MouseButton = EnumMouseButton.Right } };
}

/// <summary>When a place at the table was cleared, and when it is set again.</summary>
public class BlockEntityL73Table : BlockEntity
{
    private double readyAt = -1;

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (api.Side == EnumAppSide.Server) RegisterGameTickListener(_ => Refill(), 5000 + api.World.Rand.Next(2000));
    }

    private bool IsSet => Block is BlockL73Table { IsSet: true };

    public void Eat(IServerPlayer player)
    {
        if (!IsSet)
        {
            player.SendIngameError("l73table", Say.T(player, "backrooms:l73-table-cleared"));
            return;
        }
        EntityPlayer entity = player.Entity;
        double now = Api.World.Calendar.TotalHours;
        double last = entity.WatchedAttributes.GetDouble(L73System.LastMealKey, double.NegativeInfinity);
        if (last <= now && now - last < L73System.MealEveryHours)
        {
            // (Already fed: the place stays set for the next guest)
            player.SendIngameError("l73table", Say.T(player, "backrooms:l73-table-fed"));
            return;
        }
        entity.WatchedAttributes.SetDouble(L73System.LastMealKey, now);
        entity.WatchedAttributes.MarkPathDirty(L73System.LastMealKey);
        entity.ReceiveSaturation(L73System.MealSatiety, EnumFoodCategory.Protein);
        Needs.Needs.Hydrate(entity, L73System.MealHydration);
        Api.World.PlaySoundAt(new AssetLocation("game:sounds/player/eat"), entity, null, randomizePitch: true, range: 12);
        Api.World.RegisterCallback(_ => Api.World.PlaySoundAt(new AssetLocation("game:sounds/player/drink1"), entity, null, randomizePitch: true, range: 12), 600);
        readyAt = Api.World.Calendar.TotalHours + L73System.RefillHours;
        Swap("bare");
        MarkDirty();
    }

    private void Refill()
    {
        if (IsSet || readyAt < 0 || Api.World.Calendar.TotalHours < readyAt) return;
        readyAt = -1;
        Swap("set");
        MarkDirty();
    }

    private void Swap(string state)
    {
        Block now = Api.World.GetBlock(BlockCodes.WithVariant(Block, "state", state));
        if (now == null || now.BlockId == Block.BlockId) return;
        Api.World.BlockAccessor.ExchangeBlock(now.BlockId, Pos);
        Api.World.BlockAccessor.MarkBlockDirty(Pos);
    }

    public override void ToTreeAttributes(ITreeAttribute tree)
    {
        base.ToTreeAttributes(tree);
        tree.SetDouble("readyAt", readyAt);
    }

    public override void FromTreeAttributes(ITreeAttribute tree, IWorldAccessor worldAccessForResolve)
    {
        base.FromTreeAttributes(tree, worldAccessForResolve);
        readyAt = tree.GetDouble("readyAt", -1);
    }
}

/// <summary>A barrel of warm water that never empties: right-click to wash (and warm through), or with an empty bottle to fill it.</summary>
public class BlockL73Bath : Block
{
    private WorldInteraction[] help;

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side != EnumAppSide.Server || byPlayer is not IServerPlayer player) return true;
        EntityPlayer entity = player.Entity;
        ItemSlot slot = player.InventoryManager.ActiveHotbarSlot;
        if (slot?.Itemstack?.Collectible?.Code?.ToString() == Needs.Water.Drinks.EmptyBottle)
        {
            Item full = world.GetItem(new AssetLocation("backrooms:bottledwater-clean"));
            if (full == null) return true;
            slot.TakeOut(1);
            slot.MarkDirty();
            Needs.Water.Drinks.Give(entity, new ItemStack(full));
            world.PlaySoundAt(new AssetLocation("game:sounds/effect/water-fill*"), blockSel.Position.X + 0.5, blockSel.Position.Y + 0.8, blockSel.Position.Z + 0.5, null, true, 12);
            return true;
        }
        // Washing: warm through, the island's dirt off
        if (entity.GetBehavior<EntityBehaviorBodyTemperature>() is { } warmth) warmth.CurBodyTemperature = warmth.NormalBodyTemperature;
        world.PlaySoundAt(new AssetLocation("game:sounds/environment/mediumsplash"), blockSel.Position.X + 0.5, blockSel.Position.Y + 0.8, blockSel.Position.Z + 0.5, null, true, 12, 0.6f);
        player.SendIngameError("l73bath", Say.T(player, "backrooms:l73-bath-washed"));
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer)
    {
        if (help != null) return help;
        Item bottle = world.GetItem(new AssetLocation(Needs.Water.Drinks.EmptyBottle));
        return help = new[]
        {
            new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l73-wash", MouseButton = EnumMouseButton.Right },
            new WorldInteraction { ActionLangCode = "backrooms:blockhelp-fillbottle", MouseButton = EnumMouseButton.Right, Itemstacks = bottle == null ? null : new[] { new ItemStack(bottle) } },
        };
    }
}

/// <summary>
/// CORAN: never hurt by anything (he regenerates whatever is done to him while one of his three hearts beats), never
/// stored with the world (L73System puts him down while anyone is in the level). Right-click: he turns to you and speaks.
/// </summary>
public class EntityCoran : EntityAgent
{
    private static WorldInteraction[] help;
    private long nextWordMs;

    public override bool StoreWithChunk => false;

    public override bool ReceiveDamage(DamageSource damageSource, float damage)
    {
        if (World.Side == EnumAppSide.Server && damageSource?.Type != EnumDamageType.Heal) L73System.Server?.OnCoranHurt(this, damageSource);
        return false;
    }

    private static WorldInteraction[] restedHelp;

    public override WorldInteraction[] GetInteractionHelp(IClientWorldAccessor world, EntitySelection es, IClientPlayer player)
    {
        // Once you have slept a night under his roof, you may ask him to lead you out
        if (player?.Entity?.WatchedAttributes.GetBool(L73System.RestedKey) == true)
            return restedHelp ??= new[]
            {
                new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l73-coran", MouseButton = EnumMouseButton.Right },
                new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l73-leadout", MouseButton = EnumMouseButton.Right, HotKeyCode = "shift" },
            };
        return help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l73-coran", MouseButton = EnumMouseButton.Right } };
    }

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode)
    {
        if (mode == EnumInteractMode.Attack)
        {
            base.OnInteract(byEntity, itemslot, hitPosition, mode);
            return;
        }
        if (World.Side != EnumAppSide.Server || byEntity is not EntityPlayer { Player: IServerPlayer player }) return;
        long now = World.ElapsedMilliseconds;
        if (now < nextWordMs) return;
        nextWordMs = now + 2500;
        GetBehavior<EntityBehaviorTaskAI>()?.TaskManager.GetTask<AiTaskL73Coran>()?.TurnTo(byEntity);
        // Sneaking: asking him to lead you out (L73System.Links.cs)
        if (byEntity.Controls.Sneak)
        {
            L73System.Server?.AskToLeave(this, player);
            return;
        }
        L73System.Server?.CoranSays(this, player, $"backrooms:l73-coran-say-{1 + World.Rand.Next(AiTaskL73Coran.Lines)}");
    }
}

/// <summary>
/// What Coran does (all of it, at priority over looking about). He is blind: he hunts by ear, so whatever hostile thing
/// moves within <see cref="HearRange"/> of him outside the castle's walls, and no farther than <see cref="Leash"/> from
/// them, he runs down and kills with a swing of a gauntlet on its chain (a sweep of both when there are several), and he
/// is never hostile to a human. Otherwise he walks the hill round the castle, stopping to listen; a wanderer who comes
/// close is greeted, now and then, with a bow and a word.
/// </summary>
public partial class AiTaskL73Coran : AiTaskBase
{
    /// <summary>How many things he says when spoken to (l73-coran-say-1 to -N), and when he greets (l73-coran-greet-1 to -N).</summary>
    public const int Lines = 8, Greetings = 4;

    private const double HearRange = 40, Leash = 140, ReachBlocks = 3.0, SweepBlocks = 3.8, PatrolMin = 36, PatrolMax = 75;
    private const long ThinkMs = 400, SwingMs = 450, GreetEveryMs = 240_000;

    /// <summary>The hostile things he kills (by code path).</summary>
    private static readonly HashSet<string> Prey = new()
    {
        "smiler", "hound", "deathmoth-male", "deathmoth-female", "skinstealer", "duller", "deathrat", "clump", "wretch", "bacteria",
        "mangled", "giantspider",
    };

    private readonly float walkSpeed, runSpeed;
    private Entity prey;
    private Vec3d goal;
    private string moving;
    private long nextThinkMs, strikeAtMs = -1, idleUntilMs, nextStepMs, nextChainMs, nextLogMs, lastPathMs;
    private MenaceSystem menace;

    /// <summary>To the server log, while the entity log is on (/backrooms entitylog).</summary>
    private void Log(string format, params object[] args)
    {
        menace ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        if (menace?.Logging == true) entity.World.Logger.Notification("[backrooms] Coran #" + entity.EntityId + ": " + format, args);
    }
    private readonly Dictionary<long, long> greeted = new();

    public AiTaskL73Coran(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.022f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.05f);
    }

    public override bool ShouldExecute() => true;

    public override bool ContinueExecute(float dt)
    {
        L73System l73 = L73System.Server;
        if (l73 == null) return true;
        long now = entity.World.ElapsedMilliseconds;
        Sounds(now);
        // Mid-swing: the blow lands, then he looks for the next
        // Put down for a picture (/backrooms l73coran): standing still, listening, facing the way he was set
        if (now < l73.CoranHoldUntilMs)
        {
            if (moving != null || pathTraverser.Active)
            {
                pathTraverser.Stop();
                Move(null);
                goal = null;
                prey = null;
            }
            entity.Pos.Yaw = l73.CoranHoldYaw;
            entity.ServerPos.Yaw = l73.CoranHoldYaw;
            return true;
        }
        if (strikeAtMs >= 0)
        {
            if (now >= strikeAtMs)
            {
                strikeAtMs = -1;
                Strike();
            }
            return true;
        }
        if (now >= nextThinkMs)
        {
            nextThinkMs = now + ThinkMs;
            Entity heard = Hear(l73);
            if (heard != prey && heard != null) Log("hears {0} #{1} {2:0.0} blocks off", heard.Code.Path, heard.EntityId, heard.Pos.DistanceTo(entity.Pos.XYZ));
            prey = heard;
            if (now >= nextLogMs)
            {
                nextLogMs = now + 15_000;
                Log("at {0:0},{1:0},{2:0}, {3}", entity.Pos.X, entity.Pos.Y, entity.Pos.Z, prey != null ? "hunting" : moving ?? "standing");
            }
        }
        if (prey != null)
        {
            Hunt(now);
            return true;
        }
        // Leading a wanderer out to the north door (L73System.Links.cs)
        if (Lead(l73, now)) return true;
        if (Greet(l73, now)) return true;
        Patrol(l73, now);
        return true;
    }

    /// <summary>The nearest hostile thing he can hear, outside the walls and within his leash.</summary>
    private Entity Hear(L73System l73)
    {
        Vec3d home = l73.CastleMiddle;
        Entity best = null;
        double bestD = double.MaxValue;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, (float)HearRange, 16, e => e.Alive && e.Code?.Domain == "backrooms" && Prey.Contains(e.Code.Path)))
        {
            if (!l73.Outside(e.Pos.X, e.Pos.Z) || e.Pos.HorDistanceTo(home) > Leash) continue;
            double d = e.Pos.SquareDistanceTo(entity.Pos.XYZ);
            if (d < bestD)
            {
                bestD = d;
                best = e;
            }
        }
        return best;
    }

    private void Hunt(long now)
    {
        if (!prey.Alive)
        {
            prey = null;
            return;
        }
        double d = entity.Pos.HorDistanceTo(prey.Pos.XYZ);
        if (d <= ReachBlocks && Math.Abs(prey.Pos.Y - entity.Pos.Y) < 4.5)
        {
            pathTraverser.Stop();
            Move(null);
            TurnTo(prey);
            int near = entity.World.GetEntitiesAround(entity.Pos.XYZ, (float)SweepBlocks, 3, e => e.Alive && e.Code != null && Prey.Contains(e.Code.Path)).Length;
            entity.AnimManager.StartAnimation(near >= 2 ? "sweep" : "attack");
            strikeAtMs = now + SwingMs;
            return;
        }
        Move("run");
        // (Steered at it again twice a second: it moves, and a traverser set going every tick never gets anywhere)
        if (!pathTraverser.Active || now - lastPathMs > 500)
        {
            lastPathMs = now;
            pathTraverser.WalkTowards(prey.Pos.XYZ.Clone(), runSpeed, (float)(ReachBlocks - 0.6), () => { }, () => { });
        }
        // A bellow when he goes for a pack
        if (now >= nextChainMs + 4000 && entity.World.Rand.NextDouble() < 0.08)
            entity.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/73/coran/roar"), entity, null, randomizePitch: true, range: 64, volume: 1f);
    }

    /// <summary>The blow: everything hostile within reach of the gauntlets, killed.</summary>
    private void Strike()
    {
        var hit = entity.World.GetEntitiesAround(entity.Pos.XYZ, (float)SweepBlocks, 5, e => e.Alive && e.Code != null && Prey.Contains(e.Code.Path));
        foreach (Entity e in hit)
        {
            e.ReceiveDamage(new DamageSource
            {
                Source = EnumDamageSource.Entity, SourceEntity = entity, CauseEntity = entity, Type = EnumDamageType.BluntAttack, KnockbackStrength = 2f,
                SourcePos = entity.Pos.XYZ,
            }, 1000f);
            // He leaves nothing (balance fixes 2026-11): no carcass to harvest, so following him is no meat or hide farm
            if (!e.Alive) e.Die(EnumDespawnReason.Removed);
        }
        entity.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/entity/73/coran/strike{1 + entity.World.Rand.Next(2)}"), entity, null, randomizePitch: true, range: 48, volume: 1f);
        if (hit.Length > 0) entity.World.Logger.Notification("[backrooms] Coran #{0} struck {1} ({2})", entity.EntityId, hit.Length, string.Join(", ", hit.Select(e => e.Code.Path)));
        prey = null;
    }

    /// <summary>A wanderer close by, not greeted for a while: he turns, bows, and has a word.</summary>
    private bool Greet(L73System l73, long now)
    {
        if (now < idleUntilMs && moving == null) return true;
        var player = entity.World.GetNearestEntity(entity.Pos.XYZ, 5, 3, e => e is EntityPlayer { Alive: true, Player: IServerPlayer }) as EntityPlayer;
        if (player == null) return false;
        if (greeted.TryGetValue(player.EntityId, out long last) && now - last < GreetEveryMs) return false;
        greeted[player.EntityId] = now;
        pathTraverser.Stop();
        Move(null);
        TurnTo(player);
        entity.AnimManager.StartAnimation("bow");
        idleUntilMs = now + 3000;
        l73.CoranSays(entity, (IServerPlayer)player.Player, $"backrooms:l73-coran-greet-{1 + entity.World.Rand.Next(Greetings)}");
        return true;
    }

    /// <summary>The round of the hill: to a point outside the walls, then a while standing, listening.</summary>
    private void Patrol(L73System l73, long now)
    {
        if (now < idleUntilMs) return;
        if (goal != null && entity.Pos.HorDistanceTo(goal) > 2.5 && pathTraverser.Active) return;
        if (goal != null)
        {
            // Arrived (or stuck): listen a while
            goal = null;
            pathTraverser.Stop();
            Move(null);
            entity.AnimManager.StartAnimation("listen");
            idleUntilMs = now + 4000 + entity.World.Rand.Next(7000);
            return;
        }
        entity.AnimManager.StopAnimation("listen");
        Vec3d home = l73.CastleMiddle;
        for (int tries = 0; tries < 8; tries++)
        {
            // On round the hill from where he is (a straight walk across would meet the castle's walls)
            double here = Math.Atan2(entity.Pos.Z - home.Z, entity.Pos.X - home.X);
            double a = here + (entity.World.Rand.NextDouble() * 2 - 1) * 0.8, r = PatrolMin + entity.World.Rand.NextDouble() * (PatrolMax - PatrolMin);
            int gx = (int)Math.Floor(home.X + Math.Cos(a) * r), gz = (int)Math.Floor(home.Z + Math.Sin(a) * r);
            if (l73.GroundAt(gx, gz) is not double y) continue;
            goal = new Vec3d(gx + 0.5, y, gz + 0.5);
            Move("walk");
            pathTraverser.WalkTowards(goal, walkSpeed, 1.5f, () => { }, () => { idleUntilMs = 0; });
            return;
        }
    }

    private void Move(string anim)
    {
        if (anim == moving) return;
        if (moving != null) entity.AnimManager.StopAnimation(moving);
        moving = anim;
        if (anim != null)
        {
            entity.AnimManager.StopAnimation("listen");
            entity.AnimManager.StartAnimation(anim);
        }
    }

    public void TurnTo(Entity target)
    {
        if (target == null) return;
        entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
    }

    /// <summary>His steps and his chains, heavier at a run.</summary>
    private void Sounds(long now)
    {
        if (moving != null && now >= nextStepMs)
        {
            nextStepMs = now + (moving == "run" ? 420 : 700);
            entity.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/entity/73/coran/step{1 + entity.World.Rand.Next(3)}"), entity, null, randomizePitch: true, range: 32, volume: 0.8f);
        }
        if (now >= nextChainMs)
        {
            nextChainMs = now + 6000 + entity.World.Rand.Next(9000);
            entity.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/entity/73/coran/chain{1 + entity.World.Rand.Next(3)}"), entity, null, randomizePitch: true, range: 32, volume: 0.6f);
        }
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Move(null);
    }
}
