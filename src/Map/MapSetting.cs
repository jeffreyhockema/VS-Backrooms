using Vintagestory.API.Datastructures;

namespace Backrooms.Map;

/// <summary>
/// The world setting "backroomsMap": how much the map helps. Seen areas (the default, and what worlds made before the
/// setting have) is the map as designed: it fills in with what you have seen and the Backrooms mark the ways you took
/// and the places you were told of. No waypoints keeps the map but marks nothing for you (nor does vanilla's death
/// waypoint: <see cref="BackroomsMapSystem"/> turns off "allowDeathwaypointing"). None takes the map away
/// altogether: <see cref="BackroomsMapSystem"/> turns off vanilla's "allowMap" for the world, which takes away the
/// map, the minimap, their keys and the waypoint commands, and chalk is a little easier to find.
/// The world config is sent to clients, so both sides read the setting from it.
///
/// A player granted vanilla's "allowMap" privilege still has the map in a None world (vanilla's
/// WorldMapManager.mapAllowedClient), and it fills in for them, but the Backrooms go by the world: no waypoints, the
/// no-map tutorial step, directions told in chat. That is on purpose: with "allowMap" off in the world config vanilla
/// refuses every /waypoint command, which the map's own add, edit and delete go through, so waypoints made for that
/// player could never be edited or removed. The privilege is a view of the map, not the map setting.
/// </summary>
public static class MapSetting
{
    public const string Code = "backroomsMap";

    public enum Mode { Seen, NoWaypoints, None }

    public static Mode Of(ITreeAttribute config) => config?.GetString(Code, "seen") switch
    {
        "nowaypoints" => Mode.NoWaypoints,
        "none" => Mode.None,
        _ => Mode.Seen,
    };

    /// <summary>Whether this world has a map at all (vanilla's own "allowMap", which None turns off).</summary>
    public static bool HasMap(ITreeAttribute config) => Of(config) != Mode.None && config.GetBool("allowMap", true);

    /// <summary>Whether the Backrooms put waypoints on players' maps: only with the full map.</summary>
    public static bool Waypoints(ITreeAttribute config) => Of(config) == Mode.Seen && HasMap(config);
}
