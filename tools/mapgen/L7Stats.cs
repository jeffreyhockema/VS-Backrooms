using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>
/// l7: the way down from Level 6 to Level 7 and what lies in Level 7's deep (layout version 9's redesign).
/// <list type="bullet">
/// <item><c>l7 stairs</c>: how many stairwells down Level 6 has, by how far into its ring: squares of 8 by 8 cells at
/// eight angles and five depths, counted by threshold (FeatureOrigin), with the first of each depth.</item>
/// <item><c>l7 sites</c>: Level 7's entry rooms and sunken rooms (twilight and midnight) in squares of 8 by 8 cells at
/// eight angles and five depths, and where the first few are (for a server's /backrooms dump).</item>
/// <item><c>l7 map &lt;x&gt; &lt;z&gt; &lt;radius&gt; &lt;file&gt;</c>: the tiles round a block, one line per row of
/// "kind zone depth under stair variant level" numbers, for tools' renderers.</item>
/// <item><c>l7 trip</c>: down a stairwell and back up an entry room's stairs, through the network, and where each puts you.</item>
/// </list>
/// </summary>
static class L7Stats
{
    static (double In, double Out) Ring(WorldLayout layout, int smx, int smz, int level, double angle)
    {
        double rIn = -1, rOut = -1;
        for (double r = 1; r < 1400; r += 0.5)
        {
            int lv = layout.LevelAt(smx + (int)Math.Round(Math.Cos(angle) * r), smz + (int)Math.Round(Math.Sin(angle) * r));
            if (lv == level && rIn < 0) rIn = r;
            if (rIn >= 0 && lv > level && lv < 12) { rOut = r; break; }
        }
        return (rIn, rOut < 0 ? rIn + 20 : rOut);
    }

    public static void Run(WorldLayout layout, string[] args, long seed, int smx, int smz)
    {
        string mode = args.Length > 3 ? args[3] : "stairs";
        Console.WriteLine($"layout version {layout.Version}");
        if (mode == "map") { Map(layout, int.Parse(args[4]), int.Parse(args[5]), int.Parse(args[6]), args[7]); return; }
        if (mode == "trip") { Trip(layout, seed); return; }
        bool stairs = mode == "stairs";
        int level = stairs ? 6 : 7;
        double[] depths = { 0.1, 0.3, 0.5, 0.7, 0.9 };
        const int side = 4, angles = 32;
        int grandTotal = 0, grandCells = 0;
        double widths = 0;
        for (int a = 0; a < angles; a++) { var (i, o) = Ring(layout, smx, smz, level, a * Math.PI * 2 / angles + 0.3); widths += o - i; }
        Console.WriteLine($"Level {level}'s ring is {widths / angles:0.0} cells wide on average; squares of {side} by {side} cells at {angles} angles");
        foreach (double depth in depths)
        {
            var found = new HashSet<(int, int)>();
            int cells = 0, entry = 0, twilight = 0, midnight = 0;
            (int, int)? first = null, firstTw = null, firstMid = null, firstEntry = null;
            for (int a = 0; a < angles; a++)
            {
                double angle = a * Math.PI * 2 / angles + 0.3;
                var (rIn, rOut) = Ring(layout, smx, smz, level, angle);
                double r = rIn + depth * (rOut - rIn);
                int cx = smx + (int)Math.Round(Math.Cos(angle) * r), cz = smz + (int)Math.Round(Math.Sin(angle) * r);
                for (int mz = cz - side / 2; mz < cz + side / 2; mz++)
                    for (int mx = cx - side / 2; mx < cx + side / 2; mx++)
                    {
                        if (layout.LevelAt(mx, mz) != level) continue;
                        cells++;
                        Tile[] tiles = layout.BuildMacro(mx, mz);
                        for (int i = 0; i < tiles.Length; i++)
                        {
                            Tile t = tiles[i];
                            int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
                            if (stairs)
                            {
                                if (!WorldLayout.IsDescent(t)) continue;
                                var origin = layout.FeatureOrigin(x, z, q => WorldLayout.IsDescent(q));
                                if (found.Add(origin)) first ??= origin;
                                continue;
                            }
                            if (t.Level != 7) continue;
                            if (t.Zone is >= 1 and <= WorldLayout.L7ZoneLadder)
                            {
                                var origin = layout.FeatureOrigin(x, z, q => q.Level == 7 && q.Zone is >= 1 and <= WorldLayout.L7ZoneLadder);
                                if (found.Add(origin)) { entry++; firstEntry ??= (x, z); }
                            }
                            if (t.Zone == WorldLayout.L7ZoneBellHatch)
                            {
                                if (t.Height >= WorldLayout.MidnightDepth) { midnight++; firstMid ??= (x, z); }
                                else { twilight++; firstTw ??= (x, z); }
                            }
                        }
                    }
            }
            if (stairs)
            {
                grandTotal += found.Count; grandCells += cells;
                Console.WriteLine($"depth {depth:0.0}: {cells,4} Level 6 cells, {found.Count,3} stairwells down ({1000.0 * found.Count / Math.Max(1, cells):0.0} per 1000 cells)" + (first is { } f ? $"  e.g. {f}" : ""));
            }
            else
                Console.WriteLine($"depth {depth:0.0}: {cells,4} Level 7 cells, {entry,3} entry rooms, {twilight,3} sunken rooms in the twilight zone, {midnight,3} in the midnight zone"
                    + (firstEntry is { } e ? $"  entry e.g. {e}" : "") + (firstTw is { } tw ? $"  twilight e.g. {tw}" : "") + (firstMid is { } mi ? $"  midnight e.g. {mi}" : ""));
        }
        if (stairs) Console.WriteLine($"all: {grandCells} cells, {grandTotal} stairwells ({1000.0 * grandTotal / Math.Max(1, grandCells):0.0} per 1000 cells)");
    }

    /// <summary>Down a stairwell (the first found) and on, then back up the entry room's stairs.</summary>
    static void Trip(WorldLayout layout, long seed)
    {
        var geometry = new WorldGeometry(256);
        var net = new ThresholdNetwork(layout, geometry, seed);
        if (layout.FindDescentLanding(12345) is not { } landing) { Console.WriteLine("no stairwell found"); return; }
        Tile lt = layout.TileAt(landing.X, landing.Z);
        Console.WriteLine($"stairwell landing (first row) at {landing}: under {lt.Under}, pier {lt.Pier}");
        // Walk on to the far rows of the landing
        (int dx, int dz) = lt.Pier == ArchPier.East ? (1, 0) : (0, 1);
        int fx = landing.X + dx, fz = landing.Z + dz;
        Passage down = net.Walked(fx, fz, layout.TileAt(fx, fz), WorldLayout.L6DescentTripRel - 0.4);
        Console.WriteLine($"on the landing's first row at feet {WorldLayout.L6DescentTripRel - 0.4}: {(net.Walked(landing.X, landing.Z, lt, WorldLayout.L6DescentTripRel - 0.4) == null ? "nothing (good)" : "TRIPS (bad)")}");
        Console.WriteLine($"on a step at feet -3: {(net.Walked(landing.X - dx * 3, landing.Z - dz * 3, layout.TileAt(landing.X - dx * 3, landing.Z - dz * 3), -3) == null ? "nothing (good)" : "TRIPS (bad)")}");
        if (down == null) { Console.WriteLine("the far row does not trip (bad)"); return; }
        Link? home = net.HomeFor(down);
        Link? to = net.Take(down, home);
        Console.WriteLine($"down: source {down.Source}, two-way {down.TwoWay}, home {home}, to {to}");
        if (to is not { } link) return;
        int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z);
        Tile at = layout.TileAt(ax, az);
        Console.WriteLine($"  arrival tile: level {at.Level} zone {at.Zone} detail {at.Detail} height {at.Height}; facing {net.DeepStairsFacing(ax, az)}; y over the floor {link.Y - geometry.FloorY:0.00}");
        var stairs = layout.FeatureBeside(ax, az, ThresholdNetwork.EntryStairs);
        Console.WriteLine($"  stairs beside: {stairs}; their link back: {(stairs is { } s && net.TryGet(s, out Link back) ? back.ToString() : "none")}");
        // And up those stairs
        if (stairs is not { } st) return;
        Tile step = layout.TileAt(st.X, st.Z);
        (int cx, int cz) = step.Pier switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
        int top = WorldLayout.EntryStairSteps - step.Stair;
        int ux = st.X + cx * top, uz = st.Z + cz * top;
        Passage up = net.Walked(ux, uz, layout.TileAt(ux, uz), WorldLayout.EntryStairTripRel + 0.2);
        Console.WriteLine($"  on step {layout.TileAt(ux, uz).Stair} at feet {WorldLayout.EntryStairTripRel + 0.2:0.0}: {(up == null ? "nothing (bad)" : $"up to {net.Take(up, net.HomeFor(up))}, same as home {home}")}");
        Console.WriteLine($"  on step 2 at feet 7.5: {(net.Walked(st.X + cx, st.Z + cz, layout.TileAt(st.X + cx, st.Z + cz), 7.5) == null ? "nothing (good)" : "TRIPS (bad)")}");
        // A fresh entry room's stairs, never come down: up them to some stairwell, and back down it
        for (ulong k = 2; k < 40; k++)
        {
            if (layout.FindEntryRoomArrival(k * 7919UL) is not { } e) continue;
            var other = layout.FeatureBeside(e.X, e.Z, ThresholdNetwork.EntryStairs);
            if (other is not { } o || net.TryGet(o, out _)) continue;
            Tile os = layout.TileAt(o.X, o.Z);
            (int ox, int oz) = os.Pier switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
            int otop = WorldLayout.EntryStairSteps - os.Stair;
            Passage up2 = net.Walked(o.X + ox * otop, o.Z + oz * otop, layout.TileAt(o.X + ox * otop, o.Z + oz * otop), 10);
            if (up2 == null) { Console.WriteLine("  fresh stairs do not trip (bad)"); break; }
            Link? home2 = net.HomeFor(up2);
            Link? to2 = net.Take(up2, home2);
            Console.WriteLine($"fresh entry room stairs {o}: up to {to2} (home {home2})");
            if (to2 is { } l2)
            {
                var desc = layout.FeatureBeside((int)Math.Floor(l2.X), (int)Math.Floor(l2.Z), ThresholdNetwork.Descent);
                Tile lt2 = layout.TileAt((int)Math.Floor(l2.X), (int)Math.Floor(l2.Z));
                Console.WriteLine($"  arrival: level {lt2.Level} under {lt2.Under}, y over the floor {l2.Y - geometry.FloorY:0.00}; stairwell beside {desc}, its link {(desc is { } dd && net.TryGet(dd, out Link b2) ? b2 + (b2 == home2 ? " = home (paired)" : " (not home)") : "none")}");
            }
            break;
        }
    }

    static void Map(WorldLayout layout, int x0, int z0, int radius, string file)
    {
        using var w = new StreamWriter(file);
        w.WriteLine($"# x0 {x0 - radius} z0 {z0 - radius} size {2 * radius + 1}; per tile: kind zone depth under stair variant level height detail");
        for (int z = z0 - radius; z <= z0 + radius; z++)
        {
            var row = new List<string>();
            for (int x = x0 - radius; x <= x0 + radius; x++)
            {
                Tile t = layout.TileAt(x, z);
                row.Add($"{(int)t.Kind},{t.Zone},{t.Depth},{t.Under},{t.Stair},{t.Variant},{t.Level},{t.Height},{t.Detail},{(t.SupplyBox ? 1 : 0)}");
            }
            w.WriteLine(string.Join(" ", row));
        }
        Console.WriteLine($"wrote {file}");
    }
}
