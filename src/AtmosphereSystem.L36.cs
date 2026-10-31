using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Zone = Backrooms.Worldgen.WorldLayout.L36Zone;

namespace Backrooms;

/// <summary>
/// Level 36, "Airport"'s air and sound on the client (experimental, kept as level 25). Its base fog is its entry in
/// <see cref="Levels"/>: thin, cool, clean air, so a concourse fades into pale grey far off. A blackout is close and
/// blue-black, the back of house dim and dusty, the lounge warm, the cabin bright; at the Absolute Limit the air itself
/// goes to static grey. Each part of the terminal has its title (level-2501 to level-2514).
///
/// Sound: the terminal's bed everywhere it is lit (air handlers, a fluorescent buzz, a crowd that is not there), the
/// carousels' clatter from their own blocks; every minute or two the PA's chime and an announcement nobody can make out;
/// by the runway windows, now and then a jet taking off or landing that never comes into view. The ducts' drone out of
/// bounds, the cabin's roar aboard, static at the Limit, silence in a blackout.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L36Blackout = new(0.03f, 0.03f, 0.035f, 0.045f, 0f);
    private static readonly Atmosphere L36ServiceAir = new(0.014f, 0.10f, 0.10f, 0.11f, 0f);
    private static readonly Atmosphere L36Limit = new(0.022f, 0.62f, 0.62f, 0.64f, 0f);
    private static readonly Atmosphere L36Cabin = new(0.003f, 0.86f, 0.87f, 0.90f, 0f);
    private static readonly Atmosphere L36Warm = new(0.0045f, 0.82f, 0.74f, 0.64f, 0f);

    /// <summary>The titles (level-25xx in the lang file).</summary>
    private const int L36Baggage = 2501, L36CheckIn = 2502, L36Security = 2503, L36Concourse = 2504, L36Gates = 2505, L36DutyFree = 2506,
        L36FoodCourt = 2507, L36Lounge = 2508, L36Meeting = 2509, L36OutOfBounds = 2510, L36AbsoluteLimit = 2511, L36Flight = 2512,
        L36BlackoutKey = 2513, L36LostFound = 2514;

    private ILoadedSound l36Bed;
    private string l36BedPlaying;
    private float l36PaClock = 40, l36JetClock = 60;

    private void L36Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        Tile t = layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));
        if ((t.Detail & WorldLayout.L36LimitBit) != 0 && (t.Detail & WorldLayout.L36StaticBit) != 0 || t.Kind == TileKind.Floor && t.Zone == 0)
        {
            target = L36Limit;
            titleKey = L36AbsoluteLimit;
            return;
        }
        if (WorldLayout.L36IsDark(t))
        {
            target = t.Zone is (byte)Zone.Service or (byte)Zone.Vent ? L36ServiceAir : L36Blackout;
            titleKey = t.Zone is (byte)Zone.Service or (byte)Zone.Vent ? L36OutOfBounds : L36BlackoutKey;
            return;
        }
        switch ((Zone)t.Zone)
        {
            case Zone.Baggage: titleKey = L36Baggage; break;
            case Zone.LostFound: titleKey = L36LostFound; break;
            case Zone.CheckIn: case Zone.Booth: titleKey = L36CheckIn; break;
            case Zone.Security: titleKey = L36Security; break;
            case Zone.Concourse: case Zone.Junction: titleKey = L36Concourse; break;
            case Zone.Pier: case Zone.Holdroom: titleKey = L36Gates; break;
            case Zone.Street: case Zone.Shop: titleKey = L36DutyFree; break;
            case Zone.FoodCourt: target = L36Warm; titleKey = L36FoodCourt; break;
            case Zone.Lounge: target = L36Warm; titleKey = L36Lounge; break;
            case Zone.Meeting: titleKey = L36Meeting; break;
            case Zone.Service: case Zone.Vent: target = L36ServiceAir; titleKey = L36OutOfBounds; break;
            case Zone.Cabin: case Zone.Bridge: target = L36Cabin; titleKey = L36Flight; break;
        }
    }

    private void L36Sounds(float dt, EntityPos pos, bool here)
    {
        Tile t = here ? layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z)) : default;
        bool limit = here && ((t.Detail & WorldLayout.L36LimitBit) != 0 && (t.Detail & WorldLayout.L36StaticBit) != 0 || t.Kind == TileKind.Floor && t.Zone == 0);
        bool dark = here && WorldLayout.L36IsDark(t);
        string bed = !here ? null
            : limit ? "static"
            : t.Zone is (byte)Zone.Cabin or (byte)Zone.Bridge ? "cabin"
            : t.Zone is (byte)Zone.Service or (byte)Zone.Vent ? "service"
            : dark ? null
            : "hum";
        if (bed != l36BedPlaying)
        {
            if (l36Bed != null)
            {
                l36Bed.Stop();
                l36Bed.Dispose();
                l36Bed = null;
            }
            if (bed != null)
            {
                l36Bed = capi.World.LoadSound(new SoundParams
                {
                    Location = new AssetLocation("backrooms:sounds/ambient/36/" + bed), ShouldLoop = true, RelativePosition = true, DisposeOnFinish = false,
                    Volume = bed switch { "hum" => 0.3f, "static" => 0.45f, "cabin" => 0.5f, _ => 0.4f }, SoundType = EnumSoundType.Ambient,
                });
                l36Bed?.Start();
            }
            l36BedPlaying = bed;
        }
        if (bed != "hum") return;
        // The PA: a chime and a calm voice nobody can make out, from somewhere up in the ceiling
        l36PaClock -= dt;
        if (l36PaClock <= 0)
        {
            l36PaClock = 70 + (float)rand.NextDouble() * 80;
            double angle = rand.NextDouble() * Math.PI * 2, r = 10 + rand.NextDouble() * 12;
            double x = pos.X + Math.Cos(angle) * r, y = pos.Y + 6, z = pos.Z + Math.Sin(angle) * r;
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/36/chime" + (1 + rand.Next(2))), x, y, z, null, true, 60, 0.5f);
            string pa = "backrooms:sounds/effect/36/pa" + (1 + rand.Next(3));
            capi.Event.RegisterCallback(_ => capi.World.PlaySoundAt(new AssetLocation(pa), x, y, z, null, true, 60, 0.55f), 2600);
        }
        // Out past the windows: a jet that never comes into view
        if (t.Zone is not ((byte)Zone.Holdroom or (byte)Zone.Pier)) return;
        l36JetClock -= dt;
        if (l36JetClock > 0) return;
        l36JetClock = 90 + (float)rand.NextDouble() * 120;
        double ja = rand.NextDouble() * Math.PI * 2;
        capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/effect/36/jet" + (1 + rand.Next(2))), pos.X + Math.Cos(ja) * 24, pos.Y + 3, pos.Z + Math.Sin(ja) * 24, null, true, 80, 0.6f);
    }
}
