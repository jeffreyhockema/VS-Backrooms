using System;
using System.Collections.Generic;
using System.Text.Json;

namespace Backrooms.Notes;

/// <summary>One thing a note can say: its key (lang <c>note-&lt;key&gt;</c>, <c>notetitle-&lt;key&gt;</c>), when it is due and what else it marks.</summary>
public sealed class NoteEntry
{
    public string Key;
    /// <summary>The reader must have been to one of these levels before it is due (empty: always due).</summary>
    public int[] Gate = Array.Empty<int>();
    /// <summary>What it marks on the map besides its paper's own mark, or null.</summary>
    public string Mark;
    public NoteTrack Track;
    public int Index;
}

/// <summary>An ordered series of notes: the main one, a level's, a rare one, or the scraps.</summary>
public sealed class NoteTrack
{
    public string Id;
    /// <summary>common, rare, scrap or special.</summary>
    public string Cls;
    /// <summary>The level whose notes advance it (61 for Level 6.1), or -1 for anywhere.</summary>
    public int Level = -1;
    /// <summary>The journal chapter it is shown in.</summary>
    public string Chapter;
    public List<NoteEntry> Entries = new();
}

/// <summary>
/// Every track and entry, as written by tools/gen_notes.py into config/notes.json (no text: that is in lang). No game
/// dependencies, so the layout harness reads it too.
/// </summary>
public sealed class NoteCatalog
{
    public const int SnackroomsKey = 61;
    public const string RareChapterDefault = "rare";

    public readonly List<NoteTrack> Tracks = new();
    public readonly Dictionary<string, NoteEntry> ByKey = new();
    public readonly Dictionary<string, NoteTrack> ById = new();
    private readonly Dictionary<int, NoteTrack> commonByLevel = new(), rareByLevel = new();
    public NoteTrack Main, Scraps, RareAny;
    public string RareChapter = RareChapterDefault;

    public NoteTrack CommonFor(int levelKey) => commonByLevel.TryGetValue(levelKey, out var t) ? t : null;
    public NoteTrack RareFor(int levelKey) => rareByLevel.TryGetValue(levelKey, out var t) ? t : null;
    public NoteEntry Entry(string key) => key != null && ByKey.TryGetValue(key, out var e) ? e : null;

    public static NoteCatalog Parse(string json)
    {
        var cat = new NoteCatalog();
        using JsonDocument doc = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true });
        JsonElement root = doc.RootElement;
        if (root.TryGetProperty("rareChapter", out JsonElement rc)) cat.RareChapter = rc.GetString();
        foreach (JsonElement jt in root.GetProperty("tracks").EnumerateArray())
        {
            var track = new NoteTrack
            {
                Id = jt.GetProperty("id").GetString(),
                Cls = jt.GetProperty("cls").GetString(),
                Level = jt.TryGetProperty("level", out JsonElement lv) ? lv.GetInt32() : -1,
            };
            track.Chapter = jt.TryGetProperty("chapter", out JsonElement ch) ? ch.GetString() : track.Id;
            foreach (JsonElement je in jt.GetProperty("entries").EnumerateArray())
            {
                var gate = new List<int>();
                if (je.TryGetProperty("gate", out JsonElement g)) foreach (JsonElement x in g.EnumerateArray()) gate.Add(x.GetInt32());
                string mark = je.TryGetProperty("mark", out JsonElement m) && m.ValueKind == JsonValueKind.String ? m.GetString() : null;
                var entry = new NoteEntry { Key = je.GetProperty("key").GetString(), Gate = gate.ToArray(), Mark = mark, Track = track, Index = track.Entries.Count };
                track.Entries.Add(entry);
                cat.ByKey[entry.Key] = entry;
            }
            cat.Tracks.Add(track);
            cat.ById[track.Id] = track;
            switch (track.Cls)
            {
                case "common" when track.Id == "main": cat.Main = track; break;
                case "common" when track.Level >= 0: cat.commonByLevel[track.Level] = track; break;
                case "rare" when track.Level >= 0: cat.rareByLevel[track.Level] = track; break;
                case "rare": cat.RareAny = track; break;
                case "scrap": cat.Scraps = track; break;
            }
        }
        return cat;
    }

    /// <summary>The tracks shown in one journal chapter.</summary>
    public IEnumerable<NoteTrack> InChapter(string chapter)
    {
        foreach (NoteTrack t in Tracks) if (t.Chapter == chapter) yield return t;
    }

    /// <summary>How many entries a chapter holds in all (its heading's "n / total").</summary>
    public int ChapterTotal(string chapter)
    {
        int n = 0;
        foreach (NoteTrack t in InChapter(chapter)) if (t.Cls != "special") n += t.Entries.Count;
        return n;
    }
}
