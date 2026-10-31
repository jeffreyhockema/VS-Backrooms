using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Needs;

/// <summary>
/// Fatigue and sleep (docs/design/needs/README.md, section 4). Awake hours in the watched tree <see cref="Needs.FatigueTree"/>
/// grow by one a game hour awake (by the calendar, so a changed day length or the sleep clock behave), pause while
/// caffeinated (and land all at once, 8 a cup, when it wears off), and fall while the player sleeps in a bed, by
/// <see cref="Needs.RestPerSleptHour"/> times the bed's quality per slept hour. They set vanilla's <c>tiredness</c> (so its
/// bed gate opens at 24), the walkspeed and stability penalties, and, per slept hour outside a safe place, the chance of a
/// night visit. A sleeper is woken rested, by pain, by something menacing close, or by thirst or hunger.
/// Server side; inert outside Backrooms worlds and in Creative and Spectator. With the setting off it only wakes the
/// sleeper (rested after 8 hours or vanilla tiredness at 0, in the mod's own beds; a vanilla bed rests by its own rule).
/// </summary>
public class EntityBehaviorFatigue : EntityBehavior
{
    public const string Code = "backrooms-fatigue";

    public const string WalkStat = "backrooms:fatigue";

    /// <summary>With fatigue off, how fast the mod's beds lower vanilla tiredness (12 in 8 hours), and the longest sleep.</summary>
    private const float OffRestPerHour = 1.5f, OffSleepHours = 8f;

    private double lastHours = -1;
    private float counter;
    private float lastSynced = -1;
    private double sleptAcc, sleptTotal;
    private string pendingWake;
    private bool cleared;

    public EntityBehaviorFatigue(Entity entity) : base(entity) { }

    public override string PropertyName() => Code;

    public override void Initialize(EntityProperties properties, JsonObject attributes)
    {
        base.Initialize(properties, attributes);
        if (entity.World.Side == EnumAppSide.Server) Needs.FatigueTreeOf(entity);
    }

    public override void AfterInitialized(bool onFirstSpawn)
    {
        base.AfterInitialized(onFirstSpawn);
        if (entity.World.Side != EnumAppSide.Server) return;
        if (entity.GetBehavior<EntityBehaviorHealth>() is { } health) health.onDamaged += OnDamaged;
    }

    private float OnDamaged(float damage, DamageSource source)
    {
        if (damage > 0 && source?.Type != EnumDamageType.Heal && Sleeping(entity)) pendingWake = "pain";
        return damage;
    }

    /// <summary>Whether an entity is asleep in a bed (the mod's or a vanilla one).</summary>
    public static bool Sleeping(Entity entity) => entity is EntityAgent { MountedOn: BlockEntityBed or IRestPlace };

    /// <summary>The bed's quality: the mod's beds say; a vanilla bed's <c>sleepEfficiency</c>, else 0.6.</summary>
    public static float Quality(Entity entity) => (entity as EntityAgent)?.MountedOn switch
    {
        IRestPlace place => place.RestQuality,
        BlockEntityBed bed => bed.Block?.Attributes?["sleepEfficiency"].AsFloat(NeedsMath.DefaultQuality) ?? NeedsMath.DefaultQuality,
        _ => NeedsMath.DefaultQuality,
    };

    public override void OnGameTick(float deltaTime)
    {
        if (entity.World.Side != EnumAppSide.Server || entity is not EntityPlayer player || !player.Alive) return;
        // (Inert outside Backrooms worlds: the beds there are vanilla's own, with vanilla's own wake rules)
        if (!BackroomsWorld.IsBackroomsClimate(entity.World.Config))
        {
            if (!cleared) ClearPenalties();
            pendingWake = null;
            return;
        }
        cleared = false;
        bool exempt = EntityBehaviorThirst.Exempt(player);
        // (Pain wakes at once; the rest is looked at once a second)
        bool sleeping = Sleeping(player);
        if (pendingWake != null)
        {
            if (sleeping && !exempt) Wake(player, pendingWake);
            pendingWake = null;
            sleeping = false;
        }
        counter += deltaTime;
        if (counter < 1f) return;
        float seconds = counter;
        counter = 0;

        IWorldAccessor world = entity.World;
        double now = world.Calendar.TotalHours;
        // (Game hours since the last look; a jump of the clock (/time) counts for at most two hours, or what a full sleep speed
        // can run in the real time between looks: the calendar goes about 2.4 hours a second then)
        double most = Math.Max(2, 1.5 * seconds * world.Calendar.SpeedOfTime * world.Calendar.CalendarSpeedMul / 3600);
        float hours = lastHours < 0 ? 0 : (float)GameMath.Clamp(now - lastHours, 0, most);
        lastHours = now;
        if (!sleeping) sleptAcc = sleptTotal = 0;

        if (sleeping && !exempt && WakeReason(player) is { } reason)
        {
            Wake(player, reason);
            sleeping = false;
        }

        bool on = Needs.FatigueOn(world);
        if (!on || exempt)
        {
            ClearPenalties();
            // With fatigue off the mod's beds rest by vanilla tiredness (vanilla's own beds do it themselves)
            if (sleeping && !on && player.MountedOn is IRestPlace && player.GetBehavior<EntityBehaviorTiredness>() is { } vanilla)
            {
                vanilla.Tiredness = Math.Max(0, vanilla.Tiredness - hours * OffRestPerHour);
                sleptTotal += hours;
                if (vanilla.Tiredness <= 0 || sleptTotal >= OffSleepHours) Wake(player, "rested");
            }
            return;
        }

        ITreeAttribute tree = Needs.FatigueTreeOf(entity);
        float awake = tree.GetFloat("awakeHours", 0);
        bool caffeinated = tree.GetDouble("caffeineUntil", 0) > now;
        float crash = tree.GetFloat("crashHours", 0);
        bool dirty = false;
        if (!caffeinated && crash > 0)
        {
            awake += crash;
            tree.SetFloat("crashHours", 0);
            dirty = true;
            if (player.Player is IServerPlayer crashed) NeedsSystem.Tell(crashed, "backrooms:caffeine-crash");
        }
        if (sleeping)
        {
            awake -= hours * NeedsMath.RestPerHour(Quality(player));
            sleptAcc += hours;
            while (sleptAcc >= 1)
            {
                sleptAcc -= 1;
                if (player.Player is IServerPlayer sleeper && player.MountedOn is BlockEntity bed) NeedsSystem.Instance?.RollNightVisit(sleeper, bed.Pos);
            }
            if (awake <= 0)
            {
                awake = 0;
                Wake(player, "rested");
                sleeping = false;
            }
        }
        else if (!caffeinated) awake += hours;
        awake = GameMath.Clamp(awake, 0, Needs.CapHours);
        tree.SetFloat("awakeHours", awake);

        // The one-time hint, once per stretch awake
        bool hinted = tree.GetBool("hinted");
        if (awake < Needs.DrowsyHours && hinted)
        {
            tree.SetBool("hinted", false);
            dirty = true;
        }
        else if (awake >= Needs.DrowsyHours && !hinted && !sleeping)
        {
            tree.SetBool("hinted", true);
            dirty = true;
            if (player.Player is IServerPlayer drowsy) NeedsSystem.Tell(drowsy, "backrooms:sleep-hint");
        }
        if (dirty || lastSynced < 0 || Math.Abs(awake - lastSynced) >= 0.05f || NeedsMath.Band(awake) != NeedsMath.Band(lastSynced))
        {
            lastSynced = awake;
            entity.WatchedAttributes.MarkPathDirty(Needs.FatigueTree);
        }

        // Vanilla's tiredness follows the awake hours (its bed gate, Tiredness > 8, opens at 24)
        if (player.GetBehavior<EntityBehaviorTiredness>() is { } tiredness)
        {
            float want = NeedsMath.Tiredness(awake);
            if (Math.Abs(tiredness.Tiredness - want) > 0.01f) tiredness.Tiredness = want;
        }
        Needs.SetStat(entity, "walkspeed", WalkStat, NeedsMath.FatigueWalk(awake, caffeinated));
        Needs.SetStabilityOffset(entity, "needs:fatigue", NeedsMath.FatigueStability(awake, caffeinated));
    }

    /// <summary>Why a sleeper wakes now, or null: something menacing close, thirst, hunger.</summary>
    private static string WakeReason(EntityPlayer player)
    {
        if (Needs.MenaceNear(player.World, player.Pos.XYZ)) return "menace";
        // (Vanilla's bed wakes a sleeper when a temporal storm begins, unless the world allows sleeping through one)
        if (player.World.Config.GetString("temporalStormSleeping", "0") == "0"
            && player.World.Api.ModLoader.GetModSystem<SystemTemporalStability>(true)?.StormStrength > 0f) return "storm";
        if (Needs.ThirstOn(player.World) && Needs.HydrationFraction(player) < NeedsMath.WakeFraction) return "thirst";
        if (Needs.SatietyFraction(player) < NeedsMath.WakeFraction) return "hunger";
        return null;
    }

    private void Wake(EntityPlayer player, string reason)
    {
        sleptAcc = sleptTotal = 0;
        if (!player.TryUnmount()) return;
        if (player.Player is IServerPlayer woken) NeedsSystem.Tell(woken, "backrooms:woke-" + reason);
    }

    /// <summary>Respawn: half rested, no caffeine.</summary>
    public override void OnEntityReceiveDamage(DamageSource damageSource, ref float damage)
    {
        if (entity.World.Side != EnumAppSide.Server) return;
        if (damageSource.Type == EnumDamageType.Heal && damageSource.Source == EnumDamageSource.Revive)
        {
            ITreeAttribute tree = Needs.FatigueTreeOf(entity);
            tree.SetFloat("awakeHours", Needs.RespawnAwakeHours);
            tree.SetDouble("caffeineUntil", 0);
            tree.SetFloat("crashHours", 0);
            entity.WatchedAttributes.MarkPathDirty(Needs.FatigueTree);
        }
    }

    private void ClearPenalties()
    {
        cleared = true;
        Needs.SetStat(entity, "walkspeed", WalkStat, 0);
        Needs.SetStabilityOffset(entity, "needs:fatigue", 0);
    }
}
