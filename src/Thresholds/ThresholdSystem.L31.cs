using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 31, "Roller Rink"'s thresholds in the game (experimental, kept as level 24): nothing, it has none.
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    /// <remarks>They are turned to look along the longest open way from where they stand (down a hall, across a rink),
    /// not at the wall beside them, once they are there.</remarks>
    private void L31Arriving(IServerPlayer player, Link link, ref double drop)
    {
        int x = (int)Math.Floor(link.X), z = (int)Math.Floor(link.Z);
        int best = 0;
        float yaw = 0;
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            int run = 0;
            while (run < 40)
            {
                Tile t = layout.TileAt(x + dx * (run + 1), z + dz * (run + 1));
                if (t.Level != WorldLayout.Level31 || t.Kind is not (TileKind.Floor or TileKind.Doorway) || t.Variant == WorldLayout.L31Props.Dasher) break;
                run++;
            }
            // (a player looks along (sin yaw, cos yaw))
            if (run > best) { best = run; yaw = (float)Math.Atan2(dx, dz); }
        }
        if (best < 3) return;
        long until = sapi.World.ElapsedMilliseconds + 20000;
        void Turn(float dt)
        {
            EntityPlayer e = player.Entity;
            if (e == null || sapi.World.ElapsedMilliseconds > until) return;
            if (Math.Abs(e.Pos.X - link.X) < 1.5 && Math.Abs(e.Pos.Z - link.Z) < 1.5) Face(player, yaw);
            else sapi.Event.RegisterCallback(Turn, 250);
        }
        sapi.Event.RegisterCallback(Turn, 250);
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L31Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L31MayPass(IServerPlayer player, Passage passage) => true;
}
