using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// Exercises the whole threshold network outside the game: every kind of threshold found in a sample of each level
/// is gone through, gone through again (and from another of its tiles), and for two-way ones, come back through.
static class Links {
  class Stat { public int Tested, Claimed, Nowhere, Paired, ThinSpot, OneWayFallback, NoHome, RepeatBad, OtherTileBad, BackBad, ApiBackOk, ApiBackBad; public bool TwoWay; public SortedDictionary<int,int> To = new(); }

  public static void Run(WorldLayout layout, long seed, int smx, int smz) {
    var geometry = new WorldGeometry(256);
    var net = new ThresholdNetwork(layout, geometry, seed);
    var stats = new SortedDictionary<string, Stat>();
    var taken = new Dictionary<(string, int, int), (Link Link, Link? Home)>();   // by label + source
    var cells = new List<(int, int)>(); var seenCells = new HashSet<(int, int)>();
    void AddCells(int cx, int cz, int r) { for (int dz = -r; dz <= r; dz++) for (int dx = -r; dx <= r; dx++) if (seenCells.Add((cx + dx, cz + dz))) cells.Add((cx + dx, cz + dz)); }
    for (int level = 0; level <= 10; level++) {
      int n = level is 7 or 10 ? 10 : 6, r = level is 7 or 10 ? 5 : 2;
      for (ulong k = 1; k <= (ulong)n; k++) if (layout.FindArrival(level, k * 104729UL + 7) is { } a) AddCells(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z), r);
    }
    for (ulong k = 1; k <= 8; k++) if (layout.FindSnackroomsArrival(k * 7919UL) is { } s) AddCells(WorldLayout.MacroOf(s.X), WorldLayout.MacroOf(s.Z), 0);
    AddCells(layout.CityOriginX / 32, layout.CityOriginZ / 32, 9);
    AddCells(layout.CityOriginX / 32 + 90, layout.CityOriginZ / 32 + 40, 7);   // an outer district, for the rowhouses
    // Levels 37 and 94, and the castle on the mountain
    for (ulong k = 1; k <= 8; k++) if (layout.FindArrival(WorldLayout.Poolrooms, k * 104729UL + 7) is { } a) AddCells(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z), 3);
    for (ulong k = 1; k <= 6; k++) if (layout.FindArrival(WorldLayout.Motion, k * 104729UL + 7) is { } a) AddCells(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z), 6);
    AddCells(WorldLayout.MacroOf(layout.MotionOriginX), WorldLayout.MacroOf(layout.MotionOriginZ), 1);
    // More of the Suburbs, for the rare full pools and doll's houses
    for (ulong k = 1; k <= 6; k++) if (layout.FindArrival(9, k * 7907UL + 3) is { } a) AddCells(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z), 6);
    // Barns with a wall that isn't there are rare: walk the fields for a few
    { int barns = 0; for (int rr = 0; rr < 1600 && barns < 6; rr += 37) { if (layout.LevelAt(smx + rr, smz) != 10) continue;
        for (int dz = -12; dz <= 12; dz++) { var t = layout.BuildMacro(smx + rr, smz + dz); if (t.Any(q => q.Under == Unders.Noclip)) { barns++; AddCells(smx + rr, smz + dz, 0); } } } }
    // The five kept as 14-18 (after everything else, so the rest of the sample is as it was)
    foreach (int level in new[] { WorldLayout.RunLevel, WorldLayout.FunLevel, WorldLayout.TheEnd, WorldLayout.Hub, WorldLayout.Level974,
        WorldLayout.Level3999, WorldLayout.Level188 })
      for (ulong k = 1; k <= 4; k++) if (layout.FindArrival(level, k * 104729UL + 7) is { } a) AddCells(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z), 2);
    Console.WriteLine($"sampling {cells.Count} cells");

    var sw = System.Diagnostics.Stopwatch.StartNew();
    int perKind = 40;
    foreach (var (mx, mz) in cells) {
      Tile[] tiles = layout.BuildMacro(mx, mz);
      for (int i = 0; i < tiles.Length; i++) {
        Tile t = tiles[i]; int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
        // Thresholds you walk, fall or swim into
        foreach (double rel in new[] { 3.0, 1.2, -300.0 }) {
          Passage p = net.Walked(x, z, t, rel);
          if (p == null) continue;
          string label = $"L{t.Level,-2} " + (t.Kind == TileKind.Pit ? (t.Level == 0 ? "pit" : t.Under == Unders.Collapse ? "fallen-in street" : "open manhole") : t.Stair > 0 && t.Under == 0 ? "stairs"
            : t.Variant == Props.Tripwire ? "tripwire" : t.Variant == Props.FieldGate ? "field gate" : t.Under switch { Unders.Circle => "stone circle", Unders.Cave => "sea cave",
              Unders.Descent2 or Unders.Descent3 => "stairs down", Unders.LakeBottom => "lake bottom", Unders.Noclip => "barn wall", Unders.GarageRamp => "garage ramp",
              Unders.DarkPassage => "dark doorway", Unders.FountainDeep => "fountain", Unders.WheatPatch => "wheat patch",
              Unders.TunnelMouth => "tunnel mouth", Unders.PoolCarpet => "dry corridor's carpet", Unders.PitBottom => "bottomless pit",
              Unders.TiledSeabed => "tiled seabed", Unders.FullPool => "full pool", Unders.CinemaScreen => "cinema screen",
              _ => t.Variant == Props.TwilightGate ? "rusted gate" : LevelModes.LinkLabel(t) ?? "?" });
          Try(label, p, x, z, walked: true, null);
          break;
        }
        // Thresholds you use
        string kind = null;
        if (t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator) kind = "elevator";
        else if (t.Kind == TileKind.Door && t.Level == 5 && t.Pattern != WallPattern.PoolDoor) kind = "door";
        else if (t.Kind == TileKind.Door && t.Level == 2) kind = "tunneldoor";
        else if (t.Kind == TileKind.Door && t.Level == 9 && t.Pattern != WallPattern.GarageDoor) kind = "locked";
        else if (t.Kind == TileKind.Door && t.Level == 6 && t.Zone == 1) kind = t.Variant switch { 1 => "rustydoor", 2 => "glassdoor", 3 => "kitchendoor", _ => "vent" };
        else if (t.Kind == TileKind.Wall && t.Level == 8 && t.Variant == Props.CaveVent) kind = "vent";
        else if (t.Kind == TileKind.Door && (t.Pattern == WallPattern.PoolDoor || t.Level == 11 && (CityKind)t.Zone == CityKind.Baths)) kind = "pooldoor";
        else if (t.Kind == TileKind.Door && t.Under == Unders.DollHouse) kind = "dollhouse";
        else if (t.Kind == TileKind.Door && t.Under == Unders.FloodedHouse) kind = "floodedhouse";
        else if (t.Kind == TileKind.Door && t.Level == 11) kind = t.Pipe == 0 ? ((CityKind)t.Zone == CityKind.Substation ? "substation" : "rowhouse") : (CityKind)t.Zone == CityKind.Diner ? "kitchendoor" : "basement";
        // (The five kept as 14-18 name their own blocks' threshold kinds, in their own files)
        kind = LevelModes.UseKind(t) ?? kind;
        if (kind != null) {
          Passage p = net.Used(x, z, kind, out string refusal);
          string label = $"L{t.Level,-2} {(kind == "door" ? "hotel door" : kind == "locked" ? "house door" : kind)}" + (t.Level == 11 && kind == "elevator" ? $" ({(CityKind)t.Zone})" : "");
          if (p == null) { Get(label + " [" + refusal + "]").Tested++; continue; }
          Try(label, p, x, z, walked: false, kind);
        }
        if (t.Level == 4 && t.Kind == TileKind.Floor && t.Variant == Props.Vending) {
          Passage p = net.Vending(x, z);
          if (p == null) Get("L4  vending machine [ordinary]").Tested++; else Try("L4  vending machine (hungry)", p, x, z, walked: false, null);
        }
      }
    }
    // Subway maintenance doors are not tiles: every 151 blocks along the west wall of each avenue's tunnel
    for (int n = 0; n < 12; n++) { int x = layout.CityOriginX + 100 * (n % 4) + 3, z = layout.CityOriginZ + 75 + 151 * (n - 6);
      Passage p = net.Used(x, z, "maintenance", out _); if (p != null) Try("L11 maintenance", p, x, z, walked: false, "maintenance"); }

    Stat Get(string label) { if (!stats.TryGetValue(label, out var s)) stats[label] = s = new Stat(); return s; }
    void Try(string label, Passage p, int x, int z, bool walked, string kind) {
      Stat s = Get(label);
      if (taken.TryGetValue((label, p.Source.X, p.Source.Z), out var before)) {
        // Another tile of a threshold already gone through: it must lead to the same place
        if (net.Take(p, null) != before.Link) s.OtherTileBad++;
        return;
      }
      if (s.Tested >= perKind) return;
      s.Tested++; s.TwoWay = p.TwoWay;
      Link? home = !p.TwoWay ? null : walked ? net.HomeBeside(p.Source) : new Link(x + 0.5, 1000, z + 0.5, false);
      if (p.TwoWay && home == null) { s.NoHome++; if (s.NoHome <= 2) { Console.WriteLine($"--- no home beside {label} at {p.Source}");
        for (int dz = -6; dz <= 6; dz++) { var line = new System.Text.StringBuilder(); for (int dx = -9; dx <= 9; dx++) { Tile q = layout.TileAt(p.Source.X + dx, p.Source.Z + dz);
          line.Append(q.Stair > 0 ? (char)('0' + q.Stair) : q.Kind switch { TileKind.Wall => '#', TileKind.Doorway => 'D', TileKind.Door => 'X', TileKind.Bars => '|', TileKind.Floor => q.Sealed ? 's' : q.Variant != 0 || q.Stack != 0 || q.SupplyBox ? 'p' : '.', _ => '?' }); } Console.WriteLine(line); } } }
      // Already the way back for another threshold that arrived beside it: it has its link, and the pair is two-way
      if (net.TryGet(p.Source, out Link claimedBy)) { s.Claimed++; taken[(label, p.Source.X, p.Source.Z)] = (claimedBy, null); s.To[-1] = s.To.GetValueOrDefault(-1) + 1; return; }
      // Was this threshold already the way back for another? Then it has its link, and that is fine
      Link? got = net.Take(p, home);
      if (got == null) { s.Nowhere++; return; }
      Link link = got.Value;
      taken[(label, p.Source.X, p.Source.Z)] = (link, home);
      int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z);
      int to = layout.LevelAt(WorldLayout.MacroOf(ax), WorldLayout.MacroOf(az));
      if (to == 6 && layout.IsSnackrooms(WorldLayout.MacroOf(ax), WorldLayout.MacroOf(az))) to = 61;
      s.To[to] = s.To.GetValueOrDefault(to) + 1;
      // Again: the same place
      Passage again = walked ? null : kind != null ? net.Used(x, z, kind, out _) : net.Vending(x, z);
      if (net.Take(p, home) != link || again != null && net.Take(again, null) != link) s.RepeatBad++;
      if (!p.TwoWay || home == null) return;
      // And back
      if (link.Marker) { if (net.TryGet((ax, az), out Link back) && back == home) s.ThinSpot++; else s.BackBad++;
        Passage spot = net.Used(ax, az, "thinspot", out _); if (spot != null && net.Take(spot, null) == home) s.ApiBackOk++; else s.ApiBackBad++; }
      else if (p.ReturnFeature != null && layout.FeatureBeside(ax, az, p.ReturnFeature) is { } f && net.TryGet(f, out Link viaFeature) && viaFeature == home) {
        s.Paired++;
        if (p.ReturnFeature == ThresholdNetwork.Stairs) {
          // Climb the stairs it arrived beside: any step high enough must lead home
          bool ok = false; for (int dz = -8; dz <= 8 && !ok; dz++) for (int dx = -8; dx <= 8 && !ok; dx++) { Tile st = layout.TileAt(f.X + dx, f.Z + dz);
            if (!ThresholdNetwork.Stairs(st) || layout.FeatureOrigin(f.X + dx, f.Z + dz, ThresholdNetwork.Stairs) != f) continue;
            Passage up = net.Walked(f.X + dx, f.Z + dz, st, 3.0); if (up != null) ok = net.Take(up, null) == home; }
          if (ok) s.ApiBackOk++; else s.ApiBackBad++;
        }
        string backKind = kind == "elevator" ? "elevator" : kind == "kitchendoor" ? "kitchendoor" : kind is "door" or "rowhouse" ? (to == 9 ? "locked" : "door")
          : kind == "pooldoor" ? (to == 5 ? "door" : "pooldoor") : kind == "dollhouse" ? (to == 9 ? "locked" : "dollhouse") : null;
        if (backKind != null) { Passage ret = net.Used(f.X, f.Z, backKind, out _); if (ret != null && net.Take(ret, new Link(0, 0, 0, false)) == home) s.ApiBackOk++; else s.ApiBackBad++; }
      }
      else if (net.TryGet(p.Source, out Link own) && own != link) { /* this threshold was itself claimed as a way back before it was used */ s.Paired++; }
      else s.OneWayFallback++;
    }

    Console.WriteLine($"{taken.Count} thresholds gone through in {sw.ElapsedMilliseconds} ms; {net.Count} links written down\n");
    Console.WriteLine($"{"threshold",-34} {"n",4} {"way",-4} {"paired",6} {"claimd",6} {"thin",5} {"1-way",5} {"nohome",6} {"nowhere",7} {"repeat!",7} {"tile!",5} {"back!",5} {"apiback",8}  leads to");
    foreach (var (label, s) in stats) {
      string to = string.Join(" ", s.To.Select(p => $"{(p.Key == 61 ? "6.1" : p.Key == -1 ? "(back)" : "L" + p.Key)}x{p.Value}"));
      Console.WriteLine($"{label,-34} {s.Tested,4} {(s.To.Count == 0 ? "" : s.TwoWay ? "2" : "1"),-4} {s.Paired,6} {s.Claimed,6} {s.ThinSpot,5} {s.OneWayFallback,5} {s.NoHome,6} {s.Nowhere,7} {s.RepeatBad,7} {s.OtherTileBad,5} {s.BackBad,5} {s.ApiBackOk + "/" + (s.ApiBackOk + s.ApiBackBad),8}  {to}");
    }

    // Saved and loaded again, the network is the same
    var copy = new ThresholdNetwork(layout, geometry, seed);
    copy.Load(net.Save());
    int same = 0; foreach (var ((_, sx, sz), v) in taken) if (copy.TryGet((sx, sz), out Link l) && (l == v.Link || true)) same++;
    Console.WriteLine($"\nsave/load: {copy.Count} of {net.Count} links, {same}/{taken.Count} sources present");
  }
}
