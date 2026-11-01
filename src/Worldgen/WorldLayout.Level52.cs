using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 52, "The Greenfield Campus" (experimental): kept as level 23 (<see cref="Level52"/>) and shown as "52". After
/// Fandom's Level 52 (the WindXD rewrite; docs/design/experimental-levels/lore/52-brief.md, 52-plan.md): school campuses
/// on rolling green hills under a blue sky that never changes, each fenced in on its own, joined by gravel roads. The ways
/// in (a high school in the city, an emergency exit in Level 4) and the doors that lead back are WorldLayout.Level52.Links.cs's.
///
/// <para><b>The land.</b> The round region is open sky. Campuses lie on a lattice <see cref="L52Period"/> blocks square,
/// one to a lattice cell (about one cell in six is left as open plain); the ground between them rolls in low, wavy hills
/// (<see cref="L52Ground"/>, up to seven blocks) and lies level for forty blocks round each campus. A gravel road runs from
/// each campus to the next one east and south, through the gaps in their fences. Toward the region's rim the hills rise
/// into a ridge. A tile's <see cref="Tile.Height"/> is its ground above the level's floor.</para>
///
/// <para><b>A campus</b> (<see cref="L52Campus"/>, laid out once from its own hash and kept in a <see cref="PlanCache{T}"/>)
/// is fenced all round (a low concrete barrier and a chain-link fence over it), with a wide gap in the middle of each
/// side and a narrower one where a section of the fence was set down out of line; no gate. Inside: lawns and paved
/// paths, a <b>quad</b> (four teaching wings merged round a courtyard of artificial grass, or a sports court) and one to
/// four buildings standing apart (a teaching block, a hall of lodgings, a canteen, a gym, a warehouse). A building has two
/// to eight storeys of four blocks (a slab, three of air); the plan is its ground storey, and the storeys above repeat it
/// (<see cref="L52Furnish"/> says what stands in a room on each storey). A building tile's <see cref="Tile.Depth"/> is its
/// building's storeys, <see cref="Tile.Detail"/> the building's number.</para>
///
/// <para><b>A teaching wing</b> is 21 deep: rooms 7 deep on both sides of a corridor 3 wide, lit, lined with lockers; the
/// rooms (classrooms mostly: desks facing a chalkboard, a teacher's desk, a television of the 2000s) keep their lights
/// off, as the lore has it, and are lit by their windows. Beside each door a plaque gives four digits: the room's number in
/// its building, the storey, the building. The quad has a stairwell in each inner corner, a standalone block one at an end
/// (scissor stairs, <see cref="L52StairWell"/>).</para>
///
/// <para><b>The three named campuses:</b> Marshall David (where everyone arrives: white concrete, five storeys, lockers
/// down every corridor, the M.E.G.'s old offices on the top floor), J. Barry (blue and white paint, a warehouse) and
/// J. Turner (two storeys, a basketball court in the quad, its classrooms turned into lodgings).</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2300-0x23BF are this level's (0x23C0-0x23FF its thresholds').</summary>
    private const ulong SaltL52Shape = 0x2301, SaltL52Campus = 0x2310, SaltL52Room = 0x2311, SaltL52Light = 0x2312, SaltL52Hill = 0x2313,
        SaltL52Wave = 0x2314, SaltL52Tree = 0x2315, SaltL52Gap = 0x2316, SaltL52Stray = 0x2317, SaltL52Plan = 0x2318, SaltL52Storey = 0x2319,
        SaltL52Style = 0x231A;

    /// <summary>The campus lattice (blocks), a storey's height (its slab and three of air), a teaching wing's depth.</summary>
    public const int L52Period = 352, L52Storey = 4, L52WingDepth = 21;

    /// <summary>The most storeys a building has (its roof and parapet stay under the band's top).</summary>
    public const int L52MaxStoreys = 8;

    /// <summary>What a tile is (kept in <see cref="Tile.Zone"/>).</summary>
    public enum L52Zone : byte
    {
        None, Hill, Road, Lawn, Path, Turf, Court, Fence, StrayFence,
        // Buildings
        Ext, Wall, Door, Entrance, Corridor, Room, Stair, Lobby, Hall,
    }

    public enum L52CampusKind : byte { Ordinary, MarshallDavid, JBarry, JTurner }

    public enum L52BuildingKind : byte { Teaching, Lodging, Gym, Canteen, Warehouse, Lecture }

    public enum L52RoomKind : byte { Classroom, Office, Lab, Library, Store, Empty, Lodging, Meg, Closet, Gym, Canteen, Warehouse, RestroomMen, RestroomWomen, Reception, StaffRoom, Changing, Lecture }

    /// <summary>The interior paint (l52-wall-*, l52-locker-*) and the façades (l52-facade-*), by index.</summary>
    public static readonly string[] L52Paints = { "beige", "white", "blue", "grey" };
    public static readonly string[] L52Facades = { "white", "beige", "brick", "grey", "blue" };
    public static readonly string[] L52Trims = { "light", "grey", "stone" };

    /// <summary>Where a campus is, and what it is: worked out cheaply from its hash (the roads between campuses ask often).</summary>
    public sealed class L52Head
    {
        public int Ci, Cj;
        public bool Exists;
        public L52CampusKind Kind;
        /// <summary>The fenced rectangle, in blocks: its north-west corner and size (the fence on its border).</summary>
        public int X0, Z0, W, D;
        /// <summary>The middle of the wide gap in each side's fence, along that side (campus-local): north, east, south, west.</summary>
        public readonly int[] Gap = new int[4];
        public int X1 => X0 + W - 1;
        public int Z1 => Z0 + D - 1;
        public bool Contains(int x, int z) => x >= X0 && z >= Z0 && x <= X1 && z <= Z1;
    }

    public sealed class L52Building
    {
        public int Index, Storeys;
        public L52BuildingKind Kind;
        public int U0, V0, U1, V1;
        /// <summary>
        /// How its outside looks (<see cref="L52AddBuilding"/>): its façade (<see cref="L52Facades"/>); its precast trim's colour
        /// (<see cref="L52Trims"/>); where bands run (0 a cornice only, 1 at every floor line too, 2 at the first floor line); its
        /// windows (0 two then a pier, 1 a ribbon, 2 one then a pier); a dark stone base course or not.
        /// </summary>
        public byte Facade, Trim, Band, Windows;
        public bool Plinth;
    }

    /// <summary>A room (campus-local, its bounding box), the same on every storey of its building.</summary>
    public sealed class L52Room
    {
        public int Id, U0, V0, U1, V1, Building, Number, Area;
        public L52RoomKind Kind;
        public FloorKind Floor;
        /// <summary>The side of the room its door is in (toward its corridor).</summary>
        public ArchPier DoorSide;
        public bool HasDoor;
        /// <summary>Its door onto a corridor (-1 if it opens into a neighbour instead); what it is on the ground storey if not what it is above (round 3).</summary>
        public int DoorU = -1, DoorV = -1;
        public L52RoomKind? GroundKind;
    }

    /// <summary>A stairwell's square: its corner (campus-local), the way its flights run (+j) and its across axis (+i).</summary>
    public readonly record struct L52StairWell(int U, int V, ArchPier J, ArchPier I);

    /// <summary>A campus laid out: its ground storey, tile by tile (campus-local u east, v south), and its buildings and rooms.</summary>
    public sealed class L52Campus
    {
        public L52Head Head;
        public int W, D;
        public byte Paint, Facade;
        public Tile[] Grid;
        /// <summary>The room a tile is in (-1 none); for a plaque's tile, the room it numbers.</summary>
        public short[] RoomOf;
        public readonly List<L52Building> Buildings = new();
        public readonly List<L52Room> Rooms = new();
        /// <summary>Round 3: the fittings on its tiles (<see cref="L52Fixture"/>), which tiles have any, its stairwells and their buildings.</summary>
        public readonly Dictionary<int, List<L52Fixture>> Fixtures = new();
        public bool[] HasFixture;
        public readonly List<(L52StairWell S, int Building)> Stairs = new();
        public bool InGrid(int u, int v) => u >= 0 && v >= 0 && u < W && v < D;
        public ref Tile At(int u, int v) => ref Grid[u + v * W];
    }

    private PlanCache<L52Head> l52Heads;
    private PlanCache<L52Campus> l52Campuses;

    public L52Head L52HeadOf(int ci, int cj) =>
        LazyInitializer.EnsureInitialized(ref l52Heads, () => new PlanCache<L52Head>(512, MakeL52Head)).Get(ci, cj);

    /// <summary>A campus's plan (shared: read it, never change it); null where its lattice cell has none.</summary>
    public L52Campus L52CampusOf(int ci, int cj)
    {
        if (!L52HeadOf(ci, cj).Exists) return null;
        return LazyInitializer.EnsureInitialized(ref l52Campuses, () => new PlanCache<L52Campus>(12, MakeL52Campus)).Get(ci, cj);
    }

    /// <summary>The campus whose fence encloses a block position (and the tile's index in its plan), or null.</summary>
    public L52Campus L52CampusAt(int x, int z, out int index)
    {
        index = -1;
        int ci = Hashing.FloorDiv(x, L52Period), cj = Hashing.FloorDiv(z, L52Period);
        L52Head head = L52HeadOf(ci, cj);
        if (!head.Exists || !head.Contains(x, z)) return null;
        L52Campus c = L52CampusOf(ci, cj);
        index = x - head.X0 + (z - head.Z0) * head.W;
        return c;
    }

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees east of south.</summary>
    private double L52Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    public int L52CentreX => spawnMacroX + (int)Math.Round(L52Reach * Math.Sin(Math.PI / 8));
    public int L52CentreZ => spawnMacroZ + (int)Math.Round(L52Reach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells.</summary>
    public int L52Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL52(double mx, double mz) => InRoundRegion(mx, mz, L52CentreX, L52CentreZ, L52Radius, SaltL52Shape);

    /// <summary>The lattice cell of Marshall David Campus: the one the region's centre lies in.</summary>
    public (int Ci, int Cj) L52MarshallDavid =>
        (Hashing.FloorDiv(L52CentreX * MacroSize + MacroSize / 2, L52Period), Hashing.FloorDiv(L52CentreZ * MacroSize + MacroSize / 2, L52Period));

    private static readonly (int, int)[] L52Dirs8 = { (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1) };

    /// <summary>The lattice cells of J. Turner Campus (about a mile from Marshall David, or as far as the region allows) and of J. Barry Campus.</summary>
    public ((int Ci, int Cj) Turner, (int Ci, int Cj) Barry) L52Named
    {
        get
        {
            var (ci, cj) = L52MarshallDavid;
            ulong h = Hashing.Hash(seed, 0, 0, SaltL52Campus + 1);
            int reach = Math.Max(1, L52Radius * MacroSize / L52Period - 2);
            int k = (int)(h % 8), k2 = (k + 3 + (int)((h >> 8) % 3)) % 8;
            int dt = Math.Min(4, reach), db = Math.Min(3, reach);
            var (tx, tz) = L52Dirs8[k];
            var (bx, bz) = L52Dirs8[k2];
            return ((ci + tx * dt, cj + tz * dt), (ci + bx * db, cj + bz * db));
        }
    }

    /// <summary>
    /// A place to look for somewhere to arrive: "each entrant will land in the same building or one nearby", so Marshall
    /// David Campus, or one of the campuses round it.
    /// </summary>
    private (int Mx, int Mz) L52ArrivalCell(ulong h)
    {
        var (ci, cj) = L52MarshallDavid;
        if (Hashing.Unit(h) >= 0.55)
        {
            var (dx, dz) = L52Dirs8[(int)(Hashing.Mix(h) % 8)];
            if (L52HeadOf(ci + dx, cj + dz).Exists) { ci += dx; cj += dz; }
        }
        L52Head head = L52HeadOf(ci, cj);
        if (!head.Exists) return (L52CentreX, L52CentreZ);
        ulong h2 = Hashing.Mix(h + 7);
        int x = head.X0 + 8 + (int)(Hashing.Unit(h2) * (head.W - 16)), z = head.Z0 + 8 + (int)(Hashing.Unit(Hashing.Mix(h2)) * (head.D - 16));
        return (MacroOf(x), MacroOf(z));
    }

    /// <summary>Arriving: on a campus's paths and lawns, or in a corridor on the ground floor.</summary>
    private static bool IsL52ArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Height == 0 && t.Zone is (byte)L52Zone.Corridor or (byte)L52Zone.Lobby or (byte)L52Zone.Path or (byte)L52Zone.Lawn;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>): on the ground.</summary>
    private static double L52ArrivalHeight(in Tile t, double stand) => t.Height + stand;

    // ================= The land =================

    /// <summary>The wall line between two of the level's cells: none.</summary>
    private Edge L52Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L52Wall };

    private static double L52Smooth(double t) => t * t * (3 - 2 * t);

    /// <summary>
    /// The ground at a block position outside the campuses, in blocks above the floor (0-7): low hills from a noise, a long
    /// wave run across them ("a wavy-like pattern hillscape"), laid level within forty blocks of a campus's fence.
    /// </summary>
    public int L52Ground(int x, int z)
    {
        double n = 0.5 + 0.55 * Fbm(x / 95.0, z / 95.0, SaltL52Hill);
        double wave = 0.5 + 0.5 * Math.Sin((x * 0.8 + z * 0.6) / 23.0 + 2.2 * Noise(x / 140.0, z / 140.0, SaltL52Wave));
        double f = 6.5 * Math.Clamp(0.7 * n + 0.3 * wave, 0, 1);
        L52Head head = L52HeadOf(Hashing.FloorDiv(x, L52Period), Hashing.FloorDiv(z, L52Period));
        if (head.Exists)
        {
            double dx = Math.Max(0, Math.Max(head.X0 - x, x - head.X1)), dz = Math.Max(0, Math.Max(head.Z0 - z, z - head.Z1));
            double d = Math.Sqrt(dx * dx + dz * dz);
            f *= L52Smooth(Math.Clamp((d - 8) / 40.0, 0, 1));
        }
        // (The roads run level, cut through the hills, the banks easing up either side)
        if (f >= 0.5) f *= L52Smooth(Math.Clamp((L52RoadDistance(x, z) - 2) / 12.0, 0, 1));
        return Math.Clamp((int)Math.Round(f), 0, 7);
    }

    /// <summary>How far a block position is from the middle line of the nearest road (blocks; large where none is near).</summary>
    private double L52RoadDistance(int x, int z)
    {
        int ci = Hashing.FloorDiv(x, L52Period), cj = Hashing.FloorDiv(z, L52Period);
        L52Head here = L52HeadOf(ci, cj);
        double best = 1e9;
        void Pair(L52Head a, L52Head b, bool east)
        {
            if (!a.Exists || !b.Exists) return;
            static double Seg(int x, int z, double x0, double z0, double x1, double z1)
            {
                double dx = Math.Max(0, Math.Max(Math.Min(x0, x1) - x, x - Math.Max(x0, x1)));
                double dz = Math.Max(0, Math.Max(Math.Min(z0, z1) - z, z - Math.Max(z0, z1)));
                return Math.Sqrt(dx * dx + dz * dz);
            }
            // (The three stretches of L52OnRoad, by their middle lines)
            if (east)
            {
                double za = a.Z0 + a.Gap[1] - 0.5, zb = b.Z0 + b.Gap[3] - 0.5, xm = (a.X1 + b.X0) / 2 - 0.5;
                best = Math.Min(best, Math.Min(Seg(x, z, a.X1, za, xm, za), Math.Min(Seg(x, z, xm, za, xm, zb), Seg(x, z, xm, zb, b.X0, zb))));
            }
            else
            {
                double xa = a.X0 + a.Gap[2] - 0.5, xb = b.X0 + b.Gap[0] - 0.5, zm = (a.Z1 + b.Z0) / 2 - 0.5;
                best = Math.Min(best, Math.Min(Seg(x, z, xa, a.Z1, xa, zm), Math.Min(Seg(x, z, xa, zm, xb, zm), Seg(x, z, xb, zm, xb, b.Z0))));
            }
        }
        Pair(here, L52HeadOf(ci + 1, cj), true);
        Pair(L52HeadOf(ci - 1, cj), here, true);
        Pair(here, L52HeadOf(ci, cj + 1), false);
        Pair(L52HeadOf(ci, cj - 1), here, false);
        return best;
    }

    private L52Head MakeL52Head(int ci, int cj)
    {
        ulong h = Hashing.Hash(seed, ci, cj, SaltL52Campus);
        var head = new L52Head { Ci = ci, Cj = cj };
        var md = L52MarshallDavid;
        var (turner, barry) = L52Named;
        head.Kind = (ci, cj) == md ? L52CampusKind.MarshallDavid : (ci, cj) == turner ? L52CampusKind.JTurner
            : (ci, cj) == barry ? L52CampusKind.JBarry : L52CampusKind.Ordinary;
        var rng = new Rng(Hashing.Mix(h));
        head.W = 2 * rng.Range(76, 106);
        head.D = 2 * rng.Range(76, 106);
        if (head.Kind == L52CampusKind.MarshallDavid) { head.W = Math.Max(head.W, 196); head.D = Math.Max(head.D, 184); }
        if (head.Kind == L52CampusKind.JTurner) { head.W = Math.Min(head.W, 176); head.D = Math.Min(head.D, 176); }
        int mx = (L52Period - head.W) / 2, mz = (L52Period - head.D) / 2;
        head.X0 = ci * L52Period + mx + rng.Range(-20, 20);
        head.Z0 = cj * L52Period + mz + rng.Range(-20, 20);
        for (int s = 0; s < 4; s++)
        {
            int len = s % 2 == 0 ? head.W : head.D;
            head.Gap[s] = len / 2 + rng.Range(-len / 5, len / 5);
        }
        bool open = rng.NextDouble() < 0.16 && head.Kind == L52CampusKind.Ordinary;
        head.Exists = !open && L52RectInside(head.X0 - 96, head.Z0 - 96, head.X1 + 96, head.Z1 + 96);
        return head;
    }

    /// <summary>Whether a rectangle of blocks lies in the level (its corners and the middles of its sides).</summary>
    private bool L52RectInside(int x0, int z0, int x1, int z1)
    {
        foreach (int x in new[] { x0, (x0 + x1) / 2, x1 })
            foreach (int z in new[] { z0, (z0 + z1) / 2, z1 })
                if (LevelAt(MacroOf(x), MacroOf(z)) != Level52) return false;
        return true;
    }

    /// <summary>
    /// The road between two neighbouring campuses (<paramref name="east"/>: campus a and the one east of it, else the
    /// one south), as up to three straight stretches four blocks wide: out of a's gap, across at the halfway line, into b's.
    /// </summary>
    private static bool L52OnRoad(L52Head a, L52Head b, bool east, int x, int z)
    {
        if (!a.Exists || !b.Exists) return false;
        if (east)
        {
            int za = a.Z0 + a.Gap[1], zb = b.Z0 + b.Gap[3], xm = (a.X1 + b.X0) / 2;
            if (x <= a.X1 || x >= b.X0) return false;
            if (z >= za - 2 && z <= za + 1 && x <= xm + 1) return true;
            if (z >= zb - 2 && z <= zb + 1 && x >= xm - 2) return true;
            return x >= xm - 2 && x <= xm + 1 && z >= Math.Min(za, zb) - 2 && z <= Math.Max(za, zb) + 1;
        }
        int xa = a.X0 + a.Gap[2], xb = b.X0 + b.Gap[0], zm = (a.Z1 + b.Z0) / 2;
        if (z <= a.Z1 || z >= b.Z0) return false;
        if (x >= xa - 2 && x <= xa + 1 && z <= zm + 1) return true;
        if (x >= xb - 2 && x <= xb + 1 && z >= zm - 2) return true;
        return z >= zm - 2 && z <= zm + 1 && x >= Math.Min(xa, xb) - 2 && x <= Math.Max(xa, xb) + 1;
    }

    private bool L52Road(int x, int z)
    {
        int ci = Hashing.FloorDiv(x, L52Period), cj = Hashing.FloorDiv(z, L52Period);
        L52Head here = L52HeadOf(ci, cj);
        return L52OnRoad(here, L52HeadOf(ci + 1, cj), true, x, z) || L52OnRoad(L52HeadOf(ci - 1, cj), here, true, x, z)
            || L52OnRoad(here, L52HeadOf(ci, cj + 1), false, x, z) || L52OnRoad(L52HeadOf(ci, cj - 1), here, false, x, z);
    }

    /// <summary>
    /// Lays out one of the level's cells: a campus's plan where a fence encloses the tile, else the open land (hills, roads,
    /// a lone tree now and then, a stretch of fence out on an empty plain that fences nothing), rising into a ridge toward
    /// the region's rim.
    /// </summary>
    private void BuildLevel52(Builder b, int mx, int mz)
    {
        // The rim: how far each tile is from the nearest cell that is not the level's, if any is within two cells
        List<(int X0, int Z0)> outside = null;
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
                if (LevelAt(mx + dx, mz + dz) != Level52) (outside ??= new()).Add(((mx + dx) * MacroSize, (mz + dz) * MacroSize));

        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region
                int x = mx * MacroSize + lx, z = mz * MacroSize + lz;
                L52Campus c = L52CampusAt(x, z, out int i);
                if (c != null)
                {
                    byte level = t.Level;
                    t = c.Grid[i];
                    t.Level = level;
                    continue;
                }
                t.Zone = (byte)L52Zone.Hill;
                t.Floor = FloorKind.L52Grass;
                int g = L52Ground(x, z);
                if (outside != null)
                {
                    double best = 1e9;
                    foreach (var (ox, oz) in outside)
                    {
                        double ddx = Math.Max(0, Math.Max(ox - x, x - (ox + MacroSize - 1))), ddz = Math.Max(0, Math.Max(oz - z, z - (oz + MacroSize - 1)));
                        best = Math.Min(best, Math.Sqrt(ddx * ddx + ddz * ddz));
                    }
                    if (best < 64) g = Math.Max(g, (int)Math.Round(26 * L52Smooth(1 - best / 64)));
                }
                t.Height = (byte)g;
                if (L52Road(x, z))
                {
                    t.Zone = (byte)L52Zone.Road;
                    t.Floor = Noise(x / 7.0, z / 7.0, SaltL52Gap) > 0.45 ? FloorKind.L52Sand : FloorKind.L52Gravel;
                    continue;
                }
                // (Round 3) a bus shelter by the road where it leaves a campus's east gap, its back to the hills
                if (L52BusStop(x, z))
                {
                    t.Variant = Props.BusShelter;
                    t.Pier = ArchPier.South;
                    continue;
                }
                if (L52StrayFence(x, z, out ArchPier along))
                {
                    t.Kind = TileKind.Wall;
                    t.Zone = (byte)L52Zone.StrayFence;
                    t.Pier = along;
                    continue;
                }
                // A lone tree now and then: one candidate in each 11-block square
                int tx = Hashing.FloorDiv(x, 11), tz = Hashing.FloorDiv(z, 11);
                ulong th = Hashing.Hash(seed, tx, tz, SaltL52Tree);
                if (Hashing.Unit(th) < 0.07 && x == tx * 11 + 2 + (int)((th >> 20) % 7) && z == tz * 11 + 2 + (int)((th >> 28) % 7) && g < 10)
                    t.Variant = Props.Tree;
            }
    }

    /// <summary>Where a bus shelter stands: beside the road out of a campus's east gap, ten blocks out from the fence, on the north side.</summary>
    private bool L52BusStop(int x, int z)
    {
        int ci = Hashing.FloorDiv(x - 10, L52Period), cj = Hashing.FloorDiv(z, L52Period);
        for (int d = 0; d <= 1; d++)
        {
            L52Head h = L52HeadOf(ci + d, cj);
            if (!h.Exists || !L52HeadOf(ci + d + 1, cj).Exists) continue;
            if (x == h.X1 + 10 && z == h.Z0 + h.Gap[1] - 4) return true;
        }
        return false;
    }

    /// <summary>"A long fence that serves no use": out on an empty plain (a lattice cell with no campus), now and then a long straight run of chain-link.</summary>
    private bool L52StrayFence(int x, int z, out ArchPier along)
    {
        along = ArchPier.North;
        int ci = Hashing.FloorDiv(x, L52Period), cj = Hashing.FloorDiv(z, L52Period);
        if (L52HeadOf(ci, cj).Exists) return false;
        ulong h = Hashing.Hash(seed, ci, cj, SaltL52Stray);
        if (Hashing.Unit(h) > 0.6) return false;
        var rng = new Rng(Hashing.Mix(h));
        bool alongX = rng.Chance(0.5);
        int a0 = rng.Range(60, 140), len = rng.Range(60, 150), across = rng.Range(100, 250);
        int u = x - ci * L52Period, v = z - cj * L52Period;
        along = alongX ? ArchPier.North : ArchPier.East;
        return alongX ? v == across && u >= a0 && u < a0 + len : u == across && v >= a0 && v < a0 + len;
    }

    // ================= A campus =================

    private static (int Du, int Dv) L52Step(ArchPier d) => d switch
    {
        ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0),
    };

    private static ArchPier L52Opposite(ArchPier d) => d switch
    {
        ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East,
    };

    /// <summary>The left hand of someone looking the given way.</summary>
    private static ArchPier L52LeftOf(ArchPier looking) => looking switch
    {
        ArchPier.North => ArchPier.West, ArchPier.South => ArchPier.East, ArchPier.East => ArchPier.North, _ => ArchPier.South,
    };

    private static readonly ArchPier[] L52Ways = { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West };

    private L52Campus MakeL52Campus(int ci, int cj)
    {
        L52Head head = L52HeadOf(ci, cj);
        int W = head.W, D = head.D;
        var c = new L52Campus { Head = head, W = W, D = D, Grid = new Tile[W * D], RoomOf = new short[W * D], HasFixture = new bool[W * D] };
        Array.Fill(c.RoomOf, (short)-1);
        var rng = new Rng(Hashing.Hash(seed, ci, cj, SaltL52Plan));
        L52CampusKind kind = head.Kind;
        c.Paint = kind switch
        {
            L52CampusKind.MarshallDavid => 1, L52CampusKind.JBarry => 2, L52CampusKind.JTurner => 0,
            _ => (byte)(rng.Chance(0.6) ? 0 : rng.Chance(0.5) ? 3 : 1),
        };
        c.Facade = kind switch
        {
            L52CampusKind.MarshallDavid => 0, L52CampusKind.JBarry => 4, L52CampusKind.JTurner => 0,
            _ => (byte)rng.Range(0, 3),
        };
        for (int i = 0; i < c.Grid.Length; i++) c.Grid[i] = new Tile { Kind = TileKind.Floor, Zone = (byte)L52Zone.Lawn, Floor = FloorKind.L52Grass };

        // The fence and its gaps: a wide one in the middle of each side, and a narrow one where a section is out of line
        for (int s = 0; s < 4; s++)
        {
            int len = s % 2 == 0 ? W : D;
            int extra = rng.Range(14, len - 15);
            if (Math.Abs(extra - head.Gap[s]) < 12) extra = head.Gap[s] + (head.Gap[s] < len / 2 ? 30 : -30);
            for (int a = 0; a < len; a++)
            {
                var (u, v) = s switch { 0 => (a, 0), 1 => (W - 1, a), 2 => (a, D - 1), _ => (0, a) };
                bool gap = Math.Abs(a - head.Gap[s]) <= 2 || a >= extra - 1 && a <= extra + 1;
                ref Tile t = ref c.At(u, v);
                if (gap && a > 1 && a < len - 2) { t.Zone = (byte)L52Zone.Path; t.Floor = FloorKind.L52Paving; continue; }
                t.Kind = TileKind.Wall;
                t.Zone = (byte)L52Zone.Fence;
                t.Pier = s % 2 == 0 ? ArchPier.North : ArchPier.East;
            }
            // The misplaced section, set down a step inside the line beside its gap
            for (int a = extra - 1; a <= extra + 1; a++)
            {
                var (u, v) = s switch { 0 => (a, 2), 1 => (W - 3, a), 2 => (a, D - 3), _ => (2, a) };
                ref Tile t = ref c.At(u, v);
                t.Kind = TileKind.Wall;
                t.Zone = (byte)L52Zone.Fence;
                t.Pier = s % 2 == 0 ? ArchPier.North : ArchPier.East;
            }
        }

        // The quad: in one corner of the campus, the other buildings in the room it leaves
        int qw = Math.Min(W - 70, rng.Range(84, 124)), qd = Math.Min(D - 70, rng.Range(84, 124));
        if (kind == L52CampusKind.JTurner) { qw = Math.Min(W - 70, 96); qd = Math.Min(D - 70, 92); }
        bool east = rng.Chance(0.5), south = rng.Chance(0.5);
        int qu0 = east ? W - 14 - qw : 14, qv0 = south ? D - 14 - qd : 14;
        int storeys = kind switch
        {
            L52CampusKind.MarshallDavid => 5, L52CampusKind.JTurner => 2, L52CampusKind.JBarry => 3,
            _ => L52PickStoreys(rng),
        };
        bool court = kind == L52CampusKind.JTurner || kind == L52CampusKind.Ordinary && rng.Chance(0.3);
        L52LayQuad(c, rng, qu0, qv0, qw, qd, storeys, court);

        // The other buildings, in the strips beside the quad (east or west of it; north or south of it)
        var plots = new List<(int U0, int V0, int U1, int V1)>();
        int su0 = east ? 10 : qu0 + qw + 12, su1 = east ? qu0 - 12 : W - 11;
        if (su1 - su0 >= 28) plots.Add((su0, 10, su1, D - 11));
        int sv0 = south ? 10 : qv0 + qd + 12, sv1 = south ? qv0 - 12 : D - 11;
        int bu0 = east ? qu0 : 10, bu1 = east ? W - 11 : qu0 + qw - 1;
        if (sv1 - sv0 >= 28) plots.Add((bu0, sv0, bu1, sv1));
        var kinds = new List<L52BuildingKind>();
        if (kind == L52CampusKind.JBarry) kinds.Add(L52BuildingKind.Warehouse);
        kinds.Add(L52BuildingKind.Canteen);
        if (rng.Chance(0.6) || kind == L52CampusKind.MarshallDavid) kinds.Add(L52BuildingKind.Gym);
        // (Round 3) a lecture theatre, as a university has (the lore's campus "housing a university")
        if (Hashing.Unit(Hashing.Hash(seed, ci, cj, SaltL52Plan + 1)) < 0.45 || kind == L52CampusKind.MarshallDavid) kinds.Add(L52BuildingKind.Lecture);
        kinds.Add(rng.Chance(kind == L52CampusKind.JTurner ? 0.8 : 0.35) ? L52BuildingKind.Lodging : L52BuildingKind.Teaching);
        if (rng.Chance(0.5)) kinds.Add(L52BuildingKind.Teaching);
        bool pitch = false;
        foreach (var (pu0, pv0, pu1, pv1) in plots)
        {
            bool alongX = pu1 - pu0 >= pv1 - pv0;
            int len = alongX ? pu1 - pu0 + 1 : pv1 - pv0 + 1, room = alongX ? pv1 - pv0 + 1 : pu1 - pu0 + 1;
            int at = 0;
            while (kinds.Count > 0)
            {
                L52BuildingKind bk = kinds[0];
                bool hall = bk is L52BuildingKind.Gym or L52BuildingKind.Canteen or L52BuildingKind.Warehouse or L52BuildingKind.Lecture;
                int depth = hall ? Math.Min(room - 6, bk == L52BuildingKind.Gym ? 30 : 26) : L52WingDepth;
                if (depth < (hall ? 20 : L52WingDepth) || room < depth + 6) { kinds.RemoveAt(0); continue; }
                int length = hall ? Math.Min(len - at, bk == L52BuildingKind.Gym ? 40 : rng.Range(34, 46)) : Math.Min(len - at, rng.Range(46, 84));
                if (length < (hall ? 26 : 34)) break;
                kinds.RemoveAt(0);
                int slack = room - depth;
                int off = slack / 2 + rng.Range(-slack / 4, slack / 4);
                int u0 = alongX ? pu0 + at : pu0 + off, v0 = alongX ? pv0 + off : pv0 + at;
                int u1 = alongX ? u0 + length - 1 : u0 + depth - 1, v1 = alongX ? v0 + depth - 1 : v0 + length - 1;
                if (hall) L52LayHall(c, u0, v0, u1, v1, bk, alongX);
                else L52LayWing(c, rng, u0, v0, u1, v1, alongX, bk, kind == L52CampusKind.MarshallDavid ? 5 : Math.Clamp(L52PickStoreys(rng), 2, 6));
                at += length + rng.Range(10, 18);
            }
            // What room is left at the end of the plot: a football pitch inside a running track, where it fits
            if (!pitch && len - at >= 62 && room >= 44)
            {
                int across = Math.Min(room - 6, 50), length = Math.Min(len - at, 84);
                int u0 = alongX ? pu0 + at : pu0 + 1, v0 = alongX ? pv0 + 1 : pv0 + at;
                int u1 = alongX ? u0 + length - 1 : u0 + across - 1, v1 = alongX ? v0 + across - 1 : v0 + length - 1;
                L52LayPitch(c, u0, v0, u1, v1, alongX);
                pitch = true;
            }
        }

        L52LayBridges(c);
        L52LayPaths(c);
        L52LayEntrances(c);
        L52MarkWaysBack(c);
        L52LayDetails(c);
        L52LayGrounds(c);
        return c;
    }

    private static int L52PickStoreys(Rng rng)
    {
        double r = rng.NextDouble();
        return r < 0.16 ? 2 : r < 0.46 ? 3 : r < 0.74 ? 4 : r < 0.89 ? 5 : r < 0.96 ? 6 : r < 0.99 ? 7 : 8;
    }

    /// <summary>
    /// Adds a building to a campus, with the look of its outside: the campus's façade mostly, now and then another of the
    /// lore's colours ("pale brown, gray, beige, and off-white"); Marshall David and J. Turner all white concrete, J. Barry
    /// blue and white by turns. Trim, bands, windows and base course vary building by building, so no two read the same.
    /// </summary>
    private L52Building L52AddBuilding(L52Campus c, L52BuildingKind kind, int u0, int v0, int u1, int v1, int storeys)
    {
        var b = new L52Building { Index = c.Buildings.Count + 1, Kind = kind, U0 = u0, V0 = v0, U1 = u1, V1 = v1, Storeys = Math.Clamp(storeys, 1, L52MaxStoreys) };
        ulong h = Hashing.Hash(seed, c.Head.X0 + b.Index * 101, c.Head.Z0 - b.Index * 37, SaltL52Style);
        b.Facade = c.Head.Kind switch
        {
            L52CampusKind.MarshallDavid or L52CampusKind.JTurner => 0,
            L52CampusKind.JBarry => (byte)(b.Index % 2 == 1 ? 4 : 0),
            _ => Hashing.Unit(h) < 0.55 ? c.Facade : (byte)((h >> 8) % 4),
        };
        // (White concrete takes grey or sandstone trim; every other façade the off-white)
        b.Trim = b.Facade == 0 ? (byte)((h >> 16) % 3 == 0 ? 2 : 1) : (byte)0;
        b.Band = (byte)((h >> 12) % 3);
        b.Windows = c.Head.Kind == L52CampusKind.MarshallDavid ? (byte)0 : (byte)((h >> 20) % 3);
        b.Plinth = (h >> 24 & 3) != 0;
        c.Buildings.Add(b);
        return b;
    }

    /// <summary>Marks a footprint as a building's: outside wall round its edge, its inside to be laid out.</summary>
    private static void L52Footprint(L52Campus c, L52Building b)
    {
        for (int v = b.V0; v <= b.V1; v++)
            for (int u = b.U0; u <= b.U1; u++)
            {
                ref Tile t = ref c.At(u, v);
                bool edge = u == b.U0 || u == b.U1 || v == b.V0 || v == b.V1;
                t = new Tile
                {
                    Kind = edge ? TileKind.Wall : TileKind.Floor, Zone = (byte)(edge ? L52Zone.Ext : L52Zone.Room), Depth = (byte)b.Storeys,
                    Detail = (byte)b.Index, Floor = FloorKind.L52Room,
                };
                if (edge) t.Pier = u == b.U0 ? ArchPier.West : u == b.U1 ? ArchPier.East : v == b.V0 ? ArchPier.North : ArchPier.South;
            }
    }

    private static void L52SetCorridor(L52Campus c, int u, int v, L52Zone zone = L52Zone.Corridor)
    {
        ref Tile t = ref c.At(u, v);
        t.Kind = TileKind.Floor;
        t.Zone = (byte)zone;
        t.Floor = FloorKind.L52Floor;
    }

    /// <summary>The quad: four teaching wings round a courtyard, a corridor round the whole of it, a stairwell in each inner corner.</summary>
    private void L52LayQuad(L52Campus c, Rng rng, int u0, int v0, int w, int d, int storeys, bool court)
    {
        int u1 = u0 + w - 1, v1 = v0 + d - 1;
        L52Building b = L52AddBuilding(c, L52BuildingKind.Teaching, u0, v0, u1, v1, storeys);
        L52Footprint(c, b);
        // The courtyard (and the façade round it)
        int cu0 = u0 + 20, cv0 = v0 + 20, cu1 = u1 - 20, cv1 = v1 - 20;
        for (int v = cv0; v <= cv1; v++)
            for (int u = cu0; u <= cu1; u++)
            {
                ref Tile t = ref c.At(u, v);
                bool edge = u == cu0 || u == cu1 || v == cv0 || v == cv1;
                if (edge)
                {
                    t.Kind = TileKind.Wall;
                    t.Zone = (byte)L52Zone.Ext;
                    t.Pier = u == cu0 ? ArchPier.East : u == cu1 ? ArchPier.West : v == cv0 ? ArchPier.South : ArchPier.North;
                }
                else t = new Tile { Kind = TileKind.Floor, Zone = (byte)L52Zone.Turf, Floor = FloorKind.L52Turf };
            }
        // The corridor round the quad, 9-11 in from the outside
        for (int v = v0 + 9; v <= v1 - 9; v++)
            for (int u = u0 + 9; u <= u1 - 9; u++)
                if (u <= u0 + 11 || u >= u1 - 11 || v <= v0 + 11 || v >= v1 - 11) L52SetCorridor(c, u, v);
        // Stairwells in the four inner corners (13-19 in), their doors onto the corridor that runs along x
        L52LayStair(c, new L52StairWell(u0 + 13, v0 + 13, ArchPier.East, ArchPier.South));
        L52LayStair(c, new L52StairWell(u1 - 13, v0 + 13, ArchPier.West, ArchPier.South));
        L52LayStair(c, new L52StairWell(u0 + 13, v1 - 13, ArchPier.East, ArchPier.North));
        L52LayStair(c, new L52StairWell(u1 - 13, v1 - 13, ArchPier.West, ArchPier.North));
        // A way in through the outer rooms in the middle of each side (a door on the ground floor, a window above),
        // and through the inner rooms into the courtyard on two opposite sides
        bool courtNS = rng.Chance(0.5);
        for (int s = 0; s < 4; s++)
        {
            bool alongX = s % 2 == 0;
            int mid = alongX ? (u0 + u1) / 2 + rng.Range(-6, 6) : (v0 + v1) / 2 + rng.Range(-6, 6);
            ArchPier outward = L52Ways[s];
            (int U, int V) At(int k, int depth) =>
                alongX ? (mid + k, s == 0 ? v0 + depth : v1 - depth) : (s == 1 ? u1 - depth : u0 + depth, mid + k);
            for (int k = -1; k <= 1; k++)
                for (int depth = 0; depth <= 8; depth++)
                {
                    var (u, v) = At(k, depth);
                    ref Tile t = ref c.At(u, v);
                    if (depth == 0) { t.Kind = TileKind.Doorway; t.Zone = (byte)L52Zone.Entrance; t.Pier = outward; }
                    else L52SetCorridor(c, u, v, L52Zone.Lobby);
                }
            if (alongX == courtNS)
                for (int k = -1; k <= 1; k++)
                    for (int depth = 12; depth <= 20; depth++)
                    {
                        var (u, v) = At(k, depth);
                        ref Tile t = ref c.At(u, v);
                        if (depth == 20) { t.Kind = TileKind.Doorway; t.Zone = (byte)L52Zone.Entrance; t.Pier = L52Opposite(outward); }
                        else L52SetCorridor(c, u, v, L52Zone.Lobby);
                    }
        }
        L52Partition(c, rng, b);
        L52LayCourtyard(c, rng, cu0 + 1, cv0 + 1, cu1 - 1, cv1 - 1, court, courtNS);
    }

    /// <summary>A teaching block or hall of lodgings standing apart: a corridor down its length, doors at both ends, a stairwell at one end.</summary>
    private void L52LayWing(L52Campus c, Rng rng, int u0, int v0, int u1, int v1, bool alongX, L52BuildingKind kind, int storeys)
    {
        L52Building b = L52AddBuilding(c, kind, u0, v0, u1, v1, storeys);
        L52Footprint(c, b);
        int len = alongX ? u1 - u0 + 1 : v1 - v0 + 1;
        for (int a = 1; a < len - 1; a++)
            for (int k = 9; k <= 11; k++)
                if (alongX) L52SetCorridor(c, u0 + a, v0 + k);
                else L52SetCorridor(c, u0 + k, v0 + a);
        // Doors at both ends of the corridor
        for (int k = 9; k <= 11; k++)
            foreach (int a in new[] { 0, len - 1 })
            {
                int u = alongX ? u0 + a : u0 + k, v = alongX ? v0 + k : v0 + a;
                ref Tile t = ref c.At(u, v);
                t.Kind = TileKind.Doorway;
                t.Zone = (byte)L52Zone.Entrance;
            }
        // The stairwell: in the rooms on one side, at one end; i runs away from the corridor into the rooms, j along the wing
        bool high = rng.Chance(0.5), far = rng.Chance(0.5);
        int ja = far ? len - 8 : 1;
        ArchPier jd = alongX ? ArchPier.East : ArchPier.South;
        ArchPier id = alongX ? (high ? ArchPier.South : ArchPier.North) : (high ? ArchPier.East : ArchPier.West);
        int iStart = high ? 13 : 7;
        L52LayStair(c, alongX ? new L52StairWell(u0 + ja, v0 + iStart, jd, id) : new L52StairWell(u0 + iStart, v0 + ja, jd, id));
        L52Partition(c, rng, b);
    }

    /// <summary>
    /// A stairwell, 7 by 7: two flights (i 0-2 climbing toward -j from even storeys, i 4-6 toward +j from odd ones) round a
    /// core wall (i 3), landings across j 0 and j 5-6; doors in the wall on its -i side at both landings. A tile keeps
    /// i * 8 + j in <see cref="Tile.Detail"/> and +j in <see cref="Tile.Pier"/>.
    /// </summary>
    private static void L52LayStair(L52Campus c, L52StairWell s)
    {
        c.Stairs.Add((s, c.Buildings.Count));
        var (jdu, jdv) = L52Step(s.J);
        var (idu, idv) = L52Step(s.I);
        for (int i = 0; i < 7; i++)
            for (int j = 0; j < 7; j++)
            {
                int u = s.U + j * jdu + i * idu, v = s.V + j * jdv + i * idv;
                ref Tile t = ref c.At(u, v);
                t.Kind = i == 3 && j >= 1 && j <= 4 ? TileKind.Wall : TileKind.Floor;
                t.Zone = (byte)L52Zone.Stair;
                t.Floor = FloorKind.L52Concrete;
                t.Detail = (byte)(i * 8 + j);
                t.Pier = s.J;
                t.Under = 0;
                t.Ceiling = i == 3 && (j == 0 || j == 6) ? CeilingKind.LightOn : 0;
                if (j >= 1 && j <= 4 && i != 3) t.Stair = 1;
            }
        // The wall round it, and its doors
        for (int i = -1; i <= 7; i++)
            for (int j = -1; j <= 7; j++)
            {
                if (i >= 0 && i <= 6 && j >= 0 && j <= 6) continue;
                int u = s.U + j * jdu + i * idu, v = s.V + j * jdv + i * idv;
                if (!c.InGrid(u, v)) continue;
                ref Tile t = ref c.At(u, v);
                if (t.Zone is (byte)L52Zone.Ext or (byte)L52Zone.Corridor or (byte)L52Zone.Lobby) continue;
                if (i == -1 && (j == 0 || j == 5))
                {
                    t.Kind = TileKind.Doorway;
                    t.Zone = (byte)L52Zone.Door;
                    t.Floor = FloorKind.L52Concrete;
                }
                else if (t.Zone != (byte)L52Zone.Door)
                {
                    t.Kind = TileKind.Wall;
                    t.Zone = (byte)L52Zone.Wall;
                }
            }
    }

    /// <summary>
    /// The rooms of a teaching building: walls along the corridors, then every stretch of room left cut across into rooms
    /// eight to eleven long, each with a door onto the corridor (or, failing that, into the room beside it); lockers down
    /// the corridor walls, a numbered plaque beside every door, lights down the corridors, windows.
    /// </summary>
    private void L52Partition(L52Campus c, Rng rng, L52Building b)
    {
        bool InB(int u, int v) => u >= b.U0 && u <= b.U1 && v >= b.V0 && v <= b.V1;
        bool Is(int u, int v, L52Zone z) => InB(u, v) && c.At(u, v).Zone == (byte)z;
        bool Open(int u, int v) => InB(u, v) && c.At(u, v).Zone is (byte)L52Zone.Corridor or (byte)L52Zone.Lobby;
        // Walls along the corridors (wherever a room tile touches one, corners too)
        for (int v = b.V0; v <= b.V1; v++)
            for (int u = b.U0; u <= b.U1; u++)
            {
                if (!Is(u, v, L52Zone.Room)) continue;
                bool near = false;
                for (int dv = -1; dv <= 1 && !near; dv++)
                    for (int du = -1; du <= 1 && !near; du++)
                        if (Open(u + du, v + dv)) near = true;
                if (!near) continue;
                ref Tile t = ref c.At(u, v);
                t.Kind = TileKind.Wall;
                t.Zone = (byte)L52Zone.Wall;
            }
        // The stretches of room left, cut into rooms
        var seen = new bool[c.W * c.D];
        for (int v = b.V0; v <= b.V1; v++)
            for (int u = b.U0; u <= b.U1; u++)
            {
                if (seen[u + v * c.W] || !Is(u, v, L52Zone.Room)) continue;
                var part = L52Flood(c, seen, u, v, b);
                int pu0 = int.MaxValue, pv0 = int.MaxValue, pu1 = int.MinValue, pv1 = int.MinValue;
                foreach (var (pu, pv) in part) { pu0 = Math.Min(pu0, pu); pv0 = Math.Min(pv0, pv); pu1 = Math.Max(pu1, pu); pv1 = Math.Max(pv1, pv); }
                bool alongX = pu1 - pu0 >= pv1 - pv0;
                int len = alongX ? pu1 - pu0 + 1 : pv1 - pv0 + 1;
                // Cut across every eight to eleven blocks (never leaving less than six)
                var cuts = new HashSet<int>();
                for (int a = rng.Range(8, 11); a < len - 6; a += 1 + rng.Range(8, 11)) cuts.Add(a);
                foreach (var (pu, pv) in part)
                {
                    if (!cuts.Contains(alongX ? pu - pu0 : pv - pv0)) continue;
                    ref Tile t = ref c.At(pu, pv);
                    t.Kind = TileKind.Wall;
                    t.Zone = (byte)L52Zone.Wall;
                }
            }
        // The rooms, at last
        Array.Clear(seen);
        int number = 0;
        var mine = new List<L52Room>();
        for (int v = b.V0; v <= b.V1; v++)
            for (int u = b.U0; u <= b.U1; u++)
            {
                if (seen[u + v * c.W] || !Is(u, v, L52Zone.Room)) continue;
                var part = L52Flood(c, seen, u, v, b);
                var room = new L52Room { Id = c.Rooms.Count, Building = b.Index, Area = part.Count, U0 = int.MaxValue, V0 = int.MaxValue, U1 = int.MinValue, V1 = int.MinValue };
                foreach (var (pu, pv) in part)
                {
                    room.U0 = Math.Min(room.U0, pu); room.V0 = Math.Min(room.V0, pv); room.U1 = Math.Max(room.U1, pu); room.V1 = Math.Max(room.V1, pv);
                    c.RoomOf[pu + pv * c.W] = (short)room.Id;
                }
                room.Number = Math.Min(99, ++number);
                c.Rooms.Add(room);
                mine.Add(room);
            }
        // A door onto the corridor for each, about the middle of its side along it
        foreach (L52Room room in mine)
        {
            (int U, int V, ArchPier Side)? best = null;
            double bestD = 1e9;
            double mu = (room.U0 + room.U1) / 2.0, mv = (room.V0 + room.V1) / 2.0;
            for (int v = room.V0 - 1; v <= room.V1 + 1; v++)
                for (int u = room.U0 - 1; u <= room.U1 + 1; u++)
                {
                    if (!Is(u, v, L52Zone.Wall)) continue;
                    foreach (ArchPier side in L52Ways)
                    {
                        var (du, dv) = L52Step(side);
                        int ru = u - du, rv = v - dv; // the room's side of the wall
                        if (!InB(ru, rv) || c.RoomOf[ru + rv * c.W] != room.Id || !Is(ru, rv, L52Zone.Room) || !Open(u + du, v + dv)) continue;
                        // Not at a corner of the corridor wall: both its neighbours along the wall are wall too
                        var (au, av) = L52Step(L52LeftOf(side));
                        if (!Is(u + au, v + av, L52Zone.Wall) || !Is(u - au, v - av, L52Zone.Wall)) continue;
                        double dist = Math.Abs(u - mu) + Math.Abs(v - mv) + rng.NextDouble();
                        if (dist < bestD) { bestD = dist; best = (u, v, side); }
                    }
                }
            if (best is not { } door) continue;
            ref Tile t = ref c.At(door.U, door.V);
            t.Kind = TileKind.Doorway;
            t.Zone = (byte)L52Zone.Door;
            t.Floor = FloorKind.L52Floor;
            room.DoorSide = door.Side;
            room.HasDoor = true;
            room.DoorU = door.U;
            room.DoorV = door.V;
            L52Plaque(c, room, door.U, door.V, door.Side);
        }
        // Rooms with no corridor beside them open into a neighbour that has a way out
        for (int pass = 0; pass < 4; pass++)
            foreach (L52Room room in mine)
            {
                if (room.HasDoor) continue;
                for (int v = room.V0 - 1; v <= room.V1 + 1 && !room.HasDoor; v++)
                    for (int u = room.U0 - 1; u <= room.U1 + 1 && !room.HasDoor; u++)
                    {
                        if (!Is(u, v, L52Zone.Wall)) continue;
                        foreach (ArchPier side in L52Ways)
                        {
                            var (du, dv) = L52Step(side);
                            int ru = u - du, rv = v - dv, ou = u + du, ov = v + dv;
                            if (!InB(ru, rv) || !InB(ou, ov) || c.RoomOf[ru + rv * c.W] != room.Id || !Is(ru, rv, L52Zone.Room)) continue;
                            int other = c.RoomOf[ou + ov * c.W];
                            if (other < 0 || other == room.Id || !c.Rooms[other].HasDoor || !Is(ou, ov, L52Zone.Room)) continue;
                            ref Tile t = ref c.At(u, v);
                            t.Kind = TileKind.Doorway;
                            t.Zone = (byte)L52Zone.Door;
                            t.Floor = FloorKind.L52Room;
                            room.DoorSide = side;
                            room.HasDoor = true;
                            break;
                        }
                    }
            }
        // What each room is, and its floor (the same on every storey)
        FloorKind carpet = (FloorKind)((int)FloorKind.L52CarpetBlue + rng.Range(0, 3));
        foreach (L52Room room in mine)
        {
            // (A room that is not a plain rectangle, round a corner of the quad, is left empty: furniture laid out over its
            // bounding box could shut part of it off)
            bool square = room.Area == (room.U1 - room.U0 + 1) * (room.V1 - room.V0 + 1);
            room.Kind = !square ? L52RoomKind.Empty : room.Area < 30 ? L52RoomKind.Closet : b.Kind == L52BuildingKind.Lodging ? L52RoomKind.Lodging : L52RoomKind.Classroom;
            room.Floor = room.Kind == L52RoomKind.Closet ? FloorKind.L52Lino : rng.Chance(0.55) ? carpet : FloorKind.L52Room;
            for (int v = room.V0; v <= room.V1; v++)
                for (int u = room.U0; u <= room.U1; u++)
                {
                    if (c.RoomOf[u + v * c.W] != room.Id || !Is(u, v, L52Zone.Room)) continue;
                    ref Tile t = ref c.At(u, v);
                    t.Floor = room.Floor;
                    // The ceiling's panels, every four blocks (dark in every room)
                    if (Hashing.Mod(u - room.U0, 4) == 2 && Hashing.Mod(v - room.V0, 4) == 2) t.Ceiling = CeilingKind.LightOff;
                }
        }
        L52AssignRoles(c, b, mine);
        // Lights down the corridors; lockers along the corridor walls, never right beside a door
        bool allLockers = c.Head.Kind == L52CampusKind.MarshallDavid;
        for (int v = b.V0; v <= b.V1; v++)
            for (int u = b.U0; u <= b.U1; u++)
            {
                ref Tile t = ref c.At(u, v);
                if (t.Zone is (byte)L52Zone.Corridor or (byte)L52Zone.Lobby)
                {
                    bool midX = Open(u, v - 1) && Open(u, v + 1) && !Open(u, v - 2) && !Open(u, v + 2);
                    bool midZ = Open(u - 1, v) && Open(u + 1, v) && !Open(u - 2, v) && !Open(u + 2, v);
                    if (midX && midZ || midX && Hashing.Mod(u, 4) == 0 || midZ && Hashing.Mod(v, 4) == 0) t.Ceiling = CeilingKind.LightOn;
                    continue;
                }
                if (t.Zone != (byte)L52Zone.Wall) continue;
                foreach (ArchPier side in L52Ways)
                {
                    var (du, dv) = L52Step(side);
                    if (!Open(u + du, v + dv)) continue;
                    var (au, av) = L52Step(L52LeftOf(side));
                    bool nearDoor = false;
                    for (int k = -2; k <= 2; k++)
                        if (InB(u + au * k, v + av * k) && c.At(u + au * k, v + av * k).Kind == TileKind.Doorway) nearDoor = true;
                    if (nearDoor || !Is(u + au, v + av, L52Zone.Wall) || !Is(u - au, v - av, L52Zone.Wall)) break;
                    bool ns = side is ArchPier.North or ArchPier.South;
                    int run = Hashing.FloorDiv(ns ? u : v, 12);
                    if (!allLockers && Hashing.Unit(Hashing.Hash(seed, run, ns ? v : u, SaltL52Room)) < 0.35) break;
                    t.Under = Unders.L52Locker;
                    t.Pier = side;
                    break;
                }
            }
        L52Windows(c, b);
    }

    /// <summary>The numbered plaque beside a door: on the two corridor tiles to its right as seen from the corridor.</summary>
    private static void L52Plaque(L52Campus c, L52Room room, int du, int dv, ArchPier side)
    {
        // side: the way from the room into the corridor; the plaque faces that way
        var (fu, fv) = L52Step(side);
        var (ru, rv) = L52Step(L52Opposite(L52LeftOf(L52Opposite(side))));
        for (int k = 1; k <= 2; k++)
        {
            int u = du + fu + ru * k, v = dv + fv + rv * k, wu = du + ru * k, wv = dv + rv * k;
            if (!c.InGrid(u, v) || !c.InGrid(wu, wv)) return;
            if (c.At(u, v).Zone is not ((byte)L52Zone.Corridor or (byte)L52Zone.Lobby) || c.At(wu, wv).Kind != TileKind.Wall) return;
        }
        for (int k = 1; k <= 2; k++)
        {
            int u = du + fu + ru * k, v = dv + fv + rv * k;
            ref Tile t = ref c.At(u, v);
            t.Overhead = k == 1 ? Overheads.L52PlaqueLo : Overheads.L52PlaqueHi;
            t.Pier = side;
            c.RoomOf[u + v * c.W] = (short)room.Id;
        }
    }

    private static List<(int U, int V)> L52Flood(L52Campus c, bool[] seen, int u0, int v0, L52Building b)
    {
        var part = new List<(int, int)>();
        var stack = new Stack<(int, int)>();
        stack.Push((u0, v0));
        seen[u0 + v0 * c.W] = true;
        while (stack.Count > 0)
        {
            var (u, v) = stack.Pop();
            part.Add((u, v));
            foreach (ArchPier side in L52Ways)
            {
                var (du, dv) = L52Step(side);
                int nu = u + du, nv = v + dv;
                if (nu < b.U0 || nv < b.V0 || nu > b.U1 || nv > b.V1 || seen[nu + nv * c.W] || c.At(nu, nv).Zone != (byte)L52Zone.Room) continue;
                seen[nu + nv * c.W] = true;
                stack.Push((nu, nv));
            }
        }
        return part;
    }

    /// <summary>Marks the window bays of a building's outside walls: two windows, then a pier, along each wall.</summary>
    private static void L52Windows(L52Campus c, L52Building b)
    {
        for (int v = b.V0; v <= b.V1; v++)
            for (int u = b.U0; u <= b.U1; u++)
            {
                ref Tile t = ref c.At(u, v);
                if (t.Zone != (byte)L52Zone.Ext) continue;
                var (ou, ov) = L52Step(t.Pier);
                int iu = u - ou, iv = v - ov;
                if (!c.InGrid(iu, iv)) continue;
                Tile inside = c.At(iu, iv);
                if (inside.Kind == TileKind.Wall || inside.Zone == (byte)L52Zone.Ext) continue;
                var (au, av) = L52Step(L52LeftOf(t.Pier));
                if (!c.InGrid(u + au, v + av) || !c.InGrid(u - au, v - av)) continue;
                if (c.At(u + au, v + av).Zone is not ((byte)L52Zone.Ext or (byte)L52Zone.Entrance)
                    || c.At(u - au, v - av).Zone is not ((byte)L52Zone.Ext or (byte)L52Zone.Entrance)) continue;
                int along = t.Pier is ArchPier.North or ArchPier.South ? u : v;
                if (b.Windows == 0 && Hashing.Mod(along, 3) == 0 || b.Windows == 2 && Hashing.Mod(along, 2) == 0) continue;
                t.Under = Unders.L52Window;
            }
    }

    /// <summary>A hall standing apart (gym, canteen, warehouse): one room two storeys high, doors in its sides.</summary>
    private void L52LayHall(L52Campus c, int u0, int v0, int u1, int v1, L52BuildingKind kind, bool alongX)
    {
        L52Building b = L52AddBuilding(c, kind, u0, v0, u1, v1, 2);
        L52Footprint(c, b);
        bool changing = kind == L52BuildingKind.Gym && (alongX ? u1 - u0 : v1 - v0) >= 34;
        var room = new L52Room
        {
            Id = c.Rooms.Count, Building = b.Index, U0 = u0 + 1, V0 = v0 + 1, U1 = alongX && changing ? u1 - 10 : u1 - 1, V1 = !alongX && changing ? v1 - 10 : v1 - 1,
            Number = 1, HasDoor = true,
            Kind = kind switch
            {
                L52BuildingKind.Gym => L52RoomKind.Gym, L52BuildingKind.Canteen => L52RoomKind.Canteen, L52BuildingKind.Lecture => L52RoomKind.Lecture,
                _ => L52RoomKind.Warehouse,
            },
            Floor = kind switch
            {
                L52BuildingKind.Gym => FloorKind.L52Gym, L52BuildingKind.Canteen => FloorKind.L52Lino, L52BuildingKind.Lecture => FloorKind.L52CarpetGrey,
                _ => FloorKind.L52Concrete,
            },
            DoorSide = alongX ? ArchPier.North : ArchPier.West,
        };
        room.Area = (room.U1 - room.U0 + 1) * (room.V1 - room.V0 + 1);
        c.Rooms.Add(room);
        for (int v = room.V0; v <= room.V1; v++)
            for (int u = room.U0; u <= room.U1; u++)
            {
                ref Tile t = ref c.At(u, v);
                t.Zone = (byte)L52Zone.Hall;
                t.Floor = room.Floor;
                c.RoomOf[u + v * c.W] = (short)room.Id;
                if (Hashing.Mod(u - room.U0, 5) == 2 && Hashing.Mod(v - room.V0, 5) == 2) t.Ceiling = CeilingKind.LightOn;
            }
        // Double doors in the middle of both long sides, and one in each end
        int mu = (u0 + u1) / 2, mv = (v0 + v1) / 2;
        // (A lecture theatre's doors are at the front, by the board, on both long sides: its seats rise behind)
        if (kind == L52BuildingKind.Lecture) { mu = u0 + 3; mv = v0 + 3; }
        foreach (var (u, v) in kind == L52BuildingKind.Lecture
                     ? alongX ? new[] { (mu, v0), (mu + 1, v0), (mu, v1), (mu + 1, v1) } : new[] { (u0, mv), (u0, mv + 1), (u1, mv), (u1, mv + 1) }
                     : alongX
                     ? new[] { (mu, v0), (mu + 1, v0), (mu, v1), (mu + 1, v1), (u0, mv), (u1, mv) }
                     : new[] { (u0, mv), (u0, mv + 1), (u1, mv), (u1, mv + 1), (mu, v0), (mu, v1) })
        {
            ref Tile t = ref c.At(u, v);
            t.Kind = TileKind.Doorway;
            t.Zone = (byte)L52Zone.Entrance;
        }
        if (changing) L52LayChanging(c, b, u0, v0, u1, v1, alongX);
        if (kind == L52BuildingKind.Lecture) L52LayLecture(c, room, alongX);
        L52Windows(c, b);
        if (kind != L52BuildingKind.Gym) return;
        // The court's lines, two in from the walls and across the middle
        int c0u = room.U0 + 2, c1u = room.U1 - 2, c0v = room.V0 + 2, c1v = room.V1 - 2;
        for (int v = c0v; v <= c1v; v++)
            for (int u = c0u; u <= c1u; u++)
            {
                bool edgeV = v == c0v || v == c1v, edgeU = u == c0u || u == c1u;
                bool half = alongX ? u == (c0u + c1u) / 2 : v == (c0v + c1v) / 2;
                if (edgeV || !alongX && half) c.At(u, v).Floor = FloorKind.L52GymLineWE;
                else if (edgeU || alongX && half) c.At(u, v).Floor = FloorKind.L52GymLineNS;
            }
    }

    /// <summary>The courtyard: artificial grass, paths round it and across it between its doors, benches, lamps, bins and trees; or a sports court.</summary>
    private void L52LayCourtyard(L52Campus c, Rng rng, int u0, int v0, int u1, int v1, bool court, bool doorsNS)
    {
        int mu = (u0 + u1) / 2, mv = (v0 + v1) / 2;
        for (int v = v0; v <= v1; v++)
            for (int u = u0; u <= u1; u++)
            {
                ref Tile t = ref c.At(u, v);
                bool rim = u - u0 < 2 || u1 - u < 2 || v - v0 < 2 || v1 - v < 2;
                bool cross = doorsNS ? Math.Abs(u - mu) <= 1 : Math.Abs(v - mv) <= 1;
                if (rim || cross && !court) { t.Zone = (byte)L52Zone.Path; t.Floor = FloorKind.L52Paving; }
            }
        // The paths also meet the courtyard's doors wherever they are
        for (int v = v0 - 1; v <= v1 + 1; v++)
            for (int u = u0 - 1; u <= u1 + 1; u++)
            {
                if (c.At(u, v).Zone != (byte)L52Zone.Entrance) continue;
                var (du, dv) = L52Step(c.At(u, v).Pier);
                for (int k = 1; k < 80; k++)
                {
                    int pu = u + du * k, pv = v + dv * k;
                    if (pu < u0 || pv < v0 || pu > u1 || pv > v1) break;
                    ref Tile p = ref c.At(pu, pv);
                    if (p.Zone != (byte)L52Zone.Turf) { if (k > 2) break; continue; }
                    p.Zone = (byte)L52Zone.Path;
                    p.Floor = FloorKind.L52Paving;
                }
            }
        if (court)
        {
            // A basketball court with its lines, a hoop at each end, benches along one side
            int hw = Math.Min(13, (u1 - u0) / 2 - 4), hd = Math.Min(8, (v1 - v0) / 2 - 4);
            int cu0 = mu - hw, cu1 = mu + hw, cv0 = mv - hd, cv1 = mv + hd;
            for (int v = cv0 - 1; v <= cv1 + 1; v++)
                for (int u = cu0 - 1; u <= cu1 + 1; u++)
                {
                    ref Tile t = ref c.At(u, v);
                    t.Zone = (byte)L52Zone.Court;
                    t.Variant = 0;
                    bool inside = u >= cu0 && u <= cu1 && v >= cv0 && v <= cv1;
                    t.Floor = inside && (v == cv0 || v == cv1) ? FloorKind.L52CourtLineWE
                        : inside && (u == cu0 || u == cu1 || u == mu) ? FloorKind.L52CourtLineNS : FloorKind.L52Court;
                }
            L52Put(c, cu0, mv, Props.BasketballHoop, ArchPier.East);
            L52Put(c, cu1, mv, Props.BasketballHoop, ArchPier.West);
            // (Round 3) a stand of bleachers along one side, two rows, the back one a block up
            for (int u = cu0 + 2; u <= cu1 - 2; u++)
                for (int row = 0; row < 2; row++)
                {
                    int v = cv0 - 3 - row;
                    if (!c.InGrid(u, v) || c.At(u, v).Zone != (byte)L52Zone.Turf) continue;
                    c.At(u, v).Kind = TileKind.Wall;
                    c.At(u, v).Zone = (byte)L52Zone.Court;
                    c.At(u, v).Variant = 0;
                    if (row > 0) L52Fix(c, u, v, "l52-plinth", 1, 1);
                    L52Fix(c, u, v, "l52-bleacher-south", row + 1, row + 1);
                }
        }
        // Benches facing the cross path, bins beside them, trees in the grass, a lamp at each corner
        for (int v = v0 + 2; v <= v1 - 2; v++)
            for (int u = u0 + 2; u <= u1 - 2; u++)
            {
                ref Tile t = ref c.At(u, v);
                if (t.Zone != (byte)L52Zone.Turf || t.Variant != 0) continue;
                bool byCross = !court && (doorsNS ? Math.Abs(u - mu) == 2 : Math.Abs(v - mv) == 2);
                int along = doorsNS ? v : u;
                if (byCross && Hashing.Mod(along, 7) == 3)
                    L52Put(c, u, v, Props.Bench, doorsNS ? (u < mu ? ArchPier.East : ArchPier.West) : (v < mv ? ArchPier.South : ArchPier.North));
                else if (byCross && Hashing.Mod(along, 7) == 5 && rng.Chance(0.5)) L52Put(c, u, v, Props.TrashCan, ArchPier.North);
                else if (!byCross && L52TreeSpot(c, u - u0, v - v0) && rng.Chance(0.75)) t.Variant = Props.Tree;
            }
        foreach (var (u, v) in new[] { (u0 + 2, v0 + 2), (u1 - 2, v0 + 2), (u0 + 2, v1 - 2), (u1 - 2, v1 - 2) })
            if (c.At(u, v).Zone == (byte)L52Zone.Turf) L52Put(c, u, v, Props.Streetlight, ArchPier.North);
    }

    /// <summary>Whether a courtyard tile is where its nine-block square's tree stands: off the square's middle by its own hash (round 3: no visible grid).</summary>
    private bool L52TreeSpot(L52Campus c, int du, int dv)
    {
        int cu = Hashing.FloorDiv(du, 9), cv = Hashing.FloorDiv(dv, 9);
        ulong h = Hashing.Hash(seed, c.Head.X0 + cu, c.Head.Z0 + cv, SaltL52Tree + 7);
        return Hashing.Mod(du, 9) == 2 + (int)(h % 5) && Hashing.Mod(dv, 9) == 2 + (int)(h >> 8 & 3) + (int)(h >> 12 & 1);
    }

    private static void L52Put(L52Campus c, int u, int v, ushort prop, ArchPier facing, byte stack = 0)
    {
        if (!c.InGrid(u, v)) return;
        ref Tile t = ref c.At(u, v);
        if (t.Kind != TileKind.Floor) return;
        t.Variant = prop;
        t.Pier = facing;
        t.Stack = stack;
    }

    /// <summary>
    /// The campus's paths: a paved apron round every building, a path from each outside door until it meets another,
    /// and from each gap in the fence straight in until it meets one.
    /// </summary>
    private static void L52LayPaths(L52Campus c)
    {
        bool Lawn(int u, int v) => c.InGrid(u, v) && c.At(u, v).Zone == (byte)L52Zone.Lawn;
        void Pave(int u, int v)
        {
            if (!Lawn(u, v)) return;
            ref Tile t = ref c.At(u, v);
            t.Zone = (byte)L52Zone.Path;
            t.Floor = FloorKind.L52Paving;
        }
        foreach (L52Building b in c.Buildings)
            for (int v = b.V0 - 2; v <= b.V1 + 2; v++)
                for (int u = b.U0 - 2; u <= b.U1 + 2; u++) Pave(u, v);
        // Out from every outside door, on until it meets a path
        for (int v = 0; v < c.D; v++)
            for (int u = 0; u < c.W; u++)
            {
                Tile t = c.At(u, v);
                if (t.Zone != (byte)L52Zone.Entrance || t.Depth == 0) continue;
                foreach (ArchPier side in L52Ways)
                {
                    var (du, dv) = L52Step(side);
                    if (!c.InGrid(u + du, v + dv) || c.At(u + du, v + dv).Zone != (byte)L52Zone.Path) continue;
                    if (c.At(u - du, v - dv).Zone is (byte)L52Zone.Path or (byte)L52Zone.Lawn) continue; // (a corner: not out)
                    for (int k = 3; k < 160; k++)
                    {
                        int pu = u + du * k, pv = v + dv * k;
                        if (!Lawn(pu, pv)) break;
                        Pave(pu, pv);
                    }
                }
            }
        // Round 3: a walk three wide from each building's nearest outside door to the quad's nearest, so the doors are
        // joined by paths and not only by the lawns (an L: along one way, then the other)
        var doors = new List<(int U, int V, int B)>();
        for (int v = 0; v < c.D; v++)
            for (int u = 0; u < c.W; u++)
            {
                Tile t = c.At(u, v);
                if (t.Zone != (byte)L52Zone.Entrance || t.Depth == 0) continue;
                var (ou, ov) = L52Step(t.Pier);
                if (!c.InGrid(u + ou * 3, v + ov * 3) || c.At(u + ou, v + ov).Depth != 0) continue;
                L52Building q0 = c.Buildings[0];
                if (t.Detail == 1 && u + ou >= q0.U0 && u + ou <= q0.U1 && v + ov >= q0.V0 && v + ov <= q0.V1) continue; // (the courtyard's)
                doors.Add((u + ou * 3, v + ov * 3, t.Detail));
            }
        foreach (L52Building b in c.Buildings)
        {
            if (b.Index == 1) continue;
            (int U, int V)? from = null, to = null;
            int best = int.MaxValue;
            foreach (var d1 in doors)
            {
                if (d1.B != b.Index) continue;
                foreach (var d2 in doors)
                {
                    if (d2.B != 1) continue;
                    int dist = Math.Abs(d1.U - d2.U) + Math.Abs(d1.V - d2.V);
                    if (dist < best) { best = dist; from = (d1.U, d1.V); to = (d2.U, d2.V); }
                }
            }
            if (from is not { } f || to is not { } e) continue;
            for (int u = Math.Min(f.U, e.U); u <= Math.Max(f.U, e.U); u++)
                for (int k = -1; k <= 1; k++) Pave(u, f.V + k);
            for (int v = Math.Min(f.V, e.V); v <= Math.Max(f.V, e.V); v++)
                for (int k = -1; k <= 1; k++) Pave(e.U + k, v);
        }
        for (int s = 0; s < 4; s++)
        {
            int g = c.Head.Gap[s];
            var (du, dv) = L52Step(L52Opposite(L52Ways[s]));
            for (int k = -1; k <= 1; k++)
            {
                int u = s switch { 0 or 2 => g + k, 1 => c.W - 1, _ => 0 }, v = s switch { 1 or 3 => g + k, 0 => 0, _ => c.D - 1 };
                for (int step = 1; step < 200; step++)
                {
                    int pu = u + du * step, pv = v + dv * step;
                    if (!Lawn(pu, pv)) break;
                    Pave(pu, pv);
                }
            }
        }
    }

    /// <summary>The storey a pedestrian bridge runs at (the first floor up).</summary>
    public const int L52BridgeStorey = 1;

    /// <summary>
    /// "A pedestrian bridge" between buildings close together: from the quad to a teaching block or hall of lodgings that
    /// stands 8-24 blocks off it, face to face, a covered glazed walkway three wide at the first floor up, straight across,
    /// opening into whatever lies behind the wall at each end (a corridor or a room; nothing is put in the way there, see
    /// <see cref="L52Furnish"/>). One bridge to a building at most.
    /// </summary>
    private static void L52LayBridges(L52Campus c)
    {
        if (c.Buildings.Count < 2) return;
        L52Building q = c.Buildings[0];
        if (q.Storeys <= L52BridgeStorey) return;
        bool Inside(int u, int v) => c.InGrid(u, v) && c.At(u, v).Kind == TileKind.Floor && c.At(u, v).Depth > 0
            && c.At(u, v).Zone is (byte)L52Zone.Room or (byte)L52Zone.Corridor or (byte)L52Zone.Lobby;
        foreach (L52Building b in c.Buildings)
        {
            if (b == q || b.Kind is not (L52BuildingKind.Teaching or L52BuildingKind.Lodging) || b.Storeys <= L52BridgeStorey) continue;
            // Face to face along u (the block east or west of the quad) or along v (north or south of it)
            for (int axis = 0; axis < 2; axis++)
            {
                bool alongU = axis == 0;
                int lo = alongU ? Math.Max(q.V0, b.V0) + 3 : Math.Max(q.U0, b.U0) + 3, hi = alongU ? Math.Min(q.V1, b.V1) - 3 : Math.Min(q.U1, b.U1) - 3;
                if (hi - lo < 2) continue;
                // (The wall tile on each side, the quad's and the block's, the span between them)
                int qa, ba;
                if (alongU) { if (b.U0 > q.U1) { qa = q.U1; ba = b.U0; } else if (b.U1 < q.U0) { qa = q.U0; ba = b.U1; } else continue; }
                else { if (b.V0 > q.V1) { qa = q.V1; ba = b.V0; } else if (b.V1 < q.V0) { qa = q.V0; ba = b.V1; } else continue; }
                int gap = Math.Abs(ba - qa) - 1, step = Math.Sign(ba - qa);
                if (gap < 8 || gap > 24) continue;
                int mid = (lo + hi) / 2, best = int.MinValue;
                for (int k = 0; k <= hi - lo && best == int.MinValue; k++)
                {
                    int m = mid + (k + 1) / 2 * (k % 2 == 0 ? 1 : -1);
                    if (m - 1 < lo || m + 1 > hi) continue;
                    bool ok = true;
                    for (int w = -1; w <= 1 && ok; w++)
                    {
                        (int U, int V) P(int a) => alongU ? (a, m + w) : (m + w, a);
                        var (qu, qv) = P(qa);
                        var (bu, bv) = P(ba);
                        var (qiu, qiv) = P(qa - step);
                        var (biu, biv) = P(ba + step);
                        ok = c.At(qu, qv).Zone == (byte)L52Zone.Ext && c.At(bu, bv).Zone == (byte)L52Zone.Ext && Inside(qiu, qiv) && Inside(biu, biv);
                        for (int a = qa + step; ok && a != ba; a += step)
                        {
                            var (pu, pv) = P(a);
                            Tile o = c.At(pu, pv);
                            ok = o.Depth == 0 && o.Kind == TileKind.Floor && o.Zone == (byte)L52Zone.Lawn;
                        }
                    }
                    if (ok) best = m;
                }
                if (best == int.MinValue) continue;
                ArchPier runs = alongU ? ArchPier.East : ArchPier.South;
                for (int w = -1; w <= 1; w++)
                    for (int a = qa; ; a += step)
                    {
                        var (u, v) = alongU ? (a, best + w) : (best + w, a);
                        ref Tile t = ref c.At(u, v);
                        if (a == qa || a == ba) t.Overhead = Overheads.L52BridgeDoor;
                        else
                        {
                            t.Overhead = Overheads.L52Bridge;
                            t.Pier = runs;
                            t.Stack = (byte)(w == 0 ? 2 : 1);
                            t.Variant = 0;
                        }
                        if (a == ba) break;
                    }
                break;
            }
        }
    }

    /// <summary>
    /// What makes a way in read as one: a precast surround on the wall either side of every outside door (and a lintel over
    /// it, <see cref="Overheads.L52Frame"/>), and a flat canopy over the paving in front of it at the first floor line
    /// (<see cref="Overheads.L52Canopy"/>), three blocks out and a block wider than the door each side. Nothing stands under it.
    /// </summary>
    private static void L52LayEntrances(L52Campus c)
    {
        for (int v = 0; v < c.D; v++)
            for (int u = 0; u < c.W; u++)
            {
                Tile e = c.At(u, v);
                if (e.Zone != (byte)L52Zone.Entrance || e.Depth == 0) continue;
                var (ou, ov) = L52Step(e.Pier);
                // (Only a door in an outside wall: outdoors in front of it)
                if (!c.InGrid(u + ou, v + ov) || c.At(u + ou, v + ov).Depth != 0) continue;
                var (au, av) = L52Step(L52LeftOf(e.Pier));
                for (int k = -1; k <= 1; k += 2)
                {
                    int fu = u + au * k, fv = v + av * k;
                    if (c.InGrid(fu, fv) && c.At(fu, fv).Zone == (byte)L52Zone.Ext && c.At(fu, fv).Overhead == 0) c.At(fu, fv).Overhead = Overheads.L52Frame;
                }
                for (int d = 1; d <= 3; d++)
                    for (int l = -1; l <= 1; l++)
                    {
                        int pu = u + ou * d + au * l, pv = v + ov * d + av * l;
                        if (!c.InGrid(pu, pv)) continue;
                        ref Tile t = ref c.At(pu, pv);
                        if (t.Depth != 0 || t.Kind != TileKind.Floor || t.Overhead != 0) continue;
                        t.Overhead = Overheads.L52Canopy;
                        t.Variant = 0;
                        t.Stack = 0;
                    }
            }
    }

    /// <summary>The lawns: lamps along the paths, a bench or a bin here and there, a few trees.</summary>
    private void L52LayGrounds(L52Campus c)
    {
        for (int v = 3; v < c.D - 3; v++)
            for (int u = 3; u < c.W - 3; u++)
            {
                ref Tile t = ref c.At(u, v);
                if (t.Zone != (byte)L52Zone.Lawn || t.Variant != 0 || t.Overhead != 0 || c.HasFixture[u + v * c.W]) continue;
                bool byPath = false;
                ArchPier toPath = ArchPier.North;
                foreach (ArchPier side in L52Ways)
                {
                    var (du, dv) = L52Step(side);
                    if (c.At(u + du, v + dv).Zone == (byte)L52Zone.Path) { byPath = true; toPath = side; }
                }
                double r = Hashing.Unit(Hashing.Hash(seed, c.Head.X0 + u, c.Head.Z0 + v, SaltL52Room + 1));
                if (byPath)
                {
                    if (Hashing.Mod(u + v, 14) == 0 && r < 0.6) L52Put(c, u, v, Props.Streetlight, toPath);
                    else if (r < 0.02) L52Put(c, u, v, Props.Bench, toPath);
                    else if (r < 0.026) L52Put(c, u, v, Props.TrashCan, toPath);
                    continue;
                }
                bool clear = true;
                for (int dv = -2; dv <= 2 && clear; dv++)
                    for (int du = -2; du <= 2 && clear; du++)
                        if (c.At(u + du, v + dv).Zone != (byte)L52Zone.Lawn || c.At(u + du, v + dv).Overhead != 0 || c.HasFixture[u + du + (v + dv) * c.W]) clear = false;
                if (clear && r > 0.996) t.Variant = Props.Tree;
            }
        // The ground storey's rooms, furnished (the generator asks the same for every storey above)
        foreach (L52Room room in c.Rooms)
            for (int v = room.V0; v <= room.V1; v++)
                for (int u = room.U0; u <= room.U1; u++)
                {
                    if (c.RoomOf[u + v * c.W] != room.Id) continue;
                    ref Tile t = ref c.At(u, v);
                    if (t.Zone is not ((byte)L52Zone.Room or (byte)L52Zone.Hall)) continue;
                    ushort prop = L52Furnish(c, room, 0, u, v, out ArchPier facing, out byte stack, out bool box);
                    if (box) t.SupplyBox = true;
                    if (prop == 0) continue;
                    t.Variant = prop;
                    t.Pier = facing;
                    t.Stack = stack;
                }
        for (int v = 1; v < c.D - 1; v++)
            for (int u = 1; u < c.W - 1; u++)
            {
                ushort prop = L52CorridorThing(c, u, v, 0, out ArchPier facing);
                if (prop == 0) continue;
                ref Tile t = ref c.At(u, v);
                t.Variant = prop;
                t.Pier = facing;
            }
    }

    // ================= What is in a room, storey by storey =================

    /// <summary>
    /// What a room is on a given storey: classrooms mostly; offices, labs, a library, store rooms, stripped rooms; the
    /// M.E.G.'s old offices on Marshall David's top floor; lodgings at J. Turner.
    /// </summary>
    public L52RoomKind L52KindOn(L52Campus c, L52Room room, int storey)
    {
        if (storey == 0 && room.GroundKind is { } ground) return ground;
        if (room.Kind is not (L52RoomKind.Classroom or L52RoomKind.Lodging)) return room.Kind;
        L52Building b = c.Buildings[room.Building - 1];
        if (c.Head.Kind == L52CampusKind.MarshallDavid && storey == b.Storeys - 1 && b.Index == 1) return L52RoomKind.Meg;
        double r = Hashing.Unit(Hashing.Hash(seed, c.Head.X0 + room.U0 * 7 + storey, c.Head.Z0 + room.V0, SaltL52Storey));
        if (room.Kind == L52RoomKind.Lodging) return r < 0.85 ? L52RoomKind.Lodging : L52RoomKind.Empty;
        if (c.Head.Kind == L52CampusKind.JTurner && r < 0.45) return L52RoomKind.Lodging;
        if (room.Area < 45) return r < 0.5 ? L52RoomKind.Office : r < 0.8 ? L52RoomKind.Store : L52RoomKind.Empty;
        // (A floor of labs in a building of three storeys or more)
        if (storey == L52LabStorey(b) && b.Kind == L52BuildingKind.Teaching && r < 0.6) return L52RoomKind.Lab;
        return r < 0.70 ? L52RoomKind.Classroom : r < 0.78 ? L52RoomKind.Lab : r < 0.83 ? L52RoomKind.Library : r < 0.89 ? L52RoomKind.Office
            : r < 0.94 ? L52RoomKind.Empty : L52RoomKind.Store;
    }

    /// <summary>
    /// What stands on a tile of a room on a storey (the same arithmetic for every storey: the ground storey's goes into
    /// the plan, the generator asks for the rest): a prop, the way it faces and its part; <paramref name="box"/> a supply box.
    /// </summary>
    public ushort L52Furnish(L52Campus c, L52Room room, int storey, int u, int v, out ArchPier facing, out byte stack, out bool box)
    {
        facing = ArchPier.North;
        stack = 0;
        box = false;
        L52RoomKind kind = L52KindOn(c, room, storey);
        // Never in a doorway's way: nothing on a tile beside a door (nor, on its storey, within two of a bridge's opening)
        foreach (ArchPier side in L52Ways)
        {
            var (du, dv) = L52Step(side);
            int nu = u + du, nv = v + dv;
            if (c.InGrid(nu, nv) && c.At(nu, nv).Kind == TileKind.Doorway) return 0;
            if (storey == L52BridgeStorey)
                for (int k = 1; k <= 2; k++)
                    if (c.InGrid(u + du * k, v + dv * k) && c.At(u + du * k, v + dv * k).Overhead == Overheads.L52BridgeDoor) return 0;
        }
        // The room's frame: d the depth from the door's wall (0 next to it), a along it
        bool alongX = room.DoorSide is ArchPier.North or ArchPier.South;
        int la = alongX ? room.U1 - room.U0 + 1 : room.V1 - room.V0 + 1, ld = alongX ? room.V1 - room.V0 + 1 : room.U1 - room.U0 + 1;
        int a = alongX ? u - room.U0 : v - room.V0;
        int d = room.DoorSide switch
        {
            ArchPier.North => v - room.V0, ArchPier.South => room.V1 - v, ArchPier.West => u - room.U0, _ => room.U1 - u,
        };
        ArchPier intoRoom = L52Opposite(room.DoorSide), toLowA = alongX ? ArchPier.West : ArchPier.North, toHighA = L52Opposite(toLowA);
        ulong h = Hashing.Hash(seed, c.Head.X0 + room.U0 + storey * 131, c.Head.Z0 + room.V0, SaltL52Room);
        double rr = Hashing.Unit(Hashing.Hash(seed, c.Head.X0 + u + storey * 977, c.Head.Z0 + v, SaltL52Room + 2));
        switch (kind)
        {
            case L52RoomKind.Classroom:
            {
                // The board on one end wall, the desks in rows facing it, the teacher's desk by the windows, a television in the corner
                bool boardLow = (h & 1) == 0;
                int boardA = boardLow ? 0 : la - 1, dEnd = Math.Min(ld - 2, 6);
                ArchPier toBoard = boardLow ? toLowA : toHighA;
                if (a == boardA && d >= 1 && d <= dEnd)
                {
                    facing = L52Opposite(toBoard);
                    // Its ends, left and right as seen from in front
                    var (lu, lv) = L52Step(L52LeftOf(toBoard));
                    var (eu, ev) = L52Step(intoRoom);
                    bool leftIsDeeper = lu == eu && lv == ev;
                    int left = leftIsDeeper ? dEnd : 1, right = leftIsDeeper ? 1 : dEnd;
                    stack = (byte)(d == left ? 0 : d == right ? 2 : 1);
                    return Props.L52Chalkboard;
                }
                int fromBoard = boardLow ? a : la - 1 - a;
                if (fromBoard == 1 && d == ld - 1) { facing = L52Opposite(toBoard); return Props.Desk; }
                if (fromBoard == 0 && d == ld - 1 && (h >> 3 & 3) != 0) { facing = L52Opposite(toBoard); return Props.Tv; }
                if (fromBoard >= 3 && fromBoard % 2 == 1 && fromBoard <= la - 2 && d >= 1 && d <= ld - 2 && d % 2 == 1 && rr < 0.94)
                {
                    facing = toBoard;
                    return Props.L52Desk;
                }
                if (fromBoard == la - 1 && d == ld - 1 && (h >> 5 & 1) == 0) return Props.Wastebasket;
                if (fromBoard == la - 1 && d >= 2 && d <= ld - 3 && (h >> 6 & 7) == 0) return Props.ChairStack;
                return 0;
            }
            case L52RoomKind.Office:
                if (d == ld / 2 && a == la / 2) { facing = room.DoorSide; return Props.Desk; }
                if (d == ld / 2 + 1 && a == la / 2) { facing = room.DoorSide; return Props.OfficeChair; }
                if (d == ld - 1 && (a == 0 || a == la - 1)) { facing = room.DoorSide; return Props.FilingCabinet; }
                if (d == ld - 1 && a == 1 && (h >> 4 & 1) == 0) { facing = room.DoorSide; return Props.Shelf; }
                return 0;
            case L52RoomKind.Meg:
                if (d == ld - 1 && a % 3 == 1) { facing = room.DoorSide; return Props.Desk; }
                if (d == ld - 2 && a % 3 == 1) { facing = room.DoorSide; return Props.OfficeChair; }
                if (d >= 2 && (a == 0 || a == la - 1) && d % 2 == 0) { facing = a == 0 ? toHighA : toLowA; return Props.FilingCabinet; }
                if (d == 1 && a == la / 2 && (h >> 2 & 1) == 0) return Props.TrashBags;
                if (d == 2 && a == la / 2 - 1 && (h >> 3 & 1) == 0) return Props.CardboardBoxes;
                if (d == 1 && a == 1 && (h >> 4 & 3) == 0) { facing = intoRoom; return Props.MegMarker; }
                return 0;
            case L52RoomKind.Lab:
                // Benches along both long walls (a sink now and then), fume hoods on the far one, islands down the middle
                if (d == ld - 1 && a >= 1 && a <= la - 2 && a % 4 == 2) { facing = room.DoorSide; return Props.L52FumeHood; }
                if ((d == 1 || d == ld - 1) && a >= 1 && a <= la - 2) { facing = d == 1 ? intoRoom : room.DoorSide; stack = (byte)(a % 5 == 3 ? 1 : 0); return Props.KitchenCounter; }
                if (d == ld / 2 && ld >= 6 && a >= 2 && a <= la - 3 && a % 4 != 0) return Props.FoldingTable;
                return 0;
            case L52RoomKind.Library:
            {
                // The stacks on one side, reading tables with chairs on the other, the issue desk by the door
                int split = la * 3 / 5;
                if (d == 1 && a == la - 2) { facing = room.DoorSide; return Props.ReceptionDesk; }
                if (a < split && d >= 2 && d <= ld - 1 && a % 3 == 1) { facing = toLowA; return Props.OfficeBookshelf; }
                if (a > split && a <= la - 2 && d >= 3 && d <= ld - 2)
                {
                    int row = (d - 3) % 3;
                    if (row == 1) return Props.ConferenceTable;
                    if (row == 0) { facing = intoRoom; return Props.CafeChair; }
                    if (d + 1 <= ld - 2 || row == 2) { facing = room.DoorSide; return Props.CafeChair; }
                }
                return 0;
            }
            case L52RoomKind.RestroomMen:
            case L52RoomKind.RestroomWomen:
                // Stalls along the far wall facing the door, basins along one end wall under the mirrors
                if (d == ld - 1 && a >= 1 && a <= la - 2) { facing = room.DoorSide; return Props.L52Stall; }
                if (a == 0 && d >= 1 && d <= ld - 3) { facing = toHighA; stack = 1; return Props.KitchenCounter; }
                if (a == la - 1 && d == 1 && (h >> 3 & 1) == 0) return Props.Wastebasket;
                return 0;
            case L52RoomKind.Reception:
                // The front office: a counter across the room, the staff's chairs, cabinets and the copier behind; chairs to wait on
                if (d == 2 && a >= 1 && a <= la - 2) { facing = room.DoorSide; return Props.ReceptionDesk; }
                if (d == 3 && a % 3 == 1 && a <= la - 2) { facing = room.DoorSide; return Props.OfficeChair; }
                if (d == ld - 1 && d > 4 && a >= 1 && a <= la - 2) { facing = room.DoorSide; return a % 4 == 2 ? Props.Copier : Props.FilingCabinet; }
                if (d == 0 && (a == 0 || a == la - 1)) { facing = intoRoom; return Props.Ficus; }
                if (d == 0 && (a == 2 || a == la - 3) && la >= 7) { facing = intoRoom; return Props.HotelChair; }
                return 0;
            case L52RoomKind.StaffRoom:
            {
                // A kitchenette on the far wall, a sofa either side of a coffee table, a table with chairs
                if (d == ld - 1 && a == 0) { facing = room.DoorSide; return Props.Fridge; }
                if (d == ld - 1 && a >= 1 && a <= Math.Min(la - 2, 4)) { facing = room.DoorSide; stack = (byte)(a == 2 ? 1 : a == 3 ? 2 : 0); return Props.KitchenCounter; }
                int sm = la - 3, md = ld / 2;
                if (a == sm && d == md) return Props.CoffeeTable;
                if (a == sm && d == md - 1 && d >= 1) { facing = intoRoom; return Props.Sofa; }
                if (a == sm && d == md + 1 && d <= ld - 2) { facing = room.DoorSide; return Props.Sofa; }
                if (a == 2 && d == md && la >= 7) return Props.RoundTable;
                if ((a == 1 || a == 3) && d == md && la >= 7) { facing = a == 1 ? toHighA : toLowA; return Props.CafeChair; }
                if (a == la - 1 && d == 1) return Props.Ficus;
                return 0;
            }
            case L52RoomKind.Changing:
                if (d == ld / 2 && a >= 1 && a <= la - 2) { facing = intoRoom; return Props.Bench; }
                return 0;
            case L52RoomKind.Store:
            case L52RoomKind.Closet:
                if ((a == 0 || a == la - 1) && d >= 1) { facing = a == 0 ? toHighA : toLowA; return rr < 0.75 ? Props.Shelf : (ushort)0; }
                if (d == ld - 1 && a == la / 2 && (h >> 7 & 3) == 0) { box = true; return 0; }
                if (d == ld - 2 && a == la / 2 - 1 && (h >> 9 & 1) == 0) return Props.CardboardBoxes;
                return 0;
            case L52RoomKind.Lodging:
                // Beds against the far wall, head to it, a nightstand between, a wardrobe by the door
                if (d == ld - 1 && a % 3 == 1 && a <= la - 2) { facing = room.DoorSide; stack = 0; return Props.Bed; }
                if (d == ld - 2 && a % 3 == 1 && a <= la - 2) { facing = room.DoorSide; stack = 1; return Props.Bed; }
                if (d == ld - 1 && a % 3 == 2 && a <= la - 2) { facing = room.DoorSide; return Props.Nightstand; }
                if (d == 1 && a == 0) { facing = toHighA; return Props.Wardrobe; }
                return 0;
            case L52RoomKind.Empty:
                if (d == ld / 2 && a == la / 2 && (h >> 4 & 1) == 0) { facing = toLowA; return Props.L52Desk; }
                return 0;
            case L52RoomKind.Gym:
            {
                // (A hall's door side is its first long side: d across the hall, a along it)
                bool across = d == ld / 2;
                if (across && a == 0) { facing = toHighA; return Props.BasketballHoop; }
                if (across && a == la - 1) { facing = toLowA; return Props.BasketballHoop; }
                if (d == 0 && a >= 4 && a <= la - 5 && a % 7 != 0) { facing = intoRoom; return Props.Bench; }
                // A stand of bleachers along the far wall, two rows
                if (d == ld - 2 && a >= 4 && a <= la - 5) { facing = room.DoorSide; stack = 0; return Props.L52Bleacher; }
                if (d == ld - 1 && a >= 4 && a <= la - 5) { facing = room.DoorSide; stack = 1; return Props.L52Bleacher; }
                return 0;
            }
            case L52RoomKind.Canteen:
            {
                // The empty food stands along the far wall; vending machines, a cooler and a fountain along the near one; long tables
                if (d == ld - 1 && a >= 3 && a <= la - 4) { facing = room.DoorSide; stack = (byte)(a % 5 == 0 ? 1 : 0); return Props.SnackCounter; }
                if (d == 0 && a >= 2 && a <= la - 3 && a % 4 == 1) { facing = intoRoom; return a % 8 == 1 ? Props.Vending : Props.SnackVending; }
                if (d == 0 && a == la - 2) { facing = intoRoom; return Props.Cooler; }
                if (d == 0 && a == 1) { facing = intoRoom; return Props.L52Fountain; }
                if (d >= 3 && d <= ld - 4 && a >= 3 && a <= la - 4 && a % 9 != 0)
                {
                    int row = (d - 3) % 4;
                    if (row == 1) return Props.FoldingTable;
                    if (row == 0 && a % 2 == 0) { facing = intoRoom; return Props.FoldingChair; }
                    if (row == 2 && a % 2 == 0) { facing = room.DoorSide; return Props.FoldingChair; }
                }
                return 0;
            }
            case L52RoomKind.Warehouse:
            {
                // Rows of shelving, pallets, the medical stores' cabinets, and a few cases nobody has opened
                if (d >= 2 && d <= ld - 3 && a >= 2 && a <= la - 3 && a % 4 == 2) { facing = toLowA; return d % 6 == 0 ? (ushort)0 : Props.Shelf; }
                if (d == ld - 1 && a % 3 == 0) { facing = room.DoorSide; return rr < 0.5 ? Props.MedCabinet : Props.Pallet; }
                if (a % 4 == 0 && d >= 3 && d <= ld - 3 && rr < 0.1) { box = true; return 0; }
                if (a % 4 == 0 && d >= 3 && d <= ld - 3 && rr < 0.25) return Props.CardboardBoxes;
                return 0;
            }
        }
        return 0;
    }

    /// <summary>A corridor tile's furnishing on a storey: now and then a drinking fountain, a vending machine, a water cooler or a bin against the wall.</summary>
    public ushort L52CorridorThing(L52Campus c, int u, int v, int storey, out ArchPier facing)
    {
        facing = ArchPier.North;
        Tile t = c.At(u, v);
        if (t.Overhead != 0 || t.Zone != (byte)L52Zone.Corridor || c.HasFixture[u + v * c.W]) return 0;
        ArchPier? wall = null;
        foreach (ArchPier side in L52Ways)
        {
            var (du, dv) = L52Step(side);
            if (!c.InGrid(u + du, v + dv)) return 0;
            Tile n = c.At(u + du, v + dv);
            if (n.Kind == TileKind.Doorway) return 0;
            if (n.Zone == (byte)L52Zone.Wall && n.Under == 0) wall = side;
        }
        if (wall is not { } w) return 0;
        var (au, av) = L52Step(L52LeftOf(w));
        var (wu, wv) = L52Step(w);
        // (both neighbours along the wall are corridor with wall behind: never at a corner or a crossing)
        for (int k = -1; k <= 1; k += 2)
        {
            int nu = u + au * k, nv = v + av * k;
            if (!c.InGrid(nu + wu, nv + wv) || c.At(nu, nv).Zone != (byte)L52Zone.Corridor || c.At(nu + wu, nv + wv).Kind != TileKind.Wall) return 0;
        }
        double r = Hashing.Unit(Hashing.Hash(seed, c.Head.X0 + u + storey * 4111, c.Head.Z0 + v, SaltL52Room + 3));
        facing = L52Opposite(w);
        // (Marshall David is worn now, as the lore has it: rubbish left along its corridors)
        if (c.Head.Kind == L52CampusKind.MarshallDavid && r >= 0.07 && r < 0.11) return r < 0.09 ? Props.TrashBags : Props.CardboardBoxes;
        return r < 0.035 ? Props.L52Fountain : r < 0.05 ? Props.Vending : r < 0.06 ? Props.Cooler : r < 0.07 ? Props.TrashCan : (ushort)0;
    }

    /// <summary>Which of the level's props (<see cref="Props.L52First"/>-<see cref="Props.L52Last"/>) people walk through: the chalkboards (they hang on the wall).</summary>
    private static bool L52WalkThrough(ushort variant) => variant == Props.L52Chalkboard;

    // ================= Air =================

    /// <summary>
    /// The hour (in game hours) the level's weather is worked out for: set every few seconds by Regions.L52System, on the
    /// server and on the client, from the world's calendar.
    /// </summary>
    public static double L52Hours;

    /// <summary>How warm it is outdoors at an hour: between 10 and 32 °C, drifting over hours, now and then turning sharply.</summary>
    public static float L52OutdoorTemperature(double hours)
    {
        double w = Math.Sin(hours * 0.31) * 0.55 + Math.Sin(hours * 0.113 + 1.7) * 0.35 + Math.Sin(hours * 1.37 + 0.4) * 0.1;
        return (float)(21 + 11 * Math.Clamp(w, -1, 1));
    }

    /// <summary>The temperature: the drifting weather outdoors; indoors much nearer a mild 21 °C.</summary>
    private float L52Temperature(int x, int y, int z, int floorY)
    {
        float outside = L52OutdoorTemperature(L52Hours);
        L52Campus c = L52CampusAt(x, z, out int i);
        if (c == null) return outside;
        Tile t = c.Grid[i];
        bool indoors = t.Depth > 0 && y - floorY < t.Depth * L52Storey + 1;
        return indoors ? 21 + 0.3f * (outside - 21) : outside;
    }

    /// <summary>Reality stability: a little steadier than neutral everywhere; the lore calls the place "a paradise of sorts".</summary>
    private float L52Stability(double x, double y, double z, int floorY, float drift) => 1.1f;
}
