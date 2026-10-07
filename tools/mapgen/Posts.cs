using System.Reflection;
using Backrooms.Worldgen;
static class Posts {
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    var hz = typeof(WorldLayout).GetMethod("HotelZoneAt", BindingFlags.NonPublic | BindingFlags.Instance);
    var hc = typeof(WorldLayout).GetMethod("HotelCellAt", BindingFlags.NonPublic | BindingFlags.Static);
    int corners = 0, bad = 0; string ex = "";
    for (int mz = m0z; mz < m0z+n; mz++) for (int mx = m0x; mx < m0x+n; mx++) {
      bool Wing(int a, int b) => l.LevelAt(a,b) == 5 && hz.Invoke(l, new object[]{a,b}).ToString() is "Wing" or "Beverly";
      if (!(Wing(mx,mz) && Wing(mx-1,mz) && Wing(mx,mz-1) && Wing(mx-1,mz-1))) continue;
      corners++; var t = l.BuildMacro(mx,mz)[0];
      string cell = hc.Invoke(null, new object[]{mx*32, mz*32}).ToString();
      if (t.Kind == TileKind.Wall && cell != "Wall") { bad++; ex += " | " + $"{(mx-m0x)*32},{(mz-m0z)*32} grid={cell}"; }
    }
    Console.WriteLine($"L5 all-wing corners {corners}, post standing where the grid has {{corridor/room/door}}: {bad} e.g. {ex}");
  }
}
