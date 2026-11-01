using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round The Basement's thresholds in the game (experimental, kept as level 22; ThresholdNetwork.Basement.cs):
/// the floor giving way (a crumbling sound and the floor's dust where it went, the fall itself under the crack: several
/// tens of feet, which hurts as it would, but never kills), and the cracked patches of Level 2, which the walked
/// thresholds do not look at, on <see cref="Regions.BasementSystem"/>'s tick. This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>
    /// How far over the floor under the crack someone who fell through a cracked patch is put down: ten blocks and a bit
    /// of fall (Fandom: "often several tens of feet"), about six health's worth of fall damage, never a killing one
    /// (<see cref="FallGraceKey"/>).
    /// </summary>
    private const double BasementFallDrop = 10;

    /// <summary>The block code of the cracked patch's pieces (tools/gen_basement.py).</summary>
    private const string BasementCrackCode = "basement-floorcrack-";

    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    private void BasementArriving(IServerPlayer player, Link link, ref double drop)
    {
        // Through a cracked patch in another level's floor: put down high in the crack's shaft, to fall the rest of the way
        EntityPos pos = player.Entity.Pos;
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        Tile from = layout.TileAt(x, z);
        if (!WorldLayout.BasementCrackGives(from)) return;
        drop = BasementFallDrop;
        // (The grace lasts through the loading and the fall: they land hurt but alive)
        player.Entity.Attributes.SetLong(FallGraceKey, sapi.World.ElapsedMilliseconds + FallGraceMs + 20000);
        // The floor goes: a crumbling where they stood, and its dust
        var floor = new BlockPos(x, geometry.FloorFor(from.Level), z);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/rockslide"), pos.X, pos.Y, pos.Z, null, randomizePitch: true, range: 24);
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/rock-break-pickaxe"), pos.X, pos.Y, pos.Z, null, randomizePitch: true, range: 16);
        try { sapi.World.SpawnCubeParticles(floor, new Vec3d(x + 0.5, floor.Y + 1.05, z + 0.5), 1.5f, 40, 0.8f); }
        catch (Exception ex) { sapi.Logger.Debug("[backrooms] basement: no dust at the crack ({0})", ex.Message); }
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? BasementRedirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>
    /// Whether a threshold someone has walked into lets them through now: a cracked patch only where its crack lies on the
    /// floor (a stretch of a level made before the patch was laid out, or one whose crack has been dug away, holds).
    /// </summary>
    private bool BasementMayPass(IServerPlayer player, Passage passage)
    {
        if (passage.Message != ThresholdNetwork.BasementFallMessage) return true;
        EntityPos pos = player.Entity.Pos;
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        Tile here = layout.TileAt(x, z);
        if (!WorldLayout.IsBasementCrack(here)) return false;
        Block on = sapi.World.BlockAccessor.GetBlock(new BlockPos(x, geometry.FloorFor(here.Level) + 1, z));
        return on.Code?.Domain == "backrooms" && on.Code.Path.StartsWith(BasementCrackCode, StringComparison.Ordinal);
    }

    /// <summary>
    /// A cracked patch in Level 2 (whose tiles the walked thresholds do not look at): if the player stands on its middle,
    /// it gives way, as everywhere else. Called on <see cref="Regions.BasementSystem"/>'s tick for whoever is in Level 2.
    /// </summary>
    public void BasementCrackInLevel2(IServerPlayer player)
    {
        if (network == null || layout == null || !CanTravel(player) || player.Entity.Teleporting || IsBusy(player)) return;
        if (player.WorldData.CurrentGameMode == EnumGameMode.Spectator) return;
        EntityPos pos = player.Entity.Pos;
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        Tile tile = layout.TileAt(x, z);
        if (tile.Level != 2 || !WorldLayout.BasementCrackGives(tile) || pos.Y - geometry.FloorFor(2) >= ThresholdNetwork.BasementCrackTripRel) return;
        Passage passage = network.BasementFall(x, z, tile);
        if (!BasementMayPass(player, passage)) return;
        Go(player, passage, network.Take(passage, null), "walk");
    }
}
