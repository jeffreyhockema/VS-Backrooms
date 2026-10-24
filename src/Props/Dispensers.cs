using System.Text;
using Backrooms.Salvage;
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
/// How much they hold, and how soon they restock, follow the world's Backrooms scarcity (<see cref="ScarcitySystem"/>).
/// </summary>
public class BlockDispenser : Block
{

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        // Level 3999's vending machines take something for what they give, and never run out (attributes takes, stockless)
        if (Attributes?["takes"].AsString() is string takes)
        {
            if (world.Side == EnumAppSide.Server && byPlayer is IServerPlayer buyer) Regions.L3999System.Vend(buyer, blockSel.Position, this, takes);
            return true;
        }
        BlockEntityDispenser dispenser = world.BlockAccessor.GetBlockEntity(blockSel.Position) as BlockEntityDispenser;
        if (dispenser == null && EntityClass != null && Attributes?["dispenses"].Exists == true)
        {
            // A dispenser placed before its block had a block entity (the Level 10 hand pump in older worlds) gets one now.
            // The client has none either, so it must still say it handled the click, or the click never reaches the server
            if (world.Side != EnumAppSide.Server) return true;
            world.BlockAccessor.SpawnBlockEntity(EntityClass, blockSel.Position);
            dispenser = world.BlockAccessor.GetBlockEntity(blockSel.Position) as BlockEntityDispenser;
        }
        if (dispenser == null) return base.OnBlockInteractStart(world, byPlayer, blockSel);

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

    /// <summary>With thirst on, an Almond Water seep still fills up, but only once a fortnight and with a few portions.</summary>
    private const double SeepRestockDays = 14;

    /// <summary>Items left; rolled when first loaded, then saved with the block.</summary>
    private int stock = -1;
    private double emptySinceDay = -1;

    /// <summary>
    /// Water is as scarce as food (docs/design/needs/README.md section 3): with thirst on, a dispenser that hands out only drinks
    /// (every item it gives has a <c>hydration</c>) never restocks, and holds just its one-time stock, except the Level 8 seeps.
    /// Food dispensers, and every dispenser with thirst off, are as they always were.
    /// </summary>
    private bool ScarceDrinks => Needs.Needs.ThirstOn(Api.World) && GivesOnlyDrinks();

    private bool Seep => Block?.Code?.Path.StartsWith("almondseep") == true;

    private bool Restocks => Block?.Attributes?["restock"].AsBool() == true && (!ScarceDrinks || Seep);

    private double RestockAfterDays => ScarceDrinks && Seep ? SeepRestockDays : RestockDays;

    private bool GivesOnlyDrinks()
    {
        string[] options = Block?.Attributes?["dispenses"].AsArray<string>();
        if (options is not { Length: > 0 }) options = new[] { "backrooms:almondwater" };
        foreach (string code in options)
            if (Api.World.GetItem(new AssetLocation(code))?.Attributes?["hydration"].Exists != true) return false;
        return true;
    }

    /// <summary>
    /// A full load, scaled by the world's scarcity: 1-3 items, or 4-8 for one that restocks (1-3 for a drink dispenser, which
    /// keeps what it holds: a seep's refill too). On Scarce one that restocks always gets at least one; one that doesn't may
    /// be found empty.
    /// </summary>
    private int RollStock() => Restocks && !ScarceDrinks
        ? ScarcitySystem.Portions(Api.World, Api.World.Rand.Next(4, 9), min: 1)
        : ScarcitySystem.Portions(Api.World, Api.World.Rand.Next(1, 4), min: Restocks ? 1 : 0);

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        // (A stock rolled before is kept, as saved)
        if (api.Side == EnumAppSide.Server && stock < 0) stock = RollStock();
    }

    public void Dispense(IPlayer player)
    {
        if (Api.Side != EnumAppSide.Server) return;
        // A week to restock, longer where food is scarcer (three weeks on Scarce) and half that on Plentiful
        if (stock <= 0 && Restocks && emptySinceDay >= 0 && Api.World.Calendar.TotalDays - emptySinceDay >= RestockAfterDays / ScarcitySystem.FoodScale(Api.World))
        {
            stock = RollStock();
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
        // (A pump gives its own sound: dispenseSound)
        string sound = Block.Attributes?["dispenseSound"].AsString("game:sounds/block/vesselopen") ?? "game:sounds/block/vesselopen";
        Api.World.PlaySoundAt(new AssetLocation(sound), Pos.X + 0.5, Pos.Y + 0.5, Pos.Z + 0.5, null, randomizePitch: true, range: 12);
        MarkDirty();
    }

    public override void GetBlockInfo(IPlayer forPlayer, StringBuilder dsc)
    {
        base.GetBlockInfo(forPlayer, dsc);
        if (Block?.Attributes?["stockless"].AsBool(false) == true) return; // (Level 3999's: never empty)
        // (-1: not rolled yet, or not sent yet. Unknown, not empty)
        if (stock < 0) return;
        dsc.AppendLine(stock > 0 ? Lang.Get("backrooms:dispenser-stock", stock) : Lang.Get(Restocks ? (ScarceDrinks ? "backrooms:dispenser-restocks-slowly" : "backrooms:dispenser-restocks") : "backrooms:dispenser-empty"));
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
