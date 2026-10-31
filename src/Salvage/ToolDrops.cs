using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Salvage;

/// <summary>
/// Where the tool in hand changes what a piece of the building gives, and only where a real tool would. There are
/// three such places, none of them needed for anything and none above one and a half times the usual yield:
/// <list type="bullet">
/// <item>Pipes, cable runs and machinery (<see cref="Mode.Pick"/>): a bronze pickaxe cuts and prises them apart in
/// longer, cleaner lengths than a copper one that crushes them (a quarter more), and an iron one more still (a half).</item>
/// <item>Dead light fixtures (<see cref="Mode.Careful"/>): worked loose with a knife, scraper, shiv or chisel instead of
/// being smashed, the tube and its lens come out in pieces worth keeping (a half more).</item>
/// <item>Stripping wallpaper and carpet with a metal knife gives what the glass shiv does (see
/// <see cref="BlockBehaviorStrippable"/>, which uses <see cref="IsMetalKnife"/>).</item>
/// </list>
/// It works by scaling the drop quantity, so a block's drops keep their own odds and a tool that does not qualify
/// changes nothing.
/// </summary>
public class BlockBehaviorToolDrops : BlockBehavior
{
    public enum Mode
    {
        /// <summary>A pickaxe of bronze or better.</summary>
        Pick,
        /// <summary>A knife (the Lobby's own blades are knives too) or a chisel.</summary>
        Careful,
    }

    private const float BronzeYield = 1.25f, IronYield = 1.5f, CarefulYield = 1.5f;

    /// <summary>The metals a knife is made of that hold an edge: a flint or bone knife does not count, nor does a ruined one.</summary>
    private static readonly HashSet<string> KnifeMetals = new()
    {
        "copper", "tinbronze", "bismuthbronze", "blackbronze", "gold", "silver", "iron", "meteoriciron", "steel",
    };

    private readonly Mode mode;

    public BlockBehaviorToolDrops(Block block, Mode mode) : base(block)
    {
        this.mode = mode;
    }

    /// <summary>Whether a vanilla knife is metal (copper or better), so it holds an edge like the shiv's.</summary>
    public static bool IsMetalKnife(CollectibleObject held) =>
        held?.Variant != null && held.Variant.TryGetValue("material", out string material) && KnifeMetals.Contains(material);

    /// <summary>What a pick of this tier gets out of metalwork against a copper one: the same up to copper, a quarter more for bronze, a half more for iron and better.</summary>
    public static float PickYield(int tier) => tier >= 4 ? IronYield : tier >= 3 ? BronzeYield : 1f;

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, ref float dropQuantityMultiplier, ref EnumHandling handling)
    {
        ItemSlot slot = byPlayer?.InventoryManager?.ActiveHotbarSlot;
        CollectibleObject held = slot?.Itemstack?.Collectible;
        if (held == null) return null;
        EnumTool? tool = held.GetTool(slot);
        if (mode == Mode.Pick)
        {
            if (tool == EnumTool.Pickaxe) dropQuantityMultiplier *= PickYield(held.ToolTier);
        }
        else if (tool is EnumTool.Knife or EnumTool.Chisel)
        {
            dropQuantityMultiplier *= CarefulYield;
        }
        return null;
    }
}
