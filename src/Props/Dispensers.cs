using System.Text;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Props;

/// <summary>Registers vending machines and water coolers that still dispense Almond Water.</summary>
public class DispenserSystem : ModSystem
{
    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockClass("BackroomsDispenser", typeof(BlockDispenser));
        api.RegisterBlockEntityClass("BackroomsDispenser", typeof(BlockEntityDispenser));
    }
}

/// <summary>Using the block hands the player one bottle of Almond Water, while stock lasts.</summary>
public class BlockDispenser : Block
{
    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.BlockAccessor.GetBlockEntity(blockSel.Position) is BlockEntityDispenser dispenser)
        {
            dispenser.Dispense(byPlayer);
            return true;
        }
        return base.OnBlockInteractStart(world, byPlayer, blockSel);
    }
}

public class BlockEntityDispenser : BlockEntity
{
    /// <summary>Bottles left; rolled when first loaded, then saved with the block.</summary>
    private int stock = -1;

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (api.Side == EnumAppSide.Server && stock < 0) stock = api.World.Rand.Next(2, 6);
    }

    public void Dispense(IPlayer player)
    {
        if (Api.Side != EnumAppSide.Server) return;
        if (stock <= 0)
        {
            (player as IServerPlayer)?.SendIngameError("dispenserempty", Lang.Get("backrooms:dispenser-empty"));
            return;
        }

        stock--;
        var bottle = new ItemStack(Api.World.GetItem(new AssetLocation("backrooms:almondwater")));
        if (!player.InventoryManager.TryGiveItemstack(bottle, slotNotifyEffect: true))
        {
            Api.World.SpawnItemEntity(bottle, Pos.ToVec3d().Add(0.5, 1, 0.5));
        }
        Api.World.PlaySoundAt(new AssetLocation("game:sounds/block/vesselopen"), Pos.X + 0.5, Pos.Y + 0.5, Pos.Z + 0.5, null, randomizePitch: true, range: 12);
        MarkDirty();
    }

    public override void GetBlockInfo(IPlayer forPlayer, StringBuilder dsc)
    {
        base.GetBlockInfo(forPlayer, dsc);
        dsc.AppendLine(stock > 0 ? Lang.Get("backrooms:dispenser-stock", stock) : Lang.Get("backrooms:dispenser-empty"));
    }

    public override void ToTreeAttributes(ITreeAttribute tree)
    {
        base.ToTreeAttributes(tree);
        tree.SetInt("stock", stock);
    }

    public override void FromTreeAttributes(ITreeAttribute tree, IWorldAccessor worldAccessForResolve)
    {
        base.FromTreeAttributes(tree, worldAccessForResolve);
        stock = tree.GetInt("stock", -1);
    }
}
