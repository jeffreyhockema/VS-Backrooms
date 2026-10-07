using System.Linq;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;
using Backrooms.Map;

namespace Backrooms.Cheats;

/// <summary>The client side of the cheats: the menu, and the view cheats (debug HUD, fog, map), which only touch this client.</summary>
public partial class CheatSystem
{
    public const string HotkeyCode = "backroomscheats";
    private const string ClearAirKey = "backrooms-cheat-clearair";

    private ICoreClientAPI capi;
    private GuiDialogCheats dialog;
    private HudCheatInfo hud;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        dialog = new GuiDialogCheats(api, this);
        api.Input.RegisterHotKey(HotkeyCode, "Backrooms: cheat menu", GlKeys.F7, HotkeyType.GUIOrOtherControls);
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
        if (capi.World.Player?.HasPrivilege(Privilege.controlserver) == true) return true;
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
        int mapped = layer.RevealLoadedAround(radius);
        capi.ShowChatMessage($"Mapped {mapped} columns within {radius} blocks (only loaded chunks)");
    }

    public override void Dispose()
    {
        dialog?.Dispose();
        hud?.Dispose();
    }
}
