namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 14, "The Hospital" (experimental, kept as level 29), laid out in WorldLayout.Level14.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Scaffolding only: plain concrete floor, walls and ceiling, a fluorescent light
/// every eight blocks. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>The level's block ids (called from the constructor): none of its own yet.</summary>
    private void InitL14()
    {
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level14Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int ceiling = WorldGeometry.RoomHeight + 1;
        if (rel <= 0 || rel > ceiling) return concreteId;
        if (t.Kind != TileKind.Floor) return rel < ceiling ? concreteWallId : concreteId;
        if (rel < ceiling) return 0;
        return (gx & 7) == 4 && (gz & 7) == 4 ? lightOnId : concreteCeilingId;
    }
}
