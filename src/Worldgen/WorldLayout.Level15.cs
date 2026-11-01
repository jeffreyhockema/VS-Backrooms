using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 15, "Futuristic Halls" (experimental): kept as level 27 (<see cref="Level15"/>) and shown as "15". A maze of clean
/// white halls in a round noclip region far out to the north-west, beyond the End (both wikis' Level 15; the design is
/// docs/design/experimental-levels/15-plan.md). No thresholds in or out: the cheats menu or <c>/backrooms goto 15</c> only.
///
/// <para><b>The lattice.</b> Main halls run straight through the whole region every <see cref="L15Period"/> blocks each
/// way, five wide (x or z mod 128 in 1-5) and five high, a strip of LED panels down the middle, glowing strips along the
/// foot of both walls and a steel rib across the top every eight blocks. Between four halls lies a <b>wing</b>, 121 blocks
/// square (mod 128 in 7-127, its walls at 6 and 128), laid out once from its own hash (<see cref="L15PlanOf"/>, kept in a
/// <see cref="PlanCache{T}"/>).</para>
///
/// <para><b>A wing</b> is cut again and again by side corridors (three wide, four high) or bare service passages (two wide
/// between their own grey walls, three high, a grating floor and a duct), each cut running the whole width of the piece it
/// splits, so every corridor ends on another corridor or opens through the wing's wall onto a main hall. What is left
/// between the cuts are rooms, each with a door onto a corridor beside it: machine rooms (tall, behind a security gate with
/// a dead hand scanner and a wall of thick glass; mostly dead machines from cabinet size to monoliths, a few still running,
/// now and then a rod press feeding a conveyor), wrecked machine rooms, laboratories, stores, dormitories, kitchens, control
/// rooms, lecture halls, bare white rooms, now and then a crematorium full of bones, and far out from the middle the one
/// room with the star door. Abandoned camps and the dead are scattered through it. Everything is planned once per wing.</para>
///
/// <para><b>The dark.</b> One square of 64 blocks in about six has lost its power (<see cref="L15DarkQuad"/>): every light
/// there is dead, its machines stopped; that is where the level's few Robo-Men walk, and where its air goes bad.</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> is the <see cref="L15Zone"/>, with <see cref="L15DarkBit"/> set in the dark; a
/// floor tile's <see cref="Tile.Height"/> is its air (3 to 7), its <see cref="Tile.Depth"/> the floor finish
/// (<see cref="L15FloorCeramic"/> ...); a wall tile's <see cref="Tile.Depth"/> is its material and its <see cref="Tile.Detail"/>
/// what is on its face (<see cref="L15WallPilaster"/> ...), the face the one <see cref="Tile.Pier"/> points to. Props are this
/// level's (<see cref="Props.L15Machine"/> ...) and a few of the other levels' (shelving, cots, counters, camps, bones).</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2700-0x27BF are this level's (0x27C0-0x27FF its thresholds').</summary>
    private const ulong SaltL15Shape = 0x2701, SaltL15Wing = 0x2710, SaltL15Light = 0x2711, SaltL15Dark = 0x2712, SaltL15Star = 0x2713,
        SaltL15Hall = 0x2714, SaltL15HallStyle = 0x2715, SaltL15Lift = 0x2716, SaltL15Dock = 0x2717;

    /// <summary>The lattice: a main hall every 128 blocks each way, five wide; a wing's inside is 121 square, its plan 123 with its walls.</summary>
    public const int L15Period = 128, L15HallWidth = 5, L15WingSize = 121, L15Grid = 123;

    /// <summary>How high the main halls are (blocks of air).</summary>
    public const int L15HallHeight = 5;

    /// <summary>What part of the level a tile is in (kept in the low bits of <see cref="Tile.Zone"/>).</summary>
    public enum L15Zone : byte
    {
        None, Hall, Corridor, Service, Machine, Wreck, Lab, Storage, Dorm, Kitchen, Control, Lecture, Blank, Crematorium, Star, Wall,
        /// <summary>Round 3's rooms: a canteen with its serving line, a medical bay, a hydroponics bay.</summary>
        Canteen, Medical, Hydro,
    }

    /// <summary>Set in <see cref="Tile.Zone"/> where the power is out.</summary>
    public const byte L15DarkBit = 0x80;

    /// <summary>A tile's zone, without the dark bit.</summary>
    public static L15Zone L15ZoneOf(in Tile t) => (L15Zone)(t.Zone & 0x3F);

    /// <summary>Whether the power is out on this tile.</summary>
    public static bool L15IsDark(in Tile t) => (t.Zone & L15DarkBit) != 0;

    /// <summary>Whether a zone is one of the rooms (as against the halls, corridors and walls).</summary>
    public static bool L15IsRoom(L15Zone z) => z is >= L15Zone.Machine and <= L15Zone.Star or >= L15Zone.Canteen and <= L15Zone.Hydro;

    /// <summary>Whether the power is out at a block position in Level 15 (false elsewhere).</summary>
    public bool L15DarkAt(int gx, int gz) => LevelAt(MacroOf(gx), MacroOf(gz)) == Level15 && L15IsDark(TileAt(gx, gz));

    /// <summary>A floor tile's finish (<see cref="Tile.Depth"/>).</summary>
    public const byte L15FloorCeramic = 0, L15FloorWorn = 1, L15FloorCoating = 2, L15FloorCarpet = 3, L15FloorGrating = 4, L15FloorStrip = 5,
        L15FloorBlood = 6, L15FloorScorch = 7, L15FloorTrack = 8, L15FloorDust = 9, L15FloorVinyl = 11, L15FloorTerrazzo = 12;

    /// <summary>
    /// A wall tile's material (<see cref="Tile.Depth"/>): white panels, bare grey concrete (the service passages), scorched;
    /// a room's own walls: pale grey cast concrete (machine rooms, stores, the crematorium: both wikis' "white or grey
    /// concrete"), white wall tiles (kitchens, some labs).
    /// </summary>
    public const byte L15WallWhite = 0, L15WallGrey = 1, L15WallScorched = 2, L15WallCast = 3, L15WallTile = 4;

    /// <summary>
    /// What is on a wall tile's face (<see cref="Tile.Detail"/>, the face toward <see cref="Tile.Pier"/>): nothing; a steel
    /// pilaster (the whole tile); thick glass (rel 2-3), cracked; a dead hand scanner beside a gate; a room's code in black
    /// (which one in <see cref="Tile.Stack"/>); a dead wall display; the radar; the ESCAPE panel; a view of somewhere else
    /// (<see cref="Tile.Stack"/>); a vent grille at the foot of the wall, one with a code scrawled beside it; symbols etched in
    /// a steel pilaster; a wooden door set in the wall that opens on nothing; a smear of dried blood; a doorway's steel jamb
    /// with its strip of light (the whole tile, to door height).
    /// </summary>
    public const byte L15WallPlain = 0, L15WallPilaster = 1, L15WallGlass = 2, L15WallGlassCracked = 3, L15WallScanner = 4, L15WallCode = 5,
        L15WallDisplay = 6, L15WallRadar = 7, L15WallEscape = 8, L15WallView = 9, L15WallVent = 10, L15WallVentCode = 11, L15WallEtched = 12,
        L15WallWoodDoor = 13, L15WallBlood = 14, L15WallJamb = 15;

    /// <summary>
    /// Round 3's wall dress (<see cref="Tile.Detail"/>): an AUTHORIZED PERSONNEL ONLY plate, a DECONTAMINATION plate (both at eye
    /// height beside a door); a lift's left and right door leaves (rel 1-3, its indicator over them) and its call panel; a service
    /// hatch and a grille with pipes behind it (at the foot of the wall); the canteen's menu board (<see cref="Tile.Stack"/> its
    /// part, 0-2 from the left as you face it); a HIGH VOLTAGE plate.
    /// </summary>
    public const byte L15WallAuth = 16, L15WallDecon = 17, L15WallLiftL = 18, L15WallLiftR = 19, L15WallLiftCall = 20, L15WallHatch = 21,
        L15WallPipes = 22, L15WallMenu = 23, L15WallHV = 24;

    /// <summary>
    /// How many room codes there are to paint (<see cref="L15WallCode"/>): two per letter, H (labs), e (stores), M, D, K, C, L, S,
    /// and round 3's F (canteens), R (medical bays), G (hydroponics). The letter (code / 2) also names the plate under it.
    /// </summary>
    public const int L15Codes = 22;

    /// <summary>How many views of other places a wall display can show (<see cref="L15WallView"/>).</summary>
    public const int L15Views = 3;

    /// <summary>A machine's state (<see cref="Tile.Detail"/> of a <see cref="Props.L15Machine"/>): dead, running, wrecked, an incinerator, a rod press.</summary>
    public const byte L15MachineDead = 0, L15MachineRunning = 1, L15MachineWrecked = 2, L15MachineIncinerator = 3, L15MachinePress = 4;

    /// <summary>A console's screen (<see cref="Tile.Detail"/>): dead; lit, ACCESS DENIED; lit, the radar.</summary>
    public const byte L15ConsoleDead = 0, L15ConsoleDenied = 1, L15ConsoleRadar = 2;

    /// <summary>A body (<see cref="Tile.Stack"/>): sitting against a wall (facing <see cref="Tile.Pier"/>), or lying: its head, its feet (Pier from head to feet).</summary>
    public const byte L15CorpseSitting = 0, L15CorpseHead = 1, L15CorpseFeet = 2;

    /// <summary>A doorway's <see cref="Tile.Detail"/>: a security gate (its shutter rolled up into the lintel).</summary>
    public const byte L15DoorGate = 1;

    /// <summary>The plan of one wing, by (A, B) = (x, z) from its inside's north-west corner, -1..121 each way (its walls included).</summary>
    public sealed partial class L15Plan
    {
        public int Hx, Hz;
        public int Rooms, Machines, Corpses, Camps, Boxes, Lockers, Lifts;
        public bool Star;
        /// <summary>Where the camps are (block positions), for the notes left at them.</summary>
        public readonly List<(int X, int Z)> CampSpots = new();
        public readonly Tile[] Tiles = new Tile[L15Grid * L15Grid];

        public ref Tile AtAB(int a, int b) => ref Tiles[a + 1 + (b + 1) * L15Grid];
        public static bool In(int a, int b) => a >= -1 && b >= -1 && a <= L15WingSize && b <= L15WingSize;
        /// <summary>The block position of a place in the plan.</summary>
        public (int X, int Z) World(int a, int b) => (Hx * L15Period + 7 + a, Hz * L15Period + 7 + b);
    }

    private PlanCache<L15Plan> l15Plans;

    /// <summary>A wing's plan (shared: read it, never change it).</summary>
    public L15Plan L15PlanOf(int hx, int hz) =>
        LazyInitializer.EnsureInitialized(ref l15Plans, () => new PlanCache<L15Plan>(24, MakeL15Plan)).Get(hx, hz);

    /// <summary>The wing a block position lies in (or whose wall it is): its plan coordinates and the place in it; null in a main hall.</summary>
    public static (int Hx, int Hz, int A, int B)? L15WingAt(int gx, int gz)
    {
        int u = Hashing.Mod(gx, L15Period), v = Hashing.Mod(gz, L15Period);
        if (u is >= 1 and <= L15HallWidth || v is >= 1 and <= L15HallWidth) return null;
        int hx = Hashing.FloorDiv(gx, L15Period) - (u == 0 ? 1 : 0), hz = Hashing.FloorDiv(gz, L15Period) - (v == 0 ? 1 : 0);
        return (hx, hz, u == 0 ? L15WingSize : u - 7, v == 0 ? L15WingSize : v - 7);
    }

    // ================= Where it is =================

    /// <summary>
    /// How far out along the north-west diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond the End, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L15Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    public int L15CentreX => spawnMacroX - L15Reach;
    public int L15CentreZ => spawnMacroZ - L15Reach;

    /// <summary>The region's radius in macro cells: "practically infinite" (both wikis), as big as the far places get.</summary>
    public int L15Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL15(double mx, double mz) => InRoundRegion(mx, mz, L15CentreX, L15CentreZ, L15Radius, SaltL15Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L15ArrivalCell(ulong h) => RoundArrivalCell(h, L15CentreX, L15CentreZ, L15Radius);

    /// <summary>
    /// Arriving: in a lit main hall, away from its walls (never on the floor lights along their foot), never in a room, a
    /// side corridor or the dark; facing along the hall (<c>ThresholdSystem.L15Arriving</c>).
    /// </summary>
    private static bool IsL15ArrivalSpot(Tile t) => IsArrivalSpot(t) && !L15IsDark(t) && L15ZoneOf(t) == L15Zone.Hall && t.Depth != L15FloorStrip;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L15ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the halls and wings are laid over the edges).</summary>
    private Edge L15Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L15Wall };

    /// <summary>
    /// Lays out one of the level's cells: the main halls from arithmetic, the rest copied from the plans of the wings it
    /// covers; where the region ends, a hallway runs round inside its wall (<see cref="CarveEdgeHall"/>) so nothing it cuts
    /// through is left shut off.
    /// </summary>
    private void BuildLevel15(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (L15WingAt(gx, gz) is { } w)
                {
                    t = L15PlanOf(w.Hx, w.Hz).AtAB(w.A, w.B);
                    continue;
                }
                L15HallTile(ref t, gx, gz, Hashing.Mod(gx, L15Period), Hashing.Mod(gz, L15Period));
            }
        bool[] other = WalledNeighbours(Level15, mx, mz);
        if (other == null) return;
        CarveEdgeHall(b, mx, mz, GetEdge(mx, mz, west: true), GetEdge(mx, mz, west: false));
        // The hallway along the rim is a plain corridor, whatever it was carved through (no box or crate left standing in it)
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
                if (t.Height < 3) t.Height = 4;
                if (L15ZoneOf(t) is L15Zone.Wall or L15Zone.None) t.Zone = (byte)((byte)L15Zone.Corridor | (t.Zone & L15DarkBit));
                if (t.Overhead is Overheads.L15RibWE or Overheads.L15RibNS or Overheads.L15OddBeam) t.Overhead = 0;
            }
    }

    /// <summary>
    /// Whether the power is out in the square of 64 blocks a position lies in: about one in six, never at the very middle.
    /// The squares are centred on the main halls' lines (every other one on a hall, the hall down its middle), so a dark
    /// stretch of hall has its own side rooms dark round it rather than lit ones pouring light through their doors.
    /// </summary>
    public bool L15DarkQuad(int gx, int gz)
    {
        int qx = Hashing.FloorDiv(gx + 32, 64), qz = Hashing.FloorDiv(gz + 32, 64);
        int cx = L15CentreX * MacroSize, cz = L15CentreZ * MacroSize;
        if (Math.Abs(qx * 64 - cx) < 160 && Math.Abs(qz * 64 - cz) < 160) return false; // the middle stays lit (arrivals)
        return Hashing.Unit(Hashing.Hash(seed, qx, qz, SaltL15Dark)) < 0.15;
    }

    /// <summary>
    /// A ceiling light by hash: in the dark, dead (now and then still stuttering); in the light a few dead and a few
    /// failing, the rest giving light (<paramref name="emit"/>) or only looking lit (the panels between, so lighting stays cheap).
    /// </summary>
    private CeilingKind L15Lamp(int gx, int gz, bool emit, bool dark)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL15Light));
        if (dark) return r < 0.04 ? CeilingKind.L15LightFlicker : CeilingKind.L15LightDead;
        if (r < 0.03) return CeilingKind.L15LightDead;
        if (r < 0.075) return CeilingKind.L15LightFlicker;
        return emit ? CeilingKind.L15LightOn : CeilingKind.L15LightLit;
    }

    /// <summary>A tile of a main hall (along z where x mod 128 is 1-5, along x where z mod 128 is), or of a crossing.</summary>
    private void L15HallTile(ref Tile t, int gx, int gz, int u, int v)
    {
        bool alongZ = u is >= 1 and <= L15HallWidth, alongX = v is >= 1 and <= L15HallWidth;
        bool dark = L15DarkQuad(gx, gz);
        t.Kind = TileKind.Floor;
        t.Floor = FloorKind.L15Floor;
        t.Ceiling = CeilingKind.L15Ceiling;
        t.Pattern = WallPattern.L15Wall;
        t.Zone = (byte)((byte)L15Zone.Hall | (dark ? L15DarkBit : 0));
        t.Height = L15HallHeight;
        ulong h = Hashing.Hash(seed, gx, gz, SaltL15Hall);
        t.Depth = Hashing.Unit(h) < 0.08 ? L15FloorWorn : L15FloorCeramic;
        if (alongZ && alongX)
        {
            // A crossing: a square of nine panels over it, the middle one giving light
            if (u is >= 2 and <= 4 && v is >= 2 and <= 4) t.Ceiling = L15Lamp(gx, gz, u == 3 && v == 3, dark);
            return;
        }
        int across = alongZ ? u : v, along = alongZ ? gz : gx;
        t.Pier = alongZ ? ArchPier.North : ArchPier.East; // the way the hall runs
        if (across is 1 or L15HallWidth) t.Depth = L15FloorStrip; // the glowing strips along the foot of both walls
        // The lights down the middle, each stretch between two crossings its own way: one strip of panels (every sixth
        // giving light), two strips (between the ribs), or a square of panels in the middle of each bay; a steel rib across
        // the top every eight blocks, and now and then a beam set in at an angle nobody would build
        int bay = Hashing.Mod(along, 8);
        switch (L15HallStyle(gx, gz, alongZ))
        {
            case 0:
                if (across == 3) t.Ceiling = L15Lamp(gx, gz, Hashing.Mod(along, 6) == 0, dark);
                break;
            case 1:
                if (across is 2 or 4 && bay != 0) t.Ceiling = L15Lamp(gx, gz, across == 2 ? bay == 2 : bay == 6, dark);
                break;
            default:
                if (across is >= 2 and <= 4 && bay is >= 3 and <= 5) t.Ceiling = L15Lamp(gx, gz, across == 3 && bay == 4, dark);
                break;
        }
        if (Hashing.Mod(along, 8) == 0) t.Overhead = alongZ ? Overheads.L15RibWE : Overheads.L15RibNS;
        double p = Hashing.Unit(Hashing.Mix(h));
        if (t.Overhead == 0 && across is 1 or L15HallWidth && p > 0.9985) t.Overhead = Overheads.L15OddBeam;
        // A robot's charging dock against the wall now and then, under a wall light (round 3; never by a door)
        if (L15HallDockAt(gx, gz, alongZ, across))
        {
            t.Variant = Props.L15Dock;
            t.Pier = alongZ ? (across == 1 ? ArchPier.East : ArchPier.West) : (across == 1 ? ArchPier.South : ArchPier.North);
            return;
        }
        // Now and then something left against a wall: a body, a dropped bag, bones (never in front of a door); more of them
        // where the power is out (round 3: the lore's dead and the Robo-Men's leavings lie in the dark)
        double left = dark ? 0.0045 : 0.0017;
        if (dark && p >= 0.0017 && p < left) p = 0.0013 + (p - 0.0017) / (left - 0.0017) * 0.0004; // bags and bones, not more bodies
        if (across is 1 or L15HallWidth && t.Overhead == 0 && p < left && !L15DoorBeside(gx, gz, alongZ, across == 1))
        {
            if (p < 0.0007)
            {
                t.Variant = Props.L15Corpse;
                t.Stack = L15CorpseSitting;
                t.Pier = alongZ ? (across == 1 ? ArchPier.East : ArchPier.West) : (across == 1 ? ArchPier.South : ArchPier.North);
                t.Detail = (byte)(Hashing.Mix(h + 1) % 3 == 0 ? 1 : 0);
            }
            else if (p < 0.0013) t.Variant = Props.Backpack;
            else if (p < 0.0017) t.Variant = Props.BonePile;
        }
    }

    /// <summary>
    /// Whether a robot's charging dock stands on a main hall's tile: against either wall (across 1 or 5), under a wall light
    /// (8 blocks apart, bay 4), away from the crossings, about one bay in eighteen, never by a doorway.
    /// </summary>
    public bool L15HallDockAt(int gx, int gz, bool alongZ, int across)
    {
        if (across is not (1 or L15HallWidth)) return false;
        int along = alongZ ? gz : gx, stretch = Hashing.Mod(along, L15Period);
        if (Hashing.Mod(along, 8) != 4 || stretch < 16 || stretch > 112) return false;
        if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL15Dock)) >= 0.055) return false;
        return !L15DoorBeside(gx, gz, alongZ, across == 1);
    }

    /// <summary>How a stretch of main hall between two crossings is lit (0 one strip, 1 two strips, 2 squares in the bays).</summary>
    public int L15HallStyle(int gx, int gz, bool alongZ)
    {
        int line = alongZ ? Hashing.FloorDiv(gx, L15Period) : Hashing.FloorDiv(gz, L15Period);
        int stretch = alongZ ? Hashing.FloorDiv(gz, L15Period) : Hashing.FloorDiv(gx, L15Period);
        return (int)(Hashing.Hash(seed, line, stretch, SaltL15HallStyle + (alongZ ? 0UL : 1UL)) % 3);
    }

    /// <summary>Whether the wall beside a main hall tile has a doorway in it (or in the tile either side along it).</summary>
    private bool L15DoorBeside(int gx, int gz, bool alongZ, bool low)
    {
        for (int k = -1; k <= 1; k++)
        {
            int x = alongZ ? gx + (low ? -1 : 1) : gx + k, z = alongZ ? gz + k : gz + (low ? -1 : 1);
            if (L15WingAt(x, z) is not { } w) continue;
            if (L15PlanOf(w.Hx, w.Hz).AtAB(w.A, w.B).Kind == TileKind.Doorway) return true;
        }
        return false;
    }

    // ================= A wing =================

    private L15Plan MakeL15Plan(int hx, int hz)
    {
        var plan = new L15Plan { Hx = hx, Hz = hz };
        new L15Work(this, plan, Hashing.Hash(seed, hx, hz, SaltL15Wing)).Lay();
        // Its links: the door that does not open, now and then a way out (WorldLayout.Level15.Links.cs)
        L15LinkPlan(plan);
        // Round 3: lifts on its walls along the main halls, where the links left the wall plain
        L15Lifts(plan);
        return plan;
    }

    /// <summary>
    /// Round 3: now and then a lift in a wing's wall onto a main hall: two steel door leaves that do not open (a bay's blocks 1
    /// and 2 after a pilaster), its indicator over them and its call panel beside (block 3, under the bay's wall light's
    /// neighbour), on plain wall only and away from the crossings and their signs. About one wall in three.
    /// </summary>
    private void L15Lifts(L15Plan plan)
    {
        var rng = new Rng(Hashing.Hash(seed, plan.Hx, plan.Hz, SaltL15Lift));
        bool Plain(int a, int b) => L15Plan.In(a, b) && plan.AtAB(a, b) is { Kind: TileKind.Wall, Detail: L15WallPlain, Depth: L15WallWhite, Under: 0 };
        for (int side = 0; side < 4; side++)
        {
            if (!rng.Chance(0.35)) continue;
            for (int attempt = 0; attempt < 8; attempt++)
            {
                int k = rng.Range(12, L15WingSize - 14);
                var (a, b, face) = L15WingWall(side, k);
                var (x, z) = plan.World(a, b);
                int along = side < 2 ? z : x, stretch = Hashing.Mod(along, L15Period);
                if (Hashing.Mod(along, 8) != 1 || stretch < 16 || stretch > 110) continue;
                var (a1, b1, _) = L15WingWall(side, k + 1);
                var (a2, b2, _) = L15WingWall(side, k + 2);
                if (!Plain(a, b) || !Plain(a1, b1) || !Plain(a2, b2)) continue;
                // Which leaf is the left one, as seen from the hall
                var (rx, rz) = L15Work.RightOf(face);
                bool kLeft = (a1 - a) * rx + (b1 - b) * rz > 0;
                ref Tile l0 = ref plan.AtAB(a, b);
                l0.Detail = kLeft ? L15WallLiftL : L15WallLiftR;
                l0.Pier = face;
                ref Tile l1 = ref plan.AtAB(a1, b1);
                l1.Detail = kLeft ? L15WallLiftR : L15WallLiftL;
                l1.Pier = face;
                ref Tile call = ref plan.AtAB(a2, b2);
                call.Detail = L15WallLiftCall;
                call.Pier = face;
                plan.Lifts++;
                break;
            }
        }
    }

    /// <summary>Whether a wing is far enough out (past 55% of the radius) and lucky enough to hold the star door.</summary>
    private bool L15StarWing(int hx, int hz)
    {
        double cx = hx * L15Period + 64, cz = hz * L15Period + 64;
        double dx = cx / MacroSize - L15CentreX, dz = cz / MacroSize - L15CentreZ;
        if (Math.Sqrt(dx * dx + dz * dz) < L15Radius * 0.55) return false;
        return Hashing.Unit(Hashing.Hash(seed, hx, hz, SaltL15Star)) < 0.035;
    }

    /// <summary>Lays out one wing (see the class remarks): the cuts, then the rooms, then what is on the walls.</summary>
    private sealed class L15Work
    {
        private const int N = L15WingSize, MinLeaf = 7;
        private enum Side : byte { Wing, Corridor, Service }
        private sealed record Leaf(int X0, int Z0, int X1, int Z1, Side[] Sides);
        private static readonly (int Dx, int Dz, ArchPier Out)[] Dirs =
            { (-1, 0, ArchPier.West), (1, 0, ArchPier.East), (0, -1, ArchPier.North), (0, 1, ArchPier.South) };

        private readonly WorldLayout layout;
        private readonly L15Plan plan;
        private Rng rng;
        private readonly List<Leaf> leaves = new();

        public L15Work(WorldLayout layout, L15Plan plan, ulong seed)
        {
            this.layout = layout;
            this.plan = plan;
            rng = new Rng(seed);
        }

        private ref Tile At(int a, int b) => ref plan.AtAB(a, b);
        private bool Dark(int a, int b)
        {
            var (x, z) = plan.World(a, b);
            return layout.L15DarkQuad(x, z);
        }

        public void Lay()
        {
            for (int i = 0; i < plan.Tiles.Length; i++)
                plan.Tiles[i] = new Tile
                {
                    Kind = TileKind.Wall, Pattern = WallPattern.L15Wall, Floor = FloorKind.L15Floor, Ceiling = CeilingKind.L15Ceiling,
                    Zone = (byte)L15Zone.Wall, Height = 4, Level = Level15,
                };
            Split(0, 0, N - 1, N - 1, new[] { Side.Wing, Side.Wing, Side.Wing, Side.Wing }, 0);
            int star = -1;
            if (layout.L15StarWing(plan.Hx, plan.Hz))
            {
                // The biggest room there is, if it is big enough
                int best = 0;
                for (int i = 0; i < leaves.Count; i++)
                {
                    var l = leaves[i];
                    int w = l.X1 - l.X0 + 1, d = l.Z1 - l.Z0 + 1;
                    if (Math.Min(w, d) >= 14 && w * d > best) { best = w * d; star = i; }
                }
            }
            for (int i = 0; i < leaves.Count; i++) Room(leaves[i], i == star);
            CorridorWalls();
            HallWalls();
            // The dark: the corridors and walls by the square they lie in (each room went dark or not as a whole)
            for (int b = -1; b <= N; b++)
                for (int a = -1; a <= N; a++)
                {
                    ref Tile t = ref At(a, b);
                    if (!L15IsRoom(L15ZoneOf(t)) && Dark(a, b)) t.Zone |= L15DarkBit;
                }
        }

        // ---------------- The cuts ----------------

        /// <summary>Cuts a piece of the wing in two with a corridor across it, or leaves it a room.</summary>
        private void Split(int x0, int z0, int x1, int z1, Side[] sides, int depth)
        {
            int w = x1 - x0 + 1, d = z1 - z0 + 1, big = Math.Max(w, d);
            bool can = big >= 2 * MinLeaf + 4;
            bool stop = !can || depth >= 2 && (big <= 18 || big <= 34 && rng.Chance(0.45) || big <= 48 && rng.Chance(0.15));
            if (stop)
            {
                leaves.Add(new Leaf(x0, z0, x1, z1, sides));
                return;
            }
            bool acrossX = w > d || w == d && rng.Chance(0.5); // the cut runs along z, splitting x
            bool service = depth >= 2 && rng.Chance(0.3);
            int cw = service ? 4 : 3;
            int lo = acrossX ? x0 : z0, hi = acrossX ? x1 : z1;
            int s = rng.Range(lo + MinLeaf, hi - MinLeaf - cw + 1);
            Cut(acrossX, s, cw, service, acrossX ? z0 : x0, acrossX ? z1 : x1);
            Side cut = service ? Side.Service : Side.Corridor;
            if (acrossX)
            {
                Split(x0, z0, s - 1, z1, new[] { sides[0], cut, sides[2], sides[3] }, depth + 1);
                Split(s + cw, z0, x1, z1, new[] { cut, sides[1], sides[2], sides[3] }, depth + 1);
            }
            else
            {
                Split(x0, z0, x1, s - 1, new[] { sides[0], sides[1], sides[2], cut }, depth + 1);
                Split(x0, s + cw, x1, z1, new[] { sides[0], sides[1], cut, sides[3] }, depth + 1);
            }
        }

        /// <summary>
        /// Carves a corridor (or a service passage between its own grey walls) across a piece: along z at x = s..s+cw-1 when
        /// <paramref name="alongZ"/>, else along x, from <paramref name="from"/> to <paramref name="to"/>, and opens both ends
        /// onto whatever corridor (or main hall, through the wing's wall) lies past them.
        /// </summary>
        private void Cut(bool alongZ, int s, int cw, bool service, int from, int to)
        {
            // A corridor's floor, the whole length of it: ceramic tiles, or now and then the dark non-slip coating
            coat = !service && rng.Chance(0.28);
            tray = !service && rng.Chance(0.6);
            for (int k = from; k <= to; k++)
                for (int i = 0; i < cw; i++)
                {
                    int a = alongZ ? s + i : k, b = alongZ ? k : s + i;
                    ref Tile t = ref At(a, b);
                    if (service && (i == 0 || i == cw - 1))
                    {
                        t.Kind = TileKind.Wall;
                        t.Depth = L15WallGrey;
                        continue;
                    }
                    var (x, z) = plan.World(a, b);
                    CorridorTile(ref t, x, z, alongZ, service, i, alongZ ? z : x, Dark(a, b));
                }
            // The ends: on through a wall (a service passage's, or the wing's own) to the corridor or hall beyond
            int first = service ? 1 : 0, last = service ? cw - 2 : cw - 1;
            for (int i = first; i <= last; i++)
                foreach (int dir in new[] { -1, 1 })
                {
                    int k = dir < 0 ? from - 1 : to + 1;
                    for (int step = 0; step < 3; step++, k += dir)
                    {
                        int a = alongZ ? s + i : k, b = alongZ ? k : s + i;
                        if (!L15Plan.In(a, b)) break;
                        ref Tile t = ref At(a, b);
                        if (t.Kind == TileKind.Floor) break;
                        var (x, z) = plan.World(a, b);
                        CorridorTile(ref t, x, z, alongZ, service, i, alongZ ? z : x, Dark(a, b));
                        if (a is -1 or N || b is -1 or N) break; // through the wing's wall: the main hall is beyond
                    }
                }
        }

        /// <summary>Whether the corridor being cut has the non-slip coating, a cable tray along its top (<see cref="Cut"/>).</summary>
        private bool coat, tray;

        private void CorridorTile(ref Tile t, int x, int z, bool alongZ, bool service, int i, int along, bool dark)
        {
            t.Kind = TileKind.Floor;
            t.Zone = (byte)(service ? L15Zone.Service : L15Zone.Corridor);
            t.Height = (byte)(service ? 3 : 4);
            t.Pier = alongZ ? ArchPier.North : ArchPier.East;
            t.Variant = 0;
            t.Detail = 0;
            t.Overhead = 0;
            t.Pipe = 0;
            ulong h = Hashing.Hash(layout.seed, x, z, SaltL15Hall);
            if (service)
            {
                t.Depth = L15FloorGrating;
                t.Ceiling = CeilingKind.L15ServiceCeiling;
                // A duct along one side, a caged lamp every eight blocks (half of them dead), an air handler's grille now and then
                if (i == 2) t.Pipe = alongZ ? Pipes.L15DuctNS : Pipes.L15DuctWE;
                else if (Hashing.Mod(along, 8) == 4) t.Ceiling = Hashing.Unit(h) < 0.5 || dark ? CeilingKind.L15LightDead : CeilingKind.L15LightOn;
                else if (Hashing.Mod(along, 12) == 9) t.Ceiling = CeilingKind.L15CeilingVent;
                return;
            }
            t.Depth = coat ? L15FloorCoating : Hashing.Unit(h) < 0.1 ? L15FloorWorn : L15FloorCeramic;
            t.Ceiling = i == 1 && Hashing.Mod(along, 6) == 3 ? layout.L15Lamp(x, z, true, dark) : CeilingKind.L15Ceiling;
            if (i != 1 && Hashing.Mod(along, 16) == 11) t.Ceiling = CeilingKind.L15CeilingVent;
            if (Hashing.Mod(along, 8) == 0) t.Overhead = alongZ ? Overheads.L15RibWE : Overheads.L15RibNS;
            else if (i != 1 && Hashing.Unit(Hashing.Mix(h)) > 0.997) t.Overhead = Overheads.L15OddBeam;
            // Round 3: a cable tray along the top of one side (between the ribs)
            if (tray && i == 0 && t.Overhead == 0) t.Overhead = alongZ ? Overheads.L15TrayNS : Overheads.L15TrayWE;
        }

        // ---------------- The rooms ----------------

        private readonly record struct RoomBox(int X0, int Z0, int X1, int Z1)
        {
            public int W => X1 - X0 + 1;
            public int D => Z1 - Z0 + 1;
            public bool Inside(int a, int b) => a >= X0 && a <= X1 && b >= Z0 && b <= Z1;
        }

        private void Room(Leaf leaf, bool star)
        {
            int ix0 = leaf.Sides[0] == Side.Wing ? leaf.X0 : leaf.X0 + 1, ix1 = leaf.Sides[1] == Side.Wing ? leaf.X1 : leaf.X1 - 1;
            int iz0 = leaf.Sides[2] == Side.Wing ? leaf.Z0 : leaf.Z0 + 1, iz1 = leaf.Sides[3] == Side.Wing ? leaf.Z1 : leaf.Z1 - 1;
            var r = new RoomBox(ix0, iz0, ix1, iz1);
            int w = r.W, d = r.D, small = Math.Min(w, d);
            L15Zone kind = star ? L15Zone.Star : PickKind(w, d);
            bool tall = kind is L15Zone.Machine or L15Zone.Wreck or L15Zone.Lecture or L15Zone.Star;
            int height = tall ? (small >= 12 ? 7 : 5) : 4;
            bool dark = Dark((ix0 + ix1) / 2, (iz0 + iz1) / 2);
            byte zone = (byte)((byte)kind | (dark ? L15DarkBit : 0));
            plan.Rooms++;

            // The floor, and a light every six blocks each way
            for (int b = iz0; b <= iz1; b++)
                for (int a = ix0; a <= ix1; a++)
                {
                    ref Tile t = ref At(a, b);
                    var (x, z) = plan.World(a, b);
                    t.Kind = TileKind.Floor;
                    t.Zone = zone;
                    t.Height = (byte)height;
                    t.Detail = 0;
                    t.Depth = kind switch
                    {
                        L15Zone.Dorm or L15Zone.Lecture => L15FloorCarpet,
                        L15Zone.Kitchen or L15Zone.Storage => L15FloorCoating,
                        L15Zone.Crematorium => L15FloorWorn,
                        L15Zone.Star => L15FloorDust,
                        L15Zone.Medical => L15FloorVinyl,
                        L15Zone.Lab => rng.Chance(0.08) ? L15FloorWorn : L15FloorVinyl,
                        L15Zone.Canteen => L15FloorTerrazzo,
                        L15Zone.Hydro => L15FloorGrating,
                        _ => rng.Chance(0.06) ? L15FloorWorn : L15FloorCeramic,
                    };
                    bool lamp = Hashing.Mod(a - ix0 - (w % 6) / 2, 6) == 3 && Hashing.Mod(b - iz0 - (d % 6) / 2, 6) == 3;
                    t.Ceiling = !lamp ? CeilingKind.L15Ceiling
                        : kind == L15Zone.Star ? CeilingKind.L15LightDead
                        : layout.L15Lamp(x, z, true, dark || kind is L15Zone.Crematorium && rng.Chance(0.5) || kind is L15Zone.Wreck && rng.Chance(0.4));
                }
            // Steel ribs across a tall room every six blocks, the walls' pilasters under them
            if (tall)
            {
                bool ribAlongX = w <= d; // across the narrower way
                int span = ribAlongX ? d : w;
                for (int k = 3; k < span - 2; k += 6)
                {
                    if (ribAlongX)
                    {
                        for (int a = ix0; a <= ix1; a++) At(a, iz0 + k).Overhead = Overheads.L15RibWE;
                        Pilaster(ix0 - 1, iz0 + k, ArchPier.East);
                        Pilaster(ix1 + 1, iz0 + k, ArchPier.West);
                    }
                    else
                    {
                        for (int b = iz0; b <= iz1; b++) At(ix0 + k, b).Overhead = Overheads.L15RibNS;
                        Pilaster(ix0 + k, iz0 - 1, ArchPier.South);
                        Pilaster(ix0 + k, iz1 + 1, ArchPier.North);
                    }
                }
            }

            // The doors: one onto a corridor (or the main hall) beside it, a second in a big room
            int doorWidth = tall ? 3 : small >= 6 ? 2 : 1;
            var doors = new List<int>();
            int first = PickDoorSide(r, -1);
            if (Door(leaf, r, first, doorWidth, kind, zone)) doors.Add(first);
            if (w * d > 260 && rng.Chance(0.7) || doors.Count == 0)
            {
                int second = PickDoorSide(r, first);
                if (Door(leaf, r, second, doorWidth, kind, zone)) doors.Add(second);
            }
            if (doors.Count == 0) return; // (a room too small for any door: left a bare white room nobody gets into)
            // A lit room whose door opens into the dark goes dark with it (its lights would flood the dark through the door)
            if (!dark && DoorIntoDark(r, zone))
            {
                dark = true;
                byte was = zone;
                zone |= L15DarkBit;
                for (int b = r.Z0 - 3; b <= r.Z1 + 3; b++)
                    for (int a = r.X0 - 3; a <= r.X1 + 3; a++)
                    {
                        if (!L15Plan.In(a, b)) continue;
                        ref Tile t = ref At(a, b);
                        if (t.Zone != was || t.Kind is not (TileKind.Floor or TileKind.Doorway)) continue;
                        t.Zone = zone;
                        if (t.Kind == TileKind.Floor && t.Ceiling is CeilingKind.L15LightOn or CeilingKind.L15LightLit or CeilingKind.L15LightFlicker)
                        {
                            var (x, z) = plan.World(a, b);
                            t.Ceiling = layout.L15Lamp(x, z, true, true);
                        }
                    }
            }
            RoomWalls(r, kind);

            switch (kind)
            {
                case L15Zone.Machine: Machines(r, height, dark, false); break;
                case L15Zone.Wreck: Machines(r, height, dark, true); break;
                case L15Zone.Lab: Lab(r); break;
                case L15Zone.Storage: Storage(r); break;
                case L15Zone.Dorm: Dorm(r); break;
                case L15Zone.Kitchen: Kitchen(r); break;
                case L15Zone.Control: Control(r, doors[0], dark); break;
                case L15Zone.Lecture: Lecture(r, doors[0], dark, height); break;
                case L15Zone.Blank: Blank(r); break;
                case L15Zone.Crematorium: Crematorium(r, doors[0]); break;
                case L15Zone.Star: StarRoom(r, doors[0]); break;
                case L15Zone.Canteen: Canteen(r, doors[0], dark); break;
                case L15Zone.Medical: Medical(r, doors[0]); break;
                case L15Zone.Hydro: Hydro(r, dark); break;
            }
            // Abandoned camps, and the dead
            double camp = kind switch
            {
                L15Zone.Dorm => 0.3, L15Zone.Blank or L15Zone.Storage => 0.14,
                L15Zone.Lab or L15Zone.Kitchen or L15Zone.Control or L15Zone.Canteen or L15Zone.Hydro => 0.08, L15Zone.Medical => 0.12, _ => 0,
            };
            if (rng.Chance(camp)) Camp(r);
            double dead = kind switch
            {
                L15Zone.Lab or L15Zone.Control or L15Zone.Medical => 0.18, L15Zone.Machine or L15Zone.Storage or L15Zone.Kitchen or L15Zone.Canteen => 0.08,
                L15Zone.Wreck => 0.25, L15Zone.Hydro => 0.06,
                L15Zone.Star => 0, _ => 0.04,
            };
            if (rng.Chance(dead)) Corpse(r);
            InnerWalls(r, kind, dark);
        }

        /// <summary>
        /// A room's own walls (not the wing's wall onto a main hall): the machine rooms, stores and the crematorium in pale
        /// grey cast concrete, kitchens and some labs in white wall tiles, the rest white panels. Its doors' jambs, codes,
        /// scanners and glass stay as they are.
        /// </summary>
        private void RoomWalls(RoomBox r, L15Zone kind)
        {
            byte mat = kind switch
            {
                L15Zone.Machine or L15Zone.Wreck or L15Zone.Storage or L15Zone.Crematorium => L15WallCast,
                L15Zone.Kitchen or L15Zone.Canteen or L15Zone.Medical => L15WallTile,
                L15Zone.Lab => rng.Chance(0.5) ? L15WallTile : L15WallWhite,
                L15Zone.Blank => rng.Chance(0.25) ? L15WallCast : L15WallWhite,
                _ => L15WallWhite,
            };
            if (mat == L15WallWhite) return;
            for (int b = r.Z0 - 1; b <= r.Z1 + 1; b++)
                for (int a = r.X0 - 1; a <= r.X1 + 1; a++)
                {
                    if (r.Inside(a, b) || a is -1 or N || b is -1 or N || !L15Plan.In(a, b)) continue;
                    ref Tile t = ref At(a, b);
                    if (t.Kind == TileKind.Wall && t.Depth == L15WallWhite) t.Depth = mat;
                }
        }

        /// <summary>Whether a door of the room (its doorway tiles, by the room's zone) opens onto a place where the power is out.</summary>
        private bool DoorIntoDark(RoomBox r, byte zone)
        {
            for (int b = r.Z0 - 3; b <= r.Z1 + 3; b++)
                for (int a = r.X0 - 3; a <= r.X1 + 3; a++)
                {
                    if (r.Inside(a, b) || !L15Plan.In(a, b)) continue;
                    Tile t = At(a, b);
                    if (t.Kind != TileKind.Doorway || t.Zone != zone) continue;
                    var (dx, dz) = Step(t.Pier);
                    if (Dark(a, b) || Dark(a + dx, b + dz)) return true;
                }
            return false;
        }

        private L15Zone PickKind(int w, int d)
        {
            int small = Math.Min(w, d);
            double p = rng.NextDouble();
            // Round 3: canteens (the big kitchens), medical bays and hydroponics bays among them; machine rooms still the most
            if (small >= 16)
                return p < 0.45 ? L15Zone.Machine : p < 0.54 ? L15Zone.Lecture : p < 0.64 ? L15Zone.Wreck : p < 0.71 ? L15Zone.Blank
                    : p < 0.77 ? L15Zone.Storage : p < 0.83 ? L15Zone.Lab : p < 0.89 ? L15Zone.Hydro : p < 0.95 ? L15Zone.Canteen
                    : p < 0.975 ? L15Zone.Crematorium : L15Zone.Dorm;
            if (small >= 8)
                return p < 0.22 ? L15Zone.Machine : p < 0.36 ? L15Zone.Lab : p < 0.48 ? L15Zone.Storage : p < 0.56 ? L15Zone.Dorm
                    : p < 0.63 ? (small >= 10 ? L15Zone.Canteen : L15Zone.Kitchen) : p < 0.72 ? L15Zone.Control : p < 0.78 ? L15Zone.Wreck
                    : p < 0.84 ? L15Zone.Medical : p < 0.89 ? L15Zone.Hydro : p < 0.99 ? L15Zone.Blank : L15Zone.Crematorium;
            return p < 0.30 ? L15Zone.Storage : p < 0.51 ? L15Zone.Blank : p < 0.66 ? L15Zone.Machine : p < 0.78 ? L15Zone.Control
                : p < 0.88 ? L15Zone.Lab : p < 0.94 ? L15Zone.Kitchen : L15Zone.Medical;
        }

        /// <summary>A side of the room to put a door in (0 west, 1 east, 2 north, 3 south), weighted by its length; not <paramref name="not"/>.</summary>
        private int PickDoorSide(RoomBox r, int not)
        {
            int total = 0;
            var len = new int[4];
            for (int s = 0; s < 4; s++)
                if (s != not)
                    total += len[s] = s < 2 ? r.D : r.W;
            int pick = rng.Range(0, total - 1);
            for (int s = 0; s < 4; s++)
            {
                if (pick < len[s]) return s;
                pick -= len[s];
            }
            return 0;
        }

        /// <summary>
        /// Opens a door <paramref name="width"/> wide in a side of the room, through its wall (and a service passage's grey
        /// wall) to the corridor beyond, or through the wing's wall to the main hall; the room's code beside it on the
        /// corridor side, and at a machine room's security gate a dead hand scanner and a wall of thick glass.
        /// </summary>
        private bool Door(Leaf leaf, RoomBox r, int side, int width, L15Zone kind, byte zone)
        {
            var (dx, dz, outward) = Dirs[side];
            bool alongX = side >= 2;
            int lo = alongX ? r.X0 : r.Z0, hi = alongX ? r.X1 : r.Z1;
            if (hi - lo + 1 < width + 2) width = Math.Max(1, hi - lo - 1);
            if (hi - lo + 1 < width + 2) return false;
            int at = rng.Range(lo + 1, hi - width);
            // The wall line just outside the room on that side
            int edge = side switch { 0 => r.X0 - 1, 1 => r.X1 + 1, 2 => r.Z0 - 1, _ => r.Z1 + 1 };
            bool gate = kind is L15Zone.Machine or L15Zone.Wreck;
            int reach = -1;
            for (int i = 0; i < width; i++)
            {
                int a = alongX ? at + i : edge, b = alongX ? edge : at + i;
                for (int step = 0; step < 3; step++, a += dx, b += dz)
                {
                    if (!L15Plan.In(a, b)) break;
                    ref Tile t = ref At(a, b);
                    if (t.Kind == TileKind.Floor) break;
                    t.Kind = TileKind.Doorway;
                    t.Zone = zone;
                    t.Height = 3;
                    t.Detail = (byte)(gate && step == 0 ? L15DoorGate : 0);
                    t.Depth = gate ? L15FloorTrack : L15FloorCeramic;
                    t.Pier = outward;
                    t.Variant = 0;
                    reach = Math.Max(reach, step);
                    if (a is -1 or N || b is -1 or N) break;
                }
            }
            if (reach < 0) return false;
            // The outermost wall tiles either side of the door, on the corridor side: a steel jamb with its strip of light
            // either side, the room's code (and at a gate the hand scanner) on the wall beyond
            int line = edge + (alongX ? dz : dx) * reach;
            (int A, int B) Beside(int k) => alongX ? (k, line) : (line, k);
            foreach (int k in new[] { at - 1, at + width })
            {
                var (ja, jb) = Beside(k);
                if (!L15Plan.In(ja, jb)) continue;
                ref Tile j = ref At(ja, jb);
                if (j.Kind != TileKind.Wall) continue;
                j.Detail = L15WallJamb;
                j.Pier = outward;
            }
            var (ca, cb) = Beside(at - 2);
            var (sa, sb) = Beside(at + width + 1);
            if (rng.Chance(0.5)) (ca, cb, sa, sb) = (sa, sb, ca, cb);
            Decorate(ca, cb, L15WallCode, outward, CodeOf(kind));
            if (gate) Decorate(sa, sb, L15WallScanner, outward, 0);
            // Round 3: AUTHORIZED PERSONNEL ONLY by a control room's door, DECONTAMINATION by most labs' and hydroponics bays'
            else if (kind == L15Zone.Control) Decorate(sa, sb, L15WallAuth, outward, 0);
            else if (kind is L15Zone.Lab or L15Zone.Hydro && rng.Chance(0.7)) Decorate(sa, sb, L15WallDecon, outward, 0);
            // A machine room's wall of thick glass, looking out on the corridor (not through a service passage's double wall); round
            // 3: the labs, control rooms, hydroponics bays and canteens have their glass walls too, now and then, so the rooms show
            // from the corridors
            bool glass = gate || kind switch
            {
                L15Zone.Lab => rng.Chance(0.6), L15Zone.Control => rng.Chance(0.75), L15Zone.Hydro => rng.Chance(0.8), L15Zone.Canteen => rng.Chance(0.5),
                _ => false,
            };
            if (glass && reach == 0 && leaf.Sides[side] != Side.Service)
                for (int k = lo + 1; k < hi; k++)
                {
                    if (k >= at - 2 && k <= at + width + 1) continue;
                    var (ga, gb) = alongX ? (k, edge) : (edge, k);
                    ref Tile g = ref At(ga, gb);
                    if (g.Kind != TileKind.Wall || g.Detail != L15WallPlain || g.Depth != L15WallWhite) continue;
                    g.Detail = rng.Chance(0.22) ? L15WallGlassCracked : L15WallGlass;
                    g.Pier = outward;
                }
            return true;
        }

        private byte CodeOf(L15Zone kind)
        {
            int letter = kind switch
            {
                L15Zone.Lab => 0, L15Zone.Storage => 1, L15Zone.Machine or L15Zone.Wreck => 2, L15Zone.Dorm => 3, L15Zone.Kitchen => 4,
                L15Zone.Control => 5, L15Zone.Lecture => 6, L15Zone.Canteen => 8, L15Zone.Medical => 9, L15Zone.Hydro => 10, _ => 7,
            };
            return (byte)(letter * 2 + rng.Range(0, 1));
        }

        /// <summary>Puts something on a wall tile's face toward <paramref name="face"/>, if it is a plain white wall.</summary>
        private void Decorate(int a, int b, byte what, ArchPier face, byte stack)
        {
            if (!L15Plan.In(a, b)) return;
            ref Tile t = ref At(a, b);
            if (t.Kind != TileKind.Wall || t.Detail != L15WallPlain || t.Depth != L15WallWhite) return;
            t.Detail = what;
            t.Pier = face;
            t.Stack = stack;
        }

        private void Pilaster(int a, int b, ArchPier face)
        {
            if (!L15Plan.In(a, b)) return;
            ref Tile t = ref At(a, b);
            if (t.Kind != TileKind.Wall || t.Detail != L15WallPlain) return;
            t.Detail = rng.Chance(0.12) ? L15WallEtched : L15WallPilaster;
            t.Pier = face;
        }

        /// <summary>Puts a prop on a free floor tile of the plan; false if the tile is taken or not floor.</summary>
        private bool Put(int a, int b, ushort prop, ArchPier pier = ArchPier.North, byte stack = 0, byte detail = 0)
        {
            if (!L15Plan.In(a, b) || NextToDoor(a, b)) return false;
            ref Tile t = ref At(a, b);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stack != 0) return false;
            t.Variant = prop;
            t.Pier = pier;
            t.Stack = stack;
            t.Detail = detail;
            return true;
        }

        private bool Free(int a, int b) =>
            L15Plan.In(a, b) && At(a, b) is { Kind: TileKind.Floor, Variant: 0, SupplyBox: false, Stack: 0 } && !NextToDoor(a, b);

        private bool NextToDoor(int a, int b)
        {
            foreach (var (dx, dz, _) in Dirs)
                if (L15Plan.In(a + dx, b + dz) && At(a + dx, b + dz).Kind == TileKind.Doorway) return true;
            return false;
        }

        /// <summary>The way to a wall beside (a, b), if there is one.</summary>
        private ArchPier? AgainstWall(int a, int b)
        {
            foreach (var (dx, dz, outward) in Dirs)
                if (L15Plan.In(a + dx, b + dz) && At(a + dx, b + dz).Kind == TileKind.Wall) return outward;
            return null;
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

        /// <summary>The wall line just outside a room on a side (0 west, 1 east, 2 north, 3 south), and a place along it.</summary>
        private static (int A, int B) WallAt(RoomBox r, int side, int k) => side switch
        {
            0 => (r.X0 - 1, r.Z0 + k), 1 => (r.X1 + 1, r.Z0 + k), 2 => (r.X0 + k, r.Z0 - 1), _ => (r.X0 + k, r.Z1 + 1),
        };

        /// <summary>A place in a room counted from a side: <paramref name="k"/> along it, <paramref name="row"/> in from it.</summary>
        private static (int A, int B) FromSide(RoomBox r, int side, int k, int row) => side switch
        {
            0 => (r.X0 + row, r.Z0 + k), 1 => (r.X1 - row, r.Z0 + k), 2 => (r.X0 + k, r.Z0 + row), _ => (r.X0 + k, r.Z1 - row),
        };

        private static int Across(int side) => side switch { 0 => 1, 1 => 0, 2 => 3, _ => 2 };

        // ---------------- Machine rooms ----------------

        /// <summary>
        /// A machine room: blocks of machinery in a grid with aisles between (cabinets to monoliths four or five blocks
        /// high), smaller machines along the walls; mostly dead, one in five still running where there is power, a few
        /// wrecked; now and then a rod press feeding a conveyor. A wrecked room: nearly all burnt out, scrap everywhere.
        /// </summary>
        private void Machines(RoomBox r, int height, bool dark, bool wrecked)
        {
            byte State()
            {
                double p = rng.NextDouble();
                if (wrecked) return p < 0.7 ? L15MachineWrecked : L15MachineDead;
                if (dark) return p < 0.88 ? L15MachineDead : L15MachineWrecked;
                return p < 0.22 ? L15MachineRunning : p < 0.86 ? L15MachineDead : L15MachineWrecked;
            }
            int x0 = r.X0 + 2, z0 = r.Z0 + 2, x1 = r.X1 - 2, z1 = r.Z1 - 2;
            // The rod press first, if any: along the room's longer way, a press then a conveyor out of it to a heap of rods
            if (!wrecked && !dark && r.W >= 10 && r.D >= 10 && rng.Chance(0.18))
            {
                bool alongX = r.W >= r.D;
                int len = Math.Min(alongX ? x1 - x0 + 1 : z1 - z0 + 1, 12);
                ArchPier run = alongX ? ArchPier.East : ArchPier.South;
                for (int k = 0; k < len; k++)
                    for (int j = 0; j < 2; j++)
                    {
                        int a = alongX ? x0 + k : x0 + j, b = alongX ? z0 + j : z0 + k;
                        if (k < 2) Put(a, b, Props.L15Machine, ArchPier.North, (byte)Math.Min(3, height - 1), L15MachinePress);
                        else if (j == 0 && k < len - 1) Put(a, b, Props.Conveyor, run, (byte)(rng.Chance(0.2) ? 1 : 0));
                        else if (j == 0) Put(a, b, Props.L15Rods, run);
                    }
                plan.Machines++;
                if (alongX) z0 += 4; else x0 += 4;
            }
            // The grid of machines: in a big room up to 4 by 4 (the monoliths), with a gap of open floor now and then
            int most = Math.Min(r.W, r.D) >= 20 ? 4 : 3;
            for (int b = z0; b <= z1;)
            {
                int fd = rng.Range(1, Math.Min(most, z1 - b + 1));
                for (int a = x0; a <= x1;)
                {
                    int fw = rng.Range(1, Math.Min(most, x1 - a + 1));
                    int gap = rng.Chance(0.15) ? 4 : 2;
                    if (rng.Chance(0.72))
                    {
                        int big = Math.Max(fw, fd);
                        int h = big >= 3 ? rng.Range(Math.Min(3, height - 1), height - 1) : big == 2 ? rng.Range(2, Math.Min(4, height - 1)) : rng.Range(1, 2);
                        byte state = State();
                        for (int j = 0; j < fd; j++)
                            for (int i = 0; i < fw; i++)
                                Put(a + i, b + j, Props.L15Machine, ArchPier.North, (byte)Math.Max(1, h), state);
                        plan.Machines++;
                        if (state == L15MachineWrecked) Scorch(a - 1, b - 1, a + fw, b + fd, 0.35);
                    }
                    a += fw + gap + (rng.Chance(0.3) ? 1 : 0);
                }
                b += fd + 2 + (rng.Chance(0.3) ? 1 : 0);
            }
            // Along the walls: switchgear, gauges, generators, tanks, small cabinets, a gap now and then
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!Free(a, b) || rng.Chance(0.55)) continue;
                ArchPier into = Opp(wall);
                double p = rng.NextDouble();
                if (wrecked && p < 0.5) Put(a, b, rng.Chance(0.5) ? Props.ScrapMetal : Props.MachineParts, into);
                else if (p < 0.3) Put(a, b, Props.Switchgear, into);
                else if (p < 0.5) Put(a, b, Props.GaugeFrame, into, (byte)rng.Range(0, 3));
                else if (p < 0.6) Put(a, b, Props.Generator, into);
                else if (p < 0.72) Put(a, b, Props.PressureTank, into, (byte)rng.Range(0, 1));
                else Put(a, b, Props.L15Machine, into, (byte)rng.Range(1, 2), wrecked ? L15MachineWrecked : State());
            }
            if (wrecked)
                for (int k = rng.Range(6, 14); k > 0; k--)
                {
                    int a = rng.Range(r.X0, r.X1), b = rng.Range(r.Z0, r.Z1);
                    if (Free(a, b)) Put(a, b, rng.Chance(0.5) ? Props.ScrapMetal : Props.MachineParts, (ArchPier)rng.Range(0, 3));
                }
        }

        /// <summary>Burns the floor round a wrecked machine (and the white walls by it, if any).</summary>
        private void Scorch(int a0, int b0, int a1, int b1, double p)
        {
            for (int b = b0; b <= b1; b++)
                for (int a = a0; a <= a1; a++)
                {
                    if (!L15Plan.In(a, b) || !rng.Chance(p)) continue;
                    ref Tile t = ref At(a, b);
                    if (t.Kind == TileKind.Floor) t.Depth = L15FloorScorch;
                    else if (t.Kind == TileKind.Wall && t.Detail == L15WallPlain && t.Depth == L15WallWhite) t.Depth = L15WallScorched;
                }
        }

        // ---------------- The other rooms ----------------

        /// <summary>A laboratory: rows of benches (sinks, instruments, glassware) with stools, cabinets along the walls.</summary>
        private void Lab(RoomBox r)
        {
            bool alongX = r.W >= r.D;
            int across = alongX ? r.D : r.W, len = alongX ? r.W : r.D;
            for (int row = 2; row < across - 1; row += 4)
                for (int k = 2; k < len - 2; k++)
                {
                    if ((k - 2) % 7 == 6) continue; // a way through the row
                    int a = alongX ? r.X0 + k : r.X0 + row, b = alongX ? r.Z0 + row : r.Z0 + k;
                    double p = rng.NextDouble();
                    byte kind = (byte)(p < 0.4 ? 0 : p < 0.6 ? 1 : p < 0.85 ? 2 : 3);
                    ArchPier face = alongX ? ArchPier.South : ArchPier.East;
                    // Round 3: now and then a stripped appliance on a plain bench (Stack: 1 a coffee machine, 2 a 3D printer's frame)
                    byte gear = (byte)(kind == 0 && rng.Chance(0.22) ? rng.Range(1, 2) : 0);
                    if (!Put(a, b, Props.L15LabBench, face, gear, kind)) continue;
                    var (sx, sz) = Step(face);
                    if (rng.Chance(0.45)) Put(a + sx, b + sz, Props.FoldingChair, Opp(face));
                }
            foreach (var (a, b, wall) in Rim(r))
                if (Free(a, b) && rng.Chance(0.12)) Put(a, b, rng.Chance(0.6) ? Props.MedCabinet : Props.FilingCabinet, Opp(wall));
            if (rng.Chance(0.3)) Blood(r);
        }

        /// <summary>A store: rows of steel shelving, lockers along a wall, boxes, a crate or two; now and then a sealed supply box.</summary>
        private void Storage(RoomBox r)
        {
            bool alongX = r.W >= r.D;
            int across = alongX ? r.D : r.W, len = alongX ? r.W : r.D;
            for (int row = 2; row < across - 2; row += 3)
                for (int k = 2; k < len - 2; k++)
                {
                    if ((k - 2) % 9 == 8) continue;
                    int a = alongX ? r.X0 + k : r.X0 + row, b = alongX ? r.Z0 + row : r.Z0 + k;
                    Put(a, b, Props.Shelf, alongX ? (row % 2 == 0 ? ArchPier.North : ArchPier.South) : (row % 2 == 0 ? ArchPier.West : ArchPier.East));
                }
            int lockers = 0;
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!Free(a, b)) continue;
                double p = rng.NextDouble();
                if (p < 0.08 && lockers < 3)
                {
                    Put(a, b, Props.L15Locker, Opp(wall), 0, (byte)(rng.Chance(0.55) ? 1 : 0));
                    lockers++;
                }
                else if (p < 0.24) Put(a, b, Props.CardboardBoxes, Opp(wall));
                else if (p < 0.28) At(a, b).Stack = (byte)rng.Range(1, 2); // a crate or two
            }
            plan.Lockers += lockers;
            if (rng.Chance(0.35)) SupplyBox(r);
        }

        /// <summary>A dormitory: cots along the walls, head to the wall, lockers between.</summary>
        private void Dorm(RoomBox r)
        {
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!Free(a, b)) continue;
                ArchPier into = Opp(wall);
                var (dx, dz) = Step(into);
                if ((a + b) % 2 == 0 && rng.Chance(0.6) && Free(a + dx, b + dz))
                {
                    // The cot: its head against the wall, Pier from the head to the foot
                    Put(a, b, Props.RunSafeCot, into, 0);
                    Put(a + dx, b + dz, Props.RunSafeCot, into, 1);
                }
                else if (rng.Chance(0.06))
                {
                    Put(a, b, Props.L15Locker, into, 0, (byte)(rng.Chance(0.5) ? 1 : 0));
                    plan.Lockers++;
                }
            }
            if (rng.Chance(0.2)) SupplyBox(r);
        }

        /// <summary>A kitchen: counters (sinks, microwaves), a fridge and a stove along the walls, tables in the middle; all stripped.</summary>
        private void Kitchen(RoomBox r)
        {
            bool fridge = false, stove = false;
            foreach (var (a, b, wall) in Rim(r))
            {
                if (!Free(a, b) || rng.Chance(0.35)) continue;
                ArchPier into = Opp(wall);
                if (!fridge && rng.Chance(0.15)) { Put(a, b, Props.Fridge, into); fridge = true; }
                else if (!stove && rng.Chance(0.15)) { Put(a, b, Props.Stove, into); stove = true; }
                else Counter(a, b, into, rng.Chance(0.6) ? 0 : rng.Range(1, 2));
            }
            for (int b = r.Z0 + 3; b <= r.Z1 - 3; b += 4)
                for (int a = r.X0 + 3; a <= r.X1 - 3; a += 4)
                {
                    if (!Put(a, b, Props.RoundTable)) continue;
                    foreach (var (dx, dz, outward) in Dirs)
                        if (rng.Chance(0.5)) Put(a + dx, b + dz, Props.FoldingChair, Opp(outward));
                }
        }

        /// <summary>
        /// A kitchen counter (its kind: plain, sink, microwave); round 3: on a plain one now and then an appliance stripped of its
        /// insides (Fandom), in <see cref="Tile.Detail"/>: 1 a coffee machine, 2 a 3D printer's frame.
        /// </summary>
        private void Counter(int a, int b, ArchPier into, int kind)
        {
            byte gear = (byte)(kind == 0 && rng.Chance(0.25) ? rng.Range(1, 2) : 0);
            Put(a, b, Props.KitchenCounter, into, (byte)kind, gear);
        }

        /// <summary>A control room: rows of consoles facing a wall of displays (the radar, the ESCAPE panel, views of elsewhere), chairs behind them.</summary>
        private void Control(RoomBox r, int doorSide, bool dark)
        {
            int front = Across(doorSide);
            ArchPier toFront = Dirs[front].Out, toBack = Opp(toFront);
            int len = front >= 2 ? r.W : r.D, depth = front >= 2 ? r.D : r.W;
            for (int k = 1; k < len - 1; k++)
            {
                if (rng.Chance(0.35)) continue;
                var (a, b) = WallAt(r, front, k);
                double p = rng.NextDouble();
                byte what = dark ? L15WallDisplay : p < 0.3 ? L15WallRadar : p < 0.42 ? L15WallEscape : p < 0.65 ? L15WallView : L15WallDisplay;
                Decorate(a, b, what, toBack, (byte)rng.Range(0, L15Views - 1));
            }
            for (int row = 2; row < depth - 1; row += 3)
                for (int k = 1; k < len - 1; k++)
                {
                    if ((k - 1) % 6 == 5 || rng.Chance(0.08)) continue;
                    var (a, b) = FromSide(r, front, k, row);
                    double p = rng.NextDouble();
                    byte screen = dark || p < 0.55 ? L15ConsoleDead : p < 0.8 ? L15ConsoleDenied : L15ConsoleRadar;
                    if (!Put(a, b, Props.L15Console, toBack, 0, screen)) continue;
                    var (sx, sz) = Step(toBack);
                    if (rng.Chance(0.8)) Put(a + sx, b + sz, Props.OfficeChair, rng.Chance(0.85) ? toFront : (ArchPier)rng.Range(0, 3));
                }
        }

        /// <summary>
        /// A lecture hall, raked (round 3): a stage along the front wall, by the door, under a big display; rows of seats with
        /// backs facing it, each row on a step half a block higher than the one before, a way behind each row, an aisle of steps
        /// up the middle and along both side walls. Round any other door the floor stays flat (a well at the foot of the steps).
        /// </summary>
        private void Lecture(RoomBox r, int doorSide, bool dark, int height)
        {
            int front = doorSide;
            ArchPier toFront = Dirs[front].Out;
            int len = front >= 2 ? r.W : r.D, depth = front >= 2 ? r.D : r.W;
            for (int row = 0; row < 3; row++)
                for (int k = 0; k < len; k++)
                {
                    var (a, b) = FromSide(r, front, k, row);
                    if (!NextToDoor(a, b)) Put(a, b, Props.L15Stage);
                }
            for (int k = len / 2 - 1; k <= len / 2 + 1; k++)
            {
                var (a, b) = WallAt(r, front, k);
                Decorate(a, b, dark ? L15WallDisplay : L15WallView, Opp(toFront), (byte)rng.Range(0, L15Views - 1));
            }
            int mid = len / 2, most = Math.Max(0, 2 * (height - 3)); // the highest step (half blocks) leaving two blocks of headroom
            int tier = 0;
            for (int row = 4; row < depth; row += 2, tier = Math.Min(most, tier + 1))
                for (int j = 0; j < 2 && row + j < depth; j++)
                    for (int k = 0; k < len; k++)
                    {
                        var (a, b) = FromSide(r, front, k, row + j);
                        if (NearDoor(a, b, 2)) continue;
                        bool aisle = Math.Abs(k - mid) <= 1 || k == 0 || k == len - 1;
                        if (j == 0 && !aisle) Put(a, b, Props.L15Seat, toFront, (byte)tier);
                        else if (tier > 0) Put(a, b, Props.L15Riser, toFront, (byte)tier);
                    }
        }

        /// <summary>Whether a doorway lies within <paramref name="d"/> tiles of (a, b) (either way).</summary>
        private bool NearDoor(int a, int b, int d)
        {
            for (int db = -d; db <= d; db++)
                for (int da = -d; da <= d; da++)
                    if (L15Plan.In(a + da, b + db) && At(a + da, b + db).Kind == TileKind.Doorway) return true;
            return false;
        }

        /// <summary>The way to step along a wall facing <paramref name="face"/> to go right, as someone in front of it looking at it sees it.</summary>
        public static (int Dx, int Dz) RightOf(ArchPier face) => face switch
        {
            ArchPier.North => (-1, 0), ArchPier.South => (1, 0), ArchPier.East => (0, -1), _ => (0, 1),
        };

        /// <summary>
        /// A canteen (round 3): the kitchen along the back wall (counters, a stove, a fridge) under the menu board, the serving
        /// line two rows out (trays at one end, steel wells, the till at the other), and long tables with chairs down the room.
        /// </summary>
        private void Canteen(RoomBox r, int doorSide, bool dark)
        {
            int back = Across(doorSide);
            ArchPier into = Opp(Dirs[back].Out);
            int len = back >= 2 ? r.W : r.D, depth = back >= 2 ? r.D : r.W, mid = len / 2;
            bool fridge = false, stove = false;
            for (int k = 0; k < len; k++)
            {
                var (a, b) = FromSide(r, back, k, 0);
                if (!Free(a, b)) continue;
                if (!fridge && (k == len - 1 || rng.Chance(0.08))) { Put(a, b, Props.Fridge, into); fridge = true; }
                else if (!stove && k >= mid - 3 && rng.Chance(0.3)) { Put(a, b, Props.Stove, into); stove = true; }
                else if (rng.Chance(0.85)) Counter(a, b, into, rng.Chance(0.65) ? 0 : rng.Range(1, 2));
            }
            // The menu board over the kitchen, three wide, read left to right from the room
            var (rx, rz) = RightOf(into);
            var (la, lb) = WallAt(r, back, mid - 1);
            var (ha, hb) = WallAt(r, back, mid + 1);
            bool lowFirst = (ha - la) * rx + (hb - lb) * rz > 0; // stepping right from mid - 1 reaches mid + 1
            for (int k = mid - 1; k <= mid + 1; k++)
            {
                var (a, b) = WallAt(r, back, k);
                int part = lowFirst ? k - (mid - 1) : (mid + 1) - k;
                Decorate(a, b, L15WallMenu, into, (byte)part);
            }
            // The serving line, the customers' side toward the room
            if (depth >= 7)
                for (int k = 2; k <= len - 3; k++)
                {
                    var (a, b) = FromSide(r, back, k, 2);
                    byte kind = (byte)(k == 2 ? 1 : k == len - 3 ? 2 : 0);
                    Put(a, b, Props.L15Serve, into, kind);
                }
            // Long tables down the room, chairs both sides
            for (int row = 5; row < depth - 1; row += 3)
                for (int k = 2; k < len - 2; k++)
                {
                    if ((k - 2) % 7 == 6) continue;
                    var (a, b) = FromSide(r, back, k, row);
                    if (!Put(a, b, Props.FoldingTable)) continue;
                    foreach (int j in new[] { -1, 1 })
                    {
                        var (ca, cb) = FromSide(r, back, k, row + j);
                        if (rng.Chance(0.7)) Put(ca, cb, Props.FoldingChair, j < 0 ? into : Dirs[back].Out);
                    }
                }
        }

        /// <summary>
        /// A medical bay (round 3; the lore's rumour of Level 14's MEDICAL CENTER door): hospital beds head to the side walls
        /// every three blocks, a drip stand at each head and a bedside cabinet, medicine cabinets and a crash cart along the back.
        /// </summary>
        private void Medical(RoomBox r, int doorSide)
        {
            int back = Across(doorSide);
            int[] sides = doorSide < 2 ? new[] { 2, 3 } : new[] { 0, 1 };
            foreach (int s in sides)
            {
                ArchPier into = Opp(Dirs[s].Out);
                int len = s >= 2 ? r.W : r.D;
                for (int k = 2; k + 1 < len - 1; k += 3)
                {
                    var (ha, hb) = FromSide(r, s, k, 0);
                    var (fa, fb) = FromSide(r, s, k, 1);
                    if (!Free(ha, hb) || !Free(fa, fb)) continue;
                    Put(ha, hb, Props.HospitalBed, into, 0);
                    Put(fa, fb, Props.HospitalBed, into, 1);
                    var (ia, ib) = FromSide(r, s, k - 1, 0);
                    if (rng.Chance(0.8)) Put(ia, ib, Props.RunIvStand, into);
                    var (ca, cb) = FromSide(r, s, k + 1, 0);
                    if (rng.Chance(0.6)) Put(ca, cb, Props.RunBedside, into);
                }
            }
            int blen = back >= 2 ? r.W : r.D;
            bool cart = false;
            ArchPier fromBack = Opp(Dirs[back].Out);
            for (int k = 1; k < blen - 1; k++)
            {
                var (a, b) = FromSide(r, back, k, 0);
                if (!Free(a, b) || rng.Chance(0.35)) continue;
                if (!cart && rng.Chance(0.2)) { Put(a, b, Props.RunCrashCart, fromBack); cart = true; }
                else Put(a, b, Props.MedCabinet, fromBack);
            }
            if (rng.Chance(0.3)) Blood(r);
        }

        /// <summary>
        /// A hydroponics bay (round 3; our invention: the lore has kitchens, not farms): rows of two-high racks of dead plants
        /// under grow lights (dead where the power is out), nutrient tanks along one end wall. Nothing in it can be eaten.
        /// </summary>
        private void Hydro(RoomBox r, bool dark)
        {
            bool alongX = r.W >= r.D;
            int across = alongX ? r.D : r.W, len = alongX ? r.W : r.D;
            for (int row = 2; row < across - 2; row += 3)
                for (int k = 1; k < len - 3; k++)
                {
                    if ((k - 1) % 8 == 7) continue;
                    int a = alongX ? r.X0 + k : r.X0 + row, b = alongX ? r.Z0 + row : r.Z0 + k;
                    ArchPier face = alongX ? (row % 2 == 0 ? ArchPier.North : ArchPier.South) : (row % 2 == 0 ? ArchPier.West : ArchPier.East);
                    Put(a, b, Props.L15GrowRack, face);
                }
            // The nutrient tanks along the far end
            int end = alongX ? 1 : 3;
            for (int k = 1; k < across - 1; k++)
            {
                var (a, b) = FromSide(r, end, k, 0);
                if (!Free(a, b) || rng.Chance(0.4)) continue;
                Put(a, b, Props.PressureTank, Opp(Dirs[end].Out), (byte)rng.Range(0, 1));
            }
        }

        /// <summary>
        /// Round 3: what is on the side corridors' walls, toward the corridor: now and then a service hatch at the foot of the
        /// wall or a grille with the pipes behind it.
        /// </summary>
        private void CorridorWalls()
        {
            for (int b = 0; b < N; b++)
                for (int a = 0; a < N; a++)
                {
                    Tile t = At(a, b);
                    if (t.Kind != TileKind.Floor || L15ZoneOf(t) != L15Zone.Corridor) continue;
                    foreach (var (dx, dz, outward) in Dirs)
                    {
                        if (!L15Plan.In(a + dx, b + dz) || At(a + dx, b + dz).Kind != TileKind.Wall) continue;
                        double p = rng.NextDouble();
                        if (p < 0.014) Decorate(a + dx, b + dz, L15WallHatch, Opp(outward), 0);
                        else if (p < 0.024) Decorate(a + dx, b + dz, L15WallPipes, Opp(outward), 0);
                    }
                }
        }

        /// <summary>A bare white room: nothing, or something wrong with it (a pillar stub out of the floor, a wooden door in a wall).</summary>
        private void Blank(RoomBox r)
        {
            if (rng.Chance(0.35))
            {
                int a = rng.Range(r.X0 + 1, r.X1 - 1), b = rng.Range(r.Z0 + 1, r.Z1 - 1);
                if (Free(a, b)) Put(a, b, Props.L15Pillar, ArchPier.North, (byte)rng.Range(1, 3));
            }
            if (rng.Chance(0.2))
            {
                var rim = new List<(int A, int B, ArchPier Wall)>(Rim(r));
                var (a, b, wall) = rim[rng.Range(0, rim.Count - 1)];
                var (dx, dz) = Step(wall);
                Decorate(a + dx, b + dz, L15WallWoodDoor, Opp(wall), 0);
            }
            if (rng.Chance(0.15)) SupplyBox(r);
        }

        /// <summary>
        /// A crematorium: an incinerator against the wall across from the door, bones heaped and scattered over a sooty
        /// floor (Wikidot's burnt Hounds), the lights mostly gone.
        /// </summary>
        private void Crematorium(RoomBox r, int doorSide)
        {
            int back = Across(doorSide);
            ArchPier into = Opp(Dirs[back].Out);
            int len = back >= 2 ? r.W : r.D, mid = len / 2;
            for (int k = mid - 1; k <= mid + 1; k++)
                for (int j = 0; j < 2; j++)
                {
                    var (a, b) = FromSide(r, back, k, j);
                    Put(a, b, Props.L15Machine, into, 3, L15MachineIncinerator);
                }
            plan.Machines++;
            for (int k = rng.Range(7, 14); k > 0; k--)
            {
                int a = rng.Range(r.X0, r.X1), b = rng.Range(r.Z0, r.Z1);
                if (!Free(a, b)) continue;
                double p = rng.NextDouble();
                Put(a, b, p < 0.5 ? Props.BonePile : p < 0.8 ? Props.JawSkeleton : Props.Ribcage, (ArchPier)rng.Range(0, 3));
            }
            Scorch(r.X0, r.Z0, r.X1, r.Z1, 0.3);
        }

        /// <summary>The star door: an empty, unlit machine room, a doorframe standing in the middle with a night sky and a blue star in it.</summary>
        private void StarRoom(RoomBox r, int doorSide)
        {
            plan.Star = true;
            int a = (r.X0 + r.X1) / 2, b = (r.Z0 + r.Z1) / 2;
            Put(a, b, Props.L15StarDoor, Dirs[doorSide].Out);
            for (int k = rng.Range(2, 4); k > 0; k--)
            {
                int pa = rng.Range(r.X0, r.X1), pb = rng.Range(r.Z0, r.Z1);
                if (Free(pa, pb) && Math.Abs(pa - a) + Math.Abs(pb - b) > 3) Put(pa, pb, Props.MachineParts, (ArchPier)rng.Range(0, 3));
            }
        }

        /// <summary>An abandoned camp in a corner: a tent or a sleeping bag, a bag, a chair, boxes, a cold barrel, a supply box gone through.</summary>
        private void Camp(RoomBox r)
        {
            if (r.W < 7 || r.D < 7) return;
            int corner = rng.Range(0, 3);
            bool west = corner % 2 == 0, north = corner < 2;
            int a = west ? r.X0 + 1 : r.X1 - 2, b = north ? r.Z0 + 1 : r.Z1 - 2;
            bool placed = false;
            if (rng.Chance(0.5))
            {
                // The tent: 2 by 2, its door toward the room (front-left part as PartTile has it)
                ArchPier facing = north ? ArchPier.South : ArchPier.North;
                int fa = facing == ArchPier.South ? a + 1 : a, fb = facing == ArchPier.South ? b + 1 : b;
                var parts = new (int A, int B)[4];
                bool ok = true;
                for (int n = 0; n < 4 && ok; n++)
                {
                    parts[n] = PartTile(fa, fb, facing, n % 2, n / 2);
                    ok = r.Inside(parts[n].A, parts[n].B) && Free(parts[n].A, parts[n].B) && SameCell(parts[0], parts[n]);
                }
                if (ok)
                {
                    for (int n = 0; n < 4; n++) Put(parts[n].A, parts[n].B, Props.CampTent, facing, (byte)n);
                    placed = true;
                }
            }
            if (!placed)
            {
                // A sleeping bag: head then foot, Pier from the head to the foot
                ArchPier toward = west ? ArchPier.East : ArchPier.West;
                var (dx, dz) = Step(toward);
                if (!Free(a, b) || !Free(a + dx, b + dz) || !SameCell((a, b), (a + dx, b + dz))) return;
                Put(a, b, Props.SleepingBag, toward, 0);
                Put(a + dx, b + dz, Props.SleepingBag, toward, 1);
            }
            plan.Camps++;
            int ca = west ? a + 3 : a - 2, cb = north ? b + 1 : b;
            plan.CampSpots.Add(plan.World(ca, cb));
            // What was left about it
            for (int k = 0; k < 6; k++)
            {
                int pa = ca + rng.Range(-1, 1), pb = cb + rng.Range(-2, 2);
                if (!r.Inside(pa, pb) || !Free(pa, pb)) continue;
                double p = rng.NextDouble();
                ArchPier dir = (ArchPier)rng.Range(0, 3);
                if (p < 0.25) Put(pa, pb, Props.Backpack, dir);
                else if (p < 0.45) Put(pa, pb, Props.FoldingChair, dir);
                else if (p < 0.6) Put(pa, pb, Props.CardboardBoxes, dir);
                else if (p < 0.72) Put(pa, pb, Props.BurnBarrel, dir);
                else if (p < 0.85)
                {
                    At(pa, pb).SupplyBox = true;
                    plan.Boxes++;
                }
            }
            // Whoever kept it: sometimes still there
            if (rng.Chance(0.35)) Corpse(r);
        }

        /// <summary>Whether two places of the plan lie in the same cell (a tent or a sleeping bag cut by a cell's edge is taken away: KeepPartsWhole).</summary>
        private bool SameCell((int A, int B) p, (int A, int B) q)
        {
            var (px, pz) = plan.World(p.A, p.B);
            var (qx, qz) = plan.World(q.A, q.B);
            return MacroOf(px) == MacroOf(qx) && MacroOf(pz) == MacroOf(qz);
        }

        /// <summary>A body: sitting against a wall, or lying where it fell; one in three with a makeshift spear beside it; dried blood.</summary>
        private void Corpse(RoomBox r)
        {
            for (int tries = 0; tries < 12; tries++)
            {
                int a = rng.Range(r.X0, r.X1), b = rng.Range(r.Z0, r.Z1);
                if (!Free(a, b)) continue;
                byte spear = (byte)(rng.Chance(0.35) ? 1 : 0);
                if (AgainstWall(a, b) is ArchPier wall && rng.Chance(0.6))
                    Put(a, b, Props.L15Corpse, Opp(wall), L15CorpseSitting, spear);
                else
                {
                    var (dx, dz, toward) = Dirs[rng.Range(0, 3)];
                    if (!Free(a + dx, b + dz) || !r.Inside(a + dx, b + dz)) continue;
                    Put(a, b, Props.L15Corpse, toward, L15CorpseHead, spear);
                    Put(a + dx, b + dz, Props.L15Corpse, toward, L15CorpseFeet, 0);
                }
                plan.Corpses++;
                // Dried blood on the floor round it
                for (int k = 0; k < 3; k++)
                {
                    int ba = a + rng.Range(-1, 1), bb = b + rng.Range(-1, 1);
                    if (L15Plan.In(ba, bb) && At(ba, bb).Kind == TileKind.Floor && At(ba, bb).Depth is L15FloorCeramic or L15FloorWorn or L15FloorCoating)
                        At(ba, bb).Depth = L15FloorBlood;
                }
                return;
            }
        }

        private void Blood(RoomBox r)
        {
            var rim = new List<(int A, int B, ArchPier Wall)>(Rim(r));
            var (a, b, wall) = rim[rng.Range(0, rim.Count - 1)];
            var (dx, dz) = Step(wall);
            Decorate(a + dx, b + dz, L15WallBlood, Opp(wall), 0);
            if (At(a, b).Kind == TileKind.Floor && At(a, b).Depth is L15FloorCeramic or L15FloorWorn) At(a, b).Depth = L15FloorBlood;
        }

        private void SupplyBox(RoomBox r)
        {
            for (int tries = 0; tries < 8; tries++)
            {
                int a = rng.Range(r.X0, r.X1), b = rng.Range(r.Z0, r.Z1);
                if (!Free(a, b) || AgainstWall(a, b) == null) continue;
                At(a, b).SupplyBox = true;
                plan.Boxes++;
                return;
            }
        }

        /// <summary>What is on a room's walls, inside: dead displays, vent grilles at the foot, a code scrawled by one.</summary>
        private void InnerWalls(RoomBox r, L15Zone kind, bool dark)
        {
            double display = kind switch
            {
                L15Zone.Lab or L15Zone.Control => 0.05, L15Zone.Machine => 0.03, L15Zone.Wreck or L15Zone.Star or L15Zone.Crematorium => 0, _ => 0.012,
            };
            foreach (var (a, b, wall) in Rim(r))
            {
                var (dx, dz) = Step(wall);
                double p = rng.NextDouble();
                if (p < 0.02) Decorate(a + dx, b + dz, rng.Chance(0.3) ? L15WallVentCode : L15WallVent, Opp(wall), 0);
                else if (kind is L15Zone.Machine or L15Zone.Wreck && p < 0.035) Decorate(a + dx, b + dz, L15WallHV, Opp(wall), 0);
                else if (p < 0.02 + display)
                {
                    double q = rng.NextDouble();
                    byte what = dark || q < 0.6 ? L15WallDisplay : q < 0.8 ? L15WallView : L15WallRadar;
                    Decorate(a + dx, b + dz, what, Opp(wall), (byte)rng.Range(0, L15Views - 1));
                }
            }
        }

        // ---------------- The wing's outer walls ----------------

        /// <summary>
        /// The faces of the wing's walls toward the main halls: a steel pilaster under each rib (every eight blocks), and
        /// between them now and then a dead display, a vent, a view of somewhere else.
        /// </summary>
        private void HallWalls()
        {
            for (int k = 0; k < N; k++)
            {
                int z = plan.World(0, k).Z, x = plan.World(k, 0).X;
                HallWall(-1, k, ArchPier.West, z);
                HallWall(N, k, ArchPier.East, z);
                HallWall(k, -1, ArchPier.North, x);
                HallWall(k, N, ArchPier.South, x);
            }
        }

        private void HallWall(int a, int b, ArchPier face, int along)
        {
            ref Tile t = ref At(a, b);
            if (t.Kind != TileKind.Wall) return;
            if (Hashing.Mod(along, 8) == 0)
            {
                if (t.Detail == L15WallPlain)
                {
                    t.Detail = rng.Chance(0.1) ? L15WallEtched : L15WallPilaster;
                    t.Pier = face;
                }
                return;
            }
            double p = rng.NextDouble();
            if (p < 0.012) Decorate(a, b, L15WallDisplay, face, 0);
            else if (p < 0.017) Decorate(a, b, L15WallView, face, (byte)rng.Range(0, L15Views - 1));
            else if (p < 0.03) Decorate(a, b, rng.Chance(0.25) ? L15WallVentCode : L15WallVent, face, 0);
        }
    }

    /// <summary>Which of the level's props (<see cref="Props.L15First"/>-<see cref="Props.L15Last"/>) people walk through: the stage, the lecture hall's steps (a step up).</summary>
    private static bool L15WalkThrough(ushort variant) => variant is Props.L15Stage or Props.L15Riser;

    // ================= Air =================

    /// <summary>The temperature: the level's own (clean conditioned air) where the power is on; four degrees cooler where it is out.</summary>
    private float L15Temperature(int x, int y, int z, int floorY) => LevelTemperatures[Level15] - (L15DarkAt(x, z) ? 4f : 0f);

    /// <summary>
    /// Reality stability: a little steadier than neutral in the clean lit halls; where the power is out the air goes stale
    /// (Fandom: the CO2 rises, dizziness, a slowing heart), and it tells on you.
    /// </summary>
    private float L15Stability(double x, double y, double z, int floorY, float drift) =>
        L15DarkAt((int)Math.Floor(x), (int)Math.Floor(z)) ? 0.7f + 0.1f * drift : 1.05f;
}
