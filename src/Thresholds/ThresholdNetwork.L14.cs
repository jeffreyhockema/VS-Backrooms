using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 14, "The Hospital"'s thresholds (experimental, kept as level 29; docs/design/experimental-levels/LINKS.md, "Level 14,
/// the Hospital"; WorldLayout.Level14.Links.cs lays them out). Every one is one-way. This file is the level's own.
///
/// <list type="bullet">
/// <item><b>In:</b> the EMERGENCY EXIT door in a Lobby wall of Level 0 (kind <c>l14-exit</c>; Fandom: "a rare emergency exit
/// door found in Level 0") and the door marked MEDICAL CENTER in a medical bay's wall in Level 15 (kind <c>l14-medical</c>;
/// Fandom 15): each opens on a reception room ("all of Level 14's entrants will first arrive" there), its stained-glass
/// revolving door behind you showing nothing. There is no way back through either.</item>
/// <item><b>Out:</b> the futuristic door (kind <c>l14-future</c>; Fandom 14): a lit main hall of Level 15, beside a
/// reinforced door that does not open, as Level 15's other ways in. The red exit door (kind <c>l14-red</c>; Fandom 14): a start
/// room of Level !, the door slamming behind you, as Level !'s other ways in. The floor that gives way (walked onto; our
/// invention, LINKS.md): a fall out of the sky onto the Redlands, Level 73 (ThresholdSystem.L14.cs sees to the fall).</item>
/// </list>
/// The arrows on the floor to the main exit (Level 130), the glowing window (777), too far in (16), the equipment (268), the
/// teddy bear (14.1), the torture chambers (4.4), and the ways in from 13, 130, 39 and 0.01 are rumours (notes, handbook).
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x29C0-0x29FF).</summary>
    private const ulong SaltL14Threshold = 0x29C0;

    /// <summary>The message on falling through the floor that gives way (also how ThresholdSystem.L14 knows the passage).</summary>
    public const string L14CollapseMessage = "backrooms:l14-collapse-arrive";

    /// <summary>The feet of someone standing on the floor (rel 1), or just over it: the sagging floor takes them.</summary>
    public const double L14CollapseTripRel = 1.6;

    /// <summary>How far over the Redlands' ground someone who fell through is put down, to fall the rest of the way.</summary>
    public const double L14CollapseDrop = 8;

    private static readonly Func<Tile, bool> L14Collapse = t => WorldLayout.IsL14Collapse(t);

    private Passage L14Walked(int x, int z, in Tile tile, double rel)
    {
        if (rel >= L14CollapseTripRel || tile.Level != WorldLayout.Level14) return null;
        if (WorldLayout.IsL14Collapse(tile)) return L14Fall(layout, x, z);
        // (A world made before layout 16: a floor that gives way laid at the pre-releases' rate, one wing in 112, and dropped
        // by the rate of one in 448 after its chunk was made, still gives way: WorldLayout.PreBalance. ThresholdSystem.L14MayPass
        // lets it through only where the sagging floor's block is there, so none is added where it was never built)
        return layout.PreBalance is { } old && WorldLayout.IsL14Collapse(old.TileAt(x, z)) ? L14Fall(old, x, z) : null;
    }

    /// <summary>Whether a tile is a floor that gives way, by the layout or (a world made before layout 16) by its <see cref="WorldLayout.PreBalance"/> twin.</summary>
    public bool L14CollapseAt(int x, int z) =>
        WorldLayout.IsL14Collapse(layout.TileAt(x, z)) || layout.PreBalance is { } old && WorldLayout.IsL14Collapse(old.TileAt(x, z));

    /// <summary>The floor giving way under someone standing on a sagging tile: one way, out of the sky onto the Redlands. The patch is one threshold.</summary>
    private Passage L14Fall(WorldLayout by, int x, int z)
    {
        var patch = by.FeatureOrigin(x, z, L14Collapse);
        return new Passage
        {
            Source = patch, Key = KeyOf(patch, SaltL14Threshold + 5), Message = L14CollapseMessage,
            Find = key => IntoL73()(key) is { } a ? (a.X, a.Z, a.Height + L14CollapseDrop) : null,
        };
    }

    private Passage L14Used(int x, int z, int level, string kind, ref string refusal)
    {
        if (!kind.StartsWith("l14-", StringComparison.Ordinal)) return null;
        Tile here = layout.TileAt(x, z);
        switch (kind)
        {
            case "l14-exit" when level == 0 && WorldLayout.IsL14ExitDoor(here):
                return new Passage
                {
                    Source = (x, z), Key = KeyOf((x, z), SaltL14Threshold + 1), Find = IntoL14(),
                    Message = "backrooms:l14-arrive", Sound = "game:sounds/block/metaldoor",
                };
            // (In a world made before layout 16, also a door built at the pre-releases' rate, one wing in 64, that the rate of one
            // in 256 dropped from the layout after its chunk was made: WorldLayout.PreBalance; the block used shows it is there)
            case "l14-medical" when level == WorldLayout.Level15 && (WorldLayout.IsL14MedDoor(here)
                || layout.PreBalance is { } old && WorldLayout.IsL14MedDoor(old.TileAt(x, z))):
                return new Passage
                {
                    Source = (x, z), Key = KeyOf((x, z), SaltL14Threshold + 2), Find = IntoL14(),
                    Message = "backrooms:l14-arrive", Sound = "game:sounds/effect/translocate-breakdimension",
                };
            case "l14-future" when level == WorldLayout.Level14 && WorldLayout.IsL14FutureDoor(here):
                // Into a lit main hall of Level 15, beside one of its doors that do not open
                return L15In((x, z), SaltL14Threshold + 3, "backrooms:l14-future-arrive", "game:sounds/effect/translocate-breakdimension");
            case "l14-red" when level == WorldLayout.Level14 && WorldLayout.IsL14RedDoor(here):
                // Into a start room of Level ! (the lane is settled on arrival, ThresholdSystem.RunRedirect); the door slams behind you
                return new Passage
                {
                    Source = (x, z), Key = KeyOf((x, z), SaltL14Threshold + 4), Find = IntoRun(),
                    Message = "backrooms:run-arrive", Sound = RunSlamSound,
                };
            case "l14-collapse" when level == WorldLayout.Level14 && WorldLayout.IsL14Collapse(here):
                // (No block has this kind: it is for the dev command /backrooms wayback l14-collapse x z, to go through the floor headless)
                return L14Fall(layout, x, z);
        }
        // Anything else of the level's own (a door set down by hand, out of its place) leads nowhere
        refusal = "nowhere";
        return null;
    }

    /// <summary>An arrival finder in the level (a reception room: WorldLayout.IsL14ArrivalSpot), beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL14(Func<Tile, bool> beside = null) => In(WorldLayout.Level14, beside);
}
