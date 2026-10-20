using System;
using System.Collections.Generic;
using System.Linq;
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
/// haze in Level 0, grey fog with a low ground fog over Level 1's concrete, a dark murk in Level 2, and so on. Every
/// level but 10, 11 and 94 ignores the outside world's day and night (its fog and ambient light are held at the day's);
/// the Suburbs are always night, and Level 10's sky is always overcast.
///
/// Level 6 is darkness that light barely reaches: a candle shows the floor at your feet, a torch a few steps, a
/// lantern a stretch of corridor, and now and then the dark lifts for a heartbeat to show where you really are,
/// while something scuttles, breathes or whispers out in it. Level 7 darkens as you dive.
///
/// It also darkens the world during a Reality Shift (the lights fail: everything beyond a few steps is lost in
/// black, with the odd flash as the power fights back) and a Level 1 Flickering (the same, round the player only),
/// blinks to black for a moment when the player is carried somewhere else by an elevator, a pit or a door that opens
/// onto the wrong place, and names each level as the player enters it.
///
/// The level's air is kept the last of the client's ambient modifiers (<see cref="KeepAirLast"/>), so it is what
/// shows wherever it has a say: the game's own low-stability fog, added later, used to be laid over it. Low stability
/// shows in the level's own air instead: as the player's own stability falls below 0.3 the fog thickens and goes a
/// dull, dark brown-grey of its own colour, and the world dims (<see cref="Strained"/>).
/// </summary>
public partial class AtmosphereSystem : ModSystem
{
    /// <summary>The key the level's air is kept under among the client's ambient modifiers.</summary>
    private const string ModifierKey = "backrooms";

    private readonly struct Atmosphere
    {
        /// <summary>
        /// GroundFog is vanilla's flat fog density. It must be negative for fog that thickens below the fog
        /// surface; positive values fog everything above it instead. Scene is how bright the world is, applied with
        /// SceneWeight (1 on enclosed levels, so the outside night never reaches them). Clouds are only applied
        /// where they are not negative, at CloudBrightness (vanilla's own clouds are lit by the outside day, which a
        /// level's night or overcast doesn't share). FogMin is a floor of fog on everything, the sky dome included:
        /// enough of it (with the density) and the whole sky takes the fog colour, sun and cloud edges gone.
        /// </summary>
        public readonly float Density, R, G, B, GroundFog, Scene, SceneWeight, Clouds, CloudBrightness, FogMin;

        /// <summary>
        /// The levels with the outside world's day and night (10, 11 and 94) let the vanilla day and night tint their fog
        /// and light their open ground. Every other level, the Suburbs' endless night and Level 188's open courtyard
        /// included, keeps its own at every hour: its fog brightness and its ambient light are held at the day's, so it
        /// looks at midnight as it does at noon.
        /// </summary>
        public readonly bool DayNight;

        public Atmosphere(float density, float r, float g, float b, float groundFog, float scene = 1, float sceneWeight = 1, float clouds = -1, bool dayNight = false,
            float cloudBrightness = 0.75f, float fogMin = 0f)
        {
            Density = density; R = r; G = g; B = b; GroundFog = groundFog; Scene = scene; SceneWeight = sceneWeight; Clouds = clouds; DayNight = dayNight;
            CloudBrightness = cloudBrightness; FogMin = fogMin;
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
        // Level 7: a thin, near-black sea mist under the ceiling: the distance fades into the dark rather than glowing
        // brighter than the dimly lit sea and ceiling (the mist on the water stays)
        new(0.008f, 0.03f, 0.05f, 0.08f, -0.3f),
        // Level 8: close, dusty brown air in the tunnels
        new(0.030f, 0.17f, 0.13f, 0.09f, 0f),
        // Level 9: a suburban night that never ends, a mist lying in its streets, under a thin deck of black cloud
        new(0.010f, 0.05f, 0.06f, 0.12f, -0.22f, scene: 0.32f, clouds: 0.4f, cloudBrightness: 0.08f),
        // Level 10: a flat, leaden overcast over the fields, a little dimmer than a clear day, and a thin ground fog. The
        // sky dome, the sun and the moon are hidden in a sphere of fog round the player (AtmosphereSystem.L10.cs), so the
        // fog itself can stay thin enough to see the hedges a long way off; a full cloud deck as grey as the fog. Now and
        // then a spell of thick fog comes over the fields for a few minutes, and lifts
        new(0.0075f, 0.60f, 0.61f, 0.62f, -0.14f, scene: 0.6f, sceneWeight: 0.35f, clouds: 1f, dayNight: true, cloudBrightness: 0.5f, fogMin: 0.02f),
        // Level 11: the city's own day and night, under a thin haze that softens the towers at a distance
        new(0.0045f, 0.70f, 0.72f, 0.76f, 0f, sceneWeight: 0f, dayNight: true),
        // Level 37: clear, pale and faintly teal, the white tile showing a long way off
        new(0.0035f, 0.86f, 0.93f, 0.91f, 0f),
        // Level 94: a bright, saturated day (and night) of its own, clear to the painted backdrop: a film set has no haze,
        // and the castle on its mountain shows on the horizon (MotionLandmark.cs draws it past the view distance)
        new(0.0016f, 0.62f, 0.78f, 0.95f, 0f, sceneWeight: 0f, dayNight: true),
        // The five kept as 14-18, each level's own line (placeholders: a faint neutral haze). Parts of a level with air of
        // their own are swapped in by its AtmosphereSystem.<level>.cs
        // Level !: a close red murk, the EXIT signs repeating into it (it pulses with the alarm: AtmosphereSystem.Run.cs)
        new(0.022f, 0.30f, 0.04f, 0.04f, 0f),
        // Level Fun: warm and a little dusty, like any party venue (its open decks: AtmosphereSystem.Fun.cs)
        new(0.004f, 0.96f, 0.90f, 0.74f, 0f),
        // The End: still, cool and dry, a thin neutral haze with the faint cool cast of fluorescent tubes, like the
        // photographs' (its fake realities, distortions and lights-out: AtmosphereSystem.End.cs)
        new(0.0035f, 0.80f, 0.81f, 0.77f, 0f),
        // The Hub: the orange haze of a road tunnel under sodium lamps (its Far Tunnels and Tower: AtmosphereSystem.Hub.cs)
        new(0.010f, 0.32f, 0.21f, 0.09f, 0f),
        // Level 974: clear, with the faintest warm pink to the air
        new(0.0015f, 0.98f, 0.88f, 0.92f, 0f),
        // Level 3999: thin, dark violet black-light air; a concourse fades to purple, never grey (its Natatorium and its
        // Blackout: AtmosphereSystem.L3999.cs)
        new(0.0035f, 0.20f, 0.10f, 0.30f, 0f),
        // Level 188: the hotel's faint grey air (its courtyard's black night and its roof: AtmosphereSystem.L188.cs)
        new(0.005f, 0.60f, 0.58f, 0.55f, 0f),
    };

    /// <summary>
    /// Level 7 from layout version 9, under its high ceiling: the lore's "dim natural light" from nowhere, the same at every
    /// hour (the light comes in through the ceiling and the world is held at half its brightness), and a thin grey-blue sea
    /// haze over the water that takes the far distance, the mist lying on the surface. The sky sphere (L10Sky) takes the
    /// band of sky that would otherwise show between the sea and the ceiling past the view distance.
    /// </summary>
    private static readonly Atmosphere HighSea = new(0.011f, 0.19f, 0.23f, 0.27f, -0.25f, scene: 0.5f, fogMin: 0.06f);

    /// <summary>Level 37.1, the Sanguine Reservoir: close, dark and red.</summary>
    private static readonly Atmosphere Reservoir = new(0.03f, 0.18f, 0.02f, 0.03f, 0f);

    /// <summary>Level 94's castle: nothing in here is animated, and the air is plain; its blinding halls are white.</summary>
    private static readonly Atmosphere Castle = new(0.004f, 0.90f, 0.88f, 0.86f, 0f);
    private static readonly Atmosphere Blinding = new(0.07f, 1f, 1f, 1f, 0f, scene: 1.3f);

    /// <summary>Title keys for the Reservoir (level-371) and the castle (level-941) in the lang file.</summary>
    private const int ReservoirKey = 371, CastleKey = 941;

    /// <summary>How far off the Reservoir's chanting is heard, and a siren pole's tune.</summary>
    private const int ChantHeard = 160;

    /// <summary>
    /// Level 94's siren-pole tune: how far off it is heard, and how loud. It used to be heard 72 blocks off at 0.9, which
    /// in a town was a blast from every street; now a radio heard through a house wall (40 blocks, a third of the volume).
    /// </summary>
    private const int TuneHeard = 40;
    private const float SirenVolume = 0.3f;

    private ILoadedSound poolTone;
    private MusicVoice sirenVoice;
    private int musicLevel;
    private (int X, int Z)? sirenAt;
    private double sirenDistance;
    private float nextChant = 6, nextPoolSound = 8;

    /// <summary>Level 7's water just under the surface, a blue that darkens to black as the player dives.</summary>
    private static readonly float[] SeaWater = { 0.10f, 0.20f, 0.30f };

    /// <summary>Level 6.1: bright, warm and clean, the food court lights all on.</summary>
    private static readonly Atmosphere Snackrooms = new(0.002f, 0.95f, 0.85f, 0.68f, 0f);

    /// <summary>Level 0's Red Rooms: close, dim and red.</summary>
    private static readonly Atmosphere RedRooms = new(0.035f, 0.30f, 0.03f, 0.02f, 0f);

    /// <summary>The key the Red Rooms' title is kept under (level-redrooms in the lang file).</summary>
    private const int RedRoomsKey = 1000;

    /// <summary>
    /// The ambient light of a clear noon (vanilla's, from its sky colour: white, at the day's light strength), which every
    /// level without a day and night keeps at every hour. The game lights a block by the brighter of its block light and
    /// its sunlight times this ambient, and even a block no sunlight reaches has a floor of sunlight (the lowest of the
    /// world's sun light levels, about 0.06); so where a level's own lights don't reach, the ambient is all there is, and
    /// left to vanilla it falls with the outside evening to a small fraction of the day's (Level 188's courtyard, lit only
    /// by its windows, went black at night).
    /// </summary>
    private const float DayAmbient = 1.05f;

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

    // The player's own low stability. Below StrainStart the cue comes in, in full at zero: the fog grows to
    // StrainDensityGain times as thick plus StrainDensityAdd (never past StrainDensityCap, unless it was already
    // thicker: Level 6's dark and Level 7's depths keep a lantern's reach), its colour goes StrainGrey of the way to a
    // brown-grey of its own brightness and down to StrainDark of it, and the ambient light (and the fog with it) falls
    // by StrainDim. Lamps are block light, which the ambient doesn't touch, so a lit room stays lit.
    private const float StrainStart = 0.3f;
    private const float StrainDensityGain = 1.6f, StrainDensityAdd = 0.008f, StrainDensityCap = 0.05f;
    private const float StrainGrey = 0.75f, StrainDark = 0.6f, StrainDim = 0.3f;
    /// <summary>The brown-grey low stability turns the fog to, as a tint on its brightness (it keeps its brightness).</summary>
    private static readonly float[] StrainTint = { 1.15f, 0.97f, 0.80f };

    /// <summary>How long before a level's (or zone's) title is shown again, so walking along a border doesn't keep showing it.</summary>
    private const double TitleCooldownSeconds = 300;

    private static readonly string[] DarkSounds = { "scuttle", "breath", "whisper" };

    /// <summary>How far off, in Level 6, the stairs down can be heard: the faint sound of waves from below.</summary>
    private const int WavesHeard = 160;

    private ICoreClientAPI capi;
    private long tickListener;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private RealitySystem reality;
    private AmbientModifier fog;
    private float mangledFog;
    private static readonly float[] MangledGrey = { 0.36f, 0.38f, 0.41f };
    private readonly Random rand = new();

    // The level's own atmosphere, eased towards as the player moves; darkness is laid over it
    private float baseDensity, baseFogMin, baseScene = 1, sceneWeight = 1, baseClouds, baseCloudBright = 0.75f, cloudWeight, fogBrightWeight = 1, ownWeight = 1;
    private readonly float[] baseColor = new float[3];
    private readonly float[] targetColor = new float[3];
    private readonly float[] strainColor = new float[3];
    private bool snapNext = true;

    private Vec3d lastPos;
    private float blink;
    private float flash;
    private float reveal;
    private float nextDarkSound = 20;
    private float nextWaves = 4;
    private float flicker;
    private bool shiftWasActive, shiftSeen;
    // How far the player's low stability shows in the air (0 not at all, 1 at zero stability), eased
    private float strain;

    // Which level the player was last in, and when each level's name was last shown
    private int lastLevelKey = -1;
    private readonly Dictionary<int, double> titleShownAt = new();

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Event.LevelFinalize += OnLevelFinalize;
        HotelMusicInit();
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
        fog.AmbientColor = WeightedFloatArray.New(new[] { DayAmbient, DayAmbient, DayAmbient }, 1f);
        fog.CloudDensity = WeightedFloat.New(0f, 0f);
        fog.CloudBrightness = WeightedFloat.New(0.75f, 0f);
        capi.Ambient.CurrentModifiers[ModifierKey] = fog;

        tickListener = capi.Event.RegisterGameTickListener(OnTick, 50);
    }

    public override void Dispose()
    {
        if (capi != null)
        {
            if (tickListener != 0) capi.Event.UnregisterGameTickListener(tickListener);
            if (fog != null) capi.Ambient.CurrentModifiers.Remove(ModifierKey);
        }
        // Every loop the levels may have running, so none is left playing after the world closes
        foreach (ILoadedSound sound in new[]
        {
            poolTone, endTone, endWind, funBed, hubDrone, hubWind, l188Loop, l188Pipe, l188Party, l3999Music, l3999Hum, l3999Zone,
            l974Lullaby, l974Fridge, hotelTune, hotelFading, runAlarm, runAlarmFar, runHorde, runHeart, runSafe,
        }.Concat(sirenVoice?.Loaded() ?? []).Concat(funVoiceA?.Loaded() ?? []).Concat(funVoiceB?.Loaded() ?? []))
        {
            sound?.Stop();
            sound?.Dispose();
        }
        base.Dispose();
    }

    /// <summary>
    /// Keeps the level's air the last of the client's ambient modifiers (but for the cheats' clear air), so it is what
    /// shows. The game blends its modifiers in the order they were added, each over the ones before at its weight, and
    /// adds its own low-stability one ("brownrainandfog", EntityBehaviorTemporalStabilityAffected) on the player's
    /// first tick, after this one: while the player's own stability was low it laid dark brown fog and a dark ambient
    /// over every level's air. In the Backrooms stability stays low a long time (every Reality Shift drains it to
    /// nothing, and it recovers only where a place's stability is above 1: Level 4, the Manila Room, the Snackrooms,
    /// the 9th Road, Levels 10 and 11, and a few more), so that darkness and fog followed players through every
    /// threshold and read as the air of the level they had left. The game's distortion, whispers and rust still say
    /// that stability is low, and the level's own air shows it (thicker, browner and dimmer; see OnTick).
    /// </summary>
    private void KeepAirLast()
    {
        var modifiers = capi.Ambient.CurrentModifiers;
        int at = modifiers.IndexOfKey(ModifierKey), count = modifiers.Count;
        bool last = at == count - 1 || at == count - 2 && modifiers.GetKeyAtIndex(count - 1) == Cheats.CheatSystem.ClearAirKey;
        if (at >= 0 && last) return;
        modifiers.Remove(ModifierKey);
        modifiers[ModifierKey] = fog;
        // The cheat wins over the level's air by coming after it
        if (modifiers.TryGetValue(Cheats.CheatSystem.ClearAirKey, out AmbientModifier clear))
        {
            modifiers.Remove(Cheats.CheatSystem.ClearAirKey);
            modifiers[Cheats.CheatSystem.ClearAirKey] = clear;
        }
    }

    /// <summary>Whether the player was in a Red Room last tick, and the seconds left of the quick change of air after crossing its wall.</summary>
    private bool wasRed;
    private float redSwitch;

    private void OnTick(float dt)
    {
        EntityPlayer entity = capi.World.Player?.Entity;
        EntityPos pos = entity?.Pos;
        if (pos == null) return;
        KeepAirLast();

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
        Atmosphere target = snack ? Snackrooms : red ? RedRooms : reservoir ? Reservoir : blinding ? Blinding : castle ? Castle
            : level == 7 && layout.Version >= 9 ? HighSea : Levels[level];
        int titleKey = snack ? 61 : red ? RedRoomsKey : reservoir ? ReservoirKey : castle ? CastleKey : level;
        // The five kept as 14-18 tune their own air, and name their own parts, in their own files
        switch (level)
        {
            case WorldLayout.RunLevel: RunAir(dt, pos, ref target, ref titleKey); break;
            case WorldLayout.FunLevel: FunAir(dt, pos, ref target, ref titleKey); break;
            case WorldLayout.TheEnd: EndAir(dt, pos, ref target, ref titleKey); break;
            case WorldLayout.Hub: HubAir(dt, pos, ref target, ref titleKey); break;
            case WorldLayout.Level974: L974Air(dt, pos, ref target, ref titleKey); break;
            case WorldLayout.Level3999: L3999Air(dt, pos, ref target, ref titleKey); break;
            case WorldLayout.Level188: L188Air(dt, pos, ref target, ref titleKey); break;
            case 10: L10Air(ref target); break;
        }
        AnnounceLevel(titleKey);
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

        // The player's own stability: below 0.3 the air shows it, more the lower it falls, coming and going over about
        // a second so it never jumps. It is laid over whatever air the player is in now, so it goes with them through
        // a door and changes with the level, and lifts as their stability comes back. (Spectators are left the plain
        // air, as in Level 6.)
        float strainTarget = spectator ? 0f : GameMath.Clamp((StrainStart - (float)Entities.Senses.Stability(entity)) / StrainStart, 0f, 1f);
        strain += (strainTarget - strain) * Math.Min(1f, dt * 3f);
        if (strainTarget == 0 && strain < 0.005f) strain = 0f;

        float density = target.Density, fogMin = target.FogMin, groundFog = target.GroundFog;
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
            for (int i = 0; i < 3; i++) targetColor[i] = GameMath.Lerp(SeaWater[i], 0.003f, deep);
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
        // Stepping into or out of a Red Room (its wall is the threshold) turns the air over in well under a second, so
        // the red is whole as soon as you are inside the wallpaper rather than creeping in over the first few blocks
        if (red != wasRed) { wasRed = red; redSwitch = 1.5f; }
        redSwitch = Math.Max(0f, redSwitch - dt);
        float k = snapNext ? 1f : Math.Min(1f, dt * (redSwitch > 0 ? 5f : dark || baseFogMin > 0.2f ? 3f : 0.6f));
        snapNext = false;
        baseDensity += (density - baseDensity) * k;
        baseFogMin += (fogMin - baseFogMin) * k;
        for (int i = 0; i < 3; i++) baseColor[i] += (targetColor[i] - baseColor[i]) * k;
        baseScene += (target.Scene - baseScene) * k;
        sceneWeight += (target.SceneWeight - sceneWeight) * k;
        fogBrightWeight += ((target.DayNight ? 0f : 1f) - fogBrightWeight) * k;
        baseClouds += ((target.Clouds >= 0 ? target.Clouds : 0f) - baseClouds) * k;
        baseCloudBright += (target.CloudBrightness - baseCloudBright) * k;
        cloudWeight += ((target.Clouds >= 0 ? 1f : 0f) - cloudWeight) * k;
        ownWeight += (ownTarget - ownWeight) * Math.Min(1f, dt * 4f);

        // A Level 6 reveal briefly lifts the dark altogether
        float d = GameMath.Lerp(baseDensity, 0.004f, reveal), m = GameMath.Lerp(baseFogMin, 0f, reveal);
        if (strain > 0) d = GameMath.Lerp(d, Math.Min(d * StrainDensityGain + StrainDensityAdd, Math.Max(d, StrainDensityCap)), strain);
        fog.FogDensity.Value = GameMath.Lerp(d, BlackoutDensity, black);
        fog.FogDensity.Weight = ownWeight;
        float[] fogColor = fog.FogColor.Value;
        Strained(baseColor, strainColor);
        for (int i = 0; i < 3; i++) fogColor[i] = GameMath.Lerp(GameMath.Lerp(baseColor[i], strainColor[i], strain), 0.01f, black);
        fog.FogColor.Weight = ownWeight;
        fog.FogMin.Value = Math.Max(m, Math.Max(BlackoutFogMin * shift * (1f - 0.8f * flash), BlinkFogMin * blink));
        fog.FogMin.Weight = ownWeight;
        // Low stability dims the world by StrainDim of whatever it would be: the game lays each modifier's brightness over
        // the ones before at its weight, so this one, at weight w and value v, gives w v + (1 - w) before. The level's
        // own (baseScene at sceneWeight) dimmed is sceneWeight (1 - dim) baseScene + (1 - sceneWeight)(1 - dim) before,
        // which is the same thing at the w and v below. Where the level keeps the outside day and night (weight 0
        // there), that dims the night by the same share as the day rather than lighting it up.
        float dim = StrainDim * strain, sceneW = 1f - (1f - sceneWeight) * (1f - dim);
        fog.SceneBrightness.Value = sceneW > 0.001f ? sceneWeight * (1f - dim) * baseScene / sceneW : baseScene;
        fog.SceneBrightness.Weight = sceneW;
        fog.FogBrightness.Weight = fogBrightWeight;
        // The day's ambient light too, wherever the fog's brightness is held (but under water, the game's own tint)
        fog.AmbientColor.Weight = fogBrightWeight * ownWeight;
        fog.CloudDensity.Value = baseClouds;
        fog.CloudDensity.Weight = cloudWeight;
        fog.CloudBrightness.Value = baseCloudBright;
        fog.CloudBrightness.Weight = cloudWeight;
        // (Level 7 too: its ceiling ends at the view distance, and the sky past it would show as a bright band on the horizon)
        L10Sky(k, level is 10 or 7);

        fog.FlatFogDensity.Value += (groundFog - fog.FlatFogDensity.Value) * Math.Max(k, Math.Min(1f, dt * 2f));
        // Flat fog height is relative to sea level, which the server sets to the floor; compute it absolutely anyway
        fog.FlatFogYPos.Value = geometry.FloorY + GroundFogHeight - capi.World.SeaLevel;
    }

    /// <summary>
    /// The fog colour low stability turns <paramref name="color"/> to: most of the way to a brown-grey of the same
    /// brightness, and darker in step with it, so each level's fog keeps a little of its own hue and stays as much lighter
    /// or darker than the next level's as it was (Level 6's black stays black; Level 37's pale tile air goes a dull, dim
    /// brown).
    /// </summary>
    private static void Strained(float[] color, float[] into)
    {
        float lum = 0.30f * color[0] + 0.59f * color[1] + 0.11f * color[2];
        for (int i = 0; i < 3; i++) into[i] = StrainDark * GameMath.Lerp(color[i], lum * StrainTint[i], StrainGrey);
    }

    /// <summary>
    /// The sounds of Levels 37 and 94. In the Poolrooms: the soft wash of the water everywhere, a drip or a lap now and
    /// then, and from the way the nearest Reservoir lies, a chanting that grows as you near it. In Motion: by day the
    /// nearest siren pole's tune (slowed and gone flat in the last hours of the afternoon); at dusk it stops.
    /// </summary>
    private void LevelSounds(float dt, EntityPos pos, int level, bool reservoir, bool castle)
    {
        musicLevel = level;
        // The five kept as 14-18 start and stop their own (every tick, so they can stop when the player leaves)
        RunSounds(dt, pos, level == WorldLayout.RunLevel);
        FunSounds(dt, pos, level == WorldLayout.FunLevel);
        FunMusic(pos, level == WorldLayout.FunLevel);
        EndSounds(dt, pos, level == WorldLayout.TheEnd);
        HubSounds(dt, pos, level == WorldLayout.Hub);
        L974Sounds(dt, pos, level == WorldLayout.Level974);
        L3999Sounds(dt, pos, level == WorldLayout.Level3999);
        L188Sounds(dt, pos, level == WorldLayout.Level188);
        HotelSounds(dt, pos, level == 5);

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

        // Motion's siren poles, by day: one voice, heard as a radio through a house wall (see TuneHeard)
        string tune = null;
        (int X, int Z)? pole = null;
        if (level == WorldLayout.Motion && !castle && !Regions.MotionSystem.IsNight(capi.World.Calendar))
        {
            pole = layout.NearestSirenPole((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z), TuneHeard);
            if (pole != null) tune = Regions.MotionSystem.IsDusk(capi.World.Calendar) ? "sirentune-dusk" : "sirentune";
        }
        sirenVoice ??= new MusicVoice(capi);
        if (tune == null) sirenVoice.Set(null, null, 0, 0, fadeOut: 0.6f); // at dusk it cuts out
        else
        {
            int ground = geometry.FloorFor(level) + layout.TileAt(pole.Value.X, pole.Value.Z).Height;
            sirenVoice.Set("ambient/" + tune, new Vec3f(pole.Value.X + 0.5f, ground + 3.5f, pole.Value.Z + 0.5f), TuneHeard, SirenVolume);
        }
        sirenAt = pole;
        sirenDistance = pole == null ? -1 : Math.Sqrt((pole.Value.X + 0.5 - pos.X) * (pole.Value.X + 0.5 - pos.X) + (pole.Value.Z + 0.5 - pos.Z) * (pole.Value.Z + 0.5 - pos.Z));
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
