namespace Backrooms.Worldgen;

/// <summary>
/// The experimental levels' ways in, laid out in the other levels (docs/design/experimental-levels/LINKS.md). Each level marks
/// its own entrances in its own partial (<c>partial void L31Entrances</c> and so on, in its own file), with its own salts,
/// so nothing else in the host level moves; this file only calls them, once per cell, in a fixed order.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>
    /// Whether the experimental levels' entrances in other levels are laid out (always, but for the harness's check that
    /// nothing else moved: mapgen turns it off when BACKROOMS_NO_EXP_ENTRANCES=1; the library never reads the environment).
    /// </summary>
    internal static bool ExpEntrances = true;

    /// <summary>Whether a tile is already one of the experimental levels' entrances (their Unders are all past 255).</summary>
    public static bool IsExpEntrance(in Tile t) => t.Under >= 256 && t.Level <= Level188;

    // Each level's own: mark its entrances in this cell of a host level (b.Level is the host), on tiles still free.
    // Unimplemented ones compile away.
    partial void L15Entrances(Builder b, int mx, int mz);
    partial void L36Entrances(Builder b, int mx, int mz);
    partial void L52Entrances(Builder b, int mx, int mz);
    partial void L120Entrances(Builder b, int mx, int mz);
    partial void L31Entrances(Builder b, int mx, int mz);
    partial void L23Entrances(Builder b, int mx, int mz);
    partial void BasementEntrances(Builder b, int mx, int mz);
    partial void L73Entrances(Builder b, int mx, int mz);
    partial void L47Entrances(Builder b, int mx, int mz);
    partial void L14Entrances(Builder b, int mx, int mz);

    /// <summary>
    /// The experimental levels' entrances in a cell of one of the levels 0 to 20, after the level has laid the cell out
    /// and before its walls are lined and its doorways cleared. The order is the precedence where two could want the same
    /// tile: the earlier wins, and a later one skips a tile <see cref="IsExpEntrance"/> already claims. (Level 47's dead
    /// trees in Level 10 come just after Level 15's white wall there; Level 14's emergency exits in Level 0 come last,
    /// after the Basement's cracks: LINKS.md.)
    /// </summary>
    private void MarkExpEntrances(Builder b, int mx, int mz)
    {
        if (!ExpEntrances || b.Level > Level188) return;
        L15Entrances(b, mx, mz);
        L47Entrances(b, mx, mz);
        L36Entrances(b, mx, mz);
        L52Entrances(b, mx, mz);
        L120Entrances(b, mx, mz);
        L31Entrances(b, mx, mz);
        L23Entrances(b, mx, mz);
        BasementEntrances(b, mx, mz);
        L73Entrances(b, mx, mz);
        L14Entrances(b, mx, mz);
    }
}
