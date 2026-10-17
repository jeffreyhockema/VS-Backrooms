using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 52, "School Halls" (experimental): kept as level 23 (<see cref="Level52"/>) and shown as "52". One endless school
/// building, the same for everyone in the world, in a round noclip region far out to the south-south-east (after Fandom's
/// "Greenfield Campus"; the design is docs/design/experimental-levels/52-plan.md). No thresholds in or out: the cheats menu
/// or <c>/backrooms goto 52</c> only.
///
/// <para><b>The lattice.</b> Main halls run straight through the whole region every <see cref="L52Period"/> blocks each way,
/// seven wide (x or z mod 96 in 1-7), lit down the middle, lined with lockers on both walls; where two cross there is a
/// square with a pillar. Between four halls lies a <b>wing</b>, 87 blocks square (mod 96 in 9-95, its walls at 8 and 96).
/// A wing is laid out once from its own hash (<see cref="L52PlanOf"/>, kept in a <see cref="PlanCache{T}"/>) and copied
/// into the cells it covers; nothing depends on a neighbour, so wings never have to agree.</para>
///
/// <para><b>A wing</b> is six rows of classrooms 12-13 deep, two rows against the main halls and four along two secondary
/// halls (three wide) that cross the wing and open into the main halls at both ends: every room has its door onto a
/// hall, one in five a second door into the room next to it. Classrooms hold rows of desks facing a chalkboard on a side
/// wall and a teacher's desk; most are dark (their lights are off, as the lore has it), a few are store rooms or stripped
/// bare. One wing in ten is a <b>gym</b> (8 high, a sports floor with court lines, hoops at both ends, benches) and one
/// in eight a <b>canteen</b> (5 high, long tables, vending machines, a serving counter), in place of the middle rows on one
/// half of the wing; neither is laid out unless the whole wing and the cells round it are the level's.</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> is the <see cref="L52Zone"/>; a wall tile's <see cref="Tile.Height"/> is how
/// high it is dressed (4, or the gym's 8 / the canteen's 5 beside them), <see cref="Tile.Detail"/> 1 marks a bank of
/// lockers on its <see cref="Tile.Pier"/> face. A chalkboard piece is <see cref="Props.L52Chalkboard"/> (Stack: 0 left end,
/// 1 middle, 2 right end, as seen from in front).</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2300-0x23BF are this level's (0x23C0-0x23FF its thresholds').</summary>
    private const ulong SaltL52Shape = 0x2301, SaltL52Wing = 0x2310, SaltL52Room = 0x2311, SaltL52Light = 0x2312, SaltL52Hall = 0x2313;

    /// <summary>The lattice: a main hall every 96 blocks each way; a wing's inside is 87 square, its plan 89 with its walls.</summary>
    public const int L52Period = 96, L52WingSize = 87, L52Grid = 89;

    /// <summary>What part of the school a tile is in (kept in <see cref="Tile.Zone"/>).</summary>
    public enum L52Zone : byte { None, Hall, Hub, Corridor, Classroom, Store, Gym, Canteen, Wall }

    public enum L52WingKind : byte { Classrooms, Gym, Canteen }

    public enum L52RoomKind : byte { Classroom, Empty, Store, Gym, Canteen }

    /// <summary>A room of a wing, in the plan's own coordinates (P along its row, Q across; inclusive, the inside only).</summary>
    public sealed class L52Room
    {
        public int P0, Q0, P1, Q1;
        public L52RoomKind Kind;
        public bool Lit;
        public int Doors;
    }

    /// <summary>
    /// The plan of one wing. Laid out in its own coordinates (P, Q), which are the wing's (A east, B south) or, in a
    /// flipped wing, the same transposed; <see cref="Tiles"/> are kept by (A, B), -1..87 each way (the walls round it
    /// included).
    /// </summary>
    public sealed class L52Plan
    {
        public int Wx, Wz;
        public L52WingKind Kind;
        public bool Flip;
        public readonly Tile[] Tiles = new Tile[L52Grid * L52Grid];
        public readonly List<L52Room> Rooms = new();

        public (int A, int B) AB(int p, int q) => Flip ? (q, p) : (p, q);
        public ref Tile At(int p, int q)
        {
            var (a, b) = AB(p, q);
            return ref Tiles[a + 1 + (b + 1) * L52Grid];
        }
        public ref Tile AtAB(int a, int b) => ref Tiles[a + 1 + (b + 1) * L52Grid];
        /// <summary>A way in the plan's coordinates (North = -Q, West = -P) as a way in the world.</summary>
        public ArchPier Dir(ArchPier d) => !Flip ? d : d switch
        {
            ArchPier.North => ArchPier.West,
            ArchPier.South => ArchPier.East,
            ArchPier.West => ArchPier.North,
            _ => ArchPier.South,
        };
        /// <summary>The block position of a place in the plan.</summary>
        public (int X, int Z) World(int p, int q)
        {
            var (a, b) = AB(p, q);
            return (Wx * L52Period + 9 + a, Wz * L52Period + 9 + b);
        }
    }

    private PlanCache<L52Plan> l52Plans;

    /// <summary>A wing's plan (shared: read it, never change it).</summary>
    public L52Plan L52PlanOf(int wx, int wz) =>
        LazyInitializer.EnsureInitialized(ref l52Plans, () => new PlanCache<L52Plan>(48, MakeL52Plan)).Get(wx, wz);

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees east of south.</summary>
    private double L52Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    public int L52CentreX => spawnMacroX + (int)Math.Round(L52Reach * Math.Sin(Math.PI / 8));
    public int L52CentreZ => spawnMacroZ + (int)Math.Round(L52Reach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells.</summary>
    public int L52Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL52(double mx, double mz) => InRoundRegion(mx, mz, L52CentreX, L52CentreZ, L52Radius, SaltL52Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L52ArrivalCell(ulong h) => RoundArrivalCell(h, L52CentreX, L52CentreZ, L52Radius);

    /// <summary>Arriving: out in a main hall, never in a classroom.</summary>
    private static bool IsL52ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone is (byte)L52Zone.Hall or (byte)L52Zone.Hub;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L52ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the halls and wings are laid over the edges).</summary>
    private Edge L52Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L52Wall };

    /// <summary>
    /// Lays out one of the level's cells: the main halls from arithmetic, the rest copied from the plans of the wings it
    /// covers; where the region ends, a hallway runs round inside its wall (<see cref="CarveEdgeHall"/>) so nothing it cuts
    /// through is left shut off.
    /// </summary>
    private void BuildLevel52(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int u = Hashing.Mod(gx, L52Period), v = Hashing.Mod(gz, L52Period);
                bool hallX = u is >= 1 and <= 7, hallZ = v is >= 1 and <= 7;
                if (hallX || hallZ)
                {
                    L52HallTile(ref t, gx, gz, u, v, hallX, hallZ);
                    continue;
                }
                int wx = Hashing.FloorDiv(gx, L52Period) - (u == 0 ? 1 : 0), wz = Hashing.FloorDiv(gz, L52Period) - (v == 0 ? 1 : 0);
                int a = u == 0 ? L52WingSize : u - 9, bb = v == 0 ? L52WingSize : v - 9;
                t = L52PlanOf(wx, wz).AtAB(a, bb);
            }
        if (WalledNeighbours(Level52, mx, mz) != null) CarveEdgeHall(b, mx, mz, GetEdge(mx, mz, west: true), GetEdge(mx, mz, west: false));
    }

    /// <summary>A tile of a main hall, or of a square where two cross.</summary>
    private void L52HallTile(ref Tile t, int gx, int gz, int u, int v, bool hallX, bool hallZ)
    {
        t.Kind = TileKind.Floor;
        t.Floor = FloorKind.L52Floor;
        t.Ceiling = CeilingKind.L52Ceiling;
        t.Zone = (byte)(hallX && hallZ ? L52Zone.Hub : L52Zone.Hall);
        ulong h = Hashing.Hash(seed, gx, gz, SaltL52Light);
        double r = Hashing.Unit(h);
        CeilingKind Light(bool emits) => r < 0.07 ? CeilingKind.LightOff : r < 0.12 ? CeilingKind.LightFlicker : emits ? CeilingKind.LightOn : CeilingKind.LightLit;
        if (hallX && hallZ)
        {
            // The square where two halls cross: a pillar in the middle, a light at each corner of it
            if (u == 4 && v == 4)
            {
                t.Kind = TileKind.Wall;
                t.Pattern = WallPattern.L52Wall;
                t.Zone = (byte)L52Zone.Wall;
                t.Height = 4;
                return;
            }
            if (u is 2 or 6 && v is 2 or 6) t.Ceiling = Light(true);
            return;
        }
        // Down the middle of a hall, a light every six blocks: one in two gives light, the rest only glow
        if (hallX && u == 4 && Hashing.Mod(gz, 6) == 3) t.Ceiling = Light(Hashing.Mod(Hashing.FloorDiv(gz, 6), 2) == 0);
        if (hallZ && v == 4 && Hashing.Mod(gx, 6) == 3) t.Ceiling = Light(Hashing.Mod(Hashing.FloorDiv(gx, 6), 2) == 0);
        bool side = hallX ? u is 1 or 7 : v is 1 or 7;
        if (!side) return;
        // Just past some crossings, a vending machine or a water cooler against the lockers
        int along = hallX ? v : u;
        if (along == 9)
        {
            ulong c = Hashing.Hash(seed, Hashing.FloorDiv(gx, L52Period), Hashing.FloorDiv(gz, L52Period), SaltL52Hall);
            int which = (hallX ? 0 : 2) + ((hallX ? u : v) == 7 ? 1 : 0);
            if ((int)(c % 4) == which && Hashing.Unit(c) < 0.5)
            {
                t.Variant = Hashing.Unit(Hashing.Mix(c)) < 0.6 ? Props.Vending : Props.Cooler;
                // Facing out from the wall it stands against
                t.Pier = hallX ? (u == 1 ? ArchPier.East : ArchPier.West) : (v == 1 ? ArchPier.South : ArchPier.North);
                return;
            }
        }
        // Now and then a bin, or a wet-floor sign, against the lockers
        double p = Hashing.Unit(Hashing.Mix(h));
        if (p < 0.004) t.Variant = Props.TrashCan;
        else if (p < 0.006)
        {
            t.Variant = Props.WetFloorSign;
            t.Pier = hallX ? ArchPier.North : ArchPier.East;
        }
    }

    // ================= A wing =================

    /// <summary>Whether a wing and the cells round it are all the level's (a gym or a canteen is laid out only then).</summary>
    private bool L52WingInside(int wx, int wz)
    {
        int x0 = MacroOf(wx * L52Period + 8) - 1, x1 = MacroOf(wx * L52Period + L52Period) + 1;
        int z0 = MacroOf(wz * L52Period + 8) - 1, z1 = MacroOf(wz * L52Period + L52Period) + 1;
        for (int mz = z0; mz <= z1; mz++)
            for (int mx = x0; mx <= x1; mx++)
                if (LevelAt(mx, mz) != Level52) return false;
        return true;
    }

    /// <summary>The rows of rooms across a wing (Q from, Q to, and the way their doors face) and its two secondary halls.</summary>
    private static readonly (int Q0, int Q1, ArchPier Door)[] L52Rows =
    {
        (0, 11, ArchPier.North), (13, 24, ArchPier.South), (30, 42, ArchPier.North),
        (44, 55, ArchPier.South), (61, 72, ArchPier.North), (74, 86, ArchPier.South),
    };
    private static readonly (int Q0, int Q1)[] L52Halls = { (26, 28), (57, 59) };

    private L52Plan MakeL52Plan(int wx, int wz)
    {
        var plan = new L52Plan { Wx = wx, Wz = wz };
        ulong h = Hashing.Hash(seed, wx, wz, SaltL52Wing);
        var rng = new Rng(Hashing.Mix(h));
        plan.Flip = (h & 1) != 0;
        double r = Hashing.Unit(h);
        plan.Kind = r < 0.10 ? L52WingKind.Gym : r < 0.22 ? L52WingKind.Canteen : L52WingKind.Classrooms;
        if (plan.Kind != L52WingKind.Classrooms && !L52WingInside(wx, wz)) plan.Kind = L52WingKind.Classrooms;
        bool special = plan.Kind != L52WingKind.Classrooms, low = (h >> 1 & 1) == 0;
        // The big room takes the second and third rows and the hall between them, on one half of the wing
        int s0 = low ? 0 : 44, s1 = low ? 42 : 86, sq0 = 13, sq1 = 42, sWall = 43;

        for (int i = 0; i < plan.Tiles.Length; i++)
            plan.Tiles[i] = new Tile
            {
                Kind = TileKind.Wall, Pattern = WallPattern.L52Wall, Zone = (byte)L52Zone.Wall, Floor = FloorKind.L52Floor,
                Ceiling = CeilingKind.L52Ceiling, Height = 4,
            };
        // Lockers along every main hall
        for (int i = 0; i < L52WingSize; i++)
        {
            Locker(plan, -1, i, ArchPier.West);
            Locker(plan, L52WingSize, i, ArchPier.East);
            Locker(plan, i, -1, ArchPier.North);
            Locker(plan, i, L52WingSize, ArchPier.South);
        }

        // The secondary halls, opening into the main halls at both ends (or into the big room)
        foreach (var (hq0, hq1) in L52Halls)
        {
            bool cut = special && hq0 == 26;
            for (int p = 0; p < L52WingSize; p++)
            {
                if (cut && p >= s0 && p <= s1) continue;
                if (cut && p == sWall) continue;
                for (int q = hq0; q <= hq1; q++)
                {
                    ref Tile t = ref plan.At(p, q);
                    Open(ref t, L52Zone.Corridor, FloorKind.L52Floor);
                    if (q == hq0 + 1 && Hashing.Mod(p, 6) == 2) t.Ceiling = L52Light(plan, p, q, Hashing.Mod(p / 6, 2) == 0);
                }
                Locker(plan, p, hq0 - 1, ArchPier.South);
                Locker(plan, p, hq1 + 1, ArchPier.North);
            }
            for (int q = hq0; q <= hq1; q++)
            {
                if (!(cut && low)) Open(ref plan.At(-1, q), L52Zone.Corridor, FloorKind.L52Floor);
                if (!(cut && !low)) Open(ref plan.At(L52WingSize, q), L52Zone.Corridor, FloorKind.L52Floor);
                if (cut) Door(ref plan.At(sWall, q), L52Zone.Corridor);
            }
        }

        // The rows of rooms
        foreach (var (q0, q1, door) in L52Rows)
        {
            bool cut = special && q0 >= sq0 && q1 <= sq1;
            int pa = cut && low ? sWall + 1 : 0, pb = cut && !low ? sWall - 1 : L52WingSize - 1;
            bool extra = false;
            for (int p = pa; p <= pb;)
            {
                int rem = pb - p + 1;
                int w = rem <= 13 ? rem : rem <= 22 ? (rem - 1) / 2 : rng.Range(9, 12);
                L52LayRoom(plan, p, q0, p + w - 1, q1, door, ref extra, p + w < pb);
                p += w + 1;
            }
        }

        if (special) L52LayBig(plan, s0, sq0, s1, sq1, low);

        // Each chalkboard piece knows which end of its board it is (left and right as seen from in front)
        for (int b = 0; b < L52WingSize; b++)
            for (int a = 0; a < L52WingSize; a++)
            {
                ref Tile t = ref plan.AtAB(a, b);
                if (t.Variant != Props.L52Chalkboard) continue;
                var (lx, lz) = L52Step(L52LeftOf(L52Opposite(t.Pier)));
                bool Board(int x, int z) => x >= 0 && z >= 0 && x < L52WingSize && z < L52WingSize && plan.AtAB(x, z).Variant == Props.L52Chalkboard;
                t.Stack = (byte)(!Board(a + lx, b + lz) ? 0 : !Board(a - lx, b - lz) ? 2 : 1);
            }

        // Walls are dressed as high as the tallest room beside them
        for (int b = -1; b <= L52WingSize; b++)
            for (int a = -1; a <= L52WingSize; a++)
            {
                ref Tile t = ref plan.AtAB(a, b);
                if (!t.IsWallLike) continue;
                int height = 4;
                foreach (var (dx, dz) in Steps)
                {
                    int x = a + dx, z = b + dz;
                    if (x < -1 || z < -1 || x > L52WingSize || z > L52WingSize) continue;
                    byte zone = plan.AtAB(x, z).Zone;
                    height = Math.Max(height, zone == (byte)L52Zone.Gym ? 8 : zone == (byte)L52Zone.Canteen ? 5 : 4);
                }
                t.Height = (byte)height;
            }
        return plan;
    }

    private static void Locker(L52Plan plan, int p, int q, ArchPier face)
    {
        ref Tile t = ref plan.At(p, q);
        if (t.Kind != TileKind.Wall) return;
        t.Detail = 1;
        t.Pier = plan.Dir(face);
    }

    private static void Open(ref Tile t, L52Zone zone, FloorKind floor)
    {
        t.Kind = TileKind.Floor;
        t.Zone = (byte)zone;
        t.Floor = floor;
        t.Detail = 0;
    }

    private static void Door(ref Tile t, L52Zone zone)
    {
        t.Kind = TileKind.Doorway;
        t.Zone = (byte)zone;
        t.Detail = 0;
    }

    /// <summary>The state of a light of a wing, by hash: a few dead, a few failing.</summary>
    private CeilingKind L52Light(L52Plan plan, int p, int q, bool emits, double dead = 0.07)
    {
        var (x, z) = plan.World(p, q);
        double r = Hashing.Unit(Hashing.Hash(seed, x, z, SaltL52Light));
        return r < dead ? CeilingKind.LightOff : r < dead + 0.05 ? CeilingKind.LightFlicker : emits ? CeilingKind.LightOn : CeilingKind.LightLit;
    }

    private static ArchPier L52Opposite(ArchPier d) => d switch
    {
        ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East,
    };

    /// <summary>The left hand of someone looking the given way.</summary>
    private static ArchPier L52LeftOf(ArchPier looking) => looking switch
    {
        ArchPier.North => ArchPier.West, ArchPier.South => ArchPier.East, ArchPier.East => ArchPier.North, _ => ArchPier.South,
    };

    private static (int Dx, int Dz) L52Step(ArchPier d) => d switch
    {
        ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0),
    };

    /// <summary>
    /// One room of a row (its inside P0-P1 by Q0-Q1), its door onto the hall on its <paramref name="door"/> side, perhaps
    /// a second door into the next room along (<paramref name="next"/>: there is one), and what is in it.
    /// </summary>
    private void L52LayRoom(L52Plan plan, int p0, int q0, int p1, int q1, ArchPier door, ref bool extra, bool next)
    {
        var (wx0, wz0) = plan.World(p0, q0);
        var rng = new Rng(Hashing.Hash(seed, wx0, wz0, SaltL52Room));
        int w = p1 - p0 + 1;
        double r = rng.NextDouble();
        var room = new L52Room
        {
            P0 = p0, Q0 = q0, P1 = p1, Q1 = q1,
            Kind = w < 8 || r < 0.08 ? L52RoomKind.Store : r < 0.18 ? L52RoomKind.Empty : L52RoomKind.Classroom,
            Lit = rng.Chance(1 / 6.0), Doors = extra ? 1 : 0,
        };
        plan.Rooms.Add(room);
        L52Zone zone = room.Kind == L52RoomKind.Store ? L52Zone.Store : L52Zone.Classroom;
        for (int q = q0; q <= q1; q++)
            for (int p = p0; p <= p1; p++) Open(ref plan.At(p, q), zone, FloorKind.L52Room);

        // The door onto the hall, about the middle of the room's front; the odd one also into the next room
        int dq = door == ArchPier.North ? q0 - 1 : q1 + 1;
        int dp = Math.Clamp((p0 + p1) / 2 + rng.Range(-2, 2), p0 + 1, p1 - 1);
        Door(ref plan.At(dp, dq), zone);
        room.Doors++;
        int sideQ = door == ArchPier.North ? q0 + 1 : q1 - 1;
        extra = next && rng.Chance(0.2);
        if (extra)
        {
            Door(ref plan.At(p1 + 1, sideQ), zone);
            room.Doors++;
        }

        // Lights in a grid: dark but for one room in six
        for (int q = q0 + 2; q <= q1 - 1; q += 4)
            for (int p = p0 + 2; p <= p1 - 1; p += 4)
                plan.At(p, q).Ceiling = room.Lit ? L52Light(plan, p, q, ((p - p0) / 4 + (q - q0) / 4) % 2 == 0, 0.15) : CeilingKind.LightOff;

        void Put(int p, int q, ushort prop, ArchPier facing, byte stack = 0)
        {
            ref Tile t = ref plan.At(p, q);
            t.Variant = prop;
            t.Pier = plan.Dir(facing);
            t.Stack = stack;
        }

        switch (room.Kind)
        {
            case L52RoomKind.Classroom:
                // The chalkboard on the wall at the low-P end, the desks in rows facing it, the teacher's desk beside it
                for (int q = q0 + 3; q <= Math.Min(q0 + 8, q1 - 2); q++) Put(p0, q, Props.L52Chalkboard, ArchPier.East);
                for (int p = p0 + 3; p <= p1 - 1; p += 2)
                    for (int q = q0 + 2; q <= q1 - 2; q += 2)
                        if (rng.Chance(0.93)) Put(p, q, Props.L52Desk, ArchPier.West);
                Put(p0 + 1, door == ArchPier.North ? q1 - 1 : q0 + 1, Props.Desk, ArchPier.East);
                // One in six has the chairs stacked at the back
                if (rng.Chance(1 / 6.0))
                    for (int q = q0 + 3; q <= q1 - 3; q += 3) Put(p1, q, Props.ChairStack, ArchPier.North);
                if (rng.Chance(0.5)) Put(p1, door == ArchPier.North ? q1 : q0, Props.Wastebasket, ArchPier.North);
                break;
            case L52RoomKind.Store:
                // Shelves down both long walls, a few boxes on the floor
                for (int q = q0 + 2; q <= q1 - 2; q++)
                {
                    if (rng.Chance(0.8)) Put(p0, q, Props.Shelf, ArchPier.West);
                    if (rng.Chance(0.8)) Put(p1, q, Props.Shelf, ArchPier.East);
                }
                for (int k = rng.Range(1, 3); k > 0; k--) Put(rng.Range(p0 + 2, p1 - 2), rng.Range(q0 + 3, q1 - 3), Props.CardboardBoxes, ArchPier.North);
                break;
            case L52RoomKind.Empty:
                // Stripped: a desk left behind
                if (rng.Chance(0.5)) Put(rng.Range(p0 + 2, p1 - 2), rng.Range(q0 + 3, q1 - 3), Props.L52Desk, ArchPier.West);
                break;
        }
    }

    /// <summary>The gym or the canteen: inside P s0-s1 by Q q0-q1, its doors onto the main hall and the secondary hall.</summary>
    private void L52LayBig(L52Plan plan, int s0, int q0, int s1, int q1, bool low)
    {
        bool gym = plan.Kind == L52WingKind.Gym;
        var room = new L52Room { P0 = s0, Q0 = q0, P1 = s1, Q1 = q1, Kind = gym ? L52RoomKind.Gym : L52RoomKind.Canteen, Lit = true, Doors = 1 };
        plan.Rooms.Add(room);
        L52Zone zone = gym ? L52Zone.Gym : L52Zone.Canteen;
        for (int q = q0; q <= q1; q++)
            for (int p = s0; p <= s1; p++) Open(ref plan.At(p, q), zone, gym ? FloorKind.L52Gym : FloorKind.L52Floor);
        // Doors onto the main hall: double doors where the secondary hall would have run, and two more
        int edge = low ? -1 : L52WingSize;
        foreach (int q in new[] { 16, 17, 26, 27, 28, 38, 39 }) Door(ref plan.At(edge, q), zone);
        room.Doors += 3;

        void Put(int p, int q, ushort prop, ArchPier facing, byte stack = 0)
        {
            ref Tile t = ref plan.At(p, q);
            t.Variant = prop;
            t.Pier = plan.Dir(facing);
            t.Stack = stack;
        }

        if (gym)
        {
            // The court: a line round it two in from the walls and one across the middle
            int c0 = s0 + 2, c1 = s1 - 2, d0 = q0 + 3, d1 = q1 - 3, mid = (s0 + s1) / 2;
            for (int q = d0; q <= d1; q++)
                for (int p = c0; p <= c1; p++)
                {
                    bool alongP = q == d0 || q == d1, alongQ = p == c0 || p == c1 || p == mid;
                    if (!alongP && !alongQ) continue;
                    // A line along P runs along the world's X unless the wing is flipped
                    bool westEast = alongP ? !plan.Flip : plan.Flip;
                    plan.At(p, q).Floor = westEast ? FloorKind.L52GymLineWE : FloorKind.L52GymLineNS;
                }
            // Hoops at both ends, benches down one side
            int hq = (q0 + q1) / 2;
            Put(s0 + 1, hq, Props.BasketballHoop, ArchPier.East);
            Put(s1 - 1, hq, Props.BasketballHoop, ArchPier.West);
            for (int p = s0 + 6; p <= s1 - 6; p++)
                if ((p - s0) % 8 != 0) Put(p, q0, Props.Bench, ArchPier.South);
            // High lights in rows
            for (int q = q0 + 3; q <= q1 - 1; q += 6)
                for (int p = s0 + 3; p <= s1 - 1; p += 6)
                    plan.At(p, q).Ceiling = L52Light(plan, p, q, ((p - s0) / 6 + (q - q0) / 6) % 2 == 0, 0.1);
        }
        else
        {
            // Long tables with chairs down both sides, in four rows, an aisle across the middle where the doors are
            foreach (int tq in new[] { q0 + 4, q0 + 9, q1 - 11, q1 - 6 })
                for (int p = s0 + 4; p <= s1 - 4; p++)
                {
                    if ((p - s0 - 4) % 9 == 8) continue; // a gap between tables
                    Put(p, tq, Props.FoldingTable, ArchPier.North);
                    if ((p & 1) == 0)
                    {
                        Put(p, tq - 1, Props.FoldingChair, ArchPier.South);
                        Put(p, tq + 1, Props.FoldingChair, ArchPier.North);
                    }
                }
            // Vending machines along the wall at the low-Q side, a serving counter and its kitchen at the high-Q side
            for (int p = s0 + 3; p <= s1 - 3; p += 3) Put(p, q0, (p / 3 & 1) == 0 ? Props.Vending : Props.SnackVending, ArchPier.South);
            int k0 = low ? s0 + 6 : s1 - 20, k1 = k0 + 14;
            for (int p = k0; p <= k1; p++)
            {
                Put(p, q1 - 2, Props.SnackCounter, ArchPier.North, (byte)(p == k0 + 3 ? 1 : (p - k0) % 4 == 1 ? 2 : 0));
                if ((p - k0) % 5 == 2) Put(p, q1, (p & 1) == 0 ? Props.Stove : Props.Fryer, ArchPier.North);
            }
            for (int q = q0 + 2; q <= q1 - 1; q += 4)
                for (int p = s0 + 2; p <= s1 - 1; p += 4)
                    plan.At(p, q).Ceiling = L52Light(plan, p, q, ((p - s0) / 4 + (q - q0) / 4) % 2 == 0, 0.12);
        }
    }

    /// <summary>Which of the level's props (<see cref="Props.L52First"/>-<see cref="Props.L52Last"/>) people walk through: the chalkboards (they hang on the wall).</summary>
    private static bool L52WalkThrough(ushort variant) => variant == Props.L52Chalkboard;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one everywhere (its entry in <see cref="LevelTemperatures"/>).</summary>
    private float L52Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level52];

    /// <summary>Reality stability: a little steadier than neutral everywhere; a school is a calm place.</summary>
    private float L52Stability(double x, double y, double z, int floorY, float drift) => 1.1f;
}
