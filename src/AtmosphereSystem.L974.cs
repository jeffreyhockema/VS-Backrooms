using System;
using Backrooms.Regions;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;

namespace Backrooms;

/// <summary>
/// Level 974's air and sound on the client (kept as level 18). Its base fog is its entry in <see cref="Levels"/>: clear,
/// faintly pink. Stay past the calm (<see cref="L974System.CalmHours"/>) and the pink presses in: the fog thickens and
/// deepens, and the music box's lullaby slows and goes out of tune. This file is the level's own; see
/// docs/design/new-levels/CONTRACT.md.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L974Close = new(0.005f, 0.98f, 0.70f, 0.80f, 0f);
    private ILoadedSound l974Lullaby, l974Fridge;
    private bool l974Warped;
    private float l974NextCreak = 20;

    /// <summary>How many in-game hours the player has been in the house (0 if not on a visit).</summary>
    private double L974Hours()
    {
        var entity = capi.World.Player?.Entity;
        if (entity == null || entity.WatchedAttributes.GetInt(L974System.VisitKey) == 0) return 0;
        return capi.World.Calendar.TotalHours - entity.WatchedAttributes.GetDouble(L974System.ArrivedKey, capi.World.Calendar.TotalHours);
    }

    private void L974Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        double hours = L974Hours();
        if (hours >= L974System.CalmHours) target = L974Close;
    }

    private void L974Sounds(float dt, EntityPos pos, bool here)
    {
        bool warped = here && L974Hours() >= L974System.WarpHours;
        if (!here || warped != l974Warped)
        {
            l974Lullaby?.Stop();
            l974Lullaby?.Dispose();
            l974Lullaby = null;
        }
        if (!here)
        {
            l974Fridge?.Stop();
            l974Fridge?.Dispose();
            l974Fridge = null;
            return;
        }
        l974Warped = warped;
        if (l974Lullaby == null)
        {
            // The music box in the bedroom: heard all through the house, faintly
            l974Lullaby = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation(warped ? "backrooms:sounds/ambient/974/lullaby-warped" : "backrooms:sounds/ambient/974/lullaby"),
                ShouldLoop = true, RelativePosition = true, DisposeOnFinish = false, Volume = 0.22f, SoundType = EnumSoundType.Ambient,
            });
            l974Lullaby?.Start();
        }

        // The fridge's hum, near the kitchen
        int mx = WorldLayout.MacroOf((int)Math.Floor(pos.X)), mz = WorldLayout.MacroOf((int)Math.Floor(pos.Z));
        var (fx, fz) = layout.L974At(mx, mz, 1, 10);
        double d = Math.Sqrt((pos.X - fx - 0.5) * (pos.X - fx - 0.5) + (pos.Z - fz - 0.5) * (pos.Z - fz - 0.5));
        float volume = (float)Math.Clamp(1 - d / 7, 0, 1) * 0.35f;
        if (volume > 0.01f && l974Fridge == null)
        {
            l974Fridge = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/974/fridge"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = volume, SoundType = EnumSoundType.Ambient,
            });
            l974Fridge?.Start();
        }
        else if (volume <= 0.01f && l974Fridge != null)
        {
            l974Fridge.Stop();
            l974Fridge.Dispose();
            l974Fridge = null;
        }
        else l974Fridge?.SetVolume(volume);

        // Now and then, the house settles
        l974NextCreak -= dt;
        if (l974NextCreak <= 0)
        {
            l974NextCreak = 25 + (float)rand.NextDouble() * 50;
            double yaw = rand.NextDouble() * Math.PI * 2, dist = 3 + rand.NextDouble() * 6;
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/974/creak*"), pos.X + Math.Sin(yaw) * dist, pos.Y + 2, pos.Z + Math.Cos(yaw) * dist,
                null, true, 16, 0.3f);
        }
    }
}
