using Backrooms.Thresholds;
using Backrooms.Worldgen;
using static Backrooms.Worldgen.WorldLayout;

/// <summary>
/// Level 3999's harness modes (this file is the level's own; see docs/design/new-levels/CONTRACT.md):
///   3999stats [blocks]       what the plan blocks round the centre (and a ring far out) hold: units by kind against their
///                            weights, the Blackout's share past 65%, natatoria, walkways (both ways), escalators per
///                            junction, arrivals, and that every unit's floor can be walked to from a concourse
///   3999hash                 the layout hash with the level's entrances in other levels left out, then with them, and
///                            the lines that differ
///   3999ways                 finds Level 10 arcades (their windmills wholly in Level 10, about 120 apart), Level 11's
///                            glitch walls and Level 37's magenta tiles, and goes through every threshold of the level
///                            and back
///   3999map bi bj n out.ppm  a picture of n x n plan blocks from block (bi, bj), one pixel a block
/// </summary>
static partial class LevelModes
{
    static bool L3999Modes(WorldLayout layout, string mode, string[] args)
    {
        switch (mode)
        {
            case "3999stats": L3999StatsMode(layout, args.Length > 3 ? int.Parse(args[3]) : 3); return true;
            case "3999hash": L3999HashMode(args); return true;
            case "3999ways": L3999WaysMode(layout, long.Parse(args[0])); return true;
            case "3999map": L3999MapMode(layout, int.Parse(args[3]), int.Parse(args[4]), int.Parse(args[5]), args[6]); return true;
        }
        return false;
    }

    /// <summary>For the links mode: what to call a threshold of the level's walked into on this tile, or null.</summary>
    static string L3999LinkLabel(Tile t) => t.Under switch
    {
        Unders.L3999GlitchWall => "glitch wall (3999)",
        Unders.L3999MagentaTiles => "magenta tiles (3999)",
        Unders.L3999Drain => "natatorium drain",
        _ => t.Level == Level3999 && t.Variant == Props.L3999Rusted ? "rusted cabinet" : null,
    };

    /// <summary>For the links mode: the threshold kind of one of the level's blocks used on this tile (its BlockBehaviorThreshold kind), or null.</summary>
    static string L3999UseKind(Tile t)
    {
        if (t.Kind == TileKind.Door && t.Pattern == WallPattern.L3999Revolving && (t.Level == Level3999 || t.Under == Unders.L3999Arcade)) return "l3999-revolving";
        if (t.Level != Level3999) return null;
        if (t.Kind == TileKind.Door && t.Pattern == WallPattern.L3999Staff) return "l3999-staff";
        if (t.Kind == TileKind.Door && t.Pattern == WallPattern.L3999Elevator) return "l3999-elevator";
        if (t.Kind == TileKind.Floor && t.Variant == Props.L3999Themed) return "l3999-cabinet";
        return null;
    }

    static readonly Dictionary<(int, int), Tile[]> l3999Cells = new();

    static Tile L3999Tile(WorldLayout layout, int x, int z)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        if (!l3999Cells.TryGetValue((mx, mz), out var t))
        {
            if (l3999Cells.Count > 6000) l3999Cells.Clear();
            l3999Cells[(mx, mz)] = t = layout.BuildMacro(mx, mz);
        }
        return t[TileIndex(x - mx * 32, z - mz * 32)];
    }

    static void L3999StatsMode(WorldLayout layout, int reach)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var units = new Dictionary<L3999Kind, int>();
        int blocks = 0, mini = 0;
        // Blocks round the centre
        for (int bj = -reach; bj <= reach; bj++)
            for (int bi = -reach; bi <= reach; bi++)
            {
                blocks++;
                foreach (var u in layout.L3999UnitsOf(bi, bj)) { units[u.Kind] = units.GetValueOrDefault(u.Kind) + 1; if (u.Mini) mini++; }
            }
        Console.WriteLine($"{blocks} plan blocks round the centre planned in {sw.ElapsedMilliseconds} ms ({sw.ElapsedMilliseconds / (double)blocks:0.0} ms each)");
        int quadrants = units.Sum(p => p.Key is L3999Kind.GameHall or L3999Kind.Natatorium ? 2 * p.Value : p.Value);
        var weights = new Dictionary<L3999Kind, double> { [L3999Kind.Game] = 40, [L3999Kind.FoodCourt] = 14, [L3999Kind.Lobby] = 12, [L3999Kind.Lanes] = 5, [L3999Kind.Shuttered] = 8 };
        foreach (var (k, n) in units.OrderBy(p => p.Key))
        {
            string expect = weights.TryGetValue(k, out double w) ? $"  (weight share of single quadrants {w / 79:P0})" : "";
            Console.WriteLine($"  {k,-11} {n,4}  {(k is L3999Kind.GameHall or L3999Kind.Natatorium ? 2 * n : n) / (double)quadrants,6:P1} of quadrants{expect}");
        }
        Console.WriteLine($"  game areas with a mini arcade: {mini}");

        // Far out: the Blackout's share, natatoria
        int far = 0, dark = 0, nat = 0, farBlocks = 0;
        for (int bj = -110; bj <= 110; bj += 3)
            for (int bi = -110; bi <= 110; bi += 3)
            {
                double f = layout.L3999BlockFraction(bi, bj);
                if (f > 1) continue;
                farBlocks++;
                if (f >= 0.65) { far++; if (layout.L3999BlackoutBlock(bi, bj)) dark++; }
                if (layout.L3999UnitsOf(bi, bj).Any(u => u.Kind == L3999Kind.Natatorium)) nat++;
            }
        Console.WriteLine($"sampled {farBlocks} blocks over the whole region: Blackout {dark}/{far} past 65% ({dark / (double)Math.Max(1, far):P1}, plan ~7%); natatoria in {nat} blocks ({nat / (double)farBlocks:P1})");

        // Tiles of the central blocks: zones, walkways both ways, escalators, arrivals, reach
        var (ox, oz) = (layout.L3999OriginX, layout.L3999OriginZ);
        var zones = new Dictionary<L3999Zone, int>();
        var dirs = new Dictionary<ArchPier, int>();
        int escalators = 0, junctions = 0, total = 0;
        int x0 = ox - 128, z0 = oz - 128, size = 384;
        var floor = new bool[size * size];
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                Tile t = L3999Tile(layout, x0 + x, z0 + z);
                if (t.Level != Level3999) continue;
                total++;
                zones[(L3999Zone)t.Zone] = zones.GetValueOrDefault((L3999Zone)t.Zone) + 1;
                if (t.Variant == Props.L3999Walkway) dirs[t.Pier] = dirs.GetValueOrDefault(t.Pier) + 1;
                if (t.Variant == Props.L3999Escalator && t.Stair == 7) escalators++;
                if (t.Overhead == Overheads.L3999Sign3999) junctions++;
                floor[z * size + x] = t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.Water;
            }
        Console.WriteLine($"3x3 central blocks: {total} tiles; " + string.Join(", ", zones.OrderBy(p => p.Key).Select(p => $"{p.Key} {p.Value / (double)total:P1}")));
        Console.WriteLine($"  walkway treads by direction: " + string.Join(", ", dirs.Select(p => $"{p.Key} {p.Value}")) + $"; escalator top steps {escalators} (two tiles each) round {junctions} junctions");

        // Every unit's floor reachable from a concourse (walking over floors, doorways, water; props not counted)
        var seen = new bool[size * size];
        var queue = new Queue<int>();
        for (int i = 0; i < size * size; i++)
        {
            Tile t = L3999Tile(layout, x0 + i % size, z0 + i / size);
            if (floor[i] && t.Zone is (byte)L3999Zone.Concourse or (byte)L3999Zone.Junction) { seen[i] = true; queue.Enqueue(i); }
        }
        while (queue.Count > 0)
        {
            int i = queue.Dequeue(), x = i % size, z = i / size;
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                int n = nz * size + nx;
                if (seen[n] || !floor[n]) continue;
                seen[n] = true;
                queue.Enqueue(n);
            }
        }
        var cut = new Dictionary<L3999Zone, int>();
        for (int i = 0; i < size * size; i++)
            if (floor[i] && !seen[i]) { var zn = (L3999Zone)L3999Tile(layout, x0 + i % size, z0 + i / size).Zone; cut[zn] = cut.GetValueOrDefault(zn) + 1; }
        Console.WriteLine("  floor not walkable to from a concourse: " + (cut.Count == 0 ? "none" : string.Join(", ", cut.Select(p => $"{p.Key} {p.Value}"))));

        // Arrivals
        int arrivals = 0, lobby = 0, nata = 0;
        for (ulong k = 1; k <= 40; k++)
        {
            if (layout.FindArrival(Level3999, k * 104729UL + 7) is { } a) { arrivals++; if (L3999Tile(layout, a.X, a.Z).Zone == (byte)L3999Zone.Lobby) lobby++; }
            if (layout.L3999NatatoriumArrival(k * 7919UL) is { } n && L3999Tile(layout, n.X, n.Z).Kind == TileKind.Water) nata++;
        }
        Console.WriteLine($"arrivals: {arrivals}/40 found, {lobby} on a lobby floor; natatorium arrivals afloat: {nata}/40");
        Console.WriteLine($"done in {sw.ElapsedMilliseconds} ms");
    }

    /// <summary>3999hash: the layout hash with the level's entrances in other levels left out, then with them, and the lines that differ.</summary>
    static void L3999HashMode(string[] args)
    {
        string Capture(bool entrances)
        {
            WorldLayout.L3999Entrances = entrances;
            var old = Console.Out;
            var sw = new StringWriter();
            Console.SetOut(sw);
            try { LayoutHash.Run(args); }
            finally { Console.SetOut(old); WorldLayout.L3999Entrances = true; }
            return sw.ToString();
        }
        string[] without = Capture(false).Split(Environment.NewLine), with = Capture(true).Split(Environment.NewLine);
        Console.WriteLine($"without Level 3999's entrances: {without.LastOrDefault(l => l.StartsWith("layout hash"))}");
        Console.WriteLine($"with them:                      {with.LastOrDefault(l => l.StartsWith("layout hash"))}");
        string world = "";
        int differ = 0;
        for (int i = 0; i < Math.Min(without.Length, with.Length); i++)
        {
            if (with[i].StartsWith("world")) world = with[i].Split(':')[0];
            if (without[i] != with[i]) { differ++; Console.WriteLine($"  {world} differs: {without[i].Trim()}  ->  {with[i].Trim()}"); }
        }
        if (differ == 0) Console.WriteLine("  no line differs (the entrances fall outside the sampled cells)");
    }

    static void L3999WaysMode(WorldLayout layout, long seed)
    {
        var net = new ThresholdNetwork(layout, new WorldGeometry(256), seed);
        var sw = System.Diagnostics.Stopwatch.StartNew();
        // Level 10's arcades
        int found = 0, squares = 0;
        WorldLayout.L3999ArcadeSite first = null;
        for (ulong k = 1; k <= 60 && found < 6; k++)
        {
            var site = layout.L3999ArcadeNear(k * 7919UL);
            squares++;
            if (site == null || site == first) continue;
            first ??= site;
            found++;
            bool all10 = true;
            double minGap = double.MaxValue, maxGap = 0;
            for (int m = 0; m < site.Mills.Length; m++)
            {
                var (mx, mz) = site.Mills[m];
                for (int dz = -4; dz <= 4; dz++) for (int dx = -4; dx <= 4; dx++) if (layout.LevelAt(MacroOf(mx + dx), MacroOf(mz + dz)) != 10) all10 = false;
                var prev = m == 0 ? (site.X, site.Z) : site.Mills[m - 1];
                double gap = Math.Sqrt(Math.Pow(mx - prev.Item1, 2) + Math.Pow(mz - prev.Item2, 2));
                minGap = Math.Min(minGap, gap); maxGap = Math.Max(maxGap, gap);
            }
            int doors = 0, beacons = 0;
            for (int dz = -20; dz <= 20; dz++) for (int dx = -20; dx <= 20; dx++) if (WorldLayout.IsL3999ArcadeDoor(layout.TileAt(site.X + dx, site.Z + dz))) doors++;
            foreach (var (mx, mz) in site.Mills) { Tile c = layout.TileAt(mx, mz); if (c.Under == Unders.L3999Windmill && c.Variant == 1) beacons++; }
            Console.WriteLine($"arcade at {site.X},{site.Z} facing {site.Facing}: door tiles {doors}/3, beacons {beacons}/5, windmills all in Level 10: {all10}, gaps {minGap:0}-{maxGap:0}");
        }
        Console.WriteLine($"{found} arcades found from {squares} searches ({sw.ElapsedMilliseconds} ms)");
        // Level 11's glitch walls
        (int X, int Z)? glitch = null;
        int cityBlocks = 0;
        for (int r = 0; r < 60 && glitch == null; r++)
            for (int dz = -r; dz <= r && glitch == null; dz++)
                for (int dx = -r; dx <= r && glitch == null; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    int mx = layout.CityOriginX / 32 + dx * 4, mz = layout.CityOriginZ / 32 + dz * 3;
                    if (layout.LevelAt(mx, mz) != 11) continue;
                    cityBlocks++;
                    Tile[] tiles = layout.BuildMacro(mx, mz);
                    for (int i = 0; i < tiles.Length; i++) if (tiles[i].Under == Unders.L3999GlitchWall) { glitch = (mx * 32 + i % 32, mz * 32 + i / 32); break; }
                }
        Console.WriteLine(glitch is { } g ? $"glitch wall at {g.X},{g.Z} (after {cityBlocks} city cells)" : $"no glitch wall in {cityBlocks} city cells");
        // Level 37's magenta tiles
        (int X, int Z)? magenta = null;
        for (ulong k = 1; k <= 400 && magenta == null; k++)
        {
            var a = layout.FindArrival(Poolrooms, k * 104729UL + 11);
            if (a == null) continue;
            for (int dz = -3; dz <= 3 && magenta == null; dz++)
                for (int dx = -3; dx <= 3 && magenta == null; dx++)
                {
                    Tile[] tiles = layout.BuildMacro(MacroOf(a.Value.X) + dx * 3, MacroOf(a.Value.Z) + dz * 3);
                    for (int i = 0; i < tiles.Length; i++) if (tiles[i].Under == Unders.L3999MagentaTiles) { magenta = ((MacroOf(a.Value.X) + dx * 3) * 32 + i % 32, (MacroOf(a.Value.Z) + dz * 3) * 32 + i / 32); break; }
                }
        }
        Console.WriteLine(magenta is { } mg ? $"magenta tiles at {mg.X},{mg.Z} (depth {layout.TileAt(mg.X, mg.Z).Depth})" : "no magenta tiles found near Poolrooms arrivals (they lie past 40% of its radius)");

        // Through each and back
        void Report(string label, Passage p, Link? home)
        {
            if (p == null) { Console.WriteLine($"  {label,-28} no passage"); return; }
            Link? to = net.Take(p, home);
            if (to is not { } l) { Console.WriteLine($"  {label,-28} leads nowhere"); return; }
            int ax = (int)Math.Floor(l.X), az = (int)Math.Floor(l.Z);
            Tile at = layout.TileAt(ax, az);
            string back = !p.TwoWay ? "one-way" : l.Marker ? (net.TryGet((ax, az), out Link b) && b == home ? "thin spot back ok" : "thin spot BAD")
                : p.ReturnFeature != null && layout.FeatureBeside(ax, az, p.ReturnFeature) is { } f && net.TryGet(f, out Link b2) && b2 == home ? $"paired with the {f} ok" : "back BAD";
            Console.WriteLine($"  {label,-28} -> L{DisplayNumber(at.Level),-4} {ax},{az} zone {at.Zone} {(at.Kind == TileKind.Water ? "afloat" : "")}  {back}; again {(net.Take(p, home) == l ? "same" : "DIFFERS")}");
        }
        Console.WriteLine("going through:");
        if (first != null)
            Report("L10 arcade revolving door", net.Used(first.X, first.Z, "l3999-revolving", out _), new Link(first.X + 0.5, 1000, first.Z + 0.5, false));
        if (glitch is { } gw) Report("L11 glitch wall", net.Walked(gw.X, gw.Z, layout.TileAt(gw.X, gw.Z), 1.2), net.HomeBeside(gw));
        if (magenta is { } mt) Report("L37 magenta tiles", net.Walked(mt.X, mt.Z, layout.TileAt(mt.X, mt.Z), -300), null);
        // In 3999 itself: the first of each kind round some arrivals
        var done = new HashSet<string>();
        for (ulong k = 1; k <= 30 && done.Count < 6; k++)
        {
            var a = layout.FindArrival(Level3999, k * 104729UL + 7);
            if (a == null) continue;
            for (int dz = -100; dz <= 100; dz++)
                for (int dx = -100; dx <= 100; dx++)
                {
                    int x = a.Value.X + dx, z = a.Value.Z + dz;
                    Tile t = layout.TileAt(x, z);
                    string kind = L3999UseKind(t);
                    if (kind != null && done.Add(kind == "l3999-staff" && net.Used(x, z, kind, out _) == null ? "staff-locked" : kind))
                    {
                        Passage p = net.Used(x, z, kind, out string refusal);
                        if (p == null) { Console.WriteLine($"  {kind,-28} refused: {refusal}"); continue; }
                        Report(kind + (kind == "l3999-cabinet" ? $" ({L3999Themes[t.Stack]})" : ""), p, new Link(x + 0.5, 1000, z + 0.5, false));
                    }
                    string label = L3999LinkLabel(t);
                    if (label != null && t.Level == Level3999 && done.Add(label)) Report(label, net.Walked(x, z, t, -300), null);
                }
        }
        // The rare ones, further out: a natatorium's drain, a rusted cabinet (only within 24 blocks of the Blackout)
        bool drain = false, rusted = false;
        for (int r = 30; r <= 90 && !(drain && rusted); r++)
            for (int k = 0; k < 64 && !(drain && rusted); k++)
            {
                int bi = (int)Math.Round(Math.Cos(k * Math.PI / 32) * r), bj = (int)Math.Round(Math.Sin(k * Math.PI / 32) * r);
                foreach (var u in layout.L3999UnitsOf(bi, bj))
                {
                    if (u.Kind is not (L3999Kind.Natatorium or L3999Kind.Game or L3999Kind.GameHall)) continue;
                    if (u.Kind == L3999Kind.Natatorium ? drain : rusted) continue;
                    int bx = layout.L3999OriginX + bi * L3999Block, bz = layout.L3999OriginZ + bj * L3999Block;
                    for (int c = u.C0; c <= u.C1; c++)
                        for (int a = u.A0; a <= u.A1; a++)
                        {
                            Tile t = layout.TileAt(bx + a, bz + c);
                            if (!drain && t.Under == Unders.L3999Drain) { drain = true; Report("natatorium drain", net.Walked(bx + a, bz + c, t, -300), null); }
                            if (!rusted && t.Variant == Props.L3999Rusted && t.Level == Level3999) { rusted = true; Report("rusted cabinet", net.Walked(bx + a, bz + c, t, 1.2), null); }
                        }
                }
            }
        if (!drain) Console.WriteLine("  (no natatorium drain found)");
        if (!rusted) Console.WriteLine("  (no rusted cabinet found)");
        // The Hub's door marked 3999, and The End's TRUEEND.EXE
        var staff = net.L3999StaffDoorArrival()(12345);
        Console.WriteLine(staff is { } s ? $"  Hub door arrival             -> {s.X},{s.Z} beside a staff door: {layout.FeatureBeside(s.X, s.Z, ThresholdNetwork.L3999StaffDoor) != null}" : "  Hub door arrival: none");
        int trueEnds = 0;
        for (int i = 0; i < 2000; i++) if (net.L3999TrueEnd(i * 37, i * 91, false) != null) trueEnds++;
        Console.WriteLine($"  TRUEEND.EXE on {trueEnds} of 2000 sample computers ({trueEnds / 20.0:0.0}%; of the three in four that are not \"=)\")");
        Console.WriteLine($"done in {sw.ElapsedMilliseconds} ms");
    }

    static void L3999MapMode(WorldLayout layout, int bi0, int bj0, int n, string path)
    {
        int size = n * L3999Block;
        int x0 = layout.L3999OriginX + bi0 * L3999Block, z0 = layout.L3999OriginZ + bj0 * L3999Block;
        using var w = new BinaryWriter(File.Create(path));
        w.Write(System.Text.Encoding.ASCII.GetBytes($"P6 {size} {size} 255\n"));
        byte[] Rgb(Tile t)
        {
            if (t.Level != Level3999) return new byte[] { 0, 0, 0 };
            bool dark = L3999IsDark(t);
            byte[] c = t.Kind switch
            {
                TileKind.Wall => t.Pattern == WallPattern.L3999Shopfront ? new byte[] { 120, 200, 230 } : t.Pattern == WallPattern.L3999Window ? new byte[] { 255, 160, 60 } : new byte[] { 40, 30, 60 },
                TileKind.Door => t.Pattern == WallPattern.L3999Revolving ? new byte[] { 255, 255, 0 } : t.Pattern == WallPattern.L3999Elevator ? new byte[] { 255, 0, 255 } : new byte[] { 200, 90, 40 },
                TileKind.Doorway => new byte[] { 200, 200, 200 },
                TileKind.Water => new byte[] { 140, 60, 220 },
                _ => (L3999Zone)t.Zone switch
                {
                    L3999Zone.Concourse or L3999Zone.Junction => L3999HasSlab(t) ? new byte[] { 150, 150, 160 } : new byte[] { 220, 220, 225 },
                    L3999Zone.Service => new byte[] { 110, 110, 110 },
                    L3999Zone.Game or L3999Zone.GameHall => new byte[] { 50, 20, 90 },
                    L3999Zone.FoodCourt => new byte[] { 230, 150, 70 },
                    L3999Zone.Lobby => new byte[] { 200, 120, 200 },
                    L3999Zone.Lanes => new byte[] { 190, 150, 90 },
                    L3999Zone.Shuttered => new byte[] { 90, 90, 80 },
                    L3999Zone.MiniArcade => new byte[] { 255, 60, 120 },
                    _ => new byte[] { 180, 200, 255 },
                },
            };
            if (t.Kind == TileKind.Floor && t.Variant != 0) c = t.Variant == Props.L3999Walkway ? new byte[] { 60, 220, 220 } : t.Variant == Props.L3999Escalator ? new byte[] { 255, 230, 0 }
                : new byte[] { (byte)(c[0] / 2 + 60), (byte)(c[1] / 2 + 10), (byte)(c[2] / 2 + 60) };
            if (dark) c = new byte[] { (byte)(c[0] / 4), (byte)(c[1] / 4), (byte)(c[2] / 4) };
            return c;
        }
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++) w.Write(Rgb(L3999Tile(layout, x0 + x, z0 + z)));
        Console.WriteLine($"wrote {path}: blocks {bi0},{bj0} +{n}, {size}x{size}, world {x0},{z0}");
    }
}
