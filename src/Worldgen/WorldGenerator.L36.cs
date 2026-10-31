using System.Collections.Generic;
using Zone = Backrooms.Worldgen.WorldLayout.L36Zone;
using Mat = Backrooms.Worldgen.WorldLayout.L36Mat;
using L36 = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 36, "Airport" (experimental, kept as level 25), laid out in WorldLayout.Level36.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Every floor tile carries its air (<see cref="Tile.Height"/>) with its ceiling just
/// above; walls are dressed to their own height and solid above. The level's own blocks (tools/gen_36_surfaces.py,
/// tools/gen_36_props.py): marble and carpet, the carousels' belts and islands, the terminal's walls, the painted runway
/// windows, steel ceilings and their lights, the gate and wayfinding signs, the flight screens, the check-in desks, gate
/// seats, podiums and jet-bridge doors, the security lanes, the Travel Agency's booth, the shops' fascias and stock, the
/// cabin, the meeting point and the static of the Absolute Limit. Borrowed: Level 3999's moving walkways, couches,
/// planters, bins and shutters, Level 4's machines and fountains, the shared detail props (benches, suitcases, café chairs,
/// snack counters, shelves, toilets, boxes...).
///
/// Every block is looked up softly (<see cref="L36Block"/>): what is missing is drawn as its stand-in, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L36Dirs = { "n", "e", "s", "w" };

    private int l36Concrete, l36TileFloor, l36Kick, l36Panel, l36Plaster, l36WallTile, l36Service, l36Purple, l36Stainless, l36Island,
        l36Trays, l36Bin, l36Planter, l36LightHigh, l36Glass, l36CeilSteel, l36CeilTile, l36CeilDark, l36CeilCabin;
    private readonly int[] l36Marble = new int[3], l36Carpet = new int[4], l36Static = new int[4], l36Light = new int[4],
        l36BeltRun = new int[4], l36BeltStill = new int[4], l36Walk = new int[4], l36WalkEnd = new int[4], l36Flap = new int[4],
        l36Door = new int[8], l36GateDesk = new int[4], l36Stanchion = new int[5], l36Scanner = new int[8], l36Xray = new int[8],
        l36Perfume = new int[4], l36Meal = new int[4], l36Meeting = new int[3], l36CabinSeat = new int[4], l36LostFound = new int[4],
        l36Couch = new int[8], l36Shutter = new int[8];
    private readonly int[,] l36Window = new int[4, 4], l36Clock = new int[2, 4], l36CabinWall = new int[3, 4], l36Checkin = new int[2, 4],
        l36Seat = new int[4, 4], l36Booth = new int[5, 4], l36GateSign = new int[86, 4], l36Sign = new int[13, 4];
    private readonly int[,,] l36Fids = new int[6, 2, 4], l36ShopSign = new int[8, 3, 4];
    private readonly HashSet<string> l36Missing = new();

    /// <summary>A block of this mod's, or <paramref name="fallback"/> if it is not there (logged once).</summary>
    private int L36Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l36Missing.Add(code) && l36Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 36: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL36()
    {
        l36Concrete = L36Block("concretefloor-plain", concreteId);
        string[] marbles = { "white", "grey", "dark" }, carpets = { "blue", "teal", "red", "grey" };
        for (int i = 0; i < 3; i++) l36Marble[i] = L36Block("l36-marble-" + marbles[i], l36Concrete);
        for (int i = 0; i < 4; i++) l36Carpet[i] = L36Block("l36-carpet-" + carpets[i], l36Marble[0]);
        for (int i = 0; i < 4; i++) l36Static[i] = L36Block("l36-static-" + "abcd"[i], concreteId);
        l36Panel = L36Block("l36-wall-panel", concreteWallId);
        l36Kick = L36Block("l36-wall-kick", l36Panel);
        l36Plaster = L36Block("l36-wall-plaster", l36Panel);
        l36WallTile = L36Block("l36-wall-tile", l36Plaster);
        l36Service = L36Block("l36-wall-service", concreteWallId);
        l36Purple = L36Block("l36-wall-purple", l36Panel);
        l36Stainless = L36Block("l36-wall-stainless", l36Panel);
        l36TileFloor = l36WallTile;
        l36CeilSteel = L36Block("l36-ceiling-steel", concreteCeilingId);
        l36CeilTile = L36Block("l36-ceiling-tile", ceilingTileId);
        l36CeilDark = L36Block("l36-ceiling-dark", concreteCeilingId);
        l36CeilCabin = L36Block("l36-ceiling-cabin", l36CeilTile);
        string[] states = { "on", "lit", "flicker", "off" };
        int[] lights = { lightOnId, lightLitId, lightFlickerId, lightOffId };
        for (int i = 0; i < 4; i++) l36Light[i] = L36Block("l36-light-" + states[i], lights[i]);
        l36LightHigh = L36Block("l36-light-high", l36Light[0]);
        l36Glass = L36Block("l3999-glass-clear", l36Plaster);
        l36Island = L36Block("l36-carousel-island");
        l36Trays = L36Block("l36-trays");
        l36Bin = L36Block("l3999-trashbin");
        l36Planter = L36Block("l3999-planter");
        string[] meals = { "tray", "cups", "plate", "clean" }, meeting = { "base", "mid", "top" }, belts = { "none", "north", "east", "south", "west" };
        for (int i = 0; i < 4; i++) l36Meal[i] = L36Block("l36-mealtable-" + meals[i]);
        for (int i = 0; i < 3; i++) l36Meeting[i] = L36Block("l36-meetingpoint-" + meeting[i]);
        for (int i = 0; i < 5; i++) l36Stanchion[i] = L36Block("l36-stanchion-" + belts[i]);
        string[] rows = { "low", "mid", "horizon", "sky" }, cabin = { "plain", "window", "bin" }, seats = { "blue", "grey", "coat", "bag" },
            booth = { "desk", "rack", "signl", "signm", "signr" }, parts = { "l", "m", "r" }, halves = { "l", "r" };
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f], dir = L36Dirs[f];
            l36BeltRun[f] = L36Block($"l36-belt-run-{dir}", l36Marble[1]);
            l36BeltStill[f] = L36Block($"l36-belt-still-{dir}", l36Marble[1]);
            l36Walk[f] = L36Block($"l3999-walkway-{dir}", l36BeltRun[f]);
            l36WalkEnd[f] = L36Block($"l3999-walkwayend-{dir}", l36Marble[1]);
            l36Flap[f] = L36Block($"l36-carousel-flap-{side}", l36Panel);
            l36Door[f] = L36Block($"l36-gatedoor-lower-{side}", l36Panel);
            l36Door[4 + f] = L36Block($"l36-gatedoor-upper-{side}", l36Panel);
            l36GateDesk[f] = L36Block($"l36-gatedesk-{side}");
            l36Scanner[f] = L36Block($"l36-scanner-lower-{side}");
            l36Scanner[4 + f] = L36Block($"l36-scanner-upper-{side}");
            l36Xray[f] = L36Block($"l36-xray-body-{side}");
            l36Xray[4 + f] = L36Block($"l36-xray-belt-{side}");
            l36Perfume[f] = L36Block($"l36-perfume-{side}");
            l36CabinSeat[f] = L36Block($"l36-cabinseat-{side}");
            l36LostFound[f] = L36Block($"l36-lostfound-{side}");
            l36Couch[f] = L36Block($"l3999-couch-left-{side}");
            l36Couch[4 + f] = L36Block($"l3999-couch-right-{side}");
            l36Shutter[f] = L36Block($"l3999-shutter-lower-{side}", l36Panel);
            l36Shutter[4 + f] = L36Block($"l3999-shutter-upper-{side}", l36Panel);
            for (int i = 0; i < 4; i++) l36Window[i, f] = L36Block($"l36-window-{rows[i]}-{side}", l36Plaster);
            l36Clock[0, f] = L36Block($"l36-wallclock-nohands-{side}", l36Panel);
            l36Clock[1, f] = L36Block($"l36-wallclock-stopped-{side}", l36Panel);
            for (int i = 0; i < 3; i++) l36CabinWall[i, f] = L36Block($"l36-cabinwall-{cabin[i]}-{side}", l36Plaster);
            l36Checkin[0, f] = L36Block($"l36-checkin-desk-{side}");
            l36Checkin[1, f] = L36Block($"l36-checkin-scale-{side}");
            for (int i = 0; i < 4; i++) l36Seat[i, f] = L36Block($"l36-seat-{seats[i]}-{side}");
            for (int i = 0; i < 5; i++) l36Booth[i, f] = L36Block($"l36-booth-{booth[i]}-{side}");
            for (int g = 0; g < 86; g++) l36GateSign[g, f] = L36Block($"l36-gatesign-{(g < 26 ? ((char)('a' + g)).ToString() : (g - 25).ToString())}-{side}");
            for (int g = 0; g < L36.L36SignGlyphs.Length; g++) l36Sign[g, f] = L36Block($"l36-sign-{L36.L36SignGlyphs[g]}-{side}");
            for (int t = 0; t < L36.L36FidsTexts.Length; t++)
                for (int h = 0; h < 2; h++) l36Fids[t, h, f] = L36Block($"l36-fids-{L36.L36FidsTexts[t]}-{halves[h]}-{side}");
            for (int s = 0; s < L36.L36Shops.Length; s++)
                for (int p = 0; p < 3; p++) l36ShopSign[s, p, f] = L36Block($"l36-shopsign-{L36.L36Shops[s]}-{parts[p]}-{side}", l36Panel);
        }
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level36Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < 0) return concreteId;
        bool stat = (t.Detail & L36.L36StaticBit) != 0;
        int noise = (int)((uint)(gx * 73856093 ^ gz * 19349663 ^ rel * 83492791) % 4);
        if (t.Kind != TileKind.Floor)
        {
            // The region's rim (no zone of ours): the Absolute Limit, static from the floor to well over any ceiling
            if (t.Zone == 0) return rel <= 15 ? l36Static[noise] : concreteId;
            int high = t.Height > 0 ? t.Height : 9;
            if (rel == 0 || rel > high) return concreteId;
            return stat ? l36Static[noise] : L36Wall(t, rel);
        }
        int air = t.Height > 0 ? t.Height : 4;
        if (rel == 0) return stat ? l36Static[noise] : L36Floor(t);
        if (rel == air + 1) return stat ? l36Static[noise] : L36Ceiling(t);
        if (rel > air + 1)
        {
            // Over a low opening between taller rooms: the wall it is cut in (a shop's fascia over its way in)
            if (rel > 15) return concreteId;
            if (t.Zone == (byte)Zone.Shop && t.Roof > 0 && rel == air + 2) return l36ShopSign[t.Depth % 8, (t.Roof - 1) % 3, Facing(t.Pier)];
            return t.Zone is (byte)Zone.Service or (byte)Zone.Vent ? l36Service : t.Zone is (byte)Zone.Shop or (byte)Zone.Lounge ? l36Plaster
                : t.Zone == (byte)Zone.Booth ? l36Purple : l36Panel;
        }
        if (t.SupplyBox) return rel == 1 ? BoxOf(t) : 0;
        if (rel == air && t.Overhead != 0)
        {
            int f = Facing(t.Pier);
            switch (t.Overhead)
            {
                case Overheads.L36GateSign: return l36GateSign[t.Depth % 86, f];
                case Overheads.L36Sign: return l36Sign[t.Depth % 13, f];
                case Overheads.L36Fids: return l36Fids[t.Depth % 6, t.Roof & 1, f];
                case Overheads.L36BoothSign: return l36Booth[2 + t.Roof % 3, f];
            }
        }
        return t.Variant == 0 ? 0 : L36Prop(t, rel);
    }

    private int L36Floor(in Tile t)
    {
        int f = Facing(t.Pier);
        return (t.Detail & L36.L36MatMask) switch
        {
            Mat.Marble => l36Marble[0],
            Mat.MarbleGrey => l36Marble[1],
            Mat.MarbleDark => l36Marble[2],
            Mat.CarpetBlue => l36Carpet[0],
            Mat.CarpetTeal => l36Carpet[1],
            Mat.CarpetRed => l36Carpet[2],
            Mat.CarpetGrey => l36Carpet[3],
            Mat.Concrete => l36Concrete,
            Mat.TileFloor => l36TileFloor,
            Mat.BeltRun => l36BeltRun[f],
            Mat.BeltStill => l36BeltStill[f],
            // (a comb plate ramps up toward the floor beyond it: the way the walkway runs at its far end, back at its start)
            Mat.Travelator => (t.Stack & 1) == 0 ? l36Walk[f] : l36WalkEnd[(t.Stack & 8) != 0 ? Facing(Opposite(t.Pier)) : f],
            Mat.TravelatorStill => (t.Stack & 1) == 0 ? l36BeltStill[f] : l36WalkEnd[(t.Stack & 8) != 0 ? Facing(Opposite(t.Pier)) : f],
            _ => l36Marble[0],
        };
    }

    private int L36Ceiling(in Tile t)
    {
        switch (t.Ceiling)
        {
            // (the halls seven high and more take the brighter panel, so their floors are lit evenly)
            case CeilingKind.LightOn: return t.Height >= 7 ? l36LightHigh : l36Light[0];
            case CeilingKind.LightLit: return l36Light[1];
            case CeilingKind.LightFlicker: return l36Light[2];
            case CeilingKind.LightOff: return l36Light[3];
        }
        return t.Zone switch
        {
            (byte)Zone.Restroom or (byte)Zone.Lounge or (byte)Zone.Shop or (byte)Zone.LostFound or (byte)Zone.Booth or (byte)Zone.Bridge => l36CeilTile,
            (byte)Zone.Service or (byte)Zone.Vent => l36CeilDark,
            (byte)Zone.Cabin => l36CeilCabin,
            _ => l36CeilSteel,
        };
    }

    /// <summary>A wall, by its material, <paramref name="rel"/> above the floor (its features on its <see cref="Tile.Pier"/> face).</summary>
    private int L36Wall(in Tile t, int rel)
    {
        int f = Facing(t.Pier);
        int panel = rel == 1 ? l36Kick : l36Panel;
        int window = l36Window[rel <= 1 ? 0 : rel == 2 ? 1 : rel == 3 ? 2 : 3, f];
        return (t.Detail & L36.L36MatMask) switch
        {
            Mat.Plaster => l36Plaster,
            Mat.WallTile => l36WallTile,
            Mat.Service => l36Service,
            Mat.Purple => l36Purple,
            Mat.Glass => rel <= 5 ? l36Glass : l36Plaster,
            Mat.Stainless => l36Stainless,
            Mat.Window => window,
            Mat.GateDoor => rel == 1 ? l36Door[f] : rel == 2 ? l36Door[4 + f] : window,
            Mat.Flap => rel == 1 ? l36Flap[f] : panel,
            Mat.Clock => rel == 4 ? l36Clock[t.Stack & 1, f] : panel,
            Mat.ShopSign => rel == 5 && t.Roof > 0 ? l36ShopSign[t.Depth % 8, (t.Roof - 1) % 3, f] : panel,
            Mat.Shutter => rel == 1 ? l36Shutter[f] : rel == 2 ? l36Shutter[4 + f] : t.Roof > 0 && rel == 7 ? l36ShopSign[t.Depth % 8, (t.Roof - 1) % 3, f] : l36Plaster,
            Mat.CabinWall => l36CabinWall[rel <= 1 ? 0 : rel == 2 ? 1 : 2, f],
            _ => panel,
        };
    }

    private int L36Prop(in Tile t, int rel)
    {
        int f = Facing(t.Pier);
        switch (t.Variant)
        {
            case Props.L36Scanner: return rel <= 2 ? l36Scanner[(rel - 1) * 4 + f] : 0;
            case Props.L36MeetingPoint: return rel <= 3 ? l36Meeting[rel - 1] : 0;
        }
        if (rel != 1) return 0;
        return t.Variant switch
        {
            Props.L36Checkin => l36Checkin[t.Stack & 1, f],
            Props.L36Seat => l36Seat[t.Stack & 3, f],
            Props.L36GateDesk => l36GateDesk[f],
            Props.L36Stanchion => l36Stanchion[System.Math.Min((int)t.Stack, 4)],
            Props.L36Xray => l36Xray[(t.Stack & 1) * 4 + f],
            Props.L36Trays => l36Trays,
            Props.L36Booth => l36Booth[t.Stack & 1, f],
            Props.L36Perfume => l36Perfume[f],
            Props.L36MealTable => l36Meal[t.Stack & 3],
            Props.L36CabinSeat => l36CabinSeat[f],
            Props.L36LostFound => l36LostFound[f],
            Props.L36CarouselIsland => l36Island,
            Props.L36Couch => l36Couch[(t.Stack & 1) * 4 + f],
            Props.L36Planter => l36Planter,
            Props.L36Bin => l36Bin,
            Props.Vending => vendingIds[f],
            Props.Cooler => coolerIds[f],
            Props.Shelf => shelfIds[Facing(Opposite(t.Pier))],
            >= 40 and < Props.L36First => PropBlock(t),
            _ => 0,
        };
    }
}
