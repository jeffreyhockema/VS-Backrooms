using System;
using System.Linq;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Backrooms.Entities;
using Backrooms.Map;
using Backrooms.Salvage;

namespace Backrooms.Cheats;

/// <summary>
/// The cheat menu. Most buttons send <c>/backrooms</c> debug commands (and a few vanilla ones) as chat commands, so
/// the server decides whether the player may use them and the replies show in chat; the View tab's, and restarting
/// the tutorial, act on this client only. A status line on every tab says where you are and how the world is set.
/// </summary>
public class GuiDialogCheats : GuiDialog
{
    private const double Width = 600, ButtonHeight = 26, Gap = 6, RowGap = 10, LineHeight = 18;

    private static readonly string[] Tabs = { "Travel", "Player", "Creatures", "World", "View", "Dev" };
    private static readonly string[] LevelNumbers = { "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "37", "94", "!", "Fun", "End", "Hub", "974", "3999", "188" };

    /// <summary>A level's name on a button: "Level 37", "Level !", but "The End" and "The Hub".</summary>
    private static string LevelLabel(string number) => number is "End" or "Hub" ? "The " + number : "Level " + number;
    private static readonly string[] EncounterKinds = { "hunt", "stalk", "glimpse", "ambient" };
    private static readonly string[] Distances = { "auto", "4", "8", "14", "24", "40" };

    private static readonly string[] CreatureCodes = Roster.AllCodes.Append("backrooms:wanderer-male").ToArray();

    /// <summary>The <c>nearest</c> targets that are camera spots (for the screenshots), for the Dev tab.</summary>
    private static readonly (string Code, string Name, int Radius, int MaxRadius)[] PhotoSpots =
        CheatSystem.Targets.Where(t => !CheatSystem.GameplayTargets.Contains(t.Code) && t.Code != "manhole").ToArray();

    /// <summary>The kinds of note <c>/backrooms note read</c> takes; <c>give</c> takes all but the last.</summary>
    private static readonly string[] NoteKinds = { "door", "way", "cache", "refuge", "folded", "altered" };

    /// <summary>The world settings the World tab can change, with their options (as in worldconfig.json).</summary>
    private static readonly (string Code, string Label, string[] Values)[] Settings =
    {
        ("backroomsMenace", "Entities", new[] { "off", "low", "normal", "high" }),
        (ScarcitySystem.ConfigKey, "Scarcity", new[] { "plentiful", "normal", "sparse", "scarce" }),
        (MapSetting.Code, "Map", new[] { "seen", "nowaypoints", "none" }),
    };

    private readonly CheatSystem cheats;
    // (The dialog lives as long as the session, so the tab and choices are still there when it is opened again)
    private int tab;
    private string creature = CreatureCodes[0];
    private string encounter = EncounterKinds[0];
    private string distance = Distances[0];
    private string findLevel = "";
    private string photoSpot = PhotoSpots[0].Code;
    private string noteKind = NoteKinds[0];
    private readonly string[] settingChoice = new string[Settings.Length];
    private long statusListener;

    public GuiDialogCheats(ICoreClientAPI capi, CheatSystem cheats) : base(capi)
    {
        this.cheats = cheats;
    }

    public override string ToggleKeyCombinationCode => CheatSystem.HotkeyCode;

    public override void OnGuiOpened()
    {
        Compose();
        base.OnGuiOpened();
        statusListener = capi.Event.RegisterGameTickListener(_ => SingleComposer?.GetDynamicText("status")?.SetNewText(cheats.StatusLine()), 500);
    }

    public override void OnGuiClosed()
    {
        base.OnGuiClosed();
        capi.Event.UnregisterGameTickListener(statusListener);
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
        composer.AddDynamicText(cheats.StatusLine(), CairoFont.WhiteDetailText(), ElementBounds.Fixed(0, y, Width, LineHeight), "status");
        y += LineHeight + 2;
        if (!cheats.Privileged)
        {
            y = Note(composer, "You lack the controlserver privilege: the server refuses these commands, and the view cheats are off.", y,
                CairoFont.WhiteDetailText().WithColor(GuiStyle.ErrorTextColor));
        }
        y += 4;
        switch (tab)
        {
            case 0: y = ComposeTravel(composer, y); break;
            case 1: y = ComposePlayer(composer, y); break;
            case 2: y = ComposeCreatures(composer, y); break;
            case 3: y = ComposeWorld(composer, y); break;
            case 4: y = ComposeView(composer, y); break;
            default: y = ComposeDev(composer, y); break;
        }
        composer.AddStaticText("Replies show in chat. F7 or .cheats toggles this menu.",
            CairoFont.WhiteDetailText(), ElementBounds.Fixed(0, y + 6, Width, 20));

        composer.EndChildElements();
        composer.GetHorizontalTabs("tabs").activeElement = tab;
        SingleComposer = composer.Compose();
    }

    // ================= Tabs =================

    private double ComposeTravel(GuiComposer c, double y)
    {
        y = Heading(c, "Go to a level", y);
        y = ButtonGrid(c, y, LevelNumbers.Select(n => B(LevelLabel(n), $"/backrooms goto {n}")).ToArray(), 7);

        y = Heading(c, "Go beside a feature", y + RowGap);
        c.AddStaticText("in level", CairoFont.WhiteSmallText(), ElementBounds.Fixed(0, y + 4, 70, ButtonHeight));
        string[] levelValues = LevelNumbers.Prepend("").ToArray();
        string[] levelNames = LevelNumbers.Select(LevelLabel).Prepend("its usual level").ToArray();
        c.AddDropDown(levelValues, levelNames, Math.Max(0, Array.IndexOf(levelValues, findLevel)), (code, _) => findLevel = code,
            ElementBounds.Fixed(70, y, 180, ButtonHeight), "findlevel");
        y += ButtonHeight + Gap;
        y = ButtonGrid(c, y, CheatSystem.Features.Select(f => new Button(f.Name, () => Send($"/backrooms find {f.Code}" + (findLevel != "" ? " " + findLevel : "")))).ToArray(), 3);

        y = Heading(c, "Nearest from here (in this level)", y + RowGap);
        y = ButtonGrid(c, y, CheatSystem.Targets.Where(t => CheatSystem.GameplayTargets.Contains(t.Code))
            .Select(t => B(t.Name, $"/backrooms nearest {t.Code}")).ToArray(), 3);

        y = Heading(c, "Other", y + RowGap);
        return ButtonGrid(c, y, new[]
        {
            B("Back", "/backrooms back", "Back to where you were before your last goto, find, nearest, home or back (this session only)"),
            B("Wake-up point", "/backrooms home"),
            B("Where am I?", "/backrooms where"),
        }, 3);
    }

    private double ComposePlayer(GuiComposer c, double y)
    {
        y = Heading(c, "Game mode", y);
        y = ButtonGrid(c, y, new[]
        {
            B("Survival", "/gm survival"),
            B("Creative", "/gm creative"),
            B("Spectator", "/gm spectator"),
        }, 3);

        y = Heading(c, "Survival", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Heal and rest", "/backrooms heal", "Health, food, body temperature and stability back to full, and your time out reset"),
            B("Die (test waking)", "/backrooms die"),
            B("Lantern in hand", "/backrooms light lantern", "A lit light in your active hotbar slot (only a light in hand lights Level 6)"),
            B("Torch in hand", "/backrooms light torch"),
        }, 4);

        y = Heading(c, "Set your state", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Health 10%", "/backrooms stat health 0.1"),
            B("Food 5%", "/backrooms stat food 0.05"),
            B("Stability 0", "/backrooms stat stability 0"),
            B("Stability 0.4", "/backrooms stat stability 0.4"),
        }, 4);

        y = Heading(c, "Time out (raises menace until you rest)", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Rested", "/backrooms exposure 0"),
            B("Out 6 h", "/backrooms exposure 6"),
            B("Out 24 h", "/backrooms exposure 24"),
            B("Out 72 h", "/backrooms exposure 72"),
        }, 4);

        y = Heading(c, "Kits", y + RowGap);
        return ButtonGrid(c, y, CheatSystem.Kits.Where(k => k.Code is "testing" or "explorer")
            .Select(k => B(k.Name, $"/backrooms kit {k.Code}", KitContents(k.Things))).ToArray(), 4);
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
        c.AddSmallButton("Perceive", () => Send(PerceiveCommand()), ElementBounds.Fixed(460, y, 120, ButtonHeight));
        y += ButtonHeight + Gap;
        y = Note(c, "Smilers need the dark, the Thing needs deep water; auto picks a fitting spot or fails. "
            + "Perceive puts the creature down that many blocks off (held still, 20 on auto) and reports each second what it sees, hears and believes of you.", y, lines: 3);

        y = Heading(c, "Director", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Pause director", "/backrooms director off", "Nothing new is put down near anyone and no distant sounds play; what is out stays"),
            B("Resume director", "/backrooms director on"),
            B("Make noise", "/backrooms noise", "As loud as you can be: what hunts by sound comes to see"),
            B("Stop probes", "/backrooms perceive stop", "Ends every perception probe (Perceive), and its reports"),
        }, 4);

        y = Heading(c, "Manage", y + RowGap);
        return ButtonGrid(c, y, new[]
        {
            B("Clear nearby (64)", "/backrooms clear 64"),
            B("Clear all (512)", "/backrooms clear 512"),
        }, 3);
    }

    private double ComposeWorld(GuiComposer c, double y)
    {
        y = Heading(c, "Reality Shift", y);
        y = ButtonGrid(c, y, new[]
        {
            B("Start (2 h)", "/backrooms shift 2"),
            B("Start (8 h)", "/backrooms shift 8"),
            B("End", "/backrooms shift 0"),
        }, 4);

        y = Heading(c, "Events", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("L1 Flickering", "/backrooms flicker", "The lights round you go out and Hounds hunt until they come back"),
            B("Rats' Screaming", "/backrooms scream", "The lights fail in Levels 1 and 2 and a pack of Death Rats runs past"),
            B("Mangled's weather", "/backrooms mangled", "Its cold weather comes down on you; in the Suburbs, it then comes"),
            B("L10 fog spell", "/backrooms fogspell", "Moves the calendar on to the thick of the next spell of fog over Level 10's fields"),
            B("L5 Beast", "/backrooms beast", "The Beast of Level 5 chooses you: the music stops, a drum, then he comes with his offer (anywhere)"),
        }, 4);

        y = Heading(c, "Time", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Morning", "/time set morning"),
            B("Day", "/time set day"),
            B("Night", "/time set night"),
            B("Midnight", "/time set midnight"),
            B("+1 hour", "/time add 1 hour"),
            B("+1 day", "/time add 1 day"),
            B("Stop time", "/time stop"),
            B("Resume time", "/time resume"),
        }, 4);

        y = Heading(c, "World settings", y + RowGap);
        ITreeAttribute config = capi.World.Config;
        for (int i = 0; i < Settings.Length; i++)
        {
            var (code, label, values) = Settings[i];
            string current = config?.GetString(code, "") is { Length: > 0 } set ? set : values[code == MapSetting.Code ? 0 : Array.IndexOf(values, "normal")];
            settingChoice[i] ??= current;
            int index = i;
            c.AddStaticText(label, CairoFont.WhiteSmallText(), ElementBounds.Fixed(0, y + 4, 90, ButtonHeight))
                .AddDropDown(values, values, Math.Max(0, Array.IndexOf(values, settingChoice[i])), (value, _) => settingChoice[index] = value,
                    ElementBounds.Fixed(90, y, 160, ButtonHeight), "setting-" + code)
                .AddSmallButton("Set", () => Send($"/worldconfig {code} {settingChoice[index]}"), ElementBounds.Fixed(260, y, 70, ButtonHeight))
                .AddStaticText("world: " + current, CairoFont.WhiteDetailText(), ElementBounds.Fixed(345, y + 5, Width - 345, ButtonHeight));
            y += ButtonHeight + Gap;
        }
        int version = config?.GetInt(BackroomsWorld.LayoutVersionKey, 1) ?? 1;
        string food = config?.HasAttribute(BackroomsWorld.WorldgenFoodKey) == true ? $"{config.GetFloat(BackroomsWorld.WorldgenFoodKey):0.##}"
            : version < 7 ? "1 (no thinning before layout version 7)" : "not recorded yet";
        int levelSize = config?.GetInt(BackroomsWorld.LayoutLevelSizeKey, 100) ?? 100;
        y = Note(c, $"Layout version {version}, worldgen food {food}, level size {levelSize}%: fixed when the world was made, never changed here.", y);
        return Note(c, "Set sends /worldconfig. It takes effect after a server restart (dispensers and Kitty's fridge follow scarcity at once). "
            + "Worldgen thinning keeps the recorded worldgen food, whatever the scarcity. This menu shows new values once you rejoin.", y, lines: 3);
    }

    private double ComposeView(GuiComposer c, double y)
    {
        y = Heading(c, "This client only", y);
        bool hasMap = MapSetting.HasMap(capi.World.Config);
        y = ButtonGrid(c, y, new[]
        {
            new Button("Debug HUD on/off", cheats.ToggleHud, "Level, depth through it, cell and tile under your feet, Level 0's zone, dens, sanctuaries, stability, temperature"),
            new Button("Fog off/on", cheats.ToggleClearAir, "No fog, and the scene at full brightness"),
            hasMap ? new Button("Reveal map (loaded)", () => cheats.RevealMap(256), "Maps every loaded column within 256 blocks") : default,
        }, 3);
        if (!hasMap) c.AddStaticText("Reveal map: no map in this world", CairoFont.WhiteDetailText().WithColor(GuiStyle.DialogDefaultTextColor),
            ElementBounds.Fixed(2 * ((Width - 2 * Gap) / 3 + Gap), y - ButtonHeight - Gap + 5, (Width - 2 * Gap) / 3, ButtonHeight));
        return Note(c, "The HUD reads the layout under your feet as this client works it out from the seed.", y);
    }

    private double ComposeDev(GuiComposer c, double y)
    {
        y = Heading(c, "Photo spots (nearest in this level)", y);
        c.AddDropDown(PhotoSpots.Select(t => t.Code).ToArray(), PhotoSpots.Select(t => t.Name).ToArray(),
            Math.Max(0, Array.FindIndex(PhotoSpots, t => t.Code == photoSpot)), (code, _) => photoSpot = code, ElementBounds.Fixed(0, y, 400, ButtonHeight), "photospot");
        c.AddSmallButton("Go", () => Send($"/backrooms nearest {photoSpot}"), ElementBounds.Fixed(410, y, 90, ButtonHeight));
        y += ButtonHeight + Gap;

        y = Heading(c, "Inspect here", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Column", "/backrooms column", "The block stack, block entities and light of the column you stand in"),
            new Button("Can break", () => SendHere("/backrooms canbreak {0} {1}"), "The tool tier each block of this column needs, and what it breaks down to"),
            new Button("Ground", () => SendHere("/backrooms ground {0} {1}"), "Rock, ore and caves under the foundations of this chunk, by depth"),
            new Button("Dump (32)", () => SendHere("/backrooms dump {0} {1} 32"), "Writes the blocks and light within 32 blocks to ModData/backrooms (run twice: the first loads the chunks)"),
            B("Where", "/backrooms where"),
        }, 5);

        y = Heading(c, "Systems", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Entity log on/off", "/backrooms entitylog", "What the director and the entities decide, to the server log"),
            B("Menace readout", "/backrooms menace"),
            B("End loop on", "/endloop on", "The End's looping long aisles and the Turnaround"),
            B("End loop off", "/endloop off"),
        }, 4);
        c.AddStaticText("Note", CairoFont.WhiteSmallText(), ElementBounds.Fixed(0, y + 4, 50, ButtonHeight))
            .AddDropDown(NoteKinds, NoteKinds, Math.Max(0, Array.IndexOf(NoteKinds, noteKind)), (kind, _) => noteKind = kind,
                ElementBounds.Fixed(50, y, 120, ButtonHeight), "notekind");
        double half = (Width - 180 - Gap) / 2;
        c.AddSmallButton("Read one here", () => Send($"/backrooms note read {noteKind}"), ElementBounds.Fixed(180, y, half, ButtonHeight))
            .AddSmallButton("Give 4", () => noteKind == "altered" ? Say("Level Fun's altered notes can be read here, not given") : Send($"/backrooms note give {noteKind} 4"),
                ElementBounds.Fixed(180 + half + Gap, y, half, ButtonHeight));
        y += ButtonHeight + Gap;
        y = ButtonGrid(c, y, new[]
        {
            B("Note status", "/backrooms note status", "Where you are in each sequence of notes (J opens the journal)"),
            new Button("Note log", () => Send($"/backrooms note log {capi.World.Player.PlayerName}"), "Every note you have read, in order"),
            B("Forget all notes", "/backrooms note reset", "Empties your journal, so the sequence starts again"),
        }, 3);

        y = Heading(c, "Perception tests", y + RowGap);
        y = ButtonGrid(c, y, new[]
        {
            B("Dummy here", "/backrooms dummy place here", "Puts a straw dummy down in front of you, to stand in for a player (the first try may only load the chunks: try again)"),
            B("Dummy: torch", "/backrooms dummy light 14", "The nearest straw dummy carries a torch"),
            B("Dummy: no light", "/backrooms dummy light 0", "The nearest straw dummy carries no light"),
            B("Dummy: sneak", "/backrooms dummy sneak", "Toggles whether the nearest straw dummy sneaks"),
            B("Dummy: run", "/backrooms dummy run", "Toggles whether the nearest straw dummy counts as running"),
            B("Dummy: unsteady", "/backrooms dummy stability 0.3", "Sets the nearest straw dummy's Reality Stability to 0.3"),
            B("Dummy: noise", "/backrooms dummy noise 0.5", "The nearest straw dummy makes a noise, at loudness 0.5, which the creatures can hear"),
            B("Remove dummies", "/backrooms dummy remove", "Removes every straw dummy put down for tests"),
        }, 4);

        y = Heading(c, "Feature tests", y + RowGap);
        var crucible = CheatSystem.Kits.First(k => k.Code == "crucible");
        var pottery = CheatSystem.Kits.First(k => k.Code == "pottery");
        return ButtonGrid(c, y, new[]
        {
            B("Crucible kit", "/backrooms kit crucible", KitContents(crucible.Things)),
            B("Pottery kit", "/backrooms kit pottery", KitContents(pottery.Things)),
            B("Every item (chests)", "/backrooms allitems", "One of every Backrooms item in chests round you, to set down and look at on the ground"),
            B("Manhole ladder", "/backrooms nearest manhole", "In Level 3: down the nearest manhole, at the foot of its rungs"),
            new Button("Restart First Steps", cheats.RestartTutorial, "Starts the Backrooms: First Steps tutorial again from its first step, on this client"),
        }, 3);
    }

    // ================= Helpers =================

    /// <summary>A button: its label, what it does, and the text shown while the mouse is over it (none if null).</summary>
    private readonly record struct Button(string Label, Action OnClick, string Hover = null);

    private Button B(string label, string command, string hover = null) => new(label, () => Send(command), hover);

    /// <summary>What a kit holds, by the names the game gives the things, for its button's hover text.</summary>
    private string KitContents((string Code, int Quantity)[] things) => string.Join(", ", things.Select(t =>
    {
        var location = new AssetLocation(t.Code);
        CollectibleObject thing = (CollectibleObject)capi.World.GetItem(location) ?? capi.World.GetBlock(location);
        return $"{t.Quantity} {(thing != null ? new ItemStack(thing).GetName() : location.Path)}";
    }));

    private static double Heading(GuiComposer c, string text, double y)
    {
        c.AddStaticText(text, CairoFont.WhiteSmallishText(), ElementBounds.Fixed(0, y, Width, 24));
        return y + 26;
    }

    private static double Note(GuiComposer c, string text, double y, CairoFont font = null, int lines = 1)
    {
        c.AddStaticText(text, font ?? CairoFont.WhiteDetailText(), ElementBounds.Fixed(0, y, Width, LineHeight * lines));
        return y + LineHeight * lines + Gap;
    }

    /// <summary>Lays out buttons, <paramref name="columns"/> to a row (a default one leaves its place empty); returns the y below them.</summary>
    private static double ButtonGrid(GuiComposer c, double y, Button[] buttons, int columns)
    {
        double width = (Width - Gap * (columns - 1)) / columns;
        for (int i = 0; i < buttons.Length; i++)
        {
            if (buttons[i].OnClick is not { } onClick) continue;
            double x = i % columns * (width + Gap), top = y + i / columns * (ButtonHeight + Gap);
            c.AddSmallButton(buttons[i].Label, () =>
            {
                onClick();
                return true;
            }, ElementBounds.Fixed(x, top, width, ButtonHeight));
            if (buttons[i].Hover != null) c.AddAutoSizeHoverText(buttons[i].Hover, CairoFont.WhiteDetailText(), 360, ElementBounds.Fixed(x, top, width, ButtonHeight));
        }
        int rows = (buttons.Length + columns - 1) / columns;
        return y + rows * (ButtonHeight + Gap);
    }

    private string SpawnCommand()
    {
        string code = creature.Split(':')[1];
        // (The encounter command takes x and z before the distance; a player's own position is used whatever they are)
        return distance == "auto" ? $"/backrooms encounter {code} {encounter}" : $"/backrooms encounter {code} {encounter} 0 0 {distance}";
    }

    /// <summary>A perception probe of the chosen creature, at the chosen distance (20 on auto).</summary>
    private string PerceiveCommand()
    {
        string code = creature.Split(':')[1];
        string blocks = distance == "auto" ? "20" : distance;
        return $"/backrooms perceive {code} {blocks}";
    }

    /// <summary>A command about the column you stand in, which takes its x and z (world coordinates, not the HUD's).</summary>
    private bool SendHere(string format)
    {
        var pos = capi.World.Player.Entity.Pos;
        return Send(string.Format(format, (int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)));
    }

    private bool Send(string command)
    {
        capi.SendChatMessage(command);
        return true;
    }

    private bool Say(string text)
    {
        capi.ShowChatMessage(text);
        return true;
    }

    private void OnTabClicked(int index)
    {
        tab = index;
        Compose();
    }
}
