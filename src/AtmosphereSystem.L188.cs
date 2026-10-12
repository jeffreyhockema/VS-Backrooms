using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Part = Backrooms.Worldgen.WorldLayout.L188Part;

namespace Backrooms;

/// <summary>
/// Level 188, "The Courtyard of Windows"'s air and sound on the client (kept as level 20). Its base fog (its entry in
/// <see cref="Levels"/>) is the hotel's faint grey; the courtyard is a blue-black night under its black sky, the roof
/// darker still. No hum anywhere: the hotel's lights are silent. The courtyard has its near-silence, the downpipe running
/// into its drain, now and then three soft knocks on glass somewhere, whispers from a window with someone in it, a party
/// muffled behind the confetti window; the corridors have the hotel's room tone. This file is the level's own; see
/// docs/design/new-levels/CONTRACT.md.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L188Courtyard = new(0.014f, 0.05f, 0.06f, 0.09f, -0.15f);
    private static readonly Atmosphere L188RoofAir = new(0.020f, 0.03f, 0.03f, 0.05f, 0f);
    private ILoadedSound l188Loop, l188Pipe, l188Party;
    private bool l188LoopCourt;
    private float l188NextKnock = 25, l188NextConfetti;

    /// <summary>Where the player is in the building: the courtyard (or out over it), the roof, or inside.</summary>
    private (bool Court, bool Roof) L188Where(EntityPos pos)
    {
        var c = layout.L188CellAtWorld((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));
        double rel = pos.Y - geometry.FloorFor(WorldLayout.Level188);
        bool court = c.Part is Part.Court or Part.Void;
        bool roof = !court && rel >= WorldLayout.L188RoofRel + 0.5;
        return (court, roof);
    }

    private void L188Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        var (court, roof) = L188Where(pos);
        if (roof)
        {
            target = L188RoofAir;
            titleKey = 2002;
        }
        else if (court) target = L188Courtyard; // the level's own title: the Courtyard of Windows
        else titleKey = 2001; // the hotel
    }

    private void L188Sounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            L188Stop(ref l188Loop);
            L188Stop(ref l188Pipe);
            L188Stop(ref l188Party);
            return;
        }
        var (court, roof) = L188Where(pos);
        bool outside = court || roof;
        if (l188Loop == null || outside != l188LoopCourt)
        {
            L188Stop(ref l188Loop);
            l188LoopCourt = outside;
            l188Loop = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation(outside ? "backrooms:sounds/ambient/188/courtyard" : "backrooms:sounds/ambient/188/corridor"),
                ShouldLoop = true, RelativePosition = true, DisposeOnFinish = false, Volume = outside ? 0.35f : 0.3f, SoundType = EnumSoundType.Ambient,
            });
            l188Loop?.Start();
        }

        // The downpipe on the north façade, running into its drain
        double floor = geometry.FloorFor(WorldLayout.Level188);
        L188Positional(ref l188Pipe, "backrooms:sounds/ambient/188/pipe", pos,
            layout.L188BuildX0 + WorldLayout.L188PipeBx + 0.5, floor + 1.5, layout.L188BuildZ0 + WorldLayout.L188PipeBz + 0.5, 16, 0.45f);

        // The party behind the confetti window, and its confetti drifting down the glass on the courtyard side
        int funWindow = -1;
        for (int wi = 0; wi < WorldLayout.L188Windows && funWindow < 0; wi++) if (layout.L188LinkLevel(wi) == WorldLayout.FunLevel) funWindow = wi;
        if (funWindow >= 0)
        {
            var (l, r, facing) = WorldLayout.L188WindowTiles(funWindow);
            var (fx, fz) = WorldLayout.L188Step(facing);
            double cx = layout.L188BuildX0 + (l.Bx + r.Bx) / 2.0 + 0.5 + fx * 0.6, cz = layout.L188BuildZ0 + (l.Bz + r.Bz) / 2.0 + 0.5 + fz * 0.6;
            L188Positional(ref l188Party, "backrooms:sounds/effect/188/partymuffled", pos, cx, floor + 3, cz, 12, 0.5f);
            l188NextConfetti -= dt;
            if (l188NextConfetti <= 0 && (pos.X - cx) * (pos.X - cx) + (pos.Z - cz) * (pos.Z - cz) < 24 * 24)
            {
                l188NextConfetti = 0.25f;
                int colour = ColorUtil.ToRgba(255, 120 + rand.Next(135), 80 + rand.Next(175), 80 + rand.Next(175));
                var confetti = new SimpleParticleProperties(2, 4, colour, new Vec3d(cx - 0.9, floor + 4, cz - 0.9), new Vec3d(cx + 0.9, floor + 4.2, cz + 0.9),
                    new Vec3f(-0.05f, -0.4f, -0.05f), new Vec3f(0.05f, -0.2f, 0.05f), 3f, 0.05f, 0.15f, 0.25f, EnumParticleModel.Quad);
                capi.World.SpawnParticles(confetti);
            }
        }

        // Three soft knocks on glass, somewhere round the courtyard
        l188NextKnock -= dt;
        if (l188NextKnock <= 0)
        {
            l188NextKnock = 30 + (float)rand.NextDouble() * 60;
            int wi = rand.Next(WorldLayout.L188Windows), s = rand.Next(WorldLayout.L188Storeys);
            var (l, _, _) = WorldLayout.L188WindowTiles(wi);
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/188/knock"), layout.L188BuildX0 + l.Bx + 0.5, floor + 4 * s + 3,
                layout.L188BuildZ0 + l.Bz + 0.5, null, true, 40, court ? 0.6f : 0.3f);
        }
        // (The whispers from a window with someone in it are the server's: Regions.L188System plays them for everyone near)
    }

    /// <summary>A looping sound at a place, louder the nearer, started and stopped as the player comes and goes.</summary>
    private void L188Positional(ref ILoadedSound sound, string location, EntityPos pos, double x, double y, double z, double reach, float loudest)
    {
        double d = Math.Sqrt((pos.X - x) * (pos.X - x) + (pos.Y - y) * (pos.Y - y) + (pos.Z - z) * (pos.Z - z));
        float volume = (float)Math.Clamp(1 - d / reach, 0, 1) * loudest;
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

    private static void L188Stop(ref ILoadedSound sound)
    {
        sound?.Stop();
        sound?.Dispose();
        sound = null;
    }
}
