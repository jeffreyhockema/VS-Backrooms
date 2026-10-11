using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// Level 10's sky and weather on the client. The lore's sky is "an overcast, leaden sky, with brief and infrequent
/// spells of light rain and fog".
/// <list type="bullet">
/// <item><b>No sun.</b> Vintage Story fogs the sun as if it hung a few blocks off (it is drawn that close), so no fog
/// thin enough to see the fields through hides it. A fog sphere does: the game's fog spheres (vanilla's own use is round
/// the devastation tower) take the alpha of the sun and the moon down by their radius times their density, and colour
/// the sky dome beyond them. One round the player, of the fog's own colour, with a radius times density a little over
/// one, takes the sun, the moon, the stars, the sun's glow and godrays and every patch of blue, and leaves the land as
/// it was: within the view distance it is far thinner than the level's own fog, and the game only lets a sphere's fog
/// through where it is thicker than half the fog already there.</item>
/// <item><b>Spells of fog.</b> Now and then (about one half-day in three, never on the same hours twice) a spell of
/// thick fog rolls over the fields for a few minutes, the same for everyone in the world, and lifts again. There is no
/// rain: Vintage Story's rain comes from its weather simulation, which runs by region rather than by level, and wets
/// whoever stands in it, puts out fires and fills barrels; the levels next to Level 10 would get it too, and every
/// level's climate is held dry (<see cref="BackroomsModSystem"/>).</item>
/// </list>
/// </summary>
public partial class AtmosphereSystem
{
    /// <summary>The sky sphere: its radius, and its density at full (radius times density a little over one).</summary>
    private const float SkySphereRadius = 2000f, SkySphereDensity = 0.0006f;

    /// <summary>A half-day in which a spell of fog may come, the chance it does, and how long one lasts (in-game hours).</summary>
    private const double FogSpellSlot = 12, FogSpellChance = 0.3, FogSpellShortest = 1.5, FogSpellLongest = 3;

    /// <summary>The thick of a spell of fog: thick and pale, the ground fog risen to the knees.</summary>
    private const float SpellDensity = 0.035f, SpellFogMin = 0.1f, SpellGroundFog = -0.35f;
    private static readonly float[] SpellGrey = { 0.68f, 0.69f, 0.70f };

    private float farmSky;
    private bool farmSphereSet;

    /// <summary>The spell of fog that may come in a half-day: when it starts and how long it lasts (in hours), or null if none does.</summary>
    private static (double Start, double Length)? FogSpellIn(int worldSeed, long slot)
    {
        ulong h = Hashing.Hash((ulong)(uint)worldSeed, (int)slot, (int)(slot >> 32), 0x10F0);
        if (Hashing.Unit(h) >= FogSpellChance) return null;
        double length = FogSpellShortest + (FogSpellLongest - FogSpellShortest) * Hashing.Unit(Hashing.Mix(h));
        return (slot * FogSpellSlot + (FogSpellSlot - length) * Hashing.Unit(Hashing.Mix(h + 1)), length);
    }

    /// <summary>How far into a spell of fog Level 10 is at a moment (0 clear, 1 at its thickest), from the calendar and the seed.</summary>
    public static float L10FogSpell(int worldSeed, double totalHours)
    {
        if (FogSpellIn(worldSeed, (long)Math.Floor(totalHours / FogSpellSlot)) is not { } spell) return 0;
        double t = (totalHours - spell.Start) / spell.Length;
        if (t <= 0 || t >= 1) return 0;
        // It rolls in over the first quarter of the spell and lifts over the last
        double e = Math.Min(1, Math.Min(t, 1 - t) / 0.25);
        return (float)(e * e * (3 - 2 * e));
    }

    /// <summary>The middle of the next spell of fog over Level 10 after a moment (in total hours), for the cheat that skips to it.</summary>
    public static double NextL10FogSpell(int worldSeed, double totalHours)
    {
        for (long slot = (long)Math.Floor(totalHours / FogSpellSlot); ; slot++)
            if (FogSpellIn(worldSeed, slot) is { } spell && spell.Start + spell.Length / 2 > totalHours) return spell.Start + spell.Length / 2;
    }

    private void L10Air(ref Atmosphere target)
    {
        float spell = L10FogSpell(capi.World.Seed, capi.World.Calendar.TotalHours);
        if (spell <= 0) return;
        target = new Atmosphere(GameMath.Lerp(target.Density, SpellDensity, spell),
            GameMath.Lerp(target.R, SpellGrey[0], spell), GameMath.Lerp(target.G, SpellGrey[1], spell), GameMath.Lerp(target.B, SpellGrey[2], spell),
            GameMath.Lerp(target.GroundFog, SpellGroundFog, spell), target.Scene, target.SceneWeight, target.Clouds, target.DayNight,
            target.CloudBrightness, GameMath.Lerp(target.FogMin, SpellFogMin, spell));
    }

    /// <summary>The sphere of fog that hides Level 10's sun, eased in and out with the level's own air (<paramref name="k"/>).</summary>
    private void L10Sky(float k, bool here)
    {
        farmSky += ((here ? 1f : 0f) - farmSky) * k;
        DefaultShaderUniforms uniforms = capi.Render.ShaderUniforms;
        if (farmSky < 0.01f)
        {
            if (farmSphereSet) uniforms.FogSphereQuantity = 0;
            farmSphereSet = false;
            return;
        }
        // Centred on the player (the spheres are placed relative to the camera), the colour the fog is now
        Vec4f fogColor = capi.Ambient.BlendedFogColor;
        float[] sphere = uniforms.FogSpheres;
        sphere[0] = sphere[1] = sphere[2] = 0;
        sphere[3] = SkySphereRadius;
        sphere[4] = SkySphereDensity * farmSky;
        sphere[5] = fogColor.R;
        sphere[6] = fogColor.G;
        sphere[7] = fogColor.B;
        uniforms.FogSphereQuantity = 1;
        farmSphereSet = true;
    }
}
