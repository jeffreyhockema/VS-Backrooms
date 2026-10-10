using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>Level 974's harness modes (this file is the level's own; see docs/new-levels/CONTRACT.md).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 974stats [houses]: checks a sample of Kitty's houses (each has its arrival tile, every room, everything inside
    /// reachable from the arrival, no doorway blocked, both ways round), draws the first two, and goes through Kitty's
    /// wake-up from each (a safe place in Level 4, 37 or 6.1, the same every time).
    /// </summary>
    static bool L974Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode != "974stats") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int k) ? k : 60;
        var net = new ThresholdNetwork(layout, new WorldGeometry(256), 12345);
        int houses = 0, bad = 0, mirrored = 0, arrivals = 0;
        var wakeTo = new SortedDictionary<int, int>();
        int wakeNone = 0, wakeUnstable = 0, drawn = 0;
        var seen = new HashSet<(int, int)>();
        for (ulong key = 1; houses < n && key < (ulong)n * 20; key++)
        {
            ulong h = Hashing.Mix(key * 7919UL);
            if (layout.L974HouseCellFor(h) is not { } cell || !seen.Add(cell)) continue;
            houses++;
            var (mx, mz) = cell;
            Tile[] tiles = layout.BuildMacro(mx, mz);
            Tile T(int x, int z) => tiles[WorldLayout.TileIndex(x - mx * 32, z - mz * 32)];
            if (layout.L974Mirrored(mx, mz)) mirrored++;
            var (ax, az) = layout.L974Arrival(mx, mz);
            if (T(ax, az).Under != Unders.L974Arrival) { bad++; Console.WriteLine($"  house {mx},{mz}: no arrival tile at {ax},{az}"); continue; }
            arrivals++;

            // Everything inside reachable from the arrival, walking (doorways, floor, the rug)
            bool Walk(Tile t) => t.Kind == TileKind.Doorway || t.Kind == TileKind.Floor && (t.Variant == 0 || t.Variant == Props.L974Rug);
            var reach = new HashSet<(int, int)> { (ax, az) };
            var q = new Queue<(int, int)>();
            q.Enqueue((ax, az));
            while (q.Count > 0)
            {
                var (x, z) = q.Dequeue();
                foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    int nx = x + dx, nz = z + dz;
                    if (WorldLayout.MacroOf(nx) != mx || WorldLayout.MacroOf(nz) != mz || !Walk(T(nx, nz)) || !reach.Add((nx, nz))) continue;
                    q.Enqueue((nx, nz));
                }
            }
            int floor = 0, walkable = 0, unreached = 0, blockedDoor = 0;
            var rooms = new HashSet<byte>();
            for (int i = 0; i < tiles.Length; i++)
            {
                Tile t = tiles[i];
                int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
                if (t.Kind == TileKind.Floor) { floor++; rooms.Add(t.Zone); }
                if (!Walk(t)) continue;
                walkable++;
                if (!reach.Contains((x, z))) unreached++;
                if (t.Kind == TileKind.Doorway)
                    foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        Tile nb = T(x + dx, z + dz);
                        bool across = t.Pier is ArchPier.North or ArchPier.South ? dz != 0 : dx != 0;
                        if (across && nb.Kind == TileKind.Floor && !Walk(nb)) blockedDoor++;
                    }
            }
            // Every furnished tile next to a walkable one (nothing stranded behind other furniture)
            int stranded = 0;
            for (int i = 0; i < tiles.Length; i++)
            {
                Tile t = tiles[i];
                if (t.Kind != TileKind.Floor || t.Variant == 0) continue;
                int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
                bool touch = false;
                foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) }) touch |= reach.Contains((x + dx, z + dz));
                if (!touch) stranded++;
            }
            // Kitty's places are all floor
            int badSpots = 0;
            foreach (var (sx, sz, kind) in layout.L974Spots(mx, mz))
            {
                Tile s = T(sx, sz);
                if (kind == WorldLayout.L974SpotKind.Table ? s.Variant != Props.L974Table : !Walk(s)) badSpots++;
            }
            if (rooms.Count != 7 || unreached > 0 || blockedDoor > 0 || badSpots > 0)
            {
                bad++;
                Console.WriteLine($"  house {mx},{mz}: rooms {rooms.Count}/7, unreached {unreached}, blocked doorways {blockedDoor}, Kitty's spots not floor {badSpots}");
            }
            if (houses == 1) Console.WriteLine($"  a house: {floor} floor tiles in 7 rooms, {walkable} walkable, {stranded} furnished tiles out of reach");

            if (drawn < 2 && (drawn == 0 || layout.L974Mirrored(mx, mz) != layout.L974Mirrored(seen.First().Item1, seen.First().Item2)))
            {
                drawn++;
                Console.WriteLine($"  house {mx},{mz}{(layout.L974Mirrored(mx, mz) ? " (mirrored)" : "")}:");
                var (x0, z0) = WorldLayout.L974HouseCorner(mx, mz);
                for (int z = z0; z < z0 + WorldLayout.L974HouseD; z++)
                {
                    var sb = new System.Text.StringBuilder("    ");
                    for (int x = x0; x < x0 + WorldLayout.L974HouseW; x++) sb.Append(Glyph(T(x, z)));
                    Console.WriteLine(sb);
                }
            }

            // Kitty's wake-up from this house: somewhere safe, and the same place every time
            var (hx, hz) = layout.L974At(mx, mz, 9, 8);
            Passage wake = net.KittyWake((hx, hz));
            Link? first = net.Take(wake, null), again = net.Take(net.KittyWake((hx, hz)), null);
            if (first is not { } w) { wakeNone++; continue; }
            if (again is not { } w2 || w2.X != w.X || w2.Z != w.Z) wakeUnstable++;
            int lv = layout.LevelAt(WorldLayout.MacroOf((int)w.X), WorldLayout.MacroOf((int)w.Z));
            wakeTo[lv] = wakeTo.GetValueOrDefault(lv) + 1;
            if (!layout.IsSanctuary((int)w.X, (int)w.Z, lv) && lv != 4) Console.WriteLine($"  house {mx},{mz}: wakes in Level {WorldLayout.DisplayNumber(lv)} outside a sanctuary at {w.X:0},{w.Z:0}");
        }
        Console.WriteLine($"Level 974: {houses} houses ({mirrored} mirrored), {arrivals} with their arrival, {bad} with a fault");
        Console.WriteLine($"  Kitty's wake-up: " + string.Join(", ", wakeTo.Select(p => $"Level {WorldLayout.DisplayNumber(p.Key)} {p.Value}")) + $"; none found {wakeNone}, not the same twice {wakeUnstable}");
        var a = layout.FindArrival(WorldLayout.Level974, 99991UL);
        Console.WriteLine(a is { } p0 ? $"  /backrooms goto 974 lands at {p0.X},{p0.Z} (tile {(layout.TileAt(p0.X, p0.Z).Under == Unders.L974Arrival ? "the arrival" : "WRONG")})" : "  /backrooms goto 974 finds nowhere");
        return true;
    }

    static char Glyph(Tile t)
    {
        if (t.Kind == TileKind.Doorway) return t.Stack == 1 ? 'A' : 'D';
        if (t.Kind == TileKind.Wall) return t.Pattern switch
        {
            WallPattern.L974Window => 'W',
            WallPattern.L974BathTile => '%',
            WallPattern.L974Backsplash => '=',
            WallPattern.L974Wall => ' ',
            _ => '#',
        };
        if (t.Under == Unders.L974Arrival) return '@';
        return t.Variant switch
        {
            Props.L974Bed => 'B', Props.L974Nightstand => 'n', Props.L974PlushHeap => 'p', Props.L974Desk => t.Stack == 1 ? 'k' : 'd',
            Props.L974Chair => 'h', Props.L974Dresser => 'r', Props.L974Rug => 'R', Props.L974Fridge => 'F', Props.L974Pantry => 'P',
            Props.L974Counter => t.Stack == 2 ? 's' : 'c', Props.L974Stove => 'S', Props.L974Banquette => 'b', Props.L974Table => 'T',
            Props.L974Toilet => 'w', Props.L974Basin => 'i', Props.L974Bathtub => 't', Props.L974CatBed => 'm',
            _ => t.Overhead == Overheads.L974ClosetRod ? 'o' : t.Ceiling == CeilingKind.LightOn ? '+' : '.',
        };
    }

    /// <summary>For the links mode: the label of one of the level's thresholds walked into on this tile (e.g. "pit"), or null.</summary>
    static string L974LinkLabel(Tile t) => null;

    /// <summary>For the links mode: the threshold kind of one of the level's blocks used on this tile (its BlockBehaviorThreshold kind), or null.</summary>
    static string L974UseKind(Tile t) => null;
}
