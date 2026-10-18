using Backrooms.Worldgen;
static class Deep {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static bool Passable(Tile t) => t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water || t.Kind == TileKind.Floor && (t.Variant == 0 && t.Stack == 0 || t.Variant is Props.Crop or Props.TallGrass or Props.Tripwire or Props.Reeds or Props.FieldGate or Props.Flowers or Props.Vegetable or Props.GlowcapRed or Props.GlowcapMixed) && !t.SupplyBox && t.Stair == 0;
  static bool Escapes(int sx, int sz, int need = 40) {
    var seen = new HashSet<(int,int)> { (sx,sz) }; var q = new Queue<(int,int)>(); q.Enqueue((sx,sz));
    while (q.Count > 0) { var (x,z) = q.Dequeue(); if (Math.Abs(x-sx)+Math.Abs(z-sz) >= need) return true; if (seen.Count > 20000) return true;
      foreach (var (dx,dz) in new[]{(1,0),(-1,0),(0,1),(0,-1)}) { var n=(x+dx,z+dz); if (seen.Contains(n) || !Passable(At(n.Item1,n.Item2))) continue; seen.Add(n); q.Enqueue(n); } }
    return false; }

  static void Dump(int cx, int cz) {
    Console.WriteLine($"--- trapped L10 at {cx},{cz}");
    for (int z = cz - 8; z <= cz + 8; z++) { var line = new System.Text.StringBuilder();
      for (int x = cx - 20; x <= cx + 20; x++) { var t = At(x,z); char c = t.Kind switch { TileKind.Wall => '#', TileKind.Doorway => 'D', TileKind.Door => 'X', TileKind.Bars => '|', TileKind.Water => '~', _ => Passable(t) ? '.' : 'p' };
        if (x == cx && z == cz) c = '@'; line.Append(c); }
      Console.WriteLine(line); } }
  public static void Run(WorldLayout l, int m0x, int m0z, int n) {
    layout = l;
    const int N = 150;
    for (int level = 6; level <= 10; level++) {
      int found = 0, wrong = 0, trapped = 0, snack = 0;
      for (ulong k = 1; k <= N; k++) { var a = layout.FindArrival(level, k * 7919UL + 13); if (a == null) continue; found++;
        var (x,z) = a.Value; if (At(x,z).Level != level) wrong++; if (layout.IsSnackrooms(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z))) snack++; if (!Escapes(x,z)) { trapped++; if (trapped == 1 && level is 8 or 10) Dump(x, z); } }
      Console.WriteLine($"Level {level,2} open    : found {found}/{N}, wrong level {wrong}, trapped {trapped}, in snackrooms {snack}");
    }
    { int found = 0, ok = 0, trapped = 0;
      for (ulong k = 1; k <= N; k++) { var a = layout.FindSnackroomsArrival(k * 7919UL + 13); if (a == null) continue; found++;
        var (x,z) = a.Value; if (layout.IsSnackrooms(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z))) ok++; if (!Escapes(x,z,12)) trapped++; }
      Console.WriteLine($"Snackrooms      : found {found}/{N}, really snackrooms {ok}, trapped {trapped}"); }
    { int found = 0, ok = 0;
      for (ulong k = 1; k <= N; k++) { var a = layout.FindEntryRoomArrival(k * 7919UL + 13); if (a == null) continue; found++;
        var (x,z) = a.Value; var t = At(x,z); if (t.Level == 7 && t.Zone == 1) ok++; }
      Console.WriteLine($"L7 entry rooms  : found {found}/{N}, ok {ok}"); }

    // Thresholds in the sampled area
    var counts = new Dictionary<string,(int n,int x,int z)>();
    void Count(string name, int x, int z) { counts.TryGetValue(name, out var c); counts[name] = (c.n + 1, c.n == 0 ? x : c.x, c.n == 0 ? z : c.z); }
    for (int mz = 0; mz < n; mz++) for (int mx = 0; mx < n; mx++) {
      var tiles = layout.BuildMacro(m0x + mx, m0z + mz);
      for (int i = 0; i < tiles.Length; i++) { var t = tiles[i]; int x = (m0x + mx) * 32 + i % 32, z = (m0z + mz) * 32 + i / 32;
        if (t.Level == 5 && t.Stair == 1) Count("L5 staff stairs", x, z);
        if (t.Level == 6 && t.Variant == Props.Tripwire && t.Kind == TileKind.Floor && t.Zone == 0) Count("L6 tripwire", x, z);
        // (From layout version 9 a stairwell's landing has four such tiles: the one with the sound of waves under it)
        if (t.Level == 6 && t.Under == Unders.Descent3 && (layout.Version < 9 || t.Detail == WorldLayout.L6WaveEcho)) Count("L6 descent", x, z);
        if (t.Level == 7 && t.Zone == WorldLayout.L7ZoneBellHatch) Count(t.Height >= WorldLayout.MidnightDepth ? "L7 sunken room, midnight" : "L7 sunken room, twilight", x, z);
        if (t.Level == 7 && layout.Version >= 9 && t.Detail == WorldLayout.L7EntryFoot) Count("L7 entry room foot", x, z);
        if (t.Level == 6 && t.Zone == 1 && t.Kind == TileKind.Door) Count($"L6.1 exit v{t.Variant}", x, z);
        if (t.Level == 6 && t.Zone == 1 && t.Kind == TileKind.Doorway && t.Variant >= Decor.First) Count("L6.1 shop sign", x, z);
        if (t.Level == 7 && t.Under == Unders.Circle) Count("L7 circle", x, z);
        if (t.Level == 7 && t.Under == Unders.Cave) Count("L7 cave", x, z);
        if (t.Level == 7 && t.Zone == 1 && t.Stack == 0 && t.Kind == TileKind.Floor) Count("L7 entry room floor", x, z);
        if (t.Level == 6 && t.Zone == 1 && t.Variant == Props.VendingPile) Count("L6.1 vending pile", x, z);
        if (t.Level == 6 && t.Zone == 1 && t.Kind == TileKind.Doorway && t.Detail == WorldLayout.SnackVendingFront) Count("L6.1 vending room door", x, z);
        if (t.Level == 7 && t.Detail == WorldLayout.L7Pillar) Count(t.Depth > 0 ? "L7 sea stack tile" : "L7 island pillar tile", x, z);
        if (t.Level == 7 && t.Kind == TileKind.Floor && t.Height > 0) Count($"L7 island h{t.Height}", x, z);
        if (t.Level == 7 && t.Kind == TileKind.Floor && t.Detail == WorldLayout.L7TarUnder) Count("L7 shelter tar", x, z);
        if (t.Level == 8 && t.Variant is Props.GlowcapRed or Props.GlowcapMixed) Count("L8 glowcaps by road", x, z);
        if (t.Level == 8 && t.Variant == Props.RoadLamp) Count($"L8 lamp {t.Pier}", x, z);
        if (t.Level == 8 && t.Kind == TileKind.Floor && t.Height > 0) Count($"L8 roof {t.Height}", x, z);
        if (t.Level == 8 && layout.IsNinthRoad(x, z)) Count("L8 road", x, z);
        if (t.Level == 8 && t.Variant == Props.CaveVent) Count("L8 vent", x, z);
        if (t.Level == 9 && t.Variant == Props.FieldGate) Count("L9 field gate", x, z);
        if (t.Level == 9 && t.Floor == FloorKind.HouseCarpet) Count("L9 house", x, z);
        if (t.Level == 10 && t.Under == Unders.LakeBottom) Count("L10 lake bottom", x, z);
        if (t.Level == 10 && layout.IsPasture(x, z)) Count("L10 pasture", x, z);
        if (t.Level == 10 && t.Variant == Props.Crop) Count("L10 crop", x, z);
      }
    }
    foreach (var (k, v) in counts.OrderBy(p => p.Key)) Console.WriteLine($"{k,-22}: {v.n,6}  e.g. {v.x},{v.z}");
  }
}
