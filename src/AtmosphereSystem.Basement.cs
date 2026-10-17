using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Zone = Backrooms.Worldgen.WorldLayout.BasementZone;

namespace Backrooms;

/// <summary>
/// The Basement's air and sound on the client (experimental, kept as level 22). Its base fog (its entry in
/// <see cref="Levels"/>) is the Cellar's close blue-green dark; out in the Flood the fog is thicker still, and the Dry
/// Patch's a little thinner. The Cellar has a low room tone (a boiler through the walls, far drips); the Flood the soft
/// wash of still water, with a drip or a slosh now and then and, rarely, a wail from somewhere far off in the dark. The
/// title names the Basement on arriving, then the Flood, the Dry Patch and the Cellar as the player comes to each. This
/// file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere BasementFloodAir = new(0.07f, 0.040f, 0.075f, 0.072f, 0f);
    private static readonly Atmosphere BasementPatchAir = new(0.035f, 0.060f, 0.090f, 0.080f, 0f);

    /// <summary>Title keys for the Cellar (once the player has left it), the Flood and the Dry Patch.</summary>
    private const int BasementCellarKey = 2201, BasementFloodKey = 2202, BasementPatchKey = 2203;

    private ILoadedSound basementTone, basementWash;
    private bool basementLeftCellar;
    private float basementNextDrip = 6, basementNextWail = 240;

    private Zone BasementWhere(EntityPos pos) => layout.BasementZoneAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void BasementAir(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        switch (BasementWhere(pos))
        {
            case Zone.Flood:
                target = BasementFloodAir;
                titleKey = BasementFloodKey;
                basementLeftCellar = true;
                break;
            case Zone.Patch:
                target = BasementPatchAir;
                titleKey = BasementPatchKey;
                basementLeftCellar = true;
                break;
            default:
                // On arriving, the level's own title; coming back up out of the water, the Cellar's
                if (basementLeftCellar) titleKey = BasementCellarKey;
                break;
        }
    }

    private void BasementSounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            BasementStop(ref basementTone);
            BasementStop(ref basementWash);
            basementLeftCellar = false;
            return;
        }
        Zone zone = BasementWhere(pos);
        bool wet = zone == Zone.Flood;
        // The Cellar's room tone everywhere (quieter out in the water), the wash of the water in the Flood
        BasementLoop(ref basementTone, "backrooms:sounds/ambient/basement/cellar", wet ? 0.18f : 0.4f);
        if (wet) BasementLoop(ref basementWash, "backrooms:sounds/ambient/poolroom", 0.35f);
        else BasementStop(ref basementWash);

        basementNextDrip -= dt;
        if (basementNextDrip <= 0)
        {
            basementNextDrip = (wet ? 4 : 8) + (float)rand.NextDouble() * (wet ? 9 : 14);
            double yaw = rand.NextDouble() * Math.PI * 2, dist = 4 + rand.NextDouble() * 12;
            string what = wet && rand.NextDouble() < 0.5 ? "poollap" : "pooldrip";
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/" + what), pos.X + Math.Sin(yaw) * dist, pos.Y + 0.5,
                pos.Z + Math.Cos(yaw) * dist, null, 0.7f + (float)rand.NextDouble() * 0.25f, 32, wet ? 0.4f : 0.3f);
        }

        // Now and then, out in the water, a wail from far off: a groan slowed until it is no voice anyone has
        basementNextWail -= dt;
        if (basementNextWail <= 0)
        {
            basementNextWail = 180 + (float)rand.NextDouble() * 300;
            if (wet)
            {
                double yaw = rand.NextDouble() * Math.PI * 2;
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/entity/groan"), pos.X + Math.Sin(yaw) * 20, pos.Y + 1,
                    pos.Z + Math.Cos(yaw) * 20, null, 0.55f, 48, 0.35f);
            }
        }
    }

    private void BasementLoop(ref ILoadedSound sound, string location, float volume)
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

    private static void BasementStop(ref ILoadedSound sound)
    {
        sound?.Stop();
        sound?.Dispose();
        sound = null;
    }
}
