using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Entities;

/// <summary>A blow from an entity, scaled by the world's entity setting; a close call for whoever takes it.</summary>
public static class Strike
{
    public static void Hit(Entity attacker, Entity target, float damage, EnumDamageType type, int tier, float knockback)
    {
        MenaceSystem director = attacker.Api.ModLoader.GetModSystem<MenaceSystem>();
        float scaled = damage * (float)(director?.Setting.Damage ?? 1) * GlobalConstants.CreatureDamageModifier;
        if (scaled <= 0) return;
        target.ReceiveDamage(new DamageSource
        {
            Source = EnumDamageSource.Entity,
            SourceEntity = attacker,
            Type = type,
            DamageTier = tier,
            KnockbackStrength = knockback,
        }, scaled);
        director?.NoteCloseCall(target);
        Log(attacker, "hit {0} for {1:0.0}", target.Code, scaled);
    }

    public static bool IsCreative(Entity target) =>
        target is EntityPlayer player && player.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator;

    public static void Log(Entity entity, string format, params object[] args)
    {
        if (entity.Api is not ICoreServerAPI sapi || sapi.ModLoader.GetModSystem<MenaceSystem>()?.Logging != true) return;
        sapi.Logger.Notification("[backrooms] {0} #{1} at {2:0},{3:0},{4:0}: {5}", entity.Code.Path, entity.EntityId, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, string.Format(format, args));
    }
}

/// <summary>
/// A Clump: a bundle of limbs that buries itself where it waits, a single arm left out of the floor like something
/// dropped there, a finger twitching now and then. Whoever comes within a few blocks wakes it: the floor gives up the
/// whole knot of limbs, and anyone within reach is grabbed and dragged at, after which it feeds a moment. It hunts by
/// sound: a player who runs or makes a racket within earshot brings it crawling after them, and when they go quiet
/// it buries itself again where it stopped. After a couple of grabs, or once hurt, it crawls off to be gone.
/// </summary>
public class AiTaskClump : AiTaskBase
{
    private enum State { Buried, Awake, Crawling, Leaving }

    private readonly float reach, damage, crawlSpeed, hearing;
    private readonly int cooldownMs, grabsBeforeLeaving;
    private readonly AssetLocation grabSound, stirSound;

    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private State state;
    private float think, quietFor;
    private long lastGrabMs, lastPathMs;
    private int grabs;
    private bool started, crawling;

    public AiTaskClump(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        reach = taskConfig["reach"].AsFloat(1.3f);
        damage = taskConfig["damage"].AsFloat(4);
        cooldownMs = taskConfig["cooldownMs"].AsInt(3500);
        grabsBeforeLeaving = taskConfig["grabsBeforeLeaving"].AsInt(2);
        crawlSpeed = taskConfig["crawlSpeed"].AsFloat(0.02f);
        hearing = taskConfig["hearing"].AsFloat(14);
        grabSound = Sound(taskConfig["grabSound"].AsString(null));
        stirSound = Sound(taskConfig["stirSound"].AsString(null));
    }

    private static AssetLocation Sound(string code) => code == null ? null : AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/");

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        return menace != null && menace.Kind is Encounter.Stalk or Encounter.Hunt or Encounter.Leave;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        if (started) return;
        started = true;
        state = State.Buried;
        entity.AnimManager.StartAnimation("dormant");
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        think -= dt;
        if (think > 0) return true;
        think = 0.2f;

        Entity target = menace.Target;
        if (menace.Kind == Encounter.Leave || target == null || !target.Alive)
        {
            if (menace.Kind != Encounter.Leave) menace.Kind = Encounter.Leave;
            if (state != State.Leaving) CrawlAway(target);
            return true;
        }

        double distance = entity.Pos.DistanceTo(target.Pos);
        double gap = distance - (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2;
        double dy = Math.Abs(target.Pos.Y - entity.Pos.Y);
        bool loud = director != null && director.AssessmentOf(target).Noise > 0.35 || target is EntityAgent agent && Senses.Running(agent);
        quietFor = loud ? 0 : quietFor + 0.2f;

        switch (state)
        {
            case State.Buried:
                if (gap < 4 && dy < 2) Wake(State.Awake);
                else if (loud && distance < hearing && !Strike.IsCreative(target)) Wake(State.Crawling);
                return true;

            case State.Crawling:
                if (gap <= reach + 0.3)
                {
                    pathTraverser.Stop();
                    Crawl(false);
                    state = State.Awake;
                }
                else if (quietFor > 6)
                {
                    Bury();
                }
                else if (!pathTraverser.Active || entity.World.ElapsedMilliseconds - lastPathMs > 1500)
                {
                    lastPathMs = entity.World.ElapsedMilliseconds;
                    Crawl(true);
                    pathTraverser.NavigateTo_Async(target.Pos.XYZ.Clone(), crawlSpeed * Danger.Speed(Danger.Of(entity)), reach * 0.8f, () => Crawl(false), () => Crawl(false), () => Crawl(false), 1500, 1);
                }
                return true;

            case State.Awake:
                if (gap <= reach && dy < 1.5 && entity.World.ElapsedMilliseconds - lastGrabMs > cooldownMs && !Strike.IsCreative(target))
                {
                    lastGrabMs = entity.World.ElapsedMilliseconds;
                    entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
                    entity.AnimManager.StartAnimation("grab");
                    if (grabSound != null) entity.World.PlaySoundAt(grabSound, entity.Pos.X, entity.Pos.Y + 0.5, entity.Pos.Z, null, true, 20);
                    double danger = Danger.Of(entity);
                    Strike.Hit(entity, target, damage * Danger.Damage(danger), EnumDamageType.PiercingAttack, 1 + Danger.TierBonus(danger), -1.2f);
                    // It feeds a moment on what it caught, the limbs folded over its mouth
                    entity.World.RegisterCallback(_ => { if (entity.Alive) entity.AnimManager.StartAnimation("feed"); }, 850);
                    entity.World.RegisterCallback(_ => { if (entity.Alive) entity.AnimManager.StopAnimation("feed"); }, 2600);
                    if (++grabs >= grabsBeforeLeaving)
                    {
                        menace.Kind = Encounter.Leave;
                        return true;
                    }
                }
                else if (gap > reach + 0.5 && loud && distance < hearing) state = State.Crawling;
                else if (gap > 5 && quietFor > 8) Bury();
                return true;
        }
        return true;
    }

    private void Wake(State next)
    {
        state = next;
        entity.AnimManager.StopAnimation("dormant");
        entity.AnimManager.StartAnimation("emerge");
        entity.AnimManager.StartAnimation("stir");
        if (stirSound != null) entity.World.PlaySoundAt(stirSound, entity.Pos.X, entity.Pos.Y + 0.5, entity.Pos.Z, null, true, 16, 0.6f);
        Strike.Log(entity, "wakes ({0})", next);
    }

    private void Bury()
    {
        pathTraverser.Stop();
        Crawl(false);
        state = State.Buried;
        entity.AnimManager.StopAnimation("emerge");
        entity.AnimManager.StartAnimation("dormant");
        Strike.Log(entity, "buries itself again");
    }

    private void Crawl(bool on)
    {
        if (on == crawling) return;
        crawling = on;
        if (on) entity.AnimManager.StartAnimation("crawl");
        else entity.AnimManager.StopAnimation("crawl");
    }

    private void CrawlAway(Entity from)
    {
        if (state == State.Buried) Wake(State.Leaving);
        state = State.Leaving;
        Vec3d away = from?.Pos.XYZ ?? entity.Pos.XYZ.Add(1, 0, 0);
        double angle = Math.Atan2(entity.Pos.Z - away.Z, entity.Pos.X - away.X);
        for (int i = 0; i < 6; i++)
        {
            double a = angle + (entity.World.Rand.NextDouble() - 0.5) * (i < 3 ? 1.2 : 3);
            int x = (int)Math.Floor(entity.Pos.X + Math.Cos(a) * 12), z = (int)Math.Floor(entity.Pos.Z + Math.Sin(a) * 12);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 1, 4);
            if (y == int.MinValue) continue;
            Crawl(true);
            pathTraverser.NavigateTo_Async(new Vec3d(x + 0.5, y, z + 0.5), crawlSpeed * 1.4f, 1, () => Crawl(false), () => Crawl(false), () => Crawl(false), 1500, 1);
            return;
        }
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        // Struck, it goes
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace != null && source.GetCauseEntity() is EntityAgent) menace.Kind = Encounter.Leave;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        pathTraverser.Stop();
        Crawl(false);
    }
}

/// <summary>
/// The Thing on Level 7: something vast in the deep water. It circles a diver far out at the edge of what they can
/// see, groaning now and then. A diver who stays below the twilight zone for too long with their mind coming apart
/// (Reality Stability under a half) is struck once, hard, from the dark, and the Thing goes back down. It cannot be
/// fought; surfacing ends it.
/// </summary>
public class AiTaskTheThing : AiTaskBase
{
    private readonly float speed, rushSpeed, orbitRadius, damage, patienceSeconds;
    private readonly AssetLocation groanSound;

    private EntityBehaviorMenace menace;
    private int floorY = int.MinValue;
    private float think, phase, deepFor, nextGroan = 8;
    private bool rushing;
    private Vec3d goal;

    public AiTaskTheThing(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        // (The same scale as vanilla's movespeed: fish swim at 0.03 to 0.06, about 1 to 2 blocks a second)
        speed = taskConfig["speed"].AsFloat(0.035f);
        rushSpeed = taskConfig["rushSpeed"].AsFloat(0.14f);
        orbitRadius = taskConfig["orbitRadius"].AsFloat(18);
        damage = taskConfig["damage"].AsFloat(8);
        patienceSeconds = taskConfig["patienceSeconds"].AsFloat(40);
        string sound = taskConfig["groanSound"].AsString(null);
        groanSound = sound == null ? null : AssetLocation.Create(sound, "backrooms").WithPathPrefixOnce("sounds/");
    }

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        return menace != null;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        if (floorY == int.MinValue) floorY = BackroomsWorld.CreateGeometry(entity.World).FloorY;
        phase = (float)Math.Atan2(entity.Pos.Z - (menace.Target?.Pos.Z ?? entity.Pos.Z), entity.Pos.X - (menace.Target?.Pos.X ?? entity.Pos.X));
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        think -= dt;
        if (think <= 0)
        {
            think = 0.25f;
            Decide();
        }
        Steer();
        return true;
    }

    private void Decide()
    {
        Entity target = menace.Target;
        if (menace.Kind == Encounter.Leave || target == null || !target.Alive || target.Pos.Y >= floorY - 1)
        {
            // Back down into the dark
            if (menace.Kind != Encounter.Leave) menace.Kind = Encounter.Leave;
            Vec3d from = target?.Pos.XYZ ?? entity.Pos.XYZ;
            double away = Math.Atan2(entity.Pos.Z - from.Z, entity.Pos.X - from.X);
            goal = entity.Pos.XYZ.Add(Math.Cos(away) * 10, -6, Math.Sin(away) * 10);
            rushing = false;
            return;
        }

        bool deep = target.Pos.Y < floorY - 20;
        deepFor = deep ? deepFor + 0.25f : 0;
        double distance = entity.Pos.DistanceTo(target.Pos);

        if (rushing)
        {
            goal = target.Pos.XYZ.Add(0, 0.5, 0);
            if (distance < 3.5 + entity.SelectionBox.XSize / 2)
            {
                Strike.Hit(entity, target, damage, EnumDamageType.BluntAttack, 3, 1.5f);
                rushing = false;
                menace.Kind = Encounter.Leave;
            }
            return;
        }

        // Round and round, far out, a little below
        phase += 0.25f * 0.09f;
        goal = target.Pos.XYZ.Add(Math.Cos(phase) * orbitRadius, -3 + 2 * Math.Sin(phase * 0.5), Math.Sin(phase) * orbitRadius);

        nextGroan -= 0.25f;
        if (nextGroan <= 0 && groanSound != null)
        {
            nextGroan = 20 + (float)entity.World.Rand.NextDouble() * 25;
            entity.World.PlaySoundAt(groanSound, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, null, 0.55f + (float)entity.World.Rand.NextDouble() * 0.15f, 64, 0.9f);
        }

        // In the abyss it may come at anyone; above that, only at a diver who stayed down too long, coming apart
        bool strike = menace.Kind == Encounter.Hunt && target.Pos.Y < floorY - 55 || deepFor > patienceSeconds && Senses.Stability(target) < 0.5;
        if (strike && !Strike.IsCreative(target))
        {
            rushing = true;
            menace.Kind = Encounter.Hunt;
            Strike.Log(entity, "rushes {0} from {1:0} blocks", target.Code, distance);
            if (groanSound != null) entity.World.PlaySoundAt(groanSound, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, null, 0.45f, 64, 1f);
        }
    }

    private void Steer()
    {
        if (goal == null) return;
        double dx = goal.X - entity.Pos.X, dy = goal.Y - entity.Pos.Y, dz = goal.Z - entity.Pos.Z;
        double length = Math.Sqrt(dx * dx + dy * dy + dz * dz);
        if (length < 1.0)
        {
            entity.Controls.FlyVector.Set(0, 0, 0);
            entity.Controls.WalkVector.Set(0, 0, 0);
            return;
        }
        float s = rushing ? rushSpeed : speed;
        entity.Controls.FlyVector.Set(dx / length * s, dy / length * s, dz / length * s);
        entity.Controls.WalkVector.Set(entity.Controls.FlyVector);
        float yaw = (float)Math.Atan2(dx, dz);
        entity.Pos.Yaw += GameMath.Clamp(GameMath.AngleRadDistance(entity.Pos.Yaw, yaw), -0.05f, 0.05f);
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        entity.Controls.FlyVector.Set(0, 0, 0);
        entity.Controls.WalkVector.Set(0, 0, 0);
    }
}
