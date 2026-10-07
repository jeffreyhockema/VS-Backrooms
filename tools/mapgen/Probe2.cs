using Backrooms.Worldgen;
static class Probe2 {
  public static void Run(WorldLayout l, int smx, int smz) {
    var want = new Dictionary<string, Func<Tile, bool>> {
      ["L5 ice machine"] = t => t.Level == 5 && t.Kind == TileKind.Floor && t.Variant == Props.IceMachine,
      ["L5 tray"] = t => t.Level == 5 && t.Kind == TileKind.Floor && t.Variant == Props.RoomServiceTray,
      ["L6 wet"] = t => t.Level == 6 && t.Floor == FloorKind.L6Wet,
      ["L6 flashlight"] = t => t.Level == 6 && t.Kind == TileKind.Floor && t.Variant == Props.Flashlight,
      ["L7 jetty post"] = t => t.Level == 7 && t.Variant == Props.JettyPost,
      ["L7 kelp"] = t => t.Level == 7 && t.Variant == Props.Kelp,
      ["L7 driftwood"] = t => t.Level == 7 && t.Kind == TileKind.Water && t.Variant == 0 && t.Stack == 1,
      ["L9 pool"] = t => t.Level == 9 && t.Floor == FloorKind.PoolDeep,
      ["L9 chimney"] = t => t.Level == 9 && t.Kind == TileKind.Wall && t.Variant == 3,
      ["L9 photo"] = t => t.Level == 9 && t.Kind == TileKind.Wall && t.Variant == Decor.FamilyPhoto,
      ["L9 light"] = t => t.Level == 9 && t.Ceiling == CeilingKind.LightOff,
      ["L9 hydrant"] = t => t.Level == 9 && t.Kind == TileKind.Floor && t.Variant == Props.FireHydrant,
      ["L9 flowers"] = t => t.Level == 9 && t.Kind == TileKind.Floor && t.Variant == Props.Flowers,
      ["L9 veg"] = t => t.Level == 9 && t.Kind == TileKind.Floor && t.Variant == Props.Vegetable,
      ["L10 silo"] = t => t.Level == 10 && t.Pattern == WallPattern.Silo && t.Kind == TileKind.Wall,
      ["L10 farmhouse"] = t => t.Level == 10 && t.Zone == 9 && t.Kind == TileKind.Wall,
      ["L10 tractor"] = t => t.Level == 10 && t.Variant == Props.Tractor,
      ["L10 hayroll"] = t => t.Level == 10 && t.Variant == Props.HayRoll,
      ["L10 stubble"] = t => t.Level == 10 && t.Floor == FloorKind.Stubble,
      ["L10 pole"] = t => t.Level == 10 && t.Variant == Props.PowerPole,
    };
    var found = new Dictionary<string, (int, int)>();
    foreach (int level in new[] { 5, 6, 7, 8, 9, 10 }) {
      // walk outward along east until inside the level, then scan cells around
      int r = 1; while (l.LevelAt(smx + r, smz) < level) r++;
      int cx = smx + r + (level == 10 ? 10 : 6), cz = smz;
      for (int rad = 0; rad <= 12 && found.Count < want.Count; rad++)
        for (int dz = -rad; dz <= rad; dz++) for (int dx = -rad; dx <= rad; dx++) {
          if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != rad) continue;
          var tiles = l.BuildMacro(cx + dx, cz + dz);
          for (int i = 0; i < 1024; i++) foreach (var (k, f) in want) if (!found.ContainsKey(k) && f(tiles[i])) found[k] = ((cx + dx) * 32 + i % 32, (cz + dz) * 32 + i / 32);
        }
      if (level == 8) Console.WriteLine($"L8 cell: {(cx) * 32 + 16},{cz * 32 + 16}");
    }
    foreach (var k in want.Keys) Console.WriteLine($"{k,-16}: {(found.TryGetValue(k, out var p) ? $"{p.Item1},{p.Item2}" : "-")}");
  }
}
