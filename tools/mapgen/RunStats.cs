using Backrooms.Worldgen;

/// <summary>Level !'s harness modes (this file is the level's own; see docs/new-levels/CONTRACT.md).</summary>
static partial class LevelModes
{
    /// <summary>
    /// runstats: every lane checked (course length, a way through, the obstacle rules, dark stretches, false exits, the
    /// Safe Zone and holes, arrivals). runmap &lt;lane&gt;: the lane as text (runmap-&lt;lane&gt;.txt). runsim: the chase
    /// against scripted runners.
    /// </summary>
    static bool RunModes(WorldLayout layout, string mode, string[] args)
    {
        switch (mode)
        {
            case "runstats": RunStats(layout); return true;
            case "runmap": RunMap(layout, args.Length > 3 ? int.Parse(args[3]) : 0); return true;
            case "runsim": RunSim(layout); return true;
            case "runlinks": RunLinks(layout); return true;
            case "runhash":
                // The layout hash without Level !'s ways in, then with them: only the levels they are in may differ
                WorldLayout.RunEntrances = false;
                Console.WriteLine("--- without Level !'s entrances");
                LayoutHash.Run(args);
                WorldLayout.RunEntrances = true;
                Console.WriteLine("--- with them");
                LayoutHash.Run(args);
                return true;
        }
        return false;
    }

    static void RunStats(WorldLayout layout)
    {
        int problems = 0;
        void Problem(string what) { problems++; Console.WriteLine("  PROBLEM " + what); }
        var sw = System.Diagnostics.Stopwatch.StartNew();
        int safe = 0, holes = 0;
        var dests = new Dictionary<int, int>();
        for (int lane = 0; lane < WorldLayout.RunLanes; lane++)
        {
            var L = layout.RunPlan(lane);
            if (L.HasSafe) safe++;
            if (L.HasHole) holes++;
            dests[L.Destination] = dests.GetValueOrDefault(L.Destination) + 1;

            // A way through from the hallway door to the exit, going round everything solid (jumpable shelving counts as open)
            bool Passable(Tile t) => t.Kind is TileKind.Floor or TileKind.Doorway
                && (t.Variant == 0 || WorldLayout.IsWalkThroughProp(t.Variant) || t.Variant == Props.RunShelfFallen);
            var seen = new HashSet<(int, int)> { L.HallDoor };
            var q = new Queue<(int, int)>();
            q.Enqueue(L.HallDoor);
            bool through = false;
            while (q.Count > 0)
            {
                var (x, z) = q.Dequeue();
                if (Math.Abs(x - L.ExitDoor.X) + Math.Abs(z - L.ExitDoor.Z) == 1) { through = true; break; }
                foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    var n = (x + dx, z + dz);
                    if (!L.In(n.Item1, n.Item2) || seen.Contains(n) || !Passable(L.At(n.Item1, n.Item2))) continue;
                    seen.Add(n);
                    q.Enqueue(n);
                }
            }
            if (!through) Problem($"lane {lane}: no way from the hallway door to the exit");

            // Rows of a straight: blocked count (hard props, pits) <= 3 of 5
            int worst = 0, rows = 0, hard = 0, trips = 0;
            for (int s = 0; s < L.ExitS; s++)
            {
                var (cx, cz) = L.Line[s];
                bool crossways = s > 0 && L.Line[s - 1].Z == cz;
                if (crossways) continue;
                int blocked = 0;
                for (int k = -2; k <= 2; k++)
                {
                    Tile t = L.At(cx + k, cz);
                    if (t.Kind == TileKind.Pit || t.Kind == TileKind.Floor && t.Variant != 0 && !WorldLayout.IsWalkThroughProp(t.Variant) && t.Variant != Props.RunShelfFallen)
                        blocked++;
                    if (t.Kind == TileKind.Floor && t.Variant is Props.RunToyCar or Props.RunBoxes or Props.RunCord or Props.RunDebris) trips++;
                }
                if (blocked > 0) hard++;
                worst = Math.Max(worst, blocked);
                rows++;
            }
            if (worst > 3) Problem($"lane {lane}: a row with {worst} of 5 tiles blocked");

            // Dark stretches between signs
            int darkest = 0, darkestLast = 0;
            for (int i = 1; i < L.Signs.Count; i++)
            {
                int gap = L.Signs[i] - L.Signs[i - 1];
                if (L.HasSafe && L.Signs[i - 1] <= L.SafeTo && L.Signs[i] >= L.SafeFrom) continue; // the Safe Zone has its own lights
                if (L.Third(L.Signs[i]) == 2) darkestLast = Math.Max(darkestLast, gap);
                else darkest = Math.Max(darkest, gap);
            }
            if (darkest > 32 || darkestLast > 40) Problem($"lane {lane}: a dark stretch of {darkest} / {darkestLast}");
            if (L.FakeExits.Count != 2) Problem($"lane {lane}: {L.FakeExits.Count} false exits");

            int doors = 0, events = L.Events.Count;
            for (int i = 0; i < L.Tiles.Length; i++) if (L.Tiles[i].Kind == TileKind.Door && L.Tiles[i].Pattern is WallPattern.RunSideDoor or WallPattern.RunDentedDoor or WallPattern.RunSwingDoor) doors++;
            string ev = string.Join(" ", L.Events.GroupBy(e => e.Kind).Select(g => $"{g.Key}:{g.Count()}"));
            Console.WriteLine($"lane {lane,2}: course {L.ExitS,3} (thirds at {L.Middle}, {L.Last}), signs {L.Signs.Count,2}, darkest {darkest}/{darkestLast}, " +
                $"doors {doors,3}, obstacle rows {hard,3}, worst {worst}, trip props {trips,2}, {ev}{(L.HasSafe ? $", SAFE {L.SafeFrom}-{L.SafeTo}" : "")}{(L.HasHole ? ", hole" : "")} -> {WorldLayout.DisplayNumber(L.Destination)}");
            if (L.ExitS < 600 || L.ExitS > 640) Problem($"lane {lane}: course length {L.ExitS} outside 600-640");
        }
        Console.WriteLine($"planned {WorldLayout.RunLanes} lanes in {sw.ElapsedMilliseconds} ms; safe zones {safe}, holes {holes}, exits " +
            string.Join(", ", dests.Select(d => $"{WorldLayout.DisplayNumber(d.Key)} x{d.Value}")));

        // Arrivals: always on a start room's marked tile
        int found = 0, wrong = 0;
        for (ulong k = 1; k <= 60; k++)
        {
            var a = layout.FindArrival(WorldLayout.RunLevel, k * 7919UL + 3);
            if (a == null) continue;
            found++;
            int lane = layout.RunLaneAt(a.Value.X, a.Value.Z);
            var (lx, lz) = layout.RunLocal(lane, a.Value.X, a.Value.Z);
            if (lane < 0 || (lx, lz) != layout.RunPlan(lane).Arrival) wrong++;
        }
        Console.WriteLine($"arrivals: {found}/60 found, {wrong} not on a start room's arrival tile");
        if (found < 60 || wrong > 0) problems++;

        // Cell build cost
        sw.Restart();
        var (ox, oz) = (layout.RunOriginX / 32, layout.RunOriginZ / 32);
        int cells = 0;
        for (int dz = 0; dz < 17; dz += 4) for (int dx = 0; dx < 17; dx += 3) { layout.BuildMacro(ox + dx, oz + dz); cells++; }
        Console.WriteLine($"{cells} cells built in {sw.ElapsedMilliseconds} ms");
        Console.WriteLine(problems == 0 ? "runstats: all good" : $"runstats: {problems} problems");
    }

    static void RunMap(WorldLayout layout, int lane)
    {
        var L = layout.RunPlan(lane);
        var sb = new System.Text.StringBuilder();
        for (int z = 0; z < WorldLayout.RunLane.Length; z++)
        {
            for (int x = 0; x < WorldLayout.RunLane.Width; x++)
            {
                Tile t = L.At(x, z);
                char c = t.Kind switch
                {
                    TileKind.Wall => t.Pattern == WallPattern.RunVoid ? '%' : t.Pattern == WallPattern.RunSafeWall ? '=' : '#',
                    TileKind.Pit => 'O',
                    TileKind.Door => t.Pattern switch
                    {
                        WallPattern.RunFakeExit => 'F', WallPattern.RunTrueExit => 'E', WallPattern.RunChainedDoor => 'C',
                        WallPattern.RunMarkedDoor => '!', WallPattern.RunDentedDoor => 'D', WallPattern.RunSwingDoor => 'S', _ => 'd',
                    },
                    TileKind.Doorway => 'h',
                    _ => t.Variant switch
                    {
                        0 => t.Ceiling == CeilingKind.RunExitSign ? '*' : t.Zone == WorldLayout.RunZone.Safe ? 'b' : t.Floor == FloorKind.RunCracked ? ':' : '.',
                        Props.RunGurney => 'g', Props.RunWheelchair => 'w', Props.RunIvStand => 'i', Props.RunChairs => 'c',
                        Props.RunCrashCart => 'k', Props.RunShelfFallen => '_', Props.RunShelfStanding => 'T', Props.RunTray => '+',
                        Props.RunRemains => 'r', _ => WorldLayout.IsWalkThroughProp(t.Variant) ? ',' : 'x',
                    },
                };
                if ((x, z) == L.Arrival) c = '@';
                sb.Append(c);
            }
            sb.Append($"  {z}\n");
        }
        File.WriteAllText($"runmap-{lane}.txt", sb.ToString());
        Console.WriteLine($"wrote runmap-{lane}.txt");
    }

    /// <summary>
    /// runlinks: Level !'s thresholds through the network: every lane's true exit (where to, the same each time), its holes,
    /// and the ways in found in a search of Levels 1, 2 and 37 (each into a start room).
    /// </summary>
    static void RunLinks(WorldLayout layout)
    {
        var net = new Backrooms.Thresholds.ThresholdNetwork(layout, new WorldGeometry(256), 12345);
        int bad = 0;
        string LevelOf(Backrooms.Thresholds.Link? l) => l is { } k ? WorldLayout.DisplayNumber(layout.LevelAt(WorldLayout.MacroOf((int)k.X), WorldLayout.MacroOf((int)k.Z))) : "nowhere";
        var exits = new Dictionary<string, int>();
        for (int lane = 0; lane < WorldLayout.RunLanes; lane++)
        {
            var L = layout.RunPlan(lane);
            var (ex, ez) = layout.RunWorld(lane, L.ExitDoor.X, L.ExitDoor.Z);
            var p = net.Used(ex, ez, "runexit", out _);
            var a = p == null ? null : net.Take(p, null);
            var b = p == null ? null : net.Take(net.Used(ex, ez, "runexit", out _), null);
            string to = LevelOf(a);
            if (a == null || a != b || to != WorldLayout.DisplayNumber(L.Destination) || p.TwoWay) { bad++; Console.WriteLine($"  PROBLEM lane {lane} exit -> {to}"); }
            exits[to] = exits.GetValueOrDefault(to) + 1;
            for (int z = 0; z < WorldLayout.RunLane.Length; z++)
                for (int x = 0; x < WorldLayout.RunLane.Width; x++)
                {
                    Tile t = L.At(x, z);
                    if (t.Under != Unders.RunHole) continue;
                    var (hx, hz) = layout.RunWorld(lane, x, z);
                    var hole = net.Walked(hx, hz, layout.TileAt(hx, hz), -3);
                    string down = LevelOf(hole == null ? null : net.Take(hole, null));
                    if (down != "8") { bad++; Console.WriteLine($"  PROBLEM lane {lane} hole -> {down}"); }
                    x = 99; z = 99999;
                }
        }
        Console.WriteLine("exits: " + string.Join(", ", exits.Select(e => $"Level {e.Key} x{e.Value}")) + " (one-way, the same each time)");

        // The ways in: walk out from many arrivals in Levels 1, 2 and 37 looking for them
        var found = new Dictionary<string, int>();
        var seen = new HashSet<(int, int)>();
        foreach (int level in new[] { 1, 2, WorldLayout.Poolrooms })
            for (ulong k = 1; k <= 120 && found.GetValueOrDefault("L" + level) < 6; k++)
            {
                if (layout.FindArrival(level, k * 104729UL + 11) is not { } at) continue;
                for (int dz = -6; dz <= 6; dz++)
                    for (int dx = -6; dx <= 6; dx++)
                    {
                        int mx = WorldLayout.MacroOf(at.X) + dx, mz = WorldLayout.MacroOf(at.Z) + dz;
                        if (!seen.Add((mx, mz)) || layout.LevelAt(mx, mz) != level) continue;
                        var tiles = layout.BuildMacro(mx, mz);
                        for (int i = 0; i < tiles.Length; i++)
                        {
                            Tile t = tiles[i];
                            string kind = t.Under switch
                            {
                                Unders.RunEntrance => "runentry",
                                Unders.RunRedCorridor when t.Kind == TileKind.Door => "runentry",
                                Unders.RunFalseWall => "runfalsewall",
                                _ => null,
                            };
                            if (kind == null) continue;
                            int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
                            var p = net.Used(x, z, kind, out _);
                            var a = p == null ? null : net.Take(p, null);
                            string to = LevelOf(a);
                            bool start = a is { } l && layout.RunLaneAt((int)l.X, (int)l.Z) is int ln and >= 0
                                && layout.RunLocal(ln, (int)l.X, (int)l.Z) == layout.RunPlan(ln).Arrival;
                            if (!start || p.TwoWay) { bad++; Console.WriteLine($"  PROBLEM L{level} {kind} at {x},{z} -> {to}"); }
                            found["L" + level] = found.GetValueOrDefault("L" + level) + 1;
                        }
                    }
            }
        Console.WriteLine($"ways in found (searched {seen.Count} cells): " + string.Join(", ", found.Select(f => $"{f.Key} x{f.Value}")) + ", each into a start room, one-way");
        Console.WriteLine(bad == 0 ? "runlinks: all good" : $"runlinks: {bad} problems");
    }

    /// <summary>The chase against scripted runners: who is caught, and when.</summary>
    static void RunSim(WorldLayout layout)
    {
        var L = layout.RunPlan(0);
        double sprint = RunChase.SprintSpeed; const double dt = 0.1;
        string[] names = { "Low", "Normal", "High" };
        for (int diff = 0; diff < 3; diff++)
        {
            Console.WriteLine($"{names[diff]} (course {L.ExitS}, sprint {sprint:0.00} b/s, a clean run {L.ExitS / sprint:0} s):");
            foreach (var (name, leaveAt, mistakes, speed) in new (string, double, int, double)[]
                     { ("clean sprint", 5, 0, 1.0), ("3 mistakes of 2.5 s", 5, 3, 1.0), ("5 mistakes", 5, 5, 1.0), ("8 mistakes", 5, 8, 1.0),
                       ("dawdles 10 s, clean", 10, 0, 1.0), ("walking", 5, 0, 0.5), ("stops at 200", 5, 0, -1.0) })
            {
                var chase = new RunChase(sprint, diff, L.Last, -1, -1, -8);
                double pos = -4, t = 0, stall = 0;
                var mistakeAt = new HashSet<int>();
                for (int m = 0; m < mistakes; m++) mistakeAt.Add(60 + m * (L.ExitS - 100) / Math.Max(1, mistakes));
                string result = null;
                double minGap = double.MaxValue;
                while (t < 400)
                {
                    t += dt;
                    double v = 0;
                    if (t >= leaveAt)
                    {
                        if (stall > 0) stall -= dt;
                        else if (speed < 0 && pos >= 200) v = 0;
                        else v = sprint * Math.Abs(speed);
                    }
                    int before = (int)pos;
                    pos += v * dt;
                    if ((int)pos != before && mistakeAt.Remove((int)pos)) stall = 2.5;
                    if (chase.Step(dt, pos)) { result = $"caught at {pos:0} after {t:0.0} s"; break; }
                    if (chase.Loose) minGap = Math.Min(minGap, chase.Gap(pos));
                    if (pos >= L.ExitS) { result = $"escaped in {t:0.0} s, closest {minGap:0.0}"; break; }
                }
                Console.WriteLine($"  {name,-22} {result ?? "still running"}");
            }
        }
    }

    /// <summary>For the links mode: the label of one of the level's thresholds walked into on this tile (e.g. "pit"), or null.</summary>
    static string RunLinkLabel(Tile t) => t.Under switch
    {
        Unders.RunFalseWall => "run-falsewall",
        Unders.RunHole when t.Level == WorldLayout.RunLevel => "run-hole",
        _ => null,
    };

    /// <summary>For the links mode: the threshold kind of one of the level's blocks used on this tile (its BlockBehaviorThreshold kind), or null.</summary>
    static string RunUseKind(Tile t) => t.Kind == TileKind.Door ? t.Pattern switch
    {
        WallPattern.RunEntryDoor => "runentry",
        WallPattern.RunTrueExit => "runexit",
        _ => null,
    } : null;
}
