using System;
using Backrooms.Notes;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// A Faceling greeted (right-clicked, see <see cref="EntityBehaviorFaceling"/>): it stops where it is and turns to
/// whoever greeted it, and waves; then turns, the whole body, toward the nearest gate out of the level it knows of
/// (within <see cref="SearchRadius"/> blocks), points down that bearing and holds it a moment, turns back and nods. The
/// one it greeted is told in chat which way it pointed and roughly how far. If it knows of no gate it shrugs. A child
/// only waves.
///
/// As a task of its own, above the wander and the idle gestures, nothing else turns it or walks it off meanwhile
/// (the old greeting stopped the other tasks, and the next tick they started again: it was turned and walked off
/// mid-wave and pointed wherever it then faced). Only fleeing (Hounds) and being hurt come before it.
/// </summary>
public class AiTaskGreet : AiTaskBase
{
    private enum Step { Wave, TurnToWay, Point, TurnBack, Nod, Shrug }

    /// <summary>How far a Faceling knows its way about (it was 400 before 0.514.0, too little for much of Level 1).</summary>
    public const int SearchRadius = 800;

    // Seconds each gesture takes (the shape's frames at the speeds the entity file plays them: wave 80 at 0.8,
    // point 90 at 0.8, nod 60 at 0.9, shrug 50 at 1)
    private const float WaveSeconds = 2.9f, ChildWaveSeconds = 3.3f, PointSeconds = 3.6f, NodSeconds = 2.3f, ShrugSeconds = 1.9f;
    private const double GreeterRange = 20;

    private readonly bool child;
    private EntityBehaviorMenace menace;
    private Entity greeter, asked;
    private long askedAtMs = -1;
    private Step step;
    private float stepTime;
    private Way way;
    private string playing;

    /// <summary>Whether it is greeting someone now.</summary>
    public bool Busy { get; private set; }

    public AiTaskGreet(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        child = entity.Code.Path.EndsWith("child", StringComparison.Ordinal);
    }

    /// <summary>Asks it to greet someone (null for nobody in particular, from a test): it does on its next tick, if nothing more pressing is going on.</summary>
    public void Ask(Entity by)
    {
        asked = by;
        askedAtMs = entity.World.ElapsedMilliseconds;
    }

    public override bool ShouldExecute()
    {
        if (askedAtMs < 0) return false;
        // (Asked while it was running from a Hound, or set on someone: the moment passes)
        if (entity.World.ElapsedMilliseconds - askedAtMs > 1500 || !entity.Alive)
        {
            Log("greeting not taken up");
            askedAtMs = -1;
            return false;
        }
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        return menace == null || menace.Kind == Encounter.Ambient;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        Busy = true;
        greeter = asked;
        asked = null;
        askedAtMs = -1;
        pathTraverser.Stop();
        entity.Controls.StopAllMovement();
        way = child ? null : FindWay(entity);
        if (child) Log("greeted by {0}: waves (a child)", Who(greeter));
        else if (way != null)
            Log("greeted by {0}: gate at {1},{2} (to Level {3}), {4:0} blocks off, bearing {5:0} ({6}); waves, then points",
                Who(greeter), way.X, way.Z, way.To, way.Distance, way.BearingDeg, way.Dir);
        else Log("greeted by {0}: knows of no gate within {1} blocks; waves, then shrugs", Who(greeter), SearchRadius);
        Play("wave");
        Go(Step.Wave);
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive) return false;
        stepTime += dt;
        entity.Controls.StopAllMovement();
        bool greeterNear = greeter != null && greeter.Alive && greeter.Pos.DistanceTo(entity.Pos) < GreeterRange;
        switch (step)
        {
            case Step.Wave:
                if (greeterNear) Turn(YawTo(greeter.Pos.XYZ), 4f, dt);
                if (stepTime < (child ? ChildWaveSeconds : WaveSeconds)) return true;
                if (child) return false;
                Stop();
                if (way != null) Go(Step.TurnToWay);
                else
                {
                    Play("shrug");
                    Tell(greeter, "backrooms:faceling-shrugs");
                    Go(Step.Shrug);
                }
                return true;

            case Step.TurnToWay:
                // The whole body round to the bearing, then the arm up along it
                if (Turn(way.Yaw, 2.6f, dt) > 0.05f && stepTime < 2.5f) return true;
                entity.Pos.Yaw = way.Yaw;
                Play("point");
                Tell(greeter, "backrooms:faceling-points", "backrooms:dir-" + way.Dir, way.Distance < 96 ? "backrooms:faceling-near" : way.Distance < 224 ? "backrooms:faceling-mid" : "backrooms:faceling-far");
                Go(Step.Point);
                return true;

            case Step.Point:
                entity.Pos.Yaw = way.Yaw;
                if (stepTime < PointSeconds) return true;
                Stop();
                Go(Step.TurnBack);
                return true;

            case Step.TurnBack:
                // A nod back at whoever asked, after: too long, as they do
                if (greeterNear && Turn(YawTo(greeter.Pos.XYZ), 3f, dt) > 0.1f && stepTime < 1.5f) return true;
                Play("nod");
                Go(Step.Nod);
                return true;

            case Step.Nod:
                if (greeterNear) Turn(YawTo(greeter.Pos.XYZ), 2f, dt);
                return stepTime < NodSeconds;

            case Step.Shrug:
                if (greeterNear) Turn(YawTo(greeter.Pos.XYZ), 3f, dt);
                return stepTime < ShrugSeconds;
        }
        return false;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        // (Cut short by a Hound or a blow: leave no arm in the air. A gesture that ran its course is left to ease out)
        if (cancelled) Stop();
        Log(cancelled ? "greeting cut short at {0}" : "greeting done", step);
        playing = null;
        greeter = null;
        Busy = false;
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

    /// <summary>Turns toward a yaw at no more than <paramref name="ratePerSecond"/>; returns how far there is still to turn.</summary>
    private float Turn(float desired, float ratePerSecond, float dt)
    {
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float by = GameMath.Clamp(delta, -ratePerSecond * dt, ratePerSecond * dt);
        entity.Pos.Yaw = GameMath.Mod(entity.Pos.Yaw + by, GameMath.TWOPI);
        return Math.Abs(delta - by);
    }

    /// <summary>Says a lang entry to a player in that player's own language (the server's language is not theirs); the arguments are lang keys too.</summary>
    private static void Tell(Entity who, string key, params string[] argKeys)
    {
        if (who is not EntityPlayer { Player: IServerPlayer player }) return;
        object[] args = new object[argKeys.Length];
        for (int i = 0; i < args.Length; i++) args[i] = Lang.GetL(player.LanguageCode, argKeys[i]);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.GetL(player.LanguageCode, key, args), EnumChatType.Notification);
    }

    private static string Who(Entity e) => e == null ? "nobody" : e is EntityPlayer p ? p.Player?.PlayerName ?? "a player" : e.Code.Path + " #" + e.EntityId;

    private void Log(string format, params object[] args) => Strike.Log(entity, format, args);

    // ================= The way it knows =================

    /// <summary>The nearest gate a Faceling knows of: where, which way it lies (as a yaw to face and a compass bearing), and how far.</summary>
    public sealed record Way(int X, int Z, int To, double Distance, float Yaw, double BearingDeg, string Dir);

    /// <summary>The nearest gate out of the level within <see cref="SearchRadius"/> blocks of an entity, or null (and null outside a Backrooms world).</summary>
    public static Way FindWay(Entity entity)
    {
        WorldLayout layout = entity.Api.ModLoader.GetModSystem<MenaceSystem>()?.Layout;
        if (layout == null) return null;
        int x = (int)Math.Floor(entity.Pos.X), z = (int)Math.Floor(entity.Pos.Z);
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
        if (layout.NearestGate(x, z, level, SearchRadius) is not { } gate) return null;
        double dx = gate.X + 0.5 - entity.Pos.X, dz = gate.Z + 0.5 - entity.Pos.Z;
        // (Yaw as the game has it, from +z toward +x; bearing as a compass, 0 north (-z), 90 east)
        float yaw = GameMath.Mod((float)Math.Atan2(dx, dz), GameMath.TWOPI);
        double bearing = (Math.Atan2(dx, -dz) * 180 / Math.PI + 360) % 360;
        return new Way(gate.X, gate.Z, gate.To, Math.Sqrt(dx * dx + dz * dz), yaw, bearing, MarkResolver.Direction(dx, dz));
    }
}
