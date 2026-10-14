using System;
using System.Collections.Generic;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

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

    public override void StartServerSide(ICoreServerAPI api)
    {
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
