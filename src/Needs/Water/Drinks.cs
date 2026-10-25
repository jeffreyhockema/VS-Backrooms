using System;
using Backrooms.Worldgen;
using NeedsApi = Backrooms.Needs.Needs;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Client;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Needs.Water;

/// <summary>Shared pieces of the drinks (docs/design/needs/README.md section 3): the item attributes, the bottle left behind.</summary>
public static class Drinks
{
    /// <summary>The bottle a drink leaves when thirst is on (attribute <c>leavesBottle</c>).</summary>
    public const string EmptyBottle = "backrooms:emptybottle";

    /// <summary>The hydration an item gives (attribute <c>hydration</c>, in the meter's own units), or null when it is not a drink.</summary>
    public static float? HydrationOf(CollectibleObject collectible) =>
        collectible?.Attributes?["hydration"].Exists == true ? collectible.Attributes["hydration"].AsFloat() : null;

    /// <summary>A drink's tooltip line "Hydration: N%" (with thirst on, for an item that has a <c>hydration</c>).</summary>
    public static void AppendHydrationInfo(CollectibleObject collectible, IWorldAccessor world, System.Text.StringBuilder dsc)
    {
        if (HydrationOf(collectible) is float hydration && NeedsApi.ThirstOn(world))
            dsc.AppendLine(Lang.Get("backrooms:iteminfo-hydration", Math.Round(hydration / NeedsApi.MaxHydration * 100)));
    }

    /// <summary>Server: moves the entity's temporal stability by <paramref name="amount"/> (at most 1, as drinks always did).</summary>
    public static void AddStability(Entity entity, double amount)
    {
        double stability = entity.WatchedAttributes.GetDouble("temporalStability", 1);
        entity.WatchedAttributes.SetDouble("temporalStability", Math.Min(1, stability + amount));
    }

    /// <summary>Server: hydrates the drinker by the stack's own <c>hydration</c> (no-op for an item without one, or with thirst off).</summary>
    public static void Hydrate(CollectibleObject collectible, Entity entity)
    {
        if (HydrationOf(collectible) is float amount) NeedsApi.Hydrate(entity, amount);
    }

    /// <summary>How much stability a drink restores, unless its <c>stabilityRestored</c> attribute says otherwise.</summary>
    private const double StabilityRestored = 0.15;

    /// <summary>The stability a drink restores (attribute <c>stabilityRestored</c>, 0.15 if absent).</summary>
    public static double StabilityOf(CollectibleObject collectible) =>
        collectible?.Attributes?["stabilityRestored"].AsDouble(StabilityRestored) ?? StabilityRestored;

    /// <summary>
    /// Server: everything drinking <paramref name="drink"/> does to <paramref name="byEntity"/>, whether they drank the item from their
    /// hand (ItemAlmondWater, which leaves its bottle) or straight from a water cooler or fountain (no bottle):
    /// stability, the Duller ward, sleep aid and caffeine, and with thirst on hydration, gut rot, and the empty bottle.
    /// </summary>
    public static void ApplyDrink(ItemStack drink, EntityAgent byEntity, bool leavesBottle)
    {
        CollectibleObject drinkItem = drink?.Collectible;
        if (drinkItem == null) return;
        AddStability(byEntity, StabilityOf(drinkItem));
        // ...and keeps the Dullers off for a while
        if (drinkItem.Attributes?["wardsDullers"].AsBool(true) != false) Backrooms.Entities.AlmondWater.Drank(byEntity);

        // Thirst: the drink hydrates (nothing happens with thirst off), may help or hinder sleep, and leaves its bottle
        // (Sleep aid and caffeine are fatigue's: they work with thirst off)
        if (NeedsApi.FatigueOn(byEntity.World))
        {
            if (drinkItem.Attributes?["sleepAid"].AsBool(false) == true) NeedsApi.MakeDrowsy(byEntity);
            if (drinkItem.Attributes?["caffeineHours"].Exists == true) NeedsApi.Caffeinate(byEntity, drinkItem.Attributes["caffeineHours"].AsDouble());
        }
        if (!NeedsApi.ThirstOn(byEntity.World)) return;
        Hydrate(drinkItem, byEntity);
        double taint = drinkItem.Attributes?["taintChance"].AsDouble(0) ?? 0;
        if (taint > 0 && byEntity.World.Rand.NextDouble() < taint)
        {
            NeedsApi.MakeSick(byEntity, WaterClass.SickHours); // (MakeSick tells the player)
        }
        if (leavesBottle && drinkItem.Attributes?["leavesBottle"].AsString() is string bottle)
        {
            Item empty = byEntity.World.GetItem(new AssetLocation(bottle));
            if (empty != null) Give(byEntity, new ItemStack(empty));
        }
    }

    /// <summary>Server: a stack goes to the drinker's inventory, or falls at their feet.</summary>
    public static void Give(EntityAgent entity, ItemStack stack)
    {
        if (stack == null) return;
        IPlayer player = (entity as EntityPlayer)?.Player;
        if (player == null || !player.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true))
            entity.World.SpawnItemEntity(stack, entity.Pos.XYZ.AddCopy(0, 0.5, 0));
    }
}

/// <summary>
/// The glass bottle a drink leaves behind (with thirst on). Held in an empty hand's place at water, right-click fills it by the
/// water's class: clean, murky or salt (boiling water fills a clean bottle). Its item is <c>liquidSelectable</c>, so the click can
/// land on water at all.
/// </summary>
public class ItemEmptyBottle : Item
{
    public override void OnHeldInteractStart(ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, bool firstEvent, ref EnumHandHandling handling)
    {
        // (A water cooler or fountain answers its own click: drink, or fill this bottle. Water behind it is not what was clicked)
        if (blockSel != null && firstEvent && byEntity.World.BlockAccessor.GetBlock(blockSel.Position).Attributes?["liquidSource"].AsBool(false) != true)
        {
            IWorldAccessor world = byEntity.World;
            Block fluid = world.BlockAccessor.GetBlock(blockSel.Position, BlockLayersAccess.Fluid);
            if (WaterClass.IsDrinkable(fluid))
            {
                handling = EnumHandHandling.PreventDefault;
                if (world.Side != EnumAppSide.Server) return;
                WorldLayout layout = null;
                try { layout = BackroomsWorld.IsBackroomsClimate(world.Config) ? BackroomsWorld.CreateLayout(world) : null; }
                catch (Exception) { /* plain water */ }
                WaterKind kind = WaterClass.Of(world, layout, fluid, blockSel.Position);
                Item filled = world.GetItem(new AssetLocation(WaterClass.BottleCode(kind)));
                if (filled == null) return;
                slot.TakeOut(1);
                slot.MarkDirty();
                Drinks.Give(byEntity, new ItemStack(filled));
                world.PlaySoundAt(new AssetLocation("game:sounds/environment/smallsplash"), byEntity, (byEntity as EntityPlayer)?.Player, true, 12);
                return;
            }
        }
        base.OnHeldInteractStart(slot, byEntity, blockSel, entitySel, firstEvent, ref handling);
    }

    public override WorldInteraction[] GetHeldInteractionHelp(ItemSlot inSlot) =>
        new[] { new WorldInteraction { ActionLangCode = "backrooms:heldhelp-fillbottle", MouseButton = EnumMouseButton.Right } };
}

/// <summary>LUCA tears from Level Fun's golden pool: a sip of something that is, at least, wet. Hydrates a little; the rest of what
/// the tears are for is not built yet.</summary>
public class ItemLucaTears : Item
{
    public override void GetHeldItemInfo(ItemSlot inSlot, System.Text.StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        Drinks.AppendHydrationInfo(this, world, dsc);
    }

    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;
        Drinks.Hydrate(this, byEntity);
    }
}
