using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Notes;

/// <summary>The client side: this player's log, the reading dialog, the journal on J, and the links in them.</summary>
public partial class NoteSystem
{
    private ICoreClientAPI capi;
    private IClientNetworkChannel clientChannel;
    private GuiDialogNote noteDialog;
    private GuiDialogBackroomsJournal journalDialog;
    private int noteDialogId, noteDialogMarks;

    /// <summary>This player's notes, as the server last sent them.</summary>
    public NoteLog Own { get; private set; } = new();

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        LoadCatalog();
        clientChannel = api.Network.GetChannel(Channel);
        clientChannel.SetMessageHandler<NoteLogPacket>(p =>
        {
            Own = NoteLog.FromJson(p.Json);
            if (journalDialog?.IsOpened() == true) journalDialog.Recompose();
            // The note still open has had its marks found meanwhile (they come a moment after the text): show them
            if (noteDialog?.IsOpened() == true && Own.Find(noteDialogId) is { } shown && shown.Marks.Count != noteDialogMarks) ShowNote(shown);
        });
        clientChannel.SetMessageHandler<ShowNotePacket>(OnShowNote);
        api.RegisterLinkProtocol("backroomsnote", OnLink);
        api.ChatCommands.Create("journal").WithDescription("Opens your wanderer's journal").HandleWith(_ => { ToggleJournal(); return TextCommandResult.Success(); });
        api.Event.LevelFinalize += () =>
        {
            if (!BackroomsWorld.IsBackroomsClimate(api.World.Config)) return;
            // J opens the Backrooms journal instead of vanilla's (which has nothing to show in these worlds)
            if (api.Input.HotKeys.ContainsKey("journal")) api.Input.SetHotKeyHandler("journal", _ => { ToggleJournal(); return true; });
            else
            {
                api.Input.RegisterHotKey("backroomsjournal", Lang.Get("backrooms:journal-hotkey"), GlKeys.J, HotkeyType.GUIOrOtherControls);
                api.Input.SetHotKeyHandler("backroomsjournal", _ => { ToggleJournal(); return true; });
            }
        };
    }

    public void ToggleJournal()
    {
        if (capi == null || Catalog == null) return;
        if (journalDialog?.IsOpened() == true) { journalDialog.TryClose(); return; }
        journalDialog ??= new GuiDialogBackroomsJournal(capi, this);
        journalDialog.TryOpen();
    }

    private void OnShowNote(ShowNotePacket packet)
    {
        if (Own.Find(packet.Id) is { } read) ShowNote(read);
    }

    private void ShowNote(NoteRead read)
    {
        noteDialog?.TryClose();
        noteDialog = new GuiDialogNote(capi, this, read);
        noteDialogId = read.Id;
        noteDialogMarks = read.Marks.Count;
        noteDialog.TryOpen();
    }

    /// <summary>backroomsnote://map/x/z opens the map there; backroomsnote://mark/id/mark marks it again.</summary>
    private void OnLink(LinkTextComponent link)
    {
        string[] parts = link.Href.Substring("backroomsnote://".Length).Split('/');
        if (parts.Length >= 3 && parts[0] == "map" && int.TryParse(parts[1], out int x) && int.TryParse(parts[2], out int z))
        {
            var maps = capi.ModLoader.GetModSystem<WorldMapManager>();
            if (maps == null) return;
            if (maps.worldMapDlg?.IsOpened() != true) maps.ToggleMap(EnumDialogType.Dialog);
            int y = (int)(capi.World.Player?.Entity?.Pos.Y ?? 0);
            (maps.worldMapDlg?.SingleComposer?.GetElement("mapElem") as GuiElementMap)?.CenterMapTo(new BlockPos(x, y, z));
        }
        else if (parts.Length >= 3 && parts[0] == "mark" && int.TryParse(parts[1], out int id) && int.TryParse(parts[2], out int m))
            clientChannel.SendPacket(new MarkAgainPacket { Id = id, Mark = m });
    }

    // ================= How a read note is shown =================

    /// <summary>A level as the journal names it: "Level 3", "Level 6.1", "The End".</summary>
    public static string LevelName(int key)
    {
        if (key == NoteCatalog.SnackroomsKey) return Lang.Get("backrooms:levelname-6.1");
        if (key >= WorldLayout.RunLevel && key <= WorldLayout.Level188) return Lang.Get("backrooms:levelname-" + key);
        return Lang.Get("backrooms:levelname", WorldLayout.DisplayNumber(key));
    }

    /// <summary>One read note as rich text: number and title, where and when, the text, and its marks with their links.</summary>
    public string NoteVtml(NoteRead read, int number)
    {
        var sb = new StringBuilder();
        double perDay = capi.World.Calendar.HoursPerDay;
        int day = (int)(read.Hours / perDay) + 1;
        double hourOfDay = read.Hours % perDay;
        string when = Lang.Get("backrooms:journal-read-at", LevelName(read.Level), day, (int)hourOfDay, (int)((hourOfDay % 1) * 60));
        if (read.Key != null)
        {
            sb.Append("<font size=\"18\" weight=\"bold\">").Append(number > 0 ? number + ". " : "").Append(Lang.Get("backrooms:notetitle-" + read.Key)).Append("</font><br>");
            sb.Append("<font color=\"#a89f86\">").Append(when).Append("</font><br><br>");
            sb.Append(Lang.Get("backrooms:note-" + read.Key)).Append("<br>");
        }
        else sb.Append("<font color=\"#a89f86\">").Append(when).Append("</font><br>");
        for (int m = 0; m < read.Marks.Count; m++)
        {
            NoteMark mark = read.Marks[m];
            sb.Append("<br><i>").Append(Lang.Get("backrooms:journal-pocket")).Append("</i> ")
              .Append(Lang.Get(mark.Ps, Lang.Get("backrooms:dir-" + mark.Dir), mark.Paces)).Append("<br>");
            sb.Append("<font color=\"#e8d68c\">").Append(Lang.Get("backrooms:journal-marked", mark.Title)).Append("</font> ")
              .Append($"<a href=\"backroomsnote://map/{mark.X}/{mark.Z}\">").Append(Lang.Get("backrooms:journal-showmap")).Append("</a> · ")
              .Append($"<a href=\"backroomsnote://mark/{read.Id}/{m}\">").Append(Lang.Get("backrooms:journal-markagain")).Append("</a><br>");
        }
        return sb.ToString();
    }

    /// <summary>The journal's chapters that have something in them, in their order: the main series, the levels, folded notes, scraps, directions.</summary>
    public List<(string Chapter, int Read, int Total)> Chapters()
    {
        var result = new List<(string, int, int)>();
        if (Catalog == null) return result;
        var order = new List<string>();
        void Add(string ch) { if (ch != null && !order.Contains(ch)) order.Add(ch); }
        Add("main");
        foreach (NoteTrack t in Catalog.Tracks.Where(t => t.Cls is "common" or "special" && t.Level >= 0).OrderBy(t => ChapterOrder(t.Level))) Add(t.Chapter);
        Add(Catalog.RareChapter);
        Add("scraps");
        foreach (string ch in order)
        {
            int read = Catalog.InChapter(ch).Sum(t => t.Entries.Count(e => Own.Has(e.Key)));
            if (read > 0) result.Add((ch, read, Catalog.ChapterTotal(ch)));
        }
        if (Own.Directions.Count > 0) result.Add(("dir", Own.Directions.Count, 0));
        return result;
    }

    /// <summary>Levels in the journal's order: 0 to 11 with 6.1 after 6, then 37, 94 and the rest by id.</summary>
    private static double ChapterOrder(int level) => level == NoteCatalog.SnackroomsKey ? 6.5 : level;

    /// <summary>A chapter's notes, as rich text: in track order (which is also the order they were read).</summary>
    public string ChapterVtml(string chapter)
    {
        if (chapter == "dir")
        {
            var sb = new StringBuilder();
            for (int i = Own.Directions.Count - 1; i >= 0; i--) sb.Append(NoteVtml(Own.Directions[i], 0)).Append("<br>");
            return sb.Length == 0 ? Lang.Get("backrooms:journal-empty") : sb.ToString();
        }
        var parts = new StringBuilder();
        var tracks = Catalog.InChapter(chapter).ToList();
        // Read order within the chapter (for the rare chapter, the order found; for a level, its track order)
        int number = 0;
        for (int i = 0; i < Own.Read.Count; i++)
        {
            NoteRead r = Own.Read[i];
            NoteEntry e = Catalog.Entry(r.Key);
            if (e == null || !tracks.Contains(e.Track)) continue;
            number++;
            if (parts.Length > 0) parts.Append("<br><font color=\"#6b6455\">———</font><br><br>");
            parts.Append(NoteVtml(r, e.Track.Cls == "special" ? 0 : number));
        }
        return parts.Length == 0 ? Lang.Get("backrooms:journal-empty") : parts.ToString();
    }
}
