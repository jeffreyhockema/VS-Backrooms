using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 23, "Petrified Garden"'s thresholds in the game (experimental, kept as level 28): nothing, it has none.
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>
    /// Someone is about to be put down in the level at <paramref name="link"/>: they face the most open way among the
    /// eight round them (the longest run of open forest floor, up to 32 blocks), not the trunk beside them.
    /// </summary>
    private void L23Arriving(IServerPlayer player, Link link, ref double drop)
    {
        int x = (int)System.Math.Floor(link.X), z = (int)System.Math.Floor(link.Z);
        int best = 0;
        float yaw = 0;
        for (int k = 0; k < 8; k++)
        {
            double a = k * System.Math.PI / 4, sx = System.Math.Sin(a), sz = System.Math.Cos(a);
            int run = 0;
            while (run < 32)
            {
                Tile t = layout.TileAt((int)System.Math.Floor(x + 0.5 + sx * (run + 1)), (int)System.Math.Floor(z + 0.5 + sz * (run + 1)));
                if (t.Level != WorldLayout.Level23 || t.Kind != TileKind.Floor) break;
                run++;
            }
            // (A player looks along (sin yaw, cos yaw))
            if (run > best) { best = run; yaw = (float)a; }
        }
        if (best == 0) return;
        Face(player, yaw);
        // (Again once they are down, in case the client took the first before the move)
        sapi.Event.RegisterCallback(_ => Face(player, yaw), 1500);
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L23Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L23MayPass(IServerPlayer player, Passage passage) => true;
}
