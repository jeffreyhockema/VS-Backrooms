using Backrooms.Worldgen;

/// <summary>
/// Levels 37 and 94, the noclip regions past the rings:
///   regions                       where they lie, arrivals (found, wrong level, trapped), time per cell
///   regionmap &lt;37|94&gt; [dx dz]     writes region.bin round the region's middle (offset in cells) for render_region.py
///   poolstats [blocks]            Level 37: dry, shallow, deep and lit shares, rooms by kind, thresholds
///   motionstats [cells]           Level 94: what stands on the hills, roads, towns, thresholds, steepest step
/// </summary>
static class Regions
{
    static WorldLayout layout;
    static readonly Dictionary<(int, int), Tile[]> cache = new();

    static Tile At(int x, int z)
    {
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        if (!cache.TryGetValue((mx, mz), out var t)) cache[(mx, mz)] = t = layout.BuildMacro(mx, mz);
        return t[WorldLayout.TileIndex(x - mx * 32, z - mz * 32)];
    }

    static bool Passable(Tile t) => t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water
        || t.Kind == TileKind.Floor && (t.Variant == 0 || RegionAccess.WalkThrough(t.Variant)) && !t.SupplyBox && t.Stack == 0;

    /// <summary>How many tiles can be reached from a spot, up to a limit, stepping no more than one block up (Level 94).</summary>
    static int Reach(int sx, int sz, int limit, bool heights)
    {
        var seen = new HashSet<(int, int)> { (sx, sz) };
        var q = new Queue<(int, int)>();
        q.Enqueue((sx, sz));
        while (q.Count > 0 && seen.Count < limit)
        {
            var (x, z) = q.Dequeue();
            Tile here = At(x, z);
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                var n = (x + dx, z + dz);
                if (seen.Contains(n)) continue;
                Tile t = At(n.Item1, n.Item2);
                if (!Passable(t) && !(t.Variant == Props.TwilightGate)) continue;
                if (heights && t.Height - here.Height > 1 && t.Stair == 0) continue;
                seen.Add(n);
                q.Enqueue(n);
            }
        }
        return seen.Count;
    }

    public static void Run(WorldLayout l, int smx, int smz)
    {
        layout = l;
        foreach (int level in new[] { WorldLayout.Poolrooms, WorldLayout.Motion })
        {
            string name = WorldLayout.DisplayNumber(level);
            // Where is it, and does any ring reach it?
            int cells = 0, nearest = int.MaxValue;
            for (int a = 0; a < 360; a += 2)
            {
                double ang = a * Math.PI / 180;
                for (int r = 0; r < 6000; r += 4)
                {
                    int lv = l.LevelAt(smx + (int)(Math.Cos(ang) * r), smz + (int)(Math.Sin(ang) * r));
                    if (lv == level) { nearest = Math.Min(nearest, r); cells++; break; }
                    if (lv < 10 && r > 1000) break;
                }
            }
            Console.WriteLine($"Level {name}: nearest {nearest} cells ({nearest * 32 / 1000.0:0.0} km) from spawn, seen in {cells}/180 directions");
            var sw = System.Diagnostics.Stopwatch.StartNew();
            int found = 0, wrong = 0, small = 0;
            const int N = 60;
            for (ulong k = 1; k <= N; k++)
            {
                var a = l.FindArrival(level, k * 7919UL + 13);
                if (a == null) continue;
                found++;
                var (x, z) = a.Value;
                if (At(x, z).Level != level) wrong++;
                if (Reach(x, z, 3000, level == WorldLayout.Motion) < 3000) small++;
            }
            Console.WriteLine($"  arrivals: found {found}/{N}, wrong level {wrong}, in pockets under 3000 tiles {small}  ({sw.ElapsedMilliseconds} ms)");
        }
        // Time to build cells, cold
        foreach (int level in new[] { WorldLayout.Poolrooms, WorldLayout.Motion })
        {
            var a = l.FindArrival(level, 99991UL);
            if (a == null) continue;
            int mx = WorldLayout.MacroOf(a.Value.X), mz = WorldLayout.MacroOf(a.Value.Z);
            var sw = System.Diagnostics.Stopwatch.StartNew();
            int n = 0;
            for (int dz = 10; dz < 18; dz++) for (int dx = 10; dx < 18; dx++) { l.BuildMacro(mx + dx, mz + dz); n++; }
            Console.WriteLine($"Level {WorldLayout.DisplayNumber(level)}: {sw.Elapsed.TotalMilliseconds / n:0.00} ms per cell (cold)");
        }
    }

    public static void Map(WorldLayout l, int level, int n, int dx, int dz)
    {
        layout = l;
        var a = l.FindArrival(level, 99991UL) ?? (0, 0);
        int cmx = WorldLayout.MacroOf(a.X) + dx, cmz = WorldLayout.MacroOf(a.Z) + dz;
        if (level == WorldLayout.Motion && dx == 0 && dz == 0) { cmx = WorldLayout.MacroOf(l.MotionOriginX); cmz = WorldLayout.MacroOf(l.MotionOriginZ); }
        int m0x = cmx - n / 2, m0z = cmz - n / 2, size = n * 32;
        using var w = new BinaryWriter(File.Create("region.bin"));
        w.Write(size); w.Write(level);
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                Tile t = At(m0x * 32 + x, m0z * 32 + z);
                w.Write((byte)t.Kind); w.Write((byte)t.Floor); w.Write((byte)t.Pattern); w.Write(t.Variant); w.Write(t.Depth);
                w.Write(t.Height); w.Write(t.Zone); w.Write(t.Under); w.Write(t.Roof); w.Write((byte)t.Pier); w.Write(t.Stair); w.Write(t.Level);
            }
        Console.WriteLine($"region map of level {WorldLayout.DisplayNumber(level)}: {size}x{size} from blocks {m0x * 32},{m0z * 32}");
    }

    public static void PoolStats(WorldLayout l, int blocks)
    {
        layout = l;
        var a = l.FindArrival(WorldLayout.Poolrooms, 99991UL).Value;
        int x0 = a.X - blocks * 48, z0 = a.Z - blocks * 48, size = blocks * 96;
        var counts = new Dictionary<string, int>();
        void C(string k) => counts[k] = counts.GetValueOrDefault(k) + 1;
        var light = new int[size * size];
        Array.Fill(light, int.MaxValue);
        var q = new Queue<int>();
        int floors = 0;
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                Tile t = At(x0 + x, z0 + z);
                if (t.Level != WorldLayout.Poolrooms) { C("not 37"); continue; }
                if (t.Kind == TileKind.Wall && t.Variant is PoolWalls.Slit or PoolWalls.Arch)
                {
                    C(t.Variant == PoolWalls.Slit ? "slit" : "arch");
                    var (fx, fz) = t.Pier switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
                    int nx = x + fx, nz = z + fz;
                    if (nx >= 0 && nz >= 0 && nx < size && nz < size) { light[nz * size + nx] = 0; q.Enqueue(nz * size + nx); }
                }
                if (t.Kind == TileKind.Door) C("POOL door");
                if (t.Kind != TileKind.Floor) continue;
                floors++;
                C(t.Depth == 0 ? "floor dry" : t.Depth == 1 ? "floor wading" : t.Depth <= 6 ? "floor swimming" : "floor deep pit");
                if (t.Zone == 1) C("reservoir");
                if (t.Under == Unders.TunnelMouth) C("tunnel mouth tile");
                if (t.Under == Unders.PoolCarpet) C("carpet end tile");
                if (t.Under == Unders.PitBottom) C("pit bottom tile");
                if (t.Under == Unders.PoolHole) C("hole tile");
                if (t.Variant == Props.EpsomCrust) C("epsom crust");
                if (t.Variant == Props.PoolLadder) C("ladder");
                if (t.Variant == Props.LostThing) C("lost thing");
                if (t.Variant == Props.RedSprout) C("red sprout");
                if (t.Sealed) C("sealed floor");
            }
        while (q.Count > 0)
        {
            int i = q.Dequeue();
            if (light[i] >= 14) continue;
            int x = i % size, z = i / size;
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                int j = nz * size + nx;
                if (light[j] <= light[i] + 1 || At(x0 + nx, z0 + nz).Kind != TileKind.Floor) continue;
                light[j] = light[i] + 1;
                q.Enqueue(j);
            }
        }
        int lit = 0;
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
                if (light[z * size + x] != int.MaxValue && At(x0 + x, z0 + z).Kind == TileKind.Floor) lit++;
        Console.WriteLine($"Level 37, {size}x{size} round {a}: {floors} floor tiles, lit (within 14 of a slit) {100.0 * lit / Math.Max(1, floors):0.0}%");
        foreach (var (k, v) in counts.OrderBy(p => p.Key)) Console.WriteLine($"  {k,-20} {v,7}  {(k.StartsWith("floor") ? $"{100.0 * v / floors:0.0}%" : "")}");
    }

    public static void MotionStats(WorldLayout l, int n)
    {
        layout = l;
        var counts = new Dictionary<string, (int N, int X, int Z)>();
        void C(string k, int x, int z) { var c = counts.GetValueOrDefault(k); counts[k] = (c.N + 1, c.N == 0 ? x : c.X, c.N == 0 ? z : c.Z); }
        int ox = l.MotionOriginX, oz = l.MotionOriginZ, steep = 0, size = n * 32;
        var sw = System.Diagnostics.Stopwatch.StartNew();
        for (int z = -size / 2; z < size / 2; z++)
            for (int x = -size / 2; x < size / 2; x++)
            {
                int gx = ox + x, gz = oz + z;
                Tile t = At(gx, gz);
                if (t.Level != WorldLayout.Motion) { C("not 94", gx, gz); continue; }
                Tile e = (x & 1) == 0 ? At(gx + 1, gz) : At(gx, gz + 1);
                if (t.Zone == 0 && e.Zone == 0 && t.Roof == 0 && e.Roof == 0 && Math.Abs(t.Height - e.Height) > 1 && t.Stair == 0 && e.Stair == 0
                    && t.Kind == TileKind.Floor && e.Kind == TileKind.Floor)
                {
                    steep++;
                    string why = t.Floor == FloorKind.MotionPath || e.Floor == FloorKind.MotionPath ? "path" : t.Variant != 0 || e.Variant != 0 ? "prop" : "ground";
                    C($"steep {why} {t.Floor}/{e.Floor}", gx, gz);
                }
                if (t.Floor == FloorKind.MotionAsphalt) C("road", gx, gz);
                if (t.Floor == FloorKind.MotionPath) C("path", gx, gz);
                if (t.Stair > 0) C("path stair", gx, gz);
                if (t.Variant == Props.StopSign) C("stop sign", gx, gz);
                if (t.Variant == Props.NoOutletSign) C("no outlet sign", gx, gz);
                if (t.Kind == TileKind.Bars && t.Pattern == WallPattern.Fence) C("fence", gx, gz);
                if (t.Kind == TileKind.Door && t.Under == Unders.DollHouse) C("door to L9", gx, gz);
                if (t.Kind == TileKind.Door && t.Under == Unders.FloodedHouse) C("flooded house door", gx, gz);
                if (t.Variant == Props.TwilightGate) C("twilight gate", gx, gz);
                if (t.Variant == Props.WaterTower && t.Stack == 12) C("water tower", gx, gz);
                if (t.Variant == Props.AlmondFountain && t.Stack == 12) C("fountain (town)", gx, gz);
                if (t.Variant == Props.SirenPole) C("siren pole", gx, gz);
                if (t.Variant == Props.MilkVan) C("milk van", gx, gz);
                if (t.Variant == Props.OldCar) C("old car", gx, gz);
                if (t.Variant == Props.FurniturePile) C("furniture pile", gx, gz);
                if (t.Variant == Props.Icebox) C("icebox", gx, gz);
                if (t.Kind == TileKind.Door && t.Pattern == WallPattern.ThroneDoor) C("throne door", gx, gz);
                if (t.Variant == Props.TrialChair) C("trial chair", gx, gz);
                if (t.Zone == 2) C("mountain", gx, gz);
                if (t.Zone is 3 or 4) C("castle", gx, gz);
                if (t.Roof > 0 && t.Kind == TileKind.Floor) C("house floor", gx, gz);
            }
        Console.WriteLine($"Level 94, {size}x{size} round the mountain ({sw.ElapsedMilliseconds} ms): {steep} steps of more than one block between neighbouring ground tiles");
        foreach (var (k, v) in counts.OrderBy(p => p.Key)) Console.WriteLine($"  {k,-20} {v.N,7}  e.g. {v.X},{v.Z}");
    }
}

/// <summary>What the harness needs of the layout's internal rules.</summary>
static class RegionAccess
{
    public static bool WalkThrough(byte variant) => variant is Props.WheelStop or Props.SpeedBump or Props.FloorCable or Props.Bedroll or Props.Crop
        or Props.TallGrass or Props.Reeds or Props.Tripwire or Props.FieldGate or Props.MachineParts or Props.TwilightGate or Props.EpsomCrust or Props.LostThing;
}

static class HeightPeek
{
    public static void Run(WorldLayout l, int cx, int cz, int r)
    {
        for (int z = cz - r; z <= cz + r; z++)
        {
            var line = new System.Text.StringBuilder();
            for (int x = cx - r; x <= cx + r; x++)
            {
                Tile t = l.TileAt(x, z);
                line.Append(t.Kind == TileKind.Floor ? (t.Height % 36).ToString("x1").PadLeft(3) : t.Kind == TileKind.Wall ? "  #" : t.Kind == TileKind.Door ? "  X" : "  |");
            }
            Console.WriteLine(line + $"  z={z}");
        }
    }
}

static class FindReservoir
{
    public static void Run(WorldLayout l)
    {
        var a = l.FindArrival(WorldLayout.Poolrooms, 99991UL).Value;
        for (int r = 0; r < 40000; r += 96)
            for (int k = 0; k < 16; k++)
            {
                double ang = k * Math.PI / 8;
                int x = a.X + (int)(Math.Cos(ang) * r), z = a.Z + (int)(Math.Sin(ang) * r);
                if (l.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) == WorldLayout.Poolrooms && l.IsReservoirAt(x, z) && l.IsReservoir(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)))
                {
                    Console.WriteLine($"reservoir at {x},{z} ({r} blocks from the arrival)");
                    return;
                }
            }
    }
}
