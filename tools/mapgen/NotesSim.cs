using Backrooms.Notes;

/// <summary>
/// mapgen notes [catalog.json]: simulates players reading wanderers' notes with the mod's own NoteSequencer and the
/// generated config/notes.json. Two scripted players read in different orders and levels (printed in full), then
/// 10,000 random players; checks that main 1 always comes first, every track comes in order, nothing repeats, folded
/// notes give rare entries while there are any, and gates are respected.
/// </summary>
static class NotesSim
{
    public static void Run(string[] args, Backrooms.Worldgen.WorldLayout layout, int m0x, int m0z, int n)
    {
        Supply(layout, m0x, m0z, n);
        string path = args.Length > 3 ? args[3] : Path.Combine(FindRepo(), "assets", "backrooms", "config", "notes.json");
        var cat = NoteCatalog.Parse(File.ReadAllText(path));
        Console.WriteLine($"catalog: {cat.Tracks.Count} tracks, {cat.ByKey.Count} entries ({path})");
        int failures = 0;

        // Two scripted players: (level read in, folded paper?) in the order they read
        var a = new (int Level, bool Rare)[] { (0, false), (0, false), (0, false), (0, false), (0, true), (0, false), (1, false), (1, false), (1, false), (0, false), (3, false), (3, true), (8, true), (8, false), (61, false), (61, true) };
        var b = new (int Level, bool Rare)[] { (1, true), (1, false), (3, false), (0, false), (0, false), (8, false), (1, false), (0, true), (0, true), (0, true), (0, false), (12, false), (17, false), (15, false) };
        failures += Scripted("player A", cat, a);
        failures += Scripted("player B", cat, b);

        // Many random players
        var rand = new Random(1234);
        int[] levels = { 0, 1, 2, 3, 4, 5, 6, 61, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 };
        int reads = 0, rareGiven = 0, rareAsked = 0, dirs = 0;
        for (int p = 0; p < 10000; p++)
        {
            var log = new NoteLog();
            var been = new HashSet<int> { 0 };
            int depth = 0;
            for (int i = 0; i < 400; i++)
            {
                // Players drift deeper over time, and sometimes go home
                if (rand.NextDouble() < 0.05) depth = Math.Min(levels.Length - 1, depth + 1);
                int level = rand.NextDouble() < 0.3 ? 0 : levels[rand.Next(depth + 1)];
                been.Add(level == 61 ? 6 : level);
                bool rare = rand.NextDouble() < 0.12;
                var res = NoteSequencer.Resolve(cat, log, level, rare, been.Contains);
                reads++;
                if (rare) rareAsked++;
                string err = CheckOne(cat, log, res, level, rare, been.Contains);
                if (err != null) { if (failures++ < 10) Console.WriteLine($"FAIL player {p} read {i}: {err}"); }
                if (res == null) { dirs++; log.Add(new NoteRead { Key = null }, null); continue; }
                if (res.Track.Cls == "rare") rareGiven++;
                log.Add(new NoteRead { Key = res.Entry.Key, Track = res.Track.Id, Level = level }, res.Pick);
            }
            failures += CheckLog(cat, log, $"random player {p}");
        }
        Console.WriteLine($"random: {reads} reads, {rareAsked} folded ({rareGiven} gave a rare entry), {dirs} plain directions");
        Console.WriteLine(failures == 0 ? "notes: OK" : $"notes: {failures} FAILURES");
        if (failures > 0) Environment.Exit(1);
    }

    /// <summary>Notes per cell in the window, by level: sealed and torn boxes (their own drops plus the code's extra) and loose notes.</summary>
    private static void Supply(Backrooms.Worldgen.WorldLayout layout, int m0x, int m0z, int n)
    {
        var cells = new Dictionary<int, int>();
        var sealedBoxes = new Dictionary<int, int>();
        var torn = new Dictionary<int, int>();
        var spots = new Dictionary<int, int>();
        var folded = new Dictionary<int, int>();
        for (int mz = m0z; mz < m0z + n; mz++)
            for (int mx = m0x; mx < m0x + n; mx++)
            {
                int level = layout.LevelAt(mx, mz);
                cells[level] = cells.GetValueOrDefault(level) + 1;
                foreach (var t in layout.BuildMacro(mx, mz))
                    if (t.SupplyBox) { if (t.Looted) torn[level] = torn.GetValueOrDefault(level) + 1; else sealedBoxes[level] = sealedBoxes.GetValueOrDefault(level) + 1; }
                foreach (var s in layout.NoteSpots(mx, mz))
                    if (s.Kind == "folded") folded[level] = folded.GetValueOrDefault(level) + 1; else spots[level] = spots.GetValueOrDefault(level) + 1;
            }
        Console.WriteLine($"note supply in a {n}x{n}-cell window (boxes and loose notes only; furniture adds more):");
        foreach (var (level, c) in cells.OrderBy(kv => kv.Key))
        {
            double s = sealedBoxes.GetValueOrDefault(level), tb = torn.GetValueOrDefault(level), sp = spots.GetValueOrDefault(level), fo = folded.GetValueOrDefault(level);
            double near = level <= 1 ? 1 : 0;
            double before = (s * 0.15 + tb * 0.06) / c, after = (s * (0.15 + 0.10 * near) + tb * (0.06 + 0.06 * near) + sp) / c;
            Console.WriteLine($"  level {level,2}: {c,5} cells, {s / c:0.00} sealed and {tb / c:0.00} torn boxes per cell, {sp / c:0.000} loose and {fo / c:0.000} folded loose notes per cell; ordinary notes per cell {before:0.000} before, {after:0.000} now");
        }
    }

    private static int Scripted(string name, NoteCatalog cat, (int Level, bool Rare)[] reads)
    {
        var log = new NoteLog();
        var been = new HashSet<int>();
        int failures = 0;
        Console.WriteLine($"\n{name}:");
        foreach (var (level, rare) in reads)
        {
            been.Add(level == 61 ? 6 : level);
            var res = NoteSequencer.Resolve(cat, log, level, rare, been.Contains);
            string err = CheckOne(cat, log, res, level, rare, been.Contains);
            if (err != null) { failures++; Console.WriteLine("  FAIL " + err); }
            string what = res == null ? "(plain directions)" : $"{res.Entry.Key,-8} {res.Track.Cls,-6} track {res.Track.Id}";
            Console.WriteLine($"  read in level {level,2}{(rare ? " (folded)" : "         ")} -> {what}");
            log.Add(new NoteRead { Key = res?.Entry.Key, Track = res?.Track.Id, Level = level }, res?.Pick);
        }
        return failures + CheckLog(cat, log, name);
    }

    /// <summary>Checks one resolution against the rules.</summary>
    private static string CheckOne(NoteCatalog cat, NoteLog log, NoteResolution res, int level, bool rare, Func<int, bool> been)
    {
        if (log.Read.Count == 0 && res?.Entry.Key != cat.Main.Entries[0].Key) return $"first note was {res?.Entry.Key}, not {cat.Main.Entries[0].Key}";
        if (res == null) return null;
        if (log.Has(res.Entry.Key)) return $"{res.Entry.Key} given twice";
        if (!NoteSequencer.GateMet(res.Entry, been)) return $"{res.Entry.Key} given before its gate";
        var track = res.Track;
        for (int i = 0; i < res.Entry.Index; i++) if (!log.Has(track.Entries[i].Key)) return $"{res.Entry.Key} before {track.Entries[i].Key}";
        if (track.Cls == "common" && track.Level >= 0 && track.Level != level) return $"{res.Entry.Key} (level {track.Level}) read in level {level}";
        if (track.Cls == "rare" && !rare) return $"rare {res.Entry.Key} from an ordinary note";
        if (rare && track.Cls != "rare" && res.Entry != cat.Main.Entries[0])
        {
            // Only once every rare note that could be due here is read (or waiting)
            if (NoteSequencer.Due(cat.RareFor(level), log, been) != null || NoteSequencer.Due(cat.RareAny, log, been) != null) return $"folded note gave common {res.Entry.Key} while rare ones were due";
        }
        if (!rare && track.Cls == "scrap" && (NoteSequencer.Due(cat.Main, log, been) != null || NoteSequencer.Due(cat.CommonFor(level), log, been) != null)) return $"scrap {res.Entry.Key} while common notes were due";
        return null;
    }

    private static int CheckLog(NoteCatalog cat, NoteLog log, string who)
    {
        var seen = new HashSet<string>();
        int failures = 0, lastMain = -1;
        foreach (var r in log.Read)
        {
            if (!seen.Add(r.Key)) { failures++; Console.WriteLine($"FAIL {who}: {r.Key} twice"); }
            var e = cat.Entry(r.Key);
            if (e.Track == cat.Main) { if (e.Index != lastMain + 1) { failures++; Console.WriteLine($"FAIL {who}: main out of order at {r.Key}"); } lastMain = e.Index; }
        }
        return failures;
    }

    private static string FindRepo()
    {
        string dir = AppContext.BaseDirectory;
        for (int i = 0; i < 8 && dir != null; i++, dir = Path.GetDirectoryName(dir))
            if (File.Exists(Path.Combine(dir, "Backrooms.csproj"))) return dir;
        return Directory.GetCurrentDirectory();
    }
}
