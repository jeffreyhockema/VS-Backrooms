using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 120, "Broken Servos"'s thresholds in the game (experimental, kept as level 26): it has none in
/// or out. Its pockets (a booted terminal into a White Void or a Pitch-Black Hallway, a broken window back) are inside the
/// level and are L120System's; this only lends them the way everyone is carried (the fade, the loading, the arrival).
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    private void L120Arriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L120Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L120MayPass(IServerPlayer player, Passage passage) => true;

    /// <summary>
    /// Carries a player to a place in Level 120 (into a pocket, or back out of one) the way a threshold would: the screen
    /// goes dark, the place is loaded, they are put down. Nothing is written down: this is not a threshold. False if not.
    /// </summary>
    public bool L120Carry(IServerPlayer player, double x, double y, double z, string style = null) =>
        layout != null && player.Entity != null && Arrive(player, new Link(x, y, z, false), style);
}
