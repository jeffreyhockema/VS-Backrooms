using System.Reflection;
using Backrooms.Worldgen;
static class Boiler {
  static bool W(Tile t) { if (t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water) return true; if (t.Kind != TileKind.Floor) return false; if (t.SupplyBox) return false; if (t.Stack > 0 && t.Variant == 0) return false; return t.Variant is 0; }
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    var hz = typeof(WorldLayout).GetMethod("HotelZoneAt", BindingFlags.NonPublic | BindingFlags.Instance);
    int cells = 0, entries = 0, dead = 0; var ex = new List<string>();
    for (int mz = m0z; mz < m0z+n; mz++) for (int mx = m0x; mx < m0x+n; mx++) {
      if (l.LevelAt(mx,mz) != 5 || hz.Invoke(l, new object[]{mx,mz}).ToString() != "Boiler") continue; cells++;
      var t = l.BuildMacro(mx,mz); var E = l.BuildMacro(mx+1,mz); var S = l.BuildMacro(mx,mz+1);
      var seen = new bool[1024]; var q = new Queue<int>(); int start = 15*32+16; seen[start]=true; q.Enqueue(start);
      while (q.Count>0) { int i=q.Dequeue(); int x=i%32,z=i/32; foreach (var (dx,dz) in new[]{(1,0),(-1,0),(0,1),(0,-1)}) { int nx=x+dx,nz=z+dz; if (nx<0||nz<0||nx>31||nz>31) continue; int j=nz*32+nx; if (seen[j]||!W(t[j])) continue; seen[j]=true; q.Enqueue(j);} }
      // entries: own west/north edge passages, and E/S neighbours' edge passages
      for (int i = 1; i < 32; i++) {
        foreach (var (x,z,open) in new[]{(0,i,W(t[i*32])),(i,0,W(t[i])),(31,i,W(E[i*32])),(i,31,W(S[i]))}) {
          if (!open) continue; entries++;
          if (!seen[z*32+x]) { dead++; if (ex.Count<6) ex.Add($"cell {(mx-m0x)*32},{(mz-m0z)*32} local {x},{z} tile={t[z*32+x].Kind}/{t[z*32+x].Variant}/box={t[z*32+x].SupplyBox}"); }
        }
      }
    }
    Console.WriteLine($"boiler cells {cells}, edge entry tiles {entries}, not joined to the aisle {dead}");
    foreach (var e in ex) Console.WriteLine("  " + e);
  }
}
