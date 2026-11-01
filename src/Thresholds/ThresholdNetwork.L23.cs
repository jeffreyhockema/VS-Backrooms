using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level 23, "The Petrified Garden"'s thresholds (experimental, kept as level 28; docs/design/experimental-levels/LINKS.md,
/// the layout in WorldLayout.Level23.Links.cs). This file is the level's own.
/// <list type="bullet">
/// <item><b>In.</b> A huge hollow tree of green bark growing up through the tiles of Level 37: climb into its hollow and you
/// climb out of a hollow trunk in the Garden's forest. One-way (Wikidot).</item>
/// <item><b>Base Seedling's hollow tree</b>: climb up into it and you come out of the hollow tree in Level 37 that stands in
/// for the lore's Level 135 (our substitution), and that tree brings you back. Two-way: climbing is walking.</item>
/// <item><b>The Heart of Water</b>: down the well at the bottom of the pool, the reservoir takes you, and you come up in the
/// open sea of Level 7 (Wikidot). One-way: dived.</item>
/// </list>
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here (0x28C0-0x28FF).</summary>
    private const ulong SaltL23Threshold = 0x28C0;

    /// <summary>A Poolrooms tree's hollow and mouth: one of those that lead into the forest, and the one that is Base Seedling's way home.</summary>
    private static readonly Func<Tile, bool> L23PoolTree = t => t.Level == WorldLayout.Poolrooms && t.Under is Unders.L23PoolHollow or Unders.L23PoolMouth,
        L23PoolSeedTree = t => t.Level == WorldLayout.Poolrooms && t.Under is Unders.L23PoolSeedHollow or Unders.L23PoolSeedMouth;

    /// <summary>Base Seedling's hollow tree: its hollow and its doorway.</summary>
    private static readonly Func<Tile, bool> L23CampTree = t => t.Level == WorldLayout.Level23 && t.Under is Unders.L23SeedlingHollow or Unders.L23SeedlingDoor;

    private const string L23TreeSound = "backrooms:sounds/ambient/23/woodgroan";

    private Passage L23Walked(int x, int z, in Tile tile, double rel)
    {
        if (tile.Under < Unders.L23PoolBark || tile.Under > Unders.L23Well) return null;
        int level = tile.Level;
        if (level == WorldLayout.Poolrooms)
        {
            // Into the hollow of a tree in the Poolrooms (its floor is at the water's level): up through the dark inside it
            if (tile.Under is not (Unders.L23PoolHollow or Unders.L23PoolSeedHollow) || rel < -1 || rel > 2.5) return null;
            if (tile.Under == Unders.L23PoolSeedHollow)
            {
                var home = layout.FeatureOrigin(x, z, L23PoolSeedTree);
                return new Passage
                {
                    Source = home, Key = KeyOf(home, SaltL23Threshold + 1), Find = IntoL23Camp(), ReturnFeature = L23CampTree, TwoWay = true,
                    Message = "backrooms:l23-tree-camp", Sound = L23TreeSound,
                };
            }
            var tree = layout.FeatureOrigin(x, z, L23PoolTree);
            return new Passage { Source = tree, Key = KeyOf(tree, SaltL23Threshold), Find = IntoL23Hollow(), Message = "backrooms:l23-tree-in", Sound = L23TreeSound };
        }
        if (level != WorldLayout.Level23) return null;
        if (tile.Under == Unders.L23SeedlingHollow && rel < -tile.Depth + 2.5)
        {
            // Up Base Seedling's hollow tree, the camp's way home: out of the hollow tree in the Poolrooms that leads back
            var camp = layout.FeatureOrigin(x, z, L23CampTree);
            return new Passage
            {
                Source = camp, Key = KeyOf(camp, SaltL23Threshold + 2), Find = IntoL23PoolSeedTree(), ReturnFeature = L23PoolSeedTree, TwoWay = true,
                Message = "backrooms:l23-tree-home", Sound = L23TreeSound,
            };
        }
        if (tile.Under == Unders.L23Well && rel < -tile.Depth + 2)
        {
            // The bottom of the well in the Heart of Water's pool: the reservoir takes you, out into the sea of Level 7
            var well = layout.FeatureOrigin(x, z, t => t.Under == Unders.L23Well && t.Level == WorldLayout.Level23);
            return new Passage
            {
                Source = well, Key = KeyOf(well, SaltL23Threshold + 3), Find = IntoL23Sea(), Message = "backrooms:l23-well",
                Sound = "game:sounds/environment/largesplash1",
            };
        }
        return null;
    }

    private Passage L23Used(int x, int z, int level, string kind, ref string refusal) => null;

    /// <summary>An arrival finder in the level, beside a feature if one is given.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL23(Func<Tile, bool> beside = null) => In(WorldLayout.Level23, beside);

    /// <summary>Climbing out of a hollow trunk in the forest (any of them, by key), or anywhere in the forest if there is none.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL23Hollow() => key =>
        layout.L23HollowArrival(key) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : IntoL23()(key);

    /// <summary>Coming home to Base Seedling, in front of its hollow tree's doorway.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL23Camp() => key =>
        layout.L23SeedlingArrival(key) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : IntoL23()(key);

    /// <summary>Coming out of Base Seedling's tree in the Poolrooms, right outside its mouth.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL23PoolSeedTree() => key =>
        layout.L23SeedlingTreeArrival(key) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : In(WorldLayout.Poolrooms)(key);

    /// <summary>Coming up in the open sea of Level 7 (swimming, at the surface), or anywhere in Level 7 if no open water is found.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoL23Sea() => key =>
        layout.L23SeaArrival(key) is { } a ? (a.X, a.Z, 0.2) : In(7)(key);
}
