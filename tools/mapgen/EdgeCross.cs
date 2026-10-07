using Backrooms.Worldgen;
static class EdgeCross {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static bool W(Tile t) { if (t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water) return true; if (t.Kind != TileKind.Floor) return false; if (t.Stack > 0 && t.Variant == 0) return false; return t.Variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable or Props.Bedroll; }
  static bool Escapes(int sx, int sz, int bx, int bz) { // reach 40 tiles without crossing the doorway
    var seen = new HashSet<(int,int)>{(sx,sz),(bx,bz)}; var q = new Queue<(int,int)>(); q.Enqueue((sx,sz)); int n=0;
    while (q.Count>0) { var (x,z)=q.Dequeue(); if (++n >= 80) return true; foreach (var (dx,dz) in new[]{(1,0),(-1,0),(0,1),(0,-1)}) { var p=(x+dx,z+dz); if (seen.Contains(p)||!W(At(p.Item1,p.Item2))) continue; seen.Add(p); q.Enqueue(p);} }
    return false; }
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    layout = l; var tot = new Dictionary<string,int>(); var dead = new Dictionary<string,int>(); var ex = new Dictionary<string,List<string>>();
    for (int mz = m0z+1; mz < m0z+n-1; mz++) for (int mx = m0x+1; mx < m0x+n-1; mx++) foreach (bool west in new[]{true,false}) {
      int la = l.LevelAt(west ? mx-1 : mx, west ? mz : mz-1), lb = l.LevelAt(mx, mz); if (la == lb || la > 6 || lb > 6) continue;
      bool any = false, crossing = false;
      for (int i = 1; i < 32; i++) {
        int x = west ? mx*32 : mx*32+i, z = west ? mz*32+i : mz*32; var t = At(x,z); if (t.Kind != TileKind.Doorway) continue; any = true;
        int ax = west ? x-1 : x, az = west ? z : z-1, bx = west ? x+1 : x, bz = west ? z : z+1;
        if (W(At(ax,az)) && W(At(bx,bz)) && Escapes(ax,az,x,z) && Escapes(bx,bz,x,z)) { crossing = true; break; }
      }
      string key = $"L{Math.Min(la,lb)}-L{Math.Max(la,lb)}"; tot[key] = tot.GetValueOrDefault(key)+1;
      if (!crossing) { dead[key] = dead.GetValueOrDefault(key)+1; if (!ex.ContainsKey(key)) ex[key]=new(); if (ex[key].Count<3) ex[key].Add($"{(mx-m0x)*32},{(mz-m0z)*32} {(west?"W":"N")} any={any}"); }
    }
    foreach (var k in tot.Keys.OrderBy(k=>k)) Console.WriteLine($"{k}: boundary edges {tot[k]}, with no real crossing {dead.GetValueOrDefault(k)}  {string.Join("; ", ex.GetValueOrDefault(k) ?? new())}");
  }
}
