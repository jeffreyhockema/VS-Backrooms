namespace Backrooms.Worldgen;

/// <summary>
/// Vanilla touches for the indoor levels (0-6): the scalding sumps let into the floors of Level 5's boiler bays,
/// filled with vanilla's boiling water (it steams, warms and scalds by its own behaviours).
/// </summary>
public sealed partial class WorldGenerator
{
    private int boilingWaterId;

    private void InitInterior()
    {
        boilingWaterId = GameId("game:boilingwater-still-7", "game:water-still-7");
    }

    /// <summary>
    /// A sump (a <see cref="TileKind.Water"/> tile in Levels 1-5): the floor block itself is the water, one deep, over
    /// the soaked floor below (<see cref="BelowFloor"/>). Floor blocks stand all round it at the same height, so it never
    /// meets open air at its own level and stays put.
    /// </summary>
    private bool InteriorSump(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        if (rel != 0 || t.Kind != TileKind.Water || t.Level is < 1 or > 5) return false;
        fluid = t.Level == 5 ? boilingWaterId : waterId;
        return true;
    }
}
