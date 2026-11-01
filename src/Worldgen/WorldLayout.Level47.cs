using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 47, "The Adderwood" (experimental): kept as level 30 (<see cref="Level47"/>) and shown as "47". After the Wikidot
/// page (DrChandra; Fandom's Level 47 is an unrelated place and is not used): "a primeval, old-growth forest", temperate,
/// deciduous and coniferous trees "exceeding a hundred feet in height", "thick green moss and lichens cover most surfaces";
/// streams of safe water, mushrooms; a thick damp fog by day, a full moon by night (AtmosphereSystem.L47.cs). A single
/// serpentine trail runs through it that does not change, and at its end a glade where the Ophion Occult Order's manor house
/// and an ancient megalith stand "simultaneously, in a state of superposition" (WorldLayout.Level47.Glade.cs). See
/// docs/design/experimental-levels/47-plan.md.
///
/// <para><b>Everything is a pure function of the block position</b> (and the seed), shared by the layout, the generator
/// (WorldGenerator.L47.cs) and the client: the ground (<see cref="L47Ground"/>), the streams (<see cref="L47Stream"/>),
/// the trail (<see cref="L47TrailDistance"/>), the trees on a jittered lattice (<see cref="L47TreeAt"/>) with their crowns,
/// roots and limbs, the fallen logs and boulders (<see cref="L47Wood"/>). Heights are relative to the level's floor
/// (<see cref="WorldGeometry.FloorFor"/>, ten below the shared floor): the ground lies at 1 to 4, the streams' water at 0,
/// the tallest crowns reach the top of the world (48).</para>
///
/// <para><b>Tiles</b>: <see cref="Tile.Zone"/> is the zone (<see cref="L47Forest"/> ... <see cref="L47RimZone"/>);
/// <see cref="Tile.Height"/> the ground; <see cref="Tile.Detail"/> bit 1 marks open ground all round (where people are put
/// down).</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x3000-0x30BF are this level's (0x30C0-0x30FF its thresholds').</summary>
    private const ulong SaltL47Shape = 0x3001, SaltL47Mid = 0x3002, SaltL47Ground = 0x3003, SaltL47Stream = 0x3004, SaltL47Tree = 0x3005,
        SaltL47Log = 0x3006, SaltL47Boulder = 0x3007, SaltL47Box = 0x3008, SaltL47Giant = 0x300A, SaltL47Leaf = 0x300B,
        SaltL47Marker = 0x300D;

    /// <summary>The zones (<see cref="Tile.Zone"/>).</summary>
    public const byte L47Forest = 1, L47TrailZone = 2, L47GladeZone = 3, L47StreamZone = 4, L47ManorZone = 5, L47RimZone = 9;

    /// <summary>A tile's <see cref="Tile.Detail"/> bit: open forest floor all round it.</summary>
    public const byte L47OpenGround = 1;

    /// <summary>The top of the world above the level's floor (the floor is <see cref="WorldGeometry.L47Drop"/> below the shared one, which is 39 below the world's top block).</summary>
    public const int L47Top = 38 + WorldGeometry.L47Drop;

    /// <summary>What a block of the forest is (<see cref="L47Wood"/>): nothing, the barks, leaves, stone, fallen logs, the Order's trail stones.</summary>
    public const byte L47Air = 0, L47BarkOak = 1, L47BarkBeech = 2, L47BarkFir = 3, L47BarkSpruce = 4, L47BarkDead = 5, L47BarkGreen = 6,
        L47LeafOak = 8, L47LeafBeech = 9, L47LeafNeedle = 10, L47Stone = 11, L47LogOakX = 12, L47LogOakZ = 13, L47LogDeadX = 14, L47LogDeadZ = 15,
        L47TrailStone = 16, L47KindLimit = 24;

    public static bool L47IsBark(byte k) => k is >= L47BarkOak and <= L47BarkGreen;
    public static bool L47IsLeaf(byte k) => k is >= L47LeafOak and <= L47LeafNeedle;

    /// <summary>Whether a block on the ground is low enough to step up onto (a root, a fallen log, a low stone) when nothing is over it.</summary>
    public static bool L47Steppable(byte k) => k != L47Air && !L47IsLeaf(k);

    /// <summary>The glade's meadow, how far out from its middle no tree stands, and the trail's half-width and the room kept clear beside it.</summary>
    public const int L47GladeRadius = 46, L47GladeClear = 56;
    public const double L47TrailHalf = 1.6, L47TrailClear = 3.2;

    /// <summary>The trail's spiral: how far apart its turns lie, and how far out it goes.</summary>
    public const double L47TrailSpacing = 150, L47TrailOut = 1600;

    /// <summary>The trees' lattice (blocks), and the green giants' (one at most to a square this wide).</summary>
    private const int L47Pitch = 12, L47GiantPitch = 300;

    // ================= Where it is =================

    /// <summary>
    /// How far out the region's centre lies: 1.35 times the city's distance, 33.75 degrees east of south (between Level 52's 22.5 and the Hub's 45,
    /// and beyond both).
    /// </summary>
    private double L47Reach => RegionReach * 1.35;

    /// <summary>The region's centre, in macro cells.</summary>
    public int L47CentreX => spawnMacroX + (int)Math.Round(L47Reach * Math.Sin(3 * Math.PI / 16));
    public int L47CentreZ => spawnMacroZ + (int)Math.Round(L47Reach * Math.Cos(3 * Math.PI / 16));

    /// <summary>The region's radius in macro cells: the forest goes on further than anyone has walked.</summary>
    public int L47Radius => Math.Max(40, spawnMacroX / 50);

    private bool InL47(double mx, double mz) => InRoundRegion(mx, mz, L47CentreX, L47CentreZ, L47Radius, SaltL47Shape);

    private int l47MidX = int.MinValue, l47MidZ;

    /// <summary>The middle of the glade (the end of the trail), in blocks: near the region's centre, moved a little by the seed.</summary>
    public int L47MidX
    {
        get
        {
            if (l47MidX == int.MinValue)
            {
                ulong h = Hashing.Hash(seed, 0, 0, SaltL47Mid);
                l47MidZ = L47CentreZ * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Mix(h)) * 25) - 12;
                l47MidX = L47CentreX * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(h) * 25) - 12;
            }
            return l47MidX;
        }
    }

    public int L47MidZ
    {
        get
        {
            _ = L47MidX;
            return l47MidZ;
        }
    }

    /// <summary>How far a point lies from the glade's middle (the middle of its middle block).</summary>
    public double L47FromMid(double px, double pz)
    {
        double dx = px - L47MidX - 0.5, dz = pz - L47MidZ - 0.5;
        return Math.Sqrt(dx * dx + dz * dz);
    }

    /// <summary>A place to look for somewhere to arrive: out in the forest, 120 to 420 blocks from the glade (the spot test keeps it on open ground).</summary>
    private (int Mx, int Mz) L47ArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = 120 + 300 * Hashing.Unit(Hashing.Mix(h));
        return (MacroOf(L47MidX + (int)Math.Round(Math.Cos(angle) * r)), MacroOf(L47MidZ + (int)Math.Round(Math.Sin(angle) * r)));
    }

    /// <summary>Arriving: on the forest floor (or the trail) with open ground all round.</summary>
    private static bool IsL47ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone is L47Forest or L47TrailZone && (t.Detail & L47OpenGround) != 0;

    /// <summary>How high above the level's floor to put someone down: on the ground.</summary>
    private static double L47ArrivalHeight(in Tile t, double stand) => t.Height + stand;

    // ================= The ground and the streams =================

    private static double L47Smooth(double t) => t * t * (3 - 2 * t);

    /// <summary>How far a column lies from a stream's middle line, as a noise value (0 on it; the water is within <see cref="L47WaterAt"/>).</summary>
    public double L47Stream(int gx, int gz)
    {
        // The zero line of a noise field winds like a brook; warped a little so it meanders
        double wx = gx + 24 * Fbm(gx / 64.0, gz / 64.0, SaltL47Stream + 1), wz = gz + 24 * Fbm(gx / 64.0 + 7.3, gz / 64.0, SaltL47Stream + 2);
        double s = Math.Abs(Noise(wx / 118.0, wz / 118.0, SaltL47Stream));
        // (None in the glade or near it)
        double dm = L47FromMid(gx, gz);
        if (dm < L47GladeClear + 14) s += (L47GladeClear + 14 - dm) * 0.004;
        return s;
    }

    /// <summary>A stream's water: within this much of its middle line; its banks slope down to it over the next.</summary>
    public const double L47WaterAt = 0.020, L47BankAt = 0.058;

    /// <summary>
    /// The forest floor at a column, above the level's floor: humus in long gentle swells (1 to 4), sloping down to the
    /// streams' banks (1) and their beds (-1, -2 in the middle, the water's surface at 0); flat in the glade.
    /// </summary>
    public int L47Ground(int gx, int gz)
    {
        double g = 2.3 + 1.4 * Fbm(gx / 74.0, gz / 74.0, SaltL47Ground) + 0.55 * Noise(gx / 15.0, gz / 15.0, SaltL47Ground + 3);
        double dm = L47FromMid(gx, gz);
        if (dm < L47GladeRadius + 12) g = 1 + (g - 1) * L47Smooth(Math.Clamp((dm - L47GladeRadius) / 12.0, 0, 1));
        double s = L47Stream(gx, gz);
        if (s < L47WaterAt) return s < L47WaterAt * 0.5 ? -2 : -1;
        if (s < L47BankAt) g = 1 + (g - 1) * L47Smooth((s - L47WaterAt) / (L47BankAt - L47WaterAt));
        return Math.Clamp((int)Math.Round(g), 1, 4);
    }

    /// <summary>Whether a column is under a stream's water (its surface at rel 0).</summary>
    public bool L47InWater(int gx, int gz) => L47Stream(gx, gz) < L47WaterAt;

    // ================= The trail =================

    /// <summary>The bearing the trail leaves the glade by (south, toward the manor's door), radians along x then z.</summary>
    private const double L47TrailStartA = Math.PI / 2;

    /// <summary>How far the trail's spiral climbs outward per radian it turns.</summary>
    private const double L47TrailA = L47TrailSpacing / (2 * Math.PI);

    /// <summary>
    /// The trail's distance from the glade's middle after it has turned <paramref name="phi"/> radians, and how fast that
    /// changes per radian: a spiral out from the glade, swinging from side to side as it goes (a serpentine every seventy
    /// blocks or so, and a slower wander).
    /// </summary>
    private static (double R, double dR) L47TrailR(double phi)
    {
        double r0 = L47GladeRadius - 2 + L47TrailA * phi;
        // (Arc length along it, for the swings)
        double s = (L47GladeRadius - 2) * phi + L47TrailA * phi * phi / 2;
        double ease = Math.Min(1, phi / 1.2);
        double w = 7.5 * Math.Sin(s * 2 * Math.PI / 68) + 4 * Math.Sin(s * 2 * Math.PI / 29 + 1.3);
        double dsdphi = (L47GladeRadius - 2) + L47TrailA * phi;
        double dw = (7.5 * 2 * Math.PI / 68 * Math.Cos(s * 2 * Math.PI / 68) + 4 * 2 * Math.PI / 29 * Math.Cos(s * 2 * Math.PI / 29 + 1.3)) * dsdphi;
        return (r0 + ease * w, L47TrailA + ease * dw);
    }

    /// <summary>The longest the trail turns (where it ends far out in the forest).</summary>
    private static double L47TrailPhiMax => (L47TrailOut - L47GladeRadius) / L47TrailA;

    /// <summary>A point on the trail after it has turned <paramref name="phi"/>: its block position.</summary>
    public (double X, double Z) L47TrailPoint(double phi)
    {
        var (r, _) = L47TrailR(phi);
        double a = L47TrailStartA + phi;
        return (L47MidX + 0.5 + Math.Cos(a) * r, L47MidZ + 0.5 + Math.Sin(a) * r);
    }

    /// <summary>
    /// How far a point lies from the trail's middle line (blocks, roughly: across the trail, not along it), and how far
    /// the trail has turned there; far (999) where no turn of it is near.
    /// </summary>
    public double L47TrailDistance(double px, double pz, out double phiAt)
    {
        phiAt = -1;
        double dx = px - L47MidX - 0.5, dz = pz - L47MidZ - 0.5;
        double r = Math.Sqrt(dx * dx + dz * dz);
        if (r < L47GladeRadius - 16 || r > L47TrailOut + 30) return 999;
        double a = Math.Atan2(dz, dx) - L47TrailStartA;
        a -= 2 * Math.PI * Math.Floor(a / (2 * Math.PI));
        int n0 = (int)Math.Floor((r - L47GladeRadius) / L47TrailSpacing);
        double best = 999;
        for (int n = n0 - 1; n <= n0 + 1; n++)
        {
            double phi = a + 2 * Math.PI * n;
            if (phi < 0 || phi > L47TrailPhiMax) continue;
            // (A turn far off by its plain spiral is far off however it swings: the swings are 11.5 at most)
            if (Math.Abs(r - (L47GladeRadius - 2 + L47TrailA * phi)) > 60) continue;
            var (tr, dr) = L47TrailR(phi);
            double d = Math.Abs(r - tr) / Math.Sqrt(1 + dr * dr / (tr * tr));
            if (d < best)
            {
                best = d;
                phiAt = phi;
            }
        }
        return best;
    }

    /// <summary>The trail's distance at a column (its middle).</summary>
    public double L47TrailAt(int gx, int gz) => L47TrailDistance(gx + 0.5, gz + 0.5, out _);

    /// <summary>The arc length along the trail from the glade to a turn of it.</summary>
    private static double L47TrailArc(double phi) => (L47GladeRadius - 2) * phi + L47TrailA * phi * phi / 2;

    /// <summary>
    /// The Order's way-stones along the trail (our invention): one at the trail's side every hundred and twenty blocks or
    /// so, a stone post with a snake cut into it. The column of the <paramref name="k"/>th out from the glade.
    /// </summary>
    public (int X, int Z) L47MarkerAt(int k)
    {
        double s = 60 + 120.0 * k, r0 = L47GladeRadius - 2;
        double phi = (-r0 + Math.Sqrt(r0 * r0 + 2 * L47TrailA * s)) / L47TrailA;
        var (r, _) = L47TrailR(phi);
        double side = (Hashing.Hash(seed, k, 0, SaltL47Marker) & 1) == 0 ? 1 : -1;
        double a = L47TrailStartA + phi;
        double rr = r + side * (L47TrailHalf + 1.4);
        return ((int)Math.Floor(L47MidX + 0.5 + Math.Cos(a) * rr), (int)Math.Floor(L47MidZ + 0.5 + Math.Sin(a) * rr));
    }

    /// <summary>Whether a column holds one of the Order's way-stones.</summary>
    public bool L47MarkerHere(int gx, int gz)
    {
        if (L47TrailDistance(gx + 0.5, gz + 0.5, out double phi) > L47TrailHalf + 3 || phi < 0) return false;
        int k = (int)Math.Round((L47TrailArc(phi) - 60) / 120.0);
        for (int d = -1; d <= 1; d++)
        {
            if (k + d < 0) continue;
            var (mx, mz) = L47MarkerAt(k + d);
            if (mx == gx && mz == gz) return true;
        }
        return false;
    }

    // ================= The trees =================

    /// <summary>One tree: where it stands, how thick and how tall, its bark, its crown, and whether it is hollow.</summary>
    public struct L47Tree
    {
        public bool Exists, Conifer, Dead, Giant, Hollow;
        public double X, Z, R;
        public byte Bark, Leaf;
        public int Base, Top, CrownBase, Lobes;
        public double CrownR, Phase, Lean, LeanPhase, MouthA;
        public ulong H;
        /// <summary>
        /// Its roots and limbs, worked out once (<see cref="L47Shape"/>): per root its end and radius (3 numbers), per limb its
        /// start, its rise from, its end, its rise and radius (7 numbers; NaN for a limb it does not have); how far out the
        /// roots reach, and the lowest height a limb comes down to.
        /// </summary>
        public double[] Roots, Limbs;
        public double RootReach;
        public int LimbLow;
    }

    /// <summary>Works out a tree's roots and limbs once, as <see cref="L47TreeWood"/> draws them.</summary>
    private static void L47Shape(ref L47Tree t)
    {
        int roots = t.R >= 1.2 ? 3 + (int)((t.H >> 60) % 3) : 0;
        t.Roots = new double[roots * 3];
        t.RootReach = 0;
        for (int k = 0; k < roots; k++)
        {
            ulong h = Hashing.Mix(t.H + 17 + (ulong)k);
            double a = t.Phase / t.Lobes + k * Math.PI * 2 / roots + (Hashing.Unit(h) - 0.5) * 0.7;
            double len = t.R + (t.Giant ? 9 : 3) + 4 * Hashing.Unit(Hashing.Mix(h));
            double rr = t.Giant ? 1.4 : 0.75 + 0.2 * Hashing.Unit(h << 7);
            t.Roots[k * 3] = t.X + Math.Cos(a) * len;
            t.Roots[k * 3 + 1] = t.Z + Math.Sin(a) * len;
            t.Roots[k * 3 + 2] = rr;
            t.RootReach = Math.Max(t.RootReach, len + rr + 1);
        }
        t.LimbLow = int.MaxValue;
        if (t.Conifer || t.R < 0.9) { t.Limbs = Array.Empty<double>(); return; }
        int limbs = t.Dead ? 2 + (int)(t.H >> 58 & 1) : 3 + (int)(t.H >> 58 & 1) + (t.R >= 2.4 ? 1 : 0);
        t.Limbs = new double[limbs * 7];
        for (int k = 0; k < limbs; k++)
        {
            ulong h = Hashing.Mix(t.H + 101 + (ulong)k);
            double a = Hashing.Unit(h) * Math.PI * 2;
            double from = t.Dead ? t.Base + 6 + (t.Top - t.Base - 6) * Hashing.Unit(Hashing.Mix(h)) : t.CrownBase - 3 + 6 * Hashing.Unit(Hashing.Mix(h));
            if (from > t.Top - 1) { t.Limbs[k * 7] = double.NaN; continue; }
            double len = t.Dead ? 3 + 3 * Hashing.Unit(h << 9) : t.CrownR * (0.55 + 0.3 * Hashing.Unit(h << 9));
            double rise = t.Dead ? len * 0.8 : len * 0.6;
            double rr = t.Dead ? 0.55 : 0.6 + 0.15 * t.R;
            var (lx, lz) = L47Lean(t, (int)from);
            double ax = t.X + lx, az = t.Z + lz;
            t.Limbs[k * 7] = ax;
            t.Limbs[k * 7 + 1] = az;
            t.Limbs[k * 7 + 2] = from;
            t.Limbs[k * 7 + 3] = ax + Math.Cos(a) * len;
            t.Limbs[k * 7 + 4] = az + Math.Sin(a) * len;
            t.Limbs[k * 7 + 5] = rise;
            t.Limbs[k * 7 + 6] = rr;
            t.LimbLow = Math.Min(t.LimbLow, (int)from - 2);
        }
    }

    /// <summary>The tree at a point of the lattice (Exists false where there is none: a gap, the glade, the trail, a stream).</summary>
    public L47Tree L47TreeAt(int i, int j)
    {
        var t = new L47Tree();
        ulong h = Hashing.Hash(seed, i, j, SaltL47Tree);
        t.H = h;
        if (Hashing.Unit(h) < 0.1) return t;
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3), h5 = Hashing.Mix(h4), h6 = Hashing.Mix(h5), h7 = Hashing.Mix(h6), h8 = Hashing.Mix(h7);
        t.X = (i + 0.5) * L47Pitch + (Hashing.Unit(h2) - 0.5) * 8;
        t.Z = (j + 0.5) * L47Pitch + (Hashing.Unit(h3) - 0.5) * 8;
        int ix = (int)Math.Floor(t.X), iz = (int)Math.Floor(t.Z);
        // Kind: oak and beech, fir and spruce, and here and there a dead one
        double k = Hashing.Unit(h4), u = Hashing.Unit(h5);
        if (k < 0.09)
        {
            t.Dead = true;
            t.Bark = L47BarkDead;
            t.R = 1.1 + 1.6 * u;
        }
        else if (k < 0.39) { t.Bark = L47BarkOak; t.Leaf = L47LeafOak; t.R = Hashing.Unit(h6) < 0.07 ? 3.0 + 0.8 * u : 1.3 + 1.6 * Math.Pow(u, 1.3); }
        else if (k < 0.54) { t.Bark = L47BarkBeech; t.Leaf = L47LeafBeech; t.R = 1.1 + 1.2 * u; }
        else if (k < 0.82) { t.Conifer = true; t.Bark = L47BarkFir; t.Leaf = L47LeafNeedle; t.R = Hashing.Unit(h6) < 0.07 ? 2.9 + 0.8 * u : 1.1 + 1.5 * Math.Pow(u, 1.3); }
        else { t.Conifer = true; t.Bark = L47BarkSpruce; t.Leaf = L47LeafNeedle; t.R = 0.9 + 1.0 * u; }
        // Young ones among the old (a sapling's trunk, a small crown), so the forest is not all of one age
        if (!t.Dead && Hashing.Unit(h6 << 17) < 0.12) t.R = 0.55 + 0.25 * Hashing.Unit(h6 << 31);
        if (L47FromMid(t.X, t.Z) < L47GladeClear + t.R) return t;
        if (L47TrailDistance(t.X, t.Z, out _) < L47TrailClear + t.R + 0.5) return t;
        if (L47Stream(ix, iz) < L47BankAt + 0.008) return t;
        t.Base = L47Ground(ix, iz);
        bool young = t.R < 0.9;
        if (t.Dead) t.Top = t.Base + 9 + (int)(18 * Hashing.Unit(h7));
        else if (young) t.Top = t.Base + 8 + (int)(8 * Hashing.Unit(h7));
        else if (t.Conifer) t.Top = Math.Min(L47Top - 1, t.Base + 34 + (int)(12 * Hashing.Unit(h7)) + (int)(t.R * 1.5));
        else t.Top = Math.Min(L47Top - 2, t.Base + 28 + (int)(10 * Hashing.Unit(h7)) + (int)(t.R * 1.5));
        t.Lobes = 3 + (int)(h8 % 3);
        t.Phase = Hashing.Unit(h8 << 9) * Math.PI * 2;
        t.Lean = young ? 0.2 : 0.3 + 0.6 * Hashing.Unit(h8 << 21);
        t.LeanPhase = Hashing.Unit(h8 << 33) * Math.PI * 2;
        if (t.Conifer)
        {
            t.CrownBase = t.Base + (young ? 2 : 9 + (int)(6 * Hashing.Unit(Hashing.Mix(h8))));
            t.CrownR = young ? 2.2 : 4.2 + 1.4 * t.R;
        }
        else
        {
            t.CrownBase = t.Top - (young ? 6 : 14 + (int)(5 * Hashing.Unit(Hashing.Mix(h8))));
            t.CrownR = young ? 2.6 : 4.0 + 1.5 * t.R;
        }
        t.Exists = true;
        L47MaybeHollow(ref t);
        L47Shape(ref t);
        return t;
    }

    /// <summary>The green giant of a square of its own lattice, if one stands there: huge, green-barked and hollow (Wikidot's Level 23: "huge hollow green-barked trees in Levels 37 and 47").</summary>
    public L47Tree L47GiantAt(int i, int j)
    {
        var t = new L47Tree();
        ulong h = Hashing.Hash(seed, i, j, SaltL47Giant);
        t.H = h;
        if (Hashing.Unit(h) > 0.5) return t;
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3);
        t.X = (i + 0.2 + 0.6 * Hashing.Unit(h2)) * L47GiantPitch;
        t.Z = (j + 0.2 + 0.6 * Hashing.Unit(h3)) * L47GiantPitch;
        int ix = (int)Math.Floor(t.X), iz = (int)Math.Floor(t.Z);
        if (LevelAt(MacroOf(ix), MacroOf(iz)) != Level47) return t;
        t.R = 4.2 + 0.6 * Hashing.Unit(h4);
        if (L47FromMid(t.X, t.Z) < L47GladeClear + 30) return t;
        if (L47TrailDistance(t.X, t.Z, out _) < L47TrailClear + t.R + 4) return t;
        if (L47Stream(ix, iz) < L47BankAt + 0.03) return t;
        t.Giant = t.Exists = t.Hollow = true;
        t.Bark = L47BarkGreen;
        t.Leaf = L47LeafOak;
        t.Base = L47Ground(ix, iz);
        t.Top = L47Top;
        t.Lobes = 5;
        t.Phase = Hashing.Unit(Hashing.Mix(h4)) * Math.PI * 2;
        t.Lean = 0.5;
        t.LeanPhase = Hashing.Unit(Hashing.Mix(h4 + 1)) * Math.PI * 2;
        t.CrownBase = L47Top - 22;
        t.CrownR = 13;
        t.MouthA = Hashing.Unit(Hashing.Mix(h4 + 2)) * Math.PI * 2;
        L47Shape(ref t);
        return t;
    }

    /// <summary>How far a trunk's middle has wandered at a height (they lean a little as they climb).</summary>
    private static (double Dx, double Dz) L47Lean(in L47Tree t, int rel)
    {
        double up = Math.Max(0, rel - t.Base);
        return (t.Lean * Math.Sin(up / 13.0 + t.LeanPhase), t.Lean * Math.Cos(up / 17.0 + t.LeanPhase * 1.7));
    }

    /// <summary>
    /// Whether a point is in a trunk at a height: its radius narrowing toward the top, its foot flared into buttresses
    /// (the old ones). <paramref name="depth"/> is how far inside the bark it is.
    /// </summary>
    private static bool L47InTrunk(in L47Tree t, double px, double pz, int rel, out double depth)
    {
        depth = 0;
        if (rel > t.Top) return false;
        var (lx, lz) = L47Lean(t, rel);
        double dx = px - (t.X + lx), dz = pz - (t.Z + lz);
        double up = Math.Max(0, rel - t.Base);
        double h = Math.Max(1, t.Top - t.Base);
        double r = t.R * (1 - (t.Conifer ? 0.55 : t.Dead ? 0.3 : 0.4) * Math.Min(1, up / h));
        r = Math.Max(Math.Min(t.R, 0.75), r);
        double d = Math.Sqrt(dx * dx + dz * dz);
        if (up < 6 && t.R >= 1.3)
        {
            double a = Math.Atan2(dz, dx);
            double fin = Math.Pow(Math.Max(0, Math.Cos(t.Lobes * a + t.Phase)), 3);
            r += (t.Giant ? 3.5 : 1.6 * Math.Min(1, t.R / 2.5)) * fin * Math.Exp(-up / 1.8) + 0.6 * Math.Exp(-up / 1.3);
        }
        depth = r - d;
        // (The thinnest always fill the column they stand in)
        if (d >= r && (int)Math.Floor(px) == (int)Math.Floor(t.X + lx) && (int)Math.Floor(pz) == (int)Math.Floor(t.Z + lz)) { depth = 0.01; return true; }
        return d < r;
    }

    /// <summary>A tube from A to B (heights relative to the floor), arched up by Rise in its middle, thinning by Taper toward B.</summary>
    private static bool L47InTube(double px, double pz, int rel, double ax, double az, double ay, double bx, double bz, double by, double rise, double radius,
        double taper = 0)
    {
        double vx = bx - ax, vz = bz - az, vy = by - ay, len2 = vx * vx + vz * vz + vy * vy;
        if (len2 < 1e-6) return false;
        double py = rel + 0.5;
        double t = Math.Clamp(((px - ax) * vx + (pz - az) * vz + (py - ay) * vy) / len2, 0, 1);
        double cx = ax + vx * t, cz = az + vz * t, cy = ay + vy * t + rise * Math.Sin(Math.PI * t);
        double r = radius * (1 - taper * t);
        double dx = px - cx, dz = pz - cz, dy = py - cy;
        return dx * dx + dz * dz + dy * dy < r * r;
    }

    /// <summary>The trees of a window of the lattice round a column, kept for the columns that ask for the same one.</summary>
    private sealed class L47TreeWindow
    {
        public WorldLayout Owner;
        public int I0, J0;
        public readonly L47Tree[] Trees = new L47Tree[49];
        public WorldLayout CacheOwner;
        public System.Collections.Generic.Dictionary<(int, int), L47Tree> Cache;
    }

    [ThreadStatic] private static L47TreeWindow l47TreeWindow;

    /// <summary>The trees from three lattice steps before a point to three after.</summary>
    private L47Tree[] L47TreesAround(int i0, int j0)
    {
        var w = l47TreeWindow ??= new L47TreeWindow();
        if (w.Owner == this && w.I0 == i0 && w.J0 == j0) return w.Trees;
        w.Owner = null;
        if (w.Cache == null || w.CacheOwner != this || w.Cache.Count > 8192)
        {
            w.Cache = new System.Collections.Generic.Dictionary<(int, int), L47Tree>();
            w.CacheOwner = this;
        }
        for (int dj = -3; dj <= 3; dj++)
            for (int di = -3; di <= 3; di++)
            {
                if (!w.Cache.TryGetValue((i0 + di, j0 + dj), out L47Tree t)) w.Cache[(i0 + di, j0 + dj)] = t = L47TreeAt(i0 + di, j0 + dj);
                w.Trees[(dj + 3) * 7 + di + 3] = t;
            }
        w.Owner = this;
        w.I0 = i0;
        w.J0 = j0;
        return w.Trees;
    }

    [ThreadStatic] private static System.Collections.Generic.List<L47Tree> l47Giants;

    /// <summary>The green giants that may reach a column (its square and the eight round it).</summary>
    private System.Collections.Generic.List<L47Tree> L47GiantsNear(int gx, int gz)
    {
        var into = l47Giants ??= new System.Collections.Generic.List<L47Tree>();
        into.Clear();
        int i0 = Hashing.FloorDiv(gx, L47GiantPitch), j0 = Hashing.FloorDiv(gz, L47GiantPitch);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                double cx = (i0 + di + 0.5) * L47GiantPitch, cz = (j0 + dj + 0.5) * L47GiantPitch;
                if (Math.Abs(gx - cx) > L47GiantPitch * 0.5 + 40 || Math.Abs(gz - cz) > L47GiantPitch * 0.5 + 40) continue;
                L47Tree g = L47GiantCached(i0 + di, j0 + dj);
                if (!g.Exists) continue;
                double dx = gx + 0.5 - g.X, dz = gz + 0.5 - g.Z;
                if (dx * dx + dz * dz < 40 * 40) into.Add(g);
            }
        return into;
    }

    /// <summary>
    /// What fills a column of the forest, from <paramref name="lowest"/> up: <paramref name="kinds"/>[rel - lowest] (see
    /// <see cref="L47Air"/> and the rest). Trunks and their buttresses, roots crawling from their feet, limbs, crowns of
    /// leaves (round lumps for the oaks and beeches, tiered cones for the firs and spruces), the dead trees' bare limbs,
    /// the green giants; fallen logs and mossy boulders on the ground; the Order's way-stones beside the trail.
    /// </summary>
    public void L47Wood(int gx, int gz, int lowest, byte[] kinds)
    {
        Array.Clear(kinds);
        double px = gx + 0.5, pz = gz + 0.5;
        int top = lowest + kinds.Length - 1;
        // (Only what can reach this 16-block square: worked out once for the square, in the order the full search met it)
        L47Bucket near = L47BucketAt(gx, gz);
        L47Tree[] trees = near.Trees;
        // (Trunks first, so a crown's leaves never fill a neighbour's bark)
        for (int pass = 0; pass < 2; pass++)
        {
            if (pass == 1 && top < near.CrownFrom) break;
            for (int n = 0; n < near.TreeCount; n++)
            {
                if (pass == 0) L47TreeWood(trees[n], px, pz, lowest, top, kinds);
                else L47Crown(trees[n], gx, gz, px, pz, lowest, top, kinds);
            }
            if (pass == 0) L47GroundThings(gx, gz, px, pz, lowest, top, kinds, near);
        }
    }

    /// <summary>The trees (the lattice's, then the green giants), logs and boulders that can reach a 16-block square, in the order the full search met them.</summary>
    private sealed class L47Bucket
    {
        public WorldLayout Owner;
        public int Bx = int.MinValue, Bz, TreeCount;
        /// <summary>The lowest height any of its trees' crowns comes down to (a column worked out under it skips the crowns).</summary>
        public int CrownFrom;
        public L47Tree[] Trees = new L47Tree[64];
        public readonly System.Collections.Generic.List<L47Log> Logs = new();
        public readonly System.Collections.Generic.List<L47Boulder> Boulders = new();

        public void Add(in L47Tree t)
        {
            if (TreeCount == Trees.Length) Array.Resize(ref Trees, Trees.Length * 2);
            Trees[TreeCount++] = t;
            if (!t.Dead) CrownFrom = Math.Min(CrownFrom, t.CrownBase - 8);
        }
    }

    [ThreadStatic] private static L47Bucket[] l47Buckets;
    [ThreadStatic] private static int l47BucketNext;

    /// <summary>How far from its middle a tree's wood or leaves can reach, at any height.</summary>
    private static double L47TreeReach(in L47Tree t) =>
        Math.Max(t.R + (t.Giant ? 22 : 9) + t.Lean + (t.Dead || t.Conifer ? 0 : t.CrownR), t.Dead ? 0 : t.CrownR * 1.25 + 2 + t.Lean) + 1;

    private L47Bucket L47BucketAt(int gx, int gz)
    {
        int bx = gx >> 4, bz = gz >> 4;
        var all = l47Buckets ??= new[] { new L47Bucket(), new L47Bucket(), new L47Bucket(), new L47Bucket() };
        for (int k = 0; k < all.Length; k++)
            if (all[k].Owner == this && all[k].Bx == bx && all[k].Bz == bz) return all[k];
        var b = all[l47BucketNext];
        l47BucketNext = (l47BucketNext + 1) % all.Length;
        b.Owner = null;
        b.CrownFrom = int.MaxValue;
        b.TreeCount = 0;
        b.Logs.Clear();
        b.Boulders.Clear();
        double x0 = bx * 16, z0 = bz * 16, x1 = x0 + 16, z1 = z0 + 16;
        double Away(double x, double z)
        {
            double dx = x < x0 ? x0 - x : x > x1 ? x - x1 : 0, dz = z < z0 ? z0 - z : z > z1 ? z - z1 : 0;
            return Math.Sqrt(dx * dx + dz * dz);
        }
        // The lattice's trees in the lattice's order (rows, then columns): what any column of the square could reach
        int ia = Hashing.FloorDiv((int)x0, L47Pitch) - 3, ib = Hashing.FloorDiv((int)x1 - 1, L47Pitch) + 3;
        int ja = Hashing.FloorDiv((int)z0, L47Pitch) - 3, jb = Hashing.FloorDiv((int)z1 - 1, L47Pitch) + 3;
        var kept = L47KeptHere();
        for (int j = ja; j <= jb; j++)
            for (int i = ia; i <= ib; i++)
            {
                if (!kept.Trees.TryGetValue((i, j), out L47Tree t)) kept.Trees[(i, j)] = t = L47TreeAt(i, j);
                if (t.Exists && Away(t.X, t.Z) < L47TreeReach(t)) b.Add(t);
            }
        int gi0 = Hashing.FloorDiv((int)x0, L47GiantPitch), gj0 = Hashing.FloorDiv((int)z0, L47GiantPitch);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L47Tree g = L47GiantCached(gi0 + di, gj0 + dj);
                if (g.Exists && Away(g.X, g.Z) < 40) b.Add(g);
            }
        int li0 = Hashing.FloorDiv((int)x0, 23) - 1, li1 = Hashing.FloorDiv((int)x1 - 1, 23) + 1, lj0 = Hashing.FloorDiv((int)z0, 23) - 1, lj1 = Hashing.FloorDiv((int)z1 - 1, 23) + 1;
        for (int j = lj0; j <= lj1; j++)
            for (int i = li0; i <= li1; i++)
            {
                L47Log l = L47LogCached(i, j);
                if (!l.Exists) continue;
                double pad = l.R + 2;
                if (Math.Max(l.Ax, l.Bx) + pad < x0 || Math.Min(l.Ax, l.Bx) - pad > x1 || Math.Max(l.Az, l.Bz) + pad < z0 || Math.Min(l.Az, l.Bz) - pad > z1) continue;
                b.Logs.Add(l);
            }
        int oi0 = Hashing.FloorDiv((int)x0, 19) - 1, oi1 = Hashing.FloorDiv((int)x1 - 1, 19) + 1, oj0 = Hashing.FloorDiv((int)z0, 19) - 1, oj1 = Hashing.FloorDiv((int)z1 - 1, 19) + 1;
        for (int j = oj0; j <= oj1; j++)
            for (int i = oi0; i <= oi1; i++)
            {
                L47Boulder o = L47BoulderCached(i, j);
                if (o.Exists && Away(o.Cx, o.Cz) < Math.Max(o.Rx, o.Rz) * 1.2 + 1.5) b.Boulders.Add(o);
            }
        b.Bx = bx;
        b.Bz = bz;
        b.Owner = this;
        return b;
    }

    /// <summary>A tree's trunk (hollowed where it is hollow), the roots from its foot, and its limbs.</summary>
    private void L47TreeWood(in L47Tree t, double px, double pz, int lowest, int top, byte[] kinds)
    {
        double dx = px - t.X, dz = pz - t.Z, d2 = dx * dx + dz * dz;
        double reach = t.R + (t.Giant ? 22 : 9) + t.Lean + (t.Dead || t.Conifer ? 0 : t.CrownR);
        if (d2 > reach * reach) return;
        int floor = int.MinValue;
        double trunkReach = t.R + (t.Giant ? 5 : 2.6) + t.Lean;
        if (d2 < trunkReach * trunkReach)
            for (int rel = Math.Max(lowest, t.Base - 6); rel <= Math.Min(top, t.Top); rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                if (!L47InTrunk(t, px, pz, rel, out double depth)) continue;
                if (t.Hollow)
                {
                    if (floor == int.MinValue) floor = L47Ground((int)Math.Floor(px), (int)Math.Floor(pz));
                    if (L47Hollowed(t, px, pz, rel, floor, depth)) continue;
                }
                kinds[rel - lowest] = t.Bark;
            }
        // Roots: three to five crawling out over the ground from the foot of the old ones (a step up)
        if (t.Roots.Length > 0 && lowest <= t.Base + 2 && d2 < t.RootReach * t.RootReach && !(t.Hollow && L47InHollowsWay(t, px, pz)))
            for (int k = 0; k < t.Roots.Length; k += 3)
                for (int rel = Math.Max(lowest, t.Base - 1); rel <= Math.Min(top, t.Base + 2); rel++)
                {
                    if (kinds[rel - lowest] != 0) continue;
                    if (L47InTube(px, pz, rel, t.X, t.Z, t.Base + 0.7, t.Roots[k], t.Roots[k + 1], t.Base + 0.2, 0.3, t.Roots[k + 2], 0.5)) kinds[rel - lowest] = t.Bark;
                }
        // Limbs: the broadleaves' boughs out into their crowns; the dead trees' bare limbs; the conifers have none to speak of
        if (top < t.LimbLow) return;
        for (int k = 0; k < t.Limbs.Length; k += 7)
        {
            double ax = t.Limbs[k];
            if (double.IsNaN(ax)) continue;
            double az = t.Limbs[k + 1], from = t.Limbs[k + 2], bx = t.Limbs[k + 3], bz = t.Limbs[k + 4], rise = t.Limbs[k + 5], rr = t.Limbs[k + 6];
            double lx = bx - ax, lz = bz - az, len = Math.Sqrt(lx * lx + lz * lz);
            if ((px - ax) * (px - ax) + (pz - az) * (pz - az) > (len + 2) * (len + 2)) continue;
            int lo = Math.Max(lowest, (int)from - 2), hi = Math.Min(top, (int)(from + rise) + 2);
            for (int rel = lo; rel <= hi; rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                if (L47InTube(px, pz, rel, ax, az, from, bx, bz, from + rise, 0, rr, 0.4)) kinds[rel - lowest] = t.Bark;
            }
        }
    }

    /// <summary>
    /// A tree's crown: for the broadleaves (and the green giants) a cluster of rough round lumps of leaves over its boughs;
    /// for the conifers a tiered cone, each tier's skirt wider than the one over it; none for the dead.
    /// </summary>
    private void L47Crown(in L47Tree t, int gx, int gz, double px, double pz, int lowest, int top, byte[] kinds)
    {
        if (t.Dead || top < t.CrownBase - 8) return;
        double dx = px - t.X, dz = pz - t.Z, d2 = dx * dx + dz * dz;
        double reach = t.CrownR * 1.25 + 2 + t.Lean;
        if (d2 > reach * reach) return;
        if (t.Conifer)
        {
            var (lx, lz) = L47Lean(t, t.CrownBase);
            double cdx = px - (t.X + lx), cdz = pz - (t.Z + lz), cd = Math.Sqrt(cdx * cdx + cdz * cdz);
            double span = Math.Max(1, t.Top + 2 - t.CrownBase);
            for (int rel = Math.Max(lowest, t.CrownBase); rel <= Math.Min(top, t.Top + 2); rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                double up = (rel - t.CrownBase) / span;
                int tier = (rel - t.CrownBase) % 4;
                double r = t.CrownR * Math.Pow(1 - up, 0.85) * (0.62 + 0.38 * (tier == 0 ? 1 : tier == 1 ? 0.82 : tier == 2 ? 0.64 : 0.5));
                // Ragged edges: the tips of the boughs
                double jag = 0.9 * (Hashing.Unit(Hashing.Hash(seed, gx * 61 + rel, gz, SaltL47Leaf)) - 0.5);
                // (A shell two blocks thick: the light gets in under it, as through a real crown's gaps)
                if (cd < r + jag && cd > 0.4 && (cd > r - 2.2 || tier == 0)) kinds[rel - lowest] = t.Leaf;
            }
            return;
        }
        // Broadleaves: the main lump over the trunk's top and the others round it
        int lobes = t.Giant ? 7 : t.R < 0.9 ? 2 : 4 + (int)(t.H >> 40 & 1);
        for (int k = 0; k < lobes; k++)
        {
            ulong h = Hashing.Mix(t.H + 401 + (ulong)k);
            double a = Hashing.Unit(h) * Math.PI * 2, outward = k == 0 ? 0 : t.CrownR * (0.35 + 0.35 * Hashing.Unit(Hashing.Mix(h)));
            double cy = k == 0 ? t.Top - t.CrownR * 0.35 : t.CrownBase + (t.Top - t.CrownBase) * (0.25 + 0.5 * Hashing.Unit(h << 11));
            var (lx, lz) = L47Lean(t, (int)cy);
            double cx = t.X + lx + Math.Cos(a) * outward, cz = t.Z + lz + Math.Sin(a) * outward;
            double lr = t.CrownR * (k == 0 ? 0.62 : 0.48 + 0.14 * Hashing.Unit(h << 23));
            double ddx = px - cx, ddz = pz - cz, hd2 = ddx * ddx + ddz * ddz;
            if (hd2 > (lr + 1) * (lr + 1)) continue;
            for (int rel = Math.Max(lowest, (int)(cy - lr * 0.7) - 1); rel <= Math.Min(top, (int)(cy + lr * 0.75) + 1); rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                double dy = (rel + 0.5 - cy) / (rel + 0.5 < cy ? 0.62 : 0.78);
                double rough = 0.9 * (Hashing.Unit(Hashing.Hash(seed, gx * 61 + rel, gz, SaltL47Leaf)) - 0.5);
                // (Each lump a shell two blocks thick: the light gets in under it, as through a real crown's gaps)
                double e2 = hd2 + dy * dy, inner = Math.Max(0, lr + rough - 2.2);
                if (e2 < (lr + rough) * (lr + rough) && e2 > inner * inner) kinds[rel - lowest] = t.Leaf;
            }
        }
    }

    // ================= Logs, boulders and the Order's stones =================

    /// <summary>A fallen log on its own lattice (23 blocks), if there is one: its ends, the height of its middle line, its radius, and whether it is dead wood.</summary>
    private bool L47LogAt(int i, int j, out double ax, out double az, out double bx, out double bz, out double y, out double r, out bool dead)
    {
        ulong h = Hashing.Hash(seed, i, j, SaltL47Log);
        ax = az = bx = bz = y = r = 0;
        dead = false;
        if (Hashing.Unit(h) > 0.4) return false;
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3), h5 = Hashing.Mix(h4);
        double cx = (i + 0.5) * 23 + (Hashing.Unit(h2) - 0.5) * 12, cz = (j + 0.5) * 23 + (Hashing.Unit(h3) - 0.5) * 12;
        // Mostly along x or z (so the bark reads as a log), some askew
        double a = Hashing.Unit(h4) < 0.7 ? ((h4 >> 20 & 1) == 0 ? 0 : Math.PI / 2) + (Hashing.Unit(h5) - 0.5) * 0.25 : Hashing.Unit(h5) * Math.PI;
        double len = 7 + 9 * Hashing.Unit(Hashing.Mix(h5));
        r = 0.6 + 0.55 * Hashing.Unit(h5 << 13);
        dead = (h5 >> 40 & 3) == 0;
        if (L47FromMid(cx, cz) < L47GladeClear + len / 2) return false;
        if (L47TrailDistance(cx, cz, out _) < L47TrailClear + len / 2 + 1) return false;
        // (None across a stream: a trunk one block thick spanning the water looked like a plank hung in the air)
        if (L47Stream((int)Math.Floor(cx), (int)Math.Floor(cz)) < L47BankAt + 0.01) return false;
        ax = cx - Math.Cos(a) * len / 2;
        az = cz - Math.Sin(a) * len / 2;
        bx = cx + Math.Cos(a) * len / 2;
        bz = cz + Math.Sin(a) * len / 2;
        if (L47Stream((int)Math.Floor(ax), (int)Math.Floor(az)) < L47BankAt || L47Stream((int)Math.Floor(bx), (int)Math.Floor(bz)) < L47BankAt) return false;
        int ga = L47Ground((int)Math.Floor(ax), (int)Math.Floor(az)), gb = L47Ground((int)Math.Floor(bx), (int)Math.Floor(bz)), gc = L47Ground((int)Math.Floor(cx), (int)Math.Floor(cz));
        // (Over a stream it lies across from bank to bank, a bridge)
        y = Math.Max(Math.Max(ga, gb), Math.Max(gc, 0)) + r + 0.15;
        return true;
    }

    /// <summary>A boulder on its own lattice (19 blocks), if there is one: its middle, its radii, and the height of its middle.</summary>
    private bool L47BoulderAt(int i, int j, out double cx, out double cz, out double rx, out double rz, out double ry, out double cy)
    {
        ulong h = Hashing.Hash(seed, i, j, SaltL47Boulder);
        cx = cz = rx = rz = ry = cy = 0;
        if (Hashing.Unit(h) > 0.28) return false;
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3);
        cx = (i + 0.5) * 19 + (Hashing.Unit(h2) - 0.5) * 12;
        cz = (j + 0.5) * 19 + (Hashing.Unit(h3) - 0.5) * 12;
        double s = 1.0 + 1.6 * Math.Pow(Hashing.Unit(h4), 1.5);
        rx = s * (0.8 + 0.4 * Hashing.Unit(h4 << 10));
        rz = s * (0.8 + 0.4 * Hashing.Unit(h4 << 20));
        ry = s * (0.6 + 0.3 * Hashing.Unit(h4 << 30));
        if (L47FromMid(cx, cz) < L47GladeClear) return false;
        if (L47TrailDistance(cx, cz, out _) < L47TrailHalf + Math.Max(rx, rz) + 0.6) return false;
        cy = L47Ground((int)Math.Floor(cx), (int)Math.Floor(cz)) + 0.4;
        return true;
    }

    /// <summary>The logs, boulders and way-stones in a column.</summary>
    private void L47GroundThings(int gx, int gz, double px, double pz, int lowest, int top, byte[] kinds, L47Bucket near)
    {
        if (lowest > 8) return;
        foreach (L47Log log in near.Logs)
        {
            double ax = log.Ax, az = log.Az, bx = log.Bx, bz = log.Bz, y = log.Y, r = log.R;
            bool alongZ = Math.Abs(bz - az) > Math.Abs(bx - ax);
            byte kind = log.Dead ? (alongZ ? L47LogDeadZ : L47LogDeadX) : (alongZ ? L47LogOakZ : L47LogOakX);
            for (int rel = Math.Max(lowest, (int)(y - r) - 1); rel <= Math.Min(top, (int)(y + r) + 1); rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                if (L47InTube(px, pz, rel, ax, az, y, bx, bz, y, 0, r + 0.15)) kinds[rel - lowest] = kind;
            }
        }
        foreach (L47Boulder stone in near.Boulders)
        {
            double cx = stone.Cx, cz = stone.Cz, rx = stone.Rx, rz = stone.Rz, ry = stone.Ry, cy = stone.Cy;
            double ux = (px - cx) / rx, uz = (pz - cz) / rz;
            if (ux * ux + uz * uz > 1.2) continue;
            for (int rel = Math.Max(lowest, (int)(cy - ry) - 1); rel <= Math.Min(top, (int)(cy + ry) + 1); rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                double uy = (rel + 0.5 - cy) / ry;
                double rough = 0.25 * (Hashing.Unit(Hashing.Hash(seed, gx * 61 + rel, gz, SaltL47Boulder + 1)) - 0.5);
                if (ux * ux + uz * uz + uy * uy < 1 + rough) kinds[rel - lowest] = L47Stone;
            }
        }
        if (L47MarkerHere(gx, gz))
        {
            int g = L47Ground(gx, gz);
            for (int rel = Math.Max(lowest, g + 1); rel <= Math.Min(top, g + 2); rel++) kinds[rel - lowest] = L47TrailStone;
        }
    }

    // ================= Kept: the things on their lattices, worked out once a thread =================

    /// <summary>A fallen log, or a boulder, as <see cref="L47LogAt"/> and <see cref="L47BoulderAt"/> work them out.</summary>
    private struct L47Log { public bool Exists, Dead; public double Ax, Az, Bx, Bz, Y, R; }
    private struct L47Boulder { public bool Exists; public double Cx, Cz, Rx, Rz, Ry, Cy; }

    /// <summary>
    /// The logs, boulders and green giants already worked out on this thread (each lattice point's thing asked for by every
    /// column round it: worked out once instead of a few hundred times; dropped when the layout changes or they grow many).
    /// </summary>
    private sealed class L47Kept
    {
        public WorldLayout Owner;
        public readonly System.Collections.Generic.Dictionary<(int, int), L47Log> Logs = new();
        public readonly System.Collections.Generic.Dictionary<(int, int), L47Boulder> Boulders = new();
        public readonly System.Collections.Generic.Dictionary<(int, int), L47Tree> Giants = new();
        public readonly System.Collections.Generic.Dictionary<(int, int), L47Tree> Trees = new();
    }

    [ThreadStatic] private static L47Kept l47Kept;

    private L47Kept L47KeptHere()
    {
        var k = l47Kept ??= new L47Kept();
        if (k.Owner != this || k.Logs.Count + k.Boulders.Count + k.Trees.Count > 32768)
        {
            k.Logs.Clear();
            k.Boulders.Clear();
            k.Giants.Clear();
            k.Trees.Clear();
            k.Owner = this;
        }
        return k;
    }

    private L47Log L47LogCached(int i, int j)
    {
        var k = L47KeptHere();
        if (k.Logs.TryGetValue((i, j), out L47Log l)) return l;
        l.Exists = L47LogAt(i, j, out l.Ax, out l.Az, out l.Bx, out l.Bz, out l.Y, out l.R, out l.Dead);
        k.Logs[(i, j)] = l;
        return l;
    }

    private L47Boulder L47BoulderCached(int i, int j)
    {
        var k = L47KeptHere();
        if (k.Boulders.TryGetValue((i, j), out L47Boulder b)) return b;
        b.Exists = L47BoulderAt(i, j, out b.Cx, out b.Cz, out b.Rx, out b.Rz, out b.Ry, out b.Cy);
        k.Boulders[(i, j)] = b;
        return b;
    }

    private L47Tree L47GiantCached(int i, int j)
    {
        var k = L47KeptHere();
        if (k.Giants.TryGetValue((i, j), out L47Tree g)) return g;
        return k.Giants[(i, j)] = L47GiantAt(i, j);
    }

    /// <summary>The harness's 47prof: how long the parts of a tile take, over a cell's worth of columns near the glade.</summary>
    public void L47Profile()
    {
        int x0 = L47MidX + 150, z0 = L47MidZ + 90;
        var kinds = new byte[3];
        var sw = new System.Diagnostics.Stopwatch();
        void Time(string name, Action<int, int> f)
        {
            sw.Restart();
            for (int z = 0; z < 64; z++) for (int x = 0; x < 64; x++) f(x0 + x, z0 + z);
            Console.WriteLine($"{name,-12} {sw.Elapsed.TotalMilliseconds / 4:0.00} ms a cell");
        }
        Time("ground", (x, z) => L47Ground(x, z));
        Time("stream", (x, z) => L47Stream(x, z));
        Time("trail", (x, z) => L47TrailAt(x, z));
        Time("marker", (x, z) => L47MarkerHere(x, z));
        Time("wood3", (x, z) => L47Wood(x, z, L47Ground(x, z) + 1, kinds));
        Time("hollow", (x, z) => L47InHollow(x, z, 2, out _, out _));
        Time("anytrunk", (x, z) => L47InAnyTrunk(x, z, 3));
        Time("tile", (x, z) => L47TileAt(x, z, kinds));
        Time("window", (x, z) => L47TreesAround(Hashing.FloorDiv(x, L47Pitch), Hashing.FloorDiv(z, L47Pitch)));
        Time("giants", (x, z) => L47GiantsNear(x, z));
        Time("bucket", (x, z) => L47BucketAt(x, z));
        Time("treewood", (x, z) => { var w = L47TreesAround(Hashing.FloorDiv(x, L47Pitch), Hashing.FloorDiv(z, L47Pitch)); for (int n = 0; n < 49; n++) if (w[n].Exists) L47TreeWood(w[n], x + 0.5, z + 0.5, 3, 5, kinds); });
        Time("crown", (x, z) => { var w = L47TreesAround(Hashing.FloorDiv(x, L47Pitch), Hashing.FloorDiv(z, L47Pitch)); for (int n = 0; n < 49; n++) if (w[n].Exists) L47Crown(w[n], x, z, x + 0.5, z + 0.5, 3, 5, kinds); });
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the forest is laid out tile by tile).</summary>
    private Edge L47Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L47Wall };

    [ThreadStatic] private static byte[] l47Kinds;

    /// <summary>
    /// Lays out one of the level's cells, tile by tile: the thicket where the region ends (every cell on its edge), the
    /// forest (wall where a trunk, a boulder or a high log stands in the way), the trail, the streams, the glade and its
    /// manor; then the supply boxes, and the open ground where people are put down.
    /// </summary>
    private void BuildLevel47(Builder b, int mx, int mz)
    {
        bool rimCell = false;
        for (int dz = -1; dz <= 1 && !rimCell; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Level47) { rimCell = true; break; }

        var kinds = l47Kinds ??= new byte[3];
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (rimCell)
                {
                    t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L47Wall, Floor = FloorKind.L47Bark, Zone = L47RimZone };
                    continue;
                }
                t = L47TileAt(gx, gz, kinds);
            }
        if (rimCell) return;
        L47PlaceThings(b, mx, mz);
        L47MarkOpen(b);
    }

    /// <summary>One tile of the forest.</summary>
    private Tile L47TileAt(int gx, int gz, byte[] kinds)
    {
        int ground = L47Ground(gx, gz);
        var t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.L47Floor, Zone = L47Forest, Height = (byte)Math.Max(0, ground) };
        if (L47FromMid(gx, gz) < L47GladeRadius)
        {
            t.Zone = L47GladeZone;
            t.Floor = FloorKind.L47Grass;
            L47GladeTile(ref t, gx, gz);
            return t;
        }
        if (ground < 1)
        {
            t.Zone = L47StreamZone;
            t.Floor = FloorKind.L47Stream;
            t.Height = 0;
        }
        else if (L47TrailAt(gx, gz) < L47TrailHalf)
        {
            t.Zone = L47TrailZone;
            t.Floor = FloorKind.L47Trail;
        }
        // In the way: a trunk at the foot, anything solid at head height, a root or log to step onto with no room over it
        L47Wood(gx, gz, Math.Max(ground, 0) + 1, kinds);
        bool Solid(byte k) => k != 0 && !L47IsLeaf(k);
        bool blocked = Solid(kinds[1]) || Solid(kinds[0]) && (Solid(kinds[2]) || L47IsBark(kinds[0]) && L47InAnyTrunk(gx, gz, Math.Max(ground, 0) + 1));
        if (blocked)
        {
            t.Kind = TileKind.Wall;
            t.Pattern = WallPattern.L47Wall;
            t.Floor = FloorKind.L47Bark;
        }
        // Inside a hollow tree, or in its mouth (WorldLayout.Level47.Links.cs)
        if (t.Zone == L47Forest && L47InHollow(gx, gz, ground, out bool green, out bool still))
            t.Under = green ? Unders.L47GreenHollow : still ? Unders.L47StillHollow : Unders.L47DeadHollow;
        return t;
    }

    /// <summary>Whether a column's block at a height is in a trunk proper (not a root crawling over the ground).</summary>
    private bool L47InAnyTrunk(int gx, int gz, int rel)
    {
        double px = gx + 0.5, pz = gz + 0.5;
        L47Bucket near = L47BucketAt(gx, gz);
        for (int n = 0; n < near.TreeCount; n++)
        {
            ref readonly L47Tree t = ref near.Trees[n];
            double dx = px - t.X, dz = pz - t.Z, reach = t.R + (t.Giant ? 6 : 3.5) + t.Lean;
            if (dx * dx + dz * dz < reach * reach && L47InTrunk(t, px, pz, rel, out _)) return true;
        }
        return false;
    }

    /// <summary>How far round an arrival spot the ground must be open (a square this many tiles out each way), and along each of the four ways.</summary>
    private const int L47OpenReach = 2, L47OpenWay = 6;

    /// <summary>Marks the tiles with open ground all round them (a five by five square, and six blocks out along each of the four ways), where people are put down.</summary>
    private static void L47MarkOpen(Builder b)
    {
        int n = MacroSize;
        var open = new bool[n * n];
        for (int lz = 0; lz < n; lz++)
            for (int lx = 0; lx < n; lx++)
            {
                Tile t = b.At(lx, lz);
                open[lz * n + lx] = t.Kind == TileKind.Floor && t.Zone is L47Forest or L47TrailZone && t.Under == 0 && t.Variant == 0 && !t.SupplyBox;
            }
        for (int lz = L47OpenWay; lz < n - L47OpenWay; lz++)
            for (int lx = L47OpenWay; lx < n - L47OpenWay; lx++)
            {
                bool all = true;
                for (int dz = -L47OpenReach; dz <= L47OpenReach && all; dz++)
                    for (int dx = -L47OpenReach; dx <= L47OpenReach; dx++)
                        if (!open[(lz + dz) * n + lx + dx]) { all = false; break; }
                for (int d = L47OpenReach + 1; d <= L47OpenWay && all; d++)
                    all = open[(lz + d) * n + lx] && open[(lz - d) * n + lx] && open[lz * n + lx + d] && open[lz * n + lx - d];
                if (all) b.At(lx, lz).Detail |= L47OpenGround;
            }
    }

    /// <summary>A supply box at the foot of a tree in about one cell in six (and the Order's stores in the manor: WorldLayout.Level47.Glade.cs).</summary>
    private void L47PlaceThings(Builder b, int mx, int mz)
    {
        ulong h = Hashing.Hash(seed, mx, mz, SaltL47Box);
        if (Hashing.Unit(h) < 0.17)
        {
            var rng = new Rng(Hashing.Mix(h));
            for (int attempt = 0; attempt < 40; attempt++)
            {
                int x = rng.Range(1, MacroSize - 2), z = rng.Range(1, MacroSize - 2);
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Floor || t.Zone != L47Forest || t.Variant != 0 || t.Under != 0) continue;
                if (b.At(x + 1, z).Kind != TileKind.Wall && b.At(x - 1, z).Kind != TileKind.Wall && b.At(x, z + 1).Kind != TileKind.Wall
                    && b.At(x, z - 1).Kind != TileKind.Wall) continue;
                t.SupplyBox = true;
                break;
            }
        }
        L47PlaceManorThings(b, mx, mz);
    }

    /// <summary>Which of the level's props (<see cref="Props.L47First"/>-<see cref="Props.L47Last"/>) people walk through: none (it has none).</summary>
    private static bool L47WalkThrough(ushort variant) => false;

    // ================= Where someone is =================

    /// <summary>The zone at a position (for the air, the cold and the creatures): the glade (the manor inside it), the trail, a stream, the forest.</summary>
    public byte L47ZoneAt(double x, double z)
    {
        int gx = (int)Math.Floor(x), gz = (int)Math.Floor(z);
        if (L47FromMid(gx + 0.5, gz + 0.5) < L47GladeRadius) return L47InManor(gx, gz) ? L47ManorZone : L47GladeZone;
        if (L47TrailAt(gx, gz) < L47TrailHalf + 0.5) return L47TrailZone;
        if (L47InWater(gx, gz)) return L47StreamZone;
        return L47Forest;
    }

    // ================= Air =================

    /// <summary>The temperature: cool and damp under the trees, colder by the water, a little milder in the glade and the manor.</summary>
    private float L47Temperature(int x, int y, int z, int floorY) => L47ZoneAt(x + 0.5, z + 0.5) switch
    {
        L47ManorZone => 15f,
        L47GladeZone => 12f,
        L47StreamZone => 9f,
        _ => LevelTemperatures[Level47],
    };

    /// <summary>Reality stability: the lore's "high level of ontological instability" (noclipping out is easier than anywhere); the trail holds better, the glade best.</summary>
    private float L47Stability(double x, double y, double z, int floorY, float drift) => L47ZoneAt(x, z) switch
    {
        L47ManorZone or L47GladeZone => 0.95f,
        L47TrailZone => 0.92f,
        _ => 0.86f,
    };
}
