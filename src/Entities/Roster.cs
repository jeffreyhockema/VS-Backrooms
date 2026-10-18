using System;
using System.Collections.Generic;
using Vintagestory.API.Common.Entities;

namespace Backrooms.Entities;

/// <summary>How dangerous a place is, from somewhere nothing hostile goes to the edge into the next level.</summary>
public enum MenaceBand
{
    /// <summary>Nothing hostile spawns, and anything hostile that wanders in turns away.</summary>
    Safe,
    /// <summary>The heart of a level: sounds, and things seen far off that leave when approached.</summary>
    Heartland,
    /// <summary>Further out: things that follow at a distance and test you.</summary>
    Approach,
    /// <summary>The edge into the next level, and the ways through: things that hunt.</summary>
    Threshold,
}

/// <summary>What a spawned entity is there to do.</summary>
public enum Encounter
{
    /// <summary>Going about its own business (Facelings, rats in the heartland). Harmless unless provoked.</summary>
    Ambient,
    /// <summary>Seen far off, standing or crossing a doorway; leaves when approached or watched.</summary>
    Glimpse,
    /// <summary>Follows at a distance, out of the light; closes in when the player falters.</summary>
    Stalk,
    /// <summary>Seeks and attacks.</summary>
    Hunt,
    /// <summary>Leaving: running off to be despawned out of sight.</summary>
    Leave,
}

[Flags]
public enum Encounters
{
    None = 0,
    Ambient = 1,
    Glimpse = 2,
    Stalk = 4,
    Hunt = 8,
    Menacing = Glimpse | Stalk | Hunt,
}

/// <summary>One kind of entity a level can hold, and when.</summary>
public sealed record RosterEntry(string Code, MenaceBand MinBand, Encounters Kinds, double Weight, int PackMin = 1, int PackMax = 1)
{
    /// <summary>Only ever put down in the dark (Smilers).</summary>
    public bool NeedsDark { get; init; }

    /// <summary>Only on Level 11 below the streets.</summary>
    public bool SubwayOnly { get; init; }

    /// <summary>Only while a Reality Shift has the lights out (the Mangled), and gone when it ends.</summary>
    public bool ShiftOnly { get; init; }

    /// <summary>Put down in deep water (The Thing on Level 7).</summary>
    public bool Aquatic { get; init; }

    /// <summary>Lies in wait ahead of the player rather than following (Clumps).</summary>
    public bool Ambush { get; init; }

    /// <summary>How likely a wanderer picked for the moment is actually put down (Facelings are met seldom).</summary>
    public double Rarity { get; init; } = 1;

    /// <summary>Put down in a frenzy: rats in the Screaming, crossing the way ahead at a run.</summary>
    public bool Frenzy { get; init; }

    /// <summary>Only put down under the open sky (the Neighborhood Watch, too tall for any door).</summary>
    public bool Outdoors { get; init; }
}

/// <summary>A distant sound, with how its pitch may vary.</summary>
public sealed record DistantSound(string Location, float PitchMin = 0.9f, float PitchMax = 1.1f, float Volume = 0.7f);

/// <summary>
/// How much more dangerous everything is in a level, from 0 (the Lobby) towards 1 (the city): set on each entity as it
/// is put down, it makes it faster, harder-hitting, tougher and more persistent, and makes the director send more of
/// them, more often, to hunt. Deeper levels reward the risk: fuller caches, and a bounty on what you kill.
/// </summary>
public static class Danger
{
    /// <summary>Entity attribute: the danger of the level it was put down in.</summary>
    public const string Key = "backrooms:danger";

    public static double OfLevel(int level) => level switch
    {
        0 => 0,
        1 => 0.12,
        2 => 0.24,
        3 => 0.36,
        4 => 0.44,
        5 => 0.52,
        6 => 0.6,
        7 => 0.66,
        8 => 0.74,
        9 => 0.82,
        10 => 0.88,
        11 => 0.95,
        Backrooms.Worldgen.WorldLayout.Poolrooms => 0.5,
        // The far places (ids 14-20)
        Backrooms.Worldgen.WorldLayout.RunLevel => 0.9, // Level !: the horde, Class 5
        Backrooms.Worldgen.WorldLayout.FunLevel => 0.9, // Level Fun: Survival Difficulty 5, the Partygoers' own level
        Backrooms.Worldgen.WorldLayout.TheEnd => 0.4,
        Backrooms.Worldgen.WorldLayout.Hub => 0,
        Backrooms.Worldgen.WorldLayout.Level974 => 0,
        Backrooms.Worldgen.WorldLayout.Level3999 => 0.8, // (only its Neon Blackout has anything in it)
        Backrooms.Worldgen.WorldLayout.Level188 => 0.45, // the Courtyard of Windows: unsafe (Class 2-5 by the wikis), its windows worst of all
        // Level 94 keeps its own balance (the King's trial)
        _ => 0,
    };

    public static double Of(Entity entity) => entity.Attributes.GetDouble(Key, 0);

    /// <summary>Movement: a quarter to a third faster at the bottom.</summary>
    public static float Speed(double d) => (float)(1 + 0.3 * d);

    /// <summary>Damage: about double by Level 9.</summary>
    public static float Damage(double d) => (float)(1 + 1.1 * d);

    /// <summary>Time between attacks: down to seven tenths.</summary>
    public static float Cooldown(double d) => (float)(1 - 0.3 * d);

    /// <summary>Extra health, as a share of the base: up to more than twice as much.</summary>
    public static float ExtraHealth(double d) => (float)(1.4 * d);

    /// <summary>Armour tiers: from Level 6 down, everything strikes one tier harder.</summary>
    public static int TierBonus(double d) => d >= 0.6 ? 1 : 0;
}

/// <summary>Which entities each level holds, and the sounds it makes when nothing is there.</summary>
public static class Roster
{
    public const string Smiler = "backrooms:smiler";
    public const string Hound = "backrooms:hound";
    public const string Faceling = "backrooms:faceling";
    public const string FacelingChild = "backrooms:faceling-child";
    public const string DeathmothMale = "backrooms:deathmoth-male";
    public const string DeathmothFemale = "backrooms:deathmoth-female";
    public const string SkinStealer = "backrooms:skinstealer";
    public const string Duller = "backrooms:duller";
    public const string DeathRat = "backrooms:deathrat";
    public const string Clump = "backrooms:clump";
    public const string TheThing = "backrooms:thething";
    public const string Mangled = "backrooms:mangled";
    /// <summary>The dark figures of Level 0 (the Howler of the found footage; Entity 1 on the Fandom wiki).</summary>
    public const string Bacteria = "backrooms:bacteria";
    /// <summary>Wanderers the Backrooms wore down: starved, parched, sleepless (Entity 15).</summary>
    public const string Wretch = "backrooms:wretch";
    public const string AnimationClay = "backrooms:animation-clay";
    public const string AnimationWooden = "backrooms:animation-wooden";
    public const string AnimationPaper = "backrooms:animation-paper";
    public const string RoboMan = "backrooms:roboman";
    public const string Partygoer = "backrooms:partygoer";
    public const string PartygoerIntern = "backrooms:partygoer-intern";
    /// <summary>A giant eyeball on six long legs, walking the Suburbs' streets (Entity 96).</summary>
    public const string NeighborhoodWatch = "backrooms:neighborhoodwatch";

    /// <summary>Every entity the director puts down.</summary>
    public static readonly string[] AllCodes = { Smiler, Hound, Faceling, FacelingChild, DeathmothMale, DeathmothFemale, SkinStealer, Duller, DeathRat, Clump, TheThing, Mangled, Bacteria, Wretch,
        AnimationClay, AnimationWooden, AnimationPaper, RoboMan, Partygoer, PartygoerIntern, NeighborhoodWatch };

    private static RosterEntry E(string code, MenaceBand band, Encounters kinds, double weight, int packMin = 1, int packMax = 1) =>
        new(code, band, kinds, weight, packMin, packMax);

    private const MenaceBand Safe = MenaceBand.Safe, Heart = MenaceBand.Heartland, Approach = MenaceBand.Approach, Edge = MenaceBand.Threshold;
    private const Encounters Amb = Encounters.Ambient, Menacing = Encounters.Menacing;

    private static readonly Dictionary<int, RosterEntry[]> ByLevel = new()
    {
        // The Lobby: empty, as the lore has it, but for eyes in the blackouts and something waiting at the edge
        [0] = new[]
        {
            E(Smiler, Approach, Menacing, 1.0) with { NeedsDark = true },
            E(Hound, Edge, Encounters.Glimpse | Encounters.Stalk, 0.5, 1, 2),
            // "Wanderers have claimed to have seen dark figures stalking them between the corridors": seen far off, now and
            // then following; it only turns on someone who runs near the way out
            E(Bacteria, Approach, Encounters.Glimpse | Encounters.Stalk, 0.6),
        },
        // The Habitable Zone: wanderers and rats in the halls, Hounds in the dark sections
        [1] = new[]
        {
            E(Faceling, Heart, Amb, 0.5) with { Rarity = 0.35 },
            E(DeathRat, Heart, Menacing, 0.6, 2, 4),
            E(Hound, Approach, Menacing, 1.0, 2, 3),
            E(Wretch, Approach, Menacing, 0.3),
            E(Smiler, Approach, Menacing, 0.5) with { NeedsDark = true },
            E(SkinStealer, Approach, Menacing, 0.4),
            E(DeathmothFemale, Edge, Encounters.Stalk | Encounters.Hunt, 0.4, 3, 5),
        },
        // Pipe Dreams: rats in the pipes and the eyes of the Smilers in every dark stretch
        [2] = new[]
        {
            E(DeathRat, Heart, Menacing, 1.0, 3, 5),
            E(Smiler, Heart, Menacing, 1.2) with { NeedsDark = true },
            E(Hound, Edge, Encounters.Stalk | Encounters.Hunt, 0.6, 2, 3),
            // Bundles of limbs, wedged into the tight spots, that grab whoever squeezes past
            E(Clump, Approach, Encounters.Stalk, 0.5) with { Ambush = true },
        },
        [3] = new[]
        {
            E(Faceling, Heart, Amb, 0.4) with { Rarity = 0.35 },
            E(Smiler, Heart, Menacing, 0.8) with { NeedsDark = true },
            E(Hound, Approach, Menacing, 1.0, 2, 3),
            E(SkinStealer, Approach, Menacing, 0.5),
            E(Duller, Approach, Encounters.Stalk | Encounters.Hunt, 0.5),
            E(Clump, Approach, Encounters.Stalk, 0.3) with { Ambush = true },
            E(Wretch, Approach, Menacing, 0.4, 1, 2),
        },
        // The Abandoned Office: a calm place where people rest; a Duller in the walls, the odd Hound near the stairs
        [4] = new[]
        {
            E(Faceling, Safe, Amb, 1.5) with { Rarity = 0.3 },
            E(Duller, Approach, Encounters.Stalk | Encounters.Hunt, 1.0),
            E(Hound, Approach, Menacing, 0.3, 1, 2),
        },
        [5] = new[]
        {
            E(Faceling, Heart, Amb, 0.6) with { Rarity = 0.35 },
            E(FacelingChild, Heart, Amb, 0.15) with { Rarity = 0.35 },
            E(DeathmothMale, Heart, Amb | Encounters.Glimpse, 0.6, 2, 3),
            E(Hound, Approach, Menacing, 1.0, 2, 3),
            E(SkinStealer, Approach, Menacing, 0.6),
            E(DeathmothFemale, Approach, Encounters.Stalk | Encounters.Hunt, 0.6, 3, 5),
            E(Wretch, Approach, Menacing, 0.3),
        },
        // Lights Out: the darkness is the entity. Things are heard; almost nothing is ever seen
        [6] = new[]
        {
            E(Smiler, Approach, Menacing, 0.3) with { NeedsDark = true },
            E(Duller, Approach, Encounters.Stalk | Encounters.Hunt, 0.8),
        },
        // Thalassophobia: something vast below the twilight zone, which is why nothing else lives down there
        [7] = new[]
        {
            E(TheThing, Approach, Encounters.Stalk | Encounters.Hunt, 1.0) with { Aquatic = true },
        },
        [8] = new[]
        {
            E(DeathRat, Heart, Menacing, 0.8, 2, 4),
            // (Level 8's feral dark: the Wretches, once the drifters of the vanilla spawner)
            E(Wretch, Heart, Menacing, 1.2, 1, 3),
            E(Duller, Approach, Encounters.Stalk | Encounters.Hunt, 0.5),
            E(Smiler, Approach, Menacing, 0.6) with { NeedsDark = true },
            E(Hound, Edge, Menacing, 0.8, 2, 3),
        },
        [9] = new[]
        {
            E(Faceling, Heart, Amb, 0.5) with { Rarity = 0.35 },
            E(FacelingChild, Heart, Amb, 0.3) with { Rarity = 0.35 },
            E(DeathRat, Heart, Menacing, 0.8, 2, 4),
            E(Hound, Approach, Menacing, 1.0, 2, 3),
            E(Smiler, Approach, Menacing, 0.5) with { NeedsDark = true },
            E(SkinStealer, Approach, Menacing, 0.5),
            E(Wretch, Approach, Menacing, 0.4, 1, 2),
            E(DeathmothFemale, Edge, Encounters.Stalk | Encounters.Hunt, 0.5, 3, 5),
            // The Neighborhood Watch: a giant eyeball on legs walking the streets, finding people by sight (AiTaskWatch)
            E(NeighborhoodWatch, Approach, Menacing, 0.7) with { Outdoors = true },
            // (The Mangled is not put down by the director: it comes with its own fog, see MangledEvent)
        },
        // The fields are safe; only near the barns where the city lies through the wall do Hounds come
        [10] = new[]
        {
            E(Hound, Edge, Menacing, 1.0, 2, 3),
            E(Clump, Edge, Encounters.Stalk, 0.6) with { Ambush = true },
        },
        // The Poolrooms: devoid of life, as far as anyone knows; only in the dark of the Sanguine Reservoir is anything ever seen
        [Backrooms.Worldgen.WorldLayout.Poolrooms] = new[]
        {
            E(Smiler, Heart, Encounters.Glimpse | Encounters.Stalk, 1.0) with { NeedsDark = true },
        },
        // Motion: the stop-motion rats potter about by day; by night the Animations come out, and hunt anything that does
        // not look animated
        [Backrooms.Worldgen.WorldLayout.Motion] = new[]
        {
            E(DeathRat, Safe, Amb, 0.6, 1, 2),
            E(AnimationClay, Approach, Menacing, 1.0, 1, 2),
            E(AnimationWooden, Approach, Menacing, 1.0, 1, 2),
            E(AnimationPaper, Approach, Encounters.Stalk | Encounters.Hunt, 0.7, 3, 5),
        },
        // The far places (ids 14-20). Level !: nothing from the director (the chase is its own)
        [Backrooms.Worldgen.WorldLayout.RunLevel] = Array.Empty<RosterEntry>(),
        // Level Fun: Partygoers walking the corridors in twos and threes (you can never catch one alone); the rest stand at
        // their parties (put down by Regions.FunSystem, not the director)
        [Backrooms.Worldgen.WorldLayout.FunLevel] = new[]
        {
            E(Partygoer, Approach, Encounters.Stalk, 1.0, 2, 3),
            E(PartygoerIntern, Approach, Encounters.Stalk, 0.4, 2, 2),
        },
        // The End: devoid of all life; only in the dark of its collapses, or with its lights out, a grin now and then
        [Backrooms.Worldgen.WorldLayout.TheEnd] = new[] { E(Smiler, Heart, Encounters.Glimpse, 1.0) with { NeedsDark = true } },
        [Backrooms.Worldgen.WorldLayout.Hub] = Array.Empty<RosterEntry>(),
        [Backrooms.Worldgen.WorldLayout.Level974] = Array.Empty<RosterEntry>(),
        // Level 3999: nothing hostile in the Neon Paradise; in the dark of its Blackout, Smilers, Hound packs, and
        // Partygoers (canon's Euphoric Wars) (MenaceSystem gives the Blackout the Threshold band, the rest Safe)
        [Backrooms.Worldgen.WorldLayout.Level3999] = new[]
        {
            E(Smiler, Heart, Menacing, 1.0) with { NeedsDark = true },
            E(Hound, Approach, Menacing, 0.8, 2, 3),
            E(Partygoer, Edge, Encounters.Stalk | Encounters.Hunt, 0.4, 2, 3),
        },
        // Level 188: the Windows are its own (Regions.L188System); a Skin-Stealer in the upper corridors now and then, a grin in
        // the dark (Miraheze's list, kept light)
        [Backrooms.Worldgen.WorldLayout.Level188] = new[]
        {
            E(SkinStealer, Approach, Encounters.Stalk | Encounters.Hunt, 0.5),
            E(Smiler, Heart, Encounters.Glimpse | Encounters.Stalk, 0.6) with { NeedsDark = true },
        },
        // The city: crowds of Facelings, Hounds that ignore you, rats in the alleys, a Duller in the subway
        [11] = new[]
        {
            E(Faceling, Heart, Amb, 1.4) with { Rarity = 0.6 },
            E(FacelingChild, Heart, Amb, 0.4) with { Rarity = 0.6 },
            E(Hound, Heart, Amb, 0.4, 1, 2),
            E(DeathRat, Heart, Menacing, 0.6, 2, 4),
            E(Duller, Approach, Encounters.Stalk | Encounters.Hunt, 0.5) with { SubwayOnly = true },
            E(Wretch, Approach, Menacing, 0.5, 1, 2) with { SubwayOnly = true },
        },
    };

    /// <summary>Level 94's castle: its Robo-Men, once someone has touched something there.</summary>
    public static readonly RosterEntry[] Castle = { E(RoboMan, Heart, Encounters.Hunt, 1.0, 1, 2) };

    /// <summary>The Snackrooms: only Facelings, sitting at the tables, friendly.</summary>
    public static readonly RosterEntry[] Snackrooms = { E(Faceling, Safe, Amb, 1.0) with { Rarity = 0.6 }, E(FacelingChild, Safe, Amb, 0.4) with { Rarity = 0.6 } };

    private static readonly RosterEntry[] None = Array.Empty<RosterEntry>();

    public static RosterEntry[] For(int level) => ByLevel.TryGetValue(level, out RosterEntry[] entries) ? entries : None;

    /// <summary>What lives in a den, and comes for those who go in.</summary>
    public static RosterEntry DenEntry(Backrooms.Worldgen.DenKind den) => den switch
    {
        Backrooms.Worldgen.DenKind.Pack => E(Hound, Heart, Menacing, 1, 2, 3),
        Backrooms.Worldgen.DenKind.Hive => E(DeathmothFemale, Heart, Encounters.Stalk | Encounters.Hunt, 1, 3, 5),
        Backrooms.Worldgen.DenKind.Dark => E(Smiler, Heart, Menacing, 1) with { NeedsDark = true },
        Backrooms.Worldgen.DenKind.Warren => E(DeathRat, Heart, Menacing, 1, 3, 5),
        Backrooms.Worldgen.DenKind.Lair => E(SkinStealer, Heart, Menacing, 1),
        _ => null,
    };

    /// <summary>How likely each kind of encounter is in a band: sounds, glimpses, stalkers, hunters.</summary>
    public static (double Sound, double Glimpse, double Stalk, double Hunt) Weights(MenaceBand band) => band switch
    {
        MenaceBand.Heartland => (0.65, 0.35, 0, 0),
        MenaceBand.Approach => (0.45, 0.25, 0.25, 0.05),
        MenaceBand.Threshold => (0.3, 0.2, 0.25, 0.25),
        _ => (1, 0, 0, 0),
    };

    /// <summary>How many menacing entities may be about a player at once in a band, whoever they were put down for (Ambient ones are counted apart).</summary>
    public static int Cap(MenaceBand band) => band switch
    {
        MenaceBand.Heartland => 2,
        MenaceBand.Approach => 4,
        MenaceBand.Threshold => 6,
        _ => 0,
    };

    /// <summary>The cap, with one more allowed from Level 5 down and another from Level 9.</summary>
    public static int Cap(MenaceBand band, int level)
    {
        int cap = Cap(band);
        if (cap == 0) return 0;
        double d = Danger.OfLevel(level);
        return cap + (d >= 0.5 ? 1 : 0) + (d >= 0.8 ? 1 : 0);
    }

    /// <summary>
    /// The encounter weights deeper down: fewer of the encounters are only a sound, and more of them stalk and hunt.
    /// Even the heart of a deep level is not quiet.
    /// </summary>
    public static (double Sound, double Glimpse, double Stalk, double Hunt) Weights(MenaceBand band, int level)
    {
        var w = Weights(band);
        double d = Danger.OfLevel(level);
        if (band == MenaceBand.Safe || d <= 0) return w;
        double stalk = band == MenaceBand.Heartland ? 0.15 * d : 0.1 * d;
        double hunt = band switch { MenaceBand.Heartland => 0.03 * d, MenaceBand.Approach => 0.15 * d, _ => 0.25 * d };
        return (Math.Max(0.1, w.Sound - stalk - hunt), w.Glimpse, w.Stalk + stalk, w.Hunt + hunt);
    }

    private static DistantSound S(string location, float pitchMin = 0.9f, float pitchMax = 1.1f, float volume = 0.7f) =>
        new(location, pitchMin, pitchMax, volume);

    private static readonly DistantSound HoundHowl = S("game:sounds/creature/wolf/howl*", 0.55f, 0.7f, 0.5f);
    private static readonly DistantSound HoundGrowl = S("game:sounds/creature/wolf/growl*", 0.6f, 0.75f, 0.6f);
    private static readonly DistantSound Footsteps = S("backrooms:sounds/entity/footsteps", 0.9f, 1.05f, 0.6f);
    private static readonly DistantSound Scratch = S("backrooms:sounds/entity/scratch", 0.85f, 1.1f, 0.6f);
    private static readonly DistantSound Murmur = S("backrooms:sounds/entity/murmur", 0.9f, 1.1f, 0.45f);
    private static readonly DistantSound Whisper = S("backrooms:sounds/effect/whisper", 0.8f, 1.0f, 0.5f);
    private static readonly DistantSound Scuttle = S("backrooms:sounds/effect/scuttle", 0.8f, 1.2f, 0.6f);
    private static readonly DistantSound Squeak = S("backrooms:sounds/entity/squeak", 0.8f, 1.1f, 0.5f);
    private static readonly DistantSound Groan = S("backrooms:sounds/entity/groan", 0.8f, 1.0f, 0.6f);
    private static readonly DistantSound Drag = S("backrooms:sounds/entity/drag", 0.85f, 1.05f, 0.6f);
    private static readonly DistantSound Cough = S("backrooms:sounds/entity/cough", 0.85f, 1.05f, 0.5f);
    private static readonly DistantSound Knock = S("backrooms:sounds/entity/knock", 0.9f, 1.05f, 0.6f);
    private static readonly DistantSound Slam = S("backrooms:sounds/entity/slam", 0.85f, 1.0f, 0.7f);
    private static readonly DistantSound Phone = S("backrooms:sounds/entity/phone", 1f, 1f, 0.45f);
    private static readonly DistantSound Static = S("backrooms:sounds/entity/static", 0.9f, 1.1f, 0.4f);
    private static readonly DistantSound Wings = S("backrooms:sounds/entity/wings", 0.8f, 1.1f, 0.6f);
    private static readonly DistantSound Cowbell = S("backrooms:sounds/entity/cowbell", 0.95f, 1.05f, 0.4f);
    private static readonly DistantSound CarAlarm = S("backrooms:sounds/entity/caralarm", 1f, 1f, 0.35f);
    private static readonly DistantSound Hurt = S("game:sounds/player/hurt*", 0.85f, 1.0f, 0.45f);
    private static readonly DistantSound Bell = S("game:sounds/effect/receptionbell", 0.9f, 1.0f, 0.4f);
    private static readonly DistantSound Rockfall = S("game:sounds/effect/rockslide", 0.8f, 1.0f, 0.5f);
    private static readonly DistantSound Drifter = S("game:sounds/creature/drifter-idle*", 0.8f, 0.95f, 0.55f);
    private static readonly DistantSound Worms = S("game:sounds/effect/wormgrunting", 0.8f, 1.0f, 0.5f);
    private static readonly DistantSound Machinery = S("game:sounds/effect/gearbox_turn", 0.6f, 0.8f, 0.5f);
    private static readonly DistantSound Drip = S("backrooms:sounds/ambient/pooldrip", 0.85f, 1.15f, 0.4f);
    private static readonly DistantSound Lapping = S("backrooms:sounds/ambient/poollap", 0.9f, 1.1f, 0.35f);
    private static readonly DistantSound Laughter = S("backrooms:sounds/entity/laughter", 0.9f, 1.15f, 0.55f);
    private static readonly DistantSound AllGlory = S("backrooms:sounds/entity/allglory", 0.95f, 1.05f, 0.45f);
    private static readonly DistantSound WatchSteps = S("backrooms:sounds/entity/watch-steps", 0.9f, 1.1f, 0.5f);

    private static readonly Dictionary<int, DistantSound[]> SoundsByLevel = new()
    {
        [0] = new[] { Scratch, Whisper, Footsteps, Murmur },
        [1] = new[] { HoundHowl, HoundGrowl, Drag, Footsteps, Scuttle, Squeak, Cough },
        [2] = new[] { Scuttle, Squeak, Groan, Scratch, Footsteps },
        [3] = new[] { Bell, Cough, Machinery, HoundGrowl, Footsteps, Hurt },
        [4] = new[] { Phone, Drag, Footsteps },
        [5] = new[] { Whisper, Knock, Footsteps, Wings, Cough, HoundGrowl },
        [6] = new[] { Footsteps, Whisper, Scratch, Scuttle },
        [7] = new[] { Groan },
        [8] = new[] { Rockfall, Drifter, Footsteps, Squeak },
        [9] = new[] { HoundHowl, Slam, Static, Footsteps, Hurt, Squeak, WatchSteps },
        [10] = new[] { Worms, Wings, Cowbell },
        [11] = new[] { CarAlarm, Murmur, Footsteps, Squeak },
        [Backrooms.Worldgen.WorldLayout.Poolrooms] = new[] { Drip, Lapping },
        [Backrooms.Worldgen.WorldLayout.Motion] = new[] { Laughter, Laughter, AllGlory, Squeak },
        // The far places (ids 14-20). Level !: none (its alarm and its horde are sound enough)
        [Backrooms.Worldgen.WorldLayout.RunLevel] = Array.Empty<DistantSound>(),
        // Level Fun: a party somewhere else: a cheer, a party horn, a balloon popping, laughing, now and then far-off singing
        [Backrooms.Worldgen.WorldLayout.FunLevel] = new[]
        {
            S("backrooms:sounds/ambient/fun/cheer", 0.9f, 1.1f, 0.45f), S("backrooms:sounds/ambient/fun/partyhorn", 0.85f, 1.15f, 0.4f),
            S("backrooms:sounds/ambient/fun/balloonpop", 0.85f, 1.15f, 0.4f), Laughter, S("backrooms:sounds/ambient/fun/singing", 0.95f, 1.05f, 0.35f),
        },
        // The End: near silence; a book falls somewhere, a shelf creaks, a chair scrapes, a page turns
        [Backrooms.Worldgen.WorldLayout.TheEnd] = new[]
        {
            S("backrooms:sounds/ambient/end/bookfall", 0.9f, 1.1f, 0.5f), S("backrooms:sounds/ambient/end/shelfcreak", 0.9f, 1.1f, 0.45f),
            S("backrooms:sounds/ambient/end/chairscrape", 0.9f, 1.05f, 0.45f), S("backrooms:sounds/ambient/end/pageturn", 0.95f, 1.05f, 0.4f),
        },
        [Backrooms.Worldgen.WorldLayout.Hub] = Array.Empty<DistantSound>(),
        [Backrooms.Worldgen.WorldLayout.Level974] = Array.Empty<DistantSound>(),
        [Backrooms.Worldgen.WorldLayout.Level3999] = Array.Empty<DistantSound>(),
        // Level 188: a hotel at night: a dead lift's chime, a TV through a wall, a vacuum cleaner far off, the ice machine,
        // footsteps on the floor above, knocking on glass
        [Backrooms.Worldgen.WorldLayout.Level188] = new[]
        {
            S("backrooms:sounds/effect/188/liftchime", 0.95f, 1.05f, 0.35f), S("backrooms:sounds/effect/188/tvwall", 0.9f, 1.1f, 0.35f),
            S("backrooms:sounds/effect/188/vacuum", 0.9f, 1.05f, 0.3f), S("backrooms:sounds/effect/188/icedrop", 0.9f, 1.1f, 0.35f),
            S("backrooms:sounds/effect/188/thump", 0.85f, 1.05f, 0.5f), S("backrooms:sounds/effect/188/knock", 0.9f, 1.1f, 0.4f), Footsteps,
        },
    };

    public static DistantSound[] SoundsFor(int level) => SoundsByLevel.TryGetValue(level, out DistantSound[] s) ? s : Array.Empty<DistantSound>();
}
