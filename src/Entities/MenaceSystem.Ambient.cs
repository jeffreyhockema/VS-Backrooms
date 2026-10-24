using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common.Entities;

namespace Backrooms.Entities;

/// <summary>
/// The harmless wanderers the director puts down (Facelings, scavenger rats, moths, fed Skin-Stealers), kept rare for
/// the isolation round: one at a time, a long wait between two for the same person, and no refilling of a big room.
/// </summary>
public partial class MenaceSystem
{
    /// <summary>Real minutes between two ambient creatures put down for one person (Levels 1, 4 and 5 are lived in: <see cref="AmbientMinutesLived"/>), and how far the wait is jittered either way.</summary>
    private const double AmbientMinutes = 15, AmbientMinutesLived = 8, AmbientMinutesCrowd = 3, AmbientMinutesDay94 = 5, AmbientJitterLow = 0.7, AmbientJitterHigh = 1.3;

    /// <summary>Ambient creatures within <see cref="AmbientRadius"/> blocks of a person: ordinarily, and in Level 11 and the Snackrooms.</summary>
    private const int AmbientCap = 1, AmbientCapCrowd = 3, AmbientRadius = 48;

    /// <summary>Facelings: ordinarily one within 100 blocks; Level 11 three and the Snackrooms two within 48.</summary>
    private const int FacelingMax = 1, FacelingRadius = 100, FacelingMaxCity = 3, FacelingMaxSnackrooms = 2, FacelingRadiusCrowd = 48;

    /// <summary>At most this many scavenger rat packs about one person (also what the heartland's menacing roll obeys).</summary>
    private const int MaxRatPacks = 1;

    /// <summary>Per player (by entity id): the real time (ElapsedMilliseconds) before which no ambient creature is put down.</summary>
    private readonly Dictionary<long, long> ambientNextMs = new();

    /// <summary>How long (ms) an ambient roll is put off when the cap of wanderers about was full.</summary>
    private const long CapBlockedRecheckMs = 10_000;

    private static readonly Vintagestory.API.Common.ActionConsumable<Entity> AmbientAlive = e => e.Alive && EntityBehaviorMenace.KindOf(e) == Encounter.Ambient;

    /// <summary>The ambient-capable entries of a roster, worked out once per roster array (the rosters are static).</summary>
    private static readonly System.Runtime.CompilerServices.ConditionalWeakTable<RosterEntry[], RosterEntry[]> ambientCapable = new();

    private static RosterEntry[] AmbientCapable(RosterEntry[] roster)
    {
        lock (ambientCapable)
        {
            if (!ambientCapable.TryGetValue(roster, out RosterEntry[] capable))
                ambientCapable.Add(roster, capable = roster.Where(e => (e.Kinds & Encounters.Ambient) != 0).ToArray());
            return capable;
        }
    }

    private void SpawnAmbient(Entity target, Assessment a, RosterEntry[] roster)
    {
        long now = sapi.World.ElapsedMilliseconds;
        if (ambientNextMs.TryGetValue(target.EntityId, out long next) && now < next) return;
        RosterEntry[] capable = AmbientCapable(roster);
        if (capable.Length == 0) return;
        bool crowd = a.Level == 11 || a.Snackrooms;
        // (Everything wandering counts, scavenger rats and fed Skin-Stealers too; the rats' packs have a cap of their own besides.)
        // Counted first, before anything is built: a full cap is the usual state beside a Faceling, and this runs every tick.
        int count = sapi.World.GetEntitiesAround(target.Pos.XYZ, AmbientRadius, 16, AmbientAlive).Length;
        if (count >= (crowd ? AmbientCapCrowd : AmbientCap))
        {
            ambientNextMs[target.EntityId] = now + CapBlockedRecheckMs; // (not looked at again every tick)
            return;
        }
        var options = new List<RosterEntry>(capable.Length);
        foreach (RosterEntry e in capable)
            if (types.ContainsKey(e.Code) && (a.Band != MenaceBand.Safe || a.NearWanderer || e.MinBand == MenaceBand.Safe) && (!e.SubwayOnly || a.Subway)) options.Add(e);
        if (options.Count == 0) return;
        RosterEntry entry = Pick(options.ToArray());
        if (entry == null || rand.NextDouble() > entry.Rarity) return;
        if (entry.Code == Roster.DeathRat && RatPacksNear(target) >= MaxRatPacks) return;
        if (entry.Code is Roster.Faceling or Roster.FacelingChild)
        {
            int max = a.Level == 11 ? FacelingMaxCity : a.Snackrooms ? FacelingMaxSnackrooms : FacelingMax;
            float radius = crowd ? FacelingRadiusCrowd : FacelingRadius;
            int facelings = sapi.World.GetEntitiesAround(target.Pos.XYZ, radius, 16, e => e.Alive && e.Code.Path.StartsWith("faceling", StringComparison.Ordinal)).Length;
            if (facelings >= max) return;
        }
        if (!TrySpawn(target, a, entry, Encounter.Ambient)) return;
        double minutes = a.Level == WorldLayout.Motion && !a.Castle && !Regions.MotionSystem.IsNight(sapi.World.Calendar) ? AmbientMinutesDay94
            : crowd ? AmbientMinutesCrowd : a.Level is 1 or 4 or 5 ? AmbientMinutesLived : AmbientMinutes;
        long wait = (long)(minutes * 60_000 * (AmbientJitterLow + (AmbientJitterHigh - AmbientJitterLow) * rand.NextDouble()));
        ambientNextMs[target.EntityId] = now + wait;
        if (Logging) sapi.Logger.Notification("[backrooms] ambient {0} put down by the wanderers' roll; the next in {1:0} s", entry.Code, wait / 1000.0);
    }

    /// <summary>How many packs of scavenger (Ambient) rats are within 48 blocks: rats within ten blocks of each other are one pack.</summary>
    private int RatPacksNear(Entity target)
    {
        Entity[] rats = sapi.World.GetEntitiesAround(target.Pos.XYZ, AmbientRadius, 16, e => e.Alive && e.Code.Path == "deathrat" && EntityBehaviorMenace.KindOf(e) == Encounter.Ambient);
        var leaders = new List<Entity>();
        foreach (Entity rat in rats)
            if (!leaders.Any(l => l.Pos.DistanceTo(rat.Pos) <= 10)) leaders.Add(rat);
        return leaders.Count;
    }
}
