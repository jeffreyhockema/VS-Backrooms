using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// The doors and elevators built as ways back (ThresholdNetwork.WayBack.cs), level by level: for many arrivals in each
/// level, what a two-way door and a two-way elevator coming out there would have as their way back, each on a network of
/// its own (as the first one through in a new world): a door or an elevator of the level's own built in a wall beside the
/// arrival, or the thin spot, and a few of each drawn. `wayback [n]` (n arrivals a level, default 100).
static class WayBacks {
  public static void Run(WorldLayout layout, long seed, int n) {
    var geometry = new WorldGeometry(256);
    int[] levels = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, WorldLayout.Poolrooms, WorldLayout.Motion, WorldLayout.RunLevel, WorldLayout.FunLevel,
      WorldLayout.TheEnd, WorldLayout.Hub, WorldLayout.Level974, WorldLayout.Level3999, WorldLayout.Level188 };
    Console.WriteLine($"{"level",-6} {"kind",-9} {"n",4} {"built",6} {"thin",5} {"none",5}  styles (and how far the arrival moved, mean/max steps)");
    foreach (int level in levels)
      foreach (WayBackKind kind in new[] { WayBackKind.Door, WayBackKind.Elevator }) {
        int built = 0, thin = 0, none = 0, drawn = 0; double moved = 0; int maxMoved = 0;
        var styles = new SortedDictionary<string, int>();
        for (int i = 1; i <= n; i++) {
          ulong key = (ulong)i * 7919UL + 13;
          var net = new ThresholdNetwork(layout, geometry, seed);
          (int X, int Z)? first = null;
          var passage = new Passage {
            Source = (-4_000_000 - i, -4_000_000), Key = key, TwoWay = true, WayBack = kind,
            Find = k => { if (layout.FindArrival(level, k) is not { } a) return null; first ??= (a.X, a.Z); return (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)); },
          };
          var home = new Link(0.5, 100, 0.5, false);
          if (net.Take(passage, home) is not { } link) { none++; continue; }
          int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z);
          if (net.WayBackOf(passage.Source) is { } way) {
            built++;
            styles[way.Style.ToString()] = styles.GetValueOrDefault(way.Style.ToString()) + 1;
            if (first is { } f0) { int d = Math.Abs(f0.X - ax) + Math.Abs(f0.Z - az); moved += d; maxMoved = Math.Max(maxMoved, d); }
            // Using it leads home, from every leaf
            foreach (var (tx, tz) in way.Tiles) if (!net.TryGet((tx, tz), out Link back) || back != home) Console.WriteLine($"!!! L{level} {way.Style} at {tx},{tz} does not lead home");
            if (drawn < 1) { drawn++; Draw(layout, level, kind, link, way); }
          }
          else if (link.Marker) thin++;
          else none++;
        }
        string what = string.Join(" ", styles.Select(s => $"{s.Key}x{s.Value}"));
        Console.WriteLine($"L{level,-5} {kind,-9} {n,4} {built,6} {thin,5} {none,5}  {what}{(built > 0 ? $" (moved {moved / built:0.0}/{maxMoved})" : "")}");
      }
  }

  static void Draw(WorldLayout layout, int level, WayBackKind kind, Link link, WayBack way) {
    int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z);
    Console.WriteLine($"--- L{level} {kind}: {way.Style} at {way.X},{way.Z} facing {way.Facing}, arrival {ax},{az} (@ arrival, O door, E elevator leaf; # wall, . floor, s sealed, p prop, X door, D doorway, ~ another level)");
    for (int dz = -5; dz <= 5; dz++) { var line = new System.Text.StringBuilder(); for (int dx = -8; dx <= 8; dx++) { int qx = ax + dx, qz = az + dz; Tile q = layout.TileAt(qx, qz);
      bool door = System.Array.Exists(way.Tiles, t => t.X == qx && t.Z == qz);
      line.Append(qx == ax && qz == az ? '@' : door ? (way.Wide ? 'E' : 'O') : q.Level != level ? '~' : q.Stair > 0 ? (char)('0' + Math.Min(9, (int)q.Stair)) : q.Kind switch { TileKind.Wall => '#', TileKind.Doorway => 'D', TileKind.Door => 'X', TileKind.Bars => '|', TileKind.Floor => q.Sealed ? 's' : q.Variant != 0 || q.Stack != 0 || q.SupplyBox ? 'p' : '.', _ => '?' }); }
      Console.WriteLine(line); }
  }
}
