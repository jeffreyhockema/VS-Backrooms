using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 52, "The Greenfield Campus"'s thresholds in the game (experimental, kept as level 23): nothing, it has none; arrivals face into the open.
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    private void L52Arriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    /// <summary>
    /// The way someone put down in the level at (x, z) faces: the cardinal heading with the longest clear run (up to 40
    /// blocks), so a corridor is looked along and a lawn across, never a wall point-blank; null where nothing is open.
    /// </summary>
    private float? L52ArrivalYaw(int x, int z)
    {
        int best = 0;
        float yaw = 0;
        Tile here = layout.TileAt(x, z);
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            int run = 0;
            while (run < 40)
            {
                Tile t = layout.TileAt(x + dx * (run + 1), z + dz * (run + 1));
                if (t.Level != WorldLayout.Level52 || t.Kind is not (TileKind.Floor or TileKind.Doorway) || t.Variant != 0 || t.Height > here.Height + 1) break;
                run++;
            }
            // A player looks along (sin yaw, cos yaw)
            if (run > best) { best = run; yaw = (float)System.Math.Atan2(dx, dz); }
        }
        return best > 0 ? yaw : null;
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L52Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L52MayPass(IServerPlayer player, Passage passage) => true;
}
