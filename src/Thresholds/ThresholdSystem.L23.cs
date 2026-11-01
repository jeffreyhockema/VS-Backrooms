using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 23, "The Petrified Garden"'s thresholds in the game (experimental, kept as level 28): those put
/// down in the level face the most open way; and the dev test of its walked ways (<c>/backrooms l23walk</c>, registered by
/// Regions.L23System). This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>
    /// Someone is about to be put down in the level at <paramref name="link"/>: they face the most open way among the
    /// eight round them (the longest run of open forest floor, up to 32 blocks), not the trunk beside them.
    /// </summary>
    private void L23Arriving(IServerPlayer player, Link link, ref double drop)
    {
        int x = (int)System.Math.Floor(link.X), z = (int)System.Math.Floor(link.Z);
        int best = 0;
        float yaw = 0;
        for (int k = 0; k < 8; k++)
        {
            double a = k * System.Math.PI / 4, sx = System.Math.Sin(a), sz = System.Math.Cos(a);
            int run = 0;
            while (run < 32)
            {
                Tile t = layout.TileAt((int)System.Math.Floor(x + 0.5 + sx * (run + 1)), (int)System.Math.Floor(z + 0.5 + sz * (run + 1)));
                if (t.Level != WorldLayout.Level23 || t.Kind != TileKind.Floor) break;
                run++;
            }
            // (A player looks along (sin yaw, cos yaw))
            if (run > best) { best = run; yaw = (float)a; }
        }
        if (best == 0) return;
        Face(player, yaw);
        // (Again once they are down, in case the client took the first before the move)
        sapi.Event.RegisterCallback(_ => Face(player, yaw), 1500);
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L23Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L23MayPass(IServerPlayer player, Passage passage) => true;

    /// <summary>
    /// (Dev test, <c>/backrooms l23walk x z [rel]</c>) Goes through the walked threshold at x z as someone standing there at
    /// <paramref name="rel"/> over the level's floor would (by default on the floor of the tile: a Poolrooms tree's hollow,
    /// Base Seedling's hollow tree, the bottom of the Heart of Water's well): where it leads (the first time, or as written
    /// down), whether it is two-way and where its way back leads, then loads where it leads and reports the blocks at the
    /// arrival's feet, head and under them.
    /// </summary>
    internal void L23WalkTest(int x, int z, double? rel, Action<string> report)
    {
        if (network == null || layout == null) { report("This is not a Backrooms world"); return; }
        Tile tile = layout.TileAt(x, z);
        double r = rel ?? (tile.Level == WorldLayout.Poolrooms ? 1.0 : -tile.Depth + 1.0);
        Passage passage = network.Walked(x, z, tile, r);
        if (passage == null) { report($"nothing to go through at {x}, {z} (level {tile.Level}, Under {tile.Under}, rel {r:0.0})"); return; }
        bool known = network.TryGet(passage.Source, out _);
        Link? home = passage.TwoWay ? network.HomeFor(passage) : null;
        if (network.Take(passage, home) is not { } to) { report($"{x}, {z} leads nowhere"); return; }
        int ax = (int)Math.Floor(to.X), az = (int)Math.Floor(to.Z);
        Tile at = layout.TileAt(ax, az);
        string text = $"{x}, {z} (level {tile.Level}, source {passage.Source.X}, {passage.Source.Z}, {(known ? "written down before" : "first time")}, "
            + $"{(passage.TwoWay ? "two-way" : "one-way")}, {passage.Message}) leads to {to.X:0.0}, {to.Y:0.0}, {to.Z:0.0} in level {at.Level} (Under {at.Under}, zone {at.Zone})"
            + (to.Marker ? ", a thin spot" : "");
        if (passage.TwoWay && passage.ReturnFeature != null)
        {
            if (layout.FeatureBeside(ax, az, passage.ReturnFeature) is { } back)
                text += network.TryGet(back, out Link b) ? $"; its way back {back.X}, {back.Z} leads to {b.X:0.0}, {b.Y:0.0}, {b.Z:0.0}" : $"; its way back {back.X}, {back.Z} is not written down";
            else text += "; no way back beside the arrival";
            if (home is { } h) text += $" (home {h.X:0.0}, {h.Y:0.0}, {h.Z:0.0})";
        }
        sapi.WorldManager.LoadChunkColumnPriority(ax / GlobalConstants.ChunkSize, az / GlobalConstants.ChunkSize, new ChunkLoadOptions
        {
            OnLoaded = () =>
            {
                IBlockAccessor blocks = sapi.World.BlockAccessor;
                string Of(int y)
                {
                    var pos = new BlockPos(ax, y, az);
                    Block solid = blocks.GetBlock(pos), fluid = blocks.GetBlock(pos, BlockLayersAccess.Fluid);
                    return solid.Code + (fluid.Id != 0 ? "+" + fluid.Code : "");
                }
                int feet = (int)Math.Floor(to.Y);
                report(text + $"; under {Of(feet - 1)}, feet {Of(feet)}, head {Of(feet + 1)}");
            },
        });
    }
}
