using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level 23, "The Petrified Garden"'s air and sound on the client (experimental, kept as level 28). Its base fog (its entry in
/// <see cref="Levels"/>) is a dim green murk under the lid of leaves, a mist lying on the forest floor; no day and no night.
/// The outside sky is hidden in a sphere of pale gold-green, so the holes in the lid show only the glare of the star that
/// never moves. Below, each glow room has the colour of its Sorries (teal, violet or amber); the root tunnels are close and
/// brown; Base Seedling is warm with its lanterns; the ruins are cold and grey-green; the Heart of Water is the clearest air
/// in the level, under the light that falls on its pool.
///
/// The sound bed: the lid rustling far overhead, the trunks creaking and groaning, now and then a sentry's scream a long way
/// off; in the caverns drips, and the Sorries whispering "sorry" all round; at the pool, running water; at the camp, people
/// talking low. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    // (Dim but readable: the fog thin enough that the trunks stand one behind another for thirty-odd blocks before they
    // fade, its colour the grey-green of the light that gets through the lid, not black)
    // (A ground fog thickens with depth under the fog's surface: only a trace of it on the forest floor, and none down in
    // the basin or the caverns, where it closed everything in)
    // (Round 3: thinner and a shade paler again, so the depth of the trunks reads; a glade under one of the wide holes is
    // brighter still, the light of the star coming down into it)
    private static readonly Atmosphere L23Forest = new(0.0056f, 0.19f, 0.25f, 0.16f, -0.07f, scene: 0.97f);
    private static readonly Atmosphere L23GladeAir = new(0.0048f, 0.30f, 0.34f, 0.22f, -0.07f, scene: 1f);
    private static readonly Atmosphere L23CoreAir = new(0.0045f, 0.26f, 0.33f, 0.24f, 0f, scene: 1f);
    private static readonly Atmosphere L23TunnelAir = new(0.013f, 0.10f, 0.08f, 0.05f, 0f, scene: 0.9f);
    private static readonly Atmosphere L23SeedlingAir = new(0.006f, 0.24f, 0.18f, 0.10f, 0f, scene: 1f);
    private static readonly Atmosphere L23RuinAir = new(0.0065f, 0.12f, 0.14f, 0.12f, 0f, scene: 1f);
    /// <summary>The glow rooms' air by their colour: teal, violet, amber.</summary>
    private static readonly Atmosphere[] L23GlowAir =
    {
        new(0.007f, 0.04f, 0.12f, 0.12f, 0f, scene: 1f),
        new(0.007f, 0.09f, 0.05f, 0.13f, 0f, scene: 1f),
        new(0.007f, 0.13f, 0.09f, 0.04f, 0f, scene: 1f),
    };

    /// <summary>The title keys of the level's named places (level-2801... in the lang file).</summary>
    private const int L23CoreKey = 2801, L23SeedlingKey = 2802, L23RuinKey = 2803;

    /// <summary>The colour of the glare through the holes in the lid (the sky hidden behind it).</summary>
    private static readonly float[] L23Glare = { 0.78f, 0.82f, 0.58f };

    private ILoadedSound l23Rustle, l23Water;
    private float l23NextCreak = 8, l23NextGroan = 30, l23NextScream = 160, l23NextDrip = 2, l23NextSorry = 4, l23NextMurmur = 10;
    private float l23Sky, l23NextMote;
    private bool l23SphereSet;

    private byte L23Where(EntityPos pos, out byte colour) =>
        layout.L23ZoneAt(pos.X, pos.Y, pos.Z, geometry.FloorFor(WorldLayout.Level23), out colour);

    private void L23Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        switch (L23Where(pos, out byte colour))
        {
            case WorldLayout.L23Core:
                target = L23CoreAir;
                titleKey = L23CoreKey;
                break;
            case WorldLayout.L23Seedling:
                target = L23SeedlingAir;
                titleKey = L23SeedlingKey;
                break;
            case WorldLayout.L23Ruin:
                target = L23RuinAir;
                titleKey = L23RuinKey;
                break;
            case WorldLayout.L23Glow:
                target = L23GlowAir[Math.Clamp(colour - 1, 0, 2)];
                break;
            case WorldLayout.L23TunnelZone:
                target = L23TunnelAir;
                break;
            default:
                target = layout.L23InGlade(pos.X, pos.Z, 2) ? L23GladeAir : L23Forest;
                break;
        }
    }

    private void L23Sounds(float dt, EntityPos pos, bool here)
    {
        L23SkySphere(dt, here);
        if (!here)
        {
            L188Stop(ref l23Rustle);
            L188Stop(ref l23Water);
            return;
        }
        byte zone = L23Where(pos, out _);
        bool under = zone is WorldLayout.L23Glow or WorldLayout.L23TunnelZone or WorldLayout.L23Seedling or WorldLayout.L23Ruin;

        if (!under) L23Shafts(dt, pos);
        else if (zone == WorldLayout.L23Glow) L23Sparks(dt, pos);
        // The lid rustling far overhead, muffled below ground
        L23Loop(ref l23Rustle, "game:sounds/weather/wind-leafy", under ? 0.02f : 0.12f);
        // The Heart of Water: the pool, running water heard from its banks
        int mx = layout.L23MidX, mz = layout.L23MidZ;
        double floor = geometry.FloorFor(WorldLayout.Level23);
        L188Positional(ref l23Water, "game:sounds/environment/creek", pos, mx + 0.5, floor + WorldLayout.L23PoolSurface, mz + 0.5, 70, 0.45f);

        if (under)
        {
            // Drips, close by
            l23NextDrip -= dt;
            if (l23NextDrip <= 0)
            {
                l23NextDrip = 1.5f + (float)rand.NextDouble() * 4;
                L23PlayNear(pos, $"game:sounds/environment/drip{1 + rand.Next(3)}", 3, 9, -1, 3, 0.25f, 16);
            }
            // The Sorries whispering all round (at the camp, where the M.E.G. keep them few, now and then)
            l23NextSorry -= dt;
            if (l23NextSorry <= 0)
            {
                l23NextSorry = (zone == WorldLayout.L23Seedling ? 12f : 3f) + (float)rand.NextDouble() * 6;
                if (zone != WorldLayout.L23TunnelZone || rand.NextDouble() < 0.4)
                    L23PlayNear(pos, $"backrooms:sounds/ambient/23/sorry{1 + rand.Next(3)}", 4, 11, 0, 4, zone == WorldLayout.L23Seedling ? 0.12f : 0.3f, 16);
            }
            if (zone == WorldLayout.L23Seedling)
            {
                l23NextMurmur -= dt;
                if (l23NextMurmur <= 0)
                {
                    l23NextMurmur = 14 + (float)rand.NextDouble() * 18;
                    L23PlayNear(pos, "backrooms:sounds/entity/murmur", 6, 12, 0, 1, 0.22f, 20);
                }
            }
        }
        else
        {
            // The trunks creaking round about, and up in the dark
            l23NextCreak -= dt;
            if (l23NextCreak <= 0)
            {
                l23NextCreak = 10 + (float)rand.NextDouble() * 22;
                L23PlayNear(pos, $"backrooms:sounds/ambient/974/creak{1 + rand.Next(3)}", 6, 16, 4, 12, 0.3f, 32);
            }
            // A deep groan of wood, somewhere
            l23NextGroan -= dt;
            if (l23NextGroan <= 0)
            {
                l23NextGroan = 35 + (float)rand.NextDouble() * 55;
                L23PlayNear(pos, "backrooms:sounds/ambient/23/woodgroan", 18, 30, 0, 8, 0.35f, 48);
            }
        }
        // A buried sentry screaming, a long way off: someone said it
        l23NextScream -= dt;
        if (l23NextScream <= 0)
        {
            l23NextScream = 150 + (float)rand.NextDouble() * 180;
            L23PlayNear(pos, "backrooms:sounds/ambient/23/sentryscream", 28, 40, 0, 4, under ? 0.06f : 0.12f, 64);
        }
    }

    /// <summary>
    /// The shafts of light under the holes in the lid, made visible: motes of dust and pollen drifting down through the
    /// sunlight of the nearest holes round the player (within 56 blocks), faintly self-lit so the shaft reads through the
    /// green air as a pale column from the forest floor up into the hole: the forest's landmarks.
    /// </summary>
    private void L23Shafts(float dt, EntityPos pos)
    {
        l23NextMote -= dt;
        if (l23NextMote > 0) return;
        l23NextMote = 0.12f;
        int floor = geometry.FloorFor(WorldLayout.Level23);
        int hi = (int)Math.Floor(pos.X / 48), hj = (int)Math.Floor(pos.Z / 48);
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (!layout.L23HoleAt(hi + di, hj + dj, out double cx, out double cz, out double r)) continue;
                L23Mote(pos, cx, cz, r * 0.8, floor, 3);
            }
        L23Mote(pos, layout.L23MidX + 0.5, layout.L23MidZ + 0.5, 6, floor, 6);
    }

    /// <summary>The glow rooms' air: a few motes of the Sorries' light drifting about the player, in the room's colour.</summary>
    private void L23Sparks(float dt, EntityPos pos)
    {
        l23NextMote -= dt;
        if (l23NextMote > 0) return;
        l23NextMote = 0.25f;
        L23Where(pos, out byte colour);
        (int R, int G, int B) c = colour switch { 1 => (120, 255, 230), 2 => (210, 140, 255), _ => (255, 200, 110) };
        for (int k = 0; k < 2; k++)
        {
            double a = rand.NextDouble() * Math.PI * 2, d = 2 + rand.NextDouble() * 12;
            double x = pos.X + Math.Cos(a) * d, z = pos.Z + Math.Sin(a) * d, y = pos.Y + rand.NextDouble() * 6 - 1;
            var spark = new SimpleParticleProperties(1, 1, ColorUtil.ToRgba(200, c.R, c.G, c.B), new Vec3d(x, y, z), new Vec3d(x + 0.01, y + 0.01, z + 0.01),
                new Vec3f(-0.05f, -0.03f, -0.05f), new Vec3f(0.05f, 0.05f, 0.05f), 6f, 0f, 0.08f, 0.16f, EnumParticleModel.Quad)
            {
                VertexFlags = 220,
                ShouldDieInLiquid = true,
                WindAffected = false,
            };
            capi.World.SpawnParticles(spark);
        }
    }

    private void L23Mote(EntityPos pos, double cx, double cz, double r, int floor, int count)
    {
        double dx = cx - pos.X, dz = cz - pos.Z;
        if (dx * dx + dz * dz > 56 * 56) return;
        int ground = Math.Max(WorldLayout.L23PoolSurface, layout.L23Ground((int)Math.Floor(cx), (int)Math.Floor(cz)));
        for (int k = 0; k < count; k++)
        {
            double a = rand.NextDouble() * Math.PI * 2, d = r * Math.Sqrt(rand.NextDouble());
            double x = cx + Math.Cos(a) * d, z = cz + Math.Sin(a) * d, y = floor + ground + 1 + rand.NextDouble() * (WorldLayout.L23LidLow - ground);
            int c = ColorUtil.ToRgba(150 + rand.Next(60), 255, 246, 200);
            var mote = new SimpleParticleProperties(1, 1, c, new Vec3d(x, y, z), new Vec3d(x + 0.01, y + 0.01, z + 0.01),
                new Vec3f(-0.04f, -0.12f, -0.04f), new Vec3f(0.04f, -0.03f, 0.04f), 9f, 0f, 0.1f, 0.22f, EnumParticleModel.Quad)
            {
                VertexFlags = 90,
                ShouldDieInLiquid = true,
                WindAffected = false,
            };
            capi.World.SpawnParticles(mote);
        }
    }

    /// <summary>Plays a sound once somewhere round the player: so far off (horizontally), so high above or below.</summary>
    private void L23PlayNear(EntityPos pos, string location, double near, double far, double low, double high, float volume, float range)
    {
        double yaw = rand.NextDouble() * Math.PI * 2, d = near + rand.NextDouble() * (far - near);
        capi.World.PlaySoundAt(new AssetLocation(location), pos.X + Math.Sin(yaw) * d, pos.Y + low + rand.NextDouble() * (high - low), pos.Z + Math.Cos(yaw) * d, null,
            randomizePitch: true, range: range, volume: volume);
    }

    /// <summary>A loop that follows the player at a volume, started and stopped as the volume comes and goes.</summary>
    private void L23Loop(ref ILoadedSound sound, string location, float volume)
    {
        if (volume > 0.01f && sound == null)
        {
            sound = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation(location), ShouldLoop = true, RelativePosition = true, DisposeOnFinish = false, Volume = volume,
                SoundType = EnumSoundType.Ambient,
            });
            sound?.Start();
        }
        else if (volume <= 0.01f && sound != null) L188Stop(ref sound);
        else sound?.SetVolume(volume);
    }

    /// <summary>
    /// The sphere round the player that hides the outside sky (its sun, moon and stars, its blue and its night) while in the
    /// level: the pale glare of the fixed star through the lid instead, eased in and out; Level 10's own sphere is left alone.
    /// </summary>
    private void L23SkySphere(float dt, bool here)
    {
        l23Sky += ((here ? 1f : 0f) - l23Sky) * Math.Min(1f, dt * 2f);
        DefaultShaderUniforms uniforms = capi.Render.ShaderUniforms;
        if (l23Sky < 0.01f)
        {
            if (l23SphereSet) uniforms.FogSphereQuantity = 0;
            l23SphereSet = false;
            return;
        }
        float[] sphere = uniforms.FogSpheres;
        sphere[0] = sphere[1] = sphere[2] = 0;
        sphere[3] = SkySphereRadius;
        sphere[4] = SkySphereDensity * 1.3f * l23Sky;
        sphere[5] = L23Glare[0];
        sphere[6] = L23Glare[1];
        sphere[7] = L23Glare[2];
        uniforms.FogSphereQuantity = 1;
        l23SphereSet = true;
    }
}
