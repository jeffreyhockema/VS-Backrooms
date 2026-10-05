using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 4, "Abandoned Office": a single endless office floor. Grey carpet with darker rectangles where furniture
/// once stood, drywall columns, a drop ceiling with fluorescent troffers (about half dead) and the odd missing
/// tile, and walls of windows looking out onto heavy rain and fog that never ends. Safe and cool; vending machines
/// and water coolers still dispense Almond Water.
///
/// Cells are either open-plan floors (columns, cubicle farms, break nooks) or office blocks (a 2-wide corridor
/// grid with small lit offices, glass conference rooms, break rooms, stairwells that climb into the ceiling and
/// elevator lobbies whose doors never open).
/// </summary>
public sealed partial class WorldLayout
{
    private const int L4ColumnGrid = 7;
    private const int L4OfficeGrid = 8;

    private const ulong SaltL4Zone = 0x4D01;
    private const ulong SaltL4Room = 0x4D02;
    private const ulong SaltL4Light = 0x4D03;
    private const ulong SaltL4Section = 0x4D04;

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

        // Between an open floor and an office block: drywall with doorways
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        foreach (int at in new[] { rng.Range(2, 13), rng.Range(17, 28) }) edge.Tiles[at] = edge.Tiles[at + 1] = EdgeTile.Doorway;
        return edge;
    }

    private void BuildLevel4(Builder b, int mx, int mz)
    {
        for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i].Floor = FloorKind.OfficeCarpet;

        if (IsOfficeBlock(mx, mz)) BuildOfficeBlock(b, mx, mz);
        else BuildOpenPlan(b, mx, mz);

        // Missing ceiling tiles show the dark void above
        ref Rng rng = ref b.Rng;
        for (int i = 0; i < b.Tiles.Length; i++)
        {
            ref Tile t = ref b.Tiles[i];
            if (!t.IsWallLike && t.Ceiling == CeilingKind.Tile && rng.Chance(0.06)) t.Worn = true;
        }

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

        if (rng.Chance(0.35)) AddCubicleFarm(b, mx, mz);
        if (rng.Chance(0.25)) AddBreakNook(b);
    }

    /// <summary>
    /// Rows of 3x3 cubicles back to back, each with a desk, a chair and an old computer, under full lights. Pattern
    /// along Z repeats every 9: a 2-wide aisle, a row of cubicles opening onto it, a shared back partition, and a
    /// row opening onto the next aisle.
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
                int gx = mx * MacroSize + x, gz = mz * MacroSize + z;
                if (row <= 1)
                {
                    if (Hashing.Mod(gx, 3) == 1 && row == 0) tile.Ceiling = Level4LightState(gx, gz, 0.15);
                    continue; // aisle
                }
                if (row == 5) { tile.Variant = Props.Partition; tile.Pier = ArchPier.West; continue; }
                if (col == 0) { tile.Variant = Props.Partition; tile.Pier = ArchPier.North; continue; }
                bool rowA = row < 5;
                // Desk against the back partition with the chair in front of it
                if (col == 2 && (row == 4 || row == 6)) { tile.Variant = Props.Desk; tile.Pier = rowA ? ArchPier.North : ArchPier.South; }
                else if (col == 2 && (row == 3 || row == 7)) { tile.Variant = Props.OfficeChair; tile.Pier = rowA ? ArchPier.South : ArchPier.North; }
                if (col == 2 && (row == 3 || row == 7)) tile.Ceiling = Level4LightState(gx, gz, 0.15);
            }
        }
    }

    /// <summary>A vending machine and a water cooler beside a column, both still dispensing Almond Water.</summary>
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
            return;
        }
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
                // 0 office, 1 conference room, 2 break room, 3 stairwell, 4 elevator lobby
                int room = kind < 0.55 ? 0 : kind < 0.72 ? 1 : kind < 0.84 ? 2 : kind < 0.93 ? 3 : 4;

                if (perimeter)
                {
                    bool door = (int)((h >> 8) % 2) == 0 ? iz == 2 && ix == 4 : ix == 2 && iz == 5;
                    SetWall(ref tile, room == 1 ? WallPattern.OfficeGlass : WallPattern.Drywall, BaseStyle.Plain);
                    if (door)
                    {
                        tile.Kind = TileKind.Doorway;
                        tile.ExitSign = room == 3; // stairwells are signed
                    }
                    else if (room == 4 && iz == 7 && (ix == 4 || ix == 5))
                    {
                        tile.Kind = TileKind.Door;
                        tile.Pattern = WallPattern.Elevator;
                    }
                    continue;
                }

                // Room interior: offices are lit; others vary
                if (ix == 4 && iz == 4 || ix == 5 && iz == 5) tile.Ceiling = room == 0 || room == 1 ? CeilingKind.LightOn : Level4LightState(gx, gz, 0.5);
                switch (room)
                {
                    case 0:
                        if (ix == 4 && iz == 6) { tile.Variant = Props.Desk; tile.Pier = ArchPier.North; }
                        else if (ix == 4 && iz == 5) { tile.Variant = Props.OfficeChair; tile.Pier = ArchPier.South; }
                        else if (ix == 6 && iz == 3) { tile.Variant = Props.FilingCabinet; tile.Pier = ArchPier.South; }
                        break;
                    case 1:
                        if ((ix == 4 || ix == 5) && (iz == 4 || iz == 5)) tile.Variant = Props.ConferenceTable;
                        break;
                    case 2:
                        if (ix == 3 && iz == 6) { tile.Variant = Props.Vending; tile.Pier = ArchPier.North; }
                        else if (ix == 4 && iz == 6) { tile.Variant = Props.Cooler; tile.Pier = ArchPier.North; }
                        break;
                    case 3:
                        // Stairs along the back wall that climb into the ceiling
                        if (iz == 6 && ix >= 3 && ix <= 5) { tile.Stair = (byte)(ix - 2); tile.Pier = ArchPier.East; }
                        else if (iz == 6 && ix == 6) SetWall(ref tile, WallPattern.Drywall, BaseStyle.Plain);
                        break;
                }
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
                else if (tile.Kind == TileKind.Wall && tile.Pattern == WallPattern.Drywall) tile.Pattern = WallPattern.Hotel;
            }
        }
    }
}
