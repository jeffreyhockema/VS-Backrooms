using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 23, "Petrified Garden" (experimental): kept as level 28 (<see cref="Level23"/>) and shown as "23". Scaffolding only: a round
/// noclip region far out to the south-west, beyond Level 974, laid out as an open concrete floor under the open sky (<see cref="IsOpenSky"/>), its rim
/// <see cref="WallPattern.L23Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2800-0x28BF are this level's (0x28C0-0x28FF its thresholds').</summary>
    private const ulong SaltL23Shape = 0x2801;

    // ================= Where it is =================

    /// <summary>
    /// How far out along the south-west diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond Level 974, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L23Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    private int L23CentreX => spawnMacroX - L23Reach;
    private int L23CentreZ => spawnMacroZ + L23Reach;

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int L23Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL23(double mx, double mz) => InRoundRegion(mx, mz, L23CentreX, L23CentreZ, L23Radius, SaltL23Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L23ArrivalCell(ulong h) => RoundArrivalCell(h, L23CentreX, L23CentreZ, L23Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL23ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L23ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L23Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L23Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel23(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L23Floor;
                t.Ceiling = CeilingKind.L23Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L23First"/>-<see cref="Props.L23Last"/>) people walk through: none yet.</summary>
    private static bool L23WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L23Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level23];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L23Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
