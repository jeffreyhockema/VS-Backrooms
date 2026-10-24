using System;
using System.Collections.Generic;
using System.Globalization;

namespace Backrooms.Needs;

/// <summary>
/// The numbers of thirst and fatigue (docs/design/needs/README.md, sections 2 to 6), with no game dependencies, so the
/// behaviours, the director and <c>/backrooms needstest</c> share one copy of each rule.
/// </summary>
public static class NeedsMath
{
    // ================= Thirst =================

    /// <summary>Hydration lost per real second at the default calendar: walking (and standing within 3 s of moving).</summary>
    public const float DrainMoving = 1.0f;

    /// <summary>Added per real second spent sprinting (vanilla hunger's shape: on top of the walking drain).</summary>
    public const float DrainSprintExtra = 1.5f;

    /// <summary>Idle for longer than this (ms), the drain is quartered.</summary>
    public const long IdleAfterMs = 3000;

    /// <summary>Below this fraction of the meter the player slows, down to <see cref="ThirstSlowAtEmpty"/> at empty.</summary>
    public const float ThirstSlowFrom = 0.4f, ThirstSlowAtEmpty = -0.25f;

    /// <summary>Below this fraction the Wretch counts you as parched; below <see cref="WakeFraction"/> thirst or hunger wakes (and refuses) sleep.</summary>
    public const float ParchedFraction = 0.25f, WakeFraction = 0.1f;

    /// <summary>At empty: damage every <see cref="EmptyDamageSeconds"/> and the stability offset.</summary>
    public const float EmptyDamage = 0.2f, EmptyDamageSeconds = 6f, EmptyStability = -0.2f;

    /// <summary>Gut rot: added to thirstrate and hungerrate.</summary>
    public const float SickRate = 0.5f;

    /// <summary>
    /// Hydration lost over <paramref name="seconds"/> real seconds, <paramref name="sprintSeconds"/> of them sprinting
    /// (hunger's shape: 1 a second, 1.5 more a sprinting second, a quarter of that when idle), times the calendar factor
    /// (<c>SpeedOfTime * CalendarSpeedMul / 30</c>, 1 at the default calendar) and the blended <c>thirstrate</c> stat.
    /// </summary>
    public static float Drain(float seconds, float sprintSeconds, bool idle, float calendarFactor, float thirstRate)
    {
        float drain = DrainMoving * seconds + DrainSprintExtra * sprintSeconds;
        if (idle) drain /= 4f;
        return drain * calendarFactor * thirstRate;
    }

    /// <summary>The walkspeed stat for a hydration fraction: 0 above 40%, falling linearly to -0.25 at empty.</summary>
    public static float ThirstWalk(float fraction) =>
        fraction >= ThirstSlowFrom ? 0f : ThirstSlowAtEmpty * (ThirstSlowFrom - Math.Max(0f, fraction)) / ThirstSlowFrom;

    // ================= Fatigue =================

    /// <summary>The vanilla <c>tiredness</c> value for awake hours: 8 at 24 h (vanilla's bed gate opens above 8), 12 at 60 h and on.</summary>
    public static float Tiredness(float awake) =>
        awake < Needs.DrowsyHours ? 8f * Math.Max(0f, awake) / Needs.DrowsyHours : Math.Min(12f, 8f + 4f * (awake - Needs.DrowsyHours) / (Needs.DeadHours - Needs.DrowsyHours));

    /// <summary>The walkspeed stat from fatigue: -10% exhausted, -20% dead on your feet, nothing while caffeinated.</summary>
    public static float FatigueWalk(float awake, bool caffeinated) =>
        caffeinated ? 0f : awake >= Needs.DeadHours ? -0.2f : awake >= Needs.ExhaustedHours ? -0.1f : 0f;

    /// <summary>Awake hours at which the stability offset starts, and the offset at <see cref="Needs.DeadHours"/> and on.</summary>
    public const float StabilityFromHours = 30f, StabilityAtDead = -0.5f;

    /// <summary>The fatigue stability offset: 0 at 30 awake hours, -0.5 at 60 and on, nothing while caffeinated.</summary>
    public static float FatigueStability(float awake, bool caffeinated) =>
        caffeinated ? 0f : StabilityAtDead * Math.Clamp((awake - StabilityFromHours) / (Needs.DeadHours - StabilityFromHours), 0f, 1f);

    /// <summary>Awake hours one slept game hour removes in a bed of this quality (1: 60 hours in 8).</summary>
    public static float RestPerHour(float quality) => Needs.RestPerSleptHour * quality;

    /// <summary>The bed quality when nothing better is known.</summary>
    public const float DefaultQuality = 0.6f;

    /// <summary>Hours a crash adds when caffeine wears off, per cup.</summary>
    public const float CrashHours = 8f;

    /// <summary>Green Almond Water: the new caffeine end (extends from now or from the current end) and crash hours (8 more a cup).</summary>
    public static (double Until, float Crash) Caffeinate(double now, double until, float crash, double hours) =>
        (Math.Max(now, until) + hours, crash + CrashHours);

    /// <summary>The fatigue band's name.</summary>
    public static string Band(float awake) =>
        awake >= Needs.DeadHours ? "dead on your feet" : awake >= Needs.ExhaustedHours ? "exhausted" : awake >= Needs.DrowsyHours ? "drowsy" : "rested";

    /// <summary>The thirst band's name.</summary>
    public static string ThirstBand(float fraction) =>
        fraction <= 0 ? "empty" : fraction < ParchedFraction ? "parched" : fraction < ThirstSlowFrom ? "thirsty" : "fine";

    // ================= Director =================

    /// <summary>
    /// The director's multiplier on spawn odds (section 6): 1 below 24 awake hours, ramping to 2.5 at 60 and 3.5 at 84;
    /// 0.5 more with thirst empty. Caffeine holds the fatigue part at 1 (it does nothing for thirst).
    /// </summary>
    public static double DirectorMult(float awake, bool fatigueOn, bool caffeinated, bool thirstEmpty)
    {
        double mult = 1;
        if (fatigueOn && !caffeinated && awake > Needs.DrowsyHours)
            mult = awake <= Needs.DeadHours
                ? 1 + 1.5 * (awake - Needs.DrowsyHours) / (Needs.DeadHours - Needs.DrowsyHours)
                : 2.5 + Math.Min(1.0, (awake - Needs.DeadHours) / (Needs.CapHours - Needs.DeadHours));
        if (thirstEmpty) mult += 0.5;
        return mult;
    }

    /// <summary>Per slept game hour outside the Safe band: the chance of a night visit.</summary>
    public const double VisitPerHour = 0.06, DoorFactor = 0.5;

    public static double VisitChance(double danger, double spawns, bool closedDoor) =>
        Math.Max(0, VisitPerHour * danger * spawns * (closedDoor ? DoorFactor : 1));

    /// <summary>The chance of at least one visit over <paramref name="hours"/> slept hours.</summary>
    public static double VisitOver(double perHour, double hours) => 1 - Math.Pow(1 - Math.Clamp(perHour, 0, 1), hours);

    // ================= Self-test =================

    /// <summary>The pure-math checks behind <c>/backrooms needstest</c>: one line each, "PASS ..." or "FAIL ...".</summary>
    public static List<string> SelfTest(Func<int, double> dangerOf)
    {
        var lines = new List<string>();
        void Check(string what, double got, double want, double tolerance)
        {
            bool ok = Math.Abs(got - want) <= tolerance;
            lines.Add(string.Format(CultureInfo.InvariantCulture, "{0} {1}: {2:0.####} (want {3:0.####})", ok ? "PASS" : "FAIL", what, got + 0.0, want));
        }

        // The clock (section 2): water full to empty in 12.5 game hours walking, 50 idle (a game hour is 120 real s at the default calendar)
        Check("thirst: walking 12.5 game hours drains", Drain(12.5f * 120, 0, false, 1, 1), Needs.MaxHydration, 0.5);
        Check("thirst: idle 50 game hours drains", Drain(50f * 120, 0, true, 1, 1), Needs.MaxHydration, 0.5);
        Check("thirst: two real minutes walking drain", Drain(120, 0, false, 1, 1), 120, 0.01);
        Check("thirst: a sprinting second drains", Drain(1, 1, false, 1, 1), 2.5, 0.001);
        // A full night (8 game hours) costs about 240 whatever the clock speed: at the sleep clock (factor 284) it is 960/284 real s
        Check("thirst: 8 slept hours at the default clock", Drain(8 * 120, 0, true, 1, 1), 240, 0.5);
        Check("thirst: 8 slept hours at the sleep clock", Drain(8 * 120 / 284f, 0, true, 284, 1), 240, 0.5);
        Check("thirst: heat at its worst (thirstrate 1.5)", Drain(120, 0, false, 1, 1.5f), 180, 0.01);
        Check("thirst: walkspeed at 40%", ThirstWalk(0.4f), 0, 1e-6);
        Check("thirst: walkspeed at 20%", ThirstWalk(0.2f), -0.125, 1e-6);
        Check("thirst: walkspeed at empty", ThirstWalk(0f), -0.25, 1e-6);

        // Fatigue bands and vanilla's tiredness (its bed gate is tiredness > 8)
        Check("fatigue: tiredness at 0 h", Tiredness(0), 0, 1e-6);
        Check("fatigue: tiredness at 24 h", Tiredness(24), 8, 1e-5);
        Check("fatigue: vanilla gate shut at 23.9 h", Tiredness(23.9f) > 8 ? 1 : 0, 0, 0);
        Check("fatigue: vanilla gate open at 24.1 h", Tiredness(24.1f) > 8 ? 1 : 0, 1, 0);
        Check("fatigue: tiredness at 60 h", Tiredness(60), 12, 1e-5);
        Check("fatigue: tiredness at 84 h (capped)", Tiredness(84), 12, 1e-5);
        Check("fatigue: walkspeed at 44.9 h", FatigueWalk(44.9f, false), 0, 1e-6);
        Check("fatigue: walkspeed at 45 h", FatigueWalk(45, false), -0.1, 1e-6);
        Check("fatigue: walkspeed at 60 h", FatigueWalk(60, false), -0.2, 1e-6);
        Check("fatigue: walkspeed at 60 h, caffeinated", FatigueWalk(60, true), 0, 1e-6);
        Check("fatigue: stability at 30 h", FatigueStability(30, false), 0, 1e-6);
        Check("fatigue: stability at 45 h", FatigueStability(45, false), -0.25, 1e-6);
        Check("fatigue: stability at 60 h", FatigueStability(60, false), -0.5, 1e-6);
        Check("fatigue: stability at 84 h", FatigueStability(84, false), -0.5, 1e-6);
        Check("fatigue: stability at 70 h, caffeinated", FatigueStability(70, true), 0, 1e-6);
        Check("fatigue: band at 23.9 h is rested", Band(23.9f) == "rested" ? 1 : 0, 1, 0);
        Check("fatigue: band at 24 h is drowsy", Band(24) == "drowsy" ? 1 : 0, 1, 0);
        Check("fatigue: band at 45 h is exhausted", Band(45) == "exhausted" ? 1 : 0, 1, 0);
        Check("fatigue: band at 60 h is dead on your feet", Band(60) == "dead on your feet" ? 1 : 0, 1, 0);
        Check("rest: a good bed, 8 slept hours", 8 * RestPerHour(1f), 60, 1e-4);
        Check("rest: a bedroll, hours to rest 60", 60 / RestPerHour(DefaultQuality), 13.333, 0.001);
        var (until, crash) = Caffeinate(100, 0, 0, 10);
        Check("caffeine: one cup lasts to", until, 110, 1e-9);
        (until, crash) = Caffeinate(105, until, crash, 10);
        Check("caffeine: a second cup extends to", until, 120, 1e-9);
        Check("caffeine: two cups crash", crash, 16, 1e-6);

        // The director (section 6)
        Check("director: 0 awake h", DirectorMult(0, true, false, false), 1, 1e-9);
        Check("director: 24 awake h", DirectorMult(24, true, false, false), 1, 1e-9);
        Check("director: 42 awake h", DirectorMult(42, true, false, false), 1.75, 1e-9);
        Check("director: 60 awake h", DirectorMult(60, true, false, false), 2.5, 1e-9);
        Check("director: 70 awake h", DirectorMult(70, true, false, false), 2.9167, 1e-4);
        Check("director: 84 awake h", DirectorMult(84, true, false, false), 3.5, 1e-9);
        Check("director: 84 awake h and thirst empty", DirectorMult(84, true, false, true), 4, 1e-9);
        Check("director: 70 awake h, caffeinated", DirectorMult(70, true, true, false), 1, 1e-9);
        Check("director: 70 awake h, fatigue off", DirectorMult(70, false, false, false), 1, 1e-9);
        Check("director: rested, thirst empty", DirectorMult(0, true, false, true), 1.5, 1e-9);

        // Night visits (section 4): a full sleep is 8 slept hours
        Check("visits: Level 0 (danger 0), full sleep", VisitOver(VisitChance(dangerOf(0), 1, false), 8), 0, 1e-9);
        Check("visits: Level 1, per hour", VisitChance(dangerOf(1), 1, false), 0.06 * dangerOf(1), 1e-9);
        Check("visits: Level 1, shut door halves", VisitChance(dangerOf(1), 1, true), 0.03 * dangerOf(1), 1e-9);
        Check("visits: Level 5, full sleep", VisitOver(VisitChance(dangerOf(5), 1, false), 8), 1 - Math.Pow(1 - 0.06 * dangerOf(5), 8), 1e-9);
        Check("visits: Level 11, full sleep at least 30%", VisitOver(VisitChance(dangerOf(11), 1, false), 8) >= 0.3 ? 1 : 0, 1, 0);
        return lines;
    }
}
