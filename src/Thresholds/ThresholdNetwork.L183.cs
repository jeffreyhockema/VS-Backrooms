using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 183, "Clean Sewers"'s thresholds (experimental, kept as level 27): none. The level is reached only by the cheats menu or
/// <c>/backrooms goto</c>. This file is the level's own.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x27C0-0x27FF).</summary>
    private const ulong SaltL183Threshold = 0x27C0;

    private Passage L183Walked(int x, int z, in Tile tile, double rel) => null;

    private Passage L183Used(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL183(Func<Tile, bool> beside = null) => In(WorldLayout.Level183, beside);
}
