using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 23's ways in and out, as laid out (docs/design/experimental-levels/LINKS.md, 23-plan.md "Links"); the thresholds
/// themselves are in ThresholdNetwork.L23.cs. This file is the level's own.
/// <list type="bullet">
/// <item><b>In, from Level 37</b> (Wikidot: "huge hollow green-barked trees in Levels 37 and 47"): now and then a huge
/// tree of green bark grows up through the Poolrooms' tiles, floor and ceiling, its roots breaking the tile round its foot;
/// at most one to a square of 16 by 16 of the Poolrooms' plan blocks (1536 blocks a side), in three of five of them, in a
/// hall with room round it. Climb into its hollow and you climb out of a hollow trunk in the Garden's forest: one-way.</item>
/// <item><b>Out, from Base Seedling</b>: the camp's hollow tree. The lore's way leads to Level 135, which this mod does not
/// have: it stands in for it with one of those trees in Level 37, the one nearest the Poolrooms' middle, and the way is
/// two-way (our substitution).</item>
/// <item><b>Out, from the Heart of Water</b>: in the middle of the pool's bed a well goes on down, deeper than the bed; at
/// its bottom the reservoir takes you, and you come up in the open sea of Level 7 (Wikidot). One-way.</item>
/// <item>Where those from Level 37 come out: a hollow trunk in the forest, about one of the thick trunks in twelve,
/// hollowed out from its foot to some nine blocks up, with a mouth between two buttresses.</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The links' layout salts (0x2860-0x286F, of the level's 0x2800-0x28BF).</summary>
    private const ulong SaltL23PoolTree = 0x2860, SaltL23PoolSite = 0x2861, SaltL23Hollow = 0x2862;

    // ================= The Heart of Water's well =================

    /// <summary>The well in the middle of the pool's bed: its radius, and its floor (above the level's floor; the bed round it is at -14 at most).</summary>
    public const double L23WellRadius = 3.5;
    public const int L23WellFloor = -19;

    // ================= Hollow trunks in the forest =================

    /// <summary>Of the thick trunks (radius 3.4 or more, whole, not forked, with no sentry), how many are hollow.</summary>
    private const double L23HollowChance = 0.08;

    /// <summary>A hollow trunk's bark is this thick; its hollow goes up this far over its foot; its mouth is this high and half as wide.</summary>
    private const double L23HollowWall = 1.3, L23MouthHalf = 1.1;
    private const int L23HollowHigh = 9, L23MouthHigh = 3;

    /// <summary>Whether a trunk is hollow, and which way its mouth faces (between two of its buttresses).</summary>
    private void L23MaybeHollow(ref L23Trunk t, int i, int j)
    {
        if (!t.Exists || t.Giant || t.Sentry || t.Snag || t.ForkAt != 0 || t.R < 3.4) return;
        ulong h = Hashing.Hash(seed, i, j, SaltL23Hollow);
        if (Hashing.Unit(h) >= L23HollowChance) return;
        int k = (int)(Hashing.Mix(h) % (ulong)t.Lobes);
        t.Hollow = true;
        t.MouthA = (Math.PI - t.Phase + k * Math.PI * 2) / t.Lobes;
    }

    /// <summary>
    /// Whether a point inside a hollow trunk's bark (<paramref name="depth"/> in from it) at a height is hollowed out: deeper
    /// than the bark's thickness, over this column's ground and up to <see cref="L23HollowHigh"/> over the trunk's foot; or in
    /// the mouth, a slot from the middle out between two buttresses, <see cref="L23MouthHigh"/> high over the ground.
    /// </summary>
    private static bool L23Hollowed(in L23Trunk t, double px, double pz, int rel, int floor, double depth)
    {
        if (rel <= floor || rel > t.Base + L23HollowHigh) return false;
        if (depth > L23HollowWall) return true;
        if (rel > floor + L23MouthHigh) return false;
        var (lx, lz) = L23Lean(t, rel);
        double dx = px - (t.X + lx), dz = pz - (t.Z + lz), ca = Math.Cos(t.MouthA), sa = Math.Sin(t.MouthA);
        return dx * ca + dz * sa > 0 && Math.Abs(dz * ca - dx * sa) < L23MouthHalf;
    }

    /// <summary>Whether a point is in a hollow trunk's hollow or mouth, or the few blocks in front of its mouth (where its roots do not go).</summary>
    private static bool L23InHollowsWay(in L23Trunk t, double px, double pz)
    {
        var (lx, lz) = L23Lean(t, t.Base + 1);
        double dx = px - (t.X + lx), dz = pz - (t.Z + lz), ca = Math.Cos(t.MouthA), sa = Math.Sin(t.MouthA);
        if (dx * dx + dz * dz < t.R * t.R) return true;
        double along = dx * ca + dz * sa;
        return along > 0 && along < t.R + 4 && Math.Abs(dz * ca - dx * sa) < L23MouthHalf + 1;
    }

    /// <summary>Whether a column of the forest floor is inside a hollow trunk or in its mouth (at the height over its ground where one walks).</summary>
    private bool L23InHollowTrunk(int gx, int gz, int ground)
    {
        double px = gx + 0.5, pz = gz + 0.5;
        int i0 = Hashing.FloorDiv(gx, L23Pitch), j0 = Hashing.FloorDiv(gz, L23Pitch);
        L23Trunk[] around = L23TrunksAround(i0, j0);
        for (int dj = -2; dj <= 2; dj++)
            for (int di = -2; di <= 2; di++)
            {
                L23Trunk t = around[(dj + 2) * 6 + di + 2];
                if (!t.Exists || !t.Hollow) continue;
                if (L23InTrunk(t, px, pz, ground + 1, out double depth) && L23Hollowed(t, px, pz, ground + 1, ground, depth)) return true;
            }
        return false;
    }

    private List<(int X, int Z, double MouthA, double R)> l23Hollows;

    /// <summary>
    /// The hollow trunks of the forest someone can climb out of (their hollow on the forest floor, not over a cavern), by
    /// lattice order: the middle of each at its foot, the way its mouth faces, and its radius.
    /// </summary>
    public IReadOnlyList<(int X, int Z, double MouthA, double R)> L23HollowTrunks()
    {
        if (l23Hollows != null) return l23Hollows;
        var list = new List<(int, int, double, double)>();
        int reach = L23Reach + 40;
        int i0 = Hashing.FloorDiv(L23MidX - reach, L23Pitch), i1 = Hashing.FloorDiv(L23MidX + reach, L23Pitch);
        int j0 = Hashing.FloorDiv(L23MidZ - reach, L23Pitch), j1 = Hashing.FloorDiv(L23MidZ + reach, L23Pitch);
        for (int j = j0; j <= j1; j++)
            for (int i = i0; i <= i1; i++)
            {
                L23Trunk t = L23TrunkAt(i, j);
                if (!t.Exists || !t.Hollow) continue;
                var (lx, lz) = L23Lean(t, t.Base + 1);
                int x = (int)Math.Floor(t.X + lx), z = (int)Math.Floor(t.Z + lz);
                if (L23FromMid(x, z) > L23Reach - 10 || LevelAt(MacroOf(x), MacroOf(z)) != Level23) continue;
                if (TileAt(x, z).Under != Unders.L23HollowTrunk) continue;
                list.Add((x, z, t.MouthA, t.R));
            }
        Interlocked.CompareExchange(ref l23Hollows, list, null);
        return l23Hollows;
    }

    /// <summary>A place to climb out of a hollow trunk (chosen by key among them): on the forest floor right outside its mouth.</summary>
    public (int X, int Z)? L23HollowArrival(ulong key)
    {
        var hollows = L23HollowTrunks();
        if (hollows.Count == 0) return null;
        var h = hollows[(int)(Hashing.Mix(key) % (ulong)hollows.Count)];
        // The open floor nearest the trunk (round 3 puts arrivals in the open, not nose to the bark; the hollow stays in sight)
        for (int d = 1; d <= 20; d++)
        {
            (int X, int Z)? best = null;
            int bestSq = int.MaxValue;
            for (int dz = -d; dz <= d; dz++)
                for (int dx = -d; dx <= d; dx++)
                {
                    if (Math.Abs(dx) != d && Math.Abs(dz) != d) continue;
                    Tile t = TileAt(h.X + dx, h.Z + dz);
                    if (t.Level != Level23 || !IsL23ArrivalSpot(t) || dx * dx + dz * dz >= bestSq) continue;
                    best = (h.X + dx, h.Z + dz);
                    bestSq = dx * dx + dz * dz;
                }
            if (best != null) return best;
        }
        return FindArrival(Level23, key, t => t.Under == Unders.L23HollowTrunk && t.Level == Level23, near: (MacroOf(h.X), MacroOf(h.Z)));
    }

    // ================= Base Seedling's hollow tree =================

    /// <summary>A place to come home to Base Seedling: on the camp's floor in front of the hollow tree's doorway.</summary>
    public (int X, int Z)? L23SeedlingArrival(ulong key)
    {
        var s = L23SeedlingAt;
        return FindArrival(Level23, key, t => t.Under == Unders.L23SeedlingDoor && t.Level == Level23,
            spot: t => IsArrivalSpot(t) && t.Zone == L23Seedling, checkEscape: false, near: (MacroOf(s.X), MacroOf(s.Z + 4)));
    }

    // ================= Level 7: the sea the reservoir comes out in =================

    /// <summary>A place to come up in Level 7's open sea (out of the Heart of Water's well): open water at least eight deep, nothing afloat.</summary>
    public (int X, int Z)? L23SeaArrival(ulong key) =>
        FindArrival(7, key, spot: t => t.Kind == TileKind.Water && t.Zone == 0 && t.Under == 0 && t.Stack == 0 && t.Depth >= 8 && !t.Sealed,
            checkEscape: false);

    // ================= The hollow trees in Level 37 =================

    /// <summary>The Poolrooms' plan blocks are grouped in squares of this many a side, each with at most one hollow tree.</summary>
    public const int L23TreeSquare = 16;

    /// <summary>How many of those squares have one (where it finds room).</summary>
    private const double L23TreeChance = 0.6;

    /// <summary>A hollow tree in the Poolrooms: its middle (block), its bark's outer radius, the way its mouth faces (radians, along x then z), its plan block.</summary>
    public sealed class L23PoolTree
    {
        public bool Valid;
        public int X, Z, Bi, Bj;
        public double R, MouthA;
    }

    private PlanCache<L23PoolTree> l23PoolTrees;

    /// <summary>The plan block of a square that may hold a tree (whether it does is the site's to say).</summary>
    private (int Bi, int Bj)? L23TreeBlock(int si, int sj)
    {
        ulong h = Hashing.Hash(seed, si, sj, SaltL23PoolTree);
        if (Hashing.Unit(h) >= L23TreeChance) return null;
        // (In the middle half of the square each way, so two trees are never much nearer than half a square)
        const int span = L23TreeSquare / 2;
        return (si * L23TreeSquare + span / 2 + (int)(Hashing.Mix(h) % span), sj * L23TreeSquare + span / 2 + (int)(Hashing.Mix(h + 1) % span));
    }

    /// <summary>The hollow tree of a square of plan blocks (Valid false where it has none).</summary>
    public L23PoolTree L23PoolTreeOfSquare(int si, int sj) =>
        LazyInitializer.EnsureInitialized(ref l23PoolTrees, () => new PlanCache<L23PoolTree>(64, PlanL23PoolTree)).Get(si, sj);

    /// <summary>The hollow tree in a plan block of the Poolrooms, if it has one.</summary>
    public L23PoolTree L23PoolTreeIn(int bi, int bj)
    {
        int si = Hashing.FloorDiv(bi, L23TreeSquare), sj = Hashing.FloorDiv(bj, L23TreeSquare);
        if (L23TreeBlock(si, sj) is not { } at || at.Bi != bi || at.Bj != bj) return null;
        L23PoolTree tree = L23PoolTreeOfSquare(si, sj);
        return tree.Valid ? tree : null;
    }

    /// <summary>The hollow tree whose plan block holds a block position (the generator's question), if any.</summary>
    public L23PoolTree L23PoolTreeAt(int gx, int gz)
    {
        var (bi, bj) = PoolBlockOf(gx, gz);
        return L23PoolTreeIn(bi, bj);
    }

    /// <summary>Whether a floor tile of a plan could stand under a tree or round its foot: dry or a step deep, under a high ceiling, with nothing on it or under it.</summary>
    private static bool L23TreeRoom(in Tile t) =>
        t.Kind == TileKind.Floor && t.Under == 0 && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Stair == 0 && !t.Sealed
        && t.Depth <= 1 && t.Height >= 6 && t.Zone == 0 && t.Floor != FloorKind.OfficeCarpet && t.Floor != FloorKind.PoolDeep;

    /// <summary>Offsets within a disc of radius 9, nearest first (for how much room a spot has round it).</summary>
    private static readonly (int Dx, int Dz, double D)[] L23Around = MakeL23Around();

    private static (int, int, double)[] MakeL23Around()
    {
        var list = new List<(int, int, double)>();
        for (int dz = -9; dz <= 9; dz++)
            for (int dx = -9; dx <= 9; dx++)
            {
                double d = Math.Sqrt(dx * dx + dz * dz);
                if (d <= 9) list.Add((dx, dz, d));
            }
        list.Sort((a, b) => a.Item3.CompareTo(b.Item3));
        return list.ToArray();
    }

    /// <summary>
    /// Plans the tree of a square: in its plan block, the floor with the most room round it (a hall rather than a corridor,
    /// in the light where it can be), the whole of the tree and its roots inside one cell, and its mouth toward the most
    /// open way.
    /// </summary>
    private L23PoolTree PlanL23PoolTree(int si, int sj)
    {
        var tree = new L23PoolTree();
        if (L23TreeBlock(si, sj) is not { } at) return tree;
        int bi = at.Bi, bj = at.Bj;
        // In the Poolrooms, and not in the Sanguine Reservoir
        int gx0 = PoolOriginX + bi * PoolBlock, gz0 = PoolOriginZ + bj * PoolBlock;
        if (LevelAt(MacroOf(gx0 + PoolBlock / 2), MacroOf(gz0 + PoolBlock / 2)) != Poolrooms || IsReservoirBlock(bi, bj)) return tree;
        ulong h = Hashing.Hash(seed, si, sj, SaltL23PoolSite);
        double r = 3.6 + 0.8 * Hashing.Unit(h);
        int margin = (int)Math.Ceiling(r + 3);
        Tile[] plan = PoolPlan(bi, bj);
        bool Room(int u, int v) => u >= 0 && v >= 0 && u < PoolBlock && v < PoolBlock && L23TreeRoom(plan[v * PoolBlock + u]);

        int bestU = -1, bestV = -1;
        double bestScore = -1;
        double need = r + 1.5;
        for (int v = 0; v < PoolBlock; v++)
            for (int u = 0; u < PoolBlock; u++)
            {
                // (The plan blocks count from a cell corner, so u and v modulo a cell are the cell's own)
                int lx = u % MacroSize, lz = v % MacroSize;
                if (lx < margin || lz < margin || lx >= MacroSize - margin || lz >= MacroSize - margin) continue;
                if (!Room(u, v)) continue;
                double clear = 9.5;
                foreach (var (dx, dz, d) in L23Around)
                {
                    if (Room(u + dx, v + dz)) continue;
                    clear = d;
                    break;
                }
                if (clear <= need) continue;
                double score = clear + (plan[v * PoolBlock + u].Detail == PoolDark ? 0 : 2.5)
                    + 0.01 * Hashing.Unit(Hashing.Hash(seed, gx0 + u, gz0 + v, SaltL23PoolSite));
                if (score > bestScore) { bestScore = score; bestU = u; bestV = v; }
            }
        if (bestU < 0) return tree;
        int x = gx0 + bestU, z = gz0 + bestV, mx = MacroOf(x), mz = MacroOf(z);
        // Never in a cell at the Poolrooms' edge (those are solid tile)
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Poolrooms) return tree;
        // The mouth: toward the longest run of open floor of the eight ways
        int bestRun = -1;
        double mouth = 0;
        for (int k = 0; k < 8; k++)
        {
            double a = k * Math.PI / 4, ca = Math.Cos(a), sa = Math.Sin(a);
            int run = 0;
            for (int d = (int)Math.Ceiling(r + 0.5); d < r + 14; d++)
            {
                if (!Room(bestU + (int)Math.Round(ca * d), bestV + (int)Math.Round(sa * d))) break;
                run++;
            }
            if (run > bestRun) { bestRun = run; mouth = a; }
        }
        tree.Valid = true;
        tree.X = x;
        tree.Z = z;
        tree.Bi = bi;
        tree.Bj = bj;
        tree.R = r;
        tree.MouthA = mouth;
        return tree;
    }

    /// <summary>What part of a Poolrooms tree a position (offset from its middle) is: 0 none, or one of the tree's Unders (seedling: Base Seedling's tree).</summary>
    public static ushort L23PoolTreePart(L23PoolTree tree, int dx, int dz, bool seedling)
    {
        double d = Math.Sqrt(dx * dx + dz * dz), r = tree.R;
        if (d >= r + 2.5) return 0;
        double ca = Math.Cos(tree.MouthA), sa = Math.Sin(tree.MouthA);
        double along = dx * ca + dz * sa, across = dz * ca - dx * sa;
        bool slot = along > 0 && Math.Abs(across) < 1.2;
        if (d < r - 1.5) return seedling ? Unders.L23PoolSeedHollow : Unders.L23PoolHollow;
        if (d < r) return slot ? (seedling ? Unders.L23PoolSeedMouth : Unders.L23PoolMouth) : Unders.L23PoolBark;
        // Round its foot, roots and broken tile, but for the way out of its mouth (kept clear to stand on)
        return along > 0 && Math.Abs(across) < 2.6 ? (ushort)0 : Unders.L23PoolRoots;
    }

    /// <summary>Whether a position round a Poolrooms tree's foot (offset from its middle) lies on one of its three roots, which crawl out over the tile away from its mouth.</summary>
    public static bool L23PoolRootAt(L23PoolTree tree, int dx, int dz)
    {
        for (int k = 1; k <= 3; k++)
        {
            double a = tree.MouthA + k * Math.PI / 2 + 0.25 * Math.Sin(tree.X * 0.7 + tree.Z * 1.3 + k);
            double ca = Math.Cos(a), sa = Math.Sin(a);
            double along = dx * ca + dz * sa, across = dz * ca - dx * sa;
            if (along > 0 && Math.Abs(across) < 0.75) return true;
        }
        return false;
    }

    private L23PoolTree l23SeedlingTree;
    private static readonly L23PoolTree L23NoTree = new();

    /// <summary>
    /// Base Seedling's way home: the Poolrooms tree nearest the Poolrooms' middle (null in a world with none). Its hollow
    /// leads to the camp's hollow tree and back; every other tree's leads one way, into the forest.
    /// </summary>
    public L23PoolTree L23SeedlingTree
    {
        get
        {
            if (l23SeedlingTree == null)
            {
                L23PoolTree best = L23NoTree;
                int cx = PoolCentreX * MacroSize + MacroSize / 2, cz = PoolCentreZ * MacroSize + MacroSize / 2;
                var (bi0, bj0) = PoolBlockOf(cx, cz);
                int si0 = Hashing.FloorDiv(bi0, L23TreeSquare), sj0 = Hashing.FloorDiv(bj0, L23TreeSquare);
                int squares = PoolRadius * MacroSize / (PoolBlock * L23TreeSquare) + 1;
                long bestD = long.MaxValue;
                int foundRing = -1;
                for (int ring = 0; ring <= squares; ring++)
                {
                    // (A nearer tree may lie in the ring past the first one found)
                    if (foundRing >= 0 && ring > foundRing + 1) break;
                    for (int sj = sj0 - ring; sj <= sj0 + ring; sj++)
                        for (int si = si0 - ring; si <= si0 + ring; si++)
                        {
                            if (Math.Max(Math.Abs(si - si0), Math.Abs(sj - sj0)) != ring) continue;
                            L23PoolTree t = L23PoolTreeOfSquare(si, sj);
                            if (!t.Valid) continue;
                            long d = (long)(t.X - cx) * (t.X - cx) + (long)(t.Z - cz) * (t.Z - cz);
                            if (d < bestD) { bestD = d; best = t; }
                            if (foundRing < 0) foundRing = ring;
                        }
                }
                Interlocked.CompareExchange(ref l23SeedlingTree, best, null);
            }
            return l23SeedlingTree.Valid ? l23SeedlingTree : null;
        }
    }

    /// <summary>The Poolrooms' middle and radius in blocks (for the harness and the showcase).</summary>
    public (int X, int Z, int R) L23PoolroomsDisc => (PoolCentreX * MacroSize + MacroSize / 2, PoolCentreZ * MacroSize + MacroSize / 2, PoolRadius * MacroSize);

    /// <summary>Whether a Poolrooms tree is Base Seedling's way home.</summary>
    public bool L23IsSeedlingTree(L23PoolTree tree) => L23SeedlingTree is { } s && s.X == tree.X && s.Z == tree.Z;

    /// <summary>A place to come out in the Poolrooms from Base Seedling: right outside the mouth of its tree there.</summary>
    public (int X, int Z)? L23SeedlingTreeArrival(ulong key)
    {
        if (L23SeedlingTree is not { } tree) return null;
        return FindArrival(Poolrooms, key, t => t.Under == Unders.L23PoolSeedMouth && t.Level == Poolrooms, near: (MacroOf(tree.X), MacroOf(tree.Z)));
    }

    /// <summary>
    /// Marks a hollow tree in a cell of Level 37 (WorldLayout.ExpLinks.cs; its blocks: WorldGenerator.L23.Links.cs): its bark
    /// is wall, its hollow and mouth dry floor, the tile round its foot taken by its roots. It only ever takes tiles its
    /// plan found free.
    /// </summary>
    partial void L23Entrances(Builder b, int mx, int mz)
    {
        if (b.Level != Poolrooms) return;
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        var (bi, bj) = PoolBlockOf(x0, z0);
        if (L23PoolTreeIn(bi, bj) is not { } tree || MacroOf(tree.X) != mx || MacroOf(tree.Z) != mz) return;
        bool seedling = L23IsSeedlingTree(tree);
        int m = (int)Math.Ceiling(tree.R + 2.5);
        for (int dz = -m; dz <= m; dz++)
            for (int dx = -m; dx <= m; dx++)
            {
                ushort part = L23PoolTreePart(tree, dx, dz, seedling);
                if (part == 0) continue;
                int lx = tree.X + dx - x0, lz = tree.Z + dz - z0;
                if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor || t.Under != 0 || t.Variant != 0 || t.SupplyBox) continue;
                t.Under = part;
                if (part == Unders.L23PoolBark)
                {
                    t.Kind = TileKind.Wall;
                    t.Pattern = WallPattern.PoolTile;
                }
                else if (part != Unders.L23PoolRoots) t.Depth = 0;
            }
    }
}
