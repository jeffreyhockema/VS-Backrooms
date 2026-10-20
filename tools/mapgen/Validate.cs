using Backrooms.Worldgen;

/// <summary>Checks a region of generated layout for things that would make no sense in game.</summary>
static class Validator
{
    static bool Walkable(in Tile t)
    {
        if (t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water) return true;
        // (Level 8's dark passage round a break in the road is rock tiles in the layout, but a way on)
        if (t.Level == 8 && t.Zone == WorldLayout.L8ZoneCrawl && t.Kind == TileKind.Wall) return true;
        if (t.Kind != TileKind.Floor) return false;
        if (t.Stack > 0 && t.Variant == 0) return false; // crates
        return t.Variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable or Props.Bedroll or Props.SleepingBag or Props.Crop or Props.TallGrass or Props.Reeds or Props.Tripwire or Props.FieldGate or Props.MachineParts
            // (Level Fun's confetti and a tied balloon have no collision: in a Level 1 stair core they lie at the foot of its flight up)
            or Props.FunConfetti or Props.FunBalloonTied
            // (nor have Level 8's glowcaps)
            or Props.GlowcapRed or Props.GlowcapMixed;
    }

    public static void Run(WorldLayout layout, int m0x, int m0z, int n, int spawnX, int spawnZ)
    {
        int size = n * 32;
        var tiles = new Tile[size * size];
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                var cell = layout.BuildMacro(m0x + mx, m0z + mz);
                for (int i = 0; i < 1024; i++) tiles[(mz * 32 + i / 32) * size + mx * 32 + i % 32] = cell[i];
            }
        ref Tile At(int x, int z) => ref tiles[z * size + x];
        bool In(int x, int z) => x >= 0 && z >= 0 && x < size && z < size;

        // Reachability from spawn
        var seen = new bool[size * size];
        var q = new Queue<(int, int)>();
        q.Enqueue((spawnX, spawnZ)); seen[spawnZ * size + spawnX] = true;
        while (q.Count > 0)
        {
            var (x, z) = q.Dequeue();
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (!In(nx, nz) || seen[nz * size + nx] || !Walkable(At(nx, nz))) continue;
                seen[nz * size + nx] = true; q.Enqueue((nx, nz));
            }
        }
        // Orphan regions: walkable, not sealed, not reached. Ignore a 40-block margin (cut off by the render edge).
        // (13 buckets for the ring levels and their two zones; the regions kept as 14 and up count past them)
        var levelTotals = new int[64]; var levelOrphans = new int[64];
        int Bucket(in Tile t) => t.Level == 6 && t.Zone == 1 ? 11 : t.Level == 7 && t.Zone > 0 ? 12 : t.Level;
        var visited = new bool[size * size];
        var regions = new List<(int Size, int X, int Z, int Level)>();
        for (int z = 40; z < size - 40; z++)
            for (int x = 40; x < size - 40; x++)
            {
                Tile t = At(x, z);
                if (!Walkable(t) || t.Sealed) continue;
                levelTotals[Bucket(t)]++;
                if (seen[z * size + x] || visited[z * size + x]) continue;
                int count = 0; var rq = new Queue<(int, int)>(); rq.Enqueue((x, z)); visited[z * size + x] = true;
                while (rq.Count > 0)
                {
                    var (cx, cz) = rq.Dequeue(); count++;
                    foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nx = cx + dx, nz = cz + dz;
                        if (!In(nx, nz) || visited[nz * size + nx] || seen[nz * size + nx] || !Walkable(At(nx, nz)) || At(nx, nz).Sealed) continue;
                        visited[nz * size + nx] = true; rq.Enqueue((nx, nz));
                    }
                }
                levelOrphans[Bucket(t)] += count;
                regions.Add((count, x, z, Bucket(t)));
            }
        for (int l = 0; l < 64; l++)
            if (l < 13 || levelTotals[l] > 0)
                Console.WriteLine($"Level {l}: {levelTotals[l]} walkable tiles, {levelOrphans[l]} unreachable ({100.0 * levelOrphans[l] / Math.Max(1, levelTotals[l]):0.0}%)");
        foreach (var r in regions.OrderByDescending(r => r.Size).Take(12))
            Console.WriteLine($"  unreachable region of {r.Size} at {r.X},{r.Z} (level {r.Level}, cell-local {r.X % 32},{r.Z % 32})");
        int dumps = 0;
        foreach (var r in regions.OrderByDescending(r => r.Size))
        {
            if (dumps >= 6) break;
            if (Environment.GetEnvironmentVariable("DUMP_LEVEL") is string dl && dl != r.Level.ToString()) continue;
            dumps++;
            Console.WriteLine($"--- level {r.Level} around {r.X},{r.Z}");
            for (int z = r.Z - 7; z <= r.Z + 7; z++)
            {
                var line = new System.Text.StringBuilder();
                for (int x = r.X - 20; x <= r.X + 20; x++)
                {
                    if (!In(x, z)) { line.Append(' '); continue; }
                    Tile t = At(x, z);
                    char c = t.Kind switch
                    {
                        TileKind.Wall => t.Variant >= Decor.First ? 'w' : '#',
                        TileKind.Doorway => 'D',
                        TileKind.Door => t.Pattern == WallPattern.Elevator ? 'E' : 'X',
                        TileKind.Bars => '|',
                        TileKind.Pit => 'O',
                        _ => !Walkable(t) ? (t.Stack > 0 && t.Variant == 0 ? 'c' : 'p') : t.Sealed ? '~' : seen[z * size + x] ? '.' : 'u',
                    };
                    if (x == r.X && z == r.Z) c = '@';
                    if (c == '.' && (x % 32 == 0 || z % 32 == 0)) c = ',';
                    line.Append(c);
                }
                Console.WriteLine(line);
            }
        }

        // Doorways must lead somewhere on both sides; props must not stand right in front of them
        int badDoors = 0, blockedDoors = 0, badLifts = 0, badDecor = 0;
        var examples = new List<string>();
        for (int z = 1; z < size - 1; z++)
            for (int x = 1; x < size - 1; x++)
            {
                Tile t = At(x, z);
                if (t.Kind == TileKind.Doorway)
                {
                    bool ew = Walkable(At(x - 1, z)) && Walkable(At(x + 1, z));
                    bool ns = Walkable(At(x, z - 1)) && Walkable(At(x, z + 1));
                    bool ewFloor = At(x - 1, z).Kind == TileKind.Floor && At(x + 1, z).Kind == TileKind.Floor;
                    bool nsFloor = At(x, z - 1).Kind == TileKind.Floor && At(x, z + 1).Kind == TileKind.Floor;
                    if (!ew && !ns)
                    {
                        // Two-wide doorways count their partner as open
                        bool partner = At(x - 1, z).Kind == TileKind.Doorway || At(x + 1, z).Kind == TileKind.Doorway || At(x, z - 1).Kind == TileKind.Doorway || At(x, z + 1).Kind == TileKind.Doorway;
                        if (ewFloor || nsFloor) { blockedDoors++; if (examples.Count < 6) examples.Add($"blocked doorway at {x},{z} L{t.Level}"); }
                        else if (!partner) { badDoors++; if (examples.Count < 20) examples.Add($"doorway to nowhere at {x},{z} L{t.Level}"); }
                    }
                }
                if (t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator && t.Level != 3)
                {
                    // A two-wide elevator: the partner leaf sits beside it along the wall, facing the same way
                    bool alongX = t.Pier is ArchPier.North or ArchPier.South;
                    Tile a = alongX ? At(x - 1, z) : At(x, z - 1), b2 = alongX ? At(x + 1, z) : At(x, z + 1);
                    bool ok = (a.Kind == TileKind.Door && a.Pattern == WallPattern.Elevator && a.Stack != t.Stack && a.Pier == t.Pier)
                           || (b2.Kind == TileKind.Door && b2.Pattern == WallPattern.Elevator && b2.Stack != t.Stack && b2.Pier == t.Pier);
                    // and opens onto somewhere you can stand
                    var (fx, fz) = t.Pier switch { ArchPier.North => (x, z - 1), ArchPier.South => (x, z + 1), ArchPier.East => (x + 1, z), _ => (x - 1, z) };
                    if (!ok || !Walkable(At(fx, fz))) { badLifts++; if (examples.Count < 30) examples.Add($"bad elevator at {x},{z} L{t.Level} facing {t.Pier} ok={ok}"); }
                }
                if (t.Kind == TileKind.Wall && t.Variant >= Decor.First)
                {
                    var (fx, fz) = t.Pier switch { ArchPier.North => (x, z - 1), ArchPier.South => (x, z + 1), ArchPier.East => (x + 1, z), _ => (x - 1, z) };
                    if (At(fx, fz).IsWallLike) { badDecor++; if (examples.Count < 40) examples.Add($"decor {t.Variant} facing a wall at {x},{z} L{t.Level}"); }
                }
            }
        Console.WriteLine($"doorways to nowhere: {badDoors}, doorways blocked by props: {blockedDoors}, bad elevators: {badLifts}, decor facing walls: {badDecor}");
        foreach (var e in examples) Console.WriteLine("  " + e);
    }
}
