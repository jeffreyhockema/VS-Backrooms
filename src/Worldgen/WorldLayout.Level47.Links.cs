using System;
using System.Collections.Concurrent;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 47's ways in and out, as laid out (docs/design/experimental-levels/LINKS.md, 47-plan.md "Links"); the thresholds
/// themselves are in ThresholdNetwork.L47.cs. This file is the level's own.
/// <list type="bullet">
/// <item><b>In, from Level 10</b> (Wikidot: "no-clipping to or from Level 47 is easier and more frequent than average ... The
/// hollows of dead trees appear to be especially prone"; the host is ours): very rarely an ancient dead tree stands in Level
/// 10's fields, on a field's edge where it can, grey, hollow, far older than anything round it, its bare limbs over the
/// hedges; at most one to a square of 1408 blocks, in three of five. Step into its hollow and you noclip out of a dead
/// tree's hollow in the Adderwood: one-way.</item>
/// <item><b>Out, to Level 10</b>: about half the Adderwood's dead trees are hollow, and four hollows in ten of them lead
/// out: step in and you come out in Level 10 beside its own ancient dead tree. One-way.</item>
/// <item><b>Out, to Level 23</b> (Wikidot 23: "huge hollow green-barked trees in Levels 37 and 47"): the green giants, one at
/// most to a square of 300 blocks, in half of them, each hollow with a mouth between its buttresses: climb in and you come
/// out of a hollow trunk in the Petrified Garden (Level 23's own finder). One-way.</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The links' layout salts (0x3060-0x306F, of the level's 0x3000-0x30BF).</summary>
    private const ulong SaltL47Hollow = 0x3060, SaltL47Leads = 0x3061, SaltL47Tree10 = 0x3062, SaltL47Tree10Pick = 0x3063;

    // ================= Hollow trees in the Adderwood =================

    /// <summary>Of the dead trees thick enough (radius 1.6 or more), how many are hollow; of those, how many lead out.</summary>
    private const double L47HollowChance = 0.55, L47LeadsChance = 0.4;

    /// <summary>A dead tree's bark round its hollow is this thick (a green giant's thicker); the hollow goes up this far; its mouth is this high and twice this wide.</summary>
    private const double L47DeadWall = 0.75, L47GiantWall = 1.4, L47DeadMouth = 0.9, L47GiantMouth = 1.3;
    private const int L47DeadHollowHigh = 7, L47GiantHollowHigh = 11, L47MouthHigh = 3;

    /// <summary>Whether a dead tree is hollow (and which way its mouth faces).</summary>
    private void L47MaybeHollow(ref L47Tree t)
    {
        if (!t.Exists || !t.Dead || t.R < 1.6) return;
        ulong h = Hashing.Hash(seed, (int)Math.Floor(t.X), (int)Math.Floor(t.Z), SaltL47Hollow);
        if (Hashing.Unit(h) >= L47HollowChance) return;
        t.Hollow = true;
        t.MouthA = Hashing.Unit(Hashing.Mix(h)) * Math.PI * 2;
    }

    /// <summary>Whether a hollow dead tree's hollow leads out (to Level 10), by the tree.</summary>
    public bool L47HollowLeads(double x, double z) => Hashing.Unit(Hashing.Hash(seed, (int)Math.Floor(x), (int)Math.Floor(z), SaltL47Leads)) < L47LeadsChance;

    /// <summary>
    /// Whether a point inside a hollow tree's bark (<paramref name="depth"/> in from it) at a height is hollowed out: deeper
    /// than the bark's thickness, over this column's ground and up the hollow; or in the mouth, a slot out from the middle,
    /// <see cref="L47MouthHigh"/> high over the ground.
    /// </summary>
    private static bool L47Hollowed(in L47Tree t, double px, double pz, int rel, int floor, double depth)
    {
        if (rel <= floor || rel > t.Base + (t.Giant ? L47GiantHollowHigh : L47DeadHollowHigh)) return false;
        if (depth > (t.Giant ? L47GiantWall : L47DeadWall)) return true;
        if (rel > floor + L47MouthHigh) return false;
        var (lx, lz) = L47Lean(t, rel);
        double dx = px - (t.X + lx), dz = pz - (t.Z + lz), ca = Math.Cos(t.MouthA), sa = Math.Sin(t.MouthA);
        return dx * ca + dz * sa > 0 && Math.Abs(dz * ca - dx * sa) < (t.Giant ? L47GiantMouth : L47DeadMouth);
    }

    /// <summary>Whether a point is in a hollow tree's hollow, its mouth, or the few blocks in front of its mouth (where its roots do not go).</summary>
    private static bool L47InHollowsWay(in L47Tree t, double px, double pz)
    {
        var (lx, lz) = L47Lean(t, t.Base + 1);
        double dx = px - (t.X + lx), dz = pz - (t.Z + lz), ca = Math.Cos(t.MouthA), sa = Math.Sin(t.MouthA);
        if (dx * dx + dz * dz < t.R * t.R) return true;
        double along = dx * ca + dz * sa;
        return along > 0 && along < t.R + 5 && Math.Abs(dz * ca - dx * sa) < (t.Giant ? L47GiantMouth : L47DeadMouth) + 1.2;
    }

    /// <summary>Whether a column is in a hollow tree's hollow or mouth (at the height over its ground where one walks), and whether the tree is a green giant; a dead tree's that leads nowhere is <paramref name="still"/>.</summary>
    private bool L47InHollow(int gx, int gz, int ground, out bool green, out bool still)
    {
        green = still = false;
        double px = gx + 0.5, pz = gz + 0.5;
        int rel = ground + 1;
        L47Tree[] around = L47TreesAround(Hashing.FloorDiv(gx, L47Pitch), Hashing.FloorDiv(gz, L47Pitch));
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L47Tree t = around[(dj + 3) * 7 + di + 3];
                if (!t.Exists || !t.Hollow) continue;
                if (!L47InTrunk(t, px, pz, rel, out double depth) || !L47Hollowed(t, px, pz, rel, ground, depth)) continue;
                still = !L47HollowLeads(t.X, t.Z);
                return true;
            }
        foreach (L47Tree g in L47GiantsNear(gx, gz))
        {
            if (!L47InTrunk(g, px, pz, rel, out double depth) || !L47Hollowed(g, px, pz, rel, ground, depth)) continue;
            green = true;
            return true;
        }
        return false;
    }

    private List<(int X, int Z, bool Leads)> l47Hollows;
    private List<(int X, int Z)> l47GreenGiants;
    private readonly object l47Lock = new();

    /// <summary>The hollow dead trees within 520 blocks of the glade (worked out once): their middles, and whether they lead out.</summary>
    public List<(int X, int Z, bool Leads)> L47HollowTrees()
    {
        lock (l47Lock)
        {
            if (l47Hollows != null) return l47Hollows;
            var list = new List<(int, int, bool)>();
            int i0 = Hashing.FloorDiv(L47MidX - 520, L47Pitch), i1 = Hashing.FloorDiv(L47MidX + 520, L47Pitch);
            int j0 = Hashing.FloorDiv(L47MidZ - 520, L47Pitch), j1 = Hashing.FloorDiv(L47MidZ + 520, L47Pitch);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    L47Tree t = L47TreeAt(i, j);
                    if (!t.Exists || !t.Hollow || L47FromMid(t.X, t.Z) > 520) continue;
                    if (LevelAt(MacroOf((int)Math.Floor(t.X)), MacroOf((int)Math.Floor(t.Z))) != Level47) continue;
                    list.Add(((int)Math.Floor(t.X), (int)Math.Floor(t.Z), L47HollowLeads(t.X, t.Z)));
                }
            return l47Hollows = list;
        }
    }

    /// <summary>The green giants within 1500 blocks of the glade (worked out once), nearest first.</summary>
    public List<(int X, int Z)> L47GreenGiants()
    {
        lock (l47Lock)
        {
            if (l47GreenGiants != null) return l47GreenGiants;
            var list = new List<(int X, int Z)>();
            int i0 = Hashing.FloorDiv(L47MidX - 1500, L47GiantPitch), i1 = Hashing.FloorDiv(L47MidX + 1500, L47GiantPitch);
            int j0 = Hashing.FloorDiv(L47MidZ - 1500, L47GiantPitch), j1 = Hashing.FloorDiv(L47MidZ + 1500, L47GiantPitch);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    L47Tree g = L47GiantAt(i, j);
                    if (g.Exists) list.Add(((int)Math.Floor(g.X), (int)Math.Floor(g.Z)));
                }
            list.Sort((a, b) => L47FromMid(a.X, a.Z).CompareTo(L47FromMid(b.X, b.Z)));
            return l47GreenGiants = list;
        }
    }

    /// <summary>Whether a tile is one of the Adderwood's tree hollows (any of them).</summary>
    public static bool IsL47Hollow(in Tile t) => t.Level == Level47 && t.Under is Unders.L47DeadHollow or Unders.L47StillHollow or Unders.L47GreenHollow;

    /// <summary>A place to come out of a dead tree's hollow in the Adderwood (one of those near the glade, by key): on the forest floor in front of its mouth.</summary>
    public (int X, int Z)? L47HollowArrival(ulong key)
    {
        var hollows = L47HollowTrees();
        if (hollows.Count == 0) return null;
        var h = hollows[(int)(Hashing.Mix(key) % (ulong)hollows.Count)];
        return FindArrival(Level47, key, t => t.Level == Level47 && t.Under is Unders.L47DeadHollow or Unders.L47StillHollow,
            spot: t => IsArrivalSpot(t) && t.Zone is L47Forest or L47TrailZone, near: (MacroOf(h.X), MacroOf(h.Z)));
    }

    // ================= Level 10's ancient dead trees =================

    /// <summary>The side of a square of Level 10 that holds at most one ancient dead tree, how many squares have one, and the tree's size.</summary>
    public const int L47Tree10Square = 1408;
    private const double L47Tree10Chance = 0.6, L47Tree10R = 2.6, L47Tree10Foot = 7.5;

    /// <summary>One of Level 10's ancient dead trees: its middle (block), the way its mouth faces, its top, its hash.</summary>
    public sealed class L47Tree10
    {
        public bool Valid;
        public int X, Z, Top;
        public double MouthA;
        public ulong H;
    }

    private readonly ConcurrentDictionary<(int, int), L47Tree10> l47Trees10 = new();

    /// <summary>The ancient dead tree of a square of Level 10 (Valid false where it has none), worked out from the layout alone.</summary>
    public L47Tree10 L47Tree10In(int si, int sj) => l47Trees10.GetOrAdd((si, sj), k => L47PlanTree10(k.Item1, k.Item2));

    private L47Tree10 L47PlanTree10(int si, int sj)
    {
        var none = new L47Tree10();
        ulong h = Hashing.Hash(seed, si, sj, SaltL47Tree10);
        if (Hashing.Unit(h) >= L47Tree10Chance) return none;
        // (Most squares are no part of Level 10: ask that first)
        int cx0 = si * L47Tree10Square + L47Tree10Square / 2, cz0 = sj * L47Tree10Square + L47Tree10Square / 2;
        bool any = false;
        for (int k = 0; k < 9 && !any; k++)
            any = LevelAt(MacroOf(cx0 + (k % 3 - 1) * 600), MacroOf(cz0 + (k / 3 - 1) * 600)) == 10;
        if (!any) return none;
        var rng = new Rng(Hashing.Mix(h));
        L47Tree10 fallback = null;
        for (int attempt = 0; attempt < 40; attempt++)
        {
            int x = si * L47Tree10Square + rng.Range(250, L47Tree10Square - 251), z = sj * L47Tree10Square + rng.Range(250, L47Tree10Square - 251);
            if (!L47Tree10Fits(x, z)) continue;
            var t = new L47Tree10
            {
                Valid = true, X = x, Z = z, H = Hashing.Mix(h + (ulong)attempt),
                MouthA = Hashing.Unit(Hashing.Mix(h + 99 + (ulong)attempt)) * Math.PI * 2,
            };
            t.Top = 13 + (int)(5 * Hashing.Unit(t.H));
            // On a field's edge (a tree line) where it can; else wherever it fits
            if (FieldAt(x, z).EdgeGap < 4) return t;
            fallback ??= t;
        }
        return fallback ?? none;
    }

    /// <summary>Whether an ancient dead tree fits at a column of Level 10: its cell and the two rings of cells round it in Level 10, off the roads, not in a farmstead, a paddock or a pond, nowhere near the spawn.</summary>
    private bool L47Tree10Fits(int x, int z)
    {
        // (Every cell round its own in Level 10 too: a neighbouring level lines its edge from the cells beside it, and the
        // tree must change nothing outside Level 10)
        int tmx = MacroOf(x), tmz = MacroOf(z);
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
                if (LevelAt(tmx + dx, tmz + dz) != 10 || IsSpawnMacro(tmx + dx, tmz + dz)) return false;
        for (int dz = -6; dz <= 6; dz += 6)
            for (int dx = -6; dx <= 6; dx += 6)
                if (FarmRoadAt(x + dx, z + dz) >= 0) return false;
        var f = FieldAt(x, z);
        return FieldKind(f.I, f.J) is not (FarmField.Farmstead or FarmField.Lake or FarmField.Pasture);
    }

    /// <summary>The ancient dead tree whose footprint may hold a column of Level 10, if any.</summary>
    public L47Tree10 L47Tree10Near(int gx, int gz)
    {
        L47Tree10 t = L47Tree10In(Hashing.FloorDiv(gx, L47Tree10Square), Hashing.FloorDiv(gz, L47Tree10Square));
        if (!t.Valid || Math.Abs(gx - t.X) > 10 || Math.Abs(gz - t.Z) > 10) return null;
        return t;
    }

    /// <summary>Whether a point of the ancient dead tree's trunk is hollow: inside it, or in its mouth (three high).</summary>
    private static bool L47Tree10Hollowed(L47Tree10 t, double dx, double dz, double d, int rel)
    {
        if (rel < 1) return false;
        if (d < L47Tree10R - 1.0 && rel <= t.Top - 3) return true;
        if (rel > 3) return false;
        double ca = Math.Cos(t.MouthA), sa = Math.Sin(t.MouthA);
        return dx * ca + dz * sa > 0 && Math.Abs(dz * ca - dx * sa) < 0.95;
    }

    /// <summary>
    /// What the ancient dead tree has at a column and height of Level 10 (rel from its floor): 0 nothing (the host's own),
    /// 1 bark, 2 mossy bark, 3 leaf litter (the hollow's floor), 4 air (the hollow, its mouth).
    /// </summary>
    public int L47Tree10Block(int gx, int gz, int rel)
    {
        L47Tree10 t = L47Tree10Near(gx, gz);
        if (t == null) return 0;
        double px = gx + 0.5, pz = gz + 0.5, dx = px - t.X - 0.5, dz = pz - t.Z - 0.5, d = Math.Sqrt(dx * dx + dz * dz);
        double up = Math.Max(0, rel - 1);
        // The trunk: wide at the foot (buttressed), narrowing, broken off jagged at the top
        double a = Math.Atan2(dz, dx);
        double r = L47Tree10R * (1 - 0.3 * Math.Min(1, up / t.Top)) + 1.4 * Math.Pow(Math.Max(0, Math.Cos(4 * a + t.H % 7)), 3) * Math.Exp(-up / 1.6) + 0.5 * Math.Exp(-up / 1.2);
        int top = t.Top + (int)(Hashing.Hash((ulong)t.H, gx, gz, SaltL47Tree10Pick) % 4) - 1;
        if (d < r && rel >= 1 && rel <= top)
        {
            if (L47Tree10Hollowed(t, dx, dz, d, rel)) return 4;
            return rel <= 3 + (int)(t.H >> 33 & 1) || Math.Sin(a * 3 + rel * 0.4) > 0.6 ? 2 : 1;
        }
        if (rel == 0 && d < L47Tree10R - 1.0) return 3;
        // Roots over the ground, and bare limbs reaching out over the hedges
        for (int k = 0; k < 4; k++)
        {
            ulong h = Hashing.Mix(t.H + 7 + (ulong)k);
            double ra = Hashing.Unit(h) * Math.PI * 2, len = 5 + 2.5 * Hashing.Unit(Hashing.Mix(h));
            if (rel == 1 && L47InTube(px, pz, rel, t.X + 0.5, t.Z + 0.5, 1.0, t.X + 0.5 + Math.Cos(ra) * len, t.Z + 0.5 + Math.Sin(ra) * len, 0.6, 0, 0.8, 0.5)) return 2;
            double la = ra + 0.8, from = 7 + 5 * Hashing.Unit(h << 9), ll = 4 + 3 * Hashing.Unit(h << 19);
            if (rel > 5 && L47InTube(px, pz, rel, t.X + 0.5, t.Z + 0.5, from, t.X + 0.5 + Math.Cos(la) * ll, t.Z + 0.5 + Math.Sin(la) * ll, from + ll * 0.9, 0, 0.6, 0.4)) return 1;
        }
        return 0;
    }

    /// <summary>Lays Level 10's ancient dead trees over a cell (where one stands in it): its trunk is wall, its hollow and mouth open floor, the ground round it its foot.</summary>
    partial void L47Entrances(Builder b, int mx, int mz)
    {
        if (b.Level != 10) return;
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        L47Tree10 t = L47Tree10In(Hashing.FloorDiv(x0 + MacroSize / 2, L47Tree10Square), Hashing.FloorDiv(z0 + MacroSize / 2, L47Tree10Square));
        if (!t.Valid || t.X < x0 - 10 || t.X > x0 + MacroSize + 9 || t.Z < z0 - 10 || t.Z > z0 + MacroSize + 9) return;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                int gx = x0 + lx, gz = z0 + lz;
                double dx = gx + 0.5 - t.X - 0.5, dz = gz + 0.5 - t.Z - 0.5, d = Math.Sqrt(dx * dx + dz * dz);
                if (d > L47Tree10Foot) continue;
                ref Tile tile = ref b.At(lx, lz);
                if (tile.Under != 0) continue;
                int at = L47Tree10Block(gx, gz, 1);
                if (at == 4 || d < L47Tree10R - 1.0)
                {
                    tile.Kind = TileKind.Floor;
                    tile.Under = Unders.L47Tree10Hollow;
                    tile.Variant = 0;
                    tile.Overhead = 0;
                }
                else if (at is 1 or 2 && L47Tree10Block(gx, gz, 2) is 1 or 2)
                {
                    tile.Kind = TileKind.Wall;
                    tile.Under = Unders.L47Tree10Bark;
                    tile.Variant = 0;
                }
                else tile.Under = Unders.L47Tree10Foot;
            }
    }

    private List<(int X, int Z)> l47Trees10Near;

    /// <summary>The ancient dead trees nearest the spawn (up to twelve, by squares outward), worked out once: where the Adderwood's hollows lead out to.</summary>
    public List<(int X, int Z)> L47NearestTrees10()
    {
        lock (l47Lock)
        {
            if (l47Trees10Near != null) return l47Trees10Near;
            var found = new List<(int X, int Z)>();
            int sx = Hashing.FloorDiv(spawnMacroX * MacroSize, L47Tree10Square), sz = Hashing.FloorDiv(spawnMacroZ * MacroSize, L47Tree10Square);
            for (int ring = 0; ring <= 24 && found.Count < 12; ring++)
                for (int dj = -ring; dj <= ring; dj++)
                    for (int di = -ring; di <= ring; di++)
                    {
                        if (Math.Max(Math.Abs(di), Math.Abs(dj)) != ring) continue;
                        L47Tree10 t = L47Tree10In(sx + di, sz + dj);
                        if (t.Valid) found.Add((t.X, t.Z));
                    }
            return l47Trees10Near = found;
        }
    }

    /// <summary>A place to come out in Level 10 beside one of its ancient dead trees (one of those nearest the spawn, by key).</summary>
    public (int X, int Z)? L47Tree10Arrival(ulong key)
    {
        var trees = L47NearestTrees10();
        if (trees.Count == 0) return null;
        var (x, z) = trees[(int)(Hashing.Mix(key + 3) % (ulong)trees.Count)];
        return FindArrival(10, key, t => t.Level == 10 && t.Under is Unders.L47Tree10Bark or Unders.L47Tree10Foot,
            spot: t => t.Kind == TileKind.Floor && !t.Sealed && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Stair == 0 && t.Under is 0 or Unders.L47Tree10Foot,
            near: (MacroOf(x), MacroOf(z)));
    }
}
