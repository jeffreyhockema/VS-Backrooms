using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Server;

namespace Backrooms.Worldgen;

/// <summary>
/// Computes block light for a freshly generated Level 0 chunk column and writes it straight into the chunks.
///
/// Vintage Story's own light engine recalculates every nearby light source each time one light is placed, which
/// makes a ceiling full of fluorescent panels very slow to generate. Because the layout is deterministic, the
/// light sources in neighbouring chunks are known in advance, so a single flood fill over this column plus a
/// margin gives the same result in a few milliseconds. It follows the engine's rules: a light source has its
/// full brightness, and each step loses one level plus the light absorption of the block it leaves.
///
/// Light sources are also registered in each chunk's LightPositions, so the engine relights correctly when
/// players later break or place blocks.
/// </summary>
public sealed class WorldLighting
{
    private const int Margin = WorldLayout.MacroSize;

    private readonly ICoreServerAPI api;
    private readonly WorldGenerator generator;
    private readonly int chunkSize;
    private readonly int width;
    private readonly int height;
    /// <summary>The bottom of the band being lit: the usual one, or (for Level 11, whose streets lie lower) the city's.</summary>
    private int bandBottom;
    private readonly int defaultBottom, cityBottom;

    private readonly byte[] absorption;
    private readonly byte[] level;
    /// <summary>Block id of the light source that lit each cell, for its hue and saturation.</summary>
    private readonly int[] source;
    private readonly List<int>[] buckets = new List<int>[32];
    private readonly IList<Block> blocks;

    public WorldLighting(ICoreServerAPI api, WorldGenerator generator, int chunkSize)
    {
        this.api = api;
        this.generator = generator;
        this.chunkSize = chunkSize;
        blocks = api.World.Blocks;
        width = chunkSize + 2 * Margin;
        bandBottom = defaultBottom = generator.Geometry.BandBottom;
        cityBottom = generator.Geometry.CityBandBottom;
        height = generator.Geometry.BandTop - bandBottom + 1;

        int cells = width * width * height;
        absorption = new byte[cells];
        level = new byte[cells];
        source = new int[cells];
        for (int i = 0; i < buckets.Length; i++) buckets[i] = new List<int>();
    }

    private int Index(int x, int y, int z) => (y * width + z) * width + x;

    public void Light(IServerChunk[] chunks, int chunkX, int chunkZ)
    {
        Array.Clear(level);
        foreach (List<int> bucket in buckets) bucket.Clear();
        bandBottom = generator.Macro(chunkX, chunkZ)[0].Level == 11 ? cityBottom : defaultBottom;

        // Absorption and light sources for this column and its eight neighbours
        for (int mz = -1; mz <= 1; mz++)
        {
            for (int mx = -1; mx <= 1; mx++)
            {
                Tile[] tiles = generator.Macro(chunkX + mx, chunkZ + mz);
                for (int lz = 0; lz < chunkSize; lz++)
                {
                    for (int lx = 0; lx < chunkSize; lx++)
                    {
                        Tile t = tiles[WorldLayout.TileIndex(lx, lz)];
                        int gx = (mx + 1) * chunkSize + lx;
                        int gz = (mz + 1) * chunkSize + lz;
                        for (int y = 0; y < height; y++)
                        {
                            int block = generator.ColumnBlock(t, (chunkX + mx) * chunkSize + lx, (chunkZ + mz) * chunkSize + lz, bandBottom + y, out int fluid);
                            int absorb = Math.Max(blocks[block].LightAbsorption, fluid != 0 ? blocks[fluid].LightAbsorption : 0);
                            int index = Index(gx, y, gz);
                            absorption[index] = (byte)Math.Min(255, absorb);

                            if (blocks[block].LightHsv[2] > 0)
                            {
                                Seed(index, block);
                                if (mx == 0 && mz == 0) RegisterLightPosition(chunks, lx, bandBottom + y, lz);
                            }
                        }
                    }
                }
            }
        }

        Flood();
        Write(chunks);
    }

    private void Seed(int index, int blockId)
    {
        byte brightness = Math.Min((byte)31, blocks[blockId].LightHsv[2]);
        if (brightness <= level[index]) return;
        level[index] = brightness;
        source[index] = blockId;
        buckets[brightness].Add(index);
    }

    /// <summary>Brightest-first flood fill, so every cell is finalised the first time it is expanded.</summary>
    private void Flood()
    {
        int layer = width * width;
        for (int current = buckets.Length - 1; current > 0; current--)
        {
            List<int> bucket = buckets[current];
            for (int i = 0; i < bucket.Count; i++)
            {
                int index = bucket[i];
                if (level[index] != current) continue; // superseded by a brighter path

                int spread = current - absorption[index] - 1;
                if (spread <= 0) continue;

                int x = index % width;
                int z = index / width % width;
                int y = index / layer;
                if (x > 0) Spread(index - 1, spread, index);
                if (x < width - 1) Spread(index + 1, spread, index);
                if (z > 0) Spread(index - width, spread, index);
                if (z < width - 1) Spread(index + width, spread, index);
                if (y > 0) Spread(index - layer, spread, index);
                if (y < height - 1) Spread(index + layer, spread, index);
            }
        }
    }

    private void Spread(int neighbour, int spread, int from)
    {
        if (level[neighbour] >= spread) return;
        level[neighbour] = (byte)spread;
        source[neighbour] = source[from];
        buckets[spread].Add(neighbour);
    }

    private void Write(IServerChunk[] chunks)
    {
        for (int y = 0; y < height; y++)
        {
            int worldY = bandBottom + y;
            IServerChunk chunk = chunks[worldY / chunkSize];
            for (int lz = 0; lz < chunkSize; lz++)
            {
                for (int lx = 0; lx < chunkSize; lx++)
                {
                    int index = Index(Margin + lx, y, Margin + lz);
                    int value = level[index];
                    if (value == 0) continue;
                    Block emitter = blocks[source[index]];
                    int index3d = ((worldY % chunkSize) * chunkSize + lz) * chunkSize + lx;
                    chunk.Lighting.SetBlocklight(index3d, (value << 5) | (emitter.LightHsv[0] << 10) | (emitter.LightHsv[1] << 16));
                }
            }
        }
    }

    private void RegisterLightPosition(IServerChunk[] chunks, int lx, int worldY, int lz)
    {
        IServerChunk chunk = chunks[worldY / chunkSize];
        chunk.LightPositions ??= new HashSet<int>();
        chunk.LightPositions.Add(((worldY % chunkSize) * chunkSize + lz) * chunkSize + lx);
    }
}
