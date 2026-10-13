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

    /// <summary>Save data: whether the server turned vanilla's "allowDeathwaypointing" off for a setting without waypoints.</summary>
    private const string DeathWaypointOffKey = "backrooms-deathwpoff";

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
    /// No waypoints and None also turn off vanilla's own death waypoint ("You died here"), with its world config
    /// "allowDeathwaypointing" (vanilla's WaypointMapLayer checks it at each death; a player's own choice, /waypoint
    /// deathwp, is player mod data and is left alone), and turn it back on in the same way.
    /// </summary>
    private static void ApplyAllowMap(ICoreServerAPI api)
    {
        ISaveGame save = api.WorldManager.SaveGame;
        if (save.WorldType != BackroomsWorld.WorldTypeCode) return;
        MapSetting.Mode mode = MapSetting.Of(api.World.Config);
        Apply(api, "allowMap", MapOffKey, mode == MapSetting.Mode.None, "the world map");
        Apply(api, "allowDeathwaypointing", DeathWaypointOffKey, mode != MapSetting.Mode.Seen, "vanilla's death waypoint");
    }

    /// <summary>
    /// Turns a vanilla world config flag off while the map setting wants it off, and back on once it no longer does, but
    /// only if it was this that turned it off (<paramref name="saveKey"/> remembers).
    /// </summary>
    private static void Apply(ICoreServerAPI api, string flag, string saveKey, bool off, string what)
    {
        ISaveGame save = api.WorldManager.SaveGame;
        ITreeAttribute config = api.World.Config;
        string setting = config.GetString(MapSetting.Code, "seen");
        if (off && config.GetBool(flag, true))
        {
            config.SetBool(flag, false);
            save.StoreData(saveKey, true);
            api.Logger.Notification("[backrooms] Map setting {0}: {1} is off", setting, what);
        }
        else if (!off && save.GetData(saveKey, false))
        {
            config.SetBool(flag, true);
            save.StoreData(saveKey, false);
            api.Logger.Notification("[backrooms] Map setting {0}: {1} is back on", setting, what);
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
