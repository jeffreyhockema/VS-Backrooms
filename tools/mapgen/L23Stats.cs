using System;
using System.Diagnostics;
using System.Linq;
using System.Text;
using Backrooms.Worldgen;

/// <summary>Level 23's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 23stats: the region (its cells, how long they take), the share of its tiles in each zone, the special places (the
    /// Heart of Water, Base Seedling, the four ruins: where they are, and that each is its own zone), how many glow rooms
    /// there are and whether every tunnel comes out on open forest floor. 23map: the region as text, one character per 6
    /// blocks (# trunks and tangle, . forest, o glow rooms, = tunnels, S Seedling, R ruins, ~ and h the Heart of Water).
    /// </summary>
    static bool L23Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "23map") { L23Map(layout); return true; }
        if (mode == "23links") { L23Links(layout); return true; }
        if (mode != "23stats") return false;
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }

        int mx0 = WorldLayout.MacroOf(layout.L23MidX), mz0 = WorldLayout.MacroOf(layout.L23MidZ);
        Console.WriteLine($"middle (Heart of Water) {layout.L23MidX},{layout.L23MidZ} (cell {mx0},{mz0})");
        var s = layout.L23SeedlingAt;
        Console.WriteLine($"Base Seedling {s.X},{s.Z} r {s.R}");
        for (int k = 0; k < 4; k++)
        {
            var r = layout.L23RuinAt(k);
            Console.WriteLine($"ruin {(WorldLayout.L23RuinKind)k} {r.X},{r.Z} r {r.R}");
        }

        var zones = new long[10];
        long walls = 0, all = 0, boxes = 0, tents = 0;
        int cells = 0;
        var sw = Stopwatch.StartNew();
        for (int mz = mz0 - 16; mz <= mz0 + 16; mz++)
            for (int mx = mx0 - 16; mx <= mx0 + 16; mx++)
            {
                if (layout.LevelAt(mx, mz) != WorldLayout.Level23) continue;
                cells++;
                foreach (Tile t in layout.BuildMacro(mx, mz))
                {
                    all++;
                    zones[Math.Min(9, (int)t.Zone)]++;
                    if (t.Kind == TileKind.Wall && t.Zone != WorldLayout.L23RimZone) walls++;
                    if (t.SupplyBox) boxes++;
                    if (t.Variant == Props.CampTent) tents++;
                }
            }
        double ms = sw.Elapsed.TotalMilliseconds / Math.Max(1, cells);
        Console.WriteLine($"region: {cells} cells, {ms:0.0} ms a cell");
        string[] names = { "none", "forest", "glow", "tunnel", "seedling", "ruin", "core", "7", "8", "tangle" };
        Console.WriteLine("tiles: " + string.Join(", ", Enumerable.Range(0, 10).Where(z => zones[z] > 0).Select(z => $"{names[z]} {zones[z] * 100.0 / all:0.0}%")));
        long forest = zones[WorldLayout.L23Surface];
        Console.WriteLine($"trunks and roots in the way: {walls * 100.0 / Math.Max(1, forest):0.0}% of the forest's tiles; supply boxes {boxes}; tent tiles {tents}");
        if (zones[0] > 0) Bad($"{zones[0]} tiles of no zone");
        if (zones[WorldLayout.L23Seedling] == 0) Bad("no Base Seedling");
        if (zones[WorldLayout.L23Ruin] == 0) Bad("no ruins");
        if (zones[WorldLayout.L23Core] == 0) Bad("no Heart of Water");
        if (tents != 12) Bad($"{tents} tent tiles, not 12");

        // The special places: their middles are theirs
        void Place(string name, int x, int z, byte zone)
        {
            Tile t = layout.TileAt(x, z);
            if (t.Zone != zone) Bad($"{name} is zone {t.Zone}");
        }
        Place("Base Seedling (by the hollow tree)", s.X, s.Z + 6, WorldLayout.L23Seedling);
        for (int k = 0; k < 4; k++)
        {
            var r = layout.L23RuinAt(k);
            Place($"ruin {k}'s plaza", r.X + 15, r.Z, WorldLayout.L23Ruin);
        }
        Place("the Heart of Water", layout.L23MidX, layout.L23MidZ, WorldLayout.L23Core);

        // The caverns and their tunnels: each tunnel's mouth on open forest floor
        int glow = 0, tunnels = 0, blocked = 0;
        var seen = new System.Collections.Generic.HashSet<(int, int)>();
        for (int z = layout.L23MidZ - 330; z <= layout.L23MidZ + 330; z += 8)
            for (int x = layout.L23MidX - 330; x <= layout.L23MidX + 330; x += 8)
            {
                if (!layout.L23Cave(x, z, out _, out _, out WorldLayout.L23Cavern c) || !seen.Add((c.X, c.Z))) continue;
                if (c.Kind == WorldLayout.L23CaveKind.Glow) glow++;
                for (int m = 0; m < c.Tunnels; m++)
                {
                    tunnels++;
                    WorldLayout.L23Passage p = c.Tunnel(m);
                    int bx = (int)Math.Floor(p.Bx), bz = (int)Math.Floor(p.Bz);
                    Tile t = layout.TileAt(bx, bz);
                    if (t.Kind == TileKind.Wall || t.Zone == WorldLayout.L23RimZone)
                    {
                        blocked++;
                        Console.WriteLine($"  tunnel mouth in a wall at {bx},{bz} ({c.Kind} at {c.X},{c.Z})");
                    }
                }
            }
        Console.WriteLine($"caverns: {seen.Count} ({glow} glow rooms), {tunnels} tunnels, {blocked} mouths in a wall");
        if (glow < 10) Bad($"only {glow} glow rooms");
        if (blocked > tunnels / 10) Bad($"{blocked} tunnel mouths blocked");
        Console.WriteLine(bad == 0 ? "23stats: ok" : $"23stats: {bad} problems");
        return true;
    }

    static void L23Map(WorldLayout layout)
    {
        const int step = 6, reach = 336;
        var sb = new StringBuilder();
        for (int z = layout.L23MidZ - reach; z <= layout.L23MidZ + reach; z += step)
        {
            for (int x = layout.L23MidX - reach; x <= layout.L23MidX + reach; x += step)
            {
                if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.Level23) { sb.Append(' '); continue; }
                Tile t = layout.TileAt(x, z);
                sb.Append(t.Zone switch
                {
                    WorldLayout.L23RimZone => '#',
                    WorldLayout.L23Core => t.Floor == FloorKind.L23Water ? '~' : 'h',
                    WorldLayout.L23Seedling => 'S',
                    WorldLayout.L23Ruin => 'R',
                    WorldLayout.L23Glow => 'o',
                    WorldLayout.L23TunnelZone => '=',
                    _ => t.Kind == TileKind.Wall ? '#' : '.',
                });
            }
            sb.AppendLine();
        }
        Console.Write(sb.ToString());
    }

    /// <summary>For the links mode: what one of the level's walked thresholds is, or null.</summary>
    static string L23LinkLabel(Tile t) => t.Under switch
    {
        Unders.L23PoolHollow or Unders.L23PoolMouth => "hollow green tree (23)",
        Unders.L23PoolSeedHollow or Unders.L23PoolSeedMouth => "Base Seedling's tree in 37 (23)",
        Unders.L23SeedlingHollow or Unders.L23SeedlingDoor => "Base Seedling's hollow tree",
        Unders.L23Well => "Heart of Water's well",
        _ => null,
    };

    /// <summary>
    /// 23links: Level 23's ways in and out for the lead to check rarity and find them. The hollow trees in Level 37: how many
    /// to a square kilometre where people arrive (the inner two fifths of the Poolrooms), how far apart, the nearest few to
    /// spawn and to the Poolrooms' middle, and which is Base Seedling's way home; that each has its hollow and a spot to stand
    /// outside its mouth. In the level: the hollow trunks (where those from 37 climb out), Base Seedling's hollow tree and the
    /// well in the Heart of Water; and that every arrival finder finds somewhere.
    /// </summary>
    static void L23Links(WorldLayout layout)
    {
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        var spawn = layout.FindSpawn();
        var (pcx, pcz, prad) = layout.L23PoolroomsDisc;
        int side = WorldLayout.L23TreeSquare * WorldLayout.PoolBlock;
        Console.WriteLine($"spawn {spawn.X},{spawn.Z}; Poolrooms middle {pcx},{pcz}, radius {prad} ({Dist(spawn.X, spawn.Z, pcx, pcz) / 1000:0.0} km from spawn)");
        Console.WriteLine($"hollow trees in 37: at most one to a square {side} blocks a side");
        static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
        int SquareOf(int g, int origin) => (int)Math.Floor((g - origin) / (double)side);

        // Where people arrive in the Poolrooms (within two fifths of its radius of the middle): how many, how far apart
        var trees = new System.Collections.Generic.List<WorldLayout.L23PoolTree>();
        double inner = prad * 0.4;
        int sq0x = SquareOf(pcx, layout.PoolOriginX), sq0z = SquareOf(pcz, layout.PoolOriginZ), reach = (int)(inner / side) + 1, squares = 0;
        var sw = System.Diagnostics.Stopwatch.StartNew();
        for (int sj = sq0z - reach; sj <= sq0z + reach; sj++)
            for (int si = sq0x - reach; si <= sq0x + reach; si++)
            {
                double cx = layout.PoolOriginX + (si + 0.5) * side, cz = layout.PoolOriginZ + (sj + 0.5) * side;
                if (Dist(cx, cz, pcx, pcz) > inner) continue;
                squares++;
                var t = layout.L23PoolTreeOfSquare(si, sj);
                if (t.Valid) trees.Add(t);
            }
        double km2 = squares * (double)side * side / 1e6;
        Console.WriteLine($"inner Poolrooms: {squares} squares ({km2:0} km2), {trees.Count} trees: {trees.Count / km2:0.00} per km2, one per {km2 / Math.Max(1, trees.Count):0.0} km2"
            + $" ({sw.Elapsed.TotalMilliseconds / Math.Max(1, squares):0} ms a square)");
        if (trees.Count > 1)
        {
            var nn = trees.Select(a => trees.Where(b => b != a).Min(b => Dist(a.X, a.Z, b.X, b.Z))).OrderBy(d => d).ToList();
            Console.WriteLine($"nearest neighbour: least {nn[0]:0} blocks, median {nn[nn.Count / 2]:0}, most {nn[^1]:0}");
            if (nn[0] < 600) Bad($"two trees only {nn[0]:0} blocks apart");
        }
        if (trees.Count == 0) Bad("no hollow trees where people arrive");

        // Each one laid out: its hollow, its mouth, and a floor to stand on outside it
        foreach (var t in trees)
        {
            Tile mid = layout.TileAt(t.X, t.Z);
            if (mid.Level != WorldLayout.Poolrooms || mid.Under is not (Unders.L23PoolHollow or Unders.L23PoolSeedHollow)) Bad($"tree at {t.X},{t.Z}: middle tile Under {mid.Under}");
            int fx = t.X + (int)Math.Round(Math.Cos(t.MouthA) * (t.R + 1.5)), fz = t.Z + (int)Math.Round(Math.Sin(t.MouthA) * (t.R + 1.5));
            Tile front = layout.TileAt(fx, fz);
            if (front.Kind != TileKind.Floor || front.Under != 0 || front.Depth > 1) Bad($"tree at {t.X},{t.Z}: nothing to stand on outside its mouth ({front.Kind}, Under {front.Under}, depth {front.Depth})");
        }

        // The nearest few to spawn (on the Poolrooms' near edge), and to its middle
        var ring = new System.Collections.Generic.List<(int Si, int Sj, double D)>();
        int all = (int)(prad / side) + 2;
        for (int sj = sq0z - all; sj <= sq0z + all; sj++)
            for (int si = sq0x - all; si <= sq0x + all; si++)
            {
                double cx = layout.PoolOriginX + (si + 0.5) * side, cz = layout.PoolOriginZ + (sj + 0.5) * side;
                if (Dist(cx, cz, pcx, pcz) > prad + side) continue;
                ring.Add((si, sj, Dist(cx, cz, spawn.X, spawn.Z)));
            }
        int shown = 0;
        foreach (var (si, sj, _) in ring.OrderBy(r => r.D))
        {
            var t = layout.L23PoolTreeOfSquare(si, sj);
            if (!t.Valid) continue;
            Console.WriteLine($"  near spawn: Level 37, hollow tree (in, one-way), {t.X},{t.Z} (water level y = floor of 37), {Dist(t.X, t.Z, spawn.X, spawn.Z) / 1000:0.0} km from spawn");
            if (++shown == 4) break;
        }
        foreach (var t in trees.OrderBy(t => Dist(t.X, t.Z, pcx, pcz)).Take(4))
            Console.WriteLine($"  near the Poolrooms' middle: Level 37, hollow tree{(layout.L23IsSeedlingTree(t) ? " (Base Seedling's way home, two-way)" : " (in, one-way)")}, {t.X},{t.Z}, "
                + $"{Dist(t.X, t.Z, pcx, pcz):0} from the middle, {Dist(t.X, t.Z, spawn.X, spawn.Z) / 1000:0.0} km from spawn");
        var home = layout.L23SeedlingTree;
        if (home == null) Bad("no tree for Base Seedling's way home");
        else Console.WriteLine($"Base Seedling's tree in 37: {home.X},{home.Z}, {Dist(home.X, home.Z, pcx, pcz):0} blocks from the Poolrooms' middle");

        // In the level
        var hollows = layout.L23HollowTrunks();
        Console.WriteLine($"Level 23: {hollows.Count} hollow trunks to climb out of");
        foreach (var h in hollows.OrderBy(h => Dist(h.X, h.Z, layout.L23MidX, layout.L23MidZ)).Take(3))
            Console.WriteLine($"  hollow trunk {h.X},{h.Z} (radius {h.R:0.0}), {Dist(h.X, h.Z, layout.L23MidX, layout.L23MidZ):0} from the Heart of Water");
        if (hollows.Count < 8) Bad($"only {hollows.Count} hollow trunks");
        var s = layout.L23SeedlingAt;
        Console.WriteLine($"Base Seedling's hollow tree (out, two-way to 37): {s.X},{s.Z}, {Dist(s.X, s.Z, spawn.X, spawn.Z) / 1000:0.0} km from spawn; tile Under {layout.TileAt(s.X, s.Z).Under}");
        if (layout.TileAt(s.X, s.Z).Under != Unders.L23SeedlingHollow) Bad("Base Seedling's hollow is not marked");
        Tile well = layout.TileAt(layout.L23MidX, layout.L23MidZ);
        Console.WriteLine($"the Heart of Water's well (out, one-way to 7): {layout.L23MidX},{layout.L23MidZ}, depth {well.Depth}, Under {well.Under}");
        if (well.Under != Unders.L23Well) Bad("the well is not marked");

        // The arrival finders
        int hollowOk = 0, campOk = 0, seaOk = 0, treeOk = 0;
        for (ulong k = 1; k <= 20; k++)
        {
            ulong key = k * 104729UL + 7;
            if (layout.L23HollowArrival(key) is { } a && layout.TileAt(a.X, a.Z).Zone == WorldLayout.L23Surface
                && new[] { (1, 0), (-1, 0), (0, 1), (0, -1) }.Any(o => layout.TileAt(a.X + o.Item1, a.Z + o.Item2).Under == Unders.L23HollowTrunk)) hollowOk++;
            else if (layout.L23HollowArrival(key) is { } miss) Console.WriteLine($"  arrival {miss.X},{miss.Z} not beside a hollow trunk");
            if (layout.L23SeedlingArrival(key) is { } c && layout.TileAt(c.X, c.Z).Zone == WorldLayout.L23Seedling && Dist(c.X, c.Z, s.X, s.Z) < 6) campOk++;
            if (layout.L23SeaArrival(key) is { } e && layout.TileAt(e.X, e.Z) is { Kind: TileKind.Water, Level: 7 }) seaOk++;
            if (home != null && layout.L23SeedlingTreeArrival(key) is { } f && Dist(f.X, f.Z, home.X, home.Z) < home.R + 3) treeOk++;
        }
        Console.WriteLine($"arrivals (of 20 keys): beside a hollow trunk {hollowOk}, at Seedling's door {campOk}, in Level 7's open sea {seaOk}, beside Seedling's tree in 37 {treeOk}");
        if (hollowOk < 20) Bad("an arrival not beside a hollow trunk");
        if (campOk < 20) Bad("an arrival not at Base Seedling's door");
        if (seaOk < 20) Bad("an arrival not in the sea");
        if (home != null && treeOk < 20) Bad("an arrival not beside Seedling's tree in 37");
        Console.WriteLine(bad == 0 ? "23links: ok" : $"23links: {bad} problems");
    }

    static string L23UseKind(Tile t) => null;
}
