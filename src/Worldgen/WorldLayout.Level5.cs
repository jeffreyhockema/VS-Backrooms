using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 5, "the Terror Hotel": a 1930s grand hotel that never ends. Long double-loaded corridors with red and
/// gold damask carpet, mahogany wainscot under red panels in gilt frames, candle sconces and dome lights, creepy
/// portraits, and numbered doors, most of them locked. Guest rooms behind open doors are cramped and sometimes
/// furnished. Grand lobbies have red faux-marble columns, chandeliers and palms under a taller ceiling; the
/// Beverly Room is a ballroom with a half-finished game of Mahjong under its chandelier; staff doors lead into hot
/// boiler halls of stained plaster, barred machinery bays, furnaces and leaking pipes.
///
/// Wings follow one global grid, so corridors line up across cells. Along Z it repeats every
/// <see cref="HallPeriod"/> blocks:
/// <code>
///   z % 11 == 0        back wall between two rows of rooms
///   z % 11 in 1..3     guest rooms (5 wide along X, five of them between each pair of cross corridors)
///   z % 11 == 4        corridor wall with room doors
///   z % 11 in 5..6     corridor
///   z % 11 == 7        corridor wall with room doors
///   z % 11 in 8..10    guest rooms
/// </code>
/// A cross corridor runs north-south every <see cref="CrossPeriod"/> blocks.
/// </summary>
public sealed partial class WorldLayout
{
    private const int HallPeriod = 11;
    /// <summary>Along a row of rooms: five blocks of room, then the wall to the next.</summary>
    private const int RoomPitch = 6;
    private const int CrossPeriod = 33;

    private const ulong SaltL5Zone = 0x5E01;
    private const ulong SaltL5Boiler = 0x5E02;
    private const ulong SaltL5Room = 0x5E03;
    private const ulong SaltL5Light = 0x5E04;
    private const ulong SaltL5Beverly = 0x5E05;
    private const ulong SaltL5Prop = 0x5E06;

    private enum HotelZone { Wing, Lobby, Boiler, Beverly }

    private enum HotelCell { Room, Corridor, Wall, Door }

    private HotelZone HotelZoneAt(int mx, int mz)
    {
        if (Noise(mx / 3.0, mz / 3.0, SaltL5Boiler) > 0.5) return HotelZone.Boiler;
        if (Noise(mx / 3.0, mz / 3.0, SaltL5Zone) > 0.48) return HotelZone.Lobby;
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL5Beverly)) < 0.05) return HotelZone.Beverly;
        return HotelZone.Wing;
    }

    private static HotelCell HotelCellAt(int gx, int gz)
    {
        int row = Hashing.Mod(gz, HallPeriod), xc = Hashing.Mod(gx, CrossPeriod);
        if (row == 5 || row == 6 || xc == 16 || xc == 17) return HotelCell.Corridor;
        if (xc == 15 || xc == 18 || row == 0) return HotelCell.Wall;
        int inRoom = RoomU(gx) % RoomPitch;
        if (row == 4 || row == 7) return inRoom == 2 ? HotelCell.Door : HotelCell.Wall;
        return inRoom == 5 ? HotelCell.Wall : HotelCell.Room;
    }

    /// <summary>
    /// Position along the row of rooms between two cross corridors, 0 to 28. Rooms are measured from the cross
    /// corridor, so it never cuts one in two.
    /// </summary>
    private static int RoomU(int gx) => Hashing.Mod(gx - 19, CrossPeriod);

    private static bool IsGrandZone(HotelZone zone) => zone is HotelZone.Lobby or HotelZone.Boiler;

    private Edge Level5Edge(ref Rng rng, int mx, int mz, int nx, int nz, bool west)
    {
        HotelZone a = HotelZoneAt(mx, mz), b = HotelZoneAt(nx, nz);
        bool wingA = a is HotelZone.Wing or HotelZone.Beverly, wingB = b is HotelZone.Wing or HotelZone.Beverly;
        var edge = new Edge { Pattern = a == HotelZone.Boiler && b == HotelZone.Boiler ? WallPattern.Plaster : WallPattern.Hotel };
        int gx0 = mx * MacroSize, gz0 = mz * MacroSize;

        if (wingA && wingB)
        {
            // The grid carries straight on across the edge
            for (int i = 1; i < MacroSize; i++)
            {
                HotelCell cell = west ? HotelCellAt(gx0, gz0 + i) : HotelCellAt(gx0 + i, gz0);
                edge.Tiles[i] = cell is HotelCell.Corridor or HotelCell.Room ? EdgeTile.Open : EdgeTile.Wall;
            }
            return edge;
        }
        if (a == b) return edge; // lobby into lobby, boiler hall into boiler hall: one big space

        // A wall between a wing and a grand room, or between a lobby and the boilers, with doorways where the
        // wing's corridors arrive (staff-only doors into the boiler halls)
        edge.Tall = true;
        edge.ExitSigns = a == HotelZone.Boiler || b == HotelZone.Boiler;
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        int doors = 0;
        for (int i = 2; i < MacroSize - 2; i++)
        {
            HotelCell cell = west ? HotelCellAt(gx0, gz0 + i) : HotelCellAt(gx0 + i, gz0);
            if (cell == HotelCell.Corridor) { edge.Tiles[i] = EdgeTile.Doorway; doors++; }
        }
        if (doors == 0) edge.Tiles[15] = edge.Tiles[16] = EdgeTile.Doorway;
        return edge;
    }

    private void BuildLevel5(Builder b, int mx, int mz, Edge west, Edge north)
    {
        switch (HotelZoneAt(mx, mz))
        {
            case HotelZone.Lobby: BuildLobby(b, mx, mz); break;
            case HotelZone.Boiler: BuildBoilerHall(b, mx, mz, west, north); break;
            case HotelZone.Beverly: BuildWing(b, mx, mz); BuildBeverlyRoom(b, mz); break;
            default: BuildWing(b, mx, mz); break;
        }
    }

    // ================= Guest wings =================

    private void BuildWing(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                tile.Floor = FloorKind.HotelCarpet;
                if (tile.Kind != TileKind.Floor) continue;

                int row = Hashing.Mod(gz, HallPeriod), xc = Hashing.Mod(gx, CrossPeriod);
                bool rowA = row <= 4;
                int u = RoomU(gx);
                int roomX = Hashing.FloorDiv(gx - 19, CrossPeriod) * 8 + u / RoomPitch, roomZ = Hashing.FloorDiv(gz, HallPeriod) * 2 + (rowA ? 0 : 1);
                ulong h = Hashing.Hash(seed, roomX, roomZ, SaltL5Room);
                bool locked = Hashing.Unit(h) < 0.65;
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL5Prop));

                switch (HotelCellAt(gx, gz))
                {
                    case HotelCell.Corridor:
                        // Dome lights every 4 blocks down the middle; the odd armchair left in the way
                        bool crossCorridor = xc == 16 || xc == 17;
                        if (crossCorridor ? xc == 16 && Hashing.Mod(gz, 4) == 0 : row == 5 && Hashing.Mod(gx, 4) == 0) tile.Ceiling = HotelLightState(gx, gz);
                        else if (r < 0.006) { tile.Variant = Props.WingChair; tile.Pier = (ArchPier)((h >> 4) % 4); }
                        break;

                    case HotelCell.Wall:
                        SetWall(ref tile, WallPattern.Hotel, BaseStyle.Plain);
                        // Corridor walls: sconces between doors, a portrait every other room; elevators on the cross corridors
                        if (row == 4 || row == 7)
                        {
                            if (xc == 15 || xc == 18) break;
                            if (u % RoomPitch == 5) tile.Variant = Props.WallSconce;
                            else if (u % RoomPitch == 0 && u / RoomPitch % 2 == 0) tile.Variant = Props.WallPortrait;
                        }
                        else if ((xc == 15 || xc == 18) && (row == 2 || row == 9) && r < 0.3)
                        {
                            tile.Kind = TileKind.Door;
                            tile.Pattern = WallPattern.Elevator;
                        }
                        break;

                    case HotelCell.Door:
                        SetWall(ref tile, WallPattern.Hotel, BaseStyle.Plain);
                        tile.Kind = locked ? TileKind.Door : TileKind.Doorway;
                        tile.Variant = (byte)((h >> 12) % 8); // room number plaque
                        break;

                    case HotelCell.Room:
                        if (Hashing.Unit(h >> 20) < 0.3) tile.Floor = FloorKind.HotelWood;
                        if (locked) tile.Sealed = true;
                        else FurnishGuestRoom(ref tile, u % RoomPitch, row, rowA, h);
                        break;
                }
            }
        }
    }

    /// <summary>Open rooms are often furnished: a bed against the back wall, a nightstand with a lamp, a wardrobe.</summary>
    private static void FurnishGuestRoom(ref Tile tile, int x, int row, bool rowA, ulong h)
    {
        if (Hashing.Unit(h >> 24) > 0.6) return; // empty room
        int back = rowA ? 1 : 10, middle = rowA ? 2 : 9;
        ArchPier facing = rowA ? ArchPier.South : ArchPier.North;
        if (x == 3 && row == back) { tile.Variant = Props.Bed; tile.Stack = 0; tile.Pier = facing; }
        else if (x == 3 && row == middle) { tile.Variant = Props.Bed; tile.Stack = 1; tile.Pier = facing; }
        else if (x == 4 && row == back) { tile.Variant = (h >> 30) % 10 == 0 ? Props.Turntable : Props.Nightstand; tile.Pier = facing; }
        else if (x == 0 && row == back) { tile.Variant = Props.Wardrobe; tile.Pier = facing; }
    }

    private CeilingKind HotelLightState(int gx, int gz)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL5Light));
        return r < 0.12 ? CeilingKind.LightOff : r < 0.16 ? CeilingKind.LightFlicker : CeilingKind.LightOn;
    }

    // ================= Grand lobby =================

    private void BuildLobby(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                tile.Grand = true;
                tile.Floor = FloorKind.HotelLobby;
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (Hashing.Mod(gx, 6) == 2 && Hashing.Mod(gz, 6) == 2)
                {
                    SetWall(ref tile, WallPattern.Marble, BaseStyle.Plain);
                    continue;
                }
                // A red carpet border around each column bay
                if (Hashing.Mod(gx, 6) == 5 || Hashing.Mod(gz, 6) == 5) tile.Floor = FloorKind.HotelCarpet;
                if (Hashing.Mod(gx, 6) == 5 && Hashing.Mod(gz, 6) == 5) tile.Ceiling = CeilingKind.Chandelier;

                double r = rng.NextDouble();
                if (Hashing.Mod(gx, 6) == 3 && Hashing.Mod(gz, 6) == 2 && r < 0.35) tile.Variant = Props.Palm;
                else if (r < 0.025) { tile.Variant = Props.WingChair; tile.Pier = (ArchPier)rng.Range(0, 3); }
                else if (r < 0.04) { tile.Variant = Props.Sofa; tile.Pier = (ArchPier)rng.Range(0, 3); }
                else if (r < 0.042) tile.Variant = Props.Turntable;
            }
        }
    }

    // ================= The Beverly Room =================

    /// <summary>A grand ballroom in the middle of a wing cell, reached from the corridors around it.</summary>
    private void BuildBeverlyRoom(Builder b, int mz)
    {
        const int x0 = 6, x1 = 25, z0 = 6, z1 = 25;
        for (int z = z0; z <= z1; z++)
        {
            for (int x = x0; x <= x1; x++)
            {
                ref Tile tile = ref b.At(x, z);
                tile = default;
                tile.Grand = true;
                tile.Floor = FloorKind.HotelMaroon;
                if (x == x0 || x == x1 || z == z0 || z == z1)
                {
                    SetWall(ref tile, WallPattern.Hotel, BaseStyle.Plain);
                    if (z != z0 && z != z1 && Hashing.Mod(z, 5) == 2) tile.Variant = Props.WallSconce;
                }
            }
        }

        // Two doors on the east wall and two on the west, each with a placard beside it
        foreach (int z in new[] { 11, 20 })
        {
            foreach (int x in new[] { x0, x1 })
            {
                b.At(x, z).Kind = TileKind.Doorway;
                b.At(x, z + 1).Variant = Props.WallBeverly;
                // Clear a way out: straight to the side of the cell, then along it to the nearest corridor row
                int dir = x == x0 ? -1 : 1, edgeX = x == x0 ? 1 : MacroSize - 2;
                for (int k = x + dir; k != edgeX + dir; k += dir) ClearForWalking(ref b.At(k, z));
                for (int zz = z; zz >= 1 && zz <= MacroSize - 2; zz += z < 16 ? -1 : 1)
                {
                    ClearForWalking(ref b.At(edgeX, zz));
                    if (Hashing.Mod(mz * MacroSize + zz, HallPeriod) is 5 or 6) break;
                }
            }
        }

        // The small Art Deco table with the unfinished game, under the great chandelier
        int cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
        b.At(cx, cz).Variant = Props.MahjongTable;
        foreach ((int x, int z) in new[] { (cx, cz - 1), (cx - 5, cz - 5), (cx + 5, cz - 5), (cx - 5, cz + 5), (cx + 5, cz + 5) })
            b.At(x, z).Ceiling = CeilingKind.Chandelier;
        foreach ((int x, int z, ArchPier f) in new[] { (x0 + 1, cz - 3, ArchPier.East), (x0 + 1, cz + 3, ArchPier.East), (x1 - 1, cz - 3, ArchPier.West), (x1 - 1, cz + 3, ArchPier.West) })
        {
            b.At(x, z).Variant = Props.Sofa;
            b.At(x, z).Pier = f;
        }
        b.At(x0 + 2, z0 + 2).Variant = Props.Turntable;
    }

    // ================= Boiler halls =================

    /// <summary>
    /// A central aisle along X with barred-off machinery bays on both sides holding boilers and glowing furnaces;
    /// pipes and leaks overhead, sparse bare bulbs, and every passage in the edges joined to the aisle.
    /// </summary>
    private void BuildBoilerHall(Builder b, int mx, int mz, Edge west, Edge north)
    {
        ref Rng rng = ref b.Rng;
        const int aisle0 = 13, aisle1 = 18;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                tile.Grand = true;
                tile.Floor = FloorKind.Dusty;
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx;

                if (lz >= aisle0 && lz <= aisle1)
                {
                    tile.Pipe = lz == aisle0 + 1 || lz == aisle1 - 1 ? (rng.Chance(0.05) ? Pipes.LeakX : Pipes.RunX) : Pipes.None;
                    if ((lz == aisle0 + 2 || lz == aisle1 - 2) && Hashing.Mod(gx, 6) == 3)
                        tile.Ceiling = rng.Chance(0.4) ? CeilingKind.LightOff : CeilingKind.LightWarm;
                    continue;
                }

                // Bays 5 wide between plaster walls, barred across the front
                bool front = lz == aisle0 - 1 || lz == aisle1 + 1;
                bool bayWall = Hashing.Mod(gx, 6) == 0 || lz == 1 || lz == MacroSize - 1;
                if (bayWall && !front) { SetWall(ref tile, WallPattern.Plaster, BaseStyle.Plain); continue; }
                if (front)
                {
                    tile.Kind = Hashing.Mod(gx, 6) == 0 ? TileKind.Wall : TileKind.Bars;
                    tile.Pattern = WallPattern.Plaster;
                    tile.Pier = ArchPier.West;
                    continue;
                }
                tile.Sealed = true; // behind the bars
                int inBay = Hashing.Mod(gx, 6);
                bool deep = lz <= 4 || lz >= MacroSize - 4;
                if (deep && inBay == 2) { tile.Variant = Props.Boiler; tile.Pier = lz < 16 ? ArchPier.South : ArchPier.North; }
                else if (deep && inBay == 4) { tile.Variant = Props.Furnace; tile.Pier = lz < 16 ? ArchPier.South : ArchPier.North; }
                else if (rng.Chance(0.02)) tile.SupplyBox = true;
            }
        }

        // Join every passage in the edges to the aisle
        void Clear(int x, int z)
        {
            ref Tile t = ref b.At(x, z);
            if (t.Kind is TileKind.Wall or TileKind.Bars && (x > 0 && z > 0)) { t.Kind = TileKind.Floor; t.Variant = 0; }
        }
        void ToAisle(int x, int z)
        {
            int target = z < aisle0 ? aisle0 : z > aisle1 ? aisle1 : z;
            for (int zz = Math.Min(z, target); zz <= Math.Max(z, target); zz++) Clear(x, zz);
        }
        foreach (int i in Passages(west))
        {
            for (int x = 1; x <= 3; x++) Clear(x, i);
            ToAisle(3, i);
        }
        foreach (int i in Passages(GetEdge(mx + 1, mz, west: true)))
        {
            for (int x = MacroSize - 4; x < MacroSize; x++) Clear(x, i);
            ToAisle(MacroSize - 4, i);
        }
        foreach (int i in Passages(north)) ToAisle(i, 1);
        foreach (int i in Passages(GetEdge(mx, mz + 1, west: false))) ToAisle(i, MacroSize - 1);
    }

    private static void ClearForWalking(ref Tile tile)
    {
        if (tile.Kind is TileKind.Wall or TileKind.Door or TileKind.Doorway) tile.Kind = TileKind.Floor;
        tile.Variant = 0;
        tile.Stack = 0;
    }
}
