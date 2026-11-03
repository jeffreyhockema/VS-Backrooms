using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 23's skin (round 4, 2026-11-02, the asset-quality pass): which blocks of the trunks, logs, mushroom caps and
/// boulders the generator dresses with model blocks so they stop reading as columns and boxes. None of it changes what
/// is wood and what is air in <see cref="L23Wood"/> (the layout's walls), except the root flares and limbs, which sit in
/// the air at a trunk's foot and side and are a step and nothing, so layouts are unchanged:
/// <list type="bullet">
/// <item>the outermost bark of a trunk near eye height, in relief, facing out (<see cref="L23SkinFace"/>);</item>
/// <item>a root flare in the air at a trunk's foot (<see cref="L23FlareAt"/>);</item>
/// <item>broken limbs out of the trunks' sides under the canopy (<see cref="L23LimbAt"/>);</item>
/// <item>a fallen log's cells as slices of its round section (<see cref="L23LogPiece"/>);</item>
/// <item>a stone mushroom cap's rim and its upper layer's edge (<see cref="L23CapPiece"/>), a boulder's rounded top (<see cref="L23BoulderPiece"/>).</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>How high over the ground the trunks' bark is in relief (the rest is far enough up to read from its texture).</summary>
    public const int L23SkinHeight = 9;

    /// <summary>Whether the wood at a height of a column is the outermost bark of a trunk (a Green Giant's too), and the way it faces out.</summary>
    public bool L23SkinFace(int gx, int gz, int rel, out ArchPier facing)
    {
        facing = ArchPier.North;
        double px = gx + 0.5, pz = gz + 0.5;
        L23Trunk[] around = L23TrunksAround(Hashing.FloorDiv(gx, L23Pitch), Hashing.FloorDiv(gz, L23Pitch));
        for (int k = 0; k < 9; k++)
        {
            L23Trunk t = around[(k / 3 + 1) * 6 + k % 3 + 1];
            if (t.Exists && L23Faces(t, px, pz, rel, out facing)) return true;
        }
        if (Math.Abs(L23FromMid(gx, gz) - L23GiantRing) < 24)
            for (int k = 0; k < 7; k++)
                if (L23Faces(L23GiantAt(k), px, pz, rel, out facing)) return true;
        return false;
    }

    private static bool L23Faces(in L23Trunk t, double px, double pz, int rel, out ArchPier facing)
    {
        facing = ArchPier.North;
        if (!L23InTrunk(t, px, pz, rel, out _)) return false;
        var (lx, lz) = L23Lean(t, rel);
        facing = L23Cardinal(px - (t.X + lx), pz - (t.Z + lz));
        var (fx, fz) = L23Step(facing);
        return !L23InTrunk(t, px + fx, pz + fz, rel, out _);
    }

    /// <summary>
    /// A root flare in the air of a column at a height (its ground + 1): the bark of a trunk (not a hollow one: its mouth
    /// stays open) right behind it toward the trunk's middle. The way it faces (away from the trunk), whether it is a Green
    /// Giant's, and its form (0 a full slope, 1 a lower slope with a root running out).
    /// </summary>
    public bool L23FlareAt(int gx, int gz, int rel, out ArchPier facing, out bool giant, out int form)
    {
        facing = ArchPier.North;
        giant = false;
        form = 0;
        double px = gx + 0.5, pz = gz + 0.5;
        L23Trunk[] around = L23TrunksAround(Hashing.FloorDiv(gx, L23Pitch), Hashing.FloorDiv(gz, L23Pitch));
        for (int k = 0; k < 9; k++)
        {
            L23Trunk t = around[(k / 3 + 1) * 6 + k % 3 + 1];
            if (!t.Exists || t.Hollow || !L23Behind(t, px, pz, rel, out facing)) continue;
            form = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL23Trunk + 41)) < 0.3 ? 1 : 0;
            return true;
        }
        if (Math.Abs(L23FromMid(gx, gz) - L23GiantRing) < 24)
            for (int k = 0; k < 7; k++)
                if (L23Behind(L23GiantAt(k), px, pz, rel, out facing))
                {
                    giant = true;
                    form = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL23Trunk + 41)) < 0.45 ? 1 : 0;
                    return true;
                }
        return false;
    }

    /// <summary>A stone mushroom's stem flaring at its foot: the air of a column at a height (its ground + 1) with a stem right behind it, and the way it faces (out).</summary>
    public bool L23StemFootAt(int gx, int gz, int rel, out ArchPier facing)
    {
        facing = ArchPier.North;
        double px = gx + 0.5, pz = gz + 0.5;
        foreach (L23Feature f in L23FeaturesAround(gx, gz))
        {
            if (f.Kind != L23FeatureKind.Mushroom) continue;
            for (int k = 0; k < f.Count; k++)
            {
                L23Mushroom(f, k, out double mx, out double mz, out double stem, out _, out _);
                double dx = px - mx, dz = pz - mz;
                if (dx * dx + dz * dz < stem * stem || dx * dx + dz * dz > (stem + 1.6) * (stem + 1.6)) continue;
                ArchPier out1 = L23Cardinal(dx, dz);
                var (fx, fz) = L23Step(out1);
                double ix = dx - fx, iz = dz - fz;
                if (ix * ix + iz * iz >= stem * stem) continue;
                facing = out1;
                return true;
            }
        }
        return false;
    }

    private static bool L23Behind(in L23Trunk t, double px, double pz, int rel, out ArchPier facing)
    {
        facing = ArchPier.North;
        var (lx, lz) = L23Lean(t, rel);
        double dx = px - (t.X + lx), dz = pz - (t.Z + lz);
        double far = t.R * (1 + t.Ecc + t.Swell) + (t.Giant ? 6.5 : 4.5);
        if (dx * dx + dz * dz > far * far) return false;
        if (L23InTrunk(t, px, pz, rel, out _)) return false;
        facing = L23Cardinal(dx, dz);
        var (fx, fz) = L23Step(facing);
        return L23InTrunk(t, px - fx, pz - fz, rel, out _);
    }

    /// <summary>
    /// A broken limb out of a trunk's side at a column, if one grows there: on most trees (not the Green Giants nor the
    /// hollow ones), two to five, four to fifteen over the foot, at the first column outside the bark along
    /// their bearing. Returns the height, the way it points (away from the trunk), the bark, and whether it is a long limb
    /// (else a short stub).
    /// </summary>
    public bool L23LimbAt(int gx, int gz, out int rel, out ArchPier facing, out byte bark, out bool longLimb)
    {
        rel = 0;
        facing = ArchPier.North;
        bark = 0;
        longLimb = false;
        L23Trunk[] around = L23TrunksAround(Hashing.FloorDiv(gx, L23Pitch), Hashing.FloorDiv(gz, L23Pitch));
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L23Trunk t = around[(dj + 2) * 6 + di + 2];
                if (!t.Exists || t.R < 1.8 || t.Hollow) continue;
                ulong h = Hashing.Mix(t.H + 727);
                if (Hashing.Unit(h) > 0.85) continue;
                double dx0 = gx + 0.5 - t.X, dz0 = gz + 0.5 - t.Z, far = t.R * (1 + t.Ecc + t.Swell) + 4;
                if (dx0 * dx0 + dz0 * dz0 > far * far) continue;
                int n = 2 + (int)(h % 3) + (t.R >= 3.5 ? 1 : 0);
                for (int k = 0; k < n; k++)
                {
                    ulong hk = Hashing.Mix(h + (ulong)k * 29);
                    int r = t.Base + 4 + (int)(hk % 12);
                    if (t.Snag && r > t.Top - 2) continue;
                    var (lx, lz) = L23Lean(t, r);
                    double a = Hashing.Unit(hk << 10) * Math.PI * 2, ca = Math.Cos(a), sa = Math.Sin(a);
                    bool inside = false;
                    for (double d = 0; d < t.R * 1.6 + 4; d += 0.5)
                    {
                        int x = (int)Math.Floor(t.X + lx + ca * d), z = (int)Math.Floor(t.Z + lz + sa * d);
                        if (L23InTrunk(t, x + 0.5, z + 0.5, r, out _)) { inside = true; continue; }
                        if (!inside || x != gx || z != gz) break;
                        ArchPier f = L23Cardinal(ca, sa);
                        var (fx, fz) = L23Step(f);
                        if (!L23InTrunk(t, x - fx + 0.5, z - fz + 0.5, r, out _)) break;
                        rel = r;
                        facing = f;
                        bark = t.Kind;
                        longLimb = Hashing.Unit(hk << 30) < 0.55;
                        return true;
                    }
                }
            }
        return false;
    }

    /// <summary>The pieces of a fallen log's round section, in <c>l23-logpart</c>'s order (tools/gen_23_r4.py's LOG_PARTS).</summary>
    private static readonly (int Size, int Off, int Level)[] L23LogParts =
    {
        (1, 0, 1), (2, 0, 1), (2, 1, 1), (2, 0, 2), (2, 1, 2), (3, -1, 1), (3, 1, 1), (3, -1, 2), (3, 1, 2), (3, 0, 3), (3, 0, 1),
    };

    /// <summary>Which slice of its log's round section a fallen log's cell at a height is (an index of <c>l23-logpart</c>'s parts), or -1 for a whole block (inside it, or under its line's ground).</summary>
    public int L23LogPiece(int gx, int gz, int rel)
    {
        foreach (L23Feature f in L23FeaturesAround(gx, gz))
        {
            if (f.Kind != L23FeatureKind.Log) continue;
            int along = f.AlongZ ? gz : gx, across = f.AlongZ ? gx : gz;
            if (along < f.A || along > f.B || f.Gap != int.MinValue && (along == f.Gap || along == f.Gap + 1)) continue;
            int off = across - f.Line;
            int lo = f.Size == 2 ? 0 : -(f.Size / 2), hi = f.Size == 2 ? 1 : f.Size / 2;
            if (off < lo || off > hi) continue;
            int baseLine = L23Ground(f.AlongZ ? f.Line : gx, f.AlongZ ? gz : f.Line);
            int level = rel - baseLine;
            for (int p = 0; p < L23LogParts.Length; p++)
                if (L23LogParts[p] == (f.Size, off, level)) return p;
            return -1;
        }
        return -1;
    }

    /// <summary>
    /// A stone mushroom cap's edge at a height of a column: part 0 the rim's side, 1 its corner, 2 the upper layer's side,
    /// 3 its corner; the way it faces (out; a corner by the quadrant: north is the north-east corner, east the south-east...).
    /// </summary>
    public bool L23CapPiece(int gx, int gz, int rel, out int part, out ArchPier facing)
    {
        part = 0;
        facing = ArchPier.North;
        double px = gx + 0.5, pz = gz + 0.5;
        foreach (L23Feature f in L23FeaturesAround(gx, gz))
        {
            if (f.Kind != L23FeatureKind.Mushroom) continue;
            for (int k = 0; k < f.Count; k++)
            {
                L23Mushroom(f, k, out double mx, out double mz, out _, out int height, out double cap);
                double dx = px - mx, dz = pz - mz, d = Math.Sqrt(dx * dx + dz * dz);
                if (d >= cap + 0.5) continue;
                int capAt = L23Ground((int)Math.Floor(mx), (int)Math.Floor(mz)) + height + 1;
                if (rel == capAt && d < cap && d > cap - 1.1) part = 0;
                else if (rel == capAt + 1 && cap >= 2.4 && d < cap - 1.3 && d > cap - 2.4) part = 2;
                else continue;
                L23Outward(dx, dz, d, ref part, out facing);
                return true;
            }
        }
        return false;
    }

    /// <summary>A boulder's top at a height of a column: part 0 its cap (the middle), 1 an edge, 2 a corner; the way it faces as <see cref="L23CapPiece"/>.</summary>
    public bool L23BoulderPiece(int gx, int gz, int rel, out int part, out ArchPier facing)
    {
        part = 0;
        facing = ArchPier.North;
        double px = gx + 0.5, pz = gz + 0.5;
        foreach (L23Feature f in L23FeaturesAround(gx, gz))
        {
            if (f.Kind != L23FeatureKind.Boulder) continue;
            ulong h = Hashing.Mix(f.H + 77);
            double r = 1.2 + 1.1 * Hashing.Unit(h);
            double dx = px - f.X, dz = pz - f.Z;
            double rr = r * (1 + 0.22 * Noise(gx / 2.5, gz / 2.5, SaltL23Feature + 1));
            double q2 = (dx * dx + dz * dz) / (rr * rr);
            if (q2 >= 1) continue;
            int baseAt = L23Ground((int)Math.Floor(f.X), (int)Math.Floor(f.Z));
            int to = baseAt + (int)Math.Round(r * 0.9 * Math.Sqrt(1 - q2));
            if (rel != to) return false;
            if (q2 < 0.3) return true;
            part = 1;
            L23Outward(dx, dz, Math.Sqrt(dx * dx + dz * dz), ref part, out facing);
            return true;
        }
        return false;
    }

    /// <summary>The way an edge faces out from a middle, a corner (part + 1) where it is near a diagonal.</summary>
    private static void L23Outward(double dx, double dz, double d, ref int part, out ArchPier facing)
    {
        if (d > 0.01 && Math.Abs(dx) > 0.42 * d && Math.Abs(dz) > 0.42 * d)
        {
            part++;
            facing = dx > 0 ? (dz < 0 ? ArchPier.North : ArchPier.East) : (dz > 0 ? ArchPier.South : ArchPier.West);
            return;
        }
        facing = L23Cardinal(dx, dz);
    }
}
