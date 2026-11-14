using System;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Server;

namespace Backrooms.Wear;

/// <summary>
/// The hazmat suit and hood (item pass 0.700, tools/gen_items_wear.py; their items carry <c>"hazmat": "suit"</c> or
/// <c>"hood"</c> in their attributes). What a sealed suit plausibly answers, and nothing else:
/// <list type="bullet">
/// <item><b>Level 14's contaminated rooms</b> (L14System.Contaminated): the suit keeps <see cref="SuitBlocks"/> of the
/// poison off your skin (the hurt), the hood keeps <see cref="HoodBlocks"/> of the air out (the pull on your stability).
/// Each hurt the room would do wears each piece worn by 1.</item>
/// <item><b>The Basement's smell of the dead</b> (BasementSystem.Breathe): the hood's filter lets the smell build at only
/// <see cref="HoodSmell"/> of its pace (so about three minutes among the dead before it chokes, not 45 s). It wears the hood
/// by 1 every <see cref="SmellWearSeconds"/> it filters.</item>
/// </list>
/// A piece worn down to nothing (durability 0) still sits on you but keeps nothing out. The trade-offs: the suit is hot
/// (<see cref="SuitThirst"/> on the thirst rate, or on hunger in a world without thirst) and bulky (5 % slower, the item's
/// own statModifiers); the hood is stuffy (<see cref="HoodThirst"/>); neither is armour, so a blow goes straight through.
/// </summary>
public class HazmatSystem : ModSystem
{
    public const float SuitBlocks = 0.75f, HoodBlocks = 0.75f, HoodSmell = 0.25f;
    public const float SuitThirst = 0.35f, HoodThirst = 0.15f;
    public const float SmellWearSeconds = 5f;
    private const string StatCode = "backrooms:hazmat";

    private ICoreServerAPI sapi;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.RegisterGameTickListener(OnTick, 2000, 1000);
    }

    /// <summary>The suit's and hood's heat: worn, worn out or not, they are hot (only touched when it changes: it is synced).</summary>
    private void OnTick(float dt)
    {
        bool thirst = Needs.Needs.ThirstOn(sapi.World);
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online.Entity is not { } entity) continue;
            float extra = (Worn(entity, "suit", false) != null ? SuitThirst : 0) + (Worn(entity, "hood", false) != null ? HoodThirst : 0);
            Needs.Needs.SetStat(entity, thirst ? "thirstrate" : "hungerrate", StatCode, extra);
            Needs.Needs.SetStat(entity, thirst ? "hungerrate" : "thirstrate", StatCode, 0);
        }
    }

    /// <summary>The slot of the piece ("suit" or "hood") the player wears; with <paramref name="sound"/>, only one with wear left in it.</summary>
    public static ItemSlot Worn(Entity who, string piece, bool sound = true)
    {
        if (who is not EntityPlayer { Player: { } player }) return null;
        IInventory worn = player.InventoryManager?.GetOwnInventory(GlobalConstants.characterInvClassName);
        if (worn == null) return null;
        foreach (ItemSlot slot in worn)
        {
            if (slot.Empty || slot.Itemstack.ItemAttributes?["hazmat"].AsString() != piece) continue;
            if (sound && slot.Itemstack.Collectible.GetMaxDurability(slot.Itemstack) > 0 && slot.Itemstack.Collectible.GetRemainingDurability(slot.Itemstack) <= 0) continue;
            return slot;
        }
        return null;
    }

    /// <summary>
    /// How much of a hazard gets through the piece worn (1 with none, 1 - <paramref name="blocks"/> with a sound one), and
    /// wears that piece by <paramref name="wear"/>.
    /// </summary>
    public static float Through(Entity who, string piece, float blocks, int wear = 1)
    {
        ItemSlot slot = Worn(who, piece);
        if (slot == null) return 1f;
        if (wear > 0) slot.Itemstack.Collectible.DamageItem(who.World, who, slot, wear);
        return 1f - blocks;
    }
}
