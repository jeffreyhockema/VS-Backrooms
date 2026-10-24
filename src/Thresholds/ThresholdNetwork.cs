using System;
using System.Collections.Generic;
using System.IO;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>Where a threshold puts you down. <see cref="Marker"/>: a thin spot belongs there, as the way back.</summary>
public readonly record struct Link(double X, double Y, double Z, bool Marker);

/// <summary>A threshold someone is about to go through: what it is, and how to find where it leads the first time.</summary>
public sealed class Passage
{
    /// <summary>The one position that stands for the whole threshold (see <see cref="WorldLayout.FeatureOrigin"/>).</summary>
    public (int X, int Z) Source;
    public ulong Key;
    /// <summary>Finds a place to arrive for a key, with the height above the floor to arrive at; null if there is none.</summary>
    public Func<ulong, (int X, int Z, double Height)?> Find;
    /// <summary>Two-way thresholds: what beside the arrival can serve as the way back (an elevator for an elevator). Null: a thin spot.</summary>
    public Func<Tile, bool> ReturnFeature;
    /// <summary>Whether you can come back the way you went.</summary>
    public bool TwoWay;
    /// <summary>A sound to play at the threshold and a message to show on arriving, if any.</summary>
    public string Sound, Message;
    /// <summary>Only open at twilight (dusk and dawn): Level 94's rusted gates.</summary>
    public bool Twilight;
    /// <summary>
    /// A flight of stairs that goes up: one that climbs into the ceiling (Level 1's and Level 4's), or a stairwell's
    /// flight up into its shaft (Levels 1 and 4, from layout version 4). Whoever goes up it and comes out on a flight that
    /// climbs into the ceiling comes out near its top, as if they had come up that one and over, and whoever comes back
    /// down one of those this way is put down near the top of this one (see <see cref="ThresholdNetwork.TopOfFlight"/>);
    /// the stairwells' flights put people down on their landings instead (<see cref="ThresholdNetwork.FlightLanding"/>).
    /// </summary>
    public bool Upstairs;
    /// <summary>
    /// A door or an elevator (two-way, used rather than walked into): where it would leave a thin spot, the level's own
    /// door or elevator is built there instead, where one can stand (see ThresholdNetwork.WayBack.cs). Set by
    /// <see cref="ThresholdNetwork.Used"/> from the kind of block.
    /// </summary>
    public WayBackKind WayBack;
}

/// <summary>
/// The network of ways between the levels, and its two rules.
///
/// <b>Every threshold always leads to the same place.</b> Where it leads is worked out from the world seed the first
/// time anyone goes through it, then written down (<see cref="Take"/>) and saved with the world, so it never changes
/// afterwards. A threshold is one thing however many tiles it covers: both halves of a gate, every step of a flight
/// of stairs and every tile of a lake's bottom lead to the same place.
///
/// <b>If you walked through it, you can walk back. If you fell, dived or were taken, you cannot.</b> Elevators,
/// stairwells, doors, vents, gates and walls that aren't quite there are two-way: the first trip also writes down
/// the way back. Where the arrival is beside a threshold of the same kind that nothing else leads back from yet (an
/// elevator arriving beside an elevator, stairs beside stairs, a door beside a locked door), that threshold becomes
/// the way back, whatever it would have led to otherwise. Where there is none, a door or an elevator that leads on
/// has one of the level's own built in a wall beside the arrival, where one can stand naturally, as its way back (an
/// elevator for an elevator, a door for a door: ThresholdNetwork.WayBack.cs); otherwise a thin spot is left at the
/// arrival: step through it to return. Pits, manholes, fallen-in streets, dives, tripwires, hungry vending machines and
/// every way out of the Snackrooms are one-way.
///
/// Vintage Story's own translocators work the same way: a repaired translocator picks its exit once, builds its
/// partner there, and the pair is fixed from then on.
///
/// This class has no game dependencies, so the whole network can be exercised outside the game.
/// </summary>
public sealed partial class ThresholdNetwork
{
    private const ulong SaltElevator = 0x7E01, SaltDoor = 0x7E02, SaltPit = 0x7E03, SaltStairs = 0x7E04, SaltDeep = 0x7E05, SaltVending = 0x7E06;

    /// <summary>Chance that a hotel door which looks locked opens after all, and that a Level 4 vending machine is a hungry one.</summary>
    private const double OpenDoorChance = 0.06, HungryMachineChance = 0.06, OpenTunnelDoorChance = 0.3;

    /// <summary>Whether one of Level 2's steel tunnel doors (a door of one tile, at its own position) opens; the rest stay locked.
    /// (For the layout, which puts the Hub's doors only on the locked ones.)</summary>
    public static bool TunnelDoorOpens(ulong seed, int x, int z) => Hashing.Unit(Hashing.Hash(seed, x, z, SaltDoor + 2)) < OpenTunnelDoorChance;

    public const double StandHeight = 1.05, EntryRoomHeight = 6.05;

    // What makes up each kind of threshold (and so what an arrival can stand beside to come back by)
    public static readonly Func<Tile, bool> Elevator = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator;
    public static readonly Func<Tile, bool> Stairs = t => t.Stair > 0 && t.Under == 0 && !WorldLayout.IsEntryStair(t);
    /// <summary>
    /// Level 6's stairs down to Level 7, and (from layout version 9) the stairs that come down into an entry room of Level 7:
    /// each is the way back of the other.
    /// </summary>
    public static readonly Func<Tile, bool> Descent = t => WorldLayout.IsDescent(t), EntryStairs = t => WorldLayout.IsEntryStair(t);
    /// <summary>
    /// The two flights of the stairwells of Levels 1 and 4 from layout version 4 (see
    /// <see cref="WorldLayout.StairwellSteps"/>): up through the ceiling into a shaft, and down through the floor into
    /// one. Each is the way back of the other kind elsewhere: going up you come out at the top of a flight down, going
    /// down at the foot of a flight up, as between the floors of a real building. (A flight up into Level Fun is neither.)
    /// </summary>
    public static readonly Func<Tile, bool> L1FlightUp = t => t.Level == 1 && t.Stair > 0 && t.Zone == WorldLayout.FlightZoneUp;
    public static readonly Func<Tile, bool> L1FlightDown = t => t.Level == 1 && t.Stair > 0 && t.Zone == WorldLayout.FlightZoneDown;
    public static readonly Func<Tile, bool> L4FlightUp = t => t.Level == 4 && t.Stair > 0 && t.Zone == WorldLayout.FlightZoneUp;
    public static readonly Func<Tile, bool> L4FlightDown = t => t.Level == 4 && t.Stair > 0 && t.Zone == WorldLayout.FlightZoneDown;
    /// <summary>
    /// The first step of each, beside which an arrival is looked for, on its landing (the last steps lie under the far
    /// wall, with somewhere else on its other side): in Level 1 of any floor, or of one floor (by
    /// <see cref="WorldLayout.L1FloorOf"/>).
    /// </summary>
    private static readonly Func<Tile, bool> L1FlightUpFirst = t => L1FlightUp(t) && t.Stair == 1, L1FlightDownFirst = t => L1FlightDown(t) && t.Stair == 1,
        L4FlightUpFirst = t => L4FlightUp(t) && t.Stair == 1, L4FlightDownFirst = t => L4FlightDown(t) && t.Stair == 1;
    private static readonly Func<Tile, bool>[] L1FlightUpFirstOn = FloorPredicates(L1FlightUpFirst), L1FlightDownFirstOn = FloorPredicates(L1FlightDownFirst);

    /// <summary>The first step of a Level 1 flight down (or up) on a floor, or on any floor (-1).</summary>
    private static Func<Tile, bool> L1First(bool down, int floor) =>
        floor < 0 ? (down ? L1FlightDownFirst : L1FlightUpFirst) : (down ? L1FlightDownFirstOn : L1FlightUpFirstOn)[floor];

    private static Func<Tile, bool>[] FloorPredicates(Func<Tile, bool> first)
    {
        var on = new Func<Tile, bool>[WorldLayout.L1Floors];
        for (int floor = 0; floor < on.Length; floor++)
        {
            int f = floor;
            on[f] = t => first(t) && WorldLayout.L1FloorOf(t) == f;
        }
        return on;
    }

    /// <summary>
    /// Stairs that climb into the ceiling (or a wall) and stop: every flight but those of the stairwells from layout
    /// version 4 (in Level 1 since then, the stairs to nowhere).
    /// </summary>
    private static readonly Func<Tile, bool> OldStairs = t => Stairs(t) && !WorldLayout.IsShaftFlight(t);

    /// <summary>
    /// Level 1's floors (<see cref="WorldLayout.L1FloorLabel"/>): from the top ones, P4 and P5, a flight up now and then
    /// climbs out into the Abandoned Office; from the bottom one, B3, a flight down in four leads into the pipes of Level
    /// 2, where the stairs give out (the rest go on down to another B3: the stairs keep going down).
    /// </summary>
    private const int L1OfficeFrom = 6, L1Bottom = 0;
    private const double L1OfficeChance = 0.15, L1PipesChance = 0.25, L4LobbyChance = 0.2;
    public static readonly Func<Tile, bool> Door = t => t.Kind == TileKind.Door && t.Pattern is not (WallPattern.Elevator or WallPattern.GarageDoor);
    public static readonly Func<Tile, bool> KitchenDoor = t => t.Kind == TileKind.Door && t.Level == 6 && t.Zone == 1 && t.Variant == 3;
    /// <summary>The cyan doors marked POOL: the Poolrooms' own, the hotel's few, and the city's baths'.</summary>
    public static readonly Func<Tile, bool> PoolDoor = t => t.Kind == TileKind.Door && (t.Pattern == WallPattern.PoolDoor || t.Level == 11 && t.Zone == (byte)CityKind.Baths);
    /// <summary>A front door between Level 94 and the Suburbs.</summary>
    public static readonly Func<Tile, bool> DollDoor = t => t.Kind == TileKind.Door && t.Under == Unders.DollHouse;
    /// <summary>
    /// An ordinary locked door of the hotel or a house, to come back by: never a POOL door nor one of the far levels'
    /// own doors (Level Fun's FUN doors, 188's), whose way on would be lost to the way back. (Every tile of a plain door
    /// is plain, so its <see cref="WorldLayout.FeatureOrigin"/> is the same by this test as by <see cref="Door"/>, which
    /// is how using the door looks for its way back.)
    /// </summary>
    private static readonly Func<Tile, bool> PlainDoor = t => Door(t) && t.Under == 0 && (byte)t.Pattern < 64 && t.Pattern != WallPattern.PoolDoor;

    private readonly WorldLayout layout;
    private readonly WorldGeometry geometry;
    private readonly ulong seed;
    private readonly Dictionary<long, Link> links = new();

    /// <summary>Whether links have been written down since the last <see cref="Save"/>.</summary>
    public bool Dirty { get; private set; }
    public int Count => links.Count;

    public ThresholdNetwork(WorldLayout layout, WorldGeometry geometry, long seed)
    {
        this.layout = layout;
        this.geometry = geometry;
        this.seed = (ulong)seed;
    }

    private static long Id((int X, int Z) at) => ((long)at.X << 32) | (uint)at.Z;

    /// <summary>Where the threshold at a position leads, if anyone has been through it (or come back by it) yet.</summary>
    public bool TryGet((int X, int Z) at, out Link link) => links.TryGetValue(Id(at), out link);

    private ulong KeyOf((int X, int Z) source, ulong salt) => Hashing.Hash(seed, source.X, source.Z, salt);

    private Func<ulong, (int X, int Z, double Height)?> In(int level, Func<Tile, bool> beside = null) => key =>
        layout.FindArrival(level, key, beside) is { } a ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : null;

    /// <summary>Surfacing in a Suburbs backyard pool that was never drained (or, if none is near, anywhere in the Suburbs).</summary>
    private Func<ulong, (int X, int Z, double Height)?> InFullPool() => key =>
    {
        if (layout.FindArrival(9, key, spot: t => t.Under == Unders.FullPool && t.Floor == FloorKind.PoolDeep && !t.Sealed, checkEscape: false) is { } pool)
            return (pool.X, pool.Z, 0.1);
        return layout.FindArrival(9, key) is { } a ? (a.X, a.Z, StandHeight) : null;
    };

    private Passage OneWay((int X, int Z) source, ulong key, int level) =>
        new Passage { Source = source, Key = key, Find = In(level) };

    /// <summary>A two-way threshold, coming out beside its way back (or beside <paramref name="anchor"/>, a part of it, if given).</summary>
    private Passage BothWays((int X, int Z) source, ulong key, int level, Func<Tile, bool> returnFeature = null, Func<Tile, bool> anchor = null) =>
        new Passage { Source = source, Key = key, Find = In(level, anchor ?? returnFeature), ReturnFeature = returnFeature, TwoWay = true };

    private Func<ulong, (int X, int Z, double Height)?> InSnackrooms((int Mx, int Mz)? avoid = null, Func<Tile, bool> beside = null) => key =>
    {
        (int Mx, int Mz)? cell = layout.SnackroomCellFor(key);
        if (cell == null || cell == avoid) return null;
        return layout.FindSnackroomsArrival(key, beside) is { } a ? (a.X, a.Z, StandHeight) : null;
    };

    // ================= Thresholds you stumble through =================

    /// <summary>
    /// The threshold someone standing (falling, swimming) on a tile is going through, if any. <paramref name="rel"/>
    /// is their height above the level's floor.
    /// </summary>
    public Passage Walked(int x, int z, in Tile tile, double rel)
    {
        int level = tile.Level;
        (int X, int Z) Whole(Func<Tile, bool> part) => layout.FeatureOrigin(x, z, t => t.Level == level && part(t));
        // The five kept as 14-18 keep their thresholds, out of them and into them from anywhere, in their own files
        Passage region = RunWalked(x, z, tile, rel) ?? FunWalked(x, z, tile, rel) ?? EndWalked(x, z, tile, rel)
            ?? HubWalked(x, z, tile, rel) ?? L974Walked(x, z, tile, rel) ?? L3999Walked(x, z, tile, rel) ?? L188Walked(x, z, tile, rel);
        if (region != null) return region;
        switch (level)
        {
            case 0 when tile.Kind == TileKind.Pit && rel < -1.5:
            {
                // Falling out of Level 0: you land in the pipe tunnels of Level 2
                var pit = Whole(t => t.Kind == TileKind.Pit);
                return OneWay(pit, KeyOf(pit, SaltPit), 2);
            }
            case 1 or 4 when tile.Zone == WorldLayout.FlightZoneUp && tile.Stair >= WorldLayout.UpTripStep(level) && rel >= WorldLayout.UpTripStep(level) + 0.4:
                // Up a stairwell's flight, through the ceiling and on up into the dark of the shaft
                return FlightUpTrip(level, Whole(level == 1 ? L1FlightUp : L4FlightUp));
            case 1 or 4 when tile.Zone == WorldLayout.FlightZoneDown && rel <= WorldLayout.DownTripRel:
                // Down a stairwell's flight, through the floor and on down to its last step, in the dark under the far wall
                return FlightDownTrip(level, Whole(level == 1 ? L1FlightDown : L4FlightDown));
            case 1 when tile.Zone == WorldLayout.NowhereLanding && rel >= WorldLayout.NowhereTripRel && layout.Version >= 10 && NowhereFlight(x, z, tile) is { } flight:
                // From layout version 10, the stairs to nowhere go on in the dark through a doorway in the wall and over the
                // next stall's ceiling to a landing, where the trip is (their steps no longer trip, see below)
                return NowhereTrip(flight);
            case 1 when tile.Stair >= 2 && rel >= 2.4 && !WorldLayout.IsShaftFlight(tile) && tile.Zone != WorldLayout.FlightZoneNowhere:
                // Level 1's other stairs climb into the ceiling (or a wall) and come out of another stairwell, or now and
                // then up the stairs of the Abandoned Office. Up to layout version 4 that was every stairwell's; since,
                // only the stairs to nowhere's, and they come out at the top of a stairwell's flight down, on any floor
                return NowhereTrip(Whole(OldStairs));
            case 4 when tile.Stair >= 1 && rel >= 1.4 && !WorldLayout.IsShaftFlight(tile):
            {
                // Office stairwells loop back to the same floor... usually
                var stairs = Whole(Stairs);
                ulong key = KeyOf(stairs, SaltStairs);
                bool loops = Hashing.Unit(key) < 0.8;
                // (Level 0 has no stairwells to come out of: the way back from there is a thin spot)
                Passage up = BothWays(stairs, key, loops ? 4 : 0, loops ? Stairs : null);
                up.Upstairs = true;
                return up;
            }
            case 5 when tile.Stair >= 1 && tile.Grand:
            {
                // A front hall's grand staircase (layout version 5) climbs through the ceiling and back up to Level 4,
                // out on the landing of a stairwell's flight down, whose steps lead back down to it (the lore's way in
                // and out: down an old stairway in Level 4, and back up the stairs). Its lower steps are only steps
                if (tile.Stair < WorldLayout.GrandStairTripStep || rel < WorldLayout.GrandStairTripStep + 0.4) return null;
                var grand = Whole(t => t.Grand && t.Stair > 0);
                Passage up = ToStairwell(grand, KeyOf(grand, SaltStairs + 5), 4, L4FlightDown, L4FlightDownFirst);
                up.Upstairs = true;
                return up;
            }
            case 5 when tile.Stair >= 1 && rel >= 1.4:
            {
                // The hotel's staff stairs come out somewhere in the dark
                var stairs = Whole(Stairs);
                return BothWays(stairs, KeyOf(stairs, SaltDeep + 5), 6);
            }
            case 6 when layout.Version >= 9 && tile.Under == Unders.Descent3 && rel < WorldLayout.L6DescentTripRel:
            {
                // From layout version 9: down the stairwell to its landing and on, "directly" into an entry room of Level 7,
                // at the foot of the stairs that come down into it; back up those stairs is back to this landing
                var descent = Whole(t => WorldLayout.IsDescent(t));
                return new Passage
                {
                    Source = descent, Key = KeyOf(descent, SaltDeep + 6), TwoWay = true, ReturnFeature = EntryStairs,
                    Find = key => layout.FindEntryRoomArrival(key) is { } room ? (room.X, room.Z, EntryRoomHeight)
                        : layout.FindArrival(7, key) is { } sea ? (sea.X, sea.Z, layout.ArrivalHeight(sea.X, sea.Z)) : null,
                };
            }
            case 7 when layout.Version >= 9 && WorldLayout.IsEntryStair(tile) && tile.Stair >= WorldLayout.EntryStairSteps && rel >= WorldLayout.EntryStairTripRel:
            {
                // Up an entry room's stairs into the dark of its shaft, and out on the landing of one of Level 6's stairwells
                // down, as if just come down it; that stairwell is the way back
                var stairs = Whole(EntryStairs);
                return new Passage
                {
                    Source = stairs, Key = KeyOf(stairs, SaltDeep + 70), TwoWay = true, ReturnFeature = Descent,
                    Find = key => layout.FindDescentLanding(key) is { } landing ? (landing.X, landing.Z, WorldLayout.L6LandingHeight)
                        : layout.FindArrival(6, key) is { } dark ? (dark.X, dark.Z, StandHeight) : null,
                };
            }
            case 6 when layout.Version < 9 && tile.Under is Unders.Descent2 or Unders.Descent3 && rel < -0.8:
            {
                // Down the stairs, toward the waves, and out of a doorway in the ceiling of the sea
                var descent = Whole(t => t.Under is >= Unders.Descent1 and <= Unders.Descent3);
                return new Passage
                {
                    Source = descent, Key = KeyOf(descent, SaltDeep + 6),
                    Find = key => layout.FindEntryRoomArrival(key) is { } room ? (room.X, room.Z, EntryRoomHeight)
                        : layout.FindArrival(7, key) is { } sea ? (sea.X, sea.Z, StandHeight) : null,
                };
            }
            case 6 when tile.Kind == TileKind.Floor && tile.Variant == Worldgen.Props.Tripwire && tile.Zone == 0 && rel < 1.6:
            {
                var wire = Whole(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.Tripwire);
                return new Passage { Source = wire, Key = KeyOf(wire, SaltDeep + 61), Find = InSnackrooms(), Message = "backrooms:tripwire" };
            }
            case 7 when tile.Under == Unders.Circle && rel < -tile.Depth + 3:
            {
                var circle = Whole(t => t.Under == Unders.Circle);
                return OneWay(circle, KeyOf(circle, SaltDeep + 7), 9);
            }
            case 7 when tile.Under == Unders.Cave && rel < -tile.Depth - 1:
            {
                // Through the cave and into the tunnels: out on the 9th Road
                var cave = Whole(t => t.Under == Unders.Cave);
                return OneWay(cave, KeyOf(cave, SaltDeep + 8), 8);
            }
            case 9 when tile.Kind == TileKind.Floor && tile.Variant == Worldgen.Props.FieldGate:
            {
                var gate = Whole(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.FieldGate);
                return BothWays(gate, KeyOf(gate, SaltDeep + 9), 10);
            }
            case 10 when tile.Under == Unders.LakeBottom && rel < -tile.Depth + 2.5:
            {
                var lake = Whole(t => t.Under == Unders.LakeBottom);
                return OneWay(lake, KeyOf(lake, SaltDeep + 10), 7);
            }
            case 10 when tile.Under == Unders.Noclip && rel > 0.5 && rel < 2.5:
            {
                // Into the barn wall, which isn't there, and out into the Endless City
                Passage noclip = BothWays((x, z), KeyOf((x, z), SaltDeep + 11), 11);
                noclip.Message = "backrooms:noclip";
                return noclip;
            }
            case 11 when tile.Kind == TileKind.Pit && tile.Under == Unders.OpenManhole && rel < -1.5:
                return OneWay((x, z), KeyOf((x, z), SaltDeep + 12), 2);
            case 11 when tile.Kind == TileKind.Pit && tile.Under == Unders.Collapse && rel < -2.5:
            {
                var hole = Whole(t => t.Kind == TileKind.Pit && t.Under == Unders.Collapse);
                return OneWay(hole, KeyOf(hole, SaltDeep + 13), 8);
            }
            case 11 when tile.Under == Unders.GarageRamp && rel < -1.2:
            {
                var ramp = Whole(t => t.Under == Unders.GarageRamp);
                return BothWays(ramp, KeyOf(ramp, SaltDeep + 14), 1);
            }
            case 11 when tile.Under == Unders.DarkPassage && tile.Kind == TileKind.Doorway && rel < 2:
            {
                Passage dark = BothWays((x, z), KeyOf((x, z), SaltDeep + 15), 6);
                dark.Message = "backrooms:darkpassage";
                return dark;
            }
            case 11 when tile.Under == Unders.FountainDeep && rel < -1.5:
            {
                var fountain = Whole(t => t.Under == Unders.FountainDeep);
                return OneWay(fountain, KeyOf(fountain, SaltDeep + 16), 7);
            }
            case 11 when tile.Under == Unders.WheatPatch && rel < 1.6:
                return BothWays((x, z), KeyOf((x, z), SaltDeep + 17), 10);
            case 11 when tile.Under == Unders.CinemaScreen && tile.Kind == TileKind.Floor && rel < 2.5:
            {
                // Walk up to the screen and on into the picture: you fall out of the sky over the hills of Level 94
                var screen = Whole(t => t.Under == Unders.CinemaScreen && t.Kind == TileKind.Floor);
                Passage film = BothWays(screen, KeyOf(screen, SaltDeep + 94), WorldLayout.Motion);
                film.Message = "backrooms:cinemascreen";
                return film;
            }
            case 7 when tile.Under == Unders.TiledSeabed && rel < -tile.Depth + 2:
            {
                // Down to the white tile on the seabed, and up into the Poolrooms
                var tiled = Whole(t => t.Under == Unders.TiledSeabed);
                Passage dive = OneWay(tiled, KeyOf(tiled, SaltDeep + 37), WorldLayout.Poolrooms);
                dive.Message = "backrooms:surface37";
                return dive;
            }
            case 9 when tile.Under == Unders.FullPool && tile.Floor == FloorKind.PoolDeep && rel < -0.7:
            {
                // The bottom of the pool is not the bottom
                var pool = Whole(t => t.Under == Unders.FullPool);
                Passage dive = OneWay(pool, KeyOf(pool, SaltDeep + 38), WorldLayout.Poolrooms);
                dive.Message = "backrooms:surface37";
                return dive;
            }
            case WorldLayout.Poolrooms when tile.Under == Unders.TunnelMouth && rel < 2:
            {
                // Into the black of a tunnel mouth, and out over the sea
                var mouth = Whole(t => t.Under == Unders.TunnelMouth);
                Passage tunnel = BothWays(mouth, KeyOf(mouth, SaltDeep + 39), 7);
                tunnel.Message = "backrooms:tunnelmouth";
                return tunnel;
            }
            case WorldLayout.Poolrooms when tile.Under == Unders.PoolCarpet && rel < 2:
            {
                // Where the tile gives way to office carpet: on into the Abandoned Office
                var carpet = Whole(t => t.Under == Unders.PoolCarpet);
                Passage office = BothWays(carpet, KeyOf(carpet, SaltDeep + 40), 4);
                office.Message = "backrooms:poolcarpet";
                return office;
            }
            case WorldLayout.Poolrooms when tile.Under == Unders.PitBottom && rel < -tile.Depth + 2.5:
            {
                // The bottom of a pit no one has found the bottom of: you come up in a backyard pool in the Suburbs
                var pit = Whole(t => t.Under == Unders.PitBottom);
                return new Passage { Source = pit, Key = KeyOf(pit, SaltDeep + 41), Find = InFullPool(), Message = "backrooms:pitbottom" };
            }
            case WorldLayout.Motion when tile.Kind == TileKind.Floor && tile.Variant == Worldgen.Props.TwilightGate && rel - tile.Height < 2:
            {
                // Through a rusted gate at twilight, into the fields
                var gate = Whole(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.TwilightGate);
                Passage fields = BothWays(gate, KeyOf(gate, SaltDeep + 42), 10);
                fields.Twilight = true;
                fields.Message = "backrooms:twilightgate";
                return fields;
            }
        }
        return null;
    }

    /// <summary>
    /// Up Level 1's stairs to nowhere (the steps, or from layout version 10 the landing they go on to): out of another
    /// stairwell, or now and then up the stairs of the Abandoned Office.
    /// </summary>
    private Passage NowhereTrip((int X, int Z) stairs)
    {
        ulong key = KeyOf(stairs, SaltStairs + 1);
        bool office = Hashing.Unit(key) >= 0.85;
        Passage up = office || layout.Version < 4 ? BothWays(stairs, key, office ? 4 : 1, Stairs) : ToStairwell(stairs, key, 1, L1FlightDown, L1FlightDownFirst);
        up.Upstairs = true;
        return up;
    }

    /// <summary>
    /// The stairs to nowhere (the origin of its steps) whose dark landing a tile is (layout version 10): four tiles back
    /// along the way it climbs is the third step. Null if it is not.
    /// </summary>
    public (int X, int Z)? NowhereFlight(int x, int z, in Tile landing)
    {
        if (landing.Level != 1 || landing.Zone != WorldLayout.NowhereLanding) return null;
        (int dx, int dz) = Climb(landing.Pier);
        // Straight on: four tiles back along the climb is the third step. Along the wall: three back is the doorway's last
        // tile, and the third step is one back from that, the way the doorway's step climbs
        (int X, int Z) step = (x - dx * 4, z - dz * 4);
        if (layout.TileAt(step.X, step.Z).Zone != WorldLayout.FlightZoneNowhere)
        {
            Tile door = layout.TileAt(x - dx * 3, z - dz * 3);
            if (door.Zone != WorldLayout.NowhereWall) return null;
            (int cx, int cz) = Climb(door.Pier);
            step = (x - dx * 3 - cx, z - dz * 3 - cz);
        }
        return layout.TileAt(step.X, step.Z).Zone == WorldLayout.FlightZoneNowhere ? layout.FeatureOrigin(step.X, step.Z, t => t.Level == 1 && OldStairs(t)) : null;
    }

    /// <summary>
    /// Up a flight of one of the stairwells of Levels 1 and 4 (from layout version 4): out at the top of the flight down
    /// in another stairwell, a floor up, as if come up it. In Level 1 that is a stairwell of the next floor up (from P5,
    /// another P5), or now and then, from P4 or P5, one of the Abandoned Office's; in Level 4 another of its own (the
    /// office's stairs only ever come back to the same floor).
    /// </summary>
    private Passage FlightUpTrip(int level, (int X, int Z) flight)
    {
        ulong key = KeyOf(flight, level == 1 ? SaltStairs + 1 : SaltStairs);
        int floor = WorldLayout.L1FloorOf(layout.TileAt(flight.X, flight.Z));
        Passage up = level == 4 || floor >= L1OfficeFrom && Hashing.Unit(key) >= 1 - L1OfficeChance
            ? ToStairwell(flight, key, 4, L4FlightDown, L4FlightDownFirst)
            : ToStairwell(flight, key, 1, L1FlightDown, L1First(down: true, floor < 0 ? -1 : Math.Min(floor + 1, WorldLayout.L1Floors - 1)));
        up.Upstairs = true;
        return up;
    }

    /// <summary>
    /// Down a flight of one of the stairwells of Levels 1 and 4 (from layout version 4): out at the foot of the flight up
    /// in another stairwell, a floor down, as if come down it. In Level 1 that is a stairwell of the next floor down; from
    /// the bottom, B3, another B3, except for one flight in four (fixed by where it is), which comes out in the pipe
    /// tunnels of Level 2 (back by a thin spot). In Level 4 another of its own, or one in five out into the Lobby.
    /// </summary>
    private Passage FlightDownTrip(int level, (int X, int Z) flight)
    {
        ulong key = KeyOf(flight, level == 1 ? SaltStairs + 2 : SaltStairs);
        if (level == 4)
            return Hashing.Unit(key) < 1 - L4LobbyChance ? ToStairwell(flight, key, 4, L4FlightUp, L4FlightUpFirst) : BothWays(flight, key, 0);
        int floor = WorldLayout.L1FloorOf(layout.TileAt(flight.X, flight.Z));
        if (floor == L1Bottom && Hashing.Unit(KeyOf(flight, SaltStairs + 3)) < L1PipesChance) return BothWays(flight, key, 2);
        return ToStairwell(flight, key, 1, L1FlightUp, L1First(down: false, floor < 0 ? -1 : Math.Max(floor - 1, L1Bottom)));
    }

    /// <summary>
    /// A two-way trip that comes out beside the first step of a stairwell's flight (<paramref name="first"/>), whose
    /// flight (<paramref name="flight"/>) is the way back. Only a few stairwells may be the right floor, so the search
    /// looks in up to eight places before it settles for any floor (and a thin spot back).
    /// </summary>
    private Passage ToStairwell((int X, int Z) source, ulong key, int level, Func<Tile, bool> flight, Func<Tile, bool> first) => new Passage
    {
        Source = source, Key = key, ReturnFeature = flight, TwoWay = true,
        Find = k =>
        {
            (int X, int Z)? fallback = null;
            for (int attempt = 0; attempt < StairwellSearches; attempt++, k = Hashing.Mix(k))
            {
                if (layout.FindArrival(level, k, first) is not { } a) continue;
                if (layout.FeatureBeside(a.X, a.Z, first) != null)
                {
                    // (From layout version 9 a public stairwell's flights are two wide, with a landing tile before each lane's
                    // first step: the one taken is always the landing of the lane that stands for the flight, where whoever
                    // comes back down it is put too, FlightLanding)
                    if (layout.Version >= 9 && layout.FeatureBeside(a.X, a.Z, flight) is { } whole && FlightLandingAt(whole) is { } landing) a = landing;
                    return (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z));
                }
                fallback ??= a;
            }
            return fallback is { } f ? (f.X, f.Z, layout.ArrivalHeight(f.X, f.Z)) : null;
        },
    };

    /// <summary>How many places <see cref="ToStairwell"/> looks in for a stairwell of the right floor.</summary>
    private const int StairwellSearches = 8;

    // ================= Thresholds you use =================

    /// <summary>
    /// The threshold behind a block someone is using (an elevator, a door, a vent, a thin spot), or null with the
    /// reason it will not let them through ("locked", "outoforder", "nowhere", or a region's own: "endexit", "endfake",
    /// "l3999-staff"; ThresholdSystem picks the message by it).
    /// </summary>
    public Passage Used(int x, int z, string kind, out string refusal)
    {
        Passage passage = UsedThreshold(x, z, kind, out refusal);
        // Doors and elevators that lead on can have a door or an elevator built where they come out, as the way back
        if (passage is { TwoWay: true, Find: not null }) passage.WayBack = WayBackKindOf(kind);
        return passage;
    }

    private Passage UsedThreshold(int x, int z, string kind, out string refusal)
    {
        refusal = null;
        (int X, int Z) at = (x, z);
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        int level = layout.LevelAt(mx, mz);
        // The Snackrooms' doors answer for their whole food court, so every door of a kind leads to the same place
        ulong court = Hashing.Hash(seed, mx, mz, SaltDoor + KindSalt(kind));
        ulong here = KeyOf(at, SaltDoor);

        // The five kept as 14-18 answer for their own kinds of block first, in their own files
        Passage region = RunUsed(x, z, level, kind, ref refusal) ?? FunUsed(x, z, level, kind, ref refusal) ?? EndUsed(x, z, level, kind, ref refusal)
            ?? HubUsed(x, z, level, kind, ref refusal) ?? L974Used(x, z, level, kind, ref refusal)
            ?? L3999Used(x, z, level, kind, ref refusal) ?? L188Used(x, z, level, kind, ref refusal);
        if (region != null || refusal != null) return region;

        switch (kind)
        {
            case "thinspot":
                // Always the way back of a two-way threshold (so two-way itself, for the map), and only ever written down
                if (TryGet(at, out _)) return new Passage { Source = at, TwoWay = true, Sound = "game:sounds/effect/translocate-breakdimension" };
                refusal = "nowhere";
                return null;
            case "elevator":
            {
                // Both leaves of a two-wide elevator are the same elevator
                var car = layout.FeatureOrigin(x, z, Elevator);
                ulong key = KeyOf(car, SaltElevator);
                // In the city it depends on the building: an office tower's go to the Abandoned Office, a hotel's to
                // the Terror Hotel, and an apartment block's are out of order
                int target = level == 11 ? layout.CityElevatorTarget(car.X, car.Z) : ElevatorTarget(level, Hashing.Unit(key));
                if (target < 0 && !TryGet(car, out _))
                {
                    refusal = "outoforder";
                    return null;
                }
                // Level 1 has no elevators to arrive beside: the way back from there is a thin spot
                Passage ride = BothWays(car, key, target, target == 1 ? null : Elevator);
                ride.Sound = "game:sounds/block/metaldoor";
                return ride;
            }
            case "rustydoor":
                return new Passage { Source = at, Key = court, Find = In(6), Sound = "game:sounds/block/metaldoor" };
            case "glassdoor":
                return new Passage { Source = at, Key = court, Find = In(Hashing.Unit(court) < 0.6 ? 4 : 5), Sound = "game:sounds/block/glass" };
            case "kitchendoor":
            {
                // A city diner's kitchen door opens into a food court of the Snackrooms, out of one of its kitchen
                // doors, and that door leads back: the one sure way in and out of the Snackrooms
                if (level == 11)
                    return new Passage { Source = at, Key = court, Find = InSnackrooms(beside: KitchenDoor), ReturnFeature = KitchenDoor, TwoWay = true, Sound = "game:sounds/block/door" };
                // A food court's own kitchen doors lead to another food court, and shut behind you
                var door = layout.FeatureOrigin(x, z, KitchenDoor);
                return new Passage { Source = door, Key = court, Find = InSnackrooms(avoid: (mx, mz)), Sound = "game:sounds/block/door" };
            }
            case "vent":
            {
                // The Snackrooms' vents lead to the Electrical Station and shut behind you; the vents beside the 9th
                // Road lead up into the pipes, and you can crawl back
                Passage vent = level == 6 ? new Passage { Source = at, Key = court, Find = In(3) } : BothWays(at, here, 2);
                vent.Sound = "game:sounds/block/heavymetal-hit";
                return vent;
            }
            case "rowhouse":
                // A rowhouse's front door opens into the Suburbs: where it can, out of a house's locked front door
                return WithSound(BothWays(at, here, 9, PlainDoor), "game:sounds/block/door");
            case "pooldoor":
            {
                // A door marked POOL: from the hotel or the city's baths into the Poolrooms, out of one of its own POOL
                // doors; and from the Poolrooms out into a corridor of the hotel, beside a locked guest door
                var door = layout.FeatureOrigin(x, z, PoolDoor);
                ulong key = KeyOf(door, SaltDoor + 37);
                return WithSound(level == WorldLayout.Poolrooms ? BothWays(door, key, 5, PlainDoor) : BothWays(door, key, WorldLayout.Poolrooms, PoolDoor),
                    "game:sounds/block/door");
            }
            case "dollhouse":
            {
                // A doll's house in the Suburbs opens onto a house on the hills of Level 94, and one house in forty there
                // opens back onto the Suburbs, out of a locked front door
                var door = layout.FeatureOrigin(x, z, DollDoor);
                ulong key = KeyOf(door, SaltDoor + 94);
                Passage house = level == WorldLayout.Motion ? BothWays(door, key, 9, PlainDoor) : BothWays(door, key, WorldLayout.Motion, DollDoor);
                house.Message = level == WorldLayout.Motion ? null : "backrooms:dollhouse";
                return WithSound(house, "game:sounds/block/door");
            }
            case "floodedhouse":
            {
                // A house full of water to its ceiling: open the door and it takes you, out into the sea
                ulong key = KeyOf(at, SaltDoor + 95);
                return new Passage { Source = at, Key = key, Find = In(7), Message = "backrooms:floodedhouse", Sound = "game:sounds/environment/largesplash1" };
            }
            case "basement":
                return WithSound(BothWays(at, here, 0), "game:sounds/block/door");
            case "substation":
                return WithSound(BothWays(at, here, 3), "game:sounds/block/metaldoor");
            case "maintenance":
                return WithSound(BothWays(at, here, 2), "game:sounds/block/metaldoor");
            case "tunneldoor":
            {
                // A steel door off one of Level 2's tunnels. Most are locked; some open, onto the Electrical
                // Station, the Abandoned Office, or now and then back in Level 1
                var door = layout.FeatureOrigin(x, z, Door);
                ulong key = KeyOf(door, SaltDoor + 2);
                if (!TryGet(door, out _) && Hashing.Unit(key) >= OpenTunnelDoorChance)
                {
                    refusal = "locked";
                    return null;
                }
                double where = Hashing.Unit(Hashing.Mix(key));
                return WithSound(BothWays(door, key, where < 0.4 ? 3 : where < 0.75 ? 4 : 1), "game:sounds/block/metaldoor");
            }
            case "locked":
            {
                // A door that is simply locked, unless something on the other side has opened onto it
                var door = layout.FeatureOrigin(x, z, Door);
                if (TryGet(door, out _)) return new Passage { Source = door, TwoWay = true, Sound = "game:sounds/block/door" };
                refusal = "locked";
                return null;
            }
        }

        // A hotel door. Most are locked and stay locked; a few open, onto somewhere else: another corridor of the
        // hotel (out of another door), the Electrical Station, or the Lobby
        {
            var door = layout.FeatureOrigin(x, z, Door);
            ulong key = KeyOf(door, SaltDoor);
            if (!TryGet(door, out _) && Hashing.Unit(key) >= OpenDoorChance)
            {
                refusal = "locked";
                return null;
            }
            double where = Hashing.Unit(Hashing.Mix(key));
            int target = where < 0.5 ? 5 : where < 0.85 ? 3 : 0;
            return WithSound(BothWays(door, key, target, target == 5 ? PlainDoor : null), "game:sounds/block/door");
        }
    }

    /// <summary>A stable number for a kind of door (string.GetHashCode differs from run to run).</summary>
    private static ulong KindSalt(string kind)
    {
        ulong h = 1469598103934665603UL;
        foreach (char c in kind) h = (h ^ c) * 1099511628211UL;
        return h & 0xFFFF;
    }

    private static Passage WithSound(Passage passage, string sound)
    {
        passage.Sound = sound;
        return passage;
    }

    /// <summary>
    /// A Level 4 vending machine that takes whoever presses its buttons to the Snackrooms: a few of them do, and
    /// those always do. Null for an ordinary machine.
    /// </summary>
    public Passage Vending(int x, int z)
    {
        if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != 4) return null;
        ulong key = KeyOf((x, z), SaltVending);
        if (Hashing.Unit(key) >= HungryMachineChance) return null;
        return new Passage { Source = (x, z), Key = Hashing.Mix(key), Find = InSnackrooms(), Message = "backrooms:vending-snackrooms", Sound = "game:sounds/block/vesselopen" };
    }

    /// <summary>
    /// Where the King sends whoever wins his trial, one way, from his table (so it is the same for everyone): the
    /// Habitable Zone, the Abandoned Office, or back to a town in Level 94.
    /// </summary>
    public Passage Trial((int X, int Z) chair)
    {
        ulong key = KeyOf(chair, SaltDeep + 96);
        double r = Hashing.Unit(key);
        if (r < 0.8) return new Passage { Source = chair, Key = key, Find = In(r < 0.4 ? 1 : 4), Message = "backrooms:trial-carried" };
        return new Passage
        {
            Source = chair, Key = key, Message = "backrooms:trial-carried",
            Find = k => layout.FindArrival(WorldLayout.Motion, k, spot: t => t.Floor == FloorKind.MotionConcrete && t.Variant == 0 && !t.Sealed) is { } a
                ? (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z)) : null,
        };
    }

    private static int ElevatorTarget(int level, double r) => level switch
    {
        3 => r < 0.6 ? 4 : r < 0.9 ? 5 : 3,
        4 => r < 0.5 ? 5 : r < 0.75 ? 3 : 4,
        _ => r < 0.45 ? 5 : r < 0.75 ? 3 : r < 0.9 ? 4 : 1,
    };

    // ================= Going through =================

    /// <summary>
    /// The clear floor beside a threshold where someone coming back through it is put down, for thresholds that are
    /// walked into rather than used (someone using a door comes back to where they stood).
    /// </summary>
    public Link? HomeBeside((int X, int Z) source)
    {
        if (layout.StandingSpotNear(source.X, source.Z) is not { } spot) return null;
        int level = layout.LevelAt(WorldLayout.MacroOf(spot.X), WorldLayout.MacroOf(spot.Z));
        // (On the hills of Level 94 the ground is not the level's floor, and in the Poolrooms the floor may be under water)
        return new Link(spot.X + 0.5, geometry.FloorFor(level) + layout.ArrivalHeight(spot.X, spot.Z), spot.Z + 0.5, false);
    }

    /// <summary>
    /// Where someone coming back through a walked threshold is put down: on the landing of a stairwell's flight (Levels
    /// 1 and 4, from layout version 4: <see cref="FlightLanding"/>), near the top of its flight for other stairs that go up
    /// (<see cref="Passage.Upstairs"/>), otherwise on the clear floor beside it.
    /// </summary>
    public Link? HomeFor(Passage passage) =>
        FlightLanding(passage.Source) ?? DeepStairsHome(passage.Source)
        ?? (passage.Upstairs && TopOfFlight(passage.Source) is { } top ? top : HomeBeside(passage.Source));

    /// <summary>
    /// From layout version 9, where someone coming back down (or up) the stairs between Levels 6 and 7 is put: on the
    /// first row of the landing of a Level 6 stairwell down, as if just come down it (the far rows take you on), and on
    /// the floor at the foot of an entry room's stairs, as if just come down them. Null for anything else.
    /// </summary>
    public Link? DeepStairsHome((int X, int Z) source)
    {
        if (layout.Version < 9) return null;
        Tile t = layout.TileAt(source.X, source.Z);
        if (WorldLayout.IsDescent(t) && layout.L6LandingOf(source.X, source.Z) is { } landing)
            return new Link(landing.X + 0.5, geometry.FloorFor(6) + WorldLayout.L6LandingHeight, landing.Z + 0.5, false);
        if (!WorldLayout.IsEntryStair(t)) return null;
        // The stairs climb toward their Pier from the foot, step n n tiles on from it
        (int dx, int dz) = Climb(t.Pier);
        int fx = source.X - dx * t.Stair, fz = source.Z - dz * t.Stair;
        return new Link(fx + 0.5, geometry.FloorFor(7) + EntryRoomHeight, fz + 0.5, false);
    }

    /// <summary>
    /// The way to face on being put down at the foot of an entry room's stairs (away from them, into the room, toward the
    /// doorway onto the sea) or on the landing of a Level 6 stairwell down (back up its steps), from layout version 9, as a
    /// step along x and z. Null anywhere else.
    /// </summary>
    public (int Dx, int Dz)? DeepStairsFacing(int x, int z)
    {
        if (layout.Version < 9) return null;
        Tile t = layout.TileAt(x, z);
        if (t.Level == 6 && t.Under == Unders.Descent2)
        {
            (int dx, int dz) = Climb(t.Pier); // (the way the stairwell goes down)
            return (-dx, -dz);
        }
        if (t.Level != 7 || t.Detail != WorldLayout.L7EntryFoot) return null;
        foreach ((int dx, int dz) in FlightSteps)
            if (WorldLayout.IsEntryStair(layout.TileAt(x + dx, z + dz)) && layout.TileAt(x + dx, z + dz).Stair == 1) return (-dx, -dz);
        return null;
    }

    /// <summary>The way a flight climbs, toward its <see cref="Tile.Pier"/>.</summary>
    private static (int Dx, int Dz) Climb(ArchPier pier) => pier switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    /// <summary>
    /// The floor at the open end of a flight of one of the stairwells of Levels 1 and 4 (from layout version 4), by any of its steps:
    /// before the first step of a flight up, at its foot, and past the first step of a flight down, at its top. That is
    /// where whoever comes out of the flight is put down, as if they had just come down the one or up the other (and
    /// it is no step, so nothing there takes them anywhere). Null for any other threshold.
    /// </summary>
    public Link? FlightLanding((int X, int Z) step) => FlightLandingAt(step) is { } at
        ? new Link(at.X + 0.5, geometry.FloorFor(layout.TileAt(at.X, at.Z).Level) + StandHeight, at.Z + 0.5, false) : null;

    private (int X, int Z)? FlightLandingAt((int X, int Z) step)
    {
        Tile t = layout.TileAt(step.X, step.Z);
        if (!WorldLayout.IsShaftFlight(t)) return null;
        // Each flight is straight and numbered from its landing (a flight up's steps run on the way it climbs, a flight
        // down's the other way), so its landing is as many tiles off a step as the step's number
        (int dx, int dz) = Climb(t.Pier);
        int toward = t.Zone == WorldLayout.FlightZoneDown ? 1 : -1;
        int x = step.X + toward * dx * t.Stair, z = step.Z + toward * dz * t.Stair;
        // (The tile beyond step 1 must be the landing, clear floor)
        Tile first = layout.TileAt(x - toward * dx, z - toward * dz), landing = layout.TileAt(x, z);
        if (first.Stair != 1 || first.Zone != t.Zone || landing.Kind != TileKind.Floor || landing.Stair != 0) return null;
        return (x, z);
    }

    /// <summary>
    /// The way to face on being put down at a tile (as a step along x and z), if it is the landing of a stairwell's
    /// flight (Levels 1 and 4, from layout version 4): away from the flight, as if just come off it. Null anywhere else.
    /// </summary>
    public (int Dx, int Dz)? AwayFromFlight(int x, int z)
    {
        foreach ((int dx, int dz) in FlightSteps)
            if (layout.TileAt(x + dx, z + dz) is { Stair: 1 } next && WorldLayout.IsShaftFlight(next) && FlightLandingAt((x + dx, z + dz)) == (x, z))
                return (-dx, -dz);
        return null;
    }

    /// <summary>Someone standing is this tall: the headroom a step needs to be stood on.</summary>
    private const double PersonHeight = 1.85;

    private static readonly (int, int)[] FlightSteps = { (1, 0), (-1, 0), (0, 1), (0, -1) };

    /// <summary>
    /// The highest step of a flight of stairs (by any of its tiles) that someone can stand on without their head in
    /// the ceiling, as a place to put them down, or null if there is none. The flights climb into the ceiling, so the
    /// top step or two are too close under it: in Level 1 (four high) that leaves the second step, in Level 4 (three
    /// high) the first; a step under a beam, a hanging light or a pipe has a block less. Of the tiles of that height,
    /// the first by x, then z is taken, so the answer is the same every time.
    /// </summary>
    public Link? TopOfFlight((int X, int Z) stairs)
    {
        Tile first = layout.TileAt(stairs.X, stairs.Z);
        if (!Stairs(first)) return null;
        int level = first.Level;
        if (level >= WorldGeometry.LevelRoomHeights.Length) return null;
        int room = WorldGeometry.LevelRoomHeights[level];
        (int X, int Z)? best = null;
        int bestStep = 0;
        var seen = new HashSet<(int, int)> { stairs };
        var queue = new Queue<(int X, int Z)>();
        queue.Enqueue(stairs);
        while (queue.Count > 0 && seen.Count < 256)
        {
            (int x, int z) = queue.Dequeue();
            Tile t = layout.TileAt(x, z);
            // Anything solid hanging under the slab takes the top block of the room: in Level 1 a beam, a fixture or a
            // pipe (not its sprinklers, clearance bars, signs or loose wires, which nobody bumps into); in the office a
            // cable down out of a gap (its lights and vents are in the ceiling)
            bool hung = level == 1 ? t.Beam || t.Pipe != 0 || t.Ceiling != CeilingKind.Tile
                : t.Worn && t.Pipe is Pipes.CableDroopX or Pipes.CableDroopZ;
            int ceiling = room + 1 - (hung ? 1 : 0);
            if (t.Stair + 1 + PersonHeight <= ceiling
                && (t.Stair > bestStep || t.Stair == bestStep && best is { } b && (x < b.X || x == b.X && z < b.Z)))
            {
                best = (x, z);
                bestStep = t.Stair;
            }
            foreach ((int dx, int dz) in FlightSteps)
            {
                (int X, int Z) next = (x + dx, z + dz);
                Tile n = layout.TileAt(next.X, next.Z);
                if (seen.Contains(next) || !Stairs(n) || n.Level != level) continue;
                seen.Add(next);
                queue.Enqueue(next);
            }
        }
        if (best is not { } at) return null;
        // On the step, not in it: its top is one block above its own height over the floor
        return new Link(at.X + 0.5, geometry.FloorFor(level) + bestStep + StandHeight, at.Z + 0.5, false);
    }

    /// <summary>
    /// Where a threshold leads. The first time, this finds the place and writes it down, and for a two-way threshold
    /// with somewhere to come back to (<paramref name="home"/>), writes down the way back as well. Null if it leads
    /// nowhere after all.
    /// </summary>
    public Link? Take(Passage passage, Link? home)
    {
        if (links.TryGetValue(Id(passage.Source), out Link known)) return known;
        if (passage.Find == null) return null;
        if (!passage.TwoWay) home = null;

        (int X, int Z, double Height)? arrival = null, spare = null;
        (int X, int Z)? back = null;
        ulong key = passage.Key;
        for (int attempt = 0; attempt < 6 && arrival == null; attempt++, key = Hashing.Mix(key))
        {
            if (passage.Find(key) is not { } found) continue;
            if (home == null)
            {
                arrival = found;
                break;
            }
            // Two-way: the way back is the threshold of the same kind beside the arrival, if nothing leads back from
            // it already; otherwise a thin spot on the arrival itself, if none is there already
            (int X, int Z)? feature = passage.ReturnFeature != null ? layout.FeatureBeside(found.X, found.Z, passage.ReturnFeature) : null;
            if (feature != null && feature != passage.Source && !links.ContainsKey(Id(feature.Value)))
            {
                arrival = found;
                back = feature;
            }
            else if (!links.ContainsKey(Id((found.X, found.Z))))
            {
                // The search found nowhere beside one (it looks hard): a thin spot will do. Only where the one it
                // found already leads somewhere is it worth looking again
                spare ??= found;
                if (passage.ReturnFeature == null || feature == null) arrival = found;
            }
        }
        arrival ??= spare;
        if (arrival is not { } a) return null;

        bool marker = home != null && back == null && !links.ContainsKey(Id((a.X, a.Z)));
        // A door or an elevator that would leave a thin spot: the level's own door or elevator in a wall beside the
        // arrival instead, where one can stand, and the arrival on the floor in front of it
        WayBack? built = null;
        if (marker && passage.WayBack != WayBackKind.None && PlanWayBack(passage.WayBack, a.X, a.Z) is { } plan)
        {
            built = plan.Way;
            a = (plan.X, plan.Z, layout.ArrivalHeight(plan.X, plan.Z));
            marker = false;
        }
        int level = layout.LevelAt(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z));
        var link = new Link(a.X + 0.5, geometry.FloorFor(level) + a.Height, a.Z + 0.5, marker);
        // Up one flight and out near the top of another that climbs into the ceiling, its way back, rather than at its
        // foot. (Links written down before this was so are read back as they were saved, and keep putting people at the
        // foot.) A stairwell's flight from layout version 4 as the way back is arrived at on its landing, which is where
        // the arrival was found.
        if (passage.Upstairs && back is { } other && !WorldLayout.IsShaftFlight(layout.TileAt(other.X, other.Z)) && TopOfFlight(other) is { } top)
            link = top;
        links[Id(passage.Source)] = link;
        if (home != null && back != null) links[Id(back.Value)] = home.Value;
        else if (home != null && built is { } way)
        {
            // (Every leaf of it: using either one asks for its own position, see Used)
            foreach ((int X, int Z) tile in way.Tiles) links[Id(tile)] = home.Value;
            wayBacks[Id(passage.Source)] = way;
        }
        else if (marker) links[Id((a.X, a.Z))] = home.Value;
        Dirty = true;
        return link;
    }

    // ================= Saving =================

    /// <summary>
    /// The layout of the saved links. Version 1: the version (int), the number of links (int), then for each link its
    /// threshold's id (long), where it puts you down (three doubles) and whether a thin spot belongs there (bool), 33
    /// bytes a link. A later version must still read every earlier one: worlds keep their links for good.
    /// </summary>
    private const int SaveVersion = 1;

    public byte[] Save()
    {
        using var stream = new MemoryStream();
        using (var writer = new BinaryWriter(stream))
        {
            writer.Write(SaveVersion);
            writer.Write(links.Count);
            foreach ((long id, Link link) in links)
            {
                writer.Write(id);
                writer.Write(link.X);
                writer.Write(link.Y);
                writer.Write(link.Z);
                writer.Write(link.Marker);
            }
        }
        Dirty = false;
        return stream.ToArray();
    }

    /// <summary>
    /// Reads saved links. False if there was something saved that could not all be read: a newer version (nothing is
    /// kept), or damaged. Links are a fixed size, so everything before the damage is still good and is kept (a cut-off
    /// end loses only the links that were cut off; a link with an impossible position is left out).
    /// </summary>
    public bool Load(byte[] data)
    {
        links.Clear();
        wayBacks.Clear();
        Dirty = false;
        if (data == null || data.Length == 0) return true;
        try
        {
            using var reader = new BinaryReader(new MemoryStream(data));
            int version = reader.ReadInt32();
            if (version < 1 || version > SaveVersion) return false;
            int n = reader.ReadInt32();
            if (n < 0) return false;
            bool whole = true;
            for (; n > 0; n--)
            {
                long id = reader.ReadInt64();
                var link = new Link(reader.ReadDouble(), reader.ReadDouble(), reader.ReadDouble(), reader.ReadBoolean());
                if (double.IsFinite(link.X) && double.IsFinite(link.Y) && double.IsFinite(link.Z)) links[id] = link;
                else whole = false;
            }
            return whole;
        }
        catch (EndOfStreamException)
        {
            return false;
        }
    }
}
