using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 974, Kitty's House (kept as level 18), laid out in WorldLayout.Level974.cs. Its floor is the shared
/// one. A house stands four blocks of air high: the floor at rel 0, walls from 1 to 4 (a white baseboard at the
/// bottom, crown moulding at the top), the ceiling at 5, and solid nothing everywhere else. Furniture stands at rel 1
/// (the fridge and the pantry are two tall), pictures and mirrors hang at 2, shelves and the cat clock at 3, fairy
/// lights at 4.
///
/// Every block is looked up softly (<see cref="L974Block"/>): until the level's assets exist, what is missing is left
/// out (or drawn as concrete, for structure), logged once, so the level can be built and walked before it is dressed.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L974WallKinds = { "plain", "base", "crown", "backsplash", "bathtile", "bathtilecap" };
    private static readonly string[] L974Paintings = { "clouds", "hills", "rainbow", "sunset" };
    private static readonly string[] L974Beddings = { "hearts", "strawberries", "stars" };
    private static readonly string[] L974Counters = { "plain", "corner", "sink", "canisters", "utensils" };
    private static readonly string[] L974Rugs = { "nw", "ne", "sw", "se" };

    private readonly int[] l974Wall = new int[6], l974Floor = new int[3], l974Slope = new int[4], l974Lintel = new int[2], l974Casing = new int[2];
    private readonly int[,,] l974Window = new int[4, 4, 4]; // part (bl br tl tr), painting, facing
    private readonly int[,] l974Fairy = new int[2, 4];
    private readonly int[] l974NightLight = new int[4], l974Rod = new int[4];
    private int l974Ceiling, l974LightOn, l974Table, l974CatBed;
    private readonly int[,,] l974Bed = new int[3, 2, 4]; // bedding, part (head, feet), side
    private readonly int[,] l974Hung = new int[15, 4]; // a thing hung on the wall, by kind (L974Hung), facing
    private readonly Dictionary<(ushort Prop, int Stack), int[]> l974Props = new(); // facing -> block
    private readonly HashSet<string> l974Missing = new();

    /// <summary>A block of the level's, or <paramref name="fallback"/> if its asset is not there (logged once).</summary>
    private int L974Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l974Missing.Add(code)) api.Logger.Warning("[backrooms] Level 974: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>Looks up the level's blocks, once, when the generator is made.</summary>
    private void InitL974()
    {
        for (int i = 0; i < L974WallKinds.Length; i++) l974Wall[i] = L974Block("l974-wall-" + L974WallKinds[i], concreteId);
        l974Floor[0] = L974Block("l974-floor-carpet", concreteId);
        l974Floor[1] = L974Block("l974-floor-checker", concreteId);
        l974Floor[2] = L974Block("l974-floor-bathhex", concreteId);
        l974Ceiling = L974Block("l974-ceiling", concreteId);
        l974LightOn = L974Block("l974-downlight-on", l974Ceiling);
        l974Lintel[0] = L974Block("l974-lintel-ns", l974Wall[2]);
        l974Lintel[1] = L974Block("l974-lintel-we", l974Wall[2]);
        l974Casing[0] = L974Block("l974-casing-ns");
        l974Casing[1] = L974Block("l974-casing-we");
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            l974Slope[f] = L974Block("l974-slope-" + side, l974Wall[0]);
            l974NightLight[f] = L974Block("l974-nightlight-" + side);
            l974Rod[f] = L974Block("l974-closetrod-" + side);
            l974Fairy[0, f] = L974Block("l974-fairylights-on-" + side);
            l974Fairy[1, f] = L974Block("l974-fairylights-off-" + side);
            string[] parts = { "bl", "br", "tl", "tr" };
            for (int p = 0; p < 4; p++)
                for (int k = 0; k < 4; k++) l974Window[p, k, f] = L974Block($"l974-window-{parts[p]}-{L974Paintings[k]}-{side}", p < 2 ? l974Wall[0] : l974Wall[0]);
            for (int b = 0; b < 3; b++)
            {
                l974Bed[b, 0, f] = L974Block($"l974-bed-{L974Beddings[b]}-head-{side}");
                l974Bed[b, 1, f] = L974Block($"l974-bed-{L974Beddings[b]}-feet-{side}");
            }
            for (int p = 0; p < WorldLayout.L974Hung.Posters.Length; p++)
                l974Hung[WorldLayout.L974Hung.PosterFirst + p, f] = L974Block($"l974-poster-{WorldLayout.L974Hung.Posters[p]}-{side}");
            l974Hung[WorldLayout.L974Hung.FrameWhite, f] = L974Block("l974-frame-white-" + side);
            l974Hung[WorldLayout.L974Hung.FrameGold, f] = L974Block("l974-frame-gold-" + side);
            l974Hung[WorldLayout.L974Hung.ShelfPlush, f] = L974Block("l974-shelf-plush-" + side);
            l974Hung[WorldLayout.L974Hung.ShelfFigures, f] = L974Block("l974-shelf-figures-" + side);
            l974Hung[WorldLayout.L974Hung.Mirror, f] = L974Block("l974-mirror-" + side);
            l974Hung[WorldLayout.L974Hung.TowelRail, f] = L974Block("l974-towelrail-" + side);
            l974Hung[WorldLayout.L974Hung.CatClock, f] = L974Block("l974-catclock-" + side);
            l974Hung[WorldLayout.L974Hung.NightLight, f] = l974NightLight[f];
        }
        l974Table = L974Block("l974-table");
        l974CatBed = L974Block("l974-catbed");

        void Faced(ushort prop, int stack, string code)
        {
            var ids = new int[4];
            for (int f = 0; f < 4; f++) ids[f] = L974Block($"{code}-{Sides[f]}");
            l974Props[(prop, stack)] = ids;
        }
        Faced(Props.L974Nightstand, 0, "l974-nightstand");
        Faced(Props.L974PlushHeap, 0, "l974-plushheap-a");
        Faced(Props.L974PlushHeap, 1, "l974-plushheap-b");
        Faced(Props.L974Desk, 0, "l974-desk-plain");
        Faced(Props.L974Desk, 1, "l974-desk-computer");
        Faced(Props.L974Chair, 0, "l974-chair-desk");
        Faced(Props.L974Chair, 1, "l974-chair-dining");
        Faced(Props.L974Dresser, 0, "l974-dresser");
        Faced(Props.L974Fridge, 0, "l974-fridge-lower");
        Faced(Props.L974Fridge, 1, "l974-fridge-upper");
        Faced(Props.L974Pantry, 0, "l974-pantry-lower");
        Faced(Props.L974Pantry, 1, "l974-pantry-upper");
        for (int k = 0; k < L974Counters.Length; k++) Faced(Props.L974Counter, k, "l974-counter-" + L974Counters[k]);
        Faced(Props.L974Stove, 0, "l974-stove");
        Faced(Props.L974Banquette, 0, "l974-banquette-straight");
        Faced(Props.L974Banquette, 1, "l974-banquette-corner");
        Faced(Props.L974Toilet, 0, "l974-toilet");
        Faced(Props.L974Basin, 0, "l974-basin");
        Faced(Props.L974Bathtub, 0, "l974-bathtub-head");
        Faced(Props.L974Bathtub, 1, "l974-bathtub-foot");
        for (int k = 0; k < 4; k++)
        {
            int rug = L974Block("l974-rug-" + L974Rugs[k]);
            l974Props[(Props.L974Rug, k)] = new[] { rug, rug, rug, rug };
        }
    }

    /// <summary>The block (and fluid) at <paramref name="rel"/> above the level's floor in the column of tile <paramref name="t"/>.</summary>
    private int Level974Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        // Solid nothing below the floor, above the ceiling, and between the houses
        if (rel < 0 || rel > 5 || t.Kind == TileKind.Wall && t.Pattern == WallPattern.L974Wall) return concreteId;
        if (rel == 5) return t.Kind == TileKind.Floor && t.Ceiling == CeilingKind.LightOn ? l974LightOn : l974Ceiling;

        switch (t.Kind)
        {
            case TileKind.Floor:
                return L974Room(t, rel);
            case TileKind.Doorway:
            {
                int axis = t.Pier is ArchPier.North or ArchPier.South ? 0 : 1;
                if (rel == 0) return l974Floor[0];
                if (t.Stack == 2) return 0; // (a tall opening, from layout version 9: no lintel, no casing)
                if (rel == 4) return l974Lintel[axis];
                return t.Stack == 1 ? 0 : l974Casing[axis];
            }
            default:
            {
                if (rel == 0) return concreteId;
                bool bath = t.Pattern == WallPattern.L974BathTile;
                if (rel == 4) return l974Wall[2];
                if (t.Pattern == WallPattern.L974Window && rel is 2 or 3)
                {
                    int part = (rel == 3 ? 2 : 0) + (t.Stack & 1);
                    return l974Window[part, t.Detail & 3, Facing(t.Pier)];
                }
                if (rel == 1) return bath ? l974Wall[4] : l974Wall[1];
                if (rel == 2) return bath ? l974Wall[5] : t.Pattern == WallPattern.L974Backsplash ? l974Wall[3] : l974Wall[0];
                return l974Wall[0];
            }
        }
    }

    /// <summary>A column of a room: its floor, and what stands on it, hangs on the wall beside it, or is up under the ceiling.</summary>
    private int L974Room(in Tile t, int rel)
    {
        if (rel == 0) return t.Floor switch
        {
            FloorKind.L974Checker => l974Floor[1],
            FloorKind.L974BathHex => l974Floor[2],
            _ => l974Floor[0],
        };

        // Under the alcove's sloping ceiling
        int high = t.Depth >> 2, highFacing = Facing((ArchPier)(t.Depth & 3));
        if (high == WorldLayout.L974HighSlope)
        {
            if (t.Height == 2 && rel == 4) return l974Wall[2];
            if (rel == t.Height + 1) return l974Slope[highFacing];
        }

        // Furniture
        if (t.Variant != 0)
        {
            int f = Facing(t.Pier);
            switch (t.Variant)
            {
                case Props.L974Bed:
                    if (rel == 1) return l974Bed[(t.Stack >> 1) % 3, t.Stack & 1, f];
                    break;
                case Props.L974Fridge:
                case Props.L974Pantry:
                    if (rel <= 2) return l974Props[(t.Variant, rel - 1)][f];
                    break;
                case Props.L974Table:
                    if (rel == 1) return l974Table;
                    break;
                case Props.L974CatBed:
                    if (rel == 1) return l974CatBed;
                    break;
                default:
                    if (rel == 1 && l974Props.TryGetValue((t.Variant, t.Stack), out int[] ids)) return ids[f];
                    break;
            }
        }

        // Things hung on the wall beside the tile
        int hung = t.Detail >> 2;
        if (hung > 0 && hung < l974Hung.GetLength(0))
        {
            int at = hung switch
            {
                WorldLayout.L974Hung.NightLight => 1,
                WorldLayout.L974Hung.ShelfPlush or WorldLayout.L974Hung.ShelfFigures or WorldLayout.L974Hung.CatClock => 3,
                _ => 2,
            };
            if (rel == at && !(at == 1 && t.Variant != 0)) return l974Hung[hung, Facing((ArchPier)(t.Detail & 3))];
        }
        if (t.Overhead == Overheads.L974ClosetRod && rel == 3) return l974Rod[Facing(t.Pier)];
        if (high == WorldLayout.L974HighFairy && rel == 4) return l974Fairy[0, highFacing];
        return 0;
    }
}
