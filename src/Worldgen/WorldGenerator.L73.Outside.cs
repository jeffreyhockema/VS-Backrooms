using Atp = Backrooms.Worldgen.WorldLayout.L73AtticPart;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 73's castle from outside (round 4, 2026-11-02; models in tools/gen_73_r4_castle.py): the masonry weathered (moss and
/// damp at the foot, rain streaks under the parapets, pale quoins at the corners); machicolations (stepped corbels carrying a
/// projecting floor) under every parapet, the merlons standing on them with sloped caps, some with arrow slits; arrow slits
/// in the towers; conical slate roofs with iron finials on the corner towers, the gatehouse's drums and the keep's turrets;
/// the gatehouse's two half-round drum towers standing out before the gate, a pointed arch with the raised portcullis
/// hanging into it; the attic under a 45-degree slate roof with stone gables, coped and crossed, dormers, an eave with its
/// gutter and a ridge with iron cresting; chimney caps with pots; the keep's windows framed in stone with pointed heads, the
/// rooms' light showing between the boards. Side indices are <see cref="Sides"/>' (0 north, 1 east, 2 south, 3 west).
/// </summary>
public sealed partial class WorldGenerator
{
    private int l73Foot, l73Streak, l73Quoin, l73ChimneyCap;
    private readonly int[,] l73Corbel = new int[2, 4], l73Merlon = new int[3, 4], l73Roof = new int[5, 4], l73Dormer = new int[3, 4],
        l73Window = new int[2, 4], l73Arch = new int[8, 2], l73Drum = new int[8, 5];
    private readonly int[] l73Slit = new int[4], l73Cone = new int[3];
    private readonly int[,] l73Wreck = new int[2, 4];
    private readonly int[] l73Hood = new int[2];
    private readonly int[,] l73String = new int[2, 4];
    private readonly int[] l73Bartizan = new int[4], l73Stairs = new int[4];
    // the castle's own chairs and tables (round 4, in place of the Level 5 hotel's)
    private readonly int[] l73Chair = new int[4], l73WingChair = new int[4], l73LowTable = new int[4], l73Sideboard = new int[4];
    private readonly int[,] l73Settee = new int[2, 4];
    private readonly int[] l73Armoire = new int[4], l73Bedside = new int[4], l73Drawers = new int[4], l73Desk = new int[4], l73Clock = new int[4], l73Privy = new int[4];

    private const int L73Straight = 0, L73Corner = 1, L73MerlonPlain = 0, L73MerlonSlit = 1, L73MerlonCorner = 2;
    private const int L73RoofSlate = 0, L73RoofEave = 1, L73RoofRidge = 2, L73RoofGable = 3, L73RoofPeak = 4;
    private const int L73DrumFoot = 0, L73DrumBody = 1, L73DrumString = 2, L73DrumCorbel = 3, L73DrumMerlon = 4;

    private void InitL73Outside()
    {
        l73Foot = Id("l73-silverfoot");
        l73Streak = Id("l73-silverstreak");
        l73Quoin = Id("l73-quoin");
        l73ChimneyCap = Id("l73-chimneycap");
        string[] corbels = { "straight", "corner" }, merlons = { "plain", "slit", "corner" }, roofs = { "slate", "eave", "ridge", "gable", "gablepeak" },
            dormers = { "window", "roof", "roofback" }, windows = { "low", "high" }, courses = { "foot", "body", "string", "corbel", "merlon" },
            cones = { "big", "drum", "small" };
        for (int f = 0; f < 4; f++)
        {
            for (int k = 0; k < 2; k++) l73Corbel[k, f] = Id($"l73-corbel-{corbels[k]}-{Sides[f]}");
            for (int k = 0; k < 2; k++) l73String[k, f] = Id($"l73-string-{corbels[k]}-{Sides[f]}");
            for (int k = 0; k < 3; k++) l73Merlon[k, f] = Id($"l73-merlon-{merlons[k]}-{Sides[f]}");
            for (int k = 0; k < 5; k++) l73Roof[k, f] = Id($"l73-roof-{roofs[k]}-{Sides[f]}");
            for (int k = 0; k < 3; k++) l73Dormer[k, f] = Id($"l73-dormer-{dormers[k]}-{Sides[f]}");
            for (int k = 0; k < 2; k++) l73Window[k, f] = Id($"l73-window-{windows[k]}-{Sides[f]}");
            l73Slit[f] = Id("l73-slit-" + Sides[f]);
            l73Bartizan[f] = Id("l73-bartizan-" + Sides[f]);
            l73Stairs[f] = Id("l73-stairs-" + Sides[f]);
            l73Chair[f] = Id("l73-chair-" + Sides[f]);
            l73WingChair[f] = Id("l73-wingchair-" + Sides[f]);
            l73LowTable[f] = Id("l73-lowtable-" + Sides[f]);
            l73Sideboard[f] = Id("l73-sideboard-" + Sides[f]);
            l73Settee[0, f] = Id("l73-settee-l-" + Sides[f]);
            l73Settee[1, f] = Id("l73-settee-r-" + Sides[f]);
            l73Armoire[f] = Id("l73-armoire-" + Sides[f]);
            l73Bedside[f] = Id("l73-bedside-" + Sides[f]);
            l73Drawers[f] = Id("l73-drawers-" + Sides[f]);
            l73Desk[f] = Id("l73-desk-" + Sides[f]);
            l73Clock[f] = Id("l73-clock-" + Sides[f]);
            l73Privy[f] = Id("l73-privy-" + Sides[f]);
            l73Wreck[0, f] = Id("l73-wreck-ribs-" + Sides[f]);
            l73Wreck[1, f] = Id("l73-wreck-planks-" + Sides[f]);
        }
        for (int k = 0; k < 3; k++) l73Cone[k] = Id("l73-cone-" + cones[k]);
        l73Hood[0] = Id("l73-hood-l");
        l73Hood[1] = Id("l73-hood-r");
        for (int col = 0; col < 4; col++)
            for (int row = 3; row <= 4; row++)
            {
                l73Arch[col + 4 * (row - 3), 0] = Id($"l73-arch-{col}{row}-plain");
                l73Arch[col + 4 * (row - 3), 1] = Id($"l73-arch-{col}{row}-gate");
            }
        for (int dx = -2; dx <= 1; dx++)
            for (int dz = 0; dz <= 1; dz++)
                for (int k = 0; k < 5; k++) l73Drum[(dx + 2) * 2 + dz, k] = Id($"l73-drum-{dx + 2}{dz}-{courses[k]}");
    }

    private static int L73Ccw(int side) => (side + 3) & 3;

    /// <summary>A tower's or turret's top ring: which side a perimeter cell faces out to and whether it is a corner (the
    /// corner variants face their side and the one anticlockwise: NW is "north", NE "east", SE "south", SW "west"); -1 inside.</summary>
    private static (int Side, bool Corner) L73RingSide(int a, int b, int size)
    {
        int m = size - 1;
        if (a == 0 && b == 0) return (0, true);
        if (a == m && b == 0) return (1, true);
        if (a == m && b == m) return (2, true);
        if (a == 0 && b == m) return (3, true);
        if (b == 0) return (0, false);
        if (a == m) return (1, false);
        if (b == m) return (2, false);
        if (a == 0) return (3, false);
        return (-1, false);
    }

    /// <summary>The machicolation course and the merlons over it for a ring cell (side from <see cref="L73RingSide"/>).</summary>
    private int L73Corbels(int side, bool corner) => l73Corbel[corner ? L73Corner : L73Straight, side];

    private int L73MerlonFor(int side, bool corner, int a, int b) =>
        corner ? l73Merlon[L73MerlonCorner, side] : ((a + b) & 1) == 0 ? l73Merlon[(a * 7 + b * 3) % 4 == 0 ? L73MerlonSlit : L73MerlonPlain, side] : 0;

    /// <summary>A curtain wall's block (castle-local u, v, c over the plateau): the outer course weathered, its machicolations
    /// at c 7 and merlons at c 8, an arrow slit now and then.</summary>
    private int L73CurtainBlock(int u, int v, int c)
    {
        const int w = WorldLayout.L73CastleW, d = WorldLayout.L73CastleD;
        int outer = v == 0 ? 0 : u == w - 1 ? 1 : v == d - 1 ? 2 : u == 0 ? 3 : -1;
        if (c <= 1) return l73Foot;
        if (c == 3 && outer >= 0 && (u * 5 + v * 3) % 9 == 4 && !(v == 0 && u is >= 25 and <= 30) && !(v == d - 1 && u is >= 19 and <= 23))
            return l73Slit[outer];
        if (c == 5 && outer >= 0) return l73String[L73Straight, outer];
        if (c <= 5) return l73Silver;
        if (c == 6) return outer >= 0 ? l73Streak : l73Silver;
        if (c == 7) return outer >= 0 ? l73Corbel[L73Straight, outer] : l73Silver;
        if (c == 8 && outer >= 0 && ((u + v) & 1) == 0) return l73Merlon[(u + v) % 6 == 0 ? L73MerlonSlit : L73MerlonPlain, outer];
        return 0;
    }

    /// <summary>A corner tower (6 x 6): quoins at its corners, slits in its outer faces, machicolations at c 10, merlons at
    /// c 11 and the conical slate roof over its middle.</summary>
    private int L73TowerBlock(int u, int v, int c)
    {
        const int w = WorldLayout.L73CastleW, d = WorldLayout.L73CastleD;
        int a = u < 6 ? u : u - (w - 6), b = v < 6 ? v : v - (d - 6);
        var (side, corner) = L73RingSide(a, b, 6);
        bool outerFace = u == 0 || v == 0 || u == w - 1 || v == d - 1;
        if (c <= 1) return side >= 0 ? l73Foot : l73Silver;
        if (c == 5 && side >= 0) return l73String[corner ? L73Corner : L73Straight, side];
        if (c <= 9)
        {
            if (corner) return l73Quoin;
            if (side >= 0 && outerFace)
            {
                int along = (side & 1) == 0 ? a : b;
                if (c == 4 && along == 2 || c == 7 && along == 3) return l73Slit[side];
            }
            return c == 9 && side >= 0 ? l73Streak : l73Silver;
        }
        if (c == 10) return side >= 0 ? L73Corbels(side, corner) : l73Silver;
        if (c == 11)
        {
            // (round 4: a bartizan at the castle's own corner)
            if (corner && (u == 0 || u == w - 1) && (v == 0 || v == d - 1)) return l73Bartizan[side];
            if (side >= 0) return L73MerlonFor(side, corner, a, b);
            return a == 2 && b == 2 ? l73Cone[0] : 0;
        }
        return 0;
    }

    /// <summary>The gatehouse's towers behind their drums (4 x 5, castle-local u 22-25 and 30-33, v 43-47): the drum goes on
    /// out from their south edge (<see cref="L73DrumBlock"/>), so that edge has no parapet of its own.</summary>
    private int L73GateTowerBlock(int u, int v, int c)
    {
        int a = u - (u < 28 ? 22 : 30), b = v - 43;
        int side = a == 0 && b == 0 ? 0 : a == 3 && b == 0 ? 1 : b == 0 ? 0 : a == 3 ? 1 : a == 0 ? 3 : -1;
        bool corner = b == 0 && a is 0 or 3;
        if (c <= 1) return side >= 0 ? l73Foot : l73Silver;
        if (c == 5 && side >= 0) return l73String[corner ? L73Corner : L73Straight, side];
        if (c <= 9)
        {
            if (corner) return l73Quoin;
            return c == 9 && side >= 0 ? l73Streak : l73Silver;
        }
        if (c == 10) return side >= 0 ? L73Corbels(side, corner) : l73Silver;
        if (c == 11)
        {
            if (side >= 0) return L73MerlonFor(side, corner, a, b);
            return a == 1 && b == 4 ? l73Cone[1] : 0; // (the drum's cone, about the corner it shares with the drum's middle)
        }
        return 0;
    }

    /// <summary>Whether a castle-local position is under one of the gatehouse's drums (outside the castle's square, before the
    /// gate towers: u 22-25 and 30-33, v 48-49), and its cell from the drum's middle.</summary>
    public static bool L73DrumCell(int u, int v, out int dx, out int dz)
    {
        dz = v - WorldLayout.L73CastleD;
        dx = u - (u < 28 ? 24 : 32);
        return dz is 0 or 1 && (u is >= 22 and <= 25 || u is >= 30 and <= 33);
    }

    /// <summary>A drum's block over the plateau (c 1 to 11; the ground stays at c 0).</summary>
    private int L73DrumBlock(int dx, int dz, int c)
    {
        int course = c switch
        {
            <= 0 => -1,
            <= 2 => L73DrumFoot,
            6 => L73DrumString,
            <= 9 => L73DrumBody,
            10 => L73DrumCorbel,
            11 => L73DrumMerlon,
            _ => -1,
        };
        if (course < 0) return 0;
        if (course == L73DrumMerlon && dz == 0 && dx is -1 or 0) return 0; // (inside the parapet: the cone's deck)
        return l73Drum[(dx + 2) * 2 + dz, course];
    }

    /// <summary>The gate (u 26-29, v 46-47): the pointed arch cut into its top cells, the raised portcullis in the outer one,
    /// machicolations and merlons over it on the outside.</summary>
    private int L73GateBlock(int u, int v, int c)
    {
        const int d = WorldLayout.L73CastleD;
        int col = u - 26;
        if (c == 0) return l73PathFlags;
        if (c is 3 or 4)
        {
            if (c == 3 && col is 1 or 2) return 0;
            return l73Arch[col + 4 * (c - 3), v == d - 1 && c == 4 ? 1 : 0];
        }
        // a candle-sconce on each side of the passage, on its inner half (the castle is "fully furnished and lit"; the glow
        // shows through the gate from the bridge)
        if (c == 2 && v == d - 2 && col is 0 or 3) return l73Sconce[col == 0 ? 1 : 3];
        if (c <= 4) return 0;
        if (c <= 6) return v == d - 1 && c == 6 ? l73Streak : l73Silver;
        if (c == 7) return v == d - 1 ? l73Corbel[L73Straight, 2] : l73Silver;
        return c == 8 && v == d - 1 && ((u + v) & 1) == 0 ? l73Merlon[col == 1 ? L73MerlonSlit : L73MerlonPlain, 2] : 0;
    }

    /// <summary>The keep's outer wall, at a slab (c a multiple of the storey): the string course, but at the terrace the
    /// machicolations under the parapet (not under the turrets).</summary>
    private int L73KeepRingCourse(int ku, int kv, int c)
    {
        const int kw = WorldLayout.L73KeepW, kd = WorldLayout.L73KeepD;
        bool turret = (ku < 3 || ku >= kw - 3) && (kv < 3 || kv >= kd - 3);
        if (c != WorldLayout.L73Terrace || turret)
        {
            // a moulded string course (round 4), turning the corners
            bool corner = (ku is 0 or kw - 1) && (kv is 0 or kd - 1);
            int cs = !corner ? L73KeepOut(ku, kv) : ku == 0 ? (kv == 0 ? 0 : 3) : (kv == 0 ? 1 : 2);
            return l73String[corner ? L73Corner : L73Straight, cs];
        }
        int side = kv == 0 ? 0 : ku == kw - 1 ? 1 : kv == kd - 1 ? 2 : 3;
        return l73Corbel[L73Straight, side];
    }

    /// <summary>The way a keep ring cell faces out (0 north, 1 east, 2 south, 3 west).</summary>
    private static int L73KeepOut(int ku, int kv) =>
        kv == 0 ? 0 : ku == WorldLayout.L73KeepW - 1 ? 1 : kv == WorldLayout.L73KeepD - 1 ? 2 : 3;

    /// <summary>A keep turret's top (3 x 3 at each corner, over the terrace): machicolations at c 19, the conical roof over its
    /// middle at c 20.</summary>
    private int L73TurretTop(int ku, int kv, int c)
    {
        const int kw = WorldLayout.L73KeepW, kd = WorldLayout.L73KeepD;
        int a = ku < 3 ? ku : ku - (kw - 3), b = kv < 3 ? kv : kv - (kd - 3);
        var (side, corner) = L73RingSide(a, b, 3);
        if (c <= 17) return corner && (ku is 0 or kw - 1) && (kv is 0 or kd - 1) ? l73Quoin : l73Silver;
        if (c == 18) return side >= 0 ? l73Streak : l73Silver;
        if (c == 19) return side >= 0 ? L73Corbels(side, corner) : l73Silver;
        return c == 20 && side < 0 ? l73Cone[2] : 0;
    }

    /// <summary>The height (c) of the attic roof's slope over a row (kv 4-15): up from the eaves at 18 to the ridge at 23.</summary>
    private static int L73RoofC(int kv) => kv <= 9 ? 18 + (kv - 4) : 18 + (15 - kv);

    /// <summary>The dormers: in the eave rows (kv 4 north, 15 south) at these columns.</summary>
    private static bool L73Dormer(int ku, int kv) => kv == 4 && ku is 13 or 22 || kv == 15 && ku is 12 or 23;

    /// <summary>
    /// The attic's roof and gables at c 18 and over (keep-local ku 9-26, kv 4-15), or -1 where the attic's own walls and
    /// furnishings carry on (<see cref="Atp"/>): slopes rising from the eaves to the ridge between rows 9 and 10; the stone
    /// gables at both ends, coped, with a cross at the top; dormers in the eaves.
    /// </summary>
    private int L73AtticRoof(int ku, int kv, int c)
    {
        if (ku is < 9 or > 26 || kv is < 4 or > 15 || c < 18) return -1;
        int rc = L73RoofC(kv);
        int rise = kv <= 9 ? 2 : 0; // the north slope rises toward the south, the south slope toward the north
        bool gable = ku is 9 or 26;
        int outward = kv <= 9 ? 0 : 2;
        // A dormer: its window in the eave, its little roof over it and over the slope's next row
        if (!gable && c == 18 && L73Dormer(ku, kv)) return l73Dormer[0, outward];
        if (!gable && c == 19 && L73Dormer(ku, kv)) return l73Dormer[1, outward];
        if (!gable && c == 19 && (L73Dormer(ku, kv - 1) && kv == 5 || L73Dormer(ku, kv + 1) && kv == 14)) return l73Dormer[2, outward];
        if (c > rc) return 0;
        if (c < rc) return gable ? l73Silver : -1;
        if (gable) return kv == 9 ? l73Roof[L73RoofPeak, rise] : l73Roof[L73RoofGable, rise];
        int kind = kv is 4 or 15 ? L73RoofEave : kv == 9 ? L73RoofRidge : L73RoofSlate;
        return l73Roof[kind, rise];
    }

    /// <summary>A window in the keep's outer wall: its stone-framed lower half (h 2) or pointed head (h 3).</summary>
    private int L73WindowBlock(int ku, int kv, int h) => l73Window[h == 2 ? 0 : 1, L73KeepOut(ku, kv)];

    /// <summary>What lies on a beach column (ash sand), one over the ground: now and then a black rock, seldom washed-up planks,
    /// more seldom a boat's ribs; 0 nothing.</summary>
    private int L73ShoreThing(int gx, int gz)
    {
        ulong h = Hashing.Hash(seed, gx, gz, 0x2190);
        double r = Hashing.Unit(h);
        int f = (int)(Hashing.Mix(h) & 3);
        if (r < 1 / 700.0) return l73Wreck[0, f];
        if (r < 1 / 700.0 + 1 / 260.0) return l73Wreck[1, f];
        if (r < 1 / 700.0 + 1 / 260.0 + 1 / 40.0) return l73Boulder[(int)((Hashing.Mix(h) >> 3) & 1), f];
        return 0;
    }
}
