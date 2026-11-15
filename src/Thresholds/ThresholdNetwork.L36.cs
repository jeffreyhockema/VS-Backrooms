using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 36, "Airport"'s thresholds (experimental, kept as level 25; docs/design/experimental-levels/LINKS.md). This file is
/// the level's own. Salts 0x25C0-0x25FF.
///
/// In: a door under an airplane sign in a wall of the city (Level 11) or the Suburbs (Level 9), used: two-way, into the claim
/// hall beside one of the doors under the same sign in the baggage wall, which is its way back. Those doors are locked but for
/// the one somebody has come in by.
///
/// Out: a gate's flight (kind "l36-flight", asked by Regions.L36System when the plane lands, at the gate's jet-bridge door):
/// one-way, to the gate's own level of six, standing on open ground or a floor; a restroom sink overflowed, head under (kind
/// "l36-sink", asked by the sink when held): one-way, up in the Poolrooms.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>
    /// Whether the doors under an airplane sign in Levels 9 and 11 let anyone in. False from 0.701.0: Level 36 is experimental
    /// and not reachable in play (the user's decision, 2026-11-15); the doors are drawn as before (worldgen does not move) but
    /// stay locked, in every world, including one somebody already came in by. Its ways out still work for anyone inside, and
    /// the cheats (F7, /tp) still reach it. Set true to open it again.
    /// </summary>
    public static readonly bool L36Open = false;

    /// <summary>Hash salts for the level's thresholds start here (0x25C0-0x25FF).</summary>
    private const ulong SaltL36Threshold = 0x25C0;

    /// <summary>A door into the airport in Level 9 or 11, and a door in the baggage wall (each the other's way back).</summary>
    public static readonly Func<Tile, bool> L36AirportDoor = WorldLayout.IsL36AirportDoor, L36LandDoor = WorldLayout.IsL36LandDoor;

    // (Nothing of the level's is walked into: its ways are all used)
    private Passage L36Walked(int x, int z, in Tile tile, double rel) => null;

    private Passage L36Used(int x, int z, int level, string kind, ref string refusal)
    {
        switch (kind)
        {
            case "l36-airport" when level is 9 or 11:
            {
                // A door under an airplane sign in the city or the Suburbs: into the claim hall, beside a door like it in
                // the baggage wall, the way back (locked while the level is experimental)
                if (!L36Open) { refusal = "locked"; return null; }
                var door = layout.FeatureOrigin(x, z, L36AirportDoor);
                if (!L36AirportDoor(layout.TileAt(door.X, door.Z))) { refusal = "nowhere"; return null; }
                Passage passage = BothWays(door, KeyOf(door, SaltL36Threshold + 1), WorldLayout.Level36, L36LandDoor);
                passage.Find = IntoL36Landside();
                passage.Message = "backrooms:l36-arrive-door";
                return WithSound(passage, "game:sounds/block/door");
            }
            case "l36-airport" when level == WorldLayout.Level36:
            {
                // A door in the baggage wall: out again the way someone came in, else locked
                var door = layout.FeatureOrigin(x, z, L36LandDoor);
                if (TryGet(door, out _)) return new Passage { Source = door, TwoWay = true, Sound = "game:sounds/block/door", Message = "backrooms:l36-leave-door" };
                refusal = "locked";
                return null;
            }
            case "l36-flight":
            {
                // The plane at this jet-bridge door has landed: in the level its gate's screen names, always the same place
                if (level != WorldLayout.Level36 || layout.L36GateAt(x, z) is not { SupportGroup: false } gate) { refusal = "nowhere"; return null; }
                (int X, int Z) source = (gate.DoorX, gate.DoorZ);
                int to = WorldLayout.L36LevelOf(layout.L36FlightTo(gate));
                return new Passage { Source = source, Key = KeyOf(source, WorldLayout.L36FlightKeySalt), Find = L36Landing(to), Message = "backrooms:l36-landed" };
            }
            case "l36-sink":
            {
                // An overflowing restroom sink, head under: up in the Poolrooms (each sink always to the same place)
                if (level != WorldLayout.Level36) { refusal = "nowhere"; return null; }
                return new Passage
                {
                    Source = (x, z), Key = KeyOf((x, z), WorldLayout.L36SinkKeySalt), Find = In(WorldLayout.Poolrooms),
                    Message = "backrooms:l36-sink-arrive", Sound = "game:sounds/environment/mediumsplash",
                };
            }
        }
        return null;
    }

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL36(Func<Tile, bool> beside = null) => In(WorldLayout.Level36, beside);

    /// <summary>In the claim hall, off the belts, beside a door under an airplane sign in the baggage wall where one can be found.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL36Landside() => key =>
        layout.FindArrival(WorldLayout.Level36, key, L36LandDoor, spot: WorldLayout.IsL36LandsideSpot) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : null;

    /// <summary>
    /// Where a flight comes down: standing, on open ground or a floor of its level, never in water or a wall (the Poolrooms: a
    /// dry deck; the others their own arrival spots, which are all dry and open).
    /// </summary>
    private Func<ulong, (int X, int Z, double Height)?> L36Landing(int level) => level == WorldLayout.Poolrooms
        ? key => layout.FindArrival(WorldLayout.Poolrooms, key, spot: WorldLayout.IsL36DryPoolSpot) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : null
        : In(level);
}
