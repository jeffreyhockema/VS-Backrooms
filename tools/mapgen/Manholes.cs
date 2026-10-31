using Backrooms.Worldgen;

/// <summary>
/// <c>mapgen &lt;seed&gt; &lt;cells&gt; manholes [maps]</c>: Level 3's manholes round the level's first arrival, checked the way
/// the game moves a player (EntityBehaviorControlledPhysics: a player is climbing when a climbable block's collision
/// box at the feet or a block above, in the player's own column or a neighbouring one, is within 0.5 of the player's
/// box; while climbing with feet in water no physics module moves them sideways). The blocks are rebuilt here from
/// the tiles as WorldGenerator.BelowFloor and Level3Block lay them, with the collision boxes of the blocktypes
/// (gen_blocktypes.py: manhole, rungs, manholeladder, tunnelstep). For each manhole it measures, for a player 0.6
/// wide and 1.85 tall:
///   drop: the floor area where a player standing at floor height has nothing under them and drops in;
///   caught: of those, how many are then within reach of something to climb (so the fall stops);
///   lock: standing places below with the feet in the water and a hand on the rungs (stuck: cannot step away);
///   top: the highest block of the ladder or rungs below the floor (0 = at the lip, -1 = a block short);
///   foot: the headroom over the foot of the ladder, and whether a dry place out of reach is a walk away;
///   exit: the floor a player at the top of the ladder walks off onto is clear.
/// With <c>maps</c>, the first few are drawn in plan at the floor and at the tunnel.
/// </summary>
static class Manholes
{
    enum Vox { Air, Solid, Water, Rungs, RungsWater, Frame, Ladder, Step }

    const double Half = 0.3, Height = 1.85, Reach = 0.5;
    static WorldLayout L;

    // ---- The blocks under and at the floor of a Level 3 tile (rel 0 = the floor block) ----

    static (Vox Kind, ArchPier Side) At(int x, int rel, int z)
    {
        Tile t = L.TileAt(x, z);
        if (t.Level != 3) return (Vox.Solid, 0);
        if (rel >= 1) return (t.Kind is TileKind.Floor or TileKind.Doorway ? Vox.Air : Vox.Solid, 0);
        if (rel == 0) return t.Under == 2 ? (t.Zone != 0 ? Vox.Ladder : Vox.Frame, t.Pier) : (Vox.Solid, 0);
        if (t.Under == 0 || rel < -5) return (Vox.Solid, 0);
        if (rel == -5) return (Vox.Solid, 0); // clay
        if (t.Under == 2 && t.Zone != 0) return rel == -4 ? (Vox.Solid, 0) : (Vox.Ladder, t.Pier);
        if (t.Under == 1 && t.Zone == WorldLayout.L3TunnelLanding) return (rel is -4 or -1 ? Vox.Solid : Vox.Air, 0);
        if (rel == -4) return (t.Under == 2 ? Vox.RungsWater : t.Under == 1 && t.Zone == WorldLayout.L3TunnelStep ? Vox.Step : Vox.Water, 0);
        if (rel == -1) return (t.Under == 2 ? Vox.Rungs : Vox.Solid, 0);
        return (t.Under == 2 ? Vox.Rungs : Vox.Air, 0);
    }

    static readonly (double, double, double, double, double, double)[] Full = { (0, 0, 0, 1, 1, 1) };
    static readonly (double, double, double, double, double, double)[] StepBox = { (0, 0, 0, 1, 0.5, 1) };
    static readonly (double, double, double, double, double, double)[] RungsBox = { (0.1875, 0, 0, 0.8125, 1, 0.1875) };
    static readonly (double, double, double, double, double, double)[] FrameBoxes =
        { (0, 0, 0, 1, 1, 0.125), (0, 0, 0.875, 1, 1, 1), (0, 0, 0.125, 0.125, 1, 0.875), (0.875, 0, 0.125, 1, 1, 0.875) };

    /// <summary>The vanilla ladder's box, 3 px deep, on the given side of the block.</summary>
    static (double, double, double, double, double, double)[] LadderBox(ArchPier side) => side switch
    {
        ArchPier.North => new[] { (0.0, 0.0, 0.0, 1.0, 1.0, 0.1875) },
        ArchPier.South => new[] { (0.0, 0.0, 0.8125, 1.0, 1.0, 1.0) },
        ArchPier.East => new[] { (0.8125, 0.0, 0.0, 1.0, 1.0, 1.0) },
        _ => new[] { (0.0, 0.0, 0.0, 0.1875, 1.0, 1.0) },
    };

    static (double, double, double, double, double, double)[] Boxes(Vox v, ArchPier side) => v switch
    {
        Vox.Solid => Full,
        Vox.Step => StepBox,
        Vox.Rungs or Vox.RungsWater => RungsBox,
        Vox.Frame => FrameBoxes,
        Vox.Ladder => LadderBox(side),
        _ => System.Array.Empty<(double, double, double, double, double, double)>(),
    };

    static bool Climbable(Vox v) => v is Vox.Rungs or Vox.RungsWater or Vox.Frame or Vox.Ladder;
    static bool Wet(Vox v) => v is Vox.Water or Vox.RungsWater or Vox.Step;

    // ---- A player's box at a position (centre x, z; feet y, in rel units) ----

    static double Dist(double px, double py, double pz, int bx, int by, int bz, (double X1, double Y1, double Z1, double X2, double Y2, double Z2) b)
    {
        double dx = Math.Max(0, Math.Max(bx + b.X1 - (px + Half), px - Half - (bx + b.X2)));
        double dy = Math.Max(0, Math.Max(by + b.Y1 - (py + Height), py - (by + b.Y2)));
        double dz = Math.Max(0, Math.Max(bz + b.Z1 - (pz + Half), pz - Half - (bz + b.Z2)));
        return Math.Sqrt(dx * dx + dy * dy + dz * dz);
    }

    static bool Overlaps(double px, double py, double pz, int bx, int by, int bz, (double X1, double Y1, double Z1, double X2, double Y2, double Z2) b) =>
        px + Half > bx + b.X1 + 1e-9 && px - Half < bx + b.X2 - 1e-9 && py + Height > by + b.Y1 + 1e-9 && py < by + b.Y2 - 1e-9
        && pz + Half > bz + b.Z1 + 1e-9 && pz - Half < bz + b.Z2 - 1e-9;

    /// <summary>Whether the box at this place passes through anything solid.</summary>
    static bool Blocked(double px, double py, double pz)
    {
        for (int bx = (int)Math.Floor(px - Half); bx <= (int)Math.Floor(px + Half); bx++)
            for (int bz = (int)Math.Floor(pz - Half); bz <= (int)Math.Floor(pz + Half); bz++)
                for (int by = (int)Math.Floor(py); by <= (int)Math.Floor(py + Height); by++)
                {
                    var (v, side) = At(bx, by, bz);
                    foreach (var b in Boxes(v, side)) if (Overlaps(px, py, pz, bx, by, bz, b)) return true;
                }
        return false;
    }

    /// <summary>Whether something holds up a player whose feet are at py: a box top at py under their footprint.</summary>
    static bool Supported(double px, double py, double pz)
    {
        int by = (int)Math.Floor(py - 1e-6);
        for (int bx = (int)Math.Floor(px - Half); bx <= (int)Math.Floor(px + Half - 1e-9); bx++)
            for (int bz = (int)Math.Floor(pz - Half); bz <= (int)Math.Floor(pz + Half - 1e-9); bz++)
            {
                var (v, side) = At(bx, by, bz);
                foreach (var b in Boxes(v, side))
                    if (Math.Abs(by + b.Item5 - py) < 1e-6 && px + Half > bx + b.Item1 + 1e-9 && px - Half < bx + b.Item4 - 1e-9
                        && pz + Half > bz + b.Item3 + 1e-9 && pz - Half < bz + b.Item6 - 1e-9) return true;
            }
        return false;
    }

    /// <summary>The game's climbing test (EntityBehaviorControlledPhysics), for a player standing (onGround) or not.</summary>
    static bool Climbing(double px, double py, double pz, bool onGround)
    {
        int cx = (int)Math.Floor(px), cz = (int)Math.Floor(pz), fy = (int)Math.Floor(py);
        double frac = py - fy;
        for (int i = 0; i < 2; i++)
        {
            var (v, side) = At(cx, fy + i, cz);
            if (!Climbable(v)) continue;
            foreach (var b in Boxes(v, side)) if (Dist(px, py, pz, cx, fy + i, cz, b) < Reach) return true;
        }
        foreach (var (dx, dz) in new[] { (0, -1), (1, 0), (0, 1), (-1, 0) })
            for (int i = 0; i < 2; i++)
            {
                var (v, side) = At(cx + dx, fy + i, cz + dz);
                if (!Climbable(v)) continue;
                foreach (var b in Boxes(v, side))
                    if ((b.Item5 > 0.375 + frac || !onGround) && Dist(px, py, pz, cx + dx, fy + i, cz + dz, b) < Reach) return true;
            }
        return false;
    }

    /// <summary>How high the space is over a player's footprint, from the feet at py to the first box above.</summary>
    static double FreeAbove(double px, double py, double pz)
    {
        double free = 9;
        for (int bx = (int)Math.Floor(px - Half); bx <= (int)Math.Floor(px + Half - 1e-9); bx++)
            for (int bz = (int)Math.Floor(pz - Half); bz <= (int)Math.Floor(pz + Half - 1e-9); bz++)
                for (int by = (int)Math.Floor(py); by <= (int)Math.Floor(py) + 4; by++)
                {
                    var (v, side) = At(bx, by, bz);
                    foreach (var b in Boxes(v, side))
                        if (by + b.Item2 >= py - 1e-9 && px + Half > bx + b.Item1 + 1e-9 && px - Half < bx + b.Item4 - 1e-9
                            && pz + Half > bz + b.Item3 + 1e-9 && pz - Half < bz + b.Item6 - 1e-9) free = Math.Min(free, by + b.Item2 - py);
                }
        return free;
    }

    static bool FeetWet(double px, double py, double pz) => Wet(At((int)Math.Floor(px), (int)Math.Floor(py), (int)Math.Floor(pz)).Kind);

    /// <summary>The surface a player stands on in a column, going down from just under y (rel), or null.</summary>
    static double? Ground(double px, double py, double pz)
    {
        for (double y = Math.Floor(py * 16) / 16; y >= -5; y -= 1 / 16.0)
            if (!Blocked(px, y, pz) && Supported(px, y, pz)) return y;
            else if (Blocked(px, y, pz)) return null;
        return null;
    }

    public static void Run(WorldLayout layout, long seed, int cells, bool maps)
    {
        L = layout;
        var a = layout.FindArrival(3, 99991UL);
        if (a == null) { Console.WriteLine("no Level 3 arrival"); return; }
        int amx = WorldLayout.MacroOf(a.Value.X), amz = WorldLayout.MacroOf(a.Value.Z);
        Console.WriteLine($"layout version {layout.Version}, Level 3 manholes within {cells / 2} cells of the arrival at {a.Value}");
        int found = 0, drawn = 0, good = 0, backed = 0;
        double dropSum = 0;
        for (int mz = amz - cells / 2; mz <= amz + cells / 2; mz++)
            for (int mx = amx - cells / 2; mx <= amx + cells / 2; mx++)
            {
                if (layout.LevelAt(mx, mz) != 3) continue;
                var shaft = new List<(int X, int Z)>();
                for (int lz = 0; lz < WorldLayout.MacroSize; lz++)
                    for (int lx = 0; lx < WorldLayout.MacroSize; lx++)
                    {
                        int gx = mx * WorldLayout.MacroSize + lx, gz = mz * WorldLayout.MacroSize + lz;
                        Tile t = layout.TileAt(gx, gz);
                        if (t.Under == 2 && t.Kind != TileKind.Wall) shaft.Add((gx, gz));
                    }
                if (shaft.Count == 0) continue;
                found++;
                var r = Measure(shaft);
                dropSum += r.Drop;
                bool ok = r.Drop >= 0.3 && r.Caught == r.DropN && r.Locks == 0 && r.Top == 0 && r.Headroom >= Height && r.WalkAway && r.Exit;
                if (ok) good++;
                Tile s0 = layout.TileAt(shaft[0].X, shaft[0].Z);
                var (bdx, bdz) = s0.Pier switch { ArchPier.North => (0, 1), ArchPier.South => (0, -1), ArchPier.East => (-1, 0), _ => (1, 0) };
                bool walled = s0.Zone != 0 && shaft.All(p => At(p.X + bdx, 1, p.Z + bdz).Kind == Vox.Solid);
                if (walled) backed++;
                Console.WriteLine($"manhole at {shaft[0].X},{shaft[0].Z} ({shaft.Count} block{(shaft.Count > 1 ? "s" : "")}{(s0.Zone != 0 ? $", ladder {s0.Pier.ToString().ToLowerInvariant()}{(walled ? ", wall behind" : ", open behind")}" : "")}): drop {r.Drop:0.000} m2 " +
                    $"({r.DropW:0.00} x {r.DropD:0.00}), caught {r.Caught}/{r.DropN}, lock {r.Locks}/{r.Below}, top {r.Top}, foot headroom {r.Headroom:0.00}" +
                    $" walk away {(r.WalkAway ? "yes" : "NO")}, exit {(r.Exit ? "clear" : "BLOCKED")}{(ok ? "" : "  <- check")}");
                if (maps && drawn++ < 2) Draw(shaft);
            }
        Console.WriteLine($"{found} manholes, {good} pass every check, {backed} with a wall behind the opening, mean drop area {(found > 0 ? dropSum / found : 0):0.000} m2");
    }

    record Result(double Drop, double DropW, double DropD, int DropN, int Caught, int Locks, int Below, int Top, double Headroom, bool WalkAway, bool Exit);

    static Result Measure(List<(int X, int Z)> shaft)
    {
        int x0 = shaft.Min(s => s.X) - 3, x1 = shaft.Max(s => s.X) + 4, z0 = shaft.Min(s => s.Z) - 3, z1 = shaft.Max(s => s.Z) + 4;
        const double step = 1 / 32.0;
        // At the floor: where a player has nothing under them, and whether that drop is caught half a block down
        int dropN = 0, caught = 0;
        double minX = double.MaxValue, maxX = double.MinValue, minZ = double.MaxValue, maxZ = double.MinValue;
        for (double px = x0 + Half; px <= x1 - Half; px += step)
            for (double pz = z0 + Half; pz <= z1 - Half; pz += step)
            {
                if (Blocked(px, 1, pz) || Supported(px, 1, pz)) continue;
                dropN++;
                (minX, maxX, minZ, maxZ) = (Math.Min(minX, px), Math.Max(maxX, px), Math.Min(minZ, pz), Math.Max(maxZ, pz));
                if (Climbing(px, 0.5, pz, false)) caught++;
            }
        double drop = dropN * step * step;
        // Below: every standing place in the tunnel round the shaft
        int locks = 0, below = 0;
        var dry = new List<(double X, double Y, double Z, bool Reach)>();
        for (double px = x0 + Half; px <= x1 - Half; px += 1 / 16.0)
            for (double pz = z0 + Half; pz <= z1 - Half; pz += 1 / 16.0)
            {
                if (Ground(px, -1 - Height, pz) is not double gy || Blocked(px, gy, pz)) continue;
                below++;
                bool climbing = Climbing(px, gy, pz, true), wet = FeetWet(px, gy, pz);
                if (climbing && wet) locks++;
                if (!wet) dry.Add((px, gy, pz, climbing));
            }
        // The top of the ladder: the highest climbable block in the shaft's columns below the floor
        int top = -9;
        foreach (var (sx, sz) in shaft)
            for (int rel = 0; rel >= -5; rel--)
                if (At(sx, rel, sz).Kind is Vox.Rungs or Vox.RungsWater or Vox.Ladder) { top = Math.Max(top, rel); break; }
        // The foot: the lowest standing place within reach of the ladder, its headroom, and a dry place out of reach
        // joined to it by dry places (steps of at most half a block)
        double headroom = 0;
        bool walkAway = false;
        var foot = dry.Where(d => d.Reach).OrderBy(d => d.Y).FirstOrDefault();
        if (foot != default)
        {
            // The least headroom anywhere a player can stand within reach of the ladder at its foot
            headroom = dry.Where(d => d.Reach && d.Y <= foot.Y + 0.5).Min(d => FreeAbove(d.X, d.Y, d.Z));
            var seen = new HashSet<(double, double)> { (foot.X, foot.Z) };
            var queue = new Queue<(double X, double Y, double Z, bool Reach)>();
            queue.Enqueue(foot);
            var byXZ = dry.ToDictionary(d => (d.X, d.Z));
            while (queue.Count > 0 && !walkAway)
            {
                var c = queue.Dequeue();
                if (!c.Reach) { walkAway = true; break; }
                foreach (var (dx, dz) in new[] { (1 / 16.0, 0.0), (-1 / 16.0, 0.0), (0.0, 1 / 16.0), (0.0, -1 / 16.0) })
                    if (byXZ.TryGetValue((c.X + dx, c.Z + dz), out var n) && Math.Abs(n.Y - c.Y) <= 0.5 && seen.Add((n.X, n.Z))) queue.Enqueue(n);
            }
        }
        // The exit: from the ladder's top, the floor beyond its back (or, with the old frame, the frame itself) is clear
        bool exit = true;
        foreach (var (sx, sz) in shaft)
        {
            Tile t = L.TileAt(sx, sz);
            if (t.Zone == 0) continue; // the old manhole: one climbs out onto its frame
            var (ex, ez) = t.Pier switch { ArchPier.North => (sx, sz - 1), ArchPier.South => (sx, sz + 1), ArchPier.East => (sx + 1, sz), _ => (sx - 1, sz) };
            if (At(ex, 0, ez).Kind != Vox.Solid || At(ex, 1, ez).Kind != Vox.Air || At(ex, 2, ez).Kind != Vox.Air) exit = false;
        }
        return new Result(drop, dropN > 0 ? maxX - minX + 2 * Half : 0, dropN > 0 ? maxZ - minZ + 2 * Half : 0, dropN, caught, locks, below, top, headroom, walkAway, exit);
    }

    /// <summary>Plan of the floor (rel 0-1) and of the tunnel (rel -3/-4) round a manhole.</summary>
    static void Draw(List<(int X, int Z)> shaft)
    {
        int x0 = shaft.Min(s => s.X) - 4, x1 = shaft.Max(s => s.X) + 7, z0 = shaft.Min(s => s.Z) - 3, z1 = shaft.Max(s => s.Z) + 3;
        Console.WriteLine("  floor (# wall, . floor, M manhole frame, L/l ladder top: capital on the ladder's half to the viewer's left)   tunnel (# rock, ~ water, s step, _ landing, = ladder/rungs, R rungs in water)");
        for (int z = z0; z <= z1; z++)
        {
            var top = new System.Text.StringBuilder("  ");
            var under = new System.Text.StringBuilder("    ");
            for (int x = x0; x <= x1; x++)
            {
                Tile t = L.TileAt(x, z);
                var (v0, _) = At(x, 0, z);
                top.Append(v0 == Vox.Frame ? 'M' : v0 == Vox.Ladder ? (t.Zone == WorldLayout.L3ShaftLeft ? 'L' : 'l') : At(x, 1, z).Kind == Vox.Air ? '.' : '#');
                var (v4, _) = At(x, -4, z);
                var (v3, _) = At(x, -3, z);
                under.Append(v3 == Vox.Ladder ? '=' : v4 == Vox.RungsWater ? 'R' : v4 == Vox.Step ? 's' : v4 == Vox.Water ? '~' : v4 == Vox.Solid && v3 == Vox.Air ? '_' : '#');
            }
            Console.WriteLine(top.ToString() + under + $"   z={z}");
        }
        var s0 = L.TileAt(shaft[0].X, shaft[0].Z);
        Console.WriteLine($"  ladder side {(s0.Zone == 0 ? "north (old rungs)" : s0.Pier.ToString().ToLowerInvariant())}, x from {x0}");
    }
}

/// <summary><c>mapgen &lt;seed&gt; &lt;cells&gt; tunnels</c>: from each Level 3 manhole round the arrival, how many tunnel blocks (Under 1 or 2) are joined to it, by flood fill.</summary>
static class Tunnels
{
    public static void Run(WorldLayout layout, int cells)
    {
        var a = layout.FindArrival(3, 99991UL);
        if (a == null) { Console.WriteLine("no Level 3 arrival"); return; }
        int amx = WorldLayout.MacroOf(a.Value.X), amz = WorldLayout.MacroOf(a.Value.Z);
        var lens = new List<int>();
        const int Cap = 5000;
        bool Tun(int x, int z) { var t = layout.TileAt(x, z); return t.Level == 3 && (t.Under == 1 || t.Under == 2); }
        for (int mz = amz - cells / 2; mz <= amz + cells / 2; mz++)
            for (int mx = amx - cells / 2; mx <= amx + cells / 2; mx++)
            {
                if (layout.LevelAt(mx, mz) != 3) continue;
                (int, int)? shaft = null;
                for (int lz = 0; lz < WorldLayout.MacroSize && shaft == null; lz++)
                    for (int lx = 0; lx < WorldLayout.MacroSize; lx++)
                    {
                        int gx = mx * WorldLayout.MacroSize + lx, gz = mz * WorldLayout.MacroSize + lz;
                        var t = layout.TileAt(gx, gz);
                        if (t.Under == 2 && t.Kind != TileKind.Wall) { shaft = (gx, gz); break; }
                    }
                if (shaft is not { } s) continue;
                var seen = new HashSet<(int, int)> { s };
                var q = new Queue<(int, int)>(); q.Enqueue(s);
                while (q.Count > 0 && seen.Count < Cap)
                {
                    var (x, z) = q.Dequeue();
                    foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                        if (Tun(x + dx, z + dz) && seen.Add((x + dx, z + dz))) q.Enqueue((x + dx, z + dz));
                }
                lens.Add(seen.Count);
            }
        lens.Sort();
        Console.WriteLine($"layout version {layout.Version}: {lens.Count} manholes; reachable tunnel blocks min {lens.FirstOrDefault()}, p10 {lens[lens.Count / 10]}, median {lens[lens.Count / 2]}, p90 {lens[lens.Count * 9 / 10]}, max {lens.LastOrDefault()}; under 40: {lens.Count(l => l < 40)}; capped at {Cap}: {lens.Count(l => l >= Cap)}");
    }
}
