using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level 55, "Land of Ice"'s air and sound on the client (experimental, kept as level 25). Its base fog (its entry in
/// <see cref="Levels"/>) is a thin pale blue-white haze under a polar day held bright at every hour; the sky (sun, moon and
/// stars) is hidden in a sphere of fog of the fog's own colour (as Level 73's and Level 10's are), so there is no sun, no
/// sunrise and no night. Now and then a whiteout comes over the ice (<see cref="L55Whiteout"/>): the fog closes in,
/// white, and the wind rises. In the research hut the air is close and warm, lit by its lamps and its stove; in the ice
/// cave it is still and blue.
///
/// The sound bed is all reused: vanilla's wind, louder in a whiteout; a deep groan or crack in the ice far off now and
/// then (vanilla's heavy ice and Level 974's creaks, pitched down); in the hut, the stove crackling. This file is the
/// level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L55HutAir = new(0.0030f, 0.32f, 0.26f, 0.20f, 0f, scene: 0.80f);
    private static readonly Atmosphere L55CaveAir = new(0.0060f, 0.50f, 0.71f, 0.85f, 0f, scene: 0.55f);

    /// <summary>The title keys of the hut and the cave (level-2501, level-2502 in the lang file).</summary>
    private const int L55HutKey = 2501, L55CaveKey = 2502;

    /// <summary>The whiteout's fog: thick, and nearly white.</summary>
    private const float L55WhiteDensity = 0.02f, L55WhiteScene = 0.80f;
    private static readonly float[] L55White = { 0.95f, 0.965f, 0.98f };

    private ILoadedSound l55Wind, l55Stove;
    private float l55NextGroan = 50;
    private float l55Sky;
    private bool l55SphereSet;

    /// <summary>A slot of game hours in which a whiteout may come, the chance it does, and how long it lasts (in game hours).</summary>
    private const double L55WhiteSlot = 2, L55WhiteChance = 0.25, L55WhiteLength = 0.3;

    /// <summary>
    /// How deep a whiteout is at a moment (0 clear, 1 at its worst), the same for everyone in the world: in about one slot of
    /// two game hours in four, for three tenths of an hour, easing in and out.
    /// </summary>
    public static float L55Whiteout(int worldSeed, double totalHours)
    {
        long slot = (long)Math.Floor(totalHours / L55WhiteSlot);
        ulong h = Hashing.Hash((ulong)(uint)worldSeed, (int)slot, (int)(slot >> 32), 0x2510);
        if (Hashing.Unit(h) >= L55WhiteChance) return 0;
        double start = slot * L55WhiteSlot + (L55WhiteSlot - L55WhiteLength) * Hashing.Unit(Hashing.Mix(h));
        double t = (totalHours - start) / L55WhiteLength;
        if (t <= 0 || t >= 1) return 0;
        double e = Math.Min(1, Math.Min(t, 1 - t) / 0.25);
        return (float)(e * e * (3 - 2 * e));
    }

    /// <summary>Where the player is: in the hut, or in the cave (under its ice).</summary>
    private (bool Hut, bool Cave) L55Where(EntityPos pos)
    {
        int bx = (int)Math.Floor(pos.X), bz = (int)Math.Floor(pos.Z);
        double rel = pos.Y - geometry.FloorFor(WorldLayout.Level55);
        bool hut = layout.InL55Hut(bx, bz) && rel > WorldLayout.L55HutFloor && rel < WorldLayout.L55HutFloor + WorldLayout.L55HutRoof;
        bool cave = !hut && layout.InL55Cave(bx, bz, rel + 0.5);
        return (hut, cave);
    }

    private void L55Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        var (hut, cave) = L55Where(pos);
        if (hut)
        {
            target = L55HutAir;
            titleKey = L55HutKey;
            return;
        }
        if (cave)
        {
            target = L55CaveAir;
            titleKey = L55CaveKey;
            return;
        }
        float white = L55Whiteout(capi.World.Seed, capi.World.Calendar.TotalHours);
        if (white > 0)
            target = new Atmosphere(GameMath.Lerp(target.Density, L55WhiteDensity, white), GameMath.Lerp(target.R, L55White[0], white),
                GameMath.Lerp(target.G, L55White[1], white), GameMath.Lerp(target.B, L55White[2], white), target.GroundFog,
                GameMath.Lerp(target.Scene, L55WhiteScene, white));
    }

    private void L55Sounds(float dt, EntityPos pos, bool here)
    {
        L55SkySphere(dt, here);
        if (!here)
        {
            L188Stop(ref l55Wind);
            L188Stop(ref l55Stove);
            return;
        }
        var (hut, cave) = L55Where(pos);
        float white = L55Whiteout(capi.World.Seed, capi.World.Calendar.TotalHours);

        // The wind: muffled in the hut, a far moan in the cave, rising in a whiteout
        L55Loop(ref l55Wind, "game:sounds/environment/wind", hut ? 0.06f : cave ? 0.10f : 0.30f + 0.40f * white);

        // The stove in the hut
        var (sx, sz) = layout.L55Stove;
        double floor = geometry.FloorFor(WorldLayout.Level55) + WorldLayout.L55HutFloor;
        L188Positional(ref l55Stove, "game:sounds/environment/fireplace", pos, sx + 1, floor + 2.5, sz + 0.5, 14, 0.6f);
        if (hut) return;

        // The ice groaning or cracking somewhere off across the glacier, too far to place
        l55NextGroan -= dt;
        if (l55NextGroan <= 0)
        {
            l55NextGroan = 60 + (float)rand.NextDouble() * 80;
            double yaw = rand.NextDouble() * Math.PI * 2;
            string sound = rand.NextDouble() < 0.5 ? "game:sounds/block/heavyice" : $"backrooms:sounds/ambient/974/creak{1 + rand.Next(3)}";
            capi.World.PlaySoundAt(new AssetLocation(sound), pos.X + Math.Sin(yaw) * 24, pos.Y - 2, pos.Z + Math.Cos(yaw) * 24, null,
                0.45f + 0.15f * (float)rand.NextDouble(), 64f, cave ? 0.45f : 0.3f);
        }
    }

    /// <summary>A loop that follows the player at a volume, started and stopped as the volume comes and goes.</summary>
    private void L55Loop(ref ILoadedSound sound, string location, float volume)
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
    /// The sphere of fog round the player that hides the outside sky (its sun, moon and stars) while in the level, the colour
    /// the fog is now, eased in and out; the other levels' spheres are left alone.
    /// </summary>
    private void L55SkySphere(float dt, bool here)
    {
        l55Sky += ((here ? 1f : 0f) - l55Sky) * Math.Min(1f, dt * 2f);
        DefaultShaderUniforms uniforms = capi.Render.ShaderUniforms;
        if (l55Sky < 0.01f)
        {
            if (l55SphereSet) uniforms.FogSphereQuantity = 0;
            l55SphereSet = false;
            return;
        }
        Vec4f fogColor = capi.Ambient.BlendedFogColor;
        float[] sphere = uniforms.FogSpheres;
        sphere[0] = sphere[1] = sphere[2] = 0;
        sphere[3] = SkySphereRadius;
        sphere[4] = SkySphereDensity * 1.3f * l55Sky;
        sphere[5] = fogColor.R;
        sphere[6] = fogColor.G;
        sphere[7] = fogColor.B;
        uniforms.FogSphereQuantity = 1;
        l55SphereSet = true;
    }
}
