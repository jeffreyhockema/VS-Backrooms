using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 4, "Abandoned Office": a single endless office floor, almost completely devoid of furniture. Grey carpet
/// with darker rectangles where desks once stood, drywall with a dark skirting, a drop ceiling of troffers (about
/// half dead), air diffusers, sprinkler heads and water-stained tiles, and the odd tile missing. Most windows are
/// papered over or shut behind blinds; the few left clear look out onto rain and fog that never ends. Safe and
/// cool: drinking fountains, water coolers and vending machines still give Almond Water.
///
/// Cells are either open-plan floors or office blocks. Open floors have columns on a regular grid, troffer rows,
/// and in places the cubicle farms that once filled them, row after row continuing from one cell to the next, nearly
/// all cleared out now: partitions round pale squares of carpet. Office blocks are a 2-wide corridor grid with small
/// rooms between (offices, mostly emptied out, some locked; glass conference rooms, break rooms, copy rooms, server
/// rooms, storerooms, a manager's office, restrooms), crossed every <see cref="L4ConcourseEvery"/> rooms by a
/// broad, bright concourse. Stairs and elevators are found together, with restrooms, in building cores, about one in
/// each region of two cells by two that is offices. Corridors carry evacuation maps, fire alarms, clocks and the pale marks of
/// pictures long taken down. The windows are where the floor ends: the wall round the level, looking out on rain.
/// </summary>
public sealed partial class WorldLayout
{
    private const int L4ColumnGrid = 8;
    private const int L4OfficeGrid = 8;
    /// <summary>Every this many rooms of the office grid, each way, the rooms give way to a concourse.</summary>
    private const int L4ConcourseEvery = 6;
    /// <summary>Building cores: one per region of this many cells each way (where that cell is an office block).</summary>
    private const int L4CoreRegion = 2;
    /// <summary>Approaching the hotel (layout 5): all hotel red this many blocks from it, and none past the fringe.</summary>
    private const double L4HotelSolid = 5, L4HotelFringe = 14;

    private const ulong SaltL4Zone = 0x4D01;
    private const ulong SaltL4Room = 0x4D02;
    private const ulong SaltL4Light = 0x4D03;
    private const ulong SaltL4Section = 0x4D04;
    private const ulong SaltL4Detail = 0x4D05;
    private const ulong SaltL4Core = 0x4D06;
    private const ulong SaltL4Farm = 0x4D07;

    private enum L4Room { Office, Conference, Break, Copy, Server, Storage, Manager, Stairwell, Elevators, Restroom }

    /// <summary>Whether a position in an office block is part of a concourse rather than the grid of rooms.</summary>
    private static bool L4Concourse(int gx, int gz) =>
        Hashing.Mod(Hashing.FloorDiv(gx, L4OfficeGrid), L4ConcourseEvery) == 3 || Hashing.Mod(Hashing.FloorDiv(gz, L4OfficeGrid), L4ConcourseEvery) == 3;

    /// <summary>Whether a position in an office block is out in a corridor or a concourse.</summary>
    private static bool L4Corridor(int gx, int gz) =>
        Hashing.Mod(gx, L4OfficeGrid) < 2 || Hashing.Mod(gz, L4OfficeGrid) < 2 || L4Concourse(gx, gz);

    /// <summary>
    /// The building core of a region, if the cell picked for it is an office block: four rooms of the office grid
    /// in the middle of the cell, two elevator lobbies, a signed stairwell and a restroom, all round one crossing.
    /// Returns the grid position of the core's first room.
    /// </summary>
    private (int RoomX, int RoomZ)? L4Core(int mx, int mz)
    {
        if (!RegionPick(mx, mz, L4CoreRegion, SaltL4Core, 0.95) || !IsOfficeBlock(mx, mz)) return null;
        // The four rooms of the cell (it holds four by four) that no concourse runs through
        bool Rooms(int i) => Hashing.Mod(i, L4ConcourseEvery) != 3 && Hashing.Mod(i + 1, L4ConcourseEvery) != 3;
        int x0 = mx * MacroSize / L4OfficeGrid, z0 = mz * MacroSize / L4OfficeGrid;
        int rx = Rooms(x0 + 1) ? x0 + 1 : Rooms(x0) ? x0 : x0 + 2, rz = Rooms(z0 + 1) ? z0 + 1 : Rooms(z0) ? z0 : z0 + 2;
        return Rooms(rx) && Rooms(rz) ? (rx, rz) : null;
    }

    private bool IsOfficeBlock(int mx, int mz) => Noise(mx / 3.0, mz / 3.0, SaltL4Zone) > 0.2;

    private Edge Level4Edge(ref Rng rng, int mx, int mz, int nx, int nz)
    {
        bool block = IsOfficeBlock(mx, mz), otherBlock = IsOfficeBlock(nx, nz);
        var edge = new Edge { Pattern = WallPattern.Drywall };

        // Office corridor grids run straight across
        if (block && otherBlock) return edge;

        if (!block && !otherBlock) return edge; // one open floor

        // Between an open floor and an office block: drywall with doorways at the block's corridors, and wide open
        // where a concourse meets it
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        bool west = nx != mx;
        foreach (int at in new[] { rng.Range(0, 1) * L4OfficeGrid, 2 * L4OfficeGrid + rng.Range(0, 1) * L4OfficeGrid })
        {
            int start = Math.Max(1, at);
            edge.Tiles[start] = edge.Tiles[start + 1] = EdgeTile.Doorway;
        }
        for (int i = 1; i < MacroSize; i++)
        {
            int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
            // Along the edge, not down it (a concourse running the length of the wall is not crossing it)
            if (L4Concourse(west ? gx + 4 : gx, west ? gz : gz + 4) && L4Concourse(west ? gx - 4 : gx, west ? gz : gz - 4)) edge.Tiles[i] = EdgeTile.Open;
        }
        return edge;
    }

    private void BuildLevel4(Builder b, int mx, int mz)
    {
        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Floor = FloorKind.OfficeCarpet;

        if (IsOfficeBlock(mx, mz)) BuildOfficeBlock(b, mx, mz);
        else BuildOpenPlan(b, mx, mz);

        ref Rng rng = ref b.Rng;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                ulong h = Hashing.Hash(seed, mx * MacroSize + lx, mz * MacroSize + lz, SaltL4Detail);
                double r = Hashing.Unit(h);
                if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.OfficeWindow)
                {
                    // Most windows are papered over or shut behind blinds; the clear ones are not to be trusted
                    t.Variant = (byte)(r < 0.55 ? 1 : r < 0.82 ? 2 : 0);
                    continue;
                }
                if (t.IsWallLike) continue;
                // Missing ceiling tiles show the dark void above; others hold diffusers, sprinklers, stains
                if (t.Ceiling == CeilingKind.Tile)
                {
                    double c = Hashing.Unit(h << 20);
                    if (c < 0.05)
                    {
                        t.Worn = true;
                        // Half the gaps had a cable hanging out of them; from layout 5 about one in six does, as a
                        // ceiling full of them read as clutter
                        double droop = Version >= 5 ? 0.008 : 0.025;
                        if (c < droop) t.Pipe = c < droop / 2 ? Pipes.CableDroopX : Pipes.CableDroopZ;
                    }
                    else if (c < 0.12) t.Overhead = Overheads.CeilingVent;
                    else if (c < 0.2) t.Overhead = Overheads.CeilingSprinkler;
                    else if (c < 0.24) t.Overhead = Overheads.CeilingStain;
                }
                if (t.Floor == FloorKind.OfficeCarpet && t.Variant == 0)
                {
                    if (r < 0.025) t.Floor = FloorKind.OfficePapers;
                    else if (r < 0.04) t.Floor = FloorKind.OfficeStain;
                }
            }
        }

        DecorateOfficeWalls(b, mx, mz);

        // Approaching the Terror Hotel the carpet warms to red and wood panelling creeps in (up to layout version 8; from 9
        // the office is grey to the hotel's wall, and only the way through a gate has the hotel's carpet: WorldLayout.Linings.cs)
        if (Version < 9 && TouchesLevel(mx, mz, 5)) WarmTowardsHotel(b, mx, mz);

        // The End's way in (end-plan.md): now and then a lone wooden doorway stands on an open-plan floor
        if (EndEntrances && !IsOfficeBlock(mx, mz)) PlaceEndDoorframe(b, mx, mz);
    }

    /// <summary>
    /// The End's lone wooden doorway, in about one open-plan cell in sixty: on the open floor tile nearest the cell's
    /// middle with open floor all round it, so it can be walked through either way. Its own salt, so nothing else moves.
    /// </summary>
    private void PlaceEndDoorframe(Builder b, int mx, int mz)
    {
        ulong h = Hashing.Hash(seed, mx, mz, 0x1611);
        if (Hashing.Unit(h) >= 1 / 60.0) return;
        static bool Open(in Tile t) => t.Kind == TileKind.Floor && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Under == 0;
        for (int r = 0; r < 12; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int x = 16 + dx, z = 16 + dz;
                    if (x < 2 || z < 2 || x > MacroSize - 3 || z > MacroSize - 3) continue;
                    bool clear = true;
                    for (int ez = -1; ez <= 1 && clear; ez++)
                        for (int ex = -1; ex <= 1; ex++)
                            if (!Open(b.At(x + ex, z + ez))) { clear = false; break; }
                    if (!clear) continue;
                    ref Tile t = ref b.At(x, z);
                    t.Variant = Props.EndFrame;
                    t.Under = Unders.EndFrame;
                    t.Pier = (Hashing.Mix(h) & 1) == 0 ? ArchPier.North : ArchPier.East;
                    return;
                }
    }

    private void BuildOpenPlan(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (Hashing.Mod(gx, L4ColumnGrid) == 3 && Hashing.Mod(gz, L4ColumnGrid) == 3)
                {
                    SetWall(ref tile, WallPattern.Drywall, BaseStyle.Plain);
                    continue;
                }
                // Troffer rows; large open areas are mostly dark
                if (Hashing.Mod(gx, 3) == 1 && Hashing.Mod(gz, 4) == 2) tile.Ceiling = Level4LightState(gx, gz, 0.55);
            }
        }

        // Darker rectangles where rows of desks once stood, in the same rows as the cubicles elsewhere
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (Noise(gx / 30.0, gz / 30.0, SaltL4Farm + 1) < 0.2) continue;
                if (Hashing.Mod(gz, 9) is 3 or 4 or 6 && Hashing.Mod(gx, 4) is 1 or 2 && b.At(lx, lz).Kind == TileKind.Floor)
                    b.At(lx, lz).Floor = FloorKind.OfficeCarpetGhost;
            }

        // What little was left behind: a stack of chairs, boxes, a dead plant by a column, a lone chair
        for (int n = rng.Range(2, 5); n > 0; n--)
        {
            int x = rng.Range(2, MacroSize - 3), z = rng.Range(2, MacroSize - 3);
            ref Tile t = ref b.At(x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0) continue;
            double r = rng.NextDouble();
            t.Variant = r < 0.25 ? Props.ChairStack : r < 0.5 ? Props.CardboardBoxes : r < 0.7 ? Props.OfficeChair : r < 0.82 ? Props.TippedChair : Props.Wastebasket;
            t.Pier = (ArchPier)rng.Range(0, 3);
        }
        for (int lz = 2; lz < MacroSize - 2; lz++)
            for (int lx = 2; lx < MacroSize - 2; lx++)
                if (b.At(lx, lz).Kind == TileKind.Wall && b.At(lx + 1, lz).Kind == TileKind.Floor && b.At(lx + 1, lz).Variant == 0 && rng.Chance(0.15))
                    b.At(lx + 1, lz).Variant = Props.Ficus;

        AddCubicleFarm(b, mx, mz);
        if (rng.Chance(0.12)) AddReception(b);
        if (rng.Chance(0.3)) AddBreakNook(b);
    }

    /// <summary>
    /// Cubicle farms: rows of 3x3 cubicles back to back, laid out from block positions, so a farm runs on across
    /// cells for as far as it goes. Along Z the pattern repeats every 9: a 2-wide aisle, a row of cubicles opening
    /// onto it, a shared back partition, and a row opening onto the next aisle. Nearly all were cleared out long ago,
    /// leaving the partitions round a pale square of carpet; here and there a whole patch is still as it was left,
    /// each desk with its chair and its old computer.
    /// </summary>
    private void AddCubicleFarm(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        for (int z = 1; z < MacroSize - 1; z++)
        {
            for (int x = 1; x < MacroSize - 1; x++)
            {
                ref Tile tile = ref b.At(x, z);
                if (tile.Kind != TileKind.Floor || tile.Variant != 0) continue;
                int gx = mx * MacroSize + x, gz = mz * MacroSize + z;
                // A farm, and a margin round the columns so they stand in the aisles
                if (Noise(gx / 48.0, gz / 48.0, SaltL4Farm) < 0.25) continue;
                int row = Hashing.Mod(gz, 9), col = Hashing.Mod(gx, 4);
                tile.Floor = FloorKind.OfficeCarpet;
                if (Hashing.Mod(gx, 24) < 2) row = 0; // a cross aisle every few cubicles
                if (row <= 1)
                {
                    if (Hashing.Mod(gx, 3) == 1 && row == 0) tile.Ceiling = Level4LightState(gx, gz, 0.15);
                    continue; // aisle
                }
                if (row == 5) { tile.Variant = Props.Partition; tile.Pier = ArchPier.West; continue; }
                if (col == 0) { tile.Variant = Props.Partition; tile.Pier = ArchPier.North; continue; }
                bool rowA = row < 5;
                // Keyed on the whole cubicle, so it is cleared all at once; only in a few patches is anything left
                bool intact = Noise(gx / 20.0, gz / 20.0, SaltL4Farm + 2) > 0.5;
                bool cleared = Hashing.Unit(Hashing.Hash(seed, gx - col, Hashing.FloorDiv(gz, 9) * 2 + (rowA ? 0 : 1), SaltL4Room + 9)) < (intact ? 0.2 : 0.9);
                if (col == 2 && (row == 3 || row == 7)) tile.Ceiling = Level4LightState(gx, gz, 0.15);
                if (cleared)
                {
                    if (col == 2 && (row == 4 || row == 6)) tile.Floor = FloorKind.OfficeCarpetGhost;
                    continue;
                }
                // Desk against the back partition with the chair in front of it, a bin beside
                if (col == 2 && (row == 4 || row == 6)) { tile.Variant = Props.Desk; tile.Pier = rowA ? ArchPier.North : ArchPier.South; }
                else if (col == 2 && (row == 3 || row == 7)) { tile.Variant = Props.OfficeChair; tile.Pier = rowA ? ArchPier.South : ArchPier.North; }
                else if (col == 3 && (row == 4 || row == 6) && rng.Chance(0.4)) tile.Variant = Props.Wastebasket;
                else if (col == 1 && (row == 4 || row == 6) && rng.Chance(0.25)) { tile.Variant = Props.FilingCabinet; tile.Pier = rowA ? ArchPier.South : ArchPier.North; }
            }
        }
    }

    /// <summary>A vending machine and a water cooler beside a column, both still giving Almond Water.</summary>
    private static void AddBreakNook(Builder b)
    {
        ref Rng rng = ref b.Rng;
        for (int attempt = 0; attempt < 30; attempt++)
        {
            int x = rng.Range(2, MacroSize - 3), z = rng.Range(2, MacroSize - 3);
            if (b.At(x, z).Kind != TileKind.Wall || b.At(x, z + 1).Kind != TileKind.Floor || b.At(x + 1, z + 1).Kind != TileKind.Floor) continue;
            // Props face away from the column they stand against
            b.At(x, z + 1).Variant = Props.Vending;
            b.At(x, z + 1).Pier = ArchPier.South;
            b.At(x + 1, z + 1).Variant = Props.Cooler;
            b.At(x + 1, z + 1).Pier = ArchPier.South;
            if (b.At(x - 1, z + 1).Kind == TileKind.Floor) b.At(x - 1, z + 1).Variant = Props.Wastebasket;
            return;
        }
    }

    /// <summary>A reception desk facing a bench and a dead plant, the company long gone.</summary>
    private static void AddReception(Builder b)
    {
        ref Rng rng = ref b.Rng;
        int x = rng.Range(6, MacroSize - 10), z = rng.Range(6, MacroSize - 10);
        for (int dz = 0; dz <= 5; dz++)
            for (int dx = 0; dx <= 5; dx++)
                if (b.At(x + dx, z + dz).Kind != TileKind.Floor) return;
        for (int dx = 1; dx <= 3; dx++) { b.At(x + dx, z + 1).Variant = Props.ReceptionDesk; b.At(x + dx, z + 1).Pier = ArchPier.South; }
        b.At(x + 2, z).Variant = Props.OfficeChair;
        b.At(x + 2, z).Pier = ArchPier.South;
        b.At(x + 4, z).Variant = Props.CoatStand;
        for (int dx = 1; dx <= 3; dx++) { b.At(x + dx, z + 5).Variant = Props.Bench; b.At(x + dx, z + 5).Pier = ArchPier.North; }
        b.At(x, z + 5).Variant = Props.Ficus;
        b.At(x + 4, z + 5).Variant = Props.Ficus;
        b.At(x + 2, z + 3).Floor = FloorKind.OfficeStain;
    }

    /// <summary>A grid of 2-wide corridors every 8 blocks with a 4x4 room in each block between.</summary>
    private void BuildOfficeBlock(Builder b, int mx, int mz)
    {
        var core = L4Core(mx, mz);
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int ix = Hashing.Mod(gx, L4OfficeGrid), iz = Hashing.Mod(gz, L4OfficeGrid);
                if (L4Concourse(gx, gz))
                {
                    // A concourse: broad, bright, troffers in rows
                    if (Hashing.Mod(gx, 3) == 1 && Hashing.Mod(gz, 4) == 2) tile.Ceiling = Level4LightState(gx, gz, 0.12);
                    continue;
                }
                if (ix < 2 || iz < 2)
                {
                    // Corridors: dim, a troffer at every crossing
                    if (ix == 0 && iz == 0) tile.Ceiling = Level4LightState(gx, gz, 0.4);
                    continue;
                }

                int roomX = Hashing.FloorDiv(gx, L4OfficeGrid), roomZ = Hashing.FloorDiv(gz, L4OfficeGrid);
                ulong h = Hashing.Hash(seed, roomX, roomZ, SaltL4Room);
                double kind = Hashing.Unit(h);
                bool perimeter = ix == 2 || ix == 7 || iz == 2 || iz == 7;
                L4Room room = kind < 0.47 ? L4Room.Office : kind < 0.58 ? L4Room.Conference : kind < 0.68 ? L4Room.Break
                    : kind < 0.74 ? L4Room.Copy : kind < 0.79 ? L4Room.Server : kind < 0.86 ? L4Room.Storage
                    : kind < 0.93 ? L4Room.Manager : L4Room.Restroom;
                bool doorNorth = (int)((h >> 8) % 2) == 0;
                // The building core: elevators, stairs and a restroom round one crossing, every door toward it
                if (core is { } c && roomX - c.RoomX is 0 or 1 && roomZ - c.RoomZ is 0 or 1)
                {
                    int cdx = roomX - c.RoomX, cdz = roomZ - c.RoomZ;
                    room = cdz == 0 ? L4Room.Elevators : cdx == 0 ? L4Room.Stairwell : L4Room.Restroom;
                    doorNorth = cdz == 1;
                }
                // Some offices were locked when everyone left
                bool locked = room == L4Room.Office && Hashing.Unit(h << 40) < 0.2;

                if (perimeter)
                {
                    bool door = doorNorth ? iz == 2 && ix == 4 : ix == 2 && iz == 5;
                    SetWall(ref tile, room == L4Room.Conference ? WallPattern.OfficeGlass : WallPattern.Drywall, BaseStyle.Plain);
                    if (door)
                    {
                        tile.Kind = locked ? TileKind.Door : TileKind.Doorway;
                        tile.ExitSign = room == L4Room.Stairwell; // stairwells are signed
                    }
                    else if (room == L4Room.Elevators && iz == 7 && (ix == 4 || ix == 5))
                    {
                        // Two-wide elevator doors facing into the lobby
                        tile.Kind = TileKind.Door;
                        tile.Pattern = WallPattern.Elevator;
                        tile.Pier = ArchPier.North;
                        tile.Stack = (byte)(ix == 5 ? 0 : 1);
                    }
                    else if (room == L4Room.Elevators && iz == 7 && ix == 6)
                    {
                        tile.Variant = Decor.CallButton;
                        tile.Pier = ArchPier.North;
                    }
                    else if (room == L4Room.Stairwell && !doorNorth && ix == 2 && iz == 4)
                    {
                        tile.Variant = Decor.OfficeStairSign;
                        tile.Pier = ArchPier.West;
                    }
                    else if (room == L4Room.Stairwell && doorNorth && iz == 2 && ix == 5)
                    {
                        tile.Variant = Decor.OfficeStairSign;
                        tile.Pier = ArchPier.North;
                    }
                    continue;
                }

                if (locked) tile.Sealed = true;
                // Room interior: offices are lit; others vary
                if (ix == 4 && iz == 4 || ix == 5 && iz == 5) tile.Ceiling = room is L4Room.Office or L4Room.Conference or L4Room.Manager ? CeilingKind.LightOn : Level4LightState(gx, gz, 0.5);
                FurnishOfficeRoom(ref tile, room, ix, iz, h);
                // Nothing stands just inside the door
                if (doorNorth ? ix == 4 && iz == 3 : ix == 3 && iz == 5) { tile.Variant = 0; tile.Stack = 0; }
            }
        }
        if (Version >= 4 && core is { } stairs) BuildL4StairwellV4(b, mx, mz, stairs.RoomX, stairs.RoomZ + 1);
    }

    /// <summary>
    /// From layout version 4 a building core's stairwell has a flight up and a flight down, as Level 1's stairwells do
    /// (<see cref="StampStairwellV4"/>). A room of the office grid is too small for them, so the stairwell takes in the
    /// corridor along its east side as far as the restroom's wall: the flights run east from a landing inside its door,
    /// three steps up in the room under an opening in the ceiling and three more under the restroom's wall and the
    /// corridor's, in the dark; four steps down under an opening in the floor and two more under the wall. In room
    /// coordinates (ix 3-7 its own, then the corridor's 0-1, and the restroom's wall at 2):
    /// <code>
    ///   iz 2   #  #  door #  #  #  #  #  #      (the STAIRS sign beside the door, outside)
    ///   iz 3   #  L  L    U1 U2 U3 U4 U5 U6
    ///   iz 4   #  L  L    #  #  #  #  #  #
    ///   iz 5   #  L  L    D1 D2 D3 D4 D5 D6
    ///   iz 6   #  L  L    #  #  #  #  #  #
    ///   ix     2  3  4    5  6  7  0  1  2
    /// </code>
    /// The corridor between the stairwell and the restroom is walled up from crossing to crossing. The shaft over the
    /// flight up is walled off from the void over the drop ceiling: the column of its first step is solid above the
    /// ceiling, and every tile round the rest of it is wall.
    /// </summary>
    private void BuildL4StairwellV4(Builder b, int mx, int mz, int roomX, int roomZ)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        int farX = (roomX + 1) * L4OfficeGrid + 2 - x0, northZ = roomZ * L4OfficeGrid + 2 - z0;
        ref Tile At(int a, int c) => ref b.At(farX - a, northZ + c);
        // The room and the corridor beside it, cleared (the old stairs along the back wall too)
        for (int a = 1; a <= 7; a++)
            for (int c = 1; c <= 4; c++)
            {
                ref Tile t = ref At(a, c);
                t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.OfficeCarpet, Level = t.Level };
            }
        // The corridor walled up at both ends
        for (int a = 1; a <= 2; a++)
        {
            SetWall(ref At(a, 0), WallPattern.Drywall, BaseStyle.Plain);
            SetWall(ref At(a, 5), WallPattern.Drywall, BaseStyle.Plain);
        }
        StampStairwellV4((a, c) => ref At(a, c), ArchPier.East, 3, WallPattern.Drywall, false, -1);
        // A light over the landing's far corner, as likely as any other room's to be dead
        At(7, 4).Ceiling = Level4LightState(x0 + farX - 7, z0 + northZ + 4, 0.5);
    }

    /// <summary>One tile of an office-block room (interior 3-6 each way; the door is on the north or west wall).</summary>
    private static void FurnishOfficeRoom(ref Tile tile, L4Room room, int ix, int iz, ulong h)
    {
        void Put(ref Tile t, byte prop, ArchPier facing, byte stack = 0)
        {
            t.Variant = prop;
            t.Pier = facing;
            t.Stack = stack;
        }
        double r = Hashing.Unit(h << 16);
        switch (room)
        {
            case L4Room.Office:
                // Mostly emptied out: a pale mark where the desk stood, perhaps a chair left behind
                if (r < 0.45)
                {
                    if (ix == 4 && iz == 6 || ix == 5 && iz == 6) tile.Floor = FloorKind.OfficeCarpetGhost;
                    else if (ix == 5 && iz == 4 && r < 0.25) Put(ref tile, r < 0.08 ? Props.TippedChair : Props.OfficeChair, (ArchPier)((h >> 24) % 4));
                }
                else if (r < 0.78)
                {
                    if (ix == 4 && iz == 6) Put(ref tile, Props.Desk, ArchPier.North);
                    else if (ix == 4 && iz == 5) Put(ref tile, Props.OfficeChair, ArchPier.South);
                    else if (ix == 6 && iz == 3) Put(ref tile, Props.FilingCabinet, ArchPier.South);
                    else if (ix == 6 && iz == 6) Put(ref tile, Props.Wastebasket, ArchPier.North);
                }
                else
                {
                    if (ix == 6 && iz == 6) Put(ref tile, Props.CardboardBoxes, ArchPier.North);
                    else if (ix == 5 && iz == 6) Put(ref tile, Props.CardboardBoxes, ArchPier.North);
                    else if (ix == 6 && iz == 5) Put(ref tile, Props.ChairStack, ArchPier.North);
                }
                break;
            case L4Room.Conference:
                if ((ix == 4 || ix == 5) && (iz == 4 || iz == 5)) Put(ref tile, Props.ConferenceTable, ArchPier.North);
                else if ((ix == 4 || ix == 5) && iz == 3 && Hashing.Unit(h << (ix * 3)) < 0.75) Put(ref tile, Props.OfficeChair, ArchPier.South);
                else if ((ix == 4 || ix == 5) && iz == 6 && Hashing.Unit(h << (ix * 5)) < 0.75) Put(ref tile, Props.OfficeChair, ArchPier.North);
                else if (ix == 6 && (iz == 4 || iz == 5) && Hashing.Unit(h << (iz * 7)) < 0.6) Put(ref tile, Props.OfficeChair, ArchPier.West);
                break;
            case L4Room.Break:
                // Counters along the back wall, a fridge in the corner, a table in the middle
                if (iz == 6 && ix == 3) Put(ref tile, Props.KitchenCounter, ArchPier.North, 2);
                else if (iz == 6 && ix == 4) Put(ref tile, Props.KitchenCounter, ArchPier.North, 1);
                else if (iz == 6 && ix == 5) Put(ref tile, Props.KitchenCounter, ArchPier.North, 0);
                else if (iz == 6 && ix == 6) Put(ref tile, Props.Fridge, ArchPier.North);
                else if (ix == 6 && iz == 3) Put(ref tile, r < 0.5 ? Props.Vending : Props.Cooler, ArchPier.West);
                else if (ix == 4 && iz == 4) Put(ref tile, Props.RoundTable, ArchPier.North);
                else if (ix == 5 && iz == 4) Put(ref tile, Props.OfficeChair, ArchPier.West);
                break;
            case L4Room.Copy:
                if (iz == 6 && ix == 4) Put(ref tile, Props.Copier, ArchPier.North);
                else if (iz == 6 && ix == 6) Put(ref tile, Props.CardboardBoxes, ArchPier.North);
                else if (ix == 6 && iz == 4) Put(ref tile, Props.Shelf, ArchPier.East);
                else if (iz == 6 && ix == 3) Put(ref tile, Props.Wastebasket, ArchPier.North);
                break;
            case L4Room.Server:
                // Two rows of racks, humming in the dark
                if ((ix == 3 || ix == 6) && iz >= 4 && iz <= 6) Put(ref tile, Props.ServerRack, ix == 3 ? ArchPier.East : ArchPier.West);
                break;
            case L4Room.Storage:
                if (ix == 3 && iz == 3 && Hashing.Unit(h << 30) < 0.5) tile.SupplyBox = true; // someone's stash
                if (iz == 6 && ix >= 4) Put(ref tile, Props.OfficeBookshelf, ArchPier.North);
                else if (ix == 6 && iz == 4) Put(ref tile, Props.CardboardBoxes, ArchPier.North);
                else if (ix == 6 && iz == 3) Put(ref tile, Props.ChairStack, ArchPier.North);
                break;
            case L4Room.Manager:
                if (ix == 4 && iz == 5) Put(ref tile, Props.Desk, ArchPier.North);
                else if (ix == 4 && iz == 4) Put(ref tile, Props.OfficeChair, ArchPier.South);
                else if (iz == 6 && (ix == 5 || ix == 6)) Put(ref tile, Props.OfficeBookshelf, ArchPier.North);
                else if (ix == 6 && iz == 3) Put(ref tile, Props.Ficus, ArchPier.North);
                else if (ix == 3 && iz == 6) Put(ref tile, Props.CoatStand, ArchPier.North);
                break;
            case L4Room.Stairwell:
                // Stairs along the back wall that climb east into the ceiling, with room to step onto the first
                if (iz == 6 && ix >= 4 && ix <= 6) { tile.Stair = (byte)(ix - 3); tile.Pier = ArchPier.East; }
                break;
            case L4Room.Elevators:
                // A bench facing the doors, plants either side
                if (iz == 3 && (ix == 4 || ix == 5)) Put(ref tile, Props.Bench, ArchPier.South);
                else if (iz == 3 && (ix == 3 || ix == 6)) Put(ref tile, Props.Ficus, ArchPier.North);
                break;
            case L4Room.Restroom:
                // Two stalls along the back wall, a row of basins on the side wall
                if (iz == 6 && (ix == 3 || ix == 5)) Put(ref tile, Props.Toilet, ArchPier.North);
                else if (ix == 4 && iz >= 5) Put(ref tile, Props.Partition, ArchPier.North);
                else if (ix == 6 && iz is 3 or 4) Put(ref tile, Props.KitchenCounter, ArchPier.West, 1);
                break;
        }
    }

    /// <summary>
    /// Clocks, whiteboards, evacuation maps, fire alarms, fountains, light switches and the pale marks of frames
    /// long taken down, each on a wall facing somewhere you can stand.
    /// </summary>
    private void DecorateOfficeWalls(Builder b, int mx, int mz)
    {
        bool Walkable(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && b.At(x, z).Kind == TileKind.Floor
                                       && b.At(x, z).Variant == 0 && b.At(x, z).Stair == 0;
        bool office = IsOfficeBlock(mx, mz);

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.Drywall || t.Variant != 0 || t.Stair != 0) continue;
                ArchPier? face = Walkable(lx, lz - 1) ? ArchPier.North : Walkable(lx, lz + 1) ? ArchPier.South
                    : Walkable(lx + 1, lz) ? ArchPier.East : Walkable(lx - 1, lz) ? ArchPier.West : null;
                if (face == null) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                ulong h = Hashing.Hash(seed, gx, gz, SaltL4Detail + 1);
                double r = Hashing.Unit(h);
                // In the office blocks, which side of this wall is a corridor?
                var (fx, fz) = Step(gx, gz, face.Value);
                bool corridor = office && L4Corridor(fx, fz);
                // Light switches beside doorways, on the inside
                bool besideDoor = IsDoorAt(b, lx + 1, lz) || IsDoorAt(b, lx - 1, lz) || IsDoorAt(b, lx, lz + 1) || IsDoorAt(b, lx, lz - 1);
                byte decor;
                if (besideDoor && !corridor) decor = r < 0.6 ? Decor.LightSwitch : (byte)0;
                else if (corridor || !office)
                    decor = r < 0.012 ? Decor.Fountain : r < 0.026 ? Decor.EvacMap : r < 0.038 ? Decor.FireAlarm
                        : r < 0.048 ? Decor.ExtCabinet : r < 0.058 ? Decor.Clock : r < 0.088 ? Decor.FrameGhost
                        : r < 0.095 ? Decor.Phone : r < 0.103 ? (byte)(Decor.Poster + (int)((h >> 24) % 3)) : (byte)0;
                else
                    decor = r < 0.05 ? Decor.Whiteboard : r < 0.09 ? Decor.Corkboard : r < 0.13 ? Decor.Clock
                        : r < 0.2 ? Decor.FrameGhost : r < 0.24 ? (byte)(Decor.Poster + (int)((h >> 24) % 3)) : (byte)0;
                if (decor == 0) continue;
                t.Variant = decor;
                t.Pier = face.Value;
            }
        }
    }

    private CeilingKind Level4LightState(int gx, int gz, double deadChance)
    {
        double section = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 12), Hashing.FloorDiv(gz, 12), SaltL4Section));
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL4Light));
        if (section < 0.2) return CeilingKind.LightOff;
        return r < deadChance ? CeilingKind.LightOff : r < deadChance + 0.04 ? CeilingKind.LightFlicker : CeilingKind.LightOn;
    }

    /// <summary>
    /// Approaching the Terror Hotel the carpet turns to hotel red and wood panelling takes over the walls. From layout
    /// version 5 it is a ramp: all red within about <see cref="L4HotelSolid"/> blocks of the nearest Level 5 cell,
    /// ragged out to <see cref="L4HotelFringe"/> where the noise frays its edge, and grey office beyond (in 1-4,
    /// patches of red wherever the noise was high, in islands all over a cell beside the hotel).
    /// </summary>
    private void WarmTowardsHotel(Builder b, int mx, int mz)
    {
        // The Level 5 cells round this one, for the distance to the nearest
        var hotel = new List<(int Dx, int Dz)>();
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if ((dx != 0 || dz != 0) && LevelAt(mx + dx, mz + dz) == 5) hotel.Add((dx, dz));
        double ToHotel(int lx, int lz)
        {
            double best = double.MaxValue;
            foreach ((int dx, int dz) in hotel)
            {
                // Blocks to the nearest tile of that cell, along x and z (0 where the cell is level with this tile)
                int ax = dx < 0 ? lx + 1 : dx > 0 ? MacroSize - lx : 0, az = dz < 0 ? lz + 1 : dz > 0 ? MacroSize - lz : 0;
                best = Math.Min(best, Math.Sqrt(ax * ax + az * az));
            }
            return best;
        }
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                double patch = Noise((mx * MacroSize + lx) / 5.0, (mz * MacroSize + lz) / 5.0, SaltL4Zone + 7);
                if (Version >= 5 ? ToHotel(lx, lz) >= L4HotelSolid + (1 + patch) / 2 * (L4HotelFringe - L4HotelSolid) : patch < 0.15) continue;
                if (tile.Kind == TileKind.Floor) tile.Floor = FloorKind.HotelCarpet;
                // Walls that sign a stairwell or call an elevator stay as they are
                else if (tile.Kind == TileKind.Wall && tile.Pattern == WallPattern.Drywall && tile.Variant is not (Decor.OfficeStairSign or Decor.CallButton))
                {
                    tile.Pattern = WallPattern.Hotel;
                    if (tile.Variant >= Decor.First) tile.Variant = 0; // office fittings don't belong on panelling
                }
            }
        }
    }

    /// <summary>The tile a Level 4 refuge's wanderer keeps to, from layout version 5 (in <see cref="Tile.Detail"/>).</summary>
    internal const byte L4CampSite = 1;

    /// <summary>
    /// From layout version 5 a Level 4 refuge (<see cref="WandererSite"/>) is an outpost, as Level 1's camps are: round
    /// the spot the wanderer keeps to, bedrolls on the carpet, a camp lantern, a folding table and chair, boxes of what
    /// they have gathered and a crate of supplies, now and then a tent. No fire: the office is lit and nothing here
    /// needs keeping off. It is pitched in the open, on the clear floor nearest the cell's middle with five by five of
    /// it (else three by three, else wherever the wanderer would have stood before), after the cell's doorways are
    /// cleared and its pockets sealed; anything you cannot walk through stands clear of doors and of the wanderer's
    /// four sides, and keeps the floor round it joined up. The spot is marked, so the wanderer is put on it. From layout
    /// version 6 the bedrolls are sleeping bags and the tent a camp tent, as big as the real things (WorldLayout.Parts.cs).
    /// </summary>
    private void PitchL4Camp(Builder b, int mx, int mz)
    {
        if (!HasWandererSite(mx, mz, 4)) return;
        bool Clear(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1
            && b.At(x, z) is { Kind: TileKind.Floor, Variant: 0, Stack: 0, SupplyBox: false, Stair: 0, Sealed: false, Under: 0 };
        bool ClearAround(int x, int z, int r)
        {
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                    if (!Clear(x + dx, z + dz)) return false;
            return true;
        }
        const int c = MacroSize / 2;
        (int X, int Z)? found = null;
        for (int tier = 0; tier < 3 && found == null; tier++)
            for (int r = 0; r <= 12 && found == null; r++)
                for (int dz = -r; dz <= r && found == null; dz++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                        int x = c + dx, z = c + dz;
                        if (tier < 2 ? !ClearAround(x, z, 2 - tier) : !IsEntitySpot(b.At(x, z)) || b.At(x, z).Variant != 0) continue;
                        found = (x, z);
                        break;
                    }
        if (found is not (int sx, int sz)) return;
        b.At(sx, sz).Detail = L4CampSite;

        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltL4Detail + 2));
        int turn = rng.Range(0, 3);
        // Laid out facing north, then turned a quarter at a time
        (int, int) Turn(int dx, int dz)
        {
            for (int k = 0; k < turn; k++) (dx, dz) = (-dz, dx);
            return (dx, dz);
        }
        ArchPier TurnPier(ArchPier p)
        {
            for (int k = 0; k < turn; k++) p = p switch { ArchPier.North => ArchPier.East, ArchPier.East => ArchPier.South, ArchPier.South => ArchPier.West, _ => ArchPier.North };
            return p;
        }
        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z));
        bool NearOpening(int x, int z)
        {
            foreach ((int ox, int oz) in Ring)
            {
                int nx = x + ox, nz = z + oz;
                if (nx < 0 || nz < 0 || nx >= MacroSize || nz >= MacroSize) continue;
                if (b.At(nx, nz).Kind is TileKind.Door or TileKind.Doorway or TileKind.ArchDoor || b.At(nx, nz).Stair != 0) return true;
            }
            return false;
        }
        void Put(int dx, int dz, byte prop, ArchPier facing, bool box = false)
        {
            (int tx, int tz) = Turn(dx, dz);
            int x = sx + tx, z = sz + tz;
            if (!Clear(x, z)) return;
            if (box || !IsWalkThroughProp(prop))
            {
                // Clear of the wanderer's four sides and of doors, and never cutting the floor round it in two
                if (Math.Abs(tx) + Math.Abs(tz) == 1 || NearOpening(x, z) || !SafeToBlock(Open, x, z)) return;
                int open = 0;
                foreach ((int ox, int oz) in Ring) if (Open(x + ox, z + oz)) open++;
                if (open < 6) return;
            }
            ref Tile t = ref b.At(x, z);
            if (box) t.SupplyBox = true;
            else
            {
                t.Variant = prop;
                t.Pier = TurnPier(facing);
            }
        }
        // From layout version 6 the bedrolls are sleeping bags and the tent a camp tent, as big as the real things: the
        // parts are laid out turned with the camp, from the front-left (a sleeping bag's head)
        bool PutBig(int dx, int dz, byte prop, ArchPier facing)
        {
            (int tx, int tz) = Turn(dx, dz);
            bool Free(int x, int z) => Clear(x, z) && (IsWalkThroughProp(prop)
                || Math.Abs(x - sx) + Math.Abs(z - sz) > 1 && !NearOpening(x, z));
            return PutParts(b.At, MacroSize, Free, prop, sx + tx, sz + tz, TurnPier(facing));
        }
        bool v6 = Version >= 6;
        // Two bedrolls side by side behind the wanderer, the lantern between their heads
        if (v6)
        {
            PutBig(-1, -2, Props.SleepingBag, ArchPier.South);
            if (rng.Chance(0.6)) PutBig(1, -2, Props.SleepingBag, ArchPier.South);
        }
        else
        {
            Put(-1, -1, Props.Bedroll, ArchPier.South);
            if (rng.Chance(0.6)) Put(1, -1, Props.Bedroll, ArchPier.South);
        }
        Put(0, -2, Props.Lantern, ArchPier.North);
        // A folding table with its chair to one side, the hoard and the supplies to the other
        Put(-2, 1, Props.FoldingTable, ArchPier.North);
        Put(-1, 1, Props.FoldingChair, ArchPier.West);
        Put(2, 1, Props.CardboardBoxes, ArchPier.North);
        Put(2, 2, 0, ArchPier.North, box: true);
        if (rng.Chance(0.4)) Put(1, 2, Props.CardboardBoxes, ArchPier.North);
        // (the camp tent in the corner behind the sleeping bags, its door to the east)
        if (rng.Chance(0.5))
        {
            if (v6) PutBig(-2, -3, Props.CampTent, ArchPier.East);
            else Put(-2, -2, Props.Tent, ArchPier.East);
        }
    }
}
