using System;
using System.Collections.Generic;
using System.Threading;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 23's forest floor between the trees (round 3, 2026-11-01): fallen petrified logs (some broken in two, some with
/// the plate of roots they tore out of the ground still standing at one end), giant stone mushrooms alone or in a little
/// cluster, and mossy boulders half sunk in the humus. Each stands on a lattice of its own (<see cref="L23FeaturePitch"/>),
/// clear of the trunks, the hollow trunks' ways, the tunnels' mouths, the Heart of Water and the tangle, and is drawn into
/// a column's wood (<see cref="L23Wood"/>) like the trees, so the layout's walls and the generator's blocks agree.
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The lattice the forest floor's things lie on (blocks).</summary>
    private const int L23FeaturePitch = 13;

    /// <summary>What lies at a point of the lattice.</summary>
    public enum L23FeatureKind : byte { None, Log, Mushroom, Boulder }

    /// <summary>
    /// One thing on the forest floor. A log lies along x (or z when <see cref="AlongZ"/>) from <see cref="A"/> to
    /// <see cref="B"/> on the line <see cref="Line"/>, <see cref="Size"/> blocks thick (1 to 3), maybe broken at
    /// <see cref="Gap"/> (two blocks), maybe with its root plate standing at A. A mushroom (and up to two more beside it)
    /// or a boulder stands at X, Z.
    /// </summary>
    public struct L23Feature
    {
        public L23FeatureKind Kind;
        public double X, Z;
        public bool AlongZ, RootPlate;
        public int A, B, Line, Size, Gap;
        public byte Bark;
        public int Count;
        public ulong H;
    }

    /// <summary>The thing at a point of the floor's lattice (Kind None where there is none).</summary>
    public L23Feature L23FeatureAt(int i, int j)
    {
        var f = new L23Feature();
        ulong h = Hashing.Hash(seed, i, j, SaltL23Feature);
        f.H = h;
        double u = Hashing.Unit(h);
        L23FeatureKind kind = u < 0.24 ? L23FeatureKind.Log : u < 0.37 ? L23FeatureKind.Mushroom : u < 0.52 ? L23FeatureKind.Boulder : L23FeatureKind.None;
        if (kind == L23FeatureKind.None) return f;
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3), h5 = Hashing.Mix(h4);
        f.X = (i + 0.25 + 0.5 * Hashing.Unit(h2)) * L23FeaturePitch;
        f.Z = (j + 0.25 + 0.5 * Hashing.Unit(h3)) * L23FeaturePitch;
        int cx = (int)Math.Floor(f.X), cz = (int)Math.Floor(f.Z);
        double dc = L23FromMid(cx, cz);
        if (dc < L23CoreRadius + 8 || dc > L23Reach - 14) return f;
        if (kind == L23FeatureKind.Log)
        {
            f.AlongZ = (h4 & 1) == 1;
            int len = 7 + (int)(12 * Hashing.Unit(h4 << 8));
            double s = Hashing.Unit(h5);
            f.Size = s < 0.35 ? 1 : s < 0.75 ? 2 : 3;
            int c = f.AlongZ ? cz : cx;
            f.A = c - len / 2;
            f.B = f.A + len - 1;
            f.Line = f.AlongZ ? cx : cz;
            f.Gap = len >= 11 && Hashing.Unit(h5 << 16) < 0.35 ? f.A + len / 3 + (int)(h5 % (ulong)Math.Max(1, len / 3)) : int.MinValue;
            f.RootPlate = f.Size >= 2 && Hashing.Unit(h5 << 32) < 0.5;
            double k = Hashing.Unit(Hashing.Mix(h5));
            f.Bark = k < 0.4 ? L23BarkGrey : k < 0.6 ? L23BarkRed : k < 0.78 ? L23BarkPale : k < 0.9 ? L23BarkDark : L23BarkAspen;
            // (Its ends and middle on open ground, and clear of the ways in and out)
            for (int n = 0; n <= 4; n++)
            {
                int along = f.A + (f.B - f.A) * n / 4;
                int x = f.AlongZ ? f.Line : along, z = f.AlongZ ? along : f.Line;
                if (!L23FloorFree(x + 0.5, z + 0.5, n is 0 or 4 ? 2.5 : 0.5)) return f;
            }
        }
        else
        {
            if (!L23FloorFree(f.X, f.Z, kind == L23FeatureKind.Mushroom ? 1.5 : 1)) return f;
            f.Count = kind == L23FeatureKind.Mushroom ? 1 + (int)(h4 % 3) : 1;
        }
        f.Kind = kind;
        return f;
    }

    /// <summary>
    /// Whether a point of the forest floor is free for a fallen thing: off every trunk (by a margin past its buttressed foot),
    /// well away from a hollow trunk and its mouth, off a tunnel, in the forest (not the Heart of Water nor the tangle).
    /// </summary>
    private bool L23FloorFree(double px, double pz, double margin)
    {
        int gx = (int)Math.Floor(px), gz = (int)Math.Floor(pz);
        if (L23InTangle(gx, gz) || L23FromMid(gx, gz) < L23CoreRadius + 6) return false;
        int i0 = Hashing.FloorDiv(gx, L23Pitch), j0 = Hashing.FloorDiv(gz, L23Pitch);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L23Trunk t = L23TrunkAt(i0 + di, j0 + dj);
                if (!t.Exists) continue;
                double dx = px - t.X, dz = pz - t.Z, r = t.R * (1 + t.Ecc) + 1.6 + margin + (t.Hollow ? 6 : 0);
                if (dx * dx + dz * dz < r * r) return false;
            }
        if (L23Tunnel(gx, gz, out _, out _, out double off) && off < 2.2) return false;
        return true;
    }

    /// <summary>The things of a window of the floor's lattice (a point's neighbours each way), kept for the columns that ask for the same one.</summary>
    private sealed class L23FeatureWindow
    {
        public WorldLayout Owner;
        public int I0, J0;
        public readonly L23Feature[] Features = new L23Feature[9];
        public WorldLayout CacheOwner;
        public Dictionary<(int, int), L23Feature> Cache;
    }

    [ThreadStatic] private static L23FeatureWindow l23FeatureWindow;

    private L23Feature[] L23FeaturesAround(int gx, int gz)
    {
        int i0 = Hashing.FloorDiv(gx, L23FeaturePitch), j0 = Hashing.FloorDiv(gz, L23FeaturePitch);
        var w = l23FeatureWindow ??= new L23FeatureWindow();
        if (w.Owner == this && w.I0 == i0 && w.J0 == j0) return w.Features;
        w.Owner = null;
        // (Each point is worked out once and kept: the columns of a cell come row by row, so the same few windows come
        // round again and again, and working out a point looks at the trees and the tunnels round it)
        if (w.Cache == null || w.CacheOwner != this || w.Cache.Count > 8192)
        {
            w.Cache = new Dictionary<(int, int), L23Feature>();
            w.CacheOwner = this;
        }
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (!w.Cache.TryGetValue((i0 + di, j0 + dj), out L23Feature f)) w.Cache[(i0 + di, j0 + dj)] = f = L23FeatureAt(i0 + di, j0 + dj);
                w.Features[(dj + 1) * 3 + di + 1] = f;
            }
        w.Owner = this;
        w.I0 = i0;
        w.J0 = j0;
        return w.Features;
    }

    /// <summary>One of a mushroom cluster's mushrooms (0 the biggest): its middle, its stem's radius, its height to the cap and the cap's radius.</summary>
    public static void L23Mushroom(in L23Feature f, int k, out double x, out double z, out double stem, out int height, out double cap)
    {
        ulong h = Hashing.Mix(f.H + 41 + (ulong)k * 7);
        double a = Hashing.Unit(h) * Math.PI * 2, d = k == 0 ? 0 : 2.6 + 1.2 * Hashing.Unit(h << 12);
        x = f.X + Math.Cos(a) * d;
        z = f.Z + Math.Sin(a) * d;
        double size = (k == 0 ? 1 : 0.6) * (0.55 + 0.45 * Hashing.Unit(h << 24));
        stem = 0.5 + 0.7 * size;
        height = 2 + (int)Math.Round(4.5 * size);
        cap = 1.5 + 2.3 * size;
    }

    /// <summary>
    /// Draws the forest floor's things that reach a column into its wood (heights from <paramref name="lowest"/>), where the
    /// trees have left room: logs over the column's own ground, mushrooms' stems and caps, boulders.
    /// </summary>
    private void L23FloorThings(L23Feature[] around, int gx, int gz, int lowest, byte[] kinds)
    {
        double px = gx + 0.5, pz = gz + 0.5;
        int top = lowest + kinds.Length - 1;
        int ground = int.MinValue;
        void Put(int rel, byte kind)
        {
            if (rel < lowest || rel > top || kinds[rel - lowest] != 0) return;
            kinds[rel - lowest] = kind;
        }
        foreach (L23Feature f in around)
        {
            switch (f.Kind)
            {
                case L23FeatureKind.Log:
                {
                    int along = f.AlongZ ? gz : gx, across = f.AlongZ ? gx : gz;
                    // The root plate: a disc of roots and earth standing up at its A end, a block thick
                    if (f.RootPlate && along == f.A - 1)
                    {
                        double r = f.Size + 1.6;
                        if (Math.Abs(across - f.Line) > r) break;
                        if (ground == int.MinValue) ground = L23Ground(gx, gz);
                        int baseAt = L23Ground(f.AlongZ ? f.Line : f.A, f.AlongZ ? f.A : f.Line);
                        double cy = baseAt + f.Size * 0.5 + 0.5;
                        for (int rel = ground + 1; rel <= baseAt + f.Size + 2; rel++)
                        {
                            double dy = rel + 0.5 - cy, dx = across - f.Line;
                            if (dx * dx + dy * dy < r * r) Put(rel, L23RootWood);
                        }
                        break;
                    }
                    if (along < f.A || along > f.B || f.Gap != int.MinValue && (along == f.Gap || along == f.Gap + 1)) break;
                    int off = across - f.Line;
                    // Its cross-section: one block; two by two; three across with the corners off
                    int lo = f.Size == 2 ? 0 : -(f.Size / 2), hi = f.Size == 2 ? 1 : f.Size / 2;
                    if (off < lo || off > hi) break;
                    if (ground == int.MinValue) ground = L23Ground(gx, gz);
                    int baseLine = L23Ground(f.AlongZ ? f.Line : gx, f.AlongZ ? gz : f.Line);
                    // (It lies along its line at the line's ground: where the ground rises under it, it is half buried; where it falls, it rests on the ground)
                    int to = baseLine + (f.Size == 3 && off != 0 ? 2 : f.Size);
                    for (int rel = ground + 1; rel <= to; rel++) Put(rel, L23LogKind(f.Bark, f.AlongZ));
                    break;
                }
                case L23FeatureKind.Mushroom:
                {
                    for (int k = 0; k < f.Count; k++)
                    {
                        L23Mushroom(f, k, out double mx, out double mz, out double stem, out int height, out double cap);
                        double dx = px - mx, dz = pz - mz, d2 = dx * dx + dz * dz;
                        if (d2 > (cap + 0.5) * (cap + 0.5)) continue;
                        int baseAt = L23Ground((int)Math.Floor(mx), (int)Math.Floor(mz));
                        int capAt = baseAt + height + 1;
                        if (d2 < cap * cap) Put(capAt, L23MushCap);
                        if (cap >= 2.4 && d2 < (cap - 1.3) * (cap - 1.3)) Put(capAt + 1, L23MushCap);
                        if (d2 < stem * stem)
                        {
                            if (ground == int.MinValue) ground = L23Ground(gx, gz);
                            for (int rel = ground + 1; rel < capAt; rel++) Put(rel, L23MushStem);
                        }
                    }
                    break;
                }
                case L23FeatureKind.Boulder:
                {
                    ulong h = Hashing.Mix(f.H + 77);
                    double r = 1.2 + 1.1 * Hashing.Unit(h);
                    double dx = px - f.X, dz = pz - f.Z;
                    double rr = r * (1 + 0.22 * Noise(gx / 2.5, gz / 2.5, SaltL23Feature + 1));
                    double q2 = (dx * dx + dz * dz) / (rr * rr);
                    if (q2 >= 1) break;
                    if (ground == int.MinValue) ground = L23Ground(gx, gz);
                    int baseAt = L23Ground((int)Math.Floor(f.X), (int)Math.Floor(f.Z));
                    int to = baseAt + (int)Math.Round(r * 0.9 * Math.Sqrt(1 - q2));
                    for (int rel = ground + 1; rel <= to; rel++) Put(rel, L23Boulder);
                    break;
                }
            }
        }
    }

    // ================= Signs and bracket fungi (round 3) =================

    /// <summary>A painted board of the M.E.G.'s on the forest floor: its text (a part of <c>l23-sign</c>'s), the way its front faces, the height of the board (its post under it to the ground).</summary>
    public readonly record struct L23SignPart(string Text, ArchPier Side, int Board);

    private Dictionary<(int, int), L23SignPart> l23Signs;

    /// <summary>The way-signs at the surface mouths of Base Seedling's tunnels, the warning at the Heart of Water, and the planks by a few sentries (all on the forest floor), by column.</summary>
    public IReadOnlyDictionary<(int, int), L23SignPart> L23Signs
    {
        get
        {
            if (l23Signs != null) return l23Signs;
            var all = new Dictionary<(int, int), L23SignPart>();
            // Way-signs: beside each of Base Seedling's tunnels where it comes out, facing out the way people come to it
            L23Cavern s = L23Specials[0];
            for (int m = 0; m < s.Tunnels; m++)
            {
                L23Passage p = s.Tunnel(m);
                double dx = p.Bx - p.Ax, dz = p.Bz - p.Az, len = Math.Sqrt(dx * dx + dz * dz);
                dx /= len;
                dz /= len;
                foreach (int k in new[] { 4, -4, 5, -5, 3, -3, 6, -6 })
                {
                    int x = (int)Math.Floor(p.Bx + dx * 1.5 - dz * k), z = (int)Math.Floor(p.Bz + dz * 1.5 + dx * k);
                    if (!L23ClearSurface(x, z) || L23InGlade(x + 0.5, z + 0.5, 0)) continue;
                    all[(x, z)] = new L23SignPart("trail", L23Cardinal(dx, dz), L23Ground(x, z) + 2);
                    break;
                }
            }
            // The warning at the Heart of Water: between two Green Giants, where people come in from the forest, facing out
            {
                var (x, z, side) = L23WarningAt;
                var (lx, lz) = L23LeftOf(side);
                int x2 = x - lx, z2 = z - lz;
                int board = Math.Max(L23Ground(x, z), L23Ground(x2, z2)) + 2;
                all[(x, z)] = new L23SignPart("giants-a", side, board);
                all[(x2, z2)] = new L23SignPart("giants-b", side, board);
            }
            // A plank by one sentry in three, beside its face, facing the same way
            int reach = L23Reach + 20;
            int i0 = Hashing.FloorDiv(L23MidX - reach, L23Pitch), i1 = Hashing.FloorDiv(L23MidX + reach, L23Pitch);
            int j0 = Hashing.FloorDiv(L23MidZ - reach, L23Pitch), j1 = Hashing.FloorDiv(L23MidZ + reach, L23Pitch);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    L23Trunk t = L23TrunkAt(i, j);
                    if (!t.Exists || !t.Sentry || Hashing.Unit(Hashing.Mix(t.H + 911)) > 0.34) continue;
                    var (fx, fz) = L23Step(t.SentryFacing);
                    var (lx, lz) = L23LeftOf(t.SentryFacing);
                    foreach (int side in new[] { 2, -2, 3, -3 })
                    {
                        int x = t.SentryX + fx * 2 + lx * side, z = t.SentryZ + fz * 2 + lz * side;
                        if (!L23ClearSurface(x, z) || !L23ClearSurface(x + fx, z + fz)) continue;
                        all[(x, z)] = new L23SignPart("dontsay", t.SentryFacing, L23Ground(x, z) + 2);
                        break;
                    }
                }
            Interlocked.CompareExchange(ref l23Signs, all, null);
            return l23Signs;
        }
    }

    /// <summary>How far from the middle the Heart of Water's warning stands (inside the Green Giants' ring, on the way down to the shore).</summary>
    public const int L23WarnRing = 38;

    /// <summary>The Heart of Water's warning: its first half's column (the second is to its reader's right) and the way it faces (out, toward the forest).</summary>
    public (int X, int Z, ArchPier Side) L23WarningAt
    {
        get
        {
            L23Trunk g0 = L23GiantAt(0), g1 = L23GiantAt(1);
            double a0 = Math.Atan2(g0.Z - L23MidZ, g0.X - L23MidX), a1 = Math.Atan2(g1.Z - L23MidZ, g1.X - L23MidX);
            double a = a0 + Math.IEEERemainder(a1 - a0, Math.PI * 2) / 2;
            double ox = Math.Cos(a), oz = Math.Sin(a);
            return ((int)Math.Floor(L23MidX + ox * L23WarnRing), (int)Math.Floor(L23MidZ + oz * L23WarnRing), L23Cardinal(ox, oz));
        }
    }

    private (int X, int Z, ArchPier Side)? l23Warning;

    /// <summary>Whether a column is within ten blocks of the Heart of Water's warning (kept clear of ferns, so it can be seen: round 3's shots had a fern in front of it).</summary>
    public bool L23NearWarning(int gx, int gz)
    {
        var (wx, wz, _) = l23Warning ??= L23WarningAt;
        return (gx - wx) * (gx - wx) + (gz - wz) * (gz - wz) < 100;
    }

    /// <summary>The nearest of the four ways to a direction (x east, z south).</summary>
    public static ArchPier L23Cardinal(double dx, double dz) =>
        Math.Abs(dx) > Math.Abs(dz) ? (dx > 0 ? ArchPier.East : ArchPier.West) : (dz > 0 ? ArchPier.South : ArchPier.North);

    /// <summary>One step a way.</summary>
    public static (int Dx, int Dz) L23Step(ArchPier side) => side switch
    {
        ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0),
    };

    /// <summary>The step to the left of someone reading a board that faces a way (they look the other way: a board facing north is read looking south, with east on the left).</summary>
    public static (int Dx, int Dz) L23LeftOf(ArchPier side)
    {
        var (fx, fz) = L23Step(side);
        return (-fz, fx);
    }

    /// <summary>
    /// A bracket fungus at a column, if one grows there: on about one tree in three (not the Green Giants), one to three
    /// shelves of stone fungus up the side of the trunk, three to seven over its foot, at the first column outside the bark
    /// along their bearing. Returns the height and the way the shelves face (away from the trunk).
    /// </summary>
    public bool L23BracketAt(int gx, int gz, out int rel, out ArchPier facing)
    {
        rel = 0;
        facing = ArchPier.North;
        double px = gx + 0.5, pz = gz + 0.5;
        L23Trunk[] around = L23TrunksAround(Hashing.FloorDiv(gx, L23Pitch), Hashing.FloorDiv(gz, L23Pitch));
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L23Trunk t = around[(dj + 2) * 6 + di + 2];
                if (!t.Exists || t.R < 1.8 || t.Hollow) continue;
                ulong h = Hashing.Mix(t.H + 515);
                if (Hashing.Unit(h) > 0.35) continue;
                double dx = px - t.X, dz = pz - t.Z, far = t.R * (1 + t.Ecc + t.Swell) + 3.5;
                if (dx * dx + dz * dz > far * far) continue;
                int n = 1 + (int)(h % 3);
                for (int k = 0; k < n; k++)
                {
                    ulong hk = Hashing.Mix(h + (ulong)k * 13);
                    int r = t.Base + 3 + (int)(hk % 4) + k;
                    double a = Hashing.Unit(hk << 10) * Math.PI * 2, ca = Math.Cos(a), sa = Math.Sin(a);
                    // Out from the middle along the bearing to the first column outside the bark at that height
                    bool inside = false;
                    for (double d = 0; d < t.R * 1.6 + 4; d += 0.5)
                    {
                        int x = (int)Math.Floor(t.X + ca * d), z = (int)Math.Floor(t.Z + sa * d);
                        if (L23InTrunk(t, x + 0.5, z + 0.5, r, out _)) { inside = true; continue; }
                        if (!inside || x != gx || z != gz) break;
                        ArchPier f = L23Cardinal(ca, sa);
                        var (fx, fz) = L23Step(f);
                        // (The bark must be right behind it)
                        if (!L23InTrunk(t, x - fx + 0.5, z - fz + 0.5, r, out _)) break;
                        rel = r;
                        facing = f;
                        return true;
                    }
                }
            }
        return false;
    }

    /// <summary>
    /// Whether a column of the forest floor is on one of the trails the M.E.G. have worn out from Base Seedling's tunnels
    /// (round 3, my invention): from each tunnel's mouth straight on out for forty blocks, a block or two wide, wandering a
    /// little; the generator lays trodden earth there where the ground is open.
    /// </summary>
    public bool L23OnTrail(int gx, int gz)
    {
        L23Cavern s = L23Specials[0];
        double px = gx + 0.5, pz = gz + 0.5;
        double sx = px - s.X, sz = pz - s.Z;
        if (sx * sx + sz * sz > (s.R + 80.0) * (s.R + 80.0)) return false;
        for (int m = 0; m < s.Tunnels; m++)
        {
            L23Passage p = s.Tunnel(m);
            double dx = p.Bx - p.Ax, dz = p.Bz - p.Az, len = Math.Sqrt(dx * dx + dz * dz);
            dx /= len;
            dz /= len;
            double along = (px - p.Bx) * dx + (pz - p.Bz) * dz;
            if (along < 0 || along > 40) continue;
            double across = -(px - p.Bx) * dz + (pz - p.Bz) * dx - 2.5 * Noise(along / 9.0, m, SaltL23Feature + 2);
            if (Math.Abs(across) < 0.9 + 0.4 * Noise(gx / 3.0, gz / 3.0, SaltL23Feature + 3)) return true;
        }
        return false;
    }

    [ThreadStatic] private static Dictionary<(int, int), (int X, int Z, ArchPier Side)?> l23LostCamps;
    [ThreadStatic] private static WorldLayout l23LostCampsOwner;

    /// <summary>
    /// A lost M.E.G. explorer's last camp in a cell of the forest, if there is one (one cell in twenty; my invention): a
    /// bedroll on open ground, a crate at its foot, and a pile of bones beside it. Its bedroll's column and the way its
    /// head lies.
    /// </summary>
    public (int X, int Z, ArchPier Side)? L23LostCampIn(int mx, int mz)
    {
        if (l23LostCampsOwner != this || l23LostCamps == null || l23LostCamps.Count > 4096)
        {
            l23LostCamps = new Dictionary<(int, int), (int, int, ArchPier)?>();
            l23LostCampsOwner = this;
        }
        if (l23LostCamps.TryGetValue((mx, mz), out var known)) return known;
        (int, int, ArchPier)? found = null;
        ulong h = Hashing.Hash(seed, mx, mz, SaltL23Feature + 5);
        if (Hashing.Unit(h) < 0.05)
        {
            var rng = new Rng(Hashing.Mix(h));
            for (int attempt = 0; attempt < 16 && found == null; attempt++)
            {
                int x = mx * MacroSize + rng.Range(3, MacroSize - 4), z = mz * MacroSize + rng.Range(3, MacroSize - 4);
                if (L23FromMid(x, z) < L23CoreRadius + 12 || L23FromMid(x, z) > L23Reach - 20 || L23OnTrail(x, z)) continue;
                bool clear = true;
                for (int dz = -1; dz <= 1 && clear; dz++)
                    for (int dx = -1; dx <= 1 && clear; dx++)
                        clear = L23ClearSurface(x + dx, z + dz) && L23Ground(x + dx, z + dz) == L23Ground(x, z);
                if (!clear) continue;
                found = (x, z, (ArchPier)(Hashing.Mix(h + 9) % 4));
            }
        }
        l23LostCamps[(mx, mz)] = found;
        return found;
    }
}
