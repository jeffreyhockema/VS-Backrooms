using System;
using System.Diagnostics;
using System.Linq;
using System.Text;
using Backrooms.Worldgen;

/// <summary>Level 47's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 47stats: the cells round the glade (how long they take), the share of their tiles in each zone, the walls in the forest,
    /// supply boxes, open ground; the glade, the manor and the trail where they should be; how many trees of each kind, hollow
    /// trees and green giants. 47map [reach]: the forest round the glade as text, one character per 4 blocks (# trunks and
    /// stones, . forest, = trail, ~ water, g glade, M manor, H a hollow, G a green giant's hollow). 47links: the ways in and out.
    /// </summary>
    static bool L47Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "47map") { L47Map(layout, args.Length > 0 && int.TryParse(args[^1], out int r) ? r : 160); return true; }
        if (mode == "47links") { L47Links(layout); return true; }
        if (mode == "47prof") { layout.L47Profile(); return true; }
        if (mode != "47stats") return false;
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        int mx0 = WorldLayout.MacroOf(layout.L47MidX), mz0 = WorldLayout.MacroOf(layout.L47MidZ);
        Console.WriteLine($"glade {layout.L47MidX},{layout.L47MidZ} (cell {mx0},{mz0}); region centre cell {layout.L47CentreX},{layout.L47CentreZ}, radius {layout.L47Radius} cells");
        var zones = new long[10];
        long walls = 0, all = 0, boxes = 0, open = 0, hollows = 0, green = 0;
        int cells = 0;
        var sw = Stopwatch.StartNew();
        for (int mz = mz0 - 12; mz <= mz0 + 12; mz++)
            for (int mx = mx0 - 12; mx <= mx0 + 12; mx++)
            {
                if (layout.LevelAt(mx, mz) != WorldLayout.Level47) continue;
                cells++;
                foreach (Tile t in layout.BuildMacro(mx, mz))
                {
                    all++;
                    zones[Math.Min(9, (int)t.Zone)]++;
                    if (t.Kind == TileKind.Wall && t.Zone == WorldLayout.L47Forest) walls++;
                    if (t.SupplyBox) boxes++;
                    if ((t.Detail & WorldLayout.L47OpenGround) != 0) open++;
                    if (t.Under is Unders.L47DeadHollow or Unders.L47StillHollow) hollows++;
                    if (t.Under == Unders.L47GreenHollow) green++;
                }
            }
        Console.WriteLine($"{cells} cells, {sw.Elapsed.TotalMilliseconds / Math.Max(1, cells):0.0} ms a cell");
        string[] names = { "none", "forest", "trail", "glade", "stream", "manor", "6", "7", "8", "thicket" };
        Console.WriteLine("tiles: " + string.Join(", ", Enumerable.Range(0, 10).Where(z => zones[z] > 0).Select(z => $"{names[z]} {zones[z] * 100.0 / all:0.0}%")));
        long forest = zones[WorldLayout.L47Forest];
        Console.WriteLine($"in the way in the forest: {walls * 100.0 / Math.Max(1, forest):0.0}%; supply boxes {boxes} ({boxes / Math.Max(1.0, cells):0.00} a cell); open ground {open * 100.0 / Math.Max(1, forest):0.0}%; hollow tiles {hollows}, green giants' {green}");
        if (zones[0] > 0) Bad($"{zones[0]} tiles of no zone");
        if (zones[WorldLayout.L47TrailZone] == 0) Bad("no trail");
        if (zones[WorldLayout.L47StreamZone] == 0) Bad("no streams");
        if (open == 0) Bad("no open ground to arrive on");
        Tile hall = layout.TileAt(layout.L47MidX, layout.L47MidZ + 3);
        if (hall.Zone != WorldLayout.L47ManorZone) Bad($"the manor's hall is zone {hall.Zone}");
        Tile door = layout.TileAt(layout.L47MidX, layout.L47MidZ + WorldLayout.L47HouseV);
        if (door.Kind != TileKind.Floor) Bad("the manor's front door is shut");
        // The trail: walk it out from the glade and check it stays clear
        int blocked = 0, samples = 0;
        for (double phi = 0.2; phi < 40; phi += 0.02)
        {
            var (x, z) = layout.L47TrailPoint(phi);
            int ix = (int)Math.Floor(x), iz = (int)Math.Floor(z);
            if (layout.LevelAt(WorldLayout.MacroOf(ix), WorldLayout.MacroOf(iz)) != WorldLayout.Level47) break;
            samples++;
            Tile t = layout.TileAt(ix, iz);
            if (t.Kind == TileKind.Wall && t.Zone != WorldLayout.L47RimZone) blocked++;
        }
        Console.WriteLine($"trail: {samples} points walked, {blocked} in a wall");
        if (blocked > samples / 50) Bad($"the trail is blocked at {blocked} points");
        // Trees by kind round the glade
        var kinds = new int[8];
        int dead = 0, hollow = 0, young = 0;
        for (int j = (layout.L47MidZ - 300) / 12; j <= (layout.L47MidZ + 300) / 12; j++)
            for (int i = (layout.L47MidX - 300) / 12; i <= (layout.L47MidX + 300) / 12; i++)
            {
                var t = layout.L47TreeAt(i, j);
                if (!t.Exists) continue;
                kinds[t.Bark]++;
                if (t.Dead) dead++;
                if (t.Hollow) hollow++;
                if (t.R < 0.9) young++;
            }
        Console.WriteLine($"trees within 300: oak {kinds[1]}, beech {kinds[2]}, fir {kinds[3]}, spruce {kinds[4]}, dead {dead} ({hollow} hollow), young {young}");
        var giants = layout.L47GreenGiants();
        Console.WriteLine($"green giants within 1500: {giants.Count}; nearest {(giants.Count > 0 ? $"{giants[0].X},{giants[0].Z} ({layout.L47FromMid(giants[0].X, giants[0].Z):0} from the glade)" : "none")}");
        if (giants.Count == 0) Bad("no green giants");
        Console.WriteLine(bad == 0 ? "47stats: ok" : $"47stats: {bad} problems");
        return true;
    }

    static void L47Map(WorldLayout layout, int reach)
    {
        const int step = 4;
        var sb = new StringBuilder();
        for (int z = layout.L47MidZ - reach; z <= layout.L47MidZ + reach; z += step)
        {
            for (int x = layout.L47MidX - reach; x <= layout.L47MidX + reach; x += step)
            {
                if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.Level47) { sb.Append(' '); continue; }
                Tile t = layout.TileAt(x, z);
                sb.Append(t.Under switch
                {
                    Unders.L47GreenHollow => 'G',
                    Unders.L47DeadHollow or Unders.L47StillHollow => 'H',
                    _ => t.Zone switch
                    {
                        WorldLayout.L47RimZone => '%',
                        WorldLayout.L47ManorZone => t.Kind == TileKind.Wall ? 'M' : 'm',
                        WorldLayout.L47GladeZone => t.Kind == TileKind.Wall ? 'o' : 'g',
                        WorldLayout.L47StreamZone => '~',
                        WorldLayout.L47TrailZone => '=',
                        _ => t.Kind == TileKind.Wall ? '#' : t.SupplyBox ? 'b' : '.',
                    },
                });
            }
            sb.AppendLine();
        }
        Console.Write(sb.ToString());
    }

    /// <summary>
    /// 47links: Level 47's ways in and out. Level 10's ancient dead trees: how many to a square kilometre of Level 10, the
    /// nearest few to spawn, each laid out with its hollow; in the level: the hollow dead trees near the glade (those that lead
    /// out), the green giants (to Level 23); and that every arrival finder finds somewhere.
    /// </summary>
    static void L47Links(WorldLayout layout)
    {
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
        var spawn = layout.FindSpawn();
        int side = WorldLayout.L47Tree10Square;
        int sx = (int)Math.Floor(spawn.X / (double)side), sz = (int)Math.Floor(spawn.Z / (double)side);
        int squares10 = 0;
        var trees = new System.Collections.Generic.List<WorldLayout.L47Tree10>();
        for (int sj = sz - 14; sj <= sz + 14; sj++)
            for (int si = sx - 14; si <= sx + 14; si++)
            {
                int cx = si * side + side / 2, cz = sj * side + side / 2;
                if (layout.LevelAt(WorldLayout.MacroOf(cx), WorldLayout.MacroOf(cz)) == 10) squares10++;
                var t = layout.L47Tree10In(si, sj);
                if (t.Valid) trees.Add(t);
            }
        double km2 = squares10 * (double)side * side / 1e6;
        Console.WriteLine($"Level 10's ancient dead trees: {trees.Count} in {squares10} squares mostly of Level 10 ({km2:0} km2): {trees.Count / Math.Max(1, km2):0.00} per km2");
        foreach (var t in trees.OrderBy(t => Dist(t.X, t.Z, spawn.X, spawn.Z)).Take(5))
        {
            Tile mid = layout.TileAt(t.X, t.Z);
            if (mid.Level != 10 || mid.Under != Unders.L47Tree10Hollow) Bad($"tree at {t.X},{t.Z}: middle tile level {mid.Level} Under {mid.Under}");
            Console.WriteLine($"  near spawn: Level 10, ancient dead tree (in, one-way), {t.X},{t.Z}, {Dist(t.X, t.Z, spawn.X, spawn.Z) / 1000:0.0} km from spawn");
        }
        if (trees.Count == 0) Bad("no ancient dead trees in Level 10");
        if (trees.Count > 1)
        {
            var nn = trees.Select(a => trees.Where(b => b != a).Min(b => Dist(a.X, a.Z, b.X, b.Z))).OrderBy(d => d).ToList();
            Console.WriteLine($"nearest neighbour: least {nn[0]:0} blocks, median {nn[nn.Count / 2]:0}");
        }
        var hollows = layout.L47HollowTrees();
        int leads = hollows.Count(h => h.Leads);
        Console.WriteLine($"in 47: {hollows.Count} hollow dead trees within 520 of the glade, {leads} leading out to Level 10");
        foreach (var h in hollows.Where(h => h.Leads).OrderBy(h => layout.L47FromMid(h.X, h.Z)).Take(3))
            Console.WriteLine($"  Level 47, dead tree's hollow (out to 10, one-way), {h.X},{h.Z}, {layout.L47FromMid(h.X, h.Z):0} from the glade");
        foreach (var g in layout.L47GreenGiants().Take(3))
            Console.WriteLine($"  Level 47, green giant (out to 23, one-way), {g.X},{g.Z}, {layout.L47FromMid(g.X, g.Z):0} from the glade");
        if (leads == 0) Bad("no hollow leads out");
        // The finders
        for (ulong key = 1; key <= 6; key++)
        {
            var a = layout.L47HollowArrival(key * 7919);
            if (a == null) Bad($"no arrival beside a hollow for key {key}");
            var b = layout.L47Tree10Arrival(key * 7919);
            if (b == null) Bad($"no arrival in Level 10 beside a dead tree for key {key}");
            else if (key == 1) Console.WriteLine($"  arrival in 10 for key 1: {b.Value.X},{b.Value.Z} (level {layout.TileAt(b.Value.X, b.Value.Z).Level})");
            if (a != null && key == 1) Console.WriteLine($"  arrival in 47 for key 1: {a.Value.X},{a.Value.Z}");
        }
        Console.WriteLine(bad == 0 ? "47links: ok" : $"47links: {bad} problems");
    }

    static string L47LinkLabel(Tile t) => t.Under switch
    {
        Unders.L47Tree10Hollow => "ancient dead tree (47)",
        Unders.L47DeadHollow => "dead tree's hollow (to 10)",
        Unders.L47GreenHollow => "green giant's hollow (to 23)",
        _ => null,
    };

    static string L47UseKind(Tile t) => null;
}
