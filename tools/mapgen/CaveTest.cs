using Backrooms.Worldgen;
static class CaveTest {
  // The formulas as they were in WorldGenerator.Deep.cs before the per-column rewrite
  static ulong seed = 12345; const ulong SaltCave = 0xC401, SaltCaveTube = 0xC402, SaltStrata = 0xC403, SaltOre = 0xC404, SaltPool = 0xC405;
  static double Corner2(int x, int z, ulong salt) => Hashing.Unit(Hashing.Hash(seed, x, z, salt)) * 2 - 1;
  static double Noise2(double x, double z, ulong salt) { int x0 = (int)Math.Floor(x), z0 = (int)Math.Floor(z); double fx = x - x0, fz = z - z0;
    double sx = fx * fx * (3 - 2 * fx), sz = fz * fz * (3 - 2 * fz);
    double c00 = Corner2(x0, z0, salt), c10 = Corner2(x0 + 1, z0, salt), c01 = Corner2(x0, z0 + 1, salt), c11 = Corner2(x0 + 1, z0 + 1, salt);
    double top = c00 + (c10 - c00) * sx, bottom = c01 + (c11 - c01) * sx; return top + (bottom - top) * sz; }
  static double Noise3(double x, double y, double z, ulong salt) { int x0 = (int)Math.Floor(x), y0 = (int)Math.Floor(y), z0 = (int)Math.Floor(z);
    double fx = x - x0, fy = y - y0, fz = z - z0; double sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy), sz = fz * fz * (3 - 2 * fz);
    double Layer(int yy) { ulong s = salt + (ulong)(yy * 0x9E3779B1L);
      double c00 = Corner2(x0, z0, s), c10 = Corner2(x0 + 1, z0, s), c01 = Corner2(x0, z0 + 1, s), c11 = Corner2(x0 + 1, z0 + 1, s);
      double top = c00 + (c10 - c00) * sx, bottom = c01 + (c11 - c01) * sx; return top + (bottom - top) * sz; }
    double a = Layer(y0), b = Layer(y0 + 1); return a + (b - a) * sy; }
  static bool IsCave(int gx, int y, int gz, int floorY) { int rel = y - floorY; if (rel > 8 || rel < -62) return false;
    double fade = rel > 4 ? (rel - 4) * 0.08 : rel < -50 ? (-50 - rel) * 0.05 : 0;
    double chamber = Noise3(gx / 26.0, y / 11.0, gz / 26.0, SaltCave) + 0.45 * Noise3(gx / 10.0, y / 6.0, gz / 10.0, SaltCave + 1);
    if (chamber - fade > 0.42) return true; double tube = Math.Abs(Noise3(gx / 38.0, y / 14.0, gz / 38.0, SaltCaveTube)); return tube + fade < 0.055; }
  public static void Run() {
    int floorY = 217, bandBottom = floorY - 30, bandTop = floorY + 9; var rng = new Random(3); int bad = 0, caves = 0, n = 0;
    for (int i = 0; i < 3000; i++) {
      int gx = rng.Next(500000, 530000), gz = rng.Next(500000, 530000);
      var col = new CaveColumn(seed, gx, gz, floorY, bandBottom - 41, bandTop + 1, Noise2, SaltCave, SaltCaveTube, SaltStrata, SaltOre, SaltPool);
      if (col.StrataShift != (int)(9 * Noise2(gx / 70.0, gz / 70.0, SaltStrata))) bad++;
      if (col.Pool != (Noise2(gx / 30.0, gz / 30.0, SaltPool) > 0.2)) bad++;
      if (col.Tar != (Noise2(gx / 25.0, gz / 25.0, SaltPool + 3) > 0.62)) bad++;
      if (col.CoalSeam != (Hashing.Mod(gx + 3 * gz, 197) == 0 && Noise2(gx / 50.0, gz / 50.0, SaltOre + 9) > 0.2)) bad++;
      for (int y = bandBottom - 41; y <= bandTop + 1; y++) { n++;
        bool a = IsCave(gx, y, gz, floorY), b = col.IsCave(y); if (a) caves++; if (a != b) bad++;
        if (Math.Abs(Noise3(gx / 6.0, y / 4.0, gz / 6.0, SaltOre) - col.Ore(y)) > 1e-12) bad++; }
    }
    Console.WriteLine($"{n} blocks checked, {caves} cave, {bad} mismatches");
  }

  /// <summary>
  /// ore: Level 8's ore as bodies (layout versions 1-4) and as veins and pockets (5), over the same columns: ore blocks
  /// per 1000 of rock, metal units (30/40/50 by grade, as vanilla's common ores), and the share of the rock faces open
  /// to a cave that are ore (what you see on the walls).
  /// </summary>
  public static void OreRun() {
    int floorY = 217, yMin = floorY - 62, yMax = floorY + 8; var rng = new Random(5);
    foreach (bool veins in new[] { false, true }) {
      long rock = 0, ore = 0, units = 0, faces = 0, oreFaces = 0; var grades = new long[3];
      for (int i = 0; i < 3000; i++) {
        int gx = rng.Next(500000, 530000), gz = rng.Next(500000, 530000);
        CaveColumn Col(int x, int z) => new CaveColumn(seed, x, z, floorY, yMin - 41, yMax + 1, Noise2, SaltCave, SaltCaveTube, SaltStrata, SaltOre, SaltPool, veins);
        var col = Col(gx, gz); var sides = new[] { Col(gx + 1, gz), Col(gx - 1, gz), Col(gx, gz + 1), Col(gx, gz - 1) };
        for (int y = yMin; y <= yMax; y++) {
          if (col.IsCave(y)) continue; rock++;
          int g = col.OreGrade(y); if (g >= 0) { ore++; grades[g]++; units += 30 + 10 * g; }
          int open = (col.IsCave(y + 1) ? 1 : 0) + (col.IsCave(y - 1) ? 1 : 0); foreach (var c in sides) if (c.IsCave(y)) open++;
          faces += open; if (g >= 0) oreFaces += open;
        }
      }
      // A wall's worth of rock, seen side on (x across, y up): # ore, . rock, space cave
      for (int y = floorY + 6; y >= floorY - 20; y--) {
        var line = new System.Text.StringBuilder("  ");
        for (int x = 0; x < 100; x++) { var c = new CaveColumn(seed, 512000 + x, 512000, floorY, yMin - 41, yMax + 1, Noise2, SaltCave, SaltCaveTube, SaltStrata, SaltOre, SaltPool, veins);
          line.Append(c.IsCave(y) ? ' ' : c.OreGrade(y) >= 0 ? '#' : '.'); }
        Console.WriteLine(line); }
      Console.WriteLine($"{(veins ? "veins (5)" : "bodies (1-4)"),-13}: ore {1000.0 * ore / rock:0.0} per 1000 rock, units {1000.0 * units / rock:0} per 1000 rock, grades poor/medium/rich {grades[0]}/{grades[1]}/{grades[2]}, cave faces that are ore {100.0 * oreFaces / faces:0.0}%");
    }
  }
}
