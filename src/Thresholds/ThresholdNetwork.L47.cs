using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 47, "The Adderwood"'s thresholds (experimental, kept as level 30; docs/design/experimental-levels/LINKS.md, the
/// layout in WorldLayout.Level47.Links.cs). This file is the level's own.
/// <list type="bullet">
/// <item><b>In.</b> An ancient dead tree in Level 10's fields: step into its hollow and you noclip out of a dead tree's hollow in
/// the Adderwood (Wikidot: "the hollows of dead trees appear to be especially prone"; the host is ours). One-way.</item>
/// <item><b>Out to Level 10.</b> Some of the Adderwood's dead trees' hollows: step in and you come out in Level 10 beside its own
/// ancient dead tree. One-way.</item>
/// <item><b>Out to Level 23.</b> A green giant's hollow: climb in and you come out of a hollow trunk in the Petrified Garden
/// (Wikidot 23: "huge hollow green-barked trees in Levels 37 and 47"; Level 23's own finder). One-way.</item>
/// </list>
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x30C0-0x30FF).</summary>
    private const ulong SaltL47Threshold = 0x30C0;

    private const string L47NoclipSound = "backrooms:sounds/ambient/47/shift1";

    private static readonly Func<Tile, bool> L47Tree10Hollow = t => t.Level == 10 && t.Under == Unders.L47Tree10Hollow,
        L47DeadHollowTile = t => t.Level == WorldLayout.Level47 && t.Under == Unders.L47DeadHollow,
        L47GreenHollowTile = t => t.Level == WorldLayout.Level47 && t.Under == Unders.L47GreenHollow;

    private Passage L47Walked(int x, int z, in Tile tile, double rel)
    {
        if (tile.Under < Unders.L47First || tile.Under > Unders.L47Last) return null;
        if (tile.Level == 10)
        {
            // Into the ancient dead tree's hollow in Level 10's fields
            if (tile.Under != Unders.L47Tree10Hollow || rel < -0.5 || rel > 3) return null;
            var tree = layout.FeatureOrigin(x, z, L47Tree10Hollow);
            return new Passage { Source = tree, Key = KeyOf(tree, SaltL47Threshold), Find = IntoL47Hollow(), Message = "backrooms:l47-in", Sound = L47NoclipSound };
        }
        if (tile.Level != WorldLayout.Level47 || rel < tile.Height - 0.5 || rel > tile.Height + 3) return null;
        if (tile.Under == Unders.L47DeadHollow)
        {
            var tree = layout.FeatureOrigin(x, z, L47DeadHollowTile);
            return new Passage { Source = tree, Key = KeyOf(tree, SaltL47Threshold + 1), Find = IntoL47Tree10(), Message = "backrooms:l47-out10", Sound = L47NoclipSound };
        }
        if (tile.Under == Unders.L47GreenHollow)
        {
            var giant = layout.FeatureOrigin(x, z, L47GreenHollowTile);
            return new Passage
            {
                Source = giant, Key = KeyOf(giant, SaltL47Threshold + 2), Find = IntoL23Hollow(), Message = "backrooms:l47-out23",
                Sound = "backrooms:sounds/ambient/23/woodgroan",
            };
        }
        return null;
    }

    private Passage L47Used(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL47(Func<Tile, bool> beside = null) => In(WorldLayout.Level47, beside);

    /// <summary>Coming out of a dead tree's hollow in the Adderwood (in front of its mouth), or anywhere in the forest if none is found.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL47Hollow() => key =>
        layout.L47HollowArrival(key) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : IntoL47()(key);

    /// <summary>Coming out in Level 10 beside one of its ancient dead trees, or anywhere in Level 10 if there is none.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL47Tree10() => key =>
        layout.L47Tree10Arrival(key) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : In(10)(key);
}
