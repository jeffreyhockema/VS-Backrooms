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
    /// runs them). Arrivals: 60, all in a hall or a lobby, none sealed.
    /// </summary>
    static bool L31Modes(WorldLayout layout, string mode, string[] args)
    {
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
        int complexes = 0;
        for (int wz = wcz - n; wz <= wcz + n; wz++)
            for (int wx = wcx - n; wx <= wcx + n; wx++)
            {
                int ax = wx * P + 6, az = wz * P + 6, bx = wx * P + P, bz = wz * P + P;
                if (!(Mine(ax, az) && Mine(bx, bz) && Mine(ax, bz) && Mine(bx, az))) continue;
                var plan = layout.L31PlanOf(wx, wz);
                complexes++;
                string k = plan.Kind == WorldLayout.L31Kind.Empty ? "Empty" : plan.Tiny ? "TinyRink" : "Rink";
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
            }
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
            if (t.Level != WorldLayout.Level31 || t.Sealed || t.Variant != 0 || t.Zone is not ((byte)Zone.Hall or (byte)Zone.Crossing or (byte)Zone.Lobby)) wrong++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} outside a hall or a lobby");
        if (arrivals < 60 || wrong > 0) Bad("arrivals");
        Console.WriteLine(bad == 0 ? "31stats: OK" : $"31stats: {bad} problem(s)");
        return true;
    }

    static string L31LinkLabel(Tile t) => null;

    static string L31UseKind(Tile t) => null;
}
