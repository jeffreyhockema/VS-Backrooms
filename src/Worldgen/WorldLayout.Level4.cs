using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 4, "Abandoned Office": a single endless office floor, almost completely devoid of furniture. Grey carpet
/// with darker rectangles where desks once stood, drywall with a dark skirting, a drop ceiling of troffers (about
/// half dead), air diffusers, sprinkler heads and water-stained tiles, and the odd tile missing. Most windows are
/// papered over or shut behind blinds; the few left clear look out onto rain and fog that never ends. Safe and
/// cool: drinking fountains, water coolers and vending machines still give Almond Water.
///
/// Cells are either open-plan floors (columns, cubicle farms, break nooks, the occasional reception) or office
/// blocks: a 2-wide corridor grid with small rooms between: offices (mostly emptied out, some locked), glass
/// conference rooms, break rooms, copy rooms, server rooms, storerooms, a manager's office, stairwells and
/// elevator lobbies. Corridors carry evacuation maps, fire alarms, clocks and the pale marks of pictures long
/// taken down.
/// </summary>
public sealed partial class WorldLayout
{
    private const int L4ColumnGrid = 7;
    private const int L4OfficeGrid = 8;

    private const ulong SaltL4Zone = 0x4D01;
    private const ulong SaltL4Room = 0x4D02;
    private const ulong SaltL4Light = 0x4D03;
    private const ulong SaltL4Section = 0x4D04;
    private const ulong SaltL4Detail = 0x4D05;

    private enum L4Room { Office, Conference, Break, Copy, Server, Storage, Manager, Stairwell, Elevators }

    private bool IsOfficeBlock(int mx, int mz) => Noise(mx / 3.0, mz / 3.0, SaltL4Zone) > 0.2;

    private Edge Level4Edge(ref Rng rng, int mx, int mz, int nx, int nz)
    {
        bool block = IsOfficeBlock(mx, mz), otherBlock = IsOfficeBlock(nx, nz);
        var edge = new Edge { Pattern = WallPattern.Drywall };

        // Office corridor grids run straight across
        if (block && otherBlock) return edge;

        if (!block && !otherBlock)
        {
            if (!rng.Chance(0.3)) return edge;
            // A wall of windows onto the storm, with a way through somewhere along it
            edge.Pattern = WallPattern.OfficeWindow;
            for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
            int gap = rng.Range(3, MacroSize - 6);
            for (int k = gap; k < gap + 3; k++) edge.Tiles[k] = EdgeTile.Open;
            return edge;
        }

        // Between an open floor and an office block: drywall with doorways, at the block's corridors
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        foreach (int at in new[] { rng.Range(0, 1) * L4OfficeGrid, 2 * L4OfficeGrid + rng.Range(0, 1) * L4OfficeGrid })
        {
            int start = Math.Max(1, at);
            edge.Tiles[start] = edge.Tiles[start + 1] = EdgeTile.Doorway;
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
                    if (c < 0.05) t.Worn = true;
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

        // Approaching the Terror Hotel the carpet warms to red and wood panelling creeps in
        if (TouchesLevel(mx, mz, 5)) WarmTowardsHotel(b, mx, mz);
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

        // Darker rectangles where desks and cabinets once stood
        int ghosts = rng.Range(4, 8);
        for (int n = 0; n < ghosts; n++)
        {
            int x0 = rng.Range(2, MacroSize - 5), z0 = rng.Range(2, MacroSize - 4), w = rng.Range(2, 3), h = rng.Range(1, 2);
            for (int z = z0; z <= z0 + h; z++)
                for (int x = x0; x <= x0 + w; x++)
                    if (b.At(x, z).Kind == TileKind.Floor) b.At(x, z).Floor = FloorKind.OfficeCarpetGhost;
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

        double feature = rng.NextDouble();
        if (feature < 0.35) AddCubicleFarm(b, mx, mz);
        else if (feature < 0.47) AddReception(b);
        if (rng.Chance(0.3)) AddBreakNook(b);
    }

    /// <summary>
    /// Rows of 3x3 cubicles back to back, each with a desk, a chair and an old computer, under full lights. Pattern
    /// along Z repeats every 9: a 2-wide aisle, a row of cubicles opening onto it, a shared back partition, and a
    /// row opening onto the next aisle. A few cubicles were cleared out.
    /// </summary>
    private void AddCubicleFarm(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        int x0 = rng.Range(2, 8), z0 = rng.Range(2, 6);
        int x1 = Math.Min(MacroSize - 2, x0 + rng.Range(14, 22)), z1 = Math.Min(MacroSize - 2, z0 + 18);
        for (int z = z0; z <= z1; z++)
        {
            for (int x = x0; x <= x1; x++)
            {
                ref Tile tile = ref b.At(x, z);
                if (tile.Kind != TileKind.Floor) continue;
                int row = (z - z0) % 9, col = (x - x0) % 4;
                tile.Floor = FloorKind.OfficeCarpet;
                tile.Variant = 0;
                int gx = mx * MacroSize + x, gz = mz * MacroSize + z;
                if (row <= 1)
                {
                    if (Hashing.Mod(gx, 3) == 1 && row == 0) tile.Ceiling = Level4LightState(gx, gz, 0.15);
                    continue; // aisle
                }
                if (row == 5) { tile.Variant = Props.Partition; tile.Pier = ArchPier.West; continue; }
                if (col == 0) { tile.Variant = Props.Partition; tile.Pier = ArchPier.North; continue; }
                bool rowA = row < 5;
                // Keyed on the whole cubicle (its first column, its band of rows in this floor), so it is cleared all at once
                bool cleared = Hashing.Unit(Hashing.Hash(seed, gx - col, mz * 64 + (z - z0) / 9 * 2 + (rowA ? 0 : 1), SaltL4Room + 9)) < 0.3;
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
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int ix = Hashing.Mod(gx, L4OfficeGrid), iz = Hashing.Mod(gz, L4OfficeGrid);
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
                L4Room room = kind < 0.42 ? L4Room.Office : kind < 0.53 ? L4Room.Conference : kind < 0.62 ? L4Room.Break
                    : kind < 0.68 ? L4Room.Copy : kind < 0.73 ? L4Room.Server : kind < 0.78 ? L4Room.Storage
                    : kind < 0.83 ? L4Room.Manager : kind < 0.92 ? L4Room.Stairwell : L4Room.Elevators;
                bool doorNorth = (int)((h >> 8) % 2) == 0;
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
                if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.Drywall || t.Variant != 0) continue;
                ArchPier? face = Walkable(lx, lz - 1) ? ArchPier.North : Walkable(lx, lz + 1) ? ArchPier.South
                    : Walkable(lx + 1, lz) ? ArchPier.East : Walkable(lx - 1, lz) ? ArchPier.West : null;
                if (face == null) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                ulong h = Hashing.Hash(seed, gx, gz, SaltL4Detail + 1);
                double r = Hashing.Unit(h);
                // In the office blocks, which side of this wall is a corridor?
                var (fx, fz) = Step(gx, gz, face.Value);
                bool corridor = office && (Hashing.Mod(fx, L4OfficeGrid) < 2 || Hashing.Mod(fz, L4OfficeGrid) < 2);
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

    private void WarmTowardsHotel(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                double patch = Noise((mx * MacroSize + lx) / 5.0, (mz * MacroSize + lz) / 5.0, SaltL4Zone + 7);
                if (patch < 0.15) continue;
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
}
