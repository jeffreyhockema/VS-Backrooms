using Backrooms.Worldgen;
static class Wander {
  public static void Run(WorldLayout l, int smx, int smz) {
    var n = new int[12]; var sites = new int[12];
    for (int mz = smz - 300; mz <= smz + 300; mz += 1) for (int mx = smx - 300; mx <= smx + 300; mx += 1) {
      int lv = Math.Min(11, l.LevelAt(mx, mz)); n[lv]++;
      if (l.WandererSite(mx, mz) != null) sites[lv]++;
    }
    for (int lv = 0; lv < 12; lv++) if (n[lv] > 0) Console.WriteLine($"level {lv}: {sites[lv]} of {n[lv]} cells ({100.0 * sites[lv] / n[lv]:0.0}%)");
    // the log's sites: which cells
    foreach (var (x, z) in new[] { (511408, 514128), (511600, 514000), (511568, 513968), (511600, 513840), (511607, 513801), (511632, 513744), (511632, 513776) })
      Console.WriteLine($"{x},{z}: cell {WorldLayout.MacroOf(x)},{WorldLayout.MacroOf(z)} level {l.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z))}");
  }
}
