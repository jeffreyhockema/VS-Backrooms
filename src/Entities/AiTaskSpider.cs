using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// A Giant Spider (Level 8): one of the level's spiders bred to "extreme gigantism", a nest's queen in the old Fandom
/// telling. It is not slowed by cobwebs (its own or any other), and climbs the walls as the game's locusts do.
/// </summary>
public class EntityGiantSpider : EntityAgent
{
    public override double GetWalkSpeedMultiplier(double groundDragFactor = 0.3)
    {
        double multiplier = base.GetWalkSpeedMultiplier(groundDragFactor);
        // (As the base counts it: the block the feet are in only when they are not resting on the one below's top)
        int below = (int)(Pos.InternalY - 0.05), inside = (int)(Pos.InternalY + 0.01);
        if (below != inside && IsWeb(insideBlock) && insideBlock.WalkSpeedMultiplier > 0) multiplier /= insideBlock.WalkSpeedMultiplier;
        Block under = World.BlockAccessor.GetBlockRaw((int)Pos.X, below, (int)Pos.Z);
        if (IsWeb(under) && under.WalkSpeedMultiplier > 0) multiplier /= under.WalkSpeedMultiplier;
        return multiplier;
    }

    private static bool IsWeb(Block block) => block?.Code != null && block.Code.Domain == "game" && block.Code.Path.StartsWith("spiderweb");
}

/// <summary>
/// The Giant Spider's hunt, after the lore: "aggressively territorial", they "will not hesitate to give chase to hapless
/// victims who disturb their habitats" (Wikidot, Level 8); "loud sounds reverberate throughout the caverns, attracting
/// large numbers of spiders to the source" (the old Fandom page); "many species are HIGHLY venomous"; and "Spiders
/// can't swim!" (Tip #7: make for the nearest water).
///
/// It lies in wait where it was put down (its home), low on its legs in the dark, eyes shining, clicking now and then.
/// Whoever comes within a few blocks of it (fewer for someone creeping), runs or makes a racket within earshot, or
/// strikes it, wakes it: it rears with its forelegs up and hisses, then gives chase, faster than a sprint. Its bite is
/// wound up like every other blow and can be dodged; it lands hard, and the venom burns on for some seconds after. It
/// chases only so far from home, never into water nor up to a fire, and not for ever: someone who gets clear of its
/// ground, wades in, stands by a fire or keeps out of reach for long enough is let go, and it goes back home and lies in
/// wait again, mending slowly while it waits. Badly hurt, it flees.
/// </summary>
public class AiTaskSpider : AiTaskBase
{
    private enum State { Lurk, Rear, Chase, Return, Flee }

    /// <summary>What it notices by (see <see cref="SenseProfile"/>): <c>touch</c> is the trespass it will not stand, <c>hearing</c> how far it hears a racket, <c>sneakFactor</c> how much creeping shrinks both.</summary>
    private readonly SenseProfile senses;
    private readonly float walkSpeed, runSpeed, trespass, hearing, leash, attackRange, damage, knockback, venom, retreatBelow, mendPerSecond;
    private readonly int damageTier, attackDurationMs, damageAtMs, attackCooldownMs, rearMs, venomTicks, venomEveryMs;
    private readonly AssetLocation chitterSound, hissSound, biteSound;

    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private State state;
    private Vec3d home;
    private float think, nextChitter = 4;
    private long stateSinceMs, attackStartMs = -1, lastAttackMs, lastBloodMs, lastPathMs, calmUntilMs, inWaterSinceMs = -1;
    private bool damageDone, started, moving, running;
    private double speedMul = 1, damageMul = 1, cooldownMul = 1, patienceMs = 20_000;
    private int tierBonus;
    private int venomLeft, thoughts, noPaths;
    private long straightUntilMs;
    private float reach;
    private Vec3d chasing;
    private Entity venomTarget;

    public AiTaskSpider(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.016f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.05f);
        senses = SenseProfile.Parse(taskConfig["senses"]) ?? new SenseProfile { Touch = 5.5f, Hearing = 20, SneakFactor = 0.55f };
        trespass = senses.Touch;
        hearing = senses.Hearing;
        leash = taskConfig["leash"].AsFloat(24);
        attackRange = taskConfig["attackRange"].AsFloat(1.1f);
        damage = taskConfig["damage"].AsFloat(3.5f);
        knockback = taskConfig["knockback"].AsFloat(0.4f);
        damageTier = taskConfig["damageTier"].AsInt(2);
        attackDurationMs = taskConfig["attackDurationMs"].AsInt(900);
        damageAtMs = taskConfig["damageAtMs"].AsInt(450);
        attackCooldownMs = taskConfig["attackCooldownMs"].AsInt(1500);
        rearMs = taskConfig["rearMs"].AsInt(900);
        venom = taskConfig["venom"].AsFloat(0.5f);
        venomTicks = taskConfig["venomTicks"].AsInt(5);
        venomEveryMs = taskConfig["venomEveryMs"].AsInt(1200);
        retreatBelow = taskConfig["retreatBelow"].AsFloat(0.25f);
        mendPerSecond = taskConfig["mendPerSecond"].AsFloat(0.25f);
        chitterSound = Sound(taskConfig["chitterSound"].AsString(null));
        hissSound = Sound(taskConfig["hissSound"].AsString(null));
        biteSound = Sound(taskConfig["biteSound"].AsString(null));
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
        home = entity.Pos.XYZ;
        double d = Danger.Of(entity);
        speedMul = Danger.Speed(d);
        damageMul = Danger.Damage(d);
        cooldownMul = Danger.Cooldown(d);
        tierBonus = Danger.TierBonus(d);
        patienceMs = (20 + 15 * d) * 1000;
        // Put down to hunt, it comes out of the dark at once, and its ground reaches past where its prey stands
        Entity target = menace.Target;
        reach = target == null || menace.Kind != Encounter.Hunt ? leash : Math.Max(leash, (float)Math.Sqrt(target.Pos.XYZ.HorizontalSquareDistanceTo(home.X, home.Z)) + 12);
        if (menace.Kind == Encounter.Hunt) Rear();
        else Lurk();
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        Entity target = menace.Target;
        long now = entity.World.ElapsedMilliseconds;

        if (attackStartMs >= 0)
        {
            ContinueAttack(target, now);
            return true;
        }
        if (target != null && state is State.Lurk or State.Rear) TurnTowards(target.Pos.XYZ, dt, state == State.Rear ? 5f : 0.8f);

        think -= dt;
        if (think > 0) return true;
        think = 0.25f;

        if (menace.Kind == Encounter.Leave || target == null || !target.Alive)
        {
            if (state != State.Flee) Flee(target);
            return true;
        }
        if (state != State.Flee && HealthFraction() < retreatBelow)
        {
            menace.Kind = Encounter.Leave;
            Flee(target);
            return true;
        }

        double distance = entity.Pos.DistanceTo(target.Pos);
        double gap = distance - (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2;
        double dy = Math.Abs(target.Pos.Y - entity.Pos.Y);
        bool creative = Strike.IsCreative(target);

        switch (state)
        {
            case State.Lurk:
                Mend(0.25f);
                if (distance < hearing) Chitter(0.25f, 0.55f);
                if (creative) return true;
                if (now < calmUntilMs && gap > 2.5) return true;
                bool sneaking = target is EntityAgent sneaker && sneaker.ServerControls.Sneak;
                bool near = gap < (sneaking ? trespass * senses.SneakFactor : trespass) && dy < 4;
                bool loud = distance < hearing && (director != null && director.AssessmentOf(target).Noise > 0.35 || target is EntityAgent runner && Senses.Running(runner));
                if (near || loud || menace.Kind == Encounter.Hunt)
                {
                    Strike.Log(entity, "wakes ({0})", near ? "trespass" : loud ? "noise" : "hunt");
                    Rear();
                }
                return true;

            case State.Rear:
                if (now - stateSinceMs >= rearMs) SetState(State.Chase);
                return true;

            case State.Chase:
                Chase(target, now, distance, gap, dy);
                return true;

            case State.Return:
                Mend(0.25f);
                if (entity.Pos.XYZ.HorizontalSquareDistanceTo(home.X, home.Z) < 2.5 * 2.5 || now - stateSinceMs > 25_000)
                {
                    Lurk();
                    return true;
                }
                if (!pathTraverser.Active && now - lastPathMs > 1500) Go(home, walkSpeed, 1.2f);
                if (!creative && menace.Kind == Encounter.Hunt)
                {
                    // (Roused by a noise at its nest, WakeFor)
                    Strike.Log(entity, "wakes (a racket at the nest)");
                    Rear();
                    return true;
                }
                // Back on its ground, someone still trespassing or running wakes it again
                if (!creative && now >= calmUntilMs && (gap < trespass * 0.6 || distance < hearing * 0.5 && target is EntityAgent r && Senses.Running(r)) && GivesChaseTo(target)) Rear();
                return true;
        }
        return true;
    }

    // ================= Lying in wait =================

    /// <summary>
    /// A racket at its nest (MenaceSystem.NestHeard): it wakes and goes after whoever made it, unless it is already
    /// at someone's throat, running off or hurt too badly. Returns whether it took it up.
    /// </summary>
    public bool WakeFor(Entity who)
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null || !entity.Alive || menace.Kind == Encounter.Leave || state == State.Flee) return false;
        if (state is State.Chase or State.Rear && menace.Target is { Alive: true }) return false;
        menace.Target = who;
        menace.Kind = Encounter.Hunt;
        calmUntilMs = 0;
        // (Its ground reaches past where its prey stands, as for a hunt it was put down for)
        if (home != null) reach = Math.Max(reach, (float)Math.Sqrt(who.Pos.XYZ.HorizontalSquareDistanceTo(home.X, home.Z)) + 12);
        return true;
    }

    private void Lurk()
    {
        Stop();
        SetState(State.Lurk);
        entity.AnimManager.StopAnimation("rear");
        entity.AnimManager.StartAnimation("lurk");
        if (menace.Kind == Encounter.Hunt) menace.Kind = Encounter.Stalk;
    }

    /// <summary>The clicking of its mouthparts, now and then: what gives it away in the dark.</summary>
    private void Chitter(float dt, float pitch)
    {
        nextChitter -= dt;
        if (nextChitter > 0 || chitterSound == null) return;
        nextChitter = 6 + (float)entity.World.Rand.NextDouble() * 9;
        entity.World.PlaySoundAt(chitterSound, entity.Pos.X, entity.Pos.Y + 0.5, entity.Pos.Z, null, pitch + (float)entity.World.Rand.NextDouble() * 0.3f, 22, 0.8f);
    }

    /// <summary>Lore: "accelerated regeneration". It mends a little while it waits, never while it hunts.</summary>
    private void Mend(float dt)
    {
        if (entity.GetBehavior<EntityBehaviorHealth>() is not { } health || health.Health >= health.MaxHealth) return;
        health.Health = Math.Min(health.MaxHealth, health.Health + mendPerSecond * dt);
    }

    // ================= The chase =================

    private void Rear()
    {
        Stop();
        SetState(State.Rear);
        entity.AnimManager.StopAnimation("lurk");
        entity.AnimManager.StartAnimation("rear");
        if (hissSound != null) entity.World.PlaySoundAt(hissSound, entity.Pos.X, entity.Pos.Y + 0.6, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, 28, 1f);
        menace.Kind = Encounter.Hunt;
        lastBloodMs = entity.World.ElapsedMilliseconds;
        inWaterSinceMs = -1;
    }

    private void Chase(Entity target, long now, double distance, double gap, double dy)
    {
        entity.AnimManager.StopAnimation("rear");
        // Too far from its ground, in the water, by a fire, safe on the road, or long out of reach: it lets them go
        string why = null;
        double fromHome = target.Pos.XYZ.HorizontalSquareDistanceTo(home.X, home.Z);
        if (fromHome > reach * reach) why = "out of its ground";
        else if (!GivesChaseTo(target)) why = "warded or safe";
        else if (now - lastBloodMs > patienceMs) why = "out of reach too long";
        else if (InWater(target))
        {
            if (inWaterSinceMs < 0)
            {
                inWaterSinceMs = now;
                // It stops at the water's edge and rears at them
                Stop();
                entity.AnimManager.StartAnimation("rear");
                if (hissSound != null) entity.World.PlaySoundAt(hissSound, entity.Pos.X, entity.Pos.Y + 0.6, entity.Pos.Z, null, 0.8f, 24, 1f);
            }
            if (now - inWaterSinceMs > 4000) why = "in the water";
            else return;
        }
        else inWaterSinceMs = -1;
        if (why != null)
        {
            Strike.Log(entity, "lets {0} go: {1}", target.Code.Path, why);
            GoHome(now);
            return;
        }

        // Never into the water itself
        if (entity.FeetInLiquid)
        {
            GoHome(now);
            return;
        }

        if (gap <= attackRange && dy < 1.6 && now - lastAttackMs > attackCooldownMs * cooldownMul)
        {
            StartAttack(target, now);
            return;
        }
        // Close enough: wait out the cooldown face to face
        if (gap <= attackRange)
        {
            Stop();
            return;
        }
        // A new path when there is none or the prey has moved on; otherwise the old one is steered at it. Where no path
        // is found (a gap in the rock, a ledge), it goes straight at them, climbing whatever is in the way
        float within = attackRange * 0.6f + (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2;
        bool moved = chasing == null || chasing.SquareDistanceTo(target.Pos.X, target.Pos.Y, target.Pos.Z) >= 9;
        if (now < straightUntilMs)
        {
            if (!pathTraverser.Active || now - lastPathMs > 750)
            {
                lastPathMs = now;
                SetMoving(true, true);
                pathTraverser.WalkTowards(target.Pos.XYZ.Clone(), runSpeed * (float)speedMul, within, OnArrived, OnArrived);
            }
        }
        else if (!pathTraverser.Active || moved && now - lastPathMs > 750)
        {
            chasing = target.Pos.XYZ;
            Go(chasing, runSpeed, within, sync: true);
        }
        else
        {
            pathTraverser.CurrentTarget.X = target.Pos.X;
            pathTraverser.CurrentTarget.Y = target.Pos.Y;
            pathTraverser.CurrentTarget.Z = target.Pos.Z;
        }
        if (++thoughts % 12 == 0) Strike.Log(entity, "chasing {0}: {1:0.0} blocks (gap {2:0.0}, dy {3:0.0}){4}", target.Code.Path, distance, gap, dy, pathTraverser.Active ? ", on a path" : "");
    }

    /// <summary>Whether it will close on someone there: not within reach of a fire's ward, nor where nothing hostile goes.</summary>
    private bool GivesChaseTo(Entity target)
    {
        if (Wards.Warded(entity.World, target.Pos.XYZ, Wards.Radius + 1)) return false;
        return director == null || director.AssessmentOf(target).Band != MenaceBand.Safe;
    }

    private static bool InWater(Entity target) => target is EntityAgent agent && (agent.FeetInLiquid || agent.Swimming);

    private void GoHome(long now)
    {
        Stop();
        entity.AnimManager.StopAnimation("rear");
        SetState(State.Return);
        calmUntilMs = now + 30_000;
        menace.Kind = Encounter.Stalk;
        Go(home, walkSpeed, 1.2f);
    }

    private void StartAttack(Entity target, long now)
    {
        Stop();
        attackStartMs = now;
        damageDone = false;
        entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
        entity.AnimManager.StartAnimation("attack");
    }

    private void ContinueAttack(Entity target, long now)
    {
        long elapsed = now - attackStartMs;
        if (target != null) TurnTowards(target.Pos.XYZ, 0.05f, 5f);
        if (!damageDone && elapsed >= damageAtMs)
        {
            damageDone = true;
            double gap = target == null ? 99 : entity.Pos.DistanceTo(target.Pos) - (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2;
            // (Out of reach by more than a little when the fangs come down, and it misses, as every blow)
            if (target != null && target.Alive && gap <= attackRange + 0.4 && !Strike.IsCreative(target))
            {
                if (biteSound != null) entity.World.PlaySoundAt(biteSound, entity.Pos.X, entity.Pos.Y + 0.5, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, 18, 1f);
                Strike.Hit(entity, target, damage * (float)damageMul, EnumDamageType.PiercingAttack, damageTier + tierBonus, knockback);
                lastBloodMs = now;
                Envenom(target);
            }
        }
        if (elapsed >= attackDurationMs)
        {
            entity.AnimManager.StopAnimation("attack");
            attackStartMs = -1;
            lastAttackMs = now;
        }
    }

    /// <summary>The venom burns on after the bite, a little at a time. Another bite starts it over; it does not add up.</summary>
    private void Envenom(Entity target)
    {
        if (venom <= 0 || venomTicks <= 0) return;
        bool running = venomLeft > 0 && venomTarget == target;
        venomTarget = target;
        venomLeft = venomTicks;
        if (!running) entity.World.RegisterCallback(_ => VenomTick(), venomEveryMs);
    }

    private void VenomTick()
    {
        Entity target = venomTarget;
        if (venomLeft <= 0 || target == null || !target.Alive)
        {
            venomLeft = 0;
            return;
        }
        venomLeft--;
        Strike.Hit(entity, target, venom * (float)damageMul, EnumDamageType.Poison, 0, 0);
        if (venomLeft > 0) entity.World.RegisterCallback(_ => VenomTick(), venomEveryMs);
    }

    // ================= Going =================

    private void Flee(Entity from)
    {
        SetState(State.Flee);
        entity.AnimManager.StopAnimation("lurk");
        entity.AnimManager.StopAnimation("rear");
        Vec3d away = from?.Pos.XYZ ?? entity.Pos.XYZ.Add(1, 0, 0);
        double angle = Math.Atan2(entity.Pos.Z - away.Z, entity.Pos.X - away.X);
        for (int i = 0; i < 8; i++)
        {
            double a = angle + (entity.World.Rand.NextDouble() - 0.5) * (i < 4 ? 1.2 : 3);
            int x = (int)Math.Floor(entity.Pos.X + Math.Cos(a) * 16), z = (int)Math.Floor(entity.Pos.Z + Math.Sin(a) * 16);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 1, 6);
            if (y == int.MinValue) continue;
            Go(new Vec3d(x + 0.5, y, z + 0.5), runSpeed, 1);
            return;
        }
    }

    private void Go(Vec3d to, float speed, float within, bool sync = false)
    {
        lastPathMs = entity.World.ElapsedMilliseconds;
        SetMoving(true, speed >= runSpeed * 0.75f);
        // (The traverser keeps the point it is given and steers it; it must not be one this task goes on changing)
        to = to.Clone();
        if (sync)
        {
            // A search still pending would be taken for this one's answer
            pathTraverser.Stop();
            pathTraverser.NavigateTo(to, speed * (float)speedMul, within, OnArrived, OnArrived, OnNoPath, false, 2000, 1);
        }
        else pathTraverser.NavigateTo_Async(to, speed * (float)speedMul, within, OnArrived, OnArrived, OnNoPath, 1800, 1);
    }

    private void OnArrived() => SetMoving(false, false);

    private void OnNoPath()
    {
        SetMoving(false, false);
        if (state == State.Chase) straightUntilMs = entity.World.ElapsedMilliseconds + 3000;
        if (++noPaths % 8 == 1) Strike.Log(entity, "finds no path ({0} so far)", noPaths);
    }

    private void Stop()
    {
        pathTraverser.Stop();
        SetMoving(false, false);
    }

    private void SetMoving(bool on, bool run)
    {
        if (on == moving && run == running) return;
        if (moving) entity.AnimManager.StopAnimation(running ? "run" : "walk");
        moving = on;
        running = on && run;
        if (moving) entity.AnimManager.StartAnimation(running ? "run" : "walk");
    }

    private void SetState(State next)
    {
        state = next;
        stateSinceMs = entity.World.ElapsedMilliseconds;
    }

    private void TurnTowards(Vec3d point, float dt, float rate)
    {
        float desired = (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float step = rate * dt;
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -step, step)) % GameMath.TWOPI;
    }

    private float HealthFraction()
    {
        var health = entity.GetBehavior<EntityBehaviorHealth>();
        return health == null || health.MaxHealth <= 0 ? 1 : health.Health / health.MaxHealth;
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null || !entity.Alive || source.GetCauseEntity() is not EntityAgent cause) return;
        // Struck, it turns on whoever struck it (unless it is already going)
        if (state is State.Lurk or State.Return && menace.Kind != Encounter.Leave)
        {
            if (cause is EntityPlayer) menace.Target = cause;
            calmUntilMs = 0;
            Rear();
        }
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
        entity.AnimManager.StopAnimation("attack");
    }
}
