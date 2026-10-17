using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 55, "Land of Ice" (experimental): kept as level 25 (<see cref="Level55"/>) and shown as "55". A glacier under a
/// polar day that never ends and a sun that never shows: rolling swells of packed snow and wind crust, dunes, ice ridges,
/// crevasse fields (some bridged with snow), a frozen sea, one ice cave in a dome of blue ice, and one small abandoned
/// research hut, the only warm place. Deadly cold outside. Neither wiki has a Level 55 by this name: the design
/// (docs/design/experimental-levels/55-plan.md) borrows from Fandom's Level 202 "Snowy Glaciers" and Level 44 "Under the
/// Ice". A prototype: no thresholds in or out (the cheats menu or <c>/backrooms goto</c> only), no entities, no loot.
///
/// <para><b>The region</b> is round, <see cref="L55Radius"/> cells, far out to the west-south-west, under the open sky.
/// Its rim cells are a cliff of rime-coated rock. The ground (<see cref="L55Column"/>) is a pure function of the block
/// position, measured from the hut's middle (<see cref="L55HutX"/>, <see cref="L55HutZ"/>): broad swells, a lattice of
/// snow dunes, thin ice ridges on the high swells, crevasses along the zero lines of a noise in a few crevasse fields,
/// and the frozen sea in the basins of another. The level's floor (rel 0) is the ice sheet's datum.</para>
///
/// <para><b>Tiles:</b> <see cref="Tile.Zone"/> 1 snowfield, 2 glacier (the high swells and the cave's dome), 3 crevasse,
/// 4 frozen sea, 5 the hut, 6 the ice cave (its tunnel, its chamber and the open cut in front), 9 the rim. On the snow and
/// the glacier <see cref="Tile.Height"/> is the ground's top and <see cref="Tile.Depth"/> how many snow layers lie on it
/// (0-3); in a crevasse Height is the top of its lips and Depth how far below that its floor lies; on the sea Depth is
/// how far below rel 0 the ice is; in the cave Height is the dome's top and Depth the rel of the cave's ceiling block (0 in
/// the open cut). <see cref="Tile.Detail"/> holds the <c>L55Flag*</c> bits.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2500-0x25BF are this level's (0x25C0-0x25FF its thresholds').</summary>
    private const ulong SaltL55Shape = 0x2501, SaltL55Centre = 0x2502, SaltL55Swell = 0x2503, SaltL55Hill = 0x2504, SaltL55Ridge = 0x2505,
        SaltL55Crevasse = 0x2506, SaltL55Field = 0x2507, SaltL55Bridge = 0x2508, SaltL55Basin = 0x2509, SaltL55Pressure = 0x250A,
        SaltL55Crust = 0x250B, SaltL55Cave = 0x250C, SaltL55Rough = 0x250D, SaltL55CrevDepth = 0x250E, SaltL55CrevWidth = 0x250F;

    /// <summary>The zones (<see cref="Tile.Zone"/>).</summary>
    public const byte L55Snow = 1, L55Glacier = 2, L55Crevasse = 3, L55Sea = 4, L55Hut = 5, L55Cave = 6, L55RimZone = 9;

    /// <summary>The bits of <see cref="Tile.Detail"/>.</summary>
    public const byte L55FlagBridge = 1, L55FlagCrust = 2, L55FlagSteep = 4, L55FlagCrevWall = 8, L55FlagSafe = 16, L55FlagMound = 32,
        L55FlagCaveWall = 64, L55FlagRidge = 128;

    /// <summary>The hut's floor above the datum, the cave's floor, and the highest the ground goes.</summary>
    public const int L55HutFloor = 1, L55CaveFloor = 2, L55Peak = 20;

    /// <summary>The hut's footprint (u east by v south, walls included), and its storey (the roof slab above its floor).</summary>
    public const int L55HutW = 20, L55HutD = 12, L55HutRoof = 5;

    /// <summary>How deep a crevasse's floor may go below the datum.</summary>
    public const int L55CrevasseBottom = -12;

    /// <summary>What a place in the hut is.</summary>
    public enum L55Part : byte { Outside, Wall, Door, Window, Room, Stove }

    /// <summary>The hut's furnishings.</summary>
    public enum L55Thing : byte { None, Lamp, BedHead, BedFoot, Table, Chair }

    /// <summary>One column of the ground, worked out from its block position alone.</summary>
    public struct L55Col
    {
        /// <summary>The top solid block's rel (a crevasse: its lips; the cave: its dome).</summary>
        public int Top;
        public byte Zone;
        /// <summary>Snow layers on top (snow and glacier), the cut below the lips (crevasse), the ice below rel 0 (sea), the ceiling block's rel (cave).</summary>
        public byte Depth;
        public byte Flags;
    }

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees south of west.</summary>
    private double L55Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L55CentreX => spawnMacroX - (int)Math.Round(L55Reach * Math.Cos(Math.PI / 8));
    private int L55CentreZ => spawnMacroZ + (int)Math.Round(L55Reach * Math.Sin(Math.PI / 8));

    /// <summary>The region's radius in macro cells: sixteen (512 blocks), whatever the world's size (as Level 73's).</summary>
    private int L55Radius => 16;

    private bool InL55(double mx, double mz) => InRoundRegion(mx, mz, L55CentreX, L55CentreZ, L55Radius, SaltL55Shape);

    /// <summary>The middle of the hut, in blocks: near the region's centre, moved a little by the seed.</summary>
    public int L55HutX => L55CentreX * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Hash(seed, 0, 0, SaltL55Centre)) * 33) - 16;
    public int L55HutZ => L55CentreZ * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Mix(Hashing.Hash(seed, 0, 0, SaltL55Centre))) * 33) - 16;

    /// <summary>The hut's north-west corner, in blocks.</summary>
    public int L55HutX0 => L55HutX - L55HutW / 2;
    public int L55HutZ0 => L55HutZ - L55HutD / 2;

    /// <summary>The stove's first block (against the hut's north wall).</summary>
    public (int X, int Z) L55Stove => (L55HutX0 + 9, L55HutZ0 + 1);

    /// <summary>The ice cave's chamber, in blocks: 120 to 160 blocks from the hut, in a direction the seed picks.</summary>
    public (int X, int Z) L55CaveCentre
    {
        get
        {
            ulong h = Hashing.Hash(seed, 1, 0, SaltL55Cave);
            double a = Hashing.Unit(h) * Math.PI * 2, r = 120 + 40 * Hashing.Unit(Hashing.Mix(h));
            return (L55HutX + (int)Math.Round(Math.Cos(a) * r), L55HutZ + (int)Math.Round(Math.Sin(a) * r));
        }
    }

    /// <summary>
    /// A place to look for somewhere to arrive: out on the ice 70 to 210 blocks from the hut (the spot test keeps it on safe
    /// snow, away from the crevasses).
    /// </summary>
    private (int Mx, int Mz) L55ArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = 70 + 140 * Hashing.Unit(Hashing.Mix(h));
        return (MacroOf(L55HutX + (int)Math.Round(Math.Cos(angle) * r)), MacroOf(L55HutZ + (int)Math.Round(Math.Sin(angle) * r)));
    }

    /// <summary>Arriving: on snow or the glacier's crust, on gentle ground, well away from any crevasse field.</summary>
    private static bool IsL55ArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone is L55Snow or L55Glacier && (t.Detail & L55FlagSafe) != 0 && (t.Detail & (L55FlagSteep | L55FlagMound)) == 0;

    /// <summary>How high above the level's floor to put someone down: on the snow (and any layer on it).</summary>
    private static double L55ArrivalHeight(in Tile t, double stand) => t.Height + stand + t.Depth / 8.0;

    // ================= The ice =================

    private static double L55Smooth(double t) => t * t * (3 - 2 * t);

    /// <summary>The dunes: low snow domes on a jittered lattice, the highest of those round a position (none near the hut).</summary>
    private double L55Dunes(double ux, double uz)
    {
        const int pitch = 48;
        int hi = (int)Math.Floor(ux / pitch), hj = (int)Math.Floor(uz / pitch);
        double best = 0;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                ulong h = Hashing.Hash(seed, hi + di, hj + dj, SaltL55Hill);
                if (Hashing.Unit(h) < 0.25) continue; // a gap in the dunes
                ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3);
                double cx = (hi + di + 0.2 + 0.6 * Hashing.Unit(h2)) * pitch, cz = (hj + dj + 0.2 + 0.6 * Hashing.Unit(h3)) * pitch;
                if (cx * cx + cz * cz < 60 * 60) continue;
                double radius = 14 + 14 * Hashing.Unit(h4), height = 2 + 5 * Hashing.Unit(Hashing.Mix(h4));
                double dx = ux - cx, dz = uz - cz, q = (dx * dx + dz * dz) / (radius * radius);
                if (q < 1) best = Math.Max(best, height * (1 - q));
            }
        return best;
    }

    /// <summary>
    /// The ground at a block position: the frozen sea in the basins; else the swells, dunes and roughness eased down to the
    /// shore, thin ridges on the high swells, levelled round the hut (with a drift against its north wall) and round the
    /// cave's dome; and crevasses cut along the zero lines of a noise inside the crevasse fields, some bridged with snow.
    /// The hut's own footprint is not decided here (see <see cref="L55HutAt"/>).
    /// </summary>
    public L55Col L55Column(int gx, int gz)
    {
        double ux = gx - L55HutX, uz = gz - L55HutZ, d = Math.Sqrt(ux * ux + uz * uz);
        var (kx, kz) = L55CaveCentre;
        double kdx = gx - kx, kdz = gz - kz, dk = Math.Sqrt(kdx * kdx + kdz * kdz);
        var col = new L55Col();

        // The sea in the basins, never near the hut or the cave
        double basin = Fbm(ux / 170.0, uz / 170.0, SaltL55Basin) + 0.6 * Math.Max(0, 1 - d / 140) + 0.6 * Math.Max(0, 1 - dk / 100);
        const double seaAt = -0.26;
        if (basin < seaAt)
        {
            col.Zone = L55Sea;
            if (basin > seaAt - 0.04) col.Depth = 1; // the shallows, a step down from the shore
            else if (Math.Abs(Noise(ux / 34.0, uz / 34.0, SaltL55Pressure)) < 0.03) col.Flags = L55FlagRidge; // a pressure ridge, to rel 0
            else col.Depth = 2;
            col.Top = -col.Depth;
            col.Flags |= L55FlagSafe;
            return col;
        }

        double coast = L55Smooth(Math.Clamp((basin - seaAt) / 0.12, 0, 1));
        double swell = 12 * L55Smooth(Math.Clamp((Fbm(ux / 90.0, uz / 90.0, SaltL55Swell) + 0.05) / 0.6, 0, 1));
        double f = (0.6 + swell + L55Dunes(ux, uz) + 0.8 * Fbm(ux / 20.0, uz / 20.0, SaltL55Rough)) * coast;
        // Thin ice ridges along the high swells
        if (swell > 5)
        {
            double n = Math.Abs(Noise(ux / 40.0, uz / 40.0, SaltL55Ridge));
            if (n < 0.06) f += 4 * (1 - n / 0.06) * Math.Min(1, (swell - 5) / 2);
        }
        // Levelled round the hut, a drift against its north wall
        if (d < 50)
        {
            double s = L55Smooth(Math.Clamp((d - 30) / 20.0, 0, 1));
            f = L55HutFloor * (1 - s) + f * s;
            int u = gx - L55HutX0, v = gz - L55HutZ0;
            if (v is >= -5 and <= -1 && u is >= -1 and <= L55HutW) f = Math.Max(f, L55HutFloor + 3.4 * (1 + (v + 1) / 5.0));
        }
        // Levelled round the cave, and its dome of blue ice
        bool mound = false;
        if (dk < 70)
        {
            double s = L55Smooth(Math.Clamp((dk - 50) / 20.0, 0, 1));
            f = L55CaveFloor * (1 - s) + f * s;
            if (dk < 46)
            {
                f = Math.Max(f, L55CaveFloor + 15 * (1 - dk * dk / (46.0 * 46.0)));
                mound = dk < 44;
            }
        }
        f = Math.Clamp(f, 0, L55Peak);
        int g = (int)Math.Round(f);
        col.Top = g;
        col.Zone = swell > 6 || g >= 8 || mound ? L55Glacier : L55Snow;
        if (mound) col.Flags |= L55FlagMound;
        else if (f > g) col.Depth = (byte)Math.Min(3, (int)((f - g) * 8)); // snow layers soften the steps
        if (Noise(ux / 9.0, uz / 9.0, SaltL55Crust) > (col.Zone == L55Glacier ? 0.1 : 0.45)) { col.Flags |= L55FlagCrust; col.Depth = 0; }

        // The ice cave: its chamber, its tunnel, and the cut in front of it
        if (dk < 50 && L55CaveAt(gx, gz, out int ceiling))
        {
            col.Zone = L55Cave;
            col.Depth = 0;
            col.Flags = (byte)(col.Flags & L55FlagMound);
            if (ceiling + 2 <= g) col.Depth = (byte)ceiling;
            else col.Top = L55CaveFloor;
            return col;
        }

        // Crevasses: along the zero lines of a noise, in the crevasse fields, well inland and away from the hut and the cave
        double field = Fbm(ux / 150.0, uz / 150.0, SaltL55Field);
        if (field < -0.2 && d > 40 && dk > 50) col.Flags |= L55FlagSafe;
        double inland = Math.Clamp((basin - seaAt - 0.12) / 0.08, 0, 1);
        if (field > 0.1 && d > 45 && dk > 60 && inland > 0)
        {
            double taper = Math.Min(1, (field - 0.1) / 0.12) * inland;
            double w = (0.03 + 0.03 * (0.5 + 0.5 * Noise(ux / 80.0, uz / 80.0, SaltL55CrevWidth))) * taper;
            double n = Math.Abs(Noise(ux / 55.0, uz / 55.0, SaltL55Crevasse));
            if (n < w)
            {
                double depth = (6 + 6 * (0.5 + 0.5 * Noise(ux / 30.0, uz / 30.0, SaltL55CrevDepth))) * (0.7 + 0.3 * (1 - n / w)) * (0.5 + 0.5 * taper);
                int cut = Math.Clamp((int)Math.Round(depth), 3, g - L55CrevasseBottom);
                col.Zone = L55Crevasse;
                col.Depth = (byte)cut;
                col.Flags = Noise(ux / 7.0, uz / 7.0, SaltL55Bridge) > 0.15 ? L55FlagBridge : (byte)0;
            }
        }
        return col;
    }

    /// <summary>
    /// Whether a block position is in the ice cave (its chamber, round, about nineteen blocks across; its tunnel, five wide,
    /// winding out toward the hut), and the rel of the ceiling block over it there.
    /// </summary>
    public bool L55CaveAt(int gx, int gz, out int ceiling)
    {
        var (kx, kz) = L55CaveCentre;
        double px = gx - kx, pz = gz - kz;
        double r2 = px * px + pz * pz;
        ceiling = 0;
        if (r2 > 50 * 50) return false;
        if (r2 <= 81)
        {
            ceiling = L55CaveFloor + 5 + (int)Math.Round(3 * (1 - r2 / 81));
            return true;
        }
        // Along the tunnel: s out from the chamber toward the hut, t across it
        double ex = L55HutX - kx, ez = L55HutZ - kz, el = Math.Sqrt(ex * ex + ez * ez);
        ex /= el; ez /= el;
        double s = px * ex + pz * ez, t = -px * ez + pz * ex;
        if (s < 0 || s > 48) return false;
        double wind = 3.5 * Noise(s / 14.0, 0.5, SaltL55Cave) * Math.Min(1, s / 12);
        if (Math.Abs(t - wind) > 2.5) return false;
        ceiling = L55CaveFloor + 6;
        return true;
    }

    /// <summary>Whether a position lies in the cave's roofed part (its tunnel or chamber, under the ice), below its ceiling.</summary>
    public bool InL55Cave(int gx, int gz, double rel)
    {
        if (!L55CaveAt(gx, gz, out int ceiling) || rel <= L55CaveFloor || rel >= ceiling) return false;
        L55Col c = L55Column(gx, gz);
        return c.Zone == L55Cave && c.Depth > 0;
    }

    // ================= The hut =================

    /// <summary>What a hut-local position (u east, v south of its north-west corner) is.</summary>
    public static L55Part L55HutAt(int u, int v)
    {
        if (u < 0 || v < 0 || u >= L55HutW || v >= L55HutD) return L55Part.Outside;
        bool ring = u == 0 || v == 0 || u == L55HutW - 1 || v == L55HutD - 1;
        if (ring)
        {
            if (v == L55HutD - 1 && u is 9 or 10) return L55Part.Door;
            if ((u == 0 || u == L55HutW - 1) && v is 5 or 6) return L55Part.Window;
            if (v == L55HutD - 1 && u is 4 or 15) return L55Part.Window;
            return L55Part.Wall;
        }
        if (v == 1 && u is 9 or 10) return L55Part.Stove;
        return L55Part.Room;
    }

    /// <summary>The hut's furnishings, hut-local, with the way each faces.</summary>
    private static readonly Dictionary<(int, int), (L55Thing Thing, ArchPier Facing)> L55Furnishings = PlanL55Furnishings();

    private static Dictionary<(int, int), (L55Thing, ArchPier)> PlanL55Furnishings()
    {
        var f = new Dictionary<(int, int), (L55Thing, ArchPier)>();
        void Put(int u, int v, L55Thing thing, ArchPier facing) => f[(u, v)] = (thing, facing);
        // Two bunks along the west wall (a bed's facing points head to foot)
        foreach (int v in new[] { 2, 8 })
        {
            Put(1, v, L55Thing.BedHead, ArchPier.East);
            Put(2, v, L55Thing.BedFoot, ArchPier.East);
        }
        // A table with four chairs
        Put(13, 5, L55Thing.Table, ArchPier.North);
        Put(13, 4, L55Thing.Chair, ArchPier.South);
        Put(13, 6, L55Thing.Chair, ArchPier.North);
        Put(12, 5, L55Thing.Chair, ArchPier.East);
        Put(14, 5, L55Thing.Chair, ArchPier.West);
        // Four lamps, one on each wall
        Put(1, 4, L55Thing.Lamp, ArchPier.East);
        Put(18, 3, L55Thing.Lamp, ArchPier.West);
        Put(5, 1, L55Thing.Lamp, ArchPier.South);
        Put(15, 10, L55Thing.Lamp, ArchPier.North);
        return f;
    }

    /// <summary>What stands at a hut-local position, and which way it faces.</summary>
    public static (L55Thing Thing, ArchPier Facing) L55FurnishingAt(int u, int v) =>
        L55Furnishings.TryGetValue((u, v), out var f) ? f : (L55Thing.None, ArchPier.North);

    /// <summary>Whether a block position is inside the hut's square (its walls included).</summary>
    public bool InL55Hut(int gx, int gz) => L55HutAt(gx - L55HutX0, gz - L55HutZ0) != L55Part.Outside;

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the ice is laid out tile by tile).</summary>
    private Edge L55Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L55Wall };

    /// <summary>Lays out one of the level's cells: the rim's cliff, or the ice, the hut and the cave, tile by tile.</summary>
    private void BuildLevel55(Builder b, int mx, int mz)
    {
        // The rim: a cliff of rime-coated rock all the way round
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Level55) { rim = true; break; }
        if (rim)
        {
            for (int lz = 0; lz < MacroSize; lz++)
                for (int lx = 0; lx < MacroSize; lx++)
                    b.At(lx, lz) = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L55Wall, Floor = FloorKind.L55Floor, Zone = L55RimZone };
            return;
        }

        // The ground of the cell and a block round it (for slopes and crevasse lips)
        const int n = MacroSize + 2;
        int x0 = mx * MacroSize - 1, z0 = mz * MacroSize - 1;
        var cols = new L55Col[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
                cols[j * n + i] = L55Column(x0 + i, z0 + j);

        int hx0 = L55HutX0, hz0 = L55HutZ0;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                L55Part part = L55HutAt(gx - hx0, gz - hz0);
                if (part != L55Part.Outside)
                {
                    t = L55HutTile(part);
                    continue;
                }
                L55Col c = cols[(lz + 1) * n + lx + 1];
                byte flags = c.Flags;
                if (c.Zone is L55Snow or L55Glacier)
                {
                    int steep = 0;
                    bool lip = false, cave = false;
                    for (int dz = -1; dz <= 1; dz++)
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            L55Col o = cols[(lz + 1 + dz) * n + lx + 1 + dx];
                            cave |= o.Zone == L55Cave;
                            if (dx != 0 && dz != 0) continue;
                            if (o.Zone is L55Snow or L55Glacier) steep = Math.Max(steep, Math.Abs(o.Top - c.Top));
                            lip |= o.Zone == L55Crevasse;
                        }
                    if (steep >= 2) { flags |= L55FlagSteep; c.Depth = 0; }
                    if (lip) flags |= L55FlagCrevWall;
                    if (cave) flags |= L55FlagCaveWall;
                }
                t = new Tile
                {
                    Kind = TileKind.Floor, Floor = FloorKind.L55Floor, Zone = c.Zone, Height = (byte)Math.Max(0, c.Top), Depth = c.Depth, Detail = flags,
                };
            }
    }

    private static Tile L55HutTile(L55Part part)
    {
        var t = new Tile { Height = L55HutFloor, Zone = L55Hut, Floor = FloorKind.L55Floor };
        switch (part)
        {
            case L55Part.Room: t.Kind = TileKind.Floor; break;
            case L55Part.Stove: t.Kind = TileKind.Floor; t.Sealed = true; break; // nobody is put down in the stove
            case L55Part.Door: t.Kind = TileKind.Doorway; t.Pattern = WallPattern.L55Wall; break;
            default: t.Kind = TileKind.Wall; t.Pattern = WallPattern.L55Wall; break;
        }
        return t;
    }

    /// <summary>Which of the level's props (<see cref="Props.L55First"/>-<see cref="Props.L55Last"/>) people walk through: none (it has none).</summary>
    private static bool L55WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: deadly cold out on the ice, a little less so in the cave; warm in the hut, warmer by its stove.</summary>
    private float L55Temperature(int x, int y, int z, int floorY)
    {
        int rel = y - floorY;
        if (InL55Hut(x, z) && rel > L55HutFloor && rel <= L55HutFloor + L55HutRoof)
        {
            var (sx, sz) = L55Stove;
            int dx = x - sx, dz = z - sz;
            return dx >= -3 && dx <= 4 && dz <= 3 ? 24f : 18f;
        }
        if (InL55Cave(x, z, rel)) return 4f;
        return -15f;
    }

    /// <summary>Reality stability: a slow drain out on the ice; none in the hut.</summary>
    private float L55Stability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        return t.Zone == L55Hut ? 1f : 0.9f;
    }
}
