using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 31, "Roller Rink" (experimental): kept as level 24 (<see cref="Level31"/>) and shown as "31". An endless 1990s
/// roller rink, the same for everyone in the world, in a round noclip region far out to the west-north-west (the design is
/// docs/design/experimental-levels/31-plan.md). Its ways in and out are in WorldLayout.Level31.Links.cs.
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
        /// <summary>A lit sign on the wall a tile stands against (toward its Pier; round a rink, away from the wall beside it):
        /// round a rink, a column of the DJ station's neon sign (Detail's sub-kind 1-3, from the viewer's left; the rest of
        /// the wall clad in the mural); in a cinema, its EXIT sign over the door, or with the rail bit a small TV on a side
        /// wall (rel 4). (Never Stack: a tile with a Stack and no prop counts as blocked.)</summary>
        public const byte Sign = 149;
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
        /// <summary>Round 3's set pieces: a toilet stall (two blocks tall), a washroom vanity (its mirror a wall mount over it), an
        /// arcade photo booth (two tall), a jukebox, a trophy case (two tall), the cinema TV's cabinet, Level Fun's popcorn
        /// machine, Level 3999's prize case (Stack 1-4: a plush on it, Level 3999's kinds) and prize wall.</summary>
        public const ushort Stall = 729, Vanity = 730, PhotoBooth = 731, Jukebox = 732, TrophyCase = 733, MediaCab = 734, Popcorn = 735,
            PrizeCase = 736, PrizeWall = 737;
        /// <summary>Round 4: an air handler (Level 120's CRAC unit, two high with its duct up to the ceiling), a slushie machine on
        /// its cabinet.</summary>
        public const ushort AirHandler = 738, Slushie = 739;
        /// <summary>Round 4: a queue post (Level 36's stanchion; Stack 0 no belt, 1 a belt toward its Pier).</summary>
        public const ushort Stanchion = 740;
    }

    /// <summary>
    /// The wall mounts (round 3; tools/gen_31_round3.py's SIGNS, the same names, columns and rows): signs and fittings on the
    /// wall a floor tile stands against (or hung over it), at their own height: <c>Top</c> is the rel of the top row, 0 for
    /// just under the ceiling. A tile carries one column of one (<see cref="Tile.Pipe"/> = <see cref="Pipes.L31Mount"/> plus
    /// the way it faces, <see cref="Tile.Depth"/> the column's index in <see cref="L31MountParts"/>); a doorway's tile carries
    /// one for the hall tile in front of it.
    /// </summary>
    public static readonly (string Name, int Cols, int Rows, int Top)[] L31Mounts =
    {
        ("rent", 2, 1, 0), ("snack", 2, 1, 0), ("arc", 2, 1, 0), ("rest", 2, 1, 0), ("cine", 2, 1, 0), ("staff", 2, 1, 0),
        ("store", 2, 1, 0), ("mech", 2, 1, 0), ("exit", 1, 1, 0), ("rentbig", 3, 1, 0), ("sz0", 1, 1, 2), ("sz1", 1, 1, 2),
        ("sz2", 1, 1, 2), ("sz3", 1, 1, 2), ("wb", 2, 1, 2), ("snackbig", 3, 1, 0), ("prizes", 2, 1, 0), ("tokens", 1, 1, 2),
        ("name", 5, 1, 0), ("arcbig", 3, 1, 0), ("rules", 2, 2, 3), ("norun", 1, 1, 2), ("session", 2, 1, 4), ("snackwin", 2, 2, 4),
        ("admit", 3, 1, 0), ("mw", 1, 1, 2), ("mirror", 1, 1, 2), ("dryer", 1, 1, 2), ("ext", 1, 1, 2), ("alarm", 1, 1, 2),
        ("poster0", 1, 1, 2), ("poster1", 1, 1, 2), ("poster2", 1, 1, 2), ("poster3", 1, 1, 2), ("nowshow", 1, 2, 3),
        ("board", 2, 1, 2), ("bigtv", 5, 3, 5), ("hours", 1, 2, 3), ("rev9", 3, 1, 0), ("rev10", 3, 1, 0),
        ("rev11", 3, 1, 0),
    };

    /// <summary>Every column of every mount, by <see cref="Tile.Depth"/>: which mount and which column (0 the viewer's left).</summary>
    public static readonly (int Mount, int Col)[] L31MountParts = L31MakeMountParts();

    private static (int, int)[] L31MakeMountParts()
    {
        var parts = new List<(int, int)>();
        for (int m = 0; m < L31Mounts.Length; m++)
            for (int c = 0; c < L31Mounts[m].Cols; c++) parts.Add((m, c));
        return parts.ToArray();
    }

    private static int L31MountDepth(string name, int col)
    {
        for (int i = 0; i < L31MountParts.Length; i++)
            if (L31Mounts[L31MountParts[i].Mount].Name == name && L31MountParts[i].Col == col) return i;
        return -1;
    }

    /// <summary>Whether a tile carries a wall mount.</summary>
    public static bool L31HasMount(in Tile t) => t.Pipe is >= Pipes.L31Mount and <= Pipes.L31Mount + 3;

    private static int L31FacingIndex(ArchPier d) => d switch { ArchPier.North => 0, ArchPier.East => 1, ArchPier.South => 2, _ => 3 };

    /// <summary>
    /// Puts a mount along a straight run of tiles (A to B, as long as the mount is wide), facing <paramref name="face"/> (the
    /// plan's terms), its columns from the viewer's left; nothing if a tile of the run is not open floor (or, with
    /// <paramref name="doorways"/>, a doorway) or carries one already.
    /// </summary>
    private static bool L31MountRun(L31Plan plan, int pa, int qa, int pb, int qb, string name, ArchPier face, bool doorways = false)
    {
        int m = Array.FindIndex(L31Mounts, k => k.Name == name);
        if (m < 0) return false;
        int n = Math.Max(Math.Abs(pb - pa), Math.Abs(qb - qa)) + 1;
        if (n != L31Mounts[m].Cols || pa != pb && qa != qb) return false;
        int dp = Math.Sign(pb - pa), dq = Math.Sign(qb - qa);
        ArchPier world = plan.Dir(face);
        int xmin = int.MaxValue, xmax = int.MinValue, zmin = int.MaxValue, zmax = int.MinValue;
        for (int i = 0; i < n; i++)
        {
            int p = pa + i * dp, q = qa + i * dq;
            if (p < -1 || q < -1 || p > L31Size || q > L31Size) return false;
            ref Tile t = ref plan.At(p, q);
            if (!(t.Kind == TileKind.Floor || doorways && (t.Kind == TileKind.Doorway || t.Under == Unders.L31Revolving)) || L31HasMount(t)) return false;
            var (x, z) = plan.World(p, q);
            xmin = Math.Min(xmin, x); xmax = Math.Max(xmax, x); zmin = Math.Min(zmin, z); zmax = Math.Max(zmax, z);
        }
        for (int i = 0; i < n; i++)
        {
            int p = pa + i * dp, q = qa + i * dq;
            var (x, z) = plan.World(p, q);
            int col = world switch { ArchPier.North => xmax - x, ArchPier.South => x - xmin, ArchPier.East => zmax - z, _ => z - zmin };
            ref Tile t = ref plan.At(p, q);
            t.Pipe = (ushort)(Pipes.L31Mount + L31FacingIndex(world));
            t.Depth = (byte)L31MountDepth(name, col);
        }
        return true;
    }

    /// <summary>A mount centred on a tile (the left of the two middle ones for an even width), its run along P or Q.</summary>
    private static bool L31MountAt(L31Plan plan, int p, int q, bool alongP, string name, ArchPier face)
    {
        int m = Array.FindIndex(L31Mounts, k => k.Name == name);
        if (m < 0) return false;
        int a = -(L31Mounts[m].Cols - 1) / 2, b = a + L31Mounts[m].Cols - 1;
        return alongP ? L31MountRun(plan, p + a, q, p + b, q, name, face) : L31MountRun(plan, p, q + a, p, q + b, name, face);
    }

    /// <summary>The staff a <see cref="L31Props.StaffSpot"/> is for.</summary>
    public const byte L31Coach = 0, L31Server = 1, L31Dj = 2;

    public enum L31Kind : byte { Rinks, Empty }

    /// <summary>A room of a complex, in the plan's own coordinates (inclusive, the inside only).</summary>
    public sealed class L31Room
    {
        public int P0, Q0, P1, Q1, Doors;
        public L31Zone Kind;
        /// <summary>The first of its door's two doorway tiles, and the side of the room it is on (round 3: its sign outside).</summary>
        public int DoorP = -9, DoorQ = -9;
        public ArchPier DoorSide;
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
        Tile wall = L31PlanTile(bx, bz);
        // (a revolving door stands out into the hall like a doorway's opening: no strip, the cladding above it)
        TileKind behind = wall.Under == Unders.L31Revolving ? TileKind.Doorway : wall.Kind;
        if (behind is not (TileKind.Wall or TileKind.Doorway)) return;
        ArchPier facing = hallX ? (u == 1 ? ArchPier.East : ArchPier.West) : (v == 1 ? ArchPier.South : ArchPier.North);
        t.Pier = facing;
        // The wall above the neon strip: each side of each stretch is clad in the mural (three in five) or in black lacquer
        // with chrome-framed mirrors ("many chambers of shiny surfaces": Wikidot)
        ulong clad = Hashing.Hash(seed, Hashing.FloorDiv(gx, L31Period), Hashing.FloorDiv(gz, L31Period), SaltL31Clad + (ulong)facing);
        t.Overhead = Hashing.Unit(clad) < 0.6 ? L31Overhead.Mural : L31Overhead.Mirrors;
        // (over a doorway the cladding starts above the opening, and there is no strip; a sign the plan hangs over the doorway
        // on the hall's side, the rink's name over a lobby's front doors, is drawn from this tile)
        if (behind == TileKind.Doorway && L31HasMount(wall))
        {
            t.Pipe = wall.Pipe;
            t.Depth = wall.Depth;
        }
        if (behind == TileKind.Doorway) return;
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
            L31LaySigns(plan);
        }
        L31DressWalls(plan);
        // The lobby's wooden door, and now and then a revolving door (WorldLayout.Level31.Links.cs)
        L31LayLinks(plan);
        // (round 3) Where a revolving door goes, on a screen over it on the hall's side and over it inside the lobby, as
        // Level 36's gate screens (the door's way is the Links code's, read here)
        if (plan.At(L31RevolvingP, L31RevolvingQ).Under == Unders.L31Revolving)
        {
            var (mx, mz) = plan.World(L31RevolvingP, L31RevolvingQ);
            string sign = "rev" + L31RevolvingTarget(mx, mz);
            L31MountRun(plan, L31RevolvingP - 1, L31RevolvingQ, L31RevolvingP + 1, L31RevolvingQ, sign, ArchPier.North, doorways: true);
            L31MountRun(plan, L31RevolvingP - 1, L31RevolvingQ + 1, L31RevolvingP + 1, L31RevolvingQ + 1, sign, ArchPier.South);
        }
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
        (room.DoorP, room.DoorQ, room.DoorSide) = (doorP, doorQ, door);

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
                // (round 3) The waiting corner's trophy cases and jukebox on the west wall; ADMISSION hung over the counter;
                // EXIT over the front doors inside; the rink's events on the back wall
                L31Put(plan, 46, 3, L31Props.TrophyCase, ArchPier.East);
                L31Put(plan, 46, 4, L31Props.TrophyCase, ArchPier.East);
                L31Put(plan, 46, 14, L31Props.Jukebox, ArchPier.East);
                L31MountRun(plan, 53, 12, 51, 12, "admit", ArchPier.North);
                L31MountRun(plan, 60, 0, 60, 0, "exit", ArchPier.South);
                L31MountRun(plan, 55, 0, 55, 0, "hours", ArchPier.South);
                for (int k = 0; k < 3; k++) L31MountRun(plan, 53 + 4 * k, 19, 53 + 4 * k, 19, "poster" + (k + wx0 + wz0 & 3), ArchPier.North);
                for (int q = 2; q <= 16; q++)
                {
                    ref Tile wall = ref plan.At(75, q);
                    if (wall.Kind != TileKind.Wall) continue;
                    wall.Detail = (byte)(L31Wall.Locker << L31SubShift);
                    wall.Pier = plan.Dir(ArchPier.West);
                }
                for (int p = 50; p <= 51; p++) plan.At(p, 20).Detail = (byte)(L31Wall.Chart << L31SubShift);
                // The lobby's walls in the halls' mural, above the skirting, but for the lockers and the size chart
                for (int q = 0; q <= 19; q++)
                    for (int p = 46; p <= 74; p++)
                    {
                        if (p is not (46 or 74) && q is not (0 or 19)) continue;
                        ref Tile t = ref plan.At(p, q);
                        if (t.Kind != TileKind.Floor || t.Variant != 0) continue;
                        bool bare = false;
                        foreach (var (wp, wq) in new[] { (p, q - 1), (p, q + 1), (p - 1, q), (p + 1, q) })
                        {
                            ref Tile nb = ref plan.At(wp, wq);
                            if (nb.Kind is not (TileKind.Wall or TileKind.Doorway)) continue;
                            byte sub = (byte)((nb.Detail & L31SubMask) >> L31SubShift);
                            bare = sub is not (L31Wall.Locker or L31Wall.Chart);
                            if (!bare) break;
                        }
                        if (bare) t.Overhead = L31Overhead.Mural;
                    }
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
                        Put(u, 2, u == mid + 3 ? L31Props.Fountain : u == mid - 3 && u > 3 ? L31Props.Slushie : Props.SnackCounter, toNear,
                            (byte)(u == mid + 3 ? 0 : u == 3 ? 1 : u % 4 == 1 ? 2 : 0));
                    Put(mid, 1, L31Props.StaffSpot, toNear, L31Server);
                    Put(2, 4, L31Props.Condiments, toHighU);
                    // (round 3) The popcorn machine at the counter's end, a drinks fridge at the other, a second condiment
                    // stand; the lit SNACK BAR sign over the menus
                    Put(across - 2, 2, L31Props.Popcorn, toNear);
                    Put(0, 2, Props.DrinkFridge, toNear);
                    Put(across - 3, 4, L31Props.Condiments, toLowU);
                    Put(1, len - 2, L31Props.Jukebox, toHighU);
                    {
                        var (sa, sq) = At(mid - 1, 0);
                        var (sb, sr) = At(mid + 1, 0);
                        L31MountRun(plan, sa, sq, sb, sr, "snackbig", toNear);
                    }
                    // Tables in groups either side of a clear walk from the door to the till
                    foreach (int v in len >= 19 ? new[] { 6, 10, 14, 17 } : new[] { 6, 10, 14 })
                        foreach (int u in new[] { doorU - 4, doorU - 9, doorU + 5, doorU + 10 })
                        {
                            if (v > len - 3 || u < 3 || u > across - 4) continue;
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
                    // Posters over the benches on the side walls (clear of the side doors in the front band)
                    for (int v = 6; v <= len - 4; v += 6)
                    {
                        if (door == ArchPier.South && v is >= 7 and <= 10) continue;
                        var (lp, lq) = At(0, v);
                        L31MountRun(plan, lp, lq, lp, lq, "poster" + (v / 6 + mid & 3), toHighU);
                        var (rp, rq) = At(across - 1, v);
                        L31MountRun(plan, rp, rq, rp, rq, "poster" + (v / 6 + mid + 2 & 3), toLowU);
                    }
                    break;
                }
            case L31Zone.Rental:
                {
                    // Skate Rental (the front band only, its door to the south): cubbies of skates along the far wall, the
                    // counter across the room with the Coach behind it, benches to put skates on, the size chart and adverts
                    // for brands nobody has heard of on the blue walls
                    // (round 3, as a real rental: the wall of cubbies under its size boards, a free-standing rack in front of
                    // it, the Coach between them and the counter, SKATE RENTAL lit over the wall, his whiteboard on the side
                    // wall; the customers' side with back-to-back shoe benches either side of the walk from the door and coin
                    // lockers along the lobby wall)
                    int mid = across / 2;
                    for (int u = 1; u < across - 1; u++) Put(u, 0, L31Props.SkateShelf, toNear);
                    for (int u = 3; u <= across - 4; u++) Put(u, 2, L31Props.SkateShelf, toNear);
                    for (int u = 2; u <= across - 3; u++) Put(u, 5, L31Props.Counter, toNear, (byte)(u == 2 ? 0 : u == across - 3 ? 2 : 1));
                    Put(mid, 4, L31Props.StaffSpot, toNear, L31Coach);
                    // (round 4) Queue posts with their belts across the customers' side, either side of the walk to the counter
                    for (int u = 3; u <= across - 4; u++)
                    {
                        if (u >= mid - 1 && u <= mid + 1) continue;
                        bool last = u == mid - 2 || u == across - 4;
                        Put(u, 8, L31Props.Stanchion, toHighU, (byte)(last ? 0 : 1));
                    }
                    void MountHere(int ua, int ub, int v, string name, ArchPier face)
                    {
                        var (pa, qa) = At(ua, v);
                        var (pb, qb) = At(ub, v);
                        L31MountRun(plan, pa, qa, pb, qb, name, face);
                    }
                    MountHere(mid - 1, mid + 1, 0, "rentbig", toNear);
                    // (kids' sizes at the viewer's left: looking south, that is the east, the high-U end)
                    bool rev = plan.Dir(toNear) == ArchPier.North;
                    for (int k = 0; k < 4; k++)
                    {
                        int u = k < 2 ? 2 + 3 * k : across - 3 - 3 * (3 - k);
                        MountHere(u, u, 0, "sz" + (rev ? 3 - k : k), toNear);
                    }
                    {
                        var (wa, wb) = At(0, 3);
                        var (wc, wd) = At(0, 4);
                        L31MountRun(plan, wa, wb, wc, wd, "wb", toHighU);
                    }
                    foreach (int v in new[] { 11, 12, 15, 16 })
                        for (int u = 2; u <= across - 3; u++)
                            if (u < doorU - 1 || u > doorU + 2) Put(u, v, Props.Bench, v is 11 or 15 ? toFar : toNear);
                    for (int v = 10; v <= len - 2; v++)
                    {
                        var (lp, lq) = At(across, v);
                        ref Tile wall = ref plan.At(lp, lq);
                        if (wall.Kind != TileKind.Wall) continue;
                        wall.Detail = (byte)(L31Wall.Locker << L31SubShift);
                        wall.Pier = plan.Dir(toLowU);
                    }
                    for (int v = 12; v <= 13; v++)
                    {
                        var (cp, cq) = At(-1, v);
                        plan.At(cp, cq).Detail = (byte)(L31Wall.Chart << L31SubShift);
                    }
                    Sign(across, 3, L31Sign.Advert, toLowU);
                    Sign(-1, 16, L31Sign.Advert, toHighU);
                    Sign(doorU - 3, len, L31Sign.Advert, toFar);
                    break;
                }
            case L31Zone.Arcade:
                {
                    // Rows of cabinets back to back, an aisle every seventh, pinball and claw machines at the ends, now and
                    // then an old 1980s box cabinet; skee-ball along a wall; the green-card dispenser at the way in; on half
                    // of them a handmade OUT OF ORDER sign either side of the door; in one in three, a white door marked 70
                    for (int qa = q0 + 3; qa + 1 <= q1 - 3; qa += 6)
                        for (int p = p0 + 4; p <= p1 - 6; p++)
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
                    // (round 3) The redemption corner at the east end: glass prize cases as its counter with plush on them,
                    // the prize wall behind, PRIZES in neon over it
                    for (int q = q0 + 1; q <= q0 + 5; q++)
                    {
                        L31Put(plan, p1 - 2, q, L31Props.PrizeCase, ArchPier.West, (byte)(q == q0 + 3 ? 0 : 1 + (q + p1) % 4));
                        L31Put(plan, p1, q, L31Props.PrizeWall, ArchPier.West);
                    }
                    L31MountRun(plan, p1, q0 + 2, p1, q0 + 3, "prizes", ArchPier.West);
                    // A row of pinball machines along the far wall, and the photo booth in its corner
                    for (int u = 4; u <= across - 8; u++)
                    {
                        var (pp, pq) = At(u, 0);
                        if (door == ArchPier.South && pp is >= 95 and <= 100) continue;
                        if (u % 5 != 4) Put(u, 0, L31Props.Pinball, toNear);
                    }
                    Put(2, 0, L31Props.PhotoBooth, toNear);
                    Put(doorU - 1, len - 1, L31Props.CardDispenser, toFar);
                    {
                        var (dp, dq) = At(doorU - 1, len - 1);
                        L31MountRun(plan, dp, dq, dp, dq, "tokens", toFar);
                    }
                    {
                        var (na, nq) = At(doorU, len - 1);
                        var (nb, nr) = At(doorU + 1, len - 1);
                        L31MountRun(plan, na, nq, nb, nr, "arc", toFar);
                    }
                    // (the front band's arcade has a second door onto the hall, p 97-99, with its own dispenser, and ARCADE in
                    // neon over it on the hall's side)
                    if (door == ArchPier.South && p0 == 76)
                    {
                        L31Put(plan, 96, 0, L31Props.CardDispenser, ArchPier.South);
                        L31MountRun(plan, 97, -1, 99, -1, "arcbig", ArchPier.North, doorways: true);
                    }
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
                    // (round 3) The big TV is five blocks wide and three high on the wall over its low cabinet and sound bar
                    for (int c = -1; c <= 1; c++) Put(mid + c, 0, L31Props.MediaCab, toNear);
                    {
                        var (ta, tq) = At(mid - 2, 0);
                        var (tb, tr) = At(mid + 2, 0);
                        L31MountRun(plan, ta, tq, tb, tr, "bigtv", toNear);
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
                    // (small, as Wikidot has it: a wide one is walled in to sixteen across round its TV)
                    int edge = Math.Max(0, (across - 16) / 2);
                    for (int v = 0; v < len; v++)
                        for (int u = 0; u < across; u++)
                        {
                            if (u >= edge && u < across - edge) continue;
                            var (p, q) = At(u, v);
                            plan.At(p, q) = new Tile
                            {
                                Kind = TileKind.Wall, Pattern = WallPattern.L31Wall, Zone = (byte)L31Zone.Wall, Floor = FloorKind.L31Floor,
                                Ceiling = CeilingKind.L31Ceiling, Height = 4,
                            };
                        }
                    foreach (int v in new[] { 7, 9, 11 })
                        for (int u = edge + 1; u < across - edge - 1; u++) Put(u, v, L31Props.CinemaBench, toFar);
                    // Small TVs along both side walls, above the steps (Wikidot: "TV screens"), the room's only other light
                    foreach (int v in new[] { 2, 5, 8, 13 })
                        foreach (var (u, look) in new[] { (edge, toHighU), (across - edge - 1, toLowU) })
                        {
                            var (tp, tq) = At(u, v);
                            ref Tile tv = ref plan.At(tp, tq);
                            if (tv.Kind != TileKind.Floor) continue;
                            tv.Overhead = L31Overhead.Sign;
                            tv.Detail |= L31RailBit;
                            tv.Pier = plan.Dir(look);
                        }
                    // The red EXIT sign over the way out
                    {
                        var (ep, eq) = At(Math.Clamp(doorU - 1, edge, across - edge - 1), len - 1);
                        ref Tile exit = ref plan.At(ep, eq);
                        exit.Overhead = L31Overhead.Sign;
                        exit.Pier = plan.Dir(toFar);
                    }
                    break;
                }
            case L31Zone.Bath:
                {
                    // (round 3, a real restroom) Walled in to a restroom's size round its door (fourteen across, eleven deep:
                    // the rooms were halls), a row of stalls along its far wall (the men's side and the women's, a gap
                    // between), the vanity of basins under their mirrors along one side by the door, the hand dryers and a
                    // bin on the other
                    int bw = Math.Min(across, 14), ua = Math.Clamp(doorU - 6, 0, across - bw), ub = ua + bw - 1, vf = Math.Max(0, len - 11);
                    for (int v = 0; v < len; v++)
                        for (int u = 0; u < across; u++)
                        {
                            if (u >= ua && u <= ub && v >= vf) continue;
                            var (wp, wq) = At(u, v);
                            plan.At(wp, wq) = new Tile
                            {
                                Kind = TileKind.Wall, Pattern = WallPattern.L31Wall, Zone = (byte)L31Zone.Wall, Floor = FloorKind.L31Floor,
                                Ceiling = CeilingKind.L31Ceiling, Height = 4,
                            };
                        }
                    for (int u = ua + 1; u <= ub - 1; u++)
                        if (u <= ua + 5 || u >= ub - 5) Put(u, vf, L31Props.Stall, toNear);
                    for (int v = len - 2; v >= len - 4; v--)
                    {
                        Put(ua, v, L31Props.Vanity, toHighU);
                        var (mp, mq) = At(ua, v);
                        L31MountRun(plan, mp, mq, mp, mq, "mirror", toHighU);
                    }
                    foreach (int v in new[] { len - 3, len - 5 })
                    {
                        var (hp, hq) = At(ub, v);
                        L31MountRun(plan, hp, hq, hp, hq, "dryer", toLowU);
                    }
                    Put(ub, len - 2, L31Props.Bin, toLowU);
                    break;
                }
            case L31Zone.Hvac:
                {
                    // Ducting and machinery, a fan, boxes, dead radiators, a pipe run along the far wall; the cold leaks in
                    // (8 C) and one in three is flooded where its pipes burst (Fandom); puddles elsewhere
                    for (int k = rng.Range(1, 3); k > 0; k--)
                    {
                        int p = rng.Range(p0 + 2, p1 - 2), q = rng.Range(q0 + 3, q1 - 2);
                        double r = rng.NextDouble();
                        L31Put(plan, p, q, r < 0.4 ? Props.PipeStack : r < 0.6 ? Props.Generator : r < 0.8 ? Props.FloorFan : Props.CardboardBoxes,
                            (ArchPier)rng.Range(0, 3));
                    }
                    // (round 3) The plant itself along the far wall: the air handlers side by side, the pressure tanks, the
                    // water heater, under the pipe run
                    int hm = across / 2;
                    // (round 4: two of Level 120's CRAC units with their ducts up into the ceiling, in place of four low AC boxes)
                    foreach (int u in new[] { hm - 2, hm + 1 }) Put(u, 1, L31Props.AirHandler, toNear);
                    Put(hm + 3, 1, Props.PressureTank, toNear, 1);
                    Put(hm + 4, 1, Props.PressureTank, toNear);
                    Put(hm - 4, 1, Props.PressureTank, toNear, 1);
                    // and the supply duct out of them under the ceiling, the length of the room
                    for (int v = 1; v <= len - 2; v++)
                    {
                        var (dp, dq) = At(hm, v);
                        plan.At(dp, dq).Overhead = door is ArchPier.North or ArchPier.South ? Overheads.L31DuctNS : Overheads.L31DuctWE;
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
                // (round 3) The skate-repair bench in the middle, its toolbox beside it
                Put(across / 2, len / 2, Props.Workbench, toNear);
                Put(across / 2 + 1, len / 2, Props.Toolbox, toNear);
                break;
            case L31Zone.Lounge:
                {
                    // The Employees Lounge (Fandom): exposed brick, grey carpet, lockers along the walls, a kitchenette and
                    // the snack machines, tables, the CCTV desk and cameras in the corners, a custodian's corner; silent.
                    // A big one is walled off a third of the way along: past a door in a wall of lockers, the staff's
                    // stock room (shelves in rows, boxes)
                    int lw = across;
                    if (across > 22)
                    {
                        lw = 16;
                        for (int v = 0; v < len; v++)
                        {
                            var (wp, wq) = At(lw, v);
                            ref Tile wall = ref plan.At(wp, wq);
                            wall = new Tile
                            {
                                Kind = v is 3 or 4 ? TileKind.Doorway : TileKind.Wall, Pattern = WallPattern.L31Wall, Zone = (byte)L31Zone.Lounge,
                                Floor = FloorKind.L31Floor, Ceiling = CeilingKind.L31Ceiling, Height = 4,
                                Detail = v is 3 or 4 ? (byte)0 : (byte)(L31Wall.Locker << L31SubShift), Pier = plan.Dir(toLowU),
                            };
                            for (int u = lw + 1; u < across; u++)
                            {
                                var (sp, sq) = At(u, v);
                                plan.At(sp, sq).Zone = (byte)L31Zone.Store;
                                plan.At(sp, sq).Detail = L31Hue.White;
                            }
                        }
                        for (int u = lw + 3; u <= across - 2; u += 3)
                            for (int v = 1; v <= len - 4; v++)
                                if (v != len / 2) Put(u, v, Props.Shelf, (u - lw) % 2 == 0 ? toLowU : toHighU);
                        for (int k = rng.Range(2, 4); k > 0; k--) Put(rng.Range(lw + 2, across - 1), rng.Chance(0.5) ? 0 : len - 3, Props.CardboardBoxes, toNear); // (at the aisles' ends, never across one)
                        if (rng.Chance(0.5)) Box(across - 1, len - 2);
                    }
                    for (int v = 1; v <= len - 2; v++)
                    {
                        var (lp, lq) = At(-1, v);
                        ref Tile wall = ref plan.At(lp, lq);
                        if (wall.Kind != TileKind.Wall) continue;
                        wall.Detail = (byte)(L31Wall.Locker << L31SubShift);
                        wall.Pier = plan.Dir(toHighU);
                    }
                    Put(lw - 1, 0, Props.Fridge, toNear);
                    Put(lw - 2, 0, Props.KitchenCounter, toNear, 1);
                    Put(lw - 3, 0, Props.KitchenCounter, toNear);
                    Put(lw - 5, 0, L31Props.Vending, toNear, 0);
                    Put(lw - 6, 0, L31Props.Vending, toNear, 1);
                    Put(0, 0, L31Props.Monitors, toNear);
                    {
                        var (ba, bq) = At(2, 0);
                        var (bb, br) = At(3, 0);
                        L31MountRun(plan, ba, bq, bb, br, "board", toNear);
                    }
                    {
                        var (pp, pq) = At(5, 0);
                        L31MountRun(plan, pp, pq, pp, pq, "poster" + (p0 + q0 & 3), toNear);
                    }
                    for (int v = 4; v <= len - 5; v += 5)
                        for (int u = 3; u <= lw - 4; u += 5)
                        {
                            Put(u, v, Props.CafeTable, toNear);
                            Put(u - 1, v, Props.CafeChair, toHighU);
                            Put(u + 1, v, Props.CafeChair, toLowU);
                            if (rng.Chance(0.5)) Put(u, v + 1, Props.CafeChair, toFar);
                        }
                    Put(lw - 1, len - 2, Props.Shelf, toLowU);
                    Put(lw - 2, len - 2, Props.WetFloorSign, toNear);
                    Put(lw - 1, len - 3, Props.CardboardBoxes, toNear);
                    Put(0, len - 2, L31Props.Bin, toNear);
                    if (rng.Chance(0.4)) Box(lw - 2, len - 3);
                    foreach (var (u, v, look) in new[] { (lw - 1, 1, toNear), (0, len - 2, toFar) })
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

        // (round 3) A mirror ball over each turn (the star keeps the centre); the rink's name in neon on the wall facing the DJ,
        // the rules board, NO RUNNING by every door, the session board by the DJ; the snack window on the north skirt (a
        // counter against the wall under its menu, the popcorn machine and a drinks fridge); skate lockers along the side
        // walls with benches in front of them
        int turn = pc - (o0 + radius);
        plan.At(pc - turn, qc).Overhead = L31Overhead.DiscoBall;
        plan.At(pc + turn, qc).Overhead = L31Overhead.DiscoBall;
        // Lighting trusses with par cans under the ceiling: one down the middle of the long way, two across it
        for (int p = o0 + radius - 4; p <= o1 - radius + 4; p++)
            if (Math.Abs(p - pc) > 1 && Math.Abs(Math.Abs(p - pc) - turn) > 1) plan.At(p, qc).Overhead = Overheads.L31TrussWE;
        foreach (int p in new[] { pc - 12, pc + 12 })
            for (int q = qc - (tiny ? 8 : 14); q <= qc + (tiny ? 8 : 14); q++)
                if (q != qc && plan.At(p, q).Overhead == 0) plan.At(p, q).Overhead = Overheads.L31TrussNS;
        L31MountRun(plan, pc - 2, north, pc + 2, north, "name", toWall);
        L31MountRun(plan, pc - 14, north, pc - 13, north, "rules", toWall);
        L31MountRun(plan, pc + 5, south, pc + 6, south, "session", toRink);
        foreach (int p in new[] { 35, 85 }) L31MountRun(plan, p, s0, p, s0, "norun", ArchPier.South);
        foreach (int p in new[] { 58, 62 }) L31MountRun(plan, p, s1, p, s1, "norun", ArchPier.North);
        L31MountRun(plan, r0, 57, r0, 57, "norun", ArchPier.East);
        L31MountRun(plan, r1, 61, r1, 61, "norun", ArchPier.West);
        for (int p = 70; p <= 72; p++) L31Put(plan, p, north, Props.SnackCounter, toWall, (byte)(p == 70 ? 1 : 0));
        L31Put(plan, 73, north, L31Props.Slushie, toWall);
        L31Put(plan, 69, north, L31Props.Popcorn, toWall);
        L31Put(plan, 74, north, Props.DrinkFridge, toWall);
        L31MountRun(plan, 71, north, 72, north, "snackwin", toWall);
        if (!tiny)
            foreach (int q in new[] { s0 + 4, s0 + 6, s0 + 8, s0 + 10, s0 + 12, s1 - 12, s1 - 10, s1 - 8, s1 - 6, s1 - 4 })
                for (int k = 0; k <= 1; k++)
                {
                    int wallP = k == 0 ? r0 - 1 : r1 + 1, benchP = k == 0 ? r0 + 1 : r1 - 1;
                    ArchPier toIn = k == 0 ? ArchPier.East : ArchPier.West;
                    for (int dq = 0; dq <= 1; dq++)
                    {
                        ref Tile wall = ref plan.At(wallP, q + dq);
                        if (wall.Kind != TileKind.Wall) continue;
                        wall.Detail = (byte)(L31Wall.Locker << L31SubShift);
                        wall.Pier = plan.Dir(toIn);
                    }
                    L31Put(plan, benchP, q, Props.Bench, toIn);
                }

        // The walls round the skirt, above the benches: each side clad, by hash, in the mural or in black lacquer with
        // chrome-framed mirrors, as the halls are (the generator finds the wall beside the tile; doors are left bare)
        ulong clad = Hashing.Hash(seed, plan.Wx, plan.Wz, SaltL31Clad + 8);
        for (int q = s0; q <= s1; q++)
            for (int p = r0; p <= r1; p++)
            {
                int side = q == s0 ? 0 : q == s1 ? 1 : p == r0 ? 2 : p == r1 ? 3 : -1;
                if (side < 0) continue;
                var (wp, wq) = side switch { 0 => (p, q - 1), 1 => (p, q + 1), 2 => (p - 1, q), _ => (p + 1, q) };
                if (plan.At(wp, wq).Kind is not (TileKind.Wall or TileKind.Doorway)) continue;
                plan.At(p, q).Overhead = (clad >> side & 1) == 0 ? L31Overhead.Mural : L31Overhead.Mirrors;
            }
        // The DJ station's neon sign on the wall behind it (always the world's south wall: the viewer looks south, so the
        // sign's left column is the east one)
        for (int p = pc - 1; p <= pc + 1; p++)
        {
            ref Tile t = ref plan.At(p, south);
            t.Overhead = L31Overhead.Sign;
            t.Detail = (byte)(t.Detail & L31HueMask | (1 + pc + 1 - p) << L31SubShift);
        }
    }

    /// <summary>
    /// Round 3's signs outside the rooms: each room's name over its door on the corridor's side (the restroom figures beside a
    /// restroom's, NOW SHOWING cases either side of a cinema's), the rink's name over the lobby's front doors on the hall's
    /// side; fire extinguishers, alarm pulls and the rink's posters along the corridor's inner walls; EXIT over the
    /// passages out to the halls.
    /// </summary>
    private static void L31LaySigns(L31Plan plan)
    {
        foreach (L31Room room in plan.Rooms)
        {
            if (room.Kind == L31Zone.Lobby)
            {
                L31MountRun(plan, 58, -1, 62, -1, "name", ArchPier.North, doorways: true);
                continue;
            }
            string name = room.Kind switch
            {
                L31Zone.Rental => "rent", L31Zone.Snack => "snack", L31Zone.Arcade => "arc", L31Zone.Bath => "rest", L31Zone.Cinema => "cine",
                L31Zone.Lounge => "staff", L31Zone.Store => "store", L31Zone.Hvac => "mech", _ => null,
            };
            if (name == null || room.DoorP < -1) continue;
            ArchPier side = room.DoorSide;
            bool alongP = side is ArchPier.North or ArchPier.South;
            int ap = room.DoorP + (side == ArchPier.West ? -1 : side == ArchPier.East ? 1 : 0);
            int aq = room.DoorQ + (side == ArchPier.North ? -1 : side == ArchPier.South ? 1 : 0);
            int sp = alongP ? 1 : 0, sq = alongP ? 0 : 1;
            L31MountRun(plan, ap, aq, ap + sp, aq + sq, name, side);
            if (room.Kind == L31Zone.Bath) L31MountRun(plan, ap + 2 * sp, aq + 2 * sq, ap + 2 * sp, aq + 2 * sq, "mw", side);
            if (room.Kind == L31Zone.Cinema)
            {
                L31MountRun(plan, ap - sp, aq - sq, ap - sp, aq - sq, "nowshow", side);
                L31MountRun(plan, ap + 2 * sp, aq + 2 * sq, ap + 2 * sp, aq + 2 * sq, "nowshow", side);
            }
        }
        // Along the corridor's inner walls (the rink's), every ten blocks: an extinguisher, a poster, an alarm pull, a poster
        int n = 0;
        void Dress(int p, int q, int wp, int wq, ArchPier face)
        {
            if (plan.At(wp, wq).Kind != TileKind.Wall || plan.At(p, q).Zone != (byte)L31Zone.Corridor) return;
            int k = n++;
            string what = (k % 4) switch { 0 => "ext", 2 => "alarm", _ => "poster" + (k / 2 + plan.Wx + plan.Wz & 3) };
            L31MountRun(plan, p, q, p, q, what, face);
        }
        for (int p = 21; p <= 99; p += 10)
        {
            Dress(p, 24, p, 25, ArchPier.North);
            Dress(p + 4, 96, p + 4, 95, ArchPier.South);
        }
        for (int q = 31; q <= 89; q += 10)
        {
            Dress(16, q, 17, q, ArchPier.West);
            Dress(104, q + 4, 103, q + 4, ArchPier.East);
        }
        L31MountRun(plan, 0, 59, 0, 59, "exit", ArchPier.East);
        L31MountRun(plan, L31Size - 1, 60, L31Size - 1, 60, "exit", ArchPier.West);
        L31MountRun(plan, 60, L31Size - 1, 60, L31Size - 1, "exit", ArchPier.North);
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
                // (a doorway's lintel is faced as the wall it is cut in)
                if (t.Kind == TileKind.Doorway)
                {
                    t.Detail = (byte)(Material(rank) << L31SubShift);
                    continue;
                }
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
