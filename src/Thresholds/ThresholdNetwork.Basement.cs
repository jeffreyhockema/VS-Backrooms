using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// The Basement's thresholds (experimental, kept as level 22): none. The level is reached only by the cheats menu or
/// <c>/backrooms goto</c>. This file is the level's own.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x22C0-0x22FF).</summary>
    private const ulong SaltBasementThreshold = 0x22C0;

    private Passage BasementWalked(int x, int z, in Tile tile, double rel) => null;

    private Passage BasementUsed(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoBasement(Func<Tile, bool> beside = null) => In(WorldLayout.Basement, beside);
}
