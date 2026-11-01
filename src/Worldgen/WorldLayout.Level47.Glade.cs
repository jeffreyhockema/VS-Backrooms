using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 47's glade at the trail's end (Wikidot: "This glade contains either a large manor house, or an ancient megalith. The
/// two appear to exist simultaneously in a state of superposition. In either case, the glade appears to be the headquarters
/// of a group that refers to itself as the Ophion Occult Order"). Both are built in the same place (our reading of
/// "simultaneously", marked as ours in the plan): a two-storey stone manor with a slate roof, and a ring of standing stones
/// round it whose inner horseshoe of trilithons stands through the manor's rooms, floors and roof as if neither knew the
/// other were there; the Altar Stone lies in its entrance hall. The Order's banners and braziers, its long table, its
/// shelves, a ladder to the loft; its stores (supply boxes). A flagstone walk comes in from the trail's end, from the south.
/// Everything here is a pure function of the block position, in the glade's own frame (u east, v south of its middle).
/// This file is the level's own.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The manor's half-size (blocks, walls included) and its storeys: the ground floor's boards, the loft's boards, the eaves.</summary>
    public const int L47HouseU = 12, L47HouseV = 7, L47HouseFloor = 1, L47LoftFloor = 6, L47Eaves = 11;

    /// <summary>The glade's blocks (<see cref="L47GladeBlock"/>), by kind; a facing is packed above them (<see cref="L47GladeFacing"/>).</summary>
    public const int L47GAir = 0, L47GStone = 1, L47GPlinth = 2, L47GTimber = 3, L47GSlate = 4, L47GBoards = 5, L47GWindow = 6, L47GMegalith = 7,
        L47GFlag = 8, L47GLadder = 9, L47GTable = 10, L47GShelf = 11, L47GBannerTop = 12, L47GBannerFoot = 13, L47GLantern = 14, L47GBrazier = 15,
        L47GAltar = 16, L47GHearth = 17, L47GCandles = 18, L47GGrass = 19, L47GKeep = -1;

    /// <summary>The facing packed into a glade block's code (the way the thing faces: its back to the wall).</summary>
    public static ArchPier L47GladeFacing(int code) => (ArchPier)(code >> 8 & 3);

    private static int L47GF(int kind, ArchPier facing) => kind | (int)facing << 8;

    /// <summary>The outer ring's stones and the inner horseshoe's trilithons.</summary>
    private const int L47RingStones = 14, L47Trilithons = 5;
    private const double L47RingRadius = 21, L47InnerRadius = 7.5;

    /// <summary>Whether a column is inside the manor's walls (walls included).</summary>
    public bool L47InManor(int gx, int gz) => Math.Abs(gx - L47MidX) <= L47HouseU && Math.Abs(gz - L47MidZ) <= L47HouseV;

    /// <summary>
    /// A standing stone at a column, and how high it stands (its top, rel): the outer ring (a gap at the south where the walk
    /// comes in, lintels over every other pair) and the inner trilithons (through the manor, their lintels over its roof).
    /// <paramref name="lintel"/> is the height of a lintel over this column (0: none).
    /// </summary>
    public bool L47StoneAt(int gx, int gz, out int top, out int lintel)
    {
        top = lintel = 0;
        double u = gx + 0.5 - L47MidX - 0.5, v = gz + 0.5 - L47MidZ - 0.5;
        double r = Math.Sqrt(u * u + v * v);
        bool found = false;
        if (Math.Abs(r - L47RingRadius) < 2.2)
        {
            for (int k = 0; k < L47RingStones; k++)
            {
                double a = Math.PI / 2 + Math.PI / L47RingStones + k * 2 * Math.PI / L47RingStones;
                double cu = Math.Cos(a) * L47RingRadius, cv = Math.Sin(a) * L47RingRadius;
                double tan = -(u - cu) * Math.Sin(a) + (v - cv) * Math.Cos(a), rad = (u - cu) * Math.Cos(a) + (v - cv) * Math.Sin(a);
                int h = 6 + (int)(Hashing.Hash(seed, k, 1, SaltL47Mid + 0x10) % 3);
                bool paired = k % 2 == 0 && k != L47RingStones - 2;
                if (Math.Abs(tan) < 1.05 && Math.Abs(rad) < 0.75) { top = paired || k % 2 == 1 && k != L47RingStones - 1 ? 7 : h; found = true; }
                // A lintel from this stone to the next, over every other pair
                if (paired && Math.Abs(rad) < 0.75)
                {
                    double a2 = a + 2 * Math.PI / L47RingStones, cu2 = Math.Cos(a2) * L47RingRadius, cv2 = Math.Sin(a2) * L47RingRadius;
                    double vx = cu2 - cu, vz = cv2 - cv, len = Math.Sqrt(vx * vx + vz * vz);
                    double along = ((u - cu) * vx + (v - cv) * vz) / len, perp = Math.Abs((u - cu) * vz - (v - cv) * vx) / len;
                    if (along > -1 && along < len + 1 && perp < 0.75) lintel = 8;
                }
            }
        }
        if (r < L47InnerRadius + 3.5 && r > L47InnerRadius - 3.5)
        {
            for (int k = 0; k < L47Trilithons; k++)
            {
                double a = -Math.PI / 2 + k * 2 * Math.PI / L47Trilithons;
                double cu = Math.Cos(a) * L47InnerRadius, cv = Math.Sin(a) * L47InnerRadius;
                double tan = -(u - cu) * Math.Sin(a) + (v - cv) * Math.Cos(a), rad = (u - cu) * Math.Cos(a) + (v - cv) * Math.Sin(a);
                if (Math.Abs(rad) > 0.8) continue;
                if (Math.Abs(Math.Abs(tan) - 1.5) < 0.7) { top = 19; found = true; }
                if (Math.Abs(tan) < 2.3) lintel = 20;
            }
        }
        return found || lintel > 0;
    }

    /// <summary>A glade tile (inside its meadow): the manor's walls and the stones are wall, the rest open floor.</summary>
    private void L47GladeTile(ref Tile t, int gx, int gz)
    {
        t.Height = 1;
        int u = gx - L47MidX, v = gz - L47MidZ;
        bool stone = L47StoneAt(gx, gz, out int top, out _) && top > 0;
        if (L47InManor(gx, gz))
        {
            t.Zone = L47ManorZone;
            t.Floor = FloorKind.L47Bark;
            bool wall = Math.Abs(u) == L47HouseU || Math.Abs(v) == L47HouseV || Math.Abs(u) == 4 && !(v is 0 or 1);
            bool door = v == L47HouseV && Math.Abs(u) <= 1;
            if (wall && !door || stone)
            {
                t.Kind = TileKind.Wall;
                t.Pattern = WallPattern.L47Wall;
            }
            return;
        }
        if (stone)
        {
            t.Kind = TileKind.Wall;
            t.Pattern = WallPattern.L47Wall;
        }
        // (The walk in, and the braziers and banner poles beside it, are kept clear of anything put down)
        if (Math.Abs(u) <= 1 && v > L47HouseV) t.Floor = FloorKind.L47Trail;
        if (Math.Abs(u) == 3 && (v == 9 || v == 44))
        {
            t.Kind = TileKind.Wall;
            t.Pattern = WallPattern.L47Wall;
        }
    }

    /// <summary>The roof's height over a row of the manor (rel): from the eaves at the long walls to the ridge over its middle.</summary>
    private static int L47RoofAt(int v) => L47Eaves + (L47HouseV + 1 - Math.Abs(v));

    /// <summary>
    /// The glade's block at a column and height (rel), as a kind of <see cref="L47GAir"/>... with its facing packed in, or
    /// <see cref="L47GKeep"/> where the generator draws the meadow (ground, grass and flowers) as it would.
    /// </summary>
    public int L47GladeBlock(int gx, int gz, int rel)
    {
        int u = gx - L47MidX, v = gz - L47MidZ;
        int au = Math.Abs(u), av = Math.Abs(v);
        // The stones first: they stand through everything
        if (L47StoneAt(gx, gz, out int stoneTop, out int lintel))
        {
            if (stoneTop > 0 && rel >= 1 && rel <= stoneTop) return L47GMegalith;
            if (lintel > 0 && rel == lintel) return L47GMegalith;
        }
        // The Altar Stone, lying in the entrance hall
        if (au <= 2 && v is -1 or 0 && rel == 2) return L47GAltar;
        // Outside the manor: the walk, the braziers by the door, the banner poles where the walk leaves the trail
        if (au > L47HouseU + 1 || av > L47HouseV + 1)
        {
            if (au <= 1 && v > L47HouseV && rel == 1) return L47GFlag;
            if (au == 3 && v == 9) return rel == 1 ? L47GFlag : rel == 2 ? L47GBrazier : L47GKeep;
            if (au == 3 && v == 44)
            {
                if (rel >= 2 && rel <= 7) return L47GTimber;
                return L47GKeep;
            }
            if (au == 3 && v == 45 && rel == 6) return L47GF(L47GBannerTop, ArchPier.South);
            if (au == 3 && v == 45 && rel == 5) return L47GF(L47GBannerFoot, ArchPier.South);
            // The chimney stacks against the gable ends
            if (au == L47HouseU + 1 && v is -1 or 0 && rel >= 1 && rel <= 22) return L47GStone;
            if (au == L47HouseU + 2 && v is -1 or 0 && rel >= 1 && rel <= 20) return L47GStone;
            return L47GKeep;
        }
        // The roof (one over the walls all round), and the attic's open space under it
        int roof = L47RoofAt(v);
        if (au <= L47HouseU + 1 && av <= L47HouseV + 1 && rel == roof) return L47GSlate;
        if (au == L47HouseU + 1 || av == L47HouseV + 1)
        {
            if (au == L47HouseU + 1 && v is -1 or 0 && rel >= 1 && rel <= 22) return L47GStone;
            return rel == 1 ? L47GFlag : L47GKeep;
        }
        if (rel > roof) return L47GAir;
        bool longWall = av == L47HouseV, gable = au == L47HouseU;
        if (longWall || gable)
        {
            if (rel <= 0) return L47GKeep;
            if (rel == 1) return L47GPlinth;
            // Corners dressed, a timber band between the storeys
            if (longWall && gable) return rel <= L47Eaves ? L47GPlinth : L47GStone;
            if (rel == L47LoftFloor) return L47GTimber;
            if (gable && rel > L47Eaves) return v == 0 && rel == L47Eaves + 3 ? L47GWindow : L47GStone;
            // The front door (three wide, a timber lintel), the hearth's opening in each gable
            if (longWall && v > 0 && au <= 1) return rel <= 4 ? L47GAir : rel == 5 ? L47GTimber : L47GStone;
            if (gable && v is -1 or 0 && rel is 2 or 3) return L47GHearth;
            // Windows: tall pairs along the long walls and in the gables, on both storeys
            bool windowCol = longWall ? au is 2 or 6 or 9 : av == 3;
            if (windowCol && (rel is 3 or 4 || rel is 8 or 9)) return L47GWindow;
            return rel <= L47Eaves ? L47GStone : L47GStone;
        }
        // Inside: the boards of the ground floor and the loft
        if (rel <= 0) return L47GKeep;
        if (rel == L47HouseFloor) return L47GBoards;
        if (rel == L47LoftFloor) return u == -3 && v == -6 ? L47GAir : L47GBoards;
        // The partitions between the hall and the rooms either side (a doorway in each)
        if (au == 4 && rel < L47LoftFloor) return v is 0 or 1 && rel <= 4 ? L47GAir : L47GStone;
        // A ladder up to the loft, against the back wall of the entrance hall
        if (u == -3 && v == -6 && rel >= 2 && rel <= L47LoftFloor + 1) return L47GF(L47GLadder, ArchPier.South);
        if (rel < L47LoftFloor)
        {
            // The great hall (west): a long table down its middle, lanterns on it, the Order's banners on the far wall
            if (u <= -5)
            {
                if (v == 0 && u >= -10 && u <= -6) return rel == 2 ? L47GTable : rel == 3 && u is -10 or -6 ? L47GLantern : rel == 3 && u == -8 ? L47GCandles : L47GAir;
                if (u == -11 && v is -3 or 3 && rel is 3 or 4) return L47GF(rel == 4 ? L47GBannerTop : L47GBannerFoot, ArchPier.East);
                return L47GAir;
            }
            // The east room: shelves along the gable wall, candles, a lantern
            if (u >= 5)
            {
                if (u == 11 && av != 3 && av <= 5 && rel is 2 or 3) return L47GF(L47GShelf, ArchPier.West);
                if (u == 8 && v == 4 && rel == 2) return L47GTable;
                if (u == 8 && v == 4 && rel == 3) return L47GLantern;
                return L47GAir;
            }
            // The entrance hall: candles on the Altar Stone's ends, lanterns either side of the door
            if (au == 2 && v == 0 && rel == 3) return L47GCandles;
            if (au == 3 && v == 6 && rel == 2) return L47GLantern;
            return L47GAir;
        }
        // The loft: a lantern or two, banners on the gables
        if (rel == L47LoftFloor + 1 && (u, v) is (6, -4) or (-7, 3)) return L47GLantern;
        if (au == L47HouseU - 1 && v is -2 or 2 && rel is 8 or 9) return L47GF(rel == 9 ? L47GBannerTop : L47GBannerFoot, u < 0 ? ArchPier.East : ArchPier.West);
        return L47GAir;
    }

    /// <summary>
    /// Where the level's notes lie (WorldLayout.Notes.cs): at the foot of every third of the Order's way-stones along the
    /// trail (someone sat down there to write), and in the manor's great hall.
    /// </summary>
    private void L47NoteSpots(int mx, int mz, Action<int, int, string, int> near)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        int hx = L47MidX - 7, hz = L47MidZ + 2;
        if (MacroOf(hx) == mx && MacroOf(hz) == mz) near(hx - x0, hz - z0, "cache", 2);
        // (The way-stones whose arc along the trail falls in this cell: worked out from the cell's middle)
        double phi0;
        if (L47TrailDistance(x0 + MacroSize / 2, z0 + MacroSize / 2, out phi0) > 40 || phi0 < 0) return;
        int k0 = (int)Math.Round((L47TrailArc(phi0) - 60) / 120.0);
        for (int k = Math.Max(0, k0 - 1); k <= k0 + 1; k++)
        {
            if (k % 3 != 1) continue;
            var (wx, wz) = L47MarkerAt(k);
            if (MacroOf(wx) == mx && MacroOf(wz) == mz) near(wx - x0, wz - z0, "way", 3);
        }
    }

    /// <summary>The Order's stores in the manor (supply boxes), manor-local.</summary>
    private static readonly (int U, int V)[] L47Stores = { (10, -5), (10, 5), (-10, -5), (-2, 5), (7, 1) };

    /// <summary>Puts the Order's stores down in the manor (where its cell holds them).</summary>
    private void L47PlaceManorThings(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        foreach (var (u, v) in L47Stores)
        {
            int lx = L47MidX + u - x0, lz = L47MidZ + v - z0;
            if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
            ref Tile t = ref b.At(lx, lz);
            if (t.Kind != TileKind.Floor || L47GladeBlock(L47MidX + u, L47MidZ + v, 2) != L47GAir) continue;
            t.SupplyBox = true;
        }
    }
}
