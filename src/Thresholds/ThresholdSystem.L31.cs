using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 31, "Roller Rink"'s thresholds in the game (experimental, kept as level 24; the ways themselves are
/// in ThresholdNetwork.L31.cs). Whoever arrives is turned to the longest view; whoever leaves the level with the rink's skates
/// on them (the Coach's, on loan) is not let go with them: they noclip into Level 0 instead, without the skates (Fandom), and
/// so does a thief who walks out of Skate Rental with a pair from the cubbies (<see cref="L31Steal"/>). This file is the
/// level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    /// <remarks>They are turned to look along the longest open way from where they stand (down a hall, across a rink),
    /// not at the wall beside them, once they are there.</remarks>
    private void L31Arriving(IServerPlayer player, Link link, ref double drop)
    {
        int x = (int)Math.Floor(link.X), z = (int)Math.Floor(link.Z);
        int best = 0;
        float yaw = 0;
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            int run = 0;
            while (run < 40)
            {
                Tile t = layout.TileAt(x + dx * (run + 1), z + dz * (run + 1));
                if (t.Level != WorldLayout.Level31 || t.Kind is not (TileKind.Floor or TileKind.Doorway) || t.Variant == WorldLayout.L31Props.Dasher) break;
                run++;
            }
            // (a player looks along (sin yaw, cos yaw))
            if (run > best) { best = run; yaw = (float)Math.Atan2(dx, dz); }
        }
        if (best < 3) return;
        long until = sapi.World.ElapsedMilliseconds + 20000;
        void Turn(float dt)
        {
            EntityPlayer e = player.Entity;
            if (e == null || sapi.World.ElapsedMilliseconds > until) return;
            if (Math.Abs(e.Pos.X - link.X) < 1.5 && Math.Abs(e.Pos.Z - link.Z) < 1.5) Face(player, yaw);
            else sapi.Event.RegisterCallback(Turn, 250);
        }
        sapi.Event.RegisterCallback(Turn, 250);
    }

    /// <summary>
    /// Just before any arrival anywhere: whoever goes out of the level by any way at all with the rink's skates about them
    /// loses the skates and comes out in Level 0 instead (the same place for that way every time); null for anyone else.
    /// </summary>
    private Link? L31Redirect(IServerPlayer player, Passage passage, Link destination)
    {
        int from = layout.LevelAt(WorldLayout.MacroOf(passage.Source.X), WorldLayout.MacroOf(passage.Source.Z));
        int to = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(destination.X)), WorldLayout.MacroOf((int)Math.Floor(destination.Z)));
        if (from != WorldLayout.Level31 || to == WorldLayout.Level31 || !Regions.L31System.TakeSkates(player)) return null;
        passage.Message = "backrooms:l31-skates-noclip";
        if (to == 0) return null;
        ulong key = Hashing.Mix((ulong)(uint)passage.Source.X << 32 | (uint)passage.Source.Z) ^ 0x24C7;
        if (layout.FindArrival(0, key) is not { } a) return null;
        return new Link(a.X + 0.5, geometry.FloorFor(0) + layout.ArrivalHeight(a.X, a.Z), a.Z + 0.5, false);
    }

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L31MayPass(IServerPlayer player, Passage passage) => true;

    /// <summary>
    /// A thief walks out of Skate Rental with a pair from the cubbies (Regions.L31System): "an immediate noclip to Level 0,
    /// without skates" (Fandom). False if they could not be moved just now.
    /// </summary>
    public bool L31Steal(IServerPlayer player)
    {
        if (network == null || player.Entity == null || !CanTravel(player) || IsBusy(player)) return false;
        EntityPos at = player.Entity.Pos;
        Passage passage = network.L31SkatesNoclip(((int)Math.Floor(at.X), (int)Math.Floor(at.Z)));
        return Go(player, passage, network.Take(passage, null), "plain");
    }
}
