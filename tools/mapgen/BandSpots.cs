using Backrooms.Worldgen;
/// <summary>
/// bandspots &lt;level&gt; [n]: open floor spots of a level by the director's band (as MenaceSystem.Rate works it out for the ring
/// levels: heartland, approach, threshold; dens left out), n of each, for headless director measurements (straw dummies put down
/// there with /backrooms encounter ... x z). Level 8 also by the 9th Road: "road" (7 to 12 blocks off it, outside its
/// sanctuary) and "offroad" (over 18 off, its worst dark).
/// </summary>
static class BandSpots {
  public static void Run(WorldLayout l, int smx, int smz, int level, int n) {
    var rand = new Random(4242 + level);
    var found = new Dictionary<string, List<(int X, int Z)>>();
    int tries = 0;
    while (tries++ < 400000) {
      int gx = smx * 32 + rand.Next(-9000, 9000), gz = smz * 32 + rand.Next(-9000, 9000);
      if (l.LevelAt(WorldLayout.MacroOf(gx), WorldLayout.MacroOf(gz)) != level) continue;
      var t = l.TileAt(gx, gz);
      if (level != 8 && (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stair != 0)) continue;
      if (l.IsSanctuary(gx, gz, level) || l.DenNear(gx, gz) != null) continue;
      double depth = l.LevelDepth(gx, gz, level); int next = l.BlocksToNextLevel(gx, gz, level);
      var dark = l.DarkPlaceAt(gx, gz, level);
      string band = "heartland";
      if (depth >= 0.5 || dark == WorldLayout.DarkPlace.Bad) band = "approach";
      if (depth >= 0.8 || next <= 40 || dark == WorldLayout.DarkPlace.Worst || l.NearThreshold(gx, gz)) band = "threshold";
      var keys = new List<string> { band };
      if (level == 8) { int road = l.NinthRoadDistance(gx, gz); if (road is >= 7 and <= 12) keys.Add("road"); if (dark == WorldLayout.DarkPlace.Worst) keys.Add("offroad"); }
      foreach (string key in keys) {
        if (!found.TryGetValue(key, out var list)) found[key] = list = new();
        if (list.Count < n && list.All(p => Math.Abs(p.X - gx) + Math.Abs(p.Z - gz) > 400)) {
          list.Add((gx, gz));
          Console.WriteLine($"level {level} {key,-9} {gx} {gz}  band {band}, depth {depth:0.00}, next {(next == int.MaxValue ? -1 : next)}, dark {dark}" + (level == 8 ? $", road {l.NinthRoadDistance(gx, gz)}" : ""));
        }
      }
      if (found.Count > 0 && found.Values.All(v => v.Count >= n) && found.Count >= (level == 8 ? 4 : 3)) break;
    }
  }
}

/// <summary>
/// rigspots: places for the client rig's shots of the feedback round's tells (seed and version as given): the nearest Level 10
/// barn wall that isn't quite there to Level 10's first arrival, with a spot 30 blocks east of it (the wall is a barn's east
/// wall), and the nearest city rowhouse doors to Level 11's first arrival, those that lead to Level 9 and those that do not,
/// each with a spot out in the street in front of it.
/// </summary>
static class RigSpots {
  public static void Run(WorldLayout l) {
    if (l.FindArrival(10, 99991UL) is { } a10 && l.NearestBarnWall(a10.X, a10.Z, 4000) is { } w)
      Console.WriteLine($"barnwall {w.X} {w.Z}  stand {w.X + 30} {w.Z} looking west (heading 270)");
    if (l.FindArrival(11, 99991UL) is not { } a11) return;
    int portals = 0, plain = 0;
    for (int r = 0; r < 600 && (portals < 3 || plain < 2); r++)
      for (int dz = -r; dz <= r; dz++) for (int dx = -r; dx <= r; dx++) {
        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
        int x = a11.X + dx, z = a11.Z + dz;
        var t = l.TileAt(x, z);
        if (t.Kind != TileKind.Door || t.Level != 11 || t.Zone != (byte)CityKind.Rowhouse) continue;
        bool portal = WorldLayout.IsRowhousePortal(t);
        if (portal ? portals >= 3 : plain >= 2) continue;
        // The street side: the way out of the wall with open floor for 6 blocks
        foreach ((int sx, int sz, int heading) in new[] { (0, -1, 180), (0, 1, 0), (1, 0, 270), (-1, 0, 90) }) {
          bool open = true;
          for (int k = 1; k <= 6 && open; k++) { var n = l.TileAt(x + sx * k, z + sz * k); open = n.Kind is TileKind.Floor or TileKind.Doorway; }
          if (!open) continue;
          Console.WriteLine($"rowhouse {(portal ? "portal" : "plain ")} {x} {z}  stand {x + sx * 9} {z + sz * 9} looking at it (heading {heading})");
          if (portal) portals++; else plain++;
          break;
        }
      }
  }
}
