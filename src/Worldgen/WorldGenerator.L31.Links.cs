namespace Backrooms.Worldgen;

/// <summary>
/// Level 31, "Roller Rink"'s ways in and out, drawn (laid out in WorldLayout.Level31.Links.cs): the wooden door into the rink
/// in a wall of Level 2, 3 or 6 and the lobby's wooden door (<c>l31-door</c>, a varnished panel door; tools/gen_31_links.py),
/// and a lobby's revolving door (<c>l31-revolvingdoor</c>: Level 3999's drum of glass wings, its own threshold). This file is
/// the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>The wooden door's lower and upper halves by axis (0 facing north or south, 1 east or west); the revolving door's side, middle and top by facing.</summary>
    private readonly int[,] l31Door = new int[2, 2], l31Revolving = new int[3, 4];

    private void InitL31Links()
    {
        string[] parts = { "lower", "upper" }, axes = { "ns", "we" }, drum = { "side", "center", "top" };
        for (int k = 0; k < 2; k++)
            for (int a = 0; a < 2; a++) l31Door[k, a] = L31Block($"l31-door-{parts[k]}-{axes[a]}", k == 0 ? L31Block("housedoor-lower") : L31Block("housedoor-upper"));
        for (int f = 0; f < 4; f++)
            for (int k = 0; k < 3; k++) l31Revolving[k, f] = L31Block($"l31-revolvingdoor-{drum[k]}-{Sides[f]}", k == 1 ? l31Plain : 0);
    }

    /// <summary>A wooden door's block at a height above its floor (rel 1 and 2), or -1 above and below it.</summary>
    private int L31DoorPart(in Tile t, int rel) =>
        rel is 1 or 2 ? l31Door[rel - 1, t.Pier is ArchPier.North or ArchPier.South ? 0 : 1] : -1;

    /// <summary>A block of the level's own ways out and back on a wall tile: the lobby's wooden door, a revolving door (rel 1-3: the
    /// middle tile draws the whole drum at its foot, the rest is invisible collision); -1 for the wall's own.</summary>
    private int L31LinkBlock(in Tile t, int rel)
    {
        if (t.Under == Unders.L31LobbyDoor) return L31DoorPart(t, rel);
        if (t.Under != Unders.L31Revolving || rel is < 1 or > 3) return -1;
        int f = Facing(t.Pier);
        return rel > 1 ? l31Revolving[2, f] : t.Stack == 1 ? l31Revolving[1, f] : l31Revolving[0, f];
    }

    /// <summary>The wooden door into the rink in a wall of Level 2, 3 or 6: its two halves; the host's own wall round it.</summary>
    partial void L31EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        if (t.Under == Unders.L31HostDoor) id = L31DoorPart(t, rel);
    }
}
