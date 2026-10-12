using System;
using Vintagestory.API.Client;
using Vintagestory.API.Config;

namespace Backrooms.Notes;

/// <summary>
/// The note just read: its text and marks, with a way into the journal. A new one is made for every note shown, so it
/// leaves the game's list of dialogs when closed (else every note read would stay loaded for the rest of the session).
/// </summary>
public class GuiDialogNote : GuiDialog
{
    private const double Width = 440, TextHeight = 300;

    public override string ToggleKeyCombinationCode => null;

    public override bool UnregisterOnClose => true;

    public GuiDialogNote(ICoreClientAPI capi, NoteSystem notes, NoteRead read) : base(capi)
    {
        string vtml = notes.NoteVtml(read, 0);
        ElementBounds textBounds = ElementBounds.Fixed(0, GuiStyle.TitleBarHeight + 4, Width, TextHeight);
        ElementBounds clipBounds = textBounds.ForkBoundingParent();
        ElementBounds scrollBounds = clipBounds.CopyOffsetedSibling(Width + 4, 0).WithFixedWidth(16);
        ElementBounds closeBounds = ElementBounds.Fixed(0, GuiStyle.TitleBarHeight + TextHeight + 16, 130, 26);
        ElementBounds journalBounds = ElementBounds.Fixed(Width - 130, GuiStyle.TitleBarHeight + TextHeight + 16, 130, 26);
        ElementBounds bg = ElementBounds.Fill.WithFixedPadding(GuiStyle.ElementToDialogPadding);
        bg.BothSizing = ElementSizing.FitToChildren;
        bg.WithChildren(clipBounds, scrollBounds, closeBounds, journalBounds);
        ElementBounds dialog = ElementStdBounds.AutosizedMainDialog.WithAlignment(EnumDialogArea.CenterMiddle);

        SingleComposer = capi.Gui.CreateCompo("backrooms-note", dialog)
            .AddShadedDialogBG(bg)
            .AddDialogTitleBar(Lang.Get("backrooms:note-dialog-title"), () => TryClose())
            .BeginChildElements(bg)
                .BeginClip(clipBounds)
                    .AddRichtext(vtml, CairoFont.WhiteSmallText().WithLineHeightMultiplier(1.15), textBounds, "text")
                .EndClip()
                .AddVerticalScrollbar(OnScroll, scrollBounds, "scroll")
                .AddSmallButton(Lang.Get("backrooms:note-dialog-close"), () => TryClose(), closeBounds)
                .AddSmallButton(Lang.Get("backrooms:note-dialog-journal"), () => { TryClose(); notes.ToggleJournal(); return true; }, journalBounds)
            .EndChildElements()
            .Compose();
        GuiElementRichtext text = SingleComposer.GetRichtext("text");
        text.BeforeCalcBounds();
        SingleComposer.GetScrollbar("scroll").SetHeights((float)TextHeight, (float)Math.Max(TextHeight, text.Bounds.fixedHeight));
    }

    private void OnScroll(float value)
    {
        GuiElementRichtext text = SingleComposer.GetRichtext("text");
        text.Bounds.fixedY = -value;
        text.Bounds.CalcWorldBounds();
    }
}

/// <summary>
/// The wanderer's journal (J): every note this player has read, by chapter (the main series, each level, folded notes,
/// scraps, directions), each with where and when it was read and its marks (show on map, mark again).
/// </summary>
public class GuiDialogBackroomsJournal : GuiDialog
{
    private const double ListWidth = 230, PageWidth = 560, Height = 520, Row = 26;
    private readonly NoteSystem notes;
    private string chapter;

    public override string ToggleKeyCombinationCode => null;

    public GuiDialogBackroomsJournal(ICoreClientAPI capi, NoteSystem notes) : base(capi)
    {
        this.notes = notes;
    }

    public override void OnGuiOpened()
    {
        Recompose();
        base.OnGuiOpened();
    }

    public void Recompose()
    {
        var chapters = notes.Chapters();
        if (chapter == null || !chapters.Exists(c => c.Chapter == chapter)) chapter = chapters.Count > 0 ? chapters[0].Chapter : null;

        double top = GuiStyle.TitleBarHeight + 4;
        double listHeight = Math.Max(Height, chapters.Count * Row + 8);
        ElementBounds listBounds = ElementBounds.Fixed(0, top, ListWidth, listHeight);
        ElementBounds pageBounds = ElementBounds.Fixed(ListWidth + 14, top + 4, PageWidth, listHeight - 8);
        ElementBounds clipBounds = pageBounds.ForkBoundingParent();
        ElementBounds insetBounds = clipBounds.FlatCopy().FixedGrow(8).WithFixedOffset(-4, -4);
        ElementBounds scrollBounds = insetBounds.CopyOffsetedSibling(insetBounds.fixedWidth + 4, 0).WithFixedWidth(16);
        ElementBounds bg = ElementBounds.Fill.WithFixedPadding(GuiStyle.ElementToDialogPadding);
        bg.BothSizing = ElementSizing.FitToChildren;
        bg.WithChildren(listBounds, insetBounds, scrollBounds);
        ElementBounds dialog = ElementStdBounds.AutosizedMainDialog.WithAlignment(EnumDialogArea.CenterMiddle);

        GuiComposer c = capi.Gui.CreateCompo("backrooms-journal", dialog)
            .AddShadedDialogBG(bg)
            .AddDialogTitleBar(Lang.Get("backrooms:journal-title"), () => TryClose())
            .BeginChildElements(bg);
        for (int i = 0; i < chapters.Count; i++)
        {
            var (ch, read, total) = chapters[i];
            string label = Lang.Get("backrooms:journal-track-" + ch) + (ch == "dir" ? $"  ({read})" : "  " + Lang.Get("backrooms:journal-count", read, total));
            string code = ch;
            CairoFont font = CairoFont.WhiteSmallText();
            if (ch == chapter) font = font.Clone().WithColor(GuiStyle.ActiveButtonTextColor);
            c.AddButton(label, () => { chapter = code; Recompose(); return true; }, ElementBounds.Fixed(0, top + i * Row, ListWidth, Row - 2), font, EnumButtonStyle.Small, "ch" + i);
        }
        string vtml = chapter == null ? Lang.Get("backrooms:journal-empty") : notes.ChapterVtml(chapter);
        c.AddInset(insetBounds, 3, 0.85f)
            .BeginClip(clipBounds)
                .AddRichtext(vtml, CairoFont.WhiteSmallText().WithLineHeightMultiplier(1.15), pageBounds, "page")
            .EndClip()
            .AddVerticalScrollbar(OnScroll, scrollBounds, "scroll")
            .EndChildElements();
        SingleComposer = c.Compose();
        GuiElementRichtext page = SingleComposer.GetRichtext("page");
        page.BeforeCalcBounds();
        SingleComposer.GetScrollbar("scroll").SetHeights((float)clipBounds.fixedHeight, (float)Math.Max(clipBounds.fixedHeight, page.Bounds.fixedHeight));
    }

    private void OnScroll(float value)
    {
        GuiElementRichtext page = SingleComposer.GetRichtext("page");
        page.Bounds.fixedY = -value;
        page.Bounds.CalcWorldBounds();
    }
}
