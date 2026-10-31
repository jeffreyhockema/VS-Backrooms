using Backrooms.Worldgen;

/// <summary>
/// l4plan: Level 4's floor and reflected ceiling over <c>cells</c> by <c>cells</c> macro cells (AT= centres it; AT=L4 on the
/// level's first arrival). Writes <c>l4plan.bin</c> for <c>render_l4plan.py</c> (an int size, then per tile: kind, ceiling,
/// overhead, variant, flags (1 worn, 2 stair, 4 sealed), level, pier) and prints, over the Level 4 cells: the sprinkler
/// heads (how many, per 100 m2 of open ceiling, nearest-neighbour spacing, the share of ceiling farther than 3.25 m from
/// a head; heads doubled up beside each other, or with a light or a wall just south of the head, which hangs in its
/// block's south half), the free-standing columns of the open floors (per cell, nearest-neighbour spacing) and the
/// whiteboards (one-block, two-block pairs, halves without their partner).
/// </summary>
static class L4Plan
{
    public static void Run(WorldLayout layout, int m0x, int m0z, int n)
    {
        int size = n * 32;
        var tiles = new Tile[size * size];
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                var cell = layout.BuildMacro(m0x + mx, m0z + mz);
                for (int i = 0; i < cell.Length; i++) tiles[(mz * 32 + i / 32) * size + mx * 32 + i % 32] = cell[i];
            }
        Tile At(int x, int z) => tiles[z * size + x];
        bool In(int x, int z) => x >= 0 && z >= 0 && x < size && z < size;

        using (var w = new BinaryWriter(File.Create("l4plan.bin")))
        {
            w.Write(size);
            foreach (var t in tiles)
            {
                w.Write((byte)t.Kind); w.Write((byte)t.Ceiling); w.Write(t.Overhead); w.Write((byte)Math.Min((int)t.Variant, 255));
                w.Write((byte)((t.Worn ? 1 : 0) | (t.Stair != 0 ? 2 : 0) | (t.Sealed ? 4 : 0))); w.Write(t.Level); w.Write((byte)t.Pier);
            }
        }

        var heads = new List<(double X, double Z)>();
        int doubled = 0, southLight = 0, southWall = 0, ceilingTiles = 0, l4cells = 0;
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                Tile t = At(x, z);
                if (t.Level != 4 || t.IsWallLike || t.Kind != TileKind.Floor) continue;
                if (t.Stair == 0) ceilingTiles++;
                if (t.Overhead != Overheads.CeilingSprinkler) continue;
                heads.Add((x + 0.5, z + 0.75));
                for (int dz = -1; dz <= 1; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                        if ((dx != 0 || dz != 0) && In(x + dx, z + dz) && At(x + dx, z + dz).Overhead == Overheads.CeilingSprinkler && !At(x + dx, z + dz).IsWallLike) doubled++;
                if (In(x, z + 1))
                {
                    Tile s = At(x, z + 1);
                    if (s.IsWallLike) southWall++;
                    else if (s.Ceiling != CeilingKind.Tile) southLight++;
                }
            }
        for (int mz = 0; mz < n; mz++) for (int mx = 0; mx < n; mx++) if (layout.LevelAt(m0x + mx, m0z + mz) == 4) l4cells++;
        Console.WriteLine($"Level 4 cells: {l4cells} of {n * n}; floor tiles under the ceiling: {ceilingTiles}");
        Console.WriteLine($"sprinkler heads: {heads.Count} ({100.0 * heads.Count / Math.Max(1, ceilingTiles):0.0} per 100 m2 of floor)");
        Console.WriteLine($"  doubled up (another head in the 8 tiles round it): {doubled / 2} pairs; light just south of the head: {southLight}; wall just south: {southWall}");
        // Nearest-neighbour spacing (grid buckets for speed)
        var bucket = new Dictionary<(int, int), List<int>>();
        for (int i = 0; i < heads.Count; i++)
        {
            var k = ((int)(heads[i].X / 8), (int)(heads[i].Z / 8));
            if (!bucket.TryGetValue(k, out var l)) bucket[k] = l = new List<int>();
            l.Add(i);
        }
        double Nearest(double x, double z, int skip)
        {
            double best = double.MaxValue;
            int bx = (int)(x / 8), bz = (int)(z / 8);
            for (int dz = -1; dz <= 1; dz++)
                for (int dx = -1; dx <= 1; dx++)
                    if (bucket.TryGetValue((bx + dx, bz + dz), out var l))
                        foreach (int j in l)
                        {
                            if (j == skip) continue;
                            double d = Math.Sqrt((heads[j].X - x) * (heads[j].X - x) + (heads[j].Z - z) * (heads[j].Z - z));
                            if (d < best) best = d;
                        }
            return best;
        }
        var hist = new SortedDictionary<int, int>();
        double sum = 0; int counted = 0;
        for (int i = 0; i < heads.Count; i++)
        {
            double d = Nearest(heads[i].X, heads[i].Z, i);
            if (d == double.MaxValue) continue;
            int b = (int)Math.Floor(d * 2) ; // half-metre bins
            hist[b] = hist.GetValueOrDefault(b) + 1;
            sum += d; counted++;
        }
        Console.WriteLine($"  nearest-neighbour spacing: mean {sum / Math.Max(1, counted):0.00} m; by half metre: " + string.Join(", ", hist.Select(kv => $"{kv.Key / 2.0:0.0}-{kv.Key / 2.0 + 0.5:0.0}: {kv.Value}")));
        int far = 0;
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                Tile t = At(x, z);
                if (t.Level != 4 || t.Kind != TileKind.Floor || t.Stair != 0) continue;
                if (Nearest(x + 0.5, z + 0.5, -1) > 3.25) far++;
            }
        Console.WriteLine($"  floor tiles farther than 3.25 m from a head: {far} ({100.0 * far / Math.Max(1, ceilingTiles):0.0}%)");

        // Free-standing columns: a lone wall tile on a Level 4 floor, every tile round it open
        var cols = new List<(int X, int Z)>();
        for (int z = 1; z < size - 1; z++)
            for (int x = 1; x < size - 1; x++)
            {
                Tile t = At(x, z);
                if (t.Level != 4 || t.Kind != TileKind.Wall) continue;
                bool lone = true;
                for (int dz = -1; dz <= 1 && lone; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                        if ((dx != 0 || dz != 0) && At(x + dx, z + dz).IsWallLike) { lone = false; break; }
                if (lone) cols.Add((x, z));
            }
        double csum = 0; int cn = 0;
        var chist = new SortedDictionary<int, int>();
        foreach (var c in cols)
        {
            double best = double.MaxValue;
            foreach (var o in cols)
                if (o != c && Math.Abs(o.X - c.X) <= 40 && Math.Abs(o.Z - c.Z) <= 40)
                    best = Math.Min(best, Math.Sqrt((o.X - c.X) * (o.X - c.X) + (o.Z - c.Z) * (o.Z - c.Z)));
            if (best == double.MaxValue) continue;
            csum += best; cn++;
            chist[(int)best] = chist.GetValueOrDefault((int)best) + 1;
        }
        Console.WriteLine($"free-standing columns: {cols.Count} ({(double)cols.Count / Math.Max(1, l4cells):0.0} per Level 4 cell), nearest-neighbour mean {csum / Math.Max(1, cn):0.0} m; by metre: " + string.Join(", ", chist.Select(kv => $"{kv.Key}: {kv.Value}")));

        // Whiteboards
        int single = 0, pairs = 0, orphans = 0;
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                Tile t = At(x, z);
                if (t.Kind != TileKind.Wall || t.Level != 4) continue;
                if (t.Variant == Decor.Whiteboard) single++;
                if (t.Variant != Decor.WhiteboardLeft && t.Variant != Decor.WhiteboardRight) continue;
                // The left half is on the larger coordinate facing north or east, the smaller facing south or west
                int lx = t.Pier switch { ArchPier.North => 1, ArchPier.South => -1, _ => 0 }, lz = t.Pier switch { ArchPier.East => 1, ArchPier.West => -1, _ => 0 };
                int s = t.Variant == Decor.WhiteboardLeft ? -1 : 1;
                int px = x + s * lx, pz = z + s * lz;
                bool ok = In(px, pz) && At(px, pz) is { Kind: TileKind.Wall } p && p.Pier == t.Pier
                          && p.Variant == (t.Variant == Decor.WhiteboardLeft ? Decor.WhiteboardRight : Decor.WhiteboardLeft);
                if (!ok) orphans++;
                else if (t.Variant == Decor.WhiteboardLeft) pairs++;
            }
        Console.WriteLine($"whiteboards: {single} one block wide, {pairs} two wide, {orphans} halves without their partner");
    }
}
