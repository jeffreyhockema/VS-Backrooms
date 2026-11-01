using System;
using System.Collections.Generic;
using L = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 14, "The Hospital" (experimental, kept as level 29), laid out in WorldLayout.Level14.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Walls by material (<c>l14-wall</c>: mint paint over its wainscot, inpatient white,
/// tiles, quilted, cinder block, plywood, rust, bloodied tiles, mould, bare concrete), the handrail at the foot of the halls'
/// and corridors' walls (<c>l14-rail</c>), what hangs on them (<c>l14-walldeco</c>), windows onto blackness
/// (<c>l14-window</c>), the revolving door's back row; floors (<c>l14-floor</c>), ceiling tiles and troffers
/// (<c>l14-ceiling</c>); doors (<c>l14-door</c>, <c>l14-contamdoor</c>, <c>l14-firedoor</c>); the props of
/// tools/gen_14_props.py and the mod's own (Level !'s gurneys, wheelchairs, drip stands, crash carts, bedside cabinets, cots,
/// the shelving, boxes, filing cabinets, office chairs). Everything above the rooms is solid to the top of the band.
///
/// Every block of the level's own is looked up softly (<see cref="L14Block"/>): what is missing is left out, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L14WallKinds = { "paint", "paintscuff", "paintbase", "white", "whitebase", "tile", "tilebase", "padded", "cinder",
        "plywood", "rust", "rustblood", "tileblood", "mould", "whitemoss", "concrete", "lintel" };
    private static readonly string[] L14FloorKinds = { "vinyl", "vinylworn", "vinylborder", "white", "pink", "theatre", "terrazzo", "concrete", "marble",
        "marbleshattered", "blood", "mould", "contam", "cracked", "sagging", "line-ns", "line-we", "arrow-n", "arrow-e", "arrow-s", "arrow-w" };
    private static readonly string[] L14CeilingKinds = { "tile", "on", "bright", "lit", "flicker", "off", "hole", "stained", "blood", "mould", "plaster", "concrete" };
    private static readonly string[] L14DecoKinds = { "plate-ward", "plate-icu", "plate-surgery", "plate-maternity", "plate-psych", "plate-storage",
        "plate-reception", "plate-office", "plate-research", "plate-danger", "plate-biohazard", "sign-0", "sign-1", "sign-2", "sign-3", "sign-4", "sign-5",
        "sign-6", "sign-7", "poster-kid0", "poster-kid1", "poster-kid2", "poster-health0", "poster-health1", "clock", "whiteboard", "xray", "blood",
        "blooddrip", "mould", "scratches", "exitsign", "sanitizer", "extinguisher", "trg" };
    private const int L14DkPlate = 0, L14DkSign = 11, L14DkPoster = 19, L14DkClock = 24, L14DkBoard = 25, L14DkXray = 26, L14DkBlood = 27, L14DkDrip = 28,
        L14DkMould = 29, L14DkScratches = 30, L14DkExit = 31, L14DkSanitizer = 32, L14DkExtinguisher = 33, L14DkTrg = 34;
    private const int L14WPaint = 0, L14WScuff = 1, L14WPaintBase = 2, L14WWhite = 3, L14WWhiteBase = 4, L14WTile = 5, L14WTileBase = 6, L14WPadded = 7,
        L14WCinder = 8, L14WPlywood = 9, L14WRust = 10, L14WRustBlood = 11, L14WTileBlood = 12, L14WMould = 13, L14WWhiteMoss = 14, L14WConcrete = 15, L14WLintel = 16;

    private readonly int[] l14Wall = new int[17], l14Floor = new int[21], l14Ceiling = new int[12];
    private readonly int[,] l14Deco = new int[35, 4], l14Rail = new int[2, 4];
    private readonly int[,,] l14Window = new int[2, 2, 4];
    /// <summary>[state closed/open/locked, hinge, part, side]; the contaminated room's door [part, side]; fire doors [hinge, part, side].</summary>
    private readonly int[,,,] l14Door = new int[3, 2, 2, 4];
    private readonly int[,] l14ContamDoor = new int[2, 4];
    private readonly int[,,] l14FireDoor = new int[2, 2, 4];
    /// <summary>The revolving door: [col, row back/front, tier, side].</summary>
    private readonly int[,,,] l14Revolving = new int[3, 2, 3, 4];
    private readonly int[,] l14HangSign = new int[8, 2];
    /// <summary>The props: by prop (less <see cref="Props.L14First"/>), then a kind index and side; two-high ones keep their upper part at kind + 8.</summary>
    private readonly int[,,] l14Prop = new int[Props.L14Last - Props.L14First + 1, 16, 4];
    private int l14SurgLamp, l14Hook;
    private readonly HashSet<string> l14Missing = new();

    /// <summary>A block of the level's, or <paramref name="fallback"/> if its asset is not there (logged once).</summary>
    private int L14Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l14Missing.Add(code) && l14Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 14: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>Registers a prop's blocks: <paramref name="name"/>(kind) gives the code before its side ("" for none).</summary>
    private void L14Prop(ushort prop, int kinds, Func<int, string> name, bool sided = true)
    {
        for (int k = 0; k < kinds; k++)
            for (int f = 0; f < 4; f++)
                l14Prop[prop - Props.L14First, k, f] = L14Block(sided ? $"{name(k)}-{Sides[f]}" : name(k));
    }

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL14()
    {
        int plainWall = BlockId("backrooms:concretewall-plain"), plainFloor = BlockId("backrooms:concretefloor-plain");
        for (int i = 0; i < l14Wall.Length; i++) l14Wall[i] = L14Block("l14-wall-" + L14WallKinds[i], plainWall);
        for (int i = 0; i < l14Floor.Length; i++) l14Floor[i] = L14Block("l14-floor-" + L14FloorKinds[i], plainFloor);
        int[] ceilingFallback = { concreteCeilingId, lightOnId, lightOnId, lightLitId, lightFlickerId, lightOffId, concreteCeilingId, concreteCeilingId,
            concreteCeilingId, concreteCeilingId, concreteCeilingId, concreteCeilingId };
        for (int i = 0; i < l14Ceiling.Length; i++) l14Ceiling[i] = L14Block("l14-ceiling-" + L14CeilingKinds[i], ceilingFallback[i]);
        string[] states = { "closed", "open", "locked" }, hinges = { "l", "r" }, parts = { "lower", "upper" }, rows = { "back", "front" }, tiers = { "lower", "middle", "upper" };
        for (int f = 0; f < 4; f++)
        {
            string s = Sides[f];
            for (int k = 0; k < L14DecoKinds.Length; k++) l14Deco[k, f] = L14Block($"l14-walldeco-{L14DecoKinds[k]}-{s}", l14Wall[L14WPaint]);
            l14Rail[0, f] = L14Block($"l14-rail-paint-{s}", l14Wall[L14WPaintBase]);
            l14Rail[1, f] = L14Block($"l14-rail-white-{s}", l14Wall[L14WWhiteBase]);
            for (int p = 0; p < 2; p++)
            {
                l14Window[p, 0, f] = L14Block($"l14-window-{parts[p]}-broken-{s}", l14Wall[L14WWhite]);
                l14Window[p, 1, f] = L14Block($"l14-window-{parts[p]}-shattered-{s}", l14Window[p, 0, f]);
                l14ContamDoor[p, f] = L14Block($"l14-contamdoor-{parts[p]}-{s}");
                for (int h = 0; h < 2; h++)
                {
                    l14FireDoor[h, p, f] = L14Block($"l14-firedoor-{hinges[h]}-{parts[p]}-{s}");
                    for (int st = 0; st < 3; st++) l14Door[st, h, p, f] = L14Block($"l14-door-{states[st]}-{hinges[h]}-{parts[p]}-{s}");
                }
            }
            for (int c = 0; c < 3; c++)
                for (int r = 0; r < 2; r++)
                    for (int t = 0; t < 3; t++)
                        l14Revolving[c, r, t, f] = L14Block($"l14-revolving-{c}-{rows[r]}-{tiers[t]}-{s}", l14Wall[L14WPaint]);
        }
        for (int n = 0; n < 8; n++)
        {
            l14HangSign[n, 0] = L14Block($"l14-hangsign-{n}-we");
            l14HangSign[n, 1] = L14Block($"l14-hangsign-{n}-ns");
        }
        l14SurgLamp = L14Block("l14-surglamp");
        l14Hook = L14Block("l14-hook");

        string[] desk = { "endl", "mid", "supplies", "lamp", "phone", "endr" }, chairs = { "plain", "magazine", "soda", "torn" };
        L14Prop(Props.L14Desk, 6, k => "l14-desk-" + desk[k]);
        L14Prop(Props.L14WaitChair, 4, k => "l14-waitchair-" + chairs[k]);
        L14Prop(Props.L14FloorLamp, 4, k => $"l14-floorlamp-{parts[k / 2]}-{(k % 2 == 0 ? "on" : "off")}", false);
        L14Prop(Props.L14MagTable, 1, _ => "l14-magtable", false);
        L14Prop(Props.L14Sodas, 1, _ => "l14-sodas", false);
        L14Prop(Props.L14Bed, 4, k => $"l14-bed-{(k / 2 == 0 ? "head" : "foot")}-{(k % 2 == 0 ? "made" : "stripped")}");
        L14Prop(Props.L14StrapBed, 2, k => "l14-strapbed-" + (k == 0 ? "head" : "foot"));
        L14Prop(Props.L14Overbed, 1, _ => "l14-overbed");
        L14Prop(Props.L14Monitor, 2, k => "l14-monitor-" + (k == 0 ? "on" : "off"));
        L14Prop(Props.L14Ventilator, 1, _ => "l14-ventilator");
        L14Prop(Props.L14Crib, 1, _ => "l14-crib");
        L14Prop(Props.L14Teddy, 1, _ => "l14-teddy");
        L14Prop(Props.L14Desk2, 1, _ => "l14-desk2");
        L14Prop(Props.L14Cabinet, 2, k => "l14-cabinet-" + parts[k]);
        L14Prop(Props.L14OpTable, 2, k => "l14-optable-" + (k == 0 ? "head" : "foot"));
        L14Prop(Props.L14Trolley, 2, k => "l14-trolley-" + (k == 0 ? "clean" : "rusty"));
        L14Prop(Props.L14Anaesthesia, 1, _ => "l14-anaesthesia");
        L14Prop(Props.L14EquipShelf, 2, k => "l14-equipshelf-" + parts[k]);
        L14Prop(Props.L14TubeRack, 1, _ => "l14-tuberack");
        L14Prop(Props.L14Vines, 1, _ => "l14-vines", false);
        L14Prop(Props.L14MouldFloor, 1, _ => "l14-mouldfloor", false);
        L14Prop(Props.L14Stretchers, 2, k => "l14-stretchers-" + parts[k]);
        L14Prop(Props.L14KnifeCab, 2, k => "l14-knifecab-" + parts[k]);
        L14Prop(Props.L14BloodPool, 1, _ => "l14-bloodpool", false);
        string[] trg = { "papers", "radio", "samples" };
        L14Prop(Props.L14TrgDesk, 3, k => "l14-trgdesk-" + trg[k]);
        L14Prop(Props.L14SampleRack, 1, _ => "l14-samplerack");
        L14Prop(Props.L14Cell, 4, k => $"l14-cell-{parts[k / 2]}-{(k % 2 == 0 ? "intact" : "broken")}");
        L14Prop(Props.L14Crate, 1, _ => "l14-crate");
        L14Prop(Props.L14Drum, 2, k => "l14-drum-" + (k == 0 ? "sealed" : "leaking"), false);
        string[] station = { "counter", "computer", "corner" };
        L14Prop(Props.L14Station, 3, k => "l14-station-" + station[k]);
        L14Prop(Props.L14LinenCart, 1, _ => "l14-linencart");
        L14Prop(Props.L14Bench, 1, _ => "l14-bench");
        InitL14Links();
    }

    /// <summary>The level's links' blocks (WorldGenerator.L14.Links.cs).</summary>
    partial void InitL14Links();

    /// <summary>The level's links' blocks at a tile (WorldGenerator.L14.Links.cs): -1 where it has none.</summary>
    partial void L14LinkBlock(in Tile t, int gx, int gz, int rel, ref int id);

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level14Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int top = 6;
        if (t.Under != 0)
        {
            int link = -1;
            L14LinkBlock(t, gx, gz, rel, ref link);
            if (link >= 0) return link;
        }
        if (rel < 0 || rel > top) return concreteId;
        switch (t.Kind)
        {
            case TileKind.Floor: break;
            case TileKind.Doorway: return L14DoorwayBlock(t, gx, gz, rel);
            default: return L14WallBlock(t, gx, gz, rel);
        }
        int air = t.Height is >= 3 and <= 5 ? t.Height : 3;
        if (rel == 0) return l14Floor[t.Depth < l14Floor.Length ? t.Depth : 0];
        if (rel == air + 1) return L14CeilingBlock(t);
        if (rel > air) return concreteId;
        bool dark = L.L14IsDark(t);
        // What hangs in the top block of air: a department sign across a hall, a surgical light, chains and a hook
        if (rel == air)
        {
            switch (t.Overhead)
            {
                case Overheads.L14HangSign: return l14HangSign[t.Stack & 7, t.Pier is ArchPier.North or ArchPier.South ? 0 : 1];
                case Overheads.L14SurgLamp: return l14SurgLamp;
                case Overheads.L14Hook: return l14Hook;
            }
        }
        int f = Facing(t.Pier), p = t.Variant - Props.L14First;
        if (t.Variant is >= Props.L14First and <= Props.L14Last)
        {
            switch (t.Variant)
            {
                case Props.L14Revolving:
                    return rel <= 3 ? l14Revolving[Math.Min((int)t.Stack, 2), 1, rel - 1, f] : 0;
                case Props.L14FloorLamp:
                    return rel <= 2 ? l14Prop[p, (rel - 1) * 2 + (dark || t.Detail == 0 ? 1 : 0), 0] : 0;
                case Props.L14Cabinet or Props.L14EquipShelf or Props.L14Stretchers or Props.L14KnifeCab:
                    return rel <= 2 ? l14Prop[p, rel - 1, f] : 0;
                case Props.L14Cell:
                    return rel <= 2 ? l14Prop[p, (rel - 1) * 2 + (t.Detail == 1 ? 1 : 0), f] : 0;
            }
            if (rel != 1) return L14Curtain(t, rel);
            return t.Variant switch
            {
                Props.L14Desk => l14Prop[p, Math.Min((int)t.Stack, 5), f],
                Props.L14WaitChair or Props.L14Trolley or Props.L14TrgDesk or Props.L14Station => l14Prop[p, Math.Min((int)t.Stack, 3), f],
                Props.L14Bed => l14Prop[p, (t.Stack == 0 ? 0 : 2) + (t.Detail == 1 ? 1 : 0), f],
                Props.L14StrapBed or Props.L14OpTable => l14Prop[p, t.Stack == 0 ? 0 : 1, f],
                Props.L14Monitor => l14Prop[p, dark || t.Detail == 1 ? 1 : 0, f],
                Props.L14Drum => l14Prop[p, t.Stack == 1 ? 1 : 0, 0],
                Props.L14MagTable or Props.L14Sodas or Props.L14Vines or Props.L14MouldFloor or Props.L14BloodPool => l14Prop[p, 0, 0],
                _ => l14Prop[p, 0, f],
            };
        }
        switch (t.Variant)
        {
            case 0:
                if (t.SupplyBox) return rel == 1 ? BoxOf(t) : 0;
                if (t.Stack > 0 && rel <= t.Stack) return CrateOf(t);
                return L14Curtain(t, rel);
            case Props.Shelf: return rel <= 2 ? shelfIds[Facing(Opposite(t.Pier))] : 0;
            case Props.OfficeChair: return rel == 1 ? chairIds[f] : 0;
            case Props.FilingCabinet: return rel == 1 ? filingIds[f] : 0;
        }
        if (rel != 1) return L14Curtain(t, rel);
        return PropBlock(t);
    }

    /// <summary>A ward's curtain between two beds: hung from its rail along the tile's edge (toward <see cref="Tile.Roof"/>), rel 1 and 2.</summary>
    private int L14Curtain(in Tile t, int rel) =>
        t.Overhead == Overheads.L14Curtain && rel is 1 or 2 && t.Variant == 0 ? L14CurtainBlock(rel, Facing((ArchPier)t.Roof)) : 0;

    private int[,] l14Curtain;

    private int L14CurtainBlock(int rel, int f)
    {
        if (l14Curtain == null)
        {
            l14Curtain = new int[2, 4];
            for (int s = 0; s < 4; s++)
            {
                l14Curtain[0, s] = L14Block($"l14-curtain-lower-{Sides[s]}");
                l14Curtain[1, s] = L14Block($"l14-curtain-upper-{Sides[s]}");
            }
        }
        return l14Curtain[rel - 1, f];
    }

    /// <summary>A ceiling block by <see cref="Tile.Ceiling"/>.</summary>
    private int L14CeilingBlock(in Tile t)
    {
        bool dark = L.L14IsDark(t);
        return t.Ceiling switch
        {
            CeilingKind.L14LightOn => l14Ceiling[dark ? 5 : 1],
            CeilingKind.L14LightBright => l14Ceiling[dark ? 5 : 2],
            CeilingKind.L14LightLit => l14Ceiling[dark ? 5 : 3],
            CeilingKind.L14LightFlicker => l14Ceiling[4],
            CeilingKind.L14LightDead => l14Ceiling[5],
            CeilingKind.L14CeilingHole => l14Ceiling[6],
            CeilingKind.L14CeilingStained => l14Ceiling[7],
            CeilingKind.L14CeilingBlood => l14Ceiling[8],
            CeilingKind.L14CeilingMould => l14Ceiling[9],
            CeilingKind.L14CeilingPlaster => l14Ceiling[10],
            CeilingKind.L14CeilingConcrete => l14Ceiling[11],
            _ => l14Ceiling[0],
        };
    }

    /// <summary>A doorway: its floor (the room's), the door two high (or the fire doors' leaves, or open), the lintel, the wall above.</summary>
    private int L14DoorwayBlock(in Tile t, int gx, int gz, int rel)
    {
        if (rel == 0) return l14Floor[t.Depth < l14Floor.Length ? t.Depth : 0];
        if (rel >= 3) return rel == 3 ? l14Wall[L14WLintel] : l14Wall[L14WPaint];
        int f = Facing(t.Pier), part = rel - 1, hinge = t.Stack == 1 ? 1 : 0;
        switch (t.Detail)
        {
            case L.L14DoorOpen: return l14Door[1, hinge, part, f];
            case L.L14DoorClosed: return l14Door[0, hinge, part, f];
            case L.L14DoorLocked: return l14Door[2, hinge, part, f];
            case L.L14DoorContam: return l14ContamDoor[part, f];
            case L.L14DoorFire:
                if (t.Stack > 1) return 0;
                // The leaf stands against the jamb on its own side, its face toward the middle of the doorway
                bool alongZ = t.Pier is ArchPier.North or ArchPier.South;
                ArchPier face = alongZ ? (t.Stack == 0 ? ArchPier.East : ArchPier.West) : (t.Stack == 0 ? ArchPier.South : ArchPier.North);
                return l14FireDoor[hinge, part, Facing(face)];
        }
        return 0;
    }

    /// <summary>A wall's plain block at a height, by its material: the foot (a wainscot under paint, a white skirting) and the upper blocks.</summary>
    private int L14WallBase(in Tile t, int gx, int gz, int rel)
    {
        bool foot = rel <= 1;
        switch (t.Depth)
        {
            case L.L14MWhite: return l14Wall[foot ? L14WWhiteBase : L14WWhite];
            case L.L14MWhiteMoss: return l14Wall[foot ? L14WWhiteBase : (Hashing.Hash(seed, gx, gz * 16 + rel, 0x2920) & 3) == 0 ? L14WWhiteMoss : L14WWhite];
            case L.L14MTile: return l14Wall[foot ? L14WTileBase : L14WTile];
            case L.L14MPadded: return l14Wall[L14WPadded];
            case L.L14MCinder: return l14Wall[L14WCinder];
            case L.L14MPlywood: return l14Wall[foot ? L14WCinder : L14WPlywood];
            case L.L14MRust: return l14Wall[(Hashing.Hash(seed, gx, gz * 16 + rel, 0x2921) % 3) == 0 ? L14WRustBlood : L14WRust];
            case L.L14MTileBlood: return l14Wall[rel >= 3 || (Hashing.Hash(seed, gx, gz, 0x2922) & 1) == 0 ? L14WTileBlood : L14WTile];
            case L.L14MMould: return l14Wall[foot ? L14WPaintBase : L14WMould];
            case L.L14MConcrete: return l14Wall[L14WConcrete];
        }
        if (foot) return l14Wall[L14WPaintBase];
        return Hashing.Unit(Hashing.Hash(seed, gx, gz * 16 + rel, 0x2923)) < 0.15 ? l14Wall[L14WScuff] : l14Wall[L14WPaint];
    }

    /// <summary>A wall tile: its plain blocks, the handrail at its foot along a hall or corridor, and what is on its face at its own height.</summary>
    private int L14WallBlock(in Tile t, int gx, int gz, int rel)
    {
        if (rel == 0) return l14Floor[L.L14FConcrete];
        int f = Facing(t.Pier);
        bool white = t.Depth is L.L14MWhite or L.L14MWhiteMoss;
        switch (t.Detail)
        {
            case L.L14DRevolving when rel <= 3: return l14Revolving[Math.Min((int)t.Stack, 2), 0, rel - 1, f];
            case L.L14DWindow when rel is 2 or 3: return l14Window[rel - 2, t.Stack == 1 ? 1 : 0, f];
            case L.L14DPlate when rel == 2: return l14Deco[L14DkPlate + Math.Min((int)t.Stack, 10), f];
            case L.L14DSign when rel == 3: return l14Deco[L14DkSign + (t.Stack & 7), f];
            case L.L14DPoster when rel == 2: return l14Deco[L14DkPoster + Math.Min((int)t.Stack, 4), f];
            case L.L14DClock when rel == 3: return l14Deco[L14DkClock, f];
            case L.L14DBoard when rel == 2: return l14Deco[L14DkBoard, f];
            case L.L14DXray when rel == 2: return l14Deco[L14DkXray, f];
            case L.L14DBlood when rel == 2: return l14Deco[L14DkBlood, f];
            case L.L14DBloodDrip when rel == 3: return l14Deco[L14DkDrip, f];
            case L.L14DBloodDrip when rel == 2: return l14Deco[L14DkBlood, f];
            case L.L14DMould when rel == 2 + (int)((uint)(gx ^ gz) & 1): return l14Deco[L14DkMould, f];
            case L.L14DScratches when rel == 2: return l14Deco[L14DkScratches, f];
            case L.L14DExit when rel == 3: return l14Deco[L14DkExit, f];
            case L.L14DSanitizer when rel == 2: return l14Deco[L14DkSanitizer, f];
            case L.L14DExtinguisher when rel == 2: return l14Deco[L14DkExtinguisher, f];
            case L.L14DTrg when rel == 2: return l14Deco[L14DkTrg, f];
        }
        // The handrail at the foot of a wall along a hall or corridor (under whatever hangs above it there)
        if (rel == 1 && t.Detail is L.L14DRail or L.L14DPlate or L.L14DSign or L.L14DClock or L.L14DExit or L.L14DSanitizer or L.L14DExtinguisher
            && t.Depth is L.L14MPaint or L.L14MWhite or L.L14MWhiteMoss or L.L14MMould)
            return l14Rail[white ? 1 : 0, f];
        return L14WallBase(t, gx, gz, rel);
    }
}
