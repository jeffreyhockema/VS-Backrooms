using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Map;

/// <summary>
/// Swaps the vanilla terrain map layer for <see cref="BackroomsMapLayer"/> in Backrooms worlds, and carries out the
/// map setting (<see cref="MapSetting"/>) on the server.
/// </summary>
public class BackroomsMapSystem : ModSystem
{
    /// <summary>Save data: whether the server turned vanilla's "allowMap" off for the None setting (so it can turn it back on).</summary>
    private const string MapOffKey = "backrooms-mapoff";

    /// <summary>How much more chalk crumbled ceilings and backpacks give in a world with no map.</summary>
    private const float MaplessChalk = 1.5f;

    // Must start before WorldMapManager (0.1) so our LevelFinalize handler runs before it creates the layers
    public override double ExecuteOrder() => 0.05;

    public override void StartClientSide(ICoreClientAPI api)
    {
        api.Event.LevelFinalize += () =>
        {
            if (!BackroomsWorld.IsBackroomsClimate(api.World.Config)) return;
            // (Even with no map: the layer then sits idle, where vanilla's would go on drawing the roof)
            api.ModLoader.GetModSystem<WorldMapManager>().MapLayerRegistry["chunks"] = typeof(BackroomsMapLayer);
        };
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        // Before anyone joins: the world config goes to each client as it connects
        api.Event.SaveGameLoaded += () => ApplyAllowMap(api);
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () => MoreChalk(api));
    }

    /// <summary>
    /// None turns vanilla's "allowMap" off: no map, no minimap, no map keys, no waypoint commands. Set back to another
    /// setting (with /worldconfig and a restart), the map comes back, unless it was off before the setting turned it off.
    /// </summary>
    private static void ApplyAllowMap(ICoreServerAPI api)
    {
        ISaveGame save = api.WorldManager.SaveGame;
        if (save.WorldType != BackroomsWorld.WorldTypeCode) return;
        ITreeAttribute config = api.World.Config;
        bool none = MapSetting.Of(config) == MapSetting.Mode.None, turnedOff = save.GetData(MapOffKey, false);
        if (none && config.GetBool("allowMap", true))
        {
            config.SetBool("allowMap", false);
            save.StoreData(MapOffKey, true);
            api.Logger.Notification("[backrooms] Map setting none: the world map is off");
        }
        else if (!none && turnedOff)
        {
            config.SetBool("allowMap", true);
            save.StoreData(MapOffKey, false);
            api.Logger.Notification("[backrooms] Map setting {0}: the world map is back on", config.GetString(MapSetting.Code, "seen"));
        }
    }

    /// <summary>With no map, chalk is what you find your way by: a little more of it in the ceilings and backpacks.</summary>
    private static void MoreChalk(ICoreServerAPI api)
    {
        if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode || MapSetting.Of(api.World.Config) != MapSetting.Mode.None) return;
        int changed = 0;
        foreach (Block block in api.World.Blocks)
        {
            if (block?.Code?.Domain != "backrooms" || block.Drops == null) continue;
            foreach (BlockDropItemStack drop in block.Drops)
            {
                if (drop?.Code == null || drop.Code.Domain != "backrooms" || drop.Code.Path != "chalk" || drop.Quantity.avg >= 1) continue;
                drop.Quantity = NatFloat.createUniform(drop.Quantity.avg * MaplessChalk, drop.Quantity.var * MaplessChalk);
                changed++;
            }
        }
        api.Logger.Notification("[backrooms] Map setting none: chalk in {0} drops scaled by {1}", changed, MaplessChalk);
    }
}
