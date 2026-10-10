using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level Fun's thresholds in the game (kept as level 15). This file is the level's own; see
/// docs/new-levels/CONTRACT.md.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>
    /// Someone is about to be put down in the level at <paramref name="link"/>: raise <paramref name="drop"/> to drop
    /// them from above (as Motion does), or do anything else the arrival needs.
    /// </summary>
    private void FunArriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    /// <summary>
    /// Just before someone going through any threshold (walked, used, an elevator's riders one by one) is put down at
    /// <paramref name="destination"/>: return somewhere else to send them there instead, or null to leave it be. Asked
    /// for every arrival in every level, so answer only for the level's own cases. The network's link is unchanged.
    /// </summary>
    private Link? FunRedirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now (Motion's gates open only at twilight).</summary>
    private bool FunMayPass(IServerPlayer player, Passage passage) => true;
}
