using Backrooms.Worldgen;
static class EdgeDoors {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static bool W(Tile t) { if (t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water) return true; if (t.Kind != TileKind.Floor) return false; if (t.Stack > 0 && t.Variant == 0) return false; return t.Variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable or Props.Bedroll or Props.SleepingBag; }
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    layout = l; var tot = new Dictionary<string,int>(); var bad = new Dictionary<string,int>(); var both = new Dictionary<string,int>(); var ex = new Dictionary<string,string>();
    for (int z = m0z*32+32; z < (m0z+n)*32-32; z++) for (int x = m0x*32+32; x < (m0x+n)*32-32; x++) {
      bool ex0 = Hashing.Mod(x,32)==0, ez0 = Hashing.Mod(z,32)==0; if (ex0 == ez0) continue; // edge line, not corner
      var t = At(x,z); if (t.Kind != TileKind.Doorway) continue;
      Tile a = ex0 ? At(x-1,z) : At(x,z-1), b = ex0 ? At(x+1,z) : At(x,z+1);
      string key = $"L{a.Level}|L{b.Level}"; if (a.Level > 6 || b.Level > 6) continue;
      tot[key] = tot.GetValueOrDefault(key)+1;
      if (!W(a) || !W(b)) { bad[key] = bad.GetValueOrDefault(key)+1; if (!ex.ContainsKey(key)) ex[key] = $"{x-m0x*32},{z-m0z*32} a={a.Kind}/{a.Variant} b={b.Kind}/{b.Variant}"; }
    }
    // pairs: a doorway run where every tile is bad
    foreach (var k in tot.Keys.OrderBy(k=>k)) Console.WriteLine($"{k}: edge doorway tiles {tot[k]}, blocked on a side {bad.GetValueOrDefault(k)} ({100.0*bad.GetValueOrDefault(k)/tot[k]:0}%)  e.g. {ex.GetValueOrDefault(k)}");
  }
}
