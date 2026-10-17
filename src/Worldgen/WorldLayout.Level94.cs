using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 94, "Motion": a stop-motion picture of the 1930s to 50s that never stops being made. Perfectly round hills of
/// mown grass go on forever, each with one cream house on top and a straight path down to the winding roads in the
/// valleys, where a STOP sign stands at every junction and a NO OUTLET sign at roads that never end. Here and there a
/// white water tower full of Almond Water stands on a hill, or a car is parked in the middle of nowhere. Small towns
/// lie in the valleys round a fountain running with Almond Water, siren poles at its corners playing the same happy
/// tune all day, milk vans full of Almond Milk at the kerb.
///
/// Toward the middle the houses come apart: first a kitchen alone on a hill, then a bedroom that is one wall and a
/// floor, then furniture with no walls at all, then heaps of it; and then the transparent mountain, a cone of glass
/// with a white castle on top, where the King keeps his court. Everything the wanderers saw got stranger the nearer
/// they came to it, and so it is the way to find it.
///
/// Kept as level 13 (<see cref="Motion"/>) and shown as 94. It is not a ring: it lies far out to the north, and you
/// fall into it out of the sky. Its valleys lie <see cref="WorldGeometry.MotionDrop"/> blocks below the other levels'
/// floor, so its hills and its mountain have room. A floor tile's <see cref="Tile.Height"/> is the height of its ground
/// above the valley floor. Its edge is the painted backdrop of the set.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltMotionShape = 0x9401, SaltHill = 0x9402, SaltRoadKept = 0x9403, SaltTown = 0x9404, SaltMotionTop = 0x9405,
        SaltMotionSign = 0x9406, SaltStripe = 0x9407, SaltCastle = 0x9408, SaltFence = 0x9409;

    /// <summary>How far apart the hills are, on a jittered lattice.</summary>
    public const int HillPitch = 56;

    /// <summary>The glass mountain: its foot, the flat top the castle stands on, and how high that is.</summary>
    public const int MountainRadius = 90, PlateauRadius = 40, MountainHeight = 40;

    /// <summary>The castle's plan, square, on the mountain's top.</summary>
    public const int CastleSize = 56;

    /// <summary>A town: a square of roads round eight lots and the plaza. One to a district of six by six hills.</summary>
    private const int TownSize = 74, TownEvery = 6;

    /// <summary>The lot a hilltop is planned in.</summary>
    private const int HillLot = 18;

    // ================= Where Motion is =================

    /// <summary>Motion's centre, the mountain, in macro cells: as far out to the north as the city is to the east.</summary>
    private int MotionCentreX => spawnMacroX;
    private int MotionCentreZ => spawnMacroZ - Math.Max(800, spawnMacroZ / 4);

    /// <summary>Motion's radius in macro cells.</summary>
    private int MotionRadius => Math.Max(80, spawnMacroZ / 20);

    /// <summary>The middle of the mountain, in blocks: everything in Motion is planned from here.</summary>
    public int MotionOriginX => MotionCentreX * MacroSize + MacroSize / 2;
    public int MotionOriginZ => MotionCentreZ * MacroSize + MacroSize / 2;

    private bool InMotion(double mx, double mz)
    {
        double dx = mx - MotionCentreX, dz = mz - MotionCentreZ;
        double r = Math.Sqrt(dx * dx + dz * dz);
        if (r > MotionRadius * 1.2) return false;
        return r * (1 + 0.08 * Fbm(mx / 40.0, mz / 40.0, SaltMotionShape)) < MotionRadius;
    }

    /// <summary>
    /// A place to look for somewhere to fall to: out in the hills between a quarter and three quarters of a kilometre
    /// from the mountain, near enough that the houses have started to come apart, or will soon.
    /// </summary>
    private (int Mx, int Mz) MotionArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, radius = 260 + 440 * Hashing.Unit(Hashing.Mix(h));
        return (MacroOf(MotionOriginX + (int)Math.Round(Math.Cos(angle) * radius)), MacroOf(MotionOriginZ + (int)Math.Round(Math.Sin(angle) * radius)));
    }

    /// <summary>Arriving in Motion: on the grass, out in the open.</summary>
    private static bool IsMotionArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Roof == 0 && t.Zone == 0 && t.Floor is FloorKind.TurfLight or FloorKind.TurfDark && t.Overhead == 0;

    /// <summary>How far a block position is from the middle of the mountain.</summary>
    public double MotionDistance(int gx, int gz)
    {
        double dx = gx - MotionOriginX, dz = gz - MotionOriginZ;
        return Math.Sqrt(dx * dx + dz * dz);
    }

    /// <summary>The nearest of the towns' siren poles within a radius of a position, if any (block coordinates of its foot).</summary>
    public (int X, int Z)? NearestSirenPole(int gx, int gz, int radius)
    {
        int ux = gx - MotionOriginX, uz = gz - MotionOriginZ, span = HillPitch * TownEvery;
        int ti = Hashing.FloorDiv(ux, span), tj = Hashing.FloorDiv(uz, span);
        (int X, int Z)? best = null;
        long bestD = (long)radius * radius;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (TownOf(ti + di, tj + dj) is not { } town) continue;
                foreach (var (u, v) in SirenPoleOffsets)
                {
                    int x = MotionOriginX + town.X0 + u, z = MotionOriginZ + town.Z0 + v;
                    long d = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                    if (d <= bestD) { bestD = d; best = (x, z); }
                }
            }
        return best;
    }

    /// <summary>Where a town's four siren poles stand, from its corner (asked every tick by the atmosphere by day).</summary>
    private static readonly (int U, int V)[] SirenPoleOffsets = { (22, 22), (51, 22), (22, 51), (51, 51) };

    /// <summary>Whether a Level 94 position is in a town (its square of roads, houses and plaza).</summary>
    public bool InMotionTown(int gx, int gz) => TownAt(gx - MotionOriginX, gz - MotionOriginZ) != null;

    /// <summary>Whether a Level 94 position is inside the castle on the mountain.</summary>
    public bool InCastle(int gx, int gz)
    {
        int cu = gx - MotionOriginX + CastleSize / 2, cv = gz - MotionOriginZ + CastleSize / 2;
        return cu >= 0 && cv >= 0 && cu < CastleSize && cv < CastleSize;
    }

    // ================= Cells =================

    private void BuildLevel94(Builder b, int mx, int mz)
    {
        // The edge of the set: a painted backdrop, solid, all the way round
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Motion) { rim = true; break; }

        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                t = rim ? new Tile { Kind = TileKind.Wall, Pattern = WallPattern.Backdrop, Floor = FloorKind.TurfLight }
                    : MotionTile(mx * MacroSize + lx, mz * MacroSize + lz);
            }
    }

    private Tile MotionTile(int gx, int gz)
    {
        int ux = gx - MotionOriginX, uz = gz - MotionOriginZ;
        double d = Math.Sqrt((double)ux * ux + (double)uz * uz);
        if (d < MountainRadius) return MountainTile(ux, uz, d);
        if (TownAt(ux, uz) is { } town)
        {
            Tile tt = TownPlan(town.Ti, town.Tj)[(uz - town.Z0) * TownSize + ux - town.X0];
            return tt;
        }
        return HillTile(gx, gz, ux, uz);
    }

    // ================= Hills =================

    private enum HillTop : byte { None, House, Kitchen, Bedroom, Parlour, Pile, Car, WaterTower, Tree, Gate }

    /// <summary>One hill: its middle, its size, and what stands on top. A hill with radius 0 is a lattice point with no hill.</summary>
    private readonly record struct Hill(int X, int Z, int Radius, int Height, HillTop Top, bool FacesSouth);

    private (int X, int Z) HillCentre(int hi, int hj)
    {
        ulong h = Hashing.Hash(seed, hi, hj, SaltHill);
        return (hi * HillPitch + HillPitch / 2 + (int)(Hashing.Unit(h) * 25) - 12, hj * HillPitch + HillPitch / 2 + (int)(Hashing.Unit(Hashing.Mix(h)) * 25) - 12);
    }

    /// <summary>
    /// The hill at a lattice point (see <see cref="PlanHillAt"/>), remembered: every tile asks for the nine round it, and
    /// each of those looks at nine towns and eight more hills, so working them out afresh made Motion the slowest level
    /// to build by far.
    /// </summary>
    private Hill HillAt(int hi, int hj) => (hills ??= new LatticeMemo<Hill>(4096, PlanHillAt)).Get(hi, hj);

    private LatticeMemo<Hill> hills;

    /// <summary>Works out the hill at a lattice point (a pure function of the seed and the point).</summary>
    private Hill PlanHillAt(int hi, int hj)
    {
        var (x, z) = HillCentre(hi, hj);
        double d = Math.Sqrt((double)x * x + (double)z * z);
        // No hills on the plain round the mountain, nor where a town lies
        if (d < MountainRadius + 30 || NearTown(x, z, 26)) return new Hill(x, z, 0, 0, HillTop.None, false);
        // Never so wide that a hill runs into the road between it and the next
        int nearest = int.MaxValue;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (di == 0 && dj == 0) continue;
                var (nx, nz) = HillCentre(hi + di, hj + dj);
                nearest = Math.Min(nearest, (int)Math.Sqrt((double)(nx - x) * (nx - x) + (double)(nz - z) * (nz - z)));
            }
        var rng = new Rng(Hashing.Hash(seed, hi, hj, SaltHill + 1));
        int radius = Math.Min(rng.Range(20, 26), nearest / 2 - 3);
        // A parabola no steeper than a block a block, so the hills can be walked (if not without jumping)
        int height = Math.Max(4, Math.Min(radius / 2, rng.Range(9, 13)));
        return new Hill(x, z, radius, height, PickHillTop(ref rng, d), rng.Chance(0.5));
    }

    /// <summary>What stands on a hill: whole houses far out, coming apart the nearer the mountain is.</summary>
    private static HillTop PickHillTop(ref Rng rng, double d)
    {
        double r = rng.NextDouble();
        if (d < 230) return r < 0.6 ? HillTop.Pile : r < 0.75 ? HillTop.Car : r < 0.85 ? HillTop.Parlour : HillTop.None;
        if (d < 430) return r < 0.3 ? HillTop.Kitchen : r < 0.55 ? HillTop.Bedroom : r < 0.72 ? HillTop.Parlour : r < 0.8 ? HillTop.Pile : r < 0.9 ? HillTop.Tree : HillTop.None;
        if (d < 700) return r < 0.6 ? HillTop.House : r < 0.68 ? HillTop.Kitchen : r < 0.75 ? HillTop.Bedroom : r < 0.83 ? HillTop.WaterTower : r < 0.93 ? HillTop.Tree : HillTop.None;
        return r < 0.7 ? HillTop.House : r < 0.78 ? HillTop.WaterTower : r < 0.9 ? HillTop.Tree : r < 0.93 ? HillTop.Gate : r < 0.96 ? HillTop.Car : HillTop.None;
    }

    /// <summary>The ground of the hills alone (before lots and paths): the highest of the domes round a position.</summary>
    private int HillGround(int ux, int uz, out Hill owner)
    {
        int hi = Hashing.FloorDiv(ux, HillPitch), hj = Hashing.FloorDiv(uz, HillPitch);
        double best = 0;
        owner = default;
        double ownerDistance = double.MaxValue;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                Hill hill = HillAt(hi + di, hj + dj);
                double dx = ux - hill.X, dz = uz - hill.Z, r = Math.Sqrt(dx * dx + dz * dz);
                if (r < ownerDistance) { ownerDistance = r; owner = hill; }
                if (hill.Radius == 0 || r >= hill.Radius) continue;
                double q = r / hill.Radius;
                best = Math.Max(best, hill.Height * (1 - q * q));
            }
        return (int)Math.Round(best);
    }

    /// <summary>
    /// The roads in the valleys run along the lines halfway between neighbouring hills, so they wind as the hills lie.
    /// Returns how far a position is from the nearest such line, whether the road along it is there (a few are not,
    /// leaving dead ends), and how far from the next line over (small near a junction).
    /// </summary>
    private (double Off, bool Kept, double Next) RoadNear(int ux, int uz)
    {
        int hi = Hashing.FloorDiv(ux, HillPitch), hj = Hashing.FloorDiv(uz, HillPitch);
        (double D, int I, int J, int X, int Z) a = (double.MaxValue, 0, 0, 0, 0), b = a, c = a;
        for (int dj = -2; dj <= 2; dj++)
            for (int di = -2; di <= 2; di++)
            {
                // (A hill's X and Z are its lattice point's HillCentre, remembered with the rest of it)
                Hill hill = HillAt(hi + di, hj + dj);
                int x = hill.X, z = hill.Z;
                double d = (double)(ux - x) * (ux - x) + (double)(uz - z) * (uz - z);
                var e = (d, hi + di, hj + dj, x, z);
                if (d < a.D) { c = b; b = a; a = e; }
                else if (d < b.D) { c = b; b = e; }
                else if (d < c.D) c = e;
            }
        double Bisector((double D, int I, int J, int X, int Z) p, (double D, int I, int J, int X, int Z) q)
        {
            double len = Math.Sqrt((double)(p.X - q.X) * (p.X - q.X) + (double)(p.Z - q.Z) * (p.Z - q.Z));
            return (q.D - p.D) / (2 * Math.Max(1, len));
        }
        // An edge is kept or dropped as a whole: hash its two hills in order
        (int, int, int, int) key = a.I < b.I || a.I == b.I && a.J < b.J ? (a.I, a.J, b.I, b.J) : (b.I, b.J, a.I, a.J);
        bool kept = Hashing.Unit(Hashing.Hash(seed, key.Item1 * 7919 + key.Item3, key.Item2 * 7919 + key.Item4, SaltRoadKept)) < 0.68;
        return (Bisector(a, b), kept, Bisector(a, c));
    }

    private Tile HillTile(int gx, int gz, int ux, int uz)
    {
        int ground = HillGround(ux, uz, out Hill owner);
        var t = new Tile { Kind = TileKind.Floor, Height = (byte)ground, Floor = Stripe(ux, uz, owner) };
        var (off, kept, next) = RoadNear(ux, uz);
        bool town = NearTown(ux, uz, 3);

        // The roads: asphalt five wide, a kerb either side
        if (kept && !town && ground == 0)
        {
            if (off < 2.5) { t.Floor = FloorKind.MotionAsphalt; return t; }
            if (off < 3.5) { t.Floor = FloorKind.MotionKerb; return t; }
            // Signs on the corners of junctions: STOP, or now and then NO OUTLET
            if (off < 4.5 && next is >= 6 and < 7.5)
            {
                ulong h = Hashing.Hash(seed, gx, gz, SaltMotionSign);
                if (Hashing.Unit(h) < 0.08)
                {
                    t.Variant = Hashing.Unit(Hashing.Mix(h)) < 0.75 ? Props.StopSign : Props.NoOutletSign;
                    t.Pier = (ArchPier)(h % 4);
                    return t;
                }
            }
            // White picket fences along some stretches of road, broken now and then
            if (off < 4.5 && FenceAlong(ux, uz) && Hashing.Mod(ux + uz, 23) > 2)
            {
                t.Kind = TileKind.Bars;
                t.Pattern = WallPattern.Fence;
                t.Stack = FenceMask(ux, uz);
                return t;
            }
        }

        // The hilltop, and the path down from its house
        if (owner.Radius > 0 && owner.Top != HillTop.None)
        {
            HillPlan plan = HillPlanOf(Hashing.FloorDiv(owner.X, HillPitch), Hashing.FloorDiv(owner.Z, HillPitch));
            if (plan != null)
            {
                ground = plan.Ground(ux, uz, ground, kept ? off : 99);
                t.Height = (byte)ground;
                int lu = ux - plan.X0, lv = uz - plan.Z0;
                if (lu >= 0 && lv >= 0 && lu < HillLot && lv < HillLot)
                {
                    Tile lot = plan.Tiles[lv * HillLot + lu];
                    lot.Height = (byte)ground;
                    if (lot.Floor is FloorKind.Lawn or FloorKind.Grass) lot.Floor = t.Floor;
                    // The path to the door climbs the yard in steps
                    if (lot.Floor == FloorKind.MotionPath && lot.Kind == TileKind.Floor)
                    {
                        int uv = plan.FacesSouth ? lv - 1 : lv + 1, uz2 = plan.Z0 + uv;
                        if (uv >= 0 && uv < HillLot && plan.Ground(ux, uz2, HillGround(ux, uz2, out _), 99) == lot.Height + 1)
                        {
                            lot.Stair = 1;
                            lot.Pier = plan.FacesSouth ? ArchPier.North : ArchPier.South;
                        }
                    }
                    return lot;
                }
                if (plan.Path.TryGetValue((ux, uz), out var step) && !(kept && off < 3.5))
                {
                    t.Floor = FloorKind.MotionPath;
                    t.Height = step.Height;
                    if (step.Stair) { t.Stair = 1; t.Pier = step.Up; }
                    return t;
                }
            }
        }
        // Now and then a tree in a valley
        if (ground == 0 && off > 6 && Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltMotionTop + 9)) < 0.0015) t.Variant = Props.Tree;
        return t;
    }

    /// <summary>The grass is mown in stripes three wide, each hill at its own angle, the valleys at another.</summary>
    private FloorKind Stripe(int ux, int uz, Hill owner)
    {
        double angle = owner.Radius > 0 ? Hashing.Unit(Hashing.Hash(seed, owner.X, owner.Z, SaltStripe)) * Math.PI : 0.6;
        double along = ux * Math.Cos(angle) + uz * Math.Sin(angle);
        return Hashing.Mod((int)Math.Floor(along / 3), 2) == 0 ? FloorKind.TurfLight : FloorKind.TurfDark;
    }

    /// <summary>
    /// Whether a position beside a road (a block out from its kerb) has a picket fence: rolled once for each square of the
    /// hill lattice, so a fence runs along the roads through a square and stops at its edge.
    /// </summary>
    private bool FenceAlong(int ux, int uz)
    {
        var (off, kept, _) = RoadNear(ux, uz);
        if (!kept || off < 3.5 || off >= 4.5) return false;
        int hi = Hashing.FloorDiv(ux, HillPitch), hj = Hashing.FloorDiv(uz, HillPitch);
        return Hashing.Unit(Hashing.Hash(seed, hi, hj, SaltFence)) < 0.35;
    }

    /// <summary>Which neighbours a length of fence joins (N1 E2 S4 W8).</summary>
    private byte FenceMask(int ux, int uz)
    {
        bool F(int x, int z) => FenceAlong(x, z) && Hashing.Mod(x + z, 23) > 2 && HillGround(x, z, out _) == 0;
        return (byte)((F(ux, uz - 1) ? 1 : 0) | (F(ux + 1, uz) ? 2 : 0) | (F(ux, uz + 1) ? 4 : 0) | (F(ux - 1, uz) ? 8 : 0));
    }

    // ================= Hilltops =================

    /// <summary>A hill's top as planned: its lot (in the hill's own corner of the world), how high the lot stands, and the path down.</summary>
    private sealed class HillPlan
    {
        public Tile[] Tiles;
        public int X0, Z0;
        public byte Floor;
        public bool FacesSouth;
        /// <summary>What stands level on the hill (a house and its porch, or a room or a heap), in the hill's own coordinates.</summary>
        public int CoreX0, CoreZ0, CoreX1, CoreZ1;

        /// <summary>
        /// The ground round what stands on the hill: level with it beside it, then falling a block a block until it
        /// meets the hill, so neither the yard nor the hill round it is ever a step too high to walk.
        /// </summary>
        public int Ground(int ux, int uz, int natural, double road)
        {
            int away = Math.Max(Math.Max(CoreX0 - ux, ux - CoreX1), Math.Max(CoreZ0 - uz, uz - CoreZ1));
            // ...and never so high beside a road that the kerb is a step too high
            return Math.Max(natural, Math.Min(Floor - Math.Max(0, away), (int)Math.Floor(road - 3)));
        }
        public readonly Dictionary<(int, int), (byte Height, bool Stair, ArchPier Up)> Path = new();
    }

    private PlanCache<HillPlan> hillPlans;

    private HillPlan HillPlanOf(int hi, int hj) => (hillPlans ??= new PlanCache<HillPlan>(256, PlanHill)).Get(hi, hj);

    private HillPlan PlanHill(int hi, int hj)
    {
        Hill hill = HillAt(hi, hj);
        if (hill.Radius == 0 || hill.Top == HillTop.None) return null;
        var plan = new HillPlan { Tiles = new Tile[HillLot * HillLot], X0 = hill.X - HillLot / 2, Z0 = hill.Z - HillLot / 2, Floor = (byte)hill.Height,
            FacesSouth = hill.FacesSouth };
        // The part of the lot that stands level: a house and its porch, or the middle where a room or a heap stands
        int coreU0 = 5, coreU1 = 12, coreV0 = 5, coreV1 = 12;
        var rng = new Rng(Hashing.Hash(seed, hi, hj, SaltMotionTop));
        Tile[] lot = new Tile[HillLot * HillLot];
        // (Laid as lawn, so the front yard gets its flower beds and shrubs; drawn as the hill's mown turf)
        for (int i = 0; i < lot.Length; i++) lot[i] = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Lawn };
        ref Tile At(int u, int v) => ref lot[v * HillLot + u];
        int doorU = -1;

        switch (hill.Top)
        {
            case HillTop.House:
            {
                House house = PlanHouse(lot, HillLot, ref rng, farmhouse: true);
                PlanFrontYard(lot, HillLot, house, ref rng);
                doorU = house.DoorU;
                (coreU0, coreU1, coreV0, coreV1) = (house.U0, house.U1, house.V0 - 2, house.V1);
                double kind = rng.NextDouble();
                for (int i = 0; i < lot.Length; i++)
                {
                    ref Tile t = ref lot[i];
                    // Cream clapboard, every one (in layout versions 1-7, three in ten white); the fittings of the 1950s
                    if (t.Pattern is >= WallPattern.SidingWhite and <= WallPattern.Brick)
                        t.Pattern = Version >= 8 || kind < 0.7 ? WallPattern.SidingYellow : WallPattern.SidingWhite;
                    // (Props only: a wall's Variant is its decor, numbered apart)
                    if (t.Kind == TileKind.Floor)
                    {
                        if (t.Variant == Props.Fridge) t.Variant = Props.Icebox;
                        else if (t.Variant == Props.OfficeBookshelf) t.Variant = Props.RadioCabinet;
                        else if (t.Variant == Props.FloorLamp && rng.Chance(0.5)) t.Variant = Props.RotaryPhone;
                        else if (t.Variant is Props.WheelieBin or Props.Mailbox) t.Variant = 0;
                    }
                    if (t.Ceiling == CeilingKind.LightOn) t.Ceiling = CeilingKind.LightOff;
                    if (t.Floor == FloorKind.Sidewalk) t.Floor = FloorKind.MotionPath;
                }
                ref Tile front = ref At(house.DoorU, house.V0);
                if (rng.Chance(1 / 40.0))
                {
                    // A house whose front door opens onto the Suburbs
                    front.Kind = TileKind.Door;
                    front.Under = Unders.DollHouse;
                }
                else if (rng.Chance(1 / 50.0))
                {
                    // A house full of water to its ceiling, its door shut on it
                    front.Kind = TileKind.Door;
                    front.Under = Unders.FloodedHouse;
                    for (int v = house.V0 + 1; v < house.V1; v++)
                        for (int u = house.U0 + 1; u < house.U1; u++)
                            if (At(u, v).Kind == TileKind.Floor) { At(u, v).Under = Unders.FloodedHouse; At(u, v).Sealed = true; }
                }
                break;
            }
            case HillTop.Kitchen:
            {
                // A kitchen standing alone on the grass, walls on two sides, as if the rest of the house was never made
                int u0 = 5, v0 = 5, u1 = 12, v1 = 11;
                for (int v = v0; v <= v1; v++)
                    for (int u = u0; u <= u1; u++)
                    {
                        ref Tile t = ref At(u, v);
                        t.Floor = FloorKind.HouseLino;
                        if (u == u0 || v == v0) SetWall(ref t, WallPattern.InteriorStripe, BaseStyle.Plain);
                    }
                PutLot(lot, u0 + 1, v0 + 1, Props.KitchenCabinet, ArchPier.South);
                PutLot(lot, u0 + 2, v0 + 1, Props.Stove, ArchPier.South);
                PutLot(lot, u0 + 3, v0 + 1, Props.KitchenCounter, ArchPier.South, 1);
                PutLot(lot, u0 + 4, v0 + 1, Props.Icebox, ArchPier.South);
                PutLot(lot, u0 + 1, v0 + 3, Props.KitchenCabinet, ArchPier.East);
                PutLot(lot, u0 + 4, v0 + 4, Props.RoundTable, ArchPier.North);
                PutLot(lot, u0 + 3, v0 + 4, Props.HotelChair, ArchPier.East);
                PutLot(lot, u0 + 5, v0 + 4, Props.HotelChair, ArchPier.West);
                At(u0, v0 + 3).Variant = Decor.HouseClock;
                At(u0, v0 + 3).Pier = ArchPier.East;
                break;
            }
            case HillTop.Bedroom:
            {
                // A bedroom that is one wall and a floor
                int u0 = 5, v0 = 6, u1 = 12, v1 = 11;
                for (int v = v0; v <= v1; v++)
                    for (int u = u0; u <= u1; u++)
                    {
                        ref Tile t = ref At(u, v);
                        t.Floor = FloorKind.HouseCarpet;
                        if (v == v0) SetWall(ref t, WallPattern.InteriorFloral, BaseStyle.Plain);
                    }
                PutLot(lot, u0 + 3, v0 + 1, Props.Bed, ArchPier.South, 0);
                PutLot(lot, u0 + 3, v0 + 2, Props.Bed, ArchPier.South, 1);
                PutLot(lot, u0 + 2, v0 + 1, Props.Nightstand, ArchPier.South);
                PutLot(lot, u0 + 4, v0 + 1, Props.Nightstand, ArchPier.South);
                PutLot(lot, u0 + 6, v0 + 1, Props.Wardrobe, ArchPier.South);
                PutLot(lot, u0 + 1, v0 + 4, Props.Dresser, ArchPier.East);
                for (int u = u0 + 2; u <= u0 + 4; u++) At(u, v0 + 3).Floor = FloorKind.HouseRug;
                At(u0 + 1, v0).Variant = Decor.HouseMirror;
                At(u0 + 1, v0).Pier = ArchPier.South;
                break;
            }
            case HillTop.Parlour:
            {
                // A living room with no room: a sofa, a set, a lamp, a rug on the grass
                int cu = 8, cv = 8;
                for (int u = cu - 2; u <= cu + 2; u++)
                    for (int v = cv - 1; v <= cv + 1; v++) At(u, v).Floor = FloorKind.HouseRug;
                PutLot(lot, cu - 3, cv, Props.Tv, ArchPier.East);
                PutLot(lot, cu, cv, Props.CoffeeTable, ArchPier.North);
                PutLot(lot, cu + 3, cv, Props.Sofa, ArchPier.West);
                PutLot(lot, cu, cv - 3, Props.WingChair, ArchPier.South);
                PutLot(lot, cu + 3, cv - 2, Props.FloorLamp, ArchPier.North);
                PutLot(lot, cu - 3, cv + 2, Props.RadioCabinet, ArchPier.North);
                break;
            }
            case HillTop.Pile:
            {
                // Heaps of furniture with no house at all, now and then a staircase going nowhere or a car
                // tipped on its side among them
                for (int k = 0; k < 16; k++)
                {
                    int u = 4 + rng.Range(0, 9), v = 4 + rng.Range(0, 9);
                    PutLot(lot, u, v, Props.FurniturePile, (ArchPier)rng.Range(0, 3), (byte)rng.Range(0, 3));
                }
                if (rng.Chance(0.4)) PutLot(lot, 3, 13, Props.Sofa, (ArchPier)rng.Range(0, 3));
                if (rng.Chance(0.5))
                {
                    // Five steps up toward the north, and nothing at the top
                    for (int k = 0; k < 5; k++)
                    {
                        ref Tile step = ref At(14, 13 - k);
                        step = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Lawn, Stair = (byte)(k + 1), Pier = ArchPier.North, Under = Unders.Nowhere };
                    }
                }
                else if (rng.Chance(0.5)) PutLot(lot, 13, 3, Props.TippedCar, (ArchPier)rng.Range(0, 3), (byte)rng.Range(0, 2));
                break;
            }
            case HillTop.Car:
                PlaceLotCar(lot, 7, 6, Props.OldCar, (byte)rng.Range(0, 3));
                break;
            case HillTop.WaterTower:
                for (int dv = -2; dv <= 2; dv++)
                    for (int du = -2; du <= 2; du++)
                    {
                        ref Tile t = ref At(9 + du, 9 + dv);
                        t.Variant = Props.WaterTower;
                        t.Stack = (byte)((du + 2) + (dv + 2) * 5);
                    }
                break;
            case HillTop.Tree:
                At(9, 9).Variant = Props.Tree;
                for (int dv = -1; dv <= 1; dv++)
                    for (int du = -1; du <= 1; du++)
                        if (du != 0 || dv != 0) At(9 + du, 9 + dv).Overhead = Overheads.Leaves;
                break;
            case HillTop.Gate:
            {
                // A rusted field gate with no sign on it, in a stretch of fence going nowhere
                for (int u = 5; u <= 12; u++)
                {
                    ref Tile t = ref At(u, 9);
                    if (u is 8 or 9) { t.Variant = Props.TwilightGate; t.Pier = ArchPier.North; continue; }
                    t.Kind = TileKind.Bars;
                    t.Pattern = WallPattern.Fence;
                    t.Stack = (byte)((u > 5 && u != 10 ? 8 : 0) | (u < 12 && u != 7 ? 2 : 0));
                }
                break;
            }
        }

        // One colour of shingles to a house, red or brown as in the pictures (kept in Detail, one more than the material)
        byte shingles = (byte)(rng.Chance(0.7) ? 3 : 2);
        for (int i = 0; i < lot.Length; i++) lot[i].Detail = shingles;

        // Face the lot north or south: the plans are drawn with their front (v = 0) to the north
        for (int v = 0; v < HillLot; v++)
            for (int u = 0; u < HillLot; u++)
            {
                Tile t = lot[v * HillLot + u];
                int z = hill.FacesSouth ? HillLot - 1 - v : v;
                if (hill.FacesSouth)
                {
                    if (t.Variant == Props.Car) t.Variant = Props.CarPart;
                    else if (t.Variant == Props.CarPart && u > 0 && lot[v * HillLot + u - 1].Variant == Props.Car) t.Variant = Props.Car;
                    t.Pier = MirrorNS(t.Pier);
                    t.Roof = RoofBits.Turned(t.Roof, MirrorNS);
                    if (t.Kind == TileKind.Bars) t.Stack = MirrorMask(t.Stack);
                    if (t.Variant == Props.WaterTower) t.Stack = (byte)(t.Stack % 5 + (4 - t.Stack / 5) * 5);
                }
                plan.Tiles[z * HillLot + u] = t;
            }

        // What stands level, in the hill's coordinates (the lot is mirrored north to south when it faces south)
        plan.CoreX0 = plan.X0 + coreU0;
        plan.CoreX1 = plan.X0 + coreU1;
        plan.CoreZ0 = plan.Z0 + (hill.FacesSouth ? HillLot - 1 - coreV1 : coreV0);
        plan.CoreZ1 = plan.Z0 + (hill.FacesSouth ? HillLot - 1 - coreV0 : coreV1);

        // The path from the front door down the hill to the road, a staircase where the hill falls away
        if (doorU >= 0)
        {
            int px = plan.X0 + doorU, step = hill.FacesSouth ? 1 : -1;
            int pz = hill.FacesSouth ? plan.Z0 + HillLot : plan.Z0 - 1;
            int edgeV = hill.FacesSouth ? HillLot - 1 : 0;
            int previous = plan.Ground(px, plan.Z0 + edgeV, HillGround(px, plan.Z0 + edgeV, out _), 99);
            ArchPier up = hill.FacesSouth ? ArchPier.North : ArchPier.South;
            for (int k = 0; k < 40; k++, pz += step)
            {
                var (off, kept, _) = RoadNear(px, pz);
                if (kept && off < 3.5 || NearTown(px, pz, 2)) break;
                int natural = plan.Ground(px, pz, HillGround(px, pz, out _), kept ? off : 99);
                int height = Math.Max(natural, previous - 1);
                plan.Path[(px, pz)] = ((byte)height, previous - height == 1, up);
                if (height == 0 && natural == 0 && k > 2) break;
                previous = height;
            }
        }
        return plan;
    }

    private static void PutLot(Tile[] lot, int u, int v, byte prop, ArchPier facing, byte stack = 0)
    {
        if (u < 0 || v < 0 || u >= HillLot || v >= HillLot) return;
        ref Tile t = ref lot[v * HillLot + u];
        if (t.Kind != TileKind.Floor || t.Variant != 0) return;
        t.Variant = prop;
        t.Pier = facing;
        t.Stack = stack;
    }

    /// <summary>A car (or a milk van) facing north: the anchor tile draws it, two by four.</summary>
    private static void PlaceLotCar(Tile[] lot, int u, int v, byte prop, byte colour)
    {
        for (int dv = 0; dv < 4; dv++)
            for (int du = 0; du < 2; du++)
            {
                ref Tile c = ref lot[(v + dv) * HillLot + u + du];
                c.Variant = du == 0 && dv == 0 ? prop : Props.CarPart;
                c.Stack = colour;
                c.Pier = ArchPier.North;
            }
    }

    // ================= Towns =================

    /// <summary>Where the town of a district stands (the corner of its square), if it has one (remembered, as the hills are).</summary>
    private (int Ti, int Tj, int X0, int Z0)? TownOf(int ti, int tj) => (towns ??= new LatticeMemo<(int, int, int, int)?>(1024, PlanTownOf)).Get(ti, tj);

    private LatticeMemo<(int, int, int, int)?> towns;

    private (int Ti, int Tj, int X0, int Z0)? PlanTownOf(int ti, int tj)
    {
        ulong h = Hashing.Hash(seed, ti, tj, SaltTown);
        int span = HillPitch * TownEvery;
        int cx = ti * span + span / 2 + (int)(Hashing.Unit(Hashing.Mix(h)) * HillPitch * 2) - HillPitch;
        int cz = tj * span + span / 2 + (int)(Hashing.Unit(Hashing.Mix(Hashing.Mix(h))) * HillPitch * 2) - HillPitch;
        if (Math.Sqrt((double)cx * cx + (double)cz * cz) < 460 || Hashing.Unit(h) >= 0.7) return null;
        return (ti, tj, cx - TownSize / 2, cz - TownSize / 2);
    }

    /// <summary>The town whose square a position lies in.</summary>
    private (int Ti, int Tj, int X0, int Z0)? TownAt(int ux, int uz)
    {
        int span = HillPitch * TownEvery;
        int ti = Hashing.FloorDiv(ux, span), tj = Hashing.FloorDiv(uz, span);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (TownOf(ti + di, tj + dj) is not { } town) continue;
                if (ux >= town.X0 && uz >= town.Z0 && ux < town.X0 + TownSize && uz < town.Z0 + TownSize) return town;
            }
        return null;
    }

    /// <summary>Whether a position lies within <paramref name="margin"/> of a town's square.</summary>
    private bool NearTown(int ux, int uz, int margin)
    {
        int span = HillPitch * TownEvery;
        int ti = Hashing.FloorDiv(ux, span), tj = Hashing.FloorDiv(uz, span);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (TownOf(ti + di, tj + dj) is not { } town) continue;
                if (ux >= town.X0 - margin && uz >= town.Z0 - margin && ux < town.X0 + TownSize + margin && uz < town.Z0 + TownSize + margin) return true;
            }
        return false;
    }

    private PlanCache<Tile[]> townPlans;

    private Tile[] TownPlan(int ti, int tj) => (townPlans ??= new PlanCache<Tile[]>(16, PlanTown)).Get(ti, tj);

    /// <summary>
    /// A town: roads in a square of three by three, eight small houses round a paved plaza with the fountain of Almond
    /// Water in the middle, a siren pole on each corner of it, and milk vans and old cars at the kerbs.
    /// </summary>
    private Tile[] PlanTown(int ti, int tj)
    {
        var tiles = new Tile[TownSize * TownSize];
        var rng = new Rng(Hashing.Hash(seed, ti, tj, SaltTown + 1));
        ref Tile At(int u, int v) => ref tiles[v * TownSize + u];
        static bool Road(int a) => a < 5 || a is >= 23 and < 28 || a is >= 46 and < 51 || a >= 69;
        for (int v = 0; v < TownSize; v++)
            for (int u = 0; u < TownSize; u++)
            {
                ref Tile t = ref At(u, v);
                t = new Tile { Kind = TileKind.Floor, Floor = Road(u) || Road(v) ? FloorKind.MotionAsphalt : FloorKind.TurfLight };
                // Kerbs along the plaza and the lots
                if (!Road(u) && !Road(v)) continue;
                bool edge = Road(u) && !Road(v) && (u is 4 or 23 or 27 or 46 or 50 or 69) || Road(v) && !Road(u) && (v is 4 or 23 or 27 or 46 or 50 or 69);
                if (edge) t.Floor = FloorKind.MotionKerb;
            }

        // The plaza and its fountain
        for (int v = 28; v < 46; v++)
            for (int u = 28; u < 46; u++) At(u, v).Floor = FloorKind.MotionConcrete;
        for (int dv = -2; dv <= 2; dv++)
            for (int du = -2; du <= 2; du++)
            {
                ref Tile t = ref At(36 + du, 36 + dv);
                t.Variant = Props.AlmondFountain;
                t.Stack = (byte)((du + 2) + (dv + 2) * 5);
            }
        foreach (var (u, v, p) in new[] { (30, 31, ArchPier.East), (43, 31, ArchPier.West), (30, 42, ArchPier.East), (43, 42, ArchPier.West) })
        {
            At(u, v).Variant = Props.Bench;
            At(u, v).Pier = p;
        }
        foreach (var (u, v) in new[] { (29, 29), (44, 29), (29, 44), (44, 44) })
        {
            At(u, v).Variant = Props.Tree;
            for (int dv = -1; dv <= 1; dv++)
                for (int du = -1; du <= 1; du++)
                    if ((du != 0 || dv != 0) && At(u + du, v + dv).Variant == 0) At(u + du, v + dv).Overhead = Overheads.Leaves;
        }
        // Siren poles on the corners of the plaza, across the road from it (in layout versions 1-7 here, where the
        // lots below were laid over them; from 8 after the lots, on their front corners)
        if (Version < 8) PlaceSirenPoles(tiles);
        // Milk vans and old cars at the kerbs round the plaza
        int vans = 0;
        foreach (var (u, v) in new[] { (24, 30), (48, 30), (24, 38), (48, 38) })
        {
            if (!rng.Chance(0.6)) continue;
            byte prop = vans++ < 2 ? Props.MilkVan : Props.OldCar;
            for (int dv = 0; dv < 4; dv++)
                for (int du = 0; du < 2; du++)
                {
                    ref Tile c = ref At(u + du, v + dv);
                    c.Variant = du == 0 && dv == 0 ? prop : Props.CarPart;
                    c.Stack = (byte)rng.Range(0, 3);
                    c.Pier = ArchPier.North;
                }
        }

        // The eight lots round the plaza, each a house facing the road on its plaza side
        for (int row = 0; row < 3; row++)
            for (int col = 0; col < 3; col++)
            {
                if (row == 1 && col == 1) continue;
                int u0 = col == 0 ? 5 : col == 1 ? 28 : 51, v0 = row == 0 ? 5 : row == 1 ? 28 : 51;
                var lot = new Tile[HillLot * HillLot];
                for (int i = 0; i < lot.Length; i++) lot[i] = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Lawn };
                var lotRng = new Rng(Hashing.Hash(seed, ti * 3 + col, tj * 3 + row, SaltTown + 2));
                House house = PlanHouse(lot, HillLot, ref lotRng, farmhouse: true);
                PlanFrontYard(lot, HillLot, house, ref lotRng);
                bool facesSouth = row == 0; // the north row faces the road to its south
                byte shingles = (byte)(lotRng.Chance(0.7) ? 3 : 2);
                for (int v = 0; v < HillLot; v++)
                    for (int u = 0; u < HillLot; u++)
                    {
                        Tile t = lot[v * HillLot + u];
                        if (t.Pattern is >= WallPattern.SidingWhite and <= WallPattern.Brick)
                            t.Pattern = Version < 8 && (row + col) % 3 == 0 ? WallPattern.SidingWhite : WallPattern.SidingYellow;
                        if (t.Kind == TileKind.Floor) // (props only, as on the hills)
                        {
                            if (t.Variant == Props.Fridge) t.Variant = Props.Icebox;
                            else if (t.Variant == Props.OfficeBookshelf) t.Variant = Props.RadioCabinet;
                            else if (t.Variant is Props.WheelieBin or Props.Mailbox) t.Variant = 0;
                        }
                        if (t.Ceiling == CeilingKind.LightOn) t.Ceiling = CeilingKind.LightOff;
                        if (t.Floor == FloorKind.Sidewalk) t.Floor = FloorKind.MotionPath;
                        if (t.Floor is FloorKind.Lawn or FloorKind.Grass) t.Floor = FloorKind.TurfLight;
                        t.Detail = shingles;
                        if (facesSouth)
                        {
                            if (t.Variant == Props.Car) t.Variant = Props.CarPart;
                            else if (t.Variant == Props.CarPart && u > 0 && lot[v * HillLot + u - 1].Variant == Props.Car) t.Variant = Props.Car;
                            t.Pier = MirrorNS(t.Pier);
                            t.Roof = RoofBits.Turned(t.Roof, MirrorNS);
                            if (t.Kind == TileKind.Bars) t.Stack = MirrorMask(t.Stack);
                        }
                        At(u0 + u, v0 + (facesSouth ? HillLot - 1 - v : v)) = t;
                    }
            }
        if (Version >= 8) PlaceSirenPoles(tiles);
        return tiles;
    }

    /// <summary>
    /// A town's four siren poles, each on a square of concrete at <see cref="SirenPoleOffsets"/>: the front corner of
    /// a lot, at the kerb, across the crossroads from a corner of the plaza. From layout version 8 they go down after
    /// the lots and replace whatever the lot had there (its lawn); before that, before the lots, which covered them.
    /// </summary>
    private static void PlaceSirenPoles(Tile[] tiles)
    {
        foreach (var (u, v) in SirenPoleOffsets)
        {
            ref Tile t = ref tiles[v * TownSize + u];
            if (t.Kind != TileKind.Floor) t = new Tile { Kind = TileKind.Floor, Detail = t.Detail };
            t.Variant = Props.SirenPole;
            t.Floor = FloorKind.MotionConcrete;
            t.Overhead = 0;
        }
    }

    // ================= The mountain and the castle =================

    /// <summary>
    /// The glass mountain, a cone with a flat top; on the top, the castle. Mountain tiles are kept in <see cref="Tile.Zone"/>
    /// 2, the castle's in 3 (its blinding halls in 4).
    /// </summary>
    private Tile MountainTile(int ux, int uz, double d)
    {
        int height = d <= PlateauRadius ? MountainHeight : (int)Math.Round(MountainHeight * (MountainRadius - d) / (MountainRadius - PlateauRadius));
        int cu = ux + CastleSize / 2, cv = uz + CastleSize / 2;
        if (cu >= 0 && cv >= 0 && cu < CastleSize && cv < CastleSize)
        {
            Tile c = CastlePlan()[cv * CastleSize + cu];
            c.Height = MountainHeight;
            return c;
        }
        return new Tile { Kind = TileKind.Floor, Floor = FloorKind.TurfLight, Zone = 2, Height = (byte)Math.Max(0, height) };
    }

    private Tile[] castlePlan;

    private Tile[] CastlePlan() => castlePlan ??= PlanCastle();

    /// <summary>The castle's square, in its own coordinates (0 to <see cref="CastleSize"/>; the gate is in the south wall).</summary>
    private static bool CastleTower(int u, int v) => (u < 7 || u >= CastleSize - 7) && (v < 7 || v >= CastleSize - 7);

    /// <summary>
    /// The castle: white walls two thick with a red-roofed tower on each corner and a gate in the south wall. Inside,
    /// nothing is animated. A ring hall runs round inside the walls and another round the throne room in the middle;
    /// between them, rooms: the foyer, a ball pit, the blinding halls, the animation studio, the arcade, the slides, a
    /// hall of mirrors. The throne room has a door on each side, and only one of them opens, a different one each day.
    /// </summary>
    private Tile[] PlanCastle()
    {
        const int n = CastleSize;
        var tiles = new Tile[n * n];
        ref Tile At(int u, int v) => ref tiles[v * n + u];
        void Wall(int u, int v, WallPattern pattern) => At(u, v) = new Tile { Kind = TileKind.Wall, Pattern = pattern, Zone = 3 };
        void Floor(int u, int v, FloorKind floor, byte zone = 3) => At(u, v) = new Tile { Kind = TileKind.Floor, Floor = floor, Zone = zone, Ceiling = CeilingKind.Tile };
        var rng = new Rng(SaltCastle);

        // Fill: the funhouse's own walls
        for (int v = 0; v < n; v++)
            for (int u = 0; u < n; u++) Wall(u, v, WallPattern.Funhouse);
        // The outer walls and towers
        for (int v = 0; v < n; v++)
            for (int u = 0; u < n; u++)
                if (u < 2 || v < 2 || u >= n - 2 || v >= n - 2 || CastleTower(u, v)) Wall(u, v, WallPattern.CastleWall);

        void Room(int u0, int v0, int u1, int v1, FloorKind floor, byte zone = 3)
        {
            for (int v = v0; v <= v1; v++)
                for (int u = u0; u <= u1; u++) Floor(u, v, floor, zone);
        }
        void Door(int u, int v) => Floor(u, v, FloorKind.FunCarpet);

        // The halls inside the walls (the towers break them into four, joined through the corner rooms), and the ring
        // round the throne room
        Room(2, 7, 4, n - 8, FloorKind.FunCarpet); Room(n - 5, 7, n - 3, n - 8, FloorKind.FunCarpet);
        Room(7, 2, n - 8, 4, FloorKind.FunCarpet); Room(7, n - 5, n - 8, n - 3, FloorKind.FunCarpet);
        Room(18, 18, 37, 21, FloorKind.Checker); Room(18, 34, 37, 37, FloorKind.Checker);
        Room(18, 22, 21, 33, FloorKind.Checker); Room(34, 22, 37, 33, FloorKind.Checker);

        // The rooms between the rings: four in the corners, four at the sides
        Room(6, 6, 16, 16, FloorKind.Checker);          // north-west: the ball pit
        Room(39, 6, 49, 16, FloorKind.MotionConcrete, 4); // north-east: a blinding hall
        Room(6, 39, 16, 49, FloorKind.Checker);         // south-west: the animation studio
        Room(39, 39, 49, 49, FloorKind.Checker);        // south-east: the arcade
        Room(19, 6, 36, 16, FloorKind.FunCarpet);       // north: the hall of mirrors (a loop round a block)
        Room(19, 39, 36, 49, FloorKind.StarFloor);      // south: the foyer, in from the gate
        Room(6, 19, 16, 36, FloorKind.Checker);         // west: the slides
        Room(39, 19, 49, 36, FloorKind.MotionConcrete, 4); // east: another blinding hall

        // The hall of mirrors is a loop round a block of wall; the slide room has a climbing frame of wall down its middle
        for (int v = 9; v <= 13; v++) for (int u = 22; u <= 33; u++) Wall(u, v, WallPattern.Funhouse);
        for (int v = 23; v <= 32; v += 3) for (int u = 9; u <= 13; u++) Wall(u, v, WallPattern.Funhouse);

        // Doorways: each room to the outer ring and to the inner ring, the gate into the foyer
        foreach (var (u, v) in new[] { (5, 11), (11, 5), (50, 11), (44, 5), (5, 44), (11, 50), (50, 44), (44, 50),
                                       (27, 5), (28, 5), (27, 50), (28, 50), (5, 27), (5, 28), (50, 27), (50, 28),
                                       (17, 27), (17, 28), (38, 27), (38, 28), (27, 17), (28, 17), (27, 38), (28, 38) })
            Door(u, v);
        for (int u = 26; u <= 29; u++)
        {
            Floor(u, n - 1, FloorKind.StarFloor);
            Floor(u, n - 2, FloorKind.StarFloor);
        }

        // The throne room: sealed walls, a door in the middle of each, and inside the long table set for two
        Room(23, 23, 32, 32, FloorKind.FunCarpet);
        for (int k = 22; k <= 33; k++)
        {
            Wall(k, 22, WallPattern.Funhouse); Wall(k, 33, WallPattern.Funhouse);
            Wall(22, k, WallPattern.Funhouse); Wall(33, k, WallPattern.Funhouse);
        }
        foreach (var (u, v, p) in new[] { (27, 22, ArchPier.North), (33, 27, ArchPier.East), (28, 33, ArchPier.South), (22, 28, ArchPier.West) })
        {
            At(u, v) = new Tile { Kind = TileKind.Door, Pattern = WallPattern.ThroneDoor, Pier = p, Zone = 3 };
        }
        for (int v = 25; v <= 30; v++)
        {
            At(27, v).Variant = Props.ThroneTable;
            At(28, v).Variant = Props.ThroneTable;
        }
        At(27, 31).Variant = Props.TrialChair; At(27, 31).Pier = ArchPier.North;
        At(28, 24).Variant = Props.KingStatue; At(28, 24).Pier = ArchPier.South;
        for (int v = 23; v <= 32; v++)
            for (int u = 23; u <= 32; u++)
                if (At(u, v).Kind == TileKind.Floor) At(u, v).Sealed = true; // nobody is ever put down in there

        // The ball pit, sunk a block into the floor and full to the brim
        for (int v = 7; v <= 15; v++)
            for (int u = 7; u <= 15; u++) At(u, v).Variant = Props.BallPit;
        // The throne room: an old, dim dining hall, dark panelling, a deep red carpet, two chandeliers
        for (int v = 22; v <= 33; v++)
            for (int u = 22; u <= 33; u++)
            {
                ref Tile t = ref At(u, v);
                if (t.Kind == TileKind.Wall) t.Pattern = WallPattern.Hotel;
                else if (t.Kind == TileKind.Floor) t.Floor = FloorKind.HotelMaroon;
            }
        At(27, 27).Ceiling = CeilingKind.Chandelier;
        At(28, 30).Ceiling = CeilingKind.Chandelier;
        // The animation studio: the model of the town on its table, the camera, easels of sketches
        At(11, 44).Variant = Props.Diorama;
        At(11, 41).Variant = Props.StudioCamera; At(11, 41).Pier = ArchPier.South;
        foreach (var (u, v) in new[] { (7, 40), (15, 40), (7, 48), (15, 48) }) { At(u, v).Variant = Props.Easel; At(u, v).Pier = ArchPier.East; }
        // The arcade
        for (int u = 40; u <= 48; u += 2) { At(u, 40).Variant = Props.Arcade; At(u, 40).Pier = ArchPier.South; At(u, 48).Variant = Props.Arcade; At(u, 48).Pier = ArchPier.North; }
        // The slides
        foreach (var (u, v) in new[] { (8, 21), (8, 34), (14, 27) }) { At(u, v).Variant = Props.Slide; At(u, v).Pier = (ArchPier)rng.Range(0, 3); }
        // Lamps: the funhouse is lit, the blinding halls blindingly
        for (int v = 2; v < n - 2; v++)
            for (int u = 2; u < n - 2; u++)
            {
                ref Tile t = ref At(u, v);
                if (t.Kind != TileKind.Floor) continue;
                bool blinding = t.Zone == 4;
                if (u is >= 23 and <= 32 && v is >= 23 and <= 32) continue; // the throne room keeps to its chandeliers
                if (blinding ? u % 2 == 0 && v % 2 == 0 : u % 5 == 2 && v % 5 == 2) t.Ceiling = CeilingKind.LightOn;
            }
        return tiles;
    }
}

/// <summary>
/// A small memo of something worked out per point of a lattice (Motion's hills, its towns), for values that are pure
/// functions of the seed and the point and are asked for over and over while neighbouring tiles are built. Direct-mapped
/// and lock-free: each slot holds one immutable entry, replaced whole, so threads building cells at once only ever see a
/// complete entry, or a different point's (a miss: the value is worked out again). Bounded, so it never grows.
/// </summary>
internal sealed class LatticeMemo<T>
{
    private sealed class Entry
    {
        public readonly int I, J;
        public readonly T Value;
        public Entry(int i, int j, T value) { I = i; J = j; Value = value; }
    }

    private readonly Entry[] slots;
    private readonly Func<int, int, T> make;

    /// <param name="size">The number of slots, a power of two.</param>
    public LatticeMemo(int size, Func<int, int, T> make)
    {
        slots = new Entry[size];
        this.make = make;
    }

    public T Get(int i, int j)
    {
        int slot = (int)(unchecked((uint)(i * 73856093 ^ j * 19349663)) & (uint)(slots.Length - 1));
        Entry e = System.Threading.Volatile.Read(ref slots[slot]);
        if (e != null && e.I == i && e.J == j) return e.Value;
        T value = make(i, j);
        System.Threading.Volatile.Write(ref slots[slot], new Entry(i, j, value));
        return value;
    }
}
