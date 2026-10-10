using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// The Hub, the hidden crossroads of the Backrooms: kept as level 17 (<see cref="Hub"/>) and shown as "Hub". An endless
/// network of road tunnels of seamed concrete slabs, lit orange by caged lamps, an asphalt road with three lines of yellow
/// studs, silent; both walls lined with great concrete doors, a crop circle carved over each, one for every level, and
/// almost all of them locked (docs/new-levels/hub-plan.md).
///
/// Like the Poolrooms it is not a ring: it lies far out to the south-east, a region you can only noclip into, its floor
/// <see cref="WorldGeometry.HubDrop"/> below the other levels'. It is planned round one centre, the Tower: ten numbered
/// tunnels (the spokes) run out from a roundabout round it to the rim, ring roads cross them, and narrower side tunnels
/// twist between, some ending blind at a door. Every tunnel is a chain of straight, axis-aligned stretches, because a
/// door three blocks wide needs a straight wall. The plan is a small graph of stretches worked out once per world
/// (<see cref="HubRoads"/>) and rasterised cell by cell.
///
/// Tiles: a floor tile's <see cref="Tile.Height"/> is the air above it (7 in a main tunnel, 5 in a side tunnel); its
/// <see cref="Tile.Detail"/> says what hangs on the wall behind it (<see cref="HubWallLamp"/> ...: wall-hung things belong
/// to the air in front of the wall), at <see cref="Tile.Depth"/> above the floor, facing <see cref="Tile.Pier"/>, with a
/// number in <see cref="Tile.Pipe"/>; a door's Detail is its sigil (<see cref="HubSigilLevel"/>) and its
/// <see cref="Tile.Stack"/> which of its three columns it is. <see cref="Tile.Zone"/>: <see cref="HubZoneCrossroads"/>,
/// <see cref="HubZoneFar"/>, <see cref="HubZoneTower"/>.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x1700-0x17BF are this level's (0x1710 is Level 37's corridor-end roll).</summary>
    private const ulong SaltHubShape = 0x1701, SaltHubSpoke = 0x1702, SaltHubRing = 0x1703, SaltHubLattice = 0x1704,
        SaltHubLive = 0x1705, SaltHubSlot = 0x1706, SaltHubFeature = 0x1707, SaltHubLamp = 0x1708, SaltHubFloor = 0x1709,
        SaltHubTheta = 0x170A;

    // ================= Where it is =================

    /// <summary>The region's centre, in macro cells: far out to the south-east, a quarter further out than the city.</summary>
    private int HubCentreX => spawnMacroX + DiagonalReach;
    private int HubCentreZ => spawnMacroZ + DiagonalReach;

    /// <summary>The region's radius in macro cells (1,920 blocks), whatever the size of the world.</summary>
    private const int HubRadius = 60;

    /// <summary>The middle of the Tower, in blocks: everything in the Hub is planned from here.</summary>
    public int HubOriginX => HubCentreX * MacroSize + MacroSize / 2;
    public int HubOriginZ => HubCentreZ * MacroSize + MacroSize / 2;

    /// <summary>A round region with a clean edge: its rim ring must always lie inside.</summary>
    private bool InHub(double mx, double mz)
    {
        double dx = mx - HubCentreX, dz = mz - HubCentreZ;
        return dx * dx + dz * dz < HubRadius * HubRadius;
    }

    /// <summary>Whether a square of the world (block coordinates) might reach into the region.</summary>
    public bool MayReachHub(int x0, int z0, int size)
    {
        double dx = (x0 + size / 2.0) / MacroSize - HubCentreX, dz = (z0 + size / 2.0) / MacroSize - HubCentreZ;
        return Math.Sqrt(dx * dx + dz * dz) < HubRadius + 1 + size / (double)MacroSize;
    }

    /// <summary>A place to look for somewhere to arrive: in the Crossroads, between 200 and 1,000 blocks from the Tower.</summary>
    private (int Mx, int Mz) HubArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, radius = 200 + 800 * Hashing.Unit(Hashing.Mix(h));
        return (MacroOf(HubOriginX + (int)Math.Round(Math.Cos(angle) * radius)), MacroOf(HubOriginZ + (int)Math.Round(Math.Sin(angle) * radius)));
    }

    /// <summary>Arriving in the Hub: on a sidewalk of the Crossroads.</summary>
    private static bool IsHubArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Floor == FloorKind.HubSidewalk && t.Zone == HubZoneCrossroads;

    /// <summary>How high above the level's floor to put someone down: the sidewalks are half a block up.</summary>
    private static double HubArrivalHeight(in Tile t, double stand) => t.Floor == FloorKind.HubSidewalk ? stand + 0.5 : stand;

    // ================= The plan =================

    /// <summary>Half the width of a main and a side tunnel's inside: a tile is inside where |offset| is at most this.</summary>
    public const int HubMainHalf = 6, HubSideHalf = 3;

    /// <summary>The air over a main and a side tunnel's floor (the ceiling is the block above).</summary>
    public const int HubMainHeight = 7, HubSideHeight = 5;

    /// <summary>The ring roads' radii: the last is the rim, which every spoke ends on.</summary>
    private static readonly int[] HubRingRadii = { 330, 700, 1100, 1480, 1820 };

    /// <summary>The roundabout round the Tower, the Tower's own radius, and the edge of the known area (the Crossroads).</summary>
    public const int HubRoundabout = 62, HubTowerRadius = 24, HubKnownRadius = 1100;

    /// <summary>The side tunnels' lattice.</summary>
    private const int HubLatticePitch = 96;

    /// <summary>What a stretch is part of.</summary>
    private const byte HubSpokeSeg = 0, HubRingSeg = 1, HubSideSeg = 2;

    public const byte HubZoneCrossroads = 0, HubZoneFar = 1, HubZoneTower = 2;

    /// <summary>On a wall tile's Detail: a lamp (lit or dead), an M.E.G. stencil (its number in Height, 11 = TOWER), a plaque by an open door (Height: 1, 11, 178).</summary>
    public const byte HubWallLamp = 1, HubWallDeadLamp = 2, HubWallStencil = 3, HubWallPlaque = 4, HubWallBanner = 5, HubWallCabinet = 6;

    /// <summary>The door to Level 6.1 (canon's door to Level 178).</summary>
    public const int HubSnackroomsDoor = 61;

    /// <summary>A straight stretch of tunnel: along x (at z = C) or along z (at x = C), from A0 to A1.</summary>
    private sealed class HubSeg
    {
        public int Id;
        public bool AlongX;
        public int C, A0, A1, Half;
        public byte Kind;
        /// <summary>For a spoke's stretches, the tunnel's number (1 to 10).</summary>
        public int Spoke;
        /// <summary>The stretch ends blind here, with a door (or the tile turning white) in the end wall.</summary>
        public bool CapLow, CapHigh;
        /// <summary>The tunnel's middle line's distance from the Tower at the stretch's middle.</summary>
        public double R;

        public int Height => Half == HubMainHalf ? HubMainHeight : HubSideHeight;
        public bool Main => Half == HubMainHalf;

        /// <summary>A block position in this stretch's own terms: along it, and across it (signed).</summary>
        public (int Along, int Across) Local(int x, int z) => AlongX ? (x, z - C) : (z, x - C);
        public (int X, int Z) World(int along, int across) => AlongX ? (along, C + across) : (C + across, along);

        public bool Inside(int x, int z)
        {
            var (a, c) = Local(x, z);
            return c >= -Half && c <= Half && a >= A0 - Half && a <= A1 + Half;
        }
    }

    /// <summary>A door's place: on a stretch, on one side (+1 or -1 across), or in its end wall (0), at a point along it.</summary>
    private readonly record struct HubSlot(int Seg, int Side, int Along);

    /// <summary>What stands in a door's place.</summary>
    private enum HubSlotKind : byte { Dead, Live, Service, FalseWall, Window }

    private sealed class HubPlan
    {
        public readonly List<HubSeg> Segs = new();
        public readonly Dictionary<(int, int), List<HubSeg>> Bins = new();
        /// <summary>The ten tunnels' directions and the ten approaches to the Tower: from the roundabout to the Tower's wall.</summary>
        public readonly (double Dx, double Dz)[] Spokes = new (double, double)[10];
        /// <summary>The level doors: where each is (sigil → slot), and what is at a slot.</summary>
        public readonly Dictionary<int, HubSlot> LiveDoors = new();
        public readonly Dictionary<HubSlot, (HubSlotKind Kind, byte Sigil)> Special = new();
        /// <summary>The holes down to Level 94 (their corner, along their stretch), and the tunnels whose blind end has turned to tile.</summary>
        public readonly List<(int Seg, int Along)> Holes = new();
        public readonly HashSet<(int Seg, bool High)> TileEnds = new();
        /// <summary>The angle the plan is turned by: the ten tunnels lie at Theta0 + 18 + 36k degrees, the balcony at Theta0.</summary>
        public double Theta0;
    }

    private const int HubBin = 128;
    private HubPlan hubPlan;
    private readonly object hubPlanLock = new();

    /// <summary>The Hub's tunnels, worked out once for the world.</summary>
    private HubPlan HubRoads
    {
        get
        {
            if (hubPlan != null) return hubPlan;
            lock (hubPlanLock) return hubPlan ??= PlanHub();
        }
    }

    private HubPlan PlanHub()
    {
        var plan = new HubPlan();
        int ox = HubOriginX, oz = HubOriginZ;
        double theta0 = Hashing.Unit(Hashing.Hash(seed, 17, 0, SaltHubTheta)) * Math.PI * 2;
        plan.Theta0 = theta0;

        void Add(HubSeg s)
        {
            if (s.A1 < s.A0) (s.A0, s.A1) = (s.A1, s.A0);
            s.Id = plan.Segs.Count;
            var (mx, mz) = s.World((s.A0 + s.A1) / 2, 0);
            s.R = Math.Sqrt((double)(mx - ox) * (mx - ox) + (double)(mz - oz) * (mz - oz));
            plan.Segs.Add(s);
        }

        // Joins two points with one or two straight stretches (an L), turning at the corner the hash picks
        void Join((int X, int Z) p, (int X, int Z) q, int half, byte kind, int spoke, ulong h, List<HubSeg> into = null)
        {
            if (p == q) return;
            bool xFirst = Hashing.Unit(h) < 0.5;
            (int X, int Z) corner = xFirst ? (q.X, p.Z) : (p.X, q.Z);
            foreach (var (a, b) in new[] { (p, corner), (corner, q) })
            {
                if (a == b) continue;
                var s = a.Z == b.Z
                    ? new HubSeg { AlongX = true, C = a.Z, A0 = a.X, A1 = b.X, Half = half, Kind = kind, Spoke = spoke }
                    : new HubSeg { AlongX = false, C = a.X, A0 = a.Z, A1 = b.Z, Half = half, Kind = kind, Spoke = spoke };
                Add(s);
                into?.Add(s);
            }
        }

        (int, int) At(double angle, double radius) => (ox + (int)Math.Round(Math.Cos(angle) * radius), oz + (int)Math.Round(Math.Sin(angle) * radius));

        // The roundabout and the ring roads: loops of stretches round the Tower
        void Loop(double radius, int half, int ring, double jitter)
        {
            int n = Math.Max(10, (int)Math.Round(2 * Math.PI * radius / 64));
            var points = new List<(int, int)>();
            for (int i = 0; i < n; i++)
            {
                ulong h = Hashing.Hash(seed, ring, i, SaltHubRing);
                double r = radius + (Hashing.Unit(h) * 2 - 1) * jitter;
                points.Add(At(theta0 + 2 * Math.PI * i / n, r));
            }
            for (int i = 0; i < n; i++) Join(points[i], points[(i + 1) % n], half, HubRingSeg, 0, Hashing.Hash(seed, ring, i + 1000, SaltHubRing));
        }
        Loop(HubRoundabout, HubMainHalf, 0, 0);
        for (int ring = 0; ring < HubRingRadii.Length; ring++)
            Loop(HubRingRadii[ring], ring < 3 ? HubMainHalf : HubSideHalf, ring + 1, 10);

        // The ten tunnels, numbered clockwise: from the roundabout out to past the rim, wandering off their rays
        for (int k = 0; k < 10; k++)
        {
            double angle = theta0 + Math.PI / 10 + 2 * Math.PI * k / 10;
            plan.Spokes[k] = (Math.Cos(angle), Math.Sin(angle));
            double px = -Math.Sin(angle), pz = Math.Cos(angle);
            var points = new List<(int, int)> { At(angle, HubRoundabout) };
            double r = HubRoundabout;
            for (int i = 0; r < HubRingRadii[^1] - 60; i++)
            {
                ulong h = Hashing.Hash(seed, k, i, SaltHubSpoke);
                r = Math.Min(HubRingRadii[^1] - 40, r + 48 + 48 * Hashing.Unit(h));
                double off = (Hashing.Unit(Hashing.Mix(h)) * 2 - 1) * 10;
                points.Add((ox + (int)Math.Round(Math.Cos(angle) * r + px * off), oz + (int)Math.Round(Math.Sin(angle) * r + pz * off)));
            }
            // The last stretch runs straight out along the spoke's main axis until it meets the rim
            var (lx, lz) = points[^1];
            bool xMain = Math.Abs(Math.Cos(angle)) >= Math.Abs(Math.Sin(angle));
            int reach = HubRingRadii[^1] + 4;
            points.Add(xMain ? (ox + (int)Math.Round(Math.Sign(Math.Cos(angle)) * Math.Sqrt(Math.Max(0, (double)reach * reach - (double)(lz - oz) * (lz - oz)))), lz)
                : (lx, oz + (int)Math.Round(Math.Sign(Math.Sin(angle)) * Math.Sqrt(Math.Max(0, (double)reach * reach - (double)(lx - ox) * (lx - ox))))));
            for (int i = 0; i + 1 < points.Count; i++) Join(points[i], points[i + 1], HubMainHalf, HubSpokeSeg, k + 1, Hashing.Hash(seed, k, i + 500, SaltHubSpoke));
        }
        int mainCount = plan.Segs.Count;
        foreach (HubSeg s in plan.Segs) Bin(plan, s);

        // The side tunnels: a jittered lattice, about half its edges there; anything not joined to a main tunnel is left out
        int span = HubRingRadii[^1] / HubLatticePitch + 1;
        (int X, int Z)? Node(int i, int j)
        {
            ulong h = Hashing.Hash(seed, i, j, SaltHubLattice);
            int x = ox + i * HubLatticePitch + (int)((Hashing.Unit(h) * 2 - 1) * 20), z = oz + j * HubLatticePitch + (int)((Hashing.Unit(Hashing.Mix(h)) * 2 - 1) * 20);
            double r = Math.Sqrt((double)(x - ox) * (x - ox) + (double)(z - oz) * (z - oz));
            return r >= 140 && r <= HubRingRadii[^1] - 30 ? (x, z) : null;
        }
        var edges = new List<(int I, int J, int I2, int J2, List<HubSeg> Segs)>();
        for (int j = -span; j <= span; j++)
            for (int i = -span; i <= span; i++)
            {
                if (Node(i, j) is not { } a) continue;
                foreach ((int di, int dj, ulong salt) in new[] { (1, 0, 1UL), (0, 1, 2UL) })
                {
                    if (Node(i + di, j + dj) is not { } b) continue;
                    ulong h = Hashing.Hash(seed, i * 2 + (int)salt, j, SaltHubLattice + 1);
                    if (Hashing.Unit(h) >= 0.55) continue;
                    var segs = new List<HubSeg>();
                    int before = plan.Segs.Count;
                    Join(a, b, HubSideHalf, HubSideSeg, 0, Hashing.Mix(h), segs);
                    // Never through the middle, where the roundabout and the Tower are
                    bool near = false;
                    foreach (HubSeg s in segs)
                        if (SegDistance(s, ox, oz) < 100) near = true;
                    if (near)
                    {
                        plan.Segs.RemoveRange(before, plan.Segs.Count - before);
                        continue;
                    }
                    edges.Add((i, j, i + di, j + dj, segs));
                }
            }

        // Which lattice pieces reach a main tunnel
        var parent = new Dictionary<(int, int), (int, int)>();
        (int, int) Find((int, int) n)
        {
            while (parent.TryGetValue(n, out var p) && p != n) n = p;
            return n;
        }
        void Union((int, int) a, (int, int) b)
        {
            parent.TryAdd(a, a);
            parent.TryAdd(b, b);
            var ra = Find(a);
            var rb = Find(b);
            if (ra != rb) parent[ra] = rb;
        }
        foreach (var e in edges) Union((e.I, e.J), (e.I2, e.J2));
        var joined = new HashSet<(int, int)>();
        foreach (var e in edges)
            foreach (HubSeg s in e.Segs)
                if (TouchesMain(plan, s)) joined.Add(Find((e.I, e.J)));
        var degree = new Dictionary<(int, int), int>();
        var kept = new List<HubSeg>();
        foreach (var e in edges)
        {
            if (!joined.Contains(Find((e.I, e.J)))) continue;
            degree[(e.I, e.J)] = degree.GetValueOrDefault((e.I, e.J)) + 1;
            degree[(e.I2, e.J2)] = degree.GetValueOrDefault((e.I2, e.J2)) + 1;
            kept.AddRange(e.Segs);
        }
        // Renumber: the main tunnels first, then the side tunnels kept
        plan.Segs.RemoveRange(mainCount, plan.Segs.Count - mainCount);
        foreach (HubSeg s in kept)
        {
            s.Id = plan.Segs.Count;
            plan.Segs.Add(s);
            Bin(plan, s);
        }
        // A side tunnel that goes nowhere else ends blind (unless its end lies in a main tunnel anyway)
        foreach (var ((i, j), d) in degree)
        {
            if (d != 1 || Node(i, j) is not { } n) continue;
            foreach (HubSeg s in kept)
            {
                var (a, c) = s.Local(n.X, n.Z);
                if (c != 0 || a != s.A0 && a != s.A1) continue;
                bool high = a == s.A1;
                // Not blind if the end opens into another tunnel
                var (ex, ez) = s.World(high ? s.A1 + s.Half + 1 : s.A0 - s.Half - 1, 0);
                if (HubInsideAny(plan, ex, ez, s)) continue;
                if (high) s.CapHigh = true; else s.CapLow = true;
            }
        }

        PlaceHubFeatures(plan);
        return plan;
    }

    private static void Bin(HubPlan plan, HubSeg s)
    {
        var (x0, z0) = s.World(s.A0 - s.Half - 2, -s.Half - 2);
        var (x1, z1) = s.World(s.A1 + s.Half + 2, s.Half + 2);
        for (int bz = Hashing.FloorDiv(Math.Min(z0, z1), HubBin); bz <= Hashing.FloorDiv(Math.Max(z0, z1), HubBin); bz++)
            for (int bx = Hashing.FloorDiv(Math.Min(x0, x1), HubBin); bx <= Hashing.FloorDiv(Math.Max(x0, x1), HubBin); bx++)
            {
                if (!plan.Bins.TryGetValue((bx, bz), out var list)) plan.Bins[(bx, bz)] = list = new List<HubSeg>();
                list.Add(s);
            }
    }

    /// <summary>The distance from a point to the middle line of a stretch.</summary>
    private static double SegDistance(HubSeg s, int x, int z)
    {
        var (a, c) = s.Local(x, z);
        int da = a < s.A0 ? s.A0 - a : a > s.A1 ? a - s.A1 : 0;
        return Math.Sqrt((double)da * da + (double)c * c);
    }

    private static bool TouchesMain(HubPlan plan, HubSeg s)
    {
        var (x0, z0) = s.World(s.A0 - s.Half, -s.Half);
        var (x1, z1) = s.World(s.A1 + s.Half, s.Half);
        (x0, x1) = (Math.Min(x0, x1), Math.Max(x0, x1));
        (z0, z1) = (Math.Min(z0, z1), Math.Max(z0, z1));
        foreach (HubSeg m in plan.Segs)
        {
            if (m.Kind == HubSideSeg) continue;
            var (mx0, mz0) = m.World(m.A0 - m.Half, -m.Half);
            var (mx1, mz1) = m.World(m.A1 + m.Half, m.Half);
            if (Math.Max(mx0, mx1) < x0 || Math.Min(mx0, mx1) > x1 || Math.Max(mz0, mz1) < z0 || Math.Min(mz0, mz1) > z1) continue;
            return true;
        }
        return false;
    }

    private static bool HubInsideAny(HubPlan plan, int x, int z, HubSeg except = null)
    {
        if (!plan.Bins.TryGetValue((Hashing.FloorDiv(x, HubBin), Hashing.FloorDiv(z, HubBin)), out var list)) return false;
        foreach (HubSeg s in list)
            if (s != except && s.Inside(x, z)) return true;
        return false;
    }

    // ================= Inside the tunnels =================

    /// <summary>Whether a block position lies inside a tunnel (or an approach to the Tower), and which stretch holds it best.</summary>
    private HubSeg HubSegAt(HubPlan plan, int x, int z)
    {
        if (!plan.Bins.TryGetValue((Hashing.FloorDiv(x, HubBin), Hashing.FloorDiv(z, HubBin)), out var list)) return null;
        HubSeg best = null;
        int bestAcross = int.MaxValue;
        foreach (HubSeg s in list)
        {
            if (!s.Inside(x, z)) continue;
            int across = Math.Abs(s.Local(x, z).Across) + (s.Main ? 0 : 100);
            if (across < bestAcross) { best = s; bestAcross = across; }
        }
        return best;
    }

    /// <summary>An approach to the Tower: which of the ten (0-9) a position lies in, if any, and how far off its middle.</summary>
    private int HubApproachAt(HubPlan plan, int x, int z, out double off, out double r)
    {
        double dx = x + 0.5 - (HubOriginX + 0.5), dz = z + 0.5 - (HubOriginZ + 0.5);
        r = Math.Sqrt(dx * dx + dz * dz);
        off = 0;
        if (r < HubTowerInner || r > HubRoundabout) return -1;
        for (int k = 0; k < 10; k++)
        {
            var (ux, uz) = plan.Spokes[k];
            double along = dx * ux + dz * uz;
            if (along <= 0) continue;
            double across = -dx * uz + dz * ux;
            if (Math.Abs(across) <= 2.6) { off = across; return k; }
        }
        return -1;
    }

    private bool HubInside(HubPlan plan, int x, int z) =>
        HubSegAt(plan, x, z) != null || HubApproachAt(plan, x, z, out _, out double r) >= 0 && r >= HubTowerRadius + 0.5;

    // ================= Doors =================

    /// <summary>The slots along a stretch: every 24 blocks a side in a main tunnel (the two sides staggered), every 16 in a side tunnel.</summary>
    private static IEnumerable<HubSlot> SlotsOf(HubSeg s)
    {
        int spacing = s.Main ? 24 : 16;
        foreach (int side in new[] { -1, 1 })
        {
            int start = s.A0 + 8 + (s.Main && side > 0 ? 12 : 0);
            for (int a = start; a <= s.A1 - 8; a += spacing) yield return new HubSlot(s.Id, side, a);
        }
        if (s.CapLow) yield return new HubSlot(s.Id, 0, s.A0);
        if (s.CapHigh) yield return new HubSlot(s.Id, 0, s.A1);
    }

    /// <summary>The three wall tiles a door in a slot fills (left, middle, right as seen by someone facing it), and the way it faces.</summary>
    private static ((int X, int Z) L, (int X, int Z) C, (int X, int Z) R, ArchPier Facing) SlotTiles(HubSeg s, HubSlot slot)
    {
        (int X, int Z) Pos(int along, int across) => s.World(along, across);
        if (slot.Side != 0)
        {
            int across = slot.Side * (s.Half + 1);
            // Facing back into the tunnel
            ArchPier facing = s.AlongX ? (slot.Side > 0 ? ArchPier.North : ArchPier.South) : (slot.Side > 0 ? ArchPier.West : ArchPier.East);
            var (rx, rz) = RightOf(facing);
            var c = Pos(slot.Along, across);
            return ((c.X - rx, c.Z - rz), c, (c.X + rx, c.Z + rz), facing);
        }
        {
            bool high = slot.Along == s.A1;
            int along = high ? s.A1 + s.Half + 1 : s.A0 - s.Half - 1;
            ArchPier facing = s.AlongX ? (high ? ArchPier.West : ArchPier.East) : (high ? ArchPier.North : ArchPier.South);
            var (rx, rz) = RightOf(facing);
            var c = Pos(along, 0);
            return ((c.X - rx, c.Z - rz), c, (c.X + rx, c.Z + rz), facing);
        }
    }

    /// <summary>
    /// The right hand of someone looking at the front of something that faces <paramref name="facing"/> (so looking the
    /// other way).
    /// </summary>
    private static (int X, int Z) RightOf(ArchPier facing) => facing switch
    {
        ArchPier.North => (-1, 0), // looking south: west on the right
        ArchPier.South => (1, 0),
        ArchPier.East => (0, -1), // looking west: north on the right
        _ => (0, 1),
    };

    private static (int X, int Z) Step(ArchPier p) => p switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    /// <summary>Whether a door fits a slot: three wall tiles in a straight wall, open floor in front of all three, wall either side.</summary>
    private bool SlotFits(HubPlan plan, HubSeg s, HubSlot slot)
    {
        var (l, c, r, facing) = SlotTiles(s, slot);
        var (fx, fz) = Step(facing);
        var (rx, rz) = RightOf(facing);
        foreach (var t in new[] { l, c, r })
        {
            if (HubInside(plan, t.X, t.Z) || !HubInside(plan, t.X + fx, t.Z + fz)) return false;
            // Behind it, solid: a door is never a hole into the next tunnel
            if (HubInside(plan, t.X - fx, t.Z - fz)) return false;
        }
        return !HubInside(plan, l.X - rx, l.Z - rz) && !HubInside(plan, r.X + rx, r.Z + rz);
    }

    /// <summary>The level each sigil's door leads to, or -1 for the doors to levels nobody can reach (and the Hub's own, 0).</summary>
    public static int HubSigilLevel(int sigil) => sigil switch
    {
        >= 1 and <= 12 => sigil - 1,
        13 => Poolrooms,
        14 => Motion,
        15 => RunLevel,
        16 => FunLevel,
        17 => TheEnd,
        18 => Level974,
        19 => Level3999,
        20 => HubSnackroomsDoor,
        _ => -1,
    };

    /// <summary>The sigil over the door that leads to a level (<see cref="HubSnackroomsDoor"/> for canon's "178"), or 0.</summary>
    public static int HubSigilOf(int level)
    {
        for (int s = 1; s <= 20; s++)
            if (HubSigilLevel(s) == level) return s;
        return 0;
    }

    /// <summary>
    /// The levels with a door in the Hub (LINKS.md: Level 974's is the pink ribbon door; Level 3999's, restored in round 2,
    /// an ordinary keyed door, placed last so the others stay where they were). Level 188 has a window instead.
    /// </summary>
    private static readonly int[] HubDoorLevels =
        { 0, 1, 2, 3, 4, 5, 6, HubSnackroomsDoor, 7, 8, 9, 10, 11, Poolrooms, Motion, RunLevel, FunLevel, TheEnd, Level974, Level3999 };

    /// <summary>Whether a level's door in the Hub opens for anyone: canon's three (Level 1, Level 11, and 178).</summary>
    public static bool HubDoorOpen(int level) => level is 1 or 11 or HubSnackroomsDoor;

    /// <summary>
    /// The level doors, the false walls, the holes and the tiled ends: placed once for the world, each by its own hash.
    /// Canon's three open doors are in its tunnels: Level 1 in the 7th, Level 11 in the 10th, 178 in the 5th.
    /// </summary>
    private void PlaceHubFeatures(HubPlan plan)
    {
        var spokeSlots = new List<HubSlot>[11];
        for (int k = 1; k <= 10; k++) spokeSlots[k] = new List<HubSlot>();
        var used = new List<(int X, int Z)>();
        foreach (HubSeg s in plan.Segs)
        {
            if (s.Kind != HubSpokeSeg) continue;
            foreach (HubSlot slot in SlotsOf(s))
                if (slot.Side != 0) spokeSlots[s.Spoke].Add(slot);
        }

        int ox = HubOriginX, oz = HubOriginZ;
        double Dist((int X, int Z) p) => Math.Sqrt((double)(p.X - ox) * (p.X - ox) + (double)(p.Z - oz) * (p.Z - oz));
        bool Pick(int spoke, double rMin, double rMax, ulong h, HubSlotKind kind, byte sigil)
        {
            List<HubSlot> slots = spokeSlots[spoke];
            if (slots.Count == 0) return false;
            int first = (int)(Hashing.Mix(h) % (ulong)slots.Count);
            for (int n = 0; n < slots.Count; n++)
            {
                HubSlot slot = slots[(first + n * 7919) % slots.Count];
                if (plan.Special.ContainsKey(slot)) continue;
                HubSeg s = plan.Segs[slot.Seg];
                var (_, c, _, _) = SlotTiles(s, slot);
                double d = Dist(c);
                if (d < rMin || d > rMax) continue;
                bool crowded = false;
                foreach (var u in used)
                    if (Math.Abs(u.X - c.X) + Math.Abs(u.Z - c.Z) < 40) crowded = true;
                if (crowded || !SlotFits(plan, s, slot)) continue;
                plan.Special[slot] = (kind, sigil);
                if (kind == HubSlotKind.Live) plan.LiveDoors[sigil] = slot;
                used.Add(c);
                return true;
            }
            return false;
        }

        var perSpoke = new int[11];
        foreach (int level in HubDoorLevels)
        {
            byte sigil = (byte)HubSigilOf(level);
            ulong h = Hashing.Hash(seed, level, 0, SaltHubLive);
            int spoke = level switch { 1 => 7, 11 => 10, HubSnackroomsDoor => 5, _ => 0 };
            if (spoke != 0)
            {
                if (Pick(spoke, 150, 450, h, HubSlotKind.Live, sigil) || Pick(spoke, 120, 900, h, HubSlotKind.Live, sigil)) perSpoke[spoke]++;
                continue;
            }
            // Elsewhere, any tunnel with fewer than three level doors
            int start = (int)(Hashing.Mix(h + 1) % 10);
            for (int n = 0; n < 10; n++)
            {
                int k = 1 + (start + n) % 10;
                if (perSpoke[k] >= 3) continue;
                if (Pick(k, 120, 900, h, HubSlotKind.Live, sigil)) { perSpoke[k]++; break; }
            }
        }

        // The one open window in a tunnel wall, into Level 188 (canon: "look for a window in The Hub, and climb in"): on a
        // tunnel of its own hash, in the Crossroads
        int windowSpoke = 1 + (int)(Hashing.Hash(seed, 188, 0, SaltHubFeature) % 10);
        for (int n = 0; n < 10 && !plan.Special.ContainsValue((HubSlotKind.Window, 0)); n++)
            Pick(1 + (windowSpoke - 1 + n) % 10, 300, 900, Hashing.Hash(seed, 188, n + 1, SaltHubFeature), HubSlotKind.Window, 0);

        // Six stretches of wall that aren't there, on six tunnels, out where the lamps start to die
        int firstSpoke = (int)(Hashing.Hash(seed, 1, 1, SaltHubFeature) % 10);
        for (int n = 0; n < 6; n++)
            Pick(1 + (firstSpoke + n * 3) % 10, 700, 1300, Hashing.Hash(seed, n, 2, SaltHubFeature), HubSlotKind.FalseWall, 0);

        // Four holes in the road of a side tunnel, and five blind ends turned to white tile
        var side = new List<HubSeg>();
        var ends = new List<(HubSeg S, bool High)>();
        foreach (HubSeg s in plan.Segs)
        {
            if (s.Kind != HubSideSeg || s.Main) continue;
            if (s.R >= 600 && s.R <= 1500 && s.A1 - s.A0 >= 30) side.Add(s);
            if (s.R >= 700 && s.R <= 1650)
            {
                if (s.CapLow) ends.Add((s, false));
                if (s.CapHigh) ends.Add((s, true));
            }
        }
        for (int n = 0; n < 4 && side.Count > 0; n++)
        {
            HubSeg s = side[(int)(Hashing.Hash(seed, n, 3, SaltHubFeature) % (ulong)side.Count)];
            int along = (s.A0 + s.A1) / 2 - 2;
            if (!plan.Holes.Exists(hole => hole.Seg == s.Id)) plan.Holes.Add((s.Id, along));
        }
        for (int n = 0; n < 5 && ends.Count > 0; n++)
        {
            var (s, high) = ends[(int)(Hashing.Hash(seed, n, 4, SaltHubFeature) % (ulong)ends.Count)];
            plan.TileEnds.Add((s.Id, high));
        }
    }

    /// <summary>What stands in a door's place: a level door, a service door, a wall that isn't there, or a dead door (and its sigil).</summary>
    private (HubSlotKind Kind, byte Sigil) HubSlotContent(HubPlan plan, HubSlot slot, double r)
    {
        if (plan.Special.TryGetValue(slot, out var special)) return special;
        ulong h = Hashing.Hash(seed, slot.Seg * 4 + slot.Side + 1, slot.Along, SaltHubSlot);
        if (r >= 150 && r <= HubKnownRadius && Hashing.Unit(h) < 0.25) return (HubSlotKind.Service, 0);
        return (HubSlotKind.Dead, (byte)(21 + Hashing.Mix(h) % 24));
    }

    /// <summary>Where the door to a level is (its middle column), facing which way; null if the Hub has none.</summary>
    public (int X, int Z, ArchPier Facing)? HubDoorOf(int level)
    {
        HubPlan plan = HubRoads;
        if (!plan.LiveDoors.TryGetValue(HubSigilOf(level), out HubSlot slot)) return null;
        var (_, c, _, facing) = SlotTiles(plan.Segs[slot.Seg], slot);
        return (c.X, c.Z, facing);
    }

    /// <summary>
    /// The one window into Level 188 (canon: "look for a window in The Hub, and climb in"): its two wall tiles, left and
    /// right as seen from the tunnel, and the way it faces (toward the tunnel). Null if the Hub has none. The window's
    /// tiles carry <see cref="Unders.HubWindow188"/>; rel 2 is its lower half, rel 3 its upper.
    /// </summary>
    public ((int X, int Z) Left, (int X, int Z) Right, ArchPier Facing)? HubWindowOf()
    {
        HubPlan plan = HubRoads;
        foreach (var (slot, content) in plan.Special)
        {
            if (content.Kind != HubSlotKind.Window) continue;
            var (_, c, r, facing) = SlotTiles(plan.Segs[slot.Seg], slot);
            return (c, r, facing);
        }
        return null;
    }

    /// <summary>The level a carved door in the Hub leads to (its sigil's), or -1 for a dead door; null if there is no carved door here.</summary>
    public int? HubDoorLevelAt(int x, int z)
    {
        Tile t = TileAt(x, z);
        if (t.Level != Hub || t.Kind != TileKind.Door || t.Pattern != WallPattern.HubDoor) return null;
        return HubSigilLevel(t.Detail);
    }

    /// <summary>The number of the tunnel (1 to 10) a block position lies in, or 0 if it is not one of the ten.</summary>
    public int HubTunnelAt(int x, int z) => HubSegAt(HubRoads, x, z) is { Kind: HubSpokeSeg } s ? s.Spoke : 0;

    /// <summary>How far a block position is from the middle of the Tower.</summary>
    public double HubDistance(int gx, int gz)
    {
        double dx = gx - HubOriginX, dz = gz - HubOriginZ;
        return Math.Sqrt(dx * dx + dz * dz);
    }

    // ================= Cells =================

    /// <summary>The wall line on a cell's west or north side, between two cells of the level: the plan is laid over it.</summary>
    private Edge HubEdge(int mx, int mz, bool west) => new() { Pattern = WallPattern.HubWall };

    private void BuildLevelHub(Builder b, int mx, int mz)
    {
        HubPlan plan = HubRoads;
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        // Inside or not, a tile and a ring round the cell (to tell walls from the solid mass, and sidewalks from road)
        const int pad = 2, w = MacroSize + 2 * pad;
        var inside = new bool[w * w];
        var segs = new HubSeg[w * w];
        for (int lz = 0; lz < w; lz++)
            for (int lx = 0; lx < w; lx++)
            {
                int gx = x0 + lx - pad, gz = z0 + lz - pad;
                HubSeg s = HubSegAt(plan, gx, gz);
                segs[lz * w + lx] = s;
                inside[lz * w + lx] = s != null || HubApproachAt(plan, gx, gz, out _, out double r) >= 0 && r >= HubTowerRadius + 0.5;
            }
        bool In(int gx, int gz) => inside[(gz - z0 + pad) * w + gx - x0 + pad];

        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = x0 + lx, gz = z0 + lz;
                ref Tile t = ref b.At(lx, lz);
                double r = HubDistance(gx, gz);
                byte zone = r < HubRoundabout - HubMainHalf - 1 ? HubZoneTower : r < HubKnownRadius ? HubZoneCrossroads : HubZoneFar;
                if (!In(gx, gz))
                {
                    t = new Tile { Kind = TileKind.Wall, Pattern = r < HubTowerRadius + 0.5 ? WallPattern.HubAshlar : WallPattern.HubWall, Zone = zone };
                    continue;
                }
                HubSeg s = segs[(lz + pad) * w + lx + pad];
                if (s == null)
                {
                    // An approach to the Tower: marble, lower, its ornate doors at the Tower's wall
                    t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.HubMarble, Height = HubSideHeight, Zone = HubZoneTower, Pattern = WallPattern.HubWall };
                    continue;
                }
                bool edge = !In(gx + 1, gz) || !In(gx - 1, gz) || !In(gx, gz + 1) || !In(gx, gz - 1);
                var (along, across) = s.Local(gx, gz);
                t = new Tile { Kind = TileKind.Floor, Pattern = WallPattern.HubWall, Zone = zone, Height = (byte)s.Height };
                if (edge)
                {
                    t.Floor = FloorKind.HubSidewalk;
                    continue;
                }
                // The road: three dotted lines of yellow studs in a main tunnel, one in a side tunnel
                bool line = s.Main ? across is -3 or 0 or 3 : across == 0;
                ulong h = Hashing.Hash(seed, gx, gz, SaltHubFloor);
                t.Floor = line && Hashing.Mod(along, 2) == 0 ? FloorKind.HubStud
                    : Hashing.Unit(h) < 0.03 ? FloorKind.HubAsphaltPatch : Hashing.Unit(h) < 0.11 ? FloorKind.HubAsphaltWorn : FloorKind.HubAsphalt;
                if (s.Main)
                {
                    // Jet fans hung in pairs, and a gantry of lane signals, along each stretch
                    int a = along - s.A0;
                    if ((a == 24 || a == 72) && along <= s.A1 - 8 && across is -2 or 2) t.Overhead = s.AlongX ? Overheads.HubFanWE : Overheads.HubFanNS;
                    else if (a == 48 && along <= s.A1 - 8 && across is -4 or -1 or 1 or 4)
                    {
                        t.Overhead = Hashing.Unit(h) < 0.05 ? Overheads.HubSignalWE : Overheads.HubSignalNS;
                        t.Pier = s.AlongX ? (across < 0 ? ArchPier.East : ArchPier.West) : (across < 0 ? ArchPier.South : ArchPier.North);
                    }
                }
            }

        // What the walls carry: doors, lamps, stencils, plaques; holes in the road; blind ends turned to tile
        // (Every stretch whose walls reach into the cell is in the cell's bin, in the order they were planned, so a cell
        // and its neighbours settle every tile the same way)
        if (plan.Bins.TryGetValue((Hashing.FloorDiv(x0, HubBin), Hashing.FloorDiv(z0, HubBin)), out var binned))
            foreach (HubSeg s in binned) DecorateHubStretch(b, plan, s, x0, z0, In);
        BuildHubTower(b, plan, x0, z0);
        PlaceHubOutposts(b, x0, z0);
    }

    private void DecorateHubStretch(Builder b, HubPlan plan, HubSeg s, int x0, int z0, Func<int, int, bool> inside)
    {
        bool InCell(int gx, int gz) => gx >= x0 && gz >= z0 && gx < x0 + MacroSize && gz < z0 + MacroSize;
        ref Tile Here(int gx, int gz) => ref b.At(gx - x0, gz - z0);
        // Whether the stretch passes within reach of the cell at all
        var (ax, az) = s.World(s.A0 - s.Half - 2, -s.Half - 2);
        var (bx, bz) = s.World(s.A1 + s.Half + 2, s.Half + 2);
        if (Math.Max(ax, bx) < x0 || Math.Min(ax, bx) >= x0 + MacroSize || Math.Max(az, bz) < z0 || Math.Min(az, bz) >= z0 + MacroSize) return;

        // Something hung on a wall (a lamp, a stencil, a plaque): it belongs to the air in front of the wall, so it is kept
        // on the floor tile there (Detail what, Depth how high, Pier the way it faces, Pipe a number)
        bool Hang((int X, int Z) wall, ArchPier facing, byte kind, byte rel, byte value)
        {
            var (fx, fz) = Step(facing);
            int ax = wall.X + fx, az = wall.Z + fz;
            if (!InCell(ax, az) || HubInside(plan, wall.X, wall.Z) || !s.Inside(ax, az)) return false;
            ref Tile front = ref Here(ax, az);
            if (front.Kind != TileKind.Floor || front.Detail != 0 || front.Under != 0) return false;
            front.Detail = kind;
            front.Depth = rel;
            front.Pier = facing;
            front.Pipe = value;
            return true;
        }

        // Doors
        foreach (HubSlot slot in SlotsOf(s))
        {
            var (l, c, r, facing) = SlotTiles(s, slot);
            if (!InCell(l.X, l.Z) && !InCell(c.X, c.Z) && !InCell(r.X, r.Z)) continue;
            if (!SlotFits(plan, s, slot)) continue;
            double dist = HubDistance(c.X, c.Z);
            var (kind, sigil) = HubSlotContent(plan, slot, dist);
            if (slot.Side == 0 && plan.TileEnds.Contains((s.Id, slot.Along == s.A1))) continue;
            int col = 0;
            foreach (var p in new[] { l, c, r })
            {
                int column = col++;
                if (!InCell(p.X, p.Z)) continue;
                ref Tile t = ref Here(p.X, p.Z);
                switch (kind)
                {
                    case HubSlotKind.Live or HubSlotKind.Dead:
                        t = new Tile { Kind = TileKind.Door, Pattern = WallPattern.HubDoor, Detail = sigil, Stack = (byte)column, Pier = facing, Height = (byte)s.Height, Zone = t.Zone };
                        break;
                    case HubSlotKind.Service when column == 1:
                        t = new Tile { Kind = TileKind.Door, Pattern = WallPattern.HubServiceDoor, Pier = facing, Height = (byte)s.Height, Zone = t.Zone };
                        break;
                    case HubSlotKind.Window when column >= 1:
                        // The window into Level 188: two wall tiles (the middle and right columns), its sill at the
                        // sidewalk's height (Level 188 supplies its blocks)
                        t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.HubWall, Under = Unders.HubWindow188, Stack = (byte)(column - 1), Pier = facing, Height = (byte)s.Height, Zone = t.Zone };
                        break;
                    case HubSlotKind.FalseWall:
                        // A floor tile that looks like the wall: walk into it
                        t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.HubSidewalk, Under = Unders.HubFalseWall, Pier = facing, Height = (byte)s.Height, Zone = t.Zone, Pattern = WallPattern.HubWall };
                        break;
                }
            }
            // The M.E.G. tagged the three doors that are always open
            if (kind == HubSlotKind.Live && HubDoorOpen(HubSigilLevel(sigil)))
            {
                var (rx, rz) = RightOf(facing);
                int level = HubSigilLevel(sigil);
                Hang((r.X + rx, r.Z + rz), facing, HubWallPlaque, 3, (byte)(level == HubSnackroomsDoor ? 178 : level));
            }
        }

        // Lamps every eight blocks: in a main tunnel on both walls (staggered), in a side tunnel on one; and the M.E.G.'s
        // stencils
        for (int a = s.A0, k = 0; a <= s.A1 + 4; a += 4, k++)
        {
            // (Side -1 at 4, 12, 20 ...; side +1 at 0, 8, 16 ..., clear of both walls' door slots)
            int side = k % 2 == 1 ? -1 : 1;
            if (!s.Main && side > 0 || a > s.A1) continue;
            var (_, p, _, facing) = SlotTiles(s, new HubSlot(s.Id, side, a));
            double dist = HubDistance(p.X, p.Z);
            double deadShare = dist < HubKnownRadius ? 0.04 : 0.2 + 0.55 * Math.Clamp((dist - HubKnownRadius) / (HubRingRadii[^1] - HubKnownRadius), 0, 1);
            Hang(p, facing, Hashing.Unit(Hashing.Hash(seed, p.X, p.Z, SaltHubLamp)) < deadShare ? HubWallDeadLamp : HubWallLamp, 4, 0);
        }
        if (s.Kind == HubSpokeSeg)
        {
            for (int a = s.A0 + 18; a <= s.A1 - 4; a += 64)
                foreach (int side in new[] { -1, 1 })
                {
                    var (_, p, _, facing) = SlotTiles(s, new HubSlot(s.Id, side, a));
                    if (HubDistance(p.X, p.Z) > HubKnownRadius) continue;
                    // Toward the middle, one wall points the way to the Tower
                    Hang(p, facing, HubWallStencil, 3, (byte)(side < 0 && s.R < HubRingRadii[0] ? 11 : s.Spoke));
                }
        }

        // A rectangular hole in the road, three across and four along
        foreach (var (seg, along) in plan.Holes)
        {
            if (seg != s.Id) continue;
            for (int a = along; a < along + 4; a++)
                for (int c = -1; c <= 1; c++)
                {
                    var p = s.World(a, c);
                    if (!InCell(p.X, p.Z) || Here(p.X, p.Z).Kind != TileKind.Floor) continue;
                    ref Tile t = ref Here(p.X, p.Z);
                    t.Kind = TileKind.Pit;
                    t.Under = Unders.HubHole;
                    t.Floor = FloorKind.HubAsphalt;
                }
        }

        // A blind end where the concrete has turned to white tile: the last eight blocks, and the end itself leads on
        foreach (bool high in new[] { false, true })
        {
            if (!plan.TileEnds.Contains((s.Id, high))) continue;
            int end = high ? s.A1 + s.Half : s.A0 - s.Half;
            for (int d = 0; d <= 9; d++)
                for (int c = -s.Half - 1; c <= s.Half + 1; c++)
                {
                    var p = s.World(high ? end + 1 - d : end - 1 + d, c);
                    if (!InCell(p.X, p.Z)) continue;
                    ref Tile t = ref Here(p.X, p.Z);
                    bool wall = d == 0 || c == -s.Half - 1 || c == s.Half + 1;
                    if (wall && t.Kind == TileKind.Wall)
                    {
                        // Tile, and where it gives out, concrete with the tiles beginning (Stack: how far gone)
                        if (d <= 4) t.Pattern = WallPattern.PoolTile;
                        else if (d <= 6) t.Stack = (byte)(7 - d);
                        t.Detail = 0;
                        continue;
                    }
                    if (t.Kind != TileKind.Floor || !s.Inside(p.X, p.Z)) continue;
                    t.Floor = d <= 5 ? FloorKind.PoolTile : t.Floor;
                    t.Overhead = 0;
                    if (d == 1) t.Under = Unders.HubTileEnd;
                }
        }
    }

    // ================= The Tower =================

    /// <summary>
    /// The Tower: a rotunda of pale ashlar (inside radius <see cref="HubTowerInner"/>, its wall out to
    /// <see cref="HubTowerRadius"/>), up to <see cref="HubTowerCeiling"/>. Ten passages run in through its wall from the
    /// ornate doors where the approaches end. Inside: the headless statue in the middle, a spiral stair up the inside of
    /// the wall past four galleries of ornate doors forbidden to wanderers (<see cref="HubTowerGalleries"/>), and the
    /// meeting hall on top (<see cref="HubTowerHall"/>), whose balcony looks out over a black void of storm. The tiles
    /// only say what is where (Zone <see cref="HubZoneTower"/>, the balcony and void's <see cref="HubZoneVoid"/>); the
    /// stair, the galleries and the doors on them are worked out from the geometry by the generator.
    /// </summary>
    public const int HubTowerInner = 20, HubTowerHall = 30, HubTowerCeiling = 35;

    /// <summary>The heights of the galleries round the inside of the Tower.</summary>
    public static readonly int[] HubTowerGalleries = { 8, 14, 20, 26 };

    /// <summary>On a tile's Zone: the balcony and the void beyond it.</summary>
    public const byte HubZoneVoid = 3;

    /// <summary>The angle the Hub's plan is turned by (the ten tunnels lie at this plus 18 + 36k degrees; the balcony at this).</summary>
    public double HubTheta0 => HubRoads.Theta0;

    /// <summary>The direction (unit vector) of tunnel <paramref name="k"/> (0-9) from the Tower, and of its approach.</summary>
    public (double X, double Z) HubSpokeDirection(int k) => HubRoads.Spokes[k];

    /// <summary>
    /// The height of the Tower's spiral stair over a column at an angle (radians, as atan2(dz, dx)) from the middle, if it
    /// passes there, or -1. It starts just past tunnel 1's passage and climbs one block in every block and a half of the
    /// way round, over the band nearest the wall, to the meeting hall.
    /// </summary>
    public int HubStairHeight(double angle)
    {
        double start = HubTheta0 + Math.PI / 10 + 0.16;
        double turned = (angle - start) % (2 * Math.PI);
        if (turned < 0) turned += 2 * Math.PI;
        int h = 1 + (int)Math.Floor(turned * 19 / 1.5);
        return h <= HubTowerHall ? h : -1;
    }

    private void BuildHubTower(Builder b, HubPlan plan, int x0, int z0)
    {
        int ox = HubOriginX, oz = HubOriginZ;
        if (x0 > ox + 44 || x0 + MacroSize < ox - 44 || z0 > oz + 44 || z0 + MacroSize < oz - 44) return;
        double vx = Math.Cos(plan.Theta0), vz = Math.Sin(plan.Theta0);
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = x0 + lx, gz = z0 + lz, dx = gx - ox, dz = gz - oz;
                double r = Math.Sqrt((double)dx * dx + (double)dz * dz);
                if (r >= 44) continue;
                ref Tile t = ref b.At(lx, lz);
                // The balcony, out through the wall of the meeting hall, and the void beyond it
                double along = dx * vx + dz * vz, tang = -dx * vz + dz * vx;
                if (along > 0 && r >= HubTowerInner + 0.5 && r < 41 && Math.Abs(tang) <= 5)
                {
                    bool open = Math.Abs(tang) <= 4 && r < 40 && (r >= HubTowerRadius + 0.5 || Math.Abs(tang) <= 1.6);
                    if (open && t.Kind == TileKind.Wall)
                    {
                        t = new Tile
                        {
                            Kind = TileKind.Floor, Floor = FloorKind.HubMarble, Zone = HubZoneVoid, Height = HubTowerCeiling - 1, Pattern = WallPattern.HubAshlar,
                            Under = r >= 27 ? Unders.HubTowerVoid : (byte)0,
                        };
                        continue;
                    }
                    if (t.Kind == TileKind.Wall && r >= HubTowerRadius + 0.5)
                    {
                        t.Zone = HubZoneVoid;
                        continue;
                    }
                }
                if (r < HubTowerInner + 0.5)
                {
                    // The rotunda's floor: polished marble, an inlaid ring round the statue
                    t = new Tile
                    {
                        Kind = TileKind.Floor, Floor = r >= 6 && r < 7 ? FloorKind.HubMarbleInlay : FloorKind.HubMarble, Zone = HubZoneTower,
                        Height = HubTowerCeiling - 1, Pattern = WallPattern.HubAshlar, Variant = dx == 0 && dz == 0 ? Props.HubStatue : (ushort)0,
                    };
                    continue;
                }
                if (r >= HubTowerRadius + 0.5) continue;
                int k = HubApproachAt(plan, gx, gz, out double off, out _);
                if (k >= 0 && Math.Abs(off) <= 1.5)
                {
                    var (ux, uz) = plan.Spokes[k];
                    if (r >= HubTowerRadius - 0.5)
                    {
                        // An ornate door, two leaves wide, facing out along its approach
                        ArchPier facing = Math.Abs(ux) >= Math.Abs(uz) ? (ux > 0 ? ArchPier.East : ArchPier.West) : (uz > 0 ? ArchPier.South : ArchPier.North);
                        var (rx, rz) = RightOf(facing);
                        bool right = off * (-uz * rx + ux * rz) > 0;
                        t = new Tile { Kind = TileKind.Door, Pattern = WallPattern.HubOrnate, Pier = facing, Stack = (byte)(right ? 1 : 0), Height = HubSideHeight, Zone = HubZoneTower };
                    }
                    else t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.HubMarble, Zone = HubZoneTower, Height = 4, Pattern = WallPattern.HubAshlar };
                    continue;
                }
                t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.HubAshlar, Zone = HubZoneTower };
            }
    }

    /// <summary>Whether a position is inside the Tower (the rotunda and the passages through its wall), not the void.</summary>
    public bool InHubTower(double x, double z)
    {
        double dx = x - (HubOriginX + 0.5), dz = z - (HubOriginZ + 0.5);
        return dx * dx + dz * dz < (HubTowerRadius - 0.5) * (HubTowerRadius - 0.5);
    }

    // ================= The outposts' things =================

    /// <summary>
    /// The M.E.G.'s "Doorstep Carpet" by the Level 11 door: the door register on its stand at the kerb, the doorstep carpet,
    /// the banner and the key cabinet on the wall. Camp Amber's sign by the Level 1 door.
    /// </summary>
    private void PlaceHubOutposts(Builder b, int x0, int z0)
    {
        bool InCell(int x, int z) => x >= x0 && z >= z0 && x < x0 + MacroSize && z < z0 + MacroSize;
        foreach (int level in new[] { 11, 1 })
        {
            if (HubDoorOf(level) is not { } door) continue;
            var (fx, fz) = Step(door.Facing);
            var (rx, rz) = RightOf(door.Facing);
            // Out from the door's wall (1: the sidewalk, 2: the road's edge) and along it to the right
            (int X, int Z) At(int outward, int right) => (door.X + fx * outward + rx * right, door.Z + fz * outward + rz * right);
            void Prop((int X, int Z) p, ushort prop)
            {
                if (!InCell(p.X, p.Z)) return;
                ref Tile t = ref b.At(p.X - x0, p.Z - z0);
                if (t.Kind != TileKind.Floor || t.Floor == FloorKind.HubSidewalk || t.Variant != 0 || t.Overhead != 0 || t.Under != 0) return;
                t.Variant = prop;
                t.Pier = door.Facing;
            }
            void Hang((int X, int Z) p, byte kind, byte rel)
            {
                if (!InCell(p.X, p.Z)) return;
                ref Tile t = ref b.At(p.X - x0, p.Z - z0);
                if (t.Kind != TileKind.Floor || t.Detail != 0) return;
                t.Detail = kind;
                t.Depth = rel;
                t.Pier = door.Facing;
            }
            if (level == 11)
            {
                Prop(At(2, 5), Props.HubRegister);
                Prop(At(2, 8), Props.HubDoormat);
                Hang(At(1, 6), HubWallBanner, 3);
                Hang(At(1, 10), HubWallCabinet, 2);
            }
            else Prop(At(2, 6), Props.HubAmberSign);
        }
    }

    // ================= Outposts =================

    /// <summary>
    /// Where the Hub's two outposts keep a wanderer, if one stands in this cell: the M.E.G.'s "Doorstep Carpet" a few
    /// steps from the Level 11 door (canon's "public Hub Route" by the Level 11 entrance), and Camp Amber's by the Level 1
    /// door (Camp Amber came from Level 1).
    /// </summary>
    private (int X, int Z)? HubWandererSite(int mx, int mz)
    {
        foreach (int level in new[] { 11, 1 })
        {
            if (HubDoorOf(level) is not { } door) continue;
            var (fx, fz) = Step(door.Facing);
            var (rx, rz) = RightOf(door.Facing);
            int x = door.X + fx + rx * 8, z = door.Z + fz + rz * 8;
            if (StandingSpotNear(x, z, 6) is not { } spot || MacroOf(spot.X) != mx || MacroOf(spot.Z) != mz) continue;
            return spot;
        }
        return null;
    }

    /// <summary>Where the M.E.G.'s outpost wanderer keeps (the one who sells Level Keys), or null if the Hub has no Level 11 door.</summary>
    public (int X, int Z)? HubMegSite()
    {
        if (HubDoorOf(11) is not { } door) return null;
        var (fx, fz) = Step(door.Facing);
        var (rx, rz) = RightOf(door.Facing);
        return StandingSpotNear(door.X + fx + rx * 8, door.Z + fz + rz * 8, 6);
    }

    // ================= The white-tile ends and Level 37's asphalt ends: arriving beside each other =================

    /// <summary>
    /// Where someone coming in by one of Level 37's asphalt corridor ends is put down: on the white tile of one of the
    /// Hub's five tile ends (picked by <paramref name="key"/>), the step before the end that leads back. (No ordinary
    /// arrival can be there: they are out in the Far Tunnels, and not on a sidewalk.)
    /// </summary>
    public (int X, int Z)? HubTileEndArrival(ulong key)
    {
        HubPlan plan = HubRoads;
        if (plan.TileEnds.Count == 0) return null;
        var ends = new List<(int Seg, bool High)>(plan.TileEnds);
        ends.Sort((p, q) => p.Seg != q.Seg ? p.Seg.CompareTo(q.Seg) : p.High.CompareTo(q.High));
        var (id, high) = ends[(int)(key % (ulong)ends.Count)];
        HubSeg s = plan.Segs[id];
        int end = high ? s.A1 + s.Half : s.A0 - s.Half;
        var (x, z) = s.World(high ? end - 1 : end + 1, 0);
        return IsArrivalSpot(TileAt(x, z)) ? (x, z) : null;
    }

    /// <summary>Where someone coming out of a white-tile end arrives in Level 37: on the asphalt of a dry corridor's end.</summary>
    public static bool IsPoolAsphaltSpot(Tile t) => IsArrivalSpot(t) && t.Floor == FloorKind.HubAsphalt;

    // ================= The ways in from Levels 1 and 2 =================

    private const ulong SaltHubLevel1 = 0x1720, SaltHubLevel2 = 0x1721;

    /// <summary>
    /// Level 1: in the outer half of its maintenance halls, one hall block in 250 has a grey door with the Hub's carved
    /// sigil over it in the middle of its north wall, facing the corridor; chalk arrows along the corridor point to it.
    /// Called after the halls are laid out and dressed; its own salt, so nothing else moves.
    /// </summary>
    private void MarkHubDoorInLevel1(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        int bx0 = Hashing.FloorDiv(x0 - HallOffset - 2 - 24, HallGrid), bx1 = Hashing.FloorDiv(x0 + MacroSize + 24 - HallOffset - 2, HallGrid);
        int bz0 = Hashing.FloorDiv(z0 - HallOffset - 2, HallGrid), bz1 = Hashing.FloorDiv(z0 + MacroSize - HallOffset - 2, HallGrid) + 1;
        for (int bz = bz0; bz <= bz1; bz++)
            for (int bx = bx0; bx <= bx1; bx++)
            {
                if (Hashing.Unit(Hashing.Hash(seed, bx, bz, SaltHubLevel1)) >= 1 / 250.0) continue;
                // The middle of the block's north wall, and the corridor in front of it
                int dx = bx * HallGrid + HallOffset + 2 + 6, dz = bz * HallGrid + HallOffset + 2;
                int dmx = MacroOf(dx), dmz = MacroOf(dz);
                if (LevelAt(dmx, dmz) != 1 || !IsLevel1Corridors(dmx, dmz) || RingFraction(dx, dz, 1) < 0.5) continue;
                Tile[] plan = HallBlockPlan(bx, bz);
                if (plan[6].Kind != TileKind.Wall || LevelAt(MacroOf(dx), MacroOf(dz - 1)) != 1) continue;
                if (dx >= x0 && dx < x0 + MacroSize && dz >= z0 && dz < z0 + MacroSize)
                {
                    ref Tile wall = ref b.At(dx - x0, dz - z0);
                    if (wall.Kind == TileKind.Wall)
                    {
                        wall.Pattern = WallPattern.WhiteBlock;
                        wall.Variant = Decor.HubEntranceDoor;
                        wall.Pier = ArchPier.North;
                    }
                }
                // Chalk arrows on the same wall, along the corridor, pointing to it (facing the wall, west is on the right)
                foreach (int off in new[] { -18, -12, -6, 6, 12, 18 })
                {
                    int ax = dx + off, az = dz - 1;
                    if (ax < x0 || ax >= x0 + MacroSize || az < z0 || az >= z0 + MacroSize) continue;
                    ref Tile floor = ref b.At(ax - x0, az - z0);
                    if (floor.Kind != TileKind.Floor || az + 1 >= z0 + MacroSize || b.At(ax - x0, az + 1 - z0).Kind != TileKind.Wall) continue;
                    floor.Chalk = ChalkBits.Make(ArchPier.South, off < 0 ? 0 : 1);
                }
            }
    }

    /// <summary>Level 2: one locked steel door in forty is a door into the Hub, with a chalk circle on the wall beside it.</summary>
    private void MarkHubDoorsInLevel2(Builder b, int mx, int mz)
    {
        for (int lz = 1; lz < MacroSize - 1; lz++)
            for (int lx = 1; lx < MacroSize - 1; lx++)
            {
                ref Tile door = ref b.At(lx, lz);
                if (door.Kind != TileKind.Door) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                // Only of those that would be locked (the hub plan): one that opens leads where it always did
                if (Thresholds.ThresholdNetwork.TunnelDoorOpens(seed, gx, gz)) continue;
                if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltHubLevel2)) >= 1 / 40.0) continue;
                door.Under = Unders.HubEntrance;
                // The floor in front of it, and the tile beside that, whose wall gets the circle
                var (fx, fz) = Step(door.Pier);
                var (rx, rz) = RightOf(door.Pier);
                int cx = lx + fx + rx, cz = lz + fz + rz;
                if (cx < 0 || cz < 0 || cx >= MacroSize || cz >= MacroSize) continue;
                ref Tile beside = ref b.At(cx, cz);
                if (beside.Kind == TileKind.Floor && b.At(cx - fx, cz - fz).Kind == TileKind.Wall)
                    beside.Chalk = ChalkBits.Make(Opposite37(door.Pier), 3);
            }
    }

    /// <summary>Which of the level's props (<see cref="Props.HubFirst"/> to <see cref="Props.HubLast"/>) are walked through rather than around.</summary>
    private static bool HubWalkThrough(ushort variant) => variant == Props.HubDoormat;

    // ================= What it is like =================

    /// <summary>Cold: the jet fans are still, yet the air moves. Colder out where the lamps die; milder in the Tower.</summary>
    private float HubTemperature(int x, int y, int z, int floorY)
    {
        double r = HubDistance(x, z);
        return r < HubRoundabout - HubMainHalf - 1 ? 14f : r < HubKnownRadius ? 6f : 2f;
    }

    /// <summary>A nexus that knows the intent of all who enter: steady in the Crossroads, less so out in the dark.</summary>
    private float HubStability(double x, double y, double z, int floorY, float drift)
    {
        double r = HubDistance((int)Math.Floor(x), (int)Math.Floor(z));
        return r < HubRoundabout - HubMainHalf - 1 ? 1.2f : r < HubKnownRadius ? 1.3f : 1.0f + 0.1f * drift;
    }
}
