using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 120, "Broken Servos"'s thresholds (experimental, kept as level 26; docs/design/experimental-levels/LINKS.md). Both are
/// doors, used, never walked into (WorldLayout.Level120.Links.cs lays them out):
///
/// <list type="bullet">
/// <item><b>In:</b> the door marked SERVER ROOM in Level 4's offices (Wikidot: a "Server Room" door in Level 4.3, which Level
/// 4 stands in for), kind <c>l120-serverroom</c>: it opens on a server room of Level 120, beside one of that level's doors
/// back, and that door becomes its way back. Two-way: you walked through it.</item>
/// <item><b>Out:</b> the doors in the server rooms and the Pitch-Black Hallways (Wikidot: "doors ... back to Level 4.3"),
/// kind <c>l120-door</c>: each opens on Level 4 beside a locked office door, one-way (it is only an office door on that side,
/// and locked), unless it is a SERVER ROOM door's way back, when it leads back to the corridor in front of that door.</item>
/// </list>
/// The smashed arcade screen of Level 25 and noclipping into Level 70 are rumours (notes, handbook): neither level is in this mod.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x26C0-0x26FF).</summary>
    private const ulong SaltL120Threshold = 0x26C0;

    private static readonly Func<Tile, bool> L120ServerDoor = t => WorldLayout.IsL120ServerDoor(t);
    private static readonly Func<Tile, bool> L120ExitDoor = t => WorldLayout.IsL120ExitDoor(t);

    private Passage L120Walked(int x, int z, in Tile tile, double rel) => null;

    private Passage L120Used(int x, int z, int level, string kind, ref string refusal)
    {
        switch (kind)
        {
            case "l120-serverroom":
            {
                if (level != 4 || !L120ServerDoor(layout.TileAt(x, z))) { refusal = "locked"; return null; }
                // Into a server room, beside a door back: that door is the way back
                var door = layout.FeatureOrigin(x, z, L120ServerDoor);
                return new Passage
                {
                    Source = door, Key = KeyOf(door, SaltL120Threshold + 1), Find = IntoL120(L120ExitDoor), ReturnFeature = L120ExitDoor, TwoWay = true,
                    Message = "backrooms:l120-serverroom-arrive", Sound = "game:sounds/block/metaldoor",
                };
            }
            case "l120-door":
            {
                if (level != WorldLayout.Level120 || !L120ExitDoor(layout.TileAt(x, z))) { refusal = "locked"; return null; }
                // Back to the offices, out of a locked office door; or, the way back of a SERVER ROOM door, back to it
                var door = layout.FeatureOrigin(x, z, L120ExitDoor);
                return new Passage
                {
                    Source = door, Key = KeyOf(door, SaltL120Threshold + 2), Find = In(4, PlainDoor),
                    Message = "backrooms:l120-door-arrive", Sound = "game:sounds/block/metaldoor",
                };
            }
        }
        return null;
    }

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL120(Func<Tile, bool> beside = null) => In(WorldLayout.Level120, beside);
}
