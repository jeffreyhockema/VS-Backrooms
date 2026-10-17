using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 183, "Clean Sewers" (experimental): kept as level 27 (<see cref="Level183"/>) and shown as "183". Scaffolding only: a round
/// noclip region far out to the north-west, beyond the End, laid out as an open concrete floor under a plain lit ceiling, its rim
/// <see cref="WallPattern.L183Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2700-0x27BF are this level's (0x27C0-0x27FF its thresholds').</summary>
    private const ulong SaltL183Shape = 0x2701;

    // ================= Where it is =================

    /// <summary>
    /// How far out along the north-west diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond the End, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L183Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    private int L183CentreX => spawnMacroX - L183Reach;
    private int L183CentreZ => spawnMacroZ - L183Reach;

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int L183Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL183(double mx, double mz) => InRoundRegion(mx, mz, L183CentreX, L183CentreZ, L183Radius, SaltL183Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L183ArrivalCell(ulong h) => RoundArrivalCell(h, L183CentreX, L183CentreZ, L183Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL183ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L183ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L183Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L183Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel183(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L183Floor;
                t.Ceiling = CeilingKind.L183Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L183First"/>-<see cref="Props.L183Last"/>) people walk through: none yet.</summary>
    private static bool L183WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L183Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level183];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L183Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
