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
/// Registers the "backrooms" world type. Vanilla terrain, climate, vegetation and creature generators only
/// run for the "standard" and "superflat" world types, so a world created with the Backrooms playstyle
/// gets nothing but what this system generates.
/// </summary>
public class BackroomsModSystem : ModSystem
{
    /// <summary>Level 0's temperature, used for the climate maps and on the client (which only needs it for visuals).</summary>
    private const float LobbyTemperature = 22f;
    private const float TintTemperature = 15f;
    private const int TintRainfall = 190;

    private ICoreServerAPI sapi;
    private IWorldGenBlockAccessor worldgenBlockAccessor;
    private WorldLayout layout;
    private WorldGenerator generator;
    private bool isBackroomsWorld;

    private ICoreClientAPI capi;
    private bool? clientIsBackroomsWorld;

    // Run after the weather systems so our climate override has the final say
    public override double ExecuteOrder() => 1.0;

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
                .WithDescription("Teleports you into a level (0-11)")
                .RequiresPlayer()
                .WithArgs(api.ChatCommands.Parsers.IntRange("level", 0, WorldLayout.LevelCount - 1))
                .HandleWith(OnGotoCommand)
            .EndSubCommand()
            .BeginSubCommand("shift")
                .WithDescription("Starts a Reality Shift lasting the given number of in-game hours (default 2, 0 ends it)")
                .WithArgs(api.ChatCommands.Parsers.OptionalDouble("hours"))
                .HandleWith(OnShiftCommand)
            .EndSubCommand()
            .BeginSubCommand("where")
                .WithDescription("Shows which Level 0 zone you are in")
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
    }

    private void OnModsAndConfigReady()
    {
        ISaveGame save = sapi.WorldManager.SaveGame;
        isBackroomsWorld = save.WorldType == BackroomsWorld.WorldTypeCode;
        if (!isBackroomsWorld) return;

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
        layout = new WorldLayout(sapi.WorldManager.Seed, spawnMacroX, spawnMacroZ);
        generator = new WorldGenerator(sapi, layout);

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
        // moist, so the Suburbs' lawns and Level 10's meadows and hedges are green rather than parched
        int climate = (Climate.DescaleTemperature(TintTemperature) << 16) | (TintRainfall << 8) | 0;
        mapRegion.ClimateMap = ConstantMap(climate);
        mapRegion.ForestMap = ConstantMap(0);
        mapRegion.ShrubMap = ConstantMap(0);
    }

    private static IntDataMap2D ConstantMap(int value)
    {
        // 1x1 inner map with 1 block of padding on each side, as the lerping lookup requires
        var data = new int[9];
        for (int i = 0; i < data.Length; i++) data[i] = value;
        return new IntDataMap2D { Data = data, Size = 3, TopLeftPadding = 1, BottomRightPadding = 1 };
    }

    private void OnTerrainPass(IChunkColumnGenerateRequest request)
    {
        generator.Generate(request);
    }

    private void OnFeaturesPass(IChunkColumnGenerateRequest request)
    {
        worldgenBlockAccessor.BeginColumn();
        generator.SpawnBlockEntities(request, worldgenBlockAccessor);
    }

    private void OnLightPass(IChunkColumnGenerateRequest request)
    {
        worldgenBlockAccessor.BeginColumn();
        sapi.WorldManager.SunFloodChunkColumnForWorldGen(request.Chunks, request.ChunkX, request.ChunkZ);
        worldgenBlockAccessor.RunScheduledBlockLightUpdates(request.ChunkX, request.ChunkZ);
    }

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
        int level = (int)args[0];
        var thresholds = sapi.ModLoader.GetModSystem<Thresholds.ThresholdSystem>();
        ulong key = (ulong)sapi.World.Rand.NextInt64();
        return thresholds.Send((IServerPlayer)args.Caller.Player, level, key, null)
            ? TextCommandResult.Success($"Sent to Level {level}")
            : TextCommandResult.Error($"Found nowhere to arrive in Level {level}");
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

        // The city lies lower than the other levels, and its towers rise much higher
        int dumpLevel = layout.LevelAt(WorldLayout.MacroOf(cx), WorldLayout.MacroOf(cz)), floor = g.FloorFor(dumpLevel);
        int y0 = floor - 10, y1 = dumpLevel == 11 ? Math.Min(g.TopY, floor + 90) : g.BandTop, size = 2 * r + 1, height = y1 - y0 + 1;
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
        if (level != 0) return TextCommandResult.Success($"Level {level}, stability {stability:0.00}");
        string zone = layout.IsManilaMacro(mx, mz) ? "Manila Room" : layout.ZoneAt(mx, mz).ToString();
        return TextCommandResult.Success($"Level 0, zone: {zone}, stability {stability:0.00}");
    }

    /// <summary>Marks where a player first woke up, so there is always one known place to find on the map.</summary>
    private void OnPlayerCreate(IServerPlayer player)
    {
        if (!isBackroomsWorld) return;
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
        if (!isBackroomsWorld) return;
        ApplyIndoorClimate(climate, layout.TemperatureAt(pos.X, pos.Y, pos.Z, generator.Geometry.FloorY));
    }

    private void OnGetClimateClient(ref ClimateCondition climate, BlockPos pos, EnumGetClimateMode mode, double totalDays)
    {
        if (clientIsBackroomsWorld == null)
        {
            // World config arrives from the server after StartClientSide, so resolve this lazily
            string worldClimate = capi.World?.Config?.GetString("worldClimate");
            if (worldClimate == null) return;
            clientIsBackroomsWorld = worldClimate == BackroomsWorld.ClimateCode;
        }
        // The client only uses climate for visuals; body temperature is worked out on the server
        if (clientIsBackroomsWorld == true) ApplyIndoorClimate(climate, LobbyTemperature);
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
