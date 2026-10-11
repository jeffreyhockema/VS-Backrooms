using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>
/// Every Backrooms entity carries one: who it was put down for, what it is there to do (see <see cref="Encounter"/>),
/// and when to go. It ends encounters that have run their course, despawns entities out of sight once they leave,
/// and makes the ones that cannot be killed (Smilers) withdraw when hurt instead.
///
/// Nothing it watches over is kept with the world: an entity loaded back from a save is gone at once, and the director
/// puts down new ones as needed.
/// </summary>
public class EntityBehaviorMenace : EntityBehavior
{
    private const string KindKey = "backrooms:kind", OwnerKey = "backrooms:owner", PassiveKey = "backrooms:passive";
    private const string BornKey = "backrooms:born", SessionKey = "backrooms:session";
    private const string UntilKey = "backrooms:untilHours", ShiftKey = "backrooms:duringShift", SinceKey = "backrooms:kindSinceMs";
    /// <summary>Set on an entity another of its pack called to the hunt, so it does not announce the hunt again.</summary>
    public const string RalliedKey = "backrooms:rallied";
    /// <summary>What a Duller took; dropped where it goes.</summary>
    public const string StolenKey = "backrooms:stolen";
    /// <summary>When (elapsed ms) something last struck an unkillable thing that does not withdraw (the Mangled).</summary>
    public const string StruckKey = "backrooms:struckMs";

    /// <summary>Different every time a server starts, so entities saved with the world can be told apart.</summary>
    private static string Session = Guid.NewGuid().ToString("N");

    /// <summary>Called when a server starts: a new session, and nothing remembered from the last one.</summary>
    public static void NewSession()
    {
        Session = Guid.NewGuid().ToString("N");
        Wards.Invalidate();
        AlmondWater.Invalidate();
    }

    private bool immortal, unmoved;
    private int glimpseSeconds, stalkSeconds, huntSeconds;
    private float checkIn;
    private long leftAtMs, lastSeenMs;

    public EntityBehaviorMenace(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-menace";

    public override void Initialize(EntityProperties properties, JsonObject attributes)
    {
        base.Initialize(properties, attributes);
        immortal = attributes["immortal"].AsBool(false);
        unmoved = attributes["unmoved"].AsBool(false);
        glimpseSeconds = attributes["glimpseSeconds"].AsInt(30);
        stalkSeconds = attributes["stalkSeconds"].AsInt(150);
        huntSeconds = attributes["huntSeconds"].AsInt(180);
    }

    /// <summary>Marks a new entity, before it is spawned, as put down for a target and an encounter.</summary>
    public static void Prepare(Entity entity, Entity target, Encounter kind, bool passive, long now, double untilHours = -1, bool duringShift = false)
    {
        // Some encounters last only while something else does: a Level 1 Flickering, a Reality Shift
        entity.Attributes.SetDouble(UntilKey, untilHours);
        entity.Attributes.SetBool(ShiftKey, duringShift);
        entity.Attributes.SetInt(KindKey, (int)kind);
        entity.Attributes.SetLong(SinceKey, now);
        entity.Attributes.SetLong(OwnerKey, target.EntityId);
        entity.Attributes.SetBool(PassiveKey, passive);
        entity.Attributes.SetLong(BornKey, now);
        entity.Attributes.SetString(SessionKey, Session);
    }

    public static Encounter KindOf(Entity entity) => (Encounter)entity.Attributes.GetInt(KindKey, -1);

    public static long OwnerOf(Entity entity) => entity.Attributes.GetLong(OwnerKey, -1);

    /// <summary>What the entity is doing; setting it to Leave sends it away.</summary>
    public Encounter Kind
    {
        get => KindOf(entity);
        set
        {
            if (value == Kind) return;
            entity.Attributes.SetInt(KindKey, (int)value);
            entity.Attributes.SetLong(SinceKey, entity.World.ElapsedMilliseconds);
            if (value == Encounter.Leave) leftAtMs = entity.World.ElapsedMilliseconds;
        }
    }

    /// <summary>Level 11: leaves people alone unless they start something.</summary>
    public bool Passive
    {
        get => entity.Attributes.GetBool(PassiveKey);
        set => entity.Attributes.SetBool(PassiveKey, value);
    }

    /// <summary>Who it was put down for (a player, or a straw dummy in tests).</summary>
    public Entity Target
    {
        get
        {
            long id = OwnerOf(entity);
            return id < 0 ? null : entity.World.GetEntityById(id);
        }
        set => entity.Attributes.SetLong(OwnerKey, value?.EntityId ?? -1);
    }

    public long AgeMs => entity.World.ElapsedMilliseconds - entity.Attributes.GetLong(BornKey);

    /// <summary>How long the entity has been doing what it is doing now.</summary>
    public long PhaseMs => entity.World.ElapsedMilliseconds - entity.Attributes.GetLong(SinceKey, entity.Attributes.GetLong(BornKey));

    public bool Immortal => immortal;

    public override void OnGameTick(float dt)
    {
        if (entity.World.Side != EnumAppSide.Server || !entity.Alive) return;
        checkIn -= dt;
        if (checkIn > 0) return;
        checkIn = 1;

        // Loaded back from a save: not ours to keep
        if (entity.Attributes.GetString(SessionKey) != Session)
        {
            Despawn();
            return;
        }

        Entity target = Target;
        Vec3d pos = entity.Pos.XYZ;
        bool anyoneNear = entity.World.GetNearestEntity(pos, 72, 48, e => e is EntityPlayer p && p.Alive) != null;
        if (!anyoneNear && target?.WatchedAttributes.GetBool("backrooms:testTarget") != true)
        {
            Despawn();
            return;
        }
        if (target == null || !target.Alive)
        {
            Kind = Kind == Encounter.Ambient ? Encounter.Ambient : Encounter.Leave;
        }

        if (Kind is not (Encounter.Ambient or Encounter.Leave))
        {
            double until = entity.Attributes.GetDouble(UntilKey, -1);
            if (until > 0 && entity.World.Calendar.TotalHours > until) Kind = Encounter.Leave;
            if (entity.Attributes.GetBool(ShiftKey) && (entity.Api.ModLoader.GetModSystem<Reality.RealitySystem>()?.ShiftStrength ?? 0) <= 0) Kind = Encounter.Leave;
        }

        long now = entity.World.ElapsedMilliseconds;
        bool seen = SeenByAnyone(48);
        if (seen) lastSeenMs = now;

        switch (Kind)
        {
            case Encounter.Ambient:
                // Wanderers drift off once nobody is near, and are never pulled out of sight of anyone
                if (!seen && entity.World.GetNearestEntity(pos, 56, 32, e => e is EntityPlayer p && p.Alive) == null) Despawn();
                break;
            case Encounter.Glimpse:
                if (PhaseMs > glimpseSeconds * 1000) Kind = Encounter.Leave;
                break;
            case Encounter.Stalk:
                if (PhaseMs > stalkSeconds * 1000) Kind = Encounter.Leave;
                break;
            case Encounter.Hunt:
                if (PhaseMs > huntSeconds * 1000) Kind = Encounter.Leave;
                break;
            case Encounter.Leave:
                // Gone the moment nobody is looking, or once far enough off and out of sight
                double away = target == null ? 99 : target.Pos.DistanceTo(pos);
                if (now - lastSeenMs > 1500 || away > 30 && !seen || now - leftAtMs > 20_000) Despawn();
                break;
        }
    }

    /// <summary>Whether any player could see this entity right now.</summary>
    public bool SeenByAnyone(double range)
    {
        foreach (Entity e in entity.World.GetEntitiesAround(entity.Pos.XYZ, (float)range, (float)range, e => e is EntityPlayer p && p.Alive && p.Player?.WorldData.CurrentGameMode != EnumGameMode.Spectator))
        {
            if (Senses.Sees(e, entity, range)) return true;
        }
        Entity target = Target;
        return target != null && target.WatchedAttributes.GetBool("backrooms:testTarget") && Senses.Sees(target, entity, range);
    }

    public override void OnEntityReceiveDamage(DamageSource damageSource, ref float damage)
    {
        if (entity.World.Side != EnumAppSide.Server) return;
        Entity cause = damageSource.GetCauseEntity();
        if (immortal && damageSource.Type != EnumDamageType.Heal)
        {
            // Smilers cannot be killed: struck, they withdraw into the dark. The Mangled is not even moved by it
            damage = 0;
            if (cause != null && unmoved) entity.Attributes.SetLong(StruckKey, entity.World.ElapsedMilliseconds);
            else if (cause != null) Kind = Encounter.Leave;
            return;
        }
        if (cause is EntityPlayer && Passive) Passive = false;
    }

    public void Despawn()
    {
        DropStolen();
        if (entity.Alive) entity.Die(EnumDespawnReason.Expire);
    }

    public override void OnEntityDeath(DamageSource damageSourceForDeath)
    {
        if (entity.World.Side == EnumAppSide.Server)
        {
            DropStolen();
            if (damageSourceForDeath?.GetCauseEntity() is EntityPlayer killer) Rewards.Bounty(entity, killer);
        }
        base.OnEntityDeath(damageSourceForDeath);
    }

    /// <summary>Leaves whatever a Duller took lying where it was when it went.</summary>
    private void DropStolen()
    {
        ItemStack stolen = entity.Attributes.GetItemstack(StolenKey);
        if (stolen == null) return;
        entity.Attributes.RemoveAttribute(StolenKey);
        stolen.ResolveBlockOrItem(entity.World);
        entity.World.SpawnItemEntity(stolen, entity.Pos.XYZ.Add(0, 0.3, 0));
    }
}
