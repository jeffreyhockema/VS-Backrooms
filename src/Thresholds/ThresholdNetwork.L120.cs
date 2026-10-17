using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 120, "Server Room"'s thresholds (experimental, kept as level 26): none. The level is reached only by the cheats menu or
/// <c>/backrooms goto</c>. This file is the level's own.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x26C0-0x26FF).</summary>
    private const ulong SaltL120Threshold = 0x26C0;

    private Passage L120Walked(int x, int z, in Tile tile, double rel) => null;

    private Passage L120Used(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL120(Func<Tile, bool> beside = null) => In(WorldLayout.Level120, beside);
}
