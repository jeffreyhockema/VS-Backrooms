using System;
using Backrooms.Regions;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Zone = Backrooms.Worldgen.WorldLayout.L14Zone;

namespace Backrooms;

/// <summary>
/// Level 14, "The Hospital"'s air and sound on the client (experimental, kept as level 29). Its base fog (its entry in
/// <see cref="Levels"/>) is a pale green-grey haze, "heavy with the scent of antiseptic and decay"; the halls and
/// corridors are dimmer and greyer, and where the lights are dead the air closes in, near black; the inpatient rooms are a
/// clean, blinding white, a surgery room faintly green, a storage room dusty, a torture chamber a dark rust-red, a
/// contaminated room a sickly yellow-green that swims the longer you stay. Titles for each kind of room (2901-2911) as you
/// walk into one.
/// <para><b>The Hunter's dread</b> ("wanderers will suddenly feel a sense of dread. The temperature will drop drastically,
/// and the air will become heavy with a thick, smoky aura"): with a Hunter within about 30 blocks (or 40 while it hunts:
/// <see cref="L14HunterSystem.HuntingKey"/>) the fog thickens and darkens toward a cold blue-black smoke, your breath
/// shows, a sub-bass pressure swells and your heart beats in your ears, faster as it comes.</para>
/// <para><b>Sound</b> (tools/gen_14_sounds.py): the ventilation's drone everywhere, the fluorescent tubes' failing buzz
/// where they are lit, the wards' bright hum and a heart monitor's slow beep, the torture chambers' drip, chains and wet
/// sounds (heard from near their doors too), a Geiger counter in a contaminated room (and, after a while in there, whispers
/// close by from nobody); and "the constant sound of distant footsteps and whispers": every 10 to 30 seconds something
/// somewhere off in the halls (footsteps, a shuffling pair, a door, whispering, a gurney's wheel, a monitor's alarm, the
/// PA's chime).</para>
/// This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L14HallAir = new(0.010f, 0.42f, 0.47f, 0.44f, 0f, scene: 0.92f);
    private static readonly Atmosphere L14DarkAir = new(0.034f, 0.028f, 0.034f, 0.032f, 0f, scene: 0.8f);
    private static readonly Atmosphere L14WhiteAir = new(0.0045f, 0.90f, 0.93f, 0.91f, 0f, scene: 1.12f);
    private static readonly Atmosphere L14MaternityAir = new(0.0045f, 0.93f, 0.89f, 0.90f, 0f, scene: 1.1f);
    private static readonly Atmosphere L14ReceptionAir = new(0.006f, 0.64f, 0.62f, 0.52f, 0f);
    private static readonly Atmosphere L14SurgeryAir = new(0.0075f, 0.44f, 0.62f, 0.53f, 0f);
    private static readonly Atmosphere L14StoreAir = new(0.014f, 0.50f, 0.46f, 0.37f, 0f, scene: 0.95f);
    private static readonly Atmosphere L14TortureAir = new(0.026f, 0.21f, 0.06f, 0.045f, 0f, scene: 0.85f);
    private static readonly Atmosphere L14ContamAir = new(0.022f, 0.52f, 0.62f, 0.16f, 0f);
    private static readonly Atmosphere L14ContamDarkAir = new(0.032f, 0.16f, 0.21f, 0.05f, 0f, scene: 0.85f);
    private static readonly Atmosphere L14DreadAir = new(0.07f, 0.018f, 0.022f, 0.034f, 0f, scene: 0.7f);

    /// <summary>The far-off sounds of the halls and how loud each is (one listed twice comes up twice as often).</summary>
    private static readonly (string Name, float Volume)[] L14Far =
    {
        ("steps1", 0.5f), ("steps1", 0.5f), ("steps2", 0.45f), ("door", 0.45f), ("whisper1", 0.4f), ("whisper2", 0.4f),
        ("gurney", 0.42f), ("beeps", 0.32f), ("chime", 0.3f),
    };

    private ILoadedSound l14Air, l14Buzz, l14Ward, l14Monitor, l14Torture, l14Contam, l14Dread, l14Heart;
    private float l14AirVol, l14BuzzVol, l14WardVol, l14MonitorVol, l14TortureVol, l14ContamVol, l14DreadVol, l14HeartVol;
    /// <summary>The dread (0-1) and what it eases toward; how near a torture chamber is (0-1); seconds in a contaminated room.</summary>
    private float l14DreadLevel, l14DreadWant, l14TortureClose, l14ContamTime;
    private float l14Scan, l14NextFar = 8, l14NextVoice = 6, l14NextBreath;

    private Tile L14TileAt(EntityPos pos) => layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void L14Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        Tile t = L14TileAt(pos);
        Zone zone = WorldLayout.L14ZoneOf(t);
        bool dark = WorldLayout.L14IsDark(t), contam = WorldLayout.L14IsContam(t) && WorldLayout.L14IsRoom(zone);
        if (contam)
        {
            target = dark ? L14ContamDarkAir : L14ContamAir;
            titleKey = 2911;
            // The air swims, more the longer you stay ("hallucinations, disorientation")
            float sick = 0.4f + 0.6f * Math.Min(1f, l14ContamTime / 20f);
            double s = capi.World.ElapsedMilliseconds / 1000.0;
            float swim = (float)Math.Sin(s * 2 * Math.PI / 3.7), drift = (float)Math.Sin(s * 2 * Math.PI / 5.3 + 1);
            target = new Atmosphere(target.Density * (1 + 0.9f * sick * swim), target.R * (1 + 0.25f * sick * drift), target.G, target.B * (1 - 0.4f * sick * drift),
                0f, scene: target.Scene * (1 - 0.1f * sick * swim));
        }
        else
        {
            switch (zone)
            {
                case Zone.Hall or Zone.Corridor or Zone.Station: target = L14HallAir; break;
                case Zone.Reception: target = L14ReceptionAir; titleKey = 2901; break;
                case Zone.Ward: target = L14WhiteAir; titleKey = 2902; break;
                case Zone.Icu: target = L14WhiteAir; titleKey = 2903; break;
                case Zone.Psych: target = L14WhiteAir; titleKey = 2904; break;
                case Zone.Maternity: target = L14MaternityAir; titleKey = 2905; break;
                case Zone.Surgery: target = L14SurgeryAir; titleKey = 2906; break;
                case Zone.Storage: target = L14StoreAir; titleKey = 2907; break;
                case Zone.Torture: target = L14TortureAir; titleKey = 2908; break;
                case Zone.Research: target = L14HallAir; titleKey = 2909; break;
                case Zone.Office: titleKey = 2910; break;
            }
            if (dark) target = L14DarkAir;
        }

        // Twice a second: is the Hunter near, is a torture chamber
        l14Scan -= dt;
        if (l14Scan <= 0)
        {
            l14Scan = 0.5f;
            l14DreadWant = L14DreadOf(pos);
            int bx = (int)Math.Floor(pos.X), bz = (int)Math.Floor(pos.Z);
            l14TortureClose = zone == Zone.Torture ? 1f
                : layout.L14TortureNear(bx, bz, 16) is { } c ? GameMath.Clamp(1f - ((float)Math.Sqrt((c.X - bx) * (c.X - bx) + (c.Z - bz) * (c.Z - bz)) - 4f) / 12f, 0f, 1f) : 0f;
        }
        // The dread comes quickly and lifts slowly
        l14DreadLevel += Math.Clamp(l14DreadWant - l14DreadLevel, -dt * 0.15f, dt * 0.6f);
        if (l14DreadLevel > 0.005f) target = L14Mix(target, L14DreadAir, l14DreadLevel);
    }

    /// <summary>How much dread a Hunter near the player brings (0-1): from 30 blocks off, all of it within 8; while one hunts, never under half within 40.</summary>
    private float L14DreadOf(EntityPos pos)
    {
        var me = new Vec3d(pos.X, pos.Y, pos.Z);
        float best = 0;
        foreach (Entity e in capi.World.GetEntitiesAround(me, 40, 16, e => e.Alive && e.Code?.Path == L14HunterSystem.HunterPath))
        {
            double dx = e.Pos.X - me.X, dy = e.Pos.Y - me.Y, dz = e.Pos.Z - me.Z, d = Math.Sqrt(dx * dx + dy * dy + dz * dz);
            float close = GameMath.Clamp((float)((30 - d) / 22), 0f, 1f);
            float v = e.WatchedAttributes.GetBool(L14HunterSystem.HuntingKey) ? 0.45f + 0.55f * close : 0.7f * close;
            best = Math.Max(best, v);
        }
        return best;
    }

    private static Atmosphere L14Mix(in Atmosphere a, in Atmosphere b, float f) => new(
        GameMath.Lerp(a.Density, b.Density, f), GameMath.Lerp(a.R, b.R, f), GameMath.Lerp(a.G, b.G, f), GameMath.Lerp(a.B, b.B, f),
        GameMath.Lerp(a.GroundFog, b.GroundFog, f), scene: GameMath.Lerp(a.Scene, b.Scene, f), sceneWeight: a.SceneWeight, clouds: a.Clouds,
        dayNight: a.DayNight, cloudBrightness: a.CloudBrightness, fogMin: GameMath.Lerp(a.FogMin, b.FogMin, f));

    private void L14Sounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            L14Stop(ref l14Air);
            L14Stop(ref l14Buzz);
            L14Stop(ref l14Ward);
            L14Stop(ref l14Monitor);
            L14Stop(ref l14Torture);
            L14Stop(ref l14Contam);
            L14Stop(ref l14Dread);
            L14Stop(ref l14Heart);
            l14DreadLevel = l14DreadWant = l14TortureClose = l14ContamTime = 0;
            return;
        }
        Tile t = L14TileAt(pos);
        Zone zone = WorldLayout.L14ZoneOf(t);
        bool dark = WorldLayout.L14IsDark(t), contam = WorldLayout.L14IsContam(t) && WorldLayout.L14IsRoom(zone);
        bool inpatient = zone is Zone.Ward or Zone.Icu or Zone.Psych or Zone.Maternity;
        l14ContamTime = contam ? l14ContamTime + dt : 0;

        // The ventilation everywhere; the tubes' buzz where they are lit; the wards' bright hum and the monitors
        float air = dark ? 0.18f : zone == Zone.Torture ? 0.12f : 0.3f;
        float buzz = dark || inpatient || contam || zone == Zone.Torture ? 0f : zone is Zone.Hall or Zone.Corridor or Zone.Station ? 0.16f : 0.11f;
        float ward = inpatient && !dark && !contam ? 0.26f : 0f;
        float monitor = contam ? 0f : (zone switch { Zone.Icu => 0.3f, Zone.Ward => 0.16f, Zone.Maternity => 0.12f, _ => 0f }) * (dark ? 0.6f : 1f);
        L14Loop(ref l14Air, ref l14AirVol, "air", air, dt, 0.3f);
        L14Loop(ref l14Buzz, ref l14BuzzVol, "buzz", buzz, dt, 0.4f);
        L14Loop(ref l14Ward, ref l14WardVol, "ward", ward, dt, 0.4f);
        L14Loop(ref l14Monitor, ref l14MonitorVol, "monitor", monitor, dt, 0.4f);
        // The torture chambers, heard from near their doors; a contaminated room's counter
        L14Loop(ref l14Torture, ref l14TortureVol, "torture", zone == Zone.Torture ? 0.5f : 0.35f * l14TortureClose, dt, 0.3f);
        L14Loop(ref l14Contam, ref l14ContamVol, "contam", contam ? 0.45f : 0f, dt, 0.8f);
        // The dread: the pressure, and your heart, faster as it comes
        L14Loop(ref l14Dread, ref l14DreadVol, "dread", 0.65f * l14DreadLevel, dt, 0.6f);
        L14Loop(ref l14Heart, ref l14HeartVol, "heartbeat", l14DreadLevel > 0.08f ? 0.25f + 0.45f * l14DreadLevel : 0f, dt, 0.5f);
        l14Heart?.SetPitch(0.9f + 0.4f * l14DreadLevel);
        if (l14DreadLevel > 0.3f) L14Breath(dt);

        // In a contaminated room a while: whispers close by, from nobody
        if (contam && l14ContamTime > 8)
        {
            l14NextVoice -= dt;
            if (l14NextVoice <= 0)
            {
                l14NextVoice = 5 + (float)rand.NextDouble() * 6;
                double a = rand.NextDouble() * Math.PI * 2, d = 1.5 + rand.NextDouble() * 2.5;
                capi.World.PlaySoundAt(new AssetLocation(rand.Next(2) == 0 ? "backrooms:sounds/ambient/14/whisper1" : "backrooms:sounds/ambient/14/whisper2"),
                    pos.X + Math.Cos(a) * d, pos.Y + 1.6, pos.Z + Math.Sin(a) * d, null, 0.85f + (float)rand.NextDouble() * 0.25f, 12, 0.5f);
            }
        }

        // "The constant sound of distant footsteps and whispers": something somewhere off in the halls every 10 to 30 s
        l14NextFar -= dt;
        if (l14NextFar > 0) return;
        l14NextFar = 10 + (float)rand.NextDouble() * 20;
        var (name, volume) = L14Far[rand.Next(L14Far.Length)];
        double angle = rand.NextDouble() * Math.PI * 2, far = 14 + rand.NextDouble() * 16;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/14/" + name), pos.X + Math.Cos(angle) * far, pos.Y + 1.5, pos.Z + Math.Sin(angle) * far,
            null, 0.92f + (float)rand.NextDouble() * 0.14f, 48, volume);
    }

    /// <summary>The cold: your breath showing, a puff every few seconds in front of your face.</summary>
    private void L14Breath(float dt)
    {
        l14NextBreath -= dt;
        if (l14NextBreath > 0) return;
        l14NextBreath = 2.2f + (float)rand.NextDouble() * 1.4f;
        EntityPlayer me = capi.World.Player?.Entity;
        if (me == null) return;
        Vec3f look = me.Pos.GetViewVector();
        double x = me.Pos.X + look.X * 0.5, y = me.Pos.Y + me.LocalEyePos.Y - 0.18 + look.Y * 0.5, z = me.Pos.Z + look.Z * 0.5;
        // Round 4: a fine mist of many small motes, not a few big quads (a big pale square hung in front of the camera)
        var puff = new SimpleParticleProperties(12, 18, ColorUtil.ToRgba(34, 225, 230, 240), new Vec3d(x - 0.08, y - 0.06, z - 0.08), new Vec3d(x + 0.08, y + 0.03, z + 0.08),
            new Vec3f(look.X * 0.25f - 0.06f, 0.0f, look.Z * 0.25f - 0.06f), new Vec3f(look.X * 0.5f + 0.06f, 0.08f, look.Z * 0.5f + 0.06f), 1.2f, -0.01f, 0.05f, 0.11f,
            EnumParticleModel.Quad)
        {
            SizeEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, 0.6f),
            OpacityEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, -40f),
            WindAffected = false,
            ShouldDieInLiquid = true,
        };
        capi.World.SpawnParticles(puff);
    }

    /// <summary>Keeps one of the level's loops going, easing its volume toward <paramref name="want"/> at <paramref name="rate"/> a second; stops it once faded out.</summary>
    private void L14Loop(ref ILoadedSound sound, ref float volume, string name, float want, float dt, float rate)
    {
        if (sound == null)
        {
            if (want <= 0) return;
            volume = 0.01f;
            sound = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/14/" + name), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = volume, SoundType = EnumSoundType.Ambient,
            });
            sound?.Start();
            return;
        }
        float next = volume + Math.Clamp(want - volume, -dt * rate, dt * rate);
        if (next <= 0.005f && want <= 0)
        {
            L14Stop(ref sound);
            volume = 0;
            return;
        }
        if (Math.Abs(next - volume) > 0.002f)
        {
            volume = next;
            sound.SetVolume(volume);
        }
    }

    private static void L14Stop(ref ILoadedSound sound)
    {
        if (sound == null) return;
        sound.Stop();
        sound.Dispose();
        sound = null;
    }
}
