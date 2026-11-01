using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L15Zone;

/// <summary>Level 15's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 15stats [wings] [rim] [map]: over a square of (2 x wings + 1) wings each way round the region's centre (or, with "rim",
    /// round a point on its east rim): the rooms of each kind, machines, the dead, camps, supply boxes and lockers, the tiles
    /// of each zone and how many are dark, which wings hold the star door, and whether every room, and every walkable tile,
    /// can be walked to from the main halls (after the shared SealPockets and ClearDoorways passes, as BuildMacro runs them).
    /// Arrivals: 60, all in a lit hall or corridor. With "map", writes l15map.ppm: one pixel a block of the middle wing and
    /// the halls round it.
    /// </summary>
    static bool L15Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "15dump") return L15Dump(layout, args);
        if (mode == "15links") return L15Links(layout, args);
        if (mode == "15showcase")
        {
            // The showcase spots (as /backrooms showcase 15 lists them), with what is under each
            foreach (var s in layout.L15ShowcaseSpots(new WorldGeometry(256)))
            {
                Tile t = layout.TileAt((int)Math.Floor(s.X), (int)Math.Floor(s.Z));
                Console.WriteLine($"spot {s.Name} {s.X} {s.Y} {s.Z} h{s.Heading:0} p{s.Pitch:0} | {s.Setup}  [{WorldLayout.L15ZoneOf(t)}{(WorldLayout.L15IsDark(t) ? " dark" : "")} {t.Kind} v{t.Variant}]");
            }
            return true;
        }
        if (mode != "15stats") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int wn) ? wn : 2;
        bool rim = args.Contains("rim"), map = args.Contains("map");
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        const int P = WorldLayout.L15Period;

        int cx = layout.L15CentreX * WorldLayout.MacroSize + 16, cz = layout.L15CentreZ * WorldLayout.MacroSize + 16;
        if (rim) cx += (layout.L15Radius - 2) * WorldLayout.MacroSize;
        int hcx = Hashing.FloorDiv(cx, P), hcz = Hashing.FloorDiv(cz, P);
        Console.WriteLine($"region centre cells {layout.L15CentreX},{layout.L15CentreZ}, radius {layout.L15Radius}; window {2 * n + 1}x{2 * n + 1} wings round wing {hcx},{hcz}{(rim ? " (east rim)" : "")}");
        int x0 = (hcx - n) * P, x1 = (hcx + n + 1) * P + 6;
        int z0 = (hcz - n) * P, z1 = (hcz + n + 1) * P + 6;

        var cells = new Dictionary<(int, int), Tile[]>();
        Tile T(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            if (!cells.TryGetValue((mx, mz), out var tiles)) cells[(mx, mz)] = tiles = layout.BuildMacro(mx, mz);
            return tiles[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
        }
        bool Mine(int x, int z) => T(x, z).Level == WorldLayout.Level15;
        bool Walk(Tile t) => t.Level == WorldLayout.Level15 && (t.Kind is TileKind.Doorway
            || t.Kind == TileKind.Floor && !(t.Stack > 0 && t.Variant == 0) && !t.SupplyBox && WorldLayout.IsWalkThroughProp(t.Variant));

        // Walk from every main hall tile
        var reached = new HashSet<(int, int)>();
        var queue = new Queue<(int, int)>();
        int walkable = 0, sealedTiles = 0, darkTiles = 0, levelTiles = 0, lights = 0;
        var zones = new int[16];
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
            {
                Tile t = T(x, z);
                if (t.Level != WorldLayout.Level15) continue;
                levelTiles++;
                zones[(int)WorldLayout.L15ZoneOf(t) & 15]++;
                if (WorldLayout.L15IsDark(t) && darkTiles++ == 0) Console.WriteLine($"  first dark tile: block {x},{z} ({WorldLayout.L15ZoneOf(t)})");
                if (t.Kind == TileKind.Floor && t.Ceiling == CeilingKind.L15LightOn && !WorldLayout.L15IsDark(t)) lights++;
                if (!Walk(t)) continue;
                walkable++;
                if (t.Sealed) sealedTiles++;
                if (WorldLayout.L15ZoneOf(t) == Zone.Hall && reached.Add((x, z))) queue.Enqueue((x, z));
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

        // Wings: rooms by kind, and whether each room was reached from the halls
        var rooms = new SortedDictionary<string, int>();
        int unreachedShown = 0, wings = 0, clipped = 0, totalRooms = 0, machines = 0, corpses = 0, camps = 0, boxes = 0, lockers = 0, stars = 0, roomsCut = 0, worstWing = 0;
        for (int hz = hcz - n; hz <= hcz + n; hz++)
            for (int hx = hcx - n; hx <= hcx + n; hx++)
            {
                var plan = layout.L15PlanOf(hx, hz);
                int bx0 = hx * P + 6, bx1 = hx * P + P, bz0 = hz * P + 6, bz1 = hz * P + P;
                bool whole = Mine(bx0, bz0) && Mine(bx1, bz1) && Mine(bx0, bz1) && Mine(bx1, bz0);
                if (!whole) { clipped++; continue; }
                wings++;
                totalRooms += plan.Rooms;
                machines += plan.Machines;
                corpses += plan.Corpses;
                camps += plan.Camps;
                boxes += plan.Boxes;
                lockers += plan.Lockers;
                if (plan.Star) { stars++; Console.WriteLine($"  the star door: wing {hx},{hz}"); }
                // Each room (a connected run of one zone's floor): whether any of it was reached
                var seen = new HashSet<(int, int)>();
                int inside = 0, got = 0;
                for (int z = bz0 + 1; z < bz1; z++)
                    for (int x = bx0 + 1; x < bx1; x++)
                    {
                        Tile t = T(x, z);
                        var zone = WorldLayout.L15ZoneOf(t);
                        if (Walk(t))
                        {
                            inside++;
                            if (reached.Contains((x, z))) got++;
                            else if (!t.Sealed && unreachedShown++ < 3) Console.WriteLine($"  unreached, not sealed: {x},{z} ({zone})");
                        }
                        if (!WorldLayout.L15IsRoom(zone) || t.Kind != TileKind.Floor || seen.Contains((x, z))) continue;
                        var room = new Queue<(int, int)>();
                        room.Enqueue((x, z));
                        seen.Add((x, z));
                        bool any = false;
                        int size = 0;
                        while (room.Count > 0)
                        {
                            var (rx, rz) = room.Dequeue();
                            size++;
                            if (reached.Contains((rx, rz))) any = true;
                            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                            {
                                int nx = rx + dx, nz = rz + dz;
                                if (nx <= bx0 || nz <= bz0 || nx >= bx1 || nz >= bz1 || seen.Contains((nx, nz))) continue;
                                Tile nt = T(nx, nz);
                                if (nt.Kind != TileKind.Floor || WorldLayout.L15ZoneOf(nt) != zone) continue;
                                seen.Add((nx, nz));
                                room.Enqueue((nx, nz));
                            }
                        }
                        string k = zone.ToString();
                        if (!rooms.ContainsKey(k)) Console.WriteLine($"  first {k}: block {x},{z}");
                        rooms[k] = rooms.GetValueOrDefault(k) + 1;
                        if (!any && size > 4)
                        {
                            roomsCut++;
                            if (roomsCut <= 6) Console.WriteLine($"  cut off: {k} of {size} tiles at {x},{z}");
                        }
                    }
                worstWing = Math.Max(worstWing, inside - got);
            }
        int counted = rooms.Values.Sum();
        double per = Math.Max(1, wings);
        Console.WriteLine($"wings wholly inside: {wings} (clipped by the rim: {clipped}); rooms planned {totalRooms} ({totalRooms / per:0.0} a wing)");
        Console.WriteLine("  rooms walked: " + string.Join(", ", rooms.Select(p => $"{p.Key} {p.Value} ({100.0 * p.Value / Math.Max(1, counted):0}%)")));
        Console.WriteLine($"  a wing: machines {machines / per:0.0}, the dead {corpses / per:0.0}, camps {camps / per:0.0}, supply boxes {boxes / per:0.0}, lockers {lockers / per:0.0}; star doors {stars}");
        Console.WriteLine("zones (tiles): " + string.Join(", ", Enum.GetValues<Zone>().Select(zn => $"{zn} {zones[(int)zn]}")));
        Console.WriteLine($"dark: {100.0 * darkTiles / Math.Max(1, levelTiles):0.0}% of the level's tiles; lights giving light: one per {levelTiles / (double)Math.Max(1, lights):0} tiles");
        int unreached = walkable - reached.Count;
        Console.WriteLine($"walkable tiles {walkable}, reached from the halls {reached.Count}, unreached {unreached} ({100.0 * unreached / Math.Max(1, walkable):0.00}%), sealed {sealedTiles}; most unreached in one wing {worstWing}");
        Console.WriteLine($"rooms not reached from the halls: {roomsCut}");
        if (roomsCut > 0) Bad("rooms not reached from the halls");
        if (unreached > walkable / 100) Bad("more than 1% of walkable tiles unreached");

        // Arrivals
        int arrivals = 0, wrong = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level15, key * 7919UL) is not { } a) continue;
            arrivals++;
            Tile t = layout.TileAt(a.X, a.Z);
            if (t.Level != WorldLayout.Level15 || WorldLayout.L15IsDark(t) || WorldLayout.L15ZoneOf(t) is not (Zone.Hall or Zone.Corridor)) wrong++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} outside a lit hall or corridor");
        if (arrivals < 60 || wrong > 0) Bad("arrivals");

        if (map)
        {
            // The middle wing and the halls round it: walls black (glass blue), doors yellow, rooms by kind, props darker, the dark dimmed
            int mx0 = hcx * P - 8, mz0 = hcz * P - 8, size = P + 24;
            using var f = new StreamWriter("l15map.ppm");
            f.Write($"P3\n{size} {size}\n255\n");
            for (int z = mz0; z < mz0 + size; z++)
            {
                for (int x = mx0; x < mx0 + size; x++)
                {
                    Tile t = T(x, z);
                    var (r, g, b) = t.Level != WorldLayout.Level15 ? (60, 0, 0)
                        : t.Kind == TileKind.Wall ? (t.Detail is WorldLayout.L15WallGlass or WorldLayout.L15WallGlassCracked ? (80, 160, 200) : (0, 0, 0))
                        : t.Kind == TileKind.Doorway ? (255, 255, 0)
                        : WorldLayout.L15ZoneOf(t) switch
                        {
                            Zone.Hall => (230, 230, 230), Zone.Corridor => (190, 190, 200), Zone.Service => (120, 120, 120),
                            Zone.Machine => (90, 140, 220), Zone.Wreck => (150, 80, 40), Zone.Lab => (120, 220, 160), Zone.Storage => (200, 170, 110),
                            Zone.Dorm => (200, 120, 200), Zone.Kitchen => (240, 160, 120), Zone.Control => (80, 220, 220), Zone.Lecture => (220, 220, 120),
                            Zone.Blank => (250, 250, 250), Zone.Crematorium => (120, 40, 40), Zone.Star => (40, 40, 160), _ => (255, 0, 255),
                        };
                    if (t.Kind == TileKind.Floor && (t.Variant != 0 || t.SupplyBox || t.Stack > 0)) (r, g, b) = (r / 2, g / 2, b / 2);
                    if (WorldLayout.L15IsDark(t)) (r, g, b) = (r / 3, g / 3, b / 3);
                    f.Write($"{r} {g} {b} ");
                }
                f.Write("\n");
            }
            Console.WriteLine($"wrote l15map.ppm ({size} x {size}, from block {mx0},{mz0})");
        }
        Console.WriteLine(bad == 0 ? "15stats: OK" : $"15stats: {bad} problem(s)");
        return true;
    }

    /// <summary>15dump x z [r]: the tiles round a block position as letters (walls #, doors +, props by kind, walkable floor by zone), for looking into a problem.</summary>
    static bool L15Dump(WorldLayout layout, string[] args)
    {
        int x = int.Parse(args[3]), z = int.Parse(args[4]), r = args.Length > 5 ? int.Parse(args[5]) : 12;
        for (int dz = -r; dz <= r; dz++)
        {
            var line = new System.Text.StringBuilder();
            for (int dx = -r; dx <= r; dx++)
            {
                Tile t = layout.TileAt(x + dx, z + dz);
                char c = t.Level != WorldLayout.Level15 ? '~' : t.Kind == TileKind.Wall ? '#' : t.Kind == TileKind.Doorway ? '+'
                    : t.SupplyBox ? 'B' : t.Variant == 0 && t.Stack > 0 ? 'C' : t.Variant != 0 && !WorldLayout.IsWalkThroughProp(t.Variant) ? (t.Variant >= 1300 ? (char)('a' + t.Variant - 1300) : 'P')
                    : t.Sealed ? 's' : "?HcvMWLSDKCTBXZw"[(int)WorldLayout.L15ZoneOf(t) & 15];
                line.Append(dx == 0 && dz == 0 ? '@' : c);
            }
            Console.WriteLine(line);
        }
        return true;
    }

    static string L15LinkLabel(Tile t) => t.Level != WorldLayout.Level15 ? null : t.Under switch
    {
        Unders.L15Gateway => "ESCAPE gateway (to 3)", Unders.L15Window => "street pane (to 11)", Unders.L15Stairs => "office stairs (to 4)", _ => null,
    };

    static string L15UseKind(Tile t) => t.Under switch
    {
        Unders.L15WallDoor10 when t.Level == 10 => "l15-walldoor",
        Unders.L15Door3 when t.Level == 3 => "l15-l3door",
        Unders.L15Sealed when t.Level == WorldLayout.Level15 => "l15-sealed",
        _ => null,
    };

    /// <summary>
    /// 15links: Level 15's ways in and out, for the seed and spawn given (SPAWN, default full size): the white walls in Level
    /// 10's fields and the doors in Level 3, how many to a square kilometre of their level and the nearest few to spawn; in
    /// Level 15 round its middle, the doors that do not open and the ways out of each kind, how many to a square kilometre and
    /// the nearest few to the middle (where people are put down).
    /// </summary>
    static bool L15Links(WorldLayout layout, string[] args)
    {
        int smx = int.TryParse(Environment.GetEnvironmentVariable("SPAWN"), out int sp) ? sp : 16000, smz = smx;
        int sx = smx * 32 + 16, sz = smz * 32 + 16;
        // A level's extent in cells (rays out from spawn) and how many cells of it there are
        (int X0, int Z0, int X1, int Z1, long Cells) Extent(int level)
        {
            int x0 = int.MaxValue, z0 = int.MaxValue, x1 = int.MinValue, z1 = int.MinValue;
            for (int a = 0; a < 144; a++)
            {
                double ang = a * Math.PI * 2 / 144;
                for (int r = 0; r < 12000; r += 4)
                {
                    int mx = smx + (int)Math.Round(Math.Cos(ang) * r), mz = smz + (int)Math.Round(Math.Sin(ang) * r);
                    if (layout.LevelAt(mx, mz) != level) continue;
                    x0 = Math.Min(x0, mx); z0 = Math.Min(z0, mz); x1 = Math.Max(x1, mx); z1 = Math.Max(z1, mz);
                }
            }
            x0 -= 8; z0 -= 8; x1 += 8; z1 += 8;
            long cells = 0;
            for (int mz = z0; mz <= z1; mz += 4)
                for (int mx = x0; mx <= x1; mx += 4)
                    if (layout.LevelAt(mx, mz) == level) cells += 16;
            return (x0, z0, x1, z1, cells);
        }
        double Km2(long cells) => cells * 1024.0 / 1e6;
        double Dist(int x, int z) => Math.Sqrt((double)(x - sx) * (x - sx) + (double)(z - sz) * (z - sz));

        // Level 10: the white walls
        var e10 = Extent(10);
        var walls = new List<(double D, WorldLayout.L15WallSite W)>();
        for (int j = Hashing.FloorDiv(e10.Z0 * 32, WorldLayout.L15WallLattice); j <= Hashing.FloorDiv(e10.Z1 * 32, WorldLayout.L15WallLattice); j++)
            for (int i = Hashing.FloorDiv(e10.X0 * 32, WorldLayout.L15WallLattice); i <= Hashing.FloorDiv(e10.X1 * 32, WorldLayout.L15WallLattice); i++)
            {
                var w = layout.L15WallAt(i, j);
                if (!w.Valid) continue;
                var (dx, dz) = w.DoorAt;
                walls.Add((Dist(dx, dz), w));
            }
        walls.Sort((a, b) => a.D.CompareTo(b.D));
        double a10 = Km2(e10.Cells);
        Console.WriteLine($"Level 10: {a10:0} km2; white walls {walls.Count}: one per {a10 / Math.Max(1, walls.Count):0.0} km2 (about {Math.Sqrt(a10 / Math.Max(1, walls.Count)) * 1000:0} m apart)");
        foreach (var (d, w) in walls.Take(5))
        {
            var (x, z) = w.DoorAt;
            Console.WriteLine($"  wall door {x},{z} facing {w.DoorFace}, {d / 1000:0.0} km from spawn; wall {(w.AlongX ? "along x" : "along z")} {w.From}..{w.To} at {w.Line}");
        }

        // Level 3: the doors
        var e3 = Extent(3);
        var doors = new List<(double D, int X, int Z)>();
        int hashed = 0;
        for (int mz = e3.Z0; mz <= e3.Z1; mz++)
            for (int mx = e3.X0; mx <= e3.X1; mx++)
            {
                if (!layout.L15Door3Cell(mx, mz)) continue;
                hashed++;
                Tile[] tiles = layout.BuildMacro(mx, mz);
                for (int k = 0; k < tiles.Length; k++)
                    if (tiles[k].Under == Unders.L15Door3)
                    {
                        int x = mx * 32 + k % 32, z = mz * 32 + k / 32;
                        doors.Add((Dist(x, z), x, z));
                    }
            }
        doors.Sort((a, b) => a.D.CompareTo(b.D));
        double a3 = Km2(e3.Cells);
        Console.WriteLine($"Level 3: {a3:0.0} km2; doors {doors.Count} (of {hashed} cells picked): one per {a3 / Math.Max(1, doors.Count):0.00} km2 (about {Math.Sqrt(a3 / Math.Max(1, doors.Count)) * 1000:0} m apart)");
        foreach (var (d, x, z) in doors.Take(5))
        {
            Tile t = layout.TileAt(x, z);
            Console.WriteLine($"  door {x},{z} facing {t.Pier}, {d / 1000:0.0} km from spawn");
        }

        // Level 15 round its middle
        const int P = WorldLayout.L15Period, rings = 14;
        int cx = layout.L15CentreX * 32 + 16, cz = layout.L15CentreZ * 32 + 16;
        int hcx = Hashing.FloorDiv(cx, P), hcz = Hashing.FloorDiv(cz, P);
        int wings = 0, sealedDoors = 0;
        var exits = new SortedDictionary<int, List<(double D, int X, int Z, int Hx, int Hz)>>();
        for (int hz = hcz - rings; hz <= hcz + rings; hz++)
            for (int hx = hcx - rings; hx <= hcx + rings; hx++)
            {
                var plan = layout.L15PlanOf(hx, hz);
                var (wx, wz) = plan.World(60, 60);
                if (layout.LevelAt(WorldLayout.MacroOf(wx), WorldLayout.MacroOf(wz)) != WorldLayout.Level15) continue;
                wings++;
                if (plan.HasSealed) sealedDoors++;
                if (plan.Exit == 0) continue;
                var (x, z) = plan.World(plan.ExitA, plan.ExitB);
                if (!exits.TryGetValue(plan.Exit, out var list)) exits[plan.Exit] = list = new();
                list.Add((Math.Sqrt((double)(x - cx) * (x - cx) + (double)(z - cz) * (z - cz)), x, z, hx, hz));
            }
        double a15 = wings * (double)P * P / 1e6;
        Console.WriteLine($"Level 15 (middle {2 * rings + 1} x {2 * rings + 1} wings, {wings} in the level, {a15:0.0} km2): doors that do not open {sealedDoors} ({100.0 * sealedDoors / Math.Max(1, wings):0}% of wings)");
        string[] names = { "", "ESCAPE panel and gateway (to 3)", "street pane (to 11)", "office stairs (to 4)" };
        foreach (var (kind, list) in exits)
        {
            list.Sort((a, b) => a.D.CompareTo(b.D));
            Console.WriteLine($"  {names[kind]}: {list.Count}, one per {a15 / list.Count:0.00} km2 ({list.Count * 100.0 / Math.Max(1, wings):0.0}% of wings)");
            foreach (var (d, x, z, hx, hz) in list.Take(4)) Console.WriteLine($"    {x},{z} (wing {hx},{hz}), {d:0} blocks from the middle");
        }
        int found = 0;
        for (ulong key = 1; key <= 40; key++) if (layout.L15SealedArrival(key * 7919UL) is { } a && layout.TileAt(a.X, a.Z).Level == WorldLayout.Level15) found++;
        Console.WriteLine($"  arrivals beside a door that does not open: {found}/40");
        // Through each: the nearest of every kind, gone through in the network (as the game does), where it puts you down
        var net = new Backrooms.Thresholds.ThresholdNetwork(layout, new WorldGeometry(256), long.Parse(args[0]));
        int tripsBad = 0;
        void Trip(string what, Backrooms.Thresholds.Passage p, int want, Func<Tile, bool> beside = null)
        {
            if (p == null) { tripsBad++; Console.WriteLine($"  trip {what}: no passage"); return; }
            var to = net.Take(p, null);
            if (to is not { } l) { tripsBad++; Console.WriteLine($"  trip {what}: nowhere"); return; }
            int ax = (int)Math.Floor(l.X), az = (int)Math.Floor(l.Z);
            Tile t = layout.TileAt(ax, az);
            bool near = beside == null;
            for (int dz = -1; dz <= 1 && !near; dz++)
                for (int dx = -1; dx <= 1 && !near; dx++)
                    if (Math.Abs(dx) + Math.Abs(dz) == 1 && beside(layout.TileAt(ax + dx, az + dz))) near = true;
            bool ok = t.Level == want && t.Kind == TileKind.Floor && near && !p.TwoWay && net.Take(p, null) == to;
            if (!ok) tripsBad++;
            Console.WriteLine($"  trip {what}: {(ok ? "ok" : "BAD")}, to level {WorldLayout.DisplayNumber(t.Level)} at {ax},{az} (h {l.Y:0.0}){(beside != null ? (near ? ", beside it" : ", NOT beside it") : "")}{(p.TwoWay ? ", TWO-WAY" : ", one way")}");
        }
        Func<Tile, bool> sealedDoor = t => t.Under == Unders.L15Sealed && t.Level == WorldLayout.Level15;
        if (walls.Count > 0) { var (x, z) = walls[0].W.DoorAt; Trip("white wall door", net.Used(x, z, "l15-walldoor", out _), WorldLayout.Level15, sealedDoor); }
        if (doors.Count > 0) Trip("Level 3 door", net.Used(doors[0].X, doors[0].Z, "l15-l3door", out _), WorldLayout.Level15, sealedDoor);
        {
            var plan0 = layout.L15PlanOf(hcx, hcz);
            for (int k = 0; k < 9 && !plan0.HasSealed; k++) plan0 = layout.L15PlanOf(hcx + k % 3 - 1, hcz + k / 3 - 1);
            var (x, z) = plan0.World(plan0.SealedA, plan0.SealedB);
            var p = net.Used(x, z, "l15-sealed", out string refusal);
            Console.WriteLine($"  door that does not open at {x},{z}: {(p == null && refusal == "locked" ? "locked, ok" : "BAD")}");
            if (p != null || refusal != "locked") tripsBad++;
        }
        foreach (var (kind, list) in exits)
        {
            var (_, x, z, hx, hz) = list[0];
            var plan = layout.L15PlanOf(hx, hz);
            double floor15 = 0;
            switch (kind)
            {
                case WorldLayout.L15ExitEscape:
                {
                    var (gx, gz) = plan.World(plan.GateA, plan.GateB);
                    var shut = net.Used(gx, gz, "l15-gatewayshut", out string refusal);
                    Console.WriteLine($"  gateway shut at {gx},{gz}: {(shut == null && refusal == "locked" ? "locked, ok" : "BAD")}");
                    Trip("ESCAPE gateway (walked in)", net.Walked(gx, gz, layout.TileAt(gx, gz), floor15 + 1.0), 3);
                    Trip("ESCAPE gateway (used)", net.Used(gx, gz, "l15-gateway", out _), 3);
                    break;
                }
                case WorldLayout.L15ExitWindow:
                    Trip("street pane (broken)", net.Used(x, z, "l15-window", out _), 11);
                    Trip("street pane (climbed)", net.Walked(x, z, layout.TileAt(x, z), 2.0), 11);
                    break;
                case WorldLayout.L15ExitStairs:
                {
                    Tile step = layout.TileAt(x, z);
                    var p = net.Walked(x, z, step, 1.0);
                    Console.WriteLine($"  office stairs at the top: {(p == null ? "nothing, ok" : "BAD (trips at the top)")}");
                    if (p != null) tripsBad++;
                    var (dx, dz) = (-(step.Pier == ArchPier.West ? -1 : step.Pier == ArchPier.East ? 1 : 0), -(step.Pier == ArchPier.North ? -1 : step.Pier == ArchPier.South ? 1 : 0));
                    int x4 = x + dx * 3, z4 = z + dz * 3;
                    Trip("office stairs (four steps down)", net.Walked(x4, z4, layout.TileAt(x4, z4), -2.0), 4);
                    break;
                }
            }
        }
        Console.WriteLine(tripsBad == 0 ? "15links: trips OK" : $"15links: {tripsBad} trip problem(s)");
        return true;
    }
}
