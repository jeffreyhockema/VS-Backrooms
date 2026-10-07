using Backrooms.Worldgen;
static class Cubes {
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    int desks = 0, chairOverGhost = 0, deskNoChair = 0; string ex = "";
    for (int mz = m0z; mz < m0z+n; mz++) for (int mx = m0x; mx < m0x+n; mx++) {
      if (l.LevelAt(mx,mz) != 4) continue; var t = l.BuildMacro(mx,mz);
      for (int z = 1; z < 31; z++) for (int x = 1; x < 31; x++) { var c = t[z*32+x];
        if (c.Variant == Props.Desk && (c.Pier is ArchPier.North or ArchPier.South)) { desks++; int dz = c.Pier == ArchPier.North ? -1 : 1; var ch = t[(z+dz)*32+x]; if (ch.Variant != Props.OfficeChair && t[(z-dz)*32+x].Variant == Props.Partition) { deskNoChair++; } }
        if (c.Variant == Props.OfficeChair && (c.Pier is ArchPier.North or ArchPier.South)) { int dz = c.Pier == ArchPier.South ? 1 : -1; var d = t[(z+dz)*32+x]; if (d.Variant == 0 && d.Floor == FloorKind.OfficeCarpetGhost && t[(z+2*dz)*32+x].Variant == Props.Partition) { chairOverGhost++; if (ex == "") ex = $"{(mx-m0x)*32+x},{(mz-m0z)*32+z}"; } }
      }
    }
    Console.WriteLine($"L4 cubicle-ish desks {desks}; desks against partition with no chair {deskNoChair}; chairs facing a cleared (ghost) desk spot {chairOverGhost} e.g. {ex}");
  }
}
