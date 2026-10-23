using System;
using System.Linq;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

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
    /// <summary>When (elapsed ms) the entity first stopped being Ambient; never reset by a later change of kind (the encounter's budget).</summary>
    public const string EncounterSinceKey = "backrooms:encounterSinceMs";
    /// <summary>When (elapsed ms) something last struck an unkillable thing that does not withdraw (the Mangled).</summary>
    public const string StruckKey = "backrooms:struckMs";
    /// <summary>Calendar hours until which a Skin-Stealer is fed (and docile); absent or past: hungry. New in the AI overhaul, read with a default.</summary>
    public const string FedKey = "backrooms:fedUntilHours";
    /// <summary>Until when (elapsed ms) a Duller, hard to catch, can be hurt by a player: its grab and a moment after it.</summary>
    public const string CatchableKey = "backrooms:catchableUntilMs";

    /// <summary>Different every time a server starts, so entities saved with the world can be told apart.</summary>
    private static string Session = Guid.NewGuid().ToString("N");

    /// <summary>Called when a server starts: a new session, and nothing remembered from the last one.</summary>
    public static void NewSession()
    {
        Session = Guid.NewGuid().ToString("N");
        Wards.Reset();
        AlmondWater.Invalidate();
    }

    private bool immortal, unmoved;
    private int glimpseSeconds, stalkSeconds, huntSeconds, investigateSeconds, searchSeconds, maxEncounterSeconds;
    /// <summary>Bleeds clear (a Skin-Stealer: a pale burst of particles when struck), cannot be hurt by players but in its window (a Duller), and the looks (texture indices) that never bite (Level 2's bald rats).</summary>
    private bool bleedsClear, hardToCatch;
    private int[] harmlessLooks = Array.Empty<int>();
    /// <summary>What a fed (docile) Skin-Stealer says now and then, standing about.</summary>
    private AssetLocation[] fedVoices = Array.Empty<AssetLocation>();
    private float nextFedVoice = 10;
    private float checkIn;
    /// <summary>What damage from an arrow, a thrown spear or any other projectile is multiplied by (the Watch: "ranged weapons work on them").</summary>
    private float rangedDamageMul = 1;
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
        investigateSeconds = attributes["investigateCapSeconds"].AsInt(30);
        searchSeconds = attributes["searchCapSeconds"].AsInt(40);
        maxEncounterSeconds = attributes["maxEncounterSeconds"].AsInt(0);
        bleedsClear = attributes["bleedsClear"].AsBool(false);
        hardToCatch = attributes["hardToCatch"].AsBool(false);
        harmlessLooks = attributes["harmlessLooks"].AsArray(Array.Empty<int>());
        fedVoices = Array.ConvertAll(attributes["fedVoices"].AsArray(Array.Empty<string>()),
            code => AssetLocation.Create(code, "backrooms").WithPathPrefixOnce("sounds/"));
        rangedDamageMul = attributes["rangedDamageMul"].AsFloat(1);
    }

    public override void AfterInitialized(bool onFirstSpawn)
    {
        base.AfterInitialized(onFirstSpawn);
        // The Duller takes no damage from players but in the window of its grab (before the health behaviour applies it)
        if (hardToCatch && entity.World.Side == EnumAppSide.Server && entity.GetBehavior<EntityBehaviorHealth>() is { } health)
            health.onDamaged += (damage, source) => HardToCatch(damage, source);
    }

    private float HardToCatch(float damage, DamageSource source)
    {
        if (damage <= 0 || source.Type == EnumDamageType.Heal) return damage;
        Entity by = source.GetCauseEntity();
        if (by is not EntityPlayer && !Senses.IsTestTarget(by)) return damage;
        return entity.World.ElapsedMilliseconds <= entity.Attributes.GetLong(CatchableKey, 0) ? damage : 0;
    }

    /// <summary>Whether this one is fed (a Skin-Stealer within its day of a kill: docile).</summary>
    public bool Fed => entity.Attributes.GetDouble(FedKey, 0) > entity.World.Calendar.TotalHours;

    /// <summary>Feeds it for this many in-game hours.</summary>
    public void Feed(double hours) => entity.Attributes.SetDouble(FedKey, entity.World.Calendar.TotalHours + hours);

    /// <summary>Hungry again at once (a test).</summary>
    public void Starve() => entity.Attributes.RemoveAttribute(FedKey);

    /// <summary>Whether its look is one that never bites (Level 2's hairless rats).</summary>
    public bool Harmless => harmlessLooks.Length > 0 && Array.IndexOf(harmlessLooks, entity.WatchedAttributes.GetInt("textureIndex", 0)) >= 0;

    /// <summary>A hard-to-catch one can be hurt by a player for this long from now (a Duller's grab).</summary>
    public void OpenCatchWindow(long ms) => entity.Attributes.SetLong(CatchableKey, entity.World.ElapsedMilliseconds + ms);

    /// <summary>The pale, translucent burst a Skin-Stealer bleeds instead of blood: "blood runs clear, don't get near".</summary>
    private void BleedClear()
    {
        Vec3d at = Senses.Centre(entity);
        var burst = new SimpleParticleProperties(10, 16, ColorUtil.ToRgba(140, 238, 246, 250),
            at.AddCopy(-0.2, -0.15, -0.2), at.AddCopy(0.2, 0.25, 0.2),
            new Vec3f(-0.8f, 0.1f, -0.8f), new Vec3f(0.8f, 1.1f, 0.8f), 1.1f, 0.6f, 0.08f, 0.22f, EnumParticleModel.Quad);
        burst.SelfPropelled = true;
        entity.World.SpawnParticles(burst);
    }

    /// <summary>What this entity believes about where its target is (used by the menace task when it has senses; shared with its pack).</summary>
    public Belief Belief { get; } = new();

    /// <summary>How long (ms) since the entity first stopped being Ambient, or 0 if it has not.</summary>
    public long EncounterMs => entity.Attributes.HasAttribute(EncounterSinceKey) ? entity.World.ElapsedMilliseconds - entity.Attributes.GetLong(EncounterSinceKey) : 0;

    /// <summary>
    /// How long (ms) the encounter has left before it is sent to Leave. The budget is opt-in: the behaviour attribute
    /// <c>maxEncounterSeconds</c> defaults to 0, meaning none (scripted creatures are untouched), so this is then unbounded.
    /// </summary>
    public long EncounterLeftMs => maxEncounterSeconds <= 0 ? long.MaxValue : maxEncounterSeconds * 1000L - EncounterMs;

    /// <summary>Marks a new entity, before it is spawned, as put down for a target and an encounter.</summary>
    public static void Prepare(Entity entity, Entity target, Encounter kind, bool passive, long now, double untilHours = -1, bool duringShift = false)
    {
        // Some encounters last only while something else does: a Level 1 Flickering, a Reality Shift
        entity.Attributes.SetDouble(UntilKey, untilHours);
        entity.Attributes.SetBool(ShiftKey, duringShift);
        entity.Attributes.SetInt(KindKey, (int)kind);
        if (kind != Encounter.Ambient) entity.Attributes.SetLong(EncounterSinceKey, now);
        entity.Attributes.SetLong(SinceKey, now);
        entity.Attributes.SetLong(OwnerKey, target.EntityId);
        entity.Attributes.SetBool(PassiveKey, passive);
        entity.Attributes.SetLong(BornKey, now);
        entity.Attributes.SetString(SessionKey, Session);
    }

    /// <summary>The in-game hour an entity put down for a set piece (the Flickering) leaves at, or -1 for none.</summary>
    public static double UntilOf(Entity entity) => entity.Attributes.GetDouble(UntilKey, -1);

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
            if (value != Encounter.Ambient && !entity.Attributes.HasAttribute(EncounterSinceKey))
                entity.Attributes.SetLong(EncounterSinceKey, entity.World.ElapsedMilliseconds);
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
        // One scan for the players about, from which "anyone near", the wanderer's 56 x 32 test and who could see it all follow
        Entity[] players = entity.World.GetEntitiesAround(pos, 72, 48, e => e is EntityPlayer p && p.Alive);
        bool anyoneNear = players.Length > 0;
        if (!anyoneNear && target?.WatchedAttributes.GetBool("backrooms:testTarget") != true)
        {
            Despawn();
            return;
        }
        if (target == null || !target.Alive)
        {
            Kind = Kind == Encounter.Ambient ? Encounter.Ambient : Encounter.Leave;
        }

        // A Skin-Stealer's day: docile and talking to itself while fed, hungry (and stalking, as it was put down to) after
        if (entity.Attributes.HasAttribute(FedKey))
        {
            if (!Fed)
            {
                entity.Attributes.RemoveAttribute(FedKey);
                if (Kind == Encounter.Ambient && target is { Alive: true }) Kind = Encounter.Stalk;
                // Hungry, it sheds the clothes and the fresher skin it wore while fed (MenaceSystem's look 1) for the waxy one
                if (entity.WatchedAttributes.GetInt("textureIndex", 0) != 0)
                {
                    entity.WatchedAttributes.SetInt("textureIndex", 0);
                    entity.WatchedAttributes.MarkPathDirty("textureIndex");
                }
            }
            else if (Kind == Encounter.Ambient && fedVoices.Length > 0 && (nextFedVoice -= 1) <= 0)
            {
                nextFedVoice = 15 + (float)entity.World.Rand.NextDouble() * 25;
                entity.World.PlaySoundAt(fedVoices[entity.World.Rand.Next(fedVoices.Length)], entity.Pos.X, entity.Pos.Y + 1.5, entity.Pos.Z, null, true, 24);
            }
        }

        if (Kind is not (Encounter.Ambient or Encounter.Leave))
        {
            double until = entity.Attributes.GetDouble(UntilKey, -1);
            if (until > 0 && entity.World.Calendar.TotalHours > until) Kind = Encounter.Leave;
            if (entity.Attributes.GetBool(ShiftKey) && (entity.Api.ModLoader.GetModSystem<Reality.RealitySystem>()?.ShiftStrength ?? 0) <= 0) Kind = Encounter.Leave;
            // An encounter has a budget, however many times it changes kind
            if (maxEncounterSeconds > 0 && EncounterMs > maxEncounterSeconds * 1000L) Kind = Encounter.Leave;
        }

        long now = entity.World.ElapsedMilliseconds;
        bool seen = SeenByAnyone(players, 48);
        if (seen) lastSeenMs = now;

        switch (Kind)
        {
            case Encounter.Ambient:
                // Wanderers drift off once nobody is near, and are never pulled out of sight of anyone
                // (One put down for a console test's straw dummy stays while the dummy is near, as for the other kinds above)
                if (!seen && !players.Any(p => Math.Abs(p.Pos.Y - pos.Y) <= 32 && p.Pos.SquareHorDistanceTo(pos) <= 56 * 56)
                    && !(target?.WatchedAttributes.GetBool("backrooms:testTarget") == true && target.Pos.DistanceTo(pos) < 56)) Despawn();
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
            case Encounter.Investigate:
                if (PhaseMs > investigateSeconds * 1000) Kind = Encounter.Leave;
                break;
            case Encounter.Search:
                if (PhaseMs > searchSeconds * 1000) Kind = Encounter.Leave;
                break;
            case Encounter.Leave:
                // Gone the moment nobody is looking, or once far enough off and out of sight
                double away = target == null ? 99 : target.Pos.DistanceTo(pos);
                if (now - lastSeenMs > 1500 || away > 30 && !seen || now - leftAtMs > 20_000) Despawn();
                break;
        }
    }

    /// <summary>Whether any player could see this entity right now.</summary>
    public bool SeenByAnyone(double range) =>
        SeenByAnyone(entity.World.GetEntitiesAround(entity.Pos.XYZ, (float)range, (float)range, e => e is EntityPlayer p && p.Alive), range);

    /// <summary>The same, from the players already found about (alive ones, at least as far as <paramref name="range"/>): those beyond the range or spectating do not count.</summary>
    private bool SeenByAnyone(Entity[] players, double range)
    {
        Vec3d pos = entity.Pos.XYZ;
        foreach (Entity e in players)
        {
            if (Math.Abs(e.Pos.Y - pos.Y) > range || e.Pos.SquareHorDistanceTo(pos) > range * range) continue;
            if (e is EntityPlayer { Player: { } who } && who.WorldData.CurrentGameMode == EnumGameMode.Spectator) continue;
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
        if (rangedDamageMul != 1 && damage > 0 && damageSource.SourceEntity is IProjectile) damage *= rangedDamageMul;
        if (bleedsClear && damage > 0 && damageSource.Type != EnumDamageType.Heal) BleedClear();
        if (cause is EntityPlayer && Passive) Passive = false;
        // Striking it is heard: a fight draws more
        if (cause is EntityPlayer && damage > 0)
            entity.Api.ModLoader.GetModSystem<MenaceSystem>()?.RaiseNoise(entity.Pos.XYZ, MenaceSystem.FightLoudness, "fight", cause);
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
            if (VenomSystem.KillerOf(entity, damageSourceForDeath) is EntityPlayer killer) Rewards.Bounty(entity, killer);
            // A Clump put down leaves a remnant (one that merely goes, from Despawn, dies with no damage source)
            if (damageSourceForDeath != null && entity.Code.Path == "clump") BlockClumpRemnant.PlaceWhereDied(entity);
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
