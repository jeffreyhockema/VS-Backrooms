using Backrooms.Worldgen;

/// <summary>
/// Dark areas of Level 0 or 1: a block-light estimate over the floor (emitting lights spread one level a block through
/// open tiles, less the room's height), then the connected stretches of floor where it falls under a threshold, with
/// their widest extent. Usage: mapgen seed 1 dark LEVEL [half-size-in-blocks] [centre-x centre-z in macro cells]
/// </summary>
static class DarkAreas {
  public static void Run(WorldLayout layout, int smx, int smz, string[] args) {
    int level = int.Parse(args[3]);
    int half = args.Length > 4 ? int.Parse(args[4]) : 1200;
    int cx = args.Length > 6 ? int.Parse(args[5]) * 32 : smx * 32, cz = args.Length > 6 ? int.Parse(args[6]) * 32 : smz * 32;
    int x0 = cx - half, z0 = cz - half, w = 2 * half;
    int drop = level == 1 ? 4 : 3;
    var tiles = new Tile[w * w];
    int floor = 0;
    for (int z = 0; z < w; z++)
      for (int x = 0; x < w; x++) {
        Tile t = layout.TileAt(x0 + x, z0 + z);
        if (t.Level != level) t.Kind = TileKind.Wall; // outside the level counts as solid
        tiles[z * w + x] = t;
      }
    bool Open(in Tile t) => t.Kind is not (TileKind.Wall or TileKind.Door) && !(t.Kind == TileKind.Pit);
    var lit = new byte[w * w];
    var buckets = new List<int>[32]; for (int i = 0; i < 32; i++) buckets[i] = new List<int>();
    int emit = 0;
    for (int i = 0; i < tiles.Length; i++) {
      Tile t = tiles[i];
      if (t.Level != level) continue;
      int b = 0;
      if (t.Ceiling == CeilingKind.LightOn) b = level == 1 ? 19 : 21;
      else if (level == 1 && t.Ceiling == CeilingKind.LightLit) b = 19;
      else if (t.Ceiling == CeilingKind.LightWarm) b = 13;
      else if (level == 1 && t.Kind == TileKind.Wall && t.Pattern == WallPattern.Pillar && (t.Variant & 8) != 0) b = 14;
      if (b == 0) continue;
      emit++;
      lit[i] = (byte)b; buckets[b].Add(i);
    }
    for (int cur = 31; cur > 0; cur--)
      for (int k = 0; k < buckets[cur].Count; k++) {
        int i = buckets[cur][k];
        if (lit[i] != cur || cur <= 1) continue;
        int x = i % w, z = i / w;
        int[] nb = { x > 0 ? i - 1 : -1, x < w - 1 ? i + 1 : -1, z > 0 ? i - w : -1, z < w - 1 ? i + w : -1 };
        foreach (int n in nb) {
          if (n < 0 || !(Open(tiles[n]))) continue;
          if (lit[n] < cur - 1) { lit[n] = (byte)(cur - 1); buckets[cur - 1].Add(n); }
        }
      }
    if (level == 0) {
      // Mean floor light by zone (the same estimate; arched openings pass light), to compare the zones
      var sum = new Dictionary<ZoneKind, (double light, int n, int dark, int bright)>();
      for (int z = 0; z < w; z += 3)
        for (int x = 0; x < w; x += 3) {
          Tile t = tiles[z * w + x];
          if (t.Level != 0 || t.Kind != TileKind.Floor) continue;
          ZoneKind zone = layout.Level0ZoneAt(x0 + x, z0 + z);
          int v = Math.Max(0, lit[z * w + x] - drop);
          sum.TryGetValue(zone, out var e);
          sum[zone] = (e.light + v, e.n + 1, e.dark + (v < 8 ? 1 : 0), e.bright + (v >= 14 ? 1 : 0));
        }
      foreach (var (zone, e) in sum.OrderBy(k => k.Key))
        Console.WriteLine($"zone {zone}: mean floor light {e.light / e.n:0.0}, under 8: {100.0 * e.dark / e.n:0}%, 14 or more: {100.0 * e.bright / e.n:0}% ({e.n} samples)");
    }
    foreach (int threshold in new[] { 1, 4, 8 }) {
      var seen = new bool[w * w];
      var sizes = new List<(int area, int extent, int px, int pz, int black)>();
      int totalFloor = 0, totalDark = 0;
      for (int i = 0; i < tiles.Length; i++) {
        Tile t = tiles[i];
        if (t.Level != level || t.Kind != TileKind.Floor) continue;
        totalFloor++;
        if (lit[i] - drop >= threshold) continue; // lit
        totalDark++;
      }
      for (int i = 0; i < tiles.Length; i++) {
        Tile t = tiles[i];
        if (seen[i] || t.Level != level || !Open(t) || lit[i] - drop >= threshold) continue;
        int black = 0, minx = int.MaxValue, maxx = int.MinValue, minz = int.MaxValue, maxz = int.MinValue, area = 0;
        var stack = new Stack<int>(); stack.Push(i); seen[i] = true;
        while (stack.Count > 0) {
          int j = stack.Pop(); int x = j % w, z = j / w;
          if (tiles[j].Kind == TileKind.Floor) { area++; if (level == 0 && (j & 3) == 0 && layout.Level0ZoneAt(x0 + x, z0 + z) == ZoneKind.Blackout) black++; }
          minx = Math.Min(minx, x); maxx = Math.Max(maxx, x); minz = Math.Min(minz, z); maxz = Math.Max(maxz, z);
          if (x > 0) Try(j - 1); if (x < w - 1) Try(j + 1); if (z > 0) Try(j - w); if (z < w - 1) Try(j + w);
        }
        void Try(int n) { if (!seen[n] && tiles[n].Level == level && Open(tiles[n]) && lit[n] - drop < threshold) { seen[n] = true; stack.Push(n); } }
        sizes.Add((area, Math.Max(maxx - minx, maxz - minz) + 1, x0 + (minx + maxx) / 2, z0 + (minz + maxz) / 2, 400 * black / Math.Max(1, area)));
      }
      sizes = sizes.Where(s => s.area >= 30).OrderByDescending(s => s.extent).ToList();
      Console.WriteLine($"level {level}, floor light < {threshold}: dark {100.0 * totalDark / Math.Max(1, totalFloor):0.0}% of {totalFloor} floor tiles; regions (>=30 floor tiles): {sizes.Count}");
      foreach (int e in new[] { 32, 64, 100, 150, 200, 300 }) Console.WriteLine($"   extent >= {e}: {sizes.Count(s => s.extent >= e)}");
      foreach (var s in sizes.Take(6)) Console.WriteLine($"   extent {s.extent}, floor tiles {s.area}, centre block {s.px},{s.pz}, {s.black}% in a blackout zone");
    }
    Console.WriteLine($"({emit} light sources in the window; blocks {x0}..{x0 + w}, {z0}..{z0 + w})");
  }
}
