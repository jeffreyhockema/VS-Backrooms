using System;
using System.Collections.Generic;
using System.IO;
using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.L36Zone;

/// <summary>
/// Level 36's harness modes (experimental; this file is the level's own):
/// <c>36stats [superblocks]</c> lays out the landside and a square of superblocks east of it round the centre line and
/// reports each zone's share, the superblocks' kinds, the gates (and C32s), the Travel Planner's spots, and how much of the
/// walkable floor can be walked to from a carousel (the cabins and bridges are sealed on purpose: reached by boarding);
/// <c>36map [width height]</c> (blocks, from the baggage wall, centred on the centre line) writes l36map.bin (int width,
/// int height, then per tile: zone, kind, material bits, prop/overhead flags) for render_36.py.
/// </summary>
static partial class LevelModes
{
    static bool L36Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "36stats") { L36Stats(layout, args.Length > 3 ? int.Parse(args[3]) : 3); return true; }
        if (mode == "36map") { L36Map(layout, args.Length > 3 ? int.Parse(args[3]) : 1100, args.Length > 4 ? int.Parse(args[4]) : 1100); return true; }
        return false;
    }

    static string L36LinkLabel(Tile t) => null;

    static string L36UseKind(Tile t) => null;

    static void L36Map(WorldLayout layout, int w, int h)
    {
        int x0 = layout.L36WallX - 8, z0 = layout.L36LineZ - h / 2;
        using var f = new BinaryWriter(File.Create("l36map.bin"));
        f.Write(w);
        f.Write(h);
        for (int z = 0; z < h; z++)
            for (int x = 0; x < w; x++)
            {
                Tile t = layout.TileAt(x0 + x, z0 + z);
                bool ours = layout.LevelAt(WorldLayout.MacroOf(x0 + x), WorldLayout.MacroOf(z0 + z)) == WorldLayout.Level36;
                f.Write((byte)(ours ? t.Zone : 255));
                f.Write((byte)t.Kind);
                f.Write(t.Detail);
                f.Write((byte)((t.Variant != 0 ? 1 : 0) | (t.Overhead != 0 ? 2 : 0) | (t.SupplyBox ? 4 : 0) | (t.Ceiling is CeilingKind.LightOn ? 8 : 0)));
            }
        Console.WriteLine($"wrote l36map.bin: {w} x {h} from {x0},{z0}");
    }

    static void L36Stats(WorldLayout layout, int n)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        int x0 = layout.L36WallX, x1 = x0 + WorldLayout.L36Airside + n * WorldLayout.L36Period - 1;
        int z0 = layout.L36LineZ - n * WorldLayout.L36Period / 2, z1 = z0 + n * WorldLayout.L36Period - 1;
        int w = x1 - x0 + 1, h = z1 - z0 + 1;
        var zones = new long[32];
        long walk = 0, cabin = 0, dark = 0, limit = 0, boxes = 0;
        var tiles = new Tile[w * h];
        for (int z = 0; z < h; z++)
            for (int x = 0; x < w; x++)
            {
                Tile t = tiles[x + z * w] = layout.TileAt(x0 + x, z0 + z);
                zones[t.Kind == TileKind.Floor ? t.Zone : (byte)Zone.Wall]++;
                if (t.Kind != TileKind.Floor) continue;
                walk++;
                if (t.Zone is (byte)Zone.Cabin or (byte)Zone.Bridge) cabin++;
                if (WorldLayout.L36IsDark(t)) dark++;
                if ((t.Detail & WorldLayout.L36LimitBit) != 0) limit++;
                if (t.SupplyBox) boxes++;
            }
        Console.WriteLine($"Level 36: landside and {n} x {n} superblocks round the centre line ({w} x {h} blocks from {x0},{z0}); {sw.ElapsedMilliseconds} ms");
        foreach (Zone zone in Enum.GetValues<Zone>())
            if (zones[(int)zone] > 0) Console.WriteLine($"  {zone,-10} {100.0 * zones[(int)zone] / tiles.Length,5:0.0}%");
        Console.WriteLine($"  floor {walk}: blackout {dark}, Absolute Limit {limit}, supply boxes {boxes}, cabins and bridges {cabin}");
        var kinds = new Dictionary<WorldLayout.L36Kind, int>();
        int gates = 0, c32 = 0;
        for (int sz = -n / 2; sz < n - n / 2; sz++)
            for (int sx = 0; sx < n; sx++)
            {
                var k = layout.L36KindOf(sx, sz);
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
                if (k != WorldLayout.L36Kind.Pier) continue;
                var plan = layout.L36PlanOf(sx, sz);
                gates += plan.Gates.Count;
                foreach (var g in plan.Gates) if (g.SupportGroup) c32++;
            }
        Console.WriteLine("  superblocks: " + string.Join(", ", kinds) + $"; gates {gates}, C32 {c32}");
        int sites = 0;
        for (int mz = WorldLayout.MacroOf(z0); mz <= WorldLayout.MacroOf(z1); mz++)
            for (int mx = WorldLayout.MacroOf(x0); mx <= WorldLayout.MacroOf(x1); mx++)
                if (layout.WandererSite(mx, mz) is { } s && layout.IsEntitySpot(s.X, s.Z)) sites++;
        Console.WriteLine($"  Travel Planner spots (standable): {sites}");
        // Reach: from a carousel near the centre line, over walkable floor (props that block not counted as walls)
        int sx0 = 8, sz0 = h / 2;
        while (sz0 < h && tiles[sx0 + sz0 * w].Kind != TileKind.Floor) sz0++;
        var seen = new bool[w * h];
        var q = new Queue<int>();
        q.Enqueue(sx0 + sz0 * w);
        seen[sx0 + sz0 * w] = true;
        long reached = 0;
        while (q.Count > 0)
        {
            int i = q.Dequeue();
            reached++;
            int x = i % w, z = i / w;
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= w || nz >= h) continue;
                int j = nx + nz * w;
                if (seen[j] || tiles[j].Kind != TileKind.Floor) continue;
                seen[j] = true;
                q.Enqueue(j);
            }
        }
        long sealedOther = 0;
        var byZone = new Dictionary<Zone, long>();
        var sample = new Dictionary<Zone, (int, int)>();
        for (int i = 0; i < tiles.Length; i++)
            if (tiles[i].Kind == TileKind.Floor && !seen[i] && tiles[i].Zone is not ((byte)Zone.Cabin or (byte)Zone.Bridge))
            {
                sealedOther++;
                byZone[(Zone)tiles[i].Zone] = byZone.GetValueOrDefault((Zone)tiles[i].Zone) + 1;
                sample.TryAdd((Zone)tiles[i].Zone, (x0 + i % w, z0 + i / w));
            }
        Console.WriteLine($"  reached from a carousel: {reached} of {walk} floor tiles; not reached (not cabins): {sealedOther} " + string.Join(", ", byZone) + "; e.g. " + string.Join(", ", sample));
    }
}
