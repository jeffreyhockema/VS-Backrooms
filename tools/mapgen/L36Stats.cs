using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L36Zone;

/// <summary>
/// Level 36's harness modes (experimental; this file is the level's own):
/// <c>36stats [superblocks]</c> lays out the landside and a square of superblocks east of it round the centre line and
/// reports each zone's share, the superblocks' kinds, the gates (and C32s), the Travel Planner's spots, and how much of the
/// walkable floor can be walked to from a carousel (the cabins and bridges are sealed on purpose: reached by boarding);
/// <c>36map [width height [dx dz]]</c> (blocks, from the baggage wall, centred on the centre line, moved by dx, dz) writes l36map.bin (int width,
/// int height, then per tile: zone, kind, material bits, prop/overhead flags) for render_36.py;
/// <c>36links [rings]</c> (links, 2026-10-31) lists the doors into the airport in Levels 9 and 11 nearest the spawn and nearest
/// each host's middle (position, facing, distance), how many there are to a square kilometre of each host, and the level each
/// gate of the nearest piers flies to, with the doors in the baggage wall and the restroom sinks near the centre line.
/// </summary>
static partial class LevelModes
{
    static bool L36Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "36stats") { L36Stats(layout, args.Length > 3 ? int.Parse(args[3]) : 3); return true; }
        if (mode == "36shots") { L36Shots(layout); return true; }
        if (mode == "36links") { L36Links(layout, args.Length > 3 ? int.Parse(args[3]) : 400, long.Parse(args[0])); return true; }
        if (mode == "36map")
        {
            L36Map(layout, args.Length > 3 ? int.Parse(args[3]) : 1100, args.Length > 4 ? int.Parse(args[4]) : 1100,
                args.Length > 5 ? int.Parse(args[5]) : 0, args.Length > 6 ? int.Parse(args[6]) : 0);
            return true;
        }
        return false;
    }

    /// <summary>36shots: the showcase spots, each with the tile at its feet and how far the view runs clear along its heading.</summary>
    static void L36Shots(WorldLayout layout)
    {
        foreach (var s in Backrooms.Cheats.Showcase.For(WorldLayout.Level36, layout, new WorldGeometry(256)))
        {
            int x = (int)Math.Floor(s.X), z = (int)Math.Floor(s.Z);
            Tile t = layout.TileAt(x, z);
            double hx = Math.Sin(s.Heading * Math.PI / 180), hz = -Math.Cos(s.Heading * Math.PI / 180);
            int clear = 0;
            for (; clear < 200; clear++)
            {
                Tile n = layout.TileAt((int)Math.Floor(s.X + hx * (clear + 1)), (int)Math.Floor(s.Z + hz * (clear + 1)));
                if (n.Kind != TileKind.Floor) break;
            }
            Console.WriteLine($"{s.Name,-15} {s.X,9:0.0} {s.Z,9:0.0} h{s.Heading,5:0} p{s.Pitch,4:0}  {t.Kind} {(Zone)t.Zone} air {t.Height} prop {t.Variant}{(t.SupplyBox ? " box" : "")}{(WorldLayout.L36IsDark(t) ? " dark" : "")}  clear {clear}  level {layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z))}");
        }
    }

    static string L36LinkLabel(Tile t) => null;

    /// <summary>For the links mode: the doors under the airplane sign (in the hosts and the baggage wall) and the restroom sinks.</summary>
    static string L36UseKind(Tile t) =>
        WorldLayout.IsL36AirportDoor(t) || WorldLayout.IsL36LandDoor(t) ? "l36-airport" : t.Level == WorldLayout.Level36 && t.Kind == TileKind.Floor && t.Variant == Props.L36Sink ? "l36-sink" : null;

    /// <summary>36links: where the ways in and out are, and how common the ways in.</summary>
    static void L36Links(WorldLayout layout, int rings, long seed)
    {
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        var net = new Backrooms.Thresholds.ThresholdNetwork(layout, new WorldGeometry(256), seed);
        // The arrival is in the level asked for, on a floor tile
        bool Lands(Backrooms.Thresholds.Link l, int level, string line)
        {
            Tile at = layout.TileAt((int)Math.Floor(l.X), (int)Math.Floor(l.Z));
            if (at.Level != level) { Bad(line + $": lands in level {at.Level}, not {level}"); return false; }
            if (at.Kind != TileKind.Floor) { Bad(line + $": the arrival tile is {at.Kind}, not floor"); return false; }
            return true;
        }
        int smx = 16000, smz = 16000;
        if (int.TryParse(Environment.GetEnvironmentVariable("SPAWN"), out int sp)) smx = smz = sp;
        double Km(int x, int z, int ox, int oz) => Math.Sqrt((double)(x - ox) * (x - ox) + (double)(z - oz) * (z - oz)) / 1000;
        foreach (int host in new[] { 11, 9 })
        {
            var (cx, cz) = layout.L36HostCentre(host);
            Console.WriteLine($"Level {host}: middle cell {cx},{cz} (blocks {cx * 32},{cz * 32}), {Km(cx * 32, cz * 32, smx * 32, smz * 32):0.0} km from the spawn");
            // How common: every cell of the host within the window round its middle, and the doors in them
            long cells = 0;
            int doors = 0, chosen = 0;
            var near = new List<(int X, int Z, ArchPier F)>();
            for (int mz = cz - rings; mz <= cz + rings; mz++)
                for (int mx = cx - rings; mx <= cx + rings; mx++)
                {
                    if (layout.LevelAt(mx, mz) != host) continue;
                    cells++;
                    if (!layout.IsL36EntranceCell(mx, mz)) continue;
                    chosen++;
                    Tile[] tiles = layout.BuildMacro(mx, mz);
                    for (int i = 0; i < tiles.Length; i++)
                        if (WorldLayout.IsL36AirportDoor(tiles[i])) { doors++; near.Add((mx * 32 + i % 32, mz * 32 + i / 32, tiles[i].Pier)); }
                }
            double km2 = cells * 32.0 * 32.0 / 1e6;
            Console.WriteLine($"  window of {2 * rings + 1} cells square round it: {cells} cells of the level ({km2:0.0} km2), {chosen} chosen, {doors} doors"
                + $" = {doors / Math.Max(km2, 1e-9):0.000} a km2, one to {km2 / Math.Max(doors, 1):0.0} km2 (mean spacing about {Math.Sqrt(km2 / Math.Max(doors, 1)):0.0} km)");
            near.Sort((a, b) => Km(a.X, a.Z, cx * 32, cz * 32).CompareTo(Km(b.X, b.Z, cx * 32, cz * 32)));
            for (int i = 0; i < Math.Min(5, near.Count); i++)
            {
                var (x, z, f) = near[i];
                double nn = double.MaxValue;
                foreach (var o in near) if (o.X != x || o.Z != z) nn = Math.Min(nn, Km(x, z, o.X, o.Z));
                Console.WriteLine($"  door at {x},{z} facing {f}: {Km(x, z, cx * 32, cz * 32):0.00} km from the middle, {Km(x, z, smx * 32, smz * 32):0.0} km from the spawn, the next door {nn:0.00} km off");
            }
            // The nearest to the spawn: rings out from the spawn
            var fromSpawn = layout.L36HostDoorsNear(smx, smz, 6000, 3, host);
            foreach (var d in fromSpawn)
                Console.WriteLine($"  nearest the spawn: {d.X},{d.Z} facing {d.Facing}, {Km(d.X, d.Z, smx * 32, smz * 32):0.00} km from the spawn");
            if (near.Count == 0) Bad($"no door into the airport in Level {host}'s window");
            foreach (var (x, z, _) in near.Take(2))
            {
                var p = net.Used(x, z, "l36-airport", out string refusal);
                if (p == null) { Bad($"airport door {x},{z} in Level {host} leads nowhere ({refusal})"); continue; }
                var home = new Backrooms.Thresholds.Link(x + 0.5, 1000, z + 0.5, false);
                if (net.Take(p, home) is not { } arr) { Bad($"airport door {x},{z}: no arrival"); continue; }
                int ax = (int)Math.Floor(arr.X), az = (int)Math.Floor(arr.Z);
                string line = $"  Level {host} airport door {x},{z} -> {ax} {az}";
                if (!Lands(arr, WorldLayout.Level36, line)) continue;
                if (layout.FeatureBeside(ax, az, WorldLayout.IsL36LandDoor) is not { } bd) { Bad(line + ": no baggage-wall door beside the arrival"); continue; }
                var q = net.Used(bd.X, bd.Z, "l36-airport", out _);
                var again = q == null ? (Backrooms.Thresholds.Link?)null : net.Take(q, null);
                if (again != home) { Bad(line + $": the baggage-wall door {bd.X},{bd.Z} does not lead back"); continue; }
                Console.WriteLine(line + $", back through {bd.X},{bd.Z}");
            }
        }
        // Inside: the doors in the baggage wall, the gates' flights, the sinks, near the centre line
        int wx = layout.L36WallX, lz = layout.L36LineZ;
        int land = 0;
        for (int z = lz - 1024; z < lz + 1024; z++) if (WorldLayout.IsL36LandDoor(layout.TileAt(wx, z))) land++;
        Console.WriteLine($"Level 36: {land} doors under the airplane sign in 2048 blocks of the baggage wall (x {wx})");
        var count = new int[WorldLayout.L36FlightLevels.Length];
        int gates = 0, sinks = 0;
        var firstTo = new int[WorldLayout.L36FlightLevels.Length];
        (int X, int Z)? firstSink = null;
        for (int sx = 0; sx < 4; sx++)
            for (int sz = -3; sz <= 3; sz++)
            {
                WorldLayout.L36Plan plan = layout.L36PlanOf(sx, sz);
                foreach (WorldLayout.L36Gate g in plan.Gates)
                {
                    if (g.SupportGroup) continue;
                    gates++;
                    {
                        var fp = net.Used(g.DoorX, g.DoorZ, "l36-flight", out string fref);
                        int want = WorldLayout.L36LevelOf(layout.L36FlightTo(g));
                        if (fp == null) Bad($"gate {g.Code} flight leads nowhere ({fref})");
                        else if (net.Take(fp, null) is not { } fl) Bad($"gate {g.Code} flight: no arrival");
                        else Lands(fl, want, $"  gate {g.Code} ({g.DoorX},{g.DoorZ}) flight");
                    }
                    count[layout.L36FlightIndex(g.DoorX, g.DoorZ)]++;
                    if (firstTo[layout.L36FlightIndex(g.DoorX, g.DoorZ)]++ > 0) continue;
                    string board = "none";
                    for (int dz = -4; dz <= 4; dz++)
                        for (int dx = -4; dx <= 4; dx++)
                            if (layout.TileAt(g.DoorX + dx, g.DoorZ + dz) is { Overhead: Overheads.L36Fids } st) board = WorldLayout.L36FidsTexts[st.Depth];
                    Console.WriteLine($"  the first gate to it: {g.Code} (door {g.DoorX},{g.DoorZ}) flies to Level {layout.L36FlightTo(g)}; its screen: {board}");
                }
                for (int i = 0; i < plan.Tiles.Length; i++)
                    if (plan.Tiles[i].Variant == Props.L36Sink)
                    {
                        sinks++;
                        firstSink ??= (plan.X0 + i % WorldLayout.L36Size, plan.Z0 + i / WorldLayout.L36Size);
                    }
            }
        Console.Write($"  {gates} gates in 4 x 7 superblocks fly to:");
        for (int i = 0; i < count.Length; i++) Console.Write($" {WorldLayout.L36FlightLevels[i]}: {count[i]}");
        Console.WriteLine($"; {sinks} restroom sinks, the first at {firstSink}");
        for (int z = lz; z < lz + 256; z++)
            if (WorldLayout.IsL36LandDoor(layout.TileAt(wx, z)))
            {
                Console.WriteLine($"  the first door in the baggage wall south of the centre line: {wx},{z}");
                if (net.Used(wx, z, "l36-airport", out string wref) != null || wref != "locked") Bad($"baggage-wall door {wx},{z} that nobody came in by is not locked");
                break;
            }
        if (land == 0) Bad("no baggage-wall doors on the centre line");
        if (gates == 0) Bad("no gates");
        if (firstSink is { } fs)
        {
            var sinkp = net.Used(fs.X, fs.Z, "l36-sink", out string sref);
            if (sinkp == null) Bad($"restroom sink {fs.X},{fs.Z} leads nowhere ({sref})");
            else if (net.Take(sinkp, null) is not { } sl) Bad("restroom sink: no arrival");
            else Lands(sl, WorldLayout.Poolrooms, $"  restroom sink {fs.X},{fs.Z}");
        }
        else Bad("no restroom sinks");
        Console.WriteLine(bad == 0 ? "36links: OK" : $"36links: {bad} problem(s)");
    }

    static void L36Map(WorldLayout layout, int w, int h, int dx, int dz)
    {
        int x0 = layout.L36WallX - 8 + dx, z0 = layout.L36LineZ - h / 2 + dz;
        using var f = new BinaryWriter(File.Create("l36map.bin"));
        f.Write(w);
        f.Write(h);
        for (int z = 0; z < h; z++)
            for (int x = 0; x < w; x++)
            {
                Tile t = layout.TileAt(x0 + x, z0 + z);
                bool ours = layout.LevelAt(WorldLayout.MacroOf(x0 + x), WorldLayout.MacroOf(z0 + z)) == WorldLayout.Level36;
                f.Write((byte)(ours ? t.Zone : 255));
                f.Write((byte)t.Kind);
                f.Write(t.Detail);
                f.Write((byte)((t.Variant != 0 ? 1 : 0) | (t.Overhead != 0 ? 2 : 0) | (t.SupplyBox ? 4 : 0) | (t.Ceiling is CeilingKind.LightOn ? 8 : 0)));
            }
        Console.WriteLine($"wrote l36map.bin: {w} x {h} from {x0},{z0}");
    }

    static void L36Stats(WorldLayout layout, int n)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        int x0 = layout.L36WallX, x1 = x0 + WorldLayout.L36Airside + n * WorldLayout.L36Period - 1;
        int z0 = layout.L36LineZ - n * WorldLayout.L36Period / 2, z1 = z0 + n * WorldLayout.L36Period - 1;
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        var zones = new long[32];
        long walk = 0, cabin = 0, dark = 0, limit = 0, boxes = 0;
        var tiles = new Tile[w * h];
        for (int z = 0; z < h; z++)
            for (int x = 0; x < w; x++)
            {
                Tile t = tiles[x + z * w] = layout.TileAt(x0 + x, z0 + z);
                zones[t.Kind == TileKind.Floor ? t.Zone : (byte)Zone.Wall]++;
                if (t.Kind != TileKind.Floor) continue;
                walk++;
                if (t.Zone is (byte)Zone.Cabin or (byte)Zone.Bridge) cabin++;
                if (WorldLayout.L36IsDark(t)) dark++;
                if ((t.Detail & WorldLayout.L36LimitBit) != 0) limit++;
                if (t.SupplyBox) boxes++;
            }
        Console.WriteLine($"Level 36: landside and {n} x {n} superblocks round the centre line ({w} x {h} blocks from {x0},{z0}); {sw.ElapsedMilliseconds} ms");
        foreach (Zone zone in Enum.GetValues<Zone>())
            if (zones[(int)zone] > 0) Console.WriteLine($"  {zone,-10} {100.0 * zones[(int)zone] / tiles.Length,5:0.0}%");
        Console.WriteLine($"  floor {walk}: blackout {dark}, Absolute Limit {limit}, supply boxes {boxes}, cabins and bridges {cabin}");
        var kinds = new Dictionary<WorldLayout.L36Kind, int>();
        int gates = 0, c32 = 0;
        for (int sz = -n / 2; sz < n - n / 2; sz++)
            for (int sx = 0; sx < n; sx++)
            {
                var k = layout.L36KindOf(sx, sz);
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
                if (k != WorldLayout.L36Kind.Pier) continue;
                var plan = layout.L36PlanOf(sx, sz);
                gates += plan.Gates.Count;
                foreach (var g in plan.Gates) if (g.SupportGroup) c32++;
            }
        Console.WriteLine("  superblocks: " + string.Join(", ", kinds) + $"; gates {gates}, C32 {c32}");
        int sites = 0;
        for (int mz = WorldLayout.MacroOf(z0); mz <= WorldLayout.MacroOf(z1); mz++)
            for (int mx = WorldLayout.MacroOf(x0); mx <= WorldLayout.MacroOf(x1); mx++)
                if (layout.WandererSite(mx, mz) is { } s && layout.IsEntitySpot(s.X, s.Z)) sites++;
        Console.WriteLine($"  Travel Planner spots (standable): {sites}");
        // Reach: from a carousel near the centre line, over walkable floor (props that block not counted as walls)
        int sx0 = 8, sz0 = h / 2;
        while (sz0 < h && tiles[sx0 + sz0 * w].Kind != TileKind.Floor) sz0++;
        var seen = new bool[w * h];
        var q = new Queue<int>();
        q.Enqueue(sx0 + sz0 * w);
        seen[sx0 + sz0 * w] = true;
        long reached = 0;
        while (q.Count > 0)
        {
            int i = q.Dequeue();
            reached++;
            int x = i % w, z = i / w;
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= w || nz >= h) continue;
                int j = nx + nz * w;
                if (seen[j] || tiles[j].Kind != TileKind.Floor) continue;
                seen[j] = true;
                q.Enqueue(j);
            }
        }
        long sealedOther = 0;
        var byZone = new Dictionary<Zone, long>();
        var sample = new Dictionary<Zone, (int, int)>();
        for (int i = 0; i < tiles.Length; i++)
            if (tiles[i].Kind == TileKind.Floor && !seen[i] && tiles[i].Zone is not ((byte)Zone.Cabin or (byte)Zone.Bridge))
            {
                sealedOther++;
                byZone[(Zone)tiles[i].Zone] = byZone.GetValueOrDefault((Zone)tiles[i].Zone) + 1;
                sample.TryAdd((Zone)tiles[i].Zone, (x0 + i % w, z0 + i / w));
            }
        Console.WriteLine($"  reached from a carousel: {reached} of {walk} floor tiles; not reached (not cabins): {sealedOther} " + string.Join(", ", byZone) + "; e.g. " + string.Join(", ", sample));
    }
}
