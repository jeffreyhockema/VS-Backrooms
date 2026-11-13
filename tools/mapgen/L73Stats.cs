using System;
using System.Diagnostics;
using System.Linq;
using Backrooms.Worldgen;
using Part = Backrooms.Worldgen.WorldLayout.L73Part;

/// <summary>Level 73's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 73stats: the region (its cells, how long they take), the share of its tiles that are land, sea, castle and rim, the
    /// island's heights, the castle (every tile of its square is the castle's, and is level), and 60 arrivals (on dry land,
    /// 40 to 220 blocks from the gate). 73map: the island as text, one character per 8 blocks.
    /// </summary>
    static bool L73Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "73map") { L73Map(layout); return true; }
        if (mode == "73links") { L73Links(layout); return true; }
        if (mode == "73grid")
        {
            // Every column 300 blocks round the island's middle: height (negative under the sea), floor kind, zone, prop (for a picture)
            int cx = layout.L73IslandX, cz = layout.L73IslandZ;
            using var w = new System.IO.StreamWriter(args.Length > 0 ? args[^1] : "l73grid.txt");
            for (int z = cz - 300; z < cz + 300; z++)
            {
                var line = new System.Text.StringBuilder();
                for (int x = cx - 300; x < cx + 300; x++)
                {
                    Tile t = layout.TileAt(x, z);
                    int h = t.Depth > 0 ? -t.Depth : t.Height;
                    int bone = layout.InL73Hound(x, z) && Enumerable.Range(1, 9).Any(r => layout.L73HoundBoneAt(x, z, h + r)) ? 1 : 0;
                    line.Append(h).Append(',').Append((int)t.Floor).Append(',').Append(t.Zone).Append(',').Append(t.Variant != 0 ? 1 : bone * 2).Append(' ');
                }
                w.WriteLine(line.ToString());
            }
            return true;
        }
        if (mode != "73stats") return false;
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }

        int ix = layout.L73IslandX, iz = layout.L73IslandZ;
        int mx0 = WorldLayout.MacroOf(ix), mz0 = WorldLayout.MacroOf(iz);
        Console.WriteLine($"island centre {ix},{iz} (cell {mx0},{mz0}); castle corner {layout.L73CastleX0},{layout.L73CastleZ0}; gate {layout.L73Gate}");

        // The region's tiles, by zone
        long land = 0, sea = 0, court = 0, keep = 0, walls = 0, rim = 0, other = 0, sealedLand = 0;
        int cells = 0, peak = 0, deepest = 0;
        var heights = new int[WorldLayout.L73TorPeak + 1];
        var sw = Stopwatch.StartNew();
        for (int mz = mz0 - 22; mz <= mz0 + 22; mz++)
            for (int mx = mx0 - 22; mx <= mx0 + 22; mx++)
            {
                if (layout.LevelAt(mx, mz) != WorldLayout.Level73) continue;
                cells++;
                foreach (Tile t in layout.BuildMacro(mx, mz))
                {
                    switch (t.Zone)
                    {
                        case WorldLayout.L73Land:
                            land++;
                            heights[t.Height]++;
                            peak = Math.Max(peak, t.Height);
                            if (t.Sealed && t.Variant == 0) sealedLand++; // (a tile with bones on it is sealed itself)
                            break;
                        case WorldLayout.L73Sea: sea++; deepest = Math.Max(deepest, t.Depth); break;
                        case WorldLayout.L73Court: court++; break;
                        case WorldLayout.L73Keep: keep++; break;
                        case WorldLayout.L73Walls: walls++; break;
                        case WorldLayout.L73RimZone: rim++; break;
                        default: other++; break;
                    }
                }
            }
        double ms = sw.Elapsed.TotalMilliseconds / Math.Max(1, cells);
        double all = Math.Max(1, land + sea + court + keep + walls + rim + other);
        long castle = court + keep + walls;
        Console.WriteLine($"region: {cells} cells, {ms:0.0} ms a cell");
        Console.WriteLine($"tiles: land {land / all:P1}, sea {sea / all:P1}, castle {castle / all:P2} ({court} courtyard, {keep} keep, {walls} walls), rim {rim / all:P1}, other {other}");
        Console.WriteLine($"land heights: peak {peak}, deepest sea {deepest}; " + string.Join(" ", Enumerable.Range(0, heights.Length).Select(h => $"{h}:{heights[h] * 100.0 / Math.Max(1, land):0.#}%")));
        if (other > 0) Bad($"{other} tiles of no zone");
        // (The Great Hound's footprint is sealed on purpose)
        var (hx, hz, hg) = layout.L73Hound;
        long houndSealed = 0;
        for (int z = hz - WorldLayout.L73HoundHalf - 1; z <= hz + WorldLayout.L73HoundHalf + 1; z++)
            for (int x = hx - 1; x <= hx + WorldLayout.L73HoundLength; x++)
                if (layout.TileAt(x, z) is { Zone: WorldLayout.L73Land, Sealed: true, Variant: 0 }) houndSealed++;
        Console.WriteLine($"the Great Hound at {hx},{hz}, on ground {hg}: {houndSealed} tiles sealed under it");
        sealedLand -= houndSealed;
        // (and so are the dead trees' trunks and the boulders, round 3)
        long trees = 0, boulders = 0, heaps = 0, ditch = 0, drums = 0;
        for (int z = iz - 300; z <= iz + 300; z++)
            for (int x = ix - 300; x <= ix + 300; x++)
            {
                Tile t = layout.TileAt(x, z);
                if (t.Zone != WorldLayout.L73Land || !t.Sealed || t.Variant != 0 || layout.InL73Hound(x, z)) continue;
                if (layout.L73TreeNear(x, z) is { } tree && tree.X == x && tree.Z == z) trees++;
                else if (layout.L73BoulderAt(x, z) != null) boulders++;
                else if (t.Detail == 2) heaps++;
                else
                {
                    int u = x - layout.L73CastleX0, v = z - layout.L73CastleZ0;
                    if (WorldLayout.L73Ditch(u, v) > 0 || WorldLayout.L73BridgeSide(u, v)) ditch++;
                    else if (v is >= WorldLayout.L73CastleD and <= WorldLayout.L73CastleD + 1 && (u is >= 22 and <= 25 || u is >= 30 and <= 33)) drums++;
                }
            }
        Console.WriteLine($"dead trees {trees}, boulder tiles {boulders}; round 4: heaps of the dead {heaps}, ditch and bridge {ditch}, drum tiles {drums}");
        sealedLand -= trees + boulders + heaps + ditch + drums;
        if (drums != 16) Bad($"{drums} drum tiles, not 16");
        if (trees < 40) Bad("too few dead trees");
        if (sealedLand > 0) Bad($"{sealedLand} land tiles sealed");
        if (castle != WorldLayout.L73CastleW * WorldLayout.L73CastleD) Bad($"castle has {castle} tiles, not {WorldLayout.L73CastleW * WorldLayout.L73CastleD}");
        if (land < sea / 4) Bad("hardly any land");

        // The castle: its square, all the castle's, level on the plateau; the gate, the path and the door join up
        int notLevel = 0;
        for (int v = 0; v < WorldLayout.L73CastleD; v++)
            for (int u = 0; u < WorldLayout.L73CastleW; u++)
            {
                Tile t = layout.TileAt(layout.L73CastleX0 + u, layout.L73CastleZ0 + v);
                if (t.Level != WorldLayout.Level73) Bad($"castle tile {u},{v} is level {t.Level}");
                if (t.Height != WorldLayout.L73Plateau) notLevel++;
            }
        if (notLevel > 0) Bad($"{notLevel} castle tiles off the plateau");
        for (int v = WorldLayout.L73CastleD; v < WorldLayout.L73CastleD + 8; v++)
        {
            Tile t = layout.TileAt(layout.L73CastleX0 + 27, layout.L73CastleZ0 + v);
            if (t.Height < WorldLayout.L73Plateau - 1 && v < WorldLayout.L73CastleD + 4) Bad($"ground falls away outside the gate ({t.Height} at v {v})");
        }
        if (WorldLayout.L73CastleAt(27, WorldLayout.L73CastleD - 1) != Part.Gate) Bad("no gate");
        if (!WorldLayout.L73MainDoor(17, WorldLayout.L73KeepD - 1) || !WorldLayout.L73MainDoor(18, WorldLayout.L73KeepD - 1)) Bad("no keep door");
        for (int v = WorldLayout.L73KeepV0 + WorldLayout.L73KeepD; v < WorldLayout.L73CastleD - 2; v++)
            if (WorldLayout.L73CastleAt(27, v) != Part.Path) Bad($"the path is broken at v {v}");

        // The keep: every storey's flight lands where the next begins, every room has a way in, every window a room
        // behind it, every furnishing stands in a room, the lore's counts (six guest rooms of two beds, two bathrooms)
        int guestBeds = 0, baths = 0, windows = 0, settings = 0, misplaced = 0;
        for (int s = 0; s <= 2; s++)
            for (int kv = 0; kv < WorldLayout.L73KeepD; kv++)
                for (int ku = 0; ku < WorldLayout.L73KeepW; ku++)
                {
                    if (WorldLayout.L73Window(ku, kv, s)) windows++;
                    foreach (WorldLayout.L73Layer layer in new[] { WorldLayout.L73Layer.Floor, WorldLayout.L73Layer.Wall, WorldLayout.L73Layer.Ceiling })
                    {
                        var thing = WorldLayout.L73FurnishingAt(ku, kv, s, layer).Thing;
                        if (thing == WorldLayout.L73Thing.None) continue;
                        if (WorldLayout.L73RoomAt(ku, kv, s) == WorldLayout.L73Room.Wall || WorldLayout.L73StairStep(ku, kv, s) > 0
                            || layer == WorldLayout.L73Layer.Floor && (WorldLayout.L73Doorway(ku - 1, kv, s) || WorldLayout.L73Doorway(ku + 1, kv, s)
                                || WorldLayout.L73Doorway(ku, kv - 1, s) || WorldLayout.L73Doorway(ku, kv + 1, s)))
                        {
                            misplaced++;
                            Console.WriteLine($"  misplaced {thing} at {ku},{kv} storey {s} ({layer})");
                        }
                        if (thing == WorldLayout.L73Thing.BedHead && WorldLayout.L73RoomAt(ku, kv, s) == WorldLayout.L73Room.Guest) guestBeds++;
                        if (thing == WorldLayout.L73Thing.Bath) baths++;
                        if (thing == WorldLayout.L73Thing.Table) settings++;
                    }
                }
        Console.WriteLine($"keep: {guestBeds} guest beds, {baths} bath barrels, {settings} places at the table, {windows} windows, {misplaced} misplaced");
        if (guestBeds != 24) Bad("not six guest rooms of two large beds (two beds side by side under a canopy)");
        if (misplaced > 0) Bad("furnishings in walls, on stairs or in doorways");
        for (int s = 0; s <= 1; s++)
        {
            int top = s == 1 ? 11 : 24, beyond = s == 1 ? 10 : 25;
            if (WorldLayout.L73StairStep(top, 12, s) != 5 || WorldLayout.L73RoomAt(beyond, 12, s + 1) == WorldLayout.L73Room.Wall) Bad($"storey {s}'s flight lands nowhere");
        }

        // Arrivals
        int found = 0, dry = 0, near = 0;
        var (gx, gz) = layout.L73Gate;
        double nearest = double.MaxValue, farthest = 0;
        for (int k = 0; k < 60; k++)
        {
            var a = layout.FindArrival(WorldLayout.Level73, (ulong)k * 7919UL + 13);
            if (a is not { } at) { Bad($"arrival {k}: none"); continue; }
            found++;
            Tile t = layout.TileAt(at.X, at.Z);
            if (t.Level == WorldLayout.Level73 && t.Zone == WorldLayout.L73Land && t.Height >= 2) dry++;
            else Bad($"arrival {k} at {at.X},{at.Z}: level {t.Level} zone {t.Zone} height {t.Height}");
            double d = Math.Sqrt((double)(at.X - gx) * (at.X - gx) + (double)(at.Z - gz) * (at.Z - gz));
            nearest = Math.Min(nearest, d);
            farthest = Math.Max(farthest, d);
            if (d >= 40 && d <= 220) near++;
        }
        Console.WriteLine($"arrivals: {found}/60 found, {dry} on dry land, {near} within 40-220 of the gate (nearest {nearest:0}, farthest {farthest:0})");
        if (near < 54) Bad("too few arrivals within sight of the castle");
        Console.WriteLine(bad == 0 ? "73stats: OK" : $"73stats: {bad} BAD");
        return true;
    }

    /// <summary>The island as text: one character per 8 by 8 blocks (sea ~, beach ., land by height, castle #, rim |).</summary>
    static void L73Map(WorldLayout layout)
    {
        int ix = layout.L73IslandX, iz = layout.L73IslandZ;
        for (int z = iz - 520; z <= iz + 520; z += 16)
        {
            var line = new System.Text.StringBuilder();
            for (int x = ix - 520; x <= ix + 520; x += 8)
            {
                Tile t = layout.TileAt(x, z);
                line.Append(t.Level != WorldLayout.Level73 ? ' ' : t.Zone switch
                {
                    WorldLayout.L73Sea => '~',
                    WorldLayout.L73RimZone => '|',
                    WorldLayout.L73Land => t.Floor == FloorKind.L73Mud ? 'm' : t.Height <= 1 ? '.' : (char)('0' + Math.Min(9, (int)t.Height)),
                    _ => '#',
                });
            }
            Console.WriteLine(line.ToString());
        }
    }

    static string L73LinkLabel(Tile t) => null;

    static string L73UseKind(Tile t) => null;
    /// <summary>
    /// 73links: Level 73's ways in and out (WorldLayout.Level73.Links.cs). The nearest Glooms in Level 9 and cells of Level 6's
    /// deepest dark to spawn (position, distance), how many there are a square kilometre of their host (from the chance a cell
    /// has, and the share of the cells that roll it that hold one), the Glooms' sizes and ground, the north door, and where each
    /// way leads when first taken (the threshold network, offline): into the level on dry land for the ways in, into Level 9
    /// for the way out.
    /// </summary>
    static void L73Links(WorldLayout layout)
    {
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }
        var geometry = new WorldGeometry(256);
        var net = new Backrooms.Thresholds.ThresholdNetwork(layout, geometry, 12345);
        const double cellsPerKm2 = 1e6 / (WorldLayout.MacroSize * WorldLayout.MacroSize);

        // The Gloom, in Level 9
        var sw = Stopwatch.StartNew();
        var glooms = layout.L73NearestGlooms(8);
        Console.WriteLine($"Glooms (Level 9; one cell in {WorldLayout.L73GloomCells} rolls one; {sw.ElapsedMilliseconds} ms to find the nearest {glooms.Count}):");
        int rolled = 0, held = 0, tilesAll = 0;
        var grounds = new System.Collections.Generic.Dictionary<FloorKind, int>();
        foreach (var (gx, gz, dist) in glooms)
        {
            int mx = WorldLayout.MacroOf((int)gx), mz = WorldLayout.MacroOf((int)gz);
            int tiles = 0, heart = 0;
            Tile[] cell = layout.BuildMacro(mx, mz);
            foreach (Tile t in cell)
            {
                if (t.Under == Unders.L73Gloom) heart++;
                if (t.Under is Unders.L73Gloom or Unders.L73GloomRim) tiles++;
            }
            tilesAll += tiles;
            if (heart == 0) Bad($"the Gloom at {gx:0},{gz:0} has no heart");
            // What it lies on (as the cell is without it), and that nothing else in the cell moved
            WorldLayout.ExpEntrances = false;
            Tile[] plain = layout.BuildMacro(mx, mz);
            WorldLayout.ExpEntrances = true;
            for (int i = 0; i < cell.Length; i++)
            {
                Tile a = cell[i], b = plain[i];
                bool ours = a.Under is Unders.L73Gloom or Unders.L73GloomRim;
                if (ours)
                {
                    grounds[b.Floor] = grounds.GetValueOrDefault(b.Floor) + 1;
                    if (b.Under != 0 || b.Variant != 0 || b.Kind != TileKind.Floor) Bad($"the Gloom at {gx:0},{gz:0} took a tile that held something");
                    a.Under = b.Under;
                }
                if (!a.Equals(b)) Bad($"the Gloom's cell {mx},{mz} changed more than the Gloom's tiles' Under (tile {i})");
            }
            var p = net.L73Gloom((int)gx, (int)gz);
            var to = p == null ? null : net.Take(p, null);
            string where = to is { } l ? $"to {l.X:0},{l.Y:0},{l.Z:0} ({Describe(layout, l.X, l.Z)})" : "NOWHERE";
            if (to is not { } ll || layout.TileAt((int)Math.Floor(ll.X), (int)Math.Floor(ll.Z)) is not { Level: WorldLayout.Level73, Zone: WorldLayout.L73Land })
                Bad($"the Gloom at {gx:0},{gz:0} does not lead onto the island's land");
            Console.WriteLine($"  {gx:0},{gz:0}  {dist / 1000:0.00} km from spawn  {tiles} tiles ({heart} under the murk)  leads {where}");
        }
        // The share of the cells that roll one that hold one (Level 9 cells only), over a wider sample
        foreach (var (rx, rz) in SampleRolled(60, (mx, mz) => layout.IsL73GloomCell(mx, mz) && layout.LevelAt(mx, mz) == 9))
        {
            rolled++;
            if (layout.BuildMacro(rx, rz).Any(t => t.Under is Unders.L73Gloom or Unders.L73GloomRim)) held++;
        }
        double gloomDensity = cellsPerKm2 / WorldLayout.L73GloomCells * held / Math.Max(1, rolled);
        Console.WriteLine($"  {held} of {rolled} Level 9 cells that rolled one hold one: {gloomDensity:0.00} a km2 of Level 9 (about {1 / Math.Sqrt(Math.Max(1e-9, gloomDensity)):0.0} km apart); "
                          + $"{tilesAll / Math.Max(1.0, glooms.Count):0} tiles each, on " + string.Join(", ", grounds.Select(kv => $"{kv.Key} {kv.Value}")));

        // Level 6's deepest dark
        sw.Restart();
        var dark = layout.L73NearestDark(8);
        Console.WriteLine($"Level 6's deepest dark (one cell in {layout.L73DarkOneIn}; {sw.ElapsedMilliseconds} ms to find the nearest {dark.Count}):");
        foreach (var (dx, dz, dist) in dark)
        {
            int mx = WorldLayout.MacroOf((int)dx), mz = WorldLayout.MacroOf((int)dz);
            var p = net.L73Dark(mx, mz);
            var to = p == null ? null : net.Take(p, null);
            string where = to is { } l ? $"to {l.X:0},{l.Y:0},{l.Z:0} ({Describe(layout, l.X, l.Z)})" : "NOWHERE";
            if (to is not { } ll || layout.TileAt((int)Math.Floor(ll.X), (int)Math.Floor(ll.Z)) is not { Level: WorldLayout.Level73, Zone: WorldLayout.L73Land })
                Bad($"the dark cell {mx},{mz} does not lead onto the island's land");
            Console.WriteLine($"  cell {mx},{mz} (middle {dx:0},{dz:0})  {dist / 1000:0.00} km from spawn  leads {where}");
        }
        int darkRolled = 0, darkHeld = 0;
        foreach (var (rx, rz) in SampleRolled(60, (mx, mz) => layout.L73DarkRolls(mx, mz) && layout.LevelAt(mx, mz) == 6 && !layout.IsSnackrooms(mx, mz)))
        {
            darkRolled++;
            if (layout.IsL73DarkCell(rx, rz)) darkHeld++;
        }
        double darkDensity = cellsPerKm2 / layout.L73DarkOneIn * darkHeld / Math.Max(1, darkRolled);
        Console.WriteLine($"  {darkHeld} of {darkRolled} Level 6 cells that rolled one have the wall corner that stands for it: {darkDensity:0.00} a km2 of Level 6 "
                          + $"(about {1 / Math.Sqrt(Math.Max(1e-9, darkDensity)):0.0} km apart)");

        // The north door
        var (px, pz) = layout.L73Postern;
        var (fx, fz) = layout.L73PosternFront;
        Console.WriteLine($"north door: leaves at {px},{pz} and {px + 1},{pz}; Coran stands at {fx:0.#},{fz:0.#}; the gate is at {layout.L73Gate}");
        for (int leaf = 0; leaf < 2; leaf++)
            if (layout.TileAt(px + leaf, pz) is not { Level: WorldLayout.Level73, Zone: WorldLayout.L73Walls }) Bad("the north door is not in the castle's walls");
        for (int z = pz - 5; z < pz; z++)
            for (int x = px - 3; x <= px + 4; x++)
                if (layout.TileAt(x, z) is not { Zone: WorldLayout.L73Land, Variant: 0, Height: WorldLayout.L73Plateau }) Bad($"the ground before the north door at {x},{z} is not clear plateau");
        var outTo = net.Take(net.L73OutPassage(), null);
        Console.WriteLine($"  leads {(outTo is { } o ? $"to {o.X:0},{o.Y:0},{o.Z:0} ({Describe(layout, o.X, o.Z)})" : "NOWHERE")}");
        if (outTo is not { } oo || layout.TileAt((int)Math.Floor(oo.X), (int)Math.Floor(oo.Z)).Level != Backrooms.Thresholds.ThresholdNetwork.L73OutLevel)
            Bad("the north door does not lead into Level 9");
        // The showcase's spots at the ways in
        foreach (var spot in layout.L73LinkSpots(geometry))
            Console.WriteLine($"  showcase {spot.Name}: {spot.X:0.#},{spot.Y:0.#},{spot.Z:0.#} heading {spot.Heading:0}");
        Console.WriteLine(bad == 0 ? "73links: OK" : $"73links: {bad} BAD");
    }

    /// <summary>A level, a zone and a floor, said briefly.</summary>
    static string Describe(WorldLayout layout, double x, double z)
    {
        Tile t = layout.TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        return $"level {t.Level}, zone {t.Zone}, floor {t.Floor}";
    }

    /// <summary>Up to n cells that pass a test, in rings out from the world's spawn cell (for a share among them).</summary>
    static System.Collections.Generic.IEnumerable<(int X, int Z)> SampleRolled(int n, Func<int, int, bool> test)
    {
        // (The harness's spawn cell: SPAWN, 16000 by default)
        int s = int.TryParse(Environment.GetEnvironmentVariable("SPAWN"), out int sp) ? sp : 16000, found = 0;
        var side = new (int, int)[4];
        for (int r = 1; r < 6000 && found < n; r++)
            for (int i = -r; i < r && found < n; i++)
            {
                side[0] = (i, -r); side[1] = (r, i); side[2] = (-i, r); side[3] = (-r, -i);
                for (int k = 0; k < 4; k++)
                {
                    var (dx, dz) = side[k];
                    if (!test(s + dx, s + dz)) continue;
                    found++;
                    yield return (s + dx, s + dz);
                    if (found >= n) yield break;
                }
            }
    }
}
