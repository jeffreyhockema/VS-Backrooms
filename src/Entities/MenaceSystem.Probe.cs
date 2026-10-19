using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// The director's ears and test bench: the noises the engine only ever sends to players (doors, Firesalt lit, a
/// thrown stone landing, a jump), put on the noise bus; what the director costs; and the perception probes
/// (<c>/backrooms perceive</c>, <c>/backrooms dummy ...</c>) that show what an entity sees, hears and believes.
/// See docs/design/entity-ai-overhaul/README.md, sections 4.2 and 4.5.
/// </summary>
public partial class MenaceSystem
{
    // ================= Listening =================

    /// <summary>Who was holding jump at the last look (player entity id), to hear each jump once.</summary>
    private readonly Dictionary<long, bool> jumping = new();

    /// <summary>Thrown stones, arrows and the like in the air: where each was last, how many looks it has lain still, and since when it flies.</summary>
    private readonly List<(Entity Thing, Vec3d Last, int Still, long Since)> inFlight = new();

    private const int ListenMs = 200;
    private const long FlightGiveUpMs = 15_000;

    private void StartListening(ICoreServerAPI api)
    {
        api.Event.DidUseBlock += OnUsedBlock;
        api.Event.DidPlaceBlock += OnPlacedBlock;
        api.Event.OnEntitySpawn += OnSpawned;
        api.Event.RegisterGameTickListener(Listen, e => api.Logger.Error("[backrooms] entity director (listening): {0}", e), ListenMs, 500);
    }

    /// <summary>A door opened or shut: heard down the hall, unless it was done quietly (sneaking).</summary>
    private void OnUsedBlock(IServerPlayer player, BlockSelection sel)
    {
        if (player?.Entity == null || sel?.Position == null) return;
        Block block = sapi.World.BlockAccessor.GetBlock(sel.Position);
        if (block?.GetBehavior<BlockBehaviorDoor>() == null) return;
        RaiseNoise(sel.Position.ToVec3d().Add(0.5, 1, 0.5), Senses.Sneaking(player.Entity) ? QuietDoorLoudness : DoorLoudness, "door", player.Entity);
    }

    /// <summary>Firesalt set down catches at once, with a crackle.</summary>
    private void OnPlacedBlock(IServerPlayer player, int oldBlockId, BlockSelection sel, ItemStack stack)
    {
        if (player?.Entity == null || sel?.Position == null) return;
        AssetLocation code = stack?.Collectible?.Code;
        if (code == null || code.Domain != "backrooms" || !code.Path.StartsWith("firesalt")) return;
        RaiseNoise(sel.Position.ToVec3d().Add(0.5, 0.5, 0.5), FireLoudness, "fire", player.Entity);
    }

    private void OnSpawned(Entity entity)
    {
        if (entity is IProjectile && layout != null) inFlight.Add((entity, entity.Pos.XYZ, 0, sapi.World.ElapsedMilliseconds));
    }

    /// <summary>Every fifth of a second: jumps, and anything thrown coming down.</summary>
    private void Listen(float dt)
    {
        if (layout == null) return;
        long now = sapi.World.ElapsedMilliseconds;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online.Entity is not EntityPlayer player || !player.Alive) continue;
            bool jump = player.ServerControls.Jump;
            if (jump && !jumping.GetValueOrDefault(player.EntityId)) RaiseNoise(player.Pos.XYZ, JumpLoudness * (Senses.Sneaking(player) ? 0.5 : 1), "jump", player);
            jumping[player.EntityId] = jump;
        }

        for (int i = inFlight.Count - 1; i >= 0; i--)
        {
            (Entity thing, Vec3d last, int still, long since) = inFlight[i];
            bool landed = !thing.Alive;
            Vec3d at = landed ? last : thing.Pos.XYZ;
            if (!landed)
            {
                still = thing.Pos.Motion.LengthSq() < 0.0004 ? still + 1 : 0;
                landed = still >= 2;
            }
            if (landed) RaiseNoise(at, ImpactLoudness, "impact", (thing as IProjectile)?.FiredBy);
            if (landed || now - since > FlightGiveUpMs) inFlight.RemoveAt(i);
            else inFlight[i] = (thing, at, still, since);
        }
    }

    // ================= Cost =================

    private readonly long[] tickCosts = new long[30];
    private int tickCostAt, tickCostCount;
    private long costReadAtMs = -1, costReadCalls, costReadTicks;

    private void NoteTickCost(long ticks)
    {
        tickCosts[tickCostAt] = ticks;
        tickCostAt = (tickCostAt + 1) % tickCosts.Length;
        tickCostCount = Math.Min(tickCosts.Length, tickCostCount + 1);
    }

    /// <summary>What the director's tick costs (the last minute or so) and how many perception checks run, for /backrooms menace.</summary>
    public string CostLine()
    {
        double tickMs = tickCostCount == 0 ? 0 : tickCosts.Take(tickCostCount).Average() * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
        (long calls, long ticks) = Perception.Cost;
        long now = sapi.World.ElapsedMilliseconds;
        string perception;
        if (costReadAtMs < 0 || now <= costReadAtMs) perception = "perception: " + calls + " checks so far";
        else
        {
            long dc = calls - costReadCalls;
            double seconds = (now - costReadAtMs) / 1000.0;
            double eachMs = dc <= 0 ? 0 : (ticks - costReadTicks) * 1000.0 / System.Diagnostics.Stopwatch.Frequency / dc;
            perception = string.Format(CultureInfo.InvariantCulture, "perception: {0:0.0} checks a second since the last readout, {1:0.000} ms each", dc / seconds, eachMs);
        }
        costReadAtMs = now;
        costReadCalls = calls;
        costReadTicks = ticks;
        return string.Format(CultureInfo.InvariantCulture, "Cost: director {0:0.00} ms a tick (last {1}); {2}; {3} noises heard now.",
            tickMs, tickCostCount, perception, Noises.Recent(now).Count);
    }

    // ================= Probes =================

    /// <summary>One perception probe: an entity held still, facing someone, reporting what it makes of them every second.</summary>
    private sealed class Probe
    {
        public Entity Thing, Target;
        public SenseProfile Senses;
        public readonly Belief Belief = new();
        public int Seconds, Elapsed, Seen, Sensed, Heard, FirstSeen = -1, LostAt = -1;
        public bool Believed;
        public long Listener;
        public IServerPlayer Caller;
    }

    private readonly List<Probe> probes = new();

    private void RegisterProbeCommands(ICoreServerAPI api, IChatCommand command)
    {
        var parsers = api.ChatCommands.Parsers;
        command
            .BeginSubCommand("perceive")
                .WithDescription("Perception probe: puts an entity down (held still) some blocks from you, or from the console from the latest straw dummy, and reports every second what it sees, hears, senses and believes of you. Args: entity, distance (20), seconds (30), toward|away (how it faces), sense overrides (hearing=8,sightDark=4,...). 'perceive stop' ends every probe")
                .WithArgs(parsers.Word("entity"), parsers.OptionalInt("distance"), parsers.OptionalInt("seconds"), parsers.OptionalWord("facing"), parsers.OptionalWord("senses"))
                .HandleWith(OnPerceiveCommand)
            .EndSubCommand()
            .BeginSubCommand("dummy")
                .WithDescription("Straw dummies for perception tests, standing in for a player: place, move, light, sneak, run, stability, noise, remove")
                .BeginSubCommand("place")
                    .WithDescription("Puts a straw dummy down: in a level (a number or name, as for goto) at one of its arrival spots, or 'here', in front of you, or 'nest', 8 blocks from the heart of a Level 8 spider nest (worlds from layout version 9). The first try may only load the chunks: try again")
                    .WithArgs(parsers.Word("where"), parsers.OptionalInt("key"))
                    .HandleWith(OnDummyPlace)
                .EndSubCommand()
                .BeginSubCommand("move")
                    .WithDescription("Moves the latest straw dummy (the nearest one to you) by dx, dz blocks, onto the floor there")
                    .WithArgs(parsers.Int("dx"), parsers.Int("dz"), parsers.OptionalWord("ignored"))
                    .HandleWith(OnDummyMove)
                .EndSubCommand()
                .BeginSubCommand("light")
                    .WithDescription("The light the latest straw dummy carries (0 none, 7 a candle, 14 a torch, 18 a lantern)")
                    .WithArgs(parsers.Int("light"), parsers.OptionalWord("ignored"))
                    .HandleWith(args => OnDummySet(args, d => { d.WatchedAttributes.SetInt(Senses.TestLightKey, Math.Clamp((int)args[0], 0, 20)); return "carries light " + d.WatchedAttributes.GetInt(Senses.TestLightKey); }))
                .EndSubCommand()
                .BeginSubCommand("sneak")
                    .WithDescription("Whether the latest straw dummy sneaks (on/off; toggles without)")
                    .WithArgs(parsers.OptionalWord("on"))
                    .HandleWith(args => OnDummySet(args, d => Toggle(d, Senses.TestSneakKey, args, "sneaks", "stands up")))
                .EndSubCommand()
                .BeginSubCommand("run")
                    .WithDescription("Whether the latest straw dummy counts as running (on/off; toggles without)")
                    .WithArgs(parsers.OptionalWord("on"))
                    .HandleWith(args => OnDummySet(args, d => Toggle(d, Senses.TestRunKey, args, "runs", "stops running")))
                .EndSubCommand()
                .BeginSubCommand("stability")
                    .WithDescription("The latest straw dummy's Reality Stability (0 to 1)")
                    .WithArgs(parsers.Double("stability"), parsers.OptionalWord("ignored"))
                    .HandleWith(args => OnDummySet(args, d => { d.WatchedAttributes.SetDouble("temporalStability", Math.Clamp((double)args[0], 0, 1)); return "stability " + Senses.Stability(d).ToString("0.00", CultureInfo.InvariantCulture); }))
                .EndSubCommand()
                .BeginSubCommand("noise")
                    .WithDescription("The latest straw dummy makes a noise (loudness 0 to 1, default 0.5): on the noise bus, and in its menace")
                    .WithArgs(parsers.OptionalDouble("loudness"), parsers.OptionalWord("ignored"))
                    .HandleWith(args => OnDummySet(args, d =>
                    {
                        double loud = args.Parsers[0].IsMissing ? 0.5 : Math.Clamp((double)args[0], 0, 1);
                        MakeNoise(d, loud, source: "test");
                        return "makes a noise of " + loud.ToString("0.00", CultureInfo.InvariantCulture);
                    }))
                .EndSubCommand()
                .BeginSubCommand("remove")
                    .WithDescription("Removes every straw dummy put down for tests")
                    .WithArgs(parsers.OptionalWord("ignored"))
                    .HandleWith(_ =>
                    {
                        int n = 0;
                        foreach (Entity d in dummies.Where(d => d.Alive).ToList()) { d.Die(EnumDespawnReason.Removed); n++; }
                        dummies.Clear();
                        return TextCommandResult.Success($"Removed {n} dummies");
                    })
                .EndSubCommand()
            .EndSubCommand();
    }

    private static string Toggle(Entity dummy, string key, TextCommandCallingArgs args, string on, string off)
    {
        string word = args.Parsers[0].IsMissing ? "" : ((string)args[0]).Trim().ToLowerInvariant();
        bool value = word switch { "on" or "true" or "1" => true, "off" or "false" or "0" => false, _ => !dummy.WatchedAttributes.GetBool(key) };
        dummy.WatchedAttributes.SetBool(key, value);
        return value ? on : off;
    }

    /// <summary>The straw dummy a command is about: the nearest to the player who gave it, or the latest put down (from the console).</summary>
    private Entity LatestDummy(TextCommandCallingArgs args)
    {
        dummies.RemoveAll(d => !d.Alive);
        if (args.Caller.Entity is { } caller)
            return sapi.World.GetNearestEntity(caller.Pos.XYZ, 64, 32, e => e.Alive && Senses.IsTestTarget(e));
        return dummies.Count == 0 ? null : dummies[^1];
    }

    private TextCommandResult OnDummySet(TextCommandCallingArgs args, System.Func<Entity, string> set)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity dummy = LatestDummy(args);
        if (dummy == null) return TextCommandResult.Error("No straw dummy (put one down with /backrooms dummy place)");
        return TextCommandResult.Success($"Dummy #{dummy.EntityId} " + set(dummy));
    }

    private TextCommandResult OnDummyPlace(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string where = ((string)args[0]).Trim();
        int x, y, z;
        if (where.Equals("here", StringComparison.OrdinalIgnoreCase))
        {
            if (args.Caller.Entity is not { } caller) return TextCommandResult.Error("'here' needs a player; from the console, name a level");
            Vec3f view = caller.Pos.GetViewVector();
            double length = Math.Max(1e-3, Math.Sqrt(view.X * view.X + view.Z * view.Z));
            x = (int)Math.Floor(caller.Pos.X + view.X / length * 3);
            z = (int)Math.Floor(caller.Pos.Z + view.Z / length * 3);
            y = (int)Math.Floor(caller.Pos.Y);
        }
        else if (where.Equals("nest", StringComparison.OrdinalIgnoreCase))
        {
            (int X, int Z)? heart = null;
            int arrivals = 0;
            for (int k = 0; k < 12 && heart == null; k++)
                if (layout.FindArrival(8, (ulong)k) is { } arrival) { arrivals++; heart = layout.NearestNest(arrival.X, arrival.Z, 100); }
            if (heart is not { } nest)
            {
                int l8 = 0, dens = 0;
                if (layout.FindArrival(8, 0) is { } probe)
                    for (int dz = -60; dz <= 60; dz++)
                        for (int dx = -60; dx <= 60; dx++)
                        {
                            int mx = WorldLayout.MacroOf(probe.X) + dx, mz = WorldLayout.MacroOf(probe.Z) + dz;
                            if (layout.LevelAt(mx, mz) != 8) continue;
                            l8++;
                            if (layout.DenAt(mx, mz) != DenKind.None) dens++;
                        }
                return TextCommandResult.Error($"Found no spider nest ({arrivals} Level 8 spots tried; layout version {layout.Version}; {l8} Level 8 cells near the first, {dens} with dens)");
            }
            x = nest.X + 8;
            z = nest.Z;
            y = geometry.FloorFor(8) + 1;
        }
        else
        {
            int level = WorldLayout.FromDisplayName(where);
            if (level < 0) return TextCommandResult.Error($"There is no Level {where} (0-11, 37, 94, !, fun, end, hub, 974, 3999 or 188)");
            ulong key = args.Parsers[1].IsMissing ? (ulong)sapi.World.Rand.NextInt64() : (ulong)(int)args[1];
            if (layout.FindArrival(level, key) is not { } spot) return TextCommandResult.Error("Found nowhere in that level");
            (x, z) = spot;
            y = geometry.FloorFor(level) + 1;
        }
        Entity dummy = SpawnDummy(x, y, z, out string why);
        if (dummy == null) return TextCommandResult.Error(why);
        dummies.Add(dummy);
        if (!watches.TryGetValue(dummy.EntityId, out Watch watch)) watches[dummy.EntityId] = watch = new Watch();
        Assess(dummy, watch);
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "Dummy #{0} at {1:0} {2:0} {3:0}, Level {4}, light {5}",
            dummy.EntityId, dummy.Pos.X, dummy.Pos.Y, dummy.Pos.Z, WorldLayout.DisplayNumber(watch.Now.Level), Perception.LightOn(dummy)));
    }

    private TextCommandResult OnDummyMove(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity dummy = LatestDummy(args);
        if (dummy == null) return TextCommandResult.Error("No straw dummy (put one down with /backrooms dummy place)");
        int x = (int)Math.Floor(dummy.Pos.X) + (int)args[0], z = (int)Math.Floor(dummy.Pos.Z) + (int)args[1];
        int y = Senses.FindFloor(sapi.World, x, (int)Math.Floor(dummy.Pos.Y), z, 2, 6);
        if (y == int.MinValue) return TextCommandResult.Error("No floor there");
        dummy.TeleportToDouble(x + 0.5, y, z + 0.5);
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "Dummy #{0} moved to {1} {2} {3}, light {4}", dummy.EntityId, x, y, z, Perception.LightOn(dummy)));
    }

    private TextCommandResult OnPerceiveCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string code = ((string)args[0]).Trim();
        if (code.Equals("stop", StringComparison.OrdinalIgnoreCase))
        {
            int n = probes.Count;
            foreach (Probe p in probes.ToList()) FinishProbe(p);
            return TextCommandResult.Success($"Stopped {n} probes");
        }
        if (!code.Contains(':')) code = "backrooms:" + code;
        EntityProperties type = types.GetValueOrDefault(code) ?? sapi.World.GetEntityType(new AssetLocation(code));
        if (type == null) return TextCommandResult.Error("No such entity: " + code);

        Entity target = args.Caller.Entity ?? LatestDummy(args);
        if (target == null) return TextCommandResult.Error("From the console, put a straw dummy down first (/backrooms dummy place <level>)");
        int distance = args.Parsers[1].IsMissing ? 20 : Math.Clamp((int)args[1], 1, 80);
        int seconds = args.Parsers[2].IsMissing ? 30 : Math.Clamp((int)args[2], 1, 300);
        string facing = args.Parsers[3].IsMissing ? "toward" : ((string)args[3]).Trim().ToLowerInvariant();
        if (facing is not ("toward" or "away")) return TextCommandResult.Error("Facing is toward or away");
        string overrides = args.Parsers[4].IsMissing ? "" : ((string)args[4]).Trim();

        // Somewhere at the distance with a clear line to them, if there is one
        Vec3d eyes = Senses.Eyes(target), spot = null;
        bool clear = false;
        for (int i = 0; i < 32 && !clear; i++)
        {
            double angle = i * Math.PI * 2 / 32;
            int x = (int)Math.Floor(target.Pos.X + Math.Cos(angle) * distance), z = (int)Math.Floor(target.Pos.Z + Math.Sin(angle) * distance);
            int y = Senses.FindFloor(sapi.World, x, (int)Math.Floor(target.Pos.Y), z, 2, 4);
            if (y == int.MinValue) continue;
            var at = new Vec3d(x + 0.5, y, z + 0.5);
            bool line = Senses.ClearLine(sapi.World, eyes, at.AddCopy(0, 1.2, 0));
            if (line || spot == null) (spot, clear) = (at, line);
        }
        if (spot == null) return TextCommandResult.Error($"No floor {distance} blocks from the target");

        Entity thing = sapi.World.ClassRegistry.CreateEntity(type);
        thing.Pos.SetPos(spot.X, spot.Y + 0.02, spot.Z);
        float yaw = (float)Math.Atan2(target.Pos.X - spot.X, target.Pos.Z - spot.Z);
        thing.Pos.Yaw = facing == "away" ? (yaw + GameMath.PI) % GameMath.TWOPI : yaw;
        EntityBehaviorMenace.Prepare(thing, target, Encounter.Ambient, passive: true, sapi.World.ElapsedMilliseconds);
        thing.AlwaysActive = true;
        sapi.World.SpawnEntity(thing);
        // (Held still and facing as put: its own tasks never run)
        if (thing.GetBehavior<EntityBehaviorTaskAI>()?.TaskManager is { } tasks)
        {
            tasks.OnShouldExecuteTask += _ => false;
            tasks.StopTasks();
        }

        SenseProfile own = SenseProfile.Of(thing);
        SenseProfile senses = (own ?? SenseProfile.Default).With(overrides, out string error);
        if (senses == null)
        {
            thing.Die(EnumDespawnReason.Removed);
            return TextCommandResult.Error(error);
        }
        var probe = new Probe { Thing = thing, Target = target, Senses = senses, Seconds = seconds, Caller = args.Caller.Player as IServerPlayer };
        probes.Add(probe);
        probe.Listener = sapi.Event.RegisterGameTickListener(_ => StepProbe(probe), 1000, 1000);
        string start = string.Format(CultureInfo.InvariantCulture,
            "perceive {0}#{1} start: {2:0.0} blocks from {3} #{4}, facing {5}, line {6}, light on target {7}, senses{8}: {9}",
            thing.Code.Path, thing.EntityId, spot.DistanceTo(target.Pos.XYZ), target.Code.Path, target.EntityId, facing, clear ? "clear" : "blocked",
            Perception.LightOn(target), own == null ? " (none of its own: defaults)" : "", senses);
        sapi.Logger.Notification("[backrooms] " + start);
        return TextCommandResult.Success(start);
    }

    private void StepProbe(Probe p)
    {
        if (!p.Thing.Alive || !p.Target.Alive)
        {
            FinishProbe(p);
            return;
        }
        long now = sapi.World.ElapsedMilliseconds;
        p.Elapsed++;
        Perception.Result r = Perception.Perceive(p.Thing, p.Target, p.Senses, p.Belief, Noises, now);
        switch (r.Contact)
        {
            case Contact.Seen:
                p.Seen++;
                if (p.FirstSeen < 0) p.FirstSeen = p.Elapsed;
                break;
            case Contact.Sensed: p.Sensed++; break;
            case Contact.Heard: p.Heard++; break;
        }
        double confidence = p.Belief.ConfidenceAt(now, p.Senses.MemorySeconds);
        if (confidence > 0) p.Believed = true;
        else if (p.Believed && p.LostAt < 0) p.LostAt = p.Elapsed;
        string detail = r.Contact switch
        {
            Contact.Seen => string.Format(CultureInfo.InvariantCulture, "plainness {0:0.00}", r.Plainness),
            Contact.Sensed => "by " + r.Sense,
            Contact.Heard => r.Noise is { } n ? string.Format(CultureInfo.InvariantCulture, "{0} {1:0.00} from {2:0.0} blocks", n.Source, n.Loudness, n.Pos.DistanceTo(Senses.Eyes(p.Thing))) : "",
            _ => "(" + (r.WhyNotSeen ?? "nothing") + ")",
        };
        string line = string.Format(CultureInfo.InvariantCulture,
            "perceive {0}#{1} t={2} d={3:0.0} light={4} held={5}{6}{7} -> {8} {9} | belief {10} conf {11:0.00} err {12}",
            p.Thing.Code.Path, p.Thing.EntityId, p.Elapsed, p.Thing.Pos.DistanceTo(p.Target.Pos), Perception.LightOn(p.Target), Senses.HeldLight(p.Target),
            Senses.Sneaking(p.Target) ? " sneaking" : "", Senses.Running(p.Target) ? " running" : "", r.Contact, detail,
            p.Belief.Source, confidence, p.Belief.Pos == null ? "-" : p.Belief.Pos.DistanceTo(p.Target.Pos.XYZ).ToString("0.0", CultureInfo.InvariantCulture));
        sapi.Logger.Notification("[backrooms] " + line);
        p.Caller?.SendMessage(GlobalConstants.GeneralChatGroup, line, EnumChatType.Notification);
        if (p.Elapsed >= p.Seconds) FinishProbe(p);
    }

    private void FinishProbe(Probe p)
    {
        if (!probes.Remove(p)) return;
        sapi.Event.UnregisterGameTickListener(p.Listener);
        string summary = string.Format(CultureInfo.InvariantCulture, "perceive {0}#{1} done: seen {2}/{3}, sensed {4}, heard {5}, first seen t={6}, lost t={7}",
            p.Thing.Code.Path, p.Thing.EntityId, p.Seen, p.Elapsed, p.Sensed, p.Heard, p.FirstSeen, p.LostAt);
        sapi.Logger.Notification("[backrooms] " + summary);
        p.Caller?.SendMessage(GlobalConstants.GeneralChatGroup, summary, EnumChatType.Notification);
        if (p.Thing.Alive) p.Thing.Die(EnumDespawnReason.Removed);
    }
}
