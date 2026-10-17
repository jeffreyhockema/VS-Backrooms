using System;

namespace Backrooms.Worldgen;

/// <summary>
/// The Basement (experimental): kept as level 22 (<see cref="Basement"/>) and shown as "Basement". Scaffolding only: a round
/// noclip region far out to the south-south-west, laid out as an open concrete floor under a plain lit ceiling, its rim
/// <see cref="WallPattern.BasementWall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2200-0x22BF are this level's (0x22C0-0x22FF its thresholds').</summary>
    private const ulong SaltBasementShape = 0x2201;

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees west of south.</summary>
    private double BasementReach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int BasementCentreX => spawnMacroX - (int)Math.Round(BasementReach * Math.Sin(Math.PI / 8));
    private int BasementCentreZ => spawnMacroZ + (int)Math.Round(BasementReach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int BasementRadius => Math.Max(40, spawnMacroX / 50);

    private bool InBasement(double mx, double mz) => InRoundRegion(mx, mz, BasementCentreX, BasementCentreZ, BasementRadius, SaltBasementShape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) BasementArrivalCell(ulong h) => RoundArrivalCell(h, BasementCentreX, BasementCentreZ, BasementRadius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsBasementArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double BasementArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge BasementEdge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.BasementWall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevelBasement(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.BasementFloor;
                t.Ceiling = CeilingKind.BasementCeiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.BasementFirst"/>-<see cref="Props.BasementLast"/>) people walk through: none yet.</summary>
    private static bool BasementWalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float BasementTemperature(int x, int y, int z, int floorY) => LevelTemperatures[Basement];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float BasementStability(double x, double y, double z, int floorY, float drift) => 1f;
}
