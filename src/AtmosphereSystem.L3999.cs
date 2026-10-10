using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;

namespace Backrooms;

/// <summary>
/// Level 3999, "The Neon Paradise"'s air and sound on the client (kept as level 19). Its base fog is its entry in
/// <see cref="Levels"/>: thin, dark violet black-light air, so the far end of a concourse fades to purple, never to grey.
/// The Natatorium is a warm lilac haze; the Neon Blackout (3999.1) close and brown-black.
///
/// Sound: faint mall music of mysterious origin, different for each wanderer (canon): one of four loops, picked by the
/// player's id, low and sourceless, silent in the Blackout; a very quiet neon hum; now and then a cabinet's attract
/// jingle somewhere nearby; lapping in the Natatorium; drips and a dead relay in the Blackout.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L3999Natatorium = new(0.008f, 0.45f, 0.30f, 0.55f, 0f);
    private static readonly Atmosphere L3999Blackout = new(0.03f, 0.06f, 0.05f, 0.05f, 0f);

    /// <summary>The Blackout's and the Natatorium's titles (level-1901, level-1902 in the lang file).</summary>
    private const int L3999BlackoutKey = 1901, L3999NatatoriumKey = 1902;

    private static readonly string[] L3999Music = { "dream", "nostalgia", "glide", "lonely" };

    private ILoadedSound l3999Music, l3999Hum, l3999Zone;
    private string l3999ZonePlaying;
    private float l3999AttractClock = 8;

    private void L3999Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        Tile t = layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));
        if (WorldLayout.L3999IsDark(t))
        {
            target = L3999Blackout;
            titleKey = L3999BlackoutKey;
        }
        else if (t.Zone == (byte)WorldLayout.L3999Zone.Natatorium)
        {
            target = L3999Natatorium;
            titleKey = L3999NatatoriumKey;
        }
    }

    private ILoadedSound L3999Loop(string path, float volume)
    {
        ILoadedSound sound = capi.World.LoadSound(new SoundParams
        {
            Location = new AssetLocation(path), ShouldLoop = true, RelativePosition = true, DisposeOnFinish = false, Volume = volume,
            SoundType = EnumSoundType.Ambient,
        });
        sound?.Start();
        return sound;
    }

    private static void L3999Stop(ref ILoadedSound sound)
    {
        if (sound == null) return;
        sound.Stop();
        sound.Dispose();
        sound = null;
    }

    private void L3999Sounds(float dt, EntityPos pos, bool here)
    {
        Tile t = here ? layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)) : default;
        bool dark = here && WorldLayout.L3999IsDark(t);
        bool lit = here && !dark;
        // The music and the hum, wherever the neon still works
        if (lit && l3999Music == null)
        {
            string uid = capi.World.Player?.PlayerUID ?? "";
            int pick = 0;
            foreach (char c in uid) pick = (pick * 31 + c) & 0x7FFFFFFF;
            l3999Music = L3999Loop("backrooms:sounds/ambient/3999/music-" + L3999Music[pick % L3999Music.Length], 0.25f);
            l3999Hum = L3999Loop("backrooms:sounds/ambient/3999/neonhum", 0.08f);
        }
        else if (!lit && l3999Music != null)
        {
            L3999Stop(ref l3999Music);
            L3999Stop(ref l3999Hum);
        }
        // The Natatorium's lapping, the Blackout's drips
        string zone = !here ? null : dark ? "blackout" : t.Zone == (byte)WorldLayout.L3999Zone.Natatorium ? "natatorium" : null;
        if (zone != l3999ZonePlaying)
        {
            L3999Stop(ref l3999Zone);
            if (zone != null) l3999Zone = L3999Loop("backrooms:sounds/ambient/3999/" + zone, 0.35f);
            l3999ZonePlaying = zone;
        }
        if (!lit) return;
        // Now and then a cabinet's attract jingle, somewhere close by
        l3999AttractClock -= dt;
        if (l3999AttractClock > 0) return;
        l3999AttractClock = 6 + (float)rand.NextDouble() * 8;
        if (t.Zone is not ((byte)WorldLayout.L3999Zone.Game or (byte)WorldLayout.L3999Zone.GameHall or (byte)WorldLayout.L3999Zone.MiniArcade)) return;
        double angle = rand.NextDouble() * Math.PI * 2, r = 4 + rand.NextDouble() * 12;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/3999/attract-" + (1 + rand.Next(4))),
            pos.X + Math.Cos(angle) * r, pos.Y + 1, pos.Z + Math.Sin(angle) * r, null, true, 20, 0.35f);
    }
}
