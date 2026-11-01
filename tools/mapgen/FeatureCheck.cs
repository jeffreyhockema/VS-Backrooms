using Backrooms.Cheats;
using Backrooms.Worldgen;

/// <summary>
/// featurecheck [arrivals] [level...]: runs every finder of the cheat menu's "Go to feature" list (src/Cheats/FeatureCatalog.cs,
/// FeatureFinder.cs) from a few arrival points in its level, as /backrooms feature does (its default radius; tile scans
/// are given 30 s instead of the server's 2), and says for each how many found one, how far, and whether there was a
/// floor to stand on. A miss is printed with why (wrong level, no such thing within the radius, the scan stopped).
/// </summary>
static class FeatureCheck
{
    public static void Run(WorldLayout layout, string[] args)
    {
        int arrivals = args.Length > 3 && int.TryParse(args[3], out int n) ? n : 3;
        var only = args.Skip(4).Select(WorldLayout.FromDisplayName).ToHashSet();
        var finder = new FeatureFinder(layout, new WorldGeometry(256)) { TileScanMillis = 30000 };
        int total = 0, allFound = 0, someFound = 0;
        var misses = new List<string>();
        foreach (var group in FeatureCatalog.All.GroupBy(e => e.Level))
        {
            int level = group.Key;
            if (only.Count > 0 && !only.Contains(level)) continue;
            var starts = new List<(int X, int Z)>();
            for (ulong k = 1; starts.Count < arrivals && k <= 40; k++)
                if (layout.FindArrival(level, k * 99991UL + 7) is { } a && !starts.Contains(a)) starts.Add(a);
            Console.WriteLine($"=== Level {WorldLayout.DisplayNumber(level)}: {group.Count()} features, from {starts.Count} arrivals");
            foreach (var e in group)
            {
                total++;
                int found = 0, stand = 0, elsewhere = 0;
                var dists = new List<int>();
                string why = "";
                long ms = 0;
                foreach (var (sx, sz) in starts)
                {
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    FeatureFinder.Hit hit;
                    try { hit = finder.Feature(e.Code, sx, sz, e.Radius, level, 12345UL); }
                    catch (Exception ex) { why = "THREW " + ex.GetType().Name + ": " + ex.Message; continue; }
                    ms = Math.Max(ms, sw.ElapsedMilliseconds);
                    if (hit == null) { why = finder.Error ?? (finder.Stopped ? "scan stopped" : $"none within {e.Radius}"); continue; }
                    found++;
                    if (hit.Elsewhere) elsewhere++;
                    dists.Add((int)Math.Sqrt((double)(hit.X - sx) * (hit.X - sx) + (double)(hit.Z - sz) * (hit.Z - sz)));
                    if (finder.Resolve(hit, level))
                    {
                        Tile t = layout.TileAt(hit.Stand.Value.X, hit.Stand.Value.Z);
                        if (t.Level == level || hit.FeetY != null) stand++;
                        else why = $"stand in level {t.Level}";
                    }
                    else why = "nowhere to stand";
                }
                if (found == starts.Count && stand == found) allFound++;
                else if (found > 0) someFound++;
                string line = $"  {e.Code,-16} {e.Name,-28} found {found}/{starts.Count} stand {stand}" + (elsewhere > 0 ? $" (elsewhere {elsewhere})" : "")
                    + (dists.Count > 0 ? $"  dist {dists.Min()}-{dists.Max()}" : "") + $"  {ms} ms" + (why.Length > 0 ? "  -- " + why : "");
                Console.WriteLine(line);
                if (found < starts.Count || stand < found) misses.Add($"Level {WorldLayout.DisplayNumber(level)} {e.Code}: {found}/{starts.Count}, stand {stand}; {why}");
            }
        }
        Console.WriteLine($"--- {total} features: {allFound} found from every arrival, {someFound} from some, {total - allFound - someFound} from none");
        foreach (string m in misses) Console.WriteLine("MISS " + m);
    }
}
