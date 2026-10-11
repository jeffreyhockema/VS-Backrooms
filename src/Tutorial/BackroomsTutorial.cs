using System;
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
///
/// The game checks every unfinished step against everything the player does, not only the current one, so a step's
/// matcher must not be met by what an earlier step makes (the glass shiv is a knife), and a count that has to hold
/// for what comes next is a <see cref="TutorialStepHold"/>.
/// </summary>
public class BackroomsTutorial : TutorialBase
{
    /// <summary>Key in ModSystemTutorial.Tutorials; the handbook page is "tutorial-" + this.</summary>
    public const string Code = "backrooms-firststeps";

    public BackroomsTutorial(ICoreClientAPI capi) : base(capi, "tutorial-" + Code) { }

    private static string Text(int n) => "backrooms:tutorial-backrooms-" + n;

    // What the bag takes (recipes/grid/carpetbag.json and twine-from-carpet.json, and the texts of steps 9 and 10)
    private const int TwineFibres = 3, CarpetBagFibres = 5;

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
        TutorialStepReceive craftShiv = TutorialStepBase.Craft(capi, "craftshiv", Text(7), s => Ours(s, "glassshiv") || Ours(s, "scraper"), 1);
        TutorialStepReceive craftTwine = TutorialStepBase.Craft(capi, "crafttwine", Text(9), s => Is(s, "game", "flaxtwine"), 1);
        TutorialStepReceive craftBag = TutorialStepBase.Craft(capi, "craftbag", Text(10), s => Ours(s, "carpetbag"), 1);
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
            craftShiv,
            // 8. More carpet, for a bag: 3 for the twine and 5 for the bag, in hand once the shiv is made (the fibre cut
            // in step 6 went into the shiv, so it must not count). Steps run side by side, so a player who makes the
            // twine first needs only the bag's 5, and one who has made the bag is done
            new TutorialStepHold(capi, "cutfibres", Text(8), s => Ours(s, "carpetfibre"),
                goal: () => craftTwine.Complete ? CarpetBagFibres : CarpetBagFibres + TwineFibres,
                ready: () => craftShiv.Complete, done: () => craftBag.Complete),
            // 9. Twine
            craftTwine,
            // 10. The carpet bag
            craftBag,
            // 11. Flint, from sealed boxes
            TutorialStepBase.Collect(capi, "getflint", Text(11), Knappable, 2),
            // 12. Knap a knife blade
            TutorialStepBase.Knap(capi, "knapknife", Text(12), s => s?.Collectible?.Code != null && s.Collectible.Code.Path.Contains("knifeblade"), 1),
            // 13. Haft it: a knife of the game's (stone or better), not the shiv or the scraper, which are knives too
            TutorialStepBase.Craft(capi, "craftknife", Text(13), s => s?.Collectible?.Code?.Domain == "game" && s.Collectible.GetTool(new DummySlot(s)) == EnumTool.Knife, 1),
            // 14. The map
            TutorialStepBase.Press(capi, "map", Text(14), "worldmaphud"),
            // 15. The handbook, and the end of the tutorial
            TutorialStepBase.Press(capi, "handbook", Text(15), "handbook")
        );
    }
}

/// <summary>
/// A step met by having so many of something in the inventory at once, counted only from when <c>ready</c> says the
/// steps before it are done. The game's own Collect step is checked from the tutorial's start alongside every other
/// step and keeps its last count whenever the player holds none, so a carpet fibre cut in step 6 and then sewn into
/// the shiv still counted toward step 8: it asked for one fewer than the twine and the bag take, and could even be
/// met before the shiv was made. This one counts what is held now (none included), and only once it is its turn.
/// </summary>
public class TutorialStepHold : TutorialStepReceive
{
    private readonly ItemStackMatcherDelegate matcher;
    private readonly Func<int> goal;
    private readonly Func<bool> ready, done;

    /// <param name="goal">How many must be held, asked again at every check (it may fall as later steps are done).</param>
    /// <param name="ready">Whether counting has begun.</param>
    /// <param name="done">Whether what the step was for has been done already, which also completes it.</param>
    public TutorialStepHold(ICoreClientAPI capi, string code, string text, ItemStackMatcherDelegate matcher, Func<int> goal, Func<bool> ready, Func<bool> done = null)
        : base(capi, text, matcher, EnumReceiveType.Collect, goal())
    {
        this.code = code;
        this.matcher = matcher;
        this.goal = goal;
        this.ready = ready;
        this.done = done;
    }

    // (What is held is all that counts: picking things up is seen by the inventory check anyway)
    public override bool OnItemStackReceived(ItemStack stack, string eventName) => false;

    public override bool DoCheckPlayerInventory(IPlayerInventoryManager inventoryManager)
    {
        if (watcher.MilestoneReached()) return false;
        if (done?.Invoke() == true)
        {
            watcher.Skip();
            return true;
        }
        watcher.QuantityGoal = goal();
        int held = 0;
        if (ready())
        {
            // As the game's check does: every inventory of the player's but the creative one and the ground
            foreach (var (_, inventory) in inventoryManager.Inventories)
            {
                if (inventory.ClassName is "creative" or "ground") continue;
                foreach (ItemSlot slot in inventory)
                    if (slot?.Itemstack != null && matcher(slot.Itemstack)) held += slot.Itemstack.StackSize;
            }
        }
        if (held == watcher.QuantityAchieved) return false;
        watcher.QuantityAchieved = held;
        return true;
    }
}
