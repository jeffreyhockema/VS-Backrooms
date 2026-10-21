using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Server;

namespace Backrooms.Worldgen;

/// <summary>
/// Computes block light for a freshly generated chunk column and writes it straight into the chunks.
///
/// Vintage Story's own light engine recalculates every nearby light source each time one light is placed, which
/// makes a ceiling full of fluorescent panels very slow to generate. Because the layout is deterministic, the
/// light sources in neighbouring chunks are known in advance, so a single flood fill over this column plus a
/// margin gives the same result in a few milliseconds. It follows the engine's rules: a light source has its
/// full brightness, and each step loses one level plus the light absorption of the block it leaves.
///
/// Light sources are also registered in each chunk's LightPositions, so the engine relights correctly when
/// players later break or place blocks.
///
/// What lighting needs of a cell (how much each block absorbs, and where its lights are) is worked out once and
/// kept: every cell is wanted by the chunk it is in and by its eight neighbours, and the generator hands over what
/// it has just built rather than having it computed again. Whichever of the two comes first is kept, so every chunk
/// lit with a cell sees the same cell. A cell worked out here for a neighbour before its own chunk was generated also
/// keeps the blocks it computed, and <see cref="WorldGenerator.Generate"/> places those rather than working them out
/// a second time (see <see cref="Computed"/>).
///
/// <see cref="Light"/> works in one set of scratch arrays, so it lights one column at a time (the terrain pass runs on
/// one thread anyway); the cell cache has its own lock.
/// </summary>
public sealed class WorldLighting
{
    private const int Margin = WorldLayout.MacroSize;

    /// <summary>A cell's absorption per block and its light sources, over one band of heights.</summary>
    public sealed class CellLight
    {
        public readonly byte[] Absorption;
        public readonly List<(int Lx, int Y, int Lz, int BlockId)> Sources = new();

        /// <summary>
        /// The block and fluid ids the cell was worked out from, in the same order as <see cref="Absorption"/>; null
        /// for a cell the generator handed over (it has placed the blocks itself). <see cref="Fluids"/> stays null
        /// while the cell has no fluid at all.
        /// </summary>
        public int[] Blocks, Fluids;

        public CellLight(int chunkSize, int height) => Absorption = new byte[chunkSize * chunkSize * height];
    }

    /// <summary>
    /// Cells wanted lately, by position and band (a city cell is lit over a lower band than its neighbours, and so on).
    /// A cell worked out here holds its block ids too, some 300 KB at 40 blocks high, hence the modest number.
    /// </summary>
    private const int CellCacheSize = 64;
    private readonly Dictionary<(int, int, int), CellLight> cellCache = new();
    private readonly Queue<(int, int, int)> cellOrder = new();

    private readonly WorldGenerator generator;
    private readonly int chunkSize;
    private readonly int width;
    private readonly int height;
    /// <summary>The bottom of the band being lit: the usual one, or the one of a level that lies lower (see <see cref="WorldGeometry.BandBottomFor"/>).</summary>
    private int bandBottom;

    private readonly byte[] absorption;
    private readonly byte[] level;
    /// <summary>Block id of the light source that lit each cell, for its hue and saturation.</summary>
    private readonly int[] source;
    // One bucket per brightness, 0 to 31; Seed caps a light at 31 to keep the index in range
    private readonly List<int>[] buckets = new List<int>[32];
    /// <summary>Guards the scratch arrays above, and <see cref="bandBottom"/>.</summary>
    private readonly object scratchLock = new();

    // What lighting needs of each block, by id, read once from the blocks: how much light it absorbs, how bright a
    // light it is (0 for none), and its light's hue and saturation as they go into the block light value
    private readonly int[] absorptionById;
    private readonly byte[] brightnessById;
    private readonly int[] hueSatById;

    public WorldLighting(ICoreServerAPI api, WorldGenerator generator, int chunkSize)
    {
        this.generator = generator;
        this.chunkSize = chunkSize;
        IList<Block> blocks = api.World.Blocks;
        absorptionById = new int[blocks.Count];
        brightnessById = new byte[blocks.Count];
        hueSatById = new int[blocks.Count];
        for (int id = 0; id < blocks.Count; id++)
        {
            Block block = blocks[id];
            if (block == null) continue;
            absorptionById[id] = block.LightAbsorption;
            byte[] hsv = block.LightHsv;
            if (hsv == null || hsv.Length < 3) continue;
            brightnessById[id] = hsv[2];
            hueSatById[id] = (hsv[0] << 10) | (hsv[1] << 16);
        }
        width = chunkSize + 2 * Margin;
        bandBottom = generator.Geometry.BandBottom;
        height = generator.Geometry.BandTop - bandBottom + 1;

        int cells = width * width * height;
        absorption = new byte[cells];
        level = new byte[cells];
        source = new int[cells];
        for (int i = 0; i < buckets.Length; i++) buckets[i] = new List<int>();
    }

    private int Index(int x, int y, int z) => (y * width + z) * width + x;

    /// <summary>The band of heights a cell is lit over: the usual one, or its own level's (the city, the Poolrooms, Motion).</summary>
    public int BandBottomFor(int chunkX, int chunkZ) => generator.Geometry.BandBottomFor(generator.Macro(chunkX, chunkZ)[0].Level);

    public int Height => height;

    /// <summary>What the generator records about a block it has just placed, for the cell's lighting data.</summary>
    public void Note(CellLight cell, int lx, int y, int lz, int bandBottomUsed, int block, int fluid)
    {
        int yy = y - bandBottomUsed;
        if (yy < 0 || yy >= height) return;
        int absorb = Math.Max(absorptionById[block], fluid != 0 ? absorptionById[fluid] : 0);
        cell.Absorption[(yy * chunkSize + lz) * chunkSize + lx] = (byte)Math.Min(255, absorb);
        if (brightnessById[block] > 0) cell.Sources.Add((lx, yy, lz, block));
    }

    /// <summary>Keeps a cell's lighting data the generator has just built.</summary>
    public void Offer(int chunkX, int chunkZ, int bandBottomUsed, CellLight cell) => Remember((chunkX, chunkZ, bandBottomUsed), cell);

    private void Remember((int, int, int) key, CellLight cell)
    {
        lock (cellCache)
        {
            if (!cellCache.TryAdd(key, cell)) return;
            cellOrder.Enqueue(key);
            if (cellOrder.Count > CellCacheSize) cellCache.Remove(cellOrder.Dequeue());
        }
    }

    /// <summary>
    /// A cell that was worked out here, with the blocks it was worked out from, if it is still cached; otherwise null.
    /// The generator places those blocks instead of computing the same ones again, so that a cell lit as somebody's
    /// neighbour first is not paid for twice, and so that its blocks and its light cannot disagree (Level 188's windows
    /// follow the calendar). The cell is never changed once cached.
    /// </summary>
    public CellLight Computed(int chunkX, int chunkZ, int bandBottomUsed)
    {
        lock (cellCache)
        {
            return cellCache.TryGetValue((chunkX, chunkZ, bandBottomUsed), out CellLight cell) && cell.Blocks != null ? cell : null;
        }
    }

    /// <summary>The place of a block in a cell's arrays (<paramref name="yy"/> is the height above the band's bottom).</summary>
    public int CellIndex(int lx, int yy, int lz) => (yy * chunkSize + lz) * chunkSize + lx;

    /// <summary>A cell's lighting data over a band, from the cache or computed now.</summary>
    private CellLight Cell(int chunkX, int chunkZ, int bandBottomUsed)
    {
        var key = (chunkX, chunkZ, bandBottomUsed);
        lock (cellCache)
        {
            if (cellCache.TryGetValue(key, out CellLight cached)) return cached;
        }
        var cell = new CellLight(chunkSize, height) { Blocks = new int[chunkSize * chunkSize * height] };
        Tile[] tiles = generator.Macro(chunkX, chunkZ);
        for (int lz = 0; lz < chunkSize; lz++)
        {
            for (int lx = 0; lx < chunkSize; lx++)
            {
                Tile t = tiles[WorldLayout.TileIndex(lx, lz)];
                int gx = chunkX * chunkSize + lx, gz = chunkZ * chunkSize + lz;
                for (int y = 0; y < height; y++)
                {
                    int block = generator.ColumnBlock(t, gx, gz, bandBottomUsed + y, out int fluid);
                    Note(cell, lx, bandBottomUsed + y, lz, bandBottomUsed, block, fluid);
                    int at = CellIndex(lx, y, lz);
                    cell.Blocks[at] = block;
                    if (fluid != 0) (cell.Fluids ??= new int[cell.Blocks.Length])[at] = fluid;
                }
            }
        }
        Remember(key, cell);
        return cell;
    }

    /// <summary>Lights a column the generator has just built (its blocks must have been offered with <see cref="Offer"/>, or are worked out now).</summary>
    public void Light(IServerChunk[] chunks, int chunkX, int chunkZ)
    {
        lock (scratchLock) LightLocked(chunks, chunkX, chunkZ);
    }

    private void LightLocked(IServerChunk[] chunks, int chunkX, int chunkZ)
    {
        Array.Clear(level);
        foreach (List<int> bucket in buckets) bucket.Clear();
        bandBottom = BandBottomFor(chunkX, chunkZ);

        // Absorption and light sources for this column and its eight neighbours
        for (int mz = -1; mz <= 1; mz++)
        {
            for (int mx = -1; mx <= 1; mx++)
            {
                CellLight cell = Cell(chunkX + mx, chunkZ + mz, bandBottom);
                int ox = (mx + 1) * chunkSize, oz = (mz + 1) * chunkSize;
                for (int y = 0; y < height; y++)
                {
                    for (int lz = 0; lz < chunkSize; lz++)
                    {
                        Array.Copy(cell.Absorption, (y * chunkSize + lz) * chunkSize, absorption, Index(ox, y, oz + lz), chunkSize);
                    }
                }
                foreach ((int lx, int y, int lz, int block) in cell.Sources)
                {
                    Seed(Index(ox + lx, y, oz + lz), block);
                    if (mx == 0 && mz == 0) RegisterLightPosition(chunks, lx, bandBottom + y, lz);
                }
            }
        }

        Flood();
        Write(chunks);
    }

    private void Seed(int index, int blockId)
    {
        byte brightness = Math.Min((byte)31, brightnessById[blockId]);
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
                    int index3d = ((worldY % chunkSize) * chunkSize + lz) * chunkSize + lx;
                    chunk.Lighting.SetBlocklight(index3d, (value << 5) | hueSatById[source[index]]);
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
