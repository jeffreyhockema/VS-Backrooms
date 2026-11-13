using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 36, "Airport" (experimental): kept as level 25 (<see cref="Level36"/>) and shown as "36". The Timeless Airport /
/// Desolate Terminal: an endless, empty, spotless terminal in a round noclip region far out to the west-south-west (the
/// design is docs/design/experimental-levels/36-plan.md). Its ways in and out (doors under an airplane sign in Levels 9 and
/// 11, the flights, a restroom sink) are WorldLayout.Level36.Links.cs's.
///
/// <para><b>Landside</b> (west to east, in blocks from the baggage wall, <see cref="L36WallX"/>, a straight north-south line
/// three quarters of the radius west of the centre: everything west of it is solid, the only bounded edge the lore knows):
/// the baggage claim hall (1-24, 7 high: a carousel every 32 blocks coming out of the wall, Lost and Found offices), the
/// check-in hall (26-43, 9 high: islands of desks under flight screens, queue mazes, the Backrooms Travel Agency's booths,
/// booth 0 on the region's centre line), the defunct security checkpoint (45-56, 5 high: lanes of scanners and X-ray belts).</para>
///
/// <para><b>Airside</b> (from 58 on): concourses 16 wide and 9 high every 256 blocks each way (travelators down the north-south
/// ones, flight screens, signs, seats, machines), and between them a <b>superblock</b> 240 square, laid out once from its
/// hash (<see cref="L36PlanOf"/>): a pier (a terminal wing: a letter A-Z, twenty gates numbered within 1-60, each a holdroom
/// of seats facing a runway window with a jet-bridge door, the plane's cabin parked behind it in the solid apron), a duty-free
/// street, a food court, a first-class lounge, the Meeting Place (always the same, as the lore has it) or a back-of-house
/// service maze with vents (out of bounds). Deeper in, whole concourse stretches and superblocks are blacked out; things wait
/// there and nowhere else. Within three cells of the region's rim the walls dissolve into static: the Absolute Limit.</para>
///
/// <para><b>Tiles.</b> <see cref="Tile.Zone"/> is the <see cref="L36Zone"/>; <see cref="Tile.Height"/> on a floor tile is its
/// air, on a wall how high it is dressed. <see cref="Tile.Detail"/>: bits 0-3 the material (<see cref="L36Mat"/>), bit 4 a
/// blackout, bit 5 drawn as static, bit 6 inside the Absolute Limit. <see cref="Tile.Overhead"/> is what hangs under the
/// ceiling (<see cref="Overheads.L36GateSign"/>...), <see cref="Tile.Depth"/> its glyph or text and <see cref="Tile.Roof"/>
/// its part (a shop fascia's: 1-3, 0 none). <see cref="Tile.Pier"/> is the way a prop, a window or a door faces;
/// <see cref="Tile.Stack"/> a prop's kind.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2500-0x25BF are this level's (0x25C0-0x25FF its thresholds').</summary>
    private const ulong SaltL36Shape = 0x2501, SaltL36Plan = 0x2510, SaltL36Light = 0x2512, SaltL36Hall = 0x2513,
        SaltL36Prop = 0x2514, SaltL36Static = 0x2515, SaltL36Belt = 0x2516, SaltL36Gate = 0x2517, SaltL36Heat = 0x2518;

    /// <summary>The airside lattice: a concourse every 256 blocks each way (16 wide), a superblock of 240 between.</summary>
    public const int L36Period = 256, L36Hall = 16, L36Size = 240;

    /// <summary>Where the landside bands lie, in blocks east of the baggage wall.</summary>
    public const int L36BaggageEnd = 24, L36CheckInEnd = 43, L36SecurityEnd = 56, L36Airside = 58;

    public enum L36Zone : byte
    {
        None, Solid, Wall, Baggage, LostFound, CheckIn, Booth, Security, Concourse, Junction, Pier, Holdroom, Bridge, Cabin, Restroom,
        Street, Shop, FoodCourt, Lounge, Meeting, Service, Vent,
    }

    /// <summary>A tile's material (Detail bits 0-3): for floors and for walls.</summary>
    public static class L36Mat
    {
        // Floors
        public const byte Marble = 0, MarbleGrey = 1, MarbleDark = 2, CarpetBlue = 3, CarpetTeal = 4, CarpetRed = 5, CarpetGrey = 6, Concrete = 7,
            TileFloor = 8, BeltRun = 9, BeltStill = 10, Travelator = 11, TravelatorStill = 12;
        // Walls
        public const byte Panel = 0, Plaster = 1, WallTile = 2, Service = 3, Purple = 4, Stainless = 6, Window = 7, GateDoor = 8,
            Flap = 9, Clock = 10, ShopSign = 11, Shutter = 12, CabinWall = 13, Auto = 15,
            // (round 2) a shop's glass front
            Glass = 5,
            // (links) a door under an airplane sign in the baggage wall, the way back of a door in Level 9 or 11
            LandDoor = 14;
    }

    public const byte L36MatMask = 15, L36DarkBit = 16, L36StaticBit = 32, L36LimitBit = 64,
        // (round 3) on a panel wall facing a public hall: a travertine dado to three blocks up
        L36StoneBit = 128;

    /// <summary>The wayfinding signs' glyphs (<c>l36-sign-*</c>), in <see cref="Tile.Depth"/> under <see cref="Overheads.L36Sign"/>.</summary>
    public static readonly string[] L36SignGlyphs = L36MakeSignGlyphs();
    public const byte L36GatesL = 0, L36GatesR = 1, L36SBaggage = 2, L36SExit = 3, L36SMeeting = 4, L36SDutyFree = 5, L36SFood = 6, L36SLounge = 7,
        L36SToilets = 8, L36SSecurity = 9, L36SCheckIn = 10, L36SBlank = 11, L36SBroken = 12,
        // (round 3) the information desk's "i", then the wide signs (four blocks: pictogram, words, arrow), each word with its arrow left and right
        L36SInfo = 13, L36WideFirst = 14;

    /// <summary>(round 3) The wide signs' words, in the order of their glyphs (tools/gen_36_surfaces_signs.py's WIDE).</summary>
    public const int L36WGates = 0, L36WBaggage = 1, L36WExit = 2, L36WMeeting = 3, L36WFood = 4, L36WDutyFree = 5, L36WLounge = 6, L36WToilets = 7,
        L36WSecurity = 8, L36WCheckIn = 9, L36WTransfer = 10, L36WNothing = 11, L36WGoods = 12;

    private static string[] L36MakeSignGlyphs()
    {
        var glyphs = new List<string> { "gatesl", "gatesr", "baggage", "exit", "meeting", "dutyfree", "food", "lounge", "toilets", "security", "checkin", "blank", "broken", "info" };
        foreach (string w in new[] { "gates", "baggage", "exit", "meeting", "food", "dutyfree", "lounge", "toilets", "security", "checkin", "transfer", "nothing", "goods" })
            foreach (char d in "lr")
                for (int i = 0; i < 4; i++) glyphs.Add($"w{w}-{d}-{i}");
        return glyphs.ToArray();
    }

    /// <summary>(round 3) A wide sign's glyph: <paramref name="part"/> 0-3, the leftmost seen from in front first.</summary>
    public static byte L36Wide(int word, bool right, int part) => (byte)(L36WideFirst + (word * 2 + (right ? 1 : 0)) * 4 + part);

    /// <summary>(round 3) The wall pictures (<c>l36-art-*</c>), in <see cref="Tile.Depth"/> under <see cref="Overheads.L36Art"/>: the DEPARTURES and
    /// ARRIVALS boards (4 x 2), eight posters (1 x 2), four menu boards (2 x 1), the WELCOME banner (4 x 1).</summary>
    public static readonly string[] L36ArtKinds = { "dep", "arr", "p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "m0", "m1", "m2", "m3", "welc" };
    public static readonly byte[] L36ArtCols = { 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4 }, L36ArtRows = { 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1 };
    public const byte L36ArtDep = 0, L36ArtArr = 1, L36ArtPoster = 2, L36ArtMenu = 10, L36ArtWelcome = 14;
    /// <summary>(round 3) The posters a column carries (<c>l36-colposter-*</c>): their kinds among <see cref="L36ArtKinds"/>; Roof 255 on a wall tile means "on all its faces".</summary>
    public static readonly byte[] L36ColumnPosters = { 2, 5, 7, 8 };
    public const byte L36OnAllFaces = 255;

    /// <summary>The flight screens' boards (<c>l36-fids-*</c>), in <see cref="Tile.Depth"/> under <see cref="Overheads.L36Fids"/>.</summary>
    public static readonly string[] L36FidsTexts = { "a", "b", "c", "d", "c32", "to11", "to9", "to37", "to3999", "to188", "to10", "arr0", "arr1", "arr2" };
    /// <summary>(round 3) The first of the carousels' screens (three boards).</summary>
    public const byte L36BoardBelt = 11;

    /// <summary>Gate C32's board, and the first of the gates' boards, one for each of <see cref="L36FlightLevels"/> in order.</summary>
    public const byte L36BoardC32 = 4, L36BoardTo = 5;

    /// <summary>The shops (<c>l36-shopsign-*</c>), in <see cref="Tile.Depth"/> of a shop's fascia.</summary>
    public static readonly string[] L36Shops = { "perfume", "fashion", "books", "snacks", "tech", "bags", "cafe", "pharma",
        // (round 3) the concourses' units and the food court's further stalls
        "news", "dutyfree", "exchange", "prayer", "info", "lostfound", "toilets", "shoeshine", "phones", "noodles", "burger", "pizza", "lounge", "foodcourt" };
    public const byte L36ShopPerfume = 0, L36ShopFashion = 1, L36ShopBooks = 2, L36ShopSnacks = 3, L36ShopTech = 4, L36ShopBags = 5, L36ShopCafe = 6,
        L36ShopPharma = 7, L36ShopNews = 8, L36ShopDutyFree = 9, L36ShopExchange = 10, L36ShopPrayer = 11, L36ShopInfo = 12, L36ShopLostFound = 13,
        L36ShopToilets = 14, L36ShopShoeShine = 15, L36ShopPhones = 16, L36ShopNoodles = 17, L36ShopBurger = 18, L36ShopPizza = 19, L36ShopLounge = 20,
        L36ShopFoodCourt = 21;

    public enum L36Kind : byte { Pier, DutyFree, FoodCourt, Lounge, Meeting, Service }

    /// <summary>A gate: its letter and number, its door, the spot in front of it, the plane's aisle, and the ground it covers.</summary>
    public sealed class L36Gate
    {
        public char Letter;
        public int Number, Sx, Sz;
        public int DoorX, DoorZ, FrontX, FrontZ, AisleX, AisleZ;
        /// <summary>The way the door faces (into the holdroom).</summary>
        public ArchPier Facing;
        /// <summary>The holdroom, the jet bridge and the cabin, in world blocks (inclusive).</summary>
        public int X0, Z0, X1, Z1;
        public bool SupportGroup => Letter == 'C' && Number == 32;
        public string Code => Letter + Number.ToString();
        public bool Contains(int x, int z) => x >= X0 && x <= X1 && z >= Z0 && z <= Z1;
        /// <summary>(Flight status pass) The bridge's start just inside the door, and its end where it meets the cabin; set at the end of L36LayGate.</summary>
        public int BridgeX, BridgeZ, BridgeEndX, BridgeEndZ;
    }

    /// <summary>The plan of one superblock in its own coordinates (P, Q); in the world (A east, B south) the same, Q mirrored, then transposed.</summary>
    public sealed class L36Plan
    {
        public int Sx, Sz, X0, Z0;
        public L36Kind Kind;
        public bool Flip, Mirror, Dark;
        public char Letter;
        public readonly Tile[] Tiles = new Tile[L36Size * L36Size];
        public readonly List<L36Gate> Gates = new();

        public (int A, int B) AB(int p, int q)
        {
            if (Mirror) q = L36Size - 1 - q;
            return Flip ? (q, p) : (p, q);
        }
        public ref Tile At(int p, int q)
        {
            var (a, b) = AB(p, q);
            return ref Tiles[a + b * L36Size];
        }
        public ref Tile AtAB(int a, int b) => ref Tiles[a + b * L36Size];
        public ArchPier Dir(ArchPier d)
        {
            if (Mirror) d = d switch { ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, _ => d };
            return !Flip ? d : d switch { ArchPier.North => ArchPier.West, ArchPier.South => ArchPier.East, ArchPier.West => ArchPier.North, _ => ArchPier.South };
        }
        public (int X, int Z) World(int p, int q)
        {
            var (a, b) = AB(p, q);
            return (X0 + a, Z0 + b);
        }
    }

    private PlanCache<L36Plan> l36Plans;

    /// <summary>A superblock's plan (shared: read it, never change it).</summary>
    public L36Plan L36PlanOf(int sx, int sz) =>
        LazyInitializer.EnsureInitialized(ref l36Plans, () => new PlanCache<L36Plan>(24, MakeL36Plan)).Get(sx, sz);

    // ================= Where it is =================

    private double L36Reach => RegionReach * 1.1;
    public int L36CentreX => spawnMacroX - (int)Math.Round(L36Reach * Math.Cos(Math.PI / 8));
    public int L36CentreZ => spawnMacroZ + (int)Math.Round(L36Reach * Math.Sin(Math.PI / 8));
    public int L36Radius => Math.Max(40, spawnMacroX / 50);

    /// <summary>The baggage wall: the region's one straight edge, a north-south line three quarters of the radius west of the centre.</summary>
    public int L36WallX => (L36CentreX - L36Radius * 3 / 4) * MacroSize;
    /// <summary>The centre line (z) every module and the airside lattice count from: booth 0 stands on it.</summary>
    public int L36LineZ => L36CentreZ * MacroSize + MacroSize / 2;
    private int L36AirX => L36WallX + L36Airside;

    private bool InL36(double mx, double mz) => InRoundRegion(mx, mz, L36CentreX, L36CentreZ, L36Radius, SaltL36Shape);

    /// <summary>Arriving: brought in by the conveyor, on a baggage carousel somewhere along the claim hall near the middle.</summary>
    private (int Mx, int Mz) L36ArrivalCell(ulong h) =>
        (MacroOf(L36WallX + 8), L36CentreZ + (int)Math.Round((Hashing.Unit(Hashing.Mix(h)) - 0.5) * L36Radius * 0.6));

    private static bool IsL36ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone == (byte)L36Zone.Baggage && (t.Detail & L36MatMask) is L36Mat.BeltRun or L36Mat.BeltStill;

    private static double L36ArrivalHeight(in Tile t, double stand) => stand;

    /// <summary>Which part of a sign run a block is, counted left to right as seen from in front: <paramref name="index"/> is its place counting along the world axis upward (x for a sign facing north or south, z for east or west).</summary>
    private static byte L36Part(ArchPier facing, int index, int count) => (byte)(facing is ArchPier.North or ArchPier.East ? count - 1 - index : index);

    /// <summary>(round 3) Puts a piece of a wall picture on a wall tile's <paramref name="face"/>: <paramref name="index"/> its place along the world axis
    /// upward (x for a face north or south, z for east or west), <paramref name="bottom"/> the height of its lowest row above the floor.</summary>
    private static void L36WallArt(ref Tile w, ArchPier face, int index, byte kind, int bottom)
    {
        w.Overhead = Overheads.L36Art;
        w.Pier = face;
        w.Depth = kind;
        w.Roof = L36Part(face, index, L36ArtCols[kind]);
        w.Stack = (byte)bottom;
    }

    /// <summary>(round 3) A column's tile carrying a poster on all its faces.</summary>
    private static Tile L36PosterColumn(int which)
    {
        Tile c = L36Solid();
        c.Overhead = Overheads.L36Art;
        c.Depth = L36ColumnPosters[Hashing.Mod(which, L36ColumnPosters.Length)];
        c.Roof = L36OnAllFaces;
        c.Stack = 2;
        return c;
    }

    // ================= Cells =================

    private Edge L36Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L36Wall };

    /// <summary>
    /// Lays out one cell: each tile from <see cref="L36Raw"/>, walls dressed from the tiles round them; near the rim the
    /// Absolute Limit's static, thicker the closer the rim.
    /// </summary>
    private void BuildLevel36(Builder b, int mx, int mz)
    {
        // How far the rim is, in cells (1-3), or 0 when further than that
        int rim = 0;
        for (int r = 1; r <= 3 && rim == 0; r++)
            for (int dz = -r; dz <= r && rim == 0; dz++)
                for (int dx = -r; dx <= r; dx++)
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) == r && LevelAt(mx + dx, mz + dz) != Level36) { rim = r; break; }
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Floor) continue; // the wall round the region (drawn as the Absolute Limit's static)
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                t = L36Raw(gx, gz);
                if (t.Kind == TileKind.Wall) L36Dress(ref t, gx, gz);
                if (rim == 0) continue;
                // (round 2) The very edge, where a hall would run on into the next level: a wall of static, floor to band
                if (rim == 1 && L36AtEdge(mx, mz, lx, lz))
                {
                    t = L36Solid(L36Mat.Panel);
                    t.Zone = 0;
                    continue;
                }
                t.Detail |= L36LimitBit;
                double share = rim == 1 ? 0.85 : rim == 2 ? 0.4 : 0.12;
                if (t.Kind != TileKind.Floor) share = Math.Min(1, share * 1.3);
                if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL36Static)) < share) t.Detail |= L36StaticBit;
                if (t.Kind == TileKind.Floor && rim <= 2 && t.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit)
                    t.Ceiling = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL36Light + 1)) < 0.5 ? CeilingKind.LightFlicker : CeilingKind.LightOff;
            }
    }

    /// <summary>Whether a tile of a cell lies on the cell's side (or corner) that touches a cell of another level.</summary>
    private bool L36AtEdge(int mx, int mz, int lx, int lz)
    {
        int dx = lx == 0 ? -1 : lx == MacroSize - 1 ? 1 : 0, dz = lz == 0 ? -1 : lz == MacroSize - 1 ? 1 : 0;
        if (dx == 0 && dz == 0) return false;
        return dx != 0 && LevelAt(mx + dx, mz) != Level36 || dz != 0 && LevelAt(mx, mz + dz) != Level36
            || dx != 0 && dz != 0 && LevelAt(mx + dx, mz + dz) != Level36;
    }

    private static Tile L36Air(L36Zone zone, int height, byte mat) => new Tile
    {
        Kind = TileKind.Floor, Zone = (byte)zone, Height = (byte)height, Detail = mat, Floor = FloorKind.L36Floor, Ceiling = CeilingKind.L36Ceiling,
        Pattern = WallPattern.L36Wall,
    };

    private static Tile L36Solid(byte mat = L36Mat.Auto, L36Zone zone = L36Zone.Wall) => new Tile
    {
        Kind = TileKind.Wall, Zone = (byte)zone, Detail = mat, Floor = FloorKind.L36Floor, Ceiling = CeilingKind.L36Ceiling, Pattern = WallPattern.L36Wall,
    };

    /// <summary>A tile as laid out, before its wall is dressed: landside and the concourses from arithmetic, the rest from the plans.</summary>
    private Tile L36Raw(int gx, int gz)
    {
        int u = gx - L36WallX;
        if (u < 0) return L36Solid(L36Mat.Panel, L36Zone.Solid);
        if (u < L36Airside) return L36Landside(gx, gz, u);
        int a = Hashing.Mod(gx - L36AirX, L36Period), bb = Hashing.Mod(gz - L36LineZ, L36Period);
        if (a < L36Hall || bb < L36Hall) return L36ConcourseTile(gx, gz, a, bb);
        int sx = Hashing.FloorDiv(gx - L36AirX, L36Period), sz = Hashing.FloorDiv(gz - L36LineZ, L36Period);
        return L36PlanOf(sx, sz).AtAB(a - L36Hall, bb - L36Hall);
    }

    /// <summary>Walls are dressed as high as the tallest air beside them, faced with the material of the most telling zone (unless laid out with one).</summary>
    private void L36Dress(ref Tile t, int gx, int gz)
    {
        int height = 0, rank = -1;
        byte mat = L36Mat.Panel;
        ArchPier cabin = ArchPier.North;
        bool toCabin = false, toHall = false;
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
            {
                if (dx == 0 && dz == 0) continue;
                Tile n = L36Raw(gx + dx, gz + dz);
                if (n.Kind == TileKind.Wall) continue;
                height = Math.Max(height, n.Height);
                // (round 4: the holdrooms and the food courts too, so their walls are not bare panel)
                if ((L36Zone)n.Zone is L36Zone.Concourse or L36Zone.Junction or L36Zone.Pier or L36Zone.Street or L36Zone.Meeting or L36Zone.CheckIn
                    or L36Zone.Baggage or L36Zone.Holdroom or L36Zone.FoodCourt) toHall = true;
                var (r, m) = (L36Zone)n.Zone switch
                {
                    L36Zone.Restroom => (6, L36Mat.WallTile),
                    L36Zone.Booth => (5, L36Mat.Purple),
                    L36Zone.Cabin => (4, L36Mat.CabinWall),
                    L36Zone.Bridge => (3, L36Mat.Stainless),
                    L36Zone.Lounge or L36Zone.Shop or L36Zone.LostFound => (2, L36Mat.Plaster),
                    L36Zone.Service or L36Zone.Vent => (0, L36Mat.Service),
                    _ => (1, L36Mat.Panel),
                };
                if (n.Zone == (byte)L36Zone.Cabin && (dx == 0 || dz == 0))
                {
                    toCabin = true;
                    cabin = dx < 0 ? ArchPier.West : dx > 0 ? ArchPier.East : dz < 0 ? ArchPier.North : ArchPier.South;
                }
                if (r > rank) (rank, mat) = (r, m);
            }
        t.Height = (byte)height;
        if ((t.Detail & L36MatMask) != L36Mat.Auto) return;
        if (mat == L36Mat.CabinWall && !toCabin) mat = L36Mat.Plaster;
        t.Detail = (byte)(t.Detail & ~L36MatMask | mat);
        if (mat == L36Mat.CabinWall) t.Pier = cabin;
        // (round 3) A travertine dado on the panel walls of the public halls
        if (mat == L36Mat.Panel && toHall) t.Detail |= L36StoneBit;
    }

    // ================= Landside =================

    /// <summary>Baggage claim, check-in and security: modules every 32 (16 at security) blocks along the hall from the centre line.</summary>
    private Tile L36Landside(int gx, int gz, int u)
    {
        int line = gz - L36LineZ;
        int k = Hashing.Mod(line, 32), module = Hashing.FloorDiv(line, 32);
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL36Prop));
        if (u == 0)
        {
            // The baggage wall: the carousels come out of it through their flaps; a stopped clock now and then
            Tile w = L36Solid(L36Mat.Panel);
            if (L36IsCarousel(module) && k is 10 or 14) { w.Detail = L36Mat.Flap; w.Pier = ArchPier.East; }
            else if (Hashing.Mod(line, 64) == 40) { w.Detail = L36Mat.Clock; w.Pier = ArchPier.East; w.Stack = (byte)(module & 1); }
            // (links) Every fourth module a door under an airplane sign, out to the city or the Suburbs (locked, but for one
            // somebody has come in by)
            else if (k == 24 && Hashing.Mod(module, 4) == 3 && L36IsCarousel(module)) { w.Detail = L36Mat.LandDoor; w.Pier = ArchPier.East; }
            // (round 4) posters along the baggage wall between the carousels (the Agency's, the ads, the baggage notice)
            else if (k is 4 or 19) L36WallArt(ref w, ArchPier.East, 0, (byte)(L36ArtPoster + Hashing.Mod(module * 5 + k, 8)), 2);
            return w;
        }
        if (u <= L36BaggageEnd) return L36Baggage(gx, gz, u, k, module, r);
        if (u == 25)
        {
            // Wide openings into check-in; an EXIT sign over one in four, leading nowhere but check-in
            if (k is >= 12 and <= 19)
            {
                Tile o = L36Air(L36Zone.Baggage, 7, L36Mat.MarbleGrey);
                // (round 3) Customs on the way out: the green channel and the red, side by side; one opening in four instead the
                // EXIT that leads only into check-in
                o.Overhead = Overheads.L36Sign;
                o.Pier = ArchPier.West;
                if (Hashing.Mod(module, 4) == 1) o.Depth = L36Wide(L36WExit, true, L36Part(ArchPier.West, k - 12 - 2, 4));
                else o.Depth = L36Wide(k < 16 ? L36WNothing : L36WGoods, false, L36Part(ArchPier.West, (k - 12) % 4, 4));
                if (Hashing.Mod(module, 4) == 1 && k is < 14 or > 17) o.Overhead = 0;
                return o;
            }
            Tile w = L36Solid(Hashing.Mod(line, 64) == 40 ? L36Mat.Clock : L36Mat.Auto);
            w.Pier = ArchPier.West;
            w.Stack = 1;
            // (round 3) Departures boards facing check-in, the arrivals board or the WELCOME banner facing the claim hall
            if (k is >= 2 and <= 5 && Hashing.Mod(module, 2) == 0) L36WallArt(ref w, ArchPier.East, k - 2, L36ArtDep, 6);
            else if (k is >= 22 and <= 25) L36WallArt(ref w, ArchPier.West, k - 22, Hashing.Mod(module, 2) == 0 ? L36ArtWelcome : L36ArtArr, Hashing.Mod(module, 2) == 0 ? 5 : 4);
            else if (k is 28 or 9 && w.Detail != L36Mat.Clock) L36WallArt(ref w, ArchPier.West, 0, (byte)(L36ArtPoster + Hashing.Mod(module * 3 + k, 8)), 2);
            return w;
        }
        if (u <= L36CheckInEnd) return L36CheckIn(gx, gz, u, k, module, r);
        if (u == 44)
        {
            if (k is >= 8 and <= 23) return L36Air(L36Zone.Security, 5, L36Mat.MarbleGrey);
            // (round 3) Notices on the security side of the wall: unattended baggage, and the Agency's
            Tile sw = L36Solid();
            if (k is 3 or 28) L36WallArt(ref sw, ArchPier.East, 0, (byte)(L36ArtPoster + (k == 3 ? 6 : 1 + Hashing.Mod(module, 2))), 2);
            return sw;
        }
        int m = Hashing.Mod(line, 16);
        if (u <= L36SecurityEnd) return L36Security(gx, gz, u, m, r);
        // u == 57: through to the airside where the lanes come out
        return m is >= 6 and <= 9 ? L36Air(L36Zone.Security, 5, L36Mat.MarbleGrey) : L36Solid();
    }

    /// <summary>A carousel in this 32-block module (most), or a Lost and Found office (one in twelve).</summary>
    private static bool L36IsCarousel(int module) => Hashing.Mod(module, 12) != 6;

    private Tile L36Baggage(int gx, int gz, int u, int k, int module, double r)
    {
        // (round 2) A column between every two modules, out in the hall
        if (u is 19 or 20 && k is 0 or 31) return L36PosterColumn(k == 31 ? module + 1 : module);
        Tile t = L36Air(L36Zone.Baggage, 7, L36Mat.Marble);
        if (u == 1 || u == L36BaggageEnd || k is 0 or 31) t.Detail = L36Mat.MarbleGrey;
        L36HallLights(ref t, gx, gz, u is 4 or 10 or 16 or 22, k);
        if (!L36IsCarousel(module))
        {
            // A Lost and Found office: shelves of luggage against the wall, a counter, bags heaped about
            if (u <= 10 && k is >= 4 and <= 27)
            {
                if (u == 10 && k is not (>= 14 and <= 17))
                {
                    // (round 3) Its fascia beside the door, facing the hall
                    Tile lw = L36Solid(k is >= 11 and <= 13 ? L36Mat.ShopSign : L36Mat.Plaster);
                    if (k is >= 11 and <= 13) { lw.Pier = ArchPier.East; lw.Depth = L36ShopLostFound; lw.Roof = (byte)(1 + L36Part(ArchPier.East, k - 11, 3)); }
                    return lw;
                }
                t.Zone = (byte)L36Zone.LostFound;
                t.Detail = L36Mat.CarpetGrey;
                // (round 4) an office's ceiling, four high, not the claim hall's seven over a few shelves
                t.Height = 4;
                t.Ceiling = (u - 2) % 4 == 0 && k % 4 == 2 ? CeilingKind.LightOn : CeilingKind.L36Ceiling;
                if (u == 1 && k % 2 == 0) { t.Variant = Props.L36LostFound; t.Pier = ArchPier.East; }
                else if (u == 8 && k is >= 10 and <= 21 && k is not (15 or 16)) { t.Variant = Props.ReceptionDesk; t.Pier = ArchPier.East; }
                else if (u is >= 3 and <= 6 && r < 0.18) { t.Variant = r < 0.12 ? Props.Suitcase : Props.Backpack; t.Pier = (ArchPier)(int)(r * 40 % 4); }
                // (round 4) and heaps of the cases nobody claimed (decor: the ones you can open are the suitcases above)
                else if (u is >= 2 and <= 7 && r < 0.42) { t.Variant = Props.L36Luggage; t.Stack = (byte)((int)(r * 997) % 5); t.Pier = (ArchPier)(int)(r * 7919 % 4); }
                else if (u == 2 && k == 5) t.SupplyBox = true;
            }
            if (u == 12 && k == 15) { t.Overhead = Overheads.L36Sign; t.Depth = L36SBaggage; t.Pier = ArchPier.East; }
            return t;
        }
        // The carousel: a loop of belt round a steel island, out of the wall at row 10 and back in at row 14
        bool running = Hashing.Unit(Hashing.Hash(seed, module, 36, SaltL36Belt)) < 0.3;
        if (k is >= 10 and <= 14 && u <= 14)
        {
            if (k is >= 11 and <= 13 && u <= 13)
            {
                t.Variant = Props.L36CarouselIsland;
                // The carousel's number, hung over the island by the wall
                if (u == 2 && k == 12) { t.Overhead = Overheads.L36GateSign; t.Depth = (byte)(26 + Hashing.Mod(module, 24)); t.Pier = ArchPier.East; }
                return t;
            }
            t.Detail = running ? L36Mat.BeltRun : L36Mat.BeltStill;
            t.Pier = u == 14 ? (k == 14 ? ArchPier.West : ArchPier.South) : k == 10 ? ArchPier.East : ArchPier.West;
            // Bags nobody came for (more on a running one: ten rounds and they go to Lost and Found)
            // (round 3: more of them, as the Fandom page has it, "luggage seemingly abandoned")
            if (r < (running ? 0.26 : 0.12)) { t.Variant = r < 0.07 ? Props.Backpack : Props.Suitcase; t.Stack = (byte)((int)(r * 97) % 4); }
            // (round 4) and more that cannot be opened: hard-shell spinners, duffels, garment bags (decor, no loot; they face the way the belt runs)
            else if (r < (running ? 0.42 : 0.24)) { t.Variant = Props.L36Luggage; t.Stack = (byte)((int)(r * 997) % 4); }
            return t;
        }
        // Round it: benches facing the belt, trolleys, bins, a fountain, abandoned bags; a sign over the middle of the hall
        // (round 4) rows of three gate seats on their beam facing the belt, in place of lone benches; airport trolleys
        if (u == 18 && (k is >= 7 and <= 9 or >= 15 and <= 17))
        {
            t.Variant = Props.L36Seat; t.Pier = ArchPier.West;
            t.Stack = (byte)(r < 0.06 ? 2 : r < 0.1 ? 3 : 1);
        }
        else if (u == 22 && k == 2) t.Variant = Props.L36Bin;
        else if (u is 16 or 17 && k is 4 or 5 && r < 0.6) { t.Variant = Props.L36Trolley; t.Pier = (ArchPier)(int)(r * 40 % 4); }
        else if (u == 23 && k == 24 && r < 0.6) { t.Variant = Props.Cooler; t.Pier = ArchPier.West; }
        else if (u is > 14 and < 24 && r < 0.012) { t.Variant = r < 0.008 ? Props.Suitcase : Props.Backpack; t.Pier = (ArchPier)(int)(r * 997 % 4); }
        if (u is 12 or 13 && k == 24) { t.Overhead = Overheads.L36Sign; t.Depth = u == 12 ? L36SCheckIn : L36SBaggage; t.Pier = ArchPier.West; }
        // (round 3) The carousel's screen at the loop's head: its belt, where its bags came from
        if (u == 15 && k is 12 or 13) { t.Overhead = Overheads.L36Fids; t.Pier = ArchPier.East; t.Depth = (byte)(L36BoardBelt + Hashing.Mod(module, 3)); t.Roof = L36Part(ArchPier.East, k - 12, 2); }
        // (round 3) A bay of nested trolleys by the columns; a customs bench on the red channel's side
        if (u == 21 && k is 28 or 29 or 30 && t.Variant == 0) { t.Variant = Props.L36Trolley; t.Pier = ArchPier.North; }
        if (u == 23 && k is 16 or 17 && Hashing.Mod(module, 4) != 1) { t.Variant = Props.FoldingTable; t.Pier = ArchPier.West; }
        if (u == 20 && k == 28 && Hashing.Mod(module, 5) == 2) t.SupplyBox = true;
        return t;
    }

    /// <summary>Ceiling lights in rows six apart, every four blocks along, each giving light (round 2: the halls lit evenly); a few dead or failing.</summary>
    private void L36HallLights(ref Tile t, int gx, int gz, bool row, int along)
    {
        if (!row || Hashing.Mod(along, 4) != 2) return;
        t.Ceiling = L36Light(gx, gz, true, 0.04, 0.03);
    }

    private CeilingKind L36Light(int gx, int gz, bool emits, double dead, double flicker)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL36Light));
        return r < dead ? CeilingKind.LightOff : r < dead + flicker ? CeilingKind.LightFlicker : emits ? CeilingKind.LightOn : CeilingKind.LightLit;
    }

    private Tile L36CheckIn(int gx, int gz, int u, int k, int module, double r)
    {
        // (round 2) Columns down the middle of the hall, between the islands
        if (u is 34 or 35 && k is 0 or 31) return L36PosterColumn((k == 31 ? module + 1 : module) + 1);
        Tile t = L36Air(L36Zone.CheckIn, 9, L36Mat.Marble);
        if (u == 26 || u == L36CheckInEnd) t.Detail = L36Mat.MarbleGrey;
        L36HallLights(ref t, gx, gz, u is 28 or 34 or 40, k);
        // One module in 32 is a Backrooms Travel Agency booth (booth 0 on the centre line) in place of an island
        if (Hashing.Mod(module, 32) == 0)
        {
            if (u is >= 30 and <= 39 && k is >= 9 and <= 22)
            {
                t.Zone = (byte)L36Zone.Booth;
                if (u == 39 && k is >= 11 and <= 20)
                {
                    // (round 3) Its back a kiosk's purple wall five high, the Agency's posters on the side facing security
                    t.Detail = L36Mat.MarbleDark;
                    t.Height = 5;
                    t.Variant = Props.L36KioskWall;
                    t.Pier = ArchPier.East;
                    t.Stack = (byte)(k is 13 or 15 or 18 ? 1 + L36ArtPoster + (k - 13) / 2 % 3 : 0);
                    return t;
                }
                t.Detail = L36Mat.MarbleDark;
                // (round 2) Under its own purple canopy, five high, the fascia hung from it over the desk
                t.Height = 5;
                if (u == 33 && k is >= 12 and <= 19) { t.Variant = Props.L36Booth; t.Pier = ArchPier.West; }
                if (u == 33 && k is >= 14 and <= 16) { t.Overhead = Overheads.L36BoothSign; t.Roof = L36Part(ArchPier.West, k - 14, 3); t.Pier = ArchPier.West; }
                if (u == 37 && k is 10 or 21) { t.Variant = Props.L36Booth; t.Stack = 1; t.Pier = ArchPier.West; }
                if (u == 31 && k is 10 or 21) t.Variant = Props.L36Planter;
            }
            return t;
        }
        // (round 3) One module in 32, half way between the Agency's booths, an information desk under its "i" in place of an island
        if (Hashing.Mod(module, 32) == 16)
        {
            if (u is 33 or 36 && k is >= 12 and <= 19 || k is 12 or 19 && u is >= 33 and <= 36)
            {
                t.Variant = Props.ReceptionDesk;
                t.Pier = u == 33 ? ArchPier.West : u == 36 ? ArchPier.East : k == 12 ? ArchPier.North : ArchPier.South;
            }
            if (u is 34 or 35 && k is 15 or 16) { t.Overhead = Overheads.L36Sign; t.Depth = L36SInfo; t.Pier = k == 15 ? ArchPier.North : ArchPier.South; }
            // (round 4) an information pylon off each end of the desk, facing the hall
            if (u == 34 && k == 10) { t.Variant = Props.L36InfoPylon; t.Pier = ArchPier.North; }
            if (u == 35 && k == 21) { t.Variant = Props.L36InfoPylon; t.Pier = ArchPier.South; }
            if (u is 34 or 35 && k is 14 or 17) { t.Overhead = Overheads.L36Fids; t.Depth = (byte)Hashing.Mod(module + u, 4); t.Pier = k == 14 ? ArchPier.North : ArchPier.South; t.Roof = L36Part(t.Pier, u - 34, 2); }
            return t;
        }
        // An island: a row of desks back to back over a bag belt, flight screens over it, queue lanes in front of each side
        if (u is >= 29 and <= 40)
        {
            if (k is 15 or 16) { t.Variant = Props.Conveyor; t.Pier = k == 15 ? ArchPier.East : ArchPier.West; t.Stack = (byte)(r < 0.2 ? 1 : 0); return t; }
            if (k is 14 or 17)
            {
                t.Variant = Props.L36Checkin;
                t.Stack = (byte)(u % 2 == 0 ? 0 : 1);
                t.Pier = k == 14 ? ArchPier.North : ArchPier.South;
                if (u is 34 or 35) { t.Overhead = Overheads.L36Fids; t.Depth = (byte)Hashing.Mod(module * 3 + k, 4); t.Roof = L36Part(t.Pier, u - 34, 2); }
                return t;
            }
            // Queue mazes of stanchions: lines along the hall, the way round at alternate ends
            if (k is 8 or 11 or 20 or 23)
            {
                bool gapEast = k is 11 or 20;
                if (gapEast ? u >= 39 : u <= 30) return t;
                t.Variant = Props.L36Stanchion;
                t.Stack = (byte)(u == (gapEast ? 38 : 40) ? 0 : 2);
                return t;
            }
        }
        if (k is 12 or 19 && u is 41 or 42) t.Detail = L36Mat.CarpetBlue;
        if (u == 42 && k == 3 && r < 0.7) t.Variant = Props.L36Bin;
        if (u == 27 && k == 30) { t.Variant = Props.Vending; t.Pier = ArchPier.East; }
        if (u is 33 or 34 && k == 2) { t.Overhead = Overheads.L36Sign; t.Depth = u == 33 ? L36SSecurity : L36GatesR; t.Pier = ArchPier.West; }
        return t;
    }

    private Tile L36Security(int gx, int gz, int u, int m, double r)
    {
        Tile t = L36Air(L36Zone.Security, 5, L36Mat.MarbleGrey);
        if (u is 47 or 53 && Hashing.Mod(m, 4) == 2) t.Ceiling = L36Light(gx, gz, true, 0.15, 0.12);
        if (m is 6 or 7 or 8 && u is >= 49 and <= 55) t.Detail = L36Mat.CarpetGrey;
        // The queue: two lines of stanchions, the way through at alternate ends
        if (u == 46 && m is not (0 or 1)) { t.Variant = Props.L36Stanchion; t.Stack = (byte)(m == 15 ? 0 : 3); return t; }
        if (u == 48 && m is not (14 or 15)) { t.Variant = Props.L36Stanchion; t.Stack = (byte)(m == 13 ? 0 : 3); return t; }
        // A lane: the X-ray belt (bags east), the scanner arch to walk through, the officer's podium, stanchions either side
        if (m == 6 && u is >= 50 and <= 54) { t.Variant = Props.L36Xray; t.Stack = (byte)(u == 52 ? 0 : 1); t.Pier = ArchPier.East; return t; }
        if (m == 7 && u == 52) { t.Variant = Props.L36Scanner; t.Pier = ArchPier.East; return t; }
        if (m == 9 && u == 54) { t.Variant = Props.L36GateDesk; t.Pier = ArchPier.West; return t; }
        if (m is 5 or 10 && u is >= 50 and <= 55) { t.Variant = Props.L36Stanchion; t.Stack = (byte)(u < 55 ? 2 : 0); return t; }
        if (m == 4 && u == 50 && r < 0.6) { t.Variant = Props.L36Trays; return t; }
        if (m is 12 or 13 && u == 51 && r < 0.5) { t.Variant = r < 0.25 ? Props.L36Trays : Props.L36Bin; return t; }
        if (m == 0 && u == 52) { t.Overhead = Overheads.L36Sign; t.Depth = L36SSecurity; t.Pier = ArchPier.West; }
        return t;
    }

    // ================= The concourses =================

    /// <summary>The key of a stretch of concourse between two junctions: north-south (the one at the west of superblock sx, sz) or west-east (at its north).</summary>
    private ulong L36Stretch(int sx, int sz, bool ns, ulong salt) => Hashing.Hash(seed, sx, sz * 2 + (ns ? 1 : 0), salt);

    /// <summary>
    /// A concourse tile (a or b within the hall's 16): marble with a carpet runner, travelators down the north-south ones,
    /// seats and machines along the sides, flight screens, signs; a junction where two cross. A stretch may be blacked out.
    /// </summary>
    private Tile L36ConcourseTile(int gx, int gz, int a, int bb)
    {
        bool ns = a < L36Hall, we = bb < L36Hall;
        int sx = Hashing.FloorDiv(gx - L36AirX, L36Period), sz = Hashing.FloorDiv(gz - L36LineZ, L36Period);
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL36Prop));
        if (ns && we)
        {
            // A junction: dark marble inlay, a cluster of screens over the middle, lit
            Tile j = L36Air(L36Zone.Junction, 9, a is >= 4 and <= 11 && bb is >= 4 and <= 11 ? (a + bb) % 2 == 0 ? L36Mat.MarbleDark : L36Mat.Marble : L36Mat.MarbleGrey);
            j.Ceiling = CeilingKind.L36Coffer;
            if (a % 4 == 2 && bb % 4 == 2) j.Ceiling = CeilingKind.LightOn;
            if (a is 7 or 8 && bb is 7 or 8)
            {
                j.Overhead = Overheads.L36Fids;
                j.Pier = bb == 7 ? ArchPier.North : ArchPier.South;
                j.Depth = (byte)Hashing.Mod(sx * 7 + sz * 3 + (bb == 7 ? 0 : 1), 4);
                j.Roof = L36Part(j.Pier, a - 7, 2);
            }
            return j;
        }
        // c across the hall (0-15), s along it (0-255 from the junction)
        int c = ns ? a : bb, s = ns ? bb : a;
        ulong seg = L36Stretch(sx, sz, ns, SaltL36Hall);
        bool dark = L36DarkStretch(sx, seg);
        Tile t = L36Air(L36Zone.Concourse, 9, c is 0 or 15 ? L36Mat.MarbleGrey : L36Mat.Marble);
        if (dark) t.Detail |= L36DarkBit;
        // Lights in three rows, every four; a dark stretch's dead, those near its ends failing
        if (c is 2 or 8 or 13 && Hashing.Mod(s, 4) == 2)
            t.Ceiling = dark ? (s < 28 || s > 228) ? CeilingKind.LightFlicker : CeilingKind.LightOff : L36Light(gx, gz, true, 0.03, 0.03);
        // The way along: travelators on the north-south halls (one each way, in two runs), a carpet runner otherwise
        if (ns && c is 5 or 6 or 9 or 10 && s is (>= 24 and <= 123) or (>= 132 and <= 231))
        {
            bool second = s >= 132;
            bool still = dark || Hashing.Unit(Hashing.Hash(seed, sx * 2 + (second ? 1 : 0), sz, SaltL36Belt)) < 0.2;
            t.Detail = (byte)(t.Detail & ~L36MatMask | (still ? L36Mat.TravelatorStill : L36Mat.Travelator));
            bool north = c is 5 or 6;
            t.Pier = north ? ArchPier.North : ArchPier.South;
            int start = second ? 132 : 24, end = second ? 231 : 123;
            // Stack bit 0: a comb plate at an end; bit 3: at the end it runs from (it ramps the other way)
            if (s == start || s == end) t.Stack = (byte)(1 | ((north ? s == end : s == start) ? 8 : 0));
            return t;
        }
        if (c is >= 6 and <= 9 && !ns || c is 7 or 8 && ns) t.Detail = (byte)(t.Detail & ~L36MatMask | L36Mat.CarpetBlue);
        // Signs over the hall near each junction: what lies ahead, contradicting each other now and then; one stretch in nine its signs empty
        // (round 3: one wide sign across the middle, its pictogram, words and arrow, in place of four boxes each saying its own thing)
        if (c is >= 6 and <= 9 && s is 30 or 226)
        {
            t.Overhead = Overheads.L36Sign;
            t.Pier = ns ? (s == 30 ? ArchPier.North : ArchPier.South) : (s == 30 ? ArchPier.West : ArchPier.East);
            ulong g = Hashing.Hash(seed, gx, gz, SaltL36Hall + 1);
            if (Hashing.Unit(seg) < 0.11) t.Depth = Hashing.Unit(g) < 0.7 ? L36SBlank : L36SBroken;
            else
            {
                ulong run = Hashing.Hash(seed, sx * 2 + (s == 30 ? 0 : 1), sz * 2 + (ns ? 1 : 0), SaltL36Hall + 2);
                int[] words = { L36WGates, L36WGates, L36WMeeting, L36WFood, L36WDutyFree, L36WLounge, L36WToilets, L36WBaggage, L36WExit, L36WTransfer };
                t.Depth = L36Wide(words[(int)(run % (ulong)words.Length)], (run >> 20 & 1) != 0, L36Part(t.Pier, c - 6, 4));
            }
            return t;
        }
        // Flight screens over the middle, back to back, half way along
        if (c is 7 or 8 && s is 128 or 129)
        {
            t.Overhead = Overheads.L36Fids;
            t.Pier = ns ? (s == 128 ? ArchPier.North : ArchPier.South) : (s == 128 ? ArchPier.West : ArchPier.East);
            t.Depth = (byte)(seg % 4);
            t.Roof = L36Part(t.Pier, c - 7, 2);
        }
        // Along the sides: seats facing in, bins, plants, machines and fountains; now and then a bag left behind
        if (c is 1 or 14)
        {
            ArchPier inward = ns ? (c == 1 ? ArchPier.East : ArchPier.West) : (c == 1 ? ArchPier.South : ArchPier.North);
            int m = Hashing.Mod(s, 24);
            if (m is 8 or 9 or 10) { t.Variant = Props.L36Seat; t.Stack = (byte)(r < 0.1 ? 2 : r < 0.15 ? 3 : (seg & 1) == 0 ? 0 : 1); t.Pier = inward; }
            else if (m == 12) t.Variant = r < 0.5 ? Props.L36Planter : Props.Ficus;
            else if (m == 6) t.Variant = Props.L36Bin;
            else if (m == 18 && Hashing.Mod(s, 72) == 18) { t.Variant = (seg & 2) == 0 ? Props.Vending : Props.SnackVending; t.Pier = inward; }
            else if (m == 18 && Hashing.Mod(s, 72) == 42) { t.Variant = Props.Cooler; t.Pier = inward; }
        }
        else if (c == 2 && Hashing.Mod(s, 96) == 50 && dark) t.SupplyBox = true;
        else if (c is >= 2 and <= 13 && r < 0.0025) { t.Variant = r < 0.0015 ? Props.Suitcase : Props.Backpack; t.Pier = (ArchPier)(int)(r * 4000 % 4); }
        return t;
    }

    /// <summary>Whether a stretch of concourse is blacked out: never near the landside, more often the further airside it is.</summary>
    private static bool L36DarkStretch(int sx, ulong seg) => sx >= 2 && Hashing.Unit(Hashing.Mix(seg)) < Math.Min(0.3, 0.08 + 0.02 * sx);

    // ================= The superblocks =================

    /// <summary>What a superblock holds, from its hash alone.</summary>
    public L36Kind L36KindOf(int sx, int sz)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, sx, sz, SaltL36Plan));
        if (sx == 0) return r < 0.6 ? L36Kind.Pier : r < 0.8 ? L36Kind.DutyFree : r < 0.92 ? L36Kind.FoodCourt : L36Kind.Meeting;
        return r < 0.44 ? L36Kind.Pier : r < 0.58 ? L36Kind.DutyFree : r < 0.69 ? L36Kind.FoodCourt : r < 0.78 ? L36Kind.Lounge
            : r < 0.84 ? L36Kind.Meeting : L36Kind.Service;
    }

    private L36Plan MakeL36Plan(int sx, int sz)
    {
        ulong h = Hashing.Hash(seed, sx, sz, SaltL36Plan + 1);
        var rng = new Rng(Hashing.Mix(h));
        var plan = new L36Plan
        {
            Sx = sx, Sz = sz, X0 = L36AirX + sx * L36Period + L36Hall, Z0 = L36LineZ + sz * L36Period + L36Hall,
            Kind = L36KindOf(sx, sz), Flip = (h & 1) != 0, Mirror = (h >> 1 & 1) != 0,
        };
        if (plan.Kind == L36Kind.Meeting) plan.Flip = plan.Mirror = false;
        for (int i = 0; i < plan.Tiles.Length; i++) plan.Tiles[i] = L36Solid(L36Mat.Auto, L36Zone.Solid);
        // Out here the lights may be out across the whole superblock (half the service mazes; never the Meeting Place)
        double darkChance = plan.Kind == L36Kind.Service ? 0.5 : plan.Kind == L36Kind.Meeting || sx < 2 ? 0 : Math.Min(0.25, 0.05 + 0.015 * sx);
        plan.Dark = rng.Chance(darkChance);
        switch (plan.Kind)
        {
            case L36Kind.Pier: L36LayPier(plan, ref rng); break;
            case L36Kind.DutyFree: L36LayDutyFree(plan, ref rng); break;
            case L36Kind.FoodCourt: L36LayFoodCourt(plan, ref rng); break;
            case L36Kind.Lounge: L36LayLounge(plan, ref rng); break;
            case L36Kind.Meeting: L36LayMeeting(plan); break;
            default: L36LayService(plan, ref rng); break;
        }
        // (round 3) Shops, services and posters along the concourses, in the superblock's edges
        if (plan.Kind != L36Kind.Service) L36LayFrontage(plan);
        if (plan.Dark)
            for (int i = 0; i < plan.Tiles.Length; i++)
            {
                ref Tile t = ref plan.Tiles[i];
                if (t.Kind != TileKind.Floor || t.Zone is (byte)L36Zone.Cabin or (byte)L36Zone.Bridge) continue;
                t.Detail |= L36DarkBit;
                if (t.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit or CeilingKind.LightFlicker)
                    t.Ceiling = ((uint)i * 2654435761u >> 28) < 2 ? CeilingKind.LightFlicker : CeilingKind.LightOff;
            }
        return plan;
    }

    private static void L36Fill(L36Plan plan, int p0, int q0, int p1, int q1, L36Zone zone, int height, byte mat)
    {
        for (int q = Math.Min(q0, q1); q <= Math.Max(q0, q1); q++)
            for (int p = Math.Min(p0, p1); p <= Math.Max(p0, p1); p++) plan.At(p, q) = L36Air(zone, height, mat);
    }

    private static void L36Put(L36Plan plan, int p, int q, ushort prop, ArchPier facing, byte stack = 0)
    {
        ref Tile t = ref plan.At(p, q);
        if (t.Kind != TileKind.Floor) return;
        t.Variant = prop;
        t.Pier = plan.Dir(facing);
        t.Stack = stack;
    }

    private static void L36Hang(L36Plan plan, int p, int q, ushort overhead, ArchPier facing, byte depth, byte roof = 0)
    {
        ref Tile t = ref plan.At(p, q);
        if (t.Kind != TileKind.Floor) return;
        t.Overhead = overhead;
        t.Pier = plan.Dir(facing);
        t.Depth = depth;
        t.Roof = roof;
    }

    /// <summary>Where a block of a run along P (from <paramref name="p0"/>) counts along the world axis upward, as <see cref="L36Part"/> wants it.</summary>
    private static int L36Upward(L36Plan plan, int p0, int q, int index, int count)
    {
        var (x0, z0) = plan.World(p0, q);
        var (x1, z1) = plan.World(p0 + 1, q);
        return x1 > x0 || z1 > z0 ? index : count - 1 - index;
    }

    /// <summary>A pair of screen halves along P (p and p + 1), facing <paramref name="facing"/> in the plan.</summary>
    private static void L36Screens(L36Plan plan, int p, int q, ArchPier facing, byte text)
    {
        ArchPier world = plan.Dir(facing);
        for (int i = 0; i < 2; i++) L36Hang(plan, p + i, q, Overheads.L36Fids, facing, text, L36Part(world, L36Upward(plan, p, q, i, 2), 2));
    }

    private void L36Lights(L36Plan plan, int p0, int q0, int p1, int q1, int step, double dead = 0.04, double flicker = 0.04)
    {
        for (int q = Math.Min(q0, q1) + step / 2; q <= Math.Max(q0, q1); q += step)
            for (int p = Math.Min(p0, p1) + step / 2; p <= Math.Max(p0, p1); p += step)
            {
                ref Tile t = ref plan.At(p, q);
                if (t.Kind != TileKind.Floor || t.Ceiling != CeilingKind.L36Ceiling) continue;
                var (x, z) = plan.World(p, q);
                t.Ceiling = L36Light(x, z, step >= 6 || ((p - p0) / step + (q - q0) / step) % 2 == 0, dead, flicker);
            }
    }

    private static void L36Supply(L36Plan plan, int p, int q)
    {
        ref Tile t = ref plan.At(p, q);
        if (t.Kind == TileKind.Floor && t.Variant == 0 && t.Overhead == 0) t.SupplyBox = true;
    }

    // ---- A pier (a terminal wing) ----

    private void L36LayPier(L36Plan plan, ref Rng rng)
    {
        ulong h = Hashing.Hash(seed, plan.Sx, plan.Sz, SaltL36Gate);
        plan.Letter = (char)('A' + (int)(h % 26));
        int n0 = 20 * (int)(h / 26 % 3);
        bool through = rng.Chance(0.3);
        int end = through ? L36Size - 1 : 231;
        // The pier's corridor, from the concourse out to its window (or on through to the next)
        L36Fill(plan, 0, 114, end, 125, L36Zone.Pier, 7, L36Mat.Marble);
        for (int p = 0; p <= end; p++)
            for (int q = 118; q <= 121; q++) plan.At(p, q).Detail = L36Mat.CarpetBlue;
        if (!through)
            for (int q = 113; q <= 126; q++)
            {
                plan.At(232, q) = L36Solid(L36Mat.Window);
                plan.At(232, q).Pier = plan.Dir(ArchPier.West);
            }
        for (int p = 2; p <= end; p += 4)
            foreach (int q in new[] { 116, 123 })
            {
                var (x, z) = plan.World(p, q);
                plan.At(p, q).Ceiling = L36Light(x, z, true, 0.04, 0.04);
            }
        // (round 3) Moving walkways down the corridor's middle in two runs, out toward the window on one side and back on the
        // other, the benches between them; one run in five stopped (all of them in a blackout)
        foreach (var (p0, p1) in new[] { (20, 98), (132, 210) })
            for (int lane = 0; lane < 2; lane++)
            {
                bool still = plan.Dark || rng.Chance(0.2);
                ArchPier way = lane == 0 ? ArchPier.East : ArchPier.West;
                foreach (int q in lane == 0 ? new[] { 116, 117 } : new[] { 122, 123 })
                    for (int p = p0; p <= p1; p++)
                    {
                        ref Tile t = ref plan.At(p, q);
                        t.Detail = still ? L36Mat.TravelatorStill : L36Mat.Travelator;
                        t.Pier = plan.Dir(way);
                        bool from = lane == 0 ? p == p0 : p == p1;
                        if (p == p0 || p == p1) t.Stack = (byte)(1 | (from ? 8 : 0));
                    }
            }
        // The wing's letter over its mouth, and the way to its gates
        L36Hang(plan, 3, 119, Overheads.L36GateSign, ArchPier.West, (byte)(plan.Letter - 'A'));
        L36Hang(plan, 3, 120, Overheads.L36Sign, ArchPier.West, L36GatesR);
        int supplyGate = rng.Range(0, 19);
        for (int k = 0; k < 10; k++)
            for (int side = 0; side < 2; side++)
            {
                int pa0 = 8 + 22 * k;
                if (k == 4 && side == 0) { L36LayRestroom(plan, pa0, ref rng); continue; }
                L36LayGate(plan, pa0, side, n0 + 2 * k + side + 1, k * 2 + side == supplyGate, ref rng);
            }
        // Benches and planters down the middle of the corridor
        for (int p = 30; p < end - 6; p += 44)
        {
            L36Put(plan, p, 119, Props.L36Planter, ArchPier.North);
            L36Put(plan, p + 1, 119, Props.Bench, ArchPier.North);
            L36Put(plan, p + 1, 120, Props.Bench, ArchPier.South);
            L36Put(plan, p + 2, 120, Props.L36Planter, ArchPier.North);
        }
        L36Screens(plan, 108, 119, ArchPier.West, (byte)(h % 4));
        L36Screens(plan, 108, 120, ArchPier.East, (byte)(h / 4 % 4));
    }

    /// <summary>Plan Q for a gate side: side 0 is north of the corridor (as laid out), side 1 its mirror south of it.</summary>
    private static int L36Q(int side, int q) => side == 0 ? q : L36Size - 1 - q;

    /// <summary>
    /// One gate: its holdroom (seats facing the runway window, the podium, the screen, the sign over its mouth), the jet-bridge door in
    /// the window wall, the bridge, and the plane's cabin parked behind it in the apron (reached only by boarding).
    /// </summary>
    private void L36LayGate(L36Plan plan, int pa0, int side, int number, bool supply, ref Rng rng)
    {
        int Q(int q) => L36Q(side, q);
        ArchPier toWindow = side == 0 ? ArchPier.North : ArchPier.South, fromWindow = side == 0 ? ArchPier.South : ArchPier.North;
        var gate = new L36Gate { Letter = plan.Letter, Number = number, Sx = plan.Sx, Sz = plan.Sz };
        bool c32 = gate.SupportGroup;
        // The holdroom, open along the corridor; partitions between holdrooms most of the way back
        for (int q = 84; q <= 113; q++)
            for (int p = pa0 - 1; p <= pa0 + 21; p++)
                if (!((p == pa0 - 1 || p == pa0 + 21) && q <= 105)) plan.At(p, Q(q)) = L36Air(L36Zone.Holdroom, 6, q >= 112 ? L36Mat.Marble : L36Mat.CarpetTeal);
        // The window wall, the door in it; (round 3) round the door the plane at the gate, painted, nine panels wide
        for (int p = pa0 - 1; p <= pa0 + 21; p++)
        {
            ref Tile w = ref plan.At(p, Q(83));
            w = L36Solid(p == pa0 + 10 ? L36Mat.GateDoor : L36Mat.Window);
            w.Pier = plan.Dir(fromWindow);
            if (p - (pa0 + 6) is >= 0 and <= 8)
            {
                w.Overhead = Overheads.L36Apron;
                w.Roof = L36Part(w.Pier, L36Upward(plan, pa0 + 6, Q(83), p - (pa0 + 6), 9), 9);
            }
        }
        // The bridge and the cabin (cabin pass, 2026-11-13, layout 16: a narrow-body's cabin, the bridge meeting it at the front
        // left door; WorldLayout.Level36.Cabin.cs)
        L36Fill(plan, pa0 + 9, Q(71), pa0 + 11, Q(82), L36Zone.Bridge, 3, L36Mat.CarpetGrey);
        // (round 4) In one bridge in four a wanderer's chalk cross on the wall, just inside the door (the lore: the flights do
        // not come back)
        {
            var (bx, bz) = plan.World(pa0 + 9, Q(81));
            if (Hashing.Unit(Hashing.Hash(seed, bx, bz, SaltL36Prop + 9)) < 0.25) plan.At(pa0 + 9, Q(81)).Chalk = ChalkBits.Make(plan.Dir(ArchPier.West), 2);
        }
        if (Version >= 16) L36LayCabin(plan, pa0, side);
        else
        {
            // (layout 15 and before, the released pre-releases: the old cabin, rows either side of an aisle, the door mid-cabin)
            for (int p = pa0 + 9; p <= pa0 + 11; p++)
                if (p != pa0 + 10) plan.At(p, Q(71)) = L36Solid();
            for (int q = 66; q <= 70; q++)
                for (int p = pa0 + 1; p <= pa0 + 19; p++)
                {
                    ref Tile c = ref plan.At(p, Q(q));
                    c = L36Air(L36Zone.Cabin, 3, L36Mat.CarpetBlue);
                    if (q != 68 && p >= pa0 + 4 && p != pa0 + 10) { c.Variant = Props.L36CabinSeat; c.Pier = plan.Dir(ArchPier.West); }
                    if (q == 68 && (p - pa0) % 4 == 1) c.Ceiling = CeilingKind.LightOn;
                }
        }
        // The seats: rows facing the window, an aisle down the middle; (round 3) in one holdroom in four, coats and bags left
        // over the seats all over (Fandom: "clothing laying all over the chairs, and luggage seemingly abandoned")
        var (gx0, gz0) = plan.World(pa0, Q(84));
        double left = Hashing.Unit(Hashing.Hash(seed, gx0, gz0, SaltL36Prop + 4)) < 0.25 ? 0.3 : 0.08;
        for (int qr = 89; qr <= 101; qr += 4)
            for (int p = pa0 + 2; p <= pa0 + 18; p++)
            {
                if (p == pa0 + 10) continue;
                var (x, z) = plan.World(p, Q(qr));
                double r = Hashing.Unit(Hashing.Hash(seed, x, z, SaltL36Prop));
                byte kind = (byte)(r < left ? 2 : r < left + 0.05 ? 3 : (qr / 4 + p / 9) % 2 == 0 ? 0 : 1);
                L36Put(plan, p, Q(qr), Props.L36Seat, toWindow, kind);
                // Bags left between the rows
                if (r > 0.97) L36Put(plan, p, Q(qr + 1), r > 0.985 ? Props.Suitcase : Props.Backpack, (ArchPier)(int)(r * 1000 % 4));
            }
        // (round 3) The gate counter: two desks and the podium in a row facing the room, the gate's sign hung over it
        L36Put(plan, pa0 + 12, Q(86), Props.L36Checkin, fromWindow, 0);
        L36Put(plan, pa0 + 13, Q(86), Props.L36Checkin, fromWindow, 0);
        L36Put(plan, pa0 + 14, Q(86), Props.L36GateDesk, fromWindow);
        // Charging posts at the ends of the seat rows (the lore's outlets and USB ports)
        for (int qr = 89; qr <= 101; qr += 4)
        {
            L36Put(plan, pa0 + 1, Q(qr), Props.L36Charger, toWindow);
            L36Put(plan, pa0 + 19, Q(qr), Props.L36Charger, toWindow);
        }
        // (links) The gate's screen names where its flight lands, always the same level for the gate
        var (doorX, doorZ) = plan.World(pa0 + 10, Q(83));
        L36Screens(plan, pa0 + 13, Q(84), fromWindow, L36GateBoard(doorX, doorZ, c32));
        // The gate's sign over its mouth: the letter and the number, read left to right from the corridor
        ArchPier signFacing = plan.Dir(fromWindow);
        L36Hang(plan, pa0 + 9 + L36Upward(plan, pa0 + 9, Q(112), L36Part(signFacing, 0, 2), 2), Q(112), Overheads.L36GateSign, fromWindow, (byte)(plan.Letter - 'A'));
        L36Hang(plan, pa0 + 9 + L36Upward(plan, pa0 + 9, Q(112), L36Part(signFacing, 1, 2), 2), Q(112), Overheads.L36GateSign, fromWindow, (byte)(26 + number - 1));
        L36Hang(plan, pa0 + 12 + L36Upward(plan, pa0 + 12, Q(86), L36Part(signFacing, 0, 2), 2), Q(86), Overheads.L36GateSign, fromWindow, (byte)(plan.Letter - 'A'));
        L36Hang(plan, pa0 + 12 + L36Upward(plan, pa0 + 12, Q(86), L36Part(signFacing, 1, 2), 2), Q(86), Overheads.L36GateSign, fromWindow, (byte)(26 + number - 1));
        L36Lights(plan, pa0, Q(84), pa0 + 20, Q(113), 4);
        L36Put(plan, pa0 + 1, Q(108), Props.L36Bin, toWindow);
        if (supply) L36Supply(plan, pa0 + 19, Q(85));
        if (c32)
        {
            // The Gate C32 Support Group: some hundred and fifty waiting for flight 1784XBA8JLP to Level 186. Their bedding,
            // their bags, their lanterns; they are out somewhere just now
            for (int qr = 90; qr <= 102; qr += 4)
                for (int p = pa0 + 2; p <= pa0 + 18; p += 2)
                {
                    double r = rng.NextDouble();
                    ushort prop = r < 0.45 ? Props.SleepingBag : r < 0.6 ? Props.Bedroll : r < 0.75 ? Props.Suitcase : r < 0.85 ? Props.Lantern : (ushort)0;
                    if (prop != 0) L36Put(plan, p, Q(qr), prop, toWindow, 0);
                }
            L36Supply(plan, pa0 + 1, Q(86));
            L36Supply(plan, pa0 + 2, Q(86));
        }
        // Where the gate is, for boarding
        var (dx, dz) = plan.World(pa0 + 10, Q(83));
        var (fx, fz) = plan.World(pa0 + 10, Q(85));
        var (ax, az) = plan.World(pa0 + 10, Q(68));
        var (cx0, cz0) = plan.World(pa0 - 1, Q(65));
        var (cx1, cz1) = plan.World(pa0 + 21, Q(113));
        gate.DoorX = dx; gate.DoorZ = dz; gate.FrontX = fx; gate.FrontZ = fz; gate.AisleX = ax; gate.AisleZ = az;
        gate.Facing = plan.Dir(fromWindow);
        gate.X0 = Math.Min(cx0, cx1); gate.X1 = Math.Max(cx0, cx1); gate.Z0 = Math.Min(cz0, cz1); gate.Z1 = Math.Max(cz0, cz1);
        (gate.BridgeX, gate.BridgeZ) = plan.World(pa0 + 10, Q(82));
        (gate.BridgeEndX, gate.BridgeEndZ) = plan.World(pa0 + 10, Q(71));
        plan.Gates.Add(gate);
    }

    /// <summary>A pair of restrooms in place of one gate: tiled, toilets along the back, basins by the door.</summary>
    private void L36LayRestroom(L36Plan plan, int pa0, ref Rng rng)
    {
        for (int q = 106; q <= 113; q++)
            for (int p = pa0 - 1; p <= pa0 + 21; p++) plan.At(p, q) = L36Air(L36Zone.Holdroom, 6, q >= 112 ? L36Mat.Marble : L36Mat.CarpetTeal);
        L36Lights(plan, pa0, 106, pa0 + 20, 113, 4);
        foreach (var (p0, p1) in new[] { (pa0, pa0 + 9), (pa0 + 11, pa0 + 20) })
        {
            L36Fill(plan, p0, 90, p1, 104, L36Zone.Restroom, 4, L36Mat.TileFloor);
            plan.At((p0 + p1) / 2, 105) = L36Air(L36Zone.Restroom, 4, L36Mat.TileFloor);
            plan.At((p0 + p1) / 2 + 1, 105) = L36Air(L36Zone.Restroom, 4, L36Mat.TileFloor);
            // (round 3) A row of cubicles, partitions and doors, in place of toilets in the open
            for (int p = p0; p <= p1; p++) L36Put(plan, p, 90, Props.L36Stall, ArchPier.South);
            for (int p = p0 + 1; p <= p1 - 1; p += 3) L36Put(plan, p, 101, Props.L36Sink, ArchPier.North);
            L36Lights(plan, p0, 90, p1, 104, 4, 0.08, 0.06);
            if (rng.Chance(0.5)) L36Put(plan, p0 + 2, 103, Props.WetFloorSign, ArchPier.South);
        }
        L36Hang(plan, pa0 + 10, 112, Overheads.L36Sign, ArchPier.South, L36SToilets);
        L36Put(plan, pa0 + 2, 107, Props.Cooler, ArchPier.South);
        L36Put(plan, pa0 + 18, 107, Props.Vending, ArchPier.South);
    }

    // ---- Duty free ----

    private void L36LayDutyFree(L36Plan plan, ref Rng rng)
    {
        L36Fill(plan, 0, 108, L36Size - 1, 131, L36Zone.Street, 8, L36Mat.Marble);
        for (int p = 0; p < L36Size; p++)
            foreach (int q in new[] { 108, 131 }) plan.At(p, q).Detail = L36Mat.MarbleGrey;
        L36Lights(plan, 0, 108, L36Size - 1, 131, 6, 0.03, 0.03);
        // (round 3) A run of skylights down the street's middle
        for (int p = 0; p < L36Size; p++)
            for (int q = 118; q <= 121; q++)
                if (plan.At(p, q).Ceiling == CeilingKind.L36Ceiling) plan.At(p, q).Ceiling = CeilingKind.L36Skylight;
        for (int p = 10; p < L36Size - 10; p += 16)
        {
            L36Put(plan, p, 119, Props.L36Planter, ArchPier.North);
            L36Put(plan, p, 120, Props.L36Planter, ArchPier.North);
            L36Put(plan, p + 1, 119, Props.Bench, ArchPier.North);
            L36Put(plan, p + 1, 120, Props.Bench, ArchPier.South);
            L36Put(plan, p - 1, 119, Props.Bench, ArchPier.North);
            L36Put(plan, p - 1, 120, Props.Bench, ArchPier.South);
        }
        L36Hang(plan, 3, 119, Overheads.L36Sign, ArchPier.West, L36SDutyFree);
        L36Hang(plan, L36Size - 4, 120, Overheads.L36Sign, ArchPier.East, L36SDutyFree);
        L36Screens(plan, 117, 119, ArchPier.West, (byte)rng.Range(0, 3));
        L36Screens(plan, 117, 120, ArchPier.East, (byte)rng.Range(0, 3));
        for (int j = 0; j < 10; j++)
            for (int side = 0; side < 2; side++) L36LayShop(plan, 2 + 23 * j, side, ref rng);
    }

    /// <summary>One shop on the duty-free street: its front onto the street (open, or shuttered), its fascia, its stock.</summary>
    private void L36LayShop(L36Plan plan, int p0, int side, ref Rng rng)
    {
        int shop = rng.Range(0, L36Shops.Length - 1);
        bool closed = rng.Chance(0.35);
        int Q(int q) => L36Q(side, q);
        ArchPier toStreet = side == 0 ? ArchPier.South : ArchPier.North, toBack = side == 0 ? ArchPier.North : ArchPier.South;
        int p1 = p0 + 20;
        L36Fill(plan, p0, Q(80), p1, Q(106), L36Zone.Shop, 5, shop is 0 or 4 ? L36Mat.MarbleGrey : shop == 6 ? L36Mat.CarpetRed : L36Mat.CarpetGrey);
        if (!closed) L36Lights(plan, p0, Q(80), p1, Q(106), 4, 0.06, 0.05);
        // The front: wall either side, the way in (or the shutter) in the middle, the fascia over its middle three
        ArchPier front = plan.Dir(toStreet);
        for (int p = p0 - 1; p <= p1 + 1; p++)
        {
            ref Tile f = ref plan.At(p, Q(107));
            bool door = p >= p0 + 6 && p <= p0 + 14;
            f = door && !closed ? L36Air(L36Zone.Shop, 5, L36Mat.Marble) : L36Solid(door ? L36Mat.Shutter : p >= p0 + 1 && p <= p1 - 1 ? L36Mat.Glass : L36Mat.Auto);
            f.Pier = front;
            if (door && p >= p0 + 9 && p <= p0 + 11)
            {
                f.Depth = (byte)shop;
                f.Roof = (byte)(1 + L36Part(front, L36Upward(plan, p0 + 9, Q(107), p - p0 - 9, 3), 3));
            }
        }
        // The stock (a shuttered shop's still on its shelves)
        for (int q = 84; q <= 102; q += 4)
            for (int p = p0 + 2; p <= p1 - 2; p++)
            {
                if (p == p0 + 10) continue;
                double r = rng.NextDouble();
                switch (shop)
                {
                    case 0: if (p % 3 != 0) L36Put(plan, p, Q(q), Props.L36Perfume, p % 2 == 0 ? toStreet : toBack); break;
                    case 1: if (p % 2 == 0) L36Put(plan, p, Q(q), Props.ClothesRack, toStreet); break;
                    case 2: if (q % 8 == 4 || p % 4 == 0) L36Put(plan, p, Q(q), Props.HotelBookshelf, toStreet); break;
                    case 3: L36Put(plan, p, Q(q), Props.SnackShelf, q % 8 == 4 ? toStreet : toBack); break;
                    case 4: if (p % 3 != 1) L36Put(plan, p, Q(q), r < 0.5 ? Props.ConsoleTable : Props.Tv, toStreet); break;
                    case 5: if (r < 0.7) L36Put(plan, p, Q(q), r < 0.5 ? Props.Suitcase : Props.Backpack, toStreet); break;
                    case 6:
                        if (p % 4 == 0 && q < 100)
                        {
                            L36Put(plan, p, Q(q), Props.L36MealTable, toStreet, (byte)(r < 0.3 ? 0 : r < 0.55 ? 1 : r < 0.7 ? 2 : 3));
                            L36Put(plan, p - 1, Q(q), Props.CafeChair, ArchPier.East);
                            L36Put(plan, p + 1, Q(q), Props.CafeChair, ArchPier.West);
                        }
                        break;
                    default: if (p % 2 == 0) L36Put(plan, p, Q(q), p % 4 == 0 ? Props.MedCabinet : Props.Shelf, toStreet); break;
                }
            }
        // Along the back wall
        for (int p = p0 + 1; p <= p1 - 1; p++)
        {
            ushort back = shop switch
            {
                3 => p % 2 == 0 ? Props.DrinkFridge : Props.SnackVending,
                6 => p % 3 == 0 ? Props.Stove : p % 3 == 1 ? Props.SnackCounter : Props.Fryer,
                2 => Props.HotelBookshelf,
                _ => p % 2 == 0 ? Props.Shelf : (ushort)0,
            };
            if (back != 0) L36Put(plan, p, Q(80), back, toStreet, 0);
        }
        // The till by the door
        L36Put(plan, p0 + 3, Q(104), Props.SnackCounter, toStreet, 1);
        L36Put(plan, p0 + 4, Q(104), Props.SnackCounter, toStreet, 0);
        if (!closed && rng.Chance(0.12)) L36Supply(plan, p1 - 1, Q(82));
    }

    // ---- The food court ----

    private void L36LayFoodCourt(L36Plan plan, ref Rng rng)
    {
        // The ways in, from all four concourses
        L36Fill(plan, 0, 114, 59, 125, L36Zone.Concourse, 7, L36Mat.Marble);
        // (round 3) FOOD COURT over the west way in (the way the signs point), as a shop's fascia
        L36MouthFascia(plan, 0, 118, L36ShopFoodCourt, ArchPier.West);
        L36Fill(plan, 180, 114, L36Size - 1, 125, L36Zone.Concourse, 7, L36Mat.Marble);
        L36Fill(plan, 114, 0, 125, 59, L36Zone.Concourse, 7, L36Mat.Marble);
        L36Fill(plan, 114, 180, 125, L36Size - 1, L36Zone.Concourse, 7, L36Mat.Marble);
        L36Lights(plan, 0, 114, 59, 125, 6);
        L36Lights(plan, 180, 114, L36Size - 1, 125, 6);
        L36Lights(plan, 114, 0, 125, 59, 6);
        L36Lights(plan, 114, 180, 125, L36Size - 1, 6);
        L36Hang(plan, 3, 119, Overheads.L36Sign, ArchPier.West, L36SFood);
        L36Hang(plan, 119, 3, Overheads.L36Sign, ArchPier.North, L36SFood);
        // The hall, 10 high
        L36Fill(plan, 60, 60, 179, 179, L36Zone.FoodCourt, 10, L36Mat.Marble);
        L36Lights(plan, 60, 60, 179, 179, 6, 0.05, 0.05);
        // (round 3) Skylights in bands across the hall
        for (int q = 64; q <= 175; q++)
            for (int p = 64; p <= 175; p++)
                if (Hashing.Mod(q - 60, 30) is 14 or 15 && plan.At(p, q).Ceiling == CeilingKind.L36Ceiling) plan.At(p, q).Ceiling = CeilingKind.L36Skylight;
        // Stalls round the walls (not where the ways come in): a counter facing in, the kitchen behind, the stall's fascia on the wall
        for (int i = 0; i < 4; i++)
            for (int along = 62; along <= 170; along += 12)
            {
                if (along is >= 104 and <= 125) continue;
                // a cafe or a snack bar; (round 3) noodles, burgers or pizza, each with its menu boards either side of its fascia
                byte stall = (byte)(rng.Chance(0.5) ? 6 : 3);
                double kindR = Hashing.Unit(Hashing.Hash(seed, plan.Sx * 64 + i, plan.Sz * 64 + along, SaltL36Prop + 1));
                if (kindR < 0.45) stall = kindR < 0.15 ? L36ShopNoodles : kindR < 0.3 ? L36ShopBurger : L36ShopPizza;
                byte menuKind = (byte)(L36ArtMenu + (stall == L36ShopCafe ? 0 : stall == L36ShopNoodles ? 1 : stall == L36ShopPizza ? 3 : 2));
                ArchPier inward = i switch { 0 => ArchPier.South, 1 => ArchPier.North, 2 => ArchPier.East, _ => ArchPier.West };
                for (int d = 0; d < 9; d++)
                {
                    int s = along + d;
                    (int P, int Q) At(int depth) => i switch
                    {
                        0 => (s, 60 + depth), 1 => (s, 179 - depth), 2 => (60 + depth, s), _ => (179 - depth, s),
                    };
                    var counter = At(3);
                    bool cafe = stall == L36ShopCafe;
                    // (round 4) a cafe's counter: pastry cases and the till; its kitchen espresso counters; stools along the counters
                    if (cafe && d is 2 or 3 or 5 or 6) L36Put(plan, counter.P, counter.Q, Props.L36Pastry, inward);
                    else if (d == 4) L36Put(plan, counter.P, counter.Q, Props.L36Till, inward);
                    else L36Put(plan, counter.P, counter.Q, Props.SnackCounter, inward, (byte)(d % 3 == 0 ? 2 : 0));
                    if (d is 1 or 3 or 5 or 7 && Hashing.Unit(Hashing.Hash(seed, counter.P + plan.Sx * 256, counter.Q + plan.Sz * 256, SaltL36Prop + 7)) < 0.8)
                    {
                        var seat = At(4);
                        L36Put(plan, seat.P, seat.Q, Props.L36Stool, inward);
                    }
                    var kitchen = At(0);
                    L36Put(plan, kitchen.P, kitchen.Q, cafe ? (d % 3 == 0 ? Props.L36Coffee : Props.KitchenCounter)
                        : d % 3 == 0 ? Props.Stove : d % 3 == 1 ? Props.Fryer : Props.KitchenCounter, inward);
                    if (d is 1 or 2 or 6 or 7)
                    {
                        // (round 3) The menu boards, two blocks each, at head height over the kitchen
                        var mw = At(-1);
                        ref Tile m = ref plan.At(mw.P, mw.Q);
                        m = L36Solid();
                        int mi = d is 1 or 6 ? 0 : 1, m0 = d < 4 ? along + 1 : along + 6;
                        int upwardM = i < 2 ? L36Upward(plan, m0, mw.Q, mi, 2) : L36UpwardQ(plan, mw.P, m0, mi, 2);
                        L36WallArt(ref m, plan.Dir(inward), upwardM, menuKind, 3);
                        m.Roof = L36Part(m.Pier, upwardM, 2);
                    }
                    if (d is < 3 or > 5) continue;
                    var wall = At(-1);
                    ref Tile w = ref plan.At(wall.P, wall.Q);
                    w = L36Solid(L36Mat.ShopSign);
                    w.Pier = plan.Dir(inward);
                    w.Depth = stall;
                    // (the run goes along P for the north and south walls, along Q for the others)
                    int index = d - 3;
                    int upward = i < 2 ? L36Upward(plan, along + 3, wall.Q, index, 3) : L36UpwardQ(plan, wall.P, along + 3, index, 3);
                    w.Roof = (byte)(1 + L36Part(w.Pier, upward, 3));
                }
            }
        // The tables: what was left on them (much of it spoiled), chairs round each
        for (int q = 72; q <= 167; q += 6)
            for (int p = 72; p <= 167; p += 6)
            {
                if (p is >= 112 and <= 127 && q is >= 112 and <= 127) continue;
                double r = rng.NextDouble();
                L36Put(plan, p, q, Props.L36MealTable, ArchPier.North, (byte)(r < 0.3 ? 0 : r < 0.55 ? 1 : r < 0.7 ? 2 : 3));
                L36Put(plan, p - 1, q, Props.CafeChair, ArchPier.East);
                L36Put(plan, p + 1, q, Props.CafeChair, ArchPier.West);
                if (r > 0.5) L36Put(plan, p, q - 1, Props.CafeChair, ArchPier.South);
                if (r > 0.8) L36Put(plan, p, q + 1, Props.CafeChair, ArchPier.North);
            }
        // In the middle: bins, machines, screens
        L36Put(plan, 116, 116, Props.L36Bin, ArchPier.North);
        L36Put(plan, 123, 123, Props.L36Bin, ArchPier.North);
        L36Put(plan, 119, 116, Props.Vending, ArchPier.North);
        L36Put(plan, 120, 116, Props.SnackVending, ArchPier.North);
        L36Put(plan, 119, 123, Props.DrinkFridge, ArchPier.South);
        L36Put(plan, 120, 123, Props.Cooler, ArchPier.South);
        L36Screens(plan, 119, 119, ArchPier.North, (byte)rng.Range(0, 3));
        L36Screens(plan, 119, 120, ArchPier.South, (byte)rng.Range(0, 3));
        if (rng.Chance(0.5)) L36Supply(plan, 64, 66 + rng.Range(0, 3));
        // (round 2) Columns holding up the hall, clear of the tables
        foreach (int cq in new[] { 87, 119, 151 })
            foreach (int cp in new[] { 87, 119, 151 })
            {
                if (cp == 119 && cq == 119) continue;
                for (int dq = 0; dq < 2; dq++)
                    for (int dp = 0; dp < 2; dp++) plan.At(cp + dp, cq + dq) = L36PosterColumn(cp + cq);   // (round 4: clad and postered)
            }
    }

    /// <summary>(round 3) A fascia over a way in at the plan's edge: three tiles along Q from <paramref name="q0"/>, made a shop's doorway so the
    /// fascia shows two over their air, facing <paramref name="facing"/> (plan).</summary>
    private static void L36MouthFascia(L36Plan plan, int p, int q0, byte shop, ArchPier facing)
    {
        ArchPier world = plan.Dir(facing);
        for (int i = 0; i < 3; i++)
        {
            ref Tile t = ref plan.At(p, q0 + i);
            if (t.Kind != TileKind.Floor) continue;
            t.Zone = (byte)L36Zone.Shop;
            t.Depth = shop;
            t.Pier = world;
            t.Roof = (byte)(1 + L36Part(world, L36UpwardQ(plan, p, q0, i, 3), 3));
        }
    }

    /// <summary>As <see cref="L36Upward"/>, for a run along Q.</summary>
    private static int L36UpwardQ(L36Plan plan, int p, int q0, int index, int count)
    {
        var (x0, z0) = plan.World(p, q0);
        var (x1, z1) = plan.World(p, q0 + 1);
        return x1 > x0 || z1 > z0 ? index : count - 1 - index;
    }

    // ---- The first-class lounge ----

    private void L36LayLounge(L36Plan plan, ref Rng rng)
    {
        L36Fill(plan, 0, 116, 69, 123, L36Zone.Lounge, 5, L36Mat.CarpetGrey);
        // (round 3) Its name over the way in from the concourse
        L36MouthFascia(plan, 0, 118, L36ShopLounge, ArchPier.West);
        L36Lights(plan, 0, 116, 69, 123, 4);
        L36Hang(plan, 3, 119, Overheads.L36Sign, ArchPier.West, L36SLounge);
        L36Fill(plan, 70, 90, 169, 149, L36Zone.Lounge, 5, L36Mat.CarpetRed);
        // The showers, and a store room: a courier group's stockpile, hidden away
        L36Fill(plan, 150, 90, 169, 105, L36Zone.Restroom, 5, L36Mat.TileFloor);
        L36Fill(plan, 150, 134, 169, 149, L36Zone.Service, 4, L36Mat.Concrete);
        for (int p = 150; p <= 169; p++)
        {
            if (p is not (155 or 156)) plan.At(p, 106) = L36Solid();
            if (p != 160) plan.At(p, 133) = L36Solid();
        }
        for (int q = 90; q <= 149; q++)
            if (q is <= 106 or >= 133) plan.At(149, q) = L36Solid();
        L36Lights(plan, 70, 90, 169, 149, 4, 0.03, 0.02);
        L36Lights(plan, 150, 134, 169, 149, 6, 0.3, 0.2);
        for (int q = 117; q <= 122; q++)
            if (q is not (119 or 120)) L36Put(plan, 73, q, Props.ReceptionDesk, ArchPier.West);
        // Sofas facing each other over coffee tables
        for (int q = 96; q <= 136; q += 8)
            for (int p = 82; p <= 140; p += 10)
            {
                L36Put(plan, p, q, Props.L36Couch, ArchPier.South, 0);
                L36Put(plan, p + 1, q, Props.L36Couch, ArchPier.South, 1);
                L36Put(plan, p, q + 1, Props.CoffeeTable, ArchPier.North);
                L36Put(plan, p + 1, q + 2, Props.L36Couch, ArchPier.North, 0);
                L36Put(plan, p, q + 2, Props.L36Couch, ArchPier.North, 1);
                if (rng.Chance(0.25)) L36Put(plan, p + 3, q + 1, Props.FloorLamp, ArchPier.North);
            }
        // Bookshelves along one wall, the buffet along the other, tables before it
        for (int p = 72; p <= 146; p++)
        {
            if (p % 3 != 0) L36Put(plan, p, 90, Props.HotelBookshelf, ArchPier.South);
            ushort buffet = p % 5 == 0 ? Props.Fridge : p % 5 == 1 ? Props.DrinkFridge : Props.KitchenCounter;
            if (p is >= 90 and <= 140) L36Put(plan, p, 149, buffet, ArchPier.North, (byte)(p % 7 == 0 ? 2 : 0));
        }
        for (int p = 92; p <= 138; p += 4) L36Put(plan, p, 145, Props.L36MealTable, ArchPier.North, (byte)rng.Range(0, 3));
        for (int p = 151; p <= 168; p += 2) L36Put(plan, p, 90, Props.Toilet, ArchPier.South);
        for (int p = 152; p <= 168; p += 4) L36Put(plan, p, 100, Props.L36Sink, ArchPier.North);
        int boxes = rng.Range(2, 4);
        for (int i = 0; i < boxes; i++) L36Supply(plan, 152 + 4 * i, 147);
        for (int p = 151; p <= 168; p += 3) L36Put(plan, p, 137, Props.CardboardBoxes, ArchPier.North);
    }

    // ---- The Meeting Place (always the same: the lore's forty-seven positions are one place) ----

    /// <summary>Where the Travel Planner stands in a Meeting Place, in the plan's own coordinates.</summary>
    private const int L36PlannerP = 120, L36PlannerQ = 135;

    private void L36LayMeeting(L36Plan plan)
    {
        L36Fill(plan, 0, 114, L36Size - 1, 125, L36Zone.Meeting, 8, L36Mat.Marble);
        L36Fill(plan, 114, 0, 125, L36Size - 1, L36Zone.Meeting, 8, L36Mat.Marble);
        L36Lights(plan, 0, 114, L36Size - 1, 125, 6);
        L36Lights(plan, 114, 0, 125, L36Size - 1, 6);
        for (int q = 0; q < L36Size; q++)
            for (int p = 0; p < L36Size; p++)
            {
                double dx = p - 119.5, dz = q - 119.5, d = Math.Sqrt(dx * dx + dz * dz);
                if (d > 44) continue;
                byte mat = d is > 19 and < 21 or > 31 and < 33 ? L36Mat.MarbleDark : d is > 7 and < 9 ? L36Mat.MarbleGrey : L36Mat.Marble;
                ref Tile t = ref plan.At(p, q);
                t = L36Air(L36Zone.Meeting, 14, mat);
                // A grid of lights over the whole atrium (it is 14 high), rings of panels between
                // (round 3) coffered, a skylight over the marker
                t.Ceiling = d < 9 ? CeilingKind.L36Skylight : CeilingKind.L36Coffer;
                if (p % 4 == 2 && q % 4 == 2 && d >= 9) t.Ceiling = CeilingKind.LightOn;
                // (round 4) lights among the skylight's panes too: the floor round the marker was dark
                else if (p % 4 == 0 && q % 4 == 0 && d is >= 2.5 and < 9) t.Ceiling = CeilingKind.LightOn;
                else if ((d is > 13.5 and < 14.5 || d is > 25.5 and < 26.5 || d is > 37.5 and < 38.5) && (p + q) % 3 == 0) t.Ceiling = CeilingKind.LightLit;
            }
        // (round 2) A ring of eight columns round the atrium, between the planters and the outer lights
        for (int i = 0; i < 8; i++)
        {
            double ang = i * Math.PI / 4 + Math.PI / 8;
            int cp = (int)Math.Round(119.5 + Math.Cos(ang) * 31 - 0.5), cq = (int)Math.Round(119.5 + Math.Sin(ang) * 31 - 0.5);
            for (int dq = 0; dq < 2; dq++)
                for (int dp = 0; dp < 2; dp++) plan.At(cp + dp, cq + dq) = L36PosterColumn(i);
        }
        // The meeting point in the middle (round 3: the sign every airport has, a lit cube two blocks on a side on a post, the
        // pictogram and MEETING POINT on its four faces; Stack the quarter of it a block holds, 0 north-west, 1 north-east,
        // 2 south-west, 3 south-east: this plan is never turned)
        for (int q = 119; q <= 120; q++)
            for (int p = 119; p <= 120; p++)
            {
                plan.At(p, q).Variant = Props.L36MeetingPoint;
                plan.At(p, q).Stack = (byte)((q - 119) * 2 + (p - 119));
            }
        // Benches round it facing in, planters further out
        for (int i = 0; i < 16; i++)
        {
            double ang = i * Math.PI / 8;
            int p = (int)Math.Round(119.5 + Math.Cos(ang) * 11), q = (int)Math.Round(119.5 + Math.Sin(ang) * 11);
            ArchPier inward = Math.Abs(Math.Cos(ang)) > Math.Abs(Math.Sin(ang)) ? (Math.Cos(ang) > 0 ? ArchPier.West : ArchPier.East) : (Math.Sin(ang) > 0 ? ArchPier.North : ArchPier.South);
            L36Put(plan, p, q, Props.Bench, inward);
            int pp = (int)Math.Round(119.5 + Math.Cos(ang + 0.2) * 23), qq = (int)Math.Round(119.5 + Math.Sin(ang + 0.2) * 23);
            L36Put(plan, pp, qq, i % 2 == 0 ? Props.L36Planter : Props.Ficus, ArchPier.North);
        }
        // The Travel Agency's booth to the south of it (round 2: a purple kiosk, its canopy five high, open to the north): the
        // desk, the Planner behind it, the fascia hung over the desk, the screens over the Planner
        // (round 3: its walls a kiosk's, five high with open air over them, not wall columns up to the atrium's ceiling; the
        // Agency's posters on the outside)
        L36Fill(plan, 114, 131, 126, 138, L36Zone.Booth, 5, L36Mat.MarbleDark);
        for (int p = 114; p <= 126; p++) L36Put(plan, p, 138, Props.L36KioskWall, ArchPier.South, (byte)(p is 117 or 120 or 123 ? 1 + L36ArtPoster + (p - 117) / 3 : 0));
        for (int q = 131; q <= 137; q++)
        {
            L36Put(plan, 114, q, Props.L36KioskWall, ArchPier.West, (byte)(q == 134 ? 1 + L36ArtPoster : 0));
            L36Put(plan, 126, q, Props.L36KioskWall, ArchPier.East, (byte)(q == 134 ? 1 + L36ArtPoster + 1 : 0));
        }
        L36Lights(plan, 115, 131, 125, 137, 4);
        L36Screens(plan, 119, 137, ArchPier.North, 3);
        for (int p = 118; p <= 122; p++) L36Put(plan, p, 133, Props.L36Booth, ArchPier.North, 0);
        L36Put(plan, 117, 135, Props.L36Booth, ArchPier.North, 1);
        L36Put(plan, 123, 135, Props.L36Booth, ArchPier.North, 1);
        for (int p = 119; p <= 121; p++) L36Hang(plan, p, 133, Overheads.L36BoothSign, ArchPier.North, 0, L36Part(ArchPier.North, p - 119, 3));
        foreach (var (p, q, f) in new[] { (3, 119, ArchPier.West), (L36Size - 4, 120, ArchPier.East), (119, 3, ArchPier.North), (120, L36Size - 4, ArchPier.South) })
            L36Hang(plan, p, q, Overheads.L36Sign, f, L36SMeeting);
    }

    // ---- (round 3) The concourses' frontage ----

    /// <summary>
    /// Units along every edge of a superblock (where the plan left it solid), their fronts on the concourse: shops behind glass
    /// with their fascias (news, duty free, the cafe, the pharmacy, a bureau de change...), a services alcove (payphones, cash
    /// machines, a drinking fountain), restrooms, a prayer room, an information desk, a shoe-shine stand, or a stretch of wall
    /// with a departures board or posters; a poster on the wall between each two.
    /// </summary>
    private void L36LayFrontage(L36Plan plan)
    {
        const int Deep = 11;
        for (int edge = 0; edge < 4; edge++)
        {
            (int P, int Q) At(int s, int d) => edge switch { 0 => (d, s), 1 => (L36Size - 1 - d, s), 2 => (s, d), _ => (s, L36Size - 1 - d) };
            ArchPier outward = edge switch { 0 => ArchPier.West, 1 => ArchPier.East, 2 => ArchPier.North, _ => ArchPier.South };
            ArchPier inward = Opposite(outward);
            // Where a run along the edge counts upward in the world, for fascias and pictures
            int Up(int s0, int index, int count)
            {
                var a0 = At(s0, 0);
                var a1 = At(s0 + 1, 0);
                var (x0, z0) = plan.World(a0.P, a0.Q);
                var (x1, z1) = plan.World(a1.P, a1.Q);
                return x1 > x0 || z1 > z0 ? index : count - 1 - index;
            }
            void Put(int s, int d, ushort prop, ArchPier facing, byte stack = 0)
            {
                var (p, q) = At(s, d);
                L36Put(plan, p, q, prop, facing, stack);
            }
            void Art(int s, int d, ArchPier facing, int index, byte kind, int bottom)
            {
                var (p, q) = At(s, d);
                L36WallArt(ref plan.At(p, q), plan.Dir(facing), index, kind, bottom);
            }
            ArchPier face = plan.Dir(outward);
            for (int s0 = 14; s0 + 18 <= L36Size - 14; s0 += 20)
            {
                bool clear = true;
                for (int d = 0; d <= Deep + 1 && clear; d++)
                    for (int s = s0 - 1; s <= s0 + 19 && clear; s++)
                    {
                        var (p, q) = At(s, d);
                        Tile c = plan.At(p, q);
                        if (c.Kind != TileKind.Wall || c.Zone != (byte)L36Zone.Solid) clear = false;
                    }
                if (!clear) continue;
                var mid = At(s0 + 9, 0);
                var (ux, uz) = plan.World(mid.P, mid.Q);
                ulong h = Hashing.Hash(seed, ux, uz, SaltL36Plan + 2);
                double r = Hashing.Unit(h), r2 = Hashing.Unit(Hashing.Mix(h));
                // The wall between this unit and the next: a poster facing the concourse
                Art(s0 + 19, 0, outward, 0, (byte)(L36ArtPoster + (int)((h >> 40) % 8)), 2);
                if (r < 0.2)
                {
                    // No unit: a stretch of wall with a departures board high up, or posters
                    if (r < 0.1)
                        for (int i = 0; i < 4; i++) Art(s0 + 7 + i, 0, outward, Up(s0 + 7, i, 4), L36ArtDep, 5);
                    else
                        foreach (int ps in new[] { s0 + 3, s0 + 9, s0 + 15 }) Art(ps, 0, outward, 0, (byte)(L36ArtPoster + (int)((h >> (ps - s0) * 2) % 8)), 2);
                    continue;
                }
                int kind = r < 0.58 ? 0 : r < 0.7 ? 1 : r < 0.8 ? 2 : r < 0.86 ? 3 : r < 0.93 ? 4 : 5;   // shop, services, restrooms, prayer, info, shoe shine
                byte[] shops = { L36ShopNews, L36ShopDutyFree, L36ShopCafe, L36ShopPharma, L36ShopExchange, L36ShopBooks, L36ShopTech, L36ShopNews,
                    L36ShopDutyFree, L36ShopFashion, L36ShopSnacks, L36ShopCafe };
                byte shop = kind switch
                {
                    0 => shops[Math.Min(shops.Length - 1, (int)(r2 * shops.Length))], 1 => L36ShopPhones, 2 => L36ShopToilets, 3 => L36ShopPrayer, 4 => L36ShopInfo,
                    _ => L36ShopShoeShine,
                };
                bool closed = kind == 0 && r2 * 7 % 1 < 0.25;
                L36Zone zone = kind == 2 ? L36Zone.Restroom : L36Zone.Shop;
                bool alcove = kind is 1 or 4 or 5;
                // (an alcove is shallow: six deep, the rest of the unit's depth left solid behind it)
                int deep = alcove ? 6 : Deep;
                int height = kind is 1 or 4 or 5 ? 6 : kind == 2 ? 4 : 5;
                byte floor = kind == 2 ? L36Mat.TileFloor : kind == 3 ? L36Mat.CarpetBlue : kind == 0 && shop == L36ShopCafe ? L36Mat.CarpetRed : kind == 0 ? L36Mat.MarbleGrey : L36Mat.Marble;
                for (int d = 1; d < deep; d++)
                    for (int s = s0 + 1; s <= s0 + 17; s++)
                    {
                        var (p, q) = At(s, d);
                        plan.At(p, q) = L36Air(zone, height, floor);
                    }
                var (lp0, lq0) = At(s0 + 1, 1);
                var (lp1, lq1) = At(s0 + 17, deep - 1);
                if (!closed) L36Lights(plan, Math.Min(lp0, lp1), Math.Min(lq0, lq1), Math.Max(lp0, lp1), Math.Max(lq0, lq1), 4, 0.05, 0.05);
                // The front: open for an alcove, else glass (plaster for the restrooms and the prayer room) round a doorway; the
                // fascia over the doorway's middle three
                int door0 = alcove ? s0 + 2 : kind is 2 or 3 ? s0 + 8 : s0 + 7, door1 = alcove ? s0 + 16 : kind is 2 or 3 ? s0 + 10 : s0 + 11;
                for (int s = s0; s <= s0 + 18; s++)
                {
                    var (p, q) = At(s, 0);
                    ref Tile f = ref plan.At(p, q);
                    bool door = s >= door0 && s <= door1;
                    if (door && !closed) f = L36Air(L36Zone.Shop, height, kind == 2 ? L36Mat.TileFloor : L36Mat.Marble);
                    else f = L36Solid(door ? L36Mat.Shutter : s > s0 && s < s0 + 18 && kind == 0 ? L36Mat.Glass : kind is 2 or 3 ? L36Mat.Plaster : L36Mat.Auto);
                    f.Pier = face;
                    if (s >= s0 + 8 && s <= s0 + 10 && door)
                    {
                        f.Depth = shop;
                        f.Roof = (byte)(1 + L36Part(face, Up(s0 + 8, s - s0 - 8, 3), 3));
                    }
                }
                // What is in it
                switch (kind)
                {
                    case 0:
                        for (int d = 2; d <= Deep - 2; d += 2)
                            for (int s = s0 + 2; s <= s0 + 16; s++)
                            {
                                if (s - s0 is 8 or 9 or 10) continue;
                                double rr = Hashing.Unit(Hashing.Hash(seed, s * 31 + edge, d * 17 + (int)(h % 997), SaltL36Prop + 3));
                                ushort prop = shop switch
                                {
                                    // (round 4) a newsstand's magazine racks between its shelves of books and snacks
                                    L36ShopNews => d % 4 == 2 ? Props.HotelBookshelf : s % 2 == 0 ? Props.L36MagRack : Props.SnackShelf,
                                    L36ShopDutyFree => d % 4 == 2 ? (s % 3 != 0 ? Props.L36Gondola : (ushort)0) : s % 3 != 0 ? Props.L36Perfume : Props.DrinkFridge,
                                    L36ShopPharma => s % 2 == 0 ? Props.MedCabinet : Props.Shelf,
                                    L36ShopExchange => 0,
                                    L36ShopBooks => Props.HotelBookshelf,
                                    L36ShopTech => rr < 0.5 ? Props.ConsoleTable : Props.Tv,
                                    L36ShopFashion => s % 2 == 0 ? Props.ClothesRack : (ushort)0,
                                    L36ShopSnacks => Props.SnackShelf,
                                    _ => s % 4 == 0 && d < Deep - 2 ? Props.L36MealTable : (ushort)0,
                                };
                                if (prop == 0) continue;
                                Put(s, d, prop, prop == Props.L36Perfume && d % 4 == 0 ? inward : outward,
                                    prop == Props.L36MealTable ? (byte)(rr < 0.3 ? 0 : rr < 0.55 ? 1 : rr < 0.7 ? 2 : 3) : (byte)0);
                                if (prop == Props.L36MealTable)
                                {
                                    Put(s - 1, d, Props.CafeChair, edge < 2 ? ArchPier.South : ArchPier.East);
                                    Put(s + 1, d, Props.CafeChair, edge < 2 ? ArchPier.North : ArchPier.West);
                                }
                            }
                        // the back wall's shelves (a cafe's kitchen; the bureau's long counter), the till by the door
                        for (int s = s0 + 2; s <= s0 + 16; s++)
                        {
                            if (shop == L36ShopExchange) { Put(s, 6, Props.ReceptionDesk, outward); continue; }
                            // (round 4) a cafe's back counter: espresso machines between the worktops
                            ushort back = shop == L36ShopCafe ? (s % 3 == 0 ? Props.L36Coffee : s % 3 == 1 ? Props.SnackCounter : Props.KitchenCounter)
                                : s % 2 == 0 ? Props.Shelf : (ushort)0;
                            if (back != 0) Put(s, Deep - 1, back, outward);
                        }
                        // (round 4) the till by the door, the clerk behind it; a cafe's pastry case beside it
                        Put(s0 + 3, 1, Props.L36Till, inward);
                        Put(s0 + 4, 1, shop == L36ShopCafe ? Props.L36Pastry : Props.SnackCounter, shop == L36ShopCafe ? inward : outward);
                        if (shop == L36ShopExchange)
                            for (int i = 0; i < 4; i++) Art(s0 + 7 + i, Deep, outward, Up(s0 + 7, i, 4), L36ArtDep, 3);
                        if (!closed && Hashing.Unit(Hashing.Mix(h + 7)) < 0.1)
                        {
                            var (p, q) = At(s0 + 16, Deep - 1);
                            L36Supply(plan, p, q);
                        }
                        break;
                    case 1:
                        // payphones down one side of the back wall, cash machines and a fountain on the other; a bench
                        for (int s = s0 + 2; s <= s0 + 7; s++) Put(s, deep - 1, Props.L36Phone, outward);
                        for (int s = s0 + 10; s <= s0 + 12; s++) Put(s, deep - 1, Props.L36Atm, outward);
                        Put(s0 + 14, deep - 1, Props.L36Fountain, outward);
                        Put(s0 + 15, deep - 1, Props.L36Fountain, outward);
                        Put(s0 + 16, deep - 1, Props.L36Bin, outward);
                        Put(s0 + 8, 2, Props.Bench, inward);
                        Put(s0 + 9, 2, Props.Bench, inward);
                        break;
                    case 2:
                        // cubicles along the back, basins either side of the door, the wet-floor sign
                        for (int s = s0 + 1; s <= s0 + 17; s++) Put(s, Deep - 1, Props.L36Stall, outward);
                        for (int s = s0 + 2; s <= s0 + 16; s += 2)
                            if (s - s0 is < 7 or > 11) Put(s, 1, Props.L974Basin, inward);
                        Put(s0 + 13, 5, Props.WetFloorSign, outward);
                        break;
                    case 3:
                        // rows of chairs facing the back wall, books and plants along it; quiet
                        // (round 4) chairs on one side of the aisle, prayer mats laid in rows on the other, one rolled at a row's end
                        for (int d = 3; d <= 7; d += 2)
                            for (int s = s0 + 3; s <= s0 + 15; s++)
                            {
                                if (s - s0 is 8 or 9 or 10) continue;
                                if (s - s0 < 8) Put(s, d, Props.HotelChair, inward);
                                else Put(s, d, Props.L36PrayerMat, inward, (byte)(s - s0 == 15 && d == 7 ? 1 : 0));
                            }
                        for (int s = s0 + 5; s <= s0 + 13; s++) Put(s, Deep - 1, s % 2 == 0 ? Props.OfficeBookshelf : Props.Ficus, outward);
                        break;
                    case 4:
                        // the information desk across the alcove, its screens behind it, the "i" hung in front
                        for (int s = s0 + 4; s <= s0 + 14; s++) Put(s, 3, Props.ReceptionDesk, outward);
                        // (round 4) an information pylon either side of the desk, facing the concourse
                        Put(s0 + 2, 2, Props.L36InfoPylon, outward);
                        Put(s0 + 16, 2, Props.L36InfoPylon, outward);
                        for (int i = 0; i < 2; i++)
                        {
                            var (p, q) = At(s0 + 8 + i, 5);
                            L36Hang(plan, p, q, Overheads.L36Fids, outward, (byte)(h % 4), L36Part(face, Up(s0 + 8, i, 2), 2));
                        }
                        {
                            var (p, q) = At(s0 + 11, 2);
                            L36Hang(plan, p, q, Overheads.L36Sign, outward, L36SInfo);
                        }
                        Put(s0 + 3, deep - 1, Props.CardboardBoxes, outward);
                        for (int i = 0; i < 4; i++) Art(s0 + 12 + i, deep, outward, Up(s0 + 12, i, 4), L36ArtDep, 3);
                        break;
                    default:
                        // shoe-shine chairs on their platforms, a shelf of polish, a coat stand
                        for (int s = s0 + 4; s <= s0 + 14; s += 2) Put(s, deep - 1, Props.L36ShoeShine, outward);
                        Put(s0 + 2, deep - 1, Props.Shelf, outward);
                        Put(s0 + 16, deep - 1, Props.CoatStand, outward);
                        Put(s0 + 8, 2, Props.Bench, inward);
                        Put(s0 + 10, 2, Props.Bench, inward);
                        foreach (int ps in new[] { s0 + 3, s0 + 15 }) Art(ps, deep, outward, 0, (byte)(L36ArtPoster + (ps - s0) % 8), 3);
                        break;
                }
                if (Hashing.Unit(Hashing.Mix(h + 3)) < 0.5)
                    foreach (int ps in new[] { s0 + 1, s0 + 17 })
                    {
                        if (ps >= door0 && ps <= door1) continue;
                        var (p, q) = At(ps, 0);
                        if ((plan.At(p, q).Detail & L36MatMask) == L36Mat.Glass) continue;
                        Art(ps, 0, outward, 0, (byte)(L36ArtPoster + (int)((h >> (ps - s0)) % 8)), 2);
                    }
            }
        }
    }

    // ---- Out of bounds: a service maze with vents ----

    private void L36LayService(L36Plan plan, ref Rng rng)
    {
        // Corridors on lines every twelve, three wide; each stretch between two crossings there or not (dead ends are the point),
        // the two lines from the staff doors always; one stretch in eight a vent, two high
        static bool Line(int k) => k is 5 or 15;
        for (int k = 0; k < 20; k++)
            for (int j = 0; j < 19; j++)
                for (int axis = 0; axis < 2; axis++)
                {
                    if (!Line(k) && !rng.Chance(0.55)) continue;
                    bool vent = !Line(k) && rng.Chance(0.12);
                    for (int s = j * 12 + 5; s <= (j + 1) * 12 + 7; s++)
                        for (int w = k * 12 + 5; w <= k * 12 + 7; w++)
                        {
                            int p = axis == 0 ? s : w, q = axis == 0 ? w : s;
                            if (p >= L36Size || q >= L36Size) continue;
                            ref Tile t = ref plan.At(p, q);
                            if (t.Kind == TileKind.Floor && t.Zone == (byte)L36Zone.Service) continue;
                            t = vent ? L36Air(L36Zone.Vent, 2, L36Mat.Concrete) : L36Air(L36Zone.Service, 3, L36Mat.Concrete);
                        }
                }
        // The ways in: staff doors from two concourses
        L36Fill(plan, 0, 65, 4, 67, L36Zone.Service, 3, L36Mat.Concrete);
        L36Fill(plan, 185, 0, 187, 4, L36Zone.Service, 3, L36Mat.Concrete);
        for (int q = 0; q < L36Size; q++)
            for (int p = 0; p < L36Size; p++)
            {
                ref Tile t = ref plan.At(p, q);
                if (t.Kind != TileKind.Floor) continue;
                var (x, z) = plan.World(p, q);
                double r = Hashing.Unit(Hashing.Hash(seed, x, z, SaltL36Prop));
                if (t.Zone == (byte)L36Zone.Vent)
                {
                    // Fans in the vents
                    if (r < 0.03) { t.Variant = Props.FloorFan; t.Pier = (ArchPier)(int)(r * 400 % 4); }
                    continue;
                }
                if (p % 12 == 6 && q % 6 == 0 || q % 12 == 6 && p % 6 == 0) t.Ceiling = L36Light(x, z, true, 0.45, 0.2);
                // The junk of the back of house; at a crossing now and then a sign with nothing on it
                if (r < 0.02) t.Variant = Props.CardboardBoxes;
                else if (r < 0.026) t.Variant = Props.Pallet;
                else if (r < 0.03) t.Variant = Props.LuggageCart;
                else if (r < 0.033) { t.Variant = r < 0.0315 ? Props.Generator : Props.PipeStack; t.Pier = (ArchPier)(int)(r * 4000 % 4); }
                else if (r < 0.0335) t.SupplyBox = true;
                if (r > 0.99 && p % 12 == 6 && q % 12 == 6) { t.Overhead = Overheads.L36Sign; t.Depth = r > 0.995 ? L36SBroken : L36SBlank; t.Pier = (ArchPier)(int)(r * 9999 % 4); }
            }
    }

    // ================= Gates, for the airport's runtime rules =================

    /// <summary>The gate whose holdroom, bridge or cabin covers a block, or null.</summary>
    public L36Gate L36GateAt(int gx, int gz)
    {
        int a = Hashing.Mod(gx - L36AirX, L36Period), bb = Hashing.Mod(gz - L36LineZ, L36Period);
        if (gx - L36WallX < L36Airside || a < L36Hall || bb < L36Hall) return null;
        int sx = Hashing.FloorDiv(gx - L36AirX, L36Period), sz = Hashing.FloorDiv(gz - L36LineZ, L36Period);
        if (L36KindOf(sx, sz) != L36Kind.Pier) return null;
        foreach (L36Gate g in L36PlanOf(sx, sz).Gates)
            if (g.Contains(gx, gz)) return g;
        return null;
    }

    /// <summary>The gates of the piers nearest a block, nearest superblocks first, until at least <paramref name="most"/> are found.</summary>
    public List<L36Gate> L36GatesNear(int gx, int gz, int most)
    {
        var found = new List<L36Gate>();
        int sx0 = Math.Max(0, Hashing.FloorDiv(gx - L36AirX, L36Period)), sz0 = Hashing.FloorDiv(gz - L36LineZ, L36Period);
        for (int r = 0; r <= 3 && found.Count < most; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || sx0 + dx < 0) continue;
                    if (L36KindOf(sx0 + dx, sz0 + dz) != L36Kind.Pier) continue;
                    L36Plan plan = L36PlanOf(sx0 + dx, sz0 + dz);
                    if (LevelAt(MacroOf(plan.X0 + 120), MacroOf(plan.Z0 + 120)) != Level36) continue;
                    found.AddRange(plan.Gates);
                }
        return found;
    }

    public static bool L36IsDark(in Tile t) => t.Kind == TileKind.Floor && (t.Detail & L36DarkBit) != 0;

    /// <summary>Whether a block is in a blackout (where the director may put something).</summary>
    public bool L36DarkAt(int gx, int gz) => L36IsDark(TileAt(gx, gz));

    // ================= The Travel Planner =================

    /// <summary>
    /// The Travel Planner's spot in a cell, if it holds one: behind a Backrooms Travel Agency booth in check-in (one module in 32,
    /// booth 0 on the centre line), or behind the Agency's desk in a Meeting Place.
    /// </summary>
    private (int X, int Z)? L36WandererSite(int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        int bx = L36WallX + 35;
        if (bx >= x0 && bx < x0 + MacroSize)
        {
            int first = Hashing.FloorDiv(z0 - L36LineZ - 15, 1024), last = Hashing.FloorDiv(z0 + MacroSize - 1 - L36LineZ - 15, 1024);
            for (int i = first; i <= last; i++)
            {
                int bz = L36LineZ + i * 1024 + 15;
                if (bz >= z0 && bz < z0 + MacroSize) return (bx, bz);
            }
        }
        int cx = x0 + MacroSize / 2, cz = z0 + MacroSize / 2;
        if (cx - L36WallX < L36Airside) return null;
        int sx = Hashing.FloorDiv(cx - L36AirX, L36Period), sz = Hashing.FloorDiv(cz - L36LineZ, L36Period);
        if (L36KindOf(sx, sz) != L36Kind.Meeting) return null;
        int px = L36AirX + sx * L36Period + L36Hall + L36PlannerP, pz = L36LineZ + sz * L36Period + L36Hall + L36PlannerQ;
        return px >= x0 && px < x0 + MacroSize && pz >= z0 && pz < z0 + MacroSize ? (px, pz) : null;
    }

    /// <summary>
    /// The level's loose notes in a cell (<see cref="NoteSpots"/>): a wanderer's note by the Travel Planner's spot, one in a Lost
    /// and Found office, a folded note by gate C32's podium.
    /// </summary>
    private void L36NoteSpots(int mx, int mz, Action<int, int, string, int> near)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        if (L36WandererSite(mx, mz) is { } site) near(site.X - x0, site.Z - z0, "way", 4);
        // A Lost and Found office: in the module whose index is 6 mod 12, against the baggage wall
        int ox = L36WallX + 5;
        if (ox >= x0 && ox < x0 + MacroSize)
            for (int module = Hashing.FloorDiv(z0 - L36LineZ, 32); module <= Hashing.FloorDiv(z0 + MacroSize - 1 - L36LineZ, 32); module++)
            {
                int oz = L36LineZ + module * 32 + 8;
                if (!L36IsCarousel(module) && oz >= z0 && oz < z0 + MacroSize) near(ox - x0, oz - z0, "cache", 3);
            }
        int cx = x0 + MacroSize / 2, cz = z0 + MacroSize / 2;
        if (cx - L36WallX < L36Airside) return;
        int sx = Hashing.FloorDiv(cx - L36AirX, L36Period), sz = Hashing.FloorDiv(cz - L36LineZ, L36Period);
        if (L36KindOf(sx, sz) != L36Kind.Pier) return;
        foreach (L36Gate g in L36PlanOf(sx, sz).Gates)
            if (g.SupportGroup && g.FrontX >= x0 && g.FrontX < x0 + MacroSize && g.FrontZ >= z0 && g.FrontZ < z0 + MacroSize)
                near(g.FrontX - x0, g.FrontZ - z0, "folded", 6);
    }

    /// <summary>Which of the level's props people walk through: the scanner arch.</summary>
    private static bool L36WalkThrough(ushort variant) => variant == Props.L36Scanner;

    // ================= Air =================

    /// <summary>
    /// The temperature: 21 C as the terminal is kept; a stretch of concourse in seven runs cold (10 C) and one in seven warm
    /// (28 C) (the lore's "drastically different temperatures"); the cabin and the vents cooler.
    /// </summary>
    private float L36Temperature(int x, int y, int z, int floorY)
    {
        Tile t = TileAt(x, z);
        if (t.Zone == (byte)L36Zone.Cabin) return 18f;
        if (t.Zone == (byte)L36Zone.Vent) return 12f;
        if (t.Zone != (byte)L36Zone.Concourse || x - L36WallX < L36Airside) return LevelTemperatures[Level36];
        bool ns = Hashing.Mod(x - L36AirX, L36Period) < L36Hall;
        int sx = Hashing.FloorDiv(x - L36AirX, L36Period), sz = Hashing.FloorDiv(z - L36LineZ, L36Period);
        double r = Hashing.Unit(L36Stretch(sx, sz, ns, SaltL36Heat));
        return r < 1 / 7.0 ? 10f : r < 2 / 7.0 ? 28f : LevelTemperatures[Level36];
    }

    /// <summary>Reality stability: steady (a safe hub); a blackout a little less; the Absolute Limit drains it.</summary>
    private float L36Stability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        if ((t.Detail & L36LimitBit) != 0) return 0.6f;
        return L36IsDark(t) ? 0.95f : 1.05f;
    }
}
