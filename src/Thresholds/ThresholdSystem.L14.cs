using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 14, "The Hospital"'s thresholds in the game (experimental, kept as level 29;
/// ThresholdNetwork.L14.cs): arrivals in a reception room turned to face into the room, away from the stained-glass revolving
/// door; and the floor that gives way (a crumbling, the floor's dust where it went, and a fall out of the sky onto the
/// Redlands that hurts as it would but never kills). The doors are used as any door is and need nothing here. This file is
/// the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>The block code of the floor that gives way (tools/gen_14.py).</summary>
    private const string L14SaggingCode = "l14-floor-sagging";

    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    /// <remarks>
    /// In a reception room they face into it, away from the revolving door at its back (the door's front row faces into the
    /// room): the desk, the chairs, the way out. The turn waits until they are down.
    /// </remarks>
    private void L14Arriving(IServerPlayer player, Link link, ref double drop)
    {
        int ax = (int)Math.Floor(link.X), az = (int)Math.Floor(link.Z);
        if (WorldLayout.L14ZoneOf(layout.TileAt(ax, az)) != WorldLayout.L14Zone.Reception) return;
        long best = long.MaxValue;
        ArchPier? into = null;
        for (int dz = -14; dz <= 14; dz++)
            for (int dx = -14; dx <= 14; dx++)
            {
                Tile t = layout.TileAt(ax + dx, az + dz);
                if (t.Level != WorldLayout.Level14 || t.Kind != TileKind.Floor || t.Variant != Backrooms.Worldgen.Props.L14Revolving) continue;
                long d = (long)dx * dx + (long)dz * dz;
                if (d < best) { best = d; into = t.Pier; }
            }
        if (into is not { } face) return;
        var (fx, fz) = face switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
        // (A player looks along (sin yaw, cos yaw))
        float yaw = (float)Math.Atan2(fx, fz);
        int tries = 0;
        void Check(float _)
        {
            if (player.Entity == null || ++tries > 40) return;
            if (player.Entity.Pos.SquareDistanceTo(link.X, player.Entity.Pos.Y, link.Z) < 2.25) Face(player, yaw);
            else sapi.Event.RegisterCallback(Check, 250);
        }
        sapi.Event.RegisterCallback(Check, 250);
    }

    /// <summary>
    /// Just before any arrival anywhere: somewhere else to send them, or null. Never anywhere else for Level 14's; but the
    /// floor that gives way goes here, where they still stand on it: a crumbling, its dust, and a grace on the fall (the
    /// arrival is in the air over the Redlands: ThresholdNetwork.L14CollapseDrop).
    /// </summary>
    private Link? L14Redirect(IServerPlayer player, Passage passage, Link destination)
    {
        if (passage.Message != ThresholdNetwork.L14CollapseMessage || player.Entity == null) return null;
        EntityPos pos = player.Entity.Pos;
        // (The grace lasts through the loading and the fall: they land hurt but alive)
        player.Entity.Attributes.SetLong(FallGraceKey, sapi.World.ElapsedMilliseconds + FallGraceMaxMs);
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        var floor = new BlockPos(x, geometry.FloorFor(WorldLayout.Level14), z);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/rockslide"), pos.X, pos.Y, pos.Z, null, randomizePitch: true, range: 24);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/rock-break-pickaxe"), pos.X, pos.Y, pos.Z, null, randomizePitch: true, range: 16);
        try { sapi.World.SpawnCubeParticles(floor, new Vec3d(x + 0.5, floor.Y + 1.05, z + 0.5), 1.5f, 40, 0.8f); }
        catch (Exception ex) { sapi.Logger.Debug("[backrooms] l14: no dust at the floor that gave way ({0})", ex.Message); }
        return null;
    }

    /// <summary>
    /// Whether a threshold someone has walked into lets them through now: the floor that gives way only where its sagging floor
    /// is still there (a stretch of the level made before it was laid out, or a floor dug away and replaced, holds).
    /// </summary>
    private bool L14MayPass(IServerPlayer player, Passage passage)
    {
        if (passage.Message != ThresholdNetwork.L14CollapseMessage) return true;
        EntityPos pos = player.Entity.Pos;
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        // (The layout's, or in a world made before layout 16 one the pre-releases' rate laid and the quarter dropped: its block decides)
        if (!network.L14CollapseAt(x, z)) return false;
        Block on = sapi.World.BlockAccessor.GetBlock(new BlockPos(x, geometry.FloorFor(WorldLayout.Level14), z));
        return on.Code?.Domain == "backrooms" && on.Code.Path == L14SaggingCode;
    }
}
