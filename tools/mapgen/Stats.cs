using System.Reflection;
using Backrooms.Worldgen;
static class Stats {
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    int corr = 0, corrSealed = 0, doors = 0, locked = 0, l4Door = 0, l4Locked = 0, l5RoomOpen = 0, l5RoomEmpty = 0, l5Wood = 0, l5Room = 0, liftModern = 0, liftCage = 0, staff = 0;
    var cellsSealedCorr = new HashSet<(int,int)>();
    for (int mz = m0z; mz < m0z + n; mz++) for (int mx = m0x; mx < m0x + n; mx++) {
      var tiles = l.BuildMacro(mx, mz);
      for (int i = 0; i < 1024; i++) { var t = tiles[i]; int gx = mx*32 + i%32, gz = mz*32 + i/32;
        if (t.Level == 5 && !t.Grand) {
          int row = Hashing.Mod(gz, 12), xc = Hashing.Mod(gx, 33);
          if (t.Kind == TileKind.Floor && (row is 5 or 6 or 7) && xc != 16 && xc != 17) { corr++; if (t.Sealed) { corrSealed++; cellsSealedCorr.Add((mx,mz)); } }
          if ((row == 4 || row == 8) && Hashing.Mod(gx - 19, 33) % 6 == 2 && xc != 15 && xc != 18 && xc != 16 && xc != 17 && i % 32 != 0 && i / 32 != 0) { if (t.Kind == TileKind.Door) locked++; else if (t.Kind == TileKind.Doorway) doors++; }
          if (t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator && t.Stack == 0) { if (t.Variant == 1) liftModern++; else liftCage++; }
          if (t.Stair == 3) staff++;
        }
      }
    }
    Console.WriteLine($"L5 main corridor floor tiles {corr}, sealed {corrSealed} ({100.0*corrSealed/corr:0.0}%) in {cellsSealedCorr.Count} cells");
    Console.WriteLine($"L5 room door slots: open {doors}, locked {locked} ({100.0*locked/(doors+locked):0}%) ; elevators cage {liftCage} modern {liftModern}; staff stairs {staff}");
  }
}
