using Backrooms.Worldgen;

/// <summary>
/// Level 9's houses from layout version 5 (l9houses): how many have two storeys, a porch, a lamp; the street signs; and
/// whether every floor tile upstairs in a two-storey house can be walked to from the top of its stairs. Prints the
/// plan of the first two-storey house it finds, downstairs and up.
/// </summary>
static class L9Houses
{
    public static void Run(WorldLayout layout, int n)
    {
        var arrival = layout.FindArrival(9, 99991UL);
        if (arrival == null) { Console.WriteLine("no arrival"); return; }
        int x0 = arrival.Value.X - n * 16, z0 = arrival.Value.Z - n * 16, size = n * 32;
        Tile At(int x, int z) => layout.TileAt(x0 + x, z0 + z);
        int stairs = 0, porchPosts = 0, lamps = 0, lit = 0, steps = 0, signs = 0, guides = 0, upFloor = 0, upLost = 0, badStairs = 0;
        var guideWays = new Dictionary<ArchPier, int>();
        bool printed = false;
        for (int z = 1; z < size - 1; z++)
            for (int x = 1; x < size - 1; x++)
            {
                Tile t = At(x, z);
                if (t.Level != 9) continue;
                if (t.Variant == Props.SuburbSign) signs++;
                if (t.Variant == Props.SuburbSign && signs == 0) Console.WriteLine($"street-name sign at {x0 + x},{z0 + z}");
                if (t.Variant == Props.CitySign && guides == 0) Console.WriteLine($"guide sign at {x0 + x},{z0 + z}, arrow {t.Pier}");
                if (t.Variant == Props.CitySign) { guides++; guideWays[t.Pier] = guideWays.GetValueOrDefault(t.Pier) + 1; }
                if ((t.Height & WorldLayout.StoreyPorch) != 0)
                {
                    int parts = t.Height & ~WorldLayout.StoreyPorch;
                    if ((parts & WorldLayout.PorchPost) != 0) porchPosts++;
                    if ((parts & WorldLayout.PorchStep) != 0) steps++;
                    if ((parts & WorldLayout.PorchLamp) != 0) { lamps++; if ((parts & WorldLayout.PorchLampLit) != 0) lit++; }
                }
                // (houses at the edge of the area are left out: their upstairs runs off it)
                if (t.Stair != 4 || t.Height == 0 || x < 16 || z < 16 || x >= size - 16 || z >= size - 16) continue;
                stairs++;
                // The stairs below: steps 3, 2, 1 behind it, and the floor before the first
                int dx = t.Pier == ArchPier.East ? -1 : t.Pier == ArchPier.West ? 1 : 0, dz = t.Pier == ArchPier.South ? -1 : t.Pier == ArchPier.North ? 1 : 0;
                for (int s = 1; s <= 4; s++)
                {
                    Tile below = At(x + dx * s, z + dz * s);
                    bool ok = s < 4 ? below.Stair == 4 - s && below.Pier == t.Pier : below.Kind == TileKind.Floor && below.Stair == 0 && below.Variant == 0;
                    if (!ok) badStairs++;
                }
                // Upstairs, from the top step: everything on a floor code within 20 blocks
                var seen = new HashSet<(int, int)> { (x, z) };
                var q = new Queue<(int, int)>();
                q.Enqueue((x, z));
                bool Walk(Tile u) => u.Height == WorldLayout.StoreyDoorway
                    || WorldLayout.IsUpstairsFloor(u.Height) && ((u.Detail & 31) == 0 || u.Stair == 4);
                while (q.Count > 0)
                {
                    var (cx, cz) = q.Dequeue();
                    foreach (var (ax, az) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    {
                        int nx = cx + ax, nz = cz + az;
                        if (nx < 0 || nz < 0 || nx >= size || nz >= size || seen.Contains((nx, nz)) || !Walk(At(nx, nz))) continue;
                        seen.Add((nx, nz));
                        q.Enqueue((nx, nz));
                    }
                }
                int lostHere = 0;
                for (int vz = z - 14; vz <= z + 14; vz++)
                    for (int vx = x - 14; vx <= x + 14; vx++)
                    {
                        if (vx < 0 || vz < 0 || vx >= size || vz >= size) continue;
                        Tile u = At(vx, vz);
                        if (u.Level != 9 || !WorldLayout.IsUpstairsFloor(u.Height) || (u.Detail & 31) != 0) continue;
                        // (only this house's: the nearest stair top)
                        if (Math.Abs(vx - x) > 9 || Math.Abs(vz - z) > 9) continue;
                        upFloor++;
                        if (!seen.Contains((vx, vz))) { upLost++; lostHere++; if (Environment.GetEnvironmentVariable("L9LOST") == "1") Console.WriteLine($"  lost {vx - x},{vz - z}: height {u.Height} detail {u.Detail} kind {u.Kind}"); }
                    }
                if (!printed && (lostHere > 0 || Environment.GetEnvironmentVariable("L9LOST") != "1"))
                {
                    printed = true;
                    Console.WriteLine($"two-storey house, top of its stairs at {x0 + x},{z0 + z} (climbing {t.Pier}), {lostHere} tiles upstairs out of reach");
                    for (int pz = z - 13; pz <= z + 13; pz++)
                    {
                        var down = new System.Text.StringBuilder();
                        var up = new System.Text.StringBuilder();
                        for (int px = x - 10; px <= x + 10; px++)
                        {
                            Tile p = At(px, pz);
                            down.Append(p.Kind switch
                            {
                                TileKind.Wall => p.Variant is 1 or 2 ? 'w' : '#', TileKind.Doorway => 'D', TileKind.Door => 'X', TileKind.Bars => '|',
                                _ => p.Stair > 0 ? (char)('0' + p.Stair) : (p.Height & WorldLayout.StoreyPorch) != 0 ? 'o' : p.Variant != 0 ? 'p' : '.',
                            });
                            if (seen.Contains((px, pz)) && Environment.GetEnvironmentVariable("L9LOST") == "1") { up.Append('+'); continue; }
                            up.Append(p.Height switch
                            {
                                WorldLayout.StoreyOuter => 'W', WorldLayout.StoreyOuterBlank => '#', WorldLayout.StoreyWall => '#', WorldLayout.StoreyDoorway => 'D',
                                WorldLayout.StoreyHole => 'O', WorldLayout.StoreyLightOff or WorldLayout.StoreyLightOn => (p.Detail & 31) != 0 ? 'P' : 'L',
                                WorldLayout.StoreyFloor => p.Stair == 4 ? '4' : (p.Detail & 31) != 0 ? 'p' : '.',
                                _ => ' ',
                            });
                        }
                        Console.WriteLine($"{down}   {up}");
                    }
                }
            }
        Console.WriteLine($"{n}x{n} cells round a Level 9 arrival: {stairs} two-storey houses (stairs wrong in {badStairs} places), " +
                          $"{upFloor} open floor tiles upstairs, {upLost} not reachable from the stairs");
        Console.WriteLine($"porch posts {porchPosts}, porch steps {steps}, lamps by doors {lamps} ({lit} lit), street-name signs {signs}, " +
                          $"guide signs {guides} ({string.Join(", ", guideWays.Select(k => $"{k.Key} {k.Value}"))})");
    }
}
