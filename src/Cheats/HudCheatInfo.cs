using System;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// A live readout of what the layout says about where you stand: level, how far through it, the cell and tile under
/// your feet, Level 0's zone, dens and sanctuaries, stability and temperature. Worked out on the client from the seed,
/// as the map is; the menace band lives on the server (/backrooms menace).
/// </summary>
public class HudCheatInfo : HudElement
{
    // A read-only overlay: never swallow clicks that fall inside its frame (see HudNeeds)
    public override void OnMouseDown(MouseEvent args) { }
    public override void OnMouseUp(MouseEvent args) { }

    private const int Width = 460, Height = 168;

    private readonly WorldLayout layout;
    private readonly WorldGeometry geometry;
    private long listener;

    public HudCheatInfo(ICoreClientAPI capi) : base(capi)
    {
        layout = BackroomsWorld.CreateLayout(capi.World);
        geometry = BackroomsWorld.CreateGeometry(capi.World);

        ElementBounds textBounds = ElementBounds.Fixed(0, 0, Width, Height);
        ElementBounds bgBounds = textBounds.ForkBoundingParent(8, 6, 8, 6);
        ElementBounds dialogBounds = bgBounds.ForkBoundingParent().WithAlignment(EnumDialogArea.LeftTop)
            .WithFixedAlignmentOffset(GuiStyle.DialogToScreenPadding, 160);
        SingleComposer = capi.Gui.CreateCompo("backrooms-cheathud", dialogBounds)
            .AddGameOverlay(bgBounds)
            .AddDynamicText("", CairoFont.WhiteDetailText(), textBounds, "text")
            .Compose();
    }

    public override void OnGuiOpened()
    {
        base.OnGuiOpened();
        Update(0);
        listener = capi.Event.RegisterGameTickListener(Update, 250);
    }

    public override void OnGuiClosed()
    {
        base.OnGuiClosed();
        capi.Event.UnregisterGameTickListener(listener);
    }

    private void Update(float dt)
    {
        EntityPlayer player = capi.World.Player?.Entity;
        if (player == null) return;
        int x = (int)Math.Floor(player.Pos.X), z = (int)Math.Floor(player.Pos.Z);
        int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
        int level = layout.LevelAt(mx, mz);
        int floorY = geometry.FloorFor(level);
        var spawn = capi.World.DefaultSpawnPosition;

        var sb = new StringBuilder();
        int toNext = layout.BlocksToNextLevel(x, z, level);
        sb.Append($"Level {WorldLayout.DisplayNumber(level)}, {layout.LevelDepth(x, z, level):P0} through it");
        sb.AppendLine(toNext == int.MaxValue ? "" : $", ~{toNext} blocks to the next");
        sb.AppendLine($"Position {x - spawn.X:0}, {player.Pos.Y - floorY:0.0}, {z - spawn.Z:0} (y above the floor)   cell {mx}, {mz}   in cell {x - mx * WorldLayout.MacroSize}, {z - mz * WorldLayout.MacroSize}");

        Tile t = layout.TileAt(x, z);
        sb.AppendLine($"Tile {t.Kind}, floor {t.Floor}, ceiling {t.Ceiling}, wall {t.Pattern}, zone {t.Zone}, variant {t.Variant}, detail {t.Detail}");
        sb.AppendLine($"     stack {t.Stack}, stair {t.Stair}, under {t.Under}, depth {t.Depth}, height {t.Height}, roof {t.Roof}"
            + (t.Sealed ? ", sealed" : "") + (t.SupplyBox ? ", supply box" : "") + (t.Looted ? ", looted" : "") + (t.Grand ? ", grand" : "") + (t.Low ? ", low" : ""));

        var notes = new StringBuilder();
        if (level == 0) notes.Append(layout.IsManilaMacro(mx, mz) ? "Manila Room" : layout.IsRedRoom(mx, mz) ? "Red Room" : $"zone {layout.ZoneAt(mx, mz)}");
        if (level == 6 && layout.IsSnackrooms(mx, mz)) notes.Append("Snackrooms");
        if (layout.IsSanctuary(x, z, level)) notes.Append(notes.Length > 0 ? ", " : "").Append("sanctuary");
        if (layout.DenNear(x, z) is { } den) notes.Append(notes.Length > 0 ? ", " : "").Append($"in a {den.Kind} den ({(int)Math.Sqrt((den.X - x) * (den.X - x) + (den.Z - z) * (den.Z - z))} from its heart)");
        if (notes.Length > 0) sb.AppendLine(notes.ToString());

        double stability = player.WatchedAttributes.GetDouble("temporalStability", 1);
        sb.Append($"Stability here {layout.StabilityAt(player.Pos.X, player.Pos.Y, player.Pos.Z, geometry.FloorY):0.00}, yours {stability:0.00}");
        sb.AppendLine($"   temperature {layout.TemperatureAt(x, (int)player.Pos.Y, z, geometry.FloorY):0}°C");
        float awake = Needs.Needs.AwakeHours(player);
        string band = awake >= Needs.Needs.DeadHours ? "dead on feet" : awake >= Needs.Needs.ExhaustedHours ? "exhausted" : awake >= Needs.Needs.DrowsyHours ? "drowsy" : "fine";
        sb.Append($"hydration {Needs.Needs.Hydration(player):0}  awake {awake:0.0} h ({band}{(Needs.Needs.Caffeinated(player) ? ", caffeinated" : "")})");

        SingleComposer.GetDynamicText("text").SetNewText(sb.ToString());
    }
}
