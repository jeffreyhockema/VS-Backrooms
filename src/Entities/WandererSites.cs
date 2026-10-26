using System;
using System.Reflection;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// A wanderer's site: camp, outpost, road, city, end, hub, amber or 3999 (see <see cref="Sites"/>). It picks the
/// wanderer's trade list (<c>config/trade/wanderer-&lt;site&gt;.json</c>, written by <c>tools/gen_entities.py</c>), the
/// name a new one is given, and what it says (<c>config/dialogue/wanderer.json</c>, from <c>tools/gen_dialogue.py</c>,
/// reads it as <c>entity.backroomsSite</c>). It is kept as a dialogue variable, a string in the entity's watched
/// <c>variables</c> tree, so it is saved with the wanderer and seen by the client.
/// <para>
/// Wanderers stay vanilla's <c>EntityTrader</c>: a saved entity keeps the class it was saved with, so a subclass would
/// only ever reach new ones. Vanilla reads the trade list from the entity type each time a trader is loaded, so
/// <see cref="WandererSystem"/> puts the site's list back (<see cref="Apply"/>) whenever a wanderer loads or spawns.
/// </para>
/// </summary>
public static class WandererSites
{
    /// <summary>The dialogue variable (entity scope) holding the site.</summary>
    public const string Variable = "backroomsSite";

    /// <summary>Every site, each with its trade list and its lines in the dialogue.</summary>
    public static readonly string[] Sites = { "camp", "outpost", "road", "city", "end", "hub", "amber", "3999" };

    private static readonly MethodInfo Refresh = typeof(EntityTradingHumanoid).GetMethod("RefreshBuyingSellingInventory", BindingFlags.Instance | BindingFlags.NonPublic);

    /// <summary>A wanderer's site, or null if it has none yet.</summary>
    public static string Site(Entity entity) => entity.WatchedAttributes.GetTreeAttribute("variables")?.GetString(Variable);

    /// <summary>Gives a wanderer its site key, before it is spawned (<see cref="Apply"/> does the rest once it is).</summary>
    public static void SetSite(Entity entity, string site)
    {
        entity.WatchedAttributes.GetOrAddTreeAttribute("variables").SetString(Variable, site);
        entity.WatchedAttributes.MarkPathDirty("variables");
    }

    /// <summary>A site's trade list, or null (logged) if it is missing or unreadable.</summary>
    public static TradeProperties LoadTradeProps(ICoreAPI api, string site)
    {
        IAsset asset = api.Assets.TryGet(new AssetLocation("backrooms", "config/trade/wanderer-" + site + ".json"));
        if (asset == null)
        {
            api.Logger.Warning("[backrooms] no trade list for the wanderers' site {0}", site);
            return null;
        }
        try { return JsonUtil.FromString<TradeProperties>(asset.ToText()); }
        catch (Exception e)
        {
            api.Logger.Error("[backrooms] could not read the trade list of the wanderers' site {0}: {1}", site, e.Message);
            return null;
        }
    }

    /// <summary>
    /// Server: gives a wanderer in the world its site key and trade list (its next weekly restock draws from it). With
    /// <paramref name="restock"/>, its wares are cleared and it is stocked afresh from the list at once (its gears kept).
    /// </summary>
    public static bool Apply(EntityTradingHumanoid trader, string site, bool restock)
    {
        if (Site(trader) != site) SetSite(trader, site);
        if (LoadTradeProps(trader.Api, site) is not { } props) return false;
        trader.TradeProps = props;
        if (!restock || trader.Inventory == null) return true;
        foreach (ItemSlotTrade slot in trader.Inventory.SellingSlots) Clear(slot);
        foreach (ItemSlotTrade slot in trader.Inventory.BuyingSlots) Clear(slot);
        if (Refresh == null)
        {
            trader.Api.Logger.Warning("[backrooms] cannot restock a wanderer: the game has no RefreshBuyingSellingInventory");
            return true;
        }
        Refresh.Invoke(trader, new object[] { 1.1f });
        return true;
    }

    private static void Clear(ItemSlotTrade slot)
    {
        if (slot == null) return;
        slot.TradeItem = null;
        slot.Itemstack = null;
    }

    /// <summary>Server: names a new wanderer from its site's names (the type's <c>backroomsSiteNames</c>), if it has any.</summary>
    public static void NameForSite(Entity entity, string site)
    {
        string[] names = entity.Properties.Attributes?["backroomsSiteNames"][site].AsArray<string>();
        if (names == null || names.Length == 0) return;
        entity.GetBehavior<EntityBehaviorNameTag>()?.SetName(names[entity.World.Rand.Next(names.Length)]);
    }

    /// <summary>How many wares it has for sale and how many it wants (for the log).</summary>
    public static (int Selling, int Buying) WareCount(EntityTradingHumanoid trader)
    {
        int selling = 0, buying = 0;
        if (trader.Inventory == null) return (0, 0);
        foreach (ItemSlotTrade slot in trader.Inventory.SellingSlots)
            if (slot?.Itemstack != null && slot.TradeItem != null) selling++;
        foreach (ItemSlotTrade slot in trader.Inventory.BuyingSlots)
            if (slot?.Itemstack != null && slot.TradeItem != null) buying++;
        return (selling, buying);
    }
}
