using System;
using System.Diagnostics;
using System.Linq;
using System.Text;
using Backrooms.Worldgen;

/// <summary>Level 23's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 23stats: the region (its cells, how long they take), the share of its tiles in each zone, the special places (the
    /// Heart of Water, Base Seedling, the four ruins: where they are, and that each is its own zone), how many glow rooms
    /// there are and whether every tunnel comes out on open forest floor. 23map: the region as text, one character per 6
    /// blocks (# trunks and tangle, . forest, o glow rooms, = tunnels, S Seedling, R ruins, ~ and h the Heart of Water).
    /// </summary>
    static bool L23Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "23map") { L23Map(layout); return true; }
        if (mode != "23stats") return false;
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }

        int mx0 = WorldLayout.MacroOf(layout.L23MidX), mz0 = WorldLayout.MacroOf(layout.L23MidZ);
        Console.WriteLine($"middle (Heart of Water) {layout.L23MidX},{layout.L23MidZ} (cell {mx0},{mz0})");
        var s = layout.L23SeedlingAt;
        Console.WriteLine($"Base Seedling {s.X},{s.Z} r {s.R}");
        for (int k = 0; k < 4; k++)
        {
            var r = layout.L23RuinAt(k);
            Console.WriteLine($"ruin {(WorldLayout.L23RuinKind)k} {r.X},{r.Z} r {r.R}");
        }

        var zones = new long[10];
        long walls = 0, all = 0, boxes = 0, tents = 0;
        int cells = 0;
        var sw = Stopwatch.StartNew();
        for (int mz = mz0 - 16; mz <= mz0 + 16; mz++)
            for (int mx = mx0 - 16; mx <= mx0 + 16; mx++)
            {
                if (layout.LevelAt(mx, mz) != WorldLayout.Level23) continue;
                cells++;
                foreach (Tile t in layout.BuildMacro(mx, mz))
                {
                    all++;
                    zones[Math.Min(9, (int)t.Zone)]++;
                    if (t.Kind == TileKind.Wall && t.Zone != WorldLayout.L23RimZone) walls++;
                    if (t.SupplyBox) boxes++;
                    if (t.Variant == Props.CampTent) tents++;
                }
            }
        double ms = sw.Elapsed.TotalMilliseconds / Math.Max(1, cells);
        Console.WriteLine($"region: {cells} cells, {ms:0.0} ms a cell");
        string[] names = { "none", "forest", "glow", "tunnel", "seedling", "ruin", "core", "7", "8", "tangle" };
        Console.WriteLine("tiles: " + string.Join(", ", Enumerable.Range(0, 10).Where(z => zones[z] > 0).Select(z => $"{names[z]} {zones[z] * 100.0 / all:0.0}%")));
        long forest = zones[WorldLayout.L23Surface];
        Console.WriteLine($"trunks and roots in the way: {walls * 100.0 / Math.Max(1, forest):0.0}% of the forest's tiles; supply boxes {boxes}; tent tiles {tents}");
        if (zones[0] > 0) Bad($"{zones[0]} tiles of no zone");
        if (zones[WorldLayout.L23Seedling] == 0) Bad("no Base Seedling");
        if (zones[WorldLayout.L23Ruin] == 0) Bad("no ruins");
        if (zones[WorldLayout.L23Core] == 0) Bad("no Heart of Water");
        if (tents != 12) Bad($"{tents} tent tiles, not 12");

        // The special places: their middles are theirs
        void Place(string name, int x, int z, byte zone)
        {
            Tile t = layout.TileAt(x, z);
            if (t.Zone != zone) Bad($"{name} is zone {t.Zone}");
        }
        Place("Base Seedling (by the hollow tree)", s.X, s.Z + 6, WorldLayout.L23Seedling);
        for (int k = 0; k < 4; k++)
        {
            var r = layout.L23RuinAt(k);
            Place($"ruin {k}'s plaza", r.X + 15, r.Z, WorldLayout.L23Ruin);
        }
        Place("the Heart of Water", layout.L23MidX, layout.L23MidZ, WorldLayout.L23Core);

        // The caverns and their tunnels: each tunnel's mouth on open forest floor
        int glow = 0, tunnels = 0, blocked = 0;
        var seen = new System.Collections.Generic.HashSet<(int, int)>();
        for (int z = layout.L23MidZ - 330; z <= layout.L23MidZ + 330; z += 8)
            for (int x = layout.L23MidX - 330; x <= layout.L23MidX + 330; x += 8)
            {
                if (!layout.L23Cave(x, z, out _, out _, out WorldLayout.L23Cavern c) || !seen.Add((c.X, c.Z))) continue;
                if (c.Kind == WorldLayout.L23CaveKind.Glow) glow++;
                for (int m = 0; m < c.Tunnels; m++)
                {
                    tunnels++;
                    WorldLayout.L23Passage p = c.Tunnel(m);
                    int bx = (int)Math.Floor(p.Bx), bz = (int)Math.Floor(p.Bz);
                    Tile t = layout.TileAt(bx, bz);
                    if (t.Kind == TileKind.Wall || t.Zone == WorldLayout.L23RimZone)
                    {
                        blocked++;
                        Console.WriteLine($"  tunnel mouth in a wall at {bx},{bz} ({c.Kind} at {c.X},{c.Z})");
                    }
                }
            }
        Console.WriteLine($"caverns: {seen.Count} ({glow} glow rooms), {tunnels} tunnels, {blocked} mouths in a wall");
        if (glow < 10) Bad($"only {glow} glow rooms");
        if (blocked > tunnels / 10) Bad($"{blocked} tunnel mouths blocked");
        Console.WriteLine(bad == 0 ? "23stats: ok" : $"23stats: {bad} problems");
        return true;
    }

    static void L23Map(WorldLayout layout)
    {
        const int step = 6, reach = 336;
        var sb = new StringBuilder();
        for (int z = layout.L23MidZ - reach; z <= layout.L23MidZ + reach; z += step)
        {
            for (int x = layout.L23MidX - reach; x <= layout.L23MidX + reach; x += step)
            {
                if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.Level23) { sb.Append(' '); continue; }
                Tile t = layout.TileAt(x, z);
                sb.Append(t.Zone switch
                {
                    WorldLayout.L23RimZone => '#',
                    WorldLayout.L23Core => t.Floor == FloorKind.L23Water ? '~' : 'h',
                    WorldLayout.L23Seedling => 'S',
                    WorldLayout.L23Ruin => 'R',
                    WorldLayout.L23Glow => 'o',
                    WorldLayout.L23TunnelZone => '=',
                    _ => t.Kind == TileKind.Wall ? '#' : '.',
                });
            }
            sb.AppendLine();
        }
        Console.Write(sb.ToString());
    }

    static string L23LinkLabel(Tile t) => null;

    static string L23UseKind(Tile t) => null;
}
