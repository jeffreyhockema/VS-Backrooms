using System;
using System.Linq;
using Vintagestory.API.Common.Entities;

namespace Backrooms.Entities;

/// <summary>The director's part of the zero blackout (docs/design/progression/plan.md 3.4): the hunter that comes at once.</summary>
public partial class MenaceSystem
{
    /// <summary>
    /// Most to least dangerous to someone unarmoured in a chase. The level's "worst hunter" is the first of these its roster can
    /// hunt with (the piece B lethality table may reorder this once it exists).
    /// </summary>
    private static readonly string[] WorstFirst =
    {
        Roster.GiantSpider, Roster.Hound, Roster.Duller, Roster.DeathmothFemale, Roster.SkinStealer, Roster.Wretch,
        Roster.Smiler, Roster.Faceling, Roster.DeathRat, Roster.Partygoer,
    };

    /// <summary>The tries to find the hunter a place, and the wait between them.</summary>
    private const int ZeroHunterTries = 5, ZeroHunterRetryMs = 3000;

    /// <summary>
    /// Sends the worst hunter of the target's level at once, as a set piece (put down well away and unseen, capped as a pack is).
    /// Nothing comes in the Safe band, with the entities off, or from a level whose roster has nothing that hunts. Returns whether
    /// a hunter was chosen (it may take a few tries to find it a place: they are made every few seconds).
    /// </summary>
    public bool SendWorstHunter(Entity target)
    {
        if (layout == null || target == null || !Setting.Entities) return false;
        Assessment a = AssessmentOf(target);
        if (a.Band == MenaceBand.Safe || a.Trial) return false;
        RosterEntry[] roster = a.Snackrooms ? Roster.Snackrooms : a.Castle ? Roster.Castle : Roster.For(a.Level);
        RosterEntry entry = roster
            .Where(e => (e.Kinds & Encounters.Hunt) != 0 && !e.Ambush && !e.Aquatic && types.ContainsKey(e.Code)
                && (!e.ShiftOnly || a.Shift) && (!e.SubwayOnly || a.Subway) && (!e.LightsOutOnly || a.Worst || a.Shift) && (!e.NeedsDark || a.Dark))
            .OrderBy(e => { int i = Array.IndexOf(WorstFirst, e.Code); return i < 0 ? int.MaxValue : i; })
            .FirstOrDefault();
        if (entry == null) return false; // (a roster with nothing that hunts, or the dark ones in the light: asked again each second until the bar rises)
        sapi.Logger.Notification("[backrooms] zero: sending {0} for {1} (Level {2})", entry.Code, (target as Vintagestory.API.Common.EntityPlayer)?.Player?.PlayerName ?? target.Code.ToString(), Worldgen.WorldLayout.DisplayNumber(a.Level));
        ZeroHunterTry(target, entry, 0);
        return true;
    }

    private void ZeroHunterTry(Entity target, RosterEntry entry, int failed)
    {
        if (!target.Alive) return;
        Assessment a = AssessmentOf(target);
        if (TrySpawn(target, a, entry, Encounter.Hunt, setPiece: true, failedTries: failed))
        {
            if (watches.TryGetValue(target.EntityId, out Watch watch)) watch.LastBodyMs = sapi.World.ElapsedMilliseconds;
            return;
        }
        if (failed + 1 >= ZeroHunterTries) return;
        sapi.World.RegisterCallback(_ => ZeroHunterTry(target, entry, failed + 1), ZeroHunterRetryMs);
    }
}
