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
    private const ulong SaltL31Shape = 0x2401, SaltL31Complex = 0x2410, SaltL31Room = 0x2411, SaltL31Light = 0x2412, SaltL31Hall = 0x2413;

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
        public const byte Skate = 0, Concrete = 1, Blue = 2, Glazed = 3, Dark = 4, Chart = 5, Locker = 6;
    }

    /// <summary>A rink board's sub-kind; a corridor tile's pipe run (along X or Z, in the world).</summary>
    public const byte L31BoardPlain = 0, L31BoardStripeNS = 1, L31BoardStripeWE = 2, L31BoardCentre = 3, L31PipeX = 1, L31PipeZ = 2;

    /// <summary>Values of <see cref="Tile.Overhead"/> (the level's 140-149): a hall's neon tube under the ceiling, lit or dead, and the disco ball.</summary>
    public static class L31Overhead
    {
        public const byte NeonNS = 140, NeonWE = 141, DeadNS = 142, DeadWE = 143, DiscoBall = 144;
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
    }

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

    /// <summary>Arriving: out in a neon hall or in a lobby, never in a room or out on the rink.</summary>
    private static bool IsL31ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone is (byte)L31Zone.Hall or (byte)L31Zone.Crossing or (byte)L31Zone.Lobby;

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
        plan.Flip = (h & 1) != 0;
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
            L31LayRoom(plan, 0, 0, 26, 19, rng.Chance(0.55) ? L31Zone.Snack : L31Zone.Lounge, ArchPier.South);
            L31LayRoom(plan, 28, 0, 44, 19, rng.Chance(0.55) ? L31Zone.Rental : L31Zone.Store, ArchPier.South);
            L31LayRoom(plan, 46, 0, 74, 19, L31Zone.Lobby, ArchPier.South);
            bool arcade = rng.Chance(0.65);
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
                    L31Zone z = r < 0.30 ? L31Zone.Bath : r < 0.50 ? L31Zone.Hvac : r < 0.68 ? L31Zone.Store : r < 0.76 ? L31Zone.CarpetRoom : L31Zone.Lounge;
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
                L31Zone z = r < 0.20 ? L31Zone.Cinema : r < 0.35 ? L31Zone.Arcade : r < 0.50 ? L31Zone.Bath : r < 0.65 ? L31Zone.Hvac
                    : r < 0.75 ? L31Zone.Snack : r < 0.85 ? L31Zone.Store : L31Zone.Lounge;
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
        int air = L31Air(zone, plan.Tiny);
        for (int q = q0; q <= q1; q++)
            for (int p = p0; p <= p1; p++) L31Open(ref plan.At(p, q), zone, air, hue);

        // The door, two wide, about the middle of the side it is on (kept within the corridor's reach)
        if (door is ArchPier.North or ArchPier.South)
        {
            int dq = door == ArchPier.North ? q0 - 1 : q1 + 1;
            int dp = Math.Clamp((p0 + p1) / 2 + rng.Range(-2, 2), Math.Max(p0, 14), Math.Min(p1 - 1, 105));
            L31Door(ref plan.At(dp, dq), zone);
            L31Door(ref plan.At(dp + 1, dq), zone);
            if (zone == L31Zone.Lobby) for (int p = 58; p <= 62; p++) L31Door(ref plan.At(p, dq), zone);
        }
        else
        {
            int dp = door == ArchPier.West ? p0 - 1 : p1 + 1;
            int dq = Math.Clamp((q0 + q1) / 2 + rng.Range(-2, 2), q0 + 1, q1 - 2);
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
                // The counter across the far end and its kitchen behind, tables and chairs, machines along one side
                for (int p = p0 + 3; p <= p1 - 3; p++)
                {
                    L31Put(plan, p, q1 - 2, Props.SnackCounter, ArchPier.North, (byte)(p == p0 + 4 ? 1 : (p - p0) % 4 == 1 ? 2 : 0));
                    if ((p - p0) % 3 == 1) L31Put(plan, p, q1, (p & 1) == 0 ? Props.Fryer : Props.Stove, ArchPier.North);
                }
                for (int q = q0 + 3; q <= q1 - 6; q += 4)
                    for (int p = p0 + 4; p <= p1 - 3; p += 5)
                    {
                        L31Put(plan, p, q, Props.CafeTable, ArchPier.North);
                        L31Put(plan, p - 1, q, Props.CafeChair, ArchPier.East);
                        L31Put(plan, p + 1, q, Props.CafeChair, ArchPier.West);
                    }
                for (int q = q0 + 1; q <= q1 - 5; q += 2) L31Put(plan, p0, q, (q & 2) == 0 ? Props.SnackVending : Props.DrinkFridge, ArchPier.East);
                break;
            case L31Zone.Rental:
                // The counter across the room, shelves of skates behind it, benches in front, the size chart on the wall
                for (int p = p0 + 2; p <= p1 - 3; p++) L31Put(plan, p, q0 + 11, L31Props.Counter, ArchPier.North, (byte)(p == p0 + 2 ? 0 : p == p1 - 3 ? 2 : 1));
                for (int p = p0 + 1; p <= p1 - 1; p++) if (rng.Chance(0.85)) L31Put(plan, p, q1, Props.Shelf, ArchPier.South);
                for (int p = p0 + 2; p <= p1 - 2; p += 2) L31Put(plan, p, q0 + 4, Props.Bench, ArchPier.South);
                plan.At(p0 - 1, q0 + 4).Detail = (byte)(L31Wall.Chart << L31SubShift);
                plan.At(p0 - 1, q0 + 5).Detail = (byte)(L31Wall.Chart << L31SubShift);
                break;
            case L31Zone.Arcade:
                // Rows of cabinets back to back, an aisle every seventh, pinball and claw machines at the ends; skee-ball along a wall
                for (int qa = q0 + 3; qa + 1 <= q1 - 3; qa += 6)
                    for (int p = p0 + 4; p <= p1 - 3; p++)
                    {
                        int k = (p - p0) % 7;
                        if (k == 0) continue;
                        bool end = k is 1 or 6;
                        var (x, z) = plan.World(p, qa);
                        ulong c = Hashing.Hash(seed, x, z, SaltL31Room + 1);
                        ushort front = end ? ((c & 1) == 0 ? L31Props.Pinball : L31Props.Claw) : Hashing.Unit(c) < 0.1 ? L31Props.DeadCabinet : L31Props.Cabinet;
                        L31Put(plan, p, qa, front, ArchPier.North, (byte)(c % 6));
                        L31Put(plan, p, qa + 1, end ? L31Props.Pinball : L31Props.Cabinet, ArchPier.South, (byte)(c / 7 % 6));
                    }
                for (int q = q0 + 2; q <= q1 - 2; q += 3)
                {
                    L31Put(plan, p0, q, L31Props.SkeeTarget, ArchPier.East);
                    L31Put(plan, p0 + 1, q, L31Props.SkeeLane, ArchPier.East);
                }
                L31Put(plan, p1, q0 + 2, L31Props.PrizeCounter, ArchPier.West);
                L31Put(plan, p1, q0 + 3, L31Props.PrizeCounter, ArchPier.West);
                break;
            case L31Zone.Cinema:
                {
                    // The screen across the far wall (hung under the ceiling), rows of benches facing it, an aisle up the middle
                    int mid = (p0 + p1) / 2;
                    int screenQ = door == ArchPier.North ? q1 : q0;
                    ArchPier toScreen = door == ArchPier.North ? ArchPier.South : ArchPier.North;
                    for (int p = mid - 5; p <= mid + 5; p++) L31Put(plan, p, screenQ, L31Props.Screen, L31Opposite(toScreen), (byte)(p == mid - 5 ? 0 : p == mid + 5 ? 2 : 1));
                    for (int k = 5; k <= d - 4; k += 3)
                    {
                        int q = door == ArchPier.North ? q1 - k : q0 + k;
                        for (int p = p0 + 2; p <= p1 - 2; p++)
                            if (Math.Abs(p - mid) > 1) L31Put(plan, p, q, Props.Bench, toScreen);
                    }
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
                // Ducting and machinery, a fan, boxes; puddles on the floor (WorldGenerator.L31.cs wets it)
                for (int k = rng.Range(3, 6); k > 0; k--)
                {
                    int p = rng.Range(p0 + 2, p1 - 2), q = rng.Range(q0 + 2, q1 - 2);
                    double r = rng.NextDouble();
                    L31Put(plan, p, q, r < 0.4 ? Props.PipeStack : r < 0.6 ? Props.Generator : r < 0.8 ? Props.FloorFan : Props.CardboardBoxes,
                        (ArchPier)rng.Range(0, 3));
                }
                break;
            case L31Zone.Store:
                for (int i = 2; wide ? i <= w - 3 : i <= d - 3; i++)
                {
                    if (rng.Chance(0.8)) { if (wide) L31Put(plan, p0 + i, q0, Props.Shelf, ArchPier.North); else L31Put(plan, p0, q0 + i, Props.Shelf, ArchPier.West); }
                    if (rng.Chance(0.8)) { if (wide) L31Put(plan, p0 + i, q1, Props.Shelf, ArchPier.South); else L31Put(plan, p1, q0 + i, Props.Shelf, ArchPier.East); }
                }
                for (int k = rng.Range(1, 3); k > 0; k--) L31Put(plan, rng.Range(p0 + 3, p1 - 3), rng.Range(q0 + 3, q1 - 3), Props.CardboardBoxes, ArchPier.North);
                break;
            case L31Zone.Lounge:
                // Benches along the far wall, a bin, a machine
                {
                    int bq = door == ArchPier.North ? q1 : q0;
                    if (wide) for (int p = p0 + 2; p <= p1 - 2; p += 3) L31Put(plan, p, bq, Props.Bench, door == ArchPier.North ? ArchPier.North : ArchPier.South);
                    else for (int q = q0 + 2; q <= q1 - 2; q += 3) L31Put(plan, door == ArchPier.West ? p1 : p0, q, Props.Bench, door == ArchPier.West ? ArchPier.West : ArchPier.East);
                    L31Put(plan, p0 + 1, q0 + 1, L31Props.Bin, ArchPier.North);
                    L31Put(plan, p1 - 1, q0 + 1, L31Props.Vending, ArchPier.South, (byte)rng.Range(0, 1));
                    break;
                }
        }
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
        plan.At(pc, qc).Overhead = L31Overhead.DiscoBall;

        // Benches along the skirt by the near wall, facing the rink, and either side of the DJ booth
        for (int p = r0 + 4; p <= r1 - 4; p += 3)
            if (p is not (>= 34 and <= 40 or >= 80 and <= 86)) L31Put(plan, p, s0, Props.Bench, ArchPier.South);
        // The DJ booth on the far skirt: a counter facing the rink, the DJ's screen behind
        for (int p = pc - 4; p <= pc + 4; p++) L31Put(plan, p, s1 - 4, L31Props.Counter, ArchPier.North, (byte)(p == pc - 4 ? 0 : p == pc + 4 ? 2 : 1));
        for (int p = pc - 2; p <= pc + 2; p++) L31Put(plan, p, s1 - 1, L31Props.DjScreen, ArchPier.North);
        for (int p = r0 + 6; p <= r1 - 6; p += 4)
            if (Math.Abs(p - pc) > 7) L31Put(plan, p, s1, Props.Bench, ArchPier.North);

        // Mirror panels round the rink's walls, facing in
        for (int p = r0; p <= r1; p += 6)
        {
            L31Mirror(plan, p, s0 - 1, ArchPier.South);
            L31Mirror(plan, p, s1 + 1, ArchPier.North);
        }
        for (int q = s0 + 2; q <= s1; q += 6)
        {
            L31Mirror(plan, r0 - 1, q, ArchPier.East);
            L31Mirror(plan, r1 + 1, q, ArchPier.West);
        }
    }

    private static void L31Mirror(L31Plan plan, int p, int q, ArchPier face)
    {
        ref Tile t = ref plan.At(p, q);
        if (t.Kind != TileKind.Wall) return;
        t.Detail |= L31MirrorBit;
        t.Pier = plan.Dir(face);
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
            (byte)L31Zone.Corridor or (byte)L31Zone.Hvac or (byte)L31Zone.Store or (byte)L31Zone.Empty or (byte)L31Zone.CarpetRoom or (byte)L31Zone.Wall or 0 => 0,
            _ => 1,
        };
        static byte Material(int rank) => rank switch
        {
            5 => L31Wall.Blue,
            4 => L31Wall.Glazed,
            3 => L31Wall.Dark,
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
                // A chart or the lockers laid out by a room stay as they are; an emptiness's pillars too; the mirror bit stays
                byte sub = (byte)((t.Detail & L31SubMask) >> L31SubShift);
                if (sub is L31Wall.Chart or L31Wall.Locker) continue;
                t.Detail = (byte)(t.Detail & L31MirrorBit | Material(rank) << L31SubShift);
            }
        // The outside walls facing the halls: a mirror panel every eight blocks
        for (int i = 3; i < L31Size; i += 8)
        {
            OuterMirror(ref plan.AtAB(i, -1), ArchPier.North);
            OuterMirror(ref plan.AtAB(i, L31Size), ArchPier.South);
            OuterMirror(ref plan.AtAB(-1, i), ArchPier.West);
            OuterMirror(ref plan.AtAB(L31Size, i), ArchPier.East);
        }
        static void OuterMirror(ref Tile t, ArchPier face)
        {
            if (t.Kind != TileKind.Wall) return;
            t.Detail |= L31MirrorBit;
            t.Pier = face;
        }
    }

    /// <summary>Which of the level's props (<see cref="Props.L31First"/>-<see cref="Props.L31Last"/>) people walk through: none.</summary>
    private static bool L31WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: 12 C (the plan's; <see cref="LevelTemperatures"/> keeps the scaffold's 16 for now), 8 C in the HVAC rooms where the cold leaks in.</summary>
    private float L31Temperature(int x, int y, int z, int floorY) => TileAt(x, z).Zone == (byte)L31Zone.Hvac ? 8f : 12f;

    /// <summary>Reality stability: a little steadier than neutral everywhere; the rink is a safe place.</summary>
    private float L31Stability(double x, double y, double z, int floorY, float drift) => 1.1f;
}
