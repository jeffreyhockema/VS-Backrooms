using Backrooms.Worldgen;

/// <summary>
/// conduitmap [radius]: Level 1's ceiling conduit round the first Level 1 arrival, drawn from above, and a tally of what each
/// run ends against. '=' conduit that goes on, 'o' a capped end, 'T' a junction-box end, 'X' a block closed at both ends,
/// '#' wall, 'b' beam, 'L' light, '+' door, '.' floor. The ends are the ones <see cref="WorldLayout.ConduitEnds"/> picks
/// for the generator.
/// </summary>
static class ConduitMap
{
    public static void Run(WorldLayout layout, int radius)
    {
        var a = layout.FindArrival(1, 99991UL);
        if (a == null) { Console.WriteLine("no arrival"); return; }
        int cx = a.Value.X, cz = a.Value.Z;
        var tally = new SortedDictionary<string, int>();
        for (int z = cz - radius; z <= cz + radius; z++)
        {
            var line = new System.Text.StringBuilder();
            for (int x = cx - 2 * radius; x <= cx + 2 * radius; x++)
            {
                Tile t = layout.TileAt(x, z);
                char c;
                if (t.Pipe is Pipes.ConduitX or Pipes.ConduitZ && t.Kind == TileKind.Floor)
                {
                    var (lo, hi) = WorldLayout.ConduitEnds(layout.TileAt, x, z, out string why);
                    c = lo == 0 && hi == 0 ? '=' : lo != 0 && hi != 0 ? 'X' : (lo != 0 ? lo : hi) == WorldLayout.ConduitBox ? 'T' : 'o';
                    tally[why] = tally.GetValueOrDefault(why) + 1;
                }
                else c = t.Kind switch
                {
                    TileKind.Wall or TileKind.ArchWindow => '#',
                    TileKind.Doorway or TileKind.Door or TileKind.ArchDoor => '+',
                    _ => t.Beam ? 'b' : t.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit or CeilingKind.LightOff or CeilingKind.LightFlicker or CeilingKind.LightWarm ? 'L' : '.',
                };
                line.Append(c);
            }
            Console.WriteLine(line + $"  z={z}");
        }
        foreach (var kv in tally) Console.WriteLine($"{kv.Value,6}  {kv.Key}");
    }
}
