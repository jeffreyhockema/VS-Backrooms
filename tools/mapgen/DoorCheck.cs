using Backrooms.Worldgen;
/// For each doorway in levels 0-5, check that both sides reach >= N tiles (not a dead-end pocket) ignoring Sealed flags.
static class DoorCheck {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static bool W(Tile t) { if (t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water) return true; if (t.Kind != TileKind.Floor) return false; if (t.Stack > 0 && t.Variant == 0) return false; return t.Variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable or Props.Bedroll or Props.SleepingBag or Props.ImprovBed; }
  static int Reach(int sx, int sz, int cap, int bx, int bz) {
    var seen = new HashSet<(int,int)>{(sx,sz),(bx,bz)}; var q = new Queue<(int,int)>(); q.Enqueue((sx,sz)); int n = 0;
    while (q.Count > 0 && n < cap) { var (x,z) = q.Dequeue(); n++; foreach (var (dx,dz) in new[]{(1,0),(-1,0),(0,1),(0,-1)}) { var p=(x+dx,z+dz); if (seen.Contains(p) || !W(At(p.Item1,p.Item2))) continue; seen.Add(p); q.Enqueue(p);} }
    return n; }
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    layout = l; var counts = new Dictionary<string,int>(); var ex = new Dictionary<string,List<string>>();
    for (int z = m0z*32+40; z < (m0z+n)*32-40; z++) for (int x = m0x*32+40; x < (m0x+n)*32-40; x++) {
      var t = At(x,z); if (t.Kind != TileKind.Doorway || t.Level > 5) continue;
      // which axis: walls on the sides
      bool ew = At(x-1,z).IsWallLike == false || At(x+1,z).IsWallLike == false; 
      foreach (var (ax,az,bx,bz) in new[]{(x-1,z,x+1,z),(x,z-1,x,z+1)}) {
        var A = At(ax,az); var B = At(bx,bz); if (A.IsWallLike || B.IsWallLike) continue;
        // count reach on each side excluding the doorway itself
        int ra = W(A) ? Reach(ax,az,60,x,z) : 0, rb = W(B) ? Reach(bx,bz,60,x,z) : 0;
        // partner doorway counts: skip if partner doorway beside offers path
        foreach (var (side, r, sx, sz, st) in new[]{("A",ra,ax,az,A),("B",rb,bx,bz,B)}) {
          if (r >= 60) continue;
          string key = $"L{t.Level} dead-end side reach<60" + (r == 0 ? " (blocked)" : "");
          counts[key] = counts.GetValueOrDefault(key) + 1;
          if (!ex.ContainsKey(key)) ex[key] = new(); if (ex[key].Count < 8) ex[key].Add($"{x - m0x*32},{z - m0z*32} reach {r} sealed={st.Sealed} var={st.Variant}");
        }
      }
    }
    foreach (var kv in counts) { Console.WriteLine($"{kv.Key}: {kv.Value}"); foreach (var e in ex[kv.Key]) Console.WriteLine("   " + e); }
  }
}
