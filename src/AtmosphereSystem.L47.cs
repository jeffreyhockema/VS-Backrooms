using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level 47, "The Adderwood"'s air and sound on the client (experimental, kept as level 30). Wikidot: "During daylight hours,
/// the forest is uniformly covered in a thick, damp fog, and no direct sunlight has ever been observed. Each night, however,
/// the fog will disperse without fail to reveal a full moon." By day a thick pale grey-green fog under the trees, a mist
/// lying on the ground, the sky hidden (a sphere of fog of the fog's own colour, as Level 10's and 73's, so no sun shows
/// through it); at dusk it thins away, and the night is clear and dark blue, moonlit (the scene held at a moonlit dimness,
/// not black), its stars, moon and rare aurora drawn by Regions.L47Sky. The glade's fog is a little thinner; the manor's air
/// close and warm. Titles: the Ophion Glade (3001), the Trail (3002).
///
/// The sound bed: the wind in the crowns; by day crows and ravens, now and then a woodpecker far off; a stream running when
/// one is near; at night howls far off (the Black Shucks call their pack: "their long, baleful howls travel for miles");
/// dry branches snapping; now and then, behind you, something in the forest shifting (the lore's superposition, heard and
/// never seen); near the glade, the Order chanting. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L47DayForest = new(0.017f, 0.50f, 0.55f, 0.52f, -0.07f, scene: 0.9f, clouds: 0f, cloudBrightness: 0f, fogMin: 0.035f);
    private static readonly Atmosphere L47NightForest = new(0.0055f, 0.030f, 0.045f, 0.080f, -0.04f, scene: 0.85f, clouds: 0f, cloudBrightness: 0f);
    private static readonly Atmosphere L47DayGlade = new(0.012f, 0.55f, 0.59f, 0.56f, -0.05f, scene: 0.95f, clouds: 0f, cloudBrightness: 0f, fogMin: 0.025f);
    private static readonly Atmosphere L47NightGlade = new(0.0045f, 0.035f, 0.05f, 0.09f, -0.03f, scene: 0.9f, clouds: 0f, cloudBrightness: 0f);
    private static readonly Atmosphere L47ManorAir = new(0.006f, 0.14f, 0.10f, 0.07f, 0f, scene: 0.75f, clouds: 0f, cloudBrightness: 0f);

    /// <summary>The title keys of the level's named places (level-3001... in the lang file).</summary>
    private const int L47GladeKey = 3001, L47TrailKey = 3002;

    private ILoadedSound l47Wind, l47Creek, l47Chant;
    private float l47NextBird = 12, l47NextPecker = 70, l47NextHowl = 30, l47NextSnap = 20, l47NextShift = 150, l47CreekCheck, l47CreekVolume;
    private float l47Sky;
    private bool l47SphereSet;

    /// <summary>
    /// How far into the night it is in the Adderwood (0 the day's fog, 1 the clear night): the fog thins from 19:00 to
    /// 20:30 and comes back from 5:00 to 6:30, by the world's own clock.
    /// </summary>
    public static float L47Night(IGameCalendar calendar)
    {
        double h = calendar.HourOfDay;
        double k = h >= 12 ? (h - 19) / 1.5 : (6.5 - h) / 1.5;
        k = Math.Clamp(k, 0, 1);
        return (float)(k * k * (3 - 2 * k));
    }

    private static Atmosphere L47Blend(in Atmosphere a, in Atmosphere b, float t) => new(
        GameMath.Lerp(a.Density, b.Density, t), GameMath.Lerp(a.R, b.R, t), GameMath.Lerp(a.G, b.G, t), GameMath.Lerp(a.B, b.B, t),
        GameMath.Lerp(a.GroundFog, b.GroundFog, t), GameMath.Lerp(a.Scene, b.Scene, t), a.SceneWeight, a.Clouds, false, a.CloudBrightness,
        GameMath.Lerp(a.FogMin, b.FogMin, t));

    private void L47Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        float night = L47Night(capi.World.Calendar);
        switch (layout.L47ZoneAt(pos.X, pos.Z))
        {
            case WorldLayout.L47ManorZone when pos.Y < geometry.FloorFor(WorldLayout.Level47) + WorldLayout.L47Eaves + 1:
                target = L47ManorAir;
                titleKey = L47GladeKey;
                break;
            case WorldLayout.L47ManorZone or WorldLayout.L47GladeZone:
                target = L47Blend(L47DayGlade, L47NightGlade, night);
                titleKey = L47GladeKey;
                break;
            case WorldLayout.L47TrailZone:
                target = L47Blend(L47DayForest, L47NightForest, night);
                titleKey = L47TrailKey;
                break;
            default:
                target = L47Blend(L47DayForest, L47NightForest, night);
                break;
        }
    }

    private void L47Sounds(float dt, EntityPos pos, bool here)
    {
        L47SkySphere(dt, here);
        if (!here)
        {
            L188Stop(ref l47Wind);
            L188Stop(ref l47Creek);
            L188Stop(ref l47Chant);
            return;
        }
        float night = L47Night(capi.World.Calendar);
        byte zone = layout.L47ZoneAt(pos.X, pos.Z);
        bool inside = zone == WorldLayout.L47ManorZone;

        // The wind in the crowns, high and soft (stiller in the night, muffled in the manor)
        L73Loop(ref l47Wind, "game:sounds/environment/wind", inside ? 0.04f : 0.16f - 0.06f * night);

        // A stream, when one runs near: looked for once a second over the ground round about
        l47CreekCheck -= dt;
        if (l47CreekCheck <= 0)
        {
            l47CreekCheck = 1;
            double best = 99;
            int bx = (int)Math.Floor(pos.X), bz = (int)Math.Floor(pos.Z);
            for (int dz = -16; dz <= 16; dz += 4)
                for (int dx = -16; dx <= 16; dx += 4)
                    if (layout.L47InWater(bx + dx, bz + dz)) best = Math.Min(best, Math.Sqrt(dx * dx + dz * dz));
            l47CreekVolume = (float)Math.Clamp(1 - best / 20, 0, 1) * 0.45f;
        }
        L73Loop(ref l47Creek, "game:sounds/environment/creek", l47CreekVolume);

        // The Order chanting, from the manor, heard well out into the forest round the glade
        double floor = geometry.FloorFor(WorldLayout.Level47);
        L188Positional(ref l47Chant, "backrooms:sounds/ambient/47/chant", pos, layout.L47MidX + 0.5, floor + 3, layout.L47MidZ + 0.5, 110, inside ? 0.55f : 0.35f);
        if (inside) return;

        // By day the crows and ravens (the only things that hunt the snakes), a woodpecker far off
        if (night < 0.5f)
        {
            l47NextBird -= dt;
            if (l47NextBird <= 0)
            {
                l47NextBird = 14 + (float)rand.NextDouble() * 30;
                bool raven = rand.NextDouble() < 0.35;
                string snd = raven ? $"backrooms:sounds/ambient/47/raven{1 + rand.Next(3)}" : $"backrooms:sounds/ambient/47/crow{1 + rand.Next(4)}";
                L47Far(pos, snd, 16 + rand.NextDouble() * 18, 10 + rand.NextDouble() * 12, 0.45f);
            }
            l47NextPecker -= dt;
            if (l47NextPecker <= 0)
            {
                l47NextPecker = 60 + (float)rand.NextDouble() * 80;
                L47Far(pos, "backrooms:sounds/ambient/47/woodpecker", 30, 14, 0.3f);
            }
        }
        else
        {
            // At night the Shucks' howls, far off and carrying ("beacons to other pack members")
            l47NextHowl -= dt;
            if (l47NextHowl <= 0)
            {
                l47NextHowl = 50 + (float)rand.NextDouble() * 70;
                L47Far(pos, $"game:sounds/creature/wolf/howl{1 + rand.Next(7)}", 40, 6, 0.22f);
            }
        }
        l47NextSnap -= dt;
        if (l47NextSnap <= 0)
        {
            l47NextSnap = (night > 0.5f ? 25 : 45) + (float)rand.NextDouble() * 40;
            L47Far(pos, $"backrooms:sounds/ambient/47/branchsnap{1 + rand.Next(2)}", 10 + rand.NextDouble() * 12, 2, 0.4f);
        }
        // Behind you, now and then, the forest shifting where nobody is looking
        l47NextShift -= dt;
        if (l47NextShift <= 0)
        {
            l47NextShift = 150 + (float)rand.NextDouble() * 180;
            double yaw = capi.World.Player.Entity.Pos.Yaw;
            capi.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/ambient/47/shift{1 + rand.Next(2)}"), pos.X + Math.Sin(yaw) * 9, pos.Y + 1.5,
                pos.Z + Math.Cos(yaw) * 9, null, randomizePitch: true, range: 24, volume: 0.35f);
        }
    }

    /// <summary>A sound somewhere off in the forest, at a distance and height, in a random direction.</summary>
    private void L47Far(EntityPos pos, string location, double distance, double up, float volume)
    {
        double yaw = rand.NextDouble() * Math.PI * 2;
        capi.World.PlaySoundAt(new AssetLocation(location), pos.X + Math.Sin(yaw) * distance, pos.Y + up, pos.Z + Math.Cos(yaw) * distance, null,
            randomizePitch: true, range: (float)distance + 24, volume: volume);
    }

    /// <summary>
    /// The sphere of fog round the player that hides the outside sky (its sun, moon and stars and its blue) while in the
    /// level, the colour the fog is now, eased in and out; the Adderwood's own night sky is drawn over it (Regions.L47Sky).
    /// </summary>
    private void L47SkySphere(float dt, bool here)
    {
        l47Sky += ((here ? 1f : 0f) - l47Sky) * Math.Min(1f, dt * 2f);
        DefaultShaderUniforms uniforms = capi.Render.ShaderUniforms;
        if (l47Sky < 0.01f)
        {
            if (l47SphereSet) uniforms.FogSphereQuantity = 0;
            l47SphereSet = false;
            return;
        }
        Vec4f fogColor = capi.Ambient.BlendedFogColor;
        float[] sphere = uniforms.FogSpheres;
        sphere[0] = sphere[1] = sphere[2] = 0;
        sphere[3] = SkySphereRadius;
        sphere[4] = SkySphereDensity * 1.3f * l47Sky;
        sphere[5] = fogColor.R;
        sphere[6] = fogColor.G;
        sphere[7] = fogColor.B;
        uniforms.FogSphereQuantity = 1;
        l47SphereSet = true;
    }
}
