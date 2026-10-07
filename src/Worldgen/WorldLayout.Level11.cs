using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 11, "The Endless City": a Western metropolis that goes on forever, block after bland block, its avenues
/// running north to south and its streets east to west. Downtown is all towers, some of glass and some of stone,
/// stepped back as they rise; elsewhere the buildings are apartment blocks over stores, or brick rowhouses no
/// higher than three storeys. Nothing moves. The cars are parked where they were left, the traffic lights are dead
/// or stuck, most of the street lamps are out, and the only sound is a hum like distant traffic that isn't there.
///
/// A third of the buildings can never be entered: their windows are black mirrors and they have no doors. The
/// rest open onto lobbies, diners, grocery stores, pharmacies, hardware stores, laundromats, a church or a museum,
/// with the lights still on and the shelves still stocked; Almond Water is everywhere, in vending machines and on
/// street vendors' carts. A subway runs under every avenue, with a station at every third street. It is the safest
/// place in the Backrooms, and the best connected: its exits are as many as they are hard to notice. An office
/// tower's elevators go to Level 4 and a hotel's to Level 5; a basement door to Level 0, a garage ramp to Level 1,
/// an open manhole to Level 2, a substation to Level 3; a dark doorway off an alley to Level 6, the deep middle of a
/// park fountain to Level 7, a broken street to Level 8, a rowhouse's front door to Level 9, a patch of wheat in a
/// park to Level 10, and a diner's kitchen door to the Snackrooms.
///
/// The city is not a ring. It lies far out past the fields of Level 10, and no one walks there: you noclip in,
/// through a barn wall in Level 10 that isn't quite there. Its streets are <see cref="WorldGeometry.CityDrop"/>
/// blocks below the other levels, so its towers have room to rise.
///
/// The street grid is regular: an avenue every <see cref="AvePitch"/> blocks and a street every
/// <see cref="StreetPitch"/>, so every block is the same size, cut in two by an alley. Each block is planned as a
/// whole (<see cref="BlockPlan"/>) and the plan reused by every cell it covers.
/// </summary>
public sealed partial class WorldLayout
{
    private const ulong SaltCityShape = 0xB101, SaltCityDistrict = 0xB102, SaltCityBlock = 0xB103, SaltCityStreet = 0xB105,
        SaltCitySide = 0xB106, SaltCityCar = 0xB107, SaltCityCollapse = 0xB108, SaltCityManhole = 0xB109, SaltCityPark = 0xB10A;

    /// <summary>Distance between avenues (running north-south) and their width: a sidewalk, eleven of road, a sidewalk.</summary>
    public const int AvePitch = 100, AveWidth = 17;
    /// <summary>Distance between streets (running west-east) and their width: a sidewalk, nine of road, a sidewalk.</summary>
    public const int StreetPitch = 76, StreetWidth = 15;
    private const int BlockW = AvePitch - AveWidth, BlockD = StreetPitch - StreetWidth;
    /// <summary>The alley through the middle of a block: three rows from here.</summary>
    private const int AlleyZ = 29;
    /// <summary>A subway station at every third street, reaching this far either side of it.</summary>
    public const int StationEvery = 3, StationReach = 12, StationLength = StreetWidth + 2 * StationReach;

    // ================= Where the city is =================

    /// <summary>The city's centre, in macro cells: far out past the fields, in a direction the rings never reach.</summary>
    private int CityCentreX => spawnMacroX + Math.Max(800, spawnMacroX / 4);
    private int CityCentreZ => spawnMacroZ;

    /// <summary>The city's radius in macro cells: some seventy kilometres in a full-size world, endless to anyone in it.</summary>
    private int CityRadius => Math.Max(240, spawnMacroX * 3 / 20);

    /// <summary>The block the city's street grid counts from (the corner of the block at its centre).</summary>
    public int CityOriginX => CityCentreX * MacroSize;
    public int CityOriginZ => CityCentreZ * MacroSize;

    private bool InCity(double mx, double mz)
    {
        double dx = mx - CityCentreX, dz = mz - CityCentreZ;
        double r = Math.Sqrt(dx * dx + dz * dz);
        if (r > CityRadius * 1.2) return false;
        return r * (1 + 0.08 * Fbm(mx / 60.0, mz / 60.0, SaltCityShape)) < CityRadius;
    }

    /// <summary>A place near the middle of the city to look for somewhere to arrive, picked by hash.</summary>
    private (int Mx, int Mz) CityArrivalCell(ulong h)
    {
        double angle = Hashing.Unit(h) * Math.PI * 2, radius = Math.Sqrt(Hashing.Unit(Hashing.Mix(h))) * CityRadius * 0.35;
        return (CityCentreX + (int)Math.Round(Math.Cos(angle) * radius), CityCentreZ + (int)Math.Round(Math.Sin(angle) * radius));
    }

    /// <summary>Arriving in the city: on a sidewalk or a plaza, out in the open.</summary>
    private static bool IsCityArrivalSpot(Tile t) =>
        IsArrivalSpot(t) && t.Depth == 0 && t.Roof == 0 && t.Floor is FloorKind.Sidewalk or FloorKind.CityPlaza;

    /// <summary>Where an elevator in the city goes: an office tower's to Level 4, a hotel's to Level 5; an apartment block's is out of order.</summary>
    public int CityElevatorTarget(int x, int z)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        if (LevelAt(mx, mz) != 11) return -1;
        Tile t = BuildMacro(mx, mz)[TileIndex(x - mx * MacroSize, z - mz * MacroSize)];
        return (CityKind)t.Zone switch { CityKind.Office => 4, CityKind.Hotel => 5, _ => -1 };
    }

    // ================= Districts and blocks =================

    private enum District : byte { Lowrise, Midtown, Downtown }

    private enum CityBlock : byte { Lots, Park, Plaza, ParkingLot, Museum }

    /// <summary>How built up the city is around a block: towers downtown (always near the centre, and elsewhere in patches), brick and stores further out.</summary>
    private District DistrictOf(int bi, int bj)
    {
        double d = 0.5 + 0.55 * Fbm(bi / 5.0, bj / 6.5, SaltCityDistrict);
        double far = bi * bi + bj * bj * 1.7;
        d += 0.35 * Math.Exp(-far / 220.0);
        return d > 0.66 ? District.Downtown : d > 0.42 ? District.Midtown : District.Lowrise;
    }

    private CityBlock BlockKindOf(int bi, int bj, District district)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, bi, bj, SaltCityBlock));
        return district switch
        {
            District.Downtown => r < 0.05 ? CityBlock.Park : r < 0.27 ? CityBlock.Plaza : r < 0.29 ? CityBlock.Museum : r < 0.31 ? CityBlock.ParkingLot : CityBlock.Lots,
            District.Midtown => r < 0.07 ? CityBlock.Park : r < 0.11 ? CityBlock.ParkingLot : r < 0.12 ? CityBlock.Museum : CityBlock.Lots,
            _ => r < 0.11 ? CityBlock.Park : r < 0.17 ? CityBlock.ParkingLot : CityBlock.Lots,
        };
    }

    // ================= Cells =================

    private void BuildLevel11(Builder b, int mx, int mz)
    {
        // The city's edge: a wall of black glass, solid to the sky, all the way round
        bool rim = false;
        for (int dz = -1; dz <= 1 && !rim; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (LevelAt(mx + dx, mz + dz) != 11) { rim = true; break; }

        for (int lz = 0; lz < MacroSize; lz++)
        {
            for (int lx = 0; lx < MacroSize; lx++)
            {
                ref Tile t = ref b.At(lx, lz);
                if (rim)
                {
                    t = new Tile { Kind = TileKind.Wall, Pattern = WallPattern.CityMirror, Zone = (byte)CityKind.Rim, Floor = FloorKind.Sidewalk };
                    continue;
                }
                t = CityTile(mx * MacroSize + lx, mz * MacroSize + lz);
            }
        }
    }

    private Tile CityTile(int gx, int gz)
    {
        int ux = gx - CityOriginX, uz = gz - CityOriginZ;
        int ax = Hashing.Mod(ux, AvePitch), sz = Hashing.Mod(uz, StreetPitch);
        int bi = Hashing.FloorDiv(ux, AvePitch), bj = Hashing.FloorDiv(uz, StreetPitch);
        if (ax < AveWidth || sz < StreetWidth) return CityStreetTile(gx, gz, ux, uz, ax, sz, bi, bj);
        Tile t = BlockPlan(bi, bj)[(sz - StreetWidth) * BlockW + ax - AveWidth];
        // A tree's crown spreads over the tiles round it; in the parks and plazas that is worked out in the plan
        return t;
    }

    // ---- Block plans, cached: a cell covers parts of up to four blocks, and neighbouring cells share them ----

    private PlanCache<Tile[]> blockPlans;

    private Tile[] BlockPlan(int bi, int bj) => (blockPlans ??= new PlanCache<Tile[]>(64, PlanBlock)).Get(bi, bj);

    private Tile[] PlanBlock(int bi, int bj)
    {
        var tiles = new Tile[BlockW * BlockD];
        for (int i = 0; i < tiles.Length; i++) tiles[i] = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Sidewalk };
        var rng = new Rng(Hashing.Hash(seed, bi, bj, SaltCityBlock + 1));
        District district = DistrictOf(bi, bj);
        switch (BlockKindOf(bi, bj, district))
        {
            case CityBlock.Park: PlanPark(tiles, ref rng); break;
            case CityBlock.Plaza: PlanPlaza(tiles, district, ref rng); break;
            case CityBlock.ParkingLot: PlanParkingLot(tiles, bi, bj, ref rng); break;
            case CityBlock.Museum:
                Fill(tiles, 0, BlockW - 1, 0, BlockD - 1, FloorKind.CityPlaza);
                PlanBuilding(tiles, 6, BlockW - 7, 8, BlockD - 7, true, true, true, true,
                             new Spec(CityKind.Museum, 24, 0, WallPattern.CityStone), ref rng);
                PlazaDressing(tiles, ref rng);
                break;
            default: PlanLots(tiles, district, bi, bj, ref rng); break;
        }
        return tiles;
    }

    private static ref Tile At(Tile[] tiles, int x, int z) => ref tiles[z * BlockW + x];

    private static void Fill(Tile[] tiles, int x0, int x1, int z0, int z1, FloorKind floor)
    {
        for (int z = z0; z <= z1; z++)
            for (int x = x0; x <= x1; x++) tiles[z * BlockW + x] = new Tile { Kind = TileKind.Floor, Floor = floor };
    }

    // ================= Lots and buildings =================

    private readonly struct Spec
    {
        public readonly CityKind Kind;
        public readonly int Height, Setback;
        public readonly WallPattern Style;

        public Spec(CityKind kind, int height, int setback, WallPattern style)
        {
            Kind = kind; Height = height; Setback = setback; Style = style;
        }
    }

    /// <summary>
    /// An ordinary block: an alley down the middle, and on either side of it a row of lots fronting the street,
    /// each with its own building. The lots at the ends front the avenues too.
    /// </summary>
    private void PlanLots(Tile[] tiles, District district, int bi, int bj, ref Rng rng)
    {
        for (int half = 0; half < 2; half++)
        {
            int z0 = half == 0 ? 0 : AlleyZ + 3, z1 = half == 0 ? AlleyZ - 1 : BlockD - 1;
            int min = district == District.Lowrise ? 7 : district == District.Midtown ? 12 : 18;
            int x = 0;
            while (x < BlockW)
            {
                int w = district switch
                {
                    District.Downtown => rng.Range(20, 40),
                    District.Midtown => rng.Range(12, 26),
                    _ => rng.Chance(0.45) ? rng.Range(7, 9) : rng.Range(10, 18),
                };
                if (BlockW - (x + w) < min) w = BlockW - x;
                Spec spec = ChooseSpec(district, w, ref rng);
                PlanBuilding(tiles, x, x + w - 1, z0, z1, half == 0, x == 0, x + w == BlockW, true, spec, ref rng);
                // A few lots are something else: planned again over the top, on their own, so the lots after them
                // come out as they always have
                if (OddLot(district, spec, w, bi, bj, x, half) is { } odd)
                {
                    var own = new Rng(Hashing.Hash(seed, bi * 128 + x, bj * 2 + half, SaltCityBlock + 37));
                    PlanBuilding(tiles, x, x + w - 1, z0, z1, half == 0, x == 0, x + w == BlockW, true, odd, ref own);
                }
                x += w;
            }
        }
        PlanAlley(tiles, ref rng);
    }

    private static Spec ChooseSpec(District district, int w, ref Rng rng)
    {
        double r = rng.NextDouble();
        CityKind kind;
        int height;
        switch (district)
        {
            case District.Downtown:
                kind = r < 0.30 ? CityKind.Sealed : r < 0.75 ? CityKind.Office : r < 0.87 ? CityKind.Hotel : CityKind.Apartment;
                height = 4 * rng.Range(10, 20);
                break;
            case District.Midtown:
                kind = r < 0.28 ? CityKind.Sealed : r < 0.48 ? CityKind.Office : r < 0.54 ? CityKind.Hotel
                    : r < 0.59 && w >= 16 ? CityKind.Garage : r < 0.61 && w >= 14 ? CityKind.Church : r < 0.63 ? CityKind.Substation
                    : r < 0.80 ? CityKind.Apartment : Shop(ref rng, w);
                height = 4 * rng.Range(4, 10);
                break;
            default:
                if (w <= 9) kind = r < 0.68 ? CityKind.Rowhouse : r < 0.83 ? CityKind.Sealed : Shop(ref rng, w);
                else kind = r < 0.18 ? CityKind.Sealed : r < 0.23 && w >= 14 ? CityKind.Church : r < 0.27 ? CityKind.Substation
                    : r < 0.31 && w >= 16 ? CityKind.Garage : r < 0.45 ? CityKind.Apartment : Shop(ref rng, w);
                height = kind == CityKind.Apartment ? 4 * rng.Range(3, 4) : 4 * rng.Range(1, 3);
                break;
        }
        // Each kind of building has its own proportions and its own materials
        switch (kind)
        {
            case CityKind.Rowhouse: height = 12; break;
            case CityKind.Church: height = 16; break;
            case CityKind.Substation: height = 8; break;
            case CityKind.Garage: height = 4 * rng.Range(3, 5); break;
        }
        height = Math.Min(height, 80);
        WallPattern style = kind switch
        {
            CityKind.Sealed => WallPattern.CityMirror,
            CityKind.Office => r < 0.5 ? WallPattern.CityGlass : r < 0.75 ? WallPattern.CityStone : WallPattern.CityConcrete,
            CityKind.Hotel => rng.Chance(0.5) ? WallPattern.CityStone : rng.Chance(0.6) ? WallPattern.CityBrick : WallPattern.CityBrickDark,
            CityKind.Church or CityKind.Museum => WallPattern.CityStone,
            CityKind.Garage => WallPattern.CityConcrete,
            CityKind.Substation => WallPattern.CityBrick,
            CityKind.Rowhouse => rng.Chance(0.4) ? WallPattern.CityBrick : rng.Chance(0.5) ? WallPattern.CityBrickDark : WallPattern.CityStone,
            _ => rng.Chance(0.4) ? WallPattern.CityBrick : rng.Chance(0.4) ? WallPattern.CityBrickDark : rng.Chance(0.5) ? WallPattern.CityStone : WallPattern.CityConcrete,
        };
        // Towers step back as they rise
        int setback = height >= 44 && w >= 14 && rng.Chance(0.7) ? 4 * (int)Math.Round(height * 0.55 / 4) : 0;
        return new Spec(kind, height, setback, style);
    }

    /// <summary>
    /// The odd lot: now and then an apartment block in midtown is a cinema showing a stop-motion picture, and a
    /// substation is public baths with a door marked POOL. Null for an ordinary lot.
    /// </summary>
    private Spec? OddLot(District district, Spec spec, int w, int bi, int bj, int x, int half)
    {
        double r = Hashing.Unit(Hashing.Hash(seed, bi * 128 + x, bj * 2 + half, SaltCityBlock + 38));
        if (district == District.Midtown && spec.Kind == CityKind.Apartment && w >= 12 && r < 0.07)
            return new Spec(CityKind.Cinema, Math.Min(spec.Height, 12), 0, WallPattern.CityBrick);
        if (spec.Kind == CityKind.Substation && r < 0.4)
            return new Spec(CityKind.Baths, 8, 0, WallPattern.CityStone);
        return null;
    }

    private static CityKind Shop(ref Rng rng, int w)
    {
        double r = rng.NextDouble();
        return r < 0.22 ? CityKind.Diner : r < 0.42 && w >= 12 ? CityKind.Grocery : r < 0.56 ? CityKind.Pharmacy
            : r < 0.72 ? CityKind.Hardware : r < 0.86 ? CityKind.Clothing : CityKind.Laundromat;
    }

    public static bool CityEnterable(CityKind kind) => kind is not (CityKind.Sealed or CityKind.Rowhouse or CityKind.Substation or CityKind.Rim or CityKind.None or CityKind.Baths);

    /// <summary>
    /// A lot's frame, turned so that its street front is always at v = 0 ("north") whichever side it really faces,
    /// with u running across it. Props and doors are laid out in this frame.
    /// </summary>
    private readonly struct Frame
    {
        private readonly Tile[] tiles;
        public readonly int X0, X1, Z0, Z1, W, D;
        private readonly bool north;

        public Frame(Tile[] tiles, int x0, int x1, int z0, int z1, bool frontNorth)
        {
            this.tiles = tiles; X0 = x0; X1 = x1; Z0 = z0; Z1 = z1; north = frontNorth;
            W = x1 - x0 + 1; D = z1 - z0 + 1;
        }

        public ref Tile At(int u, int v) => ref tiles[(north ? Z0 + v : Z1 - v) * BlockW + (north ? X0 + u : X1 - u)];

        /// <summary>A direction in the frame, as a direction in the world.</summary>
        public ArchPier P(ArchPier p) => north ? p : p switch
        {
            ArchPier.North => ArchPier.South,
            ArchPier.South => ArchPier.North,
            ArchPier.East => ArchPier.West,
            _ => ArchPier.East,
        };

        public bool Inside(int u, int v) => u >= 1 && v >= 1 && u <= W - 2 && v <= D - 2;

        /// <summary>Puts a prop on an inside floor tile that has nothing on it yet.</summary>
        public void Prop(int u, int v, byte prop, ArchPier facing, int stack = 0)
        {
            if (!Inside(u, v)) return;
            ref Tile t = ref At(u, v);
            if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Stair != 0 || t.Under != 0) return;
            t.Variant = prop;
            t.Pier = P(facing);
            t.Stack = (byte)stack;
        }

        /// <summary>An inside wall (a partition of the ground floor), facing the given way.</summary>
        public void Partition(int u, int v, WallPattern pattern, ArchPier facing)
        {
            if (!Inside(u, v)) return;
            ref Tile t = ref At(u, v);
            t.Kind = TileKind.Wall;
            t.Pattern = pattern;
            t.Pier = P(facing);
            t.Variant = 0;
        }
    }

    /// <summary>
    /// A building filling the lot: its walls on the edge (each facing out, blank where it meets the next building),
    /// set back for the upper floors if it is a tower, and its ground floor fitted out for what it is.
    /// </summary>
    private void PlanBuilding(Tile[] tiles, int x0, int x1, int z0, int z1, bool frontNorth, bool westOpen, bool eastOpen, bool backOpen,
                              Spec spec, ref Rng rng)
    {
        // A rowhouse stands back behind a little railed yard; a substation's switchyard is in front of it
        int yard = spec.Kind == CityKind.Rowhouse ? 2 : spec.Kind == CityKind.Substation ? Math.Min(6, (z1 - z0) / 3) : 0;
        var lot = new Frame(tiles, x0, x1, z0, z1, frontNorth);
        if (yard > 0) Yard(lot, yard, spec, ref rng);
        if (frontNorth) z0 += yard; else z1 -= yard;
        var f = new Frame(tiles, x0, x1, z0, z1, frontNorth);

        FloorKind floor = spec.Kind switch
        {
            CityKind.Office => FloorKind.CityMarble,
            CityKind.Hotel => FloorKind.HotelLobby,
            CityKind.Apartment => FloorKind.HouseLino,
            CityKind.Diner => FloorKind.SnackChecker,
            CityKind.Grocery or CityKind.Pharmacy => FloorKind.SnackTerrazzo,
            CityKind.Clothing => FloorKind.OfficeCarpet,
            CityKind.Laundromat => FloorKind.HouseLino,
            CityKind.Church => FloorKind.L3Stone,
            CityKind.Museum => FloorKind.HotelMarble,
            CityKind.Rowhouse => FloorKind.HouseWood,
            _ => FloorKind.CityGarage,
        };
        bool northOpen = frontNorth || backOpen, southOpen = !frontNorth || backOpen;
        for (int z = z0; z <= z1; z++)
        {
            for (int x = x0; x <= x1; x++)
            {
                ref Tile t = ref At(tiles, x, z);
                int dW = x - x0, dE = x1 - x, dN = z - z0, dS = z1 - z;
                int d = Math.Min(Math.Min(dW, dE), Math.Min(dN, dS));
                t = new Tile
                {
                    Kind = TileKind.Floor, Floor = floor, Pattern = spec.Style, Zone = (byte)spec.Kind,
                    Depth = (byte)spec.Height, Roof = (byte)spec.Setback, Pipe = (byte)Math.Min(d, 3),
                };
                if (spec.Kind == CityKind.Sealed) t.Sealed = true;
                if (d == 0)
                {
                    t.Kind = TileKind.Wall;
                    t.Pier = dN == 0 ? ArchPier.North : dS == 0 ? ArchPier.South : dW == 0 ? ArchPier.West : ArchPier.East;
                    bool cornerTile = (dW == 0 || dE == 0) && (dN == 0 || dS == 0);
                    if (cornerTile) t.Detail |= CityDetail.Corner;
                    bool party = dW == 0 && !westOpen || dE == 0 && !eastOpen || dN == 0 && !northOpen || dS == 0 && !southOpen;
                    // A wall against the next building is blank; at a corner, the open face shows
                    if (party && !cornerTile) t.Detail |= CityDetail.Party;
                    if (party && cornerTile)
                    {
                        // Face the corner the open way
                        if (dN == 0 && northOpen) t.Pier = ArchPier.North;
                        else if (dS == 0 && southOpen) t.Pier = ArchPier.South;
                        else if (dW == 0 && westOpen) t.Pier = ArchPier.West;
                        else if (dE == 0 && eastOpen) t.Pier = ArchPier.East;
                        else t.Detail |= CityDetail.Party;
                    }
                    if (spec.Kind == CityKind.Garage && !party) t.Detail |= CityDetail.Open;
                }
                else if (spec.Setback > 0 && d == 2)
                {
                    ArchPier face = dN == 2 ? ArchPier.North : dS == 2 ? ArchPier.South : dW == 2 ? ArchPier.West : ArchPier.East;
                    t.Detail |= (byte)(CityDetail.Setback | (byte)face);
                }
            }
        }

        // The roofs: plant and tanks, a mast on the tallest towers
        RoofDressing(f, spec, ref rng);

        switch (spec.Kind)
        {
            case CityKind.Sealed: return; // no doors, and windows like black mirrors
            case CityKind.Rowhouse:
            {
                // A front door that is not locked, and opens somewhere else
                ref Tile door = ref f.At((f.W - 1) / 2, 0);
                door.Kind = TileKind.Door;
                door.Detail = 0;
                return;
            }
            case CityKind.Substation:
            case CityKind.Baths:
            {
                ref Tile door = ref f.At(f.W / 2, 0);
                door.Kind = TileKind.Door;
                door.Detail = 0;
                return;
            }
        }

        // The way in, and plate glass along the front of stores and lobbies
        int doors = spec.Kind is CityKind.Office or CityKind.Hotel or CityKind.Church ? 3 : spec.Kind == CityKind.Garage ? 4
            : spec.Kind == CityKind.Museum ? 5 : 2;
        int first = (f.W - doors) / 2;
        bool glassFront = spec.Kind is not (CityKind.Church or CityKind.Garage or CityKind.Museum or CityKind.Apartment);
        for (int u = 1; u < f.W - 1; u++)
        {
            ref Tile t = ref f.At(u, 0);
            if (u >= first && u < first + doors)
            {
                t.Kind = TileKind.Doorway;
                t.Detail &= unchecked((byte)~CityDetail.Open);
            }
            else if (glassFront) t.Detail |= CityDetail.Storefront;
        }
        // Over the door, the sign
        byte sign = SignFor(spec.Kind, ref rng);
        if (sign != 0)
        {
            ref Tile over = ref f.At(first + doors / 2, 0);
            over.Variant = sign;
            if (f.W >= 16 && spec.Kind is not (CityKind.Office or CityKind.Hotel))
            {
                ref Tile second = ref f.At(Math.Max(1, first - 3), 0);
                if (second.Kind == TileKind.Wall) second.Variant = sign;
            }
        }
        // A big building on a corner has a side door onto the avenue as well
        if (f.D >= 12 && f.W >= 16 && (westOpen || eastOpen) && spec.Kind is CityKind.Office or CityKind.Hotel or CityKind.Museum)
        {
            int v = f.D / 3;
            bool sideLeft = frontNorth ? westOpen : eastOpen;
            int u = sideLeft ? 0 : f.W - 1;
            for (int k = 0; k < 2; k++) { ref Tile s = ref f.At(u, v + k); s.Kind = TileKind.Doorway; }
        }

        switch (spec.Kind)
        {
            case CityKind.Office: OfficeLobby(f, ref rng); break;
            case CityKind.Hotel: HotelLobby(f, ref rng); break;
            case CityKind.Apartment: ApartmentLobby(f, ref rng); break;
            case CityKind.Diner: Diner(f, ref rng); break;
            case CityKind.Grocery: Grocery(f, ref rng); break;
            case CityKind.Pharmacy: Pharmacy(f, ref rng); break;
            case CityKind.Hardware: HardwareStore(f, ref rng); break;
            case CityKind.Clothing: ClothingStore(f, ref rng); break;
            case CityKind.Laundromat: Laundromat(f, ref rng); break;
            case CityKind.Cinema: Cinema(f); break;
            case CityKind.Church: Church(f, ref rng); break;
            case CityKind.Garage: Garage(f, ref rng); break;
            case CityKind.Museum: Museum(f, ref rng); break;
        }
    }

    private static byte SignFor(CityKind kind, ref Rng rng) => kind switch
    {
        // Now and then the signs are in Spanish
        CityKind.Diner => Decor.SignDiner,
        CityKind.Grocery => rng.Chance(0.3) ? Decor.SignBodega : Decor.SignGrocery,
        CityKind.Pharmacy => rng.Chance(0.35) ? Decor.SignFarmacia : Decor.SignPharmacy,
        CityKind.Hardware => Decor.SignHardware,
        CityKind.Laundromat => rng.Chance(0.35) ? Decor.SignLavanderia : Decor.SignLaundry,
        CityKind.Clothing => Decor.SignClothing,
        CityKind.Hotel => Decor.SignHotel,
        CityKind.Office => Decor.SignOffices,
        CityKind.Apartment => Decor.SignApartments,
        CityKind.Garage => Decor.SignParking,
        CityKind.Museum => Decor.SignMuseum,
        _ => 0,
    };

    /// <summary>A rowhouse's little front yard behind black railings, or a substation's switchyard behind a fence.</summary>
    private static void Yard(Frame lot, int depth, Spec spec, ref Rng rng)
    {
        int gate = spec.Kind == CityKind.Substation ? lot.W / 2 : (lot.W - 1) / 2;
        for (int v = 0; v < depth; v++)
        {
            for (int u = 0; u < lot.W; u++)
            {
                ref Tile t = ref lot.At(u, v);
                t = new Tile { Kind = TileKind.Floor, Floor = spec.Kind == CityKind.Substation ? FloorKind.CityGarage : FloorKind.Sidewalk, Zone = (byte)spec.Kind };
                bool edge = v == 0 || u == 0 || u == lot.W - 1;
                if (edge && !(v == 0 && u == gate))
                {
                    t.Kind = TileKind.Bars;
                    t.Pattern = WallPattern.CityRail;
                    t.Pier = lot.P(v == 0 ? ArchPier.East : ArchPier.North); // along the fence
                }
                // Transformers humming in the switchyard
                else if (spec.Kind == CityKind.Substation && v >= 2 && v < depth - 1 && u % 3 == 2 && u < lot.W - 2)
                {
                    t.Variant = Props.Transformer;
                    t.Pier = lot.P(ArchPier.North);
                }
            }
        }
    }

    /// <summary>Things on the roof: air-conditioning plant, old wooden water tanks on the brick buildings, a mast on the tallest.</summary>
    private static void RoofDressing(Frame f, Spec spec, ref Rng rng)
    {
        if (spec.Kind is CityKind.Garage or CityKind.Church or CityKind.Rowhouse || f.W < 6 || f.D < 6) return;
        bool brick = spec.Style is WallPattern.CityBrick or WallPattern.CityBrickDark or WallPattern.CityStone;
        int inset = spec.Setback > 0 ? 3 : 2;
        int u0 = inset, u1 = f.W - 1 - inset, v0 = inset, v1 = f.D - 1 - inset;
        if (u1 - u0 < 2 || v1 - v0 < 2) return;
        if (brick && spec.Height <= 48 && rng.Chance(0.6)) Mark(f, rng.Range(u0 + 1, u1 - 1), rng.Range(v0 + 1, v1 - 1), Props.WaterTank);
        if (spec.Height >= 60 && rng.Chance(0.6)) Mark(f, (u0 + u1) / 2, (v0 + v1) / 2, Props.Antenna);
        int units = rng.Range(1, Math.Max(1, (u1 - u0) * (v1 - v0) / 40));
        for (int i = 0; i < units; i++) Mark(f, rng.Range(u0, u1), rng.Range(v0, v1), Props.AcUnit);

        static void Mark(Frame f, int u, int v, byte what)
        {
            ref Tile t = ref f.At(u, v);
            if (t.Overhead == 0) t.Overhead = what;
        }
    }

    // ---- Ground floors ----

    /// <summary>Ceiling lights over a room: one fitting every few tiles, the rest plain.</summary>
    private static void Lights(Frame f, int v0, int v1, int spacing, CeilingKind on, ref Rng rng)
    {
        for (int v = v0; v <= v1; v++)
            for (int u = 1; u < f.W - 1; u++)
            {
                ref Tile t = ref f.At(u, v);
                bool fitting = u % spacing == spacing / 2 && v % spacing == spacing / 2;
                t.Ceiling = fitting ? (rng.Chance(0.12) ? CeilingKind.LightFlicker : on) : CeilingKind.Tile;
            }
    }

    /// <summary>A wall across the ground floor, closing off what lies behind the room (the stockroom, the rest of the building).</summary>
    private static int BackWall(Frame f, int depth, WallPattern pattern)
    {
        int back = Math.Min(f.D - 1, depth + 1);
        if (back >= f.D - 1) return f.D - 2; // the room runs right to the back wall of the building
        for (int u = 1; u < f.W - 1; u++) f.Partition(u, back, pattern, ArchPier.North);
        return back - 1;
    }

    private void OfficeLobby(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 12, WallPattern.Drywall), mid = f.W / 2;
        Lights(f, 1, last, 4, CeilingKind.LightOn, ref rng);
        // A bank of elevators in the back wall, a pair each side of the middle
        Elevators(f, last + 1, mid - 3);
        if (f.W >= 14) Elevators(f, last + 1, mid + 2);
        WallDecor(f, mid, last + 1, Decor.CallButton);
        WallDecor(f, mid - 5, last + 1, Decor.EvacMap);
        WallDecor(f, mid + 5, last + 1, Decor.Clock);
        f.Prop(mid, last - 3, Props.ReceptionDesk, ArchPier.North);
        f.Prop(mid, last - 2, Props.OfficeChair, ArchPier.North);
        for (int v = 3; v < last - 1; v += 3)
        {
            f.Prop(1, v, Props.Bench, ArchPier.East);
            f.Prop(f.W - 2, v, Props.Bench, ArchPier.West);
        }
        f.Prop(1, 1, Props.Ficus, ArchPier.North);
        f.Prop(f.W - 2, 1, Props.Ficus, ArchPier.North);
        f.Prop(1, last, Props.Vending, ArchPier.East);
        f.Prop(mid + 3, 1, Props.TrashCan, ArchPier.North);
        // Stairs that climb into the ceiling and stop
        if (f.W >= 10) Stairs(f, f.W - 3, last - 2);
        if (rng.Chance(0.5)) f.Prop(2, last, Props.Cooler, ArchPier.North);
    }

    private void HotelLobby(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 12, WallPattern.Hotel), mid = f.W / 2;
        Lights(f, 1, last, 4, CeilingKind.LightLit, ref rng);
        // A chandelier over the middle of the lobby
        if (f.Inside(mid, last / 2 + 1)) f.At(mid, last / 2 + 1).Ceiling = CeilingKind.Chandelier;
        for (int u = mid - 1; u <= mid + 1; u++) f.Prop(u, last - 1, Props.FrontDesk, ArchPier.North);
        WallDecor(f, mid, last + 1, Decor.KeyRack);
        if (f.W >= 12) Elevators(f, last + 1, f.W - 4);
        WallDecor(f, 3, last + 1, Decor.Landscape);
        // A sitting area to one side, palms in the corners
        f.Prop(2, 3, Props.Sofa, ArchPier.East);
        f.Prop(3, 3, Props.CoffeeTable, ArchPier.North);
        f.Prop(4, 3, Props.WingChair, ArchPier.West);
        f.Prop(3, 5, Props.WingChair, ArchPier.North);
        f.Prop(1, 1, Props.Palm, ArchPier.North);
        f.Prop(f.W - 2, 1, Props.Palm, ArchPier.North);
        f.Prop(f.W - 2, last, Props.GrandfatherClock, ArchPier.West);
        f.Prop(mid + 2, last - 3, Props.LuggageCart, ArchPier.North);
        f.Prop(1, last, Props.AshtrayStand, ArchPier.North);
        if (rng.Chance(0.5)) f.Prop(f.W - 3, 4, Props.GrandPiano, ArchPier.West);
    }

    private void ApartmentLobby(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 7, WallPattern.CityPlaster), mid = f.W / 2;
        Lights(f, 1, last, 3, CeilingKind.LightLit, ref rng);
        WallDecor(f, 2, last + 1, Decor.Mailboxes);
        WallDecor(f, 3, last + 1, Decor.Mailboxes);
        WallDecor(f, mid, last + 1, Decor.Directory);
        if (rng.Chance(0.5)) WallDecor(f, mid + 2, last + 1, Decor.MissingPoster);
        // The elevator is out of order; the basement door is not locked
        if (f.W >= 9) Elevators(f, last + 1, f.W - 4);
        Door(f, mid - 2, last + 1);
        Stairs(f, 1, Math.Max(1, last - 2));
        f.Prop(f.W - 2, 1, Props.Radiator, ArchPier.West);
        if (rng.Chance(0.4)) f.Prop(mid, 2, Props.Bench, ArchPier.North);
    }

    private void Diner(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 11, WallPattern.SnackMall), mid = f.W / 2;
        Lights(f, 1, last, 3, CeilingKind.LightOn, ref rng);
        int counter = f.W - 4;
        for (int v = 2; v < last; v++)
        {
            f.Prop(counter, v, Props.SnackCounter, ArchPier.West, v == 2 ? 1 : v == 4 ? 2 : 0);
            if (v % 2 == 0) f.Prop(counter - 1, v, Props.CafeChair, ArchPier.East);
        }
        f.Prop(f.W - 2, 2, Props.Stove, ArchPier.West);
        f.Prop(f.W - 2, 4, Props.Fryer, ArchPier.West);
        f.Prop(f.W - 2, 6, Props.DrinkFridge, ArchPier.West);
        f.Prop(f.W - 2, 8, Props.KitchenCounter, ArchPier.West, 1);
        // Booths along the window, and tables down the middle
        for (int u = 2; u < counter - 2; u += 4)
        {
            f.Prop(u, 2, Props.CafeTable, ArchPier.North);
            f.Prop(u - 1, 2, Props.CafeChair, ArchPier.East);
            f.Prop(u + 1, 2, Props.CafeChair, ArchPier.West);
            if (last >= 7)
            {
                f.Prop(u, 6, Props.CafeTable, ArchPier.North);
                f.Prop(u, 5, Props.CafeChair, ArchPier.South);
                f.Prop(u, 7, Props.CafeChair, ArchPier.North);
            }
        }
        WallDecor(f, mid, last + 1, Decor.MenuBoard);
        // The kitchen door, behind the counter, opens into another restaurant altogether
        if (last + 1 < f.D - 1) Door(f, f.W - 3, last + 1);
        f.Prop(1, last, Props.TrashCan, ArchPier.North);
    }

    private void Grocery(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 16, WallPattern.CityPlaster);
        Lights(f, 1, last, 3, CeilingKind.LightOn, ref rng);
        // Checkouts by the door, carts beside them
        for (int u = 2; u < Math.Min(f.W - 3, 12); u += 3) f.Prop(u, 3, Props.SnackCounter, ArchPier.West, 1);
        f.Prop(1, 1, Props.ShoppingCart, ArchPier.North);
        f.Prop(2, 1, Props.ShoppingCart, ArchPier.North);
        f.Prop(f.W - 2, 1, Props.Vending, ArchPier.West);
        // Aisles of shelves, back to back, with a gap halfway
        int gap = (6 + last) / 2;
        for (int u = 3; u < f.W - 3; u += 4)
            for (int v = 6; v < last - 1; v++)
            {
                if (v == gap) continue;
                byte shelf = (u / 4) % 2 == 0 ? Props.PantryShelf : Props.SnackShelf;
                f.Prop(u, v, shelf, ArchPier.West);
                f.Prop(u + 1, v, shelf, ArchPier.East);
            }
        // Fridges along the back
        for (int u = 1; u < f.W - 1; u++) f.Prop(u, last, u % 3 == 0 ? Props.Fridge : Props.DrinkFridge, ArchPier.North);
    }

    private void Pharmacy(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 12, WallPattern.CityPlaster), mid = f.W / 2;
        Lights(f, 1, last, 3, CeilingKind.LightOn, ref rng);
        for (int v = 2; v < last - 1; v++)
        {
            f.Prop(1, v, Props.MedCabinet, ArchPier.East);
            f.Prop(f.W - 2, v, Props.MedCabinet, ArchPier.West);
        }
        for (int v = 4; v < last - 2; v++)
        {
            f.Prop(mid - 1, v, Props.SnackShelf, ArchPier.West);
            f.Prop(mid, v, Props.PantryShelf, ArchPier.East);
        }
        for (int u = mid - 2; u <= mid + 2; u++) f.Prop(u, last, Props.SnackCounter, ArchPier.North, u == mid ? 1 : 0);
        f.Prop(f.W - 3, 1, Props.Vending, ArchPier.North);
        if (rng.Chance(0.5)) WallDecor(f, mid + 3, last + 1, Decor.MissingPoster);
    }

    private void HardwareStore(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 14, WallPattern.CityPlaster);
        Lights(f, 1, last, 4, CeilingKind.LightOn, ref rng);
        for (int v = 2; v < last; v++)
        {
            if (v % 3 != 1) f.Prop(1, v, Props.ToolRack, ArchPier.East);
            else f.Prop(1, v, Props.NailBarrel, ArchPier.North);
        }
        for (int u = 4; u < f.W - 3; u += 4)
            for (int v = 4; v < last - 1; v++)
            {
                f.Prop(u, v, Props.ToolShelf, ArchPier.West);
                f.Prop(u + 1, v, Props.ToolShelf, ArchPier.East);
            }
        f.Prop(f.W - 3, 2, Props.SnackCounter, ArchPier.West, 1);
        f.Prop(f.W - 2, last, Props.Workbench, ArchPier.West);
        f.Prop(f.W - 2, last - 1, Props.CableSpool, ArchPier.North);
        f.Prop(f.W - 3, last, Props.Pallet, ArchPier.North);
        f.Prop(f.W - 2, 1, Props.NailBarrel, ArchPier.North);
        if (rng.Chance(0.5)) f.Prop(2, last, Props.Toolbox, ArchPier.North);
    }

    private void ClothingStore(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 12, WallPattern.InteriorBeige), mid = f.W / 2;
        Lights(f, 1, last, 3, CeilingKind.LightOn, ref rng);
        for (int v = 3; v < last - 1; v += 3)
            for (int u = 3; u < f.W - 3; u += 2) f.Prop(u, v, Props.ClothesRack, ArchPier.North);
        for (int v = 2; v < last; v += 2)
        {
            f.Prop(1, v, Props.Wardrobe, ArchPier.East);
            f.Prop(f.W - 2, v, Props.Dresser, ArchPier.West);
        }
        f.Prop(f.W - 3, last, Props.SnackCounter, ArchPier.North, 1);
        WallDecor(f, mid, last + 1, Decor.HouseMirror);
        f.Prop(2, 1, Props.CoatStand, ArchPier.North);
        if (rng.Chance(0.5)) f.Prop(mid, last, Props.Suitcase, ArchPier.North);
    }

    private void Laundromat(Frame f, ref Rng rng)
    {
        int last = BackWall(f, 12, WallPattern.CityPlaster), mid = f.W / 2;
        Lights(f, 1, last, 3, CeilingKind.LightOn, ref rng);
        for (int v = 3; v <= last; v++)
        {
            f.Prop(1, v, Props.Laundry, ArchPier.East, 0);
            f.Prop(f.W - 2, v, Props.Laundry, ArchPier.West, 1);
        }
        for (int v = 3; v < last; v += 2) f.Prop(mid, v, Props.FoldingTable, ArchPier.North);
        f.Prop(2, 1, Props.FoldingChair, ArchPier.North);
        f.Prop(3, 1, Props.FoldingChair, ArchPier.North);
        f.Prop(f.W - 2, 1, Props.Vending, ArchPier.West);
        f.Prop(mid + 1, last, Props.LaundryCart, ArchPier.North);
        f.Prop(mid - 1, 1, Props.Wastebasket, ArchPier.North);
        if (rng.Chance(0.4)) WallDecor(f, mid, last + 1, Decor.MissingPoster);
    }

    /// <summary>
    /// A cinema: rows of seats facing a screen across the back wall, the picture still running, a stop-motion picture
    /// of round green hills. Walk up to the screen and on into it, and you are in Level 94.
    /// </summary>
    private static void Cinema(Frame f)
    {
        int mid = f.W / 2, back = f.D - 2;
        for (int v = 1; v <= back; v++)
            for (int u = 1; u < f.W - 1; u++) f.At(u, v).Floor = FloorKind.HotelMaroon;
        // The screen across the back wall, and the floor right in front of it
        for (int u = 2; u < f.W - 2; u++)
        {
            ref Tile screen = ref f.At(u, back + 1);
            if (screen.Kind == TileKind.Wall) screen.Under = Unders.CinemaScreen;
            f.At(u, back).Under = Unders.CinemaScreen;
        }
        // Rows of seats, an aisle down the middle
        for (int v = 3; v < back - 3; v += 2)
            for (int u = 1; u < f.W - 1; u++)
                if (Math.Abs(u - mid) >= 1) f.Prop(u, v, Props.HotelChair, ArchPier.South);
        f.Prop(1, 1, Props.Vending, ArchPier.East);
        f.Prop(f.W - 2, 1, Props.Wastebasket, ArchPier.North);
    }

    /// <summary>A church: one tall nave, pews in rows either side of a red-carpeted aisle, an altar with candles at the far end.</summary>
    private void Church(Frame f, ref Rng rng)
    {
        int mid = f.W / 2;
        Lights(f, 1, f.D - 2, 4, CeilingKind.LightLit, ref rng);
        for (int v = 1; v < f.D - 1; v++)
            for (int u = mid - 1; u <= mid + 1; u++) f.At(u, v).Floor = FloorKind.SanctumCarpet;
        for (int v = 3; v < f.D - 5; v += 2)
            for (int u = 1; u < f.W - 1; u++)
                if (Math.Abs(u - mid) >= 2) f.Prop(u, v, Props.Pew, ArchPier.North);
        int altar = f.D - 3;
        f.Prop(mid, altar, Props.ConsoleTable, ArchPier.North);
        f.Prop(mid - 2, altar, Props.Candelabra, ArchPier.North);
        f.Prop(mid + 2, altar, Props.Candelabra, ArchPier.North);
        f.Prop(1, altar, Props.AngelStatue, ArchPier.East);
        f.Prop(f.W - 2, altar, Props.AngelStatue, ArchPier.West);
    }

    /// <summary>
    /// A parking garage: open-sided decks of concrete on columns, cars still parked on every one, a pay station by
    /// the way in, and in a back corner the ramp down to the basement, which goes on down further than it should.
    /// </summary>
    private void Garage(Frame f, ref Rng rng)
    {
        int mid = f.W / 2;
        Lights(f, 1, f.D - 2, 6, CeilingKind.LightWarm, ref rng);
        // Columns holding up the decks
        for (int v = 4; v < f.D - 2; v += 8)
            for (int u = 4; u < f.W - 2; u += 8)
                if (Math.Abs(u - mid) > 2) f.Partition(u, v, WallPattern.CityConcrete, ArchPier.North);
        // The ramp down: two wide, five steps, along the right-hand side at the back
        int ru = f.W - 4;
        for (int k = 1; k <= 5; k++)
            for (int du = 0; du < 2; du++)
            {
                int v = f.D - 2 - 5 + k;
                if (!f.Inside(ru + du, v)) continue;
                ref Tile t = ref f.At(ru + du, v);
                t.Under = Unders.GarageRamp;
                t.Stair = (byte)k;
                t.Pier = f.P(ArchPier.North);
            }
        for (int k = 0; k <= 5; k++) RailAt(f, ru - 1, f.D - 2 - 5 + k);
        // Bays along both sides and down the middle, a car in most; the decks above have theirs too
        foreach (int bu in new[] { 1, mid - 4, mid + 3, f.W - 3 })
        {
            if (bu < 1 || bu + 1 > f.W - 2) continue;
            for (int v = 3; v + 3 < f.D - 2; v += 5)
            {
                if (bu >= ru - 1 && v + 3 >= f.D - 8) continue;
                bool clear = true;
                for (int dv = 0; dv < 4 && clear; dv++)
                    for (int du = 0; du < 2; du++)
                    {
                        Tile c = f.At(bu + du, v + dv);
                        if (c.Kind != TileKind.Floor || c.Under != 0) clear = false;
                    }
                if (!clear) continue;
                ArchPier facing = bu < mid ? ArchPier.South : ArchPier.North;
                int colour = rng.Range(0, 3);
                // Every bay is marked for the upper decks; the ground deck is fuller near the way in
                for (int dv = 0; dv < 4; dv++)
                    for (int du = 0; du < 2; du++)
                    {
                        ref Tile c = ref f.At(bu + du, v + dv);
                        bool anchor = CarAnchor(f, facing, du, dv);
                        if (anchor) { c.Overhead = (byte)(1 + colour); c.Pier = f.P(facing); }
                    }
                if (rng.Chance(0.6)) PlaceFrameCar(f, bu, v, facing, colour);
            }
        }
        f.Prop(1, 1, Props.PayStation, ArchPier.East);
        f.Prop(f.W - 2, 1, Props.TrafficCone, ArchPier.North);
        if (rng.Chance(0.5)) f.Prop(2, 1, Props.WetFloorSign, ArchPier.North);
    }

    /// <summary>Whether a car's footprint tile (du across, dv along) is the one that draws it, as the world sees it.</summary>
    private static bool CarAnchor(Frame f, ArchPier facing, int du, int dv)
    {
        // In the world, a north-facing car is drawn from its north-west corner, a south-facing one from its south-east
        ArchPier world = f.P(facing);
        int wu = f.P(ArchPier.North) == ArchPier.North ? du : 1 - du, wv = f.P(ArchPier.North) == ArchPier.North ? dv : 3 - dv;
        return world == ArchPier.North ? wu == 0 && wv == 0 : wu == 1 && wv == 3;
    }

    private static void PlaceFrameCar(Frame f, int u, int v, ArchPier facing, int colour)
    {
        for (int dv = 0; dv < 4; dv++)
            for (int du = 0; du < 2; du++)
            {
                ref Tile c = ref f.At(u + du, v + dv);
                c.Variant = CarAnchor(f, facing, du, dv) ? Props.Car : Props.CarPart;
                c.Stack = (byte)colour;
                c.Pier = f.P(facing);
            }
    }

    /// <summary>A museum: galleries opening one into the next, paintings of the other levels on their walls.</summary>
    private void Museum(Frame f, ref Rng rng)
    {
        Lights(f, 1, f.D - 2, 4, CeilingKind.LightOn, ref rng);
        const int room = 12;
        // Gallery walls on a grid, each with a wide opening in the middle
        for (int v = 1; v < f.D - 1; v++)
            for (int u = 1; u < f.W - 1; u++)
            {
                bool wallU = u % room == 0 && u < f.W - 3, wallV = v % room == 0 && v < f.D - 3;
                if (!wallU && !wallV) continue;
                int along = wallU ? v % room : u % room;
                if (along is >= 5 and <= 7) continue;
                f.Partition(u, v, WallPattern.CityPlaster, ArchPier.North);
            }
        // On the gallery walls, the paintings, facing into the rooms; benches before them, cases and statues
        int painting = rng.Range(0, 7);
        for (int v = 1; v < f.D - 1; v++)
            for (int u = 1; u < f.W - 1; u++)
            {
                ref Tile t = ref f.At(u, v);
                if (t.Kind != TileKind.Wall || u % 3 != 1 && v % 3 != 1) continue;
                bool faceSouth = v % room == 0 && f.Inside(u, v + 1) && f.At(u, v + 1).Kind == TileKind.Floor;
                bool faceEast = u % room == 0 && f.Inside(u + 1, v) && f.At(u + 1, v).Kind == TileKind.Floor;
                if (!faceSouth && !faceEast) continue;
                t.Variant = (byte)(Decor.Gallery + painting++ % 8);
                t.Pier = f.P(faceSouth ? ArchPier.South : ArchPier.East);
            }
        for (int v = room / 2; v < f.D - 2; v += room)
            for (int u = room / 2; u < f.W - 2; u += room)
            {
                double r = rng.NextDouble();
                if (r < 0.35) f.Prop(u, v, Props.AngelStatue, ArchPier.North);
                else if (r < 0.7) f.Prop(u, v, Props.Bench, ArchPier.North);
                else f.Prop(u, v, Props.CurioCabinet, ArchPier.North);
                f.Prop(u + 3, v + 3, Props.CurioCabinet, ArchPier.West);
            }
        f.Prop(2, 1, Props.ReceptionDesk, ArchPier.North);
        f.Prop(f.W - 3, 1, Props.Vending, ArchPier.North);
    }

    // ---- Helpers for the ground floors ----

    /// <summary>Two-wide elevator doors in a wall (at u, u + 1), facing into the room.</summary>
    private static void Elevators(Frame f, int v, int u)
    {
        if (!f.Inside(u, v) || !f.Inside(u + 1, v)) return;
        for (int k = 0; k < 2; k++)
        {
            ref Tile t = ref f.At(u + k, v);
            if (t.Kind != TileKind.Wall) return;
        }
        // Seen from in front (from the north of the frame), the left leaf is the one to the east
        for (int k = 0; k < 2; k++)
        {
            ref Tile t = ref f.At(u + k, v);
            t.Kind = TileKind.Door;
            t.Variant = 0;
            t.Pattern = WallPattern.Elevator;
            t.Pier = f.P(ArchPier.North);
            t.Stack = (byte)(k == 1 ? 0 : 1);
        }
    }

    /// <summary>A door in an inside wall: the basement door of an apartment block, the kitchen door of a diner.</summary>
    private static void Door(Frame f, int u, int v)
    {
        if (!f.Inside(u, v)) return;
        ref Tile t = ref f.At(u, v);
        if (t.Kind != TileKind.Wall) return;
        t.Kind = TileKind.Door;
        t.Variant = 0;
        t.Pier = f.P(ArchPier.North);
    }

    private static void WallDecor(Frame f, int u, int v, byte decor)
    {
        if (!f.Inside(u, v)) return;
        ref Tile t = ref f.At(u, v);
        if (t.Kind != TileKind.Wall || t.Variant != 0) return;
        t.Variant = decor;
        t.Pier = f.P(ArchPier.North);
    }

    /// <summary>Three steps up toward the back, ending at the ceiling: stairs that lead nowhere.</summary>
    private static void Stairs(Frame f, int u, int v)
    {
        for (int k = 1; k <= 3; k++)
        {
            if (!f.Inside(u, v + k - 1)) return;
            ref Tile t = ref f.At(u, v + k - 1);
            if (t.Kind != TileKind.Floor || t.Variant != 0) return;
            t.Stair = (byte)k;
            t.Pier = f.P(ArchPier.South);
        }
    }

    private static void RailAt(Frame f, int u, int v)
    {
        if (!f.Inside(u, v)) return;
        ref Tile t = ref f.At(u, v);
        if (t.Kind != TileKind.Floor) return;
        t.Kind = TileKind.Bars;
        t.Pattern = WallPattern.CityRail;
        t.Pier = f.P(ArchPier.North); // along the ramp
    }

    // ================= The alley =================

    /// <summary>
    /// The alley through the middle of the block: wet asphalt, dumpsters and bags of rubbish against the backs of
    /// the buildings, and now and then a doorway into a darkness that does not belong to the building behind it.
    /// </summary>
    private void PlanAlley(Tile[] tiles, ref Rng rng)
    {
        for (int z = AlleyZ; z < AlleyZ + 3; z++)
            for (int x = 0; x < BlockW; x++)
            {
                ref Tile t = ref At(tiles, x, z);
                t = new Tile { Kind = TileKind.Floor, Floor = rng.Chance(0.35) ? FloorKind.AsphaltWet : FloorKind.Asphalt };
            }
        for (int x = 3; x < BlockW - 3; x++)
        {
            foreach ((int z, ArchPier face) in new[] { (AlleyZ, ArchPier.South), (AlleyZ + 2, ArchPier.North) })
            {
                ref Tile t = ref At(tiles, x, z);
                double r = rng.NextDouble();
                if (r < 0.05) { t.Variant = Props.Dumpster; t.Pier = face; }
                else if (r < 0.09) { t.Variant = Props.TrashBags; }
                else if (r < 0.11) { t.Variant = Props.WheelieBin; t.Pier = face; }
                else if (r < 0.115) { t.Variant = Props.BurnBarrel; }
            }
        }
        // A dark doorway: Level 6 is on the other side
        if (rng.Chance(0.2))
        {
            int x = rng.Range(10, BlockW - 11);
            bool north = rng.Chance(0.5);
            int wz = north ? AlleyZ - 1 : AlleyZ + 3, iz = north ? AlleyZ - 2 : AlleyZ + 4;
            ref Tile wall = ref At(tiles, x, wz);
            ref Tile inside = ref At(tiles, x, iz);
            if (wall.Kind == TileKind.Wall && (wall.Detail & CityDetail.Corner) == 0 && inside.Kind == TileKind.Floor && inside.Variant == 0)
            {
                wall.Kind = TileKind.Doorway;
                wall.Under = Unders.DarkPassage;
                inside.Under = Unders.DarkPassage;
                inside.Ceiling = CeilingKind.Tile;
                ref Tile front = ref At(tiles, x, north ? AlleyZ : AlleyZ + 2);
                front.Variant = 0;
            }
        }
    }

    // ================= Parks, plazas, parking lots =================

    /// <summary>
    /// A park: lawns behind low railings, gravel paths round and across, trees, benches and lamps along them, a
    /// fountain where the paths meet, a playground, a statue, and sometimes, in a corner, a patch of wheat.
    /// </summary>
    private void PlanPark(Tile[] tiles, ref Rng rng)
    {
        int cx = BlockW / 2, cz = BlockD / 2;
        for (int z = 0; z < BlockD; z++)
        {
            for (int x = 0; x < BlockW; x++)
            {
                ref Tile t = ref At(tiles, x, z);
                t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Lawn };
                int edge = Math.Min(Math.Min(x, BlockW - 1 - x), Math.Min(z, BlockD - 1 - z));
                bool gateX = Math.Abs(x - cx) <= 1, gateZ = Math.Abs(z - cz) <= 1;
                if (edge == 0)
                {
                    if (gateX || gateZ) { t.Floor = FloorKind.ParkPath; continue; }
                    t.Kind = TileKind.Bars;
                    t.Pattern = WallPattern.CityRail;
                    t.Pier = x == 0 || x == BlockW - 1 ? ArchPier.North : ArchPier.East; // along the fence
                    continue;
                }
                bool ring = edge is 4 or 5, cross = gateX || gateZ;
                double fd = Math.Sqrt((x - cx) * (x - cx) + (z - cz) * (z - cz));
                if (fd < 8.5)
                {
                    t.Floor = FloorKind.ParkPath;
                    if (fd < 4.6)
                    {
                        t.Kind = TileKind.Water;
                        t.Depth = (byte)(fd < 1.3 ? 4 : 1);
                        t.Floor = FloorKind.PoolDeep;
                        if (fd < 1.3) t.Under = Unders.FountainDeep;
                    }
                    else if (fd < 5.6)
                    {
                        t.Kind = TileKind.Wall;
                        t.Pattern = WallPattern.FountainRim;
                    }
                    continue;
                }
                if (ring || cross) t.Floor = FloorKind.ParkPath;
            }
        }
        // Trees on the lawns, well apart; their crowns spread over the tiles round them
        bool Lawn(int x, int z) => x > 1 && z > 1 && x < BlockW - 2 && z < BlockD - 2 && At(tiles, x, z).Kind == TileKind.Floor
            && At(tiles, x, z).Floor == FloorKind.Lawn;
        var trees = new List<(int, int)>();
        for (int z = 3; z < BlockD - 3; z += 3)
            for (int x = 3; x < BlockW - 3; x += 3)
            {
                if (!rng.Chance(0.3)) continue;
                int tx = x + rng.Range(-1, 1), tz = z + rng.Range(-1, 1);
                bool clear = true;
                for (int dz = -1; dz <= 1 && clear; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                        if (!Lawn(tx + dx, tz + dz)) { clear = false; break; }
                if (clear) trees.Add((tx, tz));
            }
        // Benches and lamps along the paths through the middle
        for (int k = 8; k < BlockD - 8; k += 6)
        {
            if (Math.Abs(k - cz) < 10) continue;
            ParkProp(tiles, cx - 2, k, Props.Bench, ArchPier.East);
            ParkProp(tiles, cx + 2, k + 3, Props.Streetlight, ArchPier.West, Lamp(ref rng));
        }
        for (int k = 8; k < BlockW - 8; k += 6)
        {
            if (Math.Abs(k - cx) < 10) continue;
            ParkProp(tiles, k, cz - 2, Props.Bench, ArchPier.South);
            ParkProp(tiles, k + 3, cz + 2, Props.Streetlight, ArchPier.North, Lamp(ref rng));
            if (k % 12 == 2) ParkProp(tiles, k + 1, cz - 2, Props.TrashCan, ArchPier.North);
        }
        ParkProp(tiles, cx + 7, cz - 7, Props.VendorCart, ArchPier.West);
        ParkProp(tiles, cx - 1, 2, Props.Vending, ArchPier.North);
        // A statue on a paved square, flowers round it
        int sx = 18, sz = 14;
        for (int dz = -2; dz <= 2; dz++)
            for (int dx = -2; dx <= 2; dx++)
            {
                ref Tile t = ref At(tiles, sx + dx, sz + dz);
                t = new Tile { Kind = TileKind.Floor, Floor = Math.Abs(dx) == 2 || Math.Abs(dz) == 2 ? FloorKind.Flowerbed : FloorKind.CityPlaza };
                if (t.Floor == FloorKind.Flowerbed) { t.Variant = Props.Flowers; t.Stack = (byte)rng.Range(0, 7); }
            }
        At(tiles, sx, sz).Variant = Props.AngelStatue;
        At(tiles, sx, sz).Pier = ArchPier.South;
        // A playground
        if (rng.Chance(0.6))
        {
            ParkProp(tiles, 62, 12, Props.SwingSet, ArchPier.South);
            ParkProp(tiles, 70, 18, Props.BasketballHoop, ArchPier.West);
        }
        // And in one corner, wheat. Nobody planted it. Stand in the middle of it and you are in Level 10
        if (rng.Chance(0.5))
        {
            int wx = 15, wz = BlockD - 15;
            for (int dz = -3; dz <= 3; dz++)
                for (int dx = -3; dx <= 3; dx++)
                {
                    ref Tile t = ref At(tiles, wx + dx, wz + dz);
                    t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Field, Variant = Props.Crop };
                    if (dx == 0 && dz == 0) t.Under = Unders.WheatPatch;
                }
            trees.RemoveAll(p => Math.Abs(p.Item1 - wx) <= 5 && Math.Abs(p.Item2 - wz) <= 5);
        }
        PlantTrees(tiles, trees);
    }

    private static byte Lamp(ref Rng rng)
    {
        double r = rng.NextDouble();
        return (byte)(r < 0.15 ? 0 : r < 0.3 ? 2 : 1); // most are dead; some flicker
    }

    private static void ParkProp(Tile[] tiles, int x, int z, byte prop, ArchPier facing, byte stack = 0)
    {
        if (x < 1 || z < 1 || x >= BlockW - 1 || z >= BlockD - 1) return;
        ref Tile t = ref At(tiles, x, z);
        if (t.Kind != TileKind.Floor || t.Variant != 0 || t.Under != 0) return;
        t.Variant = prop;
        t.Pier = facing;
        t.Stack = stack;
    }

    private static void PlantTrees(Tile[] tiles, List<(int X, int Z)> trees)
    {
        foreach ((int x, int z) in trees)
        {
            ref Tile t = ref At(tiles, x, z);
            if (t.Kind != TileKind.Floor || t.Variant != 0) continue;
            t.Variant = Props.Tree;
            for (int dz = -1; dz <= 1; dz++)
                for (int dx = -1; dx <= 1; dx++)
                {
                    if (dx == 0 && dz == 0) continue;
                    int nx = x + dx, nz = z + dz;
                    if (nx < 0 || nz < 0 || nx >= BlockW || nz >= BlockD) continue;
                    ref Tile c = ref At(tiles, nx, nz);
                    if (c.Kind == TileKind.Floor && c.Depth == 0) c.Overhead = Overheads.Leaves;
                }
        }
    }

    /// <summary>A plaza with one great tower standing in the middle of it.</summary>
    private void PlanPlaza(Tile[] tiles, District district, ref Rng rng)
    {
        Fill(tiles, 0, BlockW - 1, 0, BlockD - 1, FloorKind.CityPlaza);
        int height = 4 * rng.Range(15, 20);
        WallPattern style = rng.Chance(0.6) ? WallPattern.CityGlass : rng.Chance(0.5) ? WallPattern.CityStone : WallPattern.CityConcrete;
        CityKind kind = rng.Chance(0.25) ? CityKind.Sealed : CityKind.Office;
        if (kind == CityKind.Sealed) style = WallPattern.CityMirror;
        PlanBuilding(tiles, 16, BlockW - 17, 12, BlockD - 13, true, true, true, true,
                     new Spec(kind, height, 4 * (int)Math.Round(height * 0.6 / 4), style), ref rng);
        PlazaDressing(tiles, ref rng);
    }

    /// <summary>Round a tower or a museum: trees in planters, benches, lamps, a fountain, a vendor's cart.</summary>
    private void PlazaDressing(Tile[] tiles, ref Rng rng)
    {
        var trees = new List<(int, int)>();
        for (int z = 3; z < BlockD - 2; z += 8)
            for (int x = 4; x < BlockW - 3; x += 8)
            {
                ref Tile t = ref At(tiles, x, z);
                if (t.Kind != TileKind.Floor || t.Depth != 0) continue;
                bool clear = true;
                for (int dz = -1; dz <= 1 && clear; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        Tile c = At(tiles, x + dx, z + dz);
                        if (c.Kind != TileKind.Floor || c.Depth != 0) { clear = false; break; }
                    }
                if (!clear) continue;
                if (rng.Chance(0.55)) trees.Add((x, z));
                else if (rng.Chance(0.5)) ParkProp(tiles, x, z, Props.Bench, ArchPier.North);
                else ParkProp(tiles, x, z, Props.Streetlight, ArchPier.North, Lamp(ref rng));
            }
        PlantTrees(tiles, trees);
        ParkProp(tiles, 8, 6, Props.VendorCart, ArchPier.North);
        ParkProp(tiles, BlockW - 6, 2, Props.Vending, ArchPier.North);
        ParkProp(tiles, 12, BlockD - 3, Props.TrashCan, ArchPier.North);
    }

    /// <summary>A surface car park behind railings: bays in rows facing the aisles, a car in more than half of them.</summary>
    private void PlanParkingLot(Tile[] tiles, int bi, int bj, ref Rng rng)
    {
        for (int z = 0; z < BlockD; z++)
        {
            for (int x = 0; x < BlockW; x++)
            {
                ref Tile t = ref At(tiles, x, z);
                t = new Tile { Kind = TileKind.Floor, Floor = rng.Chance(0.12) ? FloorKind.AsphaltCracked : FloorKind.Asphalt };
                int edge = Math.Min(Math.Min(x, BlockW - 1 - x), Math.Min(z, BlockD - 1 - z));
                bool gate = (z == 0 || z == BlockD - 1) && Math.Abs(x - BlockW / 2) <= 3;
                if (edge == 0 && !gate)
                {
                    t.Kind = TileKind.Bars;
                    t.Pattern = WallPattern.CityRail;
                    t.Pier = x == 0 || x == BlockW - 1 ? ArchPier.North : ArchPier.East; // along the fence
                }
            }
        }
        // Rows of bays: four rows deep with a car in each, an aisle, four rows facing the other way, a strip with lamps
        for (int z = 2; z + 3 < BlockD - 2; z += 15)
        {
            foreach ((int row, ArchPier facing) in new[] { (z, ArchPier.South), (z + 8, ArchPier.North) })
            {
                if (row + 3 >= BlockD - 1) continue;
                for (int x = 3; x + 1 < BlockW - 2; x += 3)
                {
                    if (Math.Abs(x - BlockW / 2) <= 4) continue;
                    // The white line between bays
                    for (int dz = 0; dz < 4; dz++) At(tiles, x + 2, row + dz).Floor = FloorKind.AsphaltBayNS;
                    if (!rng.Chance(0.55)) continue;
                    int colour = rng.Range(0, 3);
                    for (int dz = 0; dz < 4; dz++)
                        for (int dx = 0; dx < 2; dx++)
                        {
                            ref Tile c = ref At(tiles, x + dx, row + dz);
                            bool anchor = facing == ArchPier.North ? dx == 0 && dz == 0 : dx == 1 && dz == 3;
                            c.Variant = anchor ? Props.Car : Props.CarPart;
                            c.Stack = (byte)colour;
                            c.Pier = facing;
                        }
                }
            }
            if (z + 13 < BlockD - 1)
                for (int x = 6; x < BlockW - 4; x += 12) ParkProp(tiles, x, z + 13, Props.Streetlight, ArchPier.North, Lamp(ref rng));
        }
        ParkProp(tiles, BlockW / 2 + 5, 1, Props.PayStation, ArchPier.North);
    }

    // ================= Streets and avenues =================

    /// <summary>
    /// A tile of an avenue or a street: the road with its markings and its parked cars, the sidewalks with what
    /// stands on them, the subway under the avenues and its stairs down, the open manholes and the broken places.
    /// </summary>
    private Tile CityStreetTile(int gx, int gz, int ux, int uz, int ax, int sz, int bi, int bj)
    {
        var t = new Tile { Kind = TileKind.Floor, Floor = FloorKind.Sidewalk };
        bool ave = ax < AveWidth, street = sz < StreetWidth;
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz, SaltCityStreet));
        bool stationStairs = false;

        if (ave)
        {
            int sl = Hashing.Mod(uz + StationReach, StreetPitch * StationEvery);
            bool station = sl < StationLength;
            t.Under = station ? Unders.Station : Unders.Subway;
            t.Pipe = (byte)ax;
            if (station)
            {
                // Stairs down to the platforms at both ends of the station, against the buildings on both sides
                int step = sl is >= 1 and <= 5 ? sl : sl >= StationLength - 6 && sl <= StationLength - 2 ? StationLength - 1 - sl : 0;
                bool stairColumn = ax <= 1 || ax >= AveWidth - 2;
                if (stairColumn && step > 0)
                {
                    t.Stair = (byte)step;
                    t.Pier = sl < StationLength / 2 ? ArchPier.North : ArchPier.South; // the way back up
                    return t;
                }
                bool alongRail = (ax == 2 || ax == AveWidth - 3) && step > 0;
                bool endRail = stairColumn && (sl == 6 || sl == StationLength - 7);
                if (alongRail || endRail)
                {
                    t.Kind = TileKind.Bars;
                    t.Pattern = WallPattern.CityRail;
                    t.Pier = alongRail ? ArchPier.North : ArchPier.East; // along the railing
                    return t;
                }
                stationStairs = sl <= 8 || sl >= StationLength - 9;
            }
        }

        bool aveRoad = ave && ax >= 3 && ax <= 13, streetRoad = street && sz >= 3 && sz <= 11;
        if (aveRoad || streetRoad)
        {
            double wet = Noise(gx / 6.0, gz / 6.0, SaltCityStreet + 1), worn = Noise(gx / 9.0, gz / 9.0, SaltCityStreet + 2);
            t.Floor = wet > 0.5 ? FloorKind.AsphaltWet : worn > 0.42 ? FloorKind.AsphaltCracked : FloorKind.Asphalt;
            if (aveRoad && streetRoad) return t; // the junction itself
            // Zebra crossings where the sidewalks cross the road
            if (aveRoad && street) { t.Floor = FloorKind.AsphaltCrossingNS; return t; }
            if (streetRoad && ave) { t.Floor = FloorKind.AsphaltCrossing; return t; }
            if (aveRoad)
            {
                // A double yellow line down the middle, white lines at the edges of the parking lanes, cars parked along both curbs
                if (ax == 8) t.Floor = FloorKind.AsphaltDoubleNS;
                else if (ax is 5 or 11) t.Floor = FloorKind.AsphaltBayNS;
                else if (ax is 3 or 4 or 12 or 13) AvenueCar(ref t, uz, ax, bi);
                return t;
            }
            // A street: the same, and under it the city's pipes, an open manhole now and then, a place where it has fallen in
            int lx = Hashing.Mod(ux, AvePitch) - AveWidth;
            if (Collapse(bi, bj, lx, sz, out double hole))
            {
                if (hole < 1)
                {
                    t.Kind = TileKind.Pit;
                    t.Under = Unders.Collapse;
                    return t;
                }
                t.Floor = FloorKind.AsphaltCracked;
                return t;
            }
            if (sz == 7) t.Floor = FloorKind.AsphaltDoubleWE;
            else if (sz is 5 or 9) t.Floor = FloorKind.AsphaltBayWE;
            else if (sz is 3 or 4 or 10 or 11 && !CollapsedStreet(bi, bj)) StreetCar(ref t, ux, sz, bj);
            if (sz == 6 && Hashing.Mod(ux, 40) == 20)
            {
                t.Floor = FloorKind.Manhole;
                if (Hashing.Unit(Hashing.Hash(seed, Hashing.FloorDiv(ux, 40), bj, SaltCityManhole)) < 0.06)
                {
                    t.Kind = TileKind.Pit;
                    t.Under = Unders.OpenManhole;
                }
            }
            return t;
        }

        // ---- Sidewalks ----
        if (ave && street)
        {
            CornerFurniture(ref t, ax, sz, r);
            return t;
        }
        if (stationStairs) return t;
        Sidewalk side = SidewalkAt(ax, sz, ux, uz, bi, bj, ave);
        SidewalkFurniture(ref t, side, gx, gz, r);
        if (t.Variant == 0 && StreetTreeNear(gx, gz)) t.Overhead = Overheads.Leaves;
        return t;
    }

    /// <summary>Where a sidewalk tile is: which row across it (curb, middle, by the buildings), how far along its block, and the block beside it.</summary>
    private readonly struct Sidewalk
    {
        public readonly bool Curb, Middle, Inner, Avenue;
        public readonly int Along, Length, BlockI, BlockJ, SideIndex;
        public readonly ArchPier Roadward;

        public Sidewalk(bool curb, bool middle, bool inner, bool avenue, int along, int length, int bi, int bj, int sideIndex, ArchPier roadward)
        {
            Curb = curb; Middle = middle; Inner = inner; Avenue = avenue; Along = along; Length = length;
            BlockI = bi; BlockJ = bj; SideIndex = sideIndex; Roadward = roadward;
        }
    }

    private static Sidewalk SidewalkAt(int ax, int sz, int ux, int uz, int bi, int bj, bool ave)
    {
        if (ave)
        {
            bool west = ax <= 2;
            int row = west ? ax : AveWidth - 1 - ax; // 0 by the buildings, 2 at the curb
            return new Sidewalk(row == 2, row == 1, row == 0, true, Hashing.Mod(uz, StreetPitch) - StreetWidth, BlockD,
                                west ? bi - 1 : bi, bj, west ? 1 : 3, west ? ArchPier.East : ArchPier.West);
        }
        bool north = sz <= 2;
        int r = north ? sz : StreetWidth - 1 - sz;
        return new Sidewalk(r == 2, r == 1, r == 0, false, Hashing.Mod(ux, AvePitch) - AveWidth, BlockW,
                            bi, north ? bj - 1 : bj, north ? 2 : 0, north ? ArchPier.South : ArchPier.North);
    }

    private void SidewalkFurniture(ref Tile t, Sidewalk s, int gx, int gz, double r)
    {
        District district = DistrictOf(s.BlockI, s.BlockJ);
        double side = Hashing.Unit(Hashing.Hash(seed, s.BlockI * 4 + s.SideIndex, s.BlockJ, SaltCitySide));
        int a = s.Along;
        ArchPier away = s.Roadward switch { ArchPier.North => ArchPier.South, ArchPier.South => ArchPier.North, ArchPier.East => ArchPier.West, _ => ArchPier.East };
        if (s.Curb)
        {
            // The city that never sleeps: most of the street lights still burn
            if (a % 20 == 10) { t.Variant = Props.Streetlight; t.Pier = s.Roadward; t.Stack = (byte)(r < 0.55 ? 0 : r < 0.65 ? 2 : 1); }
            else if (a == 8) { t.Variant = Props.FireHydrant; t.Pier = s.Roadward; }
            else if (a == 3 || a == s.Length - 4) { t.Variant = Props.TrashCan; }
            else if (IsStreetTree(s)) { t.Variant = Props.Tree; }
            else if (!s.Avenue && district != District.Downtown && a % 6 == 1 && a > 5 && a < s.Length - 6) { t.Variant = Props.ParkingMeter; t.Pier = s.Roadward; }
            else if (a == 14 && side < 0.5) { t.Variant = Props.Postbox; t.Pier = away; }
            return;
        }
        if (s.Middle)
        {
            if (s.Avenue && a == 30) { t.Variant = Props.BusShelter; t.Pier = s.Roadward; }
            else if (s.Avenue && a == 33) { t.Variant = Props.Bench; t.Pier = s.Roadward; }
            else if (a == 5 && district != District.Lowrise) { t.Variant = Props.NewsBox; t.Pier = away; }
            else if (a == 44 && side > 0.85) { t.Variant = Props.PhoneBooth; t.Pier = away; }
            else if (a == 46 && side < 0.12) { t.Variant = Props.VendorCart; t.Pier = away; }
            // Now and then the sidewalk has come loose and goes on up into the sky
            else if (a is >= 20 and <= 27 && side > 0.3 && side < 0.32) t.Roof = (byte)(3 + 2 * (a - 20));
            return;
        }
        // Against the buildings
        if (a == 22 && side > 0.55) { t.Variant = Props.Vending; t.Pier = s.Roadward; }
        else if (a == 50 && side < 0.3) { t.Variant = Props.TrashBags; }
    }

    private bool IsStreetTree(Sidewalk s)
    {
        if (!s.Curb || s.Along % 10 != 5 || s.Along < 5 || s.Along > s.Length - 6) return false;
        return DistrictOf(s.BlockI, s.BlockJ) != District.Downtown;
    }

    /// <summary>Whether a street tree stands next to this tile, so its crown spreads over it.</summary>
    private bool StreetTreeNear(int gx, int gz)
    {
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
            {
                if (dx == 0 && dz == 0) continue;
                int x = gx + dx, z = gz + dz;
                int ux = x - CityOriginX, uz = z - CityOriginZ;
                int ax = Hashing.Mod(ux, AvePitch), sz = Hashing.Mod(uz, StreetPitch);
                bool ave = ax < AveWidth, street = sz < StreetWidth;
                if (ave == street) continue; // inside a block, or on a corner
                if (ave && (ax > 2 && ax < AveWidth - 3) || street && (sz > 2 && sz < StreetWidth - 3)) continue; // the road
                if (ave)
                {
                    int sl = Hashing.Mod(uz + StationReach, StreetPitch * StationEvery);
                    if (sl < StationLength && (sl <= 8 || sl >= StationLength - 9)) continue;
                }
                Sidewalk s = SidewalkAt(ax, sz, ux, uz, Hashing.FloorDiv(ux, AvePitch), Hashing.FloorDiv(uz, StreetPitch), ave);
                if (IsStreetTree(s)) return true;
            }
        return false;
    }

    /// <summary>The corners: traffic lights (dead, stuck on red, or blinking amber), and the street signs.</summary>
    private static void CornerFurniture(ref Tile t, int ax, int sz, double r)
    {
        bool curbX = ax == 2 || ax == AveWidth - 3, curbZ = sz == 2 || sz == StreetWidth - 3;
        if (curbX && curbZ)
        {
            t.Variant = Props.TrafficLight;
            t.Pier = sz == 2 ? (ax == 2 ? ArchPier.South : ArchPier.West) : (ax == 2 ? ArchPier.East : ArchPier.North);
            t.Stack = (byte)(r < 0.55 ? 0 : r < 0.8 ? 1 : 2);
            return;
        }
        if (curbX && (sz == 1 || sz == StreetWidth - 2) && (ax == 2) == (sz == 1))
        {
            t.Variant = Props.StreetSign;
            t.Pier = ax == 2 ? ArchPier.South : ArchPier.North;
        }
    }

    private void AvenueCar(ref Tile t, int uz, int ax, int bi)
    {
        // Southbound traffic keeps to the west side, so the cars on the west curb face south
        bool west = ax <= 4;
        int slot = Hashing.FloorDiv(uz, 6), z0 = slot * 6, along = uz - z0;
        if (along >= 4) return;
        for (int j = -1; j <= 4; j++)
            if (Hashing.Mod(z0 + j, StreetPitch) < StreetWidth) return; // clear of the crossing street
        ulong h = Hashing.Hash(seed, bi * 2 + (west ? 0 : 1), slot, SaltCityCar);
        if (Hashing.Unit(h) >= 0.45) return;
        int dx = west ? ax - 3 : ax - 12;
        bool anchor = west ? dx == 1 && along == 3 : dx == 0 && along == 0;
        t.Variant = anchor ? Props.Car : Props.CarPart;
        t.Stack = (byte)((h >> 40) % 4);
        t.Pier = west ? ArchPier.South : ArchPier.North;
    }

    private void StreetCar(ref Tile t, int ux, int sz, int bj)
    {
        // Westbound traffic keeps to the north side, so the cars on the north curb face west
        bool north = sz <= 4;
        int slot = Hashing.FloorDiv(ux, 6), x0 = slot * 6, along = ux - x0;
        if (along >= 4) return;
        for (int j = -1; j <= 4; j++)
            if (Hashing.Mod(x0 + j, AvePitch) < AveWidth) return;
        ulong h = Hashing.Hash(seed, bj * 2 + (north ? 0 : 1), slot, SaltCityCar + 1);
        if (Hashing.Unit(h) >= 0.4) return;
        int dz = north ? sz - 3 : sz - 10;
        // A west-facing car is drawn from its west end on its south side; an east-facing one from its east end on its north side
        bool anchor = north ? along == 0 && dz == 1 : along == 3 && dz == 0;
        t.Variant = anchor ? Props.Car : Props.CarPart;
        t.Stack = (byte)((h >> 40) % 4);
        t.Pier = north ? ArchPier.West : ArchPier.East;
    }

    private bool CollapsedStreet(int bi, int bj) => Hashing.Unit(Hashing.Hash(seed, bi, bj, SaltCityCollapse)) < 0.035;

    /// <summary>A street that has broken and fallen in, partway along: the hole, and the cracked asphalt round it.</summary>
    private bool Collapse(int bi, int bj, int lx, int sz, out double hole)
    {
        hole = 9;
        if (!CollapsedStreet(bi, bj)) return false;
        double dx = (lx - 40) / 3.6, dz = (sz - 7) / 2.6;
        hole = dx * dx + dz * dz;
        hole += 0.25 * Noise((lx + bi * 7) / 2.0, (sz + bj * 5) / 2.0, SaltCityCollapse + 1);
        return hole < 2.2;
    }
}
