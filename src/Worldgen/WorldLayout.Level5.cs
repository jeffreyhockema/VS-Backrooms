using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 5, "the Terror Hotel": a 1930s grand hotel that never ends, oddly clean and well kept. Long
/// double-loaded corridors with red and gold damask carpet (or walnut boards under a runner), mahogany wainscot
/// under red panels in gilt frames, candle sconces and dome lights, gilt mirrors and creepy portraits, brass
/// speakers playing jazz from nowhere, and console tables, bookshelves, curio cabinets and sofas along the walls.
/// Numbered doors with gold plaques, most of them locked; the guest rooms behind open doors are often fully
/// furnished. Elevators are rare: antique copper cages with a floor dial above, or now and then a modern lift.
///
/// Grand lobbies have red faux-marble columns over white marble, chandeliers, a front desk, a grandfather clock,
/// seating round coffee tables and palms; dining halls are laid for a dinner nobody comes to, a grand piano in the
/// corner; the Beverly Room is a ballroom lined with doors on every side, a half-finished game of Mahjong and
/// untouched drinks on the little table under its chandelier; staff doors lead into hot boiler halls of stained
/// plaster crowded with pipes and valves, barred machinery bays, furnaces and coal.
///
/// Wings follow one global grid, so corridors line up across cells. Along Z it repeats every
/// <see cref="HallPeriod"/> blocks:
/// <code>
///   z % 12 == 0        back wall between two rows of rooms
///   z % 12 in 1..3     guest rooms (5 wide along X, five of them between each pair of cross corridors)
///   z % 12 == 4        corridor wall with room doors
///   z % 12 in 5..7     corridor, 3 wide, with furniture along its walls
///   z % 12 == 8        corridor wall with room doors
///   z % 12 in 9..11    guest rooms
/// </code>
/// A 2-wide cross corridor runs north-south every <see cref="CrossPeriod"/> blocks.
/// </summary>
public sealed partial class WorldLayout
{
    private const int HallPeriod = 12;
    /// <summary>Along a row of rooms: five blocks of room, then the wall to the next.</summary>
    private const int RoomPitch = 6;
    private const int CrossPeriod = 33;

    private const ulong SaltL5Zone = 0x5E01;
    private const ulong SaltL5Boiler = 0x5E02;
    private const ulong SaltL5Room = 0x5E03;
    private const ulong SaltL5Light = 0x5E04;
    private const ulong SaltL5Beverly = 0x5E05;
    private const ulong SaltL5Prop = 0x5E06;
    private const ulong SaltL5Wood = 0x5E07;
    private const ulong SaltL5Lift = 0x5E08;

    private enum HotelZone { Wing, Lobby, Boiler, Beverly, Dining }

    private enum HotelCell { Room, Corridor, Wall, Door }

    private HotelZone HotelZoneAt(int mx, int mz)
    {
        if (Noise(mx / 3.0, mz / 3.0, SaltL5Boiler) > 0.5) return HotelZone.Boiler;
        if (Noise(mx / 3.0, mz / 3.0, SaltL5Zone) > 0.48) return HotelZone.Lobby;
        double r = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL5Beverly));
        if (r < 0.05) return HotelZone.Beverly;
        if (r < 0.11) return HotelZone.Dining;
        return HotelZone.Wing;
    }

    private static HotelCell HotelCellAt(int gx, int gz)
    {
        int row = Hashing.Mod(gz, HallPeriod), xc = Hashing.Mod(gx, CrossPeriod);
        if (row is 5 or 6 or 7 || xc == 16 || xc == 17) return HotelCell.Corridor;
        if (xc == 15 || xc == 18 || row == 0) return HotelCell.Wall;
        int inRoom = RoomU(gx) % RoomPitch;
        if (row == 4 || row == 8) return inRoom == 2 ? HotelCell.Door : HotelCell.Wall;
        return inRoom == 5 ? HotelCell.Wall : HotelCell.Room;
    }

    /// <summary>
    /// Position along the row of rooms between two cross corridors, 0 to 28. Rooms are measured from the cross
    /// corridor, so it never cuts one in two.
    /// </summary>
    private static int RoomU(int gx) => Hashing.Mod(gx - 19, CrossPeriod);

    private static bool IsGrandZone(HotelZone zone) => zone is HotelZone.Lobby or HotelZone.Boiler or HotelZone.Dining;

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
                edge.Tiles[i] = cell == HotelCell.Wall ? EdgeTile.Wall : EdgeTile.Open; // doors are laid by the cell itself
            }
            return edge;
        }
        if (a == b) return edge; // lobby into lobby, boiler hall into boiler hall: one big space

        // A wall between a wing and a grand room, or between two kinds of grand room, with doorways where the
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
            case HotelZone.Dining: BuildDiningHall(b, mx, mz); break;
            case HotelZone.Boiler: BuildBoilerHall(b, mx, mz, west, north); break;
            case HotelZone.Beverly: BuildWing(b, mx, mz); BuildBeverlyRoom(b, mz); AddElevators(b, mx, mz); break;
            default: BuildWing(b, mx, mz); AddElevators(b, mx, mz); break;
        }
    }

    // ================= Guest wings =================

    private void BuildWing(Builder b, int mx, int mz)
    {
        // Some wings are floored in walnut with a runner down the middle of the corridor
        bool walnut = Noise(mx / 2.0, mz / 2.0, SaltL5Wood) > 0.3;
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
                bool locked = Hashing.Unit(h) < 0.6;
                bool staffStairs = !locked && IsStaffStairs(h);
                ulong ph = Hashing.Hash(seed, gx, gz, SaltL5Prop);
                double r = Hashing.Unit(ph);

                switch (HotelCellAt(gx, gz))
                {
                    case HotelCell.Corridor:
                        bool crossCorridor = xc == 16 || xc == 17;
                        if (walnut) tile.Floor = crossCorridor ? (row is 5 or 6 or 7 ? FloorKind.HotelWood : FloorKind.HotelRunnerNS)
                                                              : row == 6 ? FloorKind.HotelRunnerWE : FloorKind.HotelWood;
                        // Dome lights every 4 blocks down the middle
                        if (crossCorridor ? xc == 16 && Hashing.Mod(gz, 4) == 0 && row is not (5 or 6 or 7) : row == 6 && Hashing.Mod(gx, 4) == 0)
                            tile.Ceiling = HotelLightState(gx, gz);
                        else if (!crossCorridor && (row == 5 || row == 7)) FurnishCorridor(ref tile, row, u, r, ph);
                        break;

                    case HotelCell.Wall:
                        SetWall(ref tile, WallPattern.Hotel, BaseStyle.Plain);
                        // Corridor walls: sconces between doors, portraits and mirrors, the odd speaker or phone
                        if ((row == 4 || row == 8) && xc != 15 && xc != 18)
                        {
                            tile.Pier = row == 4 ? ArchPier.South : ArchPier.North;
                            if (u % RoomPitch == 5) tile.Variant = Props.WallSconce;
                            else if (u % RoomPitch == 0 && u / RoomPitch % 2 == 0) tile.Variant = Props.WallPortrait;
                            else if (r < 0.06) tile.Variant = Decor.Mirror;
                            else if (r < 0.085) tile.Variant = Decor.Speaker;
                            else if (r < 0.1) tile.Variant = Decor.Landscape;
                            else if (r < 0.11) tile.Variant = Decor.HousePhone;
                            else if (r < 0.12) tile.Variant = Decor.FireHose;
                            else if (r < 0.13) tile.Variant = Decor.HotelClock;
                        }
                        break;

                    case HotelCell.Door:
                        SetWall(ref tile, WallPattern.Hotel, BaseStyle.Plain);
                        tile.Kind = locked ? TileKind.Door : TileKind.Doorway;
                        tile.Variant = (byte)((h >> 12) % 8); // room number plaque
                        tile.ExitSign = staffStairs;
                        break;

                    case HotelCell.Room:
                        bool wood = Hashing.Unit(h << 20) < 0.3;
                        if (wood) tile.Floor = FloorKind.HotelWood;
                        if (locked) tile.Sealed = true;
                        else if (staffStairs) PlanStaffStairs(ref tile, u % RoomPitch, row, rowA);
                        else FurnishGuestRoom(ref tile, u % RoomPitch, row, rowA, h, wood);
                        break;
                }
            }
        }
    }

    /// <summary>Now and then an open door under a STAFF sign leads not to a guest room but to a service stair.</summary>
    private static bool IsStaffStairs(ulong roomHash) => Hashing.Unit(roomHash << 44) < 0.025;

    /// <summary>
    /// A bare service stair along the back wall, climbing into the ceiling. Whoever climbs it comes out somewhere
    /// in the dark of Level 6.
    /// </summary>
    private static void PlanStaffStairs(ref Tile tile, int x, int row, bool rowA)
    {
        tile.Floor = FloorKind.Dusty;
        if (row != (rowA ? 1 : 11) || x < 1 || x > 3) return;
        tile.Stair = (byte)x;
        tile.Pier = ArchPier.East;
    }

    /// <summary>Furniture along a corridor wall, under the sconces: console tables, bookcases, cabinets, sofas.</summary>
    private static void FurnishCorridor(ref Tile tile, int row, int u, double r, ulong ph)
    {
        // Against the wall row 4 (north) or row 8 (south), facing into the corridor
        ArchPier facing = row == 5 ? ArchPier.South : ArchPier.North;
        int slot = u % RoomPitch;
        // A room-service tray left on the carpet outside a door, the plates still covered
        if (slot == 2 && r > 0.93) { tile.Variant = Props.RoomServiceTray; tile.Pier = facing; return; }
        if (slot is not (4 or 5 or 0) || r > 0.2) return;
        double k = r / 0.2;
        tile.Pier = facing;
        tile.Variant = k < 0.34 ? Props.ConsoleTable : k < 0.45 ? Props.HotelBookshelf : k < 0.52 ? Props.CurioCabinet
            : k < 0.61 ? Props.WingChair : k < 0.68 ? Props.Sofa : k < 0.74 ? Props.Radiator : k < 0.79 ? Props.LuggageCart
            : k < 0.84 ? Props.ServiceTrolley : k < 0.88 ? Props.LaundryCart : k < 0.91 ? Props.IceMachine
            : k < 0.96 ? Props.Palm : Props.GrandfatherClock;
        if (tile.Variant == Props.WingChair) tile.Pier = (ArchPier)((ph >> 8) % 4);
    }

    /// <summary>
    /// Open rooms are often fully furnished, as if someone still lived there: the bed's head against the back wall,
    /// a nightstand with a lamp, a wardrobe, a writing desk and chair by the door, a rug on bare boards.
    /// </summary>
    private static void FurnishGuestRoom(ref Tile tile, int x, int row, bool rowA, ulong h, bool wood)
    {
        int back = rowA ? 1 : 11, middle = rowA ? 2 : 10, front = rowA ? 3 : 9;
        if (wood && x >= 1 && x <= 3) tile.Floor = FloorKind.HotelRug;
        if (Hashing.Unit(h << 24) > 0.65) return; // empty room
        ArchPier into = rowA ? ArchPier.South : ArchPier.North; // away from the back wall
        double extra = Hashing.Unit(h << 36);
        // A ceiling fan over the foot of the bed, turning, that cannot be switched off
        if (x == 2 && row == front) tile.Overhead = Overheads.CeilingFan;
        if (x == 2 && row == back) { tile.Variant = Props.Bed; tile.Stack = 0; tile.Pier = into; }
        else if (x == 2 && row == middle) { tile.Variant = Props.Bed; tile.Stack = 1; tile.Pier = into; }
        else if (x == 3 && row == back) { tile.Variant = (h >> 30) % 10 == 0 ? Props.Turntable : Props.Nightstand; tile.Pier = into; }
        else if (x == 1 && row == back && extra < 0.6) { tile.Variant = Props.Nightstand; tile.Pier = into; }
        else if (x == 4 && row == back) { tile.Variant = Props.Wardrobe; tile.Pier = into; }
        else if (x == 0 && row == front && extra > 0.3) { tile.Variant = Props.WritingDesk; tile.Pier = ArchPier.East; }
        // The desk chair is drawn up from the side, so the corner by the bed can still be reached
        else if (x == 0 && row == middle && extra > 0.3) { tile.Variant = Props.HotelChair; tile.Pier = rowA ? ArchPier.South : ArchPier.North; }
        else if (x == 4 && row == front && extra < 0.45) { tile.Variant = extra < 0.2 ? Props.FloorLamp : Props.WingChair; tile.Pier = ArchPier.West; }
        else if (x == 3 && row == middle && extra > 0.85) { tile.Variant = Props.Suitcase; tile.Pier = ArchPier.West; }
    }

    /// <summary>
    /// Elevators are rare: in a cross corridor wall, two blocks wide, with a dial or indicator above and a call
    /// plate beside. Most are antique copper cages; a few are modern lifts that make no more sense.
    /// </summary>
    private void AddElevators(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize - 1; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int xc = Hashing.Mod(gx, CrossPeriod), row = Hashing.Mod(gz, HallPeriod);
                if (xc != 15 && xc != 18 || row != 2 && row != 9) continue;
                // The doors must open onto the cross corridor inside this cell
                int front = xc == 15 ? lx + 1 : lx - 1;
                if (front < 1 || front >= MacroSize || b.At(front, lz).Kind != TileKind.Floor || b.At(front, lz + 1).Kind != TileKind.Floor) continue;
                ulong h = Hashing.Hash(seed, Hashing.FloorDiv(gx, CrossPeriod) * 2 + (xc == 15 ? 0 : 1), Hashing.FloorDiv(gz, HallPeriod) * 2 + (row == 2 ? 0 : 1), SaltL5Lift);
                if (Hashing.Unit(h) > 0.1) continue;
                ArchPier facing = xc == 15 ? ArchPier.East : ArchPier.West;
                byte style = (byte)(Hashing.Unit(h << 20) < 0.3 ? 1 : 0);
                bool smallerIsLeft = LeftIsSmaller(facing);
                if (b.At(lx, lz).Kind != TileKind.Wall || b.At(lx, lz + 1).Kind != TileKind.Wall || b.At(lx, lz).Grand || b.At(lx, lz + 1).Grand) continue;
                for (int k = 0; k < 2; k++)
                {
                    ref Tile t = ref b.At(lx, lz + k);
                    t.Kind = TileKind.Door;
                    t.Pattern = WallPattern.Elevator;
                    t.Variant = style;
                    t.Pier = facing;
                    t.Stack = (byte)((k == 0) == smallerIsLeft ? 0 : 1);
                }
                // The call plate on the wall beside the doors
                int plateZ = row == 2 ? lz - 1 : lz + 2;
                if (plateZ >= 0 && plateZ < MacroSize && b.At(lx, plateZ).Kind == TileKind.Wall)
                {
                    b.At(lx, plateZ).Variant = Decor.CallPlate;
                    b.At(lx, plateZ).Pier = facing;
                }
            }
        }
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
                tile.Floor = FloorKind.HotelMarble;
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int cx = Hashing.Mod(gx, 6), cz = Hashing.Mod(gz, 6);
                if (cx == 2 && cz == 2)
                {
                    SetWall(ref tile, WallPattern.Marble, BaseStyle.Plain);
                    continue;
                }
                // A red carpet border around each column bay, a chandelier at each crossing
                if (cx == 5 || cz == 5) tile.Floor = FloorKind.HotelCarpet;
                if (cx == 5 && cz == 5) tile.Ceiling = CeilingKind.Chandelier;
            }
        }

        // Each bay between columns is furnished as something: a seating group, the front desk, a quiet corner
        int bx0 = Hashing.FloorDiv(mx * MacroSize, 6), bz0 = Hashing.FloorDiv(mz * MacroSize, 6);
        for (int bz = bz0; bz <= bz0 + 6; bz++)
        {
            for (int bx = bx0; bx <= bx0 + 6; bx++)
            {
                double r = Hashing.Unit(Hashing.Hash(seed, bx, bz, SaltL5Prop + 1));
                int x0 = bx * 6 - mx * MacroSize, z0 = bz * 6 - mz * MacroSize; // bay tiles 0..4 hold furniture, column at (2,2)
                void Put(int dx, int dz, byte prop, ArchPier facing)
                {
                    int x = x0 + dx, z = z0 + dz;
                    if (x < 1 || z < 1 || x >= MacroSize || z >= MacroSize) return;
                    ref Tile t = ref b.At(x, z);
                    if (t.Kind != TileKind.Floor || t.Variant != 0) return;
                    t.Variant = prop;
                    t.Pier = facing;
                }
                if (r < 0.32)
                {
                    // Sofa and armchairs round a coffee table
                    Put(0, 1, Props.Sofa, ArchPier.East);
                    Put(1, 0, Props.WingChair, ArchPier.South);
                    Put(1, 3, Props.WingChair, ArchPier.North);
                    Put(1, 1, Props.CoffeeTable, ArchPier.North);
                    Put(0, 3, Props.AshtrayStand, ArchPier.North);
                    Put(4, 4, Props.FloorLamp, ArchPier.North);
                }
                else if (r < 0.4)
                {
                    // The front desk, guest book and bell, a clock behind
                    Put(1, 4, Props.FrontDesk, ArchPier.North);
                    Put(2, 4, Props.FrontDesk, ArchPier.North);
                    Put(3, 4, Props.FrontDesk, ArchPier.North);
                    Put(4, 3, Props.GrandfatherClock, ArchPier.West);
                    Put(0, 3, Props.LuggageCart, ArchPier.North);
                }
                else if (r < 0.5)
                {
                    Put(3, 2, Props.Palm, ArchPier.North);
                    Put(1, 2, Props.Palm, ArchPier.North);
                    Put(4, 1, Props.HotelBookshelf, ArchPier.West);
                }
                else if (r < 0.56) Put(3, 2, Props.Turntable, ArchPier.North);
                else if (r < 0.62) Put(rng.Range(0, 4), rng.Range(0, 1), Props.LuggageCart, ArchPier.North);
                else if (r < 0.72) Put(3, 2, Props.Palm, ArchPier.North);
            }
        }
    }

    // ================= Dining hall =================

    /// <summary>A dining room laid for a dinner nobody comes to: round tables under chandeliers, a piano, music.</summary>
    private void BuildDiningHall(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile tile = ref b.At(lx, lz);
                tile.Grand = true;
                tile.Floor = FloorKind.HotelWood;
                if (tile.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int cx = Hashing.Mod(gx, 5), cz = Hashing.Mod(gz, 5);
                // Tables every 5 blocks with a chair on each side, a chandelier over every other one
                if (cx == 2 && cz == 2 && lx > 2 && lz > 2 && lx < MacroSize - 3 && lz < MacroSize - 3)
                {
                    tile.Variant = Props.DiningTable;
                    tile.Floor = FloorKind.HotelRug;
                    if (Hashing.Mod(gx / 5 + gz / 5, 2) == 0) tile.Ceiling = CeilingKind.Chandelier;
                    continue;
                }
                if (lx <= 2 || lz <= 2 || lx >= MacroSize - 3 || lz >= MacroSize - 3) continue;
                ArchPier? chair = (cx, cz) switch { (2, 1) => ArchPier.South, (2, 3) => ArchPier.North, (1, 2) => ArchPier.East, (3, 2) => ArchPier.West, _ => null };
                if (chair != null && rng.Chance(0.85))
                {
                    tile.Variant = Props.HotelChair;
                    tile.Pier = chair.Value;
                    tile.Floor = FloorKind.HotelRug;
                }
            }
        }
        // A grand piano and a speaker in one corner, palms in the others
        ref Tile piano = ref b.At(4, 3);
        if (piano.Kind == TileKind.Floor) { piano.Variant = Props.GrandPiano; piano.Pier = ArchPier.South; }
        foreach ((int x, int z) in new[] { (MacroSize - 3, 2), (2, MacroSize - 3), (MacroSize - 3, MacroSize - 3) })
            if (b.At(x, z).Kind == TileKind.Floor) b.At(x, z).Variant = Props.Palm;
        b.At(8, 2).Variant = Props.Turntable;
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
                    // Doors on every side: most locked, a few open onto somewhere else entirely
                    bool corner = (x == x0 || x == x1) && (z == z0 || z == z1);
                    int along = x == x0 || x == x1 ? z : x;
                    if (!corner && along % 2 == 1 && along > x0 + 1 && along < x1 - 1)
                    {
                        tile.Kind = TileKind.Door;
                        tile.Variant = (byte)(along % 8);
                    }
                    else if (!corner && z != z0 && z != z1 && along % 4 == 0) tile.Variant = Props.WallSconce;
                }
            }
        }

        // Two real doorways on the east wall and two on the west, each with a placard beside it
        foreach (int z in new[] { 11, 20 })
        {
            foreach (int x in new[] { x0, x1 })
            {
                b.At(x, z).Kind = TileKind.Doorway;
                b.At(x, z).Variant = 0;
                b.At(x, z + 1).Kind = TileKind.Wall;
                b.At(x, z + 1).Variant = Props.WallBeverly;
                // Clear a way out: straight to the side of the cell, then along it to the nearest corridor row
                int dir = x == x0 ? -1 : 1, edgeX = x == x0 ? 1 : MacroSize - 2;
                for (int k = x + dir; k != edgeX + dir; k += dir) ClearForWalking(ref b.At(k, z));
                for (int zz = z; zz >= 1 && zz <= MacroSize - 2; zz += z < 16 ? -1 : 1)
                {
                    ClearForWalking(ref b.At(edgeX, zz));
                    if (Hashing.Mod(mz * MacroSize + zz, HallPeriod) is 5 or 6 or 7) break;
                }
            }
        }

        // The corridors squeezed round the room are kept clear
        for (int z = z0 - 1; z <= z1 + 1; z++)
            for (int x = x0 - 1; x <= x1 + 1; x++)
            {
                if (x >= x0 && x <= x1 && z >= z0 && z <= z1) continue;
                ref Tile t = ref b.At(x, z);
                if (t.Kind == TileKind.Floor) { t.Variant = 0; t.Stack = 0; }
            }

        // The small Art Deco table with the unfinished game and its drinks, under the great chandelier
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
        b.At(x1 - 2, z0 + 2).Variant = Props.Palm;
        b.At(x0 + 2, z1 - 2).Variant = Props.Palm;
        b.At(x1 - 2, z1 - 2).Variant = Props.GrandfatherClock;
        b.At(x1 - 2, z1 - 2).Pier = ArchPier.North;
    }

    // ================= Boiler halls =================

    /// <summary>
    /// A central aisle along X with barred-off machinery bays on both sides holding boilers, glowing furnaces and
    /// coal; walls crowded with pipes, valves and gauges; leaks overhead, sparse bare bulbs, and every passage in the
    /// edges joined to the aisle.
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
                    // Coal heaped against the bars by the furnace bays, ready to shovel
                    if ((lz == aisle0 || lz == aisle1) && Hashing.Mod(gx, 12) == 4 && rng.Chance(0.6)) tile.Variant = Props.CoalPile;
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
                ArchPier toAisle = lz < 16 ? ArchPier.South : ArchPier.North;
                if (deep && inBay == 2) { tile.Variant = Props.Boiler; tile.Pier = toAisle; }
                else if (deep && inBay == 4) { tile.Variant = Props.Furnace; tile.Pier = toAisle; }
                else if (deep && inBay == 3 && rng.Chance(0.5)) tile.Variant = Props.CoalPile;
                else if (rng.Chance(0.02)) tile.SupplyBox = true;
            }
        }

        // Pipes, valves and gauges crowd the plaster walls of the bays
        for (int lz = 1; lz < MacroSize - 1; lz++)
        {
            for (int lx = 1; lx < MacroSize - 1; lx++)
            {
                ref Tile wall = ref b.At(lx, lz);
                if (wall.Kind != TileKind.Wall || wall.Pattern != WallPattern.Plaster || wall.Variant != 0) continue;
                ArchPier? face = null;
                foreach (ArchPier dir in new[] { ArchPier.East, ArchPier.West, ArchPier.North, ArchPier.South })
                {
                    var (x, z) = Step(lx, lz, dir);
                    if (b.At(x, z).Kind == TileKind.Floor && b.At(x, z).Variant == 0) { face = dir; break; }
                }
                if (face == null) continue;
                double r = rng.NextDouble();
                wall.Pier = face.Value;
                wall.Variant = r < 0.35 ? Decor.PipesV : r < 0.47 ? Decor.Valve : r < 0.57 ? Decor.PlasterGauges : r < 0.72 ? Decor.PipeCluster : (byte)0;
            }
        }

        // Join every passage in the edges to the aisle
        void Clear(int x, int z)
        {
            ref Tile t = ref b.At(x, z);
            if (x <= 0 || z <= 0) return;
            if (t.Kind is TileKind.Wall or TileKind.Bars) t.Kind = TileKind.Floor;
            // Whatever stood in the bay (a boiler, a furnace, coal, a box) makes way for the path
            if (t.Kind == TileKind.Floor) { t.Variant = 0; t.SupplyBox = false; t.Stack = 0; t.Sealed = false; }
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
        tile.Sealed = false;
    }
}
