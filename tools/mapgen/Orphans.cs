using Backrooms.Thresholds;
using Backrooms.Worldgen;

/// <summary>The orphans harness mode (0.700.0-pre.13: the new levels' balance in every world, WorldLayout.ExpVersion).</summary>
static partial class LevelModes
{
    /// <summary>
    /// orphans &lt;kind&gt; x z [rel]: a way out of a new level that a world made before layout 16 built at the pre-releases' rate
    /// and the quartered rate has since dropped from its layout (an orphan: WorldLayout.PreBalance). Prints the tile there in
    /// the layout and in its PreBalance twin, then what the threshold network makes of it: <c>kind</c> as a block used there
    /// (l31-revolving, l14-medical, l15-window), or <c>walk</c> as stood on at <c>rel</c> (a Level 14 floor that gives way at
    /// 1.05, a Level 15 pane at 2.5, its office stairs at -2). Run with LAYOUT_VERSION=15 (it still leads where it did) and 16
    /// (no twin: it leads nowhere).
    /// </summary>
    static bool OrphanModes(WorldLayout layout, string mode, string[] args)
    {
        if (mode != "orphans") return false;
        if (args.Length < 6) { Console.WriteLine("usage: orphans <l31-revolving|l14-medical|l15-window|walk> x z [rel]"); return true; }
        string kind = args[3];
        int x = int.Parse(args[4]), z = int.Parse(args[5]);
        double rel = args.Length > 6 ? double.Parse(args[6], System.Globalization.CultureInfo.InvariantCulture) : 1.05;
        var net = new ThresholdNetwork(layout, new WorldGeometry(256), long.Parse(args[0]));
        Tile t = layout.TileAt(x, z);
        Tile? was = layout.PreBalance?.TileAt(x, z);
        Console.WriteLine($"layout version {layout.Version} (new levels read {layout.ExpVersion}); {x},{z}: level {t.Level} under {t.Under}"
            + (was is { } w ? $"; pre-balance twin: level {w.Level} under {w.Under}" : "; no pre-balance twin"));
        string refusal = null;
        Passage p = kind == "walk" ? net.Walked(x, z, t, rel) : net.Used(x, z, kind, out refusal);
        if (p == null) { Console.WriteLine($"  {kind}: no passage" + (refusal != null ? $" (refusal {refusal})" : "")); return true; }
        var to = p.Find?.Invoke(p.Key);
        Console.WriteLine($"  {kind}: passage from {p.Source.X},{p.Source.Z} ({p.Message})"
            + (to is { } a ? $" to level {layout.LevelAt(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z))} at {a.X},{a.Z}" : " to nowhere found"));
        return true;
    }
}
