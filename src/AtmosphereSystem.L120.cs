using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Zone = Backrooms.Worldgen.WorldLayout.L120Zone;

namespace Backrooms;

/// <summary>
/// Level 120, "Broken Servos": its air and sound on the client (experimental, kept as level 26). Its base fog (its entry in
/// <see cref="Levels"/>) is near black; a hot aisle has a warm haze of its own, a White Void a glaring white, a Pitch-Black
/// Hallway a black that closes in. The sound bed is one loop chosen by where you are: the fans (brown noise, the mains hum,
/// a faint whine) among the server rooms, quiet in the passages; a clean high tone in the voids; near silence in the
/// hallways. Among the server rooms the machines still make their noises now and then, somewhere off in the dark: a hard
/// drive seeking, a relay, a fan spinning up and down, far-off static. Titles for the hot aisles, the terminal rooms, the
/// voids and the hallways. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L120HotAir = new(0.02f, 0.10f, 0.055f, 0.03f, 0f, scene: 0.8f);
    private static readonly Atmosphere L120VoidAir = new(0.012f, 0.96f, 0.96f, 0.95f, 0f, scene: 1.15f);
    private static readonly Atmosphere L120HallwayAir = new(0.045f, 0f, 0f, 0f, 0f, scene: 0.7f);
    private static readonly string[] L120Loops = { "serverhum", "voidtone", "hallway" };
    private static readonly string[] L120OneShots = { "hdd1", "hdd2", "relay", "fanspin", "farstatic" };
    private ILoadedSound l120Loop;
    private int l120LoopKind = -1;
    private float l120Volume, l120NextShot = 6;

    private Tile L120TileAt(EntityPos pos) => layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void L120Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        switch (L120TileAt(pos).Zone)
        {
            case (byte)Zone.Hot: target = L120HotAir; titleKey = 2602; break;
            case (byte)Zone.Terminals: titleKey = 2603; break;
            case (byte)Zone.Void: target = L120VoidAir; titleKey = 2604; break;
            case (byte)Zone.Hallway: target = L120HallwayAir; titleKey = 2605; break;
        }
    }

    private void L120Sounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            L120StopLoop();
            return;
        }
        Tile t = L120TileAt(pos);
        int kind = t.Zone switch { (byte)Zone.Void => 1, (byte)Zone.Hallway => 2, _ => 0 };
        float want = kind switch
        {
            1 => 0.35f,
            2 => 0.5f,
            _ => t.Zone switch
            {
                (byte)Zone.Hot => 0.45f,
                (byte)Zone.Room or (byte)Zone.Wreck => 0.32f,
                (byte)Zone.Terminals => 0.22f,
                _ => 0.18f,
            },
        };
        if (kind != l120LoopKind)
        {
            // Into a pocket or out of one: the sound changes at once, as everything else does
            L120StopLoop();
            l120LoopKind = kind;
            l120Volume = want;
            l120Loop = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation($"backrooms:sounds/ambient/120/{L120Loops[kind]}"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = want, SoundType = EnumSoundType.Ambient,
            });
            l120Loop?.Start();
        }
        else if (l120Loop != null)
        {
            // Ease towards the zone's loudness over a second or two
            float next = l120Volume + Math.Clamp(want - l120Volume, -dt * 0.25f, dt * 0.25f);
            if (Math.Abs(next - l120Volume) > 0.002f)
            {
                l120Volume = next;
                l120Loop.SetVolume(l120Volume);
            }
        }

        // The machines in the dark: now and then, somewhere off among the server rooms
        if (kind != 0) return;
        l120NextShot -= dt;
        if (l120NextShot > 0) return;
        var rand = capi.World.Rand;
        l120NextShot = 7 + (float)rand.NextDouble() * 22;
        double angle = rand.NextDouble() * Math.PI * 2, far = 6 + rand.NextDouble() * 16;
        string shot = L120OneShots[rand.Next(L120OneShots.Length)];
        capi.World.PlaySoundAt(new AssetLocation($"backrooms:sounds/ambient/120/{shot}"), pos.X + Math.Cos(angle) * far, pos.Y + 1.5, pos.Z + Math.Sin(angle) * far,
            null, 0.9f + (float)rand.NextDouble() * 0.2f, 32, shot == "farstatic" ? 0.35f : 0.55f);
    }

    private void L120StopLoop()
    {
        l120LoopKind = -1;
        if (l120Loop == null) return;
        l120Loop.Stop();
        l120Loop.Dispose();
        l120Loop = null;
    }
}
