using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L14Zone;

/// <summary>Level 14's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 14stats [wings] [map]: over a square of (2 x wings + 1) wings round the region's centre: the departments, rooms of each
    /// kind, receptions, torture chambers, the research group's rooms, contaminated rooms, supply boxes, dark tiles, and whether
    /// every walkable tile can be walked to from the main halls (BAD lines for any that cannot). With "map", writes l14map.ppm
    /// (one pixel a block). 14showcase: the showcase spots with what is under each. 14links: see WorldLayout.Level14.Links.cs.
    /// </summary>
    static bool L14Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "14showcase")
        {
            foreach (var s in layout.L14ShowcaseSpots(new WorldGeometry(256)))
            {
                Tile t = layout.TileAt((int)Math.Floor(s.X), (int)Math.Floor(s.Z));
                Console.WriteLine($"spot {s.Name} {s.X} {s.Y} {s.Z} h{s.Heading:0} p{s.Pitch:0} | {s.Setup}  [L{t.Level} {WorldLayout.L14ZoneOf(t)} {t.Kind} v{t.Variant}]");
            }
            return true;
        }
        if (mode == "14links") return L14Links(layout, args);
        if (mode == "14dump")
        {
            // 14dump x z [r]: the tiles round a place as letters (# wall, D doorway, . floor, p prop, w walk-through prop, b box, c crates)
            int dx0 = int.Parse(args[3]), dz0 = int.Parse(args[4]), rr = args.Length > 5 ? int.Parse(args[5]) : 10;
            for (int z = dz0 - rr; z <= dz0 + rr; z++)
            {
                var sb = new System.Text.StringBuilder();
                for (int x = dx0 - rr; x <= dx0 + rr; x++)
                {
                    Tile t = layout.TileAt(x, z);
                    char c = t.Kind switch
                    {
                        TileKind.Wall => '#', TileKind.Doorway => (char)('0' + t.Detail),
                        TileKind.Floor => t.SupplyBox ? 'b' : t.Variant == 0 && t.Stack > 0 ? 'c' : t.Variant == 0 ? '.' : WorldLayout.IsWalkThroughProp(t.Variant) ? 'w' : 'p',
                        _ => '?',
                    };
                    if (x == dx0 && z == dz0) c = '@';
                    sb.Append(c);
                }
                Console.WriteLine(sb.ToString());
            }
            return true;
        }
        if (mode != "14stats") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int wn) ? wn : 3;
        bool map = args.Contains("map");
        const int P = WorldLayout.L14Period;
        int cx = layout.L14CentreX * WorldLayout.MacroSize + 16, cz = layout.L14CentreZ * WorldLayout.MacroSize + 16;
        int hcx = Hashing.FloorDiv(cx, P), hcz = Hashing.FloorDiv(cz, P);
        int x0 = (hcx - n) * P, x1 = (hcx + n + 1) * P + 5, z0 = (hcz - n) * P, z1 = (hcz + n + 1) * P + 5;
        Console.WriteLine($"region centre cells {layout.L14CentreX},{layout.L14CentreZ}, radius {layout.L14Radius}; window {2 * n + 1}x{2 * n + 1} wings round wing {hcx},{hcz}");
        var cells = new Dictionary<(int, int), Tile[]>();
        Tile T(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            if (!cells.TryGetValue((mx, mz), out var tiles)) cells[(mx, mz)] = tiles = layout.BuildMacro(mx, mz);
            return tiles[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
        }
        bool Walk(Tile t) => t.Level == WorldLayout.Level14 && (t.Kind is TileKind.Doorway && t.Detail != WorldLayout.L14DoorContam
            || t.Kind == TileKind.Floor && !(t.Stack > 0 && t.Variant == 0) && !t.SupplyBox && WorldLayout.IsWalkThroughProp(t.Variant));
        var reached = new HashSet<(int, int)>();
        var queue = new Queue<(int, int)>();
        var zones = new int[64];
        int walkable = 0, dark = 0, boxes = 0, lightsOn = 0;
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
            {
                Tile t = T(x, z);
                if (t.Level != WorldLayout.Level14) continue;
                if (t.Kind is TileKind.Floor or TileKind.Doorway) zones[(int)WorldLayout.L14ZoneOf(t)]++;
                if (WorldLayout.L14IsDark(t) && t.Kind == TileKind.Floor) dark++;
                if (t.SupplyBox) boxes++;
                if (t.Kind == TileKind.Floor && t.Ceiling is CeilingKind.L14LightOn or CeilingKind.L14LightBright) lightsOn++;
                if (!Walk(t)) continue;
                walkable++;
                if (WorldLayout.L14ZoneOf(t) == Zone.Hall && reached.Add((x, z))) queue.Enqueue((x, z));
            }
        while (queue.Count > 0)
        {
            var (x, z) = queue.Dequeue();
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < x0 || nz < z0 || nx > x1 || nz > z1 || reached.Contains((nx, nz)) || !Walk(T(nx, nz))) continue;
                reached.Add((nx, nz));
                queue.Enqueue((nx, nz));
            }
        }
        int lost = 0, shown = 0;
        var lostZones = new int[64];
        for (int z = z0 + 8; z <= z1 - 8; z++)
            for (int x = x0 + 8; x <= x1 - 8; x++)
            {
                Tile t = T(x, z);
                if (!Walk(t) || reached.Contains((x, z))) continue;
                lost++;
                lostZones[(int)WorldLayout.L14ZoneOf(t)]++;
                if (shown++ < 12) Console.WriteLine($"  BAD: not reached from the halls: {x},{z} {WorldLayout.L14ZoneOf(t)} {t.Kind} v{t.Variant}");
            }
        var depts = new int[8];
        int rooms = 0, rec = 0, tort = 0, res = 0, contam = 0, surg = 0;
        for (int hz = hcz - n; hz <= hcz + n; hz++)
            for (int hx = hcx - n; hx <= hcx + n; hx++)
            {
                var plan = layout.L14PlanOf(hx, hz);
                depts[(int)plan.Dept]++;
                rooms += plan.Rooms; rec += plan.Receptions; tort += plan.Tortures; res += plan.Research; contam += plan.Contaminated; surg += plan.Surgeries;
            }
        int wings = (2 * n + 1) * (2 * n + 1);
        Console.WriteLine($"wings {wings}: departments " + string.Join(", ", Enum.GetValues<WorldLayout.L14Dept>().Select(d => $"{d} {depts[(int)d]}")));
        Console.WriteLine($"rooms {rooms} ({rooms / (double)wings:0.0} a wing); receptions {rec}, surgeries {surg}, torture chambers {tort}, research {res}, contaminated {contam}; supply boxes {boxes}");
        Console.WriteLine("tiles by zone: " + string.Join(", ", Enum.GetValues<Zone>().Where(z => zones[(int)z] > 0).Select(z => $"{z} {zones[(int)z]}")));
        Console.WriteLine($"walkable {walkable}, dark floor {dark}, lights on {lightsOn}; not reached from the halls: {lost}"
            + (lost > 0 ? " (" + string.Join(", ", Enum.GetValues<Zone>().Where(z => lostZones[(int)z] > 0).Select(z => $"{z} {lostZones[(int)z]}")) + ")" : ""));
        if (map)
        {
            int w = x1 - x0 + 1, h = z1 - z0 + 1;
            using var f = new BinaryWriter(File.Create("l14map.ppm"));
            f.Write(System.Text.Encoding.ASCII.GetBytes($"P6 {w} {h} 255\n"));
            for (int z = z0; z <= z1; z++)
                for (int x = x0; x <= x1; x++)
                {
                    Tile t = T(x, z);
                    (int r, int g, int b) c = t.Kind switch
                    {
                        TileKind.Doorway => (255, 220, 60),
                        TileKind.Floor => WorldLayout.L14ZoneOf(t) switch
                        {
                            Zone.Hall => (150, 190, 170), Zone.Corridor => (120, 160, 140), Zone.Reception => (230, 120, 220), Zone.Ward => (240, 240, 240),
                            Zone.Icu => (180, 220, 255), Zone.Psych => (255, 250, 200), Zone.Maternity => (255, 190, 200), Zone.Surgery => (90, 200, 120),
                            Zone.Storage => (170, 140, 100), Zone.Torture => (200, 20, 20), Zone.Research => (60, 120, 255), Zone.Office => (200, 200, 150),
                            _ => (130, 130, 130),
                        },
                        _ => (30, 30, 34),
                    };
                    if (t.Kind == TileKind.Floor && t.Variant != 0 && !WorldLayout.IsWalkThroughProp(t.Variant)) c = (c.r / 2, c.g / 2, c.b / 2);
                    if (t.Kind == TileKind.Floor && WorldLayout.L14IsContam(t)) c = (160, 255, 40);
                    if (t.Kind != TileKind.Wall && !reached.Contains((x, z)) && Walk(t)) c = (255, 0, 0);
                    f.Write((byte)c.r); f.Write((byte)c.g); f.Write((byte)c.b);
                }
            Console.WriteLine($"l14map.ppm: {w}x{h} from {x0},{z0}");
        }
        return true;
    }
}
