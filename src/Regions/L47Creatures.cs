using System;
using System.Collections.Generic;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// What the Adderwood's own creatures have in common (experimental, Level 47): going somewhere by path or straight at
/// something, the walk and run animations, turning, a blow with a wind-up, and the level's system (<see cref="L47System"/>).
/// This file is the level's own.
/// </summary>
public abstract class AiTaskL47Base : AiTaskBase
{
    protected readonly string walkAnim, runAnim;
    protected float walkSpeed, runSpeed;
    protected bool moving, running;
    protected long lastPathMs, attackStartMs = -1, lastAttackMs;
    protected bool damageDone;
    protected Entity target;
    protected float think;

    protected AiTaskL47Base(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig, string walk, string run, float walkDefault, float runDefault)
        : base(entity, taskConfig, aiConfig)
    {
        walkAnim = walk;
        runAnim = run;
        walkSpeed = taskConfig["walkSpeed"].AsFloat(walkDefault);
        runSpeed = taskConfig["runSpeed"].AsFloat(runDefault);
    }

    protected L47System System => entity.Api.ModLoader.GetModSystem<L47System>();

    public override bool ShouldExecute() => entity.Alive;

    protected long Now => entity.World.ElapsedMilliseconds;

    /// <summary>Put down for a showcase shot: it holds its pose (an animation of its own) and does nothing else; true while it does.</summary>
    protected bool Showing(string anim)
    {
        if (!entity.WatchedAttributes.GetBool(L47System.ShowKey)) return false;
        if (anim != null && !entity.AnimManager.IsAnimationActive(anim)) entity.AnimManager.StartAnimation(anim);
        return true;
    }

    protected void Go(Vec3d to, bool run, float within = 1.2f)
    {
        lastPathMs = Now;
        SetMoving(true, run);
        pathTraverser.Stop();
        pathTraverser.NavigateTo_Async(to.Clone(), run ? runSpeed : walkSpeed, within, OnArrived, OnArrived, OnNoPath, 1500, 1);
    }

    protected void Straight(Vec3d to, bool run, float within = 1.2f)
    {
        lastPathMs = Now;
        SetMoving(true, run);
        pathTraverser.WalkTowards(to.Clone(), run ? runSpeed : walkSpeed, within, OnArrived, OnArrived);
    }

    protected virtual void OnArrived() => SetMoving(false, false);

    protected virtual void OnNoPath() => SetMoving(false, false);

    protected void Stop()
    {
        pathTraverser.Stop();
        SetMoving(false, false);
    }

    protected void SetMoving(bool on, bool run)
    {
        if (on == moving && run == running) return;
        if (moving) entity.AnimManager.StopAnimation(running ? runAnim : walkAnim);
        moving = on;
        running = on && run;
        if (moving) entity.AnimManager.StartAnimation(running ? runAnim : walkAnim);
    }

    protected void TurnTowards(Vec3d point, float dt, float rate)
    {
        float desired = (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float step = rate * dt;
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -step, step)) % GameMath.TWOPI;
    }

    protected double Gap(Entity other) => entity.Pos.DistanceTo(other.Pos) - (entity.SelectionBox.XSize + other.SelectionBox.XSize) / 2;

    /// <summary>Whether a player (not creative or spectator) is a target here.</summary>
    protected static bool Prey(Entity e) => e.Alive && (e is EntityPlayer || Senses.IsTestTarget(e)) && !Strike.IsCreative(e);

    protected void Play(string sound, float range, float volume = 1f)
    {
        if (sound == null) return;
        entity.World.PlaySoundAt(new AssetLocation(sound), entity.Pos.X, entity.Pos.Y + 1, entity.Pos.Z, null, 0.9f + (float)entity.World.Rand.NextDouble() * 0.2f, range, volume);
    }

    protected void StartAttack(string anim)
    {
        Stop();
        attackStartMs = Now;
        damageDone = false;
        if (target != null) entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
        entity.AnimManager.StartAnimation(anim);
    }

    /// <summary>A blow under way: lands at <paramref name="hitAt"/> ms if the target is still within reach, done at <paramref name="duration"/>.</summary>
    protected bool ContinueAttack(string anim, int hitAt, int duration, float reach, float damage, int tier, float knockback, string sound)
    {
        if (attackStartMs < 0) return false;
        long elapsed = Now - attackStartMs;
        if (target != null) TurnTowards(target.Pos.XYZ, 0.05f, 6f);
        if (!damageDone && elapsed >= hitAt)
        {
            damageDone = true;
            Play(sound, 20);
            if (target != null && target.Alive && Gap(target) <= reach + 0.4 && Math.Abs(target.Pos.Y - entity.Pos.Y) < 2.5 && !Strike.IsCreative(target))
                Strike.Hit(entity, target, damage, EnumDamageType.PiercingAttack, tier, knockback);
        }
        if (elapsed >= duration)
        {
            entity.AnimManager.StopAnimation(anim);
            attackStartMs = -1;
            lastAttackMs = Now;
        }
        return true;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
    }
}

/// <summary>
/// One of the Adderwood's snakes (Wikidot: "a large and diverse population of numerous species of snakes ... none of them
/// appear to be anomalous"). Harmless: it lies in the litter, slithers about a little, and slips away from anyone who comes
/// close; cornered (someone right on top of it), it rears. Whoever harms one, the Great Adder comes for
/// (<see cref="L47System.Offend"/>). It drifts off and is gone once nobody is near (L47System despawns it).
/// </summary>
public class AiTaskL47Snake : AiTaskL47Base
{
    private enum State { Lie, Wander, Flee, Rear }
    private State state = State.Lie;
    private long stateUntil;

    public AiTaskL47Snake(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig, "slither", "slither", 0.006f, 0.022f) { }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        if (Showing("rear")) return true;
        think -= dt;
        if (think > 0) return true;
        think = 0.3f;
        var rand = entity.World.Rand;
        Entity near = entity.World.GetNearestEntity(entity.Pos.XYZ, 4, 3, e => e.Alive && e is EntityPlayer && !Strike.IsSpectator(e));
        if (near != null)
        {
            double d = near.Pos.DistanceTo(entity.Pos);
            if (d < 1.4 && state != State.Rear)
            {
                Stop();
                state = State.Rear;
                stateUntil = Now + 2500;
                entity.AnimManager.StartAnimation("rear");
                Play($"backrooms:sounds/creature/47/snakehiss{1 + rand.Next(3)}", 10, 0.7f);
                return true;
            }
            if (state is State.Lie or State.Wander || state == State.Rear && Now > stateUntil)
            {
                entity.AnimManager.StopAnimation("rear");
                // Away from them, along the ground
                double ax = entity.Pos.X - near.Pos.X, az = entity.Pos.Z - near.Pos.Z, len = Math.Max(0.1, Math.Sqrt(ax * ax + az * az));
                var to = new Vec3d(entity.Pos.X + ax / len * 6, entity.Pos.Y, entity.Pos.Z + az / len * 6);
                Straight(to, true, 0.8f);
                state = State.Flee;
                stateUntil = Now + 3000;
                if (rand.NextDouble() < 0.3) Play($"backrooms:sounds/creature/47/snakehiss{1 + rand.Next(3)}", 8, 0.5f);
            }
            return true;
        }
        if (state == State.Rear && Now > stateUntil) { entity.AnimManager.StopAnimation("rear"); state = State.Lie; }
        if (state == State.Flee && Now > stateUntil) { Stop(); state = State.Lie; }
        if (state == State.Lie && rand.NextDouble() < 0.04)
        {
            double a = rand.NextDouble() * Math.PI * 2, r = 2 + rand.NextDouble() * 4;
            Go(new Vec3d(entity.Pos.X + Math.Cos(a) * r, entity.Pos.Y, entity.Pos.Z + Math.Sin(a) * r), false, 0.6f);
            state = State.Wander;
            stateUntil = Now + 8000;
        }
        else if (state == State.Wander && (!pathTraverser.Active || Now > stateUntil)) { Stop(); state = State.Lie; }
        return true;
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        // Harming a snake: the Great Adder comes for whoever did it (crows and ravens, and the forest itself, it lets be)
        if (source?.GetCauseEntity() is EntityPlayer player && player.Player is IServerPlayer sp) System?.Offend(sp, entity.Pos.XYZ, "snake");
    }
}

/// <summary>
/// The Great Old Adder (Wikidot): "Harming or killing any of the snakes on Level 47 will result in the immediate appearance of a
/// bright crimson Titanoboa ... which will then proceed to hunt and devour the offending parties. There is no known instance
/// where killing or harming a snake has not resulted in the appearance of the Great Adder, or of anyone successfully evading
/// it or fending it off." Put down out of sight near whoever offended (<see cref="L47System.Offend"/>), it rears and roars,
/// and comes: faster than anyone runs, through the trees by the ways the forest gives it, and where the forest gives it none
/// it is simply nearer the next time it is looked for. Its strike is terrible; whoever it brings down it devours. It pays
/// no heed to anyone else (unless they strike it), and once its quarry is dead or gone from the level it slides away and is gone.
/// </summary>
public class AiTaskL47Adder : AiTaskL47Base
{
    public const string QuarryKey = "backrooms:l47Quarry";
    private enum State { Rise, Hunt, Leave }
    private State state = State.Rise;
    private long stateSince, lastSlipMs, nextHiss, lastLogMs;
    private bool started;
    private Vec3d lastPos;
    private long stuckSince;

    public AiTaskL47Adder(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig, "slither", "slither", 0.02f, 0.062f) { }

    public override void StartExecute()
    {
        base.StartExecute();
        if (started) return;
        started = true;
        stateSince = Now;
        entity.AnimManager.StartAnimation("rear");
        Play("backrooms:sounds/creature/47/adderroar", 64, 1f);
    }

    private Entity Quarry()
    {
        string uid = entity.WatchedAttributes.GetString(QuarryKey);
        if (string.IsNullOrEmpty(uid)) return null;
        if (entity.Api is ICoreServerAPI sapi && sapi.World.PlayerByUid(uid)?.Entity is EntityPlayer p) return p;
        // (A test dummy, by its id)
        if (long.TryParse(uid, out long id)) return entity.World.GetEntityById(id);
        return null;
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        if (Showing("rear")) return true;
        // (Scaled by the level's danger like the other attacks, but capped: 16 flat was a one-hit kill, now 12 to 14 at the default)
        float strike = Math.Min(14f, 9f * Danger.Damage(Danger.Of(entity)));
        if (ContinueAttack("strike", 380, 850, 2.8f, strike, 5, 0.6f, "backrooms:sounds/creature/47/adderstrike")) return true;
        think -= dt;
        if (think > 0) return true;
        think = 0.25f;
        target ??= Quarry();
        var rand = entity.World.Rand;
        if (Now > nextHiss)
        {
            nextHiss = Now + 4000 + rand.Next(5000);
            Play($"backrooms:sounds/creature/47/adderhiss{1 + rand.Next(2)}", 40, 0.9f);
        }
        switch (state)
        {
            case State.Rise:
                if (target != null) TurnTowards(target.Pos.XYZ, 0.25f, 4f);
                if (Now - stateSince > 1800)
                {
                    entity.AnimManager.StopAnimation("rear");
                    state = State.Hunt;
                    stateSince = Now;
                    Strike.Log(entity, "hunts {0}", target?.Code?.Path ?? "nobody");
                }
                return true;
            case State.Hunt:
                Hunt(rand);
                return true;
            case State.Leave:
                if (Now - stateSince > 9000 || !pathTraverser.Active)
                {
                    entity.Die(EnumDespawnReason.Expire);
                    return false;
                }
                return true;
        }
        return true;
    }

    private void Hunt(Random rand)
    {
        // Its quarry dead, gone from the level, or never there: it has what it came for
        bool gone = target == null || !target.Alive || entity.World.Api is ICoreServerAPI && !System.InLevel(target.Pos.X, target.Pos.Z)
            || target.Pos.SquareDistanceTo(entity.Pos) > 160 * 160;
        if (gone || Now - stateSince > 8 * 60_000)
        {
            if (target != null && !target.Alive) entity.AnimManager.StartAnimation("devour");
            if (target != null && !target.Alive) Play("backrooms:sounds/creature/47/adderswallow", 24);
            Leave();
            return;
        }
        if (Strike.IsCreative(target)) { Stop(); return; }
        double gap = Gap(target), dy = Math.Abs(target.Pos.Y - entity.Pos.Y);
        if (Now - lastLogMs > 5000) { lastLogMs = Now; Strike.Log(entity, "hunting, {0:0.0} blocks off, path {1}", gap, pathTraverser.Active); }
        if (gap <= 2.8 && dy < 2.5 && Now - lastAttackMs > 1500)
        {
            StartAttack("strike");
            return;
        }
        // Stuck behind the trees, or left far behind: where nobody is looking, it is suddenly nearer (the forest's own way)
        if (lastPos == null || lastPos.SquareDistanceTo(entity.Pos.XYZ) > 1) { lastPos = entity.Pos.XYZ; stuckSince = Now; }
        bool stuck = Now - stuckSince > 2500;
        if ((stuck || gap > 30) && Now - lastSlipMs > 6000 && !Senses.Sees(target, entity, 64, 60) && Slip(rand)) return;
        if (!pathTraverser.Active && Now - lastPathMs > 700 || Now - lastPathMs > 1600) Go(target.Pos.XYZ, true, 1.5f);
        else if (pathTraverser.Active) { pathTraverser.CurrentTarget.X = target.Pos.X; pathTraverser.CurrentTarget.Y = target.Pos.Y; pathTraverser.CurrentTarget.Z = target.Pos.Z; }
    }

    protected override void OnNoPath()
    {
        base.OnNoPath();
        if (target != null) Straight(target.Pos.XYZ, true, 1.5f);
    }

    /// <summary>Somewhere six to twelve blocks from its quarry, behind them, out of their sight, on open ground: there it is now.</summary>
    private bool Slip(Random rand)
    {
        lastSlipMs = Now;
        for (int attempt = 0; attempt < 10; attempt++)
        {
            double back = target.Pos.Yaw + Math.PI + (rand.NextDouble() - 0.5) * 1.6, r = 6 + rand.NextDouble() * 6;
            int x = (int)Math.Floor(target.Pos.X + Math.Sin(back) * r), z = (int)Math.Floor(target.Pos.Z + Math.Cos(back) * r);
            int y = Senses.FindFloor(entity.World, x, (int)target.Pos.Y, z, 3, 5);
            if (y == int.MinValue) continue;
            var to = new Vec3d(x + 0.5, y, z + 0.5);
            if (Senses.LooksAt(target, to, 50)) continue;
            Stop();
            entity.TeleportToDouble(to.X, to.Y, to.Z);
            lastPos = null;
            Strike.Log(entity, "slips nearer, out of sight");
            return true;
        }
        return false;
    }

    private void Leave()
    {
        state = State.Leave;
        stateSince = Now;
        var rand = entity.World.Rand;
        double a = rand.NextDouble() * Math.PI * 2;
        Go(new Vec3d(entity.Pos.X + Math.Cos(a) * 30, entity.Pos.Y, entity.Pos.Z + Math.Sin(a) * 30), false, 2f);
        Strike.Log(entity, "slides away");
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        // Struck, it turns on whoever struck it (the Order excepted)
        if (source?.GetCauseEntity() is EntityPlayer p && p.Player != null && state != State.Leave)
        {
            target = p;
            entity.WatchedAttributes.SetString(QuarryKey, p.PlayerUID);
        }
    }
}

/// <summary>
/// A Black Shuck (Wikidot: "At night, packs of large black canids become active and will prey upon humans ... When a scout
/// finds prey, they will not let it out of their sight until they are joined by the rest of their hunting party. This typically
/// results in the scout stalking their quarry at close range for prolonged periods of time without ever attacking ... The
/// Shucks themselves also appear to be able to translocate short distances when unobserved by their prey ... the Shucks have
/// never been encountered during the day ... the Black Shucks have been witnessed fleeing from even a lone member of the
/// order"). L47System puts a scout down at night; it keeps close and watches, howling now and then for the rest, who come
/// (L47System puts them down out of sight further off); with three of the pack together they close in. Unobserved, a Shuck
/// may be a few blocks nearer. Out of reach (up a tree), they circle under it and wait. At dawn, or from an Order member,
/// they run, and are gone.
/// </summary>
public class AiTaskL47Shuck : AiTaskL47Base
{
    public const string QuarryKey = "backrooms:l47Quarry";
    private enum State { Stalk, Hunt, Flee }
    private State state = State.Stalk;
    private long stateSince, lastBlinkMs, nextHowl, nextGrowl;
    private bool started;

    public AiTaskL47Shuck(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig, "walk", "run", 0.022f, 0.048f) { }

    public override void StartExecute()
    {
        base.StartExecute();
        if (started) return;
        started = true;
        stateSince = Now;
        nextHowl = Now + 4000;
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        if (Showing("growl")) return true;
        double d = Danger.Of(entity);
        if (ContinueAttack("attack", 300, 700, 1.7f, 5.5f * (float)Danger.Damage(d), 3, 0.3f, $"game:sounds/creature/wolf/attack{1 + entity.World.Rand.Next(8)}")) return true;
        think -= dt;
        if (think > 0) return true;
        think = 0.25f;
        var rand = entity.World.Rand;
        L47System system = System;
        if (state != State.Flee && system != null)
        {
            // Dawn, or an Order member near: run
            if (!system.IsNight() || system.OphionNear(entity.Pos.XYZ, 12)) { Flee(); return true; }
        }
        if (state == State.Flee)
        {
            if (Now - stateSince > 7000 || !pathTraverser.Active) { entity.Die(EnumDespawnReason.Expire); return false; }
            return true;
        }
        if (target == null || !target.Alive)
        {
            string uid = entity.WatchedAttributes.GetString(QuarryKey);
            target = entity.Api is ICoreServerAPI sapi && !string.IsNullOrEmpty(uid) ? sapi.World.PlayerByUid(uid)?.Entity : null;
            if (target == null && long.TryParse(uid, out long id)) target = entity.World.GetEntityById(id);
            target ??= entity.World.GetNearestEntity(entity.Pos.XYZ, 40, 10, Prey);
            if (target == null || !target.Alive) { Flee(); return true; }
        }
        if (Strike.IsCreative(target)) { Stop(); return true; }
        int pack = entity.World.GetEntitiesAround(target.Pos.XYZ, 24, 12, e => e.Alive && e.Code?.Path == "l47-shuck").Length;
        if (state == State.Stalk && pack >= L47System.ShuckPackHunts) { state = State.Hunt; stateSince = Now; StopGrowl(); Play($"game:sounds/creature/wolf/growl{1 + rand.Next(4)}", 24); }
        // Calling the pack in
        if (Now > nextHowl)
        {
            nextHowl = Now + 14000 + rand.Next(12000);
            Stop();
            entity.AnimManager.StartAnimation("howl");
            entity.World.PlaySoundAt(new AssetLocation($"game:sounds/creature/wolf/howl{1 + rand.Next(7)}"), entity.Pos.X, entity.Pos.Y + 1, entity.Pos.Z, null, 0.7f, 96, 1f);
            return true;
        }
        double gap = Gap(target);
        double above = target.Pos.Y - entity.Pos.Y;
        // Up a tree, out of reach: they circle under it and wait for the dawn
        bool treed = above > 2.6;
        if (state == State.Hunt && !treed)
        {
            if (gap <= 1.7 && Math.Abs(above) < 1.6 && Now - lastAttackMs > 1100) { StartAttack("attack"); return true; }
            if (!pathTraverser.Active && Now - lastPathMs > 500 || Now - lastPathMs > 1200) Go(target.Pos.XYZ, true, 1f);
            else if (pathTraverser.Active) { pathTraverser.CurrentTarget.X = target.Pos.X; pathTraverser.CurrentTarget.Y = target.Pos.Y; pathTraverser.CurrentTarget.Z = target.Pos.Z; }
        }
        else
        {
            // Stalking (or treed): stay six to nine blocks off, circling, watching; never attacking
            double want = treed ? 3 : 7;
            if (gap > want + 3 || gap < want - 2) StopGrowl();
            if (gap > want + 3)
            {
                if (!pathTraverser.Active || Now - lastPathMs > 1500) Go(target.Pos.XYZ, gap > 14, (float)want);
            }
            else if (gap < want - 2)
            {
                double ax = entity.Pos.X - target.Pos.X, az = entity.Pos.Z - target.Pos.Z, len = Math.Max(0.1, Math.Sqrt(ax * ax + az * az));
                Straight(new Vec3d(target.Pos.X + ax / len * want, entity.Pos.Y, target.Pos.Z + az / len * want), false, 1f);
            }
            else
            {
                Stop();
                TurnTowards(target.Pos.XYZ, 0.25f, 5f);
                if (Now > nextGrowl)
                {
                    nextGrowl = Now + 6000 + rand.Next(9000);
                    entity.AnimManager.StartAnimation(rand.NextDouble() < 0.5 ? "growl" : "sniff");
                    if (rand.NextDouble() < 0.5) Play($"game:sounds/creature/wolf/growl{1 + rand.Next(4)}", 16, 0.7f);
                }
            }
        }
        // Unobserved, a few blocks nearer
        if (Now - lastBlinkMs > 7000 && gap > 4 && !Senses.Sees(target, entity, 48, 55)) Blink(rand);
        return true;
    }

    /// <summary>A growl or sniff started while stalking is cut short when the stalking ends (Showing holds the task while one plays).</summary>
    private void StopGrowl()
    {
        entity.AnimManager.StopAnimation("growl");
        entity.AnimManager.StopAnimation("sniff");
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        StopGrowl();
    }

    private void Blink(Random rand)
    {
        lastBlinkMs = Now;
        double ax = entity.Pos.X - target.Pos.X, az = entity.Pos.Z - target.Pos.Z, len = Math.Sqrt(ax * ax + az * az);
        if (len < 0.1) return;
        double r = Math.Max(3.5, len - 3 - rand.NextDouble() * 3), a = Math.Atan2(az, ax) + (rand.NextDouble() - 0.5) * 1.2;
        int x = (int)Math.Floor(target.Pos.X + Math.Cos(a) * r), z = (int)Math.Floor(target.Pos.Z + Math.Sin(a) * r);
        int y = Senses.FindFloor(entity.World, x, (int)entity.Pos.Y, z, 2, 4);
        if (y == int.MinValue) return;
        var to = new Vec3d(x + 0.5, y, z + 0.5);
        if (Senses.LooksAt(target, to, 55)) return;
        Stop();
        entity.TeleportToDouble(to.X, to.Y, to.Z);
        Strike.Log(entity, "translocates, unobserved");
    }

    private void Flee()
    {
        if (state == State.Flee) return;
        StopGrowl();
        state = State.Flee;
        stateSince = Now;
        var rand = entity.World.Rand;
        Vec3d from = target?.Pos.XYZ ?? entity.Pos.XYZ;
        double ax = entity.Pos.X - from.X, az = entity.Pos.Z - from.Z, len = Math.Max(0.1, Math.Sqrt(ax * ax + az * az));
        if (len < 0.5) { double a = rand.NextDouble() * Math.PI * 2; ax = Math.Cos(a); az = Math.Sin(a); len = 1; }
        Straight(new Vec3d(entity.Pos.X + ax / len * 40, entity.Pos.Y, entity.Pos.Z + az / len * 40), true, 2f);
        Strike.Log(entity, "runs for its den");
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        if (state == State.Stalk && source?.GetCauseEntity() is EntityPlayer p) { target = p; state = State.Hunt; stateSince = Now; StopGrowl(); }
    }
}

/// <summary>
/// A member of the Ophion Occult Order (Wikidot: "typically hostile towards any wanderers who come across their secret glade
/// ... Members of this order have also been spotted along the trail or in the forest itself, typically clad in hooded, crimson
/// garb and ivory masks. Though normally indifferent to wanderers, encounters have varied from abduction to proselytization").
/// In the glade (a "keeper", by its home there) it guards: whoever comes into the glade it warns once, then drives off,
/// striking, as far as the edge of the forest, and goes back. On the trail (a "walker") it walks the trail, indifferent; whoever
/// comes near it stops for, looks at, and now and then preaches to (the Order's boasts: L47System's lines). Struck, it fights
/// back; and harming one brings the Great Adder (our reading of "an ability to summon and to some extent command The Great
/// Adder"). The Black Shucks run from it.
/// </summary>
public class AiTaskL47Ophion : AiTaskL47Base
{
    public const string HomeKey = "backrooms:l47Home", WalkerKey = "backrooms:l47Walker";
    private enum State { Idle, Walk, Watch, Preach, Drive, Return }
    private State state = State.Idle;
    private long stateUntil, nextWord;
    private bool started, walker;
    /// <summary>The intruders (by entity id) already warned in the glade.</summary>
    private readonly HashSet<long> warnedIds = new();
    private Vec3d home;
    private double trailPhi = -1;
    private int trailDir = 1;

    public AiTaskL47Ophion(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig, "walk", "run", 0.016f, 0.04f) { }

    public override void StartExecute()
    {
        base.StartExecute();
        if (started) return;
        started = true;
        ITreeAttribute a = entity.WatchedAttributes;
        walker = a.GetBool(WalkerKey);
        home = a.HasAttribute(HomeKey + "X") ? new Vec3d(a.GetDouble(HomeKey + "X"), a.GetDouble(HomeKey + "Y"), a.GetDouble(HomeKey + "Z")) : entity.Pos.XYZ;
        trailDir = entity.World.Rand.NextDouble() < 0.5 ? 1 : -1;
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        if (Showing("preach")) return true;
        double dng = Danger.Of(entity);
        if (ContinueAttack("attack", 420, 800, 1.9f, 4.5f * (float)Danger.Damage(dng), 2, 0.5f, "game:sounds/player/strike1")) return true;
        think -= dt;
        if (think > 0) return true;
        think = 0.3f;
        var rand = entity.World.Rand;
        L47System system = System;
        if (system == null) return true;
        Entity near = entity.World.GetNearestEntity(entity.Pos.XYZ, 14, 6, Prey);

        if (state == State.Drive)
        {
            if (target == null || !target.Alive || Strike.IsCreative(target) || !walker && !system.InGlade(target.Pos.X, target.Pos.Z, 12) && Gap(target) > 4
                || entity.Pos.SquareDistanceTo(home) > 70 * 70)
            {
                target = null;
                state = State.Return;
                Go(home, false, 2f);
                return true;
            }
            if (Gap(target) <= 1.9 && Math.Abs(target.Pos.Y - entity.Pos.Y) < 1.8 && Now - lastAttackMs > 1300) { StartAttack("attack"); return true; }
            if (!pathTraverser.Active && Now - lastPathMs > 600 || Now - lastPathMs > 1400) Go(target.Pos.XYZ, true, 1.2f);
            return true;
        }
        if (state == State.Return)
        {
            if (!pathTraverser.Active || entity.Pos.SquareDistanceTo(home) < 4) { Stop(); state = State.Idle; }
            return true;
        }

        // A keeper in the glade: whoever comes into it is warned, then driven out
        if (near == null && warnedIds.Count > 0) warnedIds.Clear();
        if (!walker && near != null && system.InGlade(near.Pos.X, near.Pos.Z, 0))
        {
            if (warnedIds.Add(near.EntityId))
            {
                Stop();
                TurnTowards(near.Pos.XYZ, 1, 99);
                entity.AnimManager.StartAnimation("beckon");
                system.Say(entity, near, "l47-ophion-warn");
                stateUntil = Now + 3500;
                state = State.Watch;
                return true;
            }
            if (state != State.Watch || Now > stateUntil)
            {
                target = near;
                state = State.Drive;
                system.Say(entity, near, "l47-ophion-drive");
                Go(near.Pos.XYZ, true, 1.2f);
            }
            return true;
        }

        // Someone near, out of the glade: it stops and looks at them; now and then it preaches
        if (near != null && Gap(near) < 7)
        {
            if (state is State.Idle or State.Walk)
            {
                Stop();
                state = State.Watch;
                stateUntil = Now + 6000 + rand.Next(6000);
            }
            TurnTowards(near.Pos.XYZ, 0.3f, 4f);
            if (Now > nextWord && rand.NextDouble() < 0.35)
            {
                nextWord = Now + 20000 + rand.Next(20000);
                entity.AnimManager.StartAnimation(rand.NextDouble() < 0.6 ? "preach" : "beckon");
                system.Preach(entity, near);
                state = State.Preach;
                stateUntil = Now + 5000;
            }
            if (state == State.Preach && Now > stateUntil) { entity.AnimManager.StopAnimation("preach"); state = State.Watch; stateUntil = Now + 5000; }
            if (state == State.Watch && Now > stateUntil && walker) { state = State.Idle; }
            return true;
        }
        entity.AnimManager.StopAnimation("preach");
        if (state is State.Watch or State.Preach) state = State.Idle;

        // Going about: a walker goes along the trail; a keeper stands, or walks a little about the glade
        if (walker)
        {
            if (!pathTraverser.Active || Now - lastPathMs > 12000)
            {
                if (trailPhi < 0) trailPhi = system.TrailPhiAt(entity.Pos.X, entity.Pos.Z);
                if (trailPhi >= 0)
                {
                    trailPhi = Math.Max(0, trailPhi + trailDir * 0.18 * 150 / Math.Max(60, system.TrailRadius(trailPhi)));
                    var (x, z) = system.TrailPoint(trailPhi);
                    int y = Senses.FindFloor(entity.World, (int)Math.Floor(x), (int)entity.Pos.Y, (int)Math.Floor(z), 2, 6);
                    if (y != int.MinValue) Go(new Vec3d(x, y, z), false, 1.5f);
                    state = State.Walk;
                }
            }
            return true;
        }
        if (state == State.Idle && rand.NextDouble() < 0.02)
        {
            double a = rand.NextDouble() * Math.PI * 2, r = rand.NextDouble() * 6;
            Go(new Vec3d(home.X + Math.Cos(a) * r, home.Y, home.Z + Math.Sin(a) * r), false, 1f);
            state = State.Walk;
        }
        else if (state == State.Walk && !pathTraverser.Active) state = State.Idle;
        return true;
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        if (source?.GetCauseEntity() is not EntityPlayer p || p.Player is not IServerPlayer sp) return;
        target = p;
        state = State.Drive;
        System?.Say(entity, p, "l47-ophion-struck");
        System?.Offend(sp, entity.Pos.XYZ, "ophion");
    }
}
