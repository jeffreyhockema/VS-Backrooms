namespace Backrooms.Worldgen;

/// <summary>
/// Level 36, "Airport"'s way in, drawn in the levels it is found in (WorldLayout.Level36.Links.cs): in a wall of Level 11 or 9,
/// a door (two blocks) under a backlit sign with an airplane on it, all facing out; above them the host's own wall goes on.
/// This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    partial void L36EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        if (t.Under != Unders.L36AirportDoor || t.Kind != TileKind.Wall || rel is < 1 or > 3) return;
        int f = Facing(t.Pier);
        id = rel == 1 ? l36AirDoor[f] : rel == 2 ? l36AirDoor[4 + f] : l36AirSign[f];
    }
}
