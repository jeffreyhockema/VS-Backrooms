using Backrooms.Worldgen;

/// stairs: checks every flight of stairs in a window (by default round spawn; `stairs <level> [count]` round that many
/// arrivals in a level instead). Stairs that climb into the ceiling: nothing stands on a step, and the floor before the
/// first step is clear. The flights of a stairwell of Level 1 or 4 (from layout version 4): six steps in a straight
/// line, numbered from the landing, those below the ceiling on the floor and the rest under the far wall (the first four
/// of a flight down); the landing clear floor; walls on both sides of every step, so nobody falls in sideways; nothing
/// round the shaft that could open into it (another level's cell, or a way into somewhere else under the floor or in the
/// wall); the flight the other way beside it; and in Level 1 every step of both flights, and the painted wall, on the
/// same floor (counted by floor).
static class StairCheck {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static (int, int) Climb(ArchPier p) => p switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };

  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    layout = l; var c = new Dictionary<string,int>(); var ex = new Dictionary<string,string>();
    Scan(m0x, m0z, n, c, ex);
    Print(c, ex);
  }

  public static void RunLevel(WorldLayout l, int level, int n, int count) {
    layout = l; var c = new Dictionary<string,int>(); var ex = new Dictionary<string,string>();
    var seen = new HashSet<(int, int)>();
    for (ulong k = 1; k <= (ulong)count; k++) {
      var a = l.FindArrival(level, k * 99991UL); if (a == null) continue;
      int cx = WorldLayout.MacroOf(a.Value.X) - n / 2, cz = WorldLayout.MacroOf(a.Value.Z) - n / 2;
      if (seen.Add((cx, cz))) Scan(cx, cz, n, c, ex);
    }
    Print(c, ex);
  }

  static void Print(Dictionary<string,int> c, Dictionary<string,string> ex) {
    foreach (var k in c.Keys.OrderBy(k=>k)) Console.WriteLine($"{k}: {c[k]} e.g. {ex[k]}");
    foreach (var k in headKinds.Keys.OrderBy(k=>k)) {
      var (n, bad, least, eg) = headKinds[k];
      Console.WriteLine($"headroom {k}: {n} flights, least {least:0.00}, {(bad == 0 ? "ok" : $"FAIL {bad}")}{(bad > 0 ? " e.g. " + eg : "")}");
    }
    headKinds.Clear();
  }

  // ---- headroom: the player's box (0.6 x 1.85, stepping up at most 0.6, as l9stairs does) walked up each flight over the blocks the
  // generator builds. Covers Level 1's stairs to nowhere (the steps and the dark way on from layout 10) and Level 5's grand
  // staircases, modelled from NowhereBlock / Level1Block and Level5Block in WorldGenerator.cs, which this must be kept in step with.
  const double Half = 0.3, Tall = 1.85, StepUp = 0.6, MinHead = 2.0;
  record struct Box(double X1, double Y1, double Z1, double X2, double Y2, double Z2);
  static readonly Dictionary<string, (int N, int Bad, double Least, string Eg)> headKinds = new();
  static readonly WorldGeometry geo = new(256);

  static int Order(in Tile t) {
    if (t.Level == 5) return t.Grand ? t.Stair : -1;
    if (t.Level != 1 || t.Zone < WorldLayout.FlightZoneNowhere || t.Zone > WorldLayout.NowhereTurn2) return -1;
    if (t.Zone == WorldLayout.FlightZoneNowhere) return t.Stair;
    return t.Zone switch { WorldLayout.NowhereWall => 4, WorldLayout.NowhereRise or WorldLayout.NowhereTurn1 => 5, WorldLayout.NowhereTop or WorldLayout.NowhereTurn2 => 6, _ => 7 };
  }

  /// A block of the stairs' column: 0 air, 1 full, 2 stair (lower half, the upper half on the side it climbs toward).
  static int KindAt(in Tile t, int rel) {
    int top = geo.BandTop - geo.FloorY - 1, v = layout.Version;
    if (t.Level == 5) {
      int room = t.Grand ? WorldGeometry.MaxRoomHeight : WorldGeometry.RoomHeight;
      bool grandStair = t.Grand && t.Stair >= (v >= 13 ? 2 : WorldLayout.GrandStairTripStep);
      if (rel > room + 1) return grandStair && rel == room + 2 ? 0 : 1;
      if (rel == 0) return 1;
      if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? 1 : 2;
      if (rel == room + 1) return grandStair ? 0 : 1;
      if (t.Kind is TileKind.Wall or TileKind.Door) return 1;
      if (t.Kind == TileKind.Doorway) return rel <= 2 ? 0 : 1;
      if (rel == room) return t.Ceiling == CeilingKind.Chandelier || t.Overhead != 0 || (int)t.Pipe != 0 ? 1 : 0;
      return 0;
    }
    const int rm = WorldGeometry.Level1RoomHeight;
    if (v >= 10 && t.Zone >= WorldLayout.FlightZoneNowhere && t.Zone <= WorldLayout.NowhereTurn2) {
      if (t.Zone == WorldLayout.FlightZoneNowhere) {
        const int slab = rm + 1;
        bool open = v >= 13 ? t.Stair == 2 && rel == slab || t.Stair == 3 && rel is slab or slab + 1 : t.Stair == 3 && rel == slab;
        if (open) return 0;
      } else {
        int step = t.Zone is WorldLayout.NowhereWall ? 4 : t.Zone is WorldLayout.NowhereRise or WorldLayout.NowhereTurn1 ? 5 : t.Zone is WorldLayout.NowhereTop or WorldLayout.NowhereTurn2 ? 6 : 7;
        if (rel > top || rel < step - 1 && t.Zone != WorldLayout.NowhereLanding) { }
        else if (t.Zone == WorldLayout.NowhereLanding) { if (rel == 6) return 1; if (rel > 6) return 0; }
        else if (rel == step) return 2;
        else if (rel > step) return 0;
      }
    }
    if (rel > rm + 1) return 1;
    if (rel == 0 || rel == rm + 1) return 1;
    if (t.Kind is TileKind.Wall or TileKind.Door) return 1;
    if (t.Kind == TileKind.Doorway) return rel <= 2 ? 0 : 1;
    if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? 1 : 2;
    if (rel == rm) return t.Beam || t.Overhead != 0 || (int)t.Pipe != 0 ? 1 : 0;
    return 0;
  }

  static IEnumerable<Box> BlockBoxes(int x, int rel, int z) {
    Tile t = At(x, z); int k = KindAt(t, rel);
    if (k == 1) { yield return new Box(x, rel, z, x + 1, rel + 1, z + 1); yield break; }
    if (k != 2) yield break;
    var (cx, cz) = Climb(t.Pier);
    yield return new Box(x, rel, z, x + 1, rel + 0.5, z + 1);
    yield return new Box(cx > 0 ? x + 0.5 : x, rel + 0.5, cz > 0 ? z + 0.5 : z, cx < 0 ? x + 0.5 : x + 1, rel + 1, cz < 0 ? z + 0.5 : z + 1);
  }

  static IEnumerable<Box> Near(double px, double pz, double feet, double reach = Tall + 1) {
    for (int bx = (int)Math.Floor(px - Half); bx <= (int)Math.Floor(px + Half - 1e-9); bx++)
      for (int bz = (int)Math.Floor(pz - Half); bz <= (int)Math.Floor(pz + Half - 1e-9); bz++)
        for (int rel = (int)Math.Floor(feet) - 1; rel <= (int)Math.Floor(feet + reach); rel++)
          foreach (var b in BlockBoxes(bx, rel, bz))
            if (b.X2 > px - Half + 1e-6 && b.X1 < px + Half - 1e-6 && b.Z2 > pz - Half + 1e-6 && b.Z1 < pz + Half - 1e-6) yield return b;
  }

  /// Walks the flight whose first step is at (x, z), every column of it at the middle and 0.2 to either side, from the floor before the
  /// first step to the end of its tiles; records the least headroom, and any place the box strikes something or cannot step up.
  static void Headroom(Tile first, int x, int z) {
    var (cx, cz) = Climb(first.Pier);
    int px0 = cz != 0 ? 1 : 0, pz0 = cx != 0 ? 1 : 0; // across the flight
    bool Same(int ax, int az) { var o = At(ax, az); return o.Stair == 1 && o.Level == first.Level && o.Zone == first.Zone && o.Pier == first.Pier && o.Grand == first.Grand; }
    if (Same(x - px0, z - pz0)) return; // (a column of a flight already walked from its first)
    string kind = first.Level == 5 ? "L5 grand staircases" : "L1 stairs to nowhere";
    double least = double.MaxValue; string fault = null;
    for (int col = 0; Same(x + px0 * col, z + pz0 * col); col++) {
      int tx = x + px0 * col, tz = z + pz0 * col;
      var cells = new List<(int X, int Z)> { (tx - cx, tz - cz), (tx, tz) };
      while (true) {
        var (lx, lz) = cells[^1]; int want = Order(At(lx, lz)) + 1; (int X, int Z)? next = null;
        foreach (var (dx, dz) in new[] { (0, -1), (0, 1), (1, 0), (-1, 0) }) {
          Tile o = At(lx + dx, lz + dz);
          if (Order(o) == want && o.Level == first.Level && !cells.Contains((lx + dx, lz + dz))) { next = (lx + dx, lz + dz); break; }
        }
        if (next is not { } n) break;
        cells.Add(n);
      }
      bool straight = cells.Skip(1).Zip(cells, (b, a) => (b.X - a.X, b.Z - a.Z)).All(d => d == (cx, cz));
      foreach (double side in straight ? new[] { -0.2, 0.0, 0.2 } : new[] { 0.0 }) {
        var path = new List<(double X, double Z)>();
        for (int i = 1; i < cells.Count; i++)
          for (double s = i == 1 ? 0 : 0.05; s <= 1.0001; s += 0.05) {
            var (a, b) = (cells[i - 1], cells[i]);
            path.Add((a.X + 0.5 + (b.X - a.X) * s + px0 * side, a.Z + 0.5 + (b.Z - a.Z) * s + pz0 * side));
          }
        double feet = 1;
        foreach (var (px, pz) in path) {
          double support = 0;
          foreach (var b in Near(px, pz, feet)) if (b.Y1 < feet + StepUp - 1e-6) support = Math.Max(support, b.Y2);
          if (support > feet + StepUp + 1e-6) { least = 0; fault ??= $"could not step up at {px:0.00},{pz:0.00}"; break; }
          double nf = support, ceiling = double.MaxValue; bool hit = false;
          foreach (var b in Near(px, pz, nf, 8)) {
            if (b.Y1 >= nf - 1e-6) ceiling = Math.Min(ceiling, b.Y1);
            if (b.Y2 > nf + 1e-6 && b.Y1 < nf + Tall - 1e-6) hit = true;
          }
          least = Math.Min(least, ceiling - nf);
          if (hit) { least = Math.Min(least, 0); fault ??= $"strikes something at {px:0.00},{pz:0.00} (feet {nf:0.00}, headroom {ceiling - nf:0.00})"; break; }
          if (ceiling - nf < MinHead - 1e-6) fault ??= $"headroom {ceiling - nf:0.00} at {px:0.00},{pz:0.00} (feet {nf:0.00})";
          feet = nf;
        }
      }
    }
    var (n0, bad0, l0, e0) = headKinds.GetValueOrDefault(kind, (0, 0, double.MaxValue, null));
    headKinds[kind] = (n0 + 1, bad0 + (fault != null ? 1 : 0), Math.Min(l0, least), e0 ?? (fault != null ? $"flight at {x},{z} climbing {first.Pier}: {fault}" : null));
  }

  static void Scan(int m0x, int m0z, int n, Dictionary<string,int> c, Dictionary<string,string> ex) {
    void Note(string k, int x, int z) { c[k] = c.GetValueOrDefault(k)+1; if (!ex.ContainsKey(k)) ex[k] = $"{x},{z} (cell-local {x & 31},{z & 31})"; }
    for (int z = m0z*32+1; z < (m0z+n)*32-1; z++) for (int x = m0x*32+1; x < (m0x+n)*32-1; x++) {
      var t = At(x,z); if (t.Zone == WorldLayout.NowhereTurn1 && t.Level == 1) Note("L1 stairs to nowhere: turned along the wall (counted once per tile of the run)", x, z); else if (t.Zone == WorldLayout.NowhereRise && t.Level == 1) Note("L1 stairs to nowhere: straight on (counted once per tile)", x, z);
      if (t.Stair == 0 || t.Level > 5) continue;
      if (t.Stair == 1 && (t.Level == 1 && t.Zone == WorldLayout.FlightZoneNowhere || t.Level == 5 && t.Grand)) Headroom(t, x, z);
      if (t.Variant != 0 || t.Stack != 0 || t.SupplyBox) Note($"L{t.Level} prop/box on a stair tile", x, z);
      if (WorldLayout.IsShaftFlight(t)) { Shaft(t, x, z, Note); continue; }
      if (t.Stair == 1) { // bottom step: tile behind it (opposite the climb) should be standable floor
        var (bx,bz) = t.Pier switch { ArchPier.East => (x-1,z), ArchPier.West => (x+1,z), ArchPier.North => (x,z+1), _ => (x,z-1) };
        var b = At(bx,bz); bool ok = b.Kind == TileKind.Floor && b.Variant == 0 && b.Stair == 0 && !b.SupplyBox;
        Note($"L{t.Level} flights", x, z); if (t.Zone == WorldLayout.FlightZoneNowhere) Note($"L1 stairs to nowhere with the dark way on, climbing {t.Pier}", x, z); else if (t.Level == 1) {
          Note("L1 stairs to nowhere into a blank wall", x, z);
          var (cx, cz) = Climb(t.Pier);
          // (step 1 is two tiles back from step 3; the wall is just past step 3, the way beyond it three tiles more)
          for (int k = 4; k <= 6; k++) { int qx = x + cx * k, qz = z + cz * k; Tile q = At(qx, qz); int lx = qx & 31, lz = qz & 31;
            string why = lx < 1 || lz < 1 || lx > 30 || lz > 30 ? "cell edge" : q.Kind != TileKind.Floor ? "not floor: " + q.Kind : q.Floor == FloorKind.L1Hall ? "hall" : q.Stair != 0 ? "stairs" : q.Under != 0 ? "under" : q.Zone != 0 ? "zone" : q.Sealed ? "sealed" : null;
            if (why != null) { Note("  blank because beyond: " + why, x, z); break; } }
        } if (!ok) Note($"L{t.Level} bottom step approach blocked", x, z);
      }
    }
  }

  static void Shaft(Tile t, int x, int z, Action<string, int, int> Note) {
    string kind = $"L{t.Level} flight " + (t.Zone == WorldLayout.FlightZoneDown ? "down" : t.Zone == WorldLayout.FlightZoneFun ? "up to Fun" : "up");
    var (dx, dz) = Climb(t.Pier);
    // Steps are numbered from the landing: up the flight up, against the climb down the flight down
    int along = t.Zone == WorldLayout.FlightZoneDown ? -1 : 1;
    // Each step on its own: under the wall from the fifth, walled in on both sides, nothing round it opening elsewhere
    bool walled = t.Kind == TileKind.Wall;
    int open = t.Zone == WorldLayout.FlightZoneDown || t.Level == 1 ? 4 : 3;
    if (walled != t.Stair > open) Note($"{kind}: step {t.Stair} {(walled ? "under a wall" : "on the floor")}", x, z);
    foreach (int side in new[] { 1, -1 }) {
      Tile s = At(x + dz * side, z + dx * side);
      // (From layout 9 a flight is two wide: the neighbouring step of the same flight is a side too, only the outer column has a wall)
      bool sibling = WorldLayout.IsShaftFlight(s) && s.Zone == t.Zone && s.Stair == t.Stair && s.Pier == t.Pier && s.Level == t.Level;
      if (!s.IsWallLike && !sibling) Note($"{kind}: open side (could fall in or bump the shaft's edge)", x, z);
      if (s.Level != t.Level || s.Under != 0) Note($"{kind}: shaft beside another level or a way elsewhere", x, z);
      if (t.Level == 1 && s.Variant == Decor.LevelSign && WorldLayout.L1FloorOf(s) != WorldLayout.L1FloorOf(t)) Note($"{kind}: painted floor not its own", x, z);
    }
    if (t.Stair == WorldLayout.StairwellSteps) {
      // The far end of the shaft: solid in that column, of this level
      Tile end = At(x + dx * along, z + dz * along);
      if (end.Level != t.Level || end.Under != 0 || WorldLayout.IsShaftFlight(end)) Note($"{kind}: shaft's end not plain", x, z);
    }
    if (t.Stair != 1) {
      Tile prev = At(x - dx * along, z - dz * along);
      if (!WorldLayout.IsShaftFlight(prev) || prev.Zone != t.Zone || prev.Stair != t.Stair - 1 || prev.Pier != t.Pier || prev.Height != t.Height) Note($"{kind}: steps not in line", x, z);
      return;
    }
    Note($"{kind}s", x, z);
    if (t.Level == 1 && t.Zone == WorldLayout.FlightZoneDown) Note($"L1 stairwells on floor {(WorldLayout.L1FloorOf(t) is int f && f >= 0 ? WorldLayout.L1FloorLabel(f) : "none")}", x, z);
    // The landing: clear floor before the first step (Level Fun's confetti and balloon are walked through)
    Tile landing = At(x - dx * along, z - dz * along);
    bool clear = landing.Kind == TileKind.Floor && landing.Stair == 0 && landing.Stack == 0 && !landing.SupplyBox && !landing.Sealed
      && (landing.Variant == 0 || t.Zone == WorldLayout.FlightZoneFun && landing.Variant is Props.FunConfetti or Props.FunBalloonTied);
    if (!clear) Note($"{kind}: landing blocked", x, z);
    // Its pair, across the dividing wall, from the same landing
    bool pair = false;
    for (int ox = -4; ox <= 4; ox++) for (int oz = -4; oz <= 4; oz++) { Tile o = At(x + ox, z + oz);
      pair |= WorldLayout.IsShaftFlight(o) && o.Stair == 1 && (o.Zone == WorldLayout.FlightZoneDown) != (t.Zone == WorldLayout.FlightZoneDown) && o.Height == t.Height; }
    if (!pair) Note($"{kind}: no flight the other way beside it (on its floor)", x, z);
  }
}
