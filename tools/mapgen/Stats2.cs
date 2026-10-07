using Backrooms.Worldgen;
static class Stats2 {
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    int l4Door=0, l4Way=0, l1Pipe=0, l1Drip=0, l3Cable=0, l3Droop=0, confSlots=0, confChairs=0, l5Rooms=0, l5Empty=0, l5Wood=0, l5Beds=0;
    var l5RoomSeen = new HashSet<(int,int)>();
    for (int mz = m0z; mz < m0z + n; mz++) for (int mx = m0x; mx < m0x + n; mx++) {
      var tiles = l.BuildMacro(mx, mz);
      for (int i = 0; i < 1024; i++) { var t = tiles[i]; int gx = mx*32+i%32, gz = mz*32+i/32;
        if (t.Level == 4 && t.Pattern == WallPattern.Drywall && i%32!=0 && i/32!=0) { int ix = Hashing.Mod(gx,8), iz = Hashing.Mod(gz,8); if ((ix==4&&iz==2)||(ix==2&&iz==5)) { if (t.Kind==TileKind.Door) l4Door++; else if (t.Kind==TileKind.Doorway) l4Way++; } }
        if (t.Level == 4 && t.Pattern == WallPattern.OfficeGlass) { }
        if (t.Level == 4 && t.Variant == Props.ConferenceTable && Hashing.Mod(gx,8)==4 && Hashing.Mod(gz,8)==4) { confSlots += 6; 
            foreach (var (dx,dz) in new[]{(0,-1),(1,-1),(0,2),(1,2),(2,0),(2,1)}) { int lx=i%32+dx, lz=i/32+dz; if (lx<32&&lz<32&&lx>=0&&lz>=0 && tiles[lz*32+lx].Variant==Props.OfficeChair) confChairs++; } }
        if (t.Level == 1 && (t.Pipe is Pipes.RunX or Pipes.RunZ or Pipes.DripX or Pipes.DripZ) && t.Floor != FloorKind.Concrete) { l1Pipe++; if (t.Pipe is Pipes.DripX or Pipes.DripZ) l1Drip++; }
        if (t.Level == 3 && t.Pipe is Pipes.CableX or Pipes.CableZ or Pipes.CableDroopX or Pipes.CableDroopZ) { l3Cable++; if (t.Pipe is Pipes.CableDroopX or Pipes.CableDroopZ) l3Droop++; }
        if (t.Level == 5 && !t.Grand && t.Kind == TileKind.Floor) { int row = Hashing.Mod(gz,12), xc = Hashing.Mod(gx,33); int u = Hashing.Mod(gx-19,33);
          if ((row is 1 or 2 or 3 or 9 or 10 or 11) && xc != 16 && xc != 17 && u < 29 && u%6 == 2 && (row == 2 || row == 10) && i/32 + (row==2?2:-2) is >= 0 and < 32 && tiles[(i/32 + (row==2?2:-2))*32 + i%32].Kind == TileKind.Doorway) { l5Rooms++; if (t.Variant == 0) l5Empty++; if (t.Floor is FloorKind.HotelWood or FloorKind.HotelRug) l5Wood++; } }
      }
    }
    Console.WriteLine($"L4 office doors locked {l4Door}, open {l4Way} (locked share of all room doors {100.0*l4Door/(l4Door+l4Way):0.0}%; offices are 42% of rooms -> expect ~8.4%)");
    Console.WriteLine($"L4 conference chair fill {confChairs}/{confSlots} = {100.0*confChairs/Math.Max(1,confSlots):0}% (expect ~70%)");
    Console.WriteLine($"L1 hall pipes {l1Pipe}, drips {100.0*l1Drip/Math.Max(1,l1Pipe):0.0}% (expect 3.5%)  L3 cables {l3Cable}, droops {100.0*l3Droop/Math.Max(1,l3Cable):0.0}% (expect 7%)");
    Console.WriteLine($"L5 reachable room middle tiles (x=2,row middle) {l5Rooms}, no bed {100.0*l5Empty/Math.Max(1,l5Rooms):0}% (expect ~35% empty, staff ~2.5%), wood {100.0*l5Wood/Math.Max(1,l5Rooms):0}% (expect 30%)");
  }
}
