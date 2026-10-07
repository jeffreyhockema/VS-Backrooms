using Backrooms.Worldgen;
static class Timing
{
    public static void Run(WorldLayout layout, int m0x, int m0z, int n)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        int cells = 0;
        for (int z = 0; z < n; z++) for (int x = 0; x < n; x++) { layout.BuildMacro(m0x + x, m0z + z); cells++; }
        System.Console.WriteLine($"{cells} cells in {sw.ElapsedMilliseconds} ms: {sw.Elapsed.TotalMilliseconds / cells:0.00} ms/cell");
    }
}
