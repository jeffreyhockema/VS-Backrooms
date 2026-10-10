using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;
using Vintagestory.API.Client;

namespace Backrooms.Entities;

/// <summary>
/// What a Backrooms entity does about the person it was put down for, according to its encounter (see
/// <see cref="EntityBehaviorMenace"/>):
/// <list type="bullet">
/// <item>Glimpse: stands far off, facing them, and leaves when they come close or stare.</item>
/// <item>Stalk: keeps a distance, out of sight or out of the light, moving when they move. It turns to the hunt when
/// they falter: running, coming apart (low Reality Stability), alone in the dark at the edge of a level.</item>
/// <item>Hunt: closes in and attacks, as far as its counters let it.</item>
/// <item>Leave: runs off, to be despawned out of sight.</item>
/// </list>
/// Ambient entities (Facelings, the city's Hounds) leave this task idle and wander with the vanilla tasks, unless
/// someone hurts them.
///
/// Each kind of entity sets what holds it back in its task config: <c>lightBound</c> (Smilers never step into light,
/// and freeze while stared at), <c>fearsFire</c> (keeps clear of lit firepits, Firesalt and angel statues),
/// <c>grabsThroughWalls</c> and <c>respectsAlmond</c> (Dullers), <c>avoidsLight</c> (rats keep out of a carried
/// light), <c>slowedByLight</c>, <c>coward</c> (flees when hurt or faced), <c>retaliates</c>.
/// </summary>
public class AiTaskMenace : AiTaskBase
{
    private enum Motion { Still, Walk, Run }

    // ---- Config ----
    private readonly float walkSpeed, runSpeed, stalkMin, stalkMax, glimpseFleeDistance, attackRange, damage, knockback;
    private readonly int damageTier, attackDurationMs, damageAtMs, attackCooldownMs;
    private readonly EnumDamageType damageType;
    private readonly string walkAnim, runAnim, attackAnim;
    private readonly AssetLocation stalkSound, huntSound, attackSound, grabSound;
    private readonly AssetLocation[] voices;
    private readonly bool lightBound, fearsFire, grabsThroughWalls, respectsAlmond, avoidsLight, slowedByLight, coward, retaliates, prefersHidden, staredDown;
    private readonly float retreatBelow, cryRange, stealChance, liftBlocks;
    /// <summary>Played once, standing still, when it first appears (the Bacteria rising out of the mould), and for how long.</summary>
    private readonly string emergeAnim;
    private readonly int emergeMs;
    /// <summary>Played standing still as it turns to the hunt (a Wretch's snarl, the Bacteria's howl), and for how long.</summary>
    private readonly string huntAnim;
    private readonly int huntAnimMs;
    /// <summary>May turn on someone who runs near the way out of Level 0 (where nothing else hunts but in the Red Rooms).</summary>
    private readonly bool huntsInLobby;
    private bool emerged;
    /// <summary>Until when it stands where it is, playing one of those, only turning to face its target.</summary>
    private long holdUntilMs;

    // ---- State ----
    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private Entity target;
    private Motion motion;
    private float think, watchedFor, heldFor, runningFor, nextVoice = 10, nextGrowl = 4;
    private long attackStartMs = -1, lastAttackMs, lastPathMs, lastHurtByTargetMs, noPathUntilMs;
    private bool damageDone, announcedHunt, glimpseDecided, crossing, crossed;
    private int thoughts;
    private Vec3d plannedAt, chasing;
    private Encounter lastKind = (Encounter)(-1);
    /// <summary>What the level's danger does to this one (see <see cref="Danger"/>), read when it first thinks.</summary>
    private float speedMul = 1, damageMul = 1, cooldownMul = 1, turnMul = 1;
    private int tierBonus;
    private double giveUpAt = 40;
    private bool dangerRead;
    /// <summary>A Hound's nerve under a stare, in seconds; it is spent, never regained (-1 until first stared at).</summary>
    private float nerve = -1;
    private bool growling;

    public AiTaskMenace(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.02f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.04f);
        stalkMin = taskConfig["stalkMin"].AsFloat(8);
        stalkMax = taskConfig["stalkMax"].AsFloat(14);
        glimpseFleeDistance = taskConfig["glimpseFleeDistance"].AsFloat(14);
        attackRange = taskConfig["attackRange"].AsFloat(0.9f);
        damage = taskConfig["damage"].AsFloat(2);
        knockback = taskConfig["knockback"].AsFloat(0.5f);
        damageTier = taskConfig["damageTier"].AsInt(1);
        damageType = Enum.TryParse(taskConfig["damageType"].AsString("PiercingAttack"), true, out EnumDamageType t) ? t : EnumDamageType.PiercingAttack;
        attackDurationMs = taskConfig["attackDurationMs"].AsInt(900);
        damageAtMs = taskConfig["damageAtMs"].AsInt(450);
        attackCooldownMs = taskConfig["attackCooldownMs"].AsInt(1500);
        walkAnim = Anim(taskConfig["walkAnimation"].AsString("walk"));
        runAnim = Anim(taskConfig["runAnimation"].AsString("run"));
        attackAnim = Anim(taskConfig["attackAnimation"].AsString(null));
        stalkSound = Sound(taskConfig["stalkSound"].AsString(null));
        huntSound = Sound(taskConfig["huntSound"].AsString(null));
        attackSound = Sound(taskConfig["attackSound"].AsString(null));
        grabSound = Sound(taskConfig["grabSound"].AsString(null));
        voices = Array.ConvertAll(taskConfig["voices"].AsArray(Array.Empty<string>()), Sound);
        cryRange = taskConfig["soundRange"].AsFloat(24);
        lightBound = taskConfig["lightBound"].AsBool(false);
        fearsFire = taskConfig["fearsFire"].AsBool(false);
        grabsThroughWalls = taskConfig["grabsThroughWalls"].AsBool(false);
        respectsAlmond = taskConfig["respectsAlmond"].AsBool(false);
        avoidsLight = taskConfig["avoidsLight"].AsBool(false);
        slowedByLight = taskConfig["slowedByLight"].AsBool(false);
        coward = taskConfig["coward"].AsBool(false);
        retaliates = taskConfig["retaliates"].AsBool(true);
        prefersHidden = taskConfig["prefersHidden"].AsBool(false);
        retreatBelow = taskConfig["retreatBelow"].AsFloat(0);
        staredDown = taskConfig["staredDown"].AsBool(false);
        stealChance = taskConfig["stealChance"].AsFloat(0);
        liftBlocks = taskConfig["liftBlocks"].AsFloat(0);
        emergeAnim = Anim(taskConfig["emergeAnimation"].AsString(null));
        emergeMs = taskConfig["emergeMs"].AsInt(0);
        huntAnim = Anim(taskConfig["huntAnimation"].AsString(null));
        huntAnimMs = taskConfig["huntAnimationMs"].AsInt(0);
        huntsInLobby = taskConfig["huntsInLobby"].AsBool(false);
    }

    /// <summary>An animation code, or null for none (an empty string in the config).</summary>
    private static string Anim(string code) => string.IsNullOrEmpty(code) ? null : code.ToLowerInvariant();

    private static AssetLocation Sound(string code) => code == null ? null : AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/");

    private Encounter Kind
    {
        get => menace.Kind;
        set
        {
            if (menace.Kind == value) return;
            Log("{0} -> {1}", menace.Kind, value);
            menace.Kind = value;
        }
    }

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null) return false;
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        Encounter kind = menace.Kind;
        return kind is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Leave;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        if (!dangerRead)
        {
            dangerRead = true;
            double d = Danger.Of(entity);
            speedMul = Danger.Speed(d);
            damageMul = Danger.Damage(d);
            cooldownMul = Danger.Cooldown(d);
            tierBonus = Danger.TierBonus(d);
            turnMul = (float)(1 + 2 * d);
            giveUpAt = 40 + 25 * d;
        }
        if (emergeAnim != null && !emerged)
        {
            emerged = true;
            Hold(emergeAnim, emergeMs);
        }
        Log("starts: {0}", menace.Kind);
        think = 0;
        plannedAt = null;
        motion = Motion.Still;
        attackStartMs = -1;
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || menace == null) return false;
        Encounter kind = Kind;
        if (kind is Encounter.Ambient) return false;
        target = menace.Target;

        if (attackStartMs >= 0)
        {
            ContinueAttack();
            return true;
        }

        // Still coming up out of the floor, or snarling before the chase: only the head turns
        if (entity.World.ElapsedMilliseconds < holdUntilMs)
        {
            if (target != null) TurnTowards(target.Pos.XYZ, dt);
            return true;
        }

        if (kind != lastKind)
        {
            OnKindChanged(kind);
            lastKind = kind;
            if (entity.World.ElapsedMilliseconds < holdUntilMs) return true;
        }

        think -= dt;
        if (motion == Motion.Still && target != null && kind != Encounter.Leave) TurnTowards(target.Pos.XYZ, dt);
        if (think > 0) return true;
        think = 0.3f;

        if (target == null || !target.Alive)
        {
            Kind = Encounter.Leave;
            Leave();
            return true;
        }

        if (kind == Encounter.Leave)
        {
            Leave();
            return true;
        }

        double distance = entity.Pos.DistanceTo(target.Pos);
        MenaceSystem.Assessment a = director.AssessmentOf(target);
        if (++thoughts % 10 == 0) Log("{0}, {1:0.0} blocks from {2}, {3}{4}", kind, distance, target.Code.Path, motion, pathTraverser.Active ? " (on a path)" : "");

        // Whatever it is doing, it gives up on someone who reaches a sanctuary, and the hurt ones run
        bool provoked = EntityBehaviorFaceling.Provoked(entity);
        if (a.Band == MenaceBand.Safe && kind != Encounter.Glimpse && !provoked || retreatBelow > 0 && HealthFraction() < retreatBelow)
        {
            Kind = Encounter.Leave;
            return true;
        }
        if (distance > giveUpAt + 16)
        {
            Kind = Encounter.Leave;
            return true;
        }

        // Things that will not stand in the light, or near a fire, get out of it first
        if (lightBound && LitHere(Senses.Centre(entity)) || fearsFire && Wards.Warded(entity.World, entity.Pos.XYZ, Wards.Radius - 1))
        {
            if (!pathTraverser.Active && entity.World.ElapsedMilliseconds - lastPathMs > 1200)
                MoveAwayFrom(lightBound ? target.Pos.XYZ : Wards.Near(entity.World, entity.Pos.XYZ) ?? target.Pos.XYZ, 6, runSpeed);
            return true;
        }

        if (target is EntityAgent agent && Senses.Running(agent)) runningFor += 0.3f;
        else runningFor = 0;

        switch (kind)
        {
            case Encounter.Glimpse:
                Glimpse(distance);
                break;
            case Encounter.Stalk:
                Stalk(distance, a);
                break;
            case Encounter.Hunt:
                Hunt(distance, a);
                break;
        }
        PlayVoice(dt: 0.3f, distance);
        return true;
    }

    private void OnKindChanged(Encounter kind)
    {
        Encounter before = lastKind;
        plannedAt = chasing = null;
        lastPathMs = 0;
        if (kind == Encounter.Stalk && before != Encounter.Hunt && stalkSound != null && entity.World.Rand.NextDouble() < 0.6) PlaySound(stalkSound);
        if (kind == Encounter.Hunt && !announcedHunt)
        {
            announcedHunt = true;
            if (!entity.Attributes.GetBool(EntityBehaviorMenace.RalliedKey))
            {
                if (huntSound != null) PlaySound(huntSound);
                RallyPack();
            }
            if (huntAnim != null) Hold(huntAnim, huntAnimMs);
        }
    }

    // ================= Encounters =================

    private void Glimpse(double distance)
    {
        if (distance < glimpseFleeDistance)
        {
            Kind = Encounter.Leave;
            return;
        }

        // Some glimpses are of something crossing: a few unhurried steps across the way ahead, and it is gone
        if (!glimpseDecided)
        {
            glimpseDecided = true;
            bool frenzy = entity.Attributes.GetBool(FrenzyKey);
            Vec3d across = frenzy || entity.World.Rand.NextDouble() < 0.4 ? CrossingPoint(frenzy ? 9 : 5) : null;
            if (across != null)
            {
                crossing = true;
                Go(across, frenzy ? runSpeed : walkSpeed, 0.8f);
            }
        }
        if (crossing)
        {
            if (crossed || entity.World.ElapsedMilliseconds - lastPathMs > 1000 && !pathTraverser.Active) Kind = Encounter.Leave;
            return;
        }

        Stop();
        // Stared at, it goes
        if (target is EntityAgent viewer && Senses.LooksAt(viewer, Senses.Centre(entity), 10) && Senses.Sees(viewer, entity, 64))
        {
            watchedFor += 0.3f;
            if (watchedFor > 3) Kind = Encounter.Leave;
        }
        else watchedFor = Math.Max(0, watchedFor - 0.15f);
    }

    private void Stalk(double distance, MenaceSystem.Assessment a)
    {
        bool stared = target is EntityAgent viewer && Senses.LooksAt(viewer, Senses.Centre(entity), 14) && Senses.Sees(viewer, entity, 48);

        // A Duller confronted runs; a Smiler held in someone's gaze, who neither runs nor looks away, freezes and at last withdraws
        if (stared && coward && distance < 16)
        {
            Kind = Encounter.Leave;
            return;
        }
        if (lightBound && stared && runningFor == 0)
        {
            Stop();
            watchedFor += 0.3f;
            if (watchedFor > 6) Kind = Encounter.Leave;
            return;
        }
        watchedFor = Math.Max(0, watchedFor - 0.1f);

        if (grabsThroughWalls && TryGrab(distance)) return;
        if (staredDown && StaredDown(distance)) return;

        if (ShouldTurnToHunt(distance, a))
        {
            Kind = Encounter.Hunt;
            return;
        }

        // Keep the distance: close in when too far off, fall back when too near, otherwise wait and watch
        if (distance > stalkMax || distance < stalkMin - 1)
        {
            bool replan = plannedAt == null || plannedAt.DistanceTo(target.Pos.XYZ) > 3 || !pathTraverser.Active;
            if (replan && entity.World.ElapsedMilliseconds - lastPathMs > 1200)
            {
                Vec3d point = StalkPoint();
                if (point != null)
                {
                    plannedAt = target.Pos.XYZ;
                    Go(point, distance > stalkMax + 10 ? runSpeed * 0.8f : walkSpeed, 1);
                }
            }
        }
        else if (motion != Motion.Still && !pathTraverser.Active) Stop();
        else if (motion != Motion.Still && distance < (stalkMin + stalkMax) / 2) Stop();

        if (stalkSound != null)
        {
            nextGrowl -= 0.3f;
            if (nextGrowl <= 0)
            {
                nextGrowl = 8 + (float)entity.World.Rand.NextDouble() * 12;
                if (entity.World.Rand.NextDouble() < 0.4) PlaySound(stalkSound);
            }
        }
    }

    /// <summary>Whether a stalker loses patience: the person it follows runs, comes apart, or stands alone in the dark at the edge.</summary>
    private bool ShouldTurnToHunt(double distance, MenaceSystem.Assessment a)
    {
        if (menace.Passive || a.Band < MenaceBand.Approach || NoPathLately) return false;
        if (IsCreative(target)) return false;
        // The Lobby is empty, as the lore has it: what watches there never hunts, but in the Red Rooms
        if (a.Level == 0 && !a.Worst && !(huntsInLobby && a.Band == MenaceBand.Threshold && runningFor > 1.5 && distance < 20)) return false;
        if (respectsAlmond && Protected(target)) return false;
        Random rand = entity.World.Rand;
        if (lightBound)
        {
            // Smilers come only for those in the dark
            if (!a.Dark) return false;
            return runningFor > 1 || Senses.Stability(target) < 0.4 || a.Band == MenaceBand.Threshold && rand.NextDouble() < 0.08 * 0.3;
        }
        if (avoidsLight && Senses.HeldLight(target) >= 10) return false;
        // Running is what gives you away: anything following within earshot gives chase
        if (runningFor > 1.5 && distance < 28) return true;
        if (Senses.Stability(target) < 0.4) return rand.NextDouble() < 0.2 * 0.3 * turnMul;
        return a.Value >= 0.8 && rand.NextDouble() < 0.04 * 0.3 * turnMul;
    }

    private void Hunt(double distance, MenaceSystem.Assessment a)
    {
        if (menace.Passive || IsCreative(target))
        {
            Kind = Encounter.Stalk;
            return;
        }
        if (distance > giveUpAt)
        {
            Kind = Encounter.Leave;
            return;
        }
        // A coward faced runs, even mid-hunt
        if (coward && distance < 16 && target is EntityAgent viewer && Senses.LooksAt(viewer, Senses.Centre(entity), 14) && Senses.Sees(viewer, entity, 48))
        {
            Kind = Encounter.Leave;
            return;
        }
        if (grabsThroughWalls)
        {
            if (TryGrab(distance)) return;
            if (respectsAlmond && Protected(target))
            {
                Kind = Encounter.Leave;
                return;
            }
        }

        if (staredDown && StaredDown(distance)) return;

        // A Smiler held in someone's gaze, who neither runs nor looks away, freezes
        if (lightBound && runningFor == 0 && target is EntityAgent starer && Senses.LooksAt(starer, Senses.Centre(entity), 14) && Senses.Sees(starer, entity, 48))
        {
            Stop();
            watchedFor += 0.3f;
            if (watchedFor > 6) Kind = Encounter.Leave;
            return;
        }
        watchedFor = Math.Max(0, watchedFor - 0.1f);

        // What holds it back: a Smiler stops dead at the edge of the light (the next step would be lit), the rest at
        // the edge of a fire's reach, and rats keep clear of a carried light. Held back too long, it gives up.
        bool heldBack = lightBound && LitHere(NextStepTowards(target.Pos.XYZ, 1.5))
            || fearsFire && Wards.Warded(entity.World, target.Pos.XYZ, Wards.Radius + 1)
            || avoidsLight && Senses.HeldLight(target) >= 10 && distance < 5;
        if (heldBack)
        {
            heldFor += 0.3f;
            if (heldFor > 20)
            {
                Kind = Encounter.Leave;
                return;
            }
            if (distance < 5 && !pathTraverser.Active && entity.World.ElapsedMilliseconds - lastPathMs > 1200) MoveAwayFrom(target.Pos.XYZ, 4, walkSpeed);
            else if (distance >= 5) Stop();
            return;
        }
        heldFor = 0;
        if (NoPathLately)
        {
            Stop();
            return;
        }

        double gap = Gap(target);
        if (gap <= attackRange && entity.World.ElapsedMilliseconds - lastAttackMs > attackCooldownMs * cooldownMul
            && Senses.ClearLine(entity.World, Senses.Centre(entity), Senses.Centre(target)))
        {
            StartAttack();
            return;
        }

        // Close enough: wait out the cooldown face to face
        if (gap <= attackRange)
        {
            Stop();
            return;
        }

        float speed = runSpeed;
        if (slowedByLight && !Senses.InDark(target)) speed *= 0.7f;
        // A new path when there is none or the prey has moved on (as vanilla's seek does); otherwise steer the old one at it
        bool moved = chasing == null || chasing.SquareDistanceTo(target.Pos.X, target.Pos.Y, target.Pos.Z) >= 9;
        if (!pathTraverser.Active || moved && entity.World.ElapsedMilliseconds - lastPathMs > 750)
        {
            chasing = target.Pos.XYZ;
            Go(chasing, speed, attackRange * 0.6f + (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2, async: false);
        }
        else
        {
            pathTraverser.CurrentTarget.X = target.Pos.X;
            pathTraverser.CurrentTarget.Y = target.Pos.Y;
            pathTraverser.CurrentTarget.Z = target.Pos.Z;
        }
    }

    /// <summary>
    /// A Hound met with a steady stare (the lore's one sure thing about them): it stops, lowers its head and growls, and
    /// backs off a step. It holds only a few seconds, all told, for each Hound: then its nerve goes the other way and
    /// it comes at whoever stared. Returns whether it is held for now.
    /// </summary>
    private bool StaredDown(double distance)
    {
        if (nerve < 0) nerve = 4 + (float)entity.World.Rand.NextDouble() * 4;
        bool stared = nerve > 0 && distance < 12 && target is EntityPlayer viewer && !IsCreative(target)
            && Senses.LooksAt(viewer, Senses.Centre(entity), 10) && Senses.Sees(viewer, entity, 16);
        if (!stared)
        {
            if (growling) entity.AnimManager.StopAnimation("growl");
            growling = false;
            return false;
        }
        nerve -= 0.3f;
        if (nerve <= 0)
        {
            nerve = 0;
            if (growling) entity.AnimManager.StopAnimation("growl");
            growling = false;
            Log("its nerve breaks: it comes on");
            if (huntSound != null) PlaySound(huntSound);
            if (!menace.Passive) Kind = Encounter.Hunt;
            return false;
        }
        if (!growling || !entity.AnimManager.ActiveAnimationsByAnimCode.ContainsKey("growl"))
        {
            if (!growling)
            {
                Stop();
                Log("stared down");
                if (stalkSound != null) PlaySound(stalkSound);
            }
            growling = true;
            entity.AnimManager.StartAnimation("growl");
        }
        if (distance < 6 && !pathTraverser.Active && entity.World.ElapsedMilliseconds - lastPathMs > 1500) MoveAwayFrom(target.Pos.XYZ, 3, walkSpeed);
        else if (!pathTraverser.Active && motion != Motion.Still) SetMotion(Motion.Still);
        return true;
    }

    private void Leave()
    {
        if (target == null)
        {
            Stop();
            return;
        }
        if (!pathTraverser.Active || entity.World.ElapsedMilliseconds - lastPathMs > 2500)
        {
            MoveAwayFrom(target.Pos.XYZ, 24, runSpeed);
        }
    }

    // ================= Attacks =================

    private void StartAttack()
    {
        Stop();
        attackStartMs = entity.World.ElapsedMilliseconds;
        damageDone = false;
        if (attackAnim != null) entity.AnimManager.StartAnimation(attackAnim);
        if (attackSound != null) PlaySound(attackSound);
    }

    private void ContinueAttack()
    {
        long elapsed = entity.World.ElapsedMilliseconds - attackStartMs;
        if (target != null) TurnTowards(target.Pos.XYZ, 0.05f);
        if (!damageDone && elapsed >= damageAtMs)
        {
            damageDone = true;
            if (target != null && target.Alive && Gap(target) <= attackRange + 0.4)
            {
                Hit(knockback);
                if (liftBlocks > 0) Lift(target, liftBlocks);
            }
        }
        if (elapsed >= attackDurationMs)
        {
            if (attackAnim != null) entity.AnimManager.StopAnimation(attackAnim);
            attackStartMs = -1;
            lastAttackMs = entity.World.ElapsedMilliseconds;
        }
    }

    /// <summary>
    /// The Mangled's tendril: whoever it takes is pulled up into the dark, a block at a time over most of a second, as
    /// far as the open air above allows; then let go. (A player's movement is their own client's, so it is done in
    /// short teleports.)
    /// </summary>
    private void Lift(Entity who, float blocks)
    {
        IBlockAccessor ba = entity.World.BlockAccessor;
        var at = new BlockPos(0);
        int x = (int)Math.Floor(who.Pos.X), z = (int)Math.Floor(who.Pos.Z), y0 = (int)Math.Floor(who.Pos.Y);
        int room = 0;
        while (room < blocks && Senses.Open(ba, at.Set(x, y0 + 2 + room, z))) room++;
        int steps = Math.Min(room, (int)blocks);
        if (steps <= 0) return;
        double startY = who.Pos.Y;
        Log("lifts {0} {1} blocks", who.Code, steps);
        for (int i = 1; i <= steps; i++)
        {
            int step = i;
            entity.World.RegisterCallback(_ =>
            {
                if (!who.Alive) return;
                who.TeleportToDouble(who.Pos.X, startY + step, who.Pos.Z);
            }, 90 * i);
        }
    }

    /// <summary>How far apart the two bodies are (centre to centre, less half of each one's width).</summary>
    private double Gap(Entity other) =>
        entity.Pos.DistanceTo(other.Pos) - (entity.SelectionBox.XSize + other.SelectionBox.XSize) / 2;

    private void Hit(float knock)
    {
        float scaled = damage * damageMul * (float)director.Setting.Damage * GlobalConstants.CreatureDamageModifier;
        if (scaled <= 0) return;
        target.ReceiveDamage(new DamageSource
        {
            Source = EnumDamageSource.Entity,
            SourceEntity = entity,
            Type = damageType,
            DamageTier = damageTier + tierBonus,
            KnockbackStrength = knock,
        }, scaled);
        director.NoteCloseCall(target);
        Log("hit {0} for {1:0.0}", target.Code, scaled);
    }

    /// <summary>
    /// A Duller's grab: an arm through the wall at someone passing close by on the other side. It drags them a step
    /// towards the wall, then the Duller is gone.
    /// </summary>
    private bool TryGrab(double distance)
    {
        if (IsCreative(target) || menace.Passive || respectsAlmond && Protected(target)) return false;
        double dy = Math.Abs(target.Pos.Y - entity.Pos.Y);
        if (entity.Pos.XYZ.HorizontalSquareDistanceTo(target.Pos.X, target.Pos.Z) > 2.6 * 2.6 || dy > 1.5) return false;
        if (Senses.ClearLine(entity.World, Senses.Centre(entity), Senses.Centre(target))) return false;
        if (grabSound != null) PlaySound(grabSound);
        PlasterDust(Senses.Centre(entity), Senses.Centre(target));
        if (stealChance > 0 && entity.World.Rand.NextDouble() < stealChance && Steal(target)) { }
        else Hit(-1.6f);
        Kind = Encounter.Leave;
        return true;
    }

    /// <summary>Where an arm comes through a wall, the plaster puffs out on the far side: dust at the first solid block between the two.</summary>
    private void PlasterDust(Vec3d from, Vec3d to)
    {
        IBlockAccessor ba = entity.World.BlockAccessor;
        var at = new BlockPos(0);
        double length = from.DistanceTo(to);
        for (double d = 0.3; d < length; d += 0.25)
        {
            double t = d / length;
            at.Set((int)Math.Floor(from.X + (to.X - from.X) * t), (int)Math.Floor(from.Y + (to.Y - from.Y) * t), (int)Math.Floor(from.Z + (to.Z - from.Z) * t));
            if (Senses.Open(ba, at)) continue;
            var dust = new SimpleParticleProperties(18, 26, ColorUtil.ToRgba(200, 196, 188, 176),
                new Vec3d(at.X, at.Y, at.Z), new Vec3d(at.X + 1, at.Y + 1, at.Z + 1),
                new Vec3f(-0.6f, -0.1f, -0.6f), new Vec3f(0.6f, 0.5f, 0.6f), 1.6f, 0.25f, 0.3f, 0.7f, EnumParticleModel.Quad);
            dust.SelfPropelled = true;
            entity.World.SpawnParticles(dust);
            return;
        }
    }

    /// <summary>
    /// A Duller's theft: the hand closes on something in the hotbar and takes it back through the wall. It lies where
    /// the Duller goes (dropped when it despawns or dies), for whoever can find the room on the other side.
    /// </summary>
    private bool Steal(Entity who)
    {
        if (who is not EntityPlayer { Player: { } player }) return false;
        IInventory hotbar = player.InventoryManager.GetHotbarInventory();
        if (hotbar == null) return false;
        var full = new System.Collections.Generic.List<ItemSlot>();
        foreach (ItemSlot slot in hotbar) if (!slot.Empty && slot is not ItemSlotBackpack) full.Add(slot);
        if (full.Count == 0) return false;
        ItemSlot taken = full[entity.World.Rand.Next(full.Count)];
        ItemStack stack = taken.TakeOutWhole();
        taken.MarkDirty();
        entity.Attributes.SetItemstack(EntityBehaviorMenace.StolenKey, stack);
        Log("stole {0}", stack.Collectible.Code);
        return true;
    }

    // ================= Movement =================

    /// <summary>
    /// Somewhere around the target to watch them from: about halfway into the distance band, on standable floor,
    /// out of the light for things that need the dark and out of sight for things that hide. The one nearest this
    /// entity wins.
    /// </summary>
    private Vec3d StalkPoint()
    {
        Random rand = entity.World.Rand;
        double radius = (stalkMin + stalkMax) / 2;
        Vec3d best = null;
        double bestScore = double.MaxValue;
        double baseAngle = Math.Atan2(entity.Pos.Z - target.Pos.Z, entity.Pos.X - target.Pos.X);
        Vec3d eyes = Senses.Eyes(target);
        for (int i = 0; i < 10; i++)
        {
            double angle = baseAngle + (rand.NextDouble() - 0.5) * Math.PI * (i < 5 ? 0.8 : 2);
            int x = (int)Math.Floor(target.Pos.X + Math.Cos(angle) * radius), z = (int)Math.Floor(target.Pos.Z + Math.Sin(angle) * radius);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(target.Pos.Y), z, 2, 4);
            if (y == int.MinValue) continue;
            var point = new Vec3d(x + 0.5, y, z + 0.5);
            if (lightBound && LitHere(point.AddCopy(0, 1, 0))) continue;
            if (fearsFire && Wards.Warded(entity.World, point)) continue;
            double score = point.DistanceTo(entity.Pos.XYZ);
            if (prefersHidden && Senses.ClearLine(entity.World, eyes, point.AddCopy(0, 1.4, 0))) score += 30;
            if (score < bestScore)
            {
                bestScore = score;
                best = point;
            }
        }
        return best;
    }

    /// <summary>Set on rats put down for the Screaming: they cross the way ahead at a run, after something.</summary>
    public const string FrenzyKey = "backrooms:frenzy";

    /// <summary>A spot a few steps to one side, across the line between the target and this entity.</summary>
    private Vec3d CrossingPoint(double reach = 5)
    {
        double dx = entity.Pos.X - target.Pos.X, dz = entity.Pos.Z - target.Pos.Z, length = Math.Sqrt(dx * dx + dz * dz);
        if (length < 1e-3) return null;
        double side = entity.World.Rand.NextDouble() < 0.5 ? 1 : -1;
        for (int i = 0; i < 4; i++)
        {
            double step = reach + entity.World.Rand.NextDouble() * 3;
            int x = (int)Math.Floor(entity.Pos.X - dz / length * step * side), z = (int)Math.Floor(entity.Pos.Z + dx / length * step * side);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 2, 2);
            if (y == int.MinValue) { side = -side; continue; }
            var point = new Vec3d(x + 0.5, y, z + 0.5);
            if (lightBound && LitHere(point.AddCopy(0, 1, 0))) { side = -side; continue; }
            return point;
        }
        return null;
    }

    /// <summary>A point a short way from this entity towards another, at chest height.</summary>
    private Vec3d NextStepTowards(Vec3d to, double step)
    {
        double dx = to.X - entity.Pos.X, dz = to.Z - entity.Pos.Z, length = Math.Sqrt(dx * dx + dz * dz);
        if (length < step) return Senses.Centre(entity);
        return new Vec3d(entity.Pos.X + dx / length * step, entity.Pos.Y + 1, entity.Pos.Z + dz / length * step);
    }

    private void MoveAwayFrom(Vec3d from, double distance, float speed)
    {
        Random rand = entity.World.Rand;
        double away = Math.Atan2(entity.Pos.Z - from.Z, entity.Pos.X - from.X);
        for (int i = 0; i < 8; i++)
        {
            double angle = away + (rand.NextDouble() - 0.5) * (i < 4 ? 1.2 : 3);
            int x = (int)Math.Floor(entity.Pos.X + Math.Cos(angle) * distance), z = (int)Math.Floor(entity.Pos.Z + Math.Sin(angle) * distance);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 2, 5);
            if (y == int.MinValue) continue;
            var point = new Vec3d(x + 0.5, y, z + 0.5);
            if (lightBound && LitHere(point.AddCopy(0, 1, 0)) && i < 6) continue;
            Go(point, speed, 1);
            return;
        }
        // Nowhere better: back straight off
        Go(entity.Pos.XYZ.Add(Math.Cos(away) * 4, 0, Math.Sin(away) * 4), speed, 1, async: false, straight: true);
    }

    private void Go(Vec3d to, float speed, float within, bool async = true, bool straight = false)
    {
        lastPathMs = entity.World.ElapsedMilliseconds;
        SetMotion(speed >= runSpeed * 0.75f ? Motion.Run : Motion.Walk);
        // (The traverser keeps the point it is given and steers it; it must not be one this task goes on changing)
        to = to.Clone();
        speed *= speedMul;
        if (straight) pathTraverser.WalkTowards(to, speed, within, OnArrived, OnStuck);
        else if (async) pathTraverser.NavigateTo_Async(to, speed, within, OnArrived, OnStuck, OnNoPath, 2500, 1);
        else
        {
            // A search still pending would be taken for this one's answer
            pathTraverser.Stop();
            pathTraverser.NavigateTo(to, speed, within, OnArrived, OnStuck, OnNoPath, false, 2000, 1);
        }
    }

    /// <summary>Stops where it is and plays an animation through, for so long.</summary>
    private void Hold(string animation, int ms)
    {
        Stop();
        entity.AnimManager.StartAnimation(animation);
        holdUntilMs = entity.World.ElapsedMilliseconds + ms;
    }

    private void Stop()
    {
        pathTraverser.Stop();
        SetMotion(Motion.Still);
    }

    private void OnArrived()
    {
        SetMotion(Motion.Still);
        if (crossing) crossed = true;
    }

    private void OnStuck()
    {
        SetMotion(Motion.Still);
        if (crossing) crossed = true;
    }

    private void OnNoPath()
    {
        Stop();
        // Can't get there (a closed door, a wall): a hunter goes back to watching for a while, a stalker tries elsewhere
        noPathUntilMs = entity.World.ElapsedMilliseconds + 4000;
        if (Kind == Encounter.Hunt) Kind = Encounter.Stalk;
        plannedAt = null;
    }

    private bool NoPathLately => entity.World.ElapsedMilliseconds < noPathUntilMs;

    private void SetMotion(Motion next)
    {
        if (next == motion) return;
        if (motion == Motion.Walk && walkAnim != null) entity.AnimManager.StopAnimation(walkAnim);
        if (motion == Motion.Run && runAnim != null) entity.AnimManager.StopAnimation(runAnim);
        motion = next;
        if (motion == Motion.Walk && walkAnim != null) entity.AnimManager.StartAnimation(walkAnim);
        if (motion == Motion.Run && runAnim != null) entity.AnimManager.StartAnimation(runAnim);
    }

    private void TurnTowards(Vec3d point, float dt)
    {
        float desired = (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float step = 4f * dt;
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -step, step)) % GameMath.TWOPI;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
        if (attackStartMs >= 0 && attackAnim != null) entity.AnimManager.StopAnimation(attackAnim);
        attackStartMs = -1;
    }

    // ================= Senses =================

    private bool LitHere(Vec3d pos)
    {
        var carriers = entity.World.GetEntitiesAround(pos, 20, 8, e => e is EntityAgent && Senses.HeldLight(e) > 0);
        return Senses.LightAt(entity.World, pos, carriers) >= Senses.LitLevel;
    }

    /// <summary>Whether Almond Water, drunk in the last five minutes, keeps a Duller off someone.</summary>
    private static bool Protected(Entity target) => AlmondWater.Protects(target) || AlmondWater.Near(target.World, target.Pos.XYZ);

    private static bool IsCreative(Entity target) =>
        target is EntityPlayer player && player.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator;

    private float HealthFraction()
    {
        var health = entity.GetBehavior<EntityBehaviorHealth>();
        return health == null || health.MaxHealth <= 0 ? 1 : health.Health / health.MaxHealth;
    }

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null || menace.Immortal) return;
        Entity cause = source.GetCauseEntity();
        if (cause is not EntityAgent) return;
        lastHurtByTargetMs = entity.World.ElapsedMilliseconds;
        if (coward)
        {
            Kind = Encounter.Leave;
            return;
        }
        if (!retaliates) return;
        // Turning on whoever hurt it, even a wanderer that meant no harm
        menace.Target = cause;
        menace.Passive = false;
        if (Kind != Encounter.Leave) Kind = Encounter.Hunt;
    }

    // ================= Sounds and packs =================

    /// <summary>Mimics: from out of sight, now and then, a voice (a cough, a cry of pain, a whisper).</summary>
    private void PlayVoice(float dt, double distance)
    {
        if (voices.Length == 0 || distance > 32) return;
        nextVoice -= dt;
        if (nextVoice > 0) return;
        nextVoice = 15 + (float)entity.World.Rand.NextDouble() * 25;
        if (target is EntityAgent viewer && Senses.Sees(viewer, entity, 48)) return;
        PlaySound(voices[entity.World.Rand.Next(voices.Length)]);
    }

    private void PlaySound(AssetLocation sound)
    {
        entity.World.PlaySoundAt(sound, entity.Pos.X, entity.Pos.Y + 1, entity.Pos.Z, null, true, cryRange);
    }

    /// <summary>A pack hunts together: the rest of it, put down for the same person, joins in.</summary>
    private void RallyPack()
    {
        long owner = EntityBehaviorMenace.OwnerOf(entity);
        foreach (Entity other in entity.World.GetEntitiesAround(entity.Pos.XYZ, 20, 8, e => e != entity && e.Alive && e.Code == entity.Code))
        {
            var behavior = other.GetBehavior<EntityBehaviorMenace>();
            if (behavior == null || EntityBehaviorMenace.OwnerOf(other) != owner || behavior.Kind is not (Encounter.Stalk or Encounter.Glimpse)) continue;
            other.Attributes.SetBool(EntityBehaviorMenace.RalliedKey, true);
            behavior.Kind = Encounter.Hunt;
        }
    }

    private void Log(string format, params object[] args)
    {
        if (director?.Logging != true || entity.Api is not ICoreServerAPI sapi) return;
        sapi.Logger.Notification("[backrooms] {0} #{1} at {2:0},{3:0},{4:0}: {5}", entity.Code.Path, entity.EntityId, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, string.Format(format, args));
    }
}
