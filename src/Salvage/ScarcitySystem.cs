using System;
using System.Collections.Generic;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Backrooms.Regions;

namespace Backrooms.Salvage;

/// <summary>
/// The world setting "backroomsScarcity": how much food the Backrooms leave lying about. On the server, once the world
/// is up, it scales the food and drink (anything with nutrition, Almond Water and the other drinks among them, and
/// flour) that every box, crate, cupboard and fridge of ours gives when broken; seeds and everything else are left
/// alone. The same multiplier (<see cref="FoodScale(ITreeAttribute)"/>) scales what dispensers hold and how fast they
/// restock (src/Props/Dispensers.cs), Level 974's fridge and pantry, Level 10's livestock (src/Deep/CreatureSystem.cs),
/// and, in worlds from layout version 7, thins the crops, vegetable patches and berry bushes of Levels 9 and 10 as
/// they are generated (WorldLayout.ThinFood; that one is fixed when the world is made, BackroomsWorld.WorldgenFoodScale,
/// while the rest follows the setting as it is now). Normal is the game as designed: scarce enough that scavenging matters.
/// </summary>
public class ScarcitySystem : ModSystem
{
    public const string ConfigKey = "backroomsScarcity";

    // (The codes are kept for good: worlds already made have "plentiful", "normal" or "sparse" in their config)
    private static readonly (string Code, float Food)[] Settings = { ("plentiful", 2f), ("normal", 1f), ("sparse", 0.6f), ("scarce", 0.33f) };

    /// <summary>The food multiplier of a world's config: 1 for Normal, or for a config without the setting.</summary>
    public static float FoodScale(ITreeAttribute config)
    {
        string code = config?.GetString(ConfigKey, "normal") ?? "normal";
        return Settings.FirstOrDefault(s => s.Code == code, Settings[1]).Food;
    }

    public static float FoodScale(IWorldAccessor world) => FoodScale(world?.Config);

    /// <summary>
    /// How much of its food and drink a level leaves lying about, by the lore's survival class (progression revision, decision 21):
    /// x1 in Classes 0 to 2, x0.7 in Class 3, x0.5 in Class 4, x0.35 in Class 5. Multiplied with <see cref="FoodScale(ITreeAttribute)"/>
    /// into what a broken supply box, crate or cache gives and what a dispenser holds when its stock is rolled (and restocked).
    /// Level 94 (Class 3), the Hub and Level 974 are exempt: their abundance is deliberate; the Snackrooms (inside Level 6) are Class 1.
    /// </summary>
    public static float ClassScale(int level)
    {
        if (level < 0 || level is Worldgen.WorldLayout.Motion or Worldgen.WorldLayout.Hub or Worldgen.WorldLayout.Level974) return 1f;
        return Worldgen.WorldLayout.SurvivalClass(level) switch { 3 => 0.7f, 4 => 0.5f, 5 => 0.35f, _ => 1f };
    }

    /// <summary><see cref="ClassScale(int)"/> of the level at a block position (1 outside a Backrooms world).</summary>
    public static float ClassScale(IWorldAccessor world, int x, int z) => ClassScale(ProtectionSystem.LevelAt(world, x, z));

    /// <summary>
    /// <paramref name="count"/> scaled by the world's food multiplier, rounded at random so the average is right (on
    /// Scarce, a dispenser that held 2 holds 1 now and then and nothing the rest of the time); at least
    /// <paramref name="min"/>.
    /// </summary>
    public static int Portions(IWorldAccessor world, double count, int min = 0) =>
        Math.Max(min, GameMath.RoundRandom(world.Rand, (float)(count * FoodScale(world))));

    /// <summary>What counts as food: anything with nutrition, eaten or in a meal, and flour; never seeds.</summary>
    public static bool IsFood(CollectibleObject thing)
    {
        if (thing?.Code == null) return false;
        string path = thing.Code.Path;
        if (path.StartsWith("seeds-") || path.StartsWith("treeseed-") || path.StartsWith("seedpacket-")) return false;
        return thing.NutritionProps != null || thing.Attributes?["nutritionPropsWhenInMeal"].Exists == true
            || thing.Code.Domain == "game" && path.StartsWith("flour-");
    }

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    private static TextCommandResult OnClassDropsCommand(ICoreServerAPI api, TextCommandCallingArgs args) =>
        ClassDrops(api, (string)args[0], (int)args[1], (int)args[2], (int)args[3]);

    /// <summary>The command's work, also used by the client rig (/backrooms rig classdrops) at the player's own position.</summary>
    internal static TextCommandResult ClassDrops(ICoreServerAPI api, string blockCode, int x, int z, int rollCount)
    {
        Block block = api.World.GetBlock(new AssetLocation("backrooms", blockCode));
        if (block == null) return TextCommandResult.Error("No such block: backrooms:" + blockCode);
        int rolls = Math.Clamp(rollCount, 1, 100000);
        var pos = new BlockPos(x, 1, z);
        var totals = new SortedDictionary<string, long>();
        for (int i = 0; i < rolls; i++)
            foreach (ItemStack stack in block.GetDrops(api.World, pos, null) ?? Array.Empty<ItemStack>())
                totals[stack.Collectible.Code.ToShortString()] = totals.GetValueOrDefault(stack.Collectible.Code.ToShortString()) + stack.StackSize;
        int level = ProtectionSystem.LevelAt(api.World, x, z);
        return TextCommandResult.Success($"{block.Code.Path} at {x},{z}: level {level}, class scale {ClassScale(level)}, food setting {FoodScale(api.World)}; average per roll over {rolls}: "
            + string.Join(", ", totals.Select(t => $"{t.Key} {t.Value / (double)rolls:0.000}")));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        // The per-class thinning: every block of ours that gives food or drink thins what it gives by the level it stands in
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            int blocks = 0;
            foreach (Block block in api.World.Blocks)
            {
                if (block?.Code?.Domain != "backrooms" || block.Drops == null) continue;
                var isFood = new bool[block.Drops.Length];
                bool any = false;
                for (int i = 0; i < isFood.Length; i++)
                {
                    BlockDropItemStack drop = block.Drops[i];
                    if (drop?.Code == null) continue;
                    CollectibleObject thing = drop.ResolvedItemstack?.Collectible
                        ?? (drop.Type == EnumItemClass.Item ? api.World.GetItem(drop.Code) : api.World.GetBlock(drop.Code));
                    if (IsFood(thing)) { isFood[i] = true; any = true; }
                }
                if (!any) continue;
                BehaviorInjection.Add(block, new BlockBehaviorClassScale(block, isFood));
                blocks++;
            }
            api.Logger.Notification("[backrooms] Scarcity by class: {0} block types thin their food and drink by the level's survival class", blocks);
        });
        // (Once the world is up: the /backrooms command is made by then, whatever order the systems start in)
        api.Event.ServerRunPhase(EnumServerRunPhase.GameReady, () => api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("classdrops")
                .WithDescription("Rolls a block's drops many times as if it stood at x, z (the level's survival class thins the food and drink) and lists the average of each. Args: block (e.g. supplybox), x, z, [rolls]")
                .RequiresPrivilege(Privilege.controlserver)
                .WithArgs(api.ChatCommands.Parsers.Word("block"), api.ChatCommands.Parsers.Int("x"), api.ChatCommands.Parsers.Int("z"), api.ChatCommands.Parsers.OptionalInt("rolls", 2000))
                .HandleWith(args => OnClassDropsCommand(api, args))
            .EndSubCommand());
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            string code = api.World.Config.GetString(ConfigKey, "normal");
            float food = FoodScale(api.World.Config);
            if (food == 1f) return;
            int changed = 0, blocks = 0;
            var scaled = new HashSet<BlockDropItemStack>(ReferenceEqualityComparer.Instance);
            var kinds = new SortedSet<string>();
            foreach (Block block in api.World.Blocks)
            {
                if (block?.Code?.Domain != "backrooms" || block.Drops == null) continue;
                bool any = false;
                foreach (BlockDropItemStack drop in block.Drops)
                {
                    if (drop?.Code == null || drop.Quantity == null || !scaled.Add(drop)) continue;
                    CollectibleObject thing = drop.ResolvedItemstack?.Collectible
                        ?? (drop.Type == EnumItemClass.Item ? api.World.GetItem(drop.Code) : api.World.GetBlock(drop.Code));
                    if (!IsFood(thing)) continue;
                    drop.Quantity = NatFloat.createUniform(drop.Quantity.avg * food, drop.Quantity.var * food);
                    kinds.Add(thing.Code.ToShortString());
                    changed++;
                    any = true;
                }
                if (any) blocks++;
            }
            api.Logger.Notification("[backrooms] Scarcity {0}: food in {1} drops of {2} blocks scaled by {3} ({4} kinds: {5})",
                code, changed, blocks, food, kinds.Count, string.Join(", ", kinds));
        });
    }
}

/// <summary>
/// Thins the food and drink a block gives when broken by the survival class of the level it stands in
/// (<see cref="ScarcitySystem.ClassScale(int)"/>); everything else it gives is as it was. Added to every block of ours with
/// food among its drops when the world starts. In Classes 0 to 2 (and the exempt levels) it does nothing.
/// </summary>
public class BlockBehaviorClassScale : BlockBehavior
{
    private readonly bool[] isFood;

    public BlockBehaviorClassScale(Block block, bool[] isFood) : base(block)
    {
        this.isFood = isFood;
    }

    public override ItemStack[] GetDrops(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, ref float dropQuantityMultiplier, ref EnumHandling handling)
    {
        float scale = ScarcitySystem.ClassScale(world, pos.X, pos.Z);
        BlockDropItemStack[] drops = block.Drops;
        if (scale >= 1f || drops == null) return null;
        // (As Block.GetDrops rolls them, with the food entries' multiplier thinned; the other behaviours' drops are added by the caller)
        var rolled = new List<ItemStack>();
        for (int i = 0; i < drops.Length; i++)
        {
            ItemStack stack = drops[i].ToRandomItemstackForPlayer(byPlayer, world, dropQuantityMultiplier * (i < isFood.Length && isFood[i] ? scale : 1f));
            if (stack == null) continue;
            rolled.Add(stack);
            if (drops[i].LastDrop) break;
        }
        handling = EnumHandling.PreventDefault;
        return rolled.ToArray();
    }
}
