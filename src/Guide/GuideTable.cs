using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;

namespace Backrooms;

/// <summary>
/// The handbook's levels and creatures (config/guide.json, written by tools/gen_guide.py from its LEVELS, ENTITIES,
/// MEETS and @-marked pages; the text is in lang): what the handbook lists, and how the server knows a creature has
/// been met. Nothing here is hard-coded to a level or a creature, so new levels and creatures are table rows.
/// </summary>
public sealed class GuideTable
{
    /// <summary>One creature of What Lives Here, and the rules that say an entity is one of it.</summary>
    public sealed class Creature
    {
        public string Code;
        /// <summary>The levels it lives in (What Lives Here lists it once one of them has been visited).</summary>
        public int[] Levels = Array.Empty<int>();
        /// <summary>Entity codes (domain backrooms unless given; a trailing * matches any variant), or none for any type.</summary>
        public string[] Types = Array.Empty<string>();
        /// <summary>An attribute the entity must carry (the horde's mark, the King's nightmare), or null.</summary>
        public string Attribute;
        /// <summary>Only where the player is in one of these levels (null: anywhere).</summary>
        public int[] AtLevels;
        /// <summary>Not where the player is in one of these levels.</summary>
        public int[] NotAtLevels;
        /// <summary>A watched int attribute of the player that is non-zero once the thing has happened to them (not an entity).</summary>
        public string PlayerAttribute;

        /// <summary>Whether an entity is one of these, seen by a player in a level.</summary>
        public bool Matches(Entity entity, int playerLevel)
        {
            if (PlayerAttribute != null || entity?.Code == null) return false;
            if (AtLevels != null && Array.IndexOf(AtLevels, playerLevel) < 0) return false;
            if (NotAtLevels != null && Array.IndexOf(NotAtLevels, playerLevel) >= 0) return false;
            if (Attribute != null && !entity.Attributes.HasAttribute(Attribute)) return false;
            if (Types.Length == 0) return Attribute != null;
            foreach (string type in Types)
            {
                string domain = "backrooms", path = type;
                int colon = type.IndexOf(':');
                if (colon >= 0) { domain = type.Substring(0, colon); path = type.Substring(colon + 1); }
                if (entity.Code.Domain != domain) continue;
                if (path.EndsWith("*") ? entity.Code.Path.StartsWith(path.Substring(0, path.Length - 1), StringComparison.Ordinal) : entity.Code.Path == path)
                    return true;
            }
            return false;
        }
    }

    /// <summary>Every level with a page, in the order The Levels lists them.</summary>
    public int[] Levels = Array.Empty<int>();
    /// <summary>The levels listed (by name) before they have been visited.</summary>
    public int[] Listed = Array.Empty<int>();
    public Creature[] Entities = Array.Empty<Creature>();
    /// <summary>Ways Between Levels: for each section (lang guide-thresholds-s&lt;n&gt;), each line's levels (empty: always shown).</summary>
    public int[][][] Thresholds = Array.Empty<int[][]>();
    /// <summary>The end of What Lives Here, as <see cref="Thresholds"/> (lang guide-entities-s&lt;n&gt;).</summary>
    public int[][][] EntityNotes = Array.Empty<int[][]>();

    public const string Path = "config/guide.json";

    /// <summary>The table, from the mod's assets; an empty one (and an error in the log) if it cannot be read.</summary>
    public static GuideTable Load(ICoreAPI api)
    {
        try
        {
            IAsset asset = api.Assets.TryGet(new AssetLocation("backrooms", Path));
            if (asset != null) return Parse(asset.ToText());
            api.Logger.Error("[backrooms] {0} is missing: the handbook lists no levels or creatures", Path);
        }
        catch (Exception ex)
        {
            api.Logger.Error("[backrooms] could not read {0}: {1}", Path, ex);
        }
        return new GuideTable();
    }

    public static GuideTable Parse(string json)
    {
        var options = new JsonSerializerOptions { IncludeFields = true, PropertyNameCaseInsensitive = true, ReadCommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true };
        return JsonSerializer.Deserialize<GuideTable>(json, options) ?? new GuideTable();
    }

    public Creature Find(string code) => Entities.FirstOrDefault(c => c.Code == code);

    /// <summary>The creatures an entity counts as, for a player in a level (a Hound of the horde is both).</summary>
    public IEnumerable<string> CreaturesOf(Entity entity, int playerLevel)
    {
        foreach (Creature c in Entities)
            if (c.Matches(entity, playerLevel)) yield return c.Code;
    }
}

/// <summary>
/// What a player has found, as the handbook reads it: the levels visited (<c>backrooms:visitedLevels</c>, bits by
/// level id, the same the Hub's Keymaster reads) and the creatures met (<c>backrooms:metCreatures</c>, the codes of
/// config/guide.json joined by commas). Both are the player entity's watched attributes, so they are synced to that
/// player's client, kept through death and saved with the player. Written by the server only (<see cref="DiscoverySystem"/>).
/// </summary>
public static class Discovery
{
    public const string VisitedKey = "backrooms:visitedLevels", MetKey = "backrooms:metCreatures";

    /// <summary>The highest level id the visited bits hold (bit 31 is the sign).</summary>
    public const int MaxLevelBit = 30;

    public static int Visited(Entity player) => player?.WatchedAttributes.GetInt(VisitedKey) ?? 0;

    public static bool HasVisited(int bits, int level) => level is >= 0 and <= MaxLevelBit && (bits & (1 << level)) != 0;

    public static bool HasVisitedAny(int bits, IEnumerable<int> levels) => levels.Any(l => HasVisited(bits, l));

    public static HashSet<string> Met(Entity player)
    {
        string s = player?.WatchedAttributes.GetString(MetKey);
        return string.IsNullOrEmpty(s) ? new HashSet<string>() : new HashSet<string>(s.Split(',', StringSplitOptions.RemoveEmptyEntries));
    }

    /// <summary>Joins met codes in a fixed (sorted) order, so the same set is always the same string.</summary>
    public static string Join(IEnumerable<string> codes) => string.Join(",", codes.Distinct().OrderBy(c => c, StringComparer.Ordinal));
}
