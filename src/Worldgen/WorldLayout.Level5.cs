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
///   z % 16 == 0        back wall between two rows of rooms
///   z % 16 in 1..5     guest rooms (5 by 5, five of them between each pair of cross corridors)
///   z % 16 == 6        corridor wall with room doors, odd numbers
///   z % 16 in 7..9     corridor, 3 wide, with furniture along its walls
///   z % 16 == 10       corridor wall with room doors, even numbers
///   z % 16 in 11..15   guest rooms
/// </code>
/// A 2-wide cross corridor runs north-south every <see cref="CrossPeriod"/> blocks. Now and then a corridor does not
/// go on across one, but ends against a wall with a tall mirror at the end of it. The door numbers count up along a
/// corridor, 201, 203, 205, 207, and then, a few doors on, 201 again.
/// </summary>
public sealed partial class WorldLayout
{
    private const int HallPeriod = 16;
    /// <summary>The rows of a hall (z modulo <see cref="HallPeriod"/>): the doors of the first row of rooms, the corridor, the doors of the second.</summary>
    private const int DoorRowA = 6, CorridorRow0 = 7, CorridorMid = 8, CorridorRow1 = 9, DoorRowB = 10;
    /// <summary>Along a row of rooms: five blocks of room, then the wall to the next.</summary>
    private const int RoomPitch = 6;
    private const int CrossPeriod = 33;
    /// <summary>Lobby columns stand this far apart each way, a chandelier between every four.</summary>
    private const int LobbyBay = 8;

    private const ulong SaltL5Zone = 0x5E01;
    private const ulong SaltL5Boiler = 0x5E02;
    private const ulong SaltL5Room = 0x5E03;
    private const ulong SaltL5Light = 0x5E04;
    private const ulong SaltL5Beverly = 0x5E05;
    private const ulong SaltL5Prop = 0x5E06;
    private const ulong SaltL5Wood = 0x5E07;
    private const ulong SaltL5Lift = 0x5E08;
    private const ulong SaltL5End = 0x5E09;
    private const ulong SaltL5Dining = 0x5E0A;

    private enum HotelZone { Wing, Lobby, Boiler, Beverly, Dining }

    private enum HotelCell { Room, Corridor, Wall, Door }

    private HotelZone HotelZoneAt(int mx, int mz)
    {
        if (Noise(mx / 3.0, mz / 3.0, SaltL5Boiler) > 0.5) return HotelZone.Boiler;
        if (Noise(mx / 3.0, mz / 3.0, SaltL5Zone) > 0.48) return HotelZone.Lobby;
        // There is one Beverly Room in a stretch of hotel, and a dining hall every so often
        if (RegionPick(mx, mz, 6, SaltL5Beverly, 0.8)) return HotelZone.Beverly;
        if (RegionPick(mx, mz, 4, SaltL5Dining, 0.9)) return HotelZone.Dining;
        return HotelZone.Wing;
    }

    /// <summary>Whether a cell is the one picked (with a chance) in its region of <paramref name="size"/> cells each way.</summary>
    private bool RegionPick(int mx, int mz, int size, ulong salt, double chance)
    {
        int rx = Hashing.FloorDiv(mx, size), rz = Hashing.FloorDiv(mz, size);
        ulong h = Hashing.Hash(seed, rx, rz, salt);
        return Hashing.Unit(h) < chance && mx == rx * size + (int)((h >> 8) % (ulong)size) && mz == rz * size + (int)((h >> 24) % (ulong)size);
    }

    private HotelCell HotelCellAt(int gx, int gz)
    {
        int row = Hashing.Mod(gz, HallPeriod), xc = Hashing.Mod(gx, CrossPeriod);
        bool corridorRow = row is CorridorRow0 or CorridorMid or CorridorRow1;
        if (corridorRow && xc == 18 && CorridorEnds(gx, gz)) return HotelCell.Wall;
        if (corridorRow || xc == 16 || xc == 17) return HotelCell.Corridor;
        if (xc == 15 || xc == 18 || row == 0) return HotelCell.Wall;
        int inRoom = RoomU(gx) % RoomPitch;
        if (row == DoorRowA || row == DoorRowB) return inRoom == 2 ? HotelCell.Door : HotelCell.Wall;
        return inRoom == 5 ? HotelCell.Wall : HotelCell.Room;
    }

    /// <summary>
    /// Whether the corridor running east from a cross corridor is walled off there, ending (at its west end) in a
    /// tall mirror: about one stretch of corridor in eight.
    /// </summary>
    private bool CorridorEnds(int gx, int gz)
    {
        int span = Hashing.FloorDiv(gx, CrossPeriod);
        if (Hashing.Unit(Hashing.Hash(seed, span, Hashing.FloorDiv(gz, HallPeriod), SaltL5End)) >= 0.12) return false;
        // Not where the Beverly Room stands across the far end: the stretch would have no way out at all
        int mz = MacroOf(gz);
        for (int x = span * CrossPeriod + 18; x <= (span + 1) * CrossPeriod + 18; x += MacroSize / 2)
            if (HotelZoneAt(MacroOf(x), mz) == HotelZone.Beverly) return false;
        return HotelZoneAt(MacroOf((span + 1) * CrossPeriod + 18), mz) != HotelZone.Beverly;
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
        // wing's corridors cross it (staff-only doors into the boiler halls): the west-east corridors cross a wall
        // running north-south, the cross corridors one running west-east. (A wall that happens to run down the
        // length of a corridor is not crossed by it.)
        edge.Tall = true;
        edge.ExitSigns = a == HotelZone.Boiler || b == HotelZone.Boiler;
        for (int i = 1; i < MacroSize; i++) edge.Tiles[i] = EdgeTile.Wall;
        for (int i = 2; i < MacroSize - 2; i++)
        {
            int gx = west ? gx0 : gx0 + i, gz = west ? gz0 + i : gz0;
            bool crossing = west ? Hashing.Mod(gz, HallPeriod) is CorridorRow0 or CorridorMid or CorridorRow1 : Hashing.Mod(gx, CrossPeriod) is 16 or 17;
            if (crossing && HotelCellAt(gx, gz) == HotelCell.Corridor) edge.Tiles[i] = EdgeTile.Doorway;
        }
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
                bool rowA = row <= DoorRowA;
                int u = RoomU(gx);
                int roomX = Hashing.FloorDiv(gx - 19, CrossPeriod) * 8 + u / RoomPitch, roomZ = Hashing.FloorDiv(gz, HallPeriod) * 2 + (rowA ? 0 : 1);
                ulong h = Hashing.Hash(seed, roomX, roomZ, SaltL5Room);
                // Doors are numbered along the corridor, odd on its north side and even on its south
                int doorIndex = Hashing.FloorDiv(gx - 19, CrossPeriod) * 5 + u / RoomPitch;
                byte plaque = (byte)Hashing.Mod(2 * doorIndex + (rowA ? 0 : 1), 8);
                bool locked = Hashing.Unit(h) < 0.6;
                bool staffStairs = !locked && IsStaffStairs(h);
                ulong ph = Hashing.Hash(seed, gx, gz, SaltL5Prop);
                double r = Hashing.Unit(ph);

                switch (HotelCellAt(gx, gz))
                {
                    case HotelCell.Corridor:
                        bool crossCorridor = xc == 16 || xc == 17;
                        bool inCorridorRow = row is CorridorRow0 or CorridorMid or CorridorRow1;
                        if (walnut) tile.Floor = crossCorridor ? (inCorridorRow ? FloorKind.HotelWood : FloorKind.HotelRunnerNS)
                                                              : row == CorridorMid ? FloorKind.HotelRunnerWE : FloorKind.HotelWood;
                        // Dome lights every 4 blocks down the middle
                        if (crossCorridor ? xc == 16 && Hashing.Mod(gz, 4) == 0 && !inCorridorRow : row == CorridorMid && Hashing.Mod(gx, 4) == 0)
                            tile.Ceiling = HotelLightState(gx, gz);
                        else if (!crossCorridor && (row == CorridorRow0 || row == CorridorRow1)) FurnishCorridor(ref tile, row, u, r, ph);
                        break;

                    case HotelCell.Wall:
                        SetWall(ref tile, WallPattern.Hotel, BaseStyle.Plain);
                        // The end of a corridor that goes no further: a tall mirror, looking back down it
                        if (row == CorridorMid && xc == 18) { tile.Variant = Decor.Mirror; tile.Pier = ArchPier.East; }
                        // Corridor walls: sconces between doors, portraits and mirrors, the odd speaker or phone
                        if ((row == DoorRowA || row == DoorRowB) && xc != 15 && xc != 18)
                        {
                            tile.Pier = row == DoorRowA ? ArchPier.South : ArchPier.North;
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
                        tile.Variant = plaque; // room number plaque
                        tile.ExitSign = staffStairs;
                        // Now and then a locked door is not a guest room's at all: a cyan door marked POOL, onto the Poolrooms
                        if (locked && Hashing.Unit(Hashing.Hash(seed, roomX, roomZ, SaltL5Room + 37)) < 1 / 120.0) tile.Pattern = WallPattern.PoolDoor;
                        break;

                    case HotelCell.Room:
                        bool wood = Hashing.Unit(h << 20) < 0.3;
                        if (wood) tile.Floor = FloorKind.HotelWood;
                        if (locked) tile.Sealed = true;
                        else if (staffStairs) PlanStaffStairs(ref tile, u % RoomPitch, row, rowA);
                        else FurnishGuestRoom(ref tile, u % RoomPitch, row, rowA, h, wood);
                        // A cramped bathroom in the corner by the door, behind a partition (locked rooms too)
                        if (!staffStairs && Hashing.Unit(h << 52) < 0.7)
                        {
                            int x = u % RoomPitch, byDoor = rowA ? 5 : 11, inside = rowA ? 4 : 12, before = rowA ? 3 : 13;
                            if (x == 3 && (row == byDoor || row == inside)) SetWall(ref tile, WallPattern.Hotel, BaseStyle.Plain);
                            else if (x == 4 && row == byDoor) { tile.Variant = Props.Toilet; tile.Pier = rowA ? ArchPier.North : ArchPier.South; }
                            else if (x == 4 && (row == inside || row == before)) tile.Variant = 0; // the way into it
                        }
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
        if (row != (rowA ? 1 : 15) || x < 1 || x > 3) return;
        tile.Stair = (byte)x;
        tile.Pier = ArchPier.East;
    }

    /// <summary>Furniture along a corridor wall, under the sconces: console tables, bookcases, cabinets, sofas.</summary>
    private static void FurnishCorridor(ref Tile tile, int row, int u, double r, ulong ph)
    {
        // Against the north or south wall of the corridor, facing into it
        ArchPier facing = row == CorridorRow0 ? ArchPier.South : ArchPier.North;
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
        // Rooms are five deep: the furniture stands in the back three rows, leaving the way in by the door clear
        int back = rowA ? 1 : 15, middle = rowA ? 2 : 14, front = rowA ? 3 : 13;
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
                if (xc != 15 && xc != 18 || row != 2 && row != 13) continue;
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
                int cx = Hashing.Mod(gx, LobbyBay), cz = Hashing.Mod(gz, LobbyBay);
                if (cx == 3 && cz == 3)
                {
                    SetWall(ref tile, WallPattern.Marble, BaseStyle.Plain);
                    continue;
                }
                // A red carpet border around each column bay, a chandelier at each crossing
                if (cx == LobbyBay - 1 || cz == LobbyBay - 1) tile.Floor = FloorKind.HotelCarpet;
                if (cx == LobbyBay - 1 && cz == LobbyBay - 1) tile.Ceiling = CeilingKind.Chandelier;
            }
        }

        // Each bay between columns is furnished as something: a seating group, the front desk, a quiet corner
        int bx0 = Hashing.FloorDiv(mx * MacroSize, LobbyBay), bz0 = Hashing.FloorDiv(mz * MacroSize, LobbyBay);
        for (int bz = bz0; bz <= bz0 + MacroSize / LobbyBay; bz++)
        {
            for (int bx = bx0; bx <= bx0 + MacroSize / LobbyBay; bx++)
            {
                double r = Hashing.Unit(Hashing.Hash(seed, bx, bz, SaltL5Prop + 1));
                int x0 = bx * LobbyBay - mx * MacroSize, z0 = bz * LobbyBay - mz * MacroSize; // bay tiles 0..6 hold furniture, column at (3,3)
                void Put(int dx, int dz, byte prop, ArchPier facing)
                {
                    int x = x0 + dx, z = z0 + dz;
                    if (x < 1 || z < 1 || x >= MacroSize || z >= MacroSize) return;
                    ref Tile t = ref b.At(x, z);
                    if (t.Kind != TileKind.Floor || t.Variant != 0) return;
                    t.Variant = prop;
                    t.Pier = facing;
                }
                if (r < 0.3)
                {
                    // Sofa and armchairs round a coffee table
                    Put(0, 1, Props.Sofa, ArchPier.East);
                    Put(1, 0, Props.WingChair, ArchPier.South);
                    Put(1, 2, Props.WingChair, ArchPier.North);
                    Put(1, 1, Props.CoffeeTable, ArchPier.North);
                    Put(0, 2, Props.AshtrayStand, ArchPier.North);
                    Put(6, 6, Props.FloorLamp, ArchPier.North);
                }
                else if (r < 0.33)
                {
                    // The front desk, guest book and bell, a clock behind (a lobby has one, or near enough)
                    for (int k = 1; k <= 5; k++) Put(k, 6, Props.FrontDesk, ArchPier.North);
                    Put(6, 5, Props.GrandfatherClock, ArchPier.West);
                    Put(0, 5, Props.LuggageCart, ArchPier.North);
                }
                else if (r < 0.45)
                {
                    // Palms either side of the column, a bookcase against it
                    Put(2, 3, Props.Palm, ArchPier.North);
                    Put(4, 3, Props.Palm, ArchPier.North);
                    Put(3, 4, Props.HotelBookshelf, ArchPier.South);
                }
                else if (r < 0.5) Put(5, 2, Props.Turntable, ArchPier.North);
                else if (r < 0.56) Put(rng.Range(0, 6), rng.Range(0, 1), Props.LuggageCart, ArchPier.North);
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
        (int X, int Z)[] corners = { (4, 3), (MacroSize - 5, 3), (4, MacroSize - 4), (MacroSize - 5, MacroSize - 4) };
        int pianoCorner = rng.Range(0, 3);
        for (int k = 0; k < 4; k++)
        {
            ref Tile t = ref b.At(corners[k].X, corners[k].Z);
            if (t.Kind != TileKind.Floor) continue;
            t.Variant = k == pianoCorner ? Props.GrandPiano : Props.Palm;
            t.Pier = corners[k].Z < 16 ? ArchPier.South : ArchPier.North;
        }
        ref Tile music = ref b.At(corners[pianoCorner].X + (corners[pianoCorner].X < 16 ? 4 : -4), corners[pianoCorner].Z);
        if (music.Kind == TileKind.Floor) music.Variant = Props.Turntable;
    }

    // ================= The Beverly Room =================

    /// <summary>
    /// A grand ballroom set into a wing in place of the rooms between two of its corridors, which run on along its
    /// north and south walls; it opens straight onto both. (Every cell has the same rows of the hall grid, since a
    /// cell is two halls deep.)
    /// </summary>
    private const int BeverlyX0 = 3, BeverlyX1 = 28, BeverlyZ0 = DoorRowB, BeverlyZ1 = HallPeriod + DoorRowA;

    private void BuildBeverlyRoom(Builder b, int mz)
    {
        const int x0 = BeverlyX0, x1 = BeverlyX1, z0 = BeverlyZ0, z1 = BeverlyZ1;
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
                    int along = x == x0 || x == x1 ? z - z0 : x - x0;
                    int length = x == x0 || x == x1 ? z1 - z0 : x1 - x0;
                    if (!corner && along % 2 == 1 && along > 1 && along < length - 1)
                    {
                        tile.Kind = TileKind.Door;
                        tile.Variant = (byte)(along % 8);
                    }
                    else if (!corner && (x == x0 || x == x1) && along % 4 == 0) tile.Variant = Props.WallSconce;
                }
            }
        }

        // Two real doorways onto each of the corridors, each with a placard beside it
        foreach (int z in new[] { z0, z1 })
        {
            foreach (int x in new[] { x0 + 6, x1 - 6 })
            {
                b.At(x, z).Kind = TileKind.Doorway;
                b.At(x, z).Variant = 0;
                b.At(x + 1, z).Kind = TileKind.Wall;
                b.At(x + 1, z).Variant = Props.WallBeverly;
                b.At(x + 1, z).Pier = z == z0 ? ArchPier.North : ArchPier.South;
            }
        }

        // The corridors along it are kept clear
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
        foreach ((int x, int z) in new[] { (cx, cz - 1), (cx - 8, cz - 3), (cx + 8, cz - 3), (cx - 8, cz + 3), (cx + 8, cz + 3) })
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
        // A boiler hall beside another is one space with it: the aisles run straight on east and west, and to the
        // north and south a service passage at the same place in both joins them
        bool Boiler(int x, int z) => HotelZoneAt(x, z) == HotelZone.Boiler;
        if (!Boiler(mx - 1, mz))
            foreach (int i in Passages(west))
            {
                for (int x = 1; x <= 3; x++) Clear(x, i);
                ToAisle(3, i);
            }
        if (!Boiler(mx + 1, mz))
            foreach (int i in Passages(GetEdge(mx + 1, mz, west: true)))
            {
                for (int x = MacroSize - 4; x < MacroSize; x++) Clear(x, i);
                ToAisle(MacroSize - 4, i);
            }
        if (Boiler(mx, mz - 1)) { ToAisle(15, 1); ToAisle(16, 1); }
        else foreach (int i in Passages(north)) ToAisle(i, 1);
        if (Boiler(mx, mz + 1)) { ToAisle(15, MacroSize - 1); ToAisle(16, MacroSize - 1); }
        else foreach (int i in Passages(GetEdge(mx, mz + 1, west: false))) ToAisle(i, MacroSize - 1);
    }

    private static void ClearForWalking(ref Tile tile)
    {
        if (tile.Kind is TileKind.Wall or TileKind.Door or TileKind.Doorway) tile.Kind = TileKind.Floor;
        tile.Variant = 0;
        tile.Stack = 0;
        tile.Sealed = false;
    }
}
