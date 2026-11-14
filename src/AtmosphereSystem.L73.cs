using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level 73, "The Redlands"'s air and sound on the client (experimental, kept as level 21). Its base fog (its entry in
/// <see cref="Levels"/>) is a thin crimson-black murk under a dim, unchanging night; over the sea it thickens, and in the
/// keep of the Silver Castle it is close, warm and lit by its fires. The sky is hidden in a sphere of fog of the fog's own
/// colour (as Level 10's sun is, <see cref="L10Sky"/>), so the outside day never shows; the full moon that hangs fixed over
/// the sea is drawn by Regions.L73Moon. Now and then black cloud covers the moon for a while
/// (<see cref="L73DarkSpell"/>): the night goes darker still and the moon is gone.
///
/// The sound bed is all reused: the wind, the surf louder toward the coast, a far-off howl now and then, a heartbeat
/// heard faintly; in the keep, the fire crackling in the dining hall, timber creaking, a step somewhere overhead. This
/// file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    // (scene 0.48 / 0.44, a shade up from round 4's 0.44 / 0.40 and its 0.36 / 0.33 before, so the ridges, trees and rocks read by the moon alone)
    // (clouds 0: vanilla's clouds are hidden, never drawn low and white over the island's night; the lore's black cloud is
    // the dark spell, which takes the moon away rather than drawing cloud)
    private static readonly Atmosphere L73Island = new(0.0035f, 0.10f, 0.03f, 0.035f, -0.12f, scene: 0.48f, clouds: 0f, cloudBrightness: 0f);
    private static readonly Atmosphere L73SeaAir = new(0.0060f, 0.08f, 0.025f, 0.03f, -0.18f, scene: 0.44f, clouds: 0f, cloudBrightness: 0f);
    private static readonly Atmosphere L73KeepAir = new(0.0015f, 0.12f, 0.07f, 0.035f, 0f, scene: 0.85f, clouds: 0f, cloudBrightness: 0f);

    /// <summary>The title key of the castle's keep (level-2101 in the lang file).</summary>
    private const int L73KeepKey = 2101;

    private ILoadedSound l73Wind, l73Surf, l73Fire;
    private float l73NextHowl = 40, l73NextBeat = 70, l73NextCreak = 15, l73NextStep = 50;
    private float l73Sky;
    private bool l73SphereSet;

    // The ways in (WorldLayout.Level73.Links.cs): how long the player has stood in the Gloom (Level 9) or in Level 6's deepest
    // dark with no light, as the client counts it (the server keeps its own count and does the taking); the black that closes
    // round them in the Gloom (0-1); the next beat of the heart heard there
    private float l73GloomTime, l73DarkTime, l73GloomFog, l73LingerBeat;

    /// <summary>How long the Gloom takes (seconds, as Regions.L73System.Links), and Level 6's deepest dark.</summary>
    private const float L73GloomTakes = 90f, L73DarkTakes = 180f;

    /// <summary>A slot of game hours in which the moon may be covered, the chance it is, and how long for (in game hours).</summary>
    private const double L73SpellSlot = 2, L73SpellChance = 0.35, L73SpellLength = 0.35;

    /// <summary>
    /// How far the moon is covered by black cloud at a moment (0 clear, 1 gone), the same for everyone in the world: in
    /// about one slot of two game hours in three, for a third of an hour (some forty seconds at the usual speed).
    /// </summary>
    public static float L73DarkSpell(int worldSeed, double totalHours)
    {
        long slot = (long)Math.Floor(totalHours / L73SpellSlot);
        ulong h = Hashing.Hash((ulong)(uint)worldSeed, (int)slot, (int)(slot >> 32), 0x2110);
        if (Hashing.Unit(h) >= L73SpellChance) return 0;
        double start = slot * L73SpellSlot + (L73SpellSlot - L73SpellLength) * Hashing.Unit(Hashing.Mix(h));
        double t = (totalHours - start) / L73SpellLength;
        if (t <= 0 || t >= 1) return 0;
        double e = Math.Min(1, Math.Min(t, 1 - t) / 0.2);
        return (float)(e * e * (3 - 2 * e));
    }

    /// <summary>Where the player is: in the keep (and on which storey), or out over the sea.</summary>
    private (bool Keep, bool Sea) L73Where(EntityPos pos)
    {
        int bx = (int)Math.Floor(pos.X), bz = (int)Math.Floor(pos.Z);
        double rel = pos.Y - geometry.FloorFor(WorldLayout.Level73);
        bool keep = layout.InL73Keep(bx, bz) && rel > WorldLayout.L73Plateau - WorldLayout.L73CellarDepth && rel < WorldLayout.L73Plateau + WorldLayout.L73Terrace;
        bool sea = !keep && layout.L73Shore(bx, bz, out _) > 8;
        return (keep, sea);
    }

    private void L73Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        var (keep, sea) = L73Where(pos);
        if (keep)
        {
            target = L73KeepAir;
            titleKey = L73KeepKey;
            return;
        }
        target = sea ? L73SeaAir : L73Island;
        float spell = L73DarkSpell(capi.World.Seed, capi.World.Calendar.TotalHours);
        if (spell > 0)
            target = new Atmosphere(GameMath.Lerp(target.Density, target.Density * 2.5f, spell), target.R * (1 - 0.5f * spell), target.G * (1 - 0.5f * spell),
                target.B * (1 - 0.5f * spell), target.GroundFog, GameMath.Lerp(target.Scene, 0.12f, spell), target.SceneWeight, target.Clouds,
                target.DayNight, target.CloudBrightness, target.FogMin);
    }

    private void L73Sounds(float dt, EntityPos pos, bool here)
    {
        L73Lingering(dt, pos);
        L73SkySphere(dt, here);
        if (!here)
        {
            L188Stop(ref l73Wind);
            L188Stop(ref l73Surf);
            L188Stop(ref l73Fire);
            return;
        }
        var (keep, _) = L73Where(pos);
        double beyond = layout.L73Shore((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z), out _);

        // The wind, muffled in the keep; the surf, louder toward the coast and out over the sea
        L73Loop(ref l73Wind, "game:sounds/environment/wind", keep ? 0.08f : 0.35f);
        float surf = (float)Math.Clamp((beyond + 120) / 120, 0, 1);
        L73Loop(ref l73Surf, "game:sounds/environment/waterwaves", keep ? 0f : 0.05f + 0.4f * surf * surf);

        // The nearest fire on the storey one is on: the dining hall's hearth, the fireplaces (round 3)
        double floor = geometry.FloorFor(WorldLayout.Level73) + WorldLayout.L73Plateau;
        int storey = Math.Clamp((int)Math.Floor((pos.Y - floor - 1) / WorldLayout.L73Storey), 0, 2);
        var (hx, hz) = layout.L73NearestFire(pos.X, pos.Z, storey);
        L188Positional(ref l73Fire, "game:sounds/environment/fireplace", pos, hx, floor + storey * WorldLayout.L73Storey + 1.5, hz, 16, 0.7f);

        if (keep)
        {
            // Timber creaking; on the ground storey, a step somewhere overhead
            l73NextCreak -= dt;
            if (l73NextCreak <= 0)
            {
                l73NextCreak = 18 + (float)rand.NextDouble() * 30;
                double yaw = rand.NextDouble() * Math.PI * 2;
                capi.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/ambient/974/creak{1 + rand.Next(3)}"), pos.X + Math.Sin(yaw) * 5, pos.Y + 2,
                    pos.Z + Math.Cos(yaw) * 5, null, randomizePitch: true, range: 24, volume: 0.3f);
            }
            l73NextStep -= dt;
            if (l73NextStep <= 0)
            {
                l73NextStep = 40 + (float)rand.NextDouble() * 50;
                int over = ((int)(pos.Y - floor) / WorldLayout.L73Storey + 1) * WorldLayout.L73Storey;
                if (over < WorldLayout.L73Terrace)
                    capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/end/echostep"), pos.X + rand.Next(-6, 7), floor + over + 1,
                        pos.Z + rand.Next(-6, 7), null, randomizePitch: true, range: 24, volume: 0.2f);
            }
            return;
        }

        // Out on the island: a howl far off now and then, too far to place; a faint wet pulse, like a heartbeat
        l73NextHowl -= dt;
        if (l73NextHowl <= 0)
        {
            l73NextHowl = 45 + (float)rand.NextDouble() * 60;
            double yaw = rand.NextDouble() * Math.PI * 2;
            capi.World.PlaySoundAt(new AssetLocation($"game:sounds/creature/wolf/howl{1 + rand.Next(7)}"), pos.X + Math.Sin(yaw) * 20, pos.Y + 2,
                pos.Z + Math.Cos(yaw) * 20, null, randomizePitch: true, range: 48, volume: 0.18f);
        }
        l73NextBeat -= dt;
        if (l73NextBeat <= 0)
        {
            l73NextBeat = 70 + (float)rand.NextDouble() * 70;
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/run/heartbeat"), capi.World.Player.Entity, null, randomizePitch: false, range: 8,
                volume: 0.07f);
        }
    }

    /// <summary>A loop that follows the player at a volume, started and stopped as the volume comes and goes.</summary>
    private void L73Loop(ref ILoadedSound sound, string location, float volume)
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
    /// The sphere of fog round the player that hides the outside sky (its sun, moon and stars and its blue) while in the
    /// level, the colour the fog is now, eased in and out; Level 10's own sphere is left alone.
    /// </summary>
    private void L73SkySphere(float dt, bool here)
    {
        l73Sky += ((here ? 1f : 0f) - l73Sky) * Math.Min(1f, dt * 2f);
        DefaultShaderUniforms uniforms = capi.Render.ShaderUniforms;
        if (l73Sky < 0.01f && l73GloomFog >= 0.01f)
        {
            // In the Gloom (Level 9): a black that closes in round the player, tighter the longer they stay
            float[] dark = uniforms.FogSpheres;
            dark[0] = dark[1] = dark[2] = 0;
            dark[3] = 48f;
            dark[4] = 0.32f * l73GloomFog;
            dark[5] = dark[6] = dark[7] = 0.004f;
            uniforms.FogSphereQuantity = 1;
            l73SphereSet = true;
            return;
        }
        if (l73Sky < 0.01f)
        {
            if (l73SphereSet) uniforms.FogSphereQuantity = 0;
            l73SphereSet = false;
            return;
        }
        Vec4f fogColor = capi.Ambient.BlendedFogColor;
        float[] sphere = uniforms.FogSpheres;
        sphere[0] = sphere[1] = sphere[2] = 0;
        sphere[3] = SkySphereRadius;
        sphere[4] = SkySphereDensity * 1.3f * l73Sky;
        sphere[5] = fogColor.R;
        sphere[6] = fogColor.G;
        sphere[7] = fogColor.B;
        uniforms.FogSphereQuantity = 1;
        l73SphereSet = true;
    }

    /// <summary>
    /// The ways in, as the player feels them (the server does the taking, Regions/L73System.Links.cs). Standing in the Gloom in
    /// Level 9: the dark closes in round them (<see cref="L73SkySphere"/>) and a slow heartbeat comes, louder and quicker the
    /// longer they stay. In Level 6's deepest dark with no light: the same heart, faint and far off, as if under the floor.
    /// </summary>
    private void L73Lingering(float dt, EntityPos pos)
    {
        EntityPlayer entity = capi.World.Player?.Entity;
        bool playing = entity != null && capi.World.Player.WorldData.CurrentGameMode is not (EnumGameMode.Creative or EnumGameMode.Spectator);
        int bx = (int)Math.Floor(pos.X), bz = (int)Math.Floor(pos.Z);
        int level = layout.LevelAt(WorldLayout.MacroOf(bx), WorldLayout.MacroOf(bz));
        bool gloom = false, dark = false;
        if (playing && level == 9)
        {
            double rel = pos.Y - geometry.FloorFor(9);
            gloom = rel > 0.5 && rel < 3.5 && WorldLayout.IsL73Gloom(layout.TileAt(bx, bz));
        }
        else if (playing && level == 6 && layout.IsL73DarkCell(WorldLayout.MacroOf(bx), WorldLayout.MacroOf(bz)))
            dark = Entities.Senses.HeldLight(entity) < Entities.Senses.LitLevel
                && capi.World.BlockAccessor.GetLightLevel(new BlockPos(bx, (int)Math.Floor(pos.Y + 1.5), bz), EnumLightLevelType.OnlyBlockLight) <= 3;
        l73GloomTime = gloom ? l73GloomTime + dt : Math.Max(0, l73GloomTime - dt * 4);
        l73DarkTime = dark ? l73DarkTime + dt : Math.Max(0, l73DarkTime - dt * 2);

        // The black round them: at once a little, then more as they stay
        float fogTarget = gloom ? Math.Min(1f, 0.3f + 0.7f * l73GloomTime / L73GloomTakes) : 0f;
        l73GloomFog += (fogTarget - l73GloomFog) * Math.Min(1f, dt * (fogTarget > l73GloomFog ? 0.8f : 2.5f));
        if (l73GloomFog < 0.005f) l73GloomFog = 0;

        if (!gloom && !dark) return;
        float k = gloom ? Math.Min(1f, l73GloomTime / L73GloomTakes) : Math.Min(1f, l73DarkTime / L73DarkTakes);
        l73LingerBeat -= dt;
        if (l73LingerBeat > 0) return;
        // In the Gloom a beat every 6 s at first, every 1.5 at the last; in Level 6's dark one every 20 s, then 6
        l73LingerBeat = gloom ? 6f - 4.5f * k : 20f - 14f * k;
        float volume = gloom ? 0.12f + 0.3f * k : 0.04f + 0.12f * k;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/run/heartbeat"), entity, null, randomizePitch: false, range: 8, volume: volume);
    }
}
