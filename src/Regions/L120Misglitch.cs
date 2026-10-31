using System;
using System.Linq;
using Backrooms.Entities;
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
/// A Misglitch (Level 120, Wikidot): "glitched, zombie-like versions of those who die in the Backrooms"; "anyone who dies
/// here instantly becomes a Misglitch". A black figure surrounded by pixels, red marks where its victim was hurt (all black
/// if the death was from within), a pointed tentacle of an arm that slices.
///
/// Put down where a player died in the level (<see cref="L120System"/>), it stays by the place, standing slumped and
/// crackling with static every few seconds (the warning: it cannot be seen in the dark). Whoever comes within a few blocks
/// of it (fewer, creeping), runs within earshot, or carries a light where it can see it, wakes it: it jerks upright,
/// shrieks and comes, a little slower than a sprint, but now and then it skips a couple of blocks forward in a blink of
/// static. Its arm reaches far (about two and a half blocks). It does not chase far from where it stood up, nor for ever;
/// it goes back and waits again. It lasts a day (in-game), then comes apart; or until it is killed. It never leaves Level
/// 120 and is never the director's.
/// </summary>
public class AiTaskMisglitch : AiTaskBase
{
    public const string HomeKey = "backrooms:l120Home", UntilKey = "backrooms:l120Until";

    private enum State { Lurk, Wake, Chase, Return }

    private readonly float walkSpeed, runSpeed, touch, sneakTouch, hearing, lightSight, leash, attackRange, damage, knockback, skipDistance;
    private readonly int damageTier, attackDurationMs, damageAtMs, attackCooldownMs, skipEveryMs, patienceMs;
    private readonly double lifeHours;
    private readonly AssetLocation[] staticSounds;
    private readonly AssetLocation huntSound, sliceSound, skipSound;

    private State state;
    private Vec3d home;
    private Entity target;
    private float think, nextStatic = 2;
    private long stateSinceMs, attackStartMs = -1, lastAttackMs, lastPathMs, lastSkipMs, lastBloodMs, straightUntilMs;
    private bool damageDone, started, moving, running;
    private double speedMul = 1, damageMul = 1, cooldownMul = 1;
    private int tierBonus;
    private Vec3d chasing;

    public AiTaskMisglitch(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.016f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.043f);
        touch = taskConfig["touch"].AsFloat(6);
        sneakTouch = taskConfig["sneakTouch"].AsFloat(3.5f);
        hearing = taskConfig["hearing"].AsFloat(18);
        lightSight = taskConfig["lightSight"].AsFloat(16);
        leash = taskConfig["leash"].AsFloat(32);
        attackRange = taskConfig["attackRange"].AsFloat(2.4f);
        damage = taskConfig["damage"].AsFloat(5);
        damageTier = taskConfig["damageTier"].AsInt(2);
        knockback = taskConfig["knockback"].AsFloat(0.35f);
        attackDurationMs = taskConfig["attackDurationMs"].AsInt(1000);
        damageAtMs = taskConfig["damageAtMs"].AsInt(430);
        attackCooldownMs = taskConfig["attackCooldownMs"].AsInt(1700);
        skipEveryMs = taskConfig["skipEveryMs"].AsInt(4500);
        skipDistance = taskConfig["skipDistance"].AsFloat(2.2f);
        patienceMs = taskConfig["patienceMs"].AsInt(25000);
        lifeHours = taskConfig["lifeHours"].AsDouble(24);
        staticSounds = (taskConfig["staticSounds"].AsArray<string>() ?? Array.Empty<string>()).Select(Sound).Where(s => s != null).ToArray();
        huntSound = Sound(taskConfig["huntSound"].AsString(null));
        sliceSound = Sound(taskConfig["sliceSound"].AsString(null));
        skipSound = Sound(taskConfig["skipSound"].AsString(null));
    }

    private static AssetLocation Sound(string code) => code == null ? null : AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/");

    public override bool ShouldExecute() => entity.Alive;

    public override void StartExecute()
    {
        base.StartExecute();
        if (started) return;
        started = true;
        ITreeAttribute attrs = entity.WatchedAttributes;
        if (attrs.HasAttribute(HomeKey + "X")) home = new Vec3d(attrs.GetDouble(HomeKey + "X"), attrs.GetDouble(HomeKey + "Y"), attrs.GetDouble(HomeKey + "Z"));
        else
        {
            home = entity.Pos.XYZ;
            attrs.SetDouble(HomeKey + "X", home.X);
            attrs.SetDouble(HomeKey + "Y", home.Y);
            attrs.SetDouble(HomeKey + "Z", home.Z);
        }
        if (!attrs.HasAttribute(UntilKey)) attrs.SetDouble(UntilKey, entity.World.Calendar.TotalHours + lifeHours);
        double d = Danger.Of(entity);
        speedMul = Danger.Speed(d);
        damageMul = Danger.Damage(d);
        cooldownMul = Danger.Cooldown(d);
        tierBonus = Danger.TierBonus(d);
        Lurk();
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        long now = entity.World.ElapsedMilliseconds;
        if (attackStartMs >= 0)
        {
            ContinueAttack(now);
            return true;
        }
        if (target != null && state is State.Lurk or State.Wake) TurnTowards(target.Pos.XYZ, dt, state == State.Wake ? 6f : 0.6f);

        think -= dt;
        if (think > 0) return true;
        think = 0.25f;

        // A day, then it comes apart
        if (entity.World.Calendar.TotalHours > entity.WatchedAttributes.GetDouble(UntilKey, double.MaxValue))
        {
            Strike.Log(entity, "comes apart (its day is up)");
            if (staticSounds.Length > 0) entity.World.PlaySoundAt(staticSounds[0], entity, null, true, 20, 1f);
            entity.Die(EnumDespawnReason.Expire);
            return false;
        }
        Crackle(0.25f);

        switch (state)
        {
            case State.Lurk:
                if (Notice() is { } who)
                {
                    target = who;
                    Wake();
                }
                return true;

            case State.Wake:
                if (now - stateSinceMs >= 700) SetState(State.Chase);
                return true;

            case State.Chase:
                Chase(now);
                return true;

            case State.Return:
                if (Notice() is { } next)
                {
                    target = next;
                    Wake();
                    return true;
                }
                if (entity.Pos.XYZ.HorizontalSquareDistanceTo(home.X, home.Z) < 2 * 2 || now - stateSinceMs > 30_000)
                {
                    Lurk();
                    return true;
                }
                if (!pathTraverser.Active && now - lastPathMs > 1500) Go(home, walkSpeed, 1f);
                return true;
        }
        return true;
    }

    // ================= Noticing =================

    /// <summary>
    /// Whoever it notices now, the nearest first: anyone within reach of it (less for someone creeping), anyone running
    /// within earshot, anyone carrying a light it can see. Never someone in creative or spectator mode; straw dummies count.
    /// </summary>
    private Entity Notice()
    {
        float range = Math.Max(hearing, lightSight);
        Entity best = null;
        double bestDistance = double.MaxValue;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, range, 6, e => e.Alive && (e is EntityPlayer || Senses.IsTestTarget(e))))
        {
            if (Strike.IsCreative(e)) continue;
            double distance = e.Pos.DistanceTo(entity.Pos);
            double gap = distance - (entity.SelectionBox.XSize + e.SelectionBox.XSize) / 2;
            bool near = gap < (Senses.Sneaking(e) ? sneakTouch : touch) && Math.Abs(e.Pos.Y - entity.Pos.Y) < 4;
            bool heard = distance < hearing && Senses.Running(e);
            bool lit = distance < lightSight && Senses.HeldLight(e) >= 7 && Senses.ClearLine(entity.World, Senses.Eyes(entity), Senses.Centre(e));
            if (!(near || heard || lit) || distance >= bestDistance) continue;
            best = e;
            bestDistance = distance;
        }
        return best;
    }

    /// <summary>The static it gives off: every few seconds while it waits, more often while it hunts; what gives it away in the dark.</summary>
    private void Crackle(float dt)
    {
        nextStatic -= dt;
        if (nextStatic > 0 || staticSounds.Length == 0) return;
        var rand = entity.World.Rand;
        nextStatic = state == State.Chase ? 1.8f + (float)rand.NextDouble() * 2.5f : 4 + (float)rand.NextDouble() * 6;
        entity.World.PlaySoundAt(staticSounds[rand.Next(staticSounds.Length)], entity.Pos.X, entity.Pos.Y + 1.2, entity.Pos.Z, null,
            0.85f + (float)rand.NextDouble() * 0.3f, 20, 0.8f);
    }

    // ================= Waiting, waking, going home =================

    private void Lurk()
    {
        Stop();
        SetState(State.Lurk);
        target = null;
        entity.AnimManager.StartAnimation("lurk");
    }

    private void Wake()
    {
        Stop();
        SetState(State.Wake);
        lastBloodMs = entity.World.ElapsedMilliseconds;
        entity.AnimManager.StopAnimation("lurk");
        entity.AnimManager.StartAnimation("glitch");
        if (huntSound != null) entity.World.PlaySoundAt(huntSound, entity.Pos.X, entity.Pos.Y + 1.4, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, 28, 1f);
        Strike.Log(entity, "wakes for {0}", target?.Code.Path ?? "nobody");
    }

    private void GoHome(long now, string why)
    {
        Strike.Log(entity, "lets {0} go: {1}", target?.Code.Path ?? "nobody", why);
        Stop();
        SetState(State.Return);
        target = null;
        Go(home, walkSpeed, 1f);
    }

    // ================= The chase =================

    private void Chase(long now)
    {
        if (target == null || !target.Alive || Strike.IsCreative(target)) { GoHome(now, "gone"); return; }
        double fromHome = target.Pos.XYZ.HorizontalSquareDistanceTo(home.X, home.Z);
        if (fromHome > leash * leash) { GoHome(now, "too far from its place"); return; }
        if (now - lastBloodMs > patienceMs) { GoHome(now, "out of reach too long"); return; }
        if (Wards.Warded(entity.World, target.Pos.XYZ, Wards.Radius + 1)) { GoHome(now, "by a fire"); return; }

        double distance = entity.Pos.DistanceTo(target.Pos);
        double gap = distance - (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2;
        double dy = Math.Abs(target.Pos.Y - entity.Pos.Y);
        if (gap <= attackRange && dy < 1.8 && now - lastAttackMs > attackCooldownMs * cooldownMul && Senses.ClearLine(entity.World, Senses.Eyes(entity), Senses.Centre(target)))
        {
            StartAttack(now);
            return;
        }
        if (gap <= attackRange * 0.7)
        {
            Stop();
            return;
        }
        // Now and then it is suddenly a couple of blocks nearer, in a burst of static
        if (gap > 3.5 && now - lastSkipMs > skipEveryMs && TrySkip(now)) return;

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
        else if (!pathTraverser.Active && now - lastPathMs > 600 || moved && now - lastPathMs > 750)
        {
            chasing = target.Pos.XYZ;
            Go(chasing, runSpeed, within);
        }
        else
        {
            pathTraverser.CurrentTarget.X = target.Pos.X;
            pathTraverser.CurrentTarget.Y = target.Pos.Y;
            pathTraverser.CurrentTarget.Z = target.Pos.Z;
        }
    }

    /// <summary>A glitch: a jump of a couple of blocks straight at its prey, if the floor there is clear and nothing is in the way.</summary>
    private bool TrySkip(long now)
    {
        lastSkipMs = now;
        double dx = target.Pos.X - entity.Pos.X, dz = target.Pos.Z - entity.Pos.Z;
        double len = Math.Sqrt(dx * dx + dz * dz);
        if (len < 0.1) return false;
        double x = entity.Pos.X + dx / len * skipDistance, z = entity.Pos.Z + dz / len * skipDistance, y = entity.Pos.Y;
        IBlockAccessor ba = entity.World.BlockAccessor;
        var feet = new BlockPos((int)Math.Floor(x), (int)Math.Floor(y + 0.05), (int)Math.Floor(z));
        if (!Senses.Open(ba, feet) || !Senses.Open(ba, feet.UpCopy()) || Senses.Open(ba, feet.DownCopy())) return false;
        if (!Senses.ClearLine(entity.World, entity.Pos.XYZ.Add(0, 1, 0), new Vec3d(x, y + 1, z))) return false;
        Stop();
        entity.TeleportToDouble(x, y, z);
        entity.AnimManager.StartAnimation("glitch");
        if (skipSound != null) entity.World.PlaySoundAt(skipSound, x, y + 1, z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, 16, 0.9f);
        Strike.Log(entity, "skips {0:0.0} blocks", skipDistance);
        return true;
    }

    private void StartAttack(long now)
    {
        Stop();
        attackStartMs = now;
        damageDone = false;
        entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
        entity.AnimManager.StartAnimation("attack");
    }

    private void ContinueAttack(long now)
    {
        long elapsed = now - attackStartMs;
        if (target != null) TurnTowards(target.Pos.XYZ, 0.05f, 5f);
        if (!damageDone && elapsed >= damageAtMs)
        {
            damageDone = true;
            if (sliceSound != null) entity.World.PlaySoundAt(sliceSound, entity.Pos.X, entity.Pos.Y + 1, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, 18, 1f);
            double gap = target == null ? 99 : entity.Pos.DistanceTo(target.Pos) - (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2;
            // (Out of reach by more than a little when the arm comes round, and it misses, as every blow)
            if (target != null && target.Alive && gap <= attackRange + 0.4 && !Strike.IsCreative(target))
            {
                Strike.Hit(entity, target, damage * (float)damageMul, EnumDamageType.SlashingAttack, damageTier + tierBonus, knockback);
                lastBloodMs = now;
            }
        }
        if (elapsed >= attackDurationMs)
        {
            entity.AnimManager.StopAnimation("attack");
            attackStartMs = -1;
            lastAttackMs = now;
        }
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        if (!entity.Alive || source.GetCauseEntity() is not EntityAgent cause) return;
        // Struck, it turns on whoever struck it
        lastBloodMs = entity.World.ElapsedMilliseconds;
        if (state is State.Lurk or State.Return)
        {
            target = cause;
            Wake();
        }
    }

    // ================= Going =================

    private void Go(Vec3d to, float speed, float within)
    {
        lastPathMs = entity.World.ElapsedMilliseconds;
        SetMoving(true, speed >= runSpeed * 0.75f);
        to = to.Clone();
        pathTraverser.Stop();
        pathTraverser.NavigateTo_Async(to, speed * (float)speedMul, within, OnArrived, OnArrived, OnNoPath, 1800, 1);
    }

    private void OnArrived() => SetMoving(false, false);

    private void OnNoPath()
    {
        SetMoving(false, false);
        if (state == State.Chase) straightUntilMs = entity.World.ElapsedMilliseconds + 3000;
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
        if (moving)
        {
            entity.AnimManager.StopAnimation("lurk");
            entity.AnimManager.StartAnimation(running ? "run" : "walk");
        }
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

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
        entity.AnimManager.StopAnimation("attack");
    }
}

/// <summary>
/// A whole terminal in Level 120 (<c>l120-terminal-boot-*</c>): right-clicked, it boots (L120System), and a moment later
/// whoever booted it is somewhere else: a White Void or a Pitch-Black Hallway.
/// </summary>
public class BlockBehaviorL120Boot : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorL120Boot(Block block) : base(block) { }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player)
            world.Api.ModLoader.GetModSystem<L120System>()?.Boot(player, blockSel.Position);
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l120-boot", MouseButton = EnumMouseButton.Right } };
        return help;
    }
}
