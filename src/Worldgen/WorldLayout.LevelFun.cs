using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>What part of Level Fun a tile is in, kept in <see cref="Tile.Zone"/>.</summary>
public enum FunZone : byte
{
    None, Promenade, Hall, Lobby, Party, Mural, Themed, Play, Bounce, Arcade, Kitchen, Gifts, Service, Deck, Sea, Waiting,
    Vestibule, Stair, Clone,
}

/// <summary>
/// Level Fun: what hangs on a wall, kept on the floor tile in front of it (in <see cref="Tile.Roof"/>, which the level
/// has no other use for): the item in the low five bits, the way it faces (away from its wall) in the next two.
/// </summary>
public static class FunWallItems
{
    public const byte PosterTime4Fun = 1, PosterHappyBday = 2, PosterComeJoin = 3, PosterReversed = 4;
    public const byte Smiley1 = 5; // to 8
    public const byte SpeakerOn = 9, SpeakerOff = 10, StringLights = 11;
    /// <summary>Bunting: a pennant per letter of HAPPY BIRTHDAY, and blanks.</summary>
    public const byte BuntingFirst = 12; // h a p y b i r t d blank: 12-21
    public const byte DeckSign = 22, LifeRing = 23, DeckLamp = 24, ScreenL = 25, ScreenM = 26, ScreenR = 27;
    /// <summary>The ship's directory board in a lobby (layout version 5).</summary>
    public const byte Directory = 28;

    public static byte Pack(byte item, ArchPier facing) => (byte)(item | ((int)facing << 5));
    public static byte Item(byte roof) => (byte)(roof & 31);
    public static ArchPier Facing(byte roof) => (ArchPier)((roof >> 5) & 3);

    /// <summary>The bunting pennant for a letter (blank for anything else).</summary>
    public static byte Bunting(char c)
    {
        int i = "hapybirtd".IndexOf(char.ToLowerInvariant(c));
        return (byte)(BuntingFirst + (i < 0 ? 9 : i));
    }

    /// <summary>How high above the floor an item hangs: posters and smileys at eye height, lamps a little higher, the rest under the ceiling (0).</summary>
    public static int Rel(byte item) => item switch
    {
        <= Smiley1 + 3 => 2,
        LifeRing or ScreenL or ScreenM or ScreenR or Directory => 2,
        DeckSign or DeckLamp => 3,
        _ => 0,
    };
}

/// <summary>One room of Level Fun: what it is, where its floor is, and who is at its party.</summary>
public sealed class FunRoom
{
    public FunZone Kind;
    /// <summary>The room's floor, in block coordinates (inclusive).</summary>
    public int X0, Z0, X1, Z1;
    public ulong Key;
    /// <summary>How many Partygoers stand round its head table (0: the party is over).</summary>
    public int Guests;
    public byte Palette;
    public WallPattern Wall = WallPattern.FunPaint;
    /// <summary>The head table's cake, and where the guests stand.</summary>
    public (int X, int Z) Head;
    public readonly List<(int X, int Z)> Spots = new();
    /// <summary>The floor tiles just inside its doors.</summary>
    public readonly List<(int X, int Z)> Doors = new();
    /// <summary>A threshold of the level's own in it (the waiting room's door, the FUN doors, the stairs), none for most.</summary>
    public bool Threshold;

    public bool Contains(int x, int z) => x >= X0 && x <= X1 && z >= Z0 && z <= Z1;
}

/// <summary>
/// Level Fun =): endless children's party rooms on a ship that cannot be this big. Kept as level 15
/// (<see cref="FunLevel"/>) and shown as "Fun". Like the Poolrooms it is not a ring: it lies far out to the
/// north-east, a region you can only noclip into, and its rim is the ship's riveted hull.
///
/// The level is planned in blocks of <see cref="FunBlock"/> square. Every 32 blocks a corridor runs each way:
/// promenades (three wide, cream walls over a band of party colours) on the block lines, halls (two wide) between.
/// They jog sideways every twelve blocks, so no corridor can be seen down for long, and run straight where they cross.
/// Where two promenades cross there is an elevator lobby (red carpet, brass doors that never open): it is where people
/// arrive. Between the corridors each block has three by three squares, each one suite: party rooms (most), the mural
/// room, a themed room, a play room with a ball pit, a bounce hall, an arcade, a kitchen, crew corridors, an open
/// deck over black water, now and then a waiting room, the FUN doors or service stairs into the ceiling. One block
/// in eight has a hall that runs straight, lined with the same party room over and over.
///
/// On a floor tile: <see cref="Tile.Height"/> is the air above the floor (the ceiling is one higher),
/// <see cref="Tile.Variant"/> the prop (<see cref="Props.FunTable"/>…, Stack its kind, Pier its facing),
/// <see cref="Tile.Pipe"/> what lies on a table (<see cref="Pipes.FunPlates"/>…), <see cref="Tile.Overhead"/> what
/// hangs from the ceiling, <see cref="Tile.Roof"/> what hangs on the wall beside it (<see cref="FunWallItems"/>),
/// <see cref="Tile.Detail"/> the room's palette (paint, cloth, balloons), <see cref="Tile.Zone"/> a
/// <see cref="FunZone"/>, <see cref="Tile.Depth"/> how far the floor lies below the level's (ball pits, the sea), and
/// for a bounce house's floor the height of the hall's ceiling over it. On a wall: Detail its paint, Pier the face
/// that looks into the room, Height (if not 0) a low wall's top with the room's air over it up to Depth.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x1500-0x15BF are this level's.</summary>
    private const ulong SaltFunShape = 0x1501, SaltFunBlock = 0x1502, SaltFunLine = 0x1503, SaltFunSuite = 0x1504,
        SaltFunGuests = 0x1505, SaltFunClone = 0x1506, SaltFunSpecial = 0x1507, SaltFunLight = 0x1508, SaltFunRoom = 0x1509,
        SaltFunLobby = 0x150A;
    /// <summary>Salts of the ways in that Level Fun adds to other levels (each its own, so nothing else there shifts).</summary>
    private const ulong SaltFunL0 = 0x1520, SaltFunL1 = 0x1521, SaltFunL5 = 0x1522, SaltFunL11 = 0x1523;

    /// <summary>Size of the blocks the level is planned in.</summary>
    public const int FunBlock = 96;

    /// <summary>The air over the floors: corridors, party rooms, the play rooms, the bounce halls, an open deck.</summary>
    private const int FunCorridorHeight = 3, FunRoomHeight = 4, FunPlayHeight = 5, FunBounceHeight = 8, FunDeckHeight = 14;

    /// <summary>
    /// How far an elevator lobby's floor reaches west and east of its crossing: 4 (nine wide) before layout version 9; from
    /// 9, 5 (eleven wide), so the two-wide elevator doors on its north and south walls stand between wall on both sides
    /// rather than right beside the promenade's opening. North to south it stays nine deep (4 either way), so the walls
    /// behind the doors still back onto solid ship, not a promenade's jog.
    /// </summary>
    private int FunLobbyHalfX => Version >= 9 ? 5 : 4;

    /// <summary>How far below the deck the sea's bottom lies, and its surface.</summary>
    public const int FunSeaDepth = 10, FunSeaSurface = -6;

    // ================= Where it is =================

    /// <summary>The region's centre, in macro cells: far out to the north-east, a quarter further out than the city.</summary>
    private int FunCentreX => spawnMacroX + DiagonalReach;
    private int FunCentreZ => spawnMacroZ - DiagonalReach;

    /// <summary>The region's radius in macro cells: still endless to anyone in it.</summary>
    private int FunRadius => Math.Max(60, spawnMacroX / 40);

    /// <summary>The block the level's plans count from.</summary>
    public int FunOriginX => FunCentreX * MacroSize;
    public int FunOriginZ => FunCentreZ * MacroSize;

    private bool InFun(double mx, double mz) => InRoundRegion(mx, mz, FunCentreX, FunCentreZ, FunRadius, SaltFunShape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) FunArrivalCell(ulong h) => RoundArrivalCell(h, FunCentreX, FunCentreZ, FunRadius);

    /// <summary>Arriving: in an elevator lobby, the one calm place, never among the props.</summary>
    private static bool IsFunArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone == (byte)FunZone.Lobby;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double FunArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The plans are laid over the edges, as in the Poolrooms (the rim is solid, see <see cref="LevelBoundaryEdge"/>).</summary>
    private Edge FunEdge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.FunWall };

    private void BuildLevelFun(Builder b, int mx, int mz)
    {
        // The ship's hull, all the way round, wherever the level meets another
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != FunLevel) { rim = true; break; }

        if (rim)
        {
            for (int i = 0; i < b.Tiles.Length; i++) b.Tiles[i] = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.FunWall, Tall = true };
            return;
        }
        // The plan blocks count from a cell corner and are three cells a side, so the whole cell lies in one of them
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        var (bi, bj) = FunBlockOf(x0, z0);
        Tile[] plan = FunPlan(bi, bj).Tiles;
        int u0 = x0 - FunOriginX - bi * FunBlock, v0 = z0 - FunOriginZ - bj * FunBlock;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
                b.At(lx, lz) = plan[(v0 + lz) * FunBlock + u0 + lx];
        // Level 188's confetti window, the one in the world (188's salted hook: nothing else moves)
        MarkL188FunWindow(b, mx, mz);
    }

    /// <summary>Which of the level's props (<see cref="Props.FunFirst"/> to <see cref="Props.FunLast"/>) are walked through rather than around.</summary>
    private static bool FunWalkThrough(ushort variant) => variant is Props.FunBalloonsFloor or Props.FunBalloonTied or Props.FunArchL
        or Props.FunArchR or Props.FunConfetti or Props.FunInflatableArch or Props.FunCord or Props.FunCBalloon or Props.FunPosterTrap
        or Props.FunSmiley;

    // ================= What it is like =================

    private float FunTemperature(int x, int y, int z, int floorY)
    {
        Tile t = TileAt(x, z);
        return (FunZone)t.Zone switch
        {
            FunZone.Bounce => 13f, // the blowers
            FunZone.Deck or FunZone.Sea => 11f, // night wind off the water
            _ => LevelTemperatures[FunLevel], // the air conditioning, turned up too high as at every party venue
        };
    }

    /// <summary>Reality stability here (see <see cref="StabilityAt"/>; <paramref name="drift"/> is gentle noise in [-1, 1]).</summary>
    private float FunStability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        float s = (FunZone)t.Zone switch
        {
            FunZone.Promenade or FunZone.Hall or FunZone.Lobby => 0.75f,
            FunZone.Waiting => 0.9f, // oddly calm
            FunZone.Service or FunZone.Kitchen => 0.5f,
            FunZone.Deck or FunZone.Sea => 0.6f,
            _ => 0.55f, // the party rooms
        };
        return s + 0.04f * drift;
    }

    // ================= Plans =================

    /// <summary>Which plan block a block position lies in.</summary>
    public (int Bi, int Bj) FunBlockOf(int gx, int gz) =>
        (Hashing.FloorDiv(gx - FunOriginX, FunBlock), Hashing.FloorDiv(gz - FunOriginZ, FunBlock));

    /// <summary>A planned block: its tiles and its rooms.</summary>
    public sealed class FunBlockPlan
    {
        public Tile[] Tiles;
        public FunRoom[] Rooms;
    }

    private PlanCache<FunBlockPlan> funPlans;

    public FunBlockPlan FunPlan(int bi, int bj) => funPlans.Get(bi, bj);

    /// <summary>
    /// The rooms of each plan block, kept apart from the tiles (a block's 9k tiles are only kept for the last few blocks, but a
    /// search for the rooms near a position looks at dozens, and the rooms are all it wants of each).
    /// </summary>
    private PlanCache<FunRoom[]> funRooms;

    /// <summary>
    /// The level's rooms with their middles within <paramref name="radius"/> blocks of a position, block by block (a room lies
    /// inside its plan block, so a block further than the radius from the position is not even planned).
    /// </summary>
    public IEnumerable<FunRoom> FunRoomsNear(int x, int z, int radius)
    {
        var (bi, bj) = FunBlockOf(x, z);
        int reach = radius / FunBlock + 1;
        for (int dj = -reach; dj <= reach; dj++)
            for (int di = -reach; di <= reach; di++)
            {
                int ox = FunOriginX + (bi + di) * FunBlock, oz = FunOriginZ + (bj + dj) * FunBlock;
                int gapX = Math.Max(Math.Max(ox - x, x - (ox + FunBlock - 1)), 0), gapZ = Math.Max(Math.Max(oz - z, z - (oz + FunBlock - 1)), 0);
                if ((long)gapX * gapX + (long)gapZ * gapZ > (long)radius * radius) continue;
                if (LevelAt(MacroOf(ox + FunBlock / 2), MacroOf(oz + FunBlock / 2)) != FunLevel) continue;
                foreach (FunRoom room in funRooms.Get(bi + di, bj + dj))
                {
                    int cx = (room.X0 + room.X1) / 2 - x, cz = (room.Z0 + room.Z1) / 2 - z;
                    if (cx * cx + cz * cz <= radius * radius) yield return room;
                }
            }
    }

    /// <summary>The level's room a block position lies in, or null.</summary>
    public FunRoom FunRoomAt(int x, int z)
    {
        var (bi, bj) = FunBlockOf(x, z);
        foreach (FunRoom room in FunPlan(bi, bj).Rooms)
            if (room.Contains(x, z)) return room;
        return null;
    }

    // ================= Corridors =================

    /// <summary>
    /// How far a corridor's middle lies off its line, at a point along it: promenades (every third line, on the block
    /// lines) three either way, halls two, changing side every twelve blocks; straight across where lines meet,
    /// and down the whole of a block's cloned hall.
    /// </summary>
    private int FunJog(int axis, int line, int along)
    {
        bool promenade = Hashing.Mod(line, 3) == 0;
        int toCross = Hashing.Mod(along, 32);
        toCross = Math.Min(toCross, 32 - toCross);
        if (toCross <= (promenade ? 7 : 4)) return 0;
        if (!promenade && axis == 1 && Hashing.Mod(line, 3) == 1
            && IsFunCloneBlock(Hashing.FloorDiv(line, 3), Hashing.FloorDiv(along, FunBlock))) return 0;
        int phase = funPhases.Get(axis, line);
        int segment = Hashing.FloorDiv(along + phase, 12);
        int sign = (segment & 1) == 0 ? 1 : -1;
        int amplitude = promenade ? 3 : 2; // never overlapping the straight band where lines cross, so no look runs on past a jog
        return sign * amplitude;
    }

    /// <summary>Where along a line its jogs start (a function of the line alone, asked for by every tile beside it, so remembered).</summary>
    private LatticeMemo<int> funPhases;

    private int FunPhaseOf(int axis, int line) => (int)(Hashing.Hash(seed, axis * 7919 + line, 0, SaltFunLine) % 12);

    /// <summary>Whether a tile at <paramref name="off"/> across a line lies in its corridor at a point along it (the jogs are joined up).</summary>
    private bool InFunBand(int axis, int line, int off, int along)
    {
        bool promenade = Hashing.Mod(line, 3) == 0;
        if (off < -4 || off > 4) return false;
        int c = FunJog(axis, line, along), before = FunJog(axis, line, along - 1);
        int lo = c - 1, hi = promenade ? c + 1 : c;
        if (off >= lo && off <= hi) return true;
        if (c == before) return false;
        int lo2 = before - 1, hi2 = promenade ? before + 1 : before;
        return off >= Math.Min(lo, lo2) && off <= Math.Max(hi, hi2);
    }

    /// <summary>What corridor a block position lies in (none, a promenade, a hall or a lobby), and whether a light hangs over it.</summary>
    private (FunZone Zone, bool Light, int Line) FunCorridorAt(int gx, int gz)
    {
        int ux = gx - FunOriginX, uz = gz - FunOriginZ;
        int lineX = (int)Math.Round(ux / 32.0), lineZ = (int)Math.Round(uz / 32.0);
        int offX = ux - lineX * 32, offZ = uz - lineZ * 32;
        // (Layout version 9 on: a lobby is eleven wide west to east, not nine, so its elevator doors have wall either side
        // of them, not the promenade's opening right beside them)
        if (Hashing.Mod(lineX, 3) == 0 && Hashing.Mod(lineZ, 3) == 0 && Math.Abs(offX) <= FunLobbyHalfX && Math.Abs(offZ) <= 4)
            return (FunZone.Lobby, Math.Abs(offX) == 2 && Math.Abs(offZ) == 2, lineX + lineZ);
        bool ns = InFunBand(1, lineX, offX, uz), we = InFunBand(0, lineZ, offZ, ux);
        if (!ns && !we) return (FunZone.None, false, 0);
        bool nsProm = ns && Hashing.Mod(lineX, 3) == 0, weProm = we && Hashing.Mod(lineZ, 3) == 0;
        FunZone zone = nsProm || weProm ? FunZone.Promenade : FunZone.Hall;
        bool light = ns && offX == FunJog(1, lineX, uz) && Hashing.Mod(uz, 4) == 2
            || we && offZ == FunJog(0, lineZ, ux) && Hashing.Mod(ux, 4) == 2;
        return (zone, light, ns ? lineX : lineZ);
    }

    /// <summary>One block in eight has a hall running straight down it, lined with the same party room again and again.</summary>
    private bool IsFunCloneBlock(int bi, int bj) => Hashing.Unit(Hashing.Hash(seed, bi, bj, SaltFunClone)) < 0.125;

    // ================= Block plans =================

    private sealed class FunPlanner
    {
        public const int N = FunBlock;
        public readonly Tile[] Tiles = new Tile[N * N];
        /// <summary>0: wall, -1: a corridor, k: room k-1.</summary>
        public readonly short[] Owner = new short[N * N];
        /// <summary>Floor that must stay clear: in front of doors.</summary>
        public readonly bool[] Reserved = new bool[N * N];
        public readonly List<FunRoom> Rooms = new();
        public int X0, Z0;
        public Rng Rng;

        public static bool In(int u, int v) => u >= 0 && v >= 0 && u < N && v < N;
        public ref Tile At(int u, int v) => ref Tiles[v * N + u];
        public short OwnerAt(int u, int v) => In(u, v) ? Owner[v * N + u] : (short)0;

        public bool Free(int u, int v) => In(u, v) && !Reserved[v * N + u] && At(u, v).Kind == TileKind.Floor && At(u, v).Variant == 0
            && At(u, v).Stair == 0 && At(u, v).Depth == 0;
    }

    /// <summary>A room's frame: its floor in block coordinates, which way is "along" (the long way), and its index.</summary>
    private readonly struct FunFrame
    {
        public readonly int U0, V0, U1, V1, Index;
        public readonly bool AlongX;
        public FunFrame(int u0, int v0, int u1, int v1, int index)
        {
            U0 = u0; V0 = v0; U1 = u1; V1 = v1; Index = index;
            AlongX = u1 - u0 >= v1 - v0;
        }
        public int Long => AlongX ? U1 - U0 + 1 : V1 - V0 + 1;
        public int Short => AlongX ? V1 - V0 + 1 : U1 - U0 + 1;
        public (int U, int V) P(int a, int s) => AlongX ? (U0 + a, V0 + s) : (U0 + s, V0 + a);
        /// <summary>The way "along" (a growing), and the way "across" (s growing).</summary>
        public ArchPier AlongDir => AlongX ? ArchPier.East : ArchPier.South;
        public ArchPier AcrossDir => AlongX ? ArchPier.South : ArchPier.East;
    }

    private static readonly int[] FunSquareLo = { 6, 36, 68 }, FunSquareHi = { 27, 59, 90 };

    private FunBlockPlan PlanFunBlock(int bi, int bj)
    {
        var p = new FunPlanner
        {
            X0 = FunOriginX + bi * FunBlock,
            Z0 = FunOriginZ + bj * FunBlock,
            Rng = new Rng(Hashing.Hash(seed, bi, bj, SaltFunBlock)),
        };
        for (int i = 0; i < p.Tiles.Length; i++) p.Tiles[i] = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.FunSolid };

        // The corridors and lobbies, laid out from world coordinates so they run on from block to block
        for (int v = 0; v < FunPlanner.N; v++)
            for (int u = 0; u < FunPlanner.N; u++)
            {
                var (zone, light, line) = FunCorridorAt(p.X0 + u, p.Z0 + v);
                if (zone == FunZone.None) continue;
                p.At(u, v) = CorridorTile(zone, light, line, p.X0 + u, p.Z0 + v);
                p.Owner[v * FunPlanner.N + u] = -1;
            }

        // What each square holds: the odd special one first, then the rest by weight
        ulong special = Hashing.Hash(seed, bi, bj, SaltFunSpecial);
        var kinds = new FunZone[9];
        for (int i = 0; i < 9; i++) kinds[i] = PickFunSuite(ref p.Rng);
        bool clone = IsFunCloneBlock(bi, bj);
        var specials = new List<FunZone>();
        if (Hashing.Unit(special) < 0.25) specials.Add(FunZone.Waiting);
        if (Hashing.Unit(special << 12) < 1 / 9.0) specials.Add(FunZone.Vestibule);
        if (Hashing.Unit(special << 24) < 1 / 9.0) specials.Add(FunZone.Stair);
        int slot = (int)(Hashing.Mix(special) % 9);
        foreach (FunZone s in specials)
        {
            // Never in the cloned column
            while (clone && slot % 3 == 1) slot = (slot + 1) % 9;
            kinds[slot] = s;
            slot = (slot + 4) % 9;
        }

        for (int sj = 0; sj < 3; sj++)
            for (int si = 0; si < 3; si++)
            {
                int u0 = FunSquareLo[si] + 1, u1 = FunSquareHi[si] - 1, v0 = FunSquareLo[sj] + 1, v1 = FunSquareHi[sj] - 1;
                var rng = new Rng(Hashing.Hash(seed, bi * 3 + si, bj * 3 + sj, SaltFunSuite));
                if (clone && si == 1) PlanFunCloneSquare(p, u0, v0, u1, v1, bi, bj);
                else PlanFunSquare(p, kinds[sj * 3 + si], u0, v0, u1, v1, ref rng);
            }

        FinishFunWalls(p);
        PlaceFunLobbyFittings(p);
        PlaceReversedPoster(p, bi, bj);
        return new FunBlockPlan { Tiles = p.Tiles, Rooms = p.Rooms.ToArray() };
    }

    private Tile CorridorTile(FunZone zone, bool light, int line, int gx, int gz)
    {
        var t = new Tile
        {
            Kind = TileKind.Floor,
            Zone = (byte)zone,
            Height = (byte)(zone == FunZone.Lobby ? FunRoomHeight : FunCorridorHeight),
            Floor = zone == FunZone.Lobby ? FloorKind.FunLobbyCarpet : (FloorKind)((int)FloorKind.FunFloor + Hashing.Mod(line, 4)),
            Ceiling = CeilingKind.Tile,
        };
        if (light)
        {
            double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltFunLight));
            t.Ceiling = r < 0.08 ? CeilingKind.LightFlicker : r < 0.14 ? CeilingKind.LightOff : CeilingKind.LightOn;
        }
        return t;
    }

    private static FunZone PickFunSuite(ref Rng rng)
    {
        double r = rng.NextDouble();
        return r < 0.42 ? FunZone.Party : r < 0.52 ? FunZone.Mural : r < 0.61 ? FunZone.Themed : r < 0.70 ? FunZone.Play
            : r < 0.76 ? FunZone.Bounce : r < 0.82 ? FunZone.Arcade : r < 0.87 ? FunZone.Kitchen : r < 0.96 ? FunZone.Service
            : FunZone.Deck;
    }

    // ================= Rooms =================

    /// <summary>A room: its floor laid, its walls round it (their paint is settled at the end), its record kept.</summary>
    private FunRoom AddFunRoom(FunPlanner p, FunZone kind, int u0, int v0, int u1, int v1, int height, FloorKind floor, byte palette,
        WallPattern wall = WallPattern.FunPaint)
    {
        int index = p.Rooms.Count;
        var room = new FunRoom
        {
            Kind = kind, X0 = p.X0 + u0, Z0 = p.Z0 + v0, X1 = p.X0 + u1, Z1 = p.Z0 + v1, Palette = palette, Wall = wall,
            Key = Hashing.Hash(seed, p.X0 + u0, p.Z0 + v0, SaltFunRoom),
        };
        p.Rooms.Add(room);
        for (int v = v0; v <= v1; v++)
            for (int u = u0; u <= u1; u++)
            {
                p.At(u, v) = new Tile { Kind = TileKind.Floor, Floor = floor, Height = (byte)height, Zone = (byte)kind, Detail = palette, Ceiling = CeilingKind.Tile };
                p.Owner[v * FunPlanner.N + u] = (short)(index + 1);
            }
        return room;
    }

    /// <summary>A grid of lights, one every <paramref name="pitch"/> blocks; <paramref name="on"/> of them working, the rest dead or failing.</summary>
    private static void FunLights(FunPlanner p, FunFrame f, int pitch, double on, double flicker, ref Rng rng)
    {
        int offA = Math.Max(1, (f.Long % pitch) / 2 + pitch / 2 - 1), offS = Math.Max(1, (f.Short % pitch) / 2 + pitch / 2 - 1);
        for (int a = offA % pitch; a < f.Long; a += pitch)
            for (int s = offS % pitch; s < f.Short; s += pitch)
            {
                var (u, v) = f.P(a, s);
                double r = rng.NextDouble();
                p.At(u, v).Ceiling = r < on ? CeilingKind.LightOn : r < on + flicker ? CeilingKind.LightFlicker : CeilingKind.LightOff;
            }
    }

    private static byte FunPalette(ref Rng rng, int paint = -1) =>
        (byte)((paint >= 0 ? paint : rng.Range(0, 5)) | rng.Range(0, 4) << 3 | rng.Range(0, 1) << 6);

    /// <summary>
    /// Opens a door from a room through the walls to the nearest corridor on one side, at the place along that side
    /// nearest its middle where a corridor can be reached within eight blocks. False if there is none.
    /// </summary>
    private static bool OpenFunDoor(FunPlanner p, FunRoom room, FunFrame f, ArchPier side, int width)
    {
        var (du, dv) = FacingStep(side);
        bool alongU = du == 0; // the side runs along u
        int lo = alongU ? f.U0 : f.V0, hi = (alongU ? f.U1 : f.V1) - (width - 1), mid = (lo + hi) / 2;
        for (int k = 0; k <= hi - lo; k++)
        {
            int pos = mid + (k % 2 == 0 ? k / 2 : -(k + 1) / 2);
            if (pos < lo || pos > hi) continue;
            int reach = -1;
            for (int lane = 0; lane < width; lane++)
            {
                // Start on the room's floor at the edge, then step out over walls until a corridor's floor
                int u = alongU ? pos + lane : side == ArchPier.West ? f.U0 : f.U1;
                int v = alongU ? (side == ArchPier.North ? f.V0 : f.V1) : pos + lane;
                int steps = 0, found = -1;
                for (int n = 1; n <= 9; n++)
                {
                    int x = u + du * n, z = v + dv * n;
                    if (!FunPlanner.In(x, z)) break;
                    short owner = p.OwnerAt(x, z);
                    if (owner == -1 && p.At(x, z).Kind == TileKind.Floor) { found = n; break; }
                    if (owner != 0 || p.At(x, z).Kind != TileKind.Wall) break;
                    steps = n;
                }
                if (found < 0 || steps != found - 1) { reach = -1; break; }
                reach = Math.Max(reach, found);
            }
            if (reach < 0) continue;
            for (int lane = 0; lane < width; lane++)
            {
                int u = alongU ? pos + lane : side == ArchPier.West ? f.U0 : f.U1;
                int v = alongU ? (side == ArchPier.North ? f.V0 : f.V1) : pos + lane;
                for (int n = 1; n < reach; n++)
                {
                    int x = u + du * n, z = v + dv * n;
                    if (p.OwnerAt(x, z) == -1) break;
                    ref Tile t = ref p.At(x, z);
                    t = new Tile
                    {
                        Kind = TileKind.Doorway, Floor = FloorKind.FunFloor, Zone = (byte)FunZone.Hall,
                        Pattern = n == 1 ? room.Wall : WallPattern.FunPromenade, Detail = room.Palette,
                        Pier = side,
                    };
                    p.Owner[z * FunPlanner.N + x] = -1;
                }
                // Keep the way in clear
                for (int n = 0; n <= 1; n++)
                {
                    int x = u - du * n, z = v - dv * n;
                    if (FunPlanner.In(x, z)) p.Reserved[z * FunPlanner.N + x] = true;
                }
                if (lane == 0) room.Doors.Add((p.X0 + u, p.Z0 + v));
            }
            return true;
        }
        return false;
    }

    /// <summary>Opens a room onto the corridors: on one or two of the sides it may, the others tried in turn if those fail.</summary>
    private static void OpenFunRoom(FunPlanner p, FunRoom room, FunFrame f, ArchPier[] sides, int doors, int width, ref Rng rng)
    {
        var order = new List<ArchPier>(sides);
        for (int i = order.Count - 1; i > 0; i--)
        {
            int j = rng.Range(0, i);
            (order[i], order[j]) = (order[j], order[i]);
        }
        int opened = 0;
        foreach (ArchPier side in order)
        {
            if (opened >= doors) break;
            if (OpenFunDoor(p, room, f, side, width)) opened++;
        }
    }

    private static readonly ArchPier[] AllSides = { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West };

    /// <summary>One square of a block: one suite of rooms.</summary>
    private void PlanFunSquare(FunPlanner p, FunZone kind, int u0, int v0, int u1, int v1, ref Rng rng)
    {
        switch (kind)
        {
            case FunZone.Party:
            case FunZone.Waiting:
            case FunZone.Vestibule:
            case FunZone.Stair:
                PlanFunPartySuite(p, kind, u0, v0, u1, v1, ref rng);
                break;
            case FunZone.Service:
                PlanFunService(p, u0, v0, u1, v1, ref rng);
                break;
            case FunZone.Deck:
                PlanFunDeck(p, u0, v0, u1, v1, ref rng);
                break;
            default:
            {
                FunZone k = kind;
                int height = k == FunZone.Play ? FunPlayHeight : k == FunZone.Bounce ? FunBounceHeight : FunRoomHeight;
                FloorKind floor = k switch
                {
                    FunZone.Mural => FloorKind.FunRaceCarpet,
                    FunZone.Play => FloorKind.FunCheckerA,
                    FunZone.Bounce or FunZone.Arcade => FloorKind.FunRetroCarpet,
                    FunZone.Kitchen => FloorKind.FunVinylB,
                    _ => rng.Chance(0.5) ? FloorKind.FunVinylC : FloorKind.FunRaceCarpet,
                };
                WallPattern wall = k == FunZone.Mural ? WallPattern.FunMural : k == FunZone.Kitchen ? WallPattern.FunSteel : WallPattern.FunPaint;
                FunRoom room = AddFunRoom(p, k, u0, v0, u1, v1, height, floor, FunPalette(ref rng, k == FunZone.Mural ? 4 : -1), wall);
                var f = new FunFrame(u0, v0, u1, v1, p.Rooms.Count - 1);
                OpenFunRoom(p, room, f, AllSides, rng.Range(1, 2), k is FunZone.Bounce or FunZone.Play ? 2 : 1, ref rng);
                switch (k)
                {
                    case FunZone.Mural: FurnishFunMural(p, room, f, ref rng); break;
                    case FunZone.Themed: FurnishFunThemed(p, room, f, ref rng); break;
                    case FunZone.Play: FurnishFunPlay(p, room, f, ref rng); break;
                    case FunZone.Bounce: FurnishFunBounce(p, room, f, ref rng); break;
                    case FunZone.Arcade: FurnishFunArcade(p, room, f, ref rng); break;
                    case FunZone.Kitchen: FurnishFunKitchen(p, room, f, ref rng); break;
                }
                break;
            }
        }
    }

    /// <summary>
    /// A square of party rooms: one big room, two, or four, between partitions two blocks thick (so each room keeps
    /// its own paint). Each opens onto the corridors on its outer sides. A special square makes one of them a waiting
    /// room, the vestibule of the FUN doors or the service stairs; now and then one is a cloakroom full of gifts.
    /// </summary>
    private void PlanFunPartySuite(FunPlanner p, FunZone special, int u0, int v0, int u1, int v1, ref Rng rng)
    {
        double r = rng.NextDouble();
        int splitsU = 1, splitsV = 1;
        if (r < 0.5 || special != FunZone.Party) { splitsU = 2; splitsV = 2; }
        else if (r < 0.85) { if (u1 - u0 >= v1 - v0) splitsU = 2; else splitsV = 2; }
        int midU = (u0 + u1) / 2, midV = (v0 + v1) / 2;
        var boxes = new List<(int U0, int V0, int U1, int V1, ArchPier[] Outer)>();
        for (int j = 0; j < splitsV; j++)
            for (int i = 0; i < splitsU; i++)
            {
                int a0 = splitsU == 1 ? u0 : i == 0 ? u0 : midU + 1, a1 = splitsU == 1 ? u1 : i == 0 ? midU - 2 : u1;
                int b0 = splitsV == 1 ? v0 : j == 0 ? v0 : midV + 1, b1 = splitsV == 1 ? v1 : j == 0 ? midV - 2 : v1;
                var outer = new List<ArchPier>();
                if (j == 0) outer.Add(ArchPier.North);
                if (j == splitsV - 1) outer.Add(ArchPier.South);
                if (i == 0) outer.Add(ArchPier.West);
                if (i == splitsU - 1) outer.Add(ArchPier.East);
                boxes.Add((a0, b0, a1, b1, outer.ToArray()));
            }
        int specialAt = special != FunZone.Party ? rng.Range(0, boxes.Count - 1) : -1;
        for (int k = 0; k < boxes.Count; k++)
        {
            var (a0, b0, a1, b1, outer) = boxes[k];
            FunZone kind = k == specialAt ? special : boxes.Count > 1 && rng.Chance(0.12) ? FunZone.Gifts : FunZone.Party;
            byte palette = FunPalette(ref rng);
            FloorKind floor = kind switch
            {
                FunZone.Waiting => FloorKind.OfficeCarpet,
                FunZone.Stair => FloorKind.Concrete,
                _ => rng.NextDouble() switch { < 0.45 => (FloorKind)((int)FloorKind.FunFloor + rng.Range(0, 3)), < 0.75 => FloorKind.FunRaceCarpet, _ => FloorKind.OfficeCarpet },
            };
            // (The stairwell is a room's height: under a corridor's ceiling nobody could climb onto the second step, where
            // the way up into Level 1 begins)
            int height = kind == FunZone.Waiting ? FunCorridorHeight : FunRoomHeight;
            FunRoom room = AddFunRoom(p, kind, a0, b0, a1, b1, height, floor, palette);
            var f = new FunFrame(a0, b0, a1, b1, p.Rooms.Count - 1);
            OpenFunRoom(p, room, f, outer, kind == FunZone.Party && rng.Chance(0.3) ? 2 : 1, 1, ref rng);
            switch (kind)
            {
                case FunZone.Party: FurnishFunParty(p, room, f, ref rng, false); break;
                case FunZone.Gifts: FurnishFunGifts(p, room, f, ref rng); break;
                case FunZone.Waiting: FurnishFunWaiting(p, room, f, outer, ref rng); break;
                case FunZone.Vestibule: FurnishFunVestibule(p, room, f, outer, ref rng); break;
                case FunZone.Stair: FurnishFunStair(p, room, f, ref rng); break;
            }
        }
    }

    /// <summary>The cloned column of a block: three of the same party room, one above the other, all the way down the straight hall.</summary>
    private void PlanFunCloneSquare(FunPlanner p, int u0, int v0, int u1, int v1, int bi, int bj)
    {
        // The same seed for every copy: the same paint, the same tables, the same balloon in the same corner
        ulong copy = Hashing.Hash(seed, bi, bj, SaltFunClone + 1);
        int depth = 6, w = 8;
        for (int k = 0; k < 3; k++)
        {
            int b0 = v0 + k * (depth + 1), b1 = b0 + depth - 1;
            if (b1 > v1) break;
            var rng = new Rng(copy);
            byte palette = FunPalette(ref rng);
            FunRoom room = AddFunRoom(p, FunZone.Clone, u0, b0, u0 + w - 1, b1, FunRoomHeight, FloorKind.FunRaceCarpet, palette);
            var f = new FunFrame(u0, b0, u0 + w - 1, b1, p.Rooms.Count - 1);
            OpenFunDoor(p, room, f, ArchPier.West, 1);
            FurnishFunParty(p, room, f, ref rng, true, copy);
        }
        // The rest of the column: an ordinary party room
        var own = new Rng(Hashing.Hash(seed, bi, bj, SaltFunClone + 2));
        int a0 = u0 + w + 2;
        if (u1 - a0 >= 5)
        {
            FunRoom rest = AddFunRoom(p, FunZone.Party, a0, v0, u1, v1, FunRoomHeight, FloorKind.FunVinylD, FunPalette(ref own));
            var f = new FunFrame(a0, v0, u1, v1, p.Rooms.Count - 1);
            OpenFunRoom(p, rest, f, new[] { ArchPier.North, ArchPier.South, ArchPier.East }, 1, 1, ref own);
            FurnishFunParty(p, rest, f, ref own, false);
        }
    }

    // ================= Furnishing =================

    /// <summary>How many guests a party has, from its key: none at two in five.</summary>
    private static int FunGuestsFor(ulong key)
    {
        double r = Hashing.Unit(Hashing.Mix(key ^ SaltFunGuests));
        return r < 0.4 ? 0 : r < 0.75 ? 2 : r < 0.95 ? 3 : 4;
    }

    private static void FunProp(FunPlanner p, int u, int v, ushort prop, ArchPier facing, int stack = 0)
    {
        if (!p.Free(u, v)) return;
        ref Tile t = ref p.At(u, v);
        t.Variant = prop;
        t.Pier = facing;
        t.Stack = (byte)stack;
    }

    private static void FunItem(FunPlanner p, int u, int v, byte item, ArchPier facing)
    {
        if (!FunPlanner.In(u, v)) return;
        ref Tile t = ref p.At(u, v);
        if (t.Kind != TileKind.Floor || t.Roof != 0) return;
        t.Roof = FunWallItems.Pack(item, facing);
    }

    /// <summary>The floor tiles along one wall of a room, as (a, s) with the way into the room.</summary>
    private static IEnumerable<(int U, int V, ArchPier Into)> FunWallRow(FunFrame f, ArchPier wall)
    {
        switch (wall)
        {
            case ArchPier.North: for (int u = f.U0; u <= f.U1; u++) yield return (u, f.V0, ArchPier.South); break;
            case ArchPier.South: for (int u = f.U0; u <= f.U1; u++) yield return (u, f.V1, ArchPier.North); break;
            case ArchPier.West: for (int v = f.V0; v <= f.V1; v++) yield return (f.U0, v, ArchPier.East); break;
            default: for (int v = f.V0; v <= f.V1; v++) yield return (f.U1, v, ArchPier.West); break;
        }
    }

    /// <summary>
    /// A birthday party room: rows of folding tables in plastic cloths with chairs down both sides, the cake on the
    /// head table, plates and cups and cookies, gifts heaped in a corner, balloons against the ceiling and streamers
    /// across it, bunting along the head wall, string lights, a speaker over the door. With guests, red smileys on
    /// the walls and every light on; without, half the lights dead and balloons on the floor.
    /// </summary>
    private void FurnishFunParty(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng, bool clone, ulong look = 0)
    {
        room.Guests = FunGuestsFor(room.Key);
        if (look == 0) look = room.Key;
        bool party = room.Guests > 0;
        FunLights(p, f, 4, party ? 0.95 : 0.45, party ? 0.03 : 0.1, ref rng);
        int cloth = (room.Palette >> 3) & 7;
        ArchPier along = f.AlongDir;
        bool head = true;
        for (int s = 2; s + 1 <= f.Short - 2; s += 4)
        {
            for (int a = 2; a + 1 <= f.Long - 3; a += 3)
            {
                var (ua, va) = f.P(a, s);
                var (ub, vb) = f.P(a + 1, s);
                if (!p.Free(ua, va) || !p.Free(ub, vb)) continue;
                FunProp(p, ua, va, Props.FunTable, along, cloth * 2);
                FunProp(p, ub, vb, Props.FunTable, along, cloth * 2 + 1);
                for (int k = 0; k < 2; k++)
                {
                    var (tu, tv) = k == 0 ? (ua, va) : (ub, vb);
                    if (head && k == 1)
                    {
                        p.At(tu, tv).Pipe = Hashing.Unit(look << 7) < 0.2 ? Pipes.FunCakeVelvet : Pipes.FunCakeBirthday;
                        room.Head = (p.X0 + tu, p.Z0 + tv);
                        continue;
                    }
                    double r = rng.NextDouble();
                    p.At(tu, tv).Pipe = r < 0.3 ? Pipes.FunPlates : r < 0.55 ? Pipes.FunCups : r < 0.68 ? Pipes.FunCookies : r < 0.8 ? Pipes.FunMess : (byte)0;
                }
                head = false;
                // Chairs down both sides, facing the table; the odd one knocked over
                for (int k = 0; k < 2; k++)
                    foreach (int ds in new[] { -1, 1 })
                    {
                        var (cu, cv) = f.P(a + k, s + ds);
                        ArchPier facing = ds < 0 ? f.AcrossDir : Opposite(f.AcrossDir);
                        int colour = rng.Range(0, 4);
                        FunProp(p, cu, cv, rng.Chance(0.05) ? Props.FunChairTipped : Props.FunChair, facing, colour);
                    }
            }
        }
        if (room.Head == default)
        {
            // Too small for tables: the cake on a single table in the middle
            var (cu, cv) = f.P(f.Long / 2, f.Short / 2);
            if (p.Free(cu, cv)) { FunProp(p, cu, cv, Props.FunTable, along, cloth * 2 + 1); p.At(cu, cv).Pipe = Pipes.FunCakeBirthday; }
            room.Head = (p.X0 + cu, p.Z0 + cv);
        }

        // Gifts heaped in the far corner from the head table
        int gifts = rng.Range(2, 4);
        for (int g = 0; g < 6 && gifts > 0; g++)
        {
            var (gu, gv) = f.P(f.Long - 1 - g % 2, f.Short - 1 - g / 2);
            if (!p.Free(gu, gv)) continue;
            FunProp(p, gu, gv, Props.FunGift, along, rng.Range(0, 4) * 2 + (rng.Chance(0.4) ? 1 : 0));
            gifts--;
        }

        // Balloons overhead, streamers across, what has fallen; confetti about the tables
        int set = room.Palette >> 6;
        for (int a = 0; a < f.Long; a++)
            for (int s = 0; s < f.Short; s++)
            {
                var (u, v) = f.P(a, s);
                ref Tile t = ref p.At(u, v);
                double r = rng.NextDouble();
                if (r < 0.2) t.Overhead = Overheads.FunBalloons;
                else if (s % 3 == 1) t.Overhead = f.AlongX ? Overheads.FunStreamerWE : Overheads.FunStreamerNS;
                if (!p.Free(u, v)) continue;
                double q = rng.NextDouble();
                if (q < (party ? 0.05 : 0.12)) FunProp(p, u, v, Props.FunBalloonsFloor, along, set & 1);
                else if (q < (party ? 0.07 : 0.13)) FunProp(p, u, v, Props.FunBalloonTied, along, rng.Range(0, 4));
                else if (q < 0.2) FunProp(p, u, v, Props.FunConfetti, along);
            }

        // The head wall's bunting, string lights along a long wall, the speaker over the door, posters, smileys
        ArchPier headWall = f.AlongX ? ArchPier.West : ArchPier.North;
        var row = new List<(int U, int V, ArchPier Into)>(FunWallRow(f, headWall));
        string words = row.Count >= 14 ? "happy birthday" : row.Count >= 5 ? "happy" : "";
        int start = (row.Count - words.Length) / 2;
        for (int i = 0; i < row.Count; i++)
        {
            char c = i >= start && i < start + words.Length ? words[i - start] : ' ';
            FunItem(p, row[i].U, row[i].V, FunWallItems.Bunting(c), row[i].Into);
        }
        foreach (var (u, v, into) in FunWallRow(f, f.AlongX ? ArchPier.North : ArchPier.West))
            if (rng.Chance(0.9)) FunItem(p, u, v, FunWallItems.StringLights, into);
        foreach (var (dx, dz) in room.Doors)
        {
            int u = dx - p.X0, v = dz - p.Z0;
            ArchPier into = u == f.U0 ? ArchPier.East : u == f.U1 ? ArchPier.West : v == f.V0 ? ArchPier.South : ArchPier.North;
            p.At(u, v).Roof = 0;
            FunItem(p, u, v, party ? FunWallItems.SpeakerOn : FunWallItems.SpeakerOff, into);
        }
        var walls = new List<(int U, int V, ArchPier Into)>();
        foreach (ArchPier w in AllSides) walls.AddRange(FunWallRow(f, w));
        int posters = rng.Range(1, 2), smileys = party ? rng.Range(0, 2) : 0;
        for (int tries = 0; tries < 20 && posters + smileys > 0; tries++)
        {
            var (u, v, into) = walls[rng.Range(0, walls.Count - 1)];
            if (p.At(u, v).Roof != 0) continue;
            if (posters > 0) { FunItem(p, u, v, (byte)rng.Range(FunWallItems.PosterTime4Fun, FunWallItems.PosterComeJoin), into); posters--; }
            else { FunItem(p, u, v, (byte)(FunWallItems.Smiley1 + rng.Range(0, 3)), into); smileys--; }
        }

        FunGuestSpots(p, room);
        // A party with guests wears a balloon arch outside its door
        if (party) FunDoorArches(p, room);
    }

    /// <summary>Where the guests stand: on clear floor round the head table, nearest first.</summary>
    private static void FunGuestSpots(FunPlanner p, FunRoom room)
    {
        if (room.Guests == 0) return;
        int hu = room.Head.X - p.X0, hv = room.Head.Z - p.Z0;
        var candidates = new List<(int D, int U, int V)>();
        for (int v = room.Z0 - p.Z0; v <= room.Z1 - p.Z0; v++)
            for (int u = room.X0 - p.X0; u <= room.X1 - p.X0; u++)
            {
                Tile t = p.At(u, v);
                if (t.Kind != TileKind.Floor || !IsWalkThroughProp(t.Variant)) continue;
                int d = Math.Abs(u - hu) + Math.Abs(v - hv);
                if (d >= 2) candidates.Add((d * 16 + (u * 7 + v * 3) % 16, u, v));
            }
        candidates.Sort((x, y) => x.D.CompareTo(y.D));
        for (int i = 0; i < candidates.Count && room.Spots.Count < room.Guests; i++)
        {
            var (_, u, v) = candidates[i];
            // Not shoulder to shoulder
            bool near = false;
            foreach (var (sx, sz) in room.Spots) if (Math.Abs(sx - p.X0 - u) + Math.Abs(sz - p.Z0 - v) < 2) near = true;
            if (!near) room.Spots.Add((p.X0 + u, p.Z0 + v));
        }
    }

    /// <summary>The two halves of a balloon arch on the corridor floor either side of each of a room's doorways.</summary>
    private static void FunDoorArches(FunPlanner p, FunRoom room)
    {
        foreach (var (dx, dz) in room.Doors)
        {
            int u = dx - p.X0, v = dz - p.Z0;
            // Walk out through the doorway to the corridor
            foreach (ArchPier side in AllSides)
            {
                var (du, dv) = FacingStep(side);
                if (!FunPlanner.In(u + du, v + dv) || p.At(u + du, v + dv).Kind != TileKind.Doorway) continue;
                int x = u + du, z = v + dv;
                while (FunPlanner.In(x, z) && p.At(x, z).Kind == TileKind.Doorway) { x += du; z += dv; }
                if (!FunPlanner.In(x, z) || p.At(x, z).Kind != TileKind.Floor) break;
                // Either side of the way out, facing out into the corridor
                var (lu, lv) = (x - dv, z + du);
                var (ru, rv) = (x + dv, z - du);
                Tile l = FunPlanner.In(lu, lv) ? p.At(lu, lv) : default, r = FunPlanner.In(ru, rv) ? p.At(ru, rv) : default;
                if (l.Kind == TileKind.Floor && l.Variant == 0 && r.Kind == TileKind.Floor && r.Variant == 0)
                {
                    p.At(lu, lv).Variant = Props.FunArchL; p.At(lu, lv).Pier = side;
                    p.At(ru, rv).Variant = Props.FunArchR; p.At(ru, rv).Pier = side;
                }
                break;
            }
        }
    }

    /// <summary>The cloakroom: gifts heaped everywhere but a way through. The guests' belongings, wrapped.</summary>
    private static void FurnishFunGifts(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        FunLights(p, f, 4, 0.3, 0.2, ref rng);
        for (int a = 0; a < f.Long; a++)
            for (int s = 0; s < f.Short; s++)
            {
                if (s == f.Short / 2) continue; // the way through
                var (u, v) = f.P(a, s);
                if (rng.Chance(0.45)) FunProp(p, u, v, Props.FunGift, f.AlongDir, rng.Range(0, 4) * 2 + (rng.Chance(0.5) ? 1 : 0));
                else if (rng.Chance(0.1)) FunProp(p, u, v, Props.FunConfetti, f.AlongDir);
            }
    }

    /// <summary>
    /// The mural room, as in the photograph: yellow walls with big cartoon figures painted on them two blocks wide,
    /// the red race-track carpet, troffers. Hardly ever a party in it, and all the more wrong for that.
    /// </summary>
    private void FurnishFunMural(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        room.Guests = Hashing.Unit(room.Key << 9) < 0.2 ? 2 : 0;
        FunLights(p, f, 4, 0.9, 0.05, ref rng);
        // The murals go up once the walls are settled (see FinishFunWalls); mark the spots now on the floor in front
        var (cu, cv) = f.P(f.Long / 2, f.Short / 2);
        room.Head = (p.X0 + cu, p.Z0 + cv);
        for (int a = 1; a < f.Long - 1; a++)
            for (int s = 1; s < f.Short - 1; s++)
            {
                var (u, v) = f.P(a, s);
                if (rng.Chance(0.03)) FunProp(p, u, v, Props.FunBalloonsFloor, f.AlongDir, 0);
            }
        FunGuestSpots(p, room);
    }

    /// <summary>A themed room: movie night, a Halloween party, or a dolls' tea party at one long table.</summary>
    private void FurnishFunThemed(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        double r = Hashing.Unit(room.Key << 13);
        if (r < 0.34)
        {
            // Movie night: rows of chairs facing a blank pull-down screen, a popcorn cart at the back
            room.Guests = 0;
            FunLights(p, f, 4, 0.2, 0.1, ref rng);
            int mid = f.Short / 2;
            ArchPier screenWall = f.AlongX ? ArchPier.West : ArchPier.North;
            var row = new List<(int U, int V, ArchPier Into)>(FunWallRow(f, screenWall));
            for (int k = -1; k <= 1; k++)
                if (mid + k >= 0 && mid + k < row.Count)
                    FunItem(p, row[mid + k].U, row[mid + k].V, (byte)(FunWallItems.ScreenM + k), row[mid + k].Into);
            for (int a = 3; a < f.Long - 1; a += 2)
                for (int s = 1; s < f.Short - 1; s++)
                {
                    if (Math.Abs(s - mid) < 1) continue;
                    var (u, v) = f.P(a, s);
                    FunProp(p, u, v, Props.FunChair, Opposite(f.AlongDir), (int)(room.Key % 5));
                }
            var (pu, pv) = f.P(f.Long - 1, 0);
            FunProp(p, pu, pv, Props.FunPopcornCart, Opposite(f.AlongDir));
            var (hu, hv) = f.P(1, mid);
            room.Head = (p.X0 + hu, p.Z0 + hv);
            return;
        }
        if (r < 0.67)
        {
            // Halloween: a party like any other, orange and black, with pumpkins about the floor
            room.Palette = (byte)(room.Palette & ~7 | 0);
            FurnishFunParty(p, room, f, ref rng, false);
            for (int a = 0; a < f.Long; a++)
                for (int s = 0; s < f.Short; s++)
                {
                    var (u, v) = f.P(a, s);
                    if (rng.Chance(0.06)) FunProp(p, u, v, Props.FunPumpkin, f.AlongDir);
                }
            return;
        }
        // The tea party: one long table down the middle, set all the way along, chairs both sides
        room.Guests = FunGuestsFor(room.Key);
        FunLights(p, f, 4, room.Guests > 0 ? 0.9 : 0.4, 0.05, ref rng);
        int s0 = f.Short / 2, cloth = (room.Palette >> 3) & 7;
        for (int a = 2; a + 1 <= f.Long - 3; a += 2)
        {
            var (ua, va) = f.P(a, s0);
            var (ub, vb) = f.P(a + 1, s0);
            FunProp(p, ua, va, Props.FunTable, f.AlongDir, cloth * 2);
            FunProp(p, ub, vb, Props.FunTable, f.AlongDir, cloth * 2 + 1);
            p.At(ua, va).Pipe = Pipes.FunCups;
            p.At(ub, vb).Pipe = a == 2 ? Pipes.FunCakeBirthday : Pipes.FunPlates;
            if (a == 2) room.Head = (p.X0 + ub, p.Z0 + vb);
            for (int k = 0; k < 2; k++)
            {
                var (c1u, c1v) = f.P(a + k, s0 - 1);
                var (c2u, c2v) = f.P(a + k, s0 + 1);
                FunProp(p, c1u, c1v, Props.FunChair, f.AcrossDir, 0);
                FunProp(p, c2u, c2v, Props.FunChair, Opposite(f.AcrossDir), 0);
            }
        }
        FunGuestSpots(p, room);
    }

    /// <summary>
    /// A play room, five high: foam mats, soft-play blocks in the corners, a climbing net on a wall, a slide, and a
    /// ball pit in the middle. One pit in four is deep: dive to its bottom and you come up somewhere else.
    /// </summary>
    private void FurnishFunPlay(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        FunLights(p, f, 4, 0.8, 0.05, ref rng);
        bool deep = Hashing.Unit(room.Key << 17) < 0.25;
        int pa = Math.Min(7, f.Long - 6), ps = Math.Min(7, f.Short - 6);
        int a0 = (f.Long - pa) / 2, s0 = (f.Short - ps) / 2;
        for (int a = a0; a < a0 + pa; a++)
            for (int s = s0; s < s0 + ps; s++)
            {
                var (u, v) = f.P(a, s);
                if (!p.Free(u, v)) continue;
                ref Tile t = ref p.At(u, v);
                bool middle = a > a0 && a < a0 + pa - 1 && s > s0 && s < s0 + ps - 1;
                t.Depth = (byte)(deep && middle ? 3 : 1);
                t.Floor = FloorKind.FunCheckerB;
                if (deep && middle) t.Under = Unders.FunBallPitDeep;
            }
        var (hu, hv) = f.P(a0 + pa / 2, s0 + ps / 2);
        room.Head = (p.X0 + hu, p.Z0 + hv);
        // Foam blocks in two corners
        foreach (var (ca, cs) in new[] { (0, 0), (f.Long - 2, f.Short - 2) })
            for (int k = 0; k < 4; k++)
            {
                var (u, v) = f.P(ca + k % 2, cs + k / 2);
                FunProp(p, u, v, Props.FunFoam, f.AlongDir, rng.Range(0, 3));
            }
        // A climbing net along one wall
        int netAt = rng.Range(2, Math.Max(2, f.Long - 6));
        for (int k = 0; k < 4; k++)
        {
            var (u, v) = f.P(netAt + k, f.Short - 1);
            FunProp(p, u, v, Props.FunNet, Opposite(f.AcrossDir));
        }
        // A slide down toward the pit
        var (su, sv) = f.P(Math.Max(1, a0 - 2), s0 + ps / 2);
        FunProp(p, su, sv, Props.Slide, f.AlongDir);
        for (int a = 0; a < f.Long; a++)
            for (int s = 0; s < f.Short; s++)
            {
                var (u, v) = f.P(a, s);
                if (rng.Chance(0.12)) p.At(u, v).Overhead = Overheads.FunBalloons;
            }
    }

    /// <summary>
    /// A bounce hall: faded carpet, extension cords snaking over it, and one or two bounce houses (walk in under the
    /// arch: the quilted floor bounces you) with their blowers droning beside them. Colder than the rest.
    /// </summary>
    private void FurnishFunBounce(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        FunLights(p, f, 5, 0.7, 0.1, ref rng);
        int houses = f.Long >= 15 ? 2 : 1;
        int s0 = (f.Short - 5) / 2;
        for (int h = 0; h < houses; h++)
        {
            int a0 = houses == 1 ? (f.Long - 5) / 2 : h == 0 ? 2 : f.Long - 7;
            byte colour = (byte)rng.Range(0, 2);
            for (int a = 0; a < 5; a++)
                for (int s = 0; s < 5; s++)
                {
                    var (u, v) = f.P(a0 + a, s0 + s);
                    if (!FunPlanner.In(u, v)) continue;
                    ref Tile t = ref p.At(u, v);
                    bool edgeA = a == 0 || a == 4, edgeS = s == 0 || s == 4;
                    if (edgeA && edgeS)
                    {
                        t.Variant = Props.FunInflatableTower;
                        t.Stack = colour;
                    }
                    else if (edgeA || edgeS)
                    {
                        // The way in, in the middle of the side toward the room's middle line
                        if (s == 4 && a == 2)
                        {
                            t.Variant = Props.FunInflatableArch;
                            t.Pier = f.AcrossDir;
                            t.Stack = colour;
                            continue;
                        }
                        ArchPier into = a == 0 ? f.AlongDir : a == 4 ? Opposite(f.AlongDir) : s == 0 ? f.AcrossDir : Opposite(f.AcrossDir);
                        t = new Tile
                        {
                            Kind = TileKind.Wall, Pattern = WallPattern.FunInflatable, Detail = colour, Pier = into, Height = 3,
                            Floor = FloorKind.FunRetroCarpet, Zone = (byte)FunZone.Bounce,
                        };
                        p.Owner[v * FunPlanner.N + u] = (short)(f.Index + 1);
                    }
                    else
                    {
                        t.Floor = FloorKind.FunInflatableFloor;
                        t.Height = 3;
                        t.Ceiling = CeilingKind.FunInflatableRoof;
                        t.Depth = 0;
                        t.Stair = 0;
                        t.Detail = (byte)(colour | t.Detail & ~7);
                    }
                }
            // The blower against the back of the house, its cord running off to the wall
            var (bu, bv) = f.P(a0 + 2, s0 - 1);
            if (p.Free(bu, bv))
            {
                FunProp(p, bu, bv, Props.FunBlower, f.AcrossDir);
                for (int s = s0 - 2; s >= 0; s--)
                {
                    var (cu, cv) = f.P(a0 + 2, s);
                    if (!p.Free(cu, cv)) break;
                    FunProp(p, cu, cv, Props.FunCord, f.AcrossDir, s == 0 ? 2 : 0);
                }
            }
        }
        var (hu, hv) = f.P(f.Long / 2, f.Short - 1);
        room.Head = (p.X0 + hu, p.Z0 + hv);
    }

    /// <summary>An arcade: cabinets round the walls (half of them dead), air hockey in the middle.</summary>
    private void FurnishFunArcade(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        FunLights(p, f, 4, 0.5, 0.15, ref rng);
        foreach (ArchPier wall in AllSides)
            foreach (var (u, v, into) in FunWallRow(f, wall))
                if (rng.Chance(0.7)) FunProp(p, u, v, Props.Arcade, into);
        for (int a = 3; a + 1 < f.Long - 3; a += 4)
        {
            var (ua, va) = f.P(a, f.Short / 2);
            var (ub, vb) = f.P(a + 1, f.Short / 2);
            if (!p.Free(ua, va) || !p.Free(ub, vb)) continue;
            FunProp(p, ua, va, Props.FunAirHockey, f.AlongDir, 0);
            FunProp(p, ub, vb, Props.FunAirHockey, f.AlongDir, 1);
        }
        var (hu, hv) = f.P(f.Long / 2, f.Short / 2 + 1);
        room.Head = (p.X0 + hu, p.Z0 + hv);
    }

    /// <summary>The bakery: stainless counters round grey walls, ovens, racks of tins of something red. The Red Velvet comes from here.</summary>
    private void FurnishFunKitchen(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        FunLights(p, f, 4, 0.7, 0.1, ref rng);
        foreach (ArchPier wall in AllSides)
            foreach (var (u, v, into) in FunWallRow(f, wall))
            {
                if (!p.Free(u, v)) continue;
                double r = rng.NextDouble();
                if (r < 0.15) FunProp(p, u, v, Props.FunOven, into);
                else if (r < 0.8)
                {
                    FunProp(p, u, v, Props.FunCounter, into);
                    if (rng.Chance(0.2)) p.At(u, v).Pipe = Pipes.FunCakeVelvet;
                }
            }
        for (int a = 3; a < f.Long - 3; a += 2)
        {
            var (u, v) = f.P(a, f.Short / 2);
            FunProp(p, u, v, Props.FunCakeTins, f.AcrossDir);
        }
        var (hu, hv) = f.P(f.Long / 2, f.Short / 2 + 1);
        room.Head = (p.X0 + hu, p.Z0 + hv);
    }

    /// <summary>A waiting room: grey carpet, rows of cushioned chairs facing a reception desk behind glass, and a plain white door out.</summary>
    private void FurnishFunWaiting(FunPlanner p, FunRoom room, FunFrame f, ArchPier[] outer, ref Rng rng)
    {
        FunLights(p, f, 4, 1, 0, ref rng);
        room.Threshold = PlaceFunWallDoor(p, room, f, outer, WallPattern.FunExitDoor, 1);
        var (ru, rv) = f.P(1, f.Short / 2);
        FunProp(p, ru, rv, Props.FunReception, f.AlongDir);
        for (int a = 3; a < f.Long - 1; a += 2)
            for (int s = 1; s < f.Short - 1; s++)
            {
                if (s == f.Short / 2) continue;
                var (u, v) = f.P(a, s);
                FunProp(p, u, v, Props.FunWaitingChair, Opposite(f.AlongDir));
            }
        var (mu, mv) = f.P(f.Long - 1, 0);
        FunProp(p, mu, mv, Props.FunMagazineTable, f.AlongDir);
        room.Head = (p.X0 + ru, p.Z0 + rv);
    }

    /// <summary>The FUN doors: wooden double doors with the big letters, in a little room hung with balloons and COME JOIN US posters.</summary>
    private void FurnishFunVestibule(FunPlanner p, FunRoom room, FunFrame f, ArchPier[] outer, ref Rng rng)
    {
        FunLights(p, f, 3, 1, 0, ref rng);
        room.Threshold = PlaceFunWallDoor(p, room, f, outer, WallPattern.FunDoor, 2);
        foreach (ArchPier w in AllSides)
            foreach (var (u, v, into) in FunWallRow(f, w))
                if (rng.Chance(0.2)) FunItem(p, u, v, FunWallItems.PosterComeJoin, into);
        for (int a = 0; a < f.Long; a++)
            for (int s = 0; s < f.Short; s++)
            {
                var (u, v) = f.P(a, s);
                if (rng.Chance(0.35)) p.At(u, v).Overhead = Overheads.FunBalloons;
                if (rng.Chance(0.15)) FunProp(p, u, v, Props.FunConfetti, f.AlongDir);
            }
        var (hu, hv) = f.P(f.Long / 2, f.Short / 2);
        room.Head = (p.X0 + hu, p.Z0 + hv);
    }

    /// <summary>
    /// A door of the level's own in one of a room's inner walls (the partition, never a side onto a corridor): the
    /// waiting room's way out, the FUN doors. Pier faces into the room; a two-leaf door's Variant is 0 for the leaf on
    /// the left as you face it, 1 the right.
    /// </summary>
    private static bool PlaceFunWallDoor(FunPlanner p, FunRoom room, FunFrame f, ArchPier[] outer, WallPattern pattern, int width)
    {
        foreach (ArchPier side in AllSides)
        {
            if (Array.IndexOf(outer, side) >= 0) continue;
            var row = new List<(int U, int V, ArchPier Into)>(FunWallRow(f, side));
            int start = row.Count / 2 - width / 2;
            if (start < 1 || start + width > row.Count - 1) continue;
            var (du, dv) = FacingStep(side);
            bool ok = true;
            for (int k = 0; k < width && ok; k++)
            {
                var (u, v, _) = row[start + k];
                ok = FunPlanner.In(u + du, v + dv) && p.At(u + du, v + dv).Kind == TileKind.Wall && p.OwnerAt(u + du, v + dv) == 0
                    && p.Free(u, v);
            }
            if (!ok) continue;
            for (int k = 0; k < width; k++)
            {
                var (u, v, into) = row[start + k];
                ref Tile door = ref p.At(u + du, v + dv);
                // Left as you face the door from inside: facing north the left is west (lower u); south, east; east, north; west, south
                bool reversed = side is ArchPier.South or ArchPier.West;
                door = new Tile { Kind = TileKind.Door, Pattern = pattern, Pier = into, Detail = room.Palette, Floor = FloorKind.FunFloor, Variant = (ushort)(width == 1 ? 0 : reversed ? width - 1 - k : k) };
                p.Owner[(v + dv) * FunPlanner.N + u + du] = (short)(p.Rooms.IndexOf(room) + 1);
                p.Reserved[v * FunPlanner.N + u] = true;
            }
            return true;
        }
        return false;
    }

    /// <summary>
    /// Service stairs: a bare stairwell, confetti on the floor, steps climbing into the ceiling. Climb them and you
    /// come out of a stairwell in Level 1, which leads back.
    /// </summary>
    private void FurnishFunStair(FunPlanner p, FunRoom room, FunFrame f, ref Rng rng)
    {
        FunLights(p, f, 4, 0.5, 0.3, ref rng);
        for (int a = f.Long - 3; a < f.Long; a++)
            for (int s = 0; s < f.Short; s++)
            {
                var (u, v) = f.P(a, s);
                ref Tile t = ref p.At(u, v);
                t.Stair = (byte)(a - (f.Long - 3) + 1);
                t.Pier = f.AlongDir;
            }
        room.Threshold = true;
        for (int a = 0; a < f.Long - 3; a++)
            for (int s = 0; s < f.Short; s++)
            {
                var (u, v) = f.P(a, s);
                if (rng.Chance(0.25)) FunProp(p, u, v, Props.FunConfetti, f.AlongDir);
            }
        var (bu, bv) = f.P(f.Long - 4, 0);
        FunProp(p, bu, bv, Props.FunBalloonTied, f.AlongDir, 0);
        var (hu, hv) = f.P(f.Long / 2, f.Short / 2);
        room.Head = (p.X0 + hu, p.Z0 + hv);
    }

    /// <summary>
    /// Crew corridors: a loop of bare grey steel two wide, round the square and across its middle, lit by failing
    /// lights or not at all. Shelves of party supplies, linen carts; and in the dark, balloons tied to nothing.
    /// </summary>
    private void PlanFunService(FunPlanner p, int u0, int v0, int u1, int v1, ref Rng rng)
    {
        int index = p.Rooms.Count;
        var room = new FunRoom { Kind = FunZone.Service, X0 = p.X0 + u0, Z0 = p.Z0 + v0, X1 = p.X0 + u1, Z1 = p.Z0 + v1, Wall = WallPattern.FunSteel, Key = Hashing.Hash(seed, p.X0 + u0, p.Z0 + v0, SaltFunRoom) };
        p.Rooms.Add(room);
        int midV = (v0 + v1) / 2;
        for (int v = v0; v <= v1; v++)
            for (int u = u0; u <= u1; u++)
            {
                bool ring = u - u0 < 2 || u1 - u < 2 || v - v0 < 2 || v1 - v < 2, cross = v == midV || v == midV + 1;
                if (!ring && !cross) continue;
                double r = Hashing.Unit(Hashing.Hash(seed, p.X0 + u, p.Z0 + v, SaltFunLight));
                p.At(u, v) = new Tile
                {
                    Kind = TileKind.Floor, Floor = FloorKind.Concrete, Height = FunCorridorHeight, Zone = (byte)FunZone.Service,
                    Ceiling = (u + v) % 5 == 0 ? (r < 0.25 ? CeilingKind.LightFlicker : r < 0.4 ? CeilingKind.LightOn : CeilingKind.LightOff) : CeilingKind.Tile,
                };
                p.Owner[v * FunPlanner.N + u] = (short)(index + 1);
            }
        var f = new FunFrame(u0, v0, u1, v1, index);
        OpenFunRoom(p, room, f, AllSides, 2, 1, ref rng);
        for (int v = v0; v <= v1; v++)
            for (int u = u0; u <= u1; u++)
            {
                if (!p.Free(u, v)) continue;
                // Beside a wall: shelves and carts; out in the dark: a balloon that should not be there
                ArchPier? wallSide = null;
                foreach (ArchPier side in AllSides)
                {
                    var (du, dv) = FacingStep(side);
                    if (FunPlanner.In(u + du, v + dv) && p.At(u + du, v + dv).Kind == TileKind.Wall) { wallSide = side; break; }
                }
                double r = rng.NextDouble();
                if (wallSide is { } w && r < 0.1) FunProp(p, u, v, Props.FunSupplyShelf, Opposite(w));
                else if (r < 0.13) FunProp(p, u, v, Props.FunLinenCart, ArchPier.North);
                else if (r < 0.155 && p.At(u, v).Ceiling is CeilingKind.Tile or CeilingKind.LightOff) FunProp(p, u, v, Props.FunCBalloon, ArchPier.North, rng.Range(0, 4));
            }
        var (hu, hv) = (u0, midV);
        room.Head = (p.X0 + hu, p.Z0 + hv);
    }

    /// <summary>
    /// An open deck: teak planks along one side of the square under a black sky, deck chairs, caged lamps on the white
    /// bulkhead, a life ring; and past the white rail, black water far below. Climb over and you are overboard.
    /// </summary>
    private void PlanFunDeck(FunPlanner p, int u0, int v0, int u1, int v1, ref Rng rng)
    {
        ArchPier back = AllSides[rng.Range(0, 3)]; // the side the deck runs along (its bulkhead)
        const int width = 5;
        int du0 = back == ArchPier.East ? u1 - width + 1 : u0, du1 = back == ArchPier.West ? u0 + width - 1 : u1;
        int dv0 = back == ArchPier.South ? v1 - width + 1 : v0, dv1 = back == ArchPier.North ? v0 + width - 1 : v1;
        FunRoom deck = AddFunRoom(p, FunZone.Deck, du0, dv0, du1, dv1, FunDeckHeight, FloorKind.FunDeck, 0, WallPattern.FunWall);
        var f = new FunFrame(du0, dv0, du1, dv1, p.Rooms.Count - 1);
        // The sea: everything else in the square, its walls the black of the night
        int su0 = back == ArchPier.West ? du1 + 1 : u0, su1 = back == ArchPier.East ? du0 - 1 : u1;
        int sv0 = back == ArchPier.North ? dv1 + 1 : v0, sv1 = back == ArchPier.South ? dv0 - 1 : v1;
        FunRoom sea = AddFunRoom(p, FunZone.Sea, su0, sv0, su1, sv1, FunDeckHeight, FloorKind.Concrete, 0, WallPattern.FunVoid);
        for (int v = sv0; v <= sv1; v++)
            for (int u = su0; u <= su1; u++)
            {
                ref Tile t = ref p.At(u, v);
                t.Depth = FunSeaDepth;
                t.Under = Unders.FunOverboard;
                t.Ceiling = CeilingKind.FunCeiling;
            }
        for (int v = dv0; v <= dv1; v++)
            for (int u = du0; u <= du1; u++) p.At(u, v).Ceiling = CeilingKind.FunCeiling;
        OpenFunDoor(p, deck, f, back, 1);
        // The rail along the water's edge, facing out over it
        ArchPier seaward = Opposite(back);
        foreach (var (u, v, _) in FunWallRow(f, seaward)) FunProp(p, u, v, Props.FunShipRail, seaward);
        // Lamps and life rings on the bulkhead, deck chairs below them facing the sea
        int k = 0;
        foreach (var (u, v, into) in FunWallRow(f, back))
        {
            if (k % 6 == 3) FunItem(p, u, v, FunWallItems.DeckLamp, into);
            else if (k % 12 == 6) FunItem(p, u, v, FunWallItems.LifeRing, into);
            k++;
        }
        bool alongU = back is ArchPier.North or ArchPier.South;
        int lineU = back == ArchPier.West ? du0 + 1 : back == ArchPier.East ? du1 - 1 : 0;
        int lineV = back == ArchPier.North ? dv0 + 1 : back == ArchPier.South ? dv1 - 1 : 0;
        ArchPier chairWay = alongU ? ArchPier.East : ArchPier.South;
        for (int i = 2; i + 1 < (alongU ? du1 - du0 : dv1 - dv0); i += 4)
        {
            var (ua, va) = alongU ? (du0 + i, lineV) : (lineU, dv0 + i);
            var (ub, vb) = alongU ? (du0 + i + 1, lineV) : (lineU, dv0 + i + 1);
            if (!p.Free(ua, va) || !p.Free(ub, vb)) continue;
            FunProp(p, ua, va, Props.FunDeckChair, chairWay, 0);
            FunProp(p, ub, vb, Props.FunDeckChair, chairWay, 1);
        }
        var (hu, hv) = f.P(f.Long / 2, f.Short / 2);
        deck.Head = (p.X0 + hu, p.Z0 + hv);
        sea.Head = deck.Head;
    }

    // ================= Finishing =================

    /// <summary>
    /// Settles every wall's face: a room's own paint toward the room, the promenades' cream toward a corridor, the black
    /// toward the sea; and on the walls of the mural rooms, the murals.
    /// </summary>
    private void FinishFunWalls(FunPlanner p)
    {
        for (int v = 0; v < FunPlanner.N; v++)
            for (int u = 0; u < FunPlanner.N; u++)
            {
                ref Tile t = ref p.At(u, v);
                if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.FunSolid) continue;
                FunRoom best = null;
                ArchPier bestSide = ArchPier.North, corridorSide = ArchPier.North;
                bool corridor = false;
                foreach (ArchPier side in AllSides)
                {
                    var (du, dv) = FacingStep(side);
                    int x = u + du, z = v + dv;
                    if (FunPlanner.In(x, z))
                    {
                        short owner = p.OwnerAt(x, z);
                        TileKind kind = p.At(x, z).Kind;
                        if (owner > 0 && kind == TileKind.Floor && best == null) { best = p.Rooms[owner - 1]; bestSide = side; }
                        else if (owner == -1 && kind is TileKind.Floor or TileKind.Doorway && !corridor) { corridor = true; corridorSide = side; }
                    }
                    else if (!corridor && FunCorridorAt(p.X0 + x, p.Z0 + z).Zone != FunZone.None) { corridor = true; corridorSide = side; }
                }
                if (best != null)
                {
                    t.Pattern = best.Wall;
                    t.Detail = best.Palette;
                    t.Pier = bestSide;
                }
                else if (corridor)
                {
                    t.Pattern = WallPattern.FunPromenade;
                    t.Pier = corridorSide;
                }
            }

        // The murals: two blocks wide, every seven along each wall of a mural room
        foreach (FunRoom room in p.Rooms)
        {
            if (room.Kind != FunZone.Mural) continue;
            var f = new FunFrame(room.X0 - p.X0, room.Z0 - p.Z0, room.X1 - p.X0, room.Z1 - p.Z0, 0);
            int mural = (int)(room.Key % 4);
            foreach (ArchPier side in AllSides)
            {
                var row = new List<(int U, int V, ArchPier Into)>(FunWallRow(f, side));
                var (du, dv) = FacingStep(side);
                // Left as seen from the room: on the north wall the lower u, on the south the higher; east, the lower v; west, the higher
                bool reversed = side is ArchPier.South or ArchPier.West;
                for (int i = 2; i + 1 < row.Count - 1; i += 7)
                {
                    var (au, av, _) = row[i];
                    var (bu, bv) = (row[i + 1].U, row[i + 1].V);
                    if (!FunPlanner.In(au + du, av + dv) || !FunPlanner.In(bu + du, bv + dv)) continue;
                    ref Tile wa = ref p.At(au + du, av + dv);
                    ref Tile wb = ref p.At(bu + du, bv + dv);
                    if (wa.Kind != TileKind.Wall || wb.Kind != TileKind.Wall || wa.Pattern != WallPattern.FunMural || wb.Pattern != WallPattern.FunMural) continue;
                    wa.Variant = (ushort)(1 + mural * 2 + (reversed ? 1 : 0));
                    wb.Variant = (ushort)(1 + mural * 2 + (reversed ? 0 : 1));
                    mural = (mural + 1) % 4;
                }
            }
        }
    }

    /// <summary>
    /// The lobbies' fittings, on whichever of their walls fall in this block: the brass elevator doors, a deck sign. From
    /// layout version 5 the party has reached the lobbies too (Wikidot's Level Fun is balloons, streamers and confetti
    /// from the first look, and a lobby is where everyone arrives): see <see cref="DressFunLobbyTile"/>, and one pair of
    /// doors in each lobby says OUT OF ORDER =) (elevator Variant 2: the left leaf with the sign).
    /// </summary>
    private void PlaceFunLobbyFittings(FunPlanner p)
    {
        bool party = Version >= 5;
        for (int v = 0; v < FunPlanner.N; v++)
            for (int u = 0; u < FunPlanner.N; u++)
            {
                int ux = p.X0 + u - FunOriginX, uz = p.Z0 + v - FunOriginZ;
                int lineX = (int)Math.Round(ux / 32.0), lineZ = (int)Math.Round(uz / 32.0);
                if (Hashing.Mod(lineX, 3) != 0 || Hashing.Mod(lineZ, 3) != 0) continue;
                int offX = ux - lineX * 32, offZ = uz - lineZ * 32;
                ref Tile t = ref p.At(u, v);
                ulong look = Hashing.Hash(seed, lineX, lineZ, SaltFunLobby);
                // Elevators on the north wall (west of the way in) and the south wall (east of it); from layout version 9
                // one further out in the wider lobby, so a block of wall stands either side of each pair
                int shift = FunLobbyHalfX - 4;
                if (t.Kind == TileKind.Wall && offZ == -5 && (offX == -3 - shift || offX == -2 - shift))
                {
                    t.Pattern = WallPattern.FunElevator;
                    t.Pier = ArchPier.South;
                    t.Variant = (ushort)(offX == -3 - shift ? party && (look & 1) == 0 ? 2 : 0 : 1);
                }
                else if (t.Kind == TileKind.Wall && offZ == 5 && (offX == 2 + shift || offX == 3 + shift))
                {
                    t.Pattern = WallPattern.FunElevator;
                    t.Pier = ArchPier.North;
                    t.Variant = (ushort)(offX == 3 + shift ? party && (look & 1) == 1 ? 2 : 0 : 1);
                }
                else if (t.Kind == TileKind.Floor && offZ == -4 && offX == 3) FunItem(p, u, v, FunWallItems.DeckSign, ArchPier.South);
                else if (party && t.Kind == TileKind.Floor && t.Zone == (byte)FunZone.Lobby) DressFunLobbyTile(p, u, v, offX, offZ, look, shift);
            }
    }

    /// <summary>
    /// A lobby's party (layout version 5), by the tile's place in it (offsets from the crossing, -4 to 4; from layout version 9, -5 to 5 west to east): string lights
    /// along the top of the wall over each pair of elevator doors and confetti trodden into the carpet in front of them,
    /// balloons bunched on the floor beside them, a TIME 4 FUN =) poster by the deck sign, the ship's directory board and
    /// a potted palm (the plan's, never placed before), a cluster of balloons against the ceiling in the middle with
    /// crepe streamers running out from it to the four ways out. The doors' approach and the four openings stay clear
    /// (confetti and the balloons are walked through; the palm stands in a corner).
    /// </summary>
    private static void DressFunLobbyTile(FunPlanner p, int u, int v, int offX, int offZ, ulong look, int shift)
    {
        ref Tile t = ref p.At(u, v);
        // (Layout version 9 on, the lobby is a block wider west and east: what stood against its west wall and before the
        // elevator doors moves out with them, the balloons by the south doors to the new corner; the poster keeps its place
        // by the deck sign, and where things stood before is bare carpet)
        if (shift != 0)
            (offX, offZ) = (offX, offZ) switch
            {
                (-5, _) => (-4, offZ),
                (-4 or -3, -4) => (offX + 1, -4),
                (3 or 4, 4) => (offX - 1, 4),
                (5, 4) => (4, 4),
                (-2, -4) or (2, 4) or (-4, 2) or (-4, 4) => (offX, 99),
                _ => (offX, offZ),
            };
        // The balloons' set and the streamers' colours, as a party room's palette holds them
        byte palette = (byte)((int)((look >> 8) % 3) | (int)((look >> 16) % 3) << 6);
        switch (offX, offZ)
        {
            case (-3 or -2, -4):
                FunItem(p, u, v, FunWallItems.StringLights, ArchPier.South);
                FunProp(p, u, v, Props.FunConfetti, ArchPier.South);
                break;
            case (2 or 3, 4):
                FunItem(p, u, v, FunWallItems.StringLights, ArchPier.North);
                FunProp(p, u, v, Props.FunConfetti, ArchPier.North);
                break;
            case (-4, -4) or (4, 4):
                FunProp(p, u, v, Props.FunBalloonsFloor, ArchPier.South, (int)(look >> 24) & 1);
                break;
            case (4, -4):
                FunItem(p, u, v, FunWallItems.PosterTime4Fun, ArchPier.South);
                break;
            case (-4, 2):
                FunItem(p, u, v, FunWallItems.Directory, ArchPier.East);
                break;
            case (-4, 4):
                FunProp(p, u, v, Props.Palm, ArchPier.North);
                break;
            case (0, 0):
                t.Overhead = Overheads.FunBalloons;
                t.Detail = palette;
                break;
            case (0, _):
                t.Overhead = Overheads.FunStreamerNS;
                t.Detail = palette;
                break;
            case (_, 0):
                t.Overhead = Overheads.FunStreamerWE;
                t.Detail = palette;
                break;
        }
    }

    /// <summary>
    /// Half the blocks have one poster that is wrong: its writing reversed and swimming out of focus, in a room where
    /// the party is over. Touch it and you are somewhere else (Level 4).
    /// </summary>
    private void PlaceReversedPoster(FunPlanner p, int bi, int bj)
    {
        ulong h = Hashing.Hash(seed, bi, bj, SaltFunSpecial + 1);
        if (Hashing.Unit(h) >= 0.5) return;
        var rng = new Rng(h);
        foreach (FunRoom room in p.Rooms)
        {
            if (room.Kind != FunZone.Party || room.Guests > 0) continue;
            var f = new FunFrame(room.X0 - p.X0, room.Z0 - p.Z0, room.X1 - p.X0, room.Z1 - p.Z0, 0);
            foreach (ArchPier side in AllSides)
                foreach (var (u, v, into) in FunWallRow(f, side))
                {
                    ref Tile t = ref p.At(u, v);
                    if (t.Kind != TileKind.Floor || p.Reserved[v * FunPlanner.N + u]) continue;
                    if (t.Roof != 0 && FunWallItems.Rel(FunWallItems.Item(t.Roof)) != 2) continue;
                    if (!rng.Chance(0.15)) continue;
                    t.Roof = FunWallItems.Pack(FunWallItems.PosterReversed, into);
                    room.Threshold = true;
                    return;
                }
        }
    }

    // ================= The level's own thresholds =================

    /// <summary>Clear floor anyone could be put down on (the rules of <see cref="IsArrivalSpot"/>), in any level.</summary>
    public static bool IsOpenArrivalFloor(Tile t) => IsArrivalSpot(t) && t.Zone != (byte)FunZone.Sea;

    /// <summary>Whether a block was dealt a room of a special kind (a waiting room, the FUN doors, service stairs).</summary>
    private bool FunBlockHas(FunZone kind, int bi, int bj)
    {
        ulong special = Hashing.Hash(seed, bi, bj, SaltFunSpecial);
        return kind switch
        {
            FunZone.Waiting => Hashing.Unit(special) < 0.25,
            FunZone.Vestibule => Hashing.Unit(special << 12) < 1 / 9.0,
            FunZone.Stair => Hashing.Unit(special << 24) < 1 / 9.0,
            _ => true,
        };
    }

    /// <summary>
    /// A room of the level with one of its own thresholds in it (the waiting room's door, the FUN doors, the service
    /// stairs), picked for a key: the nearest to a point near the middle of the region the key picks. Null if none.
    /// </summary>
    public FunRoom FunThresholdRoom(FunZone kind, ulong key)
    {
        var (cmx, cmz) = FunArrivalCell(Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltFunSpecial + 2));
        var (bi0, bj0) = FunBlockOf(cmx * MacroSize, cmz * MacroSize);
        // The few nearest, one of them picked by the key, so that two ways in seldom share one way back
        var found = new List<FunRoom>();
        for (int r = 0; r <= 14 && found.Count < 4; r++)
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r || !FunBlockHas(kind, bi0 + di, bj0 + dj)) continue;
                    foreach (FunRoom room in FunPlan(bi0 + di, bj0 + dj).Rooms)
                    {
                        if (room.Kind != kind || !room.Threshold) continue;
                        // Not cut off by the rim
                        int mx = MacroOf((room.X0 + room.X1) / 2), mz = MacroOf((room.Z0 + room.Z1) / 2);
                        bool inside = true;
                        for (int dz = -1; dz <= 1 && inside; dz++)
                            for (int dx = -1; dx <= 1 && inside; dx++) inside = LevelAt(mx + dx, mz + dz) == FunLevel;
                        if (inside) found.Add(room);
                    }
                }
        return found.Count == 0 ? null : found[(int)(Hashing.Mix(key) % (ulong)found.Count)];
    }

    // ================= Ways in from other levels =================

    /// <summary>
    /// For checking that nothing but the entrances changed the other levels: the layout harness sets it (from the environment
    /// variable BACKROOMS_NO_FUN_ENTRANCES=1) to lay out no way into Level Fun. The library never reads the environment, so a
    /// server cannot lay out a different world by accident.
    /// </summary>
    internal static bool NoFunEntrances;

    /// <summary>
    /// Level 0: a cell dressed for a party nobody came to (about one Lobby cell in six hundred, never near spawn):
    /// balloons on the carpet, confetti, a red "=)", and on a wall the TIME 4 FUN =) poster. Touch the poster and you are
    /// in Level Fun. (It was meant to keep to the outer three fifths of the Lobby, but Level 0 has no ring fraction, so
    /// the test of one that stood here was always true and is gone. From layout version 11 the cell must lie beyond the inner two
    /// fifths, by <see cref="LevelDepth"/>.)
    /// </summary>
    public bool IsFunPartyCell(int mx, int mz)
    {
        if (NoFunEntrances) return false;
        if (Math.Abs(mx - spawnMacroX) < 8 && Math.Abs(mz - spawnMacroZ) < 8) return false;
        if (Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltFunL0)) >= 1 / 600.0) return false;
        if (LevelAt(mx, mz) != 0 || RegionAt(mx, mz).Zone != ZoneKind.Lobby || IsRedRoom(mx, mz) || IsManilaMacro(mx, mz)) return false;
        if (Version >= 11 && LevelDepth(mx * MacroSize, mz * MacroSize, 0) <= 0.4) return false;
        return true;
    }

    /// <summary>Dresses a Level 0 party cell (see <see cref="IsFunPartyCell"/>): props only, nothing walled.</summary>
    private void DressFunPartyCell(Builder b, int mx, int mz)
    {
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltFunL0 + 1));
        bool poster = false;
        // The poster first, on the wall nearest the middle of the cell, at eye height
        for (int r = 0; r < 14 && !poster; r++)
            for (int lz = 16 - r; lz <= 16 + r && !poster; lz++)
                for (int lx = 16 - r; lx <= 16 + r && !poster; lx++)
                {
                    if (lx < 1 || lz < 1 || lx >= MacroSize - 1 || lz >= MacroSize - 1) continue;
                    ref Tile t = ref b.At(lx, lz);
                    if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stack != 0 || t.Sealed) continue;
                    foreach (ArchPier side in AllSides)
                    {
                        var (dx, dz) = FacingStep(side);
                        if (b.At(lx + dx, lz + dz).Kind != TileKind.Wall) continue;
                        t.Variant = Props.FunPosterTrap;
                        t.Pier = Opposite(side);
                        poster = true;
                        break;
                    }
                }
        bool smiley = false;
        for (int lz = 1; lz < MacroSize - 1; lz++)
            for (int lx = 1; lx < MacroSize - 1; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stack != 0) continue;
                int d = Math.Abs(lx - 16) + Math.Abs(lz - 16);
                if (d > 14) continue;
                double r = rng.NextDouble();
                if (!smiley && r < 0.03)
                {
                    foreach (ArchPier side in AllSides)
                    {
                        var (dx, dz) = FacingStep(side);
                        if (b.At(lx + dx, lz + dz).Kind != TileKind.Wall) continue;
                        t.Variant = Props.FunSmiley;
                        t.Pier = Opposite(side);
                        t.Stack = (byte)rng.Range(0, 3);
                        smiley = true;
                        break;
                    }
                }
                else if (r < 0.1) { t.Variant = Props.FunBalloonsFloor; t.Stack = (byte)rng.Range(0, 1); }
                else if (r < 0.12) { t.Variant = Props.FunBalloonTied; t.Stack = (byte)rng.Range(0, 4); }
                else if (r < 0.24) t.Variant = Props.FunConfetti;
            }
    }

    /// <summary>
    /// Level 1: whether a stair core's flight climbs into Level Fun: one in twenty, with confetti trickling down the
    /// steps. It is asked by the flight's position: up to layout version 3 its lowest-numbered step tile (the
    /// threshold's origin), from version 4 the top step's.
    /// </summary>
    public bool IsFunStairCore(int originX, int originZ) => !NoFunEntrances && Hashing.Unit(Hashing.Hash(seed, originX, originZ, SaltFunL1)) < (Version >= 12 ? 1 / 80.0 : 1 / 20.0);

    /// <summary>Level 5: whether a locked guest room's door is the FUN doors (one in 150, never a POOL door).</summary>
    private bool IsFunHotelDoor(int roomX, int roomZ) => !NoFunEntrances && Hashing.Unit(Hashing.Hash(seed, roomX, roomZ, SaltFunL5)) < 1 / 150.0;

    /// <summary>
    /// Level 11: green gym doors painted with a tiger, a parrot and a giraffe in the middle of a parking garage's back
    /// wall, its two leaves (Variant 0 the left as you face them from inside). They open onto a waiting room in Level Fun.
    /// </summary>
    private static void PlaceFunMascotDoors(Frame f)
    {
        int mid = f.W / 2, back = f.D - 1;
        for (int k = 0; k < 2; k++)
        {
            Tile wall = f.At(mid - 1 + k, back), inside = f.At(mid - 1 + k, back - 1);
            if (wall.Kind != TileKind.Wall || inside.Kind != TileKind.Floor || inside.Under != 0 || inside.Stair != 0) return;
        }
        for (int k = 0; k < 2; k++)
        {
            ref Tile door = ref f.At(mid - 1 + k, back);
            door.Kind = TileKind.Door;
            door.Under = Unders.FunMascotDoor;
            door.Detail = 0;
            door.Variant = (ushort)(k == 1 ? 0 : 1);
            ref Tile inside = ref f.At(mid - 1 + k, back - 1);
            inside.Variant = 0;
        }
    }

    /// <summary>Level 11: whether a parking garage has the gym doors at its back (one in four).</summary>
    private bool IsFunGarage(int bi, int bj, int x, int half) => !NoFunEntrances && Hashing.Unit(Hashing.Hash(seed, bi * 128 + x, bj * 2 + half, SaltFunL11)) < 0.25;
}
