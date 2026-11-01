using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Zone = Backrooms.Worldgen.WorldLayout.L31Zone;

namespace Backrooms;

/// <summary>
/// Level 31, "Roller Rink"'s air and sound on the client (experimental, kept as level 24). Its base fog (its entry in
/// <see cref="Levels"/>) is a thin indigo haze lit by the coloured tubes; the cinema, the emptinesses and the glowing-carpet
/// rooms are darker and closer, the food court warmer. Titles name the rink, the arcade, the food court, the rental counter,
/// the cinema and the employees' lounge. Sound: one muffled synth-pop loop from ceiling speakers somewhere (loudest out on the rink, quiet in
/// the back rooms, gone in the cinema and the empty rooms, which have a faint room tone instead); now and then an arcade
/// machine's attract jingle close by in an arcade; skates and laughter overhead on the rink and in the halls; a CCTV camera's
/// servo in the silent employees' lounge. Out of the level: in Levels 2, 3 and 6, 2000s bubblegum pop playing faintly behind
/// a wooden door into the rink, when you come near one (the lore's way in). This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L31Dark = new(0.020f, 0.04f, 0.03f, 0.08f, 0f);
    private static readonly Atmosphere L31Warm = new(0.008f, 0.24f, 0.15f, 0.12f, 0f);
    private ILoadedSound l31Music, l31Room, l31DoorMusic;
    private float l31Volume, l31Attract = 8, l31Above = 20, l31Cctv = 15, l31DoorScan;
    private (int X, int Z)? l31DoorAt;

    /// <summary>How near a wooden door into the rink its music is heard from (blocks), and how far round a player one is looked for.</summary>
    private const int L31DoorRange = 18;

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
            case (byte)Zone.Lounge: titleKey = 2406; break;
        }
    }

    /// <summary>How loud the speakers are in each part of the level.</summary>
    private static float L31MusicVolume(byte zone) => zone switch
    {
        (byte)Zone.Rink or (byte)Zone.Skirt => 0.34f,
        (byte)Zone.Lobby or (byte)Zone.Hall or (byte)Zone.Crossing => 0.24f,
        (byte)Zone.Snack or (byte)Zone.Rental => 0.18f,
        // (the employees' lounge is eerily silent: Fandom)
        (byte)Zone.Cinema or (byte)Zone.Empty or (byte)Zone.CarpetRoom or (byte)Zone.Lounge => 0f,
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
            L31DoorSounds(dt, pos);
            return;
        }
        if (l31DoorMusic != null) { L31Stop(ref l31DoorMusic); l31DoorAt = null; }
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

        // Skates on the boards and laughter, heard "from above" (Fandom), out on the rink and in the halls and lobbies
        if (zone is (byte)Zone.Rink or (byte)Zone.Skirt or (byte)Zone.Hall or (byte)Zone.Crossing or (byte)Zone.Lobby or (byte)Zone.Snack)
        {
            l31Above -= dt;
            if (l31Above <= 0)
            {
                l31Above = 25 + (float)rand.NextDouble() * 35;
                double a = rand.NextDouble() * Math.PI * 2;
                bool laugh = rand.NextDouble() < 0.3;
                capi.World.PlaySoundAt(new AssetLocation(laugh ? "backrooms:sounds/entity/laughter" : "backrooms:sounds/ambient/31/skates"),
                    pos.X + Math.Cos(a) * 6, pos.Y + 9, pos.Z + Math.Sin(a) * 6, null, true, 24, laugh ? 0.12f : 0.35f);
            }
        }
        // A CCTV camera turning on its mount in the employees' lounge
        if (zone == (byte)Zone.Lounge)
        {
            l31Cctv -= dt;
            if (l31Cctv <= 0)
            {
                l31Cctv = 18 + (float)rand.NextDouble() * 30;
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/31/cctv"), pos.X + rand.Next(-4, 5), pos.Y + 2.5, pos.Z + rand.Next(-4, 5), null, true, 12, 0.3f);
            }
        }

        // An arcade machine's attract jingle, somewhere close by
        if (zone != (byte)Zone.Arcade) return;
        l31Attract -= dt;
        if (l31Attract > 0) return;
        l31Attract = 7 + (float)rand.NextDouble() * 9;
        double angle = rand.NextDouble() * Math.PI * 2, r = 3 + rand.NextDouble() * 9;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/3999/attract-" + (1 + rand.Next(4))),
            pos.X + Math.Cos(angle) * r, pos.Y + 1, pos.Z + Math.Sin(angle) * r, null, true, 16, 0.3f);
    }

    /// <summary>
    /// The music behind a wooden door into the rink (Wikidot, Fandom: "bubblegum pop from the middle of the 2000s playing on the
    /// other side"), in Levels 2, 3 and 6: a faint loop at the nearest such door within <see cref="L31DoorRange"/> blocks, looked
    /// for once a second.
    /// </summary>
    private void L31DoorSounds(float dt, EntityPos pos)
    {
        l31DoorScan -= dt;
        if (l31DoorScan > 0) return;
        l31DoorScan = 1;
        int px = (int)Math.Floor(pos.X), pz = (int)Math.Floor(pos.Z);
        int level = layout.LevelAt(WorldLayout.MacroOf(px), WorldLayout.MacroOf(pz));
        (int X, int Z)? door = null;
        if (level is 2 or 3 or 6)
        {
            int best = int.MaxValue;
            for (int dz = -L31DoorRange; dz <= L31DoorRange; dz++)
                for (int dx = -L31DoorRange; dx <= L31DoorRange; dx++)
                {
                    int d = dx * dx + dz * dz;
                    if (d >= best || d > L31DoorRange * L31DoorRange) continue;
                    if (WorldLayout.IsL31HostDoor(layout.TileAt(px + dx, pz + dz))) { best = d; door = (px + dx, pz + dz); }
                }
        }
        if (door == l31DoorAt) return;
        L31Stop(ref l31DoorMusic);
        l31DoorAt = door;
        if (door is not { } at) return;
        // (Behind the door, a little into the wall: it is the other side that plays)
        l31DoorMusic = capi.World.LoadSound(new SoundParams
        {
            Location = new AssetLocation("backrooms:sounds/ambient/31/doorpop"), ShouldLoop = true, DisposeOnFinish = false,
            Position = new Vec3f(at.X + 0.5f, geometry.FloorFor(level) + 1.5f, at.Z + 0.5f), RelativePosition = false,
            Range = L31DoorRange, Volume = 0.55f, SoundType = EnumSoundType.Ambient,
        });
        l31DoorMusic?.Start();
    }
}
