using System;
using System.Collections.Generic;
using System.IO;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;
using Backrooms.Worldgen;

namespace Backrooms.Map;

/// <summary>
/// Replaces the vanilla terrain map in Backrooms worlds. The vanilla map draws the top-most block of every
/// column, which here is just the slab above the ceiling, and it reveals everything within view distance.
/// This layer instead reveals only what the player has actually seen: it casts rays at head height from the
/// player, stops at walls, and records what it saw (walls, carpet, doorways, supply boxes, light level).
/// Explored pixels are remembered per world, so earlier routes stay on the map.
/// </summary>
public class BackroomsMapLayer : MapLayer
{
    private const int RevealRadius = 24;
    private const int RayCount = 360;
    /// <summary>In darkness the player only makes out their immediate surroundings.</summary>
    private const int DarkRevealRadius = 4;
    private const int DarkLightLevel = 5;
    /// <summary>In Level 6 maps fail: only what is within reach is remembered, lit or not.</summary>
    private const int Level6RevealRadius = 2;

    private const float RevealInterval = 0.25f;
    private const float TextureInterval = 0.5f;
    private const float SaveInterval = 30f;

    private readonly ICoreClientAPI capi;
    private readonly ExploredMapStore store;
    private readonly WorldGeometry geometry;
    private readonly WorldLayout layout;
    private double revealLimit = RevealRadius;

    private readonly Dictionary<FastVec2i, MultiChunkMapComponent> components = new();
    private readonly HashSet<FastVec2i> visibleChunks = new();
    private readonly HashSet<FastVec2i> dirtyChunks = new();

    // Scratch state for one reveal pass, sized for the square around the player
    private const int GridSize = RevealRadius * 2 + 1;
    private readonly sbyte[] sightGrid = new sbyte[GridSize * GridSize];
    private readonly int[] visitedPass = new int[GridSize * GridSize];
    private int pass;
    private readonly BlockPos tmpPos = new BlockPos(0, 0, 0);

    private float revealAccum;
    private float textureAccum;
    private float saveAccum;

    public override string Title => Lang.Get("backrooms:maplayer-explored");
    public override string LayerGroupCode => "terrain";
    public override EnumMapAppSide DataSide => EnumMapAppSide.Client;

    public BackroomsMapLayer(ICoreAPI api, IWorldMapManager mapSink) : base(api, mapSink)
    {
        capi = api as ICoreClientAPI;
        if (capi == null) return;

        geometry = new WorldGeometry(capi.World.BlockAccessor.MapSizeY);
        layout = BackroomsWorld.CreateLayout(capi.World);
        string path = Path.Combine(GamePaths.DataPath, "ModData", "backrooms", $"explored-{capi.World.SavegameIdentifier}.bin");
        store = new ExploredMapStore(path, capi.Logger);
        store.Load();
    }

    public override void OnTick(float dt)
    {
        if (capi == null) return;

        revealAccum += dt;
        if (revealAccum >= RevealInterval)
        {
            revealAccum = 0;
            RevealAroundPlayer();
        }

        textureAccum += dt;
        if (textureAccum >= TextureInterval)
        {
            textureAccum = 0;
            RefreshTextures();
        }

        saveAccum += dt;
        if (saveAccum >= SaveInterval)
        {
            saveAccum = 0;
            store.Save();
        }
    }

    public override void OnViewChangedClient(List<FastVec2i> nowVisible, List<FastVec2i> nowHidden)
    {
        foreach (FastVec2i chunk in nowVisible) visibleChunks.Add(chunk);
        foreach (FastVec2i chunk in nowHidden) visibleChunks.Remove(chunk);
    }

    public override void Render(GuiElementMap mapElem, float dt)
    {
        if (!Active) return;
        foreach (MultiChunkMapComponent component in components.Values) component.Render(mapElem, dt);
    }

    public override void OnShutDown()
    {
        store?.Save(wait: true);
    }

    public override void Dispose()
    {
        foreach (MultiChunkMapComponent component in components.Values) component.ActuallyDispose();
        components.Clear();
    }

    // ---- Revealing ----

    private void RevealAroundPlayer()
    {
        EntityPlayer player = capi.World.Player?.Entity;
        if (player == null) return;

        double originX = player.Pos.X;
        double originZ = player.Pos.Z;
        int centerX = (int)Math.Floor(originX);
        int centerZ = (int)Math.Floor(originZ);
        int mx = WorldLayout.MacroOf(centerX), mz = WorldLayout.MacroOf(centerZ);
        int level = layout.LevelAt(mx, mz);
        if (!SampleHeights(level, player.Pos.Y)) return;
        revealLimit = level == 6 && !layout.IsSnackrooms(mx, mz) ? Level6RevealRadius : RevealRadius;

        Array.Clear(sightGrid);
        pass++;

        for (int ray = 0; ray < RayCount; ray++)
        {
            double angle = ray * (2 * Math.PI / RayCount);
            double dx = Math.Cos(angle);
            double dz = Math.Sin(angle);

            for (double t = 0; t <= revealLimit; t += 0.4)
            {
                int x = (int)Math.Floor(originX + dx * t);
                int z = (int)Math.Floor(originZ + dz * t);
                int index = (z - centerZ + RevealRadius) * GridSize + (x - centerX + RevealRadius);

                sbyte sight = SightAt(index, x, z);
                if (sight == SightUnloaded) break;

                if (visitedPass[index] != pass)
                {
                    visitedPass[index] = pass;
                    RevealColumn(x, z, t);
                }
                if (sight == SightBlocked) break;
            }
        }
    }

    /// <summary>The floor the current pass maps (the floor under the player's feet, in the sea and the caves).</summary>
    private int floorY;

    /// <summary>
    /// Decides which floor to map from where the player is: the level's own floor on most levels; the surface of
    /// Level 7's sea, even while diving; and in Level 8's caves, whatever floor the player stands on.
    /// </summary>
    private bool SampleHeights(int level, double y)
    {
        floorY = geometry.FloorY;
        switch (level)
        {
            case 7:
                return y > geometry.FloorY - 70 && y < geometry.FloorY + WorldGeometry.MaxRoomHeight + 1;
            case 8:
                if (y < geometry.FloorY - 62 || y > geometry.FloorY + 9) return false;
                floorY = (int)Math.Floor(y) - 1;
                return true;
            case 11:
                // The city's streets, or the subway platforms seven blocks under the avenues
                if (y < geometry.CityFloorY - 9 || y > geometry.CityFloorY + 6) return false;
                floorY = y < geometry.CityFloorY - 1 ? geometry.CityFloorY - 6 : geometry.CityFloorY;
                return true;
            default:
                return geometry.Contains(y);
        }
    }

    private const sbyte SightOpen = 1;
    private const sbyte SightBlocked = 2;
    private const sbyte SightUnloaded = 3;

    private sbyte SightAt(int index, int x, int z)
    {
        sbyte cached = sightGrid[index];
        if (cached != 0) return cached;

        IBlockAccessor blockAccessor = capi.World.BlockAccessor;
        sbyte sight;
        if (blockAccessor.GetChunkAtBlockPos(x, floorY + 2, z) == null) sight = SightUnloaded;
        else sight = IsSolid(blockAccessor.GetBlock(tmpPos.Set(x, floorY + 2, z))) ? SightBlocked : SightOpen;

        sightGrid[index] = sight;
        return sight;
    }

    private void RevealColumn(int x, int z, double distance)
    {
        IBlockAccessor blockAccessor = capi.World.BlockAccessor;
        int light = blockAccessor.GetLightLevel(tmpPos.Set(x, floorY + 1, z), EnumLightLevelType.MaxLight);
        if (light < DarkLightLevel && distance > DarkRevealRadius) return;

        int color = MapColors.Classify(blockAccessor, floorY, floorY + geometry.CeilingY - 1 - geometry.FloorY, tmpPos, x, z, light);
        if (store.SetPixel(x, z, color))
        {
            dirtyChunks.Add(new FastVec2i(x / ExploredMapStore.ChunkSize, z / ExploredMapStore.ChunkSize));
        }
    }

    private static bool IsSolid(Block block) => block.BlockId != 0 && block.CollisionBoxes != null && block.CollisionBoxes.Length > 0;

    // ---- Textures ----

    private void RefreshTextures()
    {
        var groupsToRebuild = new HashSet<FastVec2i>();
        foreach (FastVec2i chunk in dirtyChunks)
        {
            FastVec2i group = GroupOf(chunk.X, chunk.Y);
            if (IsGroupVisible(group)) groupsToRebuild.Add(group);
        }
        dirtyChunks.Clear();

        // Create textures for explored groups that just scrolled into view
        foreach (FastVec2i chunk in visibleChunks)
        {
            FastVec2i group = GroupOf(chunk.X, chunk.Y);
            if (!components.ContainsKey(group) && store.TryGetChunk(chunk.X, chunk.Y, out _)) groupsToRebuild.Add(group);
        }

        foreach (FastVec2i group in groupsToRebuild) RebuildGroup(group);

        // Free textures for groups that are no longer on screen
        var hidden = new List<FastVec2i>();
        foreach (FastVec2i group in components.Keys)
        {
            if (!IsGroupVisible(group)) hidden.Add(group);
        }
        foreach (FastVec2i group in hidden)
        {
            components[group].ActuallyDispose();
            components.Remove(group);
        }
    }

    private void RebuildGroup(FastVec2i group)
    {
        var baseChunk = new FastVec2i(group.X * MultiChunkMapComponent.ChunkLen, group.Y * MultiChunkMapComponent.ChunkLen);
        if (!components.TryGetValue(group, out MultiChunkMapComponent component))
        {
            component = new MultiChunkMapComponent(capi, baseChunk);
            components[group] = component;
        }

        bool any = false;
        for (int dz = 0; dz < MultiChunkMapComponent.ChunkLen; dz++)
        {
            for (int dx = 0; dx < MultiChunkMapComponent.ChunkLen; dx++)
            {
                if (!store.TryGetChunk(baseChunk.X + dx, baseChunk.Y + dz, out int[] pixels)) continue;
                component.setChunk(dx, dz, pixels);
                any = true;
            }
        }
        if (any) component.FinishSetChunks();
    }

    private bool IsGroupVisible(FastVec2i group)
    {
        for (int dz = 0; dz < MultiChunkMapComponent.ChunkLen; dz++)
        {
            for (int dx = 0; dx < MultiChunkMapComponent.ChunkLen; dx++)
            {
                if (visibleChunks.Contains(new FastVec2i(group.X * MultiChunkMapComponent.ChunkLen + dx, group.Y * MultiChunkMapComponent.ChunkLen + dz))) return true;
            }
        }
        return false;
    }

    private static FastVec2i GroupOf(int chunkX, int chunkZ) => new FastVec2i(chunkX / MultiChunkMapComponent.ChunkLen, chunkZ / MultiChunkMapComponent.ChunkLen);
}
