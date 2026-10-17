using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 31, "Roller Rink" (experimental): kept as level 24 (<see cref="Level31"/>) and shown as "31". Scaffolding only: a round
/// noclip region far out to the west-north-west, laid out as an open concrete floor under a plain lit ceiling, its rim
/// <see cref="WallPattern.L31Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2400-0x24BF are this level's (0x24C0-0x24FF its thresholds').</summary>
    private const ulong SaltL31Shape = 0x2401;

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees north of west.</summary>
    private double L31Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L31CentreX => spawnMacroX - (int)Math.Round(L31Reach * Math.Cos(Math.PI / 8));
    private int L31CentreZ => spawnMacroZ - (int)Math.Round(L31Reach * Math.Sin(Math.PI / 8));

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    private int L31Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL31(double mx, double mz) => InRoundRegion(mx, mz, L31CentreX, L31CentreZ, L31Radius, SaltL31Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L31ArrivalCell(ulong h) => RoundArrivalCell(h, L31CentreX, L31CentreZ, L31Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL31ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L31ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L31Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L31Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel31(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L31Floor;
                t.Ceiling = CeilingKind.L31Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L31First"/>-<see cref="Props.L31Last"/>) people walk through: none yet.</summary>
    private static bool L31WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L31Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level31];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L31Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
