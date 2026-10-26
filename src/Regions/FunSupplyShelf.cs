using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// Level Fun's party-supply shelf: the game's typed container, which picks and drops itself by rebuilding its code
/// from the first code part. With a hyphen in the base name that found no block, and looking at a shelf crashed the
/// client (the block-info HUD asks for the pick stack). This picks the right block, and gives the JSON drops where the
/// shelf itself is not to drop.
/// </summary>
public class BlockFunSupplyShelf : BlockGenericTypedContainer
{
    public override ItemStack OnPickBlock(IWorldAccessor world, BlockPos pos)
    {
        var stack = new ItemStack(world.GetBlock(BlockCodes.WithVariant(this, "side", "east")) ?? this, 1);
        string type = (world.BlockAccessor.GetBlockEntity(pos) as BlockEntityGenericTypedContainer)?.type ?? Attributes?["defaultType"].AsString("shelf") ?? "shelf";
        stack.Attributes.SetString("type", type);
        return stack;
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier = 1f)
    {
        bool self = Attributes?["drop"]?[GetType(world.BlockAccessor, pos)]?.AsBool(false) == true;
        if (self) return new[] { OnPickBlock(world, pos) };
        var drops = new List<ItemStack>();
        if (Drops != null)
            foreach (BlockDropItemStack drop in Drops)
                // (Class 5: its food and drink thinned like every other block's, Salvage.ScarcitySystem.ClassScale)
                if (drop.GetNextItemStack(dropQuantityMultiplier * (Salvage.ScarcitySystem.IsFood(drop.ResolvedItemstack?.Collectible) ? Salvage.ScarcitySystem.ClassScale(world, pos.X, pos.Z) : 1f)) is { } stack) drops.Add(stack);
        return drops.ToArray();
    }
}
