using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// What an Ambient Death Rat does (README 6.1: "scavenger first"). Rats put down in the heart of a level are not after
/// anyone: they go to food lying on the floor (dropped food items, carcasses) within <c>foodRange</c> blocks and eat it,
/// one item at a time, and they scatter from a walking person within <c>scatterRange</c> blocks (closer, when the person
/// creeps or stands still) and from a carried light.
///
/// They bite only when they have to: cornered (a person within <c>corneredRange</c> and no open floor away from them
/// within <c>corneredOpen</c>: it bites once, then runs again), or when a pack of <c>packBites</c> or more is near
/// someone below <c>packBiteHealth</c> of their health. (At the edge of a level and in a den the director puts them down
/// hunting, as before.) A rat of a harmless look (Level 2's hairless ones, see <see cref="EntityBehaviorMenace.Harmless"/>)
/// never bites at all.
///
/// The menace task takes over when the encounter becomes anything but Ambient, so a bite is a turn to the hunt.
/// </summary>
public class AiTaskScavenge : AiTaskBase
{
    private enum Mode { None, Scatter, GoToFood, Eat }

    // ---- Config (every number is in the generator; these are the defaults) ----
    private readonly float walkSpeed, runSpeed, foodRange, scatterRange, sneakScatterRange, lightScatterRange, scatterDistance, scatterSeconds;
    private readonly float eatSeconds, carcassSeconds, corneredRange, corneredOpen, packBiteHealth, packRange;
    private readonly int packBites, torchLight;
    private readonly string eatAnim;
    private readonly AssetLocation eatSound;

    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private Mode mode;
    private Entity food, threat;
    private long nextLookMs, nextThinkMs, scatterEndMs, nextBiteMs, eatEndMs, startedMs, lastPathMs;
    private bool arrived, stuck, noPath, eating;
    /// <summary>The gait it is playing (run to scatter, walk to food), until it settles to eat.</summary>
    private string moveAnim;
    /// <summary>What it has had its fill of, or cannot reach, and until when (entity id to elapsed ms).</summary>
    private readonly Dictionary<long, long> ignored = new();

    public AiTaskScavenge(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.022f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.048f);
        foodRange = taskConfig["foodRange"].AsFloat(16);
        scatterRange = taskConfig["scatterRange"].AsFloat(6);
        sneakScatterRange = taskConfig["sneakScatterRange"].AsFloat(3);
        lightScatterRange = taskConfig["lightScatterRange"].AsFloat(8);
        torchLight = taskConfig["torchLight"].AsInt(10);
        scatterDistance = taskConfig["scatterDistance"].AsFloat(8);
        scatterSeconds = taskConfig["scatterSeconds"].AsFloat(5);
        eatSeconds = taskConfig["eatSeconds"].AsFloat(4);
        carcassSeconds = taskConfig["carcassSeconds"].AsFloat(10);
        corneredRange = taskConfig["corneredRange"].AsFloat(2);
        corneredOpen = taskConfig["corneredOpen"].AsFloat(3);
        packBites = taskConfig["packBites"].AsInt(4);
        packBiteHealth = taskConfig["packBiteHealth"].AsFloat(0.5f);
        packRange = taskConfig["packRange"].AsFloat(12);
        eatAnim = taskConfig["eatAnimation"].AsString("eat");
        string sound = taskConfig["eatSound"].AsString(null);
        eatSound = sound == null ? null : AssetLocation.Create(sound, "backrooms").WithPathPrefixOnce("sounds/");
    }

    // ================= Deciding =================

    public override bool ShouldExecute()
    {
        if (!entity.Alive) return false;
        long now = entity.World.ElapsedMilliseconds;
        if (now < nextLookMs) return false;
        nextLookMs = now + 400;
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null || menace.Kind != Encounter.Ambient) return false;
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        Entity who = Threat();
        if (who != null)
        {
            if (Escalate(who)) return false;
            threat = who;
            mode = Mode.Scatter;
            return true;
        }
        food = FindFood(now);
        if (food == null) return false;
        mode = Mode.GoToFood;
        return true;
    }

    /// <summary>The nearest person it would run from: walking near it, or carrying a light, or (creeping or standing) very near.</summary>
    private Entity Threat()
    {
        float reach = Math.Max(scatterRange, lightScatterRange);
        Entity nearest = null;
        double best = double.MaxValue;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, reach, 6, IsPerson))
        {
            double d = entity.Pos.DistanceTo(e.Pos);
            float range = Walking(e) ? scatterRange : sneakScatterRange;
            if (Senses.HeldLight(e) >= torchLight) range = Math.Max(range, lightScatterRange);
            if (d > range || d >= best) continue;
            best = d;
            nearest = e;
        }
        return nearest;
    }

    private static bool IsPerson(Entity e) =>
        e.Alive && (Senses.IsTestTarget(e) || e is EntityPlayer p && p.Player?.WorldData.CurrentGameMode != EnumGameMode.Spectator);

    /// <summary>Whether someone is walking about (not creeping, not standing still); a straw dummy always is, unless it sneaks.</summary>
    private static bool Walking(Entity e)
    {
        if (Senses.IsTestTarget(e)) return !Senses.Sneaking(e);
        return e is EntityAgent a && a.ServerControls.TriesToMove && !a.ServerControls.Sneak;
    }

    /// <summary>
    /// Turns to a bite if this person has cornered it, or a pack of it is round someone who is hurt. Returns whether it
    /// did (it is then no longer Ambient).
    /// </summary>
    private bool Escalate(Entity who)
    {
        if (menace.Harmless) return false;
        double d = entity.Pos.DistanceTo(who.Pos);
        bool cornered = d <= corneredRange && Cornered(who);
        bool pack = false;
        if (!cornered && d <= scatterRange && who.GetBehavior<EntityBehaviorHealth>() is { MaxHealth: > 0 } health && health.Health / health.MaxHealth < packBiteHealth)
        {
            pack = entity.World.GetEntitiesAround(entity.Pos.XYZ, packRange, 6, e => e.Alive && e.Code == entity.Code).Length >= packBites;
        }
        if (!cornered && !pack) return false;
        Log("{0}: it bites", cornered ? "cornered" : "a pack round someone hurt");
        menace.Target = who;
        menace.Belief.Forget();
        menace.Passive = false;
        if (cornered) entity.Attributes.SetBool(AiTaskMenace.CorneredKey, true);
        menace.Kind = Encounter.Hunt;
        return true;
    }

    /// <summary>Cornered: no open floor within <c>corneredOpen</c> blocks, on the far side of it from this person.</summary>
    private bool Cornered(Entity who)
    {
        double away = Math.Atan2(entity.Pos.Z - who.Pos.Z, entity.Pos.X - who.Pos.X);
        Vec3d from = entity.Pos.XYZ.Add(0, 0.3, 0);
        for (int step = -2; step <= 2; step++)
        {
            double angle = away + step * Math.PI / 6;
            int x = (int)Math.Floor(entity.Pos.X + Math.Cos(angle) * corneredOpen), z = (int)Math.Floor(entity.Pos.Z + Math.Sin(angle) * corneredOpen);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 1, 1);
            if (y == int.MinValue) continue;
            if (Senses.ClearLine(entity.World, from, new Vec3d(x + 0.5, y + 0.3, z + 0.5))) return false;
        }
        return true;
    }

    /// <summary>The nearest thing to eat: food lying on the floor, or a carcass.</summary>
    private Entity FindFood(long now)
    {
        foreach (long id in new List<long>(ignored.Keys)) if (ignored[id] < now) ignored.Remove(id);
        Entity best = null;
        double bestDistance = double.MaxValue;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, foodRange, 6, e => IsFood(e) && !ignored.ContainsKey(e.EntityId)))
        {
            double d = entity.Pos.DistanceTo(e.Pos);
            if (d >= bestDistance) continue;
            bestDistance = d;
            best = e;
        }
        return best;
    }

    private bool IsFood(Entity e)
    {
        if (e is EntityItem item)
        {
            ItemStack stack = item.Itemstack;
            return item.Alive && stack?.Collectible != null && stack.StackSize > 0
                   && (stack.Collectible.NutritionProps != null || stack.Collectible.GetNutritionProperties(entity.World, stack, entity) != null);
        }
        return !e.Alive && e is EntityAgent && e is not EntityPlayer;
    }

    // ================= Doing =================

    public override void StartExecute()
    {
        base.StartExecute();
        long now = entity.World.ElapsedMilliseconds;
        startedMs = now;
        arrived = stuck = noPath = eating = false;
        Log("{0}", mode == Mode.Scatter ? "scatters from " + threat.Code.Path : "goes to eat " + food.Code.Path);
        moveAnim = mode == Mode.Scatter ? "run" : "walk";
        entity.AnimManager.StartAnimation(moveAnim);
        if (mode == Mode.Scatter) Scatter(now);
        else GoTo(food.Pos.XYZ, walkSpeed, 1.0f);
    }

    private void Scatter(long now)
    {
        scatterEndMs = now + (long)(scatterSeconds * 1000);
        Random rand = entity.World.Rand;
        double away = Math.Atan2(entity.Pos.Z - threat.Pos.Z, entity.Pos.X - threat.Pos.X);
        for (int i = 0; i < 8; i++)
        {
            double angle = away + (rand.NextDouble() - 0.5) * (i < 4 ? 1.2 : 3);
            int x = (int)Math.Floor(entity.Pos.X + Math.Cos(angle) * scatterDistance), z = (int)Math.Floor(entity.Pos.Z + Math.Sin(angle) * scatterDistance);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 1, 4);
            if (y == int.MinValue) continue;
            GoTo(new Vec3d(x + 0.5, y, z + 0.5), runSpeed, 1);
            return;
        }
        // Nowhere better: straight off
        pathTraverser.WalkTowards(entity.Pos.XYZ.Add(Math.Cos(away) * 4, 0, Math.Sin(away) * 4), runSpeed, 1, () => arrived = true, () => stuck = true);
    }

    private void GoTo(Vec3d to, float speed, float within)
    {
        lastPathMs = entity.World.ElapsedMilliseconds;
        pathTraverser.NavigateTo_Async(to.Clone(), speed, within, () => arrived = true, () => stuck = true, () => noPath = true, 2000, 1);
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || menace == null || menace.Kind != Encounter.Ambient) return false;
        long now = entity.World.ElapsedMilliseconds;
        if (now >= nextThinkMs)
        {
            nextThinkMs = now + 300;
            Entity who = Threat();
            if (who != null)
            {
                if (Escalate(who)) return false;
                // Something to run from, and it was eating or on its way: look again as a scatter
                if (mode != Mode.Scatter) return false;
            }
        }
        switch (mode)
        {
            case Mode.Scatter:
                return !(arrived || stuck || noPath || now > scatterEndMs);
            case Mode.GoToFood:
                if (!StillFood()) return false;
                if (noPath || now - startedMs > 14_000)
                {
                    ignored[food.EntityId] = now + 60_000;
                    Log("cannot reach it");
                    return false;
                }
                if (entity.Pos.XYZ.HorizontalSquareDistanceTo(food.Pos.X, food.Pos.Z) < 1.4 * 1.4 && Math.Abs(entity.Pos.Y - food.Pos.Y) < 1.5)
                {
                    pathTraverser.Stop();
                    BeginEating(now);
                    return true;
                }
                if (!pathTraverser.Active && now - lastPathMs > 1200) GoTo(food.Pos.XYZ, walkSpeed, 1.0f);
                return true;
            case Mode.Eat:
                if (!StillFood()) return false;
                FaceFood(dt);
                if (now < nextBiteMs) return true;
                if (food is EntityItem item)
                {
                    Eat(item);
                    nextBiteMs = now + (long)(eatSeconds * 1000);
                    return StillFood();
                }
                // A carcass: it nibbles for a while, then has had enough of it (it is not used up)
                if (now >= eatEndMs)
                {
                    ignored[food.EntityId] = now + 300_000;
                    Log("has had enough of {0}", food.Code.Path);
                    return false;
                }
                nextBiteMs = now + 2500;
                PlayEat();
                return true;
        }
        return false;
    }

    private bool StillFood() =>
        food != null && food.State != EnumEntityState.Despawned && (food is not EntityItem it || it.Alive && it.Itemstack?.StackSize > 0);

    private void BeginEating(long now)
    {
        mode = Mode.Eat;
        eating = true;
        StopMoveAnim();
        entity.AnimManager.StartAnimation(eatAnim);
        nextBiteMs = now + (long)(eatSeconds * 1000);
        eatEndMs = now + (long)(carcassSeconds * 1000);
        Log("eats {0}", food.Code.Path);
    }

    private void FaceFood(float dt)
    {
        float desired = (float)Math.Atan2(food.Pos.X - entity.Pos.X, food.Pos.Z - entity.Pos.Z);
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float step = 4f * dt;
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -step, step)) % GameMath.TWOPI;
    }

    /// <summary>Takes one of a stack of food (and the lot, when it is the last).</summary>
    private void Eat(EntityItem item)
    {
        ItemStack stack = item.Itemstack.Clone();
        stack.StackSize--;
        PlayEat();
        Log("ate one {0} ({1} left)", stack.Collectible.Code.Path, stack.StackSize);
        if (stack.StackSize <= 0) item.Die(EnumDespawnReason.Death);
        else item.Itemstack = stack;
    }

    private void PlayEat()
    {
        if (eatSound != null) entity.World.PlaySoundAt(eatSound, entity.Pos.X, entity.Pos.Y + 0.3, entity.Pos.Z, null, true, 12, 0.6f);
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        pathTraverser.Stop();
        StopMoveAnim();
        if (eating) entity.AnimManager.StopAnimation(eatAnim);
        eating = false;
        mode = Mode.None;
    }

    private void StopMoveAnim()
    {
        if (moveAnim != null) entity.AnimManager.StopAnimation(moveAnim);
        moveAnim = null;
    }

    private void Log(string format, params object[] args)
    {
        if (director?.Logging != true || entity.Api is not ICoreServerAPI sapi) return;
        sapi.Logger.Notification("[backrooms] {0} #{1} at {2:0},{3:0},{4:0}: scavenger {5}", entity.Code.Path, entity.EntityId, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, string.Format(format, args));
    }
}
