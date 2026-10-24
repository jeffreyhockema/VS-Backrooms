using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

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
/// into this; piece A owns the implementation (the behaviours behind the watched trees, the stability offsets and the
/// director multiplier). Until A lands, the mutators here are inert and the readers return "full and fine", so every
/// other piece compiles and runs unchanged against it.
/// </summary>
public static class Needs
{
    /// <summary>World settings (bool attributes). Absent means on: worlds made before the needs existed get both.</summary>
    public const string ThirstSetting = "backroomsThirst", FatigueSetting = "backroomsFatigue";

    /// <summary>Watched trees on the player entity (synced to the client).</summary>
    public const string ThirstTree = "backrooms-thirst", FatigueTree = "backrooms-fatigue";

    public const float MaxHydration = 1500f;

    /// <summary>Awake hours at which you can sleep, are exhausted, are dead on your feet, and the hard cap.</summary>
    public const float DrowsyHours = 24f, ExhaustedHours = 45f, DeadHours = 60f, CapHours = 84f;

    /// <summary>How many awake hours one slept hour removes in a quality-1 bed.</summary>
    public const float RestPerSleptHour = 7.5f;

    public static bool ThirstOn(IWorldAccessor world) =>
        world != null && BackroomsWorld.IsBackroomsClimate(world.Config) && world.Config.GetBool(ThirstSetting, true);

    public static bool FatigueOn(IWorldAccessor world) =>
        world != null && BackroomsWorld.IsBackroomsClimate(world.Config) && world.Config.GetBool(FatigueSetting, true);

    // ================= Thirst =================

    /// <summary>Current hydration, 0..<see cref="MaxHydration"/>. Full when the tree is missing (old saves, other worlds).</summary>
    public static float Hydration(Entity entity) =>
        entity?.WatchedAttributes.GetTreeAttribute(ThirstTree)?.GetFloat("hydration", MaxHydration) ?? MaxHydration;

    public static float HydrationFraction(Entity entity) => GameMath.Clamp(Hydration(entity) / MaxHydration, 0f, 1f);

    /// <summary>Below a quarter: the Wretch's "parched".</summary>
    public static bool Parched(Entity entity) => ThirstOn(entity?.World) && HydrationFraction(entity) < 0.25f;

    /// <summary>Server side. Adds (or, negative, removes) hydration, clamped. No-op while thirst is off.</summary>
    public static void Hydrate(Entity entity, float amount) { /* piece A */ }

    /// <summary>Server side. Gut rot: thirst and hunger run half again as fast for this many game hours (stacks by extending).</summary>
    public static void MakeSick(Entity entity, double gameHours) { /* piece A */ }

    public static bool IsSick(Entity entity) =>
        entity != null && entity.WatchedAttributes.GetDouble("backrooms:sickUntil", 0) > entity.World.Calendar.TotalHours;

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
    public static void SetAwakeHours(Entity entity, float hours) { /* piece A */ }

    /// <summary>Server side. Blue Almond Water: drowsy at once (awake hours raised to <see cref="DrowsyHours"/> if lower).</summary>
    public static void MakeDrowsy(Entity entity) { /* piece A */ }

    /// <summary>Server side. Green Almond Water: fatigue stops growing and the penalties lift for this many game hours; when it
    /// wears off, 8 awake hours land at once (another cup while it lasts extends it and adds another 8).</summary>
    public static void Caffeinate(Entity entity, double gameHours) { /* piece A */ }

    /// <summary>
    /// Server side. Null when the player may lie down here, else the lang key of the refusal ("not-tired-enough",
    /// "backrooms:cantsleep-hungry", "backrooms:cantsleep-thirsty", "backrooms:cantsleep-menace"). With fatigue off only
    /// the vanilla tiredness gate applies.
    /// </summary>
    public static string CanSleep(IServerPlayer player, BlockPos bed) => null;

    /// <summary>The director's per-player multiplier on spawn odds (1 when rested and watered; up to 4 at the worst).</summary>
    public static double DirectorMult(Entity entity) => 1.0;

    // ================= Stability =================

    /// <summary>
    /// Server side. Named contributions to the player's temporal-stability offset (the field vanilla's rifts use), summed into
    /// it once a tick. Sources: "needs:fatigue", "needs:thirst", "l974". Zero removes the contribution.
    /// </summary>
    public static void SetStabilityOffset(Entity entity, string source, double value) { /* piece A */ }
}
