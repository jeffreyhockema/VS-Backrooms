using System.Collections.Generic;
using Zone = Backrooms.Worldgen.WorldLayout.L31Zone;
using L31 = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 31, "Roller Rink" (experimental, kept as level 24), laid out in WorldLayout.Level31.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Every floor tile carries its air height (<see cref="Tile.Height"/>: halls and the
/// lobby 5, rooms and the corridor 4, the cinema 6, the rink 7 or 5) with its ceiling just above; walls are dressed to
/// their own height and solid above. The level's own blocks (tools/gen_31.py) are the rink boards, the rink's walls and
/// barrier, the mirror panels and the disco ball, the coloured tubes and the glowing carpet; the rest is borrowed: Level
/// 3999's neon, carpets, ceilings, counters and arcade machines, Level Fun's carpet, vinyl and cinema screen, Level 52's
/// lockers, Level 3's glazed tile, the shared detail props (benches, café tables, snack counters, toilets, machinery).
///
/// Every block is looked up softly (<see cref="L31Block"/>): what is missing is drawn as its stand-in, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l31Galaxy, l31Cosmic, l31Marble, l31Retro, l31Vinyl, l31CheckerA, l31CheckerB, l31Maroon, l31Glow, l31ConcFloor, l31ConcWet,
        l31ConcDark, l31Stripe, l31Plain, l31Blue, l31Chart, l31Dasher, l31Glazed, l31Dark, l31Ball, l31CeilBlack, l31CeilAcoustic, l31Bin;
    private readonly int[] l31Board = new int[4], l31Mirror = new int[4], l31NeonDead = new int[2], l31DeadCab = new int[4], l31Pinball = new int[4],
        l31Claw = new int[4], l31SkeeLane = new int[4], l31SkeeTarget = new int[4], l31Prize = new int[4], l31DjScreen = new int[4];
    private readonly int[,] l31Tube = new int[6, 4], l31Locker = new int[2, 4], l31Neon = new int[6, 2], l31Rail = new int[6, 4], l31Cabinet = new int[6, 4],
        l31Counter = new int[3, 4], l31Vending = new int[2, 4], l31Couch = new int[2, 4], l31Screen = new int[3, 4];
    // The detail pass's blocks (tools/gen_31_props.py)
    private int l31CarpetRink, l31CarpetBlack, l31CarpetGrey, l31Polished, l31RentalTile, l31Quarry, l31Brick, l31Table, l31Star;
    private readonly int[] l31Chair = new int[4], l31Condiments = new int[4], l31Fountain = new int[4], l31Speaker = new int[4], l31Gate = new int[2],
        l31Dispenser = new int[4], l31SkateShelf = new int[4], l31CinemaBench = new int[4], l31Cctv = new int[4], l31Monitors = new int[4],
        l31Door70High = new int[4];
    private readonly int[,] l31Sign = new int[9, 4], l31ParkBench = new int[2, 4], l31DjDesk = new int[2, 4], l31RetroCab = new int[3, 4], l31Tv = new int[6, 4];
    /// <summary>The halls' cladding (tools/gen_31_walls.py): the mural's 6 x 4 blocks by [column * 4 + row, side], the mirror's
    /// 2 x 3 by [row * 2 + column, side], the lacquer (plain, with its top trim).</summary>
    private readonly int[,] l31Mural = new int[24, 4], l31CladMirror = new int[6, 4], l31Lacquer = new int[2, 4], l31DjSign = new int[6, 4];
    private readonly int[] l31Exit = new int[4], l31Crt = new int[4];
    private readonly HashSet<string> l31Missing = new();

    /// <summary>A block of this mod's, or <paramref name="fallback"/> if it is not there (logged once).</summary>
    private int L31Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l31Missing.Add(code) && l31Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 31: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>The level's block ids (called from the constructor, after Level 3999's and Level 52's).</summary>
    private void InitL31()
    {
        l31ConcFloor = L31Block("concretefloor-plain", concreteId);
        l31ConcWet = L31Block("concretefloor-wet", l31ConcFloor);
        l31ConcDark = L31Block("concretefloor-dark", l31ConcFloor);
        l31Galaxy = L31Block("l3999-carpet-galaxy", l31ConcFloor);
        l31Cosmic = L31Block("l3999-carpet-cosmic", l31Galaxy);
        l31Marble = L31Block("l3999-marble-black", l31ConcFloor);
        l31Retro = L31Block("fun-retrocarpet", l31Cosmic);
        l31Vinyl = L31Block("fun-vinyl-a", l31ConcFloor);
        l31CheckerA = L31Block("fun-checkermat-a", l31Vinyl);
        l31CheckerB = L31Block("fun-checkermat-b", l31Vinyl);
        l31Maroon = L31Block("hotelcarpet-maroon", l31Retro);
        l31Glow = L31Block("l31-glowcarpet-plain", l31Cosmic);
        string[] boards = { "plain", "stripens", "stripewe", "centre" };
        for (int i = 0; i < 4; i++) l31Board[i] = L31Block("l31-rinkwood-" + boards[i], i == 0 ? L31Block("hotelwood", l31ConcFloor) : l31Board[0]);
        l31Plain = L31Block("l31-skatewall-plain", concreteWallId);
        l31Stripe = L31Block("l31-skatewall-stripe", l31Plain);
        l31Blue = L31Block("l31-skatewall-blue", l31Plain);
        l31Chart = L31Block("l31-skatewall-chart", l31Blue);
        l31Dasher = L31Block("l31-skatewall-dasher", l31Plain);
        l31Glazed = L31Block("l3wall-glazed", l31Plain);
        l31Dark = L31Block("l3999-wall-midnight", l31Plain);
        l31Ball = L31Block("l31-mirror-ball");
        l31CeilBlack = L31Block("l3999-ceiling-black", concreteCeilingId);
        l31CeilAcoustic = L31Block("l3999-ceiling-acoustic", ceilingTileId);
        l31Bin = L31Block("l3999-trashbin");
        string[] hues = { "magenta", "cyan", "amber", "green", "violet", "white" }, states = { "on", "lit", "flicker", "off" };
        int[] fallbacks = { lightOnId, lightLitId, lightFlickerId, lightOffId };
        for (int h = 0; h < 6; h++)
            for (int s = 0; s < 4; s++) l31Tube[h, s] = L31Block($"l31-tube-{hues[h]}-{states[s]}", fallbacks[s]);
        string[] colours = WorldLayout.L3999Colours, games = { "a", "b", "c", "d", "e", "f" }, desk = { "left", "mid", "right" }, screens = { "l", "m", "r" };
        l31NeonDead[0] = L31Block("l3999-neondead-ns");
        l31NeonDead[1] = L31Block("l3999-neondead-we");
        for (int c = 0; c < 6; c++)
        {
            l31Neon[c, 0] = L31Block($"l3999-neonceiling-{colours[c]}-ns");
            l31Neon[c, 1] = L31Block($"l3999-neonceiling-{colours[c]}-we");
        }
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            l31Mirror[f] = L31Block("l31-mirror-" + side, l31Plain);
            l31Locker[0, f] = L31Block($"l52-locker-lower-{side}", l31Stripe);
            l31Locker[1, f] = L31Block($"l52-locker-upper-{side}", l31Plain);
            for (int c = 0; c < 6; c++)
            {
                l31Rail[c, f] = L31Block($"l3999-neonrail-{colours[c]}-{side}");
                l31Cabinet[c, f] = L31Block($"l3999-cabinet-{games[c]}-{side}");
            }
            l31DeadCab[f] = L31Block($"l3999-cabinet-dead-{side}");
            l31Pinball[f] = L31Block($"l3999-pinball-{side}");
            l31Claw[f] = L31Block($"l3999-claw-{side}");
            l31SkeeLane[f] = L31Block($"l3999-skeeball-lane-{side}");
            l31SkeeTarget[f] = L31Block($"l3999-skeeball-target-{side}");
            l31Prize[f] = L31Block($"l3999-prizecounter-{side}");
            l31DjScreen[f] = L31Block($"l3999-dance-screen-{side}");
            for (int k = 0; k < 3; k++)
            {
                l31Counter[k, f] = L31Block($"l3999-reception-{desk[k]}-{side}");
                l31Screen[k, f] = L31Block($"fun-screen-{screens[k]}-{side}");
            }
            l31Vending[0, f] = L31Block($"l3999-vending-snack-{side}");
            l31Vending[1, f] = L31Block($"l3999-vending-drink-{side}");
            l31Couch[0, f] = L31Block($"l3999-couch-left-{side}");
            l31Couch[1, f] = L31Block($"l3999-couch-right-{side}");
        }
        InitL31Detail();
    }

    /// <summary>The blocks of the detail pass (2026-10-30): the level's own carpets and floors, the signs on its walls, the
    /// food court's furniture, the DJ station, the star, the gates, the arcade's dispenser and old cabinets, the rental's
    /// shelves, the cinema's benches and TV, the lounge's CCTV.</summary>
    private void InitL31Detail()
    {
        l31CarpetRink = L31Block("l31-carpet-rink", l31Galaxy);
        l31CarpetBlack = L31Block("l31-carpet-black", l31Retro);
        l31CarpetGrey = L31Block("l31-carpet-grey", l31Retro);
        l31Polished = L31Block("l31-floor-polished", l31Marble);
        l31RentalTile = L31Block("l31-floor-tile", l31CheckerA);
        l31Quarry = L31Block("l31-floor-quarry", l31Vinyl);
        l31Brick = L31Block("l31-brick-plain", l31Plain);
        l31Table = L31Block("l31-table-plain");
        l31Star = L31Block("l31-star-plain", l31Ball);
        l31Gate[0] = L31Block("l31-gate-we");
        l31Gate[1] = L31Block("l31-gate-ns");
        // (By WorldLayout.L31Sign's numbers: 4 is the first advert, 7 and 8 the other two; 0 the staff door's upper half)
        string[] signs = { "staffdoorhigh", "trash", "outoforder", "menu", "ad1", "staffdoorlow", "door70low", "ad2", "ad3" };
        string[] games = { "shooter", "barrels", "pyramid" }, parts = { "tl", "tm", "tr", "bl", "bm", "br" };
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            for (int k = 0; k < signs.Length; k++) l31Sign[k, f] = L31Block($"l31-sign-{signs[k]}-{side}", l31Plain);
            l31Door70High[f] = L31Block($"l31-sign-door70high-{side}", l31Dark);
            l31Chair[f] = L31Block($"l31-chair-{side}");
            l31ParkBench[0, f] = L31Block($"l31-bench-orange-{side}");
            l31ParkBench[1, f] = L31Block($"l31-bench-green-{side}");
            l31Condiments[f] = L31Block($"l31-condiments-{side}");
            l31Fountain[f] = L31Block($"l31-fountain-{side}");
            l31DjDesk[0, f] = L31Block($"l31-djdesk-deck-{side}");
            l31DjDesk[1, f] = L31Block($"l31-djdesk-mixer-{side}");
            l31Speaker[f] = L31Block($"l31-speaker-{side}");
            l31Dispenser[f] = L31Block($"l31-dispenser-{side}");
            for (int g = 0; g < 3; g++) l31RetroCab[g, f] = L31Block($"l31-retrocab-{games[g]}-{side}", l31Cabinet[g, f]);
            l31SkateShelf[f] = L31Block($"l31-skateshelf-{side}");
            l31CinemaBench[f] = L31Block($"l31-cinemabench-{side}");
            for (int k = 0; k < 6; k++) l31Tv[k, f] = L31Block($"l31-tv-{parts[k]}-{side}");
            l31Cctv[f] = L31Block($"l31-cctv-{side}");
            l31Monitors[f] = L31Block($"l31-monitors-{side}");
            for (int c = 0; c < 6; c++)
                for (int r = 0; r < 4; r++) l31Mural[c * 4 + r, f] = L31Block($"l31-cladding-m{c}{r}-{side}");
            string[] mirror = { "ftl", "ftr", "fml", "fmr", "fbl", "fbr" };
            for (int k = 0; k < 6; k++) l31CladMirror[k, f] = L31Block($"l31-cladding-{mirror[k]}-{side}");
            l31Lacquer[0, f] = L31Block($"l31-cladding-lacq-{side}");
            l31Lacquer[1, f] = L31Block($"l31-cladding-lacqtop-{side}");
            for (int c = 0; c < 3; c++)
                for (int r = 0; r < 2; r++) l31DjSign[c * 2 + r, f] = L31Block($"l31-cladding-dj{c}{r}-{side}");
            l31Exit[f] = L31Block($"l31-cladding-exit-{side}");
            l31Crt[f] = L31Block($"l31-cladding-crt-{side}");
        }
    }

    /// <summary>A sign on a wall's face at a height (0 where the sign has nothing at that height).</summary>
    private int L31SignBlock(in Tile t, int gx, int gz, int rel, int high)
    {
        int f = Facing(t.Pier);
        int sign = t.Detail & L31.L31HueMask;
        switch (sign)
        {
            case L31.L31Sign.StaffDoor: return rel == 1 ? l31Sign[5, f] : rel == 2 ? l31Sign[0, f] : 0;
            case L31.L31Sign.Door70: return rel == 1 ? l31Sign[6, f] : rel == 2 ? l31Door70High[f] : 0;
            case L31.L31Sign.Menu: return rel == (high >= 4 ? 3 : 2) ? l31Sign[3, f] : 0;
            case L31.L31Sign.Advert:
                if (rel != 2) return 0;
                uint h = (uint)(gx * 73856093 ^ gz * 19349663) % 3;
                return l31Sign[h == 0 ? 4 : h == 1 ? 7 : 8, f];
            default: return rel == 2 && sign < 4 ? l31Sign[sign, f] : 0;
        }
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level31Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < 0) return concreteId;
        if (t.Kind != TileKind.Floor)
        {
            int high = t.Height > 0 ? t.Height : 4;
            if (rel > high) return concreteId;
            if (rel == 0) return t.Kind == TileKind.Doorway ? L31Floor(t, gx, gz) : concreteId;
            if (t.Kind == TileKind.Doorway && rel <= 3) return 0;
            return L31WallBlock(t, gx, gz, rel, high);
        }
        int air = t.Height > 0 ? t.Height : 4;
        if (rel == 0) return L31Floor(t, gx, gz);
        if (rel == air + 1) return L31Ceiling(t);
        if (rel > air) return concreteId;
        if (rel >= 2 && t.Overhead is L31.L31Overhead.Mural or L31.L31Overhead.Mirrors or L31.L31Overhead.Sign)
        {
            // (a sign alone on a wall leaves the rest of its column to the room: a cinema's steps, say)
            int clad = L31Cladding(t, gx, gz, rel, air);
            if (clad != 0 || t.Overhead != L31.L31Overhead.Sign || t.Zone != (byte)Zone.Cinema) return clad;
        }
        if (rel == air)
        {
            switch (t.Overhead)
            {
                case L31.L31Overhead.NeonNS: return l31Neon[(t.Detail & L31.L31HueMask) % 6, 0];
                case L31.L31Overhead.NeonWE: return l31Neon[(t.Detail & L31.L31HueMask) % 6, 1];
                case L31.L31Overhead.DeadNS: return l31NeonDead[0];
                case L31.L31Overhead.DeadWE: return l31NeonDead[1];
                case L31.L31Overhead.DiscoBall: return l31Ball;
                case L31.L31Overhead.Star: return l31Star;
                case L31.L31Overhead.Cctv: return l31Cctv[Facing(t.Pier)];
            }
            if (t.Zone is (byte)Zone.Corridor or (byte)Zone.Hvac)
            {
                int pipe = (t.Detail & L31.L31SubMask) >> L31.L31SubShift;
                if (pipe == L31.L31PipeX) return pipeRunXId;
                if (pipe == L31.L31PipeZ) return pipeRunZId;
            }
        }
        if (t.Variant == L31.L31Props.Screen) return rel == air ? l31Screen[System.Math.Min((int)t.Stack, 2), Facing(t.Pier)] : 0;
        // The cinema's big TV on the wall, its top row at rel 3 and its bottom at rel 2
        if (t.Variant == L31.L31Props.Tv) return rel is 2 or 3 ? l31Tv[(rel == 3 ? 0 : 3) + System.Math.Min((int)t.Stack, 2), Facing(t.Pier)] : 0;
        int sub = (t.Detail & L31.L31SubMask) >> L31.L31SubShift;
        // A cinema row raised a step or three; a flooded HVAC room's water over its wet floor
        int lift = t.Zone == (byte)Zone.Cinema ? sub : 0;
        if (lift > 0 && rel <= lift) return l31Maroon;
        if (t.Zone == (byte)Zone.Hvac && sub == L31.L31SubFlood && rel == 1)
        {
            fluid = waterId;
            return 0;
        }
        if (rel != 1 + lift) return 0;
        if (t.SupplyBox) return BoxOf(t);
        if (t.Variant != 0) return L31Prop(t);
        if ((t.Detail & L31.L31RailBit) != 0 && t.Zone == (byte)Zone.Hall) return l31Rail[(t.Detail & L31.L31HueMask) % 6, Facing(t.Pier)];
        return 0;
    }

    /// <summary>
    /// A hall's wall cladding, <paramref name="rel"/> 2 up to the ceiling: the mural, six blocks to a repeat, or black lacquer
    /// with a mirror two wide and three high (rel 2-4) in every five. The pictures run from the viewer's left, so along the
    /// wall the column counts the way the viewer's right goes (looking south, the right is west).
    /// </summary>
    private int L31Cladding(in Tile t, int gx, int gz, int rel, int air)
    {
        if (t.Overhead == L31.L31Overhead.Sign && t.Zone == (byte)Zone.Cinema)
            return rel != 4 ? 0 : (t.Detail & L31.L31RailBit) != 0 ? l31Crt[Facing(t.Pier)] : l31Exit[Facing(t.Pier)];
        ArchPier facing = t.Pier;
        // (round a rink or in a lobby the tile's Pier may be its prop's: the wall is found beside it, and the cladding faces away from it)
        if (t.Zone != (byte)Zone.Hall)
        {
            if (L31Walled(layout.TileAt(gx, gz - 1))) facing = ArchPier.South;
            else if (L31Walled(layout.TileAt(gx, gz + 1))) facing = ArchPier.North;
            else if (L31Walled(layout.TileAt(gx - 1, gz))) facing = ArchPier.East;
            else if (L31Walled(layout.TileAt(gx + 1, gz))) facing = ArchPier.West;
            else return 0;
        }
        // (over a doorway, only above its opening)
        var (bx, bz) = facing switch { ArchPier.North => (gx, gz + 1), ArchPier.South => (gx, gz - 1), ArchPier.East => (gx - 1, gz), _ => (gx + 1, gz) };
        if (rel <= 3 && layout.TileAt(bx, bz).Kind == TileKind.Doorway) return 0;
        int f = Facing(facing);
        if (t.Overhead == L31.L31Overhead.Sign && rel >= air - 1)
            return l31DjSign[System.Math.Clamp(((t.Detail & L31.L31SubMask) >> L31.L31SubShift) - 1, 0, 2) * 2 + (air - rel), f];
        int along = facing switch { ArchPier.North => -gx, ArchPier.South => gx, ArchPier.East => -gz, _ => gz };
        if (t.Overhead != L31.L31Overhead.Mirrors && rel <= 5)
            return l31Mural[Hashing.Mod(along, 6) * 4 + (5 - rel), f];
        int c = Hashing.Mod(along, 5);
        if (t.Overhead == L31.L31Overhead.Mirrors && c is 1 or 2 && rel <= 4) return l31CladMirror[(4 - rel) * 2 + c - 1, f];
        return l31Lacquer[rel == air ? 1 : 0, f];
    }

    private static bool L31Walled(in Tile t) => t.Kind is TileKind.Wall or TileKind.Doorway;

    private int L31WallBlock(in Tile t, int gx, int gz, int rel, int high)
    {
        if ((t.Detail & L31.L31HueMask) != 0 && L31SignBlock(t, gx, gz, rel, high) is int sign and > 0) return sign;
        if ((t.Detail & L31.L31MirrorBit) != 0 && (high >= 7 ? rel is >= 3 and <= 5 : rel is 2 or 3)) return l31Mirror[Facing(t.Pier)];
        int skate = rel == 1 ? l31Stripe : l31Plain;
        int sub = (t.Detail & L31.L31SubMask) >> L31.L31SubShift;
        // (a complex's outside wall shows the halls the rink's navy band at its foot, behind their neon strip, whatever the room inside)
        if (rel == 1 && sub is not (L31.L31Wall.Locker or L31.L31Wall.Chart) && t.Kind == TileKind.Wall
            && (Hashing.Mod(gx, L31.L31Period) is 0 or 6 || Hashing.Mod(gz, L31.L31Period) is 0 or 6)) return l31Stripe;
        return sub switch
        {
            L31.L31Wall.Concrete => concreteWallId,
            L31.L31Wall.Blue => l31Blue,
            L31.L31Wall.Glazed => l31Glazed,
            L31.L31Wall.Dark => l31Dark,
            L31.L31Wall.Chart => rel == 2 ? l31Chart : skate,
            L31.L31Wall.Locker => rel <= 2 ? l31Locker[rel - 1, Facing(t.Pier)] : l31Plain,
            L31.L31Wall.Brick => l31Brick,
            _ => skate,
        };
    }

    private int L31Floor(in Tile t, int gx, int gz) => t.Zone switch
    {
        // The level's own dark rink carpet in the halls and the lobby, rough black carpet round the rink (Wikidot), the
        // crossings in shiny, just-cleaned concrete (Fandom), grey carpet in the employees' lounge
        (byte)Zone.Hall or (byte)Zone.Lobby => l31CarpetRink,
        (byte)Zone.Crossing => l31Polished,
        (byte)Zone.Skirt => l31CarpetBlack,
        (byte)Zone.Lounge => l31CarpetGrey,
        (byte)Zone.Rink => t.Variant == L31.L31Props.Dasher ? l31Board[0] : l31Board[System.Math.Min(3, (t.Detail & L31.L31SubMask) >> L31.L31SubShift)],
        (byte)Zone.Snack => (t.Detail & L31.L31SubMask) >> L31.L31SubShift == L31.L31SubKitchen ? l31Quarry : l31Vinyl,
        (byte)Zone.Rental => l31RentalTile,
        (byte)Zone.Bath => l31CheckerB,
        (byte)Zone.Arcade => l31Cosmic,
        (byte)Zone.Cinema => l31Maroon,
        (byte)Zone.CarpetRoom => l31Glow,
        (byte)Zone.Empty => l31ConcDark,
        // Puddles where the HVAC leaks
        (byte)Zone.Hvac => (uint)(gx * 73856093 ^ gz * 19349663) % 5 < 2 ? l31ConcWet : l31ConcFloor,
        _ => l31ConcFloor,
    };

    private int L31Ceiling(in Tile t)
    {
        int state = t.Ceiling switch
        {
            CeilingKind.LightOn => 0,
            CeilingKind.LightLit => 1,
            CeilingKind.LightFlicker => 2,
            CeilingKind.LightOff => 3,
            _ => -1,
        };
        if (state >= 0)
        {
            int hue = t.Detail & L31.L31HueMask;
            if (hue < 6) return l31Tube[hue, state];
            return state switch { 0 => lightOnId, 1 => lightLitId, 2 => lightFlickerId, _ => lightOffId };
        }
        return t.Zone switch
        {
            (byte)Zone.Rink or (byte)Zone.Skirt or (byte)Zone.Hall or (byte)Zone.Crossing or (byte)Zone.Arcade or (byte)Zone.Cinema
                or (byte)Zone.CarpetRoom => l31CeilBlack,
            (byte)Zone.Lobby or (byte)Zone.Snack or (byte)Zone.Rental or (byte)Zone.Lounge or (byte)Zone.Bath => l31CeilAcoustic,
            _ => concreteCeilingId,
        };
    }

    private int L31Prop(in Tile t)
    {
        int f = Facing(t.Pier);
        return t.Variant switch
        {
            L31.L31Props.Dasher => l31Dasher,
            L31.L31Props.Cabinet => l31Cabinet[t.Stack % 6, f],
            L31.L31Props.DeadCabinet => l31DeadCab[f],
            L31.L31Props.Pinball => l31Pinball[f],
            L31.L31Props.Claw => l31Claw[f],
            L31.L31Props.SkeeLane => l31SkeeLane[f],
            L31.L31Props.SkeeTarget => l31SkeeTarget[f],
            L31.L31Props.PrizeCounter => l31Prize[f],
            L31.L31Props.Counter => l31Counter[System.Math.Min((int)t.Stack, 2), f],
            L31.L31Props.DjScreen => l31DjScreen[f],
            L31.L31Props.Vending => l31Vending[t.Stack & 1, f],
            L31.L31Props.Bin => l31Bin,
            L31.L31Props.Couch => l31Couch[t.Stack & 1, f],
            L31.L31Props.Gate => l31Gate[t.Stack & 1],
            L31.L31Props.Chair => l31Chair[f],
            L31.L31Props.Table => l31Table,
            L31.L31Props.ParkBench => l31ParkBench[t.Stack & 1, f],
            L31.L31Props.Condiments => l31Condiments[f],
            L31.L31Props.Fountain => l31Fountain[f],
            L31.L31Props.DjDesk => l31DjDesk[t.Stack & 1, f],
            L31.L31Props.Speaker => l31Speaker[f],
            L31.L31Props.CardDispenser => l31Dispenser[f],
            L31.L31Props.RetroCabinet => l31RetroCab[t.Stack % 3, f],
            L31.L31Props.SkateShelf => l31SkateShelf[f],
            L31.L31Props.CinemaBench => l31CinemaBench[f],
            L31.L31Props.Monitors => l31Monitors[f],
            L31.L31Props.StaffSpot => 0,
            Props.Shelf => shelfIds[Facing(Opposite(t.Pier))],
            >= 40 and < Props.Limit => PropBlock(t),
            _ => 0,
        };
    }
}
