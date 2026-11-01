using System;

namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 23's way in, in Level 37 (WorldLayout.Level23.Links.cs): a huge hollow tree of green bark (the Green
/// Giants' bark) growing up through the Poolrooms' tiles, floor and ceiling; its hollow dry underfoot (humus and leaf
/// litter on bark) and going up into the dark further than the room is high; its mouth three blocks high; round its foot its
/// roots crawling out over the tile and the tile broken up into earth and moss, and where it goes through the ceiling, roots
/// in the tile there too. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltL23Links = 0x2864;

    partial void L23EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        if (t.Level != WorldLayout.Poolrooms) return;
        if (layout.L23PoolTreeAt(gx, gz) is not { } tree) return;
        int bark = l23Bark[WorldLayout.L23BarkGreen];
        int bandTop = Geometry.BandTop - Geometry.FloorFor(WorldLayout.Poolrooms);
        switch (t.Under)
        {
            case Unders.L23PoolBark:
                id = bark;
                return;
            case Unders.L23PoolHollow or Unders.L23PoolSeedHollow or Unders.L23PoolMouth or Unders.L23PoolSeedMouth:
            {
                bool mouth = t.Under is Unders.L23PoolMouth or Unders.L23PoolSeedMouth;
                int top = mouth ? 3 : Math.Min(t.Height + 3, bandTop - 2);
                if (rel < 0 || rel > top) id = bark;
                else if (rel == 0)
                {
                    double u = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL23Links));
                    id = mouth ? (u < 0.5 ? l23Root : l23Humus) : u < 0.45 ? l23Humus : u < 0.8 ? l23Litter : l23Earth;
                }
                else id = 0;
                return;
            }
            case Unders.L23PoolRoots:
            {
                int dx = gx - tree.X, dz = gz - tree.Z;
                double d = Math.Sqrt(dx * dx + dz * dz), near = Math.Clamp((tree.R + 2.5 - d) / 2.5, 0, 1);
                double u = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL23Links + 1));
                int bed = -t.Depth;
                if (rel == bed)
                {
                    // The roots crawl out over the tile; between them the tile has broken up, more of it nearer the trunk
                    if (WorldLayout.L23PoolRootAt(tree, dx, dz)) id = l23Root;
                    else if (u < 0.55 * near) id = u < 0.3 * near ? l23Earth : l23Moss;
                }
                else if (rel == t.Height && u < 0.6 * near)
                    // Where it goes up through the ceiling, it has broken the tile there too
                    id = WorldLayout.L23PoolRootAt(tree, dx, dz) || u < 0.3 * near ? l23Root : l23Earth;
                return;
            }
        }
    }
}
