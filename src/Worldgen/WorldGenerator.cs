using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Worldgen;

/// <summary>
/// Writes the Backrooms into freshly generated chunk columns (the Terrain pass), one cell of the layout to a chunk
/// column. Most levels share one floor height (<see cref="WorldGeometry.FloorFor"/> has the exceptions). Vertically,
/// for the indoor levels: the ground (vanilla's, see <see cref="UndergroundSystem"/>, or plain concrete), the
/// foundations, the floor, the walkable space of the level (3 blocks on Levels 0 and 2, 4 on Level 1), its ceiling,
/// then concrete (with a dusty crawlspace above the Level 0 tiles) up to a mantle cap.
///
/// Threads: the game runs each world generation pass on one thread at a time (a pass per worldgen thread), so
/// <see cref="Generate"/> never runs alongside itself, but it does run alongside <see cref="SpawnBlockEntities"/> (a
/// later pass) and alongside the main thread asking <see cref="ColumnBlock"/> what a block should be. Everything set up
/// in the constructor is only read afterwards; the caches (<see cref="Macro"/>, Level 8's noise, the lighting's cells)
/// take their own locks.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] PatternCodes = { "chevron", "dotted", "cream", "manila", "red" };

    /// <summary>Level 0's papered walls: the index of a pattern's blocks, or -1 for any other wall.</summary>
    private static int Paper(WallPattern pattern) => pattern <= WallPattern.Manila ? (int)pattern : pattern == WallPattern.RedRoom ? 4 : -1;
    private static readonly string[] PierCodes = { "west", "east", "north", "south" };
    private static readonly string[] Sides = { "north", "east", "south", "west" };
    private static readonly string[] Letters = { "a", "b", "c", "d", "e", "f" };

    private const int PartUpper = 0, PartPlain = 1, PartBaseboard = 2, PartRail = 3, PartOutlet = 4;
    private static readonly string[] PartCodes = { "upper", "plain", "baseboard", "rail", "outlet" };

    /// <summary>
    /// The detail props: which block draws each value of <see cref="Tile.Variant"/>. Oriented props come in four
    /// variants by facing; props with kinds pick theirs from <see cref="Tile.Stack"/>. HeadFirst props (beds) are
    /// modelled head to the north, so they turn to face away from their <see cref="Tile.Pier"/>.
    /// </summary>
    private static readonly (ushort Prop, string Code, bool Oriented, string[] Kinds, bool HeadFirst)[] PropTable =
    {
        (Props.CardboardBoxes, "cardboardboxes", false, null, false),
        (Props.Workbench, "workbench", true, null, false),
        (Props.Toolbox, "toolbox", true, null, false),
        (Props.Plywood, "plywood", true, null, false),
        (Props.Tent, "tent", true, null, false),
        (Props.Bedroll, "bedroll", true, null, false),
        (Props.CampTent, "camptent", true, new[] { "nw", "ne", "sw", "se" }, false),
        (Props.SleepingBag, "sleepingbag", true, new[] { "head", "foot" }, true),
        (Props.LongSofa, "longsofa", true, new[] { "l", "r" }, false),
        (Props.Lantern, "camplantern", false, null, false),
        (Props.HospitalBed, "hospitalbed", true, new[] { "head", "foot" }, true),
        (Props.FoldingTable, "foldingtable", false, null, false),
        (Props.FoldingChair, "foldingchair", true, null, false),
        (Props.MedCabinet, "medcabinet", true, null, false),
        (Props.TrafficCone, "trafficcone", false, null, false),
        (Props.WetFloorSign, "wetfloorsign", true, null, false),
        (Props.Pallet, "pallet", false, null, false),
        (Props.TrashCan, "trashcan", false, null, false),
        (Props.PayStation, "paystation", true, null, false),
        (Props.SpeedBump, "speedbump", true, null, false),
        (Props.BurnBarrel, "burnbarrel", false, null, false),
        (Props.Coil, "coilunit", false, null, false),
        (Props.Switchgear, "switchgear", true, null, false),
        (Props.FloorFan, "floorfan", true, null, false),
        (Props.Generator, "generator", true, null, false),
        (Props.CableSpool, "cablespool", false, null, false),
        (Props.ControlDesk, "controldesk", true, null, false),
        (Props.Conveyor, "conveyor", true, new[] { "empty", "box" }, false),
        (Props.Candelabra, "candelabra", false, null, false),
        (Props.AngelStatue, "angelstatue", true, null, false),
        (Props.FloorCable, "floorcable", true, null, false),
        (Props.PipeStack, "pipestack", true, null, false),
        (Props.GaugeFrame, "gaugeframe", true, new[] { "gauges", "manifold", "valve", "sightglass" }, false),
        (Props.PressureTank, "pressuretank", true, new[] { "plain", "valved" }, false),
        (Props.RustMachine, "rustmachine", true, new[] { "pump", "governor" }, false),
        (Props.FloorLever, "floorlever", true, new[] { "single", "double" }, false),
        (Props.Tram, "deadtram", true, new[] { "front", "rear" }, false),
        (Props.TramWagon, "tramwagon", true, null, false),
        (Props.CandleStubs, "candlestubs", false, null, false),
        (Props.Ficus, "ficus", false, null, false),
        (Props.ChairStack, "chairstack", false, null, false),
        (Props.Copier, "copier", true, null, false),
        (Props.OfficeBookshelf, "officebookshelf", true, null, false),
        (Props.ServerRack, "serverrack", true, null, false),
        (Props.KitchenCounter, "kitchencounter", true, new[] { "plain", "sink", "micro" }, false),
        (Props.Fridge, "fridge", true, null, false),
        (Props.RoundTable, "roundtable", false, null, false),
        (Props.ReceptionDesk, "receptiondesk", true, null, false),
        (Props.Wastebasket, "wastebasket", false, null, false),
        (Props.CoatStand, "coatstand", false, null, false),
        (Props.TippedChair, "officechairtipped", true, null, false),
        (Props.Bench, "bench", true, null, false),
        (Props.ConsoleTable, "consoletable", true, null, false),
        (Props.HotelBookshelf, "hotelbookshelf", true, null, false),
        (Props.CurioCabinet, "curiocabinet", true, null, false),
        (Props.LuggageCart, "luggagecart", false, null, false),
        (Props.ServiceTrolley, "servicetrolley", true, null, false),
        (Props.Radiator, "radiator", true, null, false),
        (Props.WritingDesk, "writingdesk", true, null, false),
        (Props.HotelChair, "hotelchair", true, null, false),
        (Props.FloorLamp, "floorlamp", false, null, false),
        (Props.Suitcase, "suitcase", true, null, false),
        (Props.CoffeeTable, "coffeetable", false, null, false),
        (Props.GrandfatherClock, "grandfatherclock", true, null, false),
        (Props.FrontDesk, "hotelreception", true, null, false),
        (Props.AshtrayStand, "ashtraystand", false, null, false),
        (Props.DiningTable, "diningtable", false, null, false),
        (Props.GrandPiano, "grandpiano", true, null, false),
        (Props.CoalPile, "coalpile", false, null, false),
        (Props.CoalBin, "coalbin", false, null, false),
        (Props.Tripwire, "tripwire", true, null, false),
        (Props.CafeTable, "cafetable", false, null, false),
        (Props.CafeChair, "cafechair", true, null, false),
        (Props.SnackCounter, "snackcounter", true, new[] { "plain", "register", "display" }, false),
        (Props.Stove, "stove", true, null, false),
        (Props.Fryer, "fryer", true, null, false),
        (Props.SnackShelf, "snackshelf", true, null, false),
        (Props.SnackVending, "snackvending", true, null, false),
        (Props.DrinkFridge, "drinkfridge", true, null, false),
        (Props.VendingPile, "vendingpile", true, new[] { "standing", "toppled", "ontop" }, false),
        (Props.BonePile, "bonepile", false, null, false),
        (Props.MothHive, "mothhive", false, null, false),
        (Props.ScrapMetal, "scrapmetal", false, null, false),
        (Props.JawSkeleton, "jawskeleton", true, null, false),
        (Props.Ribcage, "ribcage", true, null, false),
        (Props.Backpack, "backpack", true, null, false),
        (Props.WreckCrate, "wreckcrate", false, null, false),
        (Props.MegMarker, "megmarker", true, null, false),
        (Props.RoadLamp, "roadlamp", false, null, false),
        (Props.GlowcapRed, "glowcapred", true, new[] { "floor", "wall" }, false),
        (Props.GlowcapMixed, "glowcapmixed", true, new[] { "floor", "wall" }, false),
        (Props.StoneHand, "stonehand", true, null, false),
        (Props.StoneStapler, "stonestapler", false, null, false),
        (Props.Tv, "tv", true, null, false),
        (Props.Bathtub, "bathtub", true, new[] { "head", "foot" }, true),
        (Props.Toilet, "toilet", true, null, false),
        (Props.Dresser, "dresser", true, null, false),
        (Props.Streetlight, "streetlight", true, new[] { "on", "off", "flicker" }, false),
        (Props.Mailbox, "mailbox", true, null, false),
        (Props.SeedSacks, "seedsacks", false, null, false),
        (Props.ToolShelf, "toolshelf", true, null, false),
        (Props.PantryShelf, "pantryshelf", true, null, false),
        (Props.KitchenCabinet, "kitchencabinet", true, null, false),
        (Props.FieldGate, "fieldgate", true, null, false),
        (Props.FeedTrough, "feedtrough", true, null, false),
        (Props.ToolRack, "toolrack", true, null, false),
        (Props.NailBarrel, "nailbarrel", false, null, false),
        (Props.FireHydrant, "firehydrant", true, null, false),
        (Props.StopSign, "stopsign", true, null, false),
        (Props.WheelieBin, "wheeliebin", true, null, false),
        (Props.BasketballHoop, "basketballhoop", true, null, false),
        (Props.SwingSet, "swingset", true, null, false),
        (Props.Grill, "grill", true, null, false),
        (Props.Laundry, "laundry", true, new[] { "washer", "dryer" }, false),
        (Props.ToyBox, "toybox", true, null, false),
        (Props.Doghouse, "doghouse", true, null, false),
        (Props.PatioChair, "patiochair", true, null, false),
        (Props.SuburbSign, "suburbsign", false, new[] { "elm", "oak", "maple", "pine", "cedar", "birch", "walnut", "ash" }, false),
        (Props.CitySign, "citysign", true, null, false),
        (Props.Scarecrow, "scarecrow", true, null, false),
        (Props.PowerPole, "powerpole", true, null, false),
        (Props.Plough, "plough", true, null, false),
        (Props.WaterPump, "waterpump", false, null, false),
        (Props.Tractor, "tractor", false, null, false),
        (Props.HayRoll, "hayroll", true, null, false),
        (Props.WaterTrough, "watertrough", true, null, false),
        (Props.FallenGate, "fallengate", true, null, false),
        (Props.IceMachine, "icemachine", true, null, false),
        (Props.RoomServiceTray, "roomservicetray", true, null, false),
        (Props.LaundryCart, "laundrycart", true, null, false),
        (Props.Flashlight, "flashlight", true, null, false),
        (Props.Driftwood, "driftwood", true, null, false),
        (Props.Buoy, "buoy", false, null, false),
        (Props.TrafficLight, "trafficlight", true, new[] { "dead", "red", "amber" }, false),
        (Props.BusShelter, "busshelter", true, null, false),
        (Props.NewsBox, "newsbox", true, null, false),
        (Props.StreetSign, "streetsign", true, null, false),
        (Props.ParkingMeter, "parkingmeter", true, null, false),
        (Props.PhoneBooth, "phonebooth", true, null, false),
        (Props.VendorCart, "vendorcart", true, null, false),
        (Props.ClothesRack, "clothesrack", true, null, false),
        (Props.ShoppingCart, "shoppingcart", true, null, false),
        (Props.Pew, "pew", true, null, false),
        (Props.Dumpster, "dumpster", true, null, false),
        (Props.TrashBags, "trashbags", false, null, false),
        (Props.AcUnit, "acunit", true, null, false),
        (Props.WaterTank, "watertank", false, null, false),
        (Props.Antenna, "antenna", false, null, false),
        (Props.Postbox, "postbox", true, null, false),
        (Props.Billboard, "billboard", true, new[] { "almond", "city", "diner", "stripped" }, false),
        (Props.AdPillar, "adpillar", false, new[] { "a", "b", "c" }, false),
        (Props.Trolley, "trolley", true, null, false),
        (Props.MachineParts, "machineparts", true, null, false),
        (Props.TrafficSign, "trafficsign", true, new[] { "oneway", "noentry", "exit" }, false),
        // Level 37
        (Props.PoolLadder, "poolladder", true, null, false),
        (Props.EpsomCrust, "epsomcrust", false, null, false),
        (Props.LostThing, "lostthing", true, new[] { "towel", "flipflop", "noodle" }, false),
        (Props.RedSprout, "redsprout", false, null, false),
        // Level 94
        (Props.SirenPole, "sirenpole", false, null, false),
        (Props.MilkVan, "milkvan", true, null, false),
        (Props.OldCar, "oldcar", true, new[] { "black", "green", "maroon" }, false),
        (Props.NoOutletSign, "nooutletsign", true, null, false),
        (Props.Icebox, "icebox", true, null, false),
        (Props.RadioCabinet, "radiocabinet", true, null, false),
        (Props.RotaryPhone, "rotaryphone", true, null, false),
        (Props.FurniturePile, "furniturepile", true, new[] { "chairs", "tables", "drawers", "mixed" }, false),
        (Props.TwilightGate, "twilightgate", true, null, false),
        (Props.BallPit, "ballpit", false, null, false),
        (Props.Arcade, "arcade", true, null, false),
        (Props.Diorama, "diorama", false, null, false),
        (Props.StudioCamera, "studiocamera", true, null, false),
        (Props.Easel, "easel", true, null, false),
        (Props.ThroneTable, "thronetable", false, null, false),
        (Props.TrialChair, "trialchair", true, null, false),
        (Props.KingStatue, "kingstatue", true, null, false),
        (Props.Slide, "slide", true, null, false),
        (Props.TippedCar, "tippedcar", true, new[] { "black", "green" }, false),
        // Level Fun's ways in from other levels (its own props are drawn in WorldGenerator.Fun.cs): the party
        // dressing of a Level 0 cell and of a Level 1 stair core, and the poster that takes you
        (Props.FunPosterTrap, "fun-poster-trap", true, null, false),
        (Props.FunSmiley, "fun-smiley", true, new[] { "1", "2", "3", "4" }, false),
        (Props.FunBalloonsFloor, "fun-balloons-floor", false, new[] { "mixed", "pastel" }, false),
        (Props.FunBalloonTied, "fun-balloon-tied", false, new[] { "red", "yellow", "blue", "green", "pink" }, false),
        (Props.FunConfetti, "fun-confetti", false, null, false),
        // Level !(its two-block-tall shelving and curtain are drawn in WorldGenerator.Run.cs)
        (Props.RunGurney, "run-gurney", true, new[] { "head", "foot" }, true),
        (Props.RunWheelchair, "run-wheelchair", true, null, false),
        (Props.RunIvStand, "run-ivstand", true, null, false),
        (Props.RunChairs, "run-chairs", true, null, false),
        (Props.RunCrashCart, "run-crashcart", true, null, false),
        (Props.RunShelfFallen, "run-shelf", true, new[] { "fallen-a", "fallen-b" }, false),
        (Props.RunToyCar, "run-toycar", true, null, false),
        (Props.RunBoxes, "run-boxes", true, null, false),
        (Props.RunCord, "run-cord", true, null, false),
        (Props.RunSheets, "run-sheets", true, null, false),
        (Props.RunRemains, "run-remains", true, null, false),
        (Props.RunTray, "run-tray", true, new[] { "bar", "water" }, false),
        (Props.RunBedside, "run-bedside", true, null, false),
        (Props.RunSafeShelf, "run-safeshelf", true, null, false),
        (Props.RunSafeCot, "run-safecot", true, new[] { "head", "foot" }, true),
        (Props.RunDebris, "run-debris", true, null, false),
        // The End (its tall props are drawn in WorldGenerator.End.cs; this row draws the low shelving of Level 11's closed bookstore)
        (Props.EndShelf, "end-shelf", true, new[] { "empty-lower", "books-lower", "dusty-lower", "endpanel-lower", "leaning-lower" }, false),
    };

    /// <summary>Wall decoration families: one block type per wall material.</summary>
    private static readonly Dictionary<string, WallPattern> DecorFamilies = new()
    {
        ["l1deco"] = WallPattern.WhiteBlock, ["concretedeco"] = WallPattern.Concrete, ["pillardeco"] = WallPattern.Pillar,
        ["l3decoglazed"] = WallPattern.GlazedTile, ["l3decobrick"] = WallPattern.RedBrick, ["l3decocinder"] = WallPattern.Cinder,
        ["l3decostone"] = WallPattern.Stone, ["officedeco"] = WallPattern.Drywall, ["hoteldeco"] = WallPattern.Hotel,
        ["plasterdeco"] = WallPattern.Plaster, ["l6deco"] = WallPattern.L6Wall, ["snackdeco"] = WallPattern.SnackMall,
        ["housedeco-floral"] = WallPattern.InteriorFloral, ["housedeco-stripe"] = WallPattern.InteriorStripe,
        ["housedeco-beige"] = WallPattern.InteriorBeige, ["housedeco-green"] = WallPattern.InteriorGreen,
        ["storefrontdeco"] = WallPattern.CityStorefront, ["citydeco"] = WallPattern.CityPlaster, ["subwaydeco"] = WallPattern.SubwayTile,
        ["concretecam"] = WallPattern.Concrete, ["whitecam"] = WallPattern.WhiteBlock,
        ["l3plaqueglazed"] = WallPattern.GlazedTile, ["l3plaquebrick"] = WallPattern.RedBrick, ["l3plaquecinder"] = WallPattern.Cinder,
    };

    private static readonly Dictionary<string, byte> DecorCodes = BuildDecorCodes();

    private static Dictionary<string, byte> BuildDecorCodes()
    {
        var codes = new Dictionary<string, byte>
        {
            ["powerbox"] = Decor.PowerBox, ["breaker"] = Decor.Breaker, ["outlet"] = Decor.Outlet, ["extinguisher"] = Decor.Extinguisher,
            ["alarm"] = Decor.Alarm, ["hosecab"] = Decor.HoseCabinet, ["levelsign"] = Decor.LevelSign, ["stairsign"] = Decor.StairSign,
            ["note"] = Decor.Note, ["graffiti"] = Decor.Graffiti, ["pipes"] = Decor.Pipes, ["standpipe"] = Decor.Standpipe,
            ["dangersign"] = Decor.DangerSign, ["gauges"] = Decor.Gauges, ["knifeswitch"] = Decor.KnifeSwitch,
            ["junctionbox"] = Decor.JunctionBox, ["sparkoutlet"] = Decor.SparkOutlet, ["bulkhead"] = Decor.Bulkhead,
            ["alarmbell"] = Decor.AlarmBell, ["wallcables"] = Decor.WallCables, ["risers"] = Decor.Risers, ["purpified"] = Decor.Purpified,
            ["fountain"] = Decor.Fountain, ["clock"] = Decor.Clock, ["whiteboard"] = Decor.Whiteboard, ["corkboard"] = Decor.Corkboard,
            ["whiteboardl"] = Decor.WhiteboardLeft, ["whiteboardr"] = Decor.WhiteboardRight,
            ["evacmap"] = Decor.EvacMap, ["switch"] = Decor.LightSwitch, ["frameghost"] = Decor.FrameGhost, ["phone"] = Decor.Phone,
            ["callbutton"] = Decor.CallButton, ["mirror"] = Decor.Mirror, ["speaker"] = Decor.Speaker, ["housephone"] = Decor.HousePhone,
            ["firehose"] = Decor.FireHose, ["keyrack"] = Decor.KeyRack, ["callplate"] = Decor.CallPlate, ["landscape"] = Decor.Landscape,
            ["pipesv"] = Decor.PipesV, ["valve"] = Decor.Valve, ["pipecluster"] = Decor.PipeCluster,
            ["megexit"] = Decor.MegExit, ["megcross"] = Decor.MegCross, ["meglogo"] = Decor.MegLogo, ["handprints"] = Decor.Handprints,
            ["scratches"] = Decor.Scratches, ["signburger"] = Decor.SignBurger, ["signpizza"] = Decor.SignPizza, ["signtaco"] = Decor.SignTaco,
            ["signdonut"] = Decor.SignDonut, ["menuboard"] = Decor.MenuBoard, ["mallmap"] = Decor.MallMap,
            ["familyphoto"] = Decor.FamilyPhoto, ["housepainting"] = Decor.HousePainting, ["houseclock"] = Decor.HouseClock,
            ["housemirror"] = Decor.HouseMirror,
            ["signdiner"] = Decor.SignDiner, ["signgrocery"] = Decor.SignGrocery, ["signpharmacy"] = Decor.SignPharmacy,
            ["signhardware"] = Decor.SignHardware, ["signlaundry"] = Decor.SignLaundry, ["signclothing"] = Decor.SignClothing,
            ["signhotel"] = Decor.SignHotel, ["signoffices"] = Decor.SignOffices, ["signapartments"] = Decor.SignApartments,
            ["signparking"] = Decor.SignParking, ["signmuseum"] = Decor.SignMuseum, ["signfarmacia"] = Decor.SignFarmacia,
            ["signlavanderia"] = Decor.SignLavanderia, ["signbodega"] = Decor.SignBodega,
            ["mailboxes"] = Decor.Mailboxes, ["directory"] = Decor.Directory, ["missingposter"] = Decor.MissingPoster,
            ["camera"] = Decor.Camera, ["deadswitch"] = Decor.DeadSwitch, ["plaque"] = Decor.Plaque,
            ["stationsign"] = Decor.StationSign, ["subwaymap"] = Decor.SubwayMap, ["subwaylamp"] = Decor.SubwayLamp, ["subwayad"] = Decor.SubwayAd,
        };
        for (int i = 0; i < 4; i++)
        {
            codes[$"painting{i}"] = (byte)(Decor.Painting + i);
            codes[$"banner{i}"] = (byte)(Decor.Banner + i);
        }
        for (int i = 0; i < 8; i++) codes[$"roomsign{i}"] = (byte)(Decor.RoomSign + i);
        for (int i = 0; i < 3; i++) codes[$"poster{i}"] = (byte)(Decor.Poster + i);
        for (int i = 0; i < 8; i++) codes[$"gallery{i}"] = (byte)(Decor.Gallery + i);
        return codes;
    }

    /// <summary>Decorations whose code is shared by several families but means something different in each.</summary>
    private static byte DecorFor(string family, string code) => (family, code) switch
    {
        ("officedeco", "extinguisher") => Decor.ExtCabinet,
        ("officedeco", "alarm") => Decor.FireAlarm,
        ("officedeco", "stairsign") => Decor.OfficeStairSign,
        ("hoteldeco", "clock") => Decor.HotelClock,
        ("plasterdeco", "gauges") => Decor.PlasterGauges,
        _ => DecorCodes.TryGetValue(code, out byte d) ? d : (byte)0,
    };

    private readonly ICoreServerAPI api;
    private readonly int chunkSize;
    private readonly WorldLayout layout;
    private readonly WorldLighting lighting;
    public readonly WorldGeometry Geometry;

    /// <summary>Every block of this mod by code path, for the many detail blocks looked up by name.</summary>
    private readonly Dictionary<string, int> modBlocks = new();

    // Shared
    private readonly int mantleId, concreteId, waterId, boxId, boxTornId, crateOpenId, groundFallbackId;
    /// <summary>Chalk marks by symbol (left, right, cross, circle) and by the side of the wall they are on (north, east, south, west).</summary>
    private readonly int[,] chalkIds = new int[4, 4];
    // (Sized for every value of the enums and of Props, the reserved blocks of the far places (ids 14-20) included)
    private readonly int[] floorIds = new int[256];
    private readonly int[] overheadIds = new int[256];
    /// <summary>Most kinds a prop may come in (the second index of <see cref="propIds"/>).</summary>
    private const int MaxPropKinds = 8;
    private readonly int[,,] propIds = new int[Props.Limit, MaxPropKinds, 4];
    /// <summary>How many kinds each prop comes in, and whether it is modelled head to the north (beds, baths).</summary>
    private readonly byte[] propKinds = new byte[Props.Limit];
    private readonly bool[] propHeadFirst = new bool[Props.Limit];
    /// <summary>Wall decorations: [wall pattern, decoration, height above the floor, facing].</summary>
    private readonly int[,,,] decorIds = new int[PatternCount, Decor.Limit, 6, 4];
    /// <summary>The hotel's gilt mirror on a plain cream wall block, one per facing (layout version 9 on; before it the mirror hung on the red framed panel).</summary>
    private readonly int[] hotelMirrorPlainIds = new int[4];
    private static readonly int PatternCount = MaxPattern() + 1;

    private static int MaxPattern()
    {
        int max = 0;
        foreach (WallPattern p in Enum.GetValues(typeof(WallPattern))) max = Math.Max(max, (int)p);
        return max;
    }
    private readonly int[,] exitLintelIds = new int[3, 2]; // concrete, white block, drywall x axis (we, ns)
    /// <summary>The block entity class of every block by id (null for none), so placing a block never looks it up.</summary>
    private readonly string[] entityClassById;

    // Level 0
    private readonly int ceilingTileId, lightOnId, lightLitId, lightOffId, lampDimId, lightFlickerId;
    private readonly int[,] wallIds = new int[5, 5];
    private readonly int[] archIds = new int[4];
    /// <summary>Level 0 walls where an arched area meets a papered one: by which faces are pale (bit 0 north .. 3 west), upper or baseboard.</summary>
    private readonly int[,] paperJoinIds = new int[16, 2];

    // Level 1
    private readonly int concreteWallId, concreteWallDamagedId, pillarId, pillarBaseId, pillarLightId, concreteCeilingId, crateId;
    private readonly int whiteUpperId, whiteBaseId, whiteLintelId, metalDoorLowerId, metalDoorUpperId;
    private readonly int[] pillarLetterIds = new int[6];
    private readonly int[,] hangingLightIds = new int[3, 2]; // state (on, off, flicker) x axis (we, ns)
    private readonly int[,] fireDoorIds = new int[2, 4]; // leaf (left, right) x facing
    private readonly int bulbOnId, conduitXId, conduitZId, dripXId, dripZId;
    private readonly int[,] conduitEndIds = new int[4, 2]; // side (east, north, west, south) x kind (cap, box), see ConduitBlock
    private readonly int[,] conduitStubIds = new int[2, 4]; // axis (we, ns) x ends (cc, cb, bc, bb)
    private readonly int[] shelfIds = new int[4];
    private readonly int[] stairIds = new int[4];
    private readonly int wheelStopId, carColliderId;
    private readonly int[,] carIds = new int[4, 4]; // colour x facing (north, south, east, west)
    /// <summary>Level 1's wrecks of the same cars (flat tyres, broken glass, rust; the black one burnt out), as <see cref="carIds"/>.</summary>
    private readonly int[,] carWreckIds = new int[4, 4];

    // Level 2
    private readonly int tunnelFloorId, tunnelCeilingId, drumId;
    private int tunnelDoorLowerId, tunnelDoorUpperId, lampRedId, ceilingFanId, almondSeepId;
    private readonly int pipeRunXId, pipeRunZId, pipeHubId, pipeLeakXId, pipeLeakZId, tarRunXId, tarRunZId, tarHubId;
    private readonly int[,] tunnelLightIds = new int[4, 4]; // state (white, warm, off, flicker) x pipes alongside (we, ns, hub, none)
    private readonly int[] cabinetIds = new int[4];
    /// <summary>
    /// (Layout version 9) Level 2's machine cabinets with their feed pipe straight up, and the pipe above them into the
    /// overhead bundle, by facing; and the tunnel walls with fittings that lead somewhere (tunnelfitting: a wall cabinet's
    /// conduits up into the ceiling, a gate valve in the wall pipes, a valve at a riser's foot).
    /// </summary>
    private readonly int[] cabinetFeedIds = new int[4], feedPipeIds = new int[4];
    private readonly int tunnelMachineryTopId, tunnelPipesValveId, tunnelRiserValveId;
    /// <summary>Level 2's tunnel walls, by <see cref="TunnelWallTypes"/>.</summary>
    private readonly int[] tunnelWallIds = new int[TunnelWallTypes.Length];
    private static readonly string[] TunnelWallTypes = { "plain", "machinery", "brick", "warning", "pipes", "riser", "riserjoint", "valve", "machinerybase", "pipesjoint", "pipesbracket" };
    private const int TunnelPlain = 0, TunnelMachinery = 1, TunnelBrick = 2, TunnelWarning = 3, TunnelPipes = 4, TunnelRiser = 5,
        TunnelRiserJoint = 6, TunnelValve = 7, TunnelMachineryBase = 8, TunnelPipesJoint = 9, TunnelPipesBracket = 10;
    /// <summary>Level 2's tramway rails: along X, along Z, crossing.</summary>
    private readonly int[] tramRailIds = new int[3];
    /// <summary>Level 2's steel doors in white, grey and cream paint (lower, upper); 0 where the block is missing.</summary>
    private readonly int[,] tunnelDoorPaintIds = new int[3, 2];

    // Level 3
    private readonly int dustyFloorId, plasterCeilingId, transformerId, windowGlowId, manholeId, rungsId, sanctumStoneId;
    /// <summary>A Level 3 manhole's ladder from layout version 9: [top left, top right, left, right][side it is on]; and the half step out of the water.</summary>
    private readonly int[,] manholeLadderIds = new int[4, 4];
    private readonly int tunnelStepId;
    private readonly Dictionary<WallPattern, int> l3WallIds = new();
    private readonly Dictionary<(WallPattern, ushort), int> l3FixtureIds = new();
    /// <summary>A Sanctum's vaulted ceiling: a plain vault cell, and one with a boss.</summary>
    private readonly int[] sanctumCeilingIds = new int[2];
    /// <summary>Level 3's wall pipes with a flanged joint or a bracket, by wall and <see cref="WallPipeRun"/>.</summary>
    private readonly Dictionary<(WallPattern, int), int> l3PipeRunIds = new();
    /// <summary>
    /// The wall pipes of Levels 2 and 3 turning corners and ending (wallpipecorner), by wall (0 Level 2's concrete,
    /// 1-3 Level 3's glazed tile, brick, cinder) and <see cref="WallPipeCorner"/>'s key; 0 where there is no such block.
    /// </summary>
    private readonly int[,] wallPipeCornerIds = new int[4, 1 << 12];
    /// <summary>
    /// (Layout version 9) Level 3's fittings that lead somewhere (l3fitting), by wall (glazed tile, brick, cinder): the
    /// wall pipes with their pressure gauges in them, and the junction box a panel's conduit runs up into (with a cable
    /// run coming into it from neither side, its east, its west or both, as the box faces north).
    /// </summary>
    private readonly int[] l3GaugePipeIds = new int[3];
    private readonly int[,] l3PanelBoxIds = new int[3, 4];
    /// <summary>
    /// (Layout version 9) Level 3's cable runs ending in a gland in the wall, by wall, by end (the decoration's east end,
    /// its west end, both) and facing.
    /// </summary>
    private readonly int[,,] l3CableEndIds = new int[3, 3, 4];
    /// <summary>
    /// (Layout version 9) The ends of a crossing of cables on Level 3's floor (floorcableend): a cable box, and its cables
    /// laid for a wall to the east or south; a rise into the fitting on the wall, and the same mirrored; by facing.
    /// </summary>
    private readonly int[,] floorCableEndIds = new int[4, 4];
    private readonly int cableXId, cableZId, cableHubId, cableDroopXId, cableDroopZId, cableGapXId, cableGapZId;
    private readonly int[,] cableLightIds = new int[3, 5]; // state (warm, off, flicker) x axis (we, ns, no tray, on tar pipes we, ns)
    /// <summary>Overhead runs ending with open space beyond them, by the side they end on (north, east, south, west): Level 2's
    /// bundles, Level 3's tar bundles and cable trays.</summary>
    private readonly int[] pipeEndIds = new int[4], tarEndIds = new int[4], cableEndIds = new int[4], dripEndIds = new int[4];
    /// <summary>A length of overhead bundle on its own, capped at both ends (along X, along Z): Level 2's, the tar pipes, a leaking one.</summary>
    private readonly int[] pipeStubIds = new int[2], tarStubIds = new int[2], dripStubIds = new int[2];
    private readonly int[] roomSignIds = new int[8];
    private readonly int barsWeId, barsNsId;

    // Level 4
    private readonly int officeWallId, officeWallBaseId, officeWindowId, officeGlassId, officeCeilingId, confTableId, elevatorLowerId, elevatorUpperId;
    private readonly int officeDoorLowerId, officeDoorUpperId;
    private readonly int[] officeWindowIds = new int[3]; // open, blacked out, blinds
    private readonly int[] officeLightIds = new int[4]; // on, lit, off, flicker
    private readonly int partitionWeId, partitionNsId;
    private readonly int[] deskIds = new int[4], chairIds = new int[4], filingIds = new int[4], vendingIds = new int[4], coolerIds = new int[4];
    /// <summary>Two-wide elevators: [wall (drywall, hotel / cage: hotel, plaster), part (lower, upper, header), leaf (left, right), facing].</summary>
    private readonly int[,,,] liftIds = new int[2, 3, 2, 4], cageIds = new int[2, 3, 2, 4];

    // Level 5
    private readonly int wainscotId, panelId, friezeId, marbleId, plasterId, creamCeilingId, chandelierId;
    /// <summary>The grand rooms' coffered ceiling: a plain coffer, a beam along X, a beam along Z, two beams crossing.</summary>
    private readonly int[] grandCeilingIds = new int[4];
    private readonly int sconceId, portraitId, beverlyId, staffSignId, doorLowerId, palmId, mahjongId, turntableId;
    private readonly int bulbOffId;
    /// <summary>The upper half of a hotel door by its plaque: 201-208, then (layout 5) a blank plate and 666.</summary>
    private readonly int[] doorUpperIds = new int[10];
    /// <summary>A front hall's grand staircase (layout 5): marble steps, with a runner up the middle one (kind 0), by the way they climb.</summary>
    private readonly int[,] hotelStairIds = new int[2, 4];
    private readonly int[] domeIds = new int[3]; // on, off, flicker
    private readonly int[] bedHeadIds = new int[4], bedFootIds = new int[4], nightstandIds = new int[4], wardrobeIds = new int[4];
    private readonly int[] wingChairIds = new int[4], sofaIds = new int[4], boilerIds = new int[4], furnaceIds = new int[4];
    /// <summary>(Layout version 9) Level 5's boiler plant: the header by kind (run, flue, both), end (mid, west, east) and side (north, south); the risers by part (furnace2, steam2, both3, flue3) and facing; the bay walls' top block by side.</summary>
    private readonly int[,,] plantHeaderIds = new int[3, 3, 2];
    private readonly int[,] plantRiserIds = new int[4, 4];
    private readonly int[] plantThruIds = new int[2];

    /// <summary>
    /// Block entities to spawn for blocks placed by the terrain pass (flickering lights, dispensers), by column, until
    /// the next pass spawns them. A column with none has <see cref="NoEntities"/>, so a column missing from here is one
    /// whose note was lost (see <see cref="SpawnBlockEntities"/>).
    /// </summary>
    private readonly ConcurrentDictionary<long, List<(BlockPos Pos, string EntityClass)>> pendingEntities = new();
    private static readonly List<(BlockPos Pos, string EntityClass)> NoEntities = new();
    /// <summary>
    /// How many columns may wait between the two passes before the notes are dropped (they are found again from the
    /// blocks). Columns generated only as far as the terrain, at the edge of what is loaded, can wait a long time.
    /// </summary>
    private const int PendingLimit = 4096;

    public WorldGenerator(ICoreServerAPI api, WorldLayout layout)
    {
        this.api = api;
        this.layout = layout;
        seed = (ulong)api.World.Seed;
        chunkSize = api.WorldManager.ChunkSize;
        Geometry = new WorldGeometry(api.WorldManager.MapSizeY);

        IList<Block> blocks = api.World.Blocks;
        entityClassById = new string[blocks.Count];
        for (int i = 0; i < blocks.Count; i++)
        {
            Block block = blocks[i];
            if (block?.Code != null && block.Code.Domain == "backrooms") modBlocks[block.Code.Path] = block.BlockId;
            entityClassById[i] = block?.EntityClass;
        }

        mantleId = BlockId("game:mantle");
        groundFallbackId = BlockId("game:rock-granite");
        concreteId = BlockId("backrooms:concrete");
        waterId = BlockId("game:water-still-7");
        boxId = BlockId("backrooms:supplybox");
        boxTornId = BlockId("backrooms:supplybox-torn");
        crateOpenId = BlockId("backrooms:crate-open");
        string[] sides = { "north", "east", "south", "west" };
        for (int symbol = 0; symbol < 4; symbol++)
            for (int side = 0; side < 4; side++) chalkIds[symbol, side] = BlockId($"backrooms:chalkmark-{ChalkBits.Symbols[symbol]}-{sides[side]}");

        floorIds[(int)FloorKind.Carpet] = BlockId("backrooms:carpet-normal");
        floorIds[(int)FloorKind.Stained] = BlockId("backrooms:carpet-stained");
        floorIds[(int)FloorKind.Soaked] = BlockId("backrooms:carpet-soaked");
        floorIds[(int)FloorKind.Wood] = BlockId("game:planks-aged-ud");
        floorIds[(int)FloorKind.Concrete] = BlockId("backrooms:concretefloor-plain");
        floorIds[(int)FloorKind.ConcreteWet] = BlockId("backrooms:concretefloor-wet");
        floorIds[(int)FloorKind.ConcreteLineNS] = BlockId("backrooms:concretefloor-linens");
        floorIds[(int)FloorKind.ConcreteLineWE] = BlockId("backrooms:concretefloor-linewe");
        floorIds[(int)FloorKind.ConcreteDashWE] = BlockId("backrooms:concretefloor-dashwe");
        floorIds[(int)FloorKind.ConcreteDashNS] = BlockId("backrooms:concretefloor-dashns");
        floorIds[(int)FloorKind.Dusty] = BlockId("backrooms:dustyfloor");
        floorIds[(int)FloorKind.OfficeCarpet] = BlockId("backrooms:officecarpet-plain");
        floorIds[(int)FloorKind.OfficeCarpetGhost] = BlockId("backrooms:officecarpet-ghost");
        floorIds[(int)FloorKind.HotelCarpet] = BlockId("backrooms:hotelcarpet-damask");
        floorIds[(int)FloorKind.HotelMaroon] = BlockId("backrooms:hotelcarpet-maroon");
        floorIds[(int)FloorKind.HotelLobby] = BlockId("backrooms:hotelcarpet-lobby");
        floorIds[(int)FloorKind.HotelWood] = BlockId("backrooms:hotelwood");
        floorIds[(int)FloorKind.L1Hall] = Id("l1hallfloor-plain");
        floorIds[(int)FloorKind.ParkArrowN] = Id("parkfloor-arrown");
        floorIds[(int)FloorKind.ParkArrowE] = Id("parkfloor-arrowe");
        floorIds[(int)FloorKind.ParkArrowS] = Id("parkfloor-arrows");
        floorIds[(int)FloorKind.ParkArrowW] = Id("parkfloor-arroww");
        floorIds[(int)FloorKind.ParkOil] = Id("parkfloor-oil");
        floorIds[(int)FloorKind.ParkDrain] = Id("parkfloor-drain");
        floorIds[(int)FloorKind.Grate] = Id("l3floor-grate");
        floorIds[(int)FloorKind.L3Hazard] = Id("l3floor-hazard");
        floorIds[(int)FloorKind.L3Stone] = Id("l3floor-stone");
        floorIds[(int)FloorKind.SanctumCarpet] = Id("l3floor-carpet");
        floorIds[(int)FloorKind.OfficePapers] = Id("officecarpetalt-papers");
        floorIds[(int)FloorKind.OfficeStain] = Id("officecarpetalt-stain");
        floorIds[(int)FloorKind.HotelMarble] = Id("hotelfloor-marble");
        floorIds[(int)FloorKind.HotelRunnerNS] = Id("hotelfloor-runnerns");
        floorIds[(int)FloorKind.HotelRunnerWE] = Id("hotelfloor-runnerwe");
        floorIds[(int)FloorKind.HotelRug] = Id("hotelfloor-rug");
        InitDeep();
        InitInterior();
        InitSigns();

        overheadIds[Overheads.ExitSignWE] = Id("exithanging-we");
        overheadIds[Overheads.ExitSignNS] = Id("exithanging-ns");
        overheadIds[Overheads.ClearanceWE] = Id("clearancebar-north");
        overheadIds[Overheads.ClearanceNS] = Id("clearancebar-east");
        overheadIds[Overheads.SprinklerWE] = Id("sprinkler-north");
        overheadIds[Overheads.SprinklerNS] = Id("sprinkler-east");
        overheadIds[Overheads.WireDroop] = Id("wiredroop");
        overheadIds[Overheads.CeilingVent] = Id("officeceilingalt-vent");
        overheadIds[Overheads.CeilingSprinkler] = Id("officeceilingalt-sprinkler");
        overheadIds[Overheads.CeilingStain] = Id("officeceilingalt-stain");

        foreach (var (prop, code, oriented, kinds, headFirst) in PropTable)
        {
            propKinds[prop] = (byte)(kinds?.Length ?? 1);
            propHeadFirst[prop] = headFirst;
            for (int k = 0; k < (kinds?.Length ?? 1); k++)
            {
                string kind = kinds != null ? "-" + kinds[k] : "";
                for (int f = 0; f < 4; f++) propIds[prop, k, f] = Id(oriented ? $"{code}{kind}-{Sides[f]}" : $"{code}{kind}");
            }
        }
        foreach (var (family, decor, rel, state) in DetailBlocks.Decorations)
        {
            byte d = DecorFor(family, decor);
            if (d == 0 || !DecorFamilies.TryGetValue(family, out WallPattern pattern)) continue;
            for (int f = 0; f < 4; f++) decorIds[(int)pattern, d, rel, f] = Id($"{family}-{state}-{Sides[f]}");
        }
        for (int f = 0; f < 4; f++) hotelMirrorPlainIds[f] = Id($"hoteldeco-mirrorplain-{Sides[f]}");
        string[] exitMaterials = { "concrete", "whiteblock", "drywall" };
        for (int m = 0; m < 3; m++)
        {
            exitLintelIds[m, 0] = Id($"exitlintel-{exitMaterials[m]}-we");
            exitLintelIds[m, 1] = Id($"exitlintel-{exitMaterials[m]}-ns");
        }
        string[] lifts = { "lower", "upper", "header" }, cages = { "lower", "upper", "dial" }, leaves = { "l", "r" };
        for (int part = 0; part < 3; part++)
            for (int leaf = 0; leaf < 2; leaf++)
                for (int f = 0; f < 4; f++)
                {
                    liftIds[0, part, leaf, f] = Id($"liftdoor-drywall-{lifts[part]}-{leaves[leaf]}-{Sides[f]}");
                    liftIds[1, part, leaf, f] = Id($"liftdoor-hotel-{lifts[part]}-{leaves[leaf]}-{Sides[f]}");
                    cageIds[0, part, leaf, f] = Id($"cagelift-hotel-{cages[part]}-{leaves[leaf]}-{Sides[f]}");
                    cageIds[1, part, leaf, f] = Id($"cagelift-plaster-{cages[part]}-{leaves[leaf]}-{Sides[f]}");
                }

        ceilingTileId = BlockId("backrooms:ceilingtile");
        lightOnId = BlockId("backrooms:fluorescentlight-on");
        lightLitId = BlockId("backrooms:fluorescentlight-lit");
        lightOffId = BlockId("backrooms:fluorescentlight-off");
        lampDimId = BlockId("backrooms:fluorescentlight-dim");
        lightFlickerId = BlockId("backrooms:fluorescentlight-flicker");
        for (int p = 0; p < PatternCodes.Length; p++)
            for (int part = 0; part < PartCodes.Length; part++)
                wallIds[p, part] = BlockId($"backrooms:wallpaper-{PatternCodes[p]}-{PartCodes[part]}");
        for (int i = 0; i < PierCodes.Length; i++) archIds[i] = BlockId($"backrooms:archheader-{PierCodes[i]}");
        for (int mask = 0; mask < 16; mask++)
            for (int part = 0; part < 2; part++)
            {
                string faces = string.Join("-", Array.ConvertAll(new[] { 0, 1, 2, 3 }, f => (mask >> f & 1) != 0 ? "cream" : "chevron"));
                paperJoinIds[mask, part] = BlockId($"backrooms:paperjoin-{faces}-{(part == 0 ? "upper" : "baseboard")}");
            }

        concreteWallId = BlockId("backrooms:concretewall-plain");
        concreteWallDamagedId = BlockId("backrooms:concretewall-damaged");
        pillarId = BlockId("backrooms:concretepillar-plain");
        pillarBaseId = Id("pillarbase-plain");
        for (int i = 0; i < Letters.Length; i++) pillarLetterIds[i] = BlockId($"backrooms:concretepillar-{Letters[i]}");
        pillarLightId = BlockId("backrooms:pillarlight");
        concreteCeilingId = BlockId("backrooms:concreteceiling");
        crateId = BlockId("backrooms:crate");
        whiteUpperId = Id("whiteblock-upper");
        whiteBaseId = Id("whiteblock-base");
        whiteLintelId = Id("whiteblock-lintel");
        metalDoorLowerId = Id("metaldoor-lower");
        metalDoorUpperId = Id("metaldoor-upper");
        for (int f = 0; f < 4; f++)
        {
            fireDoorIds[0, f] = Id($"firedoor-l-{Sides[f]}");
            fireDoorIds[1, f] = Id($"firedoor-r-{Sides[f]}");
        }
        string[] lightStates = { "on", "off", "flicker" }, axes = { "we", "ns" };
        for (int st = 0; st < 3; st++)
            for (int a = 0; a < 2; a++)
                hangingLightIds[st, a] = BlockId($"backrooms:hanginglight-{lightStates[st]}-{axes[a]}");
        bulbOnId = BlockId("backrooms:hangingbulb-on");
        conduitXId = BlockId("backrooms:conduit-we");
        conduitZId = BlockId("backrooms:conduit-ns");
        string[] conduitSides = { "east", "north", "west", "south" }, conduitKinds = { "cap", "box" }, conduitStubEnds = { "cc", "cb", "bc", "bb" };
        for (int s = 0; s < 4; s++)
            for (int k = 0; k < 2; k++) conduitEndIds[s, k] = Id($"conduitend-end-{conduitSides[s]}-{conduitKinds[k]}");
        for (int a = 0; a < 2; a++)
            for (int e = 0; e < 4; e++) conduitStubIds[a, e] = Id($"conduitend-stub-{(a == 0 ? "we" : "ns")}-{conduitStubEnds[e]}");
        dripXId = Id("drippipe-we");
        dripZId = Id("drippipe-ns");
        wheelStopId = BlockId("backrooms:wheelstop");
        carColliderId = BlockId("backrooms:carcollider");
        string[] colours = { "red", "blue", "white", "black" };
        for (int c = 0; c < 4; c++)
        {
            carIds[c, 0] = BlockId($"backrooms:car-{colours[c]}-north");
            carIds[c, 1] = BlockId($"backrooms:car-{colours[c]}-south");
            carIds[c, 2] = BlockId($"backrooms:car-{colours[c]}-east");
            carIds[c, 3] = BlockId($"backrooms:car-{colours[c]}-west");
        }
        string[] wrecks = { "redwreck", "bluewreck", "whitewreck", "burnt" };
        for (int c = 0; c < 4; c++)
            for (int f = 0; f < 4; f++)
                carWreckIds[c, f] = Id($"car-{wrecks[c]}-{new[] { "north", "south", "east", "west" }[f]}") is int w and not 0 ? w : carIds[c, f];
        for (int i = 0; i < Sides.Length; i++)
        {
            shelfIds[i] = BlockId($"backrooms:metalshelf-{Sides[i]}");
            stairIds[i] = BlockId($"backrooms:concretestairs-{Sides[i]}");
            cabinetIds[i] = BlockId($"backrooms:machinecabinet-{Sides[i]}");
            cabinetFeedIds[i] = Id($"machinecabinetfeed-{Sides[i]}");
            feedPipeIds[i] = Id($"feedpipe-{Sides[i]}");
        }
        tunnelMachineryTopId = Id("tunnelfitting-machinerytop");
        tunnelPipesValveId = Id("tunnelfitting-pipesvalve");
        tunnelRiserValveId = Id("tunnelfitting-riservalve");
        InitStairwells();

        tunnelFloorId = BlockId("backrooms:concretefloor-dark");
        tunnelCeilingId = BlockId("backrooms:tunnelceiling");
        for (int i = 0; i < TunnelWallTypes.Length; i++) tunnelWallIds[i] = BlockId($"backrooms:tunnelwall-{TunnelWallTypes[i]}");
        drumId = BlockId("backrooms:oildrum");
        pipeRunXId = BlockId("backrooms:pipes-run-we");
        pipeRunZId = BlockId("backrooms:pipes-run-ns");
        pipeHubId = BlockId("backrooms:pipes-hub");
        pipeLeakXId = BlockId("backrooms:pipes-leak-we");
        pipeLeakZId = BlockId("backrooms:pipes-leak-ns");
        tarRunXId = BlockId("backrooms:pipes-tar-we");
        tarRunZId = BlockId("backrooms:pipes-tar-ns");
        tarHubId = BlockId("backrooms:pipes-tar-hub");
        string[] tunnelStates = { "white", "warm", "off", "flicker" }, tunnelAxes = { "we", "ns", "hub", "none" };
        for (int st = 0; st < 4; st++)
            for (int a = 0; a < 4; a++)
                tunnelLightIds[st, a] = BlockId($"backrooms:tunnellight-{tunnelStates[st]}-{tunnelAxes[a]}");

        // Level 3
        dustyFloorId = BlockId("backrooms:dustyfloor");
        plasterCeilingId = BlockId("backrooms:plasterceiling");
        transformerId = BlockId("backrooms:transformer");
        windowGlowId = BlockId("backrooms:windowglow");
        manholeId = BlockId("backrooms:manhole");
        rungsId = BlockId("backrooms:rungs");
        string[] ladderParts = { "topleft", "topright", "left", "right" }, ladderSides = { "north", "east", "south", "west" };
        for (int part = 0; part < 4; part++)
            for (int side = 0; side < 4; side++)
                manholeLadderIds[part, side] = BlockId($"backrooms:manholeladder-{ladderParts[part]}-{ladderSides[side]}");
        tunnelStepId = BlockId("backrooms:tunnelstep");
        sanctumStoneId = Id("sanctumstone-plain");
        sanctumCeilingIds[0] = Id("sanctumceiling-vault");
        sanctumCeilingIds[1] = Id("sanctumceiling-boss");
        foreach ((WallPattern pattern, string code) in new[] { (WallPattern.GlazedTile, "glazed"), (WallPattern.RedBrick, "brick"), (WallPattern.Cinder, "cinder") })
        {
            l3WallIds[pattern] = BlockId($"backrooms:l3wall-{code}");
            l3FixtureIds[(pattern, Props.WallPipes)] = BlockId($"backrooms:l3wallfixture-{code}-pipes");
            l3FixtureIds[(pattern, Props.WallPanel)] = BlockId($"backrooms:l3wallfixture-{code}-panel");
            l3FixtureIds[(pattern, Props.WallFan)] = BlockId($"backrooms:l3wallfixture-{code}-fan");
            l3PipeRunIds[(pattern, TunnelPipesJoint)] = BlockId($"backrooms:l3wallfixture-{code}-pipesjoint");
            l3PipeRunIds[(pattern, TunnelPipesBracket)] = BlockId($"backrooms:l3wallfixture-{code}-pipesbracket");
            // (Layout version 9)
            int m = L3WallIndex(pattern);
            l3GaugePipeIds[m] = Id($"l3fitting-{code}-pipesgauge");
            string[] boxes = { "panelbox", "panelboxe", "panelboxw", "panelboxew" };
            for (int k = 0; k < 4; k++) l3PanelBoxIds[m, k] = Id($"l3fitting-{code}-{boxes[k]}");
            string[] cableEnds = { "e", "w", "ew" };
            for (int e = 0; e < 3; e++)
                for (int f = 0; f < 4; f++) l3CableEndIds[m, e, f] = Id($"l3deco{code}-wallcablesend{cableEnds[e]}-{Sides[f]}");
        }
        string[] floorCableEnds = { "box", "boxm", "riser", "riserm" };
        for (int k = 0; k < 4; k++)
            for (int f = 0; f < 4; f++) floorCableEndIds[k, f] = Id($"floorcableend-{floorCableEnds[k]}-{Sides[f]}");
        InitWallPipeCorners();
        l3WallIds[WallPattern.Stone] = sanctumStoneId;
        InitCity();
        InitPool();
        InitMotion();
        InitVegetation(); // vanilla trees, grass and flowers under the open sky (WorldGenerator.Vegetation.cs)
        // The five kept as 14-18
        InitRun();
        InitFun();
        InitEnd();
        InitHub();
        InitL974();
        // Levels 3999 and 188
        InitL3999();
        InitL188();
        cableXId = BlockId("backrooms:cables-run-we");
        cableZId = BlockId("backrooms:cables-run-ns");
        cableHubId = BlockId("backrooms:cables-hub");
        cableDroopXId = Id("cabledroop-plain-north");
        cableDroopZId = Id("cabledroop-plain-east");
        cableGapXId = Id("cabledroop-gap-north");
        cableGapZId = Id("cabledroop-gap-east");
        string[] cableStates = { "warm", "off", "flicker" };
        for (int st = 0; st < 3; st++)
            for (int a = 0; a < 5; a++)
                cableLightIds[st, a] = BlockId($"backrooms:cablelight-{cableStates[st]}-{new[] { "we", "ns", "none", "tarwe", "tarns" }[a]}");
        for (int f = 0; f < 4; f++)
        {
            pipeEndIds[f] = BlockId($"backrooms:pipes-end-{Sides[f]}");
            tarEndIds[f] = BlockId($"backrooms:pipes-tar-end-{Sides[f]}");
            cableEndIds[f] = BlockId($"backrooms:cables-end-{Sides[f]}");
            dripEndIds[f] = Id($"drippipe-end-{Sides[f]}");
        }
        for (int a = 0; a < 2; a++)
        {
            pipeStubIds[a] = BlockId($"backrooms:pipes-stub-{axes[a]}");
            tarStubIds[a] = BlockId($"backrooms:pipes-tar-stub-{axes[a]}");
            dripStubIds[a] = Id($"drippipe-stub-{axes[a]}");
        }
        for (int i = 0; i < 8; i++) roomSignIds[i] = BlockId($"backrooms:roomsign-{i}");
        barsWeId = BlockId("backrooms:ironbars-we");
        barsNsId = BlockId("backrooms:ironbars-ns");

        // Level 4
        officeWallId = BlockId("backrooms:officewall");
        officeWallBaseId = Id("drywallbase-plain");
        officeWindowId = BlockId("backrooms:officewindow");
        officeWindowIds[0] = officeWindowId;
        officeWindowIds[1] = Id("officewindowalt-blackout");
        officeWindowIds[2] = Id("officewindowalt-blinds");
        officeGlassId = BlockId("backrooms:officeglass");
        officeCeilingId = BlockId("backrooms:officeceiling");
        confTableId = BlockId("backrooms:conferencetable");
        elevatorLowerId = BlockId("backrooms:elevatordoor-lower");
        elevatorUpperId = BlockId("backrooms:elevatordoor-upper");
        officeDoorLowerId = Id("officedoor-lower");
        officeDoorUpperId = Id("officedoor-upper");
        string[] officeLightStates = { "on", "lit", "off", "flicker" };
        for (int st = 0; st < 4; st++) officeLightIds[st] = BlockId($"backrooms:officelight-{officeLightStates[st]}");
        partitionWeId = BlockId("backrooms:partition-we");
        partitionNsId = BlockId("backrooms:partition-ns");

        // Level 5
        wainscotId = BlockId("backrooms:hotelwall-wainscot");
        panelId = BlockId("backrooms:hotelwall-panel");
        friezeId = BlockId("backrooms:hotelwall-frieze");
        marbleId = BlockId("backrooms:marblecolumn");
        plasterId = BlockId("backrooms:plasterwall");
        string[] grandCeilings = { "coffer", "beam-we", "beam-ns", "beam-cross" };
        for (int i = 0; i < 4; i++) grandCeilingIds[i] = BlockId($"backrooms:hotelceiling-{grandCeilings[i]}");
        creamCeilingId = BlockId("backrooms:hotelceiling-cream");
        chandelierId = BlockId("backrooms:chandelier");
        sconceId = BlockId("backrooms:hotelfixture-sconce");
        portraitId = BlockId("backrooms:hotelfixture-portrait");
        beverlyId = BlockId("backrooms:hotelfixture-beverly");
        staffSignId = BlockId("backrooms:staffsign");
        doorLowerId = BlockId("backrooms:hoteldoor-lower");
        for (int i = 0; i < doorUpperIds.Length; i++) doorUpperIds[i] = BlockId($"backrooms:hoteldoor-upper{i}");
        for (int f = 0; f < 4; f++)
        {
            hotelStairIds[0, f] = BlockId($"backrooms:hotelstairs-runner-{Sides[f]}");
            hotelStairIds[1, f] = BlockId($"backrooms:hotelstairs-marble-{Sides[f]}");
        }
        palmId = BlockId("backrooms:pottedpalm");
        mahjongId = BlockId("backrooms:mahjongtable");
        turntableId = BlockId("backrooms:turntable");
        bulbOffId = BlockId("backrooms:hangingbulb-off");
        string[] domeStates = { "on", "off", "flicker" };
        for (int st = 0; st < 3; st++) domeIds[st] = BlockId($"backrooms:domelight-{domeStates[st]}");

        for (int i = 0; i < Sides.Length; i++)
        {
            deskIds[i] = BlockId($"backrooms:desk-{Sides[i]}");
            chairIds[i] = BlockId($"backrooms:officechair-{Sides[i]}");
            filingIds[i] = BlockId($"backrooms:filingcabinet-{Sides[i]}");
            vendingIds[i] = BlockId($"backrooms:vendingmachine-{Sides[i]}");
            coolerIds[i] = BlockId($"backrooms:watercooler-{Sides[i]}");
            bedHeadIds[i] = BlockId($"backrooms:bed-head-{Sides[i]}");
            bedFootIds[i] = BlockId($"backrooms:bed-foot-{Sides[i]}");
            nightstandIds[i] = BlockId($"backrooms:nightstand-{Sides[i]}");
            wardrobeIds[i] = BlockId($"backrooms:wardrobe-{Sides[i]}");
            wingChairIds[i] = BlockId($"backrooms:wingchair-{Sides[i]}");
            sofaIds[i] = BlockId($"backrooms:sofa-{Sides[i]}");
            boilerIds[i] = BlockId($"backrooms:boiler-{Sides[i]}");
            furnaceIds[i] = BlockId($"backrooms:furnace-{Sides[i]}");
        }
        string[] plantKinds = { "run", "flue", "both" }, plantEnds = { "mid", "west", "east" }, plantParts = { "furnace2", "steam2", "both3", "flue3" };
        for (int k = 0; k < 3; k++)
            for (int e = 0; e < 3; e++)
                for (int sd = 0; sd < 2; sd++) plantHeaderIds[k, e, sd] = BlockId($"backrooms:plantheader-{plantKinds[k]}-{plantEnds[e]}-{(sd == 0 ? "north" : "south")}");
        for (int k = 0; k < 4; k++)
            for (int f = 0; f < 4; f++) plantRiserIds[k, f] = BlockId($"backrooms:plantriser-{plantParts[k]}-{Sides[f]}");
        plantThruIds[0] = BlockId("backrooms:plantthru-north");
        plantThruIds[1] = BlockId("backrooms:plantthru-south");

        lighting = new WorldLighting(api, this, chunkSize);
    }

    public WorldLayout Layout => layout;

    // Recently built cells: lighting a chunk needs its eight neighbours, so each cell is wanted about ten times
    private const int MacroCacheSize = 96;
    private readonly Dictionary<(int, int), Tile[]> macroCache = new();
    private readonly Queue<(int, int)> macroOrder = new();

    /// <summary>The layout of a cell, from a small cache. The array is shared: read it, never change it.</summary>
    public Tile[] Macro(int mx, int mz)
    {
        lock (macroCache)
        {
            if (macroCache.TryGetValue((mx, mz), out Tile[] cached)) return cached;
        }
        Tile[] tiles = layout.BuildMacro(mx, mz);
        lock (macroCache)
        {
            if (macroCache.TryAdd((mx, mz), tiles))
            {
                macroOrder.Enqueue((mx, mz));
                if (macroOrder.Count > MacroCacheSize) macroCache.Remove(macroOrder.Dequeue());
            }
        }
        return tiles;
    }

    public void Generate(IChunkColumnGenerateRequest request)
    {
        IServerChunk[] chunks = request.Chunks;
        // Vanilla has laid the ground down already (UndergroundSystem): build on top of it
        bool ground = UndergroundSystem.Active;
        if (!ground) foreach (IServerChunk chunk in chunks) chunk.Data.ClearBlocksAndPrepare();

        WorldGeometry g = Geometry;
        Tile[] tiles = Macro(request.ChunkX, request.ChunkZ);
        int level = tiles[0].Level;
        bool openSky = WorldLayout.IsOpenSky(level);
        // Plain concrete deeper than the foundations is left to the ground
        int groundBelow = g.FloorFor(level) - FoundationDepth;
        var (bottom, bandTop, cap) = Band(level);

        if (ground)
        {
            // Whatever the land raised above the band (hills over the roof, peaks in the open levels' sky) is not there
            for (int y = bandTop + 1; y <= g.TopY; y++) FillLayer(chunks, y, 0);
        }
        else
        {
            for (int y = 1; y < g.BandBottom; y++) FillLayer(chunks, y, concreteId);
        }
        FillLayer(chunks, 0, mantleId);
        if (!openSky) FillLayer(chunks, cap, mantleId);

        IMapChunk mapChunk = chunks[0].MapChunk;
        var entities = new List<(BlockPos, string)>();
        int yMax = 0;
        // What the lighting pass needs of this cell, gathered as the blocks go down rather than computed twice
        int lightBottom = lighting.BandBottomFor(request.ChunkX, request.ChunkZ);
        var cellLight = new WorldLighting.CellLight(chunkSize, lighting.Height);

        for (int lz = 0; lz < chunkSize; lz++)
        {
            for (int lx = 0; lx < chunkSize; lx++)
            {
                Tile t = tiles[WorldLayout.TileIndex(lx, lz)];
                int gx = request.ChunkX * chunkSize + lx, gz = request.ChunkZ * chunkSize + lz;
                int top = 0;
                int column = lz * chunkSize + lx;
                // Where vanilla's land ends, and the rock to fill on up to the foundations with where it lay lower
                int land = 0, fill = 0;
                if (ground)
                {
                    land = Math.Min(mapChunk.WorldGenTerrainHeightMap[column], groundBelow - 1);
                    fill = GroundFill(chunks, lx, lz, land);
                    for (int y = land + 1; y < Math.Min(bottom, groundBelow); y++) Petrify(chunks, lx, y, lz, fill);
                }
                for (int y = bottom; y <= bandTop; y++)
                {
                    int block = ColumnBlock(t, gx, gz, y, out int fluid);
                    if (ground && block == concreteId && fluid == 0 && y < groundBelow)
                    {
                        // Under the foundations: the ground as vanilla laid it, filled up with its own rock
                        if (y > land) Petrify(chunks, lx, y, lz, fill);
                        block = GetBlock(chunks, lx, y, lz);
                        lighting.Note(cellLight, lx, y, lz, lightBottom, block, 0);
                        if (block != 0) top = y;
                        continue;
                    }
                    lighting.Note(cellLight, lx, y, lz, lightBottom, block, fluid);
                    if (block != 0 || y < g.BandBottom || ground) SetBlock(chunks, lx, y, lz, block);
                    if (fluid != 0 || ground) SetFluid(chunks, lx, y, lz, fluid);
                    if (block != 0 || fluid != 0) top = y;
                    string entityClass = EntityClassOf(block);
                    if (entityClass != null) entities.Add((new BlockPos(gx, y, gz), entityClass));
                }
                if (t.Kind == TileKind.Pit && t.Level == 0) LineShaft(chunks, tiles, lx, lz);

                int rainHeight = openSky ? top : cap;
                mapChunk.RainHeightMap[column] = (ushort)rainHeight;
                mapChunk.WorldGenTerrainHeightMap[column] = (ushort)(openSky ? Math.Max(g.FloorFor(level), top) : g.FloorY);
                yMax = Math.Max(yMax, rainHeight);
            }
        }

        mapChunk.YMax = (ushort)yMax;
        lighting.Offer(request.ChunkX, request.ChunkZ, lightBottom, cellLight);
        lighting.Light(chunks, request.ChunkX, request.ChunkZ);
        // (Dropping the notes loses nothing: SpawnBlockEntities finds them again from the blocks)
        if (pendingEntities.Count >= PendingLimit) pendingEntities.Clear();
        pendingEntities[ChunkKey(request.ChunkX, request.ChunkZ)] = entities.Count > 0 ? entities : NoEntities;
    }

    /// <summary>
    /// The heights a level's columns are generated over (<paramref name="bottom"/> to <paramref name="top"/>), and
    /// where the mantle cap over them goes (none is placed under the open sky).
    /// </summary>
    private (int Bottom, int Top, int Cap) Band(int level)
    {
        WorldGeometry g = Geometry;
        // The sea runs far deeper than the usual band, and Level 8's rock goes down further to be mined; the city's
        // streets lie lower than every other level's floor and its towers rise to the top of the world
        int bottom = level switch
        {
            7 => Math.Max(2, g.FloorY - 125),
            8 => g.BandBottom - 40,
            11 => g.CityBandBottom,
            WorldLayout.Poolrooms => g.FloorFor(level) - WorldGeometry.PoolPitDepth - 2,
            WorldLayout.Motion => g.FloorFor(level) - 6,
            // The five kept as 14-18 (and 3999 and 188): the band they are lit over (see WorldGeometry.BandBottomFor),
            // or the usual one if that begins higher (their column builders fill in under their floors)
            WorldLayout.RunLevel or WorldLayout.FunLevel or WorldLayout.TheEnd or WorldLayout.Hub
                or WorldLayout.Level974 or WorldLayout.Level3999 or WorldLayout.Level188 => Math.Min(g.BandBottom, g.BandBottomFor(level)),
            _ => g.BandBottom,
        };
        int top = level is 11 or WorldLayout.Motion ? g.TopY : g.BandTop;
        // From layout version 9 the Suburbs go on up to the roofs of their two-storey houses, their chimneys and the tops
        // of their trees (in 1-8 nothing above the usual band was built: a two-storey house stopped at its eaves, flat)
        if (level == 9 && layout.Version >= 9) top = Math.Min(g.TopY - 1, g.FloorY + SuburbTop);
        // Those levels are generated over their own band, and sealed just above it
        bool region = level >= WorldLayout.RunLevel && level <= WorldLayout.Level188;
        if (region) top = g.BandTopFor(level);
        return (bottom, top, region ? top + 1 : g.CapY);
    }

    /// <summary>The block entity class a block needs, or null.</summary>
    private string EntityClassOf(int blockId) => (uint)blockId < (uint)entityClassById.Length ? entityClassById[blockId] : null;

    /// <summary>
    /// Spawns the block entities for a column generated earlier (flickering lights, dispensers). They are noted when
    /// the terrain is generated, but a column can stop between the two passes (the server saved and stopped with it
    /// half generated, or the notes were dropped): then they are found again from the blocks of the column, any that
    /// has no block entity yet getting one.
    /// </summary>
    public void SpawnBlockEntities(IChunkColumnGenerateRequest request, IBlockAccessor blockAccessor)
    {
        if (pendingEntities.TryRemove(ChunkKey(request.ChunkX, request.ChunkZ), out var entities))
        {
            foreach ((BlockPos pos, string entityClass) in entities) blockAccessor.SpawnBlockEntity(entityClass, pos);
            return;
        }
        IServerChunk[] chunks = request.Chunks;
        var (bottom, top, _) = Band(Macro(request.ChunkX, request.ChunkZ)[0].Level);
        top = Math.Min(top, chunks.Length * chunkSize - 1);
        int x0 = request.ChunkX * chunkSize, z0 = request.ChunkZ * chunkSize;
        var at = new BlockPos(0, 0, 0);
        for (int y = Math.Max(0, bottom); y <= top; y++)
        {
            for (int lz = 0; lz < chunkSize; lz++)
            {
                for (int lx = 0; lx < chunkSize; lx++)
                {
                    string entityClass = EntityClassOf(GetBlock(chunks, lx, y, lz));
                    if (entityClass == null) continue;
                    at.Set(x0 + lx, y, z0 + lz);
                    if (blockAccessor.GetBlockEntity(at) == null) blockAccessor.SpawnBlockEntity(entityClass, at.Copy());
                }
            }
        }
    }

    private static long ChunkKey(int chunkX, int chunkZ) => ((long)chunkX << 32) | (uint)chunkZ;

    /// <summary>
    /// The block (and fluid) at height <paramref name="y"/> of a column, within
    /// [<see cref="WorldGeometry.BandBottom"/>, <see cref="WorldGeometry.BandTop"/>]. Shaft lining, which
    /// depends on neighbouring columns, is left out; it absorbs light exactly like the concrete it replaces.
    /// </summary>
    public int ColumnBlock(in Tile t, int gx, int gz, int y, out int fluid)
    {
        fluid = 0;
        int rel = y - Geometry.FloorY;
        // Level !'s ways in, in other levels (a door that shouldn't be there, a wall that wasn't, a red corridor)
        if (t.Under is >= Unders.RunFirst and <= Unders.RunLast && t.Level != WorldLayout.RunLevel
            && RunEntranceBlock(t, gx, gz, y - Geometry.FloorFor(t.Level), out fluid) is int run and >= 0) return run;
        // The End's ways in, in other levels (an EXIT door in Level 1, a lone doorway in Level 4, a bookstore's door in the city)
        if (t.Under is >= Unders.EndFirst and <= Unders.EndLast && t.Level != WorldLayout.TheEnd
            && EndEntranceBlock(t, y - Geometry.FloorFor(t.Level), out fluid) is int end and >= 0) return end;
        // Level 3999's ways in, in other levels (the lone arcade and its windmills in Level 10, a glitching wall in the city, magenta tiles in Level 37)
        if (t.Under is >= Unders.L3999First and <= Unders.L3999Last && t.Level != WorldLayout.Level3999
            && L3999EntranceBlock(t, y - Geometry.FloorFor(t.Level), out fluid) is int l3999 and >= 0) return l3999;
        // Level 188's ways in, in other levels (a window where no window should be, in Level 0, Level 1 and Level Fun)
        if (t.Under is >= Unders.L188First and <= Unders.L188Last && t.Level != WorldLayout.Level188
            && L188EntranceBlock(t, y - Geometry.FloorFor(t.Level), out fluid) is int l188 and >= 0) return l188;
        switch (t.Level)
        {
            case 7: return Level7Block(t, gx, gz, rel, out fluid);
            case 8: return Level8Block(t, gx, gz, y, rel, out fluid);
            case 9:
                if (t.Under == Unders.FullPool && t.Floor == FloorKind.PoolDeep && rel is -1 or 0) { fluid = waterId; return 0; }
                return Level9Block(t, gx, gz, rel);
            case 10: return Level10Block(t, gx, gz, rel, out fluid);
            case 11: return Level11Block(t, gx, gz, y - Geometry.CityFloorY, out fluid);
            case WorldLayout.Poolrooms: return Level37Block(t, y - Geometry.FloorFor(WorldLayout.Poolrooms), out fluid);
            case WorldLayout.Motion: return Level94Block(t, gx, gz, y - Geometry.FloorFor(WorldLayout.Motion), out fluid);
            // The five kept as 14-18, each in its own file, from its own floor
            case WorldLayout.RunLevel: return LevelRunBlock(t, gx, gz, y - Geometry.FloorFor(WorldLayout.RunLevel), out fluid);
            case WorldLayout.FunLevel: return LevelFunBlock(t, gx, gz, y - Geometry.FloorFor(WorldLayout.FunLevel), out fluid);
            case WorldLayout.TheEnd: return LevelEndBlock(t, gx, gz, y - Geometry.FloorFor(WorldLayout.TheEnd), out fluid);
            case WorldLayout.Hub: return LevelHubBlock(t, gx, gz, y - Geometry.FloorFor(WorldLayout.Hub), out fluid);
            case WorldLayout.Level974: return Level974Block(t, gx, gz, y - Geometry.FloorFor(WorldLayout.Level974), out fluid);
            case WorldLayout.Level3999: return Level3999Block(t, gx, gz, y - Geometry.FloorFor(WorldLayout.Level3999), out fluid);
            case WorldLayout.Level188: return Level188Block(t, gx, gz, y - Geometry.FloorFor(WorldLayout.Level188), out fluid);
        }
        // The stairwells of Levels 1 and 4 (from layout version 4): flights up through the ceiling and down through the floor
        if (WorldLayout.IsShaftFlight(t)) return FlightBlock(t, rel);
        if (rel < 0) return BelowFloor(t, rel, out fluid);

        // Walls between levels (or around grand rooms) run solid up to the top of the tallest space next to them
        int room = t.Level == 1 || t.Grand ? WorldGeometry.MaxRoomHeight : WorldGeometry.RoomHeight;
        if (t.Tall && t.IsWallLike && rel > room && rel <= WorldGeometry.MaxRoomHeight + 1 && t.Level != 0) return concreteId;
        // A sump let into the floor (Level 5's boiler bays): the water stands where the floor block would be
        if (InteriorSump(t, rel, out fluid)) return 0;

        int block = t.Level switch
        {
            0 => Level0Block(t, rel, out fluid),
            1 => Level1Block(t, rel, gx, gz),
            2 => Level2Block(t, rel, gx, gz),
            3 => Level3Block(t, rel, gx, gz),
            4 => Level4Block(t, rel, gx, gz),
            5 => Level5Block(t, rel, gx, gz),
            _ => Level6Block(t, rel),
        };
        // A chalk mark at eye height on the wall beside the tile, left by someone before
        if (block == 0 && fluid == 0 && rel == 2 && t.Chalk != 0) return ChalkMark(t.Chalk);
        return block;
    }

    /// <summary>
    /// The chalk mark block for a tile's <see cref="Tile.Chalk"/>. A mark is named for the face of the wall it is drawn
    /// on, which is the face looking back at the tile: a wall to the north has the mark on its south face.
    /// </summary>
    private int ChalkMark(byte chalk)
    {
        int face = ChalkBits.Wall(chalk) switch { ArchPier.North => 2, ArchPier.East => 3, ArchPier.South => 0, _ => 1 };
        return chalkIds[Math.Clamp(ChalkBits.Symbol(chalk), 0, 3), face];
    }

    private int BelowFloor(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        if (t.Level == 6 && t.Under is >= Unders.Descent1 and <= Unders.Descent3) return DescentBlock(t, rel);
        if (t.Level == 3 && t.Under > 0 && rel >= -5)
        {
            // Level 3's flooded utility tunnel: 3 high, knee-deep freezing water, reached down a manhole shaft, its
            // floor deep in the clay silt the water has carried in
            if (rel == -5) return clayId != 0 ? clayId : concreteId;
            // Layout version 9's manholes: the ladder from the dry landing at its foot up to the lip, the landing round
            // it (shaft, a block either side and the row behind), and a half step out of the water onto it
            if (t.Under == 2 && t.Zone != 0) return rel == -4 ? concreteId : ManholeLadder(t, false);
            if (t.Under == 1 && t.Zone == WorldLayout.L3TunnelLanding) return rel is -4 or -1 ? concreteId : 0;
            if (rel == -4) fluid = waterId;
            if (rel == -4 && t.Under == 1 && t.Zone == WorldLayout.L3TunnelStep && tunnelStepId != 0) return tunnelStepId;
            if (rel == -1) return t.Under == 2 ? rungsId : concreteId;
            return t.Under == 2 ? rungsId : 0;
        }
        if (t.Kind == TileKind.Pit)
        {
            if (rel > -WorldGeometry.ShaftDepth) return 0;
            if (rel == -WorldGeometry.ShaftDepth) return floorIds[(int)FloorKind.Carpet];
        }
        if (t.Kind == TileKind.Water && rel == -1) return floorIds[(int)FloorKind.Soaked];
        return concreteId;
    }

    /// <summary>
    /// A piece of a layout version 9 manhole's ladder: the top (at the floor, its rails standing on above it, the open
    /// lid against the far side) or a length below, the left or right half as seen facing it, on the tile's Pier side.
    /// </summary>
    private int ManholeLadder(in Tile t, bool top) =>
        manholeLadderIds[(top ? 0 : 2) + (t.Zone == WorldLayout.L3ShaftLeft ? 0 : 1), Facing(t.Pier)];

    // ---- Shared detail ----

    /// <summary>The decoration block for a wall tile at this height, or 0 if it has none there.</summary>
    private int Decorated(in Tile t, int rel)
    {
        if (t.Variant < Decor.First || t.Variant >= Decor.Limit || rel < 0 || rel > 5) return 0;
        // Level 1's power box conduit runs on up to a junction box under the ceiling (layout version 9 on; before it
        // stopped at the plain wall block above the riser)
        if (rel == 4 && t.Variant == Decor.PowerBox && (t.Level != 1 || layout.Version < 9)) return 0;
        // The hotel's mirror hangs on a plain cream wall block, not on the red framed panel (layout version 9 on)
        if (rel == 2 && t.Variant == Decor.Mirror && t.Pattern == WallPattern.Hotel && layout.Version >= 9) return hotelMirrorPlainIds[Facing(t.Pier)];
        return decorIds[(int)t.Pattern, t.Variant, rel, Facing(t.Pier)];
    }

    /// <summary>The block for a detail prop, or 0 if the tile holds none.</summary>
    private int PropBlock(in Tile t)
    {
        if (t.Variant < 40 || t.Variant >= Props.Limit) return 0;
        int kind = Math.Min(t.Stack, propKinds[t.Variant] - 1);
        return propIds[t.Variant, Math.Max(0, kind), Facing(propHeadFirst[t.Variant] ? Opposite(t.Pier) : t.Pier)];
    }

    /// <summary>A part of a two-wide elevator door. Stack says which leaf (0 left, 1 right) as seen from in front.</summary>
    private int LiftPart(int[,,,] ids, int wall, int part, in Tile t) => ids[wall, part, t.Stack & 1, Facing(t.Pier)];

    // ---- Level 0: wallpaper, carpet, drop ceiling ----

    private int Level0Block(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        const int room = WorldGeometry.RoomHeight;
        if (t.Tall && t.IsWallLike && rel > room) return concreteId; // seals the crawlspace off from taller levels
        if (rel > room + 1 + WorldGeometry.CrawlspaceHeight) return concreteId;
        if (rel > room + 1) return 0; // crawlspace
        if (rel == room + 1) return t.Worn ? 0 : CeilingBlock0(t.Ceiling);

        if (rel == 0)
        {
            if (t.Kind == TileKind.Pit) return 0;
            if (t.Kind == TileKind.Water)
            {
                // Recessed one block and flooded
                fluid = waterId;
                return 0;
            }
            return floorIds[(int)t.Floor];
        }

        bool bottom = rel == 1, top = rel == room;
        int pattern = Paper(t.Pattern);
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (pattern < 0) return concreteId;
                // Where the pale walls meet the paper, each face takes the finish of the side it faces
                if (WorldLayout.L0FlipBits(t) is int flip and not 0 && t.Pattern is WallPattern.Chevron or WallPattern.Cream)
                    return paperJoinIds[t.Pattern == WallPattern.Cream ? ~flip & 15 : flip, bottom ? 1 : 0];
                return wallIds[pattern, bottom ? (t.Outlet ? PartOutlet : BasePart(t.Base)) : PartUpper];
            case TileKind.Doorway:
                return top ? (pattern < 0 ? concreteId : wallIds[pattern, PartUpper]) : 0;
            case TileKind.ArchWindow:
                return bottom ? wallIds[Math.Max(pattern, 0), BasePart(t.Base)] : top ? archIds[(int)t.Pier] : 0;
            case TileKind.ArchDoor:
                return top ? archIds[(int)t.Pier] : 0;
            default:
                // (Level Fun's poster and its red smiley hang at eye height, over the carpet)
                if (t.Variant is Props.FunPosterTrap or Props.FunSmiley) return rel == 2 ? PropBlock(t) : 0;
                if (bottom) return t.SupplyBox ? BoxOf(t) : t.Variant >= 40 ? PropBlock(t) : 0;
                // The Manila Room's chandelier hangs under its ceiling
                return top && t.Ceiling == CeilingKind.Chandelier ? chandelierId : 0;
        }
    }

    private int CeilingBlock0(CeilingKind ceiling) => ceiling switch
    {
        CeilingKind.LightOn => lightOnId,
        CeilingKind.LightLit => lightLitId,
        CeilingKind.LightOff => lightOffId,
        CeilingKind.LampDim => lampDimId,
        CeilingKind.LampRed => lampRedId,
        CeilingKind.LightFlicker => lightFlickerId,
        _ => ceilingTileId,
    };

    // ---- Level 1: concrete car park and maintenance halls ----

    private int Level1Block(in Tile t, int rel, int gx, int gz)
    {
        const int room = WorldGeometry.Level1RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return floorIds[(int)t.Floor];
        if (rel == room + 1) return t.IsWallLike ? concreteId : concreteCeilingId;

        switch (t.Kind)
        {
            case TileKind.Wall:
                if (t.Pattern == WallPattern.Pillar)
                {
                    if (rel == 1) return pillarBaseId;
                    if (rel == 2) return pillarLetterIds[(t.Variant & 7) % pillarLetterIds.Length];
                    if (rel == 3 && (t.Variant & 8) != 0) return pillarLightId;
                    // A coloured cloth landmark tied round the column
                    if (rel == 3 && t.Variant >= 16)
                    {
                        int banner = decorIds[(int)WallPattern.Pillar, Decor.Banner + ((t.Variant >> 4) - 1) % 4, 3, Facing(t.Pier)];
                        if (banner != 0) return banner;
                    }
                    return pillarId;
                }
                // (From layout version 4 a stairwell's painted floor is its own: P5 to B3)
                int decor = t.Variant == Decor.LevelSign && FloorSign(t, rel) is int floor and not 0 ? floor : Decorated(t, rel);
                if (decor != 0) return decor;
                if (t.Pattern == WallPattern.WhiteBlock) return rel == 1 ? whiteBaseId : whiteUpperId;
                if (t.Pattern <= WallPattern.Manila && rel <= WorldGeometry.RoomHeight) return wallIds[(int)t.Pattern, rel == 1 ? BasePart(t.Base) : PartUpper];
                return t.Variant == 1 ? concreteWallDamagedId : concreteWallId;
            case TileKind.Doorway:
                if (rel == 1 && t.Variant == Props.FireDoor) return fireDoorIds[t.Stack & 1, Facing(t.Pier)];
                if (rel <= 2) return 0;
                if (rel == 3 && t.ExitSign && ExitLintel(t, gx, gz) is int exit and not 0) return exit;
                if (t.Pattern == WallPattern.WhiteBlock) return rel == 3 ? whiteLintelId : whiteUpperId;
                return concreteWallId;
            case TileKind.Door:
                if (rel == 1) return metalDoorLowerId;
                if (rel == 2) return metalDoorUpperId;
                return t.Pattern == WallPattern.WhiteBlock ? whiteUpperId : concreteWallId;
        }

        // Stairs to nowhere: solid under the step, then the step itself
        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? concreteId : stairIds[Facing(t.Pier)];

        if (rel == room)
        {
            // Beams between the columns, hanging fixtures and overhead pipework just below the slab
            if (t.Beam) return concreteWallId;
            int axis = t.Pier is ArchPier.North or ArchPier.South ? 1 : 0;
            switch (t.Ceiling)
            {
                case CeilingKind.LightOn or CeilingKind.LightLit: return hangingLightIds[0, axis];
                case CeilingKind.LightOff: return hangingLightIds[1, axis];
                case CeilingKind.LightFlicker: return hangingLightIds[2, axis];
                case CeilingKind.LightWarm: return bulbOnId;
            }
            if (t.Overhead != 0) return overheadIds[t.Overhead];
            // A bundle meeting one across it is a hub; one ending with open hall beyond is capped (a leaking length on
            // its own at both ends)
            if (t.Pipe is Pipes.RunX or Pipes.RunZ or Pipes.DripX or Pipes.DripZ)
            {
                int run = OverheadRun(t, gx, gz, out int end, out bool stub);
                bool drip = t.Pipe is Pipes.DripX or Pipes.DripZ;
                if (run == 3 && !drip) return pipeHubId;
                if (stub) return drip ? dripStubIds[run - 1] : pipeStubIds[run - 1];
                if (end >= 0) return drip ? dripEndIds[end] : pipeEndIds[end];
            }
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.Hub => pipeHubId,
                Pipes.DripX => dripXId,
                Pipes.DripZ => dripZId,
                Pipes.ConduitX or Pipes.ConduitZ => ConduitBlock(t, gx, gz),
                _ => 0,
            };
        }

        if (t.Variant == Props.Shelf && rel <= 2) return shelfIds[Facing(Opposite(t.Pier))];
        if (t.Variant == Props.Car) return rel == 1 ? carWreckIds[t.Stack % 4, CarFacing(t.Pier)] : 0;
        if (t.Variant == Props.CarPart) return rel == 1 ? carColliderId : 0;
        if (t.Variant == Props.WheelStop && rel == 1) return wheelStopId;
        if (rel == 1)
        {
            if (t.Variant == Props.Drum) return drumId;
            if (t.Variant == Props.Cooler) return coolerIds[Facing(t.Pier)];
            if (t.Variant == Props.FilingCabinet) return filingIds[Facing(t.Pier)];
            int prop = PropBlock(t);
            if (prop != 0) return prop;
        }
        if (t.Variant == 0 && rel <= t.Stack) return CrateOf(t);
        if (rel == 1 && t.SupplyBox) return BoxOf(t);
        // The concrete is crumbling: its aggregate lies about as loose stones and the odd flint nodule
        if (rel == 1 && t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0 && t.Stair == 0) return Rubble(gx, gz);
        return 0;
    }

    /// <summary>Loose stones and flints on a Level 1 floor, now and then.</summary>
    private int Rubble(int gx, int gz)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, 0x1D01));
        if (r < 0.005 && looseStoneL1Ids.Length > 0) return looseStoneL1Ids[(int)(r * 10000) % looseStoneL1Ids.Length];
        if (r < 0.0065) return looseFlintId;
        return 0;
    }

    // ---- Level 2: utility tunnels ----

    private int Level2Block(in Tile t, int rel, int gx, int gz)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return tunnelFloorId;
        if (rel == room + 1) return t.IsWallLike ? concreteId : tunnelCeilingId;

        switch (t.Kind)
        {
            case TileKind.Wall:
                if (layout.Version >= 9 && t.Pattern == WallPattern.Tunnel && TunnelFitting(t, rel, gx, gz) is int fitting and >= 0) return fitting;
                return TunnelWall(t.Pattern == WallPattern.Tunnel ? t.Variant : Props.WallPlain, rel, gx, gz);
            case TileKind.Doorway:
                return rel <= 2 ? 0 : tunnelWallIds[TunnelPlain];
            case TileKind.Door:
                if (rel > 2) return tunnelWallIds[TunnelPlain];
                // The steel doors come "in various shades of white, grey and cream": the paint goes by the door's place
                int paint = (int)(Hashing.Hash(seed, gx, gz, 0x2B0D) % 4);
                int painted = paint < 3 ? tunnelDoorPaintIds[paint, rel - 1] : 0;
                return painted != 0 ? painted : rel == 1 ? tunnelDoorLowerId : tunnelDoorUpperId;
        }

        if (rel == room)
        {
            // The top block of a tunnel, above head height: fixtures and pipe bundles
            int run = OverheadRun(t, gx, gz, out int end, out bool stub);
            int axis = run == 1 ? 0 : run == 2 ? 1 : run == 3 ? 2 : 3;
            switch (t.Ceiling)
            {
                case CeilingKind.LightOn or CeilingKind.LightLit: return tunnelLightIds[0, axis];
                case CeilingKind.LightWarm: return tunnelLightIds[1, axis];
                case CeilingKind.LightOff: return tunnelLightIds[2, axis];
                case CeilingKind.LightFlicker: return tunnelLightIds[3, axis];
            }
            if (run == 3) return pipeHubId;
            if (stub) return pipeStubIds[run - 1];
            if (end >= 0) return pipeEndIds[end];
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.Hub => pipeHubId,
                Pipes.LeakX => pipeLeakXId,
                Pipes.LeakZ => pipeLeakZId,
                _ => 0,
            };
        }

        // (Layout version 9) A machine cabinet's feed pipe goes on up the wall behind it into the overhead bundle (in
        // 1-8, and wherever the blocks are missing, the cabinet's own pipe turns back into the wall above it)
        bool feed = t.Variant == Props.Cabinet && layout.Version >= 9 && cabinetFeedIds[0] != 0 && feedPipeIds[0] != 0;
        if (feed && rel == 2) return feedPipeIds[Facing(Opposite(t.Pier))];
        if (rel == 1)
        {
            if (t.Variant == Props.Drum) return drumId;
            if (feed) return cabinetFeedIds[Facing(Opposite(t.Pier))];
            if (t.Variant == Props.Cabinet) return cabinetIds[Facing(Opposite(t.Pier))];
            if (t.Variant == Props.Shelf) return shelfIds[Facing(Opposite(t.Pier))];
            if (t.Variant == Props.Desk) return deskIds[Facing(t.Pier)];
            if (t.Variant >= 40) return PropBlock(t);
            if (t.Variant == 0 && t.Stack > 0) return CrateOf(t);
            if (t.SupplyBox) return BoxOf(t);
            // The B.N.T.G.'s tramway down a main (from layout version 5)
            if (t.Zone is >= 1 and <= 3) return tramRailIds[t.Zone - 1];
        }
        return 0;
    }

    /// <summary>Tunnel walls: plain at the top, with pipework, valves or machinery at body height.</summary>
    private int TunnelWall(ushort variant, int rel, int gx, int gz)
    {
        // Where the pipes turn a corner or end, the corner block (and a riser there makes way for it)
        if (variant is Props.WallPipes or Props.WallValve && rel == 2 || variant == Props.WallRiser && rel is >= 1 and <= 3)
        {
            int corner = WallPipeCorner(0, gx, gz);
            if (corner != 0)
            {
                if (rel == 2) return corner;
                variant = Props.WallPipes;
            }
        }
        return TunnelWallBlock(variant, rel, gx, gz);
    }

    /// <summary>
    /// (Layout version 9) A tunnel wall's fitting that leads somewhere, or -1 to draw the wall as in 1-8: over a wall
    /// cabinet its conduits run on up into the ceiling; a valve wall has its valve in the wall pipes (at a corner of the
    /// pipes, just the corner) and bare wall below them, where 1-8 put a wheel on the bare wall; a riser marked for one
    /// (Tile.Stack 1, see WorldLayout.PlaceL2Valve) has a valve at its foot. Where a block is missing, the 1-8 wall.
    /// </summary>
    private int TunnelFitting(in Tile t, int rel, int gx, int gz)
    {
        switch (t.Variant)
        {
            case Props.WallMachinery when rel == 3 && tunnelMachineryTopId != 0:
                return tunnelMachineryTopId;
            case Props.WallValve when tunnelPipesValveId != 0:
                if (rel == 1) return tunnelWallIds[TunnelPlain];
                if (rel != 2) return -1;
                int corner = WallPipeCorner(0, gx, gz);
                return corner != 0 ? corner : tunnelPipesValveId;
            case Props.WallRiser when rel == 1 && t.Stack == 1 && tunnelRiserValveId != 0:
                // (Where the pipes turn a corner the riser makes way for them: no riser, no valve)
                return WallPipeCorner(0, gx, gz) == 0 ? tunnelRiserValveId : -1;
        }
        return -1;
    }

    private int TunnelWallBlock(ushort variant, int rel, int gx, int gz) => tunnelWallIds[variant switch
    {
        Props.WallPipes => rel == 2 ? WallPipeRun(gx, gz) : TunnelPlain,
        Props.WallRiser => rel == 2 ? TunnelRiserJoint : TunnelRiser,
        Props.WallValve => rel == 1 ? TunnelValve : rel == 2 ? WallPipeRun(gx, gz) : TunnelPlain,
        Props.WallMachinery => rel == 1 ? TunnelMachineryBase : rel == 2 ? TunnelMachinery : TunnelPlain,
        Props.WallBrick => TunnelBrick,
        Props.WallWarning => rel == 2 ? TunnelWarning : TunnelPlain,
        _ => TunnelPlain,
    }];

    /// <summary>
    /// Which length of the wall pipes (Levels 2 and 3) a wall block carries: a flanged joint every four blocks along a
    /// wall, a bracket half way between, plain pipe the rest (x + z counts along a wall either way).
    /// </summary>
    private static int WallPipeRun(int gx, int gz) => Hashing.Mod(gx + gz, 4) switch { 0 => TunnelPipesJoint, 2 => TunnelPipesBracket, _ => TunnelPipes };

    /// <summary>Which way an overhead run goes (Levels 2 and 3): 1 along X, 2 along Z, 3 a hub, 0 none.</summary>
    private static int RunAxis(byte pipe) => pipe switch
    {
        Pipes.RunX or Pipes.LeakX or Pipes.CableX or Pipes.CableDroopX or Pipes.DripX => 1,
        Pipes.RunZ or Pipes.LeakZ or Pipes.CableZ or Pipes.CableDroopZ or Pipes.DripZ => 2,
        Pipes.Hub or Pipes.CableHub => 3,
        _ => 0,
    };

    /// <summary>Two columns whose overhead runs hang at the same height (Level 3's galleries are a block taller).</summary>
    private static bool SameOverhead(in Tile a, in Tile b) => a.Level == b.Level && a.Grand == b.Grand && a.Low == b.Low && !b.IsWallLike;

    /// <summary>
    /// An overhead run (Levels 1, 2 and 3) as it is drawn (<see cref="RunAxis"/>): a hub where it meets a run across it (the
    /// layouts draw some T-junctions and turns, where a main steps aside or round a pump gallery, as two straight runs
    /// side by side; in Level 2 the scan goes on across the width of a main, so the meeting is hubs right across it as
    /// at a planned crossing), and in <paramref name="end"/> the side (north, east,
    /// south, west) where it ends with open space beyond, nothing overhead there to run on into (else -1; Level 1's
    /// beams close a run too), and in <paramref name="stub"/> whether it does so at both ends.
    /// </summary>
    private int OverheadRun(in Tile t, int gx, int gz, out int end, out bool stub)
    {
        end = -1;
        stub = false;
        int axis = RunAxis(t.Pipe);
        if (axis is 0 or 3) return axis;
        bool x = axis == 1;
        // (Level 2's always; elsewhere only a run along a wall, and not toward a hub in the middle of a room: in Level 3's
        // crowded rooms runs lie side by side without meeting)
        bool alongWall = t.Level == 2 || (x ? TileAt(gx, gz - 1).IsWallLike || TileAt(gx, gz + 1).IsWallLike : TileAt(gx - 1, gz).IsWallLike || TileAt(gx + 1, gz).IsWallLike);
        for (int dir = -1; dir <= 1 && alongWall; dir += 2)
            for (int k = 1; k <= (t.Level == 2 ? 3 : 1); k++)
            {
                int nx = x ? gx : gx + dir * k, nz = x ? gz + dir * k : gz;
                Tile n = TileAt(nx, nz);
                if (!SameOverhead(t, n)) break;
                int across = RunAxis(n.Pipe == Pipes.None ? GrandFill(n, nx, nz) : n.Pipe);
                if (across == 3 - axis || across == 3 && (t.Level == 2 || !OpenRound(nx, nz))) return 3;
                if (across != axis) break;
            }
        for (int dir = -1; dir <= 1; dir += 2)
        {
            int nx = x ? gx + dir : gx, nz = x ? gz : gz + dir;
            Tile n = TileAt(nx, nz);
            if (n.IsWallLike || n.Beam || n.Low && !t.Low) continue;
            // (Level 1's hanging lights interrupt its bundles: they carry none of their own)
            bool lamp = n.Level == 1 && n.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit or CeilingKind.LightOff or CeilingKind.LightFlicker or CeilingKind.LightWarm;
            if (SameOverhead(t, n) && !lamp && RunAxis(n.Pipe == Pipes.None ? GrandFill(n, nx, nz) : n.Pipe) != 0) continue;
            stub = end >= 0;
            end = x ? (dir > 0 ? 1 : 3) : (dir > 0 ? 2 : 0);
        }
        return axis;
    }

    /// <summary>Whether all eight columns round one are open (a hub there is in the middle of a room, not at a corridor's junction).</summary>
    private bool OpenRound(int gx, int gz)
    {
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (TileAt(gx + dx, gz + dz).IsWallLike) return false;
        return true;
    }

    /// <summary>
    /// Level 3's galleries and halls carry cable trays (or the tar pipes) round their walls, but the layout leaves bare
    /// their corners and where a corridor comes in: the run there (a hub in a corner, the run carried on across a
    /// corridor's mouth), or none.
    /// </summary>
    private byte GrandFill(in Tile t, int gx, int gz)
    {
        if (t.Level != 3 || !t.Grand || t.Kind != TileKind.Floor || t.Pipe != Pipes.None) return Pipes.None;
        Tile e = TileAt(gx + 1, gz), w = TileAt(gx - 1, gz), s = TileAt(gx, gz + 1), n = TileAt(gx, gz - 1);
        static bool Run(in Tile o, int axis) => o.Level == 3 && o.Grand && RunAxis(o.Pipe) == axis;
        bool xe = Run(e, 1), xw = Run(w, 1), zs = Run(s, 2), zn = Run(n, 2);
        bool tar = (xe ? e.Pipe : xw ? w.Pipe : zs ? s.Pipe : n.Pipe) is Pipes.RunX or Pipes.RunZ;
        if ((xe || xw) && (zs || zn)) return tar ? Pipes.Hub : Pipes.CableHub;
        if (xe && xw) return tar ? Pipes.RunX : Pipes.CableX;
        if (zs && zn) return tar ? Pipes.RunZ : Pipes.CableZ;
        return Pipes.None;
    }

    /// <summary>North, east, south, west: the faces of a wall block in the order wallpipecorner names them.</summary>
    private static readonly (int Dx, int Dz)[] PipeFaces = { (0, -1), (1, 0), (0, 1), (-1, 0) };

    /// <summary>Reads the wallpipecorner blocks' states ("wallpipecorner-<wall>-<faces>-<corners>", see tools/gen_shapes.py).</summary>
    private void InitWallPipeCorners()
    {
        string[] walls = { "tunnel", "glazed", "brick", "cinder" };
        foreach ((string path, int id) in modBlocks)
        {
            string[] parts = path.Split('-');
            if (parts.Length != 4 || parts[0] != "wallpipecorner" || parts[3].Length != 4) continue;
            int wall = Array.IndexOf(walls, parts[1]);
            if (wall < 0) continue;
            int key = 0;
            foreach (char f in parts[2]) key |= 1 << "nesw".IndexOf(f);
            for (int c = 0; c < 4; c++) key |= "ocjw".IndexOf(parts[3][c]) << (4 + 2 * c);
            wallPipeCornerIds[wall, key] = id;
        }
    }

    /// <summary>Whether the block at wall-pipe height in a column is open, so that a wall pipe beside it shows.</summary>
    private static bool PipeOpen(in Tile n) => n.Kind is TileKind.Floor or TileKind.Doorway or TileKind.Pit or TileKind.Bars or TileKind.Water or TileKind.ArchDoor;

    /// <summary>Whether a column's wall carries the wall pipes (Level 2's pipe stretches, Level 3's pipe walls).</summary>
    private bool CarriesWallPipes(in Tile n) => n.Kind == TileKind.Wall && n.Level switch
    {
        2 => n.Pattern == WallPattern.Tunnel && n.Variant is Props.WallPipes or Props.WallRiser or Props.WallValve,
        // (From layout version 9 a pressure gauge sits in the pipes: WorldLayout.PlanL3WallRuns)
        3 => (n.Variant == Props.WallPipes || n.Variant == Decor.Gauges && layout.Version >= 9) && n.Pattern != WallPattern.Stone,
        _ => false,
    };

    /// <summary>
    /// The block for a wall carrying the wall pipes where they turn a corner or end, or 0 where the runs simply go on
    /// along every face into the next blocks (the straight blocks). Each face that looks into the open has a run; at
    /// each corner (north-east, south-east, south-west, north-west, corner c between face c and face c + 1): both faces
    /// open, the runs turn the outer corner ("w"); one open, the run goes on along the next wall if that carries pipes
    /// too ("o"), else ends in a blind flange ("c"); in an inner corner it stops against the pipes of the wall it meets
    /// if that is face c's run ("j"; face c + 1's run goes on through), else a flange where it meets a bare wall ("c").
    /// </summary>
    private int WallPipeCorner(int wall, int gx, int gz)
    {
        int mask = 0;
        for (int f = 0; f < 4; f++)
            if (PipeOpen(TileAt(gx + PipeFaces[f].Dx, gz + PipeFaces[f].Dz))) mask |= 1 << f;
        if (mask == 0) return 0;
        int key = mask, corners = 0;
        for (int c = 0; c < 4; c++)
        {
            int next = (c + 1) & 3;
            bool here = (mask >> c & 1) != 0, on = (mask >> next & 1) != 0;
            if (!here && !on) continue;
            int code;
            if (here && on) code = 3;
            else
            {
                (int dx, int dz) = here ? PipeFaces[next] : PipeFaces[c];
                Tile diagonal = TileAt(gx + PipeFaces[c].Dx + PipeFaces[next].Dx, gz + PipeFaces[c].Dz + PipeFaces[next].Dz);
                if (PipeOpen(diagonal)) code = CarriesWallPipes(TileAt(gx + dx, gz + dz)) ? 0 : 1;
                else code = !CarriesWallPipes(diagonal) ? 1 : here ? 2 : 0;
            }
            corners |= code << (4 + 2 * c);
        }
        return corners == 0 ? 0 : wallPipeCornerIds[wall, key | corners];
    }

    /// <summary>
    /// Level 1's ceiling conduit in a column. From layout version 9 a run is finished off where it ends
    /// (<see cref="WorldLayout.ConduitEnds"/>): a capped end, or a junction box where it meets a wall or a beam, one block
    /// of the run on its own having one at each end; before that the bare tubes were left as they stood.
    /// </summary>
    private int ConduitBlock(in Tile t, int gx, int gz)
    {
        bool x = t.Pipe == Pipes.ConduitX;
        if (layout.Version < 9) return x ? conduitXId : conduitZId;
        (int low, int high) = WorldLayout.ConduitEnds(TileAt, gx, gz, out _);
        if (low == 0 && high == 0) return x ? conduitXId : conduitZId;
        // (the low end of a run along X is its west end, of one along Z its north end; the stub blocks name their ends
        // west then east, which an "ns" block turns to south then north)
        if (low != 0 && high != 0)
        {
            int west = (x ? low : high) - 1, east = (x ? high : low) - 1;
            return conduitStubIds[x ? 0 : 1, west * 2 + east];
        }
        bool isLow = low != 0;
        int side = x ? (isLow ? 2 : 0) : (isLow ? 1 : 3);
        return conduitEndIds[side, (isLow ? low : high) - 1];
    }

    /// <summary>The four columns beside a column, in the order every neighbour check here looks at them (east, west, south, north).</summary>
    private static readonly (int Dx, int Dz)[] Neighbours4 = { (1, 0), (-1, 0), (0, 1), (0, -1) };

    /// <summary>Index into the north/east/south/west block variants for a direction.</summary>
    private static int Facing(ArchPier dir) => dir switch
    {
        ArchPier.North => 0,
        ArchPier.East => 1,
        ArchPier.South => 2,
        _ => 3,
    };

    private static ArchPier Opposite(ArchPier dir) => dir switch
    {
        ArchPier.North => ArchPier.South,
        ArchPier.South => ArchPier.North,
        ArchPier.East => ArchPier.West,
        _ => ArchPier.East,
    };

    // ---- Level 3: electrical station ----

    private int Level3Block(in Tile t, int rel, int gx, int gz)
    {
        // Galleries and halls are a block taller, squeezes a block lower
        int room = t.Grand ? WorldGeometry.MaxRoomHeight : t.Low ? WorldGeometry.RoomHeight - 1 : WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (t.Low && rel == room && !t.IsWallLike && t.Kind != TileKind.Bars) return 0; // nothing hangs where there is barely room to pass
        if (rel == 0) return t.Under == 2 ? (t.Zone != 0 ? ManholeLadder(t, true) : manholeId) : t.Floor == FloorKind.Dusty ? dustyFloorId : floorIds[(int)t.Floor];
        if (rel == room + 1)
        {
            if (t.IsWallLike) return concreteId;
            // A Sanctum (and a shrine) is vaulted in stone, a boss where the ribs of every fourth block cross
            if (t.Floor is FloorKind.L3Stone or FloorKind.SanctumCarpet && sanctumCeilingIds[0] != 0)
                return sanctumCeilingIds[Hashing.Mod(gx, 4) == 0 && Hashing.Mod(gz, 4) == 0 ? 1 : 0];
            return plasterCeilingId;
        }

        int wall = l3WallIds.TryGetValue(t.Pattern, out int id) ? id : l3WallIds[WallPattern.GlazedTile];
        switch (t.Kind)
        {
            case TileKind.Wall:
                WallPattern fixturePattern = l3WallIds.ContainsKey(t.Pattern) ? t.Pattern : WallPattern.GlazedTile;
                if (layout.Version >= 9 && t.Pattern != WallPattern.Stone && L3Fitting(t, rel, gx, gz, fixturePattern) is int fitting and not 0)
                    return fitting;
                int decor = Decorated(t, rel);
                if (decor != 0) return decor;
                // Where Level 3's wall pipes turn a corner or end
                if (rel == 2 && t.Variant == Props.WallPipes && t.Pattern != WallPattern.Stone
                    && WallPipeCorner(L3WallIndex(fixturePattern) + 1, gx, gz) is int corner and not 0)
                    return corner;
                if (rel == 2 && t.Variant == Props.WallPipes && WallPipeRun(gx, gz) != TunnelPipes
                    && l3PipeRunIds.TryGetValue((fixturePattern, WallPipeRun(gx, gz)), out int run) && run != 0) return run;
                if (rel == 2 && l3FixtureIds.TryGetValue((fixturePattern, t.Variant), out int fixture)) return fixture;
                return wall;
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                return t.Variant == Props.WallSign ? roomSignIds[t.Stack % 8] : wall;
            case TileKind.Bars:
                return BarsBlock(t);
            case TileKind.Door:
                return rel == 1 ? elevatorLowerId : rel == 2 ? elevatorUpperId : wall;
        }

        if (t.Variant == Props.WindowGlow) return windowGlowId;
        if (rel == room)
        {
            // (A gallery's runs round its walls, carried round its corners and across the mouths of corridors)
            Tile over = t;
            if (over.Pipe == Pipes.None) over.Pipe = GrandFill(t, gx, gz);
            int run = OverheadRun(over, gx, gz, out int end, out bool stub);
            bool tar = over.Pipe is Pipes.RunX or Pipes.RunZ or Pipes.Hub;
            // Fixtures hang from the tray, from the tar pipes, or (with nothing overhead) on chains from the ceiling
            int axis = over.Pipe == Pipes.None ? 2 : tar ? (run == 2 ? 4 : 3) : run == 1 ? 0 : 1;
            switch (t.Ceiling)
            {
                case CeilingKind.LightWarm or CeilingKind.LightOn: return cableLightIds[0, axis];
                case CeilingKind.LightOff: return cableLightIds[1, axis];
                case CeilingKind.LightFlicker: return cableLightIds[2, axis];
            }
            if (run == 3) return tar ? tarHubId : cableHubId;
            if (stub && tar) return tarStubIds[run - 1];
            if (end >= 0) return tar ? tarEndIds[end] : cableEndIds[end];
            // Level 3's pipes carry the black sludge
            return over.Pipe switch
            {
                Pipes.RunX => tarRunXId,
                Pipes.RunZ => tarRunZId,
                Pipes.Hub => tarHubId,
                Pipes.CableX => cableXId,
                Pipes.CableZ => cableZId,
                Pipes.CableHub => cableHubId,
                Pipes.CableDroopX => cableDroopXId,
                Pipes.CableDroopZ => cableDroopZId,
                _ => 0,
            };
        }
        if (rel == 1)
        {
            // (Layout version 9) The ends of a crossing of cables on the floor (WorldLayout.PlanL3FloorCables): a box against
            // the wall, or the rise into the fitting on it (Stack 1, 2). Their cables are mirrored for a wall to the east or
            // south, so that they line up with the lengths between, which are not symmetric.
            if (t.Variant == Props.FloorCable && t.Stack is 1 or 2 && layout.Version >= 9)
            {
                int end = floorCableEndIds[(t.Stack - 1) * 2 + (t.Pier is ArchPier.East or ArchPier.South ? 1 : 0), Facing(t.Pier)];
                if (end != 0) return end;
            }
            if (t.Variant == Props.Transformer) return transformerId;
            if (t.Variant == Props.Drum) return drumId;
            if (t.Variant == Props.Boiler) return boilerIds[Facing(t.Pier)];
            if (t.Variant == Props.Shelf) return shelfIds[Facing(Opposite(t.Pier))];
            if (t.Variant == Props.OfficeChair) return chairIds[Facing(t.Pier)];
            int prop = PropBlock(t);
            if (prop != 0) return prop;
            if (t.SupplyBox) return BoxOf(t);
        }
        if (t.Variant == Props.Shelf && rel == 2) return shelfIds[Facing(Opposite(t.Pier))];
        if (t.Variant == 0 && rel <= t.Stack) return CrateOf(t);
        return 0;
    }

    /// <summary>Level 3's walls in the order their blocks are kept: glazed tile, brick, cinder (and the wallpipecorner wall less one).</summary>
    private static int L3WallIndex(WallPattern pattern) => pattern switch { WallPattern.RedBrick => 1, WallPattern.Cinder => 2, _ => 0 };

    /// <summary>
    /// (Layout version 9) A Level 3 wall's fitting where its runs lead somewhere (WorldLayout.PlanL3WallRuns), or 0 to draw
    /// the wall as in 1-8: a pressure gauge sits in the wall pipes (in 1-8 on a length of pipe of its own, which lined up
    /// with nothing; where the pipes turn a corner there, just the corner); a panel's conduit runs on up the wall into a
    /// junction box (in 1-8 it stopped at the wall above), which takes the cables of a run beside it; and a cable run
    /// ends in a gland in the wall, at either end or both, unless it runs on into a panel's junction box there.
    /// </summary>
    private int L3Fitting(in Tile t, int rel, int gx, int gz, WallPattern pattern)
    {
        int m = L3WallIndex(pattern);
        switch (t.Variant)
        {
            case Decor.Gauges when rel == 2:
                int corner = WallPipeCorner(m + 1, gx, gz);
                return corner != 0 ? corner : l3GaugePipeIds[m];
            case Props.WallPanel when rel == 3:
            {
                // A cable run beside it comes into the box's side: a run on its face f to the east of it (a quarter
                // clockwise from f, the way the box's own east lies on that face) comes into its east side
                bool east = false, west = false;
                foreach (ArchPier dir in new[] { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West })
                {
                    Tile n = Beside(gx, gz, dir);
                    if (n.Kind != TileKind.Wall || n.Level != 3 || n.Variant != Decor.WallCables) continue;
                    if (dir == Clockwise(n.Pier)) east = true;
                    else if (dir == Opposite(Clockwise(n.Pier))) west = true;
                }
                return l3PanelBoxIds[m, (east ? 1 : 0) + (west ? 2 : 0)];
            }
            case Decor.WallCables when rel == 3:
            {
                // The decoration faces t.Pier, so its own east end lies a quarter clockwise from it
                ArchPier east = Clockwise(t.Pier);
                bool e = CablesRunOn(t, gx, gz, east), w = CablesRunOn(t, gx, gz, Opposite(east));
                return e && w ? 0 : l3CableEndIds[m, !e && !w ? 2 : !e ? 0 : 1, Facing(t.Pier)];
            }
        }
        return 0;
    }

    /// <summary>A direction a quarter clockwise from another, seen from above.</summary>
    private static ArchPier Clockwise(ArchPier dir) => dir switch
    {
        ArchPier.North => ArchPier.East,
        ArchPier.East => ArchPier.South,
        ArchPier.South => ArchPier.West,
        _ => ArchPier.North,
    };

    /// <summary>The tile beside a column one way.</summary>
    private Tile Beside(int gx, int gz, ArchPier dir) => dir switch
    {
        ArchPier.North => TileAt(gx, gz - 1),
        ArchPier.South => TileAt(gx, gz + 1),
        ArchPier.East => TileAt(gx + 1, gz),
        _ => TileAt(gx - 1, gz),
    };

    /// <summary>Whether a Level 3 cable run goes on past a wall block one way: into more of the run, or a panel's junction box.</summary>
    private bool CablesRunOn(in Tile t, int gx, int gz, ArchPier dir)
    {
        Tile n = Beside(gx, gz, dir);
        return n.Kind == TileKind.Wall && n.Level == 3 && (n.Variant == Decor.WallCables && n.Pier == t.Pier || n.Variant == Props.WallPanel);
    }

    private int BarsBlock(in Tile t) => t.Pier is ArchPier.North or ArchPier.South ? barsNsId : barsWeId;

    // ---- Level 4: abandoned office ----

    private int Level4Block(in Tile t, int rel, int gx, int gz)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 2) return concreteId;
        if (rel == room + 2) return t.IsWallLike ? concreteId : 0; // void above the drop ceiling
        if (rel == 0) return floorIds[(int)t.Floor];
        if (rel == room + 1)
        {
            if (t.IsWallLike) return concreteId;
            // A gap in the ceiling, perhaps with a cable tray up in it and a cable hanging down out of it
            if (t.Worn) return t.Pipe switch { Pipes.CableDroopX => cableGapXId, Pipes.CableDroopZ => cableGapZId, _ => 0 };
            return t.Ceiling switch
            {
                CeilingKind.LightOn => officeLightIds[0],
                CeilingKind.LightLit => officeLightIds[1],
                CeilingKind.LightOff => officeLightIds[2],
                CeilingKind.LightFlicker => officeLightIds[3],
                _ => t.Overhead is >= Overheads.CeilingVent and <= Overheads.CeilingStain ? overheadIds[t.Overhead] : officeCeilingId,
            };
        }

        switch (t.Kind)
        {
            case TileKind.Wall:
                int decor = Decorated(t, rel);
                if (decor != 0) return decor;
                return t.Pattern switch
                {
                    WallPattern.OfficeWindow => rel == 1 ? officeWallBaseId : officeWindowIds[t.Variant % 3],
                    WallPattern.OfficeGlass => officeGlassId,
                    WallPattern.Hotel => HotelWall(rel),
                    _ => rel == 1 ? officeWallBaseId : officeWallId,
                };
            case TileKind.Door:
                if (t.Pattern == WallPattern.Elevator) return LiftPart(liftIds, 0, Math.Min(rel - 1, 2), t);
                return rel == 1 ? officeDoorLowerId : rel == 2 ? officeDoorUpperId : officeWallId;
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                if (t.ExitSign && ExitLintel(t, gx, gz) is int exit and not 0) return exit;
                return t.Pattern == WallPattern.OfficeGlass ? officeGlassId : officeWallId;
        }

        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? officeWallId : stairIds[Facing(t.Pier)];
        if (rel != 1) return 0;
        int facing = Facing(t.Pier);
        return t.Variant switch
        {
            Props.Desk => deskIds[facing],
            Props.OfficeChair => chairIds[facing],
            Props.FilingCabinet => filingIds[facing],
            Props.Vending => vendingIds[facing],
            Props.Cooler => coolerIds[facing],
            Props.ConferenceTable => confTableId,
            Props.Partition => t.Pier is ArchPier.North or ArchPier.South ? partitionNsId : partitionWeId,
            Props.Shelf => shelfIds[Facing(Opposite(t.Pier))],
            >= 40 => PropBlock(t),
            _ => t.SupplyBox ? BoxOf(t) : 0,
        };
    }

    // ---- Level 5: terror hotel ----

    private int Level5Block(in Tile t, int rel, int gx, int gz)
    {
        int room = t.Grand ? WorldGeometry.MaxRoomHeight : WorldGeometry.RoomHeight;
        bool boiler = t.Floor == FloorKind.Dusty;
        // A front hall's grand staircase (layout 5) climbs through an opening in the ceiling into the dark over it
        bool grandStair = t.Grand && t.Stair >= WorldLayout.GrandStairTripStep;
        if (rel > room + 1) return grandStair && rel == room + 2 ? 0 : concreteId;
        if (rel == 0) return boiler ? dustyFloorId : floorIds[(int)t.Floor];
        // The staff stairs, climbing into the ceiling; the grand staircases, marble with a runner up the middle
        if (t.Stair > 0 && rel <= t.Stair)
        {
            if (rel < t.Stair) return t.Grand ? floorIds[(int)FloorKind.HotelMarble] : plasterId;
            return t.Grand ? hotelStairIds[t.Floor == FloorKind.HotelCarpet ? 0 : 1, Facing(t.Pier)] : stairIds[Facing(t.Pier)];
        }
        if (rel == room + 1)
        {
            if (grandStair) return 0;
            // (and a plain ceiling over its lower steps, which closes the opening off from the coffers beside it)
            if (t.Grand && t.Stair > 0) return creamCeilingId;
            if (t.IsWallLike) return concreteId;
            if (!t.Grand)
            {
                return t.Ceiling switch
                {
                    CeilingKind.LightOn or CeilingKind.LightLit => domeIds[0],
                    CeilingKind.LightOff => domeIds[1],
                    CeilingKind.LightFlicker => domeIds[2],
                    _ => creamCeilingId,
                };
            }
            if (boiler) return plasterCeilingId;
            // A beam along every fourth row and column (in the lobby they land on the columns)
            return grandCeilingIds[(Hashing.Mod(gz, 4) == 3 ? 1 : 0) + (Hashing.Mod(gx, 4) == 3 ? 2 : 0)];
        }

        switch (t.Kind)
        {
            case TileKind.Wall:
                // (Layout version 9) A boiler bay's wall carries the plant's header through it, over the bay's back row
                if (rel == room && t.Pipe == Pipes.PlantThru && layout.Version >= 9) return plantThruIds[PlantSide(gz)];
                int decor = Decorated(t, rel);
                if (decor != 0) return decor;
                if (t.Pattern == WallPattern.Marble) return marbleId;
                if (t.Pattern == WallPattern.Plaster) return plasterId;
                if (rel == 2)
                {
                    if (t.Variant == Props.WallSconce) return sconceId;
                    if (t.Variant == Props.WallPortrait) return portraitId;
                    if (t.Variant == Props.WallBeverly) return beverlyId;
                }
                return HotelWall(rel);
            case TileKind.Door:
                if (t.Pattern == WallPattern.Elevator)
                {
                    // Antique copper cage (Variant 0) or a modern lift (1), with a dial or indicator above
                    if (rel > 3) return t.Floor == FloorKind.Dusty ? plasterId : HotelWall(rel);
                    return t.Variant == 1 ? LiftPart(liftIds, 1, rel - 1, t) : LiftPart(cageIds, t.Floor == FloorKind.Dusty ? 1 : 0, rel - 1, t);
                }
                if (t.Pattern == WallPattern.PoolDoor) return rel == 1 ? poolDoorLowerId : rel == 2 ? poolDoorUpperId : HotelWall(rel);
                // Level Fun's FUN doors (one leaf, all three letters)
                if (t.Pattern == WallPattern.FunDoor) return rel <= 2 ? funFunDoorIds[2, rel - 1] : HotelWall(rel);
                return rel == 1 ? doorLowerId : rel == 2 ? doorUpperIds[t.Variant < doorUpperIds.Length ? t.Variant : t.Variant % 8] : HotelWall(rel);
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                if (rel == 3 && t.ExitSign && StaffSign(t, gx, gz) is int staff and not 0) return staff;
                return t.Pattern == WallPattern.Plaster ? plasterId : HotelWall(rel);
            case TileKind.Bars:
                return BarsBlock(t);
        }

        if (rel == room)
        {
            if (t.Ceiling == CeilingKind.Chandelier) return chandelierId;
            if (t.Overhead == Overheads.CeilingFan) return ceilingFanId;
            if (boiler && t.Ceiling == CeilingKind.LightWarm) return bulbOnId;
            if (boiler && t.Ceiling == CeilingKind.LightOff) return bulbOffId;
            if (t.Pipe is >= Pipes.PlantRun and <= Pipes.PlantBoth && layout.Version >= 9) return PlantHeader(t, gx, gz);
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.LeakX => pipeLeakXId,
                Pipes.LeakZ => pipeLeakZId,
                _ => 0,
            };
        }
        // (Layout version 9) A boiler's flue and steam pipe, and a furnace's flue, rise through the two blocks over them
        // to the header
        if (rel is 2 or 3 && layout.Version >= 9 && t.Variant is Props.Boiler or Props.Furnace)
            return plantRiserIds[t.Variant == Props.Boiler ? (rel == 2 ? 1 : 2) : (rel == 2 ? 0 : 3), Facing(t.Pier)];
        if (rel != 1) return 0;
        int facing = Facing(t.Pier);
        return t.Variant switch
        {
            // Beds are modelled head to the north; Pier points from the head toward the foot
            Props.Bed => t.Stack == 0 ? bedHeadIds[Facing(Opposite(t.Pier))] : bedFootIds[Facing(Opposite(t.Pier))],
            Props.Nightstand => nightstandIds[facing],
            Props.Wardrobe => wardrobeIds[facing],
            Props.WingChair => wingChairIds[facing],
            Props.Sofa => sofaIds[facing],
            Props.Palm => palmId,
            Props.MahjongTable => mahjongId,
            Props.Turntable => turntableId,
            Props.Boiler => boilerIds[facing],
            Props.Furnace => furnaceIds[facing],
            >= 40 => PropBlock(t),
            _ => t.SupplyBox ? BoxOf(t) : 0,
        };
    }

    /// <summary>Which side of its cell a boiler hall's row lies on: 0 the north bays (steam main on the north), 1 the south.</summary>
    private static int PlantSide(int gz) => Hashing.Mod(gz, WorldLayout.MacroSize) < WorldLayout.MacroSize / 2 ? 0 : 1;

    /// <summary>
    /// (Layout version 9) The header over a boiler bay's back row: a flue duct and steam main, ending against the wall
    /// where the row of bays does (nothing of the plant to its west or east), with the risers coming up into it.
    /// </summary>
    private int PlantHeader(in Tile t, int gx, int gz)
    {
        bool Joined(int x) => layout.TileAt(x, gz).Pipe is >= Pipes.PlantRun and <= Pipes.PlantThru;
        int end = !Joined(gx - 1) ? 1 : !Joined(gx + 1) ? 2 : 0;
        return plantHeaderIds[t.Pipe - Pipes.PlantRun, end, PlantSide(gz)];
    }

    /// <summary>Hotel walls: mahogany wainscot, then a red panel in a gilt frame, then a cream frieze.</summary>
    private int HotelWall(int rel) => rel == 1 ? wainscotId : rel == 2 ? panelId : friezeId;

    /// <summary>Shafts are lined with the same carpet as the room, all the way down.</summary>
    private void LineShaft(IServerChunk[] chunks, Tile[] tiles, int lx, int lz)
    {
        int bottom = Geometry.FloorY - WorldGeometry.ShaftDepth;
        foreach ((int dx, int dz) in Neighbours4)
        {
            int nx = lx + dx, nz = lz + dz;
            if (nx < 0 || nz < 0 || nx >= chunkSize || nz >= chunkSize) continue;
            if (tiles[WorldLayout.TileIndex(nx, nz)].Kind == TileKind.Pit) continue;
            for (int y = bottom + 1; y < Geometry.FloorY; y++) SetBlock(chunks, nx, y, nz, floorIds[(int)FloorKind.Carpet]);
        }
    }

    private static int BasePart(BaseStyle style) => style switch
    {
        BaseStyle.Baseboard => PartBaseboard,
        BaseStyle.Rail => PartRail,
        _ => PartPlain,
    };

    private void FillLayer(IServerChunk[] chunks, int y, int blockId)
    {
        chunks[y / chunkSize].Data.SetBlockBulk((y % chunkSize) * chunkSize * chunkSize, chunkSize, chunkSize, blockId);
    }

    private int Index3d(int lx, int y, int lz) => ((y % chunkSize) * chunkSize + lz) * chunkSize + lx;

    private void SetBlock(IServerChunk[] chunks, int lx, int y, int lz, int blockId)
    {
        chunks[y / chunkSize].Data.SetBlockUnsafe(Index3d(lx, y, lz), blockId);
    }

    private void SetFluid(IServerChunk[] chunks, int lx, int y, int lz, int blockId)
    {
        chunks[y / chunkSize].Data.SetFluid(Index3d(lx, y, lz), blockId);
    }

    private int GetBlock(IServerChunk[] chunks, int lx, int y, int lz) => chunks[y / chunkSize].Data.GetBlockIdUnsafe(Index3d(lx, y, lz));

    /// <summary>
    /// How many blocks of concrete lie under every floor before the ground begins (UndergroundSystem): what you need
    /// to break through to mine, and deep enough to hold everything the levels dig below their floors (Level 3's
    /// flooded tunnel, the fields' worms, the city's subway).
    /// </summary>
    public const int FoundationDepth = 8;

    /// <summary>The rock vanilla's land is made of at its top (what to fill on up with), or granite if none is found.</summary>
    private int GroundFill(IServerChunk[] chunks, int lx, int lz, int land)
    {
        for (int y = land; y > Math.Max(0, land - 48); y--)
        {
            int id = GetBlock(chunks, lx, y, lz);
            if (id != 0 && api.World.Blocks[id].BlockMaterial == EnumBlockMaterial.Stone) return id;
        }
        return groundFallbackId;
    }

    /// <summary>Fills a place above where vanilla's land ended (air, or sea) with rock.</summary>
    private void Petrify(IServerChunk[] chunks, int lx, int y, int lz, int rock)
    {
        SetBlock(chunks, lx, y, lz, rock);
        SetFluid(chunks, lx, y, lz, 0);
    }

    /// <summary>A supply box, or (picked over long ago) one torn open with nothing worth eating left in it.</summary>
    private int BoxOf(in Tile t) => t.Looted ? boxTornId : boxId;

    /// <summary>A crate, or one already prised open and emptied.</summary>
    private int CrateOf(in Tile t) => t.Looted ? crateOpenId : crateId;

    private int BlockId(string code)
    {
        Block block = api.World.GetBlock(new AssetLocation(code));
        if (block == null || block.BlockId == 0)
        {
            api.Logger.Error("[backrooms] Missing block {0}, the Backrooms will have holes", code);
            return 0;
        }
        return block.BlockId;
    }

    /// <summary>A block of this mod by code path.</summary>
    private int Id(string path)
    {
        if (modBlocks.TryGetValue(path, out int id)) return id;
        api.Logger.Error("[backrooms] Missing block backrooms:{0}, the Backrooms will have holes", path);
        return 0;
    }
}
