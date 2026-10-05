using System.Text;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Props;

/// <summary>Registers vending machines, water coolers, fountains and fridges that still give something.</summary>
public class DispenserSystem : ModSystem
{
    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockClass("BackroomsDispenser", typeof(BlockDispenser));
        api.RegisterBlockEntityClass("BackroomsDispenser", typeof(BlockEntityDispenser));
    }
}

/// <summary>
/// Using the block hands the player one item while stock lasts: Almond Water unless the block's
/// <c>dispenses</c> attribute lists others, one picked at random each time. Blocks with <c>restock</c> fill up again
/// a week after they run dry (the Snackrooms restock weekly). A few of Level 4's vending machines give nothing:
/// they take whoever presses their buttons to the Snackrooms instead, every time, and always to the same food court.
/// </summary>
public class BlockDispenser : Block
{

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (world.BlockAccessor.GetBlockEntity(blockSel.Position) is not BlockEntityDispenser dispenser)
            return base.OnBlockInteractStart(world, byPlayer, blockSel);

        if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer player && Code.Path.StartsWith("vendingmachine"))
        {
            ThresholdSystem thresholds = world.Api.ModLoader.GetModSystem<ThresholdSystem>();
            if (thresholds != null && thresholds.UseVendingMachine(player, blockSel.Position)) return true;
        }
        dispenser.Dispense(byPlayer);
        return true;
    }
}

public class BlockEntityDispenser : BlockEntity
{
    private const double RestockDays = 7;

    /// <summary>Items left; rolled when first loaded, then saved with the block.</summary>
    private int stock = -1;
    private double emptySinceDay = -1;

    private bool Restocks => Block?.Attributes?["restock"].AsBool() == true;

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (api.Side == EnumAppSide.Server && stock < 0) stock = api.World.Rand.Next(Restocks ? 4 : 2, Restocks ? 9 : 6);
    }

    public void Dispense(IPlayer player)
    {
        if (Api.Side != EnumAppSide.Server) return;
        if (stock <= 0 && Restocks && emptySinceDay >= 0 && Api.World.Calendar.TotalDays - emptySinceDay >= RestockDays)
        {
            stock = Api.World.Rand.Next(4, 9);
            emptySinceDay = -1;
        }
        if (stock <= 0)
        {
            (player as IServerPlayer)?.SendIngameError("dispenserempty", Lang.Get("backrooms:dispenser-empty"));
            return;
        }

        string[] options = Block.Attributes?["dispenses"].AsArray<string>();
        string code = options is { Length: > 0 } ? options[Api.World.Rand.Next(options.Length)] : "backrooms:almondwater";
        Item item = Api.World.GetItem(new AssetLocation(code));
        if (item == null) return;

        stock--;
        if (stock == 0) emptySinceDay = Api.World.Calendar.TotalDays;
        var stack = new ItemStack(item);
        if (!player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true))
        {
            Api.World.SpawnItemEntity(stack, Pos.ToVec3d().Add(0.5, 1, 0.5));
        }
        Api.World.PlaySoundAt(new AssetLocation("game:sounds/block/vesselopen"), Pos.X + 0.5, Pos.Y + 0.5, Pos.Z + 0.5, null, randomizePitch: true, range: 12);
        MarkDirty();
    }

    public override void GetBlockInfo(IPlayer forPlayer, StringBuilder dsc)
    {
        base.GetBlockInfo(forPlayer, dsc);
        dsc.AppendLine(stock > 0 ? Lang.Get("backrooms:dispenser-stock", stock) : Lang.Get(Restocks ? "backrooms:dispenser-restocks" : "backrooms:dispenser-empty"));
    }

    public override void ToTreeAttributes(ITreeAttribute tree)
    {
        base.ToTreeAttributes(tree);
        tree.SetInt("stock", stock);
        tree.SetDouble("emptySince", emptySinceDay);
    }

    public override void FromTreeAttributes(ITreeAttribute tree, IWorldAccessor worldAccessForResolve)
    {
        base.FromTreeAttributes(tree, worldAccessForResolve);
        stock = tree.GetInt("stock", -1);
        emptySinceDay = tree.GetDouble("emptySince", -1);
    }
}
