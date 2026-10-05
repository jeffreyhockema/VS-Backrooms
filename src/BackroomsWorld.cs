using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;

namespace Backrooms;

public static class BackroomsWorld
{
    public const string WorldTypeCode = "backrooms";

    /// <summary>Set as "worldClimate" in worldconfig.json. Unlike the world type, it is visible to clients.</summary>
    public const string ClimateCode = "backrooms";

    public static bool IsBackroomsClimate(ITreeAttribute worldConfig) => worldConfig?.GetString("worldClimate") == ClimateCode;

    /// <summary>
    /// The layout of this world. It is stateless and derived from the seed alone, so the server and every client
    /// can each build their own and always agree.
    /// </summary>
    public static WorldLayout CreateLayout(IWorldAccessor world)
    {
        IBlockAccessor blockAccessor = world.BlockAccessor;
        return new WorldLayout(world.Seed, WorldLayout.MacroOf(blockAccessor.MapSizeX / 2), WorldLayout.MacroOf(blockAccessor.MapSizeZ / 2));
    }

    public static WorldGeometry CreateGeometry(IWorldAccessor world) => new WorldGeometry(world.BlockAccessor.MapSizeY);
}
