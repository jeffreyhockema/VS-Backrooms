using Backrooms.Worldgen;
using static Backrooms.Worldgen.WorldLayout;

/// <summary>
/// elevsides [level ...]: every elevator round a level's arrivals (Levels 3, 4, 5, 11, Fun and 3999 by default), and
/// what stands beside it along its wall: a wall (as it should), the corner of the room (tucked against a side wall) or
/// an opening (a doorway or a corridor's floor right beside the doors). With DUMP=1, a plan round the first elevator
/// of each level: E the elevator, # wall, D doorway, X another door, . floor, p a prop.
/// </summary>
static class ElevSides
{
    static bool IsElevator(in Tile t) =>
        t.Kind == TileKind.Door && t.Pattern is WallPattern.Elevator or WallPattern.L3999Elevator
        || t.Kind == TileKind.Wall && t.Pattern == WallPattern.FunElevator;

    static bool Open(in Tile t) => t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.ArchDoor or TileKind.Water or TileKind.Pit;

    public static void Run(WorldLayout layout, string[] args, int n)
    {
        var levels = args.Length > 3 ? args.Skip(3).Select(int.Parse).ToArray() : new[] { 3, 4, 5, 11, FunLevel, Level3999 };
        bool dump = Environment.GetEnvironmentVariable("DUMP") == "1";
        foreach (int level in levels)
        {
            var seen = new HashSet<(int, int)>();
            var cache = new Dictionary<(int, int), Tile[]>();
            Tile At(int x, int z)
            {
                int mx = MacroOf(x), mz = MacroOf(z);
                if (!cache.TryGetValue((mx, mz), out var c)) cache[(mx, mz)] = c = layout.BuildMacro(mx, mz);
                return c[TileIndex(x - mx * 32, z - mz * 32)];
            }
            int groups = 0, good = 0, corner = 0, opening = 0;
            var examples = new List<string>();
            (int X, int Z)? first = null;
            var cornerAt = new List<(int X, int Z)>();
            for (ulong k = 1; k <= 3; k++)
            {
                var a = layout.FindArrival(level, k * 99991UL);
                if (a == null) continue;
                int cx = MacroOf(a.Value.X), cz = MacroOf(a.Value.Z);
                for (int mz = cz - n / 2; mz < cz + n / 2; mz++)
                    for (int mx = cx - n / 2; mx < cx + n / 2; mx++)
                    {
                        if (layout.LevelAt(mx, mz) != level) continue;
                        for (int i = 0; i < 1024; i++)
                        {
                            int x = mx * 32 + i % 32, z = mz * 32 + i / 32;
                            Tile t = At(x, z);
                            if (!IsElevator(t) || seen.Contains((x, z))) continue;
                            // Its front: the open side; where both are open (a door through a wall), the way it faces
                            var open = new List<(int Dx, int Dz)>();
                            foreach (var (dx, dz) in new[] { (0, -1), (1, 0), (0, 1), (-1, 0) })
                                if (Open(At(x + dx, z + dz))) open.Add((dx, dz));
                            if (open.Count == 0) continue;
                            (int Dx, int Dz) facing = t.Pier switch { ArchPier.North => (0, -1), ArchPier.East => (1, 0), ArchPier.South => (0, 1), _ => (-1, 0) };
                            var f = open.Count > 1 && open.Contains(facing) ? facing : open[0];
                            // The run of elevator tiles along the wall
                            var (ax, az) = (f.Dz != 0 ? 1 : 0, f.Dx != 0 ? 1 : 0);
                            int lo = 0, hi = 0;
                            while (IsElevator(At(x + ax * (lo - 1), z + az * (lo - 1)))) lo--;
                            while (IsElevator(At(x + ax * (hi + 1), z + az * (hi + 1)))) hi++;
                            for (int s = lo; s <= hi; s++) seen.Add((x + ax * s, z + az * s));
                            groups++;
                            first ??= (x, z);
                            string worst = "wall";
                            foreach (int s in new[] { lo - 1, hi + 1 })
                            {
                                int bx = x + ax * s, bz = z + az * s;
                                Tile b = At(bx, bz);
                                string side = Open(b) || b.Kind == TileKind.Door ? "opening" : At(bx + f.Dx, bz + f.Dz).Kind == TileKind.Wall ? "corner" : "wall";
                                if (side == "opening" || side == "corner" && worst == "wall") worst = side;
                            }
                            if (worst == "wall") good++;
                            else if (worst == "corner")
                            {
                                corner++;
                                if (cornerAt.Count < 3) cornerAt.Add((x + ax * lo, z + az * lo));
                            }
                            else
                            {
                                opening++;
                                if (examples.Count < 6) examples.Add($"{x + ax * lo},{z + az * lo} ({hi - lo + 1} wide, facing {(f.Dx, f.Dz)})");
                            }
                        }
                    }
            }
            Console.WriteLine($"Level {DisplayNumber(level)} ({level}): {groups} elevators; wall on both sides {good}, in a corner {corner}, beside an opening {opening}"
                + (examples.Count > 0 ? "; e.g. " + string.Join(", ", examples) : ""));
            // (DUMPAT=x,z: the plan round that place instead)
            if (Environment.GetEnvironmentVariable("DUMPAT") is string da && da.Split(',') is { Length: 2 } xz) first = (int.Parse(xz[0]), int.Parse(xz[1]));
            if (cornerAt.Count > 0) Console.WriteLine("  in a corner, e.g. " + string.Join(", ", cornerAt));
            foreach (var e in dump ? (first is { } e0 ? new[] { e0 } : Array.Empty<(int X, int Z)>()).Concat(cornerAt.Take(1)) : Enumerable.Empty<(int X, int Z)>())
            {
                Console.WriteLine($"  plan round {e.X},{e.Z}:");
                for (int z = e.Z - 8; z <= e.Z + 8; z++)
                {
                    var sb = new System.Text.StringBuilder("    ");
                    for (int x = e.X - 14; x <= e.X + 14; x++)
                    {
                        Tile t = At(x, z);
                        sb.Append(IsElevator(t) ? 'E' : t.Kind switch
                        {
                            TileKind.Wall => '#', TileKind.Doorway => 'D', TileKind.Door => 'X', TileKind.Water => '~', TileKind.Bars => '|',
                            TileKind.Floor => t.Variant != 0 ? 'p' : '.', _ => '?',
                        });
                    }
                    Console.WriteLine(sb);
                }
            }
        }
    }
}
