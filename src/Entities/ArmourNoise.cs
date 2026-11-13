using System.Text;
using Vintagestory.API.Common;
using Vintagestory.API.Config;

namespace Backrooms.Entities;

/// <summary>
/// Metal is loud (feedback round 2026-11): vanilla's chain, lamellar, brigandine, scale and plate armour carry
/// <see cref="CollectibleBehaviorClank"/> (assets/backrooms/patches/armour-noise.json), which only tells you so in the item's
/// tooltip. The effect itself is <see cref="Senses.ArmourNoise"/>.
/// </summary>
public class ArmourNoiseSystem : ModSystem
{
    public override void Start(ICoreAPI api) =>
        api.RegisterCollectibleBehaviorClass("BackroomsClank", typeof(CollectibleBehaviorClank));
}

/// <summary>A tooltip line on armour that makes you louder: how much farther things hear you while you move.</summary>
public class CollectibleBehaviorClank : CollectibleBehavior
{
    public CollectibleBehaviorClank(CollectibleObject collObj) : base(collObj) { }

    public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        double clank = Senses.ClankOf(collObj.Code?.Path ?? "");
        if (clank <= 1) return;
        dsc.AppendLine(Lang.Get(clank >= Senses.PlateClank ? "backrooms:iteminfo-clank-plate" : "backrooms:iteminfo-clank-metal"));
    }
}
