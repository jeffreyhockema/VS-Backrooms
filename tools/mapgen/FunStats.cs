using Backrooms.Worldgen;

/// <summary>Level Fun's harness modes (this file is the level's own; see docs/new-levels/CONTRACT.md).</summary>
static partial class LevelModes
{
    /// <summary>
    /// funstats [blocks]: what a square of the level's plan blocks holds (floor by zone, parties and their guests, the
    /// dark, the longest straight look down a corridor, floor that cannot be walked to, special rooms, time per block).
    /// funmap [blocks] [dx dz]: funmap.ppm, a picture of a square of blocks (each tile one pixel).
    /// </summary>
    static bool FunModes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "funstats") { FunStats(layout, args.Length > 3 ? int.Parse(args[3]) : 6); return true; }
        if (mode == "funpeek") { FunPeek(layout); return true; }
        if (mode == "funprobe") { FunProbe(layout); return true; }
        if (mode == "funlinks") { FunLinks(layout, long.Parse(args[0])); return true; }
        if (mode == "funmap")
        {
            int n = args.Length > 3 ? int.Parse(args[3]) : 3;
            int dx = args.Length > 5 ? int.Parse(args[4]) : 0, dz = args.Length > 5 ? int.Parse(args[5]) : 0;
            FunMap(layout, n, dx, dz);
            return true;
        }
        return false;
    }

    /// <summary>The square of blocks to look at: around an arrival near the middle of the region.</summary>
    static (int X0, int Z0, int Size) FunWindow(WorldLayout layout, int blocks, int dx = 0, int dz = 0)
    {
        var a = layout.FindArrival(WorldLayout.FunLevel, 99991UL) ?? throw new Exception("Level Fun: no arrival found");
        var (bi, bj) = layout.FunBlockOf(a.X, a.Z);
        bi += dx - blocks / 2; bj += dz - blocks / 2;
        return (layout.FunOriginX + bi * WorldLayout.FunBlock, layout.FunOriginZ + bj * WorldLayout.FunBlock, blocks * WorldLayout.FunBlock);
    }

    static Tile[] FunTiles(WorldLayout layout, int x0, int z0, int size)
    {
        var tiles = new Tile[size * size];
        for (int mz = 0; mz < size / 32; mz++)
            for (int mx = 0; mx < size / 32; mx++)
            {
                int cmx = WorldLayout.MacroOf(x0) + mx, cmz = WorldLayout.MacroOf(z0) + mz;
                Tile[] cell = layout.BuildMacro(cmx, cmz);
                for (int i = 0; i < cell.Length; i++)
                {
                    int x = cmx * 32 + i % 32 - x0, z = cmz * 32 + i / 32 - z0;
                    if (x >= 0 && z >= 0 && x < size && z < size) tiles[z * size + x] = cell[i];
                }
            }
        return tiles;
    }

    static bool FunWalkable(Tile t) => t.Kind is TileKind.Doorway || t.Kind == TileKind.Floor && t.Zone != (byte)FunZone.Sea
        && (WorldLayout.IsWalkThroughProp(t.Variant) || t.Stair > 0) && t.Depth == 0;

    static void FunStats(WorldLayout layout, int blocks)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var (x0, z0, size) = FunWindow(layout, blocks);
        // Time to plan a block, cold
        var (b0, c0) = layout.FunBlockOf(x0, z0);
        var tp = System.Diagnostics.Stopwatch.StartNew();
        int planned = 0;
        for (int j = 0; j < blocks; j++) for (int i = 0; i < blocks; i++) { layout.FunPlan(b0 + 40 + i, c0 + 40 + j); planned++; }
        double msPerBlock = tp.Elapsed.TotalMilliseconds / planned;

        Tile[] tiles = FunTiles(layout, x0, z0, size);
        int floor = 0, dark = 0, sealedFloor = 0, unreached = 0;
        var byZone = new int[32];
        var lit = new bool[tiles.Length];
        var q = new Queue<(int, int, int)>();
        for (int i = 0; i < tiles.Length; i++)
            if (tiles[i].Kind == TileKind.Floor && tiles[i].Ceiling == CeilingKind.LightOn) { lit[i] = true; q.Enqueue((i % size, i / size, 0)); }
        // Light from the working lights, carried across open floor (a troffer reads as light 4 or more for about nine blocks)
        var dist = new int[tiles.Length];
        Array.Fill(dist, 99);
        foreach (var (x, z, _) in q) dist[z * size + x] = 0;
        while (q.Count > 0)
        {
            var (x, z, d) = q.Dequeue();
            if (d >= 9) continue;
            foreach (var (ddx, ddz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + ddx, nz = z + ddz;
                if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                int j = nz * size + nx;
                if (tiles[j].Kind == TileKind.Wall || tiles[j].Kind == TileKind.Door || dist[j] <= d + 1) continue;
                dist[j] = d + 1;
                q.Enqueue((nx, nz, d + 1));
            }
        }
        // What can be walked to from a lobby
        var reached = new bool[tiles.Length];
        {
            // From the lobby nearest the middle of the window (corridors near its edges can wander out of it)
            int best = -1, bestD = int.MaxValue;
            for (int i = 0; i < tiles.Length; i++)
            {
                if (tiles[i].Zone != (byte)FunZone.Lobby || tiles[i].Kind != TileKind.Floor) continue;
                int d = Math.Abs(i % size - size / 2) + Math.Abs(i / size - size / 2);
                if (d < bestD) { bestD = d; best = i; }
            }
            reached[best] = true; q.Enqueue((best % size, best / size, 0));
        }
        while (q.Count > 0)
        {
            var (x, z, _) = q.Dequeue();
            foreach (var (ddx, ddz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + ddx, nz = z + ddz;
                if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                int j = nz * size + nx;
                if (reached[j] || !FunWalkable(tiles[j])) continue;
                reached[j] = true;
                q.Enqueue((nx, nz, 0));
            }
        }
        Console.WriteLine($"  reached from a lobby: {reached.Count(r => r)} tiles");
        int margin = 40;
        for (int i = 0; i < tiles.Length; i++)
        {
            Tile t = tiles[i];
            if (t.Kind != TileKind.Floor || t.Zone == (byte)FunZone.Sea) continue;
            floor++;
            byZone[t.Zone]++;
            if (dist[i] > 9) dark++;
            if (t.Sealed) sealedFloor++;
            int x = i % size, z = i / size;
            bool inner = x > margin && z > margin && x < size - margin && z < size - margin;
            if (inner && !reached[i] && FunWalkable(t) && !t.Sealed) unreached++;
        }
        // The longest straight look down a corridor (the cloned halls apart)
        int longest = 0, longestClone = 0;
        foreach (bool alongX in new[] { true, false })
            for (int a = 0; a < size; a++)
            {
                int run = 0; bool clone = false;
                for (int b = 0; b < size; b++)
                {
                    Tile t = alongX ? tiles[a * size + b] : tiles[b * size + a];
                    bool corridor = t.Kind == TileKind.Floor && t.Zone is (byte)FunZone.Promenade or (byte)FunZone.Hall;
                    if (corridor) { run++; clone |= InCloneColumn(layout, alongX ? x0 + b : x0 + a, alongX ? z0 + a : z0 + b); }
                    else
                    {
                        if (clone) longestClone = Math.Max(longestClone, run); else longest = Math.Max(longest, run);
                        run = 0; clone = false;
                    }
                }
            }
        // The rooms and their parties
        var rooms = new List<FunRoom>();
        for (int j = 0; j < blocks; j++) for (int i = 0; i < blocks; i++) rooms.AddRange(layout.FunPlan(b0 + i, c0 + j).Rooms);
        int parties = rooms.Count(r => r.Kind is FunZone.Party or FunZone.Clone), guests = rooms.Count(r => r.Guests > 0);
        int guestCount = rooms.Sum(r => r.Guests), spots = rooms.Sum(r => r.Spots.Count);

        Console.WriteLine($"Level Fun: {blocks}x{blocks} blocks at {x0},{z0} ({size}x{size}), planned in {msPerBlock:0.00} ms per block (cold)");
        Console.WriteLine($"  floor {floor} tiles ({100.0 * floor / tiles.Length:0}% of the area), dark (no working light within 9) {100.0 * dark / floor:0}%, sealed {sealedFloor}, not reached from a lobby {unreached}");
        foreach (FunZone zone in Enum.GetValues<FunZone>())
            if (byZone[(int)zone] > 0) Console.WriteLine($"    {zone,-10} {100.0 * byZone[(int)zone] / floor,5:0.0}%");
        Console.WriteLine($"  longest straight look down a corridor {longest} (cloned halls {longestClone})");
        Console.WriteLine($"  rooms {rooms.Count}: parties {parties}, with guests {guests} ({100.0 * guests / Math.Max(1, rooms.Count(r => r.Guests >= 0 && r.Kind is FunZone.Party or FunZone.Clone or FunZone.Themed or FunZone.Mural)):0}% of the rooms that could), guests {guestCount}, spots found {spots}");
        foreach (var g in rooms.GroupBy(r => r.Kind).OrderBy(g => g.Key)) Console.Write($" {g.Key}:{g.Count()}");
        Console.WriteLine();
        int reversed = tiles.Count(t => FunWallItems.Item(t.Roof) == FunWallItems.PosterReversed), deep = tiles.Count(t => t.Under == Unders.FunBallPitDeep);
        int funDoors = tiles.Count(t => t.Kind == TileKind.Door && t.Pattern == WallPattern.FunDoor), exits = tiles.Count(t => t.Kind == TileKind.Door && t.Pattern == WallPattern.FunExitDoor);
        int stairs = tiles.Count(t => t.Kind == TileKind.Floor && t.Stair > 0), sea = tiles.Count(t => t.Under == Unders.FunOverboard);
        Console.WriteLine($"  thresholds: reversed posters {reversed}, deep ball pit tiles {deep}, FUN door leaves {funDoors}, waiting-room doors {exits}, stair tiles {stairs}, sea tiles {sea}");
        Console.WriteLine($"  props {tiles.Count(t => t.Variant >= Props.FunFirst && t.Variant <= Props.FunLast)}, wall items {tiles.Count(t => t.Kind == TileKind.Floor && t.Roof != 0)}, overheads {tiles.Count(t => t.Overhead != 0)}, table tops {tiles.Count(t => t.Pipe != 0 && t.Kind == TileKind.Floor)}");
        Console.WriteLine($"  ({sw.ElapsedMilliseconds} ms)");
    }

    static bool InCloneColumn(WorldLayout layout, int x, int z)
    {
        var (bi, _) = layout.FunBlockOf(x, z);
        int u = x - layout.FunOriginX - bi * WorldLayout.FunBlock;
        return u is >= 29 and <= 35 && layout.FunRoomAt(x + 6, z) is { Kind: FunZone.Clone };
    }

    static void FunMap(WorldLayout layout, int blocks, int dx, int dz)
    {
        var (x0, z0, size) = FunWindow(layout, blocks, dx, dz);
        Tile[] tiles = FunTiles(layout, x0, z0, size);
        using var file = new FileStream("funmap.ppm", FileMode.Create);
        var header = System.Text.Encoding.ASCII.GetBytes($"P6 {size} {size} 255\n");
        file.Write(header);
        var px = new byte[3];
        (byte, byte, byte)[] paints = { (240, 138, 60), (120, 180, 230), (150, 210, 90), (240, 150, 190), (243, 226, 122), (180, 150, 220) };
        for (int i = 0; i < tiles.Length; i++)
        {
            Tile t = tiles[i];
            (byte R, byte G, byte B) c = t.Kind switch
            {
                TileKind.Wall => t.Pattern switch
                {
                    WallPattern.FunWall => (235, 235, 235), WallPattern.FunVoid => (5, 7, 11), WallPattern.FunElevator => (190, 150, 60),
                    WallPattern.FunInflatable => (230, 60, 60), WallPattern.FunSteel => (110, 115, 120), WallPattern.FunPromenade => (120, 110, 90),
                    WallPattern.FunPaint or WallPattern.FunMural => Dim(paints[Math.Min(t.Detail & 7, 5)]), _ => (40, 40, 40),
                },
                TileKind.Door => (255, 0, 255),
                TileKind.Doorway => (200, 200, 170),
                _ => (FunZone)t.Zone switch
                {
                    FunZone.Promenade => (225, 215, 185), FunZone.Hall => (205, 195, 170), FunZone.Lobby => (150, 30, 40),
                    FunZone.Sea => (10, 20, 40), FunZone.Deck => (154, 106, 62), FunZone.Service => (90, 90, 95),
                    FunZone.Bounce => (240, 230, 120), FunZone.Play => (120, 200, 240), FunZone.Waiting => (130, 140, 150),
                    _ => paints[Math.Min(t.Detail & 7, 5)],
                },
            };
            if (t.Kind == TileKind.Floor)
            {
                if (t.Variant == Props.FunTable) c = (255, 255, 255);
                else if (t.Variant is Props.FunChair or Props.FunChairTipped) c = (60, 60, 60);
                else if (t.Variant == Props.FunGift) c = (200, 0, 200);
                else if (t.Depth > 0 && t.Zone != (byte)FunZone.Sea) c = t.Under == Unders.FunBallPitDeep ? ((byte)0, (byte)90, (byte)200) : ((byte)90, (byte)160, (byte)230);
                else if (t.Stair > 0) c = ((byte)(60 * t.Stair), 0, 0);
                if (t.Pipe is Pipes.FunCakeBirthday or Pipes.FunCakeVelvet) c = (255, 0, 0);
                if (FunWallItems.Item(t.Roof) == FunWallItems.PosterReversed) c = (0, 255, 0);
            }
            px[0] = c.R; px[1] = c.G; px[2] = c.B;
            file.Write(px);
        }
        Console.WriteLine($"funmap.ppm: {size}x{size} from {x0},{z0}");

        static (byte, byte, byte) Dim((byte R, byte G, byte B) c) => ((byte)(c.R * 0.55), (byte)(c.G * 0.55), (byte)(c.B * 0.55));
    }

    /// <summary>For the links mode: the label of one of the level's thresholds walked into on this tile (e.g. "pit"), or null.</summary>
    static string FunLinkLabel(Tile t) => t.Under switch
    {
        Unders.FunBallPitDeep => "deep ball pit",
        Unders.FunOverboard => "overboard",
        _ => null,
    };

    /// <summary>For the links mode: the threshold kind of one of the level's blocks used on this tile (its BlockBehaviorThreshold kind), or null.</summary>
    static string FunUseKind(Tile t) =>
        t.Kind == TileKind.Door && t.Pattern == WallPattern.FunDoor ? "fundoor"
        : t.Kind == TileKind.Door && t.Pattern == WallPattern.FunExitDoor ? "funlobbydoor"
        : t.Kind == TileKind.Door && t.Under == Unders.FunMascotDoor ? "mascotdoor"
        : t.Kind == TileKind.Floor && t.Variant == Props.FunPosterTrap ? "funposter"
        : t.Kind == TileKind.Floor && t.Level == WorldLayout.FunLevel && FunWallItems.Item(t.Roof) == FunWallItems.PosterReversed ? "funposter-reversed"
        : null;
}

static partial class LevelModes
{
    /// <summary>funpeek: prints the tiles round the first sealed floor tile of the window (debugging).</summary>
    public static void FunPeek(WorldLayout layout)
    {
        var (x0, z0, size) = FunWindow(layout, 3);
        Tile[] tiles = FunTiles(layout, x0, z0, size);
        int idx = Array.FindIndex(tiles, t => t.Kind == TileKind.Floor && t.Sealed);
        if (idx < 0) { Console.WriteLine("no sealed floor"); return; }
        int cx = idx % size, cz = idx / size;
        Console.WriteLine($"sealed at {x0 + cx},{z0 + cz} zone {(FunZone)tiles[idx].Zone}");
        for (int z = Math.Max(0, cz - 12); z < Math.Min(size, cz + 12); z++)
        {
            var sb = new System.Text.StringBuilder();
            for (int x = Math.Max(0, cx - 30); x < Math.Min(size, cx + 30); x++)
            {
                Tile t = tiles[z * size + x];
                sb.Append(t.Kind switch { TileKind.Wall => '#', TileKind.Doorway => 'D', TileKind.Door => 'X',
                    TileKind.Floor => t.Sealed ? 's' : t.Variant != 0 ? 'p' : t.Depth > 0 ? '~' : '.', _ => '?' });
            }
            Console.WriteLine(sb);
        }
    }
}

static partial class LevelModes
{
    /// <summary>
    /// funlinks: the ways into Level Fun from Level 0 (the poster in a party cell) and Level 1 (the stair cores that
    /// climb into it), found by walking those levels, gone through, and (for the stairs) climbed back.
    /// </summary>
    static void FunLinks(WorldLayout layout, long seed)
    {
        var net = new Backrooms.Thresholds.ThresholdNetwork(layout, new WorldGeometry(256), seed);
        var spawn = layout.FindSpawn();
        int smx = WorldLayout.MacroOf(spawn.X), smz = WorldLayout.MacroOf(spawn.Z);
        int cells = 0, posters = 0, ok = 0;
        for (int dz = -140; dz <= 140 && posters < 4; dz++)
            for (int dx = -140; dx <= 140 && posters < 4; dx++)
            {
                if (!layout.IsFunPartyCell(smx + dx, smz + dz)) continue;
                cells++;
                Tile[] tiles = layout.BuildMacro(smx + dx, smz + dz);
                int i = Array.FindIndex(tiles, t => t.Variant == Props.FunPosterTrap);
                if (i < 0) { Console.WriteLine($"  party cell {smx + dx},{smz + dz}: no poster"); continue; }
                posters++;
                int x = (smx + dx) * 32 + i % 32, z = (smz + dz) * 32 + i / 32;
                var p = net.Used(x, z, "funposter", out string refusal);
                var link = p == null ? null : net.Take(p, null);
                int to = link is { } l ? layout.LevelAt(WorldLayout.MacroOf((int)l.X), WorldLayout.MacroOf((int)l.Z)) : -1;
                bool lobby = link is { } l2 && (FunZone)layout.TileAt((int)l2.X, (int)l2.Z).Zone == FunZone.Lobby;
                if (to == WorldLayout.FunLevel && lobby && !p.TwoWay) ok++;
                Console.WriteLine($"  L0 party cell {smx + dx},{smz + dz}: poster at {x},{z} -> level {to}{(lobby ? " (a lobby)" : "")} {(p?.TwoWay == true ? "two-way!" : "one-way")} {refusal}");
            }
        Console.WriteLine($"Level 0: {cells} party cells, {posters} posters, {ok} lead into a lobby of Level Fun");

        // Level 1: stair cores near its arrivals
        int cores = 0, back = 0;
        var seen = new HashSet<(int, int)>();
        for (ulong k = 1; k <= 400 && cores < 4; k++)
        {
            if (layout.FindArrival(1, k * 104729UL + 11) is not { } a) continue;
            for (int dz = -3; dz <= 3 && cores < 4; dz++)
                for (int dx = -3; dx <= 3 && cores < 4; dx++)
                {
                    int mx = WorldLayout.MacroOf(a.X) + dx, mz = WorldLayout.MacroOf(a.Z) + dz;
                    if (!seen.Add((mx, mz))) continue;
                    Tile[] tiles = layout.BuildMacro(mx, mz);
                    for (int i = 0; i < tiles.Length; i++)
                    {
                        Tile t = tiles[i];
                        if (t.Level != 1 || t.Stair < 2) continue;
                        int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
                        // (From layout version 4 the flight is climbed into the shaft over the core, and the way home is its landing)
                        var p = net.Walked(x, z, t, 3.0) ?? net.Walked(x, z, t, 6.0);
                        if (p == null || p.Message != "backrooms:funstairs") continue;
                        cores++;
                        var home = net.HomeFor(p);
                        var link = net.Take(p, home);
                        int to = link is { } l ? layout.LevelAt(WorldLayout.MacroOf((int)l.X), WorldLayout.MacroOf((int)l.Z)) : -1;
                        string ret = "no way back";
                        if (link is { } l3 && layout.FeatureBeside((int)Math.Floor(l3.X), (int)Math.Floor(l3.Z), Backrooms.Thresholds.ThresholdNetwork.FunStairs) is { } f)
                        {
                            for (int sz = -8; sz <= 8 && ret == "no way back"; sz++)
                                for (int sx = -8; sx <= 8; sx++)
                                {
                                    Tile st = layout.TileAt(f.X + sx, f.Z + sz);
                                    if (!Backrooms.Thresholds.ThresholdNetwork.FunStairs(st) || st.Stair < 2) continue;
                                    var up = net.Walked(f.X + sx, f.Z + sz, st, 3.0);
                                    if (up != null && net.Take(up, null) == home) { ret = "climbed back home"; back++; break; }
                                }
                        }
                        else if (link is { Marker: true }) ret = "thin spot";
                        Console.WriteLine($"  L1 stair core at {p.Source}: -> level {to}, {ret}");
                        break;
                    }
                }
        }
        Console.WriteLine($"Level 1: {cores} stair cores into Level Fun found, {back} climbed back");
    }
}

static partial class LevelModes
{
    /// <summary>funprobe: the middle of one room of each kind near the middle of the region (for headless dumps).</summary>
    static void FunProbe(WorldLayout layout)
    {
        var (x0, z0, size) = FunWindow(layout, 4);
        var (b0, c0) = layout.FunBlockOf(x0, z0);
        var seen = new HashSet<string>();
        for (int j = 0; j < 4; j++) for (int i = 0; i < 4; i++)
            foreach (FunRoom r in layout.FunPlan(b0 + i, c0 + j).Rooms)
            {
                string kind = r.Kind + (r.Guests > 0 ? "+guests" : "");
                if (!seen.Add(kind)) continue;
                Console.WriteLine($"{kind,-16} centre {(r.X0 + r.X1) / 2},{(r.Z0 + r.Z1) / 2} size {r.X1 - r.X0 + 1}x{r.Z1 - r.Z0 + 1} head {r.Head.X},{r.Head.Z} spots {r.Spots.Count}");
            }
        var a = layout.FindArrival(WorldLayout.FunLevel, 99991UL);
        Console.WriteLine($"lobby arrival {a}");
    }
}
