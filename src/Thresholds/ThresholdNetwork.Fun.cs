using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level Fun's thresholds (kept as level 15): the ways out of it, and the ways into it from any other level.
///
/// Walked (two-way): one stair core in twenty in Level 1 climbs into the service stairs of Level Fun, and back; the
/// FUN doors between a hotel corridor in Level 5 and Level Fun; the gym doors at the back of a parking garage in Level
/// 11 and a waiting room's plain white door. Taken, fallen or dived (one-way): the TIME 4 FUN =) poster in a Level 0
/// party cell (in); a reversed, blurred poster (out, to Level 4); overboard from an open deck (the sea of Level 7);
/// diving to the bottom of a deep ball pit (the castle's ball pit in Level 94).
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here.</summary>
    private const ulong SaltFunThreshold = 0x15C0;

    // What makes up each of the level's thresholds (and so what an arrival can stand beside to come back by)
    public static readonly Func<Tile, bool> FunStairs = t => t.Level == WorldLayout.FunLevel && t.Stair > 0;
    public static readonly Func<Tile, bool> FunDoorTile = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.FunDoor;
    public static readonly Func<Tile, bool> FunExitDoorTile = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.FunExitDoor;
    public static readonly Func<Tile, bool> FunMascotDoorTile = t => t.Kind == TileKind.Door && t.Under == Unders.FunMascotDoor;

    /// <summary>
    /// A threshold of this level's someone standing (falling, swimming) on a tile is going through, in this level or
    /// any other (see <see cref="Walked"/>); null if none. Asked before anything else, so match only the level's own
    /// tiles (its <see cref="Unders"/>, <see cref="Props"/> and patterns).
    /// </summary>
    private Passage FunWalked(int x, int z, in Tile tile, double rel)
    {
        // Up one of Level 1's stair cores, the one in twenty with confetti trickled down its stairs: from layout version
        // 4, up its flight through the slab and into the dark of the shaft, and out of the service stairs, whose way back
        // it is (its steps are marked as Level Fun's, so no trip from another stair core comes out at its foot)
        if (tile.Level == 1 && tile.Zone == WorldLayout.FlightZoneFun && tile.Stair >= WorldLayout.UpTripStep(1) && rel >= WorldLayout.UpTripStep(1) + 0.4)
        {
            var flight = layout.FeatureOrigin(x, z, t => t.Level == 1 && t.Stair > 0 && t.Zone == WorldLayout.FlightZoneFun);
            return new Passage
            {
                Source = flight, Key = KeyOf(flight, SaltFunThreshold + 1), Find = IntoFunRoom(FunZone.Stair, FunStairs), ReturnFeature = FunStairs,
                TwoWay = true, Message = "backrooms:funstairs",
            };
        }
        if (tile.Level == 1 && tile.Stair >= 2 && rel >= 2.4 && !WorldLayout.IsShaftFlight(tile))
        {
            var stairs = layout.FeatureOrigin(x, z, t => t.Level == 1 && Stairs(t));
            if (!layout.IsFunStairCore(stairs.X, stairs.Z) || layout.TileAt(stairs.X, stairs.Z + 2).Variant != Worldgen.Props.FunConfetti) return null;
            ulong key = KeyOf(stairs, SaltFunThreshold + 1);
            return new Passage
            {
                Source = stairs, Key = key, Find = IntoFunRoom(FunZone.Stair, FunStairs), ReturnFeature = FunStairs, TwoWay = true,
                Message = "backrooms:funstairs",
            };
        }
        if (tile.Level != WorldLayout.FunLevel) return null;
        (int X, int Z) Whole(Func<Tile, bool> part) => layout.FeatureOrigin(x, z, t => t.Level == WorldLayout.FunLevel && part(t));

        // Up the service stairs into the ceiling, and out of a stairwell in Level 1
        if (tile.Stair >= 2 && rel >= 2.4)
        {
            var stairs = Whole(FunStairs);
            // (From layout version 4, out at the top of the flight down in one of Level 1's stairwells, as anyone coming
            // up does; before, near the top of a Level 1 flight, as every stairwell trip was)
            ulong key = KeyOf(stairs, SaltFunThreshold + 2);
            Passage up = layout.Version >= 4 ? ToStairwell(stairs, key, 1, L1FlightDown, L1FlightDownFirst) : BothWays(stairs, key, 1, Stairs);
            up.Message = "backrooms:funstairs";
            up.Upstairs = true;
            return up;
        }
        // Down through the balls to the bottom of a deep pit: up through the castle's ball pit, on its mountain in Level 94
        if (tile.Under == Unders.FunBallPitDeep && rel < -1.5)
        {
            var pit = Whole(t => t.Under == Unders.FunBallPitDeep);
            return new Passage { Source = pit, Key = KeyOf(pit, SaltFunThreshold + 3), Find = InCastleBallPit(), Message = "backrooms:funballpit" };
        }
        // Overboard, into the black water: the open sea of Level 7
        if (tile.Under == Unders.FunOverboard && rel < WorldLayout.FunSeaSurface + 1.5)
        {
            var sea = Whole(t => t.Under == Unders.FunOverboard);
            Passage over = OneWay(sea, KeyOf(sea, SaltFunThreshold + 4), 7);
            over.Message = "backrooms:overboard";
            over.Sound = "game:sounds/environment/largesplash1";
            return over;
        }
        return null;
    }

    /// <summary>
    /// The threshold behind a block of this level's someone is using (see <see cref="Used"/>), by the block's threshold
    /// kind; null if the kind is not the level's. Set <paramref name="refusal"/> ("locked", "outoforder", "nowhere") to
    /// refuse.
    /// </summary>
    private Passage FunUsed(int x, int z, int level, string kind, ref string refusal)
    {
        switch (kind)
        {
            case "fundoor":
            {
                // The wooden doors with FUN on them: from a hotel corridor into Level Fun, out of its own FUN doors;
                // from Level Fun back out into a hotel corridor, beside a locked guest door
                var door = layout.FeatureOrigin(x, z, FunDoorTile);
                ulong key = KeyOf(door, SaltFunThreshold + 5);
                // (Never beside a POOL door or another FUN door: the way back would be written on it, and its own way lost)
                Passage p = level == WorldLayout.FunLevel ? BothWays(door, key, 5, PlainDoor)
                    : new Passage { Source = door, Key = key, Find = IntoFunRoom(FunZone.Vestibule, FunDoorTile), ReturnFeature = FunDoorTile, TwoWay = true, Message = "backrooms:fundoor" };
                p.Sound = "game:sounds/block/door";
                return p;
            }
            case "mascotdoor":
            {
                // A parking garage's gym doors, painted with animals: into a quiet waiting room of Level Fun, out of its door
                var door = layout.FeatureOrigin(x, z, FunMascotDoorTile);
                ulong key = KeyOf(door, SaltFunThreshold + 6);
                return new Passage
                {
                    Source = door, Key = key, Find = IntoFunRoom(FunZone.Waiting, FunExitDoorTile), ReturnFeature = FunExitDoorTile, TwoWay = true,
                    Message = "backrooms:mascotdoor", Sound = "game:sounds/block/door",
                };
            }
            case "funlobbydoor":
            {
                // A waiting room's plain white door: out through the gym doors of a parking garage in the city
                var door = layout.FeatureOrigin(x, z, FunExitDoorTile);
                ulong key = KeyOf(door, SaltFunThreshold + 7);
                return new Passage
                {
                    Source = door, Key = key, Find = InFunGarage(), ReturnFeature = FunMascotDoorTile, TwoWay = true,
                    Sound = "game:sounds/block/door",
                };
            }
            case "funposter":
            {
                // A TIME 4 FUN =) poster in the Lobby: touch it and the room is full of balloons. No way back
                ulong key = KeyOf((x, z), SaltFunThreshold + 8);
                return new Passage { Source = (x, z), Key = key, Find = IntoFun(), Message = "backrooms:funposter", Sound = "game:sounds/effect/translocate-breakdimension" };
            }
            case "funposter-reversed":
            {
                // The poster that is wrong, its writing reversed and swimming: out, to the Abandoned Office
                ulong key = KeyOf((x, z), SaltFunThreshold + 9);
                return new Passage { Source = (x, z), Key = key, Find = In(4), Message = "backrooms:funposter-reversed", Sound = "game:sounds/effect/translocate-breakdimension" };
            }
        }
        return null;
    }

    /// <summary>Somewhere to arrive in the level for a key (beside a tile matching <paramref name="beside"/>, where one can be found): an elevator lobby.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoFun(Func<Tile, bool> beside = null) => In(WorldLayout.FunLevel, beside);

    /// <summary>Arriving beside one of the level's own thresholds (in a room of <paramref name="kind"/>), or in a lobby if none can be found.</summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoFunRoom(FunZone kind, Func<Tile, bool> beside) => key =>
    {
        if (layout.FunThresholdRoom(kind, key) is { } room)
        {
            var near = (WorldLayout.MacroOf((room.X0 + room.X1) / 2), WorldLayout.MacroOf((room.Z0 + room.Z1) / 2));
            if (layout.FindArrival(WorldLayout.FunLevel, key, beside, spot: t => WorldLayout.IsOpenArrivalFloor(t) && t.Zone == (byte)kind, near: near) is { } a)
                return (a.X, a.Z, StandHeight);
        }
        return IntoFun()(key);
    };

    /// <summary>Arriving in a parking garage of the city beside its gym doors, or out on a sidewalk if none is near.</summary>
    private Func<ulong, (int X, int Z, double Height)?> InFunGarage() => key =>
    {
        // (The usual reach: a cell filter would widen the search to 33 x 33 city cells, built on the main thread)
        if (layout.FindArrival(11, key, FunMascotDoorTile, spot: WorldLayout.IsOpenArrivalFloor) is { } a
            && layout.FeatureBeside(a.X, a.Z, FunMascotDoorTile) != null)
            return (a.X, a.Z, StandHeight);
        return In(11)(key);
    };

    /// <summary>Surfacing beside the ball pit in the funhouse castle on Level 94's glass mountain (or anywhere in 94 if it cannot be found).</summary>
    private Func<ulong, (int X, int Z, double Height)?> InCastleBallPit() => key =>
    {
        var castle = (WorldLayout.MacroOf(layout.MotionOriginX), WorldLayout.MacroOf(layout.MotionOriginZ));
        if (layout.FindArrival(WorldLayout.Motion, key, t => t.Variant == Worldgen.Props.BallPit, checkEscape: false, near: castle,
                spot: t => t.Kind == TileKind.Floor && !t.Sealed && t.Variant == 0 && t.Under == 0 && t.Stair == 0 && t.Zone == 3) is { } a)
            return (a.X, a.Z, layout.ArrivalHeight(a.X, a.Z));
        return In(WorldLayout.Motion)(key);
    };
}
