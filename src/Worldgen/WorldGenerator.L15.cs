using System;
using System.Collections.Generic;
using L = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 15, "Futuristic Halls" (experimental, kept as level 27), laid out in WorldLayout.Level15.cs, from its own
/// floor (<see cref="WorldGeometry.FloorFor"/>). White panelled walls (<c>l15-wall</c>) with steel pilasters, a skirting row
/// and, in the service passages, bare grey concrete; ceramic floors (<c>l15-floor</c>: worn, coated, carpeted, steel grating,
/// the halls' glowing foot strips, dried blood, scorch, a gate's track, dust); LED ceiling panels (<c>l15-ceiling</c>: giving
/// light, only looking lit, failing, dead; the service passages' concrete, an air handler's grille); steel ribs
/// (<c>l15-rib</c>) under the ceilings and now and then one set in at an angle (<c>l15-oddbeam</c>). On the walls
/// (<c>l15-walldeco</c>, one face dressed): hand scanners, room codes, displays (dead, the radar, the ESCAPE panel, views of
/// elsewhere), vent grilles, a wooden door, blood; thick glass (<c>l15-glass</c>) into the machine rooms, a security gate's
/// rolled-up shutter (<c>l15-gate</c>) over their doors. Machines are stacks of casing blocks (<c>l15-machine</c>: panels,
/// vents, screens and lamp banks dead or lit, hatches, burnt, an incinerator's mouth, a press); props: consoles, lab benches,
/// lockers, the dead, steel rods, the lecture stage, the star door. Everything above the rooms is solid to the top of the band.
///
/// Every block of the level's own is looked up softly (<see cref="L15Block"/>): until its asset exists, what is missing is
/// drawn as the nearest existing block or left out, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L15WallKinds =
        { "panel", "panelb", "base", "grey", "greybase", "scorched", "beam", "etched", "cast", "castbase", "tile", "tilebase", "jamb", "jambdead", "lintel", "linteldead" };
    private const int L15WCast = 8, L15WCastBase = 9, L15WTile = 10, L15WTileBase = 11, L15WJamb = 12, L15WJambDead = 13, L15WLintel = 14, L15WLintelDead = 15;
    private static readonly string[] L15FloorKinds = { "ceramic", "worn", "coating", "carpet", "grating", "strip", "blood", "scorch", "track", "dust", "stripdead",
        "vinyl", "terrazzo" };
    private static readonly string[] L15MachineKinds = { "panel", "vent", "screen", "screenlit", "lights", "lightslit", "hatch", "warning", "burnt", "burntvent", "furnace", "press" };
    private const int L15MPanel = 0, L15MVent = 1, L15MScreen = 2, L15MScreenLit = 3, L15MLights = 4, L15MLightsLit = 5, L15MHatch = 6, L15MWarning = 7,
        L15MBurnt = 8, L15MBurntVent = 9, L15MFurnace = 10, L15MPress = 11;
    /// <summary>The wall decorations, by name (<c>l15-walldeco-{kind}-{side}</c>): their index in <see cref="l15Deco"/>.</summary>
    private static readonly string[] L15DecoKinds = BuildL15DecoKinds();
    private const int L15DScanner = 0, L15DDisplay = 1, L15DRadar = 2, L15DEscape = 3, L15DVent = 4, L15DVentCode = 5, L15DDoorLower = 6, L15DDoorUpper = 7,
        L15DBlood = 8, L15DBand = 9, L15DCornice = 10, L15DLampLower = 11, L15DLampUpper = 12, L15DLampOn = 13, L15DLampLowerDead = 14,
        L15DLampUpperDead = 15, L15DView = 16, L15DCode = 16 + L.L15Views, L15DSign = 16 + L.L15Views + L.L15Codes;
    /// <summary>How many hall signs there are (<c>l15-walldeco-sign{n}</c>).</summary>
    private const int L15Signs = 8;

    private static string[] BuildL15DecoKinds()
    {
        var kinds = new List<string> { "scanner", "display", "radar", "escape", "vent", "ventcode", "wooddoorlower", "wooddoorupper", "blood",
            "band", "cornice", "lamplower", "lampupper", "lampon", "lamplowerdead", "lampupperdead" };
        for (int i = 0; i < L.L15Views; i++) kinds.Add("view" + i);
        for (int i = 0; i < L.L15Codes; i++) kinds.Add("code" + i);
        for (int i = 0; i < L15Signs; i++) kinds.Add("sign" + i);
        return kinds.ToArray();
    }

    private readonly int[] l15Wall = new int[16], l15Floor = new int[13], l15Machine = new int[12], l15Glass = new int[2], l15Rib = new int[2], l15OddBeam = new int[2];
    private readonly int[] l15Ceiling = new int[9];
    private int l15Gate, l15Stage;
    private readonly int[,] l15Deco = new int[L15DecoKinds.Length, 4];
    private readonly int[,] l15Console = new int[3, 4], l15Bench = new int[4, 4], l15Corpse = new int[6, 4], l15StarDoor = new int[2, 4];
    private readonly int[,,] l15Locker = new int[2, 2, 4];
    private readonly int[] l15Rods = new int[4];
    private readonly HashSet<string> l15Missing = new();

    // ---- Round 3 (tools/gen_15_r3.py) ----
    /// <summary>The name plates' kinds, by the room code's letter (H e M D K C L S F R G: WorldLayout.L15Codes).</summary>
    private static readonly string[] L15PlateKinds = { "lab", "storage", "machine", "dorm", "kitchen", "control", "lecture", "blank", "canteen", "medical", "hydro" };
    /// <summary><c>l15-sign</c>'s kinds: the plates, then the rest by name (their index in <see cref="l15Sign"/>).</summary>
    private static readonly string[] L15SignKinds = BuildL15SignKinds();
    private static readonly int L15SAuth = L15PlateKinds.Length, L15SDecon = L15SAuth + 1, L15SHV = L15SAuth + 2, L15SHatch = L15SAuth + 3,
        L15SPipes = L15SAuth + 4, L15SLiftCall = L15SAuth + 5, L15SLiftInd = L15SAuth + 6, L15SLiftL = L15SAuth + 8, L15SLiftR = L15SAuth + 11,
        L15SMenu = L15SAuth + 14, L15SBand = L15SAuth + 17, L15SBig = L15SAuth + 21, L15SSlide = L15SAuth + 27, L15SMap = L15SAuth + 36, L15SExtinguisher = L15SAuth + 40;
    private readonly int[,] l15Sign = new int[L15SignKinds.Length, 4];
    /// <summary>The halls' floor marks: [colour, line ns, line we, chevron n e s w].</summary>
    private readonly int[,] l15Mark = new int[4, 6];
    /// <summary>The hanging signs: [hall, lit/off, part, axis (we, ns)].</summary>
    private readonly int[,,,] l15Hang = new int[L15Signs, 2, 3, 2];
    private readonly int[,] l15Bunk = new int[2, 4], l15Seat = new int[2, 4], l15Serve = new int[3, 4];
    private readonly int[,,] l15Grow = new int[2, 2, 4], l15Dock = new int[2, 2, 4];
    private readonly int[] l15Riser = new int[2], l15Tray = new int[2];
    private readonly int[,] l15Appliance = new int[2, 4], l15Curtain = new int[2, 4];

    // ---- Round 4 (tools/gen_15_r4.py) ----
    /// <summary><c>l15-panel</c>'s kinds by name (a white wall block with a model on its face): see <see cref="L15Panel"/>.</summary>
    private readonly Dictionary<string, int[]> l15Panel = new();
    /// <summary>The bulkheads' headers [lit/dead, we/ns], the medical monitors [lit/dead, side].</summary>
    private readonly int[,] l15Bulkhead = new int[2, 2], l15MedMon = new int[2, 4];
    /// <summary>The glazing [clear/cracked, lower/upper, we/ns].</summary>
    private readonly int[,,] l15Glazing = new int[2, 2, 2];
    private int l15Stool, l15CTable;
    private readonly int[,] l15Lectern = new int[2, 4], l15Tank = new int[2, 4];
    private readonly int[] l15Projector = new int[4], l15CageLamp = new int[2];

    private static readonly string[] L15PanelKinds = BuildL15PanelKinds();

    private static string[] BuildL15PanelKinds()
    {
        var kinds = new List<string> { "ext", "escape", "liftl0", "liftl1", "liftl2", "liftr0", "liftr1", "liftr2", "liftind0", "liftind1", "liftcall",
            "big00", "big01", "big02", "big10", "big11", "big12", "emerglit", "emergdead", "breaker", "display", "radar", "view0", "view1", "view2",
            "lamplower", "lampupper", "lampon", "lamplowerdead", "lampupperdead" };
        for (int r = 1; r <= 5; r++) { kinds.Add($"jamb{r}"); kinds.Add($"jamb{r}e"); }
        for (int i = 0; i < 4; i++) kinds.Add($"jambplate{i}");
        kinds.Add("scrawl");
        kinds.Add("medheadlit");
        kinds.Add("medheaddead");
        for (int c = 0; c < 4; c++)
            for (int n = 0; n < L15Signs; n++) kinds.Add($"tag{c}{n}");
        return kinds.ToArray();
    }

    /// <summary>Round 4's block ids (called from <see cref="InitL15"/>).</summary>
    private void InitL15Round4()
    {
        foreach (string k in L15PanelKinds)
        {
            var ids = new int[4];
            for (int f = 0; f < 4; f++) ids[f] = L15Block($"l15-panel-{k}-{Sides[f]}");
            l15Panel[k] = ids;
        }
        string[] st = { "lit", "dead" }, ax = { "we", "ns" };
        for (int a = 0; a < 2; a++)
        {
            for (int l = 0; l < 2; l++) l15Bulkhead[l, a] = L15Block($"l15-bulkhead-{st[l]}-{ax[a]}");
            for (int k = 0; k < 2; k++)
                for (int r = 0; r < 2; r++)
                    l15Glazing[k, r, a] = L15Block($"l15-glazing-{(k == 0 ? "clear" : "cracked")}-{(r == 0 ? "lower" : "upper")}-{ax[a]}");
        }
        for (int l = 0; l < 2; l++)
            for (int f = 0; f < 4; f++) l15MedMon[l, f] = L15Block($"l15-medmonitor-{st[l]}-{Sides[f]}");
        l15Stool = L15Block("l15-stool");
        for (int f = 0; f < 4; f++)
        {
            l15Lectern[0, f] = L15Block($"l15-lectern-lit-{Sides[f]}");
            l15Lectern[1, f] = L15Block($"l15-lectern-dead-{Sides[f]}");
            l15Tank[0, f] = L15Block($"l15-tank-lower-{Sides[f]}");
            l15Tank[1, f] = L15Block($"l15-tank-upper-{Sides[f]}");
            l15Projector[f] = L15Block($"l15-projector-{Sides[f]}");
            if (f == 0)
            {
                l15CageLamp[0] = L15Block("l15-cagelamp-lit", lampDimId);
                l15CageLamp[1] = L15Block("l15-cagelamp-dead", lightOffId);
            }
        }
        l15CTable = L15Block("l15-ctable");
    }

    /// <summary>A round-4 wall panel facing <paramref name="f"/>, or <paramref name="fallback"/> where its asset is missing.</summary>
    private int L15Panel(string kind, int f, int fallback) => l15Panel.TryGetValue(kind, out int[] ids) && ids[f] > 0 ? ids[f] : fallback;

    /// <summary>Round 4: a bulkhead crosses a main hall every 32 blocks, on one of its ribs.</summary>
    private static bool L15IsBulkhead(int along) => Hashing.Mod(along, 32) == 16;

    /// <summary>
    /// Round 4: how near the lit side a dark hall wall is, stepping along the hall 8 blocks at a time (1: within 8, 2: 16,
    /// 3: 24; 0 deeper in the dark), so the change from light to dark reads as a power fault (battery lamps, a tripped breaker).
    /// </summary>
    private int L15DarkEdge(int gx, int gz, bool alongZ)
    {
        for (int k = 1; k <= 3; k++)
        {
            int d = 8 * k;
            if (alongZ ? !layout.L15DarkAt(gx, gz + d) || !layout.L15DarkAt(gx, gz - d) : !layout.L15DarkAt(gx + d, gz) || !layout.L15DarkAt(gx - d, gz))
                return k;
        }
        return 0;
    }

    private static string[] BuildL15SignKinds()
    {
        var kinds = new List<string>();
        foreach (string p in L15PlateKinds) kinds.Add("plate" + p);
        kinds.AddRange(new[] { "auth", "decon", "hv", "hatch", "pipes", "liftcall", "liftind0", "liftind1", "liftl0", "liftl1", "liftl2",
            "liftr0", "liftr1", "liftr2", "menu0", "menu1", "menu2", "band0", "band1", "band2", "band3", "big00", "big01", "big02", "big10", "big11", "big12",
            "slide00", "slide01", "slide02", "slide10", "slide11", "slide12", "slide20", "slide21", "slide22",
            "map00", "map01", "map10", "map11", "extinguisher" });
        return kinds.ToArray();
    }

    /// <summary>Round 3's block ids (called from <see cref="InitL15"/>).</summary>
    private void InitL15Round3()
    {
        for (int f = 0; f < 4; f++)
        {
            for (int k = 0; k < L15SignKinds.Length; k++) l15Sign[k, f] = L15Block($"l15-sign-{L15SignKinds[k]}-{Sides[f]}", l15Wall[0]);
            for (int p = 0; p < 2; p++)
            {
                l15Bunk[p, f] = L15Block($"l15-bunk-{(p == 0 ? "head" : "foot")}-{Sides[f]}");
                l15Seat[p, f] = L15Block($"l15-seat-{(p == 0 ? "lo" : "hi")}-{Sides[f]}");
                for (int st = 0; st < 2; st++)
                {
                    l15Grow[p, st, f] = L15Block($"l15-growrack-{(p == 0 ? "lower" : "upper")}-{(st == 0 ? "lit" : "off")}-{Sides[f]}");
                    l15Dock[p, st, f] = L15Block($"l15-dock-{(p == 0 ? "lower" : "upper")}-{(st == 0 ? "lit" : "dead")}-{Sides[f]}");
                }
            }
            l15Appliance[0, f] = L15Block($"l15-appliance-coffee-{Sides[f]}");
            l15Appliance[1, f] = L15Block($"l15-appliance-printer-{Sides[f]}");
            l15Curtain[0, f] = L15Block($"l15-curtain-lower-{Sides[f]}");
            l15Curtain[1, f] = L15Block($"l15-curtain-upper-{Sides[f]}");
            string[] serve = { "wells", "trays", "till" };
            for (int k = 0; k < 3; k++) l15Serve[k, f] = L15Block($"l15-serve-{serve[k]}-{Sides[f]}");
        }
        string[] marks = { "ns", "we", "n", "e", "s", "w" };
        for (int c = 0; c < 4; c++)
            for (int m = 0; m < 6; m++)
                l15Mark[c, m] = L15Block($"l15-floormark-{(m < 2 ? "line" : "chev")}{c}{marks[m]}", l15Floor[0]);
        for (int n = 0; n < L15Signs; n++)
            for (int st = 0; st < 2; st++)
                for (int part = 0; part < 3; part++)
                    for (int ax = 0; ax < 2; ax++)
                        l15Hang[n, st, part, ax] = L15Block($"l15-hangsign-{n}-{(st == 0 ? "lit" : "off")}-{part}-{(ax == 0 ? "we" : "ns")}");
        l15Riser[0] = L15Block("l15-riser-half", l15Stage);
        l15Riser[1] = L15Block("l15-riser-full", l15Wall[0]);
        l15Tray[0] = L15Block("l15-tray-we");
        l15Tray[1] = L15Block("l15-tray-ns");
    }

    /// <summary>
    /// A main hall's place in the lattice: whether it runs along z, how far across it (1-5), the line it is on and how far
    /// along; null at a crossing or off the halls.
    /// </summary>
    private static (bool AlongZ, int Across, int Line, int Along)? L15HallPlace(int gx, int gz)
    {
        int u = Hashing.Mod(gx, L.L15Period), v = Hashing.Mod(gz, L.L15Period);
        bool alongZ = u is >= 1 and <= L.L15HallWidth, alongX = v is >= 1 and <= L.L15HallWidth;
        if (alongZ == alongX) return null;
        return alongZ ? (true, u, Hashing.FloorDiv(gx + 3, L.L15Period), gz) : (false, v, Hashing.FloorDiv(gz + 3, L.L15Period), gx);
    }

    /// <summary>A hall stretch's name (its sign's index), the same on the walls and hung over the hall.</summary>
    private int L15HallSign(int line, int along) => (int)(Hashing.Hash(seed, line, Hashing.FloorDiv(along, L.L15Period), 0x2722) % L15Signs);

    /// <summary>
    /// Round 3's dress of a main hall tile: the hall line's colour down the middle of its floor with a chevron every 16 blocks
    /// pointing to the nearer crossing; a glowing sign hung across it a few blocks before each crossing (its name both ways).
    /// 0 where there is none.
    /// </summary>
    private int L15HallTileDress(in Tile t, int gx, int gz, int rel)
    {
        if (rel != 0 && rel != L.L15HallHeight || L15HallPlace(gx, gz) is not { } h) return 0;
        int stretch = Hashing.Mod(h.Along, L.L15Period);
        if (rel == 0)
        {
            if (h.Across != 3 || t.Depth is not (L.L15FloorCeramic or L.L15FloorWorn)) return 0;
            int c = Hashing.Mod(h.Line, 4);
            if (Hashing.Mod(h.Along, 16) != 8) return l15Mark[c, h.AlongZ ? 0 : 1];
            bool up = stretch >= 64; // toward the crossing ahead (greater along), else back
            return l15Mark[c, h.AlongZ ? (up ? 4 : 2) : (up ? 3 : 5)];
        }
        if (stretch is not (10 or 124) || h.Across is < 2 or > 4 || t.Overhead != 0) return 0;
        // The sign spans the hall: part 0 at its low x (a hall along z) or low z (along x), so it reads from both ways
        int part = h.Across - 2;
        return l15Hang[L15HallSign(h.Line, h.Along), L.L15IsDark(t) ? 1 : 0, part, h.AlongZ ? 0 : 1];
    }


    /// <summary>A block of the level's, or <paramref name="fallback"/> if its asset is not there (logged once).</summary>
    private int L15Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l15Missing.Add(code) && l15Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 15: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL15()
    {
        int plainWall = BlockId("backrooms:concretewall-plain"), plainFloor = BlockId("backrooms:concretefloor-plain");
        for (int i = 0; i < l15Wall.Length; i++) l15Wall[i] = L15Block("l15-wall-" + L15WallKinds[i], plainWall);
        for (int i = 0; i < l15Floor.Length; i++) l15Floor[i] = L15Block("l15-floor-" + L15FloorKinds[i], plainFloor);
        string[] ceilings = { "panel", "on", "lit", "flicker", "off", "service", "vent", "troughns", "troughwe" };
        int[] fallbacks = { concreteCeilingId, lightOnId, lightLitId, lightFlickerId, lightOffId, concreteCeilingId, concreteCeilingId, 0, 0 };
        for (int i = 0; i < ceilings.Length; i++) l15Ceiling[i] = L15Block("l15-ceiling-" + ceilings[i], fallbacks[i]);
        for (int i = 0; i < l15Machine.Length; i++) l15Machine[i] = L15Block("l15-machine-" + L15MachineKinds[i], plainWall);
        l15Glass[0] = L15Block("l15-glass-clear");
        l15Glass[1] = L15Block("l15-glass-cracked", l15Glass[0]);
        l15Rib[0] = L15Block("l15-rib-we");
        l15Rib[1] = L15Block("l15-rib-ns");
        l15OddBeam[0] = L15Block("l15-oddbeam-we");
        l15OddBeam[1] = L15Block("l15-oddbeam-ns");
        l15Gate = L15Block("l15-gate-shutter", l15Wall[6]);
        l15Stage = L15Block("l15-stage");
        string[] consoles = { "dead", "denied", "radar" }, benches = { "plain", "sink", "equipment", "glassware" };
        string[] poses = { "sitting-plain", "head-plain", "feet-plain", "sitting-spear", "head-spear", "feet-plain" };
        for (int f = 0; f < 4; f++)
        {
            for (int k = 0; k < L15DecoKinds.Length; k++) l15Deco[k, f] = L15Block($"l15-walldeco-{L15DecoKinds[k]}-{Sides[f]}", l15Wall[0]);
            for (int s = 0; s < 3; s++) l15Console[s, f] = L15Block($"l15-console-{consoles[s]}-{Sides[f]}");
            for (int s = 0; s < 4; s++) l15Bench[s, f] = L15Block($"l15-labbench-{benches[s]}-{Sides[f]}");
            for (int s = 0; s < 6; s++) l15Corpse[s, f] = L15Block($"l15-corpse-{poses[s]}-{Sides[f]}");
            for (int p = 0; p < 2; p++)
            {
                string part = p == 0 ? "lower" : "upper";
                l15Locker[p, 0, f] = L15Block($"l15-locker-{part}-closed-{Sides[f]}");
                l15Locker[p, 1, f] = L15Block($"l15-locker-{part}-ajar-{Sides[f]}", l15Locker[p, 0, f]);
                l15StarDoor[p, f] = L15Block($"l15-stardoor-{part}-{Sides[f]}");
            }
            l15Rods[f] = L15Block("l15-rods-" + Sides[f]);
        }
        // The links' blocks (WorldGenerator.L15.Links.cs)
        InitL15Links();
        InitL15Round3();
        InitL15Round4();
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level15Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int top = 8; // the tallest room's ceiling; walls are dressed up to it everywhere
        // The links: the doors that do not open, the ESCAPE panel and its gateway, the pane, the office and its stairs
        if (t.Under is >= Unders.L15First and <= Unders.L15Last && L15LinkBlock(t, gx, gz, rel) is int link and >= 0) return link;
        // Round 4: the surround of Level 14's MEDICAL CENTER door (the look of the block over it is this level's)
        if (rel == 3 && t.Under == Unders.L14MedDoor && t.Kind == TileKind.Wall
            && L15Panel(L.L15IsDark(t) ? "medheaddead" : "medheadlit", Facing(t.Pier), 0) is int medHead and > 0)
            return medHead;
        if (t.Under is >= Unders.L14First and <= Unders.L14Last && L14InL15Block(t, rel) is int l14 and >= 0) return l14; // (Level 14's MEDICAL CENTER door: WorldGenerator.L14.Links.cs)
        if (rel < 0 || rel > top) return concreteId;
        switch (t.Kind)
        {
            case TileKind.Floor: break;
            case TileKind.Doorway:
                if (rel == 0) return l15Floor[t.Depth == L.L15FloorTrack ? L.L15FloorTrack : L.L15FloorCeramic];
                if (rel <= 3) return 0;
                if (rel == 4) return t.Detail == L.L15DoorGate ? l15Gate : l15Wall[L.L15IsDark(t) ? L15WLintelDead : L15WLintel];
                return L15WallBase(t, gx, gz, rel);
            default: return L15Wall(t, gx, gz, rel);
        }

        int air = t.Height is >= 3 and <= 7 ? t.Height : 4;
        bool dark = L.L15IsDark(t);
        if (L.L15ZoneOf(t) == L.L15Zone.Hall && t.Variant == 0 && L15HallTileDress(t, gx, gz, rel) is int hallDress and > 0) return hallDress;
        // Round 4: a bulkhead across the hall: a tread plate across its floor (the line keeps its colour), the deep header in
        // place of the rib
        if (L.L15ZoneOf(t) == L.L15Zone.Hall && (rel == 0 || rel == air) && L15HallPlace(gx, gz) is { } bh && L15IsBulkhead(bh.Along))
        {
            if (rel == 0 && t.Variant == 0 && t.Depth is L.L15FloorCeramic or L.L15FloorWorn) return l15Floor[L.L15FloorTrack];
            if (rel == air && t.Overhead is Overheads.L15RibWE or Overheads.L15RibNS
                && l15Bulkhead[dark ? 1 : 0, t.Overhead == Overheads.L15RibWE ? 0 : 1] is int head and > 0)
                return head;
        }
        if (rel == 0)
        {
            int finish = t.Depth is < 10 or L.L15FloorVinyl or L.L15FloorTerrazzo ? t.Depth : 0;
            return l15Floor[finish == L.L15FloorStrip && dark ? 10 : finish];
        }
        if (rel == air + 1)
        {
            int ceiling = L15CeilingBlock(t, dark);
            // Round 4: a cable trough along each edge of a main hall's ceiling (the trays seen through a grille)
            if (ceiling == l15Ceiling[0] && L.L15ZoneOf(t) == L.L15Zone.Hall && L15HallPlace(gx, gz) is { } hp && hp.Across is 1 or L.L15HallWidth
                && l15Ceiling[hp.AlongZ ? 7 : 8] > 0)
                return l15Ceiling[hp.AlongZ ? 7 : 8];
            return ceiling;
        }
        if (rel > air) return concreteId;

        // Round 3: a medical bay's curtain between its beds (rel 2-3, along the edge in Roof)
        if (t.Overhead == Overheads.L15Curtain && rel is 2 or 3) return l15Curtain[rel - 2, Facing((ArchPier)t.Roof)];
        // Ribs, odd beams and ducts in the top block of air
        if (rel == air)
        {
            if (t.Overhead is Overheads.L15RibWE or Overheads.L15RibNS && t.Variant != Props.L15Machine)
                return l15Rib[t.Overhead == Overheads.L15RibWE ? 0 : 1];
            if (t.Overhead == Overheads.L15OddBeam) return l15OddBeam[(gx + gz) & 1];
            if (t.Pipe == Pipes.L15DuctWE) return pipeRunXId;
            if (t.Pipe == Pipes.L15DuctNS) return pipeRunZId;
            if (t.Overhead is Overheads.L15TrayWE or Overheads.L15TrayNS && t.Variant == 0) return l15Tray[t.Overhead == Overheads.L15TrayWE ? 0 : 1];
        }

        int facing = Facing(t.Pier);
        switch (t.Variant)
        {
            case 0:
                if (t.SupplyBox) return rel == 1 ? BoxOf(t) : 0;
                return t.Stack > 0 && rel <= t.Stack ? CrateOf(t) : 0;
            case Props.L15Machine: return L15MachineBlock(t, gx, gz, rel);
            case Props.L15Pillar: return rel <= t.Stack ? l15Wall[rel == 2 ? 7 : 6] : 0;
            case Props.L15Locker: return rel <= 2 ? l15Locker[rel - 1, t.Detail == 1 ? 1 : 0, facing] : 0;
            case Props.L15StarDoor: return rel <= 2 ? l15StarDoor[rel - 1, facing] : 0;
            case Props.Shelf: return rel <= 2 ? shelfIds[Facing(Opposite(t.Pier))] : 0;
            // Round 3
            case Props.RunSafeCot when rel == 2 && L.L15ZoneOf(t) == L.L15Zone.Dorm: return l15Bunk[t.Stack == 0 ? 0 : 1, Facing(Opposite(t.Pier))];
            case Props.L15Riser when rel == air && t.Detail == 1 && l15Projector[0] > 0: return l15Projector[facing];
            case Props.L15Seat or Props.L15Riser:
            {
                int step = t.Stack, seatAt = step / 2 + 1; // full steps under it, then the seat (or the half step) on the next block
                if (rel < seatAt) return l15Riser[1];
                if (rel > seatAt) return 0;
                if (t.Variant == Props.L15Seat) return l15Seat[step % 2, facing];
                return step % 2 == 1 ? l15Riser[0] : 0;
            }
            case Props.L15Dock: return rel <= 2 ? l15Dock[rel - 1, dark ? 1 : 0, facing] : 0;
            case Props.KitchenCounter when rel == 2 && t.Detail is 1 or 2: return l15Appliance[t.Detail - 1, facing];
            case Props.L15LabBench when rel == 2 && t.Stack is 1 or 2: return l15Appliance[t.Stack - 1, facing];
            case Props.L15GrowRack: return rel <= 2 ? l15Grow[rel - 1, dark ? 1 : 0, facing] : 0;
            // Round 4: a vitals monitor on its arm over a medical bed's head; the canteen's tables and stools
            case Props.HospitalBed when rel == 2 && t.Stack == 0 && L.L15ZoneOf(t) == L.L15Zone.Medical && l15MedMon[0, 0] > 0:
                return l15MedMon[dark ? 1 : 0, facing];
            case Props.L15Stage when rel == 2 && t.Detail == 1: return l15Lectern[dark ? 1 : 0, facing];
            case Props.PressureTank when L.L15ZoneOf(t) == L.L15Zone.Hydro && l15Tank[0, 0] > 0: return rel <= 2 ? l15Tank[rel - 1, facing] : 0;
            case Props.FoldingChair when L.L15ZoneOf(t) == L.L15Zone.Canteen && l15Stool > 0: return rel == 1 ? l15Stool : 0;
            case Props.FoldingTable when L.L15ZoneOf(t) == L.L15Zone.Canteen && l15CTable > 0: return rel == 1 ? l15CTable : 0;
        }
        if (rel != 1) return 0;
        return t.Variant switch
        {
            Props.L15Console => l15Console[t.Detail <= 2 ? t.Detail : 0, facing],
            Props.L15LabBench => l15Bench[t.Detail & 3, facing],
            Props.L15Corpse => l15Corpse[(t.Stack <= 2 ? t.Stack : 0) + (t.Detail == 1 ? 3 : 0), facing],
            Props.L15Rods => l15Rods[facing],
            Props.L15Stage => l15Stage,
            Props.L15Serve => l15Serve[t.Stack <= 2 ? t.Stack : 0, facing],
            Props.OfficeChair => chairIds[facing],
            Props.FilingCabinet => filingIds[facing],
            >= 40 and < Props.Limit => PropBlock(t),
            _ => 0,
        };
    }

    /// <summary>A ceiling block: a panel, a light (dead wherever the power is out), the service passages' concrete and caged lamps, a grille.</summary>
    private int L15CeilingBlock(in Tile t, bool dark)
    {
        bool service = L.L15ZoneOf(t) == L.L15Zone.Service;
        switch (t.Ceiling)
        {
            // (round 4: the service passages' caged lamps cool white like the halls', as models)
            case CeilingKind.L15LightOn: return dark ? (service ? l15CageLamp[1] : l15Ceiling[4]) : service ? l15CageLamp[0] : l15Ceiling[1];
            case CeilingKind.L15LightLit: return dark ? l15Ceiling[4] : l15Ceiling[2];
            case CeilingKind.L15LightFlicker: return service ? l15CageLamp[1] : l15Ceiling[3];
            case CeilingKind.L15LightDead: return service ? l15CageLamp[1] : l15Ceiling[4];
            case CeilingKind.L15ServiceCeiling: return l15Ceiling[5];
            case CeilingKind.L15CeilingVent: return l15Ceiling[6];
            default: return service ? l15Ceiling[5] : l15Ceiling[0];
        }
    }

    /// <summary>A wall's plain block at a height: the skirting row at the foot, white panels above (now and then the other panel), or grey or scorched.</summary>
    private int L15WallBase(in Tile t, int gx, int gz, int rel)
    {
        switch (t.Depth)
        {
            case L.L15WallGrey: return l15Wall[rel <= 1 ? 4 : 3];
            case L.L15WallScorched: return rel <= 3 ? l15Wall[5] : l15Wall[0];
            case L.L15WallCast: return l15Wall[rel <= 1 ? L15WCastBase : L15WCast];
            case L.L15WallTile: return l15Wall[rel <= 1 ? L15WTileBase : L15WTile];
        }
        if (rel <= 1) return l15Wall[2];
        return Hashing.Unit(Hashing.Hash(seed, gx, gz * 16 + rel, 0x2720)) < 0.18 ? l15Wall[1] : l15Wall[0];
    }

    /// <summary>A wall tile: its plain blocks, with what is on its face at its own height (see <see cref="WorldLayout.L15WallPlain"/>).</summary>
    private int L15Wall(in Tile t, int gx, int gz, int rel)
    {
        if (rel == 0) return t.Depth == L.L15WallGrey ? l15Wall[3] : l15Wall[0];
        int f = Facing(t.Pier);
        if (t.Detail == L.L15WallJamb) return rel <= 3 ? l15Wall[L.L15IsDark(t) ? L15WJambDead : L15WJamb] : L15WallBase(t, gx, gz, rel);
        // Round 4: a bulkhead's jambs in place of the pilasters every 32 blocks along a main hall (a code plate in the hall
        // line's colour at the band, a status lamp where there is power, the knee brace under the header)
        if (t.Detail is L.L15WallPilaster or L.L15WallEtched && rel is >= 1 and <= L.L15HallHeight && L15HallFace(gx, gz) is { } bf && L15IsBulkhead(bf.Along))
        {
            string kind = rel == 2 ? $"jambplate{Hashing.Mod(bf.Line, 4)}"
                : rel == 3 && L.L15IsDark(t) ? "jamb2" : $"jamb{rel}{(t.Detail == L.L15WallEtched && rel != 1 ? "e" : "")}";
            if (L15Panel(kind, Facing(bf.Face), 0) is int jamb and > 0) return jamb;
        }
        if (L15WallRound4(t, rel, f) is int r4 and > 0) return r4;
        if (L15WallRound3(t, rel, f) is int r3 and > 0) return r3;
        if (t.Detail is not (L.L15WallPilaster or L.L15WallEtched) && L15HallFace(gx, gz) is { } hall && L15HallDress(t, gx, gz, rel, hall) is int dressed and > 0)
            return dressed;
        switch (t.Detail)
        {
            case L.L15WallPilaster: return l15Wall[6];
            case L.L15WallEtched: return l15Wall[rel == 2 ? 7 : 6];
            case L.L15WallGlass or L.L15WallGlassCracked when rel is 2 or 3:
                return l15Glass[0] == 0 ? L15WallBase(t, gx, gz, rel) : l15Glass[t.Detail == L.L15WallGlassCracked && rel == 2 ? 1 : 0];
            case L.L15WallScanner when rel == 2: return l15Deco[L15DScanner, f];
            case L.L15WallCode when rel == 3: return l15Deco[L15DCode + t.Stack % L.L15Codes, f];
            case L.L15WallDisplay when rel == 2: return l15Deco[L15DDisplay, f];
            case L.L15WallRadar when rel == 2: return l15Deco[L15DRadar, f];
            case L.L15WallEscape when rel == 2: return l15Deco[L15DEscape, f];
            case L.L15WallView when rel == 2: return l15Deco[L15DView + t.Stack % L.L15Views, f];
            case L.L15WallVent when rel == 1: return l15Deco[L15DVent, f];
            case L.L15WallVentCode when rel == 1: return l15Deco[L15DVentCode, f];
            case L.L15WallWoodDoor when rel is 1 or 2: return l15Deco[rel == 1 ? L15DDoorLower : L15DDoorUpper, f];
            case L.L15WallBlood when rel == 1: return l15Deco[L15DBlood, f];
        }
        return L15WallBase(t, gx, gz, rel);
    }

    /// <summary>
    /// Round 4's models on a wall tile at a height, before round 3's (0 where it has none): the extinguisher (the detail kit's
    /// own), the ESCAPE panel, the lift in its portal with its lit indicator and call panel, the big display's bezel, the
    /// thick glass in its frame.
    /// </summary>
    private int L15WallRound4(in Tile t, int rel, int f)
    {
        switch (t.Detail)
        {
            case L.L15WallExtinguisher when rel == 2: return L15Panel("ext", f, 0);
            case L.L15WallScrawl when rel == 2: return L15Panel("scrawl", f, 0);
            case L.L15WallEscape when rel == 2: return L15Panel("escape", f, 0);
            case L.L15WallDisplay when rel == 2: return L15Panel("display", f, 0);
            case L.L15WallRadar when rel == 2: return L15Panel("radar", f, 0);
            case L.L15WallView when rel == 2: return L15Panel($"view{t.Stack % L.L15Views}", f, 0);
            case L.L15WallBigScreen when rel == 2: return L15Panel(t.Stack == 1 ? "radar" : "display", f, 0);
            case L.L15WallBigScreen when rel is 3 or 4: return L15Panel($"big{rel - 3}{Math.Min((int)t.Stack, 2)}", f, 0);
            case L.L15WallLiftCall when rel == 2: return L15Panel("liftcall", f, 0);
            case L.L15WallLiftL or L.L15WallLiftR when rel is >= 1 and <= 4:
                bool left = t.Detail == L.L15WallLiftL;
                return L15Panel(rel == 4 ? $"liftind{(left ? 0 : 1)}" : $"lift{(left ? "l" : "r")}{rel - 1}", f, 0);
            case L.L15WallGlass or L.L15WallGlassCracked when rel is 2 or 3:
                return l15Glazing[t.Detail == L.L15WallGlassCracked && rel == 2 ? 1 : 0, rel - 2, f % 2];
        }
        return 0;
    }

    /// <summary>
    /// Round 3's dress of a wall tile at a height, before the halls' own (0 where it has none): the room's name plate under its
    /// code, AUTHORIZED PERSONNEL ONLY over a gate's scanner and by a control room's door, DECONTAMINATION, HIGH VOLTAGE, the
    /// lifts (leaves rel 1-3, the indicator over them, the call panel), a service hatch and a grille of pipes at the foot of the
    /// wall, the canteen's menu board.
    /// </summary>
    private int L15WallRound3(in Tile t, int rel, int f)
    {
        switch (t.Detail)
        {
            case L.L15WallCode when rel == 2: return l15Sign[Math.Min(t.Stack / 2, L15PlateKinds.Length - 1), f];
            case L.L15WallScanner when rel == 3: return l15Sign[L15SAuth, f];
            case L.L15WallAuth when rel == 2: return l15Sign[L15SAuth, f];
            case L.L15WallDecon when rel == 2: return l15Sign[L15SDecon, f];
            case L.L15WallHV when rel == 2: return l15Sign[L15SHV, f];
            case L.L15WallHatch when rel == 1: return l15Sign[L15SHatch, f];
            case L.L15WallPipes when rel == 1: return l15Sign[L15SPipes, f];
            case L.L15WallMenu when rel == 3: return l15Sign[L15SMenu + Math.Min((int)t.Stack, 2), f];
            case L.L15WallBigScreen when rel is 3 or 4: return l15Sign[L15SBig + (rel - 3) * 3 + Math.Min((int)t.Stack, 2), f];
            case L.L15WallBigScreen when rel == 2: return l15Deco[t.Stack == 1 ? L15DRadar : L15DDisplay, f];
            case L.L15WallSlide when rel is >= 2 and <= 4: return l15Sign[L15SSlide + (rel - 2) * 3 + Math.Min((int)t.Stack, 2), f];
            case L.L15WallMap when rel is 2 or 3: return l15Sign[L15SMap + (rel - 2) * 2 + Math.Min((int)t.Stack, 1), f];
            case L.L15WallExtinguisher when rel == 2: return l15Sign[L15SExtinguisher, f];
            case L.L15WallLiftCall when rel == 2: return l15Sign[L15SLiftCall, f];
            case L.L15WallLiftL or L.L15WallLiftR when rel is >= 1 and <= 4:
                bool left = t.Detail == L.L15WallLiftL;
                if (rel == 4) return l15Sign[L15SLiftInd + (left ? 0 : 1), f];
                return l15Sign[(left ? L15SLiftL : L15SLiftR) + rel - 1, f];
        }
        return 0;
    }

    /// <summary>
    /// Which way a wall of a wing faces the main hall beside it, and where along the hall it is; null for any other wall
    /// (a wing's corner, a room's wall, the region's rim).
    /// </summary>
    private static (ArchPier Face, int Along, int Line)? L15HallFace(int gx, int gz)
    {
        int u = Hashing.Mod(gx, L.L15Period), v = Hashing.Mod(gz, L.L15Period);
        bool uEdge = u is 0 or L.L15HallWidth + 1, vEdge = v is 0 or L.L15HallWidth + 1;
        if (uEdge == vEdge || u is >= 1 and <= L.L15HallWidth || v is >= 1 and <= L.L15HallWidth) return null;
        return uEdge
            ? (u == 0 ? ArchPier.East : ArchPier.West, gz, Hashing.FloorDiv(gx + 3, L.L15Period))
            : (v == 0 ? ArchPier.South : ArchPier.North, gx, Hashing.FloorDiv(gz + 3, L.L15Period));
    }

    /// <summary>
    /// The dress of a wing's wall along a main hall (0 where it has none at that height): a dark band with a pale line at
    /// waist height (the way through), a dark cornice with a strip of light under the ceiling, a tall wall light in the
    /// middle of each bay (every other one giving light, by turns along the two walls; dead where the power is out), and
    /// near each crossing a sign with the hall's letter and number. What the wing put on the wall wins where they meet.
    /// </summary>
    private int L15HallDress(in Tile t, int gx, int gz, int rel, (ArchPier Face, int Along, int Line) hall)
    {
        int f = Facing(hall.Face);
        bool dark = L.L15IsDark(t);
        int bay = Hashing.Mod(hall.Along, 8), stretch = Hashing.Mod(hall.Along, L.L15Period);
        bool decoAt2 = t.Detail is L.L15WallScanner or L.L15WallDisplay or L.L15WallRadar or L.L15WallEscape or L.L15WallView or L.L15WallWoodDoor
            or L.L15WallCode or L.L15WallAuth or L.L15WallDecon or L.L15WallHV or L.L15WallMap or L.L15WallExtinguisher;
        switch (rel)
        {
            // The band, in its hall line's colour (round 3: each line its own)
            case 2:
                if (decoAt2) return 0;
                // Round 4: the breaker panel that tripped, on one wall, the first bay into the dark
                if (dark && bay == 4 && hall.Face is ArchPier.East or ArchPier.South && t.Detail == L.L15WallPlain
                    && L15DarkEdge(gx, gz, hall.Face is ArchPier.East or ArchPier.West) == 1)
                    return L15Panel("breaker", f, l15Sign[L15SBand + Hashing.Mod(hall.Line, 4), f]);
                // Round 4: the hall's name on a tag on the band, on one wall, a few blocks past each bulkhead
                if (Hashing.Mod(hall.Along, 32) == 20 && hall.Face is ArchPier.West or ArchPier.North && t.Detail == L.L15WallPlain)
                    return L15Panel($"tag{Hashing.Mod(hall.Line, 4)}{L15HallSign(hall.Line, hall.Along)}", f, l15Sign[L15SBand + Hashing.Mod(hall.Line, 4), f]);
                return l15Sign[L15SBand + Hashing.Mod(hall.Line, 4), f];
            case 3 when t.Detail is not (L.L15WallCode or L.L15WallScanner) && stretch is 11 or 123:
                // The hall's sign: its letter from the line it runs along, its number from the stretch it is in
                return l15Deco[L15DSign + L15HallSign(hall.Line, hall.Along), f];
            case 3 when bay == 4 && t.Detail is not (L.L15WallCode or L.L15WallWoodDoor):
                return L15Panel(dark ? "lamplowerdead" : "lamplower", f, l15Deco[dark ? L15DLampLowerDead : L15DLampLower, f]);
            case 4 when bay == 4 && t.Detail != L.L15WallWoodDoor:
                // Round 4: near the lit side the dead light's place takes a battery emergency lamp, still burning amber
                if (dark && L15DarkEdge(gx, gz, hall.Face is ArchPier.East or ArchPier.West) is 1 or 2)
                    return L15Panel("emerglit", f, l15Deco[L15DLampUpperDead, f]);
                if (dark) return L15Panel("lampupperdead", f, l15Deco[L15DLampUpperDead, f]);
                bool turn = hall.Face is ArchPier.East or ArchPier.South;
                bool on = Hashing.Mod(hall.Along, 16) == (turn ? 4 : 12);
                return L15Panel(on ? "lampon" : "lampupper", f, l15Deco[on ? L15DLampOn : L15DLampUpper, f]);
            case L.L15HallHeight: return l15Deco[L15DCornice, f];
        }
        return 0;
    }

    /// <summary>
    /// A block of a machine (<see cref="Props.L15Machine"/>, <see cref="Tile.Stack"/> blocks high): its casing picked by
    /// hash for each block, by its state: hatches at the foot, then panels, vents, screens and lamp banks (lit while it
    /// runs); a wrecked one burnt, its top block gone now and then; an incinerator's mouth; a press.
    /// </summary>
    private int L15MachineBlock(in Tile t, int gx, int gz, int rel)
    {
        int h = t.Stack is >= 1 and <= 6 ? t.Stack : 1;
        if (rel > h) return 0;
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz * 16 + rel, 0x2721));
        int kind = t.Detail switch
        {
            L.L15MachineRunning => rel == 1 ? (r < 0.5 ? L15MHatch : L15MPanel) : r < 0.3 ? L15MLightsLit : r < 0.5 ? L15MScreenLit : r < 0.8 ? L15MVent : L15MPanel,
            L.L15MachineWrecked => rel == h && h > 1 && r < 0.35 ? -1 : r < 0.55 ? L15MBurnt : r < 0.85 ? L15MBurntVent : L15MPanel,
            L.L15MachineIncinerator => rel == 1 ? L15MFurnace : rel == 2 ? L15MWarning : L15MVent,
            L.L15MachinePress => rel == 1 ? L15MPress : rel == 2 ? L15MLightsLit : L15MPanel,
            _ => rel == 1 ? (r < 0.5 ? L15MHatch : L15MPanel) : rel == h && r < 0.15 ? L15MWarning : r < 0.3 ? L15MLights : r < 0.5 ? L15MScreen : r < 0.8 ? L15MVent : L15MPanel,
        };
        return kind < 0 ? 0 : l15Machine[kind];
    }
}
