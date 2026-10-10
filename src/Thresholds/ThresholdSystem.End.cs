using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round The End's thresholds in the game (kept as level 16). This file is the level's own; see
/// docs/new-levels/CONTRACT.md. <see cref="Regions.EndSystem"/> sends people through the thresholds that are not blocks
/// or tiles (a "=)" computer, a wall during a distortion) by <see cref="EndCarry"/>.
/// </summary>
public partial class ThresholdSystem
{
    private void EndArriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    private Link? EndRedirect(IServerPlayer player, Passage passage, Link destination) => null;

    private bool EndMayPass(IServerPlayer player, Passage passage) => true;

    /// <summary>Whether one of The End's EXIT doors opens (for the computers' and the catalogue cards' map marks).</summary>
    public bool EndExitOpens(int x, int z) => network != null && network.EndExitOpens(x, z);

    /// <summary>The passage behind a computer that says "=)" (null for an ordinary computer, or before the network is up).</summary>
    public Passage EndTerminal(int x, int z, bool central) => network?.EndTerminal(x, z, central);

    /// <summary>The passage through a department's walls during a distortion (null where its scene leads nowhere).</summary>
    public Passage EndDistortion(int di, int dj) => network?.EndDistortion(di, dj);

    /// <summary>
    /// Carries a player through one of The End's passages that is not a block or a tile: written down the first time,
    /// with a way back (a thin spot) if it is two-way. Returns whether they went.
    /// </summary>
    public bool EndCarry(IServerPlayer player, Passage passage)
    {
        if (network == null || passage == null || IsBusy(player) || !CanTravel(player)) return false;
        Link? destination = network.Take(passage, passage.TwoWay ? network.HomeBeside(passage.Source) : null);
        if (destination == null) return false;
        if (passage.Sound != null) Play(new Vintagestory.API.MathTools.BlockPos((int)player.Entity.Pos.X, (int)player.Entity.Pos.Y, (int)player.Entity.Pos.Z), passage.Sound);
        return Go(player, passage, destination);
    }
}
