using Backrooms.Worldgen;

/// <summary>
/// mapgen notesupply: ordinary notes a cell gives when every container in it is broken (sealed and torn boxes and the camp
/// props and desks), by level, from the drop tables as they were before the note tuning and as they are now, plus loose
/// notes per cell. Cells are sampled in a 9x9 block round several arrivals of each level. Crates (0.03 in Level 0 only now,
/// 0.02-0.03 in Levels 0-1 before) are left out.
/// </summary>
static class NoteSupply
{
    // (variant, old base drop, extra anywhere, new base drop, new Level 0 extra)
    static readonly (string Name, ushort Variant, double OldBase, double All, double NewBase, double NewNear)[] Furniture =
    {
        ("backpack", Props.Backpack, 0.5, 0, 0.25, 0.25),
        ("bedroll", Props.Bedroll, 0.12, 0.03, 0.06, 0.06),
        ("tent", Props.Tent, 0.5, 0, 0.25, 0.25),
        ("camptent", Props.CampTent, 0.55, 0, 0.275, 0.275),
        ("sleepingbag", Props.SleepingBag, 0.12, 0.03, 0.06, 0.06),
        ("filingcabinet", Props.FilingCabinet, 0.05, 0.01, 0.025, 0.025),
        ("writingdesk", Props.WritingDesk, 0.05, 0.01, 0.025, 0.025),
    };

    public static void Run(WorldLayout layout)
    {
        var seen = new HashSet<(int, int)>();
        var cells = new int[12]; var oldN = new double[12]; var newN = new double[12]; var loose = new double[12]; var folded = new double[12];
        var boxes = new double[12]; var camp = new double[12];
        for (int level = 0; level <= 11; level++)
            for (ulong k = 1; k <= 14; k++)
            {
                if (layout.FindArrival(level, k * 104729UL + 7) is not { } arr) continue;
                int cmx = WorldLayout.MacroOf(arr.X), cmz = WorldLayout.MacroOf(arr.Z);
                for (int dz = -4; dz <= 4; dz++)
                    for (int dx = -4; dx <= 4; dx++)
                    {
                        int mx = cmx + dx, mz = cmz + dz;
                        if (!seen.Add((mx, mz))) continue;
                        var tiles = layout.BuildMacro(mx, mz);
                        int l = tiles[0].Level; if (l > 11) continue;
                        cells[l]++;
                        bool near0 = l == 0, nearOld = l <= 1;
                        foreach (Tile t in tiles)
                        {
                            if (t.SupplyBox)
                            {
                                boxes[l]++;
                                if (t.Looted) { oldN[l] += 0.06 + (nearOld ? 0.06 : 0); newN[l] += 0.03 + (near0 ? 0.09 : 0); }
                                else { oldN[l] += 0.15 + (nearOld ? 0.10 : 0); newN[l] += 0.075 + (near0 ? 0.175 : 0); }
                                continue;
                            }
                            if (t.Kind != TileKind.Floor || t.Stack != 0) continue;
                            foreach (var p in Furniture)
                                if (t.Variant == p.Variant)
                                {
                                    camp[l]++;
                                    oldN[l] += p.OldBase + p.All; newN[l] += p.NewBase + p.All + (near0 ? p.NewNear : 0);
                                }
                        }
                        foreach (var s in layout.NoteSpots(mx, mz)) { if (s.Kind == "folded") folded[l]++; else loose[l]++; }
                    }
            }
        Console.WriteLine("ordinary notes per cell with every container broken (boxes and camp props; loose notes separate)");
        Console.WriteLine("level cells  boxes/cell furn/cell | old/cell new/cell | loose/cell folded-loose/cell");
        for (int l = 0; l < 12; l++)
            if (cells[l] > 0)
                Console.WriteLine($"L{l,-4} {cells[l],5}  {boxes[l] / cells[l],9:0.00} {camp[l] / cells[l],9:0.00} | {oldN[l] / cells[l],8:0.000} {newN[l] / cells[l],8:0.000} | {loose[l] / cells[l],9:0.000} {folded[l] / cells[l],9:0.000}");
    }
}
