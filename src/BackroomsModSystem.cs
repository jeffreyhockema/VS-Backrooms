using System;
using System.Linq;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;
using Vintagestory.GameContent;
using Backrooms.Worldgen;

namespace Backrooms;

/// <summary>
/// Hooks the generator passes into worlds of the Backrooms world type (declared in worldconfig.json, not here).
/// Vanilla terrain, climate, vegetation and creature generators only run for the "standard" and "superflat" world
/// types, so a world created with the Backrooms playstyle gets nothing but what this system generates. It also sets
/// the indoor climate, sea level and spawn, registers the shared oriented-block behaviour (see <see cref="Start"/>)
/// and owns the <c>/backrooms</c> command that the other systems add their subcommands to.
/// </summary>
public class BackroomsModSystem : ModSystem
{
    /// <summary>Level 0's temperature, used for the climate maps and on the client (which only needs it for visuals).</summary>
    private const float LobbyTemperature = 22f;
    private const float TintTemperature = 15f;
    private const int TintRainfall = 190;
    /// <summary>
    /// Motion's grass and leaves: hot enough that vanilla's seasonal tint drops out altogether (it yellows a milder
    /// climate's grass), and wet, so they take the deep green corner of the plant tint map and match the clay turf.
    /// </summary>
    private const float MotionTintTemperature = 30f;
    private const int MotionTintRainfall = 195;
    /// <summary>
    /// Level 10's fields, hedges and meadows: an overcast English or Midwest farm, wet and deep green rather than lime.
    /// Hot on paper (again so the seasonal yellowing drops out) and very wet, the darkest greens of the plant tint map;
    /// the rainfall wanders a little from cell to cell, so the meadows lie in broad patches of slightly different greens.
    /// </summary>
    private const float FarmTintTemperature = 37f;
    private const int FarmTintRainfall = 198, FarmTintRainfallSpread = 18;

    /// <summary>The levels <c>/backrooms goto</c> (and the other commands that take a level) accept, for their descriptions and errors.</summary>
    public const string LevelList = "0-11, 37, 94, !, fun, end, hub, 974, 3999 or 188";

    private ICoreServerAPI sapi;
    /// <summary>
    /// The one block accessor the game hands out for worldgen. The game calls the provider callback once, and
    /// <c>GetBlockAccessor(false)</c> returns the same cached instance to every caller (vanilla's own passes share it
    /// as well); it is safe to use from the TerrainFeatures and Vegetation passes on different worldgen threads
    /// because the column state <c>BeginColumn</c> resets lives in [ThreadStatic] fields, not on the instance.
    /// </summary>
    private IWorldGenBlockAccessor worldgenBlockAccessor;
    // layout and generator are assigned before the flag, and all three are volatile because the climate callbacks
    // read them from any thread
    private volatile WorldLayout layout;
    private volatile WorldGenerator generator;
    private volatile bool isBackroomsWorld;

    /// <summary>The world's generator (server side, in a Backrooms world): Level ! puts its lanes back as they were with it.</summary>
    public WorldGenerator Generator => generator;

    private ICoreClientAPI capi;
    /// <summary>0 = not known yet, 1 = a Backrooms world, 2 = another world. Resolved on the main thread when the level finalizes, read by the climate callback on any thread.</summary>
    private volatile int clientWorldKind;

    /// <summary>
    /// The Mangled's fog round this client's player, copied from its watched attributes on the main thread.
    /// Climate is asked for off the main thread too (particles, tesselation), where the attribute tree must not be read.
    /// </summary>
    private volatile float clientMangledFog;
    private long clientFogListener;

    // Run after the weather systems so our climate override has the final say
    public override double ExecuteOrder() => 1.0;

    /// <summary>
    /// Registers <c>BlockBehaviorOrientable</c> as "BackroomsHorizontalOrientable" (the name block JSON refers to; do
    /// not rename it): any block with a hyphen in its base code and a <c>facing</c> variant uses it, not only Level 3999's.
    /// </summary>
    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsHorizontalOrientable", typeof(BlockBehaviorOrientable));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, OnModsAndConfigReady);
        api.Event.GetWorldgenBlockAccessor(provider => worldgenBlockAccessor = provider.GetBlockAccessor(updateHeightmap: false));
        api.Event.MapRegionGeneration(OnMapRegionGen, BackroomsWorld.WorldTypeCode);
        api.Event.ChunkColumnGeneration(OnTerrainPass, EnumWorldGenPass.Terrain, BackroomsWorld.WorldTypeCode);
        api.Event.ChunkColumnGeneration(OnFeaturesPass, EnumWorldGenPass.TerrainFeatures, BackroomsWorld.WorldTypeCode);
        api.Event.ChunkColumnGeneration(OnLightPass, EnumWorldGenPass.Vegetation, BackroomsWorld.WorldTypeCode);
        api.Event.ChunkColumnGeneration(OnNeighbourLightPass, EnumWorldGenPass.NeighbourSunLightFlood, BackroomsWorld.WorldTypeCode);
        api.Event.OnGetClimate += OnGetClimateServer;
        api.Event.PlayerCreate += OnPlayerCreate;

        api.ChatCommands.Create("backrooms")
            .WithDescription("Backrooms debug tools")
            .RequiresPrivilege(Privilege.controlserver)
            .BeginSubCommand("column")
                .WithDescription("Lists the blocks and light levels in a column of Level 0. Defaults to your position, or the spawn point from the server console.")
                .WithArgs(api.ChatCommands.Parsers.OptionalInt("x"), api.ChatCommands.Parsers.OptionalInt("z"))
                .HandleWith(OnColumnCommand)
            .EndSubCommand()
            .BeginSubCommand("goto")
                .WithDescription("Teleports you into a level (" + LevelList + ")")
                .RequiresPlayer()
                .WithArgs(api.ChatCommands.Parsers.Word("level"))
                .HandleWith(OnGotoCommand)
            .EndSubCommand()
            .BeginSubCommand("shift")
                .WithDescription("Starts a Reality Shift lasting the given number of in-game hours (default 2, 0 ends it)")
                .WithArgs(api.ChatCommands.Parsers.OptionalDouble("hours"))
                .HandleWith(OnShiftCommand)
            .EndSubCommand()
            .BeginSubCommand("where")
                .WithDescription("Names the level you are in (and the Level 0 zone) and its stability")
                .RequiresPlayer()
                .HandleWith(OnWhereCommand)
            .EndSubCommand()
            .BeginSubCommand("dump")
                .WithDescription("Writes the blocks and light of a square of the world round x, z to a file, for rendering previews outside the game")
                .WithArgs(api.ChatCommands.Parsers.Int("x"), api.ChatCommands.Parsers.Int("z"), api.ChatCommands.Parsers.OptionalInt("radius", 24))
                .HandleWith(OnDumpCommand)
            .EndSubCommand();
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Event.OnGetClimate += OnGetClimateClient;
        // The world config arrives from the server after StartClientSide; resolve the world kind here, on the main
        // thread, so the climate callback (any thread) never reads the config's attribute tree
        api.Event.LevelFinalize += () => clientWorldKind = BackroomsWorld.IsBackroomsClimate(capi.World.Config) ? 1 : 2;
        clientFogListener = api.Event.RegisterGameTickListener(_ =>
        {
            if (clientWorldKind != 1) return;
            clientMangledFog = capi.World.Player?.Entity?.WatchedAttributes.GetFloat(Entities.MangledEvent.FogKey) ?? 0f;
        }, 250);
    }

    public override void Dispose()
    {
        if (sapi != null) sapi.Event.OnGetClimate -= OnGetClimateServer;
        if (capi != null)
        {
            capi.Event.OnGetClimate -= OnGetClimateClient;
            capi.Event.UnregisterGameTickListener(clientFogListener);
        }
        base.Dispose();
    }

    private void OnModsAndConfigReady()
    {
        ISaveGame save = sapi.WorldManager.SaveGame;
        if (save.WorldType != BackroomsWorld.WorldTypeCode) return;

        // The only creatures in the Backrooms will be ones this mod spawns
        save.EntitySpawning = false;
        // Clients tell a Backrooms world by its climate setting (they are not sent the world type). It is offered in
        // the world settings as a choice, so make sure it was not changed
        if (sapi.World.Config.GetString("worldClimate") != BackroomsWorld.ClimateCode)
        {
            sapi.World.Config.SetString("worldClimate", BackroomsWorld.ClimateCode);
            sapi.Logger.Notification("[backrooms] worldClimate was changed; set back to {0}", BackroomsWorld.ClimateCode);
        }

        // Anchor the maze to the map centre rather than the current spawn point, so moving the spawn later
        // (e.g. /setspawn) can never change the layout of chunks that are not generated yet
        int spawnMacroX = WorldLayout.MacroOf(sapi.WorldManager.MapSizeX / 2);
        int spawnMacroZ = WorldLayout.MacroOf(sapi.WorldManager.MapSizeZ / 2);
        layout = new WorldLayout(sapi.WorldManager.Seed, spawnMacroX, spawnMacroZ, BackroomsWorld.LayoutVersion(sapi.World),
            BackroomsWorld.WorldgenFoodScale(sapi.World), BackroomsWorld.RingScale(sapi.World));
        if (layout.Version >= 7)
            sapi.Logger.Notification("[backrooms] Worldgen thins crops by {0} (fixed for this world); scarcity {1} scales food by {2}",
                (float)layout.FoodScale, sapi.World.Config.GetString(Salvage.ScarcitySystem.ConfigKey, "normal"), Salvage.ScarcitySystem.FoodScale(sapi.World));
        if (layout.RingScale != 1 || BackroomsWorld.LevelSizeSetting(sapi.World.Config) != 100)
            sapi.Logger.Notification("[backrooms] Level size {0}% (fixed for this world; the setting now reads {1}%)",
                (int)Math.Round(layout.RingScale * 100), BackroomsWorld.LevelSizeSetting(sapi.World.Config));
        generator = new WorldGenerator(sapi, layout);
        // (Last: the climate callbacks take the flag to mean that layout and generator exist)
        isBackroomsWorld = true;

        // Y coordinates on the HUD are shown relative to sea level, so this makes the Level 0 floor read as y=0
        sapi.WorldManager.SetSeaLevel(generator.Geometry.FloorY);

        if (save.DefaultSpawn == null)
        {
            (int x, int z) = layout.FindSpawn();
            save.DefaultSpawn = new PlayerSpawnPos { x = x, y = generator.Geometry.FloorY + 1, z = z };
        }
    }

    private void OnMapRegionGen(IMapRegion mapRegion, int regionX, int regionZ, ITreeAttribute chunkGenParams)
    {
        // Vanilla code expects these maps to exist. Fill them with a constant mild climate and no vegetation.
        // The climate map only tints grass and leaves here (rain and temperature come from OnGetClimate): mild and
        // moist, so the Suburbs' lawns are green rather than parched (Motion's and Level 10's own regions get a map of
        // their own: LevelTintMap)
        int climate = (Climate.DescaleTemperature(TintTemperature) << 16) | (TintRainfall << 8) | 0;
        int size = sapi.WorldManager.RegionSize;
        mapRegion.ClimateMap = LevelTintMap(regionX, regionZ, size, climate) ?? ConstantMap(climate);
        mapRegion.ForestMap = ConstantMap(0);
        mapRegion.ShrubMap = ConstantMap(0);
    }

    /// <summary>
    /// A region with some of Motion, Level 10 or the Poolrooms in it: a climate map one cell per macro cell, that level's
    /// tint in its cells and the region's own everywhere else, or null for a region with none of them. The game lerps each cell towards
    /// the cells east and south of it, so a cell only takes a level's tint when the cells west, north and north-west of
    /// it are that level as well: the blend then happens inside the level, and no other level's grass is ever tinted by it.
    /// The Poolrooms' tint is the cold, wet corner of the water tint map (-20 degrees, rainfall 255), which is the
    /// blue-green of a pool; it used to be set for the whole region whenever the pool might reach into it, which also
    /// chilled the grass and leaves of the Suburbs cells beside the pool. A region that is entirely pool (every cell,
    /// whatever lies in the padding) still gets the one constant value, so the pool's water colour is the same everywhere
    /// in it. Map regions are saved: regions generated before this change keep their old whole-region tint.
    /// </summary>
    private IntDataMap2D LevelTintMap(int regionX, int regionZ, int size, int climate)
    {
        if (layout == null || size % WorldLayout.MacroSize != 0) return null;
        int cells = size / WorldLayout.MacroSize, mx0 = regionX * cells, mz0 = regionZ * cells, span = cells + 2;
        int motion = (Climate.DescaleTemperature(MotionTintTemperature) << 16) | (MotionTintRainfall << 8);
        int pool = (Climate.DescaleTemperature(-20f) << 16) | (255 << 8);
        bool allPool = true;
        for (int z = 0; z < cells && allPool; z++)
            for (int x = 0; x < cells && allPool; x++)
                allPool = layout.LevelAt(mx0 + x, mz0 + z) == WorldLayout.Poolrooms;
        if (allPool) return ConstantMap(pool);
        int Tint(int level, int mx, int mz) => level switch
        {
            WorldLayout.Poolrooms => pool,
            WorldLayout.Motion => motion,
            10 => (Climate.DescaleTemperature(FarmTintTemperature) << 16)
                  | ((FarmTintRainfall + (int)(Hashing.Hash(0x10F1, mx, mz, 0x7147) % (FarmTintRainfallSpread + 1))) << 8),
            _ => -1,
        };
        var data = new int[span * span];
        bool any = false;
        // (The padding round the inner map is the neighbouring regions' cells, worked out the same way)
        for (int z = -1; z <= cells; z++)
        {
            for (int x = -1; x <= cells; x++)
            {
                int mx = mx0 + x, mz = mz0 + z, level = layout.LevelAt(mx, mz);
                bool deep = level is WorldLayout.Motion or 10 or WorldLayout.Poolrooms && layout.LevelAt(mx - 1, mz) == level && layout.LevelAt(mx, mz - 1) == level
                    && layout.LevelAt(mx - 1, mz - 1) == level;
                data[(z + 1) * span + x + 1] = deep ? Tint(level, mx, mz) : climate;
                any |= deep;
            }
        }
        return any ? new IntDataMap2D { Data = data, Size = span, TopLeftPadding = 1, BottomRightPadding = 1 } : null;
    }

    private static IntDataMap2D ConstantMap(int value)
    {
        // 1x1 inner map with 1 block of padding on each side, as the lerping lookup requires
        var data = new int[9];
        for (int i = 0; i < data.Length; i++) data[i] = value;
        return new IntDataMap2D { Data = data, Size = 3, TopLeftPadding = 1, BottomRightPadding = 1 };
    }

    /// <summary>The Terrain pass: writes the column's blocks, fluids, height maps and block light (<c>WorldGenerator.Generate</c>).</summary>
    private void OnTerrainPass(IChunkColumnGenerateRequest request)
    {
        generator.Generate(request);
    }

    /// <summary>
    /// The TerrainFeatures pass: the only place block entities are created. <c>SpawnBlockEntities</c> takes them from
    /// the note the Terrain pass left, or works them out from the blocks when the note is gone (the server stopped
    /// between the two passes).
    /// </summary>
    private void OnFeaturesPass(IChunkColumnGenerateRequest request)
    {
        worldgenBlockAccessor.BeginColumn();
        generator.SpawnBlockEntities(request, worldgenBlockAccessor);
    }

    /// <summary>
    /// Registered under the Vegetation pass, which only gives it a slot after TerrainFeatures: nothing is grown here.
    /// It floods the column with sunlight and applies the block light updates the accessor scheduled.
    /// </summary>
    private void OnLightPass(IChunkColumnGenerateRequest request)
    {
        worldgenBlockAccessor.BeginColumn();
        sapi.WorldManager.SunFloodChunkColumnForWorldGen(request.Chunks, request.ChunkX, request.ChunkZ);
        worldgenBlockAccessor.RunScheduledBlockLightUpdates(request.ChunkX, request.ChunkZ);
    }

    /// <summary>The engine's cross-column step: carries the sunlight over the borders to the neighbouring columns.</summary>
    private void OnNeighbourLightPass(IChunkColumnGenerateRequest request)
    {
        sapi.WorldManager.SunFloodChunkColumnNeighboursForWorldGen(request.Chunks, request.ChunkX, request.ChunkZ);
    }

    private TextCommandResult OnColumnCommand(TextCommandCallingArgs args)
    {
        if (!isBackroomsWorld) return TextCommandResult.Error("This is not a Backrooms world");

        int x, z;
        if (!args.Parsers[0].IsMissing && !args.Parsers[1].IsMissing)
        {
            x = (int)args[0];
            z = (int)args[1];
        }
        else if (args.Caller.Player != null)
        {
            BlockPos pos = args.Caller.Player.Entity.Pos.AsBlockPos;
            x = pos.X;
            z = pos.Z;
        }
        else
        {
            PlayerSpawnPos spawn = sapi.WorldManager.SaveGame.DefaultSpawn;
            x = spawn.x;
            z = spawn.z;
        }

        IBlockAccessor blockAccessor = sapi.World.BlockAccessor;
        WorldGeometry g = generator.Geometry;
        if (blockAccessor.GetChunkAtBlockPos(x, g.FloorY, z) == null)
        {
            sapi.WorldManager.LoadChunkColumnPriority(x / GlobalConstants.ChunkSize, z / GlobalConstants.ChunkSize, new ChunkLoadOptions { KeepLoaded = true });
            return TextCommandResult.Success("That chunk is not loaded. Loading it now, run the command again in a moment.");
        }

        var sb = new StringBuilder();
        int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
        // Ask the game's own stability system, which shows whether our Reality Stability hook is in effect
        float stability = sapi.ModLoader.GetModSystem<SystemTemporalStability>().GetTemporalStability(x + 0.5, g.FloorY + 1, z + 0.5);
        sb.AppendLine($"Column {x}, {z} (y relative to the Level 0 floor), Level {level}, stability {stability:0.00}:");
        int floorY = g.FloorFor(level);
        for (int y = floorY + WorldGeometry.MaxRoomHeight + 2; y >= floorY - 8; y--)
        {
            var pos = new BlockPos(x, y, z);
            Block block = blockAccessor.GetBlock(pos);
            Block fluid = blockAccessor.GetBlock(pos, BlockLayersAccess.Fluid);
            int light = blockAccessor.GetLightLevel(pos, EnumLightLevelType.MaxLight);
            string fluidText = fluid.BlockId != 0 ? $" + {fluid.Code}" : "";
            string entityText = blockAccessor.GetBlockEntity(pos) is BlockEntity be ? $" [{be.GetType().Name}]" : "";
            sb.AppendLine($"  {y - floorY,3}: {block.Code}{fluidText}{entityText} (light {light})");
        }
        return TextCommandResult.Success(sb.ToString());
    }

    private TextCommandResult OnGotoCommand(TextCommandCallingArgs args)
    {
        if (!isBackroomsWorld) return TextCommandResult.Error("This is not a Backrooms world");
        string number = (string)args[0];
        int level = WorldLayout.FromDisplayName(number);
        if (level < 0) return TextCommandResult.Error($"There is no Level {number} here ({LevelList})");
        var thresholds = sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>();
        ulong key = (ulong)sapi.World.Rand.NextInt64();
        var player = (IServerPlayer)args.Caller.Player;
        Vec3d from = player.Entity.Pos.XYZ;
        if (!thresholds.Send(player, level, key, null)) return TextCommandResult.Error($"Found nowhere to arrive in Level {WorldLayout.DisplayNumber(level)}");
        // (For /backrooms back)
        sapi.ModLoader.GetModSystem<Cheats.CheatSystem>()?.RememberBack(player, from);
        return TextCommandResult.Success($"Sent to Level {WorldLayout.DisplayNumber(level)}");
    }

    private TextCommandResult OnShiftCommand(TextCommandCallingArgs args)
    {
        if (!isBackroomsWorld) return TextCommandResult.Error("This is not a Backrooms world");
        double hours = args.Parsers[0].IsMissing ? 2 : (double)args[0];
        sapi.ModLoader.GetModSystem<Reality.RealitySystem>().ForceShift(hours);
        return TextCommandResult.Success(hours > 0 ? $"Reality Shift started for {hours:0.#} in-game hours" : "Reality Shift ended");
    }

    /// <summary>
    /// Dumps a region (2r+1 square, from 10 below the floor to the top of the band) as a palette of block codes
    /// ("block|fluid") and, per block, a palette index and a light level. Chunks that are not loaded are queued
    /// to load; run it again once they are.
    /// </summary>
    private TextCommandResult OnDumpCommand(TextCommandCallingArgs args)
    {
        if (!isBackroomsWorld) return TextCommandResult.Error("This is not a Backrooms world");
        int cx = (int)args[0], cz = (int)args[1], r = Math.Clamp((int)args[2], 1, 64);
        WorldGeometry g = generator.Geometry;
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int missing = 0;
        for (int x = cx - r; x <= cx + r; x += GlobalConstants.ChunkSize)
            for (int z = cz - r; z <= cz + r; z += GlobalConstants.ChunkSize)
                foreach ((int qx, int qz) in new[] { (x, z), (Math.Min(x + GlobalConstants.ChunkSize, cx + r), z), (x, Math.Min(z + GlobalConstants.ChunkSize, cz + r)) })
                    if (ba.GetChunkAtBlockPos(qx, g.FloorY, qz) == null)
                    {
                        missing++;
                        sapi.WorldManager.LoadChunkColumnPriority(qx / GlobalConstants.ChunkSize, qz / GlobalConstants.ChunkSize, new ChunkLoadOptions { KeepLoaded = true });
                    }
        if (ba.GetChunkAtBlockPos(cx + r, g.FloorY, cz + r) == null) { missing++; sapi.WorldManager.LoadChunkColumnPriority((cx + r) / GlobalConstants.ChunkSize, (cz + r) / GlobalConstants.ChunkSize, new ChunkLoadOptions { KeepLoaded = true }); }
        if (missing > 0) return TextCommandResult.Success($"{missing} chunk columns are not loaded yet. Loading them; run the command again in a moment.");

        // The city lies lower than the other levels, and its towers rise much higher; the Poolrooms' pits go deep, and
        // Motion's hills and mountain rise far above its valleys
        int dumpLevel = layout.LevelAt(WorldLayout.MacroOf(cx), WorldLayout.MacroOf(cz)), floor = g.FloorFor(dumpLevel);
        // (The five kept as 14-18: the band each is lit over, from its own floor)
        bool region = dumpLevel >= WorldLayout.RunLevel && dumpLevel <= WorldLayout.Level188;
        // (Level 7 from layout version 9: down to the midnight zone's seabed, and up to the high ceiling)
        bool highSea = dumpLevel == 7 && layout.Version >= 9;
        int y0 = dumpLevel switch { WorldLayout.Poolrooms => floor - WorldGeometry.PoolPitDepth - 2, WorldLayout.Motion => floor - 10, _ when region => g.BandBottomFor(dumpLevel),
            _ when highSea => floor - WorldLayout.AbyssDepth - 4, _ => floor - 10 };
        int y1 = dumpLevel switch
        {
            _ when highSea => Math.Min(g.TopY, floor + WorldLayout.SeaCeiling + 1),
            11 => Math.Min(g.TopY, floor + 90),
            WorldLayout.Poolrooms => floor + 16,
            WorldLayout.Motion => Math.Min(g.TopY, floor + 66),
            _ when region => g.BandTopFor(dumpLevel),
            _ => g.BandTop,
        };
        int size = 2 * r + 1, height = y1 - y0 + 1;
        var palette = new System.Collections.Generic.Dictionary<string, int>();
        var cells = new int[size * size * height];
        var light = new byte[cells.Length];
        var pos = new BlockPos(0, 0, 0);
        for (int y = 0; y < height; y++)
            for (int z = 0; z < size; z++)
                for (int x = 0; x < size; x++)
                {
                    pos.Set(cx - r + x, y0 + y, cz - r + z);
                    Block block = ba.GetBlock(pos), fluid = ba.GetBlock(pos, BlockLayersAccess.Fluid);
                    string key = block.Code + "|" + (fluid.BlockId != 0 ? fluid.Code.ToString() : "");
                    if (!palette.TryGetValue(key, out int index)) palette[key] = index = palette.Count;
                    int i = (y * size + z) * size + x;
                    cells[i] = index;
                    light[i] = (byte)ba.GetLightLevel(pos, EnumLightLevelType.MaxLight);
                }
        string path = System.IO.Path.Combine(GamePaths.DataPath, "ModData", "backrooms", $"dump-{cx}-{cz}.bin");
        System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path));
        using (var w = new System.IO.BinaryWriter(System.IO.File.Create(path)))
        {
            w.Write(cx - r); w.Write(y0); w.Write(cz - r); w.Write(size); w.Write(height); w.Write(floor);
            w.Write(palette.Count);
            foreach (string key in palette.OrderBy(p => p.Value).Select(p => p.Key)) w.Write(key);
            foreach (int c in cells) w.Write((ushort)c);
            w.Write(light);
        }
        return TextCommandResult.Success($"Dumped {size}x{height}x{size} blocks ({palette.Count} kinds) to {path}");
    }

    private TextCommandResult OnWhereCommand(TextCommandCallingArgs args)
    {
        if (!isBackroomsWorld) return TextCommandResult.Error("This is not a Backrooms world");
        BlockPos pos = args.Caller.Player.Entity.Pos.AsBlockPos;
        int mx = WorldLayout.MacroOf(pos.X), mz = WorldLayout.MacroOf(pos.Z);
        int level = layout.LevelAt(mx, mz);
        float stability = layout.StabilityAt(pos.X, pos.Y, pos.Z, generator.Geometry.FloorY);
        if (level != 0) return TextCommandResult.Success($"Level {WorldLayout.DisplayNumber(level)}, stability {stability:0.00}");
        string zone = layout.IsManilaMacro(mx, mz) ? "Manila Room" : layout.ZoneAt(mx, mz).ToString();
        return TextCommandResult.Success($"Level 0, zone: {zone}, stability {stability:0.00}");
    }

    /// <summary>Marks where a player first woke up, so there is always one known place to find on the map (unless the map setting makes no waypoints).</summary>
    private void OnPlayerCreate(IServerPlayer player)
    {
        if (!isBackroomsWorld || !Backrooms.Map.MapSetting.Waypoints(sapi.World.Config)) return;
        WaypointMapLayer waypoints = sapi.ModLoader.GetModSystem<WorldMapManager>()?.MapLayers.OfType<WaypointMapLayer>().FirstOrDefault();
        PlayerSpawnPos spawn = sapi.WorldManager.SaveGame.DefaultSpawn;
        if (waypoints == null || spawn == null) return;

        waypoints.AddWaypoint(new Waypoint
        {
            Position = new Vec3d(spawn.x + 0.5, spawn.y ?? generator.Geometry.FloorY + 1, spawn.z + 0.5),
            Title = Lang.Get("backrooms:waypoint-wokeup"),
            Icon = "home",
            Color = ColorUtil.ColorFromRgba(215, 212, 138, 255),
            OwningPlayerUid = player.PlayerUID,
            Pinned = true,
        }, player);
    }

    private void OnGetClimateServer(ref ClimateCondition climate, BlockPos pos, EnumGetClimateMode mode, double totalDays)
    {
        // (Called from any thread: guard on the objects themselves, not only the flag)
        WorldLayout layout = this.layout;
        WorldGenerator generator = this.generator;
        if (!isBackroomsWorld || layout == null || generator == null) return;
        // (The Mangled's weather: the air goes cold round it)
        ApplyIndoorClimate(climate, layout.TemperatureAt(pos.X, pos.Y, pos.Z, generator.Geometry.FloorY) - Entities.MangledEvent.ColdDegrees * Entities.MangledEvent.ColdAt(pos));
    }

    private void OnGetClimateClient(ref ClimateCondition climate, BlockPos pos, EnumGetClimateMode mode, double totalDays)
    {
        // The client only uses climate for visuals; body temperature is worked out on the server
        if (clientWorldKind == 1) ApplyIndoorClimate(climate, LobbyTemperature - Entities.MangledEvent.ColdDegrees * clientMangledFog);
    }

    private static void ApplyIndoorClimate(ClimateCondition climate, float temperature)
    {
        climate.Temperature = temperature;
        climate.WorldGenTemperature = temperature;
        climate.Rainfall = 0f;
        climate.WorldgenRainfall = 0f;
        climate.RainCloudOverlay = 0f;
    }
}
