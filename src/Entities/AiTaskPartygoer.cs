using System;
using System.Collections.Generic;
using Backrooms.Regions;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// A Partygoer (Entity 67), as the Wikidot canon has it: slow, nearsighted, quiet, and never alone.
/// <list type="bullet">
/// <item><b>At the party</b> (a guest, put down by <see cref="FunSystem"/>): it stands at its place by the head table,
/// swaying, now and then turning to face another way. <b>On patrol</b> (a pack the director sent walking the
/// corridors): it wanders after the first of its pack.</item>
/// <item><b>Seeing.</b> In front of it (140 degrees), as far as the light lets it: 12 blocks if you are in good light
/// (a torch in hand counts), 7 in dim, 4 in the dark; less if you sneak. It hardly hears: only someone running, or a
/// bang, close by. A party hat and a red balloon fool it beyond three blocks, unless you run or strike.</item>
/// <item><b>The gaze.</b> One that sees you stops and stares for a second (it speaks, in a familiar voice), and every
/// other Partygoer that can see <i>it</i> joins the hunt. You can never catch one alone.</item>
/// <item><b>The hunt.</b> It comes at its run, slower than a sprint; it never opens a door and keeps off fire. When
/// none of its pack has seen you for six seconds it goes to where you were last seen, looks about, and goes back.</item>
/// <item><b>The latch</b> (wound up for most of a second): it bites and holds; the bite is Party Fever unless treated
/// (see <see cref="FunSystem.Latched"/>). Below half its health its chest opens (<see cref="EntityBehaviorPartygoer"/>):
/// no more biting, but claws, faster and harder.</item>
/// </list>
/// </summary>
public class AiTaskPartygoer : AiTaskBase
{
    private enum State { Party, Patrol, Gaze, Hunt, Search, Return }
    private enum Motion { Still, Walk, Run }

    private readonly float walkSpeed, runSpeed, latchDamage, clawDamage, attackRange;
    /// <summary>What it sees and hears by (the shared model, see <see cref="Perception"/>), and the same while it hunts: as far as it can see in good light, in any light, all round.</summary>
    private readonly SenseProfile senses, huntSenses;
    private readonly AssetLocation gazeSound, latchSound, clawSound;

    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private State state = State.Party;
    private Motion motion;
    private Entity target;
    private Vec3d home, lastSeenAt;
    private float think, turnTo;
    private long stateMs, lastSeenMs, attackStartMs = -1, lastAttackMs, lastPathMs, wardedSinceMs = -1;

    /// <summary>How long (ms) a hunt stands off from a target kept at bay by a fire before it is given up.</summary>
    private const long WardedGiveUpMs = 20_000;
    private bool damageDone, dangerRead, clawing;
    private float speedMul = 1, damageMul = 1, cooldownMul = 1;
    private int tierBonus;

    /// <summary>When (elapsed ms) any Partygoer last saw each player: the pack shares its eyes.</summary>
    private static readonly Dictionary<long, (long Ms, Vec3d At)> PackSaw = new();

    /// <summary>Forgets what the pack saw and heard (they are static, and times of the last world's clock): at each server start.</summary>
    internal static void Forget()
    {
        PackSaw.Clear();
        HeardMs.Clear();
    }

    public AiTaskPartygoer(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.016f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.031f);
        senses = SenseProfile.Parse(taskConfig["senses"]) ?? new SenseProfile { SightLit = 12, SightDim = 7, SightDark = 4, SightCone = 70, SneakFactor = 0.6f, Hearing = 6, Touch = 2 };
        huntSenses = senses.With(string.Format(System.Globalization.CultureInfo.InvariantCulture,
            "sightLit={0},sightDim={0},sightDark={0},sightCone=360,sneakFactor=1", senses.SightLit), out _);
        latchDamage = taskConfig["latchDamage"].AsFloat(2.5f);
        clawDamage = taskConfig["clawDamage"].AsFloat(4f);
        attackRange = taskConfig["attackRange"].AsFloat(1.6f);
        gazeSound = Sound(taskConfig["gazeSound"].AsString("backrooms:entity/partygoer/gaze"));
        latchSound = Sound(taskConfig["latchSound"].AsString("backrooms:entity/partygoer/latch"));
        clawSound = Sound(taskConfig["clawSound"].AsString("backrooms:entity/partygoer/claw"));
    }

    private static AssetLocation Sound(string code) => code == null ? null : AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/");

    private bool Guest => entity.Attributes.HasAttribute(FunSystem.RoomKey);
    private bool Berserk => entity.WatchedAttributes.GetBool(EntityBehaviorPartygoer.BerserkKey);

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        return menace != null && entity.Alive;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        if (!dangerRead)
        {
            dangerRead = true;
            double d = Danger.Of(entity);
            speedMul = Danger.Speed(d);
            damageMul = Danger.Damage(d);
            cooldownMul = Danger.Cooldown(d);
            tierBonus = Danger.TierBonus(d);
            if (Guest) home = new Vec3d(entity.Attributes.GetDouble(FunSystem.HomeKey + "X"), entity.Attributes.GetDouble(FunSystem.HomeKey + "Y"), entity.Attributes.GetDouble(FunSystem.HomeKey + "Z"));
            state = Guest ? State.Party : State.Patrol;
            turnTo = entity.Pos.Yaw;
        }
        think = 0;
        motion = Motion.Still;
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || menace == null) return false;
        long now = entity.World.ElapsedMilliseconds;

        if (attackStartMs >= 0)
        {
            ContinueAttack(now);
            return true;
        }
        if (menace.Kind == Encounter.Leave)
        {
            // (Not every tick: with nowhere to go, each try is another path search)
            if (!pathTraverser.Active && target != null && now - lastPathMs > 1500) MoveAway(target.Pos.XYZ);
            return true;
        }

        // Turning, smoothly, between thoughts
        if (motion == Motion.Still)
        {
            float desired = state is State.Gaze or State.Hunt && target != null
                ? (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z) : turnTo;
            float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
            entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -2.5f * dt, 2.5f * dt)) % GameMath.TWOPI;
        }

        think -= dt;
        if (think > 0) return true;
        think = 0.25f;

        switch (state)
        {
            case State.Party:
            case State.Patrol:
                if (Look() is { } seen) { StartGaze(seen, now); break; }
                if (state == State.Party) Party(now);
                else Patrol(now);
                break;
            case State.Gaze:
                Stop();
                if (now - stateMs >= 1000)
                {
                    entity.AnimManager.StopAnimation("gaze");
                    if (target is { Alive: true } && entity.Pos.DistanceTo(target.Pos) < 20) BeginHunt(now);
                    else SetState(Guest ? State.Return : State.Patrol, now);
                }
                break;
            case State.Hunt:
                Hunt(now);
                break;
            case State.Search:
                if (Look() is { } again) { target = again; BeginHunt(now); break; }
                if (lastSeenAt != null && !pathTraverser.Active && entity.Pos.XYZ.DistanceTo(lastSeenAt) > 2 && now - lastPathMs > 2000) Go(lastSeenAt, walkSpeed, 1.5f);
                if (now - stateMs > 12000) SetState(Guest ? State.Return : State.Patrol, now);
                break;
            case State.Return:
                if (Look() is { } seen2) { StartGaze(seen2, now); break; }
                if (home == null || entity.Pos.XYZ.DistanceTo(home) < 1.2)
                {
                    Stop();
                    SetState(Guest ? State.Party : State.Patrol, now);
                    menace.Kind = Guest ? Encounter.Ambient : Encounter.Stalk;
                }
                else if (!pathTraverser.Active && now - lastPathMs > 1500) Go(home, walkSpeed, 0.8f);
                break;
        }
        return true;
    }

    // ================= At the party, on patrol =================

    private void Party(long now)
    {
        if (home != null && entity.Pos.XYZ.DistanceTo(home) > 1.5)
        {
            if (!pathTraverser.Active && now - lastPathMs > 1500) Go(home, walkSpeed, 0.8f);
            return;
        }
        Stop();
        // Now and then it turns, slowly, to face somewhere else
        if (entity.World.Rand.NextDouble() < 0.025) turnTo = (float)(entity.World.Rand.NextDouble() * GameMath.TWOPI);
    }

    private void Patrol(long now)
    {
        if (pathTraverser.Active || now - lastPathMs < 2500) return;
        // Keep with the first of the pack, wandering after it
        Entity leader = null;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, 16, 4, e => e != entity && e.Alive && IsPartygoer(e) && !e.Attributes.HasAttribute(FunSystem.RoomKey)))
            if (e.EntityId < entity.EntityId && (leader == null || e.EntityId < leader.EntityId)) leader = e;
        Vec3d around = leader != null ? leader.Pos.XYZ : entity.Pos.XYZ;
        double reach = leader != null ? 4 : 12;
        Random rand = entity.World.Rand;
        for (int i = 0; i < 6; i++)
        {
            double angle = rand.NextDouble() * Math.PI * 2, distance = (leader != null ? 1 : 6) + rand.NextDouble() * reach;
            int x = (int)Math.Floor(around.X + Math.Cos(angle) * distance), z = (int)Math.Floor(around.Z + Math.Sin(angle) * distance);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 2, 3);
            if (y == int.MinValue) continue;
            Go(new Vec3d(x + 0.5, y, z + 0.5), walkSpeed, 1);
            return;
        }
    }

    public static bool IsPartygoer(Entity e) => e.Code?.Domain == "backrooms" && e.Code.Path.StartsWith("partygoer", StringComparison.Ordinal);

    // ================= Seeing =================

    /// <summary>The player it notices now, if any.</summary>
    private Entity Look()
    {
        Entity best = null;
        double bestD = double.MaxValue;
        // (A straw dummy put down for a headless test counts as someone)
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, 18, 6, e => e.Alive && (e is EntityPlayer || e.WatchedAttributes.GetBool("backrooms:testTarget"))))
        {
            if (Strike.IsCreative(e)) continue;
            double d = entity.Pos.DistanceTo(e.Pos);
            if (d < bestD && Notices(e, hunting: false)) { best = e; bestD = d; }
        }
        return best;
    }

    /// <summary>
    /// Whether it notices someone: by sight (the shared model: in front of it, as far as the light lets it, nothing
    /// between; hunting, all round and as far as good light) or by a noise close by. Its hearing is its own rule: only
    /// someone running, or a bang, within <c>hearing</c>, and it has no belief of where they were.
    /// </summary>
    private bool Notices(Entity who, bool hunting)
    {
        if (who is not EntityAgent agent) return false;
        Vec3d eyes = Senses.Eyes(entity), them = Senses.Centre(who);
        double distance = eyes.DistanceTo(them);
        bool running = agent is EntityPlayer && Senses.Running(agent);
        // A bang or someone running, close by, it hears even behind it
        if (!hunting && distance <= senses.Hearing && (running || FunSystemHeard(who))) return Senses.ClearLine(entity.World, eyes, them) || distance <= 3;
        // One of its own, as far as it can tell
        if (!hunting && distance > 3 && !running && !FunSystem.StruckLately(who) && FunSystem.Disguised(agent)) return false;
        return Perception.Sight(entity, who, hunting ? huntSenses : senses, out _) > 0;
    }

    private static readonly Dictionary<long, long> HeardMs = new();

    private bool FunSystemHeard(Entity who) =>
        HeardMs.TryGetValue(who.EntityId, out long at) && entity.World.ElapsedMilliseconds - at < 3000;

    /// <summary>A bang near: every Partygoer within <paramref name="range"/> that can get there comes to see, and sees whoever made it.</summary>
    public static void Hear(IWorldAccessor world, Vec3d at, Entity who, double range)
    {
        if (who != null) HeardMs[who.EntityId] = world.ElapsedMilliseconds;
        foreach (Entity e in world.GetEntitiesAround(at, (float)range, 6, e => e.Alive && IsPartygoer(e)))
        {
            AiTaskPartygoer task = TaskOf(e);
            if (task == null || task.state is State.Hunt || who == null) continue;
            task.target = who;
            task.lastSeenAt = at.Clone();
            task.SetState(State.Search, world.ElapsedMilliseconds);
            task.Go(at, task.runSpeed, 1.5f);
        }
    }

    private static AiTaskPartygoer TaskOf(Entity e) =>
        e.GetBehavior<EntityBehaviorTaskAI>()?.TaskManager?.GetTask<AiTaskPartygoer>();

    // ================= The gaze, and the hunt =================

    private void StartGaze(Entity who, long now)
    {
        target = who;
        Stop();
        SetState(State.Gaze, now);
        entity.AnimManager.StartAnimation("gaze");
        if (gazeSound != null) entity.World.PlaySoundAt(gazeSound, entity.Pos.X, entity.Pos.Y + 1.5, entity.Pos.Z, null, true, 16, 0.8f);
        Saw(who, now);
    }

    private void BeginHunt(long now)
    {
        SetState(State.Hunt, now);
        menace.Target = target;
        menace.Kind = Encounter.Hunt;
        if (target is EntityPlayer { Player: IServerPlayer player }) FunSystem.Voice(player, entity);
        // The rest of the pack, every one that can see this one, joins in
        Vec3d eyes = entity.Pos.XYZ.Add(0, entity.LocalEyePos.Y, 0);
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, 16, 6, e => e != entity && e.Alive && IsPartygoer(e)))
        {
            AiTaskPartygoer other = TaskOf(e);
            if (other == null || other.state is State.Hunt or State.Gaze) continue;
            if (!Senses.ClearLine(entity.World, eyes, e.Pos.XYZ.Add(0, e.LocalEyePos.Y, 0))) continue;
            other.target = target;
            other.menace ??= e.GetBehavior<EntityBehaviorMenace>();
            if (other.menace == null) continue;
            other.SetState(State.Hunt, now);
            other.menace.Target = target;
            other.menace.Kind = Encounter.Hunt;
        }
    }

    private void Saw(Entity who, long now)
    {
        lastSeenMs = now;
        lastSeenAt = who.Pos.XYZ;
        PackSaw[who.EntityId] = (now, who.Pos.XYZ);
    }

    private void Hunt(long now)
    {
        if (target is not { Alive: true } || Strike.IsCreative(target))
        {
            SetState(Guest ? State.Return : State.Patrol, now);
            return;
        }
        if (Notices(target, hunting: true)) Saw(target, now);
        else if (PackSaw.TryGetValue(target.EntityId, out var pack) && pack.Ms > lastSeenMs) { lastSeenMs = pack.Ms; lastSeenAt = pack.At; }
        // Lost: none of the pack has seen them for six seconds
        if (now - lastSeenMs > 6000)
        {
            SetState(State.Search, now);
            return;
        }
        // Fire: it will not go near
        if (Wards.Warded(entity.World, target.Pos.XYZ, Wards.Radius + 1))
        {
            // (It sees them all the while, so nothing else ends this: after a while of standing off, the pack gives up and goes back to the party)
            if (wardedSinceMs < 0) wardedSinceMs = now;
            if (now - wardedSinceMs > WardedGiveUpMs)
            {
                wardedSinceMs = -1;
                SetState(Guest ? State.Return : State.Patrol, now);
                return;
            }
            Stop();
            return;
        }
        wardedSinceMs = -1;
        double gap = Gap(target);
        long cooldown = (long)((Berserk ? 900 : 1500) * cooldownMul);
        if (gap <= attackRange && now - lastAttackMs > cooldown)
        {
            StartAttack(now);
            return;
        }
        Vec3d goal = now - lastSeenMs < 500 ? target.Pos.XYZ : lastSeenAt;
        if (goal != null && (!pathTraverser.Active || now - lastPathMs > 800)) Go(goal, runSpeed * (Berserk ? 1.15f : 1f), 0.9f);
    }

    private double Gap(Entity other) => entity.Pos.DistanceTo(other.Pos) - (entity.SelectionBox.XSize + other.SelectionBox.XSize) / 2;

    // ================= The latch, the claws =================

    private void StartAttack(long now)
    {
        Stop();
        attackStartMs = now;
        damageDone = false;
        clawing = Berserk;
        entity.AnimManager.StartAnimation(clawing ? "claw" : "latch");
        AssetLocation sound = clawing ? clawSound : latchSound;
        if (sound != null) entity.World.PlaySoundAt(sound, entity.Pos.X, entity.Pos.Y + 1, entity.Pos.Z, null, true, 16, 1f);
    }

    private void ContinueAttack(long now)
    {
        long elapsed = now - attackStartMs;
        int windup = clawing ? 450 : 700, duration = clawing ? 650 : 1100;
        if (target != null)
        {
            float desired = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
            entity.Pos.Yaw = desired;
        }
        if (!damageDone && elapsed >= windup)
        {
            damageDone = true;
            if (target is { Alive: true } && Gap(target) <= attackRange + 0.4) Hit();
        }
        if (elapsed >= duration)
        {
            entity.AnimManager.StopAnimation(clawing ? "claw" : "latch");
            attackStartMs = -1;
            lastAttackMs = now;
        }
    }

    private void Hit()
    {
        float damage = (clawing ? clawDamage : latchDamage) * damageMul * (float)(director?.Setting.Damage ?? 1) * GlobalConstants.CreatureDamageModifier;
        if (damage <= 0) return;
        target.ReceiveDamage(new DamageSource
        {
            Source = EnumDamageSource.Entity, SourceEntity = entity, Type = clawing ? EnumDamageType.SlashingAttack : EnumDamageType.PiercingAttack,
            DamageTier = (clawing ? 2 : 1) + tierBonus, KnockbackStrength = clawing ? 0.6f : 0.1f,
        }, damage);
        director?.NoteCloseCall(target);
        if (director?.Logging == true && entity.Api is ICoreServerAPI sapi)
            sapi.Logger.Notification("[backrooms] {0} #{1} {2} {3} for {4:0.0}", entity.Code.Path, entity.EntityId, clawing ? "claws" : "latches on", target.Code.Path, damage);
        if (!clawing) FunSystem.Latched(target);
    }

    // ================= Moving =================

    private void SetState(State next, long now)
    {
        if (next != state && director?.Logging == true && entity.Api is ICoreServerAPI sapi)
            sapi.Logger.Notification("[backrooms] {0} #{1} at {2:0},{3:0}: {4} -> {5}{6}", entity.Code.Path, entity.EntityId, entity.Pos.X, entity.Pos.Z, state, next,
                target == null ? "" : $" ({target.Code.Path}, {entity.Pos.DistanceTo(target.Pos):0.0} blocks)");
        // (The gaze is held; whatever pulls them out of it early, a noise or a blow, must let it go)
        if (state == State.Gaze && next != State.Gaze) entity.AnimManager?.StopAnimation("gaze");
        state = next;
        stateMs = now;
    }

    private void Go(Vec3d to, float speed, float within)
    {
        lastPathMs = entity.World.ElapsedMilliseconds;
        SetMotion(speed >= runSpeed * 0.75f ? Motion.Run : Motion.Walk);
        pathTraverser.NavigateTo_Async(to.Clone(), speed * speedMul, within, OnArrived, OnArrived, OnNoPath, 2500, 1);
    }

    private void MoveAway(Vec3d from)
    {
        double away = Math.Atan2(entity.Pos.Z - from.Z, entity.Pos.X - from.X);
        Go(entity.Pos.XYZ.Add(Math.Cos(away) * 16, 0, Math.Sin(away) * 16), runSpeed, 2);
    }

    private void Stop()
    {
        pathTraverser.Stop();
        SetMotion(Motion.Still);
    }

    private void OnArrived() => SetMotion(Motion.Still);

    private void OnNoPath()
    {
        SetMotion(Motion.Still);
        // Somewhere it cannot get to (behind a door): it waits, and if it is hunting, it soon loses you
        lastPathMs = entity.World.ElapsedMilliseconds + 1500;
    }

    private void SetMotion(Motion next)
    {
        if (next == motion) return;
        if (motion == Motion.Walk) entity.AnimManager.StopAnimation("walk");
        if (motion == Motion.Run) entity.AnimManager.StopAnimation("run");
        motion = next;
        if (motion == Motion.Walk) entity.AnimManager.StartAnimation("walk");
        if (motion == Motion.Run) entity.AnimManager.StartAnimation("run");
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
        if (attackStartMs >= 0) entity.AnimManager.StopAnimation(clawing ? "claw" : "latch");
        attackStartMs = -1;
        if (state == State.Gaze) entity.AnimManager.StopAnimation("gaze");
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        // Struck: it knows who did it, whatever they wear
        if (source.GetCauseEntity() is EntityPlayer player && state is not State.Hunt)
        {
            target = player;
            Saw(player, entity.World.ElapsedMilliseconds);
            menace ??= entity.GetBehavior<EntityBehaviorMenace>();
            if (menace != null) BeginHunt(entity.World.ElapsedMilliseconds);
        }
    }
}

/// <summary>
/// What a Partygoer's body does: its hide is fireproof, until below half its health the chest carapace flips open on the
/// centipede inside, which burns fiercely (fire then does three times as much). When it dies, black smoke that reeks of
/// sulphur; and its party is one guest short until tomorrow.
/// </summary>
public class EntityBehaviorPartygoer : EntityBehavior
{
    public const string BerserkKey = "backrooms:berserk";

    public EntityBehaviorPartygoer(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-partygoer";

    public override void OnEntityReceiveDamage(DamageSource damageSource, ref float damage)
    {
        if (entity.World.Side != EnumAppSide.Server || damageSource.Type == EnumDamageType.Heal) return;
        bool open = entity.WatchedAttributes.GetBool(BerserkKey);
        if (damageSource.Type == EnumDamageType.Fire) damage *= open ? 3f : 0.25f;
        if (damageSource.GetCauseEntity() is EntityPlayer player) FunSystem.Struck(player);
        if (open || entity.GetBehavior<EntityBehaviorHealth>() is not { } health) return;
        if (health.Health - damage < health.MaxHealth * 0.5f && health.Health - damage > 0)
        {
            // The carapace opens
            entity.WatchedAttributes.SetBool(BerserkKey, true);
            entity.AnimManager.StartAnimation("berserk");
            entity.World.RegisterCallback(_ => { if (entity.Alive) entity.AnimManager.StartAnimation("berserkidle"); }, 700);
            entity.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/partygoer/carapace"), entity.Pos.X, entity.Pos.Y + 1.2, entity.Pos.Z, null, true, 20, 1f);
        }
    }

    public override void OnEntityDeath(DamageSource damageSourceForDeath)
    {
        base.OnEntityDeath(damageSourceForDeath);
        if (entity.World.Side != EnumAppSide.Server) return;
        Vec3d at = entity.Pos.XYZ.Add(0, 1, 0);
        entity.World.SpawnParticles(40, ColorUtil.ToRgba(200, 20, 18, 16), at.AddCopy(-0.5, -0.8, -0.5), at.AddCopy(0.5, 0.8, 0.5),
            new Vec3f(-0.3f, 0.1f, -0.3f), new Vec3f(0.3f, 0.9f, 0.3f), 3f, -0.04f, 1.2f, EnumParticleModel.Quad);
        FunSystem.GuestKilled(entity);
    }
}
