using Backrooms.Worldgen;

/// <summary>
/// layouthash: a fingerprint of the existing levels' layout, to prove a change left them alone. For three worlds (two
/// seeds full size, one small world) it hashes, per level 0-13, the field values (not the bytes, so widening a field
/// does not change the hash) of every tile of up to 24 sample cells and their neighbours, arrivals, temperature and
/// stability at sample points, and the level of a sparse grid of cells (cells of the regions added after Level 94
/// count as the fields, Level 10, which is what they were). Run before and after a change and compare the lines.
/// After the overall hash it prints the same per-level hash for the regions kept as 14 and up (each world), which
/// are not part of the overall hash: compare the lines of the levels that existed before a change.
/// </summary>
static class LayoutHash
{
    sealed class H
    {
        public ulong V = 14695981039346656037UL;
        public void Add(long x) { unchecked { V = (V ^ (ulong)x) * 1099511628211UL; } }
        public void Add(double x) => Add(BitConverter.DoubleToInt64Bits(Math.Round(x, 6)));
    }

    static void AddTile(H h, in Tile t)
    {
        h.Add((long)t.Kind); h.Add((long)t.Pattern); h.Add((long)t.Base); h.Add((long)t.Floor); h.Add((long)t.Ceiling); h.Add((long)t.Pier);
        h.Add(t.Outlet ? 1 : 0); h.Add(t.SupplyBox ? 1 : 0); h.Add(t.Looted ? 1 : 0); h.Add(t.Level); h.Add(t.Tall ? 1 : 0); h.Add(t.Stack);
        h.Add(t.Pipe); h.Add(t.Variant); h.Add(t.Beam ? 1 : 0); h.Add(t.Stair); h.Add(t.ExitSign ? 1 : 0); h.Add(t.Worn ? 1 : 0);
        h.Add(t.Grand ? 1 : 0); h.Add(t.Low ? 1 : 0); h.Add(t.Sealed ? 1 : 0); h.Add(t.Under); h.Add(t.Overhead); h.Add(t.Depth);
        h.Add(t.Roof); h.Add(t.Zone); h.Add(t.Detail); h.Add(t.Height); h.Add(t.Chalk);
    }

    public static void Run(string[] args)
    {
        var worlds = new (long Seed, int Smx)[] { (12345, 16000), (777, 16000), (12345, 1000) };
        var all = new H();
        var extra = new List<string>();
        foreach (var (seed, smx) in worlds)
        {
            var l = new WorldLayout(seed, smx, smx);
            // Sample cells: along 120 rays from spawn, the first few cells of each level met
            var samples = new Dictionary<int, List<(int, int)>>();
            for (int lv = 0; lv < WorldLayout.LevelCount; lv++) samples[lv] = new();
            var grid = new H();
            for (int a = 0; a < 360; a += 3)
            {
                double ang = a * Math.PI / 180;
                int last = -1;
                for (int r = 0; r < Math.Max(1400, smx * 3 / 5); r += 2)
                {
                    int mx = smx + (int)Math.Round(Math.Cos(ang) * r), mz = smx + (int)Math.Round(Math.Sin(ang) * r);
                    int lv = l.LevelAt(mx, mz);
                    grid.Add(lv >= 14 ? 10 : lv);
                    if (lv != last && samples[lv].Count < 24) samples[lv].Add((mx + 1, mz + 1));
                    last = lv;
                }
            }
            Console.WriteLine($"world {seed}/{smx}: level grid {grid.V:x16}");
            extra.Add($"world {seed}/{smx} (regions 14 and up, not in the hash above):");
            for (int lv = 0; lv < WorldLayout.LevelCount; lv++)
            {
                var h = new H();
                foreach (var (cx, cz) in samples[lv])
                    for (int dz = -1; dz <= 1; dz++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            var tiles = l.BuildMacro(cx + dx, cz + dz);
                            foreach (var t in tiles) AddTile(h, t);
                            int gx = (cx + dx) * 32 + 7, gz = (cz + dz) * 32 + 21;
                            h.Add(l.TemperatureAt(gx, 100, gz, 100)); h.Add(l.TemperatureAt(gx, 90, gz, 100));
                            h.Add(l.StabilityAt(gx, 100, gz, 100));
                            h.Add((long)l.DenAt(cx + dx, cz + dz));
                            h.Add(l.IsEntitySpot(gx, gz) ? 1 : 0);
                        }
                for (ulong k = 1; k <= 6; k++)
                {
                    var a = l.FindArrival(lv, k * 7919UL + 13);
                    if (a == null) { h.Add(-1); continue; }
                    h.Add(a.Value.X); h.Add(a.Value.Z); h.Add(l.ArrivalHeight(a.Value.X, a.Value.Z));
                }
                if (lv >= 14) { extra.Add($"  level {lv,2}: {samples[lv].Count,2} cells  {h.V:x16}"); continue; }
                Console.WriteLine($"  level {lv,2}: {samples[lv].Count,2} cells  {h.V:x16}");
                all.Add((long)h.V);
            }
            all.Add((long)grid.V);
            var (sx, sz) = l.FindSpawn();
            all.Add(sx); all.Add(sz);
        }
        Console.WriteLine($"layout hash {all.V:x16}");
        foreach (string line in extra) Console.WriteLine(line);
    }
}
