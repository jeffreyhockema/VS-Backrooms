using Backrooms.Worldgen;

/// <summary>
/// Level 0's arched areas (layout version 10): rooms, rooms with fewer than two walkable arch bays, arch doors with a
/// wall on a face, arch windows that look onto a wall or stand alone, orphan piers, arches MendArches would convert
/// (one with no pier at one end or no partner), and walkable floor of the areas that cannot be reached. Mode
/// <c>archcheck [radius in cells, default 30]</c>; every count should be zero but the totals.
/// </summary>
static class ArchCheck {
  static readonly (int dx, int dz)[] D4 = { (1, 0), (-1, 0), (0, 1), (0, -1) };

  /// <summary>archlist [radius]: the arched districts round spawn (origin and size), for <c>peek</c>.</summary>
  public static void List(WorldLayout layout, int smx, int smz, int radiusCells) {
    var seen = new HashSet<string>();
    for (int z = (smz - radiusCells) * 32; z < (smz + radiusCells) * 32; z += 8)
      for (int x = (smx - radiusCells) * 32; x < (smx + radiusCells) * 32; x += 8) {
        if (layout.LevelAt(x >> 5, z >> 5) != 0 || layout.Level0ZoneAt(x, z) != ZoneKind.Arches) continue;
        string d = layout.DescribeLevel0(x, z);
        string key = d[..d.IndexOf(" tile ")];
        if (!seen.Add(key)) continue;
        // at X,Z size WxH: how many arch doors and windows the plan has, and how many rooms (an open hall, the fallback, has none)
        var m = System.Text.RegularExpressions.Regex.Match(key, @"at (-?\d+),(-?\d+) size (\d+)x(\d+)");
        int px = int.Parse(m.Groups[1].Value), pz = int.Parse(m.Groups[2].Value), pw = int.Parse(m.Groups[3].Value), ph = int.Parse(m.Groups[4].Value);
        int ad = 0, aw = 0, boxes = 0;
        for (int tz = 1; tz < ph; tz++) for (int tx = 1; tx < pw; tx++) { Tile t = layout.TileAt(px + tx, pz + tz); if (t.Kind == TileKind.ArchDoor) ad++; else if (t.Kind == TileKind.ArchWindow) aw++; if (t.SupplyBox) boxes++; }
        Console.WriteLine($"{key}: {ad} arch door tiles, {aw} window tiles, {boxes} boxes");
      }
  }

  public static void Run(WorldLayout layout, int smx, int smz, int radiusCells) {
    int x0 = (smx - radiusCells) * 32, z0 = (smz - radiusCells) * 32, N = radiusCells * 64;
    var tiles = new Tile[N * N];
    var arch = new bool[N * N];
    for (int z = 0; z < N; z++)
      for (int x = 0; x < N; x++) {
        Tile t = layout.TileAt(x0 + x, z0 + z);
        tiles[z * N + x] = t;
        arch[z * N + x] = t.Level == 0 && layout.Level0ZoneAt(x0 + x, z0 + z) == ZoneKind.Arches;
      }
    bool In(int x, int z) => x >= 0 && z >= 0 && x < N && z < N;
    bool Archy(Tile t) => t.Kind is TileKind.ArchDoor or TileKind.ArchWindow;

    int districtTiles = 0, doors = 0, windows = 0, piers = 0, stucco = 0;
    int doorOnWall = 0, windowBad = 0, windowAlone = 0, orphans = 0, mends = 0;
    var examples = new List<string>();
    // Where the plan runs out against another level, the hallway the game carves along that wall (EdgeHall) can take an arch or a pier
    // of the plan with it, in every layout version; what lies within four blocks of another level is counted apart
    int border = 0;
    bool NearBorder(int x, int z) {
      for (int dz = -4; dz <= 4; dz++)
        for (int dx = -4; dx <= 4; dx++)
          if (!In(x + dx, z + dz) || tiles[(z + dz) * N + x + dx].Level != 0) return true;
      return false;
    }
    bool Note(string what, int x, int z) {
      if (NearBorder(x, z)) { border++; return false; }
      if (examples.Count < 14) examples.Add($"{what} at {x0 + x},{z0 + z}");
      return true;
    }
    for (int z = 0; z < N; z++)
      for (int x = 0; x < N; x++) {
        Tile t = tiles[z * N + x];
        if (t.Level != 0) continue;
        if (arch[z * N + x]) districtTiles++;
        if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.Stucco) stucco++;
        if (Archy(t)) {
          if (t.Kind == TileKind.ArchDoor) doors++; else windows++;
          (int pdx, int pdz) = t.Pier switch { ArchPier.West => (-1, 0), ArchPier.East => (1, 0), ArchPier.North => (0, -1), _ => (0, 1) };
          bool along = pdx != 0; // the wall runs along x
          bool pierOk = !In(x + pdx, z + pdz) || tiles[(z + pdz) * N + x + pdx].Kind == TileKind.Wall;
          bool partnerOk = !In(x - pdx, z - pdz) || Archy(tiles[(z - pdz) * N + x - pdx]);
          if ((!pierOk || !partnerOk) && Note("mend", x, z)) mends++;
          bool wallFace = false, notFloor = false;
          foreach (int s in new[] { 1, -1 }) {
            int fx = x + (along ? 0 : s), fz = z + (along ? s : 0);
            if (!In(fx, fz)) continue;
            Tile f = tiles[fz * N + fx];
            if (f.Level != 0) continue;
            if (f.Kind is TileKind.Wall or TileKind.ArchWindow) wallFace = true;
            if (f.Kind != TileKind.Floor && f.Kind != TileKind.ArchDoor) notFloor = true;
          }
          if (t.Kind == TileKind.ArchDoor && wallFace && Note("arch onto wall", x, z)) doorOnWall++;
          if (t.Kind == TileKind.ArchWindow) {
            if ((wallFace || notFloor) && Note("window onto wall", x, z)) windowBad++;
            bool door = false;
            for (int k = -5; k <= 5 && !door; k++) {
              int wx = x + (along ? k : 0), wz = z + (along ? 0 : k);
              if (In(wx, wz) && tiles[wz * N + wx].Kind == TileKind.ArchDoor) door = true;
            }
            if (!door && Note("window with no door in its wall", x, z)) windowAlone++;
          }
        }
        if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.Stucco && arch[z * N + x]) {
          piers++;
          bool joined = false;
          foreach (var (dx, dz) in D4) if (In(x + dx, z + dz) && tiles[(z + dz) * N + x + dx].Kind is TileKind.Wall or TileKind.ArchDoor or TileKind.ArchWindow) joined = true;
          if (!joined && Note("orphan pier", x, z)) orphans++;
        }
      }

    // Rooms: pieces of floor of the arched areas, walls and arches between them
    var seen = new bool[N * N];
    int rooms = 0, thin = 0, edgeRooms = 0;
    var queue = new Queue<int>();
    for (int s = 0; s < N * N; s++) {
      if (seen[s] || !arch[s] || tiles[s].Kind != TileKind.Floor) continue;
      var doorSet = new HashSet<int>();
      bool touchesEdge = false;
      int size = 0, sx = s % N, sz = s / N;
      seen[s] = true; queue.Enqueue(s);
      while (queue.Count > 0) {
        int at = queue.Dequeue(); size++;
        int x = at % N, z = at / N;
        if (x == 0 || z == 0 || x == N - 1 || z == N - 1) touchesEdge = true;
        foreach (var (dx, dz) in D4) {
          int nx = x + dx, nz = z + dz;
          if (!In(nx, nz)) { touchesEdge = true; continue; }
          int n = nz * N + nx;
          if (tiles[n].Kind == TileKind.ArchDoor) doorSet.Add(n);
          if (seen[n] || !arch[n] || tiles[n].Kind != TileKind.Floor) continue;
          seen[n] = true; queue.Enqueue(n);
        }
      }
      if (touchesEdge) { edgeRooms++; continue; }
      rooms++;
      if (doorSet.Count < 4 && Note($"room of {size} tiles with {doorSet.Count} arch tiles", sx, sz)) thin++;
    }

    // Floor of the arched areas cut off from the rest: walkable pieces of Level 0, all but the biggest, that lie in an arched area
    var comp = new int[N * N];
    Array.Fill(comp, -1);
    var sizes = new List<int>(); var touches = new List<bool>(); var inArchComp = new List<int>(); var firstTile = new List<int>();
    bool Walk(Tile t) => t.Level == 0 && (t.Kind is TileKind.Floor or TileKind.ArchDoor or TileKind.Doorway or TileKind.Water);
    for (int s = 0; s < N * N; s++) {
      if (comp[s] >= 0 || !Walk(tiles[s])) continue;
      int id = sizes.Count, size = 0, inArch = 0; bool edge = false;
      comp[s] = id; queue.Enqueue(s);
      while (queue.Count > 0) {
        int at = queue.Dequeue(); size++;
        int x = at % N, z = at / N;
        if (arch[at]) inArch++;
        if (x == 0 || z == 0 || x == N - 1 || z == N - 1) edge = true;
        foreach (var (dx, dz) in D4) {
          int nx = x + dx, nz = z + dz;
          if (!In(nx, nz)) continue;
          int n = nz * N + nx;
          if (comp[n] >= 0 || !Walk(tiles[n])) continue;
          comp[n] = id; queue.Enqueue(n);
        }
      }
      sizes.Add(size); touches.Add(edge); inArchComp.Add(inArch); firstTile.Add(s);
    }
    int biggest = 0;
    for (int c = 1; c < sizes.Count; c++) if (sizes[c] > sizes[biggest]) biggest = c;
    int unreachable = 0;
    for (int c = 0; c < sizes.Count; c++)
      if (c != biggest && !touches[c] && inArchComp[c] > 0) { if (Note($"cut-off piece of {sizes[c]} tiles", firstTile[c] % N, firstTile[c] / N)) unreachable += inArchComp[c]; }

    Console.WriteLine($"archcheck, layout version {layout.Version}, within {radiusCells} cells of spawn: arched-area tiles {districtTiles}, stucco walls {stucco}, arch doors {doors}, windows {windows}, piers {piers}");
    Console.WriteLine($"rooms {rooms} (and {edgeRooms} touching the edge of the scan, not counted)");
    Console.WriteLine($"rooms with fewer than two walkable arch bays: {thin}");
    Console.WriteLine($"arch doors with a wall on a face: {doorOnWall}");
    Console.WriteLine($"arch windows outside a room's arcade wall (onto a wall, or no door in the wall): {windowBad + windowAlone}");
    Console.WriteLine($"orphan piers: {orphans}");
    Console.WriteLine($"MendArches conversions (an arch with no pier or no partner): {mends}");
    Console.WriteLine($"unreachable floor of the arched areas: {unreachable}");
    Console.WriteLine($"(left out: {border} problems within four blocks of another level, where the game carves its own hallway through the plan)");
    foreach (string e in examples) Console.WriteLine("  " + e);
  }
}
