using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Zone = Backrooms.Worldgen.WorldLayout.L120Zone;

namespace Backrooms;

/// <summary>
/// Level 120, "Server Room"'s air and sound on the client (experimental, kept as level 26). Its base fog (its entry in
/// <see cref="Levels"/>) is a near-black blue-green; a hot aisle has a warm haze of its own, a cold vault a pale cold air,
/// a great hall a thinner dark so the rows recede. Everywhere the fans: one drone (brown noise, the mains hum, a faint
/// whine), quiet in the corridors, louder among the racks, loudest in a great hall. Titles for the aisles, the control
/// rooms, the vaults and the great halls. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L120HotAir = new(0.018f, 0.11f, 0.065f, 0.035f, 0f);
    private static readonly Atmosphere L120VaultAir = new(0.008f, 0.32f, 0.38f, 0.40f, 0f);
    private static readonly Atmosphere L120GreatAir = new(0.0075f, 0.025f, 0.055f, 0.065f, 0f);
    private ILoadedSound l120Hum;
    private float l120Volume;

    private Tile L120TileAt(EntityPos pos) => layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void L120Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        Tile t = L120TileAt(pos);
        bool great = t.Height >= 6;
        switch (t.Zone)
        {
            case (byte)Zone.Cold:
                if (great) { target = L120GreatAir; titleKey = 2605; }
                else titleKey = 2601;
                break;
            case (byte)Zone.Hot:
                target = L120HotAir;
                titleKey = great ? 2605 : 2602;
                break;
            case (byte)Zone.Control: titleKey = 2603; break;
            case (byte)Zone.Vault: target = L120VaultAir; titleKey = 2604; break;
        }
    }

    private void L120Sounds(float dt, EntityPos pos, bool here)
    {
        if (!here)
        {
            if (l120Hum == null) return;
            l120Hum.Stop();
            l120Hum.Dispose();
            l120Hum = null;
            return;
        }
        Tile t = L120TileAt(pos);
        float want = t.Height >= 6 ? 0.55f : t.Zone switch
        {
            (byte)Zone.Cold or (byte)Zone.Hot => 0.42f,
            (byte)Zone.Store => 0.3f,
            (byte)Zone.Control => 0.3f,
            (byte)Zone.Vault => 0.2f,
            _ => 0.22f,
        };
        if (l120Hum == null)
        {
            l120Volume = want;
            l120Hum = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/120/serverhum"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = want, SoundType = EnumSoundType.Ambient,
            });
            l120Hum?.Start();
            return;
        }
        // Ease towards the zone's loudness over a second or two
        float next = l120Volume + Math.Clamp(want - l120Volume, -dt * 0.25f, dt * 0.25f);
        if (Math.Abs(next - l120Volume) > 0.002f)
        {
            l120Volume = next;
            l120Hum.SetVolume(l120Volume);
        }
    }
}
