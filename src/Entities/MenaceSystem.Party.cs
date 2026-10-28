using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;

namespace Backrooms.Entities;

/// <summary>
/// Parties: players who are about each other share one budget of arrivals (the director rolls once for the party), so two people
/// together are not visited twice as often as one. People further apart than <see cref="PartyRadius"/> are separate parties
/// with budgets of their own. A party of N is rolled at <see cref="PartyFactor"/>(N) times one person's rate.
/// </summary>
public partial class MenaceSystem
{
    /// <summary>
    /// How near (blocks, flat) and how level (blocks up or down) two people must be, in the same level, to share one budget. A bit
    /// under the 64 blocks the caps count entities within, so that the entities put down for one are the other's concern too.
    /// </summary>
    public const double PartyRadius = 48, PartyHeight = 24;

    /// <summary>
    /// What each person beyond the first adds to the party's rate, as a share of one person's rate. A party of two is rolled at
    /// 1.25 times a lone player's rate, three at 1.5: more people are more noise and more targets (and the director spreads the
    /// arrivals over them), but not N times the danger. 0 would make a pair exactly as safe as one, 1 is the old N times.
    /// </summary>
    public const double PartyBonus = 0.25;

    /// <summary>The factor on the rates of a party of <paramref name="members"/> (1 for one person).</summary>
    public static double PartyFactor(int members) => 1 + PartyBonus * Math.Max(0, members - 1);

    private static bool Within(double dx, double dz) => dx * dx + dz * dz <= PartyRadius * PartyRadius;

    /// <summary>Groups 0..count-1 greedily: each joins the first group that has a member it is <paramref name="near"/>, else starts one.</summary>
    internal static List<List<int>> PartyGroups(int count, System.Func<int, int, bool> near)
    {
        var groups = new List<List<int>>();
        for (int i = 0; i < count; i++)
        {
            List<int> home = null;
            foreach (List<int> group in groups)
            {
                foreach (int j in group)
                    if (near(i, j)) { home = group; break; }
                if (home != null) break;
            }
            if (home == null) groups.Add(home = new List<int>());
            home.Add(i);
        }
        return groups;
    }

    /// <summary>
    /// For the once-a-second set pieces rolled for each person on their own (the Beast of Level 5, the Mangled of Level 9): the share
    /// of their chance a person keeps so that the party between them rolls at <see cref="PartyFactor"/> of one person's chance, not N times it.
    /// Counts the living, surviving players (and directed dummies) of the same level within <see cref="PartyRadius"/>, the person included; 1 when alone.
    /// </summary>
    internal double PartyShare(Entity who)
    {
        if (layout == null) return 1;
        int level = AssessmentOf(who).Level, n = 1;
        foreach (Vintagestory.API.Common.IPlayer online in sapi.World.AllOnlinePlayers)
        {
            Vintagestory.API.Common.EntityPlayer other = online.Entity;
            if (other == null || other == who || !other.Alive || other.Pos.Dimension != who.Pos.Dimension) continue;
            if (online.WorldData.CurrentGameMode is Vintagestory.API.Common.EnumGameMode.Spectator or Vintagestory.API.Common.EnumGameMode.Creative) continue;
            if (Math.Abs(other.Pos.Y - who.Pos.Y) > PartyHeight || !Within(other.Pos.X - who.Pos.X, other.Pos.Z - who.Pos.Z)) continue;
            if (AssessmentOf(other) is { } o && o.Level == level && o.Band != MenaceBand.Safe) n++;
        }
        return PartyFactor(n) / n;
    }

    /// <summary>The party rule as it was before parties: places of 24 blocks rolled once each, at one person's rate.</summary>
    private const double OldPlaceRadius = 24;

    private TextCommandResult OnPartyCheckCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        int level = int.TryParse(((string)args[0]).Trim(), out int l) ? l : -1;
        string bandWord = BandWord((string)args[1]);
        int players = Math.Clamp((int)args[2], 1, 16), spacing = Math.Max(0, (int)args[3]);
        double hours = 50;
        if (!args.Parsers[4].IsMissing) double.TryParse((string)args[4], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out hours);
        hours = Math.Clamp(hours, 1, 2000);
        bool old = !args.Parsers[5].IsMissing && ((string)args[5]).Trim().ToLowerInvariant() == "old";
        bool inDen = bandWord == "den";
        MenaceBand band = inDen ? MenaceBand.Threshold : bandWord switch { "heartland" => MenaceBand.Heartland, "approach" => MenaceBand.Approach, "threshold" => MenaceBand.Threshold, _ => MenaceBand.Safe };
        if (band == MenaceBand.Safe || level < 0) return TextCommandResult.Error("Give a level id and a band (heartland, approach, threshold or den)");
        double radius = old ? OldPlaceRadius : PartyRadius;
        List<List<int>> groups = PartyGroups(players, (i, j) => Math.Abs(i - j) * (double)spacing <= radius);
        double menace = TypicalMenace(band, inDen), tick = EncounterRoll.TickSeconds * 1000, end = hours * 3_600_000;
        var rng = new Random(4242);
        int bodies = 0, sounds = 0;
        foreach (List<int> group in groups)
        {
            double spawns = Setting.Spawns * (old ? 1 : PartyFactor(group.Count)), sinceBody = 1e12, sinceSound = 1e12;
            for (double t = 0; t < end; t += tick)
            {
                sinceBody += tick;
                sinceSound += tick;
                RollKind kind = EncounterRoll.Roll(band, level, menace, spawns, sinceBody, sinceSound, inDen, 0, false, rng);
                if (kind == RollKind.Nothing) continue;
                if (kind == RollKind.Sound) { sinceSound = 0; sounds++; continue; }
                sinceBody = 0;
                bodies++;
            }
        }
        return TextCommandResult.Success(string.Format(System.Globalization.CultureInfo.InvariantCulture,
            "partycheck Level {0} {1} ({2}, {3} players {4} blocks apart in {5} parties, {6:0} h, setting {7}): bodies {8:0.00}/h in all, {9:0.00}/h for each player; sounds {10:0.00}/h in all, {11:0.00}/h for each player",
            level, bandWord, old ? "old" : "new", players, spacing, groups.Count, hours, Setting.Code, bodies / hours, bodies / hours / players, sounds / hours, sounds / hours / players));
    }
}
