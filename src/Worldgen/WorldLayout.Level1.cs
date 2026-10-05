namespace Backrooms.Worldgen;

/// <summary>
/// Level 1, "the Habitable Zone" (Fandom: "Parking Zone"): an endless cross between an underground car park and
/// an abandoned warehouse, and the level with the most supply crates.
///
/// Halls follow the layout of a real multi-storey car park, repeating every <see cref="BayWidth"/> blocks along X
/// and every <see cref="Module"/> blocks along Z:
/// <code>
///   z % 17 == 0      column line: square columns every 9 blocks, a concrete beam overhead
///   z % 17 in 1..5   a row of 3-wide parking stalls facing the aisle
///   z % 17 in 6..11  a 6-wide two-way driving aisle with a dashed centre line
///   z % 17 in 12..16 another row of stalls, back to back with the next column line
/// </code>
/// Every few bays a cross aisle cuts through the stall rows so cars could drive between aisles. Fluorescent
/// fixtures hang over the aisles and stalls; conduit runs beside the beams; a few cars were abandoned here.
///
/// Some sectors are instead tight concrete corridors with small side rooms, entered under glowing EXIT signs.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Column spacing along X: three 3-block stalls.</summary>
    private const int BayWidth = 9;
    /// <summary>Repeat along Z: column line, stalls, aisle, stalls.</summary>
    private const int Module = 17;
    /// <summary>A cross aisle every five bays.</summary>
    private const int CrossAislePeriod = BayWidth * 5;
    private const int CrossAisleStart = CrossAislePeriod - 6;
    private const int CorridorGrid = 8;

    private const ulong SaltL1Sector = 0x1A01;
    private const ulong SaltL1BigPillars = 0x1A02;
    private const ulong SaltL1Pillar = 0x1A03;
    private const ulong SaltL1Light = 0x1A04;
    private const ulong SaltL1Section = 0x1A05;
    private const ulong SaltL1Room = 0x1A06;
    private const ulong SaltL1Stall = 0x1A07;

    /// <summary>Corridor sectors: tight corridors with small rooms, behind EXIT signs.</summary>
    private bool IsLevel1Corridors(int mx, int mz) => Noise(mx / 4.0, mz / 4.0, SaltL1Sector) > 0.35;

    private Edge Level1Edge(ref Rng rng, int mx, int mz, int nx, int nz)
    {
        var edge = new Edge { Pattern = WallPattern.Concrete };
        bool corridors = IsLevel1Corridors(mx, mz), otherCorridors = IsLevel1Corridors(nx, nz);

        // Corridor grids continue straight across, and the car park flows on without walls
        if (corridors == otherCorridors) return edge;

        // Into a corridor sector: a wall with doorways under EXIT signs
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        edge.ExitSigns = true;
        foreach (int start in new[] { rng.Range(3, 12), rng.Range(18, 28) })
        {
            edge.Tiles[start] = edge.Tiles[start + 1] = EdgeTile.Doorway;
        }
        return edge;
    }

    private void BuildLevel1(Builder b, int mx, int mz)
    {
        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Floor = FloorKind.Concrete;

        if (IsLevel1Corridors(mx, mz)) BuildLevel1Corridors(b, mx, mz);
        else BuildCarPark(b, mx, mz);

        // Puddles everywhere
        ref Rng rng = ref b.Rng;
        int puddles = rng.Range(3, 6);
        for (int n = 0; n < puddles; n++) WetPatch(b, rng.Range(1, MacroSize - 1), rng.Range(1, MacroSize - 1), rng.Range(1, 3));

        // Near Level 2, pipes start to appear along the ceiling
        if (TouchesLevel(mx, mz, 2)) AddCeilingPipes(b, mx, mz);
    }

    // ================= Car park =================

    private enum ParkingZone { ColumnLine, StallsA, Aisle, StallsB }

    private static ParkingZone ZoneOfRow(int gz)
    {
        int row = Hashing.Mod(gz, Module);
        return row == 0 ? ParkingZone.ColumnLine : row <= 5 ? ParkingZone.StallsA : row <= 11 ? ParkingZone.Aisle : ParkingZone.StallsB;
    }

    private static bool InCrossAisle(int gx) => Hashing.Mod(gx, CrossAislePeriod) >= CrossAisleStart;

    private void BuildCarPark(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        // Some sectors were built with massive 2x2 columns
        bool bigColumns = Noise(mx / 6.0, mz / 6.0, SaltL1BigPillars) > 0.55;

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int bay = Hashing.Mod(gx, BayWidth), row = Hashing.Mod(gz, Module);
                bool crossAisle = InCrossAisle(gx);

                // Beams span between the columns under the slab, in both directions
                tile.Beam = row == 0 || bay == 0;
                if (tile.Kind != TileKind.Floor) continue;

                bool column = bigColumns ? bay <= 1 && (row == 0 || row == Module - 1) : bay == 0 && row == 0;
                if (column)
                {
                    int px = Hashing.FloorDiv(gx, BayWidth), pz = Hashing.FloorDiv(gz + 1, Module);
                    double r = Hashing.Unit(Hashing.Hash(seed, px, pz, SaltL1Pillar));
                    SetWall(ref tile, WallPattern.Pillar, BaseStyle.Plain);
                    // Bay letters run A-F along each column line; about half the columns carry a light
                    tile.Variant = (byte)(Hashing.Mod(px, 6) + (r > 0.5 && !SectionDead(gx, gz) ? 8 : 0));
                    continue;
                }

                ParkingZone zone = ZoneOfRow(gz);
                bool stalls = (zone == ParkingZone.StallsA || zone == ParkingZone.StallsB) && !crossAisle;

                // Paint: stall dividers, dashed yellow centre lines down the aisles
                if (stalls && Hashing.Mod(gx, 3) == 0) tile.Floor = FloorKind.ConcreteLineNS;
                else if (zone == ParkingZone.Aisle && row == 8 && !crossAisle && Hashing.Mod(gx, 4) < 2) tile.Floor = FloorKind.ConcreteDashWE;
                else if (crossAisle && Hashing.Mod(gx, CrossAislePeriod) == CrossAisleStart + 2 && Hashing.Mod(gz, 4) < 2) tile.Floor = FloorKind.ConcreteDashNS;

                // Wheel stops near the back of each stall
                if (stalls && (row == 2 || row == Module - 2) && Hashing.Mod(gx, 3) != 0) tile.Variant = Props.WheelStop;

                // Lights: rows over the aisle, a fixture over each bay of stalls, and along the cross aisles
                if (!tile.Beam)
                {
                    if (zone == ParkingZone.Aisle && (row == 7 || row == 10) && Hashing.Mod(gx, 6) == 2 && !crossAisle) tile.Ceiling = Level1LightState(gx, gz);
                    else if (stalls && (row == 3 || row == 14) && (bay == 4 || bay == 5)) tile.Ceiling = Level1LightState(gx, gz);
                    else if (crossAisle && Hashing.Mod(gx, CrossAislePeriod) == CrossAisleStart + 2 && Hashing.Mod(gz, 6) == 3)
                    {
                        tile.Ceiling = Level1LightState(gx, gz);
                        tile.Pier = ArchPier.North;
                    }
                }

                // Conduit runs alongside the column lines
                if ((row == 1 || row == Module - 1) && tile.Ceiling == CeilingKind.Tile) tile.Pipe = Pipes.ConduitX;
            }
        }

        PlaceStallContents(b, mx, mz);
        if (rng.Chance(0.1)) AddShearWall(b, mx, mz);
        if (rng.Chance(0.06)) AddStairsToNowhere(b);
    }

    /// <summary>Each stall may hold crates or, very rarely, an abandoned car.</summary>
    private void PlaceStallContents(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        // Walk stall origins: x at the start of a stall, z at the first row of a stall row
        for (int gz = z0 - Module; gz < z0 + MacroSize; gz++)
        {
            int row = Hashing.Mod(gz, Module);
            if (row != 1 && row != 12) continue;
            for (int gx = x0 - 3; gx < x0 + MacroSize; gx++)
            {
                if (Hashing.Mod(gx, 3) != 1 || InCrossAisle(gx) || InCrossAisle(gx + 1)) continue;
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL1Stall));
                bool rowA = row == 1;

                if (r < 0.025)
                {
                    // A car parked nose-in: 2 wide, 4 long, ending at the wheel stop
                    int zStart = rowA ? gz + 1 : gz;
                    PlaceCar(b, x0, z0, gx, zStart, rowA, (int)(Hashing.Hash(seed, gx, gz, SaltL1Stall + 1) % 4));
                }
                else if (r < 0.12)
                {
                    // Crates left in the stall
                    int cz = rowA ? gz + 2 : gz + 2;
                    SetStack(b, x0, z0, gx, cz, (byte)(1 + (int)(r * 100) % 3));
                    if (r < 0.07) SetStack(b, x0, z0, gx + 1, cz, 1);
                }
            }
        }
    }

    private static void SetStack(Builder b, int x0, int z0, int gx, int gz, byte height)
    {
        int lx = gx - x0, lz = gz - z0;
        if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) return;
        ref Tile tile = ref b.At(lx, lz);
        if (tile.Kind == TileKind.Floor && tile.Variant == 0 && tile.Stair == 0) tile.Stack = height;
    }

    /// <summary>
    /// A car covers 2x4 tiles. The model is drawn by one anchor tile; the others are invisible colliders. Cars that
    /// straddle a chunk edge are placed by both chunks, each writing only its own tiles.
    /// </summary>
    private static void PlaceCar(Builder b, int x0, int z0, int gx, int gz, bool noseNorth, int colour)
    {
        // Anchor at the minimum corner when facing north, the maximum corner when facing south
        int anchorX = noseNorth ? gx : gx + 1;
        int anchorZ = noseNorth ? gz : gz + 3;
        for (int dz = 0; dz < 4; dz++)
        {
            for (int dx = 0; dx < 2; dx++)
            {
                int lx = gx + dx - x0, lz = gz + dz - z0;
                if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Floor) continue;
                bool anchor = gx + dx == anchorX && gz + dz == anchorZ;
                tile.Variant = anchor ? Props.Car : Props.CarPart;
                tile.Stack = (byte)colour;
                tile.Pier = noseNorth ? ArchPier.North : ArchPier.South;
            }
        }
    }

    /// <summary>A concrete shear wall between two columns, under the beam.</summary>
    private void AddShearWall(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        int z = Hashing.Mod(-mz * MacroSize, Module) + rng.Range(0, 1) * Module;
        if (z >= MacroSize) return;
        int x = Hashing.Mod(-mx * MacroSize, BayWidth) + rng.Range(0, 2) * BayWidth;
        for (int k = 1; k < BayWidth && x + k < MacroSize; k++)
        {
            ref Tile tile = ref b.At(x + k, z);
            if (tile.Kind != TileKind.Floor) continue;
            SetWall(ref tile, WallPattern.Concrete, BaseStyle.Plain);
            tile.Variant = (byte)(rng.Chance(0.3) ? 1 : 0);
        }
    }

    /// <summary>A short concrete staircase climbing straight into a wall.</summary>
    private static void AddStairsToNowhere(Builder b)
    {
        ref Rng rng = ref b.Rng;
        var dir = (ArchPier)rng.Range(0, 3);
        int dx = dir == ArchPier.East ? 1 : dir == ArchPier.West ? -1 : 0;
        int dz = dir == ArchPier.South ? 1 : dir == ArchPier.North ? -1 : 0;
        int x = rng.Range(6, MacroSize - 7), z = rng.Range(6, MacroSize - 7);

        for (int k = 0; k <= 3; k++)
        {
            ref Tile t = ref b.At(x + dx * k, z + dz * k);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0) return;
        }
        for (int k = 0; k < 3; k++)
        {
            ref Tile step = ref b.At(x + dx * k, z + dz * k);
            step.Stair = (byte)(k + 1);
            step.Pier = dir;
        }
        SetWall(ref b.At(x + dx * 3, z + dz * 3), WallPattern.Concrete, BaseStyle.Plain);
    }

    // ================= Corridor sectors =================

    /// <summary>A grid of 2-wide corridors every 8 blocks, with a small concrete room in each block between.</summary>
    private void BuildLevel1Corridors(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int ix = Hashing.Mod(gx, CorridorGrid), iz = Hashing.Mod(gz, CorridorGrid);
                if (ix < 2 || iz < 2)
                {
                    // Corridor: a dim tube every 8 blocks, running along the corridor
                    if ((ix == 0 && iz == 5) || (iz == 0 && ix == 5))
                    {
                        tile.Ceiling = Level1LightState(gx, gz);
                        tile.Pier = ix == 0 ? ArchPier.North : ArchPier.West;
                    }
                    continue;
                }

                // Room block 2..7: walls on the perimeter, a 4x4 room inside, one door
                int roomX = Hashing.FloorDiv(gx, CorridorGrid), roomZ = Hashing.FloorDiv(gz, CorridorGrid);
                ulong h = Hashing.Hash(seed, roomX, roomZ, SaltL1Room);
                bool merged = Hashing.Unit(h) < 0.12;
                bool perimeter = ix == 2 || ix == 7 || iz == 2 || iz == 7;
                if (perimeter && !merged)
                {
                    int side = (int)((h >> 8) % 4);
                    bool door = side switch
                    {
                        0 => iz == 2 && ix == 4,
                        1 => ix == 7 && iz == 4,
                        2 => iz == 7 && ix == 5,
                        _ => ix == 2 && iz == 5,
                    };
                    SetWall(ref tile, WallPattern.Concrete, BaseStyle.Plain);
                    if (door)
                    {
                        tile.Kind = TileKind.Doorway;
                        tile.ExitSign = ((h >> 16) & 3) == 0;
                    }
                    continue;
                }

                // Inside the room: a single bulb, sometimes supplies
                if (ix == 4 && iz == 4 && ((h >> 20) & 1) == 0) tile.Ceiling = CeilingKind.LightWarm;
                // In the far corner, clear of every doorway
                if (ix == 6 && iz == 6 && ((h >> 24) % 4) == 0) tile.Stack = (byte)(1 + (h >> 28) % 2);
                // Some rooms are storerooms with shelving along the back wall
                if (iz == 3 && ix >= 3 && ix <= 6 && ((h >> 32) % 4) == 0 && tile.Stack == 0)
                {
                    tile.Variant = Props.Shelf;
                    tile.Pier = ArchPier.North;
                }
            }
        }
    }

    // ================= Shared =================

    /// <summary>Dead sections share a circuit: every tube in them is out.</summary>
    private bool SectionDead(int gx, int gz) =>
        Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 16), Hashing.FloorDiv(gz, 16), SaltL1Section)) < 0.14;

    private CeilingKind Level1LightState(int gx, int gz)
    {
        ulong section = Hashing.Hash(seed, Hashing.FloorDiv(gx, 16), Hashing.FloorDiv(gz, 16), SaltL1Section);
        double s = Hashing.Unit(section);
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL1Light));
        if (s < 0.14) return CeilingKind.LightOff;
        if (s < 0.24) return r < 0.3 ? CeilingKind.LightOff : CeilingKind.LightFlicker;
        return r < 0.08 ? CeilingKind.LightOff : r < 0.11 ? CeilingKind.LightFlicker : CeilingKind.LightOn;
    }

    private static void WetPatch(Builder b, int cx, int cz, int radius)
    {
        for (int z = cz - radius; z <= cz + radius; z++)
        {
            for (int x = cx - radius; x <= cx + radius; x++)
            {
                if (!InInterior(x, z)) continue;
                int dx = x - cx, dz = z - cz;
                if (dx * dx + dz * dz > radius * radius + b.Rng.Range(-1, 1)) continue;
                ref Tile tile = ref b.At(x, z);
                if (tile.Floor == FloorKind.Concrete) tile.Floor = FloorKind.ConcreteWet;
            }
        }
    }

    /// <summary>Parallel pipe bundles along the ceiling, heralding Level 2.</summary>
    private static void AddCeilingPipes(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Floor || tile.Ceiling != CeilingKind.Tile || tile.Beam) continue;
                int row = Hashing.Mod(mz * MacroSize + lz, Module);
                if (row == 4 || row == 13 || Hashing.Mod(mz * MacroSize + lz, CorridorGrid) == 1) tile.Pipe = Pipes.RunX;
            }
        }
    }

    /// <summary>Whether any of the eight surrounding macro cells belongs to the given level.</summary>
    private bool TouchesLevel(int mx, int mz, int level)
    {
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if ((dx != 0 || dz != 0) && LevelAt(mx + dx, mz + dz) == level) return true;
        return false;
    }
}
