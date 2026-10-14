using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms;

/// <summary>
/// The game's HorizontalOrientable behaviour for a block with a hyphen in its base code and a <c>facing</c> variant.
/// The game's own rebuilds every code it needs (the north block to pick or drop, the block facing the player to
/// place, the rotated and flipped blocks) from the first code part, so for l3999-neonlamp-magenta-north it looked for
/// a block called l3999-north: looking at a lamp or a plush crashed the client, and neither could be placed.
/// </summary>
public class BlockBehaviorOrientable : BlockBehaviorHorizontalOrientable
{
    public BlockBehaviorOrientable(Block block) : base(block)
    {
        if (block.Variant.ContainsKey("facing")) variantCode = "facing";
    }

    private Block Facing(IWorldAccessor world, string facing) => world.BlockAccessor.GetBlock(BlockCodes.WithVariant(block, variantCode, facing)) ?? block;

    public override bool TryPlaceBlock(IWorldAccessor world, IPlayer byPlayer, ItemStack itemstack, BlockSelection blockSel, ref EnumHandling handling, ref string failureCode)
    {
        handling = EnumHandling.PreventDefault;
        BlockFacing[] facings = Block.SuggestedHVOrientation(byPlayer, blockSel);
        Block oriented = Facing(world, facings[0].Code);
        if (!oriented.CanPlaceBlock(world, byPlayer, blockSel, ref failureCode)) return false;
        oriented.DoPlaceBlock(world, byPlayer, blockSel, itemstack);
        return true;
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, ref float dropQuantityMultiplier, ref EnumHandling handled)
    {
        if (!handleDrop) return null;
        handled = EnumHandling.PreventDefault;
        if (drop?.ResolvedItemstack != null) return new[] { drop.ResolvedItemstack.Clone() };
        var stack = new ItemStack(Facing(world, dropBlockFace), 1);
        stack.StackSize = GameMath.RoundRandom(world.Rand, stack.StackSize * dropQuantityMultiplier);
        return stack.StackSize <= 0 ? System.Array.Empty<ItemStack>() : new[] { stack };
    }

    public override ItemStack OnPickBlock(IWorldAccessor world, BlockPos pos, ref EnumHandling handled)
    {
        handled = EnumHandling.PreventDefault;
        if (drop != null) return drop.ResolvedItemstack?.Clone();
        return new ItemStack(Facing(world, dropBlockFace), 1);
    }

    public override AssetLocation GetRotatedBlockCode(int angle, ref EnumHandling handled)
    {
        handled = EnumHandling.PreventDefault;
        BlockFacing facing = BlockFacing.FromCode(block.Variant[variantCode]) ?? BlockFacing.NORTH;
        return BlockCodes.WithVariant(block, variantCode, BlockFacing.HORIZONTALS_ANGLEORDER[GameMath.Mod(facing.HorizontalAngleIndex - angle / 90, 4)].Code);
    }

    public override AssetLocation GetHorizontallyFlippedBlockCode(EnumAxis axis, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        BlockFacing facing = BlockFacing.FromCode(block.Variant[variantCode]) ?? BlockFacing.NORTH;
        return facing.Axis == axis ? BlockCodes.WithVariant(block, variantCode, facing.Opposite.Code) : block.Code;
    }
}
