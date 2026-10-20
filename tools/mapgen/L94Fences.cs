using Backrooms.Worldgen;

/// <summary>
/// Level 94's picket fences (l94fence): <c>mapgen &lt;seed&gt; &lt;cells&gt; l94fences [x z size]</c> tallies the fences in a square of
/// <c>cells</c> macro cells round the mountain (how far each stands from the road, the lengths they come in, ends and
/// joins, one-block gaps that are not a path, and fences on a path, a drive or beside a door), and writes
/// <c>l94fences.ppm</c>, a plan at three pixels a block of the square <c>size</c> blocks across from block offset
/// (x, z) of the mountain (default: the whole area): roads grey, kerbs pale, paths tan, houses red, fences white with
/// their joins drawn, the ground green by height.
/// </summary>
static class L94Fences
{
    static WorldLayout layout;
    static readonly Dictionary<(int, int), Tile[]> cache = new();

    static Tile At(int x, int z)
    {
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        if (!cache.TryGetValue((mx, mz), out var t)) cache[(mx, mz)] = t = layout.BuildMacro(mx, mz);
        return t[WorldLayout.TileIndex(x - mx * 32, z - mz * 32)];
    }

    static bool IsFence(Tile t) => t.Level == WorldLayout.Motion && t.Zone == 0 && t.Kind == TileKind.Bars && t.Pattern == WallPattern.Fence && t.Roof == 0;
    static bool IsRoad(Tile t) => t.Floor is FloorKind.MotionAsphalt or FloorKind.MotionKerb;

    public static void Run(WorldLayout l, string[] args)
    {
        layout = l;
        int n = int.Parse(args[1]), size = n * 32;
        int ox = l.MotionOriginX, oz = l.MotionOriginZ, x0 = ox - size / 2, z0 = oz - size / 2;
        // L94PROBE=x,z;x,z... (block coordinates) prints the tiles round each position
        if (Environment.GetEnvironmentVariable("L94PROBE") is string probe && probe.Length > 0)
        {
            foreach (var pos in probe.Split(';'))
            {
                var xz = pos.Split(',');
                int px = int.Parse(xz[0]), pz = int.Parse(xz[1]);
                Console.WriteLine($"round {px},{pz} ({px - ox},{pz - oz} of the mountain):");
                for (int z = pz - 1; z <= pz + 1; z++)
                    for (int x = px - 1; x <= px + 1; x++)
                    {
                        Tile t = At(x, z);
                        Console.WriteLine($"  {x - px,2},{z - pz,2}: {t.Kind} {t.Floor} variant {t.Variant} stack {t.Stack} pattern {t.Pattern} roof {t.Roof} h {t.Height}");
                    }
            }
            return;
        }
        var counts = new SortedDictionary<string, int>();
        var example = new Dictionary<string, (int, int)>();
        void C(string k, int x, int z) { counts[k] = counts.GetValueOrDefault(k) + 1; example.TryAdd(k, (x, z)); }

        var fence = new HashSet<(int, int)>();
        for (int z = z0; z < z0 + size; z++)
            for (int x = x0; x < x0 + size; x++)
                if (IsFence(At(x, z))) fence.Add((x, z));

        foreach (var (x, z) in fence)
        {
            Tile t = At(x, z);
            // How far from the road (Chebyshev, to the nearest asphalt or kerb)
            int d = 99;
            for (int r = 1; r <= 8 && d == 99; r++)
                for (int dz = -r; dz <= r && d == 99; dz++)
                    for (int dx = -r; dx <= r; dx++)
                        if ((Math.Abs(dx) == r || Math.Abs(dz) == r) && IsRoad(At(x + dx, z + dz))) { d = r; break; }
            C(d == 99 ? "road distance 9+" : $"road distance {d}", x, z);
            // Joins against what is there
            (int dx, int dz, int bit)[] dirs = { (0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8) };
            int joins = 0;
            foreach (var (dx, dz, bit) in dirs)
            {
                bool there = fence.Contains((x + dx, z + dz)) || IsFence(At(x + dx, z + dz));
                bool joined = (t.Stack & bit) != 0;
                if (joined) joins++;
                if (joined && !there && At(x + dx, z + dz).Kind != TileKind.Wall) C("join to nothing", x, z);
                if (!joined && there) C("fence beside, not joined", x, z);
            }
            // Heights: a joined neighbour more than a block higher or lower is a fence the ground leaves behind; one block is a step
            foreach (var (dx, dz, bit) in dirs)
            {
                if ((t.Stack & bit) == 0) continue;
                int dh = Math.Abs(At(x + dx, z + dz).Height - t.Height);
                if (dh > 1) C("joined across a drop of 2+", x, z);
                else if (dh == 1) C("joined across a step of 1", x, z);
            }
            // (every pair of neighbouring fence blocks once, joined or not)
            foreach (var (dx, dz) in new[] { (1, 0), (0, 1) })
                if (fence.Contains((x + dx, z + dz)))
                {
                    int dh = Math.Abs(At(x + dx, z + dz).Height - t.Height);
                    if (dh > 1) C("neighbours 2+ apart in height", x, z);
                    else if (dh == 1) C("neighbours 1 apart in height", x, z);
                    else C("neighbours level", x, z);
                }
            if (joins == 0) C("lone post", x, z);
            if (joins == 1) C("end", x, z);
            if (t.Floor is FloorKind.MotionPath or FloorKind.Driveway or FloorKind.Sidewalk) C("fence on a path or drive", x, z);
            foreach (var (dx, dz, _) in dirs)
                if (At(x + dx, z + dz).Kind is TileKind.Door or TileKind.Doorway) C("fence beside a door", x, z);
            if (fence.Contains((x + 1, z)) && fence.Contains((x, z + 1)) && fence.Contains((x + 1, z + 1))) C("2x2 block of fence", x, z);
        }

        // Walkable ground more than a block above its neighbour (a drop the player cannot climb, whatever the fences do)
        for (int z = z0; z < z0 + size - 1; z++)
            for (int x = x0; x < x0 + size - 1; x++)
            {
                Tile a = At(x, z);
                if (a.Level != WorldLayout.Motion || a.Zone != 0 || a.Kind != TileKind.Floor) continue;
                foreach (var (dx, dz) in new[] { (1, 0), (0, 1) })
                {
                    Tile b = At(x + dx, z + dz);
                    if (b.Level == WorldLayout.Motion && b.Zone == 0 && b.Kind == TileKind.Floor && Math.Abs(a.Height - b.Height) > 1)
                        C("floor neighbours 2+ apart in height", x, z);
                }
            }

        // One-block gaps in a straight line of fence
        foreach (var (x, z) in fence)
            foreach (var (dx, dz) in new[] { (2, 0), (0, 2) })
            {
                if (!fence.Contains((x + dx, z + dz))) continue;
                int gx = x + dx / 2, gz = z + dz / 2;
                if (fence.Contains((gx, gz))) continue;
                // (a gap whose sides are the ends of their lengths; posts running past each other on a staircase are not one)
                if (fence.Contains((x + dz / 2, z + dx / 2)) && fence.Contains((x + dx + dz / 2, z + dz + dx / 2))) continue;
                if (fence.Contains((x - dz / 2, z - dx / 2)) && fence.Contains((x + dx - dz / 2, z + dz - dx / 2))) continue;
                Tile g = At(gx, gz);
                string kind = g.Floor is FloorKind.MotionPath or FloorKind.Sidewalk || g.Stair > 0 ? "path" : g.Variant != 0 ? "prop" : g.Kind != TileKind.Floor ? "not floor" : "grass";
                C($"one-block gap ({kind})", gx, gz);
                if (kind != "path" && counts[$"one-block gap ({kind})"] <= 5)
                    Console.WriteLine($"  one-block gap ({kind}) at {gx - ox},{gz - oz} of the mountain: {g.Kind} {g.Floor} variant {g.Variant}");
            }

        // Pockets: ground shut in by fences (and walls), found by a walk of up to 400 blocks from beside each fence
        // that ignores heights (Validate's reach does the climbing)
        var open = new HashSet<(int, int)>();
        var shut = new HashSet<(int, int)>();
        bool Walkable(int x, int z) { Tile t = At(x, z); return t.Level == WorldLayout.Motion && t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.Door && !(t.Kind == TileKind.Bars); }
        foreach (var (x, z) in fence)
            foreach (var s0 in new[] { (x, z - 1), (x + 1, z), (x, z + 1), (x - 1, z) })
            {
                if (fence.Contains(s0) || open.Contains(s0) || shut.Contains(s0) || !Walkable(s0.Item1, s0.Item2)) continue;
                var seenP = new HashSet<(int, int)> { s0 };
                var q = new Queue<(int, int)>();
                q.Enqueue(s0);
                while (q.Count > 0 && seenP.Count < 400)
                {
                    var (px, pz) = q.Dequeue();
                    foreach (var nb in new[] { (px, pz - 1), (px + 1, pz), (px, pz + 1), (px - 1, pz) })
                        if (!seenP.Contains(nb) && !fence.Contains(nb) && Walkable(nb.Item1, nb.Item2)) { seenP.Add(nb); q.Enqueue(nb); }
                }
                if (seenP.Count >= 400) { open.UnionWith(seenP); continue; }
                shut.UnionWith(seenP);
                C("pocket shut in by fences", s0.Item1, s0.Item2);
                Console.WriteLine($"  pocket of {seenP.Count} at {s0.Item1 - ox},{s0.Item2 - oz} of the mountain");
            }

        // Lengths (joined pieces)
        var seen = new HashSet<(int, int)>();
        var lengths = new List<int>();
        foreach (var s in fence)
        {
            if (!seen.Add(s)) continue;
            int len = 0;
            var st = new Stack<(int, int)>();
            st.Push(s);
            while (st.Count > 0)
            {
                var (px, pz) = st.Pop();
                len++;
                foreach (var q in new[] { (px, pz - 1), (px + 1, pz), (px, pz + 1), (px - 1, pz) })
                    if (fence.Contains(q) && seen.Add(q)) st.Push(q);
            }
            lengths.Add(len);
            C(len < 4 ? "length 1-3" : len < 10 ? "length 4-9" : len < 30 ? "length 10-29" : "length 30+", s.Item1, s.Item2);
        }

        Console.WriteLine($"Level 94 fences, {size}x{size} round the mountain: {fence.Count} fence blocks in {lengths.Count} lengths"
            + (lengths.Count > 0 ? $", median length {lengths.OrderBy(v => v).ElementAt(lengths.Count / 2)}" : ""));
        foreach (var (k, v) in counts) Console.WriteLine($"  {k,-30} {v,7}  e.g. {example[k].Item1},{example[k].Item2}");

        // The plan
        int px0 = args.Length > 5 ? ox + int.Parse(args[3]) : x0, pz0 = args.Length > 5 ? oz + int.Parse(args[4]) : z0;
        int ps = args.Length > 5 ? int.Parse(args[5]) : size, S = 3;
        using var f = File.Create("l94fences.ppm");
        var header = System.Text.Encoding.ASCII.GetBytes($"P6 {ps * S} {ps * S} 255\n");
        f.Write(header);
        var row = new byte[ps * S * 3];
        for (int z = 0; z < ps; z++)
        {
            var tiles = new Tile[ps];
            for (int x = 0; x < ps; x++) tiles[x] = At(px0 + x, pz0 + z);
            for (int sy = 0; sy < S; sy++)
            {
                for (int x = 0; x < ps; x++)
                {
                    Tile t = tiles[x];
                    int g = Math.Min((int)t.Height, 30);
                    (int r, int gg, int b) c = t.Level != WorldLayout.Motion ? (40, 40, 40)
                        : t.Roof != 0 ? (170, 60, 50)
                        : t.Kind == TileKind.Wall ? (230, 225, 200)
                        : t.Floor == FloorKind.MotionAsphalt ? (85, 85, 90)
                        : t.Floor == FloorKind.MotionKerb ? (185, 185, 180)
                        : t.Floor == FloorKind.MotionPath || t.Stair > 0 ? (205, 175, 120)
                        : t.Floor == FloorKind.MotionConcrete ? (215, 210, 195)
                        : t.Zone == 2 ? (170, 200, 230)
                        : (30 + g * 4, 110 + g * 5, 30);
                    if (t.Variant == Props.StopSign) c = (255, 0, 0);
                    else if (t.Variant == Props.NoOutletSign) c = (255, 220, 0);
                    else if (t.Variant != 0 && t.Zone == 0 && t.Kind == TileKind.Floor) c = (255, 150, 40);
                    for (int sx = 0; sx < S; sx++)
                    {
                        var cc = c;
                        if (IsFence(t) || t.Kind == TileKind.Bars && t.Pattern == WallPattern.Fence)
                        {
                            bool post = sx == 1 && sy == 1;
                            bool arm = sx == 1 && sy == 0 && (t.Stack & 1) != 0 || sx == 2 && sy == 1 && (t.Stack & 2) != 0
                                || sx == 1 && sy == 2 && (t.Stack & 4) != 0 || sx == 0 && sy == 1 && (t.Stack & 8) != 0;
                            if (post || arm) cc = (255, 255, 255);
                        }
                        int o = (x * S + sx) * 3;
                        row[o] = (byte)cc.r; row[o + 1] = (byte)cc.gg; row[o + 2] = (byte)cc.b;
                    }
                }
                f.Write(row);
            }
        }
        Console.WriteLine($"l94fences.ppm: {ps}x{ps} blocks from {px0 - ox},{pz0 - oz} of the mountain");
    }
}
