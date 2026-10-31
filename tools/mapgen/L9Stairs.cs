using Backrooms.Worldgen;

/// <summary>
/// l9stairs: walks every two-storey house's stairs round a Level 9 arrival with the player's box (0.6 wide, 1.85 tall,
/// stepping up at most 0.6), the blocks round the flight modelled as the generator builds them (floors, walls, the
/// floor between the storeys and the opening in it, the steps' half-block treads, from layout version 9 the
/// balustrade), from the floor before the first step to the top step and on to the landing beside it, down the middle
/// of the flight and 0.2 to either side. Prints, per step, the least headroom over the player's head, and any place
/// the box strikes something or could not step up. l9fences: counts the places two lot fences stand side by side
/// (two lines of fence a block apart along the same lot line), and writes fences.txt, a plan of a block of lots.
/// </summary>
static class L9Stairs
{
    const double Half = 0.3, Tall = 1.85, StepUp = 0.6;

    record struct Box(double X1, double Y1, double Z1, double X2, double Y2, double Z2);

    public static void Run(WorldLayout layout, int n)
    {
        var arrival = layout.FindArrival(9, 99991UL);
        if (arrival == null) { Console.WriteLine("no arrival"); return; }
        int x0 = arrival.Value.X - n * 16, z0 = arrival.Value.Z - n * 16, size = n * 32;
        var cache = new Dictionary<(int, int), Tile>();
        Tile At(int x, int z) { if (!cache.TryGetValue((x, z), out var t)) cache[(x, z)] = t = layout.TileAt(x, z); return t; }

        // The boxes of the block at (x, rel, z), in world units (rel 0 is the floor block)
        List<Box> Blocks(int x, int rel, int z)
        {
            var list = new List<Box>();
            void Full() => list.Add(new Box(x, rel, z, x + 1, rel + 1, z + 1));
            Tile t = At(x, z);
            if (rel <= 0) { Full(); return list; }
            byte storey = t.Height;
            bool upstairs = storey is >= WorldLayout.StoreyFloor and <= WorldLayout.StoreyOuterBlank;
            if (t.Stair > 0)
            {
                if (rel < t.Stair) { Full(); return list; }
                if (rel == t.Stair)
                {
                    var (cx, cz) = Climb(t.Pier);
                    list.Add(new Box(x, rel, z, x + 1, rel + 0.5, z + 1));
                    // the upper half: on the side the stairs climb toward
                    double ux1 = cx > 0 ? x + 0.5 : x, ux2 = cx < 0 ? x + 0.5 : x + 1, uz1 = cz > 0 ? z + 0.5 : z, uz2 = cz < 0 ? z + 0.5 : z + 1;
                    list.Add(new Box(ux1, rel + 0.5, uz1, ux2, rel + 1, uz2));
                    if ((t.Detail & WorldLayout.StairRail) != 0 && layout.Version >= 9)
                    {
                        bool east = (t.Detail & WorldLayout.StairRailEast) != 0;
                        // (house stairs climb north or south, so the balustrade runs along x = its side)
                        list.Add(east ? new Box(x + 1 - 0.125, rel, z, x + 1, rel + 1.5, z + 1) : new Box(x, rel, z, x + 0.125, rel + 1.5, z + 1));
                    }
                    return list;
                }
                if (rel < 4) return list;
            }
            if (!upstairs)
            {
                // a single-storey tile (or outside): walls to the eaves, rooms three high under the ceiling
                if (t.Kind is TileKind.Wall or TileKind.Door) { if (rel <= 4) Full(); return list; }
                if (t.Kind == TileKind.Doorway) { if (rel is 3 or 4) Full(); return list; }
                if (rel == 4 && t.Roof != 0) Full();
                return list;
            }
            if (rel < 4)
            {
                if (t.Kind is TileKind.Wall or TileKind.Door) Full();
                else if (t.Kind == TileKind.Doorway && rel == 3) Full();
                return list;
            }
            if (rel == 4) { if (storey != WorldLayout.StoreyHole || t.Stair == 4) Full(); return list; }
            if (rel == 8) { Full(); return list; }
            if (rel > 8) return list;
            switch (storey)
            {
                case WorldLayout.StoreyWall or WorldLayout.StoreyOuter or WorldLayout.StoreyOuterBlank: Full(); break;
                case WorldLayout.StoreyDoorway: if (rel == 7) Full(); break;
            }
            return list;
        }

        IEnumerable<Box> Near(double px, double pz, double feet, double reach = Tall + 1)
        {
            for (int bx = (int)Math.Floor(px - Half); bx <= (int)Math.Floor(px + Half - 1e-9); bx++)
                for (int bz = (int)Math.Floor(pz - Half); bz <= (int)Math.Floor(pz + Half - 1e-9); bz++)
                    for (int rel = (int)Math.Floor(feet) - 1; rel <= (int)Math.Floor(feet + reach); rel++)
                        foreach (var b in Blocks(bx, rel, bz))
                            if (b.X2 > px - Half + 1e-6 && b.X1 < px + Half - 1e-6 && b.Z2 > pz - Half + 1e-6 && b.Z1 < pz + Half - 1e-6) yield return b;
        }

        int houses = 0, struck = 0, stuck = 0;
        var worst = new double[6];
        for (int i = 0; i < worst.Length; i++) worst[i] = double.MaxValue;
        string example = null;
        for (int z = 16; z < size - 16; z++)
            for (int x = 16; x < size - 16; x++)
            {
                int gx = x0 + x, gz = z0 + z;
                Tile top = At(gx, gz);
                if (top.Level != 9 || top.Stair != 4 || top.Height == 0) continue;
                houses++;
                var (cx, cz) = Climb(top.Pier);
                int ax = gx - 4 * cx, az = gz - 4 * cz; // the floor before the first step
                // (a balustrade keeps the box off its side: the game would slide the player along it)
                Tile first = At(gx - 3 * cx, gz - 3 * cz);
                bool railed = layout.Version >= 9 && (first.Detail & WorldLayout.StairRail) != 0;
                double railSide = railed ? ((first.Detail & WorldLayout.StairRailEast) != 0 ? 1 : -1) : 0;
                foreach (double side0 in new[] { -0.2, 0.0, 0.2 })
                {
                    double side = railed && side0 * railSide > 0.5 - 0.125 - Half ? railSide * (0.5 - 0.125 - Half) : side0;
                    // Up the flight, then off the top step onto the landing either side
                    var path = new List<(double X, double Z)>();
                    double ox = cz != 0 ? side : 0, oz = cx != 0 ? side : 0;
                    for (double s = 0; s <= 4.0001; s += 0.05) path.Add((ax + 0.5 + ox + cx * s, az + 0.5 + oz + cz * s));
                    foreach (int lateral in new[] { -1, 1 })
                    {
                        var land = new List<(double, double)>(path);
                        int lx = cz != 0 ? lateral : 0, lz = cx != 0 ? lateral : 0;
                        Tile landing = At(gx + lx, gz + lz);
                        if (!WorldLayout.IsUpstairsFloor(landing.Height) || (landing.Detail & 31) != 0) continue;
                        for (double s = 0.05; s <= 1.0001; s += 0.05) land.Add((gx + 0.5 + ox + lx * s, gz + 0.5 + oz + lz * s));
                        double feet = 1;
                        string fault = null;
                        foreach (var (px, pz) in land)
                        {
                            double support = 0;
                            // (whatever the legs meet: the highest top of anything starting below a step's height)
                            foreach (var b in Near(px, pz, feet)) if (b.Y1 < feet + StepUp - 1e-6) support = Math.Max(support, b.Y2);
                            if (support > feet + StepUp + 1e-6) { fault ??= $"could not step up at {px:0.00},{pz:0.00}"; break; }
                            double nf = support;
                            double ceiling = double.MaxValue;
                            bool hit = false;
                            foreach (var b in Near(px, pz, nf, 8))
                            {
                                if (b.Y1 >= nf - 1e-6) ceiling = Math.Min(ceiling, b.Y1);
                                if (b.Y2 > nf + 1e-6 && b.Y1 < nf + Tall - 1e-6) hit = true;
                            }
                            // the step this is over (0 the floor, 1-4 the steps, 5 the landing)
                            int k = (int)Math.Floor(Math.Abs((px - ax - 0.5) * cx + (pz - az - 0.5) * cz) + 0.5);
                            bool onLanding = Math.Abs((px - gx - 0.5) * lx + (pz - gz - 0.5) * lz) > 0.5;
                            int idx = onLanding ? 5 : Math.Clamp(k, 0, 4);
                            worst[idx] = Math.Min(worst[idx], ceiling - nf);
                            if (hit) { fault ??= $"strikes something at {px:0.00},{pz:0.00} (feet {nf:0.00}, headroom {ceiling - nf:0.00})"; break; }
                            feet = nf;
                        }
                        if (fault != null)
                        {
                            if (fault.StartsWith("strikes")) struck++; else stuck++;
                            example ??= $"house with its top step at {gx},{gz}, {(side == 0 ? "middle" : side < 0 ? "left" : "right")} of the flight, to the {(lateral < 0 ? "left" : "right")}: {fault}";
                        }
                    }
                }
            }
        Console.WriteLine($"{n}x{n} cells round a Level 9 arrival (layout version {layout.Version}): {houses} two-storey houses' stairs walked (three lines up each, off either side at the top)");
        string[] names = { "floor before the flight", "step 1", "step 2", "step 3", "step 4 (top)", "landing" };
        for (int i = 0; i < names.Length; i++) Console.WriteLine($"  least headroom over the head (feet to whatever is above) on the {names[i]}: {(worst[i] == double.MaxValue ? "-" : (worst[i] - Tall).ToString("0.00") + " to spare, " + worst[i].ToString("0.00") + " clear")}");
        Console.WriteLine($"walks that struck something: {struck}; walks that could not step up: {stuck}");
        if (example != null) Console.WriteLine("  e.g. " + example);
    }

    static (int, int) Climb(ArchPier p) => p switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };

    public static void Fences(WorldLayout layout, int n)
    {
        var arrival = layout.FindArrival(9, 99991UL);
        if (arrival == null) { Console.WriteLine("no arrival"); return; }
        int x0 = arrival.Value.X - n * 16, z0 = arrival.Value.Z - n * 16, size = n * 32;
        bool Fence(Tile t) => t.Level == 9 && t.Kind == TileKind.Bars && t.Pattern == WallPattern.Fence && t.Height == 0;
        int fences = 0, doubled = 0, loose = 0;
        for (int z = 1; z < size - 1; z++)
            for (int x = 1; x < size - 1; x++)
            {
                Tile t = layout.TileAt(x0 + x, z0 + z);
                if (!Fence(t)) continue;
                fences++;
                // Two runs side by side: a north-south run with another to its east, an east-west one with another to its south
                Tile e = layout.TileAt(x0 + x + 1, z0 + z), s = layout.TileAt(x0 + x, z0 + z + 1);
                if ((t.Stack & 5) != 0 && Fence(e) && (e.Stack & 5) != 0 && (t.Stack & 2) == 0) doubled++;
                if ((t.Stack & 10) != 0 && Fence(s) && (s.Stack & 10) != 0 && (t.Stack & 4) == 0) doubled++;
                // A rail that runs to a neighbour that is no fence
                foreach (var (bit, dx, dz) in new[] { (1, 0, -1), (2, 1, 0), (4, 0, 1), (8, -1, 0) })
                    if ((t.Stack & bit) != 0 && !Fence(layout.TileAt(x0 + x + dx, z0 + z + dz))) loose++;
            }
        Console.WriteLine($"{n}x{n} cells round a Level 9 arrival (layout version {layout.Version}): {fences} fence tiles, {doubled} places two fences stand side by side, {loose} rails running to no fence");
        // A plan of the town block nearest the arrival: the lots' fences, walls, houses and gates
        int bx = (int)Math.Floor(arrival.Value.X / 74.0) * 74, bz = (int)Math.Floor(arrival.Value.Z / 64.0) * 64;
        // (L9BLOCK=x,z draws the town block holding that block instead, to compare layout versions at one place)
        if (Environment.GetEnvironmentVariable("L9BLOCK") is string at && at.Split(',') is { Length: 2 } xz)
        {
            bx = (int)Math.Floor(int.Parse(xz[0]) / 74.0) * 74;
            bz = (int)Math.Floor(int.Parse(xz[1]) / 64.0) * 64;
        }
        var sb = new System.Text.StringBuilder();
        sb.AppendLine($"town block at {bx},{bz} (layout version {layout.Version}): | - + fence by its rails, # wall, w window, D door or doorway, G garage door, C chimney, = street, . open");
        for (int z = bz - 1; z <= bz + 64; z++)
        {
            for (int x = bx - 1; x <= bx + 74; x++)
            {
                Tile t = layout.TileAt(x, z);
                int sx = ((x % 74) + 74) % 74, sz = ((z % 64) + 64) % 64;
                char c = t.Level != 9 ? ' ' : Fence(t) ? ((t.Stack & 5) != 0 && (t.Stack & 10) != 0 ? '+' : (t.Stack & 5) != 0 ? '|' : (t.Stack & 10) != 0 ? '-' : 'o')
                    : t.Depth > 0 ? 'C'
                    : t.Kind == TileKind.Wall ? (t.Variant is 1 or 2 ? 'w' : '#')
                    : t.Kind == TileKind.Door ? (t.Pattern == WallPattern.GarageDoor ? 'G' : 'D')
                    : t.Kind == TileKind.Doorway ? 'D'
                    : t.Variant == Props.FieldGate ? 'g'
                    : sx < 8 || sz < 8 ? '=' : '.';
                sb.Append(c);
            }
            sb.AppendLine();
        }
        File.WriteAllText("fences.txt", sb.ToString());
        Console.WriteLine("wrote fences.txt");
    }
}
