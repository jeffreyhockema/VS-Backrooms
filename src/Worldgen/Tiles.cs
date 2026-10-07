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
    /// <summary>Level 1: height of a stack of crates (0 = none).</summary>
    public byte Stack;
    /// <summary>Overhead pipework, one of <see cref="Pipes"/>.</summary>
    public byte Pipe;
    /// <summary>Material or prop sub-variant: see <see cref="WallPattern"/> for walls and <see cref="Props"/> for floors.</summary>
    public byte Variant;
    /// <summary>Level 1: a concrete beam under the slab, spanning between columns.</summary>
    public bool Beam;
    /// <summary>Level 1 stairs to nowhere: the height of this step (0 = none). Climbs toward <see cref="Pier"/>.</summary>
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
    /// <summary>Level 3 below the floor: 1 = flooded utility tunnel, 2 = manhole shaft down into one.</summary>
    public byte Under;
    /// <summary>What hangs under the ceiling or replaces a ceiling tile: one of <see cref="Overheads"/>.</summary>
    public byte Overhead;
    /// <summary>Level 7 and 10 water: how far below the floor the bottom lies.</summary>
    public byte Depth;
    /// <summary>Open-sky levels: the pitched roof over a house or an outbuilding (see <see cref="RoofBits"/>), or 0.</summary>
    public byte Roof;
    /// <summary>What part of its level this tile is in; meaning depends on the level (e.g. Level 6: 1 = the Snackrooms).</summary>
    public byte Zone;
    /// <summary>Level 11: flags on a building tile (see <see cref="CityDetail"/>).</summary>
    public byte Detail;
    /// <summary>
    /// Level 37: the height above the water's surface of the ceiling over a floor tile (of the top of a slit, on a
    /// wall). Level 94: the height of the ground above the valley floor.
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
}

/// <summary>Values of <see cref="Tile.Under"/> beyond Level 3's flooded tunnels: thresholds below the floor.</summary>
public static class Unders
{
    /// <summary>Level 7: the circle of stones on the seabed that leads to Level 9.</summary>
    public const byte Circle = 3;
    /// <summary>Level 7: an underwater cave mouth in the midnight zone, leading to Level 8.</summary>
    public const byte Cave = 4;
    /// <summary>Level 6: stairs going down toward the sound of waves (step 1, 2, 3), to Level 7.</summary>
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
public static class Props
{
    public const byte Drum = 1;
    /// <summary>Level 2 machine cabinet, facing away from <see cref="Tile.Pier"/>.</summary>
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
    public const byte FloorCable = 69;
    public const byte PipeStack = 70;
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

    public const byte WallPlain = 0;
    /// <summary>Level 2 wall with horizontal pipes on it.</summary>
    public const byte WallPipes = 1;
    public const byte WallMachinery = 2;
    public const byte WallBrick = 3;
    /// <summary>Level 2 wall with a vertical riser pipe from floor to ceiling.</summary>
    public const byte WallRiser = 4;
    /// <summary>Level 2 wall with pipes and a valve wheel.</summary>
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
