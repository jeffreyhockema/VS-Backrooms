using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Zone = Backrooms.Worldgen.WorldLayout.L15Zone;

namespace Backrooms;

/// <summary>
/// Level 15, "Futuristic Halls"'s air and sound on the client (experimental, kept as level 27). Its base fog (its entry in
/// <see cref="Levels"/>) is the halls' clean, faintly cool air; where the power is out the air closes in, near black and
/// stale; the service passages are greyer, a crematorium smoky, the star door's room a deep blue. Everywhere the hum
/// (the machinery both wikis hear, and engines far off), louder in the machine rooms and faint in the dark; the air
/// handlers' whoosh in the service passages; far-off beeps now and then where the power is on; and in the dark a
/// ticking like a heartbeat (Fandom), which slows the longer you stay there. Titles for the dark, the machine rooms, the
/// service passages, the control rooms, the lecture halls, the crematoria and the star door. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L15DarkAir = new(0.022f, 0.025f, 0.028f, 0.034f, 0f);
    private static readonly Atmosphere L15ServiceAir = new(0.007f, 0.42f, 0.43f, 0.43f, 0f);
    private static readonly Atmosphere L15SmokeAir = new(0.012f, 0.30f, 0.27f, 0.24f, 0f);
    private static readonly Atmosphere L15StarAir = new(0.016f, 0.03f, 0.05f, 0.13f, 0f);
    private ILoadedSound l15Hum, l15Air, l15Heart;
    private float l15HumVolume, l15AirVolume, l15HeartVolume, l15BeepClock = 20f, l15DarkTime;

    private Tile L15TileAt(EntityPos pos) => layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void L15Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        Tile t = L15TileAt(pos);
        Zone zone = WorldLayout.L15ZoneOf(t);
        if (zone == Zone.Star)
        {
            target = L15StarAir;
            titleKey = 2708;
            return;
        }
        if (WorldLayout.L15IsDark(t))
        {
            target = L15DarkAir;
            titleKey = 2701;
            return;
        }
        switch (zone)
        {
            case Zone.Service: target = L15ServiceAir; titleKey = 2703; break;
            case Zone.Machine or Zone.Wreck: titleKey = 2702; break;
            case Zone.Control: titleKey = 2704; break;
            case Zone.Lecture: titleKey = 2705; break;
            case Zone.Lab: titleKey = 2706; break;
            case Zone.Crematorium: target = L15SmokeAir; titleKey = 2707; break;
            case Zone.Canteen: titleKey = 2709; break;
            case Zone.Medical: titleKey = 2710; break;
            case Zone.Hydro: titleKey = 2711; break;
        }
    }

    private void L15Sounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            L15Stop(ref l15Hum);
            L15Stop(ref l15Air);
            L15Stop(ref l15Heart);
            l15DarkTime = 0;
            return;
        }
        Tile t = L15TileAt(pos);
        Zone zone = WorldLayout.L15ZoneOf(t);
        bool dark = WorldLayout.L15IsDark(t);
        // The hum: everywhere, loudest among the machines, faint where they have stopped
        float hum = dark ? 0.1f : zone switch
        {
            Zone.Machine => 0.42f,
            Zone.Wreck => 0.3f,
            Zone.Service => 0.3f,
            Zone.Hall => 0.26f,
            Zone.Star => 0.06f,
            _ => 0.22f,
        };
        L15Loop(ref l15Hum, ref l15HumVolume, "backrooms:sounds/ambient/15/hum", hum, dt);
        L15Loop(ref l15Air, ref l15AirVolume, "backrooms:sounds/ambient/15/airhandler", zone == Zone.Service && !dark ? 0.32f : 0f, dt);
        // The ticking in the dark: it slows the longer you stay (Fandom: "slows until power returns")
        l15DarkTime = dark ? l15DarkTime + dt : Math.Max(0, l15DarkTime - dt * 4);
        L15Loop(ref l15Heart, ref l15HeartVolume, "backrooms:sounds/ambient/15/heartbeat", dark ? 0.3f : 0f, dt);
        l15Heart?.SetPitch(1f - 0.3f * Math.Min(1f, l15DarkTime / 240f));
        if (dark) return;
        // Now and then a beep, somewhere far off down the halls
        l15BeepClock -= dt;
        if (l15BeepClock > 0) return;
        l15BeepClock = 18 + (float)rand.NextDouble() * 30;
        double angle = rand.NextDouble() * Math.PI * 2, r = 18 + rand.NextDouble() * 22;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/15/beep" + (1 + rand.Next(3))),
            pos.X + Math.Cos(angle) * r, pos.Y + 2, pos.Z + Math.Sin(angle) * r, null, true, 48, 0.3f);
    }

    /// <summary>Keeps a looping sound going, easing its volume toward <paramref name="want"/>; stops it once it has faded out.</summary>
    private void L15Loop(ref ILoadedSound sound, ref float volume, string location, float want, float dt)
    {
        if (sound == null)
        {
            if (want <= 0) return;
            volume = 0.01f;
            sound = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation(location), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = volume, SoundType = EnumSoundType.Ambient,
            });
            sound?.Start();
            return;
        }
        float next = volume + Math.Clamp(want - volume, -dt * 0.3f, dt * 0.3f);
        if (next <= 0.005f && want <= 0)
        {
            L15Stop(ref sound);
            volume = 0;
            return;
        }
        if (Math.Abs(next - volume) > 0.002f)
        {
            volume = next;
            sound.SetVolume(volume);
        }
    }

    private static void L15Stop(ref ILoadedSound sound)
    {
        if (sound == null) return;
        sound.Stop();
        sound.Dispose();
        sound = null;
    }
}
