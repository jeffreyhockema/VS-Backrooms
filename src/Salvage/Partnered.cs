using System;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Salvage;

/// <summary>
/// A prop as big as the real thing, over several blocks (the camp tent two by two, the sleeping bag two long): one
/// model cut into a block per part (<c>tools/gen_detail.py</c>, multiblock_prop). Break any part and the whole thing
/// goes, and what it gives comes once, from its first part (the others give nothing; <c>tools/salvage.py</c>),
/// whichever part you hit. Only its own parts go: the same prop beside it, or turned another way, is left standing.
/// JSON properties: <c>parts</c>, the part names row by row from the front-left corner (as the model faces north, its
/// front to the north), and <c>width</c>, how many parts a row has.
/// </summary>
public class BlockBehaviorPartnered : BlockBehavior
{
    private string[] parts = Array.Empty<string>();
    private int width = 1;

    public BlockBehaviorPartnered(Block block) : base(block)
    {
    }

    public override void Initialize(JsonObject properties)
    {
        base.Initialize(properties);
        parts = properties["parts"].AsArray<string>() ?? parts;
        width = Math.Max(1, properties["width"].AsInt(1));
    }

    /// <summary>
    /// Where part (<paramref name="i"/> across, <paramref name="j"/> back) lies from the front-left part, for a prop facing
    /// <paramref name="side"/> (the same as <see cref="Worldgen.WorldLayout.PartTile"/>).
    /// </summary>
    private static (int X, int Z) Offset(string side, int i, int j) => side switch
    {
        "east" => (-j, i),
        "south" => (-i, -j),
        "west" => (j, -i),
        _ => (i, j),
    };

    public override void OnBlockBroken(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier, ref EnumHandling handling)
    {
        if (world.Side != EnumAppSide.Server) return;
        string side = block.Variant["side"];
        int self = Array.IndexOf(parts, block.Variant["part"]);
        if (self < 0 || side == null) return;
        (int sx, int sz) = Offset(side, self % width, self / width);
        // (As the block's own drops: none in creative)
        bool drops = byPlayer?.WorldData.CurrentGameMode != EnumGameMode.Creative;
        for (int n = 0; n < parts.Length; n++)
        {
            if (n == self) continue;
            (int px, int pz) = Offset(side, n % width, n / width);
            BlockPos at = pos.AddCopy(px - sx, 0, pz - sz);
            Block part = world.BlockAccessor.GetBlock(at);
            if (part.Code == null || part.Code.Domain != block.Code.Domain || part.FirstCodePart() != block.FirstCodePart()
                || part.Variant["part"] != parts[n] || part.Variant["side"] != side) continue;
            // A prop that straddles a claim's edge does not lose the half inside it to someone who may not build there
            if (byPlayer != null && !world.Claims.TryAccess(byPlayer, at, EnumBlockAccessFlags.BuildOrBreak)) continue;
            if (drops)
                foreach (ItemStack stack in part.GetDrops(world, at, byPlayer, dropQuantityMultiplier) ?? Array.Empty<ItemStack>())
                    world.SpawnItemEntity(stack, at.ToVec3d().Add(0.5, 0.5, 0.5));
            world.BlockAccessor.SetBlock(0, at);
        }
    }
}
