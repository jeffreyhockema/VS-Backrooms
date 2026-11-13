using Backrooms.Worldgen;

/// <summary>
/// gencount [window]: the Basement's and Level 52's food props (full and stripped, with a satiety estimate a cell), the tool
/// and seed props, and Level 52's trees and shrubs (Marshall David's 352-block square, and the whole window). Run it with
/// LAYOUT_VERSION=15 for before and the current version for after.
/// </summary>
static partial class LevelModes
{
    static bool GenModes(WorldLayout layout, string mode, string[] args)
    {
        if (mode != "gencount") return false;
        int n = args.Length > 3 && int.TryParse(args[3], out int k) ? k : 24;
        Console.WriteLine($"layout version {layout.Version}");
        // Satiety a prop gives full (after the level's food scale), from its drops: beans 450, crackers 300, a few others
        double Sat(string kind, int level) => (kind, level) switch
        {
            ("pantry", _) => 270, ("icebox", _) => 220, ("bshelf", _) => 60, ("cardboard", WorldLayout.Basement) => 22,
            ("shelf", _) => 120, ("fridge", _) => 240, ("cardboard", _) => 45, _ => 0,
        };
        string FoodKind(ushort v, int level) => v switch
        {
            Props.PantryShelf => "pantry", Props.CardboardBoxes => "cardboard", Props.Shelf => "shelf", Props.Fridge => "fridge",
            Props.Icebox => "icebox", Props.BasementShelf => "bshelf", _ => null,
        };
        foreach (int level in new[] { WorldLayout.Basement, WorldLayout.Level52 })
        {
            int cmx, cmz;
            if (level == WorldLayout.Basement) { var r = layout.BasementRegion; cmx = r.Item1; cmz = r.Item2; }
            else { cmx = layout.L52CentreX; cmz = layout.L52CentreZ; }
            var full = new SortedDictionary<string, int>(); var bare = new SortedDictionary<string, int>(); var other = new SortedDictionary<string, int>();
            int cells = 0; double satFull = 0, satLeft = 0;
            int treesMd = 0, shrubsMd = 0, treesAll = 0, shrubsAll = 0, treesCampus = 0, treesHill = 0;
            var (mci, mcj) = layout.L52MarshallDavid;
            int x0 = mci * WorldLayout.L52Period, z0 = mcj * WorldLayout.L52Period;
            for (int mz = cmz - n / 2; mz < cmz + n / 2; mz++)
                for (int mx = cmx - n / 2; mx < cmx + n / 2; mx++)
                {
                    if (layout.LevelAt(mx, mz) != level) continue;
                    var tiles = layout.BuildMacro(mx, mz);
                    cells++;
                    for (int i = 0; i < tiles.Length; i++)
                    {
                        Tile t = tiles[i];
                        if (t.Level != level) continue;
                        int gx = mx * 32 + i % 32, gz = mz * 32 + i / 32;
                        if (t.Kind != TileKind.Floor || t.SupplyBox) continue;
                        if (FoodKind(t.Variant, level) is string fk && (level == WorldLayout.Basement || fk is "shelf" or "fridge" or "cardboard"))
                        {
                            var d = t.Looted ? bare : full;
                            d[fk] = d.GetValueOrDefault(fk) + 1;
                            satFull += Sat(fk, level);
                            if (!t.Looted) satLeft += Sat(fk, level);
                        }
                        if (t.Variant is Props.ToolShelf or Props.ToolRack or Props.Toolbox or Props.SeedSacks or Props.Workbench)
                        {
                            string name = t.Variant == Props.ToolShelf ? "toolshelf" : t.Variant == Props.ToolRack ? "toolrack" : t.Variant == Props.Toolbox ? "toolbox" : t.Variant == Props.SeedSacks ? "seedsacks" : "workbench";
                            other[name] = other.GetValueOrDefault(name) + 1;
                        }
                        if (level == WorldLayout.Level52 && t.Variant is Props.Tree or Props.Shrub)
                        {
                            bool tree = t.Variant == Props.Tree;
                            bool md = gx >= x0 && gx < x0 + WorldLayout.L52Period && gz >= z0 && gz < z0 + WorldLayout.L52Period;
                            if (tree) { treesAll++; if (md) treesMd++; if (t.Zone is (byte)WorldLayout.L52Zone.Lawn or (byte)WorldLayout.L52Zone.Turf) treesCampus++; else treesHill++; }
                            else { shrubsAll++; if (md) shrubsMd++; }
                        }
                    }
                }
            Console.WriteLine($"Level {level}: {cells} cells");
            foreach (var kv in full) Console.WriteLine($"  food {kv.Key}: {kv.Value} full, {bare.GetValueOrDefault(kv.Key)} stripped; {kv.Value / (double)Math.Max(1, cells):0.00} full a cell");
            foreach (var kv in bare) if (!full.ContainsKey(kv.Key)) Console.WriteLine($"  food {kv.Key}: 0 full, {kv.Value} stripped");
            Console.WriteLine($"  satiety a cell (est.): all props {satFull / Math.Max(1, cells):0}, left after stripping {satLeft / Math.Max(1, cells):0}");
            foreach (var kv in other) Console.WriteLine($"  {kv.Key}: {kv.Value} ({kv.Value / (double)Math.Max(1, cells):0.00} a cell)");
            if (level == WorldLayout.Level52)
                Console.WriteLine($"  trees: Marshall David's square {treesMd} ({treesMd * 5} logs), shrubs there {shrubsMd}; whole window trees {treesAll} (campus lawns/courts {treesCampus}, hills {treesHill}), shrubs {shrubsAll}");
        }
        return true;
    }
}
