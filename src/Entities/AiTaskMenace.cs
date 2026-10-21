using System;
using System.Collections.Generic;
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
/// <item>Investigate: heard something; walks to it and stands looking about (entities with a <c>senses</c> profile).</item>
/// <item>Search: lost its prey; goes to where it last believed them to be and sweeps round about.</item>
/// <item>Leave: runs off, to be despawned out of sight.</item>
/// </list>
/// An entity whose config has a <c>senses</c> object works from a <see cref="Belief"/> (what it saw, heard or sensed of
/// its target) rather than the target's true position; one without it knows where its target is, as it always did.
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
    private readonly bool lightBound, fearsFire, grabsThroughWalls, respectsAlmond, avoidsLight, slowedByLight, coward, retaliates, prefersHidden;
    /// <summary>The gaze block: frozen while stared at and not running (then gone after six seconds), and a nerve spent under a stare (see <see cref="StaredDown"/>).</summary>
    private readonly bool gazeHolds, hasNerve;
    private readonly float gazeNerveMin, gazeNerveMax;
    /// <summary>What it perceives (null: it knows where its target is), and the perception-driven extras.</summary>
    private readonly SenseProfile senses;
    private readonly bool glimpseTurnsToStalk, growlBeforeCharge, barks, drawnToLight, huntsOnSight;
    private readonly int growlMs;
    private readonly float investigateSeconds, searchSeconds, retaliateSeconds, huntBarkSeconds;
    private readonly int[] huntBarkLevels;
    private readonly string lookAnim;
    private readonly AssetLocation barkSound;
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
    private float think, watchedFor, heldFor, runningFor, walkingFor, nextVoice = 10, nextGrowl = 4;
    // When the hunt began, when it last drew blood, and until when it will not turn to the hunt again (see Hunt)
    private long huntSinceMs = -1, lastBloodMs, calmUntilMs;
    // Whether this hunt was started by being struck (a fight someone picked) rather than by a runner
    private bool huntProvoked;
    /// <summary>
    /// Turning on the target (see <c>turnsWhenCornered</c>, <c>turnsWhenChased</c>): the hunt is provoked and the target
    /// kept in mind (a grudge) while it lasts. The seconds the target has been close in a row, and the seconds spent chased.
    /// </summary>
    private readonly bool turnsWhenCornered, turnsWhenChased;
    private readonly float corneredRange, corneredSeconds, chaseRange, chaseSeconds;
    private bool turnedOnTarget;
    private float corneredFor, chasedFor;
    private double lastChaseDistance = -1;
    private double patienceMs = HuntPatienceSeconds * 1000;

    /// <summary>
    /// Seconds a hunt goes on without drawing blood before it is given up (plus a quarter minute at the bottom, by
    /// danger); and how long after that it will not turn to the hunt again. Nothing chases for ever: something as
    /// fast as a sprint would otherwise never be shaken off.
    /// </summary>
    private const double HuntPatienceSeconds = 20, CalmSeconds = 60;

    /// <summary>The longest a hunt in the Lobby lasts (see <see cref="huntsInLobby"/>).</summary>
    private const long LobbyHuntMs = 25_000;

    /// <summary>The light in hand (a torch is 14, a candle 7) that slows what is slowed by light.</summary>
    private const int TorchLight = 10;

    /// <summary>How long (seconds, in all) a glimpse must have seen its target before it turns to a stalk (see <c>glimpseTurnsToStalk</c>).</summary>
    private const float GlimpseSeenSeconds = 2;

    /// <summary>The loudness of a noise not made by its target that is worth going to see.</summary>
    private const double InvestigateLoudness = 0.3;

    /// <summary>How sure of where its prey is it must be to turn to the hunt.</summary>
    private const double HuntConfidence = 0.3;

    /// <summary>Within this many blocks it has arrived; the least it takes to repath an idle traverser; how long after reaching where they were, with nothing, it gives up the hunt for a search.</summary>
    private const double ArriveWithin = 2.5;
    private const long RepathMs = 600, ArrivedLostMs = 2500, TravelCapMs = 20_000, MinBudgetMs = 15_000;
    /// <summary>A hunting pack barks twice as often within this many blocks of what it hunts.</summary>
    private const double HuntBarkClose = 8;
    /// <summary>How sure it is of where they are when it is first put down for them (it was sent there), and how far a light's edge is looked for.</summary>
    private const double SeedConfidence = 0.8;
    private const int EdgeReach = 40;

    /// <summary>
    /// Opens doors (the Skin-Stealer: it wears a person, and has their hands). Hunting someone it cannot reach, out
    /// towards the edge of a level or worse, it goes to the nearest closed door near them, knocks, waits, and opens
    /// it. A door barred from the inside it only knocks on; a fire keeps it from coming near at all.
    /// </summary>
    private readonly bool opensDoors;
    // The door it is making for, where it stands to open it, when it knocked, and until when it will not look again
    private BlockPos doorAt;
    private Vec3d doorFront;
    private long knockedAtMs = -1, noDoorUntilMs;
    private MenaceBand huntBand;
    private const int DoorSearch = 10;
    private const long KnockWaitMs = 2200, DoorRetryMs = 20_000;
    private static readonly AssetLocation KnockSound = new("backrooms:sounds/entity/knock");
    private static readonly BlockFacing[] DoorAxes = { BlockFacing.NORTH, BlockFacing.EAST };
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

    // ---- Perception, investigating, searching ----
    private Perception.Result seen = new(Contact.None, 0, null, null, null);
    private long investigateAgainMs, investigateStartMs, investigateEndMs, lastInvestigatedNoise, searchEndMs, pointStartMs, lookUntilMs;
    private Vec3d investigateAt;
    private bool investigateArrived, arrived, pathFailed, looking, lookAnimOn, sawTarget, holdStops, searchBegun, pointArrived;
    private float lookBaseYaw, lookPhase, glimpseSeenFor, nextBark;
    private List<Vec3d> searchPoints;
    private int searchIndex;
    /// <summary>Retaliation (see <see cref="OnEntityHurt"/>): when it last turned on a new target, and when it last hit one.</summary>
    private long retaliationStartMs = -1, lastHitMs = -1, nextTrackMs;
    /// <summary>What it was (and whether passive) before it first turned on a retaliation target, to go back to.</summary>
    private Encounter kindBeforeRetaliation = Encounter.Stalk;
    private bool passiveBeforeRetaliation;
    /// <summary>A hunt the director put down: until when (and how often) its belief is refreshed with a head start.</summary>
    private bool sentHunt;
    private long nextSentReseedMs, nextShareMs, nextPackCheckMs, noEdgeUntilMs, edgeComputedMs;
    private bool packNear = true;
    private readonly float sentHuntSeconds, sentHuntError;

    // ---- The AI overhaul's second batch (README 6.1); every key is optional and off by default ----
    /// <summary>The speed it runs from what faces it (a Duller's flight: 1.3 times a sprint); the run speed when not given.</summary>
    private readonly float fleeSpeed;
    /// <summary>A kill feeds it for this many in-game hours, and sends it away (a Skin-Stealer: fed, it is docile).</summary>
    private readonly bool feedsOnKill;
    private readonly float fedHours;
    /// <summary>A hit of this much damage or more stuns it (0: never) for stunSeconds, with a cooldown; the animation it plays meanwhile.</summary>
    private readonly float stunDamage, stunSeconds, stunCooldownSeconds;
    private readonly string stunAnim;
    private long stunReadyMs;
    /// <summary>How long after a grab a hard-to-catch entity can be hurt (a Duller: 1.5 s).</summary>
    private readonly float catchWindowSeconds;
    /// <summary>Its speed by look (the texture index): a Wretch in its early stage is slower, a far-gone one faster. Read when it first thinks.</summary>
    private readonly float[] lookSpeeds;
    private float lookSpeed = 1;
    /// <summary>Set on a rat that bit because it was cornered: it bites once, then goes back to being a scavenger.</summary>
    public const string CorneredKey = "backrooms:cornered";

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
        bool staredDown = taskConfig["staredDown"].AsBool(false);
        gazeHolds = taskConfig["gazeHolds"].AsBool(lightBound);
        gazeNerveMin = taskConfig["gazeNerveMin"].AsFloat(staredDown ? 4 : 0);
        gazeNerveMax = Math.Max(gazeNerveMin, taskConfig["gazeNerveMax"].AsFloat(staredDown ? 8 : 0));
        hasNerve = gazeNerveMax > 0;
        stealChance = taskConfig["stealChance"].AsFloat(0);
        liftBlocks = taskConfig["liftBlocks"].AsFloat(0);
        emergeAnim = Anim(taskConfig["emergeAnimation"].AsString(null));
        emergeMs = taskConfig["emergeMs"].AsInt(0);
        huntAnim = Anim(taskConfig["huntAnimation"].AsString(null));
        huntAnimMs = taskConfig["huntAnimationMs"].AsInt(0);
        huntsInLobby = taskConfig["huntsInLobby"].AsBool(false);
        turnsWhenCornered = taskConfig["turnsWhenCornered"].AsBool(false);
        corneredRange = taskConfig["corneredRange"].AsFloat(4);
        corneredSeconds = taskConfig["corneredSeconds"].AsFloat(1.5f);
        turnsWhenChased = taskConfig["turnsWhenChased"].AsBool(false);
        chaseRange = taskConfig["chaseRange"].AsFloat(16);
        chaseSeconds = taskConfig["chaseSeconds"].AsFloat(10);
        opensDoors = taskConfig["opensDoors"].AsBool(false);
        senses = SenseProfile.Parse(taskConfig["senses"]);
        glimpseTurnsToStalk = taskConfig["glimpseTurnsToStalk"].AsBool(false);
        growlBeforeCharge = taskConfig["growlBeforeCharge"].AsBool(false);
        growlMs = taskConfig["growlMs"].AsInt(900);
        barks = taskConfig["barks"].AsBool(false);
        barkSound = Sound(taskConfig["barkSound"].AsString(null)) ?? stalkSound;
        huntBarkSeconds = taskConfig["huntBarkSeconds"].AsFloat(0);
        huntBarkLevels = taskConfig["huntBarkLevels"].AsArray(Array.Empty<int>());
        drawnToLight = taskConfig["drawnToLight"].AsBool(false);
        huntsOnSight = taskConfig["huntsOnSight"].AsBool(false);
        investigateSeconds = taskConfig["investigateSeconds"].AsFloat(8);
        searchSeconds = taskConfig["searchSeconds"].AsFloat(10);
        retaliateSeconds = taskConfig["retaliateSeconds"].AsFloat(60);
        lookAnim = Anim(taskConfig["lookAnimation"].AsString(null));
        sentHuntSeconds = taskConfig["sentHuntSeconds"].AsFloat(10);
        sentHuntError = taskConfig["sentHuntError"].AsFloat(3);
        fleeSpeed = taskConfig["fleeSpeed"].AsFloat(runSpeed);
        feedsOnKill = taskConfig["feedsOnKill"].AsBool(false);
        fedHours = taskConfig["fedHours"].AsFloat(24);
        stunDamage = taskConfig["stunDamage"].AsFloat(0);
        stunSeconds = taskConfig["stunSeconds"].AsFloat(1.2f);
        stunCooldownSeconds = taskConfig["stunCooldownSeconds"].AsFloat(8);
        stunAnim = Anim(taskConfig["stunAnimation"].AsString("hurt"));
        catchWindowSeconds = taskConfig["catchWindowSeconds"].AsFloat(0);
        lookSpeeds = taskConfig["lookSpeeds"].AsArray(Array.Empty<float>());
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

    private Belief belief => menace.Belief;

    /// <summary>Where it believes its target is: what it last saw, heard or sensed of them, or (with no senses) where they are.</summary>
    private Vec3d Believed => senses != null && belief.Pos != null ? belief.Pos : target.Pos.XYZ;

    /// <summary>How sure it is of that now (1 for an entity without senses).</summary>
    private double Confidence(long now) => senses == null ? 1 : belief.ConfidenceAt(now, senses.MemorySeconds);

    private bool Perceives => senses != null;

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null) return false;
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        Encounter kind = menace.Kind;
        return kind is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Leave or Encounter.Investigate or Encounter.Search;
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
            patienceMs = (HuntPatienceSeconds + 15 * d) * 1000;
            int look = entity.WatchedAttributes.GetInt("textureIndex", 0);
            if (look >= 0 && look < lookSpeeds.Length) lookSpeed = lookSpeeds[look];
        }
        if (emergeAnim != null && !emerged)
        {
            emerged = true;
            Hold(emergeAnim, emergeMs);
        }
        Log("starts: {0}", menace.Kind);
        if (Perceives) Log("senses: {0}", senses);
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
            if (target != null) TurnTowards(FacePoint(), dt);
            return true;
        }
        if (holdStops)
        {
            holdStops = false;
            entity.AnimManager.StopAnimation("growl");
        }

        if (kind != lastKind)
        {
            OnKindChanged(kind);
            lastKind = kind;
            if (entity.World.ElapsedMilliseconds < holdUntilMs) return true;
        }

        think -= dt;
        if (motion == Motion.Still && target != null && kind != Encounter.Leave) TurnTowards(FacePoint(), dt);
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

        long now = entity.World.ElapsedMilliseconds;
        if (EndRetaliation(now)) return true;
        kind = Kind;
        if (kind == Encounter.Leave)
        {
            Leave();
            return true;
        }

        double distance = entity.Pos.DistanceTo(target.Pos);
        MenaceSystem.Assessment a = director.AssessmentOf(target);
        if (Perceives)
        {
            Perceive(kind, now);
            if (now < holdUntilMs) return true;
        }
        if (++thoughts % 10 == 0)
        {
            Log("{0}, {1:0.0} blocks from {2}, {3}{4}", kind, distance, target.Code.Path, motion, pathTraverser.Active ? " (on a path)" : "");
            if (Perceives)
                Log("contact {0}, confidence {1:0.00}{2}, believes {3:0.0} blocks from the truth", seen.Contact, Confidence(now), belief.Vague ? " (vague)" : "", belief.Pos?.DistanceTo(target.Pos.XYZ) ?? -1);
        }

        // Whatever it is doing, it gives up on someone who reaches a sanctuary, and the hurt ones run
        bool provoked = EntityBehaviorFaceling.Provoked(entity);
        if (a.Band == MenaceBand.Safe && kind != Encounter.Glimpse && !provoked && !huntProvoked || retreatBelow > 0 && HealthFraction() < retreatBelow)
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

        if (target is EntityAgent agent && Senses.Running(agent) && (!Perceives || seen.Contact != Contact.None))
        {
            runningFor += 0.3f;
            walkingFor = 0;
        }
        else
        {
            runningFor = 0;
            walkingFor += 0.3f;
        }

        if (kind is Encounter.Glimpse or Encounter.Stalk && (turnsWhenCornered || turnsWhenChased) && TryTurnOnTarget(kind, distance, a, now)) return true;

        switch (kind)
        {
            case Encounter.Glimpse:
                Glimpse(distance, a, now);
                break;
            case Encounter.Stalk:
                Stalk(distance, a, now);
                break;
            case Encounter.Hunt:
                Hunt(distance, a);
                break;
            case Encounter.Investigate:
                Investigate(distance, a, now);
                break;
            case Encounter.Search:
                Search(distance, a, now);
                break;
        }
        PlayVoice(dt: 0.3f, distance);
        return true;
    }

    private void OnKindChanged(Encounter kind)
    {
        Encounter before = lastKind;
        plannedAt = chasing = null;
        doorAt = null;
        lastPathMs = 0;
        StopLook();
        if (kind != Encounter.Investigate) investigateArrived = false;
        if (kind == Encounter.Search) searchBegun = false;
        if (kind == Encounter.Hunt) nextBark = huntBarkSeconds;
        // (Counters start afresh whenever the hunt ends, and a turn on the target ends with it)
        corneredFor = chasedFor = 0;
        lastChaseDistance = -1;
        if (kind != Encounter.Hunt) turnedOnTarget = false;
        sentHunt = false;
        if (kind == Encounter.Stalk && before != Encounter.Hunt && stalkSound != null && entity.World.Rand.NextDouble() < 0.6) PlaySound(stalkSound);
        if (kind == Encounter.Hunt)
        {
            huntSinceMs = lastBloodMs = entity.World.ElapsedMilliseconds;
            huntProvoked = lastHurtByTargetMs > 0 && huntSinceMs - lastHurtByTargetMs < 2000 || retaliationStartMs >= 0 || turnedOnTarget;
            // (A hunt the director put down, rather than one that came of following, investigating, searching or a blow)
            sentHunt = before == (Encounter)(-1) && !huntProvoked && retaliationStartMs < 0;
            nextSentReseedMs = huntSinceMs + SentReseedMs;
        }
        if (kind == Encounter.Hunt && !announcedHunt)
        {
            announcedHunt = true;
            if (!entity.Attributes.GetBool(EntityBehaviorMenace.RalliedKey))
            {
                if (huntSound != null)
                {
                    PlaySound(huntSound);
                    director.RaiseNoise(entity.Pos.XYZ, MenaceSystem.CryLoudness, "cry", entity);
                }
                RallyPack();
            }
            if (huntAnim != null) Hold(huntAnim, huntAnimMs);
        }
        // The warning: a growl before it comes (not when it was struck into it, nor out of a search)
        if (kind == Encounter.Hunt && growlBeforeCharge && before is Encounter.Stalk or Encounter.Investigate && !huntProvoked
            && !(huntAnim != null && announcedHunt && entity.World.ElapsedMilliseconds < holdUntilMs))
        {
            Log("growls before it charges ({0} ms)", growlMs);
            Hold("growl", growlMs, true);
        }
    }

    // ================= Encounters =================

    private void Glimpse(double distance, MenaceSystem.Assessment a, long now)
    {
        // Hostile the moment they see a human: a glimpse that has watched them for a while, out towards the edge, follows
        if (glimpseTurnsToStalk && seen.Contact == Contact.Seen) glimpseSeenFor += 0.3f;
        if (glimpseTurnsToStalk && glimpseSeenFor > GlimpseSeenSeconds && a.Band >= MenaceBand.Approach && !menace.Passive)
        {
            Log("has watched them long enough: it follows");
            Kind = Encounter.Stalk;
            return;
        }
        if (glimpseTurnsToStalk && a.Band >= MenaceBand.Approach && TryInvestigate(a, now)) return;
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
        if (Starer(64, 10) != null)
        {
            watchedFor += 0.3f;
            if (watchedFor > 3) Kind = Encounter.Leave;
        }
        else watchedFor = Math.Max(0, watchedFor - 0.15f);
    }

    /// <summary>
    /// The Bacteria's patience: a target that stays within <c>corneredRange</c> for <c>corneredSeconds</c> (it could not
    /// get away) gets a lunge at once; one that keeps closing on it within <c>chaseRange</c> for <c>chaseSeconds</c>
    /// (decaying at half the rate otherwise, a stalker only) gets a howl and the hunt. Either way the hunt is provoked,
    /// as a blow makes it (no Lobby call-off, no stare-down) and it keeps track of them. Never creative, passive,
    /// in a sanctuary, or lately given up on.
    /// </summary>
    private bool TryTurnOnTarget(Encounter kind, double distance, MenaceSystem.Assessment a, long now)
    {
        if (menace.Passive || menace.Harmless || IsCreative(target) || a.Band == MenaceBand.Safe || NoPathLately || now < calmUntilMs)
        {
            corneredFor = chasedFor = 0;
            lastChaseDistance = -1;
            return false;
        }
        bool cornered = false, chased = false;
        if (turnsWhenCornered)
        {
            corneredFor = distance <= corneredRange ? corneredFor + 0.3f : 0;
            cornered = corneredFor >= corneredSeconds;
        }
        if (turnsWhenChased && kind == Encounter.Stalk)
        {
            bool closing = lastChaseDistance >= 0 && distance < lastChaseDistance - 0.05
                || distance < stalkMin - 1 && (motion != Motion.Still || pathTraverser.Active);
            lastChaseDistance = distance;
            chasedFor = distance <= chaseRange && closing ? chasedFor + 0.3f : Math.Max(0, chasedFor - 0.15f);
            chased = chasedFor >= chaseSeconds;
        }
        if (!cornered && !chased) return false;
        if (Perceives && Confidence(now) <= HuntConfidence) return false;

        Log(cornered ? "cornered: it lunges" : "chased too long: it turns");
        bool announced = announcedHunt;
        turnedOnTarget = true;
        lastBloodMs = now;
        Kind = Encounter.Hunt;
        if (cornered)
        {
            // No time for a howl: it is on them
            if (huntAnim != null) entity.AnimManager.StopAnimation(huntAnim);
            holdUntilMs = 0;
            Stop();
        }
        else if (announced)
        {
            // (Turned on before, the first-time howl has gone: it howls again now)
            if (huntSound != null) PlaySound(huntSound);
            if (huntAnim != null) Hold(huntAnim, huntAnimMs);
        }
        return true;
    }

    private void Stalk(double distance, MenaceSystem.Assessment a, long now)
    {
        // How far it is from where it believes them to be (what it keeps its distance by)
        double believedDistance = Perceives ? entity.Pos.DistanceTo(Believed) : distance;
        Entity starer = Starer(48);
        bool stared = starer != null;

        // A Duller confronted runs; a Smiler held in someone's gaze, who neither runs nor looks away, freezes and at last withdraws
        if (stared && coward && entity.Pos.DistanceTo(starer.Pos) < 16)
        {
            Kind = Encounter.Leave;
            return;
        }
        if (gazeHolds && stared && runningFor == 0)
        {
            Stop();
            watchedFor += 0.3f;
            if (watchedFor > 6) Kind = Encounter.Leave;
            return;
        }
        watchedFor = Math.Max(0, watchedFor - 0.1f);

        if (grabsThroughWalls && TryGrab(distance)) return;
        if (hasNerve && StaredDown(distance)) return;

        if (ShouldTurnToHunt(distance, a))
        {
            Kind = Encounter.Hunt;
            return;
        }
        if (TryInvestigate(a, now)) return;
        if (drawnToLight && Perceives && DrawnToEdge(now)) return;

        // Keep the distance: close in when too far off, fall back when too near, otherwise wait and watch
        if (believedDistance > stalkMax || believedDistance < stalkMin - 1)
        {
            bool replan = plannedAt == null || plannedAt.DistanceTo(Believed) > 3 || !pathTraverser.Active;
            if (replan && entity.World.ElapsedMilliseconds - lastPathMs > 1200)
            {
                Vec3d point = StalkPoint();
                if (point != null)
                {
                    plannedAt = Believed.Clone();
                    Go(point, believedDistance > stalkMax + 10 ? runSpeed * 0.8f : walkSpeed, 1);
                }
            }
        }
        else if (motion != Motion.Still && !pathTraverser.Active) Stop();
        else if (motion != Motion.Still && believedDistance < (stalkMin + stalkMax) / 2) Stop();

        StalkSounds();
    }

    private void StalkSounds()
    {
        if (stalkSound == null) return;
        nextGrowl -= 0.3f;
        if (nextGrowl <= 0)
        {
            nextGrowl = 8 + (float)entity.World.Rand.NextDouble() * 12;
            if (entity.World.Rand.NextDouble() < 0.4) PlaySound(stalkSound);
        }
    }

    /// <summary>Whether a stalker loses patience: the person it follows runs, comes apart, or stands alone in the dark at the edge.</summary>
    private bool ShouldTurnToHunt(double distance, MenaceSystem.Assessment a)
    {
        if (!CanHunt(distance, a)) return false;
        if (retaliationStartMs >= 0 && !lightBound) return true;
        double believedDistance = Perceives ? entity.Pos.DistanceTo(Believed) : distance;
        Random rand = entity.World.Rand;
        if (lightBound)
        {
            // Smilers come only for those in the dark
            if (!a.Dark) return false;
            return runningFor > 1 || (!Perceives || seen.Contact != Contact.None) && Senses.Stability(target) < 0.4 || a.Band == MenaceBand.Threshold && rand.NextDouble() < 0.08 * 0.3;
        }
        if (avoidsLight && Senses.HeldLight(target) >= 10) return false;
        // Hostile on sight: a Hound that sees them close by comes
        if (huntsOnSight && seen.Contact == Contact.Seen && believedDistance < stalkMax + 6) return true;
        // Running is what gives you away: anything following within earshot gives chase
        if (runningFor > 1.5 && believedDistance < 28) return true;
        if (Senses.Stability(target) < 0.4) return (!Perceives || seen.Contact != Contact.None) && rand.NextDouble() < 0.2 * 0.3 * turnMul;
        return (!Perceives || seen.Contact != Contact.None) && a.Value >= 0.8 && rand.NextDouble() < 0.04 * 0.3 * turnMul;
    }

    /// <summary>
    /// Whether nothing rules the hunt out: not passive, in a band that allows it, not lately given up, not creative,
    /// not in the Lobby, not a Duller's protected one, and (with senses) it knows well enough where they are.
    /// </summary>
    private bool CanHunt(double distance, MenaceSystem.Assessment a)
    {
        // Struck, it fights: no band, Lobby or calm rules hold it back from whoever hurt it (only a way through, and knowing where they are)
        if (retaliationStartMs >= 0 && !menace.Passive && !menace.Harmless && !NoPathLately && !IsCreative(target))
            return !Perceives || Confidence(entity.World.ElapsedMilliseconds) > HuntConfidence;
        if (menace.Passive || menace.Harmless || a.Band < MenaceBand.Approach || NoPathLately) return false;
        // Lately given up on them (see Hunt)
        if (entity.World.ElapsedMilliseconds < calmUntilMs) return false;
        if (IsCreative(target)) return false;
        // The Lobby is empty, as the lore has it: what watches there never hunts, but in the Red Rooms
        if (a.Level == 0 && !a.Worst && !(huntsInLobby && a.Band == MenaceBand.Threshold && runningFor > 1.5 && distance < 20)) return false;
        if (respectsAlmond && Protected(target)) return false;
        return !Perceives || Confidence(entity.World.ElapsedMilliseconds) > HuntConfidence;
    }

    private void Hunt(double distance, MenaceSystem.Assessment a)
    {
        if (menace.Passive || menace.Harmless || IsCreative(target))
        {
            Kind = Encounter.Stalk;
            return;
        }
        if (distance > giveUpAt)
        {
            Kind = Encounter.Leave;
            return;
        }
        long now = entity.World.ElapsedMilliseconds;
        // In the Lobby, where nothing hunts but what a runner near the way out sets off (the Bacteria), the hunt is
        // a fright: it lasts only while they are still running out there, and one blow is enough. Back towards the
        // heart, a few seconds at a walk, a wound, or long enough, and it sinks back into the mould. (Struck, it fights:
        // a fight someone picks is only bounded by the patience below)
        if (huntsInLobby && a.Level == 0 && !a.Worst && !huntProvoked
            && (a.Band != MenaceBand.Threshold || walkingFor > 4 || lastBloodMs > huntSinceMs || now - huntSinceMs > LobbyHuntMs))
        {
            CallOffHunt(leave: true);
            return;
        }
        // Anywhere, a hunt that has drawn no blood for a while is given up: back to following, and not hunting again soon
        if (now - lastBloodMs > patienceMs)
        {
            CallOffHunt(leave: false);
            return;
        }
        // Lost them (nothing seen, heard or sensed for as long as it remembers), or got to where they were and found nobody: search
        Vec3d goal = Believed;
        double believedDistance = entity.Pos.DistanceTo(goal);
        if (Perceives && (belief.Lost(now, senses.MemorySeconds) || believedDistance < ArriveWithin && seen.Contact == Contact.None && now - belief.AtMs > ArrivedLostMs))
        {
            Log("has lost them");
            // (Lost for good: the search must not take the stale belief for a fresh contact)
            belief.Strength = 0;
            Stop();
            Kind = Encounter.Search;
            return;
        }
        // The pack barks as it runs them down (Level 3's packs), twice as often when close
        if (huntBarkSeconds > 0 && Array.IndexOf(huntBarkLevels, a.Level) >= 0)
        {
            nextBark -= believedDistance < HuntBarkClose ? 0.6f : 0.3f;
            if (nextBark <= 0)
            {
                nextBark = huntBarkSeconds;
                Bark();
            }
        }
        // A coward faced runs, even mid-hunt
        if (coward && Starer(48) is { } facing && entity.Pos.DistanceTo(facing.Pos) < 16)
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

        // (Not one it was struck into: a Hound that is hit fights, whoever stares)
        if (hasNerve && !huntProvoked && StaredDown(distance)) return;

        // A Smiler held in someone's gaze, who neither runs nor looks away, freezes
        if (gazeHolds && runningFor == 0 && Starer(48) != null)
        {
            Stop();
            watchedFor += 0.3f;
            if (watchedFor > 6) Kind = Encounter.Leave;
            return;
        }
        watchedFor = Math.Max(0, watchedFor - 0.1f);

        // What holds it back: a Smiler stops dead at the edge of the light (the next step would be lit), the rest at
        // the edge of a fire's reach, and rats keep clear of a carried light. Held back too long, it gives up.
        bool heldBack = lightBound && LitHere(NextStepTowards(goal, 1.5))
            || fearsFire && Wards.Warded(entity.World, goal, Wards.Radius + 1)
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
        huntBand = a.Band;
        if (doorAt != null)
        {
            WorkDoor();
            return;
        }
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
        // (A torch or a lantern in hand slows it; a candle, or the lit halls themselves, do not)
        if (slowedByLight && Senses.HeldLight(target) >= TorchLight) speed *= 0.7f;
        // The Lobby's fright is a little short of a sprint; struck, it comes in earnest
        if (huntsInLobby && a.Level == 0 && !a.Worst && !huntProvoked) speed *= 0.92f;
        // A new path when there is none or the prey has moved on (as vanilla's seek does); otherwise steer the old one at it
        // (It goes to where it believes them to be: there, and nobody, it waits for the search above)
        if (Perceives && believedDistance < ArriveWithin)
        {
            Stop();
            return;
        }
        bool moved = chasing == null || chasing.SquareDistanceTo(goal) >= 9;
        long sincePath = entity.World.ElapsedMilliseconds - lastPathMs;
        if (!pathTraverser.Active && sincePath > RepathMs || moved && sincePath > 750)
        {
            chasing = goal.Clone();
            // (Asynchronous: the traverser is not active until a later tick, so the repath is rate limited, not gated on it)
            Go(chasing, speed, attackRange * 0.6f + (entity.SelectionBox.XSize + target.SelectionBox.XSize) / 2);
        }
        else if (pathTraverser.Active && pathTraverser.CurrentTarget != null)
        {
            pathTraverser.CurrentTarget.X = goal.X;
            pathTraverser.CurrentTarget.Y = goal.Y;
            pathTraverser.CurrentTarget.Z = goal.Z;
        }
    }

    /// <summary>
    /// A Hound met with a steady stare (the lore's one sure thing about them): it stops, lowers its head and growls, and
    /// backs off a step. It holds only a few seconds, all told, for each Hound: then its nerve goes the other way and
    /// it comes at whoever stared. Returns whether it is held for now.
    /// </summary>
    private bool StaredDown(double distance)
    {
        if (nerve < 0) nerve = gazeNerveMin + (float)entity.World.Rand.NextDouble() * (gazeNerveMax - gazeNerveMin);
        // (Whoever stares, its target or someone with them: it backs off from them)
        Entity viewer = nerve > 0 ? Starer(16, 10) : null;
        bool stared = viewer is EntityPlayer && !IsCreative(viewer) && entity.Pos.DistanceTo(viewer.Pos) < 12;
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
            if (!menace.Passive) Kind = Perceives && Confidence(entity.World.ElapsedMilliseconds) <= HuntConfidence ? Encounter.Stalk : Encounter.Hunt;
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
        if (entity.Pos.DistanceTo(viewer.Pos) < 6 && !pathTraverser.Active && entity.World.ElapsedMilliseconds - lastPathMs > 1500) MoveAwayFrom(viewer.Pos.XYZ, 3, walkSpeed);
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
            MoveAwayFrom(target.Pos.XYZ, 24, fleeSpeed);
        }
    }

    // ================= Perception =================

    /// <summary>The way it faces when standing: looking about while it investigates or searches, else towards where it believes its target is.</summary>
    private Vec3d FacePoint()
    {
        if (!looking) return Believed;
        double yaw = lookBaseYaw + Math.Sin(entity.World.ElapsedMilliseconds / 1100.0 + lookPhase) * LookSweep;
        return entity.Pos.XYZ.Add(Math.Sin(yaw) * 4, 0, Math.Cos(yaw) * 4);
    }

    /// <summary>How far (radians) either side of where it was facing it sweeps its gaze when looking about.</summary>
    private const double LookSweep = 1.2;

    /// <summary>
    /// One look about: what it sees, senses or hears of its target, and what the pack knows. The first sight of them
    /// is announced (a bark, a growl).
    /// </summary>
    private void Perceive(Encounter kind, long now)
    {
        if (kind is not (Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Investigate or Encounter.Search)) return;
        // Put down for them, it was sent to about where they are
        if (belief.AtMs < 0) belief.Take(target.Pos.XYZ, SeedConfidence, Contact.Sensed, now, senses.MemorySeconds);
        seen = Perception.Perceive(entity, target, senses, belief, director.Noises, now);
        // Struck, it knows where whoever hurt it is while they stay near (a grudge, bounded by retaliateSeconds): it does not lose them in a corner of the eye
        if (kind == Encounter.Hunt && huntProvoked && (retaliationStartMs >= 0 || turnedOnTarget) && entity.Pos.DistanceTo(target.Pos) < GrudgeRange)
            belief.Take(target.Pos.XYZ, 1, Contact.Sensed, now, senses.MemorySeconds);
        ShareBelief(now);
        if (kind == Encounter.Stalk) Track(now);
        if (kind == Encounter.Hunt && sentHunt) HeadStart(now);
        if (seen.Contact == Contact.Seen && !sawTarget)
        {
            sawTarget = true;
            Log("sees its target");
            if (barks) Bark();
            if (growlBeforeCharge && kind == Encounter.Stalk)
            {
                Log("growls at the sight of them ({0} ms)", growlMs);
                Hold("growl", growlMs, true);
            }
        }
    }

    /// <summary>
    /// Tracking (a stalker only): one that has lost its target, or is hardly sure of them, now and then gets a vague idea
    /// of where they are, off by up to <c>trackError</c> blocks, so it keeps to the area. It is not contact (see <see cref="Belief.Vague"/>).
    /// </summary>
    private void Track(long now)
    {
        if (senses.TrackSeconds <= 0 || now < nextTrackMs || Confidence(now) >= TrackBelow) return;
        nextTrackMs = now + (long)(senses.TrackSeconds * 1000 * (0.75 + entity.World.Rand.NextDouble() * 0.5));
        SetVague(target, now);
        Log("has a vague idea where they are");
    }

    /// <summary>A vague belief (see <see cref="Belief.Vague"/>) of where someone is, off by up to <c>trackError</c> blocks.</summary>
    private void SetVague(Entity who, long now)
    {
        Random rand = entity.World.Rand;
        double angle = rand.NextDouble() * Math.PI * 2, off = rand.NextDouble() * senses.TrackError;
        belief.Pos = who.Pos.XYZ.Add(Math.Cos(angle) * off, 0, Math.Sin(angle) * off);
        belief.AtMs = now;
        belief.Strength = TrackBelow;
        belief.Source = Contact.Heard;
        belief.HeardInARow = 0;
        belief.Vague = true;
    }

    /// <summary>
    /// A hunt the director put down closes in for its first <c>sentHuntSeconds</c>: every two seconds its belief is
    /// refreshed to about where the target is (off by up to <c>sentHuntError</c>). After that it is honest.
    /// </summary>
    private void HeadStart(long now)
    {
        if (sentHuntSeconds <= 0 || now - huntSinceMs > sentHuntSeconds * 1000 || now < nextSentReseedMs) return;
        nextSentReseedMs = now + SentReseedMs;
        if (Confidence(now) >= SentHuntBelief) return;
        Random rand = entity.World.Rand;
        double angle = rand.NextDouble() * Math.PI * 2, off = rand.NextDouble() * sentHuntError;
        belief.Pos = target.Pos.XYZ.Add(Math.Cos(angle) * off, 0, Math.Sin(angle) * off);
        belief.AtMs = now;
        belief.Strength = SentHuntBelief;
        belief.Source = Contact.Sensed;
        belief.HeardInARow = 0;
        belief.Vague = false;
        Log("closing in on a sent hunt");
    }

    private const long SentReseedMs = 2000;

    /// <summary>How near (blocks) someone who struck it must stay for it to keep knowing where they are.</summary>
    private const double GrudgeRange = 16;
    private const double SentHuntBelief = 0.7;

    /// <summary>A vague belief's strength, and the confidence below which a stalker gets one: under the hunt's threshold.</summary>
    private const double TrackBelow = 0.25;

    /// <summary>A bark: heard by the pack, which takes up what this one believes.</summary>
    private void Bark()
    {
        if (barkSound != null) PlaySound(barkSound);
        director.RaiseNoise(entity.Pos.XYZ, MenaceSystem.CryLoudness, "bark", entity);
    }

    /// <summary>The pack shares the best belief among them: packmates close by, and those whose bark was heard.</summary>
    private void ShareBelief(long now)
    {
        if (now < nextShareMs) return;
        nextShareMs = now + ShareEveryMs;
        long owner = EntityBehaviorMenace.OwnerOf(entity);
        double memory = senses.MemorySeconds, mine = belief.ConfidenceAt(now, memory);
        void Learn(Entity other)
        {
            var behavior = other.GetBehavior<EntityBehaviorMenace>();
            if (behavior == null || EntityBehaviorMenace.OwnerOf(other) != owner) return;
            Belief theirs = behavior.Belief;
            double theirsNow = theirs.ConfidenceAt(now, memory);
            if (theirs.Pos == null || theirs.Vague || theirsNow <= mine) return;
            belief.Pos = theirs.Pos.Clone();
            belief.AtMs = theirs.AtMs;
            belief.Strength = theirs.Strength;
            belief.Source = theirs.Source;
            belief.Vague = false;
            mine = theirsNow;
        }
        // (Alone at the last look: not asking again for a few seconds)
        if (packNear || now >= nextPackCheckMs)
        {
            Entity[] mates = entity.World.GetEntitiesAround(entity.Pos.XYZ, PackReach, 8, e => e != entity && e.Alive && e.Code == entity.Code);
            packNear = mates.Length > 0;
            nextPackCheckMs = now + PackRecheckMs;
            foreach (Entity other in mates) Learn(other);
        }
        foreach (NoiseEvent noise in director.Noises.Recent(now))
        {
            if (noise.Source != "bark" || noise.Who == entity.EntityId) continue;
            Entity barker = entity.World.GetEntityById(noise.Who);
            if (barker == null || !barker.Alive || barker.Code != entity.Code || barker.Pos.DistanceTo(entity.Pos) > senses.Hearing * noise.Loudness) continue;
            Learn(barker);
        }
    }

    /// <summary>How far a packmate is for the pack to share what it knows.</summary>
    private const float PackReach = 20;

    /// <summary>The pack shares at most this often (ms), and an entity with no packmates near looks again after this long.</summary>
    private const long ShareEveryMs = 1000, PackRecheckMs = 5000;

    /// <summary>
    /// A stalker (or a glimpse that has turned hostile) that hears something, and does not have its eyes on its target,
    /// goes to see what it was. Returns whether it set off.
    /// </summary>
    private bool TryInvestigate(MenaceSystem.Assessment a, long now)
    {
        if (!Perceives || menace.Passive || now < investigateAgainMs || Kind is not (Encounter.Stalk or Encounter.Glimpse)) return false;
        NoiseEvent? noise = null;
        // (Its target's own noise, when it has not just had its eyes on them: it goes to where they were heard)
        if (seen.Contact == Contact.Heard && seen.Noise is { } own && !(belief.Source == Contact.Seen && now - belief.AtMs < RecentSightMs)) noise = own;
        else if (seen.Contact is not (Contact.Seen or Contact.Sensed))
        {
            NoiseEvent? other = Perception.HeardAnything(entity, senses, director.Noises, now);
            if (other is { } n && n.Loudness >= InvestigateLoudness && n.Who != entity.EntityId && n.Who != target.EntityId
                && (n.Id == 0 || n.Id != lastInvestigatedNoise) && !FromPackmate(n)) noise = n;
        }
        if (noise is not { } heard) return false;
        investigateAt = heard.Pos.Clone();
        // Never into the light: a noise in a lit place is gone to as far as the edge of it, or not at all
        if (lightBound && LitHere(heard.Pos.AddCopy(0, 1, 0)))
        {
            investigateAt = FindEdge(heard.Pos, entity.Pos.XYZ, EdgeReach);
            if (investigateAt == null) return false;
        }
        lastInvestigatedNoise = heard.Id;
        investigateStartMs = now;
        investigateArrived = false;
        arrived = pathFailed = false;
        Stop();
        Log("hears {0} at {1:0},{2:0},{3:0}", heard.Source, heard.Pos.X, heard.Pos.Y, heard.Pos.Z);
        Kind = Encounter.Investigate;
        return true;
    }

    /// <summary>How recently (ms) it must have seen its target for it to take no notice of their noise.</summary>
    private const long RecentSightMs = 3000;

    private bool FromPackmate(NoiseEvent noise) => entity.World.GetEntityById(noise.Who) is { } who && who.Code == entity.Code;

    /// <summary>Who stares it down (a coward faced, a gaze that holds, a nerve spent): whether it is held by that for now.</summary>
    private bool GazeBlock(double distance)
    {
        if (coward && Starer(48) is { } facing && entity.Pos.DistanceTo(facing.Pos) < 16)
        {
            Kind = Encounter.Leave;
            return true;
        }
        if (gazeHolds && runningFor == 0 && Starer(48) != null)
        {
            Stop();
            watchedFor += 0.3f;
            if (watchedFor > 6) Kind = Encounter.Leave;
            return true;
        }
        watchedFor = Math.Max(0, watchedFor - 0.1f);
        return hasNerve && StaredDown(distance);
    }

    /// <summary>It has found its target (or its trail) again: the hunt, if the hunt is open to it, else following.</summary>
    private void Spotted(double distance, MenaceSystem.Assessment a)
    {
        Kind = CanHunt(distance, a) && (!lightBound || ShouldTurnToHunt(distance, a)) ? Encounter.Hunt : Encounter.Stalk;
    }

    /// <summary>A length of time in the config's seconds, a little over or under (up to two seconds either way), in ms.</summary>
    private long Duration(float seconds) => (long)(Math.Max(1, seconds + (entity.World.Rand.NextDouble() * 4 - 2)) * 1000);

    private void BeginLook()
    {
        looking = true;
        lookBaseYaw = entity.Pos.Yaw;
        lookPhase = (float)(entity.World.Rand.NextDouble() * Math.PI * 2);
        if (lookAnim != null && !lookAnimOn)
        {
            lookAnimOn = true;
            entity.AnimManager.StartAnimation(lookAnim);
        }
    }

    private void StopLook()
    {
        looking = false;
        if (lookAnimOn && lookAnim != null) entity.AnimManager.StopAnimation(lookAnim);
        lookAnimOn = false;
    }

    // ================= Investigate and Search =================

    /// <summary>Walks to a noise, stands looking about for a while, then goes back to following (or to the hunt, if it sees them there).</summary>
    private void Investigate(double distance, MenaceSystem.Assessment a, long now)
    {
        if (GazeBlock(distance)) return;
        if (seen.Contact == Contact.Seen && Confidence(now) > HuntConfidence)
        {
            Spotted(distance, a);
            return;
        }
        if (!investigateArrived)
        {
            bool there = arrived || pathFailed || entity.Pos.DistanceTo(investigateAt) < ArriveWithin || now - investigateStartMs > TravelCapMs;
            if (!there)
            {
                if (!pathTraverser.Active && now - lastPathMs > 1200) Go(investigateAt, walkSpeed, 1.5f);
                return;
            }
            investigateArrived = true;
            Stop();
            investigateEndMs = now + Duration(investigateSeconds);
            BeginLook();
            return;
        }
        if (now < investigateEndMs) return;
        // Nothing there
        investigateAgainMs = now + ReinvestigateMs;
        StopLook();
        Kind = Encounter.Stalk;
    }

    /// <summary>How long (ms) after one investigation before it goes to see another noise.</summary>
    private const long ReinvestigateMs = 5000;

    /// <summary>
    /// Lost its prey: goes to where it last believed them to be, then sweeps two or three places near it, looking
    /// about, for <c>searchSeconds</c> in all. Finds them again (confidence over the hunt's threshold) and it hunts.
    /// </summary>
    private void Search(double distance, MenaceSystem.Assessment a, long now)
    {
        if (GazeBlock(distance)) return;
        if (seen.Contact != Contact.None && Confidence(now) > HuntConfidence)
        {
            Spotted(distance, a);
            return;
        }
        if (!searchBegun)
        {
            BeginSearch(now);
            if (searchPoints.Count == 0)
            {
                EndSearch();
                return;
            }
        }
        if (now >= searchEndMs)
        {
            EndSearch();
            return;
        }
        Vec3d point = searchPoints[searchIndex];
        if (!pointArrived)
        {
            bool there = arrived || pathFailed || entity.Pos.DistanceTo(point) < ArriveWithin || now - pointStartMs > TravelCapMs;
            if (!there)
            {
                if (!pathTraverser.Active && now - lastPathMs > 1200)
                    Go(point, searchIndex == 0 && entity.Pos.DistanceTo(point) > SearchRunBeyond ? runSpeed * 0.8f : walkSpeed, 1.5f);
                return;
            }
            pointArrived = true;
            Stop();
            lookUntilMs = now + SearchLookMs + (long)(entity.World.Rand.NextDouble() * SearchLookMs);
            BeginLook();
            return;
        }
        if (now >= lookUntilMs && searchIndex < searchPoints.Count - 1)
        {
            searchIndex++;
            pointArrived = arrived = pathFailed = false;
            pointStartMs = now;
            StopLook();
        }
    }

    /// <summary>Beyond this far it runs to where it last believed them to be; how long (ms) it looks about at each point, at least.</summary>
    private const double SearchRunBeyond = 12;
    private const long SearchLookMs = 2500;
    /// <summary>The sweep points round the last believed position: how many (2 or 3), and how far off (blocks).</summary>
    private const int SearchSweepMin = 2, SearchSweepMax = 3;
    private const double SearchRadiusMin = 4, SearchRadiusMax = 8;

    private void BeginSearch(long now)
    {
        searchBegun = true;
        Stop();
        searchPoints = new List<Vec3d>();
        searchIndex = 0;
        pointArrived = arrived = pathFailed = false;
        pointStartMs = now;
        searchEndMs = now + Duration(searchSeconds);
        Random rand = entity.World.Rand;
        Vec3d last = belief.Pos?.Clone() ?? entity.Pos.XYZ;
        bool Usable(Vec3d p) => !(lightBound && LitHere(p.AddCopy(0, 1, 0)));
        int y0 = Senses.FindFloor(entity.World, (int)Math.Floor(last.X), (int)Math.Floor(last.Y), (int)Math.Floor(last.Z), 2, 4);
        var first = new Vec3d(Math.Floor(last.X) + 0.5, y0 == int.MinValue ? last.Y : y0, Math.Floor(last.Z) + 0.5);
        if (Usable(first)) searchPoints.Add(first);
        int sweeps = rand.Next(SearchSweepMin, SearchSweepMax + 1);
        for (int tries = 0; tries < sweeps * 4 && searchPoints.Count < sweeps + 1; tries++)
        {
            double angle = rand.NextDouble() * Math.PI * 2, radius = SearchRadiusMin + rand.NextDouble() * (SearchRadiusMax - SearchRadiusMin);
            int x = (int)Math.Floor(last.X + Math.Cos(angle) * radius), z = (int)Math.Floor(last.Z + Math.Sin(angle) * radius);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(last.Y), z, 2, 4);
            if (y == int.MinValue) continue;
            var point = new Vec3d(x + 0.5, y, z + 0.5);
            if (Usable(point)) searchPoints.Add(point);
        }
        Log("searches {0} places round {1:0},{2:0},{3:0}", searchPoints.Count, last.X, last.Y, last.Z);
    }

    /// <summary>The search is over: back to following if the encounter has time left in it, else gone.</summary>
    private void EndSearch()
    {
        StopLook();
        Log("gives up the search");
        Kind = menace.EncounterLeftMs > MinBudgetMs ? Encounter.Stalk : Encounter.Leave;
    }

    // ================= The edge of the light =================

    /// <summary>
    /// A Smiler that has seen its target standing in light does not step in: it goes to a point just outside the lit
    /// area, between itself and them, and waits there, grinning. Running or a noise brings it there faster. Returns
    /// whether it is doing that (otherwise it stalks as usual).
    /// </summary>
    private bool DrawnToEdge(long now)
    {
        Vec3d at = belief.Pos;
        if (at == null || belief.Source != Contact.Seen || now - belief.AtMs > RecentSightMs * 2 || NoPathLately || now < noEdgeUntilMs) return false;
        if (!LitHere(at.AddCopy(0, 1, 0))) return false;
        // (The edge is worked out at most once a second; found none, it is not looked for again for two)
        if (edgePoint == null || now - edgeComputedMs > EdgeCacheMs || edgeFor.DistanceTo(at) >= 2)
        {
            Vec3d edge = FindEdge(at, entity.Pos.XYZ, EdgeReach);
            edgeComputedMs = now;
            if (edge == null)
            {
                edgePoint = null;
                noEdgeUntilMs = now + NoEdgeWaitMs;
                return false;
            }
            edgePoint = edge;
            edgeFor = at.Clone();
        }
        if (entity.Pos.XYZ.HorizontalSquareDistanceTo(edgePoint.X, edgePoint.Z) < EdgeWithin * EdgeWithin)
        {
            Stop();
            StalkSounds();
            return true;
        }
        if (now - lastPathMs > RepathMs)
        {
            bool urgent = runningFor > 0 || seen.Contact == Contact.Heard;
            Go(edgePoint, urgent ? runSpeed : walkSpeed, 1);
        }
        return true;
    }

    /// <summary>
    /// The first standable, unlit point on the line from one place out towards another (one block at a time, up to the
    /// distance between them or <paramref name="maxSteps"/>), or null.
    /// </summary>
    private Vec3d FindEdge(Vec3d from, Vec3d toward, int maxSteps)
    {
        double dx = toward.X - from.X, dz = toward.Z - from.Z, length = Math.Sqrt(dx * dx + dz * dz);
        if (length < 1e-3) return null;
        for (int i = 1; i <= Math.Min(maxSteps, (int)length + 1); i++)
        {
            int x = (int)Math.Floor(from.X + dx / length * i), z = (int)Math.Floor(from.Z + dz / length * i);
            if (LitHere(new Vec3d(x + 0.5, from.Y + 1, z + 0.5))) continue;
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(from.Y), z, 2, 4);
            if (y == int.MinValue) continue;
            return new Vec3d(x + 0.5, y, z + 0.5);
        }
        return null;
    }

    private const long EdgeCacheMs = 1000, NoEdgeWaitMs = 2000;

    /// <summary>Within this many blocks of the edge point it has arrived.</summary>
    private const double EdgeWithin = 1.5;
    private Vec3d edgePoint, edgeFor;

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
        // (Level 2's rats have lost their teeth along with their fur)
        if (menace.Harmless) return;
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
        director.RaiseNoise(target.Pos.XYZ, MenaceSystem.FightLoudness, "bite", target);
        lastBloodMs = lastHitMs = entity.World.ElapsedMilliseconds;
        Log("hit {0} for {1:0.0}", target.Code, scaled);
        if (feedsOnKill && !target.Alive) Feed();
        // A cornered rat bites once, and is a scavenger again
        if (entity.Attributes.GetBool(CorneredKey))
        {
            entity.Attributes.RemoveAttribute(CorneredKey);
            Log("bit once, cornered: it scatters again");
            Kind = Encounter.Ambient;
        }
    }

    /// <summary>It has killed: fed for a day (a Skin-Stealer is docile then), and it goes.</summary>
    private void Feed()
    {
        menace.Feed(fedHours);
        Log("has fed: docile for {0:0} hours", fedHours);
        Kind = Encounter.Leave;
    }

    /// <summary>Gives up the hunt: gone, or back to following at a distance; either way, no new hunt for a minute.</summary>
    private void CallOffHunt(bool leave)
    {
        calmUntilMs = entity.World.ElapsedMilliseconds + (long)(CalmSeconds * 1000);
        Log("gives up the hunt");
        Stop();
        Kind = leave ? Encounter.Leave : Encounter.Stalk;
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
        // The one moment it can be caught: its arm is out, and the wall is between (a hard-to-catch Duller, see EntityBehaviorMenace)
        if (catchWindowSeconds > 0)
        {
            menace.OpenCatchWindow((long)(catchWindowSeconds * 1000));
            Log("grabbed: can be hurt for {0:0.0} s", catchWindowSeconds);
        }
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
        // (One thing at a time: a second would overwrite the first, and it would be lost)
        if (entity.Attributes.HasAttribute(EntityBehaviorMenace.StolenKey)) return false;
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
        Vec3d centre = Believed;
        double baseAngle = Math.Atan2(entity.Pos.Z - centre.Z, entity.Pos.X - centre.X);
        Vec3d eyes = Senses.Eyes(target);
        for (int i = 0; i < 10; i++)
        {
            double angle = baseAngle + (rand.NextDouble() - 0.5) * Math.PI * (i < 5 ? 0.8 : 2);
            int x = (int)Math.Floor(centre.X + Math.Cos(angle) * radius), z = (int)Math.Floor(centre.Z + Math.Sin(angle) * radius);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(centre.Y), z, 2, 4);
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
        speed *= speedMul * lookSpeed;
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
    private void Hold(string animation, int ms, bool stopsAfter = false)
    {
        Stop();
        entity.AnimManager.StartAnimation(animation);
        holdUntilMs = entity.World.ElapsedMilliseconds + ms;
        holdStops = stopsAfter;
    }

    private void Stop()
    {
        pathTraverser.Stop();
        SetMotion(Motion.Still);
    }

    private void OnArrived()
    {
        SetMotion(Motion.Still);
        arrived = true;
        if (crossing) crossed = true;
    }

    private void OnStuck()
    {
        SetMotion(Motion.Still);
        arrived = true;
        if (crossing) crossed = true;
    }

    private void OnNoPath()
    {
        Stop();
        pathFailed = true;
        // Making for a door it cannot reach either: forget the door, and give up as below
        if (doorAt != null)
        {
            doorAt = null;
            noDoorUntilMs = entity.World.ElapsedMilliseconds + DoorRetryMs;
        }
        // Shut out: something with hands tries the door instead (see opensDoors)
        else if (Kind == Encounter.Hunt && opensDoors && huntBand >= MenaceBand.Approach && FindDoor())
        {
            plannedAt = null;
            return;
        }
        // Can't get there (a closed door, a wall): a hunter goes back to watching for a while, a stalker tries elsewhere
        noPathUntilMs = entity.World.ElapsedMilliseconds + 4000;
        if (Kind == Encounter.Hunt) Kind = Encounter.Stalk;
        plannedAt = null;
    }

    private bool NoPathLately => entity.World.ElapsedMilliseconds < noPathUntilMs;

    // ================= Doors =================

    /// <summary>
    /// The nearest closed door near the target that this entity could open, and the open floor before it on the side
    /// away from the target (which is where it is coming from). Only the game's own doors: our thresholds are not doors
    /// anything opens. Returns whether one was found (and set as <see cref="doorAt"/>).
    /// </summary>
    private bool FindDoor()
    {
        long now = entity.World.ElapsedMilliseconds;
        if (now < noDoorUntilMs) return false;
        noDoorUntilMs = now + 6000; // (a look costs a few thousand block reads: not on every failed path)
        IBlockAccessor ba = entity.World.BlockAccessor;
        BlockPos centre = Believed.AsBlockPos, pos = new(0);
        double best = double.MaxValue;
        for (int dy = -2; dy <= 2; dy++)
            for (int dz = -DoorSearch; dz <= DoorSearch; dz++)
                for (int dx = -DoorSearch; dx <= DoorSearch; dx++)
                {
                    pos.Set(centre.X + dx, centre.Y + dy, centre.Z + dz);
                    if (ba.GetBlock(pos).GetBehavior<BlockBehaviorDoor>() == null) continue;
                    BEBehaviorDoor door = BlockBehaviorDoor.getDoorAt(entity.World, pos);
                    if (door == null || door.Opened || !Openable(door)) continue;
                    BlockPos at = door.Pos;
                    if (FrontOf(at) is not { } front) continue;
                    double d = entity.Pos.SquareDistanceTo(front);
                    if (d >= best) continue;
                    best = d;
                    doorAt = at.Copy();
                    doorFront = front;
                }
        if (doorAt == null) return false;
        knockedAtMs = -1;
        Log("makes for the door at {0}", doorAt);
        return true;
    }

    /// <summary>A door a hand opens without more (not one that only opens by a mechanism, or that breaks when used).</summary>
    private static bool Openable(BEBehaviorDoor door) =>
        door.doorBh?.handopenable != false && (door.Block.Attributes?["breakOnTriggerChance"].AsFloat(0) ?? 0) <= 0;

    /// <summary>Whether a door is barred from the inside.</summary>
    private bool Barred(BlockPos at) => entity.World.BlockAccessor.GetBlockEntity(at)?.GetBehavior<BEBehaviorDoorBarLock>()?.IsLocked == true;

    /// <summary>
    /// The open floor before a door on the side away from the target: across the door one way or the other (both sides
    /// open, as a doorway is walked through, not along), the side further from the target chosen.
    /// </summary>
    private Vec3d FrontOf(BlockPos at)
    {
        IBlockAccessor ba = entity.World.BlockAccessor;
        bool Open(BlockPos p) => ba.GetBlock(p).CollisionBoxes == null && ba.GetBlock(p.UpCopy()).CollisionBoxes == null;
        foreach (BlockFacing facing in DoorAxes)
        {
            BlockPos a = at.AddCopy(facing), b = at.AddCopy(facing.Opposite);
            if (!Open(a) || !Open(b)) continue;
            Vec3d va = new(a.X + 0.5, a.Y, a.Z + 0.5), vb = new(b.X + 0.5, b.Y, b.Z + 0.5);
            Vec3d from = Believed;
            return va.SquareDistanceTo(from) > vb.SquareDistanceTo(from) ? va : vb;
        }
        return null;
    }

    /// <summary>Goes to the door, knocks, waits a moment, and opens it (or, finding it barred, gives up).</summary>
    private void WorkDoor()
    {
        long now = entity.World.ElapsedMilliseconds;
        BEBehaviorDoor door = BlockBehaviorDoor.getDoorAt(entity.World, doorAt);
        if (door == null || door.Opened)
        {
            // Gone, or opened by someone else: on with the hunt
            doorAt = null;
            noPathUntilMs = 0;
            return;
        }
        if (entity.Pos.SquareDistanceTo(doorFront) > 1.6 * 1.6)
        {
            if (!pathTraverser.Active && now - lastPathMs > 1200) Go(doorFront, walkSpeed * 1.4f, 0.8f);
            return;
        }
        Stop();
        if (knockedAtMs < 0)
        {
            knockedAtMs = now;
            entity.World.PlaySoundAt(KnockSound, doorAt.X + 0.5, doorAt.Y + 1, doorAt.Z + 0.5, null, true, 24, 1f);
            return;
        }
        if (now - knockedAtMs < KnockWaitMs) return;
        if (Barred(doorAt))
        {
            // The bar holds: it goes back to watching, and leaves this door alone for a while
            Log("finds the door barred");
            doorAt = null;
            noDoorUntilMs = now + DoorRetryMs;
            noPathUntilMs = now + 4000;
            Kind = Encounter.Stalk;
            return;
        }
        Log("opens the door");
        door.ToggleDoorState(null, true);
        doorAt = null;
        noPathUntilMs = 0;
        lastBloodMs = now; // (the hunt is getting somewhere: its patience starts again)
    }

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
        // (A Hound stared down when the task ends must not go on growling)
        if (growling || holdStops) entity.AnimManager.StopAnimation("growl");
        growling = holdStops = false;
        StopLook();
    }

    // ================= Senses =================

    private bool LitHere(Vec3d pos)
    {
        var carriers = entity.World.GetEntitiesAround(pos, 20, 8, e => e is EntityAgent && Senses.HeldLight(e) > 0);
        return Senses.LightAt(entity.World, pos, carriers) >= Senses.LitLevel;
    }

    /// <summary>
    /// Whoever is looking straight at this entity and can see it (within a few degrees, for a stare): the one it was
    /// put down for, or else any other player within the range. A stare from someone it was not put down for counts
    /// the same, so two people together can each hold a Hound or a Smiler. Null if nobody is looking.
    /// </summary>
    private Entity Starer(double range, double lookAngle = 14)
    {
        Vec3d centre = Senses.Centre(entity);
        if (target is EntityAgent viewer && Senses.LooksAt(viewer, centre, lookAngle) && Senses.Sees(viewer, entity, range)) return target;
        foreach (Entity other in entity.World.GetEntitiesAround(entity.Pos.XYZ, (float)range, (float)range, e => e != target && e is EntityPlayer p && p.Alive && p.Player?.WorldData.CurrentGameMode != EnumGameMode.Spectator))
        {
            if (Senses.LooksAt(other, centre, lookAngle) && Senses.Sees(other, entity, range)) return other;
        }
        return null;
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
        if (stunDamage > 0 && damage >= stunDamage) TryStun();
        // A rat without teeth only runs
        if (menace.Harmless)
        {
            Kind = Encounter.Leave;
            return;
        }
        if (coward)
        {
            Kind = Encounter.Leave;
            return;
        }
        if (!retaliates) return;
        // Turning on whoever hurt it, even a wanderer that meant no harm: for a while (see EndRetaliation)
        long now = entity.World.ElapsedMilliseconds;
        if (!entity.Attributes.HasAttribute(FirstOwnerKey) && EntityBehaviorMenace.OwnerOf(entity) >= 0)
            entity.Attributes.SetLong(FirstOwnerKey, EntityBehaviorMenace.OwnerOf(entity));
        // (Whoever it is, the owner too: a fed Skin-Stealer or a scavenger rat struck by its own owner goes back to what it was after retaliateSeconds)
        if (retaliationStartMs < 0)
        {
            kindBeforeRetaliation = Kind;
            passiveBeforeRetaliation = menace.Passive;
        }
        retaliationStartMs = now;
        // Struck, it fights: no Lobby call-off, no stare-down, no sanctuary, and patience starts afresh
        huntProvoked = true;
        lastBloodMs = now;
        if (menace.Target?.EntityId != cause.EntityId) ResetBelief();
        menace.Target = cause;
        if (Perceives) belief.Take(cause.Pos.XYZ, 1, Contact.Sensed, now, senses.MemorySeconds);
        menace.Passive = false;
        if (Kind != Encounter.Leave) Kind = Encounter.Hunt;
    }

    /// <summary>
    /// A hard blow (<c>stunDamage</c> or more) holds it where it stands, flinching, for <c>stunSeconds</c>, and not again
    /// for <c>stunCooldownSeconds</c>: the Skin-Stealer's opening. An attack in progress is broken off.
    /// </summary>
    private void TryStun()
    {
        long now = entity.World.ElapsedMilliseconds;
        if (now < stunReadyMs) return;
        stunReadyMs = now + (long)(stunCooldownSeconds * 1000);
        if (attackStartMs >= 0)
        {
            if (attackAnim != null) entity.AnimManager.StopAnimation(attackAnim);
            attackStartMs = -1;
            lastAttackMs = now;
        }
        Log("stunned for {0:0.0} s", stunSeconds);
        Hold(stunAnim ?? "hurt", (int)(stunSeconds * 1000));
    }

    /// <summary>Set once, on the entity, to whoever it was put down for before it first turned on anyone else.</summary>
    public const string FirstOwnerKey = "backrooms:firstOwner";

    private void ResetBelief()
    {
        if (menace != null) belief.Forget();
        sawTarget = false;
        glimpseSeenFor = 0;
    }

    /// <summary>
    /// A struck entity turns on whoever struck it, but not for ever: after <c>retaliateSeconds</c> without having hit
    /// them it goes back to the one it was put down for (if they are alive and near), or leaves. Returns whether it did.
    /// </summary>
    private bool EndRetaliation(long now)
    {
        if (retaliateSeconds <= 0 || retaliationStartMs < 0) return false;
        long first = entity.Attributes.GetLong(FirstOwnerKey, -1);
        if (first < 0 || target.EntityId == first && kindBeforeRetaliation != Encounter.Ambient)
        {
            retaliationStartMs = -1;
            return false;
        }
        if (now - Math.Max(retaliationStartMs, lastHitMs) < retaliateSeconds * 1000) return false;
        retaliationStartMs = -1;
        Entity owner = entity.World.GetEntityById(first);
        Stop();
        if (kindBeforeRetaliation == Encounter.Ambient)
        {
            // It was going about its own business (a provoked Faceling, a city Hound): back to that
            Log("is done with {0}: calm again", target.Code.Path);
            if (owner != null && owner.Alive) menace.Target = target = owner;
            ResetBelief();
            menace.Passive = passiveBeforeRetaliation;
            Kind = Encounter.Ambient;
        }
        else if (owner != null && owner.Alive && owner.Pos.DistanceTo(entity.Pos) < giveUpAt)
        {
            Log("is done with {0}: back to following {1}", target.Code.Path, owner.Code.Path);
            menace.Target = target = owner;
            ResetBelief();
            // (It does not know where the owner is: only a vague idea, as a tracker has)
            if (Perceives) SetVague(owner, now);
            Kind = Encounter.Stalk;
        }
        else
        {
            Log("is done with {0}", target.Code.Path);
            Kind = Encounter.Leave;
        }
        return true;
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
