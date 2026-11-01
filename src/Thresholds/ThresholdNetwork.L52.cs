using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 52, "The Greenfield Campus"'s thresholds (experimental, kept as level 23; docs/design/experimental-levels/LINKS.md,
/// "Level 52"). Both ways in are doors you open and walk through, so both are two-way, and the ways out are those two, back:
///
/// <list type="bullet">
/// <item><b>A high school in the city</b> (Level 11, <see cref="WorldLayout.IsL52SchoolDoor"/>): its front doors open into the
/// lobby of a campus quad, just inside its front doors (<see cref="WorldLayout.IsL52QuadDoor"/>), on Marshall David Campus or
/// one beside it ("each entrant will land in the same building or one nearby"). Out through those doors is back on the
/// city's sidewalk in front of the school.</item>
/// <item><b>An EMERGENCY EXIT door in Level 4</b> (<see cref="WorldLayout.IsL52ExitDoor"/>): it opens into the corridor at the
/// end of a teaching block, just inside its end doors (<see cref="WorldLayout.IsL52WingDoor"/>), which lead back to the
/// office.</item>
/// </list>
///
/// The campus's own doors lead anywhere only once something has come in by them; until then they are only doors. The
/// rumoured ways (random doors to Level 53, noclipping in Marshall David to Level 556) are in the notes and the handbook
/// only. Salts 0x23C0-0x23FF.
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x23C0-0x23FF).</summary>
    private const ulong SaltL52Threshold = 0x23C0;

    /// <summary>A front door of a campus quad (the way back to a city high school); an end door of a teaching block (back to Level 4).</summary>
    public static readonly Func<Tile, bool> L52QuadDoor = WorldLayout.IsL52QuadDoor, L52WingDoor = WorldLayout.IsL52WingDoor;

    /// <summary>A city high school's front doors; Level 4's EMERGENCY EXIT door.</summary>
    public static readonly Func<Tile, bool> L52SchoolDoor = WorldLayout.IsL52SchoolDoor, L52ExitDoor = WorldLayout.IsL52ExitDoor;

    private Passage L52Walked(int x, int z, in Tile tile, double rel)
    {
        // Out through a campus door that something came in by: back where it came from. (Cheap first: only those doors)
        if (tile.Under is not (Unders.L52QuadDoor or Unders.L52WingDoor) || tile.Level != WorldLayout.Level52 || rel > 2.5) return null;
        var door = layout.FeatureOrigin(x, z, tile.Under == Unders.L52QuadDoor ? L52QuadDoor : L52WingDoor);
        if (!TryGet(door, out Link back)) return null;
        int to = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(back.X)), WorldLayout.MacroOf((int)Math.Floor(back.Z)));
        return new Passage
        {
            Source = door, TwoWay = true, Sound = "game:sounds/block/door",
            Message = to == 11 ? "backrooms:l52-back-city" : to == 4 ? "backrooms:l52-back-office" : null,
        };
    }

    private Passage L52Used(int x, int z, int level, string kind, ref string refusal)
    {
        if (level is not (11 or 4))
        {
            // (Our steel door anywhere else, if one was ever placed by hand, leads nowhere)
            if (kind == "l52-door") refusal = "locked";
            return null;
        }
        Tile here = layout.TileAt(x, z);
        if (level == 11 && L52SchoolDoor(here))
        {
            // Into the high school, and in through the front doors of a campus quad under a blue sky
            var door = layout.FeatureOrigin(x, z, L52SchoolDoor);
            return WithSound(new Passage
            {
                Source = door, Key = KeyOf(door, SaltL52Threshold + 1), Find = IntoL52Door(L52QuadDoor), ReturnFeature = L52QuadDoor, TwoWay = true,
                Message = "backrooms:l52-arrive-school",
            }, "game:sounds/block/door");
        }
        if (level == 4 && L52ExitDoor(here))
        {
            // Out by the emergency exit, and in at the end door of a teaching block
            var door = layout.FeatureOrigin(x, z, L52ExitDoor);
            return WithSound(new Passage
            {
                Source = door, Key = KeyOf(door, SaltL52Threshold + 2), Find = IntoL52Door(L52WingDoor), ReturnFeature = L52WingDoor, TwoWay = true,
                Message = "backrooms:l52-arrive-exit",
            }, "game:sounds/block/metaldoor");
        }
        if (kind == "l52-door") refusal = "locked";
        return null;
    }

    /// <summary>
    /// Arriving just inside one of the campus's doors (<paramref name="door"/>: a quad's front doors, a teaching block's end
    /// doors), on the floor of its lobby or corridor, on or near Marshall David Campus; else anywhere the level puts people.
    /// </summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL52Door(Func<Tile, bool> door) => key =>
        layout.FindArrival(WorldLayout.Level52, key, door, spot: WorldLayout.IsL52InsideDoorSpot) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z))
            : IntoL52()(key);

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL52(Func<Tile, bool> beside = null) => In(WorldLayout.Level52, beside);
}
