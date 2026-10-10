using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.GameContent;

namespace Backrooms;

/// <summary>
/// "Backrooms: First Steps", the step-by-step quick start that stands in for the game's own First Steps tutorial in
/// a Backrooms world. It uses the game's tutorial system (ModSystemTutorial), so it shows in the handbook's
/// Tutorials tab, tracks what the player picks up, cuts, crafts and knaps, and keeps its progress like the vanilla
/// one. The step texts live in lang as tutorial-backrooms-N (written by tools/gen_guide.py); the title is
/// title-tutorial-backrooms-firststeps in the game domain (assets/game/lang/en.json), because the tutorial page
/// builds that key without a domain.
///
/// GuideSystem registers it, hides the vanilla tutorial in Backrooms worlds (it sends you to look for cattails and
/// trees), and starts it once on a client's first visit to a Backrooms world.
/// </summary>
public class BackroomsTutorial : TutorialBase
{
    /// <summary>Key in ModSystemTutorial.Tutorials; the handbook page is "tutorial-" + this.</summary>
    public const string Code = "backrooms-firststeps";

    public BackroomsTutorial(ICoreClientAPI capi) : base(capi, "tutorial-" + Code) { }

    private static string Text(int n) => "backrooms:tutorial-backrooms-" + n;

    private static bool Is(ItemStack stack, string domain, string path)
        => stack?.Collectible?.Code != null && stack.Collectible.Code.Domain == domain && stack.Collectible.Code.Path == path;

    private static bool Ours(ItemStack stack, string path) => Is(stack, "backrooms", path);

    private static bool Knappable(ItemStack stack)
        => Is(stack, "game", "flint") || (stack?.ItemAttributes != null && stack.ItemAttributes.IsTrue("knappable"));

    /// <summary>Anything a supply box drops: proof that the player has broken one open.</summary>
    private static bool FromSupplyBox(ItemStack stack)
    {
        if (stack?.Collectible?.Code == null) return false;
        string path = stack.Collectible.Code.Path;
        if (stack.Collectible.Code.Domain == "backrooms")
        {
            return path is "almondwater" or "crackers" or "cannedbeans" or "carpetfibre" or "wallpaperstrip"
                or "glassshard" or "metalbracket" or "glassshiv" || path.StartsWith("wanderernote") || path.StartsWith("seedpacket");
        }
        return path is "flint" or "stick" or "drygrass" or "candle";
    }

    protected override void initTutorialSteps()
    {
        steps.Clear();
        addSteps(
            // 1. Moving, and why not to run
            TutorialStepBase.Press(capi, "move", Text(1), "walkforward", "walkbackward", "walkleft", "walkright", "jump", "sneak", "sprint"),
            // 2. The note in your pocket, and the journal
            TutorialStepBase.Press(capi, "journal", Text(2), "journal"),
            // 3. The two supply boxes beside you
            TutorialStepBase.Collect(capi, "openboxes", Text(3), FromSupplyBox, 1),
            // 4. Glass from a dead light
            TutorialStepBase.Collect(capi, "getshard", Text(4), s => Ours(s, "glassshard"), 1),
            // 5. and 6. Cut wallpaper and carpet with the bare shard
            TutorialStepBase.Collect(capi, "cutstrip", Text(5), s => Ours(s, "wallpaperstrip"), 1),
            TutorialStepBase.Collect(capi, "cutfibre", Text(6), s => Ours(s, "carpetfibre"), 1),
            // 7. A real blade
            TutorialStepBase.Craft(capi, "craftshiv", Text(7), s => Ours(s, "glassshiv") || Ours(s, "scraper"), 1),
            // 8. More carpet, for a bag
            TutorialStepBase.Collect(capi, "cutfibres", Text(8), s => Ours(s, "carpetfibre"), 8),
            // 9. Twine
            TutorialStepBase.Craft(capi, "crafttwine", Text(9), s => Is(s, "game", "flaxtwine"), 1),
            // 10. The carpet bag
            TutorialStepBase.Craft(capi, "craftbag", Text(10), s => Ours(s, "carpetbag"), 1),
            // 11. Flint, from sealed boxes
            TutorialStepBase.Collect(capi, "getflint", Text(11), Knappable, 2),
            // 12. Knap a knife blade
            TutorialStepBase.Knap(capi, "knapknife", Text(12), s => s?.Collectible?.Code != null && s.Collectible.Code.Path.Contains("knifeblade"), 1),
            // 13. Haft it
            TutorialStepBase.Craft(capi, "craftknife", Text(13), s => s?.Collectible != null && s.Collectible.GetTool(new DummySlot(s)) == EnumTool.Knife, 1),
            // 14. The map
            TutorialStepBase.Press(capi, "map", Text(14), "worldmaphud"),
            // 15. The handbook, and the end of the tutorial
            TutorialStepBase.Press(capi, "handbook", Text(15), "handbook")
        );
    }
}
