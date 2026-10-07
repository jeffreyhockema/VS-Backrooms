using Backrooms.Worldgen;
static class Finder {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static bool Passable(Tile t) => t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water || t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox && t.Stair == 0;
  // Can you walk at least 48 blocks away from here?
  static bool Escapes(int sx, int sz) {
    var seen = new HashSet<(int,int)> { (sx,sz) }; var q = new Queue<(int,int)>(); q.Enqueue((sx,sz));
    while (q.Count > 0) { var (x,z) = q.Dequeue(); if (Math.Abs(x-sx)+Math.Abs(z-sz) >= 48) return true; if (seen.Count > 20000) return true;
      foreach (var (dx,dz) in new[]{(1,0),(-1,0),(0,1),(0,-1)}) { var n=(x+dx,z+dz); if (seen.Contains(n) || !Passable(At(n.Item1,n.Item2))) continue; seen.Add(n); q.Enqueue(n); } }
    return false; }
  static void Dump(int cx, int cz, int level) {
    Console.WriteLine($"--- trapped at {cx},{cz} level {level} (macro-local {cx - WorldLayout.MacroOf(cx)*32},{cz - WorldLayout.MacroOf(cz)*32})");
    for (int z = cz - 9; z <= cz + 9; z++) { var line = new System.Text.StringBuilder();
      for (int x = cx - 16; x <= cx + 16; x++) { var t = At(x,z); char c = t.Kind switch { TileKind.Wall => '#', TileKind.Doorway => 'D', TileKind.Door => 'X', TileKind.Bars => '|', TileKind.Pit => 'O', _ => t.SupplyBox ? 'b' : t.Stack > 0 ? 'c' : t.Variant != 0 ? 'p' : t.Stair > 0 ? 's' : t.Sealed ? '~' : '.' };
        if (x == cx && z == cz) c = '@'; if (c == '.' && (x % 32 == 0 || z % 32 == 0)) c = ','; line.Append(c); }
      Console.WriteLine(line); } }
  public static void Run(WorldLayout l) {
    layout = l;
    Func<Tile,bool> elevator = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator, stairs = t => t.Stair > 0;
    for (int level = 0; level < 6; level++) foreach (var (name, anchor) in new (string, Func<Tile,bool>)[]{ ("open", null), ("elevator", elevator), ("stairs", stairs) }) {
      if (anchor == elevator && level < 3) continue; if (anchor == stairs && level != 4) continue;
      int found = 0, wrongLevel = 0, trapped = 0, anchored = 0; const int N = 200;
      for (ulong k = 1; k <= N; k++) { var a = layout.FindArrival(level, k * 7919UL + 13, anchor); if (a == null) continue; found++;
        var (x,z) = a.Value; if (At(x,z).Level != level) wrongLevel++; if (!Escapes(x,z)) { trapped++; if (trapped <= 2 && anchor == null && level == 5) Dump(x, z, level); }
        if (anchor != null && (anchor(At(x+1,z)) || anchor(At(x-1,z)) || anchor(At(x,z+1)) || anchor(At(x,z-1)))) anchored++; }
      Console.WriteLine($"Level {level} {name,-8}: found {found}/{N}, wrong level {wrongLevel}, trapped {trapped}" + (anchor != null ? $", beside anchor {anchored}" : ""));
    }
  }
}
