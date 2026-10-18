using System;
using ProtoBuf;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What a player sees and hears while a threshold carries them: the screen goes dark the moment it fires, stays dark
/// while the server loads (and if need be generates) the place they arrive and until the client has it, then clears.
/// Without it nothing seems to happen for the seconds the arrival takes. It is a smooth fade, never a flash, and it
/// reaches only the player who is travelling.
/// </summary>
public partial class ThresholdSystem
{
    public enum TransitionPhase
    {
        /// <summary>A threshold has fired: go dark and wait.</summary>
        Begin = 0,
        /// <summary>The player has been put down: clear as soon as the place is there.</summary>
        End = 1,
    }

    /// <summary>
    /// Server to client. Style is how they travel: <c>door</c> (the door's own sound already played), <c>walk</c>
    /// (stairs, tripwires, gates: footsteps), <c>fall</c> (pits, manholes, hatches: a rush of air), <c>elevator</c>
    /// (a chime on arrival) or empty (just the fade).
    /// </summary>
    [ProtoContract]
    public class TransitionPacket
    {
        [ProtoMember(1)] public int Phase;
        [ProtoMember(2)] public string Style;
    }

    private void SendTransition(IServerPlayer player, TransitionPhase phase, string style)
    {
        if (player.ConnectionState != EnumClientState.Playing) return;
        sapi.Network.GetChannel(Channel).SendPacket(new TransitionPacket { Phase = (int)phase, Style = style ?? "" }, player);
    }

    /// <summary>
    /// For the <c>/backrooms transitiontest</c> command: plays the effect for this player alone for a moment, without
    /// taking them anywhere.
    /// </summary>
    public void TransitionTest(IServerPlayer player, string style, int holdMs)
    {
        SendTransition(player, TransitionPhase.Begin, style);
        sapi.Event.RegisterCallback(_ => SendTransition(player, TransitionPhase.End, style), Math.Max(100, holdMs));
    }

    /// <summary>
    /// For the <c>/backrooms transitionbench</c> command: how long the server takes to load (and if need be generate)
    /// the chunk column around a block, which is what a threshold waits for before it moves anyone. The answer is
    /// written to the log and handed to <paramref name="done"/>.
    /// </summary>
    public void BenchLoad(int x, int z, Action<string> done)
    {
        long started = Environment.TickCount64;
        int cx = x / GlobalConstants.ChunkSize, cz = z / GlobalConstants.ChunkSize;
        sapi.WorldManager.LoadChunkColumnPriority(cx, cz, new ChunkLoadOptions
        {
            OnLoaded = () =>
            {
                string text = $"Chunk column {cx}, {cz} (around {x}, {z}) was ready after {Environment.TickCount64 - started} ms";
                sapi.Logger.Notification("[backrooms] {0}", text);
                done(text);
            },
        });
    }

    // ================= The client =================

    private ICoreClientAPI transitionApi;
    private TransitionRenderer transition;

    private void StartTransitionClient(ICoreClientAPI api)
    {
        transitionApi = api;
        transition = new TransitionRenderer(api);
        api.Event.RegisterRenderer(transition, EnumRenderStage.Ortho, "backrooms-transition");
        api.Network.GetChannel(Channel).SetMessageHandler<TransitionPacket>(packet =>
        {
            if (packet.Phase == (int)TransitionPhase.Begin) transition.Begin(packet.Style);
            else transition.End(packet.Style);
        });
        api.ChatCommands.Create("transitiontest")
            .WithDescription("Plays the screen effect of passing through a threshold without going anywhere: a style (door, walk, fall, elevator or plain, default walk) and how long to hold it in seconds (default 2)")
            .WithArgs(api.ChatCommands.Parsers.OptionalWord("style"), api.ChatCommands.Parsers.OptionalDouble("seconds", 2))
            .HandleWith(args =>
            {
                string style = args[0] as string ?? "walk";
                double seconds = Math.Clamp((double)args[1], 0.2, 15);
                transition.Begin(style);
                api.Event.RegisterCallback(_ => transition.End(style), (int)(seconds * 1000));
                return TextCommandResult.Success($"Transition ({style}) for {seconds:0.0} s");
            });
    }

    /// <summary>
    /// Draws the black the screen fades to. It comes in quickly (a fifth of a second) and goes out slowly (about half
    /// a second), with nothing flickering, and is held until the server has put the player down, the chunk under them
    /// has reached this client and a moment has passed since, or at most a few seconds, whatever happens.
    /// </summary>
    private sealed class TransitionRenderer : IRenderer
    {
        private const double FadeInSeconds = 0.2, FadeOutSeconds = 0.5, SettleSeconds = 0.3, GiveUpSeconds = 8;

        private readonly ICoreClientAPI capi;
        private readonly BlockPos probe = new(0);
        private int texture;
        private bool active, released;
        private double beganAt, releasedAt, alpha;
        private double lastFrameAt = -1;

        public TransitionRenderer(ICoreClientAPI capi) { this.capi = capi; }

        public double RenderOrder => 0.95;
        public int RenderRange => 0;

        private double Now => capi.World.ElapsedMilliseconds / 1000.0;

        public void Begin(string style)
        {
            // An elevator says so when its doors close and again when the car arrives: one fade, from the first
            if (active && !released) return;
            active = true;
            released = false;
            beganAt = Now;
            Cue(style, arriving: false);
        }

        public void End(string style)
        {
            if (!active || released) return;
            released = true;
            releasedAt = Now;
            Cue(style, arriving: true);
        }

        private void Cue(string style, bool arriving)
        {
            EntityPlayer self = capi.World.Player?.Entity;
            if (self == null) return;
            // The doors and vents have the sounds of their own; these are the rest
            string sound = (style, arriving) switch
            {
                ("fall", false) => "game:sounds/effect/swoosh",
                ("walk", false) => "game:sounds/walk/stone*",
                ("elevator", true) => "game:sounds/effect/receptionbell",
                _ => null,
            };
            if (sound == null) return;
            capi.World.PlaySoundAt(new AssetLocation(sound), self, capi.World.Player, randomizePitch: true, range: 8, volume: style == "elevator" ? 0.35f : 0.6f);
        }

        /// <summary>Whether the client has the chunk the player stands in (it does not until the server has sent it).</summary>
        private bool Arrived()
        {
            EntityPlayer self = capi.World.Player?.Entity;
            if (self == null) return false;
            probe.Set((int)Math.Floor(self.Pos.X), (int)Math.Floor(self.Pos.Y), (int)Math.Floor(self.Pos.Z));
            return capi.World.BlockAccessor.GetChunkAtBlockPos(probe) != null;
        }

        public void OnRenderFrame(float deltaTime, EnumRenderStage stage)
        {
            double now = Now;
            double dt = lastFrameAt < 0 ? 0 : Math.Min(0.25, now - lastFrameAt);
            lastFrameAt = now;
            if (!active && alpha <= 0) return;
            if (capi.World.Player?.Entity == null)
            {
                active = false;
                alpha = 0;
                return;
            }

            bool hold = active && now - beganAt < GiveUpSeconds && !(released && now - releasedAt >= SettleSeconds && Arrived());
            if (!hold) active = false;
            alpha = hold ? Math.Min(1, alpha + dt / FadeInSeconds) : Math.Max(0, alpha - dt / FadeOutSeconds);
            if (alpha <= 0) return;

            if (texture <= 0) texture = capi.Render.GetOrLoadTexture(new AssetLocation("backrooms", "textures/gui/transition.png"));
            if (texture <= 0) return;
            // Smoothed, so it starts and ends gently
            float a = (float)(alpha * alpha * (3 - 2 * alpha));
            capi.Render.Render2DTexture(texture, 0, 0, capi.Render.FrameWidth, capi.Render.FrameHeight, 50, new Vec4f(1, 1, 1, a));
        }

        public void Dispose() { }
    }
}
