using System;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>Registers the Neighborhood Watch's AI task and its eye (client) with the game, on both sides.</summary>
public class WatchClasses : ModSystem
{
    public override double ExecuteOrder() => 0.05;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntityBehaviorClass("backrooms-watcheye", typeof(EntityBehaviorWatchEye));
        AiTaskRegistry.Register<AiTaskWatch>("backrooms-watch");
    }
}

/// <summary>
/// The Neighborhood Watch (Entity 96, Level 9): a giant eyeball on six long legs, walking the Suburbs' streets. It
/// has no hearing and no smell (Wikidot): it finds people by sight, and by touch close up. So:
/// <list type="bullet">
/// <item>It sees someone in the dark only within a dozen blocks, someone in light (a torch or lantern in hand, a
/// lit room, a working street lamp, a fire) within forty; a crouch shrinks both. Its gaze is a cone ahead of the eye,
/// wider while it stands sweeping the street. Glass does not stop it: it looks in through the windows.</item>
/// <item>Being seen is not being caught: it takes a moment to be sure (meeting its eye makes that quicker), and the
/// eye turns toward whoever it is making out, which is the warning. Then it stares, and comes, fast.</item>
/// <item>It chases only what it can see. Out of its sight for a few seconds, it goes to where it last saw you and
/// searches there; then, as often as not, it makes as if to leave and waits a little way off, watching (the lore's
/// "it will attempt to trick you"). The rest of the Watch near by come to search the same place.</item>
/// <item>It is too tall for any door. Someone it has seen indoors it watches through the glass, tapping, which wears
/// on the mind, until they come out or it gives up.</item>
/// </list>
/// Its encounter (see <see cref="EntityBehaviorMenace"/>): a glimpse stands sweeping the street; a stalker patrols
/// round the person it was put down for, stopping to look; a hunt (or anything it spots) is the chase.
/// </summary>
public class AiTaskWatch : AiTaskBase
{
    private enum Mode { Patrol, Chase, Search, Feint, Peer }
    private enum Motion { Still, Walk, Run }

    /// <summary>Synced to clients: the entity id the eye is turned on (-1 for none); see <see cref="WatchEyeController"/>.</summary>
    public const string WatchOnKey = "backrooms:watchOn";

    // ---- Config ----
    private readonly float walkSpeed, runSpeed, scanHalfAngle, fearRange;
    /// <summary>
    /// What it sees by (the shared model, see <see cref="Perception"/>; glass does not stop it): the cone of its gaze as it
    /// walks, as it stands sweeping the street, and the wide one while it chases or peers (it keeps its eye on them).
    /// </summary>
    private readonly SenseProfile senses, scanSenses, chaseSenses;
    private readonly float noticeSeconds, loseSeconds, searchSeconds, feintSeconds, peerSeconds;
    private readonly float damage, knockback, attackRange, retreatBelow, cryRange;
    private readonly int damageTier, attackDurationMs, damageAtMs, attackCooldownMs, stareMs;
    private readonly EnumDamageType damageType;
    private readonly string walkAnim, runAnim, attackAnim, scanAnim, stareAnim, peerAnim;
    private readonly AssetLocation noticeSound, attackSound, tapSound;

    // ---- State ----
    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private Mode mode = Mode.Patrol;
    private Motion motion;
    private string pose;
    private long modeSinceMs, holdUntilMs, attackStartMs = -1, lastAttackMs, lastPathMs, noPathUntilMs, nextTapMs, lastSeenMs, poseUntilMs;
    private bool damageDone, arrived, dangerRead;
    private float think, notice;
    private Entity watched, noticing;
    private Vec3d lastSeen, goal, chasing;
    private float speedMul = 1, damageMul = 1, cooldownMul = 1;
    private int tierBonus;
    private Encounter lastKind = (Encounter)(-1);

    public AiTaskWatch(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.016f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.044f);
        // (Someone in the dark within a dozen blocks, in light within forty; a crouch shrinks both to 0.6; no hearing, no smell)
        senses = SenseProfile.Parse(taskConfig["senses"]) ?? new SenseProfile
        {
            SightLit = 40, SightDim = 12, SightDark = 12, SightCone = 70, Touch = 2.5f, SneakFactor = 0.6f, Hearing = 0, HearsRunning = false, Glass = true,
        };
        scanHalfAngle = taskConfig["scanHalfAngle"].AsFloat(100);
        fearRange = taskConfig["fearRange"].AsFloat(24);
        scanSenses = senses.With("sightCone=" + scanHalfAngle.ToString(System.Globalization.CultureInfo.InvariantCulture), out _);
        chaseSenses = senses.With("sightCone=150", out _);
        noticeSeconds = taskConfig["noticeSeconds"].AsFloat(1.6f);
        loseSeconds = taskConfig["loseSeconds"].AsFloat(3);
        searchSeconds = taskConfig["searchSeconds"].AsFloat(14);
        feintSeconds = taskConfig["feintSeconds"].AsFloat(16);
        peerSeconds = taskConfig["peerSeconds"].AsFloat(40);
        damage = taskConfig["damage"].AsFloat(6);
        knockback = taskConfig["knockback"].AsFloat(0.8f);
        attackRange = taskConfig["attackRange"].AsFloat(1.6f);
        retreatBelow = taskConfig["retreatBelow"].AsFloat(0.3f);
        cryRange = taskConfig["soundRange"].AsFloat(32);
        damageTier = taskConfig["damageTier"].AsInt(2);
        attackDurationMs = taskConfig["attackDurationMs"].AsInt(900);
        damageAtMs = taskConfig["damageAtMs"].AsInt(500);
        attackCooldownMs = taskConfig["attackCooldownMs"].AsInt(1900);
        stareMs = taskConfig["stareMs"].AsInt(1100);
        damageType = Enum.TryParse(taskConfig["damageType"].AsString("BluntAttack"), true, out EnumDamageType t) ? t : EnumDamageType.BluntAttack;
        walkAnim = taskConfig["walkAnimation"].AsString("walk");
        runAnim = taskConfig["runAnimation"].AsString("run");
        attackAnim = taskConfig["attackAnimation"].AsString("attack");
        scanAnim = taskConfig["scanAnimation"].AsString("scan");
        stareAnim = taskConfig["stareAnimation"].AsString("stare");
        peerAnim = taskConfig["peerAnimation"].AsString("peer");
        noticeSound = Sound(taskConfig["noticeSound"].AsString(null));
        attackSound = Sound(taskConfig["attackSound"].AsString(null));
        tapSound = Sound(taskConfig["tapSound"].AsString(null));
    }

    private static AssetLocation Sound(string code) => code == null ? null : AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/");

    private long Now => entity.World.ElapsedMilliseconds;

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
        return menace.Kind is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Leave;
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
        }
        think = 0;
        motion = Motion.Still;
        attackStartMs = -1;
        lastKind = (Encounter)(-1);
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || menace == null) return false;
        Encounter kind = Kind;
        if (kind == Encounter.Ambient) return false;
        Frighten();

        if (attackStartMs >= 0)
        {
            ContinueAttack();
            return true;
        }
        // Staring: only the body turns, to keep the eye on them
        if (Now < holdUntilMs)
        {
            if (watched != null) TurnTowards(watched.Pos.XYZ, dt);
            return true;
        }
        if (kind != lastKind)
        {
            OnKindChanged(kind);
            lastKind = kind;
        }

        // Standing (scanning, peering, waiting), it turns to what it is looking at
        if (motion == Motion.Still && goal != null && kind != Encounter.Leave) TurnTowards(goal, dt);

        think -= dt;
        if (think > 0) return true;
        const float step = 0.25f;
        think = step;

        if (kind == Encounter.Leave)
        {
            Leave();
            return true;
        }

        Entity target = menace.Target;
        if (target == null || !target.Alive)
        {
            Kind = Encounter.Leave;
            return true;
        }
        MenaceSystem.Assessment a = director.AssessmentOf(target);
        bool hot = mode is Mode.Chase or Mode.Peer;
        if (a.Band == MenaceBand.Safe && !hot || retreatBelow > 0 && HealthFraction() < retreatBelow || entity.Pos.DistanceTo(target.Pos) > 72)
        {
            Kind = Encounter.Leave;
            return true;
        }

        Sense(step);
        switch (mode)
        {
            case Mode.Patrol: Patrol(kind, target); break;
            case Mode.Chase: Chase(); break;
            case Mode.Search: Search(); break;
            case Mode.Feint: Feint(); break;
            case Mode.Peer: Peer(step); break;
        }
        return true;
    }

    /// <summary>What fears the Watch ("Deathmoths, Smilers, Skin-Stealers, and Hounds all seem to fear these creatures", Wikidot).</summary>
    private static readonly System.Collections.Generic.HashSet<string> Feared = new() { "hound", "smiler", "skinstealer", "deathmoth-male", "deathmoth-female" };

    private long nextFearMs;

    /// <summary>
    /// Once a second: whichever of the creatures that fear the Watch is out hunting, stalking or watching within
    /// <c>fearRange</c> blocks of it turns tail and leaves (the ambient ones are left to their business).
    /// </summary>
    private void Frighten()
    {
        long now = Now;
        if (now < nextFearMs || fearRange <= 0) return;
        nextFearMs = now + 1000;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, fearRange, fearRange, e => e != entity && e.Alive && e.Code?.Domain == "backrooms" && Feared.Contains(e.Code.Path)))
        {
            if (e.GetBehavior<EntityBehaviorMenace>() is not { } other || other.Kind is Encounter.Ambient or Encounter.Leave) continue;
            Log("frightens {0} #{1} ({2:0} blocks)", e.Code.Path, e.EntityId, e.Pos.DistanceTo(entity.Pos));
            other.Kind = Encounter.Leave;
        }
    }

    private void OnKindChanged(Encounter kind)
    {
        // A hunt the director sent: it has not seen anyone yet, but searches round where they are
        if (kind == Encounter.Hunt && mode == Mode.Patrol && menace.Target is { } target)
        {
            Random rand = entity.World.Rand;
            BeginSearch(target.Pos.XYZ.Add((rand.NextDouble() - 0.5) * 12, 0, (rand.NextDouble() - 0.5) * 12), hurry: false);
        }
        if (kind == Encounter.Leave)
        {
            SetPose(null);
            SetWatchOn(null);
        }
    }

    // ================= Sight =================

    /// <summary>Who it is making out, and how sure it is getting; spots them when sure.</summary>
    private void Sense(float dt)
    {
        if (mode is Mode.Chase or Mode.Peer) return; // (the chase keeps its own eye on whoever it chases)
        bool alert = mode is Mode.Search or Mode.Feint;
        SenseProfile gaze = pose == scanAnim ? scanSenses : senses;
        Entity best = null;
        double bestV = 0;
        foreach (Entity who in Candidates())
        {
            double v = Visibility(who, gaze, out _);
            if (v > bestV) { bestV = v; best = who; }
        }
        if (best != null && (noticing == null || noticing == best || bestV > 0.5))
        {
            noticing = best;
            notice += (float)(bestV * dt / noticeSeconds * (alert ? 1.6 : 1));
            // The eye turns to whoever it is making out: the warning
            if (notice > 0.3f) SetWatchOn(best);
        }
        else
        {
            notice = Math.Max(0, notice - dt / (noticeSeconds * 2));
            if (notice <= 0.05f)
            {
                noticing = null;
                if (mode == Mode.Patrol) SetWatchOn(null);
            }
        }
        if (notice >= 1 && noticing != null) Spot(noticing);

        // (Every few seconds with the entity log on: what it makes of the one it was put down for)
        if (director?.Logging == true && ++thoughts % 12 == 0 && menace.Target is { } t)
        {
            Vec3d eye = Senses.Eyes(entity);
            float toward = (float)Math.Atan2(t.Pos.X - entity.Pos.X, t.Pos.Z - entity.Pos.Z);
            Log("{0}: {1:0.0} blocks, {2:0} degrees off its gaze (it looks {3:0} wide), {4}, line of sight {5}, notice {6:0.00}",
                mode, eye.DistanceTo(Senses.Centre(t)), Math.Abs(GameMath.AngleRadDistance(entity.Pos.Yaw, toward)) * GameMath.RAD2DEG, gaze.SightCone,
                Lit(t) ? "lit" : "in the dark", SightLine(entity.World, eye, Senses.Centre(t)) ? "clear" : "blocked", notice);
        }
    }

    private int thoughts;

    /// <summary>Everyone it could be watching: the players near, and a console test's straw dummy.</summary>
    private System.Collections.Generic.IEnumerable<Entity> Candidates()
    {
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, senses.SightLit + 2, 16, e => e is EntityPlayer p && p.Alive))
            if (!IsCreative(e)) yield return e;
        Entity target = menace.Target;
        if (target != null && target.Alive && target.WatchedAttributes.GetBool("backrooms:testTarget")) yield return target;
    }

    /// <summary>
    /// How plainly it sees someone (0: not at all): <see cref="Perception.Sight"/> (the range for the light they are in,
    /// the cone of its gaze, nothing but glass between; closer, plainer; a crouch shrinks it), made plainer by being lit
    /// and by meeting its eye. Within touch it knows them whatever the light. The light is its own reckoning: only lamps,
    /// windows, fires and what they carry, not the sky.
    /// </summary>
    private double Visibility(Entity who, SenseProfile gaze, out bool throughGlass)
    {
        throughGlass = false;
        if (Perception.Sensed(entity, who, gaze) == "touch") return 4;
        bool lit = Lit(who);
        double plain = Perception.Sight(entity, who, gaze, out _, lit ? Senses.LitLevel : 0);
        if (plain <= 0) return 0;
        Vec3d eye = Senses.Eyes(entity);
        throughGlass = !Senses.ClearLine(entity.World, eye, Senses.Centre(who));
        double v = lit ? 1.5 : 1.0;
        if (Senses.Sneaking(who)) v *= 0.6;
        // Meeting its eye: "The Ones That Gaze Into Souls"
        if (Senses.LooksAt(who, eye, 10)) v += 1;
        return v * plain;
    }

    /// <summary>Whether someone stands in light it can see them by: what they carry, or the lamps, windows and fires about them (not the sky).</summary>
    private static bool Lit(Entity who)
    {
        if (Senses.HeldLight(who) >= Senses.LitLevel) return true;
        if (Senses.LightsOut) return false;
        Vec3d eyes = Senses.Eyes(who);
        var pos = new BlockPos((int)Math.Floor(eyes.X), (int)Math.Floor(eyes.Y), (int)Math.Floor(eyes.Z));
        return who.World.BlockAccessor.GetLightLevel(pos, EnumLightLevelType.OnlyBlockLight) >= Senses.LitLevel;
    }

    /// <summary>Whether nothing but glass (windows) lies on the line between two points.</summary>
    public static bool SightLine(IWorldAccessor world, Vec3d from, Vec3d to)
    {
        BlockSelection blockSel = null;
        EntitySelection entitySel = null;
        world.RayTraceForSelection(from, to, ref blockSel, ref entitySel,
            (pos, block) => block.CollisionBoxes != null && block.CollisionBoxes.Length > 0 && block.Replaceable < 6000 && block.BlockMaterial != EnumBlockMaterial.Glass,
            e => false);
        return blockSel == null;
    }

    /// <summary>It has seen someone: it stares, and the chase is on; the rest of the Watch near by come to look.</summary>
    private void Spot(Entity who)
    {
        notice = 0;
        noticing = null;
        watched = who;
        lastSeen = who.Pos.XYZ;
        lastSeenMs = Now;
        if (menace.Target != who) menace.Target = who;
        Log("spots {0}", who.Code);
        SetWatchOn(who);
        SetMode(Mode.Chase);
        if (!menace.Passive) Kind = Encounter.Hunt;
        lastKind = Kind;
        if (noticeSound != null) PlaySound(noticeSound);
        Hold(stareAnim, stareMs);
        foreach (Entity other in entity.World.GetEntitiesAround(entity.Pos.XYZ, 48, 16, e => e != entity && e.Alive && e.Code == entity.Code))
            other.GetBehavior<EntityBehaviorTaskAI>()?.TaskManager.GetTask<AiTaskWatch>()?.Alarm(lastSeen, who);
    }

    /// <summary>Another of the Watch has seen someone there: come and search.</summary>
    public void Alarm(Vec3d at, Entity who)
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null || menace.Kind == Encounter.Leave || mode is Mode.Chase or Mode.Peer) return;
        menace.Target = who;
        if (!menace.Passive) menace.Kind = Encounter.Hunt;
        lastKind = menace.Kind;
        BeginSearch(at.Clone(), hurry: true);
    }

    // ================= Modes =================

    private void SetMode(Mode next)
    {
        mode = next;
        modeSinceMs = Now;
        arrived = false;
        chasing = null;
        Log("now {0}", next);
    }

    private long InMode => Now - modeSinceMs;

    /// <summary>Patrolling: a glimpse stands sweeping the street; a stalker walks from one spot to the next round the person it was put down for, stopping at each to look.</summary>
    private void Patrol(Encounter kind, Entity target)
    {
        Random rand = entity.World.Rand;
        if (kind == Encounter.Glimpse)
        {
            // Standing in the street sweeping it with its eye, turned more across the way than at you
            Stop();
            SetPose(scanAnim);
            if (goal == null)
            {
                double angle = Math.Atan2(target.Pos.Z - entity.Pos.Z, target.Pos.X - entity.Pos.X) + (rand.NextDouble() < 0.5 ? 1 : -1) * (1.0 + rand.NextDouble() * 0.8);
                goal = entity.Pos.XYZ.Add(Math.Cos(angle) * 8, 1.5, Math.Sin(angle) * 8);
            }
            return;
        }
        // On its way (a path search may still be pending), or at a spot looking about a while: then on to the next
        if (pathTraverser.Active || !arrived && Now - lastPathMs < 3000) return;
        if (Now < poseUntilMs) return;
        SetPose(null);
        Vec3d next = OutdoorPoint(target.Pos.XYZ, 8, 22) ?? OutdoorPoint(entity.Pos.XYZ, 4, 12);
        if (next == null)
        {
            Scan(4000);
            return;
        }
        arrived = false;
        Log("patrols on to {0:0},{1:0},{2:0}", next.X, next.Y, next.Z);
        Go(next, walkSpeed, 1.2f, () =>
        {
            arrived = true;
            // Facing more or less the way the person it was put down for is, give or take
            Vec3d toward = menace.Target?.Pos.XYZ ?? entity.Pos.XYZ;
            double angle = Math.Atan2(toward.Z - entity.Pos.Z, toward.X - entity.Pos.X) + (rand.NextDouble() - 0.5) * 2.2;
            goal = entity.Pos.XYZ.Add(Math.Cos(angle) * 8, 1.5, Math.Sin(angle) * 8);
            Scan(4000 + rand.Next(3500));
        });
    }

    private void Scan(int ms)
    {
        Stop();
        SetPose(scanAnim);
        poseUntilMs = Now + ms;
    }

    /// <summary>The chase: after them while it can see them; out of sight a few seconds, it goes to search where they were.</summary>
    private void Chase()
    {
        if (watched == null || !watched.Alive || IsCreative(watched))
        {
            EndHunt();
            return;
        }
        double v = Visibility(watched, chaseSenses, out bool glass);
        if (v > 0)
        {
            lastSeen = watched.Pos.XYZ;
            lastSeenMs = Now;
        }
        else if (Now - lastSeenMs > loseSeconds * 1000)
        {
            Log("loses {0}", watched.Code);
            BeginSearch(lastSeen, hurry: true);
            return;
        }

        // Seen through glass, or out of reach: it can't get in, so it watches
        if (v > 0 && (glass || Now < noPathUntilMs))
        {
            BeginPeer();
            return;
        }

        double gap = Gap(watched);
        if (gap <= attackRange && Now - lastAttackMs > attackCooldownMs * cooldownMul && Senses.ClearLine(entity.World, Senses.Centre(entity), Senses.Centre(watched)))
        {
            StartAttack();
            return;
        }
        if (gap <= attackRange)
        {
            Stop();
            goal = watched.Pos.XYZ;
            return;
        }
        if (Now < noPathUntilMs) return;
        // Only where it saw them: it does not know where they have gone
        Vec3d to = v > 0 ? watched.Pos.XYZ : lastSeen;
        bool moved = chasing == null || chasing.SquareDistanceTo(to.X, to.Y, to.Z) >= 4;
        if (!pathTraverser.Active || moved && Now - lastPathMs > 750)
        {
            chasing = to.Clone();
            Go(chasing, runSpeed, attackRange * 0.6f + (entity.SelectionBox.XSize + watched.SelectionBox.XSize) / 2, null, async: false);
        }
        else if (v > 0)
        {
            pathTraverser.CurrentTarget.X = to.X;
            pathTraverser.CurrentTarget.Y = to.Y;
            pathTraverser.CurrentTarget.Z = to.Z;
        }
    }

    private void BeginSearch(Vec3d at, bool hurry)
    {
        SetMode(Mode.Search);
        SetPose(null);
        lastSeen = at;
        goal = at;
        Go(at, hurry ? runSpeed * 0.8f : walkSpeed * 1.3f, 2.5f, () =>
        {
            arrived = true;
            Scan((int)(searchSeconds * 1000));
        });
    }

    /// <summary>Searching where it last saw them, the eye sweeping; then it makes as if to leave, or goes back to its rounds.</summary>
    private void Search()
    {
        // (Never got there: searched the way it could)
        if (!arrived && !pathTraverser.Active && Now - lastPathMs > 1500)
        {
            arrived = true;
            Scan((int)(searchSeconds * 1000));
        }
        if (!arrived) return;
        if (Now < poseUntilMs) return;
        if (entity.World.Rand.NextDouble() < 0.5) BeginFeint();
        else EndHunt();
    }

    /// <summary>A feint: it walks off as if it had given up, then stops, turns, and waits, watching the place.</summary>
    private void BeginFeint()
    {
        SetMode(Mode.Feint);
        SetPose(null);
        Vec3d place = lastSeen ?? entity.Pos.XYZ;
        Vec3d away = OutdoorPointAway(place, 12, 16);
        if (away == null)
        {
            arrived = true;
            goal = place;
            Stop();
            return;
        }
        Go(away, walkSpeed, 1.5f, () =>
        {
            arrived = true;
            goal = place.AddCopy(0, 1.5, 0);
            Stop();
        });
    }

    private void Feint()
    {
        if (!arrived && !pathTraverser.Active && Now - lastPathMs > 1500)
        {
            arrived = true;
            goal = lastSeen;
        }
        if (InMode > (feintSeconds + 12) * 1000) EndHunt();
    }

    /// <summary>Gives up: back to its rounds, the eye off whoever it was after.</summary>
    private void EndHunt()
    {
        watched = null;
        SetWatchOn(null);
        SetPose(null);
        SetMode(Mode.Patrol);
        poseUntilMs = 0;
        if (Kind == Encounter.Hunt) Kind = Encounter.Stalk;
        lastKind = Kind;
    }

    /// <summary>Someone it has seen indoors: it comes to the window and watches them through it.</summary>
    private void BeginPeer()
    {
        SetMode(Mode.Peer);
        Vec3d spot = WindowSpot(watched);
        if (spot != null && spot.DistanceTo(entity.Pos.XYZ) > 1.5) Go(spot, walkSpeed * 1.5f, 1.0f, () => arrived = true);
        else
        {
            arrived = true;
            Stop();
        }
    }

    private void Peer(float dt)
    {
        if (watched == null || !watched.Alive || IsCreative(watched))
        {
            EndHunt();
            return;
        }
        double v = Visibility(watched, chaseSenses, out bool glass);
        if (v > 0)
        {
            lastSeen = watched.Pos.XYZ;
            lastSeenMs = Now;
        }
        goal = Senses.Eyes(watched);
        if (!arrived && !pathTraverser.Active && Now - lastPathMs > 1500) arrived = true;
        if (arrived)
        {
            Stop();
            SetPose(peerAnim);
        }
        // Came out where it can get at them: the chase again
        if (v > 0 && !glass && Now >= noPathUntilMs && Outdoors(watched.Pos.XYZ))
        {
            SetPose(null);
            SetMode(Mode.Chase);
            return;
        }
        if (v > 0 && glass && arrived)
        {
            // Being watched through the glass wears on the mind; now and then a tap on the pane
            double stability = Senses.Stability(watched);
            if (stability > 0.3) watched.WatchedAttributes.SetDouble("temporalStability", Math.Max(0.3, stability - 0.005 * dt));
            if (tapSound != null && Now >= nextTapMs && entity.Pos.DistanceTo(watched.Pos) < 8)
            {
                nextTapMs = Now + 6000 + entity.World.Rand.Next(5000);
                PlaySound(tapSound);
            }
        }
        if (Now - lastSeenMs > loseSeconds * 2000 || InMode > peerSeconds * 1000)
        {
            SetPose(null);
            BeginSearch(lastSeen, hurry: false);
        }
    }

    private void Leave()
    {
        SetPose(null);
        SetWatchOn(null);
        Entity from = menace.Target;
        if (!pathTraverser.Active || Now - lastPathMs > 4000)
        {
            Vec3d away = OutdoorPointAway(from?.Pos.XYZ ?? entity.Pos.XYZ, 18, 28);
            if (away != null) Go(away, walkSpeed * 1.2f, 2, null);
        }
    }

    // ================= Attacks =================

    private void StartAttack()
    {
        Stop();
        SetPose(null);
        attackStartMs = Now;
        damageDone = false;
        if (attackAnim != null) entity.AnimManager.StartAnimation(attackAnim);
        if (attackSound != null) entity.World.RegisterCallback(_ => { if (entity.Alive) PlaySound(attackSound); }, Math.Max(0, damageAtMs - 60));
    }

    private void ContinueAttack()
    {
        long elapsed = Now - attackStartMs;
        if (watched != null) TurnTowards(watched.Pos.XYZ, 0.05f);
        if (!damageDone && elapsed >= damageAtMs)
        {
            damageDone = true;
            if (watched != null && watched.Alive && Gap(watched) <= attackRange + 0.4) Hit(watched);
        }
        if (elapsed >= attackDurationMs)
        {
            if (attackAnim != null) entity.AnimManager.StopAnimation(attackAnim);
            attackStartMs = -1;
            lastAttackMs = Now;
        }
    }

    private void Hit(Entity who)
    {
        float scaled = damage * damageMul * (float)director.Setting.Damage * GlobalConstants.CreatureDamageModifier;
        if (scaled <= 0) return;
        who.ReceiveDamage(new DamageSource
        {
            Source = EnumDamageSource.Entity,
            SourceEntity = entity,
            Type = damageType,
            DamageTier = damageTier + tierBonus,
            KnockbackStrength = knockback,
        }, scaled);
        director.NoteCloseCall(who);
        Log("hit {0} for {1:0.0}", who.Code, scaled);
    }

    private double Gap(Entity other) => entity.Pos.DistanceTo(other.Pos) - (entity.SelectionBox.XSize + other.SelectionBox.XSize) / 2;

    public override void OnEntityHurt(DamageSource source, float damage)
    {
        base.OnEntityHurt(source, damage);
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null || menace.Kind == Encounter.Leave || entity.World.Side != EnumAppSide.Server) return;
        // Struck, it feels where it came from: it turns on whoever did it
        if (source.GetCauseEntity() is EntityAgent cause && cause != entity && !IsCreative(cause) && mode != Mode.Chase)
        {
            director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
            Spot(cause);
        }
    }

    // ================= Places =================

    /// <summary>Whether a spot is under the open sky (the streets and yards it walks; not a house, a porch or a garage).</summary>
    private bool Outdoors(Vec3d pos) => entity.World.BlockAccessor.GetRainMapHeightAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)) <= (int)Math.Floor(pos.Y);

    /// <summary>A floor under the open sky with room for it, between two distances of a point.</summary>
    private Vec3d OutdoorPoint(Vec3d around, double min, double max)
    {
        Random rand = entity.World.Rand;
        for (int i = 0; i < 12; i++)
        {
            double angle = rand.NextDouble() * Math.PI * 2, d = min + rand.NextDouble() * (max - min);
            if (Floor(around.X + Math.Cos(angle) * d, around.Y, around.Z + Math.Sin(angle) * d) is { } p) return p;
        }
        return null;
    }

    /// <summary>The same, away from a point (on the side this entity is on).</summary>
    private Vec3d OutdoorPointAway(Vec3d from, double min, double max)
    {
        Random rand = entity.World.Rand;
        double away = Math.Atan2(entity.Pos.Z - from.Z, entity.Pos.X - from.X);
        for (int i = 0; i < 12; i++)
        {
            double angle = away + (rand.NextDouble() - 0.5) * (i < 6 ? 1.4 : 3.2), d = min + rand.NextDouble() * (max - min);
            if (Floor(from.X + Math.Cos(angle) * d, entity.Pos.Y, from.Z + Math.Sin(angle) * d) is { } p) return p;
        }
        return null;
    }

    private Vec3d Floor(double x, double nearY, double z)
    {
        int bx = (int)Math.Floor(x), bz = (int)Math.Floor(z);
        if (entity.World.BlockAccessor.GetChunkAtBlockPos(bx, (int)nearY, bz) == null) return null;
        int y = Senses.FindFloor(entity.World, bx, (int)Math.Floor(nearY), bz, 3, 4);
        if (y == int.MinValue) return null;
        var p = new Vec3d(bx + 0.5, y, bz + 0.5);
        return Outdoors(p) ? p : null;
    }

    /// <summary>Where to stand to look in at someone indoors: outside, close, with nothing but glass between.</summary>
    private Vec3d WindowSpot(Entity who)
    {
        Vec3d best = null;
        double bestD = double.MaxValue;
        Vec3d eyes = Senses.Eyes(who);
        for (int r = 2; r <= 7; r++)
        {
            for (int i = 0; i < 12; i++)
            {
                double angle = i * Math.PI / 6;
                if (Floor(who.Pos.X + Math.Cos(angle) * r, who.Pos.Y, who.Pos.Z + Math.Sin(angle) * r) is not { } p) continue;
                if (!SightLine(entity.World, p.AddCopy(0, 2.4, 0), eyes)) continue;
                double d = p.SquareDistanceTo(entity.Pos.XYZ);
                if (d < bestD) { bestD = d; best = p; }
            }
            if (best != null) return best;
        }
        return null;
    }

    // ================= Movement, poses and sounds =================

    private void Go(Vec3d to, float speed, float within, Action onArrived, bool async = true)
    {
        lastPathMs = Now;
        SetPose(null);
        SetMotion(speed >= runSpeed * 0.75f ? Motion.Run : Motion.Walk);
        to = to.Clone();
        speed *= speedMul;
        void Arrived()
        {
            SetMotion(Motion.Still);
            onArrived?.Invoke();
        }
        void Stuck()
        {
            SetMotion(Motion.Still);
            onArrived?.Invoke();
        }
        void NoPath()
        {
            SetMotion(Motion.Still);
            noPathUntilMs = Now + 4000;
            onArrived?.Invoke();
        }
        if (async) pathTraverser.NavigateTo_Async(to, speed, within, Arrived, Stuck, NoPath, 2500, 1);
        else
        {
            pathTraverser.Stop();
            pathTraverser.NavigateTo(to, speed, within, Arrived, Stuck, NoPath, false, 2000, 1);
        }
    }

    private void Stop()
    {
        pathTraverser.Stop();
        SetMotion(Motion.Still);
    }

    private void Hold(string animation, int ms)
    {
        Stop();
        SetPose(null);
        if (animation != null) entity.AnimManager.StartAnimation(animation);
        holdUntilMs = Now + ms;
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

    /// <summary>The standing animation it holds (sweeping the street, crouched at a window), or none.</summary>
    private void SetPose(string anim)
    {
        if (anim == pose) return;
        if (pose != null) entity.AnimManager.StopAnimation(pose);
        pose = anim;
        if (pose != null) entity.AnimManager.StartAnimation(pose);
    }

    private void SetWatchOn(Entity who)
    {
        long id = who?.EntityId ?? -1;
        if (entity.WatchedAttributes.GetLong(WatchOnKey, -1) != id) entity.WatchedAttributes.SetLong(WatchOnKey, id);
    }

    private void TurnTowards(Vec3d point, float dt)
    {
        float desired = (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float turn = 3f * dt;
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -turn, turn)) % GameMath.TWOPI;
    }

    private void PlaySound(AssetLocation sound) =>
        entity.World.PlaySoundAt(sound, entity.Pos.X, entity.Pos.Y + 2.4, entity.Pos.Z, null, true, cryRange);

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Stop();
        SetPose(null);
        if (attackStartMs >= 0 && attackAnim != null) entity.AnimManager.StopAnimation(attackAnim);
        attackStartMs = -1;
    }

    private float HealthFraction()
    {
        var health = entity.GetBehavior<EntityBehaviorHealth>();
        return health == null || health.MaxHealth <= 0 ? 1 : health.Health / health.MaxHealth;
    }

    private static bool IsCreative(Entity who) =>
        who is EntityPlayer player && player.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator;

    private void Log(string format, params object[] args)
    {
        if (director?.Logging != true || entity.Api is not ICoreServerAPI sapi) return;
        sapi.Logger.Notification("[backrooms] {0} #{1} at {2:0},{3:0},{4:0}: {5}", entity.Code.Path, entity.EntityId, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, string.Format(format, args));
    }
}

/// <summary>Gives the Watch's eye its <see cref="WatchEyeController"/> on the client.</summary>
public class EntityBehaviorWatchEye : EntityBehavior
{
    private bool noEye;

    public EntityBehaviorWatchEye(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-watcheye";

    public override void OnGameTick(float dt)
    {
        if (noEye || entity.World.Side != EnumAppSide.Client) return;
        IAnimationManager anim = entity.AnimManager;
        if (anim?.Animator == null || anim.HeadController is WatchEyeController) return;
        try
        {
            anim.HeadController = new WatchEyeController(anim, entity, (ICoreClientAPI)entity.Api);
        }
        catch (InvalidOperationException)
        {
            noEye = true;
        }
    }
}

/// <summary>
/// Turns the Watch's eye, on the client only, onto whoever the server says it is watching (<see cref="AiTaskWatch.WatchOnKey"/>):
/// steadily, so you see it come round to you. Nothing else is sent over the network.
/// </summary>
public class WatchEyeController : IHeadController
{
    private const float TurnPerSecond = 1.6f, MaxYaw = 1.4f, MaxPitch = 0.9f; // radians
    private readonly Entity entity;
    private readonly ICoreClientAPI capi;
    private readonly ElementPose eye;
    private float yaw, pitch;

    public float YawOffset { get; set; }
    public float PitchOffset { get; set; }

    public WatchEyeController(IAnimationManager animator, Entity entity, ICoreClientAPI capi)
    {
        this.entity = entity;
        this.capi = capi;
        eye = animator.Animator.GetPosebyName("Eye") ?? throw new InvalidOperationException("no Eye");
    }

    public void OnFrame(float dt)
    {
        float wantYaw = 0, wantPitch = 0;
        long id = entity.WatchedAttributes.GetLong(AiTaskWatch.WatchOnKey, -1);
        Entity on = id >= 0 && entity.Alive ? capi.World.GetEntityById(id) : null;
        if (on != null)
        {
            double dx = on.Pos.X - entity.Pos.X, dz = on.Pos.Z - entity.Pos.Z;
            float toward = (float)Math.Atan2(dx, dz);
            wantYaw = GameMath.Clamp(GameMath.AngleRadDistance(entity.Pos.Yaw, toward), -MaxYaw, MaxYaw);
            double dy = on.Pos.Y + on.LocalEyePos.Y - (entity.Pos.Y + entity.LocalEyePos.Y);
            // (+Z turns the front of the eye down)
            wantPitch = GameMath.Clamp((float)Math.Atan2(-dy, Math.Sqrt(dx * dx + dz * dz)), -MaxPitch, MaxPitch);
        }
        float step = TurnPerSecond * dt;
        yaw += GameMath.Clamp(wantYaw - yaw, -step, step);
        pitch += GameMath.Clamp(wantPitch - pitch, -step, step);
        eye.degOffY = (yaw + YawOffset) * GameMath.RAD2DEG;
        eye.degOffZ = pitch * GameMath.RAD2DEG;
    }
}
