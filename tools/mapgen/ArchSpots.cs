using Backrooms.Worldgen;

/// <summary>
/// Level 0's arched areas and where they meet the papered ones: how many boundary walls show the wrong paper to one
/// side, how many arched gaps lead in, and camera spots for a render. Mode <c>archspots</c>.
/// </summary>
static class ArchSpots {
  static readonly (int dx, int dz, double yaw)[] Dirs = { (0, -1, 180), (1, 0, 270), (0, 1, 0), (-1, 0, 90) };

  public static void Run(WorldLayout layout, int smx, int smz, int radiusCells) {
    int x0 = (smx - radiusCells) * 32, z0 = (smz - radiusCells) * 32, x1 = (smx + radiusCells) * 32, z1 = (smz + radiusCells) * 32;
    int archWalls = 0, wrongFaces = 0, splitWalls = 0, archGaps = 0, dotted = 0, chevron = 0, palePaper = 0;
    var spots = new List<string>();
    for (int z = z0; z < z1; z++)
      for (int x = x0; x < x1; x++) {
        Tile t = layout.TileAt(x, z);
        if (t.Level != 0) continue;
        if (t.Kind == TileKind.Wall) {
          if (t.Pattern == WallPattern.Dotted) dotted++;
          else if (t.Pattern == WallPattern.Chevron) chevron++;
          else if (t.Pattern == WallPattern.Cream) palePaper++;
          if (t.Detail != 0) splitWalls++;
        }
        if (t.Kind == TileKind.ArchDoor && layout.Level0ZoneAt(x, z) != ZoneKind.Arches) archGaps++;
        if (t.Kind != TileKind.Wall || t.Pattern != WallPattern.Cream) continue;
        archWalls++;
        for (int d = 0; d < 4; d++) {
          var (dx, dz, yaw) = Dirs[d];
          Tile n = layout.TileAt(x + dx, z + dz);
          if (n.Level != 0 || n.Kind is TileKind.Wall or TileKind.ArchDoor or TileKind.ArchWindow) continue;
          if (layout.Level0ZoneAt(x + dx, z + dz) == ZoneKind.Arches) continue;
          if ((t.Detail & (1 << d)) == 0) wrongFaces++;
          // A camera four blocks out on the papered side, looking back at the wall, if the way there is open
          int cx = x + dx * 4, cz = z + dz * 4;
          bool clear = true;
          for (int k = 1; k <= 4 && clear; k++) { Tile c = layout.TileAt(x + dx * k, z + dz * k); clear = c.Level == 0 && c.Kind == TileKind.Floor; }
          if (clear && spots.Count < 400 && (x + z) % 7 == 0) spots.Add($"wall {x},{z}  camera {cx + 0.5},{cz + 0.5} yaw {yaw}");
        }
      }
    Console.WriteLine($"Level 0 within {radiusCells} cells of spawn: chevron walls {chevron}, dotted {dotted}, pale {palePaper}");
    Console.WriteLine($"pale walls {archWalls}, pale faces looking into papered areas {wrongFaces}, split walls {splitWalls}, arched gaps outside arch areas {archGaps}");
    var rng = new Random(1);
    foreach (string s in spots.OrderBy(_ => rng.Next()).Take(12)) Console.WriteLine(s);
  }
}
