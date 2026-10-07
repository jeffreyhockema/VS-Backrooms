using Backrooms.Worldgen;
static class Unreach {
  // Flood from an arrival through walkable tiles; tally unreachable walkable tiles by what they are
  public static void Run(WorldLayout layout, int n) {
    var a = layout.FindArrival(11, 99991UL).Value; int x0 = a.X - n * 16, z0 = a.Z - n * 16, size = n * 32;
    bool W(Tile t) => t.Kind is TileKind.Doorway or TileKind.Water || t.Kind == TileKind.Floor && WorldLayoutAccess.Walk(t);
    var seen = new bool[size * size]; var q = new Queue<(int, int)>(); q.Enqueue((a.X - x0, a.Z - z0)); seen[(a.Z - z0) * size + a.X - x0] = true;
    while (q.Count > 0) { var (x, z) = q.Dequeue(); foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) }) { int nx = x + dx, nz = z + dz; if (nx < 0 || nz < 0 || nx >= size || nz >= size || seen[nz * size + nx]) continue; if (!W(layout.TileAt(x0 + nx, z0 + nz))) continue; seen[nz * size + nx] = true; q.Enqueue((nx, nz)); } }
    var tally = new Dictionary<string, int>(); var example = new Dictionary<string, (int, int)>();
    for (int z = 40; z < size - 40; z++) for (int x = 40; x < size - 40; x++) { Tile t = layout.TileAt(x0 + x, z0 + z); if (!W(t) || t.Sealed || seen[z * size + x]) continue;
      string k = t.Depth > 0 && t.Kind != TileKind.Water ? $"inside {(CityKind)t.Zone}" : $"outside {(CityKind)t.Zone} {t.Floor}";
      tally[k] = tally.GetValueOrDefault(k) + 1; if (!example.ContainsKey(k)) example[k] = (x0 + x, z0 + z); }
    foreach (var (k, v) in tally.OrderByDescending(p => p.Value)) Console.WriteLine($"{k,-34} {v,6}  e.g. {example[k]}");
  }
}
static class WorldLayoutAccess { public static bool Walk(Tile t) => (t.Stack == 0 || t.Variant != 0) && !t.SupplyBox && t.Stair == 0 && t.Variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable or Props.Bedroll or Props.Crop or Props.TallGrass or Props.Reeds or Props.Tripwire or Props.FieldGate or Props.MachineParts; }
