using Backrooms.Worldgen;

/// <summary>
/// Gate statistics: for each pair of neighbouring levels, how many boundary edges there are and how many gates, and
/// whether a sample of gates open onto walkable, unsealed floor on both sides.
/// </summary>
static class Gates
{
    static bool Walkable(in Tile t)
    {
        if (t.Kind is TileKind.Doorway or TileKind.ArchDoor or TileKind.Water) return true;
        if (t.Kind != TileKind.Floor) return false;
        if (t.Stack > 0 && t.Variant == 0 || t.SupplyBox) return false;
        return t.Variant is 0 or Props.WheelStop or Props.SpeedBump or Props.FloorCable or Props.Bedroll or Props.SleepingBag or Props.ImprovBed or Props.Crop or Props.TallGrass or Props.Reeds or Props.Tripwire or Props.FieldGate or Props.MachineParts or Props.MegPlacard;
    }

    public static void Run(WorldLayout layout, int smx, int smz, int radius)
    {
        var edges = new Dictionary<(int, int), int>();
        var gatesByPair = new Dictionary<(int, int), List<(int X, int Z, int To, int From)>>();
        for (int mz = smz - radius; mz <= smz + radius; mz++)
            for (int mx = smx - radius; mx <= smx + radius; mx++)
            {
                int l = layout.LevelAt(mx, mz);
                foreach (var (ox, oz) in new[] { (mx - 1, mz), (mx, mz - 1) })
                {
                    int o = layout.LevelAt(ox, oz);
                    if (o == l) continue;
                    var key = (Math.Min(l, o), Math.Max(l, o));
                    edges[key] = edges.GetValueOrDefault(key) + 1;
                }
            }
        // Gates seen from each level's side (each gate is listed from both levels; keep the lower)
        var seen = new HashSet<(int, int)>();
        for (int level = 0; level <= 10; level++)
        {
            // Scan in chunks so GatesNear's box stays small
            for (int bz = smz - radius; bz <= smz + radius; bz += 20)
                for (int bx = smx - radius; bx <= smx + radius; bx += 20)
                {
                    int cx = bx * 32 + 320, cz = bz * 32 + 320;
                    foreach (var g in layout.GatesNear(cx, cz, level, 320))
                    {
                        if (!seen.Add((g.X, g.Z))) continue;
                        var key = (Math.Min(level, g.To), Math.Max(level, g.To));
                        if (!gatesByPair.TryGetValue(key, out var list)) gatesByPair[key] = list = new();
                        list.Add((g.X, g.Z, g.To, level));
                    }
                }
        }
        foreach (var kv in edges.OrderBy(k => k.Key))
        {
            int gates = gatesByPair.TryGetValue(kv.Key, out var list) ? list.Count : 0;
            Console.WriteLine($"L{kv.Key.Item1}-L{kv.Key.Item2}: {kv.Value} boundary edges, {gates} gates, {(gates > 0 ? kv.Value / (double)gates : 0):0.0} edges per gate");
        }

        // Do a sample of gates open onto floor someone can reach, on both sides?
        int bad = 0, checkedCount = 0;
        foreach (var kv in gatesByPair.OrderBy(k => k.Key))
        {
            int pairBad = 0, pairChecked = 0;
            foreach (var g in kv.Value.Take(400))
            {
                pairChecked++;
                // The doorway is in the wall line x = mx*32 (a west edge) or z = mz*32 (a north edge)
                bool westEdge = Hashing.Mod(g.X, 32) == 0;
                int mx = WorldLayout.MacroOf(g.X), mz = WorldLayout.MacroOf(g.Z);
                Tile[] here = layout.BuildMacro(mx, mz);
                Tile[] there = westEdge ? layout.BuildMacro(mx - 1, mz) : layout.BuildMacro(mx, mz - 1);
                int lx = Hashing.Mod(g.X, 32), lz = Hashing.Mod(g.Z, 32);
                Tile door = here[WorldLayout.TileIndex(lx, lz)];
                Tile inside = westEdge ? here[WorldLayout.TileIndex(1, lz)] : here[WorldLayout.TileIndex(lx, 1)];
                Tile outside = westEdge ? there[WorldLayout.TileIndex(31, lz)] : there[WorldLayout.TileIndex(lx, 31)];
                // Any doorway tile of the gate that opens onto unsealed floor on both sides will do
                bool ok = false;
                for (int i = 1; i < 32 && !ok; i++)
                {
                    Tile d = westEdge ? here[WorldLayout.TileIndex(0, i)] : here[WorldLayout.TileIndex(i, 0)];
                    if (d.Kind != TileKind.Doorway || !d.Tall) continue;
                    Tile a = westEdge ? here[WorldLayout.TileIndex(1, i)] : here[WorldLayout.TileIndex(i, 1)];
                    Tile o = westEdge ? there[WorldLayout.TileIndex(31, i)] : there[WorldLayout.TileIndex(i, 31)];
                    ok = Walkable(a) && !a.Sealed && Walkable(o) && !o.Sealed;
                }
                if (!ok)
                {
                    pairBad++;
                    if (pairBad <= 3) Console.WriteLine($"  bad gate L{kv.Key.Item1}-L{kv.Key.Item2} at {g.X},{g.Z}: door {door.Kind}, inside {inside.Kind}/{inside.Variant}{(inside.Sealed ? " sealed" : "")}, outside {outside.Kind}/{outside.Variant}{(outside.Sealed ? " sealed" : "")}");
                }
            }
            Console.WriteLine($"L{kv.Key.Item1}-L{kv.Key.Item2}: {pairChecked - pairBad}/{pairChecked} sampled gates open both sides");
            bad += pairBad; checkedCount += pairChecked;
        }
        Console.WriteLine($"total {checkedCount - bad}/{checkedCount} gates open");
    }
}
