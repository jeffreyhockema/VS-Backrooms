using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.Server;

namespace Backrooms;

public static class BackroomsWorld
{
    public const string WorldTypeCode = "backrooms";

    /// <summary>Set as "worldClimate" in worldconfig.json. Unlike the world type, it is visible to clients.</summary>
    public const string ClimateCode = "backrooms";

    public static bool IsBackroomsClimate(ITreeAttribute worldConfig) => worldConfig?.GetString("worldClimate") == ClimateCode;

    /// <summary>World config key (synced to clients) holding the layout version the world was made with.</summary>
    public const string LayoutVersionKey = "backroomsLayoutVersion";

    /// <summary>
    /// The layout of this world. It is stateless and derived from the seed, the layout version and the world's Backrooms
    /// scarcity alone (all in the world config, which clients are sent), so the server and every client can each build
    /// their own and always agree.
    /// </summary>
    public static WorldLayout CreateLayout(IWorldAccessor world)
    {
        IBlockAccessor blockAccessor = world.BlockAccessor;
        return new WorldLayout(world.Seed, WorldLayout.MacroOf(blockAccessor.MapSizeX / 2), WorldLayout.MacroOf(blockAccessor.MapSizeZ / 2), LayoutVersion(world),
            Salvage.ScarcitySystem.FoodScale(world));
    }

    /// <summary>
    /// The layout version this world was made with (see <see cref="WorldLayout.CurrentVersion"/>). The server writes it
    /// into the world config the first time it is asked: a new world gets the current version, a world made before
    /// versions were kept gets 1. The config is saved with the world and sent to clients, so both sides agree.
    /// </summary>
    public static int LayoutVersion(IWorldAccessor world)
    {
        ITreeAttribute config = world.Config;
        if (config == null) return 1;
        if (world.Api is ICoreServerAPI sapi && sapi.WorldManager.SaveGame.WorldType == WorldTypeCode && !config.HasAttribute(LayoutVersionKey))
        {
            int version = sapi.WorldManager.SaveGame.IsNew ? WorldLayout.CurrentVersion : 1;
            config.SetInt(LayoutVersionKey, version);
            sapi.Logger.Notification("[backrooms] layout version {0} ({1} world)", version, version == 1 ? "existing" : "new");
        }
        return config.GetInt(LayoutVersionKey, 1);
    }

    public static WorldGeometry CreateGeometry(IWorldAccessor world) => new WorldGeometry(world.BlockAccessor.MapSizeY);
}
