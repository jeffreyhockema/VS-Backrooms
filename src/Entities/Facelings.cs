using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// What makes a Faceling more than a person-shaped thing walking about (the lore's Entity 9 as the wiki has it now:
/// docile, imitating human routines, communicating by gesture, defending its own):
/// <list type="bullet">
/// <item>On the client, its blank face turns, head and neck only, to follow a player who passes within a dozen
/// blocks, slowly, as if it were watching.</item>
/// <item>Greeted (a player right-clicks it with an empty hand or anything else, not striking it), it turns to them and
/// waves, waits a moment, then turns and points the way to the nearest way out of the level it knows of. A child only
/// waves. If it knows of nothing, it shrugs.</item>
/// <item>Hurt by someone, the Facelings near it turn on them together: hit one in the city and the street comes for
/// you. A child that is hurt throws a tantrum at whoever did it.</item>
/// </list>
/// </summary>
public class EntityBehaviorFaceling : EntityBehavior
{
    private const string ProvokedKey = "backrooms:provoked";
    private long greetedAtMs = -100_000;
    private bool child, noHead;

    public EntityBehaviorFaceling(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-faceling";

    public override void Initialize(EntityProperties properties, JsonObject attributes)
    {
        base.Initialize(properties, attributes);
        child = entity.Code.Path.EndsWith("child");
    }

    // ================= The face that follows (client) =================

    public override void OnGameTick(float dt)
    {
        if (noHead || entity.World.Side != EnumAppSide.Client) return;
        IAnimationManager anim = entity.AnimManager;
        if (anim?.Animator == null || anim.HeadController is FacelingHeadController) return;
        try
        {
            anim.HeadController = new FacelingHeadController(anim, (EntityAgent)entity, (ICoreClientAPI)entity.Api);
        }
        catch (InvalidOperationException)
        {
            // (A shape without a Head and a Neck: leave it be, and stop asking, rather than throw every tick)
            noHead = true;
        }
    }

    // ================= Greetings (server) =================

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode, ref EnumHandling handled)
    {
        if (entity.World.Side != EnumAppSide.Server || mode != EnumInteractMode.Interact || byEntity is not EntityPlayer || !entity.Alive) return;
        var menace = entity.GetBehavior<EntityBehaviorMenace>();
        if (menace != null && menace.Kind is Encounter.Hunt or Encounter.Leave) return; // not now
        long now = entity.World.ElapsedMilliseconds;
        if (now - greetedAtMs < 9000) return;
        greetedAtMs = now;
        handled = EnumHandling.PreventDefault;

        // Stop what it was doing, and turn to whoever greeted it
        entity.GetBehavior<EntityBehaviorTaskAI>()?.TaskManager.StopTasks();
        Face(byEntity.Pos.XYZ);
        entity.AnimManager.StartAnimation("wave");
        if (child) return;
        entity.World.RegisterCallback(_ => PointTheWay(byEntity), 3000);
    }

    private void PointTheWay(Entity greeter)
    {
        if (!entity.Alive) return;
        entity.AnimManager.StopAnimation("wave");
        WorldLayout layout = entity.Api.ModLoader.GetModSystem<MenaceSystem>()?.Layout;
        int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
        if (layout == null)
        {
            entity.AnimManager.StartAnimation("shrug");
            return;
        }
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
        if (layout.NearestGate(x, z, level, 400) is { } gate)
        {
            entity.GetBehavior<EntityBehaviorTaskAI>()?.TaskManager.StopTasks();
            Face(new Vec3d(gate.X + 0.5, entity.Pos.Y, gate.Z + 0.5));
            entity.AnimManager.StartAnimation("point");
            // A nod back at whoever asked, after: too long, as they do
            entity.World.RegisterCallback(_ =>
            {
                if (!entity.Alive) return;
                if (greeter?.Alive == true) Face(greeter.Pos.XYZ);
                entity.AnimManager.StartAnimation("nod");
            }, 3200);
        }
        else entity.AnimManager.StartAnimation("shrug");
    }

    private void Face(Vec3d point)
    {
        float yaw = (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        entity.Pos.Yaw = yaw;
    }

    // ================= Defending their own (server) =================

    public override void OnEntityReceiveDamage(DamageSource damageSource, ref float damage)
    {
        if (entity.World.Side != EnumAppSide.Server || damage <= 0) return;
        if (damageSource.GetCauseEntity() is not EntityPlayer attacker) return;
        if (attacker.Player?.WorldData.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator) return;
        if (child) entity.AnimManager.StartAnimation("tantrum");

        // Every grown Faceling within sixteen blocks that can see what happened (or is close) turns on the attacker
        foreach (Entity other in entity.World.GetEntitiesAround(entity.Pos.XYZ, 16, 6, e => e != entity && e.Alive && e.Code.Path.StartsWith("faceling")))
        {
            if (other.Code.Path.EndsWith("child")) continue;
            if (other.Pos.DistanceTo(entity.Pos) > 6 && !Senses.ClearLine(entity.World, Senses.Centre(other), Senses.Centre(entity))) continue;
            Provoke(other, attacker);
        }
        Provoke(entity, attacker);
    }

    /// <summary>Sets an entity hunting someone who wronged it, even where it otherwise would leave them be (a calm level, the city).</summary>
    public static void Provoke(Entity who, Entity attacker)
    {
        var menace = who.GetBehavior<EntityBehaviorMenace>();
        if (menace == null) return;
        menace.Target = attacker;
        menace.Passive = false;
        who.Attributes.SetLong(ProvokedKey, who.World.ElapsedMilliseconds);
        if (menace.Kind != Encounter.Leave) menace.Kind = Encounter.Hunt;
    }

    /// <summary>Whether something was wronged in the last minute and a half, and pays no mind to the safety of a place.</summary>
    public static bool Provoked(Entity who) =>
        who.Attributes.HasAttribute(ProvokedKey) && who.World.ElapsedMilliseconds - who.Attributes.GetLong(ProvokedKey) < 90_000;
}

/// <summary>
/// Turns a Faceling's head and neck, on the client only, toward the player at the screen when they are within a dozen
/// blocks and in front of it: slowly, so that it reads as watching. Nothing is sent over the network.
/// </summary>
public class FacelingHeadController : IHeadController
{
    private const double Range = 12, TurnPerSecond = 1.4, MaxTurn = 1.25; // radians
    private readonly EntityAgent entity;
    private readonly ICoreClientAPI capi;
    private readonly ElementPose head, neck;
    private float yaw;

    public float YawOffset { get; set; }
    public float PitchOffset { get; set; }

    public FacelingHeadController(IAnimationManager animator, EntityAgent entity, ICoreClientAPI capi)
    {
        this.entity = entity;
        this.capi = capi;
        head = animator.Animator.GetPosebyName("Head") ?? throw new InvalidOperationException("no Head");
        neck = animator.Animator.GetPosebyName("Neck") ?? throw new InvalidOperationException("no Neck");
    }

    public void OnFrame(float dt)
    {
        float want = 0;
        Entity player = capi.World.Player?.Entity;
        if (player != null && entity.Alive && player.Pos.DistanceTo(entity.Pos) < Range)
        {
            float toward = (float)Math.Atan2(player.Pos.X - entity.Pos.X, player.Pos.Z - entity.Pos.Z);
            float rel = GameMath.AngleRadDistance(entity.Pos.Yaw, toward);
            // (Something behind it is not watched: it would have to turn round)
            if (Math.Abs(rel) < 2.0f) want = GameMath.Clamp(rel, -(float)MaxTurn, (float)MaxTurn);
        }
        float step = (float)(TurnPerSecond * dt);
        yaw += GameMath.Clamp(want - yaw, -step, step);
        float deg = (yaw + YawOffset) * GameMath.RAD2DEG;
        head.degOffY = deg * 0.6f;
        neck.degOffY = deg * 0.4f;
    }
}

/// <summary>
/// A Faceling child's curiosity: now and then it comes to look at a player, stops a few steps off and watches them,
/// waving perhaps; if they come at it, or run, it runs off. Only while it is going about its own business.
/// </summary>
public class AiTaskCurious : AiTaskBase
{
    private readonly float walkSpeed, runSpeed, seekingRange, keepAway, fleeDistance;
    private EntityBehaviorMenace menace;
    private Entity target;
    private float think, watchedFor, watchFor;
    private long nextLookMs;
    private bool fleeing, waved, moving;
    private string anim;

    public AiTaskCurious(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.016f);
        runSpeed = taskConfig["runSpeed"].AsFloat(0.04f);
        seekingRange = taskConfig["seekingRange"].AsFloat(14);
        keepAway = taskConfig["keepAway"].AsFloat(3.5f);
        fleeDistance = taskConfig["fleeDistance"].AsFloat(2.2f);
    }

    public override bool ShouldExecute()
    {
        // (Asked every tick: the cheap checks first, and the search, with its rays, only twice a second)
        long now = entity.World.ElapsedMilliseconds;
        if (now < cooldownUntilMs || now < nextLookMs) return false;
        nextLookMs = now + 500;
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace == null || menace.Kind != Encounter.Ambient || !PreconditionsSatisfied()) return false;
        target = entity.World.GetNearestEntity(entity.Pos.XYZ, seekingRange, 4, e => e is EntityPlayer p && p.Alive
            && p.Player?.WorldData.CurrentGameMode != EnumGameMode.Spectator && Senses.ClearLine(entity.World, Senses.Centre(entity), Senses.Eyes(p)));
        return target != null;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        fleeing = waved = moving = false;
        watchedFor = 0;
        watchFor = 6 + (float)entity.World.Rand.NextDouble() * 10;
        Approach();
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || target == null || !target.Alive || menace.Kind != Encounter.Ambient) return false;
        think -= dt;
        if (!moving) Face(target.Pos.XYZ, dt);
        if (think > 0) return true;
        think = 0.3f;

        double distance = entity.Pos.DistanceTo(target.Pos);
        if (fleeing) return pathTraverser.Active;
        if (distance > seekingRange + 4) return false;
        bool rushed = distance < fleeDistance || target is EntityAgent agent && Senses.Running(agent) && distance < 8;
        if (rushed)
        {
            Flee();
            return true;
        }
        if (moving && !pathTraverser.Active) SetAnim(null);
        if (!moving)
        {
            if (distance > keepAway + 3) Approach();
            watchedFor += 0.3f;
            if (!waved && watchedFor > 2 && entity.World.Rand.NextDouble() < 0.1)
            {
                waved = true;
                entity.AnimManager.StartAnimation("wave");
            }
            if (watchedFor > watchFor) return false;
        }
        return true;
    }

    private void Approach()
    {
        SetAnim("walk");
        pathTraverser.NavigateTo_Async(target.Pos.XYZ.Clone(), walkSpeed, keepAway, () => SetAnim(null), () => SetAnim(null), () => SetAnim(null), 1500, 1);
    }

    private void Flee()
    {
        fleeing = true;
        double away = Math.Atan2(entity.Pos.Z - target.Pos.Z, entity.Pos.X - target.Pos.X);
        for (int i = 0; i < 6; i++)
        {
            double angle = away + (entity.World.Rand.NextDouble() - 0.5) * (i < 3 ? 1.0 : 2.4);
            int x = (int)Math.Floor(entity.Pos.X + Math.Cos(angle) * 9), z = (int)Math.Floor(entity.Pos.Z + Math.Sin(angle) * 9);
            int y = Senses.FindFloor(entity.World, x, (int)Math.Floor(entity.Pos.Y), z, 2, 4);
            if (y == int.MinValue) continue;
            SetAnim("run");
            pathTraverser.NavigateTo_Async(new Vec3d(x + 0.5, y, z + 0.5), runSpeed, 1, () => SetAnim(null), () => SetAnim(null), () => SetAnim(null), 1500, 1);
            return;
        }
        SetAnim(null);
    }

    private void SetAnim(string code)
    {
        moving = code != null;
        if (anim == code) return;
        if (anim != null) entity.AnimManager.StopAnimation(anim);
        anim = code;
        if (anim != null) entity.AnimManager.StartAnimation(anim);
    }

    private void Face(Vec3d point, float dt)
    {
        float desired = (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        entity.Pos.Yaw = (entity.Pos.Yaw + GameMath.Clamp(delta, -3f * dt, 3f * dt)) % GameMath.TWOPI;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        pathTraverser.Stop();
        SetAnim(null);
    }
}
