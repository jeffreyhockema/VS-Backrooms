using System.Diagnostics;
using Backrooms.Worldgen;

/// <summary>
/// The End's harness modes (this file is the level's own; see docs/design/new-levels/CONTRACT.md):
///   endstats [departments]        what the departments round the centre hold: kinds, floor, light, books, exits,
///                                 arrivals (anywhere, and beside an EXIT door), cost per department plan
///   endloop [departments]         every long aisle: its looping stretch repeats exactly every 32 blocks (tiles at s and
///                                 s + 32, the aisle and three rows either side), and every period has a gap out
///   endmap dx dz size out.ppm     a top-down picture of size x size blocks round department (dx, dz), one pixel a block
/// </summary>
static partial class LevelModes
{
    static bool EndModes(WorldLayout layout, string mode, string[] args)
    {
        switch (mode)
        {
            case "endstats": EndStatsMode(layout, args.Length > 3 ? int.Parse(args[3]) : 6); return true;
            case "endloop": EndLoopMode(layout, args.Length > 3 ? int.Parse(args[3]) : 12); return true;
            case "endhash": EndHashMode(args); return true;
            case "endfind":
                // The nearest department of each kind to the central hall, with its middle in block coordinates
                var seen = new HashSet<WorldLayout.EndKind>();
                for (int r = 0; r < 12; r++)
                    for (int dj = -r; dj <= r; dj++)
                        for (int di = -r; di <= r; di++)
                        {
                            if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                            var k = layout.EndKindAt(di, dj);
                            if (!seen.Add(k)) continue;
                            var (x, z) = layout.EndDeptCentre(di, dj);
                            Console.WriteLine($"  {k,-10} department {di},{dj}: middle {x},{z}" + (k == WorldLayout.EndKind.Fake ? $" ({layout.EndFakeAt(di, dj)})" : ""));
                        }
                return true;
            case "endmap":
                EndMapMode(layout, int.Parse(args[3]), int.Parse(args[4]), int.Parse(args[5]), args[6]);
                return true;
        }
        return false;
    }

    /// <summary>endhash: the layout hash with The End's entrances in other levels left out, then with them, and the lines that differ.</summary>
    static void EndHashMode(string[] args)
    {
        string Capture(bool entrances)
        {
            WorldLayout.EndEntrances = entrances;
            var old = Console.Out;
            var sw = new StringWriter();
            Console.SetOut(sw);
            try { LayoutHash.Run(args); }
            finally { Console.SetOut(old); WorldLayout.EndEntrances = true; }
            return sw.ToString();
        }
        string[] without = Capture(false).Split(Environment.NewLine), with = Capture(true).Split(Environment.NewLine);
        Console.WriteLine($"without The End's entrances: {without.LastOrDefault(l => l.StartsWith("layout hash"))}");
        Console.WriteLine($"with them:                   {with.LastOrDefault(l => l.StartsWith("layout hash"))}");
        string world = "";
        for (int i = 0; i < Math.Min(without.Length, with.Length); i++)
        {
            if (with[i].StartsWith("world")) world = with[i].Split(':')[0];
            if (without[i] != with[i]) Console.WriteLine($"  {world} differs: {without[i].Trim()}  ->  {with[i].Trim()}");
        }
    }

    static readonly Dictionary<(int, int), Tile[]> endCells = new();

    static Tile EndTile(WorldLayout layout, int x, int z)
    {
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        if (!endCells.TryGetValue((mx, mz), out var t))
        {
            if (endCells.Count > 4000) endCells.Clear();
            endCells[(mx, mz)] = t = layout.BuildMacro(mx, mz);
        }
        return t[WorldLayout.TileIndex(x - mx * 32, z - mz * 32)];
    }

    static void EndStatsMode(WorldLayout layout, int reach)
    {
        var kinds = new Dictionary<WorldLayout.EndKind, int>();
        var fakes = new Dictionary<WorldLayout.EndFake, int>();
        long floor = 0, lit = 0, all = 0, books = 0, shelves = 0, sealedFloor = 0, runway = 0;
        int exits = 0, fakeDoors = 0, vents = 0, terminals = 0, letters = 0;
        var watch = Stopwatch.StartNew();
        int depts = 0;
        for (int dj = -reach; dj <= reach; dj++)
            for (int di = -reach; di <= reach; di++)
            {
                var (cx, cz) = layout.EndDeptCentre(di, dj);
                if (layout.LevelAt(WorldLayout.MacroOf(cx), WorldLayout.MacroOf(cz)) != WorldLayout.TheEnd) continue;
                depts++;
                var k = layout.EndKindAt(di, dj);
                kinds[k] = kinds.GetValueOrDefault(k) + 1;
                if (k == WorldLayout.EndKind.Fake) { var f = layout.EndFakeAt(di, dj); fakes[f] = fakes.GetValueOrDefault(f) + 1; }
                int x0 = cx - 32, z0 = cz - 32;
                for (int z = z0; z < z0 + 64; z++)
                    for (int x = x0; x < x0 + 64; x++)
                    {
                        Tile t = EndTile(layout, x, z);
                        if (t.Level != WorldLayout.TheEnd) continue;
                        all++;
                        if (t.Kind == TileKind.Door && t.Pattern == WallPattern.EndExit) exits++;
                        if (t.Under == Unders.EndFakeDoor) fakeDoors++;
                        if (t.Under == Unders.EndVentWall) vents++;
                        if (t.Kind != TileKind.Floor) continue;
                        floor++;
                        if (t.Sealed && t.Variant == 0) sealedFloor++;
                        if (t.Floor == FloorKind.EndRunway) runway++;
                        if (t.Variant == Props.EndShelf) { shelves++; if (t.Stack == 1) books++; }
                        if (t.Variant == Props.EndDesk && (t.Stack & 8) != 0) terminals++;
                        if (t.Overhead == Overheads.EndSoffitLetter && t.Stack != 0) letters++;
                        if (EndLitNear(layout, x, z)) lit++;
                    }
            }
        double ms = watch.Elapsed.TotalMilliseconds;
        Console.WriteLine($"The End: {depts} departments within {reach} of the centre ({ms / Math.Max(1, depts):0.0} ms each, cells included)");
        foreach (var (k, n) in kinds.OrderBy(p => p.Key)) Console.WriteLine($"  {k,-10} {n,4}  {100.0 * n / depts:0.0}%");
        foreach (var (f, n) in fakes.OrderBy(p => p.Key)) Console.WriteLine($"    fake {f,-8} {n,3}");
        Console.WriteLine($"  floor {100.0 * floor / all:0.0}% of tiles; runway {100.0 * runway / Math.Max(1, floor):0.0}% of floor; sealed {100.0 * sealedFloor / Math.Max(1, floor):0.00}%");
        Console.WriteLine($"  lit (a working light within 3 blocks) {100.0 * lit / Math.Max(1, floor):0.0}% of floor");
        Console.WriteLine($"  shelves {shelves}, with books {books} (1 in {shelves / Math.Max(1, books)}); terminals {terminals}; letters {letters}");
        Console.WriteLine($"  EXIT doors {exits}, fake-reality doors {fakeDoors}, vents {vents}  (per km²: {exits * 1e6 / all:0.0} exits)");

        int found = 0, beside = 0, wrong = 0;
        var t0 = Stopwatch.StartNew();
        for (ulong key = 1; key <= 60; key++)
        {
            var a = layout.FindArrival(WorldLayout.TheEnd, key * 104729UL + 7);
            if (a is { } p) { found++; if (layout.LevelAt(WorldLayout.MacroOf(p.X), WorldLayout.MacroOf(p.Z)) != WorldLayout.TheEnd) wrong++; }
            var b = layout.FindArrival(WorldLayout.TheEnd, key * 7919UL + 3, WorldLayout.IsEndExitDoor);
            if (b is { } q)
            {
                bool next = false;
                foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    if (WorldLayout.IsEndExitDoor(EndTile(layout, q.X + dx, q.Z + dz))) next = true;
                if (next) beside++;
            }
        }
        Console.WriteLine($"  arrivals: {found}/60 found ({wrong} in the wrong level); beside an EXIT door {beside}/60 ({t0.Elapsed.TotalMilliseconds / 120:0.0} ms each)");
    }

    /// <summary>Whether a working (emitting) light hangs within 3 blocks of a floor tile, or a lamp, a pendant or a deck light.</summary>
    static bool EndLitNear(WorldLayout layout, int x, int z)
    {
        for (int dz = -3; dz <= 3; dz++)
            for (int dx = -3; dx <= 3; dx++)
            {
                Tile t = EndTile(layout, x + dx, z + dz);
                if (t.Kind != TileKind.Floor) continue;
                if (t.Ceiling == CeilingKind.LightOn || t.Overhead == Overheads.EndPendant) return true;
                if (t.Variant == Props.EndFurniture && t.Stack == 1) return true;
            }
        return false;
    }

    static void EndLoopMode(WorldLayout layout, int reach)
    {
        int aisles = 0, bad = 0, gapless = 0;
        for (int dj = -reach; dj <= reach; dj++)
            for (int di = -reach; di <= reach; di++)
            {
                if (layout.EndKindAt(di, dj) != WorldLayout.EndKind.LongLeft) continue;
                var (cx, cz) = layout.EndDeptCentre(di, dj);
                int x0 = cx - 32, z0 = cz - 32;
                bool inside = true;
                for (int s = 0; s < 128 && inside; s += 8)
                    if (layout.LevelAt(WorldLayout.MacroOf(x0 + s), WorldLayout.MacroOf(z0 + 31)) != WorldLayout.TheEnd) inside = false;
                if (!inside) continue;
                aisles++;
                int mismatches = 0;
                for (int s = WorldLayout.EndLoopStart + 28; s + 32 < WorldLayout.EndLoopEnd; s++)
                    for (int c = 27; c <= 35; c++)
                    {
                        Tile p = EndTile(layout, x0 + s, z0 + c), q = EndTile(layout, x0 + s + 32, z0 + c);
                        if (p.Kind != q.Kind || p.Variant != q.Variant || p.Stack != q.Stack || p.Pier != q.Pier || p.Ceiling != q.Ceiling
                            || p.Height != q.Height || p.Floor != q.Floor || p.Under != q.Under)
                        {
                            if (mismatches++ < 2) Console.WriteLine($"    s {s} row {c}: {p.Kind}/{p.Variant}/{p.Stack}/{p.Pier}/{p.Ceiling}/{p.Height}/{p.Floor}/{p.Under} vs {q.Kind}/{q.Variant}/{q.Stack}/{q.Pier}/{q.Ceiling}/{q.Height}/{q.Floor}/{q.Under}");
                        }
                    }
                // Every period has a way out to the side
                for (int period = 1; period < 3; period++)
                {
                    bool gap = false;
                    for (int s = period * 32; s < period * 32 + 32; s++)
                        foreach (int c in new[] { 28, 29, 33, 34 })
                            if (EndTile(layout, x0 + s, z0 + c).Kind == TileKind.Floor && EndTile(layout, x0 + s, z0 + c).Variant == 0
                                && EndTile(layout, x0 + s, z0 + (c < 31 ? 27 : 35)).Kind == TileKind.Floor) gap = true;
                    if (!gap) gapless++;
                }
                if (mismatches > 0) { bad++; Console.WriteLine($"  long aisle at {x0},{z0}: {mismatches} tiles differ from 32 blocks on"); }
            }
        Console.WriteLine($"The End: {aisles} long aisles within {reach} departments; {bad} not periodic; {gapless} periods with no gap out");
    }

    static void EndMapMode(WorldLayout layout, int ddx, int ddz, int size, string path)
    {
        var (cx, cz) = layout.EndDeptCentre(ddx, ddz);
        int x0 = cx - size / 2, z0 = cz - size / 2;
        using var f = File.Create(path);
        var header = System.Text.Encoding.ASCII.GetBytes($"P6\n{size} {size}\n255\n");
        f.Write(header);
        var row = new byte[size * 3];
        for (int z = z0; z < z0 + size; z++)
        {
            for (int x = x0; x < x0 + size; x++)
            {
                Tile t = EndTile(layout, x, z);
                var (r, g, b) = EndColour(t);
                int i = (x - x0) * 3;
                row[i] = r; row[i + 1] = g; row[i + 2] = b;
            }
            f.Write(row);
        }
        Console.WriteLine($"wrote {path}: {size}x{size} blocks round department {ddx},{ddz} (block {x0},{z0})");
    }

    static (byte, byte, byte) EndColour(Tile t)
    {
        if (t.Level != WorldLayout.TheEnd) return (40, 60, 30);
        if (t.Kind == TileKind.Door) return t.Pattern == WallPattern.EndExit ? ((byte)230, (byte)30, (byte)30) : ((byte)120, (byte)70, (byte)40);
        if (t.Kind == TileKind.Doorway) return t.Under == Unders.EndFakeDoor ? ((byte)255, (byte)0, (byte)255) : ((byte)200, (byte)190, (byte)160);
        if (t.Kind != TileKind.Floor)
        {
            if (t.Under == Unders.EndVentWall) return (0, 200, 255);
            return t.Pattern switch
            {
                WallPattern.EndColumn => (154, 174, 134),
                WallPattern.EndColumnSlate => (139, 154, 177),
                WallPattern.EndStockWall => (150, 150, 145),
                WallPattern.EndWall => (232, 223, 194),
                _ => (180, 150, 90),
            };
        }
        (byte, byte, byte) c = t.Floor switch
        {
            FloorKind.EndRunway => (46, 57, 104),
            FloorKind.EndConcrete or FloorKind.EndConcreteLine => (140, 138, 132),
            FloorKind.EndCarpetSnow => (240, 244, 250),
            FloorKind.Carpet => (170, 150, 90),
            FloorKind.OfficeCarpet => (110, 110, 115),
            FloorKind.HotelCarpet or FloorKind.HotelRunnerWE => (120, 30, 30),
            FloorKind.HouseWood or FloorKind.HouseRug or FloorKind.HouseCarpet => (150, 110, 70),
            _ => (100, 107, 95),
        };
        if (t.Variant is Props.EndShelf or Props.EndTallShelf or Props.EndWallShelf) c = t.Stack == 1 && t.Variant != Props.EndTallShelf ? ((byte)255, (byte)230, (byte)0) : ((byte)205, (byte)154, (byte)85);
        else if (t.Variant == Props.EndEndcap) c = (170, 110, 50);
        else if (t.Variant == Props.EndDesk) c = (t.Stack & 8) != 0 ? ((byte)255, (byte)255, (byte)255) : ((byte)185, (byte)138, (byte)78);
        else if (t.Variant is Props.EndFurniture or Props.EndCatalogue) c = (120, 80, 50);
        else if (t.Variant is Props.EndStock or Props.EndRubble) c = (90, 70, 50);
        else if (t.Variant == Props.EndEscalator) c = (60, 60, 60);
        else if (t.Variant == Props.EndTree) c = (60, 50, 40);
        else if (t.Variant != 0 && t.Variant != Props.EndSnow) c = (200, 100, 200);
        if (t.Overhead == Overheads.EndSoffitLetter) c = (60, 50, 40);
        else if (t.Overhead is Overheads.EndDeck or Overheads.EndDeckEdge) c = ((byte)(c.Item1 * 0.8), (byte)(c.Item2 * 0.8), (byte)(c.Item3 * 0.8));
        if (t.Ceiling == CeilingKind.LightOn) c = ((byte)Math.Min(255, c.Item1 + 40), (byte)Math.Min(255, c.Item2 + 40), (byte)Math.Min(255, c.Item3 + 30));
        if (t.Under == Unders.EndLoop) c = ((byte)Math.Min(255, c.Item1 + 30), c.Item2, c.Item3);
        if (t.Sealed && t.Variant == 0) c = (255, 120, 0);
        return c;
    }

    /// <summary>For the links mode: the label of one of the level's thresholds walked into on this tile (e.g. "pit"), or null.</summary>
    static string EndLinkLabel(Tile t) => t.Under switch
    {
        Unders.EndFakeDoor when t.Level == WorldLayout.TheEnd => "fakedoor",
        Unders.EndFrame when t.Level == 4 => "endframe",
        _ => null,
    };

    /// <summary>For the links mode: the threshold kind of one of the level's blocks used on this tile (its BlockBehaviorThreshold kind), or null.</summary>
    static string EndUseKind(Tile t)
    {
        if (t.Kind == TileKind.Door && t.Pattern == WallPattern.EndExit) return "endexit";
        if (t.Kind == TileKind.Door && t.Under == Unders.EndExitL1) return "endexit";
        if (t.Kind == TileKind.Door && t.Under == Unders.EndBookstore) return "endbookstore";
        if (t.Under == Unders.EndVentWall && t.Level == WorldLayout.TheEnd) return "endvent";
        return null;
    }
}
