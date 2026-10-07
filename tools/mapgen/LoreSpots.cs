using Backrooms.Worldgen;
static class LoreSpots {
  public static void Run(WorldLayout layout, int smx, int smz) {
    var found = new Dictionary<string, int>();
    void Report(string label, int x, int z, int back = 3) {
      found.TryGetValue(label, out int n); if (n >= 1) return;
      // Stand a few tiles away, on open floor, looking at it
      (int X, int Z)? best = null; int bestD = 0;
      for (int dz = -6; dz <= 6; dz++) for (int dx = -6; dx <= 6; dx++) { int d = Math.Abs(dx) + Math.Abs(dz); if (d < 2 || d > 7) continue; if (dx != 0 && dz != 0) continue;
        bool clear = true; for (int k = 1; k <= d && clear; k++) { Tile t = layout.TileAt(x + Math.Sign(dx) * k, z + Math.Sign(dz) * k); clear = t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.Water && (k < d ? t.Variant == 0 || t.Variant == Props.MachineParts : t.Variant == 0) && t.Stack == 0 && !t.SupplyBox; }
        if (clear && d > bestD) { bestD = d; best = (x + dx, z + dz); } }
      if (best == null) return;
      found[label] = n + 1;
      double yaw = Math.Atan2(x - best.Value.X, -(z - best.Value.Z)) * 180 / Math.PI;
      Console.WriteLine($"{label}|{x},{z}|{best.Value.X + 0.5} {best.Value.Z + 0.5}|{yaw:0}");
    }
    // Level 0: a Red Room and the Manila Room
    for (int r = 6; r < 60 && !(found.ContainsKey("redroom") && found.ContainsKey("manila")); r++) for (int a = 0; a < 360; a += 2) { int mx = smx + (int)(r * Math.Cos(a * Math.PI / 180)), mz = smz + (int)(r * Math.Sin(a * Math.PI / 180));
      if (layout.IsRedRoom(mx, mz)) { var t = layout.BuildMacro(mx, mz); for (int i = 0; i < 1024; i++) if (t[i].Ceiling == CeilingKind.LampRed) { Report("redroom", mx * 32 + i % 32, mz * 32 + i / 32); break; } }
      if (layout.IsManilaMacro(mx, mz)) Report("manila", mx * 32 + 16, mz * 32 + 16); }
    for (int level = 1; level <= 8; level++) for (ulong k = 1; k <= 12; k++) { if (layout.FindArrival(level, k * 104729UL + 7) is not { } arr) continue;
      int cmx = WorldLayout.MacroOf(arr.X), cmz = WorldLayout.MacroOf(arr.Z);
      for (int dmz = -3; dmz <= 3; dmz++) for (int dmx = -3; dmx <= 3; dmx++) { var tiles = layout.BuildMacro(cmx + dmx, cmz + dmz);
        for (int i = 0; i < 1024; i++) { Tile t = tiles[i]; int x = (cmx + dmx) * 32 + i % 32, z = (cmz + dmz) * 32 + i / 32; if (t.Level != level) continue;
          if (level == 1 && t.Kind == TileKind.Wall && t.Variant == Decor.Camera) Report(t.Pattern == WallPattern.Concrete ? "camera-concrete" : "camera-white", x, z);
          if (level == 1 && t.Kind == TileKind.Floor && t.Variant == Props.TrafficSign) Report("trafficsign", x, z);
          if (level == 2 && t.Kind == TileKind.Door) Report("tunneldoor", x, z);
          if (level == 2 && t.Kind == TileKind.Floor && t.Variant == Props.Shelf) Report("storeroom", x, z);
          if (level == 2 && t.Kind == TileKind.Floor && t.Variant == Props.Trolley) Report("trolley", x, z);
          if (level == 2 && t.Kind == TileKind.Floor && t.Variant == Props.MachineParts) Report("machineparts", x, z);
          if (level == 3 && t.Kind == TileKind.Floor && t.Variant == Props.Boiler) Report("boiler", x, z);
          if (level == 3 && t.Kind == TileKind.Wall && t.Variant == Decor.Plaque) Report("plaque", x, z);
          if (level == 5 && t.Overhead == Overheads.CeilingFan) Report("fan", x, z);
          if (level == 6 && t.Kind == TileKind.Wall && t.Variant == Decor.DeadSwitch) Report("deadswitch", x, z);
          if (level == 7 && t.Kind == TileKind.Floor && t.Variant == Props.Tent) Report("camp", x, z);
          if (level == 8 && t.Kind == TileKind.Wall && t.Variant == Props.AlmondSeep) Report("seep", x, z);
        } } }
  }
}
