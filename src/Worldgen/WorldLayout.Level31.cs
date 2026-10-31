using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 31, "Roller Rink" (experimental): kept as level 24 (<see cref="Level31"/>) and shown as "31". An endless 1990s
/// roller rink, the same for everyone in the world, in a round noclip region far out to the west-north-west (the design is
/// docs/design/experimental-levels/31-plan.md). No thresholds in or out: the cheats menu or <c>/backrooms goto 31</c> only.
///
/// <para><b>The lattice.</b> Neon halls run straight through the whole region every <see cref="L31Period"/> blocks each
/// way, five wide (x or z mod 128 in 1-5) and five high, on a galaxy carpet under black ceilings, a coloured neon tube
/// down the middle and neon strips along both walls' feet. Between four halls lies a <b>complex</b>, 121 blocks square
/// (mod 128 in 7-127, its walls at 6 and 128), laid out once from its own hash (<see cref="L31PlanOf"/>, a
/// <see cref="PlanCache{T}"/>), possibly mirrored and transposed, and copied into the cells it covers.</para>
///
/// <para><b>A complex</b> (<see cref="MakeL31Plan"/>): the rink hall in the middle (85 x 69, 7 high, its ceiling a block under the band's top so the mantle cap never meets a light: an oval of maple boards
/// inside a low barrier with gaps, a carpeted skirt round it with benches and the DJ booth, mirrors on the walls, a ring of
/// coloured tubes and a disco ball); round it a four-wide service corridor; round that the rooms: the lobby (always,
/// facing the hall in front), a snack bar, skate rental and an arcade in the front band, and on the other three sides
/// bathrooms, HVAC and store rooms, a cinema, a second arcade, a lounge or a dim glowing-carpet room, each with its door
/// onto the corridor. Passages from the corridor open into the halls on the other three sides, the lobby has its front
/// doors onto the hall and an arcade in front has a second door there. One complex in ten is an <b>emptiness</b>: one dim
/// bare room the whole size of a complex (a third of them carpeted in glowing carpet). The rink is a five-high "tiny" one
/// in one complex in five, and wherever the complex or the cells round it are not all the level's.</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> is the <see cref="L31Zone"/>; <see cref="Tile.Height"/> on a floor tile is
/// how many blocks of air it has, on a wall how high it is dressed. <see cref="Tile.Detail"/>: bits 0-2 the hue of the
/// tile's light or neon (<see cref="L31Hue"/>), bits 3-5 a sub-kind (a rink board's stripe, a wall's material
/// (<see cref="L31Wall"/>), a corridor's pipe run), bit 6 a neon strip at the foot of the wall behind (its
/// <see cref="Tile.Pier"/> the way it faces), bit 7 a mirror on the wall's <see cref="Tile.Pier"/> face.
/// <see cref="Tile.Overhead"/> carries the halls' neon tubes and the disco ball (<see cref="L31Overhead"/>).</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2400-0x24BF are this level's (0x24C0-0x24FF its thresholds').</summary>
    private const ulong SaltL31Shape = 0x2401, SaltL31Complex = 0x2410, SaltL31Room = 0x2411, SaltL31Light = 0x2412, SaltL31Hall = 0x2413,
        SaltL31Clad = 0x2416;

    /// <summary>The lattice: a neon hall every 128 blocks each way; a complex's inside is 121 square, its plan 123 with its walls.</summary>
    public const int L31Period = 128, L31Size = 121, L31Grid = 123;

    /// <summary>What part of the rink a tile is in (kept in <see cref="Tile.Zone"/>).</summary>
    public enum L31Zone : byte
    {
        None, Hall, Crossing, Lobby, Corridor, Rink, Skirt, Snack, Rental, Arcade, Cinema, Bath, Hvac, Store, CarpetRoom, Lounge, Empty, Wall,
    }

    /// <summary>The bits of <see cref="Tile.Detail"/> (see the class remarks).</summary>
    public const byte L31HueMask = 7, L31SubShift = 3, L31SubMask = 7 << 3, L31RailBit = 0x40, L31MirrorBit = 0x80;

    /// <summary>The hues of the rooms' tubes (<c>l31-tube-*</c>); 6 is the plain fluorescent panel, 7 none. In the halls the same
    /// bits pick a Level 3999 neon colour (<see cref="L3999Colours"/>).</summary>
    public static class L31Hue
    {
        public const byte Magenta = 0, Cyan = 1, Amber = 2, Green = 3, Violet = 4, White = 5, Fluorescent = 6, None = 7;
    }

    /// <summary>What a wall is faced with (its sub-kind): the rink's paint, bare concrete, Skate Rental's blue, bathroom tile,
    /// the arcade's and the cinema's dark paint, a size chart sign at rel 2, a bank of lockers on its Pier face.</summary>
    public static class L31Wall
    {
        public const byte Skate = 0, Concrete = 1, Blue = 2, Glazed = 3, Dark = 4, Chart = 5, Locker = 6, Brick = 7;
    }

    /// <summary>
    /// What is pinned to a wall on its <see cref="Tile.Pier"/> face (a wall's Detail bits 0-2, which on a floor tile are its
    /// light's hue): the taped sign over the food court's bins, a handmade OUT OF ORDER sign by an arcade's door, the food
    /// court's menu board, an advert for a brand that does not exist, the kitchen's EMPLOYEES ONLY door and the white door
    /// marked 70 (both closed: painted on the wall, lower half at rel 1 and upper at rel 2).
    /// </summary>
    public static class L31Sign
    {
        public const byte None = 0, Trash = 1, OutOfOrder = 2, Menu = 3, Advert = 4, StaffDoor = 5, Door70 = 6;
    }

    /// <summary>A rink board's sub-kind; a corridor tile's pipe run (along X or Z, in the world).</summary>
    public const byte L31BoardPlain = 0, L31BoardStripeNS = 1, L31BoardStripeWE = 2, L31BoardCentre = 3, L31PipeX = 1, L31PipeZ = 2;

    /// <summary>Other floor sub-kinds: a cinema row raised 1-3 blocks (the sub-kind is the step), the food court's kitchen
    /// tiles, a flooded HVAC room's water.</summary>
    public const byte L31SubKitchen = 4, L31SubFlood = 5;

    /// <summary>Values of <see cref="Tile.Overhead"/> (the level's 140-149): a hall's neon tube under the ceiling, lit or dead, and the disco ball.</summary>
    public static class L31Overhead
    {
        public const byte NeonNS = 140, NeonWE = 141, DeadNS = 142, DeadWE = 143, DiscoBall = 144;
        /// <summary>The star-shaped light at the rink's centre (Wikidot), and a CCTV camera under the ceiling of an employees' lounge (Pier the way it looks).</summary>
        public const byte Star = 145, Cctv = 146;
        /// <summary>A hall tile by a wall, its wall clad (rel 2 up, toward its Pier) in the hall mural, or in black lacquer with
        /// chrome-framed mirrors (<c>l31-cladding</c>; which, per side of each stretch of hall, by hash).</summary>
        public const byte Mural = 147, Mirrors = 148;
    }

    /// <summary>The level's props (<see cref="Props.L31First"/>-<see cref="Props.L31Last"/>), all at rel 1 but the cinema screen.</summary>
    public static class L31Props
    {
        /// <summary>The rink's low barrier (a block of <c>l31-skatewall-dasher</c>).</summary>
        public const ushort Dasher = 700;
        /// <summary>Level 3999's arcade machines (Pier the way the player faces them back; Stack the game for a cabinet).</summary>
        public const ushort Cabinet = 701, DeadCabinet = 702, Pinball = 703, Claw = 704, SkeeLane = 705, SkeeTarget = 706, PrizeCounter = 707;
        /// <summary>A counter (Level 3999's reception desk; Stack 0 left end, 1 middle, 2 right end), the DJ's screen, a vending machine (Stack 0 snacks, 1 drinks), a bin, a couch (Stack 0 left, 1 right).</summary>
        public const ushort Counter = 708, DjScreen = 709, Vending = 710, Bin = 711, Couch = 712;
        /// <summary>The cinema's screen, hung under the ceiling (Level Fun's pull-down screen; Stack 0 l, 1 m, 2 r).</summary>
        public const ushort Screen = 713;
        /// <summary>A short wooden gate with flaps in a gap of the rink's barrier (walked through; Stack 0 along X, 1 along Z).</summary>
        public const ushort Gate = 714;
        /// <summary>The food court: an orange plastic chair, a square table, a park bench screwed to the floor by the wall (Stack 0 orange, 1 green), the condiment stand, the soda fountain (Almond Water).</summary>
        public const ushort Chair = 715, Table = 716, ParkBench = 717, Condiments = 718, Fountain = 719;
        /// <summary>The DJ station: a desk (Stack 0 a turntable, 1 the mixer; Pier the way the crowd sees it) and a PA speaker.</summary>
        public const ushort DjDesk = 720, Speaker = 721;
        /// <summary>The arcade's green-card dispenser, and a 1980s box cabinet (Stack the game, 0-2).</summary>
        public const ushort CardDispenser = 722, RetroCabinet = 723;
        /// <summary>Skate Rental's cubby shelf of skates; a cinema's continuous metal bench; a cinema's big TV (Stack 0-2 its column from the viewer's left; the rows are rel 3 and 2).</summary>
        public const ushort SkateShelf = 724, CinemaBench = 725, Tv = 726;
        /// <summary>The employees' lounge: the CCTV desk.</summary>
        public const ushort Monitors = 727;
        /// <summary>Where one of the level's staff stands while anyone is near (Regions.L31System; nothing is built): Stack 0 the Coach behind the rental counter, 1 the food court's server, 2 the DJ.</summary>
        public const ushort StaffSpot = 728;
    }

    /// <summary>The staff a <see cref="L31Props.StaffSpot"/> is for.</summary>
    public const byte L31Coach = 0, L31Server = 1, L31Dj = 2;

    public enum L31Kind : byte { Rinks, Empty }

    /// <summary>A room of a complex, in the plan's own coordinates (inclusive, the inside only).</summary>
    public sealed class L31Room
    {
        public int P0, Q0, P1, Q1, Doors;
        public L31Zone Kind;
    }

    /// <summary>
    /// The plan of one complex, laid out in its own coordinates (P, Q); in the world (A east, B south) the same, or with Q
    /// reversed (<see cref="Mirror"/>), and transposed after that (<see cref="Flip"/>). <see cref="Tiles"/> are kept by (A, B),
    /// -1..121 each way (the walls round it included).
    /// </summary>
    public sealed class L31Plan
    {
        public int Wx, Wz;
        public L31Kind Kind;
        public bool Flip, Mirror, Tiny;
        public readonly Tile[] Tiles = new Tile[L31Grid * L31Grid];
        public readonly List<L31Room> Rooms = new();

        public (int A, int B) AB(int p, int q)
        {
            if (Mirror) q = L31Size - 1 - q;
            return Flip ? (q, p) : (p, q);
        }
        public ref Tile At(int p, int q)
        {
            var (a, b) = AB(p, q);
            return ref Tiles[a + 1 + (b + 1) * L31Grid];
        }
        public ref Tile AtAB(int a, int b) => ref Tiles[a + 1 + (b + 1) * L31Grid];
        /// <summary>A way in the plan's coordinates (North = -Q, West = -P) as a way in the world.</summary>
        public ArchPier Dir(ArchPier d)
        {
            if (Mirror) d = d switch { ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, _ => d };
            return !Flip ? d : d switch
            {
                ArchPier.North => ArchPier.West,
                ArchPier.South => ArchPier.East,
                ArchPier.West => ArchPier.North,
                _ => ArchPier.South,
            };
        }
        /// <summary>Whether a line along P runs west-east in the world.</summary>
        public bool AlongPIsX => !Flip;
        /// <summary>The block position of a place in the plan.</summary>
        public (int X, int Z) World(int p, int q)
        {
            var (a, b) = AB(p, q);
            return (Wx * L31Period + 7 + a, Wz * L31Period + 7 + b);
        }
    }

    private PlanCache<L31Plan> l31Plans;

    /// <summary>A complex's plan (shared: read it, never change it).</summary>
    public L31Plan L31PlanOf(int wx, int wz) =>
        LazyInitializer.EnsureInitialized(ref l31Plans, () => new PlanCache<L31Plan>(32, MakeL31Plan)).Get(wx, wz);

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees north of west.</summary>
    private double L31Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    public int L31CentreX => spawnMacroX - (int)Math.Round(L31Reach * Math.Cos(Math.PI / 8));
    public int L31CentreZ => spawnMacroZ - (int)Math.Round(L31Reach * Math.Sin(Math.PI / 8));

    /// <summary>The region's radius in macro cells.</summary>
    public int L31Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL31(double mx, double mz) => InRoundRegion(mx, mz, L31CentreX, L31CentreZ, L31Radius, SaltL31Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L31ArrivalCell(ulong h) => RoundArrivalCell(h, L31CentreX, L31CentreZ, L31Radius);

    /// <summary>Arriving: out in a neon hall, in a lobby or on the carpet round a rink, never in a room or out on the boards.</summary>
    private static bool IsL31ArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone is (byte)L31Zone.Hall or (byte)L31Zone.Crossing or (byte)L31Zone.Lobby or (byte)L31Zone.Skirt;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L31ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the halls and complexes are laid over the edges).</summary>
    private Edge L31Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L31Wall };

    /// <summary>
    /// Lays out one of the level's cells: the neon halls from arithmetic, the rest copied from the plans of the complexes it
    /// covers; where the region ends, a hallway runs round inside its wall (<see cref="CarveEdgeHall"/>).
    /// </summary>
    private void BuildLevel31(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int u = Hashing.Mod(gx, L31Period), v = Hashing.Mod(gz, L31Period);
                bool hallX = u is >= 1 and <= 5, hallZ = v is >= 1 and <= 5;
                if (hallX || hallZ)
                {
                    L31HallTile(ref t, gx, gz, u, v, hallX, hallZ);
                    continue;
                }
                t = L31PlanTile(gx, gz);
            }
        if (WalledNeighbours(Level31, mx, mz) != null) CarveEdgeHall(b, mx, mz, GetEdge(mx, mz, west: true), GetEdge(mx, mz, west: false));
    }

    /// <summary>The planned tile at a block position off the halls.</summary>
    private Tile L31PlanTile(int gx, int gz)
    {
        int u = Hashing.Mod(gx, L31Period), v = Hashing.Mod(gz, L31Period);
        int wx = Hashing.FloorDiv(gx, L31Period) - (u == 0 ? 1 : 0), wz = Hashing.FloorDiv(gz, L31Period) - (v == 0 ? 1 : 0);
        int a = u == 0 ? L31Size : u - 7, bb = v == 0 ? L31Size : v - 7;
        return L31PlanOf(wx, wz).AtAB(a, bb);
    }

    /// <summary>A tile of a neon hall, or of a square where two cross.</summary>
    private void L31HallTile(ref Tile t, int gx, int gz, int u, int v, bool hallX, bool hallZ)
    {
        t.Kind = TileKind.Floor;
        t.Floor = FloorKind.L31Floor;
        t.Ceiling = CeilingKind.L31Ceiling;
        t.Height = 5;
        if (hallX && hallZ)
        {
            t.Zone = (byte)L31Zone.Crossing;
            // A magenta panel over the middle of the square
            t.Detail = L31Hue.Magenta;
            if (u == 3 && v == 3) t.Ceiling = CeilingKind.LightOn;
            return;
        }
        t.Zone = (byte)L31Zone.Hall;
        // Each stretch of hall between two crossings has its own neon colour
        int along = hallX ? gz : gx;
        ulong s = Hashing.Hash(seed, Hashing.FloorDiv(gx, L31Period), Hashing.FloorDiv(gz, L31Period), SaltL31Hall + (hallX ? 0UL : 1UL));
        t.Detail = (byte)(s % 6);
        ulong h = Hashing.Hash(seed, gx, gz, SaltL31Light);
        // A tube down the middle every four blocks, one in fourteen dead
        int across = hallX ? u : v;
        if (across == 3 && Hashing.Mod(along, 4) == 2)
        {
            bool dead = Hashing.Unit(h) < 0.07;
            t.Overhead = hallX ? (dead ? L31Overhead.DeadNS : L31Overhead.NeonNS) : (dead ? L31Overhead.DeadWE : L31Overhead.NeonWE);
        }
        if (across is not (1 or 5)) return;
        // Along the walls: the neon strip at their foot where there is a wall behind (not a door); now and then a bench or a bin
        int bx = hallX ? gx + (u == 1 ? -1 : 1) : gx, bz = hallZ ? gz + (v == 1 ? -1 : 1) : gz;
        if (L31PlanTile(bx, bz).Kind != TileKind.Wall) return;
        ArchPier facing = hallX ? (u == 1 ? ArchPier.East : ArchPier.West) : (v == 1 ? ArchPier.South : ArchPier.North);
        t.Pier = facing;
        // The wall above the neon strip: each side of each stretch is clad in the mural (three in five) or in black lacquer
        // with chrome-framed mirrors ("many chambers of shiny surfaces": Wikidot)
        ulong clad = Hashing.Hash(seed, Hashing.FloorDiv(gx, L31Period), Hashing.FloorDiv(gz, L31Period), SaltL31Clad + (ulong)facing);
        t.Overhead = Hashing.Unit(clad) < 0.6 ? L31Overhead.Mural : L31Overhead.Mirrors;
        double p = Hashing.Unit(Hashing.Mix(h));
        if (p < 0.006) t.Variant = p < 0.004 ? Props.Bench : L31Props.Bin;
        else t.Detail |= L31RailBit;
    }

    // ================= A complex =================

    /// <summary>Whether a complex and the cells round it are all the level's (a full-height rink is laid out only then).</summary>
    private bool L31ComplexInside(int wx, int wz)
    {
        int x0 = MacroOf(wx * L31Period + 6) - 1, x1 = MacroOf(wx * L31Period + L31Period) + 1;
        int z0 = MacroOf(wz * L31Period + 6) - 1, z1 = MacroOf(wz * L31Period + L31Period) + 1;
        for (int mz = z0; mz <= z1; mz++)
            for (int mx = x0; mx <= x1; mx++)
                if (LevelAt(mx, mz) != Level31) return false;
        return true;
    }

    private static void L31Open(ref Tile t, L31Zone zone, int height, byte hue = L31Hue.None)
    {
        t.Kind = TileKind.Floor;
        t.Zone = (byte)zone;
        t.Height = (byte)height;
        t.Detail = hue;
        t.Variant = 0;
        t.Stack = 0;
    }

    private static void L31Door(ref Tile t, L31Zone zone)
    {
        t.Kind = TileKind.Doorway;
        t.Zone = (byte)zone;
        t.Detail = 0;
    }

    /// <summary>How many blocks of air each zone has.</summary>
    private static int L31Air(L31Zone zone, bool tiny) => zone switch
    {
        L31Zone.Rink or L31Zone.Skirt => tiny ? 5 : 7,
        L31Zone.Hall or L31Zone.Crossing or L31Zone.Lobby => 5,
        L31Zone.Cinema => 6,
        _ => 4,
    };

    private L31Plan MakeL31Plan(int wx, int wz)
    {
        var plan = new L31Plan { Wx = wx, Wz = wz };
        ulong h = Hashing.Hash(seed, wx, wz, SaltL31Complex);
        var rng = new Rng(Hashing.Mix(h));
        // Never transposed: the arcade is to the east of the rink, the DJ station on its south side and the cinema to the
        // north, as the lore has them (mirrored, the front band is on the south and the back rooms on the north)
        plan.Flip = false;
        plan.Mirror = (h >> 1 & 1) != 0;
        plan.Kind = Hashing.Unit(h) < 0.10 ? L31Kind.Empty : L31Kind.Rinks;
        plan.Tiny = rng.Chance(0.2) || !L31ComplexInside(wx, wz);
        for (int i = 0; i < plan.Tiles.Length; i++)
            plan.Tiles[i] = new Tile
            {
                Kind = TileKind.Wall, Pattern = WallPattern.L31Wall, Zone = (byte)L31Zone.Wall, Floor = FloorKind.L31Floor,
                Ceiling = CeilingKind.L31Ceiling, Height = 4,
            };
        const int last = L31Size - 1;
        if (plan.Kind == L31Kind.Empty) L31LayEmpty(plan, rng.Chance(1 / 3.0));
        else
        {
            // The front band: a snack bar, skate rental, the lobby, an arcade
            L31LayRoom(plan, 0, 0, 26, 19, rng.Chance(0.6) ? L31Zone.Snack : L31Zone.Lounge, ArchPier.South);
            L31LayRoom(plan, 28, 0, 44, 19, rng.Chance(0.6) ? L31Zone.Rental : L31Zone.Store, ArchPier.South);
            L31LayRoom(plan, 46, 0, 74, 19, L31Zone.Lobby, ArchPier.South);
            // (the arcade is the rarer part to find: Wikidot)
            bool arcade = rng.Chance(0.45);
            L31LayRoom(plan, 76, 0, last, 19, arcade ? L31Zone.Arcade : L31Zone.Lounge, ArchPier.South);
            if (arcade) for (int p = 97; p <= 99; p++) L31Door(ref plan.At(p, -1), L31Zone.Arcade);
            // Doors between the snack bar, the rental counter and the lobby
            for (int q = 8; q <= 9; q++)
            {
                L31Door(ref plan.At(27, q), (L31Zone)plan.At(26, q).Zone);
                L31Door(ref plan.At(45, q), L31Zone.Lobby);
            }
            // The lobby's front doors onto the hall
            for (int p = 57; p <= 63; p++) L31Door(ref plan.At(p, -1), L31Zone.Lobby);

            // The service corridor round the rink, and the passages from it out to the halls on the other three sides
            for (int q = 21; q <= 99; q++)
                for (int p = 13; p <= 107; p++)
                    if (q <= 24 || q >= 96 || p <= 16 || p >= 104) L31Open(ref plan.At(p, q), L31Zone.Corridor, 4);
            for (int i = 58; i <= 61; i++)
            {
                for (int k = 0; k <= 12; k++)
                {
                    L31Open(ref plan.At(k, i), L31Zone.Corridor, 4);
                    L31Open(ref plan.At(last - k, i), L31Zone.Corridor, 4);
                }
                for (int k = 100; k <= last; k++) L31Open(ref plan.At(i, k), L31Zone.Corridor, 4);
                L31Door(ref plan.At(-1, i), L31Zone.Corridor);
                L31Door(ref plan.At(L31Size, i), L31Zone.Corridor);
                L31Door(ref plan.At(i, L31Size), L31Zone.Corridor);
            }
            L31LayCorridorFittings(plan);

            // The rooms down the sides and along the back
            int bath = 0;
            (int Q0, int Q1)[] sideRooms = { (21, 38), (40, 56), (63, 80), (82, 99) };
            for (int k = 0; k < 4; k++)
            {
                var (q0, q1) = sideRooms[k];
                for (int side = 0; side < 2; side++)
                {
                    double r = rng.NextDouble();
                    L31Zone z = r < 0.30 ? L31Zone.Bath : r < 0.52 ? L31Zone.Hvac : r < 0.74 ? L31Zone.Store : r < 0.84 ? L31Zone.CarpetRoom : L31Zone.Lounge;
                    if (k == 1 && side == 1 && bath == 0) z = L31Zone.Bath;
                    if (z == L31Zone.Bath) bath++;
                    if (side == 0) L31LayRoom(plan, 0, q0, 11, q1, z, ArchPier.East);
                    else L31LayRoom(plan, 109, q0, last, q1, z, ArchPier.West);
                }
            }
            (int P0, int P1)[] backRooms = { (0, 27), (29, 56), (63, 90), (92, last) };
            foreach (var (p0, p1) in backRooms)
            {
                double r = rng.NextDouble();
                // (a cinema only where the back rooms lie north of the rink: "walking northward ... one will stumble upon the Cinema")
                L31Zone z = r < 0.25 ? (plan.Mirror ? L31Zone.Cinema : L31Zone.Store) : r < 0.33 ? L31Zone.Arcade : r < 0.48 ? L31Zone.Bath
                    : r < 0.63 ? L31Zone.Hvac : r < 0.73 ? L31Zone.Snack : r < 0.85 ? L31Zone.Store : L31Zone.Lounge;
                L31LayRoom(plan, p0, 101, p1, last, z, ArchPier.North);
            }
            L31LayRink(plan);
        }
        L31DressWalls(plan);
        return plan;
    }

    /// <summary>The state of a light, by hash: a few dead, a few failing; <paramref name="emits"/> the ones that give light.</summary>
    private CeilingKind L31Light(L31Plan plan, int p, int q, bool emits, double dead = 0.04, double flicker = 0.05)
    {
        var (x, z) = plan.World(p, q);
        double r = Hashing.Unit(Hashing.Hash(seed, x, z, SaltL31Light));
        return r < dead ? CeilingKind.LightOff : r < dead + flicker ? CeilingKind.LightFlicker : emits ? CeilingKind.LightOn : CeilingKind.LightLit;
    }

    private static void L31Put(L31Plan plan, int p, int q, ushort prop, ArchPier facing, byte stack = 0)
    {
        ref Tile t = ref plan.At(p, q);
        if (t.Kind != TileKind.Floor) return;
        t.Variant = prop;
        t.Pier = plan.Dir(facing);
        t.Stack = stack;
    }

    /// <summary>The fluorescent panels down the middle of the service corridor, and the pipes along its outer wall.</summary>
    private void L31LayCorridorFittings(L31Plan plan)
    {
        for (int q = 21; q <= 99; q++)
            for (int p = 13; p <= 107; p++)
            {
                ref Tile t = ref plan.At(p, q);
                if (t.Zone != (byte)L31Zone.Corridor) continue;
                bool ns = q <= 24, ss = q >= 96, ws = p <= 16, es = p >= 104;
                bool alongP = (ns || ss) && !(ws || es);
                bool alongQ = (ws || es) && !(ns || ss);
                t.Detail = L31Hue.Fluorescent;
                if (alongP && q is 22 or 98 && Hashing.Mod(p, 6) == 3 || alongQ && p is 14 or 106 && Hashing.Mod(q, 6) == 3)
                    t.Ceiling = L31Light(plan, p, q, (alongP ? p / 6 : q / 6) % 2 == 0, 0.10, 0.08);
                // The pipe run along the outer wall
                bool pipeP = q is 21 or 99 && p is >= 14 and <= 106, pipeQ = p is 13 or 107 && q is >= 22 and <= 98;
                if (pipeP || pipeQ)
                {
                    bool x = pipeP == plan.AlongPIsX;
                    t.Detail = (byte)(L31Hue.Fluorescent | (x ? L31PipeX : L31PipeZ) << L31SubShift);
                }
            }
    }

    /// <summary>
    /// One room (its inside P0-P1 by Q0-Q1), its door onto the corridor on its <paramref name="door"/> side, and what is in it.
    /// </summary>
    private void L31LayRoom(L31Plan plan, int p0, int q0, int p1, int q1, L31Zone zone, ArchPier door)
    {
        var (wx0, wz0) = plan.World(p0, q0);
        var rng = new Rng(Hashing.Hash(seed, wx0, wz0, SaltL31Room));
        var room = new L31Room { P0 = p0, Q0 = q0, P1 = p1, Q1 = q1, Kind = zone, Doors = 1 };
        plan.Rooms.Add(room);
        byte hue = (byte)rng.Range(0, 5);
        if (zone is L31Zone.Bath or L31Zone.Hvac or L31Zone.Store) hue = L31Hue.White;
        if (zone == L31Zone.Arcade) hue = L31Hue.Violet;
        // (the food court warm, the lounge under plain office fluorescents)
        if (zone == L31Zone.Snack) hue = rng.Chance(0.5) ? L31Hue.Amber : L31Hue.White;
        if (zone == L31Zone.Lounge) hue = L31Hue.Fluorescent;
        int air = L31Air(zone, plan.Tiny);
        for (int q = q0; q <= q1; q++)
            for (int p = p0; p <= p1; p++) L31Open(ref plan.At(p, q), zone, air, hue);

        // The door, two wide, about the middle of the side it is on (kept within the corridor's reach)
        int doorP, doorQ;
        if (door is ArchPier.North or ArchPier.South)
        {
            int dq = door == ArchPier.North ? q0 - 1 : q1 + 1;
            int dp = Math.Clamp((p0 + p1) / 2 + rng.Range(-2, 2), Math.Max(p0, 14), Math.Min(p1 - 1, 105));
            (doorP, doorQ) = (dp, dq);
            L31Door(ref plan.At(dp, dq), zone);
            L31Door(ref plan.At(dp + 1, dq), zone);
            if (zone == L31Zone.Lobby) for (int p = 58; p <= 62; p++) L31Door(ref plan.At(p, dq), zone);
        }
        else
        {
            int dp = door == ArchPier.West ? p0 - 1 : p1 + 1;
            int dq = Math.Clamp((q0 + q1) / 2 + rng.Range(-2, 2), q0 + 1, q1 - 2);
            (doorP, doorQ) = (dp, dq);
            L31Door(ref plan.At(dp, dq), zone);
            L31Door(ref plan.At(dp, dq + 1), zone);
        }

        // Lights in a grid (the arcade mostly dark, its screens its light; the cinema and the glowing carpet entirely)
        for (int q = q0 + 2; q <= q1 - 1; q += 4)
            for (int p = p0 + 2; p <= p1 - 1; p += 4)
            {
                bool emits = ((p - p0) / 4 + (q - q0) / 4) % 2 == 0;
                CeilingKind light = zone switch
                {
                    L31Zone.CarpetRoom or L31Zone.Cinema => CeilingKind.L31Ceiling,
                    L31Zone.Arcade => ((p - p0) / 4 + (q - q0) / 4) % 3 == 0 ? L31Light(plan, p, q, true) : CeilingKind.LightOff,
                    L31Zone.Hvac => L31Light(plan, p, q, emits, 0.25, 0.10),
                    _ => L31Light(plan, p, q, emits),
                };
                plan.At(p, q).Ceiling = light;
            }

        int w = p1 - p0 + 1, d = q1 - q0 + 1;
        bool wide = w >= d;
        // The room in its own terms: u along the wall with the door, v from the far wall (0) to the door's (len - 1)
        int across = door is ArchPier.North or ArchPier.South ? w : d, len = door is ArchPier.North or ArchPier.South ? d : w;
        (int P, int Q) At(int u, int v) => door switch
        {
            ArchPier.South => (p0 + u, q0 + v),
            ArchPier.North => (p0 + u, q1 - v),
            ArchPier.East => (p0 + v, q0 + u),
            _ => (p1 - v, q0 + u),
        };
        ArchPier toNear = door, toFar = L31Opposite(door);
        ArchPier toLowU = door is ArchPier.North or ArchPier.South ? ArchPier.West : ArchPier.North, toHighU = L31Opposite(toLowU);
        void Put(int u, int v, ushort prop, ArchPier facing, byte stack = 0)
        {
            var (p, q) = At(u, v);
            L31Put(plan, p, q, prop, facing, stack);
        }
        void Sign(int u, int v, byte sign, ArchPier face)
        {
            var (p, q) = At(u, v);
            L31SignOn(plan, p, q, sign, face);
        }
        void Box(int u, int v)
        {
            var (p, q) = At(u, v);
            ref Tile t = ref plan.At(p, q);
            if (t.Kind == TileKind.Floor && t.Variant == 0) t.SupplyBox = true;
        }
        // Where the door is, in the room's terms (its first tile)
        int doorU = door is ArchPier.North or ArchPier.South ? doorP - p0 : doorQ - q0;
        switch (zone)
        {
            case L31Zone.Lobby:
                // The front counter facing the doors, couches, lockers along one wall, the size chart, vending machines
                for (int p = 49; p <= 55; p++) L31Put(plan, p, 12, L31Props.Counter, ArchPier.North, (byte)(p == 49 ? 0 : p == 55 ? 2 : 1));
                L31Put(plan, 70, 5, L31Props.Couch, ArchPier.West, 0);
                L31Put(plan, 70, 6, L31Props.Couch, ArchPier.West, 1);
                L31Put(plan, 70, 10, L31Props.Couch, ArchPier.West, 0);
                L31Put(plan, 70, 11, L31Props.Couch, ArchPier.West, 1);
                L31Put(plan, 47, 19, L31Props.Vending, ArchPier.North, 0);
                L31Put(plan, 48, 19, L31Props.Vending, ArchPier.North, 1);
                L31Put(plan, 47, 1, L31Props.Bin, ArchPier.North);
                for (int q = 2; q <= 16; q++)
                {
                    ref Tile wall = ref plan.At(75, q);
                    if (wall.Kind != TileKind.Wall) continue;
                    wall.Detail = (byte)(L31Wall.Locker << L31SubShift);
                    wall.Pier = plan.Dir(ArchPier.West);
                }
                for (int p = 50; p <= 51; p++) plan.At(p, 20).Detail = (byte)(L31Wall.Chart << L31SubShift);
                break;
            case L31Zone.Snack:
                {
                    // The food court (Wikidot): the kitchen along the far wall behind the counter, its EMPLOYEES ONLY door and
                    // the menu board over it; the counter with the soda fountain (Almond Water) and the server behind it; the
                    // condiment stand by the queue; square tables with orange plastic chairs; orange and green park benches
                    // screwed down by the side walls; bins either side of the way out under a taped sign
                    int mid = across / 2;
                    for (int u = 0; u < across; u++)
                        for (int v = 0; v <= 1; v++)
                        {
                            var (p, q) = At(u, v);
                            ref Tile k = ref plan.At(p, q);
                            k.Detail = (byte)(k.Detail & L31HueMask | L31SubKitchen << L31SubShift);
                        }
                    for (int u = 2; u < across - 1; u++)
                    {
                        int r = (u + mid) % 5;
                        Put(u, 0, r switch { 0 => Props.Stove, 1 => Props.Fryer, 2 => Props.KitchenCounter, 3 => Props.Fryer, _ => Props.Fridge }, toNear, (byte)(r == 2 ? 1 : 0));
                    }
                    Sign(1, -1, L31Sign.StaffDoor, toNear);
                    for (int u = mid - 2; u <= mid + 2; u++) Sign(u, -1, L31Sign.Menu, toNear);
                    for (int u = 2; u <= across - 3; u++)
                        Put(u, 2, u == mid + 3 ? L31Props.Fountain : Props.SnackCounter, toNear, (byte)(u == mid + 3 ? 0 : u == 3 ? 1 : u % 4 == 1 ? 2 : 0));
                    Put(mid, 1, L31Props.StaffSpot, toNear, L31Server);
                    Put(2, 4, L31Props.Condiments, toHighU);
                    for (int v = 6; v <= len - 4; v += 4)
                        for (int u = 4; u <= across - 5; u += 5)
                        {
                            Put(u, v, L31Props.Table, toNear);
                            Put(u - 1, v, L31Props.Chair, toHighU);
                            Put(u + 1, v, L31Props.Chair, toLowU);
                            Put(u, v - 1, L31Props.Chair, toNear);
                            Put(u, v + 1, L31Props.Chair, toFar);
                        }
                    byte colour = (byte)(rng.Chance(0.5) ? 0 : 1);
                    for (int v = 5; v <= len - 3; v++)
                    {
                        // (clear of the side doors to the rental counter in the front band)
                        if (door == ArchPier.South && v is >= 7 and <= 10) continue;
                        Put(0, v, L31Props.ParkBench, toHighU, colour);
                        Put(across - 1, v, L31Props.ParkBench, toLowU, (byte)(1 - colour));
                    }
                    foreach (int u in new[] { doorU - 1, doorU + 2 })
                    {
                        Put(u, len - 1, L31Props.Bin, toFar);
                        Sign(u, len, L31Sign.Trash, toFar);
                    }
                    break;
                }
            case L31Zone.Rental:
                {
                    // Skate Rental (the front band only, its door to the south): cubbies of skates along the far wall, the
                    // counter across the room with the Coach behind it, benches to put skates on, the size chart and adverts
                    // for brands nobody has heard of on the blue walls
                    int mid = across / 2;
                    for (int u = 1; u < across - 1; u++) Put(u, 0, L31Props.SkateShelf, toNear);
                    for (int u = 2; u <= across - 3; u++) Put(u, 5, L31Props.Counter, toNear, (byte)(u == 2 ? 0 : u == across - 3 ? 2 : 1));
                    Put(mid, 3, L31Props.StaffSpot, toNear, L31Coach);
                    for (int u = 2; u <= across - 3; u += 2) Put(u, len - 4, Props.Bench, toFar);
                    for (int v = 12; v <= 13; v++)
                    {
                        var (cp, cq) = At(-1, v);
                        plan.At(cp, cq).Detail = (byte)(L31Wall.Chart << L31SubShift);
                    }
                    Sign(-1, 3, L31Sign.Advert, toHighU);
                    Sign(across, 3, L31Sign.Advert, toLowU);
                    Sign(across, 15, L31Sign.Advert, toLowU);
                    break;
                }
            case L31Zone.Arcade:
                {
                    // Rows of cabinets back to back, an aisle every seventh, pinball and claw machines at the ends, now and
                    // then an old 1980s box cabinet; skee-ball along a wall; the green-card dispenser at the way in; on half
                    // of them a handmade OUT OF ORDER sign either side of the door; in one in three, a white door marked 70
                    for (int qa = q0 + 3; qa + 1 <= q1 - 3; qa += 6)
                        for (int p = p0 + 4; p <= p1 - 3; p++)
                        {
                            int k = (p - p0) % 7;
                            if (k == 0) continue;
                            bool end = k is 1 or 6;
                            var (x, z) = plan.World(p, qa);
                            ulong c = Hashing.Hash(seed, x, z, SaltL31Room + 1);
                            bool retro = !end && Hashing.Unit(Hashing.Mix(c)) < 0.14;
                            ushort front = end ? ((c & 1) == 0 ? L31Props.Pinball : L31Props.Claw)
                                : retro ? L31Props.RetroCabinet : Hashing.Unit(c) < 0.1 ? L31Props.DeadCabinet : L31Props.Cabinet;
                            L31Put(plan, p, qa, front, ArchPier.North, (byte)(retro ? c % 3 : c % 6));
                            bool retro2 = !end && Hashing.Unit(Hashing.Mix(c ^ 0x3131)) < 0.14;
                            L31Put(plan, p, qa + 1, end ? L31Props.Pinball : retro2 ? L31Props.RetroCabinet : L31Props.Cabinet, ArchPier.South,
                                (byte)(retro2 ? c / 5 % 3 : c / 7 % 6));
                        }
                    for (int q = q0 + 2; q <= q1 - 2; q += 3)
                    {
                        L31Put(plan, p0, q, L31Props.SkeeTarget, ArchPier.East);
                        L31Put(plan, p0 + 1, q, L31Props.SkeeLane, ArchPier.East);
                    }
                    L31Put(plan, p1, q0 + 2, L31Props.PrizeCounter, ArchPier.West);
                    L31Put(plan, p1, q0 + 3, L31Props.PrizeCounter, ArchPier.West);
                    Put(doorU - 1, len - 1, L31Props.CardDispenser, toFar);
                    // (the front band's arcade has a second door onto the hall, p 97-99, with its own dispenser)
                    if (door == ArchPier.South && p0 == 76) L31Put(plan, 96, 0, L31Props.CardDispenser, ArchPier.South);
                    if (rng.Chance(0.5))
                        foreach (int u in new[] { doorU - 1, doorU + 2 }) Sign(u, len, L31Sign.OutOfOrder, toNear);
                    if (rng.Chance(1 / 3.0)) L31SignOn(plan, p1 + 1, Math.Max(q0 + 6, q1 - 4), L31Sign.Door70, ArchPier.West);
                    break;
                }
            case L31Zone.Cinema:
                {
                    // Dark and small (Wikidot): one big TV on the far wall, three rows of single continuous metal benches in
                    // front of it, each a step higher than the last, and steps down again behind them to the door
                    int mid = across / 2;
                    ArchPier tvFacing = plan.Dir(toNear);
                    for (int c = -1; c <= 1; c++)
                    {
                        // (the TV's columns go from the viewer's left: looking north, west is left; looking south, east is)
                        byte col = (byte)(tvFacing == ArchPier.South ? c + 1 : 1 - c);
                        Put(mid + c, 0, L31Props.Tv, toNear, col);
                    }
                    for (int v = 0; v < len; v++)
                    {
                        int step = v < 6 ? 0 : v < 8 ? 1 : v < 10 ? 2 : v < 12 ? 3 : v == 12 ? 2 : v == 13 ? 1 : 0;
                        if (step == 0) continue;
                        for (int u = 0; u < across; u++)
                        {
                            var (p, q) = At(u, v);
                            ref Tile c = ref plan.At(p, q);
                            if (c.Kind == TileKind.Floor) c.Detail = (byte)(c.Detail & L31HueMask | step << L31SubShift);
                        }
                    }
                    foreach (int v in new[] { 7, 9, 11 })
                        for (int u = 1; u < across - 1; u++) Put(u, v, L31Props.CinemaBench, toFar);
                    break;
                }
            case L31Zone.Bath:
                // Toilets along one long wall, sinks along the other
                if (wide)
                    for (int p = p0 + 1; p <= p1 - 1; p += 2)
                    {
                        L31Put(plan, p, q1, Props.Toilet, ArchPier.North);
                        if (p % 4 == 1) L31Put(plan, p, q0 + 2, Props.KitchenCounter, ArchPier.South, 1);
                    }
                else
                    for (int q = q0 + 1; q <= q1 - 1; q += 2)
                    {
                        L31Put(plan, door == ArchPier.West ? p1 : p0, q, Props.Toilet, door == ArchPier.West ? ArchPier.West : ArchPier.East);
                        if (q % 4 == 1) L31Put(plan, door == ArchPier.West ? p0 + 2 : p1 - 2, q, Props.KitchenCounter, door == ArchPier.West ? ArchPier.East : ArchPier.West, 1);
                    }
                break;
            case L31Zone.Hvac:
                {
                    // Ducting and machinery, a fan, boxes, dead radiators, a pipe run along the far wall; the cold leaks in
                    // (8 C) and one in three is flooded where its pipes burst (Fandom); puddles elsewhere
                    for (int k = rng.Range(3, 6); k > 0; k--)
                    {
                        int p = rng.Range(p0 + 2, p1 - 2), q = rng.Range(q0 + 2, q1 - 2);
                        double r = rng.NextDouble();
                        L31Put(plan, p, q, r < 0.4 ? Props.PipeStack : r < 0.6 ? Props.Generator : r < 0.8 ? Props.FloorFan : Props.CardboardBoxes,
                            (ArchPier)rng.Range(0, 3));
                    }
                    for (int v = 2; v < len - 2; v += 3) Put(0, v, Props.Radiator, toHighU);
                    bool alongP = door is ArchPier.North or ArchPier.South;
                    for (int u = 0; u < across; u++)
                    {
                        var (p, q) = At(u, 0);
                        ref Tile t = ref plan.At(p, q);
                        if (t.Kind == TileKind.Floor) t.Detail = (byte)(t.Detail & L31HueMask | (alongP ? L31PipeX : L31PipeZ) << L31SubShift);
                    }
                    if (rng.Chance(1 / 3.0))
                        for (int v = 2; v <= len - 3; v++)
                            for (int u = 1; u <= across - 2; u++)
                            {
                                var (p, q) = At(u, v);
                                ref Tile t = ref plan.At(p, q);
                                if (t.Kind != TileKind.Floor) continue;
                                t.Variant = 0;
                                t.Detail = (byte)(t.Detail & L31HueMask | L31SubFlood << L31SubShift);
                            }
                    if (rng.Chance(0.3)) Box(across - 1, 1);
                    break;
                }
            case L31Zone.Store:
                for (int i = 2; wide ? i <= w - 3 : i <= d - 3; i++)
                {
                    if (rng.Chance(0.8)) { if (wide) L31Put(plan, p0 + i, q0, Props.Shelf, ArchPier.North); else L31Put(plan, p0, q0 + i, Props.Shelf, ArchPier.West); }
                    if (rng.Chance(0.8)) { if (wide) L31Put(plan, p0 + i, q1, Props.Shelf, ArchPier.South); else L31Put(plan, p1, q0 + i, Props.Shelf, ArchPier.East); }
                }
                for (int k = rng.Range(1, 3); k > 0; k--) L31Put(plan, rng.Range(p0 + 3, p1 - 3), rng.Range(q0 + 3, q1 - 3), Props.CardboardBoxes, ArchPier.North);
                // What the rink's staff kept back: a supply box or two
                for (int k = rng.Range(0, 2); k > 0; k--) Box(rng.Range(2, across - 3), rng.Range(2, len - 3));
                break;
            case L31Zone.Lounge:
                {
                    // The Employees Lounge (Fandom): exposed brick, grey carpet, lockers along a wall, a kitchenette, a table,
                    // the CCTV desk and cameras in the corners, a custodian's corner; silent
                    for (int v = 1; v <= len - 2; v++)
                    {
                        var (lp, lq) = At(-1, v);
                        ref Tile wall = ref plan.At(lp, lq);
                        if (wall.Kind != TileKind.Wall) continue;
                        wall.Detail = (byte)(L31Wall.Locker << L31SubShift);
                        wall.Pier = plan.Dir(toHighU);
                    }
                    Put(across - 1, 0, Props.Fridge, toNear);
                    Put(across - 2, 0, Props.KitchenCounter, toNear, 1);
                    Put(across - 3, 0, Props.KitchenCounter, toNear);
                    Put(0, 0, L31Props.Monitors, toNear);
                    Put(across / 2, len / 2, Props.CafeTable, toNear);
                    Put(across / 2 - 1, len / 2, Props.CafeChair, toHighU);
                    Put(across / 2 + 1, len / 2, Props.CafeChair, toLowU);
                    Put(across - 1, len - 2, Props.Shelf, toLowU);
                    Put(across - 2, len - 2, Props.WetFloorSign, toNear);
                    Put(across - 1, len - 3, Props.CardboardBoxes, toNear);
                    if (rng.Chance(0.4)) Box(across - 2, len - 3);
                    foreach (var (u, v, look) in new[] { (across - 1, 1, toNear), (0, len - 2, toFar) })
                    {
                        var (cp, cq) = At(u, v);
                        ref Tile cam = ref plan.At(cp, cq);
                        cam.Overhead = L31Overhead.Cctv;
                        if (cam.Variant == 0) cam.Pier = plan.Dir(look);
                    }
                    break;
                }
        }
    }

    /// <summary>Pins a sign (<see cref="L31Sign"/>) to the face of a wall that looks <paramref name="face"/> (in the plan's terms).</summary>
    private static void L31SignOn(L31Plan plan, int p, int q, byte sign, ArchPier face)
    {
        if (p < -1 || q < -1 || p > L31Size || q > L31Size) return;
        ref Tile t = ref plan.At(p, q);
        if (t.Kind != TileKind.Wall) return;
        t.Detail = (byte)(t.Detail & ~L31HueMask & ~L31MirrorBit | sign);
        t.Pier = plan.Dir(face);
    }

    private static ArchPier L31Opposite(ArchPier d) => d switch
    {
        ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East,
    };

    /// <summary>The rink hall: the skirt, the oval of boards inside the barrier, benches and the DJ booth, lights, the ball.</summary>
    private void L31LayRink(L31Plan plan)
    {
        bool tiny = plan.Tiny;
        int air = L31Air(L31Zone.Rink, tiny);
        const int r0 = 18, r1 = 102, s0 = 26, s1 = 94;
        int inset = tiny ? 12 : 6, radius = tiny ? 8 : 12;
        int o0 = r0 + inset, o1 = r1 - inset, oq0 = s0 + inset, oq1 = s1 - inset;
        int pc = (r0 + r1) / 2, qc = (s0 + s1) / 2;
        var room = new L31Room { P0 = r0, Q0 = s0, P1 = r1, Q1 = s1, Kind = L31Zone.Rink, Doors = 4 };
        plan.Rooms.Add(room);
        // Inside the oval: a rounded rectangle, its corners turned with the radius
        bool InOval(int p, int q, int shrink)
        {
            int a0 = o0 + shrink, a1 = o1 - shrink, b0 = oq0 + shrink, b1 = oq1 - shrink, rr = Math.Max(1, radius - shrink);
            if (p < a0 || p > a1 || q < b0 || q > b1) return false;
            int dx = p < a0 + rr ? a0 + rr - p : p > a1 - rr ? p - (a1 - rr) : 0;
            int dz = q < b0 + rr ? b0 + rr - q : q > b1 - rr ? q - (b1 - rr) : 0;
            return dx * dx + dz * dz <= rr * rr;
        }
        static bool InGap(int p) => p is >= 40 and <= 42 or >= 78 and <= 80;
        for (int q = s0; q <= s1; q++)
            for (int p = r0; p <= r1; p++)
            {
                bool rink = InOval(p, q, 0);
                L31Open(ref plan.At(p, q), rink ? L31Zone.Rink : L31Zone.Skirt, air, L31Hue.White);
                if (!rink) continue;
                ref Tile t = ref plan.At(p, q);
                bool edge = !InOval(p - 1, q, 0) || !InOval(p + 1, q, 0) || !InOval(p, q - 1, 0) || !InOval(p, q + 1, 0);
                if (edge && !InGap(p)) { t.Variant = L31Props.Dasher; continue; }
                // (in a gap, a short wooden gate with flaps: Wikidot)
                if (edge) { t.Variant = L31Props.Gate; t.Stack = (byte)(plan.AlongPIsX ? 0 : 1); }
                // The lane line round the inside, along the straights; the centre circle
                int dpc = p - pc, dqc = q - qc;
                byte sub = L31BoardPlain;
                if (dpc * dpc + dqc * dqc <= (tiny ? 9 : 36)) sub = L31BoardCentre;
                else if (!tiny && (q == oq0 + 9 || q == oq1 - 9) && p >= o0 + radius && p <= o1 - radius) sub = plan.AlongPIsX ? L31BoardStripeWE : L31BoardStripeNS;
                else if (!tiny && (p == o0 + 9 || p == o1 - 9) && q >= oq0 + radius && q <= oq1 - radius) sub = plan.AlongPIsX ? L31BoardStripeNS : L31BoardStripeWE;
                t.Detail = (byte)(L31Hue.White | sub << L31SubShift);
            }
        // Doors from the corridor
        foreach (int p in new[] { 36, 37, 38, 82, 83, 84 }) L31Door(ref plan.At(p, s0 - 1), L31Zone.Skirt);
        for (int p = 59; p <= 61; p++) L31Door(ref plan.At(p, s1 + 1), L31Zone.Skirt);
        for (int q = 58; q <= 60; q++)
        {
            L31Door(ref plan.At(r0 - 1, q), L31Zone.Skirt);
            L31Door(ref plan.At(r1 + 1, q), L31Zone.Skirt);
        }

        // Lights: rings of coloured tubes over the boards, white panels over the skirt, the disco ball in the middle
        for (int q = s0; q <= s1; q++)
            for (int p = r0; p <= r1; p++)
            {
                ref Tile t = ref plan.At(p, q);
                // (two rings: one just inside the barrier, one further in, so the middle of the boards is not left dark)
                int inner = tiny ? 12 : 16;
                bool ring = InOval(p, q, 4) && !InOval(p, q, 5) || InOval(p, q, inner) && !InOval(p, q, inner + 1);
                if (ring && Hashing.Mod(p + q, 4) == 0)
                {
                    int k = (p + q) / 4;
                    t.Detail = (byte)(t.Detail & ~L31HueMask | k % 5);
                    t.Ceiling = L31Light(plan, p, q, true); // (all of them give light: the rink is tall and wide)
                }
                bool skirtLine = (q == s0 + 3 || q == s1 - 3) && Hashing.Mod(p, 6) == 3 || (p == r0 + 3 || p == r1 - 3) && Hashing.Mod(q, 6) == 3;
                if (skirtLine && t.Zone == (byte)L31Zone.Skirt) t.Ceiling = L31Light(plan, p, q, true);
            }
        // The star-shaped fixture at the rink's centre (Wikidot), three blocks across under the ceiling
        plan.At(pc, qc).Overhead = L31Overhead.Star;

        // The DJ station on the south side of the rink (Wikidot): turntables and the mixer facing the boards, a speaker
        // either end, two more against the wall behind, and the DJ (a Faceling) between desk and wall
        bool southIsS1 = !plan.Mirror;
        int south = southIsS1 ? s1 : s0, north = southIsS1 ? s0 : s1, inward = southIsS1 ? -1 : 1;
        ArchPier toRink = southIsS1 ? ArchPier.North : ArchPier.South, toWall = L31Opposite(toRink);
        int desk = south + 3 * inward;
        L31Put(plan, pc - 2, desk, L31Props.Speaker, toRink);
        L31Put(plan, pc - 1, desk, L31Props.DjDesk, toRink, 0);
        L31Put(plan, pc, desk, L31Props.DjDesk, toRink, 1);
        L31Put(plan, pc + 1, desk, L31Props.DjDesk, toRink, 0);
        L31Put(plan, pc + 2, desk, L31Props.Speaker, toRink);
        L31Put(plan, pc, desk - inward, L31Props.StaffSpot, toRink, L31Dj);
        L31Put(plan, pc - 3, south, L31Props.Speaker, toRink);
        L31Put(plan, pc + 3, south, L31Props.Speaker, toRink);
        // Benches along the skirt by the walls, facing the rink, clear of the doors and the DJ station
        bool ClearOfDoors(int p, int wallQ) => plan.At(p - 1, wallQ).Kind != TileKind.Doorway && plan.At(p, wallQ).Kind != TileKind.Doorway
            && plan.At(p + 1, wallQ).Kind != TileKind.Doorway;
        for (int p = r0 + 4; p <= r1 - 4; p += 3)
            if (ClearOfDoors(p, north + inward)) L31Put(plan, p, north, Props.Bench, toWall);
        for (int p = r0 + 6; p <= r1 - 6; p += 4)
            if (Math.Abs(p - pc) > 7 && ClearOfDoors(p, south - inward)) L31Put(plan, p, south, Props.Bench, toRink);

        // The walls round the skirt, above the benches: each side clad, by hash, in the mural or in black lacquer with
        // chrome-framed mirrors, as the halls are (the generator finds the wall beside the tile; doors are left bare)
        ulong clad = Hashing.Hash(seed, plan.Wx, plan.Wz, SaltL31Clad + 8);
        for (int q = s0; q <= s1; q++)
            for (int p = r0; p <= r1; p++)
            {
                int side = q == s0 ? 0 : q == s1 ? 1 : p == r0 ? 2 : p == r1 ? 3 : -1;
                if (side < 0) continue;
                var (wp, wq) = side switch { 0 => (p, q - 1), 1 => (p, q + 1), 2 => (p - 1, q), _ => (p + 1, q) };
                if (plan.At(wp, wq).Kind != TileKind.Wall) continue;
                plan.At(p, q).Overhead = (clad >> side & 1) == 0 ? L31Overhead.Mural : L31Overhead.Mirrors;
            }
    }

    /// <summary>An emptiness: one dim bare room the size of the complex, pillars in a grid, a door in the middle of each side.</summary>
    private void L31LayEmpty(L31Plan plan, bool carpet)
    {
        L31Zone zone = carpet ? L31Zone.CarpetRoom : L31Zone.Empty;
        plan.Rooms.Add(new L31Room { P0 = 0, Q0 = 0, P1 = L31Size - 1, Q1 = L31Size - 1, Kind = zone, Doors = 4 });
        for (int q = 0; q < L31Size; q++)
            for (int p = 0; p < L31Size; p++)
            {
                ref Tile t = ref plan.At(p, q);
                if (p % 12 == 6 && q % 12 == 6)
                {
                    t.Detail = (byte)(L31Wall.Concrete << L31SubShift);
                    continue;
                }
                L31Open(ref t, zone, 4, L31Hue.Fluorescent);
                if (!carpet && p % 8 == 4 && q % 8 == 4) t.Ceiling = L31Light(plan, p, q, true, 0.75, 0.12);
            }
        for (int i = 58; i <= 62; i++)
        {
            L31Door(ref plan.At(i, -1), zone);
            L31Door(ref plan.At(i, L31Size), zone);
            L31Door(ref plan.At(-1, i), zone);
            L31Door(ref plan.At(L31Size, i), zone);
        }
    }

    /// <summary>Walls are dressed as high as the tallest air beside them, and faced with the material of the most telling room.</summary>
    private static void L31DressWalls(L31Plan plan)
    {
        static int Rank(byte zone) => zone switch
        {
            (byte)L31Zone.Rink or (byte)L31Zone.Skirt => 6,
            (byte)L31Zone.Rental => 5,
            (byte)L31Zone.Bath => 4,
            (byte)L31Zone.Arcade or (byte)L31Zone.Cinema => 3,
            (byte)L31Zone.Lounge => 2,
            (byte)L31Zone.Corridor or (byte)L31Zone.Hvac or (byte)L31Zone.Store or (byte)L31Zone.Empty or (byte)L31Zone.CarpetRoom or (byte)L31Zone.Wall or 0 => 0,
            _ => 1,
        };
        static byte Material(int rank) => rank switch
        {
            5 => L31Wall.Blue,
            4 => L31Wall.Glazed,
            3 => L31Wall.Dark,
            2 => L31Wall.Brick,
            0 => L31Wall.Concrete,
            _ => L31Wall.Skate,
        };
        for (int b = -1; b <= L31Size; b++)
            for (int a = -1; a <= L31Size; a++)
            {
                ref Tile t = ref plan.AtAB(a, b);
                if (!t.IsWallLike) continue;
                bool outer = a == -1 || b == -1 || a == L31Size || b == L31Size;
                int height = outer ? 5 : 4, rank = outer ? 1 : 0;
                for (int dz = -1; dz <= 1; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        int x = a + dx, z = b + dz;
                        if (x < -1 || z < -1 || x > L31Size || z > L31Size) continue;
                        ref Tile n = ref plan.AtAB(x, z);
                        if (n.IsWallLike) continue;
                        height = Math.Max(height, n.Height);
                        rank = Math.Max(rank, Rank(n.Zone));
                    }
                t.Height = (byte)height;
                if (t.Kind != TileKind.Wall) continue;
                // A chart or the lockers laid out by a room stay as they are; an emptiness's pillars too; the mirror bit and a sign stay
                byte sub = (byte)((t.Detail & L31SubMask) >> L31SubShift);
                if (sub is L31Wall.Chart or L31Wall.Locker) continue;
                t.Detail = (byte)(t.Detail & (L31MirrorBit | L31HueMask) | Material(rank) << L31SubShift);
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L31First"/>-<see cref="Props.L31Last"/>) people walk through: the rink's gates, and where the staff stand.</summary>
    private static bool L31WalkThrough(ushort variant) => variant is L31Props.Gate or L31Props.StaffSpot;

    // ================= Air =================

    /// <summary>The temperature: 12 C (the plan's; <see cref="LevelTemperatures"/> keeps the scaffold's 16 for now), 8 C in the HVAC rooms where the cold leaks in.</summary>
    private float L31Temperature(int x, int y, int z, int floorY) => TileAt(x, z).Zone == (byte)L31Zone.Hvac ? 8f : 12f;

    /// <summary>Reality stability: a little steadier than neutral everywhere; the rink is a safe place.</summary>
    private float L31Stability(double x, double y, double z, int floorY, float drift) => 1.1f;
}
