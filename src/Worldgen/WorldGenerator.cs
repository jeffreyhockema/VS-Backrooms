using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Worldgen;

/// <summary>
/// Writes the Backrooms into freshly generated chunk columns. All levels share one floor height. Vertically:
/// mantle, concrete, the floor, the walkable space of the level (3 blocks on Levels 0 and 2, 4 on Level 1), its
/// ceiling, then concrete (with a dusty crawlspace above the Level 0 tiles) up to a mantle cap.
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
    private static readonly (byte Prop, string Code, bool Oriented, string[] Kinds, bool HeadFirst)[] PropTable =
    {
        (Props.CardboardBoxes, "cardboardboxes", false, null, false),
        (Props.Workbench, "workbench", true, null, false),
        (Props.Toolbox, "toolbox", true, null, false),
        (Props.Plywood, "plywood", true, null, false),
        (Props.Tent, "tent", true, null, false),
        (Props.Bedroll, "bedroll", true, null, false),
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
        (Props.Tripwire, "tripwire", true, null, false),
        (Props.CafeTable, "cafetable", false, null, false),
        (Props.CafeChair, "cafechair", true, null, false),
        (Props.SnackCounter, "snackcounter", true, new[] { "plain", "register", "display" }, false),
        (Props.Stove, "stove", true, null, false),
        (Props.Fryer, "fryer", true, null, false),
        (Props.SnackShelf, "snackshelf", true, null, false),
        (Props.SnackVending, "snackvending", true, null, false),
        (Props.DrinkFridge, "drinkfridge", true, null, false),
        (Props.BonePile, "bonepile", false, null, false),
        (Props.MothHive, "mothhive", false, null, false),
        (Props.ScrapMetal, "scrapmetal", false, null, false),
        (Props.JawSkeleton, "jawskeleton", true, null, false),
        (Props.Ribcage, "ribcage", true, null, false),
        (Props.Backpack, "backpack", true, null, false),
        (Props.WreckCrate, "wreckcrate", false, null, false),
        (Props.MegMarker, "megmarker", true, null, false),
        (Props.RoadLamp, "roadlamp", false, null, false),
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
        (Props.Scarecrow, "scarecrow", true, null, false),
        (Props.PowerPole, "powerpole", true, null, false),
        (Props.Plough, "plough", true, null, false),
        (Props.WaterPump, "waterpump", false, null, false),
        (Props.Tractor, "tractor", false, null, false),
        (Props.HayRoll, "hayroll", true, null, false),
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
            ["alarmbell"] = Decor.AlarmBell, ["wallcables"] = Decor.WallCables, ["risers"] = Decor.Risers,
            ["fountain"] = Decor.Fountain, ["clock"] = Decor.Clock, ["whiteboard"] = Decor.Whiteboard, ["corkboard"] = Decor.Corkboard,
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
    private readonly int[] floorIds = new int[128];
    private readonly int[] overheadIds = new int[32];
    private readonly int[,,] propIds = new int[256, 4, 4];
    /// <summary>How many kinds each prop comes in, and whether it is modelled head to the north (beds, baths).</summary>
    private readonly byte[] propKinds = new byte[256];
    private readonly bool[] propHeadFirst = new bool[256];
    private readonly int[,,,] decorIds = new int[64, 256, 6, 4];
    private readonly int[,] exitLintelIds = new int[3, 2]; // concrete, white block, drywall x axis (we, ns)
    private readonly HashSet<int> flickerIds = new();

    // Level 0
    private readonly int ceilingTileId, lightOnId, lightLitId, lightOffId, lampDimId, lightFlickerId;
    private readonly int[,] wallIds = new int[5, 5];
    private readonly int[] archIds = new int[4];

    // Level 1
    private readonly int concreteWallId, concreteWallDamagedId, pillarId, pillarBaseId, pillarLightId, concreteCeilingId, crateId;
    private readonly int whiteUpperId, whiteBaseId, whiteLintelId, metalDoorLowerId, metalDoorUpperId;
    private readonly int[] pillarLetterIds = new int[6];
    private readonly int[,] hangingLightIds = new int[3, 2]; // state (on, off, flicker) x axis (we, ns)
    private readonly int[,] fireDoorIds = new int[2, 4]; // leaf (left, right) x facing
    private readonly int bulbOnId, conduitXId, conduitZId, dripXId, dripZId;
    private readonly int[] shelfIds = new int[4];
    private readonly int[] stairIds = new int[4];
    private readonly int wheelStopId, carColliderId;
    private readonly int[,] carIds = new int[4, 4]; // colour x facing (north, south, east, west)

    // Level 2
    private readonly int tunnelFloorId, tunnelCeilingId, drumId;
    private int tunnelDoorLowerId, tunnelDoorUpperId, lampRedId, ceilingFanId, almondSeepId;
    private readonly int pipeRunXId, pipeRunZId, pipeHubId, pipeLeakXId, pipeLeakZId;
    private readonly int[,] tunnelLightIds = new int[4, 4]; // state (white, warm, off, flicker) x pipes alongside (we, ns, hub, none)
    private readonly int[] cabinetIds = new int[4];
    private readonly Dictionary<string, int> tunnelWallIds = new();

    // Level 3
    private readonly int dustyFloorId, plasterCeilingId, transformerId, windowGlowId, manholeId, rungsId, sanctumStoneId;
    private readonly Dictionary<WallPattern, int> l3WallIds = new();
    private readonly Dictionary<(WallPattern, byte), int> l3FixtureIds = new();
    private readonly int cableXId, cableZId, cableHubId, cableDroopXId, cableDroopZId;
    private readonly int[,] cableLightIds = new int[3, 2]; // state (warm, off, flicker) x axis (we, ns)
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
    private readonly int wainscotId, panelId, friezeId, marbleId, plasterId, beamCeilingId, creamCeilingId, chandelierId;
    private readonly int sconceId, portraitId, beverlyId, staffSignId, doorLowerId, cageLowerId, cageUpperId, palmId, mahjongId, turntableId;
    private readonly int bulbOffId;
    private readonly int[] doorUpperIds = new int[8];
    private readonly int[] domeIds = new int[3]; // on, off, flicker
    private readonly int[] bedHeadIds = new int[4], bedFootIds = new int[4], nightstandIds = new int[4], wardrobeIds = new int[4];
    private readonly int[] wingChairIds = new int[4], sofaIds = new int[4], boilerIds = new int[4], furnaceIds = new int[4];

    /// <summary>Block entities to spawn for blocks placed by the terrain pass (flickering lights, dispensers).</summary>
    private readonly ConcurrentDictionary<long, List<(BlockPos Pos, string EntityClass)>> pendingEntities = new();

    public WorldGenerator(ICoreServerAPI api, WorldLayout layout)
    {
        this.api = api;
        this.layout = layout;
        seed = (ulong)api.World.Seed;
        chunkSize = api.WorldManager.ChunkSize;
        Geometry = new WorldGeometry(api.WorldManager.MapSizeY);

        foreach (Block block in api.World.Blocks)
        {
            if (block?.Code != null && block.Code.Domain == "backrooms") modBlocks[block.Code.Path] = block.BlockId;
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
        for (int i = 0; i < Sides.Length; i++)
        {
            shelfIds[i] = BlockId($"backrooms:metalshelf-{Sides[i]}");
            stairIds[i] = BlockId($"backrooms:concretestairs-{Sides[i]}");
            cabinetIds[i] = BlockId($"backrooms:machinecabinet-{Sides[i]}");
        }

        tunnelFloorId = BlockId("backrooms:concretefloor-dark");
        tunnelCeilingId = BlockId("backrooms:tunnelceiling");
        foreach (string type in new[] { "plain", "machinery", "brick", "warning", "pipes", "riser", "riserjoint", "valve" })
            tunnelWallIds[type] = BlockId($"backrooms:tunnelwall-{type}");
        drumId = BlockId("backrooms:oildrum");
        pipeRunXId = BlockId("backrooms:pipes-run-we");
        pipeRunZId = BlockId("backrooms:pipes-run-ns");
        pipeHubId = BlockId("backrooms:pipes-hub");
        pipeLeakXId = BlockId("backrooms:pipes-leak-we");
        pipeLeakZId = BlockId("backrooms:pipes-leak-ns");
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
        sanctumStoneId = Id("sanctumstone-plain");
        foreach ((WallPattern pattern, string code) in new[] { (WallPattern.GlazedTile, "glazed"), (WallPattern.RedBrick, "brick"), (WallPattern.Cinder, "cinder") })
        {
            l3WallIds[pattern] = BlockId($"backrooms:l3wall-{code}");
            l3FixtureIds[(pattern, Props.WallPipes)] = BlockId($"backrooms:l3wallfixture-{code}-pipes");
            l3FixtureIds[(pattern, Props.WallPanel)] = BlockId($"backrooms:l3wallfixture-{code}-panel");
            l3FixtureIds[(pattern, Props.WallFan)] = BlockId($"backrooms:l3wallfixture-{code}-fan");
        }
        l3WallIds[WallPattern.Stone] = sanctumStoneId;
        InitCity();
        InitPool();
        InitMotion();
        cableXId = BlockId("backrooms:cables-run-we");
        cableZId = BlockId("backrooms:cables-run-ns");
        cableHubId = BlockId("backrooms:cables-hub");
        cableDroopXId = Id("cabledroop-plain-north");
        cableDroopZId = Id("cabledroop-plain-east");
        string[] cableStates = { "warm", "off", "flicker" };
        for (int st = 0; st < 3; st++)
            for (int a = 0; a < 2; a++)
                cableLightIds[st, a] = BlockId($"backrooms:cablelight-{cableStates[st]}-{axes[a]}");
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
        beamCeilingId = BlockId("backrooms:hotelceiling-beams");
        creamCeilingId = BlockId("backrooms:hotelceiling-cream");
        chandelierId = BlockId("backrooms:chandelier");
        sconceId = BlockId("backrooms:hotelfixture-sconce");
        portraitId = BlockId("backrooms:hotelfixture-portrait");
        beverlyId = BlockId("backrooms:hotelfixture-beverly");
        staffSignId = BlockId("backrooms:staffsign");
        doorLowerId = BlockId("backrooms:hoteldoor-lower");
        for (int i = 0; i < 8; i++) doorUpperIds[i] = BlockId($"backrooms:hoteldoor-upper{i}");
        cageLowerId = BlockId("backrooms:cagedoor-lower");
        cageUpperId = BlockId("backrooms:cagedoor-upper");
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

        flickerIds.Add(lightFlickerId);
        flickerIds.Add(hangingLightIds[2, 0]);
        flickerIds.Add(hangingLightIds[2, 1]);
        for (int a = 0; a < 4; a++) flickerIds.Add(tunnelLightIds[3, a]);

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
        // The sea runs far deeper than the usual band, and Level 8's rock goes down further to be mined; the city's
        // streets lie lower than every other level's floor and its towers rise to the top of the world
        int bottom = level switch
        {
            7 => Math.Max(2, g.FloorY - 125),
            8 => g.BandBottom - 40,
            11 => g.CityBandBottom,
            WorldLayout.Poolrooms => g.FloorFor(level) - WorldGeometry.PoolPitDepth - 2,
            WorldLayout.Motion => g.FloorFor(level) - 6,
            _ => g.BandBottom,
        };
        int bandTop = level is 11 or WorldLayout.Motion ? g.TopY : g.BandTop;

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
        if (!openSky) FillLayer(chunks, g.CapY, mantleId);

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
                    string entityClass = block != 0 ? api.World.Blocks[block].EntityClass : null;
                    if (entityClass != null) entities.Add((new BlockPos(gx, y, gz), entityClass));
                }
                if (t.Kind == TileKind.Pit && t.Level == 0) LineShaft(chunks, tiles, lx, lz);

                int rainHeight = openSky ? top : g.CapY;
                mapChunk.RainHeightMap[column] = (ushort)rainHeight;
                mapChunk.WorldGenTerrainHeightMap[column] = (ushort)(openSky ? Math.Max(g.FloorFor(level), top) : g.FloorY);
                yMax = Math.Max(yMax, rainHeight);
            }
        }

        mapChunk.YMax = (ushort)yMax;
        lighting.Offer(request.ChunkX, request.ChunkZ, lightBottom, cellLight);
        lighting.Light(chunks, request.ChunkX, request.ChunkZ);
        if (entities.Count > 0) pendingEntities[ChunkKey(request.ChunkX, request.ChunkZ)] = entities;
    }

    /// <summary>Spawns the block entities for a column generated earlier (flickering lights, dispensers).</summary>
    public void SpawnBlockEntities(IChunkColumnGenerateRequest request, IBlockAccessor blockAccessor)
    {
        if (!pendingEntities.TryRemove(ChunkKey(request.ChunkX, request.ChunkZ), out var entities)) return;
        foreach ((BlockPos pos, string entityClass) in entities) blockAccessor.SpawnBlockEntity(entityClass, pos);
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
        }
        if (rel < 0) return BelowFloor(t, rel, out fluid);

        // Walls between levels (or around grand rooms) run solid up to the top of the tallest space next to them
        int room = t.Level == 1 || t.Grand ? WorldGeometry.MaxRoomHeight : WorldGeometry.RoomHeight;
        if (t.Tall && t.IsWallLike && rel > room && rel <= WorldGeometry.MaxRoomHeight + 1 && t.Level != 0) return concreteId;

        int block = t.Level switch
        {
            0 => Level0Block(t, rel, out fluid),
            1 => Level1Block(t, rel, gx, gz),
            2 => Level2Block(t, rel),
            3 => Level3Block(t, rel),
            4 => Level4Block(t, rel),
            5 => Level5Block(t, rel),
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
            if (rel == -4) fluid = waterId;
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

    // ---- Shared detail ----

    /// <summary>The decoration block for a wall tile at this height, or 0 if it has none there.</summary>
    private int Decorated(in Tile t, int rel)
    {
        if (t.Variant < Decor.First || rel < 0 || rel > 5) return 0;
        return decorIds[(int)t.Pattern, t.Variant, rel, Facing(t.Pier)];
    }

    /// <summary>The block for a detail prop, or 0 if the tile holds none.</summary>
    private int PropBlock(in Tile t)
    {
        if (t.Variant < 40) return 0;
        int kind = Math.Min(t.Stack, propKinds[t.Variant] - 1);
        return propIds[t.Variant, Math.Max(0, kind), Facing(propHeadFirst[t.Variant] ? Opposite(t.Pier) : t.Pier)];
    }

    /// <summary>An EXIT sign over a doorway; its faces look along the doorway (Pier north or south: across a west-east wall).</summary>
    private int ExitLintel(in Tile t)
    {
        int material = t.Pattern switch
        {
            WallPattern.WhiteBlock => 1,
            WallPattern.Drywall or WallPattern.OfficeGlass => 2,
            _ => 0,
        };
        return exitLintelIds[material, t.Pier is ArchPier.North or ArchPier.South ? 0 : 1];
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
                return wallIds[pattern, bottom ? (t.Outlet ? PartOutlet : BasePart(t.Base)) : PartUpper];
            case TileKind.Doorway:
                return top ? (pattern < 0 ? concreteId : wallIds[pattern, PartUpper]) : 0;
            case TileKind.ArchWindow:
                return bottom ? wallIds[Math.Max(pattern, 0), BasePart(t.Base)] : top ? archIds[(int)t.Pier] : 0;
            case TileKind.ArchDoor:
                return top ? archIds[(int)t.Pier] : 0;
            default:
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
                int decor = Decorated(t, rel);
                if (decor != 0) return decor;
                if (t.Pattern == WallPattern.WhiteBlock) return rel == 1 ? whiteBaseId : whiteUpperId;
                if (t.Pattern <= WallPattern.Manila && rel <= WorldGeometry.RoomHeight) return wallIds[(int)t.Pattern, rel == 1 ? BasePart(t.Base) : PartUpper];
                return t.Variant == 1 ? concreteWallDamagedId : concreteWallId;
            case TileKind.Doorway:
                if (rel == 1 && t.Variant == Props.FireDoor) return fireDoorIds[t.Stack & 1, Facing(t.Pier)];
                if (rel <= 2) return 0;
                if (rel == 3 && t.ExitSign) return ExitLintel(t);
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
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.Hub => pipeHubId,
                Pipes.DripX => dripXId,
                Pipes.DripZ => dripZId,
                Pipes.ConduitX => conduitXId,
                Pipes.ConduitZ => conduitZId,
                _ => 0,
            };
        }

        if (t.Variant == Props.Shelf && rel <= 2) return shelfIds[Facing(Opposite(t.Pier))];
        if (t.Variant == Props.Car) return rel == 1 ? carIds[t.Stack % 4, CarFacing(t.Pier)] : 0;
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

    private int Level2Block(in Tile t, int rel)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return tunnelFloorId;
        if (rel == room + 1) return t.IsWallLike ? concreteId : tunnelCeilingId;

        switch (t.Kind)
        {
            case TileKind.Wall:
                return TunnelWall(t.Pattern == WallPattern.Tunnel ? t.Variant : Props.WallPlain, rel);
            case TileKind.Doorway:
                return rel <= 2 ? 0 : tunnelWallIds["plain"];
            case TileKind.Door:
                return rel == 1 ? tunnelDoorLowerId : rel == 2 ? tunnelDoorUpperId : tunnelWallIds["plain"];
        }

        if (rel == room)
        {
            // The top block of a tunnel, above head height: fixtures and pipe bundles
            int axis = t.Pipe is Pipes.RunX or Pipes.LeakX ? 0 : t.Pipe is Pipes.RunZ or Pipes.LeakZ ? 1 : t.Pipe == Pipes.Hub ? 2 : 3;
            switch (t.Ceiling)
            {
                case CeilingKind.LightOn or CeilingKind.LightLit: return tunnelLightIds[0, axis];
                case CeilingKind.LightWarm: return tunnelLightIds[1, axis];
                case CeilingKind.LightOff: return tunnelLightIds[2, axis];
                case CeilingKind.LightFlicker: return tunnelLightIds[3, axis];
            }
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

        if (rel == 1)
        {
            if (t.Variant == Props.Drum) return drumId;
            if (t.Variant == Props.Cabinet) return cabinetIds[Facing(Opposite(t.Pier))];
            if (t.Variant == Props.Shelf) return shelfIds[Facing(Opposite(t.Pier))];
            if (t.Variant == Props.Desk) return deskIds[Facing(t.Pier)];
            if (t.Variant >= 40) return PropBlock(t);
            if (t.Variant == 0 && t.Stack > 0) return CrateOf(t);
            if (t.SupplyBox) return BoxOf(t);
        }
        return 0;
    }

    /// <summary>Tunnel walls: plain at the top, with pipework, valves or machinery at body height.</summary>
    private int TunnelWall(byte variant, int rel) => variant switch
    {
        Props.WallPipes => tunnelWallIds[rel == 2 ? "pipes" : "plain"],
        Props.WallRiser => tunnelWallIds[rel == 2 ? "riserjoint" : "riser"],
        Props.WallValve => tunnelWallIds[rel == 1 ? "valve" : rel == 2 ? "pipes" : "plain"],
        Props.WallMachinery => tunnelWallIds[rel <= 2 ? "machinery" : "plain"],
        Props.WallBrick => tunnelWallIds["brick"],
        Props.WallWarning => tunnelWallIds[rel == 2 ? "warning" : "plain"],
        _ => tunnelWallIds["plain"],
    };

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

    private int Level3Block(in Tile t, int rel)
    {
        // Galleries and halls are a block taller, squeezes a block lower
        int room = t.Grand ? WorldGeometry.MaxRoomHeight : t.Low ? WorldGeometry.RoomHeight - 1 : WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (t.Low && rel == room && !t.IsWallLike && t.Kind != TileKind.Bars) return 0; // nothing hangs where there is barely room to pass
        if (rel == 0) return t.Under == 2 ? manholeId : t.Floor == FloorKind.Dusty ? dustyFloorId : floorIds[(int)t.Floor];
        if (rel == room + 1) return t.IsWallLike ? concreteId : plasterCeilingId;

        int wall = l3WallIds.TryGetValue(t.Pattern, out int id) ? id : l3WallIds[WallPattern.GlazedTile];
        switch (t.Kind)
        {
            case TileKind.Wall:
                int decor = Decorated(t, rel);
                if (decor != 0) return decor;
                if (rel == 2 && l3FixtureIds.TryGetValue((l3WallIds.ContainsKey(t.Pattern) ? t.Pattern : WallPattern.GlazedTile, t.Variant), out int fixture)) return fixture;
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
            int axis = t.Pipe is Pipes.RunX or Pipes.CableX or Pipes.CableDroopX ? 0 : 1;
            switch (t.Ceiling)
            {
                case CeilingKind.LightWarm or CeilingKind.LightOn: return cableLightIds[0, axis];
                case CeilingKind.LightOff: return cableLightIds[1, axis];
                case CeilingKind.LightFlicker: return cableLightIds[2, axis];
            }
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.Hub => pipeHubId,
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

    private int BarsBlock(in Tile t) => t.Pier is ArchPier.North or ArchPier.South ? barsNsId : barsWeId;

    // ---- Level 4: abandoned office ----

    private int Level4Block(in Tile t, int rel)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 2) return concreteId;
        if (rel == room + 2) return t.IsWallLike ? concreteId : 0; // void above the drop ceiling
        if (rel == 0) return floorIds[(int)t.Floor];
        if (rel == room + 1)
        {
            if (t.IsWallLike) return concreteId;
            if (t.Worn) return 0;
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
                return t.ExitSign ? ExitLintel(t) : t.Pattern == WallPattern.OfficeGlass ? officeGlassId : officeWallId;
        }

        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? officeWallId : stairIds[Facing(t.Pier)];
        // A cable hanging down out of a gap in the ceiling
        if (rel == room && t.Worn && t.Pipe is Pipes.CableDroopX or Pipes.CableDroopZ) return t.Pipe == Pipes.CableDroopX ? cableDroopXId : cableDroopZId;
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

    private int Level5Block(in Tile t, int rel)
    {
        int room = t.Grand ? WorldGeometry.MaxRoomHeight : WorldGeometry.RoomHeight;
        bool boiler = t.Floor == FloorKind.Dusty;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return boiler ? dustyFloorId : floorIds[(int)t.Floor];
        // The staff stairs, climbing into the ceiling
        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? plasterId : stairIds[Facing(t.Pier)];
        if (rel == room + 1)
        {
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
            return boiler ? plasterCeilingId : beamCeilingId;
        }

        switch (t.Kind)
        {
            case TileKind.Wall:
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
                return rel == 1 ? doorLowerId : rel == 2 ? doorUpperIds[t.Variant % 8] : HotelWall(rel);
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                if (rel == 3 && t.ExitSign) return staffSignId;
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
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.LeakX => pipeLeakXId,
                Pipes.LeakZ => pipeLeakZId,
                _ => 0,
            };
        }
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

    /// <summary>Hotel walls: mahogany wainscot, then a red panel in a gilt frame, then a cream frieze.</summary>
    private int HotelWall(int rel) => rel == 1 ? wainscotId : rel == 2 ? panelId : friezeId;

    /// <summary>Shafts are lined with the same carpet as the room, all the way down.</summary>
    private void LineShaft(IServerChunk[] chunks, Tile[] tiles, int lx, int lz)
    {
        int bottom = Geometry.FloorY - WorldGeometry.ShaftDepth;
        foreach ((int dx, int dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
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
