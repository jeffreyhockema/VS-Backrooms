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
    public const double HardGapShare = 0.25;

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

    /// <summary>The gate on every body, the set-pieces included: fewer kinds of menacing thing about than the level allows (<see cref="Roster.MaxKinds"/>: one in Classes 0 to 2, two in 3 to 5) and the hard gap since the last body passed.</summary>
    public static bool BodyMayCome(int kinds, int maxKinds, double sinceBodyMs, double gapMs) => kinds < maxKinds && sinceBodyMs >= gapMs;

    /// <summary>
    /// One tick's roll: the body roll first (through <see cref="BodyMayCome"/>), then the sound roll, which the one-kind rule does not touch.
    /// </summary>
    /// <param name="kinds">How many different kinds of menacing entity are about already.</param>
    /// <param name="isWorst">In one of the worst places (a Red Room): Level 0's hunters are stalkers anywhere else.</param>
    /// <param name="sinceBodyMs">Real milliseconds since the last body for this place (a large number if never).</param>
    /// <param name="sinceSoundMs">Real milliseconds since the last distant sound.</param>
    public static RollKind Roll(MenaceBand band, int level, double menace, double spawns, double sinceBodyMs, double sinceSoundMs, bool inDen, int kinds, bool isWorst, Random rand)
    {
        double body = BodyMeanMs(band, level, menace, spawns, inDen);
        if (BodyMayCome(kinds, Roster.MaxKinds(level), sinceBodyMs, HardGapShare * body) && rand.NextDouble() < TickSeconds * 1000 / ((1 - HardGapShare) * body))
        {
            RollKind kind = BodyKind(band, level, rand);
            // The Lobby is empty, as the lore has it: nothing hunts there but in the Red Rooms
            return kind == RollKind.Hunt && level == 0 && !isWorst ? RollKind.Stalk : kind;
        }
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

    /// <summary>
    /// Runs the rolls over simulated hours of ticks and reports the rates (/backrooms ratecheck). Null if the band is not one.
    /// <paramref name="needsMult"/> is a player's thirst-and-fatigue multiplier on the setting's spawns (<see cref="Needs.Needs.DirectorMult"/>).
    /// </summary>
    public static string RateCheck(int level, string bandWord, double hours, double spawns, string settingCode, int kinds, Random rand, double needsMult = 1, string needsNote = null)
    {
        bandWord = BandWord(bandWord);
        spawns *= needsMult;
        bool inDen = bandWord == "den";
        MenaceBand band = inDen ? MenaceBand.Threshold : bandWord switch
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
            RollKind kind = EncounterRoll.Roll(band, level, menace, spawns, sinceBody, sinceSound, inDen, kinds, false, rand);
            if (kind == RollKind.Nothing) continue;
            if (kind == RollKind.Sound)
            {
                if (sinceSound < 1e11) { soundGapSum += sinceSound; soundGapMin = Math.Min(soundGapMin, sinceSound); }
                sinceSound = 0;
                sounds++;
                continue;
            }
            if (sinceBody < 1e11) { bodyGapSum += sinceBody; bodyGapMin = Math.Min(bodyGapMin, sinceBody); }
            sinceBody = 0;
            if (kind == RollKind.Glimpse) glimpse++; else if (kind == RollKind.Stalk) stalk++; else hunt++;
        }
        int bodies = glimpse + stalk + hunt;
        string Mean(double ms, int n) => n > 0 ? (ms / n / 60000).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture) : "-";
        string Lowest(double ms) => ms < double.MaxValue ? (ms / 60000).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture) : "-";
        var text = new StringBuilder();
        text.AppendFormat(System.Globalization.CultureInfo.InvariantCulture, "ratecheck Level {0} {1} (menace {2:0.0}, setting {3}, {4:0.#} h, {14} kinds of menacing thing about (of {15} allowed)): bodies {5:0.0}/h (glimpse {6:0.0}, stalk {7:0.0}, hunt {8:0.0}), sounds {9:0.0}/h; "
            + "body gap mean {10} min, min {11} min; sound gap mean {12} min, min {13} min",
            level, bandWord, menace, settingCode, hours, bodies / hours, glimpse / hours, stalk / hours, hunt / hours, sounds / hours,
            Mean(bodyGapSum, Math.Max(0, bodies - 1)), Lowest(bodyGapMin), Mean(soundGapSum, Math.Max(0, sounds - 1)), Lowest(soundGapMin), kinds, Roster.MaxKinds(level));
        if (needsMult != 1 || needsNote != null) text.AppendFormat(System.Globalization.CultureInfo.InvariantCulture, "; needs x{0:0.00}{1}", needsMult, needsNote == null ? "" : " (" + needsNote + ")");
        return text.ToString();
    }

    /// <summary>A band word, or the start of one ("heart" for heartland); anything else is returned as it is (and is no band).</summary>
    private static string BandWord(string word)
    {
        word = (word ?? "").Trim().ToLowerInvariant();
        if (word.Length == 0) return word;
        foreach (string band in new[] { "heartland", "approach", "threshold", "den" })
            if (band.StartsWith(word, StringComparison.Ordinal)) return band;
        return word;
    }

    private TextCommandResult OnRateCheckCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string levelWord = ((string)args[0]).Trim().ToLowerInvariant();
        int level;
        string band;
        double hours = 50;
        int kinds = 0;
        double? awake = null;
        // The words after the level: the band and the hours (for "here", only the hours), and key=value words in any of them:
        // menacing=<n> (kinds of menacing thing about) and awake=<hours> (thirst-and-fatigue's multiplier for that many awake hours)
        var plain = new System.Collections.Generic.List<string>();
        for (int i = 1; i <= 4; i++)
        {
            if (args.Parsers[i].IsMissing) continue;
            string word = ((string)args[i]).Trim().ToLowerInvariant();
            if (word.Length == 0) continue;
            if (word.StartsWith("menacing=", StringComparison.Ordinal))
            {
                if (!int.TryParse(word.Substring(9), out kinds)) return TextCommandResult.Error("menacing=<n>: how many kinds of menacing thing are about");
            }
            else if (word.StartsWith("awake=", StringComparison.Ordinal))
            {
                if (!double.TryParse(word.Substring(6), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double h)) return TextCommandResult.Error("awake=<hours>: the awake hours to rate (the needs' multiplier)");
                awake = Math.Clamp(h, 0, Needs.Needs.CapHours);
            }
            else plain.Add(word);
        }
        bool Hours(string word) => double.TryParse(word, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out hours);
        double mult = 1;
        string note = null;
        if (levelWord == "here")
        {
            if (args.Caller.Entity == null) return TextCommandResult.Error("From the console, give a level and a band");
            Assessment a = AssessmentOf(args.Caller.Entity);
            level = a.Level;
            band = a.Den != DenKind.None ? "den" : a.Band.ToString().ToLowerInvariant();
            if (plain.Count > 0 && !Hours(plain[0])) hours = 50;
            if (awake == null)
            {
                mult = Needs.Needs.DirectorMult(args.Caller.Entity);
                note = "yours";
            }
        }
        else
        {
            if (!int.TryParse(levelWord, out level) || plain.Count == 0) return TextCommandResult.Error("Give a level (its id) and a band: /backrooms ratecheck <level> <heartland|approach|threshold|den> [hours] [menacing=<n>] [awake=<hours>]");
            band = BandWord(plain[0]);
            if (plain.Count > 1 && !Hours(plain[1])) return TextCommandResult.Error("The hours are a number");
        }
        if (awake is double h2)
        {
            mult = Needs.NeedsMath.DirectorMult((float)h2, true, false, false);
            note = string.Format(System.Globalization.CultureInfo.InvariantCulture, "awake {0:0.#} h", h2);
        }
        string text = RateCheck(level, band, Math.Clamp(hours, 1, 2000), Setting.Spawns, Setting.Code, Math.Max(0, kinds), new Random(), mult, note);
        return text == null ? TextCommandResult.Error($"No rolls in the {band} band: use heartland, approach, threshold or den") : TextCommandResult.Success(text);
    }
}
