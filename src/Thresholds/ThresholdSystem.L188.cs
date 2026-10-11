using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 188, "The Courtyard of Windows"'s thresholds in the game (kept as level 20). This file is the level's own; see
/// docs/new-levels/CONTRACT.md.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>
    /// Someone is about to be put down in the level at <paramref name="link"/>: raise <paramref name="drop"/> to drop
    /// them from above (as Motion does), or do anything else the arrival needs. Coming back from elsewhere beside a fire
    /// door (the way back from wherever it opened onto), the door bangs shut behind them.
    /// </summary>
    private void L188Arriving(IServerPlayer player, Link link, ref double drop)
    {
        // (Before the teleport: the player still stands where they came from)
        EntityPlayer entity = player.Entity;
        if (entity == null || layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z))) == WorldLayout.Level188) return;
        int bx = (int)Math.Floor(link.X) - layout.L188BuildX0, bz = (int)Math.Floor(link.Z) - layout.L188BuildZ0;
        foreach (var (fx, fz, _) in WorldLayout.L188FireDoors)
            if (Math.Abs(bx - fx) <= 3 && Math.Abs(bz - fz) <= 3)
            {
                player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:l188-fireexit-arrive"), EnumChatType.Notification);
                return;
            }
    }

    /// <summary>
    /// Just before someone going through any threshold (walked, used, an elevator's riders one by one) is put down at
    /// <paramref name="destination"/>: return somewhere else to send them there instead, or null to leave it be. Asked
    /// for every arrival in every level, so answer only for the level's own cases. The network's link is unchanged.
    /// </summary>
    private Link? L188Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now (Motion's gates open only at twilight).</summary>
    private bool L188MayPass(IServerPlayer player, Passage passage) => true;
}
