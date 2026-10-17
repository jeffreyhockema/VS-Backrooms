using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L52Zone;

/// <summary>Level 52's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 52stats [wings] [rim]: over a square of (2 x wings + 1) wings each way round the region's centre (or, with "rim",
    /// round a point on its east rim): the share of each kind of wing, the rooms (kinds, lit, doors each), the tiles of
    /// each zone, and whether every room, and every walkable tile, can be walked to from the main halls (after the
    /// shared SealPockets and ClearDoorways passes, as BuildMacro runs them). Arrivals: 60, all in a hall.
    /// </summary>
    static bool L52Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode != "52stats") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int wn) ? wn : 3;
        bool rim = args.Length > 4 && args[4] == "rim";
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }

        int cx = layout.L52CentreX * WorldLayout.MacroSize + 16, cz = layout.L52CentreZ * WorldLayout.MacroSize + 16;
        if (rim) cx += (layout.L52Radius - 2) * WorldLayout.MacroSize;
        int wcx = Hashing.FloorDiv(cx, WorldLayout.L52Period), wcz = Hashing.FloorDiv(cz, WorldLayout.L52Period);
        Console.WriteLine($"region centre cells {layout.L52CentreX},{layout.L52CentreZ}, radius {layout.L52Radius}; window {2 * n + 1}x{2 * n + 1} wings round wing {wcx},{wcz}{(rim ? " (east rim)" : "")}");
        int x0 = (wcx - n) * WorldLayout.L52Period, x1 = (wcx + n + 1) * WorldLayout.L52Period + 8; // and the hall past the last wing
        int z0 = (wcz - n) * WorldLayout.L52Period, z1 = (wcz + n + 1) * WorldLayout.L52Period + 8;

        var cells = new Dictionary<(int, int), Tile[]>();
        Tile T(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            if (!cells.TryGetValue((mx, mz), out var tiles)) cells[(mx, mz)] = tiles = layout.BuildMacro(mx, mz);
            return tiles[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
        }
        bool Mine(int x, int z) => T(x, z).Level == WorldLayout.Level52;
        bool Walk(Tile t) => t.Level == WorldLayout.Level52 && (t.Kind is TileKind.Doorway
            || t.Kind == TileKind.Floor && !(t.Stack > 0 && t.Variant == 0) && WorldLayout.IsWalkThroughProp(t.Variant));

        // Wings
        var kinds = new SortedDictionary<string, int>();
        int wings = 0;
        for (int wz = wcz - n; wz <= wcz + n; wz++)
            for (int wx = wcx - n; wx <= wcx + n; wx++)
            {
                var plan = layout.L52PlanOf(wx, wz);
                bool whole = Mine(wx * 96 + 8, wz * 96 + 8) && Mine(wx * 96 + 96, wz * 96 + 96) && Mine(wx * 96 + 8, wz * 96 + 96) && Mine(wx * 96 + 96, wz * 96 + 8);
                if (!whole) continue;
                wings++;
                string k = plan.Kind.ToString();
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
            }
        Console.WriteLine($"wings wholly inside: {wings}: " + string.Join(", ", kinds.Select(p => $"{p.Key} {p.Value} ({100.0 * p.Value / Math.Max(1, wings):0}%)")));

        // Walk from every main-hall tile
        var reached = new HashSet<(int, int)>();
        var queue = new Queue<(int, int)>();
        int walkable = 0, sealedTiles = 0;
        var zones = new int[16];
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
            {
                Tile t = T(x, z);
                if (t.Level != WorldLayout.Level52) continue;
                zones[Math.Min((int)t.Zone, 15)]++;
                if (!Walk(t)) continue;
                walkable++;
                if (t.Sealed) sealedTiles++;
                if (t.Zone is (byte)Zone.Hall or (byte)Zone.Hub && reached.Add((x, z))) queue.Enqueue((x, z));
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
        Console.WriteLine("zones (tiles): " + string.Join(", ", Enum.GetValues<Zone>().Select(zn => $"{zn} {zones[(int)zn]}")));
        int unreached = walkable - reached.Count;
        Console.WriteLine($"walkable tiles {walkable}, reached from the halls {reached.Count}, unreached {unreached} ({100.0 * unreached / Math.Max(1, walkable):0.00}%), sealed {sealedTiles}");

        // Rooms: kinds, doors, lit, reachable
        var roomKinds = new SortedDictionary<string, int>();
        var doors = new SortedDictionary<int, int>();
        int rooms = 0, lit = 0, cutOff = 0, clipped = 0, boards = 0, desks = 0;
        for (int wz = wcz - n; wz <= wcz + n; wz++)
            for (int wx = wcx - n; wx <= wcx + n; wx++)
            {
                var plan = layout.L52PlanOf(wx, wz);
                foreach (var room in plan.Rooms)
                {
                    var (ax, az) = plan.World(room.P0, room.Q0);
                    var (bx, bz) = plan.World(room.P1, room.Q1);
                    int rx0 = Math.Min(ax, bx), rx1 = Math.Max(ax, bx), rz0 = Math.Min(az, bz), rz1 = Math.Max(az, bz);
                    bool whole = true, any = false;
                    for (int z = rz0 - 1; z <= rz1 + 1 && whole; z++)
                        for (int x = rx0 - 1; x <= rx1 + 1 && whole; x++)
                            if (!Mine(x, z)) whole = false;
                    if (!whole) { clipped++; continue; }
                    rooms++;
                    string k = room.Kind.ToString();
                    roomKinds[k] = roomKinds.GetValueOrDefault(k) + 1;
                    if (room.Lit && room.Kind <= WorldLayout.L52RoomKind.Store) lit++;
                    doors[room.Doors] = doors.GetValueOrDefault(room.Doors) + 1;
                    for (int z = rz0; z <= rz1; z++)
                        for (int x = rx0; x <= rx1; x++)
                        {
                            Tile t = T(x, z);
                            if (t.Variant == Props.L52Chalkboard) boards++;
                            if (t.Variant == Props.L52Desk) desks++;
                            if (reached.Contains((x, z))) any = true;
                        }
                    if (!any)
                    {
                        cutOff++;
                        if (cutOff <= 5) Console.WriteLine($"  cut off: {room.Kind} at {rx0},{rz0}..{rx1},{rz1} (wing {wx},{wz})");
                    }
                }
            }
        Console.WriteLine($"rooms wholly inside: {rooms} (clipped by the rim: {clipped}): " + string.Join(", ", roomKinds.Select(p => $"{p.Key} {p.Value}")));
        Console.WriteLine($"  classrooms/stores lit: {lit}; doors per room: " + string.Join(", ", doors.Select(p => $"{p.Key}: {p.Value}")));
        Console.WriteLine($"  chalkboard pieces {boards}, desks {desks}; rooms not reached from the halls: {cutOff}");
        if (cutOff > 0) Bad("rooms not reached from the halls");
        if (unreached > walkable / 100) Bad("more than 1% of walkable tiles unreached");

        // Arrivals
        int arrivals = 0, wrong = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level52, key * 7919UL) is not { } a) continue;
            arrivals++;
            Tile t = layout.TileAt(a.X, a.Z);
            if (t.Level != WorldLayout.Level52 || t.Zone is not ((byte)Zone.Hall or (byte)Zone.Hub)) wrong++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} outside a main hall");
        if (arrivals < 60 || wrong > 0) Bad("arrivals");
        Console.WriteLine(bad == 0 ? "52stats: OK" : $"52stats: {bad} problem(s)");
        return true;
    }

    static string L52LinkLabel(Tile t) => null;

    static string L52UseKind(Tile t) => null;
}
