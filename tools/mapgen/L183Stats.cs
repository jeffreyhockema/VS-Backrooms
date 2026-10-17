using Backrooms.Worldgen;
using Part = Backrooms.Worldgen.WorldLayout.L183Part;
using Space = Backrooms.Worldgen.WorldLayout.L183Space;
using Zone = Backrooms.Worldgen.WorldLayout.L183Zone;

/// <summary>Level 183's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// 183stats [window]: over a window of cells (24 by 24 by default) round the region's middle: the zones' shares (cells),
    /// the walkable tiles' shares by space (mains, side tunnels, dry galleries, chambers, halls), how many chambers, halls,
    /// grates, lamps and pipes; then whether it can all be walked: stepping one level at most (walkway and grate 0, curb and
    /// gutter -1, channel bed -2), the walkable tiles split into connected pieces, every piece but the largest that does not
    /// reach the window's edge a pocket; the same for the dry walkways and grates alone (every walkway one piece without
    /// wading); and the 60 arrivals the regions mode tries, each on a dry walkway. Also the zone shares over the whole
    /// region (every fourth cell). 183map [window]: writes l183.ppm of the window (one pixel a tile) for a look.
    /// </summary>
    static bool L183Modes(WorldLayout layout, string mode, string[] args)
    {
        if (mode != "183stats" && mode != "183map") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int k) ? k : 24;
        var (cmx, cmz, radius) = layout.L183Region;
        int m0x = cmx - n / 2, m0z = cmz - n / 2, size = n * 32;
        var tiles = new Tile[size * size];
        var built = new bool[n * n];
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                built[mz * n + mx] = layout.LevelAt(m0x + mx, m0z + mz) == WorldLayout.Level183;
                var cell = layout.BuildMacro(m0x + mx, m0z + mz);
                for (int i = 0; i < 1024; i++) tiles[(mz * 32 + i / 32) * size + mx * 32 + i % 32] = cell[i];
            }
        bool Ours(int i) => tiles[i].Level == WorldLayout.Level183;
        static bool Walk(in Tile t) => t.Kind == TileKind.Water || t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && !t.SupplyBox;
        static bool Dry(in Tile t) => t.Kind == TileKind.Floor && (Part)t.Detail is Part.Walk or Part.Grate;
        // The height stood on: walkway and grate 0, curb and gutter -1, a channel's or basin's bed -2
        static int Surface(in Tile t) => (Part)t.Detail switch { Part.Curb or Part.Gutter => -1, Part.Channel => -2, _ => 0 };

        if (mode == "183map")
        {
            using var w = new BinaryWriter(File.Create("l183.ppm"));
            w.Write(System.Text.Encoding.ASCII.GetBytes($"P6 {size} {size} 255\n"));
            for (int i = 0; i < tiles.Length; i++)
            {
                Tile t = tiles[i];
                Space sp = WorldLayout.L183SpaceOf(t);
                (int r, int g, int b) c = !Ours(i) ? (0, 0, 0)
                    : t.Kind == TileKind.Wall ? (t.Detail == WorldLayout.L183WallPillar ? (150, 150, 150) : (60, 64, 62))
                    : (Part)t.Detail switch
                    {
                        Part.Channel => (40, 90, 170),
                        Part.Gutter => (80, 150, 210),
                        Part.Grate => (30, 30, 30),
                        Part.Curb => (150, 160, 120),
                        _ => sp switch
                        {
                            Space.Main => (215, 215, 205),
                            Space.Side => (180, 175, 160),
                            Space.Gallery => (170, 140, 110),
                            Space.Chamber => (200, 220, 190),
                            _ => (230, 210, 170),
                        },
                    };
                if (t.Ceiling is CeilingKind.L183LampOn or CeilingKind.L183LampBright or CeilingKind.L183LampFlicker) c = (255, 230, 60);
                else if (t.Pipe != 0 && t.Kind == TileKind.Floor && (Part)t.Detail == Part.Walk) c = (120, 90, 70);
                w.Write((byte)c.r); w.Write((byte)c.g); w.Write((byte)c.b);
            }
            Console.WriteLine($"l183.ppm: {size}x{size} tiles from block {m0x * 32},{m0z * 32}");
            return true;
        }

        // Shares
        int cells = 0;
        var zoneCells = new int[4];
        for (int i = 0; i < n * n; i++)
        {
            if (!built[i]) continue;
            cells++;
            zoneCells[(int)layout.L183CellZone(m0x + i % n, m0z + i / n)]++;
        }
        var spaceTiles = new int[6];
        int walkTotal = 0, basin = 0, sump = 0, grates = 0, lamps = 0, flicker = 0, pipes = 0, sealedTiles = 0, water = 0;
        for (int i = 0; i < tiles.Length; i++)
        {
            if (!Ours(i)) continue;
            Tile t = tiles[i];
            if (!Walk(t)) continue;
            walkTotal++;
            Space sp = WorldLayout.L183SpaceOf(t);
            spaceTiles[(int)sp]++;
            var part = (Part)t.Detail;
            if (sp == Space.Chamber && part == Part.Channel) basin++;
            if (sp == Space.Hall && part == Part.Channel) sump++;
            if (part == Part.Grate) grates++;
            if (t.Kind == TileKind.Water) water++;
            if (t.Ceiling is CeilingKind.L183LampOn or CeilingKind.L183LampBright or CeilingKind.L183LampFlicker) lamps++;
            if (t.Ceiling == CeilingKind.L183LampFlicker) flicker++;
            if (t.Pipe != 0) pipes++;
            if (t.Sealed) sealedTiles++;
        }
        double Pct(int a, int b) => 100.0 * a / Math.Max(1, b);
        Console.WriteLine($"Level 183: centre cell {cmx},{cmz}, radius {radius} cells; window {n}x{n} cells round the centre, {cells} of them the level's");
        Console.WriteLine($"  cells: Trunk Tunnels {Pct(zoneCells[1], cells):0}%, Channels {Pct(zoneCells[2], cells):0}%, Junction Halls {Pct(zoneCells[3], cells):0}%");
        Console.WriteLine($"  walkable tiles {walkTotal}: mains {Pct(spaceTiles[1], walkTotal):0.0}%, side tunnels {Pct(spaceTiles[2], walkTotal):0.0}%, dry galleries {Pct(spaceTiles[3], walkTotal):0.0}%, "
            + $"chambers {Pct(spaceTiles[4], walkTotal):0.0}%, halls {Pct(spaceTiles[5], walkTotal):0.0}%; in the water {Pct(water, walkTotal):0.0}%");
        Console.WriteLine($"  chambers {basin / 9}, halls {sump / 16}, grate tiles {grates}, lamps {lamps} ({flicker} flickering; {(double)walkTotal / Math.Max(1, lamps):0} walkable tiles a lamp), pipe tiles {pipes}, sealed walkable tiles {sealedTiles}");

        // Reachability: every walkable tile (steps of one at most), then the dry walkways and grates alone
        (int Main, int Total, int EdgePieces, int Pockets, int PocketTiles, List<string> Examples) Pieces(Func<int, bool> member, Func<int, int, bool> step)
        {
            var piece = new int[tiles.Length];
            var sizes = new List<int> { 0 };
            var touches = new List<bool> { false };
            var q = new Queue<int>();
            int total = 0;
            for (int s = 0; s < tiles.Length; s++)
            {
                if (piece[s] != 0 || !member(s)) continue;
                int id = sizes.Count, count = 0;
                bool border = false;
                sizes.Add(0); touches.Add(false);
                piece[s] = id; q.Enqueue(s);
                while (q.Count > 0)
                {
                    int i = q.Dequeue(), x = i % size, z = i / size;
                    count++;
                    foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nx = x + dx, nz = z + dz;
                        if (nx < 0 || nz < 0 || nx >= size || nz >= size) { border = true; continue; }
                        int j = nz * size + nx;
                        if (piece[j] != 0 || !member(j) || !step(i, j)) continue;
                        piece[j] = id; q.Enqueue(j);
                    }
                }
                sizes[id] = count;
                touches[id] = border;
                total += count;
            }
            int main = 0;
            for (int id = 1; id < sizes.Count; id++) if (sizes[id] > sizes[main]) main = id;
            int edgePieces = 0, pockets = 0, pocketTiles = 0;
            var examples = new List<string>();
            for (int id = 1; id < sizes.Count; id++)
            {
                if (id == main) continue;
                if (touches[id]) { edgePieces++; continue; }
                pockets++;
                pocketTiles += sizes[id];
                if (examples.Count < 6)
                {
                    int at = Array.IndexOf(piece, id);
                    examples.Add($"{m0x * 32 + at % size},{m0z * 32 + at / size} ({sizes[id]})");
                }
            }
            return (sizes[main], total, edgePieces, pockets, pocketTiles, examples);
        }
        var all = Pieces(i => Ours(i) && Walk(tiles[i]), (i, j) => Math.Abs(Surface(tiles[i]) - Surface(tiles[j])) <= 1);
        Console.WriteLine($"  reach: main piece {all.Main} of {all.Total} walkable tiles ({Pct(all.Main, all.Total):0.00}%); pieces cut by the window's edge {all.EdgePieces}; "
            + $"pockets {all.Pockets} ({all.PocketTiles} tiles)" + (all.Examples.Count > 0 ? ": " + string.Join(", ", all.Examples) : ""));
        var dry = Pieces(i => Ours(i) && Dry(tiles[i]), (i, j) => true);
        Console.WriteLine($"  dry walkways and grates alone: main piece {dry.Main} of {dry.Total} ({Pct(dry.Main, dry.Total):0.00}%); cut by the edge {dry.EdgePieces}; "
            + $"pockets {dry.Pockets} ({dry.PocketTiles} tiles)" + (dry.Examples.Count > 0 ? ": " + string.Join(", ", dry.Examples) : ""));
        int drops = 0, grateDrops = 0;
        for (int i = 0; i < tiles.Length; i++)
        {
            if (!Ours(i) || !Dry(tiles[i])) continue;
            bool grate = (Part)tiles[i].Detail == Part.Grate;
            int x = i % size, z = i / size;
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                Tile o = tiles[nz * size + nx];
                if (o.Level == WorldLayout.Level183 && Walk(o) && Surface(o) == -2) { if (grate) grateDrops++; else drops++; }
            }
        }
        Console.WriteLine($"  a two-block drop into a channel with no curb between: from a walkway {drops}, from a grate (a bridge's or a deck's side) {grateDrops}");

        // The arrivals: on a dry walkway
        int found = 0, onWalk = 0;
        var spaces = new int[6];
        for (ulong key = 1; key <= 60; key++)
        {
            var a = layout.FindArrival(WorldLayout.Level183, key * 7919UL + 13);
            if (a == null) continue;
            found++;
            Tile t = layout.TileAt(a.Value.X, a.Value.Z);
            if (t.Level == WorldLayout.Level183 && t.Kind == TileKind.Floor && (Part)t.Detail == Part.Walk && !t.Sealed)
            {
                onWalk++;
                spaces[(int)WorldLayout.L183SpaceOf(t)]++;
            }
        }
        Console.WriteLine($"  arrivals: {found}/60 found, {onWalk} on a dry walkway (mains {spaces[1]}, sides {spaces[2]}, galleries {spaces[3]}, chambers {spaces[4]}, halls {spaces[5]})");

        // The whole region, every fourth cell
        int sampled = 0;
        var allZones = new int[4];
        for (int dz = -radius * 6 / 5; dz <= radius * 6 / 5; dz += 4)
            for (int dx = -radius * 6 / 5; dx <= radius * 6 / 5; dx += 4)
            {
                if (layout.LevelAt(cmx + dx, cmz + dz) != WorldLayout.Level183) continue;
                sampled++;
                allZones[(int)layout.L183CellZone(cmx + dx, cmz + dz)]++;
            }
        Console.WriteLine($"  whole region (every 4th cell, {sampled} sampled): Trunk Tunnels {Pct(allZones[1], sampled):0}%, Channels {Pct(allZones[2], sampled):0}%, Junction Halls {Pct(allZones[3], sampled):0}%");
        return true;
    }

    static string L183LinkLabel(Tile t) => null;

    static string L183UseKind(Tile t) => null;
}
