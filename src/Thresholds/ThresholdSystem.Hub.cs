using Backrooms.Regions;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round The Hub's thresholds in the game (kept as level 17): its carved doors, which need to know who is
/// using them and what they carry. This file is the level's own; see docs/new-levels/CONTRACT.md.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>
    /// Someone uses one of the Hub's carved doors. Canon's three (Level 1, Level 11, and 178, here the Snackrooms) open
    /// for anyone; the pink ribbon door to Level 974 for someone carrying something cute; every other level's door only
    /// to that level's key, which turns three times and is gone. The doors to levels nobody can reach never open. Every
    /// carved door is one way: the doorway is gone behind you. The Tower's own doors come here too: its ten ways in and
    /// out (<see cref="UseTowerDoor"/>), and the forbidden ones up the stair, which never open.
    /// </summary>
    public void UseHubDoor(IServerPlayer player, BlockPos pos)
    {
        if (network == null || IsBusy(player) || !CanTravel(player)) return;
        void Refuse(string message, int busyMs)
        {
            Play(pos, "game:sounds/effect/latch");
            player.SendIngameError("backrooms-hubdoor", Lang.Get(message));
            busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + busyMs;
        }

        // The Tower's doors up the stair and round the hall never open (known by their block: they stand in the Tower's wall,
        // on no door tile of the layout)
        if (sapi.World.BlockAccessor.GetBlock(pos).Code?.Path.StartsWith(HubSystem.ForbiddenDoorPrefix) == true)
        {
            Refuse("backrooms:hub-tower-forbidden", 800);
            return;
        }
        // The Tower's ornate doors: in once, and out again
        if (layout.TileAt(pos.X, pos.Z) is { Kind: TileKind.Door, Pattern: WallPattern.HubOrnate } && layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)) == WorldLayout.Hub)
        {
            UseTowerDoor(player, pos, Refuse);
            return;
        }
        if (layout.HubDoorLevelAt(pos.X, pos.Z) is not { } target)
        {
            Refuse("backrooms:door-locked", 800);
            return;
        }
        if (target < 0)
        {
            Refuse("backrooms:hub-door-dead", 800);
            return;
        }
        ItemSlot key = null;
        if (target == WorldLayout.Level974)
        {
            if (!HubSystem.CarriesSomethingCute(player))
            {
                Refuse("backrooms:hub-pinkdoor-refused", 800);
                return;
            }
        }
        else if (!WorldLayout.HubDoorOpen(target))
        {
            key = HubSystem.FindKey(player, target);
            if (key == null)
            {
                Refuse("backrooms:hub-door-locked", 800);
                return;
            }
        }

        Passage passage = network.HubDoor(pos.X, pos.Z, target);
        Link? destination = network.Take(passage, null);
        if (destination == null)
        {
            Refuse("backrooms:thinspot-nowhere", 2000);
            return;
        }
        if (key != null)
        {
            // Three full turns, and the key is gone with the doorway
            key.TakeOut(1);
            key.MarkDirty();
            Play(pos, "backrooms:sounds/effect/hub/keyturn");
            player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:hub-door-turn"), EnumChatType.Notification);
        }
        // The ribbon comes undone, or the slab grinds aside
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get(target == WorldLayout.Level974 ? "backrooms:hub-pinkdoor-open" : "backrooms:hub-door-open"),
            EnumChatType.Notification);
        // (Level 3999's door lets you out beside one of its STAFF ONLY doors, so there is a door behind you after all)
        if (target == WorldLayout.Level3999) passage.Message = "backrooms:l3999-arrive-staff";
        if (passage.Sound != null) Play(pos, passage.Sound);
        Go(player, passage, destination);
    }

    /// <summary>
    /// An ornate door of the Tower's. From outside it lets you into the rotunda, unless you have been in before (canon: no
    /// one is let in twice); from inside it lets you out onto its approach. Not a threshold of the network: the door is
    /// the way in and out of the one building.
    /// </summary>
    private void UseTowerDoor(IServerPlayer player, BlockPos pos, System.Action<string, int> refuse)
    {
        int ox = layout.HubOriginX, oz = layout.HubOriginZ;
        double angle = System.Math.Atan2(pos.Z - oz, pos.X - ox);
        int k = 0;
        double best = double.MaxValue;
        for (int i = 0; i < 10; i++)
        {
            var (ux, uz) = layout.HubSpokeDirection(i);
            double d = System.Math.Abs(System.Math.IEEERemainder(angle - System.Math.Atan2(uz, ux), 2 * System.Math.PI));
            if (d < best) { best = d; k = i; }
        }
        bool inside = layout.InHubTower(player.Entity.Pos.X, player.Entity.Pos.Z);
        if (!inside && HubSystem.TowerVisited(player))
        {
            refuse("backrooms:hub-tower-refused", 1500);
            return;
        }
        var (dx, dz) = layout.HubSpokeDirection(k);
        double r = inside ? 28.5 : 15;
        Play(pos, "game:sounds/block/door");
        busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + CooldownMs;
        player.Entity.TeleportToDouble(ox + 0.5 + dx * r, geometry.FloorFor(WorldLayout.Hub) + 1.05, oz + 0.5 + dz * r);
    }

    /// <summary>
    /// Someone is about to be put down in the level at <paramref name="link"/>: raise <paramref name="drop"/> to drop
    /// them from above (as Motion does), or do anything else the arrival needs.
    /// </summary>
    private void HubArriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    /// <summary>
    /// The way someone put down in the Hub at (x, z) faces: the cardinal heading with the longest open run of the tunnel
    /// (up to 48 blocks), which on a sidewalk is along the road; null where no heading is open at all.
    /// </summary>
    private float? HubArrivalYaw(int x, int z)
    {
        int best = 0;
        float yaw = 0;
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            int run = 0;
            while (run < 48)
            {
                Tile t = layout.TileAt(x + dx * (run + 1), z + dz * (run + 1));
                if (t.Level != WorldLayout.Hub || t.Kind is not (TileKind.Floor or TileKind.Doorway)) break;
                run++;
            }
            // A player looks along (sin yaw, cos yaw)
            if (run > best) { best = run; yaw = (float)System.Math.Atan2(dx, dz); }
        }
        return best > 0 ? yaw : null;
    }

    /// <summary>
    /// Just before someone going through any threshold (walked, used, an elevator's riders one by one) is put down at
    /// <paramref name="destination"/>: return somewhere else to send them there instead, or null to leave it be. Asked
    /// for every arrival in every level, so answer only for the level's own cases. The network's link is unchanged.
    /// </summary>
    private Link? HubRedirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now (Motion's gates open only at twilight).</summary>
    private bool HubMayPass(IServerPlayer player, Passage passage) => true;
}
