namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 37, the Poolrooms. Everything is the same white tile: floors, walls and ceilings. Water stands
/// over the floors (<see cref="Tile.Depth"/> deep, up to the level of the dry decks), ceilings are
/// <see cref="Tile.Height"/> above the water, and the only light is the glare of the slits in the walls.
/// </summary>
public sealed partial class WorldGenerator
{
    private int poolTileId, poolSunlitId, poolRedId, poolVoidId, poolDoorLowerId, poolDoorUpperId;
    private readonly int[] poolSlitIds = new int[4], poolArchIds = new int[4], poolRailIds = new int[4];

    private void InitPool()
    {
        poolTileId = Id("pooltile-plain");
        poolSunlitId = Id("pooltile-sunlit");
        poolRedId = Id("pooltile-red");
        poolVoidId = Id("pooltile-void");
        poolDoorLowerId = Id("pooldoor-lower");
        poolDoorUpperId = Id("pooldoor-upper");
        for (int f = 0; f < 4; f++)
        {
            poolSlitIds[f] = Id($"poolwall-slit-{Sides[f]}");
            poolArchIds[f] = Id($"poolwall-arch-{Sides[f]}");
            poolRailIds[f] = Id($"poolwall-rail-{Sides[f]}");
        }
        floorIds[(int)FloorKind.PoolTile] = poolTileId;
        floorIds[(int)FloorKind.PoolSunlit] = poolSunlitId;
        floorIds[(int)FloorKind.PoolRed] = poolRedId;
        floorIds[(int)FloorKind.PoolCoping] = Id("pooltile-coping");
    }

    /// <summary>The block at <paramref name="rel"/> above the water's surface of a Level 37 column.</summary>
    private int Level37Block(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        int tile = t.Zone == 1 ? poolRedId : poolTileId;
        if (t.Kind == TileKind.Door)
        {
            // A cyan door marked POOL, in a wall above the water
            return rel == 1 ? poolDoorLowerId : rel == 2 ? poolDoorUpperId : tile;
        }
        if (t.Kind != TileKind.Floor)
        {
            if (t.Pattern == WallPattern.PoolVoid) return poolVoidId;
            if (t.Pattern == WallPattern.Drywall) return rel is >= 1 and <= 3 ? officeWallId : tile;
            int facing = Facing(t.Pier);
            return t.Variant switch
            {
                PoolWalls.Slit when rel >= 2 && rel <= t.Height => poolSlitIds[facing],
                PoolWalls.Arch when rel >= 1 && rel <= 3 => poolArchIds[facing],
                PoolWalls.Rail when rel == 1 => poolRailIds[facing],
                _ => tile,
            };
        }

        int bed = -t.Depth;
        if (rel < bed) return tile;
        if (rel == bed) return t.Floor == FloorKind.OfficeCarpet ? floorIds[(int)FloorKind.OfficeCarpet] : floorIds[(int)t.Floor];
        // The black of a tunnel mouth closes in overhead
        if (t.Under == Unders.TunnelMouth && rel >= t.Height) return poolVoidId;
        if (rel >= t.Height) return t.Floor == FloorKind.OfficeCarpet ? officeCeilingId : tile;
        if (rel <= 0)
        {
            // Under water: a passage under a wall has tile over it from the surface up
            if (t.Under == Unders.PoolHole && rel >= 0) return tile;
            fluid = waterId;
            // A ladder climbs from the bottom to the rim; what the drowned left lies on the bottom; red sprouts glow
            if (t.Variant == Props.PoolLadder) return PropBlock(t);
            if (rel == bed + 1 && t.Variant is Props.Backpack or Props.BonePile or Props.RedSprout) return PropBlock(t);
            return 0;
        }
        // Above the water: the top of a ladder, and what lies on the dry decks
        if (rel == 1 && (t.Variant == Props.PoolLadder || t.Depth == 0 && t.Variant is Props.EpsomCrust or Props.LostThing)) return PropBlock(t);
        return 0;
    }
}
