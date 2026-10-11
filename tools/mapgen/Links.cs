using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// Exercises the whole threshold network outside the game: every kind of threshold found in a sample of each level
/// is gone through, gone through again (and from another of its tiles), and for two-way ones, come back through.
static class Links {
  class Stat { public int OnSteps, OffSteps, OnLanding, OffLanding, FloorOk, FloorBad, Tested, Claimed, Nowhere, Paired, ThinSpot, OneWayFallback, NoHome, RepeatBad, OtherTileBad, BackBad, ApiBackOk, ApiBackBad; public bool TwoWay; public SortedDictionary<int,int> To = new(); }

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
        // (Up into the shaft over a Level 1 stair core last, so every other threshold is found as it was)
        foreach (double rel in new[] { 3.0, 1.2, -300.0, 6.0 }) {
          Passage p = net.Walked(x, z, t, rel);
          if (p == null) continue;
          string label = $"L{t.Level,-2} " + (t.Kind == TileKind.Pit ? (t.Level == 0 ? "pit" : t.Under == Unders.Collapse ? "fallen-in street" : "open manhole") : t.Stair > 0 && t.Under == 0 ? (!WorldLayout.IsShaftFlight(t) ? "stairs" : t.Zone == WorldLayout.FlightZoneDown ? "flight down"
              : t.Zone == WorldLayout.FlightZoneFun ? "flight up to Fun" : "flight up")
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
      Link? home = !p.TwoWay ? null : walked ? net.HomeFor(p) : new Link(x + 0.5, 1000, z + 0.5, false);
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
      // (Up a Level 1 stair core's flight and out on stairs of the old kind, the way back comes out at the top of the
      // flight down beside it, not at the foot of the one gone up)
      if (link.Marker) { if (net.TryGet((ax, az), out Link back) && back == home) s.ThinSpot++; else s.BackBad++;
        Passage spot = net.Used(ax, az, "thinspot", out _); if (spot != null && net.Take(spot, null) == home) s.ApiBackOk++; else s.ApiBackBad++; }
      else if (p.ReturnFeature != null && layout.FeatureBeside(ax, az, p.ReturnFeature) is { } f && net.TryGet(f, out Link viaFeature) && viaFeature == home) {
        s.Paired++;
        // Through a Level 1 stair core's flight (from layout version 4), or out of one: out on the landing of the flight
        // that is the way back (not on a step, facing away from it), or near the top of stairs of the old kind; and
        // home on the landing of the flight gone through, or, up a core's flight and out on stairs of the old kind, on
        // the landing at the top of the flight down beside it
        bool srcShaft = WorldLayout.IsShaftFlight(layout.TileAt(p.Source.X, p.Source.Z)), backShaft = WorldLayout.IsShaftFlight(layout.TileAt(f.X, f.Z));
        if (srcShaft || backShaft) {
          int hx = (int)Math.Floor(home.Value.X), hz = (int)Math.Floor(home.Value.Z);
          bool arriveOk = backShaft ? net.FlightLanding(f) == link && net.AwayFromFlight(ax, az) != null : !p.Upstairs || ThresholdNetwork.Stairs(layout.TileAt(ax, az));
          bool homeOk = !srcShaft || home == net.FlightLanding(p.Source) && net.AwayFromFlight(hx, hz) != null;
          if (arriveOk && homeOk) s.OnLanding++;
          else if (++s.OffLanding <= 3) Console.WriteLine($"--- {label.Trim()} from {p.Source} to {ax},{az} (step {layout.TileAt(ax, az).Stair}, landing {arriveOk}); home {hx},{hz} (ok {homeOk})");
          // Level 1's floors: a floor up going up (P5 to P5), a floor down going down (B3 to B3)
          Tile st = layout.TileAt(p.Source.X, p.Source.Z), bt = layout.TileAt(f.X, f.Z);
          int sf = WorldLayout.L1FloorOf(st), bf = WorldLayout.L1FloorOf(bt);
          if (sf >= 0 && bf >= 0) {
            bool up = st.Zone != WorldLayout.FlightZoneDown;
            int want = up ? Math.Min(sf + 1, WorldLayout.L1Floors - 1) : Math.Max(sf - 1, 0);
            if (bf == want) s.FloorOk++; else if (++s.FloorBad <= 3) Console.WriteLine($"--- {label.Trim()} from floor {WorldLayout.L1FloorLabel(sf)} to {WorldLayout.L1FloorLabel(bf)}");
          }
        }
        // Up a flight that climbs into the ceiling: out near the top of the flight that is the way back, standing on
        // one of its steps, and the way home is near the top of the flight gone up
        else if (p.Upstairs) {
          Tile on = layout.TileAt(ax, az);
          bool steps = ThresholdNetwork.Stairs(on) && layout.FeatureOrigin(ax, az, ThresholdNetwork.Stairs) == f
            && home is { } h && ThresholdNetwork.Stairs(layout.TileAt((int)Math.Floor(h.X), (int)Math.Floor(h.Z)));
          if (steps) s.OnSteps++;
          else if (++s.OffSteps <= 3) {
            Tile hm = home is { } h2 ? layout.TileAt((int)Math.Floor(h2.X), (int)Math.Floor(h2.Z)) : default;
            Console.WriteLine($"--- {label.Trim()} from {p.Source} to {ax},{az} (L{on.Level} step {on.Stair}, y {link.Y:0.00}); home {home} (L{hm.Level} step {hm.Stair})");
          }
        }
        if (p.ReturnFeature == ThresholdNetwork.Stairs) {
          // Climb the stairs it arrived beside: any step high enough must lead home
          bool ok = false; for (int dz = -8; dz <= 8 && !ok; dz++) for (int dx = -8; dx <= 8 && !ok; dx++) { Tile st = layout.TileAt(f.X + dx, f.Z + dz);
            if (!ThresholdNetwork.Stairs(st) || layout.FeatureOrigin(f.X + dx, f.Z + dz, ThresholdNetwork.Stairs) != f) continue;
            Passage up = net.Walked(f.X + dx, f.Z + dz, st, 3.0); if (up != null) ok = net.Take(up, null) == home; }
          if (ok) s.ApiBackOk++; else s.ApiBackBad++;
        }
        if (p.ReturnFeature == ThresholdNetwork.L1FlightDown || p.ReturnFeature == ThresholdNetwork.L1FlightUp
            || p.ReturnFeature == ThresholdNetwork.L4FlightDown || p.ReturnFeature == ThresholdNetwork.L4FlightUp) {
          // Back the way come: down (or up) into the shaft of the stair core's flight arrived beside, and home
          bool down = p.ReturnFeature == ThresholdNetwork.L1FlightDown || p.ReturnFeature == ThresholdNetwork.L4FlightDown, ok = false, tried = false;
          for (int dz = -8; dz <= 8 && !tried; dz++) for (int dx = -8; dx <= 8 && !tried; dx++) { Tile st = layout.TileAt(f.X + dx, f.Z + dz);
            if (!p.ReturnFeature(st) || layout.FeatureOrigin(f.X + dx, f.Z + dz, p.ReturnFeature) != f) continue;
            Passage back = net.Walked(f.X + dx, f.Z + dz, st, down ? -300.0 : 6.0); if (back != null) { tried = true; ok = net.Take(back, null) == home; } }
          if (ok) s.ApiBackOk++; else s.ApiBackBad++;
        }
        string backKind = kind == "elevator" ? "elevator" : kind == "kitchendoor" ? "kitchendoor" : kind is "door" or "rowhouse" ? (to == 9 ? "locked" : "door")
          : kind == "pooldoor" ? (to == 5 ? "door" : "pooldoor") : kind == "dollhouse" ? (to == 9 ? "locked" : "dollhouse") : null;
        if (backKind != null) { Passage ret = net.Used(f.X, f.Z, backKind, out _); if (ret != null && net.Take(ret, new Link(0, 0, 0, false)) == home) s.ApiBackOk++; else s.ApiBackBad++; }
      }
      else if (net.TryGet(p.Source, out Link own) && own != link) { /* this threshold was itself claimed as a way back before it was used */ s.Paired++; }
      else s.OneWayFallback++;
    }

    foreach (var (label, s) in stats) if (s.OnSteps + s.OffSteps > 0) Console.WriteLine($"{label.Trim()}: {s.OnSteps} arrived on the steps of the way back (home on the steps too), {s.OffSteps} did not");
    foreach (var (label, s) in stats) if (s.OnLanding + s.OffLanding > 0) Console.WriteLine($"{label.Trim()}: {s.OnLanding} arrived where they should (a stairwell's landing, facing away, or near the top of old stairs) with home where it should be, {s.OffLanding} did not; floors {s.FloorOk} right, {s.FloorBad} wrong; thin spot (no stairwell found) {s.ThinSpot}");
    Console.WriteLine($"{taken.Count} thresholds gone through in {sw.ElapsedMilliseconds} ms; {net.Count} links written down\n");
    Console.WriteLine($"{"threshold",-34} {"n",4} {"way",-4} {"paired",6} {"claimd",6} {"thin",5} {"1-way",5} {"nohome",6} {"nowhere",7} {"repeat!",7} {"tile!",5} {"back!",5} {"apiback",8}  leads to");
    foreach (var (label, s) in stats) {
      string to = string.Join(" ", s.To.Select(p => $"{(p.Key == 61 ? "6.1" : p.Key == -1 ? "(back)" : "L" + p.Key)}x{p.Value}"));
      Console.WriteLine($"{label,-34} {s.Tested,4} {(s.To.Count == 0 ? "" : s.TwoWay ? "2" : "1"),-4} {s.Paired,6} {s.Claimed,6} {s.ThinSpot,5} {s.OneWayFallback,5} {s.NoHome,6} {s.Nowhere,7} {s.RepeatBad,7} {s.OtherTileBad,5} {s.BackBad,5} {s.ApiBackOk + "/" + (s.ApiBackOk + s.ApiBackBad),8}  {to}");
    }

    // Saved and loaded again, the network is the same
    byte[] saved = net.Save();
    var copy = new ThresholdNetwork(layout, geometry, seed);
    bool whole = copy.Load(saved);
    int same = 0; foreach (var ((_, sx, sz), v) in taken) if (copy.TryGet((sx, sz), out Link l) && net.TryGet((sx, sz), out Link o) && l == o) same++;
    Console.WriteLine($"\nsave/load: {(whole ? "read" : "NOT READ")}, {copy.Count} of {net.Count} links, {same}/{taken.Count} sources the same");
    // Damaged and foreign data: a cut-off end keeps every whole link before it, a newer version keeps nothing, and
    // neither is taken for a clean read
    var cut = new ThresholdNetwork(layout, geometry, seed);
    bool cutRead = cut.Load(saved[..(saved.Length - 40)]);
    byte[] newer = (byte[])saved.Clone(); newer[0] = 99;
    var future = new ThresholdNetwork(layout, geometry, seed);
    bool futureRead = future.Load(newer);
    var empty = new ThresholdNetwork(layout, geometry, seed);
    bool emptyRead = empty.Load(null) && empty.Load(System.Array.Empty<byte>());
    bool damageOk = !cutRead && cut.Count == Math.Max(0, net.Count - 2) && !futureRead && future.Count == 0 && emptyRead && empty.Count == 0;
    Console.WriteLine($"damaged data: cut-off end kept {cut.Count}, newer version kept {future.Count}, empty read {emptyRead}: {(damageOk ? "ok" : "WRONG")}");
  }
}
