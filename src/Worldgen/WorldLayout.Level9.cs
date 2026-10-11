using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 9, "The Suburbs": an endless American suburb at midnight, the street lamps mostly dead. Two-lane streets
/// with a dashed centre line, crossings and stop signs at the corners, manhole covers, hydrants, wheelie bins put
/// out for a collection that never comes, cars parked at the kerb. Every house is a little different: siding in
/// white, blue, yellow or green, or brick; a porch or a garage; flower beds and shrubs out front, a basketball hoop
/// over the drive. Inside they are furnished and fairly new: a living room with a sofa and a television that
/// doesn't work, a dining table, a kitchen with cupboards worth searching, a bathroom, a bedroom or two (one of them
/// a child's), a laundry, pictures and clocks on the walls. Behind them, fenced backyards: a patio and a grill, a
/// swing set, a vegetable patch, a dog house with no dog, a shed, now and then a pool, drained. Nothing that needs
/// power works. Behind some houses, a path through a field leads to a gate, and beyond it Level 10.
///
/// The town follows one grid. Streets run east-west every <see cref="TownBlockZ"/> blocks and north-south every
/// <see cref="TownBlockX"/> (a pavement, six of asphalt, a pavement); each block between holds two rows of three
/// lots, <see cref="LotWidth"/> wide and <see cref="LotDepth"/> deep, facing the street to their north or south.
/// Lots are planned from their own position, so neighbouring cells always agree.
/// </summary>
public sealed partial class WorldLayout
{
    private const int LotWidth = 22;
    private const int LotDepth = 28;
    private const int TownBlockX = 8 + 3 * LotWidth;
    private const int TownBlockZ = 8 + 2 * LotDepth;

    /// <summary>The lot a farmhouse is planned in (square, as Level 10 places it).</summary>
    private const int Lot = 18;

    private const ulong SaltL9Lot = 0x9D01;
    private const ulong SaltL9Street = 0x9D02;
    private const ulong SaltL9Car = 0x9D03;

    /// <summary>
    /// From layout version 5, what a Suburbs house's tile carries over its ground floor, in <see cref="Tile.Height"/> (0:
    /// nothing, as in every house before). A two-storey house's tiles say what stands a storey up: its floor is at rel 4
    /// (the ceiling of the ground floor), its rooms rel 5-7, its ceiling rel 8, and the roof is a storey higher. Upstairs,
    /// a floor tile's prop is in <see cref="Tile.Detail"/> (an index into <see cref="UpstairsProps"/>, its facing times 32),
    /// and a wall's or a doorway's paper (0-3 on from <see cref="WallPattern.InteriorFloral"/>). Outside walls go up as
    /// they are below, windows and all (Blank: without the windows, where a wall upstairs meets them). The porch, and
    /// the lawn by a door, carry <see cref="StoreyPorch"/> and their parts: a deck of boards, the steps up to it, a post
    /// holding up its roof, a lamp by the door (lit in the houses that still have power).
    /// </summary>
    public const byte StoreyFloor = 1, StoreyLightOff = 2, StoreyLightOn = 3, StoreyHole = 4, StoreyWall = 5, StoreyDoorway = 6,
        StoreyOuter = 7, StoreyOuterBlank = 8;
    public const byte StoreyPorch = 0x40, PorchDeck = 1, PorchStep = 2, PorchPost = 4, PorchLamp = 8, PorchLampLit = 16;

    /// <summary>The props upstairs in a two-storey house, by their index in <see cref="Tile.Detail"/>: the prop, and which part of it.</summary>
    public static readonly (ushort Prop, byte Stack)[] UpstairsProps =
    {
        (0, 0), (Props.Bed, 0), (Props.Bed, 1), (Props.Nightstand, 0), (Props.Dresser, 0), (Props.Wardrobe, 0), (Props.ToyBox, 0),
        (Props.Bathtub, 0), (Props.Bathtub, 1), (Props.Toilet, 0), (Props.MedCabinet, 0),
    };
    private const byte UpBedHead = 1, UpBedFoot = 2, UpNightstand = 3, UpDresser = 4, UpWardrobe = 5, UpToyBox = 6, UpTubHead = 7,
        UpTubFoot = 8, UpToilet = 9, UpMedCabinet = 10;

    /// <summary>Whether a storey value is a floor upstairs (so its <see cref="Tile.Detail"/> is a prop).</summary>
    public static bool IsUpstairsFloor(byte storey) => storey is StoreyFloor or StoreyLightOff or StoreyLightOn;

    /// <summary>An upstairs prop's facing, turned as its lot is mirrored.</summary>
    private static void TurnUpstairs(ref Tile t, Func<ArchPier, ArchPier> turn)
    {
        if (IsUpstairsFloor(t.Height) && (t.Detail & 31) != 0) t.Detail = (byte)((t.Detail & 31) | ((int)turn((ArchPier)(t.Detail >> 5)) << 5));
    }

    /// <summary>Which lot of the town a block lies in, as a single key (so a house can have one colour of roof).</summary>
    public (int, int) LotKeyAt(int gx, int gz)
    {
        int sx = Hashing.Mod(gx, TownBlockX), sz = Hashing.Mod(gz, TownBlockZ);
        return (Hashing.FloorDiv(gx, TownBlockX) * 3 + Math.Clamp((sx - 8) / LotWidth, 0, 2),
                Hashing.FloorDiv(gz, TownBlockZ) * 2 + (sz >= 8 + LotDepth ? 1 : 0));
    }

    /// <summary>
    /// For the grass: how far back from the pavement a block lies in its Suburbs lot (0 at the front, LotDepth - 1 at
    /// the back fence; -1 on the streets), and whether the lot was planned with a house (the same first draw as
    /// <see cref="LotPlan"/>, so nothing about the plan changes).
    /// </summary>
    public (int V, bool House) SuburbLotDepth(int gx, int gz)
    {
        int sx = Hashing.Mod(gx, TownBlockX), sz = Hashing.Mod(gz, TownBlockZ);
        if (sx < 8 || sz < 8) return (-1, false);
        bool south = sz >= 8 + LotDepth;
        int lotX = Hashing.FloorDiv(gx, TownBlockX) * TownBlockX + 8 + Math.Clamp((sx - 8) / LotWidth, 0, 2) * LotWidth;
        int lotZ = Hashing.FloorDiv(gz, TownBlockZ) * TownBlockZ + 8 + (south ? LotDepth : 0);
        var rng = new Rng(Hashing.Hash(seed, lotX, lotZ, SaltL9Lot));
        return (south ? TownBlockZ - 1 - sz : sz - 8, rng.NextDouble() < 0.88);
    }

    private void BuildLevel9(Builder b, int mx, int mz)
    {
        int x0 = mx * MacroSize, z0 = mz * MacroSize;
        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                int gx = x0 + lx, gz = z0 + lz;
                int sx = Hashing.Mod(gx, TownBlockX), sz = Hashing.Mod(gz, TownBlockZ);
                t.Floor = FloorKind.Lawn;
                if (sx >= 8 && sz >= 8) continue; // a lot; filled from its plan below
                StreetTile(ref t, gx, gz, sx, sz);
            }
        }

        // Cars parked along the kerbs of the north-south streets
        int bx0 = Hashing.FloorDiv(x0, TownBlockX), bz0 = Hashing.FloorDiv(z0, TownBlockZ);
        for (int bz = bz0 - 1; bz <= bz0 + 1; bz++)
            for (int bx = bx0 - 1; bx <= bx0 + 1; bx++)
                for (int slot = 0; slot < 8; slot++)
                    for (int side = 0; side < 2; side++)
                    {
                        bool east = side == 1;
                        int cx = bx * TownBlockX + (east ? 5 : 1), cz = bz * TownBlockZ + 9 + slot * 7;
                        ulong h = Hashing.Hash(seed, cx, cz, SaltL9Car);
                        if (Hashing.Unit(h) > 0.22) continue;
                        if (cx + 1 < x0 || cx > x0 + MacroSize || cz + 3 < z0 || cz > z0 + MacroSize) continue;
                        PlaceCar(b, x0, z0, cx, cz, noseNorth: east, (int)(h >> 20) % 4);
                    }

        // Copy in every lot that overlaps this cell
        for (int bz = bz0 - 1; bz <= bz0 + 1; bz++)
        {
            for (int bx = bx0 - 1; bx <= bx0 + 1; bx++)
            {
                for (int li = 0; li < 6; li++)
                {
                    int lotX = bx * TownBlockX + 8 + (li % 3) * LotWidth, lotZ = bz * TownBlockZ + 8 + (li / 3) * LotDepth;
                    if (lotX > x0 + MacroSize || lotZ > z0 + MacroSize || lotX + LotWidth < x0 || lotZ + LotDepth < z0) continue;
                    bool facesSouth = li / 3 == 1; // the lots in the south half face the street to their south
                    // No house is built where its street would lie beyond the edge of the town, nor where the edge
                    // of the town would cut through it
                    int streetLevel = LevelAt(MacroOf(lotX + LotWidth / 2), MacroOf(facesSouth ? lotZ + LotDepth + 3 : lotZ - 4));
                    if (streetLevel is not (9 or 10) || !AllLevel(9, lotX, lotZ, LotWidth, LotDepth)) continue;
                    Tile[] plan = LotPlan(lotX, lotZ);
                    for (int v = 0; v < LotDepth; v++)
                    {
                        for (int u = 0; u < LotWidth; u++)
                        {
                            int lx = lotX + u - x0, lz = lotZ + (facesSouth ? LotDepth - 1 - v : v) - z0;
                            if (lx < 0 || lz < 0 || lx >= MacroSize || lz >= MacroSize) continue;
                            ref Tile t = ref b.At(lx, lz);
                            if (t.Kind != TileKind.Floor && t.Kind != TileKind.Bars) continue;
                            if ((lx == 0 || lz == 0) && t.Kind != TileKind.Floor) continue; // the cell's own edge
                            t = plan[v * LotWidth + u];
                            if (facesSouth)
                            {
                                // A car is drawn from its front-left corner, which moves when the lot is mirrored
                                if (t.Variant == Props.Car) t.Variant = Props.CarPart;
                                else if (t.Variant == Props.CarPart && u > 0 && plan[v * LotWidth + u - 1].Variant == Props.Car) t.Variant = Props.Car;
                                t.Pier = MirrorNS(t.Pier);
                                t.Roof = RoofBits.Turned(t.Roof, MirrorNS);
                                TurnUpstairs(ref t, MirrorNS);
                                if (t.Kind == TileKind.Bars) t.Stack = MirrorMask(t.Stack);
                            }
                        }
                    }
                }
            }
        }
    }

    /// <summary>The streets: pavements, asphalt with its markings, and what stands on the kerbs.</summary>
    private void StreetTile(ref Tile t, int gx, int gz, int sx, int sz)
    {
        ulong h = Hashing.Hash(seed, gx, gz, SaltL9Street);
        double r = Hashing.Unit(h);
        bool roadX = sz is >= 1 and <= 6, roadZ = sx is >= 1 and <= 6; // east-west and north-south carriageways
        if (roadX || roadZ)
        {
            // Puddles and drifts of dead leaves lie in patches, not scattered tile by tile
            double wet = Noise(gx / 5.0, gz / 5.0, SaltL9Street + 1), leaves = Noise(gx / 4.0, gz / 4.0, SaltL9Street + 2);
            t.Floor = wet > 0.48 ? FloorKind.AsphaltWet : leaves > 0.5 ? FloorKind.AsphaltLeaves : FloorKind.Asphalt;
            if (roadX && roadZ) return; // the junction itself
            int along = roadX ? sx : sz, across = roadX ? sz : sx, run = roadX ? gx : gz, block = roadX ? TownBlockX : TownBlockZ;
            // The roads were never painted: wet asphalt, leaves, and the odd manhole
            if (across == 5 && Hashing.Mod(run, 52) == 26 && along is > 9 && along < block - 2) t.Floor = FloorKind.Manhole;
            return;
        }

        t.Floor = FloorKind.Sidewalk;
        // Stop signs on the corners of a few junctions, facing the traffic coming into them
        bool signed = Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(gx + 8, TownBlockX), Hashing.FloorDiv(gz + 8, TownBlockZ), SaltL9Street + 3)) < 0.2;
        if (signed && sx == 7 && sz == 7) { t.Variant = Props.StopSign; t.Pier = ArchPier.South; return; }
        if (signed && sx == 0 && sz == 0) { t.Variant = Props.StopSign; t.Pier = ArchPier.North; return; }
        if (Version >= 5)
        {
            int jx = Hashing.FloorDiv(gx, TownBlockX), jz = Hashing.FloorDiv(gz, TownBlockZ);
            // On one corner of every junction, the names of the two streets: the same all along each street (and only
            // sixteen names between them, over and over)
            if (sx == 7 && sz == 0)
            {
                t.Variant = Props.SuburbSign;
                t.Stack = (byte)(Hashing.Hash(seed, 0, jz, SaltL9Street + 6) % 8);
                t.Detail = (byte)(Hashing.Hash(seed, jx, 0, SaltL9Street + 7) % 8);
                return;
            }
            // At one junction in six, a sign pointing the way to the city: down whichever street heads more nearly
            // toward it (now and then the other, as a road would wind)
            ulong guide = Hashing.Hash(seed, jx, jz, SaltL9Street + 5);
            if (sx == 0 && sz == 7 && Hashing.Unit(guide) < 1 / 6.0)
            {
                double dx = CityOriginX - gx, dz = CityOriginZ - gz;
                bool alongX = Hashing.Unit(Hashing.Mix(guide)) * (Math.Abs(dx) + Math.Abs(dz)) < Math.Abs(dx);
                t.Variant = Props.CitySign;
                t.Pier = alongX ? (dx > 0 ? ArchPier.East : ArchPier.West) : (dz > 0 ? ArchPier.South : ArchPier.North);
                return;
            }
        }
        // Street lamps along the pavements on the lot side, every 16 blocks; most are dead
        bool lampX = sz == 7 && sx >= 8 && Hashing.Mod(gx, 16) == 12;
        bool lampZ = sx == 7 && sz >= 8 && Hashing.Mod(gz, 16) == 4;
        if (lampX || lampZ)
        {
            t.Variant = Props.Streetlight;
            t.Pier = lampX ? ArchPier.North : ArchPier.West;
            t.Stack = (byte)(r < 0.15 ? 0 : r < 0.3 ? 2 : 1);
            return;
        }
        // Fire hydrants now and then
        if ((sz == 0 && sx >= 8 && Hashing.Mod(gx, 46) == 30) || (sx == 0 && sz >= 8 && Hashing.Mod(gz, 46) == 20))
        {
            t.Variant = Props.FireHydrant;
            t.Pier = sz == 0 ? ArchPier.North : ArchPier.West;
        }
    }

    private static ArchPier MirrorNS(ArchPier p) => p == ArchPier.North ? ArchPier.South : p == ArchPier.South ? ArchPier.North : p;

    private static ArchPier MirrorEW(ArchPier p) => p == ArchPier.East ? ArchPier.West : p == ArchPier.West ? ArchPier.East : p;

    private static byte MirrorMask(byte m) => (byte)((m & ~5) | ((m & 1) << 2) | ((m & 4) >> 2));

    private static byte MirrorMaskEW(byte m) => (byte)((m & ~10) | ((m & 2) << 2) | ((m & 8) >> 2));

    /// <summary>Whether the cells under every corner of a rectangle are all of one level.</summary>
    private bool AllLevel(int level, int x, int z, int sizeX, int sizeZ) =>
        LevelAt(MacroOf(x), MacroOf(z)) == level && LevelAt(MacroOf(x + sizeX - 1), MacroOf(z)) == level
        && LevelAt(MacroOf(x), MacroOf(z + sizeZ - 1)) == level && LevelAt(MacroOf(x + sizeX - 1), MacroOf(z + sizeZ - 1)) == level;

    private bool AllLevel(int level, int x, int z, int size) => AllLevel(level, x, z, size, size);

    private enum LotKind { House, Field, Empty }

    /// <summary>
    /// Plans one lot in its own coordinates: u runs along the street, v away from it (v = 0 is the front, at the
    /// pavement). <see cref="ArchPier.North"/> in the plan means "toward the street".
    /// </summary>
    private Tile[] LotPlan(int lotX, int lotZ)
    {
        const int w = LotWidth, d = LotDepth;
        var tiles = new Tile[w * d];
        ulong h = Hashing.Hash(seed, lotX, lotZ, SaltL9Lot);
        var rng = new Rng(h);
        ref Tile At(int u, int v) => ref tiles[v * w + u];
        for (int i = 0; i < tiles.Length; i++) tiles[i].Floor = FloorKind.Lawn;

        double r = rng.NextDouble();
        // Now and then, in the far suburbs, a lot is a grass field with a path running off between the houses
        // toward Level 10
        bool farOut = RingFraction(lotX + w / 2, lotZ + d / 2, 9) > 0.66;
        LotKind kind = r < 0.88 ? LotKind.House : r < 0.89 && farOut ? LotKind.Field : LotKind.Empty;

        // A wooden fence round the backyard (connections: N1 E2 S4 W8)
        void Fence(int u, int v, byte mask)
        {
            ref Tile t = ref At(u, v);
            t.Kind = TileKind.Bars;
            t.Pattern = WallPattern.Fence;
            t.Variant = 0;
            t.Stack = mask;
        }
        int fenceFrom = kind == LotKind.House ? 18 : 8;
        for (int u = 0; u < w; u++) Fence(u, d - 1, (byte)((u > 0 ? 8 : 0) | (u < w - 1 ? 2 : 0) | (u == 0 || u == w - 1 ? 1 : 0)));
        for (int v = fenceFrom; v < d - 1; v++)
        {
            Fence(0, v, (byte)(4 | (v > fenceFrom ? 1 : 0)));
            Fence(w - 1, v, (byte)(4 | (v > fenceFrom ? 1 : 0)));
        }

        void Tree(int u, int v)
        {
            At(u, v).Variant = Props.Tree;
            for (int dv = -1; dv <= 1; dv++)
                for (int du = -1; du <= 1; du++)
                    if ((du != 0 || dv != 0) && At(u + du, v + dv).Kind == TileKind.Floor) At(u + du, v + dv).Overhead = Overheads.Leaves;
        }

        switch (kind)
        {
            case LotKind.House:
            {
                var house = PlanHouse(tiles, w, ref rng, farmhouse: false, v5: Version >= 5);
                PlanFrontYard(tiles, w, house, ref rng);
                PlanBackyard(tiles, w, d, house, ref rng);
                // About one backyard pool in seventeen was never drained: lit teal at midnight, and its bottom is not the
                // bottom (Level 37). One house in a hundred and fifty is a doll's house, too clean and too cream, and
                // its front door opens onto Level 94
                ulong odd = Hashing.Hash(seed, lotX, lotZ, SaltL9Lot + 37);
                if (Hashing.Unit(odd) < 0.06)
                    for (int i = 0; i < tiles.Length; i++)
                        if (tiles[i].Floor == FloorKind.PoolDeep) tiles[i].Under = Unders.FullPool;
                if (Hashing.Unit(Hashing.Mix(odd)) < 1 / 150.0)
                {
                    for (int i = 0; i < tiles.Length; i++)
                        if (tiles[i].Pattern is >= WallPattern.SidingWhite and <= WallPattern.Brick) tiles[i].Pattern = WallPattern.SidingYellow;
                    ref Tile front = ref At(house.DoorU, house.V0);
                    front.Kind = TileKind.Door;
                    front.Under = Unders.DollHouse;
                }
                if (rng.Chance(0.55)) Tree(rng.Chance(0.5) ? 2 : w - 3, 2);
                // Some lots are mirrored, so the garages and porches are not all on one side
                if (rng.Chance(0.5)) FlipU(tiles, w, d);
                break;
            }
            case LotKind.Field:
            {
                // A path through long grass to a gate in the back fence: the way to Level 10
                for (int v = 0; v < d - 1; v++)
                {
                    At(9, v).Floor = FloorKind.DirtRoad;
                    At(10, v).Floor = FloorKind.DirtRoad;
                }
                for (int v = 1; v < d - 1; v++)
                    for (int u = 1; u < w - 1; u++)
                        if (u is not (9 or 10) && At(u, v).Kind == TileKind.Floor)
                        {
                            if (rng.Chance(0.55)) At(u, v).Variant = Props.TallGrass;
                            else if (rng.Chance(0.04)) { At(u, v).Variant = Props.Flowers; At(u, v).Stack = (byte)rng.Range(0, 7); }
                        }
                foreach (int u in new[] { 9, 10 })
                {
                    ref Tile gate = ref At(u, d - 1);
                    gate.Kind = TileKind.Floor;
                    gate.Variant = Props.FieldGate;
                    gate.Pier = ArchPier.North;
                    gate.Floor = FloorKind.DirtRoad;
                }
                // The fence posts beside the gate stop at it
                At(8, d - 1).Stack &= unchecked((byte)~2);
                At(11, d - 1).Stack &= unchecked((byte)~8);
                break;
            }
            default:
            {
                // Overgrown and empty but for a tree or two, and sometimes a car left on it
                for (int v = 1; v < d - 2; v++)
                    for (int u = 1; u < w - 1; u++)
                        if (rng.Chance(0.2)) At(u, v).Variant = Props.TallGrass;
                Tree(4, 6);
                if (rng.Chance(0.5)) Tree(14, 14);
                if (rng.Chance(0.4))
                    for (int dv = 0; dv < 4; dv++)
                        for (int du = 0; du < 2; du++)
                        {
                            ref Tile c = ref At(9 + du, 3 + dv);
                            c.Variant = du == 0 && dv == 0 ? Props.Car : Props.CarPart;
                            c.Stack = (byte)(h % 4);
                            c.Pier = ArchPier.North;
                        }
                break;
            }
        }
        return tiles;
    }

    /// <summary>Mirrors a lot plan left to right.</summary>
    private static void FlipU(Tile[] tiles, int w, int d)
    {
        for (int v = 0; v < d; v++)
            for (int u = 0; u < w / 2; u++)
                (tiles[v * w + u], tiles[v * w + w - 1 - u]) = (tiles[v * w + w - 1 - u], tiles[v * w + u]);
        for (int i = 0; i < tiles.Length; i++)
        {
            ref Tile t = ref tiles[i];
            t.Pier = MirrorEW(t.Pier);
            t.Roof = RoofBits.Turned(t.Roof, MirrorEW);
            TurnUpstairs(ref t, MirrorEW);
            if (t.Kind == TileKind.Bars) t.Stack = MirrorMaskEW(t.Stack);
            // A corner of a house: the side its second face looks out on swaps too
            else if (t.Kind == TileKind.Wall && t.Stack is 1 or 2 && t.Pattern >= WallPattern.SidingWhite && t.Pattern <= WallPattern.Brick) t.Stack = (byte)(3 - t.Stack);
        }
        // A car's model hangs off its anchor's minimum corner, which is now the other side of it
        for (int v = 0; v < d; v++)
            for (int u = 1; u < w; u++)
                if (tiles[v * w + u].Variant == Props.Car && tiles[v * w + u - 1].Variant == Props.CarPart)
                {
                    tiles[v * w + u].Variant = Props.CarPart;
                    tiles[v * w + u - 1].Variant = Props.Car;
                }
    }

    private enum HousePlan { Family, Garage, Porch }

    /// <summary>Where a house stands in its lot, and what it has, for the yards round it.</summary>
    private readonly record struct House(int U0, int U1, int V0, int V1, int DoorU, int BackDoorU, bool Garage, int GarageU0, int GarageU1, bool Locked);

    /// <summary>
    /// A house in lot coordinates, its front wall at v = 6 (or 7 behind a porch), on one of a few plans. The lot is
    /// <paramref name="w"/> wide; the farmhouses of Level 10 are planned in an 18-wide lot with their front at v = 5.
    /// From layout version 5 (<paramref name="v5"/>, the Suburbs only) the houses are less alike: about a third have two
    /// storeys (a hall up the middle with the stairs in it, bedrooms upstairs), half have a porch on posts with steps up
    /// to it, every door has a lamp by it, and the windows come in one of three rhythms.
    /// </summary>
    private static House PlanHouse(Tile[] tiles, int w, ref Rng rng, bool farmhouse, bool v5 = false)
    {
        ref Tile At(int u, int v) => ref tiles[v * w + u];
        HousePlan kind = farmhouse ? HousePlan.Family : (HousePlan)rng.Range(0, 2);
        bool porch = kind == HousePlan.Porch || farmhouse && rng.Chance(0.6);
        // A side path of two blocks either side of the house; a porch house sits a little narrower and further back
        int u0 = 2, u1 = w - 3, v0 = farmhouse ? 5 : 6, v1 = v0 + 11;
        if (kind == HousePlan.Porch) { u0 = 3; u1 = w - 4; v0 += 2; v1 = v0 + 9; }
        var siding = (WallPattern)((int)WallPattern.SidingWhite + rng.Range(0, 4));
        var paper = (WallPattern)((int)WallPattern.InteriorFloral + rng.Range(0, 3));
        var paper2 = (WallPattern)((int)WallPattern.InteriorFloral + rng.Range(0, 3));
        bool locked = !farmhouse && rng.Chance(0.15);
        bool litWindows = rng.Chance(0.1);
        bool garage = kind == HousePlan.Garage;
        // Layout version 5: two storeys over a narrower, deeper house (its porch, if any, in front of it), more porches,
        // and the windows in pairs, every other block, or every third as before
        bool twoStorey = false;
        int rhythm = 0;
        if (v5)
        {
            twoStorey = kind != HousePlan.Garage && rng.Chance(0.55);
            if (kind == HousePlan.Family && rng.Chance(0.45)) porch = true;
            rhythm = rng.Range(0, 2);
            if (twoStorey) { u0 = 3; u1 = w - 4; v0 = 6; v1 = v0 + 11; }
        }
        bool WindowAt(int u, int v) => rhythm switch
        {
            1 => (u + v) % 4 is 1 or 2,
            2 => (u + v) % 2 == 1,
            _ => (u + v) % 3 == 0,
        };

        void Wall(int u, int v, WallPattern p)
        {
            ref Tile t = ref At(u, v);
            SetWall(ref t, p, BaseStyle.Plain);
        }
        void Room(int a0, int b0, int a1, int b1, FloorKind floor, bool light = true)
        {
            for (int v = b0; v <= b1; v++)
                for (int u = a0; u <= a1; u++)
                {
                    ref Tile t = ref At(u, v);
                    t.Kind = TileKind.Floor;
                    t.Floor = floor;
                    t.Variant = 0;
                }
            // A ceiling light in the middle of the room: off, unless the house still has power
            if (light) At((a0 + a1) / 2, (b0 + b1) / 2).Ceiling = litWindows ? CeilingKind.LightOn : CeilingKind.LightOff;
        }
        void Put(int u, int v, byte prop, ArchPier facing, byte stack = 0)
        {
            ref Tile t = ref At(u, v);
            if (t.Kind != TileKind.Floor) return;
            t.Variant = prop;
            t.Pier = facing;
            t.Stack = stack;
        }
        void Doorway(int u, int v) { At(u, v).Kind = TileKind.Doorway; At(u, v).Variant = 0; }
        // Something on an inside wall (a photo, a painting, a clock, a mirror), facing into the room on one side
        void Hang(int u, int v, byte decor, ArchPier facing)
        {
            ref Tile t = ref At(u, v);
            if (t.Kind != TileKind.Wall || t.Pattern < WallPattern.InteriorFloral || t.Pattern > WallPattern.InteriorGreen) return;
            t.Variant = decor;
            t.Pier = facing;
        }
        void PartitionX(int u, int b0, int b1, WallPattern p) { for (int v = b0; v <= b1; v++) Wall(u, v, p); }
        void PartitionZ(int v, int a0, int a1, WallPattern p) { for (int u = a0; u <= a1; u++) Wall(u, v, p); }

        // Shell: siding outside, windows at head height, a chimney; the outside face is recorded so the inside can be papered
        for (int v = v0; v <= v1; v++)
            for (int u = u0; u <= u1; u++)
            {
                bool edge = u == u0 || u == u1 || v == v0 || v == v1;
                if (!edge) { At(u, v).Floor = FloorKind.HouseWood; continue; }
                Wall(u, v, siding);
                ref Tile t = ref At(u, v);
                t.Pier = v == v0 ? ArchPier.North : v == v1 ? ArchPier.South : u == u0 ? ArchPier.West : ArchPier.East;
                bool corner = (u == u0 || u == u1) && (v == v0 || v == v1);
                if (corner) t.Stack = (byte)(u == u1 ? 1 : 2); // its second outside face: 1 east, 2 west
                else if (WindowAt(u, v)) t.Variant = (byte)(litWindows && rng.Chance(0.5) ? 2 : 1);
            }
        int chimneyV = (v0 + v1) / 2 + rng.Range(-2, 2);
        At(u0, chimneyV).Variant = 3; // a brick chimney up the side wall

        int doorU, backDoorU;
        int mid = v0 + 5; // the wall between the front rooms and the back
        int garageU0 = 0, garageU1 = 0;
        switch (kind)
        {
            case HousePlan.Family or HousePlan.Porch when twoStorey:
            {
                // Two storeys, like the houses in the pictures. Downstairs a hall from the front door to the kitchen, the
                // stairs up one side of it; the dining room on one side of the hall, the living room on the other; the
                // kitchen, a bathroom and a utility room behind. Upstairs, off a landing across the house, three
                // bedrooms (one a child's) and a bathroom
                int hall = u0 + 6, stair = u0 + 7, k1 = u0 + 8, b1 = u0 + 11;
                PartitionX(hall - 1, v0 + 1, mid - 1, paper2);
                PartitionX(stair + 1, v0 + 1, mid - 1, paper2);
                PartitionZ(mid, u0 + 1, u1 - 1, paper);
                PartitionX(k1, mid + 1, v1 - 1, paper);
                PartitionX(b1, mid + 1, v1 - 1, paper);
                Room(u0 + 1, v0 + 1, hall - 2, mid - 1, FloorKind.HouseWood);
                Room(hall, v0 + 1, stair, mid - 1, FloorKind.HouseWood);
                Room(stair + 2, v0 + 1, u1 - 1, mid - 1, FloorKind.HouseCarpet);
                Room(u0 + 1, mid + 1, k1 - 1, v1 - 1, FloorKind.HouseLino);
                Room(k1 + 1, mid + 1, b1 - 1, v1 - 1, FloorKind.HouseTile);
                Room(b1 + 1, mid + 1, u1 - 1, v1 - 1, FloorKind.HouseLino);
                Doorway(hall - 1, v0 + 3); Doorway(stair + 1, v0 + 1);
                Doorway(hall, mid); Doorway(k1 + 1, mid); Doorway(b1 + 2, mid);
                // The stairs: four steps up the side of the hall away from the street, the last in the line of the wall
                // behind, coming out on the landing
                for (int s = 1; s <= 4; s++)
                {
                    ref Tile step = ref At(stair, v0 + 1 + s);
                    step.Kind = TileKind.Floor;
                    step.Floor = FloorKind.HouseWood;
                    step.Variant = 0;
                    step.Stair = (byte)s;
                    step.Pier = ArchPier.South;
                }
                // Dining room: a table laid for nobody
                Put(u0 + 2, v0 + 3, Props.DiningTable, ArchPier.North);
                Put(u0 + 1, v0 + 3, Props.HotelChair, ArchPier.East);
                Put(u0 + 3, v0 + 3, Props.HotelChair, ArchPier.West);
                Put(u0 + 2, v0 + 2, Props.HotelChair, ArchPier.South);
                Put(u0 + 2, v0 + 4, Props.HotelChair, ArchPier.North);
                Put(u0 + 4, v0 + 1, Props.CurioCabinet, ArchPier.West);
                // Living room
                Put(u1 - 1, v0 + 1, Props.OfficeBookshelf, ArchPier.West);
                Put(u1 - 1, v0 + 3, Props.Tv, ArchPier.West);
                Put(stair + 3, v0 + 3, Props.Sofa, ArchPier.East);
                Put(stair + 5, v0 + 3, Props.CoffeeTable, ArchPier.North);
                Put(stair + 5, v0 + 1, Props.WingChair, ArchPier.South);
                Put(u1 - 1, v0 + 4, Props.FloorLamp, ArchPier.North);
                for (int u = stair + 4; u <= stair + 6; u++) for (int v = v0 + 2; v <= v0 + 3; v++) At(u, v).Floor = FloorKind.HouseRug;
                // Kitchen
                Put(u0 + 1, v1 - 1, Props.KitchenCabinet, ArchPier.North);
                Put(u0 + 3, v1 - 1, Props.KitchenCounter, ArchPier.North, 1);
                Put(u0 + 4, v1 - 1, Props.Stove, ArchPier.North);
                Put(u0 + 5, v1 - 1, Props.KitchenCabinet, ArchPier.North);
                Put(k1 - 1, v1 - 1, Props.Fridge, ArchPier.North);
                Put(u0 + 1, mid + 2, Props.KitchenCabinet, ArchPier.East);
                Put(u0 + 3, mid + 3, Props.RoundTable, ArchPier.North);
                Put(u0 + 2, mid + 3, Props.HotelChair, ArchPier.East);
                Put(u0 + 4, mid + 3, Props.HotelChair, ArchPier.West);
                Put(k1 - 1, mid + 1, Props.PantryShelf, ArchPier.West);
                // Bathroom
                Put(k1 + 1, v1 - 1, Props.Bathtub, ArchPier.East, 0);
                Put(k1 + 2, v1 - 1, Props.Bathtub, ArchPier.East, 1);
                Put(k1 + 2, mid + 1, Props.Toilet, ArchPier.West);
                Put(k1 + 2, mid + 3, Props.MedCabinet, ArchPier.West);
                // Utility room: the laundry, and the shelves nobody else had room for
                Put(b1 + 1, v1 - 1, Props.Laundry, ArchPier.North, 0);
                Put(b1 + 2, v1 - 1, Props.Laundry, ArchPier.North, 1);
                Put(u1 - 1, mid + 1, Props.PantryShelf, ArchPier.West);
                Put(b1 + 1, mid + 2, Props.ToolShelf, ArchPier.East);
                doorU = hall;
                backDoorU = u0 + 2;
                Hang(hall - 1, v0 + 1, Decor.FamilyPhoto, ArchPier.East);
                Hang(stair + 1, v0 + 3, Decor.HousePainting, ArchPier.East);
                Hang(k1, mid + 2, Decor.HouseClock, ArchPier.West);

                // Upstairs: floor over everything inside the outside walls, which go on up
                void Up(int u, int v, byte storey, byte detail = 0) { At(u, v).Height = storey; At(u, v).Detail = detail; }
                void UpWall(int u, int v) => Up(u, v, StoreyWall, (byte)(paper - WallPattern.InteriorFloral));
                void UpDoor(int u, int v) => Up(u, v, StoreyDoorway, (byte)(paper - WallPattern.InteriorFloral));
                void UpProp(int u, int v, byte prop, ArchPier facing) => At(u, v).Detail = (byte)(prop | (int)facing << 5);
                for (int v = v0; v <= v1; v++)
                    for (int u = u0; u <= u1; u++)
                        Up(u, v, u == u0 || u == u1 || v == v0 || v == v1 ? StoreyOuter : StoreyFloor);
                // The stairwell, walled in, open over the second and third steps
                for (int v = v0 + 1; v <= v0 + 4; v++) { UpWall(hall, v); UpWall(stair + 1, v); }
                UpWall(stair, v0 + 1); UpWall(stair, v0 + 2);
                Up(stair, v0 + 3, StoreyHole); Up(stair, v0 + 4, StoreyHole);
                // Two bedrooms at the front, across the landing from a bedroom, the bathroom and another bedroom
                for (int u = u0 + 1; u < u1; u++)
                {
                    if (u < hall || u > stair + 1) UpWall(u, v0 + 4);
                    UpWall(u, mid + 1);
                }
                for (int v = mid + 2; v < v1; v++) { UpWall(hall, v); UpWall(u0 + 9, v); }
                UpDoor(u0 + 3, v0 + 4); UpDoor(u0 + 11, v0 + 4);
                UpDoor(u0 + 3, mid + 1); UpDoor(stair + 1, mid + 1); UpDoor(u0 + 12, mid + 1);
                byte lamp = litWindows ? StoreyLightOn : StoreyLightOff;
                foreach (var (lu, lv) in new[] { (u0 + 3, v0 + 2), (u0 + 11, v0 + 2), (u0 + 4, mid), (u0 + 3, mid + 3), (stair, mid + 3), (u0 + 12, mid + 3) })
                    At(lu, lv).Height = lamp;
                // The front bedrooms: the parents' and a child's
                UpProp(u0 + 2, v0 + 1, UpBedHead, ArchPier.South); UpProp(u0 + 2, v0 + 2, UpBedFoot, ArchPier.South);
                UpProp(u0 + 1, v0 + 1, UpNightstand, ArchPier.South); UpProp(u0 + 3, v0 + 1, UpNightstand, ArchPier.South);
                UpProp(u0 + 5, v0 + 2, UpDresser, ArchPier.West); UpProp(u0 + 5, v0 + 1, UpWardrobe, ArchPier.West);
                UpProp(u0 + 13, v0 + 1, UpBedHead, ArchPier.South); UpProp(u0 + 13, v0 + 2, UpBedFoot, ArchPier.South);
                UpProp(u0 + 14, v0 + 1, UpNightstand, ArchPier.South);
                UpProp(u0 + 9, v0 + 3, UpToyBox, ArchPier.East); UpProp(u0 + 9, v0 + 1, UpDresser, ArchPier.East);
                // At the back: a bedroom, the bathroom, a guest room
                UpProp(u0 + 3, v1 - 1, UpBedHead, ArchPier.North); UpProp(u0 + 3, v1 - 2, UpBedFoot, ArchPier.North);
                UpProp(u0 + 2, v1 - 1, UpNightstand, ArchPier.North); UpProp(u0 + 4, v1 - 1, UpNightstand, ArchPier.North);
                UpProp(u0 + 1, mid + 2, UpWardrobe, ArchPier.East); UpProp(u0 + 5, mid + 2, UpDresser, ArchPier.West);
                UpProp(stair, v1 - 1, UpTubHead, ArchPier.East); UpProp(stair + 1, v1 - 1, UpTubFoot, ArchPier.East);
                UpProp(stair, mid + 2, UpToilet, ArchPier.East); UpProp(stair, mid + 3, UpMedCabinet, ArchPier.East);
                UpProp(u1 - 1, v1 - 2, UpBedHead, ArchPier.West); UpProp(u1 - 2, v1 - 2, UpBedFoot, ArchPier.West);
                UpProp(u1 - 1, v1 - 1, UpNightstand, ArchPier.West);
                UpProp(u0 + 10, v1 - 1, UpWardrobe, ArchPier.North); UpProp(u0 + 10, mid + 2, UpToyBox, ArchPier.East);
                // No window upstairs where a wall inside meets it
                for (int v = v0; v <= v1; v++)
                    for (int u = u0; u <= u1; u++)
                    {
                        if (At(u, v).Height != StoreyOuter) continue;
                        int iu = u == u0 ? u + 1 : u == u1 ? u - 1 : u, iv = v == v0 ? v + 1 : v == v1 ? v - 1 : v;
                        if (At(iu, iv).Height == StoreyWall) At(u, v).Height = StoreyOuterBlank;
                    }
                break;
            }
            case HousePlan.Garage:
            {
                // Living room at the front, kitchen-diner, bathroom and bedroom behind; a garage down one side
                garageU0 = u1 - 5;
                garageU1 = u1;
                int hu1 = garageU0; // the garage's inner wall
                PartitionX(hu1, v0 + 1, v1 - 1, paper);
                PartitionZ(mid, u0 + 1, hu1 - 1, paper);
                Room(u0 + 1, v0 + 1, hu1 - 1, mid - 1, FloorKind.HouseCarpet);
                int k1 = u0 + 5, bath1 = k1 + 3;
                PartitionX(k1, mid + 1, v1 - 1, paper2);
                PartitionX(bath1, mid + 1, v1 - 1, paper2);
                Room(u0 + 1, mid + 1, k1 - 1, v1 - 1, FloorKind.HouseLino);
                Room(k1 + 1, mid + 1, bath1 - 1, v1 - 1, FloorKind.HouseTile);
                Room(bath1 + 1, mid + 1, hu1 - 1, v1 - 1, FloorKind.HouseCarpet);
                Doorway(u0 + 3, mid); Doorway(k1 + 1, mid); Doorway(bath1 + 2, mid);
                // Living room
                Put(u0 + 1, v0 + 2, Props.Tv, ArchPier.East);
                Put(u0 + 3, v0 + 2, Props.CoffeeTable, ArchPier.North);
                Put(u0 + 5, v0 + 2, Props.Sofa, ArchPier.West);
                Put(u0 + 1, v0 + 4, Props.FloorLamp, ArchPier.North);
                Put(hu1 - 1, v0 + 1, Props.OfficeBookshelf, ArchPier.West);
                Put(u0 + 5, v0 + 4, Props.WingChair, ArchPier.West);
                for (int u = u0 + 2; u <= u0 + 4; u++) At(u, v0 + 3).Floor = FloorKind.HouseRug;
                // Kitchen-diner
                Put(u0 + 1, v1 - 1, Props.KitchenCabinet, ArchPier.North);
                Put(u0 + 2, v1 - 1, Props.Stove, ArchPier.North);
                Put(u0 + 3, v1 - 1, Props.KitchenCounter, ArchPier.North, 1);
                Put(u0 + 4, v1 - 1, Props.Fridge, ArchPier.North);
                Put(u0 + 1, mid + 2, Props.KitchenCabinet, ArchPier.East);
                Put(u0 + 3, mid + 2, Props.RoundTable, ArchPier.North);
                Put(u0 + 4, mid + 2, Props.HotelChair, ArchPier.West);
                Put(u0 + 2, mid + 2, Props.HotelChair, ArchPier.East);
                // Bathroom
                Put(k1 + 1, v1 - 1, Props.Bathtub, ArchPier.East, 0);
                Put(k1 + 2, v1 - 1, Props.Bathtub, ArchPier.East, 1);
                Put(k1 + 2, mid + 2, Props.Toilet, ArchPier.West);
                Put(k1 + 1, mid + 3, Props.MedCabinet, ArchPier.East);
                // Bedroom
                Put(bath1 + 2, v1 - 1, Props.Bed, ArchPier.North, 0);
                Put(bath1 + 2, v1 - 2, Props.Bed, ArchPier.North, 1);
                Put(bath1 + 1, v1 - 1, Props.Nightstand, ArchPier.North);
                Put(hu1 - 1, mid + 1, Props.Dresser, ArchPier.West);
                // The garage: a closed roller door onto the drive, a door in from the house, tools, the laundry
                Room(garageU0 + 1, v0 + 1, garageU1 - 1, v1 - 1, FloorKind.Garage, light: false);
                Doorway(hu1, mid + 2);
                for (int u = garageU0 + 1; u <= garageU0 + 3; u++)
                {
                    ref Tile door = ref At(u, v0);
                    door.Kind = TileKind.Door;
                    door.Pattern = WallPattern.GarageDoor;
                    door.Variant = 0;
                    door.Stack = (byte)(siding - WallPattern.SidingWhite); // the siding over it
                }
                if (rng.Chance(0.5))
                {
                    // A car parked nose-in: the anchor tile draws it, the rest are colliders
                    for (int dv = 0; dv < 4; dv++)
                        for (int du = 0; du < 2; du++)
                        {
                            ref Tile c = ref At(garageU0 + 1 + du, v0 + 1 + dv);
                            c.Variant = du == 0 && dv == 0 ? Props.Car : Props.CarPart;
                            c.Stack = (byte)rng.Range(0, 3);
                            c.Pier = ArchPier.North;
                        }
                }
                Put(garageU1 - 1, v1 - 1, Props.ToolShelf, ArchPier.North);
                Put(garageU1 - 2, v1 - 1, Props.Workbench, ArchPier.North);
                Put(garageU1 - 1, v1 - 3, Props.Toolbox, ArchPier.West);
                Put(garageU0 + 1, v1 - 1, Props.Laundry, ArchPier.North, 0);
                Put(garageU0 + 2, v1 - 1, Props.Laundry, ArchPier.North, 1);
                Put(garageU1 - 1, v0 + 6, Props.PantryShelf, ArchPier.West);
                Put(garageU1 - 1, v0 + 4, Props.Drum, ArchPier.West);
                doorU = u0 + 3;
                backDoorU = u0 + 2;
                Hang(hu1, v0 + 2, Decor.FamilyPhoto, ArchPier.West);
                Hang(u0 + 4, mid, Decor.HouseClock, ArchPier.North);
                break;
            }
            default:
            {
                // Living room and a second bedroom (or a dining room) at the front; kitchen, bathroom, laundry and
                // the main bedroom behind
                int split = u0 + 8;
                PartitionZ(mid, u0 + 1, u1 - 1, paper);
                PartitionX(split, v0 + 1, mid - 1, paper2);
                bool dining = rng.Chance(0.4);
                Room(u0 + 1, v0 + 1, split - 1, mid - 1, FloorKind.HouseCarpet);
                Room(split + 1, v0 + 1, u1 - 1, mid - 1, dining ? FloorKind.HouseWood : FloorKind.HouseCarpet);
                Doorway(split, v0 + 3);
                int k1 = u0 + 6, l1 = k1 + 3;
                PartitionX(k1, mid + 1, v1 - 1, paper);
                PartitionX(l1, mid + 1, v1 - 1, paper);
                Room(u0 + 1, mid + 1, k1 - 1, v1 - 1, FloorKind.HouseLino);
                Room(k1 + 1, mid + 1, l1 - 1, v1 - 1, FloorKind.HouseTile);
                Room(l1 + 1, mid + 1, u1 - 1, v1 - 1, FloorKind.HouseCarpet);
                // (The bathroom's door is at its near side: its far side is in line with the wall between the front rooms)
                Doorway(u0 + 3, mid); Doorway(k1 + 1, mid); Doorway(l1 + 2, mid);
                // Living room
                Put(u0 + 1, v0 + 2, Props.Tv, ArchPier.East);
                Put(u0 + 3, v0 + 2, Props.CoffeeTable, ArchPier.North);
                Put(u0 + 5, v0 + 2, Props.Sofa, ArchPier.West);
                Put(u0 + 5, v0 + 4, Props.WingChair, ArchPier.West);
                Put(u0 + 1, v0 + 4, Props.FloorLamp, ArchPier.North);
                Put(split - 1, v0 + 1, Props.OfficeBookshelf, ArchPier.West);
                for (int u = u0 + 2; u <= u0 + 4; u++) for (int v = v0 + 2; v <= v0 + 3; v++) At(u, v).Floor = FloorKind.HouseRug;
                if (dining)
                {
                    // A dining table laid for nobody
                    Put(split + 3, v0 + 2, Props.DiningTable, ArchPier.North);
                    Put(split + 2, v0 + 2, Props.HotelChair, ArchPier.East);
                    Put(split + 4, v0 + 2, Props.HotelChair, ArchPier.West);
                    Put(split + 3, v0 + 1, Props.HotelChair, ArchPier.South);
                    Put(split + 3, v0 + 3, Props.HotelChair, ArchPier.North);
                    Put(u1 - 1, v0 + 4, Props.CurioCabinet, ArchPier.West);
                }
                else
                {
                    // A child's bedroom: a small bed, a toy box, a dresser
                    Put(u1 - 2, v0 + 1, Props.Bed, ArchPier.South, 0);
                    Put(u1 - 2, v0 + 2, Props.Bed, ArchPier.South, 1);
                    Put(u1 - 1, v0 + 1, Props.Nightstand, ArchPier.South);
                    Put(split + 1, v0 + 4, Props.ToyBox, ArchPier.East);
                    Put(u1 - 1, v0 + 4, Props.Dresser, ArchPier.West);
                    for (int u = split + 2; u <= split + 4; u++) At(u, v0 + 3).Floor = FloorKind.HouseRug;
                }
                // Kitchen
                Put(u0 + 1, v1 - 1, Props.KitchenCabinet, ArchPier.North);
                Put(u0 + 3, v1 - 1, Props.KitchenCounter, ArchPier.North, 1);
                Put(u0 + 4, v1 - 1, Props.Stove, ArchPier.North);
                Put(u0 + 5, mid + 1, Props.Fridge, ArchPier.West);
                Put(u0 + 1, mid + 2, Props.KitchenCabinet, ArchPier.East);
                Put(u0 + 3, mid + 2, Props.RoundTable, ArchPier.North);
                Put(u0 + 4, mid + 2, Props.HotelChair, ArchPier.West);
                // Bathroom, and the laundry in it
                Put(k1 + 1, v1 - 1, Props.Bathtub, ArchPier.East, 0);
                Put(k1 + 2, v1 - 1, Props.Bathtub, ArchPier.East, 1);
                Put(k1 + 1, mid + 1, Props.Toilet, ArchPier.East);
                Put(k1 + 2, mid + 3, Props.Laundry, ArchPier.West, (byte)rng.Range(0, 1));
                Put(k1 + 1, mid + 3, Props.MedCabinet, ArchPier.East);
                // Main bedroom: the bed's head against the back wall
                Put(l1 + 3, v1 - 1, Props.Bed, ArchPier.North, 0);
                Put(l1 + 3, v1 - 2, Props.Bed, ArchPier.North, 1);
                Put(l1 + 2, v1 - 1, Props.Nightstand, ArchPier.North);
                Put(l1 + 4, v1 - 1, Props.Nightstand, ArchPier.North);
                Put(u1 - 1, mid + 1, Props.Dresser, ArchPier.West);
                Put(l1 + 1, mid + 1, Props.Wardrobe, ArchPier.East);
                for (int u = l1 + 2; u <= l1 + 4; u++) At(u, v1 - 3).Floor = FloorKind.HouseRug;
                doorU = u0 + 3;
                backDoorU = u0 + 2;
                Hang(split, v0 + 2, Decor.FamilyPhoto, ArchPier.West);
                Hang(u0 + 5, mid, Decor.HousePainting, ArchPier.North);
                Hang(l1, v1 - 2, Decor.HouseMirror, ArchPier.East);
                Hang(k1, mid + 2, Decor.HouseClock, ArchPier.West);
                break;
            }
        }

        // The front door; most houses have a back door from the kitchen too
        ref Tile front = ref At(doorU, v0);
        front.Kind = locked ? TileKind.Door : TileKind.Doorway;
        front.Variant = 0;
        if (!locked && rng.Chance(0.75)) Doorway(backDoorU, v1);
        else backDoorU = -1;

        // A porch across the front, its railing open at the steps
        if (porch && v0 >= 3)
        {
            bool Rail(int u, int v) => u >= u0 && u <= u1 && v >= v0 - 2 && v < v0
                && (v == v0 - 2 && Math.Abs(u - doorU) > 1 || (u == u0 || u == u1) && v == v0 - 1);
            for (int u = u0; u <= u1; u++)
                for (int v = v0 - 2; v < v0; v++)
                {
                    ref Tile t = ref At(u, v);
                    t.Floor = FloorKind.Porch;
                    t.Roof = RoofBits.Make(v - (v0 - 2), ArchPier.North, lowered: true); // a lean-to against the house
                    if (!Rail(u, v)) continue;
                    t.Kind = TileKind.Bars;
                    t.Pattern = WallPattern.Fence;
                    // Each length of railing joins the next, and the posts by the wall join the house
                    t.Stack = (byte)((Rail(u, v - 1) ? 1 : 0) | (Rail(u + 1, v) ? 2 : 0) | (Rail(u, v + 1) || v == v0 - 1 ? 4 : 0) | (Rail(u - 1, v) ? 8 : 0));
                }
            Put(u0 + 1, v0 - 1, Props.PatioChair, ArchPier.North);
            Put(u1 - 1, v0 - 1, Props.PatioChair, ArchPier.North);
            if (v5 && v0 >= 4)
            {
                // Layout version 5: a deck of boards a little off the ground, posts holding up the roof (at the corners,
                // either side of the steps and every few blocks between), and steps up to it
                for (int u = u0; u <= u1; u++)
                    for (int v = v0 - 2; v < v0; v++)
                    {
                        ref Tile t = ref At(u, v);
                        bool post = t.Kind == TileKind.Bars && v == v0 - 2 && (u == u0 || u == u1 || Math.Abs(u - doorU) == 2 || (u - u0) % 4 == 0);
                        t.Height = (byte)(StoreyPorch | (post ? PorchPost : t.Kind == TileKind.Floor ? PorchDeck : 0));
                    }
                for (int u = doorU - 1; u <= doorU + 1; u++) At(u, v0 - 3).Height = StoreyPorch | PorchStep;
            }
        }
        // Layout version 5: a lamp on the wall by the front door, lit if the house still has power, and no window where a
        // wall inside meets the outside one
        if (v5)
        {
            ref Tile lamp = ref At(doorU + 1, v0 - 1);
            lamp.Height |= (byte)(StoreyPorch | (litWindows ? PorchLamp | PorchLampLit : PorchLamp));
            lamp.Pier = ArchPier.North;
            for (int v = v0 + 1; v < v1; v++)
                foreach (var (u, iu) in new[] { (u0, u0 + 1), (u1, u1 - 1) })
                    if (At(u, v).Variant is 1 or 2 && At(iu, v).Kind == TileKind.Wall) At(u, v).Variant = 0;
            for (int u = u0 + 1; u < u1; u++)
                foreach (var (v, iv) in new[] { (v0, v0 + 1), (v1, v1 - 1) })
                    if (At(u, v).Kind == TileKind.Wall && At(u, v).Variant is 1 or 2 && At(u, iv).Kind == TileKind.Wall) At(u, v).Variant = 0;
        }

        // A gable roof rises from the front and back eaves to a ridge along the middle
        for (int v = v0; v <= v1; v++)
        {
            bool frontHalf = v - v0 <= v1 - v;
            for (int u = u0; u <= u1; u++) At(u, v).Roof = RoofBits.Make(Math.Min(v - v0, v1 - v), frontHalf ? ArchPier.North : ArchPier.South);
        }

        if (locked)
            for (int v = v0 + 1; v < v1; v++)
                for (int u = u0 + 1; u < u1; u++)
                    if (At(u, v).Kind == TileKind.Floor) At(u, v).Sealed = true;
        return new House(u0, u1, v0, v1, doorU, backDoorU, garage, garageU0 + 1, garageU0 + 3, locked);
    }

    /// <summary>The front yard: a path to the door, beds of flowers and shrubs, the mailbox, a drive and a hoop, a picket fence.</summary>
    private static void PlanFrontYard(Tile[] tiles, int w, House house, ref Rng rng)
    {
        ref Tile At(int u, int v) => ref tiles[v * w + u];
        int front = house.V0 - 1;
        while (front >= 0 && At(house.DoorU, front).Floor == FloorKind.Porch) front--;
        for (int v = 0; v <= front; v++) At(house.DoorU, v).Floor = FloorKind.Sidewalk;
        At(house.DoorU + 2, 0).Variant = Props.Mailbox;
        At(house.DoorU + 2, 0).Pier = ArchPier.North;

        // Flower beds along the front of the house, shrubs at the corners
        for (int u = house.U0; u <= house.U1; u++)
        {
            ref Tile bed = ref At(u, front);
            if (bed.Floor != FloorKind.Lawn || Math.Abs(u - house.DoorU) <= 1 || house.Garage && u >= house.GarageU0 - 1 && u <= house.GarageU1 + 1) continue;
            bed.Floor = FloorKind.Flowerbed;
            if (rng.Chance(0.7)) { bed.Variant = Props.Flowers; bed.Stack = (byte)rng.Range(0, 7); }
        }
        foreach (int u in new[] { house.U0, house.U1 })
            if (At(u, front - 1).Floor == FloorKind.Lawn && rng.Chance(0.7)) At(u, front - 1).Variant = Props.Shrub;

        if (house.Garage)
        {
            // The drive, and a basketball hoop over it; sometimes the car is left out on it
            for (int v = 0; v < house.V0; v++)
                for (int u = house.GarageU0; u <= house.GarageU1; u++) { At(u, v).Floor = FloorKind.Driveway; At(u, v).Variant = 0; }
            if (rng.Chance(0.45)) { At(house.GarageU1 + 1, house.V0 - 1).Variant = Props.BasketballHoop; At(house.GarageU1 + 1, house.V0 - 1).Pier = ArchPier.North; }
            At(house.GarageU1 + 1, 0).Variant = Props.WheelieBin;
            At(house.GarageU1 + 1, 0).Pier = ArchPier.North;
        }
        else
        {
            At(house.DoorU - 2, 0).Variant = Props.WheelieBin;
            At(house.DoorU - 2, 0).Pier = ArchPier.North;
        }

        // A white picket fence along the front of some lots
        if (rng.Chance(0.3))
        {
            for (int u = 0; u < w; u++)
            {
                ref Tile t = ref At(u, 1);
                if (t.Floor is FloorKind.Sidewalk or FloorKind.Driveway || t.Variant != 0) continue;
                t.Kind = TileKind.Bars;
                t.Pattern = WallPattern.Fence;
                bool left = u > 0 && At(u - 1, 1).Floor is not (FloorKind.Sidewalk or FloorKind.Driveway);
                bool right = u < w - 1 && At(u + 1, 1).Floor is not (FloorKind.Sidewalk or FloorKind.Driveway);
                t.Stack = (byte)((left ? 8 : 0) | (right ? 2 : 0));
            }
        }
    }

    /// <summary>The backyard behind the house: a patio and a grill, then a few of a swing set, a pool, a shed, a vegetable patch, a dog house.</summary>
    private static void PlanBackyard(Tile[] tiles, int w, int d, House house, ref Rng rng)
    {
        ref Tile At(int u, int v) => ref tiles[v * w + u];
        int y0 = house.V1 + 1, y1 = d - 2; // the yard's rows
        if (y1 - y0 < 4) return;
        int door = house.BackDoorU >= 0 ? house.BackDoorU : house.U0 + 2;

        // A concrete patio outside the back door, with a grill and chairs
        for (int u = door - 1; u <= door + 3; u++)
            for (int v = y0; v <= y0 + 2; v++) At(u, v).Floor = FloorKind.Driveway;
        At(door + 3, y0).Variant = Props.Grill; At(door + 3, y0).Pier = ArchPier.South;
        At(door + 1, y0 + 2).Variant = Props.RoundTable;
        At(door + 2, y0 + 2).Variant = Props.PatioChair; At(door + 2, y0 + 2).Pier = ArchPier.West;
        At(door, y0 + 2).Variant = Props.PatioChair; At(door, y0 + 2).Pier = ArchPier.East;

        // The far half of the yard holds one big thing
        int pick = rng.Range(0, 4);
        int cu = w / 2 + 2, cv = (y0 + y1) / 2 + 2;
        switch (pick)
        {
            case 0:
                // A pool, drained long ago, with stone coping round it
                for (int v = cv - 3; v <= cv + 2; v++)
                    for (int u = cu - 3; u <= cu + 4; u++)
                    {
                        bool edge = v == cv - 3 || v == cv + 2 || u == cu - 3 || u == cu + 4;
                        At(u, v).Floor = edge ? FloorKind.PoolEdge : FloorKind.PoolDeep;
                        At(u, v).Variant = 0;
                    }
                break;
            case 1:
                // A swing set and a sandpit's worth of bare ground
                At(cu, cv).Variant = Props.SwingSet; At(cu, cv).Pier = ArchPier.North;
                break;
            case 2:
                // A garden shed of grey boards (3 by 3 inside), its door toward the house
                for (int v = cv - 2; v <= cv + 2; v++)
                    for (int u = cu; u <= cu + 4; u++)
                    {
                        ref Tile t = ref At(u, v);
                        byte roof = RoofBits.Make(Math.Min(u - cu, cu + 4 - u), u - cu <= 2 ? ArchPier.West : ArchPier.East);
                        t.Roof = roof;
                        t.Floor = FloorKind.Garage;
                        if (u == cu || u == cu + 4 || v == cv - 2 || v == cv + 2)
                        {
                            SetWall(ref t, WallPattern.BarnGrey, BaseStyle.Plain);
                            t.Roof = roof;
                            if (v == cv - 2 && u == cu + 2) t.Kind = TileKind.Doorway;
                        }
                    }
                At(cu + 1, cv + 1).Variant = Props.ToolShelf; At(cu + 1, cv + 1).Pier = ArchPier.North;
                At(cu + 3, cv + 1).Variant = Props.SeedSacks;
                At(cu + 3, cv - 1).Variant = Props.Toolbox; At(cu + 3, cv - 1).Pier = ArchPier.West;
                break;
            default:
                // A vegetable patch in rows
                for (int v = cv - 2; v <= cv + 2; v += 2)
                    for (int u = cu - 2; u <= cu + 4; u++)
                    {
                        At(u, v).Floor = FloorKind.Flowerbed;
                        At(u, v).Variant = Props.Vegetable;
                        At(u, v).Stack = (byte)((v - cv + 2) / 2 + (u & 1) * 3);
                    }
                break;
        }
        if (rng.Chance(0.4)) { At(2, y1 - 1).Variant = Props.Doghouse; At(2, y1 - 1).Pier = ArchPier.North; }
        // Fruit bushes along the back fence, gone wild
        if (rng.Chance(0.55))
        {
            byte kind = (byte)rng.Range(0, 4);
            for (int u = 4; u <= 8; u += 2)
                if (At(u, y1).Kind == TileKind.Floor && At(u, y1).Variant == 0) { At(u, y1).Variant = Props.BerryBush; At(u, y1).Stack = kind; }
        }
        if (pick != 1 && rng.Chance(0.3)) { At(w - 4, y0 + 1).Variant = Props.SwingSet; At(w - 4, y0 + 1).Pier = ArchPier.North; }
    }
}
