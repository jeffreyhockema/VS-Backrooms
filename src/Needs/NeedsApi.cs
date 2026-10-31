using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Needs;

/// <summary>
/// Something a player can sleep on. Implemented by the mod's bed block entity; the fatigue behaviour reads the quality
/// while the player is mounted on it (1.0 = a proper bed restores 60 awake hours in 8 slept hours; 0.6 = a bedroll).
/// </summary>
public interface IRestPlace
{
    float RestQuality { get; }
}

/// <summary>
/// The shared surface of the needs system (thirst and fatigue), see docs/design/needs/README.md. Pieces B, C and D call
/// into this. The meters live in watched trees on the player (<see cref="ThirstTree"/>, <see cref="FatigueTree"/>),
/// kept by <see cref="EntityBehaviorThirst"/> and <see cref="EntityBehaviorFatigue"/>; the readers work on both sides
/// (the trees are synced), the mutators are server side and do nothing on the client.
/// </summary>
public static class Needs
{
    /// <summary>World settings (bool attributes). Absent means on: worlds made before the needs existed get both.</summary>
    public const string ThirstSetting = "backroomsThirst", FatigueSetting = "backroomsFatigue";

    /// <summary>Watched trees on the player entity (synced to the client).</summary>
    public const string ThirstTree = "backrooms-thirst", FatigueTree = "backrooms-fatigue";

    /// <summary>Watched player attribute (root level): the calendar hour gut rot ends.</summary>
    public const string SickKey = "backrooms:sickUntil";

    public const float MaxHydration = 1500f;

    /// <summary>Awake hours at which you can sleep, are exhausted, are dead on your feet, and the hard cap.</summary>
    public const float DrowsyHours = 24f, ExhaustedHours = 45f, DeadHours = 60f, CapHours = 84f;

    /// <summary>How many awake hours one slept hour removes in a quality-1 bed.</summary>
    public const float RestPerSleptHour = 7.5f;

    /// <summary>Awake hours after a respawn (half rested).</summary>
    public const float RespawnAwakeHours = 12f;

    public static bool ThirstOn(IWorldAccessor world) =>
        world != null && BackroomsWorld.IsBackroomsClimate(world.Config) && SettingOn(world.Config, ThirstSetting);

    public static bool FatigueOn(IWorldAccessor world) =>
        world != null && BackroomsWorld.IsBackroomsClimate(world.Config) && SettingOn(world.Config, FatigueSetting);

    /// <summary>A bool world setting, absent meaning on. (A world made with the playstyle stores a bool; a string "false" set some other way is honoured too.)</summary>
    private static bool SettingOn(ITreeAttribute config, string key) => config?[key] switch
    {
        BoolAttribute b => b.value,
        StringAttribute s => !string.Equals(s.value?.Trim(), "false", StringComparison.OrdinalIgnoreCase),
        _ => true,
    };

    // ================= Thirst =================

    /// <summary>Current hydration, 0..<see cref="MaxHydration"/>. Full when the tree is missing (old saves, other worlds).</summary>
    public static float Hydration(Entity entity) =>
        entity?.WatchedAttributes.GetTreeAttribute(ThirstTree)?.GetFloat("hydration", MaxHydration) ?? MaxHydration;

    public static float HydrationFraction(Entity entity) => GameMath.Clamp(Hydration(entity) / MaxHydration, 0f, 1f);

    /// <summary>Below a quarter: the Wretch's "parched".</summary>
    public static bool Parched(Entity entity) => ThirstOn(entity?.World) && HydrationFraction(entity) < NeedsMath.ParchedFraction;

    /// <summary>Server side. Adds (or, negative, removes) hydration, clamped. No-op while thirst is off.</summary>
    public static void Hydrate(Entity entity, float amount)
    {
        if (!IsServer(entity) || amount == 0 || !ThirstOn(entity.World)) return;
        SetHydration(entity, Hydration(entity) + amount);
    }

    /// <summary>Server side. Sets hydration (clamped), whatever the setting (the cheats; <see cref="Hydrate"/> is what drinks use).</summary>
    public static void SetHydration(Entity entity, float value)
    {
        if (!IsServer(entity)) return;
        ITreeAttribute tree = ThirstTreeOf(entity);
        tree.SetFloat("hydration", GameMath.Clamp(value, 0f, MaxHydration));
        entity.WatchedAttributes.MarkPathDirty(ThirstTree);
    }

    /// <summary>Server side. Gut rot: thirst and hunger run half again as fast for this many game hours (stacks by extending).</summary>
    public static void MakeSick(Entity entity, double gameHours)
    {
        if (!IsServer(entity) || gameHours <= 0) return;
        double now = entity.World.Calendar.TotalHours;
        bool was = IsSick(entity);
        entity.WatchedAttributes.SetDouble(SickKey, Math.Max(now, entity.WatchedAttributes.GetDouble(SickKey, 0)) + gameHours);
        if (!was && entity is EntityPlayer { Player: IServerPlayer player }) NeedsSystem.Tell(player, "backrooms:sick-start");
        EntityBehaviorThirst.ApplySickness(entity);
    }

    public static bool IsSick(Entity entity) =>
        entity != null && entity.WatchedAttributes.GetDouble(SickKey, 0) > entity.World.Calendar.TotalHours;

    // ================= Fatigue =================

    /// <summary>Game hours awake, 0..<see cref="CapHours"/>. Zero when the tree is missing.</summary>
    public static float AwakeHours(Entity entity) =>
        entity?.WatchedAttributes.GetTreeAttribute(FatigueTree)?.GetFloat("awakeHours", 0f) ?? 0f;

    /// <summary>The Rest meter, 1 (rested) .. 0 (dead on your feet).</summary>
    public static float RestFraction(Entity entity) => GameMath.Clamp(1f - AwakeHours(entity) / DeadHours, 0f, 1f);

    public static bool Drowsy(Entity entity) => AwakeHours(entity) >= DrowsyHours;
    public static bool Exhausted(Entity entity) => FatigueOn(entity?.World) && AwakeHours(entity) >= ExhaustedHours;
    public static bool DeadOnFeet(Entity entity) => FatigueOn(entity?.World) && AwakeHours(entity) >= DeadHours;

    public static bool Caffeinated(Entity entity) =>
        entity != null && (entity.WatchedAttributes.GetTreeAttribute(FatigueTree)?.GetDouble("caffeineUntil", 0) ?? 0) > entity.World.Calendar.TotalHours;

    /// <summary>Server side. Sets the awake hours (clamped to the cap).</summary>
    public static void SetAwakeHours(Entity entity, float hours)
    {
        if (!IsServer(entity)) return;
        ITreeAttribute tree = FatigueTreeOf(entity);
        tree.SetFloat("awakeHours", GameMath.Clamp(hours, 0f, CapHours));
        entity.WatchedAttributes.MarkPathDirty(FatigueTree);
    }

    /// <summary>Server side. Blue Almond Water: drowsy at once (awake hours raised to <see cref="DrowsyHours"/> if lower).</summary>
    public static void MakeDrowsy(Entity entity)
    {
        if (!IsServer(entity) || AwakeHours(entity) >= DrowsyHours) return;
        SetAwakeHours(entity, DrowsyHours);
    }

    /// <summary>Server side. Green Almond Water: fatigue stops growing and the penalties lift for this many game hours; when it
    /// wears off, 8 awake hours land at once (another cup while it lasts extends it and adds another 8).</summary>
    public static void Caffeinate(Entity entity, double gameHours)
    {
        if (!IsServer(entity) || gameHours <= 0) return;
        ITreeAttribute tree = FatigueTreeOf(entity);
        var (until, crash) = NeedsMath.Caffeinate(entity.World.Calendar.TotalHours, tree.GetDouble("caffeineUntil", 0), tree.GetFloat("crashHours", 0), gameHours);
        tree.SetDouble("caffeineUntil", until);
        tree.SetFloat("crashHours", crash);
        entity.WatchedAttributes.MarkPathDirty(FatigueTree);
    }

    /// <summary>
    /// Server side. Null when the player may lie down here, else the lang key of the refusal ("not-tired-enough",
    /// "backrooms:cantsleep-hungry", "backrooms:cantsleep-thirsty", "backrooms:cantsleep-menace"). With fatigue off only
    /// the vanilla tiredness gate applies.
    /// </summary>
    public static string CanSleep(IServerPlayer player, BlockPos bed)
    {
        EntityPlayer entity = player?.Entity;
        if (entity == null) return null;
        IWorldAccessor world = entity.World;
        if (!FatigueOn(world))
        {
            // (Outside a Backrooms world, or with fatigue off: vanilla's own rule)
            var tiredness = entity.GetBehavior<EntityBehaviorTiredness>();
            return tiredness != null && tiredness.Tiredness <= 8 ? "not-tired-enough" : null;
        }
        if (AwakeHours(entity) < DrowsyHours) return "not-tired-enough";
        if (ThirstOn(world) && HydrationFraction(entity) < NeedsMath.WakeFraction) return "backrooms:cantsleep-thirsty";
        if (SatietyFraction(entity) < NeedsMath.WakeFraction) return "backrooms:cantsleep-hungry";
        Vec3d at = bed != null ? bed.ToVec3d().Add(0.5, 0.5, 0.5) : entity.Pos.XYZ;
        if (MenaceNear(world, at)) return "backrooms:cantsleep-menace";
        return null;
    }

    /// <summary>The director's per-player multiplier on spawn odds (1 when rested and watered; up to 4 at the worst).</summary>
    public static double DirectorMult(Entity entity)
    {
        if (entity?.World == null) return 1.0;
        IWorldAccessor world = entity.World;
        bool thirstEmpty = ThirstOn(world) && Hydration(entity) <= 0;
        return NeedsMath.DirectorMult(AwakeHours(entity), FatigueOn(world), Caffeinated(entity), thirstEmpty);
    }

    // ================= Stability =================

    /// <summary>Per player (entity id): the named contributions to the stability offset.</summary>
    private static readonly Dictionary<long, Dictionary<string, double>> offsets = new();

    /// <summary>
    /// Server side. Named contributions to the player's temporal-stability offset (the field vanilla's rifts use), summed into
    /// it once a tick. Sources: "needs:fatigue", "needs:thirst", "l974". Zero removes the contribution.
    /// </summary>
    public static void SetStabilityOffset(Entity entity, string source, double value)
    {
        if (!IsServer(entity) || source == null) return;
        lock (offsets)
        {
            if (!offsets.TryGetValue(entity.EntityId, out var mine))
            {
                if (value == 0) return;
                offsets[entity.EntityId] = mine = new Dictionary<string, double>();
            }
            if (value == 0) mine.Remove(source);
            else mine[source] = value;
            if (mine.Count == 0) offsets.Remove(entity.EntityId);
        }
        ApplyStabilityOffset(entity);
    }

    /// <summary>The sum of a player's contributions (0 with none).</summary>
    public static double StabilityOffset(Entity entity)
    {
        if (entity == null) return 0;
        lock (offsets)
        {
            if (!offsets.TryGetValue(entity.EntityId, out var mine)) return 0;
            double sum = 0;
            foreach (double v in mine.Values) sum += v;
            return sum;
        }
    }

    /// <summary>Writes the sum into vanilla's field (on a change, and once a second from <see cref="NeedsSystem"/>).</summary>
    internal static void ApplyStabilityOffset(Entity entity)
    {
        if (entity?.GetBehavior<EntityBehaviorTemporalStabilityAffected>() is { } tsa) tsa.stabilityOffset = StabilityOffset(entity);
    }

    /// <summary>A player's contributions, for /backrooms needs.</summary>
    internal static string StabilitySources(Entity entity)
    {
        lock (offsets)
        {
            if (entity == null || !offsets.TryGetValue(entity.EntityId, out var mine) || mine.Count == 0) return "none";
            var parts = new List<string>();
            foreach (var kv in mine) parts.Add(string.Format(System.Globalization.CultureInfo.InvariantCulture, "{0} {1:+0.00;-0.00}", kv.Key, kv.Value));
            return string.Join(", ", parts);
        }
    }

    /// <summary>Whether a player has any contribution (only those get the once-a-second write).</summary>
    internal static bool HasOffsets(long entityId)
    {
        lock (offsets) return offsets.ContainsKey(entityId);
    }

    internal static void ForgetOffsets(long entityId)
    {
        lock (offsets) offsets.Remove(entityId);
    }

    internal static void ForgetAllOffsets()
    {
        lock (offsets) offsets.Clear();
    }

    // ================= Helpers =================

    /// <summary>Satiety as a fraction of the most (1 without a hunger tree).</summary>
    public static float SatietyFraction(Entity entity)
    {
        ITreeAttribute hunger = entity?.WatchedAttributes.GetTreeAttribute("hunger");
        if (hunger == null) return 1f;
        float max = hunger.GetFloat("maxsaturation", 1500);
        return max > 0 ? GameMath.Clamp(hunger.GetFloat("currentsaturation", max) / max, 0f, 1f) : 1f;
    }

    /// <summary>How near (blocks) a stalking or hunting creature wakes a sleeper, or keeps them from lying down.</summary>
    public const float MenaceWakeRadius = 6;

    /// <summary>Whether a creature that is stalking or hunting is within <see cref="MenaceWakeRadius"/> blocks.</summary>
    public static bool MenaceNear(IWorldAccessor world, Vec3d at) =>
        world.GetNearestEntity(at, MenaceWakeRadius, MenaceWakeRadius, e => e.Alive && Entities.EntityBehaviorMenace.KindOf(e) is Entities.Encounter.Stalk or Entities.Encounter.Hunt) != null;

    private static bool IsServer(Entity entity) => entity?.World != null && entity.World.Side == EnumAppSide.Server;

    internal static ITreeAttribute ThirstTreeOf(Entity entity)
    {
        ITreeAttribute tree = entity.WatchedAttributes.GetTreeAttribute(ThirstTree);
        if (tree != null) return tree;
        tree = new TreeAttribute();
        tree.SetFloat("hydration", MaxHydration);
        tree.SetFloat("maxhydration", MaxHydration);
        entity.WatchedAttributes.SetAttribute(ThirstTree, tree);
        return tree;
    }

    internal static ITreeAttribute FatigueTreeOf(Entity entity)
    {
        ITreeAttribute tree = entity.WatchedAttributes.GetTreeAttribute(FatigueTree);
        if (tree != null) return tree;
        tree = new TreeAttribute();
        tree.SetFloat("awakeHours", 0);
        tree.SetDouble("caffeineUntil", 0);
        tree.SetFloat("crashHours", 0);
        entity.WatchedAttributes.SetAttribute(FatigueTree, tree);
        return tree;
    }

    /// <summary>A stat category's value under one code (0 when unset; the category may not exist yet, and the indexer would throw).</summary>
    internal static float StatOf(Entity entity, string category, string code)
    {
        foreach (var kv in entity.Stats)
            if (kv.Key == category) return kv.Value.ValuesByKey.TryGetValue(code, out var v) ? v.Value : 0f;
        return 0f;
    }

    /// <summary>Sets a stat (removing it at 0), only when it changes: Stats.Set and Remove resync the whole stats tree.</summary>
    internal static void SetStat(Entity entity, string category, string code, float value)
    {
        if (Math.Abs(StatOf(entity, category, code) - value) < 0.001f) return;
        if (value == 0) entity.Stats.Remove(category, code);
        else entity.Stats.Set(category, code, value, false);
    }
}
