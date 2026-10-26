using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Salvage;

/// <summary>How a kind of Backrooms block gives way when it is broken.</summary>
public enum BreakKind
{
    /// <summary>Not ours, or ours but not part of the building (furniture, clutter): left as it is.</summary>
    None,
    /// <summary>The building itself: walls, floors, ceilings, pipes, fixtures. Broken down into rubble and parts.</summary>
    Structure,
    /// <summary>Never broken: the ways between levels, the dispensers, the doors and the landmarks.</summary>
    Fixed,
}

/// <summary>
/// What breaking the building gives. The structure of the Backrooms breaks like anything in Vintage Story, with the
/// tool its material calls for, but it breaks <i>down</i>: bash out a stretch of wall and what you are left with is
/// rubble, a stud, a strip of paper, a twist of wire, never a clean wall block to set down again. Rubble is good for
/// rough masonry and little else, so walls can be torn out to shape a home without the building turning into a
/// quarry of building blocks, or the scarce things (copper, wood, glass) turning common.
///
/// Each block's class sets its material (which decides the tool), the tool tier it needs, how long it takes, how slowly
/// bare hands get through it, and what falls out. The tiers follow vanilla: tier 0 anything, 1 a stone tool, 2 copper,
/// 3 bronze. Concrete, brick and tile take a copper pickaxe, like rock; drywall, timber and glass give to anything,
/// but bare hands barely dent them.
/// </summary>
public static class Breakdown
{
    public sealed class Class
    {
        public EnumBlockMaterial Material;
        public int Tier;
        public float Resistance;
        /// <summary>How fast bare hands work, against a held tool (only where no tier is needed).</summary>
        public float HandFactor = 1f;
        public (string Code, float Avg, float Var)[] Drops;
    }

    private const string Rubble = "rubble", Stick = "game:stick", Plank = "game:plank-aged", Firewood = "game:firewood";
    private const string Bracket = "metalbracket", Wire = "scrapwire", Shard = "glassshard", Strip = "wallpaperstrip", Fibre = "carpetfibre";
    private const string Copper = "game:metalbit-copper", Lead = "game:metalbit-lead", Nails = "game:metalnailsandstrips-iron";

    private static (string, float, float)[] D(params (string, float, float)[] drops) => drops;

    // ---- The classes ----

    /// <summary>Poured concrete: slabs, block walls, pillars, kerbs, the city's frames. Mostly dust; a few lumps worth keeping.</summary>
    private static readonly Class Concrete = new() { Material = EnumBlockMaterial.Stone, Tier = 2, Resistance = 10, Drops = D((Rubble, 0.5f, 0.4f)) };

    /// <summary>A floor: concrete under its carpet or its finish. It takes what concrete takes.</summary>
    private static readonly Class Floor = new() { Material = EnumBlockMaterial.Stone, Tier = 2, Resistance = 9, Drops = D((Rubble, 0.4f, 0.4f)) };

    /// <summary>A carpeted floor gives a little of its pile too.</summary>
    private static readonly Class CarpetFloor = new() { Material = EnumBlockMaterial.Stone, Tier = 2, Resistance = 9, Drops = D((Rubble, 0.4f, 0.4f), (Fibre, 0.3f, 0.3f)) };

    /// <summary>Brick, cinder block, glazed tile, marble and ashlar: a copper pick, a little less work than concrete.</summary>
    private static readonly Class Masonry = new() { Material = EnumBlockMaterial.Stone, Tier = 2, Resistance = 8, Drops = D((Rubble, 0.5f, 0.4f)) };

    /// <summary>
    /// Drywall and plaster on studs: anything with an edge gets through it, an axe best. Mostly gypsum dust; now and then a
    /// stud worth keeping, or a strip of the paper still on it.
    /// </summary>
    private static readonly Class Drywall = new() { Material = EnumBlockMaterial.Wood, Tier = 0, Resistance = 5, HandFactor = 0.15f, Drops = D((Stick, 0.15f, 0.15f)) };

    /// <summary>Papered drywall: a scrap of the paper comes away too.</summary>
    private static readonly Class Papered = new() { Material = EnumBlockMaterial.Wood, Tier = 0, Resistance = 5, HandFactor = 0.15f, Drops = D((Stick, 0.15f, 0.15f), (Strip, 0.2f, 0.2f)) };

    /// <summary>Boarded walls, panelling, floorboards and roofs: splintered boards, kindling and a few nails, rarely a whole plank.</summary>
    private static readonly Class Timber = new() { Material = EnumBlockMaterial.Wood, Tier = 0, Resistance = 4, HandFactor = 0.2f, Drops = D((Stick, 0.4f, 0.4f), (Firewood, 0.1f, 0.1f), (Plank, 0.05f, 0f)) };

    /// <summary>Heavy built-in woodwork (counters, the piano, the clock): more timber in it than in a wall.</summary>
    private static readonly Class Joinery = new() { Material = EnumBlockMaterial.Wood, Tier = 0, Resistance = 5, HandFactor = 0.2f, Drops = D((Plank, 0.6f, 0.4f), (Stick, 0.6f, 0.4f), (Nails, 0.2f, 0.2f)) };

    /// <summary>Sheet metal, poles, rails, housings: a copper pick or nothing. Bent brackets, the odd bolt.</summary>
    private static readonly Class Metal = new() { Material = EnumBlockMaterial.Metal, Tier = 2, Resistance = 6, Drops = D((Bracket, 0.15f, 0.15f)) };

    /// <summary>Anything wired: switchgear, cable runs, machines. A little copper wire among the scrap.</summary>
    private static readonly Class Electrical = new() { Material = EnumBlockMaterial.Metal, Tier = 2, Resistance = 6, Drops = D((Bracket, 0.1f, 0.1f), (Wire, 0.15f, 0.15f)) };

    /// <summary>Glass: anything breaks it, and it breaks into shards.</summary>
    private static readonly Class Glass = new() { Material = EnumBlockMaterial.Glass, Tier = 0, Resistance = 1, Drops = D((Shard, 0.5f, 0.5f)) };

    /// <summary>Packed earth, tracks and stubble: a shovel's work, and it stays where it lay.</summary>
    private static readonly Class Ground = new() { Material = EnumBlockMaterial.Soil, Tier = 0, Resistance = 2, Drops = D() };

    /// <summary>A wrecked car: a copper pick and some work, for a good deal of scrap (and its seat vinyl, pleather). Its invisible hull goes with it.</summary>
    private static readonly Class Wreck = new() { Material = EnumBlockMaterial.Metal, Tier = 2, Resistance = 12,
        Drops = D((Bracket, 0.8f, 0.4f), (Wire, 0.6f, 0.4f), (Shard, 1f, 0.5f), (Copper, 0.4f, 0.4f), ("pleather", 1.5f, 0.5f)) };

    /// <summary>The invisible hull round a car's model: breaking it breaks the car (<see cref="BlockBehaviorWreck"/>).</summary>
    private static readonly Class WreckHull = new() { Material = EnumBlockMaterial.Metal, Tier = 2, Resistance = 12, Drops = D() };

    /// <summary>What a light fixture comes apart into, lit or dead: the tube shatters.</summary>
    private static readonly (string, float, float)[] LightScraps = D((Shard, 1.5f, 0.5f), (Bracket, 0.12f, 0f), (Wire, 0.3f, 0f));

    /// <summary>Soft stuff (the ball pit): gone when broken.</summary>
    private static readonly Class Soft = new() { Material = EnumBlockMaterial.Cloth, Tier = 0, Resistance = 1, Drops = D() };

    // ---- Which class each block is, by the first part of its code ----

    private static readonly Dictionary<string, Class> Classes = new();

    private static void Add(Class cls, params string[] codes)
    {
        foreach (string code in codes) Classes[code] = cls;
    }

    /// <summary>
    /// Blocks that never break: the thresholds and dispensers (found by their behaviour and class, see <see cref="KindOf"/>),
    /// and these. Doors lead somewhere or are locked (that is the pry bar's job); the rest are landmarks and the workings
    /// of the levels.
    /// </summary>
    private static readonly HashSet<string> FixedCodes = new()
    {
        "firedoor", "metaldoor", "officedoor", "noclipwall", "tripwire", "manhole", "manholeladder", "cinemascreen", "twilightgate",
        "glassmountain", "kingstatue", "megmarker", "backdrop", "diorama",
        // Level 7's high ceiling (layout version 9): over it is the top of the world
        "seaceiling",
        // Invisible sound emitters
        "cityhum", "subwayrumble", "waveecho",
    };

    /// <summary>Ours, but with a class of its own that decides what breaking it does: left exactly as they are.</summary>
    private static readonly HashSet<string> OwnRules = new() { "firesalt", "mothhiveheart", "clumpremnant", "redsprout", "tar", "trialchair", "picketfence" };

    static Breakdown()
    {
        Add(Concrete, "concrete", "concretewall", "concreteceiling", "concretepillar", "concretestairs", "concretedeco", "concretecam",
            "pillarbase", "pillardeco", "pillarlight", "l1deco", "wheelstop", "speedbump", "exitlintel", "exitlintelpair", "exitsign",
            "tunnelwall", "tunnelceiling", "l6block", "l6deco", "whiteblock", "whitecam", "oceanceiling",
            "subwaywall", "subwaydeco", "citypier", "cityfacade", "cityroof", "citydeco", "chimney", "snackceiling",
            "asphalt", "sidewalk", "motionground", "fountainrim", "roomsign", "l3wallfixture", "wallpipecorner", "tunnelfitting", "tunnelstep",
            "l3fitting");
        Add(Floor, "concretefloor", "l1hallfloor", "dustyfloor", "l3floor", "subwayfloor", "cityfloor", "parkfloor", "snackfloor",
            "funfloor", "hotelfloor");
        Add(CarpetFloor, "carpet", "officecarpet", "officecarpetalt", "hotelcarpet");
        Add(Masonry, "l3wall", "l3decobrick", "l3decocinder", "l3decoglazed", "l3decostone", "l3plaquebrick", "l3plaquecinder",
            "l3plaqueglazed", "poolwall", "pooltile", "pool", "marblecolumn", "hotelstairs", "sanctumstone", "sanctumceiling", "castleblock", "angelstatue",
            "stonehand", "stonestapler", "ribcage", "bathtub", "snackwall", "snackdeco");
        Add(Papered, "wallpaper", "paperjoin", "archheader", "stuccojoin", "archheaderstucco");
        Add(Drywall, "drywallbase", "officewall", "officedeco", "plasterwall", "plasterdeco", "plasterceiling", "cityplaster",
            "houseinterior", "housedeco", "nooutletsign");
        Add(Timber, "hotelwall", "hotelwood", "hotelfixture", "hotelceiling", "hoteldeco", "housewall", "housecorner", "housefloor",
            "houseceiling", "houseroof", "roofslope", "pitchroof", "barnwall", "barnroof", "jetty", "cityfascia", "storefrontdeco", "storefrontsign", "staffsign", "staffplaque",
            "doghouse", "watertank", "sirenpole", "powerpole", "fieldgate", "patiochair", "ceilingfan",
            "housestorey", "housestairs", "porchdeck", "porchpost");
        Add(Joinery, "kitchencounter", "hotelreception", "thronetable", "grandfatherclock", "grandpiano");
        // (trafficsign is not here: it is carried off whole, as a salvage item - see SalvageSystem.Salvageable)
        Add(Metal, "pipes", "feedpipe", "rungs", "ironbars", "radiator", "drippipe", "acunit", "antenna", "silo", "watertower", "firehydrant",
            "stopsign", "streetsign", "busshelter", "clearancebar", "basketballhoop", "swingset", "slide",
            "snackcounter", "boiler", "furnace", "chandelier", "poolladder", "waterpump", "sprinkler", "paystation", "conveyor",
            "cagelift", "suburbsign", "suburbsignblade", "citysign");
        Add(Electrical, "conduit", "conduitend", "cables", "floorcable", "floorcableend", "cabledroop", "wiredroop", "transformer", "generator", "switchgear",
            "serverrack", "coilunit", "controldesk", "streetlight", "roadlamp", "roadlamparm", "trafficlight", "porchlamp");
        Add(Glass, "officeglass", "officewindow", "officewindowalt", "officepane", "housewindow", "windowglow", "stainedglass", "exithanging", "funlight");
        Add(Ground, "dirtroad", "fieldstubble");
        Add(Soft, "ballpit", "ballpitfill");
        Add(Wreck, "car");
        Add(WreckHull, "carcollider");
    }

    /// <summary>Copper and lead pipe: a short length now and then, for the crucible.</summary>
    private static readonly Dictionary<string, (string, float, float)[]> ExtraDrops = new()
    {
        ["pipes"] = D((Copper, 0.2f, 0.2f), (Lead, 0.1f, 0.1f)),
        ["grandfatherclock"] = D(("game:gear-rusty", 0.3f, 0f)),
        ["chandelier"] = D((Shard, 1f, 0.5f), ("game:metalbit-brass", 0.5f, 0.5f)),
        ["exitsign"] = D((Shard, 0.3f, 0.3f), (Wire, 0.2f, 0.2f)),
        ["exithanging"] = D((Wire, 0.2f, 0.2f)),
        ["streetlight"] = D((Shard, 0.3f, 0.3f)),
        ["roadlamp"] = D((Shard, 0.3f, 0.3f)),
        ["roadlamparm"] = D((Shard, 0.3f, 0.3f)),
        ["trafficlight"] = D((Shard, 0.5f, 0.3f)),
    };

    /// <summary>Default classes by material, for a structural block not named above (so new blocks are never left unbreakable).</summary>
    private static Class ByMaterial(EnumBlockMaterial material) => material switch
    {
        EnumBlockMaterial.Wood => Timber,
        EnumBlockMaterial.Metal => Metal,
        EnumBlockMaterial.Glass => Glass,
        EnumBlockMaterial.Cloth => Soft,
        EnumBlockMaterial.Soil or EnumBlockMaterial.Gravel or EnumBlockMaterial.Sand => Ground,
        EnumBlockMaterial.Ceramic or EnumBlockMaterial.Brick => Masonry,
        _ => Concrete,
    };

    /// <summary>Level !'s blocks that break like props, with the drops their blocktypes give (everything else of it is fixed).</summary>
    private static readonly string[] RunProps =
    {
        "run-gurney", "run-wheelchair", "run-ivstand", "run-chairs", "run-crashcart", "run-shelf", "run-toycar", "run-boxes", "run-cord",
        "run-sheets", "run-remains", "run-tray", "run-bedside", "run-safeshelf", "run-safecot", "run-debris", "run-curtain", "run-medcabinet",
        "run-barricade",
    };

    private static bool IsRunProp(string path)
    {
        foreach (string prop in RunProps)
            if (path.StartsWith(prop, System.StringComparison.Ordinal)) return true;
        return false;
    }

    /// <summary>Made by the player from the building's scraps: theirs, and it comes back whole.</summary>
    private static readonly HashSet<string> MadeTypes = new() { "rubblemasonry" };

    /// <summary>
    /// The blocks (by code) that keep the drops their block types give, found by <see cref="FindOwnDrops"/>. Kept apart
    /// from the block objects because the client and the server each have their own, and both ask.
    /// </summary>
    private static volatile HashSet<string> ownDrops = new();

    /// <summary>
    /// A block's type: its code without its variant values (<c>l3999-plush-bear-north</c> is <c>l3999-plush</c>), so a
    /// turned or recoloured copy counts as the same thing.
    /// </summary>
    private static string TypeOf(Block block)
    {
        string path = block.Code.Path;
        if (block.Variant == null || block.Variant.Count == 0) return path;
        string suffix = "-" + string.Join("-", block.Variant.Values);
        return path.Length > suffix.Length && path.EndsWith(suffix, System.StringComparison.Ordinal) ? path[..^suffix.Length] : path;
    }

    /// <summary>
    /// Whether a block is one a player makes in the crafting grid: a <c>built-*</c> twin of a block the world generator
    /// uses (<c>backroomsBuilt</c> in its attributes). It gives itself back, breaks by its own block type, and no rule of
    /// ours (<see cref="Apply"/>, <see cref="FindOwnDrops"/>, <see cref="Protection"/>) touches it.
    /// </summary>
    public static bool IsBuilt(Block block) => block?.Attributes?["backroomsBuilt"].AsBool() == true;

    private static bool IsOurs(Block block) => block?.Code != null && block.Code.Domain == "backrooms" && block.BlockId != 0;

    /// <summary>Whether a block's own drops (as its block type gives them) are anything but the block itself.</summary>
    private static bool HasOwnLoot(ICoreAPI api, Block block)
    {
        if (block.Drops == null || block.Drops.Length == 0) return false;
        string type = TypeOf(block);
        foreach (BlockDropItemStack drop in block.Drops)
        {
            if (drop?.Code == null) continue;
            if (drop.Type != EnumItemClass.Block) return true;
            Block dropped = api.World.GetBlock(drop.Code);
            if (dropped == null || !IsOurs(dropped) || TypeOf(dropped) != type) return true;
        }
        return false;
    }

    /// <summary>Whether a block gives a block when broken (a flickering panel gives a dead one), where scaling the drops would hand out more of them.</summary>
    private static bool GivesBlock(Block block)
    {
        if (block.Drops == null) return false;
        foreach (BlockDropItemStack drop in block.Drops)
            if (drop?.Type == EnumItemClass.Block) return true;
        return false;
    }

    /// <summary>
    /// Which of our blocks keep their own drops, worked out from the block types alone (so both sides agree), before
    /// <see cref="Apply"/> changes any. The generators give furniture and clutter what is in it (the Level 188 minibar's
    /// juice and Almond Water, Level 3999's bins and prize cases, Level Fun's cake tins and carnivorous balloons, the
    /// Hub's and The End's props), and many of those share the first part of their code with their level's walls, so
    /// no list by code would find them all. So:
    /// <list type="bullet">
    /// <item>A block that gives anything but itself, and has no class of its own here, is furniture or clutter: its
    /// drops are kept.</item>
    /// <item>A block a player can come by (dropped by any of those, or by salvage; a prize at a Level 3999 counter; made
    /// by the player, <see cref="MadeTypes"/>) gives itself back, as anything a player puts down does, rather than
    /// breaking down like the building.</item>
    /// </list>
    /// </summary>
    private static HashSet<string> FindOwnDrops(ICoreAPI api)
    {
        var keep = new HashSet<string>();
        var carried = new HashSet<string>(MadeTypes);
        foreach (Block block in api.World.Blocks)
        {
            if (!IsOurs(block)) continue;
            string first = block.FirstCodePart();
            if (first == "run" || OwnRules.Contains(first) || Classes.ContainsKey(first)) continue;
            bool salvage = SalvageSystem.IsSalvage(block);
            if (!salvage && !HasOwnLoot(api, block)) continue;
            if (!salvage) keep.Add(block.Code.Path);
            // Whatever of ours it gives can be carried off and set down again
            // (On the client a block type with no drops field has a null Drops array)
            foreach (BlockDropItemStack drop in block.Drops ?? System.Array.Empty<BlockDropItemStack>())
                if (drop?.Code != null && drop.Type == EnumItemClass.Block && api.World.GetBlock(drop.Code) is Block given && IsOurs(given))
                    carried.Add(TypeOf(given));
            JsonObject tiers = block.Attributes?["l3999prizes"];
            if (tiers?.Exists == true)
                foreach (JsonObject cost in tiers)
                    foreach (JsonObject prize in tiers[cost.AsString()].AsArray() ?? System.Array.Empty<JsonObject>())
                        if (prize["type"].AsString("item") == "block"
                            && api.World.GetBlock(AssetLocation.Create(prize["code"].AsString(), "backrooms")) is Block won && IsOurs(won))
                            carried.Add(TypeOf(won));
        }
        foreach (Block block in api.World.Blocks)
        {
            if (!IsOurs(block) || !carried.Contains(TypeOf(block)) || SalvageSystem.IsSalvage(block)) continue;
            string first = block.FirstCodePart();
            if (first != "run" && !OwnRules.Contains(first) && !Classes.ContainsKey(first)) keep.Add(block.Code.Path);
        }
        return keep;
    }

    /// <summary>What kind of block this is, as far as breaking goes.</summary>
    public static BreakKind KindOf(Block block)
    {
        if (block?.Code == null || block.Code.Domain != "backrooms" || block.BlockId == 0) return BreakKind.None;
        // What the player made (the built-* twins of tools/gen_building.py): theirs, and it comes back whole
        if (IsBuilt(block)) return BreakKind.None;
        string first = block.FirstCodePart();
        // Level !: every code starts "run"; its props keep their own drops (loot), the hallway itself never breaks
        if (first == "run") return IsRunProp(block.Code.Path) ? BreakKind.None : BreakKind.Fixed;
        if (SalvageSystem.IsSalvage(block) || OwnRules.Contains(first)) return BreakKind.None;
        if (FixedCodes.Contains(first) || block is Props.BlockDispenser) return BreakKind.Fixed;
        // A way somewhere: any threshold, and the Hub's carved doors (whose threshold behaviour HubSystem swaps for its
        // own before this runs, so they would otherwise break down like the wall round them)
        if (block.BlockBehaviors != null)
            foreach (BlockBehavior behavior in block.BlockBehaviors)
                if (behavior is Thresholds.BlockBehaviorThreshold or Regions.BlockBehaviorHubDoor) return BreakKind.Fixed;
        // Furniture and clutter with what is in it, and anything a player can carry off (see FindOwnDrops)
        if (ownDrops.Contains(block.Code.Path)) return BreakKind.None;
        return BreakKind.Structure;
    }

    /// <summary>The class a structural block breaks as.</summary>
    public static Class ClassOf(Block block) =>
        Classes.TryGetValue(block.FirstCodePart(), out Class cls) ? cls : ByMaterial(block.BlockMaterial);

    /// <summary>
    /// Gives every structural block of ours its class: material, tier, resistance and drops, and the bare-hands
    /// slowdown. Fixed blocks get a tier no tool reaches. Run on both sides (the client predicts the breaking).
    /// Also says which block types keep their own drops (<see cref="FindOwnDrops"/>), and, as a check, which had drops
    /// of their own and lose them all the same: only those with a class named here should (an arch header gives what
    /// any papered wall gives, not the wallpaper its type names).
    /// </summary>
    public static (int Structure, int Fixed, SortedSet<string> Kept, SortedSet<string> Replaced) Apply(ICoreAPI api)
    {
        int structure = 0, fixedCount = 0;
        HashSet<string> keep = FindOwnDrops(api);
        ownDrops = keep;
        var kept = new SortedSet<string>();
        var replaced = new SortedSet<string>();
        foreach (Block block in api.World.Blocks)
        {
            // A lit light used to give itself back, a lamp for life: now it shatters like a dead one
            if (SalvageSystem.IsLiveLight(block)) block.Drops = ResolveDrops(api, block, LightScraps);
            BreakKind kind = KindOf(block);
            if (kind == BreakKind.None && IsOurs(block) && keep.Contains(block.Code.Path)) kept.Add(TypeOf(block));
            if (kind == BreakKind.Structure && HasOwnLoot(api, block)) replaced.Add(TypeOf(block));
            // A light fixture that shatters gives more of its glass to a careful hand (one that gives itself back is left alone)
            if (SalvageSystem.IsLight(block) && !GivesBlock(block))
                block.BlockBehaviors = new List<BlockBehavior>(block.BlockBehaviors ?? System.Array.Empty<BlockBehavior>())
                    { new BlockBehaviorToolDrops(block, BlockBehaviorToolDrops.Mode.Careful) }.ToArray();
            switch (kind)
            {
                case BreakKind.Fixed:
                    block.RequiredMiningTier = Protection.UnbreakableTier;
                    block.Resistance = 1_000_000f;
                    fixedCount++;
                    break;
                case BreakKind.Structure:
                    Class cls = ClassOf(block);
                    block.BlockMaterial = cls.Material;
                    block.RequiredMiningTier = cls.Tier;
                    block.Resistance = cls.Resistance;
                    block.Drops = ResolveDrops(api, block, cls.Drops, block.FirstCodePart());
                    var behaviors = new List<BlockBehavior>(block.BlockBehaviors ?? System.Array.Empty<BlockBehavior>());
                    if (cls.HandFactor < 1f) behaviors.Add(new BlockBehaviorBareHands(block, cls.HandFactor));
                    if (cls == Wreck || cls == WreckHull) behaviors.Add(new BlockBehaviorWreck(block));
                    // Pipes and wired machinery give more to a better pick (see BlockBehaviorToolDrops)
                    if (cls == Electrical || block.FirstCodePart() == "pipes") behaviors.Add(new BlockBehaviorToolDrops(block, BlockBehaviorToolDrops.Mode.Pick));
                    block.BlockBehaviors = behaviors.ToArray();
                    structure++;
                    break;
            }
        }
        return (structure, fixedCount, kept, replaced);
    }

    private static BlockDropItemStack[] ResolveDrops(ICoreAPI api, Block block, (string, float, float)[] baseDrops, string extraFor = null)
    {
        var drops = new List<BlockDropItemStack>();
        IEnumerable<(string, float, float)> all = baseDrops;
        if (extraFor != null && ExtraDrops.TryGetValue(extraFor, out var extra)) all = System.Linq.Enumerable.Concat(all, extra);
        foreach ((string code, float avg, float var) in all)
        {
            // Only papered walls still have paper on them
            if (code == Strip && block.Variant["pattern"] == "stripped") continue;
            var drop = new BlockDropItemStack
            {
                Type = EnumItemClass.Item,
                Code = AssetLocation.Create(code, "backrooms"),
                Quantity = NatFloat.createUniform(avg, var),
            };
            if (drop.Resolve(api.World, "backrooms breakdown", block.Code)) drops.Add(drop);
        }
        return drops.ToArray();
    }
}

/// <summary>
/// A wrecked car is one model drawn by its corner block, filled out by invisible hull blocks. Break any of it and the
/// whole car goes, with its scrap (which only the car block itself gives), so no invisible hull is left standing.
/// </summary>
public class BlockBehaviorWreck : BlockBehavior
{
    private const int MaxParts = 32;

    public BlockBehaviorWreck(Block block) : base(block)
    {
    }

    public override void OnBlockBroken(IWorldAccessor world, BlockPos pos, IPlayer byPlayer, float dropQuantityMultiplier, ref EnumHandling handling)
    {
        if (world.Side != EnumAppSide.Server) return;
        // (As the block's own drops: none in creative)
        bool drops = byPlayer?.WorldData.CurrentGameMode != EnumGameMode.Creative;
        IBlockAccessor blocks = world.BlockAccessor;
        var seen = new HashSet<BlockPos> { pos };
        var queue = new Queue<BlockPos>();
        queue.Enqueue(pos);
        while (queue.Count > 0 && seen.Count < MaxParts)
        {
            BlockPos at = queue.Dequeue();
            foreach (BlockFacing face in BlockFacing.ALLFACES)
            {
                BlockPos next = at.AddCopy(face);
                if (seen.Contains(next)) continue;
                Block part = blocks.GetBlock(next);
                if (part.Code?.Domain != "backrooms" || part.FirstCodePart() is not ("car" or "carcollider")) continue;
                seen.Add(next);
                // A car that straddles a claim's edge does not lose the part inside it to someone who may not build there
                if (byPlayer != null && !world.Claims.TryAccess(byPlayer, next, EnumBlockAccessFlags.BuildOrBreak)) continue;
                queue.Enqueue(next);
                // The car block holds the scrap; the hull gives nothing
                if (drops && part.FirstCodePart() == "car" && part.Drops != null)
                    foreach (BlockDropItemStack drop in part.Drops)
                    {
                        ItemStack stack = drop.GetNextItemStack(dropQuantityMultiplier);
                        if (stack != null) world.SpawnItemEntity(stack, next.ToVec3d().Add(0.5, 0.5, 0.5));
                    }
                blocks.SetBlock(0, next);
            }
        }
    }
}

/// <summary>
/// Slows bare hands on the soft parts of the building (drywall, timber): you can claw through a wall with your fingers,
/// but it takes a long time. Any tool in hand works at its normal pace.
/// </summary>
public class BlockBehaviorBareHands : BlockBehavior
{
    private readonly float factor;

    public BlockBehaviorBareHands(Block block, float factor) : base(block)
    {
        this.factor = factor;
    }

    public override float GetMiningSpeedModifier(IWorldAccessor world, BlockPos pos, IPlayer byPlayer)
    {
        ItemStack held = byPlayer?.InventoryManager?.ActiveHotbarSlot?.Itemstack;
        return held == null || held.Collectible.GetTool(byPlayer.InventoryManager.ActiveHotbarSlot) == null ? factor : 1f;
    }
}
