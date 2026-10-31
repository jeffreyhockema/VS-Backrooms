using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>
/// shortcuts: how many ways to a later level a fixed window of every level holds, to compare layout versions (run with
/// LAYOUT_VERSION=11 and 12: the progression revision, docs/design/progression/revision.md section 2.B). The window is the
/// cells round the first 12 arrivals of each level (radius 4) and, for Level 8's neighbours, nothing else, so the same
/// cells are looked at in both versions. The features laid down by the layout are counted as clusters of tiles; the ones
/// the threshold network decides at run time (steel doors, elevators, POOL doors) by the rule the network uses. The
/// chances that are plain constants in the network (Level 1's stairs, Level 4's hungry vending machines, Level 5's staff
/// stairs) are listed from them.
/// </summary>
static class Shortcuts
{
    static int Clusters(HashSet<(int, int)> tiles)
    {
        int n = 0;
        var seen = new HashSet<(int, int)>();
        foreach (var start in tiles)
        {
            if (!seen.Add(start)) continue;
            n++;
            var queue = new Queue<(int, int)>();
            queue.Enqueue(start);
            while (queue.Count > 0)
            {
                var (x, z) = queue.Dequeue();
                foreach (var next in new[] { (x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1) })
                    if (tiles.Contains(next) && seen.Add(next)) queue.Enqueue(next);
            }
        }
        return n;
    }

    public static void Run(WorldLayout layout, long seed, int smx, int smz)
    {
        var cells = new Dictionary<int, HashSet<(int, int)>>();
        for (int level = 0; level <= 10; level++)
        {
            var set = cells[level] = new HashSet<(int, int)>();
            for (ulong k = 1; k <= 12; k++)
                if (layout.FindArrival(level, k * 104729UL + 7) is { } a)
                    for (int dz = -4; dz <= 4; dz++)
                        for (int dx = -4; dx <= 4; dx++) set.Add((WorldLayout.MacroOf(a.X) + dx, WorldLayout.MacroOf(a.Z) + dz));
        }
        Console.WriteLine($"layout version {layout.Version}, seed {seed}: cells per level " + string.Join(" ", cells.Select(c => $"L{c.Key}={c.Value.Count}")));
        var clusters = new SortedDictionary<string, HashSet<(int, int)>>();
        var counts = new SortedDictionary<string, int>();
        var cars = new HashSet<(int, int)>();
        var doors = new HashSet<(int, int)>();
        void Add(string kind, int x, int z) { if (!clusters.TryGetValue(kind, out var s)) clusters[kind] = s = new(); s.Add((x, z)); }
        void Count(string kind) => counts[kind] = counts.GetValueOrDefault(kind) + 1;
        ulong useed = (ulong)seed;
        foreach (var (level, set) in cells)
            foreach (var (mx, mz) in set)
            {
                Tile[] tiles = layout.BuildMacro(mx, mz);
                for (int i = 0; i < tiles.Length; i++)
                {
                    Tile t = tiles[i];
                    int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
                    if (t.Kind == TileKind.Floor && t.Variant == Props.MegPlacard) Count($"placards on L{level} floors (plate {t.Stack})");
                    switch (level)
                    {
                        case 0 when t.Kind == TileKind.Pit: Add("L0 pit rooms", x, z); break;
                        case 1:
                            if (t.Stair > 0 && t.Zone == WorldLayout.FlightZoneDown) Add("L1 stair flights down (to L2: 1 in 4 of the bottom floor's)", x, z);
                            if (t.Stair > 0 && t.Zone == WorldLayout.FlightZoneUp) Add("L1 stair flights up (to L4: from the top floors)", x, z);
                            if (t.Stair > 0 && t.Zone == WorldLayout.FlightZoneFun) Add("L1 stair cores to Fun", x, z);
                            if (t.Under == Unders.RunEntrance) Add("L1 EXIT doors to Level !", x, z);
                            if (t.Under == Unders.EndExitL1) Add("L1 doors to The End", x, z);
                            break;
                        case 2 when t.Kind == TileKind.Door && ThresholdNetwork.Door(t):
                            if (doors.Add((x, z)))
                            {
                                int to = ThresholdNetwork.TunnelDoorTarget(useed, x, z, layout.Version);
                                Count(to < 0 ? "L2 steel doors: locked" : $"L2 steel doors: open to L{to}");
                            }
                            break;
                        case 3 or 4 when ThresholdNetwork.Elevator(t):
                        {
                            var car = layout.FeatureOrigin(x, z, ThresholdNetwork.Elevator);
                            if (cars.Add(car))
                            {
                                int to = ThresholdNetwork.ElevatorTarget(level, ThresholdNetwork.ElevatorRoll(useed, car.X, car.Z), layout.Version);
                                Count($"L{level} elevators: to L{to}{(to == level ? " (same level)" : "")}");
                            }
                            break;
                        }
                        case 6 when t.Under == Unders.Descent3: Add("L6 stairwells down to L7", x, z); break;
                        case 6 when t.Kind == TileKind.Floor && t.Variant == Props.Tripwire: Add("L6 tripwires", x, z); break;
                        case 7 when t.Under == Unders.Circle: Add("L7 stone circles", x, z); break;
                        case 7 when t.Under == Unders.Cave: Add("L7 cave mouths", x, z); break;
                        case 7 when t.Under == Unders.TiledSeabed: Add("L7 tiled seabeds", x, z); break;
                        case 9 when t.Kind == TileKind.Floor && t.Variant == Props.FieldGate: Add("L9 field gates", x, z); break;
                        case 9 when t.Under == Unders.FullPool: Add("L9 full pools (pool dives)", x, z); break;
                        case 10 when t.Under == Unders.Noclip: Add("L10 barn walls", x, z); break;
                    }
                }
            }
        foreach (var (kind, set) in clusters) Console.WriteLine($"  {kind,-62} {Clusters(set)}");
        foreach (var (kind, n) in counts) Console.WriteLine($"  {kind,-62} {n}");
        // The boundary gates into a higher survival class and their placards (version 12): how many have one, and where a few are
        int plated = 0, gates = 0, shown = 0;
        int sx = smx * 32, sz = smz * 32;
        foreach (int from in new[] { 0, 1, 2, 3, 4, 5, 6, 7, 9, 10 })
            foreach (var (gx, gz, to) in layout.GatesNear(sx, sz, from, 4000))
            {
                if (WorldLayout.PlacardKind(from, to) == null) continue;
                gates++;
                bool found = false;
                for (int dz = -6; dz <= 6 && !found; dz++)
                    for (int dx = -6; dx <= 6 && !found; dx++)
                    {
                        Tile t = layout.TileAt(gx + dx, gz + dz);
                        if (t.Kind != TileKind.Floor || t.Variant != Props.MegPlacard || t.Level != from) continue;
                        found = true;
                        if (shown++ < 6) Console.WriteLine($"    gate L{from}->L{to} at {gx},{gz}: placard at {gx + dx},{gz + dz} kind {t.Stack} facing {t.Pier}");
                    }
                if (found) plated++;
                else if (Environment.GetEnvironmentVariable("MISSES") == "1") Console.WriteLine($"    no placard: gate L{from}->L{to} at {gx},{gz}");
            }
        Console.WriteLine($"  boundary gates into a higher class within 4000 blocks of spawn: {gates}, with a placard on the near side: {plated}");
        if (Environment.GetEnvironmentVariable("DESCENT") == "1")
            for (ulong k = 1; k <= 3; k++) if (layout.FindDescentLanding(k * 104729UL + 11) is { } d) Console.WriteLine($"    a stairwell down to L7: landing {d.X},{d.Z}");
        if (Environment.GetEnvironmentVariable("ARRIVALS") == "1")
            foreach (int lv in new[] { 0, 1, 2, 3, 4, 5, 6, 7, 9, 10, WorldLayout.Motion, WorldLayout.Hub, WorldLayout.Level974, WorldLayout.FunLevel })
                if (layout.FindArrival(lv, 104729UL + 7) is { } a) Console.WriteLine($"    arrival L{lv}: {a.X},{a.Z}");
        Console.WriteLine("  (rule-only: L1 stairs down to L2 / up to L4, L4 hungry vending, L5 staff stairs to L6 and POOL doors: see ThresholdNetwork, version >= 12 keeps a quarter)");
    }
}
