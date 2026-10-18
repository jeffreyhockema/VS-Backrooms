using Backrooms.Worldgen;
// l10stock: how often a player crossing Level 10 is within the creature ring (16-40 blocks) of livestock ground:
// a paddock (IsPasture) or a farmstead's yard (IsFarmyard). Radials out from spawn through Level 10, a sample every 8 blocks.
static class L10Stock {
  public static void Run(WorldLayout l, int smx, int smz) {
    long pts = 0, nearPasture = 0, nearYard = 0, nearMeadow = 0, nearAny = 0, nearNone40 = 0; double longestGap = 0; int radials = 0;
    var gaps = new List<double>();
    for (double ang = 0; ang < 360; ang += 5) {
      double a = ang * Math.PI / 180, rIn = -1, rOut = -1;
      for (double r = 1; r < 3000; r += 0.5) { int lv = l.LevelAt(smx + (int)Math.Round(Math.Cos(a) * r), smz + (int)Math.Round(Math.Sin(a) * r));
        if (lv == 10 && rIn < 0) rIn = r; if (rIn >= 0 && lv != 10) { rOut = r; break; } }
      if (rIn < 0 || rOut < 0) continue;
      radials++; double gap = 0;
      for (double r = rIn * 32; r < rOut * 32; r += 8) {
        int bx = smx * 32 + (int)(Math.Cos(a) * r), bz = smz * 32 + (int)(Math.Sin(a) * r);
        pts++; bool p = false, y = false, m = false;
        for (int dz = -40; dz <= 40 && !(p && y && m); dz += 8) for (int dx = -40; dx <= 40; dx += 8) {
          if (dx * dx + dz * dz > 1600 || dx * dx + dz * dz < 256) continue;
          if (!p && l.IsPasture(bx + dx, bz + dz)) p = true;
          if (!y && l.IsFarmyard(bx + dx, bz + dz)) y = true;
          if (!m && l.IsMeadow(bx + dx, bz + dz)) m = true;
        }
        if (p) nearPasture++; if (y) nearYard++; if (m) nearMeadow++;
        if (p || y || m) { nearAny++; if (gap > 0) { gaps.Add(gap); gap = 0; } } else gap += 8;
        if (gap > longestGap) longestGap = gap;
      }
    }
    for (int ang = 0; ang < 360; ang += 90) { double a = ang * Math.PI / 180; bool found = false; for (double r = 1; r < 3000 && !found; r += 0.5) { int lv = l.LevelAt(smx + (int)Math.Round(Math.Cos(a) * r), smz + (int)Math.Round(Math.Sin(a) * r)); if (lv != 10) continue; for (int s = 0; s < 640 && !found; s += 4) { int bx = smx * 32 + (int)(Math.Cos(a) * r * 32) + s * 4, bz = smz * 32 + (int)(Math.Sin(a) * r * 32); if (l.IsFarmyard(bx, bz)) { Console.WriteLine($"farmyard at {bx} {bz}"); found = true; } else if (l.IsPasture(bx, bz)) { Console.WriteLine($"pasture at {bx} {bz}"); found = true; } } } }
    gaps.Sort();
    Console.WriteLine($"radials through Level 10: {radials}, samples {pts} (8 blocks apart)");
    Console.WriteLine($"ring (16-40 blocks) holds: paddock {100.0 * nearPasture / pts:0.0}%  farmyard {100.0 * nearYard / pts:0.0}%  meadow {100.0 * nearMeadow / pts:0.0}%  any {100.0 * nearAny / pts:0.0}%");
    if (gaps.Count > 0) Console.WriteLine($"stretches with none between encounters (blocks): median {gaps[gaps.Count / 2]:0}  p90 {gaps[gaps.Count * 9 / 10]:0}  longest {longestGap:0}");
  }
}
