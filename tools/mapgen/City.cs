using Backrooms.Worldgen;
static class City {
  static WorldLayout layout; static Dictionary<(int,int), Tile[]> cache = new();
  static Tile At(int x, int z) { int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z); if (!cache.TryGetValue((mx,mz), out var t)) cache[(mx,mz)] = t = layout.BuildMacro(mx,mz); return t[WorldLayout.TileIndex(x-mx*32, z-mz*32)]; }
  static bool Passable(Tile t) => t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water || t.Kind == TileKind.Floor && (t.Variant == 0 && t.Stack == 0 || t.Variant is Props.Crop or Props.TallGrass) && !t.SupplyBox && t.Stair == 0;
  static bool Escapes(int sx, int sz, int need = 48) {
    var seen = new HashSet<(int,int)> { (sx,sz) }; var q = new Queue<(int,int)>(); q.Enqueue((sx,sz));
    while (q.Count > 0) { var (x,z) = q.Dequeue(); if (Math.Abs(x-sx)+Math.Abs(z-sz) >= need) return true; if (seen.Count > 20000) return true;
      foreach (var (dx,dz) in new[]{(1,0),(-1,0),(0,1),(0,-1)}) { var n=(x+dx,z+dz); if (seen.Contains(n) || !Passable(At(n.Item1,n.Item2))) continue; seen.Add(n); q.Enqueue(n); } }
    return false; }
  public static void Run(WorldLayout l, int smx, int smz, int n) {
    layout = l;
    // Where is the city, and how far from spawn does it start?
    int first = -1;
    for (int r = 0; r < 8000; r += 4) if (layout.LevelAt(smx + r, smz) == 11) { first = r; break; }
    Console.WriteLine($"city starts {first} cells east of spawn ({first * 32 / 1000.0:0.0} km); origin blocks {layout.CityOriginX},{layout.CityOriginZ}");
    int minRing = 99999;
    for (int a = 0; a < 360; a += 3) { double ang = a * Math.PI / 180; for (int r = 0; r < 3000; r += 2) { int lv = layout.LevelAt(smx + (int)(Math.Cos(ang) * r), smz + (int)(Math.Sin(ang) * r)); if (lv == 10) { break; } if (lv == 11) { minRing = Math.Min(minRing, r); break; } } }
    Console.WriteLine($"any L11 inside the rings: {(minRing < 99999 ? "YES at " + minRing : "no")}");
    var sw = System.Diagnostics.Stopwatch.StartNew();
    int found = 0, wrong = 0, trapped = 0; const int N = 120;
    for (ulong k = 1; k <= N; k++) { var a = layout.FindArrival(11, k * 7919UL + 13); if (a == null) continue; found++;
      var (x,z) = a.Value; if (At(x,z).Level != 11) wrong++; if (!Escapes(x,z)) trapped++; }
    Console.WriteLine($"L11 arrivals: found {found}/{N}, wrong level {wrong}, trapped {trapped}  ({sw.ElapsedMilliseconds} ms)");
    // Census of an area round the centre
    int cmx = layout.CityOriginX / 32, cmz = layout.CityOriginZ / 32;
    int m0x = cmx - n / 2, m0z = cmz - n / 2;
    var kinds = new Dictionary<string,int>(); var counts = new Dictionary<string,(int n,int x,int z)>();
    void Count(string name, int x, int z) { counts.TryGetValue(name, out var c); counts[name] = (c.n + 1, c.n == 0 ? x : c.x, c.n == 0 ? z : c.z); }
    sw.Restart();
    for (int mz = 0; mz < n; mz++) for (int mx = 0; mx < n; mx++) {
      var tiles = layout.BuildMacro(m0x + mx, m0z + mz); cache[(m0x+mx, m0z+mz)] = tiles;
      for (int i = 0; i < tiles.Length; i++) { var t = tiles[i]; int x = (m0x + mx) * 32 + i % 32, z = (m0z + mz) * 32 + i / 32;
        if (t.Level != 11) { Count("not L11", x, z); continue; }
        if (t.Depth > 0 && t.Kind == TileKind.Wall && t.Pipe == 0) { kinds.TryGetValue(((CityKind)t.Zone).ToString(), out int c); kinds[((CityKind)t.Zone).ToString()] = c + 1; }
        if (t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator) Count($"elevator {(CityKind)t.Zone}", x, z);
        else if (t.Kind == TileKind.Door) Count($"door {(CityKind)t.Zone}", x, z);
        if (t.Under == Unders.OpenManhole) Count("open manhole", x, z);
        if (t.Under == Unders.Collapse) Count("collapse", x, z);
        if (t.Under == Unders.GarageRamp && t.Stair == 5) Count("garage ramp", x, z);
        if (t.Under == Unders.DarkPassage && t.Kind == TileKind.Doorway) Count("dark doorway", x, z);
        if (t.Under == Unders.FountainDeep) Count("fountain deep", x, z);
        if (t.Under == Unders.WheatPatch) Count("wheat patch", x, z);
        if (t.Under == Unders.Station && t.Stair == 5) Count("station stair", x, z);
        if (t.Variant == Props.Car) Count("car", x, z);
        if (t.Variant == Props.Vending || t.Variant == Props.VendorCart) Count("almond water", x, z);
        if (t.Roof > 0 && t.Depth == 0) Count("sidewalk glitch", x, z);
        if (t.Depth > 0) Count("building tile", x, z);
        if (t.Sealed) Count("sealed", x, z);
      }
    }
    Console.WriteLine($"{n*n} cells in {sw.ElapsedMilliseconds} ms");
    foreach (var (k, v) in kinds.OrderBy(p => p.Key)) Console.WriteLine($"facade {k,-12}: {v,6}");
    foreach (var (k, v) in counts.OrderBy(p => p.Key)) Console.WriteLine($"{k,-22}: {v.n,6}  e.g. {v.x},{v.z}");
  }
}
static class CityMap {
  public static void Run(WorldLayout layout, int n, int dx, int dz) {
    int cmx = layout.CityOriginX / 32 + dx, cmz = layout.CityOriginZ / 32 + dz, m0x = cmx - n / 2, m0z = cmz - n / 2, size = n * 32;
    var all = new Tile[size, size];
    for (int mz = 0; mz < n; mz++) for (int mx = 0; mx < n; mx++) { var t = layout.BuildMacro(m0x + mx, m0z + mz); for (int i = 0; i < 1024; i++) all[mx * 32 + i % 32, mz * 32 + i / 32] = t[i]; }
    using var w = new BinaryWriter(File.Create("city.bin")); w.Write(size);
    for (int z = 0; z < size; z++) for (int x = 0; x < size; x++) { var t = all[x, z];
      w.Write((byte)t.Kind); w.Write((byte)t.Floor); w.Write((byte)t.Pattern); w.Write((byte)Math.Min((int)t.Variant, 255)); w.Write(t.Depth); w.Write(t.Zone); w.Write(t.Under); w.Write(t.Detail); w.Write(t.Overhead); w.Write(t.Roof); }
    Console.WriteLine($"city map {size}x{size} from blocks {m0x*32},{m0z*32}");
  }
}
static class NoclipFind {
  public static void Run(WorldLayout layout, int smx, int smz) {
    // Walk out east from spawn into Level 10, and look for barn walls that aren't there
    int found = 0, barns = 0;
    for (int r = 0; r < 1600 && found < 5; r += 1) {
      int mx = smx + r, mz = smz;
      if (layout.LevelAt(mx, mz) != 10) continue;
      for (int dz = -20; dz <= 20 && found < 5; dz++) {
        var tiles = layout.BuildMacro(mx, mz + dz);
        for (int i = 0; i < 1024; i++) {
          if (tiles[i].Pattern == WallPattern.BarnRed && tiles[i].Kind == TileKind.Wall && i % 32 == 0) barns++;
          if (tiles[i].Under == Unders.Noclip) { found++; Console.WriteLine($"noclip barn wall at {mx*32 + i%32},{(mz+dz)*32 + i/32} kind {tiles[i].Kind} pattern {tiles[i].Pattern}"); }
        }
      }
      r += 40;
    }
    Console.WriteLine($"found {found}");
  }
}
