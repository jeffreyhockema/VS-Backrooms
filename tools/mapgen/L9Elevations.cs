using Backrooms.Worldgen;

/// <summary>
/// l9elev: front and side elevations of sample Suburbs houses round a Level 9 arrival, one of each kind found (one or two
/// storeys, the gable along the street or facing it, a garage under its own roof, a porch, a chimney), as the world
/// generator would build them, drawn at half-block height: siding, windows (dark or lit), doors, the garage door,
/// roof courses (whole, or the lower or upper half of a block), gable siding, chimney brick and cap, porch posts and
/// deck, fences. Before layout version 9 nothing above the usual band (rel 9) was built, so the elevations stop there.
/// Writes elevations.txt for tools' render (scratch elev.py): a header line per picture, then its rows, top first.
/// </summary>
static class L9Elevations
{
    // Codes: ' ' air, s siding, b brick siding, w dark glass, l lit glass, d door, g garage door, r roof, k chimney,
    // c chimney cap, p porch post, f fence, e porch deck, o doorway (open)
    public static void Run(WorldLayout layout, int n)
    {
        var arrival = layout.FindArrival(9, 99991UL);
        if (arrival == null) { Console.WriteLine("no arrival"); return; }
        int x0 = arrival.Value.X - n * 16, z0 = arrival.Value.Z - n * 16;
        int top = layout.Version >= 9 ? 24 : 9;
        Tile At(int x, int z) => layout.TileAt(x, z);

        bool House(Tile t) => t.Level == 9 && RoofBits.IsSloped(t.Roof) && !RoofBits.IsLowered(t.Roof) && t.Pattern != WallPattern.BarnGrey;
        int Lift(Tile t) => t.Height is >= WorldLayout.StoreyFloor and <= WorldLayout.StoreyOuterBlank ? 4 : 0;
        bool Siding(Tile t) => t.Pattern >= WallPattern.SidingWhite && t.Pattern <= WallPattern.Brick;

        // What is at half-block h (rel h / 2, its upper half if odd) of a column; ' ' for air
        char Code(int x, int z, int h)
        {
            Tile t = At(x, z);
            int rel = h / 2;
            bool upperHalf = (h & 1) == 1;
            if (t.Level != 9 || rel < 1 || rel > top) return ' ';
            char wall = t.Pattern == WallPattern.Brick ? 'b' : 's';
            int lift = Lift(t);
            if (layout.Version >= 9 && t.Depth > 0)
            {
                int from = RoofBits.IsSloped(t.Roof) ? RoofBits.Height(t.Roof) + lift : 1, cap = t.Depth + (RoofBits.IsSloped(t.Roof) ? lift : 0);
                if (rel >= from) return rel < cap ? 'k' : rel == cap ? (upperHalf ? ' ' : 'c') : ' ';
            }
            if ((t.Height & WorldLayout.StoreyPorch) != 0)
            {
                int parts = t.Height & ~WorldLayout.StoreyPorch;
                if ((parts & WorldLayout.PorchPost) != 0 && rel <= 3) return 'p';
                if (rel == 1 && !upperHalf && (parts & (WorldLayout.PorchDeck | WorldLayout.PorchStep)) != 0) return 'e';
            }
            if (t.Kind == TileKind.Bars && rel == 1) return 'f';
            if (RoofBits.IsSloped(t.Roof))
            {
                int rise = RoofBits.Rise(t.Roof), height = RoofBits.Height(t.Roof) + lift;
                int eaves = (RoofBits.IsLowered(t.Roof) ? 4 : 5) + lift;
                bool wallish = t.Kind is TileKind.Wall or TileKind.Door or TileKind.Doorway && Siding(t) || t.Pattern == WallPattern.GarageDoor;
                if (rel > height) return ' ';
                if (rel == height) return (rise & 1) == 0 ? (upperHalf ? ' ' : 'r') : upperHalf ? 'r' : (wallish ? wall : ' ');
                if (rel >= eaves) return wallish ? wall : ' ';
            }
            if (t.Kind is TileKind.Wall or TileKind.Door or TileKind.Doorway)
            {
                int wallTop = 4 + lift;
                if (rel > wallTop) return ' ';
                bool win = layout.Version >= 9 ? t.Kind == TileKind.Wall && t.Variant is 1 or 2 && t.Stack >= WorldLayout.WinSash : t.Variant is 1 or 2;
                bool tall = layout.Version >= 9;
                if (win && (rel == 2 || tall && rel == 3)) return t.Variant == 2 ? 'l' : 'w';
                if (t.Kind == TileKind.Wall && t.Variant == 3 && Siding(t) && layout.Version < 9) return 'k';
                if (lift > 0 && rel >= 5)
                {
                    if (layout.Version >= 9)
                    {
                        int shape = t.Detail & 0x1F;
                        if (shape >= WorldLayout.WinSash && rel is 6 or 7) return (t.Detail & WorldLayout.WinLit) != 0 ? 'l' : 'w';
                    }
                    else if (rel == 6 && (t.Variant is 1 or 2 || t.Kind is TileKind.Door or TileKind.Doorway) && t.Height != WorldLayout.StoreyOuterBlank) return 'w';
                    return wall;
                }
                if (t.Pattern == WallPattern.GarageDoor) return rel <= 2 ? 'g' : wall;
                if (t.Kind == TileKind.Door) return rel <= 2 ? 'd' : wall;
                if (t.Kind == TileKind.Doorway) return rel <= 2 ? ((t.Stack & WorldLayout.DoorMark) != 0 && layout.Version >= 9 ? ((t.Stack & WorldLayout.DoorOpen) != 0 ? 'o' : 'd') : 'o') : wall;
                return t.Kind == TileKind.Wall && Siding(t) ? wall : '#';
            }
            return ' ';
        }

        // Find the houses: the front-left corner of each house's footprint (a wall corner with the house to its south-east)
        var kinds = new Dictionary<string, (int X, int Z, int W, int D, bool South)>();
        var sb = new System.Text.StringBuilder();
        for (int z = z0; z < z0 + n * 32; z++)
            for (int x = x0; x < x0 + n * 32; x++)
            {
                Tile t = At(x, z);
                if (!House(t) || t.Kind != TileKind.Wall || t.Stack is not (1 or 2)) continue;
                // a corner on the street side: north-facing (a lot facing north) with its second face west
                bool south = t.Pier == ArchPier.South;
                if (!(t.Pier is ArchPier.North or ArchPier.South) || t.Stack != 2) continue;
                if (south != (((z % 64) + 64) % 64 >= 36)) continue; // (the lots in a block's south half face south)
                // walk east along the front to the other corner, and back to the rear
                int w = 1;
                while (w < 30 && !(At(x + w, z).Kind == TileKind.Wall && At(x + w, z).Stack == 1 && At(x + w, z).Pier == t.Pier)) w++;
                int dz = south ? -1 : 1, d = 1;
                while (d < 20 && !(At(x, z + d * dz).Kind == TileKind.Wall && At(x, z + d * dz).Stack == 2 && At(x, z + d * dz).Pier != t.Pier)) d++;
                if (w >= 30 || d >= 20) continue;
                Tile mid = At(x + w / 2, z + dz * (d / 2));
                bool two = Lift(mid) > 0;
                bool frontGable = RoofBits.Down(At(x + w / 2, z + dz).Roof) is ArchPier.East or ArchPier.West;
                bool garage = false, wing = false, porch = At(x + 1, z - dz).Floor == FloorKind.Porch, chimney = false;
                for (int i = 0; i <= w; i++) if (At(x + i, z).Pattern == WallPattern.GarageDoor) garage = true;
                if (garage) wing = RoofBits.Down(At(x + 1, z + dz * (d / 2)).Roof) is ArchPier.East or ArchPier.West || RoofBits.Down(At(x + w - 1, z + dz * (d / 2)).Roof) is ArchPier.East or ArchPier.West;
                for (int i = -1; i <= w + 1; i++) for (int j = 0; j <= d; j++) if (At(x + i, z + dz * j).Depth > 0) chimney = true;
                string kind = $"{(two ? "two storeys" : "one storey")}, {(frontGable ? "gable to the street" : "gable along the street")}"
                    + (garage ? wing ? ", garage under its own roof" : ", garage" : "") + (porch ? ", porch" : "") + (chimney ? ", chimney" : "");
                if (layout.Version < 9) kind = $"{(two ? "two storeys" : "one storey")}{(garage ? ", garage" : "")}{(porch ? ", porch" : "")}";
                if (!kinds.ContainsKey(kind)) kinds[kind] = (x, z, w, d, south);
            }
        foreach (var (kind, (hx, hz, w, d, south)) in kinds.OrderBy(k => k.Key))
        {
            int dz = south ? -1 : 1;
            // Front: looking from the street, the nearest thing in each column from the pavement back through the lot
            int ax = hx - 3, bx = hx + w + 3, hmax = 2 * top + 1;
            sb.AppendLine($"# front | {kind} | {bx - ax + 1} {hmax + 1} | house at {hx},{hz}, layout version {layout.Version}");
            for (int h = hmax; h >= 0; h--)
            {
                var row = new System.Text.StringBuilder();
                for (int cx = ax; cx <= bx; cx++)
                {
                    int px = south ? bx - (cx - ax) : cx; // (seen from the street, so a south-facing lot's west is on the right)
                    char c = ' ';
                    for (int k = -4; k <= d + 4 && c == ' '; k++) c = Code(px, hz + dz * k, h);
                    row.Append(c);
                }
                sb.AppendLine(row.ToString());
            }
            // Side: from the west, the nearest thing in each row from the side path in
            sb.AppendLine($"# side | {kind} | {d + 9} {hmax + 1} | from the west, the street on the {(south ? "right" : "left")}");
            for (int h = hmax; h >= 0; h--)
            {
                var row = new System.Text.StringBuilder();
                for (int k = -4; k <= d + 4; k++)
                {
                    char c = ' ';
                    for (int i = -3; i <= w + 3 && c == ' '; i++) c = Code(hx + i, hz + dz * k, h);
                    row.Append(c);
                }
                sb.AppendLine(row.ToString());
            }
        }
        File.WriteAllText("elevations.txt", sb.ToString());
        Console.WriteLine($"layout version {layout.Version}: {kinds.Count} kinds of house; wrote elevations.txt");
        foreach (var k in kinds.Keys.OrderBy(k => k)) Console.WriteLine("  " + k);
    }
}
