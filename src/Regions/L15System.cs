using System;
using Backrooms.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 15, "Futuristic Halls" (experimental, kept as level 27): its testing command. <c>/backrooms l15 roboman x z</c> puts a
/// Robo-Man down at a block position of the level (for the showcase's shot of one in the dark), turned toward whoever
/// asked. The level's life is otherwise the director's (Roster, MenaceSystem). This file is the level's own.
/// </summary>
public class L15System : ModSystem
{
    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After BackroomsModSystem, which creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.3;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
        });
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l15")
                .WithDescription("Level 15 (testing): 'roboman x z' puts a Robo-Man down at x z in the level, turned toward you")
                .WithArgs(api.ChatCommands.Parsers.Word("what"), api.ChatCommands.Parsers.Int("x"), api.ChatCommands.Parsers.Int("z"))
                .RequiresPrivilege(Privilege.controlserver)
                .HandleWith(OnCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnCommand(TextCommandCallingArgs args)
    {
        if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
        if ((string)args[0] != "roboman") return TextCommandResult.Error("Only 'roboman x z'");
        int x = (int)args[1], z = (int)args[2];
        if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != WorldLayout.Level15) return TextCommandResult.Error("Not in Level 15");
        var at = new Vec3d(x + 0.5, geometry.FloorFor(WorldLayout.Level15) + 1, z + 0.5);
        Entity caller = args.Caller.Entity;
        Entity robo = sapi.ModLoader.GetModSystem<MenaceSystem>()?.SpawnHunter(Roster.RoboMan, at, caller);
        if (robo == null) return TextCommandResult.Error("Could not put a Robo-Man down");
        if (caller != null)
        {
            float yaw = (float)Math.Atan2(caller.Pos.X - at.X, caller.Pos.Z - at.Z);
            robo.Pos.Yaw = yaw;
        }
        return TextCommandResult.Success($"Robo-Man put down at {x}, {z}");
    }
}
