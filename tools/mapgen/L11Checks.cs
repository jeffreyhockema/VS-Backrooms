using System.Text;
using Backrooms.Worldgen;

/// <summary>
/// l11stairs [stations]: walks every flight of stairs down into the subway at the stations nearest the city's centre
/// (both ends of each station, both sides of the avenue, both columns of each two-wide flight and the line between
/// them) with the player's box (0.6 wide, 1.85 tall, stepping up at most 0.6), down from the sidewalk to the platform
/// and back up, over the blocks the generator builds there (WorldGenerator.City.cs: SubwayBlock, the station's
/// stair tiles by <see cref="WorldLayout.CityStationStepRel"/>, what stands on the platform by
/// <see cref="WorldLayout.CityPlatformProp"/>, the sidewalk's furniture and railings). Prints, per flight, whether the
/// walk got through each way, the highest step up it met and the least headroom; and writes <c>l11stairs.txt</c>, a
/// side view of the first flight of each kind.
/// l11church: the front and back elevations of the churches near the centre, with the stained glass where the
/// generator puts it (<see cref="WorldLayout.CityStainedGlass"/>), whether each is symmetric about the door, written to
/// <c>l11church.txt</c>.
/// </summary>
static class L11Checks
{
    const double Half = 0.3, Tall = 1.85, StepUp = 0.6;

    record struct Box(double Z1, double Y1, double Z2, double Y2);

    public static void Stairs(WorldLayout layout, int stations)
    {
        int ox = layout.CityOriginX, oz = layout.CityOriginZ;
        int period = WorldLayout.StreetPitch * WorldLayout.StationEvery, L = WorldLayout.StationLength;
        var cache = new Dictionary<(int, int), Tile>();
        Tile At(int x, int z) { if (!cache.TryGetValue((x, z), out var t)) cache[(x, z)] = t = layout.TileAt(x, z); return t; }

        // The solid boxes of the column at (x, z), in (z, y), y the height above the street's floor block's bottom (rel)
        List<Box> Column(int x, int z)
        {
            var list = new List<Box>();
            void Full(int rel) => list.Add(new Box(z, rel, z + 1, rel + 1));
            Tile t = At(x, z);
            int ax = Hashing.Mod(x - ox, WorldLayout.AvePitch), uz = z - oz;
            if (t.Under == Unders.Station && t.Stair > 0)
            {
                int step = layout.CityStationStepRel(t);
                for (int rel = -8; rel < step; rel++) Full(rel);
                list.Add(new Box(z, step, z + 1, step + 0.5));
                // the upper half on the side the flight climbs toward
                list.Add(t.Pier == ArchPier.North ? new Box(z, step + 0.5, z + 0.5, step + 1) : new Box(z + 0.5, step + 0.5, z + 1, step + 1));
                return list;
            }
            if (t.Under == Unders.Station)
            {
                // A platform (the stair columns are platform from wall to edge): its floor, the ceiling, the street over it
                Full(-8); Full(-7); Full(-6);
                if (layout.CityPlatformProp(ax, uz) != 0) Full(-5);
                Full(-1); Full(0);
            }
            else for (int rel = -8; rel <= 0; rel++) Full(rel);
            // At street level: a railing, a building, or the sidewalk's furniture
            if (t.Kind is TileKind.Bars || t.Depth > 0 || t.Kind == TileKind.Wall) { Full(1); Full(2); Full(3); }
            else if (t.Variant != 0 && t.Variant is not (Props.Crop or Props.TallGrass)) Full(1);
            return list;
        }

        var sb = new StringBuilder();
        int flights = 0, badDown = 0, badUp = 0;
        double worstStep = 0, leastHead = 99;
        var drawn = new HashSet<string>();
        for (int bi = -stations; bi <= stations; bi++)
            for (int s = -stations; s <= stations; s++)
                foreach (bool northEnd in new[] { true, false })
                    foreach (bool west in new[] { true, false })
                    {
                        int top = s * period - WorldLayout.StationReach + (northEnd ? 0 : L - 1);
                        int dir = northEnd ? 1 : -1; // the way down, along z
                        int ax0 = west ? 0 : WorldLayout.AveWidth - 2;
                        int x0 = ox + bi * WorldLayout.AvePitch + ax0;
                        // (From two rows out on the sidewalk, which nothing may stand in, to the landing two rows past the foot)
                        int zStart = oz + top - 2 * dir, zEnd = oz + top + 8 * dir;
                        if (At(x0, oz + top).Level != 11) continue;
                        flights++;
                        string name = $"{(northEnd ? "north" : "south")} end, {(west ? "west" : "east")} side, at {x0},{oz + top}";
                        double flightStep = 0, flightHead = 99;
                        bool okDown = true, okUp = true;
                        // Three lines down the flight: each column's middle, and the line between them
                        foreach (double lx in new[] { 0.5, 1.0, 1.5 })
                        {
                            var cols = new List<int>();
                            for (int c = 0; c < 2; c++) if (Math.Abs(lx - (c + 0.5)) < 0.5 + Half) cols.Add(x0 + c);
                            List<Box> Boxes(double zc)
                            {
                                var all = new List<Box>();
                                for (int z = (int)Math.Floor(zc - Half); z <= (int)Math.Floor(zc + Half); z++)
                                    foreach (int x in cols) all.AddRange(Column(x, z));
                                return all;
                            }
                            foreach (bool down in new[] { true, false })
                            {
                                double z0 = down ? zStart + 0.5 : zEnd + 0.5, z1 = down ? zEnd + 0.5 : zStart + 0.5, sgn = Math.Sign(z1 - z0);
                                double feet = Support(Boxes(z0), z0, down ? 99 : -4.9); // (on the street, or on the platform under it)
                                bool ok = true;
                                for (double zc = z0; sgn * (z1 - zc) > 0; zc += sgn * 0.05)
                                {
                                    var boxes = Boxes(zc);
                                    // what is under the feet now, and the highest thing in the box's way
                                    double under = Support(boxes, zc, feet + StepUp);
                                    if (under > feet) flightStep = Math.Max(flightStep, under - feet);
                                    double blocking = boxes.Where(b => b.Z2 > zc - Half + 1e-6 && b.Z1 < zc + Half - 1e-6 && b.Y2 > feet + StepUp + 1e-6 && b.Y1 < feet + Tall - 1e-6).Select(b => b.Y2).DefaultIfEmpty(double.NaN).Max();
                                    if (!double.IsNaN(blocking))
                                    {
                                        // A lip too high to step: does the box stand under it with its head clear (it was the ceiling)?
                                        ok = false;
                                        flightStep = Math.Max(flightStep, blocking - feet);
                                        sb.AppendLine($"  {name}: {(down ? "going down" : "going up")} on line {lx}, blocked at z {zc:0.00} (feet {feet:0.00}, in the way up to {blocking:0.00})");
                                        break;
                                    }
                                    feet = under;
                                    double head = boxes.Where(b => b.Z2 > zc - Half + 1e-6 && b.Z1 < zc + Half - 1e-6 && b.Y1 >= feet + 1e-6).Select(b => b.Y1 - feet).DefaultIfEmpty(99).Min();
                                    flightHead = Math.Min(flightHead, head);
                                }
                                if (!ok) { if (down) okDown = false; else okUp = false; }
                            }
                        }
                        if (!okDown) badDown++;
                        if (!okUp) badUp++;
                        worstStep = Math.Max(worstStep, flightStep);
                        leastHead = Math.Min(leastHead, flightHead);
                        sb.AppendLine($"{name}: down {(okDown ? "ok" : "BLOCKED")}, up {(okUp ? "ok" : "BLOCKED")}, highest step up {flightStep:0.00}, least headroom {flightHead:0.00}");
                        string kind = (northEnd ? "N" : "S") + (west ? "W" : "E");
                        if (drawn.Add(kind)) sb.Append(Profile(layout, At, Column, x0, oz + top, dir, name));
                    }
        File.WriteAllText("l11stairs.txt", sb.ToString());
        Console.WriteLine($"{flights} flights: {badDown} could not be walked down, {badUp} could not be walked up; highest step up {worstStep:0.00}, least headroom {leastHead:0.00} (l11stairs.txt)");
    }

    /// <summary>The highest top of what is under the box at <paramref name="zc"/> no higher than <paramref name="limit"/>.</summary>
    static double Support(List<Box> boxes, double zc, double limit) =>
        boxes.Where(b => b.Z2 > zc - Half + 1e-6 && b.Z1 < zc + Half - 1e-6 && b.Y2 <= limit + 1e-6).Select(b => b.Y2).DefaultIfEmpty(-99).Max();

    /// <summary>A side view of a flight down its west column (z along, rel up), as the blocks are built.</summary>
    static string Profile(WorldLayout layout, Func<int, int, Tile> At, Func<int, int, List<Box>> Column, int x, int top, int dir, string name)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"--- side view, {name} (the street to the {(dir > 0 ? "left" : "right")}, z {(dir > 0 ? "rising" : "falling")} to the right; '\\' and '/' steps climbing left and right, # solid, P a prop, | a railing)");
        var zs = Enumerable.Range(-3, 14).Select(k => top + k * dir).OrderBy(z => z).ToList();
        for (int rel = 3; rel >= -7; rel--)
        {
            var line = new StringBuilder($"{rel,3} ");
            foreach (int z in zs)
            {
                Tile t = At(x, z);
                char c = ' ';
                if (t.Under == Unders.Station && t.Stair > 0)
                {
                    int step = layout.CityStationStepRel(t);
                    c = rel < step ? '#' : rel == step ? (t.Pier == ArchPier.North ? '\\' : '/') : ' ';
                }
                else
                {
                    var boxes = Column(x, z);
                    bool solid = boxes.Any(b => b.Y1 <= rel && b.Y2 >= rel + 1);
                    if (solid) c = rel >= 1 ? (t.Kind == TileKind.Bars ? '|' : t.Depth > 0 ? '#' : 'P') : rel == -5 && t.Under == Unders.Station ? 'P' : '#';
                }
                line.Append(c).Append(c);
            }
            sb.AppendLine(line.ToString());
        }
        var idx = new StringBuilder("    ");
        foreach (int z in zs) idx.Append(Hashing.Mod(z - top + 60, 10)).Append(' ');
        sb.AppendLine(idx + $" (z mod 10 from the top step at {top})");
        return sb.ToString();
    }

    public static void Church(WorldLayout layout, int blocks)
    {
        var cache = new Dictionary<(int, int), Tile>();
        Tile At(int x, int z) { if (!cache.TryGetValue((x, z), out var t)) cache[(x, z)] = t = layout.TileAt(x, z); return t; }
        var lots = L11Rooms.FindLots(layout, blocks, At).Where(l => l.Kind == CityKind.Church).ToList();
        var sb = new StringBuilder();
        int fronts = 0, symmetric = 0;
        foreach (var l in lots)
        {
            int W = l.X1 - l.X0 + 1, D = l.Z1 - l.Z0 + 1;
            (int, int) Wd(int u, int v) => l.North ? (l.X0 + u, l.Z0 + v) : (l.X1 - u, l.Z1 - v);
            // The door's middle, in the front wall; the back wall's glass is laid out on the same line
            int lo = -1, hi = -1;
            for (int u = 0; u < W; u++) { var (x, z) = Wd(u, 0); if (At(x, z).Kind == TileKind.Doorway) { if (lo < 0) lo = u; hi = u; } }
            double axis = (lo + hi) / 2.0;
            foreach (int v in new[] { 0, D - 1 })
            {
                bool front = v == 0;
                var glassCols = new List<int>();
                var rows = new List<string>();
                for (int rel = 9; rel >= 1; rel--)
                {
                    var line = new StringBuilder($"{rel,3} ");
                    for (int u = 0; u < W; u++)
                    {
                        var (x, z) = Wd(u, v); Tile t = At(x, z);
                        char c;
                        if ((t.Detail & CityDetail.Corner) != 0) c = 'P';
                        else if (t.Kind == TileKind.Doorway && rel <= 2) c = ' ';
                        else if (t.Kind == TileKind.Doorway && rel == 3) c = 'f';
                        else if ((t.Detail & CityDetail.Party) != 0) c = rel % 8 == 0 ? '-' : '#';
                        else if (layout.CityStainedGlass(t, x, z, rel, t.Pier)) { c = 'G'; if (!glassCols.Contains(u)) glassCols.Add(u); }
                        else c = rel % 8 == 0 ? '-' : '#';
                        line.Append(c).Append(c);
                    }
                    rows.Add(line.ToString());
                }
                bool sym = glassCols.All(u => glassCols.Contains((int)Math.Round(2 * axis - u)));
                if (front) { fronts++; if (sym) symmetric++; }
                sb.AppendLine($"=== church at {l.X0},{l.Z0} .. {l.X1},{l.Z1}, {W} wide, front {(l.North ? "north" : "south")}: {(front ? "front" : "back")} wall; glass in columns {string.Join(",", glassCols.OrderBy(u => u))} about the door's middle {axis}: {(sym ? "symmetric" : "NOT symmetric")}");
                foreach (var r in rows) sb.AppendLine(r);
                var idx = new StringBuilder("    ");
                for (int u = 0; u < W; u++) idx.Append(u % 10).Append(' ');
                sb.AppendLine(idx + " (u across the lot, from the left as you face the street from inside; P corner pier, G stained glass, f fascia over the door, - band)");
            }
        }
        File.WriteAllText("l11church.txt", sb.ToString());
        Console.WriteLine($"{lots.Count} churches; {symmetric} of {fronts} fronts have their stained glass symmetric about the door (l11church.txt)");
    }
}
