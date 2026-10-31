using System.Collections.Generic;
using System.Text;
using Backrooms.Needs.Water;
using Backrooms.Salvage;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Client;
using Vintagestory.API.Common.Entities;
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
    private const float DrinkSeconds = 1f, LagSlackMs = 250;

    /// <summary>Server: when each drinker began, and where (the client's count of seconds is not taken on trust).</summary>
    private static readonly Dictionary<string, (BlockPos Pos, long StartMs)> drinking = new();

    private bool LiquidSource => Attributes?["liquidSource"].AsBool(false) == true;

    /// <summary>Whether a click is the pouring kind: on a liquid source (a water cooler, a fountain, a pump, a tap, a seep), with thirst on.
    /// Such a source never makes a bottle from nothing: right-click and hold to drink, or right-click with an empty bottle to fill it.
    /// With thirst off it hands out the item as it always did.</summary>
    private bool Pours(IWorldAccessor world) => LiquidSource && Needs.Needs.ThirstOn(world);

    private static bool HoldsEmptyBottle(IPlayer player) =>
        player?.InventoryManager?.ActiveHotbarSlot?.Itemstack?.Collectible?.Code?.ToString() == Drinks.EmptyBottle;

    private static void PlayDrinkSound(IWorldAccessor world, EntityPlayer entity, int repeats)
    {
        // (Checked here, before each sound: HandUse is only set once OnBlockInteractStart has returned true)
        if (repeats <= 0 || entity.Controls.HandUse != EnumHandInteract.BlockInteract) return;
        entity.PlayEntitySound("drink", world.PlayerByUid(entity.PlayerUID));
        world.RegisterCallback(_ => PlayDrinkSound(world, entity, repeats - 1), 300);
    }

    public override bool OnBlockInteractStep(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (!Pours(world) || HoldsEmptyBottle(byPlayer)) return base.OnBlockInteractStep(secondsUsed, world, byPlayer, blockSel);
        // (The server keeps the interaction open until the client's stop arrives)
        return world.Side != EnumAppSide.Client || secondsUsed < DrinkSeconds;
    }

    public override void OnBlockInteractStop(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel)
    {
        if (!Pours(world))
        {
            base.OnBlockInteractStop(secondsUsed, world, byPlayer, blockSel);
            return;
        }
        byPlayer?.Entity?.AnimManager?.StopAnimation("eat");
        if (world.Side != EnumAppSide.Server || byPlayer is not IServerPlayer player) return;
        (BlockPos Pos, long StartMs) began;
        lock (drinking)
        {
            if (!drinking.Remove(player.PlayerUID, out began)) return;
        }
        // Held the whole second: by the client's count, and (give or take the lag) by the server's own clock
        bool held = secondsUsed >= DrinkSeconds - 0.1f;
        bool timed = world.ElapsedMilliseconds - began.StartMs >= (long)(DrinkSeconds * 1000) - LagSlackMs;
        if (!held || !timed || blockSel == null || !began.Pos.Equals(blockSel.Position) || HoldsEmptyBottle(player)) return;
        (world.BlockAccessor.GetBlockEntity(blockSel.Position) as BlockEntityDispenser)?.Dispense(player, DispenseUse.Drink);
    }

    public override bool OnBlockInteractCancel(float secondsUsed, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, EnumItemUseCancelReason cancelReason)
    {
        if (!Pours(world)) return base.OnBlockInteractCancel(secondsUsed, world, byPlayer, blockSel, cancelReason);
        byPlayer?.Entity?.AnimManager?.StopAnimation("eat");
        if (byPlayer != null) lock (drinking) drinking.Remove(byPlayer.PlayerUID);
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer)
    {
        WorldInteraction[] help = base.GetPlacedBlockInteractionHelp(world, selection, forPlayer) ?? System.Array.Empty<WorldInteraction>();
        if (!Pours(world)) return help;
        Item bottle = world.GetItem(new AssetLocation(Drinks.EmptyBottle));
        var pour = new List<WorldInteraction>(help)
        {
            new WorldInteraction { ActionLangCode = "backrooms:heldhelp-drink", MouseButton = EnumMouseButton.Right },
            new WorldInteraction
            {
                ActionLangCode = "backrooms:blockhelp-fillbottle", MouseButton = EnumMouseButton.Right,
                Itemstacks = bottle == null ? null : new[] { new ItemStack(bottle) }
            }
        };
        return pour.ToArray();
    }

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
        if (Pours(world))
        {
            // An empty bottle fills at once; anything else drinks, while the button is held (Stop does the drinking)
            if (HoldsEmptyBottle(byPlayer))
            {
                dispenser.Dispense(byPlayer, DispenseUse.Fill);
                return true;
            }
            EntityPlayer entity = byPlayer.Entity;
            if (world.Side == EnumAppSide.Server)
            {
                // (An empty source says so now, and the hold goes nowhere)
                if (!dispenser.HasPortion(byPlayer)) return true;
                lock (drinking) drinking[byPlayer.PlayerUID] = (blockSel.Position.Copy(), world.ElapsedMilliseconds);
            }
            entity.AnimManager?.StartAnimation("eat");
            // (As vanilla's tryEatBegin: the first sound after half a second, whatever the hand is doing yet)
            world.RegisterCallback(_ => PlayDrinkSound(world, entity, 4), 500);
            return true;
        }
        dispenser.Dispense(byPlayer);
        return true;
    }
}

/// <summary>What a click on a dispenser does with its portion: hand the item over, fill the held empty bottle with it, or drink it there.</summary>
public enum DispenseUse { Give, Fill, Drink }

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
        ? ScarcitySystem.Portions(Api.World, Api.World.Rand.Next(4, 9) * ClassScale, min: 1)
        : ScarcitySystem.Portions(Api.World, Api.World.Rand.Next(1, 4) * ClassScale, min: Restocks ? 1 : 0);

    /// <summary>Less in the levels of a higher survival class (<see cref="ScarcitySystem.ClassScale(int)"/>), one-time stock and refill alike.</summary>
    private double ClassScale => ScarcitySystem.ClassScale(Api.World, Pos.X, Pos.Z);

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        // (A stock rolled before is kept, as saved)
        if (api.Side == EnumAppSide.Server && stock < 0) stock = RollStock();
    }

    /// <summary>Server: restocks if the time has come; whether a portion is left (if not, the player is told).</summary>
    public bool HasPortion(IPlayer player)
    {
        if (Api.Side != EnumAppSide.Server) return false;
        // A week to restock, longer where food is scarcer (three weeks on Scarce) and half that on Plentiful
        if (stock <= 0 && Restocks && emptySinceDay >= 0 && Api.World.Calendar.TotalDays - emptySinceDay >= RestockAfterDays / ScarcitySystem.FoodScale(Api.World))
        {
            stock = RollStock();
            emptySinceDay = -1;
        }
        if (stock > 0) return true;
        (player as IServerPlayer)?.SendIngameError("dispenserempty", Lang.Get("backrooms:dispenser-empty"));
        return false;
    }

    public void Dispense(IPlayer player, DispenseUse use = DispenseUse.Give)
    {
        if (Api.Side != EnumAppSide.Server || !HasPortion(player)) return;

        string[] options = Block.Attributes?["dispenses"].AsArray<string>();
        string code = options is { Length: > 0 } ? options[Api.World.Rand.Next(options.Length)] : "backrooms:almondwater";
        Item item = Api.World.GetItem(new AssetLocation(code));
        if (item == null) return;

        if (use == DispenseUse.Fill)
        {
            // One empty bottle becomes the full one
            ItemSlot slot = player.InventoryManager.ActiveHotbarSlot;
            if (slot?.Itemstack?.Collectible?.Code?.ToString() != Drinks.EmptyBottle) return;
            slot.TakeOut(1);
            slot.MarkDirty();
        }

        stock--;
        if (stock == 0) emptySinceDay = Api.World.Calendar.TotalDays;
        var stack = new ItemStack(item);
        if (use == DispenseUse.Drink)
        {
            // Straight from the source: what drinking it does, minus the bottle (Drinks.ApplyDrink is the one place that knows)
            Drinks.ApplyDrink(stack, player.Entity, leavesBottle: false);
        }
        else if (use == DispenseUse.Fill)
        {
            Drinks.Give(player.Entity, stack);
        }
        else if (!player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true))
        {
            Api.World.SpawnItemEntity(stack, Pos.ToVec3d().Add(0.5, 1, 0.5));
        }
        // (A pump gives its own sound: dispenseSound. Drinking has the drinker's own)
        if (use != DispenseUse.Drink)
        {
            string sound = Block.Attributes?["dispenseSound"].AsString("game:sounds/block/vesselopen") ?? "game:sounds/block/vesselopen";
            Api.World.PlaySoundAt(new AssetLocation(sound), Pos.X + 0.5, Pos.Y + 0.5, Pos.Z + 0.5, null, randomizePitch: true, range: 12);
        }
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
