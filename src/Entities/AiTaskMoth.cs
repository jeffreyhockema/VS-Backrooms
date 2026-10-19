using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>
/// Deathmoths. Open flame draws them: they come out of the dark to circle a torch, bump at it and drift about it, and
/// the females, in swarms near the edges of a level, bite whoever carries it. A candle draws them only a little and
/// a closed lantern not at all; smoke (a lit firepit, burning Firesalt) scatters them.
///
/// With no flame about they flutter near where they were and now and then settle on a floor or the top of something,
/// wings folded, for a while. The males go looking for something to eat or drink: standing water, Almond Water, a
/// body, food dropped on the floor (and keep away from anyone near). A female that
/// is come at while settled, or hurt, rears up and throws her wings open on their eye spots, and calls the rest: every
/// female near turns on whoever it was, flame or no flame, and the males scatter. In Level 3 the males are aggressive
/// too, and bite and answer the alarm as the females do.
/// </summary>
public class AiTaskMoth : AiTaskBase
{
    private enum Settle { None, Landing, Resting, Feeding }

    /// <summary>Entity attribute: a female called by another's alarm (or hurt herself) goes for the one who caused it.</summary>
    public const string AlarmedKey = "backrooms:alarmed";

    /// <summary>Entity attribute: a male put down in a level where the males are aggressive (set when it first flies).</summary>
    public const string AggressiveKey = "backrooms:aggressive";

    /// <summary>How far an alarm carries from a threatening female, or from a hive heart broken.</summary>
    public const float AlarmRadius = 16;

    private readonly float speed, damage, orbitRadius, scavengeRange, scavengeAvoid, startleLoudness;
    private readonly int aggressiveLevel;
    private readonly bool bites;
    private readonly SenseProfile senses;
    private bool aggressive;
    private readonly AssetLocation biteSound;

    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private Vec3d goal, home, perch;
    private float think, phase, nextBite;
    /// <summary>What the level's danger does to its speed (see <see cref="Danger"/>), read when it first flies.</summary>
    private float speedMul = -1;
    private double drawn;
    private int thoughts;
    private Settle settle;
    private long settledUntilMs, lastThreatMs = -100_000;

    public AiTaskMoth(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        speed = taskConfig["speed"].AsFloat(0.03f);
        damage = taskConfig["damage"].AsFloat(1);
        orbitRadius = taskConfig["orbitRadius"].AsFloat(1.6f);
        bites = taskConfig["bites"].AsBool(false);
        aggressiveLevel = taskConfig["aggressiveLevel"].AsInt(-1);
        scavengeRange = taskConfig["scavengeRange"].AsFloat(12);
        scavengeAvoid = taskConfig["scavengeAvoid"].AsFloat(5);
        startleLoudness = taskConfig["startleLoudness"].AsFloat(0.5f);
        senses = SenseProfile.Parse(taskConfig["senses"]);
        string sound = taskConfig["biteSound"].AsString(null);
        biteSound = sound == null ? null : AssetLocation.Create(sound, "backrooms").WithPathPrefixOnce("sounds/");
    }

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        return menace != null;
    }

    /// <summary>Whether it bites: the females always, and the males where the level makes them aggressive.</summary>
    private bool Bites => bites || aggressive;

    public override void StartExecute()
    {
        base.StartExecute();
        home ??= entity.Pos.XYZ;
        if (!bites && aggressiveLevel >= 0 && !aggressive && director?.Layout is { } layout
            && layout.LevelAt(Backrooms.Worldgen.WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), Backrooms.Worldgen.WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z))) == aggressiveLevel)
        {
            aggressive = true;
            entity.Attributes.SetBool(AggressiveKey, true);
            Log("is aggressive (Level {0}'s males are)", aggressiveLevel);
        }
        if (speedMul < 0) speedMul = Danger.Speed(Danger.Of(entity));
        phase = (float)(entity.World.Rand.NextDouble() * Math.PI * 2);
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        think -= dt;
        phase += dt * (1.6f + (float)drawn);
        if (think <= 0)
        {
            think = 0.25f;
            Decide();
        }
        Steer(dt);
        return true;
    }

    private bool Alarmed => Bites && entity.Attributes.GetBool(AlarmedKey);

    private void Decide()
    {
        if (++thoughts % 20 == 0) Log("{0}, {1}, drawn {2:0.0}, {3:0.0} blocks from its target", menace.Kind, settle, drawn, menace.Target == null ? -1 : entity.Pos.DistanceTo(menace.Target.Pos));
        Entity target = menace.Target;
        Random rand = entity.World.Rand;
        Encounter kind = menace.Kind;
        long now = entity.World.ElapsedMilliseconds;
        drawn = 0;

        // Moth jelly set down within 24 blocks draws every male to it, whatever else is about (MothJelly.cs)
        if (!bites && BaitPull(now)) return;
        if (kind == Encounter.Leave || target == null || !target.Alive)
        {
            TakeOff();
            Vec3d from = target?.Pos.XYZ ?? home;
            double away = Math.Atan2(entity.Pos.Z - from.Z, entity.Pos.X - from.X);
            goal = entity.Pos.XYZ.Add(Math.Cos(away) * 8, 1, Math.Sin(away) * 8);
            return;
        }

        // Smoke scatters them
        Vec3d ward = Wards.Near(entity.World, entity.Pos.XYZ);
        if (ward != null && ward.DistanceTo(entity.Pos.XYZ) < Wards.Radius)
        {
            TakeOff();
            double away = Math.Atan2(entity.Pos.Z - ward.Z, entity.Pos.X - ward.X);
            goal = entity.Pos.XYZ.Add(Math.Cos(away) * 6, 0.5, Math.Sin(away) * 6);
            return;
        }

        double distance = entity.Pos.DistanceTo(target.Pos);
        if (target is EntityAgent agent && distance < 24) drawn = Senses.MothDraw(agent);
        if (Alarmed) drawn = Math.Max(drawn, 0.6);

        // Settled: stays put, unless a flame calls, someone comes right up, or it has had long enough
        if (settle is Settle.Resting or Settle.Feeding)
        {
            // (A male feeding keeps away from anyone near; any settled moth is startled by a loud noise close by)
            bool disturbed = drawn > 0.25 || distance < 2.5 || now > settledUntilMs || Startled(now) || !Bites && PlayerNear(entity.Pos.XYZ, scavengeAvoid);
            if (!disturbed) return;
            if (Bites && distance < 3.5 && kind is Encounter.Stalk or Encounter.Hunt) Threaten(target);
            TakeOff();
        }

        if (drawn > 0.25 || drawn > 0 && kind == Encounter.Hunt)
        {
            settle = Settle.None;
            // Round and round the flame (or the head of whoever angered them), closer the brighter it is
            Vec3d flame = Senses.Eyes(target).Add(0, -0.2, 0);
            double r = orbitRadius * (1.3 - 0.5 * drawn) + 0.4 * Math.Sin(phase * 0.7);
            goal = flame.Add(Math.Cos(phase) * r, 0.3 * Math.Sin(phase * 1.9), Math.Sin(phase) * r);
            home = target.Pos.XYZ;

            nextBite -= 0.25f;
            if (Bites && kind == Encounter.Hunt && drawn >= 0.5 && entity.Pos.XYZ.DistanceTo(flame) < 2.2 && nextBite <= 0 && !IsCreative(target))
            {
                nextBite = 2 + (float)rand.NextDouble() * 2.5f;
                Bite(target);
            }
            return;
        }

        // On the way down to somewhere to settle
        if (settle == Settle.Landing)
        {
            goal = perch;
            if (entity.Pos.SquareDistanceTo(perch) < 0.2 * 0.2 || entity.OnGround && entity.Pos.SquareDistanceTo(perch) < 0.6 * 0.6)
            {
                bool food = !Bites && NearFood(perch);
                settle = food ? Settle.Feeding : Settle.Resting;
                settledUntilMs = now + (long)((food ? 8 : 10) + rand.NextDouble() * 18) * 1000;
                entity.AnimManager.StartAnimation(food ? "feed" : "rest");
            }
            else if (rand.NextDouble() < 0.01) settle = Settle.None; // (could not get there)
            return;
        }

        // Nothing to draw them: now and then settle somewhere (a male, somewhere to drink), else drift about
        if (rand.NextDouble() < 0.035)
        {
            Vec3d spot = !Bites ? FindFood() ?? FindPerch() : FindPerch();
            if (spot != null)
            {
                perch = spot;
                settle = Settle.Landing;
                goal = perch;
                return;
            }
        }
        if (goal == null || entity.Pos.SquareDistanceTo(goal) < 1 || rand.NextDouble() < 0.06)
        {
            double angle = rand.NextDouble() * Math.PI * 2, d = 1 + rand.NextDouble() * 4;
            int floor = Senses.FindFloor(entity.World, (int)Math.Floor(home.X + Math.Cos(angle) * d), (int)Math.Floor(entity.Pos.Y), (int)Math.Floor(home.Z + Math.Sin(angle) * d), 2, 6);
            double y = floor == int.MinValue ? entity.Pos.Y : floor + 1.4 + rand.NextDouble() * 1.2;
            goal = new Vec3d(home.X + Math.Cos(angle) * d, y, home.Z + Math.Sin(angle) * d);
        }
    }

    // ================= Moth jelly =================

    /// <summary>
    /// A male drawn to moth jelly: flies to the spot beside it and feeds there until it is gone (a player within
    /// scavengeAvoid keeps it off, as with any food). Returns whether it is doing that.
    /// </summary>
    private bool BaitPull(long now)
    {
        Entity bait = BaitSystem.Nearest(entity, BaitSystem.Range);
        if (bait == null) return false;
        Vec3d spot = SpotBeside(bait);
        if (spot == null || PlayerNear(spot, scavengeAvoid)) return false;
        perch = spot;
        goal = spot;
        double dx = entity.Pos.X - spot.X, dz = entity.Pos.Z - spot.Z, dy = entity.Pos.Y - spot.Y;
        if (dx * dx + dz * dz < 1.0 && dy < 1.2)
        {
            if (settle != Settle.Feeding) entity.AnimManager.StartAnimation("feed");
            settle = Settle.Feeding;
            settledUntilMs = now + 4000;
            return true;
        }
        if (settle is Settle.Resting or Settle.Feeding) TakeOff();
        settle = Settle.None;
        return true;
    }

    // ================= Settling =================

    /// <summary>The top of something near home to settle on: a floor, a shelf, a table.</summary>
    private Vec3d FindPerch()
    {
        Random rand = entity.World.Rand;
        for (int i = 0; i < 6; i++)
        {
            double angle = rand.NextDouble() * Math.PI * 2, d = rand.NextDouble() * 4;
            int x = (int)Math.Floor(home.X + Math.Cos(angle) * d), z = (int)Math.Floor(home.Z + Math.Sin(angle) * d);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y) + 1, z, 1, 5);
            if (y == int.MinValue) continue;
            return new Vec3d(x + 0.3 + rand.NextDouble() * 0.4, y, z + 0.3 + rand.NextDouble() * 0.4);
        }
        return null;
    }

    /// <summary>Whether something edible lies on the floor: a dropped food item.</summary>
    private bool IsFoodItem(Entity e) =>
        e is EntityItem { Alive: true } item && item.Itemstack?.Collectible?.GetNutritionProperties(entity.World, item.Itemstack, null) != null;

    /// <summary>A male's: beside dropped food or a body within scavenging range, or at the edge of water (Almond Water too), and never by a player.</summary>
    private Vec3d FindFood()
    {
        Vec3d spot = SpotBeside(entity.World.GetNearestEntity(entity.Pos.XYZ, scavengeRange, 4, IsFoodItem))
            ?? SpotBeside(entity.World.GetNearestEntity(entity.Pos.XYZ, scavengeRange, 4, e => !e.Alive && e is EntityAgent));
        if (spot != null && !PlayerNear(spot, scavengeAvoid)) return spot;
        Random rand = entity.World.Rand;
        int range = (int)scavengeRange;
        for (int i = 0; i < 24; i++)
        {
            int x = (int)Math.Floor(entity.Pos.X) + rand.Next(-range, range + 1), z = (int)Math.Floor(entity.Pos.Z) + rand.Next(-range, range + 1);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 1, 4);
            if (y == int.MinValue) continue;
            var candidate = new Vec3d(x + 0.5, y, z + 0.5);
            if (NearFood(candidate) && !PlayerNear(candidate, scavengeAvoid)) return candidate;
        }
        return null;
    }

    private Vec3d SpotBeside(Entity thing)
    {
        if (thing == null) return null;
        int y = Senses.FindFloor(entity.World, (int)Math.Floor(thing.Pos.X), (int)Math.Floor(thing.Pos.Y), (int)Math.Floor(thing.Pos.Z), 1, 3);
        return y == int.MinValue ? null : new Vec3d(thing.Pos.X + 0.2, y, thing.Pos.Z + 0.2);
    }

    /// <summary>Whether a living player (not in spectator mode) is within a range of a spot.</summary>
    private bool PlayerNear(Vec3d at, double range) =>
        entity.World.GetNearestEntity(at, (float)range, (float)range, e => e is EntityPlayer { Alive: true } p && p.Player?.WorldData.CurrentGameMode != EnumGameMode.Spectator) != null;

    /// <summary>Whether a loud noise (a break, a fight) has just been heard near enough to startle it.</summary>
    private bool Startled(long now) =>
        senses != null && director != null && Perception.HeardAnything(entity, senses, director.Noises, now) is { } noise && noise.Loudness >= startleLoudness;

    /// <summary>Whether there is water, Almond Water, dropped food or a body right beside a spot.</summary>
    private bool NearFood(Vec3d spot)
    {
        IBlockAccessor ba = entity.World.BlockAccessor;
        var at = new BlockPos(0);
        int x0 = (int)Math.Floor(spot.X), y0 = (int)Math.Floor(spot.Y), z0 = (int)Math.Floor(spot.Z);
        for (int dy = -1; dy <= 0; dy++)
            for (int dz = -1; dz <= 1; dz++)
                for (int dx = -1; dx <= 1; dx++)
                {
                    at.Set(x0 + dx, y0 + dy, z0 + dz);
                    if (ba.GetBlock(at, BlockLayersAccess.Fluid).IsLiquid()) return true;
                    Block block = ba.GetBlock(at);
                    if (block?.Code?.Domain == "backrooms" && block.Code.Path.StartsWith("almond")) return true;
                }
        return entity.World.GetNearestEntity(spot, 1.5f, 1.5f, e => !e.Alive && e is EntityAgent || IsFoodItem(e)) != null;
    }

    private void TakeOff()
    {
        if (settle is Settle.Resting or Settle.Feeding)
        {
            entity.AnimManager.StopAnimation("rest");
            entity.AnimManager.StopAnimation("feed");
            goal = entity.Pos.XYZ.Add(0, 1.5, 0);
        }
        settle = Settle.None;
    }

    // ================= Threat and alarm =================

    /// <summary>A female rears and shows her eye spots, and her alarm calls every female near onto whoever caused it.</summary>
    private void Threaten(Entity cause)
    {
        long now = entity.World.ElapsedMilliseconds;
        if (now - lastThreatMs < 6000) return;
        lastThreatMs = now;
        entity.AnimManager.StartAnimation("threat");
        if (biteSound != null) entity.World.PlaySoundAt(biteSound, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, null, 0.6f, 16);
        Log("threatens {0}, and calls the rest", cause?.Code);
        Alarm(entity, cause);
    }

    /// <summary>Whether a Deathmoth bites and answers the alarm: the females, and the males of a level that makes them aggressive.</summary>
    public static bool IsAggressive(Entity moth) => moth.Code.Path.EndsWith("female") || moth.Attributes.GetBool(AggressiveKey);

    /// <summary>Sets every Deathmoth within sixteen blocks of one onto a cause: the females to attack, the males away.</summary>
    public static void Alarm(Entity moth, Entity cause) => AlarmAt(moth.World, moth.Pos.XYZ, cause);

    /// <summary>Sets every Deathmoth within a radius of a spot onto a cause (a hive heart broken sounds the same alarm).</summary>
    public static void AlarmAt(IWorldAccessor world, Vec3d at, Entity cause, float radius = AlarmRadius)
    {
        if (cause == null) return;
        foreach (Entity other in world.GetEntitiesAround(at, radius, 8, e => e.Alive && e.Code.Path.StartsWith("deathmoth")))
        {
            var behavior = other.GetBehavior<EntityBehaviorMenace>();
            if (behavior == null) continue;
            if (IsAggressive(other)) Rally(other, cause);
            else behavior.Kind = Encounter.Leave;
        }
    }

    /// <summary>Sets one aggressive moth onto a cause (called by an alarm, and for the waves a broken hive heart sends).</summary>
    public static void Rally(Entity moth, Entity cause)
    {
        var behavior = moth.GetBehavior<EntityBehaviorMenace>();
        if (behavior == null || cause == null) return;
        moth.Attributes.SetBool(AlarmedKey, true);
        behavior.Target = cause;
        behavior.Passive = false;
        if (behavior.Kind != Encounter.Leave) behavior.Kind = Encounter.Hunt;
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        Entity cause = source.GetCauseEntity();
        if (menace == null || cause is not EntityAgent) return;
        TakeOff();
        if (Bites) Threaten(cause);
        else menace.Kind = Encounter.Leave;
    }

    // ================= Flight =================

    private void Steer(float dt)
    {
        if (settle is Settle.Resting or Settle.Feeding || goal == null)
        {
            entity.Controls.WalkVector.Set(0, 0, 0);
            entity.Controls.FlyVector.Set(0, 0, 0);
            return;
        }
        double dx = goal.X - entity.Pos.X, dy = goal.Y - entity.Pos.Y, dz = goal.Z - entity.Pos.Z;
        double length = Math.Sqrt(dx * dx + dy * dy + dz * dz);
        if (length < 0.05)
        {
            entity.Controls.WalkVector.Set(0, 0, 0);
            return;
        }
        // A moth's flight is never straight (but it comes down to land carefully)
        double wobble = (settle == Settle.Landing && length < 1.5 ? 0.1 : 0.35) * Math.Sin(phase * 5.3);
        float s = speed * speedMul * (float)(drawn > 0 ? 1.4 : 1) * (float)Math.Min(1, length);
        entity.Controls.WalkVector.Set(dx / length + wobble * dz / length, dy / length * 1.2, dz / length - wobble * dx / length);
        entity.Controls.WalkVector.Mul(s);
        entity.Controls.FlyVector.Set(entity.Controls.WalkVector);
        entity.Pos.Yaw = (float)Math.Atan2(dx, dz);
    }

    private void Bite(Entity target)
    {
        float scaled = damage * Danger.Damage(Danger.Of(entity)) * (float)director.Setting.Damage * GlobalConstants.CreatureDamageModifier;
        if (scaled <= 0) return;
        target.ReceiveDamage(new DamageSource
        {
            Source = EnumDamageSource.Entity,
            SourceEntity = entity,
            Type = EnumDamageType.PiercingAttack,
            DamageTier = 0,
            KnockbackStrength = 0,
        }, scaled);
        if (biteSound != null) entity.World.PlaySoundAt(biteSound, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, null, true, 12);
        entity.AnimManager.StartAnimation("bite");
        Log("bit {0} for {1:0.0}", target.Code, scaled);
        director.NoteCloseCall(target);
    }

    private void Log(string format, params object[] args)
    {
        if (director?.Logging != true || entity.Api is not Vintagestory.API.Server.ICoreServerAPI sapi) return;
        sapi.Logger.Notification("[backrooms] {0} #{1} at {2:0},{3:0},{4:0}: {5}", entity.Code.Path, entity.EntityId, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, string.Format(format, args));
    }

    private static bool IsCreative(Entity target) =>
        target is EntityPlayer player && player.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator;

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        TakeOff();
        entity.Controls.WalkVector.Set(0, 0, 0);
        entity.Controls.FlyVector.Set(0, 0, 0);
    }
}

/// <summary>
/// Almond Water's hold on the Dullers: they leave alone anyone who has drunk it lately, and anyone standing near a
/// fountain or a seep of it.
/// </summary>
public static class AlmondWater
{
    /// <summary>Entity attribute holding when its owner last drank (calendar hours, which survive a restart).</summary>
    public const string DrankKey = "backrooms:almondDrankHours";

    /// <summary>How long a drink keeps them off: two and a half in-game hours, five real minutes.</summary>
    public const double WardHours = 2.5;

    /// <summary>How near an Almond Water fountain or seep keeps them off.</summary>
    public const int SourceRadius = 6;

    public static void Drank(Entity entity) => entity.Attributes.SetDouble(DrankKey, entity.World.Calendar.TotalHours);

    /// <summary>Whether a drink still keeps the Dullers off someone.</summary>
    public static bool Protects(Entity entity) => entity.World.Calendar.TotalHours - entity.Attributes.GetDouble(DrankKey, -1000) < WardHours;

    private static readonly Dictionary<(int, int, int), (long At, bool Found)> Cache = new();

    /// <summary>Whether a fountain or seep of Almond Water stands within a few blocks of a position (cached per 4-block cell for a few seconds).</summary>
    public static bool Near(IWorldAccessor world, Vec3d pos)
    {
        int cx = (int)Math.Floor(pos.X) >> 2, cy = (int)Math.Floor(pos.Y) >> 2, cz = (int)Math.Floor(pos.Z) >> 2;
        long now = world.ElapsedMilliseconds;
        lock (Cache)
        {
            if (Cache.TryGetValue((cx, cy, cz), out var hit) && now - hit.At < 4000 && hit.At <= now) return hit.Found;
            if (Cache.Count > 4096) Cache.Clear();
        }
        int x0 = (cx << 2) + 2, y0 = (cy << 2) + 2, z0 = (cz << 2) + 2, r = SourceRadius + 2;
        IBlockAccessor ba = world.BlockAccessor;
        var at = new BlockPos(0);
        bool found = false;
        for (int y = y0 - 4; y <= y0 + 3 && !found; y++)
            for (int z = z0 - r; z <= z0 + r && !found; z++)
                for (int x = x0 - r; x <= x0 + r && !found; x++)
                {
                    Block block = ba.GetBlock(at.Set(x, y, z));
                    if (block?.Code?.Domain == "backrooms" && block.Code.Path.StartsWith("almond")) found = true;
                }
        lock (Cache) Cache[(cx, cy, cz)] = (now, found);
        return found;
    }

    /// <summary>Forgets what is cached (its times are of the last world's clock): at each server start.</summary>
    public static void Invalidate() { lock (Cache) Cache.Clear(); }
}
