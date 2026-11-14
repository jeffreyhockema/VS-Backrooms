using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L31Zone;

/// <summary>Level 31's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 31stats [complexes] [rim]: over a square of (2 x complexes + 1) complexes each way round the region's centre (or,
    /// with "rim", round a point on its west rim): how many complexes there are of each kind (rinks, tiny rinks,
    /// emptinesses), the rooms of each kind, the share of tiles in each zone, and whether every room, and every walkable
    /// tile, can be walked to from the neon halls (after the shared SealPockets and ClearDoorways passes, as BuildMacro
    /// runs them). Arrivals: 60, all in a hall, a lobby or on a rink's carpet, none sealed.
    /// </summary>
    static bool L31Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "31links") return L31Links(layout, args);
        if (mode == "31peek") return L31Peek(layout, args);
        if (mode != "31stats") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int wn) ? wn : 2;
        bool rim = args.Length > 4 && args[4] == "rim";
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        const int P = WorldLayout.L31Period;

        int cx = layout.L31CentreX * WorldLayout.MacroSize + 16, cz = layout.L31CentreZ * WorldLayout.MacroSize + 16;
        if (rim) cx -= (layout.L31Radius - 2) * WorldLayout.MacroSize;
        int wcx = Hashing.FloorDiv(cx, P), wcz = Hashing.FloorDiv(cz, P);
        Console.WriteLine($"region centre cells {layout.L31CentreX},{layout.L31CentreZ}, radius {layout.L31Radius}; window {2 * n + 1}x{2 * n + 1} complexes round {wcx},{wcz}{(rim ? " (west rim)" : "")}");
        int x0 = (wcx - n) * P, x1 = (wcx + n + 1) * P + 6; // and the hall past the last complex
        int z0 = (wcz - n) * P, z1 = (wcz + n + 1) * P + 6;

        var cells = new Dictionary<(int, int), Tile[]>();
        Tile T(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            if (!cells.TryGetValue((mx, mz), out var tiles)) cells[(mx, mz)] = tiles = layout.BuildMacro(mx, mz);
            return tiles[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
        }
        bool Mine(int x, int z) => T(x, z).Level == WorldLayout.Level31;
        bool Walk(Tile t) => t.Level == WorldLayout.Level31 && (t.Kind is TileKind.Doorway
            || t.Kind == TileKind.Floor && !(t.Stack > 0 && t.Variant == 0) && WorldLayout.IsWalkThroughProp(t.Variant));

        // Complexes
        var kinds = new SortedDictionary<string, int>();
        int complexes = 0, storeRooms = 0, backRooms = 0;
        for (int wz = wcz - n; wz <= wcz + n; wz++)
            for (int wx = wcx - n; wx <= wcx + n; wx++)
            {
                int ax = wx * P + 6, az = wz * P + 6, bx = wx * P + P, bz = wz * P + P;
                if (!(Mine(ax, az) && Mine(bx, bz) && Mine(ax, bz) && Mine(bx, az))) continue;
                var plan = layout.L31PlanOf(wx, wz);
                complexes++;
                string k = plan.Kind == WorldLayout.L31Kind.Empty ? "Empty" : plan.Tiny ? "TinyRink" : "Rink";
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
                foreach (var room in plan.Rooms.Where(r => r.Kind == Zone.Store))
                {
                    storeRooms++;
                    bool covered = false;
                    for (int q = room.Q0; q <= room.Q1 && !covered; q++)
                        for (int p = room.P0; p <= room.P1; p++)
                            if (plan.At(p, q).Variant == WorldLayout.L31Props.Covered) { covered = true; break; }
                    if (covered) { backRooms++; }
                }
            }
        Console.WriteLine($"store rooms {storeRooms}, back arcades (covered machines) {backRooms} ({100.0 * backRooms / Math.Max(1, storeRooms):0}% of store rooms, {(double)backRooms / Math.Max(1, complexes):0.00} a complex)");
        Console.WriteLine($"complexes wholly inside: {complexes}: " + string.Join(", ", kinds.Select(p => $"{p.Key} {p.Value} ({100.0 * p.Value / Math.Max(1, complexes):0}%)")));

        // Walk from every hall tile
        var reached = new HashSet<(int, int)>();
        var queue = new Queue<(int, int)>();
        int walkable = 0, sealedTiles = 0, mine = 0;
        var zones = new int[32];
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
            {
                Tile t = T(x, z);
                if (t.Level != WorldLayout.Level31) continue;
                mine++;
                zones[Math.Min((int)t.Zone, 31)]++;
                if (!Walk(t)) continue;
                walkable++;
                if (t.Sealed) sealedTiles++;
                if (t.Zone is (byte)Zone.Hall or (byte)Zone.Crossing && reached.Add((x, z))) queue.Enqueue((x, z));
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
        Console.WriteLine("zones (share of the level's tiles): " + string.Join(", ", Enum.GetValues<Zone>().Where(zn => zones[(int)zn] > 0)
            .Select(zn => $"{zn} {100.0 * zones[(int)zn] / Math.Max(1, mine):0.0}%")));
        int unreached = walkable - reached.Count;
        Console.WriteLine($"walkable tiles {walkable}, reached from the halls {reached.Count}, unreached {unreached} ({100.0 * unreached / Math.Max(1, walkable):0.00}%), sealed {sealedTiles}");
        int shown = 0;
        for (int z = z0; z <= z1 && shown < 5; z++)
            for (int x = x0; x <= x1 && shown < 5; x++)
            {
                Tile t = T(x, z);
                if (t.Level != WorldLayout.Level31 || !Walk(t) || reached.Contains((x, z))) continue;
                Console.WriteLine($"  unreached: {x},{z} ({(Zone)t.Zone})");
                shown++;
            }

        // Rooms: kinds, reachable
        var roomKinds = new SortedDictionary<string, int>();
        int rooms = 0, cutOff = 0, clipped = 0, cabinets = 0, balls = 0;
        for (int wz = wcz - n; wz <= wcz + n; wz++)
            for (int wx = wcx - n; wx <= wcx + n; wx++)
            {
                var plan = layout.L31PlanOf(wx, wz);
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
                    for (int z = rz0; z <= rz1; z++)
                        for (int x = rx0; x <= rx1; x++)
                        {
                            Tile t = T(x, z);
                            if (t.Variant is WorldLayout.L31Props.Cabinet or WorldLayout.L31Props.RetroCabinet) cabinets++;
                            if (t.Overhead == WorldLayout.L31Overhead.Star) balls++;
                            if (reached.Contains((x, z))) any = true;
                        }
                    if (!any)
                    {
                        cutOff++;
                        if (cutOff <= 5) Console.WriteLine($"  cut off: {room.Kind} at {rx0},{rz0}..{rx1},{rz1} (complex {wx},{wz})");
                    }
                }
            }
        Console.WriteLine($"rooms wholly inside: {rooms} (clipped by the rim: {clipped}): " + string.Join(", ", roomKinds.Select(p => $"{p.Key} {p.Value}")));
        Console.WriteLine($"  arcade cabinets {cabinets}, star lights {balls}; rooms not reached from the halls: {cutOff}");
        if (cutOff > 0) Bad("rooms not reached from the halls");
        if (unreached > walkable / 100) Bad("more than 1% of walkable tiles unreached");

        // Arrivals
        int arrivals = 0, wrong = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level31, key * 7919UL) is not { } a) continue;
            arrivals++;
            Tile t = layout.TileAt(a.X, a.Z);
            if (t.Level != WorldLayout.Level31 || t.Sealed || t.Variant != 0 || t.Zone is not ((byte)Zone.Hall or (byte)Zone.Crossing or (byte)Zone.Lobby or (byte)Zone.Skirt)) wrong++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} outside a hall, a lobby or a rink's carpet");
        if (arrivals < 60 || wrong > 0) Bad("arrivals");
        Console.WriteLine(bad == 0 ? "31stats: OK" : $"31stats: {bad} problem(s)");
        return true;
    }

    static string L31LinkLabel(Tile t) => null;

    static string L31UseKind(Tile t) =>
        t.Under is Unders.L31HostDoor or Unders.L31LobbyDoor ? "l31-door" : t.Under == Unders.L31Revolving && t.Stack == 1 ? "l31-revolving" : null;

    /// <summary>
    /// 31links [cells]: the level's ways in and out for the lead to check their rarity and find them. For each host (Levels 2, 3
    /// and 6), scanning out from spawn ring by ring to [cells] (default 1600): the host's area (sampled), how many cells roll a
    /// wooden door and how many hold one, doors per square kilometre and the mean spacing, and the nearest few to spawn
    /// (position, distance). In the level: the complexes, lobbies with a wooden door, revolving doors (and where each leads), the
    /// nearest few revolving doors to the region's centre.
    /// </summary>
    static bool L31Links(WorldLayout layout, string[] args)
    {
        int reach = args.Length > 3 && int.TryParse(args[3], out int r0) ? r0 : 1600;
        int linkBad = 0;
        void LinkBad(string what) { linkBad++; Console.WriteLine("  BAD: " + what); }
        var (sx, sz) = layout.FindSpawn();
        int smx = WorldLayout.MacroOf(sx), smz = WorldLayout.MacroOf(sz);
        int[] hosts = { 2, 3, 6 };
        var sampled = new Dictionary<int, long>();
        var rolled = new Dictionary<int, int>();
        var doors = new Dictionary<int, List<(int X, int Z, string Facing, double D)>>();
        foreach (int h in hosts) { sampled[h] = 0; rolled[h] = 0; doors[h] = new(); }
        for (int dz = -reach; dz <= reach; dz++)
            for (int dx = -reach; dx <= reach; dx++)
            {
                int mx = smx + dx, mz = smz + dz;
                bool sample = (dx & 3) == 0 && (dz & 3) == 0;
                bool any = false;
                foreach (int h in hosts) any |= layout.L31HostDoorCell(h, mx, mz);
                if (!sample && !any) continue;
                int level = layout.LevelAt(mx, mz);
                if (level is not (2 or 3 or 6)) continue;
                if (sample) sampled[level]++;
                if (!layout.L31HostDoorCell(level, mx, mz)) continue;
                rolled[level]++;
                Tile[] tiles = layout.BuildMacro(mx, mz);
                for (int i = 0; i < tiles.Length; i++)
                    if (tiles[i].Under == Unders.L31HostDoor)
                    {
                        int x = mx * WorldLayout.MacroSize + i % WorldLayout.MacroSize, z = mz * WorldLayout.MacroSize + i / WorldLayout.MacroSize;
                        doors[level].Add((x, z, tiles[i].Pier.ToString(), Math.Sqrt((double)(x - sx) * (x - sx) + (double)(z - sz) * (z - sz))));
                    }
            }
        Console.WriteLine($"Level 31's ways in: spawn {sx},{sz}; scanned {2 * reach + 1} cells square round it");
        foreach (int h in hosts)
        {
            double km2 = sampled[h] * 16.0 * WorldLayout.MacroSize * WorldLayout.MacroSize / 1e6;
            int n = doors[h].Count;
            Console.WriteLine($"  Level {h}: about {sampled[h] * 16} cells ({km2:0.0} km2); {rolled[h]} cells rolled a door, {n} hold one; "
                + $"{(km2 > 0 ? n / km2 : 0):0.00} per km2, one per {(n > 0 ? Math.Sqrt(km2 * 1e6 / n) : 0):0} blocks square");
            foreach (var d in doors[h].OrderBy(d => d.D).Take(5))
                Console.WriteLine($"    wooden door at {d.X},{d.Z} facing {d.Facing}, {d.D:0} blocks from spawn");
        }

        // In the level: every complex wholly inside the region
        int cx = layout.L31CentreX * WorldLayout.MacroSize + 16, cz = layout.L31CentreZ * WorldLayout.MacroSize + 16;
        int radius = layout.L31Radius * WorldLayout.MacroSize, wn = radius / WorldLayout.L31Period + 1;
        int wcx = Hashing.FloorDiv(cx, WorldLayout.L31Period), wcz = Hashing.FloorDiv(cz, WorldLayout.L31Period);
        int lobbies = 0, complexes = 0;
        var revolving = new List<(int X, int Z, int To, double D)>();
        var to = new Dictionary<int, int> { [9] = 0, [10] = 0, [11] = 0 };
        for (int wz = wcz - wn; wz <= wcz + wn; wz++)
            for (int wx = wcx - wn; wx <= wcx + wn; wx++)
            {
                var (ax, az) = (wx * WorldLayout.L31Period + 66, wz * WorldLayout.L31Period + 66);
                if (layout.LevelAt(WorldLayout.MacroOf(ax), WorldLayout.MacroOf(az)) != WorldLayout.Level31) continue;
                complexes++;
                var plan = layout.L31PlanOf(wx, wz);
                if (plan.Kind == WorldLayout.L31Kind.Rinks)
                {
                    var (lx, lz) = plan.World(WorldLayout.L31LobbyDoorP, WorldLayout.L31LobbyDoorQ);
                    if (WorldLayout.IsL31LobbyDoor(layout.TileAt(lx, lz))) lobbies++;
                }
                if (layout.L31RevolvingOf(wx, wz) is not { } d) continue;
                Tile t = layout.TileAt(d.X, d.Z);
                if (!WorldLayout.IsL31Revolving(t) || t.Stack != 1) { LinkBad($"revolving door at {d.X},{d.Z} not laid"); continue; }
                int target = layout.L31RevolvingTarget(d.X, d.Z);
                to[target]++;
                revolving.Add((d.X, d.Z, target, Math.Sqrt((double)(d.X - cx) * (d.X - cx) + (double)(d.Z - cz) * (d.Z - cz))));
            }
        double area = Math.PI * radius * radius / 1e6;
        Console.WriteLine($"Level 31: {complexes} complexes, {lobbies} lobbies with a wooden door; {revolving.Count} revolving doors "
            + $"({revolving.Count / area:0.0} per km2; to Level 9: {to[9]}, 10: {to[10]}, 11: {to[11]})");
        foreach (var d in revolving.OrderBy(d => d.D).Take(5))
            Console.WriteLine($"    revolving door at {d.X},{d.Z} to Level {d.To}, {d.D:0} blocks from the region's centre");

        // Through the doors, in the threshold network as the game has it
        var net = new Backrooms.Thresholds.ThresholdNetwork(layout, new WorldGeometry(256), long.Parse(args[0]));
        foreach (int h in hosts)
        {
            if (doors[h].Count == 0) { LinkBad($"no wooden door in Level {h} within {reach} cells"); continue; }
            foreach (var d in doors[h].OrderBy(d => d.D).Take(2))
            {
                Backrooms.Thresholds.Passage p = net.Used(d.X, d.Z, "l31-door", out string refusal);
                if (p == null) { LinkBad($"wooden door at {d.X},{d.Z} in Level {h} leads nowhere ({refusal})"); continue; }
                var home = new Backrooms.Thresholds.Link(d.X + 0.5, 1000, d.Z + 0.5, false);
                if (net.Take(p, home) is not { } land) { LinkBad($"wooden door at {d.X},{d.Z}: no arrival"); continue; }
                int ax = (int)Math.Floor(land.X), az = (int)Math.Floor(land.Z);
                Tile at = layout.TileAt(ax, az);
                string line = $"  Level {h} wooden door {d.X},{d.Z} -> L{at.Level} {ax} {az}";
                if (at.Level != WorldLayout.Level31) { LinkBad(line + ": not in Level 31"); continue; }
                if (at.Kind != TileKind.Floor) { LinkBad(line + $": the arrival tile is {at.Kind}, not floor"); continue; }
                if (layout.FeatureBeside(ax, az, WorldLayout.IsL31LobbyDoor) is not { } bd) { LinkBad(line + ": no lobby door beside the arrival"); continue; }
                Backrooms.Thresholds.Passage q = net.Used(bd.X, bd.Z, "l31-door", out _);
                var again = q == null ? (Backrooms.Thresholds.Link?)null : net.Take(q, null);
                if (again != home) { LinkBad(line + $": the lobby door {bd.X},{bd.Z} does not lead back"); continue; }
                if (net.Take(p, home) != land) { LinkBad(line + ": not the same place again"); continue; }
                Console.WriteLine(line + $", back through {bd.X},{bd.Z}");
            }
        }
        var tried = new Dictionary<int, int> { [9] = 0, [10] = 0, [11] = 0 };
        foreach (var d in revolving.OrderBy(d => d.D))
        {
            if (tried[d.To] >= 2) continue;
            tried[d.To]++;
            Backrooms.Thresholds.Passage p = net.Used(d.X, d.Z, "l31-revolving", out string refusal);
            if (p == null) { LinkBad($"revolving door at {d.X},{d.Z} leads nowhere ({refusal})"); continue; }
            if (p.TwoWay) LinkBad($"revolving door at {d.X},{d.Z} is two-way");
            if (net.Take(p, null) is not { } land) { LinkBad($"revolving door at {d.X},{d.Z}: no arrival"); continue; }
            int ax = (int)Math.Floor(land.X), az = (int)Math.Floor(land.Z);
            Tile at = layout.TileAt(ax, az);
            string line = $"  revolving door {d.X},{d.Z} -> L{at.Level} {ax} {az}";
            if (at.Level != d.To) LinkBad(line + $": not in Level {d.To}");
            else if (at.Kind != TileKind.Floor) LinkBad(line + $": the arrival tile is {at.Kind}, not floor");
            else if (net.Take(p, null) != land) LinkBad(line + ": not the same place again");
            else Console.WriteLine(line);
        }
        foreach (int t in new[] { 9, 10, 11 })
            if (tried[t] == 0) LinkBad($"no revolving door to Level {t}");
        Console.WriteLine(linkBad == 0 ? "31links: OK" : $"31links: {linkBad} problem(s)");
        return true;
    }

    /// <summary>
    /// 31peek [dx dz] [p0 q0 p1 q1]: prints a complex's plan (the one dx, dz complexes from the region's centre's), in the
    /// plan's own (P, Q) terms: '#' wall, 'D' doorway, '.' floor, 'P' a prop, 'M' a wall mount on a floor tile, 'm' one on
    /// a doorway, 'B' a supply box, '~' flooded; with the zone of each room's first tile listed under it.
    /// </summary>
    static bool L31Peek(WorldLayout layout, string[] args)
    {
        int dx = args.Length > 3 ? int.Parse(args[3]) : 0, dz = args.Length > 4 ? int.Parse(args[4]) : 0;
        int p0 = args.Length > 8 ? int.Parse(args[5]) : -1, q0 = args.Length > 8 ? int.Parse(args[6]) : -1;
        int p1 = args.Length > 8 ? int.Parse(args[7]) : WorldLayout.L31Size, q1 = args.Length > 8 ? int.Parse(args[8]) : WorldLayout.L31Size;
        int cx = layout.L31CentreX * WorldLayout.MacroSize + 16, cz = layout.L31CentreZ * WorldLayout.MacroSize + 16;
        int wx = Hashing.FloorDiv(cx, WorldLayout.L31Period) + dx, wz = Hashing.FloorDiv(cz, WorldLayout.L31Period) + dz;
        var plan = layout.L31PlanOf(wx, wz);
        Console.WriteLine($"complex {wx},{wz}: {plan.Kind}, tiny {plan.Tiny}, mirror {plan.Mirror}");
        for (int q = q0; q <= q1; q++)
        {
            var line = new System.Text.StringBuilder();
            for (int p = p0; p <= p1; p++)
            {
                Tile t = plan.At(p, q);
                char c = t.Kind switch
                {
                    TileKind.Wall => t.Under != 0 ? 'U' : '#',
                    TileKind.Doorway => WorldLayout.L31HasMount(t) ? 'm' : 'D',
                    _ => t.SupplyBox ? 'B' : WorldLayout.L31HasMount(t) ? 'M' : t.Variant != 0 ? 'P' : '.',
                };
                line.Append(c);
            }
            Console.WriteLine($"{line}  q={q}");
        }
        foreach (var room in plan.Rooms) Console.WriteLine($"  {room.Kind} p {room.P0}-{room.P1} q {room.Q0}-{room.Q1} door {room.DoorP},{room.DoorQ} {room.DoorSide}");
        return true;
    }
}
