using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 3999's ways in, laid out in the levels they stand in, each over the top with a salt of its own so nothing else
/// there moves (this file is the level's own; see docs/new-levels/CONTRACT.md):
/// <list type="bullet">
/// <item><b>Level 10</b>: a lone arcade building ("PARADISE" in neon, dark glass, a revolving door) with a little car park
/// under sodium lamps, and a chain of five windmills leading to it across the fields, one every 120 blocks out to 600,
/// each with a red beacon on its cap (and a generator by its door that turns the beacon green). One arcade at most to a
/// square of the fields 2048 blocks a side, where the whole of it lies on crops, stubble or meadow.</item>
/// <item><b>Level 11</b>: a stretch of alley wall flickering purple, in one city block in three hundred.</item>
/// <item><b>Level 37</b>: a three by three patch of glowing magenta tiles at the bottom of the deepest water in one plan
/// block in thirty, past 40% of the Poolrooms' radius.</item>
/// </list>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>The side of a square of Level 10 that holds at most one arcade.</summary>
    private const int L3999ArcadeLattice = 2048;

    /// <summary>The windmills: how many, how far apart, and how far a windmill's tower reaches from its middle.</summary>
    public const int L3999Mills = 5, L3999MillSpacing = 120, L3999MillReach = 3;

    /// <summary>A lone arcade in the fields of Level 10, and its windmills.</summary>
    public sealed class L3999ArcadeSite
    {
        public bool Valid;
        /// <summary>The middle of its front wall (the revolving door's middle tile).</summary>
        public int X, Z;
        /// <summary>The way its façade faces (toward its car park).</summary>
        public ArchPier Facing;
        public readonly (int X, int Z)[] Mills = new (int, int)[L3999Mills];
        /// <summary>The way each windmill's door (and its generator) faces: toward the arcade.</summary>
        public readonly ArchPier[] MillFacing = new ArchPier[L3999Mills];
        public int MinX, MinZ, MaxX, MaxZ;
    }

    private PlanCache<L3999ArcadeSite> l3999Arcades;

    /// <summary>The arcade of a square of the fields (Valid false if it has none).</summary>
    public L3999ArcadeSite L3999ArcadeAt(int i, int j) => (l3999Arcades ??= new PlanCache<L3999ArcadeSite>(64, PlanL3999Arcade)).Get(i, j);

    private L3999ArcadeSite PlanL3999Arcade(int i, int j)
    {
        var site = new L3999ArcadeSite();
        ulong h = Hashing.Hash(seed, i, j, SaltL3999Arcade);
        if (Hashing.Unit(h) >= 0.6) return site;
        const int S = L3999ArcadeLattice;
        site.X = i * S + 600 + (int)(Hashing.Unit(Hashing.Mix(h)) * (S - 1200));
        site.Z = j * S + 600 + (int)(Hashing.Unit(Hashing.Mix(h + 1)) * (S - 1200));
        site.Facing = L3999FromIndex((int)(Hashing.Mix(h + 2) % 4));
        // The windmills stand out in front of the façade, within 60 degrees either side, so their lights lead to the door
        var (fx, fz) = L3999Step(site.Facing);
        double angle = Math.Atan2(fz, fx) + (Hashing.Unit(Hashing.Mix(h + 3)) - 0.5) * Math.PI * 2 / 3;
        site.MinX = site.X - 14; site.MaxX = site.X + 14; site.MinZ = site.Z - 14; site.MaxZ = site.Z + 14;
        for (int k = 0; k < L3999Mills; k++)
        {
            int d = L3999MillSpacing * (k + 1) + 20;
            int mx = site.X + (int)Math.Round(Math.Cos(angle) * d), mz = site.Z + (int)Math.Round(Math.Sin(angle) * d);
            site.Mills[k] = (mx, mz);
            int ax = site.X - mx, az = site.Z - mz;
            site.MillFacing[k] = Math.Abs(ax) >= Math.Abs(az) ? (ax > 0 ? ArchPier.East : ArchPier.West) : (az > 0 ? ArchPier.South : ArchPier.North);
            site.MinX = Math.Min(site.MinX, mx - 5); site.MaxX = Math.Max(site.MaxX, mx + 5);
            site.MinZ = Math.Min(site.MinZ, mz - 5); site.MaxZ = Math.Max(site.MaxZ, mz + 5);
        }
        // Only where all of it lies in Level 10, on open fields (never over a farmstead, a paddock or a pond)
        bool Open(int x, int z)
        {
            if (LevelAt(MacroOf(x), MacroOf(z)) != 10) return false;
            var f = FieldAt(x, z);
            return FieldKind(f.I, f.J) is not (FarmField.Farmstead or FarmField.Pasture or FarmField.Lake);
        }
        if (!AllLevel(10, site.X - 20, site.Z - 20, 41)) return site;
        for (int dz = -16; dz <= 16; dz += 8)
            for (int dx = -16; dx <= 16; dx += 8)
                if (!Open(site.X + dx, site.Z + dz)) return site;
        foreach (var (mx, mz) in site.Mills)
            if (!AllLevel(10, mx - 5, mz - 5, 11) || !Open(mx, mz)) return site;
        site.Valid = true;
        return site;
    }

    /// <summary>The square of the fields a block position lies in.</summary>
    private static (int I, int J) L3999ArcadeSquare(int gx, int gz) => (Hashing.FloorDiv(gx, L3999ArcadeLattice), Hashing.FloorDiv(gz, L3999ArcadeLattice));

    /// <summary>
    /// The arcade nearest to a place in the fields picked by a key (just past the Suburbs, in a direction the key gives),
    /// within six squares; null if none.
    /// </summary>
    public L3999ArcadeSite L3999ArcadeNear(ulong key)
    {
        ulong h = Hashing.Hash(seed, (int)(key & 0xFFFFFFFF), (int)(key >> 32), SaltL3999Arcade + 1);
        double angle = Hashing.Unit(h) * Math.PI * 2, radius = LevelMidRadius(10, angle) + 40;
        int gx = (spawnMacroX + (int)Math.Round(Math.Cos(angle) * radius)) * MacroSize, gz = (spawnMacroZ + (int)Math.Round(Math.Sin(angle) * radius)) * MacroSize;
        var (i0, j0) = L3999ArcadeSquare(gx, gz);
        L3999ArcadeSite best = null;
        long bestD = long.MaxValue;
        for (int r = 0; r <= 6 && best == null; r++)
            for (int j = j0 - r; j <= j0 + r; j++)
                for (int i = i0 - r; i <= i0 + r; i++)
                {
                    if (Math.Max(Math.Abs(i - i0), Math.Abs(j - j0)) != r) continue;
                    L3999ArcadeSite site = L3999ArcadeAt(i, j);
                    if (!site.Valid) continue;
                    long d = (long)(site.X - gx) * (site.X - gx) + (long)(site.Z - gz) * (site.Z - gz);
                    if (d < bestD) { bestD = d; best = site; }
                }
        return best;
    }

    /// <summary>Lays the arcades and their windmills over a cell of Level 10 (called at the end of BuildLevel10).</summary>
    private void L3999ArcadeOverlay(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize, x1 = x0 + MacroSize - 1, z1 = z0 + MacroSize - 1;
        var (i0, j0) = L3999ArcadeSquare(x0 + MacroSize / 2, z0 + MacroSize / 2);
        for (int j = j0 - 1; j <= j0 + 1; j++)
            for (int i = i0 - 1; i <= i0 + 1; i++)
            {
                // (A square's arcade and windmills lie well inside the squares round it: test the bounds before planning it)
                int si0 = i * L3999ArcadeLattice, sj0 = j * L3999ArcadeLattice;
                if (x1 < si0 - 800 || x0 > si0 + L3999ArcadeLattice + 800 || z1 < sj0 - 800 || z0 > sj0 + L3999ArcadeLattice + 800) continue;
                L3999ArcadeSite site = L3999ArcadeAt(i, j);
                if (!site.Valid || x1 < site.MinX || x0 > site.MaxX || z1 < site.MinZ || z0 > site.MaxZ) continue;
                for (int lz = 0; lz < MacroSize; lz++)
                    for (int lx = 0; lx < MacroSize; lx++)
                        L3999ArcadeTile(ref b.At(lx, lz), site, x0 + lx, z0 + lz);
            }
    }

    /// <summary>One tile of an arcade, its car park or a windmill, if the position is in one.</summary>
    private static void L3999ArcadeTile(ref Tile t, L3999ArcadeSite site, int gx, int gz)
    {
        // The building's frame: p across the façade (to its right, seen from the car park looking at it: the façade's left), q back from it
        var (fx, fz) = L3999Step(site.Facing);
        var (rx, rz) = L3999Step(L3999Right(site.Facing));
        int dx = gx - site.X, dz = gz - site.Z;
        int p = dx * rx + dz * rz, q = -(dx * fx + dz * fz);
        if (Math.Abs(p) <= 10 && q is >= 0 and <= 12)
        {
            // The building: stucco over a brick plinth, dark glass, a flat roof; the revolving door in the middle of its front
            t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L3999Wall, Under = Unders.L3999Arcade, Floor = FloorKind.Grass, Height = 6, Pier = site.Facing };
            if (q == 0 && Math.Abs(p) <= 1)
            {
                t.Kind = TileKind.Door;
                t.Pattern = WallPattern.L3999Revolving;
                t.Stack = (byte)(1 - p); // 0 its left, 1 the middle, 2 its right, seen from the car park
                t.Height = 3;
            }
            else if (q == 0 && Math.Abs(p) >= 3 && Math.Abs(p) <= 9) t.Variant = 1; // a window of dark glass
            return;
        }
        if (Math.Abs(p) <= 12 && q is >= -16 and <= -1)
        {
            // The car park: asphalt, white bays, sodium lamps, and the sign over the door
            t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.L3999Asphalt, Under = Unders.L3999Lot, Pier = site.Facing };
            if (q is >= -13 and <= -6 && Math.Abs(p) >= 3 && Math.Abs(p) % 3 == 0) t.Floor = FloorKind.L3999AsphaltLine;
            if ((Math.Abs(p) == 9 && q == -9) || (p == 0 && q == -15)) { t.Variant = Props.L3999LampPost; t.Pier = L3999Opp(site.Facing); }
            if (p == 0 && q == -1) { t.Overhead = Overheads.L3999Sign; t.Depth = 6; }
            return;
        }
        for (int k = 0; k < L3999Mills; k++)
        {
            int mdx = gx - site.Mills[k].X, mdz = gz - site.Mills[k].Z;
            if (Math.Abs(mdx) > 4 || Math.Abs(mdz) > 4) continue;
            // A smock windmill: an octagonal white tower, a dark cap, a beacon on top; by its door, the generator and the sails above it
            if (Math.Abs(mdx) <= L3999MillReach && Math.Abs(mdz) <= L3999MillReach && Math.Abs(mdx) + Math.Abs(mdz) <= 4)
            {
                t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L3999Wall, Under = Unders.L3999Windmill, Floor = FloorKind.Grass, Height = 9,
                    Variant = (ushort)(mdx == 0 && mdz == 0 ? 1 : 0), Pier = site.MillFacing[k] };
                return;
            }
            var (sx, sz) = L3999Step(site.MillFacing[k]);
            if (mdx == sx * 4 && mdz == sz * 4)
            {
                t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Grass, Under = Unders.L3999Windmill, Variant = Props.L3999Generator, Pier = site.MillFacing[k] };
                return;
            }
        }
    }

    /// <summary>Level 11: now and then a stretch of a city block's alley wall flickers purple, and isn't quite there (called at the end of PlanLots).</summary>
    private void PlaceL3999GlitchWall(Tile[] tiles, int bi, int bj)
    {
        ulong h = Hashing.Hash(seed, bi, bj, SaltL3999Glitch);
        if (Hashing.Unit(h) >= 1 / 300.0) return;
        for (int attempt = 0; attempt < 16; attempt++)
        {
            ulong k = Hashing.Mix(h + (ulong)attempt);
            int x = 10 + (int)(k % (ulong)(BlockW - 21));
            bool north = (Hashing.Mix(k) & 1) == 0;
            int wz = north ? AlleyZ - 1 : AlleyZ + 3, fz = north ? AlleyZ : AlleyZ + 2;
            ref Tile wall = ref At(tiles, x, wz);
            if (wall.Kind != TileKind.Wall || (wall.Detail & CityDetail.Corner) != 0 || wall.Under != 0) continue;
            wall.Under = Unders.L3999GlitchWall;
            wall.Pier = north ? ArchPier.South : ArchPier.North;
            At(tiles, x, fz).Variant = 0;
            return;
        }
    }

    /// <summary>Level 37: glowing magenta tiles at the bottom of a plan block's deepest water, far out (called at the end of PlanPoolBlock).</summary>
    private void PlaceL3999Magenta(PoolPlanner p, int bi, int bj)
    {
        if (p.Reservoir) return;
        ulong h = Hashing.Hash(seed, bi, bj, SaltL3999Magenta);
        if (Hashing.Unit(h) >= 1 / 30.0) return;
        double cx = (PoolOriginX + bi * PoolBlock + PoolBlock / 2.0) / MacroSize - PoolCentreX;
        double cz = (PoolOriginZ + bj * PoolBlock + PoolBlock / 2.0) / MacroSize - PoolCentreZ;
        if (cx * cx + cz * cz < 0.16 * PoolRadius * PoolRadius) return;
        // The deepest three by three of level bottom in the block
        int bestDepth = 3, bu = -1, bv = -1;
        for (int v = 1; v < PoolBlock - 3; v++)
            for (int u = 1; u < PoolBlock - 3; u++)
            {
                Tile t0 = p.At(u, v);
                if (t0.Kind != TileKind.Floor || t0.Depth <= bestDepth || t0.Under != 0) continue;
                bool level = true;
                for (int dv = 0; dv < 3 && level; dv++)
                    for (int du = 0; du < 3 && level; du++)
                    {
                        Tile t = p.At(u + du, v + dv);
                        level = t.Kind == TileKind.Floor && t.Depth == t0.Depth && t.Under == 0 && t.Variant == 0;
                    }
                if (!level) continue;
                bestDepth = t0.Depth;
                bu = u;
                bv = v;
            }
        if (bu < 0) return;
        for (int dv = 0; dv < 3; dv++)
            for (int du = 0; du < 3; du++) p.At(bu + du, bv + dv).Under = Unders.L3999MagentaTiles;
    }
}
