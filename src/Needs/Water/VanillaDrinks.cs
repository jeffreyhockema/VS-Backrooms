using System;
using HarmonyLib;
using NeedsApi = Backrooms.Needs.Needs;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Backrooms.Worldgen;
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
                var fill = AccessTools.Method(typeof(BlockLiquidContainerBase), nameof(BlockLiquidContainerBase.TryFillFromBlock),
                    new[] { typeof(ItemSlot), typeof(EntityAgent), typeof(BlockPos) });
                if (fill != null) harmony.Patch(fill, prefix: new HarmonyMethod(typeof(VanillaDrinks), nameof(FillPrefix)), postfix: new HarmonyMethod(typeof(VanillaDrinks), nameof(FillPostfix)));
                else api.Logger.Warning("[backrooms] vanilla drinks: the fill hook was not found; bowls and buckets of world water are all clean");
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

    /// <summary>The stack attribute that says where the water in a vanilla container came from (a <see cref="WaterKind"/> as an int;
    /// absent means clean).</summary>
    public const string ClassKey = "backrooms:waterclass";

    private static int Rank(WaterKind k) => k switch { WaterKind.Tainted => 1, WaterKind.Salt => 2, WaterKind.Foul => 3, _ => 0 };

    /// <summary>The litres a container held before it was filled from a block.</summary>
    public static void FillPrefix(BlockLiquidContainerBase __instance, ItemSlot itemslot, out float __state)
    {
        __state = -1;
        try { if (itemslot?.Itemstack != null) __state = __instance.GetCurrentLitres(itemslot.Itemstack); } catch (Exception) { }
    }

    /// <summary>A container just filled from water in the world takes that water's class (the worst of it and what was already in it).
    /// Only a lone container is marked: the game splits one off a stack to fill it, and that one is not in the slot afterwards.</summary>
    public static void FillPostfix(BlockLiquidContainerBase __instance, ItemSlot itemslot, EntityAgent byEntity, BlockPos pos, float __state)
    {
        try
        {
            IWorldAccessor world = byEntity?.World;
            ItemStack stack = itemslot?.Itemstack;
            if (world == null || world.Side != EnumAppSide.Server || stack == null || pos == null || stack.StackSize != 1 || !NeedsApi.ThirstOn(world)) return;
            if (__instance.GetCurrentLitres(stack) <= __state) return;
            Block fluid = world.BlockAccessor.GetBlock(pos, BlockLayersAccess.Fluid);
            if (fluid == null || fluid.LiquidCode != "water" && fluid.LiquidCode != "saltwater") return;
            WorldLayout layout = null;
            try { layout = BackroomsWorld.IsBackroomsClimate(world.Config) ? BackroomsWorld.CreateLayout(world) : null; }
            catch (Exception) { /* plain water */ }
            WaterKind kind = WaterClass.Of(world, layout, fluid, pos);
            int was = __state > 0 ? stack.Attributes.GetInt(ClassKey, 0) : 0;
            int now = Rank(kind) > Rank((WaterKind)was) ? (int)kind : was;
            if (now == 0 || now == (int)WaterKind.Clean) stack.Attributes.RemoveAttribute(ClassKey);
            else stack.Attributes.SetInt(ClassKey, now);
            itemslot.MarkDirty();
        }
        catch (Exception e) { byEntity?.World?.Logger.Warning("[backrooms] vanilla drinks: could not record the water class ({0})", e.Message); }
    }

    /// <summary>What a container held before the sip: the liquid's code, the litres, and the class its water was filled as.</summary>
    public struct Before { public string Code; public float Litres; public WaterKind Kind; }

    public static void EatStopPrefix(BlockLiquidContainerBase __instance, ItemSlot slot, EntityAgent byEntity, out Before __state)
    {
        __state = default;
        if (byEntity?.World?.Side != EnumAppSide.Server || slot?.Itemstack == null || !NeedsApi.ThirstOn(byEntity.World)) return;
        ItemStack content = __instance.GetContent(slot.Itemstack);
        if (content == null) return;
        WaterKind kind = content.Collectible.Code.Path.StartsWith("waterportion") ? (WaterKind)slot.Itemstack.Attributes.GetInt(ClassKey, 0) : WaterKind.Clean;
        __state = new Before { Code = content.Collectible.Code.Path, Litres = __instance.GetCurrentLitres(slot.Itemstack), Kind = kind };
    }

    public static void EatStopPostfix(BlockLiquidContainerBase __instance, ItemSlot slot, EntityAgent byEntity, Before __state)
    {
        if (__state.Code == null || slot?.Itemstack == null) return;
        float taken = __state.Litres - __instance.GetCurrentLitres(slot.Itemstack);
        if (taken > 0) Sip(byEntity, __state.Code, taken, __state.Kind);
        // (Emptied: the next fill starts clean)
        if (__instance.GetCurrentLitres(slot.Itemstack) <= 0) slot.Itemstack.Attributes.RemoveAttribute(ClassKey);
    }

    /// <summary>Server: the drinker has taken <paramref name="litres"/> of a liquid (by its item code path). Water that was filled
    /// from a tainted, salt or foul source in the world has the effect that source has in <c>WaterSystem.Drink</c>, per litre.</summary>
    public static void Sip(Entity entity, string code, float litres, WaterKind kind = WaterKind.Clean)
    {
        if (litres <= 0) return;
        float perLitre = PerLitre(code);
        string message = null;
        if (code != null && code.StartsWith("waterportion"))
            switch (kind)
            {
                case WaterKind.Tainted:
                    perLitre = WaterClass.TaintedHydration;
                    Drinks.AddStability(entity, WaterClass.TaintedStability * litres);
                    if (entity.World.Rand.NextDouble() < WaterClass.SickChance * litres) NeedsApi.MakeSick(entity, WaterClass.SickHours);
                    message = "backrooms:drink-tainted";
                    break;
                case WaterKind.Salt:
                    perLitre = WaterClass.SaltHydration;
                    message = "backrooms:drink-salt";
                    break;
                case WaterKind.Foul:
                    perLitre = WaterClass.FoulHydration;
                    Drinks.AddStability(entity, WaterClass.TaintedStability * litres);
                    if (entity.World.Rand.NextDouble() < WaterClass.FoulSickChance * litres) NeedsApi.MakeSick(entity, WaterClass.SickHours);
                    message = "backrooms:drink-foul";
                    break;
            }
        if (perLitre != 0) NeedsApi.Hydrate(entity, perLitre * litres);
        if (message != null && (entity as EntityPlayer)?.Player is IServerPlayer sp)
            sp.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(sp, message), EnumChatType.Notification);
    }
}
