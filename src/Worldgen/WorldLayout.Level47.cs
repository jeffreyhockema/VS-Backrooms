using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 47, "The Adderwood" (experimental): kept as level 30 (<see cref="Level47"/>) and shown as "47". Scaffolding only: a round
/// noclip region far out to the south-south-east, beyond Level 52 and the Hub, laid out as an open concrete floor under the open sky (<see cref="IsOpenSky"/>), its rim
/// <see cref="WallPattern.L47Wall"/>. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only). See
/// docs/design/experimental-levels/README.md; this file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x3000-0x30BF are this level's (0x30C0-0x30FF its thresholds').</summary>
    private const ulong SaltL47Shape = 0x3001;

    // ================= Where it is =================

    /// <summary>
    /// How far out the region's centre lies: 1.35 times the city's distance, 33.75 degrees east of south (between Level 52's 22.5 and the Hub's 45,
    /// and beyond both).
    /// </summary>
    private double L47Reach => RegionReach * 1.35;

    /// <summary>The region's centre, in macro cells.</summary>
    public int L47CentreX => spawnMacroX + (int)Math.Round(L47Reach * Math.Sin(3 * Math.PI / 16));
    public int L47CentreZ => spawnMacroZ + (int)Math.Round(L47Reach * Math.Cos(3 * Math.PI / 16));

    /// <summary>The region's radius in macro cells (placeholder).</summary>
    public int L47Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL47(double mx, double mz) => InRoundRegion(mx, mz, L47CentreX, L47CentreZ, L47Radius, SaltL47Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L47ArrivalCell(ulong h) => RoundArrivalCell(h, L47CentreX, L47CentreZ, L47Radius);

    /// <summary>Arriving: anywhere on the open floor.</summary>
    private static bool IsL47ArrivalSpot(Tile t) => IsArrivalSpot(t);

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L47ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (placeholder: one open floor).</summary>
    private Edge L47Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L47Wall };

    /// <summary>Lays out one of the level's cells (placeholder): open floor, its walls only where the region ends.</summary>
    private void BuildLevel47(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                t.Floor = FloorKind.L47Floor;
                t.Ceiling = CeilingKind.L47Ceiling;
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L47First"/>-<see cref="Props.L47Last"/>) people walk through: none yet.</summary>
    private static bool L47WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L47Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level47];

    /// <summary>Reality stability: neutral (placeholder).</summary>
    private float L47Stability(double x, double y, double z, int floorY, float drift) => 1f;
}
