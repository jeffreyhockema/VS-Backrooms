using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 7, "Thalassophobia": an enormous ocean beneath a concrete ceiling about four and a half metres above the
/// water, in dim light with no source. Its floor is carpeted. It deepens away from Level 6:
/// <code>
///   daylight zone   down to 12   barren; sunken furniture, lost backpacks, waterlogged crates
///   twilight zone   12 to 30     loose bones, rusted scrap, skeletons of things with far too large jaws
///   midnight zone   30 to 60     completely dark; enormous skeletal structures; cave mouths down to Level 8
///   abyss           below 60     mountainous piles of tar, steadily bubbling
/// </code>
/// Islands of an unknown rock break the surface here and there. Entry rooms are set into the ceiling: a furnished
/// room with a bookcase, a coffee table and a chair whose doorway opens straight down onto the water, so whoever
/// comes in falls through. A circle of stones on the seabed in the twilight zone leads to Level 9.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltL7Depth = 0x7B01;
    private const ulong SaltL7Island = 0x7B02;
    private const ulong SaltL7Detail = 0x7B03;
    private const ulong SaltL7Feature = 0x7B04;

    public const int TwilightDepth = 12, MidnightDepth = 30, AbyssDepth = 60;

    /// <summary>
    /// Level 7's <see cref="Tile.Detail"/> (from layout version 5): a shelter's furniture stuck down on a lump of tar
    /// (the prop stands one block higher), and a pillar of the islands' rock standing up into the ceiling (a wall tile;
    /// its <see cref="Tile.Depth"/> is the seabed's where it stands in the sea).
    /// </summary>
    public const byte L7TarUnder = 1, L7Pillar = 2;

    /// <summary>Depth of the seabed below the floor at a block of Level 7 (0 where an island breaks the surface).</summary>
    private int OceanDepth(int gx, int gz)
    {
        double t = RingFraction(gx, gz, 7);
        double depth = 5 + t * 55 + 10 * Fbm(gx / 40.0, gz / 40.0, SaltL7Depth);
        // Trenches plunge into the abyss
        double trench = Noise(gx / 70.0, gz / 70.0, SaltL7Depth + 5);
        if (trench > 0.45) depth += (trench - 0.45) * 220;
        // Islands rise from the shallows
        if (t < 0.7 && Fbm(gx / 18.0, gz / 18.0, SaltL7Island) > 0.55) return 0;
        return (int)Math.Clamp(depth, 3, 120);
    }

    private void BuildLevel7(Builder b, int mx, int mz)
    {
        ref Rng rng = ref b.Rng;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = mx * MacroSize + lx, gz = mz * MacroSize + lz;
                if (t.Kind != TileKind.Floor) continue;
                int depth = OceanDepth(gx, gz);
                t.Floor = depth >= AbyssDepth ? FloorKind.Tar : FloorKind.Seabed;
                if (depth == 0)
                {
                    t.Floor = FloorKind.Seabed; // an island of strange rock; stand on it
                    if (Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL7Island + 3)) < 0.09) t.Stack = 1; // a boulder of it
                    // Some islands were camped on, in the manner of Fort Surrender: tents, bedrolls, a lantern, what
                    // the researchers could not carry when they left
                    else if (Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx, 24), Hashing.FloorDiv(gz, 24), SaltL7Island + 1)) < 0.3)
                    {
                        double c = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL7Island + 2));
                        t.Pier = (ArchPier)((int)(c * 4000) & 3);
                        if (c < 0.03) t.Variant = Props.Tent;
                        else if (c < 0.05) t.Variant = Props.Bedroll;
                        else if (c < 0.062) t.Variant = Props.Lantern;
                        else if (c < 0.076) t.SupplyBox = true;
                        else if (c < 0.086) t.Variant = Props.BurnBarrel;
                        else if (c < 0.094) t.Variant = Props.CardboardBoxes;
                        else if (c < 0.1) t.Variant = Props.MegMarker;
                    }
                    continue;
                }
                t.Kind = TileKind.Water;
                t.Depth = (byte)depth;

                // What lies on the bottom depends on the depth
                double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltL7Detail));
                var facing = (ArchPier)(Hashing.Hash(seed, gx, gz, SaltL7Detail + 1) % 4);
                t.Pier = facing;
                if (depth < TwilightDepth)
                {
                    t.Variant = r < 0.004 ? Props.Backpack : r < 0.008 ? Props.WreckCrate : r < 0.011 ? Props.HotelChair
                        : r < 0.013 ? Props.FilingCabinet : r < 0.015 ? Props.WingChair : (byte)0;
                    if (r > 0.997) t.SupplyBox = true;
                    // Things afloat on the surface: driftwood, an old buoy
                    else if (r > 0.991) t.Stack = 1; // (Stack, on water with nothing on the bottom: 1 driftwood, 2 a buoy)
                    else if (r > 0.9895) t.Stack = 2;
                }
                else if (depth < MidnightDepth)
                {
                    t.Variant = r < 0.02 ? Props.BonePile : r < 0.035 ? Props.ScrapMetal : r < 0.04 ? Props.JawSkeleton : r < 0.042 ? Props.Backpack : (byte)0;
                    // Kelp rising toward a surface it never reaches, in patches
                    if (t.Variant == 0 && Noise(gx / 9.0, gz / 9.0, SaltL7Detail + 3) > 0.35 && r > 0.6)
                    {
                        t.Variant = Props.Kelp;
                        t.Stack = (byte)Math.Min(depth - 3, 4 + (int)(r * 30) % 14);
                    }
                }
                else if (depth < AbyssDepth)
                    t.Variant = r < 0.008 ? Props.Ribcage : r < 0.02 ? Props.BonePile : (byte)0;
            }
        }

        // A ledge of concrete along any wall this cell shares with another level. The walls on its east and south
        // sides belong to the neighbouring cells, so those are judged by the neighbour's level.
        bool eastWall = LevelAt(mx + 1, mz) != 7, southWall = LevelAt(mx, mz + 1) != 7, cornerWall = LevelAt(mx + 1, mz + 1) != 7;
        // (From layout version 9 this cell lines those walls with its own, a tile in: the ledge runs along the lining)
        bool eastLined = LinesWallTo(7, mx, mz, mx + 1, mz), southLined = LinesWallTo(7, mx, mz, mx, mz + 1);
        bool WallAt(int x, int z)
        {
            if (x < 0 || z < 0) return false;
            if (x == MacroSize - 1 && eastLined || z == MacroSize - 1 && southLined) return true;
            if (x >= MacroSize && z >= MacroSize) return cornerWall;
            if (x >= MacroSize) return eastWall;
            if (z >= MacroSize) return southWall;
            return b.At(x, z).IsWallLike;
        }
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind != TileKind.Water) continue;
                bool nearWall = false;
                for (int dz = -2; dz <= 2 && !nearWall; dz++)
                    for (int dx = -2; dx <= 2 && !nearWall; dx++)
                    {
                        if (WallAt(lx + dx, lz + dz)) nearWall = true;
                    }
                if (!nearWall) continue;
                t.Kind = TileKind.Floor;
                t.Floor = FloorKind.Concrete;
                t.Variant = 0;
                t.Depth = 0;
                t.SupplyBox = false;
            }
        }

        if (Version >= 5) ShapeLevel7(b, mx, mz);
        AddJetty(b, mx, mz);

        double feature = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL7Feature));
        int cx = 16, cz = 16, centreDepth = OceanDepth(mx * MacroSize + cx, mz * MacroSize + cz);
        // The entry room is one of a kind in its stretch of sea
        if (RegionPick(mx, mz, 4, SaltL7Feature + 1, 0.9) && centreDepth > 0 && centreDepth < TwilightDepth + 6) AddEntryRoom(b, cx, cz);
        else if (feature < 0.06 && centreDepth >= TwilightDepth && centreDepth < MidnightDepth) AddStoneCircle(b, cx, cz);
        else if (feature < 0.16 && centreDepth >= MidnightDepth && centreDepth < AbyssDepth) AddUnderwaterCave(b, cx, cz);
        else if (feature is >= 0.06 and < 0.1 && centreDepth >= TwilightDepth && centreDepth < MidnightDepth) AddTiledSeabed(b, cx, cz);
    }

    /// <summary>
    /// From layout version 5, what gives the sea a middle distance. The islands rise in steps from the water's edge
    /// (<see cref="Tile.Height"/> 0 at the rim, 1 a step in, 2 further in, so every step can be climbed); pillars of
    /// their rock stand from the larger islands up into the ceiling, and sea stacks of it out in the shallows, dark
    /// shapes against the mist that you can steer by. On some camped islands (one camp in two) the campers built a shelter in the manner
    /// of Fort Surrender ("a haphazardly constructed shelter composed of broken furniture held together by tar"): a
    /// ring of cabinets, bookcases and chairs, some stuck down on lumps of tar, round a bedroll, with a gap to get in.
    /// Everything is worked out from where it is, so cells agree along their edges.
    /// </summary>
    private void ShapeLevel7(Builder b, int mx, int mz)
    {
        const int margin = 8, span = MacroSize + 2 * margin;
        int x0 = mx * MacroSize - margin, z0 = mz * MacroSize - margin;
        var isle = new bool[span * span];
        for (int z = 0; z < span; z++)
            for (int x = 0; x < span; x++)
                isle[z * span + x] = OceanDepth(x0 + x, z0 + z) == 0;
        bool Isle(int gx, int gz) => gx >= x0 && gz >= z0 && gx < x0 + span && gz < z0 + span ? isle[(gz - z0) * span + gx - x0] : OceanDepth(gx, gz) == 0;
        // How far (in rings) to the nearest water, up to max + 1
        int Inland(int gx, int gz, int max)
        {
            for (int k = 1; k <= max; k++)
                for (int dz = -k; dz <= k; dz++)
                    for (int dx = -k; dx <= k; dx++)
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) == k && !Isle(gx + dx, gz + dz)) return k;
            return max + 1;
        }
        int gx0 = mx * MacroSize, gz0 = mz * MacroSize;
        for (int lz = 0; lz < MacroSize; lz++)
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (t.Kind == TileKind.Floor && t.Floor == FloorKind.Seabed) t.Height = (byte)Math.Min(Inland(gx0 + lx, gz0 + lz, 3) - 1, 2);
            }

        // A pillar of rock over a round footprint, where it touches this cell
        void Pillar(int cx, int cz, int r2, bool sea)
        {
            for (int z = cz - 2; z <= cz + 2; z++)
                for (int x = cx - 2; x <= cx + 2; x++)
                {
                    int lx = x - gx0, lz = z - gz0;
                    if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize || (x - cx) * (x - cx) + (z - cz) * (z - cz) > r2) continue;
                    ref Tile t = ref b.At(lx, lz);
                    if (t.Kind != (sea ? TileKind.Water : TileKind.Floor) || t.Zone != 0) continue;
                    int depth = sea ? t.Depth : 0;
                    t = default;
                    t.Kind = TileKind.Wall;
                    t.Pattern = WallPattern.Rock;
                    t.Detail = L7Pillar;
                    t.Depth = (byte)depth;
                }
        }
        // Never in the middle of a cell, where an entry room may hang over the water
        static bool Clear(int x, int z) => Math.Abs(Hashing.Mod(x, MacroSize) - 16) > 5 || Math.Abs(Hashing.Mod(z, MacroSize) - 16) > 5;
        // Island pillars: one place in each 10 by 10 square, if it is well inland
        for (int sz = Hashing.FloorDiv(gz0 - 2, 10); sz <= Hashing.FloorDiv(gz0 + MacroSize + 1, 10); sz++)
            for (int sx = Hashing.FloorDiv(gx0 - 2, 10); sx <= Hashing.FloorDiv(gx0 + MacroSize + 1, 10); sx++)
            {
                ulong h = Hashing.Hash(seed, sx, sz, SaltL7Island + 6);
                int cx = sx * 10 + (int)(h % 10), cz = sz * 10 + (int)((h >> 8) % 10);
                if (cx < gx0 - 2 || cz < gz0 - 2 || cx > gx0 + MacroSize + 1 || cz > gz0 + MacroSize + 1 || !Clear(cx, cz)) continue;
                int inland = Inland(cx, cz, 5);
                if (inland >= 3) Pillar(cx, cz, inland >= 5 && (h >> 20) % 2 == 0 ? 5 : 2, sea: false);
            }
        // Sea stacks out of the shallows and the twilight zone, about one to every 28 by 28 blocks, clear of islands and
        // the walls' ledges
        for (int sz = Hashing.FloorDiv(gz0 - 2, 28); sz <= Hashing.FloorDiv(gz0 + MacroSize + 1, 28); sz++)
            for (int sx = Hashing.FloorDiv(gx0 - 2, 28); sx <= Hashing.FloorDiv(gx0 + MacroSize + 1, 28); sx++)
            {
                ulong h = Hashing.Hash(seed, sx, sz, SaltL7Island + 7);
                if (Hashing.Unit(h) > 0.7) continue;
                int cx = sx * 28 + (int)((h >> 8) % 28), cz = sz * 28 + (int)((h >> 16) % 28);
                if (cx < gx0 - 2 || cz < gz0 - 2 || cx > gx0 + MacroSize + 1 || cz > gz0 + MacroSize + 1 || !Clear(cx, cz)) continue;
                int lcx = Hashing.Mod(cx, MacroSize), lcz = Hashing.Mod(cz, MacroSize);
                if (lcx < 5 || lcz < 5 || lcx > MacroSize - 6 || lcz > MacroSize - 6 || LevelAt(MacroOf(cx), MacroOf(cz)) != 7) continue;
                int depth = OceanDepth(cx, cz);
                if (depth < 2 || depth >= MidnightDepth || NearIsle(cx, cz)) continue;
                Pillar(cx, cz, (h >> 30) % 3 == 0 ? 5 : 2, sea: true);
            }
        bool NearIsle(int cx, int cz)
        {
            for (int dz = -4; dz <= 4; dz++)
                for (int dx = -4; dx <= 4; dx++)
                    if (Isle(cx + dx, cz + dz)) return true;
            return false;
        }

        // Fort Surrender's kind of shelter, in one camp in two
        for (int sz = Hashing.FloorDiv(gz0 - 2, 24); sz <= Hashing.FloorDiv(gz0 + MacroSize + 1, 24); sz++)
            for (int sx = Hashing.FloorDiv(gx0 - 2, 24); sx <= Hashing.FloorDiv(gx0 + MacroSize + 1, 24); sx++)
            {
                if (Hashing.Unit(Hashing.Hash(seed, sx, sz, SaltL7Island + 1)) >= 0.3) continue; // not a camp
                ulong h = Hashing.Hash(seed, sx, sz, SaltL7Island + 8);
                if (Hashing.Unit(h) > 0.5) continue;
                // (The first of a few places in the square that is well inland, wherever the cell is)
                for (int attempt = 0; attempt < 8; attempt++, h = Hashing.Mix(h))
                {
                    int cx = sx * 24 + 2 + (int)(h % 20), cz = sz * 24 + 2 + (int)((h >> 8) % 20);
                    if (Inland(cx, cz, 3) < 3) continue;
                    if (cx >= gx0 - 2 && cz >= gz0 - 2 && cx <= gx0 + MacroSize + 1 && cz <= gz0 + MacroSize + 1) Shelter(b, cx - gx0, cz - gz0, h);
                    break;
                }
            }
    }

    /// <summary>
    /// A shelter of broken furniture held together by tar, round (<paramref name="cx"/>, <paramref name="cz"/>) in the
    /// cell's coordinates (the middle may lie just outside the cell): the ring two out from the middle is furniture
    /// facing in, the corners lumps of tar, with one gap; inside, a bedroll and a lantern.
    /// </summary>
    private static void Shelter(Builder b, int cx, int cz, ulong h)
    {
        byte[] furniture = { Props.FilingCabinet, Props.WingChair, Props.HotelChair, Props.FilingCabinet, Props.HotelBookshelf, Props.Wardrobe };
        int gap = (int)((h >> 24) % 4); // the way in: north, east, south or west side
        int i = 0;
        for (int z = cz - 2; z <= cz + 2; z++)
            for (int x = cx - 2; x <= cx + 2; x++, i++)
            {
                if (x < 0 || z < 0 || x >= MacroSize || z >= MacroSize) continue;
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Floor || t.Floor != FloorKind.Seabed) continue;
                int dx = x - cx, dz = z - cz;
                t.Variant = 0;
                t.Stack = 0;
                t.SupplyBox = false;
                if (Math.Max(Math.Abs(dx), Math.Abs(dz)) < 2)
                {
                    // Inside: a bedroll in the middle, a lantern in a corner
                    if (dx == 0 && dz == 0) { t.Variant = Props.Bedroll; t.Pier = (ArchPier)((h >> 30) & 3); }
                    else if (dx == 1 && dz == -1) t.Variant = Props.Lantern;
                    continue;
                }
                ArchPier side = dz == -2 ? ArchPier.North : dz == 2 ? ArchPier.South : dx == 2 ? ArchPier.East : ArchPier.West;
                if (Math.Abs(dx) == 2 && Math.Abs(dz) == 2)
                {
                    t.Detail = L7TarUnder; // a corner: a lump of tar
                    continue;
                }
                if ((int)side == new[] { 2, 1, 3, 0 }[gap] && (dx == 0 || dz == 0)) continue; // the way in
                t.Variant = furniture[(int)((h >> (i % 40)) % (ulong)furniture.Length)];
                t.Pier = Opposite(side); // facing in
                // Some of it stuck down on tar, where the ceiling leaves room (never the tall pieces)
                if (t.Height <= 1 && (i + (int)(h >> 34)) % 2 == 0 && t.Variant is not (Props.HotelBookshelf or Props.Wardrobe)) t.Detail = L7TarUnder;
            }
    }

    /// <summary>
    /// An entry room set into the ceiling (Zone 1), five by five, with its doorway in the middle of the floor (Zone 2)
    /// opening straight down onto the water.
    /// </summary>
    private static void AddEntryRoom(Builder b, int cx, int cz)
    {
        for (int z = cz - 2; z <= cz + 2; z++)
            for (int x = cx - 2; x <= cx + 2; x++)
            {
                ref Tile t = ref b.At(x, z);
                t.Zone = (byte)(x == cx && z == cz ? 2 : 1);
                t.Variant = 0;
                t.SupplyBox = false;
            }
        // The furniture of the room above, by its position in the room
        b.At(cx - 2, cz - 1).Stack = 1; // bookcase
        b.At(cx + 1, cz + 1).Stack = 2; // coffee table
        b.At(cx + 2, cz + 1).Stack = 3; // chair
        b.At(cx, cz).Ceiling = CeilingKind.LightOn; // a fluorescent lamp over the doorway
    }

    /// <summary>
    /// Now and then an old wooden jetty runs out from the ledge over the water, on posts, and simply stops.
    /// </summary>
    private void AddJetty(Builder b, int mx, int mz)
    {
        ulong h = Hashing.Hash(seed, mx, mz, SaltL7Feature + 7);
        if (Hashing.Unit(h) > 0.3) return;
        for (int tries = 0; tries < 40; tries++)
        {
            h = Hashing.Mix(h);
            int lx = 2 + (int)(h % 28), lz = 2 + (int)((h >> 8) % 28);
            if (b.At(lx, lz).Kind != TileKind.Floor || b.At(lx, lz).Floor != FloorKind.Concrete) continue;
            foreach (ArchPier dir in new[] { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West })
            {
                var (x, z) = Step(lx, lz, dir);
                if (b.At(x, z).Kind != TileKind.Water) continue;
                int length = 8 + (int)((h >> 20) % 8);
                for (int k = 0; k < length; k++)
                {
                    if (x < 1 || z < 1 || x > MacroSize - 2 || z > MacroSize - 2) break;
                    ref Tile t = ref b.At(x, z);
                    if (t.Kind != TileKind.Water) break;
                    t.Floor = FloorKind.Jetty;
                    t.Variant = k % 3 == 1 ? Props.JettyPost : (byte)0;
                    t.SupplyBox = false;
                    t.Stack = 0;
                    (x, z) = Step(x, z, dir);
                }
                return;
            }
        }
    }

    /// <summary>A ring of standing stones on the seabed; swim down into its middle (Under = Circle) to leave.</summary>
    private static void AddStoneCircle(Builder b, int cx, int cz)
    {
        for (int z = cz - 5; z <= cz + 5; z++)
            for (int x = cx - 5; x <= cx + 5; x++)
            {
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Water) continue;
                int d2 = (x - cx) * (x - cx) + (z - cz) * (z - cz);
                t.Variant = 0;
                if (d2 >= 16 && d2 <= 25 && (x + z) % 2 == 0) t.Variant = Props.StoneStapler; // a standing stone, oddly shaped
                else if (d2 <= 4) t.Under = Unders.Circle;
            }
    }

    /// <summary>
    /// A patch of white pool tile on the seabed in the twilight zone, faintly lit from nowhere; dive to it (Under =
    /// TiledSeabed) and you surface in the Poolrooms, Level 37.
    /// </summary>
    private static void AddTiledSeabed(Builder b, int cx, int cz)
    {
        for (int z = cz - 3; z <= cz + 3; z++)
            for (int x = cx - 3; x <= cx + 3; x++)
            {
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Water || (x - cx) * (x - cx) + (z - cz) * (z - cz) > 10) continue;
                t.Variant = 0;
                t.Under = Unders.TiledSeabed;
            }
    }

    /// <summary>A cave mouth in the midnight zone (Under = Cave), dropping into the tunnels of Level 8.</summary>
    private static void AddUnderwaterCave(Builder b, int cx, int cz)
    {
        for (int z = cz - 1; z <= cz + 1; z++)
            for (int x = cx - 1; x <= cx + 1; x++)
            {
                ref Tile t = ref b.At(x, z);
                if (t.Kind != TileKind.Water) continue;
                t.Under = Unders.Cave;
                t.Variant = 0;
            }
    }
}
