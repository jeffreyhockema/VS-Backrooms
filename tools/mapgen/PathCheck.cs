using Backrooms.Worldgen;

/// <summary>
/// Whether one block position can be walked to from another within a window of cells round them; if not, the size and
/// extent of the first one's component. Usage: mapgen seed cells path ax az bx bz
/// </summary>
static class PathCheck
{
    public static void Run(WorldLayout layout, int n, int ax, int az, int bx, int bz)
    {
        int cmx = WorldLayout.MacroOf((ax + bx) / 2) - n / 2, cmz = WorldLayout.MacroOf((az + bz) / 2) - n / 2;
        int size = n * 32, x0 = cmx * 32, z0 = cmz * 32;
        var tiles = new Tile[size * size];
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                var cell = layout.BuildMacro(cmx + mx, cmz + mz);
                for (int i = 0; i < 1024; i++) tiles[(mz * 32 + i / 32) * size + mx * 32 + i % 32] = cell[i];
            }
        bool Walk(in Tile t) => t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water
            || t.Kind == TileKind.Floor && !t.SupplyBox && !(t.Stack > 0 && t.Variant == 0) && WorldLayoutAccess.Walk(t);
        int start = (az - z0) * size + ax - x0, goal = (bz - z0) * size + bx - x0;
        Console.WriteLine($"start walkable {Walk(tiles[start])} ({tiles[start].Kind}), goal walkable {Walk(tiles[goal])} ({tiles[goal].Kind})");
        var seen = new bool[tiles.Length];
        var q = new Queue<int>();
        seen[start] = true; q.Enqueue(start);
        int count = 0, minX = int.MaxValue, maxX = int.MinValue, minZ = int.MaxValue, maxZ = int.MinValue;
        while (q.Count > 0)
        {
            int i = q.Dequeue(), x = i % size, z = i / size;
            count++; minX = Math.Min(minX, x); maxX = Math.Max(maxX, x); minZ = Math.Min(minZ, z); maxZ = Math.Max(maxZ, z);
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                int j = nz * size + nx;
                if (seen[j] || !Walk(tiles[j])) continue;
                seen[j] = true; q.Enqueue(j);
            }
        }
        Console.WriteLine(seen[goal] ? "reached" : $"NOT reached: component of {count} tiles spanning x {x0 + minX}..{x0 + maxX}, z {z0 + minZ}..{z0 + maxZ}");
    }
}
