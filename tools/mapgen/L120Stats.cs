using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L120Zone;

/// <summary>Level 120's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 120stats [halls] [rim]: over a square of (2 x halls + 1) halls each way round the region's centre (or, with "rim",
    /// round a point on its east rim): the share of each kind of hall, the racks (standing, lit, wrecked) and terminals,
    /// the tiles of each zone, and whether every hall, and every walkable tile, can be walked to from the service corridors
    /// (after the shared SealPockets and ClearDoorways passes, as BuildMacro runs them). Arrivals: 60, all in a corridor or
    /// a cold aisle.
    /// </summary>
    static bool L120Modes(WorldLayout layout, string mode, string[] args)
    {
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
        int x0 = (hcx - n) * P, x1 = (hcx + n + 1) * P + 5; // and the corridor past the last hall
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
            || t.Kind == TileKind.Floor && !(t.Stack > 0 && t.Variant == 0) && WorldLayout.IsWalkThroughProp(t.Variant));

        // Walk from every corridor tile
        var reached = new HashSet<(int, int)>();
        var queue = new Queue<(int, int)>();
        int walkable = 0, sealedTiles = 0, racksSeen = 0, litSeen = 0, terminalsSeen = 0;
        var zones = new int[16];
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++)
            {
                Tile t = T(x, z);
                if (t.Level != WorldLayout.Level120) continue;
                zones[Math.Min((int)t.Zone, 15)]++;
                if (t.Variant == WorldLayout.L120Rack)
                {
                    racksSeen++;
                    if (t.Detail is >= WorldLayout.L120RackLedA and <= WorldLayout.L120RackBoth) litSeen++;
                }
                if (t.Variant == WorldLayout.L120Terminal) terminalsSeen++;
                if (!Walk(t)) continue;
                walkable++;
                if (t.Sealed) sealedTiles++;
                if (t.Zone == (byte)Zone.Corridor && t.Kind == TileKind.Floor && reached.Add((x, z))) queue.Enqueue((x, z));
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

        // Halls: kinds, racks, and whether each was reached from the corridors
        var kinds = new SortedDictionary<string, int>();
        int halls = 0, clipped = 0, cutOff = 0, racks = 0, lit = 0, wrecked = 0, terminals = 0, worstHall = 0;
        for (int hz = hcz - n; hz <= hcz + n; hz++)
            for (int hx = hcx - n; hx <= hcx + n; hx++)
            {
                var plan = layout.L120PlanOf(hx, hz);
                int bx0 = hx * P + 5, bx1 = hx * P + P, bz0 = hz * P + 5, bz1 = hz * P + P;
                bool whole = Mine(bx0, bz0) && Mine(bx1, bz1) && Mine(bx0, bz1) && Mine(bx1, bz0);
                if (!whole) { clipped++; continue; }
                halls++;
                string k = plan.Kind.ToString();
                if (!kinds.ContainsKey(k)) Console.WriteLine($"  first {k} hall: {hx},{hz}, its middle at block {hx * P + 51},{hz * P + 51}");
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
                racks += plan.Racks;
                lit += plan.Lit;
                wrecked += plan.Wrecked;
                terminals += plan.Terminals;
                int inside = 0, got = 0;
                for (int z = bz0 + 1; z < bz1; z++)
                    for (int x = bx0 + 1; x < bx1; x++)
                    {
                        if (!Walk(T(x, z))) continue;
                        inside++;
                        if (reached.Contains((x, z))) got++;
                    }
                worstHall = Math.Max(worstHall, inside - got);
                if (got == 0)
                {
                    cutOff++;
                    if (cutOff <= 5) Console.WriteLine($"  cut off: {plan.Kind} hall {hx},{hz}");
                }
            }
        Console.WriteLine($"halls wholly inside: {halls} (clipped by the rim: {clipped}): " + string.Join(", ", kinds.Select(p => $"{p.Key} {p.Value} ({100.0 * p.Value / Math.Max(1, halls):0}%)")));
        Console.WriteLine($"  in those halls: racks standing {racks} ({racks / Math.Max(1, halls)} a hall), lit {lit} ({100.0 * lit / Math.Max(1, racks):0}%), wrecked places {wrecked}, terminals {terminals}");
        Console.WriteLine($"  in the window: racks {racksSeen}, lit {litSeen}, terminals {terminalsSeen}");
        Console.WriteLine("zones (tiles): " + string.Join(", ", Enum.GetValues<Zone>().Select(zn => $"{zn} {zones[(int)zn]}")));
        int unreached = walkable - reached.Count;
        Console.WriteLine($"walkable tiles {walkable}, reached from the corridors {reached.Count}, unreached {unreached} ({100.0 * unreached / Math.Max(1, walkable):0.00}%), sealed {sealedTiles}; most unreached in one hall {worstHall}");
        Console.WriteLine($"halls not reached from the corridors: {cutOff}");
        if (cutOff > 0) Bad("halls not reached from the corridors");
        if (unreached > walkable / 100) Bad("more than 1% of walkable tiles unreached");

        // Arrivals
        int arrivals = 0, wrong = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level120, key * 7919UL) is not { } a) continue;
            arrivals++;
            Tile t = layout.TileAt(a.X, a.Z);
            if (t.Level != WorldLayout.Level120 || t.Zone is not ((byte)Zone.Corridor or (byte)Zone.Cold)) wrong++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} outside a corridor or a cold aisle");
        if (arrivals < 60 || wrong > 0) Bad("arrivals");
        Console.WriteLine(bad == 0 ? "120stats: OK" : $"120stats: {bad} problem(s)");
        return true;
    }

    static string L120LinkLabel(Tile t) => null;

    static string L120UseKind(Tile t) => null;
}
