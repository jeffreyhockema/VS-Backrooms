using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 15, "Futuristic Halls"'s thresholds (experimental, kept as level 27; docs/design/experimental-levels/LINKS.md). The
/// level is "extremely hard to get into and out of": every way is one-way, and rare. This file is the level's own.
///
/// <list type="bullet">
/// <item><b>In.</b> The small reinforced door in the immense white wall across Level 10's fields, and the steel door in a wall
/// of Level 3 with white light under it (its handle gives you a shock): used, each comes out in a lit main hall of Level 15
/// beside a reinforced door that does not open (<see cref="WorldLayout.L15SealedArrival"/>).</item>
/// <item><b>The doors that do not open.</b> Locked, always; so is the gateway until its ESCAPE panel is pressed.</item>
/// <item><b>Out.</b> The gateway the ESCAPE panel rolls up (walked into, or used once open): Level 3. The pane with a street's
/// light behind it (broken, or climbed through once broken): Level 11, on a sidewalk. The office's staircase down: Level 4,
/// at the foot of a stairwell's flight up where one is near, as if you had come down it.</item>
/// </list>
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x27C0-0x27FF).</summary>
    private const ulong SaltL15Threshold = 0x27C0;

    private static bool L15Part(Tile t, ushort under) => t.Under == under && t.Level == WorldLayout.Level15;

    private Passage L15Walked(int x, int z, in Tile tile, double rel)
    {
        if (tile.Level != WorldLayout.Level15) return null;
        switch (tile.Under)
        {
            // Into the gateway once it has rolled up (it can only be stood in then)
            case Unders.L15Gateway when rel is >= 0.5 and < 3.5:
                return L15Gateway(x, z);
            // Climbing through the pane once it is broken (on its sill)
            case Unders.L15Window when rel is >= 1.9 and < 3.5:
                return L15Window(x, z);
            // Down the office's stairs, out of sight of the room
            case Unders.L15Stairs when rel < -1.5:
            {
                var stairs = layout.FeatureOrigin(x, z, t => L15Part(t, Unders.L15Stairs));
                return new Passage
                {
                    Source = stairs, Key = KeyOf(stairs, SaltL15Threshold + 5), Find = In(4, L4FlightUpFirst),
                    Message = "backrooms:l15-stairs-arrive",
                };
            }
        }
        return null;
    }

    private Passage L15Gateway(int x, int z)
    {
        var gate = layout.FeatureOrigin(x, z, t => L15Part(t, Unders.L15Gateway));
        Passage passage = OneWay(gate, KeyOf(gate, SaltL15Threshold + 3), 3);
        passage.Message = "backrooms:l15-gateway-arrive";
        passage.Sound = "game:sounds/effect/translocate-breakdimension";
        return passage;
    }

    private Passage L15Window(int x, int z)
    {
        var pane = layout.FeatureOrigin(x, z, t => L15Part(t, Unders.L15Window));
        Passage passage = OneWay(pane, KeyOf(pane, SaltL15Threshold + 4), 11);
        passage.Message = "backrooms:l15-window-arrive";
        passage.Sound = "game:sounds/block/glass";
        return passage;
    }

    private Passage L15Used(int x, int z, int level, string kind, ref string refusal)
    {
        if (!kind.StartsWith("l15-")) return null;
        Tile here = layout.TileAt(x, z);
        switch (kind)
        {
            case "l15-walldoor" when level == 10 && here.Under == Unders.L15WallDoor10:
                return L15In((x, z), SaltL15Threshold + 1, "backrooms:l15-wall-arrive", "game:sounds/block/metaldoor");
            case "l15-l3door" when level == 3 && here.Under == Unders.L15Door3:
                return L15In((x, z), SaltL15Threshold + 2, "backrooms:l15-l3door-arrive", "game:sounds/effect/translocate-breakdimension");
            case "l15-gateway" when level == WorldLayout.Level15 && here.Under == Unders.L15Gateway:
                return L15Gateway(x, z);
            case "l15-window" when level == WorldLayout.Level15 && here.Under == Unders.L15Window:
                return L15Window(x, z);
            case "l15-sealed" or "l15-gatewayshut":
                refusal = "locked";
                return null;
        }
        // Anything else of the level's own leads nowhere
        refusal = "nowhere";
        return null;
    }

    /// <summary>A way in from outside: into a lit main hall, beside one of the doors that do not open (or anywhere lit, failing that).</summary>
    private Passage L15In((int X, int Z) door, ulong salt, string message, string sound) => new Passage
    {
        Source = door, Key = KeyOf(door, salt), Message = message, Sound = sound,
        Find = key => layout.L15SealedArrival(key) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : IntoL15()(key),
    };

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL15(Func<Tile, bool> beside = null) => In(WorldLayout.Level15, beside);
}
