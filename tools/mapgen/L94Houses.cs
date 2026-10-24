using Backrooms.Worldgen;

/// <summary>l94houses: <c>mapgen &lt;seed&gt; &lt;cells&gt; l94houses</c> lists the front doors of Level 94's houses round the mountain (door position, whether the
/// house has a chimney, how many windows and what kind) and tallies them.</summary>
static class L94Houses
{
    public static void Run(WorldLayout layout, int n)
    {
        var cache = new Dictionary<(int, int), Tile[]>();
        Tile At(int x, int z)
        {
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            if (!cache.TryGetValue((mx, mz), out var t)) cache[(mx, mz)] = t = layout.BuildMacro(mx, mz);
            return t[WorldLayout.TileIndex(x - mx * 32, z - mz * 32)];
        }
        int size = n * 32, x0 = layout.MotionOriginX - size / 2, z0 = layout.MotionOriginZ - size / 2;
        int doors = 0, plain = 0, windows = 0, tall = 0, chimneys = 0, shown = 0;
        for (int z = z0; z < z0 + size; z++)
            for (int x = x0; x < x0 + size; x++)
            {
                Tile t = At(x, z);
                if (t.Level != WorldLayout.Motion) continue;
                if (t.Kind == TileKind.Wall && t.Variant is 1 or 2 && t.Pattern >= WallPattern.SidingWhite && t.Pattern <= WallPattern.Brick) { windows++; if (t.Stack >= WorldLayout.WinSash) tall++; }
                if (WorldLayout.IsChimney(t) && t.Kind == TileKind.Wall) chimneys++;
                if (t.Kind == TileKind.Door && t.Under is Unders.DollHouse or Unders.FloodedHouse) Console.WriteLine($"threshold {x},{z} {t.Under} pier {t.Pier}");
                if (t.Kind is TileKind.Door or TileKind.Doorway && (t.Stack & WorldLayout.DoorMark) != 0)
                {
                    doors++;
                    if (shown++ < 12) Console.WriteLine($"door {x},{z} kind {t.Kind} under {t.Under} stack {t.Stack} pier {t.Pier} ground {t.Height}");
                }
                else if (t.Kind == TileKind.Door && t.Under == 0 && t.Pattern != WallPattern.Backdrop) plain++;
            }
        Console.WriteLine($"doors with the mark {doors}, other Door tiles {plain}, house windows {windows} (tall {tall}), outside chimney stacks {chimneys}");
    }
}
