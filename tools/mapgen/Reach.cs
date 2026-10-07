using Backrooms.Worldgen;

/// <summary>
/// Global reachability across a level's outer boundary: a window of cells centred where the level meets the next one
/// (straight out from spawn at an angle) is flooded from the level's floor nearest the middle. Reports walkable floor of
/// the level that is not marked sealed yet cannot be reached: pockets the per-cell sealing cannot see, such as rooms cut
/// off from their block by the wall between levels. Tiles near the window's border are ignored (their way round may
/// lie outside it).
/// Usage: mapgen seed cells reach level angle
/// </summary>
static class Reach
{
    public static void Run(WorldLayout layout, int smx, int smz, int n, int level, double angleDeg, int counted = -1)
    {
        double ang = angleDeg * Math.PI / 180;
        int cx = smx, cz = smz;
        for (double r = 1; r < 900; r += 0.5)
        {
            int mx = smx + (int)Math.Round(Math.Cos(ang) * r), mz = smz + (int)Math.Round(Math.Sin(ang) * r);
            if (layout.LevelAt(mx, mz) > level) { cx = mx; cz = mz; break; }
        }
        int size = n * 32, x0 = (cx - n / 2) * 32, z0 = (cz - n / 2) * 32;
        var tiles = new Tile[size * size];
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                var cell = layout.BuildMacro(cx - n / 2 + mx, cz - n / 2 + mz);
                for (int i = 0; i < 1024; i++) tiles[(mz * 32 + i / 32) * size + mx * 32 + i % 32] = cell[i];
            }
        bool Walk(in Tile t) => t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water
            || t.Kind == TileKind.Floor && !t.SupplyBox && !(t.Stack > 0 && t.Variant == 0) && WorldLayoutAccess.Walk(t);
        if (counted < 0) counted = level;
        // (Level 6.1, the Snackrooms, is sealed on purpose: it can only be fallen into)
        bool Ours(int i) => tiles[i].Level == counted && !(counted == 6 && tiles[i].Zone == 1) && Walk(tiles[i]);

        // Split the level's floor in the window into connected pieces. The largest is the level; a piece that touches
        // the window's border may go on outside it. Any other piece is a true pocket.
        var piece = new int[tiles.Length];
        var pieceSize = new List<int> { 0 };
        var touchesBorder = new List<bool> { false };
        var q = new Queue<int>();
        for (int s = 0; s < tiles.Length; s++)
        {
            if (piece[s] != 0 || !Ours(s)) continue;
            int id = pieceSize.Count, count = 0;
            bool border = false;
            pieceSize.Add(0); touchesBorder.Add(false);
            piece[s] = id; q.Enqueue(s);
            while (q.Count > 0)
            {
                int i = q.Dequeue(), x = i % size, z = i / size;
                count++;
                border |= x == 0 || z == 0 || x == size - 1 || z == size - 1;
                foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    int nx = x + dx, nz = z + dz;
                    if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                    int j = nz * size + nx;
                    if (piece[j] != 0 || !Ours(j)) continue;
                    piece[j] = id; q.Enqueue(j);
                }
            }
            pieceSize[id] = count;
            touchesBorder[id] = border;
        }
        int main = 0;
        for (int id = 1; id < pieceSize.Count; id++) if (pieceSize[id] > pieceSize[main]) main = id;
        int total = 0, lost = 0, sealedCount = 0;
        var examples = new List<(int, int)>();
        for (int z = 0; z < size; z++)
            for (int x = 0; x < size; x++)
            {
                int i = z * size + x;
                if (!Ours(i)) continue;
                total++;
                if (tiles[i].Sealed) { sealedCount++; continue; }
                if (piece[i] == main || touchesBorder[piece[i]]) continue;
                lost++;
                if (examples.Count < 8 && !examples.Exists(e => Math.Abs(e.Item1 - x0 - x) + Math.Abs(e.Item2 - z0 - z) < 20)) examples.Add((x0 + x, z0 + z));
            }
        Console.WriteLine($"level {level} boundary at cell {cx},{cz}: {total} walkable, {sealedCount} sealed, {lost} unreachable but unsealed ({100.0 * lost / Math.Max(1, total):0.00}%)");
        foreach (var e in examples) Console.WriteLine($"  e.g. {e}");
    }
}
