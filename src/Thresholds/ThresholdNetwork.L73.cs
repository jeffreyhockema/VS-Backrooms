using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 73, "The Redlands"'s thresholds (experimental, kept as level 21; docs/design/experimental-levels/LINKS.md). Two ways in,
/// both one way, both taken by lingering rather than by a step (so Regions/L73System.Links.cs times them and asks for them here):
/// the Gloom in Level 9 (<see cref="L73Gloom"/>) and Level 6's deepest dark (<see cref="L73Dark"/>). One way out, also one way:
/// the north door in the castle's curtain wall, which only Coran opens, to Level 9 (walked into: <see cref="L73Walked"/>). This
/// file is the level's own.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x21C0-0x21FF).</summary>
    private const ulong SaltL73Threshold = 0x21C0;
    private const ulong SaltL73Gloom = SaltL73Threshold + 1, SaltL73Dark = SaltL73Threshold + 2, SaltL73Out = SaltL73Threshold + 3;

    /// <summary>The message shown on coming out of the north door (also how ThresholdSystem.L73MayPass knows the passage).</summary>
    public const string L73OutMessage = "backrooms:l73-out-arrive";

    /// <summary>The level the north door leads to: the Suburbs, where the Gloom is (Coran came back that way himself).</summary>
    public const int L73OutLevel = 9;

    /// <summary>The north door: someone who walks into it while it stands open (ThresholdSystem.L73MayPass) comes out in the Suburbs.</summary>
    private Passage L73Walked(int x, int z, in Tile tile, double rel)
    {
        if (tile.Level != WorldLayout.Level73 || tile.Zone != WorldLayout.L73Walls) return null;
        int u = x - layout.L73CastleX0, v = z - layout.L73CastleZ0;
        double c = rel - WorldLayout.L73Plateau;
        if (WorldLayout.L73PosternAt(u, v) == null || c < 0.5 || c > WorldLayout.L73PosternHeight) return null;
        return L73OutPassage();
    }

    /// <summary>The north door as a threshold (both its leaves are one: the west leaf stands for it).</summary>
    public Passage L73OutPassage()
    {
        (int X, int Z) door = layout.L73Postern;
        return new Passage { Source = door, Key = KeyOf(door, SaltL73Out), Find = In(L73OutLevel), Message = L73OutMessage };
    }

    private Passage L73Used(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL73(Func<Tile, bool> beside = null) => In(WorldLayout.Level73, beside);

    /// <summary>
    /// The Gloom someone is standing in (any of its tiles, in Level 9), as a threshold: out on the island, somewhere in sight of
    /// the castle, the same place every time for the same Gloom. Null if the tile is not the Gloom.
    /// </summary>
    public Passage L73Gloom(int x, int z)
    {
        if (!WorldLayout.IsL73Gloom(layout.TileAt(x, z))) return null;
        (int X, int Z) gloom = layout.L73GloomOrigin(x, z);
        return new Passage { Source = gloom, Key = KeyOf(gloom, SaltL73Gloom), Find = IntoL73(), Message = "backrooms:l73-arrive-gloom" };
    }

    /// <summary>
    /// Level 6's deepest dark in a cell, as a threshold (its north-west corner stands for it): out on the island, the same place
    /// every time for the same cell. Null if the cell is not one.
    /// </summary>
    public Passage L73Dark(int mx, int mz)
    {
        if (!layout.IsL73DarkCell(mx, mz)) return null;
        (int X, int Z) corner = (mx * WorldLayout.MacroSize, mz * WorldLayout.MacroSize);
        return new Passage { Source = corner, Key = KeyOf(corner, SaltL73Dark), Find = IntoL73(), Message = "backrooms:l73-arrive-dark" };
    }
}
