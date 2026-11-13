using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using Backrooms.Entities;
using Backrooms.Needs.Water;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Cheats;

/// <summary>
/// Dev tests of the 2026-11 feedback round's small package (headless, from the console):
/// <c>smalltest ore &lt;level&gt; [sites] [radius]</c> counts the ore blocks round some spots of a level (the borax of Level 8 and the rest);
/// <c>smalltest sip &lt;liquid code&gt; [sips]</c> has the first straw dummy drink a bowl or jug of a vanilla liquid through the
/// game's own drinking code (with the vanilla drinks patch in place) and reports the water bar before and after.
/// </summary>
public partial class CheatSystem
{
    private void RegisterSmallTests(IChatCommand command, CommandArgumentParsers parsers)
    {
        command
            .BeginSubCommand("smalltest")
                .WithDescription("Dev test: 'ore <level> [sites] [radius]' counts ore blocks (borax) round some spots of a level (the first try loads chunks); 'sip <liquid code> [sips] [container]' has the first straw dummy drink a liquid from a bowl through the game's drinking code and reports its hydration")
                .WithArgs(parsers.Word("what"), parsers.OptionalWord("a"), parsers.OptionalInt("b", -1), parsers.OptionalInt("c", -1), parsers.OptionalWord("ignored"))
                .HandleWith(OnSmallTest)
            .EndSubCommand();
    }

    private TextCommandResult OnSmallTest(TextCommandCallingArgs args)
    {
        string what = ((string)args[0]).ToLowerInvariant();
        string a = (args[1] as string ?? "").Trim();
        int b = (int)args[2], c = (int)args[3];
        return what switch
        {
            "ore" => SmallOre(a, b, c),
            "sip" => SmallSip(a, b, args[4] as string),
            _ => TextCommandResult.Error("ore or sip"),
        };
    }

    private TextCommandResult SmallOre(string levelText, int sites, int radius)
    {
        if (layout == null) return TextCommandResult.Error("This is not a Backrooms world");
        int level = WorldLayout.FromDisplayName(levelText);
        if (level < 0) return TextCommandResult.Error("no such level");
        sites = Math.Clamp(sites > 0 ? sites : 4, 1, 24);
        radius = Math.Clamp(radius > 0 ? radius : 48, 8, 128);
        var spots = StairScanSites(level, sites, radius);
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int probeY = geometry.FloorFor(level) + 1;
        var columns = new HashSet<(int, int)>();
        foreach (var (sx, sz) in spots)
            for (int cz = (sz - radius - 1) >> 5; cz <= (sz + radius + 1) >> 5; cz++)
                for (int cx = (sx - radius - 1) >> 5; cx <= (sx + radius + 1) >> 5; cx++) columns.Add((cx, cz));
        int notReady = 0;
        foreach (var (cx, cz) in columns)
        {
            if (ba.GetChunkAtBlockPos(cx * 32 + 1, probeY, cz * 32 + 1) != null) continue;
            sapi.WorldManager.LoadChunkColumn(cx, cz, true);
            notReady++;
        }
        if (notReady > 0) return TextCommandResult.Success($"smalltest ore: {notReady} of {columns.Count} chunk columns are loading; run it again in a moment");
        var counts = new SortedDictionary<string, int>();
        long total = 0, rock = 0;
        var pos = new BlockPos(0);
        int ceiling = sapi.WorldManager.MapSizeY;
        foreach (var (sx, sz) in spots)
            for (int x = sx - radius; x <= sx + radius; x++)
                for (int z = sz - radius; z <= sz + radius; z++)
                    for (int y = 1; y < ceiling; y++)
                    {
                        pos.Set(x, y, z);
                        Block block = ba.GetBlock(pos);
                        if (block.Id == 0) continue;
                        string path = block.Code.Path;
                        if (path.StartsWith("rock-")) { rock++; continue; }
                        if (!path.StartsWith("ore-") && !path.StartsWith("looseores-")) continue;
                        total++;
                        string family = path.StartsWith("ore-borax") ? "borax" : "other";
                        counts[family] = counts.GetValueOrDefault(family) + 1;
                        if (family == "borax") counts[path] = counts.GetValueOrDefault(path) + 1;
                    }
        string line = $"smalltest ore: Level {levelText}, {spots.Length} sites of radius {radius}, layout version {layout.Version}: rock {rock}, ore {total}; "
            + string.Join(", ", counts.Select(k => $"{k.Key} {k.Value}"));
        sapi.Logger.Notification("[backrooms] " + line);
        return TextCommandResult.Success(line);
    }

    private TextCommandResult SmallSip(string liquid, int sips, string container)
    {
        var menace = sapi.ModLoader.GetModSystem<MenaceSystem>();
        Entity dummy = menace?.LivingDummies.FirstOrDefault();
        if (dummy == null) return TextCommandResult.Error("Put a straw dummy down first (/backrooms dummy place ...)");
        if (liquid.Length == 0) return TextCommandResult.Error("Give the liquid's item code, e.g. waterportion, juiceportion-apple, milkportion");
        container = string.IsNullOrWhiteSpace(container) ? "bowl-blue-fired" : container;
        var block = sapi.World.GetBlock(new AssetLocation("game", container)) as BlockLiquidContainerBase;
        Item item = sapi.World.GetItem(new AssetLocation("game", liquid));
        if (block == null || item == null) return TextCommandResult.Error($"No such container or liquid: {container}, {liquid}");
        sips = Math.Clamp(sips, 1, 20);
        var stack = new ItemStack(block);
        block.TryPutLiquid(stack, new ItemStack(item, 100000), block.CapacityLitres);
        float litres = block.GetCurrentLitres(stack);
        var slot = new DummySlot(stack);
        EntityAgent agent = (EntityAgent)dummy;
        Backrooms.Needs.Needs.SetHydration(dummy, 0);
        var nutrition = block.GetNutritionPropertiesPerLitre(sapi.World, stack, dummy);
        MethodInfo stop = typeof(BlockLiquidContainerBase).GetMethod("tryEatStop", BindingFlags.Instance | BindingFlags.NonPublic);
        float portion = block.DrinkPortionSize;
        int done = 0;
        for (; done < sips && block.GetCurrentLitres(slot.Itemstack) > 0.0001f; done++) stop.Invoke(block, new object[] { 1f, slot, agent });
        float left = slot.Itemstack == null ? 0 : block.GetCurrentLitres(slot.Itemstack);
        float hydration = Backrooms.Needs.Needs.Hydration(dummy);
        string result = string.Create(CultureInfo.InvariantCulture,
            $"smalltest sip: {container} of {liquid} ({litres:0.##} L, drinkable {(nutrition != null ? "yes" : "no")}, sip {portion:0.###} L, table {VanillaDrinks.PerLitre(liquid)}/L): {done} sips took {litres - left:0.###} L, hydration 0 -> {hydration:0.#} of {Backrooms.Needs.Needs.MaxHydration}");
        sapi.Logger.Notification("[backrooms] " + result);
        return TextCommandResult.Success(result);
    }
}
