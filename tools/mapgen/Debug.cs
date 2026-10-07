using System.Reflection;
using Backrooms.Worldgen;
static class Debugger
{
    public static void Plan(WorldLayout layout, int gx, int gz)
    {
        int bx = Hashing.FloorDiv(gx - 9, 16), bz = Hashing.FloorDiv(gz - 9, 16);
        var m = typeof(WorldLayout).GetMethod("HallBlockPlan", BindingFlags.NonPublic | BindingFlags.Instance);
        var tiles = (Tile[])m.Invoke(layout, new object[] { bx, bz });
        Console.WriteLine($"block {bx},{bz} origin {bx * 16 + 9},{bz * 16 + 9}; hall at corners: " +
            string.Join(",", new[] { (0, 0), (13, 0), (0, 13), (13, 13) }.Select(c => IsHall(layout, bx * 16 + 9 + c.Item1, bz * 16 + 9 + c.Item2))));
        for (int v = 0; v < 14; v++)
        {
            var sb = new System.Text.StringBuilder();
            for (int u = 0; u < 14; u++)
            {
                var t = tiles[v * 14 + u];
                sb.Append(t.Kind switch { TileKind.Wall => '#', TileKind.Doorway => 'D', TileKind.Door => 'X', _ => t.Variant != 0 ? 'p' : t.Sealed ? '~' : '.' });
            }
            Console.WriteLine(sb);
        }
    }
    static bool IsHall(WorldLayout l, int gx, int gz)
    {
        var m = typeof(WorldLayout).GetMethod("IsHallAt", BindingFlags.NonPublic | BindingFlags.Instance);
        return (bool)m.Invoke(l, new object[] { gx, gz });
    }
}
