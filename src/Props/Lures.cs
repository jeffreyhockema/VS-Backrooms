using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Props;

/// <summary>
/// Whatever rings for a while: the fire bell, a car alarm, an alarm clock, a radio. Each puts its noise on the noise bus
/// once a second while it lasts (the bus keeps a noise two seconds), so whatever hunts by ear and hears it (its hearing
/// times the loudness) comes to see; the sound is played again as each clip ends.
/// </summary>
public partial class PropSystem
{
    /// <summary>How loud each kind is on the noise bus (a Hound, hearing 32, hears a loudness of 1 at 32 blocks).</summary>
    public const double FireAlarmLoudness = 1.25, CarAlarmLoudness = 1.3, AlarmClockLoudness = 1.0, RadioLoudness = 0.8, TurntableLoudness = 0.7;

    /// <summary>How long each rings (ms): the fire bell, a car alarm, an alarm clock, a radio.</summary>
    public const int FireAlarmMs = 25_000, CarAlarmMs = 30_000, AlarmClockMs = 15_000, RadioMs = 40_000;

    /// <summary>How long (ms) before a struck car's alarm will go again.</summary>
    public const long CarRearmMs = 180_000;

    private sealed class Ring
    {
        public BlockPos Pos;
        public string Kind;
        public long EndMs, NextSoundMs, NextNoiseMs;
        public long SoundEveryMs;
        public string Sound;
        public float Range, Volume;
        public double Loudness;
        /// <summary>Whom the noise gives away (the one who set it going), or -1.</summary>
        public long Who = -1;
        /// <summary>The first code part of the block that rings (it stops when that block is broken or replaced).</summary>
        public string Block;
    }

    private readonly List<Ring> rings = new();
    private readonly Dictionary<long, long> carRearmMs = new();

    /// <summary>Starts something ringing at a block (replacing whatever rang there). Returns whether it started.</summary>
    internal bool StartRing(string kind, BlockPos pos, Entity who)
    {
        long now = sapi.World.ElapsedMilliseconds;
        (string sound, long every, int ms, double loud, float range, float volume) = kind switch
        {
            "firealarm" => ("backrooms:sounds/effect/props/firebell", 2000L, FireAlarmMs, FireAlarmLoudness, 64f, 1f),
            "caralarm" => ("backrooms:sounds/effect/props/caralarm", 2000L, CarAlarmMs, CarAlarmLoudness, 64f, 1f),
            "alarmclock" => ("backrooms:sounds/effect/props/alarmclock", 1000L, AlarmClockMs, AlarmClockLoudness, 40f, 1f),
            "radio" => ("backrooms:sounds/effect/props/radio", 4000L, RadioMs, RadioLoudness, 32f, 0.9f),
            // (The jazz record: 16.5 s a side, played through twice)
            "turntable" => ("backrooms:sounds/ambient/jazz", 16_550L, 33_100, TurntableLoudness, 32f, 0.9f),
            _ => (null, 0L, 0, 0.0, 0f, 0f),
        };
        if (sound == null) return false;
        StopRing(pos);
        rings.Add(new Ring
        {
            Pos = pos.Copy(), Kind = kind, EndMs = now + ms, NextSoundMs = now, NextNoiseMs = now, SoundEveryMs = every, Sound = sound,
            Range = range, Volume = volume, Loudness = loud, Who = who?.EntityId ?? -1,
            Block = sapi.World.BlockAccessor.GetBlock(pos)?.FirstCodePart(),
        });
        // Whoever set it going is heard by it too: what hunts them knows where it was done
        if (who is EntityPlayer && director != null) director.MakeNoise(who, 0.4, Centre(pos), loud, kind);
        sapi.Logger.Notification("[backrooms] props: {0} at {1} {2} {3} rings for {4} s{5}", kind, pos.X, pos.Y, pos.Z, ms / 1000,
            who == null ? "" : " (set going by " + who.Code.Path + " #" + who.EntityId + ")");
        return true;
    }

    /// <summary>Stops whatever rings at a block. Returns whether something was.</summary>
    internal bool StopRing(BlockPos pos) => rings.RemoveAll(r => r.Pos.Equals(pos)) > 0;

    /// <summary>Whether something rings at a block now, and of what kind.</summary>
    internal string RingingAt(BlockPos pos)
    {
        foreach (Ring r in rings)
            if (r.Pos.Equals(pos)) return r.Kind;
        return null;
    }

    private void TickRings(long now)
    {
        for (int i = rings.Count - 1; i >= 0; i--)
        {
            Ring r = rings[i];
            // (Broken, or gone with its chunk: it stops)
            if (now >= r.EndMs || sapi.World.BlockAccessor.GetBlock(r.Pos)?.FirstCodePart() != r.Block)
            {
                rings.RemoveAt(i);
                continue;
            }
            if (now >= r.NextSoundMs)
            {
                r.NextSoundMs += r.SoundEveryMs;
                // (Not at all if the clip would run on past the end by more than half of it)
                if (r.EndMs - now > r.SoundEveryMs / 2) Play(r.Sound, r.Pos, r.Range, r.Volume);
            }
            if (now >= r.NextNoiseMs)
            {
                r.NextNoiseMs += 1000;
                director?.RaiseNoise(Centre(r.Pos), r.Loudness, r.Kind, r.Who < 0 ? null : sapi.World.GetEntityById(r.Who));
            }
        }
    }

    // ================= Car alarms =================

    /// <summary>The block that draws a car (car-colour-side) at or round a block of it (a collider), or null.</summary>
    private BlockPos CarAt(BlockPos pos)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        if (ba.GetBlock(pos).FirstCodePart() == "car") return pos.Copy();
        BlockPos best = null;
        int bestD = int.MaxValue;
        var p = new BlockPos(pos.dimension);
        for (int dy = -1; dy <= 1; dy++)
            for (int dz = -4; dz <= 4; dz++)
                for (int dx = -4; dx <= 4; dx++)
                {
                    p.Set(pos.X + dx, pos.Y + dy, pos.Z + dz);
                    Block b = ba.GetBlock(p);
                    if (b?.Code?.Domain != "backrooms" || b.FirstCodePart() != "car") continue;
                    int d = dx * dx + dy * dy + dz * dz;
                    if (d < bestD) { bestD = d; best = p.Copy(); }
                }
        return best;
    }

    /// <summary>
    /// A car struck: its alarm blares for <see cref="CarAlarmMs"/>. A burnt-out wreck has nothing left to blare with, one
    /// wreck in three has a flat battery (always the same ones), and a car that has blared rests three minutes.
    /// </summary>
    internal void StrikeCar(BlockPos pos, IPlayer byPlayer)
    {
        BlockPos car = CarAt(pos) ?? pos.Copy();
        Block block = sapi.World.BlockAccessor.GetBlock(car);
        string colour = block.Variant?["colour"];
        if (colour == "burnt")
        {
            Tell(byPlayer, "props-car-burnt");
            return;
        }
        long now = sapi.World.ElapsedMilliseconds;
        bool flat = colour != null && colour.EndsWith("wreck", StringComparison.Ordinal) && Hash(car) % 3 == 0;
        if (flat || carRearmMs.TryGetValue(Key(car), out long rearm) && now < rearm || RingingAt(car) != null)
        {
            Play("game:sounds/effect/latch", car, 12, 0.6f);
            if (RingingAt(car) == null) Tell(byPlayer, "props-car-dead");
            return;
        }
        carRearmMs[Key(car)] = now + CarAlarmMs + CarRearmMs;
        StartRing("caralarm", car, byPlayer?.Entity);
    }

    private static uint Hash(BlockPos p)
    {
        unchecked
        {
            uint h = (uint)p.X * 73856093u ^ (uint)p.Y * 19349663u ^ (uint)p.Z * 83492791u;
            h ^= h >> 13;
            h *= 0x5bd1e995;
            return h ^ (h >> 15);
        }
    }

    // ================= Radios =================

    /// <summary>A radio switched: on, it plays for <see cref="RadioMs"/> (a turntable, its record twice through); on again, off.</summary>
    internal void SwitchRadio(BlockPos pos, Block block, IPlayer byPlayer)
    {
        if (StopRing(pos))
        {
            Play("game:sounds/effect/woodswitch", pos, 12, 0.8f);
            return;
        }
        Play("game:sounds/effect/woodswitch", pos, 12, 0.8f);
        StartRing(block.Code.Path == "turntable" ? "turntable" : "radio", pos, byPlayer?.Entity);
    }
}
