using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L52Zone;

/// <summary>Level 52's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 52stats [reach] [plan]: the campuses within <c>reach</c> lattice cells of Marshall David (default 2): for each, its
    /// kind, size, buildings (kind, storeys) and rooms (kinds on the ground storey, doors, plaques); then, over the cells
    /// each campus covers, whether every walkable tile of the ground storey can be walked to from the gaps in its fence
    /// (after the shared passes, as BuildMacro runs them), and whether every stairwell has its two doors. Arrivals: 60, all
    /// on a campus or in a ground-floor corridor. "plan" also writes l52plan.txt, Marshall David's ground storey in
    /// characters.
    /// </summary>
    static bool L52Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "52links") return L52Links(layout);
        if (mode != "52stats") return false;
        int reach = args.Length > 3 && int.TryParse(args[3], out int r) ? r : 2;
        bool plan = args.Contains("plan");
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }

        var (mci, mcj) = layout.L52MarshallDavid;
        var (turner, barry) = layout.L52Named;
        Console.WriteLine($"region centre cells {layout.L52CentreX},{layout.L52CentreZ}, radius {layout.L52Radius}; Marshall David at lattice {mci},{mcj}, J. Turner {turner}, J. Barry {barry}");

        var cells = new Dictionary<(int, int), Tile[]>();
        Tile T(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            if (!cells.TryGetValue((mx, mz), out var tiles))
            {
                if (cells.Count > 4000) cells.Clear();
                cells[(mx, mz)] = tiles = layout.BuildMacro(mx, mz);
            }
            return tiles[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
        }
        bool Walk(Tile t) => t.Level == WorldLayout.Level52 && (t.Kind is TileKind.Doorway
            || t.Kind == TileKind.Floor && !(t.Stack > 0 && t.Variant == 0) && !t.SupplyBox && WorldLayout.IsWalkThroughProp(t.Variant));

        int campuses = 0, open = 0, rooms = 0, doorless = 0, plaques = 0, buildings = 0, wells = 0, bridgeDoors = 0, canopies = 0;
        var kinds = new SortedDictionary<string, int>();
        var bkinds = new SortedDictionary<string, int>();
        var storeys = new SortedDictionary<int, int>();
        long walkable = 0, unreached = 0;
        for (int cj = mcj - reach; cj <= mcj + reach; cj++)
            for (int ci = mci - reach; ci <= mci + reach; ci++)
            {
                var head = layout.L52HeadOf(ci, cj);
                if (!head.Exists) { open++; continue; }
                var c = layout.L52CampusOf(ci, cj);
                campuses++;
                Console.WriteLine($"campus {ci},{cj} {head.Kind}: {head.W}x{head.D} at {head.X0},{head.Z0}; paint {WorldLayout.L52Paints[c.Paint]}, facade {WorldLayout.L52Facades[c.Facade]}; "
                    + string.Join(", ", c.Buildings.Select(b => $"{b.Index}:{b.Kind}x{b.Storeys} {b.U1 - b.U0 + 1}x{b.V1 - b.V0 + 1}")));
                foreach (var b in c.Buildings)
                {
                    buildings++;
                    bkinds[b.Kind.ToString()] = bkinds.GetValueOrDefault(b.Kind.ToString()) + 1;
                    storeys[b.Storeys] = storeys.GetValueOrDefault(b.Storeys) + 1;
                }
                foreach (var room in c.Rooms)
                {
                    rooms++;
                    string k = layout.L52KindOn(c, room, 0).ToString();
                    kinds[k] = kinds.GetValueOrDefault(k) + 1;
                    if (!room.HasDoor) doorless++;
                }
                for (int i = 0; i < c.Grid.Length; i++)
                {
                    if (c.Grid[i].Overhead == Overheads.L52PlaqueLo) plaques++;
                    if (c.Grid[i].Overhead == Overheads.L52BridgeDoor) bridgeDoors++;
                    if (c.Grid[i].Overhead == Overheads.L52Canopy) canopies++;
                    if (c.Grid[i].Zone == (byte)Zone.Stair && c.Grid[i].Detail == 0) wells++;
                }
                // Walk the ground storey from the gaps in the fence (through the built cells, as the game sees them)
                var reached = new HashSet<(int, int)>();
                var queue = new Queue<(int, int)>();
                for (int s = 0; s < 4; s++)
                {
                    int g = head.Gap[s];
                    var (x, z) = s switch { 0 => (head.X0 + g, head.Z0), 1 => (head.X1, head.Z0 + g), 2 => (head.X0 + g, head.Z1), _ => (head.X0, head.Z0 + g) };
                    if (Walk(T(x, z)) && reached.Add((x, z))) queue.Enqueue((x, z));
                }
                while (queue.Count > 0)
                {
                    var (x, z) = queue.Dequeue();
                    foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nx = x + dx, nz = z + dz;
                        if (!head.Contains(nx, nz) || reached.Contains((nx, nz)) || !Walk(T(nx, nz))) continue;
                        reached.Add((nx, nz));
                        queue.Enqueue((nx, nz));
                    }
                }
                int w = 0, un = 0, shown = 0;
                for (int z = head.Z0; z <= head.Z1; z++)
                    for (int x = head.X0; x <= head.X1; x++)
                    {
                        Tile t = T(x, z);
                        if (!Walk(t)) continue;
                        w++;
                        if (reached.Contains((x, z))) continue;
                        un++;
                        if (shown++ < 6) Console.WriteLine($"  unreached: {(Zone)t.Zone} at {x},{z} (campus {x - head.X0},{z - head.Z0})");
                    }
                walkable += w;
                unreached += un;
                if (un > w / 100) Bad($"campus {ci},{cj}: {un} of {w} walkable tiles unreached from the fence's gaps");
                if (plan && ((ci, cj) == (mci, mcj) || un > 0)) WriteL52Plan(c, (ci, cj) == (mci, mcj) ? "l52plan.txt" : $"l52plan-{ci}-{cj}.txt");
            }
        Console.WriteLine($"campuses {campuses} (open plain {open}); buildings {buildings}: " + string.Join(", ", bkinds.Select(p => $"{p.Key} {p.Value}"))
            + "; storeys " + string.Join(", ", storeys.Select(p => $"{p.Key}: {p.Value}")));
        Console.WriteLine($"rooms {rooms} (ground storey): " + string.Join(", ", kinds.Select(p => $"{p.Key} {p.Value}")) + $"; without a door {doorless}; plaques {plaques}; stairwells {wells}; bridges {bridgeDoors / 6}; canopy tiles {canopies}");
        Console.WriteLine($"walkable ground-storey tiles {walkable}, unreached {unreached} ({100.0 * unreached / Math.Max(1, walkable):0.00}%)");
        if (doorless > 0) Bad("rooms without a door");

        int arrivals = 0, wrong = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level52, key * 7919UL) is not { } a) continue;
            arrivals++;
            Tile t = layout.TileAt(a.X, a.Z);
            if (t.Level != WorldLayout.Level52 || t.Zone is not ((byte)Zone.Corridor or (byte)Zone.Lobby or (byte)Zone.Path or (byte)Zone.Lawn)) wrong++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} off the campuses");
        if (layout.FindArrival(WorldLayout.Level52, 5) is { } five) Console.WriteLine($"arrival for key 5 (/backrooms dummy place 52 5): {five.X},{five.Z}");
        if (arrivals < 60 || wrong > 0) Bad("arrivals");
        Console.WriteLine(bad == 0 ? "52stats: OK" : $"52stats: {bad} problem(s)");
        return true;
    }

    /// <summary>A campus's ground storey in characters (l52plan.txt).</summary>
    static void WriteL52Plan(WorldLayout.L52Campus c, string file)
    {
        var sb = new System.Text.StringBuilder();
        for (int v = 0; v < c.D; v++)
        {
            for (int u = 0; u < c.W; u++)
            {
                Tile t = c.At(u, v);
                char ch = (Zone)t.Zone switch
                {
                    Zone.Lawn => t.Variant == Props.Tree ? 'T' : '.', Zone.Path => t.Variant != 0 ? 'p' : ',', Zone.Turf => t.Variant == Props.Tree ? 'T' : t.Variant != 0 ? 'p' : '"',
                    Zone.Court => '=', Zone.Fence => '#', Zone.Ext => t.Under == Unders.L52Window ? 'o' : 'X', Zone.Wall => t.Under == Unders.L52Locker ? 'L' : 'x',
                    Zone.Door => 'D', Zone.Entrance => 'E', Zone.Corridor => t.Overhead != 0 ? 'n' : t.Variant != 0 ? 'v' : ' ', Zone.Lobby => ' ',
                    Zone.Stair => t.Kind == TileKind.Wall ? 'x' : 's', Zone.Room => t.Variant != 0 ? 'f' : t.SupplyBox ? 'b' : '_', Zone.Hall => t.Variant != 0 ? 'f' : '_',
                    _ => '?',
                };
                sb.Append(ch);
            }
            sb.AppendLine();
        }
        File.WriteAllText(file, sb.ToString());
        Console.WriteLine("wrote " + file);
    }

    static string L52LinkLabel(Tile t) => null;

    static string L52UseKind(Tile t) => null;

    /// <summary>
    /// 52links: Level 52's ways in, in the world as laid out (LINKS.md, "Level 52"): the high schools nearest spawn (the left
    /// door's position, its distance from spawn) and how many there are per km2 of the city; the EMERGENCY EXIT doors nearest
    /// spawn in Level 4 and how many per km2 of it; on the campus side, Marshall David's doors that can be a way back and where
    /// ten arrivals by each way in are put down (each just inside one of those doors).
    /// </summary>
    static bool L52Links(WorldLayout layout)
    {
        var (sx, sz) = layout.L52SpawnBlock;
        double Km(int x, int z) => Math.Sqrt((double)(x - sx) * (x - sx) + (double)(z - sz) * (z - sz)) / 1000.0;
        Tile At(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            return layout.BuildMacro(mx, mz)[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)];
        }
        int bad = 0;

        // The city
        var (cmx, cmz, crad) = layout.L52City;
        Console.WriteLine($"spawn block {sx},{sz}; the city: centre cell {cmx},{cmz}, radius {crad} cells ({crad * 32 / 1000.0:0.#} km)");
        Console.WriteLine("high schools nearest spawn (Level 11; the left door as seen from the street):");
        foreach (var s in layout.L52NearestSchools(5))
        {
            Tile t = At(s.DoorX, s.DoorZ);
            bool ok = t.Level == 11 && t.Under == Unders.L52SchoolDoor;
            if (!ok) bad++;
            Console.WriteLine($"  door {s.DoorX},{s.DoorZ} facing {s.Facing}, lot {s.X1 - s.X0 + 1} wide, block {s.Bi},{s.Bj}: {Km(s.DoorX, s.DoorZ):0.00} km from spawn{(ok ? "" : "  BAD: not built")}");
        }
        // Density: every block of a window round the city's middle
        int blocks = 0, schools = 0, candidates = 0;
        var doors = new List<(int X, int Z)>();
        int bi0 = -60, bi1 = 60, bj0 = -75, bj1 = 75;
        for (int bj = bj0; bj <= bj1; bj++)
            for (int bi = bi0; bi <= bi1; bi++)
            {
                int gx = layout.CityOriginX + bi * WorldLayout.AvePitch + WorldLayout.AvePitch / 2, gz = layout.CityOriginZ + bj * WorldLayout.StreetPitch + WorldLayout.StreetPitch / 2;
                if (layout.LevelAt(WorldLayout.MacroOf(gx), WorldLayout.MacroOf(gz)) != 11) continue;
                blocks++;
                var near = layout.L52SchoolsNear(gx, gz, 0);
                if (near.Count > 0) { schools++; doors.Add((near[0].DoorX, near[0].DoorZ)); }
            }
        candidates = (int)Math.Round(blocks * WorldLayout.L52SchoolBlockChance);
        double km2 = blocks * WorldLayout.AvePitch * WorldLayout.StreetPitch / 1e6;
        double nn = 0;
        foreach (var a in doors)
        {
            double best = double.MaxValue;
            foreach (var b in doors) if (a != b) best = Math.Min(best, Math.Sqrt((double)(a.X - b.X) * (a.X - b.X) + (double)(a.Z - b.Z) * (a.Z - b.Z)));
            nn += best;
        }
        Console.WriteLine($"city window {bi1 - bi0 + 1} x {bj1 - bj0 + 1} blocks round its middle: {blocks} blocks ({km2:0.0} km2), {schools} high schools "
            + $"(about {candidates} blocks drawn for one; the rest had no lot for it): {schools / km2:0.00} per km2, one per {(schools > 0 ? blocks / (double)schools : 0):0} blocks; "
            + $"mean distance to the next {(doors.Count > 1 ? nn / doors.Count / 1000 : 0):0.00} km");

        // Level 4
        Console.WriteLine("EMERGENCY EXIT doors nearest spawn (Level 4):");
        var exits = layout.L52NearestExits(5);
        foreach (var (x, z, f) in exits)
        {
            Tile t = At(x, z);
            bool ok = t.Level == 4 && t.Under == Unders.L52ExitDoor && t.Kind == TileKind.Wall;
            if (!ok) bad++;
            Console.WriteLine($"  door {x},{z} facing {f}: {Km(x, z):0.00} km from spawn{(ok ? "" : "  BAD")}");
        }
        // Density: of the Level 4 cells drawn for one, how many had a wall for it (the first 200 out from spawn)
        int drawn = 0, built = 0;
        for (int r = 1; r < 8000 && drawn < 200; r++)
            for (int dz = -r; dz <= r && drawn < 200; dz++)
                for (int dx = -r; dx <= r && drawn < 200; dx += Math.Abs(dz) == r ? 1 : 2 * r)
                {
                    int mx = sx / 32 + dx, mz = sz / 32 + dz;
                    if (!layout.L52ExitCell(mx, mz) || layout.LevelAt(mx, mz) != 4) continue;
                    drawn++;
                    if (layout.L52ExitIn(mx, mz) != null) built++;
                }
        double perKm2 = 1e6 / 1024.0 * WorldLayout.L52ExitCellChance * built / Math.Max(1, drawn);
        Console.WriteLine($"Level 4 cells drawn for one: {drawn}, with a wall for it: {built}; {perKm2:0.00} per km2 of Level 4, one to about every {1 / Math.Max(1e-9, perKm2):0.0} km2");

        // The campus side
        var (mi, mj) = layout.L52MarshallDavid;
        var md = layout.L52CampusOf(mi, mj);
        int quad = 0, wing = 0;
        for (int v = 0; v < md.D; v++)
            for (int u = 0; u < md.W; u++)
            {
                if (md.At(u, v).Under == Unders.L52QuadDoor) quad++;
                if (md.At(u, v).Under == Unders.L52WingDoor) wing++;
            }
        Console.WriteLine($"Marshall David: {quad} tiles of quad front doors, {wing} of teaching-block end doors that can be a way back");
        foreach (var (name, door) in new[] { ("from a high school", (Func<Tile, bool>)WorldLayout.IsL52QuadDoor), ("from an emergency exit", WorldLayout.IsL52WingDoor) })
        {
            int beside = 0, on = 0;
            var seen = new HashSet<(int, int)>();
            for (ulong k = 1; k <= 10; k++)
            {
                if (layout.FindArrival(WorldLayout.Level52, k * 7919, door, spot: WorldLayout.IsL52InsideDoorSpot) is not { } a) continue;
                if (layout.FeatureBeside(a.X, a.Z, door) is { } f) { beside++; seen.Add(f); }
                if (layout.L52CampusAt(a.X, a.Z, out _) is { } c) on++;
            }
            Console.WriteLine($"  arrivals {name}: 10 tried, {beside} just inside one of those doors ({seen.Count} different doors), {on} on a campus");
            if (beside < 10) bad++;
        }
        Console.WriteLine(bad == 0 ? "52links: OK" : $"52links: {bad} BAD");
        return true;
    }
}
