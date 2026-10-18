using System;
using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level Fun's birthday song. The wall speakers over the party rooms' doors (fun-speaker-on) used to carry the game's own
/// ambient block sound, one copy of the tune for every cluster of speakers in range, each at its own point of the tune,
/// without a limit. They no longer do; instead this plays the song from at most two speakers at once: the nearest one,
/// quietly, and, only sometimes, a second one in the next room over, fading in and out as that speaker's window (a third
/// of a three-minute cycle, its place picked by where it hangs) opens and closes. A little overlap of the same song a
/// few seconds apart suits the place; more than two never.
/// </summary>
public partial class AtmosphereSystem
{
    private const double FunMusicRange = 18, FunSecondRange = 11;
    private const double FunCycleSeconds = 180, FunSecondOnSeconds = 60;
    private const float FunMusicVolume = 0.3f, FunSecondVolume = 0.2f, FunMusicSoundRange = 20f;

    private BlockFinder funSpeakers;
    private MusicVoice funVoiceA, funVoiceB;
    private double funMusicScanAt;
    private Vec3i funSourceA, funSourceB;
    private int funMusicCandidates;

    private static uint MusicHash(Vec3i p)
    {
        unchecked
        {
            uint h = (uint)(p.X * 73856093 ^ p.Y * 19349663 ^ p.Z * 83492791);
            h ^= h >> 15; h *= 2246822519u; h ^= h >> 13;
            return h;
        }
    }

    private static bool FunSecondOn(Vec3i p, double now) => (now + MusicHash(p) % (uint)FunCycleSeconds) % FunCycleSeconds < FunSecondOnSeconds;

    private void FunMusic(EntityPos pos, bool here)
    {
        funVoiceA ??= new MusicVoice(capi);
        funVoiceB ??= new MusicVoice(capi);
        if (!here)
        {
            funVoiceA.Set(null, null, 0, 0);
            funVoiceB.Set(null, null, 0, 0);
            funSourceA = funSourceB = null;
            funMusicCandidates = 0;
            return;
        }
        double now = Environment.TickCount64 / 1000.0;
        if (now < funMusicScanAt) return;
        funMusicScanAt = now + 0.5;
        funSpeakers ??= new BlockFinder(capi, b => b.Code.Path.StartsWith("fun-speaker-on-"));
        var near = funSpeakers.Near(pos, FunMusicRange, now);
        near.Sort((x, y) => x.D2.CompareTo(y.D2));
        funMusicCandidates = near.Count;

        // The first voice: the nearest speaker, kept unless another is clearly nearer (about four blocks)
        Vec3i a = near.Count > 0 ? near[0].At : null;
        if (a != null && funSourceA != null && !funSourceA.Equals(a))
            foreach (var (at, d2) in near)
                if (at.Equals(funSourceA) && d2 < near[0].D2 + 16) { a = at; break; }
        funSourceA = a;

        // The second: another speaker within a modest range while its window is open; the one already playing stays while it is
        double r2 = FunSecondRange * FunSecondRange;
        Vec3i b = null;
        foreach (var (at, d2) in near)
        {
            if (d2 > r2 || (a != null && at.Equals(a)) || !FunSecondOn(at, now)) continue;
            if (b == null) b = at;
            if (funSourceB != null && at.Equals(funSourceB)) { b = at; break; }
        }
        funSourceB = b;

        funVoiceA.Set(a == null ? null : "ambient/fun/funtune", a == null ? null : new Vec3f(a.X + 0.5f, a.Y + 0.5f, a.Z + 0.5f), FunMusicSoundRange, FunMusicVolume);
        funVoiceB.Set(b == null ? null : "ambient/fun/funtune", b == null ? null : new Vec3f(b.X + 0.5f, b.Y + 0.5f, b.Z + 0.5f), FunMusicSoundRange, FunSecondVolume, 4f, 4f);
    }

    private string FunMusicReport() =>
        funSourceA == null ? $"Level Fun: no birthday song ({funMusicCandidates} speakers on within {FunMusicRange} blocks)."
        : $"Level Fun: song from {funSourceA.X} {funSourceA.Y} {funSourceA.Z}"
          + (funSourceB == null ? "" : $" and a second from {funSourceB.X} {funSourceB.Y} {funSourceB.Z}")
          + $" ({funMusicCandidates} speakers on within {FunMusicRange} blocks).";
}
