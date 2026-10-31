using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Zone = Backrooms.Worldgen.WorldLayout.BasementZone;

namespace Backrooms;

/// <summary>
/// The Basement's air and sound on the client (experimental, kept as level 22). Its base fog (its entry in
/// <see cref="Levels"/>) is the Cellar's close blue-green dark; out in the Flood the fog is thicker still, and the Dry
/// Patch's a little thinner; near the dead it turns a sick brown. Arriving, it is pitch black for a moment, until the
/// lights come on all at once with a clunk (the Wikidot account: "pitch black when I got here first, but the lights
/// turned on and scared the hell out of me"). The Cellar has a low room tone (a boiler through the walls, far drips), and
/// now and then something behind a shut door: a baby crying, someone pacing, a knock. Open the door and it stops; there is
/// never anyone there (the Fandom page). The Flood has the soft wash of still water, a drip or a slosh now and then and,
/// rarely, a wail from somewhere far off in the dark. The title names the Basement on arriving, then the Flood, the Dry
/// Patch and the Cellar as the player comes to each. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere BasementFloodAir = new(0.07f, 0.040f, 0.075f, 0.072f, 0f);
    private static readonly Atmosphere BasementPatchAir = new(0.035f, 0.060f, 0.090f, 0.080f, 0f);
    /// <summary>Near the dead: the fog thicker and brown, as if the smell could be seen.</summary>
    private static readonly Atmosphere BasementFoulAir = new(0.06f, 0.085f, 0.075f, 0.040f, 0f);
    /// <summary>The first moments: pitch black, before the lights come on.</summary>
    private static readonly Atmosphere BasementBlackAir = new(0.9f, 0f, 0f, 0f, 0f, scene: 0.05f);

    /// <summary>Title keys for the Cellar (once the player has left it), the Flood and the Dry Patch.</summary>
    private const int BasementCellarKey = 2201, BasementFloodKey = 2202, BasementPatchKey = 2203;

    /// <summary>How long it is dark on arriving, in seconds.</summary>
    private const float BasementDarkSeconds = 2.4f;

    private ILoadedSound basementTone, basementWash, basementDoorSound;
    private bool basementLeftCellar, basementInside, basementFoul;
    private float basementNextDrip = 6, basementNextWail = 240, basementDark, basementNextDoor = 25, basementDoorLeft, basementNextSmell;
    private BlockPos basementDoorAt;

    private Zone BasementWhere(EntityPos pos) => layout.BasementZoneAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void BasementAir(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        // Arriving: dark until the lights come on
        if (!basementInside)
        {
            basementInside = true;
            basementDark = BasementDarkSeconds;
        }
        Zone zone = BasementWhere(pos);
        switch (zone)
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
        basementNextSmell -= dt;
        if (basementNextSmell <= 0)
        {
            basementNextSmell = 1f;
            basementFoul = BasementDeadNear((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)) >= 2;
        }
        if (basementFoul) target = BasementFoulAir;
        if (basementDark > 0)
        {
            basementDark -= dt;
            target = BasementBlackAir;
            if (basementDark <= 0)
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/basement/lightson"), pos.X, pos.Y + 2, pos.Z, null, false, 32, 0.8f);
        }
    }

    /// <summary>How many of the dead lie within four blocks (bodies and heaps of bones): two or more and the air is foul.</summary>
    private int BasementDeadNear(int x, int z)
    {
        int count = 0;
        for (int dz = -4; dz <= 4; dz++)
            for (int dx = -4; dx <= 4; dx++)
            {
                Tile t = layout.TileAt(x + dx, z + dz);
                if (t.Level == WorldLayout.Basement && t.Variant is Worldgen.Props.BasementBody or Worldgen.Props.BonePile or Worldgen.Props.Ribcage or Worldgen.Props.JawSkeleton) count++;
            }
        return count;
    }

    private void BasementSounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            BasementStop(ref basementTone);
            BasementStop(ref basementWash);
            BasementStop(ref basementDoorSound);
            basementLeftCellar = false;
            basementInside = false;
            return;
        }
        Zone zone = BasementWhere(pos);
        bool wet = zone == Zone.Flood;
        // The Cellar's room tone everywhere (quieter out in the water, and nothing while it is still dark), the wash of
        // the water in the Flood
        if (basementDark > 0)
        {
            BasementStop(ref basementTone);
            BasementStop(ref basementWash);
            return;
        }
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

        BasementBehindDoors(dt, pos, zone);
    }

    /// <summary>
    /// Sounds behind the doors (Fandom: "noises can be heard from behind closed doors, such as babies crying, footsteps…
    /// these noises are known to disappear once the door is opened"): every half minute or so in the Cellar, behind a
    /// shut door three to twelve blocks off, on its far side from the player. It stops the moment the door opens, or
    /// when the player comes right up to it.
    /// </summary>
    private void BasementBehindDoors(float dt, EntityPos pos, Zone zone)
    {
        IBlockAccessor blocks = capi.World.BlockAccessor;
        if (basementDoorSound != null)
        {
            basementDoorLeft -= dt;
            Block door = blocks.GetBlock(basementDoorAt);
            bool shut = door?.Code?.Path is { } path && path.StartsWith("basement-door-") && !path.StartsWith("basement-door-open");
            double near = pos.SquareDistanceTo(basementDoorAt.X + 0.5, pos.Y, basementDoorAt.Z + 0.5);
            if (!shut || near < 1.6 * 1.6 || basementDoorLeft <= 0 || !basementDoorSound.IsPlaying && basementDoorLeft < 6)
            {
                BasementStop(ref basementDoorSound);
                basementNextDoor = 25 + (float)rand.NextDouble() * 35;
            }
            return;
        }
        if (zone != Zone.Cellar) return;
        basementNextDoor -= dt;
        if (basementNextDoor > 0) return;
        basementNextDoor = 8 + (float)rand.NextDouble() * 10; // (tried again soon if no door is near)
        int x0 = (int)Math.Floor(pos.X), z0 = (int)Math.Floor(pos.Z), y = geometry.FloorFor(WorldLayout.Basement) + 1;
        BlockPos best = null;
        int seen = 0;
        var at = new BlockPos(0, y, 0);
        for (int dz = -12; dz <= 12; dz++)
            for (int dx = -12; dx <= 12; dx++)
            {
                int d2 = dx * dx + dz * dz;
                if (d2 < 9 || d2 > 144) continue;
                at.Set(x0 + dx, y, z0 + dz);
                string path = blocks.GetBlock(at)?.Code?.Path;
                if (path == null || !path.StartsWith("basement-door-") || path.StartsWith("basement-door-open") || !path.Contains("-lower-")) continue;
                // (One of them, at random)
                if (rand.Next(++seen) == 0) best = at.Copy();
            }
        if (best == null) return;
        // The far side of the door from the player: the door's facing gives the line through it
        string side = blocks.GetBlock(best).Variant?["side"] ?? "north";
        bool alongZ = side is "north" or "south";
        double sx = best.X + 0.5, sz = best.Z + 0.5;
        if (alongZ) sz += pos.Z < sz ? 2.5 : -2.5;
        else sx += pos.X < sx ? 2.5 : -2.5;
        double roll = rand.NextDouble();
        (string Sound, bool Loop, float Seconds, float Volume, float Pitch) what = roll < 0.4
            ? ("backrooms:sounds/ambient/basement/cry", false, 10f, 0.55f, 0.95f + (float)rand.NextDouble() * 0.1f)
            : roll < 0.8 ? ("backrooms:sounds/entity/footsteps", true, 6f + (float)rand.NextDouble() * 4f, 0.45f, 0.85f)
            : ("backrooms:sounds/entity/knock", false, 4f, 0.5f, 0.9f);
        basementDoorSound = capi.World.LoadSound(new SoundParams
        {
            Location = new AssetLocation(what.Sound), ShouldLoop = what.Loop, RelativePosition = false, DisposeOnFinish = false,
            Position = new Vec3f((float)sx, y + 1f, (float)sz), Range = 24, Volume = what.Volume, Pitch = what.Pitch,
            SoundType = EnumSoundType.Ambient,
        });
        if (basementDoorSound == null) return;
        basementDoorSound.Start();
        basementDoorAt = best;
        basementDoorLeft = what.Seconds;
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
