using System;
using Backrooms.Entities;
using Backrooms.Thresholds;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 15, "Futuristic Halls" (experimental, kept as level 27): the ways out that are not tiles, and its testing command.
/// This file is the level's own.
///
/// <list type="bullet">
/// <item><b>The ESCAPE panel</b> that works (<c>l15-escapelive</c>, one control room in a few dozen wings): pressed, the
/// locked gateway in its room rolls up (<c>l15-gatewayshut</c> swapped for <c>l15-gatewayopen</c>, for good), and the gateway
/// is a threshold to Level 3 (ThresholdNetwork.L15.cs).</item>
/// <item><b>The pane with a street behind it</b> (<c>l15-cityglass</c>): whoever breaks it is taken through, to Level 11.</item>
/// <item><c>/backrooms l15 roboman x z</c> puts a Robo-Man down at a block position of the level (for the showcase's shot of
/// one in the dark), turned toward whoever asked; <c>escape x z</c> and <c>break x z</c> press a panel and break a pane (testing).
/// The level's life is otherwise the director's (Roster, MenaceSystem).</item>
/// </list>
/// </summary>
public class L15System : ModSystem
{
    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private int cityGlassId;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.3;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsL15Escape", typeof(BlockBehaviorL15Escape));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            cityGlassId = api.World.GetBlock(new AssetLocation("backrooms:l15-cityglass"))?.BlockId ?? 0;
            if (cityGlassId != 0) api.Event.DidBreakBlock += OnBrokeBlock;
        });
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l15")
                .WithDescription("Level 15 (testing): 'roboman x z' puts a Robo-Man down at x z in the level, turned toward you; 'escape x z' presses the ESCAPE panel at x z; 'break x z' breaks the street pane at x z; 'l15-<kind> x z' uses a link's block there (l15-walldoor, l15-l3door)")
                .WithArgs(api.ChatCommands.Parsers.Word("what"), api.ChatCommands.Parsers.Int("x"), api.ChatCommands.Parsers.Int("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnCommand)
            .EndSubCommand();
    }

    public override void Dispose()
    {
        if (sapi != null && cityGlassId != 0) sapi.Event.DidBreakBlock -= OnBrokeBlock;
    }

    private TextCommandResult OnCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        string what = (string)args[0];
        int x = (int)args[1], z = (int)args[2];
        if (what.StartsWith("l15-"))
        {
            // Using one of the links' blocks at x z, as the caller (testing: the showcase's trips through the ways in)
            if (args.Caller.Player is not IServerPlayer user) return TextCommandResult.Error("A player must use it");
            int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
            sapi.ModLoader.GetModSystem<ThresholdSystem>()?.Use(user, new BlockPos(x, geometry.FloorFor(level) + 1, z), what);
            return TextCommandResult.Success($"Used {what} at {x}, {z} (Level {WorldLayout.DisplayNumber(level)})");
        }
        if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.Level15) return TextCommandResult.Error("Not in Level 15");
        int floor = geometry.FloorFor(WorldLayout.Level15);
        switch (what)
        {
            case "escape":
            {
                if (args.Caller.Player is not IServerPlayer player) return TextCommandResult.Error("A player must press it");
                int opened = PressEscape(player, new BlockPos(x, floor + 2, z));
                return TextCommandResult.Success($"ESCAPE at {x}, {z}: {opened} gateway blocks rolled up");
            }
            case "break":
            {
                if (args.Caller.Player is not IServerPlayer player) return TextCommandResult.Error("A player must break it");
                var pos = new BlockPos(x, floor + 2, z);
                if (sapi.World.BlockAccessor.GetBlock(pos).BlockId != cityGlassId) return TextCommandResult.Error("No street pane there");
                sapi.World.BlockAccessor.SetBlock(0, pos);
                OnBrokeBlock(player, cityGlassId, new BlockSelection { Position = pos });
                return TextCommandResult.Success($"Pane at {x}, {z} broken");
            }
            case "roboman":
            {
                var at = new Vec3d(x + 0.5, floor + 1, z + 0.5);
                Entity caller = args.Caller.Entity;
                Entity robo = sapi.ModLoader.GetModSystem<MenaceSystem>()?.SpawnHunter(Roster.RoboMan, at, caller);
                if (robo == null) return TextCommandResult.Error("Could not put a Robo-Man down");
                if (caller != null) robo.Pos.Yaw = (float)Math.Atan2(caller.Pos.X - at.X, caller.Pos.Z - at.Z);
                return TextCommandResult.Success($"Robo-Man put down at {x}, {z}");
            }
        }
        return TextCommandResult.Error("'roboman x z', 'escape x z', 'break x z' or 'l15-<kind> x z'");
    }

    /// <summary>
    /// The ESCAPE panel at a position is pressed: the gateway in its room rolls up (every block of it still shut), for good.
    /// Returns how many of the gateway's blocks rolled up.
    /// </summary>
    public int PressEscape(IServerPlayer player, BlockPos pos)
    {
        if (layout == null) return 0;
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        int floor = geometry.FloorFor(WorldLayout.Level15), opened = 0;
        (int X, int Z)? first = null;
        var gateway = layout.L15GatewayOfWing(pos.X, pos.Z);
        if (gateway.Count == 0) gateway = layout.L15GatewayNear(pos.X, pos.Z);
        foreach (var (x, z) in gateway)
        {
            first ??= (x, z);
            for (int rel = 1; rel <= 3; rel++)
            {
                var at = new BlockPos(x, floor + rel, z);
                string path = blocks.GetBlock(at).Code?.Path;
                if (path == null || !path.StartsWith("l15-gatewayshut-")) continue;
                Block open = sapi.World.GetBlock(new AssetLocation("backrooms", path.Replace("l15-gatewayshut-", "l15-gatewayopen-")));
                if (open == null) continue;
                blocks.ExchangeBlock(open.BlockId, at);
                blocks.MarkBlockDirty(at);
                opened++;
            }
        }
        sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8);
        if (opened > 0 && first is { } g)
        {
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/block/heavymetal-hit"), g.X + 0.5, floor + 2, g.Z + 0.5, null, true, 24);
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/translocate-active"), g.X + 0.5, floor + 2, g.Z + 0.5, null, true, 16, 0.6f);
        }
        player?.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, opened > 0 ? "backrooms:l15-escape-open" : "backrooms:l15-escape-again"),
            EnumChatType.Notification);
        return opened;
    }

    /// <summary>Someone has broken the pane with a street behind it: it takes them through (ThresholdNetwork.L15.cs's window).</summary>
    private void OnBrokeBlock(IServerPlayer byPlayer, int oldblockId, BlockSelection blockSel)
    {
        if (oldblockId != cityGlassId || byPlayer == null || blockSel?.Position == null) return;
        BlockPos pos = blockSel.Position.Copy();
        // (A moment later: the glass is gone first, and its shards fall where it stood)
        sapi.Event.RegisterCallback(_ => sapi.ModLoader.GetModSystem<ThresholdSystem>()?.Use(byPlayer, pos, "l15-window"), 250);
    }
}

/// <summary>
/// The ESCAPE panel that works: a threshold block (so it never breaks) whose use rolls up its room's gateway rather than taking
/// anyone anywhere (<see cref="L15System.PressEscape"/>).
/// </summary>
public class BlockBehaviorL15Escape : BlockBehaviorThreshold
{
    private WorldInteraction[] help;

    public BlockBehaviorL15Escape(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventSubsequent;
        help ??= new[] { new WorldInteraction { ActionLangCode = "backrooms:blockhelp-l15-escape", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventSubsequent;
        if (world.Api is ICoreServerAPI sapi && byPlayer is IServerPlayer player)
            sapi.ModLoader.GetModSystem<L15System>()?.PressEscape(player, blockSel.Position);
        return true;
    }
}
