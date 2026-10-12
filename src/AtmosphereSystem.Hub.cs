using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// The Hub's air and sound on the client (kept as level 17). Its base fog is its entry in <see cref="Levels"/>: the
/// orange haze of the Crossroads. Out in the Far Tunnels, where the lamps die, it is darker and closer; in the Tower,
/// dusky rose. And it is silent: canon says "completely devoid of sound", so there is no hum, only (Fandom) a drone so
/// faint it is nearly not there, whose pitch shifts every few minutes. Only the Tower hears the storm outside: thunder
/// through its walls, and wind that is a draught at its foot and gusts round the meeting hall and its balcony.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere HubFar = new(0.016f, 0.14f, 0.09f, 0.05f, 0f);
    private static readonly Atmosphere HubTower = new(0.006f, 0.42f, 0.31f, 0.28f, 0f);

    /// <summary>The Tower's and the Far Tunnels' titles (level-1701, level-1702 in the lang file).</summary>
    private const int HubTowerKey = 1701, HubFarKey = 1702;

    private ILoadedSound hubDrone, hubWind;
    private float hubPitchClock, hubThunderClock = 20;

    private void HubAir(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        double r = layout.HubDistance((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));
        if (r < WorldLayout.HubRoundabout - WorldLayout.HubMainHalf - 1)
        {
            target = HubTower;
            titleKey = HubTowerKey;
        }
        else if (r >= WorldLayout.HubKnownRadius)
        {
            target = HubFar;
            titleKey = HubFarKey;
        }
    }

    private void HubSounds(float dt, EntityPos pos, bool here)
    {
        if (here && hubDrone == null)
        {
            hubDrone = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/hub/silence"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = 0.25f, SoundType = EnumSoundType.Ambient,
            });
            hubDrone?.Start();
            hubPitchClock = 0;
        }
        else if (!here && hubDrone != null)
        {
            hubDrone.Stop();
            hubDrone.Dispose();
            hubDrone = null;
        }
        bool tower = hubDrone != null && layout.InHubTower(pos.X, pos.Z);
        HubWind(pos, tower);
        if (hubDrone == null) return;
        // In the Tower, now and then, thunder from the storm outside, through thick walls
        if (tower)
        {
            hubThunderClock -= dt;
            if (hubThunderClock <= 0)
            {
                hubThunderClock = 60 + (float)rand.NextDouble() * 120;
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/hub/thunder" + (1 + rand.Next(3))), pos.X, pos.Y + 20, pos.Z, null, true, 64, 0.6f);
            }
        }
        // Every three minutes or so the drone settles on another pitch
        hubPitchClock -= dt;
        if (hubPitchClock > 0) return;
        hubPitchClock = 150 + (float)rand.NextDouble() * 60;
        float[] pitches = { 1f, 0.94f, 1.06f, 0.89f };
        hubDrone.SetPitch(pitches[rand.Next(pitches.Length)]);
    }

    /// <summary>The storm's wind round the Tower: faint at its foot, rising with the stair to the meeting hall (and its balcony over the void).</summary>
    private void HubWind(EntityPos pos, bool tower)
    {
        if (!tower)
        {
            if (hubWind == null) return;
            hubWind.Stop();
            hubWind.Dispose();
            hubWind = null;
            return;
        }
        if (hubWind == null)
        {
            hubWind = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/hub/wind"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = 0f, SoundType = EnumSoundType.Ambient,
            });
            hubWind?.Start();
        }
        float up = GameMath.Clamp((float)(pos.Y - geometry.FloorFor(WorldLayout.Hub)) / WorldLayout.HubTowerHall, 0f, 1f);
        hubWind?.SetVolume(0.05f + 0.35f * up);
    }
}
