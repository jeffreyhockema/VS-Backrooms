using System;
using System.Linq;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// The special places of each level that the cheat menu's "Go to feature (in this level)" offers and
/// <c>/backrooms feature &lt;code&gt;</c> goes to: by level, a code and the name a player would call it (the handbook's
/// wording), and how far the search reaches by default. Names and codes only, so the client's menu reads the same table
/// the server does; the finders are <see cref="FeatureFinder"/>'s (server side, and the layout harness's featurecheck).
/// A code may stand in several levels (an elevator is an elevator): the command looks in the player's own level.
/// </summary>
public static class FeatureCatalog
{
    public readonly record struct Entry(int Level, string Code, string Name, int Radius);

    private const int Tiles = 1024, Cells = 4096, Far = 8192;

    public static readonly Entry[] All =
    {
        // ===== Level 0, the Lobby =====
        new(0, "redroom", "Red Room", Far),
        new(0, "manila", "Manila Room", Far),
        new(0, "pit", "Room of pits", Tiles),
        new(0, "l0blackout", "Blackout zone", Cells),
        new(0, "l0arches", "Arches (cream walls)", Cells),
        new(0, "l0pillars", "Pillar hall", Cells),
        new(0, "l0office", "Open office", Cells),
        new(0, "l0party", "Party room (to Fun)", Far),
        new(0, "l0window", "Window (to Level 188)", Tiles),
        // ===== Level 1, the Habitable Zone =====
        new(1, "stairs", "Stair core", Tiles),
        new(1, "l1nowhere", "Stairs to nowhere", Tiles),
        new(1, "l1funstairs", "Stairs up to Level Fun", Tiles),
        new(1, "l1halls", "Maintenance halls", Tiles),
        new(1, "l1firstaid", "First-aid room", Tiles),
        new(1, "l1hubdoor", "Grey door (to the Hub)", Cells),
        new(1, "l1enddoor", "EXIT door (to The End)", Tiles),
        new(1, "l1rundoor", "Door that shouldn't be (!)", Far),
        new(1, "l1window", "Window (to Level 188)", Far),
        // ===== Level 2, Pipe Dreams =====
        new(2, "tram", "Dead tram", Tiles),
        new(2, "l2gallery", "Pump gallery", Cells),
        new(2, "l2hubdoor", "Chalk-circle door (Hub)", Cells),
        new(2, "l2runwall", "Blind tunnel end (!)", Tiles),
        // ===== Level 3, the Electrical Station =====
        new(3, "elevator", "Freight elevator", Tiles),
        new(3, "manhole", "Manhole (flooded tunnel)", Tiles),
        new(3, "l3sanctum", "Sanctum", Cells),
        new(3, "l3transformer", "Transformer hall", Cells),
        new(3, "l3assembly", "Assembly line hall", Cells),
        new(3, "l3shrine", "Shrine (barred statue)", Tiles),
        new(3, "l3window", "Window room", Tiles),
        new(3, "l3sludge", "Sludge pool", Tiles),
        new(3, "purpified", "Purpified thing", Tiles),
        // ===== Level 4, the Abandoned Office =====
        new(4, "elevator", "Elevator", Tiles),
        new(4, "stairs", "Stairwell", Tiles),
        new(4, "hotelturn", "Carpet turning to hotel", Tiles),
        new(4, "l4camp", "Wanderer outpost", Tiles),
        new(4, "l4endframe", "Lone doorway (The End)", Tiles),
        // ===== Level 5, the Terror Hotel =====
        new(5, "fronthall", "Front hall", Cells),
        new(5, "l5grand", "Grand staircase", Cells),
        new(5, "l5beverly", "Beverly Room", Cells),
        new(5, "l5dining", "Dining hall", Cells),
        new(5, "l5boiler", "Boiler hall", Cells),
        new(5, "door666", "Door 666", Tiles),
        new(5, "elevator", "Elevator", Tiles),
        new(5, "l5staff", "Staff stairs (to Level 6)", Tiles),
        new(5, "l5fundoor", "Party door (to Fun)", Tiles),
        // ===== Level 6, Lights Out, and 6.1, the Snackrooms =====
        new(6, "descent", "Stairs down (to Level 7)", Tiles),
        new(6, "l6tripwire", "Tripwire (to 6.1)", Tiles),
        new(6, "snackrooms", "Snackrooms (6.1)", Cells),
        new(6, "vendingroom", "Vending room (6.1)", Tiles),
        new(6, "l6snackexit", "Snackrooms exit door", Tiles),
        // ===== Level 7, Thalassophobia =====
        new(7, "entryroom", "Entry room (stairs up)", Tiles),
        new(7, "sunkenroom", "Sunken room", Tiles),
        new(7, "l7island", "Island", Tiles),
        new(7, "seapillar", "Rock pillar", Tiles),
        new(7, "shelter", "Island shelter", Tiles),
        new(7, "l7jetty", "Jetty", Tiles),
        new(7, "l7circle", "Stone circle (to Level 9)", Tiles),
        new(7, "l7cave", "Cave mouth (to Level 8)", Tiles),
        new(7, "l7tiled", "Tiled seabed (to 37)", Tiles),
        // ===== Level 8, the Cave System =====
        new(8, "l8road", "The 9th Road", Tiles),
        new(8, "l8camp", "Road camp", Tiles),
        new(8, "glowcaps", "Blood-red glowcaps", Tiles),
        new(8, "l8seep", "Almond Water seep", Tiles),
        new(8, "l8vent", "Vent (to Level 2)", Tiles),
        new(8, "l8rockfall", "Rockfall on the road", Tiles),
        new(8, "l8nest", "Spider nest", Cells),
        // ===== Level 9, the Suburbs =====
        new(9, "l9house", "Two-storey house", Tiles),
        new(9, "citysign", "DOWNTOWN sign", Tiles),
        new(9, "l9pool", "Backyard pool", Tiles),
        new(9, "l9fullpool", "Full pool (to Level 37)", Tiles),
        new(9, "l9dollhouse", "Doll's house (to 94)", Tiles),
        new(9, "l9fieldgate", "Field gate (to Level 10)", Tiles),
        new(9, "l9shed", "Garden shed", Tiles),
        new(9, "l9swings", "Swing set", Tiles),
        new(9, "l9veg", "Vegetable patch", Tiles),
        // ===== Level 10, the Bumper Crop =====
        new(10, "fieldthing", "Shed, trough or gate", Tiles),
        new(10, "l10scarecrow", "Scarecrow", Tiles),
        new(10, "l10farm", "Farmstead (barn)", Tiles),
        new(10, "l10noclip", "Barn wall (to Level 11)", Tiles),
        new(10, "l10pond", "Pond", Tiles),
        new(10, "l10pasture", "Paddock", Tiles),
        new(10, "l10arcade", "Lone arcade (to 3999)", Far),
        new(10, "l10windmill", "Windmill (to 3999)", Far),
        // ===== Level 11, the Endless City =====
        new(11, "l11station", "Subway station", Tiles),
        new(11, "billboard", "Billboard", Tiles),
        new(11, "adpillar", "Advertising pillar", Tiles),
        new(11, "l11church", "Church", Tiles),
        new(11, "l11museum", "Museum", Tiles),
        new(11, "l11diner", "Diner", Tiles),
        new(11, "l11hotel", "Hotel (to Level 5)", Tiles),
        new(11, "l11office", "Office tower (to Level 4)", Tiles),
        new(11, "l11garage", "Parking garage (to 1)", Tiles),
        new(11, "l11mascot", "Mascot doors (to Fun)", Tiles),
        new(11, "l11cinema", "Cinema (to Level 94)", Tiles),
        new(11, "l11bookstore", "Bookstore (to The End)", Tiles),
        new(11, "l11baths", "Public baths (to 37)", Tiles),
        new(11, "l11substation", "Substation", Tiles),
        new(11, "l11manhole", "Open manhole (to Level 2)", Tiles),
        new(11, "l11collapse", "Collapsed street (to 8)", Tiles),
        new(11, "l11alley", "Dark doorway (to Level 6)", Tiles),
        new(11, "l11fountain", "Park fountain (to Level 7)", Tiles),
        new(11, "l11wheat", "Wheat patch (to Level 10)", Tiles),
        new(11, "l11glitch", "Purple wall (to 3999)", Tiles),
        // ===== Level 37, the Poolrooms =====
        new(WorldLayout.Poolrooms, "l37rotunda", "Domed rotunda", Cells),
        new(WorldLayout.Poolrooms, "l37natatorium", "Natatorium", Cells),
        new(WorldLayout.Poolrooms, "l37pillars", "Pillar hall", Cells),
        new(WorldLayout.Poolrooms, "l37serpentine", "Serpentine pool", Cells),
        new(WorldLayout.Poolrooms, "pit", "Stair pit", Cells),
        new(WorldLayout.Poolrooms, "l37pitbottom", "Bottomless pit (to 9)", Tiles),
        new(WorldLayout.Poolrooms, "l37door", "POOL door", Tiles),
        new(WorldLayout.Poolrooms, "l37hole", "Underwater passage", Tiles),
        new(WorldLayout.Poolrooms, "l37tunnel", "Arch tunnel (to Level 7)", Tiles),
        new(WorldLayout.Poolrooms, "l37carpet", "Carpet corridor (to 4)", Tiles),
        new(WorldLayout.Poolrooms, "l37run", "Red corridor (to Level !)", Tiles),
        new(WorldLayout.Poolrooms, "l37asphalt", "Asphalt corridor (Hub)", Tiles),
        new(WorldLayout.Poolrooms, "l37magenta", "Magenta tiles (to 3999)", Tiles),
        new(WorldLayout.Poolrooms, "l37reservoir", "Sanguine Reservoir (37.1)", Far),
        // ===== Level 94, Motion =====
        new(WorldLayout.Motion, "l94castle", "The castle gate", Far),
        new(WorldLayout.Motion, "l94mountain", "Foot of the glass mountain", Far),
        new(WorldLayout.Motion, "l94town", "Town square (fountain)", Tiles),
        new(WorldLayout.Motion, "l94siren", "Siren pole", Tiles),
        new(WorldLayout.Motion, "l94house", "House on a hill", Cells),
        new(WorldLayout.Motion, "l94kitchen", "Kitchen on a hill", Cells),
        new(WorldLayout.Motion, "l94bedroom", "Bedroom on a hill", Cells),
        new(WorldLayout.Motion, "l94parlour", "Parlour on a hill", Cells),
        new(WorldLayout.Motion, "l94pile", "Pile of furniture", Cells),
        new(WorldLayout.Motion, "l94tower", "Water tower", Cells),
        new(WorldLayout.Motion, "l94car", "Parked car", Cells),
        new(WorldLayout.Motion, "l94gate", "Field gate (to Level 10)", Cells),
        new(WorldLayout.Motion, "l94nowhere", "Steps to nowhere", Tiles),
        new(WorldLayout.Motion, "l94flooded", "Flooded house (to 7)", Tiles),
        new(WorldLayout.Motion, "l94dollhouse", "Doll's house door (to 9)", Tiles),
        // ===== Level !, Run For Your Life =====
        new(WorldLayout.RunLevel, "runstart", "Start room", 600),
        new(WorldLayout.RunLevel, "runhall", "Hallway", 36),
        new(WorldLayout.RunLevel, "runsafe", "Safe Zone", 600),
        new(WorldLayout.RunLevel, "runfake", "False exit", 600),
        new(WorldLayout.RunLevel, "runhole", "Hole in the floor (to 8)", 600),
        new(WorldLayout.RunLevel, "runexit", "The true exit", 600),
        // ===== Level Fun =) =====
        new(WorldLayout.FunLevel, "funparty", "Party room (guests)", Tiles),
        new(WorldLayout.FunLevel, "funover", "Party's over room", Tiles),
        new(WorldLayout.FunLevel, "funmural", "Mural room", Tiles),
        new(WorldLayout.FunLevel, "funthemed", "Themed room", Tiles),
        new(WorldLayout.FunLevel, "funplay", "Ball pit room", Tiles),
        new(WorldLayout.FunLevel, "funbounce", "Bounce hall", Tiles),
        new(WorldLayout.FunLevel, "funarcade", "Arcade", Tiles),
        new(WorldLayout.FunLevel, "funkitchen", "Kitchen", Tiles),
        new(WorldLayout.FunLevel, "fungifts", "Gifts room", Tiles),
        new(WorldLayout.FunLevel, "fundeck", "Open deck (to Level 7)", Tiles),
        new(WorldLayout.FunLevel, "funwaiting", "Waiting room", Tiles),
        new(WorldLayout.FunLevel, "funvestibule", "FUN doors", Tiles),
        new(WorldLayout.FunLevel, "funstairs", "Service stairs", Tiles),
        new(WorldLayout.FunLevel, "funclone", "Cloned hall", Tiles),
        // ===== The End =====
        new(WorldLayout.TheEnd, "endcentral", "Central hall", Far),
        new(WorldLayout.TheEnd, "endexit", "Central hall's EXIT", Far),
        new(WorldLayout.TheEnd, "endwall", "Partition wall", 2048),
        new(WorldLayout.TheEnd, "enddesk", "Service desk (computer)", Cells),
        new(WorldLayout.TheEnd, "endreading", "Reading room", Cells),
        new(WorldLayout.TheEnd, "endatrium", "Atrium", Cells),
        new(WorldLayout.TheEnd, "endstock", "Stockroom", Cells),
        new(WorldLayout.TheEnd, "endloop", "Looping aisle", Cells),
        new(WorldLayout.TheEnd, "endcollapse", "Collapse", Cells),
        new(WorldLayout.TheEnd, "endfake", "Fake reality", Cells),
        // ===== The Hub =====
        new(WorldLayout.Hub, "hubtower", "The Tower", Far),
        new(WorldLayout.Hub, "hubmeg", "M.E.G. outpost", Far),
        new(WorldLayout.Hub, "hubcamp", "Camp Amber", Far),
        new(WorldLayout.Hub, "hubdoor", "Nearest level door", Far),
        new(WorldLayout.Hub, "hubwindow", "Window (to Level 188)", Far),
        new(WorldLayout.Hub, "hubtileend", "White-tile end (to 37)", Far),
        new(WorldLayout.Hub, "hubhole", "Hole in the road (to 94)", Tiles),
        new(WorldLayout.Hub, "hubfalsewall", "Wall that isn't (to 4)", Tiles),
        new(WorldLayout.Hub, "hubfar", "Far Tunnels", Tiles),
        // ===== Level 974, Kitty's house =====
        new(WorldLayout.Level974, "l974living", "Living room", 256),
        new(WorldLayout.Level974, "l974kitchen", "Kitchen-diner", 256),
        new(WorldLayout.Level974, "l974master", "Main bedroom", 256),
        new(WorldLayout.Level974, "l974bedroom", "Bedroom", 256),
        new(WorldLayout.Level974, "l974bath", "Bathroom", 256),
        new(WorldLayout.Level974, "l974hall", "Hall", 256),
        // ===== Level 3999, the Neon Paradise =====
        new(WorldLayout.Level3999, "foodcourt", "Food court", 2048),
        new(WorldLayout.Level3999, "l3999lobby", "Lobby", 2048),
        new(WorldLayout.Level3999, "l3999game", "Game room", 2048),
        new(WorldLayout.Level3999, "l3999hall", "Game hall", 2048),
        new(WorldLayout.Level3999, "l3999lanes", "Bowling lanes", 2048),
        new(WorldLayout.Level3999, "l3999natatorium", "Neon natatorium", 4096),
        new(WorldLayout.Level3999, "l3999shuttered", "Shuttered unit", 2048),
        new(WorldLayout.Level3999, "l3999mini", "Mini arcade (elevator)", 4096),
        new(WorldLayout.Level3999, "l3999junction", "Junction", Tiles),
        new(WorldLayout.Level3999, "l3999drain", "Pool drain (to 37)", 4096),
        new(WorldLayout.Level3999, "l3999blackout", "Neon Blackout (3999.1)", Far),
        // ===== Level 188, the Courtyard of Windows =====
        new(WorldLayout.Level188, "l188deck", "Courtyard deck", Far),
        new(WorldLayout.Level188, "l188hatch", "Deck hatch (to Level 37)", Far),
        new(WorldLayout.Level188, "l188window", "Courtyard window", Far),
        new(WorldLayout.Level188, "courtdoor", "Courtyard door (EXIT)", Far),
        new(WorldLayout.Level188, "downpipe", "Downpipe", Far),
        new(WorldLayout.Level188, "l188lobby", "Lobby", Far),
        new(WorldLayout.Level188, "l188stairs", "Stair hall", Far),
        new(WorldLayout.Level188, "l188firedoor", "Fire door", Far),
    };

    /// <summary>The features of a level, in the menu's order.</summary>
    public static Entry[] ForLevel(int level) => All.Where(e => e.Level == level).ToArray();

    /// <summary>A level's feature by its code, or null.</summary>
    public static Entry? Find(int level, string code) =>
        All.FirstOrDefault(e => e.Level == level && string.Equals(e.Code, code, StringComparison.OrdinalIgnoreCase)) is { Code: not null } e ? e : null;

    /// <summary>Every code there is (for the command's argument).</summary>
    public static string[] Codes => All.Select(e => e.Code).Distinct().ToArray();
}
