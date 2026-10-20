using System;
using System.Collections.Generic;
using System.IO;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>What a two-way threshold that is used (not walked into) is, for the way back that can be built where it comes out.</summary>
public enum WayBackKind : byte { None = 0, Door = 1, Elevator = 2 }

/// <summary>
/// The blocks a way back built at an arrival is made of: each level's own door or elevator. Saved by value with the
/// world (<see cref="ThresholdNetwork.SaveWayBacks"/>), so never renumber one; add new ones at the end.
/// </summary>
public enum WayBackStyle : byte
{
    /// <summary><c>backrooms:officedoor</c>: a plain wooden door in Level 0's wallpaper, an office door in Level 4's drywall.</summary>
    OfficeDoor = 1,
    /// <summary><c>backrooms:metaldoor</c>: a steel door in Level 1's concrete or Level 3's tile, brick or block.</summary>
    MetalDoor = 2,
    /// <summary><c>backrooms:tunneldoor</c> (or a painted one, by its place, as the level's own): a steel door off Level 2's tunnels.</summary>
    TunnelDoor = 3,
    /// <summary><c>backrooms:hoteldoor</c>: a guest-room door with a brass plaque, in Level 5's panelled walls.</summary>
    HotelDoor = 4,
    /// <summary><c>backrooms:pooldoor</c>: a cyan door marked POOL, in Level 37's tiled walls.</summary>
    PoolDoor = 5,
    /// <summary><c>backrooms:elevatordoor</c>: a freight elevator, one wide, in Level 1's concrete or Level 3's walls.</summary>
    FreightLift = 6,
    /// <summary><c>backrooms:liftdoor-drywall</c>: a modern elevator, two wide, in Level 0's wallpaper or Level 4's drywall.</summary>
    OfficeLift = 7,
    /// <summary><c>backrooms:liftdoor-hotel</c>: a modern elevator, two wide, in Level 5's panelled walls.</summary>
    HotelLift = 8,
    /// <summary><c>backrooms:cagelift-hotel</c>: the antique copper cage, two wide, in Level 5's panelled walls.</summary>
    HotelCage = 9,
}

/// <summary>
/// A way back built where a two-way door or elevator comes out: the wall tile of its first leaf (for a two-wide
/// elevator the one with the smaller coordinate; the second is one step on along the wall), the way it faces (toward the
/// floor in front of it, where the arrival is), and what it is made of.
/// </summary>
public readonly record struct WayBack(int X, int Z, ArchPier Facing, WayBackStyle Style)
{
    public bool Wide => Style is WayBackStyle.OfficeLift or WayBackStyle.HotelLift or WayBackStyle.HotelCage;

    /// <summary>One step along the wall, toward the larger coordinate.</summary>
    public (int Dx, int Dz) Along => Facing is ArchPier.North or ArchPier.South ? (1, 0) : (0, 1);

    /// <summary>The wall tiles it stands in, first leaf first.</summary>
    public (int X, int Z)[] Tiles => Wide ? new[] { (X, Z), (X + Along.Dx, Z + Along.Dz) } : new[] { (X, Z) };
}

/// <summary>
/// Ways back built at arrivals. A two-way door or elevator that would leave a thin spot where it comes out (there being
/// no threshold of its kind beside the arrival to come back by) has a door or an elevator built there instead, where one
/// can stand naturally: each level's own (<see cref="WayBackStyle"/>), set in a straight run of the level's own wall
/// near the arrival, with floor in front, solid wall (or a sealed room) behind, and nothing of the wall's own in the way.
/// Elevator for elevator, door for door. Where there is no such wall, and in every level not dressed here (the open
/// levels, the dark, the sea, the city's streets, the far places), the thin spot is left as before; so are the ways
/// back of thresholds that are walked into, fallen or dived through.
///
/// Like the rest of the network this is worked out from the layout alone, once, the first time anyone goes through,
/// and then written down: the arrival is the floor in front of the door, and the door's tiles (both leaves of a lift)
/// are written down as the way back, exactly as a thin spot's tile would be. The game builds the blocks once the place
/// is loaded (ThresholdSystem.BuildWayBack) and, should that not be possible after all (something put there since, a
/// claim), asks for a thin spot instead (<see cref="GiveUpWayBack"/>). A built way back is kept apart from the links
/// (<see cref="SaveWayBacks"/>), so the links' own saved layout is unchanged and every older save reads as before.
///
/// This is no part of the layout: it applies in every world, of any layout version.
/// </summary>
public sealed partial class ThresholdNetwork
{
    private const ulong SaltWayBack = 0x7E10;

    /// <summary>How many steps over open floor from the arrival a wall for the way back is looked for, and how much floor at most.</summary>
    private const int WayBackReach = 48, WayBackSearch = 12000;

    /// <summary>
    /// How near (steps) a place counts as near: a way back with solid behind it within this is preferred to one with
    /// open floor behind it (a thin partition between two aisles) nearer still, and that to a solid one farther off.
    /// </summary>
    private const int WayBackNear = 24;

    /// <summary>Ways back built at arrivals, by the threshold that leads there (its <see cref="Id"/>).</summary>
    private readonly Dictionary<long, WayBack> wayBacks = new();

    public int WayBackCount => wayBacks.Count;

    /// <summary>The way back built (or to be built) where the threshold at a position comes out, if it has one.</summary>
    public WayBack? WayBackOf((int X, int Z) source) => wayBacks.TryGetValue(Id(source), out WayBack way) ? way : null;

    /// <summary>The kinds of threshold block that are doors and elevators, for the way back built where they come out.</summary>
    private static WayBackKind WayBackKindOf(string kind) => kind switch
    {
        "elevator" or "l3999-elevator" => WayBackKind.Elevator,
        "door" or "tunneldoor" or "basement" or "substation" or "maintenance" or "rowhouse" or "pooldoor" or "dollhouse" or "kitchendoor"
            or "endexit" or "endbookstore" or "fundoor" or "mascotdoor" or "funlobbydoor" or "l3999-staff" or "l3999-revolving" or "l188-fireexit" => WayBackKind.Door,
        _ => WayBackKind.None,
    };

    /// <summary>
    /// The level's own door or elevator, for a way back built there, or null where none is built (the thin spot stays).
    /// <paramref name="pick"/> chooses between a level's styles (the hotel's modern lift or its antique cage).
    /// </summary>
    private static WayBackStyle? DressFor(int level, WayBackKind kind, ulong pick) => kind switch
    {
        WayBackKind.Door => level switch
        {
            0 or 4 => WayBackStyle.OfficeDoor,
            1 or 3 => WayBackStyle.MetalDoor,
            2 => WayBackStyle.TunnelDoor,
            5 => WayBackStyle.HotelDoor,
            WorldLayout.Poolrooms => WayBackStyle.PoolDoor,
            _ => null,
        },
        WayBackKind.Elevator => level switch
        {
            0 or 4 => WayBackStyle.OfficeLift,
            1 or 3 => WayBackStyle.FreightLift,
            // (As the hotel's own: three in ten are the modern lift)
            5 => Hashing.Unit(pick) < 0.3 ? WayBackStyle.HotelLift : WayBackStyle.HotelCage,
            _ => null,
        },
        _ => null,
    };

    /// <summary>
    /// A wall tile of the level's own ordinary wall, with nothing of its own on it, that a door or a leaf of an elevator
    /// can be set into: Level 0's wallpaper (not where the pale walls meet the paper), Level 1's bare concrete, Level 2's
    /// plain tunnel wall, Level 3's tile, brick or cinder block, Level 4's drywall, Level 5's panelled wall, Level 37's tile.
    /// </summary>
    private static bool WallTakesWayBack(int level, in Tile t)
    {
        if (t.Kind != TileKind.Wall || t.Level != level || t.Tall || t.Under != 0) return false;
        return level switch
        {
            0 => t.Pattern <= WallPattern.Manila && t.Variant == 0 && WorldLayout.L0FlipBits(t) == 0,
            // (Variant 1 is the damaged concrete, rebar showing)
            1 => t.Pattern is WallPattern.Concrete or WallPattern.WhiteBlock && t.Variant <= 1,
            // (Plain, brick, or where the pipes run along it, as the level's own doors are: never machinery, fittings or signs)
            2 => t.Pattern == WallPattern.Tunnel && t.Variant is Worldgen.Props.WallPlain or Worldgen.Props.WallBrick or Worldgen.Props.WallPipes,
            // (Tile, brick or block, whatever it is called: never a Sanctum's stone)
            3 => t.Pattern != WallPattern.Stone && t.Variant is Worldgen.Props.WallPlain or Worldgen.Props.WallBrick && !t.Low,
            4 => t.Pattern == WallPattern.Drywall && t.Variant == 0,
            5 => t.Pattern == WallPattern.Hotel && t.Variant == 0 && t.Pipe == 0,
            WorldLayout.Poolrooms => t.Pattern == WallPattern.PoolTile && t.Variant == 0,
            _ => false,
        };
    }

    /// <summary>Clear floor to stand on in front of a way back (and to be put down on): nothing on it, under it or about it, and room overhead.</summary>
    private static bool StandsBeforeWayBack(int level, in Tile t) =>
        t.Kind == TileKind.Floor && t.Level == level && !t.Sealed && t.Variant == 0 && !t.SupplyBox && t.Stack == 0 && t.Stair == 0
        && t.Under == 0 && t.Chalk == 0 && t.Floor != FloorKind.PoolDeep
        && (level != 3 || !t.Low) && (level != WorldLayout.Poolrooms || t.Depth == 0 && t.Height >= 3);

    private static readonly ArchPier[] WayBackFaces = { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West };

    private static ArchPier Opposite(ArchPier pier) => pier switch
    {
        ArchPier.North => ArchPier.South,
        ArchPier.South => ArchPier.North,
        ArchPier.East => ArchPier.West,
        _ => ArchPier.East,
    };

    /// <summary>
    /// Where a way back of the given kind can be built near an arrival: the wall for it and the floor in front of it,
    /// which becomes the arrival. The nearest such place by steps over open floor (within <see cref="WayBackReach"/>),
    /// the first found in a fixed order of looking, so the answer is the same every time. Null where there is none, or
    /// the level is not dressed for it.
    /// </summary>
    private (WayBack Way, int X, int Z)? PlanWayBack(WayBackKind kind, int ax, int az)
    {
        int level = layout.TileAt(ax, az).Level;
        if (DressFor(level, kind, Hashing.Hash(seed, ax, az, SaltWayBack)) is not { } style) return null;
        var seen = new HashSet<(int, int)> { (ax, az) };
        var queue = new Queue<(int X, int Z, int Steps)>();
        queue.Enqueue((ax, az, 0));
        bool wide = new WayBack(0, 0, ArchPier.North, style).Wide;
        // (The nearest with solid behind it, and the nearest with open floor behind it: a car park's fire wall is one block
        // thick, with the next aisle on its other side)
        (WayBack Way, int X, int Z, int Steps)? solid = null, open = null;
        while (queue.Count > 0)
        {
            (int x, int z, int steps) = queue.Dequeue();
            if (solid != null && (steps > WayBackNear || open != null)) break;
            if (StandsBeforeWayBack(level, layout.TileAt(x, z)) && !links.ContainsKey(Id((x, z))))
                foreach (ArchPier toWall in WayBackFaces)
                    for (int offset = 0; offset >= (wide ? -1 : 0); offset--)
                    {
                        if (solid == null && WayBackFits(level, style, x, z, toWall, offset) is { } way) { solid = (way, x, z, steps); goto Found; }
                        if (open == null && WayBackFits(level, style, x, z, toWall, offset, openBehind: true) is { } through) { open = (through, x, z, steps); goto Found; }
                    }
            Found:
            if (solid is { Steps: <= WayBackNear }) break;
            if (steps >= WayBackReach || seen.Count > WayBackSearch) continue;
            foreach ((int dx, int dz) in FlightSteps)
            {
                (int X, int Z) next = (x + dx, z + dz);
                if (seen.Contains(next)) continue;
                Tile n = layout.TileAt(next.X, next.Z);
                if (n.Level != level || n.Kind is not (TileKind.Floor or TileKind.Doorway or TileKind.ArchDoor or TileKind.Door) || n.Sealed) continue;
                seen.Add(next);
                queue.Enqueue((next.X, next.Z, steps + 1));
            }
        }
        // (Solid behind within reach of the arrival first; else open floor behind if that is near; else the solid one farther off)
        var pick = solid is { Steps: <= WayBackNear } || open == null || open.Value.Steps > WayBackNear && solid != null ? solid : open;
        if (pick is { } p) return (p.Way, p.X, p.Z);
        return null;
    }

    /// <summary>
    /// Whether a way back fits in the wall the given way from a floor tile, with that tile in front of its first leaf
    /// (<paramref name="offset"/> 0) or its second (-1): every leaf in the level's own wall, nothing written down on it
    /// or on the floor in front, solid behind (wall, or a sealed room nobody walks into, open floor only with <paramref name="openBehind"/>: it would
    /// show in another room), and the wall running straight on past it at both ends with floor all along in front, so it
    /// stands in a plain stretch of wall, not in a corner, a doorway, a stairwell or the end of a corridor.
    /// </summary>
    private WayBack? WayBackFits(int level, WayBackStyle style, int fx, int fz, ArchPier toWall, int offset, bool openBehind = false)
    {
        (int dx, int dz) = Climb(toWall);
        var way = new WayBack(0, 0, Opposite(toWall), style);
        (int ax, int az) = way.Along;
        int width = way.Wide ? 2 : 1;
        int x0 = fx + offset * ax + dx, z0 = fz + offset * az + dz;
        for (int k = -1; k <= width; k++)
        {
            int wx = x0 + k * ax, wz = z0 + k * az;
            Tile wall = layout.TileAt(wx, wz), front = layout.TileAt(wx - dx, wz - dz);
            if (front.Level != level || front.Kind != TileKind.Floor || front.Sealed || wall.Stair != 0) return null;
            // (Never in a stairwell: not beside a flight's steps, nor in the walls its last steps lie under)
            foreach ((int sx, int sz) in FlightSteps)
                if (layout.TileAt(wx - dx + sx, wz - dz + sz).Stair != 0) return null;
            if (k < 0 || k == width)
            {
                // (Where pipes run along the wall in Level 3's rooms they would end at the door)
                if (wall.Kind != TileKind.Wall || wall.Level != level || level == 3 && wall.Variant == Worldgen.Props.WallPipes) return null;
                continue;
            }
            if (!WallTakesWayBack(level, wall) || links.ContainsKey(Id((wx, wz)))) return null;
            if (!StandsBeforeWayBack(level, front) || links.ContainsKey(Id((wx - dx, wz - dz)))) return null;
            Tile behind = layout.TileAt(wx + dx, wz + dz);
            if (behind.Level != level || behind.Stair != 0 || !(behind.Kind == TileKind.Wall || behind.Kind == TileKind.Floor && (behind.Sealed || openBehind))) return null;
        }
        return way with { X = x0, Z = z0 };
    }

    /// <summary>
    /// The way back built for a threshold cannot stand after all (ThresholdSystem found the wall changed, or claimed):
    /// it is forgotten, its tiles lead nowhere again, and a thin spot on the arrival is the way back instead, as it
    /// would have been. Returns the threshold's link as it is now (a thin spot's), or null if it had no way back built.
    /// </summary>
    public Link? GiveUpWayBack((int X, int Z) source)
    {
        if (!wayBacks.Remove(Id(source), out WayBack way) || !links.TryGetValue(Id(source), out Link to)) return null;
        Link? home = null;
        foreach ((int X, int Z) tile in way.Tiles)
            if (links.Remove(Id(tile), out Link back)) home ??= back;
        Dirty = true;
        (int X, int Z) arrival = ((int)Math.Floor(to.X), (int)Math.Floor(to.Z));
        if (home == null || links.ContainsKey(Id(arrival))) return to;
        links[Id(source)] = to with { Marker = true };
        links[Id(arrival)] = home.Value;
        return links[Id(source)];
    }

    // ================= Saving the ways back =================

    /// <summary>
    /// The layout of the saved ways back (kept under a key of their own, beside the links). Version 1: the version (int),
    /// the number (int), then for each the id of the threshold that leads there (long), its first leaf's tile (two ints),
    /// the way it faces (byte: 0 north, 1 east, 2 south, 3 west) and its <see cref="WayBackStyle"/> (byte), 18 bytes each.
    /// A later version must still read every earlier one.
    /// </summary>
    private const int WayBackSaveVersion = 1;

    private static byte FacingByte(ArchPier pier) => pier switch { ArchPier.North => 0, ArchPier.East => 1, ArchPier.South => 2, _ => 3 };

    private static ArchPier FacingOf(byte b) => b switch { 0 => ArchPier.North, 1 => ArchPier.East, 2 => ArchPier.South, _ => ArchPier.West };

    public byte[] SaveWayBacks()
    {
        using var stream = new MemoryStream();
        using (var writer = new BinaryWriter(stream))
        {
            writer.Write(WayBackSaveVersion);
            writer.Write(wayBacks.Count);
            foreach ((long id, WayBack way) in wayBacks)
            {
                writer.Write(id);
                writer.Write(way.X);
                writer.Write(way.Z);
                writer.Write(FacingByte(way.Facing));
                writer.Write((byte)way.Style);
            }
        }
        return stream.ToArray();
    }

    /// <summary>
    /// Reads saved ways back, after the links (<see cref="Load"/>). False if something saved could not all be read (a newer
    /// version keeps nothing; a cut-off end keeps what came before it). A way back whose threshold or tiles have no link
    /// (they are written down together), or of a style this version does not know, is left out: its door, if built, still
    /// stands in the world and still leads back, as a written-down link; it is only not rebuilt.
    /// </summary>
    public bool LoadWayBacks(byte[] data)
    {
        wayBacks.Clear();
        if (data == null || data.Length == 0) return true;
        try
        {
            using var reader = new BinaryReader(new MemoryStream(data));
            int version = reader.ReadInt32();
            if (version < 1 || version > WayBackSaveVersion) return false;
            int n = reader.ReadInt32();
            if (n < 0) return false;
            for (; n > 0; n--)
            {
                long id = reader.ReadInt64();
                var way = new WayBack(reader.ReadInt32(), reader.ReadInt32(), FacingOf(reader.ReadByte()), (WayBackStyle)reader.ReadByte());
                if (!Enum.IsDefined(way.Style) || !links.ContainsKey(id)) continue;
                bool linked = true;
                foreach ((int X, int Z) tile in way.Tiles) linked &= links.ContainsKey(Id(tile));
                if (linked) wayBacks[id] = way;
            }
            return true;
        }
        catch (EndOfStreamException)
        {
            return false;
        }
    }
}
