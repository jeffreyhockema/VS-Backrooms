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
                    if (Hashing.Mod(gx * 7 + gz * 13, 11) == 0) t.Stack = 1; // a boulder of it
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
        bool WallAt(int x, int z)
        {
            if (x < 0 || z < 0) return false;
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

        AddJetty(b, mx, mz);

        double feature = Hashing.Unit(Hashing.Hash(seed, mx, mz, SaltL7Feature));
        int cx = 16, cz = 16, centreDepth = OceanDepth(mx * MacroSize + cx, mz * MacroSize + cz);
        if (feature < 0.14 && centreDepth > 0 && centreDepth < TwilightDepth + 6) AddEntryRoom(b, cx, cz);
        else if (feature < 0.2 && centreDepth >= TwilightDepth && centreDepth < MidnightDepth) AddStoneCircle(b, cx, cz);
        else if (feature < 0.3 && centreDepth >= MidnightDepth && centreDepth < AbyssDepth) AddUnderwaterCave(b, cx, cz);
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
