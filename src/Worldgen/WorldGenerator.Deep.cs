using System;
using System.Collections.Generic;
using Vintagestory.API.Common;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Levels 6 to 10. Unlike the levels above, some of these are not columns of a fixed pattern: Level 7's
/// sea runs a hundred blocks deep, Level 8's caves are carved in 3D out of real stratified rock and ore, and
/// Levels 9 and 10 lie under the open sky.
/// </summary>
public sealed partial class WorldGenerator
{
    private const ulong SaltCave = 0xC401, SaltCaveTube = 0xC402, SaltStrata = 0xC403, SaltOre = 0xC404, SaltPool = 0xC405, SaltSpike = 0xC406;

    // Level 6 and 6.1
    private int l6WallId, l6FloorId, l6CeilingId, waveEchoId;
    private int snackCeilingId, skylightId, snackWindowId, rustyLowerId, rustyUpperId, glassLowerId, glassUpperId, kitchenLowerId, kitchenUpperId, ventId;
    private readonly Dictionary<WallPattern, int> snackWallIds = new();

    // Level 7
    private int oceanCeilingId, oceanGlowId, islandRockId, seabedId, tarId, roomFloorId;
    private const ulong SaltCeilingGlow = 0x7C20;
    // Level 7 from layout version 9: the high ceiling (plain and glowing), the sunken rooms' windows, and vanilla's rope
    // ladder by the side it hangs against (as Sides)
    private int seaCeilingId, seaCeilingGlowId, glassId;
    private readonly int[] ropeLadderIds = new int[4];

    // Level 8: the road lamp with its arm out over the road (layout version 5), by the side it reaches toward
    private readonly int[] roadLampArmIds = new int[4];

    // Level 8: rock strata and the ores that can sit in each
    private string[] strata;
    private int[] strataIds;
    /// <summary>The Almond Water seep in each of the strata's rocks.</summary>
    private int[] seepIds;
    /// <summary>The ores that come in grades, and the minerals that don't, as vanilla names them.</summary>
    private static readonly string[] GradedOres = { "nativecopper", "malachite", "cassiterite", "limonite", "hematite", "magnetite", "quartz_nativegold", "galena", "galena_nativesilver", "sphalerite", "bismuthinite" };
    private static readonly string[] Minerals = { "bituminouscoal", "lignite", "anthracite", "sulfur", "quartz", "lapislazuli", "olivine", "fluorite", "graphite", "cinnabar" };
    private const int OreNativeCopper = 0, OreMalachite = 1, OreCassiterite = 2, OreLimonite = 3, OreHematite = 4, OreMagnetite = 5,
        OreGold = 6, OreGalena = 7, OreSphalerite = 9, OreBismuthinite = 10;
    private const int MineralCoal = 0, MineralLignite = 1, MineralSulfur = 3, MineralQuartz = 4, MineralLapis = 5, MineralOlivine = 6, MineralGraphite = 8;
    /// <summary>Ore blocks by stratum (index into <see cref="strata"/>), ore and grade (poor to bountiful), 0 where vanilla has none.</summary>
    private int[,,] gradedOreIds;
    /// <summary>Mineral blocks by stratum and mineral, 0 where vanilla has none.</summary>
    private int[,] mineralIds;
    private int gravelId, clayId, carpetSeamId, wallpaperSeamId;

    // Levels 9 and 10
    private int asphaltId, asphaltLeavesId, asphaltWetId, sidewalkId, lawnId, bareSoilId, logId, leavesId, wormId, lakeBedId;
    private int houseCeilingId, houseDoorLowerId, houseDoorUpperId, garageLowerId, garageUpperId, hayId, tallGrassId, cropSpeltId, cropRyeId, cropFlaxId;
    private readonly int[,] sidingIds = new int[5, 4];
    private readonly Dictionary<WallPattern, int> interiorIds = new();
    /// <summary>House windows by kind (0 and 1 dark, 2 lit) and the side their outside faces.</summary>
    private readonly int[,] windowIds = new int[3, 4];
    // The Suburbs from layout version 5: the floor between two storeys (under it a plain ceiling, a dead light or a lit
    // one), the stairs, a porch's deck, steps and posts, the lamp by the door (dark or lit) and the street signs' second blades
    private readonly int[] storeyFloorIds = new int[3];
    private readonly int[] houseStairIds = new int[4];
    private readonly int[,] porchLampIds = new int[2, 4];
    private readonly int[] suburbBladeIds = new int[8];
    private int porchDeckId, porchStepId, porchPostId;
    /// <summary>A porch post's foot in the railing, with the rails coming in to it, by the railing's mask (as <see cref="fenceIds"/>).</summary>
    private readonly int[] porchPostRailIds = new int[16];
    // The Suburbs from layout version 9 (WorldLayout.PlanExteriorV9): how high its columns go (over its floor), the tall
    // windows by glass (dark, lit), part (SuburbWindowParts) and side; the doors that open by state (closed, open,
    // locked), hinge end (as modelled facing north: west, east), half and side; the cased garage door by part and side;
    // the chimney's cap by the side its other half is on (or none); the stairs' balustraded steps by step (foot, flight),
    // balustrade end and the way they climb
    private const int SuburbTop = 24;
    private static readonly string[] SuburbWindowParts =
        { "sashlower", "sashupper", "shutterlower", "shutterupper", "picwlower", "picmlower", "picelower", "picwupper", "picmupper", "piceupper" };
    private readonly int[,,] suburbWindowIds = new int[2, 10, 4];
    private readonly int[,,,] suburbDoorIds = new int[3, 2, 2, 4];
    private readonly int[,] casedGarageIds = new int[6, 4];
    private readonly int[] chimneyCapIds = new int[5];
    private readonly int[,,] stairRailIds = new int[2, 2, 4];
    private readonly int[] roofIds = new int[3];
    private readonly int[] barnWallIds = new int[2];
    private readonly int[] fenceIds = new int[16];

    // The finer detail of Levels 6 to 10
    private int poolFloorId, jettyId, siloId, siloTopId, chimneyId, kelpSectionId, kelpTopId, webId, crystalUpId, crystalDownId, mushroomId, remainsId;
    private readonly int[] houseLightIds = new int[2];
    private readonly int[,,] roofSlopeIds = new int[4, 2, 4];
    /// <summary>The pitched roof drawn course by course (graphics pass B11): cover, gable siding, form, side (see PitchRoof).</summary>
    private readonly int[,,,] pitchRoofIds = new int[4, 8, 7, 4];
    private readonly int[,] sidingCornerIds = new int[5, 4];
    private readonly int[] flowerIds = new int[8];
    private readonly int[] vegetableIds = new int[6];
    private readonly Dictionary<string, int> looseStoneIds = new();
    // Vanilla resources laid out for Vintage Story's own progression
    private int[] looseStoneL1Ids = Array.Empty<int>();
    private int looseFlintId, cattailId, skepId, quernId;
    private readonly int[] berryBushIds = new int[5];
    private readonly Dictionary<(string Ore, string Rock), int> looseOreIds = new();
    private static readonly string[] LooseOres = { "nativecopper", "nativecopper", "cassiterite", "bituminouscoal", "malachite" };

    private static readonly string[] FenceTypes =
        { "empty", "n", "e", "ne", "s", "ns", "es", "nes", "w", "nw", "ew", "new", "sw", "nsw", "esw", "nesw" };

    /// <summary>Level 8's noise, per column (see <see cref="CaveColumn"/>).</summary>
    private CaveColumns caveColumns;

    private void InitDeep()
    {
        caveColumns = new CaveColumns((gx, gz) =>
        {
            var column = new CaveColumn(seed, gx, gz, Geometry.FloorY, Geometry.BandBottom - 41, Geometry.BandTop + 1, Noise2,
                SaltCave, SaltCaveTube, SaltStrata, SaltOre, SaltPool, veins: layout.Version >= 5);
            // From layout version 9, the rich deposits the 9th Road goes round
            if (layout.L8DepositAt(gx, gz) is int deposit and > 0)
            {
                column.DepositKind = deposit >> 8;
                column.DepositStrength = (deposit & 255) / 255.0;
            }
            // From layout version 9, the spider nests whose webs are strung through the caves
            if (layout.Version >= 9) column.Nest = layout.L8NestNear(gx, gz);
            return column;
        });
        l6WallId = Id("l6block-wall");
        l6FloorId = Id("l6block-floor");
        l6CeilingId = Id("l6block-ceiling");
        waveEchoId = Id("waveecho");
        floorIds[(int)FloorKind.L6Floor] = l6FloorId;
        floorIds[(int)FloorKind.SnackTerrazzo] = Id("snackfloor-terrazzo");
        floorIds[(int)FloorKind.SnackChecker] = Id("snackfloor-checker");
        floorIds[(int)FloorKind.SnackQuarry] = Id("snackfloor-quarry");
        snackWallIds[WallPattern.SnackMall] = Id("snackwall-mall");
        snackWallIds[WallPattern.SnackPanel] = Id("snackwall-panel");
        snackWallIds[WallPattern.SnackTile] = Id("snackwall-tile");
        snackWindowId = Id("snackwall-window");
        snackCeilingId = Id("snackceiling-grid");
        skylightId = Id("snackceiling-skylight");
        rustyLowerId = Id("rustydoor-lower");
        rustyUpperId = Id("rustydoor-upper");
        glassLowerId = Id("glassdoors-lower");
        glassUpperId = Id("glassdoors-upper");
        kitchenLowerId = Id("kitchendoor-lower");
        kitchenUpperId = Id("kitchendoor-upper");
        ventId = Id("ventgrate");

        oceanCeilingId = Id("oceanceiling-plain");
        oceanGlowId = Id("oceanceiling-glow");
        islandRockId = Id("islandrock-plain");
        seabedId = BlockId("backrooms:carpet-soaked");
        tarId = Id("tar");
        roomFloorId = seabedId; // the entry room's carpet, soaked with the water pooling on it
        floorIds[(int)FloorKind.Seabed] = seabedId;
        floorIds[(int)FloorKind.Tar] = tarId;
        seaCeilingId = Id("seaceiling-plain");
        seaCeilingGlowId = Id("seaceiling-glow");
        glassId = GameId("game:glass-plain", "game:glass-quartz");
        for (int f = 0; f < 4; f++) ropeLadderIds[f] = GameId($"game:ladder-rope-{Sides[f]}", $"game:ladder-wood-{Sides[f]}");

        // Level 8: rock types in order of the strata (deliberately not geological order), with their ores. Limestone,
        // chalk and halite are there for the quern: lime for mortar and leather, salt for curing meat
        strata = new[] { "granite", "limestone", "andesite", "shale", "basalt", "sandstone", "chalk", "granite", "slate", "claystone", "peridotite", "chert", "halite" };
        strataIds = new int[strata.Length];
        for (int i = 0; i < strata.Length; i++) strataIds[i] = GameId($"game:rock-{strata[i]}", "game:rock-granite");
        seepIds = new int[strata.Length];
        for (int i = 0; i < strata.Length; i++) seepIds[i] = Id($"almondseeprock-{strata[i]}");
        string[] grades = { "poor", "medium", "rich", "bountiful" };
        gradedOreIds = new int[strata.Length, GradedOres.Length, grades.Length];
        mineralIds = new int[strata.Length, Minerals.Length];
        for (int r = 0; r < strata.Length; r++)
        {
            for (int o = 0; o < GradedOres.Length; o++)
                for (int g = 0; g < grades.Length; g++)
                    gradedOreIds[r, o, g] = OptionalId($"game:ore-{grades[g]}-{GradedOres[o]}-{strata[r]}");
            for (int m = 0; m < Minerals.Length; m++) mineralIds[r, m] = OptionalId($"game:ore-{Minerals[m]}-{strata[r]}");
        }
        gravelId = GameId("game:gravel-granite", "game:gravel-andesite");
        floorIds[(int)FloorKind.Gravel] = gravelId;
        for (int f = 0; f < 4; f++) roadLampArmIds[f] = Id($"roadlamparm-{Sides[f]}");
        clayId = GameId("game:rawclay-blue-none", "game:rawclay-red-none");
        carpetSeamId = BlockId("backrooms:carpet-normal");
        wallpaperSeamId = BlockId("backrooms:wallpaper-chevron-upper");
        InitCaves(); // the living detail of Levels 7 and 8 (WorldGenerator.Caves.cs)

        // Levels 9 and 10
        asphaltId = Id("asphalt-plain");
        asphaltLeavesId = Id("asphalt-leaves");
        asphaltWetId = Id("asphalt-wet");
        sidewalkId = Id("sidewalk-plain");
        lawnId = GameId("game:soil-medium-normal", "game:soil-low-normal");
        bareSoilId = GameId("game:soil-medium-none", "game:soil-low-none");
        floorIds[(int)FloorKind.Asphalt] = asphaltId;
        floorIds[(int)FloorKind.AsphaltLeaves] = asphaltLeavesId;
        floorIds[(int)FloorKind.AsphaltWet] = asphaltWetId;
        floorIds[(int)FloorKind.Sidewalk] = sidewalkId;
        floorIds[(int)FloorKind.Lawn] = lawnId;
        floorIds[(int)FloorKind.Grass] = lawnId;
        // Crops only stay ripe on a block whose code starts with "farmland"
        floorIds[(int)FloorKind.Field] = OptionalId("backrooms:farmland-old") is int field and not 0 ? field : bareSoilId;
        floorIds[(int)FloorKind.HouseWood] = Id("housefloor-wood");
        floorIds[(int)FloorKind.HouseCarpet] = Id("housefloor-carpet");
        floorIds[(int)FloorKind.HouseTile] = Id("housefloor-tile");
        floorIds[(int)FloorKind.HouseLino] = Id("housefloor-lino");
        floorIds[(int)FloorKind.Garage] = Id("housefloor-garage");
        floorIds[(int)FloorKind.DirtRoad] = Id("dirtroad-plain");
        floorIds[(int)FloorKind.DirtTracks] = Id("dirtroad-tracks");
        string[] sidings = { "white", "blue", "yellow", "green", "brick" };
        string[] sides = { "north", "east", "south", "west" };
        for (int s = 0; s < sidings.Length; s++)
            for (int f = 0; f < 4; f++)
                sidingIds[s, f] = Id($"housewall-{sidings[s]}-{sides[f]}");
        interiorIds[WallPattern.InteriorFloral] = Id("houseinterior-floral");
        interiorIds[WallPattern.InteriorStripe] = Id("houseinterior-stripe");
        interiorIds[WallPattern.InteriorBeige] = Id("houseinterior-beige");
        interiorIds[WallPattern.InteriorGreen] = Id("houseinterior-green");
        interiorIds[WallPattern.InteriorTile] = Id("houseinterior-tile");
        for (int f = 0; f < 4; f++)
        {
            windowIds[1, f] = windowIds[0, f] = Id($"housewindow-dark-{sides[f]}");
            windowIds[2, f] = Id($"housewindow-lit-{sides[f]}");
            houseStairIds[f] = Id($"housestairs-{sides[f]}");
            porchLampIds[0, f] = Id($"porchlamp-off-{sides[f]}");
            porchLampIds[1, f] = Id($"porchlamp-on-{sides[f]}");
        }
        storeyFloorIds[0] = Id("housestorey-plain");
        storeyFloorIds[1] = Id("housestorey-lightoff");
        storeyFloorIds[2] = Id("housestorey-lighton");
        porchDeckId = Id("porchdeck-deck");
        porchStepId = Id("porchdeck-step");
        porchPostId = Id("porchpost");
        for (int m = 1; m < 16; m++) porchPostRailIds[m] = modBlocks.TryGetValue($"porchpostrail-{FenceTypes[m]}", out int postRail) ? postRail : porchPostId;
        string[] streets = { "willow", "linden", "aspen", "poplar", "holly", "laurel", "spruce", "cherry" };
        for (int k = 0; k < 8; k++) suburbBladeIds[k] = Id($"suburbsignblade-{streets[k]}");
        roofIds[0] = Id("houseroof-grey");
        roofIds[1] = Id("houseroof-brown");
        roofIds[2] = Id("houseroof-red");
        houseCeilingId = Id("houseceiling-plain");
        houseDoorLowerId = Id("housedoor-lower");
        houseDoorUpperId = Id("housedoor-upper");
        garageLowerId = Id("garagedoor-lower");
        garageUpperId = Id("garagedoor-upper");
        string[] glasses = { "dark", "lit" }, doorStates = { "closed", "open", "locked" }, ends = { "w", "e" }, halves2 = { "lower", "upper" };
        string[] garageParts = { "lowerw", "lowerm", "lowere", "upperw", "upperm", "uppere" }, capJoins = { "none", "north", "east", "south", "west" };
        for (int f = 0; f < 4; f++)
        {
            for (int gl = 0; gl < 2; gl++)
                for (int p = 0; p < SuburbWindowParts.Length; p++) suburbWindowIds[gl, p, f] = Id($"suburbwindow-{glasses[gl]}-{SuburbWindowParts[p]}-{sides[f]}");
            for (int st = 0; st < 3; st++)
                for (int e = 0; e < 2; e++)
                    for (int hf = 0; hf < 2; hf++) suburbDoorIds[st, e, hf, f] = Id($"suburbdoor-{doorStates[st]}-{ends[e]}-{halves2[hf]}-{sides[f]}");
            for (int p = 0; p < garageParts.Length; p++) casedGarageIds[p, f] = Id($"garagedoorcased-{garageParts[p]}-{sides[f]}");
            for (int foot = 0; foot < 2; foot++)
                for (int e = 0; e < 2; e++) stairRailIds[foot, e, f] = Id($"housestairsrail-{(foot == 1 ? "foot" : "flight")}-{ends[e]}-{sides[f]}");
        }
        for (int c = 0; c < capJoins.Length; c++) chimneyCapIds[c] = Id($"chimneycap-{capJoins[c]}");
        barnWallIds[0] = Id("barnwall-red");
        barnWallIds[1] = Id("barnwall-grey");
        logId = GameId("game:log-grown-oak-ud", "game:log-placed-oak-ud");
        leavesId = GameId("game:leaves-grown-oak", "game:leaves-placed-oak");
        wormId = Id("wormmass");
        lakeBedId = GameId("game:muddygravel", "game:soil-low-none");
        hayId = GameId("game:hay-normal-ud");
        tallGrassId = GameId("game:tallgrass-tall-free", "game:tallgrass-medium-free");
        cropSpeltId = GameId("game:crop-spelt-9", "game:crop-spelt-8");
        cropRyeId = GameId("game:crop-rye-9", "game:crop-rye-8");
        cropFlaxId = GameId("game:crop-flax-9", "game:crop-flax-8", "game:crop-flax-7");
        for (int m = 0; m < 16; m++) fenceIds[m] = GameId($"game:woodenfence-aged-{FenceTypes[m]}-free");

        // The finer detail of Levels 6 to 10
        floorIds[(int)FloorKind.L6Wet] = Id("l6block-wet");
        floorIds[(int)FloorKind.Stubble] = Id("fieldstubble-plain");
        floorIds[(int)FloorKind.Porch] = Id("housefloor-porch");
        floorIds[(int)FloorKind.Driveway] = Id("housefloor-driveway");
        floorIds[(int)FloorKind.HouseRug] = Id("housefloor-rug");
        floorIds[(int)FloorKind.AsphaltLine] = Id("asphalt-line");
        floorIds[(int)FloorKind.AsphaltCrossing] = Id("asphalt-crossing");
        floorIds[(int)FloorKind.Manhole] = Id("asphalt-manhole");
        floorIds[(int)FloorKind.AsphaltLineNS] = Id("asphalt-linens");
        floorIds[(int)FloorKind.AsphaltCrossingNS] = Id("asphalt-crossingns");
        floorIds[(int)FloorKind.PoolEdge] = Id("pool-coping");
        poolFloorId = Id("pool-floor");
        floorIds[(int)FloorKind.PoolDeep] = poolFloorId;
        floorIds[(int)FloorKind.Flowerbed] = floorIds[(int)FloorKind.Field];
        jettyId = Id("jetty-planks");
        floorIds[(int)FloorKind.Jetty] = jettyId;
        siloId = Id("silo-wall");
        siloTopId = Id("silo-top");
        chimneyId = Id("chimney-brick");
        string[] roofMaterials = { "grey", "brown", "red", "barn" }, halves = { "lower", "upper" }, sideNames = { "north", "east", "south", "west" };
        for (int m = 0; m < 4; m++)
            for (int hf = 0; hf < 2; hf++)
                for (int f = 0; f < 4; f++)
                    roofSlopeIds[m, hf, f] = Id($"roofslope-{roofMaterials[m]}-{halves[hf]}-{sideNames[f]}");
        // (a cover goes with its own gables: the houses' shingles with the five sidings, the barns' tin with their boards)
        string[] gables = { "none", "white", "blue", "yellow", "green", "brick", "barnred", "barngrey" };
        string[] forms = { "eave", "lower", "upper", "peaklower", "peakupper", "ridgelower", "ridgeupper" };
        for (int m = 0; m < 4; m++)
            for (int g = 0; g < gables.Length; g++)
            {
                if (g != 0 && (m == 3) != (g >= 6)) continue;
                for (int fm = 0; fm < forms.Length; fm++)
                    for (int f = 0; f < 4; f++)
                        pitchRoofIds[m, g, fm, f] = Id($"pitchroof-{roofMaterials[m]}-{gables[g]}-{forms[fm]}-{sideNames[f]}");
            }
        string[] sidingNames = { "white", "blue", "yellow", "green", "brick" }, corners = { "ne", "nw", "se", "sw" };
        for (int sd = 0; sd < 5; sd++)
            for (int c = 0; c < 4; c++)
                sidingCornerIds[sd, c] = Id($"housecorner-{sidingNames[sd]}-{corners[c]}");
        houseLightIds[0] = Id("houseceiling-lightoff");
        houseLightIds[1] = Id("houseceiling-lighton");
        string[] flowers = { "cornflower", "wilddaisy", "forgetmenot", "goldenpoppy", "lilyofthevalley", "bluebell", "catmint", "daffodil" };
        for (int i = 0; i < flowers.Length; i++) flowerIds[i] = GameId($"game:flower-{flowers[i]}-free", "game:flower-wilddaisy-free");
        vegetableIds[0] = GameId("game:crop-carrot-7", "game:crop-carrot-6");
        vegetableIds[1] = GameId("game:crop-cabbage-12", "game:crop-cabbage-11", "game:crop-cabbage-10");
        vegetableIds[2] = GameId("game:crop-onion-7", "game:crop-onion-6", "game:crop-onion-5", "game:crop-carrot-7");
        vegetableIds[3] = GameId("game:crop-turnip-5", "game:crop-carrot-7");
        vegetableIds[4] = GameId("game:crop-parsnip-8", "game:crop-parsnip-7", "game:crop-parsnip-6", "game:crop-carrot-7");
        vegetableIds[5] = GameId("game:crop-sunflower-12", "game:crop-sunflower-11", "game:crop-cabbage-12");
        kelpSectionId = GameId("game:aquatic-kelp-section", "game:seaweed-section");
        kelpTopId = GameId("game:aquatic-kelp-top", "game:seaweed-top");
        webId = GameId("game:spiderweb");
        crystalUpId = OptionalId("game:crystal-milkyquartz-small1-up");
        crystalDownId = OptionalId("game:crystal-amethyst-small2-down");
        mushroomId = OptionalId("game:mushroom-fieldmushroom-normal");
        remainsId = OptionalId("game:drycarcass-humanoid1");
        foreach (string rock in strata) looseStoneIds[rock] = OptionalId($"game:loosestones-{rock}-free");
        foreach (string rock in strata)
            foreach (string ore in LooseOres)
                looseOreIds[(ore, rock)] = OptionalId($"game:looseores-{ore}-{rock}-free");
        var l1Stones = new List<int>();
        foreach (string rock in new[] { "chert", "andesite", "granite" })
            if (OptionalId($"game:loosestones-{rock}-free") is int id and not 0) l1Stones.Add(id);
        looseStoneL1Ids = l1Stones.ToArray();
        looseFlintId = GameId("game:looseflints-chalk-free", "game:looseflints-limestone-free", "game:looseflints-chert-free", "game:looseflints-granite-free");
        cattailId = GameId("game:tallplant-coopersreed-land-normal-free", "game:tallgrass-tall-free");
        skepId = OptionalId("game:skep-reed-populated-east");
        quernId = GameId("game:quern-granite", "game:quern-andesite");
        string[] bushes = { "blueberry", "raspberry", "redcurrant", "blackcurrant", "strawberry" };
        for (int i = 0; i < bushes.Length; i++) berryBushIds[i] = GameId($"game:fruitingbush-grown-{bushes[i]}-free", $"game:fruitingbush-wild-{bushes[i]}-free");
    }

    // ---- Level 6: total darkness ----

    private int Level6Block(in Tile t, int rel)
    {
        if (t.Zone == 1) return Level61Block(t, rel);
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == room + 1) return t.IsWallLike ? concreteId : l6CeilingId;
        if (rel == 0) return t.Under is >= Unders.Descent1 and <= Unders.Descent3 ? DescentBlock(t, rel) : t.Floor == FloorKind.L6Wet ? floorIds[(int)FloorKind.L6Wet] : l6FloorId;
        switch (t.Kind)
        {
            case TileKind.Wall:
                int decor = Decorated(t, rel);
                return decor != 0 ? decor : t.Pattern == WallPattern.L6Wall ? l6WallId : concreteId;
            case TileKind.Doorway:
                return rel <= 2 ? 0 : l6WallId;
        }
        return rel == 1 ? AnyProp(t, rel) : 0;
    }

    /// <summary>The stairs going down toward the waves: step k of 3 is a stair block k-1 below the floor.</summary>
    private int DescentBlock(in Tile t, int rel)
    {
        if (layout.Version >= 9) return StairwellBlock(t, rel);
        int step = t.Under - Unders.Descent1; // 0, 1, 2
        int stairRel = -step;
        if (rel == stairRel) return stairIds[Facing(Opposite(t.Pier))];
        if (rel > stairRel) return 0;
        if (step == 2 && rel == stairRel - 1) return waveEchoId; // the faint sound of waves, from somewhere below
        return concreteId;
    }

    /// <summary>
    /// From layout version 9, the stairwell down toward the waves (<see cref="WorldLayout.L6DescentSteps"/>), at or below
    /// the floor: step n's tread is a stair block n - 1 down, solid under it. The first four steps are open to the chamber
    /// over them; the rest are cut on into the rock with three blocks of headroom over each tread, stepping down with
    /// the stairs, and the floor over them stays (as the floor of whatever passage crosses there). The landing's floor
    /// is a block lower than the last step, three blocks high, with the faint sound of waves under its far end.
    /// </summary>
    private int StairwellBlock(in Tile t, int rel)
    {
        bool landing = t.Under != Unders.Descent1;
        int step = landing ? WorldLayout.L6DescentSteps + 1 : t.Stair;
        int tread = 1 - step;
        if (rel == tread) return landing ? l6FloorId : stairIds[Facing(Opposite(t.Pier))];
        // (Under the far end of the landing, the waves)
        if (rel < tread) return rel == tread - 1 && t.Detail == WorldLayout.L6WaveEcho ? waveEchoId : concreteId;
        if (step <= 4 && !t.IsWallLike) return 0; // open to the chamber
        return rel <= tread + 3 && rel < 0 ? 0 : concreteId;
    }

    // ---- Level 6.1: the Snackrooms ----

    private int Level61Block(in Tile t, int rel)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == room + 1) return t.IsWallLike ? concreteId : t.Ceiling == CeilingKind.LightOn ? skylightId : snackCeilingId;
        if (rel == 0) return floorIds[(int)t.Floor];
        int wall = snackWallIds.TryGetValue(t.Pattern, out int w) ? w : snackWallIds[WallPattern.SnackMall];
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (t.Pattern == WallPattern.SnackWindow) return rel == 2 ? snackWindowId : snackWallIds[WallPattern.SnackMall];
                int decor = t.Variant >= Decor.First ? decorIds[(int)WallPattern.SnackMall, t.Variant, rel, Facing(t.Pier)] : 0;
                return decor != 0 ? decor : wall;
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                int sign = t.Variant >= Decor.First ? decorIds[(int)WallPattern.SnackMall, t.Variant, rel, Facing(t.Pier)] : 0;
                return sign != 0 ? sign : wall;
            case TileKind.Door:
                return t.Variant switch
                {
                    1 => rel == 1 ? rustyLowerId : rel == 2 ? rustyUpperId : wall,
                    2 => rel == 1 ? glassLowerId : rel == 2 ? glassUpperId : wall,
                    3 => rel == 1 ? kitchenLowerId : rel == 2 ? kitchenUpperId : wall,
                    _ => rel == 1 ? ventId : wall,
                };
        }
        // In a vending machine room, another machine lying across the top of this one (layout version 5)
        if (rel == 2 && t.Detail == WorldLayout.SnackPiledOn && t.Variant is Props.SnackVending or Props.VendingPile or Props.BrokenVending)
            return propIds[Props.VendingPile, 2, Facing(t.Pier)];
        return rel == 1 ? AnyProp(t, rel) : 0;
    }

    // ---- Level 7: the sea under the ceiling ----

    private int Level7Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        // From layout version 9: the high ceiling, the entry rooms' piers hung from it, and the sunken rooms
        if (layout.Version >= 9 && HighSeaBlock(t, gx, gz, rel, out fluid) is int high and >= 0) return high;
        // Above the water: the ceiling, and the entry rooms set into it
        if (rel >= 5)
        {
            if (t.Zone != 0 && rel <= 9)
            {
                if (rel == 9) return t.Ceiling == CeilingKind.LightOn ? lightOnId : concreteId;
                if (rel == 5) return t.Zone == 2 ? 0 : roomFloorId; // the doorway in the floor, straight down onto the water
                if (rel == 6 && t.Zone == 1)
                {
                    return t.Stack switch
                    {
                        1 => propIds[Props.HotelBookshelf, 0, 1],
                        2 => propIds[Props.CoffeeTable, 0, 0],
                        3 => propIds[Props.HotelChair, 0, 3],
                        _ => 0,
                    };
                }
                return 0;
            }
            if (rel == 5 && !t.IsWallLike) return CeilingGlows(gx, gz) ? oceanGlowId : oceanCeilingId;
            return concreteId;
        }
        // A pillar of the islands' rock, from an island or the seabed up into the ceiling (layout version 5)
        if (t.Detail == WorldLayout.L7Pillar && t.IsWallLike) return rel >= -t.Depth ? islandRockId : concreteId;
        if (t.IsWallLike)
        {
            if (rel <= 0) return concreteId;
            return t.Kind == TileKind.Doorway && rel <= 2 ? 0 : concreteId;
        }
        if (t.Kind == TileKind.Floor)
        {
            // An island of unknown rock (from layout version 5 rising in steps, Height above the water), or a concrete
            // ledge along a wall
            int top = t.Height + 1;
            if (t.Detail == WorldLayout.L7TarUnder)
            {
                // A shelter's furniture, stuck down on a lump of tar
                if (rel == top) return tarId;
                top++;
            }
            if (rel == top && t.Floor == FloorKind.Seabed && IslandRim(t, gx, gz) is int shell and >= 0) return shell; // shells along the rim
            // (A boulder is Stack 1 on bare rock: a prop's Stack is its own, as a camp tent's part)
            if (rel >= top) return rel == top && t.Floor == FloorKind.Seabed && t.Stack == 1 && t.Variant == 0 ? islandRockId : rel == top ? AnyProp(t, rel) : 0;
            if (rel > 0) return islandRockId;
            return t.Floor == FloorKind.Concrete ? floorIds[(int)FloorKind.Concrete] : islandRockId;
        }
        // The sea: water down to the carpeted (or tarred) seabed
        int bed = -t.Depth;
        int facing7 = Facing(t.Pier);
        if (rel > 0)
        {
            // Driftwood and old buoys afloat on the surface
            if (rel == 1 && t.Variant == 0 && t.Stack is 1 or 2) return t.Stack == 1 ? propIds[Props.Driftwood, 0, facing7] : propIds[Props.Buoy, 0, 0];
            return 0;
        }
        // An old jetty: boards over the water, on posts down to the bottom
        if (t.Floor == FloorKind.Jetty)
        {
            if (rel == 0) return jettyId;
            if (t.Variant == Props.JettyPost && rel > bed) return logId;
            if (rel > bed) { fluid = waterId; return 0; }
            return rel == bed ? seabedId : concreteId;
        }
        // Kelp rising from the bottom
        if (t.Variant == Props.Kelp && rel > bed && rel <= bed + t.Stack)
        {
            fluid = waterId;
            return rel == bed + t.Stack ? kelpTopId : kelpSectionId;
        }
        if (t.Under == Unders.Cave && rel <= bed && rel > bed - 8)
        {
            fluid = waterId;
            return 0; // the cave mouth drops on down
        }
        if (rel > bed)
        {
            if (t.Variant == Props.StoneStapler && rel <= bed + 4) return islandRockId; // a standing stone
            fluid = waterId;
            // Waterweed in the shallows, dead coral in the twilight zone (WorldGenerator.Caves.cs)
            if (rel <= bed + 4 && SeabedGrowth(t, gx, gz, rel, bed) is int growth and >= 0) return growth;
            return rel == bed + 1 && t.Variant != 0 && t.Variant != Props.Kelp ? AnyProp(t, 1) : rel == bed + 1 && t.SupplyBox ? BoxOf(t) : 0;
        }
        if (rel == bed) return t.Under == Unders.TiledSeabed ? poolSunlitId : t.Floor == FloorKind.Tar ? tarId : seabedId;
        return concreteId;
    }

    /// <summary>
    /// Level 7 from layout version 9 (<see cref="WorldLayout.SeaCeiling"/>), where it differs from the sea of 1-8; -1 to
    /// leave a block to the rules of 1-8 (the water and the seabed, the islands and ledges up to head height). Over the
    /// water there is open air up to the ceiling, which lets the world's light through (seaceiling: the lore's dim light
    /// from nowhere, held the same at every hour by AtmosphereSystem, and dimming in the water with depth); the walls
    /// and the islands' pillars go on up to it. The entry rooms hang from it in their piers (<see cref="WorldLayout.AddEntryRoomV9"/>),
    /// and the sunken rooms lie on the seabed (<see cref="SunkenRoomBlock"/>).
    /// </summary>
    private int HighSeaBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int ceiling = WorldLayout.SeaCeiling, floor = WorldLayout.EntryFloor;
        byte zone = t.Zone;
        if (rel <= 0)
        {
            // Under the water: the sunken rooms and the lines down to them; the entry room's ladder dips into the sea
            if (zone >= WorldLayout.L7ZoneBellWall) return SunkenRoomBlock(t, rel, out fluid);
            if (zone == WorldLayout.L7ZoneLadder && rel >= -1)
            {
                fluid = waterId;
                return ropeLadderIds[Facing(t.Pier)];
            }
            return -1;
        }
        if (rel > ceiling) return 0;
        if (zone == WorldLayout.L7ZoneLine) return rel == 1 ? propIds[Props.Buoy, 0, 0] : rel == ceiling ? SeaCeilingBlock(gx, gz) : 0;
        if (zone == WorldLayout.L7ZoneLadder) return rel <= floor ? ropeLadderIds[Facing(t.Pier)] : rel == ceiling ? SeaCeilingBlock(gx, gz) : 0;
        if (zone != 0 && zone < WorldLayout.L7ZoneBellWall && rel < floor) return 0; // (under the pier, air down to the water)
        switch (zone)
        {
            case WorldLayout.L7ZonePier:
                return concreteId;
            case WorldLayout.L7ZoneRoom:
                if (rel == floor) return roomFloorId; // the carpet, soaked, under a puddle's worth of water
                if (rel == floor + 1)
                    return t.Stack switch
                    {
                        1 => propIds[Props.HotelBookshelf, 0, Facing(t.Pier)],
                        2 => propIds[Props.CoffeeTable, 0, 0],
                        3 => propIds[Props.HotelChair, 0, Facing(t.Pier)],
                        _ => 0,
                    };
                if (rel <= floor + 3) return 0;
                if (rel == floor + 4) return t.Ceiling == CeilingKind.LightOn ? lightOnId : concreteId;
                return concreteId;
            case WorldLayout.L7ZoneStairs:
            {
                // Step n is a stair block n over the room's floor, solid under it; three blocks of air over each tread (the
                // first stays under the room's ceiling), up through it into the dark of the shaft
                int tread = floor + t.Stair;
                if (rel < tread) return concreteId;
                if (rel == tread) return stairIds[Facing(t.Pier)];
                return rel <= (t.Stair == 1 ? floor + 3 : tread + 3) ? 0 : concreteId;
            }
            case WorldLayout.L7ZoneDoorway:
                // A doorway a block wide and two high onto the sea, its sill five blocks over the water
                return rel == floor + 1 || rel == floor + 2 ? 0 : concreteId;
        }
        // The walls between the levels and the islands' pillars go on up to the ceiling
        if (t.Detail == WorldLayout.L7Pillar && t.IsWallLike) return rel < ceiling ? islandRockId : SeaCeilingBlock(gx, gz);
        if (t.IsWallLike) return rel < floor ? -1 : concreteId;
        if (rel >= 3 && UnderLowerWall(gx, gz)) return concreteId;
        if (rel == ceiling) return SeaCeilingBlock(gx, gz);
        // (Islands and ledges keep their own up to head height; over that, and over the water, the open air)
        return rel < floor ? -1 : 0;
    }

    /// <summary>The high ceiling over the sea (layout version 9), glowing in patches as the low one did.</summary>
    private int SeaCeilingBlock(int gx, int gz) => CeilingGlows(gx, gz) ? seaCeilingGlowId : seaCeilingId;

    /// <summary>
    /// Whether a column on a Level 7 cell's east or south edge stands beside the next level's wall, where this cell does
    /// not line it (a gate's passage, or a tile the lining had to leave open): that wall is only as high as the next
    /// level's roof, so here Level 7's own goes on up from head height to the ceiling.
    /// </summary>
    private bool UnderLowerWall(int gx, int gz)
    {
        int lx = Hashing.Mod(gx, WorldLayout.MacroSize), lz = Hashing.Mod(gz, WorldLayout.MacroSize);
        const int last = WorldLayout.MacroSize - 1;
        if (lx != last && lz != last) return false;
        int mx = WorldLayout.MacroOf(gx), mz = WorldLayout.MacroOf(gz);
        return lx == last && layout.LevelAt(mx + 1, mz) != 7 || lz == last && layout.LevelAt(mx, mz + 1) != 7
            || lx == last && lz == last && layout.LevelAt(mx + 1, mz + 1) != 7;
    }

    /// <summary>
    /// A sunken room (layout version 9, <see cref="WorldLayout.AddSunkenRoom"/>), at or under the water's surface. Its
    /// base is the seabed's depth at its middle (<see cref="Tile.Height"/>), and over the base: the footing (1-2), the floor
    /// (3), the air (4-6), the roof (7), the fluorescent light in its middle still on. The tunnel's mouth and the tunnel
    /// under the floor are water in the footing; the hatch is water up to the floor, the air over it. The windows are a
    /// block of glass in the middle of each side but the tunnel's. Over the roof, the sea; the line is a rope ladder from
    /// the buoy at the surface down to the seabed beside the tunnel's mouth.
    /// </summary>
    private int SunkenRoomBlock(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        int baseRel = -t.Height;
        if (t.Zone == WorldLayout.L7ZoneLine)
        {
            if (rel <= Math.Max(baseRel, -t.Depth)) return -1; // the seabed as ever
            fluid = waterId;
            return ropeLadderIds[Facing(t.Pier)];
        }
        if (rel > baseRel + 7)
        {
            fluid = waterId;
            return 0;
        }
        // Its concrete is the sea ceiling's, not the plain concrete that deep under the floor gives way to the ground's rock
        int wall = oceanCeilingId;
        // (A footing under it where the seabed falls away; under that, and under the seabed, the ground as ever)
        if (rel <= baseRel) return rel > -t.Depth ? wall : -1;
        int up = rel - baseRel;
        int roof = t.Ceiling == CeilingKind.LightOn ? lightOnId : wall;
        switch (t.Zone)
        {
            case WorldLayout.L7ZoneBellWall:
                return wall;
            case WorldLayout.L7ZoneBellWindow:
                return up == 5 ? glassId : wall;
            case WorldLayout.L7ZoneBellMouth:
                if (up > 2) return wall;
                fluid = waterId;
                return 0;
            case WorldLayout.L7ZoneBellHatch:
                if (up <= 3)
                {
                    fluid = waterId;
                    return 0;
                }
                return up == 7 ? roof : 0;
            case WorldLayout.L7ZoneBellTunnel:
                if (up <= 2)
                {
                    fluid = waterId;
                    return 0;
                }
                return up == 3 ? roomFloorId : up == 7 ? roof : 0;
            default:
                if (up <= 2) return wall;
                if (up == 3) return roomFloorId;
                if (up == 4) return t.Variant != 0 ? AnyProp(t, 1) : t.SupplyBox ? BoxOf(t) : 0;
                return up == 7 ? roof : 0;
        }
    }

    /// <summary>
    /// Where the ceiling over the sea glows. From layout version 5, in irregular patches a few blocks across (about one
    /// block in eighteen), so the light lies in pools rather than a grid of dots that reads as a dotted horizon; before,
    /// one block in each 6 by 6.
    /// </summary>
    private bool CeilingGlows(int gx, int gz) => layout.Version >= 5
        ? Noise2(gx / 7.0, gz / 7.0, SaltCeilingGlow) > 0.6 && Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltCeilingGlow + 1)) < 0.6
        : Hashing.Mod(gx, 6) == 0 && Hashing.Mod(gz, 6) == 0;

    // ---- Level 8: real rock, carved into caves ----

    private int Level8Block(in Tile t, int gx, int gz, int y, int rel, out int fluid)
    {
        fluid = 0;
        // The 9th Road and its settlements, and the road running on through the walls into other levels
        bool open = !t.IsWallLike || t.Kind == TileKind.Doorway;
        // Four blocks of air; from layout version 5, Height: an arch over the road, a dome over a settlement
        int roof = open && t.Height > 0 ? t.Height : 4;
        if (open && rel >= 1 && rel <= roof)
        {
            if (t.Variant == 0 && !t.SupplyBox && rel <= t.Stack) return CrateOf(t); // a camp's stacked crates
            // A road lamp whose arm reaches out over the road
            if (rel == 1 && t.Variant == Props.RoadLamp && layout.Version >= 5) return roadLampArmIds[Facing(t.Pier)];
            return rel == 1 ? AnyProp(t, rel) : 0;
        }
        // Gravel would fall into a cave opening under the road; rock holds it up
        if (open && rel == 0) return IsCave(gx, y - 1, gz) ? RockAt(gx, y, gz) : gravelId;
        if (t.Variant == Props.CaveVent && rel >= 1 && rel <= 4) return rel == 1 ? ventId : RockAt(gx, y, gz);
        // Almond Water seeps out of the rock beside the road, enough to fill a bottle now and then
        // (in the rock of the stratum it seeps out of)
        if (t.Variant == Props.AlmondSeep && rel >= 1 && rel <= 4) return rel == 2 ? SeepAt(gx, y, gz) : RockAt(gx, y, gz);
        // The walls between levels are never cut by caves: they hold back the sea, and keep the levels apart
        if (t.Tall) return RockAt(gx, y, gz);

        if (IsCave(gx, y, gz))
        {
            // Flooded deep pockets, speleothems hanging from ceilings and rising from floors
            if (rel < -18 && IsPool(gx, gz) && PoolHeldIn(gx, y, gz))
            {
                fluid = waterId;
                return 0;
            }
            // Tapering speleothems, glowworms, lichen, bracket fungi and cave-ins (WorldGenerator.Caves.cs); never
            // over the road, whose air the cave noise knows nothing of
            if (!open && CaveFeature(gx, y, gz, rel) is int feature and >= 0) return feature;
            // From layout version 9, a spider nest's webs where nothing else grows (WorldGenerator.Nests.cs)
            if (!open && layout.Version >= 9 && NestWeb(gx, y, gz) is int web and >= 0) return web;
            double spikeRoll = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltSpike + (ulong)(y & 255)));
            // (nothing over the road either, where it would lie on the road's air)
            return !open && spikeRoll > 0.97 ? CaveLitter(gx, y, gz, rel, (spikeRoll - 0.97) / 0.03) : 0;
        }
        // A pool of scalding tar on some cave floors
        if (caveColumns.Get(gx, gz).Tar && IsCave(gx, y + 1, gz)) return tarId;
        return RockAt(gx, y, gz);
    }

    /// <summary>
    /// What else is in the dark: cobwebs strung under the ceilings, quartz and amethyst growing from the rock,
    /// mushrooms and loose stones on the floors, and now and then what is left of somebody.
    /// </summary>
    private int CaveLitter(int gx, int y, int gz, int rel, double roll)
    {
        bool ceilingAbove = !IsCave(gx, y + 1, gz), floorBelow = !IsCave(gx, y - 1, gz);
        if (ceilingAbove)
        {
            if (roll < 0.25) return webId;
            if (roll < 0.33 && rel < -12) return crystalDownId;
            if (roll < 0.37 && rel < -24) return BigCrystal(gx, gz, up: false);
            return 0;
        }
        if (!floorBelow) return 0;
        if (roll < 0.5) return looseStoneIds.TryGetValue(StrataName(gx, y - 1, gz), out int stones) ? stones : 0;
        if (roll < 0.62) return mushroomId;
        if (roll < 0.7 && rel < -20) return crystalUpId;
        if (roll < 0.705) return remainsId;
        // Ore weathered out of the rock and lying loose: copper, tin and coal you can pick up by hand
        if (roll < 0.78)
        {
            string ore = LooseOres[(int)((roll - 0.705) * 1000) % LooseOres.Length];
            return looseOreIds.TryGetValue((ore, StrataName(gx, y - 1, gz)), out int loose) ? loose : 0;
        }
        // Deep down, crystals grown large: amethyst, smoky, milky or rose quartz, one kind to a stretch of cave
        if (roll < 0.84 && rel < -24) return BigCrystal(gx, gz, up: true);
        return 0;
    }

    private bool IsPool(int gx, int gz) => caveColumns.Get(gx, gz).Pool;

    /// <summary>
    /// Whether water here would stay put: every open cave beside it is flooded too (and so, a step further, is
    /// every open cave beside those), and what is under it is rock or held water.
    /// </summary>
    private bool PoolHeldIn(int gx, int y, int gz) => SidesHeld(gx, y, gz, 1) && (!IsCave(gx, y - 1, gz) || SidesHeld(gx, y - 1, gz, 1));

    private bool SidesHeld(int gx, int y, int gz, int depth)
    {
        foreach ((int dx, int dz) in Neighbours4)
        {
            int x = gx + dx, z = gz + dz;
            if (!IsCave(x, y, z)) continue;
            if (!IsPool(x, z)) return false;
            if (depth > 0 && !SidesHeld(x, y, z, depth - 1)) return false;
        }
        return true;
    }

    private readonly ulong seed;

    /// <summary>Caves: big chambers where two noises agree, and long winding tubes along a third's zero.</summary>
    private bool IsCave(int gx, int y, int gz) => caveColumns.Get(gx, gz).IsCave(y);

    private string StrataName(int gx, int y, int gz)
    {
        int layer = Hashing.FloorDiv(y + caveColumns.Get(gx, gz).StrataShift, 7);
        int region = Hashing.FloorDiv(gx, 160) * 7 + Hashing.FloorDiv(gz, 160) * 3; // the order shifts from place to place
        return strata[Hashing.Mod(layer + region, strata.Length)];
    }

    /// <summary>The rock (or ore, or something that should never be found in rock) at a point of Level 8.</summary>
    /// <summary>Which of the strata a block of Level 8's rock is in.</summary>
    private int StratumAt(CaveColumn column, int gx, int y, int gz, out int layer, out int region)
    {
        layer = Hashing.FloorDiv(y + column.StrataShift, 7);
        region = Hashing.FloorDiv(gx, 160) * 7 + Hashing.FloorDiv(gz, 160) * 3;
        return Hashing.Mod(layer + region, strata.Length);
    }

    private int SeepAt(int gx, int y, int gz)
    {
        int id = seepIds[StratumAt(caveColumns.Get(gx, gz), gx, y, gz, out _, out _)];
        return id != 0 ? id : almondSeepId;
    }

    private int RockAt(int gx, int y, int gz)
    {
        CaveColumn column = caveColumns.Get(gx, gz);
        int index = StratumAt(column, gx, y, gz, out int layer, out int region);
        // Strata that should not be: a seam of office carpet, a band of yellow wallpaper
        ulong lh = Hashing.Hash(seed, layer, region, SaltStrata + 1);
        if (Hashing.Unit(lh) < 0.04 && Hashing.Mod(y + column.StrataShift, 7) == 3)
            return Hashing.Unit(lh << 20) < 0.7 ? carpetSeamId : wallpaperSeamId;
        // A coal seam that runs straight up, cutting through everything
        if (column.CoalSeam)
        {
            int coal = mineralIds[index, MineralCoal];
            if (coal != 0) return coal;
        }

        // From layout version 9, a rich deposit the road goes round: one ore, thick in the rock
        int rich = column.DepositGrade(y);
        if (rich >= 0 && DepositOre(index, column.DepositKind, rich) is int deposit and not 0) return deposit;

        // Ore bodies, or from layout version 5 veins and pockets (see CaveColumn.OreGrade)
        int grade = column.OreGrade(y);
        if (grade >= 0)
        {
            ulong h = Hashing.Hash(seed, Hashing.FloorDiv(gx, 12), Hashing.FloorDiv(gz, 12), SaltOre + (ulong)Hashing.FloorDiv(y, 8));
            double pick = Hashing.Unit(h);
            // (galena with native silver is never picked)
            int ore = pick < 0.22 ? OreNativeCopper : pick < 0.3 ? OreMalachite : pick < 0.42 ? OreCassiterite : pick < 0.54 ? OreLimonite
                : pick < 0.6 ? OreHematite : pick < 0.64 ? OreMagnetite : pick < 0.68 ? OreGold : pick < 0.72 ? OreGalena
                : pick < 0.75 ? OreSphalerite : pick < 0.77 ? OreBismuthinite : -1;
            if (ore >= 0)
            {
                // A grade the rock has no block for is the poorest grade instead
                int id = gradedOreIds[index, ore, grade];
                if (id == 0 && grade > 0) id = gradedOreIds[index, ore, 0];
                if (id != 0) return id;
            }
            int mineral = pick < 0.84 ? MineralCoal : pick < 0.88 ? MineralLignite : pick < 0.91 ? MineralSulfur : pick < 0.94 ? MineralQuartz
                : pick < 0.955 ? MineralLapis : pick < 0.97 ? MineralOlivine : pick < 0.98 ? MineralGraphite : -1;
            int m = mineral >= 0 ? mineralIds[index, mineral] : 0;
            if (m != 0) return m;
            if (pick >= 0.98 && clayId != 0) return clayId;
        }
        return strataIds[index];
    }

    /// <summary>The ores of Level 8's rich deposits (layout version 9), by the deposit's kind: copper, tin, iron, zinc, bismuth or coal.</summary>
    private static readonly int[] DepositOres = { OreNativeCopper, OreMalachite, OreCassiterite, OreLimonite, OreHematite, OreSphalerite, OreBismuthinite, -1 };

    /// <summary>A rich deposit's ore block in a stratum (a poorer grade where the rock has none so rich), or 0.</summary>
    private int DepositOre(int stratum, int kind, int grade)
    {
        int ore = DepositOres[Math.Clamp(kind, 0, DepositOres.Length - 1)];
        if (ore < 0) return mineralIds[stratum, MineralCoal];
        for (int g = grade; g >= 0; g--)
            if (gradedOreIds[stratum, ore, g] is int id and not 0) return id;
        return 0;
    }

    // ---- Level 9: the suburbs under the night sky ----

    /// <param name="roofMaterial">The shingles (0 grey, 1 brown, 2 red), where the house says; otherwise one per Suburbs lot.</param>
    private int Level9Block(in Tile t, int gx, int gz, int rel, int roofMaterial = -1)
    {
        // A drained pool, two blocks deep, tiled down its sides
        if (t.Floor == FloorKind.PoolDeep && rel is >= -2 and <= 0) return rel == -2 ? (t.Under == Unders.FullPool ? poolSunlitId : poolFloorId) : 0;
        if (t.Floor == FloorKind.PoolEdge && rel is -1 or -2) return poolFloorId;
        if (rel < 0) return concreteId;
        if (rel == 0) return t.Kind == TileKind.Water ? lakeBedId : floorIds[(int)t.Floor];
        // From layout version 5: a second storey, a porch's deck, posts and steps, the lamp by the door; and over a
        // street sign, the blade naming the street that runs north-south
        if (t.Height != 0 && t.Level == 9 && SuburbExtra(t, gx, gz, rel, roofMaterial) is int extra and >= 0) return extra;
        if (t.Variant == Props.SuburbSign && rel == 2) return suburbBladeIds[t.Detail % 8];
        bool barn = t.Pattern is WallPattern.BarnRed or WallPattern.BarnGrey;
        int barnWall = barn ? barnWallIds[t.Pattern == WallPattern.BarnRed ? 0 : 1] : 0;
        var (lotX, lotZ) = layout.LotKeyAt(gx, gz);
        int material = barn ? 3 : roofMaterial >= 0 ? roofMaterial : (int)(Hashing.Hash(seed, lotX, lotZ, 0x9D09) % 3); // one colour of shingles per house
        // From layout version 9: chimneys, tall windows, doors that open, the cased garage door
        if (t.Level == 9 && layout.Version >= 9 && SuburbV9Block(t, gx, gz, rel, material) is int v9 and >= 0) return v9;
        switch (t.Kind)
        {
            case TileKind.Wall:
            {
                bool siding = t.Pattern >= WallPattern.SidingWhite && t.Pattern <= WallPattern.Brick;
                // A brick chimney up the side of the house and out past the roof
                if (t.Variant == 3 && siding) return rel <= RoofBits.Height(t.Roof) + 1 ? chimneyId : 0;
                // Under the roof: the gable ends of the house, or of a barn, rise to meet it
                int roof = RoofAt(t, rel, material, siding ? Siding(t) : barnWall, gx, gz, siding ? 1 + (t.Pattern - WallPattern.SidingWhite) : BarnGable(t));
                if (roof >= 0) return roof;
                if (rel > 4) return 0;
                if (siding)
                {
                    if (rel == 2 && t.Variant is 1 or 2) return windowIds[t.Variant, Facing(t.Pier)];
                    // The corners of a house have siding on both outside faces
                    if (t.Stack is 1 or 2) return sidingCornerIds[t.Pattern - WallPattern.SidingWhite, Corner(t.Pier, t.Stack == 1)];
                    return sidingIds[t.Pattern - WallPattern.SidingWhite, Facing(t.Pier)];
                }
                if (interiorIds.TryGetValue(t.Pattern, out int paper))
                {
                    // Pictures, a clock or a mirror hung on the wall, facing into the room
                    int hung = t.Variant >= Decor.First ? decorIds[(int)t.Pattern, t.Variant, rel, Facing(t.Pier)] : 0;
                    return hung != 0 ? hung : paper;
                }
                if (barn) return barnWall;
                return t.Pattern == WallPattern.Rock ? strataIds[0] : concreteId;
            }
            case TileKind.Door:
            {
                int roof = RoofAt(t, rel, material, 0, gx, gz);
                if (roof >= 0) return roof;
                if (rel > 4) return 0;
                // A doll's house's door, onto Level 94
                if (t.Under == Unders.DollHouse && rel <= 2) return rel == 1 ? dollDoorLowerId : dollDoorUpperId;
                // Over the door, the house's own siding (a garage door keeps its colour in Stack)
                if (t.Pattern == WallPattern.GarageDoor)
                    return rel == 1 ? garageLowerId : rel == 2 ? garageUpperId : sidingIds[Math.Min((int)t.Stack, sidingIds.GetLength(0) - 1), Facing(t.Pier)];
                return rel == 1 ? houseDoorLowerId : rel == 2 ? houseDoorUpperId : Siding(t);
            }
            case TileKind.Doorway:
            {
                // (an outbuilding's gable closes over its doorway)
                int roof = RoofAt(t, rel, material, barnWall, gx, gz, BarnGable(t));
                if (roof >= 0) return roof;
                if (rel > 4) return 0;
                if (rel <= 2) return 0;
                if (t.Pattern == WallPattern.Rock) return rel <= 5 ? strataIds[0] : 0;
                if (barn) return barnWall;
                return interiorIds.TryGetValue(t.Pattern, out int lintel) ? lintel : Siding(t);
            }
            case TileKind.Bars:
            {
                // A fence, or a porch railing under the porch roof
                if (rel == 1) return t.Pattern == WallPattern.Fence ? fenceIds[t.Stack & 15] : 0;
                int roof = RoofAt(t, rel, material, 0, gx, gz);
                return roof > 0 ? roof : CrownOver(t, gx, gz, rel); // (a tree's crown carries on over the fence)
            }
        }
        // Inside a house: a ceiling (with a light fitting in the middle of each room), the attic and the roof over it
        if (RoofBits.IsSloped(t.Roof))
        {
            if (rel == 4 && !RoofBits.IsLowered(t.Roof))
                return t.Ceiling is CeilingKind.LightOn or CeilingKind.LightOff ? houseLightIds[t.Ceiling == CeilingKind.LightOn ? 1 : 0] : houseCeilingId;
            int roof = RoofAt(t, rel, material, 0, gx, gz);
            if (roof >= 0) return roof;
        }
        return TreeOrProp(t, gx, gz, rel, trunk: 4);
    }

    /// <summary>
    /// The pitched roof over a tile at a height: the roof block itself, air above it, and below it (down to the top
    /// of the walls) <paramref name="below"/>, which is a gable wall or the attic's air. -1 where the roof has nothing
    /// to do with this height. <paramref name="gable"/> is the siding the roof block carries down into a gable over
    /// a wall (see <see cref="PitchRoof"/>; 0 inside the roof).
    /// </summary>
    private int RoofAt(in Tile t, int rel, int material, int below, int gx, int gz, int gable = 0)
    {
        if (!RoofBits.IsSloped(t.Roof)) return -1;
        int rise = RoofBits.Rise(t.Roof), height = RoofBits.Height(t.Roof), eaves = RoofBits.IsLowered(t.Roof) ? 4 : 5;
        if (rel == height) return PitchRoof(t, material, gable, gx, gz);
        if (rel > height) return 0;
        return rel >= eaves ? below : -1;
    }

    /// <summary>A barn's or shed's gable siding for <see cref="PitchRoof"/>: 6 red boards, 7 grey, 0 for anything else.</summary>
    private static int BarnGable(in Tile t) => t.Pattern == WallPattern.BarnRed ? 6 : t.Pattern == WallPattern.BarnGrey ? 7 : 0;

    /// <summary>
    /// The roof block over a tile (graphics pass B11): which of the pitched roof's forms it takes, from the rows either
    /// side of it. Where the row up the slope falls away the other way half a block lower, this row is the ridge and
    /// rises to a point of its own; where it falls away at the same height, the two rows meet at the ridge and each
    /// carries half the cap; the lowest row overhangs its wall as an eave, unless a lower roof (a porch's) leans on
    /// the wall under it. Block choice only: the layout and the roof's height are as they always were.
    /// </summary>
    private int PitchRoof(in Tile t, int material, int gable, int gx, int gz)
    {
        int rise = RoofBits.Rise(t.Roof), down = Facing(RoofBits.Down(t.Roof)), half = rise & 1;
        bool lowered = RoofBits.IsLowered(t.Roof);
        var (dx, dz) = PipeFaces[down];
        Tile up = TileAt(gx - dx, gz - dz);
        bool facing = RoofBits.IsSloped(up.Roof) && RoofBits.IsLowered(up.Roof) == lowered && Facing(RoofBits.Down(up.Roof)) == ((down + 2) & 3);
        int form = facing && RoofBits.Rise(up.Roof) == rise - 1 ? 5 + half
            : facing && RoofBits.Rise(up.Roof) == rise ? 3 + half
            : rise == 0 && !RoofBits.IsSloped(TileAt(gx + dx, gz + dz).Roof) ? 0
            : 1 + half;
        int id = pitchRoofIds[material, gable, form, down];
        return id != 0 ? id : roofSlopeIds[material, half, down];
    }

    /// <summary>
    /// What a Suburbs house from layout version 9 has that the older ones don't (see WorldLayout.PlanExteriorV9), where
    /// the tile is not drawn as ever (-1 where it is): a brick chimney stack and its cap; a tall window's lower or upper
    /// half (rel 2-3); a front or back door that opens, closed, open or locked, its gable siding over it where the gable
    /// faces the street; a garage door cased in trim.
    /// </summary>
    private int SuburbV9Block(in Tile t, int gx, int gz, int rel, int material)
    {
        bool siding = t.Pattern >= WallPattern.SidingWhite && t.Pattern <= WallPattern.Brick;
        if (WorldLayout.IsChimney(t))
        {
            // From the ground outside a gable end, or from the roof up through the ridge; a cap on top
            int from = RoofBits.IsSloped(t.Roof) ? RoofBits.Height(t.Roof) : 1;
            if (rel >= from) return rel < t.Depth ? chimneyId : rel == t.Depth ? chimneyCapIds[ChimneyJoin(gx, gz)] : 0;
        }
        switch (t.Kind)
        {
            case TileKind.Wall when siding && t.Variant is 1 or 2 && t.Stack >= WorldLayout.WinSash && rel is 2 or 3:
                return TallWindow(t.Variant == 2, t.Stack, rel == 3, t.Pier, gx, gz, upstairs: false);
            case TileKind.Door when siding && t.Under == Unders.DollHouse:
            {
                // A doll's house's door, onto Level 94 (its gable, if it faces the street, closed over it)
                int roof = RoofAt(t, rel, material, Siding(t), gx, gz, 1 + (t.Pattern - WallPattern.SidingWhite));
                if (roof >= 0) return roof;
                return rel > 4 ? 0 : rel == 1 ? dollDoorLowerId : rel == 2 ? dollDoorUpperId : Siding(t);
            }
            case TileKind.Door or TileKind.Doorway when siding && (t.Stack & WorldLayout.DoorMark) != 0:
            {
                // (where the gable faces the street, the siding goes on up over the door)
                int roof = RoofAt(t, rel, material, Siding(t), gx, gz, 1 + (t.Pattern - WallPattern.SidingWhite));
                if (roof >= 0) return roof;
                if (rel > 4) return 0;
                if (rel > 2) return Siding(t);
                int state = (t.Stack & WorldLayout.DoorLocked) != 0 ? 2 : (t.Stack & WorldLayout.DoorOpen) != 0 ? 1 : 0;
                int f = Facing(t.Pier);
                return suburbDoorIds[state, ModelEnd(f, (t.Stack & WorldLayout.DoorHingeEast) != 0), rel - 1, f];
            }
            case TileKind.Door when t.Pattern == WallPattern.GarageDoor && t.Stack >= WorldLayout.GarageTrim:
            {
                int sd = Math.Min(t.Stack & 15, sidingIds.GetLength(0) - 1), f = Facing(t.Pier);
                int roof = RoofAt(t, rel, material, sidingIds[sd, f], gx, gz, 1 + sd);
                if (roof >= 0) return roof;
                if (rel > 4) return 0;
                if (rel > 2) return sidingIds[sd, f];
                ArchPier pier = t.Pier;
                int part = AlongWall(gx, gz, pier, n => n.Kind == TileKind.Door && n.Pattern == WallPattern.GarageDoor);
                return casedGarageIds[(rel - 1) * 3 + part, f];
            }
        }
        return -1;
    }

    /// <summary>
    /// Which end of a model (as modelled facing north: 0 its west end, 1 its east) a feature at one side of it lies at, for
    /// a block facing <paramref name="f"/> (as <see cref="Facing"/> counts) with the feature on the world's east side or
    /// its west. A model turned to face east has its west end to the north, and so on round.
    /// </summary>
    private static int ModelEnd(int f, bool east) => (east ? 1 : 3) == ((f + 3) & 3) ? 0 : 1;

    /// <summary>
    /// Where a tile lies in a row of its kind along a wall facing <paramref name="pier"/>: 0 at the row's end that is the
    /// model's west end (as modelled facing north), 2 at its east end, 1 between (or alone).
    /// </summary>
    private int AlongWall(int gx, int gz, ArchPier pier, System.Func<Tile, bool> same)
    {
        int f = Facing(pier), w = (f + 3) & 3, e = (f + 1) & 3;
        Tile tw = TileAt(gx + PipeFaces[w].Dx, gz + PipeFaces[w].Dz), te = TileAt(gx + PipeFaces[e].Dx, gz + PipeFaces[e].Dz);
        bool hasW = tw.Pier == pier && same(tw), hasE = te.Pier == pier && same(te);
        return !hasW && hasE ? 0 : hasW && !hasE ? 2 : 1;
    }

    /// <summary>A Suburbs window's shape (WorldLayout.WinSash ...) on a tile: downstairs from its Stack, upstairs from its Detail.</summary>
    private static int WindowShape(in Tile n, bool upstairs) =>
        upstairs ? n.Detail & 0x1F : n.Kind == TileKind.Wall && n.Variant is 1 or 2 ? n.Stack : 0;

    /// <summary>A tall window's block: its glass, which of its parts this is, and its side.</summary>
    private int TallWindow(bool lit, int shape, bool upper, ArchPier pier, int gx, int gz, bool upstairs)
    {
        int part = shape switch
        {
            WorldLayout.WinShutter => upper ? 3 : 2,
            WorldLayout.WinPicture => (upper ? 7 : 4) + AlongWall(gx, gz, pier, n => WindowShape(n, upstairs) == WorldLayout.WinPicture),
            _ => upper ? 1 : 0,
        };
        return suburbWindowIds[lit ? 1 : 0, part, Facing(pier)];
    }

    /// <summary>A chimney cap's join: 0 alone, else 1 + the side (as <see cref="Facing"/> counts) its stack's other half is on.</summary>
    private int ChimneyJoin(int gx, int gz)
    {
        for (int f = 0; f < 4; f++)
            if (WorldLayout.IsChimney(TileAt(gx + PipeFaces[f].Dx, gz + PipeFaces[f].Dz))) return 1 + f;
        return 0;
    }

    /// <summary>
    /// What a Suburbs house from layout version 5 has that the older ones don't (see <see cref="WorldLayout.StoreyFloor"/>,
    /// kept in the tile's Height): the porch's deck, steps and posts and the lamp by the door; a two-storey house's
    /// stairs, the floor between its storeys, its rooms upstairs, and its roof a storey up. -1 where the tile is drawn
    /// as ever.
    /// </summary>
    private int SuburbExtra(in Tile t, int gx, int gz, int rel, int roofMaterial)
    {
        byte storey = t.Height;
        if ((storey & WorldLayout.StoreyPorch) != 0)
        {
            int parts = storey & ~WorldLayout.StoreyPorch;
            if ((parts & WorldLayout.PorchLamp) != 0 && rel == 2) return porchLampIds[(parts & WorldLayout.PorchLampLit) != 0 ? 1 : 0, Facing(t.Pier)];
            // (Its foot carries the railing's rails in to it, as a fence post would)
            if ((parts & WorldLayout.PorchPost) != 0 && rel <= 3)
                return rel == 1 && t.Pattern == WallPattern.Fence && (t.Stack & 15) != 0 ? porchPostRailIds[t.Stack & 15] : porchPostId;
            if (rel == 1 && t.Variant == 0 && (parts & WorldLayout.PorchDeck) != 0) return porchDeckId;
            if (rel == 1 && t.Variant == 0 && (parts & WorldLayout.PorchStep) != 0) return porchStepId;
            return -1;
        }
        // The stairs: solid under each step, open over it up through the floor above, the top step in that floor
        // (from layout version 9, the steps under the opening have a balustrade on their open side)
        if (t.Stair > 0 && rel <= t.Stair)
        {
            if (rel < t.Stair) return interiorIds[WallPattern.InteriorBeige];
            int f = Facing(t.Pier);
            return (t.Detail & WorldLayout.StairRail) != 0 && layout.Version >= 9
                ? stairRailIds[(t.Detail & WorldLayout.StairRailFoot) != 0 ? 1 : 0, ModelEnd(f, (t.Detail & WorldLayout.StairRailEast) != 0), f]
                : houseStairIds[f];
        }
        if (rel < 4) return t.Stair > 0 ? 0 : -1;
        if (storey is WorldLayout.StoreyOuter or WorldLayout.StoreyOuterBlank)
        {
            // The outside walls go on up a storey, windows over the windows (and over the doors), and the roof on them
            if (rel == 4) return -1;
            Tile upper = t;
            upper.Height = 0;
            if (layout.Version >= 9)
            {
                // Layout version 9: the windows upstairs are their own (in Detail), tall like the ones below
                int shape = t.Detail & 0x1F;
                if (shape >= WorldLayout.WinSash && rel is 6 or 7) return TallWindow((t.Detail & WorldLayout.WinLit) != 0, shape, rel == 7, t.Pier, gx, gz, upstairs: true);
                upper.Kind = TileKind.Wall;
                upper.Variant = 0;
                upper.Under = 0;
                if (upper.Stack is not (1 or 2)) upper.Stack = 0; // (a corner keeps its second face)
                return Level9Block(upper, gx, gz, rel - 4, roofMaterial);
            }
            if (t.Kind is TileKind.Door or TileKind.Doorway)
            {
                upper.Kind = TileKind.Wall;
                upper.Variant = 1;
                upper.Under = 0;
            }
            if (storey == WorldLayout.StoreyOuterBlank && upper.Variant is 1 or 2) upper.Variant = 0;
            return Level9Block(upper, gx, gz, rel - 4, roofMaterial);
        }
        // The roof (and the attic under it), a storey up
        if (rel >= 9)
        {
            Tile lifted = t;
            lifted.Height = 0;
            lifted.Stair = 0;
            return Level9Block(lifted, gx, gz, rel - 4, roofMaterial);
        }
        // The floor between the storeys: boards on top, the ceiling of the room below (and its light) underneath
        if (rel == 4)
        {
            if (storey == WorldLayout.StoreyHole) return 0;
            bool room = t.Kind == TileKind.Floor;
            return storeyFloorIds[room && t.Ceiling == CeilingKind.LightOn ? 2 : room && t.Ceiling == CeilingKind.LightOff ? 1 : 0];
        }
        // Upstairs: the walls between the rooms, their doorways, the opening over the stairs, the rooms under their ceiling
        int paper = interiorIds[(WallPattern)((int)WallPattern.InteriorFloral + (t.Detail & 3))];
        switch (storey)
        {
            case WorldLayout.StoreyWall: return paper;
            case WorldLayout.StoreyDoorway: return rel <= 6 ? 0 : paper;
            case WorldLayout.StoreyHole: return rel == 8 ? houseCeilingId : 0;
        }
        if (rel == 8) return storey == WorldLayout.StoreyLightOn ? houseLightIds[1] : storey == WorldLayout.StoreyLightOff ? houseLightIds[0] : houseCeilingId;
        int up = t.Detail & 31;
        if (rel != 5 || up == 0 || up >= WorldLayout.UpstairsProps.Length) return 0;
        var (prop, part) = WorldLayout.UpstairsProps[up];
        return AnyProp(new Tile { Kind = TileKind.Floor, Variant = prop, Stack = part, Pier = (ArchPier)(t.Detail >> 5), Level = t.Level }, 1);
    }

    /// <summary>Which corner block a house corner takes: north- or south-facing, with its second face east or west.</summary>
    private static int Corner(ArchPier face, bool east) => (face == ArchPier.North ? 0 : 2) + (east ? 0 : 1);

    /// <summary>The siding of a house wall, door or doorway, on its outside face.</summary>
    private int Siding(in Tile t) => t.Pattern >= WallPattern.SidingWhite && t.Pattern <= WallPattern.Brick
        ? sidingIds[t.Pattern - WallPattern.SidingWhite, Facing(t.Pier)] : concreteId;

    // ---- Level 10: the fields, one block of soil over the worms ----

    private int Level10Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        // A farmhouse is one of the Suburbs' houses
        if (t.Zone == 9 && rel >= 0) return Level9Block(t, gx, gz, rel);
        if (t.Kind == TileKind.Water)
        {
            // Reeds in the shallows round the edge, lilies on the open water (WorldGenerator.Vegetation.cs)
            if (PondVegetation(t, gx, gz, rel, out fluid) is int plant and >= 0) return plant;
            if (rel > 0) return 0;
            if (rel > -t.Depth) { fluid = waterId; return 0; }
            // The pond bed: mud, with banks of clay in places; the worms keep clear of the water
            if (rel == -t.Depth && clayId != 0 && Noise2(gx / 5.0, gz / 5.0, SaltPool + 7) > 0.15) return clayId;
            return rel >= -6 ? lakeBedId : concreteId;
        }
        if (rel < 0) return rel < -6 ? concreteId : t.Under == Unders.LakeRim ? lakeBedId : wormId;
        if (rel == 0) return floorIds[(int)t.Floor];
        bool barn = t.Pattern is WallPattern.BarnRed or WallPattern.BarnGrey;
        int barnWall = barn ? barnWallIds[t.Pattern == WallPattern.BarnRed ? 0 : 1] : 0;
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (t.Pattern == WallPattern.Hedge) return rel <= 2 ? leavesId : CrownOver(t, gx, gz, rel);
                if (t.Pattern == WallPattern.Silo) return rel <= 8 ? siloId : rel == 9 ? siloTopId : 0;
                if (barn)
                {
                    int roof = RoofAt(t, rel, 3, barnWall, gx, gz, BarnGable(t));
                    // A stretch of boards that isn't quite there: walk into it and you are somewhere else
                    if (t.Under == Unders.Noclip && rel <= 2) return noclipBarnId;
                    return roof >= 0 ? roof : rel <= 4 ? barnWall : 0;
                }
                return rel <= 5 ? strataIds[0] : 0; // the cliffs where the fields meet the enclosed levels
            case TileKind.Doorway:
                if (barn)
                {
                    // (the gable closes over the doorway)
                    int roof = RoofAt(t, rel, 3, barnWall, gx, gz, BarnGable(t));
                    return roof >= 0 ? roof : rel <= 3 ? 0 : rel <= 4 ? barnWall : 0;
                }
                return rel <= 2 ? 0 : rel <= 5 ? strataIds[0] : 0;
            case TileKind.Bars:
                if (rel == 1) return t.Pattern == WallPattern.Fence ? fenceIds[t.Stack & 15] : 0;
                break;
        }
        // Barns and sheds are open inside, up to the roof
        if (RoofBits.IsSloped(t.Roof))
        {
            int roof = RoofAt(t, rel, 3, 0, gx, gz);
            if (roof >= 0) return roof;
        }
        if (t.Kind == TileKind.Bars) return CrownOver(t, gx, gz, rel);
        return TreeOrProp(t, gx, gz, rel, trunk: 4);
    }

    /// <summary>A tree's trunk and crown, the crown of a neighbouring tree, or whatever stands on the tile.</summary>
    private int TreeOrProp(in Tile t, int gx, int gz, int rel, int trunk)
    {
        // Under the open sky: vanilla trees, grass, ferns and flowers (WorldGenerator.Vegetation.cs)
        if (rel >= 1 && rel <= 24 && IsVegetationLevel(t.Level) && Vegetation(t, gx, gz, rel) is int plant and >= 0) return plant;
        if (t.Variant == Props.Tree) return rel <= trunk ? logId : rel <= trunk + 2 ? leavesId : 0;
        if (t.Overhead == Overheads.Leaves && rel >= trunk && rel <= trunk + 2) return leavesId;
        if (t.Variant == Props.HayBale) return rel <= Math.Max((int)t.Stack, 1) ? hayId : 0;
        if (rel != 1) return 0;
        return t.Variant switch
        {
            Props.Crop => t.Stack switch { 1 => cropRyeId, 2 => cropFlaxId, _ => cropSpeltId },
            Props.TallGrass => tallGrassId,
            Props.Reeds => cattailId,
            Props.BerryBush => berryBushIds[t.Stack % berryBushIds.Length],
            Props.Skep => skepId,
            Props.Quern => quernId,
            Props.Shrub => leavesId,
            Props.Flowers => flowerIds[t.Stack % flowerIds.Length],
            Props.Vegetable => vegetableIds[t.Stack % vegetableIds.Length],
            _ => AnyProp(t, rel),
        };
    }

    // ---- Props on any level ----

    /// <summary>The block for whatever prop stands on a tile, on any level.</summary>
    private int AnyProp(in Tile t, int rel)
    {
        int facing = Facing(t.Pier);
        switch (t.Variant)
        {
            case 0: return t.SupplyBox ? BoxOf(t) : 0;
            case Props.Drum: return drumId;
            case Props.Shelf: return shelfIds[Facing(Opposite(t.Pier))];
            case Props.Car: return carIds[t.Stack % 4, CarFacing(t.Pier)];
            case Props.CarPart: return carColliderId;
            case Props.WheelStop: return wheelStopId;
            case Props.Transformer: return transformerId;
            case Props.Desk: return deskIds[facing];
            case Props.OfficeChair: return chairIds[facing];
            case Props.FilingCabinet: return filingIds[facing];
            case Props.Vending: return vendingIds[facing];
            case Props.Cooler: return coolerIds[facing];
            case Props.ConferenceTable: return confTableId;
            case Props.Bed: return t.Stack == 0 ? bedHeadIds[Facing(Opposite(t.Pier))] : bedFootIds[Facing(Opposite(t.Pier))];
            case Props.Nightstand: return nightstandIds[facing];
            case Props.Wardrobe: return wardrobeIds[facing];
            case Props.WingChair: return wingChairIds[facing];
            case Props.Sofa: return sofaIds[facing];
            case Props.Palm: return palmId;
            case Props.MahjongTable: return mahjongId;
            case Props.Turntable: return turntableId;
            case Props.Boiler: return boilerIds[facing];
            case Props.Furnace: return furnaceIds[facing];
            case Props.Tree or Props.HayBale or Props.Crop or Props.TallGrass or Props.Reeds or Props.Shrub or Props.Flowers or Props.Vegetable
                or Props.BerryBush or Props.Skep or Props.Quern
                or Props.Kelp or Props.JettyPost: return 0;
            case Props.CaveVent or Props.AlmondSeep: return 0;
        }
        return PropBlock(t);
    }

    // ---- Noise ----

    private double Noise2(double x, double z, ulong salt)
    {
        int x0 = (int)Math.Floor(x), z0 = (int)Math.Floor(z);
        double fx = x - x0, fz = z - z0;
        double sx = fx * fx * (3 - 2 * fx), sz = fz * fz * (3 - 2 * fz);
        double c00 = Corner2(x0, z0, salt), c10 = Corner2(x0 + 1, z0, salt), c01 = Corner2(x0, z0 + 1, salt), c11 = Corner2(x0 + 1, z0 + 1, salt);
        double top = c00 + (c10 - c00) * sx, bottom = c01 + (c11 - c01) * sx;
        return top + (bottom - top) * sz;
    }

    private double Corner2(int x, int z, ulong salt) => Hashing.Unit(Hashing.Hash(seed, x, z, salt)) * 2 - 1;

    // ---- Block lookup ----

    /// <summary>The first of several candidate vanilla blocks that exists (logging only if none do).</summary>
    private int GameId(params string[] codes)
    {
        foreach (string code in codes)
        {
            int id = OptionalId(code);
            if (id != 0) return id;
        }
        api.Logger.Error("[backrooms] None of {0} exist, the Backrooms will have holes", string.Join(", ", codes));
        return 0;
    }

    private int OptionalId(string code)
    {
        Block block = api.World.GetBlock(new AssetLocation(code));
        return block == null ? 0 : block.BlockId;
    }
}
