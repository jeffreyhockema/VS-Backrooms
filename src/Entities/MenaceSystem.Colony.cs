using System;
using System.Collections.Generic;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>
/// The Giant Spiders' colonies: "loud sounds reverberate throughout the caverns, attracting large numbers of spiders to
/// the source" (the old Fandom page). A noise of 0.5 or more within 24 blocks of a nest's heart wakes every spider of
/// that nest and sends it after whoever made it, and the nest's dark puts down one or two more if fewer than three are
/// about. Done at runtime from the noise bus: no worldgen, no layout version.
/// </summary>
public partial class MenaceSystem
{
    /// <summary>How loud a noise must be to rouse a nest, and how near its heart (blocks) it must be made.</summary>
    public const double NestWakeLoudness = 0.5, NestWakeRange = 24;

    /// <summary>A nest is kept to this many spiders about its heart by the noise that rouses it.</summary>
    public const int NestSpiders = 3;

    /// <summary>How long (ms) a nest takes to put down more spiders after it last did.</summary>
    public const long NestReinforceEveryMs = 45_000;

    /// <summary>How far from a nest's heart (blocks) a spider counts as its own.</summary>
    private const double NestGround = 30;

    private readonly Dictionary<long, long> nestReinforcedMs = new();

    /// <summary>A noise has been made: a loud one near a spider nest rouses it.</summary>
    private void NestHeard(Vec3d at, double loudness, Entity who)
    {
        if (loudness < NestWakeLoudness || layout == null || who == null || !who.Alive) return;
        // (Spiders come for whoever made it: a player, or a straw dummy in a test; not for a fight between other things)
        if (who is not EntityPlayer && !Senses.IsTestTarget(who) || Strike.IsCreative(who)) return;
        if (layout.NestHeartNear((int)Math.Floor(at.X), (int)Math.Floor(at.Z), NestWakeRange) is not { } heart) return;
        var centre = new Vec3d(heart.X + 0.5, at.Y, heart.Z + 0.5);
        Entity[] spiders = sapi.World.GetEntitiesAround(centre, (float)NestGround, 32, e => e.Alive && e.Code?.Domain == "backrooms" && e.Code.Path == "giantspider");
        int woken = 0;
        foreach (Entity spider in spiders)
            if (spider.GetBehavior<Vintagestory.GameContent.EntityBehaviorTaskAI>()?.TaskManager?.GetTask<AiTaskSpider>() is { } task && task.WakeFor(who)) woken++;
        int added = Setting.Entities ? Reinforce(heart, who, spiders.Length) : 0;
        if (Logging)
            sapi.Logger.Notification("[backrooms] a noise of {0:0.00} near the nest at {1},{2}: {3} spiders woken, {4} more put down", loudness, heart.X, heart.Z, woken, added);
    }

    /// <summary>Puts down one or two spiders in the dark about a nest's heart if fewer than <see cref="NestSpiders"/> are about it. Returns how many.</summary>
    private int Reinforce((int X, int Z) heart, Entity who, int about) => Reinforce(heart.X, heart.Z, who, about);

    private int Reinforce(int hx, int hz, Entity who, int about)
    {
        long now = sapi.World.ElapsedMilliseconds, key = DenKey(hx, hz);
        if (about >= NestSpiders || !types.TryGetValue(Roster.GiantSpider, out EntityProperties type)) return 0;
        if (nestReinforcedMs.TryGetValue(key, out long last) && now >= last && now - last < NestReinforceEveryMs) return 0;
        Assessment a = AssessmentOf(who);
        if (a.Band == MenaceBand.Safe) return 0;
        int want = Math.Min(NestSpiders - about, 1 + rand.Next(2)), added = 0;
        for (int attempt = 0; attempt < 24 && added < want; attempt++)
        {
            double angle = rand.NextDouble() * Math.PI * 2, d = 4 + rand.NextDouble() * 12;
            int x = (int)Math.Floor(hx + 0.5 + Math.Cos(angle) * d), z = (int)Math.Floor(hz + 0.5 + Math.Sin(angle) * d);
            if (NestSpot(x, z, who) is not { } spot) continue;
            if (Spawn(type, spot, who, Encounter.Hunt, a.Passive) != null) added++;
        }
        if (added > 0) nestReinforcedMs[key] = now;
        return added;
    }

    /// <summary>Somewhere dark on a cave floor, out of reach of any player's first steps, for a spider of a nest to come out of.</summary>
    private Vec3d NestSpot(int x, int z, Entity who)
    {
        if (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, (int)who.Pos.Y, z) == null) return null;
        if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != 8) return null;
        if (who.Pos.XYZ.HorizontalSquareDistanceTo(x + 0.5, z + 0.5) < 8 * 8) return null;
        if (sapi.World.GetNearestEntity(new Vec3d(x + 0.5, who.Pos.Y, z + 0.5), NoSpawnRadius, 24, e => e != who && e is EntityPlayer p && p.Alive) != null) return null;
        int y = Senses.FindFloor(sapi.World, x, (int)Math.Floor(who.Pos.Y), z, 2, 10);
        if (y == int.MinValue) return null;
        var spot = new Vec3d(x + 0.5, y, z + 0.5);
        if (Senses.LightAt(sapi.World, spot.AddCopy(0, 1, 0), who) >= Senses.LitLevel || Wards.Warded(sapi.World, spot)) return null;
        return spot;
    }
}
