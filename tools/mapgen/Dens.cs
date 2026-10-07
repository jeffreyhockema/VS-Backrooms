using Backrooms.Worldgen;
static class DenStats
{
    public static void Run(WorldLayout layout, int smx, int smz, int radius)
    {
        var cells = new int[12]; var dens = new Dictionary<(int, DenKind), int>(); var ex = new Dictionary<DenKind, string>();
        for (int mz = smz - radius; mz <= smz + radius; mz++)
            for (int mx = smx - radius; mx <= smx + radius; mx++)
            {
                int l = layout.LevelAt(mx, mz); if (l > 11) continue; cells[l]++;
                var k = layout.DenAt(mx, mz); if (k == DenKind.None) continue;
                dens[(l, k)] = dens.GetValueOrDefault((l, k)) + 1; ex.TryAdd(k, $"{mx * 32 + 16} {mz * 32 + 16} (L{l})");
            }
        foreach (var kv in dens.OrderBy(k => k.Key)) Console.WriteLine($"L{kv.Key.Item1} {kv.Key.Item2}: {kv.Value} ({100.0 * kv.Value / cells[kv.Key.Item1]:0.0}% of cells)");
        foreach (var kv in ex) Console.WriteLine($"  {kv.Key} at {kv.Value}");
    }
}
