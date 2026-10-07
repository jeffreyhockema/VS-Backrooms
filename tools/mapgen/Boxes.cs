using Backrooms.Worldgen;
static class Boxes {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static bool Open(Tile t) => t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.ArchDoor or TileKind.Water;
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    layout = l; var cnt = new Dictionary<string,int>(); var ex = new Dictionary<string,string>();
    for (int z = m0z*32+32; z < (m0z+n)*32-32; z++) for (int x = m0x*32+32; x < (m0x+n)*32-32; x++) {
      var t = At(x,z); if (!t.SupplyBox || t.Level > 5) continue;
      // a box that is a corridor plug: open on two opposite sides, walls on the other two
      bool ew = Open(At(x-1,z)) && Open(At(x+1,z)) && !Open(At(x,z-1)) && !Open(At(x,z+1));
      bool ns = Open(At(x,z-1)) && Open(At(x,z+1)) && !Open(At(x-1,z)) && !Open(At(x+1,z));
      string edge = (Hashing.Mod(x,32)==31 || Hashing.Mod(z,32)==31) ? "at E/S cell edge" : "interior";
      string k = $"L{t.Level} box {(ew||ns ? "PLUGS a 1-wide passage" : "ok")} {edge}"; cnt[k] = cnt.GetValueOrDefault(k)+1; if (!ex.ContainsKey(k)) ex[k] = $"{x-m0x*32},{z-m0z*32}";
    }
    foreach (var k in cnt.Keys.OrderBy(k=>k)) Console.WriteLine($"{k}: {cnt[k]}  e.g. {ex[k]}");
  }
}
