using Backrooms.Worldgen;
/// <summary>
/// barnwalls [n]: from n Level 10 arrival spots, how often the notes' barn-wall mark finds a barn wall that isn't quite there
/// (the city's way in) within 480, 960, 2000 and 4000 blocks (WorldLayout.NearestBarnWall, field by field), how far the
/// nearest is, and what a search costs. Run with LAYOUT_VERSION=12 (one barn in nine) and 16 (one in five).
/// </summary>
static class BarnWalls {
  public static void Run(WorldLayout l, int n) {
    int[] radii = { 480, 960, 2000, 4000 };
    var hits = new int[radii.Length]; var sw = new System.Diagnostics.Stopwatch(); long searches = 0;
    var dists = new List<double>();
    int spots = 0;
    for (ulong k = 1; k <= (ulong)n; k++) {
      if (l.FindArrival(10, k * 7919UL + 17) is not { } a) continue;
      spots++;
      for (int r = 0; r < radii.Length; r++) {
        sw.Start(); var w = l.NearestBarnWall(a.X, a.Z, radii[r]); sw.Stop(); searches++;
        if (w is { } p) { hits[r]++; if (r == radii.Length - 1) dists.Add(Math.Sqrt((double)(p.X - a.X) * (p.X - a.X) + (double)(p.Z - a.Z) * (p.Z - a.Z))); }
      }
    }
    Console.WriteLine($"layout version {l.Version}: barn wall share {l.NoclipBarnShare:0.####}; {spots} Level 10 arrivals");
    for (int r = 0; r < radii.Length; r++) Console.WriteLine($"  within {radii[r],5} blocks: found from {hits[r]}/{spots} ({100.0 * hits[r] / Math.Max(1, spots):0}%)");
    dists.Sort();
    if (dists.Count > 0) Console.WriteLine($"  nearest (within 4000): median {dists[dists.Count / 2]:0} blocks, 90th percentile {dists[(int)(dists.Count * 0.9)]:0}");
    Console.WriteLine($"  cost: {sw.Elapsed.TotalMilliseconds / Math.Max(1, searches):0.00} ms a search on average ({searches} searches)");
    // The field-by-field search against a scan of every tile within 600 blocks, from a few arrivals: the same nearest wall
    int same = 0, tried = 0;
    for (ulong k = 1; k <= 6; k++) {
      if (l.FindArrival(10, k * 7919UL + 17) is not { } a) continue;
      (int X, int Z)? brute = null; long bd = long.MaxValue;
      for (int dz = -600; dz <= 600; dz++) for (int dx = -600; dx <= 600; dx++) {
        long d = (long)dx * dx + (long)dz * dz; if (d > 600L * 600 || d >= bd) continue;
        var t = l.TileAt(a.X + dx, a.Z + dz); if (t.Level == 10 && t.Under == Unders.Noclip) { brute = (a.X + dx, a.Z + dz); bd = d; } }
      tried++; if (brute == l.NearestBarnWall(a.X, a.Z, 600)) same++;
      else Console.WriteLine($"  MISMATCH from {a.X},{a.Z}: tile scan {brute}, field search {l.NearestBarnWall(a.X, a.Z, 600)}");
    }
    Console.WriteLine($"  check against a tile scan (600 blocks): {same}/{tried} the same");
  }
}
