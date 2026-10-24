using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Salvage;

/// <summary>
/// Salvage: what the Backrooms leaves lying about to be taken. Loose objects (boxes, crates, furniture, ceiling tiles,
/// dead light fixtures) break as normal and give what is in them (<c>tools/salvage.py</c>), and wallpaper and carpet
/// can be stripped with a blade, which leaves the wall or floor in place but visibly bare. The building itself breaks
/// too, but only down to rubble and parts (<see cref="Breakdown"/>), and not where it holds a level up
/// (<see cref="ProtectionSystem"/>).
/// </summary>
public class SalvageSystem : ModSystem
{
    /// <summary>First part of the code of every block that can be broken and carried off.</summary>
    private static readonly HashSet<string> Salvageable = new()
    {
        "supplybox", "crate", "metalshelf", "oildrum", "machinecabinet", "machinecabinetfeed",
        "ceilingtile", "officeceiling",
        "desk", "officechair", "filingcabinet", "partition", "conferencetable",
        "bed", "nightstand", "wardrobe", "wingchair", "sofa", "longsofa", "pottedpalm", "mahjongtable", "turntable",
        // Loose things left lying about: crates and boxes, tools, camp gear, furniture
        "cardboardboxes", "workbench", "toolbox", "plywood", "tent", "bedroll", "camptent", "sleepingbag", "improvbed", "leanto", "camplantern", "hospitalbed",
        "foldingtable", "foldingchair", "medcabinet", "trafficcone", "wetfloorsign", "pallet", "trashcan", "burnbarrel",
        "cablespool", "floorfan", "pipestack", "candelabra",
        "ficus", "chairstack", "copier", "officebookshelf", "roundtable", "receptiondesk", "wastebasket", "coatstand",
        "officechairtipped", "bench",
        "consoletable", "hotelbookshelf", "curiocabinet", "luggagecart", "servicetrolley", "writingdesk", "hotelchair",
        "floorlamp", "suitcase", "coffeetable", "ashtraystand", "diningtable", "coalpile",
        // Levels 6 to 10: what can be raided, salvaged, dug or wiped away
        "chalkmark", "cafetable", "cafechair", "snackshelf", "stove", "fryer", "vendingpile", "brokenvending", "glowcapred", "glowcapmixed",
        "bonepile", "scrapmetal", "jawskeleton", "backpack", "wreckcrate", "islandrock", "seachest",
        "tv", "toilet", "dresser", "mailbox", "seedsacks", "toolshelf", "pantryshelf", "kitchencabinet",
        "feedtrough", "toolrack", "nailbarrel", "wormmass", "farmland",
        "driftwood", "buoy", "flashlight", "grill", "hayroll", "icemachine", "laundry", "laundrycart", "plough",
        "roomservicetray", "scarecrow", "toybox", "tractor", "wheeliebin", "officeceilingalt", "fridge",
        // Level 11: what the city leaves lying about
        "newsbox", "parkingmeter", "phonebooth", "clothesrack", "shoppingcart", "pew", "dumpster", "trashbags", "postbox",
        // Lore details
        "trolley", "machineparts", "trafficsign", "tramrails", "deadtram", "tramwagon", "candlestubs",
        // The survival loop: what is left of a hive
        "mothhive",
        // Level 37: what the pool leaves on its rims; Level 94: the 1950s, and what heaps up on the hills
        "epsomcrust", "lostthing",
        "icebox", "radiocabinet", "rotaryphone", "furniturepile", "oldcar", "tippedcar", "arcade", "easel", "studiocamera",
        // Level 94 is made of clay: its turf and the clay under it can be dug (not its roads, paths or anything built)
        "clayturf", "claysoil",
    };

    /// <summary>Light fixtures: dead or lit, they come down for their glass and fittings.</summary>
    private static readonly HashSet<string> Lights = new()
    {
        "fluorescentlight", "hanginglight", "hangingbulb", "tunnellight", "cablelight", "officelight", "domelight",
    };

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsStrippable", typeof(BlockBehaviorStrippable));
        api.RegisterBlockBehaviorClass("BackroomsPartnered", typeof(BlockBehaviorPartnered));
        api.RegisterBlockBehaviorClass("BackroomsDismantle", typeof(BlockBehaviorDismantle));
    }

    /// <summary>Whether a block of ours is salvage: taken whole, wherever it is, with what it holds.</summary>
    public static bool IsSalvage(Block block)
    {
        if (block?.Code == null || block.Code.Domain != "backrooms") return false;
        string first = block.FirstCodePart();
        return Salvageable.Contains(first) || Lights.Contains(first);
    }

    /// <summary>Whether a block of ours is a light fixture, lit or dead.</summary>
    public static bool IsLight(Block block) =>
        block?.Code?.Domain == "backrooms" && Lights.Contains(block.FirstCodePart());

    /// <summary>A light fixture of ours that is still lit (or flickering).</summary>
    public static bool IsLiveLight(Block block) =>
        block?.Code?.Domain == "backrooms" && Lights.Contains(block.FirstCodePart()) && block.Variant["state"] != "off";
}

/// <summary>
/// Lets a blade strip material off a block: the block turns into its bare variant and the player gets the
/// stripped material. JSON properties:
/// <code>
/// result:  code of the bare block, with {variant} placeholders, e.g. "wallpaper-stripped-{part}"
/// item:    code of the item given
/// variant: (optional) name of a variant group that decides whether this block can be stripped...
/// allowed: ...and the values of it that can
/// </code>
/// Knives work, as does any item with the attribute <c>crudeCutter</c> (a glass shard), which may snap in use.
/// The glass shiv and the improvised scraper were made for this: they peel the paper and lift the pile cleanly, and
/// give two of the stripped item a cut, as does a vanilla knife of copper or better; a flint or bone knife tears off one.
/// </summary>
public class BlockBehaviorStrippable : BlockBehavior
{
    private const double CrudeCutterBreakChance = 0.25;

    /// <summary>The Lobby's own blades, and what each cut gives with one of them.</summary>
    private static readonly HashSet<string> CleanCutters = new() { "backrooms:glassshiv", "backrooms:scraper" };
    private const int CleanCutYield = 2;

    private string result;
    private AssetLocation item;
    private string variant;
    private string[] allowed;
    private WorldInteraction[] help;

    public BlockBehaviorStrippable(Block block) : base(block)
    {
    }

    public override void Initialize(JsonObject properties)
    {
        base.Initialize(properties);
        result = properties["result"].AsString();
        item = AssetLocation.Create(properties["item"].AsString(), block.Code.Domain);
        variant = properties["variant"].AsString();
        allowed = properties["allowed"].AsArray<string>();
    }

    private bool CanStrip => variant == null || allowed == null || System.Array.IndexOf(allowed, block.Variant[variant]) >= 0;

    private static bool IsCutter(ItemSlot slot, out bool crude)
    {
        crude = false;
        CollectibleObject held = slot?.Itemstack?.Collectible;
        if (held == null) return false;
        if (held.GetTool(slot) == EnumTool.Knife) return true;
        crude = held.Attributes?["crudeCutter"].AsBool() == true;
        return crude;
    }

    private Block BareBlock(IWorldAccessor world)
    {
        string code = result;
        foreach (var pair in block.Variant) code = code.Replace("{" + pair.Key + "}", pair.Value);
        return world.GetBlock(AssetLocation.Create(code, block.Code.Domain));
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        ItemSlot slot = byPlayer.InventoryManager.ActiveHotbarSlot;
        if (!CanStrip || !IsCutter(slot, out bool crude)) return false;

        handling = EnumHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server) return true;
        // Not in somebody else's claim
        if (!world.Claims.TryAccess(byPlayer, blockSel.Position, EnumBlockAccessFlags.BuildOrBreak)) return true;

        Block bare = BareBlock(world);
        Item stripped = world.GetItem(item);
        if (bare == null || stripped == null) return true;

        BlockPos pos = blockSel.Position;
        world.BlockAccessor.ExchangeBlock(bare.BlockId, pos);
        world.PlaySoundAt(new AssetLocation("game:sounds/effect/clothrip"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, randomizePitch: true, range: 12);

        // (A knife of copper or better holds an edge as well as a shiv of glass; flint and bone tear)
        CollectibleObject blade = slot.Itemstack.Collectible;
        var stack = new ItemStack(stripped, CleanCutters.Contains(blade.Code.ToString()) || BlockBehaviorToolDrops.IsMetalKnife(blade) ? CleanCutYield : 1);
        // (What does not fit, all of it or the rest, falls at the player's feet)
        byPlayer.InventoryManager.TryGiveItemstack(stack, slotNotifyEffect: true);
        if (stack.StackSize > 0)
        {
            world.SpawnItemEntity(stack, pos.ToVec3d().Add(0.5 + blockSel.Face.Normalf.X, 0.5 + blockSel.Face.Normalf.Y, 0.5 + blockSel.Face.Normalf.Z));
        }

        if (crude)
        {
            // A bare shard of glass does not last
            if (world.Rand.NextDouble() < CrudeCutterBreakChance)
            {
                slot.TakeOut(1);
                slot.MarkDirty();
                world.PlaySoundAt(new AssetLocation("game:sounds/block/glass"), byPlayer.Entity, null, randomizePitch: true, range: 8);
            }
        }
        else
        {
            slot.Itemstack.Collectible.DamageItem(world, byPlayer.Entity, slot);
        }
        return true;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        if (!CanStrip) return System.Array.Empty<WorldInteraction>();
        if (help == null)
        {
            var blades = new List<ItemStack>();
            foreach (string code in new[] { "backrooms:glassshard", "backrooms:glassshiv", "backrooms:scraper", "game:knife-generic-flint" })
            {
                Item blade = world.GetItem(new AssetLocation(code));
                if (blade != null) blades.Add(new ItemStack(blade));
            }
            help = new[]
            {
                new WorldInteraction
                {
                    ActionLangCode = "backrooms:blockhelp-strip",
                    MouseButton = EnumMouseButton.Right,
                    Itemstacks = blades.ToArray(),
                },
            };
        }
        return help;
    }
}
