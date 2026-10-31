using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 36, "Airport"'s thresholds in the game (experimental, kept as level 25): nothing, it has none.
/// This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    private void L36Arriving(IServerPlayer player, Link link, ref double drop)
    {
        // Put down on a carousel (round 2): facing east, out over the claim hall, rather than wherever they last looked
        // (the baggage wall at their back)
        Face(player, Vintagestory.API.MathTools.GameMath.PIHALF);
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L36Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L36MayPass(IServerPlayer player, Passage passage) => true;
}
