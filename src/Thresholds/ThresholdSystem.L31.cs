using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 31, "Roller Rink"'s thresholds in the game (experimental, kept as level 24): nothing, it has none.
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    private void L31Arriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L31Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L31MayPass(IServerPlayer player, Passage passage) => true;
}
