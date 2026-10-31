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
    /// <summary>Ways and places of the Hub's Tower that lead to no one level: a pale violet (what every way was before 0.610.3).</summary>
    public static readonly int WayColor = ColorUtil.ColorFromRgba(196, 150, 230, 255);

    /// <summary>A way that stays inside its level (stairs or a passage to another part of it): grey, under a ladder, so it does not crowd the ways out.</summary>
    public static readonly int InLevelColor = ColorUtil.ColorFromRgba(132, 132, 130, 255);

    /// <summary>The icon of a way that stays inside its level.</summary>
    public const string InLevelIcon = "ladder";

    /// <summary>
    /// The colour of a way by the level it leads to, by level id (0-11, then 37, 94, !, Fun, The End, the Hub, 974, 3999, 188),
    /// so every way to one level is one colour on the map. Kelly's colours of greatest contrast, without the greys (taken by
    /// <see cref="InLevelColor"/>) and black (lost on a dark floor), with a teal for the Hub; picked to suit the level where one could.
    /// </summary>
    private static readonly int[] LevelColors =
    {
        Rgb(0xF3C300), // 0: the Lobby's yellow
        Rgb(0xF38400), // 1: orange
        Rgb(0xE25822), // 2: reddish orange, the pipes' heat
        Rgb(0xBE0032), // 3: red
        Rgb(0xC2B280), // 4: buff, the offices
        Rgb(0x882D17), // 5: reddish brown, the hotel
        Rgb(0xF2F3F4), // 6: white
        Rgb(0x0067A5), // 7: blue, the sea
        Rgb(0x2B3D26), // 8: olive, the caves
        Rgb(0x604E97), // 9: violet, the night
        Rgb(0xDCD300), // 10: greenish yellow, the wheat
        Rgb(0x875692), // 11: purple, the city
        Rgb(0xA1CAF1), // 37: light blue, the pools
        Rgb(0x008856), // 94: green, the hills
        Rgb(0xB3446C), // !: purplish red
        Rgb(0xE68FAC), // Fun: pink
        Rgb(0x654522), // The End: yellowish brown, the shelves
        Rgb(0x2CA6A4), // the Hub: teal
        Rgb(0xF99379), // 974: yellowish pink
        Rgb(0x8DB600), // 3999: yellow green
        Rgb(0xF6A600), // 188: orange yellow, the lit windows
    };

    private static int Rgb(int rgb) => ColorUtil.ColorFromRgba((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF, 255);

    /// <summary>The colour of a way to <paramref name="level"/> (a level id).</summary>
    public static int WayColorTo(int level) => level >= 0 && level < LevelColors.Length ? LevelColors[level] : WayColor;

    /// <summary>The colour of a way to the level at x, z.</summary>
    public static int WayColorTo(WorldLayout layout, double x, double z) =>
        WayColorTo(layout.LevelAt(WorldLayout.MacroOf((int)System.Math.Floor(x)), WorldLayout.MacroOf((int)System.Math.Floor(z))));

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
