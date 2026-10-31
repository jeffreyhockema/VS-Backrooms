using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 36, "Airport" (experimental): kept as level 25 (<see cref="Level36"/>) and shown as "36". Scaffolding only: a round
/// noclip region far out to the west-south-west (Level 55's old slot), laid out as an open concrete floor under a plain lit ceiling, its rim
/// <see cref="WallPattern.L36Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2500-0x25BF are this level's (0x25C0-0x25FF its thresholds').</summary>
    private const ulong SaltL36Shape = 0x2501;

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees south of west.</summary>
    private double L36Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L36CentreX => spawnMacroX - (int)Math.Round(L36Reach * Math.Cos(Math.PI / 8));
    private int L36CentreZ => spawnMacroZ + (int)Math.Round(L36Reach * Math.Sin(Math.PI / 8));

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int L36Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL36(double mx, double mz) => InRoundRegion(mx, mz, L36CentreX, L36CentreZ, L36Radius, SaltL36Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L36ArrivalCell(ulong h) => RoundArrivalCell(h, L36CentreX, L36CentreZ, L36Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL36ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L36ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L36Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L36Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel36(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L36Floor;
                t.Ceiling = CeilingKind.L36Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L36First"/>-<see cref="Props.L36Last"/>) people walk through: none yet.</summary>
    private static bool L36WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L36Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level36];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L36Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
