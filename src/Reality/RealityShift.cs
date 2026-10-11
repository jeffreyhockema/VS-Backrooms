using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;

namespace Backrooms.Reality;

/// <summary>
/// Reality Shifts: every so often the Backrooms itself destabilises for a few hours. The lights go out, and
/// everyone's stability drains wherever they are.
///
/// The schedule is a pure function of the world seed and the calendar, so the server and every client work it out
/// for themselves with nothing to synchronise or save. A shift can also be forced (the debug command does this);
/// that is passed to clients through a watched attribute on the player.
/// </summary>
public static class RealityShift
{
    /// <summary>Watched attribute on players: the calendar's elapsed hours (<see cref="IGameCalendar.ElapsedHours"/>) until which a forced shift lasts.</summary>
    public const string ForcedUntilAttribute = "backroomsShiftUntil";

    /// <summary>One shift happens somewhere in each period of this many in-game hours (an hour is 2 real minutes).</summary>
    private const double PeriodHours = 30;
    /// <summary>How long the lights take to fail and to come back.</summary>
    private const double RampHours = 0.15;

    private const ulong SaltShift = 0x5F17;

    /// <summary>Strength from 0 (normal) to 1 (full shift) of the scheduled shift at a given time (hours since the world began).</summary>
    public static double ScheduledStrength(long seed, double elapsedHours)
    {
        int period = (int)Math.Floor(elapsedHours / PeriodHours);
        if (period <= 0) return 0; // nothing in the first period: let newcomers find their feet

        ulong h = Hashing.Hash((ulong)seed, period, 0, SaltShift);
        double duration = 2 + 2 * Hashing.Unit(Hashing.Mix(h));
        double start = period * PeriodHours + 1 + Hashing.Unit(h) * (PeriodHours - duration - 2);
        return Ramp(elapsedHours - start, duration);
    }

    /// <summary>Strength of the shift, scheduled or forced, whichever is stronger (both in hours since the world began).</summary>
    public static double Strength(long seed, double elapsedHours, double forcedUntilHours)
    {
        double forced = forcedUntilHours > elapsedHours ? Math.Min(1, (forcedUntilHours - elapsedHours) / RampHours) : 0;
        return Math.Max(forced, ScheduledStrength(seed, elapsedHours));
    }

    /// <summary>Strength of the shift for the given side of the game right now.</summary>
    public static double CurrentStrength(ICoreAPI api, double forcedUntilHours)
    {
        // Hours since this world began (the calendar's total hours start hundreds of hours in, which would skip the
        // quiet first period and shift the whole schedule). The server sends its start with the calendar, so every
        // client counts the same hours.
        return Strength(api.World.Seed, api.World.Calendar.ElapsedHours, forcedUntilHours);
    }

    private static double Ramp(double sinceStart, double duration)
    {
        if (sinceStart < 0 || sinceStart > duration) return 0;
        return Math.Min(1, Math.Min(sinceStart, duration - sinceStart) / RampHours);
    }
}
