using Backrooms.Worldgen;
static class Bands {
  // Mirrors MenaceSystem.Rate (without the city's subway): 0 safe, 1 heartland, 2 approach, 3 threshold
  public static int Band(WorldLayout l, int gx, int gz, out int level) {
    int mx = WorldLayout.MacroOf(gx), mz = WorldLayout.MacroOf(gz);
    level = l.LevelAt(mx, mz);
    bool snack = level == 6 && l.IsSnackrooms(mx, mz);
    if (snack || l.IsSanctuary(gx, gz, level)) return 0;
    double depth = l.LevelDepth(gx, gz, level); int next = l.BlocksToNextLevel(gx, gz, level);
    var dark = l.DarkPlaceAt(gx, gz, level);
    int band = 1;
    if (depth >= 0.6 || dark == WorldLayout.DarkPlace.Bad) band = 2;
    if (depth >= 0.85 || next <= 40 || dark == WorldLayout.DarkPlace.Worst || l.NearThreshold(gx, gz)) band = 3;
    if ((level == 4 || level == 10) && band == 1) band = 0;
    if (level == 11) band = 1;
    return band;
  }
  public static void Run(WorldLayout l, int smx, int smz, string[] args) {
    double ang = args.Length > 3 ? double.Parse(args[3]) * Math.PI / 180 : 0;
    int lastLevel = -1, lastBand = -1;
    var sw = System.Diagnostics.Stopwatch.StartNew(); int calls = 0;
    for (int r = 0; r < 18000; r += 16) {
      int gx = smx * 32 + 16 + (int)(Math.Cos(ang) * r), gz = smz * 32 + 16 + (int)(Math.Sin(ang) * r);
      int b = Band(l, gx, gz, out int level); calls++;
      if (level != lastLevel || b != lastBand) {
        Console.WriteLine($"r={r,6} ({gx},{gz}) level {level,2} band {b} depth {l.LevelDepth(gx, gz, level):0.00} next {(l.BlocksToNextLevel(gx, gz, level) == int.MaxValue ? -1 : l.BlocksToNextLevel(gx, gz, level))} dark {l.DarkPlaceAt(gx, gz, level)}");
        lastLevel = level; lastBand = b;
      }
      if (level >= 10 && r > 16000) break;
    }
    Console.WriteLine($"{calls} ratings in {sw.ElapsedMilliseconds} ms");
    foreach (int cx in new[] { 512200, 515600, 516700 }) {
      Band(l, cx, 512016, out _);
      var w2 = System.Diagnostics.Stopwatch.StartNew();
      for (int i = 0; i < 200; i++) Band(l, cx + i % 9, 512016 + i % 7, out _);
      Console.WriteLine($"warm at {cx}: {w2.Elapsed.TotalMilliseconds / 200:0.000} ms per rating");
    }
    // Share of each band per level, sampled at random through the rings
    var rng = new Random(1); var counts = new int[12, 4];
    for (int i = 0; i < 6000; i++) {
      double a = rng.NextDouble() * Math.PI * 2, rr = rng.NextDouble() * 15000;
      int gx = smx * 32 + (int)(Math.Cos(a) * rr), gz = smz * 32 + (int)(Math.Sin(a) * rr);
      int b = Band(l, gx, gz, out int level); counts[Math.Min(level, 11), b]++;
    }
    for (int lv = 0; lv < 12; lv++) {
      int tot = 0; for (int b = 0; b < 4; b++) tot += counts[lv, b];
      if (tot == 0) continue;
      Console.WriteLine($"level {lv,2}: safe {100.0*counts[lv,0]/tot,4:0}%  heart {100.0*counts[lv,1]/tot,4:0}%  approach {100.0*counts[lv,2]/tot,4:0}%  threshold {100.0*counts[lv,3]/tot,4:0}%  (n={tot})");
    }
  }
}
