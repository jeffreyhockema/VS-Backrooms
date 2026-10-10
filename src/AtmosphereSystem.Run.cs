using System;
using Backrooms.Regions;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level !'s air and sound on the client (kept as level 14). The base fog is a close red murk (its line in
/// <see cref="Levels"/>); while the alarm sounds it pulses, once a second, a slow swell, never a strobe. The Safe Zone is
/// clear and blue. The alarm is in your head, not anywhere in the hall: a murmur in the walls until the chained door
/// breaks, then deafening. The horde's roar comes from where its front is, so how loud it is is how near it is; a
/// heartbeat starts when it is within 20 blocks and quickens within 10. The server keeps the run's state on the player
/// (<see cref="RunSystem.PhaseKey"/> and its neighbours).
/// </summary>
public partial class AtmosphereSystem
{
    /// <summary>The Safe Zone's air: clear and blue.</summary>
    private static readonly Atmosphere RunSafeAir = new(0.006f, 0.42f, 0.56f, 0.85f, 0f);

    /// <summary>Title keys of the level's parts (level-1401 in the lang file: the Safe Zone).</summary>
    private const int RunSafeKey = 1401;

    private ILoadedSound runAlarm, runAlarmFar, runHorde, runHeart, runSafe;

    private void RunAir(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        Tile t = layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));
        if (t.Zone == WorldLayout.RunZone.Safe)
        {
            target = RunSafeAir;
            titleKey = RunSafeKey;
            return;
        }
        var phase = (RunSystem.Phase)(capi.World.Player?.Entity?.WatchedAttributes.GetInt(RunSystem.PhaseKey) ?? 0);
        if (phase != RunSystem.Phase.Alarm) return;
        // The alarm's pulse: a smooth swell of red once a second
        float pulse = 0.5f + 0.5f * (float)Math.Sin(capi.World.ElapsedMilliseconds / 1000.0 * Math.PI * 2);
        target = new Atmosphere(target.Density + 0.004f * pulse, Math.Min(1f, target.R * (0.85f + 0.3f * pulse)), target.G, target.B, target.GroundFog);
    }

    private void RunSounds(float dt, EntityPos pos, bool here)
    {
        var watched = capi.World.Player?.Entity?.WatchedAttributes;
        var phase = here && watched != null ? (RunSystem.Phase)watched.GetInt(RunSystem.PhaseKey) : RunSystem.Phase.None;
        float gap = watched?.GetFloat(RunSystem.GapKey, 999) ?? 999;
        double[] front = (watched?[RunSystem.FrontKey] as DoubleArrayAttribute)?.value;

        RunLoop(ref runAlarm, "ambient/run/alarm", phase == RunSystem.Phase.Alarm, 0.75f);
        RunLoop(ref runAlarmFar, "ambient/run/alarm-far", phase is RunSystem.Phase.Waiting or RunSystem.Phase.Safe, 0.45f);
        RunLoop(ref runSafe, "ambient/run/safezone", phase == RunSystem.Phase.Safe, 0.5f);
        RunLoop(ref runHorde, "ambient/run/horde", phase is RunSystem.Phase.Alarm or RunSystem.Phase.Safe && front != null, 1f, front, 64);
        RunLoop(ref runHeart, "effect/run/heartbeat", phase == RunSystem.Phase.Alarm && gap <= 20, 0.8f);
        runHeart?.SetPitch(gap <= 10 ? 1.25f : 1f);
    }

    /// <summary>Starts, moves or stops one of the level's loops: non-positional unless given a position.</summary>
    private void RunLoop(ref ILoadedSound sound, string path, bool on, float volume, double[] at = null, int range = 32)
    {
        if (!on)
        {
            if (sound == null) return;
            sound.Stop();
            sound.Dispose();
            sound = null;
            return;
        }
        if (sound == null)
        {
            sound = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/" + path), ShouldLoop = true, DisposeOnFinish = false,
                RelativePosition = at == null, Position = at == null ? new Vec3f() : new Vec3f((float)at[0], (float)at[1], (float)at[2]),
                Range = range, Volume = volume, SoundType = EnumSoundType.Ambient,
            });
            sound?.Start();
        }
        else if (at != null) sound.SetPosition((float)at[0], (float)at[1], (float)at[2]);
    }
}
