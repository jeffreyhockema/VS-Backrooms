using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using Backrooms.PlayTelemetry;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.Essentials;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// Simulated players (docs/design/testing/plan.md, 2.5): <c>/backrooms walker start &lt;level&gt; [armour] [light] [minutes]</c>
/// puts a straw dummy down at an arrival spot of a level and has it walk a route like a player would, headless, for a
/// stretch of real time: from the arrival to the nearest gate out of the level and through it (or a loop of four
/// waypoints 150 to 300 blocks apart in a level that has no gate), then again from a fresh arrival. It takes the
/// director's encounters as a player does (it is a directed dummy, see <see cref="DirectsDummies"/>), runs when a hunter
/// is within 12 blocks, hides (sneaks, light off) for 20 s when it sees a stalker within 20, eats from the caches it
/// passes, wears an armour tier (the blows it takes are cut by the real items' protection, as <c>armourtest</c> does)
/// and dies at 0 health of its 15, to start again from an arrival. Everything goes to the play telemetry under the
/// dummy's name (<c>strawdummy#id</c>) with the player events' fields, so tools/telemetry/report.py reads it, and
/// the log carries <c>[backrooms] walker ...</c> lines for the harness (tools/aitest/walk.py).
/// </summary>
public partial class MenaceSystem
{
    // The AI's speed units (what a Hunter's walkSpeed is given in): the physics settles at about 140 blocks a second per unit,
    // so 0.025 is a walk of 3.5 blocks a second and 0.05 a run of 7 (a player sprints at about 6.8)
    private const float WalkerWalkSpeed = 0.025f, WalkerRunSpeed = 0.05f;
    private const double WalkerBlocksPerUnit = 140;
    private const double WalkerHunterRange = 12, WalkerStalkerRange = 20, WalkerSeenRange = 24, WalkerCacheRange = 6;
    private const long WalkerHideMs = 20_000, WalkerHideCooldownMs = 60_000;
    private const int WalkerSearchDepth = 30000;

    // The walker's own needs (a player's are vanilla's and ours, see src/Needs; a dummy has none): hunger fills at a cache and runs
    // down in HungerMinutes; starving costs a hit point every 10 s; a rested, fed walker heals 0.1 a second after 8 s without a hurt
    private const double WalkerHungerMinutes = 40, WalkerRegenPerSecond = 0.1, WalkerStarvePerSecond = 0.1;
    private const long WalkerRegenAfterMs = 8_000;

    private static readonly Regex WalkerLootBlock = new(@"supplybox|cache|crate|stash|locker|chest|cabinet|fridge|vending", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private enum WalkPhase { Place, Plan, Walk, Hide, Done }

    private sealed class Walker
    {
        public int Level;
        public string ArmourName = "none", ArmourSet = "none";
        public readonly ProtectionModifiers[] Prot = new ProtectionModifiers[3];
        public int Light = 7;
        public long StartMs, EndMs;
        public Entity Dummy;
        public List<Vec3d> Route;
        public int RouteAt;
        public WalkPhase Phase = WalkPhase.Place;
        public bool WasDirecting, Hooked, Respawn;
        public string LastCause;
        public EntityBehaviorHealth Health;

        public float Hp = 15;
        public double Hunger = 1;
        public long LastHurtMs, LastStarveLogMs;
        public double StarveOwed;

        // Place
        public int Lap, Attempt;
        public long PlaceSince;
        public (int X, int Z)? Spot;
        // Plan and walk
        public readonly List<(int X, int Z)> Legs = new();
        public int LegAt, Replans, Fails;
        public long PlanSince;
        public int Margin = 2;
        public readonly HashSet<long> Loaded = new();
        public bool Arrived, Stuck;
        public bool Running;
        public long HideUntilMs, HideAgainMs;
        public string GateInfo = "";

        // Bookkeeping
        public readonly HashSet<long> Seen = new(), Fled = new();
        public int Hid, Deaths, Caches, Laps, Gates, Stucks;
        public double Blocks;
        public double LastX = double.NaN, LastZ = double.NaN, PosWalked;
        public long NextPosMs, NextStatusMs, NextLootMs, LastTickMs;
        public int LastLevel = int.MinValue;
        public MenaceBand LastBand = (MenaceBand)(-1);
        public readonly List<(int X, int Y, int Z)> Opened = new();
        public readonly Dictionary<string, (int Hits, double Damage)> DamageBy = new();
    }

    private Walker walker;
    private long walkerLogicListener, walkerMoveListener;
    private HashSet<int> lootBlockIds;

    private void RegisterWalkerCommands(ICoreServerAPI api, IChatCommand command)
    {
        var parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("walker")
                .WithDescription("Simulated player for headless sessions: a straw dummy walking a route in a level with health 15, hunger and an armour tier, taking the director's encounters. start, stop, status")
                .BeginSubCommand("start")
                    .WithDescription("Starts the walker. Args: level, armour (none|leather|bronze|iron or a set such as chain-iron; default none), light 0-18 (default 7), minutes (default 120)")
                    .WithArgs(parsers.Word("level"), parsers.OptionalWord("armour"), parsers.OptionalInt("light"), parsers.OptionalInt("minutes"))
                    .HandleWith(OnWalkerStart)
                .EndSubCommand()
                .BeginSubCommand("stop")
                    .WithDescription("Stops the walker and removes its dummy")
                    .HandleWith(_ => walker == null ? TextCommandResult.Success("No walker") : TextCommandResult.Success(FinishWalker("stopped")))
                .EndSubCommand()
                .BeginSubCommand("hit")
                    .WithDescription("Dev test: a blow of the given damage and tier (default 6, 2) on the walker through the entities' own strike path (Strike.Hit), armour and all")
                    .WithArgs(parsers.OptionalDouble("damage"), parsers.OptionalInt("tier"))
                    .HandleWith(args =>
                    {
                        if (walker?.Dummy is not { Alive: true } d) return TextCommandResult.Error("No walker");
                        float damage = args.Parsers[0].IsMissing ? 6 : (float)(double)args[0];
                        Strike.Hit(d, d, damage, EnumDamageType.SlashingAttack, args.Parsers[1].IsMissing ? 2 : (int)args[1], 0);
                        return TextCommandResult.Success(WalkerStatus(walker));
                    })
                .EndSubCommand()
                .BeginSubCommand("status")
                    .WithDescription("Where the walker is and how it has fared")
                    .HandleWith(_ => TextCommandResult.Success(walker == null ? "No walker" : WalkerStatus(walker)))
                .EndSubCommand()
            .EndSubCommand();
    }

    private static string WalkerArmourSet(string tier) => tier switch
    {
        "none" => "none",
        "leather" => "sewn-leather",
        "bronze" => "chain-tinbronze",
        "iron" => "chain-iron",
        _ => tier,
    };

    private void WLog(string text, params object[] args) => sapi.Logger.Notification("[backrooms] walker " + text, args);

    private TextCommandResult OnWalkerStart(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        if (walker != null) return TextCommandResult.Error("A walker is already out (walker stop first)");
        string levelWord = ((string)args[0]).Trim();
        int level = WorldLayout.FromDisplayName(levelWord);
        if (level < 0) return TextCommandResult.Error($"There is no Level {levelWord}");
        var w = new Walker { Level = level };
        w.ArmourName = args.Parsers[1].IsMissing ? "none" : ((string)args[1]).Trim().ToLowerInvariant();
        w.ArmourSet = WalkerArmourSet(w.ArmourName);
        w.Light = args.Parsers[2].IsMissing ? 7 : Math.Clamp((int)args[2], 0, 18);
        int minutes = args.Parsers[3].IsMissing ? 120 : Math.Clamp((int)args[3], 1, 24 * 60);
        var missing = new List<string>();
        if (w.ArmourSet != "none")
        {
            for (int zone = 0; zone < 3; zone++)
            {
                Item item = sapi.World.GetItem(new AssetLocation("game:armor-" + ZoneParts[zone] + "-" + w.ArmourSet));
                if (item == null) missing.Add(ZoneParts[zone]);
                else w.Prot[zone] = item.GetCollectibleInterface<IWearableStatsSupplier>()?.GetProtectionModifiers(new DummySlot(new ItemStack(item)));
            }
            if (missing.Count == 3) return TextCommandResult.Error("No such armour: " + w.ArmourSet + " (none, leather, bronze, iron, or a set like chain-iron)");
        }
        w.StartMs = sapi.World.ElapsedMilliseconds;
        w.EndMs = w.StartMs + minutes * 60_000L;
        w.WasDirecting = DirectsDummies;
        DirectsDummies = true;
        walker = w;
        walkerLogicListener = sapi.Event.RegisterGameTickListener(WalkerLogic, e => sapi.Logger.Error("[backrooms] walker: {0}", e), 250, 250);
        walkerMoveListener = sapi.Event.RegisterGameTickListener(WalkerMove, e => sapi.Logger.Error("[backrooms] walker move: {0}", e), 25, 25);
        string text = string.Format(CultureInfo.InvariantCulture, "walker starting: Level {0}, armour {1} ({2}{3}), light {4}, {5} minutes",
            WorldLayout.DisplayNumber(level), w.ArmourName, w.ArmourSet, missing.Count > 0 ? ", bare: " + string.Join("/", missing) : "", w.Light, minutes);
        WLog(text.Substring("walker ".Length));
        return TextCommandResult.Success(text);
    }

    /// <summary>Ends the walk: the last status line, the telemetry's end event, the dummy removed. Returns the status line.</summary>
    private string FinishWalker(string why)
    {
        Walker w = walker;
        if (w == null) return "No walker";
        string status = WalkerStatus(w);
        Telemetry.Log("walker", w.Dummy, "state", "end", "why", why, "deaths", w.Deaths, "blocks", w.Blocks, "caches", w.Caches, "laps", w.Laps, "gates", w.Gates,
            "seen", w.Seen.Count, "fled", w.Fled.Count, "hid", w.Hid, "hp", w.Hp, "hunger", w.Hunger);
        WLog("final ({0}): {1}", why, status);
        walker = null;
        w.Phase = WalkPhase.Done;
        sapi.Event.UnregisterGameTickListener(walkerLogicListener);
        sapi.Event.UnregisterGameTickListener(walkerMoveListener);
        walkerLogicListener = walkerMoveListener = 0;
        w.Route = null;
        if (w.Dummy != null)
        {
            dummies.Remove(w.Dummy);
            if (w.Dummy.Alive) w.Dummy.Die(EnumDespawnReason.Removed);
        }
        DirectsDummies = w.WasDirecting;
        foreach (long key in w.Loaded) sapi.WorldManager.UnloadChunkColumn((int)(key >> 32), (int)(key & 0xFFFFFFFF));
        return status;
    }

    private string WalkerStatus(Walker w)
    {
        Entity d = w.Dummy;
        Assessment a = d == null ? null : AssessmentOf(d);
        long left = Math.Max(0, w.EndMs - sapi.World.ElapsedMilliseconds);
        return string.Format(CultureInfo.InvariantCulture,
            "status: Level {0}, phase {1}, at {2:0} {3:0} {4:0}, band {5}, hp {6:0.0}/15, hunger {7:0}%, armour {8}, light {9}, {10:0.0} min left; encounters seen {11} fled {12} hid {13} died {14}; blocks walked {15:0}, caches {16}, laps {17}, gates {18}, stuck {19}",
            a == null ? WorldLayout.DisplayNumber(w.Level) : WorldLayout.DisplayNumber(a.Level), w.Phase, d?.Pos.X ?? 0, d?.Pos.Y ?? 0, d?.Pos.Z ?? 0, a?.Band, w.Hp, w.Hunger * 100, w.ArmourName,
            w.Light, left / 60000.0, w.Seen.Count, w.Fled.Count, w.Hid, w.Deaths, w.Blocks, w.Caches, w.Laps, w.Gates, w.Stucks);
    }

    // ================= The traverser's tick =================

    /// <summary>
    /// Walks the dummy along its route. The game's physics (and so the path traverser) only tick entities a connected client
    /// is near, and a headless server has none, so the position is set here: along the A* waypoints at the walk's speed, the
    /// feet following the waypoints' heights, facing the way it goes. The pathfinder's grid already keeps to the floor.
    /// </summary>
    private void WalkerMove(float dt)
    {
        Walker w = walker;
        if (w?.Route == null || w.Phase != WalkPhase.Walk || w.Dummy is not { Alive: true } d) return;
        dt = Math.Min(dt, 0.2f);
        double reach = WalkSpeedNow(w) * WalkerBlocksPerUnit * dt;
        EntityPos pos = d.Pos;
        while (reach > 0 && w.RouteAt < w.Route.Count)
        {
            Vec3d to = w.Route[w.RouteAt];
            double dx = to.X - pos.X, dz = to.Z - pos.Z, dy = to.Y - pos.Y;
            double flat = Math.Sqrt(dx * dx + dz * dz);
            if (flat < 1e-4 && Math.Abs(dy) < 0.05) { w.RouteAt++; continue; }
            double go = Math.Min(flat, reach);
            if (flat > 1e-4)
            {
                pos.X += dx / flat * go;
                pos.Z += dz / flat * go;
                pos.Yaw = (float)Math.Atan2(dx, dz);
            }
            // (The feet follow the path's heights: up a step or down a drop as it goes)
            double rise = flat < 1e-4 ? dy : dy * (go / flat);
            pos.Y += Math.Abs(rise) > Math.Abs(dy) ? dy : rise;
            reach -= go;
            if (go >= flat - 1e-6) w.RouteAt++;
            else break;
        }
        pos.Motion.Set(0, 0, 0);
        if (w.RouteAt >= w.Route.Count)
        {
            w.Route = null;
            w.Arrived = true;
        }
    }

    // ================= The logic, four times a second =================

    private void WalkerLogic(float dt)
    {
        Walker w = walker;
        if (w == null) return;
        long now = sapi.World.ElapsedMilliseconds;
        if (now >= w.EndMs) { FinishWalker("time"); return; }
        if (w.NextStatusMs == 0) w.NextStatusMs = now + 60_000;
        if (now >= w.NextStatusMs)
        {
            w.NextStatusMs = now + 60_000;
            WLog(WalkerStatus(w));
        }
        float seconds = w.LastTickMs == 0 ? 0.25f : Math.Min(2f, (now - w.LastTickMs) / 1000f);
        w.LastTickMs = now;

        if (w.Dummy != null && !w.Dummy.Alive)
        {
            // (Something else killed the dummy: a fall, the void)
            dummies.Remove(w.Dummy);
            WalkerDied(w, "dummy-lost", now, replaceDummy: true);
            return;
        }
        switch (w.Phase)
        {
            case WalkPhase.Place: WalkerPlace(w, now); break;
            case WalkPhase.Plan: WalkerPlan(w, now); Living(w, now, seconds); break;
            case WalkPhase.Walk:
            case WalkPhase.Hide: WalkerWalk(w, now); Living(w, now, seconds); break;
        }
    }

    private void LoadColumns(Walker w, int x0, int z0, int x1, int z1)
    {
        for (int cz = Math.Min(z0, z1) / 32 - (Math.Min(z0, z1) < 0 ? 1 : 0); cz <= Math.Max(z0, z1) / 32; cz++)
            for (int cx = Math.Min(x0, x1) / 32 - (Math.Min(x0, x1) < 0 ? 1 : 0); cx <= Math.Max(x0, x1) / 32; cx++)
            {
                if (!w.Loaded.Add(((long)cx << 32) | (uint)cz)) continue;
                sapi.WorldManager.LoadChunkColumn(cx, cz, true);
            }
    }

    private bool ColumnsReady(int x0, int z0, int x1, int z1, int probeY)
    {
        for (int cz = Math.Min(z0, z1) / 32 - (Math.Min(z0, z1) < 0 ? 1 : 0); cz <= Math.Max(z0, z1) / 32; cz++)
            for (int cx = Math.Min(x0, x1) / 32 - (Math.Min(x0, x1) < 0 ? 1 : 0); cx <= Math.Max(x0, x1) / 32; cx++)
                if (sapi.World.BlockAccessor.GetChunkAtBlockPos(cx * 32 + 1, probeY, cz * 32 + 1) == null) return false;
        return true;
    }

    // ---------------- Place: an arrival spot (a new lap, or a respawn)

    private void WalkerPlace(Walker w, long now)
    {
        if (w.Spot == null)
        {
            ulong key = (ulong)(w.Lap * 7919L + w.Attempt * 31L + 17);
            w.Attempt++;
            if (layout.FindArrival(w.Level, key) is not { } spot)
            {
                if (w.Attempt > 24) FinishWalker("no arrival spot in the level");
                return;
            }
            w.Spot = spot;
            w.PlaceSince = now;
            // (Forget the last lap's columns, now that the walker is to be somewhere else)
            foreach (long old in w.Loaded.ToList())
            {
                int cx = (int)(old >> 32), cz = (int)(old & 0xFFFFFFFF);
                if (Math.Abs(cx - spot.X / 32) <= 2 && Math.Abs(cz - spot.Z / 32) <= 2) continue;
                if (w.Dummy != null && w.Dummy.Alive && Math.Abs(cx - (int)w.Dummy.Pos.X / 32) <= 1 && Math.Abs(cz - (int)w.Dummy.Pos.Z / 32) <= 1) continue;
                w.Loaded.Remove(old);
                sapi.WorldManager.UnloadChunkColumn(cx, cz);
            }
        }
        (int x, int z) = w.Spot.Value;
        int y = geometry.FloorFor(w.Level) + 1;
        LoadColumns(w, x - 64, z - 64, x + 64, z + 64);
        if (!ColumnsReady(x - 64, z - 64, x + 64, z + 64, y))
        {
            if (now - w.PlaceSince > 90_000) { WLog("arrival spot {0},{1} did not load in 90 s: another", x, z); w.Spot = null; }
            return;
        }
        if (w.Dummy == null || !w.Dummy.Alive)
        {
            Entity dummy = SpawnDummy(x, y, z, out string why);
            if (dummy == null)
            {
                if (why != null && !why.Contains("loading")) { WLog("could not put the dummy down at {0},{1}: {2}", x, z, why); w.Spot = null; }
                return;
            }
            w.Dummy = dummy;
            w.Hooked = false;
                dummies.Add(dummy);
        }
        else
        {
            int floor = Senses.FindFloor(sapi.World, x, y, z, 2, 8);
            if (floor == int.MinValue) { WLog("no floor at the arrival spot {0},{1}: another", x, z); w.Spot = null; return; }
            w.Route = null;
            w.Dummy.TeleportToDouble(x + 0.5, floor, z + 0.5);
        }
        Entity d = w.Dummy;
        d.WatchedAttributes.SetBool(Senses.TestSneakKey, false);
        d.WatchedAttributes.SetBool(Senses.TestRunKey, false);
        d.WatchedAttributes.SetInt(Senses.TestLightKey, w.Light);
        w.Running = false;
        if (!watches.TryGetValue(d.EntityId, out Watch watch)) watches[d.EntityId] = watch = new Watch();
        Assess(d, watch);
        w.LastX = d.Pos.X;
        w.LastZ = d.Pos.Z;
        w.LastLevel = int.MinValue;
        w.NextPosMs = 0;
        w.Legs.Clear();
        w.LegAt = w.Replans = w.Fails = 0;
        w.Margin = 2;
        w.PlanSince = now;
        w.Arrived = w.Stuck = false;
        w.Spot = null;
        w.Attempt = 0;
        w.Phase = WalkPhase.Plan;
        if (w.Respawn) Telemetry.Log("respawn", d, "level", WorldLayout.DisplayNumber(watch.Now.Level), "x", d.Pos.X, "z", d.Pos.Z, "lap", w.Lap);
        else if (w.Lap == 0) Telemetry.Log("walker", d, "state", "start", "level", WorldLayout.DisplayNumber(w.Level), "armour", w.ArmourName, "set", w.ArmourSet, "light", w.Light, "minutes", (w.EndMs - w.StartMs) / 60000.0);
        else Telemetry.Log("walker", d, "state", "arrive", "lap", w.Lap, "level", WorldLayout.DisplayNumber(watch.Now.Level), "x", d.Pos.X, "z", d.Pos.Z);
        w.Respawn = false;
        w.Hp = 15;
        WLog("placed #{0} at {1:0} {2:0} {3:0} (Level {4}, lap {5})", d.EntityId, d.Pos.X, d.Pos.Y, d.Pos.Z, WorldLayout.DisplayNumber(watch.Now.Level), w.Lap);
    }

    // ---------------- Plan: the legs of the route, and a path to the next

    /// <summary>The route of a lap: the nearest gate out of the level and through it, else a loop of four waypoints 150 to 300 blocks apart.</summary>
    private void WalkerRoute(Walker w)
    {
        Entity d = w.Dummy;
        int sx = (int)Math.Floor(d.Pos.X), sz = (int)Math.Floor(d.Pos.Z);
        w.Legs.Clear();
        w.LegAt = 0;
        w.GateInfo = "";
        var gates = layout.GatesNear(sx, sz, w.Level, 500).OrderBy(g => (long)(g.X - sx) * (g.X - sx) + (long)(g.Z - sz) * (g.Z - sz)).ToList();
        if (gates.Count > 0)
        {
            // (Each failure to find a way moves on to the next gate)
            var gate = gates[Math.Min(w.Fails, gates.Count - 1)];
            // Through it: a few blocks on, in the direction of the level beyond
            (int dx, int dz)[] dirs = { (1, 0), (-1, 0), (0, 1), (0, -1) };
            foreach (var (dx, dz) in dirs)
            {
                if (layout.LevelAt(WorldLayout.MacroOf(gate.X + dx * 10), WorldLayout.MacroOf(gate.Z + dz * 10)) != gate.To) continue;
                w.Legs.Add((gate.X + dx * 8, gate.Z + dz * 8));
                break;
            }
            if (w.Legs.Count == 0) w.Legs.Add((gate.X, gate.Z));
            w.GateInfo = $"gate at {gate.X},{gate.Z} to Level {WorldLayout.DisplayNumber(gate.To)}";
            return;
        }
        // No gate: four waypoints in this level
        var rng = new Random(unchecked(sx * 73856093 ^ sz * 19349663 ^ w.Lap * 83492791 ^ w.Fails));
        int px = sx, pz = sz;
        for (int leg = 0; leg < 4; leg++)
        {
            for (int tries = 0; tries < 40; tries++)
            {
                double angle = rng.NextDouble() * Math.PI * 2, dist = 150 + rng.NextDouble() * 150;
                int x = px + (int)(Math.Cos(angle) * dist), z = pz + (int)(Math.Sin(angle) * dist);
                if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != w.Level) continue;
                w.Legs.Add((x, z));
                (px, pz) = (x, z);
                break;
            }
        }
        w.GateInfo = "loop of " + w.Legs.Count + " waypoints";
    }

    private void WalkerPlan(Walker w, long now)
    {
        Entity d = w.Dummy;
        if (w.Legs.Count == 0)
        {
            WalkerRoute(w);
            WLog("route: {0}", w.GateInfo);
            if (w.Legs.Count == 0) { WalkerLapOver(w, "no route"); return; }
            w.PlanSince = now;
        }
        if (w.LegAt >= w.Legs.Count) { WalkerLapOver(w, "route done"); return; }
        PathfindSystem psys = sapi.ModLoader.GetModSystem<PathfindSystem>();
        if (psys == null) { FinishWalker("no pathfinder"); return; }

        (int gx, int gz) = w.Legs[w.LegAt];
        int sx = (int)Math.Floor(d.Pos.X), sz = (int)Math.Floor(d.Pos.Z);
        int sy = Senses.FindFloor(sapi.World, sx, (int)Math.Round(d.Pos.Y), sz, 3, 3);
        int goalLevel = layout.LevelAt(WorldLayout.MacroOf(gx), WorldLayout.MacroOf(gz));
        int probeY = (sy == int.MinValue ? (int)d.Pos.Y : sy);
        // Columns over the area between, with a margin (the path may wind); the first tries only start the loading
        int pad = w.Margin * 32;
        int x0 = Math.Min(sx, gx) - pad, x1 = Math.Max(sx, gx) + pad, z0 = Math.Min(sz, gz) - pad, z1 = Math.Max(sz, gz) + pad;
        if ((x1 - x0) / 32 > 40 || (z1 - z0) / 32 > 40) { w.Fails++; WalkerNextLeg(w, "too far apart"); return; }
        LoadColumns(w, x0, z0, x1, z1);
        if (!ColumnsReady(x0, z0, x1, z1, probeY))
        {
            if (now - w.PlanSince > 180_000) { WLog("chunks for the leg did not load in 180 s"); w.Fails++; w.PlanSince = now; WalkerNextLeg(w, "chunks"); }
            return;
        }
        int gy = Senses.FindFloor(sapi.World, gx, geometry.FloorFor(goalLevel) + 1, gz, 2, 8);
        if (sy == int.MinValue || gy == int.MinValue)
        {
            WLog("no floor at the {0} of the leg", sy == int.MinValue ? "start" : "end " + gx + "," + gz);
            w.Fails++;
            WalkerNextLeg(w, "no floor");
            return;
        }
        float step = d.GetBehavior<EntityBehaviorControlledPhysics>()?.StepHeight ?? 0.6f;
        List<Vec3d> waypoints = psys.FindPathAsWaypoints(new BlockPos(sx, sy, sz), new BlockPos(gx, gy, gz), -1f, 4, step, d.CollisionBox, WalkerSearchDepth, 1, EnumAICreatureType.LandCreature);
        if (waypoints == null || waypoints.Count == 0)
        {
            w.PlanSince = now;
            if (w.Margin < 4) { w.Margin += 2; WLog("no way to {0},{1} yet: wider columns ({2} nodes searched)", gx, gz, psys.astar.NodesChecked); return; }
            WLog("no way from {0},{1} to {2},{3} ({4} nodes searched)", sx, sz, gx, gz, psys.astar.NodesChecked);
            w.Fails++;
            w.Margin = 2;
            WalkerNextLeg(w, "no path");
            return;
        }
        w.Replans++;
        w.Arrived = w.Stuck = false;
        w.Route = waypoints;
        w.RouteAt = 0;
        w.Phase = WalkPhase.Walk;
        WLog("leg {0}/{1} to {2},{3}: {4} waypoints for {5:0} blocks as the crow flies", w.LegAt + 1, w.Legs.Count, gx, gz, waypoints.Count, Math.Sqrt((double)(gx - sx) * (gx - sx) + (double)(gz - sz) * (gz - sz)));
    }

    /// <summary>The leg could not be walked: the next leg (a loop), or another gate/loop after too many failures, or a fresh arrival.</summary>
    private void WalkerNextLeg(Walker w, string why)
    {
        w.Margin = 2;
        if (w.Fails >= 4) { WalkerLapOver(w, "gave up (" + why + ")"); return; }
        // (Start the route over: the next gate, or a different loop)
        w.Legs.Clear();
    }

    private void WalkerLapOver(Walker w, string why)
    {
        WLog("lap {0} over: {1}", w.Lap, why);
        Telemetry.Log("walker", w.Dummy, "state", "lap", "lap", w.Lap, "why", why, "blocks", w.Blocks);
        w.Lap++;
        w.Laps++;
        w.Fails = 0;
        w.Spot = null;
        w.Attempt = 0;
        w.Route = null;
        w.Phase = WalkPhase.Place;
    }

    private float WalkSpeedNow(Walker w) => w.Running ? WalkerRunSpeed : WalkerWalkSpeed;

    // ---------------- Walk and hide

    private void WalkerWalk(Walker w, long now)
    {
        Entity d = w.Dummy;
        if (w.Phase == WalkPhase.Hide)
        {
            if (now < w.HideUntilMs) return;
            // Up again: the light back, and the route from where it stands
            d.WatchedAttributes.SetBool(Senses.TestSneakKey, false);
            d.WatchedAttributes.SetInt(Senses.TestLightKey, w.Light);
            w.HideAgainMs = now + WalkerHideCooldownMs;
            w.Phase = WalkPhase.Plan;
            w.PlanSince = now;
            WLog("comes out of hiding");
            return;
        }
        if (w.Arrived)
        {
            w.Arrived = false;
            if (watches.TryGetValue(d.EntityId, out Watch here)) Assess(d, here);
            Assessment a = AssessmentOf(d);
            if (w.GateInfo.StartsWith("gate", StringComparison.Ordinal) && a.Level != w.Level) w.Gates++;
            WLog("leg {0} done at {1:0} {2:0} {3:0}, Level {4}", w.LegAt + 1, d.Pos.X, d.Pos.Y, d.Pos.Z, WorldLayout.DisplayNumber(a.Level));
            Telemetry.Log("walker", d, "state", "leg", "leg", w.LegAt, "level", WorldLayout.DisplayNumber(a.Level), "info", w.GateInfo);
            w.LegAt++;
            w.Phase = WalkPhase.Plan;
            w.PlanSince = now;
            w.Replans = 0;
            return;
        }
        if (w.Stuck)
        {
            w.Stuck = false;
            w.Stucks++;
            w.Replans++;
            WLog("stuck at {0:0} {1:0} {2:0} (replan {3})", d.Pos.X, d.Pos.Y, d.Pos.Z, w.Replans);
            if (w.Replans > 3)
            {
                // (A spot it cannot get out of: on to the next leg, or a fresh arrival)
                w.Replans = 0;
                w.Fails++;
                w.LegAt++;
            }
            w.Phase = WalkPhase.Plan;
            w.PlanSince = now;
            return;
        }
        // (The traverser ended without either callback: pick the route up again)
        if (w.Route == null) { w.Phase = WalkPhase.Plan; w.PlanSince = now; }
    }

    // ---------------- Living: threats, needs, loot, telemetry

    private void Living(Walker w, long now, float seconds)
    {
        Entity d = w.Dummy;
        if (d == null || !d.Alive) return;
        HookWalkerDamage(w);

        // Who is about: hunters within 12 make it run, a stalker it sees within 20 makes it hide
        double hunter = double.MaxValue, stalker = double.MaxValue;
        Vec3d eyes = Senses.Eyes(d);
        foreach (Entity e in sapi.World.GetEntitiesAround(d.Pos.XYZ, (float)WalkerSeenRange, 12, e => e.Alive && e.GetBehavior<EntityBehaviorMenace>() != null))
        {
            Encounter kind = EntityBehaviorMenace.KindOf(e);
            double dist = e.Pos.DistanceTo(d.Pos.XYZ);
            if (kind is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Search && w.Seen.Count < 5000) w.Seen.Add(e.EntityId);
            if (kind is Encounter.Hunt or Encounter.Search && dist < hunter) hunter = dist;
            else if (kind == Encounter.Stalk && dist < stalker && Senses.ClearLine(sapi.World, eyes, Senses.Centre(e))) stalker = dist;
        }
        bool run = hunter <= WalkerHunterRange && w.Phase != WalkPhase.Hide;
        if (hunter <= WalkerHunterRange)
        {
            foreach (Entity e in sapi.World.GetEntitiesAround(d.Pos.XYZ, (float)WalkerHunterRange, 12, e => e.Alive && e.GetBehavior<EntityBehaviorMenace>() is { } && EntityBehaviorMenace.KindOf(e) is Encounter.Hunt or Encounter.Search))
                if (w.Fled.Add(e.EntityId)) { Telemetry.Log("walker", d, "state", "flee", "code", e.Code.Path, "dist", e.Pos.DistanceTo(d.Pos.XYZ)); WLog("runs from {0} #{1} ({2:0.0} blocks)", e.Code.Path, e.EntityId, e.Pos.DistanceTo(d.Pos.XYZ)); }
        }
        if (run != w.Running)
        {
            w.Running = run;
            d.WatchedAttributes.SetBool(Senses.TestRunKey, run);
        }
        if (w.Phase == WalkPhase.Walk && stalker <= WalkerStalkerRange && hunter > WalkerHunterRange && now >= w.HideAgainMs)
        {
            w.Phase = WalkPhase.Hide;
            w.HideUntilMs = now + WalkerHideMs;
            w.Hid++;
            d.WatchedAttributes.SetBool(Senses.TestSneakKey, true);
            d.WatchedAttributes.SetInt(Senses.TestLightKey, 0);
            d.WatchedAttributes.SetBool(Senses.TestRunKey, false);
            w.Running = false;
            Telemetry.Log("walker", d, "state", "hide", "dist", stalker);
            WLog("hides from a stalker ({0:0.0} blocks) for 20 s", stalker);
        }

        // Hunger and health
        w.Hunger = Math.Max(0, w.Hunger - seconds / (WalkerHungerMinutes * 60));
        if (w.Hunger <= 0)
        {
            w.StarveOwed += WalkerStarvePerSecond * seconds;
            if (w.StarveOwed >= 1 || w.StarveOwed > 0 && now - w.LastStarveLogMs > 10_000)
            {
                float amount = (float)w.StarveOwed;
                w.StarveOwed = 0;
                w.LastStarveLogMs = now;
                WalkerHurt(w, amount, "hunger", EnumDamageType.Hunger, now);
            }
        }
        else if (w.Hp < 15 && w.Hunger > 0.2 && now - w.LastHurtMs > WalkerRegenAfterMs) w.Hp = Math.Min(15, w.Hp + (float)(WalkerRegenPerSecond * seconds));
        if (w.Hp <= 0) { WalkerDied(w, w.LastCause ?? "unknown", now, replaceDummy: false); return; }

        // Caches within reach: opened, and eaten from
        if (now >= w.NextLootMs) { w.NextLootMs = now + 1000; ScanCaches(w, d); }

        // Where it is: blocks walked, level and band changes, a position every 30 s
        double x = d.Pos.X, z = d.Pos.Z;
        if (!double.IsNaN(w.LastX))
        {
            double step = Math.Sqrt((x - w.LastX) * (x - w.LastX) + (z - w.LastZ) * (z - w.LastZ));
            if (step < 20) { w.Blocks += step; w.PosWalked += step; }
        }
        w.LastX = x;
        w.LastZ = z;
        if (!watches.TryGetValue(d.EntityId, out Watch watch)) return;
        Assessment now_ = watch.Now;
        string display = WorldLayout.DisplayNumber(now_.Level);
        if (now_.Level != w.LastLevel)
        {
            string from = w.LastLevel == int.MinValue ? "" : WorldLayout.DisplayNumber(w.LastLevel);
            Telemetry.Log("level", d, "from", from, "to", display, "band", now_.Band, "class", WorldLayout.SurvivalClass(now_.Level), "x", x, "z", z);
            w.LastLevel = now_.Level;
            w.LastBand = now_.Band;
        }
        else if (now_.Band != w.LastBand)
        {
            Telemetry.Log("band", d, "level", display, "from", w.LastBand < 0 ? "" : w.LastBand.ToString(), "to", now_.Band, "value", now_.Value);
            w.LastBand = now_.Band;
        }
        if (now >= w.NextPosMs)
        {
            w.NextPosMs = now + 30_000;
            Telemetry.Log("pos", d, "x", x, "z", z, "level", display, "band", now_.Band, "d", w.PosWalked, "gm", "Survival", "hp", w.Hp, "hunger", w.Hunger);
            w.PosWalked = 0;
        }
    }

    private void ScanCaches(Walker w, Entity d)
    {
        if (lootBlockIds == null)
        {
            lootBlockIds = new HashSet<int>();
            foreach (Block b in sapi.World.Blocks)
                if (b?.Code != null && b.Code.Domain == "backrooms" && WalkerLootBlock.IsMatch(b.Code.Path)) lootBlockIds.Add(b.BlockId);
        }
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var pos = new BlockPos(0);
        int cx = (int)Math.Floor(d.Pos.X), cy = (int)Math.Floor(d.Pos.Y), cz = (int)Math.Floor(d.Pos.Z);
        int r = (int)WalkerCacheRange;
        for (int dy = -1; dy <= 2; dy++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (dx * dx + dz * dz > r * r) continue;
                    pos.Set(cx + dx, cy + dy, cz + dz);
                    int id = ba.GetBlockId(pos);
                    if (id == 0 || !lootBlockIds.Contains(id)) continue;
                    // (A stack of crates, or the open and shut halves of one, is one cache: nothing opened within 3 blocks)
                    bool again = false;
                    foreach (var (ox, oy, oz) in w.Opened)
                        if (Math.Abs(ox - pos.X) <= 3 && Math.Abs(oy - pos.Y) <= 3 && Math.Abs(oz - pos.Z) <= 3) { again = true; break; }
                    if (again) continue;
                    string key = pos.X + "," + pos.Y + "," + pos.Z;
                    w.Opened.Add((pos.X, pos.Y, pos.Z));
                    w.Caches++;
                    w.Hunger = 1;
                    string block = ba.GetBlock(id).Code.Path;
                    Telemetry.Log("loot", d, "block", block, "how", "open", "level", WorldLayout.DisplayNumber(AssessmentOf(d).Level));
                    Telemetry.Log("eat", d, "item", "cache-ration", "satiety", 1);
                    WLog("opens {0} at {1} and eats", block, key);
                    if (w.Opened.Count > 4000) w.Opened.Clear();
                }
    }

    // ---------------- Damage

    private void HookWalkerDamage(Walker w)
    {
        if (w.Hooked) return;
        EntityBehaviorHealth health = w.Dummy.GetBehavior<EntityBehaviorHealth>();
        if (health == null) return;
        w.Hooked = true;
        w.Health = health;
        // (The dummy's own hundred health points are never touched: the walker's fifteen are its own, kept here)
        health.onDamaged += (damage, source) =>
        {
            if (walker != w || damage <= 0 || source == null || source.Type == EnumDamageType.Heal) return damage;
            if (w.Phase == WalkPhase.Place) return 0; // (between lives: nothing lands)
            Entity by = source.GetCauseEntity();
            float taken = damage;
            // The blow lands on the head, body or legs, and only that piece protects (flat, then relative), as armourtest says
            if (source.Type is EnumDamageType.BluntAttack or EnumDamageType.SlashingAttack or EnumDamageType.PiercingAttack
                && source.Source != EnumDamageSource.Internal && source.Source != EnumDamageSource.Suicide)
            {
                double roll = sapi.World.Rand.NextDouble();
                int zone = roll < HitZones[0] ? 0 : roll < HitZones[0] + HitZones[1] ? 1 : 2;
                taken = AfterPiece(damage, source.DamageTier, w.Prot[zone]);
            }
            WalkerHurt(w, taken, by != null ? by.Code.Path : source.Type.ToString(), source.Type, sapi.World.ElapsedMilliseconds, damage);
            return 0;
        };
    }

    private void WalkerHurt(Walker w, float taken, string cause, EnumDamageType type, long now, float raw = -1)
    {
        if (taken < 0) return;
        w.Hp -= taken;
        w.LastHurtMs = now;
        w.LastCause = cause;
        w.DamageBy.TryGetValue(cause, out var sum);
        w.DamageBy[cause] = (sum.Hits + 1, sum.Damage + taken);
        Telemetry.Log("damage", w.Dummy, "src", cause, "type", type, "amount", taken, "raw", raw < 0 ? taken : raw, "hp", Math.Max(0, w.Hp), "armour", w.ArmourName);
        if (Logging) WLog("takes {0:0.0} from {1} (raw {2:0.0}), hp {3:0.0}", taken, cause, raw < 0 ? taken : raw, Math.Max(0, w.Hp));
    }

    private void WalkerDied(Walker w, string cause, long now, bool replaceDummy)
    {
        Assessment a = w.Dummy == null ? null : AssessmentOf(w.Dummy);
        Telemetry.Log("death", w.Dummy, "cause", cause, "level", a == null ? "" : WorldLayout.DisplayNumber(a.Level), "band", a?.Band, "x", w.Dummy?.Pos.X ?? 0, "z", w.Dummy?.Pos.Z ?? 0);
        WLog("dies of {0} at {1:0} {2:0} (death {3})", cause, w.Dummy?.Pos.X ?? 0, w.Dummy?.Pos.Z ?? 0, w.Deaths + 1);
        w.Deaths++;
        w.Hp = 15;
        w.Hunger = Math.Max(w.Hunger, 0.5);
        w.LastCause = null;
        w.Respawn = true;
        w.StarveOwed = 0;
        w.Route = null;
        if (replaceDummy) w.Dummy = null;
        w.Lap++;
        w.Spot = null;
        w.Attempt = 0;
        w.Fails = 0;
        w.Phase = WalkPhase.Place;
    }
}
