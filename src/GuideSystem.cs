using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.GameContent;

namespace Backrooms;

/// <summary>
/// The handbook and the tutorial in a Backrooms world. Other worlds keep the vanilla handbook and tutorial untouched.
///
/// Guides tab: the Starter Guide, the Progression Guide and the Temporal Stability page are rewritten for the
/// Backrooms (keeping their page codes, so every link to them still works); the Backrooms' own pages are added after
/// the Progression Guide; and every other vanilla guide gets a short "In the Backrooms" preface that says what is
/// different here (the vanilla text below it stays, because the crafting it describes is unchanged).
///
/// Tutorials tab: the game's First Steps tutorial is replaced by Backrooms: First Steps (BackroomsTutorial), which
/// also starts by itself the first time a client visits a Backrooms world.
///
/// The text is written in tools/gen_guide.py and lives in the lang file as guide-*-title, guide-*-text,
/// guide-bridge-* and tutorial-backrooms-*.
/// </summary>
public class GuideSystem : ModSystem
{
    /// <summary>Vanilla pages rewritten for the Backrooms: page code to our guide.</summary>
    private static readonly Dictionary<string, string> Rewritten = new()
    {
        ["craftinginfo-starterguide"] = "starter",
        ["craftinginfo-progressionguide"] = "progression",
        ["gamemechanicinfo-temporalstability"] = "stability",
    };

    /// <summary>Pages of our own, in the order they follow the Progression Guide.</summary>
    private static readonly string[] Added =
    {
        "home", "finding", "salvage", "food", "levels", "farlevels", "thresholds", "entities",
    };

    /// <summary>Vanilla pages kept, with a Backrooms preface: page code to the preface's lang key suffix.</summary>
    private static readonly Dictionary<string, string> Bridged = new()
    {
        ["craftinginfo-knapping"] = "knapping",
        ["craftinginfo-clayforming"] = "clayforming",
        ["craftinginfo-mealcooking"] = "mealcooking",
        ["craftinginfo-charcoalburning"] = "charcoalburning",
        ["gamemechanicinfo-farming"] = "farming",
        ["gamemechanicinfo-foodpreservation"] = "foodpreservation",
        ["gamemechanicinfo-animalhusbandry"] = "animalhusbandry",
        ["gamemechanicinfo-panning"] = "panning",
        ["craftinginfo-smelting"] = "smelting",
        ["craftinginfo-smithing"] = "smithing",
        ["gamemechanicinfo-prospecting"] = "prospecting",
        ["craftinginfo-armor"] = "armor",
        ["gamemechanicinfo-mechanicalpower"] = "mechanicalpower",
        ["gamemechanicinfo-steelmaking"] = "steelmaking",
        ["craftinginfo-cokeoven"] = "cokeoven",
        ["gamemechanicinfo-weather"] = "weather",
        ["gamemechanicinfo-stonelayers"] = "stonelayers",
        ["craftinginfo-cheese"] = "cheese",
        ["craftinginfo-quenching"] = "quenching",
        ["gamemechanicinfo-fruittrees"] = "fruittrees",
        ["craftinginfo-alcohol"] = "alcohol",
        ["craftinginfo-dyemaking"] = "dyemaking",
        ["gamemechanicinfo-groundstorage"] = "groundstorage",
        ["craftinginfo-leathermaking"] = "leathermaking",
        ["gamemechanicinfo-greenhouse"] = "greenhouse",
        ["gamemechanicinfo-beehivekiln"] = "beehivekiln",
        ["gamemechanicinfo-shipbuilding"] = "shipbuilding",
        ["gamemechanicinfo-mountableanimals"] = "mountableanimals",
        ["gamemechanicinfo-fishing"] = "fishing",
    };

    private const string TutorialFlagFile = "backrooms-tutorial.json";

    private ICoreClientAPI capi;
    private ModSystemTutorial tutorials;
    private ITutorial vanillaFirstSteps;
    private BackroomsTutorial ours;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    /// <summary>After ModSystemTutorial (default order), so its handbook and level-finalize handlers run before ours.</summary>
    public override double ExecuteOrder() => 1.0;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        tutorials = api.ModLoader.GetModSystem<ModSystemTutorial>();
        tutorials.Tutorials.TryGetValue("firststeps", out vanillaFirstSteps);
        ours = new BackroomsTutorial(api);

        // Called each time the handbook builds its pages (on joining a world, and again when hotkeys change)
        api.ModLoader.GetModSystem<ModSystemSurvivalHandbook>().OnInitCustomPages += OnInitPages;
        api.Event.LevelFinalize += OnLevelFinalize;
    }

    private bool InBackrooms => capi.World?.Config != null && BackroomsWorld.IsBackroomsClimate(capi.World.Config);

    private void OnInitPages(List<GuiHandbookPage> pages)
    {
        bool backrooms = InBackrooms;
        SelectTutorial(backrooms);
        // The tutorial system has already added a page per registered tutorial; drop the one that does not belong here
        string hidden = "tutorial-" + (backrooms ? "firststeps" : BackroomsTutorial.Code);
        pages.RemoveAll(p => p is GuiHandbookTutorialPage && p.PageCode == hidden);
        if (!backrooms) return;

        int after = -1;
        for (int i = 0; i < pages.Count; i++)
        {
            if (pages[i] is not GuiHandbookTextPage page) continue;
            if (Rewritten.TryGetValue(page.pageCode, out string guide))
            {
                page.Title = Title(guide);
                page.Text = Text(guide);
                page.Init(capi);
                if (guide == "progression") after = i;
            }
            else if (Bridged.TryGetValue(page.pageCode, out string bridge))
            {
                string preface = Lang.Get($"backrooms:guide-bridge-{bridge}");
                string text = Lang.Get(page.Text);
                if (!text.StartsWith(preface)) page.Text = preface + "<br><br>" + text;
                page.Init(capi);
            }
        }

        if (after < 0) after = pages.Count - 1;
        foreach (string guide in Added)
        {
            var page = new GuiHandbookTextPage { pageCode = "backrooms-" + guide, Title = Title(guide), Text = Text(guide) };
            page.Init(capi);
            pages.Insert(++after, page);
        }
    }

    /// <summary>Registers the tutorial that belongs to this world and unregisters the other.</summary>
    private void SelectTutorial(bool backrooms)
    {
        tutorials.Tutorials.Remove("firststeps");
        tutorials.Tutorials.Remove(BackroomsTutorial.Code);
        if (backrooms) tutorials.Tutorials[BackroomsTutorial.Code] = ours;
        else if (vanillaFirstSteps != null) tutorials.Tutorials["firststeps"] = vanillaFirstSteps;
    }

    private void OnLevelFinalize()
    {
        if (!InBackrooms) return;
        SelectTutorial(true);
        if (capi.LoadModConfig<TutorialFlag>(TutorialFlagFile)?.Started == true) return;
        // Once per client: the vanilla tutorial is opt-in, but a Backrooms newcomer has no cattails to look for
        capi.Event.RegisterCallback(_ =>
        {
            if (capi.World?.Player == null) return;
            capi.StoreModConfig(new TutorialFlag { Started = true }, TutorialFlagFile);
            if (tutorials.CurrentTutorial != null) return;
            if (capi.World.Player.WorldData.CurrentGameMode == EnumGameMode.Creative) return;
            tutorials.StartTutorial(BackroomsTutorial.Code);
            capi.ShowChatMessage(Lang.Get("backrooms:tutorial-backrooms-started"));
        }, 2500);
    }

    private static string Title(string guide) => $"backrooms:guide-{guide}-title";

    private static string Text(string guide) => $"backrooms:guide-{guide}-text";

    public class TutorialFlag
    {
        public bool Started;
    }
}
