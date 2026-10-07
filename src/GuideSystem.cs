using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.GameContent;

namespace Backrooms;

/// <summary>
/// The Backrooms' pages in the handbook's Guides tab. In a Backrooms world the Starter Guide, the Progression Guide
/// and the Temporal Stability page are rewritten for the Backrooms (keeping their page codes, so every link to them
/// still works), and three reference pages are added after them: Salvage and Recipes, The Levels, and Ways Between
/// Levels. Other worlds keep the vanilla handbook untouched.
///
/// The text is written in tools/gen_guide.py and lives in the lang file as guide-*-title and guide-*-text.
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
    private static readonly string[] Added = { "home", "finding", "salvage", "levels", "thresholds", "entities" };

    private ICoreClientAPI capi;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        // Called each time the handbook builds its pages (on joining a world, and again when hotkeys change)
        api.ModLoader.GetModSystem<ModSystemSurvivalHandbook>().OnInitCustomPages += OnInitPages;
    }

    private void OnInitPages(List<GuiHandbookPage> pages)
    {
        if (!BackroomsWorld.IsBackroomsClimate(capi.World.Config)) return;

        int after = -1;
        for (int i = 0; i < pages.Count; i++)
        {
            if (pages[i] is not GuiHandbookTextPage page || !Rewritten.TryGetValue(page.pageCode, out string guide)) continue;
            page.Title = Title(guide);
            page.Text = Text(guide);
            page.Init(capi);
            if (guide == "progression") after = i;
        }

        if (after < 0) after = pages.Count - 1;
        foreach (string guide in Added)
        {
            var page = new GuiHandbookTextPage { pageCode = "backrooms-" + guide, Title = Title(guide), Text = Text(guide) };
            page.Init(capi);
            pages.Insert(++after, page);
        }
    }

    private static string Title(string guide) => $"backrooms:guide-{guide}-title";

    private static string Text(string guide) => $"backrooms:guide-{guide}-text";
}
