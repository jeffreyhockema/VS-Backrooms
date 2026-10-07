using System;
using System.Linq;
using Vintagestory.API.Client;
using Vintagestory.API.Config;
using Backrooms.Entities;

namespace Backrooms.Cheats;

/// <summary>
/// The cheat menu. Most buttons send <c>/backrooms</c> debug commands (and a few vanilla ones) as chat commands, so
/// the server decides whether the player may use them and the replies show in chat; the View tab's act on this
/// client only.
/// </summary>
public class GuiDialogCheats : GuiDialog
{
    private const double Width = 600, ButtonHeight = 26, Gap = 6, RowGap = 10;

    private static readonly string[] Tabs = { "Travel", "Creatures", "Events", "Player", "View" };
    private static readonly string[] LevelNumbers = { "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "37", "94" };
    private static readonly string[] EncounterKinds = { "hunt", "stalk", "glimpse", "ambient" };
    private static readonly string[] Distances = { "auto", "4", "8", "14", "24", "40" };

    private static readonly string[] CreatureCodes = Roster.AllCodes.Append("backrooms:wanderer-male").ToArray();

    private readonly CheatSystem cheats;
    private int tab;
    private string creature = CreatureCodes[0];
    private string encounter = EncounterKinds[0];
    private string distance = Distances[0];
    private string findLevel = "";

    public GuiDialogCheats(ICoreClientAPI capi, CheatSystem cheats) : base(capi)
    {
        this.cheats = cheats;
    }

    public override string ToggleKeyCombinationCode => CheatSystem.HotkeyCode;

    public override void OnGuiOpened()
    {
        Compose();
        base.OnGuiOpened();
    }

    private void Compose()
    {
        ElementBounds dialogBounds = ElementStdBounds.AutosizedMainDialog.WithAlignment(EnumDialogArea.RightMiddle)
            .WithFixedAlignmentOffset(-GuiStyle.DialogToScreenPadding, 0);
        ElementBounds bgBounds = ElementBounds.Fill.WithFixedPadding(GuiStyle.ElementToDialogPadding);
        bgBounds.BothSizing = ElementSizing.FitToChildren;
        // (The tabs sit on top of the dialog, like the character dialog's)
        ElementBounds tabBounds = ElementBounds.Fixed(0, -24, Width, 24);
        GuiTab[] tabs = Tabs.Select((name, i) => new GuiTab { Name = name, DataInt = i, Active = i == tab }).ToArray();

        GuiComposer composer = capi.Gui.CreateCompo("backrooms-cheats", dialogBounds)
            .AddShadedDialogBG(bgBounds)
            .AddDialogTitleBar("Backrooms cheats", () => TryClose())
            .AddHorizontalTabs(tabs, tabBounds, OnTabClicked, CairoFont.WhiteSmallText(), CairoFont.WhiteSmallText().WithColor(GuiStyle.ActiveButtonTextColor), "tabs")
            .BeginChildElements(bgBounds);

        double y = GuiStyle.TitleBarHeight + 4;
        switch (tab)
        {
            case 0: y = ComposeTravel(composer, y); break;
            case 1: y = ComposeCreatures(composer, y); break;
            case 2: y = ComposeEvents(composer, y); break;
            case 3: y = ComposePlayer(composer, y); break;
            default: y = ComposeView(composer, y); break;
        }
        composer.AddStaticText("Replies show in chat. Needs the controlserver privilege. F7 or .cheats toggles this menu.",
            CairoFont.WhiteDetailText(), ElementBounds.Fixed(0, y + 6, Width, 20));

        composer.EndChildElements();
        composer.GetHorizontalTabs("tabs").activeElement = tab;
        SingleComposer = composer.Compose();
    }

    // ================= Tabs =================

    private double ComposeTravel(GuiComposer c, double y)
    {
        y = Heading(c, "Go to a level", y);
        y = ButtonGrid(c, y, LevelNumbers.Select(n => ("Level " + n, Cmd($"/backrooms goto {n}"))).ToArray(), 7);

        y = Heading(c, "Go beside a feature", y + RowGap);
        c.AddStaticText("in level", CairoFont.WhiteSmallText(), ElementBounds.Fixed(0, y + 4, 70, ButtonHeight));
        string[] levelValues = LevelNumbers.Prepend("").ToArray();
        string[] levelNames = LevelNumbers.Select(n => "Level " + n).Prepend("its usual level").ToArray();
        c.AddDropDown(levelValues, levelNames, Math.Max(0, Array.IndexOf(levelValues, findLevel)), (code, _) => findLevel = code,
            ElementBounds.Fixed(70, y, 180, ButtonHeight), "findlevel");
        y += ButtonHeight + Gap;
        y = ButtonGrid(c, y, CheatSystem.Features.Select(f => (f.Name, (Action)(() => Send($"/backrooms find {f.Code}" + (findLevel != "" ? " " + findLevel : ""))))).ToArray(), 3);

        y = Heading(c, "Nearest from here (in this level)", y + RowGap);
        y = ButtonGrid(c, y, CheatSystem.Targets.Select(t => (t.Name, Cmd($"/backrooms nearest {t.Code}"))).ToArray(), 3);

        y = Heading(c, "Other", y + RowGap);
        return ButtonGrid(c, y, new[]
        {
            ("Wake-up point", Cmd("/backrooms home")),
            ("Where am I?", Cmd("/backrooms where")),
        }, 3);
    }

    private double ComposeCreatures(GuiComposer c, double y)
    {
        y = Heading(c, "Spawn a creature", y);
        string[] names = CreatureCodes.Select(code => Lang.Get("backrooms:item-creature-" + code.Split(':')[1])).ToArray();
        c.AddStaticText("Creature", CairoFont.WhiteSmallText(), ElementBounds.Fixed(0, y + 4, 90, ButtonHeight))
            .AddDropDown(CreatureCodes, names, Math.Max(0, Array.IndexOf(CreatureCodes, creature)), (code, _) => creature = code,
                ElementBounds.Fixed(90, y, 220, ButtonHeight), "creature");
        y += ButtonHeight + Gap;
        c.AddStaticText("Encounter", CairoFont.WhiteSmallText(), ElementBounds.Fixed(0, y + 4, 90, ButtonHeight))
            .AddDropDown(EncounterKinds, EncounterKinds, Math.Max(0, Array.IndexOf(EncounterKinds, encounter)), (code, _) => encounter = code,
                ElementBounds.Fixed(90, y, 220, ButtonHeight), "encounter");
        y += ButtonHeight + Gap;
        c.AddStaticText("Distance", CairoFont.WhiteSmallText(), ElementBounds.Fixed(0, y + 4, 90, ButtonHeight))
            .AddDropDown(Distances, Distances.Select(d => d == "auto" ? "auto (as the director would)" : d + " blocks").ToArray(),
                Math.Max(0, Array.IndexOf(Distances, distance)), (code, _) => distance = code, ElementBounds.Fixed(90, y, 220, ButtonHeight), "distance");
        c.AddSmallButton("Spawn", () => Send(SpawnCommand()), ElementBounds.Fixed(330, y, 120, ButtonHeight));
        y += ButtonHeight + Gap;
        c.AddStaticText("Smilers need the dark, the Thing needs deep water; auto picks a fitting spot or fails.",
            CairoFont.WhiteDetailText(), ElementBounds.Fixed(0, y, Width, 18));
        y += 18 + Gap;

        y = Heading(c, "Director", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            ("Pause director", Cmd("/backrooms director off")),
            ("Resume director", Cmd("/backrooms director on")),
            ("Menace readout", Cmd("/backrooms menace")),
            ("Make noise", Cmd("/backrooms noise")),
        }, 4);

        y = Heading(c, "Manage", y + RowGap);
        return ButtonGrid(c, y, new[]
        {
            ("Clear nearby (64)", Cmd("/backrooms clear 64")),
            ("Clear all (512)", Cmd("/backrooms clear 512")),
            ("Entity log on/off", Cmd("/backrooms entitylog")),
        }, 4);
    }

    private double ComposeEvents(GuiComposer c, double y)
    {
        y = Heading(c, "Reality Shift", y);
        y = ButtonGrid(c, y, new[]
        {
            ("Start (2 h)", Cmd("/backrooms shift 2")),
            ("Start (8 h)", Cmd("/backrooms shift 8")),
            ("End", Cmd("/backrooms shift 0")),
        }, 4);

        y = Heading(c, "Entity events", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            ("L1 Flickering", Cmd("/backrooms flicker")),
            ("Rats' Screaming", Cmd("/backrooms scream")),
            ("Mangled's weather", Cmd("/backrooms mangled")),
        }, 3);

        y = Heading(c, "Time", y + RowGap);
        return ButtonGrid(c, y, new[]
        {
            ("Morning", Cmd("/time set morning")),
            ("Day", Cmd("/time set day")),
            ("Night", Cmd("/time set night")),
            ("Midnight", Cmd("/time set midnight")),
            ("+1 hour", Cmd("/time add 1 hour")),
            ("+1 day", Cmd("/time add 1 day")),
            ("Stop time", Cmd("/time stop")),
            ("Resume time", Cmd("/time resume")),
        }, 4);
    }

    private double ComposePlayer(GuiComposer c, double y)
    {
        y = Heading(c, "Game mode", y);
        y = ButtonGrid(c, y, new[]
        {
            ("Survival", Cmd("/gm survival")),
            ("Creative", Cmd("/gm creative")),
            ("Spectator", Cmd("/gm spectator")),
        }, 4);

        y = Heading(c, "Survival", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            ("Heal and rest", Cmd("/backrooms heal")),
            ("Testing kit", Cmd("/backrooms kit")),
            ("Die (test waking)", Cmd("/backrooms die")),
            ("Column info", Cmd("/backrooms column")),
        }, 4);

        y = Heading(c, "Set your state", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            ("Health 10%", Cmd("/backrooms stat health 0.1")),
            ("Food 5%", Cmd("/backrooms stat food 0.05")),
            ("Stability 0", Cmd("/backrooms stat stability 0")),
            ("Stability 0.4", Cmd("/backrooms stat stability 0.4")),
        }, 4);

        y = Heading(c, "Time out (raises menace until you rest)", y + RowGap);
        return ButtonGrid(c, y, new[]
        {
            ("Rested", Cmd("/backrooms exposure 0")),
            ("Out 6 h", Cmd("/backrooms exposure 6")),
            ("Out 24 h", Cmd("/backrooms exposure 24")),
            ("Out 72 h", Cmd("/backrooms exposure 72")),
        }, 4);
    }

    private double ComposeView(GuiComposer c, double y)
    {
        y = Heading(c, "This client only", y);
        y = ButtonGrid(c, y, new (string, Action)[]
        {
            ("Debug HUD on/off", cheats.ToggleHud),
            ("Fog off/on", cheats.ToggleClearAir),
            ("Reveal map (loaded)", () => cheats.RevealMap(256)),
        }, 3);
        c.AddStaticText("The HUD reads the layout under your feet: level, depth through it, cell, tile, zone, dens, stability.",
            CairoFont.WhiteDetailText(), ElementBounds.Fixed(0, y, Width, 18));
        return y + 18 + Gap;
    }

    // ================= Helpers =================

    private static double Heading(GuiComposer c, string text, double y)
    {
        c.AddStaticText(text, CairoFont.WhiteSmallishText(), ElementBounds.Fixed(0, y, Width, 24));
        return y + 26;
    }

    /// <summary>Lays out buttons, <paramref name="columns"/> to a row; returns the y below them.</summary>
    private static double ButtonGrid(GuiComposer c, double y, (string Label, Action OnClick)[] buttons, int columns)
    {
        double width = (Width - Gap * (columns - 1)) / columns;
        for (int i = 0; i < buttons.Length; i++)
        {
            Action onClick = buttons[i].OnClick;
            double x = i % columns * (width + Gap), top = y + i / columns * (ButtonHeight + Gap);
            c.AddSmallButton(buttons[i].Label, () =>
            {
                onClick();
                return true;
            }, ElementBounds.Fixed(x, top, width, ButtonHeight));
        }
        int rows = (buttons.Length + columns - 1) / columns;
        return y + rows * (ButtonHeight + Gap);
    }

    private Action Cmd(string command) => () => Send(command);

    private string SpawnCommand()
    {
        string code = creature.Split(':')[1];
        // (The encounter command takes x and z before the distance; a player's own position is used whatever they are)
        return distance == "auto" ? $"/backrooms encounter {code} {encounter}" : $"/backrooms encounter {code} {encounter} 0 0 {distance}";
    }

    private bool Send(string command)
    {
        capi.SendChatMessage(command);
        return true;
    }

    private void OnTabClicked(int index)
    {
        tab = index;
        Compose();
    }
}
