using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// The Basement's thresholds (experimental, kept as level 22; docs/design/experimental-levels/LINKS.md), both one-way:
/// <list type="bullet">
/// <item><b>In:</b> "breaking through the floor of most levels" (Fandom). Step onto the middle of a cracked patch of floor
/// in Level 0, 1, 2, 4 or 5 (WorldLayout.LevelBasement.Links.cs) and it gives way: you fall a long way, into the Basement,
/// under a crack in its ceiling (the fall itself is ThresholdSystem.Basement.cs's). Each patch always drops into the same
/// crack.</item>
/// <item><b>Out:</b> back up the crack (Fandom: "near impossible"; bring a ladder). Whoever gets to the top of a crack's
/// shaft, level with the torn floor of the room up there, by a ladder, blocks or anything else, climbs out into Level 0,
/// where the yellow light it shows comes from. Each crack always comes out in the same place.</item>
/// </list>
/// (Level 2 is not looked at for walked thresholds; its cracks are noticed by <see cref="Regions.BasementSystem"/>.)
/// This file is the level's own.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x22C0-0x22FF).</summary>
    private const ulong SaltBasementThreshold = 0x22C0;

    /// <summary>The feet of someone standing on the floor (rel 1), or just over it: a cracked patch takes them.</summary>
    public const double BasementCrackTripRel = 1.6;

    /// <summary>
    /// Feet this high over the Basement's floor, over a crack (its open middle or the torn floor round it): the top of its
    /// shaft, level with the floor of the room above (<see cref="WorldLayout.BasementCrackTop"/> less four).
    /// </summary>
    public const double BasementClimbRel = WorldLayout.BasementCrackTop - 4;

    public const string BasementFallMessage = "backrooms:basement-fall", BasementClimbMessage = "backrooms:basement-climbout";

    private Passage BasementWalked(int x, int z, in Tile tile, double rel)
    {
        if (rel < BasementCrackTripRel && WorldLayout.BasementCrackGives(tile)) return BasementFall(x, z, tile);
        if (tile.Level == WorldLayout.Basement && rel >= BasementClimbRel
            && (tile.Ceiling == CeilingKind.BasementOpen || tile.Overhead == Overheads.BasementCrackRim)
            && BasementCrackMiddle(x, z) is { } crack)
            return BasementClimb(crack);
        return null;
    }

    private Passage BasementUsed(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>
    /// The floor giving way under someone standing on a tile of a cracked patch's middle: one-way, under a crack in the
    /// Basement's ceiling. The patch is one threshold, its middle tile standing for it.
    /// </summary>
    public Passage BasementFall(int x, int z, in Tile tile)
    {
        var (dx, dz) = WorldLayout.BasementCrackOffset(tile);
        (int X, int Z) middle = (x - dx, z - dz);
        return new Passage { Source = middle, Key = KeyOf(middle, SaltBasementThreshold + 1), Find = IntoBasement(), Message = BasementFallMessage };
    }

    /// <summary>Out of the top of a crack's shaft (its middle tile standing for it): one-way, into Level 0.</summary>
    public Passage BasementClimb((int X, int Z) crack) =>
        new Passage { Source = crack, Key = KeyOf(crack, SaltBasementThreshold + 2), Find = In(0), Message = BasementClimbMessage };

    /// <summary>The middle tile of the crack in the Basement's ceiling over a tile of its open middle or the torn floor round it.</summary>
    public (int X, int Z)? BasementCrackMiddle(int x, int z)
    {
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                Tile t = layout.TileAt(x + dx, z + dz);
                if (t.Level == WorldLayout.Basement && t.Ceiling == CeilingKind.BasementOpen && t.Detail == WorldLayout.BasementCrackMiddle) return (x + dx, z + dz);
            }
        return null;
    }

    /// <summary>An arrival finder in the level (under a crack in its ceiling), beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoBasement(Func<Tile, bool> beside = null) => In(WorldLayout.Basement, beside);
}
