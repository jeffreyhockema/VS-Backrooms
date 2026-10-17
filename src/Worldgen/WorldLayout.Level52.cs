using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 52, "School Halls" (experimental): kept as level 23 (<see cref="Level52"/>) and shown as "52". Scaffolding only: a round
/// noclip region far out to the south-south-east, laid out as an open concrete floor under a plain lit ceiling, its rim
/// <see cref="WallPattern.L52Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2300-0x23BF are this level's (0x23C0-0x23FF its thresholds').</summary>
    private const ulong SaltL52Shape = 0x2301;

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees east of south.</summary>
    private double L52Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L52CentreX => spawnMacroX + (int)Math.Round(L52Reach * Math.Sin(Math.PI / 8));
    private int L52CentreZ => spawnMacroZ + (int)Math.Round(L52Reach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int L52Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL52(double mx, double mz) => InRoundRegion(mx, mz, L52CentreX, L52CentreZ, L52Radius, SaltL52Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L52ArrivalCell(ulong h) => RoundArrivalCell(h, L52CentreX, L52CentreZ, L52Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL52ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L52ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L52Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L52Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel52(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L52Floor;
                t.Ceiling = CeilingKind.L52Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L52First"/>-<see cref="Props.L52Last"/>) people walk through: none yet.</summary>
    private static bool L52WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L52Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level52];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L52Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
