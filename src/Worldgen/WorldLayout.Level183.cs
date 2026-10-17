using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 183, "Clean Sewers" (experimental): kept as level 27 (<see cref="Level183"/>) and shown as "183". A round noclip
/// region far out to the north-west, beyond the End: endless arched sewers that carry clear, clean water. Neither wiki has
/// a Level 183 by this name, so the design (docs/design/experimental-levels/183-plan.md) is built on the name alone. No
/// thresholds in or out (the cheats menu or <c>/backrooms goto 183</c> only). This file is the level's own.
///
/// <para><b>The lattice.</b> A node every eight blocks each way (four by four to a cell, the first four in from its west and
/// north lines), joined by links. Every third node line may be a <b>main</b>: whole rows and columns, picked by hash, that
/// run straight on for as long as the Trunk Tunnels last (a "major" one, one line in five, runs on through every zone).
/// The rest of a cell's sixteen nodes are joined by a spanning tree (a hash-ordered union-find, the mains joined first) and
/// a quarter more links for loops; two links of the four node lines cross every side between two of the level's cells, and
/// every main does. So the whole region is one network.</para>
///
/// <para><b>Sections.</b> A main is nine wide: a channel three wide down the middle (its bed two below the walkways,
/// one block of water over it), a curb either side at the water's level, a walkway two wide along each wall, under a
/// stepped arch (three, four and five blocks of air). A side link is five wide: a gutter one wide down the middle (one
/// deep, its water level with the walkways) between walkways of two, a drain grate where gutters meet at a node (three
/// long, so the walkways either side join there); one in six is a <b>dry gallery</b>, three wide, with pipes overhead.
/// Where two mains cross or turn, the crossing is decked over with grates (the water runs on under them); where a main
/// ends, at about half the nodes where anything joins it and a few others, a grate bridge three wide spans the channel.
/// A node where three or more links meet may be a <b>junction chamber</b> 11 by 11 under a dome, a basin in its middle;
/// a cell of the Junction Halls may hold a <b>hall</b> 16 by 16 over its four middle nodes, four pillars and a
/// sump.</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> is the <see cref="L183Zone"/> in its low two bits and the
/// <see cref="L183Space"/> above them; on a floor or water tile <see cref="Tile.Detail"/> is the <see cref="L183Part"/> and
/// <see cref="Tile.Height"/> the top block of air above the walkways' floor; on a wall <see cref="Tile.Detail"/> is plain,
/// stained or a pillar. A wall lamp is a <see cref="Tile.Ceiling"/> kind (121-123) on the tile in front of the wall, which
/// is its <see cref="Tile.Pier"/>; pipes are <see cref="Tile.Pipe"/> 150-153. Channels, basins and gutters are
/// <see cref="TileKind.Water"/>; curbs and grates are floor, never an arrival.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2700-0x27BF are this level's (0x27C0-0x27FF its thresholds').</summary>
    private const ulong SaltL183Shape = 0x2701;
    private const ulong SaltL183Zone = 0x2700, SaltL183Main = 0x2702, SaltL183Tree = 0x2703, SaltL183Border = 0x2704,
        SaltL183Hall = 0x2706, SaltL183Chamber = 0x2707, SaltL183Bridge = 0x2708, SaltL183Lamp = 0x2709, SaltL183Pipe = 0x270A,
        SaltL183Stain = 0x270C;

    /// <summary>What part of the sewers a cell is in (the low two bits of <see cref="Tile.Zone"/>; title keys 2701-2703).</summary>
    public enum L183Zone : byte { None, Trunk, Channels, Halls }

    /// <summary>What a tile is part of (<see cref="Tile.Zone"/> above its low two bits).</summary>
    public enum L183Space : byte { Rock, Main, Side, Gallery, Chamber, Hall }

    /// <summary>
    /// What a floor or water tile is (<see cref="Tile.Detail"/>): a walkway (dry floor at the walkways' height), a curb (one
    /// lower, at the water's surface), a channel or basin (its bed two lower, one block of water), a grate (over a block of
    /// water, level with the walkways), a gutter (its bed one lower, its water level with the walkways).
    /// </summary>
    public enum L183Part : byte { Walk, Curb, Channel, Grate, Gutter }

    /// <summary>Wall tiles' <see cref="Tile.Detail"/>.</summary>
    public const byte L183WallPlain = 0, L183WallStained = 1, L183WallPillar = 2;

    private enum L183Link : byte { None, Main, Side, Gallery }

    /// <summary>The node grid: a node every eight blocks, the first four in from a cell's west (north) line.</summary>
    public const int L183Pitch = 8, L183Node0 = 4;

    /// <summary>The zone noise below which a cell is the Channels, above which the Junction Halls (tuned with 183stats).</summary>
    private const double L183ChannelsBelow = -0.2, L183HallsAbove = 0.22;

    public static L183Zone L183ZoneOf(in Tile t) => (L183Zone)(t.Zone & 3);

    public static L183Space L183SpaceOf(in Tile t) => (L183Space)(t.Zone >> 2);

    // ================= Where it is =================

    /// <summary>
    /// How far out along the north-west diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond the End, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L183Reach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    private int L183CentreX => spawnMacroX - L183Reach;
    private int L183CentreZ => spawnMacroZ - L183Reach;

    /// <summary>The region's radius in macro cells.</summary>
    private int L183Radius => Math.Max(40, spawnMacroX / 50);

    /// <summary>The region's centre and radius, in cells (for the harness).</summary>
    public (int Mx, int Mz, int Radius) L183Region => (L183CentreX, L183CentreZ, L183Radius);

    private bool InL183(double mx, double mz) => InRoundRegion(mx, mz, L183CentreX, L183CentreZ, L183Radius, SaltL183Shape);

    /// <summary>A place near the middle of the region to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) L183ArrivalCell(ulong h) => RoundArrivalCell(h, L183CentreX, L183CentreZ, L183Radius);

    /// <summary>Arriving: on a dry walkway (of a tunnel, a chamber or a hall), never in the water, on a curb or a grate.</summary>
    private static bool IsL183ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Detail == (byte)L183Part.Walk && L183SpaceOf(t) != L183Space.Rock;

    /// <summary>How high above the level's floor to put someone down on an arrival tile (see <see cref="ArrivalHeight"/>).</summary>
    private static double L183ArrivalHeight(in Tile t, double stand) => stand;

    // ================= Zones and the lattice =================

    private bool L183Ours(int mx, int mz) => LevelAt(mx, mz) == Level183;

    /// <summary>The zone of one of the level's cells: the Trunk Tunnels (mains common), the Channels (only the major mains), the Junction Halls.</summary>
    public L183Zone L183CellZone(int mx, int mz)
    {
        double f = Fbm(mx / 5.0, mz / 5.0, SaltL183Zone);
        return f < L183ChannelsBelow ? L183Zone.Channels : f > L183HallsAbove ? L183Zone.Halls : L183Zone.Trunk;
    }

    /// <summary>Whether node line <paramref name="k"/> (axis 1: the row at z = 8k + 4, running west-east; axis 0 the column) is a main: 0 no, 1 in the Trunk Tunnels, 2 a major one everywhere.</summary>
    private int L183MainLine(int axis, int k)
    {
        if (Hashing.Mod(k, 3) != 0) return 0;
        double u = Hashing.Unit(Hashing.Hash(seed, k, axis, SaltL183Main));
        return u < 0.2 ? 2 : u < 0.55 ? 1 : 0;
    }

    /// <summary>Whether the link between nodes (i, j) and (i + 1, j) is a main.</summary>
    private bool L183MainX(int i, int j) => L183MainLink(L183MainLine(1, j), i, j, i + 1, j);

    /// <summary>Whether the link between nodes (i, j) and (i, j + 1) is a main.</summary>
    private bool L183MainZ(int i, int j) => L183MainLink(L183MainLine(0, i), i, j, i, j + 1);

    private bool L183MainLink(int line, int ia, int ja, int ib, int jb)
    {
        if (line == 0) return false;
        int max = Hashing.FloorDiv(ia, 4), maz = Hashing.FloorDiv(ja, 4), mbx = Hashing.FloorDiv(ib, 4), mbz = Hashing.FloorDiv(jb, 4);
        if (!L183Ours(max, maz) || !L183Ours(mbx, mbz)) return false;
        return line == 2 || L183CellZone(max, maz) == L183Zone.Trunk && L183CellZone(mbx, mbz) == L183Zone.Trunk;
    }

    private bool L183NodeHasMain(int i, int j) => L183MainX(i - 1, j) || L183MainX(i, j) || L183MainZ(i, j - 1) || L183MainZ(i, j);

    private static L183Link L183SideKind(ulong h) => Hashing.Unit(h) < 1 / 6.0 ? L183Link.Gallery : L183Link.Side;

    /// <summary>
    /// The four links across the west (or north) side of cell (mx, mz), one on each node line: every main, and two more
    /// picked by hash (side tunnels or dry galleries); none where either cell is not the level's.
    /// </summary>
    private L183Link[] L183Border(int mx, int mz, bool west)
    {
        var links = new L183Link[4];
        if (!L183Ours(mx, mz) || !L183Ours(west ? mx - 1 : mx, west ? mz : mz - 1)) return links;
        ulong h = Hashing.Hash(seed, mx, mz, SaltL183Border + (west ? 0UL : 1UL));
        int a = (int)(h % 4), b = (int)((h >> 8) % 3);
        if (b >= a) b++;
        for (int k = 0; k < 4; k++)
        {
            bool main = west ? L183MainX(mx * 4 - 1, mz * 4 + k) : L183MainZ(mx * 4 + k, mz * 4 - 1);
            if (main) links[k] = L183Link.Main;
            else if (k == a || k == b) links[k] = L183SideKind(Hashing.Mix(h + (ulong)k * 0x9E37UL));
        }
        return links;
    }

    /// <summary>A cell's sixteen nodes: their links each way (east, west, south, north; those across the cell's sides too) and what each node is.</summary>
    private sealed class L183Plan
    {
        public bool Ours, Hall;
        public L183Zone Zone;
        public readonly L183Link[] East = new L183Link[16], West = new L183Link[16], South = new L183Link[16], North = new L183Link[16];
        /// <summary>A junction chamber; a crossing of mains (decked over); a main node with a grate bridge across its channel.</summary>
        public readonly bool[] Chamber = new bool[16], Crossing = new bool[16], Bridge = new bool[16];
    }

    private PlanCache<L183Plan> l183Plans;

    private L183Plan L183PlanAt(int mx, int mz) => (l183Plans ??= new PlanCache<L183Plan>(1024, MakeL183Plan)).Get(mx, mz);

    /// <summary>The plan holding node (i, j), and the node's index in it.</summary>
    private L183Plan L183NodePlan(int i, int j, out int n)
    {
        int mx = Hashing.FloorDiv(i, 4), mz = Hashing.FloorDiv(j, 4);
        n = (j - mz * 4) * 4 + (i - mx * 4);
        return L183PlanAt(mx, mz);
    }

    private L183Link L183LinkX(int i, int j) => L183NodePlan(i, j, out int n).East[n];

    private L183Link L183LinkZ(int i, int j) => L183NodePlan(i, j, out int n).South[n];

    private L183Plan MakeL183Plan(int mx, int mz)
    {
        var p = new L183Plan();
        if (!L183Ours(mx, mz)) return p;
        p.Ours = true;
        p.Zone = L183CellZone(mx, mz);
        int gi0 = mx * 4, gj0 = mz * 4;
        L183Link[] west = L183Border(mx, mz, true), east = L183Border(mx + 1, mz, true), north = L183Border(mx, mz, false), south = L183Border(mx, mz + 1, false);
        for (int k = 0; k < 4; k++)
        {
            p.West[k * 4] = west[k];
            p.East[k * 4 + 3] = east[k];
            p.North[k] = north[k];
            p.South[12 + k] = south[k];
        }

        // A hall over the four middle nodes, in some cells of the Junction Halls where no main runs through them
        bool hall = p.Zone == L183Zone.Halls && Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL183Hall)) < 0.55;
        for (int nj = 1; nj <= 2 && hall; nj++)
            for (int ni = 1; ni <= 2; ni++)
                if (L183NodeHasMain(gi0 + ni, gj0 + nj)) { hall = false; break; }
        p.Hall = hall;

        // The links inside the cell: the mains first, then a spanning tree in hash order, a quarter more for loops
        var parent = new int[16];
        for (int k = 0; k < 16; k++) parent[k] = k;
        int Find(int a) { while (parent[a] != a) a = parent[a] = parent[parent[a]]; return a; }
        void Set(int ni, int nj, bool alongX, L183Link kind)
        {
            int n = nj * 4 + ni;
            if (alongX) { p.East[n] = kind; p.West[n + 1] = kind; }
            else { p.South[n] = kind; p.North[n + 4] = kind; }
        }
        var rng = new Rng(Hashing.Hash(seed, mx, mz, SaltL183Tree));
        var candidates = new List<(int I, int J, bool AlongX, double Order)>();
        for (int nj = 0; nj < 4; nj++)
            for (int ni = 0; ni < 4; ni++)
                for (int d = 0; d < 2; d++)
                {
                    bool alongX = d == 0;
                    int oi = alongX ? ni + 1 : ni, oj = alongX ? nj : nj + 1;
                    if (oi > 3 || oj > 3) continue;
                    int a = nj * 4 + ni, b = oj * 4 + oi;
                    bool main = alongX ? L183MainX(gi0 + ni, gj0 + nj) : L183MainZ(gi0 + ni, gj0 + nj);
                    if (main)
                    {
                        Set(ni, nj, alongX, L183Link.Main);
                        parent[Find(b)] = Find(a);
                    }
                    else if (hall && L183InHall(ni, nj) && L183InHall(oi, oj)) parent[Find(b)] = Find(a);
                    else candidates.Add((ni, nj, alongX, rng.NextDouble()));
                }
        candidates.Sort((x, y) => x.Order.CompareTo(y.Order));
        double extra = p.Zone == L183Zone.Channels ? 0.32 : 0.25;
        foreach (var (ni, nj, alongX, _) in candidates)
        {
            int a = Find(nj * 4 + ni), b = Find(alongX ? nj * 4 + ni + 1 : (nj + 1) * 4 + ni);
            if (a != b) parent[b] = a;
            else if (!rng.Chance(extra)) continue;
            Set(ni, nj, alongX, L183SideKind(rng.NextULong()));
        }

        // What each node is
        double chamberShare = p.Zone switch { L183Zone.Halls => 0.8, L183Zone.Channels => 0.4, _ => 0.6 };
        for (int n = 0; n < 16; n++)
        {
            int ni = n % 4, nj = n / 4, gi = gi0 + ni, gj = gj0 + nj;
            bool mainX = p.East[n] == L183Link.Main || p.West[n] == L183Link.Main, mainZ = p.South[n] == L183Link.Main || p.North[n] == L183Link.Main;
            p.Crossing[n] = mainX && mainZ;
            if (mainX != mainZ)
            {
                bool deadEnd = mainX ? p.East[n] != L183Link.Main || p.West[n] != L183Link.Main : p.South[n] != L183Link.Main || p.North[n] != L183Link.Main;
                bool joined = mainX ? p.South[n] != L183Link.None || p.North[n] != L183Link.None : p.East[n] != L183Link.None || p.West[n] != L183Link.None;
                p.Bridge[n] = deadEnd || Hashing.Unit(Hashing.Hash(seed, gi, gj, SaltL183Bridge)) < (joined ? 0.45 : 0.1);
            }
            if (mainX || mainZ || hall || (gi & 1) != 0 || (gj & 1) != 0) continue;
            int degree = (p.East[n] != 0 ? 1 : 0) + (p.West[n] != 0 ? 1 : 0) + (p.South[n] != 0 ? 1 : 0) + (p.North[n] != 0 ? 1 : 0);
            if (degree < 3) continue;
            // Not beside a main (whose walkways would run into the chamber)
            if (L183NodeHasMain(gi - 1, gj) || L183NodeHasMain(gi + 1, gj) || L183NodeHasMain(gi, gj - 1) || L183NodeHasMain(gi, gj + 1)) continue;
            p.Chamber[n] = Hashing.Unit(Hashing.Hash(seed, gi, gj, SaltL183Chamber)) < chamberShare;
        }
        return p;
    }

    private static bool L183InHall(int ni, int nj) => ni is 1 or 2 && nj is 1 or 2;

    // ================= Tiles =================

    /// <summary>What the plan puts at a block position: the space and the part of it, the top block of air, and where in it (for lamps and pipes).</summary>
    private struct L183Spot
    {
        public L183Space Space;
        public L183Part Part;
        public byte Top;
        public bool Pillar;
        /// <summary>A tunnel: 1 if it runs west-east, 0 north-south; -1 a chamber or a hall.</summary>
        public int Axis;
        /// <summary>A tunnel: how far across from its middle line, and the block coordinate along it; a chamber or hall: the offsets east and south from its middle (or corner).</summary>
        public int Across, Along;
        /// <summary>A tunnel: its link's low node.</summary>
        public int LinkI, LinkJ;
    }

    private static int L183Wet(L183Part p) => p switch { L183Part.Channel => 4, L183Part.Gutter => 4, L183Part.Grate => 3, L183Part.Curb => 2, _ => 1 };

    /// <summary>How far either side of a chamber's link its mouth opens (-1: no link there).</summary>
    private static int L183MouthHalf(L183Link l) => l == L183Link.Side ? 2 : l == L183Link.Gallery ? 1 : -1;

    /// <summary>The plan at a block position, worked out from the nodes round it (pure: every cell and edge sees the same).</summary>
    private L183Spot L183Classify(int gx, int gz)
    {
        int i0 = Hashing.FloorDiv(gx, L183Pitch), j0 = Hashing.FloorDiv(gz, L183Pitch);
        int dx0 = gx - (L183Pitch * i0 + L183Node0), dz0 = gz - (L183Pitch * j0 + L183Node0); // -4..3

        // Mains (first): the strips of the rows and columns within four
        L183Spot main = default;
        bool inMain = false;
        for (int axis = 0; axis < 2; axis++)
        {
            int g = axis == 1 ? gx : gz, c = axis == 1 ? gz : gx, k0 = axis == 1 ? j0 : i0, d0 = axis == 1 ? dz0 : dx0;
            for (int k = d0 == -4 ? k0 - 1 : k0; k <= k0; k++)
            {
                int across = c - (L183Pitch * k + L183Node0);
                int li = Hashing.FloorDiv(g - L183Node0, L183Pitch);
                for (int l = g - L183Node0 - L183Pitch * li == 0 ? li - 1 : li; l <= li; l++)
                {
                    L183Link link = axis == 1 ? L183LinkX(l, k) : L183LinkZ(k, l);
                    if (link != L183Link.Main) continue;
                    int a = g - (L183Pitch * l + L183Node0); // 0..8 along the link
                    int ab = Math.Abs(across);
                    L183Part part = ab <= 1 ? L183Part.Channel : ab == 2 ? L183Part.Curb : L183Part.Walk;
                    byte top = (byte)(ab <= 1 ? 5 : ab == 2 ? 4 : 3);
                    int nai, nbi;
                    L183Plan na = axis == 1 ? L183NodePlan(l, k, out nai) : L183NodePlan(k, l, out nai);
                    L183Plan nb = axis == 1 ? L183NodePlan(l + 1, k, out nbi) : L183NodePlan(k, l + 1, out nbi);
                    bool deck = a <= 4 && na.Crossing[nai] || a >= 4 && nb.Crossing[nbi] || a <= 1 && na.Bridge[nai] || a >= 7 && nb.Bridge[nbi];
                    if (deck) part = part == L183Part.Channel ? L183Part.Grate : part == L183Part.Curb ? L183Part.Walk : part;
                    byte keepTop = inMain ? Math.Max(main.Top, top) : top;
                    if (!inMain || L183Wet(part) > L183Wet(main.Part))
                        main = new L183Spot { Space = L183Space.Main, Part = part, Axis = axis, Across = across, Along = g,
                            LinkI = axis == 1 ? l : k, LinkJ = axis == 1 ? k : l };
                    main.Top = keepTop;
                    inMain = true;
                }
            }
        }
        if (inMain) return main;

        // A hall over the middle of its cell
        int mx = MacroOf(gx), mz = MacroOf(gz), lx = gx - mx * MacroSize, lz = gz - mz * MacroSize;
        if (lx is >= 8 and <= 23 && lz is >= 8 and <= 23 && L183PlanAt(mx, mz).Hall)
        {
            var hall = new L183Spot { Space = L183Space.Hall, Axis = -1, Across = lx, Along = lz, Top = (byte)(lx is >= 12 and <= 19 && lz is >= 12 and <= 19 ? 6 : 5) };
            if (lx is 10 or 21 && lz is 10 or 21) { hall.Space = L183Space.Rock; hall.Pillar = true; }
            else if (lx is >= 14 and <= 17 && lz is >= 14 and <= 17) hall.Part = L183Part.Channel;
            else if (lx is >= 13 and <= 18 && lz is >= 13 and <= 18) hall.Part = L183Part.Curb;
            return hall;
        }

        // A junction chamber: 11 by 11 inside a ring of wall, open only where its links come in
        for (int j = j0 - 1; j <= j0 + 1; j++)
            for (int i = i0 - 1; i <= i0 + 1; i++)
            {
                int dx = gx - (L183Pitch * i + L183Node0), dz = gz - (L183Pitch * j + L183Node0);
                if (Math.Abs(dx) > 6 || Math.Abs(dz) > 6) continue;
                L183Plan plan = L183NodePlan(i, j, out int n);
                if (!plan.Chamber[n]) continue;
                int d = Math.Max(Math.Abs(dx), Math.Abs(dz));
                if (d == 6)
                {
                    bool mouth = Math.Abs(dz) <= (dx == 6 ? L183MouthHalf(plan.East[n]) : dx == -6 ? L183MouthHalf(plan.West[n]) : -1)
                        || Math.Abs(dx) <= (dz == 6 ? L183MouthHalf(plan.South[n]) : dz == -6 ? L183MouthHalf(plan.North[n]) : -1);
                    if (mouth) continue;
                    return new L183Spot { Space = L183Space.Rock, Axis = -1 };
                }
                return new L183Spot
                {
                    Space = L183Space.Chamber, Axis = -1, Across = dx, Along = dz,
                    Part = d <= 1 ? L183Part.Channel : d == 2 ? L183Part.Curb : L183Part.Walk,
                    Top = (byte)(d <= 2 ? 6 : d <= 4 ? 5 : 4),
                };
            }

        // Side tunnels (before dry galleries): only the row and column of the nearest node are near enough
        var best = new L183Spot { Axis = -1 };
        int bestPriority = 0;
        for (int axis = 0; axis < 2; axis++)
        {
            int g = axis == 1 ? gx : gz, k = axis == 1 ? j0 : i0, across = axis == 1 ? dz0 : dx0;
            if (Math.Abs(across) > 2) continue;
            int li = Hashing.FloorDiv(g - L183Node0, L183Pitch);
            for (int l = g - L183Node0 - L183Pitch * li == 0 ? li - 1 : li; l <= li; l++)
            {
                L183Link link = axis == 1 ? L183LinkX(l, k) : L183LinkZ(k, l);
                if (link is L183Link.None or L183Link.Main) continue;
                if (link == L183Link.Gallery && Math.Abs(across) > 1) continue;
                int priority = link == L183Link.Side ? 2 : 1;
                int a = g - (L183Pitch * l + L183Node0);
                L183Part part = link == L183Link.Side && across == 0 ? (a <= 1 || a >= 7 ? L183Part.Grate : L183Part.Gutter) : L183Part.Walk;
                if (priority < bestPriority || priority == bestPriority && L183Wet(part) <= L183Wet(best.Part)) continue;
                bestPriority = priority;
                best = new L183Spot { Space = link == L183Link.Side ? L183Space.Side : L183Space.Gallery, Part = part, Top = 3, Axis = axis,
                    Across = across, Along = g, LinkI = axis == 1 ? l : k, LinkJ = axis == 1 ? k : l };
            }
        }
        return best;
    }

    /// <summary>Whether a wall lamp hangs on this walkway tile, and on which wall (the tile beside it in that direction must be rock).</summary>
    private bool L183Lamp(int gx, int gz, in L183Spot s, out ArchPier wall)
    {
        wall = ArchPier.West;
        if (s.Part != L183Part.Walk) return false;
        int dx = 0, dz = 0;
        switch (s.Space)
        {
            case L183Space.Main:
            case L183Space.Side:
            case L183Space.Gallery:
            {
                int edge = s.Space == L183Space.Main ? 4 : s.Space == L183Space.Side ? 2 : 1, period = s.Space == L183Space.Main ? 12 : 24;
                int offset = s.Space == L183Space.Gallery ? 6 : 0;
                int sign = s.Across == edge && Hashing.Mod(s.Along - offset, period) == 0 ? 1
                    : s.Across == -edge && Hashing.Mod(s.Along - offset - period / 2, period) == 0 ? -1 : 0;
                if (sign == 0) return false;
                if (s.Axis == 1) dz = sign; else dx = sign;
                break;
            }
            case L183Space.Chamber:
                (dx, dz) = (s.Across, s.Along) switch { (5, -3) => (1, 0), (-5, 3) => (-1, 0), (3, 5) => (0, 1), (-3, -5) => (0, -1), _ => (0, 0) };
                break;
            case L183Space.Hall:
                (dx, dz) = (s.Across, s.Along) switch
                {
                    (11, 10) or (11, 21) => (-1, 0), (20, 10) or (20, 21) => (1, 0), (8, 15) => (-1, 0), (23, 16) => (1, 0), (15, 8) => (0, -1), (16, 23) => (0, 1),
                    _ => (0, 0),
                };
                break;
        }
        if (dx == 0 && dz == 0) return false;
        if (L183Classify(gx + dx, gz + dz).Space != L183Space.Rock) return false;
        wall = dx > 0 ? ArchPier.East : dx < 0 ? ArchPier.West : dz > 0 ? ArchPier.South : ArchPier.North;
        return true;
    }

    /// <summary>The tile the plan puts at a block position, with its lamp and pipes.</summary>
    private Tile L183PlanTile(int gx, int gz, L183Zone zone)
    {
        L183Spot s = L183Classify(gx, gz);
        if (s.Space == L183Space.Rock)
        {
            byte detail = s.Pillar ? L183WallPillar
                : Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL183Stain)) < 0.1 ? L183WallStained : L183WallPlain;
            return new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L183Wall, Detail = detail, Zone = (byte)zone };
        }
        var t = new Tile
        {
            Kind = s.Part is L183Part.Channel or L183Part.Gutter ? TileKind.Water : TileKind.Floor,
            Floor = FloorKind.L183Floor,
            Ceiling = CeilingKind.L183Ceiling,
            Detail = (byte)s.Part,
            Height = s.Top,
            Zone = (byte)((int)zone | (int)s.Space << 2),
        };
        if (L183Lamp(gx, gz, s, out ArchPier wall))
        {
            t.Pier = wall;
            ulong h = Hashing.Hash(seed, gx, gz, SaltL183Lamp);
            t.Ceiling = Hashing.Unit(h) < 0.08 ? CeilingKind.L183LampFlicker
                : s.Space is L183Space.Chamber or L183Space.Hall ? CeilingKind.L183LampBright : CeilingKind.L183LampOn;
            return t;
        }
        // Pipes along the top of one wall of a main (most stretches), and down the middle of every dry gallery
        bool pipe = s.Space == L183Space.Main && s.Part == L183Part.Walk && s.Across == -4 && s.Top == 3
            && Hashing.Unit(Hashing.Hash(seed, s.LinkI * 2 + s.Axis, s.LinkJ, SaltL183Pipe)) < 0.6
            || s.Space == L183Space.Gallery && s.Across == 0;
        if (pipe)
        {
            bool leak = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL183Pipe + 1)) < 0.1;
            t.Pipe = s.Axis == 1 ? (leak ? Pipes.L183LeakWE : Pipes.L183PipeWE) : (leak ? Pipes.L183LeakNS : Pipes.L183PipeNS);
        }
        return t;
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: open wherever the plan has a way across it.</summary>
    private Edge L183Edge(int mx, int mz, bool west)
    {
        var edge = new Edge { Pattern = WallPattern.L183Wall };
        for (int i = 1; i < MacroSize; i++)
        {
            int gx = west ? mx * MacroSize : mx * MacroSize + i, gz = west ? mz * MacroSize + i : mz * MacroSize;
            edge.Tiles[i] = L183Classify(gx, gz).Space == L183Space.Rock ? EdgeTile.Wall : EdgeTile.Open;
        }
        return edge;
    }

    /// <summary>Lays out one of the level's cells from the plan, tile by tile; where the region ends, its wall stays as the edge laid it.</summary>
    private void BuildLevel183(Builder b, int mx, int mz)
    {
        L183Zone zone = L183CellZone(mx, mz);
        bool westOurs = L183Ours(mx - 1, mz), northOurs = L183Ours(mx, mz - 1), cornerOurs = westOurs && northOurs && L183Ours(mx - 1, mz - 1);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (lx == 0 && lz == 0 ? !cornerOurs : lx == 0 ? !westOurs : lz == 0 && !northOurs)
                {
                    if (t.Kind == TileKind.Wall) t.Zone = (byte)zone;
                    continue;
                }
                t = L183PlanTile(mx * MacroSize + lx, mz * MacroSize + lz, zone);
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.L183First"/>-<see cref="Props.L183Last"/>) people walk through: none (it has none).</summary>
    private static bool L183WalkThrough(ushort variant) => false;

    /// <summary>The zone and the space at a block position (for the client's air and titles).</summary>
    public (L183Zone Zone, L183Space Space) L183Where(int x, int z)
    {
        Tile t = TileAt(x, z);
        return (L183ZoneOf(t), L183SpaceOf(t));
    }

    // ================= Air =================

    /// <summary>The temperature: cool and steady, a degree cooler in the narrow side tunnels.</summary>
    private float L183Temperature(int x, int y, int z, int floorY) => L183SpaceOf(TileAt(x, z)) == L183Space.Side ? 11f : 12f;

    /// <summary>Reality stability: neutral, a little gain in the halls.</summary>
    private float L183Stability(double x, double y, double z, int floorY, float drift) =>
        L183SpaceOf(TileAt((int)Math.Floor(x), (int)Math.Floor(z))) == L183Space.Hall ? 1.1f : 1f;
}
