using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 73, "The Redlands"'s thresholds in the game (experimental, kept as level 21): the ways in that are
/// not a step (the Gloom, Level 6's deepest dark), which Regions/L73System.Links.cs times and sends through here, and the north
/// door, which lets nobody through unless Coran has opened it. This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>: whatever night they slept under Coran's roof before is forgotten.</summary>
    private void L73Arriving(IServerPlayer player, Link link, ref double drop)
    {
        Regions.L73System.Server?.ForgetRest(player);
    }

    /// <summary>The way someone put down on the island faces: toward the castle's gate (a player looks along sin yaw, cos yaw).</summary>
    private float? L73ArrivalYaw(int x, int z)
    {
        var (gx, gz) = layout.L73Gate;
        return (float)System.Math.Atan2(gx + 0.5 - x, gz + 0.5 - z);
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L73Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now: the north door only while it stands open.</summary>
    private bool L73MayPass(IServerPlayer player, Passage passage) =>
        passage.Message != ThresholdNetwork.L73OutMessage || Regions.L73System.Server?.PosternOpen == true;

    /// <summary>
    /// Takes someone through one of the level's ways in that are lingered in rather than stepped through (L73System): "gloom"
    /// at the Gloom they stand in (x, z a block of it), "dark" from Level 6's deepest dark (x, z the cell). One way: out on the
    /// island, where that way always leads. False if it leads nowhere (or they cannot travel just now).
    /// </summary>
    public bool L73Take(IServerPlayer player, string way, int x, int z)
    {
        if (network == null || IsBusy(player) || !CanTravel(player)) return false;
        Passage passage = way == "gloom" ? network.L73Gloom(x, z) : way == "dark" ? network.L73Dark(x, z) : null;
        if (passage == null) return false;
        // (Just the fade: the dark closes over them, no step and no fall)
        return Go(player, passage, network.Take(passage, null), "plain");
    }

    /// <summary>Where the north door leads (written down the first time anyone asks), for the dev command; null if nowhere.</summary>
    public Link? L73OutLink() => network?.Take(network.L73OutPassage(), null);

    /// <summary>Where one of the ways in leads (written down the first time), for the dev command; null if nowhere.</summary>
    public Link? L73WayLink(string way, int x, int z)
    {
        if (network == null) return null;
        Passage passage = way == "gloom" ? network.L73Gloom(x, z) : way == "dark" ? network.L73Dark(x, z) : null;
        return passage == null ? null : network.Take(passage, null);
    }
}
