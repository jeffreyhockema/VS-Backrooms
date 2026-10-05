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
}

/// <summary>Which side of an arch header block is attached to its pier (the thick, low end of the curve).</summary>
public enum ArchPier : byte { West, East, North, South }

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
    /// <summary>Level 5 grand rooms: four blocks of air instead of three.</summary>
    public bool Grand;
    /// <summary>Inside a space with no way out (locked rooms, barred bays): nobody may be teleported here.</summary>
    public bool Sealed;
    /// <summary>Level 3 below the floor: 1 = flooded utility tunnel, 2 = manhole shaft down into one.</summary>
    public byte Under;

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
}
