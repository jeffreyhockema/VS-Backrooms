using System;
using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>Registers the Watcher's AI task and its eye (client) with the game, on both sides.</summary>
public class WatcherClasses : ModSystem
{
    public override double ExecuteOrder() => 0.05;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntityBehaviorClass("backrooms-watchereye", typeof(EntityBehaviorWatcherEye));
        AiTaskRegistry.Register<AiTaskWatcher>("backrooms-watcher");
    }
}

/// <summary>
/// The Watcher (Entity 96's floating form, Level 9): a gigantic eye that levitates, silent, at walking speed, a few
/// blocks over the streets and above the houses. It sees (through the shared <see cref="Perception.Sight"/>, with the
/// Neighborhood Watch's profile: by the light on someone, through glass) and has neither hearing nor smell.
/// <list type="bullet">
/// <item>Seen in the open within twelve blocks, someone gets two seconds of warning: the eye turns on them, the pupil
/// contracts, the iris brightens, a tone rises. That is the dodge window. If it still sees them in the open, within
/// twelve blocks, at the end, the beam fires and they are turned to dust, whatever they wear.</item>
/// <item>Beyond twelve blocks it drifts closer at a walking pace; behind glass it can only look (the beam needs open
/// air), so someone in a house is watched from outside the window. It never goes in: it is far too large.</item>
/// <item>Losing sight during the charge cancels it, and it searches where it last saw them for ten seconds.</item>
/// <item>Nothing hurts or moves it (EntityBehaviorMenace "immortal", "unmoved").</item>
/// </list>
/// </summary>
public class AiTaskWatcher : AiTaskBase
{
    private enum Mode { Patrol, Approach, Charge, Peer, Search, Cooldown }

    /// <summary>Synced to clients: the entity id the eye is turned on (-1 for none); see <see cref="WatcherEyeController"/>.</summary>
    public const string WatcherOnKey = "backrooms:watcherOn";

    private readonly float speed, hoverMin, hoverMax, fireRange, chargeSeconds, beamSeconds, searchSeconds, cooldownSeconds, loseGrace, hearRange;
    private readonly SenseProfile senses;
    private readonly string scanAnim, chargeAnim, beamAnim;
    private readonly AssetLocation humSound, chargeSound, beamSound;

    private EntityBehaviorMenace menace;
    private MenaceSystem director;
    private Mode mode = Mode.Patrol;
    private string pose;
    private Vec3d goal, lastSeen;
    private Entity chargeOn, peering;
    private long modeSinceMs, lostSinceMs = -1, nextHumMs, poseUntilMs, coolUntilMs;
    private float think;
    private int street = int.MinValue, thoughts;
    private bool waiting;

    public AiTaskWatcher(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        speed = taskConfig["speed"].AsFloat(0.025f);
        hoverMin = taskConfig["hoverMin"].AsFloat(4);
        hoverMax = taskConfig["hoverMax"].AsFloat(6);
        fireRange = taskConfig["fireRange"].AsFloat(12);
        chargeSeconds = taskConfig["chargeSeconds"].AsFloat(2);
        beamSeconds = taskConfig["beamSeconds"].AsFloat(0.5f);
        searchSeconds = taskConfig["searchSeconds"].AsFloat(10);
        cooldownSeconds = taskConfig["cooldownSeconds"].AsFloat(4);
        loseGrace = taskConfig["loseGraceSeconds"].AsFloat(0.4f);
        hearRange = taskConfig["soundRange"].AsFloat(40);
        senses = SenseProfile.Parse(taskConfig["senses"]) ?? new SenseProfile();
        scanAnim = taskConfig["scanAnimation"].AsString("scan");
        chargeAnim = taskConfig["chargeAnimation"].AsString("charge");
        beamAnim = taskConfig["beamAnimation"].AsString("beam");
        humSound = Sound(taskConfig["humSound"].AsString(null));
        chargeSound = Sound(taskConfig["chargeSound"].AsString(null));
        beamSound = Sound(taskConfig["beamSound"].AsString(null));
    }

    private static AssetLocation Sound(string code) => code == null ? null : AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/");

    private long Now => entity.World.ElapsedMilliseconds;

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        return menace != null;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        if (street == int.MinValue)
        {
            int f = Senses.FindFloor(entity.World, (int)Math.Floor(entity.Pos.X), (int)Math.Floor(entity.Pos.Y), (int)Math.Floor(entity.Pos.Z), 1, 14);
            street = f == int.MinValue ? (int)Math.Floor(entity.Pos.Y) : f;
        }
        nextHumMs = Now + 1500;
        think = 0;
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || menace == null) return false;
        long now = Now;
        if (humSound != null && now >= nextHumMs)
        {
            nextHumMs = now + 4500 + entity.World.Rand.Next(2500);
            entity.World.PlaySoundAt(humSound, entity.Pos.X, entity.Pos.Y + 1.2, entity.Pos.Z, null, true, hearRange, 0.8f);
        }
        Steer(dt);
        think -= dt;
        if (think > 0) return true;
        think = 0.2f;
        Think();
        return true;
    }

    // ================= Thinking =================

    private void Think()
    {
        Entity target = menace.Target;
        if (menace.Kind is Encounter.Leave or Encounter.Ambient || target == null || !target.Alive)
        {
            Leave(target);
            return;
        }
        Seen best = Look(out double bestPlain);
        if (director?.Logging == true && ++thoughts % 10 == 0)
            Log("{0}, {1}, sees {2}", mode, menace.Kind, best == null ? "no one" : $"{best.Who.Code} at {best.Distance:0.0} ({(best.Open ? "open" : "through glass")}, plainness {bestPlain:0.00})");

        switch (mode)
        {
            case Mode.Charge:
                Charging(best);
                return;
            case Mode.Cooldown:
                if (Now >= coolUntilMs)
                {
                    entity.AnimManager.StopAnimation(beamAnim);
                    SetEye(null);
                    SetMode(Mode.Patrol);
                }
                return;
        }

        if (best != null)
        {
            lostSinceMs = -1;
            lastSeen = best.Who.Pos.XYZ;
            if (menace.Target != best.Who) menace.Target = best.Who;
            SetEye(best.Who);
            SetPose(null);
            if (!menace.Passive && menace.Kind != Encounter.Hunt) menace.Kind = Encounter.Hunt;
            if (!best.Open || menace.Passive)
            {
                // Behind glass (or let alone): it can only look, from outside
                if (mode != Mode.Peer) { SetMode(Mode.Peer); Log("peers at {0} through glass", best.Who.Code); }
                peering = best.Who;
                goal = null;
            }
            else if (best.Distance <= fireRange) StartCharge(best.Who);
            else
            {
                if (mode != Mode.Approach) { SetMode(Mode.Approach); Log("sees {0}, {1:0.0} blocks off: closes in", best.Who.Code, best.Distance); }
                Vec3d p = best.Who.Pos.XYZ;
                double ang = Math.Atan2(entity.Pos.Z - p.Z, entity.Pos.X - p.X);
                goal = new Vec3d(p.X + Math.Cos(ang) * (fireRange - 3), HoverY(p.X, p.Z), p.Z + Math.Sin(ang) * (fireRange - 3));
            }
            return;
        }

        // Nothing in sight
        if (mode is Mode.Approach or Mode.Peer)
        {
            if (lostSinceMs < 0) lostSinceMs = Now;
            if (Now - lostSinceMs > 1500) BeginSearch();
            return;
        }
        if (mode == Mode.Search)
        {
            if (Now - modeSinceMs > searchSeconds * 1000)
            {
                Log("gives up the search");
                SetEye(null);
                SetMode(Mode.Patrol);
                return;
            }
            if (goal != null && entity.Pos.XYZ.DistanceTo(goal) < 1.5)
            {
                goal = null;
                Scan();
            }
            return;
        }
        Patrol(target);
    }

    private void Patrol(Entity target)
    {
        Random rand = entity.World.Rand;
        SetEye(null);
        if (menace.Kind == Encounter.Glimpse)
        {
            // Hovers where it is, sweeping the street
            goal = null;
            Scan();
            return;
        }
        if (goal != null && entity.Pos.XYZ.DistanceTo(goal) > 1.5) return;
        if (!waiting)
        {
            // Arrived (or just started): look about a while
            waiting = true;
            goal = null;
            Scan();
            poseUntilMs = Now + 3500 + rand.Next(3500);
            return;
        }
        if (Now < poseUntilMs) return;
        waiting = false;
        SetPose(null);
        double angle = rand.NextDouble() * Math.PI * 2, d = 10 + rand.NextDouble() * 16;
        double x = target.Pos.X + Math.Cos(angle) * d, z = target.Pos.Z + Math.Sin(angle) * d;
        goal = new Vec3d(x, HoverY(x, z), z);
        Log("drifts on to {0:0},{1:0},{2:0}", goal.X, goal.Y, goal.Z);
    }

    private void BeginSearch()
    {
        if (lastSeen == null)
        {
            SetMode(Mode.Patrol);
            return;
        }
        SetEye(null);
        SetMode(Mode.Search);
        goal = new Vec3d(lastSeen.X, HoverY(lastSeen.X, lastSeen.Z), lastSeen.Z);
        Log("lost sight: searches {0:0},{1:0}", lastSeen.X, lastSeen.Z);
    }

    private void Leave(Entity target)
    {
        SetEye(null);
        SetPose(null);
        entity.AnimManager.StopAnimation(chargeAnim);
        Vec3d from = target?.Pos.XYZ ?? entity.Pos.XYZ.Add(1, 0, 0);
        double away = Math.Atan2(entity.Pos.Z - from.Z, entity.Pos.X - from.X);
        goal = entity.Pos.XYZ.Add(Math.Cos(away) * 12, 2, Math.Sin(away) * 12);
    }

    // ================= Sight =================

    private sealed class Seen
    {
        public Entity Who;
        public double Distance;
        public bool Open;
    }

    /// <summary>Everyone it could be watching: the players near, and a console test's straw dummy.</summary>
    private IEnumerable<Entity> Candidates()
    {
        float range = senses.SightLit + 2;
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, range, range, e => e is EntityPlayer p && p.Alive))
            if (!IsCreative(e)) yield return e;
        Entity target = menace.Target;
        if (target != null && target.Alive && target.WatchedAttributes.GetBool("backrooms:testTarget")) yield return target;
    }

    /// <summary>The one it sees best (null for no one): how far, and whether the line to them is open air (the beam goes through no glass).</summary>
    private Seen Look(out double plain)
    {
        plain = 0;
        Seen best = null;
        Vec3d eye = Senses.Eyes(entity);
        foreach (Entity who in Candidates())
        {
            double p = Perception.Sight(entity, who, senses, out _);
            if (p <= plain) continue;
            Vec3d centre = Senses.Centre(who);
            plain = p;
            best = new Seen { Who = who, Distance = eye.DistanceTo(centre), Open = Senses.ClearLine(entity.World, eye, centre, false) };
        }
        return best;
    }

    // ================= Charge and beam =================

    private void StartCharge(Entity who)
    {
        SetMode(Mode.Charge);
        chargeOn = who;
        goal = null;
        entity.AnimManager.StartAnimation(chargeAnim);
        if (chargeSound != null) entity.World.PlaySoundAt(chargeSound, entity.Pos.X, entity.Pos.Y + 1.2, entity.Pos.Z, null, false, hearRange, 1f);
        Log("charges at {0}", who.Code);
    }

    private void Charging(Seen best)
    {
        bool still = best != null && best.Who == chargeOn;
        if (!still)
        {
            if (lostSinceMs < 0) lostSinceMs = Now;
            if (Now - lostSinceMs > loseGrace * 1000)
            {
                Log("lost sight during the charge: cancels");
                CancelCharge();
                BeginSearch();
            }
            return;
        }
        lostSinceMs = -1;
        lastSeen = best.Who.Pos.XYZ;
        if (!best.Open || best.Distance > fireRange + 0.5)
        {
            // Out of range or behind something: no beam
            Log("{0} is out of the beam ({1:0.0} blocks, {2}): cancels", best.Who.Code, best.Distance, best.Open ? "open" : "no open line");
            CancelCharge();
            return;
        }
        if (Now - modeSinceMs >= chargeSeconds * 1000) Fire(best.Who);
    }

    private void CancelCharge()
    {
        entity.AnimManager.StopAnimation(chargeAnim);
        chargeOn = null;
        waiting = false;
        SetMode(Mode.Patrol);
    }

    private Vec3d BeamOrigin()
    {
        Vec3d eye = Senses.Eyes(entity);
        return eye.AddCopy(Math.Sin(entity.Pos.Yaw) * 1.3, 0, Math.Cos(entity.Pos.Yaw) * 1.3);
    }

    private void Fire(Entity who)
    {
        Vec3d from = BeamOrigin(), to = Senses.Centre(who);
        entity.AnimManager.StopAnimation(chargeAnim);
        entity.AnimManager.StartAnimation(beamAnim);
        if (beamSound != null) entity.World.PlaySoundAt(beamSound, entity.Pos.X, entity.Pos.Y + 1.2, entity.Pos.Z, null, false, hearRange, 1f);
        SetMode(Mode.Cooldown);
        coolUntilMs = Now + (long)((beamSeconds + cooldownSeconds) * 1000);
        chargeOn = null;
        BeamParticles(from, to);
        Log("fires at {0}: turned to dust", who.Code);
        // Large enough to kill through any armour
        who.ReceiveDamage(new DamageSource
        {
            Source = EnumDamageSource.Entity,
            SourceEntity = entity,
            Type = EnumDamageType.Injury,
            DamageTier = 99,
            KnockbackStrength = 0,
        }, 9999f);
        double x = to.X, y = who.Pos.Y, z = to.Z;
        DustPile(x, y, z);
        entity.World.RegisterCallback(_ => DustPile(x, y, z), 700);
    }

    private void BeamParticles(Vec3d from, Vec3d to)
    {
        double len = from.DistanceTo(to);
        int n = Math.Max(6, (int)(len * 3));
        int white = ColorUtil.ToRgba(255, 255, 240, 205), hot = ColorUtil.ToRgba(255, 255, 150, 90);
        for (int i = 0; i <= n; i++)
        {
            double t = i / (double)n;
            var p = new SimpleParticleProperties(1, 1, i % 3 == 0 ? hot : white,
                new Vec3d(from.X + (to.X - from.X) * t - 0.05, from.Y + (to.Y - from.Y) * t - 0.05, from.Z + (to.Z - from.Z) * t - 0.05),
                new Vec3d(0.1, 0.1, 0.1), new Vec3f(0, 0, 0), new Vec3f(0, 0, 0), 0.55f, 0f, 0.3f, 0.55f, EnumParticleModel.Quad)
            {
                VertexFlags = 255,
                ShouldDieInLiquid = false,
            };
            entity.World.SpawnParticles(p);
        }
    }

    /// <summary>A puff of fine gray dust that settles where someone stood.</summary>
    private void DustPile(double x, double y, double z)
    {
        var dust = new SimpleParticleProperties(40, 60, ColorUtil.ToRgba(210, 150, 148, 142),
            new Vec3d(x - 0.4, y + 0.05, z - 0.4), new Vec3d(0.8, 1.2, 0.8), new Vec3f(-0.25f, 0.1f, -0.25f), new Vec3f(0.25f, 0.5f, 0.25f),
            4f, 0.05f, 0.08f, 0.22f, EnumParticleModel.Quad)
        {
            ShouldDieInLiquid = true,
        };
        entity.World.SpawnParticles(dust);
    }

    // ================= Flight =================

    private void SetMode(Mode next)
    {
        mode = next;
        modeSinceMs = Now;
        lostSinceMs = -1;
        if (next is Mode.Charge or Mode.Peer or Mode.Approach) SetPose(null);
        Log("now {0}", next);
    }

    /// <summary>A height to hover at over a column: four to six blocks over the street, and clear above any roof.</summary>
    private double HoverY(double x, double z)
    {
        double y = street + hoverMin + entity.World.Rand.NextDouble() * (hoverMax - hoverMin);
        int roof = entity.World.BlockAccessor.GetRainMapHeightAt((int)Math.Floor(x), (int)Math.Floor(z));
        return Math.Max(y, roof + 3.0);
    }

    private void Steer(float dt)
    {
        // What it faces: whoever it is charging, peering at or closing in on
        Entity look = mode switch
        {
            Mode.Charge => chargeOn,
            Mode.Peer => peering ?? menace.Target,
            Mode.Approach or Mode.Cooldown => menace.Target,
            _ => null,
        };
        if (goal == null || mode is Mode.Charge or Mode.Cooldown)
        {
            entity.Controls.WalkVector.Set(0, 0, 0);
            entity.Controls.FlyVector.Set(0, 0, 0);
            if (look != null) Turn((float)Math.Atan2(look.Pos.X - entity.Pos.X, look.Pos.Z - entity.Pos.Z), dt, 3f);
            else if (mode is Mode.Patrol or Mode.Search) entity.Pos.Yaw = (entity.Pos.Yaw + 0.5f * dt) % GameMath.TWOPI; // sweeping about
            return;
        }
        // Never into a roof ahead: climb over
        double dx = goal.X - entity.Pos.X, dy = goal.Y - entity.Pos.Y, dz = goal.Z - entity.Pos.Z;
        double h = Math.Sqrt(dx * dx + dz * dz);
        if (h > 0.1)
        {
            int roofAhead = entity.World.BlockAccessor.GetRainMapHeightAt((int)Math.Floor(entity.Pos.X + dx / h * 3), (int)Math.Floor(entity.Pos.Z + dz / h * 3));
            if (roofAhead + 2.5 > entity.Pos.Y) dy = Math.Max(dy, roofAhead + 3.5 - entity.Pos.Y);
        }
        double length = Math.Sqrt(dx * dx + dy * dy + dz * dz);
        if (length < 0.3)
        {
            entity.Controls.WalkVector.Set(0, 0, 0);
            entity.Controls.FlyVector.Set(0, 0, 0);
            return;
        }
        float s = speed * (float)Math.Min(1, length);
        entity.Controls.WalkVector.Set(dx / length * s, dy / length * s, dz / length * s);
        entity.Controls.FlyVector.Set(entity.Controls.WalkVector);
        Turn((float)Math.Atan2(look != null ? look.Pos.X - entity.Pos.X : dx, look != null ? look.Pos.Z - entity.Pos.Z : dz), dt, 1.5f);
    }

    private void Turn(float desired, float dt, float rate)
    {
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float turn = rate * dt;
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -turn, turn)) % GameMath.TWOPI;
    }

    // ================= Odds and ends =================

    private void Scan() => SetPose(scanAnim);

    private void SetPose(string anim)
    {
        if (anim == pose) return;
        if (pose != null) entity.AnimManager.StopAnimation(pose);
        pose = anim;
        if (pose != null) entity.AnimManager.StartAnimation(pose);
    }

    private void SetEye(Entity who)
    {
        long id = who?.EntityId ?? -1;
        if (entity.WatchedAttributes.GetLong(WatcherOnKey, -1) != id) entity.WatchedAttributes.SetLong(WatcherOnKey, id);
    }

    private static bool IsCreative(Entity who) =>
        who is EntityPlayer player && player.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator;

    private void Log(string format, params object[] args)
    {
        if (director?.Logging != true || entity.Api is not ICoreServerAPI sapi) return;
        sapi.Logger.Notification("[backrooms] {0} #{1} at {2:0},{3:0},{4:0}: {5}", entity.Code.Path, entity.EntityId, entity.Pos.X, entity.Pos.Y, entity.Pos.Z, string.Format(format, args));
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        entity.Controls.WalkVector.Set(0, 0, 0);
        entity.Controls.FlyVector.Set(0, 0, 0);
    }
}

/// <summary>Gives the Watcher's eye its <see cref="WatcherEyeController"/> on the client.</summary>
public class EntityBehaviorWatcherEye : EntityBehavior
{
    private bool noEye;

    public EntityBehaviorWatcherEye(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-watchereye";

    public override void OnGameTick(float dt)
    {
        if (noEye || entity.World.Side != EnumAppSide.Client) return;
        IAnimationManager anim = entity.AnimManager;
        if (anim?.Animator == null || anim.HeadController is WatcherEyeController) return;
        try
        {
            anim.HeadController = new WatcherEyeController(anim, entity, (ICoreClientAPI)entity.Api);
        }
        catch (InvalidOperationException)
        {
            noEye = true;
        }
    }
}

/// <summary>
/// Turns the Watcher's eye, on the client only, onto whoever the server says it is watching (<see cref="AiTaskWatcher.WatcherOnKey"/>):
/// steadily, so you see it come round to you. Nothing else is sent over the network.
/// </summary>
public class WatcherEyeController : IHeadController
{
    private const float TurnPerSecond = 1.8f, MaxYaw = 1.4f, MaxPitch = 0.9f; // radians
    private readonly Entity entity;
    private readonly ICoreClientAPI capi;
    private readonly ElementPose eye;
    private float yaw, pitch;

    public float YawOffset { get; set; }
    public float PitchOffset { get; set; }

    public WatcherEyeController(IAnimationManager animator, Entity entity, ICoreClientAPI capi)
    {
        this.entity = entity;
        this.capi = capi;
        eye = animator.Animator.GetPosebyName("Eye") ?? throw new InvalidOperationException("no Eye");
    }

    public void OnFrame(float dt)
    {
        float wantYaw = 0, wantPitch = 0;
        long id = entity.WatchedAttributes.GetLong(AiTaskWatcher.WatcherOnKey, -1);
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
