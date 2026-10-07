using Backrooms.Worldgen;
static class Overview {
  public static void Run(WorldLayout l, int smx, int smz, int R, string outPath) {
    int size = 2 * R + 1;
    using (var w = new BinaryWriter(File.Create(outPath))) {
      w.Write(size);
      for (int z = -R; z <= R; z++) for (int x = -R; x <= R; x++) {
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
  }
}
