using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>
/// The Hub's harness modes (this file is the level's own; see docs/design/new-levels/CONTRACT.md):
/// <list type="bullet">
/// <item><c>hubstats</c>: the whole region laid out: what its tiles are, its level doors (one per level, canon's three in
/// their tunnels), whether every tunnel can be walked to from the roundabout, and where every carved door leads.</item>
/// <item><c>hubmap [step]</c>: the region to hubmap.bin (a byte per tile, see <see cref="Code"/>) for render_hub.py.</item>
/// <item><c>hubentrances [cells]</c>: the Hub's doors in Levels 1 and 2 and Level 37's asphalt corridors in a sample.</item>
/// <item><c>hubvault x z [r]</c>: the tiles and the rounded roof (layout version 9, <see cref="WorldLayout.HubVault"/>) of the
/// square of radius r (default 40) round x, z to hubvault.bin, for render_hubvault.py (a slice across a tunnel, the roof
/// from below, a view down a tunnel).</item>
/// </list>
/// </summary>
static partial class LevelModes
{
    const int HubSpan = 60 * 32 + 32;

    static bool HubModes(WorldLayout layout, string mode, string[] args)
    {
        switch (mode)
        {
            case "hubstats": HubStats(layout); return true;
            case "hubmap": HubMap(layout, args.Length > 3 ? int.Parse(args[3]) : 1); return true;
            case "hubentrances": HubEntrances(layout, args.Length > 3 ? int.Parse(args[3]) : 400); return true;
            case "hubvault": HubVaultDump(layout, int.Parse(args[3]), int.Parse(args[4]), args.Length > 5 ? int.Parse(args[5]) : 40); return true;
            case "hubtile":
            {
                int x = int.Parse(args[3]), z = int.Parse(args[4]);
                for (int dz = -2; dz <= 2; dz++)
                {
                    var line = new System.Text.StringBuilder();
                    for (int dx = -3; dx <= 3; dx++) { Tile t = layout.TileAt(x + dx, z + dz); line.Append($"{t.Kind,-6}{(int)t.Pattern,4}/{t.Detail,-3}{t.Stack} "); }
                    Console.WriteLine(line);
                }
                return true;
            }
        }
        return false;
    }

    /// <summary>
    /// hubvault.bin: "HUBV", then x0, z0, size (ints), then per column (rows of z, x along each) 21 bytes: the tile's Kind,
    /// Floor, Height, Overhead, Detail, Depth, Pier, Pattern, Under, whether a tunnel holds it (the vault), the five vault cells
    /// (rel HubVaultFrom to HubVaultTop: 0 air, 1 solid, else a piece index), their facings, and the tile's Zone.
    /// </summary>
    static void HubVaultDump(WorldLayout layout, int x, int z, int r)
    {
        int size = 2 * r + 1, x0 = x - r, z0 = z - r, n = WorldLayout.HubVaultTop - WorldLayout.HubVaultFrom + 1;
        var cells = new byte[n];
        var dirs = new ArchPier[n];
        using var f = new BinaryWriter(File.Create("hubvault.bin"));
        f.Write("HUBV"u8.ToArray());
        f.Write(x0);
        f.Write(z0);
        f.Write(size);
        int vaulted = 0, towerZone = 0;
        var pieces = new int[WorldLayout.HubVaultPieces.Length];
        for (int dz = 0; dz < size; dz++)
            for (int dx = 0; dx < size; dx++)
            {
                Tile t = layout.TileAt(x0 + dx, z0 + dz);
                bool v = t.Kind is TileKind.Floor or TileKind.Pit && layout.HubVault(x0 + dx, z0 + dz, cells, dirs);
                if (!v) { Array.Clear(cells); Array.Clear(dirs); }
                else
                {
                    vaulted++;
                    foreach (byte c in cells) pieces[c]++;
                }
                f.Write(new[] { (byte)t.Kind, (byte)t.Floor, t.Height, t.Overhead, t.Detail, t.Depth, (byte)t.Pier, (byte)t.Pattern, t.Under, (byte)(v ? 1 : 0) });
                f.Write(cells);
                foreach (ArchPier d in dirs) f.Write((byte)d);
                f.Write(t.Zone);
                if (v && t.Zone is WorldLayout.HubZoneTower or WorldLayout.HubZoneVoid && t.Height > WorldLayout.HubSideHeight) towerZone++;
            }
        Console.WriteLine($"hubvault.bin: {size}x{size} from {x0},{z0}; {vaulted} vaulted columns (the Tower's middle is at {layout.HubOriginX},{layout.HubOriginZ}); {towerZone} of them in the Tower's zone, built as the Tower before layout version 9");
        for (int p = 0; p < pieces.Length; p++)
            if (pieces[p] > 0) Console.WriteLine($"  {(p == 0 ? "air" : p == 1 ? "solid" : WorldLayout.HubVaultPieces[p]),-6} {pieces[p]}");
    }

    /// <summary>A tile as a byte: 0 solid, 1 wall face, 2 road, 3 stud, 4 sidewalk, 5 marble, 6 carved door (dead), 7 live door, 8 service door,
    /// 9 ornate door, 10 hole, 11 false wall, 12 tiled end, 13 tile, 14 lamp, 15 dead lamp, 16 stencil, 17 plaque, 18 fan/signal,
    /// 19 give-way line (layout version 11; the middle line is 3, with the studs).</summary>
    static byte Code(in Tile t, bool face)
    {
        switch (t.Kind)
        {
            case TileKind.Pit: return 10;
            case TileKind.Door:
                return t.Pattern switch
                {
                    WallPattern.HubDoor => WorldLayout.HubSigilLevel(t.Detail) >= 0 ? (byte)7 : (byte)6,
                    WallPattern.HubServiceDoor => 8,
                    WallPattern.HubOrnate => 9,
                    _ => 6,
                };
            case TileKind.Floor:
                if (t.Under == Unders.HubFalseWall) return 11;
                switch (t.Detail)
                {
                    case WorldLayout.HubWallLamp: return 14;
                    case WorldLayout.HubWallDeadLamp: return 15;
                    case WorldLayout.HubWallStencil: return 16;
                    case WorldLayout.HubWallPlaque or WorldLayout.HubWallBanner or WorldLayout.HubWallCabinet: return 17;
                }
                if (t.Variant != 0) return 17;
                if (t.Zone == WorldLayout.HubZoneVoid) return t.Under == Unders.HubTowerVoid ? (byte)10 : (byte)5;
                if (t.Under == Unders.HubTileEnd) return 12;
                if (t.Overhead != 0) return 18;
                return t.Floor switch
                {
                    FloorKind.HubStud or FloorKind.HubLine => 3,
                    FloorKind.HubGiveWay => 19,
                    FloorKind.HubSidewalk => 4,
                    FloorKind.HubMarble => 5,
                    FloorKind.PoolTile => 13,
                    _ => 2,
                };
        }
        if (t.Pattern == WallPattern.PoolTile) return 13;
        return face ? (byte)1 : (byte)0;
    }

    static (int X0, int Z0, byte[] Map) HubRegion(WorldLayout layout)
    {
        int cx = WorldLayout.MacroOf(layout.HubOriginX), cz = WorldLayout.MacroOf(layout.HubOriginZ);
        int cells = 2 * 61 + 1, size = cells * 32;
        int x0 = (cx - 61) * 32, z0 = (cz - 61) * 32;
        var map = new byte[size * size];
        var sw = System.Diagnostics.Stopwatch.StartNew();
        int built = 0;
        for (int mz = 0; mz < cells; mz++)
            for (int mx = 0; mx < cells; mx++)
            {
                int gmx = cx - 61 + mx, gmz = cz - 61 + mz;
                if (layout.LevelAt(gmx, gmz) != WorldLayout.Hub) continue;
                Tile[] cell = layout.BuildMacro(gmx, gmz);
                built++;
                for (int i = 0; i < cell.Length; i++) map[(mz * 32 + i / 32) * size + mx * 32 + i % 32] = Code(cell[i], false);
            }
        Console.WriteLine($"The Hub: {built} cells laid out in {sw.ElapsedMilliseconds} ms ({sw.ElapsedMilliseconds / (double)Math.Max(1, built):0.00} ms a cell, the plan included)");
        // Wall faces: solid next to anything open
        bool Open(byte c) => c is >= 2 and <= 5 or >= 10 and <= 12 or >= 18;
        for (int z = 1; z < size - 1; z++)
            for (int x = 1; x < size - 1; x++)
            {
                int i = z * size + x;
                if (map[i] == 0 && (Open(map[i + 1]) || Open(map[i - 1]) || Open(map[i + size]) || Open(map[i - size]))) map[i] = 1;
            }
        return (x0, z0, map);
    }

    static void HubStats(WorldLayout layout)
    {
        var (x0, z0, map) = HubRegion(layout);
        Console.WriteLine("plan: " + layout.HubPlanSummary());
        int size = (int)Math.Sqrt(map.Length);
        var counts = new int[20];
        foreach (byte b in map) counts[b]++;
        string[] names = { "solid", "wall face", "road", "stud", "sidewalk", "marble", "dead door tile", "level door tile", "service door", "ornate door tile",
            "hole tile", "false wall tile", "tiled end", "tile", "lamp", "dead lamp", "stencil", "plaque", "overhead", "give-way line" };
        for (int i = 0; i < names.Length; i++) Console.WriteLine($"  {names[i],-16} {counts[i],9}");

        // Walk from the roundabout over everything that can be walked
        bool Walk(byte c) => c is 2 or 3 or 4 or 5 or 11 or 12 or 18 or 19;
        var seen = new bool[map.Length];
        var queue = new Queue<int>();
        int ox = layout.HubOriginX - x0, oz = layout.HubOriginZ - z0;
        for (int r = 0; r < 80 && queue.Count == 0; r++)
            for (int dz = -r; dz <= r && queue.Count == 0; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    int i = (oz + dz) * size + ox + dx;
                    if (Walk(map[i]) && Math.Abs(dx) + Math.Abs(dz) > WorldLayout.HubTowerRadius + 10) { seen[i] = true; queue.Enqueue(i); break; }
                }
        while (queue.Count > 0)
        {
            int i = queue.Dequeue(), x = i % size, z = i / size;
            foreach (int n in new[] { i + 1, i - 1, i + size, i - size })
            {
                if (n < 0 || n >= map.Length || seen[n] || !Walk(map[n])) continue;
                if (Math.Abs(n % size - x) > 1) continue;
                seen[n] = true;
                queue.Enqueue(n);
            }
        }
        int walkable = 0, reached = 0;
        for (int i = 0; i < map.Length; i++)
            if (Walk(map[i])) { walkable++; if (seen[i]) reached++; }
        Console.WriteLine($"walkable tiles {walkable}, reached from the roundabout {reached} ({100.0 * reached / Math.Max(1, walkable):0.00}%)");

        // The level doors: one per level, where, and can the floor in front of each be walked to
        var geometry = new WorldGeometry(256);
        var net = new ThresholdNetwork(layout, geometry, 12345);
        int[] levels = { 0, 1, 2, 3, 4, 5, 6, WorldLayout.HubSnackroomsDoor, 7, 8, 9, 10, 11, WorldLayout.Poolrooms, WorldLayout.Motion,
            WorldLayout.RunLevel, WorldLayout.FunLevel, WorldLayout.TheEnd, WorldLayout.Level974, WorldLayout.Level3999 };
        int missing = 0, unreachable = 0;
        foreach (int level in levels)
        {
            if (layout.HubDoorOf(level) is not { } d) { Console.WriteLine($"  door to {level}: NONE"); missing++; continue; }
            var (fx, fz) = d.Facing switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
            int fi = (d.Z + fz - z0) * size + d.X + fx - x0;
            bool ok = fi >= 0 && fi < map.Length && seen[fi];
            if (!ok) unreachable++;
            double r = Math.Sqrt(Math.Pow(d.X - layout.HubOriginX, 2) + Math.Pow(d.Z - layout.HubOriginZ, 2));
            Tile t = layout.TileAt(d.X, d.Z);
            Passage p = net.HubDoor(d.X, d.Z, level);
            Link? to = net.Take(p, null);
            string where = to is { } l ? $"L{layout.LevelAt(WorldLayout.MacroOf((int)l.X), WorldLayout.MacroOf((int)l.Z))}" + (layout.IsSnackrooms(WorldLayout.MacroOf((int)l.X), WorldLayout.MacroOf((int)l.Z)) ? " (6.1)" : "") : "nowhere";
            Console.WriteLine($"  door to {(level == WorldLayout.HubSnackroomsDoor ? "178/6.1" : WorldLayout.DisplayNumber(level)),-8} tunnel {layout.HubTunnelAt(d.X + fx, d.Z + fz),2} r {r,5:0} at {d.X},{d.Z} facing {d.Facing,-5} sigil {t.Detail,2} {(WorldLayout.HubDoorOpen(level) ? "open" : level == WorldLayout.Level974 ? "ribbon" : "keyed"),-6} front {(ok ? "reached" : "NOT REACHED")} -> {where}");
        }
        Console.WriteLine($"level doors missing {missing}, unreachable {unreachable}");
        // The window into Level 188: its two tiles, and the floor in front of them
        if (layout.HubWindowOf() is { } w)
        {
            var (fx, fz) = w.Facing switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
            bool tiles = layout.TileAt(w.Left.X, w.Left.Z).Under == Unders.HubWindow188 && layout.TileAt(w.Right.X, w.Right.Z).Under == Unders.HubWindow188;
            int fi = (w.Left.Z + fz - z0) * size + w.Left.X + fx - x0;
            double r = Math.Sqrt(Math.Pow(w.Left.X - layout.HubOriginX, 2) + Math.Pow(w.Left.Z - layout.HubOriginZ, 2));
            Console.WriteLine($"  window to 188  tunnel {layout.HubTunnelAt(w.Left.X + fx, w.Left.Z + fz),2} r {r,5:0} at {w.Left.X},{w.Left.Z} facing {w.Facing}: tiles {(tiles ? "placed" : "MISSING")}, front {(fi >= 0 && fi < map.Length && seen[fi] ? "reached" : "NOT REACHED")}");
        }
        else Console.WriteLine("  window to 188: NONE");
    }

    static void HubMap(WorldLayout layout, int step)
    {
        var (x0, z0, map) = HubRegion(layout);
        int size = (int)Math.Sqrt(map.Length), outSize = size / step;
        using var w = new BinaryWriter(File.Create("hubmap.bin"));
        w.Write(outSize);
        w.Write(x0);
        w.Write(z0);
        w.Write(step);
        for (int z = 0; z < outSize; z++)
            for (int x = 0; x < outSize; x++)
            {
                // The most telling tile of each step x step square
                byte best = 0;
                for (int dz = 0; dz < step; dz++)
                    for (int dx = 0; dx < step; dx++)
                    {
                        byte c = map[(z * step + dz) * size + x * step + dx];
                        if (c > best) best = c;
                    }
                w.Write(best);
            }
        Console.WriteLine($"hubmap.bin: {outSize}x{outSize} (step {step}) from {x0},{z0}");
    }

    static void HubEntrances(WorldLayout layout, int cells)
    {
        int l1 = 0, l2 = 0, l37 = 0, scanned = 0;
        var rng = new Random(7);
        foreach (int level in new[] { 1, 2 })
            for (ulong k = 1; k <= 40; k++)
            {
                if (layout.FindArrival(level, k * 104729UL + 11) is not { } a) continue;
                int amx = WorldLayout.MacroOf(a.X), amz = WorldLayout.MacroOf(a.Z);
                for (int dz = -5; dz <= 5; dz++)
                    for (int dx = -5; dx <= 5; dx++)
                    {
                        if (layout.LevelAt(amx + dx, amz + dz) != level) continue;
                        scanned++;
                        foreach (Tile t in layout.BuildMacro(amx + dx, amz + dz))
                        {
                            if (t.Kind == TileKind.Wall && t.Variant == Decor.HubEntranceDoor) l1++;
                            if (t.Kind == TileKind.Door && t.Under == Unders.HubEntrance) l2++;
                        }
                    }
            }
        for (ulong k = 1; k <= 30; k++)
            if (layout.FindArrival(WorldLayout.Poolrooms, k * 104729UL + 11) is { } a)
                for (int dz = -4; dz <= 4; dz++)
                    for (int dx = -4; dx <= 4; dx++)
                        foreach (Tile t in layout.BuildMacro(WorldLayout.MacroOf(a.X) + dx, WorldLayout.MacroOf(a.Z) + dz))
                            if (t.Under == Unders.PoolAsphalt) l37++;
        Console.WriteLine($"in {scanned} cells of Levels 1 and 2: {l1} Level 1 Hub door tiles, {l2} Level 2 Hub doors; Level 37 asphalt-end tiles: {l37}");
    }

    /// <summary>For the links mode: the label of one of the level's thresholds walked into on this tile, or null.</summary>
    static string HubLinkLabel(Tile t) => t.Under switch
    {
        Unders.HubFalseWall => "false wall",
        Unders.HubHole => "hole in the road",
        Unders.HubTileEnd => "tiled end",
        Unders.HubTowerVoid => "the Tower's void",
        Unders.PoolAsphalt => "dry corridor's asphalt",
        _ => null,
    };

    /// <summary>For the links mode: the threshold kind of one of the level's blocks used on this tile, or null.</summary>
    static string HubUseKind(Tile t) =>
        t.Kind == TileKind.Door && t.Pattern == WallPattern.HubServiceDoor ? "locked"
        : t.Kind == TileKind.Wall && t.Level == 1 && t.Variant == Decor.HubEntranceDoor ? "locked"
        : t.Kind == TileKind.Door && t.Level == 2 && t.Under == Unders.HubEntrance ? "tunneldoor"
        : null;
}
