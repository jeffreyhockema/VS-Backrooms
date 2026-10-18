using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 8's 9th Road from layout version 9: a few long roads through endless caves instead of a lattice.
///
/// <para>The road is laid out in the ring's own coordinates: <c>s</c>, how far round the ring a place lies (blocks
/// along the ring's middle, from the west round through north, east and south), and <c>q</c>, how far out from spawn
/// (blocks), measured against where the level's edges cross each line out from spawn (<see cref="L8Crossing"/>,
/// smoothed a little), so the coordinates never fold back where the edges' warp does. Two long roads run all the way
/// round, each a line of q against s: three tenths and seven tenths of the way across the ring, drawn together where
/// it narrows until they run as one (<see cref="L8Sep"/>). Each wanders across the level, from a slow drift and from
/// bends, one to each stretch of the ring about 520 blocks long (<see cref="L8Segment"/>), so it swings from side to
/// side as if it had to find its way round something; and on the inside of the bigger bends lies what it went round, a
/// rich mineral deposit (<see cref="L8Deposit"/>). Now and then a road splits round a deposit into two branches that
/// meet again a few hundred blocks on (a braid). Between the segments, now and then, a way runs off a road out to the
/// level's edge, through the wall into Level 7 or Level 9, or across between the two roads (an exit, wandering as a
/// line of s against q). Settlements sit where an exit meets a road, on the road, at the end of a short spur, or on a
/// braid beside its deposit. Everything else is cave: hundreds of blocks of it between the roads.</para>
///
/// <para>Each road, branch and exit is the zero of a smooth field (<see cref="L8Piece"/>); a cell samples the fields
/// every four blocks and a tile is on the road where its field, divided by the field's slope, is under a block and a
/// half from zero (the road three wide whatever its heading). What has to be in one place only (a lamp, a marker, a
/// settlement, a deposit) is worked out from the ring coordinates alone and found in the world along a line out from
/// spawn (<see cref="L8Ray"/>), so neighbouring cells always agree. A cell's road is planned once (<see cref="L8Plan"/>).</para>
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL8Net = 0x8C10;
    /// <summary>The road's lattice: the fields are sampled every this many blocks and interpolated between.</summary>
    private const int L8Step = 4;
    private const int L8Grid = MacroSize / L8Step + 1;
    /// <summary>About how long a stretch of the ring with one bend, one braid or none, and one place for an exit, is.</summary>
    private const double L8SegmentLength = 520;
    /// <summary>Half the road's width: a tile is on it within this many blocks of its middle line.</summary>
    private const double L8HalfWidth = 1.5;

    private sealed class L8Segment
    {
        /// <summary>Where the bend's apex, or the braid's middle, lies along the ring.</summary>
        public double Centre;
        /// <summary>Each road's bend here (blocks out from the ring's middle, before the ring's width scales it down) and its half-length.</summary>
        public readonly double[] Bend = new double[2], Half = new double[2];
        public readonly bool[] Braid = new bool[2];
        public readonly double[] BraidLength = new double[2], BraidWidth = new double[2], BraidSplit = new double[2];
        /// <summary>Road 0's braid where road 1 runs as one with it (road 1 is not drawn over the braid).</summary>
        public bool BraidSolo;
        /// <summary>Where the exits at the start of the segment leave the roads, and which there are.</summary>
        public double ExitAt;
        public bool ExitInner, ExitOuter, ExitBetween;
    }

    private sealed class L8Camp
    {
        public double X, Z;
        /// <summary>Where the spur to it leaves the road (Spur only).</summary>
        public double SX, SZ;
        public bool Spur;
    }

    private sealed class L8Deposit
    {
        public double X, Z, Radius;
        public int Kind;
    }

    private sealed class L8Network
    {
        public const int Steps = 4096;
        public readonly double[] Inner = new double[Steps + 1], Outer = new double[Steps + 1], Along = new double[Steps + 1];
        public double Perimeter, SegLen;
        public int Segments;
        public L8Segment[] Seg;
        /// <summary>Settlements and deposits, by the segment their position along the ring falls in.</summary>
        public List<L8Camp>[] Camps;
        public List<L8Deposit>[] Deposits;

        public double WrapS(double ds) => ds - Perimeter * Math.Round(ds / Perimeter);
        public double ModS(double s) { s %= Perimeter; return s < 0 ? s + Perimeter : s; }

        private static double Index(double theta)
        {
            theta = Math.IEEERemainder(theta, 2 * Math.PI);
            return (theta + Math.PI) / (2 * Math.PI) * Steps;
        }

        /// <summary>The ring's inner and outer edge (cells from spawn) in a direction.</summary>
        public (double Inner, double Outer) RingAt(double theta)
        {
            double t = Index(theta);
            int j = Math.Clamp((int)Math.Floor(t), 0, Steps - 1);
            double f = t - j;
            return (Inner[j] + (Inner[j + 1] - Inner[j]) * f, Outer[j] + (Outer[j + 1] - Outer[j]) * f);
        }

        public double AlongAt(double theta)
        {
            double t = Index(theta);
            int j = Math.Clamp((int)Math.Floor(t), 0, Steps - 1);
            return Along[j] + (Along[j + 1] - Along[j]) * (t - j);
        }

        public double ThetaOf(double s)
        {
            s = ModS(s);
            int lo = 0, hi = Steps;
            while (hi - lo > 1)
            {
                int mid = (lo + hi) / 2;
                if (Along[mid] <= s) lo = mid; else hi = mid;
            }
            double span = Along[lo + 1] - Along[lo];
            return -Math.PI + 2 * Math.PI * (lo + (span > 0 ? (s - Along[lo]) / span : 0)) / Steps;
        }
    }

    private readonly object l8NetLock = new();
    private L8Network l8Net;

    private L8Network L8Net
    {
        get
        {
            L8Network net = System.Threading.Volatile.Read(ref l8Net);
            if (net != null) return net;
            lock (l8NetLock)
            {
                net = l8Net ??= BuildL8Network();
            }
            return net;
        }
    }

    // ---------------- The ring's coordinates ----------------

    /// <summary>
    /// The warped distance from spawn the ring's edges are measured in (<see cref="RingDistance"/>), without its finest
    /// lumps, in cells, at a point given in cells.
    /// </summary>
    private double L8Warped(double mx, double mz)
    {
        double dx = mx - spawnMacroX, dz = mz - spawnMacroZ;
        return Math.Sqrt(dx * dx + dz * dz) * (1 + 0.08 * Fbm(mx / 30.0, mz / 30.0, SaltLevelBlob)) + 3.0 * Fbm(mx / 8.0, mz / 8.0, SaltLevelWarp);
    }

    /// <summary>
    /// How far from spawn (cells, plainly measured) a direction first crosses a warped distance, nearest where it would
    /// cross if nothing were warped; the plain distance itself where it never does nearby.
    /// </summary>
    private double L8Crossing(double theta, double edge)
    {
        double cx = Math.Cos(theta), cz = Math.Sin(theta);
        double F(double r) => L8Warped(spawnMacroX + cx * r, spawnMacroZ + cz * r) - edge;
        double best = double.NaN, lo = 0, hi = 0;
        double prevR = Math.Max(1, edge - 12), prev = F(prevR);
        for (double r = prevR + 1; r <= edge + 12; r += 1)
        {
            double f = F(r);
            if (prev < 0 != f < 0 && (double.IsNaN(best) || Math.Abs(r - edge) < Math.Abs(best - edge))) { best = r; lo = r - 1; hi = r; }
            prevR = r;
            prev = f;
        }
        if (double.IsNaN(best)) return edge;
        bool rising = F(lo) < 0;
        for (int it = 0; it < 12; it++)
        {
            double mid = (lo + hi) / 2;
            if (F(mid) < 0 == rising) lo = mid; else hi = mid;
        }
        return (lo + hi) / 2;
    }

    /// <summary>A point's ring coordinates (q, its plain distance from spawn; s) and the ring's inner edge and width there, in blocks.</summary>
    private (double Q, double S, double Inner, double Width) L8Base(L8Network net, double x, double z)
    {
        double dx = x - spawnMacroX * MacroSize, dz = z - spawnMacroZ * MacroSize, theta = Math.Atan2(dz, dx);
        var (inner, outer) = net.RingAt(theta);
        return (Math.Sqrt(dx * dx + dz * dz), net.AlongAt(theta), inner * MacroSize, (outer - inner) * MacroSize);
    }

    /// <summary>The point q blocks from spawn in a direction.</summary>
    private (double X, double Z) L8Ray(double theta, double q) =>
        (spawnMacroX * MacroSize + q * Math.Cos(theta), spawnMacroZ * MacroSize + q * Math.Sin(theta));

    // ---------------- The long roads ----------------

    /// <summary>
    /// How far apart the two long roads' courses run (blocks), by the ring's width: three tenths and seven tenths of
    /// the way across, drawn together where the ring is narrow until they run as one.
    /// </summary>
    private static double L8Sep(double width) => Math.Clamp(0.8 * (width - 250), 0, 0.4 * width);

    /// <summary>
    /// How far a road may stray from its course toward the level's edge (blocks): a fifth of the ring's width, but never
    /// nearer the edge than an eighth of the way across and 30 more.
    /// </summary>
    private static double L8Room(double width, double sep) => Math.Max(0, Math.Min(0.2 * width + 10, 0.38 * width - 30 - sep / 2));

    /// <summary>How much of a bend's full size a road has room for.</summary>
    private static double L8BendScale(double room) => Math.Clamp(room / 110, 0, 1);

    /// <summary>
    /// How far a long road would stray from its course (blocks, outward): its bends and a slow drift, which wide
    /// stretches of the ring give more swing (eased off by <see cref="L8Centres"/>).
    /// </summary>
    private double L8Meander(L8Network net, int road, double s, double room)
    {
        s = net.ModS(s);
        double len = net.SegLen;
        int k = (int)Math.Floor(s / len);
        double sum = 0;
        for (int kk = k - 1; kk <= k + 1; kk++)
        {
            L8Segment seg = net.Seg[Hashing.Mod(kk, net.Segments)];
            double centre = kk * len + (seg.Centre - Hashing.Mod(kk, net.Segments) * len);
            double t = (s - centre) / seg.Half[road];
            if (Math.Abs(t) < 1)
            {
                double c = Math.Cos(Math.PI * t / 2);
                sum += seg.Bend[road] * c * c;
            }
        }
        // (round a circle in the noise, so the drift closes on itself round the ring)
        double a = 2 * Math.PI * s / net.Perimeter, radius = net.Perimeter / (2 * Math.PI * 1700);
        double drift = Math.Clamp(room, 0, 200) * Noise(radius * Math.Cos(a) + 1000.5 * road, radius * Math.Sin(a), SaltL8Net + 1);
        return sum * L8BendScale(room) + drift;
    }

    /// <summary>How far into its braid a position along the ring is (0 outside, 1 in the middle), and the braid's segment.</summary>
    private static double L8BraidOmega(L8Network net, int road, int k, double s)
    {
        L8Segment seg = net.Seg[k];
        if (!seg.Braid[road]) return 0;
        double t = net.WrapS(s - seg.Centre) / seg.BraidLength[road] + 0.5;
        if (t <= 0 || t >= 1) return 0;
        double sn = Math.Sin(Math.PI * t);
        return sn * sn;
    }

    private static int L8SegmentOf(L8Network net, double s) => Math.Min((int)(net.ModS(s) / net.SegLen), net.Segments - 1);

    /// <summary>Eases a road's swing off smoothly so it never goes further than lo one way and hi the other.</summary>
    private static double L8Ease(double x, double lo, double hi) =>
        x < 0 ? (lo < 1 ? 0 : lo * Math.Tanh(x / lo)) : (hi < 1 ? 0 : hi * Math.Tanh(x / hi));

    /// <summary>
    /// The two long roads' middle lines (q) at a position along the ring, and whether the second is drawn there. Each
    /// swings toward its edge of the level as far as its room, and toward the middle just past it, so now and then the
    /// two meet and part again.
    /// </summary>
    private void L8Centres(L8Network net, double s, double inner, double width, out double q0, out double q1, out bool draw1)
    {
        double sep = L8Sep(width), room = L8Room(width, sep), f = Math.Clamp(sep / 150, 0, 1), middle = Math.Max(room, sep / 2 + 15);
        double m0 = L8Ease(L8Meander(net, 0, s, room), room, middle), m1 = L8Ease(L8Meander(net, 1, s, room), middle, room);
        q0 = inner + width / 2 - sep / 2 + m0;
        q1 = inner + width / 2 + sep / 2 + m0 + f * (m1 - m0);
        int k = L8SegmentOf(net, s);
        draw1 = sep >= 0.5 && !(net.Seg[k].BraidSolo && L8BraidOmega(net, 0, k, s) > 0);
    }

    private (double Inner, double Width) L8RingAtS(L8Network net, double s)
    {
        var (inner, outer) = net.RingAt(net.ThetaOf(s));
        return (inner * MacroSize, (outer - inner) * MacroSize);
    }

    // ---------------- The pieces of road ----------------

    private enum L8Kind : byte { Main, Plus, Minus, ExitInner, ExitOuter, ExitBetween }

    /// <summary>A road, one branch of a braid, or an exit: each the zero of a field (see <see cref="L8Field"/>).</summary>
    private readonly record struct L8Piece(L8Kind Kind, int Road, int K)
    {
        public bool IsExit => Kind is L8Kind.ExitInner or L8Kind.ExitOuter or L8Kind.ExitBetween;
        /// <summary>A number for the piece, for the noise along it.</summary>
        public int Line => IsExit ? 7 + 3 * (K % 60) : Kind == L8Kind.Main ? Road : 2 + 2 * Road + (Kind == L8Kind.Plus ? 0 : 1);
    }

    /// <summary>How far an exit wanders round the ring as it goes out (blocks, by q).</summary>
    private double L8Wobble(int k, double q) =>
        28 * Noise(q / 140.0, k * 8 + 0.5, SaltL8Net + 2) + 9 * Noise(q / 60.0, k * 8 + 2.5, SaltL8Net + 3);

    /// <summary>A braid branch's offset from its road's middle line (blocks of q).</summary>
    private static double L8BranchOffset(L8Network net, L8Piece p, double s)
    {
        L8Segment seg = net.Seg[p.K];
        double omega = L8BraidOmega(net, p.Road, p.K, s), a = seg.BraidSplit[p.Road], h = seg.BraidWidth[p.Road];
        return p.Kind == L8Kind.Plus ? a * h * omega : -(1 - a) * h * omega;
    }

    /// <summary>A piece's field at a point with ring coordinates (q, s), given the long roads' middle lines there.</summary>
    private double L8Field(L8Network net, L8Piece p, double q, double s, double q0, double q1)
    {
        if (p.IsExit) return net.WrapS(s - net.Seg[p.K].ExitAt) + L8Wobble(p.K, q);
        double c = p.Road == 0 ? q0 : q1;
        if (p.Kind != L8Kind.Main) c += L8BranchOffset(net, p, s);
        return q - c;
    }

    private double L8FieldAt(L8Network net, L8Piece p, double x, double z)
    {
        var (q, s, inner, width) = L8Base(net, x, z);
        L8Centres(net, s, inner, width, out double q0, out double q1, out _);
        return L8Field(net, p, q, s, q0, q1);
    }

    /// <summary>The unit normal of a piece's field at a point (which way its field rises).</summary>
    private (double X, double Z) L8Normal(L8Network net, L8Piece p, double x, double z)
    {
        double fx = L8FieldAt(net, p, x + 0.5, z) - L8FieldAt(net, p, x - 0.5, z);
        double fz = L8FieldAt(net, p, x, z + 0.5) - L8FieldAt(net, p, x, z - 0.5);
        double g = Math.Sqrt(fx * fx + fz * fz);
        return g < 1e-9 ? (1, 0) : (fx / g, fz / g);
    }

    /// <summary>The point on a long road or braid branch at a position along the ring, or null where it is not drawn.</summary>
    private (double X, double Z)? L8RoadPoint(L8Network net, L8Piece p, double s)
    {
        var (inner, width) = L8RingAtS(net, s);
        L8Centres(net, s, inner, width, out double q0, out double q1, out bool draw1);
        int k = L8SegmentOf(net, s);
        double omega = L8BraidOmega(net, p.Road, p.Kind == L8Kind.Main ? k : p.K, s);
        if (p.Road == 1 && !draw1) return null;
        if (p.Kind == L8Kind.Main && omega > 0) return null;
        if (p.Kind != L8Kind.Main && net.Seg[p.K].BraidWidth[p.Road] * omega < 6) return null;
        double q = p.Road == 0 ? q0 : q1;
        if (p.Kind != L8Kind.Main) q += L8BranchOffset(net, p, s);
        return L8Ray(net.ThetaOf(s), q);
    }

    /// <summary>The point on an exit at a distance q out from spawn.</summary>
    private (double X, double Z) L8ExitPoint(L8Network net, int k, double q) =>
        L8Ray(net.ThetaOf(net.Seg[k].ExitAt - L8Wobble(k, q)), q);

    // ---------------- The network, once per world ----------------

    private L8Network BuildL8Network()
    {
        var net = new L8Network();
        const int steps = L8Network.Steps;
        // Where the level's edges lie in each direction, measured plainly from spawn (so the road's coordinates never
        // fold back on themselves where the edges' warp does), smoothed over a few cells either way
        var rawIn = new double[steps];
        var rawOut = new double[steps];
        for (int j = 0; j < steps; j++)
        {
            double theta = -Math.PI + 2 * Math.PI * j / steps;
            var (inner, outer) = RingEdges(8, theta);
            rawIn[j] = L8Crossing(theta, inner);
            rawOut[j] = L8Crossing(theta, outer);
        }
        const int window = 8;
        for (int j = 0; j < steps; j++)
        {
            double sumIn = 0, sumOut = 0;
            for (int o = -window; o <= window; o++)
            {
                sumIn += rawIn[Hashing.Mod(j + o, steps)];
                sumOut += rawOut[Hashing.Mod(j + o, steps)];
            }
            net.Inner[j] = sumIn / (2 * window + 1);
            net.Outer[j] = Math.Max(net.Inner[j] + 1, sumOut / (2 * window + 1));
        }
        net.Inner[steps] = net.Inner[0];
        net.Outer[steps] = net.Outer[0];
        double dTheta = 2 * Math.PI / steps;
        for (int j = 0; j < steps; j++)
            net.Along[j + 1] = net.Along[j] + 0.25 * (net.Inner[j] + net.Outer[j] + net.Inner[j + 1] + net.Outer[j + 1]) * MacroSize * dTheta;
        net.Perimeter = net.Along[steps];
        net.Segments = Math.Max(8, (int)Math.Round(net.Perimeter / L8SegmentLength));
        net.SegLen = net.Perimeter / net.Segments;
        net.Seg = new L8Segment[net.Segments];
        double len = net.SegLen;

        // Bends, braids and exits, from hashes
        for (int k = 0; k < net.Segments; k++)
        {
            var seg = net.Seg[k] = new L8Segment();
            ulong h = Hashing.Hash(seed, k, 0, SaltL8Net);
            seg.Centre = (k + 0.5 + 0.35 * (Hashing.Unit(h) - 0.5)) * len;
            var (inner, width) = L8RingAtS(net, seg.Centre);
            double sep = L8Sep(width), room = L8Room(width, sep);
            for (int road = 0; road < 2; road++)
            {
                ulong r = Hashing.Hash(seed, k, road + 1, SaltL8Net);
                double size = Hashing.Unit(Hashing.Mix(r + 1));
                seg.Bend[road] = (Hashing.Unit(r) < 0.5 ? -1 : 1) * (20 + 90 * Math.Pow(size, 0.8));
                seg.Half[road] = (0.45 + 0.5 * Hashing.Unit(Hashing.Mix(r + 2))) * len;
                // A braid where there is room for one: road 0 alone where the roads run as one, either where they run apart
                bool fits = road == 0 ? sep < 0.5 || sep >= 150 : sep >= 150;
                if (fits && room >= 70 && Hashing.Unit(Hashing.Mix(r + 3)) < 0.22)
                {
                    seg.Braid[road] = true;
                    seg.Bend[road] = 0;
                    seg.BraidLength[road] = (0.45 + 0.15 * Hashing.Unit(Hashing.Mix(r + 4))) * len;
                    seg.BraidWidth[road] = L8BendScale(room) * (46 + 40 * Hashing.Unit(Hashing.Mix(r + 5)));
                    seg.BraidSplit[road] = 0.3 + 0.4 * Hashing.Unit(Hashing.Mix(r + 6));
                    if (road == 0 && sep < 0.5) seg.BraidSolo = true;
                }
            }
            ulong e = Hashing.Hash(seed, k, 3, SaltL8Net);
            seg.ExitAt = (k + 0.12 * (Hashing.Unit(e) - 0.5)) * len;
            seg.ExitInner = Hashing.Unit(Hashing.Mix(e + 1)) < 0.45;
            seg.ExitOuter = Hashing.Unit(Hashing.Mix(e + 2)) < 0.5;
            var (_, wE) = L8RingAtS(net, seg.ExitAt);
            seg.ExitBetween = L8Sep(wE) >= 40 && Hashing.Unit(Hashing.Mix(e + 3)) < 0.35;
        }

        net.Camps = new List<L8Camp>[net.Segments];
        net.Deposits = new List<L8Deposit>[net.Segments];
        for (int k = 0; k < net.Segments; k++) { net.Camps[k] = new List<L8Camp>(); net.Deposits[k] = new List<L8Deposit>(); }
        for (int k = 0; k < net.Segments; k++) PlaceL8Camps(net, k);
        for (int k = 0; k < net.Segments; k++) PlaceL8Deposits(net, k);
        return net;
    }

    /// <summary>
    /// The settlements of a segment: where an exit at its start meets a road, or else now and then on a road there or
    /// at the end of a short spur off it toward the middle of the ring; now and then at a bend's apex, and on a braid,
    /// beside the deposit the road goes round.
    /// </summary>
    private void PlaceL8Camps(L8Network net, int k)
    {
        L8Segment seg = net.Seg[k];
        ulong h = Hashing.Hash(seed, k, 4, SaltL8Net);
        double roll = Hashing.Unit(h);
        double s = seg.ExitAt;
        var (inner, width) = L8RingAtS(net, s);
        L8Centres(net, s, inner, width, out double q0, out double q1, out bool draw1);
        int road = draw1 && Hashing.Unit(Hashing.Mix(h + 1)) < 0.5 ? 1 : 0;
        bool exits = seg.ExitInner || seg.ExitOuter || seg.ExitBetween;
        void Add(L8Camp camp, double along) => net.Camps[L8SegmentOf(net, along)].Add(camp);
        if (exits && roll < 0.6)
        {
            // Where the exit meets the road (the exit's own field is zero there)
            if (draw1 && !seg.ExitBetween) road = seg.ExitInner == (q0 < q1) ? 0 : 1;
            double at = s;
            for (int it = 0; it < 6; it++)
            {
                var (ri, rw) = L8RingAtS(net, at);
                L8Centres(net, at, ri, rw, out double c0, out double c1, out _);
                at = seg.ExitAt - L8Wobble(k, road == 0 ? c0 : c1);
            }
            if (L8RoadPoint(net, new L8Piece(L8Kind.Main, road, 0), at) is { } p) Add(new L8Camp { X = p.X, Z = p.Z }, at);
        }
        else if (!exits && roll < 0.45 && L8RoadPoint(net, new L8Piece(L8Kind.Main, road, 0), s) is { } p)
        {
            if (Hashing.Unit(Hashing.Mix(h + 2)) < 0.5) Add(new L8Camp { X = p.X, Z = p.Z }, s);
            else
            {
                // A spur toward the middle of the ring (the field rises outward)
                var piece = new L8Piece(L8Kind.Main, road, 0);
                var (nx, nz) = L8Normal(net, piece, p.X, p.Z);
                double side = (road == 0 ? q0 : q1) < inner + width / 2 ? 1 : -1;
                double length = 14 + 10 * Hashing.Unit(Hashing.Mix(h + 3));
                Add(new L8Camp { Spur = true, SX = p.X, SZ = p.Z, X = p.X + side * length * nx, Z = p.Z + side * length * nz }, s);
            }
        }
        for (int r = 0; r < 2; r++)
        {
            // At a bend's apex, beside the deposit it goes round
            if (!seg.Braid[r] && Hashing.Unit(Hashing.Mix(h + 30 + (ulong)r)) < 0.3
                && L8RoadPoint(net, new L8Piece(L8Kind.Main, r, 0), seg.Centre) is { } apex)
                Add(new L8Camp { X = apex.X, Z = apex.Z }, seg.Centre);
            if (!seg.Braid[r] || Hashing.Unit(Hashing.Mix(h + 10 + (ulong)r)) >= 0.4) continue;
            var branch = new L8Piece(Hashing.Unit(Hashing.Mix(h + 20 + (ulong)r)) < 0.5 ? L8Kind.Plus : L8Kind.Minus, r, k);
            if (L8RoadPoint(net, branch, seg.Centre) is { } p) Add(new L8Camp { X = p.X, Z = p.Z }, seg.Centre);
        }
    }

    /// <summary>
    /// The deposits of a segment: on the inside of each road's bend, if it is a big one, touching the road at its apex,
    /// and in the middle of a braid; each shrunk until no road comes within a few blocks of it, and kept off the
    /// level's edges.
    /// </summary>
    private void PlaceL8Deposits(L8Network net, int k)
    {
        L8Segment seg = net.Seg[k];
        double s = seg.Centre;
        var (inner, width) = L8RingAtS(net, s);
        L8Centres(net, s, inner, width, out double q0, out double q1, out bool draw1);
        double sep = L8Sep(width), scale = L8BendScale(L8Room(width, sep));
        for (int road = 0; road < 2; road++)
        {
            if (road == 1 && (!draw1 || sep < 150)) continue;
            double centreQ, radius;
            double q = road == 0 ? q0 : q1;
            if (seg.Braid[road])
            {
                double hw = seg.BraidWidth[road], a = seg.BraidSplit[road];
                centreQ = q + (2 * a - 1) * hw / 2;
                radius = hw / 2 - 4;
            }
            else
            {
                double bend = seg.Bend[road] * scale;
                if (Math.Abs(bend) < 38) continue;
                radius = Math.Clamp(0.45 * Math.Abs(bend), 14, 36);
                centreQ = q - Math.Sign(bend) * (radius + 3.5);
            }
            // Shrunk clear of every road near it, and of the level's edges
            for (int i = -6; i <= 6; i++)
            {
                double ds = i * 8, at = s + ds;
                var (ri, rw) = L8RingAtS(net, at);
                L8Centres(net, at, ri, rw, out double c0, out double c1, out bool d1);
                int ka = L8SegmentOf(net, at);
                foreach (var piece in new[] { new L8Piece(L8Kind.Main, 0, ka), new L8Piece(L8Kind.Plus, 0, ka), new L8Piece(L8Kind.Minus, 0, ka),
                             new L8Piece(L8Kind.Main, 1, ka), new L8Piece(L8Kind.Plus, 1, ka), new L8Piece(L8Kind.Minus, 1, ka) })
                {
                    if (piece.Road == 1 && !d1) continue;
                    double omega = L8BraidOmega(net, piece.Road, ka, at);
                    if (piece.Kind == L8Kind.Main ? omega > 0 : omega <= 0) continue;
                    double pq = (piece.Road == 0 ? c0 : c1) + (piece.Kind == L8Kind.Main ? 0 : L8BranchOffset(net, piece, at));
                    radius = Math.Min(radius, Math.Sqrt(ds * ds + (pq - centreQ) * (pq - centreQ)) - 3);
                }
                if (i == 0) radius = Math.Min(radius, Math.Min(centreQ - ri - 24, ri + rw - 24 - centreQ));
            }
            if (radius < 10) continue;
            var (x, z) = L8Ray(net.ThetaOf(s), centreQ);
            int kind = (int)(Hashing.Mix(Hashing.Hash(seed, k, road + 6, SaltL8Net)) % 8);
            net.Deposits[k].Add(new L8Deposit { X = x, Z = z, Radius = radius, Kind = kind });
        }
    }

    // ---------------- A cell's road ----------------

    private sealed class L8Plan
    {
        public const byte Road = 1, Camp = 2, Junction = 4;
        public readonly byte[] Flags = new byte[MacroSize * MacroSize];
        /// <summary>Which third of the road a tile is in (0 and 2 the sides), and the way to its middle.</summary>
        public readonly byte[] Across = new byte[MacroSize * MacroSize], PierIn = new byte[MacroSize * MacroSize];
        public readonly int[] Along = new int[MacroSize * MacroSize];
        public readonly byte[] Line = new byte[MacroSize * MacroSize];
        /// <summary>A settlement's dome over the tile; blocks to the nearest road (at most 255).</summary>
        public readonly byte[] Dome = new byte[MacroSize * MacroSize], Dist = new byte[MacroSize * MacroSize];
        /// <summary>A lamp or marker, and the way it faces.</summary>
        public readonly byte[] Prop = new byte[MacroSize * MacroSize], PropPier = new byte[MacroSize * MacroSize];
        /// <summary>A deposit under the tile: its kind times 256 plus how near its heart (1-255), or 0.</summary>
        public readonly ushort[] Deposit = new ushort[MacroSize * MacroSize];
        /// <summary>The piece a road tile is nearest the middle of (an index into the plan's own list), or -1.</summary>
        public readonly sbyte[] Piece = new sbyte[MacroSize * MacroSize];
    }

    private PlanCache<L8Plan> l8Plans;

    private L8Plan L8PlanAt(int gx, int gz) =>
        (l8Plans ??= new PlanCache<L8Plan>(256, PlanL8Cell)).Get(MacroOf(gx), MacroOf(gz));

    private static ArchPier L8Toward(double vx, double vz) =>
        Math.Abs(vx) >= Math.Abs(vz) ? (vx > 0 ? ArchPier.East : ArchPier.West) : (vz > 0 ? ArchPier.South : ArchPier.North);

    private L8Plan PlanL8Cell(int mx, int mz)
    {
        L8Network net = L8Net;
        var plan = new L8Plan();
        Array.Fill(plan.Piece, (sbyte)-1);
        Array.Fill(plan.Dist, (byte)255);
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        const int points = L8Grid * L8Grid;

        // The ring's coordinates every four blocks (s taken on round the ring from the cell's middle, never across the seam)
        var Q = new double[points]; var S = new double[points]; var In = new double[points]; var Wd = new double[points];
        for (int j = 0; j < L8Grid; j++)
            for (int i = 0; i < L8Grid; i++)
                (Q[j * L8Grid + i], S[j * L8Grid + i], In[j * L8Grid + i], Wd[j * L8Grid + i]) = L8Base(net, x0 + i * L8Step, z0 + j * L8Step);
        double sRef = S[points / 2], sMin = double.MaxValue, sMax = double.MinValue;
        for (int n = 0; n < points; n++)
        {
            S[n] = sRef + net.WrapS(S[n] - sRef);
            sMin = Math.Min(sMin, S[n]);
            sMax = Math.Max(sMax, S[n]);
        }

        // The pieces that can reach the cell
        var pieces = new List<L8Piece> { new(L8Kind.Main, 0, 0), new(L8Kind.Main, 1, 0) };
        double sMid = (sMin + sMax) / 2, sHalf = (sMax - sMin) / 2;
        int kLo = (int)Math.Floor((sMin - 2 * L8SegmentLength) / net.SegLen), kHi = (int)Math.Floor((sMax + 2 * L8SegmentLength) / net.SegLen);
        var segs = new List<int>();
        for (int kk = kLo; kk <= kHi; kk++)
        {
            int k = Hashing.Mod(kk, net.Segments);
            if (segs.Contains(k)) continue;
            segs.Add(k);
            L8Segment seg = net.Seg[k];
            for (int road = 0; road < 2; road++)
                if (seg.Braid[road] && Math.Abs(net.WrapS(seg.Centre - sMid)) < seg.BraidLength[road] / 2 + sHalf + 4)
                {
                    pieces.Add(new L8Piece(L8Kind.Plus, road, k));
                    pieces.Add(new L8Piece(L8Kind.Minus, road, k));
                }
            if (Math.Abs(net.WrapS(seg.ExitAt - sMid)) < sHalf + 48)
            {
                if (seg.ExitInner) pieces.Add(new L8Piece(L8Kind.ExitInner, 0, k));
                if (seg.ExitOuter) pieces.Add(new L8Piece(L8Kind.ExitOuter, 0, k));
                if (seg.ExitBetween) pieces.Add(new L8Piece(L8Kind.ExitBetween, 0, k));
            }
        }
        int count = pieces.Count;
        var F = new double[count * points];
        for (int n = 0; n < points; n++)
        {
            L8Centres(net, S[n], In[n], Wd[n], out double q0, out double q1, out _);
            for (int p = 0; p < count; p++) F[p * points + n] = L8Field(net, pieces[p], Q[n], S[n], q0, q1);
        }

        // Settlements and deposits near the cell
        var camps = new List<L8Camp>();
        var deposits = new List<L8Deposit>();
        foreach (int k in segs)
        {
            foreach (L8Camp c in net.Camps[k])
                if (c.X > x0 - 40 && c.X < x0 + MacroSize + 40 && c.Z > z0 - 40 && c.Z < z0 + MacroSize + 40) camps.Add(c);
            foreach (L8Deposit dep in net.Deposits[k])
                if (dep.X + dep.Radius > x0 && dep.X - dep.Radius < x0 + MacroSize && dep.Z + dep.Radius > z0 && dep.Z - dep.Radius < z0 + MacroSize) deposits.Add(dep);
        }

        var d = new double[count];
        var act = new bool[count];
        var gxs = new double[count];
        var gzs = new double[count];
        var tileS = new double[MacroSize * MacroSize];
        var tileQ = new double[MacroSize * MacroSize];
        for (int lz = 0; lz < MacroSize; lz++)
        {
            double v = (lz + 0.5) / L8Step;
            int j0 = (int)v;
            double fz = v - j0;
            for (int lx = 0; lx < MacroSize; lx++)
            {
                double u = (lx + 0.5) / L8Step;
                int i0 = (int)u, n00 = j0 * L8Grid + i0, n10 = n00 + 1, n01 = n00 + L8Grid, n11 = n01 + 1;
                double fx = u - i0;
                double Lerp(double[] a, int o) =>
                    (a[o + n00] * (1 - fx) + a[o + n10] * fx) * (1 - fz) + (a[o + n01] * (1 - fx) + a[o + n11] * fx) * fz;
                int index = TileIndex(lx, lz);
                double s = Lerp(S, 0), q = Lerp(Q, 0), w = Lerp(Wd, 0);
                tileS[index] = s;
                tileQ[index] = q;
                int k = L8SegmentOf(net, s);
                bool draw1 = L8Sep(w) >= 0.5 && !(net.Seg[k].BraidSolo && L8BraidOmega(net, 0, k, s) > 0);
                for (int p = 0; p < count; p++)
                {
                    int o = p * points;
                    double f = Lerp(F, o);
                    double dx = ((F[o + n10] - F[o + n00]) * (1 - fz) + (F[o + n11] - F[o + n01]) * fz) / L8Step;
                    double dz = ((F[o + n01] - F[o + n00]) * (1 - fx) + (F[o + n11] - F[o + n10]) * fx) / L8Step;
                    double g = Math.Max(Math.Sqrt(dx * dx + dz * dz), 1e-6);
                    d[p] = f / g;
                    gxs[p] = dx;
                    gzs[p] = dz;
                }
                double d0 = d[0], d1 = draw1 ? d[1] : d[0];
                double hi = Math.Max(d0, d1), lo = Math.Min(d0, d1);
                int on = 0, best = -1;
                double bestAbs = double.MaxValue, dist = 255;
                for (int p = 0; p < count; p++)
                {
                    L8Piece piece = pieces[p];
                    bool active = piece.Kind switch
                    {
                        L8Kind.Main => (piece.Road == 0 || draw1) && L8BraidOmega(net, piece.Road, k, s) <= 0,
                        L8Kind.Plus or L8Kind.Minus => L8BraidOmega(net, piece.Road, piece.K, s) > 0,
                        L8Kind.ExitInner => hi <= 1,
                        L8Kind.ExitOuter => lo >= -1,
                        _ => draw1 && hi >= -1 && lo <= 1,
                    };
                    act[p] = active;
                    if (!active) continue;
                    double a = Math.Abs(d[p]);
                    dist = Math.Min(dist, Math.Max(0, a - L8HalfWidth));
                    if (a >= L8HalfWidth) continue;
                    on++;
                    if (a < bestAbs) { bestAbs = a; best = p; }
                }
                // Where two roads (or a braid's branches) run so close that only a sliver of rock would stand between
                // them, they run as one
                if (on < 2)
                    for (int p = 0; p < count && on < 2; p++)
                        for (int r = p + 1; r < count; r++)
                        {
                            if (!act[p] || !act[r] || pieces[p].IsExit || pieces[r].IsExit || d[p] * d[r] >= 0) continue;
                            if (Math.Abs(d[p]) + Math.Abs(d[r]) >= 6) continue;
                            on = 2;
                            best = Math.Abs(d[p]) <= Math.Abs(d[r]) ? p : r;
                            dist = 0;
                            break;
                        }
                if (best >= 0)
                {
                    L8Piece piece = pieces[best];
                    double dp = d[best];
                    plan.Flags[index] |= L8Plan.Road;
                    plan.Piece[index] = (sbyte)best;
                    plan.Across[index] = (byte)(dp < -0.5 ? 0 : dp <= 0.5 ? 1 : 2);
                    plan.PierIn[index] = (byte)L8Toward(-Math.Sign(dp) * gxs[best], -Math.Sign(dp) * gzs[best]);
                    plan.Along[index] = (int)Math.Floor(piece.IsExit ? q : net.ModS(s));
                    plan.Line[index] = (byte)piece.Line;
                    if (on > 1) plan.Flags[index] |= L8Plan.Junction;
                }

                // Spurs and settlements
                double gx = x0 + lx + 0.5, gz = z0 + lz + 0.5;
                foreach (L8Camp c in camps)
                {
                    double cx = gx - c.X, cz = gz - c.Z, r = Math.Sqrt(cx * cx + cz * cz);
                    if (r < CampRadius)
                    {
                        plan.Flags[index] |= L8Plan.Camp;
                        plan.Dome[index] = (byte)Math.Max(plan.Dome[index], 4 + (int)Math.Round(5 * Math.Sqrt(Math.Max(0, 1 - r * r / (CampRadius * CampRadius)))));
                    }
                    dist = Math.Min(dist, Math.Max(0, r - CampRadius));
                    if (!c.Spur) continue;
                    double ax = c.X - c.SX, az = c.Z - c.SZ, len = Math.Sqrt(ax * ax + az * az);
                    double along = ((gx - c.SX) * ax + (gz - c.SZ) * az) / len;
                    if (along < 0 || along > len) continue;
                    double across = ((gx - c.SX) * az - (gz - c.SZ) * ax) / len;
                    dist = Math.Min(dist, Math.Max(0, Math.Abs(across) - L8HalfWidth));
                    if (Math.Abs(across) >= L8HalfWidth) continue;
                    if ((plan.Flags[index] & L8Plan.Road) != 0) { plan.Flags[index] |= L8Plan.Junction; continue; }
                    plan.Flags[index] |= L8Plan.Road;
                    plan.Across[index] = (byte)(across < -0.5 ? 0 : across <= 0.5 ? 1 : 2);
                    plan.PierIn[index] = (byte)L8Toward(-Math.Sign(across) * az, Math.Sign(across) * ax);
                    plan.Along[index] = (int)along;
                    plan.Line[index] = 250;
                }
                plan.Dist[index] = (byte)Math.Min(255, (int)Math.Round(dist));

                foreach (L8Deposit dep in deposits)
                {
                    double ex = gx - dep.X, ez = gz - dep.Z, r = Math.Sqrt(ex * ex + ez * ez);
                    if (r >= dep.Radius) continue;
                    int strength = Math.Clamp((int)Math.Round(255 * (1 - r / dep.Radius)), 1, 255);
                    if (strength > (plan.Deposit[index] & 255)) plan.Deposit[index] = (ushort)(dep.Kind << 8 | strength);
                }
            }
        }

        PlaceL8Lights(net, plan, pieces, x0, z0, tileS, tileQ);
        return plan;
    }

    /// <summary>How far out to the side of the road's middle a lamp or marker is looked for, in turn.</summary>
    private static readonly double[] L8LightReach = { 1.05, 0.8, 1.3 };

    /// <summary>
    /// Lamps every twelve blocks along each road, branch and exit on one side, M.E.G. markers every twenty-four on the
    /// other, each found from where it lies along the road (so only one tile, in one cell, ever holds it), facing the road.
    /// </summary>
    private void PlaceL8Lights(L8Network net, L8Plan plan, List<L8Piece> pieces, int x0, int z0, double[] tileS, double[] tileQ)
    {
        for (int p = 0; p < pieces.Count; p++)
        {
            L8Piece piece = pieces[p];
            double lo = double.MaxValue, hi = double.MinValue;
            for (int i = 0; i < plan.Piece.Length; i++)
            {
                if (plan.Piece[i] != p) continue;
                double a = piece.IsExit ? tileQ[i] : tileS[i];
                lo = Math.Min(lo, a);
                hi = Math.Max(hi, a);
            }
            if (lo > hi) continue;
            for (int lamp = 0; lamp < 2; lamp++)
            {
                double spacing = lamp == 0 ? 12 : 24, offset = lamp == 0 ? 6 : 0, side = lamp == 0 ? 1 : -1;
                for (double at = Math.Ceiling((lo - 4 - offset) / spacing) * spacing + offset; at <= hi + 4; at += spacing)
                {
                    (double X, double Z)? point = piece.IsExit ? L8ExitPoint(net, piece.K, at) : L8RoadPoint(net, piece, at);
                    if (point is not { } pt) continue;
                    var (nx, nz) = L8Normal(net, piece, pt.X, pt.Z);
                    // The tile a block out to the side, or a little nearer or further where that tile's middle is not
                    // well inside the road's side third (worked out from the road alone, so every cell picks the same)
                    int tx = 0, tz = 0;
                    foreach (double reach in L8LightReach)
                    {
                        tx = (int)Math.Floor(pt.X + side * reach * nx);
                        tz = (int)Math.Floor(pt.Z + side * reach * nz);
                        double f = L8FieldAt(net, piece, tx + 0.5, tz + 0.5);
                        double fx = L8FieldAt(net, piece, tx + 1, tz + 0.5) - L8FieldAt(net, piece, tx, tz + 0.5);
                        double fz = L8FieldAt(net, piece, tx + 0.5, tz + 1) - L8FieldAt(net, piece, tx + 0.5, tz);
                        double across = side * f / Math.Max(Math.Sqrt(fx * fx + fz * fz), 1e-6);
                        if (across > 0.6 && across < 1.4) break;
                    }
                    tx -= x0;
                    tz -= z0;
                    if (tx < 0 || tz < 0 || tx >= MacroSize || tz >= MacroSize) continue;
                    int index = TileIndex(tx, tz);
                    if (plan.Piece[index] != p || (plan.Flags[index] & L8Plan.Junction) != 0 || plan.Prop[index] != 0) continue;
                    if (plan.Across[index] != (side > 0 ? 2 : 0)) continue;
                    plan.Prop[index] = lamp == 0 ? Props.RoadLamp : Props.MegMarker;
                    plan.PropPier[index] = plan.PierIn[index];
                }
            }
        }
    }

    // ---------------- What the rest of the layout asks ----------------

    /// <summary>
    /// Level 8's rich deposits, from layout version 9: 0 where there is none, else the deposit's kind (0-7) times 256
    /// plus how near its heart the column is (1 at the rim to 255 at the heart). Only in Level 8.
    /// </summary>
    public int L8DepositAt(int gx, int gz)
    {
        if (Version < 9 || LevelAt(MacroOf(gx), MacroOf(gz)) != 8) return 0;
        L8Plan plan = L8PlanAt(gx, gz);
        return plan.Deposit[TileIndex(gx - MacroOf(gx) * MacroSize, gz - MacroOf(gz) * MacroSize)];
    }

    private static int L8Index(int gx, int gz) => TileIndex(gx - MacroOf(gx) * MacroSize, gz - MacroOf(gz) * MacroSize);

    private bool IsL8RoadV9(int gx, int gz) => (L8PlanAt(gx, gz).Flags[L8Index(gx, gz)] & L8Plan.Road) != 0;

    private bool IsL8CampV9(int gx, int gz) => (L8PlanAt(gx, gz).Flags[L8Index(gx, gz)] & L8Plan.Camp) != 0;

    /// <summary>Where someone arriving in Level 8 is looked for, from layout version 9: on one of the long roads in that direction.</summary>
    private (int Mx, int Mz) L8ArrivalCell(double angle, ulong h)
    {
        L8Network net = L8Net;
        double s = net.AlongAt(angle);
        var (inner, width) = L8RingAtS(net, s);
        L8Centres(net, s, inner, width, out _, out _, out bool draw1);
        var road = new L8Piece(L8Kind.Main, draw1 && (Hashing.Mix(h + 7) & 1) == 1 ? 1 : 0, 0);
        var point = L8RoadPoint(net, road, s) ?? L8RoadPoint(net, new L8Piece(L8Kind.Plus, road.Road, L8SegmentOf(net, s)), s)
            ?? L8RoadPoint(net, new L8Piece(L8Kind.Main, 0, 0), s) ?? (0, 0);
        return (MacroOf((int)Math.Floor(point.X)), MacroOf((int)Math.Floor(point.Z)));
    }

    /// <summary>One of Level 8's tiles, from layout version 9, laid out from its cell's road plan.</summary>
    private void BuildLevel8Network(Builder b, int mx, int mz)
    {
        L8Plan plan = L8PlanAt(mx * MacroSize, mz * MacroSize);
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz, i = TileIndex(lx, lz);
                if (t.Kind != TileKind.Floor) continue;
                bool road = (plan.Flags[i] & L8Plan.Road) != 0, camp = (plan.Flags[i] & L8Plan.Camp) != 0;
                if (!road && !camp)
                {
                    SetWall(ref t, WallPattern.Rock, BaseStyle.Plain);
                    continue;
                }
                t.Floor = FloorKind.Gravel;
                if (!road)
                {
                    t.Height = plan.Dome[i];
                    continue;
                }
                if (plan.Prop[i] != 0)
                {
                    t.Variant = plan.Prop[i];
                    t.Pier = (ArchPier)plan.PropPier[i];
                }
                int across = plan.Across[i];
                t.Height = camp ? plan.Dome[i] : L8Roof(plan, i, gx, gz);
                // Bioluminescent fungi in stretches along the foot of the road's walls, as in older worlds
                if (t.Variant == 0 && across != 1 && Noise(gx / 50.0, gz / 50.0, SaltL8Detail + 5) > 0.35)
                {
                    ulong fh = Hashing.Hash(seed, gx, gz, SaltL8Detail + 6);
                    ArchPier wall = (ArchPier)plan.PierIn[i] switch
                    {
                        ArchPier.North => ArchPier.South,
                        ArchPier.South => ArchPier.North,
                        ArchPier.East => ArchPier.West,
                        _ => ArchPier.East,
                    };
                    var (wx, wz) = Step(gx, gz, wall);
                    if (Hashing.Unit(fh) < 0.12 && !IsNinthRoad(wx, wz) && !IsCampClearing(wx, wz))
                    {
                        t.Variant = Hashing.Unit(fh >> 20) < 0.8 ? Props.GlowcapRed : Props.GlowcapMixed;
                        t.Stack = 1;
                        t.Pier = wall;
                    }
                }
            }
        }
    }

    /// <summary>The road's arch over a tile, as <see cref="RoadRoof"/> (five where two pieces of road meet).</summary>
    private byte L8Roof(L8Plan plan, int i, int gx, int gz)
    {
        if ((plan.Flags[i] & L8Plan.Junction) != 0) return 5;
        int across = plan.Across[i], along = plan.Along[i], line = plan.Line[i];
        double n = Noise(along / 7.0, line * 5 + 0.5, SaltL8Road + 3);
        ulong h = Hashing.Hash(seed, gx, gz, SaltL8Road + 4);
        if (across == 1) return (byte)(n > 0.45 ? 6 : n > 0.15 ? 5 : 4);
        double side = Noise(along / 4.0, line * 5 + across + 0.5, SaltL8Road + 5);
        if (side > 0.5 && Hashing.Unit(h) < 0.7) return 4;
        return (byte)(side < -0.55 && Hashing.Unit(h) < 0.6 ? 2 : 3);
    }
}
