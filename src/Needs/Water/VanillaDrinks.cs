using System;
using HarmonyLib;
using NeedsApi = Backrooms.Needs.Needs;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.GameContent;

namespace Backrooms.Needs.Water;

/// <summary>
/// A vanilla liquid drunk from a bowl, jug, bucket or cup fills the water bar (with thirst on): the game gives those drinks
/// satiety only, and plain water none at all (a container of water cannot be drunk). Two patches on
/// <c>BlockLiquidContainerBase</c>, which every vanilla liquid container is: water gets a nutrition entry of nothing (so
/// the held container can be drunk from, on both sides), and a drink the game finishes hydrates by the litres it took.
/// </summary>
public class VanillaDrinks : ModSystem
{
    private const string HarmonyId = "backroomsss.vanilladrinks";
    private static int users;
    private static readonly object gate = new();
    private static Harmony harmony;

    /// <summary>Hydration per litre by liquid, in the meter's own units (0..1500): as a litre drunk from clean water in the world
    /// (<c>WaterClass.CleanHydration</c>, 600, the same as a bottle of Almond Water): water and juice 600, milk 500, cider, wine and
    /// mead 300, spirits 50, vinegar -200 (brine's -300 is the world's own). Other liquids give none.</summary>
    public static float PerLitre(string path)
    {
        if (path == null) return 0;
        if (path.StartsWith("waterportion") || path.StartsWith("juiceportion")) return WaterClass.CleanHydration;
        if (path.StartsWith("milkportion")) return 500;
        if (path.StartsWith("ciderportion")) return 300;
        if (path.StartsWith("spiritportion")) return 50;
        if (path.StartsWith("vinegarportion")) return -200;
        return 0;
    }

    public override void Start(ICoreAPI api)
    {
        lock (gate)
        {
            if (users++ > 0) return;
            harmony = new Harmony(HarmonyId);
            harmony.UnpatchAll(HarmonyId);
            try
            {
                var perLitre = AccessTools.Method(typeof(BlockLiquidContainerBase), nameof(BlockLiquidContainerBase.GetNutritionPropertiesPerLitre));
                var eatStop = AccessTools.Method(typeof(BlockLiquidContainerBase), "tryEatStop");
                harmony.Patch(perLitre, postfix: new HarmonyMethod(typeof(VanillaDrinks), nameof(PerLitrePostfix)));
                harmony.Patch(eatStop, prefix: new HarmonyMethod(typeof(VanillaDrinks), nameof(EatStopPrefix)),
                    postfix: new HarmonyMethod(typeof(VanillaDrinks), nameof(EatStopPostfix)));
            }
            catch (Exception e) { api.Logger.Warning("[backrooms] vanilla drinks: the hooks could not be applied ({0}); bowls and jugs give no hydration", e.Message); }
        }
    }

    public override void Dispose()
    {
        lock (gate)
        {
            if (--users > 0) return;
            harmony?.UnpatchAll(HarmonyId);
            harmony = null;
        }
    }

    /// <summary>Water, which the game says has no nutrition at all, is a drink when thirst is on: an entry of nothing.</summary>
    public static void PerLitrePostfix(BlockLiquidContainerBase __instance, IWorldAccessor world, ItemStack itemstack, ref FoodNutritionProperties __result)
    {
        if (__result != null || !NeedsApi.ThirstOn(world)) return;
        string path = __instance.GetContent(itemstack)?.Collectible?.Code?.Path;
        if (path != null && path.StartsWith("waterportion")) __result = new FoodNutritionProperties { Satiety = 0, FoodCategory = EnumFoodCategory.NoNutrition };
    }

    /// <summary>What a container held before the sip: the liquid's code and the litres.</summary>
    public struct Before { public string Code; public float Litres; }

    public static void EatStopPrefix(BlockLiquidContainerBase __instance, ItemSlot slot, EntityAgent byEntity, out Before __state)
    {
        __state = default;
        if (byEntity?.World?.Side != EnumAppSide.Server || slot?.Itemstack == null || !NeedsApi.ThirstOn(byEntity.World)) return;
        ItemStack content = __instance.GetContent(slot.Itemstack);
        if (content == null) return;
        __state = new Before { Code = content.Collectible.Code.Path, Litres = __instance.GetCurrentLitres(slot.Itemstack) };
    }

    public static void EatStopPostfix(BlockLiquidContainerBase __instance, ItemSlot slot, EntityAgent byEntity, Before __state)
    {
        if (__state.Code == null || slot?.Itemstack == null) return;
        float taken = __state.Litres - __instance.GetCurrentLitres(slot.Itemstack);
        if (taken > 0) Sip(byEntity, __state.Code, taken);
    }

    /// <summary>Server: the drinker has taken <paramref name="litres"/> of a liquid (by its item code path).</summary>
    public static void Sip(Entity entity, string code, float litres)
    {
        float perLitre = PerLitre(code);
        if (perLitre != 0 && litres > 0) NeedsApi.Hydrate(entity, perLitre * litres);
    }
}
