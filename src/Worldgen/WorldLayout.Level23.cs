using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 23, "The Petrified Garden" (experimental): kept as level 28 (<see cref="Level23"/>) and shown as "23". After the
/// Wikidot page (Kitty Rika and Beep Bot; Fandom's Level 23 is an unrelated Vienna and is not used): a planet-sized
/// tangle of petrified trees. The region is a patch of its crust (docs/design/experimental-levels/23-plan.md): a lid of
/// leaves overhead with a few holes the fixed star shines through, a maze of stone trunks, buttress roots and humus
/// under it, glow rooms (caverns lit by Gardener's Sorries) beneath, reached by root tunnels; four ruins of wrong-shaped
/// wonders in the deepest of them, the M.E.G.'s Base Seedling in another, and in the middle the Heart of Water, a basin
/// and its reservoir ringed by Green Giants. No thresholds in or out (the cheats menu or <c>/backrooms goto</c> only).
///
/// <para><b>Everything is a pure function of the block position</b> (and the seed), shared by the layout, the generator
/// (WorldGenerator.L23.cs) and the client (its air, AtmosphereSystem.L23.cs): the ground (<see cref="L23Ground"/>), the
/// trunks on a jittered lattice (<see cref="L23TrunkAt"/>) with their buttresses, roots, arches and limbs
/// (<see cref="L23Wood"/>), the lid and its holes (<see cref="L23LidBottom"/>, <see cref="L23Hole"/>), the caverns
/// (<see cref="L23Cave"/>) and their tunnels (<see cref="L23Tunnel"/>). Heights are relative to the level's floor
/// (<see cref="WorldGeometry.FloorFor"/>, ten below the shared floor): the ground lies at 0 to 3, the caverns at -18 to
/// -3, the lid of leaves from about 33 up to the top of the world (48).</para>
///
/// <para><b>Tiles</b>: <see cref="Tile.Zone"/> is the zone (<see cref="L23Surface"/> ... <see cref="L23RimZone"/>);
/// <see cref="Tile.Height"/> the ground under the open forest (0 to 3); <see cref="Tile.Depth"/> how far below the floor
/// a cavern's or tunnel's floor lies (or the basin's ground); <see cref="Tile.Detail"/> the cavern's colour (1 teal,
/// 2 violet, 3 amber). A column with a cavern under it counts as the cavern's.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2800-0x28BF are this level's (0x28C0-0x28FF its thresholds').</summary>
    private const ulong SaltL23Shape = 0x2801, SaltL23Centre = 0x2802, SaltL23Ground = 0x2803, SaltL23Ridge = 0x2804, SaltL23Trunk = 0x2805,
        SaltL23Arch = 0x2806, SaltL23Cave = 0x2807, SaltL23Hole = 0x2809, SaltL23Lid = 0x280A, SaltL23Rim = 0x280B,
        SaltL23Special = 0x280C, SaltL23Box = 0x280D, SaltL23Snag = 0x280F, SaltL23CaveWobble = 0x2810, SaltL23CaveFloor = 0x2811,
        SaltL23Giant = 0x2812, SaltL23Feature = 0x2814, SaltL23Glade = 0x2815;

    /// <summary>The zones (<see cref="Tile.Zone"/>).</summary>
    public const byte L23Surface = 1, L23Glow = 2, L23TunnelZone = 3, L23Seedling = 4, L23Ruin = 5, L23Core = 6, L23RimZone = 9;

    /// <summary>The top of the world above the level's floor (the floor is <see cref="WorldGeometry.L23Drop"/> below the shared one, which is 39 below the world's top block).</summary>
    public const int L23Top = 38 + WorldGeometry.L23Drop;

    /// <summary>The dense lid of leaves at its thickest: from here to the top of the world (its leaves take two of the sun's light each: under eight of them the forest floor has about six).</summary>
    public const int L23LidDense = 41;

    /// <summary>The dense lid at its thinnest (under five of its leaves the forest floor has about twelve).</summary>
    public const int L23LidThin = 44;

    /// <summary>How far down the lid's loose underside hangs at most.</summary>
    public const int L23LidLow = 33;

    /// <summary>How far out from the middle the forest goes (blocks; the tangle round it wanders some twenty either way).</summary>
    public const int L23Reach = 320;

    /// <summary>The trunks' lattice (blocks).</summary>
    private const int L23Pitch = 15;

    /// <summary>The caverns' lattice (blocks).</summary>
    private const int L23CavePitch = 72;

    /// <summary>The Heart of Water: the clearing's radius, the Green Giants' ring, the pool's radius and its surface.</summary>
    public const int L23CoreRadius = 54, L23GiantRing = 46, L23PoolRadius = 26, L23PoolSurface = -7;

    /// <summary>How deep the floor of an ordinary glow room lies at its middle, a ruin's, and Base Seedling's.</summary>
    public const int L23GlowFloor = -14, L23RuinFloor = -18, L23SeedlingFloor = -12;

    /// <summary>The kinds of wood a column's block can be (<see cref="L23Wood"/>): none, the four barks, the Green Giants' green bark, a root.</summary>
    public const byte L23NoWood = 0, L23BarkGrey = 1, L23BarkRed = 2, L23BarkPale = 3, L23BarkDark = 4, L23BarkGreen = 5, L23RootWood = 6;

    /// <summary>
    /// Round 3's kinds besides: aspen bark (white with black eyes: the lore lists aspen), a boulder's stone, a stone mushroom's
    /// stem and cap, and a fallen log (<see cref="L23LogKind"/>: 16 + its bark times two + 1 when it lies north-south).
    /// </summary>
    public const byte L23BarkAspen = 7, L23Boulder = 8, L23MushStem = 9, L23MushCap = 10, L23LogFirst = 16, L23KindLimit = 32;

    /// <summary>The kind of a fallen log's block: its bark, and whether it lies along z (north-south) rather than x.</summary>
    public static byte L23LogKind(byte bark, bool alongZ) => (byte)(L23LogFirst + bark * 2 + (alongZ ? 1 : 0));

    /// <summary>Whether a kind of block on the ground is low enough to step up onto (a root, a fallen log, a boulder) when nothing is over it.</summary>
    public static bool L23Steppable(byte kind) => kind == L23RootWood || kind == L23Boulder || kind >= L23LogFirst;

    /// <summary>The kinds of cavern.</summary>
    public enum L23CaveKind : byte { None, Glow, Seedling, Ruin }

    /// <summary>The four ruins of the Architects, in the order they lie round the Heart of Water.</summary>
    public enum L23RuinKind : byte { Lighthouse, Sphere, Colosseum, Parthenon }

    // ================= Where it is =================

    /// <summary>
    /// How far out along the south-west diagonal the region's centre lies, on each axis: 1.6 times the city's distance
    /// (beyond Level 974, which is 1.25 times out), as Level 3999 lies beyond the Hub.
    /// </summary>
    private int L23RegionReach => (int)Math.Round(RegionReach * 1.6 / Math.Sqrt(2));

    /// <summary>The region's centre, in macro cells.</summary>
    private int L23CentreX => spawnMacroX - L23RegionReach;
    private int L23CentreZ => spawnMacroZ + L23RegionReach;

    /// <summary>The region's radius in macro cells: thirteen (416 blocks) whatever the world's size: the forest, and the tangle round it.</summary>
    private int L23Radius => 13;

    private bool InL23(double mx, double mz) => InRoundRegion(mx, mz, L23CentreX, L23CentreZ, L23Radius, SaltL23Shape);

    private int l23MidX = int.MinValue, l23MidZ;

    /// <summary>The middle of the forest (the Heart of Water), in blocks: near the region's centre, moved a little by the seed.</summary>
    public int L23MidX
    {
        get
        {
            if (l23MidX == int.MinValue)
            {
                ulong h = Hashing.Hash(seed, 0, 0, SaltL23Centre);
                l23MidZ = L23CentreZ * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Mix(h)) * 25) - 12;
                l23MidX = L23CentreX * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(h) * 25) - 12;
            }
            return l23MidX;
        }
    }

    public int L23MidZ
    {
        get
        {
            _ = L23MidX;
            return l23MidZ;
        }
    }

    /// <summary>
    /// A place to look for somewhere to arrive: by the glade nearest a point of the open forest 90 to 240 blocks from the
    /// Heart of Water (the spot test keeps it on open forest floor).
    /// </summary>
    private (int Mx, int Mz) L23ArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = 90 + 150 * Hashing.Unit(Hashing.Mix(h));
        int px = L23MidX + (int)Math.Round(Math.Cos(angle) * r), pz = L23MidZ + (int)Math.Round(Math.Sin(angle) * r);
        // Round 3: toward the nearest glade (one of the lid's wide holes), where the forest floor is open all round, so
        // those who arrive see the forest and not the bark of the trunk beside them; put down by its edge, not its middle
        int hi = Hashing.FloorDiv(px, L23HolePitch), hj = Hashing.FloorDiv(pz, L23HolePitch);
        double best = double.MaxValue;
        int tx = px, tz = pz;
        for (int dj = -2; dj <= 2; dj++)
            for (int di = -2; di <= 2; di++)
            {
                if (!L23HoleAt(hi + di, hj + dj, out double cx, out double cz, out double hr) || hr < L23GladeMin) continue;
                double dm = L23FromMid((int)cx, (int)cz);
                if (dm < L23CoreRadius + 30 || dm > L23Reach - 30) continue;
                double d = (cx - px) * (cx - px) + (cz - pz) * (cz - pz);
                if (d >= best) continue;
                best = d;
                double a = Hashing.Unit(Hashing.Mix(h + 5)) * Math.PI * 2;
                tx = (int)Math.Round(cx + Math.Cos(a) * (hr - 2));
                tz = (int)Math.Round(cz + Math.Sin(a) * (hr - 2));
            }
        return (MacroOf(tx), MacroOf(tz));
    }

    /// <summary>Arriving: on the forest floor with open floor all round (never over a cavern, in the Heart of Water or the tangle).</summary>
    private static bool IsL23ArrivalSpot(Tile t) => IsArrivalSpot(t) && t.Zone == L23Surface && t.Detail == L23OpenGround;

    /// <summary>
    /// How high above the level's floor to put someone down: on the ground of the forest, or on the floor of a cavern or a
    /// tunnel (Base Seedling's, for those who come home by its hollow tree), or the Heart of Water's shore.
    /// </summary>
    private static double L23ArrivalHeight(in Tile t, double stand) => t.Zone == L23Surface ? t.Height + stand : -t.Depth + stand;

    // ================= The special places =================

    /// <summary>The angle the special places are laid out from (Base Seedling's bearing from the middle).</summary>
    private double L23Bearing => Hashing.Unit(Hashing.Hash(seed, 1, 0, SaltL23Special)) * Math.PI * 2;

    /// <summary>Base Seedling's cavern: its middle (blocks) and radius.</summary>
    public (int X, int Z, int R) L23SeedlingAt
    {
        get
        {
            double a = L23Bearing;
            return (L23MidX + (int)Math.Round(Math.Cos(a) * 165), L23MidZ + (int)Math.Round(Math.Sin(a) * 165), 30);
        }
    }

    /// <summary>A ruin's cavern (0 to 3, <see cref="L23RuinKind"/>): its middle (blocks) and radius.</summary>
    public (int X, int Z, int R) L23RuinAt(int k)
    {
        double a = L23Bearing + Math.PI / 4 + k * Math.PI / 2;
        return (L23MidX + (int)Math.Round(Math.Cos(a) * 228), L23MidZ + (int)Math.Round(Math.Sin(a) * 228), 34);
    }

    // ================= The ground, the lid and the tangle =================

    private static double L23Smooth(double t) => t * t * (3 - 2 * t);

    /// <summary>How far a block position (its middle) lies from the middle of the forest.</summary>
    public double L23FromMid(int gx, int gz)
    {
        double dx = gx + 0.5 - L23MidX, dz = gz + 0.5 - L23MidZ;
        return Math.Sqrt(dx * dx + dz * dz);
    }

    /// <summary>Whether a block position is in the tangle round the forest: fused trunks and roots, solid to the top of the world.</summary>
    public bool L23InTangle(int gx, int gz) => L23FromMid(gx, gz) > L23Reach + 20 * Fbm(gx / 45.0, gz / 45.0, SaltL23Rim);

    /// <summary>
    /// The forest floor at a block position, above the level's floor (negative in the Heart of Water's basin): humus in
    /// gentle humps, ridged where old roots run under it; in the basin it falls away to the shore, and the pool's bed
    /// lies deeper still.
    /// </summary>
    public int L23Ground(int gx, int gz)
    {
        double g = 1.1 + 0.9 * Fbm(gx / 48.0, gz / 48.0, SaltL23Ground) + 0.5 * Noise(gx / 11.0, gz / 11.0, SaltL23Ground + 3);
        if (Math.Abs(Noise(gx / 26.0, gz / 26.0, SaltL23Ridge)) < 0.045) g += 1;
        int ground = Math.Clamp((int)Math.Round(g), 0, 3);
        double dc = L23FromMid(gx, gz);
        if (dc >= L23CoreRadius) return ground;
        // The basin: down from the clearing's rim to a shore at -6, then the pool's bed, deepest in the middle
        if (dc >= L23PoolRadius + 4)
        {
            double s = L23Smooth(Math.Clamp((L23CoreRadius - dc) / (L23CoreRadius - L23PoolRadius - 4.0), 0, 1));
            return (int)Math.Round(ground * (1 - s) + -6 * s);
        }
        if (dc >= L23PoolRadius) return -6;
        // (In the middle of the bed, the well the reservoir goes on down through: WorldLayout.Level23.Links.cs)
        if (dc < L23WellRadius) return L23WellFloor;
        double q = dc / L23PoolRadius;
        return L23PoolSurface - 1 - (int)Math.Round(6 * (1 - q * q));
    }

    /// <summary>The lattice the holes in the lid lie on (blocks).</summary>
    private const int L23HolePitch = 48;

    /// <summary>The hole in the lid at a point of its lattice, if there is one: its middle and radius.</summary>
    public bool L23HoleAt(int i, int j, out double cx, out double cz, out double r)
    {
        ulong h = Hashing.Hash(seed, i, j, SaltL23Hole);
        cx = cz = r = 0;
        if (Hashing.Unit(h) > 0.45) return false;
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2);
        cx = (i + 0.2 + 0.6 * Hashing.Unit(h2)) * L23HolePitch;
        cz = (j + 0.2 + 0.6 * Hashing.Unit(h3)) * L23HolePitch;
        r = 2.2 + 2.3 * Hashing.Unit(Hashing.Mix(h3));
        // Round 3: about one hole in five is wide, a glade of sunlight on the forest floor (a landmark: no tree stands in it)
        ulong g = Hashing.Hash(seed, i, j, SaltL23Glade);
        if (Hashing.Unit(g) < 0.2) r = L23GladeMin + 3 * Hashing.Unit(Hashing.Mix(g));
        return true;
    }

    /// <summary>A hole at least this wide is a glade.</summary>
    public const double L23GladeMin = 6;

    /// <summary>Whether a point lies in a glade (one of the lid's wide holes), within a margin past its edge.</summary>
    public bool L23InGlade(double px, double pz, double margin)
    {
        int hi = Hashing.FloorDiv((int)Math.Floor(px), L23HolePitch), hj = Hashing.FloorDiv((int)Math.Floor(pz), L23HolePitch);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (!L23HoleAt(hi + di, hj + dj, out double cx, out double cz, out double r) || r < L23GladeMin) continue;
                double dx = px - cx, dz = pz - cz;
                if (dx * dx + dz * dz < (r + margin) * (r + margin)) return true;
            }
        return false;
    }

    /// <summary>Whether the sun comes through the lid over a block position: a scatter of holes, and a wide one over the pool.</summary>
    public bool L23Hole(int gx, int gz)
    {
        if (L23FromMid(gx, gz) < 7) return true;
        int hi = Hashing.FloorDiv(gx, L23HolePitch), hj = Hashing.FloorDiv(gz, L23HolePitch);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (!L23HoleAt(hi + di, hj + dj, out double cx, out double cz, out double r)) continue;
                double dx = gx + 0.5 - cx, dz = gz + 0.5 - cz;
                if (dx * dx + dz * dz < r * r) return true;
            }
        return false;
    }

    /// <summary>How far down the lid's loose underside hangs over a block position (<see cref="L23LidLow"/> to <see cref="L23LidDense"/>; higher over the Heart of Water, a vault).</summary>
    public int L23LidBottom(int gx, int gz)
    {
        double dc = L23FromMid(gx, gz);
        double lump = 7 * Fbm(gx / 20.0, gz / 20.0, SaltL23Lid) + 2.5;
        if (dc < L23CoreRadius + 20) lump *= Math.Clamp((dc - L23CoreRadius) / 20.0, 0, 1);
        int dense = L23DenseFrom(gx, gz);
        return Math.Clamp(dense - (int)Math.Round(Math.Max(0, lump)), L23LidLow, dense);
    }

    /// <summary>
    /// Where the lid's dense leaves begin over a block position (<see cref="L23LidDense"/> to <see cref="L23LidThin"/>): in
    /// broad patches it is thinner and the forest floor under it is a little less dark (about 8 to 12 of the sun's light),
    /// so the forest has pools of dimness and of deeper dark besides the shafts under its holes.
    /// </summary>
    public int L23DenseFrom(int gx, int gz)
    {
        double n = Fbm(gx / 36.0, gz / 36.0, SaltL23Lid + 1);
        return Math.Clamp(L23LidDense + 2 + (int)Math.Round(2.6 * n), L23LidDense, L23LidThin);
    }

    // ================= The trunks =================

    /// <summary>One tree of the Garden: where it stands, how thick, its bark, how high it reaches, the shape of its buttresses and lean, and its buried sentry if it has one.</summary>
    public struct L23Trunk
    {
        public bool Exists, Giant, Snag, Pillar, Sentry;
        public double X, Z, R;
        public byte Kind;
        public int Base, Top, Lobes;
        public double Phase, Lean, LeanPhase;
        /// <summary>
        /// Its silhouette: how oval it is across (and which way), how much it narrows from its foot to the lid, how it swells
        /// and pinches as it climbs, and where it forks into two stems (0: it does not) and along which line they part.
        /// </summary>
        public double Ecc, EccPhase, Taper, Swell, SwellPhase, ForkPhase;
        public int ForkAt;
        /// <summary>The sentry's face: the column, and the way it looks out.</summary>
        public int SentryX, SentryZ;
        public ArchPier SentryFacing;
        public ulong H;
        /// <summary>A hollow trunk (WorldLayout.Level23.Links.cs): hollowed out from its foot to a few blocks up, a mouth facing <see cref="MouthA"/> (radians, along x then z).</summary>
        public bool Hollow;
        public double MouthA;
    }

    /// <summary>The tree at a lattice point (Exists false where there is none: a clearing, the Heart of Water, the tangle).</summary>
    public L23Trunk L23TrunkAt(int i, int j)
    {
        var t = new L23Trunk();
        ulong h = Hashing.Hash(seed, i, j, SaltL23Trunk);
        t.H = h;
        if (Hashing.Unit(h) < 0.11) return t; // a clearing
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3), h5 = Hashing.Mix(h4), h6 = Hashing.Mix(h5);
        t.X = (i + 0.5) * L23Pitch + (Hashing.Unit(h2) - 0.5) * 8;
        t.Z = (j + 0.5) * L23Pitch + (Hashing.Unit(h3) - 0.5) * 8;
        int ix = (int)Math.Floor(t.X), iz = (int)Math.Floor(t.Z);
        double dc = L23FromMid(ix, iz);
        if (dc < L23CoreRadius + 3 || dc > L23Reach + 40) return t;
        // (No tree stands in a glade under one of the lid's wide holes: round 3)
        if (L23InGlade(t.X, t.Z, 1.5)) return t;
        double u = Hashing.Unit(h4);
        t.R = Hashing.Unit(h5) < 0.06 ? 6.5 + Hashing.Unit(h6) : 2 + 4.2 * Math.Pow(u, 1.6);
        double k = Hashing.Unit(h6);
        t.Kind = k < 0.45 ? L23BarkGrey : k < 0.65 ? L23BarkRed : k < 0.85 ? L23BarkPale : L23BarkDark;
        t.Base = L23Ground(ix, iz);
        ulong h7 = Hashing.Mix(h6), h8 = Hashing.Mix(h7), h9 = Hashing.Mix(h8);
        t.Snag = Hashing.Unit(h7) < 0.1 && t.R < 5;
        t.Top = t.Snag ? t.Base + 10 + (int)(14 * Hashing.Unit(h8)) : L23Top;
        t.Lobes = 3 + (int)(h9 % 3);
        t.Phase = Hashing.Unit(h8) * Math.PI * 2;
        t.Lean = 0.6 + 1.0 * Hashing.Unit(h9 << 8);
        t.LeanPhase = Hashing.Unit(Hashing.Mix(h9)) * Math.PI * 2;
        t.Pillar = Hashing.Unit(Hashing.Mix(h9 + 1)) < 0.55;
        // Silhouettes (round 2: the trunks were all round columns of one width all the way up): some young and thin, most
        // oval and narrowing toward the lid, some swelling and pinching, a quarter of the thick ones forked into two stems
        ulong s1 = Hashing.Mix(h9 + 3), s2 = Hashing.Mix(s1), s3 = Hashing.Mix(s2), s4 = Hashing.Mix(s3), s5 = Hashing.Mix(s4);
        if (t.R < 6 && Hashing.Unit(s1) < 0.14) t.R = 1.2 + 0.6 * Hashing.Unit(s1 << 20);
        // Round 3: aspens, slender and white with black eyes (the lore lists aspen), among the thinner trees
        if (t.R < 2.6 && Hashing.Unit(s1 << 40) < (t.R < 2 ? 0.6 : 0.3)) t.Kind = L23BarkAspen;
        t.Ecc = 0.22 * Hashing.Unit(s2);
        t.EccPhase = Hashing.Unit(s2 << 20) * Math.PI;
        t.Taper = 0.1 + 0.3 * Hashing.Unit(s3);
        t.Swell = Hashing.Unit(s3 << 20) < 0.35 ? 0.1 + 0.08 * Hashing.Unit(s3 << 40) : 0;
        t.SwellPhase = Hashing.Unit(s4) * Math.PI * 2;
        if (!t.Snag && t.R >= 3 && Hashing.Unit(s4 << 20) < 0.25) t.ForkAt = t.Base + 13 + (int)(9 * Hashing.Unit(s5));
        t.ForkPhase = Hashing.Unit(s5 << 20) * Math.PI;
        t.Exists = true;
        // A buried sentry in about one of the thicker trunks in nine: a face in the bark, between two buttresses, at head height
        if (t.R >= 3 && Hashing.Unit(Hashing.Mix(h9 + 2)) < 0.11)
        {
            double a = (Math.PI - t.Phase) / t.Lobes, ca = Math.Cos(a), sa = Math.Sin(a);
            int rel = t.Base + 2;
            int lastX = ix, lastZ = iz;
            for (double r = 0; r < t.R + 5; r += 0.5)
            {
                int sx = (int)Math.Floor(t.X + ca * r), sz = (int)Math.Floor(t.Z + sa * r);
                if (!L23InTrunk(t, sx + 0.5, sz + 0.5, rel, out _)) break;
                lastX = sx;
                lastZ = sz;
            }
            t.Sentry = true;
            t.SentryX = lastX;
            t.SentryZ = lastZ;
            t.SentryFacing = Math.Abs(ca) > Math.Abs(sa) ? (ca > 0 ? ArchPier.East : ArchPier.West) : (sa > 0 ? ArchPier.South : ArchPier.North);
        }
        L23MaybeHollow(ref t, i, j);
        return t;
    }

    /// <summary>A Green Giant of the ring round the Heart of Water (0 to 6).</summary>
    public L23Trunk L23GiantAt(int k)
    {
        ulong h = Hashing.Hash(seed, k, 0, SaltL23Giant);
        double a = (k + 0.3 * (Hashing.Unit(h) - 0.5)) * Math.PI * 2 / 7 + L23Bearing;
        var t = new L23Trunk
        {
            Exists = true, Giant = true, Kind = L23BarkGreen, H = h,
            X = L23MidX + Math.Cos(a) * L23GiantRing, Z = L23MidZ + Math.Sin(a) * L23GiantRing,
            R = 7 + 1.2 * Hashing.Unit(Hashing.Mix(h)), Top = L23Top, Lobes = 5, Phase = Hashing.Unit(Hashing.Mix(h + 1)) * Math.PI * 2,
            Lean = 0.8, LeanPhase = Hashing.Unit(Hashing.Mix(h + 2)) * Math.PI * 2, Pillar = false,
        };
        t.Base = L23Ground((int)Math.Floor(t.X), (int)Math.Floor(t.Z));
        return t;
    }

    /// <summary>How far a trunk's middle has wandered at a height (they lean and twist as they climb).</summary>
    private static (double Dx, double Dz) L23Lean(in L23Trunk t, int rel)
    {
        double up = Math.Max(0, rel - t.Base);
        return (t.Lean * Math.Sin(up / 9.0 + t.LeanPhase), t.Lean * Math.Cos(up / 11.0 + t.LeanPhase * 1.7));
    }

    /// <summary>
    /// Whether a point is in a trunk at a height: its radius, swollen at the foot into buttresses (fins at its lobes,
    /// dying away three or four blocks up). <paramref name="depth"/> is how far inside the bark it is.
    /// </summary>
    private static bool L23InTrunk(in L23Trunk t, double px, double pz, int rel, out double depth)
    {
        var (lx, lz) = L23Lean(t, rel);
        double dx = px - (t.X + lx), dz = pz - (t.Z + lz);
        double h = rel - t.Base;
        double up = Math.Max(0, h);
        // Narrowing toward the lid, swelling and pinching on the way (never under a block and a half)
        double r = t.R * (1 - t.Taper * Math.Min(1, up / 40)) * (1 + t.Swell * Math.Sin(up / 6.5 + t.SwellPhase));
        r = Math.Max(Math.Min(t.R, 1.5), r);
        // Forked: above the fork two stems, parting along their line and thinner
        if (t.ForkAt > 0 && rel > t.ForkAt)
        {
            double f = Math.Min(1, (rel - t.ForkAt) / 6.0);
            double off = Math.Min(r * 0.75 * f + Math.Max(0, rel - t.ForkAt - 6) * 0.18, r * 1.5);
            double rs = r * (1 - 0.38 * f), cx = Math.Cos(t.ForkPhase) * off, cz = Math.Sin(t.ForkPhase) * off;
            double d1 = Math.Sqrt((dx - cx) * (dx - cx) + (dz - cz) * (dz - cz)), d2 = Math.Sqrt((dx + cx) * (dx + cx) + (dz + cz) * (dz + cz));
            depth = rs - Math.Min(d1, d2);
            return depth > 0;
        }
        double a = Math.Atan2(dz, dx);
        double d = Math.Sqrt(dx * dx + dz * dz) / (1 + t.Ecc * Math.Cos(2 * (a - t.EccPhase)));
        if (h < 9)
        {
            double fin = Math.Pow(Math.Max(0, Math.Cos(t.Lobes * a + t.Phase)), 3);
            r += (t.Giant ? 4.5 : 2.6 * Math.Min(1, t.R / 3)) * fin * Math.Exp(-up / 3.2) + 0.8 * Math.Exp(-up / 2.0);
        }
        depth = r - d;
        return d < r;
    }

    /// <summary>A segment of root or limb: a tube from A to B (heights relative to the floor), arched up by Rise in its middle, thinning by Taper toward B.</summary>
    private static bool L23InTube(double px, double pz, int rel, double ax, double az, double ay, double bx, double bz, double by, double rise, double radius,
        double taper = 0)
    {
        double vx = bx - ax, vz = bz - az, len2 = vx * vx + vz * vz;
        if (len2 < 1e-6) return false;
        double t = Math.Clamp(((px - ax) * vx + (pz - az) * vz) / len2, 0, 1);
        double cx = ax + vx * t, cz = az + vz * t, cy = ay + (by - ay) * t + rise * Math.Sin(Math.PI * t);
        double r = radius * (1 - taper * t);
        double dx = px - cx, dz = pz - cz, dy = rel + 0.5 - cy;
        return dx * dx + dz * dz + dy * dy < r * r;
    }

    /// <summary>The trees of a window of the lattice (from two steps before a lattice point to three after), kept for the columns that ask for the same one.</summary>
    private sealed class L23TrunkWindow
    {
        public WorldLayout Owner;
        public int I0, J0;
        public readonly L23Trunk[] Trunks = new L23Trunk[36];
        public WorldLayout CacheOwner;
        public System.Collections.Generic.Dictionary<(int, int), L23Trunk> Cache;
    }

    [ThreadStatic] private static L23TrunkWindow l23TrunkWindow;

    private L23Trunk[] L23TrunksAround(int i0, int j0)
    {
        var w = l23TrunkWindow ??= new L23TrunkWindow();
        if (w.Owner == this && w.I0 == i0 && w.J0 == j0) return w.Trunks;
        w.Owner = null;
        // (Round 3: each tree worked out once and kept, as the cell's rows bring the same windows round again)
        if (w.Cache == null || w.CacheOwner != this || w.Cache.Count > 8192)
        {
            w.Cache = new System.Collections.Generic.Dictionary<(int, int), L23Trunk>();
            w.CacheOwner = this;
        }
        for (int dj = -2; dj <= 3; dj++)
            for (int di = -2; di <= 3; di++)
            {
                if (!w.Cache.TryGetValue((i0 + di, j0 + dj), out L23Trunk t)) w.Cache[(i0 + di, j0 + dj)] = t = L23TrunkAt(i0 + di, j0 + dj);
                w.Trunks[(dj + 2) * 6 + di + 2] = t;
            }
        w.Owner = this;
        w.I0 = i0;
        w.J0 = j0;
        return w.Trunks;
    }

    /// <summary>
    /// The wood in a column of the forest, from <paramref name="lowest"/> up: <paramref name="kinds"/>[rel - lowest] is
    /// the kind at each height (<see cref="L23NoWood"/> for none). Trunks (to the top of the world, or a snag's broken
    /// top), their buttresses, the roots crawling out over the ground from their feet, the roots that arch from one tree
    /// to the next (high enough in the middle to walk under), and the limbs up into the lid. Below the ground a trunk is
    /// solid all the way down; carving a cavern cuts it (the generator leaves a pillar of it standing there).
    /// </summary>
    public void L23Wood(int gx, int gz, int lowest, byte[] kinds)
    {
        Array.Clear(kinds);
        double px = gx + 0.5, pz = gz + 0.5;
        int i0 = Hashing.FloorDiv(gx, L23Pitch), j0 = Hashing.FloorDiv(gz, L23Pitch);
        int top = lowest + kinds.Length - 1;
        // (The floor's things first: working them out may look at other windows of the trees')
        L23Feature[] things = L23FeaturesAround(gx, gz);
        L23Trunk[] around = L23TrunksAround(i0, j0);

        void Trunk(in L23Trunk t)
        {
            double dx = px - t.X, dz = pz - t.Z;
            double reach = t.R * (1 + t.Ecc + t.Swell) + (t.Giant ? 6.5 : 4.5) + t.Lean + (t.ForkAt > 0 ? t.R * 0.9 : 0);
            if (dx * dx + dz * dz > reach * reach) return;
            int hi = Math.Min(top, t.Snag ? t.Top + (int)(Hashing.Hash(seed, gx, gz, SaltL23Snag) & 3) - 1 : top);
            int floor = int.MinValue;
            for (int rel = lowest; rel <= hi; rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                if (!L23InTrunk(t, px, pz, rel, out double depth)) continue;
                // (A hollow trunk is hollowed out over the ground of this column: WorldLayout.Level23.Links.cs)
                if (t.Hollow)
                {
                    if (floor == int.MinValue) floor = L23Ground(gx, gz);
                    if (L23Hollowed(t, px, pz, rel, floor, depth)) continue;
                }
                kinds[rel - lowest] = t.Kind;
            }
        }

        // The trunks round about (two lattice steps out, for the widest with their buttresses), and their roots and limbs
        for (int dj = -2; dj <= 2; dj++)
            for (int di = -2; di <= 2; di++)
            {
                L23Trunk t = around[(dj + 2) * 6 + di + 2];
                if (!t.Exists) continue;
                Trunk(t);
                L23RootsAndLimbs(t, px, pz, lowest, kinds);
                // Arches: to the tree east, and to the tree south, now and then
                for (int n = 0; n < 2; n++)
                {
                    int ni = i0 + di + (n == 0 ? 1 : 0), nj = j0 + dj + (n == 1 ? 1 : 0);
                    ulong ha = Hashing.Hash(seed, ni * 2 + n, nj, SaltL23Arch);
                    if (Hashing.Unit(ha) > 0.3) continue;
                    L23Trunk o = around[(nj - j0 + 2) * 6 + ni - i0 + 2];
                    if (!o.Exists) continue;
                    L23Arch(t, o, ha, px, pz, lowest, kinds);
                }
            }
        // The Green Giants, near the Heart of Water
        if (Math.Abs(L23FromMid(gx, gz) - L23GiantRing) < 24)
            for (int k = 0; k < 7; k++)
            {
                L23Trunk g = L23GiantAt(k);
                Trunk(g);
                L23RootsAndLimbs(g, px, pz, lowest, kinds);
            }
        // Round 3: what lies on the forest floor between them (WorldLayout.Level23.Features.cs)
        L23FloorThings(things, gx, gz, lowest, kinds);
    }

    /// <summary>The roots crawling out from a tree's foot over the ground (about a block proud of it: a step), and its limbs up into the lid.</summary>
    private void L23RootsAndLimbs(in L23Trunk t, double px, double pz, int lowest, byte[] kinds)
    {
        double dx = px - t.X, dz = pz - t.Z, d2 = dx * dx + dz * dz;
        int top = lowest + kinds.Length - 1;
        // Roots: three or four, out to four to nine blocks past the bark
        int roots = 3 + (int)(t.H >> 60 & 1);
        double far = t.R + (t.Giant ? 16 : 10);
        // (A hollow trunk's roots leave its hollow, its mouth and the way out of it open)
        bool inHollow = t.Hollow && L23InHollowsWay(t, px, pz);
        if (d2 < far * far && lowest <= t.Base + 3 && !inHollow)
            for (int k = 0; k < roots; k++)
            {
                ulong h = Hashing.Mix(t.H + 17 + (ulong)k);
                double a = t.Phase / t.Lobes + k * Math.PI * 2 / roots + (Hashing.Unit(h) - 0.5) * 0.6;
                double len = t.R + (t.Giant ? 9 : 4) + (t.Giant ? 6 : 5) * Hashing.Unit(Hashing.Mix(h));
                double rr = t.Giant ? 1.6 : 0.95 + 0.25 * Hashing.Unit(h << 7);
                double bx = t.X + Math.Cos(a) * len, bz = t.Z + Math.Sin(a) * len;
                double ay = t.Base + 0.6, by = t.Base + 0.1;
                for (int rel = Math.Max(lowest, t.Base - 2); rel <= Math.Min(top, t.Base + 3); rel++)
                {
                    if (kinds[rel - lowest] != 0) continue;
                    if (L23InTube(px, pz, rel, t.X, t.Z, ay, bx, bz, by, 0.4, rr, 0.45)) kinds[rel - lowest] = L23RootWood;
                }
            }
        // Round 3: cypress knees, little stumps of root standing up round a cypress's foot
        if (t.Kind == L23BarkDark && !t.Giant && !inHollow && lowest <= t.Base + 3)
        {
            int knees = 4 + (int)(t.H >> 50 & 3);
            for (int k = 0; k < knees; k++)
            {
                ulong h = Hashing.Mix(t.H + 333 + (ulong)k);
                double a = Hashing.Unit(h) * Math.PI * 2, d = t.R + 2.5 + 3 * Hashing.Unit(h << 12);
                int kx = (int)Math.Floor(t.X + Math.Cos(a) * d), kz = (int)Math.Floor(t.Z + Math.Sin(a) * d);
                if ((int)Math.Floor(px) != kx || (int)Math.Floor(pz) != kz) continue;
                int g = L23Ground(kx, kz);
                for (int rel = Math.Max(lowest, g + 1); rel <= Math.Min(top, g + 1 + (int)(h >> 62 & 1)); rel++)
                    if (kinds[rel - lowest] == 0) kinds[rel - lowest] = L23BarkDark;
            }
        }
        // Limbs: three to five from the trees that reach the lid, rising out into it
        if (t.Snag || t.R < 2.8) return;
        double reach = t.R + 16;
        if (d2 > reach * reach) return;
        int limbs = 3 + (int)(t.H >> 58 & 1) + (t.R >= 4 ? 1 : 0);
        for (int k = 0; k < limbs; k++)
        {
            ulong h = Hashing.Mix(t.H + 101 + (ulong)k);
            double a = Hashing.Unit(h) * Math.PI * 2;
            double from = 17 + 15 * Hashing.Unit(Hashing.Mix(h));
            double len = 5 + t.R + 5 * Hashing.Unit(h << 9);
            double rr = 0.8 + 0.15 * t.R;
            var (lx, lz) = L23Lean(t, (int)from);
            double ax = t.X + lx, az = t.Z + lz;
            double bx = ax + Math.Cos(a) * len, bz = az + Math.Sin(a) * len;
            int lo = Math.Max(lowest, (int)from - 3), hi = Math.Min(top, (int)(from + len * 0.6) + 3);
            for (int rel = lo; rel <= hi; rel++)
            {
                if (kinds[rel - lowest] != 0) continue;
                if (L23InTube(px, pz, rel, ax, az, from, bx, bz, from + len * 0.6, 0, rr, 0.35)) kinds[rel - lowest] = t.Kind;
            }
        }
    }

    /// <summary>A root arching from one tree's foot to the next one's, high enough in its middle to walk under.</summary>
    private void L23Arch(in L23Trunk a, in L23Trunk b, ulong h, double px, double pz, int lowest, byte[] kinds)
    {
        if (a.Giant || b.Giant) return;
        double vx = b.X - a.X, vz = b.Z - a.Z, len = Math.Sqrt(vx * vx + vz * vz);
        if (len < a.R + b.R + 3) return;
        vx /= len;
        vz /= len;
        double ax = a.X + vx * (a.R - 0.5), az = a.Z + vz * (a.R - 0.5), bx = b.X - vx * (b.R - 0.5), bz = b.Z - vz * (b.R - 0.5);
        // (Quick test: the column must lie near the line between the two)
        double t = (px - ax) * vx + (pz - az) * vz, span = len - a.R - b.R + 1;
        if (t < -3 || t > span + 3) return;
        double perp = Math.Abs((px - ax) * vz - (pz - az) * vx);
        double rr = 1.2 + 0.7 * Hashing.Unit(Hashing.Mix(h));
        if (perp > rr + 0.5) return;
        double rise = rr + 3.2 + 3.5 * Hashing.Unit(Hashing.Mix(h + 1));
        double ay = a.Base + 0.5, by = b.Base + 0.5;
        int top = lowest + kinds.Length - 1;
        for (int rel = Math.Max(lowest, Math.Min(a.Base, b.Base) - 1); rel <= Math.Min(top, (int)(Math.Max(ay, by) + rise + rr) + 1); rel++)
        {
            if (kinds[rel - lowest] != 0) continue;
            if (L23InTube(px, pz, rel, ax, az, ay, bx, bz, by, rise, rr)) kinds[rel - lowest] = L23RootWood;
        }
    }

    /// <summary>Whether a column holds a buried sentry's face at a height, and which way it looks.</summary>
    public bool L23SentryAt(int gx, int gz, int rel, out ArchPier facing)
    {
        facing = ArchPier.North;
        L23Trunk[] around = L23TrunksAround(Hashing.FloorDiv(gx, L23Pitch), Hashing.FloorDiv(gz, L23Pitch));
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L23Trunk t = around[(dj + 2) * 6 + di + 2];
                if (!t.Exists || !t.Sentry || rel != t.Base + 2 || t.SentryX != gx || t.SentryZ != gz) continue;
                facing = t.SentryFacing;
                return true;
            }
        return false;
    }

    /// <summary>The bark of the trunk that comes down through a cavern at a column, as a pillar (thinner than above), or 0.</summary>
    public byte L23PillarAt(int gx, int gz)
    {
        L23Trunk[] around = L23TrunksAround(Hashing.FloorDiv(gx, L23Pitch), Hashing.FloorDiv(gz, L23Pitch));
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L23Trunk t = around[(dj + 2) * 6 + di + 2];
                if (!t.Exists || !t.Pillar) continue;
                double dx = gx + 0.5 - t.X, dz = gz + 0.5 - t.Z, r = Math.Max(1.2, t.R * 0.55);
                if (dx * dx + dz * dz < r * r) return t.Kind;
            }
        return 0;
    }

    /// <summary>Whether a trunk's bark (at its foot, buttresses and all) comes within a margin of a block position.</summary>
    public bool L23TrunkNear(int gx, int gz, double margin)
    {
        L23Trunk[] around = L23TrunksAround(Hashing.FloorDiv(gx, L23Pitch), Hashing.FloorDiv(gz, L23Pitch));
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L23Trunk t = around[(dj + 2) * 6 + di + 2];
                if (!t.Exists) continue;
                double dx = gx + 0.5 - t.X, dz = gz + 0.5 - t.Z, r = t.R + 2.6 + margin;
                if (dx * dx + dz * dz < r * r) return true;
            }
        return false;
    }

    // ================= The caverns and their tunnels =================

    /// <summary>A root tunnel: from inside its cavern near the edge (A, at the cavern's floor) up to the forest floor (B).</summary>
    public struct L23Passage
    {
        public double Ax, Az, Bx, Bz;
        public int Fa, Fb;
    }

    /// <summary>A cavern: its middle, radius, kind and colour (1 teal, 2 violet, 3 amber), its floor at the middle, the ruin it holds, its tunnels and its hash.</summary>
    public struct L23Cavern
    {
        public bool Exists;
        public L23CaveKind Kind;
        public int X, Z, R, Floor;
        public byte Colour;
        public L23RuinKind Ruin;
        public int Tunnels;
        public L23Passage T0, T1, T2;
        public ulong H;

        public readonly L23Passage Tunnel(int m) => m == 0 ? T0 : m == 1 ? T1 : T2;
    }

    /// <summary>The ordinary glow room at a lattice point of the caverns' lattice (Exists false where there is none).</summary>
    public L23Cavern L23GlowAt(int i, int j)
    {
        var c = new L23Cavern();
        ulong h = Hashing.Hash(seed, i, j, SaltL23Cave);
        c.H = h;
        if (Hashing.Unit(h) > 0.7) return c;
        ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3);
        c.X = (int)Math.Round((i + 0.5) * L23CavePitch + (Hashing.Unit(h2) - 0.5) * 28);
        c.Z = (int)Math.Round((j + 0.5) * L23CavePitch + (Hashing.Unit(h3) - 0.5) * 28);
        c.R = 18 + (int)(14 * Hashing.Unit(h4));
        double dc = L23FromMid(c.X, c.Z);
        if (dc < L23CoreRadius + c.R + 20 || dc > L23Reach - c.R - 16) return c;
        foreach (L23Cavern s in L23Specials)
            if (L23Apart(c, s.X, s.Z, s.R) < 12) return c;
        c.Kind = L23CaveKind.Glow;
        c.Floor = L23GlowFloor;
        c.Colour = (byte)(1 + (int)(Hashing.Mix(h4) % 3));
        c.Exists = true;
        L23Dig(ref c);
        return c;
    }

    /// <summary>The lattice of the glow rooms' little petrified trees (blocks), and its salt (the generator's, 0x2842).</summary>
    public const int L23TreePitch = 7;
    private const ulong SaltL23LittleTree = 0x2842;

    /// <summary>The little tree on a point of its lattice, if there is one (it only grows where a glow room is): its column and hash.</summary>
    public bool L23LittleTreeAt(int i, int j, out int x, out int z, out ulong h)
    {
        h = Hashing.Hash(seed, i, j, SaltL23LittleTree);
        x = z = 0;
        if (Hashing.Unit(h) > 0.45) return false;
        x = i * L23TreePitch + 1 + (int)(Hashing.Mix(h) % (L23TreePitch - 2));
        z = j * L23TreePitch + 1 + (int)(Hashing.Mix(h + 1) % (L23TreePitch - 2));
        return true;
    }

    private static double L23Apart(in L23Cavern c, int x, int z, int r) => Math.Sqrt((double)(c.X - x) * (c.X - x) + (double)(c.Z - z) * (c.Z - z)) - c.R - r;

    private L23Cavern[] l23Specials;

    /// <summary>The special caverns: Base Seedling (index 0) and the four ruins (1 to 4, <see cref="L23RuinKind"/> order).</summary>
    public L23Cavern[] L23Specials
    {
        get
        {
            if (l23Specials != null) return l23Specials;
            var all = new L23Cavern[5];
            var s = L23SeedlingAt;
            all[0] = new L23Cavern
            {
                Exists = true, Kind = L23CaveKind.Seedling, X = s.X, Z = s.Z, R = s.R, Floor = L23SeedlingFloor, Colour = 3,
                H = Hashing.Hash(seed, 0, 9, SaltL23Special),
            };
            for (int k = 0; k < 4; k++)
            {
                var r = L23RuinAt(k);
                all[k + 1] = new L23Cavern
                {
                    Exists = true, Kind = L23CaveKind.Ruin, X = r.X, Z = r.Z, R = r.R, Floor = L23RuinFloor, Colour = (byte)(1 + k % 3),
                    Ruin = (L23RuinKind)k, H = Hashing.Hash(seed, k + 1, 9, SaltL23Special),
                };
            }
            for (int k = 0; k < 5; k++) L23Dig(ref all[k]);
            return l23Specials = all;
        }
    }

    /// <summary>
    /// Lays out a cavern's tunnels: two for a glow room, three for Base Seedling and the ruins, evenly round it from a
    /// bearing of its own, each turned a little at a time until its mouth is clear of trunks and of the Heart of Water.
    /// </summary>
    private void L23Dig(ref L23Cavern c)
    {
        c.Tunnels = c.Kind == L23CaveKind.Glow ? 2 : 3;
        for (int m = 0; m < c.Tunnels; m++)
        {
            double a = Hashing.Unit(Hashing.Mix(c.H + 31)) * Math.PI * 2 + m * Math.PI * 2 / c.Tunnels;
            double bx = 0, bz = 0;
            for (int tries = 0; tries < 8; tries++, a += 0.33)
            {
                bx = c.X + Math.Cos(a) * (c.R + 26);
                bz = c.Z + Math.Sin(a) * (c.R + 26);
                int ix = (int)Math.Floor(bx), iz = (int)Math.Floor(bz);
                if (!L23TrunkNear(ix, iz, 3) && L23FromMid(ix, iz) > L23CoreRadius + 6) break;
            }
            var p = new L23Passage
            {
                Ax = c.X + Math.Cos(a) * c.R * 0.72, Az = c.Z + Math.Sin(a) * c.R * 0.72, Bx = bx, Bz = bz,
                Fa = c.Kind == L23CaveKind.Glow ? c.Floor + 2 : c.Floor + 1, Fb = L23Ground((int)Math.Floor(bx), (int)Math.Floor(bz)),
            };
            if (m == 0) c.T0 = p;
            else if (m == 1) c.T1 = p;
            else c.T2 = p;
        }
    }

    /// <summary>The caverns that may reach the columns of one cell of the caverns' lattice: its glow room and its neighbours', and the special ones.</summary>
    private sealed class L23CaveWindow
    {
        public WorldLayout Owner;
        public int I0, J0, Count;
        public readonly L23Cavern[] Caverns = new L23Cavern[14];
    }

    [ThreadStatic] private static L23CaveWindow l23CaveWindow;

    private L23CaveWindow L23CavernsNear(int gx, int gz)
    {
        int i0 = Hashing.FloorDiv(gx, L23CavePitch), j0 = Hashing.FloorDiv(gz, L23CavePitch);
        var w = l23CaveWindow ??= new L23CaveWindow();
        if (w.Owner == this && w.I0 == i0 && w.J0 == j0) return w;
        w.Owner = null;
        int n = 0;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                L23Cavern c = L23GlowAt(i0 + di, j0 + dj);
                if (c.Exists) w.Caverns[n++] = c;
            }
        foreach (L23Cavern s in L23Specials) w.Caverns[n++] = s;
        w.Count = n;
        w.I0 = i0;
        w.J0 = j0;
        w.Owner = this;
        return w;
    }

    /// <summary>The flat ground a ruin or Base Seedling stands on: how far out from the cavern's middle (blocks).</summary>
    public static int L23FlatRadius(L23CaveKind kind) => kind == L23CaveKind.Ruin ? 17 : kind == L23CaveKind.Seedling ? 21 : 0;

    /// <summary>
    /// The cavern open at a column: its floor (the top of the solid ground in it) and ceiling (the lowest solid block over
    /// it), relative to the level's floor, and the cavern itself; false where there is none. A dome: the floor rises and
    /// the ceiling sinks toward the edge, where they meet; the edge wanders. Base Seedling and the ruins stand on flat ground.
    /// </summary>
    public bool L23Cave(int gx, int gz, out int floor, out int ceiling, out L23Cavern cavern)
    {
        floor = ceiling = 0;
        cavern = default;
        L23CaveWindow w = L23CavernsNear(gx, gz);
        bool found = false;
        for (int k = 0; k < w.Count; k++)
        {
            L23Cavern c = w.Caverns[k];
            double dx = gx + 0.5 - c.X, dz = gz + 0.5 - c.Z;
            double d2 = dx * dx + dz * dz, far = c.R * 1.15;
            if (d2 >= far * far) continue;
            double d = Math.Sqrt(d2);
            double r = c.R * (1 + 0.14 * Noise(gx / 16.0, gz / 16.0, SaltL23CaveWobble));
            if (d >= r) continue;
            double q = d / r;
            int flat = L23FlatRadius(c.Kind);
            int f = flat > 0 && d < flat ? c.Floor
                : (int)Math.Round(c.Floor + 3.5 * q * q + 1.1 * Noise(gx / 7.0, gz / 7.0, SaltL23CaveFloor) + (flat > 0 ? 0.6 : 0));
            double rise = c.Kind == L23CaveKind.Ruin ? 1.8 : 1.4;
            int ceil = (int)Math.Round(-3 - (c.Kind == L23CaveKind.Ruin ? 10 : 7) * Math.Pow(q, rise) - 0.6 * Math.Abs(Noise(gx / 5.0, gz / 5.0, SaltL23CaveWobble + 1)));
            if (ceil - f < 3) continue;
            if (!found || ceil - f > ceiling - floor)
            {
                floor = f;
                ceiling = ceil;
                cavern = c;
                found = true;
            }
        }
        return found;
    }

    /// <summary>
    /// A root tunnel at a column: its floor and ceiling (relative to the level's floor), and how far the column lies from
    /// its middle line as a share of its half-width (under 1 inside; up to about 2 for the walls just outside, which roots
    /// line); false where none passes near. Each slopes up from a cavern's floor near its edge to the forest floor some
    /// twenty-five blocks out, three to five wide, four high.
    /// </summary>
    public bool L23Tunnel(int gx, int gz, out int floor, out int ceiling, out double off) => L23Tunnel(gx, gz, out floor, out ceiling, out off, out _);

    /// <summary>A root tunnel at a column, as above, and the kind of cavern it leads down to.</summary>
    public bool L23Tunnel(int gx, int gz, out int floor, out int ceiling, out double off, out L23CaveKind kind)
    {
        floor = ceiling = 0;
        off = 99;
        kind = L23CaveKind.None;
        L23CaveWindow w = L23CavernsNear(gx, gz);
        double px = gx + 0.5, pz = gz + 0.5;
        for (int k = 0; k < w.Count; k++)
        {
            L23Cavern c = w.Caverns[k];
            double far = c.R + 34;
            double cdx = px - c.X, cdz = pz - c.Z;
            if (cdx * cdx + cdz * cdz > far * far) continue;
            for (int m = 0; m < c.Tunnels; m++)
            {
                L23Passage p = c.Tunnel(m);
                double vx = p.Bx - p.Ax, vz = p.Bz - p.Az, len2 = vx * vx + vz * vz;
                double t = ((px - p.Ax) * vx + (pz - p.Az) * vz) / len2;
                if (t < -0.05 || t > 1.08) continue;
                double tc = Math.Clamp(t, 0, 1);
                double ox = px - (p.Ax + vx * tc), oz = pz - (p.Az + vz * tc);
                double width = 1.7 + 0.8 * (1 - tc);
                double o = Math.Sqrt(ox * ox + oz * oz) / width;
                if (o > 2.2 || o >= off) continue;
                off = o;
                kind = c.Kind;
                floor = (int)Math.Round(p.Fa + (p.Fb - p.Fa) * L23Smooth(tc));
                ceiling = floor + 5;
            }
        }
        return off < 2.2;
    }

    // ================= Where someone is =================

    /// <summary>
    /// The zone at a position (for the air, the danger and the cold): the tangle, the Heart of Water, a cavern's kind
    /// (or a tunnel) for someone below the forest floor, else the open forest; with the cavern's colour.
    /// </summary>
    public byte L23ZoneAt(double x, double y, double z, int floorY, out byte colour)
    {
        colour = 0;
        int gx = (int)Math.Floor(x), gz = (int)Math.Floor(z);
        if (L23InTangle(gx, gz)) return L23RimZone;
        if (L23FromMid(gx, gz) < L23CoreRadius) return L23Core;
        double rel = y - floorY;
        int ground = L23Ground(gx, gz);
        if (rel < ground - 1)
        {
            if (L23Cave(gx, gz, out int f, out int c, out L23Cavern cav) && rel > f - 1 && rel < c + 1)
            {
                colour = cav.Colour;
                return cav.Kind switch { L23CaveKind.Seedling => L23Seedling, L23CaveKind.Ruin => L23Ruin, _ => L23Glow };
            }
            return L23TunnelZone;
        }
        return L23Surface;
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the forest is laid out tile by tile).</summary>
    private Edge L23Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L23Wall };

    [ThreadStatic] private static byte[] l23Kinds;

    /// <summary>
    /// Lays out one of the level's cells, tile by tile: the tangle round the forest (and every cell at the region's edge),
    /// the open forest (wall where a trunk or a high root stands in the way), the caverns and tunnels under it, the Heart
    /// of Water; then the supply boxes and Base Seedling's camp.
    /// </summary>
    private void BuildLevel23(Builder b, int mx, int mz)
    {
        bool rimCell = false;
        for (int dz = -1; dz <= 1 && !rimCell; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Level23) { rimCell = true; break; }

        var kinds = l23Kinds ??= new byte[4];
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (rimCell || L23InTangle(gx, gz))
                {
                    t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L23Wall, Floor = FloorKind.L23Bark, Zone = L23RimZone };
                    continue;
                }
                t = L23TileAt(gx, gz, kinds);
            }
        if (!rimCell) L23PlaceThings(b, mx, mz);
        if (!rimCell) L23MarkOpen(b);
    }

    /// <summary>A surface tile's <see cref="Tile.Detail"/> when open forest floor lies all round it (<see cref="L23MarkOpen"/>).</summary>
    public const byte L23OpenGround = 1;

    /// <summary>How far round an arrival spot the forest floor must be open (a square this many tiles out each way), and how far it must stay open along each of the four ways.</summary>
    private const int L23OpenReach = 2, L23OpenWay = 7;

    /// <summary>
    /// Marks the forest floor's tiles with open floor all round them (a five by five square of it, no trunk, root, log or
    /// hollow) and open forest floor seven blocks out along each of the four ways, where those who arrive are put down
    /// (round 3: they arrived nose to the bark, and whichever way they turned they saw a trunk).
    /// </summary>
    private static void L23MarkOpen(Builder b)
    {
        int n = MacroSize;
        var open = new bool[n * n];
        for (int lz = 0; lz < n; lz++)
            for (int lx = 0; lx < n; lx++)
            {
                Tile t = b.At(lx, lz);
                open[lz * n + lx] = t.Kind == TileKind.Floor && t.Zone == L23Surface && t.Under == 0 && t.Variant == 0 && !t.SupplyBox;
            }
        for (int lz = L23OpenWay; lz < n - L23OpenWay; lz++)
            for (int lx = L23OpenWay; lx < n - L23OpenWay; lx++)
            {
                bool all = true;
                for (int dz = -L23OpenReach; dz <= L23OpenReach && all; dz++)
                    for (int dx = -L23OpenReach; dx <= L23OpenReach; dx++)
                        if (!open[(lz + dz) * n + lx + dx]) { all = false; break; }
                for (int d = L23OpenReach + 1; d <= L23OpenWay && all; d++)
                    all = open[(lz + d) * n + lx] && open[(lz - d) * n + lx] && open[lz * n + lx + d] && open[lz * n + lx - d];
                if (all) b.At(lx, lz).Detail = L23OpenGround;
            }
    }

    /// <summary>One tile of the forest (not the tangle).</summary>
    private Tile L23TileAt(int gx, int gz, byte[] kinds)
    {
        int ground = L23Ground(gx, gz);
        var t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.L23Floor, Zone = L23Surface, Height = (byte)Math.Max(0, ground) };
        if (L23FromMid(gx, gz) < L23CoreRadius)
        {
            t.Zone = L23Core;
            t.Height = 0;
            t.Depth = (byte)Math.Max(0, -ground);
            t.Floor = ground < L23PoolSurface ? FloorKind.L23Water : FloorKind.L23Moss;
            if (ground == L23WellFloor) t.Under = Unders.L23Well;
        }
        // In the way: a trunk or a buttress at the foot; anything at head height; a root to step onto with no room over it
        L23Wood(gx, gz, ground + 1, kinds);
        bool blocked = kinds[1] != 0 || kinds[0] != 0 && (!L23Steppable(kinds[0]) || kinds[2] != 0);
        if (blocked)
        {
            t.Kind = TileKind.Wall;
            t.Pattern = WallPattern.L23Wall;
            t.Floor = FloorKind.L23Bark;
        }
        // A cavern or a tunnel under it: the column counts as theirs, open at their floor
        if (L23Cave(gx, gz, out int f, out _, out L23Cavern cav))
        {
            t.Kind = TileKind.Floor;
            t.Zone = cav.Kind switch { L23CaveKind.Seedling => L23Seedling, L23CaveKind.Ruin => L23Ruin, _ => L23Glow };
            t.Depth = (byte)Math.Max(0, -f);
            t.Detail = cav.Colour;
            t.Floor = FloorKind.L23Moss;
        }
        else if (L23Tunnel(gx, gz, out int tf, out _, out double off) && off < 1)
        {
            t.Kind = TileKind.Floor;
            if (tf < ground - 1)
            {
                t.Zone = L23TunnelZone;
                t.Depth = (byte)Math.Max(0, -tf);
                t.Floor = FloorKind.L23Earth;
            }
        }
        // Inside a hollow trunk, or in its mouth (WorldLayout.Level23.Links.cs)
        if (t.Zone == L23Surface && t.Kind == TileKind.Floor && L23InHollowTrunk(gx, gz, ground)) t.Under = Unders.L23HollowTrunk;
        return t;
    }

    /// <summary>
    /// What is put down in a cell besides the ground: a supply box at the foot of a tree now and then, boxes against the
    /// walls of the glow rooms and among the ruins, and Base Seedling's camp (its tents and stores round the hollow tree).
    /// </summary>
    private void L23PlaceThings(Builder b, int mx, int mz)
    {
        // A box at the foot of a tree, in about one cell in seven
        ulong h = Hashing.Hash(seed, mx, mz, SaltL23Box);
        if (Hashing.Unit(h) < 0.14)
        {
            var rng = new Rng(Hashing.Mix(h));
            for (int attempt = 0; attempt < 40; attempt++)
            {
                int x = rng.Range(1, MacroSize - 2), z = rng.Range(1, MacroSize - 2);
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Floor || t.Zone != L23Surface || t.Variant != 0) continue;
                if (b.At(x + 1, z).Kind != TileKind.Wall && b.At(x - 1, z).Kind != TileKind.Wall && b.At(x, z + 1).Kind != TileKind.Wall
                    && b.At(x, z - 1).Kind != TileKind.Wall) continue;
                t.SupplyBox = true;
                break;
            }
        }
        // In the caverns: a box at the edge of a glow room now and then, more among the ruins (never in a building)
        for (int lz = 1; lz < MacroSize - 1; lz++)
            for (int lx = 1; lx < MacroSize - 1; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Zone is not (L23Glow or L23Ruin) || t.Kind != TileKind.Floor) continue;
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                double chance = t.Zone == L23Ruin ? 0.004 : 0.0016;
                if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL23Box + 1)) >= chance) continue;
                if (t.Zone == L23Glow && b.At(lx + 1, lz).Zone == t.Zone && b.At(lx - 1, lz).Zone == t.Zone && b.At(lx, lz + 1).Zone == t.Zone
                    && b.At(lx, lz - 1).Zone == t.Zone) continue;
                if (t.Zone == L23Ruin && L23InRuinBuilding(gx, gz)) continue;
                t.SupplyBox = true;
            }
        L23PitchSeedling(b, mx, mz);
    }

    /// <summary>Whether a block position is under one of the ruins' buildings (or its steps), where no box goes.</summary>
    public bool L23InRuinBuilding(int gx, int gz)
    {
        for (int k = 0; k < 4; k++)
        {
            var r = L23RuinAt(k);
            if (Math.Abs(gx - r.X) <= 13 && Math.Abs(gz - r.Z) <= 13) return true;
        }
        return false;
    }

    /// <summary>
    /// Base Seedling's camp, in its cavern's own coordinates (u east, v south of the middle, where the hollow tree
    /// stands): three M.E.G. tents facing the tree, and their stores beside them.
    /// </summary>
    public static readonly (int U, int V, ArchPier Door)[] L23Tents = { (-11, -4, ArchPier.East), (8, -11, ArchPier.South), (6, 8, ArchPier.North) };

    /// <summary>Base Seedling's stores (supply boxes), cavern-local.</summary>
    public static readonly (int U, int V)[] L23Stores = { (-11, 0), (-10, 0), (11, -11), (9, 11), (-3, 12) };

    /// <summary>The four tiles of one of Base Seedling's tents (front left first, by part), moved a step or two if need be so one cell holds all of it.</summary>
    public (int X, int Z)[] L23TentTiles(int k)
    {
        var s = L23SeedlingAt;
        var (u, v, door) = L23Tents[k];
        ArchPier facing = PartsFacing(Props.CampTent, door);
        var tiles = new (int X, int Z)[4];
        (int, int)[] nudges = { (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1) };
        foreach (var (nx, nz) in nudges)
        {
            int x0 = s.X + u + nx, z0 = s.Z + v + nz;
            for (int n = 0; n < 4; n++) tiles[n] = PartTile(x0, z0, facing, n % 2, n / 2);
            int cx = MacroOf(tiles[0].X), cz = MacroOf(tiles[0].Z);
            bool one = true;
            for (int n = 1; n < 4; n++) one &= MacroOf(tiles[n].X) == cx && MacroOf(tiles[n].Z) == cz;
            if (one) break;
        }
        return tiles;
    }

    private void L23PitchSeedling(Builder b, int mx, int mz)
    {
        var s = L23SeedlingAt;
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        if (Math.Abs(s.X - (x0 + MacroSize / 2)) > s.R + MacroSize || Math.Abs(s.Z - (z0 + MacroSize / 2)) > s.R + MacroSize) return;
        for (int k = 0; k < L23Tents.Length; k++)
        {
            (int X, int Z)[] tiles = L23TentTiles(k);
            for (int part = 0; part < 4; part++)
            {
                int lx = tiles[part].X - x0, lz = tiles[part].Z - z0;
                if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
                ref Tile t = ref b.At(lx, lz);
                t.Kind = TileKind.Floor;
                t.Variant = Props.CampTent;
                t.Stack = (byte)part;
                t.Pier = L23Tents[k].Door;
            }
        }
        foreach (var (u, v) in L23Stores)
        {
            int lx = s.X + u - x0, lz = s.Z + v - z0;
            if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
            ref Tile t = ref b.At(lx, lz);
            if (t.Variant != 0) continue;
            t.Kind = TileKind.Floor;
            t.SupplyBox = true;
        }
        // The hollow tree in the middle: its ring of green bark is wall, its hollow floor nobody is put down in
        for (int v = -4; v <= 4; v++)
            for (int u = -4; u <= 4; u++)
            {
                int lx = s.X + u - x0, lz = s.Z + v - z0;
                if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
                double d = Math.Sqrt(u * u + v * v);
                ref Tile t = ref b.At(lx, lz);
                if (d < 2.4)
                {
                    t.Sealed = true;
                    // (Climbing up it is the way home: WorldLayout.Level23.Links.cs)
                    t.Under = Unders.L23SeedlingHollow;
                }
                else if (d < 3.9 && !L23HollowDoor(u, v))
                {
                    t.Kind = TileKind.Wall;
                    t.Pattern = WallPattern.L23Wall;
                }
                else if (d < 3.9) t.Under = Unders.L23SeedlingDoor;
            }
    }

    /// <summary>Whether a cavern-local position is in the hollow tree's opening (on its south side, three wide).</summary>
    public static bool L23HollowDoor(int u, int v) => v > 0 && Math.Abs(u) <= 1;

    /// <summary>Base Seedling's wanderer: the M.E.G.'s quartermaster, in front of the hollow tree (in that cell only).</summary>
    public (int X, int Z)? L23WandererSite(int mx, int mz)
    {
        var s = L23SeedlingAt;
        int x = s.X, z = s.Z + 6;
        return MacroOf(x) == mx && MacroOf(z) == mz ? (x, z) : null;
    }

    /// <summary>Which of the level's props (<see cref="Props.L23First"/>-<see cref="Props.L23Last"/>) people walk through: none (it has none).</summary>
    private static bool L23WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: mild in the forest, cool and damp in the glow rooms, cooler by the water, the camp a little warmer.</summary>
    private float L23Temperature(int x, int y, int z, int floorY) => L23ZoneAt(x + 0.5, y, z + 0.5, floorY, out _) switch
    {
        L23Glow or L23TunnelZone or L23Ruin => 12f,
        L23Seedling => 15f,
        L23Core => 14f,
        _ => 17f,
    };

    /// <summary>Reality stability: a slow drain everywhere but Base Seedling, a little faster among the ruins of the Architects' failed project.</summary>
    private float L23Stability(double x, double y, double z, int floorY, float drift) => L23ZoneAt(x, y, z, floorY, out _) switch
    {
        L23Seedling => 1f,
        L23Ruin => 0.86f,
        L23Core => 0.97f,
        _ => 0.93f,
    };
}
