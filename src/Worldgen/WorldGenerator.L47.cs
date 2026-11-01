namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 47, "The Adderwood" (experimental, kept as level 30), laid out in WorldLayout.Level47.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Scaffolding only: a plain concrete floor under the open sky, the rim a concrete wall
/// <see cref="L47RimTop"/> blocks high. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>The level's block ids (called from the constructor): none of its own yet.</summary>
    private void InitL47()
    {
    }

    /// <summary>How high the placeholder rim wall stands above the floor.</summary>
    private const int L47RimTop = 12;

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor: open sky over the floor.</summary>
    private int Level47Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel <= 0) return concreteId;
        if (t.Kind != TileKind.Floor) return rel <= L47RimTop ? concreteWallId : 0;
        return 0;
    }
}
