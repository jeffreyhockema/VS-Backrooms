using Backrooms.Worldgen;

/// <summary>
/// Containers per cell by level: sealed boxes, torn boxes, sealed and emptied crates, and one example of each; and (layout
/// version 14) the food props of Levels 1-5, full and stripped, by kind, with an example of each.
/// </summary>
static class Loot
{
    public static void Run(WorldLayout layout, int smx, int smz, int radius, int step)
    {
        var cells = new int[12]; var sealedBox = new int[12]; var torn = new int[12]; var crate = new int[12]; var opened = new int[12];
        var example = new Dictionary<string, string>();
        var props = new SortedDictionary<string, (int Full, int Stripped)>();
        for (int mz = smz - radius; mz <= smz + radius; mz += step)
            for (int mx = smx - radius; mx <= smx + radius; mx += step)
            {
                var tiles = layout.BuildMacro(mx, mz);
                int l = tiles[0].Level; if (l > 11) continue;
                cells[l]++;
                for (int i = 0; i < tiles.Length; i++)
                {
                    Tile t = tiles[i];
                    if (l is >= 1 and <= 5 && t.Kind == TileKind.Floor && !t.SupplyBox && FoodProp(t.Variant) is string prop)
                    {
                        string key = $"L{l} {prop}";
                        var c = props.GetValueOrDefault(key);
                        props[key] = t.Looted ? (c.Full, c.Stripped + 1) : (c.Full + 1, c.Stripped);
                        example.TryAdd($"{prop}-{(t.Looted ? "stripped" : "full")}-L{l}", $"{mx * 32 + i % 32} {mz * 32 + i / 32}");
                    }
                    bool isCrate = t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack > 0 && !t.SupplyBox && l is 1 or 2 or 3 or 8;
                    if (!t.SupplyBox && !isCrate) continue;
                    string kind = (t.SupplyBox ? "box" : "crate") + (t.Looted ? "-open" : "-sealed") + "-L" + l;
                    if (t.SupplyBox) { if (t.Looted) torn[l]++; else sealedBox[l]++; } else { if (t.Looted) opened[l]++; else crate[l]++; }
                    example.TryAdd(kind, $"{mx * 32 + i % 32} {mz * 32 + i / 32}");
                }
            }
        for (int l = 0; l < 12; l++)
            if (cells[l] > 0)
                Console.WriteLine($"L{l}: {cells[l]} cells; per cell: sealed boxes {sealedBox[l] / (double)cells[l]:0.00}, torn {torn[l] / (double)cells[l]:0.00}, sealed crates {crate[l] / (double)cells[l]:0.00}, emptied {opened[l] / (double)cells[l]:0.00}");
        foreach (var kv in props)
            Console.WriteLine($"{kv.Key}: {kv.Value.Full} full, {kv.Value.Stripped} stripped ({kv.Value.Stripped / (double)Math.Max(1, kv.Value.Full + kv.Value.Stripped):P0})");
        foreach (var kv in example.OrderBy(k => k.Key)) Console.WriteLine($"  {kv.Key} at {kv.Value}");
    }

    static string FoodProp(ushort variant) => variant switch
    {
        Props.Shelf => "shelf", Props.Drum => "drum", Props.CardboardBoxes => "cardboard", Props.Fridge => "fridge",
        Props.KitchenCabinet => "cupboard", Props.PantryShelf => "pantry", _ => null,
    };
}
