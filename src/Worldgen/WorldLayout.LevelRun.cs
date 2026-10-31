using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level !, "Run For Your Life!": kept as level 14 (<see cref="RunLevel"/>) and shown as "!". One long hospital hallway
/// lit only by red EXIT signs; an alarm; a horde bursting out of a chained door behind you; and the one way out at the far
/// end. Like the Poolrooms it is not a ring: it lies far out to the south, a region you can only be taken into.
///
/// The region is <see cref="RunLanes"/> parallel hallways ("lanes"), one to a column of cells, sealed from each other
/// ("another hallway, and another human running just like him"): each runner gets one of their own. A lane is planned
/// once, whole, from its index (<see cref="RunLane"/>), 32 blocks wide and <see cref="RunLaneLength"/> long, north to
/// south:
///
/// - the first row: the start room (a hospital room in red light, the chained door with the antechamber behind it, the door
///   you came in by, the stuck door to the hallway);
/// - the next <see cref="RunRows"/> rows: the hallway, 5 wide and 4 high, with two doglegs (at each, straight ahead, a false EXIT door);
/// - the last row: the last stretch, unbroken walls, and the true exit in the dead end.
///
/// About 610-620 blocks from the hallway door to the exit: a minute and a half at a sprint (from layout version 9, with
/// <see cref="RunRows9"/> rows of hall, about 480: a minute and ten seconds). The chase itself is
/// <see cref="RunChase"/> (a pure model) driven by <c>Regions.RunSystem</c>.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x1400-0x14BF are this level's.</summary>
    private const ulong SaltRunLane = 0x1402, SaltRunDest = 0x1403, SaltRunSafe = 0x1404, SaltRunHole = 0x1405,
        SaltRunSigns = 0x1406, SaltRunProps = 0x1407, SaltRunEvents = 0x1408;

    // ================= Where it is =================

    /// <summary>The middle of the region, in macro cells: due south of spawn, as far out as the city is to the east.</summary>
    private int RunCentreX => spawnMacroX;
    private int RunCentreZ => spawnMacroZ + RegionReach;

    /// <summary>
    /// How many cells the region runs either side of its middle: north-south along the hallways (21 rows, 672 blocks: the
    /// start room's row, <see cref="RunRows"/> of hallway, the exit's row), and west-east across them (17 columns, one
    /// lane each).
    /// </summary>
    public const int RunHalfLength = 10, RunHalfWidth = 8;

    /// <summary>How many hallways lie side by side, one to a column of cells.</summary>
    public const int RunLanes = 2 * RunHalfWidth + 1;

    /// <summary>
    /// Rows of cells of hallway between the start room and the exit's row. A sprint in Vintage Story is about 6.8 blocks
    /// a second (see <see cref="RunChase.SprintSpeed"/>), so 19 rows make about 615 blocks of running: a minute and a half.
    /// </summary>
    public const int RunRows = 2 * RunHalfLength - 1;

    /// <summary>A lane's length in blocks (its rows of cells, start room to exit).</summary>
    public const int RunLaneLength = (2 * RunHalfLength + 1) * MacroSize;

    /// <summary>The block the level's plans count from: the north-west corner of the region.</summary>
    public int RunOriginX => (RunCentreX - RunHalfWidth) * MacroSize;
    public int RunOriginZ => (RunCentreZ - RunHalfLength) * MacroSize;

    private bool InRun(double mx, double mz) => Math.Abs(mx - RunCentreX) <= RunHalfWidth && Math.Abs(mz - RunCentreZ) <= RunHalfLength;

    /// <summary>The start room's cell of a lane picked by hash: arrivals are always in a start room.</summary>
    private (int Mx, int Mz) RunArrivalCell(ulong h) =>
        (RunCentreX - RunHalfWidth + (int)(Hashing.Mix(h) % RunLanes), RunCentreZ - RunHalfLength);

    /// <summary>Arriving: on the one marked tile of a start room, beside the bed.</summary>
    private static bool IsRunArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone == RunZone.StartRoom && (t.Detail & RunArrivalMark) != 0;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double RunArrivalHeight(in Tile t, double stand) => stand;

    // ================= Lanes, in world terms =================

    /// <summary>The lane a block position lies in, or -1 outside the region.</summary>
    public int RunLaneAt(int gx, int gz)
    {
        int lx = gx - RunOriginX, lz = gz - RunOriginZ;
        if (lx < 0 || lz < 0 || lx >= RunLanes * MacroSize || lz >= RunLaneLength) return -1;
        return lx / MacroSize;
    }

    /// <summary>The world position of a lane-local tile.</summary>
    public (int X, int Z) RunWorld(int lane, int x, int z) => (RunOriginX + lane * MacroSize + x, RunOriginZ + z);

    /// <summary>The lane-local position of a world block position in a lane.</summary>
    public (int X, int Z) RunLocal(int lane, int gx, int gz) => (gx - RunOriginX - lane * MacroSize, gz - RunOriginZ);

    /// <summary>
    /// A lane's plan (worked out once and kept). Room for every lane: the cells round a runner take in all seventeen,
    /// and building them row by row through a smaller cache planned a lane over again for nearly every cell.
    /// </summary>
    public RunLane RunPlan(int lane) => runPlans.Get(lane, 0);

    private PlanCache<RunLane> runPlans;

    /// <summary>
    /// Makes the plan caches of the levels from 7 up (the outer ring and the far places) when the layout is made, so that
    /// two worldgen threads arriving together at a level's first plan never each make one and throw the other's work away.
    /// (The capacities are what each level's plans need; see the field of each.)
    /// </summary>
    partial void CreateFarPlanCaches()
    {
        // (a lot is overlapped by two to four cells, each of which would plan it again: 32 covers the 3x3 blocks of six lots one cell touches)
        lotPlans = new PlanCache<Tile[]>(32, LotPlan);
        l8Dens = new LatticeMemo<DenKind>(1024, DenAt);
        l8Plans = new PlanCache<L8Plan>(256, PlanL8Cell);
        l8Trees = new PlanCache<HashSet<(int, int, int)>>(128, PlanL8Tree);
        blockPlans = new PlanCache<Tile[]>(64, PlanBlock);
        poolPlans = new PlanCache<Tile[]>(32, PlanPoolBlock);
        poolRoomPlans = new PlanCache<PoolRoom[]>(16, PlanPoolRooms);
        hills = new LatticeMemo<Hill>(4096, PlanHillAt);
        hillFences = new PlanCache<Dictionary<(int, int), (byte Joins, byte Height)>>(256, PlanHillFence);
        hillPlans = new PlanCache<HillPlan>(256, PlanHill);
        towns = new LatticeMemo<(int, int, int, int)?>(1024, PlanTownOf);
        townPlans = new PlanCache<Tile[]>(16, PlanTown);
        castlePlan = new Lazy<Tile[]>(PlanCastle);
        runPlans = new PlanCache<RunLane>(RunLanes, (i, _) => PlanRunLane(i));
        funPlans = new PlanCache<FunBlockPlan>(32, PlanFunBlock);
        endPlans = new PlanCache<Tile[]>(24, PlanEndDepartment);
        l974Plans = new PlanCache<Tile[]>(64, PlanKittyHouse);
        l3999Arcades = new PlanCache<L3999ArcadeSite>(64, PlanL3999Arcade);
        l3999Units = new PlanCache<IReadOnlyList<L3999Unit>>(1024, (i, j) => L3999PlanOf(i, j).Units);
        funRooms = new PlanCache<FunRoom[]>(512, (i, j) => FunPlan(i, j).Rooms);
        funPhases = new LatticeMemo<int>(1024, FunPhaseOf);
        endRunways = new LatticeMemo<(int Amplitude, double Period, double Phase)>(256, EndRunwayShape);
        endLongAisles = new LatticeMemo<bool>(1024, (left, seg) => EndKindAt(left, seg) == EndKind.LongLeft);
        l3999Plans = new PlanCache<L3999Plan>(16, PlanL3999Block);
        l188Plan = new Lazy<Tile[]>(PlanL188);
    }

    // ================= Cells =================

    /// <summary>
    /// The wall line between two of the level's cells: open, as the lanes' plans lay every wall themselves. (The rim,
    /// against the fields, is the usual solid wall.)
    /// </summary>
    private Edge RunEdge(int mx, int mz, bool west) => new() { Pattern = WallPattern.RunWall };

    private void BuildLevelRun(Builder b, int mx, int mz)
    {
        int lane = mx - (RunCentreX - RunHalfWidth), z0 = (mz - (RunCentreZ - RunHalfLength)) * MacroSize;
        RunLane plan = RunPlan(lane);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
                b.At(lx, lz) = plan.At(lx, z0 + lz);
    }

    /// <summary>Which of the level's props are walked through rather than around.</summary>
    private static bool RunWalkThrough(ushort variant) => variant is Props.RunToyCar or Props.RunBoxes or Props.RunCord
        or Props.RunSheets or Props.RunRemains or Props.RunDebris or Props.RunCurtain;

    // ================= What it is like =================

    private float RunTemperature(int x, int y, int z, int floorY)
    {
        Tile t = RunTileAt(x, z);
        return t.Zone switch { RunZone.StartRoom or RunZone.Antechamber => 18f, RunZone.Safe => 21f, _ => LevelTemperatures[RunLevel] };
    }

    /// <summary>Reality stability here: the alarm wears at you; the Safe Zone is a real rest.</summary>
    private float RunStability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = RunTileAt((int)Math.Floor(x), (int)Math.Floor(z));
        return t.Zone switch
        {
            RunZone.StartRoom or RunZone.Antechamber => 0.35f,
            RunZone.Safe => 1.25f,
            RunZone.ExitStretch => 0.8f,
            _ => 0.45f + 0.05f * drift,
        };
    }

    /// <summary>A tile of the level straight from its lane's plan (solid wall outside the lanes).</summary>
    private Tile RunTileAt(int gx, int gz)
    {
        int lane = RunLaneAt(gx, gz);
        if (lane < 0) return new Tile { Kind = TileKind.Wall, Pattern = WallPattern.RunWall, Level = RunLevel };
        var (x, z) = RunLocal(lane, gx, gz);
        return RunPlan(lane).At(x, z);
    }

    // ================= The ways in, in other levels =================

    private const ulong SaltRunEntranceL1 = 0x1410, SaltRunFalseWallL2 = 0x1411;

    /// <summary>Whether Level !'s ways in are laid into Levels 1, 2 and 37 (the harness turns them off to show they move nothing else).</summary>
    internal static bool RunEntrances = true;

    /// <summary>
    /// Level 1's car park, about one cell in 300: a red EXIT door where no door should be, in a solid wall between two
    /// districts, facing into this cell (on the wall tile: <see cref="Unders.RunEntrance"/>). Kept off any tile another
    /// level's entrance took first.
    /// </summary>
    private void MarkRunEntrance(Builder b, int mx, int mz)
    {
        ulong h = Hashing.Hash(seed, mx, mz, SaltRunEntranceL1);
        if (!RunEntrances || Hashing.Unit(h) >= (Version >= 12 ? 1.0 / 1200 : 1.0 / 300)) return;
        int start = (int)(Hashing.Mix(h) % 26);
        for (int k = 0; k < 52; k++)
        {
            int i = 3 + (start + k) % 26;
            bool westEdge = k < 26 == ((h >> 40 & 1) == 0);
            var (wx, wz, fx, fz) = westEdge ? (0, i, 1, i) : (i, 0, i, 1);
            ref Tile wall = ref b.At(wx, wz);
            Tile front = b.At(fx, fz);
            if (wall.Kind != TileKind.Wall || wall.Under != 0 || wall.Variant > 1 || wall.Pattern != WallPattern.Concrete) continue;
            if (front.Kind != TileKind.Floor || front.Variant != 0 || front.Stack != 0 || front.SupplyBox || front.Under != 0 || front.Stair != 0) continue;
            // (From layout version 9 a stair core backing onto a fire wall has the wall inside it: no door from its landing)
            if (Version >= 9 && front.Floor == FloorKind.L1Hall) continue;
            Tile a = westEdge ? b.At(0, i - 1) : b.At(i - 1, 0), c = westEdge ? b.At(0, i + 1) : b.At(i + 1, 0);
            if (a.Kind != TileKind.Wall || c.Kind != TileKind.Wall) continue;
            wall.Under = Unders.RunEntrance;
            wall.Pier = westEdge ? ArchPier.East : ArchPier.South;
            return;
        }
    }

    /// <summary>The four steps and the way each faces.</summary>
    private static readonly (int Dx, int Dz, ArchPier Toward)[] RunFalseWallDirs =
        { (1, 0, ArchPier.East), (-1, 0, ArchPier.West), (0, 1, ArchPier.South), (0, -1, ArchPier.North) };

    /// <summary>
    /// Level 2, about one cell in 250: where a tunnel ends blind, the rock just past its end is not there after all. It
    /// looks like smooth new concrete across the tunnel (on that tile: <see cref="Unders.RunFalseWall"/>); walk into it
    /// and you noclip into Level !.
    /// </summary>

    private void MarkRunFalseWall(Builder b, int mx, int mz)
    {
        ulong h = Hashing.Hash(seed, mx, mz, SaltRunFalseWallL2);
        if (!RunEntrances || Hashing.Unit(h) >= 1.0 / 250) return;
        bool Open(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && IsWalkable(b.At(x, z));
        bool Rock(int x, int z) => x >= 1 && z >= 1 && x < MacroSize && z < MacroSize && b.At(x, z).Kind == TileKind.Wall && b.At(x, z).Under == 0;
        int start = (int)(Hashing.Mix(h) % (ulong)(MacroSize * MacroSize));
        for (int k = 0; k < MacroSize * MacroSize; k++)
        {
            int index = (start + k) % (MacroSize * MacroSize);
            int x = index % MacroSize, z = index / MacroSize;
            if (x < 3 || z < 3 || x > MacroSize - 4 || z > MacroSize - 4) continue;
            Tile end = b.At(x, z);
            if (end.Kind != TileKind.Floor || end.Variant != 0 || end.Under != 0) continue;
            // A blind end: open one way only, rock the other three
            int opens = 0;
            (int Dx, int Dz, ArchPier Toward) back = default;
            foreach (var d in RunFalseWallDirs)
                if (Open(x + d.Dx, z + d.Dz)) { opens++; back = d; }
            if (opens != 1) continue;
            int wx = x - back.Dx, wz = z - back.Dz;
            // Solid rock past the end, two deep, so the wall that isn't there opens onto nothing
            if (!Rock(wx, wz) || !Rock(wx - back.Dx, wz - back.Dz) || !Rock(wx + back.Dz, wz + back.Dx) || !Rock(wx - back.Dz, wz - back.Dx)) continue;
            ref Tile w = ref b.At(wx, wz);
            w = new Tile { Kind = TileKind.Floor, Floor = end.Floor, Level = 2, Under = Unders.RunFalseWall, Pier = back.Toward };
            return;
        }
    }

    // ================= The plan of a lane =================

    /// <summary>What part of a lane a tile is in (<see cref="Tile.Zone"/> on the level's tiles).</summary>
    public static class RunZone
    {
        public const byte Hall = 0, StartRoom = 1, Safe = 2, Closet = 3, Antechamber = 4, ExitStretch = 5;
    }

    /// <summary><see cref="Tile.Detail"/> bits on the level's tiles.</summary>
    public const byte RunArrivalMark = 1, RunBeacon = 2, RunSignWE = 4, RunSafeSign = 8, RunSafeSignRight = 16,
        /// <summary>On a <see cref="FloorKind.RunBorder"/> tile: the band is along its east edge (else its west).</summary>
        RunBorderEast = 32,
        /// <summary>
        /// On a start-room wall (layout version 5): <see cref="Tile.Detail"/> / RunWallDecor (its top two bits) is what
        /// hangs on its <see cref="Tile.Pier"/> face at eye height: 1 a hand-washing notice, 2 visiting hours, 3 a
        /// hand-sanitiser dispenser.
        /// </summary>
        RunWallDecor = 64;

    /// <summary>The things that happen along a lane as a runner nears them (see <c>Regions.RunSystem</c>).</summary>
    public enum RunEventKind : byte
    {
        /// <summary>A side door flies open into the hall (at <see cref="RunEvent.S"/>, 9 blocks before it).</summary>
        Swing,
        /// <summary>Shelving standing by the wall tips across the hall.</summary>
        Topple,
        /// <summary>A dented door bursts once the runner is past it, and something comes out behind them.</summary>
        Dented,
        /// <summary>An air vent in the ceiling: something may drop out of it behind a runner.</summary>
        Vent,
        /// <summary>An EXIT sign that may hiss, flicker and burst into a wall of fire (one per run, at most).</summary>
        Sign,
    }

    /// <summary>
    /// One thing along a lane: what, where (lane-local), the course position it answers to, and which way it faces
    /// (a door: into the hall; a swinging door: also the edge of the hall tile its leaf comes to rest on, in Side).
    /// </summary>
    public readonly record struct RunEvent(RunEventKind Kind, int X, int Z, int S, ArchPier Face, ArchPier Side);

    /// <summary>A lane's plan: its tiles, its course, and what happens along it.</summary>
    public sealed class RunLane
    {
        public const int Width = MacroSize, Length = RunLaneLength;
        public readonly int Index;
        public readonly Tile[] Tiles = new Tile[Width * Length];
        /// <summary>Course position + 1000 of every tile on the course (0: none). See <see cref="ProgressAt"/>.</summary>
        internal readonly short[] Course = new short[Width * Length];
        /// <summary>The centre line, one tile for each course position from the hallway door (0) to the exit door.</summary>
        public readonly List<(int X, int Z)> Line = new();
        public readonly List<RunEvent> Events = new();
        /// <summary>Course positions of the hanging EXIT signs, in order.</summary>
        public readonly List<int> Signs = new();
        /// <summary>Where the exit leads: Level 1, Level 4 or The End.</summary>
        public int Destination;
        /// <summary>The Safe Zone's stretch of the course, or -1, -1.</summary>
        public int SafeFrom = -1, SafeTo = -1;
        /// <summary>Course positions where the middle and last thirds begin (the two doglegs).</summary>
        public int Middle, Last;
        /// <summary>The course position of the true exit door (the whole run's length).</summary>
        public int ExitS;
        public (int X, int Z) Arrival, ChainedDoor, HallDoor, MarkedDoor, ExitDoor, Bedside, Cabinet;
        /// <summary>The false exits, and the hall tile in front of each.</summary>
        public readonly List<(int X, int Z, int FrontX, int FrontZ)> FakeExits = new();
        /// <summary>The three straights of the hall: the centre column and the first and last rows of each.</summary>
        public readonly List<(int C, int Z0, int Z1)> Straights = new();
        public bool HasHole, HasSafe;

        public RunLane(int index) { Index = index; }

        public ref Tile At(int x, int z) => ref Tiles[z * Width + x];
        public bool In(int x, int z) => x >= 0 && z >= 0 && x < Width && z < Length;

        /// <summary>The course position of a lane-local tile, or null if it is not on the course.</summary>
        public int? ProgressAt(int x, int z)
        {
            if (!In(x, z)) return null;
            short c = Course[z * Width + x];
            return c == 0 ? null : c - 1000;
        }

        /// <summary>The centre-line tile at a course position (clamped to the course; before 0, back toward the chained door).</summary>
        public (int X, int Z) LineAt(int s)
        {
            if (s >= 0) return Line[Math.Min(s, Line.Count - 1)];
            return (HallDoor.X, Math.Max(ChainedDoor.Z, HallDoor.Z + s));
        }

        /// <summary>Which third of the run a course position is in (0, 1, 2).</summary>
        public int Third(int s) => s < Middle ? 0 : s < Last ? 1 : 2;
    }

    // ---- The planner ----

    private sealed class RunPlanner
    {
        public RunLane L;
        public Rng Rng;
        /// <summary>Per row of the lane, the columns of the hall blocked by something you must go round (bit k: centre + k - 2).</summary>
        public readonly Dictionary<int, int> Blocked = new();
        /// <summary>Rows where nothing may be put (clear zones round corners, doors that swing, the hole).</summary>
        public readonly HashSet<int> Reserved = new();
    }

    // The lane's fixed geometry (lane-local)
    private const int RunRoomX0 = 13, RunRoomX1 = 19, RunRoomZ0 = 17, RunRoomZ1 = 23, RunHallX = 16, RunHallDoorZ = 24, RunChainZ = 16,
        RunExitStretch = 24;

    /// <summary>
    /// Layout version 9: the hall runs <see cref="RunRows9"/> rows of cells, not <see cref="RunRows"/>, so the run is about
    /// 480 blocks rather than 615 (the user's play-test: too hard to reach the other side). The region keeps its 21 rows;
    /// past the exit's row the lane is solid wall.
    /// </summary>
    public const int RunRows9 = 15;

    /// <summary>Rows of hallway in this world's lanes.</summary>
    private int RunHallRows => Version >= 9 ? RunRows9 : RunRows;

    /// <summary>Where this world's lanes end: the true exit's row (lane-local z).</summary>
    private int RunExitAt => (RunHallRows + 1) * MacroSize - 20;

    private RunLane PlanRunLane(int lane)
    {
        var L = new RunLane(lane);
        var p = new RunPlanner { L = L, Rng = new Rng(Hashing.Hash(seed, lane, 0, SaltRunLane)) };
        for (int i = 0; i < L.Tiles.Length; i++) L.Tiles[i] = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.RunWall, Level = RunLevel };

        PlanRunDestination(L);
        PlanRunStartRoom(L, Version >= 5);

        // The hallway: south from the hallway door, a dogleg in row -3 and another in row +2, on to the exit
        int c1 = RunHallX, rows = RunHallRows, exitZ = RunExitAt;
        int j1 = (1 + rows / 3) * MacroSize + p.Rng.Range(6, 20), j2 = (1 + 2 * rows / 3) * MacroSize + p.Rng.Range(6, 20);
        int d1 = p.Rng.Range(8, 10) * (p.Rng.Chance(0.5) ? 1 : -1);
        int c2 = c1 + d1;
        int c3 = c2 - Math.Sign(d1) * p.Rng.Range(8, 10);
        RunCarve(L, c1 - 2, c1 + 2, RunHallDoorZ + 1, j1 + 4);
        RunCarve(L, Math.Min(c1, c2) - 2, Math.Max(c1, c2) + 2, j1, j1 + 4);
        RunCarve(L, c2 - 2, c2 + 2, j1, j2 + 4);
        RunCarve(L, Math.Min(c2, c3) - 2, Math.Max(c2, c3) + 2, j2, j2 + 4);
        RunCarve(L, c3 - 2, c3 + 2, j2, exitZ - 1);
        for (int z = exitZ - RunExitStretch; z < exitZ; z++)
            for (int x = c3 - 2; x <= c3 + 2; x++) L.At(x, z).Zone = RunZone.ExitStretch;

        // Straight ahead at the first corner of each dogleg, a false exit with an empty closet behind it
        RunFakeExit(L, c1, j1 + 5);
        RunFakeExit(L, c2, j2 + 5);
        L.ExitDoor = (c3, exitZ);
        ref Tile exit = ref L.At(c3, exitZ);
        exit.Kind = TileKind.Door;
        exit.Pattern = WallPattern.RunTrueExit;
        exit.Pier = ArchPier.North;

        // The centre line, and the course
        void Line(int x0, int z0, int x1, int z1)
        {
            int dx = Math.Sign(x1 - x0), dz = Math.Sign(z1 - z0);
            for (int x = x0, z = z0; ; x += dx, z += dz)
            {
                if (L.Line.Count == 0 || L.Line[^1] != (x, z)) L.Line.Add((x, z));
                if (x == x1 && z == z1) break;
            }
        }
        Line(c1, RunHallDoorZ, c1, j1 + 2);
        Line(c1, j1 + 2, c2, j1 + 2);
        Line(c2, j1 + 2, c2, j2 + 2);
        Line(c2, j2 + 2, c3, j2 + 2);
        Line(c3, j2 + 2, c3, exitZ);
        L.ExitS = L.Line.Count - 1;
        L.Middle = RunLineIndex(L, c1, j1 + 2);
        L.Last = RunLineIndex(L, c2, j2 + 2);
        PlanRunSafeZone(L, p, c2, j1, j2);
        RunCourse(L);
        foreach (var f in L.FakeExits) L.Course[f.Z * RunLane.Width + f.X] = L.Course[f.FrontZ * RunLane.Width + f.FrontX];

        // Clear zones: the start of the hall, round each corner and false exit, the last steps to the exit, the Safe Zone
        for (int z = RunHallDoorZ; z <= RunHallDoorZ + 12; z++) p.Reserved.Add(z);
        foreach (int j in new[] { j1, j2 })
            for (int z = j - 6; z <= j + 10; z++) p.Reserved.Add(z);
        for (int z = exitZ - 6; z < exitZ; z++) p.Reserved.Add(z);
        if (L.HasSafe)
            for (int z = L.LineAt(L.SafeFrom).Z - 4; z <= L.LineAt(L.SafeTo).Z + 4; z++) p.Reserved.Add(z);

        // The straights, each with its centre, for doors and what stands in the way
        var straights = new List<(int C, int Z0, int Z1)> { (c1, RunHallDoorZ + 1, j1 - 1), (c2, j1 + 5, j2 - 1), (c3, j2 + 5, exitZ - 1) };
        L.Straights.AddRange(straights);
        PlanRunDoors(L, p, straights);
        PlanRunHole(L, p, c3, j2);
        PlanRunObstacles(L, p, straights, gauntlet: Version >= 6);
        PlanRunSigns(L);
        PlanRunTrim(L);
        return L;
    }

    /// <summary>Where a lane's exit leads: 3 lanes in 17 to The End, 5 to the Abandoned Office, the rest to the Habitable Zone.</summary>
    private void PlanRunDestination(RunLane L)
    {
        // Rank the lanes by hash; the first three go to The End, the next five to Level 4
        ulong mine = Hashing.Hash(seed, L.Index, 0, SaltRunDest);
        int rank = 0;
        for (int i = 0; i < RunLanes; i++)
        {
            ulong other = Hashing.Hash(seed, i, 0, SaltRunDest);
            if (other < mine || other == mine && i < L.Index) rank++;
        }
        L.Destination = rank < 3 ? TheEnd : rank < 8 ? 4 : 1;
        L.HasSafe = Hashing.Unit(Hashing.Hash(seed, L.Index, 1, SaltRunSafe)) < 0.2;
        L.HasHole = Hashing.Unit(Hashing.Hash(seed, L.Index, 2, SaltRunHole)) < 1.0 / 3;
    }

    private static void RunFloor(ref Tile t, byte zone)
    {
        t.Kind = TileKind.Floor;
        t.Pattern = WallPattern.RunWall;
        t.Floor = FloorKind.RunFloor;
        t.Ceiling = CeilingKind.RunCeiling;
        t.Grand = true;
        t.Zone = zone;
    }

    private static void RunCarve(RunLane L, int x0, int x1, int z0, int z1)
    {
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
                if (L.At(x, z).Kind == TileKind.Wall) RunFloor(ref L.At(x, z), RunZone.Hall);
    }

    private static int RunLineIndex(RunLane L, int x, int z) => Math.Max(0, L.Line.IndexOf((x, z)));

    private static void RunDoor(RunLane L, int x, int z, WallPattern pattern, ArchPier face, TileKind kind = TileKind.Door)
    {
        ref Tile t = ref L.At(x, z);
        t.Kind = kind;
        t.Pattern = pattern;
        t.Pier = face;
        t.Grand = true;
    }

    /// <summary>
    /// The start room, the antechamber behind its chained door, and its three doors; <paramref name="dressed"/> (layout
    /// version 5): its walls dressed as a hospital room's.
    /// </summary>
    private static void PlanRunStartRoom(RunLane L, bool dressed)
    {
        for (int z = RunRoomZ0; z <= RunRoomZ1; z++)
            for (int x = RunRoomX0; x <= RunRoomX1; x++) RunFloor(ref L.At(x, z), RunZone.StartRoom);
        // Behind the chained door: black, and full of something
        for (int z = 12; z <= 15; z++)
            for (int x = 14; x <= 18; x++)
            {
                RunFloor(ref L.At(x, z), RunZone.Antechamber);
                L.At(x, z).Ceiling = CeilingKind.RunPanelDead;
            }
        for (int z = 11; z <= 15; z++)
        {
            L.At(13, z).Pattern = WallPattern.RunVoid;
            L.At(19, z).Pattern = WallPattern.RunVoid;
        }
        for (int x = 13; x <= 19; x++) L.At(x, 11).Pattern = WallPattern.RunVoid;

        L.ChainedDoor = (RunHallX, RunChainZ);
        RunDoor(L, RunHallX, RunChainZ, WallPattern.RunChainedDoor, ArchPier.South);
        L.HallDoor = (RunHallX, RunHallDoorZ);
        RunDoor(L, RunHallX, RunHallDoorZ, WallPattern.RunHallDoor, ArchPier.South, TileKind.Doorway);
        L.At(RunHallX, RunHallDoorZ).Zone = RunZone.StartRoom;
        L.MarkedDoor = (RunRoomX0 - 1, 20);
        RunDoor(L, RunRoomX0 - 1, 20, WallPattern.RunMarkedDoor, ArchPier.East);
        // The bed along the east wall, head to the north; the bedside table, the cabinet, the curtain
        ref Tile head = ref L.At(19, 18);
        ref Tile foot = ref L.At(19, 19);
        head.Variant = foot.Variant = Props.HospitalBed;
        head.Pier = foot.Pier = ArchPier.South;
        foot.Stack = 1;
        L.Bedside = (19, 20);
        L.At(19, 20).Variant = Props.RunBedside;
        L.At(19, 20).Pier = ArchPier.West;
        L.Cabinet = (RunRoomX1 + 1, 22);
        L.At(RunRoomX1 + 1, 22).Pattern = WallPattern.RunMedCabinet;
        L.At(RunRoomX1 + 1, 22).Pier = ArchPier.West;
        for (int z = 17; z <= 19; z++)
        {
            L.At(17, z).Variant = Props.RunCurtain;
            L.At(17, z).Pier = ArchPier.West;
        }
        L.At(RunHallX, 20).Ceiling = CeilingKind.LampRed;
        L.Arrival = (14, 21);
        L.At(14, 21).Detail |= RunArrivalMark;
        if (!dressed) return;

        // A hospital room before the red is explained: the hallway's crash rail along its walls (not behind the bed and
        // its table; under the cabinet the generator draws it), visiting hours by the marked door, and either side of the
        // door to the hall a hand-washing notice and a sanitiser dispenser (no rail there: that wall's other face carries
        // the hall's)
        void Dress(int x, int z, ArchPier into, int decor, bool rail = true)
        {
            ref Tile w = ref L.At(x, z);
            if (w.Kind != TileKind.Wall || w.Pattern != WallPattern.RunWall) return;
            if (rail) w.Pattern = WallPattern.RunWallRail;
            w.Pier = into;
            w.Detail |= (byte)(decor * RunWallDecor);
        }
        for (int z = RunRoomZ0; z <= RunRoomZ1; z++)
        {
            Dress(RunRoomX0 - 1, z, ArchPier.East, z == 22 ? 2 : 0);
            if (z is < 18 or > 20) Dress(RunRoomX1 + 1, z, ArchPier.West, 0);
        }
        for (int x = RunRoomX0; x <= RunRoomX1; x++) Dress(x, RunChainZ, ArchPier.South, 0);
        Dress(RunRoomX0, RunHallDoorZ, ArchPier.North, 1, rail: false);
        Dress(RunRoomX1, RunHallDoorZ, ArchPier.North, 3, rail: false);
    }

    /// <summary>A false exit in the end wall at (x, z), looking north up the hall, with an empty closet behind it.</summary>
    private static void RunFakeExit(RunLane L, int x, int z)
    {
        RunDoor(L, x, z, WallPattern.RunFakeExit, ArchPier.North);
        for (int cz = z + 1; cz <= z + 3; cz++)
            for (int cx = x - 1; cx <= x + 1; cx++)
            {
                RunFloor(ref L.At(cx, cz), RunZone.Closet);
                L.At(cx, cz).Ceiling = CeilingKind.RunPanelDead;
            }
        for (int cz = z; cz <= z + 4; cz++)
            for (int cx = x - 2; cx <= x + 2; cx++)
                if (L.At(cx, cz).Kind == TileKind.Wall && (cz > z || Math.Abs(cx - x) == 2)) L.At(cx, cz).Pattern = WallPattern.RunVoid;
        L.FakeExits.Add((x, z, x, z - 1));
    }

    private static readonly (int Dx, int Dz)[] RunCourseSteps = { (0, 1), (0, -1), (1, 0), (-1, 0) };

    /// <summary>The course: how far along it every tile of the start room and the hall is (a walk from the chained door).</summary>
    private static void RunCourse(RunLane L)
    {
        var dist = new int[L.Tiles.Length];
        Array.Fill(dist, -1);
        var queue = new Queue<int>();
        int start = L.ChainedDoor.Z * RunLane.Width + L.ChainedDoor.X;
        dist[start] = 0;
        queue.Enqueue(start);
        // The antechamber too, behind the chained door (the horde starts there)
        while (queue.Count > 0)
        {
            int i = queue.Dequeue();
            int x = i % RunLane.Width, z = i / RunLane.Width;
            foreach ((int dx, int dz) in RunCourseSteps)
            {
                int nx = x + dx, nz = z + dz;
                if (!L.In(nx, nz)) continue;
                int n = nz * RunLane.Width + nx;
                if (dist[n] >= 0) continue;
                Tile t = L.Tiles[n];
                bool open = t.Kind is TileKind.Floor or TileKind.Doorway && t.Zone != RunZone.Closet
                    || n == L.ExitDoor.Z * RunLane.Width + L.ExitDoor.X;
                if (!open) continue;
                dist[n] = dist[i] + 1;
                queue.Enqueue(n);
            }
        }
        int door = dist[L.HallDoor.Z * RunLane.Width + L.HallDoor.X];
        for (int i = 0; i < dist.Length; i++)
            if (dist[i] >= 0) L.Course[i] = (short)(dist[i] - door + 1000);
    }

    /// <summary>One lane in five has the Safe Zone: 24 blocks of the middle straight in blue, with two rooms off it.</summary>
    private static void PlanRunSafeZone(RunLane L, RunPlanner p, int c, int j1, int j2)
    {
        if (!L.HasSafe) return;
        int m = p.Rng.Range(j1 + 30, j2 - 50);
        int inner = Math.Sign(RunHallX - c), outer = -inner;
        for (int z = m; z < m + 24; z++)
        {
            for (int x = c - 2; x <= c + 2; x++)
            {
                ref Tile t = ref L.At(x, z);
                t.Zone = RunZone.Safe;
                t.Floor = FloorKind.RunSafeFloor;
                t.Ceiling = x == c && (z - m) % 4 == 1 ? CeilingKind.RunSafeLight : CeilingKind.RunCeiling;
            }
            L.At(c - 3, z).Pattern = WallPattern.RunSafeWall;
            L.At(c + 3, z).Pattern = WallPattern.RunSafeWall;
        }
        // The welcome, on the outer wall
        foreach ((int dz, byte bits) in new[] { (11, RunSafeSign), (12, (byte)(RunSafeSign | RunSafeSignRight)) })
        {
            ref Tile w = ref L.At(c + 3 * outer, m + dz);
            w.Detail = bits;
            w.Pier = inner > 0 ? ArchPier.East : ArchPier.West;
        }
        // Two rooms on the inner side, each with a shelf of supplies and a cot
        foreach (int r in new[] { m + 3, m + 15 })
        {
            for (int z = r; z <= r + 4; z++)
                for (int k = 4; k <= 7; k++)
                {
                    ref Tile t = ref L.At(c + k * inner, z);
                    RunFloor(ref t, RunZone.Safe);
                    t.Floor = FloorKind.RunSafeFloor;
                    t.Ceiling = k == 5 && z == r + 2 ? CeilingKind.RunSafeLight : CeilingKind.RunCeiling;
                }
            for (int z = r - 1; z <= r + 5; z++)
                for (int k = 3; k <= 8; k++)
                    if (L.At(c + k * inner, z).Kind == TileKind.Wall) L.At(c + k * inner, z).Pattern = WallPattern.RunSafeWall;
            RunDoor(L, c + 3 * inner, r + 2, WallPattern.RunSafeDoor, inner > 0 ? ArchPier.West : ArchPier.East, TileKind.Doorway);
            L.At(c + 3 * inner, r + 2).Zone = RunZone.Safe;
            ArchPier toHall = inner > 0 ? ArchPier.West : ArchPier.East;
            ref Tile shelf = ref L.At(c + 7 * inner, r + 1);
            shelf.Variant = Props.RunSafeShelf;
            shelf.Pier = toHall;
            ref Tile head = ref L.At(c + 7 * inner, r + 3);
            ref Tile foot = ref L.At(c + 7 * inner, r + 4);
            head.Variant = foot.Variant = Props.RunSafeCot;
            head.Pier = foot.Pier = ArchPier.South;
            foot.Stack = 1;
        }
        L.SafeFrom = RunLineIndex(L, c, m);
        L.SafeTo = RunLineIndex(L, c, m + 23);
    }

    /// <summary>
    /// Locked steel doors down both walls of every straight (one every 4 blocks a side, the sides staggered by 2), a
    /// beacon over every fifth; some dented (something comes out), some that fly open as you come; shelving that topples.
    /// </summary>
    private void PlanRunDoors(RunLane L, RunPlanner p, List<(int C, int Z0, int Z1)> straights)
    {
        var rng = new Rng(Hashing.Hash(seed, L.Index, 3, SaltRunEvents));
        var doors = new List<(int X, int Z, ArchPier Face, int S)>();
        int count = 0;
        foreach (var (c, z0, z1) in straights)
        {
            for (int z = z0 + 3; z <= z1 - 3; z++)
            {
                if (z >= RunExitAt - RunExitStretch) break;
                bool west = Hashing.Mod(z, 4) == 0, east = Hashing.Mod(z, 4) == 2;
                if (!west && !east) continue;
                int x = west ? c - 3 : c + 3, behind = west ? x - 1 : x + 1;
                if (L.At(x, z).Kind != TileKind.Wall || L.At(x, z).Pattern != WallPattern.RunWall) continue;
                if (L.At(behind, z).Kind != TileKind.Wall || L.At(x, z - 1).Kind != TileKind.Wall || L.At(x, z + 1).Kind != TileKind.Wall) continue;
                if (L.At(west ? x + 1 : x - 1, z).Zone != RunZone.Hall) continue;
                ArchPier face = west ? ArchPier.East : ArchPier.West;
                RunDoor(L, x, z, WallPattern.RunSideDoor, face);
                if (count++ % 5 == 2) L.At(x, z).Detail |= RunBeacon;
                doors.Add((x, z, face, L.ProgressAt(west ? x + 1 : x - 1, z) ?? 0));
            }
        }

        // Dented doors: one in the first third, one or two in the middle, one in the last
        void Pick(int third, int n, Func<(int X, int Z, ArchPier Face, int S), bool> use)
        {
            var pool = doors.FindAll(d => L.Third(d.S) == third && L.At(d.X, d.Z).Pattern == WallPattern.RunSideDoor
                && !p.Reserved.Contains(d.Z) && !p.Reserved.Contains(d.Z - 1) && !p.Reserved.Contains(d.Z + 1));
            for (int k = 0; k < n && pool.Count > 0; k++)
            {
                int i = rng.Range(0, pool.Count - 1);
                if (!use(pool[i])) k--;
                pool.RemoveAt(i);
            }
        }
        bool Dent((int X, int Z, ArchPier Face, int S) d)
        {
            L.At(d.X, d.Z).Pattern = WallPattern.RunDentedDoor;
            L.Events.Add(new RunEvent(RunEventKind.Dented, d.X, d.Z, d.S + 2, d.Face, d.Face));
            return true;
        }
        bool Swing((int X, int Z, ArchPier Face, int S) d)
        {
            L.At(d.X, d.Z).Pattern = WallPattern.RunSwingDoor;
            ArchPier side = rng.Chance(0.5) ? ArchPier.North : ArchPier.South;
            L.Events.Add(new RunEvent(RunEventKind.Swing, d.X, d.Z, d.S - 9, d.Face, side));
            for (int z = d.Z - 1; z <= d.Z + 1; z++) p.Reserved.Add(z);
            return true;
        }
        Pick(0, 1, Dent);
        Pick(1, rng.Range(1, 2), Dent);
        Pick(2, 1, Dent);
        Pick(1, rng.Range(3, 4), Swing);
        Pick(2, rng.Range(3, 4), Swing);

        // Shelving standing by the wall that topples across the hall: one in the middle, one in the last third
        foreach (int third in new[] { 1, 2 })
        {
            for (int attempt = 0; attempt < 20; attempt++)
            {
                var (c, z0, z1) = straights[third];
                int z = rng.Range(z0 + 8, z1 - 8);
                if (z >= RunExitAt - RunExitStretch || p.Reserved.Contains(z) || p.Reserved.Contains(z + 1) || p.Blocked.ContainsKey(z)) continue;
                int side = rng.Chance(0.5) ? -1 : 1;
                int x = c + 2 * side;
                ref Tile t = ref L.At(x, z);
                if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Zone != RunZone.Hall) continue;
                t.Variant = Props.RunShelfStanding;
                t.Pier = side < 0 ? ArchPier.East : ArchPier.West;
                p.Blocked[z] = 1 << (2 + 2 * side);
                for (int r = z - 2; r <= z + 2; r++) p.Reserved.Add(r);
                L.Events.Add(new RunEvent(RunEventKind.Topple, x, z, (L.ProgressAt(x, z) ?? 0) - 10, t.Pier, t.Pier));
                break;
            }
        }
    }

    /// <summary>One lane in three has a hole in the dark last stretch, cracks in the floor before it.</summary>
    private void PlanRunHole(RunLane L, RunPlanner p, int c, int j2)
    {
        if (!L.HasHole) return;
        int h = p.Rng.Range(j2 + 40, RunExitAt - RunExitStretch - 12);
        for (int tries = 0; tries < 10 && (p.Reserved.Contains(h - 5) || p.Reserved.Contains(h + 3)); tries++) h += 7;
        int side = p.Rng.Chance(0.5) ? -1 : 1;
        for (int z = h - 4; z <= h + 1; z++)
            for (int k = 1; k <= 2; k++)
            {
                ref Tile t = ref L.At(c + k * side, z);
                if (z < h) t.Floor = FloorKind.RunCracked;
                else
                {
                    t.Kind = TileKind.Pit;
                    t.Under = Unders.RunHole;
                }
            }
        for (int z = h - 6; z <= h + 4; z++) p.Reserved.Add(z);
        p.Blocked[h] = p.Blocked[h + 1] = side < 0 ? 0b00011 : 0b11000;
    }

    /// <summary>
    /// What stands in the way, by thirds, never more than three of the five tiles of a row, always a way through; or
    /// (<paramref name="gauntlet"/>, layout version 6) the hall packed with it (see <see cref="PlanRunGauntlet"/>).
    /// </summary>
    private void PlanRunObstacles(RunLane L, RunPlanner p, List<(int C, int Z0, int Z1)> straights, bool gauntlet = false)
    {
        var rng = new Rng(Hashing.Hash(seed, L.Index, 4, SaltRunProps));
        bool Fits(Dictionary<int, int> adds)
        {
            foreach (var (z, mask) in adds)
            {
                if (p.Reserved.Contains(z)) return false;
                int row = (p.Blocked.TryGetValue(z, out int m) ? m : 0) | mask;
                if (System.Numerics.BitOperations.PopCount((uint)row) > 3) return false;
                for (int dz = -3; dz <= 3; dz++)
                {
                    if (dz == 0 || !p.Blocked.TryGetValue(z + dz, out int other)) continue;
                    if (adds.TryGetValue(z + dz, out int also)) other |= also;
                    if ((~row & ~other & 0x1F) == 0) return false;
                }
            }
            return true;
        }
        void Put(int c, int z, int k, ushort prop, ArchPier pier, byte stack = 0)
        {
            ref Tile t = ref L.At(c + k - 2, z);
            t.Variant = prop;
            t.Pier = pier;
            t.Stack = stack;
        }
        void Commit(Dictionary<int, int> adds)
        {
            foreach (var (z, mask) in adds) p.Blocked[z] = (p.Blocked.TryGetValue(z, out int m) ? m : 0) | mask;
        }
        bool Free(int c, int z, int k) => L.At(c + k - 2, z) is { Kind: TileKind.Floor, Variant: 0 } t && t.Zone is RunZone.Hall or RunZone.ExitStretch;

        int third = 0;
        foreach (var (c, z0, z1) in straights)
        {
            if (gauntlet) PlanRunGauntlet(L, p, rng, c, z0, z1, third);
            int z = gauntlet ? z1 : z0 + rng.Range(4, 10);
            while (z < z1 - 2)
            {
                int k = rng.Range(0, 4);
                double roll = rng.NextDouble();
                var adds = new Dictionary<int, int>();
                Action place = null;
                if (roll < 0.22 && Free(c, z, k) && Free(c, z + 1, k))
                {
                    // A gurney along the hall
                    adds[z] = 1 << k;
                    adds[z + 1] = 1 << k;
                    int kk = k;
                    place = () => { Put(c, z, kk, Props.RunGurney, ArchPier.South); Put(c, z + 1, kk, Props.RunGurney, ArchPier.South, 1); };
                }
                else if (roll < 0.40 && k <= 3 && Free(c, z, k) && Free(c, z, k + 1))
                {
                    // A gurney across it, and sometimes a wheelchair on the other side
                    adds[z] = 3 << k;
                    int kk = k, other = k <= 1 ? 4 : 0;
                    bool chair = rng.Chance(0.5) && Free(c, z, other);
                    if (chair) adds[z] |= 1 << other;
                    place = () =>
                    {
                        Put(c, z, kk, Props.RunGurney, ArchPier.East);
                        Put(c, z, kk + 1, Props.RunGurney, ArchPier.East, 1);
                        if (chair) Put(c, z, other, Props.RunWheelchair, ArchPier.North);
                    };
                }
                else if (roll < 0.55 && Free(c, z, k))
                {
                    adds[z] = 1 << k;
                    int kk = k;
                    var pier = (ArchPier)rng.Range(0, 3);
                    place = () => Put(c, z, kk, Props.RunWheelchair, pier);
                }
                else if (roll < 0.65 && Free(c, z, k))
                {
                    adds[z] = 1 << k;
                    int kk = k;
                    place = () => Put(c, z, kk, Props.RunIvStand, ArchPier.North);
                }
                else if (roll < 0.75)
                {
                    // Against a wall: waiting-room chairs, or (from the middle on) a crash cart
                    int wk = rng.Chance(0.5) ? 0 : 4;
                    if (Free(c, z, wk))
                    {
                        adds[z] = 1 << wk;
                        ushort prop = third >= 1 && rng.Chance(0.5) ? Props.RunCrashCart : Props.RunChairs;
                        var pier = wk == 0 ? ArchPier.East : ArchPier.West;
                        place = () => Put(c, z, wk, prop, pier);
                    }
                }
                else if (roll < 0.85 && third >= 1)
                {
                    // Shelving lying across the hall from a wall: jump it
                    int wk = rng.Chance(0.5) ? 0 : 4, nk = wk == 0 ? 1 : 3;
                    if (Free(c, z, wk) && Free(c, z, nk))
                    {
                        adds[z] = 0;
                        var pier = wk == 0 ? ArchPier.East : ArchPier.West;
                        place = () => { Put(c, z, wk, Props.RunShelfFallen, pier); Put(c, z, nk, Props.RunShelfFallen, pier, 1); };
                    }
                }
                else if (third == 2 || roll >= 0.85)
                {
                    // Small things on the floor that trip a sprinter (mostly in the dark last third), or sheets
                    adds[z] = 0;
                    double what = rng.NextDouble();
                    if (third == 2 && what < 0.25)
                    {
                        place = () => { for (int i = 0; i < 5; i++) if (Free(c, z, i)) Put(c, z, i, Props.RunCord, ArchPier.East); };
                    }
                    else if (Free(c, z, k))
                    {
                        int kk = k;
                        ushort prop = third < 2 && what < 0.6 ? Props.RunSheets : what < 0.5 ? Props.RunToyCar : what < 0.8 ? Props.RunBoxes : Props.RunDebris;
                        var pier = (ArchPier)rng.Range(0, 3);
                        place = () => Put(c, z, kk, prop, pier);
                    }
                }
                if (place != null && adds.Count > 0 && Fits(adds))
                {
                    place();
                    Commit(adds);
                    int gap = third switch { 0 => 16, 1 => 14, _ => 12 };
                    z += gap + rng.Range(-4, 4);
                }
                else z += 1;
            }

            // Supplies, half hidden beside a door; the remains of those who didn't make it
            for (int n = rng.Range(0, 1) + (third == 1 ? 1 : 0); n > 0; n--)
            {
                for (int attempt = 0; attempt < 30; attempt++)
                {
                    int tz = rng.Range(z0 + 4, z1 - 4);
                    int wk = rng.Chance(0.5) ? 0 : 4;
                    int wallX = c + (wk == 0 ? -3 : 3);
                    bool byDoor = L.At(wallX, tz + 1).Kind == TileKind.Door || L.At(wallX, tz - 1).Kind == TileKind.Door;
                    if (!byDoor || !Free(c, tz, wk)) continue;
                    var adds = new Dictionary<int, int> { [tz] = 1 << wk };
                    if (gauntlet ? p.Reserved.Contains(tz) : !Fits(adds)) continue;
                    Tile before = L.At(c + wk - 2, tz);
                    Put(c, tz, wk, Props.RunTray, wk == 0 ? ArchPier.East : ArchPier.West, (byte)(rng.Chance(0.6) ? 0 : 1));
                    if (gauntlet && !RunSprintable(L, c, z0, z1))
                    {
                        L.At(c + wk - 2, tz) = before;
                        continue;
                    }
                    Commit(adds);
                    break;
                }
            }
            for (int n = rng.Range(0, 1) + (third == 2 ? 1 : 0); n > 0; n--)
            {
                for (int attempt = 0; attempt < 30; attempt++)
                {
                    int tz = rng.Range(z0 + 4, z1 - 4), k = rng.Range(0, 4);
                    if (p.Reserved.Contains(tz) || !Free(c, tz, k)) continue;
                    Put(c, tz, k, Props.RunRemains, (ArchPier)rng.Range(0, 3));
                    // Scuffs, drag marks and claw scratches round it
                    for (int dz = -3; dz <= 3; dz++)
                        for (int dk = -2; dk <= 2; dk++)
                        {
                            int x = c + k - 2 + dk;
                            if (L.In(x, tz + dz) && L.At(x, tz + dz).Kind == TileKind.Floor && L.At(x, tz + dz).Floor == FloorKind.RunFloor
                                && Math.Abs(dz) + Math.Abs(dk) <= 3 && rng.Chance(0.7))
                                L.At(x, tz + dz).Floor = FloorKind.RunScuffed;
                        }
                    break;
                }
            }
            third++;
        }
    }

    /// <summary>
    /// How a runner gets past a tile of the hall: 0 over it (what trips you is still underfoot), 1 jumping it (a block high
    /// at most: a sprint-jump in Vintage Story rises about 1.25 blocks), 2 only round it (two blocks high, a pit, a wall).
    /// </summary>
    public static int RunHurdle(in Tile t)
    {
        if (t.Kind == TileKind.Doorway) return 0;
        if (t.Kind != TileKind.Floor) return 2;
        if (t.Variant == 0 || RunWalkThrough(t.Variant)) return 0;
        return t.Variant switch
        {
            Props.RunShelfStanding => 2,
            Props.RunCollapse => t.Stack == 0 ? 2 : 1,
            Props.RunBarricade => t.Stack <= 1 ? 2 : 1,
            _ => 1,
        };
    }

    /// <summary>
    /// Whether a runner (a block wide, two high, jumping a block) gets down rows z0..z1 of a straight centred on column c at
    /// a sprint: a row forward at a time and no more than one column across, never into anything they must go round nor
    /// between two such corner to corner. A door that swings open counts as its open leaf in the hall; shelving that
    /// topples, as standing (and its fallen half as fallen).
    /// </summary>
    public static bool RunSprintable(RunLane L, int c, int z0, int z1)
    {
        var leaves = new HashSet<(int, int)>();
        foreach (RunEvent e in L.Events)
            if (e.Kind == RunEventKind.Swing)
            {
                var (dx, dz) = FacingStep(e.Face);
                leaves.Add((e.X + dx, e.Z + dz));
            }
        int Hurdle(int k, int z) => leaves.Contains((c + k - 2, z)) ? 2 : RunHurdle(L.At(c + k - 2, z));
        int reach = 0;
        for (int k = 0; k < 5; k++)
            if (Hurdle(k, z0) < 2) reach |= 1 << k;
        for (int z = z0 + 1; z <= z1 && reach != 0; z++)
        {
            int next = 0;
            for (int k = 0; k < 5; k++)
            {
                if (Hurdle(k, z) == 2) continue;
                for (int from = Math.Max(0, k - 1); from <= Math.Min(4, k + 1); from++)
                {
                    if ((reach >> from & 1) == 0) continue;
                    if (from != k && Hurdle(from, z) == 2 && Hurdle(k, z - 1) == 2) continue;
                    next |= 1 << k;
                    break;
                }
            }
            reach = next;
        }
        return reach != 0;
    }

    /// <summary>
    /// Layout version 6: a straight packed with what a hospital leaves in its corridors and what the level throws down, a
    /// set piece every few blocks (closer together the further you get). The canon's "large obstacles (such as chairs, beds,
    /// etc.) may block the wanderers' progress … smaller obstacles (such as toy cars, boxes, etc.) are even more lethal"
    /// (Fandom), its collapsing ceilings with power lines hanging from them, and Escape the Backrooms' hallway: a whole
    /// line of objects to jump, tables and cabinets that "almost fully block your path", a blockade with the way round it
    /// beside. Barricades, tall cabinets and collapsed ceiling you must go round; gurneys, wheelchairs, chairs, carts,
    /// fallen shelving and rubble you can jump. Every piece is kept only if the straight can still be run at a sprint
    /// (<see cref="RunSprintable"/>).
    /// </summary>
    private void PlanRunGauntlet(RunLane L, RunPlanner p, Rng rng, int c, int z0, int z1, int third)
    {
        var piece = new List<(int Dz, int K, ushort Prop, byte Stack, ArchPier Pier)>();
        int side = rng.Chance(0.5) ? 1 : -1;
        // (k counts from the wall on the piece's side; mirrored for the other)
        void Add(int dz, int k, ushort prop, byte stack, ArchPier pier) => piece.Add((dz, k, prop, stack, pier));
        ArchPier In(int k) => k == 0 ? ArchPier.East : ArchPier.West; // facing into the hall from the wall at k (0 or 4)
        int Col(int k) => c + (side > 0 ? k : 4 - k) - 2;
        ArchPier Mirror(ArchPier a) => side > 0 ? a : a switch { ArchPier.East => ArchPier.West, ArchPier.West => ArchPier.East, _ => a };
        bool Free(int z, int col) => !p.Reserved.Contains(z) && z <= z1 - 1
            && L.At(col, z) is { Kind: TileKind.Floor, Variant: 0 } t && t.Zone is RunZone.Hall or RunZone.ExitStretch;
        void Small(int z, int col, ushort prop)
        {
            if (!Free(z, col)) return;
            ref Tile t = ref L.At(col, z);
            t.Variant = prop;
            t.Pier = (ArchPier)rng.Range(0, 3);
        }
        ushort JumpOne() => rng.Range(0, 2) switch { 0 => Props.RunWheelchair, 1 => Props.RunIvStand, _ => Props.RunWheelchair };

        // Weights of the set pieces by third: barricade, collapse, a line of things, a needle, a cabinet, gurneys,
        // fallen shelving, a tipped gurney, a feint by a door
        int[][] weights =
        {
            new[] { 18, 10, 8, 8, 14, 14, 6, 12, 10 },
            new[] { 16, 14, 12, 10, 10, 10, 10, 10, 8 },
            new[] { 14, 18, 14, 12, 8, 8, 10, 8, 8 },
        };
        int[] w = weights[Math.Min(third, 2)];
        int total = 0;
        foreach (int x in w) total += x;
        var undo = new List<(int X, int Z, Tile T)>();

        int z = z0 + rng.Range(3, 6);
        while (z < z1 - 2)
        {
            bool placed = false;
            int len = 1;
            for (int attempt = 0; attempt < 4 && !placed; attempt++)
            {
                piece.Clear();
                if (rng.Chance(0.7)) side = -side;
                int roll = rng.Range(0, total - 1), kind = 0;
                while (roll >= w[kind]) roll -= w[kind++];
                switch (kind)
                {
                    case 0:
                    {
                        // A barricade of beds and chairs from the wall, two to four wide, now and then two deep; something
                        // to jump on the other side
                        int wide = rng.Range(2, 4), deep = rng.Chance(0.3) ? 2 : 1;
                        for (int dz = 0; dz < deep; dz++)
                            for (int k = 0; k < wide; k++) Add(dz, k, Props.RunBarricade, 0, ArchPier.North);
                        if (wide < 4 && rng.Chance(0.7)) Add(rng.Range(0, deep - 1), 4, JumpOne(), 0, (ArchPier)rng.Range(0, 3));
                        break;
                    }
                    case 1:
                    {
                        // The ceiling come down by the wall: slabs hanging onto rubble, a heap you can jump beside them, the
                        // broken tiles strewn after
                        int tall = rng.Chance(0.5) ? 1 : 2;
                        ArchPier lean = rng.Chance(0.5) ? ArchPier.North : ArchPier.South;
                        for (int dz = 0; dz < 2; dz++)
                        {
                            for (int k = 0; k < tall; k++) Add(dz, k, Props.RunCollapse, 0, lean);
                            if (dz == 0 || rng.Chance(0.5)) Add(dz, tall, Props.RunCollapse, 1, lean);
                        }
                        break;
                    }
                    case 2:
                    {
                        // A whole line of things across the hall: jump it, or find the one gap
                        int gap = rng.Chance(0.6) ? rng.Range(0, 4) : -1;
                        for (int k = 0; k < 5; k++)
                        {
                            if (k == gap) continue;
                            double r = rng.NextDouble();
                            if (k < 4 && k + 1 != gap && r < 0.35)
                            {
                                bool tipped = rng.Chance(0.5);
                                Add(0, k, tipped ? Props.RunBarricade : Props.RunGurney, (byte)(tipped ? 2 : 0), ArchPier.East);
                                Add(0, k + 1, tipped ? Props.RunBarricade : Props.RunGurney, (byte)(tipped ? 3 : 1), ArchPier.East);
                                k++;
                            }
                            else if (k is 0 or 4 && r < 0.7) Add(0, k, rng.Chance(0.5) ? Props.RunChairs : Props.RunCrashCart, 0, In(k));
                            else Add(0, k, JumpOne(), 0, (ArchPier)rng.Range(0, 3));
                        }
                        break;
                    }
                    case 3:
                    {
                        // Thread the needle: one column left between a cabinet, barricades and another cabinet
                        int gap = rng.Range(1, 3);
                        for (int k = 0; k < 5; k++)
                        {
                            if (k == gap) continue;
                            if (k is 0 or 4 && rng.Chance(0.6)) Add(0, k, Props.RunBarricade, 1, In(k));
                            else Add(0, k, Props.RunBarricade, 0, ArchPier.North);
                        }
                        break;
                    }
                    case 4:
                    {
                        // A tall cabinet against the wall with its door hanging open, things beside it and across
                        Add(0, 0, Props.RunBarricade, 1, ArchPier.East);
                        Add(rng.Range(0, 1), rng.Range(1, 2), JumpOne(), 0, (ArchPier)rng.Range(0, 3));
                        if (rng.Chance(0.7)) Add(rng.Range(1, 2), 4, rng.Chance(0.5) ? Props.RunCrashCart : Props.RunChairs, 0, ArchPier.West);
                        break;
                    }
                    case 5:
                    {
                        // Gurneys left along the hall, staggered
                        int a = rng.Range(0, 4), b = (a + rng.Range(2, 3)) % 5;
                        Add(0, a, Props.RunGurney, 0, ArchPier.South);
                        Add(1, a, Props.RunGurney, 1, ArchPier.South);
                        Add(2, b, Props.RunGurney, 0, ArchPier.South);
                        Add(3, b, Props.RunGurney, 1, ArchPier.South);
                        break;
                    }
                    case 6:
                        // Shelving lying across the hall from the wall, its boxes spilled
                        Add(0, 0, Props.RunShelfFallen, 0, ArchPier.East);
                        Add(0, 1, Props.RunShelfFallen, 1, ArchPier.East);
                        if (rng.Chance(0.4)) Add(0, 3, Props.RunIvStand, 0, ArchPier.North);
                        break;
                    case 7:
                    {
                        // A gurney tipped on its side across the hall
                        int k = rng.Range(0, 3);
                        Add(0, k, Props.RunBarricade, 2, ArchPier.East);
                        Add(0, k + 1, Props.RunBarricade, 3, ArchPier.East);
                        if (rng.Chance(0.6)) Add(rng.Range(1, 2), k <= 1 ? 4 : 0, JumpOne(), 0, (ArchPier)rng.Range(0, 3));
                        break;
                    }
                    default:
                    {
                        // A feint: the way past a barricade opens along the wall, by a door, and ends at a cabinet; the
                        // way on is back across (or over the gurney)
                        int wall = side > 0 ? c - 3 : c + 3;
                        if (L.At(wall, z + 1).Kind != TileKind.Door && L.At(wall, z + 2).Kind != TileKind.Door) break;
                        Add(0, 2, Props.RunBarricade, 0, ArchPier.North);
                        Add(0, 3, Props.RunGurney, 0, ArchPier.East);
                        Add(0, 4, Props.RunGurney, 1, ArchPier.East);
                        Add(2, 0, Props.RunBarricade, 1, ArchPier.East);
                        Add(2, 1, Props.RunBarricade, 0, ArchPier.North);
                        break;
                    }
                }
                if (piece.Count == 0) continue;
                bool fits = true;
                len = 1;
                foreach (var e in piece)
                {
                    fits &= Free(z + e.Dz, Col(e.K));
                    len = Math.Max(len, e.Dz + 1);
                }
                if (!fits) continue;
                undo.Clear();
                foreach (var e in piece)
                {
                    int col = Col(e.K);
                    undo.Add((col, z + e.Dz, L.At(col, z + e.Dz)));
                    ref Tile t = ref L.At(col, z + e.Dz);
                    t.Variant = e.Prop;
                    t.Stack = e.Stack;
                    t.Pier = Mirror(e.Pier);
                }
                if (RunSprintable(L, c, z0, Math.Min(z1, z + len + 1))) placed = true;
                else
                    foreach (var (x, uz, t) in undo) L.At(x, uz) = t;
            }
            if (!placed)
            {
                z++;
                continue;
            }
            // Under a collapse the ceiling is broken, and its tiles lie in the rows after it (they trip a sprinter)
            if (piece[0].Prop == Props.RunCollapse)
                for (int n = rng.Range(1, 2); n > 0; n--) Small(z + len, Col(rng.Range(0, 3)), Props.RunDebris);
            int gapRows = third switch { 0 => rng.Range(2, 4), 1 => rng.Range(2, 4), _ => rng.Range(1, 3) };
            // Now and then, in the gap, something small that trips a sprinter (mostly in the dark last third), or sheets
            // (layout version 9: a little less often, now that what trips you is drawn as the heap it is)
            if (rng.Chance(Version >= 9 ? third switch { 0 => 0.2, 1 => 0.25, _ => 0.4 } : third switch { 0 => 0.25, 1 => 0.35, _ => 0.55 }))
            {
                int tz = z + len + 1 + rng.Range(0, Math.Max(0, gapRows - 2));
                double what = rng.NextDouble();
                if (third == 2 && what < 0.2)
                    for (int k = 0; k < 5; k++)
                    {
                        if (!Free(tz, c + k - 2)) continue;
                        L.At(c + k - 2, tz).Variant = Props.RunCord;
                        L.At(c + k - 2, tz).Pier = ArchPier.East;
                    }
                else Small(tz, c + rng.Range(-2, 2), third < 2 && what < 0.5 ? Props.RunSheets
                    : what < 0.6 ? Props.RunToyCar : what < 0.85 ? Props.RunBoxes : Props.RunDebris);
            }
            z += len + gapRows;
        }
    }

    /// <summary>
    /// The EXIT signs, the only light: one every 10 blocks or so down the centre line, with clusters and dark gaps (more
    /// of them, and darker, toward the end), always one at each corner and before the exit. (Layout version 9: one every
    /// 12 +- 2, no clusters, dark gaps only in the last third and at most 26 long.) The rest of the ceiling:
    /// acoustic tile, dead troffers, now and then an air vent.
    /// </summary>
    private void PlanRunSigns(RunLane L)
    {
        var rng = new Rng(Hashing.Hash(seed, L.Index, 5, SaltRunSigns));
        var forced = new HashSet<int> { 2, L.Middle, L.Last, L.ExitS - 2 };
        int last = Version >= 9 ? 0 : -100, next = 4;
        for (int s = 1; s < L.ExitS; s++)
        {
            var (x, z) = L.Line[s];
            ref Tile t = ref L.At(x, z);
            if (t.Kind != TileKind.Floor) continue;
            bool lastThird = L.Third(s) == 2;
            int seg = s / 32;
            double roll = Hashing.Unit(Hashing.Hash(seed, L.Index * 64 + seg, 6, SaltRunSigns));
            // Layout version 9: a steady run of signs (12 +- 2 apart, no clusters), dark gaps only in the last third and none over 26
            bool dark = Version >= 9 ? lastThird && roll < 0.25 : roll < (lastThird ? 0.35 : 0.15), cluster = Version < 9 && roll > 0.9;
            bool due = s >= next && !dark || forced.Contains(s) || s - last >= (Version >= 9 ? (lastThird ? 26 : 16) : lastThird ? 40 : 32);
            bool inSafe = t.Zone == RunZone.Safe;
            if (due && !inSafe)
            {
                t.Ceiling = CeilingKind.RunExitSign;
                // A sign on the crossways part of a dogleg faces along it, west and east
                bool crossways = s < L.ExitS && s > 0 && L.Line[s - 1].Z == z && L.Line[s + 1].Z == z;
                if (crossways) t.Detail |= RunSignWE;
                L.Signs.Add(s);
                last = s;
                next = s + (cluster ? 4 : Version >= 9 ? 12 + rng.Range(-2, 2) : 10 + rng.Range(-3, 3));
                continue;
            }
            if (inSafe) continue;
            if (s % 4 == 2) t.Ceiling = CeilingKind.RunPanelDead;
            else if (rng.Chance(0.06))
            {
                t.Ceiling = CeilingKind.RunVent;
                if (s > 30) L.Events.Add(new RunEvent(RunEventKind.Vent, x, z, s, ArchPier.North, ArchPier.North));
            }
        }
        foreach (int s in L.Signs)
            if (s > L.Middle && s < L.ExitS - 40)
            {
                var (x, z) = L.Line[s];
                L.Events.Add(new RunEvent(RunEventKind.Sign, x, z, s, ArchPier.North, ArchPier.North));
            }
        L.Events.Sort((a, b) => a.S.CompareTo(b.S));
    }

    private static readonly ArchPier[] RunTrimSides = { ArchPier.East, ArchPier.West, ArchPier.North, ArchPier.South },
        RunBorderSides = { ArchPier.East, ArchPier.West };

    /// <summary>The crash rail on every wall face along the hall, and the dark band in the vinyl beside it.</summary>
    private static void PlanRunTrim(RunLane L)
    {
        for (int z = 1; z < RunLane.Length - 1; z++)
            for (int x = 1; x < RunLane.Width - 1; x++)
            {
                ref Tile t = ref L.At(x, z);
                if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.RunWall)
                {
                    foreach (ArchPier dir in RunTrimSides)
                    {
                        Tile n = RunStep(L, x, z, dir);
                        if (n.Kind != TileKind.Floor || n.Zone is not (RunZone.Hall or RunZone.ExitStretch)) continue;
                        t.Pattern = WallPattern.RunWallRail;
                        t.Pier = dir;
                        break;
                    }
                }
                else if (t.Kind == TileKind.Floor && t.Floor == FloorKind.RunFloor && t.Zone is RunZone.Hall or RunZone.ExitStretch)
                {
                    foreach (ArchPier dir in RunBorderSides)
                    {
                        if (RunStep(L, x, z, dir).Kind == TileKind.Floor) continue;
                        t.Floor = FloorKind.RunBorder;
                        if (dir == ArchPier.East) t.Detail |= RunBorderEast;
                        break;
                    }
                }
            }
    }

    private static Tile RunStep(RunLane L, int x, int z, ArchPier dir)
    {
        var (dx, dz) = FacingStep(dir);
        return L.In(x + dx, z + dz) ? L.At(x + dx, z + dz) : default;
    }
}

/// <summary>
/// The chase in Level !, as a number (no game in it, so the harness can run it): the horde's front, a position along
/// the course, against a runner's. The front runs at a share of the runner's sprint (0.78, 0.82 in the last third, by
/// the Normal setting; it gathers speed over its first <see cref="WarmUp"/> seconds), keeps pace once it is more than
/// <see cref="Band"/> behind ("they are still near"), waits at the Safe Zone's door while the runner is inside, and
/// catches anyone it comes within <see cref="CatchGap"/> of.
///
/// (0.514.0, every world: the shares were 0.90 / 0.94, with no warm-up. That is fair only to a runner who keeps a
/// flat-floor sprint, and the hall since layout version 6 makes nobody do that: weaving and jumping through it, a good
/// runner keeps about 0.85-0.9 of a sprint, and was caught. Now a runner at 0.85 who bumps into things now and then
/// gets out; one who walks or stops is still caught.)
/// </summary>
public sealed class RunChase
{
    /// <summary>
    /// A player's sprint on flat ground, in blocks a second, by Vintage Story's physics: a sprint step of
    /// 1/60 × 1.5 (BaseMoveSpeed) × 2 (SprintSpeedMultiplier) = 0.05 a tick, built up against ground drag 0.7 and air drag
    /// 0.983^0.55 a tick to 2.26 times that, 60 ticks a second.
    /// </summary>
    public const double SprintSpeed = 0.05 * 0.69343 / (1 - 0.69343) * 60;

    /// <summary>How far behind the front keeps pace, out of sight; how close is caught.</summary>
    public const double Band = 40, CatchGap = 1.5;

    /// <summary>The front's share of a sprint: the first two thirds, the last third (Low, Normal, High).</summary>
    public static readonly double[] Share = { 0.73, 0.78, 0.84 }, LastShare = { 0.77, 0.82, 0.88 };

    /// <summary>
    /// The horde gathers speed after it bursts out: from <see cref="WarmUpShare"/> less than its share, up to it over
    /// this many seconds (the first stretch is where a runner learns the hall).
    /// </summary>
    public const double WarmUp = 20, WarmUpShare = 0.12;

    /// <summary>Seconds until the chained door bursts (Low, Normal, High); and after the runner crosses into the hall.</summary>
    public static readonly double[] BreakSeconds = { 15, 12, 9 };
    public const double BreakAfterLeaving = 4;

    public readonly double Sprint;
    public readonly int Difficulty;
    public readonly int LastThird, SafeFrom, SafeTo;
    /// <summary>The front's course position (it starts at the chained door) and whether it is loose yet.</summary>
    public double Front;
    public bool Loose;
    public double Elapsed;
    /// <summary>When the chained door burst (seconds since arrival).</summary>
    public double LooseAt = -1;
    /// <summary>When the runner first crossed the hallway door (seconds since arrival), or -1.</summary>
    public double LeftRoomAt = -1;
    /// <param name="sprint">The runner's sprint, in blocks a second.</param>
    /// <param name="difficulty">0 Low, 1 Normal, 2 High.</param>
    /// <param name="chainedDoor">The chained door's course position (negative).</param>
    public RunChase(double sprint, int difficulty, int lastThird, int safeFrom, int safeTo, int chainedDoor)
    {
        Sprint = sprint;
        Difficulty = Math.Clamp(difficulty, 0, 2);
        LastThird = lastThird;
        SafeFrom = safeFrom;
        SafeTo = safeTo;
        Front = chainedDoor;
    }

    /// <summary>After three hours in the Safe Zone, the horde comes in anyway (the caller counts the hours).</summary>
    public bool SafeBreached;

    public bool InSafe(double runner) => !SafeBreached && SafeFrom >= 0 && runner >= SafeFrom && runner <= SafeTo;

    /// <summary>
    /// Moves the chase on by <paramref name="dt"/> seconds with the runner at course position <paramref name="runner"/>.
    /// Returns true if the runner is caught.
    /// </summary>
    public bool Step(double dt, double runner)
    {
        Elapsed += dt;
        if (LeftRoomAt < 0 && runner > 0) LeftRoomAt = Elapsed;
        if (!Loose)
        {
            Loose = Elapsed >= BreakSeconds[Difficulty] || LeftRoomAt >= 0 && Elapsed - LeftRoomAt >= BreakAfterLeaving;
            if (Loose) LooseAt = Elapsed;
            return false;
        }
        if (InSafe(runner))
        {
            // It waits at the Safe Zone's door; after three hours in there it comes in anyway (RunSystem counts those, in game hours, and sets SafeBreached)
            Front = Math.Min(Front + Sprint * dt, SafeFrom - 2);
            return false;
        }
        double share = Front >= LastThird ? LastShare[Difficulty] : Share[Difficulty];
        double since = Elapsed - LooseAt;
        if (since < WarmUp) share -= WarmUpShare * (1 - since / WarmUp);
        double gap = runner - Front;
        if (gap > Band) share = Math.Max(share, 1.0);
        // Once past the Safe Zone it comes on from its door, not from wherever it was waiting
        Front += share * Sprint * dt;
        return runner - Front <= CatchGap;
    }

    /// <summary>The gap between the runner and the front.</summary>
    public double Gap(double runner) => runner - Front;
}
