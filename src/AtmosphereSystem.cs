using System;
using System.Collections.Generic;
using Backrooms.Reality;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Per-level fog on the client, blended smoothly as the player crosses from one level into the next: a faint warm
/// haze in Level 0, grey fog with a low ground fog over Level 1's concrete, a dark murk in Level 2, and so on. The
/// enclosed levels ignore the outside world's day and night; the Suburbs are always night, and Level 10's sky is
/// always overcast.
///
/// Level 6 is darkness that light barely reaches: a candle shows the floor at your feet, a torch a few steps, a
/// lantern a stretch of corridor, and now and then the dark lifts for a heartbeat to show where you really are,
/// while something scuttles, breathes or whispers out in it. Level 7 darkens as you dive.
///
/// It also darkens the world during a Reality Shift (the lights fail: everything beyond a few steps is lost in
/// black, with the odd flash as the power fights back), blinks to black for a moment when the player is carried
/// somewhere else by an elevator, a pit or a door that opens onto the wrong place, and names each level as the
/// player enters it.
/// </summary>
public class AtmosphereSystem : ModSystem
{
    private readonly struct Atmosphere
    {
        /// <summary>
        /// GroundFog is vanilla's flat fog density. It must be negative for fog that thickens below the fog
        /// surface; positive values fog everything above it instead. Scene is how bright the world is, applied with
        /// SceneWeight (1 on enclosed levels, so the outside night never reaches them). Clouds are only applied
        /// where they are not negative.
        /// </summary>
        public readonly float Density, R, G, B, GroundFog, Scene, SceneWeight, Clouds;

        /// <summary>Open-sky levels let the vanilla day and night tint their fog; enclosed levels keep their own.</summary>
        public readonly bool OpenSky;

        public Atmosphere(float density, float r, float g, float b, float groundFog, float scene = 1, float sceneWeight = 1, float clouds = -1, bool openSky = false)
        {
            Density = density; R = r; G = g; B = b; GroundFog = groundFog; Scene = scene; SceneWeight = sceneWeight; Clouds = clouds; OpenSky = openSky;
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
        // Level 6: black (thinned by whatever light the player holds; see OnTick)
        new(0.30f, 0.005f, 0.005f, 0.008f, 0f),
        // Level 7: a cold blue sea mist under the ceiling
        new(0.012f, 0.10f, 0.20f, 0.30f, -0.3f),
        // Level 8: close, dusty brown air in the tunnels
        new(0.030f, 0.17f, 0.13f, 0.09f, 0f),
        // Level 9: a suburban night that never ends, a mist lying in its streets
        new(0.010f, 0.05f, 0.06f, 0.12f, -0.22f, scene: 0.32f, openSky: true),
        // Level 10: a flat grey overcast over the fields, a little dimmer than a clear day, and a thin ground fog
        new(0.006f, 0.62f, 0.64f, 0.66f, -0.14f, scene: 0.6f, sceneWeight: 0.35f, clouds: 0.95f, openSky: true),
        // Level 11: the city's own day and night, under a thin haze that softens the towers at a distance
        new(0.0045f, 0.70f, 0.72f, 0.76f, 0f, sceneWeight: 0f, openSky: true),
    };

    /// <summary>Level 6.1: bright, warm and clean, the food court lights all on.</summary>
    private static readonly Atmosphere Snackrooms = new(0.002f, 0.95f, 0.85f, 0.68f, 0f);

    /// <summary>Level 0's Red Rooms: close, dim and red.</summary>
    private static readonly Atmosphere RedRooms = new(0.035f, 0.30f, 0.03f, 0.02f, 0f);

    /// <summary>The key the Red Rooms' title is kept under (level-redrooms in the lang file).</summary>
    private const int RedRoomsKey = 1000;

    /// <summary>Height of the ground fog's surface above the floor, in blocks.</summary>
    private const float GroundFogHeight = 1.3f;

    // A full Reality Shift: thick black fog, and a floor of darkness even on things close by
    private const float BlackoutDensity = 0.12f;
    private const float BlackoutFogMin = 0.62f;
    // Being carried somewhere else: a moment of real black
    private const float BlinkFogMin = 0.97f;

    // Level 6's dark, without a light and with the brightest lantern. Held light is scaled from a candle up.
    private const float DarkFogMin = 0.5f, LitDarkDensity = 0.06f, LitDarkFogMin = 0.08f;
    private const float DimmestLight = 5f, BrightestLight = 20f;

    /// <summary>How long before a level's (or zone's) title is shown again, so walking along a border doesn't keep showing it.</summary>
    private const double TitleCooldownSeconds = 300;

    private static readonly string[] DarkSounds = { "scuttle", "breath", "whisper" };

    private ICoreClientAPI capi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private RealitySystem reality;
    private AmbientModifier fog;
    private readonly Random rand = new();

    // The level's own atmosphere, eased towards as the player moves; darkness is laid over it
    private float baseDensity, baseFogMin, baseScene = 1, sceneWeight = 1, baseClouds, cloudWeight, fogBrightWeight = 1, ownWeight = 1;
    private readonly float[] baseColor = new float[3];
    private readonly float[] targetColor = new float[3];
    private bool snapNext = true;

    private Vec3d lastPos;
    private float blink;
    private float flash;
    private float reveal;
    private float nextDarkSound = 20;
    private bool shiftWasActive, shiftSeen;

    // Which level the player was last in, and when each level's name was last shown
    private int lastLevelKey = -1;
    private readonly Dictionary<int, double> titleShownAt = new();

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
        fog.SceneBrightness = WeightedFloat.New(1f, 1f);
        fog.FogBrightness = WeightedFloat.New(1f, 1f);
        fog.CloudDensity = WeightedFloat.New(0f, 0f);
        fog.CloudBrightness = WeightedFloat.New(0.75f, 0f);
        capi.Ambient.CurrentModifiers["backrooms"] = fog;

        capi.Event.RegisterGameTickListener(OnTick, 50);
    }

    private void OnTick(float dt)
    {
        EntityPlayer entity = capi.World.Player?.Entity;
        EntityPos pos = entity?.Pos;
        if (pos == null) return;

        int mx = WorldLayout.MacroOf((int)Math.Floor(pos.X)), mz = WorldLayout.MacroOf((int)Math.Floor(pos.Z));
        int level = Math.Min(layout.LevelAt(mx, mz), Levels.Length - 1);
        bool snack = level == 6 && layout.IsSnackrooms(mx, mz);
        bool spectator = capi.World.Player.WorldData.CurrentGameMode == EnumGameMode.Spectator;
        bool dark = level == 6 && !snack && !spectator;
        bool red = level == 0 && layout.IsRedRoom(mx, mz);
        Atmosphere target = snack ? Snackrooms : red ? RedRooms : Levels[level];
        AnnounceLevel(snack ? 61 : red ? RedRoomsKey : level);

        // A sudden jump means the player was carried somewhere else: blink to black, and arrive in the new
        // level's own air rather than easing into it
        if (lastPos != null && lastPos.SquareDistanceTo(pos.X, pos.Y, pos.Z) > 30 * 30)
        {
            blink = 1f;
            snapNext = true;
        }
        lastPos ??= new Vec3d();
        lastPos.Set(pos.X, pos.Y, pos.Z);
        blink = Math.Max(0f, blink - dt / 1.5f);

        // Reality Shift: the lights fail, with the odd flash as they fight back
        float shift = (float)(reality?.ShiftStrength ?? 0);
        // (A shift already under way when the player joins makes no sound)
        if (!shiftSeen) { shiftWasActive = shift > 0; shiftSeen = true; }
        if (shift > 0 && !shiftWasActive)
        {
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/powerdown"), entity, null, randomizePitch: false, range: 32, volume: 0.8f);
        }
        shiftWasActive = shift > 0;
        if (shift > 0 && rand.NextDouble() < dt * (shift < 1 ? 2.5 : 0.25)) flash = 1f;
        flash = Math.Max(0f, flash - dt * 6f);
        float black = Math.Max(blink, shift * (1f - 0.8f * flash));

        float density = target.Density, fogMin = 0f, groundFog = target.GroundFog;
        targetColor[0] = target.R; targetColor[1] = target.G; targetColor[2] = target.B;
        if (dark)
        {
            // Light barely carries here: a candle shows your feet, a torch a few steps, a lantern a stretch of corridor
            byte[] hsv = entity.LightHsv;
            float held = GameMath.Clamp(((hsv?[2] ?? 0) - DimmestLight) / (BrightestLight - DimmestLight), 0f, 1f);
            density = GameMath.Lerp(target.Density, LitDarkDensity, held);
            fogMin = GameMath.Lerp(DarkFogMin, LitDarkFogMin, (float)Math.Sqrt(held));
            DarkEvents(dt, pos);
        }
        else if (level == 7 && pos.Y < geometry.FloorY + 1)
        {
            // Diving: the water turns from blue to black through the twilight and midnight zones. The mist over
            // the surface would hide all of it, so it goes.
            float deep = GameMath.Clamp((float)(geometry.FloorY - pos.Y) / 55f, 0f, 1f);
            density = GameMath.Lerp(0.03f, 0.16f, deep);
            fogMin = 0.45f * deep;
            groundFog = 0f;
            for (int i = 0; i < 3; i++) targetColor[i] = GameMath.Lerp(targetColor[i], 0.003f, deep);
        }
        reveal = Math.Max(0f, reveal - dt * 5f);

        // Under water anywhere else, let the game's own water fog through
        float ownTarget = level != 7 && entity.IsEyesSubmerged() ? 0f : 1f;

        // Ease towards the level's own atmosphere over a couple of seconds (faster in and out of the dark);
        // darkness is applied on top at once
        float k = snapNext ? 1f : Math.Min(1f, dt * (dark || baseFogMin > 0.2f ? 3f : 0.6f));
        snapNext = false;
        baseDensity += (density - baseDensity) * k;
        baseFogMin += (fogMin - baseFogMin) * k;
        for (int i = 0; i < 3; i++) baseColor[i] += (targetColor[i] - baseColor[i]) * k;
        baseScene += (target.Scene - baseScene) * k;
        sceneWeight += (target.SceneWeight - sceneWeight) * k;
        fogBrightWeight += ((target.OpenSky ? 0f : 1f) - fogBrightWeight) * k;
        baseClouds += ((target.Clouds >= 0 ? target.Clouds : 0f) - baseClouds) * k;
        cloudWeight += ((target.Clouds >= 0 ? 1f : 0f) - cloudWeight) * k;
        ownWeight += (ownTarget - ownWeight) * Math.Min(1f, dt * 4f);

        // A Level 6 reveal briefly lifts the dark altogether
        float d = GameMath.Lerp(baseDensity, 0.004f, reveal), m = GameMath.Lerp(baseFogMin, 0f, reveal);
        fog.FogDensity.Value = GameMath.Lerp(d, BlackoutDensity, black);
        fog.FogDensity.Weight = ownWeight;
        float[] fogColor = fog.FogColor.Value;
        for (int i = 0; i < 3; i++) fogColor[i] = GameMath.Lerp(baseColor[i], 0.01f, black);
        fog.FogColor.Weight = ownWeight;
        fog.FogMin.Value = Math.Max(m, Math.Max(BlackoutFogMin * shift * (1f - 0.8f * flash), BlinkFogMin * blink));
        fog.FogMin.Weight = ownWeight;
        fog.SceneBrightness.Value = baseScene;
        fog.SceneBrightness.Weight = sceneWeight;
        fog.FogBrightness.Weight = fogBrightWeight;
        fog.CloudDensity.Value = baseClouds;
        fog.CloudDensity.Weight = cloudWeight;
        fog.CloudBrightness.Weight = cloudWeight;

        fog.FlatFogDensity.Value += (groundFog - fog.FlatFogDensity.Value) * Math.Max(k, Math.Min(1f, dt * 2f));
        // Flat fog height is relative to sea level, which the server sets to the floor; compute it absolutely anyway
        fog.FlatFogYPos.Value = geometry.FloorY + GroundFogHeight - capi.World.SeaLevel;
    }

    /// <summary>Names the level the player has just walked or fallen into, with a word of advice for the worst.</summary>
    private void AnnounceLevel(int key)
    {
        if (key == lastLevelKey) return;
        bool first = lastLevelKey < 0;
        lastLevelKey = key;
        double now = capi.World.ElapsedMilliseconds / 1000.0;
        if (titleShownAt.TryGetValue(key, out double shown) && now - shown < TitleCooldownSeconds) return;
        titleShownAt[key] = now;
        // On joining, wait a moment so the title is not lost behind the loading screen
        capi.Event.RegisterCallback(_ =>
        {
            string name = key == RedRoomsKey ? "redrooms" : key.ToString();
            string text = Lang.Get("backrooms:level-" + name);
            string hintKey = "backrooms:levelhint-" + name;
            if (Lang.HasTranslation(hintKey)) text += "\n" + Lang.Get(hintKey);
            capi.TriggerIngameDiscovery(this, "backrooms-level", text);
        }, first ? 3000 : 400);
    }

    /// <summary>In Level 6's dark: the odd flash of the real place around you, and things heard but never seen.</summary>
    private void DarkEvents(float dt, EntityPos pos)
    {
        if (rand.NextDouble() < dt / 75.0) reveal = 1f;

        nextDarkSound -= dt;
        if (nextDarkSound > 0) return;
        nextDarkSound = 25 + (float)rand.NextDouble() * 45;
        string sound = DarkSounds[rand.Next(DarkSounds.Length)];
        // Breathing comes from right behind you (the player looks along -sin(yaw), -cos(yaw)); the rest from
        // somewhere off in the dark
        bool behind = sound == "breath";
        double dist = behind ? 1.5 : 6 + rand.NextDouble() * 8;
        double yaw = behind ? pos.Yaw + (rand.NextDouble() - 0.5) * 0.6 : rand.NextDouble() * Math.PI * 2;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/" + sound),
            pos.X + Math.Sin(yaw) * dist, pos.Y + 1.2, pos.Z + Math.Cos(yaw) * dist, null, randomizePitch: true, range: 24, volume: 0.7f);
    }
}
