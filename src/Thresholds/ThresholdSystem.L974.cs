using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 974's thresholds in the game (kept as level 18): Kitty's detour into a wanderer's own
/// house, arriving there, and waking from it. The rules themselves are <see cref="Regions.L974System"/>'s. This file is
/// the level's own; see docs/design/new-levels/CONTRACT.md.
/// </summary>
public partial class ThresholdSystem
{
    private Regions.L974System l974;

    private Regions.L974System L974Rules => l974 ??= sapi.ModLoader.GetModSystem<Regions.L974System>();

    /// <summary>Someone is about to be put down in the level: their visit begins.</summary>
    private void L974Arriving(IServerPlayer player, Link link, ref double drop) => L974Rules?.Arriving(player, link);

    /// <summary>
    /// Just before anyone going through any threshold arrives: Kitty may take them to their own house instead (and
    /// whoever arrives in the level at all, by the Hub's pink door, is put in their own house). The network's link is
    /// unchanged.
    /// </summary>
    private Link? L974Redirect(IServerPlayer player, Passage passage, Link destination) => L974Rules?.Detour(player, passage, destination);

    private bool L974MayPass(IServerPlayer player, Passage passage) => true;

    /// <summary>Wakes someone who has given Kitty its gift: one-way, to the safe place fixed for the house (<see cref="ThresholdNetwork.KittyWake"/>).</summary>
    public bool L974Wake(IServerPlayer player, (int X, int Z) house)
    {
        if (network == null) return false;
        Passage passage = network.KittyWake(house);
        return Go(player, passage, network.Take(passage, null));
    }

    /// <summary>Where a house's wake-up leads (fixing it, if nobody has woken from there yet).</summary>
    public Link? L974WakeLink((int X, int Z) house) => network?.Take(network.KittyWake(house), null);
}
