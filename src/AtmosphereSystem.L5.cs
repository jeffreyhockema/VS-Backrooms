using System;
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

    private BlockFinder hotelSpeakers;
    private MusicVoice hotelVoice;
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

    /// <summary>Whether the source at <paramref name="p"/> has its record on, at this many seconds of real time.</summary>
    private static bool HotelSourceOn(Vec3i p, double seconds) =>
        (seconds + MusicHash(p) % (uint)HotelCycleSeconds) % HotelCycleSeconds < HotelOnSeconds;

    private void HotelSounds(float dt, EntityPos pos, bool here)
    {
        hotelVoice ??= new MusicVoice(capi);
        // The Beast of Level 5 about (his dread round this player, or him in sight): the music stops
        if (!here || Entities.BeastSystem.Hushed)
        {
            hotelVoice.Set(null, null, 0, 0, HotelFade, HotelFade);
            hotelSource = null;
            hotelCandidates = 0;
            return;
        }
        double now = Environment.TickCount64 / 1000.0;
        if (now < hotelScanAt) return;
        hotelScanAt = now + 0.5;

        hotelSpeakers ??= new BlockFinder(capi, b => b.Code.Path == "turntable"
            || (b.Code.Path.StartsWith("hoteldeco-", StringComparison.Ordinal) && b.Code.Path.Contains("-speaker-", StringComparison.Ordinal)));

        // The nearest source that is on, among the chunks around the player
        Vec3i best = null;
        double bestD = double.MaxValue, currentD = double.MaxValue;
        hotelCandidates = 0;
        foreach (var (s, d2) in hotelSpeakers.Near(pos, HotelMusicRange, now))
        {
            if (!HotelSourceOn(s, now)) continue;
            hotelCandidates++;
            if (hotelSource != null && s.Equals(hotelSource)) currentD = d2;
            if (d2 < bestD) { bestD = d2; best = s; }
        }

        // Keep the tune playing unless it has gone off or another source is clearly nearer (about four blocks)
        Vec3i chosen = best;
        double chosenD = bestD;
        if (hotelSource != null && currentD < double.MaxValue && (best == null || bestD > currentD - 16 || best.Equals(hotelSource)))
        {
            chosen = hotelSource;
            chosenD = currentD;
        }
        hotelSource = chosen;
        if (chosen == null)
        {
            hotelVoice.Set(null, null, 0, 0, HotelFade, HotelFade);
            return;
        }
        hotelLastDistance = Math.Sqrt(chosenD);
        hotelVoice.Set("ambient/jazz", new Vec3f(chosen.X + 0.5f, chosen.Y + 0.5f, chosen.Z + 0.5f), 20f, HotelVolume, HotelFade, HotelFade);
    }
}
