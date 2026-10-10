using Backrooms.Worldgen;
static class Overview {
  // overview R [step]: the level of every step-th cell within R cells of spawn, one byte each (overview.bin); a step
  // of 8 or more takes in the regions past the rings (thousands of cells out in a full-size world) in a few seconds
  public static void Run(WorldLayout l, int smx, int smz, int R, string outPath, int step = 1) {
    int n = R / step, size = 2 * n + 1;
    using (var w = new BinaryWriter(File.Create(outPath))) {
      w.Write(size);
      for (int j = -n; j <= n; j++) for (int i = -n; i <= n; i++) {
        int x = i * step, z = j * step;
        int lv = l.LevelAt(smx + x, smz + z);
        byte b = (byte)lv; if (lv == 6 && l.IsSnackrooms(smx + x, smz + z)) b = 11;
        w.Write(b);
      }
    }
    // Distance (in blocks) from spawn to where each level starts, over 72 directions
    for (int level = 1; level <= 10; level++) {
      var ds = new List<double>();
      for (int a = 0; a < 72; a++) {
        double ang = a * Math.PI * 2 / 72;
        for (double r = 1; r < R; r += 0.5) { int lv = l.LevelAt(smx + (int)Math.Round(Math.Cos(ang) * r), smz + (int)Math.Round(Math.Sin(ang) * r));
          if (lv >= level) { ds.Add(r * 32); break; } }
      }
      ds.Sort();
      if (ds.Count > 0) Console.WriteLine($"Level {level,2} starts at: min {ds[0],6:0} median {ds[ds.Count/2],6:0} max {ds[^1],6:0} blocks ({ds.Count}/72 dirs)");
    }
    // The regions past the rings: where each lies (the bounds of its cells seen on the grid) and how many cells it has
    var seen = new Dictionary<int, (int X0, int Z0, int X1, int Z1, int N)>();
    for (int j = -n; j <= n; j++) for (int i = -n; i <= n; i++) {
      int lv = l.LevelAt(smx + i * step, smz + j * step);
      if (lv < 11) continue;
      var s = seen.TryGetValue(lv, out var o) ? o : (int.MaxValue, int.MaxValue, int.MinValue, int.MinValue, 0);
      seen[lv] = (Math.Min(s.Item1, i * step), Math.Min(s.Item2, j * step), Math.Max(s.Item3, i * step), Math.Max(s.Item4, j * step), s.Item5 + 1);
    }
    foreach (var (lv, s) in seen.OrderBy(p => p.Key))
      Console.WriteLine($"Level {WorldLayout.DisplayNumber(lv),4}: cells {s.X0},{s.Z0} to {s.X1},{s.Z1} from spawn (seen on {s.N} grid points, step {step})");
  }
}
