using System;
using System.Collections.Generic;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level 5's music, one source at a time. The turntables (in guest rooms, the lobby, the ballroom's corner and the Beverly
/// Room) and the speakers on the hotel walls used to carry the game's own ambient block sound, which starts one looping
/// copy of the jazz for every cluster of blocks within range, each at a random point in the tune: walk down a corridor
/// and several copies of the same record played out of step. Those blocks no longer carry that sound. Instead this
/// finds the music blocks in the chunks around the player and plays a single loop, at the nearest one that is "on".
/// Each source is on for a quarter of a six-minute cycle (the point of its window picked by where it stands), so most
/// of the time the hotel is silent. When the nearest on-source changes the old tune fades out, and only then does the
/// new one fade in, so two are never heard together. <c>.bkmusic</c> in chat tells which source is playing.
/// </summary>
public partial class AtmosphereSystem
{
    /// <summary>How far off, in blocks, a record can be heard.</summary>
    private const double HotelMusicRange = 16;
    private const double HotelCycleSeconds = 360, HotelOnSeconds = 90;
    private const float HotelFade = 2.5f, HotelVolume = 0.5f;

    private HashSet<int> hotelMusicIds;
    private readonly Dictionary<long, (double At, List<Vec3i> Sources)> hotelChunks = new();
    private ILoadedSound hotelTune, hotelFading;
    private Vec3i hotelSource;
    private double hotelScanAt, hotelLastDistance = -1;
    private int hotelCandidates;

    private void HotelMusicInit()
    {
        capi.ChatCommands.Create("bkmusic").WithDescription("Level 5, 94 and Fun: which music source is playing")
            .HandleWith(_ => TextCommandResult.Success(musicLevel switch
            {
                5 => hotelSource == null
                    ? $"Level 5: no music playing ({hotelCandidates} sources on nearby)."
                    : $"Level 5: playing the source at {hotelSource.X} {hotelSource.Y} {hotelSource.Z}, {hotelLastDistance:0.0} blocks away ({hotelCandidates} sources on nearby).",
                WorldLayout.FunLevel => FunMusicReport(),
                WorldLayout.Motion => sirenAt == null
                    ? $"Level 94: no siren tune (none of a town's poles within {TuneHeard} blocks, or it is night)."
                    : $"Level 94: siren pole at {sirenAt.Value.X} {sirenAt.Value.Z}, {sirenDistance:0.0} blocks away, volume {SirenVolume}, heard to {TuneHeard} blocks.",
                _ => "No music of this kind in this level (Levels 5, 94 and Fun have it).",
            }));
    }

    private static uint HotelHash(Vec3i p)
    {
        unchecked
        {
            uint h = (uint)(p.X * 73856093 ^ p.Y * 19349663 ^ p.Z * 83492791);
            h ^= h >> 15; h *= 2246822519u; h ^= h >> 13;
            return h;
        }
    }

    /// <summary>Whether the source at <paramref name="p"/> has its record on, at this many seconds of real time.</summary>
    private static bool HotelSourceOn(Vec3i p, double seconds) =>
        (seconds + HotelHash(p) % (uint)HotelCycleSeconds) % HotelCycleSeconds < HotelOnSeconds;

    private void HotelStop()
    {
        if (hotelTune != null)
        {
            ILoadedSound old = hotelTune;
            hotelTune = null;
            hotelFading = old;
            old.FadeOut(HotelFade, s =>
            {
                s.Stop();
                s.Dispose();
                if (hotelFading == s) hotelFading = null;
            });
        }
        hotelSource = null;
    }

    private void HotelSounds(float dt, EntityPos pos, bool here)
    {
        // The Beast of Level 5 about (his dread round this player, or him in sight): the music stops
        if (!here || Entities.BeastSystem.Hushed)
        {
            if (hotelTune != null || hotelSource != null) HotelStop();
            hotelCandidates = 0;
            return;
        }
        double now = Environment.TickCount64 / 1000.0;
        if (now < hotelScanAt) return;
        hotelScanAt = now + 0.5;

        if (hotelMusicIds == null)
        {
            hotelMusicIds = new HashSet<int>();
            foreach (Block block in capi.World.Blocks)
            {
                if (block.Code == null || block.Code.Domain != "backrooms") continue;
                string path = block.Code.Path;
                if (path == "turntable" || (path.StartsWith("hoteldeco-") && path.Contains("-speaker-"))) hotelMusicIds.Add(block.BlockId);
            }
        }
        if (hotelMusicIds.Count == 0) return;

        // The nearest source that is on, among the chunks around the player
        IBlockAccessor chunks = capi.World.BlockAccessor;
        int cs = GlobalConstants.ChunkSize;
        int pcx = (int)Math.Floor(pos.X) / cs, pcy = (int)Math.Floor(pos.Y) / cs, pcz = (int)Math.Floor(pos.Z) / cs;
        Vec3i best = null;
        double range2 = HotelMusicRange * HotelMusicRange, bestD = range2, currentD = double.MaxValue;
        hotelCandidates = 0;
        for (int dx = -1; dx <= 1; dx++)
            for (int dy = -1; dy <= 1; dy++)
                for (int dz = -1; dz <= 1; dz++)
                {
                    int cx = pcx + dx, cy = pcy + dy, cz = pcz + dz;
                    IWorldChunk chunk = chunks.GetChunk(cx, cy, cz);
                    if (chunk?.Data == null) continue;
                    long key = ((long)cx & 0xFFFFF) | (((long)cy & 0xFFF) << 20) | (((long)cz & 0xFFFFF) << 32);
                    if (!hotelChunks.TryGetValue(key, out var entry) || now > entry.At)
                    {
                        var found = new List<Vec3i>();
                        bool any = false;
                        foreach (int id in hotelMusicIds)
                            if (chunk.Data.ContainsBlock(id)) { any = true; break; }
                        if (any)
                            for (int i = 0; i < cs * cs * cs; i++)
                            {
                                if (!hotelMusicIds.Contains(chunk.Data.GetBlockIdUnsafe(i))) continue;
                                found.Add(new Vec3i(cx * cs + i % cs, cy * cs + i / (cs * cs), cz * cs + i / cs % cs));
                            }
                        entry = (now + 8, found);
                        hotelChunks[key] = entry;
                    }
                    foreach (Vec3i s in entry.Sources)
                    {
                        if (!HotelSourceOn(s, now)) continue;
                        double ex = s.X + 0.5 - pos.X, ey = s.Y + 0.5 - pos.Y, ez = s.Z + 0.5 - pos.Z;
                        double d = ex * ex + ey * ey + ez * ez;
                        if (d > range2) continue;
                        hotelCandidates++;
                        if (hotelSource != null && s.Equals(hotelSource)) currentD = d;
                        if (d < bestD) { bestD = d; best = s; }
                    }
                }
        if (hotelChunks.Count > 200) hotelChunks.Clear();

        // Keep the tune playing unless it has gone off or another source is clearly nearer (about four blocks)
        if (hotelSource != null)
        {
            bool stillOn = currentD < double.MaxValue;
            if (stillOn && (best == null || bestD > currentD - 16 || best.Equals(hotelSource)))
            {
                hotelLastDistance = Math.Sqrt(currentD);
                return;
            }
            HotelStop();
        }
        if (best == null || hotelFading != null) return; // one tune at a time: wait for the old one to fade
        hotelSource = best;
        hotelLastDistance = Math.Sqrt(bestD);
        hotelTune = capi.World.LoadSound(new SoundParams
        {
            Location = new AssetLocation("backrooms:sounds/ambient/jazz"), ShouldLoop = true, RelativePosition = false, DisposeOnFinish = false,
            Position = new Vec3f(best.X + 0.5f, best.Y + 0.5f, best.Z + 0.5f), Range = 20f, Volume = 0.01f, SoundType = EnumSoundType.Ambient,
        });
        if (hotelTune == null)
        {
            hotelSource = null;
            return;
        }
        hotelTune.Start();
        hotelTune.PlaybackPosition = (float)(Random.Shared.NextDouble() * hotelTune.SoundLengthSeconds);
        hotelTune.FadeTo(HotelVolume, HotelFade, _ => { });
    }
}
