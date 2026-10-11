using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 188, "The Courtyard of Windows"'s thresholds (kept as level 20; docs/new-levels/188-plan.md, LINKS.md round 2).
/// Climbing through a window is walking, so every window is two-way; a blind opened, the hatch, a Window's arm are not.
///
/// <list type="bullet">
/// <item><b>In.</b> A window where no window should be in Level 0 or Level 1, and Level Fun's one confetti window: climb in
/// and you climb down into the courtyard beside the window that shows where you came from, which leads back. The Hub's one
/// window (<see cref="Unders.HubWindow188"/>, the Hub's layout) likewise, beside the courtyard's Hub window.</item>
/// <item><b>Out.</b> The twelve ground-storey windows that show other places (Level 0, 1, 2, 4, 5, 6, 9, the Hub, Level
/// Fun): climb in at the sill (two-way, beside the matching window there where one is near, else a thin spot). A closed
/// window's blind opened from inside its room (<c>l188-blind-&lt;storey&gt;</c>, through Regions.L188System): taken,
/// one-way, to the place fixed for that window. The fire doors (one per upper storey): Level 1, 5, 4, 2, two-way. The
/// hatch in the deck: a fall into Level 37, one-way.</item>
/// </list>
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x20C0-0x20FF).</summary>
    private const ulong SaltL188Threshold = 0x20C0;

    /// <summary>A courtyard window of 188's on the ground storey that shows (and leads to) the given level.</summary>
    public static Func<Tile, bool> L188LinkWindowTo(int level) => t => t.Under == Unders.L188LinkWindow && t.Level == WorldLayout.Level188 && t.Detail == level;

    /// <summary>A window into 188 in another level, from the given host (0 Level 0, 1 Level 1, 3 Level Fun).</summary>
    public static Func<Tile, bool> L188EntranceIn(int host) => t => WorldLayout.IsL188Entrance(t, host) && t.Level != WorldLayout.Level188;

    /// <summary>The Hub's window into 188.</summary>
    public static readonly Func<Tile, bool> L188HubWindow = t => t.Under == Unders.HubWindow188 && t.Level == WorldLayout.Hub;

    /// <summary>A fire door of 188's (the way back for whoever comes in beside it).</summary>
    private static readonly Func<Tile, bool> L188FireDoor = t => t.Under == Unders.L188FireDoor && t.Level == WorldLayout.Level188;

    private Passage L188Walked(int x, int z, in Tile tile, double rel)
    {
        int level = tile.Level;
        switch (tile.Under)
        {
            case Unders.L188LinkWindow when level == WorldLayout.Level188 && rel >= 1.9 && rel < 3.5:
            {
                // Climbing in at the sill of a window onto another place
                int target = tile.Detail;
                var window = layout.FeatureOrigin(x, z, t => t.Under == Unders.L188LinkWindow && t.Level == WorldLayout.Level188);
                ulong key = KeyOf(window, SaltL188Threshold);
                Passage passage = target switch
                {
                    0 or 1 => BothWays(window, key, target, L188EntranceIn(target)),
                    WorldLayout.FunLevel => L188BothWays(window, key, L188IntoFunWindow(), L188EntranceIn(3)),
                    WorldLayout.Hub => L188BothWays(window, key, L188IntoHubWindow(), L188HubWindow),
                    5 or 2 => BothWays(window, key, target, PlainDoor),
                    _ => BothWays(window, key, target),
                };
                passage.Message = "backrooms:l188-window-in";
                passage.Sound = "game:sounds/effect/translocate-breakdimension";
                return passage;
            }
            case Unders.L188Entrance when level != WorldLayout.Level188 && rel >= 1.6 && rel < 3.5:
            {
                // A window where no window should be: in, beside the courtyard window that shows this level
                int host = tile.Detail & 15;
                var window = layout.FeatureOrigin(x, z, t => WorldLayout.IsL188Entrance(t));
                ulong key = KeyOf(window, SaltL188Threshold + 1);
                int shows = host == 3 ? WorldLayout.FunLevel : host;
                Passage passage = new Passage
                {
                    Source = window, Key = key, Find = IntoL188(L188LinkWindowTo(shows)), ReturnFeature = L188LinkWindowTo(shows), TwoWay = true,
                    Message = "backrooms:l188-window-arrive", Sound = "game:sounds/effect/translocate-breakdimension",
                };
                return passage;
            }
            case Unders.HubWindow188 when level == WorldLayout.Hub && rel >= 0.9 && rel < 3.5:
                return L188FromHub(x, z);
            case Unders.L188Hatch when level == WorldLayout.Level188 && rel < -1.5:
            {
                // Through the hatch in the deck: a long fall through the black, into warm water
                var hatch = layout.FeatureOrigin(x, z, t => t.Under == Unders.L188Hatch && t.Level == WorldLayout.Level188);
                Passage passage = OneWay(hatch, KeyOf(hatch, SaltL188Threshold + 4), WorldLayout.Poolrooms);
                passage.Message = "backrooms:l188-hatch-arrive";
                passage.Sound = "game:sounds/environment/largesplash1";
                return passage;
            }
        }
        return null;
    }

    /// <summary>The Hub's window into 188, climbed through (walked into, or used by hand from the tunnel).</summary>
    private Passage L188FromHub(int x, int z)
    {
        var window = layout.FeatureOrigin(x, z, L188HubWindow);
        return new Passage
        {
            Source = window, Key = KeyOf(window, SaltL188Threshold + 5), Find = IntoL188(L188LinkWindowTo(WorldLayout.Hub)),
            ReturnFeature = L188LinkWindowTo(WorldLayout.Hub), TwoWay = true,
            Message = "backrooms:l188-window-arrive", Sound = "game:sounds/effect/translocate-breakdimension",
        };
    }

    private static Passage L188BothWays((int X, int Z) source, ulong key, Func<ulong, (int X, int Z, double Height)?> find, Func<Tile, bool> back) =>
        new Passage { Source = source, Key = key, Find = find, ReturnFeature = back, TwoWay = true };

    /// <summary>Arriving in the Hub on the sidewalk in front of its window into 188 (there is one in the world).</summary>
    private Func<ulong, (int X, int Z, double Height)?> L188IntoHubWindow() => key =>
    {
        if (layout.HubWindowOf() is not { } w) return In(WorldLayout.Hub)(key);
        var (sx, sz) = WorldLayout.L188Step(w.Facing);
        int x = w.Left.X + sx, z = w.Left.Z + sz;
        return (x, z, layout.ArrivalHeight(x, z));
    };

    /// <summary>Arriving in Level Fun in the party room in front of its confetti window (there is one in the world).</summary>
    private Func<ulong, (int X, int Z, double Height)?> L188IntoFunWindow() => key =>
    {
        if (layout.L188FunWindow() is not { } w) return In(WorldLayout.FunLevel)(key);
        var (sx, sz) = WorldLayout.L188Step(w.Facing);
        int x = w.Left.X + sx, z = w.Left.Z + sz;
        return (x, z, layout.ArrivalHeight(x, z));
    };

    private Passage L188Used(int x, int z, int level, string kind, ref string refusal)
    {
        if (kind == "l188-hubwindow" && level == WorldLayout.Hub) return L188FromHub(x, z);
        if (level != WorldLayout.Level188) return null;
        Tile here = layout.TileAt(x, z);
        switch (kind)
        {
            case "elevator":
                // The lifts are dead
                refusal = "outoforder";
                return null;
            case "l188-fireexit":
            {
                int storey = here.Under == Unders.L188FireDoor ? here.Detail : 0;
                if (storey == 0) { refusal = "locked"; return null; }
                var door = (x, z);
                ulong key = KeyOf(door, SaltL188Threshold + 3);
                (int target, Func<Tile, bool> partner) = storey switch
                {
                    1 => (1, (Func<Tile, bool>)null),
                    2 => (5, PlainDoor),
                    3 => (4, (Func<Tile, bool>)null),
                    _ => (2, PlainDoor),
                };
                Passage passage = BothWays(door, key, target, partner);
                passage.Message = "backrooms:l188-fireexit";
                return WithSound(passage, "game:sounds/block/metaldoor");
            }
            case "l188-frontdoor":
                refusal = "locked";
                return null;
        }
        if (kind.StartsWith("l188-blind-") && int.TryParse(kind.Substring(11), out int s) && s >= 0 && s < WorldLayout.L188Storeys)
        {
            int bx = x - layout.L188BuildX0, bz = z - layout.L188BuildZ0;
            int wi = WorldLayout.L188WindowAt(bx, bz);
            if (wi < 0 || wi == WorldLayout.L188StairWindow || s == 0 && layout.L188LinkLevel(wi) >= 0)
            {
                refusal = "nowhere";
                return null;
            }
            // One threshold per storey's window: its source is the room tile s + 1 in from the window's left half
            var (left, _, facing) = WorldLayout.L188WindowTiles(wi);
            var (fx, fz) = WorldLayout.L188Step(facing);
            var source = (layout.L188BuildX0 + left.Bx - fx * (s + 1), layout.L188BuildZ0 + left.Bz - fz * (s + 1));
            int target = layout.L188BlindTarget(wi, s);
            return new Passage
            {
                Source = source, Key = KeyOf(source, SaltL188Threshold + 2), Find = In(target),
                Message = "backrooms:l188-taken-arrive", Sound = "game:sounds/effect/translocate-breakdimension",
            };
        }
        // Any other kind of the level's own leads nowhere (never on to the built-in doors)
        if (kind.StartsWith("l188-")) refusal = "nowhere";
        return null;
    }

    /// <summary>Somewhere to arrive in the level for a key (beside a tile matching <paramref name="beside"/>, where one can be found).</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL188(Func<Tile, bool> beside = null) => In(WorldLayout.Level188, beside);
}
