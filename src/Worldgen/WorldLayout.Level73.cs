using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 73, "The Redlands" (experimental): kept as level 21 (<see cref="Level73"/>) and shown as "73". Scaffolding only: a round
/// noclip region far out to the north-north-west (the mirror of Level 188's), laid out as an open concrete floor under a plain lit ceiling, its rim
/// <see cref="WallPattern.L73Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2100-0x21BF are this level's (0x21C0-0x21FF its thresholds').</summary>
    private const ulong SaltL73Shape = 0x2101;

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees west of north.</summary>
    private double L73Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L73CentreX => spawnMacroX - (int)Math.Round(L73Reach * Math.Sin(Math.PI / 8));
    private int L73CentreZ => spawnMacroZ - (int)Math.Round(L73Reach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int L73Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL73(double mx, double mz) => InRoundRegion(mx, mz, L73CentreX, L73CentreZ, L73Radius, SaltL73Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L73ArrivalCell(ulong h) => RoundArrivalCell(h, L73CentreX, L73CentreZ, L73Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL73ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L73ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L73Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L73Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel73(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L73Floor;
                t.Ceiling = CeilingKind.L73Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L73First"/>-<see cref="Props.L73Last"/>) people walk through: none yet.</summary>
    private static bool L73WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L73Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level73];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L73Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
