using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Zone = Backrooms.Worldgen.WorldLayout.L31Zone;

namespace Backrooms;

/// <summary>
/// Level 31, "Roller Rink"'s air and sound on the client (experimental, kept as level 24). Its base fog (its entry in
/// <see cref="Levels"/>) is a thin indigo haze lit by the coloured tubes; the cinema, the emptinesses and the glowing-carpet
/// rooms are darker and closer, the snack bar warmer. Titles name the rink, the arcade, the snack bar, the rental counter
/// and the cinema. Sound: one muffled synth-pop loop from ceiling speakers somewhere (loudest out on the rink, quiet in
/// the back rooms, gone in the cinema and the empty rooms, which have a faint room tone instead); now and then an arcade
/// machine's attract jingle close by in an arcade. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L31Dark = new(0.020f, 0.04f, 0.03f, 0.08f, 0f);
    private static readonly Atmosphere L31Warm = new(0.008f, 0.24f, 0.15f, 0.12f, 0f);
    private ILoadedSound l31Music, l31Room;
    private float l31Volume, l31Attract = 8;

    private Tile L31TileAt(EntityPos pos) => layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void L31Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        switch (L31TileAt(pos).Zone)
        {
            case (byte)Zone.Rink or (byte)Zone.Skirt: titleKey = 2401; break;
            case (byte)Zone.Arcade: titleKey = 2402; break;
            case (byte)Zone.Snack: target = L31Warm; titleKey = 2403; break;
            case (byte)Zone.Rental: titleKey = 2404; break;
            case (byte)Zone.Cinema: target = L31Dark; titleKey = 2405; break;
            case (byte)Zone.Empty or (byte)Zone.CarpetRoom: target = L31Dark; break;
        }
    }

    /// <summary>How loud the speakers are in each part of the level.</summary>
    private static float L31MusicVolume(byte zone) => zone switch
    {
        (byte)Zone.Rink or (byte)Zone.Skirt => 0.34f,
        (byte)Zone.Lobby or (byte)Zone.Hall or (byte)Zone.Crossing => 0.24f,
        (byte)Zone.Snack or (byte)Zone.Rental or (byte)Zone.Lounge => 0.18f,
        (byte)Zone.Cinema or (byte)Zone.Empty or (byte)Zone.CarpetRoom => 0f,
        _ => 0.11f,
    };

    private ILoadedSound L31Loop(string path, float volume)
    {
        ILoadedSound sound = capi.World.LoadSound(new SoundParams
        {
            Location = new AssetLocation(path), ShouldLoop = true, RelativePosition = true, DisposeOnFinish = false,
            Volume = volume, SoundType = EnumSoundType.Ambient,
        });
        sound?.Start();
        return sound;
    }

    private static void L31Stop(ref ILoadedSound sound)
    {
        if (sound == null) return;
        sound.Stop();
        sound.Dispose();
        sound = null;
    }

    private void L31Sounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            L31Stop(ref l31Music);
            L31Stop(ref l31Room);
            l31Volume = 0;
            return;
        }
        byte zone = L31TileAt(pos).Zone;

        // The music: one loop, faded toward each part's loudness
        float want = L31MusicVolume(zone);
        l31Volume += Math.Clamp(want - l31Volume, -dt * 0.25f, dt * 0.25f);
        if (l31Music == null && l31Volume > 0.005f) l31Music = L31Loop("backrooms:sounds/ambient/31/rinkmusic", l31Volume);
        if (l31Music != null)
        {
            if (l31Volume <= 0.005f && want == 0) L31Stop(ref l31Music);
            else l31Music.SetVolume(l31Volume);
        }

        // Room tone where the music does not reach
        bool quiet = want == 0;
        if (quiet && l31Room == null) l31Room = L31Loop("backrooms:sounds/ambient/end/roomtone", 0.16f);
        else if (!quiet && l31Room != null) L31Stop(ref l31Room);

        // An arcade machine's attract jingle, somewhere close by
        if (zone != (byte)Zone.Arcade) return;
        l31Attract -= dt;
        if (l31Attract > 0) return;
        l31Attract = 7 + (float)rand.NextDouble() * 9;
        double angle = rand.NextDouble() * Math.PI * 2, r = 3 + rand.NextDouble() * 9;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/3999/attract-" + (1 + rand.Next(4))),
            pos.X + Math.Cos(angle) * r, pos.Y + 1, pos.Z + Math.Sin(angle) * r, null, true, 16, 0.3f);
    }
}
