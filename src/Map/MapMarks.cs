using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Map;

/// <summary>
/// Waypoints the Backrooms puts on a player's map for them: the ways between levels they have been through, and the
/// places a wanderer's note told them of. Ordinary vanilla waypoints, so they can be renamed, recoloured or deleted.
/// </summary>
public static class MapMarks
{
    /// <summary>Thresholds and gates: a pale violet.</summary>
    public static readonly int WayColor = ColorUtil.ColorFromRgba(196, 150, 230, 255);

    /// <summary>What a note pointed to: the yellow of old paper.</summary>
    public static readonly int NoteColor = ColorUtil.ColorFromRgba(232, 214, 140, 255);

    /// <summary>
    /// Adds a waypoint for a player unless they already have one within <paramref name="near"/> blocks of the spot.
    /// Returns whether one was added.
    /// </summary>
    public static bool Add(ICoreServerAPI sapi, IServerPlayer player, Vec3d at, string title, string icon, int color, double near)
    {
        WaypointMapLayer layer = sapi.ModLoader.GetModSystem<WorldMapManager>()?.MapLayers.OfType<WaypointMapLayer>().FirstOrDefault();
        if (layer == null || player == null) return false;
        foreach (Waypoint w in layer.Waypoints)
            if (w.OwningPlayerUid == player.PlayerUID && w.Position.SquareDistanceTo(at) < near * near) return false;
        layer.AddWaypoint(new Waypoint
        {
            Position = at.Clone(),
            Title = title,
            Icon = icon,
            Color = color,
            OwningPlayerUid = player.PlayerUID,
        }, player);
        return true;
    }

    /// <summary>A level's name as the waypoints give it: "Level 3", "Level 6.1" for the Snackrooms, "Level 37" for the Poolrooms, "The Hub".</summary>
    public static string LevelName(WorldLayout layout, double x, double z)
    {
        int mx = WorldLayout.MacroOf((int)System.Math.Floor(x)), mz = WorldLayout.MacroOf((int)System.Math.Floor(z));
        int level = layout.LevelAt(mx, mz);
        if (level == 6 && layout.IsSnackrooms(mx, mz)) return Lang.Get("backrooms:levelname-6.1");
        if (level == WorldLayout.Poolrooms && layout.IsReservoir(mx, mz)) return Lang.Get("backrooms:levelname-37.1");
        // The five kept as 14-18 have names of their own ("The End", "The Hub"): levelname-14 to levelname-18
        if (level >= WorldLayout.RunLevel && level <= WorldLayout.Level188) return Lang.Get("backrooms:levelname-" + level);
        return Lang.Get("backrooms:levelname", WorldLayout.DisplayNumber(level));
    }
}
