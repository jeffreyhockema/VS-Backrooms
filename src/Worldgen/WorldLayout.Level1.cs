using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 1, "the Habitable Zone" (Fandom: "Parking Zone"): an endless cross between an underground car park and
/// an abandoned warehouse, and the level with the most supply crates.
///
/// <para><b>The halls</b> follow the layout of a real multi-storey car park, repeating every
/// <see cref="BayWidth"/> blocks along X and every <see cref="Module"/> blocks along Z:</para>
/// <code>
///   z % 17 == 0      column line: square columns every 9 blocks, a concrete beam overhead
///   z % 17 in 1..5   a row of 3-wide parking stalls facing the aisle
///   z % 17 in 6..11  a 6-wide two-way driving aisle with a dashed centre line and lane arrows
///   z % 17 in 12..16 another row of stalls, back to back with the next column line
/// </code>
/// Every few bays a cross aisle cuts through the stall rows under striped clearance bars. Fluorescent fixtures
/// hang over the aisles and stalls; conduit and red sprinkler pipes run under the slab; a few cars were abandoned
/// here. Stair cores stand at regular intervals: white-painted boxes with fire doors propped open under EXIT
/// signs, and a flight of stairs inside that climbs into the ceiling (and, now and then, somewhere else).
/// Wanderer groups tie coloured cloths round columns as landmarks, with supplies left at the foot.
///
/// <para><b>The maintenance halls</b> fill whole sectors, entered through black fire doors under EXIT signs. Their
/// walls are white-painted block, much brighter than the grey car park. Tight 2-wide corridors run every
/// <see cref="HallGrid"/> blocks with leaking pipes and power boxes, and the blocks between hold small side rooms
/// (most empty and dark; others storerooms, electrical rooms, workshops, pump rooms, first-aid rooms, wanderers'
/// camps and stairwells), littered maintenance halls, encampments, and corridors cutting through.</para>
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

    /// <summary>Maintenance hall corridors run every 16 blocks, at offsets 7 and 8 of each period.</summary>
    private const int HallGrid = 16;
    private const int HallOffset = 7;
    /// <summary>A block between corridors: its perimeter wall and the 12x12 inside.</summary>
    private const int HallBlock = 14;

    private const ulong SaltL1Sector = 0x1A01;
    private const ulong SaltL1BigPillars = 0x1A02;
    private const ulong SaltL1Pillar = 0x1A03;
    private const ulong SaltL1Light = 0x1A04;
    private const ulong SaltL1Section = 0x1A05;
    private const ulong SaltL1Block = 0x1A06;
    private const ulong SaltL1Stall = 0x1A07;
    private const ulong SaltL1Detail = 0x1A08;
    private const ulong SaltL1Core = 0x1A09;

    /// <summary>
    /// The level is divided into districts of this many cells each way. Between two districts of car park stands a
    /// fire wall, open where the aisles run through it; a whole district may be maintenance halls instead.
    /// </summary>
    private const int L1District = 3;

    private static int L1DistrictOf(int m) => Hashing.FloorDiv(m, L1District);

    /// <summary>Maintenance hall sectors: whole districts, in patches.</summary>
    private bool IsLevel1Corridors(int mx, int mz) => Noise(L1DistrictOf(mx) / 1.35, L1DistrictOf(mz) / 1.35, SaltL1Sector) > 0.42;

    private bool IsHallAt(int gx, int gz)
    {
        int mx = MacroOf(gx), mz = MacroOf(gz);
        return LevelAt(mx, mz) == 1 && IsLevel1Corridors(mx, mz);
    }

    private static int HallIndex(int g) => Hashing.Mod(g - HallOffset, HallGrid);

    /// <summary>Doorway starts on an edge line that meet the maintenance hall corridors crossing it.</summary>
    private static readonly int[] HallCrossings = { HallOffset, HallOffset + HallGrid };

    private Edge Level1Edge(ref Rng rng, int mx, int mz, int nx, int nz)
    {
        var edge = new Edge { Pattern = WallPattern.Concrete };
        bool corridors = IsLevel1Corridors(mx, mz), otherCorridors = IsLevel1Corridors(nx, nz);

        // Corridor grids continue straight across, and the car park flows on without walls within a district
        if (corridors == otherCorridors)
        {
            if (corridors || L1DistrictOf(mx) == L1DistrictOf(nx) && L1DistrictOf(mz) == L1DistrictOf(nz)) return edge;
            // A fire wall between two districts of the car park: open where every other driving aisle runs through it
            // (a wall running north-south) or where the cross aisles do (a wall running west-east)
            bool west = nx != mx;
            for (int i = 1; i < MacroSize; i++)
            {
                int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
                bool gap = west ? Hashing.Mod(gz, Module) is >= 7 and <= 10 && Hashing.Mod(Hashing.FloorDiv(gz, Module), 2) == 0 : InCrossAisle(gx);
                edge.Tiles[i] = gap ? EdgeTile.Open : EdgeTile.Wall;
            }
            return edge;
        }

        // Into the maintenance halls: a white wall with fire doors where the corridors arrive
        edge.Pattern = WallPattern.WhiteBlock;
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        edge.ExitSigns = true;
        foreach (int start in HallCrossings)
        {
            if (start != HallCrossings[0] && !rng.Chance(0.7)) continue;
            edge.Tiles[start] = edge.Tiles[start + 1] = EdgeTile.Doorway;
        }
        return edge;
    }

    private void BuildLevel1(Builder b, int mx, int mz)
    {
        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Floor = FloorKind.Concrete;

        bool halls = IsLevel1Corridors(mx, mz);
        if (halls) BuildLevel1Corridors(b, mx, mz);
        else BuildCarPark(b, mx, mz);

        // Puddles everywhere in the car park; the halls are warmer and drier, wet only under leaks
        ref Rng rng = ref b.Rng;
        if (!halls)
        {
            int puddles = rng.Range(3, 6);
            for (int n = 0; n < puddles; n++)
            {
                int cx = rng.Range(2, MacroSize - 3), cz = rng.Range(2, MacroSize - 3);
                WetPatch(b, cx, cz, rng.Range(1, 3));
                ref Tile mid = ref b.At(cx, cz);
                if (mid.Kind != TileKind.Floor || mid.Variant != 0 || mid.Stack != 0 || mid.SupplyBox || mid.Stair != 0 || mid.Floor == FloorKind.L1Hall) continue;
                double r = rng.NextDouble();
                if (r < 0.3) { mid.Variant = Props.WetFloorSign; mid.Pier = (ArchPier)rng.Range(0, 3); }
                else if (r < 0.45) mid.Variant = Props.TrafficCone;
                // Traffic signs stand about the car park, pointing at walls and dead ends
                else if (r < 0.62) { mid.Variant = Props.TrafficSign; mid.Stack = (byte)rng.Range(0, 2); mid.Pier = (ArchPier)rng.Range(0, 3); }
            }
        }

        // The fire walls between districts are scarred: here and there the concrete has spalled to rusty rebar
        for (int i = 1; i < MacroSize; i++)
            foreach ((int x, int z) in new[] { (0, i), (i, 0) })
            {
                ref Tile t = ref b.At(x, z);
                if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.Concrete && t.Variant == 0
                    && Hashing.Unit(Hashing.Hash(seed, mx * MacroSize + x, mz * MacroSize + z, SaltL1Detail + 3)) < 0.08) t.Variant = 1;
            }

        // Near Level 2, pipes start to appear along the ceiling
        if (TouchesLevel(mx, mz, 2)) AddCeilingPipes(b, mx, mz);

        HangFireDoors(b, mx, mz);
    }

    /// <summary>
    /// Doorways in this cell's own edges between the car park and the maintenance halls (or another level) get a
    /// pair of black fire doors, propped open on the car park side.
    /// </summary>
    private void HangFireDoors(Builder b, int mx, int mz)
    {
        bool halls = IsLevel1Corridors(mx, mz);
        for (int i = 1; i < MacroSize - 1; i++)
        {
            foreach (bool west in new[] { true, false })
            {
                int x = west ? 0 : i, z = west ? i : 0;
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Doorway || !t.ExitSign) continue;
                int nx = west ? mx - 1 : mx, nz = west ? mz : mz - 1;
                bool otherIsLevel1 = LevelAt(nx, nz) == 1;
                // Leaves open toward the car park: away from the halls, or into this cell when the other side is another level
                bool outward = halls && otherIsLevel1 && !IsLevel1Corridors(nx, nz);
                ArchPier facing = west ? (outward ? ArchPier.West : ArchPier.East) : (outward ? ArchPier.North : ArchPier.South);
                // Which leaf: the doorway is two wide, its first tile has a doorway after it
                Tile next = west ? b.At(0, i + 1) : b.At(i + 1, 0);
                Tile prev = west ? b.At(0, i - 1) : b.At(i - 1, 0);
                bool first = next.Kind == TileKind.Doorway && prev.Kind != TileKind.Doorway;
                bool second = prev.Kind == TileKind.Doorway;
                if (!first && !second) continue;
                t.Variant = Props.FireDoor;
                t.Pier = facing;
                t.Stack = (byte)(first == LeftIsSmaller(facing) ? 0 : 1);
            }
        }
    }

    /// <summary>For a viewer facing a wall from the given side, whether the tile with the smaller coordinate is on their left.</summary>
    private static bool LeftIsSmaller(ArchPier facing) => facing is ArchPier.South or ArchPier.West;

    // ================= Car park =================

    private enum ParkingZone { ColumnLine, StallsA, Aisle, StallsB }

    private static ParkingZone ZoneOfRow(int gz)
    {
        int row = Hashing.Mod(gz, Module);
        return row == 0 ? ParkingZone.ColumnLine : row <= 5 ? ParkingZone.StallsA : row <= 11 ? ParkingZone.Aisle : ParkingZone.StallsB;
    }

    private static bool InCrossAisle(int gx) => Hashing.Mod(gx, CrossAislePeriod) >= CrossAisleStart;

    /// <summary>Stair cores stand in every fifth bay of every third module, in the first row of stalls.</summary>
    private static bool InStairCore(int gx, int gz)
    {
        int bay = Hashing.Mod(gx, BayWidth), row = Hashing.Mod(gz, Module);
        return bay >= 1 && row >= 1 && row <= 5
            && Hashing.Mod(Hashing.FloorDiv(gx, BayWidth), 5) == 2 && Hashing.Mod(Hashing.FloorDiv(gz, Module), 3) == 1;
    }

    private bool IsCarParkAt(int gx, int gz)
    {
        int mx = MacroOf(gx), mz = MacroOf(gz);
        return LevelAt(mx, mz) == 1 && !IsLevel1Corridors(mx, mz);
    }

    /// <summary>Whether the whole core, and the aisle in front of its doors, lie in the car park, in one district.</summary>
    private bool StairCoreFits(int gx, int gz)
    {
        int x0 = gx - Hashing.Mod(gx, BayWidth), z0 = gz - Hashing.Mod(gz, Module);
        return IsCarParkAt(x0, z0) && IsCarParkAt(x0 + BayWidth, z0) && IsCarParkAt(x0, z0 + 7) && IsCarParkAt(x0 + BayWidth, z0 + 7)
            && L1DistrictOf(MacroOf(x0)) == L1DistrictOf(MacroOf(x0 + BayWidth)) && L1DistrictOf(MacroOf(z0)) == L1DistrictOf(MacroOf(z0 + 7));
    }

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

                if (InStairCore(gx, gz) && StairCoreFits(gx, gz))
                {
                    BuildStairCoreTile(ref tile, gx, gz, bay, row);
                    continue;
                }

                bool column = bigColumns ? bay <= 1 && (row == 0 || row == Module - 1) : bay == 0 && row == 0;
                if (column)
                {
                    int px = Hashing.FloorDiv(gx, BayWidth), pz = Hashing.FloorDiv(gz + 1, Module);
                    ulong ph = Hashing.Hash(seed, px, pz, SaltL1Pillar);
                    double r = Hashing.Unit(ph);
                    bool light = r > 0.5 && !SectionDead(gx, gz);
                    SetWall(ref tile, WallPattern.Pillar, BaseStyle.Plain);
                    // Bay letters run A-F along each column line; about half the columns carry a light
                    tile.Variant = (byte)(Hashing.Mod(px, 6) + (light ? 8 : 0));
                    // Now and then a group has tied its coloured cloth round a column, supplies at its foot
                    if (!light && !bigColumns && Hashing.Unit(ph << 20) < 0.04)
                    {
                        tile.Variant |= (byte)((1 + (int)((ph >> 32) % 4)) << 4);
                        tile.Pier = (ph & 1) == 0 ? ArchPier.South : ArchPier.North;
                    }
                    continue;
                }

                ParkingZone zone = ZoneOfRow(gz);
                bool stalls = (zone == ParkingZone.StallsA || zone == ParkingZone.StallsB) && !crossAisle;
                ulong dh = Hashing.Hash(seed, gx, gz, SaltL1Detail);

                // Paint: stall dividers, dashed yellow centre lines, lane arrows, oil stains, drains
                if (stalls && Hashing.Mod(gx, 3) == 0) tile.Floor = FloorKind.ConcreteLineNS;
                else if (zone == ParkingZone.Aisle && row == 8 && !crossAisle && Hashing.Mod(gx, 4) < 2) tile.Floor = FloorKind.ConcreteDashWE;
                else if (crossAisle && Hashing.Mod(gx, CrossAislePeriod) == CrossAisleStart + 2 && Hashing.Mod(gz, 4) < 2) tile.Floor = FloorKind.ConcreteDashNS;
                else if (row == 7 && !crossAisle && Hashing.Mod(gx, 27) == 13) tile.Floor = FloorKind.ParkArrowW;
                else if (row == 10 && !crossAisle && Hashing.Mod(gx, 27) == 26) tile.Floor = FloorKind.ParkArrowE;
                else if (stalls && (row == 3 || row == 14) && Hashing.Mod(gx, 3) == 2 && Hashing.Unit(dh) < 0.18) tile.Floor = FloorKind.ParkOil;
                else if (row == 9 && !crossAisle && Hashing.Mod(gx, 36) == 22) tile.Floor = FloorKind.ParkDrain;
                else if ((row == 8 || row == 10) && !crossAisle && Hashing.Mod(gx, 36) is 21 or 22 or 23) tile.Floor = FloorKind.ConcreteWet;

                // Wheel stops near the back of each stall; speed bumps across the aisles
                if (stalls && (row == 2 || row == Module - 2) && Hashing.Mod(gx, 3) != 0) tile.Variant = Props.WheelStop;
                else if (zone == ParkingZone.Aisle && !crossAisle && Hashing.Mod(gx, CrossAislePeriod) == 22)
                {
                    tile.Variant = Props.SpeedBump;
                    tile.Pier = ArchPier.East;
                }

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

                // Conduit alongside the column lines, red sprinkler mains down the middle of each stall row,
                // striped clearance bars where the cross aisles meet the main aisles
                if (tile.Ceiling == CeilingKind.Tile && !tile.Beam)
                {
                    if (row == 1 || row == Module - 1) tile.Pipe = Pipes.ConduitX;
                    else if (row == 4 || row == 13) tile.Overhead = Overheads.SprinklerWE;
                    else if (crossAisle && (row == 5 || row == 12)) tile.Overhead = Overheads.ClearanceWE;
                }
            }
        }

        PlaceStallContents(b, mx, mz);
        PlaceLandmarkSupplies(b);
        if (rng.Chance(0.1)) AddShearWall(b, mx, mz);
        if (rng.Chance(0.06)) AddStairsToNowhere(b);
    }

    /// <summary>
    /// One tile of a stair core. In bay coordinates (1-8 across, rows 1-5 deep) the core is a white box with a
    /// two-wide doorway onto the aisle; inside, steps climb westward into the ceiling.
    /// </summary>
    private void BuildStairCoreTile(ref Tile tile, int gx, int gz, int bay, int row)
    {
        tile.Beam = false;
        tile.Floor = FloorKind.L1Hall;
        bool perimeter = bay == 1 || bay == 8 || row == 1 || row == 5;
        if (perimeter)
        {
            SetWall(ref tile, WallPattern.WhiteBlock, BaseStyle.Plain);
            if (row == 5 && (bay == 4 || bay == 5))
            {
                tile.Kind = TileKind.Doorway;
                tile.ExitSign = true;
                tile.Variant = Props.FireDoor;
                tile.Pier = ArchPier.South;
                tile.Stack = (byte)(bay == 4 ? 0 : 1);
            }
            else if (row == 5 && bay == 3) { tile.Variant = Decor.StairSign; tile.Pier = ArchPier.South; }
            else if (bay == 8 && row == 3) { tile.Variant = Decor.Standpipe; tile.Pier = ArchPier.West; }
            else if (row == 1 && bay == 7) { tile.Variant = Decor.LevelSign; tile.Pier = ArchPier.South; }
            else if (row == 1 && bay == 4) { tile.Variant = Decor.Outlet; tile.Pier = ArchPier.South; }
            return;
        }
        // Inside: rows 2-3 hold the flight, row 4 is the way in, bay 7 the bottom landing
        if (row <= 3)
        {
            if (bay <= 3) SetWall(ref tile, WallPattern.WhiteBlock, BaseStyle.Plain);
            else if (bay <= 6)
            {
                tile.Stair = (byte)(7 - bay);
                tile.Pier = ArchPier.West;
            }
        }
        else if (bay == 6)
        {
            tile.Ceiling = CeilingKind.LightWarm;
        }
    }

    /// <summary>Supplies left at the foot of each column that carries a group's cloth.</summary>
    private static void PlaceLandmarkSupplies(Builder b)
    {
        for (int lz = 1; lz < MacroSize - 1; lz++)
        {
            for (int lx = 1; lx < MacroSize - 1; lx++)
            {
                Tile t = b.At(lx, lz);
                if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.Pillar || t.Variant < 16) continue;
                int dz = t.Pier == ArchPier.South ? 1 : -1;
                ref Tile foot = ref b.At(lx, lz + dz);
                if (foot.Kind == TileKind.Floor && foot.Variant == 0 && foot.Stack == 0) foot.SupplyBox = true;
            }
        }
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
                if (InStairCore(gx, gz + 2) && StairCoreFits(gx, gz + 2) || InStairCore(gx + 1, gz + 2) && StairCoreFits(gx + 1, gz + 2)) continue;
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
                    int cz = gz + 2;
                    SetStack(b, x0, z0, gx, cz, (byte)(1 + (int)(r * 100) % 3));
                    if (r < 0.07) SetStack(b, x0, z0, gx + 1, cz, 1);
                }
                else if (r < 0.135)
                {
                    // A pallet of boxes, or a forgotten trash can
                    SetProp(b, x0, z0, gx, gz + 2, r < 0.128 ? Props.Pallet : Props.TrashCan);
                    if (r < 0.124) SetProp(b, x0, z0, gx + 1, gz + 2, Props.CardboardBoxes);
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

    private static void SetProp(Builder b, int x0, int z0, int gx, int gz, byte prop)
    {
        int lx = gx - x0, lz = gz - z0;
        if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) return;
        ref Tile tile = ref b.At(lx, lz);
        if (tile.Kind == TileKind.Floor && tile.Variant == 0 && tile.Stair == 0 && tile.Stack == 0) tile.Variant = prop;
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

    /// <summary>A concrete shear wall between two columns, under the beam, with fire equipment and power boxes on it.</summary>
    private void AddShearWall(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        int z = Hashing.Mod(-mz * MacroSize, Module) + rng.Range(0, 1) * Module;
        if (z >= MacroSize - 1 || z < 1) return;
        int x = Hashing.Mod(-mx * MacroSize, BayWidth) + rng.Range(0, 2) * BayWidth;
        for (int k = 1; k < BayWidth && x + k < MacroSize; k++)
        {
            ref Tile tile = ref b.At(x + k, z);
            if (tile.Kind != TileKind.Floor || tile.Stair != 0) continue;
            tile.Variant = 0;
            tile.Stack = 0;
            SetWall(ref tile, WallPattern.Concrete, BaseStyle.Plain);
            double r = rng.NextDouble();
            tile.Pier = rng.Chance(0.5) ? ArchPier.North : ArchPier.South;
            tile.Variant = r < 0.25 ? (byte)1 : r < 0.33 ? Decor.HoseCabinet : r < 0.41 ? Decor.Extinguisher : r < 0.5 ? Decor.PowerBox
                : r < 0.56 ? Decor.Graffiti : r < 0.62 ? Decor.Outlet : r < 0.7 ? Decor.Camera : (byte)0;
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
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0 || t.Stair != 0 || t.Floor == FloorKind.L1Hall) return;
        }
        for (int k = 0; k < 3; k++)
        {
            ref Tile step = ref b.At(x + dx * k, z + dz * k);
            step.Stair = (byte)(k + 1);
            step.Pier = dir;
        }
        SetWall(ref b.At(x + dx * 3, z + dz * 3), WallPattern.Concrete, BaseStyle.Plain);
    }

    // ================= Maintenance halls =================

    private void BuildLevel1Corridors(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Floor = FloorKind.L1Hall;

        // Lay out every block that overlaps this cell, then copy in the tiles that fall inside it
        int bx0 = Hashing.FloorDiv(x0 - HallOffset - 2, HallGrid), bx1 = Hashing.FloorDiv(x0 + MacroSize - 1 - HallOffset - 2, HallGrid);
        int bz0 = Hashing.FloorDiv(z0 - HallOffset - 2, HallGrid), bz1 = Hashing.FloorDiv(z0 + MacroSize - 1 - HallOffset - 2, HallGrid);
        for (int bz = bz0; bz <= bz1; bz++)
        {
            for (int bx = bx0; bx <= bx1; bx++)
            {
                Tile[] plan = HallBlockPlan(bx, bz);
                int gx0 = bx * HallGrid + HallOffset + 2, gz0 = bz * HallGrid + HallOffset + 2;
                for (int v = 0; v < HallBlock; v++)
                {
                    for (int u = 0; u < HallBlock; u++)
                    {
                        int lx = gx0 + u - x0, lz = gz0 + v - z0;
                        if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
                        ref Tile tile = ref b.At(lx, lz);
                        if (tile.Kind != TileKind.Floor) continue; // the cell's own edge walls stay
                        tile = plan[v * HallBlock + u];
                    }
                }
            }
        }

        DressHallCorridors(b, mx, mz);
    }

    /// <summary>Lights, pipes, wiring and wall clutter along the corridors between blocks.</summary>
    private void DressHallCorridors(Builder b, int mx, int mz)
    {
        bool IsCorridor(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && b.At(x, z).Kind == TileKind.Floor
                                         && (HallIndex(mx * MacroSize + x) < 2 || HallIndex(mz * MacroSize + z) < 2);

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int hx = HallIndex(gx), hz = HallIndex(gz);
                bool ns = hx < 2, we = hz < 2;
                ulong h = Hashing.Hash(seed, gx, gz, SaltL1Detail);
                double r = Hashing.Unit(h);

                if (tile.Kind == TileKind.Wall && tile.Variant == 0 && tile.Pattern == WallPattern.WhiteBlock)
                {
                    // Block walls facing a corridor carry the halls' clutter of power boxes, pipes and pictures
                    ArchPier? face = IsCorridor(lx + 1, lz) ? ArchPier.East : IsCorridor(lx - 1, lz) ? ArchPier.West
                        : IsCorridor(lx, lz + 1) ? ArchPier.South : IsCorridor(lx, lz - 1) ? ArchPier.North : null;
                    if (face == null) continue;
                    tile.Pier = face.Value;
                    double stretch = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 6), Hashing.FloorDiv(gz, 6), SaltL1Detail + 1));
                    tile.Variant = r < 0.025 ? Decor.PowerBox : r < 0.037 ? Decor.Breaker : r < 0.062 ? Decor.Outlet
                        : r < 0.07 ? Decor.Extinguisher : r < 0.078 ? Decor.Alarm : r < 0.083 ? Decor.HoseCabinet
                        : r < 0.088 ? Decor.Note : r < 0.093 ? Decor.Graffiti : r < 0.108 ? (byte)(Decor.Painting + (int)((h >> 20) % 4))
                        : r < 0.111 ? Decor.Standpipe : r < 0.118 ? Decor.Camera : stretch < 0.22 ? Decor.Pipes : (byte)0;
                    continue;
                }
                if (tile.Kind != TileKind.Floor || !(ns || we)) continue;

                bool crossing = ns && we;
                // A tube every 6 blocks down the middle of each corridor; these halls keep their power in a blackout
                if (!crossing && ns && hx == 1 && Hashing.Mod(gz, 6) == 3) { tile.Ceiling = HallLightState(gx, gz); tile.Pier = ArchPier.North; }
                else if (!crossing && we && hz == 1 && Hashing.Mod(gx, 6) == 3) { tile.Ceiling = HallLightState(gx, gz); tile.Pier = ArchPier.West; }

                // Pipes along one side of every corridor, crossing at a junction box; a few joints leak
                bool leak = Hashing.Unit(h << 24) < 0.035;
                if (crossing && hx == 0 && hz == 0) tile.Pipe = Pipes.Hub;
                else if (ns && hx == 0) tile.Pipe = leak ? Pipes.DripZ : Pipes.RunZ;
                else if (we && hz == 0) tile.Pipe = leak ? Pipes.DripX : Pipes.RunX;
                if (tile.Pipe is Pipes.DripX or Pipes.DripZ)
                {
                    tile.Floor = FloorKind.ConcreteWet;
                    ref Tile next = ref b.At(Math.Min(lx + 1, MacroSize - 1), lz);
                    if (next.Kind == TileKind.Floor) next.Floor = FloorKind.ConcreteWet;
                }

                // Hanging EXIT signs at some crossings, loose wiring here and there
                if (crossing && hx == 1 && hz == 1 && r < 0.25) tile.Overhead = (h >> 30 & 1) == 0 ? Overheads.ExitSignWE : Overheads.ExitSignNS;
                else if (!crossing && tile.Ceiling == CeilingKind.Tile && tile.Pipe == 0 && r > 0.975) tile.Overhead = Overheads.WireDroop;

                // Things left lying against the walls
                if (crossing || tile.Variant != 0 || tile.SupplyBox) continue;
                ArchPier? wall = null;
                if (ns) wall = hx == 0 ? ArchPier.West : ArchPier.East;
                else if (we) wall = hz == 0 ? ArchPier.North : ArchPier.South;
                if (wall == null || r > 0.016) continue;
                (int wx, int wz) = Step(lx, lz, wall.Value);
                if (wx < 0 || wz < 0 || wx >= MacroSize || wz >= MacroSize || b.At(wx, wz).Kind != TileKind.Wall) continue;
                (int ax, int az) = Step(lx, lz, Turn(wall.Value));
                (int bx2, int bz2) = Step(lx, lz, Turn(Turn(Turn(wall.Value))));
                if (IsDoorAt(b, wx + (ax - lx), wz + (az - lz)) || IsDoorAt(b, wx + (bx2 - lx), wz + (bz2 - lz))) continue;
                tile.Pier = Opposite(wall.Value);
                tile.Variant = r < 0.005 ? Props.Plywood : r < 0.008 ? Props.Toolbox : r < 0.011 ? Props.CardboardBoxes
                    : r < 0.013 ? Props.Pallet : r < 0.0145 ? Props.Drum : Props.TrashCan;
            }
        }
    }

    private static bool IsDoorAt(Builder b, int x, int z) =>
        x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && b.At(x, z).Kind is TileKind.Doorway or TileKind.Door;

    private CeilingKind HallLightState(int gx, int gz)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL1Light));
        return r < 0.06 ? CeilingKind.LightOff : r < 0.1 ? CeilingKind.LightFlicker : CeilingKind.LightOn;
    }

    private enum HallRoom { Empty, Storage, Electrical, Workshop, Camp, Medical, Pump, Office, Break, Stairwell }

    /// <summary>
    /// Lays out one block between corridors, in block coordinates: (0,0) is its north-west perimeter corner, the
    /// inside runs 1-12. Plans depend only on the block's position, so neighbouring cells always agree.
    /// </summary>
    private Tile[] HallBlockPlan(int bx, int bz)
    {
        var tiles = new Tile[HallBlock * HallBlock];
        ulong h = Hashing.Hash(seed, bx, bz, SaltL1Block);
        var rng = new Rng(h);
        int gx0 = bx * HallGrid + HallOffset + 2, gz0 = bz * HallGrid + HallOffset + 2;
        ref Tile At(int u, int v) => ref tiles[v * HallBlock + u];

        for (int v = 0; v < HallBlock; v++)
        {
            for (int u = 0; u < HallBlock; u++)
            {
                ref Tile t = ref At(u, v);
                t.Floor = FloorKind.L1Hall;
                if (u == 0 || v == 0 || u == HallBlock - 1 || v == HallBlock - 1) SetWall(ref t, WallPattern.WhiteBlock, BaseStyle.Plain);
            }
        }

        // A door on the perimeter only works if the corridor outside it, and the door itself, are in a hall sector
        bool DoorOk(int u, int v)
        {
            int ox = u == 0 ? -1 : u == HallBlock - 1 ? 1 : 0, oz = v == 0 ? -1 : v == HallBlock - 1 ? 1 : 0;
            return IsHallAt(gx0 + u, gz0 + v) && IsHallAt(gx0 + u + ox, gz0 + v + oz);
        }

        // Blocks cut by the edge of the sector only hold rooms, and only rooms wholly inside it are open
        bool whole = IsHallAt(gx0 - 2, gz0 - 2) && IsHallAt(gx0 + HallBlock + 1, gz0 - 2)
                     && IsHallAt(gx0 - 2, gz0 + HallBlock + 1) && IsHallAt(gx0 + HallBlock + 1, gz0 + HallBlock + 1);
        bool Inside(int u, int v) => IsHallAt(gx0 + u, gz0 + v);
        double kind = rng.NextDouble();
        ulong plan = Hashing.Mix(h + 1);
        if (!whole) PlanRooms(tiles, plan, DoorOk, Inside);
        else if (kind < 0.5) PlanRooms(tiles, plan, DoorOk, null);
        else if (kind < 0.64) PlanOpenHall(tiles, plan, DoorOk, camp: false);
        else if (kind < 0.79) PlanThroughCorridor(tiles, plan, DoorOk, gx0, gz0);
        else if (kind < 0.89) PlanOpenHall(tiles, plan, DoorOk, camp: true);
        else if (kind < 0.95)
        {
            for (int v = 1; v < HallBlock - 1; v++)
                for (int u = 1; u < HallBlock - 1; u++)
                    SetWall(ref At(u, v), WallPattern.WhiteBlock, BaseStyle.Plain);
        }
        else PlanRooms(tiles, plan, DoorOk, null);
        return tiles;
    }

    private delegate bool DoorCheck(int u, int v);

    /// <summary>Splits the inside of a block into two to four rooms, each against the perimeter, each with a door.</summary>
    private static void PlanRooms(Tile[] tiles, ulong h, DoorCheck doorOk, DoorCheck inside)
    {
        var rng = new Rng(h);
        var leaves = new List<(int U0, int V0, int U1, int V1)>();
        var queue = new Queue<(int, int, int, int, int)>();
        queue.Enqueue((1, 1, HallBlock - 2, HallBlock - 2, 0));
        while (queue.Count > 0)
        {
            (int u0, int v0, int u1, int v1, int depth) = queue.Dequeue();
            int w = u1 - u0 + 1, d = v1 - v0 + 1;
            if (depth >= 2 || (w < 9 && d < 9) || (depth == 1 && rng.Chance(0.25)))
            {
                leaves.Add((u0, v0, u1, v1));
                continue;
            }
            bool splitU = w > d || (w == d && rng.Chance(0.5));
            if (splitU && w >= 9)
            {
                int s = rng.Range(u0 + 4, u1 - 4);
                for (int v = v0; v <= v1; v++) SetWall(ref tiles[v * HallBlock + s], WallPattern.WhiteBlock, BaseStyle.Plain);
                queue.Enqueue((u0, v0, s - 1, v1, depth + 1));
                queue.Enqueue((s + 1, v0, u1, v1, depth + 1));
            }
            else if (d >= 9)
            {
                int s = rng.Range(v0 + 4, v1 - 4);
                for (int u = u0; u <= u1; u++) SetWall(ref tiles[s * HallBlock + u], WallPattern.WhiteBlock, BaseStyle.Plain);
                queue.Enqueue((u0, v0, u1, s - 1, depth + 1));
                queue.Enqueue((u0, s + 1, u1, v1, depth + 1));
            }
            else leaves.Add((u0, v0, u1, v1));
        }

        bool stairwellDone = false;
        foreach (var leaf in leaves)
        {
            // Candidate door tiles: on the perimeter beside this room, away from its corners
            var doors = new List<(int U, int V, ArchPier Out)>();
            if (leaf.U0 == 1) for (int v = leaf.V0 + 1; v < leaf.V1; v++) doors.Add((0, v, ArchPier.West));
            if (leaf.V0 == 1) for (int u = leaf.U0 + 1; u < leaf.U1; u++) doors.Add((u, 0, ArchPier.North));
            if (leaf.U1 == HallBlock - 2) for (int v = leaf.V0 + 1; v < leaf.V1; v++) doors.Add((HallBlock - 1, v, ArchPier.East));
            if (leaf.V1 == HallBlock - 2) for (int u = leaf.U0 + 1; u < leaf.U1; u++) doors.Add((u, HallBlock - 1, ArchPier.South));
            doors.RemoveAll(d => !doorOk(d.U, d.V));
            if (inside != null && !(inside(leaf.U0, leaf.V0) && inside(leaf.U1, leaf.V0) && inside(leaf.U0, leaf.V1) && inside(leaf.U1, leaf.V1)))
                doors.Clear(); // cut through by the edge of the sector

            if (doors.Count == 0)
            {
                MarkSealed(tiles, leaf);
                continue;
            }
            var door = doors[rng.Range(0, doors.Count - 1)];
            ref Tile doorTile = ref tiles[door.V * HallBlock + door.U];
            int w = leaf.U1 - leaf.U0 + 1, d = leaf.V1 - leaf.V0 + 1;
            bool locked = rng.Chance(0.3);
            if (locked)
            {
                doorTile.Kind = TileKind.Door;
                MarkSealed(tiles, leaf);
                continue;
            }
            doorTile.Kind = TileKind.Doorway;

            // Wanderers' landmark: a cloth on the wall beside the door, outside
            if (rng.Chance(0.05))
            {
                (int su, int sv) = door.Out is ArchPier.North or ArchPier.South ? (door.U + 1, door.V) : (door.U, door.V + 1);
                ref Tile beside = ref tiles[sv * HallBlock + su];
                if (beside.Kind == TileKind.Wall && beside.Variant == 0)
                {
                    beside.Variant = (byte)(Decor.Banner + rng.Range(0, 3));
                    beside.Pier = door.Out;
                }
            }

            double r = rng.NextDouble();
            HallRoom kind = r < 0.3 ? HallRoom.Empty : r < 0.44 ? HallRoom.Storage : r < 0.53 ? HallRoom.Electrical
                : r < 0.62 ? HallRoom.Workshop : r < 0.69 ? HallRoom.Camp : r < 0.75 ? HallRoom.Medical
                : r < 0.82 ? HallRoom.Pump : r < 0.89 ? HallRoom.Office : HallRoom.Break;
            if (!stairwellDone && w >= 5 && d >= 5 && rng.Chance(0.12)) { kind = HallRoom.Stairwell; stairwellDone = true; }
            FurnishHallRoom(tiles, rng.NextULong(), leaf, door.U, door.V, kind);
        }
    }

    private static void MarkSealed(Tile[] tiles, (int U0, int V0, int U1, int V1) room)
    {
        for (int v = room.V0; v <= room.V1; v++)
            for (int u = room.U0; u <= room.U1; u++)
                tiles[v * HallBlock + u].Sealed = true;
    }

    /// <summary>
    /// Furnishes a small room. Props stand against its walls, never in the doorway or the tiles beside it, so the
    /// middle of the room stays clear.
    /// </summary>
    private static void FurnishHallRoom(Tile[] tiles, ulong h, (int U0, int V0, int U1, int V1) room, int doorU, int doorV, HallRoom kind)
    {
        var rng = new Rng(h);
        ref Tile At(int u, int v) => ref tiles[v * HallBlock + u];
        int cu = (room.U0 + room.U1) / 2, cv = (room.V0 + room.V1) / 2;
        bool NearDoor(int u, int v) => Math.Abs(u - doorU) + Math.Abs(v - doorV) <= 2;

        // Tiles against each wall, facing into the room
        var wallSpots = new List<(int U, int V, ArchPier Face)>();
        for (int u = room.U0; u <= room.U1; u++)
        {
            wallSpots.Add((u, room.V0, ArchPier.South));
            wallSpots.Add((u, room.V1, ArchPier.North));
        }
        for (int v = room.V0 + 1; v < room.V1; v++)
        {
            wallSpots.Add((room.U0, v, ArchPier.East));
            wallSpots.Add((room.U1, v, ArchPier.West));
        }
        wallSpots.RemoveAll(s => NearDoor(s.U, s.V));
        // Shuffle
        for (int i = wallSpots.Count - 1; i > 0; i--)
        {
            int j = rng.Range(0, i);
            (wallSpots[i], wallSpots[j]) = (wallSpots[j], wallSpots[i]);
        }
        int next = 0;
        bool Place(byte prop, byte stack = 0)
        {
            while (next < wallSpots.Count)
            {
                var s = wallSpots[next++];
                ref Tile t = ref At(s.U, s.V);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0 || t.SupplyBox) continue;
                t.Variant = prop;
                // Shelving is the one prop that names the wall it stands against rather than the way it faces
                t.Pier = prop == Props.Shelf ? Opposite(s.Face) : s.Face;
                t.Stack = stack;
                return true;
            }
            return false;
        }
        void Crates(int n)
        {
            for (int i = 0; i < n && next < wallSpots.Count; i++)
            {
                var s = wallSpots[next++];
                ref Tile t = ref At(s.U, s.V);
                if (t.Kind == TileKind.Floor && t.Variant == 0) t.Stack = (byte)rng.Range(1, 2);
            }
        }
        void Box()
        {
            while (next < wallSpots.Count)
            {
                var s = wallSpots[next++];
                ref Tile t = ref At(s.U, s.V);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stack != 0) continue;
                t.SupplyBox = true;
                return;
            }
        }
        // Decorations on the room's own walls, facing in
        void WallDecor(byte decor)
        {
            for (int attempt = 0; attempt < 12; attempt++)
            {
                int side = rng.Range(0, 3);
                int u = side switch { 0 => room.U0 - 1, 1 => room.U1 + 1, _ => rng.Range(room.U0, room.U1) };
                int v = side switch { 2 => room.V0 - 1, 3 => room.V1 + 1, _ => rng.Range(room.V0, room.V1) };
                ref Tile w = ref At(u, v);
                if (w.Kind != TileKind.Wall || w.Variant != 0) continue;
                w.Variant = decor;
                w.Pier = side switch { 0 => ArchPier.East, 1 => ArchPier.West, 2 => ArchPier.South, _ => ArchPier.North };
                return;
            }
        }

        bool lit = kind != HallRoom.Empty && rng.Chance(0.85);
        if (lit) At(cu, cv).Ceiling = CeilingKind.LightWarm;

        switch (kind)
        {
            case HallRoom.Empty:
                if (rng.Chance(0.3)) Place(Props.CardboardBoxes);
                if (rng.Chance(0.15)) Box();
                break;
            case HallRoom.Storage:
                for (int i = 0; i < 3; i++) Place(Props.Shelf);
                Place(Props.CardboardBoxes);
                Crates(rng.Range(1, 3));
                if (rng.Chance(0.5)) Place(Props.Pallet);
                if (rng.Chance(0.5)) Box();
                break;
            case HallRoom.Electrical:
                WallDecor(Decor.PowerBox);
                WallDecor(Decor.Breaker);
                WallDecor(Decor.Breaker);
                Place(Props.Switchgear);
                if (rng.Chance(0.5)) Place(Props.Switchgear);
                Place(Props.CableSpool);
                break;
            case HallRoom.Workshop:
                Place(Props.Workbench);
                Place(Props.Toolbox);
                Place(Props.Plywood);
                if (rng.Chance(0.6)) Place(Props.Plywood);
                Place(Props.Pallet);
                if (rng.Chance(0.4)) Place(Props.FoldingTable);
                WallDecor(Decor.Outlet);
                break;
            case HallRoom.Camp:
                Place(Props.Bedroll);
                if (rng.Chance(0.6)) Place(Props.Bedroll);
                Place(Props.Lantern);
                Crates(1);
                Box();
                if (rng.Chance(0.5)) Box();
                WallDecor((byte)(Decor.Banner + rng.Range(0, 3)));
                if (rng.Chance(0.4)) WallDecor(Decor.Note);
                break;
            case HallRoom.Medical:
                // A bed head against the wall, the foot pointing into the room
                for (int attempt = 0; attempt < 8 && wallSpots.Count > 0; attempt++)
                {
                    var s = wallSpots[rng.Range(0, wallSpots.Count - 1)];
                    var (fu, fv) = Step(s.U, s.V, s.Face);
                    if (fu < room.U0 || fu > room.U1 || fv < room.V0 || fv > room.V1 || NearDoor(fu, fv)) continue;
                    ref Tile head = ref At(s.U, s.V);
                    ref Tile foot = ref At(fu, fv);
                    if (head.Variant != 0 || foot.Variant != 0 || head.Stack != 0 || foot.Stack != 0) continue;
                    head.Variant = foot.Variant = Props.HospitalBed;
                    head.Pier = foot.Pier = s.Face;
                    head.Stack = 0;
                    foot.Stack = 1;
                    break;
                }
                Place(Props.MedCabinet);
                Place(Props.FoldingChair);
                Box();
                break;
            case HallRoom.Pump:
                WallDecor(Decor.Pipes);
                WallDecor(Decor.Pipes);
                WallDecor(Decor.Standpipe);
                Place(Props.Drum);
                if (rng.Chance(0.6)) Place(Props.Drum);
                for (int v = room.V0; v <= room.V1; v++)
                    for (int u = room.U0; u <= room.U1; u++)
                        if (rng.Chance(0.4)) At(u, v).Floor = FloorKind.ConcreteWet;
                At(cu, room.V0).Pipe = Pipes.DripX;
                break;
            case HallRoom.Office:
                Place(Props.FoldingTable);
                Place(Props.FoldingChair);
                Place(Props.FilingCabinet);
                Place(Props.CardboardBoxes);
                WallDecor(Decor.Note);
                break;
            case HallRoom.Break:
                if (room.U1 - room.U0 >= 4 && room.V1 - room.V0 >= 4 && !NearDoor(cu, cv))
                {
                    At(cu, cv).Variant = Props.FoldingTable;
                    foreach (ArchPier side in new[] { ArchPier.North, ArchPier.South, ArchPier.East, ArchPier.West })
                    {
                        var (su, sv) = Step(cu, cv, side);
                        if (rng.Chance(0.7) && At(su, sv).Variant == 0 && !NearDoor(su, sv)) { At(su, sv).Variant = Props.FoldingChair; At(su, sv).Pier = Opposite(side); }
                    }
                }
                Place(Props.TrashCan);
                if (rng.Chance(0.35)) Place(Props.Cooler);
                break;
            case HallRoom.Stairwell:
                PlanHallStairs(tiles, room, doorU, doorV);
                break;
        }
    }

    /// <summary>A flight of stairs along the wall opposite the door, climbing into the ceiling, under an EXIT sign.</summary>
    private static void PlanHallStairs(Tile[] tiles, (int U0, int V0, int U1, int V1) room, int doorU, int doorV)
    {
        ref Tile At(int u, int v) => ref tiles[v * HallBlock + u];
        bool doorOnU = doorU == room.U0 - 1 || doorU == room.U1 + 1;
        ref Tile door = ref At(doorU, doorV);
        door.ExitSign = true;
        if (doorOnU)
        {
            // Door in a west or east wall: the flight runs along the far north or south wall, climbing away from the door
            int v = doorV - room.V0 > room.V1 - doorV ? room.V0 : room.V1;
            ArchPier dir = doorU < room.U0 ? ArchPier.East : ArchPier.West;
            for (int k = 0; k < 3; k++)
            {
                int u = dir == ArchPier.East ? room.U1 - 2 + k : room.U0 + 2 - k;
                At(u, v).Stair = (byte)(k + 1);
                At(u, v).Pier = dir;
            }
        }
        else
        {
            int u = doorU - room.U0 > room.U1 - doorU ? room.U0 : room.U1;
            ArchPier dir = doorV < room.V0 ? ArchPier.South : ArchPier.North;
            for (int k = 0; k < 3; k++)
            {
                int v = dir == ArchPier.South ? room.V1 - 2 + k : room.V0 + 2 - k;
                At(u, v).Stair = (byte)(k + 1);
                At(u, v).Pier = dir;
            }
        }
        At((room.U0 + room.U1) / 2, (room.V0 + room.V1) / 2).Ceiling = CeilingKind.LightWarm;
    }

    /// <summary>
    /// A single big room: a maintenance hall littered with plywood, tables and toolboxes, or a wanderers'
    /// encampment of tents and bedrolls round a burning barrel. Wide openings face every corridor.
    /// </summary>
    private static void PlanOpenHall(Tile[] tiles, ulong h, DoorCheck doorOk, bool camp)
    {
        var rng = new Rng(h);
        ref Tile At(int u, int v) => ref tiles[v * HallBlock + u];
        int openings = 0;
        foreach ((int u, int v, int du, int dv) in new[] { (6, 0, 1, 0), (6, HallBlock - 1, 1, 0), (0, 6, 0, 1), (HallBlock - 1, 6, 0, 1) })
        {
            if (!doorOk(u, v) || !doorOk(u + du, v + dv)) continue;
            At(u, v).Kind = At(u + du, v + dv).Kind = TileKind.Doorway;
            openings++;
        }
        if (openings == 0)
        {
            MarkSealed(tiles, (1, 1, HallBlock - 2, HallBlock - 2));
            return;
        }

        bool Free(int u, int v) => At(u, v).Kind == TileKind.Floor && At(u, v).Variant == 0 && At(u, v).Stack == 0 && !At(u, v).SupplyBox
                                   && At(u, v).Stair == 0 && !(u >= 5 && u <= 8) && !(v >= 5 && v <= 8);
        void Against(byte prop, int n)
        {
            for (int i = 0, tries = 0; i < n && tries < 40; tries++)
            {
                int side = rng.Range(0, 3), along = rng.Range(1, HallBlock - 2);
                (int u, int v, ArchPier face) = side switch
                {
                    0 => (along, 1, ArchPier.South),
                    1 => (along, HallBlock - 2, ArchPier.North),
                    2 => (1, along, ArchPier.East),
                    _ => (HallBlock - 2, along, ArchPier.West),
                };
                if (!Free(u, v)) continue;
                At(u, v).Variant = prop;
                At(u, v).Pier = prop == Props.Shelf ? Opposite(face) : face;
                i++;
            }
        }

        // Lights in a loose grid
        for (int v = 2; v < HallBlock - 2; v += 4)
            for (int u = 2; u < HallBlock - 2; u += 4)
            {
                At(u + 1, v + 1).Ceiling = camp ? CeilingKind.LightWarm : rng.Chance(0.15) ? CeilingKind.LightOff : CeilingKind.LightOn;
                At(u + 1, v + 1).Pier = ArchPier.West;
            }

        if (camp)
        {
            Against(Props.Tent, rng.Range(2, 4));
            Against(Props.Bedroll, rng.Range(1, 3));
            Against(Props.Pallet, 1);
            Against(Props.FoldingChair, 2);
            int boxes = 0;
            for (int tries = 0; tries < 30 && boxes < 3; tries++)
            {
                int u = rng.Range(2, HallBlock - 3), v = rng.Range(2, HallBlock - 3);
                if (!Free(u, v)) continue;
                if (boxes == 0) At(u, v).Stack = 2;
                else At(u, v).SupplyBox = true;
                boxes++;
            }
            // The fire in the middle, a table beside it
            At(6, 6).Variant = Props.BurnBarrel;
            At(8, 7).Variant = Props.FoldingTable;
            At(8, 8).Variant = Props.Lantern;
            for (int i = 0; i < 2; i++)
            {
                int side = rng.Range(0, 3);
                int u = side switch { 0 => 0, 1 => HallBlock - 1, _ => rng.Range(2, HallBlock - 3) };
                int v = side switch { 2 => 0, 3 => HallBlock - 1, _ => rng.Range(2, HallBlock - 3) };
                if (At(u, v).Kind == TileKind.Wall && At(u, v).Variant == 0)
                {
                    At(u, v).Variant = (byte)(Decor.Banner + rng.Range(0, 3));
                    At(u, v).Pier = side switch { 0 => ArchPier.East, 1 => ArchPier.West, 2 => ArchPier.South, _ => ArchPier.North };
                }
            }
        }
        else
        {
            // Square columns hold the roof up
            foreach ((int u, int v) in new[] { (4, 4), (9, 4), (4, 9), (9, 9) }) SetWall(ref At(u, v), WallPattern.Concrete, BaseStyle.Plain);
            Against(Props.Plywood, rng.Range(2, 4));
            Against(Props.Workbench, 1);
            Against(Props.Toolbox, rng.Range(1, 3));
            Against(Props.Pallet, rng.Range(1, 2));
            Against(Props.CardboardBoxes, rng.Range(1, 3));
            Against(Props.Drum, rng.Range(0, 2));
            Against(Props.Shelf, rng.Range(0, 2));
            if (rng.Chance(0.6))
            {
                At(10, 6).Variant = Props.FoldingTable;
                At(10, 7).Variant = Props.FoldingTable;
                At(11, 6).Variant = Props.FoldingChair;
                At(11, 6).Pier = ArchPier.West;
            }
            if (rng.Chance(0.5)) At(2, 7).Pipe = Pipes.DripZ;
            for (int i = 0; i < 3; i++) At(rng.Range(2, HallBlock - 3), rng.Range(2, HallBlock - 3)).Overhead = Overheads.WireDroop;
            if (rng.Chance(0.4)) At(rng.Range(2, HallBlock - 3), rng.Range(2, HallBlock - 3)).SupplyBox = true;
        }
    }

    /// <summary>A corridor straight through the middle of the block, with small rooms either side of it.</summary>
    private void PlanThroughCorridor(Tile[] tiles, ulong h, DoorCheck doorOk, int gx0, int gz0)
    {
        var rng = new Rng(h);
        ref Tile At(int u, int v) => ref tiles[v * HallBlock + u];
        bool alongU = doorOk(0, 6) && doorOk(HallBlock - 1, 6) || !(doorOk(6, 0) && doorOk(6, HallBlock - 1)) && rng.Chance(0.5);
        // In (along, across) coordinates: the corridor runs along `along` at across 6-7, walls at 5 and 8
        ref Tile Cell(int along, int across) => ref alongU ? ref At(along, across) : ref At(across, along);

        for (int along = 0; along < HallBlock; along++)
        {
            for (int across = 1; across < HallBlock - 1; across++)
            {
                ref Tile t = ref Cell(along, across);
                if (across is 6 or 7)
                {
                    bool end = along == 0 || along == HallBlock - 1;
                    if (end && !(alongU ? doorOk(along, across) : doorOk(across, along))) continue;
                    t.Kind = TileKind.Floor;
                    t.Variant = 0;
                    if (!end && across == 7 && along % 5 == 2) { t.Ceiling = HallLightState(gx0 + along, gz0 + across); t.Pier = alongU ? ArchPier.West : ArchPier.North; }
                    if (!end && across == 6) t.Pipe = alongU ? Pipes.RunX : Pipes.RunZ;
                }
                else if ((across is 5 or 8) && along > 0 && along < HallBlock - 1) SetWall(ref t, WallPattern.WhiteBlock, BaseStyle.Plain);
            }
        }

        // Each side is split into two rooms with doors onto the corridor
        foreach ((int a0, int a1, int wall) in new[] { (1, 4, 5), (9, 12, 8) })
        {
            int split = rng.Range(5, 8);
            for (int across = a0; across <= a1; across++) SetWall(ref Cell(split, across), WallPattern.WhiteBlock, BaseStyle.Plain);
            foreach ((int l0, int l1) in new[] { (1, split - 1), (split + 1, HallBlock - 2) })
            {
                int doorAlong = rng.Range(l0 + 1, Math.Max(l0 + 1, l1 - 1));
                ref Tile door = ref Cell(doorAlong, wall);
                (int U0, int V0, int U1, int V1) room = alongU ? (l0, a0, l1, a1) : (a0, l0, a1, l1);
                if (rng.Chance(0.25))
                {
                    door.Kind = TileKind.Door;
                    MarkSealed(tiles, room);
                    continue;
                }
                door.Kind = TileKind.Doorway;
                double r = rng.NextDouble();
                HallRoom kind = r < 0.35 ? HallRoom.Empty : r < 0.5 ? HallRoom.Storage : r < 0.6 ? HallRoom.Workshop
                    : r < 0.7 ? HallRoom.Electrical : r < 0.8 ? HallRoom.Pump : r < 0.9 ? HallRoom.Office : HallRoom.Camp;
                (int du, int dv) = alongU ? (doorAlong, wall) : (wall, doorAlong);
                FurnishHallRoom(tiles, rng.NextULong(), room, du, dv, kind);
            }
        }
    }

    private static (int, int) Step(int x, int z, ArchPier dir) => dir switch
    {
        ArchPier.North => (x, z - 1),
        ArchPier.South => (x, z + 1),
        ArchPier.East => (x + 1, z),
        _ => (x - 1, z),
    };

    /// <summary>Turns a direction a quarter clockwise, seen from above.</summary>
    private static ArchPier Turn(ArchPier dir) => dir switch
    {
        ArchPier.North => ArchPier.East,
        ArchPier.East => ArchPier.South,
        ArchPier.South => ArchPier.West,
        _ => ArchPier.North,
    };

    private static ArchPier Opposite(ArchPier dir) => Turn(Turn(dir));

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
                if (tile.Kind != TileKind.Floor || tile.Ceiling != CeilingKind.Tile || tile.Beam || tile.Pipe != 0) continue;
                int row = Hashing.Mod(mz * MacroSize + lz, Module);
                if (row == 5 || row == 12)
                {
                    tile.Pipe = Pipes.RunX;
                    tile.Overhead = 0;
                }
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
