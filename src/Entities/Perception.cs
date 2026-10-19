using System;
using System.Collections.Generic;
using System.Globalization;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>How an entity last knew where someone was: not at all, by a sound, by a sense other than sight, or by seeing them.</summary>
public enum Contact { None, Heard, Sensed, Seen }

/// <summary>
/// What an entity can perceive, from the <c>senses</c> object of its task config (all fields optional). An entity
/// without one has no profile, and the tasks keep their old behaviour (they know where their target is).
/// See docs/design/entity-ai-overhaul/README.md, section 4.1.
/// </summary>
public sealed class SenseProfile
{
    /// <summary>How far (blocks) it sees someone standing in light of 8 or more, in 4 to 7, and in less.</summary>
    public float SightLit = 24, SightDim = 12, SightDark = 6;
    /// <summary>Half the angle of its gaze, in degrees from the way its body faces.</summary>
    public float SightCone = 70;
    /// <summary>Whether it needs a clear line to see (false: it sees through walls within range, as nothing in the roster does yet).</summary>
    public bool SightNeedsLine = true;
    /// <summary>Range multiplier for someone carrying a light, at a torch's brightness or more (a candle counts half as much).</summary>
    public float CarriedLight = 1;
    /// <summary>How far (blocks) it hears a noise of loudness 1; a noise of loudness l is heard within hearing times l.</summary>
    public float Hearing = 16;
    /// <summary>Whether it hears someone running (as a noise of loudness 0.4 at them).</summary>
    public bool HearsRunning = true;
    /// <summary>Within this range it senses someone whose Reality Stability is below 0.4, whatever the light (0: never).</summary>
    public float FearSense;
    /// <summary>Within this range it knows someone is there regardless (bumping into them).</summary>
    public float Touch = 2;
    /// <summary>Multiplier on every sight range while the person sneaks.</summary>
    public float SneakFactor = 0.5f;
    /// <summary>How long a last known position is believed after contact is lost, in seconds.</summary>
    public float MemorySeconds = 8;
    /// <summary>
    /// Tracking: a stalker that has lost its target gets, every this many seconds (give or take a quarter), a vague
    /// idea of where they are (see <see cref="Belief.Vague"/>), off by up to <see cref="TrackError"/> blocks. 0: never.
    /// </summary>
    public float TrackSeconds;
    /// <summary>How far (blocks) a tracked guess may be off.</summary>
    public float TrackError = 10;
    /// <summary>The Duller: it senses someone just the other side of a wall (within 2.6 blocks, no line between).</summary>
    public bool Wall;
    /// <summary>The Clump: no eyes; it only hears and touches.</summary>
    public bool NoSight;
    /// <summary>The Watch: it sees through glass.</summary>
    public bool Glass;
    /// <summary>The Thing: it perceives only what is in the water, and hears swimming.</summary>
    public bool Water;

    /// <summary>The fallback for an entity probed without a profile of its own: the defaults above.</summary>
    public static readonly SenseProfile Default = new();

    /// <summary>A profile from a <c>senses</c> config object, or null where there is none.</summary>
    public static SenseProfile Parse(JsonObject senses)
    {
        if (senses == null || !senses.Exists) return null;
        var p = new SenseProfile
        {
            SightLit = senses["sightLit"].AsFloat(Default.SightLit),
            SightDim = senses["sightDim"].AsFloat(Default.SightDim),
            SightDark = senses["sightDark"].AsFloat(Default.SightDark),
            SightCone = senses["sightCone"].AsFloat(Default.SightCone),
            SightNeedsLine = senses["sightNeedsLine"].AsBool(true),
            CarriedLight = senses["carriedLight"].AsFloat(Default.CarriedLight),
            Hearing = senses["hearing"].AsFloat(Default.Hearing),
            HearsRunning = senses["hearsRunning"].AsBool(true),
            FearSense = senses["fearSense"].AsFloat(0),
            Touch = senses["touch"].AsFloat(Default.Touch),
            SneakFactor = senses["sneakFactor"].AsFloat(Default.SneakFactor),
            MemorySeconds = senses["memorySeconds"].AsFloat(Default.MemorySeconds),
            TrackSeconds = senses["trackSeconds"].AsFloat(0),
            TrackError = senses["trackError"].AsFloat(10),
        };
        foreach (string special in (senses["special"].AsString("") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            p.SetSpecial(special);
        return p;
    }

    private void SetSpecial(string special)
    {
        switch (special.ToLowerInvariant())
        {
            case "wall": Wall = true; break;
            case "noiseonly": NoSight = true; break;
            case "glass": Glass = true; break;
            case "water": Water = true; break;
        }
    }

    /// <summary>A copy with some fields changed, from "name=value,name=value" (for probing: /backrooms perceive).</summary>
    public SenseProfile With(string overrides, out string error)
    {
        error = null;
        var p = (SenseProfile)MemberwiseClone();
        if (string.IsNullOrWhiteSpace(overrides)) return p;
        foreach (string pair in overrides.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            string[] kv = pair.Split('=', 2);
            string name = kv[0].ToLowerInvariant(), value = kv.Length > 1 ? kv[1] : "true";
            bool ok = float.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out float f);
            bool on = value is "true" or "on" or "1";
            switch (name)
            {
                case "sightlit" when ok: p.SightLit = f; break;
                case "sightdim" when ok: p.SightDim = f; break;
                case "sightdark" when ok: p.SightDark = f; break;
                case "sightcone" when ok: p.SightCone = f; break;
                case "sightneedsline": p.SightNeedsLine = on; break;
                case "carriedlight" when ok: p.CarriedLight = f; break;
                case "hearing" when ok: p.Hearing = f; break;
                case "hearsrunning": p.HearsRunning = on; break;
                case "fearsense" when ok: p.FearSense = f; break;
                case "touch" when ok: p.Touch = f; break;
                case "sneakfactor" when ok: p.SneakFactor = f; break;
                case "memoryseconds" when ok: p.MemorySeconds = f; break;
                case "trackseconds" when ok: p.TrackSeconds = f; break;
                case "trackerror" when ok: p.TrackError = f; break;
                case "special": p.SetSpecial(value); break;
                default: error = $"Unknown sense or bad value: {pair}"; return null;
            }
        }
        return p;
    }

    public override string ToString() => string.Format(CultureInfo.InvariantCulture,
        "sight {0}/{1}/{2} cone {3}{4}, carried x{5}, hearing {6}{7}, fear {8}, touch {9}, sneak x{10}, memory {11}s{16}{12}{13}{14}{15}",
        SightLit, SightDim, SightDark, SightCone, SightNeedsLine ? "" : " (no line needed)", CarriedLight, Hearing, HearsRunning ? " (hears running)" : "",
        FearSense, Touch, SneakFactor, MemorySeconds, Wall ? ", wall" : "", NoSight ? ", no sight" : "", Glass ? ", glass" : "", Water ? ", water" : "",
        TrackSeconds > 0 ? string.Format(CultureInfo.InvariantCulture, ", tracks every {0}s (off by {1})", TrackSeconds, TrackError) : "");

    private static readonly Dictionary<string, SenseProfile> ByCode = new();

    /// <summary>
    /// An entity type's profile: the <c>senses</c> of the first task in its server task list that has one, or null.
    /// Cached by entity code (cleared when a server stops, see <see cref="Perception.Reset"/>).
    /// </summary>
    public static SenseProfile Of(Entity entity)
    {
        string code = entity.Code?.ToString();
        if (code == null) return null;
        lock (ByCode)
        {
            if (ByCode.TryGetValue(code, out SenseProfile cached)) return cached;
        }
        SenseProfile found = null;
        foreach (JsonObject behavior in entity.Properties?.Server?.BehaviorsAsJsonObj ?? Array.Empty<JsonObject>())
        {
            if (behavior["code"].AsString() != "taskai") continue;
            foreach (JsonObject task in behavior["aitasks"].AsArray() ?? Array.Empty<JsonObject>())
            {
                found = Parse(task["senses"]);
                if (found != null) break;
            }
            if (found != null) break;
        }
        lock (ByCode) ByCode[code] = found;
        return found;
    }

    internal static void ClearCache() { lock (ByCode) ByCode.Clear(); }
}

/// <summary>
/// Where an entity believes someone is: the last position it had from seeing, sensing or hearing them, how strongly,
/// and when. Confidence fades to nothing over the profile's memory; then the entity has lost them.
/// See docs/design/entity-ai-overhaul/README.md, section 4.3.
/// </summary>
public sealed class Belief
{
    /// <summary>The last known position (null until there has been any contact).</summary>
    public Vec3d Pos;
    /// <summary>When the last contact was (elapsed ms; -1 for never).</summary>
    public long AtMs = -1;
    /// <summary>How sure that contact was: 1 seen, 0.8 sensed, 0.6 heard.</summary>
    public double Strength;
    public Contact Source;
    /// <summary>
    /// A guess from tracking (a stalker's vague idea of where someone is), not a contact: it lets a stalker move
    /// towards the area, but never counts as contact, never turns a stalk to the hunt, and is never shared with a pack
    /// as the stronger belief. Cleared by any real <see cref="Take"/>.
    /// </summary>
    public bool Vague;
    /// <summary>Sounds heard in a row (each narrows the guess), reset by any other contact.</summary>
    public int HeardInARow;

    public double ConfidenceAt(long now, double memorySeconds) =>
        AtMs < 0 ? 0 : Strength * Math.Max(0, 1 - (now - AtMs) / (memorySeconds * 1000));

    public bool Lost(long now, double memorySeconds) => ConfidenceAt(now, memorySeconds) <= 0;

    /// <summary>Takes a contact, unless what it already believes is stronger by now.</summary>
    public bool Take(Vec3d pos, double strength, Contact source, long now, double memorySeconds)
    {
        if (strength < ConfidenceAt(now, memorySeconds)) return false;
        HeardInARow = source == Contact.Heard ? HeardInARow + 1 : 0;
        Vague = false;
        Pos = pos.Clone();
        AtMs = now;
        Strength = strength;
        Source = source;
        return true;
    }

    public void Forget()
    {
        Pos = null;
        AtMs = -1;
        Strength = 0;
        Source = Contact.None;
        HeardInARow = 0;
        Vague = false;
    }
}

/// <summary>A noise somewhere: where, how loud (1 carries as far as an entity's full hearing), what made it, and who (an entity id, or -1).</summary>
public readonly record struct NoiseEvent(int Id, Vec3d Pos, double Loudness, string Source, long Who, long AtMs);

/// <summary>
/// The noises of the last two seconds, for whatever listens. The engine sends sounds only to players, so the mod
/// raises its own: running, breaking things, doors, fights, cries, a thrown stone landing (README section 4.2).
/// </summary>
public sealed class NoiseBus
{
    /// <summary>How long a noise is kept for listeners to hear.</summary>
    public const long KeepMs = 2000;

    private readonly List<NoiseEvent> events = new();
    private int nextId;

    public void Raise(Vec3d pos, double loudness, string source, Entity who, long now)
    {
        if (pos == null || loudness <= 0) return;
        Prune(now);
        events.Add(new NoiseEvent(++nextId, pos.Clone(), loudness, source, who?.EntityId ?? -1, now));
    }

    /// <summary>The noises still heard at a moment.</summary>
    public IReadOnlyList<NoiseEvent> Recent(long now)
    {
        Prune(now);
        return events;
    }

    /// <summary>The noise heard best at a position by a listener with a hearing range, or null; optionally only from one entity.</summary>
    public NoiseEvent? Loudest(Vec3d at, double hearing, long now, long fromWho = -2)
    {
        Prune(now);
        NoiseEvent? best = null;
        double bestScore = double.MinValue;
        foreach (NoiseEvent e in events)
        {
            if (fromWho != -2 && e.Who != fromWho) continue;
            double d = e.Pos.DistanceTo(at), reach = hearing * e.Loudness;
            if (d > reach) continue;
            double score = e.Loudness - d / Math.Max(1, hearing);
            if (score > bestScore) { bestScore = score; best = e; }
        }
        return best;
    }

    public void Clear() => events.Clear();

    private void Prune(long now)
    {
        // (A time in the future is one left from an earlier server in this process)
        events.RemoveAll(e => now - e.AtMs > KeepMs || e.AtMs > now);
    }
}

/// <summary>
/// The shared perception model: what an entity with a <see cref="SenseProfile"/> sees, hears and senses of someone,
/// and what it comes to believe from that. Server side; see docs/design/entity-ai-overhaul/README.md, section 4.
/// </summary>
public static class Perception
{
    /// <summary>Stability below which an entity with a fear sense senses someone whatever the light.</summary>
    public const double FearStability = 0.4;
    /// <summary>A Duller's reach through a wall.</summary>
    public const double WallReach = 2.6;
    /// <summary>How much a heard position may be off by (blocks), before further sounds narrow it.</summary>
    public const double HeardError = 3;

    private static long calls, ticks;

    /// <summary>How many perception checks have run, and how long they took (stopwatch ticks), since the last reset.</summary>
    public static (long Calls, long Ticks) Cost => (calls, ticks);

    /// <summary>Forgets cached profiles and the cost counters (a server stopping: statics outlive it in the same process).</summary>
    public static void Reset()
    {
        SenseProfile.ClearCache();
        calls = ticks = 0;
    }

    /// <summary>The light someone stands in, as an entity sees it: the world's at their feet or eyes, whichever is brighter, or what they carry.</summary>
    public static int LightOn(Entity who)
    {
        IWorldAccessor world = who.World;
        return Math.Max(Senses.LightAt(world, Senses.Eyes(who), who), Senses.LightAt(world, who.Pos.XYZ.Add(0, 0.2, 0), who));
    }

    /// <summary>
    /// How plainly an entity sees someone (0: not at all; about 0.5 at the edge of its range, 1.25 close by), and if
    /// not, why not. The range comes from the light on them, widened for a carried light and narrowed for a sneak; they
    /// must be inside its gaze (unless within touch) and, for most, in a clear line.
    /// </summary>
    public static double Sight(Entity viewer, Entity who, SenseProfile p, out string why)
    {
        why = null;
        if (p.NoSight) { why = "it has no eyes"; return 0; }
        if (p.Water && !InWater(who)) { why = "out of the water"; return 0; }
        IWorldAccessor world = viewer.World;
        Vec3d eye = Senses.Eyes(viewer), centre = Senses.Centre(who);
        double d = eye.DistanceTo(centre);
        int light = LightOn(who);
        double range = light >= Senses.LitLevel ? p.SightLit : light >= 4 ? p.SightDim : p.SightDark;
        int held = Senses.HeldLight(who);
        if (held > 0 && p.CarriedLight != 1) range *= 1 + (p.CarriedLight - 1) * Math.Min(1, held / 14.0);
        if (Senses.Sneaking(who)) range *= p.SneakFactor;
        if (d > range) { why = string.Format(CultureInfo.InvariantCulture, "too far for the light ({0:0} > {1:0})", d, range); return 0; }
        if (d > p.Touch)
        {
            float toward = (float)Math.Atan2(who.Pos.X - viewer.Pos.X, who.Pos.Z - viewer.Pos.Z);
            double off = Math.Abs(GameMath.AngleRadDistance(viewer.Pos.Yaw, toward)) * GameMath.RAD2DEG;
            if (off > p.SightCone) { why = string.Format(CultureInfo.InvariantCulture, "outside its gaze ({0:0} degrees off)", off); return 0; }
        }
        if (p.SightNeedsLine && !Senses.ClearLine(world, eye, centre, p.Glass) && !Senses.ClearLine(world, eye, Senses.Eyes(who), p.Glass))
        {
            why = "no line of sight";
            return 0;
        }
        return Math.Max(0.5, 1.25 - 0.75 * d / Math.Max(1, range));
    }

    /// <summary>What an entity senses of someone without seeing or hearing them (touch, a wall's thickness, fear), or null.</summary>
    public static string Sensed(Entity entity, Entity who, SenseProfile p)
    {
        double d = entity.Pos.DistanceTo(who.Pos);
        if (d <= p.Touch && (d <= 1.2 || Senses.ClearLine(entity.World, Senses.Centre(entity), Senses.Centre(who)))) return "touch";
        if (p.Wall && entity.Pos.XYZ.HorizontalSquareDistanceTo(who.Pos.X, who.Pos.Z) <= WallReach * WallReach
            && Math.Abs(who.Pos.Y - entity.Pos.Y) < 1.5 && !Senses.ClearLine(entity.World, Senses.Centre(entity), Senses.Centre(who))) return "wall";
        if (p.FearSense > 0 && d <= p.FearSense && Senses.Stability(who) < FearStability) return "fear";
        return null;
    }

    /// <summary>
    /// What an entity hears of someone: the loudest of their noises within its hearing (the noise bus), or their
    /// running, or their swimming (for things in the water), with where it came from. Null if nothing.
    /// </summary>
    public static NoiseEvent? Heard(Entity entity, Entity who, SenseProfile p, NoiseBus bus, long now)
    {
        Vec3d ears = Senses.Eyes(entity);
        NoiseEvent? heard = null;
        if (!p.Water) heard = bus?.Loudest(ears, p.Hearing, now, who.EntityId);
        // Running is heard as it happens (the director's own running noise comes only every two seconds)
        if (heard == null && p.HearsRunning && !p.Water && Senses.Running(who) && who.Pos.DistanceTo(ears) <= p.Hearing * 0.4)
            heard = new NoiseEvent(0, who.Pos.XYZ, 0.4, "run", who.EntityId, now);
        if (heard == null && p.Water && InWater(who) && Moving(who) && who.Pos.DistanceTo(ears) <= p.Hearing)
            heard = new NoiseEvent(0, who.Pos.XYZ, 0.5, "swim", who.EntityId, now);
        return heard;
    }

    /// <summary>The loudest noise of anyone's (or anything's) within an entity's hearing, or null: for things that come to see what made it.</summary>
    public static NoiseEvent? HeardAnything(Entity entity, SenseProfile p, NoiseBus bus, long now) =>
        p.Water ? null : bus?.Loudest(Senses.Eyes(entity), p.Hearing, now);

    /// <summary>What a perceive pass found, for logging and probes.</summary>
    public readonly record struct Result(Contact Contact, double Plainness, string WhyNotSeen, string Sense, NoiseEvent? Noise);

    /// <summary>
    /// One look about: sees, else senses, else hears someone, and updates what the entity believes about where they
    /// are. A heard position is off by up to <see cref="HeardError"/> blocks, less with each sound in a row.
    /// </summary>
    public static Result Perceive(Entity entity, Entity who, SenseProfile p, Belief belief, NoiseBus bus, long now)
    {
        long started = System.Diagnostics.Stopwatch.GetTimestamp();
        try
        {
            double plain = Sight(entity, who, p, out string why);
            if (plain > 0)
            {
                belief.Take(who.Pos.XYZ, 1, Contact.Seen, now, p.MemorySeconds);
                return new Result(Contact.Seen, plain, null, null, null);
            }
            string sense = Sensed(entity, who, p);
            if (sense != null)
            {
                belief.Take(who.Pos.XYZ, 0.8, Contact.Sensed, now, p.MemorySeconds);
                return new Result(Contact.Sensed, 0, why, sense, null);
            }
            NoiseEvent? noise = Heard(entity, who, p, bus, now);
            if (noise is { } n)
            {
                int inARow = belief.Source == Contact.Heard && !belief.Vague && !belief.Lost(now, p.MemorySeconds) ? belief.HeardInARow + 1 : 1;
                double error = HeardError / inARow;
                // (The same noise always gives the same guess, so a guess does not jitter while one noise lasts)
                var rand = new Random(n.Id * 7919 + (int)(entity.EntityId & 0xFFFF));
                double angle = rand.NextDouble() * Math.PI * 2, off = rand.NextDouble() * error;
                belief.Take(n.Pos.AddCopy(Math.Cos(angle) * off, 0, Math.Sin(angle) * off), 0.6, Contact.Heard, now, p.MemorySeconds);
                return new Result(Contact.Heard, 0, why, null, n);
            }
            return new Result(Contact.None, 0, why, null, null);
        }
        finally
        {
            calls++;
            ticks += System.Diagnostics.Stopwatch.GetTimestamp() - started;
        }
    }

    private static bool InWater(Entity who) => who.Swimming || who.FeetInLiquid;

    private static bool Moving(Entity who) =>
        who is EntityAgent agent && agent.ServerControls.TriesToMove || who.Pos.Motion.LengthSq() > 0.0004;
}
