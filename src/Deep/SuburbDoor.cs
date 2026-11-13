using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Deep;

/// <summary>
/// A Suburbs house's front or back door (from layout version 9; <c>suburbdoor-{closed|open|locked}-{hinge}-{lower|upper}-{side}</c>,
/// tools/gen_suburbs.py): right-click either half to open or shut both, swinging in on its hinges. A locked one rattles
/// and stays shut (a pry bar forces it, as every locked door; <see cref="Salvage.PrySystem"/>), unless a way back is written onto
/// it (the door you arrive beside from a city rowhouse): that one opens onto where you came from, and no pry bar breaks it.
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
        if (!world.Claims.TryAccess(byPlayer, pos, EnumBlockAccessFlags.Use)) return true;
        string state = block.Variant["state"], part = block.Variant["part"];
        if (state == "locked")
        {
            // The way back of a city rowhouse's front door (or a doll's house of Level 94) is written onto the locked door you
            // arrive beside: that one opens, onto where you came from (ThresholdNetwork, kind "suburbdoor")
            if (byPlayer is IServerPlayer traveller && world.Api is ICoreServerAPI sapi
                && sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>() is { } thresholds
                && thresholds.LeadsSomewhere(pos, Thresholds.ThresholdNetwork.SuburbDoorKind))
            {
                thresholds.Use(traveller, pos, Thresholds.ThresholdNetwork.SuburbDoorKind);
                return true;
            }
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
        // (By variant, so a door whose code has a hyphen in its first part, Level 14's l14-door, swaps too)
        Block to = world.GetBlock(here.CodeWithVariant("state", state));
        if (to == null) return;
        world.BlockAccessor.ExchangeBlock(to.BlockId, pos);
        world.BlockAccessor.MarkBlockDirty(pos);
    }
}
