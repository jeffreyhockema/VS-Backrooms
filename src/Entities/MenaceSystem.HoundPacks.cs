using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;

namespace Backrooms.Entities;

/// <summary>
/// One Hound pack at a time in Levels 8 and 9 (feedback round 2026-11: "every 30 seconds another wolf enemy spawns on top
/// of me"). Per player (a party counts as one: <see cref="DirectByPlace"/>), no new Hound is sent while a pack sent for them
/// is still about and hunting, and after the pack leaves or dies a quiet spell follows before the next:
/// <c>quiet = U(3, 5) real minutes x sqrt(5.5 / spawns) / PartyFactor(party)</c>, so 3 to 5 minutes on Normal (5.5),
/// 3.8 to 6.3 on Low, 2 to 3.3 on Very high, and a party of two (factor 1.25) 2.4 to 4. While a pack hunts, a second one
/// may come only in the worst places (Level 8's far dark off the 9th Road, Level 9's threshold band and its dens), and only
/// <see cref="SecondPackChance"/> of the times a Hound comes up there. A Hound that comes up and is held back is a body that
/// did not come (no clock is stamped), so the other creatures keep their own rates: the rolls do not go to them instead.
/// </summary>
public partial class MenaceSystem
{
    /// <summary>The levels the one-pack rule holds in.</summary>
    public static bool OnePackLevel(int level) => level is 8 or 9;

    /// <summary>The quiet after a pack, in real minutes on Normal for one person: at least and at most.</summary>
    public const double HoundQuietMinMinutes = 3, HoundQuietMaxMinutes = 5;

    /// <summary>In the worst places, the chance that a Hound coming up while a pack hunts is sent all the same (a second pack; never a third).</summary>
    public const double SecondPackChance = 0.05;

    /// <summary>The spawns the quiet is worked out for (the Normal setting's): busier settings shorten it by the square root.</summary>
    private const double HoundQuietSpawns = 5.5;

    private sealed class HoundClock
    {
        /// <summary>The packs sent for this one that are still about: each the entity ids of its members.</summary>
        public readonly List<long[]> Packs = new();
        /// <summary>World milliseconds before which no Hound is sent for this one (the quiet after a pack).</summary>
        public long QuietUntilMs;
        /// <summary>How many were in this one's party when its last pack went (for the quiet's length).</summary>
        public int Party = 1;
    }

    private readonly Dictionary<long, HoundClock> houndClocks = new();

    /// <summary>The quiet after a pack (real milliseconds) on a setting's spawns, for a party of this size, at a random point <paramref name="u"/> in [0, 1).</summary>
    public static double HoundQuietMs(double spawns, int party, double u) =>
        (HoundQuietMinMinutes + (HoundQuietMaxMinutes - HoundQuietMinMinutes) * u) * 60_000
        * Math.Sqrt(HoundQuietSpawns / Math.Max(0.01, spawns)) / PartyFactor(Math.Max(1, party));

    /// <summary>Whether a place is one of the worst, where a second pack may come while one hunts (Level 8's far dark, Level 9's threshold and dens).</summary>
    public static bool SecondPackPlace(Assessment a) =>
        a.Level == 8 && a.Worst || a.Level == 9 && (a.Band == MenaceBand.Threshold || a.Den != DenKind.None);

    /// <summary>Whether a member of a pack is still about and after its target (not gone, dead, or leaving).</summary>
    private bool Hunting(long id)
    {
        Entity e = sapi.World.GetEntityById(id);
        return e is { Alive: true } && EntityBehaviorMenace.KindOf(e) is Encounter.Glimpse or Encounter.Stalk or Encounter.Hunt or Encounter.Investigate or Encounter.Search;
    }

    /// <summary>Brings a clock up to date: the packs that have left or died are dropped, and the last of them going starts the quiet.</summary>
    private HoundClock HoundClockOf(Entity who, long now)
    {
        if (!houndClocks.TryGetValue(who.EntityId, out HoundClock clock)) return null;
        if (clock.Packs.Count == 0) return clock;
        clock.Packs.RemoveAll(pack => !pack.Any(Hunting));
        if (clock.Packs.Count == 0)
        {
            clock.QuietUntilMs = now + (long)HoundQuietMs(Setting.Spawns, clock.Party, rand.NextDouble());
            if (Logging) sapi.Logger.Notification("[backrooms] hounds: the pack for {0} has gone; quiet for {1:0.0} min", NameOf(who), (clock.QuietUntilMs - now) / 60000.0);
        }
        return clock;
    }

    /// <summary>Brings someone's clock up to date if a pack is out for them (each director tick, so the quiet starts when the pack went).</summary>
    private void TickHoundClock(Entity who)
    {
        if (houndClocks.TryGetValue(who.EntityId, out HoundClock clock) && clock.Packs.Count > 0) HoundClockOf(who, sapi.World.ElapsedMilliseconds);
    }

    /// <summary>
    /// Whether a Hound that came up for <paramref name="actor"/> is held back by the one-pack rule (Levels 8 and 9): a pack
    /// sent for them, or anyone in their party, is still hunting (bar the worst places' rare second pack), or the quiet after
    /// one has not passed.
    /// </summary>
    private bool HoundHeldBack(Entity actor, Assessment a, List<(Entity Entity, Watch Watch)> mates)
    {
        if (!OnePackLevel(a.Level)) return false;
        long now = sapi.World.ElapsedMilliseconds;
        int packs = 0;
        foreach (Entity who in mates is { Count: > 0 } ? mates.Select(m => m.Entity).Append(actor).Distinct() : new[] { actor })
        {
            if (HoundClockOf(who, now) is not { } clock) continue;
            if (clock.Packs.Count == 0 && now < clock.QuietUntilMs)
            {
                if (Logging) sapi.Logger.Notification("[backrooms] hounds: held back for {0} (quiet for {1:0.0} min more)", NameOf(actor), (clock.QuietUntilMs - now) / 60000.0);
                return true;
            }
            packs += clock.Packs.Count;
        }
        if (packs == 0) return false;
        bool second = packs == 1 && SecondPackPlace(a) && rand.NextDouble() < SecondPackChance;
        if (Logging) sapi.Logger.Notification("[backrooms] hounds: {0} for {1} ({2} pack(s) still hunting)", second ? "a second pack comes" : "held back", NameOf(actor), packs);
        return !second;
    }

    /// <summary>Notes a Hound pack just put down (<see cref="lastPack"/>) for someone in Levels 8 and 9, if it came to follow or hunt.</summary>
    private void NoteHoundPack(Entity actor, Assessment a, Encounter kind, int party)
    {
        if (!OnePackLevel(a.Level) || kind is not (Encounter.Stalk or Encounter.Hunt) || lastPack.Count == 0) return;
        if (!houndClocks.TryGetValue(actor.EntityId, out HoundClock clock)) houndClocks[actor.EntityId] = clock = new HoundClock();
        clock.Packs.Add(lastPack.Select(e => e.EntityId).ToArray());
        clock.Party = Math.Max(1, party);
        if (Logging) sapi.Logger.Notification("[backrooms] hounds: a pack of {0} for {1} ({2} hunting)", lastPack.Count, NameOf(actor), clock.Packs.Count);
    }

    /// <summary>The one-pack rule's state for someone in Levels 8 and 9, for /backrooms menace; null elsewhere.</summary>
    private string HoundStatusLine(Entity who, int level)
    {
        if (!OnePackLevel(level)) return null;
        long now = sapi.World.ElapsedMilliseconds;
        HoundClock clock = HoundClockOf(who, now);
        if (clock == null || clock.Packs.Count == 0 && now >= clock.QuietUntilMs) return "Hounds: none after you; the next pack may come";
        return clock.Packs.Count > 0 ? $"Hounds: {clock.Packs.Count} pack(s) after you; no other comes (bar a rare second in the worst places)"
            : string.Format(System.Globalization.CultureInfo.InvariantCulture, "Hounds: quiet for {0:0.0} min more", (clock.QuietUntilMs - now) / 60000.0);
    }

    /// <summary>A player's name, or a dummy's code and id.</summary>
    private static string NameOf(Entity who) => (who as EntityPlayer)?.Player?.PlayerName ?? who.Code + " #" + who.EntityId;

    /// <summary>Forgets the Hound clocks of those no longer about.</summary>
    private void PruneHoundClocks(HashSet<long> live)
    {
        foreach (long id in houndClocks.Keys.Where(id => !live.Contains(id)).ToList()) houndClocks.Remove(id);
    }
}
