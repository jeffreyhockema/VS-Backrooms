using System.Text;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// Level 14's medicine (itemtypes/14, written by tools/gen_14_items.py): the painkillers are vanilla's healing item as it is;
/// this registers the antibiotics' behaviour (<see cref="CollectibleBehaviorL14Antibiotics"/>).
/// </summary>
public class L14ItemsSystem : ModSystem
{
    public override void Start(ICoreAPI api) =>
        api.RegisterCollectibleBehaviorClass("BackroomsL14Antibiotics", typeof(CollectibleBehaviorL14Antibiotics));
}

/// <summary>
/// Antibiotics from a reception desk ("Bandages, antibiotics, and painkillers are often found at the front desk"): they heal a
/// little, as a poultice does (vanilla's healing item, which this is), and once taken they stop any poison still burning in whoever
/// took them: an Infecting Agent's bite (<see cref="Backrooms.Entities.VenomSystem.Envenom"/>) or any other. The effects are
/// removed outright rather than stopped (a stopped effect would tick once more).
/// </summary>
public class CollectibleBehaviorL14Antibiotics : CollectibleBehaviorHealingItem
{
    public CollectibleBehaviorL14Antibiotics(CollectibleObject collectible) : base(collectible) { }

    public override void OnHeldInteractStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, ref EnumHandling handling)
    {
        // (Who takes them is decided before the base uses the pills up, as it decides it)
        Entity target = byEntity.World.Side == EnumAppSide.Server && slot.Itemstack != null && secondsUsed >= GetApplicationTime(byEntity)
            ? GetTargetEntity(slot, byEntity, entitySel) : null;
        base.OnHeldInteractStop(secondsUsed, slot, byEntity, blockSel, entitySel, ref handling);
        if (target?.GetBehavior<EntityBehaviorHealth>() is { } health)
            health.ActiveDoTEffects.RemoveAll(effect => effect.EffectType == (int)EnumDamageOverTimeEffectType.Poison);
    }

    public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        dsc.AppendLine(Lang.Get("backrooms:iteminfo-l14-antibiotics"));
    }
}
