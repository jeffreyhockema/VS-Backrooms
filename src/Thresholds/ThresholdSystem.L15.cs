using System;
using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 15, "Futuristic Halls"'s thresholds in the game (experimental, kept as level 27): its ways in and out are in WorldLayout.Level15.Links.cs;
/// someone put down in it (a way in, the cheats menu, <c>/backrooms goto</c>) faces along the hall or corridor they arrive in.
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>: they face the longest way clear.</summary>
    private void L15Arriving(IServerPlayer player, Link link, ref double drop)
    {
        int x = (int)Math.Floor(link.X), z = (int)Math.Floor(link.Z), best = 0;
        float yaw = 0;
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            int run = 0;
            while (run < 40)
            {
                Tile t = layout.TileAt(x + dx * (run + 1), z + dz * (run + 1));
                if (t.Level != WorldLayout.Level15 || t.Kind is not (TileKind.Floor or TileKind.Doorway)) break;
                run++;
            }
            // A player looks along (sin yaw, cos yaw)
            if (run > best) { best = run; yaw = (float)Math.Atan2(dx, dz); }
        }
        if (best == 0) return;
        Face(player, yaw);
        // (Again once they are there, unless they have already moved off)
        double ax = link.X, az = link.Z;
        sapi.Event.RegisterCallback(_ =>
        {
            if (player.Entity is { } e && Math.Abs(e.Pos.X - ax) < 0.6 && Math.Abs(e.Pos.Z - az) < 0.6) Face(player, yaw);
        }, 1500);
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L15Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L15MayPass(IServerPlayer player, Passage passage) => true;
}
