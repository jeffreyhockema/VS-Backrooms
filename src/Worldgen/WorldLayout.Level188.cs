using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 188, "The Courtyard of Windows": kept as level 20 (<see cref="Level188"/>) and shown as "188". One building, the
/// same for everyone in the world, far out to the north-north-east between Motion and Level Fun: a dark courtyard of four
/// mossy lawns and a round wooden deck, walled in by a five-storey budget hotel with 32 small square windows a storey onto
/// it, under a black sky. The design is in docs/design/new-levels/188-plan.md (after the original Wikidot page by 1000dumplings,
/// Fandom's "The Windows", Miraheze and Escape the Backrooms).
///
/// <para><b>The building</b> is 88 by 58 blocks (building-local X east, Z south, from <see cref="L188BuildX0"/>,
/// <see cref="L188BuildZ0"/>) and fills three cells by two in the middle of a round region four cells in radius; every other block
/// of the region is solid nothing. From the courtyard (X 17-70, Z 17-40) outward each wing is 17 deep: the courtyard
/// façade (depth 0), the inner rooms (1-5), the inner corridor wall (6), the corridor that rings the building (7-9), the
/// outer corridor wall (10), the outer rooms (11-15) and the outer façade (16), which looks onto nothing. Rooms come in
/// modules of five along their wing: a partition and four blocks of room. <see cref="L188CellAt"/> says what any
/// building-local position is; it is pure arithmetic, so the generator asks it for every block.</para>
///
/// <para><b>Storeys.</b> Five, four blocks each: storey s's floor slab at rel 4s, its air at 4s+1 to 4s+3, the roof slab at
/// rel 20, the parapet at 21, the black sky at <see cref="L188SkyRel"/>. Every storey has the ground storey's plan but for
/// the lobby, the courtyard door and the windows that show other places (ground only) and the fire doors (one per upper
/// storey); the layout's tiles are the ground storey's, which is enough, since every arrival is on the ground.</para>
///
/// <para><b>Tiles</b> (the ground storey's): <see cref="Tile.Zone"/> the <see cref="L188Part"/>; a courtyard window that
/// shows another place has <see cref="Unders.L188LinkWindow"/> and the level it leads to in <see cref="Tile.Detail"/>;
/// the hatch's tiles <see cref="Unders.L188Hatch"/>; a fire door's wall tile <see cref="Unders.L188FireDoor"/> with its
/// storey in Detail; <see cref="Tile.Pier"/> the way a wall or window faces (toward the courtyard, or the corridor).</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2000-0x20BF are this level's (0x20C0-0x20FF its thresholds').</summary>
    private const ulong SaltL188Shape = 0x2001, SaltL188Link = 0x2002, SaltL188Furnish = 0x2003, SaltL188Window = 0x2004,
        SaltL188Prey = 0x2005, SaltL188Lock = 0x2006, SaltL188Blind = 0x2007;
    /// <summary>Salts of the windows into 188 in other levels (each its own, so nothing else there shifts).</summary>
    private const ulong SaltL188EntranceL0 = 0x2010, SaltL188EntranceL1 = 0x2011;

    /// <summary>Whether Level 188's windows in other levels are laid out (always, but for the harness's check that nothing else moved).</summary>
    internal static bool L188Entrances = Environment.GetEnvironmentVariable("BACKROOMS_NO_188_ENTRANCES") != "1";

    /// <summary>The building's size (X by Z), its storeys, the roof slab, and the black sky over it all.</summary>
    public const int L188W = 88, L188D = 58, L188Storeys = 5, L188RoofRel = 20, L188SkyRel = 33;

    /// <summary>The courtyard windows: 11 on each long side, 5 on each short one (the west side's first is the stair's).</summary>
    public const int L188Windows = 32, L188StairWindow = 27;

    /// <summary>The fire doors (building-local wall tiles, one per upper storey, storeys 1-4, at the corridor's bends).</summary>
    public static readonly (int Bx, int Bz, int Storey)[] L188FireDoors = { (6, 8, 1), (81, 8, 2), (81, 49, 3), (6, 49, 4) };

    /// <summary>What a building-local position is (kept in <see cref="Tile.Zone"/>).</summary>
    public enum L188Part : byte
    {
        Void, Court, Facade, Room, Partition, WallIn, Corridor, WallOut, OuterRoom, OuterFacade, Stair, Lifts, Housekeeping, Linen, Suite, Lobby,
    }

    /// <summary>What a building-local position is, and where in its wing and room.</summary>
    public readonly struct L188Cell
    {
        public readonly L188Part Part;
        /// <summary>The side of the courtyard it lies on: 0 north, 1 east, 2 south, 3 west.</summary>
        public readonly byte Wing;
        /// <summary>Depth from the courtyard (0 the façade, 16 the outer façade).</summary>
        public readonly byte D;
        /// <summary>The coordinate along its wing (X for the north and south wings, Z for the others).</summary>
        public readonly int A;
        /// <summary>Its room along the wing, and its place in that room (U along, V from the window), or -1.</summary>
        public readonly int K, U, V;

        public L188Cell(L188Part part, int wing, int d, int a, int k = -1, int u = -1, int v = -1)
        {
            Part = part; Wing = (byte)wing; D = (byte)Math.Max(0, d); A = a; K = k; U = u; V = v;
        }
    }

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees east of north.</summary>
    private double L188Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L188CentreX => spawnMacroX + (int)Math.Round(L188Reach * Math.Sin(Math.PI / 8));
    private int L188CentreZ => spawnMacroZ - (int)Math.Round(L188Reach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells: four, whatever the world's size. It holds one building of meagre size.</summary>
    private int L188Radius => 4;

    /// <summary>The building's north-west corner, in block coordinates: in the three cells by two round the centre, with a margin.</summary>
    public int L188BuildX0 => (L188CentreX - 1) * MacroSize + 4;
    public int L188BuildZ0 => (L188CentreZ - 1) * MacroSize + 3;

    private bool InL188(double mx, double mz) => InRoundRegion(mx, mz, L188CentreX, L188CentreZ, L188Radius, SaltL188Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash: always on the building.</summary>
    private (int Mx, int Mz) L188ArrivalCell(ulong h) => RoundArrivalCell(h, L188CentreX, L188CentreZ, L188Radius);

    /// <summary>Arriving: on the courtyard's paving (by default; thresholds ask for the paving beside their window).</summary>
    private static bool IsL188ArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone == (byte)L188Part.Court && t.Floor == FloorKind.L188Paver;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L188ArrivalHeight(in Tile t, double stand) => stand;

    // ================= The building, as arithmetic =================

    private static int Mod5(int a) => ((a % 5) + 5) % 5;

    /// <summary>The way a wing faces the courtyard (its façade's front): north wing south, east wing west, and so on.</summary>
    public static ArchPier L188Toward(int wing) => wing switch { 0 => ArchPier.South, 1 => ArchPier.West, 2 => ArchPier.North, _ => ArchPier.East };

    /// <summary>A building-local position from a wing, a coordinate along it and a depth from the courtyard.</summary>
    public static (int Bx, int Bz) L188At(int wing, int a, int d) => wing switch
    {
        0 => (a, 16 - d),
        2 => (a, 41 + d),
        3 => (16 - d, a),
        _ => (71 + d, a),
    };

    /// <summary>A place in a room (inner or outer) of a wing: U along the wing, V from the window toward the door.</summary>
    public static (int Bx, int Bz) L188RoomTile(int wing, int k, bool outer, int u, int v) =>
        L188At(wing, (outer ? 7 : 17) + 5 * k + u, outer ? 15 - v : v + 1);

    /// <summary>What a building-local position is.</summary>
    public static L188Cell L188CellAt(int bx, int bz)
    {
        if (bx < 0 || bz < 0 || bx >= L188W || bz >= L188D) return new L188Cell(L188Part.Void, 0, 0, 0);
        int dx = bx <= 16 ? 16 - bx : bx >= 71 ? bx - 71 : -1;
        int dz = bz <= 16 ? 16 - bz : bz >= 41 ? bz - 41 : -1;
        int d = Math.Max(dx, dz);
        if (d < 0) return new L188Cell(L188Part.Court, 0, 0, 0);
        int wing = dz >= dx ? (bz <= 16 ? 0 : 2) : (bx >= 71 ? 1 : 3);
        int a = wing is 0 or 2 ? bx : bz;
        // The stair hall: the north-west corner and the first room slot of the west wing
        if (bx >= 11 && bx <= 15 && bz >= 11 && bz <= 20) return new L188Cell(L188Part.Stair, 3, d, bz);
        if (d == 0) return new L188Cell(L188Part.Facade, wing, 0, a, -1, Mod5(a - 17));
        if (d <= 5)
        {
            if (dx >= 1 && dz >= 1)
            {
                L188Part corner = bx >= 71 ? (bz <= 16 ? L188Part.Lifts : L188Part.Housekeeping) : L188Part.Linen;
                return new L188Cell(corner, wing, d, a);
            }
            int u = Mod5(a - 17);
            if (u == 4) return new L188Cell(L188Part.Partition, wing, d, a, -1, 4);
            return new L188Cell(L188Part.Room, wing, d, a, (a - 17) / 5, u, d - 1);
        }
        if (d == 6) return new L188Cell(L188Part.WallIn, wing, 6, a, -1, Mod5(a - 17));
        if (d <= 9) return new L188Cell(L188Part.Corridor, wing, d, a);
        int uo = Mod5(a - 7);
        if (d == 10) return new L188Cell(L188Part.WallOut, wing, 10, a, -1, uo);
        if (d <= 15)
        {
            // The corner suites: an outer corner square run together with the long wing's end room
            if (dx >= 11 && dz >= 11) return new L188Cell(L188Part.Suite, wing, d, a, -1, -1, 15 - d);
            if (wing is 0 or 2 && (a <= 10 || a >= 77))
                return new L188Cell(L188Part.Suite, wing, d, a, a <= 10 ? 0 : 14, a is >= 7 and <= 10 or >= 77 and <= 80 ? uo : -1, 15 - d);
            if (uo == 4) return new L188Cell(L188Part.Partition, wing, d, a, -1, 4);
            return new L188Cell(L188Part.OuterRoom, wing, d, a, (a - 7) / 5, uo, 15 - d);
        }
        return new L188Cell(L188Part.OuterFacade, wing, 16, a, -1, uo);
    }

    /// <summary>Whether a building-local position is the lobby on the ground storey (the south wing's outer rooms, run together).</summary>
    public static bool L188IsLobby(int bx, int bz) => bz >= 52 && bz <= 56 && bx >= 12 && bx <= 75;

    /// <summary>The ground storey's openings from the south corridor into the lobby.</summary>
    public static bool L188IsLobbyOpening(int bx, int bz) => bz == 51 && (bx is >= 22 and <= 24 or >= 63 and <= 65);

    /// <summary>The lobby's glass front doors (they open onto nothing): building-local, on the south outer façade.</summary>
    public static bool L188IsFrontDoor(int bx, int bz) => bz == 57 && bx is 43 or 44;

    /// <summary>The openings into the three service corners from the corridor (the lifts, housekeeping, the linen store).</summary>
    public static bool L188IsServiceOpening(int bx, int bz) =>
        bx == 77 && (bz is >= 12 and <= 14 or >= 43 and <= 45) || bx == 10 && bz is >= 43 and <= 45;

    /// <summary>The stair hall's doors into the west corridor (beside the north and the south landing).</summary>
    public static bool L188IsStairDoor(int bx, int bz) => bx == 10 && bz is 11 or 18;

    /// <summary>The fire door's storey at a building-local wall tile, or 0 if there is none.</summary>
    public static int L188FireDoorAt(int bx, int bz)
    {
        foreach (var (x, z, s) in L188FireDoors) if (x == bx && z == bz) return s;
        return 0;
    }

    /// <summary>Whether a wall tile at depth 6 or 10 holds a room's door (the room's U = 3 column).</summary>
    public static bool L188IsRoomDoor(in L188Cell c)
    {
        if (c.Part == L188Part.WallIn)
        {
            if (c.U != 3) return false;
            // A room behind it: along the courtyard, never the stair's slot
            return c.Wing is 0 or 2 ? c.A is >= 17 and <= 70 : c.A is >= 22 and <= 40 || c.Wing == 1 && c.A is >= 17 and <= 20;
        }
        if (c.Part == L188Part.WallOut)
            return c.U == 3 && (c.Wing is 0 or 2 ? c.A is >= 10 and <= 80 : c.A is >= 10 and <= 50);
        return false;
    }

    // ================= The courtyard's ground =================

    /// <summary>The middle of the courtyard (a grid point, between four tiles), building-local.</summary>
    private const double L188CentreBx = 44, L188CentreBz = 29;

    /// <summary>Whether a courtyard tile is the wooden deck (a circle eight across round the middle).</summary>
    public static bool L188IsDeck(int bx, int bz)
    {
        double dx = bx + 0.5 - L188CentreBx, dz = bz + 0.5 - L188CentreBz;
        return dx * dx + dz * dz <= 16;
    }

    /// <summary>Whether a courtyard tile is the hatch in the middle of the deck.</summary>
    public static bool L188IsHatch(int bx, int bz) => bx is 43 or 44 && bz is 28 or 29;

    /// <summary>Whether a courtyard tile is lawn (the four quadrants, the paths between and round them paved).</summary>
    public static bool L188IsLawn(int bx, int bz) =>
        (bx is >= 19 and <= 41 or >= 46 and <= 68) && (bz is >= 19 and <= 26 or >= 31 and <= 38) && !L188IsDeck(bx, bz);

    /// <summary>The downpipe on the north façade (the courtyard tile against it), always running.</summary>
    public const int L188PipeBx = 55, L188PipeBz = 17;

    /// <summary>A courtyard prop at a tile: benches facing the deck, the bollard lamps at its diagonals, the drain, tufts of moss.</summary>
    private ushort L188CourtProp(int bx, int bz, out ArchPier facing)
    {
        facing = ArchPier.North;
        if (bx == 38 && bz == 29) { facing = ArchPier.East; return Props.L188Bench; }
        if (bx == 49 && bz == 29) { facing = ArchPier.West; return Props.L188Bench; }
        if (bx is 39 or 48 && bz is 24 or 33) return Props.L188Bollard;
        if (bx == L188PipeBx && bz == L188PipeBz) return Props.L188Drain;
        if (L188IsLawn(bx, bz) && Hashing.Unit(Hashing.Hash(seed, bx, bz, SaltL188Furnish + 1)) < 0.15) return Props.L188MossTuft;
        return 0;
    }

    // ================= The windows =================

    /// <summary>A courtyard window's wing and its room along the wing, from its number (north 0-10, east 11-15, south 16-26, west 27-31).</summary>
    public static (int Wing, int K) L188WindowWingK(int wi) => wi switch
    {
        < 11 => (0, wi),
        < 16 => (1, wi - 11),
        < 27 => (2, wi - 16),
        _ => (3, wi - 27),
    };

    /// <summary>The courtyard window of a wing's room.</summary>
    public static int L188WindowIndex(int wing, int k) => wing switch { 0 => k, 1 => 11 + k, 2 => 16 + k, _ => 27 + k };

    /// <summary>Whether a window's part at U (1 or 2) is its left half, as seen by someone in front of a face looking the other way.</summary>
    public static bool L188IsLeft(int u, ArchPier facing) => (u == 1) == (facing is ArchPier.South or ArchPier.West);

    /// <summary>A courtyard window's two façade tiles (building-local): its left and right halves as seen from the courtyard.</summary>
    public static ((int Bx, int Bz) Left, (int Bx, int Bz) Right, ArchPier Facing) L188WindowTiles(int wi)
    {
        var (wing, k) = L188WindowWingK(wi);
        ArchPier facing = L188Toward(wing);
        var one = L188At(wing, 17 + 5 * k + 1, 0);
        var two = L188At(wing, 17 + 5 * k + 2, 0);
        return L188IsLeft(1, facing) ? (one, two, facing) : (two, one, facing);
    }

    /// <summary>The courtyard window at a building-local façade tile, or -1.</summary>
    public static int L188WindowAt(int bx, int bz)
    {
        L188Cell c = L188CellAt(bx, bz);
        if (c.Part != L188Part.Facade || c.U is not (1 or 2)) return -1;
        int k = (c.A - 17) / 5;
        int max = c.Wing is 0 or 2 ? 10 : 4;
        if (c.A < 17 || k > max) return -1;
        return L188WindowIndex(c.Wing, k);
    }

    private int[] l188Links;

    /// <summary>
    /// Where each courtyard window on the ground storey leads, if it shows another place: twelve of the 31 (the Hub's on the
    /// north side, Level Fun's confetti window on the east; three to the Lobby, two to the Habitable Zone, one each to
    /// Levels 2, 4, 5, 6 and 9), fixed for the world. -1 for an ordinary window.
    /// </summary>
    public int L188LinkLevel(int wi)
    {
        if (l188Links == null)
        {
            var links = new int[L188Windows];
            Array.Fill(links, -1);
            var rng = new Rng(Hashing.Hash(seed, 188, 0, SaltL188Link));
            links[rng.Range(0, 10)] = Hub;
            links[11 + rng.Range(0, 4)] = FunLevel;
            foreach (int level in new[] { 0, 0, 0, 1, 1, 2, 4, 5, 6, 9 })
            {
                int wi2;
                do wi2 = rng.Range(0, L188Windows - 1); while (wi2 == L188StairWindow || links[wi2] != -1);
                links[wi2] = level;
            }
            l188Links = links;
        }
        return wi >= 0 && wi < L188Windows ? l188Links[wi] : -1;
    }

    /// <summary>The state a courtyard window can be in (blocks <c>l188-window-*</c>).</summary>
    public enum L188WindowState : byte { Closed, Glow, Open, Lit, Figure, Beckon, Scene, Stair }

    /// <summary>
    /// An ordinary window's state of its own, which changes every day or so, at its own hours: blind down (most), down and
    /// glowing, up on a dark room, or up on a lit one.
    /// </summary>
    public L188WindowState L188BaseState(int wi, int storey, double totalHours)
    {
        ulong h = Hashing.Hash(seed, wi, storey, SaltL188Window);
        double period = 14 + 26 * Hashing.Unit(h), phase = Hashing.Unit(Hashing.Mix(h)) * period;
        long epoch = (long)Math.Floor((totalHours + phase) / period);
        double u = Hashing.Unit(Hashing.Hash(seed, wi * 8 + storey, (int)epoch, SaltL188Window + 1));
        return u < 0.55 ? L188WindowState.Closed : u < 0.80 ? L188WindowState.Glow : u < 0.92 ? L188WindowState.Open : L188WindowState.Lit;
    }

    /// <summary>Whether a window is a predatory one (Entity 2) on a given in-game day: about one room in sixteen, moving every night.</summary>
    public bool L188IsPrey(int wi, int storey, long day)
    {
        if (wi == L188StairWindow || storey == 0 && L188LinkLevel(wi) >= 0) return false;
        return Hashing.Unit(Hashing.Hash(seed, wi * 8 + storey, (int)day, SaltL188Prey)) < 1 / 16.0;
    }

    /// <summary>A courtyard window's state at an hour, as the world makes it (a blind someone opened is the system's to say).</summary>
    public L188WindowState L188StateAt(int wi, int storey, double totalHours, long day)
    {
        if (wi == L188StairWindow) return L188WindowState.Stair;
        if (storey == 0 && L188LinkLevel(wi) >= 0) return L188WindowState.Scene;
        if (L188IsPrey(wi, storey, day)) return L188WindowState.Figure;
        return L188BaseState(wi, storey, totalHours);
    }

    /// <summary>Whether a room's door is plainly locked (the housekeeping card opens it): about one room in twenty.</summary>
    public bool L188IsLocked(int wing, int k, bool outer, int storey) =>
        Hashing.Unit(Hashing.Hash(seed, wing * 64 + k * 2 + (outer ? 1 : 0), storey, SaltL188Lock)) < 0.05;

    private static readonly (int Level, double Weight)[] L188BlindTable =
    {
        (0, .16), (1, .10), (2, .08), (3, .07), (4, .10), (5, .10), (6, .05), (7, .04), (8, .04), (9, .08), (10, .04), (11, .04),
        (Poolrooms, .04), (Motion, .02), (TheEnd, .02), (FunLevel, .02),
    };

    /// <summary>The level whoever opens a closed window's blind is taken to: fixed for each window, weighted toward the main levels.</summary>
    public int L188BlindTarget(int wi, int storey)
    {
        double u = Hashing.Unit(Hashing.Hash(seed, wi * 8 + storey, 0, SaltL188Blind));
        foreach (var (level, weight) in L188BlindTable)
        {
            if (u < weight) return level;
            u -= weight;
        }
        return 0;
    }

    /// <summary>What a window that leads to a level shows (the name in <c>l188-window-scene-*</c>).</summary>
    public static string L188SceneOf(int level) => level switch
    {
        0 => "l0", 1 => "l1", 2 or 3 => "l2", 4 => "l4", 5 => "l5", 6 => "l6", 9 or 11 => "l9", 10 or Motion => "l94",
        Poolrooms => "l37", Hub => "hub", FunLevel => "fun", TheEnd => "end", _ => "void",
    };

    // ================= The ground storey's tiles =================

    private Tile[] l188Plan;

    /// <summary>The ground storey's tiles for the whole building, worked out once.</summary>
    private Tile[] L188Plan => l188Plan ??= PlanL188();

    /// <summary>The tile of the level at a block position (solid nothing outside the building).</summary>
    private Tile L188PlanTile(int gx, int gz)
    {
        int bx = gx - L188BuildX0, bz = gz - L188BuildZ0;
        if (bx < 0 || bz < 0 || bx >= L188W || bz >= L188D) return L188Void;
        return L188Plan[bz * L188W + bx];
    }

    private static readonly Tile L188Void = new() { Kind = TileKind.Wall, Pattern = WallPattern.L188Nothing, Tall = true };

    private Tile[] PlanL188()
    {
        var tiles = new Tile[L188W * L188D];
        for (int bz = 0; bz < L188D; bz++)
            for (int bx = 0; bx < L188W; bx++)
                tiles[bz * L188W + bx] = L188GroundTile(bx, bz);
        // Whatever the courtyard's door does not lead to (rooms behind sealed and locked doors) is sealed. The cells'
        // own pass cannot see it where a room straddles a cell line, so the building does it once, whole
        var reached = new bool[tiles.Length];
        var queue = new Queue<int>();
        int start = 20 * L188W + 20;
        reached[start] = true;
        queue.Enqueue(start);
        while (queue.Count > 0)
        {
            int i = queue.Dequeue();
            int x = i % L188W, z = i / L188W;
            foreach (var (dx, dz) in Steps)
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= L188W || nz >= L188D) continue;
                int n = nz * L188W + nx;
                if (reached[n] || !IsWalkable(tiles[n])) continue;
                reached[n] = true;
                queue.Enqueue(n);
            }
        }
        for (int i = 0; i < tiles.Length; i++)
            if (!reached[i] && tiles[i].Kind == TileKind.Floor) tiles[i].Sealed = true;
        return tiles;
    }

    private static Tile L188Wall(WallPattern pattern, ArchPier facing, byte zone) =>
        new() { Kind = TileKind.Wall, Pattern = pattern, Pier = facing, Zone = zone, Tall = true };

    /// <summary>The ground storey's tile at a building-local position.</summary>
    private Tile L188GroundTile(int bx, int bz)
    {
        L188Cell c = L188CellAt(bx, bz);
        byte zone = (byte)c.Part;
        ArchPier toward = L188Toward(c.Wing);
        ArchPier away = Opposite(toward);
        switch (c.Part)
        {
            case L188Part.Void:
                return L188Void;
            case L188Part.Court:
            {
                var t = new Tile { Kind = TileKind.Floor, Zone = zone };
                t.Floor = L188IsDeck(bx, bz) ? FloorKind.L188Deck : L188IsLawn(bx, bz) ? FloorKind.L188Turf : FloorKind.L188Paver;
                if (L188IsHatch(bx, bz)) t.Under = Unders.L188Hatch;
                else
                {
                    t.Variant = L188CourtProp(bx, bz, out ArchPier facing);
                    t.Pier = facing;
                }
                return t;
            }
            case L188Part.Facade:
            {
                int wi = L188WindowAt(bx, bz);
                // The courtyard's one door, on the ground storey, where the stair's window is above
                if (wi == L188StairWindow) return new Tile { Kind = TileKind.Doorway, Floor = FloorKind.L188Stair, Pier = ArchPier.East, Zone = zone };
                Tile wall = L188Wall(WallPattern.L188Facade, toward, zone);
                if (wi >= 0)
                {
                    wall.Stack = (byte)(L188IsLeft(c.U, toward) ? 1 : 0);
                    int link = L188LinkLevel(wi);
                    if (link >= 0)
                    {
                        wall.Under = Unders.L188LinkWindow;
                        wall.Detail = (byte)link;
                    }
                }
                return wall;
            }
            case L188Part.Room:
            case L188Part.OuterRoom:
            case L188Part.Suite:
                if (L188IsLobby(bx, bz)) return new Tile { Kind = TileKind.Floor, Floor = FloorKind.L188Lobby, Zone = (byte)L188Part.Lobby };
                return new Tile { Kind = TileKind.Floor, Floor = FloorKind.L188Room, Zone = zone };
            case L188Part.Partition:
                if (L188IsLobby(bx, bz)) return new Tile { Kind = TileKind.Floor, Floor = FloorKind.L188Lobby, Zone = (byte)L188Part.Lobby };
                return L188Wall(WallPattern.L188Partition, toward, zone);
            case L188Part.WallIn:
            case L188Part.WallOut:
            {
                ArchPier corridorSide = c.Part == L188Part.WallIn ? away : toward;
                if (L188IsStairDoor(bx, bz) || L188IsServiceOpening(bx, bz) || L188IsLobbyOpening(bx, bz))
                    return new Tile { Kind = TileKind.Doorway, Floor = FloorKind.L188Corridor, Pier = corridorSide, Zone = zone };
                int fire = L188FireDoorAt(bx, bz);
                if (fire > 0)
                {
                    Tile door = L188Wall(WallPattern.L188CorridorWall, corridorSide, zone);
                    door.Under = Unders.L188FireDoor;
                    door.Detail = (byte)fire;
                    return door;
                }
                // The ground storey's room doors: the lobby has none; a room behind a window onto elsewhere is sealed
                if (L188IsRoomDoor(c) && !(c.Part == L188Part.WallOut && c.Wing == 2 && c.A is >= 12 and <= 75))
                {
                    bool outer = c.Part == L188Part.WallOut;
                    int k = outer ? (c.Wing is 0 or 2 && c.A >= 77 ? 14 : (c.A - 7) / 5) : (c.A - 17) / 5;
                    if (!outer && L188LinkLevel(L188WindowIndex(c.Wing, k)) >= 0)
                        return new Tile { Kind = TileKind.Door, Pattern = WallPattern.L188SealedDoor, Pier = corridorSide, Zone = zone, Tall = true };
                    if (L188IsLocked(c.Wing, k, outer, 0))
                        return new Tile { Kind = TileKind.Door, Pattern = WallPattern.L188LockedDoor, Pier = corridorSide, Zone = zone, Tall = true };
                    return new Tile { Kind = TileKind.Doorway, Floor = FloorKind.L188Room, Pier = corridorSide, Zone = zone };
                }
                return L188Wall(WallPattern.L188CorridorWall, corridorSide, zone);
            }
            case L188Part.Corridor:
                return new Tile { Kind = TileKind.Floor, Floor = FloorKind.L188Corridor, Zone = zone };
            case L188Part.OuterFacade:
                if (L188IsFrontDoor(bx, bz)) return new Tile { Kind = TileKind.Door, Pattern = WallPattern.L188FrontDoor, Pier = ArchPier.North, Zone = zone, Tall = true };
                return L188Wall(WallPattern.L188OuterWall, toward, zone);
            case L188Part.Stair:
            {
                // The core between the flights; the flights themselves; the landings
                if (bx == 13 && bz is >= 13 and <= 16) return L188Wall(WallPattern.L188StairWall, ArchPier.East, zone);
                var t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.L188Stair, Zone = zone };
                if (bz is >= 13 and <= 16) t.Stair = 1;
                return t;
            }
            default:
                return new Tile { Kind = TileKind.Floor, Floor = FloorKind.L188Corridor, Zone = zone };
        }
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: the building's own plan, copied onto it.</summary>
    private Edge L188Edge(int mx, int mz, bool west)
    {
        var edge = new Edge { Pattern = WallPattern.L188Nothing, Base = BaseStyle.Plain, Tall = true };
        for (int i = 1; i < MacroSize; i++)
        {
            int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
            Tile t = L188PlanTile(gx, gz);
            edge.Tiles[i] = t.Kind is TileKind.Floor or TileKind.Water ? EdgeTile.Open
                : t.Kind is TileKind.Doorway or TileKind.ArchDoor ? EdgeTile.Doorway : EdgeTile.Wall;
        }
        return edge;
    }

    /// <summary>Lays out one of the level's cells: its share of the building, or solid nothing.</summary>
    private void BuildLevel188(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
                b.At(lx, lz) = L188PlanTile(mx * MacroSize + lx, mz * MacroSize + lz);
    }

    /// <summary>Which of the level's props (<see cref="Props.L188First"/>-<see cref="Props.L188Last"/>) people walk through.</summary>
    private static bool L188WalkThrough(ushort variant) => variant is Props.L188MossTuft or Props.L188Drain;

    // ================= Air =================

    /// <summary>What part of the building a block position is, and its height above the level's floor.</summary>
    public L188Cell L188CellAtWorld(int x, int z) => L188CellAt(x - L188BuildX0, z - L188BuildZ0);

    /// <summary>
    /// The temperature: the courtyard is cold under its black sky (8 °C), the roof colder, the hatch's shaft colder still;
    /// the stair is unheated; the hotel itself is kept warm.
    /// </summary>
    private float L188Temperature(int x, int y, int z, int floorY)
    {
        int rel = y - (floorY - WorldGeometry.L188Drop);
        L188Cell c = L188CellAtWorld(x, z);
        if (rel < 0) return 4f;
        if (rel > L188RoofRel) return 6f;
        return c.Part switch
        {
            L188Part.Court or L188Part.Void => 8f,
            L188Part.Stair => 15f,
            _ => 21f,
        };
    }

    /// <summary>
    /// Reality stability: watched from every side in the courtyard and on the roof; plain in the corridors; a little rest in
    /// the rooms. (Standing near a predatory window drains it more: Regions.L188System sees to that.)
    /// </summary>
    private float L188Stability(double x, double y, double z, int floorY, float drift)
    {
        int rel = (int)Math.Floor(y) - (floorY - WorldGeometry.L188Drop);
        L188Cell c = L188CellAtWorld((int)Math.Floor(x), (int)Math.Floor(z));
        if (rel > L188RoofRel) return 0.8f;
        return c.Part switch
        {
            L188Part.Court or L188Part.Void => 0.85f,
            L188Part.Room or L188Part.OuterRoom or L188Part.Suite => 1.05f,
            _ => 0.95f + 0.03f * drift,
        };
    }

    // ================= Windows into 188 from other levels =================

    /// <summary>
    /// Level 0: about one Lobby cell in three hundred, in its outer three fifths, has a window where no window should be
    /// (never in a party cell, a Red Room or the Manila Room).
    /// </summary>
    public bool IsL188WindowCellL0(int mx, int mz)
    {
        if (!L188Entrances || Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL188EntranceL0)) >= 1 / 300.0) return false;
        if (IsSpawnMacro(mx, mz)) return false;
        double angle = Math.Atan2(mz - spawnMacroZ, mx - spawnMacroX);
        if (RingDistance(mx, mz) < 0.4 * OuterEdge(0, angle)) return false;
        return !IsFunPartyCell(mx, mz) && !IsRedRoom(mx, mz) && !IsManilaMacro(mx, mz);
    }

    /// <summary>Level 1: about one car-park cell in two hundred and fifty has one, in bare concrete.</summary>
    public bool IsL188WindowCellL1(int mx, int mz) =>
        L188Entrances && Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL188EntranceL1)) < 1 / 250.0;

    /// <summary>Whether a tile is one of the windows into 188 in another level, from the given host (0, 1, 3 Fun; -1 any).</summary>
    public static bool IsL188Entrance(Tile t, int host = -1) => t.Under == Unders.L188Entrance && (host < 0 || (t.Detail & 15) == host);

    /// <summary>
    /// Puts a window into 188 in a straight wall of a cell: two wall tiles side by side, walls on with them at both ends,
    /// open floor in front of both (the room the window looks out of). Nothing else in the cell changes.
    /// </summary>
    private void MarkL188Window(Builder b, int mx, int mz, int host)
    {
        var rng = new Rng(Hashing.Hash(seed, mx, mz, (host == 0 ? SaltL188EntranceL0 : SaltL188EntranceL1) + 0x40));
        bool Wall(int x, int z) => x >= 0 && z >= 0 && x < MacroSize && z < MacroSize && b.At(x, z).Kind == TileKind.Wall
            && !b.At(x, z).Tall && b.At(x, z).Under == 0 && b.At(x, z).Variant == 0;
        bool Open(int x, int z) => x >= 1 && z >= 1 && x < MacroSize - 1 && z < MacroSize - 1 && b.At(x, z).Kind == TileKind.Floor
            && b.At(x, z).Variant == 0 && !b.At(x, z).SupplyBox && !b.At(x, z).Sealed && b.At(x, z).Stair == 0 && b.At(x, z).Under == 0;
        var found = new List<(int X, int Z, int Ax, int Az, ArchPier Facing)>();
        for (int z = 1; z < MacroSize - 1; z++)
            for (int x = 1; x < MacroSize - 1; x++)
                foreach (var (ax, az) in new[] { (1, 0), (0, 1) })
                {
                    // Two wall tiles along (ax, az), the wall going on past both ends
                    if (!Wall(x, z) || !Wall(x + ax, z + az) || !Wall(x - ax, z - az) || !Wall(x + 2 * ax, z + 2 * az)) continue;
                    foreach (int side in new[] { 1, -1 })
                    {
                        int fx = az * side, fz = ax * side; // the room side, across the wall
                        if (!Open(x + fx, z + fz) || !Open(x + ax + fx, z + az + fz)) continue;
                        ArchPier facing = fx > 0 ? ArchPier.East : fx < 0 ? ArchPier.West : fz > 0 ? ArchPier.South : ArchPier.North;
                        found.Add((x, z, ax, az, facing));
                    }
                }
        if (found.Count == 0) return;
        var (wx, wz, dax, daz, f) = found[rng.Range(0, found.Count - 1)];
        // Which half is on the left of someone in the room looking at the window
        var (lx, lz) = L188LeftOf(Opposite(f));
        bool firstIsLeft = lx * dax + lz * daz < 0;
        foreach (var (x, z, first) in new[] { (wx, wz, true), (wx + dax, wz + daz, false) })
        {
            ref Tile t = ref b.At(x, z);
            t.Under = Unders.L188Entrance;
            t.Detail = (byte)(host | ((int)f << 4) | (first == firstIsLeft ? 64 : 0));
        }
    }

    /// <summary>The direction on the left of someone facing a direction (x east, z south).</summary>
    public static (int X, int Z) L188LeftOf(ArchPier facing) => facing switch
    {
        ArchPier.East => (0, -1), ArchPier.North => (-1, 0), ArchPier.West => (0, 1), _ => (1, 0),
    };

    /// <summary>A direction as a step (x east, z south).</summary>
    public static (int X, int Z) L188Step(ArchPier p) => Step(p);

    /// <summary>The confetti window once worked out (null until then), boxed so one write publishes it whole to every thread.</summary>
    private System.Runtime.CompilerServices.StrongBox<((int X, int Z) Left, (int X, int Z) Right, ArchPier Facing)?> l188FunWindow;

    /// <summary>
    /// Level Fun's confetti window into 188 (one in the world): in the north wall of the quiet party room nearest the
    /// region's middle, looking into the room. Worked out from Fun's plans alone (never its built cells), so asking for it
    /// while a cell of Fun is being built is safe. Null if Fun has no such room.
    /// </summary>
    public ((int X, int Z) Left, (int X, int Z) Right, ArchPier Facing)? L188FunWindow()
    {
        if (System.Threading.Volatile.Read(ref l188FunWindow) is { } known) return known.Value;
        ((int, int), (int, int), ArchPier)? best = null;
        long bestD = long.MaxValue;
        int cx = FunCentreX * MacroSize, cz = FunCentreZ * MacroSize;
        var (bi0, bj0) = FunBlockOf(cx, cz);
        Tile PlanTile(int gx, int gz)
        {
            var (bi, bj) = FunBlockOf(gx, gz);
            return FunPlan(bi, bj).Tiles[(gz - FunOriginZ - bj * FunBlock) * FunBlock + gx - FunOriginX - bi * FunBlock];
        }
        for (int r = 0; r <= 3 && best == null; r++)
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    foreach (FunRoom room in FunPlan(bi0 + di, bj0 + dj).Rooms)
                    {
                        if (room.Kind != FunZone.Party || room.Guests != 0 || room.Threshold || room.X1 - room.X0 < 5) continue;
                        int x = (room.X0 + room.X1) / 2 - 1, z = room.Z0 - 1;
                        bool ok = true;
                        for (int i = -1; i <= 2 && ok; i++)
                        {
                            Tile w = PlanTile(x + i, z);
                            ok = w.Kind == TileKind.Wall && w.Height == 0 && w.Under == 0;
                        }
                        for (int i = 0; i <= 1 && ok; i++)
                        {
                            Tile f = PlanTile(x + i, z + 1);
                            ok = f.Kind == TileKind.Floor && f.Variant == 0 && f.Depth == 0 && f.Under == 0;
                        }
                        if (!ok || LevelAt(MacroOf(x), MacroOf(z)) != FunLevel || LevelAt(MacroOf(x) - 1, MacroOf(z) - 1) != FunLevel
                            || LevelAt(MacroOf(x) + 1, MacroOf(z) + 1) != FunLevel) continue;
                        long d = (long)(x - cx) * (x - cx) + (long)(z - cz) * (z - cz);
                        if (d >= bestD) continue;
                        bestD = d;
                        // Facing south, into the room: seen from the room (looking north) the left half is the west one
                        best = ((x, z), (x + 1, z), ArchPier.South);
                    }
                }
        System.Threading.Volatile.Write(ref l188FunWindow, new(best));
        return best;
    }

    /// <summary>Level Fun's hook: marks the confetti window's two wall tiles if they lie in this cell.</summary>
    private void MarkL188FunWindow(Builder b, int mx, int mz)
    {
        if (!L188Entrances || L188FunWindow() is not { } w) return;
        foreach (var (p, left) in new[] { (w.Left, true), (w.Right, false) })
        {
            if (MacroOf(p.X) != mx || MacroOf(p.Z) != mz) continue;
            ref Tile t = ref b.At(p.X - mx * MacroSize, p.Z - mz * MacroSize);
            if (t.Kind != TileKind.Wall) continue;
            t.Under = Unders.L188Entrance;
            t.Detail = (byte)(3 | ((int)w.Facing << 4) | (left ? 64 : 0));
        }
    }
}
