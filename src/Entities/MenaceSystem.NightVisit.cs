using System.Linq;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;

namespace Backrooms.Entities;

/// <summary>
/// Night visits (docs/design/needs/README.md, section 4): someone asleep outside a safe place may be found. The fatigue
/// behaviour rolls the odds per slept hour (<see cref="Needs.NeedsSystem.RollNightVisit"/>); a visit is a hunter from the
/// level's roster put down 12 to 18 blocks off where no one can see it, hunting the sleeper, who wakes as it closes in.
/// It is a body like any other: it waits on the kinds rule and the hard gap, and counts as the place's last body.
/// </summary>
public partial class MenaceSystem
{
    /// <summary>How far off (blocks) a night visitor is put down, at least and at most.</summary>
    public const double VisitMinDistance = 12, VisitMaxDistance = 18;

    /// <summary>Puts a hunter down for a sleeping player. Returns whether one came.</summary>
    public bool NightVisit(IServerPlayer player)
    {
        Entity target = player?.Entity;
        if (target == null || layout == null || Paused || !Setting.Entities) return false;
        if (!watches.TryGetValue(target.EntityId, out Watch watch)) watches[target.EntityId] = watch = new Watch();
        Assess(target, watch);
        Assessment a = watch.Now;
        if (a.Band == MenaceBand.Safe || a.Trial) return false;
        if (!BodyAllowed(target, watch, a))
        {
            if (Logging) sapi.Logger.Notification("[backrooms] night visit for {0}: not now (something is about, or the hard gap)", player.PlayerName);
            return false;
        }
        RosterEntry[] roster = a.Snackrooms ? Roster.Snackrooms : a.Castle ? Roster.Castle : Roster.For(a.Level);
        RosterEntry[] options = roster.Where(e => (e.Kinds & Encounters.Hunt) != 0 && e.MinBand <= a.Band && (!e.SubwayOnly || a.Subway) && (!e.ShiftOnly || a.Shift)
            && (!e.LightsOutOnly || a.Worst || a.Shift) && !e.Aquatic && types.ContainsKey(e.Code)).ToArray();
        if (Wretched(target)) options = options.Select(e => e.Code == Roster.Wretch ? e with { Weight = e.Weight * 3 } : e).ToArray();
        RosterEntry entry = Pick(options);
        if (entry == null) return false;
        bool came = TrySpawn(target, a, entry, Encounter.Hunt, minDistance: VisitMinDistance, maxDistance: VisitMaxDistance);
        if (came) watch.LastBodyMs = sapi.World.ElapsedMilliseconds;
        if (Logging) sapi.Logger.Notification("[backrooms] night visit for {0}: {1} {2}", player.PlayerName, entry.Code, came ? "comes" : "found no spot");
        return came;
    }
}
