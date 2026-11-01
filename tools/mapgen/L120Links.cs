using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>Level 120's links harness mode (experimental; this file is the level's own, beside L120Stats.cs).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 120links: Level 120's ways in and out (WorldLayout.Level120.Links.cs). In Level 4: every door marked SERVER ROOM within
    /// 1200 cells of spawn (found by their hashes, each checked on its built cell), how many to the square kilometre of Level
    /// 4 and of its office blocks, the nearest few to spawn, the spacing between neighbours, and whether each has its placard
    /// (layout 12 on). In Level 120: over the 17 x 17 halls round the region's centre, the share of clusters with a door back
    /// and the hallways with one, and how far the arrivals are from the nearest. Then the thresholds, as ThresholdNetwork
    /// takes them: the nearest SERVER ROOM doors into Level 120 (beside a door back, which leads home again), and doors back
    /// used first (one-way, into Level 4 beside a locked office door).
    /// </summary>
    static bool L120LinksMode(WorldLayout layout, string[] args)
    {
        long seed = long.Parse(args[0]);
        int smx = int.TryParse(Environment.GetEnvironmentVariable("SPAWN"), out int sc) ? sc : 16000, smz = smx;
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        double sx = smx * 32 + 16, sz = smz * 32 + 16;

        // ---- Level 4: the doors marked SERVER ROOM
        const int reach = 1200;
        long l4 = 0, office = 0;
        var doors = new List<(int X, int Z, int OutX, int OutZ, double D)>();
        int unbuilt = 0;
        for (int mz = smz - reach; mz <= smz + reach; mz++)
            for (int mx = smx - reach; mx <= smx + reach; mx++)
            {
                // (Level 4's area, counted on every other cell each way)
                if ((mx & 1) == 0 && (mz & 1) == 0 && layout.LevelAt(mx, mz) == 4)
                {
                    l4 += 4;
                    if (layout.L120IsOfficeCell(mx, mz)) office += 4;
                }
                if (layout.L120ServerDoorOf(mx, mz) is not { } d) continue;
                if (!WorldLayout.IsL120ServerDoor(layout.TileAt(d.X, d.Z))) { unbuilt++; continue; }
                doors.Add((d.X, d.Z, d.OutX, d.OutZ, Math.Sqrt((d.X - sx) * (d.X - sx) + (d.Z - sz) * (d.Z - sz))));
            }
        doors.Sort((a, b) => a.D.CompareTo(b.D));
        double km2 = l4 * 1024 / 1e6, officeKm2 = office * 1024 / 1e6;
        Console.WriteLine($"Level 4 within {reach} cells of spawn: about {km2:0.0} km2 ({officeKm2:0.0} km2 of office blocks)");
        Console.WriteLine($"SERVER ROOM doors: {doors.Count} ({doors.Count / Math.Max(0.01, km2):0.00} per km2 of Level 4, {doors.Count / Math.Max(0.01, officeKm2):0.00} per km2 of offices); "
            + $"{unbuilt} rolled but not built (the room's doorway not as the plan had it)");
        int placards = 0;
        foreach (var d in doors)
        {
            bool has = false;
            for (int dz = -3; dz <= 3 && !has; dz++)
                for (int dx = -3; dx <= 3 && !has; dx++)
                    has = layout.TileAt(d.X + dx, d.Z + dz).Under == Unders.L120Placard;
            if (has) placards++;
        }
        Console.WriteLine($"  with a placard beside them: {placards}/{doors.Count}" + (layout.Version >= 12 ? "" : " (layout before 12: none expected)"));
        if (doors.Count > 0)
        {
            var spacing = new List<double>();
            foreach (var a in doors)
            {
                double best = double.MaxValue;
                foreach (var b in doors)
                    if (a != b) best = Math.Min(best, Math.Sqrt((double)(a.X - b.X) * (a.X - b.X) + (double)(a.Z - b.Z) * (a.Z - b.Z)));
                if (best < double.MaxValue) spacing.Add(best);
            }
            spacing.Sort();
            if (spacing.Count > 0)
                Console.WriteLine($"  nearest neighbour: median {spacing[spacing.Count / 2]:0} blocks, least {spacing[0]:0}");
            Console.WriteLine("  nearest to spawn (door x z, the corridor in front, distance in blocks):");
            foreach (var d in doors.Take(5)) Console.WriteLine($"    L4 SERVER ROOM door {d.X} {d.Z}, front {d.OutX} {d.OutZ}, {d.D:0}");
        }
        else Bad("no SERVER ROOM doors");

        // ---- Level 120: the doors back
        const int P = WorldLayout.L120Period;
        var (chx, chz) = WorldLayout.L120HallOf(layout.L120CentreX * 32 + 16, layout.L120CentreZ * 32 + 16);
        int clusters = 0, clusterExits = 0, hallways = 0, hallwayExits = 0;
        var exits = new List<(int X, int Z, int FrontX, int FrontZ)>();
        for (int hz = chz - 8; hz <= chz + 8; hz++)
            for (int hx = chx - 8; hx <= chx + 8; hx++)
            {
                WorldLayout.L120HallKind kind = layout.L120KindOf(hx, hz);
                if (kind == WorldLayout.L120HallKind.Void) continue;
                var mine = layout.L120ExitDoorsOf(hx, hz);
                if (kind == WorldLayout.L120HallKind.Hallway) { hallways++; if (mine.Count > 0) hallwayExits++; }
                else { clusters++; if (mine.Count > 0) clusterExits++; }
                foreach (var e in mine)
                {
                    Tile t = layout.TileAt(e.X, e.Z), f = layout.TileAt(e.FrontX, e.FrontZ);
                    if (!WorldLayout.IsL120ExitDoor(t) || f.Kind != TileKind.Floor) Bad($"door back at {e.X} {e.Z} not built, or no floor in front");
                    else if (kind == WorldLayout.L120HallKind.Cluster) exits.Add(e);
                }
            }
        Console.WriteLine($"Level 120, 17 x 17 halls round the centre: {clusterExits}/{clusters} clusters with a door back ({100.0 * clusterExits / Math.Max(1, clusters):0}%), {hallwayExits}/{hallways} Pitch-Black Hallways");
        if (hallwayExits < hallways) Bad("a hallway without its door");
        if (layout.L120NearestPocket(chx, chz, WorldLayout.L120HallKind.Hallway, 12) is { } nh)
            foreach (var e in layout.L120ExitDoorsOf(nh.Hx, nh.Hz))
                Console.WriteLine($"    the nearest hallway's door back {e.X} {e.Z}, front {e.FrontX} {e.FrontZ}");
        // How far an arrival in the level is from the nearest door back (straight line)
        var far = new List<double>();
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level120, key * 7919UL) is not { } a) continue;
            double best = double.MaxValue;
            var (ahx, ahz) = WorldLayout.L120HallOf(a.X, a.Z);
            for (int r = 0; r <= 6 && best == double.MaxValue; r++)
                for (int dz = -r; dz <= r; dz++)
                    for (int dx = -r; dx <= r; dx++)
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) == r && layout.L120KindOf(ahx + dx, ahz + dz) == WorldLayout.L120HallKind.Cluster)
                            foreach (var e in layout.L120ExitDoorsOf(ahx + dx, ahz + dz))
                                best = Math.Min(best, Math.Sqrt((double)(e.X - a.X) * (e.X - a.X) + (double)(e.Z - a.Z) * (e.Z - a.Z)));
            if (best < double.MaxValue) far.Add(best);
        }
        far.Sort();
        if (far.Count > 0) Console.WriteLine($"  arrivals to the nearest door back (60 arrivals, straight line): median {far[far.Count / 2]:0}, most {far[^1]:0} blocks");
        exits.Sort((a, b) => Math.Abs(a.X - layout.L120CentreX * 32).CompareTo(Math.Abs(b.X - layout.L120CentreX * 32)));
        foreach (var e in exits.Take(3)) Console.WriteLine($"    L120 door back {e.X} {e.Z}, front {e.FrontX} {e.FrontZ}");

        // ---- The thresholds
        var net = new ThresholdNetwork(layout, new WorldGeometry(256), seed);
        foreach (var d in doors.Take(4))
        {
            Passage p = net.Used(d.X, d.Z, "l120-serverroom", out string refusal);
            if (p == null) { Bad($"SERVER ROOM door at {d.X} {d.Z} leads nowhere ({refusal})"); continue; }
            var home = new Link(d.OutX + 0.5, 1000, d.OutZ + 0.5, false);
            if (net.Take(p, home) is not { } to) { Bad($"SERVER ROOM door at {d.X} {d.Z}: no arrival"); continue; }
            int ax = (int)Math.Floor(to.X), az = (int)Math.Floor(to.Z);
            Tile at = layout.TileAt(ax, az);
            var back = layout.FeatureBeside(ax, az, t => WorldLayout.IsL120ExitDoor(t));
            string line = $"  L4 SERVER ROOM door {d.X} {d.Z} -> L{at.Level} {ax} {az}" + (to.Marker ? " (thin spot)" : "");
            if (at.Level != WorldLayout.Level120) Bad(line + ": not in Level 120");
            if (back is not { } bd) { Bad(line + ": no door back beside the arrival"); continue; }
            Passage q = net.Used(bd.X, bd.Z, "l120-door", out _);
            Link? again = q == null ? null : net.Take(q, null);
            line += $", beside the door back {bd.X} {bd.Z}, which leads " + (again == home ? "home (beside the SERVER ROOM door)" : $"to {again?.ToString() ?? "nowhere"}: NOT home");
            if (again != home) Bad(line); else Console.WriteLine(line);
            if (net.Take(p, home) != to) Bad("the SERVER ROOM door does not lead to the same place again");
        }
        int oneWay = 0;
        foreach (var e in exits)
        {
            if (oneWay >= 4) break;
            if (net.TryGet((e.X, e.Z), out _)) continue; // (already a way back)
            Passage q = net.Used(e.X, e.Z, "l120-door", out string refusal);
            if (q == null) { Bad($"door back at {e.X} {e.Z} leads nowhere ({refusal})"); continue; }
            if (q.TwoWay) Bad($"door back at {e.X} {e.Z} is two-way");
            if (net.Take(q, null) is not { } to) { Bad($"door back at {e.X} {e.Z}: no arrival"); continue; }
            int ax = (int)Math.Floor(to.X), az = (int)Math.Floor(to.Z);
            Tile at = layout.TileAt(ax, az);
            bool besideOffice = layout.FeatureBeside(ax, az, t => t.Kind == TileKind.Door && t.Under == 0 && t.Pattern != WallPattern.Elevator) != null;
            string line = $"  L120 door back {e.X} {e.Z} -> L{at.Level} {ax} {az}" + (besideOffice ? ", beside a locked office door" : ", in the open");
            if (at.Level != 4) Bad(line + ": not in Level 4"); else Console.WriteLine(line);
            oneWay++;
        }
        // The showcase's spots at the ways in and out
        foreach (var s in Backrooms.Cheats.Showcase.For(WorldLayout.Level120, layout, new WorldGeometry(256)))
            if (s.Name is "serverroom-door" or "door-back" or "hallway-door")
                Console.WriteLine($"  showcase {s.Name}: {s.X:0.0} {s.Y:0.0} {s.Z:0.0} heading {s.Heading:0}, the tile there L{layout.TileAt((int)Math.Floor(s.X), (int)Math.Floor(s.Z)).Level}");
        Console.WriteLine(bad == 0 ? "120links: OK" : $"120links: {bad} problem(s)");
        return true;
    }
}
