using Backrooms.Worldgen;
static class Peek {
  public static void Run(WorldLayout layout, int cx, int cz, int r) {
    for (int z = cz - r; z <= cz + r; z++) { var line = new System.Text.StringBuilder();
      for (int x = cx - 2 * r; x <= cx + 2 * r; x++) { Tile t = layout.TileAt(x, z);
        char c = t.Kind switch { TileKind.Wall => t.Variant >= 40 ? 'w' : t.Level == 0 && t.Pattern == WallPattern.Cream ? '%' : t.Level == 0 && t.Pattern == WallPattern.Dotted ? ':' : '#', TileKind.ArchDoor => 'a', TileKind.ArchWindow => 'n', TileKind.Doorway => 'D', TileKind.Door => 'X', TileKind.Bars => '|', TileKind.Pit => 'O', TileKind.Water => '~',
          _ => t.SupplyBox ? 'B' : t.Stack > 0 && t.Variant == 0 ? 'c' : t.Variant != 0 ? (t.Variant < 40 ? 'p' : 'P') : t.Stair > 0 ? 's' : '.' };
        line.Append(c); }
      Console.WriteLine(line + $"  z={z}"); }
    Tile at = layout.TileAt(cx, cz); Console.WriteLine($"at {cx},{cz}: level {at.Level} kind {at.Kind} variant {at.Variant} stack {at.Stack} pattern {at.Pattern} floor {at.Floor} pier {at.Pier} height {at.Height} detail {at.Detail} zone {at.Zone} under {at.Under} chalk {at.Chalk} sealed {at.Sealed} stair {at.Stair}");
  }
}
