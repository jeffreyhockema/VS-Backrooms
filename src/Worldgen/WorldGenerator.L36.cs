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
        l36Couch = new int[8], l36Shutter = new int[8], l36AirDoor = new int[8], l36AirSign = new int[4], l36Sink = new int[4];
    private readonly int[,] l36Window = new int[4, 4], l36Clock = new int[2, 4], l36CabinWall = new int[3, 4], l36Checkin = new int[2, 4],
        l36Seat = new int[4, 4], l36Booth = new int[5, 4], l36GateSign = new int[86, 4], l36Sign = new int[L36.L36SignGlyphs.Length, 4];
    private readonly int[,,] l36Fids = new int[L36.L36FidsTexts.Length, 2, 4], l36ShopSign = new int[L36.L36Shops.Length, 3, 4];
    // (round 3) the wall pictures, the plane at the gate, the column posters, the meeting-point sign, finishes, new props
    private readonly int[,,,] l36Art = new int[L36.L36ArtKinds.Length, 4, 2, 4];
    private readonly int[,,] l36Apron = new int[9, 5, 4];
    private readonly int[,] l36ColPoster = new int[4, 2], l36MeetBox = new int[4, 2], l36MeetPost = new int[2, 4], l36Stall = new int[2, 4];
    private readonly int[] l36Gondola = new int[4], l36Phone = new int[4], l36Atm = new int[4], l36Fountain = new int[4], l36ShoeShine = new int[4];
    private int l36Coffer, l36Wood, l36Stone, l36StoneTop, l36Skylight, l36Charger;
    // (round 4) the space frame, the columns' plinths and capitals, the carousel island's rim, the jet bridge, new props
    private readonly int[] l36Frame = new int[4], l36ColFoot = new int[4], l36ColHead = new int[4], l36Coffee = new int[4], l36Pastry = new int[4],
        l36Till = new int[4], l36Trolley = new int[4];
    private readonly int[,] l36IslandRim = new int[2, 4], l36BridgeWall = new int[3, 4];
    private int l36BridgeFloor, l36BridgeCeil, l36Stool, l36Canopy;
    private readonly int[,] l36Gallery = new int[2, 4], l36FrameLight = new int[4, 4];
    private readonly int[] l36MagRack = new int[4], l36FireCab = new int[4], l36InfoPylon = new int[4];
    private readonly int[,] l36PrayerMat = new int[2, 4], l36Luggage = new int[5, 4];
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
        // (round 3)
        l36Coffer = L36Block("l36-finish-coffer", l36CeilSteel);
        l36Wood = L36Block("l36-finish-wood", l36CeilTile);
        l36Stone = L36Block("l36-finish-stone", l36Panel);
        l36StoneTop = L36Block("l36-finish-stonetop", l36Panel);
        l36Skylight = L36Block("l36-finish-skylight", l36CeilTile);
        l36Charger = L36Block("l36-charger");
        // (round 4)
        string[] parity = { "ee", "oe", "eo", "oo" }, quarters = { "nw", "ne", "sw", "se" }, bridgeParts = { "lower", "glass", "upper" };
        for (int i = 0; i < 4; i++)
        {
            l36Frame[i] = L36Block("l36-frame-" + parity[i], l36CeilSteel);
            string[] lightStates = { "on", "high", "lit", "off" };
            for (int k = 0; k < 4; k++) l36FrameLight[i, k] = L36Block($"l36-framelight-{parity[i]}-{lightStates[k]}", l36Light[0]);
            l36ColFoot[i] = L36Block("l36-colfoot-" + quarters[i], l36Panel);
            l36ColHead[i] = L36Block("l36-colhead-" + quarters[i], l36Panel);
        }
        l36BridgeFloor = L36Block("l36-bridgefloor", l36Carpet[3]);
        l36BridgeCeil = L36Block("l36-bridgeceil", l36CeilTile);
        l36Stool = L36Block("l36-stool");
        l36Canopy = L36Block("l36-canopy", l36Purple);
        string[] quads = { "nw", "ne", "sw", "se" }, colPosters = { "p0", "p3", "p5", "p6" }, boxRows = { "lower", "upper" };
        for (int q = 0; q < 4; q++)
        {
            for (int r = 0; r < 2; r++) l36MeetBox[q, r] = L36Block("l36-meetbox-" + quads[q] + "-" + boxRows[r], l36Purple);
            l36MeetPost[0, q] = L36Block("l36-meetpost-base-" + quads[q]);
            l36MeetPost[1, q] = L36Block("l36-meetpost-pole-" + quads[q]);
            for (int r = 0; r < 2; r++) l36ColPoster[q, r] = L36Block("l36-colposter-" + colPosters[q] + "-" + r, l36Panel);
        }
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
            // (links) The door under the airplane sign, in the baggage wall and in Levels 9 and 11; the restroom sink
            l36AirDoor[f] = L36Block($"l36-airportdoor-lower-{side}", l36Panel);
            l36AirDoor[4 + f] = L36Block($"l36-airportdoor-upper-{side}", l36Panel);
            l36AirSign[f] = L36Block($"l36-airportsign-{side}", l36Panel);
            l36Sink[f] = L36Block($"l36-sink-dry-{side}");
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
            // (round 3)
            for (int k = 0; k < L36.L36ArtKinds.Length; k++)
                for (int c = 0; c < L36.L36ArtCols[k]; c++)
                    for (int r = 0; r < L36.L36ArtRows[k]; r++) l36Art[k, c, r, f] = L36Block($"l36-art-{L36.L36ArtKinds[k]}-{c}-{r}-{side}", l36Panel);
            for (int c = 0; c < 9; c++)
                for (int r = 0; r < 5; r++) l36Apron[c, r, f] = L36Block($"l36-apron-{c}-{r}-{side}", l36Window[System.Math.Min(r, 3), f]);
            l36Phone[f] = L36Block($"l36-payphone-{side}");
            l36Gondola[f] = L36Block($"l36-gondola-{side}");
            l36Atm[f] = L36Block($"l36-atm-{side}");
            l36Fountain[f] = L36Block($"l36-fountain-{side}", coolerIds[f]);
            l36ShoeShine[f] = L36Block($"l36-shoeshine-{side}");
            l36Stall[0, f] = L36Block($"l36-stall-lower-{side}");
            l36Stall[1, f] = L36Block($"l36-stall-upper-{side}");
            // (round 4)
            l36IslandRim[0, f] = L36Block($"l36-carousel-island-edge-{side}", l36Island);
            l36IslandRim[1, f] = L36Block($"l36-carousel-island-corner-{side}", l36Island);
            for (int i = 0; i < 3; i++) l36BridgeWall[i, f] = L36Block($"l36-bridge-{bridgeParts[i]}-{side}", l36Stainless);
            l36Coffee[f] = L36Block($"l36-coffee-{side}");
            l36Pastry[f] = L36Block($"l36-pastry-{side}");
            l36Till[f] = L36Block($"l36-till-{side}");
            l36Trolley[f] = L36Block($"l36-trolley-{side}");
            l36Gallery[0, f] = L36Block($"l36-gallery-lip-{side}", l36Panel);
            l36Gallery[1, f] = L36Block($"l36-gallery-glass-{side}", l36Panel);
            l36MagRack[f] = L36Block($"l36-magrack-{side}");
            l36InfoPylon[f] = L36Block($"l36-infopylon-{side}");
            l36PrayerMat[0, f] = L36Block($"l36-prayermat-laid-{side}");
            l36PrayerMat[1, f] = L36Block($"l36-prayermat-rolled-{side}");
            string[] bags = { "spin0", "spin1", "duffel", "garment", "upright" };
            for (int i = 0; i < 5; i++) l36Luggage[i, f] = L36Block($"l36-luggage-{bags[i]}-{side}");
            l36FireCab[f] = L36Block($"l36-firecab-{side}", l36Stone);
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
            if (stat) return l36Static[noise];
            // (round 4) A column's foot and head; the jet bridge's walls, faced toward the bridge
            if (t.Overhead == Overheads.L36Art && t.Roof == L36.L36OnAllFaces && (rel == 1 || rel == high))
            {
                int quad = L36ColumnQuad(gx, gz);
                if (quad >= 0) return rel == 1 ? l36ColFoot[quad] : l36ColHead[quad];
            }
            // (round 4) The gallery round the tall halls: a slab edge with its balustrade at 7, the upper level's glazing over it
            if (rel is >= 7 and <= 9 && high >= 9 && (t.Detail & L36.L36StoneBit) != 0 && t.Overhead == 0)
            {
                int face = L36HallFace(gx, gz, high);
                if (face >= 0) return l36Gallery[rel == 7 ? 0 : 1, face];
            }
            // (round 4) A fire cabinet in the travertine dado of a public hall's wall, about one wall block in forty
            if (rel == 2 && (t.Detail & L36.L36StoneBit) != 0 && t.Overhead == 0 && (t.Detail & L36.L36MatMask) == Mat.Panel
                && Hashing.Mod((int)(Hashing.Hash(seed, gx, gz, 0x2540) & 0x7fffffff), 40) == 0)
            {
                int face = L36HallFace(gx, gz, 1);
                if (face >= 0) return l36FireCab[face];
            }
            if ((t.Detail & L36.L36MatMask) == Mat.Stainless && rel <= 3)
            {
                int face = L36BridgeFace(gx, gz);
                if (face >= 0) return l36BridgeWall[rel - 1, face];
            }
            return L36Wall(t, rel);
        }
        int air = t.Height > 0 ? t.Height : 4;
        if (rel == 0) return stat ? l36Static[noise] : L36FloorAt(t, gx, gz);
        if (rel == air + 1) return stat ? l36Static[noise] : L36CeilingAt(t, gx, gz);
        if (rel > air + 1)
        {
            // Over a low opening between taller rooms: the wall it is cut in (a shop's fascia over its way in)
            if (rel > 15) return concreteId;
            // (round 3) A kiosk's canopy is five high in a taller hall: open air over it, up to the hall's own (coffered) ceiling
            if (t.Zone == (byte)Zone.Booth)
            {
                int hall = gx - layout.L36WallX < L36.L36Airside ? 9 : 14;
                return rel <= hall ? 0 : rel == hall + 1 ? l36Coffer : concreteId;
            }
            if (t.Zone == (byte)Zone.Shop && t.Roof > 0 && rel == air + 2) return l36ShopSign[t.Depth % L36.L36Shops.Length, (t.Roof - 1) % 3, Facing(t.Pier)];
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
                case Overheads.L36Sign: return l36Sign[t.Depth % L36.L36SignGlyphs.Length, f];
                case Overheads.L36Fids: return l36Fids[t.Depth % L36.L36FidsTexts.Length, t.Roof & 1, f];
                case Overheads.L36BoothSign: return l36Booth[2 + t.Roof % 3, f];
            }
        }
        if (t.Variant == Props.L36CarouselIsland) return rel == 1 ? L36IslandAt(gx, gz) : 0;
        return t.Variant == 0 ? 0 : L36Prop(t, rel);
    }

    /// <summary>(round 4) The floor, with the jet bridge's rubber and, across the claim hall and check-in, a charcoal inlay band on
    /// every module line and every eighth row, so the white field breaks into bays.</summary>
    private int L36FloorAt(in Tile t, int gx, int gz)
    {
        if (t.Zone == (byte)Zone.Bridge) return l36BridgeFloor;
        if ((t.Detail & L36.L36MatMask) == Mat.Marble && t.Zone is (byte)Zone.Baggage or (byte)Zone.CheckIn)
        {
            int u = gx - layout.L36WallX, k = Hashing.Mod(gz - layout.L36LineZ, 16);
            if (k == 8 || Hashing.Mod(u, 8) == 5) return l36Marble[2];
        }
        return L36Floor(t);
    }

    /// <summary>(round 4) The ceiling: the space frame over the big halls (not where lights, coffers or skylights are laid out).</summary>
    private int L36CeilingAt(in Tile t, int gx, int gz)
    {
        if (t.Zone == (byte)Zone.Bridge) return t.Ceiling == CeilingKind.L36Ceiling || t.Ceiling == 0 ? l36BridgeCeil : L36Ceiling(t);
        int c = L36Ceiling(t);
        if (t.Zone is (byte)Zone.Baggage or (byte)Zone.Concourse or (byte)Zone.Pier or (byte)Zone.FoodCourt or (byte)Zone.Street)
        {
            int q = (gx & 1) + 2 * (gz & 1);
            if (c == l36CeilSteel) return l36Frame[q];
            // the panels as pendants hung from the frame
            if (c == l36Light[0]) return l36FrameLight[q, 0];
            if (c == l36LightHigh) return l36FrameLight[q, 1];
            if (c == l36Light[1]) return l36FrameLight[q, 2];
            if (c == l36Light[3]) return l36FrameLight[q, 3];
        }
        return c;
    }

    /// <summary>(round 4) Which corner of a 2 x 2 column a wall tile is (0 nw, 1 ne, 2 sw, 3 se), from its neighbours; -1 if it is not one.</summary>
    private int L36ColumnQuad(int gx, int gz)
    {
        static bool Col(in Tile n) => n.Kind != TileKind.Floor && n.Overhead == Overheads.L36Art && n.Roof == L36.L36OnAllFaces;
        bool e = Col(layout.TileAt(gx + 1, gz)), w = Col(layout.TileAt(gx - 1, gz)), s = Col(layout.TileAt(gx, gz + 1)), n = Col(layout.TileAt(gx, gz - 1));
        if (e == w || n == s) return -1;
        return (e ? 0 : 1) + (s ? 0 : 2);
    }

    /// <summary>(round 4) The face of a hall's wall toward a hall at least <paramref name="high"/> tall (a facing index), or -1 (none, or more than one).</summary>
    private int L36HallFace(int gx, int gz, int high)
    {
        static bool Hall(in Tile n, int h) => n.Kind == TileKind.Floor && n.Height >= h && n.Zone is (byte)Zone.Concourse or (byte)Zone.CheckIn
            or (byte)Zone.Meeting or (byte)Zone.Junction or (byte)Zone.Pier or (byte)Zone.Street;
        int face = -1, count = 0;
        if (Hall(layout.TileAt(gx, gz - 1), high)) { face = Facing(ArchPier.North); count++; }
        if (Hall(layout.TileAt(gx + 1, gz), high)) { face = Facing(ArchPier.East); count++; }
        if (Hall(layout.TileAt(gx, gz + 1), high)) { face = Facing(ArchPier.South); count++; }
        if (Hall(layout.TileAt(gx - 1, gz), high)) { face = Facing(ArchPier.West); count++; }
        return count == 1 ? face : -1;
    }

    /// <summary>(round 4) The face of a jet-bridge wall toward the bridge (a facing index), or -1 (a corner, or no bridge beside it).</summary>
    private int L36BridgeFace(int gx, int gz)
    {
        static bool Br(in Tile n) => n.Kind == TileKind.Floor && n.Zone == (byte)Zone.Bridge;
        if (Br(layout.TileAt(gx, gz - 1))) return Facing(ArchPier.North);
        if (Br(layout.TileAt(gx + 1, gz))) return Facing(ArchPier.East);
        if (Br(layout.TileAt(gx, gz + 1))) return Facing(ArchPier.South);
        if (Br(layout.TileAt(gx - 1, gz))) return Facing(ArchPier.West);
        return -1;
    }

    /// <summary>(round 4) A carousel island's block: its rim (edge or corner) where the belt runs beside it, the deck inside.</summary>
    private int L36IslandAt(int gx, int gz)
    {
        // (the wall the island runs into counts as island: no bumper against it)
        static bool Isl(in Tile n) => n.Kind != TileKind.Floor || n.Variant == Props.L36CarouselIsland;
        bool n = !Isl(layout.TileAt(gx, gz - 1)), e = !Isl(layout.TileAt(gx + 1, gz)), s = !Isl(layout.TileAt(gx, gz + 1)), w = !Isl(layout.TileAt(gx - 1, gz));
        int open = (n ? 1 : 0) + (e ? 1 : 0) + (s ? 1 : 0) + (w ? 1 : 0);
        if (open == 1) return l36IslandRim[0, Facing(n ? ArchPier.North : e ? ArchPier.East : s ? ArchPier.South : ArchPier.West)];
        if (open == 2 && n != s)
            // a corner: the belt to <side> and the side clockwise from it
            return l36IslandRim[1, Facing(n && e ? ArchPier.North : e && s ? ArchPier.East : s && w ? ArchPier.South : ArchPier.West)];
        return l36Island;
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
            // (round 3)
            case CeilingKind.L36Coffer: return l36Coffer;
            case CeilingKind.L36Skylight: return l36Skylight;
            case CeilingKind.L36Wood: return l36Wood;
        }
        return t.Zone switch
        {
            (byte)Zone.CheckIn or (byte)Zone.Junction or (byte)Zone.Meeting => l36Coffer,
            (byte)Zone.Lounge => l36Wood,
            // (round 3: a kiosk's canopy purple, as its walls)
            (byte)Zone.Booth => l36Canopy,
            (byte)Zone.Restroom or (byte)Zone.Lounge or (byte)Zone.Shop or (byte)Zone.LostFound or (byte)Zone.Bridge => l36CeilTile,
            (byte)Zone.Service or (byte)Zone.Vent => l36CeilDark,
            (byte)Zone.Cabin => l36CeilCabin,
            _ => l36CeilSteel,
        };
    }

    /// <summary>A wall, by its material, <paramref name="rel"/> above the floor (its features on its <see cref="Tile.Pier"/> face).</summary>
    private int L36Wall(in Tile t, int rel)
    {
        int f = Facing(t.Pier);
        // (round 3) A picture on the wall's face; on a column, a poster on all its faces
        if (t.Overhead == Overheads.L36Art)
        {
            int k = t.Depth % L36.L36ArtKinds.Length, row = rel - t.Stack;
            if (row >= 0 && row < L36.L36ArtRows[k])
            {
                if (t.Roof == L36.L36OnAllFaces) return l36ColPoster[System.Math.Max(0, System.Array.IndexOf(L36.L36ColumnPosters, (byte)k)), row];
                return l36Art[k, t.Roof % L36.L36ArtCols[k], row, f];
            }
        }
        int panel = (t.Detail & L36.L36StoneBit) != 0 && rel <= 3 ? (rel == 3 ? l36StoneTop : l36Stone) : rel == 1 ? l36Kick : l36Panel;
        int window = t.Overhead == Overheads.L36Apron && rel <= 5 ? l36Apron[t.Roof % 9, rel - 1, f] : l36Window[rel <= 1 ? 0 : rel == 2 ? 1 : rel == 3 ? 2 : 3, f];
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
            Mat.LandDoor => rel == 1 ? l36AirDoor[f] : rel == 2 ? l36AirDoor[4 + f] : rel == 3 ? l36AirSign[f] : l36Panel,
            _ => panel,
        };
    }

    private int L36Prop(in Tile t, int rel)
    {
        int f = Facing(t.Pier);
        switch (t.Variant)
        {
            case Props.L36Scanner: return rel <= 2 ? l36Scanner[(rel - 1) * 4 + f] : 0;
            // (round 3: the meeting-point sign, a lit cube on a post, a quarter of it in each of four blocks)
            // (round 4: the post up to seven, the cube at eight and nine, so it reads across the 14-high atrium)
            case Props.L36MeetingPoint: return rel == 1 ? l36MeetPost[0, t.Stack & 3] : rel <= 7 ? l36MeetPost[1, t.Stack & 3] : rel <= 9 ? l36MeetBox[t.Stack & 3, rel - 8] : 0;
            case Props.L36KioskWall:
                if (rel > 5) return 0;
                if (t.Stack > 0 && rel is 2 or 3) return l36Art[(t.Stack - 1) % L36.L36ArtKinds.Length, 0, rel - 2, f];
                return l36Purple;
            case Props.L36Stall: return rel <= 2 ? l36Stall[rel - 1, f] : 0;
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
            Props.L36Sink => l36Sink[f],
            Props.L36Charger => l36Charger,
            Props.L36Phone => l36Phone[f],
            Props.L36Gondola => l36Gondola[f],
            Props.L36Atm => l36Atm[f],
            Props.L36Fountain => l36Fountain[f],
            Props.L36ShoeShine => l36ShoeShine[f],
            Props.L36Coffee => l36Coffee[f],
            Props.L36Pastry => l36Pastry[f],
            Props.L36Till => l36Till[f],
            Props.L36Stool => l36Stool,
            Props.L36Trolley => l36Trolley[f],
            Props.L36MagRack => l36MagRack[f],
            Props.L36PrayerMat => l36PrayerMat[t.Stack & 1, f],
            Props.L36InfoPylon => l36InfoPylon[f],
            Props.L36Luggage => l36Luggage[t.Stack % 5, f],
            Props.Vending => vendingIds[f],
            Props.Cooler => coolerIds[f],
            Props.Shelf => shelfIds[Facing(Opposite(t.Pier))],
            >= 40 and < Props.L36First => PropBlock(t),
            _ => 0,
        };
    }
}
