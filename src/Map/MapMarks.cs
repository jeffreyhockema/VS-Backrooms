using System.Linq;
using Backrooms.Notes;
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
/// None are made where the map setting says not (<see cref="MapSetting"/>).
/// </summary>
public static class MapMarks
{
    /// <summary>Thresholds and gates: a pale violet.</summary>
    public static readonly int WayColor = ColorUtil.ColorFromRgba(196, 150, 230, 255);

    /// <summary>What a note pointed to: the yellow of old paper.</summary>
    public static readonly int NoteColor = ColorUtil.ColorFromRgba(232, 214, 140, 255);

    /// <summary>
    /// Adds a waypoint for a player unless they already have one within <paramref name="near"/> blocks of the spot.
    /// Returns whether one was added. In a world whose map setting makes no waypoints, the player is told in chat
    /// which way the spot lies instead, if it is not where they stand, unless <paramref name="tell"/> is false (for
    /// marks the caller has its own words for, or where the player has just been).
    /// </summary>
    public static bool Add(ICoreServerAPI sapi, IServerPlayer player, Vec3d at, string title, string icon, int color, double near, bool tell = true)
    {
        if (player == null) return false;
        if (!MapSetting.Waypoints(sapi.World.Config))
        {
            if (tell && player.Entity != null)
            {
                double dx = at.X - player.Entity.Pos.X, dz = at.Z - player.Entity.Pos.Z;
                if (dx * dx + dz * dz >= near * near)
                    player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:mapmark-told", title,
                        Lang.Get("backrooms:dir-" + MarkResolver.Direction(dx, dz)), MarkResolver.Paces(dx, dz)), EnumChatType.Notification);
            }
            return false;
        }
        WaypointMapLayer layer = sapi.ModLoader.GetModSystem<WorldMapManager>()?.MapLayers.OfType<WaypointMapLayer>().FirstOrDefault();
        if (layer == null) return false;
        // (Horizontally only: a note marks at the reader's height, so on a level of several storeys the same place read
        // from another floor would otherwise be marked twice)
        foreach (Waypoint w in layer.Waypoints)
        {
            double dx = w.Position.X - at.X, dz = w.Position.Z - at.Z;
            if (w.OwningPlayerUid == player.PlayerUID && dx * dx + dz * dz < near * near) return false;
        }
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
        // Levels 14 to 20 (Level !, Fun, The End, The Hub, 974, 3999, 188) have names of their own: levelname-14 to levelname-20
        if (level >= WorldLayout.RunLevel && level <= WorldLayout.Level188) return Lang.Get("backrooms:levelname-" + level);
        return Lang.Get("backrooms:levelname", WorldLayout.DisplayNumber(level));
    }
}
