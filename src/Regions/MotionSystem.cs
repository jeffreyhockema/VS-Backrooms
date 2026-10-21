using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Entities;
using Backrooms.Thresholds;
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
/// Level 94, Motion: its days and nights, its castle, and the King.
/// <list type="bullet">
/// <item>By day the siren poles play and nothing hunts. The tune slows and goes flat in the last hours of the
/// afternoon; at dusk it stops, and the Animations come out (see <see cref="MenaceSystem"/>).</item>
/// <item>The Animations hunt anything that does not look animated. Indoors you are safe; out of doors, whoever stands
/// quite still for a few seconds is taken for a doll (<see cref="PlayingDoll"/>), and so is whoever carries a shard of
/// the King's crown.</item>
/// <item>Everyone who comes to Level 94 falls into it out of the sky, and lands softly (<see cref="LandSoftly"/>).</item>
/// <item>In the castle, nothing is animated, and the Robo-Men stand guard: touch or break anything there and they
/// come (<see cref="CastleAlarmed"/>). The throne room has a door on each side; only one opens, a different one each
/// day.</item>
/// <item>Sit in the second chair at the King's table, and he raises your nightmare, the thing that has killed you most
/// often, in clay. It can only do what you think it can: steady, it is a quarter as strong; shaken, twice. Destroy it
/// and the King bursts into light, and you are carried out of Level 94 (or back to a town).</item>
/// </list>
/// </summary>
public class MotionSystem : ModSystem
{
    /// <summary>How far above the ground someone falling into Level 94 starts.</summary>
    public const double SkyDrop = 22;

    private const string SoftKey = "backrooms:softLandingUntil";
    private const string NightmareKey = "backrooms:nightmareOf";
    private const string KilledByKey = "backrooms:killedBy";
    private const string CrownKey = "backrooms:crownGiven";
    private const double StillSeconds = 4, AlarmSeconds = 90;

    // (Static, for the menace AI's sake; cleared when a server starts, so nothing carries over from the last world
    // loaded in this process)
    private static readonly Dictionary<string, (double X, double Y, double Z, long Since)> stillness = new();
    private static readonly Dictionary<string, long> alarmedUntil = new();
    private static readonly Dictionary<string, long> trialEntity = new();
    /// <summary>The players carrying a shard of the King's crown, as of the last tick (the AI asks every time it looks).</summary>
    private static readonly HashSet<string> crownCarriers = new();
    private static long nowMs;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private long tickId;

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockClass("BackroomsTrialChair", typeof(BlockTrialChair));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        stillness.Clear();
        alarmedUntil.Clear();
        trialEntity.Clear();
        crownCarriers.Clear();
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            tickId = api.Event.RegisterGameTickListener(OnTick, 500);
            api.Event.PlayerNowPlaying += OnPlayerNowPlaying;
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
            api.Event.PlayerDeath += OnPlayerDeath;
            api.Event.OnEntityDeath += OnEntityDeath;
            api.Event.DidBreakBlock += OnBroke;
            api.Event.DidUseBlock += OnUsed;
            api.Event.DidPlaceBlock += OnPlaced;
        });
    }

    public override void Dispose()
    {
        if (sapi == null || layout == null) return;
        if (tickId != 0) sapi.Event.UnregisterGameTickListener(tickId);
        sapi.Event.PlayerNowPlaying -= OnPlayerNowPlaying;
        sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
        sapi.Event.PlayerDeath -= OnPlayerDeath;
        sapi.Event.OnEntityDeath -= OnEntityDeath;
        sapi.Event.DidBreakBlock -= OnBroke;
        sapi.Event.DidUseBlock -= OnUsed;
        sapi.Event.DidPlaceBlock -= OnPlaced;
    }

    private void OnBroke(IServerPlayer player, int oldBlockId, BlockSelection sel) => Disturbed(player, sel?.Position);
    private void OnUsed(IServerPlayer player, BlockSelection sel) => Disturbed(player, sel?.Position);
    private void OnPlaced(IServerPlayer player, int oldBlockId, BlockSelection sel, ItemStack withItem) => Disturbed(player, sel?.Position);

    // ================= Day and night =================

    /// <summary>Night in Level 94: from dusk until dawn, when the Animations are out.</summary>
    public static bool IsNight(IGameCalendar calendar)
    {
        float hour = calendar.HourOfDay;
        return hour >= 20f || hour < 5.5f;
    }

    /// <summary>The last hours of the afternoon, when the siren poles' tune slows and goes flat.</summary>
    public static bool IsDusk(IGameCalendar calendar) => calendar.HourOfDay is >= 17.5f and < 20f;

    /// <summary>Twilight, dusk and dawn, when the rusted gates open.</summary>
    public static bool IsTwilight(IGameCalendar calendar) => calendar.HourOfDay is >= 19f and < 21f or >= 4.5f and < 6.5f;

    // ================= Playing doll, and the castle's guards =================

    /// <summary>
    /// Whether the Animations take a player for one of their own, or for a doll: someone who has stood quite still for
    /// a few seconds, or who carries a shard of the King's crown.
    /// </summary>
    public static bool PlayingDoll(EntityPlayer player)
    {
        string uid = player?.PlayerUID ?? "";
        if (crownCarriers.Contains(uid)) return true;
        return stillness.TryGetValue(uid, out var still) && nowMs - still.Since >= StillSeconds * 1000;
    }

    /// <summary>Whether a shard of the King's crown is in someone's hotbar or backpack.</summary>
    private static bool CarriesCrownShard(IPlayerInventoryManager inventories) =>
        HoldsCrownShard(inventories.GetOwnInventory(GlobalConstants.hotBarInvClassName)) || HoldsCrownShard(inventories.GetOwnInventory(GlobalConstants.backpackInvClassName));

    private static bool HoldsCrownShard(IInventory inventory)
    {
        if (inventory == null) return false;
        foreach (ItemSlot slot in inventory)
            if (slot?.Itemstack?.Collectible?.Code is { Domain: "backrooms", Path: "crownshard" }) return true;
        return false;
    }

    /// <summary>Whether a player has disturbed something in the castle lately, so that its Robo-Men are after them.</summary>
    public static bool CastleAlarmed(EntityPlayer player) => alarmedUntil.TryGetValue(player?.PlayerUID ?? "", out long until) && nowMs < until;

    /// <summary>Whether a player is facing the King's trial.</summary>
    public static bool InTrial(EntityPlayer player) => trialEntity.ContainsKey(player?.PlayerUID ?? "");

    private void Disturbed(IServerPlayer player, BlockPos pos)
    {
        if (player?.Entity == null || pos == null || layout == null) return;
        if (layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)) != WorldLayout.Motion || !layout.InCastle(pos.X, pos.Z)) return;
        if (pos.Y < geometry.FloorFor(WorldLayout.Motion) + WorldLayout.MountainHeight) return;
        // (Sitting down to the King's table is no disturbance; his doors are his own)
        Block block = sapi.World.BlockAccessor.GetBlock(pos);
        if (block?.Code?.Path is { } path && (path.StartsWith("trialchair") || path.StartsWith("thronedoor"))) return;
        bool already = CastleAlarmed(player.Entity);
        alarmedUntil[player.PlayerUID] = sapi.World.ElapsedMilliseconds + (long)(AlarmSeconds * 1000);
        if (!already)
        {
            sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/robowind"), player.Entity, null, true, 32, 0.8f);
            player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:castle-alarm"), EnumChatType.Notification);
        }
    }

    // ================= Every half second =================

    private void OnTick(float dt)
    {
        nowMs = sapi.World.ElapsedMilliseconds;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer { Entity: { } entity } player) continue;
            EntityPos pos = entity.Pos;
            if (!stillness.TryGetValue(player.PlayerUID, out var still)
                || (still.X - pos.X) * (still.X - pos.X) + (still.Y - pos.Y) * (still.Y - pos.Y) + (still.Z - pos.Z) * (still.Z - pos.Z) > 0.15 * 0.15)
                stillness[player.PlayerUID] = (pos.X, pos.Y, pos.Z, nowMs);
            // (Only the menace of Level 94 asks, so only those standing in it are looked through)
            bool inMotion = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(pos.X)), WorldLayout.MacroOf((int)Math.Floor(pos.Z))) == WorldLayout.Motion;
            if (inMotion && player.InventoryManager is { } inventories && CarriesCrownShard(inventories)) crownCarriers.Add(player.PlayerUID);
            else crownCarriers.Remove(player.PlayerUID);
        }
        // A trial ends if the one facing it has gone (dead, left, or carried off)
        if (trialEntity.Count == 0) return;
        foreach (string uid in trialEntity.Keys.ToList())
        {
            IServerPlayer player = sapi.World.PlayerByUid(uid) as IServerPlayer;
            Entity nightmare = sapi.World.GetEntityById(trialEntity[uid]);
            bool facing = player?.Entity is { Alive: true } p && nightmare is { Alive: true } && p.Pos.SquareDistanceTo(nightmare.Pos.XYZ) < 40 * 40;
            if (facing) continue;
            trialEntity.Remove(uid);
            if (nightmare is { Alive: true }) nightmare.Die(EnumDespawnReason.Removed);
        }
    }

    // ================= Falling in =================

    /// <summary>Someone is about to fall into Level 94 out of the sky: they land softly.</summary>
    public static void LandSoftly(Entity entity, IWorldAccessor world) =>
        entity.Attributes.SetLong(SoftKey, world.ElapsedMilliseconds + 15000);

    // The players whose health this has hooked, by entity id (a second NowPlaying must not hook the same entity twice)
    private readonly HashSet<long> hooked = new();

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        string uid = player.PlayerUID;
        stillness.Remove(uid);
        alarmedUntil.Remove(uid);
        crownCarriers.Remove(uid);
        if (player.Entity != null) hooked.Remove(player.Entity.EntityId);
    }

    private void OnPlayerNowPlaying(IServerPlayer player)
    {
        if (player.Entity?.GetBehavior<EntityBehaviorHealth>() is not { } health || !hooked.Add(player.Entity.EntityId)) return;
        health.onDamaged += (damage, source) =>
        {
            Entity entity = player.Entity;
            if (entity == null) return damage;
            // A soft landing on the hills of Level 94
            if (source.Source == EnumDamageSource.Fall && entity.Attributes.GetLong(SoftKey, 0) > sapi.World.ElapsedMilliseconds) return 0;
            // What the King raised can only do what you think it can: steady, a quarter of its strength; shaken, twice
            Entity from = source.GetCauseEntity() ?? source.SourceEntity;
            if (from != null && from.Attributes.GetString(NightmareKey) == player.PlayerUID)
            {
                double stability = Math.Clamp(entity.WatchedAttributes.GetDouble("temporalStability", 1), 0, 1);
                return damage * (float)(2.0 - 1.75 * stability);
            }
            return damage;
        };
    }

    // ================= The throne room =================

    /// <summary>The door that opens today (0 north, 1 east, 2 south, 3 west of the throne room).</summary>
    private int TodaysDoor() => (int)(Hashing.Hash((ulong)sapi.World.Seed, (int)Math.Floor(sapi.World.Calendar.TotalDays), 94, 0x7404) % 4);

    /// <summary>Castle coordinates of a block position (0 to <see cref="WorldLayout.CastleSize"/>).</summary>
    private (int U, int V) CastleUV(int x, int z) => (x - layout.MotionOriginX + WorldLayout.CastleSize / 2, z - layout.MotionOriginZ + WorldLayout.CastleSize / 2);

    private Vec3d CastleSpot(double u, double v) => new(layout.MotionOriginX - WorldLayout.CastleSize / 2 + u + 0.5,
        geometry.FloorFor(WorldLayout.Motion) + WorldLayout.MountainHeight + 1.05, layout.MotionOriginZ - WorldLayout.CastleSize / 2 + v + 0.5);

    private static bool InThroneRoom(int u, int v) => u is >= 23 and <= 32 && v is >= 23 and <= 32;

    /// <summary>Someone tries one of the throne room's doors.</summary>
    public void UseThroneDoor(IServerPlayer player, BlockPos pos)
    {
        if (layout == null || player.Entity == null) return;
        var (u, v) = CastleUV(pos.X, pos.Z);
        int door = v == 22 ? 0 : u == 33 ? 1 : v == 33 ? 2 : 3;
        // The way in is in front of the door, inside; the way out in front of it, outside
        (int Du, int Dv) step = door switch { 0 => (0, -1), 1 => (1, 0), 2 => (0, 1), _ => (-1, 0) };
        var (pu, pv) = CastleUV((int)Math.Floor(player.Entity.Pos.X), (int)Math.Floor(player.Entity.Pos.Z));
        bool inside = InThroneRoom(pu, pv);
        if (!inside && door != TodaysDoor())
        {
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 16);
            player.SendIngameError("backrooms-throne", Say.T(player, "backrooms:thronedoor-shut"));
            return;
        }
        Vec3d to = inside ? CastleSpot(u + step.Du * 1, v + step.Dv * 1) : CastleSpot(u - step.Du, v - step.Dv);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 16);
        player.Entity.TeleportToDouble(to.X, to.Y, to.Z);
        if (!inside) player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:throneroom"), EnumChatType.Notification);
    }

    // ================= The trial =================

    /// <summary>Someone sits down in the second chair at the King's table.</summary>
    public void StartTrial(IServerPlayer player, BlockPos chair)
    {
        if (layout == null || player.Entity == null || InTrial(player.Entity)) return;
        if (trialEntity.Count > 0)
        {
            player.SendIngameError("backrooms-trial", Say.T(player, "backrooms:trial-busy"));
            return;
        }
        string code = NightmareOf(player);
        var menace = sapi.ModLoader.GetModSystem<MenaceSystem>();
        Entity nightmare = menace?.SpawnHunter(code, CastleSpot(25, 26), player.Entity) ?? menace?.SpawnHunter(Roster.Hound, CastleSpot(25, 26), player.Entity);
        if (nightmare == null) return;
        nightmare.Attributes.SetString(NightmareKey, player.PlayerUID);
        nightmare.AlwaysActive = true;
        if (nightmare.GetBehavior<EntityBehaviorHealth>() is { } health)
        {
            health.BaseMaxHealth *= 1.5f;
            health.UpdateMaxHealth();
            health.Health = health.MaxHealth;
        }
        trialEntity[player.PlayerUID] = nightmare.EntityId;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/allglory"), chair.X + 0.5, chair.Y + 1, chair.Z + 0.5, null, false, 32, 1f);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:trial-start"), EnumChatType.Notification);
    }

    /// <summary>The kind of thing that has killed a player most often (a Hound if nothing ever has).</summary>
    private string NightmareOf(IServerPlayer player)
    {
        ITreeAttribute counts = player.Entity.WatchedAttributes.GetTreeAttribute(KilledByKey);
        string worst = Roster.Hound;
        int most = 0;
        if (counts != null)
            foreach (var entry in counts)
                if (entry.Value is IntAttribute n && n.value > most && Roster.AllCodes.Contains(entry.Key)) { most = n.value; worst = entry.Key; }
        // What cannot be fought in a room (a Smiler cannot be killed, the Thing lives in the deep, a Clump lies in wait,
        // the Mangled would not fit) comes as the next worst thing: a Skin-Stealer
        return worst is Roster.Smiler or Roster.TheThing or Roster.Clump or Roster.Mangled ? Roster.SkinStealer : worst;
    }

    private void OnPlayerDeath(IServerPlayer player, DamageSource source)
    {
        Entity killer = source?.GetCauseEntity() ?? source?.SourceEntity;
        if (killer?.Code == null || player.Entity == null) return;
        string code = killer.Code.ToString();
        if (killer.Attributes.GetString(NightmareKey) != null) return; // the King's own doesn't count
        ITreeAttribute counts = player.Entity.WatchedAttributes.GetOrAddTreeAttribute(KilledByKey);
        counts.SetInt(code, counts.GetInt(code) + 1);
        player.Entity.WatchedAttributes.MarkPathDirty(KilledByKey);
    }

    private void OnEntityDeath(Entity entity, DamageSource source)
    {
        string uid = entity.Attributes.GetString(NightmareKey);
        if (uid == null || !trialEntity.TryGetValue(uid, out long id) || id != entity.EntityId) return;
        trialEntity.Remove(uid);
        if (sapi.World.PlayerByUid(uid) is not IServerPlayer { Entity: { Alive: true } } player) return;

        // The King bursts into light
        Vec3d king = CastleSpot(28, 24);
        sapi.World.SpawnParticles(60, ColorUtil.ToRgba(255, 255, 240, 180), king.AddCopy(-1, 0, -1), king.AddCopy(1, 4, 1),
            new Vec3f(-3, 0, -3), new Vec3f(3, 5, 3), 1.5f, -0.05f, 0.6f, EnumParticleModel.Quad);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/translocate-breakdimension"), king.X, king.Y, king.Z, null, false, 48, 1f);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:trial-won"), EnumChatType.Notification);
        if (!player.Entity.WatchedAttributes.GetBool(CrownKey))
        {
            player.Entity.WatchedAttributes.SetBool(CrownKey, true);
            Item shard = sapi.World.GetItem(new AssetLocation("backrooms:crownshard"));
            if (shard != null && !player.InventoryManager.TryGiveItemstack(new ItemStack(shard)))
                sapi.World.SpawnItemEntity(new ItemStack(shard), player.Entity.Pos.XYZ);
        }
        // ...and carries you out: to the Habitable Zone, the Abandoned Office, or back to a town
        sapi.Event.RegisterCallback(_ => sapi.ModLoader.GetModSystem<ThresholdSystem>()?.CarryFromTrial(player), 1500);
    }
}

/// <summary>The second chair at the King's table: sit in it, and the trial begins.</summary>
public class BlockTrialChair : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player)
            sapi.ModLoader.GetModSystem<MotionSystem>()?.StartTrial(player, blockSel.Position);
        return true;
    }

    private WorldInteraction[] help;

    // (Asked every frame the chair is looked at: the help is made once)
    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer) =>
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-trialchair", MouseButton = EnumMouseButton.Right } };
}
