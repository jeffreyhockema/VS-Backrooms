using Backrooms.Worldgen;

/// <summary>
/// campcount [cellsPerLevel]: camp gear and Level 8 markers per level over the same sample of cells (rays from spawn, every
/// 8th step, up to cellsPerLevel cells a level, default 150), to compare before and after a change to camps or markers.
/// "gear" is tents, bedrolls, camp tents and sleeping bags; "impro" the improvised camp props (layout version 11).
/// </summary>
static class CampCount
{
    public static void Run(WorldLayout l, int smx, string[] args)
    {
        int cap = args.Length > 3 ? int.Parse(args[3]) : 150;
        var cells = new Dictionary<int, List<(int, int)>>();
        for (int a = 0; a < 360; a += 3)
        {
            double ang = a * Math.PI / 180;
            for (int r = 0; r < 1400; r += 8)
            {
                int mx = smx + (int)Math.Round(Math.Cos(ang) * r), mz = smx + (int)Math.Round(Math.Sin(ang) * r);
                int lv = l.LevelAt(mx, mz);
                if (!cells.TryGetValue(lv, out var list)) cells[lv] = list = new();
                if (list.Count < cap && !list.Contains((mx, mz))) list.Add((mx, mz));
            }
        }
        Console.WriteLine("level cells  tent bedroll camptent sleepbag | impro  lanterns | markers lamps");
        foreach (var kv in cells.OrderBy(k => k.Key))
        {
            int tent = 0, roll = 0, ct = 0, sb = 0, impro = 0, lan = 0, mk = 0, lamp = 0;
            foreach (var (mx, mz) in kv.Value)
                foreach (var t in l.BuildMacro(mx, mz))
                {
                    if (t.Kind != TileKind.Floor) continue;
                    switch (t.Variant)
                    {
                        case Props.Tent: tent++; break;
                        case Props.Bedroll: roll++; break;
                        case Props.CampTent: if (t.Stack == 0) ct++; break;
                        case Props.SleepingBag: if (t.Stack == 0) sb++; break;
                        case Props.Lantern: lan++; break;
                        case Props.MegMarker: mk++; break;
                        case Props.RoadLamp: lamp++; break;
                        case >= Props.ImprovFirst and <= Props.ImprovLast: impro++; break;
                    }
                }
            Console.WriteLine($"{kv.Key,5} {kv.Value.Count,5} {tent,5} {roll,7} {ct,8} {sb,8} | {impro,5} {lan,8} | {mk,7} {lamp,5}");
        }
    }
}
