using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Part = Backrooms.Worldgen.WorldLayout.L188Part;

/// <summary>Level 188's harness modes (this file is the level's own; see docs/new-levels/CONTRACT.md).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 188stats [cells]: checks the building (where it is, its cells, the courtyard, 32 windows a storey, the twelve windows
    /// onto other places and their sealed rooms, the stair, the fire doors, the hatch), the ways round its ground storey,
    /// arrivals, every one of its thresholds, and that its windows in Levels 0, 1 and Fun change nothing else there.
    /// 188map: the ground storey as text.
    /// </summary>
    static bool L188Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "188map") { L188Map(layout); return true; }
        if (mode != "188stats") return false;
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        int x0 = layout.L188BuildX0, z0 = layout.L188BuildZ0;
        Console.WriteLine($"building at {x0},{z0} (cells {WorldLayout.MacroOf(x0)}..{WorldLayout.MacroOf(x0 + 87)} x {WorldLayout.MacroOf(z0)}..{WorldLayout.MacroOf(z0 + 57)})");

        // The region: every cell the building touches is the level's; count the region's cells
        int regionCells = 0;
        for (int mz = WorldLayout.MacroOf(z0) - 6; mz <= WorldLayout.MacroOf(z0) + 6; mz++)
            for (int mx = WorldLayout.MacroOf(x0) - 6; mx <= WorldLayout.MacroOf(x0) + 6; mx++)
                if (layout.LevelAt(mx, mz) == WorldLayout.Level188) regionCells++;
        Console.WriteLine($"region: {regionCells} cells");
        for (int mz = WorldLayout.MacroOf(z0); mz <= WorldLayout.MacroOf(z0 + 57); mz++)
            for (int mx = WorldLayout.MacroOf(x0); mx <= WorldLayout.MacroOf(x0 + 87); mx++)
                if (layout.LevelAt(mx, mz) != WorldLayout.Level188) Bad($"building cell {mx},{mz} is level {layout.LevelAt(mx, mz)}");

        Tile T(int bx, int bz) => layout.TileAt(x0 + bx, z0 + bz);
        // The courtyard
        int court = 0, paver = 0, lawn = 0, deck = 0, hatch = 0;
        for (int bz = 0; bz < WorldLayout.L188D; bz++)
            for (int bx = 0; bx < WorldLayout.L188W; bx++)
            {
                Tile t = T(bx, bz);
                if (t.Zone != (byte)Part.Court) continue;
                court++;
                if (t.Floor == FloorKind.L188Paver) paver++;
                if (t.Floor == FloorKind.L188Turf) lawn++;
                if (t.Floor == FloorKind.L188Deck) deck++;
                if (t.Under == Unders.L188Hatch) hatch++;
            }
        Console.WriteLine($"courtyard: {court} tiles ({paver} paving, {lawn} lawn, {deck} deck, {hatch} hatch)");
        if (court != 54 * 24) Bad("courtyard is not 54 x 24");
        if (hatch != 4) Bad("hatch is not 2 x 2");

        // Windows: 11/11/5/5 on the façade; the links
        int windows = 0;
        var linkTo = new SortedDictionary<int, int>();
        for (int wi = 0; wi < WorldLayout.L188Windows; wi++)
        {
            var (l, r, f) = WorldLayout.L188WindowTiles(wi);
            if (WorldLayout.L188WindowAt(l.Bx, l.Bz) != wi || WorldLayout.L188WindowAt(r.Bx, r.Bz) != wi) Bad($"window {wi} tiles don't map back");
            windows++;
            int link = layout.L188LinkLevel(wi);
            if (link < 0) continue;
            linkTo[link] = linkTo.GetValueOrDefault(link) + 1;
            if (T(l.Bx, l.Bz).Under != Unders.L188LinkWindow || T(r.Bx, r.Bz).Under != Unders.L188LinkWindow) Bad($"link window {wi} not marked");
            // Its room is sealed
            var (wing, k) = WorldLayout.L188WindowWingK(wi);
            var (rx, rz) = WorldLayout.L188RoomTile(wing, k, false, 2, 2);
            if (!T(rx, rz).Sealed) Bad($"link window {wi}'s room is not sealed");
            if (link == WorldLayout.Hub && wing != 0) Bad("the Hub window is not on the north side");
            if (link == WorldLayout.FunLevel && wing != 1) Bad("the confetti window is not on the east side");
        }
        Console.WriteLine($"windows a storey: {windows}; links: {string.Join(" ", linkTo.Select(p => $"L{p.Key}x{p.Value}"))}");
        if (linkTo.Values.Sum() != 12) Bad("not twelve link windows");

        // The ground storey: the courtyard's one door joins it to the corridor; everything walkable is reached but sealed rooms
        bool Walk(Tile t) => t.Kind is TileKind.Doorway || t.Kind == TileKind.Floor && (t.Variant == 0 || t.Variant is Props.L188MossTuft or Props.L188Drain);
        var reach = new HashSet<(int, int)>();
        var q = new Queue<(int, int)>();
        reach.Add((20, 20)); q.Enqueue((20, 20));
        while (q.Count > 0)
        {
            var (x, z) = q.Dequeue();
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= WorldLayout.L188W || nz >= WorldLayout.L188D || !Walk(T(nx, nz)) || !reach.Add((nx, nz))) continue;
                q.Enqueue((nx, nz));
            }
        }
        int walkable = 0, missed = 0, sealedRooms = 0;
        for (int bz = 0; bz < WorldLayout.L188D; bz++)
            for (int bx = 0; bx < WorldLayout.L188W; bx++)
            {
                Tile t = T(bx, bz);
                if (!Walk(t)) continue;
                walkable++;
                if (t.Sealed) { sealedRooms++; continue; }
                if (!reach.Contains((bx, bz))) { missed++; if (missed <= 5) Console.WriteLine($"  unreached {bx},{bz} ({(Part)t.Zone})"); }
            }
        Console.WriteLine($"ground storey: {walkable} walkable tiles, {reach.Count} reached from the courtyard, {sealedRooms} sealed, {missed} unreached");
        if (missed > 0) Bad("unreached ground-storey tiles");
        var lobby = T(40, 54);
        if (!reach.Contains((40, 54)) || lobby.Zone != (byte)Part.Lobby) Bad("the lobby is not reached");
        foreach (var (fx, fz, fs) in WorldLayout.L188FireDoors)
            if (T(fx, fz).Under != Unders.L188FireDoor || T(fx, fz).Detail != fs) Bad($"fire door {fs} not marked");

        // Arrivals
        int arrivals = 0, wrong = 0, beside = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            if (layout.FindArrival(WorldLayout.Level188, key * 7919UL) is not { } a) continue;
            arrivals++;
            Tile t = layout.TileAt(a.X, a.Z);
            if (t.Zone != (byte)Part.Court) wrong++;
            if (layout.FindArrival(WorldLayout.Level188, key * 104729UL, ThresholdNetwork.L188LinkWindowTo(0)) is { } b && layout.FeatureBeside(b.X, b.Z, ThresholdNetwork.L188LinkWindowTo(0)) != null) beside++;
        }
        Console.WriteLine($"arrivals: {arrivals}/60, {wrong} outside the courtyard; beside a Level 0 window: {beside}/60");
        if (arrivals < 60 || wrong > 0 || beside < 60) Bad("arrivals");

        // Thresholds: every window onto elsewhere, blinds, fire doors, the hatch, the Hub window, the Fun window
        var net = new ThresholdNetwork(layout, new WorldGeometry(256), 12345);
        for (int wi = 0; wi < WorldLayout.L188Windows; wi++)
        {
            var (l, _, _) = WorldLayout.L188WindowTiles(wi);
            int gx = x0 + l.Bx, gz = z0 + l.Bz;
            int link = layout.L188LinkLevel(wi);
            if (link >= 0)
            {
                Passage p = net.Walked(gx, gz, layout.TileAt(gx, gz), 2.2);
                if (p == null) { Bad($"link window {wi} leads nowhere"); continue; }
                Link? to = net.Take(p, net.HomeBeside(p.Source));
                int got = to is { } t ? layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(t.X)), WorldLayout.MacroOf((int)Math.Floor(t.Z))) : -1;
                Console.WriteLine($"  window {wi,2} (L{link}) -> L{got}{(to is { Marker: true } ? " (thin spot back)" : "")}");
                if (got != link) Bad($"window {wi} should lead to {link}");
            }
            for (int s = 0; s < WorldLayout.L188Storeys; s++)
            {
                Passage p = net.Used(gx, gz, "l188-blind-" + s, out _);
                bool expect = wi != WorldLayout.L188StairWindow && !(s == 0 && link >= 0);
                if (p == null != !expect) Bad($"blind {wi}/{s}: {(p == null ? "nothing" : "a way")}");
                if (p == null) continue;
                Link? to = net.Take(p, null);
                int got = to is { } t ? layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(t.X)), WorldLayout.MacroOf((int)Math.Floor(t.Z))) : -1;
                if (got != layout.L188BlindTarget(wi, s)) Bad($"blind {wi}/{s} went to {got}, not {layout.L188BlindTarget(wi, s)}");
            }
        }
        foreach (var (fx, fz, fs) in WorldLayout.L188FireDoors)
        {
            Passage p = net.Used(x0 + fx, z0 + fz, "l188-fireexit", out string refusal);
            Link? to = p == null ? null : net.Take(p, new Link(x0 + fx + 0.5, 1000, z0 + fz + 0.5, false));
            int got = to is { } t ? layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(t.X)), WorldLayout.MacroOf((int)Math.Floor(t.Z))) : -1;
            Console.WriteLine($"  fire door storey {fs} -> L{got}{(to is { Marker: true } ? " (thin spot back)" : " (beside a door)")}");
            if (got != fs switch { 1 => 1, 2 => 5, 3 => 4, _ => 2 }) Bad($"fire door {fs}");
        }
        {
            Passage p = net.Walked(x0 + 43, z0 + 28, T(43, 28), -3);
            Link? to = p == null ? null : net.Take(p, null);
            int got = to is { } t ? layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(t.X)), WorldLayout.MacroOf((int)Math.Floor(t.Z))) : -1;
            Console.WriteLine($"  hatch -> L{got}");
            if (got != WorldLayout.Poolrooms) Bad("hatch");
        }
        if (layout.HubWindowOf() is { } hw)
        {
            Passage p = net.Walked(hw.Left.X, hw.Left.Z, layout.TileAt(hw.Left.X, hw.Left.Z), 1.5);
            Link? to = p == null ? null : net.Take(p, net.HomeBeside(p.Source));
            Console.WriteLine($"  Hub window {hw.Left} -> {(to is { } t ? $"L{layout.LevelAt(WorldLayout.MacroOf((int)t.X), WorldLayout.MacroOf((int)t.Z))}" : "nowhere")}"
                + (to is { Marker: false } ? " beside the courtyard's Hub window" : ""));
            if (to == null || to.Value.Marker) Bad("Hub window not paired");
        }
        else Console.WriteLine("  (no Hub window in this world)");
        if (layout.L188FunWindow() is { } fw)
        {
            Tile ft = layout.TileAt(fw.Left.X, fw.Left.Z);
            Passage p = net.Walked(fw.Left.X, fw.Left.Z, ft, 2.2);
            Link? to = p == null ? null : net.Take(p, net.HomeBeside(p.Source));
            Console.WriteLine($"  Fun window {fw.Left} ({(ft.Under == Unders.L188Entrance ? "marked" : "NOT marked")}) -> {(to is { } t ? $"L{layout.LevelAt(WorldLayout.MacroOf((int)t.X), WorldLayout.MacroOf((int)t.Z))}" : "nowhere")}"
                + (to is { Marker: false } ? " beside the confetti window" : ""));
            if (ft.Under != Unders.L188Entrance || to == null || to.Value.Marker) Bad("Fun window");
        }
        else Bad("no Fun window");

        // The windows in Levels 0 and 1: only their two tiles differ from the level without them
        int span = args.Length > 3 && int.TryParse(args[3], out int cn) ? cn : 160;
        int found0 = 0, found1 = 0, paired = 0, extraDiff = 0, candidates = 0;
        int smx = WorldLayout.MacroOf(layout.FindSpawn().X), smz = WorldLayout.MacroOf(layout.FindSpawn().Z);
        var cellsToTry = new List<(int Level, int Mx, int Mz)>();
        for (int dz = -span; dz <= span; dz++)
            for (int dx = -span; dx <= span; dx++)
            {
                int mx = smx + dx, mz = smz + dz;
                if (layout.IsL188WindowCellL1(mx, mz) && layout.LevelAt(mx, mz) == 1) cellsToTry.Add((1, mx, mz));
                else if (layout.LevelAt(mx, mz) == 0 && layout.IsL188WindowCellL0(mx, mz)) cellsToTry.Add((0, mx, mz));
            }
        Console.WriteLine($"cells picked for a window within {span} cells of spawn: L0 {cellsToTry.Count(c => c.Level == 0)}, L1 {cellsToTry.Count(c => c.Level == 1)}");
        foreach (int level in new[] { 0, 1 })
        {
            int found = 0;
            foreach (var (lv, mx, mz) in cellsToTry)
            {
                if (lv != level) continue;
                candidates++;
                Tile[] with = layout.BuildMacro(mx, mz);
                int marked = with.Count(t => t.Under == Unders.L188Entrance);
                WorldLayout.L188Entrances = false;
                Tile[] without = layout.BuildMacro(mx, mz);
                WorldLayout.L188Entrances = true;
                int diff = 0;
                for (int i = 0; i < with.Length; i++)
                {
                    Tile a1 = with[i], b1 = without[i];
                    a1.Under = b1.Under; a1.Detail = b1.Detail;
                    if (!a1.Equals(b1)) diff++;
                }
                extraDiff += diff;
                if (marked == 0) continue;
                found++;
                int i0 = Array.FindIndex(with, t => t.Under == Unders.L188Entrance);
                int ex = mx * 32 + i0 % 32, ez = mz * 32 + i0 / 32;
                Passage p = net.Walked(ex, ez, with[i0], 2.2);
                Link? to = p == null ? null : net.Take(p, net.HomeBeside(p.Source));
                bool ok = to is { Marker: false } && layout.FeatureBeside((int)Math.Floor(to.Value.X), (int)Math.Floor(to.Value.Z), ThresholdNetwork.L188LinkWindowTo(level)) != null;
                if (ok) paired++;
                if (found <= 3) Console.WriteLine($"  L{level} window at {ex},{ez}: {marked} tiles, {diff} other tiles changed, -> {(ok ? "beside the courtyard's L" + level + " window" : "?")}");
            }
            if (level == 0) found0 = found; else found1 = found;
        }
        Console.WriteLine($"windows found: L0 {found0}, L1 {found1} (of {candidates} cells picked; the rest had no straight wall); paired with a courtyard window {paired} (the rest leave a thin spot back); other tiles changed {extraDiff}");
        if (extraDiff > 0) Bad("the windows changed other tiles");

        Console.WriteLine(bad == 0 ? "188stats: all good" : $"188stats: {bad} problems");
        return true;
    }

    /// <summary>The ground storey as text: # wall, w window, L window onto elsewhere, D doorway, X door, . floor, s sealed, , lawn, o deck, H hatch, F fire door.</summary>
    static void L188Map(WorldLayout layout)
    {
        int x0 = layout.L188BuildX0, z0 = layout.L188BuildZ0;
        for (int bz = 0; bz < WorldLayout.L188D; bz++)
        {
            var line = new System.Text.StringBuilder();
            for (int bx = 0; bx < WorldLayout.L188W; bx++)
            {
                Tile t = layout.TileAt(x0 + bx, z0 + bz);
                char ch = t.Under switch
                {
                    Unders.L188LinkWindow => 'L',
                    Unders.L188Hatch => 'H',
                    Unders.L188FireDoor => 'F',
                    _ => t.Kind switch
                    {
                        TileKind.Wall => WorldLayout.L188WindowAt(bx, bz) >= 0 ? 'w' : t.Pattern == WallPattern.L188Nothing ? ' ' : '#',
                        TileKind.Doorway => 'D',
                        TileKind.Door => 'X',
                        TileKind.Floor => t.Sealed ? 's' : t.Stair > 0 ? '^' : t.Floor == FloorKind.L188Turf ? ',' : t.Floor == FloorKind.L188Deck ? 'o'
                            : t.Variant != 0 ? 'p' : '.',
                        _ => '?',
                    },
                };
                line.Append(ch);
            }
            Console.WriteLine(line);
        }
    }

    /// <summary>For the links mode: what to call a threshold of the level's walked into on this tile, or null.</summary>
    static string L188LinkLabel(Tile t) => t.Under switch
    {
        Unders.L188LinkWindow when t.Level == WorldLayout.Level188 => "188 window onto L" + t.Detail,
        Unders.L188Entrance when t.Level != WorldLayout.Level188 => "window into 188",
        Unders.L188Hatch => "188 hatch",
        Unders.HubWindow188 => "Hub window into 188",
        _ => null,
    };

    /// <summary>For the links mode: the threshold kind of one of the level's blocks used on this tile (its BlockBehaviorThreshold kind), or null.</summary>
    static string L188UseKind(Tile t) =>
        t.Level != WorldLayout.Level188 ? null
        : t.Under == Unders.L188FireDoor ? "l188-fireexit"
        : t.Kind == TileKind.Wall && t.Pattern == WallPattern.L188Facade && t.Under == 0 && t.Stack == 1 ? "l188-blind-2"
        : null;
}
