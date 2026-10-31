using System;
using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// One looping tune heard from one place, for the levels whose music must never pile up (Level 94's siren poles, Level
/// Fun's speakers). Ask it every tick what should be heard (<see cref="Set"/>): when the wish changes the old tune fades
/// out, and only once it is gone does the new one fade in at a random point of the loop, so two tunes of one voice are
/// never heard together. Client-side only; nothing is saved.
/// </summary>
public sealed class MusicVoice
{
    private readonly ICoreClientAPI capi;
    private ILoadedSound tune, fading;
    private string key;

    public MusicVoice(ICoreClientAPI capi) => this.capi = capi;

    /// <summary>The sounds this voice has loaded, so the owner can stop them when the world closes.</summary>
    public IEnumerable<ILoadedSound> Loaded() { yield return tune; yield return fading; }

    /// <summary>Plays <paramref name="track"/> (an asset path under sounds/) at a place; a null track silences it.</summary>
    public void Set(string track, Vec3f at, float range, float volume, float fadeIn = 2.5f, float fadeOut = 2.5f)
    {
        string want = track == null ? null : track + "@" + (int)Math.Floor(at.X) + "," + (int)Math.Floor(at.Y) + "," + (int)Math.Floor(at.Z);
        if (want == key && (want == null || tune != null)) return;
        if (tune != null)
        {
            ILoadedSound old = tune;
            tune = null;
            fading = old;
            old.FadeOut(fadeOut, s =>
            {
                s.Stop();
                s.Dispose();
                if (fading == s) fading = null;
            });
        }
        key = null;
        if (want == null || fading != null) return; // one tune at a time: wait for the old one to fade
        tune = capi.World.LoadSound(new SoundParams
        {
            Location = new AssetLocation("backrooms:sounds/" + track), ShouldLoop = true, RelativePosition = false, DisposeOnFinish = false,
            Position = at, Range = range, Volume = 0.01f, SoundType = EnumSoundType.Ambient,
        });
        if (tune == null) return;
        key = want;
        tune.Start();
        tune.PlaybackPosition = (float)(Random.Shared.NextDouble() * tune.SoundLengthSeconds);
        tune.FadeTo(volume, fadeIn, _ => { });
    }
}

/// <summary>
/// Finds the blocks of a kind in the chunks around a player, remembering each chunk's blocks for a few seconds so the
/// scan is cheap to repeat. Used for music sources that are placed blocks.
/// </summary>
public sealed class BlockFinder
{
    private readonly ICoreClientAPI capi;
    private readonly System.Func<Block, bool> isSource;
    private HashSet<int> ids;
    private readonly Dictionary<long, (double At, List<Vec3i> Found)> chunks = new();

    public BlockFinder(ICoreClientAPI capi, System.Func<Block, bool> isSource)
    {
        this.capi = capi;
        this.isSource = isSource;
    }

    /// <summary>Every such block in the 27 chunks round <paramref name="pos"/> within the range, with its squared distance.</summary>
    public List<(Vec3i At, double D2)> Near(EntityPos pos, double range, double now)
    {
        var result = new List<(Vec3i, double)>();
        if (ids == null)
        {
            ids = new HashSet<int>();
            foreach (Block block in capi.World.Blocks)
                if (block.Code != null && block.Code.Domain == "backrooms" && isSource(block)) ids.Add(block.BlockId);
        }
        if (ids.Count == 0) return result;
        IBlockAccessor access = capi.World.BlockAccessor;
        int cs = GlobalConstants.ChunkSize;
        int pcx = (int)Math.Floor(pos.X) / cs, pcy = (int)Math.Floor(pos.Y) / cs, pcz = (int)Math.Floor(pos.Z) / cs;
        double range2 = range * range;
        for (int dx = -1; dx <= 1; dx++)
            for (int dy = -1; dy <= 1; dy++)
                for (int dz = -1; dz <= 1; dz++)
                {
                    int cx = pcx + dx, cy = pcy + dy, cz = pcz + dz;
                    IWorldChunk chunk = access.GetChunk(cx, cy, cz);
                    if (chunk?.Data == null) continue;
                    long key = ((long)cx & 0xFFFFF) | (((long)cy & 0xFFF) << 20) | (((long)cz & 0xFFFFF) << 32);
                    if (!chunks.TryGetValue(key, out var entry) || now > entry.At)
                    {
                        var found = new List<Vec3i>();
                        bool any = false;
                        foreach (int id in ids)
                            if (chunk.Data.ContainsBlock(id)) { any = true; break; }
                        if (any)
                            for (int i = 0; i < cs * cs * cs; i++)
                            {
                                if (!ids.Contains(chunk.Data.GetBlockIdUnsafe(i))) continue;
                                found.Add(new Vec3i(cx * cs + i % cs, cy * cs + i / (cs * cs), cz * cs + i / cs % cs));
                            }
                        entry = (now + 8, found);
                        chunks[key] = entry;
                    }
                    foreach (Vec3i s in entry.Found)
                    {
                        double ex = s.X + 0.5 - pos.X, ey = s.Y + 0.5 - pos.Y, ez = s.Z + 0.5 - pos.Z, d2 = ex * ex + ey * ey + ez * ez;
                        if (d2 <= range2) result.Add((s, d2));
                    }
                }
        if (chunks.Count > 200) chunks.Clear();
        return result;
    }
}
