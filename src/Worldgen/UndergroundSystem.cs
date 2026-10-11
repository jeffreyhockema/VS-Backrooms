using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.ServerMods;

namespace Backrooms.Worldgen;

/// <summary>
/// The ground under the Backrooms is the ground under any Vintage Story world. Vanilla's own generators lay it down
/// first, for every chunk: the shape of the land, its rock strata, its caves and its ore, coal, gems and minerals. Then
/// the Backrooms are built into the top of it (<see cref="WorldGenerator"/>): a few blocks of concrete under each floor
/// (<see cref="WorldGenerator.FoundationDepth"/>), the levels, and their roof. Where the land lay lower than the floor
/// (seas, valleys), the space up to the foundation is filled with the rock it was made of; where it rose higher, the
/// Backrooms take its place. So you break through a floor, and under it you mine as you would anywhere.
///
/// Only the underground generators are borrowed, never what grows or stands on the surface: no soil, plants, trees,
/// ruins or story structures, and none of the soil deposits (clay, peat, gravel, soil), which would otherwise break out
/// in the lawns and fields of the open levels and short-cut Level 3's clay.
/// </summary>
public class UndergroundSystem : ModSystem
{
    /// <summary>The vanilla systems whose world generation runs in a Backrooms world too.</summary>
    private static readonly HashSet<string> Borrowed = new() { "GenMaps", "GenTerra", "GenRockStrataNew", "GenCaves", "GenDeposits" };

    private ICoreServerAPI sapi;

    /// <summary>Whether vanilla's generators lay the ground in this world, for the Backrooms to be built on top of.</summary>
    public static bool Active { get; private set; }

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After BackroomsModSystem (which registers the Backrooms generator) and every vanilla generator
    public override double ExecuteOrder() => 1.1;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, OnModsAndConfigReady);
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("ground")
                .WithDescription("Counts what lies under the foundations of the chunk round x, z: rock, ore, caves, by depth")
                .WithArgs(api.ChatCommands.Parsers.Int("x"), api.ChatCommands.Parsers.Int("z"))
                .HandleWith(OnGroundCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnGroundCommand(TextCommandCallingArgs args)
    {
        int x = (int)args[0], z = (int)args[1];
        var geometry = new WorldGeometry(sapi.WorldManager.MapSizeY);
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        if (blocks.GetChunkAtBlockPos(x, geometry.FloorY, z) == null)
        {
            sapi.WorldManager.LoadChunkColumnPriority(x / 32, z / 32, new ChunkLoadOptions { KeepLoaded = true });
            return TextCommandResult.Success("That column is not loaded yet. Loading it; run the command again in a moment.");
        }
        int x0 = x / 32 * 32, z0 = z / 32 * 32, top = geometry.FloorY - WorldGenerator.FoundationDepth - 1;
        var text = new System.Text.StringBuilder($"Ground under chunk {x0},{z0} (y 1-{top}), by bands of 40 down from the foundations:");
        var pos = new BlockPos(0, 0, 0);
        for (int bandTop = top; bandTop >= 1; bandTop -= 40)
        {
            var counts = new Dictionary<string, int>();
            for (int y = bandTop; y > Math.Max(0, bandTop - 40); y--)
                for (int dz = 0; dz < 32; dz++)
                    for (int dx = 0; dx < 32; dx++)
                    {
                        pos.Set(x0 + dx, y, z0 + dz);
                        Block block = blocks.GetBlock(pos);
                        string key = block.Code == null ? "?" : block.FirstCodePart() switch
                        {
                            "rock" => "rock",
                            "ore" => block.Code.Path.Contains("-poor-") || block.Code.Path.Contains("-medium-") || block.Code.Path.Contains("-rich-")
                                ? "ore-" + block.Code.Path.Split('-')[2] : "ore-" + block.Code.Path.Split('-')[1],
                            _ => block.Code.Domain + ":" + block.FirstCodePart(),
                        };
                        counts[key] = counts.GetValueOrDefault(key) + 1;
                        Block fluid = blocks.GetBlock(pos, BlockLayersAccess.Fluid);
                        if (fluid.BlockId != 0) counts["fluid:" + fluid.FirstCodePart()] = counts.GetValueOrDefault("fluid:" + fluid.FirstCodePart()) + 1;
                    }
            text.AppendFormat("\n y {0}-{1}: {2}", Math.Max(1, bandTop - 39), bandTop,
                string.Join(", ", counts.OrderByDescending(c => c.Value).Select(c => $"{c.Key} {c.Value}")));
        }
        return TextCommandResult.Success(text.ToString());
    }

    private void OnModsAndConfigReady()
    {
        if (sapi.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
        var geometry = new WorldGeometry(sapi.WorldManager.MapSizeY);

        // Vanilla lays the land out round its sea level; put that at the Backrooms' floor, so the natural ground (and its
        // ore, which lies at depths below the surface) comes up to just under the foundations
        TerraGenConfig.seaLevel = geometry.FloorY;
        Climate.Sealevel = geometry.FloorY;

        IWorldGenHandler standard = sapi.Event.GetRegisteredWorldGenHandlers("standard");
        IWorldGenHandler backrooms = sapi.Event.GetRegisteredWorldGenHandlers(BackroomsWorld.WorldTypeCode);
        if (standard == null || backrooms == null)
        {
            sapi.Logger.Error("[backrooms] No vanilla world generator to borrow the underground from; the ground under the levels will be empty");
            return;
        }

        int borrowed = 0;
        // Ahead of the Backrooms' own handlers, in vanilla's order
        borrowed += Borrow(standard.OnMapRegionGen, backrooms.OnMapRegionGen);
        borrowed += Borrow(standard.OnMapChunkGen, backrooms.OnMapChunkGen);
        for (int pass = 0; pass < standard.OnChunkColumnGen.Length; pass++)
        {
            if (standard.OnChunkColumnGen[pass] == null || backrooms.OnChunkColumnGen[pass] == null) continue;
            borrowed += Borrow(standard.OnChunkColumnGen[pass], backrooms.OnChunkColumnGen[pass]);
        }
        // The lists the API does not expose: the generators' set-up, and map regions whose neighbours are loaded
        foreach (string field in new[] { "OnInitWorldGen", "OnMapRegionNeighborsLoaded" })
        {
            FieldInfo info = standard.GetType().GetField(field, BindingFlags.Public | BindingFlags.Instance);
            if (info?.GetValue(standard) is IList from && info.GetValue(backrooms) is IList to) borrowed += Borrow(from, to);
        }

        int soil = DropSoilDeposits();
        Active = borrowed > 0;
        sapi.Logger.Notification("[backrooms] The ground under the levels is vanilla's: {0} generator handlers borrowed, {1} soil deposits left out", borrowed, soil);
    }

    /// <summary>Copies the borrowed systems' handlers from one list to the front of another, keeping their order.</summary>
    private static int Borrow(IList from, IList to)
    {
        var picked = from.Cast<Delegate>().Where(d => d.Target != null && Borrowed.Contains(d.Target.GetType().Name) && !to.Contains(d)).ToList();
        for (int i = 0; i < picked.Count; i++) to.Insert(i, picked[i]);
        return picked.Count;
    }

    private static int Borrow<T>(List<T> from, List<T> to) where T : Delegate => Borrow((IList)from, (IList)to);

    public override void Dispose()
    {
        // (Static, so a world loaded next in the same process starts without it)
        Active = false;
    }

    /// <summary>Leaves the soil deposits (clay, peat, gravel, soil) out of vanilla's deposit generator.</summary>
    private int DropSoilDeposits()
    {
        GenDeposits deposits = sapi.ModLoader.GetModSystem<GenDeposits>();
        if (deposits?.Deposits == null) return 0;
        int before = deposits.Deposits.Length;
        deposits.Deposits = deposits.Deposits.Where(d => d.fromFile == null || !d.fromFile.Contains("deposits/soil/")).ToArray();
        return before - deposits.Deposits.Length;
    }
}
