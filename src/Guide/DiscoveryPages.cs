using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms;

/// <summary>
/// A handbook page whose text, or whether it is there at all, depends on what the player has found
/// (<see cref="Discovery"/>). Both are worked out from the player's watched attributes when they are asked for: the
/// handbook filters its list (IsDuplicate hides a page from the list and from search) each time it opens or its
/// search changes, and composes a page each time it is opened, so neither needs refreshing when something is found.
/// A hidden page can still be reached by a link (the handbook opens any page by code): it then shows only
/// <see cref="HiddenText"/>.
/// </summary>
public class DiscoveryPage : TiledHandbookTextPage
{
    /// <summary>Whether the page is in the list (null: always).</summary>
    public Func<bool> Shown;
    /// <summary>The page's rich text now (null: <see cref="GuiHandbookTextPage.Text"/>, a lang key, as it is).</summary>
    public Func<string> Compose;
    /// <summary>A lang key: what a hidden page says when a link opens it.</summary>
    public string HiddenText;
    /// <summary>Kept out of the list and search for good (an old page code that now opens another page's text).</summary>
    public bool Alias;

    private string fixedText, searchTitle;

    public override bool IsDuplicate => Alias || (Shown != null && !Shown());

    public new void Init(ICoreClientAPI capi)
    {
        base.Init(capi);
        fixedText = Text;
        searchTitle = StringUtil.ToSearchFriendly(Lang.Get(Title));
    }

    private string Current()
    {
        if (Shown != null && !Shown()) return Lang.Get(HiddenText);
        return Compose?.Invoke() ?? fixedText;
    }

    public override void ComposePage(GuiComposer detailViewGui, ElementBounds textBounds, ItemStack[] allstacks, ActionConsumable<string> openDetailPageFor)
    {
        Text = Current();
        base.ComposePage(detailViewGui, textBounds, allstacks, openDetailPageFor);
    }

    public override PageText GetPageText() => new() { Title = searchTitle, Text = Current() };
}

/// <summary>
/// The pages that learn as the player does (config/guide.json; the text is tools/gen_guide.py's): The Levels, Ways
/// Between Levels and What Lives Here as indexes, and a hidden page per level (backrooms-level-&lt;id&gt;) and per
/// creature (backrooms-entity-&lt;code&gt;) that appears once the level has been visited or the creature met.
/// </summary>
public class DiscoveryPages
{
    private readonly ICoreClientAPI capi;
    private readonly GuideTable table;

    public DiscoveryPages(ICoreClientAPI capi)
    {
        this.capi = capi;
        table = GuideTable.Load(capi);
    }

    private Vintagestory.API.Common.Entities.Entity Player => capi.World?.Player?.Entity;

    private int Visited => Discovery.Visited(Player);

    // (The met list is parsed again only when its string changes)
    private string metRaw;
    private HashSet<string> metSet = new();

    private HashSet<string> Met
    {
        get
        {
            string raw = Player?.WatchedAttributes.GetString(Discovery.MetKey) ?? "";
            if (raw != metRaw)
            {
                metRaw = raw;
                metSet = new HashSet<string>(raw.Split(',', StringSplitOptions.RemoveEmptyEntries));
            }
            return metSet;
        }
    }

    private static string L(string key) => Lang.Get("backrooms:" + key);

    private static string Link(string page, string text) => $"<a href=\"handbook://{page}\">{text}</a>";

    public static string LevelPage(int id) => "backrooms-level-" + id;

    public static string EntityPage(string code) => "backrooms-entity-" + code;

    // ================= The pages =================

    /// <summary>The Levels and the level pages (after it), with backrooms-farlevels kept as a hidden way to The Levels.</summary>
    public IEnumerable<GuiHandbookTextPage> LevelPages()
    {
        yield return Page("backrooms-levels", "guide-levels-title", ComposeLevels);
        foreach (int id in table.Levels)
        {
            int level = id;
            yield return Page(LevelPage(level), $"guide-level-{level}-title", null, $"guide-level-{level}-text",
                () => Discovery.HasVisited(Visited, level), "guide-index-level-unvisited");
        }
        var alias = Page("backrooms-farlevels", "guide-levels-title", ComposeLevels);
        alias.Alias = true;
        yield return alias;
    }

    public GuiHandbookTextPage Thresholds() => Page("backrooms-thresholds", "guide-thresholds-title", ComposeThresholds);

    /// <summary>What Lives Here and the creature pages (after it).</summary>
    public IEnumerable<GuiHandbookTextPage> EntityPages()
    {
        yield return Page("backrooms-entities", "guide-entities-title", ComposeEntities);
        foreach (GuideTable.Creature c in table.Entities)
        {
            string code = c.Code;
            yield return Page(EntityPage(code), $"guide-entity-{code}-title", null, $"guide-entity-{code}-text",
                () => Met.Contains(code), "guide-index-entity-unmet");
        }
    }

    private DiscoveryPage Page(string code, string title, Func<string> compose, string text = null, Func<bool> shown = null, string hidden = null)
    {
        var page = new DiscoveryPage
        {
            pageCode = code, Title = "backrooms:" + title, Text = text == null ? "" : "backrooms:" + text,
            Compose = compose, Shown = shown, HiddenText = hidden == null ? null : "backrooms:" + hidden,
        };
        page.Init(capi);
        return page;
    }

    // ================= The indexes =================

    /// <summary>The Levels: 0 to 11 always (names only until visited), any other level once visited.</summary>
    private string ComposeLevels()
    {
        int bits = Visited;
        var sb = new StringBuilder(L("guide-levels-text"));
        sb.Append("<br><br>").Append(L("guide-index-levels-rings"));
        foreach (int id in table.Levels.Where(l => table.Listed.Contains(l)))
            sb.Append("<br>").Append(LevelLine(id, bits));
        int[] far = table.Levels.Where(l => !table.Listed.Contains(l) && Discovery.HasVisited(bits, l)).ToArray();
        if (far.Length > 0)
        {
            sb.Append("<br><br>").Append(L("guide-index-levels-far"));
            foreach (int id in far) sb.Append("<br>").Append(LevelLine(id, bits));
        }
        return sb.Append("<br><br>").Append(L("guide-index-footer")).ToString();
    }

    private static string LevelLine(int id, int bits)
    {
        string name = L($"guide-level-{id}-title");
        return Discovery.HasVisited(bits, id) ? "- " + Link(LevelPage(id), name) : $"- {name}: <i>{L("guide-index-levels-unvisited")}</i>";
    }

    /// <summary>Ways Between Levels: the rules always, then only the ways out of levels visited.</summary>
    private string ComposeThresholds()
    {
        var sb = new StringBuilder(L("guide-thresholds-text"));
        bool any = AppendSections(sb, "thresholds", table.Thresholds, Visited);
        if (!any) sb.Append("<br><br>").Append(L("guide-index-thresholds-none"));
        return sb.Append("<br><br>").Append(L("guide-index-footer")).ToString();
    }

    /// <summary>
    /// What Lives Here: the general part, then the creatures of the levels visited (a link once met, "not yet met"
    /// before), then the notes on the levels visited.
    /// </summary>
    private string ComposeEntities()
    {
        int bits = Visited;
        HashSet<string> met = Met;
        var sb = new StringBuilder(L("guide-entities-text"));
        sb.Append("<br><br>").Append(L("guide-index-entities-known"));
        int listed = 0;
        foreach (GuideTable.Creature c in table.Entities)
        {
            if (!Discovery.HasVisitedAny(bits, c.Levels)) continue;
            string name = L($"guide-entity-{c.Code}-title");
            sb.Append("<br>").Append(met.Contains(c.Code) ? "- " + Link(EntityPage(c.Code), name) : $"- {name}: <i>{L("guide-index-entities-notmet")}</i>");
            listed++;
        }
        if (listed == 0) sb.Append("<br>").Append(L("guide-index-entities-none"));
        AppendSections(sb, "entities", table.EntityNotes, bits);
        return sb.Append("<br><br>").Append(L("guide-index-footer")).ToString();
    }

    /// <summary>
    /// The @-marked sections of a page (lang guide-&lt;page&gt;-s&lt;n&gt; and -s&lt;n&gt;-&lt;line&gt;): each line whose levels
    /// are empty (shown to everyone) or include a visited one, under its section's heading; a section with no line to
    /// show is left out. Returns whether any gated line (one with levels) was shown.
    /// </summary>
    private static bool AppendSections(StringBuilder sb, string page, int[][][] sections, int bits)
    {
        bool any = false;
        for (int s = 0; s < sections.Length; s++)
        {
            var lines = new List<string>();
            for (int n = 0; n < sections[s].Length; n++)
            {
                int[] levels = sections[s][n];
                if (levels.Length > 0 && !Discovery.HasVisitedAny(bits, levels)) continue;
                lines.Add(L($"guide-{page}-s{s + 1}-{n + 1}"));
                any |= levels.Length > 0;
            }
            if (lines.Count == 0) continue;
            sb.Append("<br><br>").Append(L($"guide-{page}-s{s + 1}"));
            foreach (string line in lines) sb.Append("<br>").Append(line);
        }
        return any;
    }
}
