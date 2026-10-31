using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 73, "The Redlands" (experimental): kept as level 21 (<see cref="Level73"/>) and shown as "73". One island of
/// crimson-black ground in a dark sea, under a night that never ends and a full moon that never moves; on its highest
/// point the Silver Castle, the only building and the only safe place. The design is in
/// docs/design/experimental-levels/73-plan.md (after the Wikidot page by Kitty Rika). Still unlinked: no thresholds in or
/// out (the cheats menu or <c>/backrooms goto</c> only); its hordes come from the director, its guardian Coran and the
/// castle's door, table and baths from Regions.L73System.
///
/// <para><b>The region</b> is round, <see cref="L73Radius"/> cells, far out to the north-north-west (the mirror of
/// Level 188's), under the open sky. Its rim cells are a cliff of black rock round the sea. The island (centre
/// <see cref="L73IslandX"/>, <see cref="L73IslandZ"/>, radius about <see cref="L73IslandRadius"/>) is a pure function of
/// the block position (<see cref="L73Ground"/>): a low dome, a scatter of hills, red gullies, an ash beach, and the sea
/// falling to six blocks deep beyond it, with old bones and the odd lost pack strewn on the fields. The level's floor is the sea's surface: a land tile's <see cref="Tile.Height"/>
/// is its ground above it, a sea tile's <see cref="Tile.Depth"/> how far down its bed lies.</para>
///
/// <para><b>The castle</b> (<see cref="L73CastleAt"/>, castle-local u east, v south from <see cref="L73CastleX0"/>,
/// <see cref="L73CastleZ0"/>) stands level on the summit plateau (<see cref="L73Plateau"/>): a curtain wall with four
/// corner towers, a gatehouse in the south wall, a stone path to the keep's door, and the keep: on the ground storey the
/// lore's three floors (<see cref="L73RoomAt"/>, storeys of <see cref="L73Storey"/>): on each a guest room at either
/// end of the south side with two beds; the main hall and the dining hall with its hearth and its table of plenty, a
/// bathroom and a gallery of paintings on the ground floor; a sitting room, the second bathroom and a library above; the
/// master bedroom and a store-room on the third; a flat roof with a parapet and turrets, and on it the attic (shut:
/// off-limits) under a slate roof, with its balcony over the front door. Every window is boarded and curtained in red
/// velvet; banners of a silver heart with ram's horns hang on the walls. The door opens only to banging.</para>
///
/// <para><b>Tiles:</b> <see cref="Tile.Zone"/> 1 land, 2 sea, 3 the courtyard (and its path and gate), 4 the keep's
/// inside, 5 the castle's walls, 9 the rim.</para>
/// </summary>
public sealed partial class WorldLayout
{
    /// <summary>Hash salts 0x2100-0x21BF are this level's (0x21C0-0x21FF its thresholds').</summary>
    private const ulong SaltL73Shape = 0x2101, SaltL73Centre = 0x2102, SaltL73Coast = 0x2103, SaltL73Hill = 0x2104, SaltL73Rough = 0x2105,
        SaltL73Gully = 0x2106, SaltL73Outcrop = 0x2107, SaltL73Bed = 0x2108, SaltL73Bones = 0x2109, SaltL73Tor = 0x210A,
        SaltL73Burnt = 0x210B, SaltL73Crust = 0x210E, SaltL73Jag = 0x2111;

    /// <summary>The zones (<see cref="Tile.Zone"/>).</summary>
    public const byte L73Land = 1, L73Sea = 2, L73Court = 3, L73Keep = 4, L73Walls = 5, L73RimZone = 9;

    /// <summary>The summit plateau's ground above the sea (the castle's floor), and the highest any other ground goes.</summary>
    public const int L73Plateau = 9, L73Peak = 12;

    /// <summary>The highest a tor of black rock stands above the sea (a little under the curtain wall's top).</summary>
    public const int L73TorPeak = 17;

    /// <summary>The island's average radius in blocks (its coast wanders a fifth either way).</summary>
    public const int L73IslandRadius = 230;

    /// <summary>The castle's square (u by v), and the keep in it (from its own corner, u by v).</summary>
    public const int L73CastleW = 56, L73CastleD = 48, L73KeepU0 = 10, L73KeepV0 = 6, L73KeepW = 36, L73KeepD = 24;

    /// <summary>
    /// The keep's heights above its floor: each storey is <see cref="L73Storey"/> blocks, floor slab to floor slab (four
    /// of air), three of them; the roof terrace's slab (the attic's floor; the attic's walls are three high over it), and the
    /// ridge of the attic's slate roof, one under the top of the band the level is lit over (a lit top layer leaks sunlight).
    /// </summary>
    public const int L73Storey = 5, L73Terrace = 15, L73AtticTop = 23;

    /// <summary>What a place in the castle is on the ground (the keep's inside is <see cref="L73RoomAt"/>'s).</summary>
    public enum L73Part : byte { Outside, Court, Path, Gate, Curtain, Tower, GateTower, Keep }

    /// <summary>The keep's rooms, by storey (<see cref="L73RoomAt"/>).</summary>
    public enum L73Room : byte { Wall, Hall, Dining, Gallery, Bath, Guest, Sitting, Library, Landing, Master, Store }

    /// <summary>The castle's furnishings.</summary>
    public enum L73Thing : byte
    {
        None, Sconce, Chandelier, Bookshelf, Clock, Candelabra, Table, Chair, BedHead, BedFoot, Nightstand, Wardrobe, Toilet,
        Bath, Painting, Banner, SofaLeft, SofaRight, Desk, RoundTable, Dresser, Box, Crate, Bones, Ribcage, Skull, Pack, Note,
    }

    /// <summary>Which layer of a tile a furnishing takes: the floor, the wall behind it (at eye height), or the ceiling.</summary>
    public enum L73Layer : byte { Floor, Wall, Ceiling }

    // ================= Where it is =================

    /// <summary>How far from spawn the region's centre lies: 1.1 times the city's distance, 22.5 degrees west of north.</summary>
    private double L73Reach => RegionReach * 1.1;

    /// <summary>The region's centre, in macro cells.</summary>
    private int L73CentreX => spawnMacroX - (int)Math.Round(L73Reach * Math.Sin(Math.PI / 8));
    private int L73CentreZ => spawnMacroZ - (int)Math.Round(L73Reach * Math.Cos(Math.PI / 8));

    /// <summary>The region's radius in macro cells: sixteen (512 blocks), whatever the world's size: the island and its sea.</summary>
    private int L73Radius => 16;

    private bool InL73(double mx, double mz) => InRoundRegion(mx, mz, L73CentreX, L73CentreZ, L73Radius, SaltL73Shape);

    /// <summary>The middle of the island (and of the castle), in blocks: near the region's centre, moved a little by the seed.</summary>
    public int L73IslandX => L73CentreX * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Hash(seed, 0, 0, SaltL73Centre)) * 33) - 16;
    public int L73IslandZ => L73CentreZ * MacroSize + MacroSize / 2 + (int)(Hashing.Unit(Hashing.Mix(Hashing.Hash(seed, 0, 0, SaltL73Centre))) * 33) - 16;

    /// <summary>The castle's north-west corner, in blocks.</summary>
    public int L73CastleX0 => L73IslandX - L73CastleW / 2;
    public int L73CastleZ0 => L73IslandZ - L73CastleD / 2;

    /// <summary>The middle of the gate, in blocks (in the south wall).</summary>
    public (int X, int Z) L73Gate => (L73CastleX0 + 28, L73CastleZ0 + L73CastleD - 1);

    /// <summary>The keep's door, in blocks (its west leaf; the east leaf is one east of it), in the keep's south wall.</summary>
    public (int X, int Z) L73Door => (L73CastleX0 + L73KeepU0 + 17, L73CastleZ0 + L73KeepV0 + L73KeepD - 1);

    /// <summary>The hearth in the dining hall, in blocks (its first fire tile).</summary>
    public (int X, int Z) L73Hearth => (L73CastleX0 + L73KeepU0 + 17, L73CastleZ0 + L73KeepV0 + 1);

    /// <summary>
    /// A place to look for somewhere to arrive: out on the island 60 to 120 blocks from the gate (a short run, for whoever
    /// does not stop), the castle on its hill in sight (the spot test keeps it on dry land).
    /// </summary>
    private (int Mx, int Mz) L73ArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, r = 60 + 60 * Hashing.Unit(Hashing.Mix(h));
        var (gx, gz) = L73Gate;
        return (MacroOf(gx + (int)Math.Round(Math.Cos(angle) * r)), MacroOf(gz + (int)Math.Round(Math.Sin(angle) * r)));
    }

    /// <summary>Arriving: on the island's dry ground, above the beach, never in a gully or the castle.</summary>
    private static bool IsL73ArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Zone == L73Land && t.Height >= 2 && t.Floor is not (FloorKind.L73Mud or FloorKind.L73Tor);

    /// <summary>How high above the level's floor (the sea) to put someone down: on the ground.</summary>
    private static double L73ArrivalHeight(in Tile t, double stand) => t.Height + stand;

    // ================= The island =================

    private static double L73Smooth(double t) => t * t * (3 - 2 * t);

    /// <summary>How far a block position lies beyond the coast (negative inland), and its distance from the island's middle.</summary>
    public double L73Shore(int gx, int gz, out double d)
    {
        double ux = gx - L73IslandX, uz = gz - L73IslandZ;
        d = Math.Sqrt(ux * ux + uz * uz);
        return d - L73IslandRadius * (1 + 0.2 * Fbm(ux / 120.0, uz / 120.0, SaltL73Coast));
    }

    /// <summary>The hills: low domes on a jittered lattice, the highest of those round a position (none near the castle).</summary>
    private double L73Hills(double ux, double uz)
    {
        const int pitch = 34;
        int hi = (int)Math.Floor(ux / pitch), hj = (int)Math.Floor(uz / pitch);
        double best = 0;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                ulong h = Hashing.Hash(seed, hi + di, hj + dj, SaltL73Hill);
                if (Hashing.Unit(h) < 0.2) continue; // a gap in the hills
                ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3);
                double cx = (hi + di + 0.2 + 0.6 * Hashing.Unit(h2)) * pitch, cz = (hj + dj + 0.2 + 0.6 * Hashing.Unit(h3)) * pitch;
                if (cx * cx + cz * cz < 90 * 90) continue;
                double radius = 10 + 12 * Hashing.Unit(h4), height = 2.5 + 4 * Hashing.Unit(Hashing.Mix(h4));
                double dx = ux - cx, dz = uz - cz, q = (dx * dx + dz * dz) / (radius * radius);
                if (q < 1) best = Math.Max(best, height * (1 - q));
            }
        return best;
    }

    /// <summary>
    /// The tors: crags of black rock standing up out of the fields on a jittered lattice, a jagged core with a spur or two
    /// beside it, how high one stands above the ground at a position (0 where there is none). None near the castle's hill or
    /// along the stone path's line down from the gate, and none on the beach (the coast factor is applied by the caller).
    /// </summary>
    private double L73Tor(double ux, double uz, int gx, int gz)
    {
        const int pitch = 26;
        int ti = (int)Math.Floor(ux / pitch), tj = (int)Math.Floor(uz / pitch);
        double best = 0;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                ulong h = Hashing.Hash(seed, ti + di, tj + dj, SaltL73Tor);
                if (Hashing.Unit(h) < 0.5) continue;
                ulong h2 = Hashing.Mix(h), h3 = Hashing.Mix(h2), h4 = Hashing.Mix(h3), h5 = Hashing.Mix(h4);
                double cx = (ti + di + 0.15 + 0.7 * Hashing.Unit(h2)) * pitch, cz = (tj + dj + 0.15 + 0.7 * Hashing.Unit(h3)) * pitch;
                if (cx * cx + cz * cz < 78 * 78) continue;
                // (the path's line: the gate is at the castle's south, the path running on south from it)
                if (Math.Abs(cx) < 12 && cz > 0) continue;
                double radius = 1.6 + 2.2 * Hashing.Unit(h4), height = 3 + 5 * Hashing.Unit(h5);
                // The core, and a lower spur off to one side
                double a = Hashing.Unit(Hashing.Mix(h5)) * Math.PI * 2;
                for (int part = 0; part < 2; part++)
                {
                    double px = cx + (part == 0 ? 0 : Math.Cos(a) * radius * 1.4), pz = cz + (part == 0 ? 0 : Math.Sin(a) * radius * 1.4);
                    double pr = part == 0 ? radius : radius * 0.6, ph = part == 0 ? height : height * 0.55;
                    double dx = ux - px, dz = uz - pz, q = (dx * dx + dz * dz) / (pr * pr);
                    if (q >= 1) continue;
                    double jag = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL73Jag)) * 1.6 - 0.6;
                    best = Math.Max(best, ph * Math.Sqrt(1 - q) + jag);
                }
            }
        return best;
    }

    /// <summary>
    /// The ground at a block position, in blocks above the sea (negative under it), and what it is made of: the island's
    /// dome, its hills and roughness, eased down to the beach over its last forty blocks; the summit level for the
    /// castle (flat within forty blocks of the middle, eased into the hills over the next twenty-two); gullies cut along
    /// the zero lines of a noise; and beyond the coast the seabed, falling to six blocks deep.
    /// </summary>
    public int L73Ground(int gx, int gz, out FloorKind floor)
    {
        double beyond = L73Shore(gx, gz, out double d), ri = d - beyond;
        double ux = gx - L73IslandX, uz = gz - L73IslandZ;
        double f;
        bool gully = false;
        if (beyond < 0)
        {
            double t = 1 - d / ri;
            double dome = 8.5 * Math.Pow(Math.Max(0, t), 0.7);
            double rough = 1.8 * Fbm(ux / 22.0, uz / 22.0, SaltL73Rough);
            double coast = L73Smooth(Math.Clamp(-beyond / 40.0, 0, 1));
            f = 1 + (dome + L73Hills(ux, uz) + rough) * coast;
            // The summit, levelled for the castle
            if (d < 62)
            {
                double s = L73Smooth(Math.Clamp((d - 40) / 22.0, 0, 1));
                f = L73Plateau * (1 - s) + f * s;
            }
            // Gullies of red mud, along the zero lines of a noise, away from the summit and the beach
            else if (f > 3.5)
            {
                double n = Math.Abs(Noise(ux / 55.0, uz / 55.0, SaltL73Gully));
                if (n < 0.07)
                {
                    double cut = 3 * (1 - n / 0.07);
                    f -= cut;
                    gully = cut > 0.8;
                }
            }
        }
        else f = 0.6 - 6.6 * L73Smooth(Math.Clamp(beyond / 90.0, 0, 1));
        int g = Math.Clamp((int)Math.Round(f), -6, L73Peak);

        // A tor of black rock standing up out of the ground (inland, off the gullies)
        if (beyond < -30 && !gully && g >= 2 && L73Tor(ux, uz, gx, gz) is var tor and >= 1)
        {
            floor = FloorKind.L73Tor;
            return Math.Min(L73TorPeak, g + (int)Math.Round(tor));
        }
        if (g < 0) floor = Noise(gx / 14.0, gz / 14.0, SaltL73Bed) > 0.2 ? FloorKind.L73Gravel : FloorKind.L73Seabed;
        else if (g <= 1) floor = FloorKind.L73Ash;
        else if (gully) floor = FloorKind.L73Mud;
        else if (g >= 11 || Noise(gx / 9.0, gz / 9.0, SaltL73Outcrop) > 0.55) floor = FloorKind.L73Rock;
        // The fields: crimson earth in broad blackened stretches ("blackened fields"), and here and there a crust of
        // dried blood, cracked into plates; a fringe of the crust round the gullies
        else if (Fbm(ux / 46.0, uz / 46.0, SaltL73Burnt) > 0.12) floor = Noise(gx / 7.0, gz / 7.0, SaltL73Crust) > 0.62 ? FloorKind.L73Crust : FloorKind.L73Burnt;
        else if (Noise(gx / 11.0, gz / 11.0, SaltL73Crust) > 0.56 || (d >= 62 && f > 3.5 && Math.Abs(Noise(ux / 55.0, uz / 55.0, SaltL73Gully)) < 0.1))
            floor = FloorKind.L73Crust;
        else floor = FloorKind.L73Floor;
        return g;
    }

    /// <summary>
    /// The dead grass on the fields at a land position (0 none, 1 short, 2 knee high, 3 tall): the red earth grows it in
    /// broad patches, thick in places; the blackened stretches only a burnt stubble, here and there; the crust of blood,
    /// rock, mud and beach nothing.
    /// </summary>
    public int L73GrassAt(int gx, int gz, FloorKind floor)
    {
        if (floor is not (FloorKind.L73Floor or FloorKind.L73Burnt)) return 0;
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL73Bones + 0x10));
        if (floor == FloorKind.L73Burnt) return r < 0.07 ? 1 : 0;
        double patch = Fbm(gx / 19.0, gz / 19.0, SaltL73Burnt + 3);
        double p = Math.Clamp(0.06 + (patch + 0.1) * 1.0, 0.03, 0.6);
        if (r >= p) return 0;
        double tall = Hashing.Unit(Hashing.Mix(Hashing.Hash(seed, gx, gz, SaltL73Bones + 0x10)));
        return patch > 0.3 && tall < 0.3 ? 3 : tall < 0.55 ? 2 : 1;
    }

    // ================= The Great Hound =================

    /// <summary>The Great Hound's skeleton's length (east to west, skull at the west), half its width, and its height.</summary>
    public const int L73HoundLength = 39, L73HoundHalf = 6, L73HoundHeight = 8;

    /// <summary>
    /// The bones of the Great Hound, which Coran killed (the lore names it; that its bones lie on the fields south-east of
    /// the castle is this mod's), skeleton-local: x along the spine from the tip of the snout (east), z across (-6 to 6),
    /// h above the ground it lies on (1 up). It lies on its belly: the skull, the neck, the spine arched over a cage of ribs
    /// that reach down to the ground either side (two broken), the pelvis, the legs stretched out flat, the tail.
    /// </summary>
    private static readonly HashSet<(int X, int Z, int H)> L73HoundBones = PlanL73Hound();

    private static HashSet<(int, int, int)> PlanL73Hound()
    {
        var b = new HashSet<(int, int, int)>();
        // The skull: a long snout with the jaw a little open, the cranium hollow behind its eye sockets
        for (int x = 0; x <= 6; x++)
            for (int z = -2; z <= 2; z++)
                for (int h = 1; h <= 4; h++)
                {
                    bool snout = x <= 2 && Math.Abs(z) <= 1 && h <= 3 && !(h == 2 && x <= 1); // (the gape between the jaws)
                    bool cranium = x >= 3 && !(Math.Abs(z) <= 1 && h is 2 or 3 && x is 4 or 5) // hollow
                        && !(x == 3 && h == 3 && Math.Abs(z) == 2) // the eye sockets
                        && !(h == 4 && Math.Abs(z) == 2);
                    if (snout || cranium) b.Add((x, z, h));
                }
        // The neck, rising to the spine
        for (int x = 7; x <= 9; x++) b.Add((x, 0, 3 + (x - 7) / 2 + 1));
        // The spine, arched over the ribs, a spur standing up from every other vertebra
        int Spine(int x) => x is >= 14 and <= 24 ? 7 : x is >= 11 and <= 27 ? 6 : 5;
        for (int x = 10; x <= 28; x++)
        {
            b.Add((x, 0, Spine(x)));
            if (x % 2 == 0 && x <= 26) b.Add((x, 0, Spine(x) + 1));
        }
        // The ribs, in pairs, curving out and down to the ground; one broken off on the north side, one on the south
        for (int x = 12; x <= 24; x += 2)
            foreach (int side in new[] { -1, 1 })
            {
                if (x == 18 && side < 0 || x == 22 && side > 0) continue;
                int top = Spine(x);
                for (int k = 0; k <= 24; k++)
                {
                    double a = k / 24.0 * Math.PI / 2;
                    int z = (int)Math.Round(5.5 * Math.Sin(a)), h = (int)Math.Round(1 + (top - 1) * Math.Cos(a));
                    if (z == 0) continue;
                    b.Add((x, side * z, h));
                }
            }
        // The pelvis
        for (int x = 27; x <= 29; x++)
            for (int z = -2; z <= 2; z++)
                if (Math.Abs(z) == 2 || x == 28) b.Add((x, z, 4));
        // The legs, stretched out flat: the forelegs forward of the ribs, the hind legs from the pelvis back
        for (int x = 7; x <= 12; x++) { b.Add((x, -4 - (12 - x) / 3, 1)); b.Add((x, 4 + (12 - x) / 3, 1)); }
        for (int x = 28; x <= 34; x++) { b.Add((x, -3 - (x - 28) / 3, 1)); b.Add((x, 3 + (x - 28) / 3, 1)); }
        b.Add((6, -6, 1)); b.Add((6, 6, 1)); b.Add((35, -5, 1)); b.Add((35, 5, 1)); // (paws)
        // The tail, falling to the ground
        for (int x = 30; x < L73HoundLength; x++) b.Add((x, (x - 30) / 4, Math.Max(1, 4 - (x - 30) / 2)));
        return b;
    }

    /// <summary>
    /// Where the Great Hound lies (its snout's tip, block coordinates) and the ground it lies on above the sea: on the fields
    /// south-east of the castle, a little off the path, in sight of anyone coming up it; its ground the lowest of a few
    /// samples under it, so no bone floats (where the ground rises, it has sunk in).
    /// </summary>
    public (int X, int Z, int Ground) L73Hound
    {
        get
        {
            // (Worked out once; a reference is swapped in whole, so any thread reads all of it or none)
            if (l73Hound is { } known) return (known.Item1, known.Item2, known.Item3);
            int x0 = L73IslandX + 20, z0 = L73IslandZ + 64;
            int ground = int.MaxValue;
            foreach (var (dx, dz) in new[] { (0, 0), (8, 0), (19, -5), (19, 5), (19, 0), (30, 0), (38, 0), (10, -5), (10, 5), (30, -4), (30, 4) })
            {
                int g = L73Ground(x0 + dx, z0 + dz, out FloorKind f);
                if (f != FloorKind.L73Mud) ground = Math.Min(ground, g);
            }
            if (ground == int.MaxValue) ground = L73Ground(x0, z0, out _);
            l73Hound = Tuple.Create(x0, z0, ground);
            return (x0, z0, ground);
        }
    }
    private volatile Tuple<int, int, int> l73Hound;

    /// <summary>Whether a block column lies under the Great Hound (its footprint, one round).</summary>
    public bool InL73Hound(int gx, int gz)
    {
        var (x0, z0, _) = L73Hound;
        int x = gx - x0, z = gz - z0;
        return x >= -1 && x <= L73HoundLength && Math.Abs(z) <= L73HoundHalf + 1;
    }

    /// <summary>Whether there is a bone of the Great Hound at a block position (rel above the sea).</summary>
    public bool L73HoundBoneAt(int gx, int gz, int rel)
    {
        var (x0, z0, ground) = L73Hound;
        return L73HoundBones.Contains((gx - x0, gz - z0, rel - ground));
    }

    // ================= The castle =================

    /// <summary>What a castle-local position is on the ground (Outside beyond the castle's square).</summary>
    public static L73Part L73CastleAt(int u, int v)
    {
        if (u < 0 || v < 0 || u >= L73CastleW || v >= L73CastleD) return L73Part.Outside;
        bool gateway = u >= 26 && u <= 29;
        if (v >= L73CastleD - 2 && gateway) return L73Part.Gate;
        if ((u < 6 || u >= L73CastleW - 6) && (v < 6 || v >= L73CastleD - 6)) return L73Part.Tower;
        if (v >= L73CastleD - 5 && (u is >= 22 and <= 25 || u is >= 30 and <= 33)) return L73Part.GateTower;
        if (u < 2 || v < 2 || u >= L73CastleW - 2 || v >= L73CastleD - 2) return L73Part.Curtain;
        int ku = u - L73KeepU0, kv = v - L73KeepV0;
        if (ku >= 0 && kv >= 0 && ku < L73KeepW && kv < L73KeepD) return L73Part.Keep;
        return gateway && v >= L73KeepV0 + L73KeepD ? L73Part.Path : L73Part.Court;
    }

    /// <summary>Whether a keep-local position is on the keep's outer wall.</summary>
    public static bool L73KeepRing(int ku, int kv) => ku == 0 || kv == 0 || ku == L73KeepW - 1 || kv == L73KeepD - 1;

    /// <summary>
    /// The keep's rooms on a storey (0 the ground floor, 1, 2), keep-local: a cross wall at kv 11 and two at ku 9 and 26
    /// cut it into six. South: a guest room at each end (the lore's "two guest rooms per floor, one on each side") and in the
    /// middle the main hall below, the landings above. North: the dining hall (its hearth on the north wall), the sitting
    /// room and the master bedroom (which takes the east end too) in the middle; west a bathroom on the two lower storeys
    /// and the store-room on the third; east the gallery of paintings and the library. The chimney rises through the upper
    /// storeys over the hearth.
    /// </summary>
    public static L73Room L73RoomAt(int ku, int kv, int storey)
    {
        if (ku <= 0 || kv <= 0 || ku >= L73KeepW - 1 || kv >= L73KeepD - 1 || kv == 11 || ku == 9) return L73Room.Wall;
        bool north = kv < 11;
        if (ku == 26 && !(storey == 2 && north)) return L73Room.Wall;
        if (storey > 0 && kv == 1 && ku is >= 16 and <= 19) return L73Room.Wall; // the chimney
        if (ku < 9) return north ? (storey == 2 ? L73Room.Store : L73Room.Bath) : L73Room.Guest;
        if (ku > 26) return north ? storey switch { 0 => L73Room.Gallery, 1 => L73Room.Library, _ => L73Room.Master } : L73Room.Guest;
        if (north) return storey switch { 0 => L73Room.Dining, 1 => L73Room.Sitting, _ => L73Room.Master };
        return storey == 0 ? L73Room.Hall : L73Room.Landing;
    }

    /// <summary>Whether a keep-local wall position on a storey is a doorway (two high) between rooms.</summary>
    public static bool L73Doorway(int ku, int kv, int storey) =>
        kv == 11 && ku is 17 or 18 || ku == 9 && kv is 6 or 17 || ku == 26 && (kv == 17 || kv == 6 && storey < 2);

    /// <summary>Whether a keep-local position is the keep's door (two leaves, three high, in the south wall).</summary>
    public static bool L73MainDoor(int ku, int kv) => kv == L73KeepD - 1 && ku is 17 or 18;

    /// <summary>The ground floor's hearth on the dining hall's north wall: 2 the fire (ku 17, 18), 1 its jambs, 0 elsewhere.</summary>
    public static int L73HearthAt(int ku, int kv) => kv != 1 ? 0 : ku is 17 or 18 ? 2 : ku is 16 or 19 ? 1 : 0;

    /// <summary>
    /// The step (1 to 5) of a flight of stairs at a keep-local position on a storey, or 0: from the ground floor and from
    /// the second up along the cross wall's south side rising east (ku 20-24), from the first rising west (ku 15-11), so
    /// that each flight lands where the next begins. Step 5 is the slab of the floor above.
    /// </summary>
    public static int L73StairStep(int ku, int kv, int storey)
    {
        if (kv is not (12 or 13)) return 0;
        if (storey == 1) return ku is >= 11 and <= 15 ? 16 - ku : 0;
        return storey is 0 or 2 && ku is >= 20 and <= 24 ? ku - 19 : 0;
    }

    /// <summary>The way a storey's flight rises.</summary>
    public static ArchPier L73StairRise(int storey) => storey == 1 ? ArchPier.West : ArchPier.East;

    /// <summary>Whether the slab over a storey is open above its flight (steps 1 to 4), for the head room.</summary>
    public static bool L73StairHole(int ku, int kv, int storey) => L73StairStep(ku, kv, storey) is >= 1 and <= 4;

    /// <summary>What the roof terrace holds at a keep-local position.</summary>
    public enum L73AtticPart : byte { None, Inside, Wall, StairWall, LockedDoor, BalconyDoor, Balcony, Rail }

    /// <summary>
    /// The attic on the roof terrace (keep-local ku 9-26, kv 4-15): its walls, the stairwell the third storey's flight
    /// comes up into (shut by a locked door in its north side: "CORAN has declared the attic off-limits"), its door onto
    /// the balcony, and the balcony over the front with its rail.
    /// </summary>
    public static L73AtticPart L73AtticAt(int ku, int kv)
    {
        if (ku is >= 9 and <= 26 && kv is >= 4 and <= 15)
        {
            if (ku is >= 19 and <= 25 && kv is >= 11 and <= 14)
            {
                if (kv == 11 && ku is 23 or 24) return L73AtticPart.LockedDoor;
                return kv is 11 or 14 || ku is 19 or 25 ? L73AtticPart.StairWall : L73AtticPart.Inside;
            }
            if (ku is 9 or 26 || kv is 4 or 15) return kv == 15 && ku is 17 or 18 ? L73AtticPart.BalconyDoor : L73AtticPart.Wall;
            return L73AtticPart.Inside;
        }
        if (kv is >= 16 and <= 20 && ku is >= 13 and <= 22) return kv == 20 || ku is 13 or 22 ? L73AtticPart.Rail : L73AtticPart.Balcony;
        return L73AtticPart.None;
    }

    /// <summary>
    /// Whether a keep-local position on the outer wall has a window on a storey (boarded, with red velvet curtains inside):
    /// every fourth along each wall, where a room lies behind it with nothing standing or hanging in front, not hard
    /// against a partition, the hearth or the door.
    /// </summary>
    public static bool L73Window(int ku, int kv, int storey)
    {
        if (storey > 2 || !L73KeepRing(ku, kv)) return false;
        bool ns = kv == 0 || kv == L73KeepD - 1, we = ku == 0 || ku == L73KeepW - 1;
        if (ns == we || (ns ? ku % 4 != 2 : kv % 4 != 2)) return false;
        if (storey == 0 && ns && ku is >= 15 and <= 20) return false; // the door, the hearth
        int iu = ku == 0 ? 1 : ku == L73KeepW - 1 ? L73KeepW - 2 : ku, iv = kv == 0 ? 1 : kv == L73KeepD - 1 ? L73KeepD - 2 : kv;
        if (L73RoomAt(iu, iv, storey) == L73Room.Wall || L73StairStep(iu, iv, storey) > 0) return false;
        bool cramped = ns ? L73RoomAt(iu - 1, iv, storey) == L73Room.Wall || L73RoomAt(iu + 1, iv, storey) == L73Room.Wall
            : L73RoomAt(iu, iv - 1, storey) == L73Room.Wall || L73RoomAt(iu, iv + 1, storey) == L73Room.Wall;
        if (cramped) return false;
        return !L73Furnishings.ContainsKey((iu, iv, storey, L73Layer.Floor)) && !L73Furnishings.ContainsKey((iu, iv, storey, L73Layer.Wall));
    }

    /// <summary>The way the curtains at a keep-local room position face, if a window is behind them; null if none.</summary>
    public static ArchPier? L73CurtainAt(int ku, int kv, int storey)
    {
        if (L73RoomAt(ku, kv, storey) == L73Room.Wall) return null;
        if (kv == 1 && L73Window(ku, 0, storey)) return ArchPier.South;
        if (kv == L73KeepD - 2 && L73Window(ku, L73KeepD - 1, storey)) return ArchPier.North;
        if (ku == 1 && L73Window(0, kv, storey)) return ArchPier.East;
        if (ku == L73KeepW - 2 && L73Window(L73KeepW - 1, kv, storey)) return ArchPier.West;
        return null;
    }

    /// <summary>
    /// The furnishings, keep-local, by storey (3 the attic) and layer, with the way each faces and its kind (which
    /// painting). Wall things face away from the wall they hang on; beds face from head to foot.
    /// </summary>
    private static readonly Dictionary<(int, int, int, L73Layer), (L73Thing Thing, ArchPier Facing, byte Kind)> L73Furnishings = PlanL73Furnishings();

    private static Dictionary<(int, int, int, L73Layer), (L73Thing, ArchPier, byte)> PlanL73Furnishings()
    {
        var f = new Dictionary<(int, int, int, L73Layer), (L73Thing, ArchPier, byte)>();
        const ArchPier N = ArchPier.North, E = ArchPier.East, S = ArchPier.South, W = ArchPier.West;
        int painting = 0;
        void Put(int ku, int kv, int s, L73Thing thing, ArchPier facing)
        {
            L73Layer layer = thing switch
            {
                L73Thing.Sconce or L73Thing.Painting or L73Thing.Banner => L73Layer.Wall,
                L73Thing.Chandelier => L73Layer.Ceiling,
                _ => L73Layer.Floor,
            };
            byte kind = thing == L73Thing.Painting ? (byte)(painting++ % L73Paintings) : (byte)0;
            f[(ku, kv, s, layer)] = (thing, facing, kind);
        }
        // Mirrored for the east end of the keep (ku to 35 - ku, east and west swapped)
        ArchPier Flip(ArchPier p) => p == E ? W : p == W ? E : p;
        void PutM(bool west, int ku, int kv, int s, L73Thing thing, ArchPier facing) =>
            Put(west ? ku : L73KeepW - 1 - ku, kv, s, thing, west ? facing : Flip(facing));
        // A long sofa from its left end (as one sits on it, facing the way it faces) to its right
        void Sofa(int ku, int kv, int s, ArchPier facing)
        {
            var (du, dv) = facing switch { N => (1, 0), S => (-1, 0), E => (0, 1), _ => (0, -1) };
            Put(ku, kv, s, L73Thing.SofaLeft, facing);
            Put(ku + du, kv + dv, s, L73Thing.SofaRight, facing);
        }

        // ---- Guest rooms, six: two beds each, heads to the cross wall, a nightstand by each, a wardrobe, a dresser
        for (int s = 0; s <= 2; s++)
            foreach (bool west in new[] { true, false })
            {
                foreach (int bed in new[] { 2, 6 })
                {
                    PutM(west, bed, 12, s, L73Thing.BedHead, S);
                    PutM(west, bed, 13, s, L73Thing.BedFoot, S);
                    PutM(west, bed + 1, 12, s, L73Thing.Nightstand, S);
                }
                PutM(west, 4, 12, s, L73Thing.Painting, S);
                PutM(west, 1, 21, s, L73Thing.Wardrobe, E);
                PutM(west, 1, 18, s, L73Thing.Dresser, E);
                PutM(west, 5, 20, s, L73Thing.Chair, N);
                PutM(west, 8, 14, s, L73Thing.Sconce, W);
                PutM(west, 8, 20, s, L73Thing.Sconce, W);
                PutM(west, 1, 16, s, L73Thing.Painting, E);
                PutM(west, 5, 17, s, L73Thing.Chandelier, N);
            }

        // ---- The bathrooms (west end, ground and first floor): the lore's barrels of warm water, two each; a toilet, a cabinet
        for (int s = 0; s <= 1; s++)
        {
            Put(3, 2, s, L73Thing.Bath, N);
            Put(6, 2, s, L73Thing.Bath, N);
            Put(1, 9, s, L73Thing.Toilet, E);
            Put(8, 9, s, L73Thing.Dresser, W);
            Put(1, 5, s, L73Thing.Sconce, E);
            Put(8, 3, s, L73Thing.Sconce, W);
        }

        // ---- Ground floor. The dining hall: the long table of plenty (twelve by two, a place set at every one of its 24
        // seats), the hearth in the middle of the north wall, banners either side of it
        for (int ku = 12; ku <= 23; ku++)
        {
            Put(ku, 5, 0, L73Thing.Table, N);
            Put(ku, 6, 0, L73Thing.Table, S);
            Put(ku, 4, 0, L73Thing.Chair, S);
            Put(ku, 7, 0, L73Thing.Chair, N);
        }
        Put(11, 2, 0, L73Thing.Candelabra, N); Put(24, 2, 0, L73Thing.Candelabra, N);
        Put(11, 9, 0, L73Thing.Candelabra, N); Put(24, 9, 0, L73Thing.Candelabra, N);
        Put(14, 1, 0, L73Thing.Banner, S); Put(21, 1, 0, L73Thing.Banner, S);
        Put(11, 1, 0, L73Thing.Sconce, S); Put(24, 1, 0, L73Thing.Sconce, S);
        Put(10, 3, 0, L73Thing.Sconce, E); Put(25, 3, 0, L73Thing.Sconce, W);
        Put(10, 8, 0, L73Thing.Painting, E); Put(25, 8, 0, L73Thing.Painting, W);
        Put(13, 10, 0, L73Thing.Painting, N); Put(22, 10, 0, L73Thing.Painting, N);
        Put(15, 10, 0, L73Thing.Sconce, N); Put(20, 10, 0, L73Thing.Sconce, N);
        Put(14, 5, 0, L73Thing.Chandelier, N); Put(21, 6, 0, L73Thing.Chandelier, N);
        // The main hall: the door in the south wall, the stair up along the cross wall, banners, a clock, candelabras
        Put(10, 14, 0, L73Thing.Clock, E);
        Put(11, 21, 0, L73Thing.Candelabra, N); Put(24, 21, 0, L73Thing.Candelabra, N);
        Put(10, 19, 0, L73Thing.Banner, E); Put(25, 19, 0, L73Thing.Banner, W);
        Put(10, 15, 0, L73Thing.Banner, E); Put(25, 15, 0, L73Thing.Banner, W);
        Put(10, 21, 0, L73Thing.Sconce, E); Put(25, 21, 0, L73Thing.Sconce, W);
        Put(14, 22, 0, L73Thing.Sconce, N); Put(21, 22, 0, L73Thing.Sconce, N);
        Put(12, 12, 0, L73Thing.Painting, S); Put(15, 12, 0, L73Thing.Painting, S);
        Sofa(12, 17, 0, E); Sofa(23, 18, 0, W);
        // Two round tables either side of the way in, chairs at them
        Put(14, 20, 0, L73Thing.RoundTable, N); Put(13, 20, 0, L73Thing.Chair, E); Put(15, 20, 0, L73Thing.Chair, W);
        Put(21, 20, 0, L73Thing.RoundTable, N); Put(20, 20, 0, L73Thing.Chair, E); Put(22, 20, 0, L73Thing.Chair, W);
        Put(14, 17, 0, L73Thing.Chandelier, N); Put(21, 18, 0, L73Thing.Chandelier, N);
        // The gallery: "numerous paintings of locations in The Frontrooms, but none of them lead outside"
        Put(27, 3, 0, L73Thing.Painting, E); Put(27, 9, 0, L73Thing.Painting, E);
        Put(34, 4, 0, L73Thing.Painting, W); Put(34, 8, 0, L73Thing.Painting, W);
        Put(29, 1, 0, L73Thing.Painting, S); Put(32, 1, 0, L73Thing.Painting, S);
        Put(29, 10, 0, L73Thing.Painting, N); Put(32, 10, 0, L73Thing.Painting, N);
        Sofa(30, 6, 0, N);
        Put(28, 2, 0, L73Thing.Candelabra, N); Put(33, 9, 0, L73Thing.Candelabra, N);
        Put(27, 5, 0, L73Thing.Sconce, E); Put(34, 6, 0, L73Thing.Sconce, W);
        Put(30, 5, 0, L73Thing.Chandelier, N);

        // ---- First floor. The sitting room round the chimney breast: two long sofas, chairs, bookshelves
        Sofa(18, 3, 1, S); Sofa(17, 8, 1, N);
        Put(14, 5, 1, L73Thing.Chair, E); Put(14, 6, 1, L73Thing.Chair, E);
        Put(21, 5, 1, L73Thing.Chair, W); Put(21, 6, 1, L73Thing.Chair, W);
        for (int kv = 2; kv <= 4; kv++)
        {
            Put(10, kv, 1, L73Thing.Bookshelf, E);
            Put(25, kv, 1, L73Thing.Bookshelf, W);
        }
        Put(11, 9, 1, L73Thing.Candelabra, N); Put(24, 9, 1, L73Thing.Candelabra, N);
        Put(17, 2, 1, L73Thing.Painting, S);
        Put(15, 1, 1, L73Thing.Banner, S); Put(20, 1, 1, L73Thing.Banner, S);
        Put(10, 8, 1, L73Thing.Sconce, E); Put(25, 8, 1, L73Thing.Sconce, W);
        Put(13, 10, 1, L73Thing.Sconce, N); Put(22, 10, 1, L73Thing.Sconce, N);
        Put(17, 5, 1, L73Thing.Chandelier, N);
        // The library
        for (int ku = 28; ku <= 33; ku++)
        {
            Put(ku, 1, 1, L73Thing.Bookshelf, S);
            Put(ku, 10, 1, L73Thing.Bookshelf, N);
        }
        Put(34, 3, 1, L73Thing.Bookshelf, W); Put(34, 4, 1, L73Thing.Bookshelf, W); Put(34, 8, 1, L73Thing.Bookshelf, W);
        Put(30, 5, 1, L73Thing.RoundTable, N); Put(30, 4, 1, L73Thing.Chair, S); Put(30, 6, 1, L73Thing.Chair, N);
        Put(28, 8, 1, L73Thing.Candelabra, N);
        Put(27, 3, 1, L73Thing.Sconce, E); Put(27, 9, 1, L73Thing.Painting, E);
        Put(31, 5, 1, L73Thing.Chandelier, N);
        // The first floor's landing: the flight up from the hall arrives in the east, the next leaves in the west
        Put(17, 18, 1, L73Thing.RoundTable, N);
        Put(16, 18, 1, L73Thing.Chair, E); Put(18, 18, 1, L73Thing.Chair, W);
        Put(11, 21, 1, L73Thing.Candelabra, N); Put(24, 21, 1, L73Thing.Candelabra, N);
        Put(10, 19, 1, L73Thing.Banner, E); Put(25, 19, 1, L73Thing.Banner, W);
        Put(10, 15, 1, L73Thing.Sconce, E); Put(25, 15, 1, L73Thing.Sconce, W);
        Put(13, 22, 1, L73Thing.Painting, N); Put(22, 22, 1, L73Thing.Painting, N);
        Put(17, 16, 1, L73Thing.Chandelier, N);

        // ---- Second floor. The master bedroom: Coran's, the whole north side east of the store-room; a bed made of two,
        // a desk, wardrobes, bookshelves
        foreach (int bed in new[] { 29, 30 })
        {
            Put(bed, 1, 2, L73Thing.BedHead, S);
            Put(bed, 2, 2, L73Thing.BedFoot, S);
        }
        Put(28, 1, 2, L73Thing.Nightstand, S); Put(31, 1, 2, L73Thing.Nightstand, S);
        Put(34, 4, 2, L73Thing.Wardrobe, W); Put(34, 5, 2, L73Thing.Wardrobe, W); Put(34, 8, 2, L73Thing.Dresser, W);
        for (int kv = 2; kv <= 4; kv++) Put(10, kv, 2, L73Thing.Bookshelf, E);
        Put(13, 3, 2, L73Thing.Desk, S); Put(13, 4, 2, L73Thing.Chair, N);
        Put(11, 9, 2, L73Thing.Candelabra, N); Put(24, 9, 2, L73Thing.Candelabra, N); Put(33, 9, 2, L73Thing.Candelabra, N);
        Put(15, 1, 2, L73Thing.Banner, S); Put(20, 1, 2, L73Thing.Banner, S);
        Put(29, 1, 2, L73Thing.Painting, S);
        Put(10, 8, 2, L73Thing.Sconce, E); Put(34, 2, 2, L73Thing.Sconce, W);
        Put(13, 10, 2, L73Thing.Sconce, N); Put(22, 10, 2, L73Thing.Sconce, N); Put(31, 10, 2, L73Thing.Sconce, N);
        Put(17, 5, 2, L73Thing.Chandelier, N); Put(29, 6, 2, L73Thing.Chandelier, N);
        // The store-room off it: what the castle keeps by (the level's supply boxes), crates, and the Hounds' bones
        Put(1, 2, 2, L73Thing.Box, E); Put(2, 1, 2, L73Thing.Box, S); Put(1, 4, 2, L73Thing.Box, E);
        Put(5, 1, 2, L73Thing.Crate, S); Put(6, 1, 2, L73Thing.Crate, S); Put(1, 8, 2, L73Thing.Crate, E);
        Put(4, 9, 2, L73Thing.Bones, N); Put(6, 9, 2, L73Thing.Bones, N);
        Put(8, 3, 2, L73Thing.Sconce, W);
        // The second floor's landing: the flight up from below arrives in the west, the shut one to the attic leaves east
        Put(11, 21, 2, L73Thing.Candelabra, N); Put(24, 21, 2, L73Thing.Candelabra, N);
        Put(10, 19, 2, L73Thing.Banner, E); Put(25, 19, 2, L73Thing.Banner, W);
        Put(10, 15, 2, L73Thing.Sconce, E); Put(25, 15, 2, L73Thing.Sconce, W);
        Put(13, 22, 2, L73Thing.Painting, N); Put(22, 22, 2, L73Thing.Painting, N);
        Sofa(16, 20, 2, N);
        Put(17, 17, 2, L73Thing.Chandelier, N);

        // ---- Notes left lying: in a guest room, the library, by the attic stair
        Put(4, 16, 0, L73Thing.Note, N); Put(32, 7, 1, L73Thing.Note, N); Put(19, 14, 2, L73Thing.Note, N); Put(30, 18, 2, L73Thing.Note, N);

        // ---- The attic (shut, and dark): crates, an old pack, bones, a great skull
        Put(11, 6, 3, L73Thing.Crate, N); Put(12, 6, 3, L73Thing.Crate, N); Put(11, 7, 3, L73Thing.Crate, N);
        Put(16, 6, 3, L73Thing.Skull, S); Put(15, 7, 3, L73Thing.Ribcage, E); Put(14, 8, 3, L73Thing.Bones, N);
        Put(22, 6, 3, L73Thing.Pack, S); Put(12, 13, 3, L73Thing.Bones, N);
        return f;
    }

    /// <summary>How many paintings of the Frontrooms there are to hang (blocks l73-painting-1 to -6).</summary>
    public const int L73Paintings = 6;

    /// <summary>What stands at a keep-local position on a storey (3 the attic) in a layer, which way it faces, and its kind.</summary>
    public static (L73Thing Thing, ArchPier Facing, byte Kind) L73FurnishingAt(int ku, int kv, int storey, L73Layer layer) =>
        L73Furnishings.TryGetValue((ku, kv, storey, layer), out var f) ? f : (L73Thing.None, ArchPier.North, (byte)0);

    /// <summary>
    /// The banners on the castle's walls and the keep's front, castle-local (positions just outside a wall, facing away
    /// from it, with the height of the banner's top above the plateau): on the outer faces of the gate towers and of each
    /// curtain, on the inner faces round the courtyard, on the keep's front either side of the door.
    /// </summary>
    public static (ArchPier Facing, int Top)? L73BannerAt(int u, int v)
    {
        const int w = L73CastleW, d = L73CastleD;
        // Outside the walls
        if (v == d && u is 23 or 32) return (ArchPier.South, 9);
        if (v == -1 && u is 18 or 37) return (ArchPier.North, 6);
        if (u == -1 && v is 16 or 31) return (ArchPier.West, 6);
        if (u == w && v is 16 or 31) return (ArchPier.East, 6);
        // Round the courtyard
        if (v == 2 && u is 18 or 37) return (ArchPier.South, 6);
        if (u == 2 && v is 18 or 34) return (ArchPier.East, 6);
        if (u == w - 3 && v is 18 or 34) return (ArchPier.West, 6);
        if (v == d - 3 && u is 12 or 43) return (ArchPier.North, 6);
        if (v == d - 6 && u is 23 or 32) return (ArchPier.North, 8);
        // The keep's front
        if (v == L73KeepV0 + L73KeepD && u is 22 or 33) return (ArchPier.South, 9);
        return null;
    }

    /// <summary>Whether a block position is inside the keep's square (its walls included).</summary>
    public bool InL73Keep(int gx, int gz)
    {
        int ku = gx - L73CastleX0 - L73KeepU0, kv = gz - L73CastleZ0 - L73KeepV0;
        return ku >= 0 && kv >= 0 && ku < L73KeepW && kv < L73KeepD;
    }

    /// <summary>Whether a block position is inside the castle's square (its walls included).</summary>
    public bool InL73Castle(int gx, int gz)
    {
        int u = gx - L73CastleX0, v = gz - L73CastleZ0;
        return u >= 0 && v >= 0 && u < L73CastleW && v < L73CastleD;
    }

    /// <summary>Whether a block position is in the dining hall's square (where the hearth keeps the ground floor warm).</summary>
    public bool InL73Dining(int gx, int gz)
    {
        int ku = gx - L73CastleX0 - L73KeepU0, kv = gz - L73CastleZ0 - L73KeepV0;
        return ku >= 0 && kv >= 0 && ku < L73KeepW && kv < L73KeepD && L73RoomAt(ku, kv, 0) == L73Room.Dining;
    }

    // ================= Cells =================

    /// <summary>The wall line between two of the level's cells: none (the island is laid out tile by tile).</summary>
    private Edge L73Edge(int mx, int mz, bool west) => new Edge { Pattern = WallPattern.L73Wall };

    /// <summary>Lays out one of the level's cells: the rim's cliff, or the island, its sea and the castle, tile by tile.</summary>
    private void BuildLevel73(Builder b, int mx, int mz)
    {
        // The rim: a cliff of black rock all the way round the sea
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != Level73) { rim = true; break; }

        int cx0 = L73CastleX0, cz0 = L73CastleZ0;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (rim)
                {
                    t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.L73Rim, Floor = FloorKind.L73Rock, Zone = L73RimZone };
                    continue;
                }
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                L73Part part = L73CastleAt(gx - cx0, gz - cz0);
                t = part == L73Part.Outside ? L73Terrain(gx, gz, cx0, cz0) : L73CastleTile(part, gx - cx0, gz - cz0);
            }
    }

    private Tile L73Terrain(int gx, int gz, int cx0, int cz0)
    {
        int g = L73Ground(gx, gz, out FloorKind floor);
        var t = new Tile { Kind = TileKind.Floor, Floor = floor, Zone = g < 0 ? L73Sea : L73Land, Height = (byte)Math.Max(0, g), Depth = (byte)Math.Max(0, -g) };
        // The stone path runs on out of the gate and down the hill ("follow the hard sensation on the bottom of your feet")
        int u = gx - cx0, v = gz - cz0;
        if (g > 0 && u is >= 26 and <= 29 && v >= L73CastleD && v < L73CastleD + 26)
        {
            t.Floor = FloorKind.L73Path;
            return t;
        }
        // Under the Great Hound's bones: nobody is put down there, nothing else lies there
        if (InL73Hound(gx, gz))
        {
            t.Sealed = true;
            return t;
        }
        // Old bones on the fields, now and then a ribcage, and seldom a pack someone dropped running for the castle
        if (g >= 2 && floor is not (FloorKind.L73Mud or FloorKind.L73Tor) && L73BannerAt(u, v) == null)
        {
            ulong h = Hashing.Hash(seed, gx, gz, SaltL73Bones);
            double r = Hashing.Unit(h);
            ushort prop = r < 1 / 170.0 ? Props.BonePile : r < 1 / 170.0 + 1 / 1400.0 ? Props.Ribcage : r < 1 / 170.0 + 1 / 1400.0 + 1 / 1100.0 ? Props.JawSkeleton
                : r < 1 / 170.0 + 1 / 1400.0 + 1 / 1100.0 + 1 / 3000.0 ? Props.Backpack : (ushort)0;
            if (prop != 0)
            {
                t.Variant = prop;
                t.Pier = (ArchPier)(Hashing.Mix(h) % 4);
            }
            // And here and there a note someone dropped running (Detail 1: a loose note lies on the ground)
            else if (r > 0.999 && r < 0.99935) t.Detail = 1;
        }
        return t;
    }

    private static Tile L73CastleTile(L73Part part, int u, int v)
    {
        var t = new Tile { Height = L73Plateau };
        switch (part)
        {
            case L73Part.Court: t.Kind = TileKind.Floor; t.Floor = FloorKind.L73Court; t.Zone = L73Court; break;
            case L73Part.Path or L73Part.Gate: t.Kind = TileKind.Floor; t.Floor = FloorKind.L73Path; t.Zone = L73Court; break;
            case L73Part.Keep:
            {
                int ku = u - L73KeepU0, kv = v - L73KeepV0;
                L73Room room = L73RoomAt(ku, kv, 0);
                t.Zone = L73Keep;
                if (L73MainDoor(ku, kv))
                {
                    t.Kind = TileKind.Doorway; t.Pattern = WallPattern.L73Wall; t.Floor = FloorKind.L73Path;
                }
                else if (room == L73Room.Wall)
                {
                    t.Kind = L73Doorway(ku, kv, 0) ? TileKind.Doorway : TileKind.Wall; t.Pattern = WallPattern.L73Wall; t.Floor = FloorKind.L73Boards;
                }
                else
                {
                    t.Kind = TileKind.Floor;
                    t.Floor = room switch
                    {
                        L73Room.Hall => FloorKind.L73Carpet,
                        L73Room.Bath => FloorKind.L73Tile,
                        L73Room.Guest => FloorKind.L73Damask,
                        _ => FloorKind.L73Boards,
                    };
                    int step = L73StairStep(ku, kv, 0);
                    if (step > 0)
                    {
                        t.Stair = (byte)step;
                        t.Pier = ArchPier.East;
                    }
                    // Nobody is put down in the fire, or on the furniture
                    if (L73HearthAt(ku, kv) > 0 || L73FurnishingAt(ku, kv, 0, L73Layer.Floor).Thing != L73Thing.None) t.Sealed = true;
                }
                break;
            }
            default: t.Kind = TileKind.Wall; t.Pattern = WallPattern.L73Wall; t.Floor = FloorKind.L73Court; t.Zone = L73Walls; break;
        }
        return t;
    }

    /// <summary>Which of the level's props (<see cref="Props.L73First"/>-<see cref="Props.L73Last"/>) people walk through: none (it has none).</summary>
    private static bool L73WalkThrough(ushort variant) => false;

    // ================= Air =================

    /// <summary>The temperature: near freezing out on the island; mild in the keep, warm on the ground floor round the hearth, cool in the attic.</summary>
    private float L73Temperature(int x, int y, int z, int floorY)
    {
        int rel = y - floorY;
        if (InL73Keep(x, z) && rel > L73Plateau && rel <= L73Plateau + L73AtticTop)
            return InL73Dining(x, z) && rel <= L73Plateau + L73Storey ? 22f : rel > L73Plateau + L73Terrace ? 9f : 16f;
        return 4f;
    }

    /// <summary>Reality stability: a slow drain out on the island and the sea; none within the castle's walls.</summary>
    private float L73Stability(double x, double y, double z, int floorY, float drift)
    {
        Tile t = TileAt((int)Math.Floor(x), (int)Math.Floor(z));
        return t.Zone is L73Court or L73Keep or L73Walls ? 1f : 0.9f;
    }
}
