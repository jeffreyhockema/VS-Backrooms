using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 120, "Server Room" (experimental): kept as level 26 (<see cref="Level120"/>) and shown as "120". Scaffolding only: a round
/// noclip region far out to the north-east, beyond Level Fun, laid out as an open concrete floor under a plain lit ceiling, its rim
/// <see cref="WallPattern.L120Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2600-0x26BF are this level's (0x26C0-0x26FF its thresholds').</summary>
    private const ulong SaltL120Shape = 0x2601;

    // ================= Where it is =================

    /// <summary>
    /// How far out along the north-east diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond Level Fun, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L120Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    private int L120CentreX => spawnMacroX + L120Reach;
    private int L120CentreZ => spawnMacroZ - L120Reach;

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int L120Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL120(double mx, double mz) => InRoundRegion(mx, mz, L120CentreX, L120CentreZ, L120Radius, SaltL120Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L120ArrivalCell(ulong h) => RoundArrivalCell(h, L120CentreX, L120CentreZ, L120Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL120ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L120ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L120Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L120Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel120(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L120Floor;
                t.Ceiling = CeilingKind.L120Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L120First"/>-<see cref="Props.L120Last"/>) people walk through: none yet.</summary>
    private static bool L120WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L120Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level120];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L120Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
