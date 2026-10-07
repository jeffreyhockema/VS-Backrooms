using Backrooms.Worldgen;
static class ChalkStats
{
    public static void Run(WorldLayout layout, int smx, int smz, int radius)
    {
        var marks = new int[12]; var cells = new int[12]; string first = null;
        var sw = System.Diagnostics.Stopwatch.StartNew();
        for (int mz = smz - radius; mz <= smz + radius; mz += 2)
            for (int mx = smx - radius; mx <= smx + radius; mx += 2)
            {
                var tiles = layout.BuildMacro(mx, mz); int l = tiles[0].Level; if (l > 11) continue; cells[l]++;
                for (int i = 0; i < tiles.Length; i++) if (tiles[i].Chalk != 0) { marks[l]++; first ??= $"{mx * 32 + i % 32} {mz * 32 + i / 32} {ChalkBits.Symbols[ChalkBits.Symbol(tiles[i].Chalk)]} wall {ChalkBits.Wall(tiles[i].Chalk)}"; }
            }
        for (int l = 0; l < 12; l++) if (cells[l] > 0) Console.WriteLine($"L{l}: {marks[l] / (double)cells[l]:0.00} chalk marks per cell");
        Console.WriteLine($"first: {first}; {sw.ElapsedMilliseconds} ms");
        var spawn = layout.FindSpawn();
        foreach (var lv in new[] { 0 })
        {
            var t0 = sw.ElapsedMilliseconds;
            Console.WriteLine($"door from spawn: {layout.NearestGate(spawn.X, spawn.Z, 0, 1200, 1)}, way: {layout.NearestThreshold(spawn.X, spawn.Z, 0, 320)}, cache: {layout.NearestCache(spawn.X, spawn.Z, 0, 256)}, refuge: {layout.NearestRefuge(spawn.X, spawn.Z, 0, 1600)} ({sw.ElapsedMilliseconds - t0} ms)");
        }
    }
}
