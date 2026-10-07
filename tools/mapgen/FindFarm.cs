using Backrooms.Worldgen;
static class FindFarm {
  public static void Run(WorldLayout l, int cx, int cz, int n) {
    for (int mz = cz - n; mz <= cz + n; mz++) for (int mx = cx - n; mx <= cx + n; mx++) {
      var t = l.BuildMacro(mx, mz);
      for (int i = 0; i < 1024; i++) if (t[i].Pattern == WallPattern.Silo && t[i].Level == 10) { Console.WriteLine($"silo at macro {mx},{mz}"); return; }
    }
  }
}
