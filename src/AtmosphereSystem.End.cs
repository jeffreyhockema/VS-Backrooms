using System;
using Backrooms.Regions;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms;

/// <summary>
/// The End's air and sound on the client (kept as level 16; docs/design/new-levels/end-plan.md). Its base fog is its entry in
/// <see cref="Levels"/>: a thin warm-cream haze. Here:
/// <list type="bullet">
/// <item>a fake reality's heart has the air of the place it imitates (the Lobby's, the office's, the hotel's; the snow
/// bright and white; Home warm), and is named as one (title 1601);</item>
/// <item>during a distortion (the server says when, and which scene) the air swings to the scene's and the floor shakes;</item>
/// <item>when the lights go out round you, black, thinned by the light you carry;</item>
/// <item>after Memory Juice, everything warm for a while;</item>
/// <item>sound: near silence (the room tone), the snow's wind, and now and then, when you stop, footsteps that stop a
/// moment after yours.</item>
/// </list>
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere EndSnow = new(0.02f, 0.90f, 0.93f, 0.97f, 0f, scene: 1.1f);
    private static readonly Atmosphere EndHome = new(0.006f, 0.80f, 0.66f, 0.48f, 0f);
    private static readonly Atmosphere EndHouse = new(0.008f, 0.62f, 0.56f, 0.48f, 0f);

    /// <summary>The title key of a fake reality (level-1601 in the lang file).</summary>
    private const int EndFakeKey = 1601;

    private ILoadedSound endTone, endWind;
    private float endMoving, endStepCooldown;

    private void EndAir(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        EntityPlayer entity = capi.World.Player?.Entity;
        if (entity == null) return;
        int bx = (int)Math.Floor(pos.X), bz = (int)Math.Floor(pos.Z);
        Tile t = layout.TileAt(bx, bz);
        double now = capi.World.Calendar.TotalHours;

        if (t.Zone == 5)
        {
            titleKey = EndFakeKey;
            target = (WorldLayout.EndFake)t.Detail switch
            {
                WorldLayout.EndFake.Lobby => Levels[0],
                WorldLayout.EndFake.Office => Levels[4],
                WorldLayout.EndFake.Hotel => Levels[5],
                WorldLayout.EndFake.House => EndHouse,
                WorldLayout.EndFake.Snow => EndSnow,
                WorldLayout.EndFake.Home => EndHome,
                _ => target,
            };
        }

        // A distortion: for a few seconds the air is somewhere else's, and the floor shakes
        if (entity.WatchedAttributes.GetDouble(EndSystem.DistortUntilKey, -1) > now)
        {
            int scene = entity.WatchedAttributes.GetInt(EndSystem.SceneKey, -1);
            target = scene switch
            {
                0 => Levels[0],
                4 => Levels[4],
                9 => EndHouse,
                WorldLayout.Poolrooms => Levels[WorldLayout.Poolrooms],
                WorldLayout.Motion => new Atmosphere(0.0022f, 0.62f, 0.78f, 0.95f, 0f),
                _ => EndSnow,
            };
            if (rand.NextDouble() < dt * 4) capi.World.AddCameraShake(0.12f);
        }

        // The lights out round you: black, thinned by whatever light you carry
        if (entity.WatchedAttributes.GetDouble(EndSystem.LightsOutKey, -1) > now)
        {
            byte[] hsv = entity.LightHsv;
            float held = GameMath.Clamp(((hsv?[2] ?? 0) - DimmestLight) / (BrightestLight - DimmestLight), 0f, 1f);
            target = new Atmosphere(GameMath.Lerp(0.28f, 0.05f, held), 0.01f, 0.01f, 0.012f, 0f);
        }
        else if (entity.WatchedAttributes.GetDouble("backrooms:memoryUntil", -1) > now)
        {
            target = EndHome;
        }
    }

    private void EndSounds(float dt, EntityPos pos, bool here)
    {
        // The silence: a room tone that is almost nothing
        if (here && endTone == null)
        {
            endTone = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/end/roomtone"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = 0.25f, SoundType = EnumSoundType.Ambient,
            });
            endTone?.Start();
        }
        else if (!here && endTone != null)
        {
            endTone.Stop();
            endTone.Dispose();
            endTone = null;
        }

        // The wind over the snow of a Snowfield
        bool snow = false;
        if (here)
        {
            Tile t = layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));
            snow = t.Zone is 4 or 5 && t.Detail == (byte)WorldLayout.EndFake.Snow;
        }
        if (snow && endWind == null)
        {
            endWind = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/end/snowwind"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = 0.5f, SoundType = EnumSoundType.Ambient,
            });
            endWind?.Start();
        }
        else if (!snow && endWind != null)
        {
            endWind.Stop();
            endWind.Dispose();
            endWind = null;
        }
        if (!here) return;

        // Footsteps that carry on a moment after yours stop, now and then, somewhere close behind
        EntityPlayer entity = capi.World.Player?.Entity;
        if (entity == null) return;
        double speed = Math.Sqrt(entity.Pos.Motion.X * entity.Pos.Motion.X + entity.Pos.Motion.Z * entity.Pos.Motion.Z);
        endStepCooldown = Math.Max(0, endStepCooldown - dt);
        if (speed > 0.03) endMoving += dt;
        else
        {
            if (endMoving > 6 && endStepCooldown <= 0 && rand.NextDouble() < 1 / 6.0)
            {
                double yaw = pos.Yaw;
                double x = pos.X + Math.Sin(yaw) * 3.5, z = pos.Z + Math.Cos(yaw) * 3.5;
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/end/echostep"), x, pos.Y + 0.5, z, null, false, 12, 0.6f);
                endStepCooldown = 90;
            }
            endMoving = 0;
        }
    }
}
