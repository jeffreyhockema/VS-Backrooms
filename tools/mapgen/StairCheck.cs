using Backrooms.Worldgen;
static class StairCheck {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    layout = l; var c = new Dictionary<string,int>(); var ex = new Dictionary<string,string>();
    void Note(string k, int x, int z) { c[k] = c.GetValueOrDefault(k)+1; if (!ex.ContainsKey(k)) ex[k] = $"{x-m0x*32},{z-m0z*32}"; }
    for (int z = m0z*32+1; z < (m0z+n)*32-1; z++) for (int x = m0x*32+1; x < (m0x+n)*32-1; x++) {
      var t = At(x,z); if (t.Stair == 0 || t.Level > 5) continue;
      if (t.Variant != 0 || t.Stack != 0 || t.SupplyBox) Note($"L{t.Level} prop/box on a stair tile", x, z);
      if (t.Stair == 1) { // bottom step: tile behind it (opposite the climb) should be standable floor
        var (bx,bz) = t.Pier switch { ArchPier.East => (x-1,z), ArchPier.West => (x+1,z), ArchPier.North => (x,z+1), _ => (x,z-1) };
        var b = At(bx,bz); bool ok = b.Kind == TileKind.Floor && b.Variant == 0 && b.Stair == 0 && !b.SupplyBox;
        Note($"L{t.Level} flights", x, z); if (!ok) Note($"L{t.Level} bottom step approach blocked", x, z);
      }
    }
    foreach (var k in c.Keys.OrderBy(k=>k)) Console.WriteLine($"{k}: {c[k]} e.g. {ex[k]}");
  }
}
