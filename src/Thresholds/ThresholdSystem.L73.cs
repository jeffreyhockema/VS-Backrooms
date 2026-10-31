using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 73, "The Redlands"'s thresholds in the game (experimental, kept as level 21): nothing, it has none.
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    private void L73Arriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    /// <summary>The way someone put down on the island faces: toward the castle's gate (a player looks along sin yaw, cos yaw).</summary>
    private float? L73ArrivalYaw(int x, int z)
    {
        var (gx, gz) = layout.L73Gate;
        return (float)System.Math.Atan2(gx + 0.5 - x, gz + 0.5 - z);
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L73Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L73MayPass(IServerPlayer player, Passage passage) => true;
}
