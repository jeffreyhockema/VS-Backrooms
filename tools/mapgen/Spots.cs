using Backrooms.Worldgen;
static class Spots {
  public static void Run(WorldLayout l) {
    var snack = l.SnackroomCellFor(12345UL);
    if (snack is { } s) Console.WriteLine($"snackrooms centre: {s.Mx * 32 + 15},{s.Mz * 32 + 15}");
    // a crossing of the 9th Road in Level 8, along the east axis
    for (int x = 518100; x < 518900; x++) {
      int z = 512000;
      for (int dz = -60; dz <= 60; dz++)
        if (l.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z + dz)) == 8 && l.IsNinthRoad(x, z + dz) && l.IsNinthRoad(x + 6, z + dz) && l.IsNinthRoad(x, z + dz + 6)) { Console.WriteLine($"9th road crossing: {x},{z + dz}"); return; }
    }
  }
}
