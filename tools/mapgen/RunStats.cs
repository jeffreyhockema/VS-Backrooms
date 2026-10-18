using Backrooms.Worldgen;

/// <summary>Level !'s harness modes (this file is the level's own; see docs/design/new-levels/CONTRACT.md).</summary>
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
            case "runfair": RunFair(layout); return true;
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

            // A way through from the hallway door to the exit, going round everything solid (what a runner can jump, a
            // block high at most, counts as open)
            bool Passable(Tile t) => WorldLayout.RunHurdle(t) < 2;
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

            // Each straight run at a sprint: a row at a time, at most a column across, jumping a block (layout version 6
            // packs the hall; this is what keeps it passable)
            double weave = 0, jumps = 0;
            foreach (var (c, z0, z1) in L.Straights)
            {
                if (!WorldLayout.RunSprintable(L, c, z0, z1)) Problem($"lane {lane}: the straight at x {c}, z {z0}-{z1} can't be run at a sprint");
                var (w, j) = RunWeave(L, c, z0, z1);
                weave += w;
                jumps += j;
            }

            // Rows of a straight: blocked count (hard props, pits) <= 3 of 5
            int worst = 0, rows = 0, hard = 0, trips = 0, walls = 0, needles = 0, jumpRows = 0;
            for (int s = 0; s < L.ExitS; s++)
            {
                var (cx, cz) = L.Line[s];
                bool crossways = s > 0 && L.Line[s - 1].Z == cz;
                if (crossways) continue;
                int blocked = 0, round = 0, jump = 0;
                for (int k = -2; k <= 2; k++)
                {
                    Tile t = L.At(cx + k, cz);
                    int h = WorldLayout.RunHurdle(t);
                    if (h == 2) round++;
                    if (h == 1) jump++;
                    if (t.Kind == TileKind.Pit || t.Kind == TileKind.Floor && t.Variant != 0 && !WorldLayout.IsWalkThroughProp(t.Variant) && t.Variant != Props.RunShelfFallen)
                        blocked++;
                    if (t.Kind == TileKind.Floor && t.Variant is Props.RunToyCar or Props.RunBoxes or Props.RunCord or Props.RunDebris) trips++;
                }
                if (blocked > 0) hard++;
                if (round >= 3) walls++;
                if (round == 4) needles++;
                if (round + jump == 5 && jump > 0) jumpRows++;
                worst = Math.Max(worst, blocked);
                rows++;
            }
            if (worst > 3 && layout.Version < 6) Problem($"lane {lane}: a row with {worst} of 5 tiles blocked");

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
                $"weave {weave,3} cols + {jumps,2} jumps at best, doors {doors,3}, obstacle rows {hard,3} (3+ to go round {walls,2}, needles {needles,2}, jump-or-weave {jumpRows,2}), worst {worst}, trip props {trips,2}, {ev}{(L.HasSafe ? $", SAFE {L.SafeFrom}-{L.SafeTo}" : "")}{(L.HasHole ? ", hole" : "")} -> {WorldLayout.DisplayNumber(L.Destination)}");
            var (shortest, longest) = layout.Version >= 9 ? (470, 510) : (600, 640);
            if (L.ExitS < shortest || L.ExitS > longest) Problem($"lane {lane}: course length {L.ExitS} outside {shortest}-{longest}");
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

    /// <summary>
    /// The least a runner must do to get down a straight at a sprint (the moves of <see cref="WorldLayout.RunSprintable"/>):
    /// columns crossed and things jumped, a jump counted as half a column.
    /// </summary>
    static (int Columns, int Jumps) RunWeave(WorldLayout.RunLane L, int c, int z0, int z1)
    {
        var leaves = new HashSet<(int, int)>();
        foreach (var e in L.Events)
            if (e.Kind == WorldLayout.RunEventKind.Swing)
                leaves.Add(e.Face switch { ArchPier.East => (e.X + 1, e.Z), ArchPier.West => (e.X - 1, e.Z), ArchPier.North => (e.X, e.Z - 1), _ => (e.X, e.Z + 1) });
        int H(int k, int z) => leaves.Contains((c + k - 2, z)) ? 2 : WorldLayout.RunHurdle(L.At(c + k - 2, z));
        const double Never = 1e9;
        var cost = new double[5];
        var cols = new int[5];
        var jumps = new int[5];
        for (int k = 0; k < 5; k++) { cost[k] = H(k, z0) == 2 ? Never : H(k, z0) * 0.5; jumps[k] = H(k, z0) == 1 ? 1 : 0; }
        for (int z = z0 + 1; z <= z1; z++)
        {
            var next = new double[5];
            var nc = new int[5];
            var nj = new int[5];
            for (int k = 0; k < 5; k++)
            {
                next[k] = Never;
                int h = H(k, z);
                if (h == 2) continue;
                for (int from = Math.Max(0, k - 1); from <= Math.Min(4, k + 1); from++)
                {
                    if (cost[from] >= Never || from != k && H(from, z) == 2 && H(k, z - 1) == 2) continue;
                    double v = cost[from] + Math.Abs(k - from) + (h == 1 && H(k, z - 1) != 1 ? 0.5 : 0);
                    if (v < next[k]) { next[k] = v; nc[k] = cols[from] + Math.Abs(k - from); nj[k] = jumps[from] + (h == 1 && H(k, z - 1) != 1 ? 1 : 0); }
                }
            }
            cost = next; cols = nc; jumps = nj;
        }
        int best = 0;
        for (int k = 1; k < 5; k++) if (cost[k] < cost[best]) best = k;
        return (cols[best], jumps[best]);
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
                        Props.RunRemains => 'r', Props.RunCollapse => t.Stack == 0 ? 'X' : 'x', Props.RunBarricade => t.Stack switch { 0 => 'B', 1 => 'K', _ => 'o' },
                        _ => WorldLayout.IsWalkThroughProp(t.Variant) ? ',' : '?',
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
            // (Layout version 6 packs the hall: at best a runner weaves and jumps at about 0.97 of a sprint, and every
            // barricade or cabinet run into costs a second or so)
            foreach (var (name, leaveAt, mistakes, speed, stallFor) in new (string, double, int, double, double)[]
                     { ("clean sprint", 5, 0, 1.0, 2.5), ("3 mistakes of 2.5 s", 5, 3, 1.0, 2.5), ("5 mistakes", 5, 5, 1.0, 2.5), ("8 mistakes", 5, 8, 1.0, 2.5),
                       ("dawdles 10 s, clean", 10, 0, 1.0, 2.5), ("walking", 5, 0, 0.5, 2.5), ("stops at 200", 5, 0, -1.0, 2.5),
                       ("weaves at 0.97, clean", 5, 0, 0.97, 1), ("weaves at 0.95, 6 bumps of 1 s", 5, 6, 0.95, 1),
                       ("weaves at 0.93, 10 bumps", 5, 10, 0.93, 1), ("weaves at 0.90, 6 bumps", 5, 6, 0.90, 1) })
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
                    if ((int)pos != before && mistakeAt.Remove((int)pos)) stall = stallFor;
                    if (chase.Step(dt, pos)) { result = $"caught at {pos:0} after {t:0.0} s"; break; }
                    if (chase.Loose) minGap = Math.Min(minGap, chase.Gap(pos));
                    if (pos >= L.ExitS) { result = $"escaped in {t:0.0} s, closest {minGap:0.0}"; break; }
                }
                Console.WriteLine($"  {name,-22} {result ?? "still running"}");
            }
        }
    }

    /// <summary>
    /// runfair: how often runners of three kinds get out, over every lane, with the chase as it is (RunChase) and as it was
    /// before 0.514.0 (front at 0.90 / 0.94 of a sprint, no warm-up; trips -0.6 for 0.8 s). A runner here is a pace (a
    /// share of a flat-floor sprint, kept through the weaving and jumping), snags (stopped dead for a second or so on a
    /// barricade, per 100 blocks), trips (slowed for a moment on junk run over), and maybe a false exit opened (2.5 s).
    /// </summary>
    static void RunFair(WorldLayout layout)
    {
        double sprint = RunChase.SprintSpeed;
        const double dt = 0.1;
        var profiles = new (string Name, double Pace0, double Pace1, double Snags, int Trips0, int Trips1, double Fake)[]
        {
            ("good (pace 0.88-0.95, 0.6 snags/100, 2-5 trips)", 0.88, 0.95, 0.6, 2, 5, 0.15),
            ("reasonable (0.82-0.90, 1.2 snags/100, 4-9 trips)", 0.82, 0.90, 1.2, 4, 9, 0.35),
            ("clumsy (0.76-0.84, 2 snags/100, 7-14 trips)", 0.76, 0.84, 2.0, 7, 14, 0.6),
            ("walks half the way (pace 0.5 from 40%)", -1, -1, 0.8, 3, 6, 0.3),
        };
        Console.WriteLine($"layout version {layout.Version}, sprint {sprint:0.00} b/s, Normal setting; 400 runs a lane, all 17 lanes");
        foreach (bool old in new[] { true, false })
        {
            Console.WriteLine(old ? "BEFORE (front 0.90/0.94, no warm-up, trips -0.6 x 0.8 s):" : "AFTER (front 0.78/0.82, 20 s warm-up from -0.12, trips -0.5 x 0.6 s):");
            foreach (var pr in profiles)
            {
                int escaped = 0, runs = 0;
                double timeSum = 0, closeSum = 0;
                var caughtAt = new List<double>();
                for (int lane = 0; lane < WorldLayout.RunLanes; lane++)
                {
                    var L = layout.RunPlan(lane);
                    var rng = new Random(lane * 7919 + 17);
                    for (int k = 0; k < 400; k++)
                    {
                        runs++;
                        var chase = new RunChase(sprint, 1, L.Last, -1, -1, -8);
                        double pace = pr.Pace0 < 0 ? 0.88 : pr.Pace0 + rng.NextDouble() * (pr.Pace1 - pr.Pace0);
                        double leave = 4 + rng.NextDouble() * 3;
                        // Where the snags, trips and the false exit fall
                        var stalls = new SortedDictionary<int, double>();
                        int snags = (int)Math.Round(pr.Snags * L.ExitS / 100 * (0.6 + rng.NextDouble() * 0.8));
                        for (int n = 0; n < snags; n++) stalls[rng.Next(20, L.ExitS - 5)] = 0.6 + rng.NextDouble() * 0.9;
                        var trips = new HashSet<int>();
                        int nt = rng.Next(pr.Trips0, pr.Trips1 + 1);
                        for (int n = 0; n < nt; n++) trips.Add(rng.Next(20, L.ExitS - 5));
                        if (rng.NextDouble() < pr.Fake) stalls[rng.NextDouble() < 0.5 ? L.Middle : L.Last] = 2.5;
                        double tripSlow = old ? 0.6 : 0.5, tripFor = old ? 0.8 : 0.6;
                        double pos = -4, t = 0, stall = 0, slowFor = 0, minGap = 999;
                        double front = -8; bool loose = false; double looseAt = 0, leftAt = -1;
                        bool caught = false;
                        while (t < 400)
                        {
                            t += dt;
                            double v = 0;
                            if (t >= leave)
                            {
                                if (stall > 0) stall -= dt;
                                else
                                {
                                    double p = pr.Pace0 < 0 && pos > 0.4 * L.ExitS ? 0.5 : pace;
                                    if (slowFor > 0) { p *= 1 - tripSlow; slowFor -= dt; }
                                    v = sprint * p;
                                }
                            }
                            int before = (int)pos;
                            pos += v * dt;
                            for (int c = before + 1; c <= (int)pos; c++)
                            {
                                if (stalls.TryGetValue(c, out double st)) stall = st;
                                if (trips.Contains(c)) slowFor = tripFor;
                            }
                            if (old)
                            {
                                // The chase before 0.514.0
                                if (leftAt < 0 && pos > 0) leftAt = t;
                                if (!loose) { loose = t >= 12 || leftAt >= 0 && t - leftAt >= 4; looseAt = t; }
                                else
                                {
                                    double share = front >= L.Last ? 0.94 : 0.90;
                                    if (pos - front > RunChase.Band) share = 1.0;
                                    front += share * sprint * dt;
                                    if (pos - front <= RunChase.CatchGap) caught = true;
                                    minGap = Math.Min(minGap, pos - front);
                                }
                            }
                            else
                            {
                                caught = chase.Step(dt, pos);
                                if (chase.Loose) minGap = Math.Min(minGap, chase.Gap(pos));
                            }
                            if (caught) { caughtAt.Add(pos / L.ExitS); break; }
                            if (pos >= L.ExitS) { escaped++; timeSum += t; closeSum += minGap; break; }
                        }
                    }
                }
                caughtAt.Sort();
                string where = caughtAt.Count > 0 ? $", caught at a median {caughtAt[caughtAt.Count / 2] * 100:0}% of the way" : "";
                Console.WriteLine($"  {pr.Name,-52} escape {100.0 * escaped / runs,5:0.0}%" +
                    (escaped > 0 ? $" (in {timeSum / escaped:0} s, closest {closeSum / escaped:0.0} blocks on average)" : "") + where);
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
