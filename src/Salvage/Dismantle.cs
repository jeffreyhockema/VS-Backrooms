using System;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Salvage;

/// <summary>
/// Furniture that can be taken apart carefully. Broken with anything, a desk or a sofa gives its lumber and cloth as
/// ever (<c>tools/salvage.py</c>); broken with a saw in hand (a hammer, for the metal pieces: the <c>tool</c> property), it comes away whole, and can be set down again facing
/// you. It is how a player furnishes a base from what the Backrooms left. Pieces with a <c>side</c> (turned to the four
/// directions) or an <c>axis</c> (we or ns) variant are set down turned to face the player; the one carried is the
/// block's north (or we) form, as the game's own horizontal-orientable blocks do.
/// </summary>
public class BlockBehaviorDismantle : BlockBehavior
{
    public BlockBehaviorDismantle(Block block) : base(block)
    {
    }

    private string Group => block.Variant != null && block.Variant.ContainsKey("side") ? "side"
        : block.Variant != null && block.Variant.ContainsKey("axis") ? "axis" : null;

    private Block Carried(IWorldAccessor world)
    {
        string group = Group;
        if (group == null) return block;
        string value = group == "side" ? "north" : "we";
        return world.GetBlock(BlockCodes.WithVariant(block, group, value)) ?? block;
    }

    // Wooden and cloth pieces come away under a saw (the default); metal ones are unbolted with a hammer
    // ({ "name": "BackroomsDismantle", "properties": { "tool": "hammer" } }, from tools/salvage.py)
    private EnumTool tool = EnumTool.Saw;

    public override void Initialize(JsonObject properties)
    {
        base.Initialize(properties);
        string name = properties?["tool"].AsString(null);
        if (name != null && Enum.TryParse(name, true, out EnumTool parsed)) tool = parsed;
    }

    private bool Sawing(IPlayer byPlayer)
    {
        ItemSlot slot = byPlayer?.InventoryManager?.ActiveHotbarSlot;
        return slot?.Itemstack?.Collectible?.GetTool(slot) == tool;
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, ref float dropQuantityMultiplier, ref EnumHandling handled)
    {
        if (!Sawing(byPlayer)) return null;
        handled = EnumHandling.PreventDefault;
        return new[] { new ItemStack(Carried(world), 1) };
    }

    public override ItemStack OnPickBlock(IWorldAccessor world, BlockPos pos, ref EnumHandling handled)
    {
        handled = EnumHandling.PreventDefault;
        return new ItemStack(Carried(world), 1);
    }

    public override bool TryPlaceBlock(IWorldAccessor world, IPlayer byPlayer, ItemStack itemstack, BlockSelection blockSel, ref EnumHandling handling, ref string failureCode)
    {
        string group = Group;
        if (group == null) return false;
        handling = EnumHandling.PreventDefault;
        BlockFacing facing = Block.SuggestedHVOrientation(byPlayer, blockSel)[0];
        string value = group == "side" ? facing.Code : facing.Axis == EnumAxis.Z ? "we" : "ns";
        Block turned = world.GetBlock(BlockCodes.WithVariant(block, group, value)) ?? block;
        if (!turned.CanPlaceBlock(world, byPlayer, blockSel, ref failureCode)) return false;
        turned.DoPlaceBlock(world, byPlayer, blockSel, itemstack);
        return true;
    }
}
