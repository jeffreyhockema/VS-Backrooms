using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Backrooms.Notes;

/// <summary>A place a note marked on the map, kept so the journal can show it again and mark it again.</summary>
public sealed class NoteMark
{
    public int X, Z, Level;
    /// <summary>The waypoint's title (as it was put on the map).</summary>
    public string Title;
    public string Icon;
    /// <summary>The pencilled postscript's lang key (note-door-2 …), the direction code (n, ne …) and the paces from where it was read.</summary>
    public string Ps, Dir;
    public int Paces;
}

/// <summary>One note a player has read.</summary>
public sealed class NoteRead
{
    /// <summary>Its number in its player's log, never reused (the journal's links name it, so trimming the directions moves nothing).</summary>
    public int Id;
    /// <summary>The entry it was (null for a plain directions note).</summary>
    public string Key, Track;
    /// <summary>Where it was read: level key (61 for Level 6.1), position, calendar hours.</summary>
    public int Level, X, Z;
    public double Hours;
    /// <summary>The paper: door, way, cache, refuge, folded or altered.</summary>
    public string Kind;
    public List<NoteMark> Marks = new();
}

/// <summary>Everything one player has read, in order: their journal, and their place in every sequence.</summary>
public sealed class NoteLog
{
    public const int DirectionsKept = 40;

    public List<NoteRead> Read = new();
    public List<NoteRead> Directions = new();
    /// <summary>"main" or "level": which kind of common note came last (they alternate).</summary>
    public string LastPick;
    public bool PocketGiven;
    /// <summary>The next <see cref="NoteRead.Id"/> to give.</summary>
    public int NextId = 1;

    private HashSet<string> keys;

    public bool Has(string key)
    {
        if (keys == null)
        {
            keys = new HashSet<string>();
            foreach (NoteRead r in Read) if (r.Key != null) keys.Add(r.Key);
        }
        return keys.Contains(key);
    }

    public int CountIn(NoteTrack track)
    {
        int n = 0;
        if (track != null) foreach (NoteEntry e in track.Entries) if (Has(e.Key)) n++;
        return n;
    }

    /// <summary>A read note by its id (in the reads or the directions), or null.</summary>
    public NoteRead Find(int id)
    {
        if (id <= 0) return null;
        foreach (NoteRead r in Read) if (r.Id == id) return r;
        foreach (NoteRead r in Directions) if (r.Id == id) return r;
        return null;
    }

    /// <summary>Gives every read note an id (logs saved before there were ids).</summary>
    public NoteLog EnsureIds()
    {
        foreach (NoteRead r in Read) NextId = Math.Max(NextId, r.Id + 1);
        foreach (NoteRead r in Directions) NextId = Math.Max(NextId, r.Id + 1);
        foreach (NoteRead r in Read) if (r.Id <= 0) r.Id = NextId++;
        foreach (NoteRead r in Directions) if (r.Id <= 0) r.Id = NextId++;
        return this;
    }

    public void Add(NoteRead read, string pick)
    {
        if (read.Id <= 0) read.Id = NextId++;
        if (read.Key == null)
        {
            Directions.Add(read);
            if (Directions.Count > DirectionsKept) Directions.RemoveAt(0);
            return;
        }
        Read.Add(read);
        Has(read.Key);
        keys.Add(read.Key);
        if (pick != null) LastPick = pick;
    }

    private static readonly JsonSerializerOptions Json = new() { IncludeFields = true, DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull };

    public string ToJson() => JsonSerializer.Serialize(this, Json);

    public static NoteLog FromJson(string json) => string.IsNullOrEmpty(json) ? new NoteLog() : (JsonSerializer.Deserialize<NoteLog>(json, Json) ?? new NoteLog()).EnsureIds();

    public static string SaveAll(Dictionary<string, NoteLog> logs) => JsonSerializer.Serialize(logs, Json);

    public static Dictionary<string, NoteLog> LoadAll(string json)
    {
        var logs = string.IsNullOrEmpty(json) ? new() : JsonSerializer.Deserialize<Dictionary<string, NoteLog>>(json, Json) ?? new();
        foreach (NoteLog log in logs.Values) log?.EnsureIds();
        return logs;
    }
}

/// <summary>What a note turned out to be when read.</summary>
public sealed class NoteResolution
{
    public NoteEntry Entry;
    /// <summary>"main" or "level" for a common note (for the alternation), else null.</summary>
    public string Pick;
    public NoteTrack Track => Entry?.Track;
}

/// <summary>
/// Decides what a note says when read (docs/notes-plan.md, section 3). Pure: no game dependencies, so the layout
/// harness simulates players with it.
/// <list type="bullet">
/// <item>A folded (rare) note: the next due entry of the rare track of the level it is read in, else of "rare-any",
/// else (every rare note read) an ordinary note.</item>
/// <item>An ordinary note: the first three are always main 1-3; then main and the level's own track alternate. An entry
/// whose gate is not met waits (the other track serves meanwhile); nothing is ever skipped.</item>
/// <item>Both waiting or done: the scraps, in order; then nothing (a plain directions note).</item>
/// </list>
/// </summary>
public static class NoteSequencer
{
    public const int OpeningPages = 3;

    /// <summary>The first entry of a track not yet read, if its gate is met (null if the track is done or waiting).</summary>
    public static NoteEntry Due(NoteTrack track, NoteLog log, Func<int, bool> visited)
    {
        if (track == null) return null;
        foreach (NoteEntry e in track.Entries)
        {
            if (log.Has(e.Key)) continue;
            return GateMet(e, visited) ? e : null;
        }
        return null;
    }

    public static bool GateMet(NoteEntry e, Func<int, bool> visited)
    {
        if (e.Gate.Length == 0) return true;
        foreach (int level in e.Gate) if (visited(level)) return true;
        return false;
    }

    public static NoteResolution Resolve(NoteCatalog cat, NoteLog log, int levelKey, bool rare, Func<int, bool> visited)
    {
        // Whatever the paper, the very first note anyone reads is main 1
        if (cat.Main?.Entries.Count > 0 && !log.Has(cat.Main.Entries[0].Key)) return new NoteResolution { Entry = cat.Main.Entries[0], Pick = "main" };
        if (rare)
        {
            NoteEntry r = Due(cat.RareFor(levelKey), log, visited) ?? Due(cat.RareAny, log, visited);
            if (r != null) return new NoteResolution { Entry = r };
        }
        NoteEntry m = Due(cat.Main, log, visited), t = Due(cat.CommonFor(levelKey), log, visited);
        if (m != null && (t == null || log.CountIn(cat.Main) < OpeningPages)) return new NoteResolution { Entry = m, Pick = "main" };
        if (t != null && m == null) return new NoteResolution { Entry = t, Pick = "level" };
        if (m != null) return log.LastPick == "main" ? new NoteResolution { Entry = t, Pick = "level" } : new NoteResolution { Entry = m, Pick = "main" };
        NoteEntry s = Due(cat.Scraps, log, visited);
        return s != null ? new NoteResolution { Entry = s } : null;
    }

    /// <summary>The next unread entry of a special track (the note someone altered), or null once read.</summary>
    public static NoteResolution ResolveSpecial(NoteCatalog cat, NoteLog log, string trackId)
    {
        if (!cat.ById.TryGetValue(trackId, out NoteTrack track)) return null;
        foreach (NoteEntry e in track.Entries) if (!log.Has(e.Key)) return new NoteResolution { Entry = e };
        return null;
    }
}
