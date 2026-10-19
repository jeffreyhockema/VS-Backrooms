using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>
/// A grown Faceling disturbed (see <see cref="EntityBehaviorFaceling"/>: a block broken, a fall, a blow struck close
/// by, by someone it can see): it turns to them, throws its arms about, steps in and shoves them once (1 damage, a
/// little knockback), then goes back to its routine. It does not hunt: only being struck does that (the kin defence).
/// A task of its own, above the greeting and the idle gestures, so nothing else walks it off mid-outburst.
/// </summary>
public class AiTaskOutburst : AiTaskBase
{
    private enum Step { Turn, Gesture, Charge, Shove, Calm }

    private readonly float damage, knockback, walkSpeed, range;
    private readonly long cooldownMs;
    private readonly string gesture;
    private Entity asked, target;
    private long askedAtMs = -1, lastMs = -1_000_000;
    private Step step;
    private float stepTime;
    private bool shoved, charging;
    private string playing;

    /// <summary>When any Faceling last shoved someone (the shove's own noise must not set the neighbours off).</summary>
    public static long LastShoveMs = -1_000_000;

    public AiTaskOutburst(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        damage = taskConfig["damage"].AsFloat(1);
        knockback = taskConfig["knockback"].AsFloat(0.35f);
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.02f);
        range = taskConfig["range"].AsFloat(6);
        cooldownMs = (long)(taskConfig["cooldownSeconds"].AsFloat(30) * 1000);
        gesture = taskConfig["gesture"].AsString("stretch");
    }

    /// <summary>Whether it may be set off now (not within its cooldown or already at it).</summary>
    public bool Ready(long now) => now - lastMs >= cooldownMs && askedAtMs < 0 && !Active;

    public bool Active { get; private set; }

    public float Range => range;

    /// <summary>Asks it to have an outburst at someone; it does on its next tick if nothing more pressing is going on.</summary>
    public void Ask(Entity at)
    {
        asked = at;
        askedAtMs = entity.World.ElapsedMilliseconds;
        lastMs = askedAtMs;
    }

    public override bool ShouldExecute()
    {
        if (askedAtMs < 0) return false;
        if (entity.World.ElapsedMilliseconds - askedAtMs > 1500 || !entity.Alive)
        {
            askedAtMs = -1;
            return false;
        }
        var menace = entity.GetBehavior<EntityBehaviorMenace>();
        return menace == null || menace.Kind == Encounter.Ambient;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        Active = true;
        target = asked;
        asked = null;
        askedAtMs = -1;
        shoved = charging = false;
        pathTraverser.Stop();
        entity.Controls.StopAllMovement();
        Strike.Log(entity, "outburst at {0}", target?.Code.Path);
        Go(Step.Turn);
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || target == null || !target.Alive) return false;
        var menace = entity.GetBehavior<EntityBehaviorMenace>();
        if (menace != null && menace.Kind != Encounter.Ambient) return false; // struck: the kin defence has it now
        stepTime += dt;
        double distance = entity.Pos.DistanceTo(target.Pos);
        switch (step)
        {
            case Step.Turn:
                if (Turn(YawTo(target.Pos.XYZ), 6f, dt) > 0.15f && stepTime < 1f) return true;
                Play(gesture);
                Go(Step.Gesture);
                return true;
            case Step.Gesture:
                Turn(YawTo(target.Pos.XYZ), 3f, dt);
                if (stepTime < 2.2f) return true;
                Stop();
                Go(Step.Charge);
                return true;
            case Step.Charge:
                if (distance > range + 4) return false; // they are gone
                Turn(YawTo(target.Pos.XYZ), 5f, dt);
                if (distance <= 1.5 || stepTime > 3f)
                {
                    pathTraverser.Stop();
                    Play("attack");
                    Go(Step.Shove);
                    return true;
                }
                if (!charging)
                {
                    charging = true;
                    Play("walk");
                    pathTraverser.NavigateTo_Async(target.Pos.XYZ.Clone(), walkSpeed, 1.2f, () => { }, () => { }, () => { }, 1500, 1);
                }
                return true;
            case Step.Shove:
                Turn(YawTo(target.Pos.XYZ), 6f, dt);
                if (!shoved && stepTime > 0.3f)
                {
                    shoved = true;
                    if (distance <= 2.2 && !Strike.IsCreative(target))
                    {
                        LastShoveMs = entity.World.ElapsedMilliseconds;
                        Strike.Hit(entity, target, damage, EnumDamageType.BluntAttack, 0, knockback);
                    }
                    else Strike.Log(entity, "outburst: shove missed, {0:0.0} blocks off", distance);
                }
                if (stepTime < 0.9f) return true;
                Stop();
                Go(Step.Calm);
                return true;
            case Step.Calm:
                return stepTime < 0.8f;
        }
        return false;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        pathTraverser.Stop();
        Stop();
        Active = false;
        target = null;
    }

    private void Go(Step next)
    {
        step = next;
        stepTime = 0;
    }

    private void Play(string code)
    {
        Stop();
        playing = code;
        entity.AnimManager.StartAnimation(code);
    }

    private void Stop()
    {
        if (playing != null) entity.AnimManager.StopAnimation(playing);
        playing = null;
    }

    private float YawTo(Vec3d point) => (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);

    private float Turn(float desired, float ratePerSecond, float dt)
    {
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float by = GameMath.Clamp(delta, -ratePerSecond * dt, ratePerSecond * dt);
        entity.Pos.Yaw = GameMath.Mod(entity.Pos.Yaw + by, GameMath.TWOPI);
        return Math.Abs(delta - by);
    }
}

/// <summary>
/// A Faceling child calmed with food (see <see cref="EntityBehaviorFaceling"/>): it follows that player, keeping two to
/// four blocks off, until the minute is up (the Level 6.1 log). Only while it is going about its own business.
/// </summary>
public class AiTaskCompanion : AiTaskBase
{
    private readonly float walkSpeed, runSpeed, minDistance, maxDistance;
    private long nextLookMs;
    private float think;
    private string anim;

    public AiTaskCompanion(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.016f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.04f);
        minDistance = taskConfig["minDistance"].AsFloat(2);
        maxDistance = taskConfig["maxDistance"].AsFloat(4);
    }

    private Entity Leader()
    {
        long id = entity.Attributes.GetLong(EntityBehaviorFaceling.FollowKey, -1);
        if (id < 0 || entity.World.ElapsedMilliseconds >= entity.Attributes.GetLong(EntityBehaviorFaceling.FollowUntilKey, 0)) return null;
        Entity who = entity.World.GetEntityById(id);
        return who != null && who.Alive ? who : null;
    }

    public override bool ShouldExecute()
    {
        long now = entity.World.ElapsedMilliseconds;
        if (now < nextLookMs) return false;
        nextLookMs = now + 500;
        var menace = entity.GetBehavior<EntityBehaviorMenace>();
        return (menace == null || menace.Kind == Encounter.Ambient) && Leader() != null;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        think = 0;
    }

    public override bool ContinueExecute(float dt)
    {
        Entity leader = Leader();
        var menace = entity.GetBehavior<EntityBehaviorMenace>();
        if (!entity.Alive || leader == null || menace != null && menace.Kind != Encounter.Ambient) return false;
        think -= dt;
        if (think > 0) return true;
        think = 0.4f;
        double distance = entity.Pos.DistanceTo(leader.Pos);
        if (distance > 40) return false;
        if (distance > maxDistance)
        {
            if (!pathTraverser.Active)
            {
                bool far = distance > maxDistance + 6;
                SetAnim(far ? "run" : "walk");
                pathTraverser.NavigateTo_Async(leader.Pos.XYZ.Clone(), far ? runSpeed : walkSpeed, (minDistance + maxDistance) / 2, () => SetAnim(null), () => SetAnim(null), () => SetAnim(null), 1500, 1);
            }
        }
        else
        {
            if (distance < minDistance) pathTraverser.Stop();
            if (!pathTraverser.Active)
            {
                SetAnim(null);
                float desired = (float)Math.Atan2(leader.Pos.X - entity.Pos.X, leader.Pos.Z - entity.Pos.Z);
                entity.Pos.Yaw = GameMath.Mod(entity.Pos.Yaw + GameMath.Clamp(GameMath.AngleRadDistance(entity.Pos.Yaw, desired), -0.9f, 0.9f), GameMath.TWOPI);
            }
        }
        return true;
    }

    private void SetAnim(string code)
    {
        if (anim == code) return;
        if (anim != null) entity.AnimManager.StopAnimation(anim);
        anim = code;
        if (anim != null) entity.AnimManager.StartAnimation(anim);
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        pathTraverser.Stop();
        SetAnim(null);
    }
}
