using System;
using System.Collections.Generic;
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
/// Level !, "Run For Your Life!": the chase.
///
/// A runner arrives in a start room in red light. Something hammers at the chained door; the door to the hallway sticks
/// (it opens on the third try). Twelve seconds after arriving, or four after stepping into the hall, the chained door
/// bursts, the alarm goes from a murmur in the walls to deafening, and the horde comes down the hall.
///
/// The horde is a number (<see cref="RunChase"/>): its front's position along the lane's course, running at nearly the
/// runner's own sprint, keeping pace out of sight once 40 blocks behind ("they are still near"), waiting at the Safe
/// Zone's door, and catching whoever it comes within a block and a half of: they are pinned, and torn apart. What is
/// seen of it is a few of the Backrooms' own entities, put down just behind the front and moved along the hall with it
/// (puppets: their own minds are switched off; they are worth nothing killed, and come back).
///
/// Along the way, as the runner nears them: side doors fly open into the hall, shelving topples, dented doors burst and
/// something slower comes out behind, a vent drops a Hound, an EXIT sign hisses, flickers and bursts into a wall of fire,
/// small things in the dark trip a sprinter. Each lane is put back as it was a little ahead of each new runner.
///
/// Escape once (the true exit), and the Backrooms never take you there again (<see cref="RanOutKey"/>).
/// </summary>
public class RunSystem : ModSystem
{
    /// <summary>Entity attribute: one of the horde (no bounty, no corpse, no mind of its own).</summary>
    public const string HordeKey = "backrooms:horde";
    /// <summary>Player attribute: has escaped Level ! once, and will never be taken there again.</summary>
    public const string RanOutKey = "backrooms:ranOut";
    /// <summary>Player attributes the client reads: the run's phase (<see cref="Phase"/>), the gap to the horde, where its front is.</summary>
    public const string PhaseKey = "backrooms:runPhase", GapKey = "backrooms:runGap", FrontKey = "backrooms:runFront";
    /// <summary>Entity attribute: when an Energy Bar's second wind runs out (elapsed ms).</summary>
    public const string SecondWindKey = "backrooms:secondWindUntil";

    public enum Phase { None, Waiting, Alarm, Safe }

    private const string CaughtStat = "backroomsRunCaught", TripStat = "backroomsRunTrip", WindStat = "backroomsSecondWind";
    private const float SecondWind = 0.12f, TripSlow = -0.6f, Pinned = -0.9f;
    private const int TickMs = 100;
    private const double PresentAt = 48, DespawnAt = 60;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private WorldGenerator generator;
    private MenaceSystem menace;
    private readonly Random rand = new();
    private readonly Dictionary<string, Run> runs = new();
    private readonly Dictionary<int, (string Uid, long Until)> claims = new();
    private readonly Dictionary<string, (Link To, long At)> escapes = new();
    private readonly Dictionary<string, int> blockIds = new();
    private int falseWallId, falseWallUpperId;

    private sealed class Chaser
    {
        public Entity Entity;
        public double S, Speed, Lateral;
        public long Until;
        public double NextHit;
    }

    private sealed class Run
    {
        public int Lane;
        public WorldLayout.RunLane Plan;
        public RunChase Chase;
        public double P;
        public int DoorStage;
        public int HallTries;
        public double NextBang = 1;
        public readonly HashSet<int> Fired = new();
        public int SignEvent = -1, SignStage;
        public double FireUntil, NextHiss;
        public int VentEvent = -1;
        public readonly List<(Entity Entity, double Offset, double Lateral)> Horde = new();
        public double NextHordeSpawn;
        public readonly List<Chaser> Chasers = new();
        public double SafeSince = -1;
        public bool Rumbled;
        public double NextPin;
        public bool[] Restored;
        public double TripUntil, TripCooldown;
        public bool Active = true;
    }

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsEnergyBar", typeof(ItemEnergyBar));
        api.RegisterBlockBehaviorClass("BackroomsRunDoor", typeof(BlockBehaviorRunDoor));
        api.RegisterBlockEntityClass("BackroomsRunBeacon", typeof(BlockEntityRunBeacon));
        api.RegisterBlockEntityClass("RunBeacon", typeof(BlockEntityRunBeacon));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            generator = api.ModLoader.GetModSystem<BackroomsModSystem>()?.Generator;
            menace = api.ModLoader.GetModSystem<MenaceSystem>();
            falseWallId = BlockId("run-falsewall-lower");
            falseWallUpperId = BlockId("run-falsewall-upper");
            api.Event.RegisterGameTickListener(OnTick, TickMs);
            api.Event.OnEntityDeath += OnEntityDeath;
            // The horde is saved with its chunk (its mark too) but not its puppeting: any of it loaded again is let go
            api.Event.OnEntityLoaded += e =>
            {
                if (e.Attributes.GetBool(HordeKey))
                    sapi.Event.RegisterCallback(_ => { if (e.State != EnumEntityState.Despawned) sapi.World.DespawnEntity(e, new EntityDespawnData { Reason = EnumDespawnReason.Expire }); }, 50);
            };
            api.Event.PlayerDisconnect += player => EndRun(player.PlayerUID, "left");
        });
    }

    private int BlockId(string code)
    {
        if (blockIds.TryGetValue(code, out int id)) return id;
        id = sapi.World.GetBlock(new AssetLocation("backrooms", code))?.BlockId ?? 0;
        blockIds[code] = id;
        return id;
    }

    private static string Side(ArchPier pier) => pier switch { ArchPier.North => "north", ArchPier.East => "east", ArchPier.South => "south", _ => "west" };

    private static (int Dx, int Dz) Step(ArchPier pier) => pier switch
    {
        ArchPier.North => (0, -1),
        ArchPier.East => (1, 0),
        ArchPier.South => (0, 1),
        _ => (-1, 0),
    };

    // ================= For the thresholds =================

    /// <summary>Whether a player has escaped Level ! before.</summary>
    public static bool HasRanOut(Entity entity) => entity?.WatchedAttributes.GetBool(RanOutKey) == true;

    /// <summary>
    /// The lane someone about to arrive will run: the one their way in leads to if nobody else is running it (or has just
    /// been given it), else the next free one; the one it leads to anyway if all are taken.
    /// </summary>
    public int ClaimLane(IServerPlayer player, int lane)
    {
        if (lane < 0) return lane;
        long now = sapi.World.ElapsedMilliseconds;
        bool Free(int l)
        {
            foreach (var (uid, r) in runs)
                if (uid != player.PlayerUID && r.Active && r.Lane == l) return false;
            return !claims.TryGetValue(l, out var c) || c.Uid == player.PlayerUID || c.Until < now;
        }
        for (int k = 0; k < WorldLayout.RunLanes; k++)
        {
            int l = (lane + k) % WorldLayout.RunLanes;
            if (!Free(l)) continue;
            claims[l] = (player.PlayerUID, now + 15_000);
            return l;
        }
        return lane;
    }

    /// <summary>Someone has gone out through a true exit, and is about to arrive at <paramref name="to"/>.</summary>
    public void NoteEscape(IServerPlayer player, Link to)
    {
        escapes[player.PlayerUID] = (to, sapi.World.ElapsedMilliseconds);
        player.Entity.WatchedAttributes.SetBool(RanOutKey, true);
        EndRun(player.PlayerUID, "escaped");
    }

    // ================= The tick =================

    private void OnTick(float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online is not IServerPlayer player || player.Entity == null) continue;
            EntityPlayer entity = player.Entity;
            SecondWindTick(entity, now);

            int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
            int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));

            // Level 2: walking into the wall that wasn't there
            if (level == 2 && falseWallId != 0 && entity.Alive && !entity.Teleporting && player.WorldData.CurrentGameMode != EnumGameMode.Spectator)
            {
                var feet = new BlockPos(x, (int)Math.Floor(entity.Pos.Y), z);
                int atFeet = sapi.World.BlockAccessor.GetBlock(feet).BlockId, atHead = sapi.World.BlockAccessor.GetBlock(feet.UpCopy()).BlockId;
                if (atFeet == falseWallId || atFeet == falseWallUpperId || atHead == falseWallId || atHead == falseWallUpperId)
                    sapi.ModLoader.GetModSystem<ThresholdSystem>()?.Use(player, feet, "runfalsewall");
            }

            // Out through a true exit: leave the door they came out of where they came out
            if (escapes.TryGetValue(player.PlayerUID, out var esc) && level != WorldLayout.RunLevel && now - esc.At > 1200)
            {
                escapes.Remove(player.PlayerUID);
                LeaveExitDoor(esc.To);
            }

            runs.TryGetValue(player.PlayerUID, out Run run);
            bool here = level == WorldLayout.RunLevel && entity.Alive && !entity.Teleporting;
            if (run != null && (!here || !run.Active))
            {
                if (!here) EndRun(player.PlayerUID, entity.Alive ? "left" : "died");
                continue;
            }
            if (!here) continue;
            if (run == null)
            {
                run = StartRun(player, x, z);
                if (run == null) continue;
            }
            TickRun(player, run, dt);
        }
        foreach (var lane in new List<int>(claims.Keys)) if (claims[lane].Until < now) claims.Remove(lane);
    }

    private Run StartRun(IServerPlayer player, int x, int z)
    {
        int lane = layout.RunLaneAt(x, z);
        if (lane < 0) return null;
        var plan = layout.RunPlan(lane);
        EnumGameMode mode = player.WorldData.CurrentGameMode;
        // Back from logging out (or a restart) partway down the hall: a run always begins in the start room, never ahead
        // of a horde that has to start again from the chained door
        if (mode == EnumGameMode.Survival && menace?.Setting.Entities != false && layout.TileAt(x, z).Zone != WorldLayout.RunZone.StartRoom)
        {
            var (ax, az) = layout.RunWorld(lane, plan.Arrival.X, plan.Arrival.Z);
            player.Entity.TeleportToDouble(ax + 0.5, geometry.FloorFor(WorldLayout.RunLevel) + layout.ArrivalHeight(ax, az), az + 0.5);
            return null;
        }
        int difficulty = menace?.Setting.Code switch { "low" => 0, "high" => 2, _ => 1 };
        int chained = plan.ProgressAt(plan.ChainedDoor.X, plan.ChainedDoor.Z) ?? -8;
        var run = new Run
        {
            Lane = lane,
            Plan = plan,
            Chase = new RunChase(SprintOf(player.Entity), difficulty, plan.Last, plan.SafeFrom, plan.SafeTo, chained),
            Restored = new bool[WorldLayout.RunLaneLength],
        };
        // A spectator, a creative player, or a world without entities: the alarm in the walls, but nothing comes
        run.Active = mode == EnumGameMode.Survival && menace?.Setting.Entities != false;
        run.P = plan.ProgressAt(layout.RunLocal(lane, x, z).X, layout.RunLocal(lane, x, z).Z) ?? -4;
        // A sign that will burst into fire this time, maybe, and a vent that will drop something, maybe
        var signs = plan.Events.FindAll(e => e.Kind == WorldLayout.RunEventKind.Sign);
        if (signs.Count > 0 && rand.NextDouble() < 1.0 / 3) run.SignEvent = plan.Events.IndexOf(signs[rand.Next(signs.Count)]);
        var vents = plan.Events.FindAll(e => e.Kind == WorldLayout.RunEventKind.Vent && e.S > 60 && e.S < plan.ExitS - 40);
        if (vents.Count > 0 && rand.NextDouble() < 0.5) run.VentEvent = plan.Events.IndexOf(vents[rand.Next(vents.Count)]);
        // Put the start room and the first stretch back as they were
        RestoreRows(run, 0, plan.HallDoor.Z + 60);
        runs[player.PlayerUID] = run;
        claims[lane] = (player.PlayerUID, sapi.World.ElapsedMilliseconds + 15_000);
        SetPhase(player.Entity, run.Active ? Phase.Waiting : Phase.None, 999, null);
        if (run.Active) Play("run/slam", Centre(run, plan.MarkedDoor), 24, 1f);
        if (sapi.ModLoader.GetModSystem<MenaceSystem>()?.Logging == true)
            sapi.Logger.Notification("[backrooms] {0} runs lane {1} of Level ! (course {2}, exit to {3}, sprint {4:0.00})", player.PlayerName, lane, plan.ExitS,
                WorldLayout.DisplayNumber(plan.Destination), run.Chase.Sprint);
        return run;
    }

    private void EndRun(string uid, string why)
    {
        if (!runs.TryGetValue(uid, out Run run)) return;
        runs.Remove(uid);
        claims.Remove(run.Lane);
        foreach (var h in run.Horde) Despawn(h.Entity);
        foreach (var c in run.Chasers) Despawn(c.Entity);
        if (sapi.World.PlayerByUid(uid) is IServerPlayer { Entity: { } e })
        {
            e.Stats.Remove("walkspeed", CaughtStat);
            e.Stats.Remove("walkspeed", TripStat);
            SetPhase(e, Phase.None, 999, null);
        }
    }

    /// <summary>The runner's sprint, in blocks a second: Vintage Story's, slowed by armour, not hurried by an Energy Bar.</summary>
    private static double SprintOf(EntityAgent entity)
    {
        double walk = entity.Stats.GetBlended("walkspeed");
        foreach (string mine in new[] { WindStat, TripStat, CaughtStat })
            if (entity.Stats["walkspeed"].ValuesByKey.TryGetValue(mine, out var v)) walk -= v.Value;
        return RunChase.SprintSpeed * Math.Clamp(walk, 0.4, 1.5);
    }

    private (int X, int Z) WorldOf(Run run, (int X, int Z) local) => layout.RunWorld(run.Lane, local.X, local.Z);

    private Vec3d Centre(Run run, (int X, int Z) local, double up = 0)
    {
        var (x, z) = WorldOf(run, local);
        return new Vec3d(x + 0.5, geometry.FloorFor(WorldLayout.RunLevel) + 1 + up, z + 0.5);
    }

    private void TickRun(IServerPlayer player, Run run, float dt)
    {
        EntityPlayer entity = player.Entity;
        var plan = run.Plan;
        var (lx, lz) = layout.RunLocal(run.Lane, (int)Math.Floor(entity.Pos.X), (int)Math.Floor(entity.Pos.Z));
        int? at = plan.ProgressAt(lx, lz);
        if (at == null)
            foreach (var f in plan.FakeExits)
                if (Math.Abs(lx - f.X) <= 1 && lz > f.Z && lz <= f.Z + 3) at = plan.ProgressAt(f.FrontX, f.FrontZ);
        if (at != null) run.P = at.Value;

        // Keep the stretch ahead as it was meant to be
        RestoreAhead(run);
        if (!run.Active)
        {
            SetPhase(entity, Phase.None, 999, null);
            return;
        }

        RunChase chase = run.Chase;
        bool wasLoose = chase.Loose;
        bool caught = chase.Step(dt, run.P);

        // Before the break: the blows on the chained door, the bulge
        if (!chase.Loose)
        {
            run.NextBang -= dt;
            if (run.NextBang <= 0)
            {
                run.NextBang = 1.2 + rand.NextDouble() * (chase.Elapsed > 6 ? 0.4 : 0.8);
                Play("run/bang" + rand.Next(1, 4), Centre(run, plan.ChainedDoor), 32, 1f);
            }
            if (chase.Elapsed > 6 && run.DoorStage == 0) SwapDoor(run, plan.ChainedDoor, "run-chaineddoor-bulging", ArchPier.South, ref run.DoorStage, 1);
        }
        else if (!wasLoose)
        {
            SwapDoor(run, plan.ChainedDoor, "run-chaineddoor-broken", ArchPier.South, ref run.DoorStage, 2);
            Play("run/doorbreak", Centre(run, plan.ChainedDoor), 48, 1f);
        }

        // In the Safe Zone: nothing comes in, for three hours
        bool safe = chase.InSafe(run.P);
        double hours = sapi.World.Calendar.TotalHours;
        if (safe && run.SafeSince < 0) run.SafeSince = hours;
        if (!safe) { run.SafeSince = -1; run.Rumbled = false; }
        if (safe && chase.Loose)
        {
            if (!run.Rumbled && hours - run.SafeSince > 2)
            {
                run.Rumbled = true;
                player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:run-rumble"), EnumChatType.Notification);
            }
            if (hours - run.SafeSince > 3) chase.SafeBreached = true;
        }

        double gap = chase.Gap(run.P);
        Vec3d front = chase.Loose ? Centre(run, plan.LineAt((int)Math.Floor(chase.Front))) : Centre(run, plan.ChainedDoor);
        SetPhase(entity, !chase.Loose ? Phase.Waiting : safe ? Phase.Safe : Phase.Alarm, chase.Loose ? gap : 999, front);

        UpdateHorde(player, run, dt);
        UpdateChasers(player, run, dt);
        FireEvents(player, run, dt);
        Trip(player, run, dt);

        // Caught: pinned, and torn apart
        if (caught && entity.Alive)
        {
            entity.Stats.Set("walkspeed", CaughtStat, Pinned, false);
            run.NextPin -= dt;
            if (run.NextPin <= 0)
            {
                run.NextPin = 0.5;
                float damage = 2f * Danger.Damage(Danger.OfLevel(WorldLayout.RunLevel)) * (float)(menace?.Setting.Damage ?? 1);
                Entity by = run.Horde.Count > 0 ? run.Horde[0].Entity : null;
                entity.ReceiveDamage(new DamageSource
                {
                    Source = by != null ? EnumDamageSource.Entity : EnumDamageSource.Unknown, SourceEntity = by, CauseEntity = by,
                    Type = EnumDamageType.SlashingAttack, KnockbackStrength = 0,
                }, damage);
            }
        }
        else entity.Stats.Remove("walkspeed", CaughtStat);
    }

    private void SetPhase(EntityPlayer entity, Phase phase, double gap, Vec3d front)
    {
        var w = entity.WatchedAttributes;
        if (w.GetInt(PhaseKey) != (int)phase) w.SetInt(PhaseKey, (int)phase);
        float g = (float)Math.Round(gap, 1);
        if (Math.Abs(w.GetFloat(GapKey, 999) - g) >= 0.1f) w.SetFloat(GapKey, g);
        if (front != null)
        {
            double[] old = (w[FrontKey] as DoubleArrayAttribute)?.value;
            if (old == null || Math.Abs(old[0] - front.X) + Math.Abs(old[2] - front.Z) > 0.5)
                w[FrontKey] = new DoubleArrayAttribute(new[] { front.X, front.Y, front.Z });
        }
    }

    // ================= The horde you see =================

    private static readonly string[] HordeKinds = { Roster.Hound, Roster.Hound, Roster.SkinStealer, Roster.Smiler, Roster.DeathRat, Roster.DeathmothFemale };

    private void UpdateHorde(IServerPlayer player, Run run, float dt)
    {
        RunChase chase = run.Chase;
        double gap = chase.Gap(run.P);
        run.Horde.RemoveAll(h => !h.Entity.Alive);
        bool show = chase.Loose && gap <= PresentAt;
        if (!chase.Loose || gap > DespawnAt)
        {
            foreach (var h in run.Horde) Despawn(h.Entity);
            run.Horde.Clear();
            return;
        }
        int want = chase.Front >= run.Plan.Last ? 3 : 5;
        run.NextHordeSpawn -= dt;
        if (show && run.Horde.Count < want && run.NextHordeSpawn <= 0 && menace != null)
        {
            run.NextHordeSpawn = run.Horde.Count == 0 ? 0 : 0.6;
            // Hounds always lead; the rest by the lane's hash
            string code = run.Horde.Count == 0 ? Roster.Hound : HordeKinds[(run.Lane * 7 + run.Horde.Count * 3 + rand.Next(3)) % HordeKinds.Length];
            double offset = run.Horde.Count == 0 ? 0.5 : 1 + rand.NextDouble() * 5;
            double lateral = (rand.NextDouble() * 2 - 1) * 1.6;
            Vec3d spot = Along(run, chase.Front - offset, lateral, code == Roster.DeathmothFemale ? 2.2 : 0);
            Entity e = menace.SpawnHunter(code, spot, player.Entity);
            if (e != null)
            {
                Puppet(e);
                run.Horde.Add((e, offset, lateral));
            }
        }
        foreach (var (e, offset, lateral) in run.Horde)
        {
            double s = Math.Min(chase.Front - offset, run.P - 0.6);
            if (chase.InSafe(run.P)) s = Math.Min(s, run.Plan.SafeFrom - 2 - offset * 0.3);
            Move(run, e, s, lateral, e.Code.Path.StartsWith("deathmoth") ? 2.2 : 0);
        }
    }

    /// <summary>A world position along a lane's course: on the centre line at course position s, moved across the hall by <paramref name="lateral"/>.</summary>
    private Vec3d Along(Run run, double s, double lateral, double up)
    {
        var plan = run.Plan;
        int i = (int)Math.Floor(s);
        var (ax, az) = plan.LineAt(i);
        var (bx, bz) = plan.LineAt(i + 1);
        double f = s - i;
        double x = ax + (bx - ax) * f, z = az + (bz - az) * f;
        // Across the way it runs
        double dx = bx - ax, dz = bz - az;
        if (dx == 0 && dz == 0) dz = 1;
        x += -dz * lateral;
        z += dx * lateral;
        var (wx, wz) = layout.RunWorld(run.Lane, 0, 0);
        return new Vec3d(wx + x + 0.5, geometry.FloorFor(WorldLayout.RunLevel) + 1 + up, wz + z + 0.5);
    }

    private void Move(Run run, Entity e, double s, double lateral, double up)
    {
        Vec3d to = Along(run, s, lateral, up);
        Vec3d ahead = Along(run, s + 1, lateral, up);
        e.ServerPos.SetPos(to);
        e.ServerPos.Yaw = (float)Math.Atan2(ahead.X - to.X, ahead.Z - to.Z);
        e.ServerPos.Motion.Set(0, 0, 0);
        e.Pos.SetFrom(e.ServerPos);
    }

    /// <summary>Switches an entity's own mind off: it goes where it is put, running.</summary>
    private static void Puppet(Entity e)
    {
        e.Attributes.SetBool(HordeKey, true);
        e.AlwaysActive = true;
        if (e.GetBehavior<EntityBehaviorTaskAI>()?.TaskManager is { } tasks)
        {
            tasks.OnShouldExecuteTask += _ => false;
            tasks.StopTasks();
        }
        string anim = e.Code.Path.StartsWith("deathmoth") ? "fly" : "run";
        e.AnimManager?.StartAnimation(anim);
    }

    private void Despawn(Entity e)
    {
        if (e != null && e.Alive) e.Die(EnumDespawnReason.Expire);
    }

    private void OnEntityDeath(Entity e, DamageSource source)
    {
        // One of the horde killed: nothing to harvest; another comes
        if (!e.Attributes.GetBool(HordeKey)) return;
        sapi.Event.RegisterCallback(_ => { if (e.State != EnumEntityState.Despawned) sapi.World.DespawnEntity(e, new EntityDespawnData { Reason = EnumDespawnReason.Expire }); }, 200);
    }

    // ================= What bursts out, and drops in =================

    private void Chase(IServerPlayer player, Run run, string code, double s, double speedShare, double lateral, double seconds, double up = 0)
    {
        if (menace == null) return;
        Entity e = menace.SpawnHunter(code, Along(run, s, lateral, up), player.Entity);
        if (e == null) return;
        Puppet(e);
        run.Chasers.Add(new Chaser
        {
            Entity = e, S = s, Speed = speedShare * run.Chase.Sprint, Lateral = lateral,
            Until = sapi.World.ElapsedMilliseconds + (long)(seconds * 1000),
        });
    }

    private void UpdateChasers(IServerPlayer player, Run run, float dt)
    {
        long now = sapi.World.ElapsedMilliseconds;
        foreach (Chaser c in run.Chasers)
        {
            if (!c.Entity.Alive) continue;
            // A vent's Hound keeps up for a few seconds, then falls back into the horde
            double speed = now < c.Until ? c.Speed : 0.8 * run.Chase.Sprint;
            c.S = Math.Min(c.S + speed * dt, run.P - 0.9);
            Move(run, c.Entity, c.S, c.Lateral, c.Entity.Code.Path.StartsWith("deathmoth") ? 2.2 : 0);
            if (run.P - c.S <= 1.2 && player.Entity.Alive)
            {
                c.NextHit -= dt;
                if (c.NextHit <= 0)
                {
                    c.NextHit = 0.8;
                    player.Entity.ReceiveDamage(new DamageSource
                    {
                        Source = EnumDamageSource.Entity, SourceEntity = c.Entity, CauseEntity = c.Entity, Type = EnumDamageType.SlashingAttack,
                    }, 3f * (float)(menace?.Setting.Damage ?? 1));
                }
            }
            // Fallen behind the front, or far behind: it is one of the horde now
            if (c.S < run.Chase.Front || run.P - c.S > 30) Despawn(c.Entity);
        }
        run.Chasers.RemoveAll(c => !c.Entity.Alive);
    }

    // ================= Events =================

    private void FireEvents(IServerPlayer player, Run run, float dt)
    {
        var plan = run.Plan;
        double p = run.P;
        for (int i = 0; i < plan.Events.Count; i++)
        {
            var e = plan.Events[i];
            if (run.Fired.Contains(i)) continue;
            if (e.S > p + 45) break; // sorted by S
            switch (e.Kind)
            {
                case WorldLayout.RunEventKind.Swing when p >= e.S && p < e.S + 9:
                {
                    run.Fired.Add(i);
                    SetDoor(run, (e.X, e.Z), "run-sidedoor-open", e.Face);
                    var (dx, dz) = Step(e.Face);
                    SetPart(run, (e.X + dx, e.Z + dz), 1, $"run-sidedoor-leaf-lower-{Side(e.Face)}");
                    SetPart(run, (e.X + dx, e.Z + dz), 2, $"run-sidedoor-leaf-upper-{Side(e.Face)}");
                    Play("run/swing", Centre(run, (e.X, e.Z)), 24, 1f);
                    break;
                }
                case WorldLayout.RunEventKind.Swing when p >= e.S + 9:
                    run.Fired.Add(i);
                    break;
                case WorldLayout.RunEventKind.Topple when p >= e.S:
                {
                    run.Fired.Add(i);
                    if (p > e.S + 9) break;
                    SetPart(run, (e.X, e.Z), 1, null);
                    SetPart(run, (e.X, e.Z), 2, null);
                    var (dx, dz) = Step(e.Face);
                    SetPart(run, (e.X, e.Z), 1, $"run-shelf-fallen-a-{Side(e.Face)}");
                    SetPart(run, (e.X + dx, e.Z + dz), 1, $"run-shelf-fallen-b-{Side(e.Face)}");
                    Play("run/topple", Centre(run, (e.X, e.Z)), 24, 1f);
                    break;
                }
                case WorldLayout.RunEventKind.Dented:
                    if (p >= e.S)
                    {
                        run.Fired.Add(i);
                        if (p > e.S + 6) break;
                        SetDoor(run, (e.X, e.Z), "run-sidedoor-open", e.Face);
                        Play("run/doorbreak", Centre(run, (e.X, e.Z)), 32, 0.8f);
                        if (rand.NextDouble() < 0.6) Chase(player, run, Roster.SkinStealer, e.S - 2, 0.8, 0, 12);
                        else for (int r = 0; r < 3; r++) Chase(player, run, Roster.DeathRat, e.S - 2 - r * 0.5, 0.8, (r - 1) * 1.2, 12);
                    }
                    else if (p >= e.S - 22 && rand.NextDouble() < dt / 0.9)
                        Play("run/bang" + rand.Next(1, 4), Centre(run, (e.X, e.Z)), 24, 0.7f);
                    break;
                case WorldLayout.RunEventKind.Vent when i == run.VentEvent && p >= e.S + 1:
                    run.Fired.Add(i);
                    SetPart(run, (e.X, e.Z), 5, "run-ceiling-vent-burst");
                    Play("run/ventburst", Centre(run, (e.X, e.Z), 3), 24, 1f);
                    Chase(player, run, Roster.Hound, p - 3, 1.0, 0, 6);
                    break;
                case WorldLayout.RunEventKind.Sign when i == run.SignEvent:
                    SignBurst(player, run, e, dt);
                    break;
            }
        }
    }

    /// <summary>A sign hisses, flickers, grows too bright, and bursts: a wall of fire across the hall for ten seconds.</summary>
    private void SignBurst(IServerPlayer player, Run run, WorldLayout.RunEvent e, float dt)
    {
        double p = run.P;
        string axis = (run.Plan.At(e.X, e.Z).Detail & WorldLayout.RunSignWE) != 0 ? "we" : "ns";
        Vec3d at = Centre(run, (e.X, e.Z), 3);
        long now = sapi.World.ElapsedMilliseconds;
        if (run.SignStage == 0 && p >= e.S - 40)
        {
            run.SignStage = 1;
            SetPart(run, (e.X, e.Z), 4, $"run-exitsign-flicker-{axis}");
        }
        if (run.SignStage == 1)
        {
            run.NextHiss -= dt;
            if (run.NextHiss <= 0) { run.NextHiss = 2.8; Play("run/signhiss", at, 20, 0.8f); }
            if (p >= e.S - 14)
            {
                run.SignStage = 2;
                SetPart(run, (e.X, e.Z), 4, $"run-exitsign-dead-{axis}");
                Play("run/signburst", at, 32, 1f);
                run.FireUntil = now + 10_000;
                Flash(at);
            }
        }
        if (run.SignStage == 2)
        {
            if (now > run.FireUntil)
            {
                run.SignStage = 3;
                run.Fired.Add(run.SignEvent);
                return;
            }
            // The curtain of fire: three blocks deep, wall to wall
            for (int k = -1; k <= 2; k++) Flames(Along(run, e.S + k, 0, 0));
            if (p >= e.S - 1.5 && p <= e.S + 2.5 && player.Entity.Alive) player.Entity.Ignite();
        }
    }

    private void Flash(Vec3d at)
    {
        var flash = new SimpleParticleProperties(30, 40, ColorUtil.ToRgba(255, 255, 250, 220), at.AddCopy(-0.5, -0.3, -0.5), at.AddCopy(0.5, 0.3, 0.5),
            new Vec3f(-3, -2, -3), new Vec3f(3, 1, 3), 0.25f, 0.3f, 0.6f, 1.2f, EnumParticleModel.Quad);
        flash.VertexFlags = 255;
        sapi.World.SpawnParticles(flash);
    }

    private void Flames(Vec3d at)
    {
        var fire = new SimpleParticleProperties(6, 10, ColorUtil.ToRgba(220, 255, 140, 30), at.AddCopy(-2.4, -1, -0.5), at.AddCopy(2.4, 1.2, 0.5),
            new Vec3f(-0.2f, 0.5f, -0.2f), new Vec3f(0.2f, 1.6f, 0.2f), 0.8f, -0.05f, 0.5f, 1.4f, EnumParticleModel.Quad);
        fire.VertexFlags = 200;
        fire.SelfPropelled = true;
        fire.OpacityEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, -160);
        sapi.World.SpawnParticles(fire);
    }

    /// <summary>Sprinting over something small in the dark: you trip.</summary>
    private void Trip(IServerPlayer player, Run run, float dt)
    {
        EntityPlayer entity = player.Entity;
        run.TripCooldown -= dt;
        if (run.TripUntil > 0)
        {
            run.TripUntil -= dt;
            if (run.TripUntil <= 0) entity.Stats.Remove("walkspeed", TripStat);
        }
        if (run.TripCooldown > 0 || !entity.Controls.Sprint || !entity.Controls.TriesToMove || !entity.OnGround) return;
        var (lx, lz) = layout.RunLocal(run.Lane, (int)Math.Floor(entity.Pos.X), (int)Math.Floor(entity.Pos.Z));
        if (!run.Plan.In(lx, lz)) return;
        if (run.Plan.At(lx, lz).Variant is not (Worldgen.Props.RunToyCar or Worldgen.Props.RunBoxes or Worldgen.Props.RunCord or Worldgen.Props.RunDebris)) return;
        run.TripCooldown = 2;
        run.TripUntil = 0.8;
        entity.Stats.Set("walkspeed", TripStat, TripSlow, false);
        Play("run/trip", entity.Pos.XYZ, 12, 1f);
    }

    // ================= The doors of the start room, and the rest =================

    /// <summary>Someone uses one of the level's doors that are not thresholds (<see cref="BlockBehaviorRunDoor"/>).</summary>
    public void UseDoor(IServerPlayer player, BlockPos pos, string kind)
    {
        if (layout == null) return;
        string message = null;
        int lane = layout.RunLaneAt(pos.X, pos.Z);
        switch (kind)
        {
            case "runhall":
            {
                runs.TryGetValue(player.PlayerUID, out Run run);
                // It sticks: it opens on the third try
                int tries = run != null ? ++run.HallTries : 3;
                if (tries < 3)
                {
                    Play("run/rattle", pos.ToVec3d().Add(0.5, 0.5, 0.5), 16, 1f);
                    message = "backrooms:run-stuck";
                    break;
                }
                if (lane >= 0)
                {
                    var plan = layout.RunPlan(lane);
                    SetDoor(lane, plan.HallDoor, "run-halldoor-open", plan.At(plan.HallDoor.X, plan.HallDoor.Z).Pier);
                }
                sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 16);
                break;
            }
            case "runfake":
            {
                if (lane < 0) break;
                var (lx, lz) = layout.RunLocal(lane, pos.X, pos.Z);
                var tile = layout.RunPlan(lane).At(lx, lz);
                SetDoor(lane, (lx, lz), "run-exitdoor-fake-open", tile.Pier);
                sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 16);
                message = "backrooms:run-fake";
                break;
            }
            case "runchained":
                Play("run/bang" + rand.Next(1, 4), pos.ToVec3d().Add(0.5, 0.5, 0.5), 24, 1f);
                message = "backrooms:run-chained";
                break;
            case "runmarked":
                Play("run/rattle", pos.ToVec3d().Add(0.5, 0.5, 0.5), 16, 1f);
                message = "backrooms:run-marked";
                break;
            default:
                Play("run/rattle", pos.ToVec3d().Add(0.5, 0.5, 0.5), 16, 1f);
                message = "backrooms:run-locked";
                break;
        }
        if (message != null) player.SendIngameError("backrooms-run", Lang.Get(message));
    }

    private void SetDoor(Run run, (int X, int Z) local, string code, ArchPier face) => SetDoor(run.Lane, local, code, face);

    private void SetDoor(int lane, (int X, int Z) local, string code, ArchPier face)
    {
        SetPart(lane, local, 1, $"{code}-lower-{Side(face)}");
        SetPart(lane, local, 2, $"{code}-upper-{Side(face)}");
    }

    private void SwapDoor(Run run, (int X, int Z) local, string code, ArchPier face, ref int stage, int to)
    {
        SetDoor(run, local, code, face);
        stage = to;
    }

    private void SetPart(Run run, (int X, int Z) local, int rel, string code) => SetPart(run.Lane, local, rel, code);

    /// <summary>Puts a block of the level's (or air, for null) at <paramref name="rel"/> above the floor of a lane's tile.</summary>
    private void SetPart(int lane, (int X, int Z) local, int rel, string code)
    {
        var (x, z) = layout.RunWorld(lane, local.X, local.Z);
        var pos = new BlockPos(x, geometry.FloorFor(WorldLayout.RunLevel) + rel, z);
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(pos) == null) return;
        int id = code == null ? 0 : BlockId(code);
        if (code != null && id == 0) return; // not built yet
        sapi.World.BlockAccessor.SetBlock(id, pos);
        sapi.World.BlockAccessor.MarkBlockDirty(pos);
    }

    // ================= Putting a lane back =================

    /// <summary>Puts back, as they were generated, the rows of a lane the course reaches 40 to 80 blocks ahead of the runner.</summary>
    private void RestoreAhead(Run run)
    {
        int from = run.Plan.LineAt((int)run.P + 40).Z, to = run.Plan.LineAt((int)run.P + 80).Z;
        RestoreRows(run, Math.Min(from, to), Math.Max(from, to));
    }

    private void RestoreRows(Run run, int z0, int z1)
    {
        if (generator == null) return;
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        int floor = geometry.FloorFor(WorldLayout.RunLevel);
        z0 = Math.Max(0, z0);
        z1 = Math.Min(WorldLayout.RunLaneLength - 1, z1);
        var pos = new BlockPos(0, 0, 0);
        for (int z = z0; z <= z1; z++)
        {
            if (run.Restored[z]) continue;
            bool done = true;
            for (int x = 0; x < WorldLayout.RunLane.Width; x++)
            {
                Tile plan = run.Plan.At(x, z);
                bool movable = plan.Kind != TileKind.Wall || plan.Pattern == WallPattern.RunMedCabinet;
                if (!movable) continue;
                var (gx, gz) = layout.RunWorld(run.Lane, x, z);
                pos.Set(gx, floor, gz);
                if (blocks.GetChunkAtBlockPos(pos) == null) { done = false; continue; }
                Tile tile = layout.TileAt(gx, gz);
                for (int rel = 0; rel <= 5; rel++)
                {
                    pos.Set(gx, floor + rel, gz);
                    int want = generator.ColumnBlock(tile, gx, gz, floor + rel, out _);
                    if (blocks.GetBlock(pos).BlockId != want) blocks.SetBlock(want, pos);
                }
            }
            run.Restored[z] = done;
        }
    }

    /// <summary>
    /// Out of the true exit: the door they came out of stands in the wall beside them, a red door now, a way into
    /// Level ! for anyone who has not been there ("the exit door has been converted into an entrance door").
    /// </summary>
    private void LeaveExitDoor(Link to)
    {
        int x = (int)Math.Floor(to.X), z = (int)Math.Floor(to.Z);
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
        int floor = geometry.FloorFor(level);
        // (Standing in the air in front of the wall, flush against it, as the arrival door is made)
        foreach (ArchPier dir in new[] { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West })
        {
            var (dx, dz) = Step(dir);
            if (layout.TileAt(x + dx, z + dz).Kind != TileKind.Wall) continue;
            // It faces away from the wall, toward where they stand
            ArchPier face = dir switch { ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East };
            var lower = new BlockPos(x, (int)Math.Floor(to.Y + 0.01), z);
            if (sapi.World.BlockAccessor.GetChunkAtBlockPos(lower) == null) return;
            if (sapi.World.BlockAccessor.GetBlock(lower).BlockId != 0 || sapi.World.BlockAccessor.GetBlock(lower.UpCopy()).BlockId != 0) return;
            int lo = BlockId($"run-exitdoor-arrival-lower-{Side(face)}"), up = BlockId($"run-exitdoor-arrival-upper-{Side(face)}");
            if (lo == 0 || up == 0) return;
            sapi.World.BlockAccessor.SetBlock(lo, lower);
            sapi.World.BlockAccessor.SetBlock(up, lower.UpCopy());
            return;
        }
    }

    private void Play(string sound, Vec3d at, int range, float volume) =>
        sapi.World.PlaySoundAt(new AssetLocation("backrooms", "sounds/effect/" + sound), at.X, at.Y, at.Z, null, true, range, volume);

    // ================= The Energy Bar's second wind =================

    /// <summary>An Energy Bar was eaten: a little more speed for half a minute.</summary>
    public static void GiveSecondWind(EntityAgent entity)
    {
        entity.Stats.Set("walkspeed", WindStat, SecondWind, false);
        entity.Attributes.SetLong(SecondWindKey, entity.World.ElapsedMilliseconds + 30_000);
    }

    private static void SecondWindTick(EntityAgent entity, long now)
    {
        long until = entity.Attributes.GetLong(SecondWindKey, 0);
        if (until == 0 || now < until) return;
        entity.Stats.Remove("walkspeed", WindStat);
        entity.Attributes.RemoveAttribute(SecondWindKey);
    }

    // ================= Commands =================

    /// <summary>What a player's run looks like now (for /backrooms run).</summary>
    public string Describe(IServerPlayer player)
    {
        if (!runs.TryGetValue(player.PlayerUID, out Run run)) return HasRanOut(player.Entity) ? "No run (escaped once already)" : "No run";
        var c = run.Chase;
        return $"Lane {run.Lane}, at {run.P:0} of {run.Plan.ExitS}, front {c.Front:0.0} (gap {c.Gap(run.P):0.0}), " +
            $"{(c.Loose ? "loose" : $"behind the door ({c.Elapsed:0.0} s)")}, sprint {c.Sprint:0.00}, exit to {WorldLayout.DisplayNumber(run.Plan.Destination)}";
    }
}

/// <summary>An Energy Bar: food, and a second wind for half a minute.</summary>
public class ItemEnergyBar : Item
{
    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;
        RunSystem.GiveSecondWind(byEntity);
    }
}

/// <summary>Level !'s doors that are not ways anywhere: the stuck hall door, the chained door, side doors, the false exits.</summary>
public class BlockBehaviorRunDoor : BlockBehavior
{
    private string kind = "runlocked";

    public BlockBehaviorRunDoor(Block block) : base(block)
    {
    }

    public override void Initialize(JsonObject properties)
    {
        base.Initialize(properties);
        kind = properties?["kind"].AsString("runlocked") ?? "runlocked";
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player)
            sapi.ModLoader.GetModSystem<RunSystem>()?.UseDoor(player, blockSel.Position, kind);
        return true;
    }
}

/// <summary>
/// An emergency beacon on a wall of Level !: dark, until the alarm goes; then it flashes red once a second (a quarter of
/// a second on). Glow only: real light changing several times a second would be far too costly, as with failing lights.
/// </summary>
public class BlockEntityRunBeacon : BlockEntity
{
    private bool lit;
    private long listener;
    private MeshData offMesh;

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (api is ICoreClientAPI capi) listener = RegisterGameTickListener(_ => Pulse(capi), 50);
    }

    private void Pulse(ICoreClientAPI capi)
    {
        var player = capi.World.Player?.Entity;
        bool alarm = player != null && player.WatchedAttributes.GetInt(RunSystem.PhaseKey) == (int)RunSystem.Phase.Alarm
            && player.Pos.SquareDistanceTo(Pos.X + 0.5, Pos.Y, Pos.Z + 0.5) < 32 * 32;
        bool on = alarm && capi.World.ElapsedMilliseconds % 1000 < 250;
        if (on == lit) return;
        lit = on;
        MarkDirty(redrawOnClient: true);
    }

    public override bool OnTesselation(ITerrainMeshPool mesher, ITesselatorAPI tesselator)
    {
        if (lit) return false;
        if (offMesh == null)
        {
            string off = Block.Code.Path.Replace("-lit-", "-dark-");
            Block offBlock = Api.World.GetBlock(new AssetLocation("backrooms", off)) ?? Block;
            tesselator.TesselateBlock(offBlock, out offMesh);
        }
        mesher.AddMeshData(offMesh);
        return true;
    }
}
