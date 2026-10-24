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
  }

  static void Scan(int m0x, int m0z, int n, Dictionary<string,int> c, Dictionary<string,string> ex) {
    void Note(string k, int x, int z) { c[k] = c.GetValueOrDefault(k)+1; if (!ex.ContainsKey(k)) ex[k] = $"{x},{z} (cell-local {x & 31},{z & 31})"; }
    for (int z = m0z*32+1; z < (m0z+n)*32-1; z++) for (int x = m0x*32+1; x < (m0x+n)*32-1; x++) {
      var t = At(x,z); if (t.Stair == 0 || t.Level > 5) continue;
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
      if (!s.IsWallLike) Note($"{kind}: open side (could fall in or bump the shaft's edge)", x, z);
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
    for (int ox = -2; ox <= 2; ox++) for (int oz = -2; oz <= 2; oz++) { Tile o = At(x + ox, z + oz);
      pair |= WorldLayout.IsShaftFlight(o) && o.Stair == 1 && (o.Zone == WorldLayout.FlightZoneDown) != (t.Zone == WorldLayout.FlightZoneDown) && o.Height == t.Height; }
    if (!pair) Note($"{kind}: no flight the other way beside it (on its floor)", x, z);
  }
}
