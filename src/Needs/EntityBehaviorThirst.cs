using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.Server;

namespace Backrooms.Needs;

/// <summary>Thirst's damage: "died of thirst" (see <see cref="NeedsSystem"/>, which words the death message).</summary>
public class ThirstDamageSource : DamageSource
{
    public string PlayerName;
}

/// <summary>
/// Thirst (docs/design/needs/README.md, section 3). The player's hydration, 0..1500 in the watched tree
/// <see cref="Needs.ThirstTree"/>, drains as vanilla hunger's satiety does (1 a real second moving, 1.5 more a sprinting
/// second, a quarter of that when idle for over 3 s, times the calendar's speed and the <c>thirstrate</c> stat). Below
/// 40% it slows the player, at empty it hurts (0.2 every 6 s) and costs 0.2 stability. Gut rot (<see cref="Needs.MakeSick"/>)
/// is kept here too. Server side; inert outside Backrooms worlds, with the setting off, and in Creative and Spectator.
/// </summary>
public class EntityBehaviorThirst : EntityBehavior
{
    public const string Code = "backrooms-thirst";

    /// <summary>Stat codes this behaviour sets.</summary>
    public const string WalkStat = "backrooms:thirst", SickStat = "backrooms:sick";

    private float counter, sprintCounter, damageCounter, syncCounter;
    private long lastMoveMs;
    private float lastSynced = -1;

    public EntityBehaviorThirst(Entity entity) : base(entity) { }

    public override string PropertyName() => Code;

    public override void Initialize(EntityProperties properties, JsonObject attributes)
    {
        base.Initialize(properties, attributes);
        // (Old saves and new players start full; the client gets the tree by sync)
        if (entity.World.Side == EnumAppSide.Server) Needs.ThirstTreeOf(entity);
    }

    public override void OnGameTick(float deltaTime)
    {
        if (entity.World.Side != EnumAppSide.Server || entity is not EntityPlayer player || !player.Alive) return;
        if (player.Controls is { } controls)
        {
            if (controls.TriesToMove || controls.Jump || controls.LeftMouseDown || controls.RightMouseDown) lastMoveMs = entity.World.ElapsedMilliseconds;
            if (controls.TriesToMove && controls.Sprint) sprintCounter += deltaTime;
        }
        counter += deltaTime;
        if (counter < 1f) return;
        float seconds = counter, sprint = sprintCounter;
        counter = sprintCounter = 0;

        ApplySickness(entity);
        if (!Needs.ThirstOn(entity.World) || Exempt(player))
        {
            ClearPenalties();
            return;
        }

        IWorldAccessor world = entity.World;
        float calendar = world.Calendar.SpeedOfTime * world.Calendar.CalendarSpeedMul / 30f;
        bool idle = world.ElapsedMilliseconds - lastMoveMs > NeedsMath.IdleAfterMs;
        float drain = NeedsMath.Drain(seconds, sprint, idle, calendar, entity.Stats.GetBlended("thirstrate"));
        ITreeAttribute tree = Needs.ThirstTreeOf(entity);
        float was = tree.GetFloat("hydration", Needs.MaxHydration);
        float now = Math.Max(0, was - Math.Max(0, drain));
        tree.SetFloat("hydration", now);
        // (Synced every few seconds, or at once on reaching empty, rather than every second)
        syncCounter += seconds;
        if (syncCounter >= 3 || now <= 0 && was > 0 || lastSynced < 0 || Math.Abs(now - lastSynced) >= 10)
        {
            syncCounter = 0;
            lastSynced = now;
            entity.WatchedAttributes.MarkPathDirty(Needs.ThirstTree);
        }

        float fraction = now / Needs.MaxHydration;
        Needs.SetStat(entity, "walkspeed", WalkStat, NeedsMath.ThirstWalk(fraction));
        bool empty = now <= 0;
        Needs.SetStabilityOffset(entity, "needs:thirst", empty ? NeedsMath.EmptyStability : 0);
        if (!empty)
        {
            damageCounter = 0;
            return;
        }
        damageCounter += seconds;
        if (damageCounter < NeedsMath.EmptyDamageSeconds) return;
        damageCounter = 0;
        entity.ReceiveDamage(new ThirstDamageSource
        {
            Source = EnumDamageSource.Internal,
            Type = EnumDamageType.Poison,
            PlayerName = player.Player?.PlayerName,
        }, NeedsMath.EmptyDamage);
    }

    /// <summary>Respawn: half full, as vanilla does with food.</summary>
    public override void OnEntityReceiveDamage(DamageSource damageSource, ref float damage)
    {
        if (entity.World.Side != EnumAppSide.Server) return;
        if (damageSource.Type == EnumDamageType.Heal && damageSource.Source == EnumDamageSource.Revive)
        {
            Needs.SetHydration(entity, Needs.MaxHydration / 2);
            damageCounter = 0;
        }
    }

    public override void OnEntityDespawn(EntityDespawnData despawn)
    {
        base.OnEntityDespawn(despawn);
        if (entity.World.Side == EnumAppSide.Server) Needs.ForgetOffsets(entity.EntityId);
    }

    private void ClearPenalties()
    {
        Needs.SetStat(entity, "walkspeed", WalkStat, 0);
        Needs.SetStabilityOffset(entity, "needs:thirst", 0);
        damageCounter = 0;
    }

    /// <summary>Gut rot's stats, on or off by its clock (thirstrate counts only while thirst is on, hungerrate always).</summary>
    internal static void ApplySickness(Entity entity)
    {
        float extra = Needs.IsSick(entity) ? NeedsMath.SickRate : 0;
        Needs.SetStat(entity, "hungerrate", SickStat, extra);
        Needs.SetStat(entity, "thirstrate", SickStat, extra);
    }

    internal static bool Exempt(EntityPlayer player) =>
        player.Player?.WorldData?.CurrentGameMode is EnumGameMode.Creative or EnumGameMode.Spectator;
}
