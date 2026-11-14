using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 31, "Roller Rink"'s thresholds (experimental, kept as level 24; docs/design/experimental-levels/LINKS.md, "Level 31";
/// laid out in WorldLayout.Level31.Links.cs). This file is the level's own.
/// <list type="bullet">
/// <item><b>In</b> (Wikidot, Fandom): a wooden door in a wall of Level 2, 3 or 6 with pop music playing faintly behind it
/// (kind <c>l31-door</c>). Walked through, so two-way: it opens in a lobby of the rink, beside the lobby's own wooden door,
/// which leads back to where you stood.</item>
/// <item><b>Out</b> (Fandom): the Revolving Door in the front of some lobbies (kind <c>l31-revolving</c>), to Level 9, 10 or 11,
/// each door always the same one; one-way. And stealing skates (Regions.L31System, <see cref="L31SkatesNoclip"/>; taking
/// the Coach's skates out of the level, ThresholdSystem.L31Redirect): you noclip to Level 0, without them; one-way.</item>
/// </list>
/// A lobby's wooden door that nobody has come in by is only a locked door.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x24C0-0x24FF).</summary>
    private const ulong SaltL31Threshold = 0x24C0;

    public static readonly Func<Tile, bool> L31HostDoor = WorldLayout.IsL31HostDoor, L31LobbyDoor = WorldLayout.IsL31LobbyDoor,
        L31Revolving = WorldLayout.IsL31Revolving;

    private Passage L31Walked(int x, int z, in Tile tile, double rel) => null;

    private Passage L31Used(int x, int z, int level, string kind, ref string refusal)
    {
        switch (kind)
        {
            case "l31-door" when level is 2 or 3 or 6 && L31HostDoor(layout.TileAt(x, z)):
            {
                // Through the wooden door, toward the music: into a lobby of the rink, beside its wooden door, the way back
                var door = layout.FeatureOrigin(x, z, L31HostDoor);
                Passage passage = BothWays(door, KeyOf(door, SaltL31Threshold + 1), WorldLayout.Level31, L31LobbyDoor);
                passage.Message = "backrooms:l31-door-arrive";
                return WithSound(passage, "game:sounds/block/door");
            }
            case "l31-door" when level == WorldLayout.Level31 && L31LobbyDoor(layout.TileAt(x, z)):
            {
                // A lobby's wooden door: back to where someone came in from, if anyone has; otherwise only a locked door
                var door = layout.FeatureOrigin(x, z, L31LobbyDoor);
                if (TryGet(door, out _))
                    return new Passage { Source = door, TwoWay = true, Message = "backrooms:l31-door-back", Sound = "game:sounds/block/door" };
                refusal = "locked";
                return null;
            }
            case "l31-door":
                refusal = "locked";
                return null;
            case "l31-revolving" when level == WorldLayout.Level31 && L31Revolving(layout.TileAt(x, z)):
                return L31RevolvingOut(layout, x, z);
            // (A world made before layout 16: a revolving door built at the pre-releases' rate, one lobby in 12, that the rate of
            // one in 48 dropped from the layout after its chunk was made, still turns as it did: WorldLayout.PreBalance. The
            // block used shows it is there, so no door is added)
            case "l31-revolving" when level == WorldLayout.Level31 && layout.PreBalance is { } old && L31Revolving(old.TileAt(x, z)):
                return L31RevolvingOut(old, x, z);
            case "l31-revolving":
                refusal = "nowhere";
                return null;
        }
        return null;
    }

    /// <summary>Round in the drum and out of the rink, to the same one of Levels 9, 10 and 11 every time (the door as <paramref name="by"/> lays it out).</summary>
    private Passage L31RevolvingOut(WorldLayout by, int x, int z)
    {
        var door = by.FeatureOrigin(x, z, L31Revolving);
        var (mx, mz) = L31MiddleOf(by, door);
        return new Passage
        {
            Source = door, Key = KeyOf(door, SaltL31Threshold + 2), Find = In(by.L31RevolvingTarget(mx, mz)),
            Message = "backrooms:l31-revolving-out", Sound = "backrooms:sounds/effect/3999/revolving",
        };
    }

    /// <summary>A revolving door's middle tile, from its origin (its three tiles run along x or along z, from the origin).</summary>
    private static (int X, int Z) L31MiddleOf(WorldLayout by, (int X, int Z) origin) =>
        L31Revolving(by.TileAt(origin.X + 1, origin.Z)) ? (origin.X + 1, origin.Z) : (origin.X, origin.Z + 1);

    /// <summary>
    /// Stealing skates (Fandom: "an immediate noclip to Level 0, without skates"): taken, one-way, from where the thief
    /// stands, into the Lobby. The skates are taken off them on the way (ThresholdSystem.L31Redirect).
    /// </summary>
    public Passage L31SkatesNoclip((int X, int Z) at) =>
        new Passage { Source = at, Key = KeyOf(at, SaltL31Threshold + 3), Find = In(0), Message = "backrooms:l31-skates-noclip" };

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL31(Func<Tile, bool> beside = null) => In(WorldLayout.Level31, beside);
}
