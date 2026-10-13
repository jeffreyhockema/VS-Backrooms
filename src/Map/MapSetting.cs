using Vintagestory.API.Datastructures;

namespace Backrooms.Map;

/// <summary>
/// The world setting "backroomsMap": how much the map helps. Seen areas (the default, and what worlds made before the
/// setting have) is the map as designed: it fills in with what you have seen and the Backrooms mark the ways you took
/// and the places you were told of. No waypoints keeps the map but marks nothing for you. None takes the map away
/// altogether: <see cref="BackroomsMapSystem"/> turns off vanilla's "allowMap" for the world, which takes away the
/// map, the minimap, their keys and the waypoint commands, and chalk is a little easier to find.
/// The world config is sent to clients, so both sides read the setting from it.
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
