using Backrooms.Worldgen;

/// <summary>
/// l8roads [angle] [step]: a map of Level 8's 9th Road over a square of cells (args[1]) centred in the middle of the
/// ring straight out from spawn at the angle (degrees, default 0), or on AT. Writes l8map.bin (int size, then a byte
/// per block: 0 another level's floor, 1 another level's wall, 2 Level 8 rock, 3 road, 4 camp clearing, 5 lamp,
/// 6 M.E.G. marker, 7 vent or seep, 8 doorway in a wall between levels, 9 deposit rock, 10 camp furniture, 11 Level 7
/// sea, 12 the passage round a break in the road, 13 rubble at a break) for render_l8roads.py, and prints how much road there is, how far the caves lie from it, the gaps between
/// roads along radial and circumferential lines, the ways through the level's walls, the pieces of road that lead
/// nowhere (cut off inside the map), and how long a cell takes to lay out.
/// </summary>
static class L8Roads
{
    public static void Run(WorldLayout layout, int smx, int smz, int n, string[] args, int atX, int atZ, bool useAt)
    {
        double ang = (args.Length > 3 ? double.Parse(args[3], System.Globalization.CultureInfo.InvariantCulture) : 0) * Math.PI / 180;
        int cx, cz;
        if (useAt) { cx = atX; cz = atZ; }
        else
        {
            double rIn = -1, rOut = -1;
            for (double r = 1; r < 900; r += 0.5)
            {
                int lv = layout.LevelAt(smx + (int)Math.Round(Math.Cos(ang) * r), smz + (int)Math.Round(Math.Sin(ang) * r));
                if (lv == 8 && rIn < 0) rIn = r;
                if (lv > 8 && rIn > 0) { rOut = r; break; }
            }
            double rm = (rIn + rOut) / 2;
            cx = smx + (int)Math.Round(Math.Cos(ang) * rm); cz = smz + (int)Math.Round(Math.Sin(ang) * rm);
            Console.WriteLine($"ring of level 8 at {args.ElementAtOrDefault(3) ?? "0"} deg: cells {rIn:0}-{rOut:0} from spawn");
        }
        int m0x = cx - n / 2, m0z = cz - n / 2, size = n * 32, x0 = m0x * 32, z0 = m0z * 32;
        Console.WriteLine($"area: {n}x{n} cells centred on cell {cx},{cz} (blocks {x0}..{x0 + size}, {z0}..{z0 + size})");
        // (The first question about the road plans the network, from layout version 9: timed on its own)
        var first = System.Diagnostics.Stopwatch.StartNew();
        layout.IsNinthRoad(cx * 32, cz * 32);
        Console.WriteLine($"first road question (plans the network in version 9): {first.ElapsedMilliseconds} ms");
        var deposit = typeof(WorldLayout).GetMethod("L8DepositAt");
        var map = new byte[size * size];
        var level8 = new bool[size * size];
        var sw = System.Diagnostics.Stopwatch.StartNew();
        int l8cells = 0; double l8ms = 0;
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                bool is8 = layout.LevelAt(m0x + mx, m0z + mz) == 8;
                long t0 = sw.ElapsedTicks;
                Tile[] tiles = layout.BuildMacro(m0x + mx, m0z + mz);
                if (is8) { l8cells++; l8ms += (sw.ElapsedTicks - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency; }
                for (int i = 0; i < tiles.Length; i++)
                {
                    Tile t = tiles[i];
                    int lx = mx * 32 + i % 32, lz = mz * 32 + i / 32, gx = x0 + lx, gz = z0 + lz, k = lz * size + lx;
                    byte c;
                    if (t.Level != 8)
                    {
                        if (t.Kind == TileKind.Doorway && t.Tall) c = 8;
                        else if (t.Level == 7 && t.Kind == TileKind.Water) c = 11;
                        else c = (byte)(t.Kind == TileKind.Floor || t.Kind == TileKind.Doorway || t.Kind == TileKind.Water ? 0 : 1);
                    }
                    else
                    {
                        level8[k] = true;
                        if (t.Kind == TileKind.Doorway) c = 8;
                        else if (t.Kind != TileKind.Floor)
                        {
                            c = t.Variant is Props.CaveVent or Props.AlmondSeep ? (byte)7 : (byte)2;
                            if (t.Zone == WorldLayout.L8ZoneCrawl) c = 12; // the dark passage round a break
                            else if (t.Zone > WorldLayout.L8ZoneRubble) c = 13; // rubble where the road ends
                            if (c == 2 && deposit != null && (int)deposit.Invoke(layout, new object[] { gx, gz }) > 0) c = 9;
                        }
                        else if (t.Variant == Props.RoadLamp) c = 5;
                        else if (t.Variant == Props.MegMarker) c = 6;
                        else if (layout.IsNinthRoad(gx, gz)) c = 3;
                        else c = t.Variant != 0 || t.SupplyBox || t.Stack > 0 ? (byte)10 : (byte)4;
                    }
                    map[k] = c;
                }
            }
        Console.WriteLine($"laid out {n * n} cells in {sw.ElapsedMilliseconds} ms; Level 8 cells {l8cells}, {l8ms / Math.Max(1, l8cells):0.00} ms a cell");
        using (var w = new BinaryWriter(File.Create("l8map.bin"))) { w.Write(size); w.Write(map); }

        bool Road(int k) => map[k] is 3 or 4 or 5 or 6 or 10;
        // Distance from every Level 8 rock tile to the nearest road or camp (8-way chamfer, about blocks)
        var dist = new int[size * size];
        Array.Fill(dist, int.MaxValue / 2);
        for (int k = 0; k < map.Length; k++) if (Road(k)) dist[k] = 0;
        for (int pass = 0; pass < 2; pass++)
        {
            for (int zz = 0; zz < size; zz++)
            {
                int z = pass == 0 ? zz : size - 1 - zz;
                for (int xx = 0; xx < size; xx++)
                {
                    int x = pass == 0 ? xx : size - 1 - xx, k = z * size + x, d = dist[k];
                    int dz = pass == 0 ? -1 : 1;
                    foreach (var (ox, oz, cost) in new[] { (-1, 0, 10), (1, 0, 10), (0, dz, 10), (-1, dz, 14), (1, dz, 14) })
                    {
                        if (pass == 0 && ox == 1 && oz == 0 || pass == 1 && ox == -1 && oz == 0) continue;
                        int nx = x + ox, nz = z + oz;
                        if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                        d = Math.Min(d, dist[nz * size + nx] + cost);
                    }
                    dist[k] = d;
                }
            }
        }
        long l8 = 0, road = 0, camp = 0, lamps = 0, markers = 0, vents = 0, dep = 0; double sumDist = 0; int far100 = 0, far200 = 0; int maxDist = 0;
        for (int k = 0; k < map.Length; k++)
        {
            if (!level8[k]) continue;
            l8++;
            if (map[k] is 3 or 5 or 6) road++;
            if (map[k] is 4 or 10) camp++;
            if (map[k] == 5) lamps++;
            if (map[k] == 6) markers++;
            if (map[k] == 7) vents++;
            if (map[k] == 9) dep++;
            if (!Road(k) && map[k] != 8)
            {
                double d = dist[k] / 10.0;
                sumDist += d; if (d > 100) far100++; if (d > 200) far200++; maxDist = Math.Max(maxDist, (int)d);
            }
        }
        long rock = l8 - road - camp;
        Console.WriteLine($"Level 8 tiles {l8}: road {road} ({100.0 * road / l8:0.00}%), camp clearings {camp}, lamps {lamps}, markers {markers}, vents and seeps {vents}, deposit rock tiles {dep}");
        Console.WriteLine($"rock to nearest road: mean {sumDist / Math.Max(1, rock):0.0} blocks, max {maxDist}; over 100 blocks {100.0 * far100 / Math.Max(1, rock):0.0}%, over 200 {100.0 * far200 / Math.Max(1, rock):0.0}%");
        Console.WriteLine("network: " + layout.L8Census());
        if (Environment.GetEnvironmentVariable("L8DBG") is { } dbg)
        {
            var pr = dbg.Split(',').Select(int.Parse).ToArray();
            for (int zz = pr[1]; zz < pr[1] + 30; zz++)
            {
                var sb = new System.Text.StringBuilder($"{zz,7} ");
                for (int xx = pr[0]; xx < pr[0] + 40; xx++)
                {
                    Tile tt = layout.BuildMacro(WorldLayout.MacroOf(xx), WorldLayout.MacroOf(zz))[WorldLayout.TileIndex(xx - WorldLayout.MacroOf(xx) * 32, zz - WorldLayout.MacroOf(zz) * 32)];
                    sb.Append(layout.IsNinthRoad(xx, zz) ? 'R' : tt.Zone == 1 ? 'z' : tt.Zone > 10 ? 'P' : layout.L8CrawlAt(xx, zz) > 0 ? 'c' : '.');
                }
                Console.WriteLine(sb);
            }
        }
        {
            // Settlements in the map: the clearings, counted as pieces of connected tiles
            var seenCamp = new bool[map.Length]; int camps = 0;
            for (int k0 = 0; k0 < map.Length; k0++)
            {
                if (seenCamp[k0] || map[k0] is not (4 or 10)) continue;
                camps++;
                var st = new Stack<int>(); st.Push(k0); seenCamp[k0] = true;
                while (st.Count > 0)
                {
                    int k1 = st.Pop(), x1 = k1 % size, z1 = k1 / size;
                    foreach (var (ox, oz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nx = x1 + ox, nz = z1 + oz;
                        if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                        int k2 = nz * size + nx;
                        if (!seenCamp[k2] && map[k2] is 4 or 10) { seenCamp[k2] = true; st.Push(k2); }
                    }
                }
            }
            Console.WriteLine($"settlements in the map: {camps} ({camps / (l8 / 1e6):0.0} per km2 of Level 8)");
        }
        Console.WriteLine($"road per km2 of Level 8: {road / 3.0 / (l8 / 1e6):0} m of road (3 wide)");

        // Gaps between roads along straight lines out from spawn and round the ring (through the map only)
        double sx = smx * 32 + 16, sz = smz * 32 + 16;
        var radialGaps = new List<int>(); var ringGaps = new List<int>();
        void Walk(Func<double, (double X, double Z)> at, double length, List<int> gaps)
        {
            int last = -1; bool onRoad = false;
            for (int i = 0; i <= length; i++)
            {
                var (x, z) = at(i);
                int lx = (int)Math.Floor(x) - x0, lz = (int)Math.Floor(z) - z0;
                if (lx < 0 || lz < 0 || lx >= size || lz >= size) { onRoad = false; last = -1; continue; }
                int k = lz * size + lx;
                if (!level8[k]) { last = -1; onRoad = false; continue; }
                bool r = Road(k);
                if (r && !onRoad) { if (last >= 0 && i - last > 3) gaps.Add(i - last); }
                if (!r && onRoad) last = i;
                if (r) last = i;
                onRoad = r;
            }
        }
        double cxB = cx * 32 + 16 - sx, czB = cz * 32 + 16 - sz, rc = Math.Sqrt(cxB * cxB + czB * czB), a0 = Math.Atan2(czB, cxB);
        double halfSpan = size / 2.0 / rc;
        for (int i = 0; i < 400; i++)
        {
            double a = a0 - halfSpan + 2 * halfSpan * i / 399;
            Walk(t => (sx + Math.Cos(a) * (rc - size / 2.0 + t), sz + Math.Sin(a) * (rc - size / 2.0 + t)), size, radialGaps);
        }
        for (int i = 0; i < 60; i++)
        {
            double r = rc - size / 2.0 + size * (i + 0.5) / 60;
            Walk(t => (sx + Math.Cos(a0 - halfSpan + t / r) * r, sz + Math.Sin(a0 - halfSpan + t / r) * r), 2 * halfSpan * r, ringGaps);
        }
        static string Gaps(List<int> g) => g.Count == 0 ? "none" : $"{g.Count} gaps, mean {g.Average():0} blocks, median {g.OrderBy(v => v).ElementAt(g.Count / 2)}";
        Console.WriteLine($"between roads, out from spawn: {Gaps(radialGaps)}");
        Console.WriteLine($"between roads, round the ring: {Gaps(ringGaps)}");

        // Ways through the level's walls: runs of doorway tiles on its boundary, by the level on the other side
        var ways = new Dictionary<int, int>();
        int blind = 0;
        var seenWay = new bool[size * size];
        for (int k = 0; k < map.Length; k++)
        {
            if (map[k] != 8 || seenWay[k]) continue;
            var q = new Queue<int>(); q.Enqueue(k); seenWay[k] = true; var levels = new HashSet<int>(); bool fromRoad = false, intoOpen = false;
            while (q.Count > 0)
            {
                int c = q.Dequeue(), x = c % size, z = c / size;
                foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    int nx = x + dx, nz = z + dz;
                    if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                    int nk = nz * size + nx;
                    if (map[nk] == 8 && !seenWay[nk]) { seenWay[nk] = true; q.Enqueue(nk); }
                    else if (map[nk] != 8)
                    {
                        levels.Add(layout.LevelAt(WorldLayout.MacroOf(x0 + nx), WorldLayout.MacroOf(z0 + nz)));
                        if (level8[nk] && Road(nk)) fromRoad = true;
                        if (!level8[nk] && map[nk] is 0 or 11) intoOpen = true;
                    }
                }
            }
            if (!levels.Contains(8)) continue;
            foreach (int lv in levels) if (lv != 8) ways[lv] = ways.GetValueOrDefault(lv) + 1;
            if (!fromRoad || !intoOpen)
            {
                blind++;
                if (blind <= 5) Console.WriteLine($"  way through the wall at {x0 + k % size},{z0 + k / size}: {(fromRoad ? "" : "no road on the Level 8 side ")}{(intoOpen ? "" : "nothing open on the far side")}");
            }
        }
        Console.WriteLine("ways through Level 8's walls: " + (ways.Count == 0 ? "none" : string.Join(", ", ways.OrderBy(p => p.Key).Select(p => $"to Level {p.Key} {p.Value}"))) + $"; {blind} not from a road into open floor");

        // Pieces of road (with camps, doorways and the passages round breaks) cut off from everything inside the map, and the biggest one
        var comp = new int[size * size];
        int pieces = 0, closed = 0, closedTiles = 0;
        for (int k = 0; k < map.Length; k++)
        {
            if (!(Road(k) || map[k] is 8 or 12) || !level8[k] && map[k] != 8 || comp[k] != 0) continue;
            pieces++;
            var q = new Queue<int>(); q.Enqueue(k); comp[k] = pieces; bool edge = false, door = false; int count = 0;
            while (q.Count > 0)
            {
                int c = q.Dequeue(), x = c % size, z = c / size; count++;
                if (map[c] == 8) door = true;
                if (x == 0 || z == 0 || x == size - 1 || z == size - 1) edge = true;
                foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    int nx = x + dx, nz = z + dz;
                    if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                    int nk = nz * size + nx;
                    if (comp[nk] == 0 && (Road(nk) && level8[nk] || map[nk] is 8 or 12)) { comp[nk] = pieces; q.Enqueue(nk); }
                }
            }
            if (!edge && !door) { closed++; closedTiles += count; if (closed <= 5) Console.WriteLine($"  cut-off road piece of {count} tiles at {x0 + k % size},{z0 + k / size}"); }
        }
        Console.WriteLine($"road pieces: {pieces}, cut off inside the map (no way to the map's edge or another level) {closed} ({closedTiles} tiles)");

        // Where someone arriving in Level 8 is put down (FindArrival, as the thresholds into it do)
        int found = 0, onRoad = 0, inCamp = 0, worst = 0;
        for (ulong key = 1; key <= 150; key++)
        {
            if (layout.FindArrival(8, key * 7919UL + 13) is not { } a) continue;
            found++;
            if (layout.IsNinthRoad(a.X, a.Z)) onRoad++;
            else if (layout.NinthRoadDistance(a.X, a.Z) == 0) inCamp++;
            worst = Math.Max(worst, layout.NinthRoadDistance(a.X, a.Z));
        }
        Console.WriteLine($"arrivals in Level 8: {found}/150 found, {onRoad} on the road, {inCamp} in a settlement off it, farthest from the road {worst} blocks");
    }
}
