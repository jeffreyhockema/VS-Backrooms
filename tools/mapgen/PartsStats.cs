using Backrooms.Worldgen;
/// <summary>
/// "parts": the camps' tents and bedrolls, and the sofas, round spawn, by level: the old one-tile ones and (layout version 6) the camp
/// tents, sleeping bags and long sofas over several tiles, any multi-tile prop missing a part (there should be none), and where
/// the first few of each are.
/// </summary>
static class PartsStats
{
    public static void Run(WorldLayout layout, int smx, int smz, int radius)
    {
        var counts = new SortedDictionary<(int, string), int>();
        var where = new Dictionary<string, List<string>>();
        void Count(int level, string what, int x, int z)
        {
            counts[(level, what)] = counts.GetValueOrDefault((level, what)) + 1;
            var list = where.TryGetValue($"{level} {what}", out var l) ? l : where[$"{level} {what}"] = new List<string>();
            if (list.Count < 4) list.Add($"{x} {z}");
        }
        for (int mz = smz - radius; mz <= smz + radius; mz++)
            for (int mx = smx - radius; mx <= smx + radius; mx++)
            {
                Tile[] tiles = layout.BuildMacro(mx, mz);
                int level = layout.LevelAt(mx, mz);
                for (int lz = 0; lz < 32; lz++)
                    for (int lx = 0; lx < 32; lx++)
                    {
                        Tile t = tiles[WorldLayout.TileIndex(lx, lz)];
                        int gx = mx * 32 + lx, gz = mz * 32 + lz;
                        if (t.Kind != TileKind.Floor) continue;
                        if (t.Variant == Props.Tent) Count(level, "tent (old)", gx, gz);
                        if (t.Variant == Props.Bedroll) Count(level, "bedroll (old)", gx, gz);
                        if (t.Variant == Props.Sofa) Count(level, "sofa (old)", gx, gz);
                        if (t.Variant == Props.MegMarker) Count(level, "M.E.G. marker", gx, gz);
                        if (t.Variant == Props.RoadLamp) Count(level, "road lamp", gx, gz);
                        var (w, d) = WorldLayout.PartsOf(t.Variant);
                        if (w * d == 1) continue;
                        if (t.Stack == 0) Count(level, t.Variant == Props.CampTent ? "camp tent" : t.Variant == Props.LongSofa ? "long sofa" : "sleeping bag", gx, gz);
                        // Whole? (every part where the front-left one says)
                        ArchPier facing = t.Variant == Props.SleepingBag ? (ArchPier)(t.Pier switch { ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East }) : t.Pier;
                        var (sx, sz) = WorldLayout.PartTile(0, 0, facing, t.Stack % w, t.Stack / w);
                        for (int n = 0; n < w * d; n++)
                        {
                            var (px, pz) = WorldLayout.PartTile(lx - sx, lz - sz, facing, n % w, n / w);
                            bool ok = px >= 0 && pz >= 0 && px < 32 && pz < 32 && tiles[WorldLayout.TileIndex(px, pz)] is var p
                                      && p.Variant == t.Variant && p.Stack == n && p.Pier == t.Pier && p.Kind == TileKind.Floor;
                            if (!ok) { Count(level, "PART MISSING", gx, gz); break; }
                        }
                    }
            }
        foreach (var kv in counts) Console.WriteLine($"L{kv.Key.Item1,-3} {kv.Key.Item2,-14} {kv.Value,5}   e.g. {string.Join(", ", where[$"{kv.Key.Item1} {kv.Key.Item2}"])}");
    }
}
