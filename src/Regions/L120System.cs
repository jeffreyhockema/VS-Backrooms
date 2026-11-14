using System;
using System.Collections.Generic;
using Backrooms.Entities;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;
using Kind = Backrooms.Worldgen.WorldLayout.L120HallKind;
using Zone = Backrooms.Worldgen.WorldLayout.L120Zone;

namespace Backrooms.Regions;

/// <summary>
/// Level 120, "Broken Servos": the rules (docs/design/experimental-levels/120-plan.md; Wikidot's Level 120).
/// <list type="bullet">
/// <item><b>Computer blocks.</b> "Reaching [the White Voids or the Pitch-Black Hallways] only requires finding an intact
/// computer block. Booting this up will 'load in' either." A whole terminal (one in most clusters) boots when right-clicked:
/// the drive spins up, and two seconds later whoever booted it is in a pocket, a White Void (three times in five, by the
/// terminal's own hash) or a Pitch-Black Hallway: the nearest pocket hall of that kind (<see cref="WorldLayout.L120NearestPocket"/>),
/// always the same one for the same terminal.</item>
/// <item><b>The windows.</b> "Travel in one direction until you reach the edge of the cluster ... windows that will lead
/// back to the computer block that brought you." Walking into a pocket's broken window puts you back in front of the
/// terminal you booted (remembered on the player); if there is none, by the nearest whole terminal, or anywhere in the level.</item>
/// <item><b>Misglitches.</b> "Anyone who dies here instantly becomes a Misglitch." A player who dies anywhere in the level
/// leaves one standing where they fell (by their body), red-marked, or all black if the death was from within; it lasts a
/// day or until killed (<see cref="AiTaskMisglitch"/>).</item>
/// <item><b>Smilers in the White Voids</b>, "too indulged in the light this room naturally emits to attack you": one to
/// three stand about each void while someone is in it, put down out of sight as wanderers (they do not hunt; struck,
/// they withdraw, as every Smiler).</item>
/// <item><b>Tripping.</b> "It's easy to trip" in the Pitch-Black Hallways: running there, now and then you go down (a little
/// hurt, slowed a moment); cables over the floor anywhere in the dark can catch you too. (The Sub-Misglitches a fall can
/// raise are left for later.)</item>
/// </list>
/// </summary>
public class L120System : ModSystem
{
    public const string BackKey = "backrooms:l120Back";
    public const string MisglitchCode = "backrooms:l120-misglitch";
    private const ulong SaltBoot = 0x26C1;
    private const long BootDelayMs = 2200, BusyMs = 3500;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private ThresholdSystem thresholds;
    private readonly Dictionary<string, long> busyUntil = new();
    private readonly Dictionary<string, (double X, double Z, double Run)> walked = new();
    private readonly Random rand = new();
    private long fastTick, slowTick;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsL120Boot", typeof(BlockBehaviorL120Boot));
        AiTaskRegistry.Register<AiTaskMisglitch>("backrooms-l120-misglitch");
    }

    public override bool ShouldLoad(EnumAppSide side) => true;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.3;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            thresholds = api.ModLoader.GetModSystem<ThresholdSystem>();
            fastTick = api.Event.RegisterGameTickListener(OnFastTick, e => api.Logger.Error("[backrooms] Level 120: {0}", e), 250, 1000);
            slowTick = api.Event.RegisterGameTickListener(OnSlowTick, e => api.Logger.Error("[backrooms] Level 120 voids: {0}", e), 2000, 1500);
            api.Event.PlayerDeath += OnPlayerDeath;
            api.Event.PlayerDisconnect += OnPlayerDisconnect;
        });

        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l120")
                .WithDescription("Level 120 (testing): 'misglitch [x z]' puts a Misglitch down where you stand (or at x z, from the console); 'void' or 'hallway' takes you into the nearest pocket of that kind; 'boot' shows the nearest whole terminal; 'back' takes you back through a window; 'smiler [x z]' puts a Smiler down lost in the light")
                .WithArgs(api.ChatCommands.Parsers.Word("what"), api.ChatCommands.Parsers.OptionalInt("x"), api.ChatCommands.Parsers.OptionalInt("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnCommand)
            .EndSubCommand();
    }

    public override void Dispose()
    {
        if (sapi == null || layout == null) return;
        if (fastTick != 0) sapi.Event.UnregisterGameTickListener(fastTick);
        if (slowTick != 0) sapi.Event.UnregisterGameTickListener(slowTick);
        sapi.Event.PlayerDeath -= OnPlayerDeath;
        sapi.Event.PlayerDisconnect -= OnPlayerDisconnect;
    }

    private void OnPlayerDisconnect(IServerPlayer player)
    {
        busyUntil.Remove(player.PlayerUID);
        walked.Remove(player.PlayerUID);
    }

    private bool InLevel(double x, double z) => layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(x)), WorldLayout.MacroOf((int)Math.Floor(z))) == WorldLayout.Level120;

    private bool Busy(IServerPlayer player) => busyUntil.TryGetValue(player.PlayerUID, out long until) && sapi.World.ElapsedMilliseconds < until;

    private static string Text(IServerPlayer player, string key, params object[] args) => Say.T(player, "backrooms:" + key, args);

    // ================= Booting a terminal =================

    /// <summary>Someone has right-clicked a whole terminal: it boots, and takes them into its pocket.</summary>
    public void Boot(IServerPlayer player, BlockPos pos)
    {
        if (layout == null || player.Entity is not { Alive: true } || Busy(player)) return;
        busyUntil[player.PlayerUID] = sapi.World.ElapsedMilliseconds + BootDelayMs + BusyMs;
        var at = new Vec3d(pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5);
        (int X, int Z)? into = PocketOf(pos.X, pos.Z);
        if (into is not { } arrival)
        {
            sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/120/relay"), at.X, at.Y, at.Z, null, true, 16);
            player.SendIngameError("backrooms-l120-boot", Text(player, "l120-boot-nothing"));
            return;
        }
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/120/boot"), at.X, at.Y, at.Z, null, false, 16);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Text(player, "l120-boot"), EnumChatType.Notification);
        // Where they stand now is where the windows bring them back to
        ITreeAttribute back = new TreeAttribute();
        back.SetDouble("x", player.Entity.Pos.X);
        back.SetDouble("y", player.Entity.Pos.Y);
        back.SetDouble("z", player.Entity.Pos.Z);
        back.SetFloat("yaw", player.Entity.Pos.Yaw);
        player.Entity.WatchedAttributes[BackKey] = back;
        sapi.Event.RegisterCallback(_ =>
        {
            if (player.Entity is not { Alive: true } || player.Entity.Pos.SquareDistanceTo(at) > 5 * 5) return;
            double y = geometry.FloorFor(WorldLayout.Level120) + layout.ArrivalHeight(arrival.X, arrival.Z);
            thresholds?.L120Carry(player, arrival.X + 0.5, y, arrival.Z + 0.5);
            busyUntil[player.PlayerUID] = sapi.World.ElapsedMilliseconds + BusyMs;
        }, (int)BootDelayMs);
    }

    /// <summary>Where a whole terminal at a block takes you: a White Void three times in five (by its hash), otherwise a Pitch-Black Hallway; the nearest pocket hall of that kind, else of the other.</summary>
    public (int X, int Z)? PocketOf(int x, int z)
    {
        var (hx, hz) = WorldLayout.L120HallOf(x, z);
        bool wantVoid = Hashing.Unit(Hashing.Hash((ulong)sapi.World.Seed, x, z, SaltBoot)) < 0.6;
        Kind first = wantVoid ? Kind.Void : Kind.Hallway, second = wantVoid ? Kind.Hallway : Kind.Void;
        var pocket = layout.L120NearestPocket(hx, hz, first) ?? layout.L120NearestPocket(hx, hz, second);
        return pocket is { } p ? layout.L120PocketArrival(p.Hx, p.Hz) : null;
    }

    // ================= The windows, and tripping =================

    private void OnFastTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity is not { Alive: true } entity || player.ConnectionState != EnumClientState.Playing) continue;
            double x = entity.Pos.X, z = entity.Pos.Z;
            if (!InLevel(x, z))
            {
                walked.Remove(player.PlayerUID);
                continue;
            }
            Tile t = layout.TileAt((int)Math.Floor(x), (int)Math.Floor(z));
            if (t.Variant == WorldLayout.L120Window && !Busy(player))
            {
                GoBack(player);
                continue;
            }
            Trip(player, entity, t);
        }
    }

    /// <summary>Through a broken window: back to the terminal that brought them, or the nearest whole one, or anywhere in the level.</summary>
    private void GoBack(IServerPlayer player)
    {
        busyUntil[player.PlayerUID] = sapi.World.ElapsedMilliseconds + BusyMs;
        EntityPlayer entity = player.Entity;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/120/window"), entity, null, true, 16);
        if (entity.WatchedAttributes[BackKey] is ITreeAttribute back)
        {
            thresholds?.L120Carry(player, back.GetDouble("x"), back.GetDouble("y"), back.GetDouble("z"));
            return;
        }
        if (NearestBoot((int)entity.Pos.X, (int)entity.Pos.Z) is { } boot)
        {
            thresholds?.L120Carry(player, boot.X + 0.5, geometry.FloorFor(WorldLayout.Level120) + 1, boot.Z + 0.5);
            return;
        }
        thresholds?.Send(player, WorldLayout.Level120, (ulong)sapi.World.ElapsedMilliseconds, null);
    }

    /// <summary>The tile in front of the nearest whole terminal to a block, in the clusters round it.</summary>
    private (int X, int Z)? NearestBoot(int x, int z, int reach = 4)
    {
        var (hx, hz) = WorldLayout.L120HallOf(x, z);
        (int, int)? best = null;
        long bestD = long.MaxValue;
        // Ring by ring outwards, stopping at the first ring with a whole terminal (each cluster's plan is costly to build)
        for (int ring = 0; ring <= reach && best == null; ring++)
        for (int dz = -ring; dz <= ring; dz++)
            for (int dx = -ring; dx <= ring; dx++)
            {
                if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != ring) continue;
                if (layout.L120KindOf(hx + dx, hz + dz) != Kind.Cluster) continue;
                foreach (var b in layout.L120PlanOf(hx + dx, hz + dz).Boots)
                {
                    long d = (long)(b.X - x) * (b.X - x) + (long)(b.Z - z) * (b.Z - z);
                    if (d < bestD && InLevel(b.X, b.Z)) { bestD = d; best = (b.FrontX, b.FrontZ); }
                }
            }
        return best;
    }

    /// <summary>
    /// "It's easy to trip": running in a Pitch-Black Hallway, about one stretch of eight blocks in six ends with you on the
    /// floor (walking, one in fifty); running over cables in the dark anywhere in the level, one crossing in four. Down,
    /// you are hurt a little and slowed for a moment.
    /// </summary>
    private void Trip(IServerPlayer player, EntityPlayer entity, Tile t)
    {
        double x = entity.Pos.X, z = entity.Pos.Z;
        if (!walked.TryGetValue(player.PlayerUID, out var last)) last = (x, z, 0);
        double step = Math.Sqrt((x - last.X) * (x - last.X) + (z - last.Z) * (z - last.Z));
        if (step > 4) step = 0; // carried somewhere
        double run = last.Run + step;
        bool hallway = t.Zone == (byte)Zone.Hallway, running = Senses.Running(entity), onGround = entity.OnGround;
        bool spill = t.Variant == WorldLayout.L120Spill && running && step > 0.05 && Senses.InDark(entity);
        double chance = 0;
        if (run >= 8)
        {
            if (hallway && onGround && step > 0) chance = running ? 0.17 : 0.02;
            run = 0;
        }
        if (spill && (int)Math.Floor(last.X) != (int)Math.Floor(x) | (int)Math.Floor(last.Z) != (int)Math.Floor(z)) chance = Math.Max(chance, 0.25);
        walked[player.PlayerUID] = (x, z, run);
        if (chance <= 0 || Busy(player) || player.WorldData.CurrentGameMode != EnumGameMode.Survival || rand.NextDouble() >= chance) return;

        busyUntil[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 1500;
        sapi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/120/trip"), entity, null, true, 12);
        entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Fall, Type = EnumDamageType.Gravity }, 1f);
        entity.Stats.Set("walkspeed", "backrooms-l120trip", -0.6f, false);
        sapi.Event.RegisterCallback(_ => entity.Stats.Remove("walkspeed", "backrooms-l120trip"), 1400);
        player.SendIngameError("backrooms-l120-trip", Text(player, "l120-trip"));
        sapi.ModLoader.GetModSystem<MenaceSystem>()?.RaiseNoise(entity.Pos.XYZ, MenaceSystem.FightLoudness, "fall", entity);
    }

    // ================= The Smilers of the White Voids =================

    private bool dummiesSeen;
    private int idleTicks;

    private void OnSlowTick(float dt)
    {
        var who = new List<Entity>();
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
            if (online is IServerPlayer player && player.Entity is { Alive: true } entity && player.ConnectionState == EnumClientState.Playing
                && player.WorldData.CurrentGameMode != EnumGameMode.Spectator) who.Add(entity);
        // (Headless tests: a straw dummy stands in for a player. The scan of every loaded entity runs only with someone in the
        // level or a dummy known, and otherwise now and then to find a first dummy)
        bool anyHere = false;
        foreach (Entity w in who) anyHere |= InLevel(w.Pos.X, w.Pos.Z);
        if (anyHere || dummiesSeen || ++idleTicks % 15 == 0)
        {
            dummiesSeen = false;
            foreach (Entity e in sapi.World.LoadedEntities.Values)
                if (e.Alive && Senses.IsTestTarget(e)) { who.Add(e); dummiesSeen = true; }
        }
        foreach (Entity entity in who)
        {
            if (!InLevel(entity.Pos.X, entity.Pos.Z) || layout.TileAt((int)Math.Floor(entity.Pos.X), (int)Math.Floor(entity.Pos.Z)).Zone != (byte)Zone.Void) continue;
            var (hx, hz) = WorldLayout.L120HallOf((int)Math.Floor(entity.Pos.X), (int)Math.Floor(entity.Pos.Z));
            int want = 1 + (int)(Hashing.Hash((ulong)sapi.World.Seed, hx, hz, SaltBoot + 1) % 3);
            int have = sapi.World.GetEntitiesAround(entity.Pos.XYZ, 48, 8, e => e.Alive && e.Code?.Path == "smiler").Length;
            if (have < want && rand.NextDouble() < 0.35) PutDownSmiler(entity, hx, hz);
        }
    }

    /// <summary>A Smiler standing in one of the void's rooms, out of sight of whoever is there, put down as a wanderer: lost in the light.</summary>
    private void PutDownSmiler(Entity player, int hx, int hz)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(Roster.Smiler));
        if (type == null) return;
        WorldLayout.L120Plan plan = layout.L120PlanOf(hx, hz);
        Vec3d eyes = Senses.Eyes(player);
        for (int tries = 0; tries < 24; tries++)
        {
            int p = rand.Next(WorldLayout.L120HallSize), q = rand.Next(WorldLayout.L120HallSize);
            Tile t = plan.At(p, q);
            if (t.Kind != TileKind.Floor || t.Zone != (byte)Zone.Void || t.Variant != 0) continue;
            var (x, z) = plan.World(p, q);
            var spot = new Vec3d(x + 0.5, geometry.FloorFor(WorldLayout.Level120) + 1, z + 0.5);
            double d = spot.DistanceTo(player.Pos.XYZ);
            if (d < 10 || d > 40 || Senses.ClearLine(sapi.World, eyes, spot.AddCopy(0, 1.2, 0))) continue;
            Entity smiler = sapi.World.ClassRegistry.CreateEntity(type);
            smiler.Pos.SetPos(spot);
            // Facing the nearest panel overhead's room middle: anywhere but at you
            smiler.Pos.Yaw = (float)(rand.NextDouble() * Math.PI * 2);
            EntityBehaviorMenace.Prepare(smiler, player, Encounter.Ambient, passive: true, sapi.World.ElapsedMilliseconds);
            if (player.WatchedAttributes.GetBool("backrooms:testTarget")) smiler.AlwaysActive = true;
            smiler.Attributes.SetDouble(Danger.Key, Danger.OfLevel(WorldLayout.Level120));
            sapi.World.SpawnEntity(smiler);
            Strike.Log(smiler, "put down in a White Void, lost in the light");
            return;
        }
    }

    // ================= Misglitches =================

    private void OnPlayerDeath(IServerPlayer player, DamageSource source)
    {
        EntityPlayer entity = player.Entity;
        if (layout == null || entity == null || !InLevel(entity.Pos.X, entity.Pos.Z)) return;
        // "Red marks where the victim died; all black if the death was internal"
        bool inside = source == null || source.Source is EnumDamageSource.Internal or EnumDamageSource.Suicide or EnumDamageSource.Drown
            || source.Type is EnumDamageType.Hunger or EnumDamageType.Poison or EnumDamageType.Suffocation;
        Entity born = PutDownMisglitch(entity.Pos.XYZ, inside ? 1 : 0, player.PlayerName);
        if (born != null) player.SendMessage(GlobalConstants.GeneralChatGroup, Text(player, "l120-misglitch-born"), EnumChatType.Notification);
    }

    /// <summary>
    /// At most this many Misglitches within 24 blocks of a death (the balance review, 2026-11-01: was six; a Class 2 level's
    /// director allows one to three menacing things at once, and six fast long-reach hunters round a corpse is a death loop).
    /// </summary>
    public const int L120MisglitchCap = 3;

    /// <summary>A Misglitch standing up at a place (look 0 red-marked, 1 all black); null if there are already three about (the balance review: was six) or the type is missing.</summary>
    public Entity PutDownMisglitch(Vec3d at, int look, string of, bool alwaysActive = false)
    {
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(MisglitchCode));
        if (type == null) return null;
        if (sapi.World.GetEntitiesAround(at, 24, 8, e => e.Alive && e.Code?.Path == "l120-misglitch").Length >= L120MisglitchCap) return null;
        Entity e = sapi.World.ClassRegistry.CreateEntity(type);
        double y = Math.Abs(at.Y - Math.Round(at.Y)) < 0.01 ? Math.Round(at.Y) : at.Y;
        e.Pos.SetPos(at.X, y, at.Z);
        e.Pos.Yaw = (float)(rand.NextDouble() * Math.PI * 2);
        e.WatchedAttributes.SetInt("textureIndex", look);
        e.WatchedAttributes.SetString("backrooms:l120Of", of ?? "");
        e.WatchedAttributes.SetDouble(AiTaskMisglitch.HomeKey + "X", at.X);
        e.WatchedAttributes.SetDouble(AiTaskMisglitch.HomeKey + "Y", y);
        e.WatchedAttributes.SetDouble(AiTaskMisglitch.HomeKey + "Z", at.Z);
        e.WatchedAttributes.SetDouble(AiTaskMisglitch.UntilKey, sapi.World.Calendar.TotalHours + 24);
        double danger = Danger.OfLevel(WorldLayout.Level120);
        e.Attributes.SetDouble(Danger.Key, danger);
        // (Headless tests: with no player about nothing would think)
        if (alwaysActive) e.AlwaysActive = true;
        sapi.World.SpawnEntity(e);
        if (e.GetBehavior<EntityBehaviorHealth>() is { } health && Danger.ExtraHealth(danger) > 0)
        {
            health.SetMaxHealthModifiers("backrooms-danger", health.BaseMaxHealth * Danger.ExtraHealth(danger));
            health.Health = health.MaxHealth;
        }
        Strike.Log(e, "stands up where {0} died", of ?? "someone");
        return e;
    }

    // ================= Testing =================

    /// <summary>The newest straw dummy in the world (headless tests), or null.</summary>
    private Entity LatestDummy()
    {
        Entity latest = null;
        foreach (Entity e in sapi.World.LoadedEntities.Values)
            if (e.Alive && Senses.IsTestTarget(e) && (latest == null || e.EntityId > latest.EntityId)) latest = e;
        return latest;
    }

    private TextCommandResult OnCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string what = (string)args[0];
        Entity caller = args.Caller.Entity;
        bool hasXz = !args.Parsers[1].IsMissing && !args.Parsers[2].IsMissing;
        switch (what)
        {
            case "misglitch":
            {
                Vec3d at;
                if (hasXz)
                {
                    int x = (int)args[1], z = (int)args[2];
                    at = new Vec3d(x + 0.5, geometry.FloorFor(WorldLayout.Level120) + 1, z + 0.5);
                }
                else if (caller != null) at = caller.Pos.XYZ;
                else if (LatestDummy() is { } dummy)
                {
                    // (Headless: six blocks along from the latest straw dummy, where the floor is open)
                    at = dummy.Pos.XYZ.AddCopy(6, 0, 0);
                    foreach (var (dx, dz) in new[] { (6, 0), (-6, 0), (0, 6), (0, -6), (4, 4), (-4, -4), (3, 0), (-3, 0) })
                    {
                        var p = new BlockPos((int)Math.Floor(dummy.Pos.X) + dx, (int)Math.Floor(dummy.Pos.Y + 0.05), (int)Math.Floor(dummy.Pos.Z) + dz);
                        if (Senses.Open(sapi.World.BlockAccessor, p) && Senses.Open(sapi.World.BlockAccessor, p.UpCopy()) && !Senses.Open(sapi.World.BlockAccessor, p.DownCopy()))
                        {
                            at = new Vec3d(p.X + 0.5, p.Y, p.Z + 0.5);
                            break;
                        }
                    }
                }
                else return TextCommandResult.Error("From the console, give x and z, or put a straw dummy down first");
                if (!InLevel(at.X, at.Z)) return TextCommandResult.Error("Not in Level 120");
                Entity e = PutDownMisglitch(at, rand.Next(2), args.Caller.Player?.PlayerName ?? "the console", alwaysActive: caller == null);
                // (Put down away from you: it stands turned to you)
                if (e != null && hasXz && caller != null) e.Pos.Yaw = (float)Math.Atan2(caller.Pos.X - at.X, caller.Pos.Z - at.Z);
                return e == null ? TextCommandResult.Error("No Misglitch (its type is missing, or three are already about)") : TextCommandResult.Success($"A Misglitch stands at {at.X:0}, {at.Y:0}, {at.Z:0} (#{e.EntityId})");
            }
            case "void":
            case "hallway":
            {
                if (caller == null && LatestDummy() is { } d)
                {
                    // (Headless: the latest straw dummy is moved into the pocket instead)
                    var (dhx, dhz) = WorldLayout.L120HallOf((int)d.Pos.X, (int)d.Pos.Z);
                    if (layout.L120NearestPocket(dhx, dhz, what == "void" ? Kind.Void : Kind.Hallway, 12) is not { } dp) return TextCommandResult.Error("No such pocket within twelve halls");
                    var (dax, daz) = layout.L120PocketArrival(dp.Hx, dp.Hz);
                    d.TeleportToDouble(dax + 0.5, geometry.FloorFor(WorldLayout.Level120) + 1, daz + 0.5);
                    return TextCommandResult.Success($"The straw dummy is in the {what} of hall {dp.Hx},{dp.Hz} at {dax}, {daz}");
                }
                if (args.Caller.Player is not IServerPlayer player || caller == null) return TextCommandResult.Error("Needs a player, or a straw dummy put down first");
                var (hx, hz) = WorldLayout.L120HallOf((int)caller.Pos.X, (int)caller.Pos.Z);
                var pocket = layout.L120NearestPocket(hx, hz, what == "void" ? Kind.Void : Kind.Hallway, 12);
                if (pocket is not { } p) return TextCommandResult.Error("No such pocket within twelve halls");
                var (ax, az) = layout.L120PocketArrival(p.Hx, p.Hz);
                ITreeAttribute back = new TreeAttribute();
                back.SetDouble("x", caller.Pos.X);
                back.SetDouble("y", caller.Pos.Y);
                back.SetDouble("z", caller.Pos.Z);
                caller.WatchedAttributes[BackKey] = back;
                thresholds?.L120Carry(player, ax + 0.5, geometry.FloorFor(WorldLayout.Level120) + layout.ArrivalHeight(ax, az), az + 0.5);
                return TextCommandResult.Success($"Into the {what} of hall {p.Hx},{p.Hz} at {ax}, {az}");
            }
            case "boot":
            {
                Entity from = caller ?? LatestDummy();
                if (!hasXz && from == null) return TextCommandResult.Error("From the console, give x and z, or put a straw dummy down first");
                int x = hasXz ? (int)args[1] : (int)from.Pos.X, z = hasXz ? (int)args[2] : (int)from.Pos.Z;
                if (NearestBoot(x, z) is not { } b) return TextCommandResult.Error("No whole terminal near");
                string into = PocketOf(b.X, b.Z) is { } a ? $"; it boots into the pocket arriving at {a.X}, {a.Z} ({layout.TileAt(a.X, a.Z).Zone})" : "; it boots into nothing";
                return TextCommandResult.Success($"The nearest whole terminal: stand at {b.X}, {b.Z}{into}");
            }
            case "smiler":
            {
                // A Smiler lost in a White Void's light, at x z (or six blocks in front of you), turned your way
                if (caller == null) return TextCommandResult.Error("Needs a player");
                EntityProperties type = sapi.World.GetEntityType(new AssetLocation(Roster.Smiler));
                if (type == null) return TextCommandResult.Error("No Smiler type");
                double sx = hasXz ? (int)args[1] + 0.5 : caller.Pos.X + Math.Sin(caller.Pos.Yaw) * 6, sz = hasXz ? (int)args[2] + 0.5 : caller.Pos.Z + Math.Cos(caller.Pos.Yaw) * 6;
                if (!InLevel(sx, sz)) return TextCommandResult.Error("Not in Level 120");
                Entity smiler = sapi.World.ClassRegistry.CreateEntity(type);
                smiler.Pos.SetPos(sx, geometry.FloorFor(WorldLayout.Level120) + 1, sz);
                smiler.Pos.Yaw = (float)Math.Atan2(caller.Pos.X - sx, caller.Pos.Z - sz);
                EntityBehaviorMenace.Prepare(smiler, caller, Encounter.Ambient, passive: true, sapi.World.ElapsedMilliseconds);
                smiler.Attributes.SetDouble(Danger.Key, Danger.OfLevel(WorldLayout.Level120));
                sapi.World.SpawnEntity(smiler);
                return TextCommandResult.Success($"A Smiler stands at {sx:0}, {sz:0} (#{smiler.EntityId})");
            }
            case "back":
                if (args.Caller.Player is not IServerPlayer who || who.Entity == null) return TextCommandResult.Error("Needs a player");
                GoBack(who);
                return TextCommandResult.Success("Back through a window");
        }
        return TextCommandResult.Error("misglitch [x z], void, hallway, boot [x z], smiler [x z] or back");
    }
}
