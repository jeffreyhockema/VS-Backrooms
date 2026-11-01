using Backrooms.Worldgen;
using Kind = Backrooms.Worldgen.WorldLayout.L120HallKind;
using Zone = Backrooms.Worldgen.WorldLayout.L120Zone;

/// <summary>Level 120's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 120stats [halls] [rim]: over a square of (2 x halls + 1) halls each way round the region's centre (or, with "rim",
    /// round a point on its east rim): the share of each kind of hall; for the clusters, the rooms (15-23 each), racks
    /// (standing, lit, wrecked), terminals, whole terminals (and where each boots into), supply boxes, and whether every
    /// cluster and every walkable tile of one can be walked to from the passages (after the shared SealPockets and
    /// ClearDoorways passes, as BuildMacro runs them); for the pockets (White Voids, Pitch-Black Hallways), that nothing of
    /// them is reached from the passages, that every open tile of one is reached from its arrival, and that it has windows.
    /// Arrivals: 60, all in a passage or a server room.
    /// </summary>
    static bool L120Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "120links") return L120LinksMode(layout, args);
        if (mode != "120stats") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int hn) ? hn : 3;
        bool rim = args.Length > 4 && args[4] == "rim";
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        const int P = WorldLayout.L120Period;

        int cx = layout.L120CentreX * WorldLayout.MacroSize + 16, cz = layout.L120CentreZ * WorldLayout.MacroSize + 16;
        if (rim) cx += (layout.L120Radius - 2) * WorldLayout.MacroSize;
        int hcx = Hashing.FloorDiv(cx, P), hcz = Hashing.FloorDiv(cz, P);
        Console.WriteLine($"region centre cells {layout.L120CentreX},{layout.L120CentreZ}, radius {layout.L120Radius}; window {2 * n + 1}x{2 * n + 1} halls round hall {hcx},{hcz}{(rim ? " (east rim)" : "")}");
        int x0 = (hcx - n) * P, x1 = (hcx + n + 1) * P + 5; // and the passage past the last hall
        int z0 = (hcz - n) * P, z1 = (hcz + n + 1) * P + 5;

        var cells = new Dictionary<(int, int), Tile[]>();
        Tile T(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            if (!cells.TryGetValue((mx, mz), out var tiles)) cells[(mx, mz)] = tiles = layout.BuildMacro(mx, mz);
            return tiles[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
        }
        bool Mine(int x, int z) => T(x, z).Level == WorldLayout.Level120;
        bool Walk(Tile t) => t.Level == WorldLayout.Level120 && (t.Kind is TileKind.Doorway
            || t.Kind == TileKind.Floor && !(t.Stack > 0 && t.Variant == 0) && !t.SupplyBox && WorldLayout.IsWalkThroughProp(t.Variant));
        HashSet<(int, int)> Flood(IEnumerable<(int, int)> from)
        {
            var reached = new HashSet<(int, int)>();
            var queue = new Queue<(int, int)>();
            foreach (var s in from) if (reached.Add(s)) queue.Enqueue(s);
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
            return reached;
        }

        // Walk from every passage tile
        var starts = new List<(int, int)>();
        int walkable = 0, sealedTiles = 0;
        var zones = new int[16];
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
            {
                Tile t = T(x, z);
                if (t.Level != WorldLayout.Level120) continue;
                zones[Math.Min((int)t.Zone, 15)]++;
                if (!Walk(t)) continue;
                walkable++;
                if (t.Sealed) sealedTiles++;
                if (t.Zone == (byte)Zone.Corridor && t.Kind == TileKind.Floor) starts.Add((x, z));
            }
        var fromPassages = Flood(starts);

        var kinds = new SortedDictionary<string, int>();
        int halls = 0, clipped = 0, cutOff = 0, worstHall = 0, minRooms = 99, maxRooms = 0, rooms = 0, racks = 0, lit = 0, wrecked = 0, terminals = 0, boots = 0, boxes = 0;
        int pockets = 0, pocketLeaks = 0, pocketHoles = 0, noWindow = 0, bootsNowhere = 0;
        var bootInto = new SortedDictionary<string, int>();
        int pocketTiles = 0;
        for (int hz = hcz - n; hz <= hcz + n; hz++)
            for (int hx = hcx - n; hx <= hcx + n; hx++)
            {
                var plan = layout.L120PlanOf(hx, hz);
                int bx0 = hx * P + 5, bx1 = hx * P + P, bz0 = hz * P + 5, bz1 = hz * P + P;
                bool whole = Mine(bx0, bz0) && Mine(bx1, bz1) && Mine(bx0, bz1) && Mine(bx1, bz0);
                if (!whole) { clipped++; continue; }
                halls++;
                string k = plan.Kind.ToString();
                if (!kinds.ContainsKey(k)) Console.WriteLine($"  first {k} hall: {hx},{hz}, its middle at block {hx * P + 51},{hz * P + 51}{(plan.Kind != Kind.Cluster ? $", arrival {plan.Arrival.X},{plan.Arrival.Z}" : "")}");
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
                int inside = 0, got = 0;
                var open = new List<(int, int)>();
                for (int z = bz0 + 1; z < bz1; z++)
                    for (int x = bx0 + 1; x < bx1; x++)
                    {
                        if (!Walk(T(x, z))) continue;
                        inside++;
                        open.Add((x, z));
                        if (fromPassages.Contains((x, z))) got++;
                    }
                if (plan.Kind == Kind.Cluster)
                {
                    rooms += plan.Rooms;
                    minRooms = Math.Min(minRooms, plan.Rooms);
                    maxRooms = Math.Max(maxRooms, plan.Rooms);
                    racks += plan.Racks;
                    lit += plan.Lit;
                    wrecked += plan.Wrecked;
                    terminals += plan.Terminals;
                    boxes += plan.Boxes;
                    foreach (var b in plan.Boots)
                    {
                        boots++;
                        var (bhx, bhz) = WorldLayout.L120HallOf(b.X, b.Z);
                        var pv = layout.L120NearestPocket(bhx, bhz, Kind.Void);
                        var ph = layout.L120NearestPocket(bhx, bhz, Kind.Hallway);
                        if (pv == null && ph == null) bootsNowhere++;
                        else bootInto[pv != null && ph != null ? "either" : pv != null ? "void only" : "hallway only"] = bootInto.GetValueOrDefault(pv != null && ph != null ? "either" : pv != null ? "void only" : "hallway only") + 1;
                        Tile front = T(b.FrontX, b.FrontZ);
                        if (!Walk(front) || !fromPassages.Contains((b.FrontX, b.FrontZ))) Bad($"whole terminal at {b.X},{b.Z}: the tile in front of it cannot be walked to");
                    }
                    worstHall = Math.Max(worstHall, inside - got);
                    if (got == 0)
                    {
                        cutOff++;
                        if (cutOff <= 5) Console.WriteLine($"  cut off: cluster {hx},{hz}");
                    }
                    continue;
                }
                // A pocket: nothing of it reached from the passages; all of it from its arrival; windows
                pockets++;
                pocketTiles += inside;
                if (got > 0) { pocketLeaks++; Bad($"{k} {hx},{hz}: {got} of its tiles reached from the passages"); }
                var fromArrival = Flood(new[] { plan.Arrival });
                int holes = open.Count(o => !fromArrival.Contains(o));
                if (!Walk(T(plan.Arrival.X, plan.Arrival.Z))) Bad($"{k} {hx},{hz}: its arrival {plan.Arrival.X},{plan.Arrival.Z} is not open floor");
                if (holes > 0) { pocketHoles++; Bad($"{k} {hx},{hz}: {holes} open tiles not reached from its arrival"); }
                int windows = open.Count(o => T(o.Item1, o.Item2).Variant == WorldLayout.L120Window);
                if (windows == 0) { noWindow++; Bad($"{k} {hx},{hz}: no window"); }
            }
        Console.WriteLine($"halls wholly inside: {halls} (clipped by the rim: {clipped}): " + string.Join(", ", kinds.Select(p => $"{p.Key} {p.Value} ({100.0 * p.Value / Math.Max(1, halls):0}%)")));
        int clusters = kinds.GetValueOrDefault("Cluster");
        Console.WriteLine($"  clusters: rooms {rooms} ({(double)rooms / Math.Max(1, clusters):0.0} each, {minRooms}-{maxRooms}); racks standing {racks} ({racks / Math.Max(1, clusters)} a cluster), lit {lit} ({100.0 * lit / Math.Max(1, racks):0.0}%), wrecked places {wrecked}, terminals {terminals}, supply boxes {boxes} ({(double)boxes / Math.Max(1, clusters):0.0} a cluster)");
        Console.WriteLine($"  whole terminals {boots} ({100.0 * boots / Math.Max(1, clusters):0}% of clusters); pockets near them: " + string.Join(", ", bootInto.Select(p => $"{p.Key} {p.Value}")) + $", none {bootsNowhere}");
        Console.WriteLine($"  pockets {pockets}: {pocketTiles} open tiles; reached from the passages {pocketLeaks}, with tiles their arrival does not reach {pocketHoles}, without a window {noWindow}");
        Console.WriteLine("zones (tiles): " + string.Join(", ", Enum.GetValues<Zone>().Select(zn => $"{zn} {zones[(int)zn]}")));
        int reachable = walkable - pocketTiles;
        int unreached = reachable - fromPassages.Count;
        Console.WriteLine($"walkable tiles outside the pockets {reachable}, reached from the passages {fromPassages.Count}, unreached {unreached} ({100.0 * unreached / Math.Max(1, reachable):0.00}%), sealed {sealedTiles}; most unreached in one cluster {worstHall}");
        Console.WriteLine($"clusters not reached from the passages: {cutOff}");
        if (cutOff > 0) Bad("clusters not reached from the passages");
        if (unreached > reachable / 100) Bad("more than 1% of walkable tiles unreached");
        if (bootsNowhere > 0) Bad("whole terminals with no pocket near");

        // Arrivals
        int arrivals = 0, wrong = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level120, key * 7919UL) is not { } a) continue;
            arrivals++;
            Tile t = layout.TileAt(a.X, a.Z);
            if (t.Level != WorldLayout.Level120 || t.Zone is not ((byte)Zone.Corridor or (byte)Zone.Room)) wrong++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} outside a passage or a server room");
        if (arrivals < 60 || wrong > 0) Bad("arrivals");
        Console.WriteLine(bad == 0 ? "120stats: OK" : $"120stats: {bad} problem(s)");
        return true;
    }

    static string L120LinkLabel(Tile t) => null;

    /// <summary>For the links mode: the door marked SERVER ROOM in Level 4, and Level 120's doors back to the offices.</summary>
    static string L120UseKind(Tile t) =>
        WorldLayout.IsL120ServerDoor(t) ? "l120-serverroom" : WorldLayout.IsL120ExitDoor(t) ? "l120-door" : null;
}
