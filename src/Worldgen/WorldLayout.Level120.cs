using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 120, "Broken Servos" (experimental): kept as level 26 (<see cref="Level120"/>) and shown as "120". Broken server
/// rooms in the dark, in a round noclip region far out to the north-east, beyond Level Fun (after Wikidot's Level 120;
/// the design is docs/design/experimental-levels/120-plan.md). No thresholds in or out: the cheats menu or
/// <c>/backrooms goto 120</c> only.
///
/// <para><b>The lattice.</b> Passages run straight through the whole region every <see cref="L120Period"/> blocks each
/// way, four wide (x or z mod 96 in 1-4), dirty yellow walls, a duct along one side and dead lights; one crossing in four
/// keeps a working tube. Between four passages lies a <b>hall</b>, 90 blocks square (mod 96 in 6-95, its walls at 5 and
/// 96), laid out once from its own hash (<see cref="L120PlanOf"/>, kept in a <see cref="PlanCache{T}"/>).</para>
///
/// <para><b>Clusters</b> (the lore's "clusters of 15-23"): nearly every hall is cut into 15 to 23 server rooms by a
/// split of its square, doors between neighbouring rooms (always every room reached, now and then a loop), one or two
/// doors onto each passage. Server rooms hold banks of racks, many of them ripped apart (gutted, toppled, torn open,
/// pulled out onto the floor); some rooms are rack aisles, terminal rooms, wrecked stores or cable rooms. Dirty white
/// floors, yellow paper on rotting boards, office ceiling tiles with smashed or dead fittings: it is pitch dark but for
/// a rack's LEDs here and there. Now and then one terminal is still whole (<see cref="L120TermBoot"/>): booting it is
/// how the pockets are reached.</para>
///
/// <para><b>Pockets</b> (reached only by booting a terminal, never by walking): a <b>White Void</b> (6-12 white rooms of 11
/// square on a grid, lit from their ceilings, black doors between them, a broken window in every outside wall) or a
/// <b>Pitch-Black Hallway</b> (two wide, hundreds of blocks long, folded back and forth, unlit, a broken window at each
/// end). The windows lead back to the terminal that brought you (L120System). Pocket halls lie wholly inside the region
/// and have no doors.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2600-0x26BF are this level's (0x26C0-0x26FF its thresholds').</summary>
    private const ulong SaltL120Shape = 0x2601, SaltL120Hall = 0x2610, SaltL120Light = 0x2611, SaltL120Corridor = 0x2612;
    private const ulong SaltL120Kind = 0x2613;

    /// <summary>The lattice: a passage every 96 blocks each way; a hall's inside is 90 square, its plan 92 with its walls.</summary>
    public const int L120Period = 96, L120HallSize = 90, L120Grid = 92;

    /// <summary>What part of the level a tile is in (kept in <see cref="Tile.Zone"/>).</summary>
    public enum L120Zone : byte { None, Corridor, Room, Hot, Terminals, Wreck, Wall, Void, VoidWall, Hallway, HallWall, Fill }

    public enum L120HallKind : byte { Cluster, Void, Hallway }

    public enum L120RoomKind : byte { Servers, Aisles, Terminals, Wreck, Cables }

    /// <summary>
    /// The level's props: a server rack (two blocks high), a terminal on its desk, an office chair, a wreck (a rack toppled
    /// or torn open), a broken window (walk into it), a black door (a White Void's), cables spilled over the floor (walked over).
    /// </summary>
    public const ushort L120Rack = Props.L120First, L120Terminal = Props.L120First + 1, L120Chair = Props.L120First + 2,
        L120Wreck = Props.L120First + 3, L120Window = Props.L120First + 4, L120VoidDoor = Props.L120First + 5, L120Spill = Props.L120First + 6;

    /// <summary>A rack's LEDs (<see cref="Tile.Detail"/>): dark, bank A on (green), bank B (amber), both (green and blue); or gutted.</summary>
    public const byte L120RackOff = 0, L120RackLedA = 1, L120RackLedB = 2, L120RackBoth = 3, L120RackGutted = 4;

    /// <summary>A terminal (<see cref="Tile.Detail"/>): dead, still whole (it boots), its screen smashed.</summary>
    public const byte L120TermDead = 0, L120TermBoot = 1, L120TermSmashed = 2;

    /// <summary>A wreck (<see cref="Tile.Detail"/>): a rack toppled onto its back, one torn open with its insides spilling out.</summary>
    public const byte L120WreckToppled = 0, L120WreckTorn = 1;

    /// <summary>The floor (<see cref="Tile.Depth"/>): clean, grimy, a perforated raised-floor panel, a panel lifted out.</summary>
    public const byte L120PanelClean = 0, L120PanelDirty = 1, L120PanelVent = 2, L120PanelHole = 3;

    /// <summary>A cable tray under the ceiling (<see cref="Tile.Overhead"/>): along x or z.</summary>
    public const byte L120TrayX = Overheads.L120LegacyFirst, L120TrayZ = Overheads.L120LegacyFirst + 1;

    /// <summary>A duct along the top of a passage (<see cref="Tile.Pipe"/>): along x, along z, where two meet.</summary>
    public const byte L120DuctX = Pipes.L120LegacyFirst, L120DuctZ = Pipes.L120LegacyFirst + 1, L120DuctHub = Pipes.L120LegacyFirst + 2;

    /// <summary>A dim fitting that still gives a little warm light, and a smashed one.</summary>
    public const CeilingKind L120Dim = CeilingKind.L120Dim, L120SmashedLamp = CeilingKind.L120Smashed;

    /// <summary>The plan of one hall, in its own coordinates (P east, Q south), -1..90 each way (the walls round it included).</summary>
    public sealed class L120Plan
    {
        public int Hx, Hz;
        public L120HallKind Kind;
        public int Rooms, Racks, Lit, Wrecked, Terminals, Windows, Boxes;
        /// <summary>Where a whole terminal stands, and the tile in front of it (world blocks).</summary>
        public readonly List<(int X, int Z, int FrontX, int FrontZ)> Boots = new();
        /// <summary>A pocket's arrival tile (world blocks).</summary>
        public (int X, int Z) Arrival;
        public readonly Tile[] Tiles = new Tile[L120Grid * L120Grid];

        public ref Tile At(int p, int q) => ref Tiles[p + 1 + (q + 1) * L120Grid];
        /// <summary>The block position of a place in the plan.</summary>
        public (int X, int Z) World(int p, int q) => (Hx * L120Period + 6 + p, Hz * L120Period + 6 + q);
    }

    private PlanCache<L120Plan> l120Plans;

    /// <summary>A hall's plan (shared: read it, never change it).</summary>
    public L120Plan L120PlanOf(int hx, int hz) =>
        LazyInitializer.EnsureInitialized(ref l120Plans, () => new PlanCache<L120Plan>(32, MakeL120Plan)).Get(hx, hz);

    /// <summary>The hall a block lies in (its passages count with the hall to their south-east).</summary>
    public static (int Hx, int Hz) L120HallOf(int x, int z) => (Hashing.FloorDiv(x - 5, L120Period), Hashing.FloorDiv(z - 5, L120Period));

    // ================= Where it is =================

    /// <summary>
    /// How far out along the north-east diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond Level Fun, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L120Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    public int L120CentreX => spawnMacroX + L120Reach;
    public int L120CentreZ => spawnMacroZ - L120Reach;

    /// <summary>The region's radius in macro cells.</summary>
    public int L120Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL120(double mx, double mz) => InRoundRegion(mx, mz, L120CentreX, L120CentreZ, L120Radius, SaltL120Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L120ArrivalCell(ulong h) => RoundArrivalCell(h, L120CentreX, L120CentreZ, L120Radius);

    /// <summary>Arriving: in a passage or a server room, never in a hot aisle or a pocket (those are reached by booting a terminal).</summary>
    private static bool IsL120ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone is (byte)L120Zone.Corridor or (byte)L120Zone.Room;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L120ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the passages and halls are laid over the edges).</summary>
    private Edge L120Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L120Wall };

    /// <summary>
    /// Lays out one of the level's cells: the passages from arithmetic, the rest copied from the plans of the halls it
    /// covers; where the region ends, a hallway runs round inside its wall (<see cref="CarveEdgeHall"/>) so nothing it cuts
    /// through is left shut off.
    /// </summary>
    private void BuildLevel120(Builder b, int mx, int mz)
    {
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                int u = Hashing.Mod(gx, L120Period), v = Hashing.Mod(gz, L120Period);
                bool alongZ = u is >= 1 and <= 4, alongX = v is >= 1 and <= 4;
                if (alongZ || alongX)
                {
                    L120CorridorTile(ref t, gx, gz, u, v, alongZ, alongX);
                    continue;
                }
                int hx = Hashing.FloorDiv(gx, L120Period) - (u == 0 ? 1 : 0), hz = Hashing.FloorDiv(gz, L120Period) - (v == 0 ? 1 : 0);
                int a = u == 0 ? L120HallSize : u - 6, bb = v == 0 ? L120HallSize : v - 6;
                t = L120PlanOf(hx, hz).At(a, bb);
            }
        if (WalledNeighbours(Level120, mx, mz) != null) CarveEdgeHall(b, mx, mz, GetEdge(mx, mz, west: true), GetEdge(mx, mz, west: false));
    }

    /// <summary>A fitting in the dark, by hash: dead or smashed nearly always (the lore's "smashed or inactive"), now and then failing, very rarely dim.</summary>
    private CeilingKind L120Lamp(int gx, int gz, double flicker = 0.03, double dim = 0.02)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL120Light));
        if (r < flicker) return CeilingKind.LightFlicker;
        if (r < flicker + dim) return L120Dim;
        return r < 0.55 ? CeilingKind.LightOff : L120SmashedLamp;
    }

    /// <summary>A tile of a passage (along z where x mod 96 is 1-4, along x where z mod 96 is), or of a crossing.</summary>
    private void L120CorridorTile(ref Tile t, int gx, int gz, int u, int v, bool alongZ, bool alongX)
    {
        t.Kind = TileKind.Floor;
        t.Floor = FloorKind.L120Floor;
        t.Ceiling = CeilingKind.L120Ceiling;
        t.Zone = (byte)L120Zone.Corridor;
        t.Height = 3;
        ulong h = Hashing.Hash(seed, gx, gz, SaltL120Corridor);
        t.Depth = Hashing.Unit(h) < 0.75 ? L120PanelDirty : L120PanelClean;
        if (alongZ && alongX)
        {
            // A crossing: the ducts meet in its north-west corner; one crossing in four keeps a working tube to steer by
            t.Pipe = u == 1 && v == 1 ? L120DuctHub : u == 1 ? L120DuctZ : v == 1 ? L120DuctX : Pipes.None;
            if (u == 3 && v == 3)
            {
                bool kept = Hashing.Mod(Hashing.FloorDiv(gx, L120Period), 2) == 0 && Hashing.Mod(Hashing.FloorDiv(gz, L120Period), 2) == 0;
                t.Ceiling = kept ? CeilingKind.LightOn : L120Lamp(gx, gz, 0.15, 0.1);
            }
            return;
        }
        // The duct along the west (or north) wall; a fitting every six blocks down the middle, all of them dead or broken
        int across = alongZ ? u : v, along = alongZ ? gz : gx;
        t.Pipe = across == 1 ? (alongZ ? L120DuctZ : L120DuctX) : Pipes.None;
        if (across == 3 && Hashing.Mod(along, 6) == 3) t.Ceiling = L120Lamp(gx, gz);
        // Now and then a dead cabinet, a bin, scrap, or cables pulled out across the floor
        double p = Hashing.Unit(Hashing.Mix(h));
        if (across is 1 or 4)
        {
            ArchPier into = alongZ ? (across == 1 ? ArchPier.East : ArchPier.West) : (across == 1 ? ArchPier.South : ArchPier.North);
            if (p < 0.012)
            {
                t.Variant = Props.Cabinet;
                t.Pier = into;
            }
            else if (p < 0.016) t.Variant = Props.TrashCan;
            else if (p < 0.02) t.Variant = Props.ScrapMetal;
        }
        else if (p < 0.012) t.Variant = L120Spill;
    }

    // ================= Halls =================

    /// <summary>Whether a hall and the cells round it are all the level's (a pocket is laid out only then).</summary>
    private bool L120HallInside(int hx, int hz)
    {
        int x0 = MacroOf(hx * L120Period + 5) - 1, x1 = MacroOf(hx * L120Period + L120Period) + 1;
        int z0 = MacroOf(hz * L120Period + 5) - 1, z1 = MacroOf(hz * L120Period + L120Period) + 1;
        for (int mz = z0; mz <= z1; mz++)
            for (int mx = x0; mx <= x1; mx++)
                if (LevelAt(mx, mz) != Level120) return false;
        return true;
    }

    /// <summary>What a hall is, without laying it out: one in seventeen a White Void, one in seventeen a Pitch-Black Hallway (only wholly inside the region), the rest clusters of server rooms.</summary>
    public L120HallKind L120KindOf(int hx, int hz)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, hx, hz, SaltL120Kind));
        L120HallKind kind = r < 0.06 ? L120HallKind.Void : r < 0.12 ? L120HallKind.Hallway : L120HallKind.Cluster;
        return kind != L120HallKind.Cluster && !L120HallInside(hx, hz) ? L120HallKind.Cluster : kind;
    }

    /// <summary>The nearest pocket hall of a kind to a hall, within <paramref name="reach"/> halls; null if none.</summary>
    public (int Hx, int Hz)? L120NearestPocket(int hx, int hz, L120HallKind kind, int reach = 8)
    {
        for (int r = 1; r <= reach; r++)
        {
            (int, int)? best = null;
            ulong bestKey = ulong.MaxValue;
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || L120KindOf(hx + dx, hz + dz) != kind) continue;
                    // (Among the halls at the same distance, the pick goes by hash)
                    ulong key = Hashing.Hash(seed, hx * 977 + dx, hz * 977 + dz, SaltL120Kind + 1);
                    if (key < bestKey) { bestKey = key; best = (hx + dx, hz + dz); }
                }
            if (best != null) return best;
        }
        return null;
    }

    private L120Plan MakeL120Plan(int hx, int hz)
    {
        var plan = new L120Plan { Hx = hx, Hz = hz, Kind = L120KindOf(hx, hz) };
        ulong h = Hashing.Hash(seed, hx, hz, SaltL120Hall);
        var rng = new Rng(Hashing.Mix(h));
        bool pocket = plan.Kind != L120HallKind.Cluster;
        for (int i = 0; i < plan.Tiles.Length; i++)
            plan.Tiles[i] = new Tile
            {
                Kind = TileKind.Wall, Pattern = WallPattern.L120Wall, Zone = (byte)(pocket ? L120Zone.Fill : L120Zone.Wall),
                Floor = FloorKind.L120Floor, Ceiling = CeilingKind.L120Ceiling, Height = 3,
            };
        // The ring round a pocket is the passages' wall, as a cluster's
        if (pocket)
            for (int i = -1; i <= L120HallSize; i++)
                plan.At(i, -1).Zone = plan.At(i, L120HallSize).Zone = plan.At(-1, i).Zone = plan.At(L120HallSize, i).Zone = (byte)L120Zone.Wall;
        switch (plan.Kind)
        {
            case L120HallKind.Void: L120LayVoid(plan, ref rng); break;
            case L120HallKind.Hallway: L120LayHallway(plan, ref rng); break;
            default: L120LayCluster(plan, ref rng); break;
        }
        return plan;
    }

    // ================= A cluster of server rooms =================

    private struct L120Room
    {
        public int P0, Q0, P1, Q1;
        public L120RoomKind Kind;
        public readonly int W => P1 - P0 + 1;
        public readonly int H => Q1 - Q0 + 1;
        public L120Room(int p0, int q0, int p1, int q1) { P0 = p0; Q0 = q0; P1 = p1; Q1 = q1; Kind = L120RoomKind.Servers; }
    }

    /// <summary>
    /// Cuts the hall into 15-23 rooms (each cut a wall one thick, no room narrower than 9), joins every room to the others
    /// with doors (a tree of them, and some loops), opens the outer walls onto the passages, then fills the rooms.
    /// </summary>
    private void L120LayCluster(L120Plan plan, ref Rng rng)
    {
        const int n = L120HallSize, min = 9;
        var rooms = new List<L120Room> { new(0, 0, n - 1, n - 1) };
        int want = rng.Range(15, 23);
        while (rooms.Count < want)
        {
            int best = -1, area = 0;
            for (int i = 0; i < rooms.Count; i++)
            {
                L120Room r = rooms[i];
                if ((r.W >= 2 * min + 1 || r.H >= 2 * min + 1) && r.W * r.H > area) { best = i; area = r.W * r.H; }
            }
            if (best < 0) break;
            L120Room c = rooms[best];
            bool cutP = c.W > c.H || c.W == c.H && rng.Chance(0.5);
            if (cutP && c.W < 2 * min + 1) cutP = false;
            if (!cutP && c.H < 2 * min + 1) cutP = true;
            rooms.RemoveAt(best);
            if (cutP)
            {
                int s = rng.Range(c.P0 + min, c.P1 - min);
                rooms.Add(new L120Room(c.P0, c.Q0, s - 1, c.Q1));
                rooms.Add(new L120Room(s + 1, c.Q0, c.P1, c.Q1));
            }
            else
            {
                int s = rng.Range(c.Q0 + min, c.Q1 - min);
                rooms.Add(new L120Room(c.P0, c.Q0, c.P1, s - 1));
                rooms.Add(new L120Room(c.P0, s + 1, c.P1, c.Q1));
            }
        }
        plan.Rooms = rooms.Count;

        // Room kinds: mostly server rooms; the big ones may be rack aisles
        for (int i = 0; i < rooms.Count; i++)
        {
            L120Room r = rooms[i];
            double k = rng.NextDouble();
            r.Kind = k < 0.5 ? L120RoomKind.Servers : k < 0.62 ? (r.W >= 16 && r.H >= 16 ? L120RoomKind.Aisles : L120RoomKind.Servers)
                : k < 0.76 ? L120RoomKind.Terminals : k < 0.88 ? L120RoomKind.Wreck : L120RoomKind.Cables;
            rooms[i] = r;
            L120Zone zone = r.Kind switch { L120RoomKind.Terminals => L120Zone.Terminals, L120RoomKind.Wreck => L120Zone.Wreck, _ => L120Zone.Room };
            for (int q = r.Q0; q <= r.Q1; q++)
                for (int p = r.P0; p <= r.P1; p++)
                {
                    ref Tile t = ref plan.At(p, q);
                    t.Kind = TileKind.Floor;
                    t.Zone = (byte)zone;
                    t.Height = 3;
                    t.Depth = r.Kind == L120RoomKind.Wreck || rng.Chance(0.45) ? L120PanelDirty : L120PanelClean;
                }
        }

        // Doors between rooms: every pair sharing a long enough wall is a candidate; a tree of them joins every room, some of the rest are loops
        var pairs = new List<(int A, int B, bool Vertical, int At, int Lo, int Hi)>();
        for (int a = 0; a < rooms.Count; a++)
            for (int c = 0; c < rooms.Count; c++)
            {
                if (a == c) continue;
                L120Room ra = rooms[a], rc = rooms[c];
                if (ra.P1 + 2 == rc.P0)
                {
                    int lo = Math.Max(ra.Q0, rc.Q0), hi = Math.Min(ra.Q1, rc.Q1);
                    if (hi - lo >= 3) pairs.Add((a, c, true, ra.P1 + 1, lo, hi));
                }
                if (ra.Q1 + 2 == rc.Q0)
                {
                    int lo = Math.Max(ra.P0, rc.P0), hi = Math.Min(ra.P1, rc.P1);
                    if (hi - lo >= 3) pairs.Add((a, c, false, ra.Q1 + 1, lo, hi));
                }
            }
        for (int i = pairs.Count - 1; i > 0; i--)
        {
            int j = rng.Range(0, i);
            (pairs[i], pairs[j]) = (pairs[j], pairs[i]);
        }
        var parent = new int[rooms.Count];
        for (int i = 0; i < parent.Length; i++) parent[i] = i;
        int Root(int x) { while (parent[x] != x) x = parent[x] = parent[parent[x]]; return x; }
        foreach (var (a, c, vertical, at, lo, hi) in pairs)
        {
            int fa = Root(a), fc = Root(c);
            bool tree = fa != fc;
            if (!tree && !rng.Chance(0.3)) continue;
            if (tree) parent[fa] = fc;
            int width = hi - lo >= 6 && rng.Chance(0.5) ? 2 : 1;
            int start = rng.Range(lo + 1, hi - width);
            byte zone = vertical ? plan.At(at - 1, start).Zone : plan.At(start, at - 1).Zone;
            for (int k = 0; k < width; k++)
            {
                ref Tile t = ref vertical ? ref plan.At(at, start + k) : ref plan.At(start + k, at);
                t.Kind = TileKind.Doorway;
                t.Zone = zone;
                t.Height = 3;
            }
        }

        // Doors onto the passages: one near the middle of each side, often another
        for (int side = 0; side < 4; side++)
        {
            int first = -1;
            for (int d = 0; d < 40 && first < 0; d++)
            {
                if (L120Opens(plan, side, 43 + d)) first = 43 + d;
                else if (L120Opens(plan, side, 43 - d)) first = 43 - d;
            }
            var doors = new List<int>();
            if (first >= 0) doors.Add(first);
            if (rng.Chance(0.7))
                for (int tries = 0; tries < 12; tries++)
                {
                    int k = rng.Range(4, n - 7);
                    if (L120Opens(plan, side, k) && (first < 0 || Math.Abs(k - first) >= 15)) { doors.Add(k); break; }
                }
            foreach (int k in doors)
                for (int j = 0; j < 3; j++)
                {
                    ref Tile t = ref plan.At(side == 0 ? -1 : side == 1 ? n : k + j, side < 2 ? k + j : side == 2 ? -1 : n);
                    t.Kind = TileKind.Doorway;
                    t.Zone = (byte)L120Zone.Corridor;
                    t.Height = 3;
                }
        }

        foreach (L120Room r in rooms)
        {
            switch (r.Kind)
            {
                case L120RoomKind.Servers: L120LayServers(plan, r, ref rng); break;
                case L120RoomKind.Aisles: L120LayAisles(plan, r, ref rng); break;
                case L120RoomKind.Terminals: L120LayTerminals(plan, r, ref rng); break;
                case L120RoomKind.Wreck: L120LayWreck(plan, r, ref rng); break;
                default: L120LayCables(plan, r, ref rng); break;
            }
            // Fittings over every room on a five grid: dead or smashed
            for (int q = r.Q0 + 2; q <= r.Q1 - 1; q += 5)
                for (int p = r.P0 + 2; p <= r.P1 - 1; p += 5)
                {
                    var (x, z) = plan.World(p, q);
                    plan.At(p, q).Ceiling = L120Lamp(x, z);
                }
            // Now and then a supply box someone left in a corner (more in the wrecked stores)
            if (rng.Chance(r.Kind == L120RoomKind.Wreck ? 0.45 : 0.22))
            {
                int p = rng.Chance(0.5) ? r.P0 + 1 : r.P1 - 1, q = rng.Chance(0.5) ? r.Q0 + 1 : r.Q1 - 1;
                ref Tile t = ref plan.At(p, q);
                if (t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0) { t.SupplyBox = true; plan.Boxes++; }
            }
        }

        // One terminal in the cluster still works, most of the time
        if (rng.Chance(0.85)) L120PlaceBoot(plan, rooms, ref rng);

        L120FillUnreached(plan);
    }

    /// <summary>Whether three tiles inside a side of the hall, from <paramref name="k"/>, are all room floor (a door onto the passage can open there).</summary>
    private static bool L120Opens(L120Plan plan, int side, int k)
    {
        const int n = L120HallSize;
        if (k < 1 || k + 2 > n - 2) return false;
        for (int j = 0; j < 3; j++)
        {
            Tile t = side switch { 0 => plan.At(0, k + j), 1 => plan.At(n - 1, k + j), 2 => plan.At(k + j, 0), _ => plan.At(k + j, n - 1) };
            if (t.Kind != TileKind.Floor) return false;
        }
        return true;
    }

    /// <summary>The inside of a room, one in from its walls (the walk round its walls stays clear, so every door is reached).</summary>
    private static (int P0, int Q0, int P1, int Q1) L120Inner(L120Room r) => (r.P0 + 1, r.Q0 + 1, r.P1 - 1, r.Q1 - 1);

    /// <summary>
    /// A server room: "massive blocks of computers ripped apart". Banks of racks back to back run along the room's long
    /// side, two-wide aisles between; nearly half the banks are wrecked: racks gutted, toppled, torn open or pulled out
    /// onto the floor, cables spilling into the aisles. One standing rack in sixteen still has its LEDs on.
    /// </summary>
    private static void L120LayServers(L120Plan plan, L120Room r, ref Rng rng)
    {
        var (p0, q0, p1, q1) = L120Inner(r);
        bool alongP = p1 - p0 >= q1 - q0;
        int l0 = alongP ? p0 : q0, l1 = alongP ? p1 : q1, s0 = alongP ? q0 : p0, s1 = alongP ? q1 : p1;
        ArchPier low = alongP ? ArchPier.North : ArchPier.West, high = alongP ? ArchPier.South : ArchPier.East;
        for (int s = s0; s + 1 <= s1; s += 4)
        {
            for (int l = l0 + rng.Range(0, 1); l <= l1;)
            {
                int len = Math.Min(rng.Range(3, 7), l1 - l + 1);
                if (len < 2) break;
                bool wrecked = rng.Chance(0.45);
                for (int k = l; k < l + len; k++)
                {
                    L120PlaceRack(plan, ref L120Along(plan, alongP, k, s), ref rng, low, wrecked);
                    L120PlaceRack(plan, ref L120Along(plan, alongP, k, s + 1), ref rng, high, wrecked);
                }
                if (wrecked)
                    // The insides of the bank spilled over the aisles either side
                    for (int k = l - 1; k <= l + len; k++)
                        foreach (int side in new[] { s - 1, s + 2 })
                        {
                            if (k < l0 - 1 || k > l1 + 1 || side < s0 - 1 || side > s1 + 1 || !rng.Chance(0.14)) continue;
                            ref Tile t = ref L120Along(plan, alongP, k, side);
                            if (t.Kind == TileKind.Floor && t.Variant == 0) t.Variant = L120Spill;
                        }
                l += len + 2;
            }
        }
        // Lifted panels and vents in the aisles
        for (int q = q0; q <= q1; q++)
            for (int p = p0; p <= p1; p++)
            {
                ref Tile t = ref plan.At(p, q);
                if (t.Variant != 0) continue;
                double v = rng.NextDouble();
                if (v < 0.03) t.Depth = L120PanelHole;
                else if (v < 0.18) t.Depth = L120PanelVent;
            }
    }

    /// <summary>A tile of the plan by a room's own axes: <paramref name="l"/> along its long side, <paramref name="s"/> across it.</summary>
    private static ref Tile L120Along(L120Plan plan, bool alongP, int l, int s) => ref alongP ? ref plan.At(l, s) : ref plan.At(s, l);

    /// <summary>
    /// One rack in a bank, facing its aisle. In a wrecked bank most are ripped apart: gutted, toppled, torn open, or gone
    /// and only its parts or its scrap left; in a standing bank one in eight is gutted.
    /// </summary>
    private static void L120PlaceRack(L120Plan plan, ref Tile t, ref Rng rng, ArchPier face, bool wrecked)
    {
        t.Pier = face;
        double w = rng.NextDouble();
        if (wrecked)
        {
            if (w >= 0.94) { Rack(ref t, L120RackOff); return; }
            plan.Wrecked++;
            if (w < 0.32) Rack(ref t, L120RackGutted);
            else if (w < 0.52) { t.Variant = L120Wreck; t.Detail = L120WreckToppled; }
            else if (w < 0.68) { t.Variant = L120Wreck; t.Detail = L120WreckTorn; }
            else if (w < 0.84) t.Variant = Props.MachineParts;
            else t.Variant = Props.ScrapMetal;
            return;
        }
        if (w < 0.12) { plan.Wrecked++; Rack(ref t, L120RackGutted); return; }
        if (w < 0.16) { plan.Wrecked++; t.Variant = L120Wreck; t.Detail = L120WreckTorn; return; }
        Rack(ref t, rng.Chance(1 / 16.0) ? (byte)rng.Range(L120RackLedA, L120RackBoth) : L120RackOff);

        void Rack(ref Tile r, byte state)
        {
            r.Variant = L120Rack;
            r.Detail = state;
            plan.Racks++;
            if (state is >= L120RackLedA and <= L120RackBoth) plan.Lit++;
        }
    }

    /// <summary>
    /// A rack aisle room (the bigger rooms now and then): rows six apart along the long side, a three-wide cold aisle
    /// with perforated panels and a cable tray between the racks' fronts, a one-wide hot aisle between their backs, the
    /// rows cut every 6-11 racks by a cross-aisle; one bank in four ripped apart.
    /// </summary>
    private static void L120LayAisles(L120Plan plan, L120Room r, ref Rng rng)
    {
        var (p0, q0, p1, q1) = L120Inner(r);
        bool alongP = p1 - p0 >= q1 - q0;
        int l0 = alongP ? p0 : q0, l1 = alongP ? p1 : q1, s0 = alongP ? q0 : p0, s1 = alongP ? q1 : p1;
        var rack = new bool[l1 + 2];
        for (int l = l0 + 1; l <= l1 - 1;)
        {
            int end = Math.Min(l + rng.Range(6, 11) - 1, l1 - 1);
            for (int k = l; k <= end; k++) rack[k] = true;
            l = end + 3;
        }
        byte tray = alongP ? L120TrayX : L120TrayZ;
        ArchPier low = alongP ? ArchPier.North : ArchPier.West, high = alongP ? ArchPier.South : ArchPier.East;
        for (int s = s0; s <= s1; s++)
        {
            int o = (s - s0) % 6;
            bool wrecked = rng.Chance(0.25);
            for (int l = l0; l <= l1; l++)
            {
                ref Tile t = ref L120Along(plan, alongP, l, s);
                if (o <= 2)
                {
                    if (o == 1)
                    {
                        t.Depth = rng.Chance(1 / 30.0) ? L120PanelHole : L120PanelVent;
                        t.Overhead = tray;
                    }
                    continue;
                }
                // (A pair of rows needs both of them and the hot aisle between inside the room: the last are left out where it ends)
                int pairEnd = s - o + 5;
                if (pairEnd > s1) continue;
                if (o == 4)
                {
                    t.Zone = (byte)L120Zone.Hot;
                    t.Depth = L120PanelDirty;
                    continue;
                }
                if (!rack[l]) continue;
                t.Zone = (byte)L120Zone.Hot;
                L120PlaceRack(plan, ref t, ref rng, o == 3 ? low : high, wrecked);
            }
        }
    }

    /// <summary>A terminal room: rows of desks, each with its CRT turned to the chair behind it; every screen dead or smashed.</summary>
    private static void L120LayTerminals(L120Plan plan, L120Room r, ref Rng rng)
    {
        var (p0, q0, p1, q1) = L120Inner(r);
        for (int q = q0; q + 1 <= q1; q += 4)
            for (int p = p0; p <= p1; p++)
            {
                if ((p - p0) % 7 == 6 || rng.Chance(0.08)) continue;
                ref Tile t = ref plan.At(p, q);
                t.Variant = L120Terminal;
                t.Pier = ArchPier.South;
                t.Detail = rng.Chance(0.45) ? L120TermSmashed : L120TermDead;
                plan.Terminals++;
                if (!rng.Chance(0.7)) continue;
                ref Tile c = ref plan.At(p, q + 1);
                c.Variant = L120Chair;
                c.Pier = rng.Chance(0.7) ? ArchPier.North : (ArchPier)rng.Range(0, 3);
            }
    }

    /// <summary>A wrecked store: racks thrown down and broken up, heaps of parts and scrap, crates, cables everywhere.</summary>
    private static void L120LayWreck(L120Plan plan, L120Room r, ref Rng rng)
    {
        var (p0, q0, p1, q1) = L120Inner(r);
        for (int q = q0; q <= q1; q++)
            for (int p = p0; p <= p1; p++)
            {
                ref Tile t = ref plan.At(p, q);
                double w = rng.NextDouble();
                t.Pier = (ArchPier)rng.Range(0, 3);
                if (w < 0.07) { t.Variant = L120Wreck; t.Detail = L120WreckToppled; plan.Wrecked++; }
                else if (w < 0.11) { t.Variant = L120Wreck; t.Detail = L120WreckTorn; plan.Wrecked++; }
                else if (w < 0.17) t.Variant = Props.ScrapMetal;
                else if (w < 0.22) t.Variant = Props.MachineParts;
                else if (w < 0.25) t.Stack = (byte)rng.Range(1, 2);
                else if (w < 0.27) { t.Variant = L120Rack; t.Detail = L120RackGutted; plan.Racks++; plan.Wrecked++; }
                else if (w < 0.37) t.Variant = L120Spill;
            }
    }

    /// <summary>A cable room: racks along one wall facing in, a tray across the middle, cables pulled out over the floor, a dead cabinet or two.</summary>
    private static void L120LayCables(L120Plan plan, L120Room r, ref Rng rng)
    {
        var (p0, q0, p1, q1) = L120Inner(r);
        for (int p = p0; p <= p1; p++)
            if (rng.Chance(0.8)) L120PlaceRack(plan, ref plan.At(p, q0), ref rng, ArchPier.South, rng.Chance(0.3));
        int mid = (q0 + q1) / 2;
        for (int p = r.P0; p <= r.P1; p++) plan.At(p, mid).Overhead = L120TrayX;
        for (int q = q0 + 2; q <= q1; q++)
            for (int p = p0; p <= p1; p++)
            {
                ref Tile t = ref plan.At(p, q);
                double w = rng.NextDouble();
                if (w < 0.12) t.Variant = L120Spill;
                else if (w < 0.14) t.Depth = L120PanelHole;
                else if (w < 0.15) { t.Variant = Props.Cabinet; t.Pier = (ArchPier)rng.Range(0, 3); }
            }
    }

    /// <summary>
    /// The cluster's whole terminal: in a terminal room if there is one (one of its desks, the chair pushed back), otherwise
    /// on a desk set by the north wall of some room, its screen to the walk round the room where whoever boots it stands.
    /// </summary>
    private static void L120PlaceBoot(L120Plan plan, List<L120Room> rooms, ref Rng rng)
    {
        var desks = new List<(int P, int Q)>();
        foreach (L120Room r in rooms)
        {
            if (r.Kind != L120RoomKind.Terminals) continue;
            for (int q = r.Q0; q <= r.Q1; q++)
                for (int p = r.P0; p <= r.P1; p++)
                    if (plan.At(p, q).Variant == L120Terminal) desks.Add((p, q));
        }
        if (desks.Count > 0)
        {
            var (p, q) = desks[rng.Range(0, desks.Count - 1)];
            plan.At(p, q).Detail = L120TermBoot;
            plan.At(p, q + 1).Variant = 0;
            var (x, z) = plan.World(p, q);
            plan.Boots.Add((x, z, x, z + 1));
            return;
        }
        for (int tries = 0; tries < 20; tries++)
        {
            L120Room r = rooms[rng.Range(0, rooms.Count - 1)];
            int p = rng.Range(r.P0 + 2, r.P1 - 2);
            ref Tile t = ref plan.At(p, r.Q0 + 1);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.SupplyBox || t.Stack != 0) continue;
            t.Variant = L120Terminal;
            t.Detail = L120TermBoot;
            t.Pier = ArchPier.North;
            plan.Terminals++;
            var (x, z) = plan.World(p, r.Q0 + 1);
            plan.Boots.Add((x, z, x, z - 1));
            return;
        }
    }

    /// <summary>
    /// Walks the cluster from its doors onto the passages; any open floor nothing reaches (shut in by racks and boxes)
    /// gets a heap of scrap, and a doorway nothing reaches is walled up, so every open tile left can be walked to.
    /// </summary>
    private static void L120FillUnreached(L120Plan plan)
    {
        const int n = L120Grid;
        var reached = new bool[n * n];
        var queue = new Queue<int>();
        for (int i = 0; i < plan.Tiles.Length; i++)
        {
            int a = i % n - 1, b = i / n - 1;
            if ((a == -1 || b == -1 || a == L120HallSize || b == L120HallSize) && plan.Tiles[i].Kind == TileKind.Doorway)
            {
                reached[i] = true;
                queue.Enqueue(i);
            }
        }
        if (queue.Count == 0) return; // (no doors at all cannot happen: every side has room floor along it)
        while (queue.Count > 0)
        {
            int i = queue.Dequeue();
            int a = i % n, b = i / n;
            foreach ((int dx, int dz) in Steps)
            {
                int x = a + dx, z = b + dz;
                if (x < 0 || z < 0 || x >= n || z >= n) continue;
                int j = x + z * n;
                if (reached[j] || !IsWalkable(plan.Tiles[j])) continue;
                reached[j] = true;
                queue.Enqueue(j);
            }
        }
        for (int i = 0; i < plan.Tiles.Length; i++)
        {
            ref Tile t = ref plan.Tiles[i];
            if (reached[i] || !IsWalkable(t)) continue;
            if (t.Kind == TileKind.Doorway) { t.Kind = TileKind.Wall; continue; }
            t.Variant = Props.ScrapMetal;
        }
    }

    // ================= Pockets =================

    /// <summary>
    /// A White Void: 6-12 rooms of 11 square (four high) on a grid of twelve, grown from one, all white and lit from the
    /// ceiling; a black door between neighbours (a tree of them and some loops), a broken window in the middle of every
    /// wall that has no room behind it. The rest of the hall is solid black. You arrive in the first room.
    /// </summary>
    private static void L120LayVoid(L120Plan plan, ref Rng rng)
    {
        const int cells = 7, pitch = 12, off = 3;
        var chosen = new bool[cells, cells];
        var list = new List<(int I, int J)>();
        var links = new List<((int, int) A, (int, int) B)>();
        (int I, int J) start = (rng.Range(2, 4), rng.Range(2, 4));
        chosen[start.I, start.J] = true;
        list.Add(start);
        int want = rng.Range(6, 12);
        (int, int)[] steps = { (1, 0), (-1, 0), (0, 1), (0, -1) };
        for (int tries = 0; list.Count < want && tries < 400; tries++)
        {
            var (i, j) = list[rng.Range(0, list.Count - 1)];
            var (di, dj) = steps[rng.Range(0, 3)];
            int ni = i + di, nj = j + dj;
            if (ni < 0 || nj < 0 || ni >= cells || nj >= cells || chosen[ni, nj]) continue;
            chosen[ni, nj] = true;
            list.Add((ni, nj));
            links.Add(((i, j), (ni, nj)));
        }
        plan.Rooms = list.Count;
        // Loops: some other neighbours get a door too
        foreach (var (i, j) in list)
            foreach (var (di, dj) in new[] { (1, 0), (0, 1) })
            {
                int ni = i + di, nj = j + dj;
                if (ni < cells && nj < cells && chosen[ni, nj] && !links.Contains(((i, j), (ni, nj))) && !links.Contains(((ni, nj), (i, j))) && rng.Chance(0.35))
                    links.Add(((i, j), (ni, nj)));
            }

        static int Lo(int i) => off + pitch * i; // a cell's low wall
        foreach (var (i, j) in list)
            for (int q = Lo(j); q <= Lo(j) + pitch; q++)
                for (int p = Lo(i); p <= Lo(i) + pitch; p++)
                {
                    ref Tile t = ref plan.At(p, q);
                    bool wall = p == Lo(i) || q == Lo(j) || p == Lo(i) + pitch || q == Lo(j) + pitch;
                    if (wall)
                    {
                        t.Zone = (byte)L120Zone.VoidWall;
                        continue;
                    }
                    t.Kind = TileKind.Floor;
                    t.Zone = (byte)L120Zone.Void;
                    t.Height = 4;
                    t.Ceiling = (p - Lo(i)) % 3 == 0 && (q - Lo(j)) % 3 == 0 ? CeilingKind.L120VoidPanel : CeilingKind.L120VoidCeiling;
                }
        // The black doors
        foreach (var ((i, j), (ni, nj)) in links)
        {
            bool alongP = ni != i; // the cells side by side along P: the door is in a wall running along Q
            int p = alongP ? Lo(Math.Max(i, ni)) : Lo(i) + pitch / 2;
            int q = alongP ? Lo(j) + pitch / 2 : Lo(Math.Max(j, nj));
            ref Tile t = ref plan.At(p, q);
            t.Kind = TileKind.Doorway;
            t.Zone = (byte)L120Zone.Void;
            t.Height = 4;
            t.Variant = L120VoidDoor;
            t.Detail = (byte)(alongP ? 0 : 1);
        }
        // A broken window in every outside wall, facing into its room
        foreach (var (i, j) in list)
            foreach (var (di, dj) in steps)
            {
                int ni = i + di, nj = j + dj;
                if (ni >= 0 && nj >= 0 && ni < cells && nj < cells && chosen[ni, nj]) continue;
                int p = di > 0 ? Lo(i) + pitch : di < 0 ? Lo(i) : Lo(i) + pitch / 2;
                int q = dj > 0 ? Lo(j) + pitch : dj < 0 ? Lo(j) : Lo(j) + pitch / 2;
                ref Tile t = ref plan.At(p, q);
                t.Kind = TileKind.Floor;
                t.Zone = (byte)L120Zone.Void;
                t.Height = 4;
                t.Ceiling = CeilingKind.L120VoidCeiling;
                t.Variant = L120Window;
                t.Pier = di > 0 ? ArchPier.West : di < 0 ? ArchPier.East : dj > 0 ? ArchPier.North : ArchPier.South;
                plan.Windows++;
            }
        plan.Arrival = plan.World(Lo(start.I) + pitch / 2 - 2, Lo(start.J) + pitch / 2 - 2);
    }

    /// <summary>
    /// A Pitch-Black Hallway: lanes two wide and 86 long, folded back and forth (6-14 of them, 500-1200 blocks end to end),
    /// unlit, cables underfoot here and there; a broken window closes each end. You arrive halfway along the middle lane:
    /// whichever way you walk, you come to a window.
    /// </summary>
    private static void L120LayHallway(L120Plan plan, ref Rng rng)
    {
        int lanes = rng.Range(6, 14);
        const int p0 = 2, p1 = 87;
        static int Q(int k) => 3 + 3 * k;
        var r = rng;
        for (int k = 0; k < lanes; k++)
        {
            for (int q = Q(k) - 1; q <= Q(k) + 2; q++)
                for (int p = p0 - 1; p <= p1 + 1; p++)
                {
                    ref Tile w = ref plan.At(p, q);
                    if (w.Kind == TileKind.Wall) w.Zone = (byte)L120Zone.HallWall;
                }
            for (int q = Q(k); q <= Q(k) + 1; q++)
                for (int p = p0; p <= p1; p++) Lane(p, q);
            // The bend into the next lane, at alternate ends
            if (k + 1 < lanes)
            {
                int e = k % 2 == 0 ? p1 - 1 : p0;
                Lane(e, Q(k) + 2);
                Lane(e + 1, Q(k) + 2);
            }
        }
        rng = r;
        // The windows: lane 0's free end is the west one; the last lane's is the end its bend does not take
        Window(p0 - 1, ArchPier.East, Q(0));
        bool lastWest = (lanes - 2) % 2 == 0;
        Window(lastWest ? p0 - 1 : p1 + 1, lastWest ? ArchPier.East : ArchPier.West, Q(lanes - 1));
        plan.Arrival = plan.World(44, Q(lanes / 2));
        plan.Rooms = lanes;

        void Lane(int p, int q)
        {
            ref Tile t = ref plan.At(p, q);
            if (t.Kind == TileKind.Floor) return;
            t.Kind = TileKind.Floor;
            t.Zone = (byte)L120Zone.Hallway;
            t.Height = 3;
            t.Depth = L120PanelDirty;
            if (r.Chance(0.045)) t.Variant = L120Spill;
        }

        void Window(int p, ArchPier face, int q)
        {
            for (int k = 0; k < 2; k++)
            {
                ref Tile t = ref plan.At(p, q + k);
                t.Kind = TileKind.Floor;
                t.Zone = (byte)L120Zone.Hallway;
                t.Height = 3;
                t.Variant = L120Window;
                t.Pier = face;
                plan.Windows++;
            }
        }
    }

    /// <summary>Where a pocket hall puts down whoever booted their way into it (a world block).</summary>
    public (int X, int Z) L120PocketArrival(int hx, int hz) => L120PlanOf(hx, hz).Arrival;

    /// <summary>Which of the level's props (<see cref="Props.L120First"/>-<see cref="Props.L120Last"/>) people walk through: the spilled cables, the broken windows.</summary>
    private static bool L120WalkThrough(ushort variant) => variant is L120Spill or L120Window;

    // ================= Air =================

    /// <summary>
    /// The temperature (the lore says nothing; kept from the prototype): the hot aisles behind the racks hot enough to cost
    /// food (38 °C, see HeatSystem), a wrecked store warm, the rooms chilled, the passages between; the voids mild and the
    /// hallways cold.
    /// </summary>
    private float L120Temperature(int x, int y, int z, int floorY)
    {
        Tile t = TileAt(x, z);
        if (t.Level != Level120) return LevelTemperatures[Level120];
        return t.Zone switch
        {
            (byte)L120Zone.Hot => 38f,
            (byte)L120Zone.Wreck => 26f,
            (byte)L120Zone.Room => 22f,
            (byte)L120Zone.Terminals => 23f,
            (byte)L120Zone.Corridor => 25f,
            (byte)L120Zone.Void => 21f,
            (byte)L120Zone.Hallway => 14f,
            _ => LevelTemperatures[Level120],
        };
    }

    /// <summary>Reality stability: steady in the server rooms; the White Voids pull at you a little, the hallways more.</summary>
    private float L120Stability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        if (t.Level != Level120) return 1.05f;
        return t.Zone switch
        {
            (byte)L120Zone.Void => 0.97f,
            (byte)L120Zone.Hallway => 0.94f,
            _ => 1.05f,
        };
    }
}
