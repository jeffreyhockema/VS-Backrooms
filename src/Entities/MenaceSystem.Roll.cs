using System;
using System.Text;
using Backrooms.Worldgen;
using Vintagestory.API.Common;

namespace Backrooms.Entities;

/// <summary>What one tick of the director's rolls came to.</summary>
public enum RollKind
{
    Nothing,
    /// <summary>A distant sound.</summary>
    Sound,
    /// <summary>A body: something seen far off.</summary>
    Glimpse,
    /// <summary>A body: something following.</summary>
    Stalk,
    /// <summary>A body: something hunting.</summary>
    Hunt,
}

/// <summary>
/// The director's rolls as rates (docs/design/entity-ai-overhaul/isolation.md 4.1): bodies and sounds each have a mean real-minute
/// interval, and a hard minimum gap after the last of their kind. Pure: everything it needs is passed in, so the rate check
/// (/backrooms ratecheck) can run it over simulated hours.
/// </summary>
public static class EncounterRoll
{
    /// <summary>How often the director ticks (seconds).</summary>
    public const double TickSeconds = 2;

    /// <summary>The hard gap after the last body (or sound), as a share of the mean interval; the random wait after it makes up the rest, so the mean stays as stated.</summary>
    public const double HardGapShare = 0.4;

    /// <summary>The menace factor on both intervals: (1.5 - menace), clamped. A calm player waits longer, an unsteady one at the edge less.</summary>
    public const double MenaceFactorBase = 1.5, MenaceFactorMin = 0.5, MenaceFactorMax = 1.5;

    /// <summary>The mean interval (real milliseconds) between bodies, or infinity where none come (the Safe band).</summary>
    public static double BodyMeanMs(MenaceBand band, int level, double menace, double spawns, bool inDen) =>
        MeanMs(Roster.BodyMinutes(band, inDen), level, menace, spawns);

    /// <summary>The mean interval (real milliseconds) between distant sounds.</summary>
    public static double SoundMeanMs(MenaceBand band, int level, double menace, double spawns, bool inDen) =>
        MeanMs(Roster.SoundMinutes(band, inDen), level, menace, spawns);

    private static double MeanMs(double minutes, int level, double menace, double spawns)
    {
        if (double.IsInfinity(minutes)) return double.PositiveInfinity;
        double factor = Math.Clamp(MenaceFactorBase - menace, MenaceFactorMin, MenaceFactorMax);
        return minutes * 60_000 * Roster.Solitude(level) * factor / Math.Max(0.01, spawns);
    }

    /// <summary>The hard gap (real milliseconds) after a body: no body is rolled before it has passed.</summary>
    public static double BodyGapMs(MenaceBand band, int level, double menace, double spawns, bool inDen) =>
        HardGapShare * BodyMeanMs(band, level, menace, spawns, inDen);

    /// <summary>
    /// One tick's roll: the body roll first, then the sound roll. Whether a body may come at all (the one-kind rule) is the
    /// caller's to check on a Glimpse, Stalk or Hunt result.
    /// </summary>
    /// <param name="sinceBodyMs">Real milliseconds since the last body for this place (a large number if never).</param>
    /// <param name="sinceSoundMs">Real milliseconds since the last distant sound.</param>
    public static RollKind Roll(MenaceBand band, int level, double menace, double spawns, double sinceBodyMs, double sinceSoundMs, bool inDen, Random rand)
    {
        double body = BodyMeanMs(band, level, menace, spawns, inDen);
        if (sinceBodyMs >= HardGapShare * body && rand.NextDouble() < TickSeconds * 1000 / ((1 - HardGapShare) * body))
            return BodyKind(band, level, rand);
        double sound = SoundMeanMs(band, level, menace, spawns, inDen);
        if (sinceSoundMs >= HardGapShare * sound && rand.NextDouble() < TickSeconds * 1000 / ((1 - HardGapShare) * sound))
            return RollKind.Sound;
        return RollKind.Nothing;
    }

    /// <summary>Glimpse, stalk or hunt, in the proportions of <see cref="Roster.Weights(MenaceBand, int)"/> with the sound share taken out.</summary>
    public static RollKind BodyKind(MenaceBand band, int level, Random rand)
    {
        var w = Roster.Weights(band, level);
        double total = w.Glimpse + w.Stalk + w.Hunt;
        if (total <= 0) return RollKind.Nothing;
        double r = rand.NextDouble() * total;
        return r < w.Glimpse ? RollKind.Glimpse : r < w.Glimpse + w.Stalk ? RollKind.Stalk : RollKind.Hunt;
    }

    public static Encounter ToEncounter(RollKind kind) => kind switch
    {
        RollKind.Glimpse => Encounter.Glimpse,
        RollKind.Stalk => Encounter.Stalk,
        _ => Encounter.Hunt,
    };

    public static bool IsBody(RollKind kind) => kind is RollKind.Glimpse or RollKind.Stalk or RollKind.Hunt;
}

public partial class MenaceSystem
{
    /// <summary>The band's typical menace, for the rate check (heartland 0.3, approach 0.6, threshold and den 0.9).</summary>
    private static double TypicalMenace(MenaceBand band, bool inDen) => inDen ? 0.9 : band switch
    {
        MenaceBand.Heartland => 0.3,
        MenaceBand.Approach => 0.6,
        _ => 0.9,
    };

    /// <summary>Runs the rolls over simulated hours of ticks and reports the rates (/backrooms ratecheck). Null if the band is not one.</summary>
    public static string RateCheck(int level, string bandWord, double hours, double spawns, string settingCode, Random rand)
    {
        bool inDen = bandWord == "den";
        MenaceBand band = inDen ? MenaceBand.Heartland : bandWord switch
        {
            "heartland" => MenaceBand.Heartland,
            "approach" => MenaceBand.Approach,
            "threshold" => MenaceBand.Threshold,
            _ => MenaceBand.Safe,
        };
        if (band == MenaceBand.Safe) return null;
        double menace = TypicalMenace(band, inDen);
        double tick = EncounterRoll.TickSeconds * 1000, end = hours * 3_600_000;
        double sinceBody = 1e12, sinceSound = 1e12;
        int glimpse = 0, stalk = 0, hunt = 0, sounds = 0;
        double bodyGapSum = 0, soundGapSum = 0, bodyGapMin = double.MaxValue, soundGapMin = double.MaxValue;
        for (double t = 0; t < end; t += tick)
        {
            sinceBody += tick;
            sinceSound += tick;
            RollKind kind = EncounterRoll.Roll(band, level, menace, spawns, sinceBody, sinceSound, inDen, rand);
            if (kind == RollKind.Nothing) continue;
            if (kind == RollKind.Sound)
            {
                if (sinceSound < 1e11) { soundGapSum += sinceSound; soundGapMin = Math.Min(soundGapMin, sinceSound); }
                sinceSound = 0;
                sounds++;
                continue;
            }
            // (Level 0's hunters are stalkers outside the Red Rooms, as in Direct)
            if (kind == RollKind.Hunt && level == 0) kind = RollKind.Stalk;
            if (sinceBody < 1e11) { bodyGapSum += sinceBody; bodyGapMin = Math.Min(bodyGapMin, sinceBody); }
            sinceBody = 0;
            if (kind == RollKind.Glimpse) glimpse++; else if (kind == RollKind.Stalk) stalk++; else hunt++;
        }
        int bodies = glimpse + stalk + hunt;
        string Mean(double ms, int n) => n > 0 ? (ms / n / 60000).ToString("0.0") : "-";
        string Lowest(double ms) => ms < double.MaxValue ? (ms / 60000).ToString("0.0") : "-";
        var text = new StringBuilder();
        text.AppendFormat("ratecheck Level {0} {1} (menace {2:0.0}, setting {3}, {4:0.#} h): bodies {5:0.0}/h (glimpse {6:0.0}, stalk {7:0.0}, hunt {8:0.0}), sounds {9:0.0}/h; "
            + "body gap mean {10} min, min {11} min; sound gap mean {12} min, min {13} min",
            level, bandWord, menace, settingCode, hours, bodies / hours, glimpse / hours, stalk / hours, hunt / hours, sounds / hours,
            Mean(bodyGapSum, Math.Max(0, bodies - 1)), Lowest(bodyGapMin), Mean(soundGapSum, Math.Max(0, sounds - 1)), Lowest(soundGapMin));
        return text.ToString();
    }

    private TextCommandResult OnRateCheckCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string levelWord = ((string)args[0]).Trim().ToLowerInvariant();
        int level;
        string band;
        double hours = 50;
        if (levelWord == "here")
        {
            if (args.Caller.Entity == null) return TextCommandResult.Error("From the console, give a level and a band");
            Assessment a = AssessmentOf(args.Caller.Entity);
            level = a.Level;
            band = a.Den != DenKind.None ? "den" : a.Band.ToString().ToLowerInvariant();
            if (!args.Parsers[1].IsMissing && double.TryParse(((string)args[1]).Trim(), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double h)) hours = h;
        }
        else
        {
            if (!int.TryParse(levelWord, out level) || args.Parsers[1].IsMissing) return TextCommandResult.Error("Give a level (its id) and a band: /backrooms ratecheck <level> <heartland|approach|threshold|den> [hours]");
            band = ((string)args[1]).Trim().ToLowerInvariant();
            if (!args.Parsers[2].IsMissing) hours = (double)args[2];
        }
        string text = RateCheck(level, band, Math.Clamp(hours, 1, 2000), Setting.Spawns, Setting.Code, new Random());
        return text == null ? TextCommandResult.Error($"No rolls in the {band} band: use heartland, approach, threshold or den") : TextCommandResult.Success(text);
    }
}
