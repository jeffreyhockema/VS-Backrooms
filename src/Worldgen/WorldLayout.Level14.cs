using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 14, "The Hospital" (experimental): kept as level 29 (<see cref="Level14"/>) and shown as "14". Fandom's Level 14: "a
/// regular, well-equipped hospital comprising infinitely segmented areas that contain shadowy hallways and unsettling rooms"
/// (the design is docs/design/experimental-levels/14-plan.md). A round noclip region far out to the north-north-west, beyond
/// Level 73 and the End.
///
/// <para><b>The lattice.</b> Shadowy main halls run straight through the region every <see cref="L14Period"/> blocks each
/// way, four wide (x or z mod 64 in 1-4) and four high, fluorescent troffers down their middle, too many of them dead.
/// Between four halls lies a <b>wing</b>, 58 blocks square (mod 64 in 6-63, its walls at 5 and 0), one department of the
/// hospital (a medical ward, intensive care, psychiatry, maternity, the surgical suite, stores), planned once from its own
/// hash (<see cref="L14PlanOf"/>).</para>
///
/// <para><b>A wing</b> is cut by side corridors (three wide, three high) running the whole width of the piece they split, so
/// every corridor ends on another or opens through the wing's wall onto a hall; the pieces between are strips of rooms
/// side by side, each with its door on the corridor (or hall) it fronts. Rooms by the page's kinds: reception rooms (where
/// everyone arrives: the oval desk, chairs, a lamp, the stained-glass revolving door that shows nothing), inpatient rooms
/// (medical, intensive care, behaviour, maternity: blinding white, windows onto blackness), surgery rooms behind shut doors,
/// storage rooms with thrown-together walls, and rarely the Hunter's torture chambers and the T.14.R.G.'s remains; offices
/// (ours). Now and then a room is contaminated.</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> is the <see cref="L14Zone"/> with <see cref="L14DarkBit"/> and
/// <see cref="L14ContamBit"/>; a floor tile's <see cref="Tile.Height"/> is its air (3 or 4), its <see cref="Tile.Depth"/>
/// the floor (<see cref="L14FVinyl"/> ...); a wall tile's <see cref="Tile.Depth"/> is its material (<see cref="L14MPaint"/>
/// ...), its <see cref="Tile.Detail"/> what is on its face toward <see cref="Tile.Pier"/> (<see cref="L14DRail"/> ...), with
/// <see cref="Tile.Stack"/> the kind; a doorway's <see cref="Tile.Detail"/> is its door (<see cref="L14DoorFrame"/> ...).</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2900-0x29BF are this level's (0x29C0-0x29FF its thresholds').</summary>
    private const ulong SaltL14Shape = 0x2901, SaltL14Wing = 0x2910, SaltL14Light = 0x2911, SaltL14Dark = 0x2912, SaltL14Dept = 0x2913,
        SaltL14Hall = 0x2914, SaltL14HallProp = 0x2916;

    /// <summary>The lattice: a main hall every 64 blocks each way, four wide; a wing's inside is 58 square, its plan 60 with its walls.</summary>
    public const int L14Period = 64, L14HallWidth = 4, L14WingSize = 58, L14Grid = 60;

    /// <summary>How high the main halls are (blocks of air); corridors and most rooms are three.</summary>
    public const int L14HallHeight = 4;

    /// <summary>What part of the level a tile is in (kept in the low six bits of <see cref="Tile.Zone"/>).</summary>
    public enum L14Zone : byte
    {
        None, Hall, Corridor, Reception, Ward, Icu, Psych, Maternity, Surgery, Storage, Torture, Research, Office, Station, Blank, Wall,
    }

    /// <summary>A wing's department (what most of its rooms are).</summary>
    public enum L14Dept : byte { Medical, Icu, Psych, Maternity, Surgery, Stores }

    /// <summary>Set in <see cref="Tile.Zone"/> where the lights are dead; and in a contaminated room.</summary>
    public const byte L14DarkBit = 0x80, L14ContamBit = 0x40;

    /// <summary>A tile's zone, without its flags.</summary>
    public static L14Zone L14ZoneOf(in Tile t) => (L14Zone)(t.Zone & 0x3F);

    public static bool L14IsDark(in Tile t) => (t.Zone & L14DarkBit) != 0;
    public static bool L14IsContam(in Tile t) => (t.Zone & L14ContamBit) != 0;

    /// <summary>Whether a zone is one of the rooms (as against the halls, corridors and walls).</summary>
    public static bool L14IsRoom(L14Zone z) => z is >= L14Zone.Reception and <= L14Zone.Blank;

    /// <summary>Whether a block position lies in Level 14.</summary>
    public bool L14In(int gx, int gz) => LevelAt(MacroOf(gx), MacroOf(gz)) == Level14;

    /// <summary>A floor tile's floor (<see cref="Tile.Depth"/>), in the order of <c>l14-floor</c>'s kinds.</summary>
    public const byte L14FVinyl = 0, L14FVinylWorn = 1, L14FBorder = 2, L14FWhite = 3, L14FPink = 4, L14FTheatre = 5, L14FTerrazzo = 6, L14FConcrete = 7,
        L14FMarble = 8, L14FMarbleShattered = 9, L14FBlood = 10, L14FMould = 11, L14FContam = 12, L14FCracked = 13, L14FSagging = 14, L14FLineNS = 15,
        L14FLineWE = 16, L14FArrowN = 17, L14FArrowE = 18, L14FArrowS = 19, L14FArrowW = 20;

    /// <summary>A wall tile's material (<see cref="Tile.Depth"/>): the generator draws its foot and its upper blocks from it.</summary>
    public const byte L14MPaint = 0, L14MWhite = 1, L14MTile = 2, L14MPadded = 3, L14MCinder = 4, L14MPlywood = 5, L14MRust = 6, L14MTileBlood = 7,
        L14MMould = 8, L14MWhiteMoss = 9, L14MConcrete = 10;

    /// <summary>
    /// What is on a wall tile's face (<see cref="Tile.Detail"/>, toward <see cref="Tile.Pier"/>; <see cref="Tile.Stack"/> the kind):
    /// the handrail at the foot of a hall's or corridor's wall; a room's name plate (Stack the plate); a department sign (Stack
    /// 0-7); a poster (Stack: kid 0-2, health 3-4); a stopped clock; a ward board; an X-ray light box; blood (a smear; running
    /// down from above); a mould bloom; scratches; an exit sign; a sanitizer; an extinguisher; the T.14.R.G.'s stencil; a
    /// window onto blackness (Stack 0 broken, 1 shattered); a part of the revolving door's back row (Stack its column).
    /// </summary>
    public const byte L14DNone = 0, L14DRail = 1, L14DPlate = 2, L14DSign = 3, L14DPoster = 4, L14DClock = 5, L14DBoard = 6, L14DXray = 7,
        L14DBlood = 8, L14DBloodDrip = 9, L14DMould = 10, L14DScratches = 11, L14DExit = 12, L14DSanitizer = 13, L14DExtinguisher = 14, L14DTrg = 15,
        L14DWindow = 16, L14DRevolving = 17, L14DDirectory = 18, L14DLift = 19, L14DMonArm = 20;

    /// <summary>The room plates (<see cref="L14DPlate"/>'s Stack), in the order of <c>l14-walldeco-plate-*</c>.</summary>
    public const byte L14PlateWard = 0, L14PlateIcu = 1, L14PlateSurgery = 2, L14PlateMaternity = 3, L14PlatePsych = 4, L14PlateStorage = 5,
        L14PlateReception = 6, L14PlateOffice = 7, L14PlateResearch = 8, L14PlateDanger = 9, L14PlateBiohazard = 10;

    /// <summary>A doorway's door (<see cref="Tile.Detail"/>; Stack its hinge, 0 left, 1 right; Pier the face it shows): an open frame, a room door standing open, shut, locked, a contaminated room's door with its window, fire doors propped open.</summary>
    public const byte L14DoorFrame = 0, L14DoorOpen = 1, L14DoorClosed = 2, L14DoorLocked = 3, L14DoorContam = 4, L14DoorFire = 5;

    /// <summary>The plan of one wing, by (A, B) = (x, z) from its inside's north-west corner, -1..58 each way (its walls included).</summary>
    public sealed partial class L14Plan
    {
        public int Hx, Hz;
        public L14Dept Dept;
        public int Rooms, Receptions, Tortures, Research, Contaminated, Surgeries, Boxes;
        /// <summary>The middle of each torture chamber, and where the research group's notes lie (block positions).</summary>
        public readonly List<(int X, int Z)> TortureSpots = new(), NoteSpots = new();
        public readonly Tile[] Tiles = new Tile[L14Grid * L14Grid];

        public ref Tile AtAB(int a, int b) => ref Tiles[a + 1 + (b + 1) * L14Grid];
        public static bool In(int a, int b) => a >= -1 && b >= -1 && a <= L14WingSize && b <= L14WingSize;
        public (int X, int Z) World(int a, int b) => (Hx * L14Period + 6 + a, Hz * L14Period + 6 + b);
    }

    private PlanCache<L14Plan> l14Plans;

    /// <summary>A wing's plan (shared: read it, never change it).</summary>
    public L14Plan L14PlanOf(int hx, int hz) =>
        LazyInitializer.EnsureInitialized(ref l14Plans, () => new PlanCache<L14Plan>(32, MakeL14Plan)).Get(hx, hz);

    /// <summary>The wing a block position lies in (or whose wall it is), and the place in it; null in a main hall.</summary>
    public static (int Hx, int Hz, int A, int B)? L14WingAt(int gx, int gz)
    {
        int u = Hashing.Mod(gx, L14Period), v = Hashing.Mod(gz, L14Period);
        if (u is >= 1 and <= L14HallWidth || v is >= 1 and <= L14HallWidth) return null;
        int hx = Hashing.FloorDiv(gx, L14Period) - (u == 0 ? 1 : 0), hz = Hashing.FloorDiv(gz, L14Period) - (v == 0 ? 1 : 0);
        return (hx, hz, u == 0 ? L14WingSize : u - 6, v == 0 ? L14WingSize : v - 6);
    }

    /// <summary>How far a block position is from the region's middle, in blocks.</summary>
    public double L14FromMiddle(int gx, int gz)
    {
        double dx = gx - (L14CentreX * MacroSize + MacroSize / 2), dz = gz - (L14CentreZ * MacroSize + MacroSize / 2);
        return Math.Sqrt(dx * dx + dz * dz);
    }

    /// <summary>The middle of the nearest torture chamber within <paramref name="reach"/> blocks of a position (a floor tile in it), or null.</summary>
    public (int X, int Z)? L14TortureNear(int gx, int gz, int reach)
    {
        (int X, int Z)? best = null;
        long bestD = (long)reach * reach;
        int r = reach / L14Period + 1, hx0 = Hashing.FloorDiv(gx, L14Period), hz0 = Hashing.FloorDiv(gz, L14Period);
        for (int hz = hz0 - r; hz <= hz0 + r; hz++)
            for (int hx = hx0 - r; hx <= hx0 + r; hx++)
            {
                int wx = hx * L14Period + 34, wz = hz * L14Period + 34;
                if (LevelAt(MacroOf(wx), MacroOf(wz)) != Level14) continue;
                foreach (var (x, z) in L14PlanOf(hx, hz).TortureSpots)
                {
                    long d = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                    if (d <= bestD && LevelAt(MacroOf(x), MacroOf(z)) == Level14) { bestD = d; best = (x, z); }
                }
            }
        return best;
    }

    // ================= Where it is =================

    /// <summary>
    /// How far out the region's centre lies: 1.35 times the city's distance, 33.75 degrees west of north (between Level 73's 22.5 and the End's 45,
    /// and beyond both).
    /// </summary>
    private double L14Reach => RegionReach * 1.35;

    /// <summary>The region's centre, in macro cells.</summary>
    public int L14CentreX => spawnMacroX - (int)Math.Round(L14Reach * Math.Sin(3 * Math.PI / 16));
    public int L14CentreZ => spawnMacroZ - (int)Math.Round(L14Reach * Math.Cos(3 * Math.PI / 16));

    /// <summary>The region's radius in macro cells: "infinitely segmented", as big as the far places get.</summary>
    public int L14Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL14(double mx, double mz) => InRoundRegion(mx, mz, L14CentreX, L14CentreZ, L14Radius, SaltL14Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L14ArrivalCell(ulong h) => RoundArrivalCell(h, L14CentreX, L14CentreZ, L14Radius);

    /// <summary>Arriving: in a reception room ("in which all of Level 14's entrants will first arrive"), on its open floor.</summary>
    private static bool IsL14ArrivalSpot(Tile t) => IsArrivalSpot(t) && L14ZoneOf(t) == L14Zone.Reception;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L14ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the halls and wings are laid over the edges).</summary>
    private Edge L14Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L14Wall };

    /// <summary>
    /// Lays out one of the level's cells: the main halls from arithmetic, the rest copied from the plans of the wings it covers;
    /// where the region ends, a hallway runs round inside its wall (<see cref="CarveEdgeHall"/>) so nothing is shut off.
    /// </summary>
    private void BuildLevel14(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (L14WingAt(gx, gz) is { } w)
                {
                    t = L14PlanOf(w.Hx, w.Hz).AtAB(w.A, w.B);
                    t.Level = Level14;
                    continue;
                }
                L14HallTile(ref t, gx, gz, Hashing.Mod(gx, L14Period), Hashing.Mod(gz, L14Period));
            }
        bool[] other = WalledNeighbours(Level14, mx, mz);
        if (other == null) return;
        CarveEdgeHall(b, mx, mz, GetEdge(mx, mz, west: true), GetEdge(mx, mz, west: false));
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor || !EdgeHall(other, lx, lz)) continue;
                if (t.Variant == 0)
                {
                    t.Stack = 0;
                    t.SupplyBox = false;
                }
                if (t.Height < 3) t.Height = 3;
                if (L14ZoneOf(t) is L14Zone.Wall or L14Zone.None)
                {
                    t.Zone = (byte)((byte)L14Zone.Corridor | (t.Zone & L14DarkBit));
                    t.Depth = L14FVinylWorn;
                    t.Ceiling = CeilingKind.L14Ceiling;
                }
                t.Overhead = 0;
            }
    }

    /// <summary>Whether a stretch of main hall (between two crossings) has its lights dead: about one in five, never near the middle.</summary>
    public bool L14DarkStretch(bool alongZ, int line, int stretch)
    {
        int gx = alongZ ? line * L14Period : stretch * L14Period + 32, gz = alongZ ? stretch * L14Period + 32 : line * L14Period;
        if (L14FromMiddle(gx, gz) < 200) return false;
        return Hashing.Unit(Hashing.Hash(seed, line, stretch, SaltL14Dark + (alongZ ? 0UL : 1UL))) < 0.2;
    }

    /// <summary>Whether a room (by its middle) is dark: one in eight, never near the middle.</summary>
    private bool L14DarkRoom(int gx, int gz) => L14FromMiddle(gx, gz) >= 160 && Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL14Dark + 7)) < 0.125;

    /// <summary>
    /// A fluorescent troffer by hash ("shadowy hallways"): in the dark dead, now and then still stuttering; elsewhere a share
    /// dead and some failing, the rest giving light (<paramref name="emit"/>) or only looking lit.
    /// </summary>
    private CeilingKind L14Lamp(int gx, int gz, bool emit, bool dark, double dead = 0.25, bool bright = false)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL14Light));
        if (dark) return r < 0.05 ? CeilingKind.L14LightFlicker : CeilingKind.L14LightDead;
        if (r < dead) return CeilingKind.L14LightDead;
        if (r < dead + 0.07) return CeilingKind.L14LightFlicker;
        return emit ? (bright ? CeilingKind.L14LightBright : CeilingKind.L14LightOn) : CeilingKind.L14LightLit;
    }

    /// <summary>A hall line's way-finding colour line: one line in three has a red line painted down it, its arrows toward the region's middle ("arrows on the floor pointing to the main hospital exit").</summary>
    private bool L14LinedHall(bool alongZ, int line) => Hashing.Hash(seed, line, alongZ ? 1 : 0, SaltL14Hall + 3) % 3 == 0;

    /// <summary>A tile of a main hall (along z where x mod 64 is 1-4, along x where z mod 64 is), or of a crossing.</summary>
    private void L14HallTile(ref Tile t, int gx, int gz, int u, int v)
    {
        bool alongZ = u is >= 1 and <= L14HallWidth, alongX = v is >= 1 and <= L14HallWidth;
        int lineX = Hashing.FloorDiv(gx, L14Period), lineZ = Hashing.FloorDiv(gz, L14Period);
        bool dark = alongZ && alongX ? false : alongZ ? L14DarkStretch(true, lineX, lineZ) : L14DarkStretch(false, lineZ, lineX);
        t.Kind = TileKind.Floor;
        t.Level = Level14;
        t.Floor = FloorKind.L14Floor;
        t.Ceiling = CeilingKind.L14Ceiling;
        t.Pattern = WallPattern.L14Wall;
        t.Zone = (byte)((byte)L14Zone.Hall | (dark ? L14DarkBit : 0));
        t.Height = L14HallHeight;
        ulong h = Hashing.Hash(seed, gx, gz, SaltL14Hall);
        double p = Hashing.Unit(h);
        t.Depth = p < 0.12 ? L14FVinylWorn : L14FVinyl;
        if (alongZ && alongX)
        {
            if (u is 2 or 3 && v is 2 or 3) t.Ceiling = L14Lamp(gx, gz, u == 2 && v == 2, false, 0.15);
            if (p > 0.995) t.Depth = L14FCracked;
            return;
        }
        int across = alongZ ? u : v, along = alongZ ? gz : gx, stretch = Hashing.Mod(along, L14Period);
        t.Pier = alongZ ? ArchPier.North : ArchPier.East;
        if (across is 1 or L14HallWidth) t.Depth = L14FBorder;
        // A pair of troffers across the middle every eight blocks (one of the pair giving light), a stained or missing tile now and then
        double c = Hashing.Unit(Hashing.Mix(h));
        if (across is 2 or 3 && Hashing.Mod(along, 8) == 4) t.Ceiling = L14Lamp(gx, gz, across == 2, dark, 0.42);
        else if (c < 0.06) t.Ceiling = CeilingKind.L14CeilingStained;
        else if (c > 0.992) t.Ceiling = CeilingKind.L14CeilingHole;
        // The way-finding line down one lane, an arrow every sixteen blocks pointing toward the middle of the region
        if (across == 2 && L14LinedHall(alongZ, alongZ ? lineX : lineZ) && t.Depth == L14FVinyl)
        {
            if (Hashing.Mod(along, 16) == 8)
            {
                int toward = alongZ ? L14CentreZ * MacroSize - gz : L14CentreX * MacroSize - gx;
                t.Depth = alongZ ? (toward < 0 ? L14FArrowN : L14FArrowS) : (toward < 0 ? L14FArrowW : L14FArrowE);
            }
            else t.Depth = alongZ ? L14FLineNS : L14FLineWE;
        }
        // A department sign hung across the hall a few blocks before each crossing
        if (across == 2 && stretch is 8 or 61)
        {
            t.Overhead = Overheads.L14HangSign;
            t.Stack = (byte)(Hashing.Hash(seed, lineX * 7 + (alongZ ? 1 : 0), lineZ * 13 + (stretch < 32 ? 0 : 1), SaltL14Hall + 4) % 8);
            return;
        }
        if (p > 0.996 && across is 2 or 3) { t.Depth = L14FCracked; return; }
        // A gurney left along a wall (round 4): two tiles, its head at an even step and its foot at the odd one after it
        if (across is 1 or L14HallWidth && stretch is >= 12 and <= 53)
        {
            int a0 = along - Hashing.Mod(along, 2);
            int hx = alongZ ? gx : a0, hz = alongZ ? a0 : gz, fx = alongZ ? gx : a0 + 1, fz = alongZ ? a0 + 1 : gz;
            if (Hashing.Unit(Hashing.Hash(seed, hx, hz, SaltL14HallProp + 9)) < 0.03 && Hashing.Mod(a0, 8) != 4 && Hashing.Mod(a0 + 1, 8) != 4
                && !L14DoorBeside(hx, hz, alongZ, across == 1) && !L14DoorBeside(fx, fz, alongZ, across == 1))
            {
                t.Variant = Props.L14Gurney;
                t.Pier = alongZ ? ArchPier.South : ArchPier.East;
                t.Stack = (byte)(along == a0 ? 0 : 1);
                return;
            }
        }
        // What was left in the halls, against the walls: gurneys, wheelchairs, drip stands, linen carts, benches
        if (across is 1 or L14HallWidth && stretch is >= 10 and <= 55)
        {
            double q = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL14HallProp));
            if (q >= 0.022) return;
            ArchPier into = alongZ ? (across == 1 ? ArchPier.East : ArchPier.West) : (across == 1 ? ArchPier.South : ArchPier.North);
            ArchPier run = alongZ ? ArchPier.South : ArchPier.East;
            if (L14DoorBeside(gx, gz, alongZ, across == 1)) return;
            if (q < 0.006) { t.Variant = Props.L14Wheelchair; t.Pier = (ArchPier)(Hashing.Mix(h) % 4); }
            else if (q < 0.010) { t.Variant = Props.L14IvStand; t.Pier = into; }
            else if (q < 0.013) { t.Variant = Props.L14LinenCart; t.Pier = run; }
            else if (q < 0.017 && Hashing.Mod(along, 8) != 4) { t.Variant = Props.L14Bench; t.Pier = into; }
            else if (q < 0.020) { t.Variant = Props.RunCrashCart; t.Pier = into; }
            else t.Variant = Props.L14BloodPool;
        }
    }

    /// <summary>Whether the wall beside a main hall tile has a doorway in it (or in the tile either side along it).</summary>
    private bool L14DoorBeside(int gx, int gz, bool alongZ, bool low)
    {
        for (int k = -1; k <= 1; k++)
        {
            int x = alongZ ? gx + (low ? -1 : 1) : gx + k, z = alongZ ? gz + k : gz + (low ? -1 : 1);
            if (L14WingAt(x, z) is not { } w) continue;
            if (L14PlanOf(w.Hx, w.Hz).AtAB(w.A, w.B).Kind == TileKind.Doorway) return true;
        }
        return false;
    }

    // ================= A wing =================

    private L14Plan MakeL14Plan(int hx, int hz)
    {
        var plan = new L14Plan { Hx = hx, Hz = hz };
        double d = Hashing.Unit(Hashing.Hash(seed, hx, hz, SaltL14Dept));
        plan.Dept = d < 0.30 ? L14Dept.Medical : d < 0.45 ? L14Dept.Icu : d < 0.57 ? L14Dept.Psych : d < 0.70 ? L14Dept.Maternity : d < 0.84 ? L14Dept.Surgery : L14Dept.Stores;
        new L14Work(this, plan, Hashing.Hash(seed, hx, hz, SaltL14Wing)).Lay();
        L14LinkPlan(plan);
        return plan;
    }

    /// <summary>Level 14's ways out laid into a wing after it is planned (WorldLayout.Level14.Links.cs).</summary>
    partial void L14LinkPlan(L14Plan plan);

    private sealed class L14Work
    {
        private const int N = L14WingSize, MinLeaf = 8;
        private static readonly (int Dx, int Dz, ArchPier Out)[] Dirs =
            { (-1, 0, ArchPier.West), (1, 0, ArchPier.East), (0, -1, ArchPier.North), (0, 1, ArchPier.South) };

        private readonly WorldLayout layout;
        private readonly L14Plan plan;
        private Rng rng;
        private readonly List<(int X0, int Z0, int X1, int Z1)> leaves = new();
        private readonly List<RoomBox> rooms = new();
        /// <summary>Round 4: what a room's furnishing adds after all of its draws (run by <see cref="Furnish"/> before Unblock).</summary>
        private readonly List<Action> later = new();

        public L14Work(WorldLayout layout, L14Plan plan, ulong seed)
        {
            this.layout = layout;
            this.plan = plan;
            rng = new Rng(seed);
        }

        private ref Tile At(int a, int b) => ref plan.AtAB(a, b);

        public void Lay()
        {
            for (int i = 0; i < plan.Tiles.Length; i++)
                plan.Tiles[i] = new Tile
                {
                    Kind = TileKind.Wall, Pattern = WallPattern.L14Wall, Floor = FloorKind.L14Floor, Ceiling = CeilingKind.L14Ceiling,
                    Zone = (byte)L14Zone.Wall, Height = 3, Level = Level14, Depth = L14MPaint,
                };
            Split(0, 0, N - 1, N - 1, 0);
            foreach (var l in leaves) Strip(l.X0, l.Z0, l.X1, l.Z1);
            Assign();
            foreach (var r in rooms) Furnish(r);
            HallWalls();
            CorridorWalls();
            HallFittings();
        }

        // ---------------- The cuts ----------------

        private void Split(int x0, int z0, int x1, int z1, int depth)
        {
            int w = x1 - x0 + 1, d = z1 - z0 + 1, big = Math.Max(w, d);
            bool can = big >= 2 * MinLeaf + 3;
            bool stop = !can || depth >= 1 && (big <= 22 || big <= 34 && rng.Chance(0.6));
            if (stop)
            {
                leaves.Add((x0, z0, x1, z1));
                return;
            }
            bool acrossX = w > d || w == d && rng.Chance(0.5);
            const int cw = 3;
            int lo = acrossX ? x0 : z0, hi = acrossX ? x1 : z1;
            int s = rng.Range(lo + MinLeaf, hi - MinLeaf - cw + 1);
            Cut(acrossX, s, cw, acrossX ? z0 : x0, acrossX ? z1 : x1);
            if (acrossX)
            {
                Split(x0, z0, s - 1, z1, depth + 1);
                Split(s + cw, z0, x1, z1, depth + 1);
            }
            else
            {
                Split(x0, z0, x1, s - 1, depth + 1);
                Split(x0, s + cw, x1, z1, depth + 1);
            }
        }

        /// <summary>Carves a corridor across a piece and opens its ends onto whatever corridor (or main hall, through the wing's wall) lies beyond.</summary>
        private void Cut(bool alongZ, int s, int cw, int from, int to)
        {
            for (int k = from; k <= to; k++)
                for (int i = 0; i < cw; i++)
                {
                    int a = alongZ ? s + i : k, b = alongZ ? k : s + i;
                    CorridorTile(ref At(a, b), a, b, alongZ, i, alongZ ? b : a);
                }
            for (int i = 0; i < cw; i++)
                foreach (int dir in new[] { -1, 1 })
                {
                    int k = dir < 0 ? from - 1 : to + 1;
                    for (int step = 0; step < 2; step++, k += dir)
                    {
                        int a = alongZ ? s + i : k, b = alongZ ? k : s + i;
                        if (!L14Plan.In(a, b)) break;
                        ref Tile t = ref At(a, b);
                        if (t.Kind == TileKind.Floor) break;
                        bool wingWall = a is -1 or N || b is -1 or N;
                        CorridorTile(ref t, a, b, alongZ, i, alongZ ? b : a);
                        if (wingWall)
                        {
                            // Through the wing's wall onto the hall: a doorway with fire doors propped open
                            t.Kind = TileKind.Doorway;
                            t.Detail = L14DoorFire;
                            t.Stack = (byte)(i == 0 ? 0 : i == cw - 1 ? 1 : 2);
                            t.Pier = alongZ ? (dir < 0 ? ArchPier.North : ArchPier.South) : (dir < 0 ? ArchPier.West : ArchPier.East);
                            break;
                        }
                    }
                }
        }

        private void CorridorTile(ref Tile t, int a, int b, bool alongZ, int i, int along)
        {
            var (x, z) = plan.World(a, b);
            bool dark = layout.L14DarkRoom(x & ~31, z & ~31) && layout.L14FromMiddle(x, z) > 220;
            t.Kind = TileKind.Floor;
            t.Zone = (byte)((byte)L14Zone.Corridor | (dark ? L14DarkBit : 0));
            t.Height = 3;
            t.Pier = alongZ ? ArchPier.North : ArchPier.East;
            t.Variant = 0;
            t.Detail = 0;
            t.Overhead = 0;
            ulong h = Hashing.Hash(layout.seed, x, z, SaltL14Hall + 1);
            double p = Hashing.Unit(h);
            t.Depth = i != 1 ? L14FBorder : p < 0.15 ? L14FVinylWorn : L14FVinyl;
            t.Ceiling = i == 1 && Hashing.Mod(along, 6) == 3 ? layout.L14Lamp(x, z, true, dark, 0.3)
                : Hashing.Unit(Hashing.Mix(h)) < 0.08 ? CeilingKind.L14CeilingStained : CeilingKind.L14Ceiling;
            if (i == 1 && p > 0.994) t.Depth = L14FCracked;
            // Left in the corridors: a wheelchair, a drip stand, a linen cart, a crash cart against the wall
            if (i != 1 && p < 0.012)
            {
                double q = Hashing.Unit(Hashing.Mix(h + 3));
                t.Variant = q < 0.35 ? Props.L14Wheelchair : q < 0.65 ? Props.L14IvStand : q < 0.8 ? Props.L14LinenCart : Props.RunCrashCart;
                t.Pier = alongZ ? (i == 0 ? ArchPier.East : ArchPier.West) : (i == 0 ? ArchPier.South : ArchPier.North);
            }
        }

        // ---------------- The rooms ----------------

        private sealed class RoomBox
        {
            public int X0, Z0, X1, Z1;
            /// <summary>The side its door is on (0 west, 1 east, 2 north, 3 south), and its sides that open on a corridor or hall.</summary>
            public int Front;
            public readonly List<int> Open = new();
            public L14Zone Kind;
            public bool Dark, Contam;
            public int W => X1 - X0 + 1;
            public int D => Z1 - Z0 + 1;
            public bool Inside(int a, int b) => a >= X0 && a <= X1 && b >= Z0 && b <= Z1;
        }

        /// <summary>Whether the tile beyond a wall tile on a side is a corridor, or the hall beyond the wing's wall.</summary>
        private bool OpenBeyond(int side, int a, int b)
        {
            if (!L14Plan.In(a, b)) return false;
            if (a is -1 or N || b is -1 or N) return true; // the wing's wall: the hall is beyond
            var (dx, dz, _) = Dirs[side];
            int na = a + dx, nb = b + dz;
            if (!L14Plan.In(na, nb)) return false;
            return At(na, nb).Kind == TileKind.Floor && L14ZoneOf(At(na, nb)) == L14Zone.Corridor;
        }

        /// <summary>
        /// Turns a piece between the cuts into a strip of rooms side by side along its longer way (two strips back to back when it
        /// is deep), with walls between; the piece's edges on a corridor are the rooms' walls, its edges on the wing's wall are that.
        /// </summary>
        private void Strip(int x0, int z0, int x1, int z1)
        {
            int ix0 = x0 == 0 ? 0 : x0 + 1, ix1 = x1 == N - 1 ? N - 1 : x1 - 1, iz0 = z0 == 0 ? 0 : z0 + 1, iz1 = z1 == N - 1 ? N - 1 : z1 - 1;
            if (ix1 - ix0 < 2 || iz1 - iz0 < 2) return;
            bool alongX = ix1 - ix0 >= iz1 - iz0;
            int acrossLo = alongX ? iz0 : ix0, acrossHi = alongX ? iz1 : ix1, across = acrossHi - acrossLo + 1;
            var bands = new List<(int Lo, int Hi, int Front)>();
            int sideLo = alongX ? 2 : 0, sideHi = alongX ? 3 : 1;
            if (across >= 14)
            {
                int mid = acrossLo + across / 2;
                bands.Add((acrossLo, mid - 1, sideLo));
                bands.Add((mid + 1, acrossHi, sideHi));
            }
            else bands.Add((acrossLo, acrossHi, rng.Chance(0.5) ? sideLo : sideHi));
            int lenLo = alongX ? ix0 : iz0, lenHi = alongX ? ix1 : iz1;
            foreach (var band in bands)
            {
                int k = lenLo;
                while (k <= lenHi)
                {
                    int left = lenHi - k + 1;
                    int w = left <= 13 ? left : Math.Min(left - 5, rng.Range(4, 12));
                    var r = alongX ? new RoomBox { X0 = k, X1 = k + w - 1, Z0 = band.Lo, Z1 = band.Hi } : new RoomBox { X0 = band.Lo, X1 = band.Hi, Z0 = k, Z1 = k + w - 1 };
                    r.Front = band.Front;
                    for (int s = 0; s < 4; s++)
                    {
                        var (ea, eb) = EdgeTile(r, s);
                        if (OpenBeyond(s, ea, eb)) r.Open.Add(s);
                    }
                    if (!r.Open.Contains(r.Front) && r.Open.Count > 0) r.Front = r.Open[rng.Range(0, r.Open.Count - 1)];
                    if (r.Open.Count > 0 && r.W >= 2 && r.D >= 2) rooms.Add(r);
                    else Seal(r);
                    k += w + 1;
                }
            }
        }

        /// <summary>The wall tile just outside the middle of a room's side.</summary>
        private static (int A, int B) EdgeTile(RoomBox r, int side) => side switch
        {
            0 => (r.X0 - 1, (r.Z0 + r.Z1) / 2), 1 => (r.X1 + 1, (r.Z0 + r.Z1) / 2), 2 => ((r.X0 + r.X1) / 2, r.Z0 - 1), _ => ((r.X0 + r.X1) / 2, r.Z1 + 1),
        };

        /// <summary>Gives every room its kind: one reception (always near the middle), the department's rooms, now and then a torture chamber or the research group's remains.</summary>
        private void Assign()
        {
            var (cx, cz) = plan.World(N / 2, N / 2);
            double from = layout.L14FromMiddle(cx, cz);
            if (rng.Chance(from < 400 ? 1.0 : 0.6))
            {
                var fits = rooms.FindAll(r => Math.Min(r.W, r.D) >= 6 && Math.Max(r.W, r.D) <= 18);
                if (fits.Count > 0)
                {
                    fits[rng.Range(0, fits.Count - 1)].Kind = L14Zone.Reception;
                    plan.Receptions++;
                }
            }
            if (from > 160 && rng.Chance(0.07))
            {
                RoomBox best = null;
                foreach (var r in rooms) if (r.Kind == L14Zone.None && Math.Min(r.W, r.D) >= 7 && (best == null || r.W * r.D > best.W * best.D)) best = r;
                if (best != null) { best.Kind = L14Zone.Research; plan.Research++; }
            }
            foreach (var r in rooms)
            {
                if (r.Kind != L14Zone.None) continue;
                if (Math.Min(r.W, r.D) >= 5 && from > 200 && rng.Chance(0.02)) { r.Kind = L14Zone.Torture; continue; }
                r.Kind = PickKind(r.W, r.D);
            }
            foreach (var r in rooms)
            {
                var (mx, mz) = plan.World((r.X0 + r.X1) / 2, (r.Z0 + r.Z1) / 2);
                r.Dark = r.Kind is not (L14Zone.Reception or L14Zone.Torture) && layout.L14DarkRoom(mx, mz);
                r.Contam = r.Kind is L14Zone.Ward or L14Zone.Storage or L14Zone.Office or L14Zone.Blank or L14Zone.Surgery
                    && layout.L14FromMiddle(mx, mz) > 120 && rng.Chance(0.06);
            }
        }

        private L14Zone PickKind(int w, int d)
        {
            int small = Math.Min(w, d);
            double p = rng.NextDouble();
            if (small <= 3) return p < 0.6 ? L14Zone.Storage : L14Zone.Blank;
            switch (plan.Dept)
            {
                case L14Dept.Medical:
                    return p < 0.56 ? L14Zone.Ward : p < 0.70 ? L14Zone.Office : p < 0.82 ? L14Zone.Storage : p < 0.86 ? L14Zone.Surgery : p < 0.9 ? L14Zone.Icu : L14Zone.Blank;
                case L14Dept.Icu:
                    return p < 0.6 ? L14Zone.Icu : p < 0.7 ? L14Zone.Ward : p < 0.8 ? L14Zone.Storage : p < 0.92 ? L14Zone.Office : L14Zone.Surgery;
                case L14Dept.Psych:
                    return p < 0.65 ? L14Zone.Psych : p < 0.8 ? L14Zone.Office : p < 0.9 ? L14Zone.Storage : L14Zone.Ward;
                case L14Dept.Maternity:
                    return p < 0.62 ? L14Zone.Maternity : p < 0.75 ? L14Zone.Ward : p < 0.87 ? L14Zone.Office : L14Zone.Storage;
                case L14Dept.Surgery:
                    return small >= 6 && p < 0.42 ? L14Zone.Surgery : p < 0.6 ? L14Zone.Storage : p < 0.75 ? L14Zone.Icu : p < 0.9 ? L14Zone.Office : L14Zone.Blank;
                default:
                    return p < 0.72 ? L14Zone.Storage : p < 0.82 ? L14Zone.Office : p < 0.9 ? L14Zone.Ward : L14Zone.Blank;
            }
        }

        private void Furnish(RoomBox r)
        {
            plan.Rooms++;
            bool tall = r.Kind is L14Zone.Reception or L14Zone.Surgery or L14Zone.Research or L14Zone.Torture;
            bool inpatient = r.Kind is L14Zone.Ward or L14Zone.Icu or L14Zone.Psych or L14Zone.Maternity;
            byte zone = (byte)((byte)r.Kind | (r.Dark ? L14DarkBit : 0) | (r.Contam ? L14ContamBit : 0));
            byte floor = r.Kind switch
            {
                L14Zone.Reception => L14FTerrazzo,
                L14Zone.Ward or L14Zone.Icu or L14Zone.Psych => L14FWhite,
                L14Zone.Maternity => L14FPink,
                L14Zone.Surgery => L14FTheatre,
                L14Zone.Storage => L14FConcrete,
                L14Zone.Torture => L14FMarbleShattered,
                L14Zone.Research => L14FVinylWorn,
                _ => L14FVinyl,
            };
            int lampStep = inpatient ? 3 : 4;
            for (int b = r.Z0; b <= r.Z1; b++)
                for (int a = r.X0; a <= r.X1; a++)
                {
                    ref Tile t = ref At(a, b);
                    var (x, z) = plan.World(a, b);
                    t.Kind = TileKind.Floor;
                    t.Zone = zone;
                    t.Height = (byte)(tall ? 4 : 3);
                    t.Detail = 0;
                    t.Depth = floor;
                    if (floor == L14FTerrazzo && rng.Chance(0.04)) t.Depth = L14FCracked;
                    if (r.Kind == L14Zone.Torture && rng.Chance(0.4)) t.Depth = rng.Chance(0.6) ? L14FMarble : L14FBlood;
                    if (r.Contam && rng.Chance(0.35)) t.Depth = L14FContam;
                    bool lamp = Hashing.Mod(a - r.X0 - (r.W % lampStep) / 2, lampStep) == lampStep / 2 && Hashing.Mod(b - r.Z0 - (r.D % lampStep) / 2, lampStep) == lampStep / 2;
                    t.Ceiling = r.Kind switch
                    {
                        // One bare light burning in the middle, the rest stuttering or dead
                        L14Zone.Torture => a == (r.X0 + r.X1) / 2 && b == (r.Z0 + r.Z1) / 2 ? CeilingKind.L14LightOn
                            : lamp ? (rng.Chance(0.5) ? CeilingKind.L14LightFlicker : CeilingKind.L14LightDead) : rng.Chance(0.35) ? CeilingKind.L14CeilingBlood : CeilingKind.L14CeilingConcrete,
                        L14Zone.Surgery => lamp ? layout.L14Lamp(x, z, true, r.Dark, 0.2) : CeilingKind.L14CeilingPlaster,
                        L14Zone.Storage => lamp ? layout.L14Lamp(x, z, true, r.Dark, 0.35) : CeilingKind.L14CeilingConcrete,
                        _ => lamp ? layout.L14Lamp(x, z, true, r.Dark, inpatient ? 0.08 : 0.25, inpatient) : rng.Chance(0.07) ? CeilingKind.L14CeilingStained : CeilingKind.L14Ceiling,
                    };
                    if (r.Contam && !lamp && rng.Chance(0.2)) t.Ceiling = CeilingKind.L14CeilingMould;
                }
            RoomWalls(r);
            var doors = new List<int>();
            if (Door(r, r.Front, r.Kind is L14Zone.Reception or L14Zone.Research ? 2 : 1, zone)) doors.Add(r.Front);
            // A second door in a big room, or a contaminated room's way in beside the door you look through
            if (r.Open.Count > 1 && (r.W * r.D > 120 && rng.Chance(0.5) || r.Contam || doors.Count == 0))
            {
                var others = r.Open.FindAll(s => s != r.Front);
                int second = others[rng.Range(0, others.Count - 1)];
                if (Door(r, second, 1, zone)) doors.Add(second);
            }
            if (doors.Count == 0) { Seal(r); plan.Rooms--; return; }
            if (r.Contam && doors.Count > 1) SetDoor(r, doors[0], L14DoorContam);
            switch (r.Kind)
            {
                case L14Zone.Reception: Reception(r, doors[0]); break;
                case L14Zone.Ward: Ward(r, doors[0], false, false); break;
                case L14Zone.Icu: Ward(r, doors[0], true, false); break;
                case L14Zone.Maternity: Ward(r, doors[0], false, true); break;
                case L14Zone.Psych: Psych(r, doors[0]); break;
                case L14Zone.Surgery: Surgery(r, doors[0]); break;
                case L14Zone.Storage: Storage(r); break;
                case L14Zone.Torture: Torture(r); break;
                case L14Zone.Research: Research(r); break;
                case L14Zone.Office: Office(r, doors[0]); break;
                default: Blank(r); break;
            }
            if (inpatient) Windows(r);
            if (r.Contam) Contaminate(r);
            foreach (var act in later) act();
            later.Clear();
            Unblock(r);
        }

        /// <summary>Whether a room tile can be walked on (open floor, or something walked through).</summary>
        private bool Walkable(int a, int b)
        {
            Tile t = At(a, b);
            return t.Kind == TileKind.Floor && !t.SupplyBox && !(t.Variant == 0 && t.Stack > 0) && IsWalkThroughProp(t.Variant);
        }

        /// <summary>
        /// Clears whatever cuts part of a room off from its doors: walks from the doors, and while some open floor is not reached,
        /// takes away a thing standing between the reached and the unreached (both halves of a bed), and walks again.
        /// </summary>
        private void Unblock(RoomBox r)
        {
            for (int round = 0; round < 40; round++)
            {
                var seen = new HashSet<(int, int)>();
                var queue = new Queue<(int, int)>();
                for (int b = r.Z0; b <= r.Z1; b++)
                    for (int a = r.X0; a <= r.X1; a++)
                        if (NextToWayIn(a, b) && Walkable(a, b) && seen.Add((a, b))) queue.Enqueue((a, b));
                while (queue.Count > 0)
                {
                    var (a, b) = queue.Dequeue();
                    foreach (var (dx, dz, _) in Dirs)
                    {
                        int na = a + dx, nb = b + dz;
                        if (!r.Inside(na, nb) || seen.Contains((na, nb)) || !Walkable(na, nb)) continue;
                        seen.Add((na, nb));
                        queue.Enqueue((na, nb));
                    }
                }
                if (seen.Count == 0) return;
                // A blocker touching the reached part with open, unreached floor beyond it
                (int A, int B)? cut = null;
                for (int b = r.Z0; b <= r.Z1 && cut == null; b++)
                    for (int a = r.X0; a <= r.X1 && cut == null; a++)
                    {
                        if (Walkable(a, b) || At(a, b).Kind is not (TileKind.Floor or TileKind.Wall) || At(a, b).Variant == Props.L14Revolving) continue;
                        bool touchSeen = false, touchLost = false;
                        foreach (var (dx, dz, _) in Dirs)
                        {
                            int na = a + dx, nb = b + dz;
                            if (!r.Inside(na, nb)) continue;
                            if (seen.Contains((na, nb))) touchSeen = true;
                            else if (Walkable(na, nb)) touchLost = true;
                        }
                        if (touchSeen && touchLost) cut = (a, b);
                    }
                if (cut == null)
                {
                    // Two things deep: the blocker by the reached part nearest any open floor still cut off
                    var lost = new List<(int, int)>();
                    for (int b = r.Z0; b <= r.Z1; b++)
                        for (int a = r.X0; a <= r.X1; a++)
                            if (Walkable(a, b) && !seen.Contains((a, b))) lost.Add((a, b));
                    if (lost.Count == 0) return;
                    int best = int.MaxValue;
                    for (int b = r.Z0; b <= r.Z1; b++)
                        for (int a = r.X0; a <= r.X1; a++)
                        {
                            if (Walkable(a, b) || At(a, b).Kind is not (TileKind.Floor or TileKind.Wall) || At(a, b).Variant == Props.L14Revolving) continue;
                            bool touch = false;
                            foreach (var (dx, dz, _) in Dirs) touch |= seen.Contains((a + dx, b + dz));
                            if (!touch) continue;
                            foreach (var (la, lb) in lost)
                            {
                                int d = Math.Abs(la - a) + Math.Abs(lb - b);
                                if (d < best) { best = d; cut = (a, b); }
                            }
                        }
                    if (cut == null) return;
                }
                Clear(cut.Value.A, cut.Value.B);
            }
        }

        /// <summary>Whether a tile is beside a doorway one can go through (not a contaminated room's window door).</summary>
        private bool NextToWayIn(int a, int b)
        {
            foreach (var (dx, dz, _) in Dirs)
                if (L14Plan.In(a + dx, b + dz) && At(a + dx, b + dz) is { Kind: TileKind.Doorway } d && d.Detail != L14DoorContam) return true;
            return false;
        }

        /// <summary>Takes a thing off a floor tile (and the other half of a two-tile one).</summary>
        private void Clear(int a, int b)
        {
            ref Tile t = ref At(a, b);
            if (t.Kind == TileKind.Wall)
            {
                // One of a store's thrown-together walls: floor again, like the floor beside it
                foreach (var (ex, ez, _) in Dirs)
                    if (L14Plan.In(a + ex, b + ez) && At(a + ex, b + ez).Kind == TileKind.Floor && L14IsRoom(L14ZoneOf(At(a + ex, b + ez))))
                    {
                        Tile n = At(a + ex, b + ez);
                        t.Kind = TileKind.Floor;
                        t.Zone = n.Zone;
                        t.Depth = n.Depth;
                        t.Height = n.Height;
                        t.Ceiling = n.Ceiling is CeilingKind.L14LightOn or CeilingKind.L14LightBright ? CeilingKind.L14Ceiling : n.Ceiling;
                        t.Detail = 0;
                        break;
                    }
                return;
            }
            ushort v = t.Variant;
            ArchPier pier = t.Pier;
            byte stack = t.Stack;
            t.Variant = 0;
            t.Stack = 0;
            t.Detail = 0;
            t.SupplyBox = false;
            if (v is not (Props.L14Bed or Props.L14StrapBed or Props.L14OpTable or Props.RunSafeCot or Props.L14Gurney)) return;
            var (dx, dz) = Step(pier);
            int oa = stack == 0 ? a + dx : a - dx, ob = stack == 0 ? b + dz : b - dz;
            if (L14Plan.In(oa, ob) && At(oa, ob).Variant == v)
            {
                At(oa, ob).Variant = 0;
                At(oa, ob).Stack = 0;
                At(oa, ob).Detail = 0;
                if (v == Props.L14OpTable) At(a, b).Overhead = At(oa, ob).Overhead = 0;
            }
        }

        /// <summary>A room no door could be cut into: left as solid wall (nobody gets in, nothing is lost).</summary>
        private void Seal(RoomBox r)
        {
            for (int b = r.Z0; b <= r.Z1; b++)
                for (int a = r.X0; a <= r.X1; a++)
                {
                    ref Tile t = ref At(a, b);
                    t = new Tile
                    {
                        Kind = TileKind.Wall, Pattern = WallPattern.L14Wall, Floor = FloorKind.L14Floor, Ceiling = CeilingKind.L14Ceiling,
                        Zone = (byte)L14Zone.Wall, Height = 3, Level = Level14, Depth = L14MPaint,
                    };
                }
        }

        /// <summary>A room's own walls, by its kind: blinding white (inpatient), tiles (surgery, ICU), quilted (psychiatry), cinder block and plywood thrown together (stores), rust and bloodied tiles (torture).</summary>
        private void RoomWalls(RoomBox r)
        {
            for (int b = r.Z0 - 1; b <= r.Z1 + 1; b++)
                for (int a = r.X0 - 1; a <= r.X1 + 1; a++)
                {
                    if (r.Inside(a, b) || a is -1 or N || b is -1 or N || !L14Plan.In(a, b)) continue;
                    ref Tile t = ref At(a, b);
                    if (t.Kind != TileKind.Wall) continue;
                    byte mat = r.Kind switch
                    {
                        L14Zone.Ward or L14Zone.Maternity => rng.Chance(0.08) ? L14MWhiteMoss : L14MWhite,
                        L14Zone.Icu => rng.Chance(0.5) ? L14MTile : L14MWhite,
                        L14Zone.Psych => Math.Min(r.W, r.D) <= 6 ? L14MPadded : L14MWhite,
                        L14Zone.Surgery => rng.Chance(0.25) ? L14MMould : L14MTile,
                        L14Zone.Storage => rng.Chance(0.45) ? L14MPlywood : rng.Chance(0.6) ? L14MCinder : L14MConcrete,
                        L14Zone.Torture => rng.Chance(0.5) ? L14MRust : L14MTileBlood,
                        L14Zone.Research => L14MConcrete,
                        _ => rng.Chance(0.1) ? L14MMould : L14MPaint,
                    };
                    // A wall between two rooms keeps the stronger of their two looks (a padded cell's quilting, a ward's white)
                    if (WallRank(mat) >= WallRank(t.Depth)) t.Depth = mat;
                }
        }

        private static int WallRank(byte m) => m switch
        {
            L14MRust or L14MTileBlood => 6, L14MPadded => 5, L14MTile => 4, L14MWhite or L14MWhiteMoss => 3, L14MPlywood or L14MCinder or L14MConcrete => 2, L14MMould => 1, _ => 0,
        };

        /// <summary>
        /// Opens a door <paramref name="width"/> wide in a side of the room, through its wall to the corridor beyond (or through
        /// the wing's wall to the hall), and puts the room's plate on the wall beside it, on the outside.
        /// </summary>
        private bool Door(RoomBox r, int side, int width, byte zone)
        {
            var (dx, dz, outward) = Dirs[side];
            bool alongX = side >= 2;
            int lo = alongX ? r.X0 : r.Z0, hi = alongX ? r.X1 : r.Z1;
            if (hi - lo + 1 < width + 2) width = 1;
            if (hi - lo + 1 < 3) return false;
            int edge = side switch { 0 => r.X0 - 1, 1 => r.X1 + 1, 2 => r.Z0 - 1, _ => r.Z1 + 1 };
            for (int tries = 0; tries < 6; tries++)
            {
                int at = rng.Range(lo + 1, hi - width);
                bool ok = true;
                for (int i = 0; i < width && ok; i++)
                {
                    int a = alongX ? at + i : edge, b = alongX ? edge : at + i;
                    if (!L14Plan.In(a, b) || At(a, b).Kind != TileKind.Wall) { ok = false; break; }
                    if (a is -1 or N || b is -1 or N) continue;
                    int na = a + dx, nb = b + dz;
                    if (!L14Plan.In(na, nb) || At(na, nb).Kind != TileKind.Floor || L14ZoneOf(At(na, nb)) != L14Zone.Corridor || At(na, nb).Variant != 0) ok = false;
                }
                if (!ok) continue;
                byte look = r.Kind switch
                {
                    L14Zone.Surgery => rng.Chance(0.1) ? L14DoorLocked : L14DoorClosed,
                    L14Zone.Reception or L14Zone.Torture or L14Zone.Research => L14DoorFrame,
                    L14Zone.Storage or L14Zone.Office => rng.Chance(0.5) ? L14DoorClosed : L14DoorOpen,
                    _ => rng.Chance(0.75) ? L14DoorOpen : L14DoorFrame,
                };
                if (width > 1 && look != L14DoorFrame) look = L14DoorOpen;
                for (int i = 0; i < width; i++)
                {
                    int a = alongX ? at + i : edge, b = alongX ? edge : at + i;
                    ref Tile t = ref At(a, b);
                    t.Kind = TileKind.Doorway;
                    t.Zone = zone;
                    t.Height = 3;
                    t.Detail = look;
                    t.Stack = (byte)(width == 1 ? rng.Range(0, 1) : i == 0 ? 0 : 1);
                    t.Pier = outward;
                    t.Variant = 0;
                    var (ia, ib) = alongX ? (at + i, edge - dz) : (edge - dx, at + i);
                    t.Depth = At(ia, ib).Depth;
                }
                byte plateKind = r.Kind switch
                {
                    L14Zone.Ward => L14PlateWard, L14Zone.Icu => L14PlateIcu, L14Zone.Surgery => L14PlateSurgery, L14Zone.Maternity => L14PlateMaternity,
                    L14Zone.Psych => L14PlatePsych, L14Zone.Storage => L14PlateStorage, L14Zone.Reception => L14PlateReception, L14Zone.Research => L14PlateResearch,
                    L14Zone.Torture => L14PlateDanger, _ => L14PlateOffice,
                };
                if (r.Contam) plateKind = L14PlateBiohazard;
                int k = rng.Chance(0.5) ? at - 1 : at + width;
                var (pa, pb) = alongX ? (k, edge) : (edge, k);
                if (r.Kind != L14Zone.Torture || rng.Chance(0.3)) Decorate(pa, pb, L14DPlate, outward, plateKind);
                return true;
            }
            return false;
        }

        /// <summary>Changes the look of a door already cut (by side).</summary>
        private void SetDoor(RoomBox r, int side, byte look)
        {
            int edge = side switch { 0 => r.X0 - 1, 1 => r.X1 + 1, 2 => r.Z0 - 1, _ => r.Z1 + 1 };
            bool alongX = side >= 2;
            for (int k = alongX ? r.X0 : r.Z0; k <= (alongX ? r.X1 : r.Z1); k++)
            {
                var (a, b) = alongX ? (k, edge) : (edge, k);
                if (L14Plan.In(a, b) && At(a, b).Kind == TileKind.Doorway) At(a, b).Detail = look;
            }
        }

        /// <summary>Puts something on a wall tile's face toward <paramref name="face"/>, if it has nothing on it yet.</summary>
        private bool Decorate(int a, int b, byte what, ArchPier face, byte stack)
        {
            if (!L14Plan.In(a, b)) return false;
            ref Tile t = ref At(a, b);
            if (t.Kind != TileKind.Wall || t.Detail is not (L14DNone or L14DRail)) return false;
            t.Detail = what;
            t.Pier = face;
            t.Stack = stack;
            return true;
        }

        private bool Put(int a, int b, ushort prop, ArchPier pier = ArchPier.North, byte stack = 0, byte detail = 0)
        {
            if (!Free(a, b)) return false;
            ref Tile t = ref At(a, b);
            t.Variant = prop;
            t.Pier = pier;
            t.Stack = stack;
            t.Detail = detail;
            return true;
        }

        private bool Free(int a, int b) =>
            L14Plan.In(a, b) && At(a, b) is { Kind: TileKind.Floor, Variant: 0, SupplyBox: false, Stack: 0 } && !NextToDoor(a, b)
            && L14ZoneOf(At(a, b)) is not (L14Zone.Corridor or L14Zone.Hall);

        private bool NextToDoor(int a, int b)
        {
            foreach (var (dx, dz, _) in Dirs)
                if (L14Plan.In(a + dx, b + dz) && At(a + dx, b + dz).Kind == TileKind.Doorway) return true;
            return false;
        }

        private static ArchPier Opp(ArchPier p) => p switch
        {
            ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East,
        };

        private static (int Dx, int Dz) Step(ArchPier p) => p switch
        {
            ArchPier.West => (-1, 0), ArchPier.East => (1, 0), ArchPier.North => (0, -1), _ => (0, 1),
        };

        /// <summary>The tiles round the inside of a room's walls, each with the way out through the wall beside it.</summary>
        private static IEnumerable<(int A, int B, ArchPier Wall)> Rim(RoomBox r)
        {
            for (int a = r.X0; a <= r.X1; a++)
            {
                yield return (a, r.Z0, ArchPier.North);
                if (r.Z1 != r.Z0) yield return (a, r.Z1, ArchPier.South);
            }
            for (int b = r.Z0 + 1; b < r.Z1; b++)
            {
                yield return (r.X0, b, ArchPier.West);
                if (r.X1 != r.X0) yield return (r.X1, b, ArchPier.East);
            }
        }

        /// <summary>The wall line just outside a room on a side, and a place along it.</summary>
        private static (int A, int B) WallAt(RoomBox r, int side, int k) => side switch
        {
            0 => (r.X0 - 1, r.Z0 + k), 1 => (r.X1 + 1, r.Z0 + k), 2 => (r.X0 + k, r.Z0 - 1), _ => (r.X0 + k, r.Z1 + 1),
        };

        /// <summary>A place in a room counted from a side: <paramref name="k"/> along it, <paramref name="row"/> in from it.</summary>
        private static (int A, int B) FromSide(RoomBox r, int side, int k, int row) => side switch
        {
            0 => (r.X0 + row, r.Z0 + k), 1 => (r.X1 - row, r.Z0 + k), 2 => (r.X0 + k, r.Z0 + row), _ => (r.X0 + k, r.Z1 - row),
        };

        private static int LenOf(RoomBox r, int side) => side >= 2 ? r.W : r.D;
        private static int DepthOf(RoomBox r, int side) => side >= 2 ? r.D : r.W;
        private static int Across(int side) => side switch { 0 => 1, 1 => 0, 2 => 3, _ => 2 };

        /// <summary>The way into the room from a side (the face of something standing against that side's wall).</summary>
        private static ArchPier Into(int side) => Opp(Dirs[side].Out);

        /// <summary>The right-hand way, facing <paramref name="facing"/>.</summary>
        private static (int Dx, int Dz) RightOf(ArchPier facing) => facing switch
        {
            ArchPier.North => (1, 0), ArchPier.East => (0, 1), ArchPier.South => (-1, 0), _ => (0, -1),
        };

        /// <summary>Wall dress inside a room: posters, a clock, a board; blood and mould where the room has gone bad.</summary>
        private void WallDress(RoomBox r, double chance, params (byte What, byte Stack)[] kinds)
        {
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!rng.Chance(chance)) continue;
                var (dx, dz) = Step(wall);
                var k = kinds[rng.Range(0, kinds.Length - 1)];
                Decorate(a + dx, b + dz, k.What, Opp(wall), k.Stack);
            }
        }

        // ---------------- Reception ----------------

        /// <summary>
        /// A reception room ("an oval reception desk, a handful of chairs, and a lamp"): the stained-glass revolving door in the
        /// middle of the back wall (three wide: its back row in the wall, its front row on the floor), the oval desk across the room
        /// facing it (bandages, antibiotics and painkillers on it), rows of chairs along the side walls facing in (crumpled
        /// magazines and soft drink bottles on some), a low table of brochures, a standard lamp in a corner by the door.
        /// </summary>
        private void Reception(RoomBox r, int doorSide)
        {
            int back = Across(doorSide);
            int len = LenOf(r, back), depth = DepthOf(r, back);
            ArchPier fromBack = Into(back), toBack = Dirs[back].Out;
            int mid = len / 2;
            // The revolving door's columns, left to right as seen from the room looking at it (facing toBack)
            var (rx, rz) = RightOf(toBack);
            bool laid = depth >= 5 && len >= 5;
            for (int c = -1; c <= 1 && laid; c++)
            {
                var (wa, wb) = WallAt(r, back, mid + c);
                laid &= L14Plan.In(wa, wb) && At(wa, wb).Kind == TileKind.Wall && At(wa, wb).Detail == L14DNone && wa is not (-1 or N) && wb is not (-1 or N);
            }
            if (laid)
            {
                var (ma, mb) = WallAt(r, back, mid);
                for (int c = -1; c <= 1; c++)
                {
                    var (wa, wb) = WallAt(r, back, mid + c);
                    var (fa, fb) = FromSide(r, back, mid + c, 0);
                    int proj = (wa - ma) * rx + (wb - mb) * rz;
                    byte col = (byte)(proj < 0 ? 0 : proj > 0 ? 2 : 1);
                    ref Tile w = ref At(wa, wb);
                    w.Detail = L14DRevolving;
                    w.Stack = col;
                    w.Pier = fromBack;
                    ref Tile f = ref At(fa, fb);
                    f.Variant = Props.L14Revolving;
                    f.Stack = col;
                    f.Pier = fromBack;
                }
            }
            // The desk: four tiles across the room, its front toward the revolving door
            int deskRow = depth >= 9 ? 4 : 3;
            bool hasDesk = deskRow <= depth - 3 && len >= 8;
            // (Nothing stands at the ends of the desk's row, so the way round it stays open)
            int RowFromBack(int a, int b) => back switch { 0 => a - r.X0, 1 => r.X1 - a, 2 => b - r.Z0, _ => r.Z1 - b };
            if (hasDesk)
            {
                var cells = new List<(int A, int B, int Proj)>();
                for (int k = mid - 2; k < mid + 2; k++)
                {
                    var (a, b) = FromSide(r, back, k, deskRow);
                    // The desk faces fromBack... its front toward the door at the back: it faces toBack's opposite? It faces the revolving door, i.e. toward the back wall
                    var (dxr, dzr) = RightOf(toBack);
                    cells.Add((a, b, a * dxr + b * dzr));
                }
                // Facing toBack, its left end is the one least to its right
                cells.Sort((p, q) => p.Proj.CompareTo(q.Proj));
                bool free = true;
                foreach (var c in cells) free &= Free(c.A, c.B);
                if (free)
                {
                    byte[] parts = { 0, 1, 1, 5 };
                    parts[1 + rng.Range(0, 1)] = 2; // the bandages, antibiotics and painkillers
                    int other = parts[1] == 2 ? 2 : 1;
                    parts[other] = (byte)(rng.Chance(0.5) ? 3 : 4); // a lamp or the phone
                    for (int i = 0; i < 4; i++) Put(cells[i].A, cells[i].B, Props.L14Desk, toBack, parts[i]);
                    var (ca, cb) = FromSide(r, back, mid, deskRow + 1);
                    Put(ca, cb, Props.OfficeChair, toBack);
                }
            }
            // Chairs in rows along the two side walls, facing in
            int sideA = back >= 2 ? 0 : 2, sideB = back >= 2 ? 1 : 3;
            foreach (int s in new[] { sideA, sideB })
            {
                int slen = LenOf(r, s);
                for (int k = 1; k < slen - 1; k++)
                {
                    var (a, b) = FromSide(r, s, k, 0);
                    if (!Free(a, b) || rng.Chance(0.12) || hasDesk && Math.Abs(RowFromBack(a, b) - deskRow) <= 1) continue;
                    double p = rng.NextDouble();
                    Put(a, b, Props.L14WaitChair, Into(s), (byte)(p < 0.55 ? 0 : p < 0.75 ? 1 : p < 0.9 ? 2 : 3));
                }
            }
            for (int tries = 0; tries < 6; tries++)
            {
                var (a, b) = FromSide(r, sideA, rng.Range(2, Math.Max(2, LenOf(r, sideA) - 3)), 1);
                if (hasDesk && Math.Abs(RowFromBack(a, b) - deskRow) <= 1) continue;
                if (Put(a, b, Props.L14MagTable)) break;
            }
            for (int k = rng.Range(1, 3); k > 0; k--)
            {
                int s = rng.Chance(0.5) ? sideA : sideB;
                var (a, b) = FromSide(r, s, rng.Range(1, Math.Max(1, LenOf(r, s) - 2)), 1);
                Put(a, b, Props.L14Sodas);
            }
            foreach (var (a, b) in new[] { FromSide(r, doorSide, 0, 0), FromSide(r, doorSide, LenOf(r, doorSide) - 1, 0) })
                if (Put(a, b, Props.L14FloorLamp, ArchPier.North, 0, 1)) break;
            WallDress(r, 0.08, (L14DPoster, 3), (L14DPoster, 4), (L14DClock, 0), (L14DSanitizer, 0));
            // Round 4 (after the draws): the musty soft drinks came from somewhere: a dead vending machine (the mod's shape) against
            // a side wall by the door, the first free of the two places
            var spots = new[] { (sideA, 1), (sideB, 1), (sideA, LenOf(r, sideA) - 2) };
            later.Add(() =>
            {
                foreach (var (s, k) in spots)
                {
                    var (a, b) = FromSide(r, s, k, 0);
                    if (Put(a, b, Props.L14Vending, Into(s))) break;
                }
            });
        }

        // ---------------- Inpatient rooms ----------------

        /// <summary>
        /// A ward: beds head to the wall down both long sides ("Equipment is situated as if while being used"), curtains on their
        /// rails between, drip stands, monitors, over-bed tables, bedside cabinets; a desk and a cabinet by the door. Intensive
        /// care: fewer beds, each with a monitor and a ventilator, a crash cart. Maternity: a bassinet by each bed, now and then a
        /// teddy bear.
        /// </summary>
        private void Ward(RoomBox r, int doorSide, bool icu, bool maternity)
        {
            int[] sides = doorSide < 2 ? new[] { 2, 3 } : new[] { 0, 1 };
            if (DepthOf(r, sides[0]) < 5) sides = new[] { sides[0] };
            int pitch = icu ? 4 : 3;
            foreach (int s in sides)
            {
                ArchPier into = Into(s);
                int len = LenOf(r, s);
                for (int k = 1; k + 1 < len; k += pitch)
                {
                    var (ha, hb) = FromSide(r, s, k, 0);
                    var (fa, fb) = FromSide(r, s, k, 1);
                    if (!Free(ha, hb) || !Free(fa, fb)) continue;
                    byte made = (byte)(rng.Chance(0.6) ? 0 : 1);
                    Put(ha, hb, Props.L14Bed, into, 0, made);
                    Put(fa, fb, Props.L14Bed, into, 1, made);
                    var (ia, ib) = FromSide(r, s, k - 1, 0);
                    var (ca, cb) = FromSide(r, s, k + 1, 0);
                    if (icu)
                    {
                        Put(ia, ib, Props.L14Monitor, into, 0, (byte)(r.Dark || rng.Chance(0.5) ? 1 : 0));
                        Put(ca, cb, Props.L14Ventilator, into);
                        // Round 4: a drip stand at the bed's side, as if still in use, and a monitor on its arm over the bed's
                        // head, high on the wall behind it (after the room's draws)
                        var (da, db) = FromSide(r, s, k + 1, 1);
                        var (wdx, wdz) = Step(Opp(into));
                        int wa = ha + wdx, wb = hb + wdz;
                        ArchPier bedInto = into;
                        later.Add(() => { Put(da, db, Props.L14IvStand, Opp(bedInto)); Decorate(wa, wb, L14DMonArm, bedInto, 0); });
                    }
                    else
                    {
                        if (rng.Chance(0.6)) Put(ia, ib, rng.Chance(0.6) ? Props.L14IvStand : Props.L14Monitor, into, 0, (byte)(r.Dark || rng.Chance(0.6) ? 1 : 0));
                        if (maternity) Put(ca, cb, Props.L14Crib, into);
                        else if (rng.Chance(0.6)) Put(ca, cb, Props.RunBedside, into);
                    }
                    var (oa, ob) = FromSide(r, s, k + 1, 1);
                    if (!icu && !maternity && rng.Chance(0.35)) Put(oa, ob, Props.L14Overbed, into);
                    if (maternity && rng.Chance(0.12)) { var (ta, tb) = FromSide(r, s, k, 2); Put(ta, tb, Props.L14Teddy, Opp(into)); }
                    // A curtain on its rail between this bed and the next (the length of the bed), most of them drawn
                    if (!icu && k + 2 < len - 1 && rng.Chance(0.6))
                    {
                        var (na, nb) = FromSide(r, s, k + 2, 0);
                        var (ma, mb) = FromSide(r, s, k + 1, 0);
                        ArchPier edge = Toward(na - ma, nb - mb);
                        for (int row = 0; row < 2; row++)
                        {
                            var (ta, tb) = FromSide(r, s, k + 1, row);
                            if (!L14Plan.In(ta, tb) || At(ta, tb).Kind != TileKind.Floor) continue;
                            At(ta, tb).Overhead = Overheads.L14Curtain;
                            At(ta, tb).Roof = (byte)edge;
                        }
                    }
                }
            }
            ArchPier fromDoor = Into(doorSide);
            int dl = LenOf(r, doorSide);
            bool desk = false, cab = false, cart = !icu;
            for (int k = 0; k < dl; k++)
            {
                var (a, b) = FromSide(r, doorSide, k, 0);
                if (!Free(a, b) || rng.Chance(0.4)) continue;
                if (!desk) { desk = Put(a, b, Props.L14Desk2, fromDoor); continue; }
                if (!cab) { cab = Put(a, b, Props.L14Cabinet, fromDoor); continue; }
                if (!cart) { cart = Put(a, b, Props.RunCrashCart, fromDoor); continue; }
                break;
            }
            if (maternity) WallDress(r, 0.06, (L14DPoster, 0), (L14DPoster, 1), (L14DPoster, 2), (L14DClock, 0));
            else WallDress(r, 0.05, (L14DBoard, 0), (L14DClock, 0), (L14DSanitizer, 0), (L14DXray, 0), (L14DPoster, 4));
            Corrosion(r, 0.05);
        }

        /// <summary>Behaviour: a small room is a cell, its walls quilted, a bed with restraint straps; a big one a ward of strapped beds.</summary>
        private void Psych(RoomBox r, int doorSide)
        {
            if (Math.Min(r.W, r.D) <= 6)
            {
                int back = Across(doorSide);
                int mid = LenOf(r, back) / 2;
                var (ha, hb) = FromSide(r, back, mid, 0);
                var (fa, fb) = FromSide(r, back, mid, 1);
                if (Free(ha, hb) && Free(fa, fb))
                {
                    Put(ha, hb, Props.L14StrapBed, Into(back), 0);
                    Put(fa, fb, Props.L14StrapBed, Into(back), 1);
                }
                WallDress(r, 0.05, (L14DScratches, 0));
                return;
            }
            int[] sides = doorSide < 2 ? new[] { 2, 3 } : new[] { 0, 1 };
            foreach (int s in sides)
            {
                int len = LenOf(r, s);
                for (int k = 1; k + 1 < len; k += 3)
                {
                    var (ha, hb) = FromSide(r, s, k, 0);
                    var (fa, fb) = FromSide(r, s, k, 1);
                    if (!Free(ha, hb) || !Free(fa, fb)) continue;
                    Put(ha, hb, Props.L14StrapBed, Into(s), 0);
                    Put(fa, fb, Props.L14StrapBed, Into(s), 1);
                }
            }
            WallDress(r, 0.06, (L14DScratches, 0), (L14DClock, 0), (L14DBoard, 0));
            // Round 4 (after the draws): the ward's night station in the middle, a desk facing the door, a wheelchair left by it
            int ca = (r.X0 + r.X1) / 2, cb = (r.Z0 + r.Z1) / 2;
            later.Add(() =>
            {
                if (Put(ca, cb, Props.L14Desk2, Into(Across(doorSide))))
                {
                    var (dx, dz) = Step(Into(Across(doorSide)));
                    Put(ca - dz, cb + dx, Props.L14Wheelchair, Into(doorSide));
                }
            });
        }

        /// <summary>
        /// Windows onto blackness on an inpatient room's walls ("(shattered) windows of sorts, which exhibit nothing but blackness on
        /// the other side"): on the walls without a door, one in three tiles, never at a corner.
        /// </summary>
        private void Windows(RoomBox r)
        {
            for (int s = 0; s < 4; s++)
            {
                int len = LenOf(r, s);
                bool door = false;
                for (int k = 0; k < len && !door; k++)
                {
                    var (a, b) = WallAt(r, s, k);
                    door = L14Plan.In(a, b) && At(a, b).Kind == TileKind.Doorway;
                }
                if (door) continue;
                for (int k = 1; k < len - 1; k++)
                {
                    if ((k + s) % 3 != 1) continue;
                    var (a, b) = WallAt(r, s, k);
                    // Not in a wall shared with another room (its far face would show the window's plain back in that room)
                    var (ox, oz, _) = Dirs[s];
                    if (L14Plan.In(a + ox, b + oz) && At(a + ox, b + oz) is { Kind: TileKind.Floor or TileKind.Doorway } beyond && L14IsRoom(L14ZoneOf(beyond))) continue;
                    Decorate(a, b, L14DWindow, Into(s), (byte)(rng.Chance(0.4) ? 1 : 0));
                }
            }
        }

        /// <summary>"sparse corrosion and moss": a mould bloom on a wall or two.</summary>
        private void Corrosion(RoomBox r, double chance)
        {
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!rng.Chance(chance * 0.3)) continue;
                var (dx, dz) = Step(wall);
                Decorate(a + dx, b + dz, L14DMould, Opp(wall), 0);
            }
        }

        // ---------------- Surgery ----------------

        /// <summary>
        /// A surgery room ("More often than not ... nothing but a tilted hospital bed and a surgical light"): the operating table
        /// in the middle under its light; usually a trolley of instruments and the anaesthesia machine; in a bigger or older one
        /// shelves of old, damaged equipment, test tubes with moss growing out of them, mould and vegetation over the floor, now
        /// and then little kid posters.
        /// </summary>
        private void Surgery(RoomBox r, int doorSide)
        {
            plan.Surgeries++;
            int back = Across(doorSide);
            int mid = LenOf(r, back) / 2, dmid = Math.Max(1, DepthOf(r, back) / 2);
            ArchPier toDoor = Opp(Into(back));
            var (ha, hb) = FromSide(r, back, mid, dmid - 1);
            var (fa, fb) = FromSide(r, back, mid, dmid);
            if (Free(ha, hb) && Free(fa, fb))
            {
                Put(ha, hb, Props.L14OpTable, Into(back), 0);
                Put(fa, fb, Props.L14OpTable, Into(back), 1);
                At(ha, hb).Overhead = Overheads.L14SurgLamp;
            }
            double decay = rng.NextDouble();
            var (sa, sb) = FromSide(r, back, mid + 1, dmid);
            if (rng.Chance(0.75)) Put(sa, sb, Props.L14Trolley, Opp(toDoor), (byte)(decay > 0.5 ? 1 : 0));
            var (aa, ab) = FromSide(r, back, mid - 1, dmid - 1);
            if (rng.Chance(0.55)) Put(aa, ab, Props.L14Anaesthesia, toDoor);
            if (Math.Min(r.W, r.D) >= 7 || decay > 0.4)
                foreach (var (a, b, wall) in Rim(r))
                {
                    if (!Free(a, b) || rng.Chance(0.6)) continue;
                    double p = rng.NextDouble();
                    if (p < 0.45) Put(a, b, Props.L14EquipShelf, Opp(wall));
                    else if (p < 0.6) Put(a, b, Props.L14TubeRack, Opp(wall));
                    else if (p < 0.7) Put(a, b, Props.RunCrashCart, Opp(wall));
                    else if (p < 0.8) Put(a, b, Props.L14Cabinet, Opp(wall));
                }
            if (decay > 0.55)
            {
                for (int b = r.Z0; b <= r.Z1; b++)
                    for (int a = r.X0; a <= r.X1; a++)
                        if (rng.Chance(0.3)) Put(a, b, rng.Chance(0.55) ? Props.L14Vines : Props.L14MouldFloor);
                Corrosion(r, 0.5);
            }
            if (rng.Chance(0.2)) WallDress(r, 0.12, (L14DPoster, 0), (L14DPoster, 1), (L14DPoster, 2));
            WallDress(r, 0.04, (L14DXray, 0), (L14DClock, 0));
            // Round 4 (after the room's draws): the rest of the set round the table's head, as if the operation were still going
            // on: a monitor on the other side of the head, a drip stand by the anaesthetist
            var (ma, mb) = FromSide(r, back, mid + 1, dmid - 1);
            var (ia, ib) = FromSide(r, back, mid - 1, dmid);
            byte dark = (byte)(r.Dark ? 1 : 0);
            later.Add(() =>
            {
                Put(ma, mb, Props.L14Monitor, toDoor, 0, dark);
                Put(ia, ib, Props.L14IvStand, Opp(toDoor));
            });
        }

        // ---------------- Storage ----------------

        /// <summary>
        /// A storage room: its walls "asymmetrical and ... almost thrown together" (short runs of plywood and cinder block jutting
        /// in from the walls), steel shelving, boxes, linen carts, a folded wheelchair; "extra supplies": a sealed supply box in
        /// one in two.
        /// </summary>
        private void Storage(RoomBox r)
        {
            if (Math.Min(r.W, r.D) >= 5)
                foreach (var (a, b, wall) in Rim(r))
                {
                    if (!Free(a, b) || !rng.Chance(0.18)) continue;
                    int walls = 0;
                    foreach (var (ex, ez, _) in Dirs) if (L14Plan.In(a + ex, b + ez) && At(a + ex, b + ez).Kind == TileKind.Wall) walls++;
                    if (walls > 1) continue; // not at a corner
                    ref Tile t = ref At(a, b);
                    t.Kind = TileKind.Wall;
                    t.Depth = rng.Chance(0.5) ? L14MPlywood : L14MCinder;
                    t.Zone = (byte)L14Zone.Wall;
                }
            bool alongX = r.W >= r.D;
            int across = alongX ? r.D : r.W, len = alongX ? r.W : r.D;
            for (int row = 2; row < across - 2; row += 3)
                for (int k = 2; k < len - 2; k++)
                {
                    if ((k - 2) % 7 == 6) continue;
                    int a = alongX ? r.X0 + k : r.X0 + row, b = alongX ? r.Z0 + row : r.Z0 + k;
                    Put(a, b, Props.Shelf, alongX ? (row % 2 == 0 ? ArchPier.North : ArchPier.South) : (row % 2 == 0 ? ArchPier.West : ArchPier.East));
                }
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!Free(a, b)) continue;
                double p = rng.NextDouble();
                if (p < 0.18) Put(a, b, Props.CardboardBoxes, Opp(wall));
                else if (p < 0.24) At(a, b).Stack = (byte)rng.Range(1, 2);
                else if (p < 0.28) Put(a, b, Props.L14LinenCart, Opp(wall));
                else if (p < 0.30) Put(a, b, Props.L14Wheelchair, Opp(wall));
                else if (p < 0.33) Put(a, b, Props.L14Cabinet, Opp(wall));
            }
            if (rng.Chance(0.5)) SupplyBox(r);
        }

        private void SupplyBox(RoomBox r)
        {
            for (int tries = 0; tries < 10; tries++)
            {
                int a = rng.Range(r.X0, r.X1), b = rng.Range(r.Z0, r.Z1);
                if (!Free(a, b)) continue;
                At(a, b).SupplyBox = true;
                plan.Boxes++;
                return;
            }
        }

        // ---------------- Torture chambers ----------------

        /// <summary>
        /// A torture chamber: "rusted stretchers stacked atop each other, ... blood dripping down the walls and ceiling, and a lining
        /// of a shattered marble floor. Metallic cabinets containing an eerie quantity of stainless knives and razor blades
        /// haphazardly line the walls." Chains and hooks hang in it; its one light stutters.
        /// </summary>
        private void Torture(RoomBox r)
        {
            plan.Tortures++;
            plan.TortureSpots.Add(plan.World((r.X0 + r.X1) / 2, (r.Z0 + r.Z1) / 2));
            foreach (var (a, b, wall) in Rim(r))
            {
                var (dx, dz) = Step(wall);
                if (rng.Chance(0.35)) Decorate(a + dx, b + dz, rng.Chance(0.6) ? L14DBloodDrip : L14DBlood, Opp(wall), 0);
                if (!Free(a, b)) continue;
                double p = rng.NextDouble();
                if (p < 0.3) Put(a, b, Props.L14KnifeCab, Opp(wall));
                else if (p < 0.6) Put(a, b, Props.L14Stretchers, Opp(wall));
                else if (p < 0.7) Put(a, b, Props.L14BloodPool);
            }
            for (int b = r.Z0 + 1; b < r.Z1; b++)
                for (int a = r.X0 + 1; a < r.X1; a++)
                {
                    if (rng.Chance(0.12)) At(a, b).Overhead = Overheads.L14Hook;
                    if (rng.Chance(0.1)) Put(a, b, Props.L14BloodPool);
                }
            // Round 4: "drag those who wander too close ... onto the beds": a gurney with restraints in the middle under a hook,
            // blood under it (placed after the draws above, so the rest of the room is as it was)
            int ga = (r.X0 + r.X1) / 2, gb = (r.Z0 + r.Z1) / 2;
            later.Add(() =>
            {
                if (r.X1 - r.X0 >= 4 && Free(ga, gb) && Free(ga + 1, gb))
                {
                    Put(ga, gb, Props.L14Gurney, ArchPier.East, 0, 1);
                    Put(ga + 1, gb, Props.L14Gurney, ArchPier.East, 1, 1);
                    At(ga, gb).Overhead = Overheads.L14Hook;
                    if (Free(ga, gb + 1)) Put(ga, gb + 1, Props.L14BloodPool);
                }
            });
        }

        // ---------------- The research group's remains ----------------

        /// <summary>
        /// What is left of the T.14.R.G.: field desks (papers, a radio, samples), racks of Compound 14, a containment chamber of glass
        /// broken out from inside, their stockpile of supplies (crates and sealed boxes), cots, their stencil on the walls.
        /// </summary>
        private void Research(RoomBox r)
        {
            int ca = (r.X0 + r.X1) / 2 - 1, cb = (r.Z0 + r.Z1) / 2 - 1;
            int brokenSide = rng.Range(0, 3);
            for (int i = 0; i < 3; i++)
            {
                PutCell(ca + i, cb, ArchPier.North, brokenSide == 2);
                PutCell(ca + i, cb + 2, ArchPier.South, brokenSide == 3);
            }
            PutCell(ca, cb + 1, ArchPier.West, brokenSide == 0);
            PutCell(ca + 2, cb + 1, ArchPier.East, brokenSide == 1);
            plan.NoteSpots.Add(plan.World(ca + 1, cb + 1));
            foreach (var (a, b, wall) in Rim(r))
            {
                var (dx, dz) = Step(wall);
                if (rng.Chance(0.06)) Decorate(a + dx, b + dz, L14DTrg, Opp(wall), 0);
                if (!Free(a, b) || rng.Chance(0.3)) continue;
                double p = rng.NextDouble();
                if (p < 0.25) Put(a, b, Props.L14TrgDesk, Opp(wall), (byte)rng.Range(0, 2));
                else if (p < 0.45) Put(a, b, Props.L14Crate, Opp(wall));
                else if (p < 0.55) Put(a, b, Props.L14SampleRack, Opp(wall));
                else if (p < 0.7) { At(a, b).SupplyBox = true; plan.Boxes++; }
                else if (p < 0.8) Put(a, b, Props.Shelf, Opp(wall));
            }
            var rim = new List<(int A, int B, ArchPier Wall)>(Rim(r));
            for (int k = rng.Range(1, 3); k > 0; k--)
                for (int tries = 0; tries < 8; tries++)
                {
                    var (a, b, wall) = rim[rng.Range(0, rim.Count - 1)];
                    var (dx, dz) = Step(Opp(wall));
                    if (!Free(a, b) || !Free(a + dx, b + dz)) continue;
                    Put(a, b, Props.RunSafeCot, Opp(wall), 0);
                    Put(a + dx, b + dz, Props.RunSafeCot, Opp(wall), 1);
                    break;
                }
        }

        /// <summary>A panel of the containment chamber: its glass along the tile's edge toward <paramref name="edge"/> (Pier).</summary>
        private void PutCell(int a, int b, ArchPier edge, bool broken) => Put(a, b, Props.L14Cell, edge, 0, (byte)(broken ? 1 : 0));

        // ---------------- Offices and the rest ----------------

        /// <summary>A doctor's office or a nurses' room (ours: a "well-equipped hospital"): desks, filing cabinets, a cabinet, an X-ray box, a board; a nurses' counter in a big one.</summary>
        private void Office(RoomBox r, int doorSide)
        {
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!Free(a, b) || rng.Chance(0.6)) continue;
                double p = rng.NextDouble();
                if (p < 0.35) Put(a, b, Props.L14Desk2, Opp(wall));
                else if (p < 0.6) Put(a, b, Props.FilingCabinet, Opp(wall));
                else if (p < 0.75) Put(a, b, Props.L14Cabinet, Opp(wall));
                else if (p < 0.85) Put(a, b, Props.CardboardBoxes, Opp(wall));
                // Round 4: staff lockers (no draw of their own: the same p), placed at the end
                else if (p < 0.95) { int la = a, lb = b; ArchPier lf = Opp(wall); later.Add(() => Put(la, lb, Props.L14Locker, lf, 0, (byte)((la * 7 + lb * 3) % 4 == 0 ? 1 : 0))); }
            }
            if (r.W >= 6 && r.D >= 6 && rng.Chance(0.5))
            {
                // A nurses' counter across the room, its computer in the middle, facing the door
                int back = Across(doorSide);
                ArchPier face = Into(back);   // its front (the ledge) toward the door, the nurse's side toward the back wall
                int row = DepthOf(r, back) / 2, l = LenOf(r, back);
                for (int k = 1; k < l - 1; k++)
                {
                    var (a, b) = FromSide(r, back, k, row);
                    Put(a, b, Props.L14Station, face, (byte)(k == l / 2 ? 1 : 0));
                    // Round 4: its back wall, against the room's back wall: cupboards and pigeonholes, a whiteboard of names
                    // over the middle, chart racks either side (placed at the end)
                    var (ba, bb) = FromSide(r, back, k, 0);
                    byte kind = (byte)(Math.Abs(k - l / 2) <= 1 ? 0 : 1);
                    if (row >= 2) later.Add(() => Put(ba, bb, Props.L14StationBack, face, 0, kind));
                }
            }
            WallDress(r, 0.1, (L14DXray, 0), (L14DBoard, 0), (L14DClock, 0), (L14DPoster, 3), (L14DPoster, 4));
            if (rng.Chance(0.15)) SupplyBox(r);
        }

        /// <summary>An emptied room: a wheelchair or a drip stand left in it, now and then blood, mould, scratches.</summary>
        private void Blank(RoomBox r)
        {
            for (int k = rng.Range(0, 2); k > 0; k--)
            {
                int a = rng.Range(r.X0, r.X1), b = rng.Range(r.Z0, r.Z1);
                Put(a, b, rng.Chance(0.5) ? Props.L14Wheelchair : Props.L14IvStand, (ArchPier)rng.Range(0, 3));
            }
            if (rng.Chance(0.25)) WallDress(r, 0.15, (L14DBlood, 0), (L14DMould, 0), (L14DScratches, 0));
        }

        /// <summary>A contaminated room: leaking drums, glowing stains, mould ("toxic, radioactive substances").</summary>
        private void Contaminate(RoomBox r)
        {
            plan.Contaminated++;
            for (int k = rng.Range(1, 3); k > 0; k--)
                for (int tries = 0; tries < 6; tries++)
                {
                    int a = rng.Range(r.X0, r.X1), b = rng.Range(r.Z0, r.Z1);
                    if (Put(a, b, Props.L14Drum, ArchPier.North, (byte)(rng.Chance(0.7) ? 1 : 0))) break;
                }
            Corrosion(r, 0.6);
        }

        // ---------------- Walls along the halls and corridors ----------------

        /// <summary>The wing's walls along the halls: the handrail at their foot, the department's sign beside each way in, a clock, a sanitizer, an extinguisher, an exit sign now and then.</summary>
        private void HallWalls()
        {
            for (int side = 0; side < 4; side++)
                for (int k = 0; k < N; k++)
                {
                    var (a, b, face) = side switch
                    {
                        0 => (-1, k, ArchPier.West), 1 => (N, k, ArchPier.East), 2 => (k, -1, ArchPier.North), _ => (k, N, ArchPier.South),
                    };
                    ref Tile t = ref At(a, b);
                    if (t.Kind != TileKind.Wall) continue;
                    t.Depth = L14MPaint;
                    var (rx, rz) = side < 2 ? (0, 1) : (1, 0);
                    bool Door(int s) => L14Plan.In(a + s * rx, b + s * rz) && At(a + s * rx, b + s * rz).Kind == TileKind.Doorway;
                    if (!Door(1) && !Door(-1) && (Door(2) || Door(-2))) { Decorate(a, b, L14DSign, face, SignOf(plan.Dept)); continue; }
                    double p = rng.NextDouble();
                    byte what = p < 0.01 ? L14DClock : p < 0.02 ? L14DSanitizer : p < 0.028 ? L14DExtinguisher : p < 0.034 ? L14DPoster : p < 0.038 ? L14DExit : L14DRail;
                    Decorate(a, b, what, face, (byte)(what == L14DPoster ? rng.Range(3, 4) : 0));
                }
        }

        /// <summary>
        /// Round 4 (after every other draw, so nothing else in the wing moves): a lift in one of the wing's hall walls in one wing
        /// in three (two wide, its doors shut; our invention), and a directory board by a crossing in one wing in two (two wide,
        /// at eye height). Stack 0 is the left half seen from the hall, 1 the right.
        /// </summary>
        private void HallFittings()
        {
            if (rng.Chance(0.34)) HallPair(rng.Range(0, 3), N / 2 - 1, L14DLift);
            if (rng.Chance(0.5)) HallPair(rng.Range(0, 3), rng.Chance(0.5) ? 2 : N - 4, L14DDirectory);
        }

        private void HallPair(int side, int k0, byte what)
        {
            (int A, int B, ArchPier Face) Wall(int k) => side switch
            {
                0 => (-1, k, ArchPier.West), 1 => (N, k, ArchPier.East), 2 => (k, -1, ArchPier.North), _ => (k, N, ArchPier.South),
            };
            for (int k = k0 - 1; k <= k0 + 2; k++)
            {
                var (a, b, _) = Wall(k);
                if (!L14Plan.In(a, b) || At(a, b).Kind != TileKind.Wall || At(a, b).Detail == L14DSign) return;
                // nothing opens beside it on the wing's side
                var (ia, ib) = side switch { 0 => (a + 1, b), 1 => (a - 1, b), 2 => (a, b + 1), _ => (a, b - 1) };
                if (L14Plan.In(ia, ib) && At(ia, ib).Kind == TileKind.Doorway) return;
            }
            // seen from the hall: facing west (side 0) or south (side 3) the left is the lower k; facing east or north the higher
            bool lowLeft = side is 0 or 3;
            for (int i = 0; i < 2; i++)
            {
                var (a, b, face) = Wall(k0 + i);
                ref Tile t = ref At(a, b);
                t.Detail = what;
                t.Pier = face;
                t.Stack = (byte)((i == 0) == lowLeft ? 0 : 1);
            }
        }

        private static byte SignOf(L14Dept d) => d switch
        {
            L14Dept.Medical => 0, L14Dept.Icu => 1, L14Dept.Surgery => 2, L14Dept.Maternity => 3, L14Dept.Psych => 4, _ => 5,
        };

        /// <summary>The handrail along the corridors' walls (on the face toward the corridor), where nothing else is on the wall.</summary>
        private void CorridorWalls()
        {
            for (int b = 0; b < N; b++)
                for (int a = 0; a < N; a++)
                {
                    ref Tile t = ref At(a, b);
                    if (t.Kind != TileKind.Wall || t.Detail != L14DNone) continue;
                    foreach (var (dx, dz, outward) in Dirs)
                    {
                        if (!L14Plan.In(a + dx, b + dz)) continue;
                        Tile n = At(a + dx, b + dz);
                        if (n.Kind != TileKind.Floor || L14ZoneOf(n) != L14Zone.Corridor) continue;
                        double p = rng.NextDouble();
                        t.Detail = p < 0.015 ? L14DClock : p < 0.03 ? L14DSanitizer : p < 0.04 ? L14DExtinguisher : p < 0.05 ? L14DPoster : p < 0.06 ? L14DBlood : L14DRail;
                        t.Stack = (byte)(t.Detail == L14DPoster ? rng.Range(3, 4) : 0);
                        t.Pier = outward;
                        break;
                    }
                }
        }
    }

    /// <summary>Which of the level's props (<see cref="Props.L14First"/>-<see cref="Props.L14Last"/>) people walk through.</summary>
    private static bool L14WalkThrough(ushort variant) => variant is Props.L14Sodas or Props.L14Teddy or Props.L14Vines or Props.L14MouldFloor or Props.L14BloodPool;

    // ================= Air =================

    /// <summary>The temperature: the level's usual one; colder in the torture chambers and where the lights are dead (the Hunter's own cold is felt where it is).</summary>
    private float L14Temperature(int x, int y, int z, int floorY)
    {
        float t = LevelTemperatures[Level14];
        Tile tile = TileAt(x, z);
        if (L14ZoneOf(tile) == L14Zone.Torture) return t - 7;
        if (L14IsDark(tile)) return t - 3;
        return t;
    }

    /// <summary>Reality stability: "Unstable" (Class 4): a little low everywhere, lower in the dark and the torture chambers, lowest in a contaminated room.</summary>
    private float L14Stability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        if (L14IsContam(t) && L14IsRoom(L14ZoneOf(t))) return 0.45f + drift * 0.1f;
        if (L14ZoneOf(t) == L14Zone.Torture) return 0.6f + drift * 0.1f;
        if (L14IsDark(t)) return 0.8f + drift * 0.1f;
        return 0.92f + drift * 0.08f;
    }
}
