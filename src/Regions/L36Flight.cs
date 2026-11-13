using System;
using System.Globalization;
using ProtoBuf;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;

namespace Backrooms.Regions;

/// <summary>
/// Level 36's flight status (the 2026-11-13 flight status pass; docs/design/experimental-levels/36-plan.md, "Flight status pass").
/// What a flight is doing, said plainly at every step: the states in the order a flight goes through them, the server's once a
/// second packet that names the state and the real seconds to its next change (<see cref="L36StatusPacket"/>), the HUD line
/// that draws it near the top of the screen while the player is at a gate or aboard, and the camera shake and cabin sound
/// that go with the state on the client. The server's side is L36System.Status.cs.
/// </summary>
public enum L36State
{
    /// <summary>At a gate, the flight not yet boarding: how long until it boards.</summary>
    Scheduled,
    /// <summary>The doors are open: how long until they close.</summary>
    Boarding,
    /// <summary>The last seconds of boarding.</summary>
    FinalCall,
    /// <summary>From here on aboard and in the air or on the way: the seconds are the time left to the landing.</summary>
    DoorsClosed,
    Pushback,
    Takeoff,
    Climb,
    Cruise,
    Descent,
    Landed,
    /// <summary>At the gate just after the plane left without you: when the next flight boards.</summary>
    Departed,
    /// <summary>Gate C32's flight, which never boards.</summary>
    Delayed,
}

/// <summary>The status line the server sends a player at a gate or aboard (State -1: none, clear the line).</summary>
[ProtoContract]
public class L36StatusPacket
{
    [ProtoMember(1)] public int State;
    [ProtoMember(2)] public string Number;
    [ProtoMember(3)] public int Destination;
    [ProtoMember(4)] public string Gate;
    /// <summary>Real seconds until the state's clock runs out (boards in, doors close in, landing in; for a delayed flight, the seconds to its boarding, shown as years).</summary>
    [ProtoMember(5)] public long Seconds;
}

/// <summary>The timeline of a flight in real milliseconds from the doors closing, and its names.</summary>
public static class L36Timeline
{
    public const long FlightMs = 70_000;
    /// <summary>When each of DoorsClosed to Landed begins.</summary>
    private static readonly long[] Starts = { 0, 6_000, 14_000, 26_000, 36_000, 54_000, 64_000 };
    /// <summary>How long a gate shows the plane gone (<see cref="L36State.Departed"/>), and the final call's length, in real seconds.</summary>
    public const double DepartedSeconds = 25, FinalCallSeconds = 20;

    public static L36State At(long elapsedMs)
    {
        int i = 0;
        while (i + 1 < Starts.Length && elapsedMs >= Starts[i + 1]) i++;
        return L36State.DoorsClosed + i;
    }

    public static long Start(L36State state) => Starts[Math.Clamp((int)state - (int)L36State.DoorsClosed, 0, Starts.Length - 1)];

    public static bool InFlight(L36State s) => s is >= L36State.DoorsClosed and <= L36State.Landed;

    public static string Name(L36State s) => s.ToString().ToLowerInvariant();

    /// <summary>A clock for a few minutes: 1:42, or 1:05:09 from an hour.</summary>
    public static string Clock(long seconds)
    {
        seconds = Math.Max(0, seconds);
        return seconds >= 3600
            ? string.Format(CultureInfo.InvariantCulture, "{0}:{1:00}:{2:00}", seconds / 3600, seconds / 60 % 60, seconds % 60)
            : string.Format(CultureInfo.InvariantCulture, "{0}:{1:00}", seconds / 60, seconds % 60);
    }

    public static double Years(long seconds) => seconds / 31_557_600.0;
}

/// <summary>Client side of the flight status: keeps the latest packet, draws the HUD line, shakes the camera, sets the cabin's loudness.</summary>
public class L36ClientSystem : ModSystem
{
    public const string Channel = "backrooms-l36";

    /// <summary>The state now on the client's screen, or -1.</summary>
    public static int CurrentState { get; private set; } = -1;

    /// <summary>How loud the cabin's loop is for the state (the climb and the cruise are louder than the ground).</summary>
    public static float CabinVolume => CurrentState switch
    {
        (int)L36State.Takeoff => 0.7f,
        (int)L36State.Climb => 0.65f,
        (int)L36State.Cruise => 0.6f,
        (int)L36State.Descent => 0.55f,
        (int)L36State.Pushback => 0.42f,
        _ => 0.35f,
    };

    private ICoreClientAPI capi;
    private HudL36Flight hud;
    private L36StatusPacket packet;
    private long arrivedMs, stateSinceMs, lastShakeMs;
    private string shown;

    public override bool ShouldLoad(EnumAppSide side) => true;

    public override void Start(ICoreAPI api)
    {
        api.Network.RegisterChannel(Channel).RegisterMessageType<L36StatusPacket>();
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Network.GetChannel(Channel).SetMessageHandler<L36StatusPacket>(OnPacket);
        api.Event.LevelFinalize += () =>
        {
            if (!BackroomsWorld.IsBackroomsClimate(api.World.Config) || hud != null) return;
            hud = new HudL36Flight(api);
            api.Event.RegisterGameTickListener(OnTick, 200);
        };
    }

    public override void Dispose()
    {
        hud?.Dispose();
        hud = null;
        CurrentState = -1;
    }

    private void OnPacket(L36StatusPacket p)
    {
        long now = capi.ElapsedMilliseconds;
        if (p.State < 0)
        {
            packet = null;
            CurrentState = -1;
            return;
        }
        if (p.State != CurrentState) stateSinceMs = now;
        packet = p;
        arrivedMs = now;
        CurrentState = p.State;
    }

    private void OnTick(float dt)
    {
        if (hud == null) return;
        long now = capi.ElapsedMilliseconds;
        // (A server that stops talking, or a player taken out of the level, loses the line after a few seconds)
        if (packet != null && now - arrivedMs > 4000) { packet = null; CurrentState = -1; }
        if (packet == null)
        {
            shown = null;
            if (hud.IsOpened()) hud.TryClose();
            return;
        }
        var state = (L36State)packet.State;
        long left = Math.Max(0, packet.Seconds - (now - arrivedMs) / 1000);
        string name = L36Timeline.Name(state);
        string time = state == L36State.Delayed
            ? Lang.Get("backrooms:l36-hud-years", Math.Max(1, (int)Math.Round(L36Timeline.Years(packet.Seconds))))
            : L36Timeline.Clock(left);
        string text = Lang.Get("backrooms:l36-hud-" + name, packet.Number, packet.Destination, packet.Gate, time);
        if (text != shown)
        {
            shown = text;
            hud.Show(text, Color(state));
        }
        if (!hud.IsOpened()) hud.TryOpen();
        Shake(state, now);
    }

    /// <summary>The camera shake of the flight, by state: a lurch at the pushback, the roll and the climb, a touch at the descent, the hard landing.</summary>
    private void Shake(L36State state, long now)
    {
        float strength = 0;
        long since = now - stateSinceMs;
        switch (state)
        {
            case L36State.Pushback: strength = since > 4500 ? 0.05f : 0.015f; break;
            case L36State.Takeoff: strength = since < 7000 ? 0.07f + 0.05f * Math.Min(1f, since / 6000f) : 0.04f; break;
            case L36State.Climb: strength = since < 4000 ? 0.045f : 0.02f; break;
            case L36State.Descent: strength = since > 5000 ? 0.04f : 0.015f; break;
            case L36State.Landed: strength = since < 1800 ? 0.2f : since < 4500 ? 0.06f : 0; break;
        }
        if (strength <= 0 || now - lastShakeMs < 200) return;
        lastShakeMs = now;
        capi.World.AddCameraShake(strength);
    }

    private static double[] Color(L36State state) => state switch
    {
        L36State.Boarding or L36State.Landed => new[] { 0.55, 1.0, 0.6, 1.0 },
        L36State.FinalCall => new[] { 1.0, 0.78, 0.25, 1.0 },
        L36State.DoorsClosed or L36State.Pushback or L36State.Takeoff => new[] { 1.0, 0.62, 0.45, 1.0 },
        L36State.Climb or L36State.Cruise or L36State.Descent => new[] { 0.65, 0.85, 1.0, 1.0 },
        L36State.Delayed or L36State.Departed => new[] { 0.8, 0.8, 0.8, 1.0 },
        _ => new[] { 1.0, 1.0, 1.0, 1.0 },
    };
}

/// <summary>The flight's status line, centred near the top of the screen. Reads nothing and takes no input.</summary>
public class HudL36Flight : HudElement
{
    private const int Width = 1200, Height = 36;
    private readonly CairoFont font;

    public HudL36Flight(ICoreClientAPI capi) : base(capi)
    {
        font = new CairoFont
        {
            Color = new[] { 1.0, 1.0, 1.0, 1.0 }, Fontname = GuiStyle.StandardFontName, UnscaledFontsize = 26, FontWeight = Cairo.FontWeight.Bold,
            Orientation = EnumTextOrientation.Center, LineHeightMultiplier = 1,
        };
        ElementBounds textBounds = ElementBounds.Fixed(0, 4, Width, Height);
        ElementBounds bgBounds = textBounds.ForkBoundingParent(8, 6, 8, 6);
        ElementBounds dialogBounds = bgBounds.ForkBoundingParent().WithAlignment(EnumDialogArea.CenterTop).WithFixedAlignmentOffset(0, 95);
        SingleComposer = capi.Gui.CreateCompo("backrooms-l36flight", dialogBounds)
            .AddGameOverlay(bgBounds, new[] { 0.0, 0.0, 0.0, 0.62 })
            .AddDynamicText("", font, textBounds, "text")
            .Compose();
    }

    public override string ToggleKeyCombinationCode => null;
    public override bool Focusable => false;
    public override bool ShouldReceiveMouseEvents() => false;
    public override bool ShouldReceiveKeyboardEvents() => false;

    public void Show(string text, double[] color)
    {
        font.Color = color;
        SingleComposer.GetDynamicText("text").SetNewText(text, false, true);
    }
}
