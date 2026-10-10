using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Notes;

/// <summary>
/// A note someone left lying on the floor (placed where a story puts one: <see cref="NoteSystem"/>'s spots).
/// Right-click picks it up as a wanderer's note of its kind; breaking it drops the same.
/// </summary>
public class BlockLooseNote : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.Side != EnumAppSide.Server) return true;
        string kind = Variant["kind"] ?? "door";
        Item item = world.GetItem(new AssetLocation("backrooms", kind == "folded" ? "wanderernote-folded" : "wanderernote-" + kind));
        if (item == null) return false;
        var stack = new ItemStack(item);
        if (!byPlayer.InventoryManager.TryGiveItemstack(stack, true))
            world.SpawnItemEntity(stack, blockSel.Position.ToVec3d().Add(0.5, 0.2, 0.5));
        world.BlockAccessor.SetBlock(0, blockSel.Position);
        world.PlaySoundAt(new AssetLocation("game:sounds/block/cloth"), blockSel.Position.X + 0.5, blockSel.Position.Y, blockSel.Position.Z + 0.5, byPlayer, true, 8);
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer) => new[]
    {
        new WorldInteraction { ActionLangCode = "backrooms:blockhelp-takenote", MouseButton = EnumMouseButton.Right },
    };
}
