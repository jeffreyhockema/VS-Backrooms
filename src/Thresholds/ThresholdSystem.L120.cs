using System;
using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 120, "Broken Servos"'s thresholds in the game (experimental, kept as level 26). Its ways in and out
/// are doors, used as any door is (ThresholdNetwork.L120.cs: the door marked SERVER ROOM in Level 4, the doors back); they
/// need nothing here but the turn on arriving. Its pockets (a booted terminal into a White Void or a Pitch-Black Hallway, a
/// broken window back) are inside the level and are L120System's; this only lends them the way everyone is carried (the
/// fade, the loading, the arrival). This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    /// <remarks>
    /// They face the way the floor runs furthest (up to 24 blocks: down a passage, along an aisle or a hallway's lane, into
    /// a void's room) rather than whatever wall was before them. The turn waits until they are down.
    /// </remarks>
    private void L120Arriving(IServerPlayer player, Link link, ref double drop)
    {
        int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z), best = 0;
        float yaw = 0;
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            int run = 0;
            while (run < 24)
            {
                Tile t = layout.TileAt(ax + dx * (run + 1), az + dz * (run + 1));
                if (t.Level != WorldLayout.Level120 || t.Kind is not (TileKind.Floor or TileKind.Doorway) || (t.Kind != TileKind.Doorway && !WorldLayout.IsWalkThroughProp(t.Variant)) || t.SupplyBox || t.Stack > 0) break;
                run++;
            }
            // (A player looks along (sin yaw, cos yaw))
            if (run > best) { best = run; yaw = (float)Math.Atan2(dx, dz); }
        }
        if (best < 3) return;
        int tries = 0;
        void Check(float _)
        {
            if (player.Entity == null || ++tries > 40) return;
            if (player.Entity.Pos.SquareDistanceTo(link.X, player.Entity.Pos.Y, link.Z) < 2.25) Face(player, yaw);
            else sapi.Event.RegisterCallback(Check, 250);
        }
        sapi.Event.RegisterCallback(Check, 250);
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

    /// <summary>Whether the player could be carried now: playing, alive, not mid-teleport and not already in a passage (for other systems that start a trip of their own).</summary>
    public bool CanTravelNow(IServerPlayer player) => CanTravel(player) && !IsBusy(player);
}
