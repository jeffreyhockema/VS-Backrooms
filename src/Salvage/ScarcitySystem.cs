using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Salvage;

/// <summary>
/// The world setting "backroomsScarcity": how much food the Backrooms leave lying about. It scales the food (and
/// Almond Water) that every box, crate, cupboard and fridge of ours gives when broken, on the server, once the world
/// is up. Normal is the game as designed: scarce enough that scavenging matters.
/// </summary>
public class ScarcitySystem : ModSystem
{
    private static readonly (string Code, float Food)[] Settings = { ("plentiful", 2f), ("normal", 1f), ("sparse", 0.6f) };

    /// <summary>Our foods and drinks, and the vanilla ones our furniture holds.</summary>
    private static bool IsFood(AssetLocation code) =>
        code.Domain == "backrooms" && code.Path is "almondwater" or "crackers" or "cannedbeans" or "chips" or "candybar" or "soda" or "waterbottle" or "cashewwater"
        || code.Domain == "game" && (code.Path.StartsWith("fruit-") || code.Path.StartsWith("cheese-") || code.Path.StartsWith("flour-") || code.Path == "honeycomb");

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            string code = api.World.Config.GetString("backroomsScarcity", "normal");
            float food = Settings.FirstOrDefault(s => s.Code == code, Settings[1]).Food;
            if (food == 1f) return;
            int changed = 0;
            foreach (Block block in api.World.Blocks)
            {
                if (block?.Code?.Domain != "backrooms" || block.Drops == null) continue;
                foreach (BlockDropItemStack drop in block.Drops)
                {
                    if (drop?.Code == null || !IsFood(drop.Code)) continue;
                    drop.Quantity = NatFloat.createUniform(drop.Quantity.avg * food, drop.Quantity.var * food);
                    changed++;
                }
            }
            api.Logger.Notification("[backrooms] Scarcity {0}: food in {1} drops scaled by {2}", code, changed, food);
        });
    }
}
