using System;
using Backrooms.Reality;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Per-level fog on the client, blended smoothly as the player crosses from one level into the next: a faint warm
/// haze in Level 0, grey fog with a low ground fog over Level 1's concrete, a dark murk in Level 2, and so on.
///
/// It also darkens the world during a Reality Shift (the lights fail: everything beyond a few steps is lost in
/// black, with the odd flash as the power fights back), and blinks to black for a moment when the player is
/// carried somewhere else by an elevator, a pit or a door that opens onto the wrong place.
/// </summary>
public class AtmosphereSystem : ModSystem
{
    private readonly struct Atmosphere
    {
        /// <summary>
        /// GroundFog is vanilla's flat fog density. It must be negative for fog that thickens below the fog
        /// surface; positive values fog everything above it instead.
        /// </summary>
        public readonly float Density, R, G, B, GroundFog;

        public Atmosphere(float density, float r, float g, float b, float groundFog)
        {
            Density = density; R = r; G = g; B = b; GroundFog = groundFog;
        }
    }

    private static readonly Atmosphere[] Levels =
    {
        new(0.004f, 0.86f, 0.83f, 0.62f, 0f),
        new(0.009f, 0.55f, 0.57f, 0.57f, -0.55f),
        new(0.014f, 0.22f, 0.20f, 0.17f, 0f),
        // Level 3: hot, dusty amber gloom
        new(0.016f, 0.30f, 0.22f, 0.12f, 0f),
        // Level 4: cold grey storm light
        new(0.007f, 0.42f, 0.45f, 0.50f, 0f),
        // Level 5: warm, smoky hotel air
        new(0.008f, 0.36f, 0.24f, 0.14f, 0f),
    };

    /// <summary>Height of the ground fog's surface above the floor, in blocks.</summary>
    private const float GroundFogHeight = 1.3f;

    // A full Reality Shift: thick black fog, and a floor of darkness even on things close by
    private const float BlackoutDensity = 0.12f;
    private const float BlackoutFogMin = 0.62f;

    private ICoreClientAPI capi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private RealitySystem reality;
    private AmbientModifier fog;
    private readonly Random rand = new();

    // The level's own atmosphere, eased towards as the player moves; darkness is laid over it
    private float baseDensity = Levels[0].Density;
    private readonly float[] baseColor = { Levels[0].R, Levels[0].G, Levels[0].B };

    private Vec3d lastPos;
    private float blink;
    private float flash;
    private bool shiftWasActive;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Event.LevelFinalize += OnLevelFinalize;
    }

    private void OnLevelFinalize()
    {
        if (!BackroomsWorld.IsBackroomsClimate(capi.World.Config)) return;

        layout = BackroomsWorld.CreateLayout(capi.World);
        geometry = BackroomsWorld.CreateGeometry(capi.World);
        reality = capi.ModLoader.GetModSystem<RealitySystem>();

        fog = new AmbientModifier().EnsurePopulated();
        fog.FogDensity = WeightedFloat.New(Levels[0].Density, 1f);
        fog.FogColor = WeightedFloatArray.New(new[] { Levels[0].R, Levels[0].G, Levels[0].B }, 1f);
        fog.FogMin = WeightedFloat.New(0f, 1f);
        fog.FlatFogDensity = WeightedFloat.New(0f, 1f);
        fog.FlatFogYPos = WeightedFloat.New(0f, 1f);
        capi.Ambient.CurrentModifiers["backrooms"] = fog;

        capi.Event.RegisterGameTickListener(OnTick, 50);
    }

    private void OnTick(float dt)
    {
        EntityPos pos = capi.World.Player?.Entity?.Pos;
        if (pos == null) return;

        int level = Math.Min(layout.LevelAt(WorldLayout.MacroOf((int)pos.X), WorldLayout.MacroOf((int)pos.Z)), Levels.Length - 1);
        Atmosphere target = Levels[level];

        // A sudden jump means the player was carried somewhere else: blink to black
        if (lastPos != null && lastPos.SquareDistanceTo(pos.X, pos.Y, pos.Z) > 30 * 30) blink = 1f;
        lastPos ??= new Vec3d();
        lastPos.Set(pos.X, pos.Y, pos.Z);
        blink = Math.Max(0f, blink - dt / 1.5f);

        // Reality Shift: the lights fail, with the odd flash as they fight back
        float shift = (float)(reality?.ShiftStrength ?? 0);
        if (shift > 0 && !shiftWasActive)
        {
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/powerdown"), capi.World.Player.Entity, null, randomizePitch: false, range: 32, volume: 0.8f);
        }
        shiftWasActive = shift > 0;
        if (shift > 0 && rand.NextDouble() < dt * (shift < 1 ? 2.5 : 0.25)) flash = 1f;
        flash = Math.Max(0f, flash - dt * 6f);
        float dark = Math.Max(blink, shift * (1f - 0.8f * flash));

        // Ease towards the level's own atmosphere over a couple of seconds; darkness is applied on top at once
        float k = Math.Min(1f, dt * 0.6f);
        baseDensity += (target.Density - baseDensity) * k;
        baseColor[0] += (target.R - baseColor[0]) * k;
        baseColor[1] += (target.G - baseColor[1]) * k;
        baseColor[2] += (target.B - baseColor[2]) * k;

        fog.FogDensity.Value = GameMath.Lerp(baseDensity, BlackoutDensity, dark);
        float[] color = fog.FogColor.Value;
        for (int i = 0; i < 3; i++) color[i] = GameMath.Lerp(baseColor[i], 0.01f, dark);
        fog.FogMin.Value = BlackoutFogMin * dark;

        fog.FlatFogDensity.Value += (target.GroundFog - fog.FlatFogDensity.Value) * k;
        // Flat fog height is relative to sea level, which the server sets to the floor; compute it absolutely anyway
        fog.FlatFogYPos.Value = geometry.FloorY + GroundFogHeight - capi.World.SeaLevel;
    }
}
