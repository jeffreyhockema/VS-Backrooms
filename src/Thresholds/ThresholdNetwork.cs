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
/// the way back, whatever it would have led to otherwise. Where there is none, a thin spot is left at the arrival:
/// step through it to return. Pits, manholes, fallen-in streets, dives, tripwires, hungry vending machines and
/// every way out of the Snackrooms are one-way.
///
/// Vintage Story's own translocators work the same way: a repaired translocator picks its exit once, builds its
/// partner there, and the pair is fixed from then on.
///
/// This class has no game dependencies, so the whole network can be exercised outside the game.
/// </summary>
public sealed class ThresholdNetwork
{
    private const ulong SaltElevator = 0x7E01, SaltDoor = 0x7E02, SaltPit = 0x7E03, SaltStairs = 0x7E04, SaltDeep = 0x7E05, SaltVending = 0x7E06;

    /// <summary>Chance that a hotel door which looks locked opens after all, and that a Level 4 vending machine is a hungry one.</summary>
    private const double OpenDoorChance = 0.06, HungryMachineChance = 0.06, OpenTunnelDoorChance = 0.3;

    public const double StandHeight = 1.05, EntryRoomHeight = 6.05;

    // What makes up each kind of threshold (and so what an arrival can stand beside to come back by)
    public static readonly Func<Tile, bool> Elevator = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator;
    public static readonly Func<Tile, bool> Stairs = t => t.Stair > 0 && t.Under == 0;
    public static readonly Func<Tile, bool> Door = t => t.Kind == TileKind.Door && t.Pattern is not (WallPattern.Elevator or WallPattern.GarageDoor);
    public static readonly Func<Tile, bool> KitchenDoor = t => t.Kind == TileKind.Door && t.Level == 6 && t.Zone == 1 && t.Variant == 3;
    /// <summary>The cyan doors marked POOL: the Poolrooms' own, the hotel's few, and the city's baths'.</summary>
    public static readonly Func<Tile, bool> PoolDoor = t => t.Kind == TileKind.Door && (t.Pattern == WallPattern.PoolDoor || t.Level == 11 && t.Zone == (byte)CityKind.Baths);
    /// <summary>A front door between Level 94 and the Suburbs.</summary>
    public static readonly Func<Tile, bool> DollDoor = t => t.Kind == TileKind.Door && t.Under == Unders.DollHouse;

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

    private Passage BothWays((int X, int Z) source, ulong key, int level, Func<Tile, bool> returnFeature = null) =>
        new Passage { Source = source, Key = key, Find = In(level, returnFeature), ReturnFeature = returnFeature, TwoWay = true };

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
        switch (level)
        {
            case 0 when tile.Kind == TileKind.Pit && rel < -1.5:
            {
                // Falling out of Level 0: you land in the pipe tunnels of Level 2
                var pit = Whole(t => t.Kind == TileKind.Pit);
                return OneWay(pit, KeyOf(pit, SaltPit), 2);
            }
            case 1 when tile.Stair >= 2 && rel >= 2.4:
            {
                // Level 1's stairwells climb into the ceiling and come out of another stairwell, or now and then
                // up the stairs of the Abandoned Office
                var stairs = Whole(Stairs);
                ulong key = KeyOf(stairs, SaltStairs + 1);
                return BothWays(stairs, key, Hashing.Unit(key) < 0.85 ? 1 : 4, Stairs);
            }
            case 4 when tile.Stair >= 1 && rel >= 1.4:
            {
                // Office stairwells loop back to the same floor... usually
                var stairs = Whole(Stairs);
                ulong key = KeyOf(stairs, SaltStairs);
                bool loops = Hashing.Unit(key) < 0.8;
                // (Level 0 has no stairwells to come out of: the way back from there is a thin spot)
                return BothWays(stairs, key, loops ? 4 : 0, loops ? Stairs : null);
            }
            case 5 when tile.Stair >= 1 && rel >= 1.4:
            {
                // The hotel's staff stairs come out somewhere in the dark
                var stairs = Whole(Stairs);
                return BothWays(stairs, KeyOf(stairs, SaltDeep + 5), 6);
            }
            case 6 when tile.Under is Unders.Descent2 or Unders.Descent3 && rel < -0.8:
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

    // ================= Thresholds you use =================

    /// <summary>
    /// The threshold behind a block someone is using (an elevator, a door, a vent, a thin spot), or null with the
    /// reason it will not let them through ("locked", "outoforder", "nowhere").
    /// </summary>
    public Passage Used(int x, int z, string kind, out string refusal)
    {
        refusal = null;
        (int X, int Z) at = (x, z);
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        int level = layout.LevelAt(mx, mz);
        // The Snackrooms' doors answer for their whole food court, so every door of a kind leads to the same place
        ulong court = Hashing.Hash(seed, mx, mz, SaltDoor + KindSalt(kind));
        ulong here = KeyOf(at, SaltDoor);

        switch (kind)
        {
            case "thinspot":
                if (TryGet(at, out _)) return new Passage { Source = at, Sound = "game:sounds/effect/translocate-breakdimension" };
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
                return WithSound(BothWays(at, here, 9, Door), "game:sounds/block/door");
            case "pooldoor":
            {
                // A door marked POOL: from the hotel or the city's baths into the Poolrooms, out of one of its own POOL
                // doors; and from the Poolrooms out into a corridor of the hotel, beside a locked guest door
                var door = layout.FeatureOrigin(x, z, PoolDoor);
                ulong key = KeyOf(door, SaltDoor + 37);
                return WithSound(level == WorldLayout.Poolrooms ? BothWays(door, key, 5, Door) : BothWays(door, key, WorldLayout.Poolrooms, PoolDoor),
                    "game:sounds/block/door");
            }
            case "dollhouse":
            {
                // A doll's house in the Suburbs opens onto a house on the hills of Level 94, and one house in forty there
                // opens back onto the Suburbs, out of a locked front door
                var door = layout.FeatureOrigin(x, z, DollDoor);
                ulong key = KeyOf(door, SaltDoor + 94);
                Passage house = level == WorldLayout.Motion ? BothWays(door, key, 9, Door) : BothWays(door, key, WorldLayout.Motion, DollDoor);
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
                if (TryGet(door, out _)) return new Passage { Source = door, Sound = "game:sounds/block/door" };
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
            return WithSound(BothWays(door, key, target, target == 5 ? Door : null), "game:sounds/block/door");
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

        int level = layout.LevelAt(WorldLayout.MacroOf(a.X), WorldLayout.MacroOf(a.Z));
        bool marker = home != null && back == null && !links.ContainsKey(Id((a.X, a.Z)));
        var link = new Link(a.X + 0.5, geometry.FloorFor(level) + a.Height, a.Z + 0.5, marker);
        links[Id(passage.Source)] = link;
        if (home != null && back != null) links[Id(back.Value)] = home.Value;
        else if (marker) links[Id((a.X, a.Z))] = home.Value;
        Dirty = true;
        return link;
    }

    // ================= Saving =================

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

    /// <summary>Reads saved links. False if there was something saved that could not be read (a newer version, or damaged).</summary>
    public bool Load(byte[] data)
    {
        links.Clear();
        Dirty = false;
        if (data == null || data.Length == 0) return true;
        try
        {
            using var reader = new BinaryReader(new MemoryStream(data));
            if (reader.ReadInt32() != SaveVersion) return false;
            for (int n = reader.ReadInt32(); n > 0; n--)
            {
                long id = reader.ReadInt64();
                links[id] = new Link(reader.ReadDouble(), reader.ReadDouble(), reader.ReadDouble(), reader.ReadBoolean());
            }
            return true;
        }
        catch (EndOfStreamException)
        {
            return false;
        }
    }
}
