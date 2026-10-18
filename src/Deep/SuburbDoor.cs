using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Deep;

/// <summary>
/// A Suburbs house's front or back door (from layout version 9; <c>suburbdoor-{closed|open|locked}-{hinge}-{lower|upper}-{side}</c>,
/// tools/gen_suburbs.py): right-click either half to open or shut both, swinging in on its hinges. A locked one rattles
/// and stays shut (a pry bar forces it, as every locked door; <see cref="Salvage.PrySystem"/>).
/// </summary>
public class BlockBehaviorSuburbDoor : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorSuburbDoor(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        if (block.Variant["state"] == "locked") return System.Array.Empty<WorldInteraction>();
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-suburbdoor", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server) return true;
        BlockPos pos = blockSel.Position;
        string state = block.Variant["state"], part = block.Variant["part"];
        if (state == "locked")
        {
            (byPlayer as IServerPlayer)?.SendIngameError("backrooms-suburbdoor", Lang.Get("backrooms:suburbdoor-locked"));
            world.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8);
            return true;
        }
        string next = state == "open" ? "closed" : "open";
        Swap(world, pos, next);
        BlockPos other = part == "lower" ? pos.UpCopy() : pos.DownCopy();
        Block half = world.BlockAccessor.GetBlock(other);
        if (half.Code?.Domain == "backrooms" && half.FirstCodePart() == block.FirstCodePart() && half.Variant["part"] != part) Swap(world, other, next);
        world.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 12);
        return true;
    }

    /// <summary>Puts the door at a position into another state, keeping its hinge, half and side.</summary>
    private static void Swap(IWorldAccessor world, BlockPos pos, string state)
    {
        Block here = world.BlockAccessor.GetBlock(pos);
        string path = $"{here.FirstCodePart()}-{state}-{here.Variant["hinge"]}-{here.Variant["part"]}-{here.Variant["side"]}";
        Block to = world.GetBlock(new AssetLocation("backrooms", path));
        if (to == null) return;
        world.BlockAccessor.ExchangeBlock(to.BlockId, pos);
        world.BlockAccessor.MarkBlockDirty(pos);
    }
}
