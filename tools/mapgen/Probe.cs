using System.Reflection;
using Backrooms.Worldgen;
static class Probe {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  public static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  public static char Ch(Tile t) => t.Kind switch { TileKind.Wall => t.Variant != 0 ? 'w' : '#', TileKind.Doorway => 'D', TileKind.Door => t.Pattern == WallPattern.Elevator ? 'E' : 'X', TileKind.Bars => '|', TileKind.Pit => 'O', TileKind.Water => '~', TileKind.ArchDoor => 'A', TileKind.ArchWindow => 'W',
      _ => t.SupplyBox ? 'b' : t.Stair > 0 ? (char)('0' + t.Stair) : t.Stack > 0 && t.Variant == 0 ? 'c' : t.Variant != 0 ? 'p' : t.Sealed ? ',' : '.' };
  // args: probe ox oz (harness coords) w h
  public static void Run(WorldLayout l, int m0x, int m0z, string[] a) {
    layout = l; int ox = int.Parse(a[3]) + m0x * 32, oz = int.Parse(a[4]) + m0z * 32; int w = a.Length > 5 ? int.Parse(a[5]) : 40, h = a.Length > 6 ? int.Parse(a[6]) : 20;
    var hz = typeof(WorldLayout).GetMethod("HotelZoneAt", BindingFlags.NonPublic | BindingFlags.Instance);
    Console.WriteLine($"origin global {ox},{oz}; macro {WorldLayout.MacroOf(ox)},{WorldLayout.MacroOf(oz)} level {l.LevelAt(WorldLayout.MacroOf(ox), WorldLayout.MacroOf(oz))} hotelzone {hz.Invoke(l, new object[]{WorldLayout.MacroOf(ox), WorldLayout.MacroOf(oz)})}");
    for (int z = oz; z < oz + h; z++) { var sb = new System.Text.StringBuilder($"{z - m0z*32,5} ");
      for (int x = ox; x < ox + w; x++) { char c = Ch(At(x, z)); if (c == '.' && (Hashing.Mod(x,32)==0 || Hashing.Mod(z,32)==0)) c = ':'; sb.Append(c); }
      sb.Append("   "); for (int x = ox; x < ox + w; x++) sb.Append((char)('0' + At(x, z).Level));
      Console.WriteLine(sb); }
  }
}
