using WL = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 120's dressing (round 3; laid out in WorldLayout.Level120.Dress.cs, assets by tools/gen_120_detail.py):
/// the UPS and battery cabinets, the cooling units and their ducts, KVM carts, mop buckets, fallen ceiling tiles, paper,
/// the banks' end panels, shelving, the holes in the raised floor; and <c>l120-walldeco</c>, the wall with something on its
/// face (plates, warnings, notes, fire points, cables, screens, plans, stencils, conduit, EXIT signs, a panel; a crack or a
/// smudge in a White Void). All looked up softly (<see cref="L120Block"/>): what is missing is left out.
/// </summary>
public sealed partial class WorldGenerator
{
    private readonly int[,,] l120Ups = new int[2, 2, 4];
    private readonly int[,] l120Battery = new int[2, 4], l120Crac = new int[4, 4], l120Shelf = new int[2, 4], l120RowEnd = new int[9, 4];
    private readonly int[] l120Lifter = new int[4];
    private readonly int[] l120Kvm = new int[4], l120Mop = new int[4], l120Debris = new int[4], l120Paper = new int[4];
    private int l120FloorHole, l120VoidGlitch, l120VoidPanelDead;
    /// <summary>(Round 4) The desks with monitors on arms [dead/glitch, side], the fire suppression bank [lower/upper/pipe, side], tape libraries.</summary>
    private readonly int[,] l120Console = new int[2, 4], l120FireSup = new int[3, 4], l120TapeLib = new int[2, 4];
    /// <summary>The wall dressing: [kind, side] (see <see cref="L120DecoKinds"/>), the plates [text, side], notes, stencils.</summary>
    private readonly int[,] l120Deco = new int[18, 4], l120Plate = new int[20, 4], l120Note = new int[4, 4], l120Stencil = new int[8, 4];

    /// <summary>The single wall dressings by index in <see cref="l120Deco"/>.</summary>
    private static readonly string[] L120DecoKinds =
    {
        "auth", "fire-lower", "fire-upper", "cables-lower", "cables-mid", "cables-upper", "screens-dead-lower", "screens-dead-upper",
        "screens-glitch-lower", "screens-glitch-upper", "evac", "conduit", "exit-dead", "exit-lit", "panel", "crack",
        "screens-smashed-lower", "screens-smashed-upper",
    };
    private const int DecoAuth = 0, DecoFireLower = 1, DecoFireUpper = 2, DecoCables = 3, DecoScreens = 6, DecoEvac = 10, DecoConduit = 11,
        DecoExitDead = 12, DecoExitLit = 13, DecoPanel = 14, DecoCrack = 15, DecoSmashed = 16;
    private readonly int[] l120Smudge = new int[4];

    private void InitL120Dress()
    {
        string[] parts = { "lower", "upper" };
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            for (int p = 0; p < 2; p++)
            {
                l120Ups[p, 0, f] = L120Block($"l120-ups-{parts[p]}-whole-{side}");
                l120Ups[p, 1, f] = L120Block($"l120-ups-{parts[p]}-open-{side}", l120Ups[p, 0, f]);
                l120Battery[p, f] = L120Block($"l120-battery-{parts[p]}-{side}");
                l120Shelf[p, f] = L120Block($"l120-shelf-{parts[p]}-{side}");
            }
            l120Crac[0, f] = L120Block("l120-crac-lower-" + side);
            l120Crac[1, f] = L120Block("l120-crac-upper-" + side);
            l120Crac[2, f] = L120Block("l120-crac-duct-" + side);
            l120Crac[3, f] = L120Block("l120-crac-loweropen-" + side, l120Crac[0, f]);
            l120RowEnd[0, f] = L120Block("l120-rowend-lower-" + side);
            for (int c = 0; c < 8; c++) l120RowEnd[1 + c, f] = L120Block($"l120-rowend-{(char)('a' + c)}-{side}");
            l120Kvm[f] = L120Block("l120-kvm-" + side);
            l120Lifter[f] = L120Block("l120-lifter-" + side);
            l120Console[0, f] = L120Block("l120-console-dead-" + side, L120Block("l120-terminal-dead-" + side));
            l120Console[1, f] = L120Block("l120-console-glitch-" + side, l120Console[0, f]);
            l120FireSup[0, f] = L120Block("l120-firesup-lower-" + side);
            l120FireSup[1, f] = L120Block("l120-firesup-upper-" + side);
            l120FireSup[2, f] = L120Block("l120-firesup-pipe-" + side);
            l120TapeLib[0, f] = L120Block("l120-tapelib-lower-" + side);
            l120TapeLib[1, f] = L120Block("l120-tapelib-upper-" + side);
            l120Mop[f] = L120Block("l120-mop-" + side);
            l120Debris[f] = L120Block("l120-debris-" + side);
            l120Paper[f] = L120Block("l120-paper-" + side);
            for (int k = 0; k < L120DecoKinds.Length; k++) l120Deco[k, f] = L120Block($"l120-walldeco-{L120DecoKinds[k]}-{side}");
            l120Smudge[f] = L120Block("l120-walldeco-smudge-" + side);
            for (int i = 0; i < 20; i++) l120Plate[i, f] = L120Block($"l120-walldeco-plate-{i}-{side}");
            for (int i = 0; i < 4; i++) l120Note[i, f] = L120Block($"l120-walldeco-note-{i}-{side}");
            for (int i = 0; i < 8; i++) l120Stencil[i, f] = L120Block($"l120-walldeco-stencil-{(char)('a' + i)}-{side}");
        }
        l120FloorHole = L120Block("l120-floorhole-open");
        l120VoidGlitch = L120Block("l120-void-glitch");
        l120VoidPanelDead = L120Block("l120-void-paneldead");
    }

    /// <summary>
    /// What is on a wall's face <paramref name="rel"/> above the floor (0 for the plain wall): the tile's decoration, or along
    /// the passages the conduit under the ceiling (on the walls of their tray side: x mod 96 = 5 facing west, z mod 96 = 5
    /// facing north).
    /// </summary>
    private int L120DecoBlock(in Tile t, int gx, int gz, int rel)
    {
        int f = Facing(t.Pier);
        switch (t.Variant)
        {
            case WL.L120DecoPlate when rel == 2: return l120Plate[t.Detail < 20 ? t.Detail : 0, f];
            case WL.L120DecoAuth when rel == 2: return l120Deco[DecoAuth, f];
            case WL.L120DecoNote when rel == 2: return l120Note[t.Detail & 3, f];
            case WL.L120DecoFire when rel is 1 or 2: return l120Deco[rel == 1 ? DecoFireLower : DecoFireUpper, f];
            case WL.L120DecoCables when rel is >= 1 and <= 3: return l120Deco[DecoCables + rel - 1, f];
            case WL.L120DecoScreens when rel is 2 or 3:
                // (Detail: bits 0 and 1 a corrupted picture on the lower or upper screen, bits 2 and 3 the screen smashed)
                if ((t.Detail & (rel == 2 ? 4 : 8)) != 0) return l120Deco[DecoSmashed + rel - 2, f];
                bool glitch = (t.Detail & (rel == 2 ? 1 : 2)) != 0;
                return l120Deco[DecoScreens + (glitch ? 2 : 0) + rel - 2, f];
            case WL.L120DecoEvac when rel == 2: return l120Deco[DecoEvac, f];
            case WL.L120DecoStencil when rel == 2: return l120Stencil[t.Detail & 7, f];
            case WL.L120DecoExit when rel == 3: return l120Deco[t.Detail != 0 ? DecoExitLit : DecoExitDead, f];
            case WL.L120DecoPanel when rel == 2: return l120Deco[DecoPanel, f];
            case WL.L120DecoCrack when rel == 2: return l120Deco[DecoCrack, f];
            case WL.L120DecoSmudge when rel == 2: return l120Smudge[f];
        }
        if (rel != 3 || t.Kind != TileKind.Wall || t.Zone != (byte)WL.L120Zone.Wall) return 0;
        bool west = Hashing.Mod(gx, WL.L120Period) == 5, north = Hashing.Mod(gz, WL.L120Period) == 5;
        if (west == north) return 0; // (not along a passage, or a corner)
        // (Only where the passage really runs beside it)
        Tile beside = west ? TileAt(gx - 1, gz) : TileAt(gx, gz - 1);
        if (beside.Kind != TileKind.Floor || beside.Zone != (byte)WL.L120Zone.Corridor) return 0;
        return l120Deco[DecoConduit, west ? 3 : 0];
    }

    /// <summary>The EXIT sign over a door back to the offices, facing the floor in front of it: lit (on its battery) over one door in two.</summary>
    private int L120ExitOverDoor(int gx, int gz)
    {
        bool lit = (Hashing.Hash(seed, gx, gz, 0x2623) & 1) == 0;
        (int Dx, int Dz, int Facing)[] ways = { (0, -1, 0), (1, 0, 1), (0, 1, 2), (-1, 0, 3) };
        foreach (var (dx, dz, f) in ways)
        {
            Tile n = TileAt(gx + dx, gz + dz);
            if (n.Kind == TileKind.Floor && n.Level == WL.Level120) return l120Deco[lit ? DecoExitLit : DecoExitDead, f];
        }
        return 0;
    }

    /// <summary>Round 3's props, <paramref name="rel"/> above the floor: the block, 0 for air, or -1 if the tile holds none of them.</summary>
    private int L120DressProp(in Tile t, int rel, int f)
    {
        switch (t.Variant)
        {
            case WL.L120Ups: return rel <= 2 ? l120Ups[rel - 1, t.Detail == WL.L120UpsOpen ? 1 : 0, f] : 0;
            case WL.L120Battery: return rel <= 2 ? l120Battery[rel - 1, f] : 0;
            case WL.L120Crac: return rel == 1 && t.Detail == 1 ? l120Crac[3, f] : rel <= 3 ? l120Crac[rel - 1, f] : 0;
            case WL.L120Shelf: return rel <= 2 ? l120Shelf[rel - 1, f] : 0;
            case WL.L120RowEnd: return rel == 1 ? l120RowEnd[0, f] : rel == 2 ? l120RowEnd[1 + (t.Detail & 7), f] : 0;
            case WL.L120Kvm: return rel == 1 ? l120Kvm[f] : 0;
            case WL.L120Mop: return rel == 1 ? l120Mop[f] : 0;
            case WL.L120Debris: return rel == 1 ? l120Debris[f] : 0;
            case WL.L120Paper: return rel == 1 ? l120Paper[f] : 0;
            case WL.L120FireSup: return rel <= 3 ? l120FireSup[rel - 1, f] : 0;
            case WL.L120TapeLib: return rel <= 2 ? l120TapeLib[rel - 1, f] : 0;
            case WL.L120Lifter: return rel == 1 ? l120Lifter[f] : 0;
        }
        return -1;
    }
}
