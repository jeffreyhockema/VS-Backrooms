namespace Backrooms.Worldgen;

/// <summary>What occupies a block column of Level 0, between the floor and the ceiling.</summary>
public enum TileKind : byte
{
    Floor,
    /// <summary>Full-height wall: partitions, pillars, room boundaries.</summary>
    Wall,
    /// <summary>Gap through a wall with a lintel above (Manila Room doors).</summary>
    Doorway,
    /// <summary>Half-height wall with an arched opening above it, like the arches photo.</summary>
    ArchWindow,
    /// <summary>Walk-through opening under an arch.</summary>
    ArchDoor,
    /// <summary>Square shaft in the floor that drops far below. Nobody survives the fall.</summary>
    Pit,
    /// <summary>Floor recessed by one block and flooded.</summary>
    Water,
    /// <summary>A closed, locked door filling a wall line (style from <see cref="Tile.Pattern"/>).</summary>
    Door,
    /// <summary>Indestructible iron bars: blocks the way but not the view.</summary>
    Bars,
}

public enum WallPattern : byte
{
    Chevron,
    Dotted,
    Cream,
    Manila,
    /// <summary>Level 1 bare concrete wall (variant 1 = damaged, rusty rebar showing).</summary>
    Concrete,
    /// <summary>Level 1 parking pillar (variant = painted bay letter, +8 = has a wall light).</summary>
    Pillar,
    /// <summary>Level 2 tunnel wall (variant 0 plain, 1 pipes, 2 machinery, 3 brick).</summary>
    Tunnel,
    /// <summary>Level 3 two-tone glazed structural tile.</summary>
    GlazedTile,
    /// <summary>Level 3 red brick of inconsistent colour.</summary>
    RedBrick,
    /// <summary>Level 3 cinder block, in machine rooms.</summary>
    Cinder,
    /// <summary>Level 4 off-white drywall.</summary>
    Drywall,
    /// <summary>Level 4 window onto a rainy, foggy nowhere.</summary>
    OfficeWindow,
    /// <summary>Level 4 glass partition.</summary>
    OfficeGlass,
    /// <summary>Level 5 hotel wall: mahogany wainscot, red panel in a gilt frame, cream frieze.</summary>
    Hotel,
    /// <summary>Level 5 stained plaster of the boiler halls.</summary>
    Plaster,
    /// <summary>Level 5 red faux-marble column.</summary>
    Marble,
    /// <summary>Door styles: Level 4 elevator doors, Level 5 staff-only doors.</summary>
    Elevator,
    Staff,
    /// <summary>Level 1 white-painted block walls of the maintenance halls and stair cores.</summary>
    WhiteBlock,
    /// <summary>Level 3 pale ashlar masonry of a Sanctum.</summary>
    Stone,
    /// <summary>Level 6: the smooth, cold material of the hallways of total darkness.</summary>
    L6Wall,
    /// <summary>Level 6.1, the Snackrooms: pastel mall walls, wood-panelled restaurants, white-tiled kitchens, glowing windows.</summary>
    SnackMall,
    SnackPanel,
    SnackTile,
    SnackWindow,
    /// <summary>Raw rock: Level 8's caves, and the cliffs where the open levels meet the rest.</summary>
    Rock,
    /// <summary>Level 9 house exteriors: painted siding in four colours and brick (Variant on a window wall: 1 = lit).</summary>
    SidingWhite,
    SidingBlue,
    SidingYellow,
    SidingGreen,
    Brick,
    /// <summary>Level 9 house interiors.</summary>
    InteriorFloral,
    InteriorStripe,
    InteriorBeige,
    InteriorGreen,
    InteriorTile,
    /// <summary>Level 9 and 10 outbuildings: red barn boards and weathered grey boards.</summary>
    BarnRed,
    BarnGrey,
    /// <summary>Level 10 hedgerows.</summary>
    Hedge,
    /// <summary>Wooden fences (on <see cref="TileKind.Bars"/> tiles; Stack holds the connections N1 E2 S4 W8).</summary>
    Fence,
    /// <summary>Level 9: a closed garage roller door (on <see cref="TileKind.Door"/> tiles).</summary>
    GarageDoor,
    /// <summary>Level 10: a round grain silo of corrugated steel, capped with a dome.</summary>
    Silo,
    /// <summary>
    /// Level 11 façades, by style: blue curtain glass, black mirror glass (the sealed buildings that can never be
    /// entered), red and dark brick, pale limestone, and grey concrete.
    /// </summary>
    CityGlass,
    CityMirror,
    CityBrick,
    CityBrickDark,
    CityStone,
    CityConcrete,
    /// <summary>Level 11: plain painted plaster inside lobbies, apartment halls and galleries.</summary>
    CityPlaster,
    /// <summary>Level 11: white tiles down in the subway.</summary>
    SubwayTile,
    /// <summary>Level 11: the low stone rim of a fountain basin.</summary>
    FountainRim,
    /// <summary>Level 11: black iron railings (on <see cref="TileKind.Bars"/> tiles).</summary>
    CityRail,
    /// <summary>Level 11: the painted fascia over a storefront, where the store's sign hangs.</summary>
    CityStorefront,
    /// <summary>Level 0's Red Rooms: the same paper, in red.</summary>
    RedRoom,
    /// <summary>
    /// Level 37: white ceramic tile, every surface (Variant on a wall: see <see cref="PoolWalls"/>). In the
    /// Sanguine Reservoir (<see cref="Tile.Zone"/> 1) a red film lies in the grout.
    /// </summary>
    PoolTile,
    /// <summary>Level 37: a cyan door marked POOL (on <see cref="TileKind.Door"/> tiles); in Level 5, the one in the hotel.</summary>
    PoolDoor,
    /// <summary>Level 37: the black of a round tunnel mouth, the way out into the sea.</summary>
    PoolVoid,
    /// <summary>Level 94: the painted backdrop at the edge of the set, more hills under more sky.</summary>
    Backdrop,
    /// <summary>Level 94: the glass of the transparent mountain.</summary>
    GlassMountain,
    /// <summary>Level 94: the castle's white walls outside, and its funhouse walls inside (striped, with porthole rings).</summary>
    CastleWall,
    Funhouse,
    /// <summary>Level 94's castle: one of the throne room's doors (on <see cref="TileKind.Door"/> tiles). Only one opens, and a different one each day.</summary>
    ThroneDoor,

    // ===== The far places (ids 14-20): one block of values each (see docs/design/new-levels/CONTRACT.md) =====
    // A level adds its members inside its own block only, with explicit values, never past the block's end; 62-63 stay free.

    /// <summary>
    /// Level ! (block 64-79): its pale hospital wall; the same with the wooden crash rail on the face toward
    /// <see cref="Tile.Pier"/>; and on <see cref="TileKind.Door"/> tiles (or a Doorway, the hall door) its doors.
    /// <see cref="Tile.Pier"/> on a door is the face that looks into the hall or room.
    /// </summary>
    RunWall = 64,
    RunWallRail = 65,
    RunSideDoor = 67,
    RunDentedDoor = 68,
    RunSwingDoor = 69,
    RunFakeExit = 70,
    RunTrueExit = 71,
    RunChainedDoor = 72,
    RunHallDoor = 73,
    RunMarkedDoor = 74,
    /// <summary>Level !: a wall with the start room's medicine cabinet on it (face toward Pier).</summary>
    RunMedCabinet = 75,
    RunSafeWall = 76,
    RunSafeDoor = 77,
    /// <summary>Level !: matte black, behind the chained door and the false exits.</summary>
    RunVoid = 78,
    /// <summary>The way into Level ! from other levels: a red EXIT door where no door should be (on Door tiles).</summary>
    RunEntryDoor = 79,
    /// <summary>
    /// Level Fun (block 80-95): the ship's hull (its rim; <see cref="Tile.Variant"/> 1 a porthole), a party room's
    /// paint (<see cref="Tile.Detail"/> the colour), the promenades' cream with its band, the mural room's yellow
    /// (Variant 1 + 2·mural + half), grey crew steel (Variant 1 a CREW ONLY plate), a bounce house's puffy vinyl,
    /// the night beyond an open deck, brass elevator doors (Variant 0 left, 1 right), plain concrete; and on
    /// <see cref="TileKind.Door"/> tiles the FUN doors (Variant 0 left leaf, 1 right) and a waiting room's exit door.
    /// <see cref="Tile.Pier"/> is the face that looks into the room or hall.
    /// </summary>
    FunWall = 80,
    FunPaint = 81,
    FunPromenade = 82,
    FunMural = 83,
    FunSteel = 84,
    FunInflatable = 85,
    FunVoid = 86,
    FunElevator = 87,
    FunSolid = 88,
    FunDoor = 89,
    FunExitDoor = 90,
    /// <summary>
    /// The End (block 96-111): its painted walls (off-white under a yellow band), and its rim; the columns, sage or
    /// slate over slatwall; the stockrooms' painted block; the EXIT door, the staff door and the bookstore's door
    /// (on <see cref="TileKind.Door"/> tiles, facing <see cref="Tile.Pier"/>).
    /// </summary>
    EndWall = 96,
    EndColumn = 97,
    EndColumnSlate = 98,
    EndStockWall = 99,
    EndExit = 100,
    EndStaff = 101,
    EndStoreDoor = 102,
    /// <summary>The Hub (block 112-143: its many doors).</summary>
    HubWall = 112,
    /// <summary>The Hub: a great carved concrete door (on <see cref="TileKind.Door"/> tiles; Detail = its sigil, Stack = which of its three columns, Pier = the way it faces).</summary>
    HubDoor = 113,
    /// <summary>The Hub: a plain grey steel service door, the way back to wherever someone came in from.</summary>
    HubServiceDoor = 114,
    /// <summary>The Hub: an ornate door into the Tower (Stack = which of its two leaves).</summary>
    HubOrnate = 115,
    /// <summary>The Hub: the Tower's pale ashlar.</summary>
    HubAshlar = 116,
    /// <summary>Level 974 (block 144-159): the solid nothing between the houses (and the region's rim).</summary>
    L974Wall = 144,
    /// <summary>Level 974: a house's Baker-Miller pink walls; behind the kitchen counters, white subway tile; round a bathroom, pastel tile.</summary>
    L974Paint = 145,
    L974Backsplash = 146,
    L974BathTile = 147,
    /// <summary>Level 974: a window that is a painting (Stack 0 left, 1 right as seen from the room; Pier the way it faces; Detail the painting).</summary>
    L974Window = 148,

    // ===== Levels 3999 and 188 (19, 20): one block of values each, as for 14-18 =====

    /// <summary>
    /// Level 3999 (block 160-175): matt painted plaster (the paint by the colour in <see cref="Tile.Detail"/>), the rim
    /// and the units' side walls; the service corridors' concrete; a glass shopfront onto a concourse (glass to rel 5,
    /// the fascia over it); a roller shutter over a closed unit's front; on <see cref="TileKind.Door"/> tiles a revolving
    /// door (Stack 0 left, 1 centre, 2 right, seen from the front), a STAFF ONLY door, the mini arcade's elevator; a
    /// painted window onto the car park (Variant the column 0-3); the natatorium's pool-tile walls.
    /// </summary>
    L3999Wall = 160,
    L3999Concrete = 161,
    L3999Shopfront = 162,
    L3999Shutter = 163,
    L3999Revolving = 164,
    L3999Staff = 165,
    L3999Elevator = 166,
    L3999Window = 167,
    L3999PoolWall = 168,
    /// <summary>Level 188 (block 176-191).</summary>
    L188Wall = 176,
    /// <summary>
    /// Level 188: the courtyard façade (its windows in it), the solid nothing round the building, partitions between
    /// rooms, corridor walls, the outer façade, the stair hall's blockwork, the lobby's front doors, and a guest door that
    /// is sealed or locked on the ground storey.
    /// </summary>
    L188Facade = 177, L188Nothing = 178, L188Partition = 179, L188CorridorWall = 180, L188OuterWall = 181, L188StairWall = 182,
    L188FrontDoor = 183, L188SealedDoor = 184, L188LockedDoor = 185,

    /// <summary>
    /// Level 0 (layout version 10 on): the arched areas' plain cream plaster, on every wall, pier and header of them
    /// (the pale paper, <see cref="Cream"/>, in layout versions 1-9). Appended last: no value before it moves.
    /// </summary>
    Stucco = 192,
}

/// <summary>Trim on the bottom block of a wall.</summary>
public enum BaseStyle : byte { Plain, Baseboard, Rail }

public enum FloorKind : byte
{
    Carpet,
    Stained,
    Soaked,
    Wood,
    Concrete,
    ConcreteWet,
    /// <summary>Level 1 painted parking bay line running north-south.</summary>
    ConcreteLineNS,
    /// <summary>Level 1 painted parking bay line running west-east.</summary>
    ConcreteLineWE,
    /// <summary>Level 1 dashed yellow aisle centre line running west-east.</summary>
    ConcreteDashWE,
    /// <summary>Level 1 dashed yellow aisle centre line running north-south.</summary>
    ConcreteDashNS,
    /// <summary>Level 3 dusty concrete.</summary>
    Dusty,
    /// <summary>Level 4 low-pile grey office carpet.</summary>
    OfficeCarpet,
    /// <summary>Level 4 carpet with a darker rectangle where furniture once stood.</summary>
    OfficeCarpetGhost,
    /// <summary>Level 5 red and gold damask hotel carpet.</summary>
    HotelCarpet,
    /// <summary>Level 5 near-black maroon ballroom carpet.</summary>
    HotelMaroon,
    /// <summary>Level 5 tan and gold lobby carpet.</summary>
    HotelLobby,
    /// <summary>Level 5 dark walnut floorboards.</summary>
    HotelWood,
    /// <summary>Level 1 painted concrete of the maintenance halls.</summary>
    L1Hall,
    /// <summary>Level 1 lane arrows painted on the aisle, pointing north, east, south or west.</summary>
    ParkArrowN,
    ParkArrowE,
    ParkArrowS,
    ParkArrowW,
    ParkOil,
    ParkDrain,
    /// <summary>Level 3 steel grating.</summary>
    Grate,
    /// <summary>Level 3 concrete with hazard stripes, around machinery.</summary>
    L3Hazard,
    /// <summary>Level 3 Sanctum flagstones and its red carpet aisle.</summary>
    L3Stone,
    SanctumCarpet,
    /// <summary>Level 4 carpet with papers scattered on it, and with a coffee stain.</summary>
    OfficePapers,
    OfficeStain,
    /// <summary>Level 5 white marble, carpet runners over walnut, and rugs.</summary>
    HotelMarble,
    HotelRunnerNS,
    HotelRunnerWE,
    HotelRug,
    /// <summary>Level 6 smooth dark floor.</summary>
    L6Floor,
    /// <summary>Level 6.1 terrazzo halls, chequered restaurants, red quarry tiles in the kitchens.</summary>
    SnackTerrazzo,
    SnackChecker,
    SnackQuarry,
    /// <summary>Level 8 gravel underfoot on the 9th Road.</summary>
    Gravel,
    /// <summary>Level 9 streets, pavements, lawns and house floors.</summary>
    Asphalt,
    AsphaltLeaves,
    AsphaltWet,
    Sidewalk,
    Lawn,
    HouseWood,
    HouseCarpet,
    HouseTile,
    HouseLino,
    Garage,
    /// <summary>Level 10 tilled field soil (crops stand on it), grass, and dirt roads.</summary>
    Field,
    Grass,
    DirtRoad,
    DirtTracks,
    /// <summary>Level 7 seabed: soaked carpet, or tar in the abyss.</summary>
    Seabed,
    Tar,
    /// <summary>Level 10: a harvested field of stubble, its hay rolled up.</summary>
    Stubble,
    /// <summary>Level 9: a porch of painted boards, concrete driveways, and the painted lines and covers of the streets.</summary>
    Porch,
    Driveway,
    AsphaltLine,
    AsphaltCrossing,
    AsphaltLineNS,
    AsphaltCrossingNS,
    Manhole,
    /// <summary>Level 9: a drained backyard pool (two blocks deep) and the stone coping round it.</summary>
    PoolDeep,
    PoolEdge,
    /// <summary>Level 9: a flower bed or vegetable patch of dug soil.</summary>
    Flowerbed,
    /// <summary>Level 9 rugs on a house's floorboards.</summary>
    HouseRug,
    /// <summary>Level 6: a slick of standing water on the cold floor.</summary>
    L6Wet,
    /// <summary>Level 7: the boards of an old jetty, over the water.</summary>
    Jetty,
    /// <summary>Level 11: polished stone in the lobbies, granite pavers on the plazas, painted concrete in the garages.</summary>
    CityMarble,
    CityPlaza,
    CityGarage,
    /// <summary>Level 11: the double yellow line down the middle of a road running north-south (NS) or west-east.</summary>
    AsphaltDoubleNS,
    AsphaltDoubleWE,
    /// <summary>Level 11: the white line of a curb parking lane, and cracked, patched asphalt.</summary>
    AsphaltBayNS,
    AsphaltBayWE,
    AsphaltCracked,
    /// <summary>Level 11: gravel paths through the parks.</summary>
    ParkPath,
    /// <summary>Level 11's subway: ballast between the rails, the two rails of a track (left and right), the platform and its yellow edge.</summary>
    SubwayBed,
    SubwayRailL,
    SubwayRailR,
    SubwayPlatform,
    SubwayEdge,
    /// <summary>Level 37: white tile underfoot; tile lit warm where light falls through a slit; red-filmed tile in the Reservoir.</summary>
    PoolTile,
    PoolSunlit,
    PoolRed,
    /// <summary>Level 37: the rounded coping tile along the edge of a deck, where it drops into deep water.</summary>
    PoolCoping,
    /// <summary>Level 94: clay turf mown in stripes (light and dark), clay soil, a dirt path, a concrete path, asphalt and its kerb.</summary>
    TurfLight,
    TurfDark,
    ClaySoil,
    MotionPath,
    MotionConcrete,
    MotionAsphalt,
    MotionKerb,
    /// <summary>Level 94's castle: a blue-and-yellow checkerboard, the red-and-white striped carpet, a star medallion.</summary>
    Checker,
    FunCarpet,
    StarFloor,

    // ===== The far places (ids 14-20): one block of values each (see docs/design/new-levels/CONTRACT.md) =====
    // A level adds its members inside its own block only, with explicit values, never past the block's end; 97-99 stay free.

    /// <summary>
    /// Level ! (block 100-115): speckled hospital vinyl; with the charcoal-blue band along the wall toward Pier; scuffed
    /// and clawed; cracked (a hole ahead); the Safe Zone's blue-grey.
    /// </summary>
    RunFloor = 100,
    RunBorder = 101,
    RunScuffed = 102,
    RunCracked = 103,
    RunSafeFloor = 104,
    /// <summary>
    /// Level Fun (block 116-131): vinyl tiles in party colours (four arrangements), the red race-track carpet, faded
    /// retro carpet, foam play mats, teak decking, parquet, the lobbies' red carpet, a bounce house's quilted floor.
    /// </summary>
    FunFloor = 116,
    FunVinylB = 117,
    FunVinylC = 118,
    FunVinylD = 119,
    FunRaceCarpet = 120,
    FunRetroCarpet = 121,
    FunCheckerA = 122,
    FunCheckerB = 123,
    FunDeck = 124,
    FunParquet = 125,
    FunLobbyCarpet = 126,
    FunInflatableFloor = 127,
    /// <summary>
    /// The End (block 132-147): grey-green library carpet (dusty, worn, stained, under snow), the navy patterned
    /// runway, the stockrooms' concrete and its safety line.
    /// </summary>
    /// <summary>The first of the End's range (the same value as <see cref="EndCarpet"/>, which is the one used).</summary>
    EndFloor = 132,
    EndCarpet = 132,
    EndCarpetDusty = 133,
    EndCarpetWorn = 134,
    EndCarpetStained = 135,
    EndCarpetSnow = 136,
    EndRunway = 137,
    EndConcrete = 138,
    EndConcreteLine = 139,
    /// <summary>The Hub (block 148-163). Placeholder.</summary>
    HubFloor = 148,
    /// <summary>The Hub: the asphalt road; with a yellow road stud; worn; patched.</summary>
    HubAsphalt = 149,
    HubStud = 150,
    HubAsphaltWorn = 151,
    HubAsphaltPatch = 152,
    /// <summary>The Hub: the raised sidewalk along each wall (a half slab), where people are put down.</summary>
    HubSidewalk = 153,
    /// <summary>The Hub: the Tower's polished marble, plain and inlaid.</summary>
    HubMarble = 154,
    HubMarbleInlay = 155,
    /// <summary>Level 974 (block 164-179): blush carpet, the kitchen's pink-and-white checker, the bathrooms' white hexagons.</summary>
    L974Floor = 164,
    L974Checker = 165,
    L974BathHex = 166,

    // ===== Levels 3999 and 188 (19, 20): one block of values each, as for 14-18 =====

    /// <summary>
    /// Level 3999 (block 180-195): black-light carpet (cosmic, galaxy, and rotten in the Neon Blackout), white and black
    /// marble, the service corridors' polished concrete, bowling-lane maple, violet and lilac pool mosaic, the pools'
    /// white edge, and (in Level 10) the arcade's car-park asphalt and its bay lines.
    /// </summary>
    L3999Floor = 180,
    L3999Galaxy = 181,
    L3999Rotten = 182,
    L3999Marble = 183,
    L3999MarbleBlack = 184,
    L3999Concrete = 185,
    L3999Lanewood = 186,
    L3999PoolViolet = 187,
    L3999PoolLilac = 188,
    L3999PoolEdge = 189,
    L3999Asphalt = 190,
    L3999AsphaltLine = 191,
    /// <summary>Level 188 (block 196-211). Placeholder.</summary>
    L188Floor = 196,
    /// <summary>Level 188: courtyard pavers, the mossy lawns, the wooden deck; corridor carpet, guest-room carpet, the lobby, the stair hall.</summary>
    L188Paver = 197, L188Turf = 198, L188Deck = 199, L188Corridor = 200, L188Room = 201, L188Lobby = 202, L188Stair = 203,
}

public enum CeilingKind : byte
{
    Tile,
    /// <summary>Working light that also emits block light.</summary>
    LightOn,
    /// <summary>Working light that only glows. Emitting from every panel would make worldgen lighting far too slow.</summary>
    LightLit,
    LightOff,
    LampDim,
    /// <summary>Failing light that blinks. Glows only (no block light), animated on the client.</summary>
    LightFlicker,
    /// <summary>Level 2 caged bulb with an orange tint.</summary>
    LightWarm,
    /// <summary>Level 5 crystal chandelier in a grand room.</summary>
    Chandelier,
    /// <summary>A dim red lamp: all the light there is in Level 0's Red Rooms.</summary>
    LampRed,

    // ===== The far places (ids 14-20): one block of values each (see docs/design/new-levels/CONTRACT.md) =====
    // A level adds its members inside its own block only, with explicit values, never past the block's end; 9-15 stay free.

    /// <summary>
    /// Level ! (block 16-23): acoustic tile; a dead troffer; a hanging EXIT sign (its faces look along the hall: north
    /// and south unless the tile's Detail has <c>WorldLayout.RunSignWE</c>); an air vent; the Safe Zone's blue panel.
    /// </summary>
    RunCeiling = 16,
    RunPanelDead = 17,
    RunExitSign = 18,
    RunVent = 20,
    RunSafeLight = 21,
    /// <summary>
    /// Level Fun (block 24-31): the black night over an open deck (FunCeiling), and a bounce house's puffy roof
    /// under the hall's own ceiling (see the level's file for the heights).
    /// </summary>
    FunCeiling = 24,
    FunInflatableRoof = 25,
    /// <summary>The End (block 32-39). Placeholder.</summary>
    EndCeiling = 32,
    /// <summary>The Hub (block 40-47). Placeholder.</summary>
    HubCeiling = 40,
    /// <summary>Level 974 (block 48-55). Placeholder.</summary>
    L974Ceiling = 48,

    // ===== Levels 3999 and 188 (19, 20): one block of values each, as for 14-18 =====

    /// <summary>
    /// Level 3999 (block 56-63): the open black ceiling of the public areas; the service corridors' acoustic tile, with
    /// a white fluorescent tube in it, or a dead one (in the Neon Blackout).
    /// </summary>
    L3999Ceiling = 56,
    L3999Acoustic = 57,
    L3999Fluoro = 58,
    L3999FluoroOff = 59,
    /// <summary>Level 188 (block 64-71). Placeholder.</summary>
    L188Ceiling = 64,
}

/// <summary>
/// A chalk mark beside a floor tile, packed in <see cref="Tile.Chalk"/>: which neighbour is the wall it is drawn on, and
/// the symbol (as the chalk item draws them: left, right, cross, circle). Left and right are as seen facing the wall.
/// </summary>
public static class ChalkBits
{
    public static readonly string[] Symbols = { "left", "right", "cross", "circle" };

    public static byte Make(ArchPier wall, int symbol) => (byte)(((symbol + 1) << 2) | ((int)wall & 3));
    public static ArchPier Wall(byte chalk) => (ArchPier)(chalk & 3);
    public static int Symbol(byte chalk) => (chalk >> 2) - 1;
}

/// <summary>Which side of an arch header block is attached to its pier (the thick, low end of the curve).</summary>
public enum ArchPier : byte { West, East, North, South }

/// <summary>
/// The pitched roof over a tile, packed in <see cref="Tile.Roof"/>. Roofs rise half a block for every block in from
/// the eaves; Rise counts those half-blocks, and Down is the way the roof slopes down (toward its eaves). Roofs sit
/// on walls four blocks high, or (Lowered) one block lower, for a porch roof leaning against the house.
/// </summary>
public static class RoofBits
{
    public const byte Sloped = 0x80, Lowered = 0x40;

    public static byte Make(int rise, ArchPier down, bool lowered = false) =>
        (byte)(Sloped | (lowered ? Lowered : 0) | (((int)down & 3) << 4) | (rise & 15));

    public static bool IsSloped(byte roof) => (roof & Sloped) != 0;
    public static bool IsLowered(byte roof) => (roof & Lowered) != 0;
    public static int Rise(byte roof) => roof & 15;
    public static ArchPier Down(byte roof) => (ArchPier)((roof >> 4) & 3);

    /// <summary>Height above the floor of the roof block over a tile.</summary>
    public static int Height(byte roof) => (IsLowered(roof) ? 4 : 5) + Rise(roof) / 2;

    /// <summary>The same roof with its slope turned (when a plan is mirrored).</summary>
    public static byte Turned(byte roof, System.Func<ArchPier, ArchPier> turn) =>
        IsSloped(roof) ? (byte)((roof & ~0x30) | (((int)turn(Down(roof)) & 3) << 4)) : roof;
}

public struct Tile
{
    public TileKind Kind;
    public WallPattern Pattern;
    public BaseStyle Base;
    public FloorKind Floor;
    public CeilingKind Ceiling;
    public ArchPier Pier;
    public bool Outlet;
    public bool SupplyBox;
    /// <summary>The supply box or crate here was picked over long ago: torn or prised open, the food gone.</summary>
    public bool Looted;
    /// <summary>Which level this column belongs to.</summary>
    public byte Level;
    /// <summary>Wall between two levels: solid up to the top of the taller level.</summary>
    public bool Tall;
    /// <summary>
    /// Level 1 (and elsewhere where <see cref="Variant"/> is 0): height of a stack of crates (0 = none). With a prop, which
    /// of its kinds or parts it is (a car's colour, a bed's head or foot, a door's leaf); its meaning is the prop's.
    /// </summary>
    public byte Stack;
    /// <summary>Overhead pipework, one of <see cref="Pipes"/>.</summary>
    public byte Pipe;
    /// <summary>
    /// Material or prop sub-variant: see <see cref="WallPattern"/> for walls and <see cref="Props"/> for floors. Wider
    /// than a byte so the far places (ids 14-20) have room for their props (<see cref="Props.Limit"/>); wall decorations
    /// stay below <see cref="Decor.Limit"/>.
    /// </summary>
    public ushort Variant;
    /// <summary>Level 1: a concrete beam under the slab, spanning between columns.</summary>
    public bool Beam;
    /// <summary>
    /// Stairs: the height of this step (0 = none). Climbs toward <see cref="Pier"/>. In the flight down of a stairwell of
    /// Level 1 or 4 (from layout version 4, <see cref="WorldLayout.FlightZoneDown"/> in <see cref="Zone"/>), the step's
    /// number down from the floor instead (see <see cref="WorldLayout.StairwellSteps"/>).
    /// </summary>
    public byte Stair;
    /// <summary>A glowing EXIT sign above this doorway.</summary>
    public bool ExitSign;
    /// <summary>Level 0 next to Level 1: the ceiling tile is missing, showing bare concrete.</summary>
    public bool Worn;
    /// <summary>Level 5 grand rooms, Level 3 galleries and halls: four blocks of air instead of three.</summary>
    public bool Grand;
    /// <summary>Level 3 squeezes: the ceiling comes down to two blocks of air.</summary>
    public bool Low;
    /// <summary>Inside a space with no way out (locked rooms, barred bays): nobody may be teleported here.</summary>
    public bool Sealed;
    /// <summary>
    /// What is below the floor, or a threshold to somewhere else: Level 3's 1 = flooded utility tunnel, 2 = manhole shaft
    /// down into one (from layout version 9 <see cref="Zone"/> tells their parts apart: <see cref="WorldLayout.L3ShaftLeft"/>,
    /// <see cref="WorldLayout.L3TunnelLanding"/>...); the rest are <see cref="Unders"/>.
    /// </summary>
    public byte Under;
    /// <summary>What hangs under the ceiling or replaces a ceiling tile: one of <see cref="Overheads"/>.</summary>
    public byte Overhead;
    /// <summary>Level 7 and 10 water: how far below the floor the bottom lies.</summary>
    public byte Depth;
    /// <summary>Open-sky levels: the pitched roof over a house or an outbuilding (see <see cref="RoofBits"/>), or 0.</summary>
    public byte Roof;
    /// <summary>
    /// What part of its level this tile is in; meaning depends on the level (e.g. Level 6: 1 = the Snackrooms; Levels 1
    /// and 4: which of a stairwell's flights a step is in, <see cref="WorldLayout.FlightZoneUp"/>; Level 7: the parts of
    /// an entry room and, from layout version 9, of a sunken room, <see cref="WorldLayout.L7ZoneRoom"/>).
    /// </summary>
    public byte Zone;
    /// <summary>Level 11: flags on a building tile (see <see cref="CityDetail"/>).</summary>
    public byte Detail;
    /// <summary>
    /// Level 37: the height above the water's surface of the ceiling over a floor tile (of the top of a slit, on a
    /// wall). Level 94: the height of the ground above the valley floor. Level 1: the floor of a stairwell, plus one, on
    /// its steps and its painted wall (<see cref="WorldLayout.L1FloorOf"/>).
    /// </summary>
    public byte Height;
    /// <summary>A chalk mark at eye height on the wall beside this floor tile, left by someone before (see <see cref="ChalkBits"/>), or 0.</summary>
    public byte Chalk;

    public readonly bool IsWallLike => Kind is TileKind.Wall or TileKind.ArchWindow or TileKind.ArchDoor or TileKind.Doorway or TileKind.Door;
}

/// <summary>Values of <see cref="Tile.Pipe"/>: what hangs in the top block of a tunnel or under a Level 1 ceiling.</summary>
public static class Pipes
{
    public const byte None = 0;
    /// <summary>A bundle of pipes running west-east.</summary>
    public const byte RunX = 1;
    /// <summary>A bundle of pipes running north-south.</summary>
    public const byte RunZ = 2;
    /// <summary>Where bundles meet or turn: both directions plus a junction box.</summary>
    public const byte Hub = 3;
    /// <summary>A bundle with a hissing steam leak.</summary>
    public const byte LeakX = 4;
    public const byte LeakZ = 5;
    /// <summary>Level 1: thin white conduit along the ceiling.</summary>
    public const byte ConduitX = 6;
    public const byte ConduitZ = 7;
    /// <summary>Level 3: bundles of black cable instead of pipes.</summary>
    public const byte CableX = 8;
    public const byte CableZ = 9;
    public const byte CableHub = 10;
    /// <summary>A bundle with a leaking joint that drips onto the floor.</summary>
    public const byte DripX = 11;
    public const byte DripZ = 12;
    /// <summary>Level 3: cable bundles with loops and loose ends hanging down.</summary>
    public const byte CableDroopX = 13;
    public const byte CableDroopZ = 14;
    /// <summary>
    /// Level 5's boiler plant, from layout version 9: what runs overhead (the top block of a boiler bay) along the back
    /// wall over the row of boilers and furnaces. The header is a flue duct with a steam main beside it, along X
    /// (the steam main on the wall side, by the row in the cell). PlantRun is the plain header,
    /// PlantFlue a furnace's flue rising into it from below, PlantBoth a boiler's flue and steam pipe rising into it;
    /// PlantThru, on a wall tile, is where the header passes through a bay wall.
    /// </summary>
    public const byte PlantRun = 15, PlantFlue = 16, PlantBoth = 17, PlantThru = 18;

    // ===== The far places (ids 14-20): one block of values each (see docs/design/new-levels/CONTRACT.md) =====
    public const byte RunFirst = 20, RunLast = 29;
    public const byte FunFirst = 30, FunLast = 39;
    /// <summary>Level Fun: not pipes but what is laid on a party table (the block above it): paper plates, cups, a mess, the cakes, cookies.</summary>
    public const byte FunPlates = 30, FunCups = 31, FunMess = 32, FunCakeBirthday = 33, FunCakeVelvet = 34, FunCookies = 35;
    public const byte EndFirst = 40, EndLast = 49;
    public const byte HubFirst = 50, HubLast = 59;
    public const byte L974First = 60, L974Last = 69;
    // Levels 3999 and 188 (19, 20)
    public const byte L3999First = 70, L3999Last = 79;
    /// <summary>
    /// Level 3999: not pipes but what stands on a mezzanine gallery over this tile (on its slab, rel 8): an arcade
    /// cabinet facing north, east, south or west (70-73), a bench facing north, east, south or west (74-77), a planter.
    /// </summary>
    public const byte L3999UpperCabinet = 70, L3999UpperBench = 74, L3999UpperPlanter = 78;
    public const byte L188First = 80, L188Last = 89;
}

/// <summary>Values of <see cref="Tile.Overhead"/>.</summary>
public static class Overheads
{
    public const byte None = 0;
    /// <summary>A double-sided EXIT sign hanging from the ceiling, its faces toward north and south (WE) or east and west.</summary>
    public const byte ExitSignWE = 1;
    public const byte ExitSignNS = 2;
    /// <summary>Level 1 striped clearance bar on chains across a car park entrance.</summary>
    public const byte ClearanceWE = 3;
    public const byte ClearanceNS = 4;
    /// <summary>Level 1 red sprinkler pipe with a sprinkler head.</summary>
    public const byte SprinklerWE = 5;
    public const byte SprinklerNS = 6;
    /// <summary>Loose wires hanging out of the ceiling.</summary>
    public const byte WireDroop = 7;
    /// <summary>Level 4 ceiling tiles: an air diffuser, a sprinkler head, a water stain.</summary>
    public const byte CeilingVent = 10;
    public const byte CeilingSprinkler = 11;
    public const byte CeilingStain = 12;
    /// <summary>Open-sky levels: the crown of a tree spreading over this tile.</summary>
    public const byte Leaves = 20;
    /// <summary>Level 5: a ceiling fan in a guest room, turning.</summary>
    public const byte CeilingFan = 21;

    // ===== The far places (ids 14-20): one block of values each (see docs/design/new-levels/CONTRACT.md) =====
    public const byte RunFirst = 40, RunLast = 49;
    public const byte FunFirst = 50, FunLast = 59;
    /// <summary>Level Fun: a cluster of balloons against the ceiling (the room's balloon set), crepe streamers across it.</summary>
    public const byte FunBalloons = 50, FunStreamerNS = 51, FunStreamerWE = 52;
    public const byte EndFirst = 60, EndLast = 69;
    /// <summary>The End: a soffit (bulkhead) at rel 4 over this tile; with a bronze letter on its <see cref="Tile.Pier"/> face (letter in <see cref="Tile.Stack"/>).</summary>
    public const byte EndSoffit = 60, EndSoffitLetter = 61;
    /// <summary>The End: a pendant lamp under the atrium's ceiling; an INFORMATION sign hung over a desk; a ceiling tile fallen out.</summary>
    public const byte EndPendant = 62, EndHangSign = 63, EndMissingTile = 64;
    /// <summary>The End: the atrium's mezzanine deck over this tile; at its edge, with a railing on the <see cref="Tile.Pier"/> side.</summary>
    public const byte EndDeck = 65, EndDeckEdge = 66;
    public const byte HubFirst = 70, HubLast = 79;
    /// <summary>The Hub: a pair of jet fans hanging from the ceiling, along a north-south or a west-east tunnel.</summary>
    public const byte HubFanNS = 70, HubFanWE = 71;
    /// <summary>The Hub: a lane signal hanging over a lane, its face to the north or south (NS) or east or west (WE).</summary>
    public const byte HubSignalNS = 72, HubSignalWE = 73;
    public const byte L974First = 80, L974Last = 89;
    /// <summary>Level 974: the closet's clothes rod, three blocks up, hung with pastel clothes (faces <see cref="Tile.Pier"/>).</summary>
    public const byte L974ClosetRod = 80;
    // Levels 3999 and 188 (19, 20)
    public const byte L3999First = 90, L3999Last = 99;
    /// <summary>
    /// Level 3999: a neon tube just under the ceiling, along x (WE) or z (NS), in the colour in <see cref="Tile.Detail"/>;
    /// a dead one; the junction's hanging "3999" sign; a neon sign at rel 5 over a unit's entrance, facing
    /// <see cref="Tile.Pier"/> (its words in <see cref="Tile.Depth"/>, see <see cref="WorldLayout.L3999Signs"/>).
    /// </summary>
    public const byte L3999TubeWE = 90, L3999TubeNS = 91, L3999DeadWE = 92, L3999DeadNS = 93, L3999Sign3999 = 94, L3999Sign = 95;
    public const byte L188First = 100, L188Last = 109;
}

/// <summary>Values of <see cref="Tile.Under"/> beyond Level 3's flooded tunnels: thresholds below the floor.</summary>
public static class Unders
{
    /// <summary>Level 7: the circle of stones on the seabed that leads to Level 9.</summary>
    public const byte Circle = 3;
    /// <summary>Level 7: an underwater cave mouth in the midnight zone, leading to Level 8.</summary>
    public const byte Cave = 4;
    /// <summary>
    /// Level 6: stairs going down toward the sound of waves (step 1, 2, 3), to Level 7. From layout version 9 a stairwell:
    /// Descent1 on its steps (<see cref="Tile.Stair"/> their number), Descent2 on the first row of its landing and
    /// Descent3 on the two beyond, which lead to Level 7 (see <see cref="WorldLayout.L6DescentSteps"/>).
    /// </summary>
    public const byte Descent1 = 5;
    public const byte Descent2 = 6;
    public const byte Descent3 = 7;
    /// <summary>Level 10: the deepest part of a lake, which leads somewhere wetter.</summary>
    public const byte LakeBottom = 8;
    /// <summary>The bank round a Level 10 lake: lake bed, not worms, under the grass.</summary>
    public const byte LakeRim = 9;
    /// <summary>Level 10: a stretch of barn wall that isn't quite there. Walk into it and you noclip into Level 11.</summary>
    public const byte Noclip = 10;
    /// <summary>Level 11: a manhole with no cover, a shaft down into the pipes of Level 2.</summary>
    public const byte OpenManhole = 11;
    /// <summary>Level 11: where the street has broken and fallen away into the caves of Level 8.</summary>
    public const byte Collapse = 12;
    /// <summary>Level 11: the ramp down to a parking garage's basement, which is Level 1 (its step in <see cref="Tile.Stair"/>).</summary>
    public const byte GarageRamp = 13;
    /// <summary>Level 11: a doorway off an alley into a darkness that is Level 6.</summary>
    public const byte DarkPassage = 14;
    /// <summary>Level 11: the deep middle of a park fountain, which leads into the sea of Level 7.</summary>
    public const byte FountainDeep = 15;
    /// <summary>Level 11: the middle of a patch of wheat that should not be growing in a city park. Level 10.</summary>
    public const byte WheatPatch = 16;
    /// <summary>
    /// Level 11: the subway under an avenue, a tunnel or a station with platforms and stairs. Tile.Pipe holds the
    /// offset across the avenue, Tile.Stair a step of the stairs down from the sidewalk.
    /// </summary>
    public const byte Subway = 17;
    public const byte Station = 18;
    /// <summary>Level 37: an opening under the water, three blocks down: the way on is a swim.</summary>
    public const byte PoolHole = 19;
    /// <summary>Level 37: the dark end of an arch-ring tunnel. Walk into it and you come out over the sea of Level 7.</summary>
    public const byte TunnelMouth = 20;
    /// <summary>Level 37: the far end of a dry corridor, where the tile gives way to office carpet. Level 4.</summary>
    public const byte PoolCarpet = 21;
    /// <summary>Level 37: the bottom of a pit too deep to see. Sink to it and you surface in a pool in Level 9.</summary>
    public const byte PitBottom = 22;
    /// <summary>Level 7: a patch of white tile on the seabed. Dive to it and you surface in Level 37.</summary>
    public const byte TiledSeabed = 23;
    /// <summary>Level 9: the one backyard pool in a hundred that is still full. Dive to its bottom: Level 37.</summary>
    public const byte FullPool = 24;
    /// <summary>Level 11: the screen of a cinema showing a stop-motion picture. Walk into it: Level 94.</summary>
    public const byte CinemaScreen = 25;
    /// <summary>Level 94: a house flooded to its ceiling (its floor, and its front door). Open the door: Level 7.</summary>
    public const byte FloodedHouse = 26;
    /// <summary>
    /// A front door between Level 94 and Level 9 (on a house's <see cref="TileKind.Door"/> tile, which keeps its siding):
    /// the door of a doll's house in the Suburbs, or of one house in forty on the hills.
    /// </summary>
    public const byte DollHouse = 27;
    /// <summary>Level 94: a flight of steps on a hill that climbs to nothing (each step's height in <see cref="Tile.Stair"/>).</summary>
    public const byte Nowhere = 28;

    // ===== The far places (ids 14-20): one block of values each, for their thresholds below the floor and the ways into
    // them from other levels (see docs/design/new-levels/CONTRACT.md). 29-39 stay free. =====
    public const byte RunFirst = 40, RunLast = 49;
    /// <summary>Level 2: a blind tunnel end that wasn't there a moment ago (a floor tile before it). Walk into it: Level !.</summary>
    public const byte RunFalseWall = 40;
    /// <summary>Level 37: a dry corridor that turns to hospital vinyl lit red, ending in an EXIT door. Level !.</summary>
    public const byte RunRedCorridor = 41;
    /// <summary>Level !: a hole in the floor of the dark last stretch (on Pit tiles). Fall in: Level 8.</summary>
    public const byte RunHole = 42;
    /// <summary>Level 1: the wall tile carrying the door that shouldn't be there (on Door tiles of pattern RunEntryDoor).</summary>
    public const byte RunEntrance = 43;
    public const byte FunFirst = 50, FunLast = 59;
    /// <summary>Level Fun: the deep middle of a ball pit (dive to its bottom: the castle of Level 94).</summary>
    public const byte FunBallPitDeep = 50;
    /// <summary>Level Fun: the black water beyond an open deck's rail (go overboard: the sea of Level 7).</summary>
    public const byte FunOverboard = 51;
    /// <summary>Level 11: the gym doors painted with a tiger, a parrot and a giraffe at the back of a parking garage (Level Fun).</summary>
    public const byte FunMascotDoor = 52;
    public const byte EndFirst = 60, EndLast = 69;
    /// <summary>The End: a working door in a fake reality (on a doorway tile; <see cref="Tile.Detail"/> = the fake reality's kind).</summary>
    public const byte EndFakeDoor = 61;
    /// <summary>Level 4: under the free-standing wooden doorway into The End.</summary>
    public const byte EndFrame = 62;
    /// <summary>Level 1: a locked hall door under a glowing EXIT sign, into The End (on a door tile).</summary>
    public const byte EndExitL1 = 63;
    /// <summary>Level 11: the closed-down bookstore's door into The End (on a door tile).</summary>
    public const byte EndBookstore = 64;
    /// <summary>The End: a long aisle that loops (on its three middle rows; <see cref="Tile.Pier"/> East: it runs along x, South: along z).</summary>
    public const byte EndLoop = 65;
    /// <summary>The End: a wall carrying a vent at rel 3, onto Level 94.</summary>
    public const byte EndVentWall = 66;
    /// <summary>The Hub has the most ways in and out.</summary>
    public const byte HubFirst = 70, HubLast = 89;
    /// <summary>Level 37: the far end of a dry corridor where the tile gives way to concrete and asphalt. The Hub.</summary>
    public const byte PoolAsphalt = 70;
    /// <summary>The Hub: a stretch of tunnel wall that isn't there (a floor tile). Walk into it: Level 4.</summary>
    public const byte HubFalseWall = 71;
    /// <summary>The Hub: a rectangular hole in the road. Fall in: the sky over Level 94.</summary>
    public const byte HubHole = 72;
    /// <summary>The Hub: the dead end of a side tunnel where the concrete has turned to white tile. Walk on: Level 37.</summary>
    public const byte HubTileEnd = 73;
    /// <summary>Levels 1 and 2: a door into the Hub (a Level 1 wall carrying the door, a Level 2 steel door).</summary>
    public const byte HubEntrance = 74;
    /// <summary>The Hub: the storm void beyond the Tower's balcony. Fall into it and you are cast out into the tunnels.</summary>
    public const byte HubTowerVoid = 75;
    /// <summary>The Hub: the one open window in a tunnel wall, into Level 188 (two wall tiles; Stack 0 left, 1 right; Pier the way it faces).</summary>
    public const byte HubWindow188 = 76;
    public const byte L974First = 90, L974Last = 99;
    /// <summary>Level 974: where a wanderer wakes in a house, beside the bed (not a threshold: only an arrival spot).</summary>
    public const byte L974Arrival = 90;
    // Levels 3999 and 188 (19, 20)
    public const byte L3999First = 100, L3999Last = 109;
    /// <summary>
    /// Level 3999's ways in, in other levels, and its own walked thresholds: Level 11's stretch of alley wall flickering
    /// purple; Level 37's glowing magenta tiles at the bottom of a deep pool; a natatorium's floor drain (to Level 37);
    /// in Level 10, the lone arcade (its walls and its revolving door), its car park, and the windmills that lead to it
    /// (a windmill's tiles, and the generator in front of its door).
    /// </summary>
    public const byte L3999GlitchWall = 100, L3999MagentaTiles = 101, L3999Drain = 102, L3999Arcade = 103, L3999Lot = 104, L3999Windmill = 105;
    public const byte L188First = 110, L188Last = 119;
    /// <summary>
    /// Level 188: a courtyard window that shows another place (<see cref="Tile.Detail"/> = the level it leads to); a
    /// window into 188 in another level (Detail: bits 0-3 the host, 0 Level 0, 1 Level 1, 3 Level Fun; bits 4-5 the way
    /// it faces; bit 6 set on its left half); the hatch in the courtyard deck; a fire door (Detail = its storey).
    /// </summary>
    public const byte L188LinkWindow = 110, L188Entrance = 111, L188Hatch = 112, L188FireDoor = 113;
}

/// <summary>Level 37: what a tile wall carries, in <see cref="Tile.Variant"/>, facing <see cref="Tile.Pier"/>.</summary>
public static class PoolWalls
{
    /// <summary>A tall slit of glare: light from somewhere you can never see, up to <see cref="Tile.Height"/>.</summary>
    public const byte Slit = 1;
    /// <summary>A stainless handrail along the wall at the height of a wader's hand.</summary>
    public const byte Rail = 2;
    /// <summary>A glowing arched opening in a rotunda's wall, onto light.</summary>
    public const byte Arch = 3;
}

/// <summary>
/// Level 11: what a building (or other piece of the city) is, kept in <see cref="Tile.Zone"/>. For a building it is
/// what its ground floor holds.
/// </summary>
public enum CityKind : byte
{
    None,
    Office,
    Hotel,
    Apartment,
    Rowhouse,
    Diner,
    Grocery,
    Pharmacy,
    Hardware,
    Clothing,
    Laundromat,
    Church,
    Garage,
    Substation,
    Sealed,
    Museum,
    /// <summary>The black glass wall at the city's edge, past which no one has been.</summary>
    Rim,
    /// <summary>Public baths: a stone building with a cyan door marked POOL, onto the Poolrooms.</summary>
    Baths,
    /// <summary>A cinema showing a stop-motion picture; walk into the screen and you are in Level 94.</summary>
    Cinema,
    /// <summary>The End's way in (end-plan.md): a closed-down bookstore, its windows papered over, its one door onto The End.</summary>
    Bookstore = 40,
}

/// <summary>Level 11: flags on a building tile, in <see cref="Tile.Detail"/>.</summary>
public static class CityDetail
{
    /// <summary>Bits 0-1: the way a set-back upper façade faces (an <see cref="ArchPier"/>), when <see cref="Setback"/> is set.</summary>
    public const byte FacingMask = 3;
    /// <summary>On an inside tile two in from the edge: the face of the narrower tower that rises above the set-back.</summary>
    public const byte Setback = 4;
    /// <summary>A wall against the next building: blank, no windows.</summary>
    public const byte Party = 8;
    /// <summary>A corner: a solid pier all the way up.</summary>
    public const byte Corner = 16;
    /// <summary>Plate glass on the ground floor, with a fascia over it.</summary>
    public const byte Storefront = 32;
    /// <summary>A column of a museum's colonnade.</summary>
    public const byte Column = 64;
    /// <summary>An open-sided parking garage: low walls, then open air, at every level.</summary>
    public const byte Open = 128;
}

/// <summary>Values of <see cref="Tile.Variant"/> on floor tiles and Level 2 walls.</summary>
/// <remarks>
/// The floor-prop values (1-6 and on) overlap the values the same field takes on walls (<see cref="WallPipes"/> and
/// the like): that works only because every reader checks <see cref="Tile.Kind"/> first.
/// </remarks>
public static class Props
{
    public const byte Drum = 1;
    /// <summary>
    /// Level 2 machine cabinet, facing away from <see cref="Tile.Pier"/> (from layout version 9 with its feed pipe up
    /// the wall behind it into the overhead pipes).
    /// </summary>
    public const byte Cabinet = 2;
    /// <summary>Level 1 metal shelving with boxes, facing away from <see cref="Tile.Pier"/>.</summary>
    public const byte Shelf = 3;
    /// <summary>Level 1 concrete wheel stop at the back of a parking stall.</summary>
    public const byte WheelStop = 4;
    /// <summary>Level 1 abandoned car: this tile draws the whole car. Colour in <see cref="Tile.Stack"/>, facing in <see cref="Tile.Pier"/>.</summary>
    public const byte Car = 5;
    /// <summary>The rest of a car's footprint: invisible and solid.</summary>
    public const byte CarPart = 6;

    // Level 3
    public const byte Transformer = 10;
    /// <summary>A lit window behind bars, glowing like a sunny day.</summary>
    public const byte WindowGlow = 11;
    // Level 4
    public const byte Desk = 20;
    public const byte OfficeChair = 21;
    public const byte FilingCabinet = 22;
    /// <summary>Vending machine that dispenses Almond Water.</summary>
    public const byte Vending = 23;
    /// <summary>Water cooler that dispenses Almond Water.</summary>
    public const byte Cooler = 24;
    public const byte ConferenceTable = 25;
    /// <summary>Low fabric cubicle partition, running along <see cref="Tile.Pier"/>'s axis.</summary>
    public const byte Partition = 26;
    // Level 5
    public const byte Bed = 30;
    public const byte Nightstand = 31;
    public const byte Wardrobe = 32;
    public const byte WingChair = 33;
    /// <summary>The one-tile velvet sofa (from layout version 6, where there is room, <see cref="LongSofa"/>).</summary>
    public const byte Sofa = 34;
    public const byte Palm = 35;
    public const byte MahjongTable = 36;
    public const byte Boiler = 37;
    public const byte Furnace = 38;
    /// <summary>A turntable playing jazz.</summary>
    public const byte Turntable = 39;

    // Level 1. Props that face a way face toward Tile.Pier; props with several kinds take it from Tile.Stack.
    public const byte CardboardBoxes = 40;
    public const byte Workbench = 41;
    public const byte Toolbox = 42;
    /// <summary>Plywood sheets leaning on the wall behind them.</summary>
    public const byte Plywood = 43;
    /// <summary>The one-tile tent and bedroll of layout versions 1-5 (from 6, <see cref="CampTent"/> and <see cref="SleepingBag"/>).</summary>
    public const byte Tent = 44;
    public const byte Bedroll = 45;
    public const byte Lantern = 46;
    /// <summary>Hospital bed: Stack 0 = head end, 1 = foot end; Pier points from the head toward the foot.</summary>
    public const byte HospitalBed = 47;
    public const byte FoldingTable = 48;
    public const byte FoldingChair = 49;
    public const byte MedCabinet = 50;
    public const byte TrafficCone = 51;
    public const byte WetFloorSign = 52;
    public const byte Pallet = 53;
    public const byte TrashCan = 54;
    public const byte PayStation = 55;
    /// <summary>Speed bump: Pier North or South runs it along X, East or West along Z.</summary>
    public const byte SpeedBump = 56;
    public const byte BurnBarrel = 57;
    /// <summary>On doorway tiles: black fire doors propped open, leaves toward Pier; Stack says which leaf (0 left, 1 right).</summary>
    public const byte FireDoor = 58;
    // Level 3
    public const byte Coil = 60;
    public const byte Switchgear = 61;
    public const byte FloorFan = 62;
    public const byte Generator = 63;
    public const byte CableSpool = 64;
    public const byte ControlDesk = 65;
    /// <summary>Conveyor belt: Stack 1 carries a parcel.</summary>
    public const byte Conveyor = 66;
    public const byte Candelabra = 67;
    public const byte AngelStatue = 68;
    /// <summary>Cables on the floor (Pier North along X, East along Z); from layout version 9, Stack 1 a cable box and 2 a rise up the wall at the end of a crossing, Pier toward that wall.</summary>
    public const byte FloorCable = 69;
    public const byte PipeStack = 70;
    /// <summary>
    /// Levels 2, 3 and 5: vanilla machinery against a wall or on the floor (Stack picks the kind; the front faces
    /// <see cref="Tile.Pier"/>, so a gauge frame's Pier points away from the wall behind it). Gauge frames: gauges,
    /// manifold, valve, sight glass. Pressure tanks: plain, valved. Old machinery: pump, governor. Levers: single, double.
    /// </summary>
    public const byte GaugeFrame = 71;
    public const byte PressureTank = 72;
    public const byte RustMachine = 73;
    public const byte FloorLever = 74;
    // Level 2, from layout version 5
    /// <summary>
    /// The B.N.T.G.'s dead tram on its rails, two blocks long (Stack 0 the locomotive's front, 1 its rear), and the goods
    /// wagon behind it, in a main's middle lane; facing <see cref="Tile.Pier"/>.
    /// </summary>
    public const byte Tram = 75;
    public const byte TramWagon = 76;
    /// <summary>Candle stubs on a tin plate by a den's cache, left burning by whoever drew the crosses.</summary>
    public const byte CandleStubs = 77;
    // Camps, from layout version 6: the tent and the bedroll as big as the real things (Tent and Bedroll stay for older worlds)
    /// <summary>
    /// A two-person ridge tent, two tiles by two, its door toward <see cref="Tile.Pier"/>. Stack is the part (0 the front
    /// left, 1 the front right, 2 and 3 behind them, left and right as you look out of the door); see <see cref="WorldLayout.PartTile"/>.
    /// </summary>
    public const byte CampTent = 78;
    /// <summary>A sleeping bag two tiles long: Stack 0 the head end, 1 the foot end; Pier points from the head toward the foot. Walked over.</summary>
    public const byte SleepingBag = 79;
    // Level 4
    public const byte Ficus = 80;
    public const byte ChairStack = 81;
    public const byte Copier = 82;
    public const byte OfficeBookshelf = 83;
    public const byte ServerRack = 84;
    /// <summary>Kitchen counter: Stack 0 plain, 1 with a sink, 2 with a microwave.</summary>
    public const byte KitchenCounter = 85;
    public const byte Fridge = 86;
    public const byte RoundTable = 87;
    public const byte ReceptionDesk = 88;
    public const byte Wastebasket = 89;
    public const byte CoatStand = 90;
    public const byte TippedChair = 91;
    public const byte Bench = 92;
    // Level 5
    public const byte ConsoleTable = 100;
    public const byte HotelBookshelf = 101;
    public const byte CurioCabinet = 102;
    public const byte LuggageCart = 103;
    public const byte ServiceTrolley = 104;
    public const byte Radiator = 105;
    public const byte WritingDesk = 106;
    public const byte HotelChair = 107;
    public const byte FloorLamp = 108;
    public const byte Suitcase = 109;
    public const byte CoffeeTable = 110;
    public const byte GrandfatherClock = 111;
    public const byte FrontDesk = 112;
    public const byte AshtrayStand = 113;
    public const byte DiningTable = 114;
    public const byte GrandPiano = 115;
    public const byte CoalPile = 116;
    /// <summary>From layout version 9, a wooden coal bin standing in front of a Level 5 furnace.</summary>
    public const byte CoalBin = 119;
    /// <summary>
    /// From layout version 6, the velvet sofa as long as a real one, two tiles across, facing <see cref="Tile.Pier"/> (Stack 0 the
    /// left part, 1 the right, as you sit on it; see <see cref="WorldLayout.PartTile"/>). <see cref="Sofa"/> stays for older worlds.
    /// </summary>
    public const byte LongSofa = 117;
    // Level 6
    /// <summary>A thin wire across a corridor at ankle height. Trip on it and you fall into the Snackrooms.</summary>
    public const byte Tripwire = 120;
    // Level 6.1
    public const byte CafeTable = 121;
    public const byte CafeChair = 122;
    /// <summary>Snack bar counter: Stack 0 plain, 1 with a till, 2 a glass food display.</summary>
    public const byte SnackCounter = 123;
    public const byte Stove = 124;
    public const byte Fryer = 125;
    public const byte SnackShelf = 126;
    public const byte SnackVending = 127;
    public const byte DrinkFridge = 128;
    /// <summary>
    /// Level 6.1's vending machine rooms (from layout version 5): a dead machine of the heap (<see cref="Tile.Stack"/> 0
    /// standing, 1 toppled over); <see cref="Tile.Detail"/> <see cref="WorldLayout.SnackPiledOn"/> on this or a working
    /// machine puts another lying across its top.
    /// </summary>
    public const byte VendingPile = 129;
    /// <summary>Layout version 9: the broken snack machine in the doorway of a vending room (a blocker you can break).</summary>
    public const byte BrokenVending = 136;
    // Level 7
    public const byte BonePile = 130;
    public const byte ScrapMetal = 131;
    public const byte JawSkeleton = 132;
    public const byte Ribcage = 133;
    public const byte Backpack = 134;
    public const byte WreckCrate = 135;
    // Level 8
    public const byte MegMarker = 140;
    public const byte RoadLamp = 141;
    public const byte StoneHand = 142;
    public const byte StoneStapler = 143;
    /// <summary>A Deathmoth hive: grey papery cocoons heaped against a wall (a den's tell).</summary>
    public const byte MothHive = 230;
    /// <summary>On a rock tile beside the 9th Road: a vent grate in the cave wall.</summary>
    public const byte CaveVent = 144;
    /// <summary>On a rock tile beside the 9th Road: Almond Water seeping out of the rock.</summary>
    public const byte AlmondSeep = 145;
    /// <summary>
    /// Level 8's bioluminescent fungi (from layout version 5): a cluster of blood-red glowing mushrooms, or of many
    /// colours (<see cref="Tile.Stack"/> 0 on the floor, 1 against the wall on its <see cref="Tile.Pier"/> side).
    /// </summary>
    public const byte GlowcapRed = 146, GlowcapMixed = 147;
    // Level 9
    public const byte Tv = 150;
    /// <summary>Bathtub: Stack 0 = tap end, 1 = far end; Pier points from the tap end along the tub.</summary>
    public const byte Bathtub = 151;
    public const byte Toilet = 152;
    public const byte Dresser = 153;
    /// <summary>Street light: Stack 0 lit, 1 dead, 2 flickering; the lamp arm reaches toward Pier.</summary>
    public const byte Streetlight = 154;
    public const byte Mailbox = 155;
    public const byte SeedSacks = 156;
    public const byte ToolShelf = 157;
    public const byte PantryShelf = 158;
    public const byte KitchenCabinet = 159;
    /// <summary>A tree: trunk on this tile, crown over it and the tiles around (marked with <see cref="Overheads.Leaves"/>).</summary>
    public const byte Tree = 160;
    /// <summary>A gate in a back fence onto the fields, leading to Level 10.</summary>
    public const byte FieldGate = 161;
    // Level 10
    public const byte FeedTrough = 170;
    public const byte ToolRack = 171;
    public const byte NailBarrel = 172;
    /// <summary>Hay bales stacked Stack high.</summary>
    public const byte HayBale = 173;
    /// <summary>A crop standing in a field: Stack 0 spelt, 1 rye, 2 flax.</summary>
    public const byte Crop = 174;
    public const byte TallGrass = 175;
    public const byte Reeds = 176;
    public const byte Scarecrow = 177;
    /// <summary>A wooden telegraph pole along a farm road.</summary>
    public const byte PowerPole = 178;
    public const byte Plough = 179;
    public const byte WaterPump = 180;
    /// <summary>An old tractor: the anchor tile draws it, 2 by 3, the rest are <see cref="CarPart"/> colliders.</summary>
    public const byte Tractor = 182;
    /// <summary>A round bale of hay left in a stubble field.</summary>
    public const byte HayRoll = 183;
    /// <summary>A galvanised water trough out in a field, a hand pump at its end (layout version 5).</summary>
    public const byte WaterTrough = 181;
    /// <summary>A field gate off its hinges, lying flat in a trampled patch of the crops (layout version 5).</summary>
    public const byte FallenGate = 184;
    // Level 9, more of it
    public const byte FireHydrant = 162;
    public const byte StopSign = 163;
    public const byte WheelieBin = 164;
    public const byte BasketballHoop = 165;
    public const byte SwingSet = 166;
    public const byte Grill = 167;
    /// <summary>A washing machine (Stack 0) or a tumble dryer (1).</summary>
    public const byte Laundry = 168;
    public const byte ToyBox = 169;
    public const byte Doghouse = 185;
    /// <summary>A garden shrub: leaves, waist high.</summary>
    public const byte Shrub = 186;
    /// <summary>Flowers in a bed: Stack picks the kind.</summary>
    public const byte Flowers = 187;
    /// <summary>A vegetable in a garden patch: Stack picks the kind.</summary>
    public const byte Vegetable = 188;
    public const byte PatioChair = 189;
    /// <summary>A fruiting bush (vanilla): Stack picks the kind.</summary>
    public const byte BerryBush = 190;
    /// <summary>A reed skep with bees in it (vanilla).</summary>
    public const byte Skep = 191;
    /// <summary>A stone quern (vanilla), for flour, salt and lime.</summary>
    public const byte Quern = 192;
    /// <summary>
    /// A green street-name sign on a Suburbs corner (layout version 5): Stack names the west-east street, Detail the
    /// north-south one (the blade for that is the block over it).
    /// </summary>
    public const byte SuburbSign = 195;
    /// <summary>A guide sign at a Suburbs junction, its arrow toward the city (Pier; layout version 5).</summary>
    public const byte CitySign = 196;
    // Level 5, more of it
    public const byte IceMachine = 200;
    /// <summary>A room-service tray left on the carpet outside a door.</summary>
    public const byte RoomServiceTray = 201;
    public const byte LaundryCart = 202;
    // Level 6, 7 and 8, more of them
    /// <summary>A dropped flashlight, long dead.</summary>
    public const byte Flashlight = 203;
    /// <summary>Driftwood floating on Level 7's sea.</summary>
    public const byte Driftwood = 204;
    public const byte Buoy = 205;
    /// <summary>Kelp growing up from the seabed (Stack tall).</summary>
    public const byte Kelp = 206;
    /// <summary>A post holding up a Level 7 jetty.</summary>
    public const byte JettyPost = 207;
    // Level 11: the street, the stores and the roofs
    /// <summary>Traffic lights on a corner: Stack 0 dead, 1 stuck on red, 2 blinking amber.</summary>
    public const byte TrafficLight = 210;
    public const byte BusShelter = 211;
    public const byte NewsBox = 212;
    /// <summary>A street-name sign: Stack 0 a street, 1 an avenue.</summary>
    public const byte StreetSign = 213;
    public const byte ParkingMeter = 214;
    public const byte PhoneBooth = 215;
    /// <summary>A street vendor's cart that still sells Almond Water, to no one.</summary>
    public const byte VendorCart = 216;
    public const byte ClothesRack = 217;
    public const byte ShoppingCart = 218;
    public const byte Pew = 219;
    public const byte Dumpster = 220;
    public const byte TrashBags = 221;
    /// <summary>On the roofs: an air-conditioning unit, a wooden water tank on legs, a radio mast.</summary>
    public const byte AcUnit = 222;
    public const byte WaterTank = 223;
    public const byte Antenna = 224;
    public const byte Postbox = 225;
    /// <summary>On a brick roof (as <see cref="Tile.Overhead"/>, like the plant): a billboard on legs, its poster to the street (layout version 5).</summary>
    public const byte Billboard = 193;
    /// <summary>A round advertising pillar on a street corner, pasted all round with posters (Stack picks which; layout version 5).</summary>
    public const byte AdPillar = 194;
    // Level 2, more of it
    /// <summary>A flatbed trolley left in a tunnel.</summary>
    public const byte Trolley = 226;
    /// <summary>Pieces of a dismantled machine scattered on the floor.</summary>
    public const byte MachineParts = 227;
    /// <summary>Level 1: a traffic sign on a post, pointing nowhere useful. Stack picks the kind.</summary>
    public const byte TrafficSign = 228;
    // Level 37
    /// <summary>A stainless pool ladder against the edge of a pool, climbing toward <see cref="Tile.Pier"/>.</summary>
    public const byte PoolLadder = 231;
    /// <summary>A crust of Epsom salt dried on a rim in the dark.</summary>
    public const byte EpsomCrust = 232;
    /// <summary>What someone lost: a towel (Stack 0), a flip-flop (1), a pool noodle (2).</summary>
    public const byte LostThing = 233;
    /// <summary>The Reservoir: a bright red sprout on the bottom of a pool, all the light there is.</summary>
    public const byte RedSprout = 234;
    // Level 94
    /// <summary>A siren pole on a street corner that plays the same happy tune all day.</summary>
    public const byte SirenPole = 236;
    /// <summary>A white water tower on a hilltop, full of Almond Water: the anchor tile draws it.</summary>
    public const byte WaterTower = 237;
    /// <summary>The town's fountain, running with Almond Water: the anchor tile draws it.</summary>
    public const byte AlmondFountain = 238;
    /// <summary>A 1930s milk van: the anchor tile draws it, 2 by 3, the rest are <see cref="CarPart"/> colliders.</summary>
    public const byte MilkVan = 239;
    /// <summary>An old 1930s car: the anchor tile draws it, the rest are <see cref="CarPart"/> colliders.</summary>
    public const byte OldCar = 240;
    /// <summary>A NO OUTLET sign at a road that goes on forever.</summary>
    public const byte NoOutletSign = 241;
    /// <summary>A 1950s icebox, a radio cabinet, a rotary telephone on a stand.</summary>
    public const byte Icebox = 242;
    public const byte RadioCabinet = 243;
    public const byte RotaryPhone = 244;
    /// <summary>A heap of furniture with no house: Stack picks which.</summary>
    public const byte FurniturePile = 245;
    /// <summary>A rusted field gate with no sign: at twilight it opens onto Level 10.</summary>
    public const byte TwilightGate = 246;
    // The castle
    /// <summary>A pit of coloured balls: you sink in to the waist.</summary>
    public const byte BallPit = 247;
    /// <summary>An arcade cabinet, dark.</summary>
    public const byte Arcade = 248;
    /// <summary>The animation studio: the table-sized model of a town, a camera on its tripod, an easel of sketches.</summary>
    public const byte Diorama = 249;
    public const byte StudioCamera = 250;
    public const byte Easel = 251;
    /// <summary>The throne room: the long table set for two, the second chair (sit in it for the trial), the King.</summary>
    public const byte ThroneTable = 252;
    public const byte TrialChair = 253;
    public const byte KingStatue = 254;
    /// <summary>A car tipped on its side among the heaps of furniture (Stack picks the colour).</summary>
    public const byte TippedCar = 235;
    /// <summary>A slide between floors of the funhouse: slick, and it carries you down toward <see cref="Tile.Pier"/>.</summary>
    public const byte Slide = 255;

    // ===== The far places (ids 14-20): one block of values each, past the byte (Tile.Variant is a ushort; see
    // docs/design/new-levels/CONTRACT.md). A level declares its props as ushort constants inside its own block only. =====
    public const ushort RunFirst = 300, RunLast = 319;
    // Level ! (Pier = the way the prop faces; Stack as noted)
    /// <summary>A gurney (Stack 0 head, 1 foot; Pier the way the foot points).</summary>
    public const ushort RunGurney = 300;
    public const ushort RunWheelchair = 301;
    public const ushort RunIvStand = 302;
    public const ushort RunChairs = 303;
    public const ushort RunCrashCart = 304;
    /// <summary>Steel shelving lying across the hall (Stack 0 the part by the wall, 1 the other). Jumped over.</summary>
    public const ushort RunShelfFallen = 305;
    /// <summary>Steel shelving standing against the wall, two blocks tall, that topples as you come.</summary>
    public const ushort RunShelfStanding = 306;
    public const ushort RunToyCar = 307;
    public const ushort RunBoxes = 308;
    public const ushort RunCord = 309;
    public const ushort RunSheets = 310;
    public const ushort RunRemains = 311;
    /// <summary>A supply tray (Stack 0 an Energy Bar, 1 Almond Water).</summary>
    public const ushort RunTray = 312;
    public const ushort RunBedside = 313;
    public const ushort RunSafeShelf = 314;
    /// <summary>A cot (Stack 0 head, 1 foot; Pier the way the foot points).</summary>
    public const ushort RunSafeCot = 315;
    public const ushort RunDebris = 316;
    /// <summary>The start room's privacy curtain, two blocks tall, walked through.</summary>
    public const ushort RunCurtain = 317;
    /// <summary>
    /// Layout version 6: where the ceiling has come down (Pier the way the fallen slab leans). Stack 0 a slab hanging from
    /// the broken ceiling onto a heap of rubble, floor to ceiling (go round it); 1 a heap of rubble under the hole (jump it).
    /// </summary>
    public const ushort RunCollapse = 318;
    /// <summary>
    /// Layout version 6: what blocks a corridor (Pier the way it faces). Stack 0 a barricade of beds and chairs, two blocks
    /// tall; 1 a tall supply cabinet against the wall, its door hanging open; 2 and 3 a gurney tipped on its side (head,
    /// foot; foot toward Pier), a block high. The first two you go round; the gurney you jump.
    /// </summary>
    public const ushort RunBarricade = 319;
    public const ushort FunFirst = 320, FunLast = 359;
    // Level Fun. Props that face a way face toward Tile.Pier; Stack picks the kind (see the level's prop table)
    /// <summary>One block of a folding party table in its cloth (Stack: cloth·2 + part; part b lies toward Pier).</summary>
    public const ushort FunTable = 320;
    /// <summary>A plastic stacking chair facing Pier (Stack the colour); knocked over.</summary>
    public const ushort FunChair = 321, FunChairTipped = 322;
    /// <summary>A wrapped gift (Stack: colour·2 + tall).</summary>
    public const ushort FunGift = 323;
    /// <summary>Balloons on the floor; one tied to the floor on a string; the two halves of a balloon arch beside a door; confetti.</summary>
    public const ushort FunBalloonsFloor = 324, FunBalloonTied = 325, FunArchL = 326, FunArchR = 327, FunConfetti = 328;
    /// <summary>A bounce house's corner tower (three blocks tall), its arched way in, the blower, an extension cord.</summary>
    public const ushort FunInflatableTower = 329, FunInflatableArch = 330, FunBlower = 331, FunCord = 332;
    /// <summary>A soft-play foam block; a climbing net (floor to ceiling).</summary>
    public const ushort FunFoam = 333, FunNet = 334;
    public const ushort FunAirHockey = 335, FunPopcornCart = 336, FunCounter = 337, FunOven = 338, FunCakeTins = 339;
    public const ushort FunWaitingChair = 340, FunReception = 341, FunMagazineTable = 342;
    /// <summary>An open deck's white rail (solid, low enough to climb over), a slatted deck chair (two blocks).</summary>
    public const ushort FunShipRail = 343, FunDeckChair = 344;
    public const ushort FunLinenCart = 345, FunSupplyShelf = 346;
    /// <summary>A Carnivorous Balloon, floating at chest height and tied to nothing (Stack the colour).</summary>
    public const ushort FunCBalloon = 347;
    /// <summary>A TIME 4 FUN =) poster on the wall at eye height (the trap in Level 0), and a red "=)" (Stack 0-3).</summary>
    public const ushort FunPosterTrap = 348, FunSmiley = 349;
    /// <summary>A vanilla pumpkin (the Halloween rooms).</summary>
    public const ushort FunPumpkin = 350;
    public const ushort EndFirst = 360, EndLast = 399;
    // The End. Props that face a way face toward Tile.Pier; Stack picks the kind (and the part, for tall ones)
    /// <summary>Double-faced gondola shelving, 2 high: Stack 0 empty, 1 a few books, 2 dusty, 3 an end panel, 4 leaning (it falls at a touch).</summary>
    public const ushort EndShelf = 360;
    /// <summary>A library stack 4 high: Stack 0 empty, 1 books, 2 with a ladder rail.</summary>
    public const ushort EndTallShelf = 361;
    /// <summary>Wall shelving, 2 high, its back to the wall behind (away from Pier): Stack 0 empty, 1 books.</summary>
    public const ushort EndWallShelf = 362;
    /// <summary>A tapered slatwall display tower, 2 high: Stack 0 plain, 1 with a price sticker.</summary>
    public const ushort EndEndcap = 363;
    /// <summary>A piece of a service desk (Stack bits 0-2: straight, curve out, curve in, end, gate; bit 3: a computer on it; bit 4: the central hall's, never "=)").</summary>
    public const ushort EndDesk = 364;
    /// <summary>Library furniture: Stack 0 table, 1 table with a lamp, 2 chair, 3 chair in plastic, 4 armchair, 5 carrel, 6 display table, 7 magazine rack.</summary>
    public const ushort EndFurniture = 365;
    /// <summary>A card catalogue: Stack 0 shut, 1 a drawer open.</summary>
    public const ushort EndCatalogue = 366;
    /// <summary>Stock in a stockroom: Stack 0 a wrapped pallet, 1 a book trolley, 2 a ladder in plastic, 3 a shelving kit.</summary>
    public const ushort EndStock = 367;
    /// <summary>A stopped escalator: the step's height is in Tile.Stair, climbing toward Pier.</summary>
    public const ushort EndEscalator = 368;
    /// <summary>Fallen shelving (Stack 0) or a fallen ceiling (1).</summary>
    public const ushort EndRubble = 369;
    /// <summary>A bare tree in the Snowfield: Stack = its height (3-5).</summary>
    public const ushort EndTree = 370;
    /// <summary>A ladder: Stack 0 a rolling library ladder (2 high), 1 a steel wall ladder (3 high) up to a vent; against the side Pier points to.</summary>
    public const ushort EndLadder = 371;
    /// <summary>Level 4: the free-standing wooden doorway into The End (2 high; Pier = the way through it).</summary>
    public const ushort EndFrame = 372;
    /// <summary>The Snowfield: snow lying on the carpet (walked through).</summary>
    public const ushort EndSnow = 373;
    public const ushort HubFirst = 400, HubLast = 439;
    /// <summary>The Hub: the headless statue in the Tower; the M.E.G.'s door register, doorstep carpet; Camp Amber's sign.</summary>
    public const ushort HubStatue = 400, HubRegister = 401, HubDoormat = 402, HubAmberSign = 403;
    public const ushort L974First = 440, L974Last = 479;
    // Level 974, Kitty's House (Pier = the way the front faces; Stack as noted)
    /// <summary>The little bed (Stack bit 0: 0 head, 1 foot; bits 1-2: the bedding). Pier: the way the foot points.</summary>
    public const ushort L974Bed = 440;
    public const ushort L974Nightstand = 441;
    /// <summary>A heap of plushies (Stack: arrangement 0 or 1).</summary>
    public const ushort L974PlushHeap = 442;
    /// <summary>The desk (Stack 0 plain, 1 with the old computer on it).</summary>
    public const ushort L974Desk = 443;
    /// <summary>A chair (Stack 0 the desk's swivel chair, 1 a dining chair).</summary>
    public const ushort L974Chair = 444;
    public const ushort L974Dresser = 445;
    /// <summary>A quarter of the heart rug (Stack 0-3: NW, NE, SW, SE). Walked over.</summary>
    public const ushort L974Rug = 446;
    /// <summary>The pink fridge and the pantry: two blocks tall.</summary>
    public const ushort L974Fridge = 447;
    public const ushort L974Pantry = 448;
    /// <summary>A kitchen counter (Stack 0 plain, 1 corner, 2 sink, 3 canisters, 4 utensils).</summary>
    public const ushort L974Counter = 449;
    public const ushort L974Stove = 450;
    /// <summary>The banquette (Stack 0 straight, 1 corner: backs opposite Pier and on Pier's right).</summary>
    public const ushort L974Banquette = 451;
    public const ushort L974Table = 452;
    public const ushort L974Toilet = 453;
    public const ushort L974Basin = 454;
    /// <summary>The bathtub (Stack 0 head, 1 foot; Pier the way the foot points).</summary>
    public const ushort L974Bathtub = 455;
    public const ushort L974CatBed = 456;

    // Levels 3999 and 188 (19, 20), as for 14-18
    public const ushort L3999First = 480, L3999Last = 539;
    // Level 3999, the Neon Paradise (Pier = the way the front faces; Stack as noted)
    /// <summary>An arcade cabinet (Stack: the game, 0-5 = a-f); a themed one (Stack: its marquee, see WorldLayout.L3999Themes); a rusted one (walked through); a dead one (3999.1).</summary>
    public const ushort L3999Cabinet = 480, L3999Themed = 481, L3999Rusted = 482, L3999DeadCabinet = 483;
    /// <summary>Two-part games: the racer's seat and its screen, the dance pad and its screen, the skee-ball lane and its target.</summary>
    public const ushort L3999RacerSeat = 484, L3999RacerScreen = 485, L3999DancePad = 486, L3999DanceScreen = 487;
    public const ushort L3999Pinball = 488, L3999Claw = 489, L3999SkeeLane = 490, L3999SkeeTarget = 491;
    /// <summary>An air hockey table, two blocks long (Stack 0 the a half, 1 the b half).</summary>
    public const ushort L3999AirHockey = 492;
    /// <summary>A prize counter; the prize wall behind it (two high); 3999.1's abandoned prize case; a plush (Stack 0-3: bear, cat, alien, smiley).</summary>
    public const ushort L3999PrizeCounter = 493, L3999PrizeWall = 494, L3999PrizeCase = 495, L3999Plush = 496;
    /// <summary>The reception desk (Stack 0 left, 1 middle, 2 right); a couch (Stack 0 left, 1 right); a coffee table; the lost-and-found bin.</summary>
    public const ushort L3999Reception = 497, L3999Couch = 498, L3999CoffeeTable = 499, L3999LostFound = 500;
    public const ushort L3999Planter = 501, L3999Bench = 502, L3999TrashBin = 503, L3999Table = 504;
    /// <summary>A moulded chair (Stack: 0 white, 1 pink, 2 cyan); a diner booth.</summary>
    public const ushort L3999Chair = 505, L3999Booth = 506;
    /// <summary>A food stall's counter (Stack: the food, see WorldLayout.L3999Foods); against the wall behind it, a menu board at rel 3 and the stall's neon sign at rel 5 (Stack: the food).</summary>
    public const ushort L3999StallCounter = 507, L3999MenuBoard = 508;
    /// <summary>A vending machine (Stack 0 snacks, 1 drinks); a mall directory.</summary>
    public const ushort L3999Vending = 509, L3999Directory = 510;
    /// <summary>
    /// A moving walkway's tread (Pier: the way it moves; Stack bit 0: the combplate at an end, bit 1: a rail on its left
    /// side, bit 2: on its right, as seen facing the way it moves; bit 3: the end it starts from). Walked over.
    /// </summary>
    public const ushort L3999Walkway = 511;
    /// <summary>A step of an escalator up to a gallery (Stair: its height; Pier: the way it climbs). Walked over.</summary>
    public const ushort L3999Escalator = 512;
    /// <summary>A mirror-steel column ringed with neon, up to the ceiling (its colour the tile's).</summary>
    public const ushort L3999Pillar = 513;
    /// <summary>The elevator's keypad, at rel 2; a table with a heap of red tickets on it; a pool lounger; a heap of fallen ceiling panels.</summary>
    public const ushort L3999Keypad = 514, L3999TicketPile = 515, L3999Lounger = 516, L3999Debris = 517;
    /// <summary>Level 10: a lamp post in the arcade's car park; the generator on a windmill's wall (its sails above it).</summary>
    public const ushort L3999LampPost = 518, L3999Generator = 519;
    public const ushort L188First = 540, L188Last = 579;
    /// <summary>Level 188's courtyard: a bench (Pier its facing), a bollard lamp, a tuft of moss (walked through), the drain under the downpipe (walked through).</summary>
    public const ushort L188Bench = 540, L188Bollard = 541, L188MossTuft = 542, L188Drain = 543;

    // ===== Improvised camps, from layout version 11 (585-589): what the lost make a camp of, in place of store-bought gear =====
    /// <summary>
    /// A bed made of what was lying about, walked over: Stack 0 flattened cardboard boxes with a coat for a blanket, 1 a heap
    /// of old curtains and blankets with a cushion, 2 a mattress dragged off a bed. Pier is the way it lies.
    /// </summary>
    public const ushort ImprovBed = 585;
    /// <summary>A lean-to: Stack 0 a blue tarp stretched over two stacked chairs, 1 a door propped over two filing cabinets. Faces Pier (its open side).</summary>
    public const ushort LeanTo = 586;
    public const ushort ImprovFirst = 585, ImprovLast = 589;

    // ===== Level 7 from layout version 9 (590-599) =====
    /// <summary>
    /// A chest in a sunken room on Level 7's seabed (WorldLayout.AddSunkenRoom), facing Pier: Stack 0 a sea chest (the
    /// twilight zone's), 1 a riveted strongbox (the midnight zone's, with better in it).
    /// </summary>
    public const ushort SeaChest = 590;

    /// <summary>One past the highest prop any level may use: the size of the generator's prop tables (raise it with a new block).</summary>
    public const int Limit = 600;

    public const byte WallPlain = 0;
    /// <summary>Level 2 wall with horizontal pipes on it.</summary>
    public const byte WallPipes = 1;
    public const byte WallMachinery = 2;
    public const byte WallBrick = 3;
    /// <summary>
    /// Level 2 wall with a vertical riser pipe from floor to ceiling; from layout version 9, <see cref="Tile.Stack"/> 1
    /// puts a valve at its foot.
    /// </summary>
    public const byte WallRiser = 4;
    /// <summary>
    /// Level 2 wall with pipes and a valve wheel (in 1-8 on the bare wall below the pipes; from layout version 9 a gate
    /// valve in the steel pipe).
    /// </summary>
    public const byte WallValve = 5;
    public const byte WallWarning = 6;
    /// <summary>Level 3 wall with an electrical panel.</summary>
    public const byte WallPanel = 7;
    /// <summary>Level 3 wall with an industrial fan.</summary>
    public const byte WallFan = 8;
    /// <summary>Level 3 numbered machine-room sign (above a doorway).</summary>
    public const byte WallSign = 9;
    /// <summary>Level 5 wall with a candle sconce.</summary>
    public const byte WallSconce = 12;
    /// <summary>Level 5 wall with a portrait.</summary>
    public const byte WallPortrait = 13;
    /// <summary>Level 5 "The Beverly Room" placard.</summary>
    public const byte WallBeverly = 14;
}

/// <summary>
/// Decorations on one face of a wall block, kept in <see cref="Tile.Variant"/> of a wall tile and facing
/// <see cref="Tile.Pier"/>. Each belongs to the wall materials noted beside it.
/// </summary>
public static class Decor
{
    public const byte First = 40;
    // Level 1: white block and concrete walls (banners also hang on pillars)
    public const byte PowerBox = 40;
    public const byte Breaker = 41;
    public const byte Outlet = 42;
    public const byte Extinguisher = 43;
    public const byte Alarm = 44;
    public const byte HoseCabinet = 45;
    public const byte LevelSign = 46;
    public const byte StairSign = 47;
    public const byte Note = 48;
    public const byte Graffiti = 49;
    public const byte Pipes = 50;
    public const byte Standpipe = 51;
    /// <summary>Four crude drawings and old paintings, 52-55.</summary>
    public const byte Painting = 52;
    /// <summary>Four coloured cloth landmarks left by groups of wanderers, 56-59.</summary>
    public const byte Banner = 56;
    // Level 3: glazed tile, brick, cinder block, Sanctum stone
    public const byte DangerSign = 60;
    public const byte Gauges = 61;
    public const byte KnifeSwitch = 62;
    public const byte JunctionBox = 63;
    public const byte SparkOutlet = 64;
    public const byte Bulkhead = 65;
    public const byte AlarmBell = 66;
    public const byte WallCables = 67;
    public const byte Risers = 68;
    /// <summary>
    /// Level 3, from layout version 5: something dead, half noclipped into the wall, it and the wall round it gone
    /// purple: "Purpification" (Wikidot). Rare.
    /// </summary>
    public const byte Purpified = 69;
    /// <summary>Eight numbered machine-room signs, 70-77, hung beside the door.</summary>
    public const byte RoomSign = 70;
    // Level 4: drywall
    public const byte Fountain = 80;
    public const byte Clock = 81;
    public const byte Whiteboard = 82;
    public const byte Corkboard = 83;
    public const byte EvacMap = 84;
    public const byte ExtCabinet = 85;
    public const byte FireAlarm = 86;
    public const byte LightSwitch = 87;
    public const byte FrameGhost = 88;
    public const byte Phone = 89;
    public const byte CallButton = 90;
    public const byte OfficeStairSign = 91;
    /// <summary>Three framed motivational posters, 92-94.</summary>
    public const byte Poster = 92;
    /// <summary>
    /// From layout version 9: a whiteboard two blocks wide, in halves on two wall tiles side by side facing the same way
    /// (the left half as you face it on the tile with the larger coordinate when it faces north or east, the smaller
    /// when south or west). In 1-8 every whiteboard was one block wide (<see cref="Whiteboard"/>).
    /// </summary>
    public const byte WhiteboardLeft = 97, WhiteboardRight = 98;
    // Level 5: hotel panelling
    public const byte Mirror = 100;
    public const byte Speaker = 101;
    public const byte HousePhone = 102;
    public const byte FireHose = 103;
    public const byte HotelClock = 104;
    public const byte KeyRack = 105;
    public const byte CallPlate = 106;
    public const byte Landscape = 107;
    // Level 5 boiler halls: plaster
    public const byte PipesV = 110;
    public const byte Valve = 111;
    public const byte PlasterGauges = 112;
    public const byte PipeCluster = 113;
    /// <summary>Level 1: a security camera high on a wall, long dead.</summary>
    public const byte Camera = 114;
    /// <summary>Level 6: a light switch. It does nothing.</summary>
    public const byte DeadSwitch = 115;
    /// <summary>Level 3: a plaque beside a barred way, OUT OF BOUNDS or DO NOT ENTER.</summary>
    public const byte Plaque = 116;
    // Level 6: chalk left by the M.E.G. and others before you
    public const byte MegExit = 120;
    public const byte MegCross = 121;
    public const byte MegLogo = 122;
    public const byte Handprints = 123;
    public const byte Scratches = 124;
    // Level 6.1: neon signs over the snack bars, menu boards, mall directories
    public const byte SignBurger = 125;
    public const byte SignPizza = 126;
    public const byte SignTaco = 127;
    public const byte SignDonut = 128;
    public const byte MenuBoard = 129;
    public const byte MallMap = 130;
    // Level 9: what hangs on the walls inside the houses
    public const byte FamilyPhoto = 131;
    public const byte HousePainting = 132;
    public const byte HouseClock = 133;
    public const byte HouseMirror = 134;
    // Level 11: signs over the stores, in English and now and then in Spanish (on the storefront fascia)
    public const byte SignDiner = 140;
    public const byte SignGrocery = 141;
    public const byte SignPharmacy = 142;
    public const byte SignHardware = 143;
    public const byte SignLaundry = 144;
    public const byte SignClothing = 145;
    public const byte SignHotel = 146;
    public const byte SignOffices = 147;
    public const byte SignApartments = 148;
    public const byte SignParking = 149;
    public const byte SignMuseum = 150;
    public const byte SignFarmacia = 151;
    public const byte SignLavanderia = 152;
    public const byte SignBodega = 153;
    // Level 11: inside, on plaster
    public const byte Mailboxes = 155;
    public const byte Directory = 156;
    public const byte MissingPoster = 157;
    /// <summary>Eight paintings in the museum galleries, 160-167, each of another level.</summary>
    public const byte Gallery = 160;
    // Level 11: the subway, on its tiles
    public const byte StationSign = 170;
    public const byte SubwayMap = 171;
    public const byte SubwayLamp = 172;
    public const byte SubwayAd = 173;

    // ===== The far places (ids 14-20): one block of values each (see docs/design/new-levels/CONTRACT.md). Decoration codes
    // are looked up by name across every family, so a level's codes must not reuse another's names. 174-175 stay free. =====
    public const byte RunFirst = 176, RunLast = 183;
    public const byte FunFirst = 184, FunLast = 195;
    public const byte EndFirst = 196, EndLast = 207;
    /// <summary>The End, on its walls and columns (facing Pier): THE END posters (yellow, pink, green, the notice), 196-199; a pale ghost where a sign hung; a crack.</summary>
    public const byte EndPoster = 196, EndGhost = 200, EndCrack = 201;
    /// <summary>The End: a bronze letter on a wall at rel 3 (the letter in Tile.Stack).</summary>
    public const byte EndLetter = 202;
    public const byte HubFirst = 208, HubLast = 223;
    /// <summary>Level 1: the grey door into the Hub, with the Hub's carved sigil over it (on concrete or white block walls).</summary>
    public const byte HubEntranceDoor = 208;
    public const byte L974First = 224, L974Last = 235;
    // Levels 3999 and 188 (19, 20)
    public const byte L3999First = 236, L3999Last = 247;
    /// <summary>Level 3999 draws its own walls; its walls' Variant is its own (a painted window's column), not a decoration.</summary>
    public const byte L188First = 248, L188Last = 255;

    /// <summary>One past the highest decoration: wall decorations stay within a byte.</summary>
    public const int Limit = 256;
}

/// <summary>The large-scale character of an area. Zones are irregular blobs a few hundred blocks across.</summary>
public enum ZoneKind : byte
{
    /// <summary>Randomly segmented rooms and hallways of all sizes, the default.</summary>
    Lobby,
    /// <summary>Big open carpet broken up by free-standing partitions that end abruptly, like the original photo.</summary>
    OpenOffice,
    /// <summary>Vast halls with a lattice of pillars, some out of place.</summary>
    PillarHall,
    /// <summary>Cream walls with half-height arched openings.</summary>
    Arches,
    /// <summary>Dead lights, silence, soaked carpet and flooded rooms.</summary>
    Blackout,
}

/// <summary>How the ceiling lights in an area behave.</summary>
public enum LightMood : byte
{
    Normal,
    /// <summary>Half the lights dead (pit rooms).</summary>
    Half,
    /// <summary>No ceiling lights at all (inside the Manila Room).</summary>
    None,
    Dim,
    Failing,
    Dark,
    Blackout,
    /// <summary>The Red Rooms: a few dim red lamps and nothing else.</summary>
    Red,
}
