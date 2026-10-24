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
        if (blockSel != null && firstEvent)
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
    protected override void tryEatStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity)
    {
        int before = slot.StackSize;
        base.tryEatStop(secondsUsed, slot, byEntity);
        if (byEntity.World.Side != EnumAppSide.Server || slot.StackSize >= before) return;
        Drinks.Hydrate(this, byEntity);
    }
}
