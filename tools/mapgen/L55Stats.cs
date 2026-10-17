using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Backrooms.Worldgen;
using Part = Backrooms.Worldgen.WorldLayout.L55Part;

/// <summary>Level 55's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 55stats: the region (its cells, how long they take), the share of its tiles in each zone, the ground's heights, the
    /// crevasses (how many, how many tiles, how many bridged, how deep), the hut (every tile of its square is the hut's,
    /// with a door and its stove), the cave (its chamber roofed, its tunnel open to the ice at one end), and 60 arrivals (on
    /// safe snow or crust, at least 40 blocks from any crevasse, on ground no steeper than a block a block). 55map: the ice
    /// as text, one character per 8 blocks.
    /// </summary>
    static bool L55Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode == "55map") { L55Map(layout); return true; }
        if (mode != "55stats") return false;
        int bad = 0;
        void Bad(string what) { bad++; Console.WriteLine("  BAD: " + what); }

        int hx = layout.L55HutX, hz = layout.L55HutZ;
        var (kx, kz) = layout.L55CaveCentre;
        int mx0 = WorldLayout.MacroOf(hx), mz0 = WorldLayout.MacroOf(hz);
        Console.WriteLine($"hut centre {hx},{hz} (cell {mx0},{mz0}); corner {layout.L55HutX0},{layout.L55HutZ0}; stove {layout.L55Stove}; cave {kx},{kz} ({Math.Sqrt((double)(kx - hx) * (kx - hx) + (double)(kz - hz) * (kz - hz)):0} from the hut)");

        // The region's tiles
        var cells = new Dictionary<(int, int), Tile[]>();
        var sw = Stopwatch.StartNew();
        for (int mz = mz0 - 22; mz <= mz0 + 22; mz++)
            for (int mx = mx0 - 22; mx <= mx0 + 22; mx++)
                if (layout.LevelAt(mx, mz) == WorldLayout.Level55) cells[(mx, mz)] = layout.BuildMacro(mx, mz);
        double ms = sw.Elapsed.TotalMilliseconds / Math.Max(1, cells.Count);
        Tile? At(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            return cells.TryGetValue((mx, mz), out var tiles) ? tiles[WorldLayout.TileIndex(x - mx * WorldLayout.MacroSize, z - mz * WorldLayout.MacroSize)] : null;
        }

        var zones = new long[10];
        long all = 0, other = 0, crust = 0, steep = 0, safe = 0, layered = 0, bridged = 0, ridge = 0;
        int peak = 0, deepest = 0;
        var heights = new long[WorldLayout.L55Peak + 1];
        var crevasse = new List<(int X, int Z)>();
        foreach (var ((mx, mz), tiles) in cells)
            for (int i = 0; i < tiles.Length; i++)
            {
                Tile t = tiles[i];
                all++;
                if (t.Zone < zones.Length) zones[t.Zone]++;
                switch (t.Zone)
                {
                    case WorldLayout.L55Snow or WorldLayout.L55Glacier:
                        heights[Math.Min((int)t.Height, WorldLayout.L55Peak)]++;
                        peak = Math.Max(peak, t.Height);
                        if ((t.Detail & WorldLayout.L55FlagCrust) != 0) crust++;
                        if ((t.Detail & WorldLayout.L55FlagSteep) != 0) steep++;
                        if ((t.Detail & WorldLayout.L55FlagSafe) != 0) safe++;
                        if (t.Depth > 0) layered++;
                        break;
                    case WorldLayout.L55Crevasse:
                        crevasse.Add((mx * WorldLayout.MacroSize + i % WorldLayout.MacroSize, mz * WorldLayout.MacroSize + i / WorldLayout.MacroSize));
                        deepest = Math.Min(deepest, t.Height - t.Depth);
                        if ((t.Detail & WorldLayout.L55FlagBridge) != 0) bridged++;
                        break;
                    case WorldLayout.L55Sea:
                        if ((t.Detail & WorldLayout.L55FlagRidge) != 0) ridge++;
                        break;
                    case WorldLayout.L55Hut or WorldLayout.L55Cave or WorldLayout.L55RimZone: break;
                    default: other++; break;
                }
            }
        double All(long n) => n / (double)Math.Max(1, all);
        long land = zones[WorldLayout.L55Snow] + zones[WorldLayout.L55Glacier];
        Console.WriteLine($"region: {cells.Count} cells, {ms:0.00} ms a cell");
        Console.WriteLine($"tiles: snow {All(zones[1]):P1}, glacier {All(zones[2]):P1}, crevasse {All(zones[3]):P2}, sea {All(zones[4]):P1} (ridges {ridge}), hut {zones[5]}, cave {zones[6]}, rim {All(zones[9]):P1}, other {other}");
        Console.WriteLine($"on the snow and glacier: crust {crust / (double)Math.Max(1, land):P0}, snow layers {layered / (double)Math.Max(1, land):P0}, steep {steep / (double)Math.Max(1, land):P1}, safe for arrivals {safe / (double)Math.Max(1, land):P0}");
        Console.WriteLine($"heights: peak {peak}; " + string.Join(" ", Enumerable.Range(0, heights.Length).Where(h => heights[h] > 0).Select(h => $"{h}:{heights[h] * 100.0 / Math.Max(1, land):0.#}%")));
        if (other > 0) Bad($"{other} tiles of no zone");
        if (zones[WorldLayout.L55Sea] == 0) Bad("no sea");

        // Crevasses: joined groups of crevasse tiles
        var crevSet = new HashSet<(int, int)>(crevasse);
        var seen = new HashSet<(int, int)>();
        var sizes = new List<int>();
        foreach (var c in crevasse)
        {
            if (!seen.Add(c)) continue;
            int size = 0;
            var queue = new Queue<(int X, int Z)>();
            queue.Enqueue(c);
            while (queue.Count > 0)
            {
                var (x, z) = queue.Dequeue();
                size++;
                foreach (var n in new[] { (x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1) })
                    if (crevSet.Contains(n) && seen.Add(n)) queue.Enqueue(n);
            }
            sizes.Add(size);
        }
        int real = sizes.Count(s => s >= 12);
        Console.WriteLine($"crevasses: {real} of 12+ tiles ({sizes.Count} groups in all, largest {(sizes.Count > 0 ? sizes.Max() : 0)}), {crevasse.Count} tiles, {bridged / (double)Math.Max(1, crevasse.Count):P0} bridged, deepest floor at rel {deepest}");
        if (real < 3) Bad("hardly any crevasses");
        // Somewhere to look at one (a bridged crevasse tile nearest the hut)
        var sample = crevasse.Where(c => (At(c.X, c.Z)?.Detail & WorldLayout.L55FlagBridge) != 0)
            .OrderBy(c => (double)(c.X - hx) * (c.X - hx) + (double)(c.Z - hz) * (c.Z - hz)).FirstOrDefault();
        Console.WriteLine($"  a bridged crevasse near the hut at {sample.X},{sample.Z}");
        if (deepest < WorldLayout.L55CrevasseBottom) Bad($"a crevasse below rel {WorldLayout.L55CrevasseBottom}");

        // The hut: its square all the hut's, its door, its stove; nothing of the terrain cut into it
        int hutTiles = 0, door = 0, stove = 0;
        for (int v = 0; v < WorldLayout.L55HutD; v++)
            for (int u = 0; u < WorldLayout.L55HutW; u++)
            {
                Tile t = layout.TileAt(layout.L55HutX0 + u, layout.L55HutZ0 + v);
                if (t.Level != WorldLayout.Level55 || t.Zone != WorldLayout.L55Hut) { Bad($"hut tile {u},{v} is level {t.Level} zone {t.Zone}"); continue; }
                hutTiles++;
                if (t.Kind == TileKind.Doorway) door++;
                if (WorldLayout.L55HutAt(u, v) == Part.Stove) stove++;
            }
        // The ground in front of the door is level with the hut's floor
        int doorX = layout.L55HutX0 + 9, doorZ = layout.L55HutZ0 + WorldLayout.L55HutD;
        Tile front = layout.TileAt(doorX, doorZ);
        Console.WriteLine($"hut: placed, {hutTiles} tiles, {door} door tiles, {stove} stove tiles; ground outside the door at {front.Height} (floor {WorldLayout.L55HutFloor}), zone {front.Zone}");
        if (hutTiles != WorldLayout.L55HutW * WorldLayout.L55HutD) Bad("the hut is not whole");
        if (door != 2) Bad("no door");
        if (Math.Abs(front.Height - WorldLayout.L55HutFloor) > 1 || front.Zone is not (WorldLayout.L55Snow or WorldLayout.L55Glacier)) Bad("the door opens onto a drop");

        // The cave: its chamber roofed, its tunnel coming out under the open sky
        int roofed = 0, cut = 0, caveOther = 0;
        for (int z = kz - 52; z <= kz + 52; z++)
            for (int x = kx - 52; x <= kx + 52; x++)
            {
                Tile? t = At(x, z);
                if (t is not { } c || c.Zone != WorldLayout.L55Cave) continue;
                if (c.Depth > 0) roofed++; else cut++;
                if (c.Level != WorldLayout.Level55) caveOther++;
            }
        Tile mid = layout.TileAt(kx, kz);
        Console.WriteLine($"cave: {roofed} roofed tiles, {cut} in the open cut; chamber's middle zone {mid.Zone}, ceiling rel {mid.Depth}, dome top {mid.Height}");
        if (mid.Zone != WorldLayout.L55Cave || mid.Depth == 0) Bad("the cave's chamber is not roofed");
        if (roofed < 150) Bad("the cave is small");
        if (cut == 0) Bad("the cave has no way in");

        // Arrivals
        int found = 0, good = 0, far = 0, gentle = 0;
        double nearestHut = double.MaxValue, farthestHut = 0, nearestCrev = double.MaxValue;
        for (int k = 0; k < 60; k++)
        {
            var a = layout.FindArrival(WorldLayout.Level55, (ulong)k * 7919UL + 13);
            if (a is not { } at) { Bad($"arrival {k}: none"); continue; }
            found++;
            Tile t = layout.TileAt(at.X, at.Z);
            if (t.Level == WorldLayout.Level55 && t.Zone is WorldLayout.L55Snow or WorldLayout.L55Glacier) good++;
            else Bad($"arrival {k} at {at.X},{at.Z}: level {t.Level} zone {t.Zone} height {t.Height}");
            double dh = Math.Sqrt((double)(at.X - hx) * (at.X - hx) + (double)(at.Z - hz) * (at.Z - hz));
            nearestHut = Math.Min(nearestHut, dh);
            farthestHut = Math.Max(farthestHut, dh);
            double dc = double.MaxValue;
            foreach (var (cx, cz) in crevasse)
            {
                double d = Math.Sqrt((double)(cx - at.X) * (cx - at.X) + (double)(cz - at.Z) * (cz - at.Z));
                if (d < dc) dc = d;
            }
            nearestCrev = Math.Min(nearestCrev, dc);
            if (dc >= 40) far++;
            else Bad($"arrival {k} at {at.X},{at.Z}: a crevasse {dc:0} blocks off");
            int worst = 0;
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                Tile n = layout.TileAt(at.X + dx, at.Z + dz);
                worst = Math.Max(worst, Math.Abs(n.Height - t.Height));
            }
            if (worst <= 1) gentle++;
            else Bad($"arrival {k} at {at.X},{at.Z}: a step of {worst} beside it");
        }
        Console.WriteLine($"arrivals: {found}/60 found, {good} on snow or crust, {far} at least 40 from any crevasse (nearest {nearestCrev:0}), {gentle} on gentle ground; {nearestHut:0}-{farthestHut:0} blocks from the hut");
        Console.WriteLine(bad == 0 ? "55stats: OK" : $"55stats: {bad} BAD");
        return true;
    }

    /// <summary>The ice as text: one character per 8 blocks across, 16 down (sea ~, crevasse /, bridged =, hut #, cave C, rim |, else height / 2).</summary>
    static void L55Map(WorldLayout layout)
    {
        int hx = layout.L55HutX, hz = layout.L55HutZ;
        for (int z = hz - 560; z <= hz + 560; z += 16)
        {
            var line = new System.Text.StringBuilder();
            for (int x = hx - 560; x <= hx + 560; x += 8)
            {
                Tile t = layout.TileAt(x, z);
                line.Append(t.Level != WorldLayout.Level55 ? ' ' : t.Zone switch
                {
                    WorldLayout.L55Sea => '~',
                    WorldLayout.L55RimZone => '|',
                    WorldLayout.L55Crevasse => (t.Detail & WorldLayout.L55FlagBridge) != 0 ? '=' : '/',
                    WorldLayout.L55Hut => '#',
                    WorldLayout.L55Cave => 'C',
                    _ => (char)('0' + Math.Min(9, t.Height / 2)),
                });
            }
            Console.WriteLine(line.ToString());
        }
    }

    static string L55LinkLabel(Tile t) => null;

    static string L55UseKind(Tile t) => null;
}
