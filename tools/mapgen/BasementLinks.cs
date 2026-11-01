using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>The Basement's links harness mode (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// basementlinks [rings]: the cracked patches of floor into the Basement in Levels 0, 1, 2, 4 and 5, over the cells
    /// within [rings] (default 400) of spawn: how many cells of each host, how many cracks laid (and cells picked where none
    /// fitted), how many to the square kilometre, the median distance from one to the next nearest in the same level, and
    /// the nearest few to spawn (where, how far). Then the thresholds: for the nearest three of each host, every tile of the
    /// patch (only its middle three by three gives way; all of it leads to the same place), the fall's arrival (under a crack
    /// in the Basement's ceiling, on dry Cellar floor), the same again, and from that crack the climb out at the top of its
    /// shaft (into Level 0; not below the top, nor from the floor). BAD lines for anything wrong.
    /// </summary>
    static bool BasementLinks(WorldLayout layout, string[] args)
    {
        long seed = long.Parse(args[0]);
        int rings = args.Length > 3 && int.TryParse(args[3], out int r) ? r : 400;
        var net = new ThresholdNetwork(layout, new WorldGeometry(256), seed);
        var (spx, spz) = layout.FindSpawn();
        int smx = WorldLayout.MacroOf(spx), smz = WorldLayout.MacroOf(spz);
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        int[] hosts = { 0, 1, 2, 4, 5 };
        var cells = new Dictionary<int, long>();
        var picked = new Dictionary<int, int>();
        var cracks = new Dictionary<int, List<(int X, int Z)>>();
        foreach (int h in hosts) { cells[h] = 0; picked[h] = 0; cracks[h] = new(); }
        var sw = System.Diagnostics.Stopwatch.StartNew();
        for (int dz = -rings; dz <= rings; dz++)
            for (int dx = -rings; dx <= rings; dx++)
            {
                int mx = smx + dx, mz = smz + dz, level = layout.LevelAt(mx, mz);
                if (!WorldLayout.IsBasementCrackHost(level)) continue;
                cells[level]++;
                if (!layout.IsBasementCrackCell(mx, mz)) continue;
                picked[level]++;
                if (layout.BasementCrackIn(mx, mz) is { } c) cracks[level].Add(c);
            }
        Console.WriteLine($"seed {seed}, spawn {spx},{spz}, cells within {rings} of spawn ({sw.ElapsedMilliseconds} ms)");
        double D(int x, int z) => Math.Sqrt((double)(x - spx) * (x - spx) + (double)(z - spz) * (z - spz));
        foreach (int h in hosts)
        {
            var list = cracks[h];
            double km2 = cells[h] * 32.0 * 32.0 / 1e6;
            var spacing = new List<double>();
            foreach (var a in list)
            {
                double best = double.MaxValue;
                foreach (var b in list)
                    if (a != b) best = Math.Min(best, Math.Sqrt((double)(a.X - b.X) * (a.X - b.X) + (double)(a.Z - b.Z) * (a.Z - b.Z)));
                if (best < double.MaxValue) spacing.Add(best);
            }
            spacing.Sort();
            string median = spacing.Count > 0 ? $"{spacing[spacing.Count / 2]:0} m" : "-";
            Console.WriteLine($"Level {h} (one cell in {1 / WorldLayout.BasementCrackChance(h):0}): {cells[h]} cells ({km2:0.0} km²), {picked[h]} picked, {list.Count} cracks laid ({picked[h] - list.Count} did not fit), "
                + $"{list.Count / Math.Max(km2, 1e-9):0.00} per km², median spacing to the next {median}");
            list.Sort((a, b) => D(a.X, a.Z).CompareTo(D(b.X, b.Z)));
            foreach (var (x, z) in list.Take(4))
            {
                Tile t = layout.TileAt(x, z);
                Console.WriteLine($"    {x},{z}  {D(x, z):0} m from spawn  (floor {t.Floor}, zone {t.Zone})");
            }
        }

        // The thresholds, from the nearest three of each host
        int falls = 0, climbs = 0;
        foreach (int h in hosts)
            foreach (var (cx, cz) in cracks[h].Take(3))
            {
                Link? first = null;
                Passage give = null;
                for (int dz = -2; dz <= 2; dz++)
                    for (int dx = -2; dx <= 2; dx++)
                    {
                        int x = cx + dx, z = cz + dz;
                        Tile t = layout.TileAt(x, z);
                        bool core = Math.Abs(dx) <= 1 && Math.Abs(dz) <= 1;
                        // (A piece left out where the floor is not free: a wall beside a narrow tunnel, say; never the middle)
                        if (!WorldLayout.IsBasementCrack(t)) { if (dx == 0 && dz == 0) Bad($"L{h} {cx},{cz}: no middle"); continue; }
                        if (WorldLayout.BasementCrackOffset(t) != (dx, dz)) Bad($"L{h} {cx},{cz}: tile {dx},{dz} thinks it is {WorldLayout.BasementCrackOffset(t)}");
                        Passage p = net.Walked(x, z, t, 1.05);
                        if (!core) { if (p != null) Bad($"L{h} {cx},{cz}: edge tile {dx},{dz} gives way"); continue; }
                        if (p == null) { Bad($"L{h} {cx},{cz}: {dx},{dz} standing does not give way"); continue; }
                        if (net.Walked(x, z, t, 2.5) != null) Bad($"L{h} {cx},{cz}: gives way under someone a block and a half over it");
                        if (p.TwoWay || p.Source != (cx, cz)) Bad($"L{h} {cx},{cz}: {dx},{dz} is two-way or not one threshold ({p.Source})");
                        Link? got = net.Take(p, null);
                        if (got == null) { Bad($"L{h} {cx},{cz}: leads nowhere"); continue; }
                        if (first == null) { first = got; give = p; }
                        else if (got != first) Bad($"L{h} {cx},{cz}: {dx},{dz} leads elsewhere");
                    }
                if (first is not { } link) continue;
                falls++;
                int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z);
                Tile under = layout.TileAt(ax, az);
                bool ok = under.Level == WorldLayout.Basement && under.Ceiling == CeilingKind.BasementOpen && under.Zone == (byte)WorldLayout.BasementZone.Cellar;
                if (!ok) Bad($"L{h} {cx},{cz}: lands at {ax},{az} not under a crack in the Cellar (level {under.Level})");
                if (net.Take(give, null) != link) Bad($"L{h} {cx},{cz}: a second fall lands elsewhere");
                // Back up that crack
                if (net.BasementCrackMiddle(ax, az) is not { } crack) { Bad($"L{h} {cx},{cz}: no crack's middle over {ax},{az}"); continue; }
                Tile mid = layout.TileAt(crack.X, crack.Z);
                if (net.Walked(ax, az, under, 1.05) != null || net.Walked(ax, az, under, 15.2) != null) Bad($"L{h} {cx},{cz}: the crack's shaft leads out below its top");
                Passage up = net.Walked(crack.X, crack.Z, mid, ThresholdNetwork.BasementClimbRel + 0.05);
                Passage rim = net.Walked(crack.X + 2, crack.Z, layout.TileAt(crack.X + 2, crack.Z), ThresholdNetwork.BasementClimbRel + 1.05);
                if (up == null || rim == null) { Bad($"L{h} {cx},{cz}: no way out at the top of the crack at {crack}"); continue; }
                if (up.TwoWay || up.Source != crack || rim.Source != crack) Bad($"L{h} {cx},{cz}: the climb out is two-way or not one threshold");
                Link? outLink = net.Take(up, null);
                if (outLink is not { } o) { Bad($"L{h} {cx},{cz}: the climb out leads nowhere"); continue; }
                int ox = (int)Math.Floor(o.X), oz = (int)Math.Floor(o.Z);
                Tile there = layout.TileAt(ox, oz);
                if (there.Level != 0) Bad($"L{h} {cx},{cz}: the climb out lands in level {there.Level}");
                climbs++;
                Console.WriteLine($"  L{h} crack {cx},{cz} -> Basement {ax},{az} (crack {crack.X},{crack.Z}, {Math.Sqrt((double)(crack.X - ax) * (crack.X - ax) + (double)(crack.Z - az) * (crack.Z - az)):0.0} from its middle) -> up and out in Level 0 at {ox},{oz}");
            }
        Console.WriteLine($"thresholds: {falls} falls and {climbs} climbs out checked, {bad} bad");
        if (bad > 0) Console.WriteLine("BAD");
        return true;
    }
}
