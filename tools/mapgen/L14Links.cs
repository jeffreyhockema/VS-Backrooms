using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>Level 14's links harness mode (experimental; this file is the level's own): see <see cref="L14Links"/>.</summary>
static partial class LevelModes
{
    /// <summary>
    /// 14links: Level 14's ways in and out, for the seed and spawn given (SPAWN, default full size; WorldLayout.Level14.Links.cs).
    /// The EMERGENCY EXIT doors in Level 0 nearest spawn (position, facing, distance; the placard beside it) and how many to a km2
    /// of the Lobby; the MEDICAL CENTER doors in Level 15 nearest its middle and how many to a km2 of it; in Level 14, the ways
    /// out of each kind nearest the region's middle (none may be within 200 blocks of it) and how many to a km2. Each nearest
    /// one is gone through (ThresholdNetwork) and where it puts you down printed. BAD lines for anything not as it should be.
    /// </summary>
    static bool L14Links(WorldLayout layout, string[] args)
    {
        long seed = long.Parse(args[0]);
        int smx = int.TryParse(Environment.GetEnvironmentVariable("SPAWN"), out int sp) ? sp : 16000, smz = smx;
        int sx = smx * 32 + 16, sz = smz * 32 + 16;
        var net = new ThresholdNetwork(layout, new WorldGeometry(256), seed);
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        static double D(int x0, int z0, int x1, int z1) => Math.Sqrt((double)(x1 - x0) * (x1 - x0) + (double)(z1 - z0) * (z1 - z0));
        static (int Dx, int Dz) Step(ArchPier p) => p switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
        string Where(Link l)
        {
            int ax = (int)Math.Floor(l.X), az = (int)Math.Floor(l.Z);
            Tile t = layout.TileAt(ax, az);
            string what = t.Level == WorldLayout.Level14 ? WorldLayout.L14ZoneOf(t).ToString() : t.Level == WorldLayout.Level15 ? WorldLayout.L15ZoneOf(t).ToString() : t.Kind.ToString();
            return $"level {t.Level} at {l.X:0.0},{l.Y:0.0},{l.Z:0.0} ({what})";
        }
        void Through(string label, Passage p, int expectLevel, Func<Link, bool> ok)
        {
            if (p == null) { Bad($"{label}: leads nowhere"); return; }
            if (net.Take(p, null) is not { } to) { Bad($"{label}: found nowhere to arrive"); return; }
            int level = layout.TileAt((int)Math.Floor(to.X), (int)Math.Floor(to.Z)).Level;
            bool good = level == expectLevel && ok(to) && !p.TwoWay;
            Console.WriteLine($"    through it: {Where(to)}{(p.TwoWay ? " TWO-WAY" : ", one way")}; message {p.Message}");
            if (!good) Bad($"{label}: not put down where expected");
            if (net.Take(p, null) != to) Bad($"{label}: a second trip leads elsewhere");
        }

        // ---- Level 0: the EMERGENCY EXIT doors ----
        // The Lobby's extent: every cell out to where Level 0 ends (every fourth cell, counted for sixteen)
        int r0 = 0;
        for (int a = 0; a < 72; a++)
        {
            double ang = a * Math.PI * 2 / 72;
            for (int r = 0; r < 4000; r += 2)
                if (layout.LevelAt(smx + (int)Math.Round(Math.Cos(ang) * r), smz + (int)Math.Round(Math.Sin(ang) * r)) == 0) r0 = Math.Max(r0, r);
        }
        r0 += 4;
        long l0Cells = 0;
        var doors0 = new List<(int X, int Z, ArchPier F)>();
        int drawn0 = 0;
        for (int mz = smz - r0; mz <= smz + r0; mz++)
            for (int mx = smx - r0; mx <= smx + r0; mx++)
            {
                if ((mx & 3) == 0 && (mz & 3) == 0 && layout.LevelAt(mx, mz) == 0) l0Cells += 16;
                if (!layout.L14ExitCell(mx, mz)) continue;
                drawn0++;
                if (layout.L14ExitIn(mx, mz) is { } e) doors0.Add(e);
            }
        doors0.Sort((p, q) => D(sx, sz, p.X, p.Z).CompareTo(D(sx, sz, q.X, q.Z)));
        double km0 = l0Cells * 1024.0 / 1e6;
        double nn0 = 0;
        foreach (var p in doors0) { double best = double.MaxValue; foreach (var q in doors0) if (p != q) best = Math.Min(best, D(p.X, p.Z, q.X, q.Z)); nn0 += best; }
        Console.WriteLine($"Level 0 (the Lobby, out to {r0} cells from spawn): {km0:0.0} km2; {drawn0} cells drawn for an EMERGENCY EXIT, {doors0.Count} with a wall for it: "
            + $"{doors0.Count / Math.Max(1e-9, km0):0.00} per km2; mean distance to the next {(doors0.Count > 1 ? nn0 / doors0.Count / 1000 : 0):0.00} km");
        Console.WriteLine("EMERGENCY EXIT doors nearest spawn (Level 0):");
        for (int i = 0; i < Math.Min(5, doors0.Count); i++)
        {
            var (x, z, f) = doors0[i];
            Tile t = layout.TileAt(x, z);
            var (dx, dz) = Step(f);
            Tile front = layout.TileAt(x + dx, z + dz);
            bool placard = false;
            for (int k = -2; k <= 2; k++) placard |= layout.TileAt(x + dx - dz * k, z + dz + dx * k).Under == Unders.L14Placard;
            Console.WriteLine($"  door {x},{z} facing {f}: {D(sx, sz, x, z) / 1000:0.00} km from spawn; front {front.Kind}{(front.Sealed ? " SEALED" : "")}; placard {(placard ? "yes" : "no")}");
            if (t.Kind != TileKind.Wall || !WorldLayout.IsL14ExitDoor(t)) Bad("door not built");
            if (front.Kind != TileKind.Floor || front.Sealed) Bad("nothing to stand on before the door");
            if (layout.ExpVersion >= 12 && !placard) Bad("no placard beside it");
            if (i < 2) Through("EMERGENCY EXIT", net.Used(x, z, "l14-exit", out _), WorldLayout.Level14,
                l => WorldLayout.L14ZoneOf(layout.TileAt((int)Math.Floor(l.X), (int)Math.Floor(l.Z))) == WorldLayout.L14Zone.Reception);
        }
        if (doors0.Count == 0) Bad("no EMERGENCY EXIT door in Level 0");

        // ---- Level 15: the MEDICAL CENTER doors ----
        int c15x = layout.L15CentreX * 32 + 16, c15z = layout.L15CentreZ * 32 + 16;
        int h15x = Hashing.FloorDiv(c15x, WorldLayout.L15Period), h15z = Hashing.FloorDiv(c15z, WorldLayout.L15Period);
        int wings15 = 0, drawn15 = 0;
        var med = new List<(int X, int Z, ArchPier F)>();
        const int n15 = 14;
        for (int j = -n15; j <= n15; j++)
            for (int i = -n15; i <= n15; i++)
            {
                int wx = (h15x + i) * WorldLayout.L15Period + 64, wz = (h15z + j) * WorldLayout.L15Period + 64;
                if (layout.LevelAt(WorldLayout.MacroOf(wx), WorldLayout.MacroOf(wz)) != WorldLayout.Level15) continue;
                wings15++;
                if (layout.L14MedWingDrawn(h15x + i, h15z + j)) drawn15++;
                if (layout.L14MedDoorIn(h15x + i, h15z + j) is { } d && layout.LevelAt(WorldLayout.MacroOf(d.X), WorldLayout.MacroOf(d.Z)) == WorldLayout.Level15) med.Add(d);
            }
        med.Sort((p, q) => D(c15x, c15z, p.X, p.Z).CompareTo(D(c15x, c15z, q.X, q.Z)));
        double km15 = wings15 * (double)WorldLayout.L15Period * WorldLayout.L15Period / 1e6;
        Console.WriteLine($"Level 15 ({2 * n15 + 1}x{2 * n15 + 1} wings round its middle, {wings15} in the level, {km15:0.0} km2): {drawn15} wings drawn for a MEDICAL CENTER door, "
            + $"{med.Count} with a medical bay's wall for it: {med.Count / Math.Max(1e-9, km15):0.00} per km2");
        Console.WriteLine("MEDICAL CENTER doors nearest Level 15's middle (where people arrive):");
        for (int i = 0; i < Math.Min(5, med.Count); i++)
        {
            var (x, z, f) = med[i];
            Tile t = layout.TileAt(x, z);
            var (dx, dz) = Step(f);
            Tile front = layout.TileAt(x + dx, z + dz), back = layout.TileAt(x - dx, z - dz);
            Console.WriteLine($"  door {x},{z} facing {f}: {D(c15x, c15z, x, z):0} blocks from the middle, {D(sx, sz, x, z) / 1000:0.00} km from spawn; "
                + $"front {WorldLayout.L15ZoneOf(front)}, behind {WorldLayout.L15ZoneOf(back)}");
            if (!WorldLayout.IsL14MedDoor(t)) Bad("door not built");
            if (front.Kind != TileKind.Floor) Bad("nothing to stand on before the door");
            if (WorldLayout.L15ZoneOf(front) != WorldLayout.L15Zone.Medical && WorldLayout.L15ZoneOf(back) != WorldLayout.L15Zone.Medical) Bad("not by a medical bay");
            if (i < 2) Through("MEDICAL CENTER", net.Used(x, z, "l14-medical", out _), WorldLayout.Level14,
                l => WorldLayout.L14ZoneOf(layout.TileAt((int)Math.Floor(l.X), (int)Math.Floor(l.Z))) == WorldLayout.L14Zone.Reception);
        }
        if (med.Count == 0) Bad("no MEDICAL CENTER door in Level 15");

        // ---- Level 14: the ways out ----
        var (cx, cz) = layout.L14Middle;
        int hcx = Hashing.FloorDiv(cx, WorldLayout.L14Period), hcz = Hashing.FloorDiv(cz, WorldLayout.L14Period);
        const int n14 = 30;
        int wings14 = 0;
        var outs = new Dictionary<byte, List<(int X, int Z)>> { [1] = new(), [2] = new(), [3] = new() };
        double nearest = double.MaxValue;
        for (int j = -n14; j <= n14; j++)
            for (int i = -n14; i <= n14; i++)
            {
                int wx = (hcx + i) * WorldLayout.L14Period + 34, wz = (hcz + j) * WorldLayout.L14Period + 34;
                if (layout.LevelAt(WorldLayout.MacroOf(wx), WorldLayout.MacroOf(wz)) != WorldLayout.Level14) continue;
                wings14++;
                if (layout.L14WayOutRoll(hcx + i, hcz + j) >= WorldLayout.L14FutureChance + WorldLayout.L14RedChance + WorldLayout.L14CollapseChance) continue;
                var plan = layout.L14PlanOf(hcx + i, hcz + j);
                if (plan.WayOut == 0) continue;
                var (x, z) = plan.World(plan.WayA, plan.WayB);
                outs[plan.WayOut].Add((x, z));
                nearest = Math.Min(nearest, layout.L14FromMiddle(x, z));
            }
        double km14 = wings14 * (double)WorldLayout.L14Period * WorldLayout.L14Period / 1e6;
        Console.WriteLine($"Level 14 ({2 * n14 + 1}x{2 * n14 + 1} wings round its middle {cx},{cz}, {wings14} in the level, {km14:0.0} km2): "
            + $"{outs[1].Count} futuristic doors ({outs[1].Count / Math.Max(1e-9, km14):0.00} per km2), {outs[2].Count} red exit doors ({outs[2].Count / Math.Max(1e-9, km14):0.00}), "
            + $"{outs[3].Count} floors that give way ({outs[3].Count / Math.Max(1e-9, km14):0.00}); nearest any to the middle {nearest:0} blocks");
        if (nearest < WorldLayout.L14WayOutClear) Bad($"a way out within {WorldLayout.L14WayOutClear} blocks of the middle");
        foreach (var (kind, name, use, expect) in new[] { (WorldLayout.L14WayFuture, "futuristic door", "l14-future", WorldLayout.Level15),
                     (WorldLayout.L14WayRed, "red exit door", "l14-red", WorldLayout.RunLevel), (WorldLayout.L14WayCollapse, "floor that gives way", null, WorldLayout.Level73) })
        {
            Console.WriteLine($"{name}s nearest the middle:");
            var near = layout.L14WaysOutNear(kind, cx, cz, 3);
            if (near.Count == 0) Bad($"no {name} near the middle");
            for (int i = 0; i < near.Count; i++)
            {
                var (x, z, f) = near[i];
                Tile t = layout.TileAt(x, z);
                var (dx, dz) = Step(f);
                Tile front = layout.TileAt(x + dx, z + dz);
                string extra;
                if (kind == WorldLayout.L14WayCollapse)
                {
                    int sag = 0, cracks = 0;
                    for (int ez = -3; ez <= 3; ez++)
                        for (int ex = -3; ex <= 3; ex++)
                        {
                            Tile q = layout.TileAt(x + ex, z + ez);
                            if (WorldLayout.IsL14Collapse(q)) sag++;
                            if (WorldLayout.IsL14Cracks(q)) cracks++;
                        }
                    extra = $"{sag} sagging tiles, {cracks} cracked round them (a {WorldLayout.L14ZoneOf(t)}, running {f})";
                    if (sag != 2 || cracks != 10) Bad("the patch is not whole");
                }
                else
                {
                    extra = $"facing {f}, front {WorldLayout.L14ZoneOf(front)} {front.Kind}";
                    bool built = kind == WorldLayout.L14WayFuture ? WorldLayout.IsL14FutureDoor(t) : WorldLayout.IsL14RedDoor(t);
                    if (!built) Bad("door not built");
                    if (front.Kind != TileKind.Floor || front.Variant != 0 && !WorldLayout.IsWalkThroughProp(front.Variant)) Bad("nothing to stand on before the door");
                }
                Console.WriteLine($"  {x},{z}: {layout.L14FromMiddle(x, z):0} blocks from the middle; {extra}");
                if (i > 0) continue;
                Passage p = use != null ? net.Used(x, z, use, out _) : net.Walked(x, z, t, 1.0);
                Through(name, p, expect, kind == WorldLayout.L14WayFuture
                    ? l => { foreach (var (sx2, sz2) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) }) if (layout.TileAt((int)Math.Floor(l.X) + sx2, (int)Math.Floor(l.Z) + sz2).Under == Unders.L15Sealed) return true; return false; }
                    : kind == WorldLayout.L14WayCollapse ? l => l.Y - layout.ArrivalHeight((int)Math.Floor(l.X), (int)Math.Floor(l.Z)) - new WorldGeometry(256).FloorFor(WorldLayout.Level73) > 6 : _ => true);
                if (kind == WorldLayout.L14WayCollapse)
                {
                    // Standing on the cracks round it holds; a step onto the sagging floor does not
                    if (net.Walked(x + (f == ArchPier.South ? 1 : 0), z + (f == ArchPier.East ? 1 : 0), layout.TileAt(x + (f == ArchPier.South ? 1 : 0), z + (f == ArchPier.East ? 1 : 0)), 1.0) != null) Bad("the cracks give way");
                    if (net.Walked(x, z, t, 3.0) != null) Bad("gives way under someone over it");
                }
            }
        }
        // The showcase's spots for the links (WorldLayout.L14LinkShowcaseSpots), with what is under each
        foreach (var s in layout.L14LinkShowcaseSpots(new WorldGeometry(256)))
        {
            Tile t = layout.TileAt((int)Math.Floor(s.X), (int)Math.Floor(s.Z));
            Console.WriteLine($"spot {s.Name} {s.X} {s.Y} {s.Z} h{s.Heading:0} p{s.Pitch:0}  [L{t.Level} {t.Kind} v{t.Variant} under {t.Under}]");
        }
        Console.WriteLine(bad == 0 ? "14links OK" : $"14links: {bad} BAD");
        return true;
    }

    static string L14LinkLabel(Tile t) => WorldLayout.IsL14Collapse(t) ? "floor that gives way (to 73)" : null;

    static string L14UseKind(Tile t) =>
        WorldLayout.IsL14ExitDoor(t) ? "l14-exit" : WorldLayout.IsL14MedDoor(t) ? "l14-medical" : WorldLayout.IsL14FutureDoor(t) ? "l14-future"
        : WorldLayout.IsL14RedDoor(t) ? "l14-red" : null;
}
