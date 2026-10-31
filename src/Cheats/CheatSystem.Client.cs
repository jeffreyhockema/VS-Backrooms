using System;
using System.Linq;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;
using Backrooms.Map;
using Backrooms.Salvage;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// The client side of the cheats: the menu, the view cheats (debug HUD, fog, map) and restarting the tutorial, which
/// only touch this client.
/// </summary>
public partial class CheatSystem
{
    public const string HotkeyCode = "backroomscheats";
    /// <summary>The clear air's key among the client's ambient modifiers (the AtmosphereSystem keeps it after the level's air).</summary>
    public const string ClearAirKey = "backrooms-cheat-clearair";

    private ICoreClientAPI capi;
    private GuiDialogCheats dialog;
    private HudCheatInfo hud;
    private WorldLayout clientLayout;

    /// <summary>Whether this player may use the cheats (the server checks again for every command).</summary>
    public bool Privileged => capi.World.Player?.HasPrivilege(Privilege.controlserver) == true;

    /// <summary>
    /// The menu's status line: the level you are in by the layout (worked out on this client, as the HUD does), where
    /// you are from spawn, your game mode, and the world's map and scarcity settings as this client was sent them.
    /// </summary>
    public string StatusLine()
    {
        EntityPlayer player = capi.World.Player?.Entity;
        ITreeAttribute config = capi.World.Config;
        if (player == null) return "";
        int x = (int)Math.Floor(player.Pos.X), z = (int)Math.Floor(player.Pos.Z);
        var spawn = capi.World.DefaultSpawnPosition;
        var sb = new StringBuilder();
        if (BackroomsWorld.IsBackroomsClimate(config))
        {
            clientLayout ??= BackroomsWorld.CreateLayout(capi.World);
            int level = clientLayout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
            sb.Append($"Level {WorldLayout.DisplayNumber(level)} (#{level})");
        }
        else sb.Append("Not a Backrooms world");
        sb.Append($"  |  {x - spawn.X:0}, {z - spawn.Z:0} from spawn  |  {capi.World.Player.WorldData.CurrentGameMode}");
        sb.Append($"  |  map {config?.GetString(MapSetting.Code, "seen")}  |  scarcity {config?.GetString(ScarcitySystem.ConfigKey, "normal")}");
        return sb.ToString();
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        dialog = new GuiDialogCheats(api, this);
        api.Input.RegisterHotKey(HotkeyCode, Lang.Get("backrooms:hotkey-cheats"), GlKeys.F7, HotkeyType.GUIOrOtherControls);
        api.Input.SetHotKeyHandler(HotkeyCode, _ => ToggleDialog());
        api.ChatCommands.Create("cheats")
            .WithDescription("Opens the Backrooms cheat menu")
            .HandleWith(_ =>
            {
                ToggleDialog();
                return TextCommandResult.Success();
            });
    }

    private bool ToggleDialog()
    {
        if (dialog.IsOpened()) dialog.TryClose();
        else dialog.TryOpen();
        return true;
    }

    /// <summary>
    /// The view cheats show what the server would not tell a player (the layout, unexplored map), so they ask for the
    /// same privilege as the commands.
    /// </summary>
    private bool Allowed()
    {
        if (Privileged) return true;
        capi.ShowChatMessage("The cheat menu needs the controlserver privilege");
        return false;
    }

    private bool InBackrooms()
    {
        if (BackroomsWorld.IsBackroomsClimate(capi.World.Config)) return true;
        capi.ShowChatMessage("This is not a Backrooms world");
        return false;
    }

    public void ToggleHud()
    {
        if (!Allowed() || !InBackrooms()) return;
        hud ??= new HudCheatInfo(capi);
        if (hud.IsOpened()) hud.TryClose();
        else hud.TryOpen();
    }

    /// <summary>No fog, and the scene at full brightness: for looking at a level's layout, not at its mood.</summary>
    public void ToggleClearAir()
    {
        if (!Allowed()) return;
        if (capi.Ambient.CurrentModifiers.Remove(ClearAirKey))
        {
            capi.ShowChatMessage("Fog back");
            return;
        }
        // Modifiers blend in the order they were added, each over the ones before at its weight: added last at
        // weight 1, this one wins over the Backrooms' own fog
        var clear = new AmbientModifier().EnsurePopulated();
        clear.FogDensity = WeightedFloat.New(0, 1);
        clear.FlatFogDensity = WeightedFloat.New(0, 1);
        clear.FogMin = WeightedFloat.New(0, 1);
        clear.FogBrightness = WeightedFloat.New(1, 1);
        clear.SceneBrightness = WeightedFloat.New(1, 1);
        capi.Ambient.CurrentModifiers[ClearAirKey] = clear;
        capi.ShowChatMessage("Fog off");
    }

    public void RevealMap(int radius)
    {
        if (!Allowed() || !InBackrooms()) return;
        BackroomsMapLayer layer = capi.ModLoader.GetModSystem<WorldMapManager>()?.MapLayers.OfType<BackroomsMapLayer>().FirstOrDefault();
        if (layer == null)
        {
            capi.ShowChatMessage("No Backrooms map layer");
            return;
        }
        if (!layer.MapAllowed)
        {
            capi.ShowChatMessage("There is no map in this world (map setting: none)");
            return;
        }
        int mapped = layer.RevealLoadedAround(radius);
        capi.ShowChatMessage($"Mapped {mapped} columns within {radius} blocks (only loaded chunks)");
    }

    /// <summary>
    /// Starts Backrooms: First Steps again from its first step on this client, as the game's own <c>.tutorial restart</c>
    /// does for the tutorial in progress (that one does nothing once the tutorial is finished): ModSystemTutorial resets
    /// every step and saves the empty progress in its ModConfig file.
    /// </summary>
    public void RestartTutorial()
    {
        if (!InBackrooms()) return;
        ModSystemTutorial tutorials = capi.ModLoader.GetModSystem<ModSystemTutorial>();
        if (tutorials == null || !tutorials.Tutorials.TryGetValue(BackroomsTutorial.Code, out ITutorial tutorial))
        {
            capi.ShowChatMessage("Backrooms: First Steps is not registered");
            return;
        }
        // (Builds the steps if the tutorial has not been opened yet: a restart resets only the steps there are)
        tutorial.GetTutorialSteps(false);
        tutorials.StartTutorial(BackroomsTutorial.Code, restart: true);
        capi.ShowChatMessage("Backrooms: First Steps starts again from its first step");
    }

    public override void Dispose()
    {
        dialog?.Dispose();
        hud?.Dispose();
    }
}
