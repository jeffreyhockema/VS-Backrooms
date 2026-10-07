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
/// black, with the odd flash as the power fights back) and a Level 1 Flickering (the same, round the player only),
/// blinks to black for a moment when the player is carried somewhere else by an elevator, a pit or a door that opens
/// onto the wrong place, and names each level as the player enters it.
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
        // Level 37: clear, pale and faintly teal, the white tile showing a long way off
        new(0.0035f, 0.86f, 0.93f, 0.91f, 0f),
        // Level 94: a bright, saturated day (and night) of its own, clear to the painted backdrop
        new(0.0022f, 0.62f, 0.78f, 0.95f, 0f, sceneWeight: 0f, openSky: true),
    };

    /// <summary>Level 37.1, the Sanguine Reservoir: close, dark and red.</summary>
    private static readonly Atmosphere Reservoir = new(0.03f, 0.18f, 0.02f, 0.03f, 0f);

    /// <summary>Level 94's castle: nothing in here is animated, and the air is plain; its blinding halls are white.</summary>
    private static readonly Atmosphere Castle = new(0.004f, 0.90f, 0.88f, 0.86f, 0f);
    private static readonly Atmosphere Blinding = new(0.07f, 1f, 1f, 1f, 0f, scene: 1.3f);

    /// <summary>Title keys for the Reservoir (level-371) and the castle (level-941) in the lang file.</summary>
    private const int ReservoirKey = 371, CastleKey = 941;

    /// <summary>How far off the Reservoir's chanting is heard, and a siren pole's tune.</summary>
    private const int ChantHeard = 160, TuneHeard = 72;

    private ILoadedSound poolTone, sirenTune;
    private string sirenPlaying;
    private float nextChant = 6, nextPoolSound = 8;

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

    /// <summary>How far off, in Level 6, the stairs down can be heard: the faint sound of waves from below.</summary>
    private const int WavesHeard = 160;

    private ICoreClientAPI capi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private RealitySystem reality;
    private AmbientModifier fog;
    private float mangledFog;
    private static readonly float[] MangledGrey = { 0.36f, 0.38f, 0.41f };
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
    private float nextWaves = 4;
    private float flicker;
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
        bool reservoir = level == WorldLayout.Poolrooms && layout.IsReservoir(mx, mz);
        int bx = (int)Math.Floor(pos.X), bz = (int)Math.Floor(pos.Z);
        bool castle = level == WorldLayout.Motion && layout.InCastle(bx, bz) && pos.Y > geometry.FloorFor(level) + WorldLayout.MountainHeight - 1;
        bool blinding = castle && layout.TileAt(bx, bz).Zone == 4;
        Atmosphere target = snack ? Snackrooms : red ? RedRooms : reservoir ? Reservoir : blinding ? Blinding : castle ? Castle : Levels[level];
        AnnounceLevel(snack ? 61 : red ? RedRoomsKey : reservoir ? ReservoirKey : castle ? CastleKey : level);
        LevelSounds(dt, pos, level, reservoir, castle);

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

        // Reality Shift: the lights fail, with the odd flash as they fight back. A Level 1 Flickering does the same to
        // the player's own stretch of the Habitable Zone for a minute or two (the server sets when it ends)
        double flickerUntil = entity.WatchedAttributes.GetDouble(Entities.MenaceSystem.FlickerKey, -1);
        float flickerTarget = level is 1 or 2 && capi.World.Calendar.TotalHours < flickerUntil ? 0.85f : 0f;
        flicker += (flickerTarget - flicker) * Math.Min(1f, dt * (flickerTarget > flicker ? 6f : 1.5f));
        if (flicker < 0.01f) flicker = 0f;
        float shift = Math.Max((float)(reality?.ShiftStrength ?? 0), flicker);
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
        else if (level == WorldLayout.Poolrooms && entity.IsEyesSubmerged())
        {
            // Under the Poolrooms' water: clear teal, darker the deeper you go; in the Reservoir, red and close
            float deep = GameMath.Clamp((float)(geometry.FloorFor(level) - pos.Y) / 20f, 0f, 1f);
            density = reservoir ? 0.09f : GameMath.Lerp(0.035f, 0.09f, deep);
            groundFog = 0f;
            targetColor[0] = reservoir ? 0.14f : GameMath.Lerp(0.30f, 0.03f, deep);
            targetColor[1] = reservoir ? 0.01f : GameMath.Lerp(0.62f, 0.10f, deep);
            targetColor[2] = reservoir ? 0.02f : GameMath.Lerp(0.56f, 0.12f, deep);
        }
        // The Mangled's weather: a cold grey fog closing in round the player (the server says how thick)
        float mangled = entity.WatchedAttributes.GetFloat(Entities.MangledEvent.FogKey, 0f);
        mangledFog += (mangled - mangledFog) * Math.Min(1f, dt * 0.8f);
        if (mangledFog > 0.01f)
        {
            density = GameMath.Lerp(density, 0.075f, mangledFog);
            fogMin = Math.Max(fogMin, 0.3f * mangledFog);
            groundFog = GameMath.Lerp(groundFog, -0.2f, mangledFog);
            for (int i = 0; i < 3; i++) targetColor[i] = GameMath.Lerp(targetColor[i], MangledGrey[i], mangledFog);
        }
        reveal = Math.Max(0f, reveal - dt * 5f);

        // Under water anywhere else, let the game's own water fog through
        float ownTarget = level is not (7 or WorldLayout.Poolrooms) && entity.IsEyesSubmerged() ? 0f : 1f;

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

    /// <summary>
    /// The sounds of Levels 37 and 94. In the Poolrooms: the soft wash of the water everywhere, a drip or a lap now and
    /// then, and from the way the nearest Reservoir lies, a chanting that grows as you near it. In Motion: by day the
    /// nearest siren pole's tune (slowed and gone flat in the last hours of the afternoon); at dusk it stops.
    /// </summary>
    private void LevelSounds(float dt, EntityPos pos, int level, bool reservoir, bool castle)
    {
        // The Poolrooms' room tone
        bool pool = level == WorldLayout.Poolrooms;
        if (pool && poolTone == null)
        {
            poolTone = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/poolroom"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = 0.45f, SoundType = EnumSoundType.Ambient,
            });
            poolTone?.Start();
        }
        else if (!pool && poolTone != null)
        {
            poolTone.Stop();
            poolTone.Dispose();
            poolTone = null;
        }
        if (pool)
        {
            nextPoolSound -= dt;
            if (nextPoolSound <= 0)
            {
                nextPoolSound = 7 + (float)rand.NextDouble() * 14;
                double yaw = rand.NextDouble() * Math.PI * 2, dist = 5 + rand.NextDouble() * 12;
                string what = rand.NextDouble() < 0.6 ? "pooldrip" : "poollap";
                // Now and then, in the dark, the water swells until it drowns out everything else
                bool swell = layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)).Detail == WorldLayout.PoolDark && rand.NextDouble() < 0.2;
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/" + (swell ? "poollap" : what)), pos.X + Math.Sin(yaw) * dist,
                    pos.Y + 0.5, pos.Z + Math.Cos(yaw) * dist, null, randomizePitch: true, range: 32, volume: swell ? 1f : 0.45f);
            }
            nextChant -= dt;
            if (nextChant <= 0)
            {
                nextChant = 10 + (float)rand.NextDouble() * 6; // the chant runs nine seconds
                if (layout.NearestReservoir((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z), ChantHeard) is { } far)
                {
                    double dx = far.X + 0.5 - pos.X, dz = far.Z + 0.5 - pos.Z, away = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
                    double at = Math.Min(away, 8);
                    float closeness = reservoir ? 1f : (float)Math.Max(0, 1 - away / ChantHeard);
                    capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/chant"), pos.X + dx / away * at, pos.Y + 0.5, pos.Z + dz / away * at,
                        null, randomizePitch: false, range: 24, volume: 0.05f + 0.45f * closeness * closeness);
                }
            }
        }

        // Motion's siren poles, by day
        string tune = null;
        (int X, int Z)? pole = null;
        if (level == WorldLayout.Motion && !castle && !Regions.MotionSystem.IsNight(capi.World.Calendar))
        {
            pole = layout.NearestSirenPole((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z), TuneHeard);
            if (pole != null) tune = Regions.MotionSystem.IsDusk(capi.World.Calendar) ? "sirentune-dusk" : "sirentune";
        }
        if (tune != sirenPlaying || tune != null && sirenTune != null && sirenTune.Params.Position is { } at0
            && (Math.Abs(at0.X - (pole.Value.X + 0.5)) > 1 || Math.Abs(at0.Z - (pole.Value.Z + 0.5)) > 1))
        {
            sirenTune?.Stop();
            sirenTune?.Dispose();
            sirenTune = null;
            sirenPlaying = tune;
            if (tune != null)
            {
                int ground = geometry.FloorFor(level) + layout.TileAt(pole.Value.X, pole.Value.Z).Height;
                sirenTune = capi.World.LoadSound(new SoundParams
                {
                    Location = new AssetLocation("backrooms:sounds/ambient/" + tune), ShouldLoop = true, DisposeOnFinish = false,
                    Position = new Vec3f(pole.Value.X + 0.5f, ground + 3.5f, pole.Value.Z + 0.5f), Range = TuneHeard, Volume = 0.9f,
                    SoundType = EnumSoundType.Ambient,
                });
                sirenTune?.Start();
            }
        }
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

    /// <summary>
    /// In Level 6's dark: the odd flash of the real place around you, things heard but never seen, and, if there are
    /// stairs down anywhere near, the faint sound of waves from the way they lie, louder the nearer you come.
    /// </summary>
    private void DarkEvents(float dt, EntityPos pos)
    {
        if (rand.NextDouble() < dt / 75.0) reveal = 1f;

        nextWaves -= dt;
        if (nextWaves <= 0)
        {
            nextWaves = 13 + (float)rand.NextDouble() * 8; // the sound runs twelve seconds
            if (layout.NearestDescent((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z), WavesHeard) is { } stairs)
            {
                double dx = stairs.X + 0.5 - pos.X, dz = stairs.Z + 0.5 - pos.Z, away = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
                // Played a little way off toward the stairs, so it has a direction even when they are far out of range
                double at = Math.Min(away, 8);
                float closeness = (float)Math.Max(0, 1 - away / WavesHeard);
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/waves"),
                    pos.X + dx / away * at, pos.Y + 0.5, pos.Z + dz / away * at, null, randomizePitch: false, range: 24, volume: 0.06f + 0.5f * closeness * closeness);
            }
        }

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
