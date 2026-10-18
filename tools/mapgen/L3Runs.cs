using Backrooms.Worldgen;

/// <summary>
/// l3runs and l3dump: Level 3's wall runs as the player sees them (layout version 9 lays them whole,
/// WorldLayout.Level3Runs.cs). l3runs tallies, over the area of the run (AT=L3 and the cell count), the pieces of wall
/// pipe (the faces the generator draws pipes on, joined along a wall, round outer corners and where one meets
/// another in an inner corner), the cable runs on the walls, the cables on the floor, the gauges (on a pipe, or on a
/// length of their own) and the switchgear cabinets with pipes coming out of their fronts. l3dump x z r writes
/// l3dump.json, the tiles of a square round a block position, for tools/mapgen/render_l3runs.py.
/// </summary>
static class L3Runs
{
    static readonly (int Dx, int Dz)[] Dirs = { (0, -1), (1, 0), (0, 1), (-1, 0) }; // north, east, south, west

    static bool PipeOpen(in Tile n) => n.Kind is TileKind.Floor or TileKind.Doorway or TileKind.Pit or TileKind.Bars or TileKind.Water or TileKind.ArchDoor;

    static bool Carries(in Tile n, int version) => n.Kind == TileKind.Wall && n.Level == 3 && n.Pattern != WallPattern.Stone
        && (n.Variant == Props.WallPipes || version >= 9 && n.Variant == Decor.Gauges);

    static int DirOf(ArchPier p) => p switch { ArchPier.North => 0, ArchPier.East => 1, ArchPier.South => 2, _ => 3 };

    public static void Run(WorldLayout layout, int m0x, int m0z, int n)
    {
        int x0 = m0x * 32, z0 = m0z * 32, size = n * 32;
        var cache = new Dictionary<(int, int), Tile>();
        Tile At(int x, int z)
        {
            if (!cache.TryGetValue((x, z), out Tile t)) cache[(x, z)] = t = layout.TileAt(x, z);
            return t;
        }
        int v = layout.Version;
        bool InArea(int x, int z) => x >= x0 && z >= z0 && x < x0 + size && z < z0 + size;

        // Pipe faces: (x, z, face) where a wall carrying the pipes looks into the open
        var seen = new HashSet<(int, int, int)>();
        var pieces = new SortedDictionary<int, int>();
        int pieceCount = 0, faceCount = 0, shortFaces = 0;
        for (int z = z0; z < z0 + size; z++)
            for (int x = x0; x < x0 + size; x++)
            {
                if (!Carries(At(x, z), v)) continue;
                for (int f = 0; f < 4; f++)
                {
                    if (!PipeOpen(At(x + Dirs[f].Dx, z + Dirs[f].Dz)) || seen.Contains((x, z, f))) continue;
                    // Flood the piece this face belongs to
                    int len = 0;
                    var stack = new Stack<(int, int, int)>();
                    stack.Push((x, z, f));
                    seen.Add((x, z, f));
                    while (stack.Count > 0)
                    {
                        var (cx, cz, cf) = stack.Pop();
                        len++;
                        void Visit(int ax, int az, int af)
                        {
                            if (!InArea(ax, az) || seen.Contains((ax, az, af)) || !Carries(At(ax, az), v)) return;
                            if (!PipeOpen(At(ax + Dirs[af].Dx, az + Dirs[af].Dz))) return;
                            seen.Add((ax, az, af));
                            stack.Push((ax, az, af));
                        }
                        // The block's other open faces (round an outer corner, or the far side of a thin wall)
                        for (int g = 0; g < 4; g++) if (g != cf) Visit(cx, cz, g);
                        // Along the wall either way, and where it meets a wall across it in an inner corner
                        foreach (int a in new[] { (cf + 1) & 3, (cf + 3) & 3 })
                        {
                            int ax = cx + Dirs[a].Dx, az = cz + Dirs[a].Dz;
                            Visit(ax, az, cf);
                            Tile next = At(ax, az);
                            if (next.Kind == TileKind.Wall && !PipeOpen(At(ax + Dirs[cf].Dx, az + Dirs[cf].Dz)))
                                Visit(cx + Dirs[a].Dx + Dirs[cf].Dx, cz + Dirs[a].Dz + Dirs[cf].Dz, (a + 2) & 3);
                        }
                    }
                    pieceCount++;
                    faceCount += len;
                    if (len <= 3) shortFaces += len;
                    int bucket = len <= 6 ? len : len <= 12 ? 12 : len <= 24 ? 24 : 99;
                    pieces[bucket] = pieces.GetValueOrDefault(bucket) + 1;
                }
            }
        Console.WriteLine($"layout version {v}, {n}x{n} cells from {m0x},{m0z}");
        Console.WriteLine($"wall pipe pieces: {pieceCount}, faces {faceCount}, mean {(pieceCount > 0 ? (double)faceCount / pieceCount : 0):0.0} faces; pieces of 1-3 faces: {pieces.Where(p => p.Key <= 3).Sum(p => p.Value)} ({shortFaces} faces)");
        Console.WriteLine("  by length (faces; 12 = 7-12, 24 = 13-24, 99 = more): " + string.Join(", ", pieces.Select(p => $"{p.Key}: {p.Value}")));

        // Gauges, on a pipe or not; switchgear with a pipe beside it, coming out of its front
        int gaugesOn = 0, gaugesOff = 0, gearTotal = 0, gearBad = 0;
        // Cable runs on the walls: consecutive cable blocks facing the same way along a wall
        var cableRuns = new SortedDictionary<int, int>();
        int cableEndsAtPanel = 0;
        // Floor cables: pieces of floor cable blocks joined side by side
        var floorRuns = new SortedDictionary<int, int>();
        int floorEnded = 0, floorPieces = 0;
        var floorSeen = new HashSet<(int, int)>();
        for (int z = z0; z < z0 + size; z++)
            for (int x = x0; x < x0 + size; x++)
            {
                Tile t = At(x, z);
                if (t.Level != 3) continue;
                if (t.Kind == TileKind.Wall && t.Variant == Decor.Gauges)
                {
                    int f = DirOf(t.Pier), a = (f + 1) & 3, b = (f + 3) & 3;
                    bool on = Carries(At(x + Dirs[a].Dx, z + Dirs[a].Dz), v) && Carries(At(x + Dirs[b].Dx, z + Dirs[b].Dz), v) && v >= 9;
                    if (on) gaugesOn++; else gaugesOff++;
                }
                if (t.Kind == TileKind.Floor && t.Variant == Props.Switchgear)
                {
                    gearTotal++;
                    int f = DirOf(t.Pier);
                    foreach (int side in new[] { (f + 1) & 3, (f + 3) & 3 })
                    {
                        int sx = x + Dirs[side].Dx, sz = z + Dirs[side].Dz;
                        // A wall carrying pipes beside it, whose face toward the cabinet is open: the pipe runs along
                        // that wall into the cabinet's front
                        if (Carries(At(sx, sz), v)) { gearBad++; break; }
                    }
                }
                if (t.Kind == TileKind.Wall && t.Variant == Decor.WallCables)
                {
                    int f = DirOf(t.Pier), back = (f + 3) & 3, fwd = (f + 1) & 3;
                    Tile prev = At(x + Dirs[back].Dx, z + Dirs[back].Dz);
                    if (prev.Kind == TileKind.Wall && prev.Variant == Decor.WallCables && prev.Pier == t.Pier) continue;
                    int len = 0, cx = x, cz = z;
                    while (At(cx, cz).Kind == TileKind.Wall && At(cx, cz).Variant == Decor.WallCables && At(cx, cz).Pier == t.Pier)
                    {
                        len++;
                        cx += Dirs[fwd].Dx;
                        cz += Dirs[fwd].Dz;
                    }
                    if (At(cx, cz).Variant == Props.WallPanel && At(cx, cz).Kind == TileKind.Wall || prev.Variant == Props.WallPanel && prev.Kind == TileKind.Wall) cableEndsAtPanel++;
                    int bucket = Math.Min(len, 10);
                    cableRuns[bucket] = cableRuns.GetValueOrDefault(bucket) + 1;
                }
                if (t.Kind == TileKind.Floor && t.Variant == Props.FloorCable && !floorSeen.Contains((x, z)))
                {
                    int len = 0, ends = 0;
                    var stack = new Stack<(int, int)>();
                    stack.Push((x, z));
                    floorSeen.Add((x, z));
                    while (stack.Count > 0)
                    {
                        var (cx, cz) = stack.Pop();
                        len++;
                        if (At(cx, cz).Stack is 1 or 2) ends++;
                        foreach (var (dx, dz) in Dirs)
                        {
                            Tile o = At(cx + dx, cz + dz);
                            if (o.Kind == TileKind.Floor && o.Variant == Props.FloorCable && floorSeen.Add((cx + dx, cz + dz))) stack.Push((cx + dx, cz + dz));
                        }
                    }
                    floorPieces++;
                    if (ends == 2) floorEnded++;
                    int bucket = Math.Min(len, 10);
                    floorRuns[bucket] = floorRuns.GetValueOrDefault(bucket) + 1;
                }
            }
        Console.WriteLine($"gauges: {gaugesOn} on a pipe run, {gaugesOff} on a length of pipe of their own");
        Console.WriteLine($"switchgear cabinets: {gearTotal}, with a pipe along the wall beside them (into the front): {gearBad}");
        Console.WriteLine($"wall cable runs: {cableRuns.Values.Sum()} (by length, 10 = 10 or more: {string.Join(", ", cableRuns.Select(p => $"{p.Key}: {p.Value}"))}); ending at a panel: {cableEndsAtPanel}");
        Console.WriteLine($"floor cable pieces: {floorPieces} (by length: {string.Join(", ", floorRuns.Select(p => $"{p.Key}: {p.Value}"))}); with an end fitting at both ends: {floorEnded}");
    }

    /// <summary>Writes l3dump.json: the tiles of the square of side 2r + 1 round (cx, cz).</summary>
    public static void Dump(WorldLayout layout, int cx, int cz, int r)
    {
        using var w = new StreamWriter("l3dump.json");
        w.Write($"{{\"version\": {layout.Version}, \"x0\": {cx - r}, \"z0\": {cz - r}, \"size\": {2 * r + 1}, \"tiles\": [");
        bool firstRow = true;
        for (int z = cz - r; z <= cz + r; z++)
        {
            w.Write(firstRow ? "[" : ",\n[");
            firstRow = false;
            for (int x = cx - r; x <= cx + r; x++)
            {
                Tile t = layout.TileAt(x, z);
                if (x > cx - r) w.Write(",");
                w.Write($"[{(int)t.Kind},{t.Variant},{(int)t.Pier},{t.Stack},{(int)t.Pattern},{t.Level},{(t.Sealed ? 1 : 0)},{t.Pipe}]");
            }
            w.Write("]");
        }
        w.WriteLine("]}");
        Console.WriteLine($"l3dump.json: {2 * r + 1} square round {cx},{cz}");
    }
}
