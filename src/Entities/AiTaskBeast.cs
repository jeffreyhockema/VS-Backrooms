using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// The Beast of Level 5 as a gentleman (<see cref="BeastSystem"/>): what he does once he has come.
/// <list type="bullet">
/// <item>Glimpse: he stands at the edge of someone's sight, watching, and is gone the moment they turn to him (or after
/// a few seconds).</item>
/// <item>Otherwise, the offer: he comes in a burst of flame, greets them, and holds out his hand, walking slowly up to
/// them. The offer is answered by:
///   <list type="bullet">
///   <item>a handshake (right-click him; <see cref="EntityBeast"/>): the deal;</item>
///   <item>holding his gaze, standing your ground and not running, for a few seconds in all: he is startled, stands
///   frozen and trembling, then is gone;</item>
///   <item>anything else is a refusal: striking him, walking off (out of sight for a few seconds, or a dozen blocks
///   away), or letting the offer lapse. He unveils, and hunts.</item>
///   </list>
/// When he comes to collect a debt there is no offer: holding his gaze still startles him (and frees you); the rest
/// is a refusal.</item>
/// </list>
/// Nothing hurts him in this form (EntityBehaviorMenace "immortal", "unmoved": a blow is only noted).
/// </summary>
public class AiTaskBeast : AiTaskBase
{
    private enum State { None, Glimpse, Offer, Shocked, Done }

    private readonly float walkSpeed, offerSeconds, stareSeconds, shockedSeconds, refuseDistance, lostSightSeconds;

    private EntityBehaviorMenace menace;
    private State state;
    private float think, sinceThink, stared, lostSight, elapsed, shockedFor;
    private long startMs, lastPathMs;
    private bool walking;

    public AiTaskBeast(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        walkSpeed = taskConfig["walkSpeed"].AsFloat(0.006f);
        offerSeconds = taskConfig["offerSeconds"].AsFloat(24);
        stareSeconds = taskConfig["stareSeconds"].AsFloat(5);
        shockedSeconds = taskConfig["shockedSeconds"].AsFloat(8);
        refuseDistance = taskConfig["refuseDistance"].AsFloat(13);
        lostSightSeconds = taskConfig["lostSightSeconds"].AsFloat(4);
    }

    public override bool ShouldExecute()
    {
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        return menace != null && menace.Kind is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Leave && state != State.Done;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        if (state != State.None) return;
        startMs = entity.World.ElapsedMilliseconds;
        Entity target = menace.Target;
        if (menace.Kind == Encounter.Glimpse)
        {
            state = State.Glimpse;
            return;
        }
        if (menace.Kind == Encounter.Leave || target == null)
        {
            Finish(flash: false);
            return;
        }
        state = State.Offer;
        BeastSystem.Manifest(entity);
        BeastSystem.Greet(entity, target);
        if (target is EntityPlayer player && !entity.Attributes.GetBool(BeastSystem.CollectKey))
            entity.WatchedAttributes.SetString(BeastSystem.OfferKey, player.PlayerUID);
        entity.AnimManager.StartAnimation("offer");
        Strike.Log(entity, "makes his offer");
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || state == State.Done) return false;
        Entity target = menace.Target;
        if (state == State.Offer || state == State.Glimpse) Face(target);
        think -= dt;
        sinceThink += dt;
        if (think > 0) return true;
        think = 0.2f;
        // (The counters are in real seconds: a pass comes a tick or more after the nominal 0.2 s)
        float step = sinceThink;
        sinceThink = 0;
        elapsed += step;

        if (target == null || !target.Alive)
        {
            Finish(flash: true);
            return false;
        }
        double distance = entity.Pos.DistanceTo(target.Pos);
        Vec3d head = entity.Pos.XYZ.Add(0, entity.LocalEyePos.Y, 0);
        bool inSight = Senses.ClearLine(entity.World, Senses.Eyes(target), head);
        bool looking = inSight && Senses.LooksAt(target, head, 14);

        switch (state)
        {
            case State.Glimpse:
                // Out of the corner of the eye: turn to him and he is gone
                if (inSight && Senses.AngleTo(target, head) < 30 || elapsed > 3.5f || menace.Kind == Encounter.Leave) Finish(flash: false);
                return true;

            case State.Shocked:
                shockedFor += step;
                if (shockedFor >= shockedSeconds) Finish(flash: true);
                return true;

            case State.Offer:
                // The offer was taken (EntityBeast: the handshake sends him to Leave)
                if (menace.Kind == Encounter.Leave)
                {
                    Walk(false);
                    pathTraverser.Stop();
                    state = State.Done;
                    return false;
                }
                // Struck: a refusal
                if (entity.Attributes.GetLong(EntityBehaviorMenace.StruckKey, 0) > startMs)
                {
                    Refuse(target, "struck");
                    return false;
                }
                // Held in a steady gaze by someone who stands their ground: he is startled
                if (looking && !(target is EntityAgent agent && Senses.Running(agent)))
                {
                    stared += step;
                    if (stared >= stareSeconds)
                    {
                        Shock(target);
                        return true;
                    }
                }
                lostSight = inSight ? 0 : lostSight + step;
                if (distance > refuseDistance || lostSight > lostSightSeconds || elapsed > offerSeconds)
                {
                    Refuse(target, distance > refuseDistance ? "walked away" : lostSight > lostSightSeconds ? "out of sight" : "lapsed");
                    return false;
                }
                // He walks slowly up to them, hand held out, and waits within reach
                if (distance > 2.4)
                {
                    long now = entity.World.ElapsedMilliseconds;
                    if (!pathTraverser.Active || now - lastPathMs > 1500)
                    {
                        lastPathMs = now;
                        Walk(true);
                        pathTraverser.NavigateTo_Async(target.Pos.XYZ.Clone(), walkSpeed, 2.0f, () => Walk(false), () => Walk(false), () => Walk(false), 1500, 1);
                    }
                }
                else if (walking)
                {
                    pathTraverser.Stop();
                    Walk(false);
                }
                return true;
        }
        return true;
    }

    private void Face(Entity target)
    {
        if (target == null || walking) return;
        entity.Pos.Yaw = (float)Math.Atan2(target.Pos.X - entity.Pos.X, target.Pos.Z - entity.Pos.Z);
    }

    private void Walk(bool on)
    {
        if (on == walking) return;
        walking = on;
        if (on) entity.AnimManager.StartAnimation("walk");
        else entity.AnimManager.StopAnimation("walk");
    }

    private void Shock(Entity target)
    {
        state = State.Shocked;
        pathTraverser.Stop();
        Walk(false);
        entity.WatchedAttributes.RemoveAttribute(BeastSystem.OfferKey);
        entity.AnimManager.StopAnimation("offer");
        entity.AnimManager.StartAnimation("shocked");
        BeastSystem.Confronted(entity, target);
    }

    private void Refuse(Entity target, string why)
    {
        state = State.Done;
        pathTraverser.Stop();
        Walk(false);
        entity.WatchedAttributes.RemoveAttribute(BeastSystem.OfferKey);
        Strike.Log(entity, "the offer refused ({0})", why);
        BeastSystem.Unveil(entity, target);
    }

    private void Finish(bool flash)
    {
        state = State.Done;
        pathTraverser.Stop();
        Walk(false);
        entity.WatchedAttributes.RemoveAttribute(BeastSystem.OfferKey);
        Strike.Log(entity, "gone{0}", flash ? " in a flash" : "");
        BeastSystem.Vanish(entity, flash);
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        Walk(false);
    }
}
