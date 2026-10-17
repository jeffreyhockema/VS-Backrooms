using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Space = Backrooms.Worldgen.WorldLayout.L183Space;
using Zone = Backrooms.Worldgen.WorldLayout.L183Zone;

namespace Backrooms;

/// <summary>
/// Level 183, "Clean Sewers"'s air and sound on the client (experimental, kept as level 27). Its base fog (its entry in
/// <see cref="Levels"/>) is the mains' pale, clean blue-grey haze, thin so the long straight tunnels can be seen down; the
/// narrow side tunnels and galleries close in a little more, the chambers and halls a little less. Everywhere the sound of
/// running water in brick (the level's own loop), the Poolrooms' soft wash over the channels, drips and laps here and
/// there, and every few minutes a far-off clank down the tunnels. The title names the level on arriving, then the Trunk
/// Tunnels, the Channels and the Junction Halls as the player comes into each. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L183NarrowAir = new(0.04f, 0.770f, 0.825f, 0.830f, 0f);
    private static readonly Atmosphere L183ChamberAir = new(0.03f, 0.800f, 0.850f, 0.845f, 0f);

    /// <summary>Title keys for the three zones (2700 + the zone).</summary>
    private const int L183KeyBase = 2700;

    private ILoadedSound l183Flow, l183Wash;
    private Zone l183ArrivedIn;
    private bool l183Moved;
    private float l183NextDrip = 5, l183NextClank = 200;

    private (Zone Zone, Space Space) L183Here(EntityPos pos) => layout.L183Where((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void L183Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        var (zone, space) = L183Here(pos);
        if (space is Space.Side or Space.Gallery) target = L183NarrowAir;
        else if (space is Space.Chamber or Space.Hall) target = L183ChamberAir;
        if (zone == Zone.None) return;
        // On arriving, the level's own title; after that, each zone's name as the player comes into it
        if (l183ArrivedIn == Zone.None) l183ArrivedIn = zone;
        else if (zone != l183ArrivedIn) l183Moved = true;
        if (l183Moved) titleKey = L183KeyBase + (int)zone;
    }

    private void L183Sounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            L183Stop(ref l183Flow);
            L183Stop(ref l183Wash);
            l183ArrivedIn = Zone.None;
            l183Moved = false;
            return;
        }
        var (_, space) = L183Here(pos);
        bool open = space is Space.Main or Space.Chamber or Space.Hall;
        // Running water everywhere, loudest beside the mains' channels; the wash of the water over them
        L183Loop(ref l183Flow, "backrooms:sounds/ambient/183/sewer", open ? 0.45f : 0.3f);
        if (open) L183Loop(ref l183Wash, "backrooms:sounds/ambient/poolroom", 0.25f);
        else L183Stop(ref l183Wash);

        l183NextDrip -= dt;
        if (l183NextDrip <= 0)
        {
            l183NextDrip = 3 + (float)rand.NextDouble() * 9;
            double yaw = rand.NextDouble() * Math.PI * 2, dist = 3 + rand.NextDouble() * 12;
            string what = open && rand.NextDouble() < 0.35 ? "poollap" : "pooldrip";
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/" + what), pos.X + Math.Sin(yaw) * dist, pos.Y + 1,
                pos.Z + Math.Cos(yaw) * dist, null, 0.9f + (float)rand.NextDouble() * 0.25f, 32, 0.35f);
        }

        // Every few minutes, far down the tunnels, a clank: a drip slowed until it is a hatch or a valve somewhere
        l183NextClank -= dt;
        if (l183NextClank <= 0)
        {
            l183NextClank = 180 + (float)rand.NextDouble() * 300;
            double yaw = rand.NextDouble() * Math.PI * 2;
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/pooldrip"), pos.X + Math.Sin(yaw) * 24, pos.Y + 1,
                pos.Z + Math.Cos(yaw) * 24, null, 0.35f, 48, 0.45f);
        }
    }

    private void L183Loop(ref ILoadedSound sound, string location, float volume)
    {
        if (sound == null)
        {
            sound = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation(location), ShouldLoop = true, RelativePosition = true, DisposeOnFinish = false, Volume = volume,
                SoundType = EnumSoundType.Ambient,
            });
            sound?.Start();
        }
        else sound.SetVolume(volume);
    }

    private static void L183Stop(ref ILoadedSound sound)
    {
        sound?.Stop();
        sound?.Dispose();
        sound = null;
    }
}
