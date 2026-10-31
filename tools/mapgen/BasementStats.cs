using Backrooms.Worldgen;
using Zone = Backrooms.Worldgen.WorldLayout.BasementZone;

/// <summary>The Basement's harness modes (experimental; this file is the level's own).</summary>
static partial class LevelModes
{
    /// <summary>
    /// basementstats [window]: over a window of cells (24 by 24 by default) round the region's middle: the zones' shares
    /// (cells and walkable tiles), Cellar rooms, stairs down into the water, lamps; then whether it can all be walked:
    /// stepping one level at most (dry floor and an upper step are level, the lower step one down, the bed two down), the
    /// walkable tiles split into connected pieces, every piece but the largest that does not reach the window's edge a
    /// sealed pocket (none should be larger than a room); where dry floor drops straight into the water; and the 60
    /// arrivals the regions mode tries, each on dry Cellar floor. Also the zone shares over the whole region (every
    /// fourth cell). basementmap [window]: writes basement.ppm of the window (one pixel a tile) for a look.
    /// </summary>
    static bool BasementModes(WorldLayout layout, string mode, string[] args)
    {
        if (mode != "basementstats" && mode != "basementmap") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int k) ? k : 24;
        var (cmx, cmz, radius) = layout.BasementRegion;
        int m0x = cmx - n / 2, m0z = cmz - n / 2, size = n * 32;
        var tiles = new Tile[size * size];
        var built = new bool[n * n];
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                built[mz * n + mx] = layout.LevelAt(m0x + mx, m0z + mz) == WorldLayout.Basement;
                var cell = layout.BuildMacro(m0x + mx, m0z + mz);
                for (int i = 0; i < 1024; i++) tiles[(mz * 32 + i / 32) * size + mx * 32 + i % 32] = cell[i];
            }
        bool Ours(int i) => tiles[i].Level == WorldLayout.Basement;
        // (A door counts unless it is swollen shut; the rubble, the dead, what lies on the floor and an Escherian stairwell's
        // steps are walked through or on: the stairwell's tiles are taken as floor, the loop is the server's)
        static bool Walk(in Tile t) => t.Kind == TileKind.Water
            || t.Kind == TileKind.Doorway && !WorldLayout.BasementDoorJammed(t)
            || t.Kind == TileKind.Floor && t.Stack == 0 && !t.SupplyBox && (t.Variant == 0 || t.Variant is Props.BasementDebris or Props.BasementBody
                or Props.BasementJunk or Props.FloorCable || t.Variant == Props.BasementEscher && t.Stair > 0);
        // The height of the surface stood on: dry floor 0, an upper step 0 (its top), a lower step -1, the bed -2
        static int Surface(in Tile t) => t.Kind == TileKind.Water ? t.Height - 2 : 0;

        if (mode == "basementmap")
        {
            using var w = new BinaryWriter(File.Create("basement.ppm"));
            w.Write(System.Text.Encoding.ASCII.GetBytes($"P6 {size} {size} 255\n"));
            for (int i = 0; i < tiles.Length; i++)
            {
                Tile t = tiles[i];
                (int r, int g, int b) c = !Ours(i) ? (0, 0, 0)
                    : t.Kind == TileKind.Wall ? (t.Pattern == WallPattern.BasementPillar ? (150, 150, 150) : (70, 74, 70))
                    : t.Kind == TileKind.Water ? (t.Height == 2 ? (120, 170, 200) : t.Height == 1 ? (60, 120, 170) : (20, 50, 110))
                    : t.Ceiling is CeilingKind.BasementBulbOn or CeilingKind.BasementBulbFlicker or CeilingKind.BasementBulbBright ? (255, 230, 120)
                    : t.Stack > 0 || t.Variant != 0 ? (150, 100, 60)
                    : t.Zone == (byte)Zone.Patch ? (200, 190, 150)
                    : t.Floor == FloorKind.BasementDamp ? (120, 125, 115) : (165, 165, 155);
                if (t.Kind == TileKind.Water && t.Ceiling == CeilingKind.BasementBulbDim) c = (220, 220, 90);
                if (t.Kind == TileKind.Water && t.Pipe != 0 && t.Height == 0) c = (60, 70, 90);
                w.Write((byte)c.r); w.Write((byte)c.g); w.Write((byte)c.b);
            }
            Console.WriteLine($"basement.ppm: {size}x{size} tiles from block {m0x * 32},{m0z * 32}");
            return true;
        }

        // Shares, rooms, stairs, lamps
        int cells = 0, cellar = 0, flood = 0, patch = 0;
        for (int i = 0; i < n * n; i++)
        {
            if (!built[i]) continue;
            cells++;
            switch (layout.BasementCellZone(m0x + i % n, m0z + i / n))
            {
                case Zone.Cellar: cellar++; break;
                case Zone.Flood: flood++; break;
                default: patch++; break;
            }
        }
        var tileZone = new int[4];
        int steps = 0, lampsOn = 0, lampsFlicker = 0, lampsOff = 0, lampsDim = 0, lampsBright = 0, props = 0, sealedTiles = 0;
        int doors = 0, jammed = 0, cracks = 0, towers = 0, bones = 0, drowned = 0, named = 0, junk = 0, boxes = 0, lifts = 0, carpet = 0, panels = 0;
        for (int i = 0; i < tiles.Length; i++)
        {
            if (!Ours(i)) continue;
            Tile t = tiles[i];
            if (Walk(t)) tileZone[t.Zone]++;
            if (t.Sealed && Walk(t)) sealedTiles++;
            if (t.Kind == TileKind.Water && t.Height == 2) steps++;
            if (t.Stack > 0 || t.Variant != 0) props++;
            if (t.Variant == Props.BasementDoor) { doors++; if (WorldLayout.BasementDoorJammed(t)) jammed++; }
            if (t.Detail == WorldLayout.BasementCrackMiddle) cracks++;
            if (t.Variant == Props.BasementEscher && t.Stair == 1) towers++;
            if (t.Variant == Props.BasementBody) { if (t.Stack == 0) bones++; else if (t.Stack == 1) drowned++; else named++; }
            if (t.Variant == Props.BasementJunk) junk++;
            if (t.SupplyBox) boxes++;
            if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.BasementLift) lifts++;
            if (t.Kind == TileKind.Floor && t.Floor is FloorKind.BasementCarpet or FloorKind.BasementCarpetWorn) carpet++;
            if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.BasementPanel) panels++;
            switch (t.Ceiling)
            {
                case CeilingKind.BasementBulbOn: lampsOn++; break;
                case CeilingKind.BasementBulbFlicker: lampsFlicker++; break;
                case CeilingKind.BasementBulbOff: lampsOff++; break;
                case CeilingKind.BasementBulbDim: lampsDim++; break;
                case CeilingKind.BasementBulbBright: lampsBright++; break;
            }
        }
        int walkTotal = tileZone[1] + tileZone[2] + tileZone[3];
        // Stairs: the Cellar-to-wet sides in the window (each one stair three wide)
        int stairs = 0;
        for (int mz = 0; mz < n; mz++)
            for (int mx = 0; mx < n; mx++)
            {
                if (!built[mz * n + mx]) continue;
                bool dry = layout.BasementCellZone(m0x + mx, m0z + mz) == Zone.Cellar;
                foreach (var (dx, dz) in new[] { (1, 0), (0, 1) })
                {
                    int ox = mx + dx, oz = mz + dz;
                    if (ox >= n || oz >= n || !built[oz * n + ox]) continue;
                    if (dry != (layout.BasementCellZone(m0x + ox, m0z + oz) == Zone.Cellar)) stairs++;
                }
            }
        Console.WriteLine($"The Basement: centre cell {cmx},{cmz}, radius {radius} cells; window {n}x{n} cells round the centre, {cells} of them the Basement's");
        Console.WriteLine($"  cells: Cellar {cellar} ({100.0 * cellar / Math.Max(1, cells):0}%), Flood {flood} ({100.0 * flood / Math.Max(1, cells):0}%), Dry Patch {patch} ({100.0 * patch / Math.Max(1, cells):0}%)");
        Console.WriteLine($"  walkable tiles: {walkTotal}: Cellar {100.0 * tileZone[1] / Math.Max(1, walkTotal):0}%, Flood {100.0 * tileZone[2] / Math.Max(1, walkTotal):0}%, Dry Patch rooms {100.0 * tileZone[3] / Math.Max(1, walkTotal):0}%");
        Console.WriteLine($"  stairs into the water: {stairs} (Cellar-to-wet sides), {steps} upper step tiles; props {props}; sealed walkable tiles {sealedTiles}");
        Console.WriteLine($"  lamps: on {lampsOn}, flicker {lampsFlicker} (Cellar); off {lampsOff}; dim {lampsDim} (Flood); bright {lampsBright} (Dry Patch)"
            + $"; Cellar floor per lit bulb {(double)tileZone[1] / Math.Max(1, lampsOn + lampsFlicker):0}, Flood tiles per lamp {(double)tileZone[2] / Math.Max(1, lampsDim):0}");

        Console.WriteLine($"  doors {doors} ({jammed} swollen shut); cracks {cracks}; Escherian stairwells {towers}; bodies: bones {bones}, drowned {drowned}, named {named}; "
            + $"things dropped {junk}; boxes {boxes}; elevator leaves {lifts}; carpet {100.0 * carpet / Math.Max(1, tileZone[1]):0}% of the Cellar's walkable tiles; panelled wall tiles {panels}");

        // Reachability: pieces joined by steps of one level at most
        var piece = new int[tiles.Length];
        var pieceSize = new List<int> { 0 };
        var touches = new List<bool> { false };
        var q = new Queue<int>();
        int drops = 0;
        for (int s = 0; s < tiles.Length; s++)
        {
            if (piece[s] != 0 || !Ours(s) || !Walk(tiles[s])) continue;
            int id = pieceSize.Count, count = 0;
            bool border = false;
            pieceSize.Add(0); touches.Add(false);
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
                    if (!Ours(j) || !Walk(tiles[j]) || Math.Abs(Surface(tiles[j]) - Surface(tiles[i])) > 1) continue;
                    if (piece[j] != 0) continue;
                    piece[j] = id; q.Enqueue(j);
                }
            }
            pieceSize[id] = count;
            touches[id] = border;
        }
        for (int i = 0; i < tiles.Length; i++)
        {
            if (!Ours(i) || tiles[i].Kind != TileKind.Floor || !Walk(tiles[i])) continue;
            int x = i % size, z = i / size;
            foreach (var (dx, dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int nx = x + dx, nz = z + dz;
                if (nx < 0 || nz < 0 || nx >= size || nz >= size) continue;
                Tile o = tiles[nz * size + nx];
                if (o.Kind == TileKind.Water && o.Height < 2) drops++;
            }
        }
        int main = 0;
        for (int id = 1; id < pieceSize.Count; id++) if (pieceSize[id] > pieceSize[main]) main = id;
        int pockets = 0, pocketTiles = 0, largest = 0, edgePieces = 0;
        var examples = new List<string>();
        for (int id = 1; id < pieceSize.Count; id++)
        {
            if (id == main) continue;
            if (touches[id]) { edgePieces++; continue; }
            pockets++;
            pocketTiles += pieceSize[id];
            largest = Math.Max(largest, pieceSize[id]);
            if (examples.Count < 6)
            {
                int at = Array.IndexOf(piece, id);
                examples.Add($"{m0x * 32 + at % size},{m0z * 32 + at / size} ({pieceSize[id]})");
            }
        }
        Console.WriteLine($"  reach: main piece {pieceSize[main]} of {walkTotal} walkable tiles ({100.0 * pieceSize[main] / Math.Max(1, walkTotal):0.0}%); "
            + $"pieces cut by the window's edge {edgePieces}; sealed pockets {pockets} ({pocketTiles} tiles, largest {largest})"
            + (examples.Count > 0 ? ": " + string.Join(", ", examples) : ""));
        Console.WriteLine($"  dry floor beside deep water with no step between: {drops}");

        // The arrivals: on dry Cellar floor
        int found = 0, dryCellar = 0;
        for (ulong key = 1; key <= 60; key++)
        {
            var a = layout.FindArrival(WorldLayout.Basement, key * 7919UL + 13);
            if (a == null) continue;
            found++;
            Tile t = layout.TileAt(a.Value.X, a.Value.Z);
            if (t.Kind == TileKind.Floor && t.Zone == (byte)Zone.Cellar && t.Level == WorldLayout.Basement) dryCellar++;
        }
        Console.WriteLine($"  arrivals: {found}/60 found, {dryCellar} on dry Cellar floor");

        // The whole region, every fourth cell
        int all = 0, allCellar = 0, allFlood = 0, allPatch = 0;
        for (int dz = -radius * 6 / 5; dz <= radius * 6 / 5; dz += 4)
            for (int dx = -radius * 6 / 5; dx <= radius * 6 / 5; dx += 4)
            {
                if (layout.LevelAt(cmx + dx, cmz + dz) != WorldLayout.Basement) continue;
                all++;
                switch (layout.BasementCellZone(cmx + dx, cmz + dz))
                {
                    case Zone.Cellar: allCellar++; break;
                    case Zone.Flood: allFlood++; break;
                    default: allPatch++; break;
                }
            }
        Console.WriteLine($"  whole region (every 4th cell, {all} sampled): Cellar {100.0 * allCellar / Math.Max(1, all):0}%, Flood {100.0 * allFlood / Math.Max(1, all):0}%, Dry Patch {100.0 * allPatch / Math.Max(1, all):0}%");
        return true;
    }

    static string BasementLinkLabel(Tile t) => null;

    static string BasementUseKind(Tile t) => null;
}
