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
    /// World config key (synced to clients) holding the food multiplier the world's crops are thinned by at worldgen
    /// (see <see cref="WorldgenFoodScale"/>).
    /// </summary>
    public const string WorldgenFoodKey = "backroomsWorldgenFood";

    /// <summary>
    /// The world setting "Level size" (worldconfig.json), chosen when the world is made: how wide the levels' rings are,
    /// in percent of the usual ("50" to "200"; see <see cref="LevelSizes"/>). Only its value at creation counts (see
    /// <see cref="RingScale"/>).
    /// </summary>
    public const string LevelSizeCode = "backroomsLevelSize";

    /// <summary>
    /// World config key (synced to clients) holding the Level size the world was made with, in percent (see
    /// <see cref="RingScale"/>).
    /// </summary>
    public const string LayoutLevelSizeKey = "backroomsLayoutLevelSize";

    /// <summary>The Level size setting's choices, in percent of the usual ring widths.</summary>
    public static readonly int[] LevelSizes = { 50, 75, 100, 150, 200 };

    /// <summary>One shared layout and the arguments it was built from, so a changed config (a client still waiting for it) builds a fresh one.</summary>
    private sealed class SharedLayout
    {
        public readonly (long Seed, int MacroX, int MacroZ, int Version, double Food, double Rings) Args;
        public readonly WorldLayout Layout;
        public SharedLayout((long, int, int, int, double, double) args, WorldLayout layout) { Args = args; Layout = layout; }
    }

    private static readonly System.Runtime.CompilerServices.ConditionalWeakTable<IWorldAccessor, SharedLayout> sharedLayouts = new();

    /// <summary>
    /// The layout of this world. It is stateless and derived from the seed, the layout version, the worldgen food
    /// scale and the ring scale alone (all in the world config, which clients are sent), so the server and every
    /// client can each build their own and always agree. Every system of one world (server or client side) is handed the
    /// same instance, so its cell and plan caches are filled once, not once per system; its caches are thread-safe and
    /// callers only read it. A new instance is built only if one of those arguments changed since it was made.
    /// </summary>
    public static WorldLayout CreateLayout(IWorldAccessor world)
    {
        IBlockAccessor blockAccessor = world.BlockAccessor;
        var args = (world.Seed, WorldLayout.MacroOf(blockAccessor.MapSizeX / 2), WorldLayout.MacroOf(blockAccessor.MapSizeZ / 2), LayoutVersion(world),
            WorldgenFoodScale(world), RingScale(world));
        lock (sharedLayouts)
        {
            if (sharedLayouts.TryGetValue(world, out SharedLayout shared) && shared.Args.Equals(args)) return shared.Layout;
            var layout = new WorldLayout(world.Seed, args.Item2, args.Item3, args.Item4, args.Item5, args.Item6);
            sharedLayouts.AddOrUpdate(world, new SharedLayout(args, layout));
            return layout;
        }
    }

    /// <summary>
    /// How wide this world's rings are against the usual (WorldLayout.RingScale): its Level size setting as it was when
    /// the world was made. Like the layout version it is fixed for good, since chunks are generated as they are first
    /// reached and must go on matching the ones already there: the server writes it into the world config (as a percent,
    /// <see cref="LayoutLevelSizeKey"/>) the first time it is asked, the setting's value in a new world and 100 in a
    /// world made before the setting (or before this was kept), so changing the setting afterwards changes nothing.
    /// </summary>
    public static double RingScale(IWorldAccessor world)
    {
        ITreeAttribute config = world.Config;
        if (config == null) return 1;
        if (world.Api is ICoreServerAPI sapi && sapi.WorldManager.SaveGame.WorldType == WorldTypeCode && !config.HasAttribute(LayoutLevelSizeKey))
        {
            bool isNew = sapi.WorldManager.SaveGame.IsNew;
            int percent = isNew ? LevelSizeSetting(config) : 100;
            config.SetInt(LayoutLevelSizeKey, percent);
            sapi.Logger.Notification("[backrooms] level size {0}% ({1} world)", percent, isNew ? "new" : "existing");
        }
        return config.GetInt(LayoutLevelSizeKey, 100) / 100.0;
    }

    /// <summary>The Level size setting as it stands, in percent: one of <see cref="LevelSizes"/>, 100 if it is unset or anything else.</summary>
    public static int LevelSizeSetting(ITreeAttribute config)
    {
        string value = config?[LevelSizeCode]?.GetValue()?.ToString();
        return int.TryParse(value, System.Globalization.NumberStyles.Integer, System.Globalization.CultureInfo.InvariantCulture, out int percent)
            && System.Array.IndexOf(LevelSizes, percent) >= 0 ? percent : 100;
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

    /// <summary>
    /// The food multiplier this world's layout thins Level 9 and 10's crops by (WorldLayout.FoodScale, from layout
    /// version 7). Unlike the live Backrooms scarcity, which goes on scaling drops, dispensers and livestock, it is fixed
    /// so that chunks generated after the setting is changed match the ones already there: the server writes the world's
    /// scarcity multiplier into the world config the first time it is asked (in a new world, or in a version 7 world made
    /// before it was kept, where the setting it has now is the best guess). Worlds before version 7 never thin: they get
    /// 1, and nothing is written.
    /// </summary>
    public static double WorldgenFoodScale(IWorldAccessor world)
    {
        ITreeAttribute config = world.Config;
        if (config == null || LayoutVersion(world) < 7) return 1;
        if (world.Api is ICoreServerAPI sapi && sapi.WorldManager.SaveGame.WorldType == WorldTypeCode && !config.HasAttribute(WorldgenFoodKey))
        {
            config.SetFloat(WorldgenFoodKey, Salvage.ScarcitySystem.FoodScale(config));
            sapi.Logger.Notification("[backrooms] worldgen food scale {0} recorded ({1} world)", config.GetFloat(WorldgenFoodKey),
                sapi.WorldManager.SaveGame.IsNew ? "new" : "existing");
        }
        return config.GetFloat(WorldgenFoodKey, Salvage.ScarcitySystem.FoodScale(config));
    }

    public static WorldGeometry CreateGeometry(IWorldAccessor world) => new WorldGeometry(world.BlockAccessor.MapSizeY);
}
