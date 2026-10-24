using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;

namespace Backrooms.Entities;

/// <summary>Why <see cref="MenaceSystem.TrySpawn"/> refused the spots it looked at (counts of looks, up to 18 a try).</summary>
public struct SpawnTry
{
    /// <summary>No floor or room at the spot.</summary>
    public int NoFloor;
    /// <summary>The sight test refused: a stalker or hunter where someone could see it, or a glimpse where no one could.</summary>
    public int InSight;
    /// <summary>Where the target had just been looking (set pieces only).</summary>
    public int JustSeen;
    /// <summary>1 when a capped scavenger pack refused before any spot was looked at.</summary>
    public int RatCap;
}

/// <summary>
/// The felt rate: the rate check counts rolls, but a roll with no fitting spot is silence. A dry run of the director's
/// placement (<c>/backrooms feltrate</c>) says how many of the rolls turn into a body, and the director counts the ones
/// that did not.
/// </summary>
public partial class MenaceSystem
{
    /// <summary>Whether a creative-mode player is directed (and hunted) like anyone else (/backrooms creativehunts). Off by default.</summary>
    public static bool CreativeHunted;

    /// <summary>What the latest <see cref="TrySpawn"/> found, to read right after it returned.</summary>
    internal SpawnTry LastTry;

    private sealed class FailedBodies
    {
        public int Count, NoFloor, InSight, RatCap;
    }

    /// <summary>Per level (this session): ordinary body rolls that found no spot, and why.</summary>
    private readonly Dictionary<int, FailedBodies> failedBodies = new();

    private void NoteFailedBody(int level, string code, SpawnTry t, double min, double max)
    {
        if (!failedBodies.TryGetValue(level, out FailedBodies f)) failedBodies[level] = f = new FailedBodies();
        f.Count++;
        f.NoFloor += t.NoFloor;
        f.InSight += t.InSight;
        f.RatCap += t.RatCap;
        if (Logging)
            sapi.Logger.Notification("[backrooms] {0}: no spot after {6} looks ({1} no floor/room, {2} in sight{3}); band {4:0}-{5:0} blocks", code, t.NoFloor, t.InSight, t.RatCap > 0 ? ", rat packs at their cap" : "", min, max, t.NoFloor + t.InSight);
    }

    private string FailedBodiesLine(int level)
    {
        if (!failedBodies.TryGetValue(level, out FailedBodies f)) return "Bodies rolled with no spot to put them (this session): none.";
        return string.Format(CultureInfo.InvariantCulture, "Bodies rolled with no spot to put them (this session): {0} ({1} looks with no floor, {2} in sight, {3} refused for a rat pack at its cap).", f.Count, f.NoFloor, f.InSight, f.RatCap);
    }

    private static readonly Regex RatesPattern = new(@"glimpse ([\d.]+), stalk ([\d.]+), hunt ([\d.]+)\)", RegexOptions.Compiled);

    private TextCommandResult OnFeltRateCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        Entity entity = args.Caller.Entity ?? LatestDummy(args);
        if (entity == null) return TextCommandResult.Error("Needs a player, or a straw dummy put down first");
        if (!watches.TryGetValue(entity.EntityId, out Watch watch)) watches[entity.EntityId] = watch = new Watch();
        Assess(entity, watch);
        Assessment a = watch.Now;

        string levelWord = ((string)args[0]).Trim().ToLowerInvariant();
        if (levelWord != "here" && (!int.TryParse(levelWord, out int asked) || asked != a.Level))
            return TextCommandResult.Error($"{entity.Code.Path} #{entity.EntityId} stands in level id {a.Level}: give that, or here");
        string bandWord = args.Parsers[1].IsMissing ? a.Band.ToString().ToLowerInvariant() : ((string)args[1]).Trim().ToLowerInvariant();
        MenaceBand band = bandWord switch { "heartland" => MenaceBand.Heartland, "approach" => MenaceBand.Approach, "threshold" => MenaceBand.Threshold, _ => MenaceBand.Safe };
        if (band == MenaceBand.Safe) return TextCommandResult.Error("The band is heartland, approach or threshold (nothing is put down in Safe places)");
        int tries = args.Parsers[2].IsMissing ? 60 : Math.Clamp((int)args[2], 1, 500);

        RosterEntry[] roster = a.Snackrooms ? Roster.Snackrooms : a.Castle ? Roster.Castle : Roster.For(a.Level);
        var rates = new Dictionary<Encounter, double>();
        string rateText = RateCheck(a.Level, bandWord, 400, Setting.Spawns, Setting.Code, 0, new Random(12345));
        Match m = rateText == null ? null : RatesPattern.Match(rateText);
        if (m != null && m.Success)
        {
            rates[Encounter.Glimpse] = double.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
            rates[Encounter.Stalk] = double.Parse(m.Groups[2].Value, CultureInfo.InvariantCulture);
            rates[Encounter.Hunt] = double.Parse(m.Groups[3].Value, CultureInfo.InvariantCulture);
        }

        Assessment at = a; // (the spot is the target's own; the band asked about only picks the roster and the rates)
        var text = new StringBuilder();
        text.AppendFormat(CultureInfo.InvariantCulture, "feltrate Level {0} {1} ({2} #{3}, {4} tries, setting {5}):", a.Level, bandWord, entity.Code.Path, entity.EntityId, tries, Setting.Code);
        double felt = 0, stalkHunt = 1;
        int noFloor = 0, inSight = 0;
        foreach (Encounter kind in new[] { Encounter.Glimpse, Encounter.Stalk, Encounter.Hunt })
        {
            Encounters flag = kind switch { Encounter.Glimpse => Encounters.Glimpse, Encounter.Stalk => Encounters.Stalk, _ => Encounters.Hunt };
            RosterEntry[] options = roster.Where(e => (e.Kinds & flag) != 0 && e.MinBand <= band && (!e.SubwayOnly || a.Subway) && (!e.ShiftOnly || a.Shift)
                && (!e.LightsOutOnly || a.Worst || a.Shift) && types.ContainsKey(e.Code)).ToArray();
            int ok = 0;
            if (options.Length > 0)
                for (int i = 0; i < tries; i++)
                {
                    RosterEntry entry = Pick(options);
                    if (entry == null) continue;
                    if (TrySpawn(entity, at, entry, kind, dryRun: true)) ok++;
                    noFloor += LastTry.NoFloor;
                    inSight += LastTry.InSight;
                }
            double success = options.Length == 0 ? 0 : (double)ok / tries;
            double rate = rates.TryGetValue(kind, out double r) ? r : 0;
            felt += success * rate;
            if (kind != Encounter.Glimpse && options.Length > 0) stalkHunt = Math.Min(stalkHunt, success);
            text.AppendFormat(CultureInfo.InvariantCulture, "\n  {0}: {1} kinds on the roster, placed {2:0}% ({3:0.0} rolls/h, {4:0.0} felt/h)", kind, options.Length, success * 100, rate, success * rate);
        }
        text.AppendFormat(CultureInfo.InvariantCulture, "\nstalk-or-hunt {0:0}%", stalkHunt * 100);
        text.AppendFormat(CultureInfo.InvariantCulture, "; looks refused: {0} no floor/room, {1} in sight", noFloor, inSight);
        text.AppendFormat(CultureInfo.InvariantCulture, "; felt bodies {0:0.0}/h{1}", felt, rates.Count == 0 ? " (no rolls in this band or setting)" : "");
        return TextCommandResult.Success(text.ToString());
    }
}
