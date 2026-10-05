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

    /// <summary>Which lot of the town a block lies in, as a single key (so a house can have one colour of roof).</summary>
    public (int, int) LotKeyAt(int gx, int gz)
    {
        int sx = Hashing.Mod(gx, TownBlockX), sz = Hashing.Mod(gz, TownBlockZ);
        return (Hashing.FloorDiv(gx, TownBlockX) * 3 + Math.Clamp((sx - 8) / LotWidth, 0, 2),
                Hashing.FloorDiv(gz, TownBlockZ) * 2 + (sz >= 8 + LotDepth ? 1 : 0));
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
                    foreach (bool east in new[] { false, true })
                    {
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
            // Zebra crossings where the street meets a junction; a dashed line down the middle; the odd manhole
            if (along is 8 or 9 || along >= block - 2) t.Floor = roadX ? FloorKind.AsphaltCrossing : FloorKind.AsphaltCrossingNS;
            else if (across == 3 && Hashing.Mod(run, 6) < 3) t.Floor = roadX ? FloorKind.AsphaltLine : FloorKind.AsphaltLineNS;
            else if (across == 5 && Hashing.Mod(run, 52) == 26) t.Floor = FloorKind.Manhole;
            return;
        }

        t.Floor = FloorKind.Sidewalk;
        // Stop signs on the corners of every junction, facing the traffic coming into it
        if (sx == 7 && sz == 7) { t.Variant = Props.StopSign; t.Pier = ArchPier.South; return; }
        if (sx == 0 && sz == 0) { t.Variant = Props.StopSign; t.Pier = ArchPier.North; return; }
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
        LotKind kind = r < 0.88 ? LotKind.House : r < 0.94 ? LotKind.Field : LotKind.Empty;

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
                var house = PlanHouse(tiles, w, ref rng, farmhouse: false);
                PlanFrontYard(tiles, w, house, ref rng);
                PlanBackyard(tiles, w, d, house, ref rng);
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
    /// </summary>
    private static House PlanHouse(Tile[] tiles, int w, ref Rng rng, bool farmhouse)
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
                else if ((u + v) % 3 == 0) t.Variant = (byte)(litWindows && rng.Chance(0.5) ? 2 : 1);
            }
        int chimneyV = (v0 + v1) / 2 + rng.Range(-2, 2);
        At(u0, chimneyV).Variant = 3; // a brick chimney up the side wall

        int doorU, backDoorU;
        int mid = v0 + 5; // the wall between the front rooms and the back
        int garageU0 = 0, garageU1 = 0;
        switch (kind)
        {
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
