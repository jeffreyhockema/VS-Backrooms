using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using Vintagestory.API.Common;

namespace Backrooms.Map;

/// <summary>
/// The pixels of every explored map chunk (32x32 blocks, one pixel per block, 0 = unexplored), persisted per
/// world on the client.
/// </summary>
public sealed class ExploredMapStore
{
    public const int ChunkSize = 32;
    private const int FileVersion = 1;

    private readonly Dictionary<long, int[]> chunks = new();
    private readonly string filePath;
    private readonly ILogger logger;

    public bool IsDirty { get; private set; }

    public ExploredMapStore(string filePath, ILogger logger)
    {
        this.filePath = filePath;
        this.logger = logger;
    }

    public static long Key(int chunkX, int chunkZ) => ((long)chunkX << 32) | (uint)chunkZ;

    public bool TryGetChunk(int chunkX, int chunkZ, out int[] pixels) => chunks.TryGetValue(Key(chunkX, chunkZ), out pixels);

    /// <summary>Sets one pixel. Returns true if it changed.</summary>
    public bool SetPixel(int x, int z, int color)
    {
        int chunkX = x / ChunkSize;
        int chunkZ = z / ChunkSize;
        long key = Key(chunkX, chunkZ);
        if (!chunks.TryGetValue(key, out int[] pixels))
        {
            pixels = new int[ChunkSize * ChunkSize];
            chunks[key] = pixels;
        }

        int index = (z % ChunkSize) * ChunkSize + (x % ChunkSize);
        if (pixels[index] == color) return false;
        pixels[index] = color;
        IsDirty = true;
        return true;
    }

    public void Load()
    {
        if (!File.Exists(filePath)) return;
        try
        {
            using var file = File.OpenRead(filePath);
            using var deflate = new DeflateStream(file, CompressionMode.Decompress);
            using var reader = new BinaryReader(deflate);
            if (reader.ReadInt32() != FileVersion) return;
            int count = reader.ReadInt32();
            for (int i = 0; i < count; i++)
            {
                long key = reader.ReadInt64();
                var pixels = new int[ChunkSize * ChunkSize];
                for (int p = 0; p < pixels.Length; p++) pixels[p] = reader.ReadInt32();
                chunks[key] = pixels;
            }
        }
        catch (Exception e)
        {
            logger.Error("[backrooms] Could not load explored map from {0}, starting fresh: {1}", filePath, e.Message);
            chunks.Clear();
        }
    }

    private System.Threading.Tasks.Task pendingSave;
    private readonly object fileLock = new();

    /// <summary>
    /// Saves the explored map if anything changed. Compressing and writing happens on a background thread unless
    /// <paramref name="wait"/> (when the world is closing).
    ///
    /// The list of chunks is taken at once, but their pixels are not copied (the whole map, every 30 seconds, would be
    /// megabytes of garbage each time): the writer reads the live arrays. A pixel the game changes while a write is
    /// under way marks the store dirty again, so it is written once more by the next save; and the final save, when
    /// the world closes, waits on the main thread, so nothing changes under it.
    /// </summary>
    public void Save(bool wait = false)
    {
        if (!IsDirty)
        {
            if (wait) pendingSave?.Wait();
            return;
        }
        var snapshot = new List<(long Key, int[] Pixels)>(chunks.Count);
        foreach (var (key, pixels) in chunks) snapshot.Add((key, pixels));
        IsDirty = false;

        pendingSave = (pendingSave ?? System.Threading.Tasks.Task.CompletedTask).ContinueWith(_ => Write(snapshot));
        if (wait) pendingSave.Wait();
    }

    private void Write(List<(long Key, int[] Pixels)> snapshot)
    {
        lock (fileLock)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(filePath));
                string tmpPath = filePath + ".tmp";
                using (var file = File.Create(tmpPath))
                using (var deflate = new DeflateStream(file, CompressionLevel.Fastest))
                using (var writer = new BinaryWriter(deflate))
                {
                    writer.Write(FileVersion);
                    writer.Write(snapshot.Count);
                    foreach (var (key, pixels) in snapshot)
                    {
                        writer.Write(key);
                        writer.Write(System.Runtime.InteropServices.MemoryMarshal.AsBytes(pixels.AsSpan()));
                    }
                }
                File.Move(tmpPath, filePath, overwrite: true);
            }
            catch (Exception e)
            {
                logger.Error("[backrooms] Could not save explored map to {0}: {1}", filePath, e.Message);
            }
        }
    }
}
