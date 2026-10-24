using System;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;

namespace Backrooms.Needs;

/// <summary>
/// The Thirst and Rest meters, drawn in the same 850-wide CenterBottom frame as vanilla's HudStatbar (decompiled from
/// VintagestoryLib, 1.22.7: frame 850 x 100 at offset (0, 5); bars Statbar(corner, 850 * 0.41), height 10). Thirst sits
/// above hunger (RightTop, filling right to left), Rest above health (LeftTop), and moves up past the oxygen bar while
/// that is showing. Values are read from the watched trees through <see cref="Needs"/>; a missing tree reads as full, so
/// the bars are composed regardless and a 100 ms tick sets values and recomposes only when the layout changes.
/// </summary>
public class HudNeeds : HudElement
{
    private const float FrameWidth = 850f;
    private const double ThirstRestFlash = 0.2;

    private static readonly double[] ThirstColor = { 0.22, 0.52, 0.86, 0.9 };
    private static readonly double[] RestColor = { 0.56, 0.44, 0.78, 0.9 };

    private GuiElementStatbar thirstBar, restBar;
    private bool shownThirst, shownRest, composedOnce;
    private double composedRestOffset;
    private float hydration = Needs.MaxHydration, maxHydration = Needs.MaxHydration, rest = 1f;
    private float lastHydration = -1, lastMaxHydration = -1, lastRest = -1;
    private long listener;

    public HudNeeds(ICoreClientAPI capi) : base(capi)
    {
        listener = capi.Event.RegisterGameTickListener(OnTick, 100);
    }

    public override string ToggleKeyCombinationCode => null;
    public override bool Focusable => false;
    public override bool TryClose() => false;
    public override bool ShouldReceiveKeyboardEvents() => false;

    public override void OnOwnPlayerDataReceived()
    {
        Compose();
    }

    public override void Dispose()
    {
        capi.Event.UnregisterGameTickListener(listener);
        base.Dispose();
    }

    /// <summary>Whether the oxygen bar is showing: the breathe tree exists and is not full (vanilla hides it when full).</summary>
    private static bool OxygenShowing(EntityPlayer player)
    {
        ITreeAttribute tree = player.WatchedAttributes.GetTreeAttribute("oxygen");
        if (tree == null) return false;
        float? current = tree.TryGetFloat("currentoxygen"), max = tree.TryGetFloat("maxoxygen");
        return current.HasValue && max.HasValue && current.Value < max.Value;
    }

    private void OnTick(float dt)
    {
        IPlayer player = capi.World.Player;
        EntityPlayer entity = player?.Entity;
        if (entity == null) return;

        EnumGameMode mode = player.WorldData.CurrentGameMode;
        bool survival = mode != EnumGameMode.Creative && mode != EnumGameMode.Spectator;
        bool thirst = survival && Needs.ThirstOn(capi.World), fatigue = survival && Needs.FatigueOn(capi.World);
        double restOffset = OxygenShowing(entity) ? -35 : -15;

        if (!composedOnce || thirst != shownThirst || fatigue != shownRest || (fatigue && restOffset != composedRestOffset))
        {
            Compose(thirst, fatigue, restOffset);
        }

        hydration = Needs.Hydration(entity);
        maxHydration = Needs.MaxHydration;
        rest = Needs.RestFraction(entity);

        if (thirstBar != null)
        {
            if (hydration != lastHydration || maxHydration != lastMaxHydration)
            {
                thirstBar.SetLineInterval(100f);
                thirstBar.SetValues(hydration, 0f, maxHydration);
                lastHydration = hydration;
                lastMaxHydration = maxHydration;
            }
            thirstBar.ShouldFlash = hydration / maxHydration < ThirstRestFlash;
        }
        if (restBar != null)
        {
            if (rest != lastRest)
            {
                restBar.SetLineInterval(0.1f);
                restBar.SetValues(rest, 0f, 1f);
                lastRest = rest;
            }
            restBar.ShouldFlash = rest < ThirstRestFlash;
        }
    }

    private void Compose()
    {
        // Force a fresh compose on the next tick, which knows the modes and settings
        composedOnce = false;
        OnTick(0);
    }

    private void Compose(bool thirst, bool fatigue, double restOffset)
    {
        ElementBounds frame = new ElementBounds
        {
            Alignment = EnumDialogArea.CenterBottom,
            BothSizing = ElementSizing.Fixed,
            fixedWidth = FrameWidth,
            fixedHeight = 100.0
        }.WithFixedAlignmentOffset(0.0, 5.0);

        ElementBounds thirstBounds = ElementStdBounds.Statbar(EnumDialogArea.RightTop, FrameWidth * 0.41).WithFixedHeight(10.0).WithFixedAlignmentOffset(-1.0, -15.0);
        thirstBounds.WithFixedHeight(10.0);
        ElementBounds restBounds = ElementStdBounds.Statbar(EnumDialogArea.LeftTop, FrameWidth * 0.41).WithFixedHeight(10.0).WithFixedAlignmentOffset(0.0, restOffset);
        restBounds.WithFixedHeight(10.0);

        Composers["needs"] = capi.Gui.CreateCompo("backrooms-needs", frame.FlatCopy().FixedGrow(0.0, 20.0))
            .BeginChildElements(frame)
            .AddIf(thirst).AddInvStatbar(thirstBounds, ThirstColor, "thirstbar").EndIf()
            .AddIf(fatigue).AddStatbar(restBounds, RestColor, "restbar").EndIf()
            .EndChildElements()
            .Compose();

        thirstBar = thirst ? Composers["needs"].GetStatbar("thirstbar") : null;
        restBar = fatigue ? Composers["needs"].GetStatbar("restbar") : null;
        if (thirstBar != null)
        {
            thirstBar.onGetStatbarValue = () => Lang.Get("backrooms:hud-hydration", (int)Math.Round(hydration), (int)Math.Round(maxHydration));
        }
        if (restBar != null)
        {
            restBar.onGetStatbarValue = () => Lang.Get("backrooms:hud-rest", (int)Math.Round(rest * 100f));
        }

        shownThirst = thirst;
        shownRest = fatigue;
        composedRestOffset = restOffset;
        composedOnce = true;
        lastHydration = lastMaxHydration = lastRest = -1;
    }
}

/// <summary>Client side of the needs: opens the meters in a Backrooms world.</summary>
public class NeedsClientSystem : ModSystem
{
    private HudNeeds hud;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    public override void StartClientSide(ICoreClientAPI capi)
    {
        capi.Event.LevelFinalize += () =>
        {
            if (!BackroomsWorld.IsBackroomsClimate(capi.World.Config) || hud != null) return;
            hud = new HudNeeds(capi);
            hud.TryOpen();
        };
    }

    public override void Dispose()
    {
        hud?.Dispose();
        hud = null;
    }
}
