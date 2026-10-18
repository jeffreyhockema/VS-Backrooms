using System.Reflection;
using System.Text;
using Backrooms.Worldgen;

/// <summary>plantmap: draws the first boiler halls it finds (Level 5) as text, one character a tile: B boiler, F furnace, c coal, # wall, | bars, - header over the tile, h header through a wall, ~ sump, otherwise . floor. CELLS=n shows n halls.</summary>
static class PlantMap
{
  public static void Run(WorldLayout l, int m0x, int m0z, int n)
  {
    var hz = typeof(WorldLayout).GetMethod("HotelZoneAt", BindingFlags.NonPublic | BindingFlags.Instance)!;
    int shown = 0, want = int.TryParse(Environment.GetEnvironmentVariable("CELLS"), out int w) ? w : 1;
    for (int mz = m0z; mz < m0z + n && shown < want; mz++)
      for (int mx = m0x; mx < m0x + n && shown < want; mx++)
      {
        if (l.LevelAt(mx, mz) != 5 || hz.Invoke(l, new object[] { mx, mz })!.ToString() != "Boiler") continue;
        shown++;
        Console.WriteLine($"boiler hall cell {mx},{mz}");
        for (int z = 0; z < 32; z++)
        {
          var sb = new StringBuilder();
          for (int x = 0; x < 32; x++)
          {
            Tile t = l.TileAt(mx * 32 + x, mz * 32 + z);
            bool plant = t.Pipe >= 15 && t.Pipe <= 19;
            char c = t.Kind switch
            {
              TileKind.Wall => plant ? 'h' : '#',
              TileKind.Bars => '|',
              TileKind.Water => '~',
              TileKind.Floor => t.Variant == Props.Boiler ? 'B' : t.Variant == Props.Furnace ? 'F' : t.Variant == Props.CoalPile ? 'c'
                : t.Variant == Props.GaugeFrame ? 'g' : t.Variant == Props.PressureTank ? 'T' : t.Variant == Props.FloorLever ? 'l'
                : t.Variant != 0 ? 'p' : plant ? '-' : '.',
              _ => '?',
            };
            sb.Append(c);
          }
          Console.WriteLine(sb + $"  z={z}");
        }
      }
  }
}
