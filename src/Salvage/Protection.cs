using System;
using System.Text;
using Backrooms.Worldgen;
using HarmonyLib;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Salvage;

/// <summary>
/// Where the building will not give, whatever you hit it with:
/// <list type="bullet">
/// <item>The roof of every level under one: the solid top of the level, from its ceiling up to the mantle, wherever
/// nothing open is left above. Break through it and you would be walking about on top of the level. What hangs below
/// the roof is fair game: Level 0's ceiling tiles and the crawlspace over them, a light, a second ceiling.</item>
/// <item>The wall between two levels, from the height of the lower of their roofs up: below that it breaks like any
/// wall of its kind, and a tunnel can go under it.</item>
/// <item>Thresholds, dispensers, doors and landmarks, wherever they are (<see cref="BreakKind.Fixed"/>).</item>
/// </list>
/// Everything else of the building breaks down (<see cref="Breakdown"/>), and anything a player puts down is theirs to
/// take up again; the walls between levels break like any other wall of their kind. All of it is decided where the game
/// asks what tool tier a block needs, so the client never starts cracking a block it cannot break, and the block info
/// says why; the server refuses the break as well.
/// </summary>
public class ProtectionSystem : ModSystem
{
    private const string HarmonyId = "backrooms.protection";

    // One per side: in single player the client and the server share a process
    private static Protection server, client;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.2;

    public override void Start(ICoreAPI api)
    {
        if (!Harmony.HasAnyPatches(HarmonyId))
        {
            var harmony = new Harmony(HarmonyId);
            harmony.Patch(AccessTools.Method(typeof(Block), nameof(Block.GetRequiredMiningTier), new[] { typeof(IWorldAccessor), typeof(BlockPos) }),
                postfix: new HarmonyMethod(typeof(ProtectionSystem), nameof(RequiredTierPostfix)));
            harmony.Patch(AccessTools.Method(typeof(Block), nameof(Block.GetBlastResistance)),
                postfix: new HarmonyMethod(typeof(ProtectionSystem), nameof(BlastResistancePostfix)));
            harmony.Patch(AccessTools.Method(typeof(Block), nameof(Block.AddMiningTierInfo), new[] { typeof(StringBuilder), typeof(IWorldAccessor), typeof(BlockPos) }),
                prefix: new HarmonyMethod(typeof(ProtectionSystem), nameof(MiningTierInfoPrefix)));
        }
    }

    public override void AssetsFinalize(ICoreAPI api)
    {
        (int structure, int fixedCount) = Breakdown.Apply(api);
        if (api.Side == EnumAppSide.Server) api.Logger.Notification("[backrooms] {0} structural block types break down; {1} never break", structure, fixedCount);
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            server = new Protection(BackroomsWorld.CreateLayout(api.World), BackroomsWorld.CreateGeometry(api.World));
        });
        // Whatever the client thought, the server has the last word
        api.Event.BreakBlock += (IServerPlayer player, BlockSelection selection, ref float dropMultiplier, ref EnumHandling handling) =>
        {
            if (player?.WorldData.CurrentGameMode == EnumGameMode.Creative) return;
            BlockPos pos = selection.Position;
            if (api.World.BlockAccessor.GetBlock(pos).GetRequiredMiningTier(api.World, pos) >= Protection.UnbreakableTier) handling = EnumHandling.PreventDefault;
        };

        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("canbreak")
                .WithDescription("Lists a column of blocks round x, z (or one block at y) with the tool tier each needs and what it breaks down to")
                .WithArgs(api.ChatCommands.Parsers.Int("x"), api.ChatCommands.Parsers.Int("z"), api.ChatCommands.Parsers.OptionalInt("y", int.MinValue))
                .HandleWith(args => OnCanBreakCommand(api, args))
            .EndSubCommand();
    }

    private static TextCommandResult OnCanBreakCommand(ICoreServerAPI api, TextCommandCallingArgs args)
    {
        if (server == null) return TextCommandResult.Error("Not a Backrooms world");
        int x = (int)args[0], z = (int)args[1], y = (int)args[2];
        WorldGeometry g = BackroomsWorld.CreateGeometry(api.World);
        if (api.World.BlockAccessor.GetChunkAtBlockPos(x, g.FloorY, z) == null)
        {
            api.WorldManager.LoadChunkColumnPriority(x / GlobalConstants.ChunkSize, z / GlobalConstants.ChunkSize, new ChunkLoadOptions { KeepLoaded = true });
            return TextCommandResult.Success("That column is not loaded yet. Loading it; run the command again in a moment.");
        }
        int level = server.LevelAt(x, z);
        int floor = g.FloorFor(level);
        var text = new StringBuilder();
        int wallRoof = server.DividingWallRoof(x, z);
        text.AppendFormat("Level {0} at {1}, {2}{3}; floor y={4}, roof from rel {5}", WorldLayout.DisplayNumber(level), x, z,
            wallRoof == int.MaxValue ? "" : $" (wall between levels, holds from rel {wallRoof})", floor, Protection.RoofFrom(level));
        int from = y == int.MinValue ? floor - Worldgen.WorldGenerator.FoundationDepth - 8 : y, to = y == int.MinValue ? Math.Min(g.TopY, floor + 12) : y;
        var pos = new BlockPos(x, 0, z);
        for (int at = to; at >= from; at--)
        {
            pos.Y = at;
            Block block = api.World.BlockAccessor.GetBlock(pos);
            int tier = block.GetRequiredMiningTier(api.World, pos);
            string verdict = block.BlockId == 0 ? "" : tier >= Protection.UnbreakableTier ? "UNBREAKABLE" : $"tier {tier}, {block.BlockMaterial}, {block.Resistance:0.#}s";
            string drops = block.BlockId == 0 || tier >= Protection.UnbreakableTier || block.Drops == null ? ""
                : " -> " + string.Join(", ", System.Linq.Enumerable.Select(block.Drops, d => $"{d.Code} ~{d.Quantity.avg:0.##}"));
            text.AppendFormat("\n rel {0,3}  {1}  {2}{3}", at - floor, block.Code, verdict, drops);
        }
        return TextCommandResult.Success(text.ToString());
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        api.Event.LevelFinalize += () =>
        {
            if (BackroomsWorld.IsBackroomsClimate(api.World.Config)) client = new Protection(BackroomsWorld.CreateLayout(api.World), BackroomsWorld.CreateGeometry(api.World));
        };
    }

    public override void Dispose()
    {
        server = client = null;
    }

    private static Protection For(IWorldAccessor world) => world?.Side == EnumAppSide.Server ? server : client;

    public static void RequiredTierPostfix(Block __instance, IWorldAccessor world, BlockPos pos, ref int __result)
    {
        if (__result >= Protection.UnbreakableTier || pos == null) return;
        Protection rules = For(world);
        if (rules == null) return;
        if (rules.IsProtected(world.BlockAccessor, __instance, pos)) __result = Protection.UnbreakableTier;
    }

    public static void BlastResistancePostfix(Block __instance, IWorldAccessor world, BlockPos pos, ref double __result)
    {
        if (pos != null && __instance.GetRequiredMiningTier(world, pos) >= Protection.UnbreakableTier) __result = 1_000_000;
    }

    public static bool MiningTierInfoPrefix(Block __instance, StringBuilder sb, IWorldAccessor world, BlockPos pos)
    {
        if (pos == null || __instance.GetRequiredMiningTier(world, pos) < Protection.UnbreakableTier) return true;
        sb.AppendLine(Lang.Get("backrooms:blockinfo-unbreakable"));
        return false;
    }
}

/// <summary>The rules of <see cref="ProtectionSystem"/>: pure functions of the layout, so the client and the server agree.</summary>
public sealed class Protection
{
    /// <summary>The tool tier no tool has: a block needing it cannot be broken (the mantle's way).</summary>
    public const int UnbreakableTier = 99;

    private readonly WorldLayout layout;
    private readonly WorldGeometry geometry;

    public Protection(WorldLayout layout, WorldGeometry geometry)
    {
        this.layout = layout;
        this.geometry = geometry;
    }

    /// <summary>
    /// The lowest height above a level's floor at which its roof can begin: the ceiling over its ordinary rooms (over
    /// the tallest of its rooms in the Poolrooms, whose rooms vary so). None under the open sky. Higher up, a block is
    /// roof only if nothing open is left above it (<see cref="IsRoof"/>).
    /// </summary>
    public static int RoofFrom(int level) => level switch
    {
        WorldLayout.Poolrooms => 16,
        1 or 7 or 8 => 5,
        _ when WorldLayout.IsOpenSky(level) => int.MaxValue,
        _ => WorldGeometry.RoomHeight + 1,
    };

    /// <summary>The level at a block position.</summary>
    public int LevelAt(int x, int z) => layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));

    /// <summary>Whether the wall line on the west or north side of a cell divides two levels (and is a wall at all).</summary>
    private static bool Divides(int level, int otherLevel)
    {
        if (level == otherLevel) return false;
        // The suburbs run on into the fields with no wall between them; the places you noclip into have rims all round
        bool walled = WorldLayout.IsNoclipRegion(level) || WorldLayout.IsNoclipRegion(otherLevel);
        return walled || !(WorldLayout.IsOpenSky(level) && WorldLayout.IsOpenSky(otherLevel));
    }

    /// <summary>
    /// How high above the floor the wall between two levels holds from, if this column is one (it runs along the west and
    /// north edges of a cell): the lower of the two levels' roofs. <see cref="int.MaxValue"/> if it is no such wall.
    /// </summary>
    public int DividingWallRoof(int x, int z)
    {
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        int level = layout.LevelAt(mx, mz), roof = int.MaxValue;
        int lx = x - mx * WorldLayout.MacroSize, lz = z - mz * WorldLayout.MacroSize;
        if (lx == 0)
        {
            int other = layout.LevelAt(mx - 1, mz);
            if (Divides(level, other)) roof = Math.Min(roof, Math.Min(RoofFrom(level), RoofFrom(other)));
        }
        if (lz == 0)
        {
            int other = layout.LevelAt(mx, mz - 1);
            if (Divides(level, other)) roof = Math.Min(roof, Math.Min(RoofFrom(level), RoofFrom(other)));
        }
        return roof;
    }

    /// <summary>Whether this block, at this position, cannot be broken.</summary>
    public bool IsProtected(IBlockAccessor blocks, Block block, BlockPos pos)
    {
        if (block == null || block.BlockId == 0) return false;
        BreakKind kind = Breakdown.KindOf(block);
        if (kind == BreakKind.Fixed) return true;
        // The roof is the building's own, or the rock over Level 8's caves; and the wall between two levels holds from
        // the height of the lower of their roofs up, so nobody climbs over it under the ceiling or through the slab
        if (kind != BreakKind.Structure && !(kind == BreakKind.None && IsRock(block))) return false;
        int wallRoof = DividingWallRoof(pos.X, pos.Z);
        if (wallRoof != int.MaxValue && pos.Y - geometry.FloorFor(LevelAt(pos.X, pos.Z)) >= wallRoof) return true;
        return IsRoof(blocks, pos);
    }

    /// <summary>
    /// Whether a position is in a level's roof: at or above where its ceilings are, with nothing open above it up to the
    /// mantle cap. So in Level 0 the ceiling tiles (the crawlspace is over them) can come down, but not the slab over the
    /// crawlspace; on a level with one plain ceiling, the ceiling is the roof.
    /// </summary>
    private bool IsRoof(IBlockAccessor blocks, BlockPos pos)
    {
        int level = LevelAt(pos.X, pos.Z);
        int roof = RoofFrom(level);
        if (roof == int.MaxValue || pos.Y - geometry.FloorFor(level) < roof) return false;
        var above = pos.Copy();
        for (int y = pos.Y + 1; y < geometry.CapY; y++)
        {
            above.Y = y;
            if (blocks.GetBlockId(above) == 0) return false;
        }
        return true;
    }

    /// <summary>Raw rock and ore: the caves, cliffs and strata. No player ever has a block of it to set down.</summary>
    private static bool IsRock(Block block) =>
        block.Code?.Domain == "game" && block.FirstCodePart() is "rock" or "ore" or "crackedrock";
}
