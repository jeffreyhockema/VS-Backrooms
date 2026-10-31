using System;
using System.Linq;
using Vintagestory.API.Common;

namespace Backrooms.Regions;

/// <summary>
/// Adds behaviours to blocks after the assets have loaded (<c>AssetsFinalize</c>, on both sides: a behaviour added now is
/// not sent to clients), for the blocks whose workings come from an attribute or a name rather than a JSON behaviour list.
/// One place for the Hub's and Level 3999's blocks, so both treat the block's behaviour lists the same way.
/// </summary>
internal static class BehaviorInjection
{
    /// <summary>Appends <paramref name="behavior"/> to the block's behaviours, unless it already has one of that very type.</summary>
    public static void Add(Block block, BlockBehavior behavior)
    {
        if (block.BlockBehaviors?.Any(b => b.GetType() == behavior.GetType()) == true) return;
        block.BlockBehaviors = (block.BlockBehaviors ?? Array.Empty<BlockBehavior>()).Append(behavior).ToArray();
    }

    /// <summary>
    /// Gives the block <paramref name="behavior"/> in place of the behaviours <paramref name="replaced"/> picks out (its plain
    /// threshold behaviour, which only knows the door as a way through). With <paramref name="inPlace"/>, the new one takes
    /// the old one's place in both of the block's behaviour lists (and is appended to the block behaviours when none matched);
    /// without it the old ones are dropped from both lists and the new one is appended to the block behaviours only.
    /// </summary>
    public static void Replace(Block block, BlockBehavior behavior, System.Func<CollectibleBehavior, bool> replaced, bool inPlace)
    {
        BlockBehavior[] behaviors = block.BlockBehaviors ?? Array.Empty<BlockBehavior>();
        CollectibleBehavior[] collectible = block.CollectibleBehaviors;
        if (!inPlace)
        {
            block.BlockBehaviors = behaviors.Where(b => !replaced(b)).Append(behavior).ToArray();
            if (collectible != null) block.CollectibleBehaviors = collectible.Where(b => !replaced(b)).ToArray();
            return;
        }
        bool swapped = false;
        for (int i = 0; i < behaviors.Length; i++)
            if (replaced(behaviors[i])) { behaviors[i] = behavior; swapped = true; }
        block.BlockBehaviors = swapped ? behaviors : behaviors.Append(behavior).ToArray();
        collectible ??= Array.Empty<CollectibleBehavior>();
        bool inCollectible = false;
        for (int i = 0; i < collectible.Length; i++)
            if (replaced(collectible[i])) { collectible[i] = behavior; inCollectible = true; }
        if (inCollectible) block.CollectibleBehaviors = collectible;
    }
}
