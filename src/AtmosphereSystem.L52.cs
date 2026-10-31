using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Zone = Backrooms.Worldgen.WorldLayout.L52Zone;
using CampusKind = Backrooms.Worldgen.WorldLayout.L52CampusKind;

namespace Backrooms;

/// <summary>
/// Level 52, "The Greenfield Campus"'s air and sound on the client (experimental, kept as level 23). Its base air (its entry
/// in <see cref="Levels"/>) is a thin, clear blue haze over the hills, with a few white clouds; the level keeps no day and
/// night (the ambient is held at noon, as every level without one), and the outside sky is hidden in a sphere of fog of a
/// fixed sky blue (as Level 10's is, <see cref="L10Sky"/>), so the sky is "constantly blue" at every hour; the sun that
/// hangs over it is drawn by Regions.L52Sun. Indoors the air is warmer and closer, a little dimmer in the classrooms (their
/// lights are off). At Terra's night the sun dims a little ("its intensity drifts").
///
/// The sound bed: the wind over the hills, soft and gusting, stronger when the temperature turns sharply (the lore's "soft
/// gales"), muffled indoors; the corridors' lights hum (their own ambient); a classroom's room tone; now and then a school
/// bell far off down the corridors (an invention of the prototype's, kept); on J. Barry Campus, now and then an alarm that
/// goes off for nothing ("strict alarms, many false ones"). Titles: the three named campuses, the gym, the canteen, the
/// courtyard. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L52Indoors = new(0.0035f, 0.80f, 0.78f, 0.72f, 0f);
    private static readonly Atmosphere L52Classroom = new(0.0055f, 0.62f, 0.60f, 0.56f, 0f, scene: 0.92f);
    /// <summary>The sky blue the sky sphere is drawn in (the outside sky never shows).</summary>
    private static readonly float[] L52SkyBlue = { 0.40f, 0.62f, 0.94f };

    /// <summary>Title keys (level-23xx in the lang file).</summary>
    private const int L52MarshallKey = 2301, L52BarryKey = 2302, L52TurnerKey = 2303, L52GymKey = 2304, L52CanteenKey = 2305, L52CourtyardKey = 2306;

    private ILoadedSound l52Room, l52Wind;
    private float l52NextBell = 90, l52NextAlarm = 120, l52Sky;
    private bool l52SphereSet;

    /// <summary>Where the player is: the campus (if any) and the tile there, and whether they are inside one of its buildings.</summary>
    private (WorldLayout.L52Campus Campus, Tile Tile, bool Indoors) L52Where(EntityPos pos)
    {
        int x = (int)Math.Floor(pos.X), z = (int)Math.Floor(pos.Z);
        WorldLayout.L52Campus c = layout.L52CampusAt(x, z, out int i);
        if (c == null) return (null, layout.TileAt(x, z), false);
        Tile t = c.Grid[i];
        double rel = pos.Y - geometry.FloorFor(WorldLayout.Level52);
        bool indoors = t.Depth > 0 && t.Zone != (byte)Zone.Ext && rel < t.Depth * WorldLayout.L52Storey + 0.5;
        return (c, t, indoors);
    }

    private void L52Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        var (c, t, indoors) = L52Where(pos);
        if (indoors) target = t.Zone == (byte)Zone.Room ? L52Classroom : L52Indoors;
        // The sun dims a little while it is night on Terra
        double hour = capi.World.Calendar.HourOfDay;
        float night = (float)GameMath.Clamp(Math.Cos((hour - 0.5) / 24 * Math.PI * 2) * 1.5 - 0.3, 0, 1);
        if (night > 0) target = new Atmosphere(target.Density, target.R, target.G, target.B, target.GroundFog, target.Scene * (1 - 0.12f * night),
            target.SceneWeight, target.Clouds, target.DayNight, target.CloudBrightness, target.FogMin);
        if (c == null) return;
        // The named campuses by name; in an ordinary one, its gym, its canteen, its courtyard
        titleKey = c.Head.Kind switch
        {
            CampusKind.MarshallDavid => L52MarshallKey, CampusKind.JBarry => L52BarryKey, CampusKind.JTurner => L52TurnerKey, _ => titleKey,
        };
        if (c.Head.Kind != CampusKind.Ordinary) return;
        int room = c.RoomOf[(int)Math.Floor(pos.X) - c.Head.X0 + ((int)Math.Floor(pos.Z) - c.Head.Z0) * c.W];
        if (indoors && t.Zone == (byte)Zone.Hall && room >= 0)
            titleKey = c.Rooms[room].Kind switch { WorldLayout.L52RoomKind.Gym => L52GymKey, WorldLayout.L52RoomKind.Canteen => L52CanteenKey, _ => titleKey };
        else if (t.Zone is (byte)Zone.Turf or (byte)Zone.Court) titleKey = L52CourtyardKey;
    }

    private void L52Sounds(float dt, EntityPos pos, bool here)
    {
        L52SkySphere(dt, here);
        if (!here)
        {
            L188Stop(ref l52Room);
            L188Stop(ref l52Wind);
            return;
        }
        var (c, t, indoors) = L52Where(pos);
        WorldLayout.L52Hours = capi.World.Calendar.TotalHours;

        // The wind: gusting over minutes, harder where the temperature is turning fast; muffled indoors
        double hours = capi.World.Calendar.TotalHours;
        float turning = Math.Abs(WorldLayout.L52OutdoorTemperature(hours + 0.25) - WorldLayout.L52OutdoorTemperature(hours - 0.25));
        float gust = (float)(0.5 + 0.5 * Math.Sin(hours * 9.1) * Math.Sin(hours * 3.7 + 1.3));
        float wind = GameMath.Clamp(0.06f + 0.22f * gust + 0.08f * turning, 0f, 0.6f);
        L73Loop(ref l52Wind, "game:sounds/environment/wind", indoors ? wind * 0.2f : wind);

        // A classroom's room tone
        L73Loop(ref l52Room, "backrooms:sounds/ambient/end/roomtone", indoors && t.Zone == (byte)Zone.Room ? 0.16f : 0f);

        // A bell, far off down the corridors, now and then
        l52NextBell -= dt;
        if (l52NextBell <= 0)
        {
            l52NextBell = 240 + (float)rand.NextDouble() * 300;
            if (indoors)
            {
                double yaw = rand.NextDouble() * Math.PI * 2;
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/52/bell"), pos.X + Math.Sin(yaw) * 40, pos.Y + 2, pos.Z + Math.Cos(yaw) * 40,
                    null, false, 96, 0.45f);
            }
        }
        // J. Barry's false alarms
        l52NextAlarm -= dt;
        if (l52NextAlarm <= 0)
        {
            l52NextAlarm = 360 + (float)rand.NextDouble() * 480;
            if (c?.Head.Kind == CampusKind.JBarry)
            {
                double yaw = rand.NextDouble() * Math.PI * 2;
                capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/run/alarm-far"), pos.X + Math.Sin(yaw) * 30, pos.Y + 2, pos.Z + Math.Cos(yaw) * 30,
                    null, false, 80, 0.4f);
            }
        }
    }

    /// <summary>
    /// The sphere of fog round the player that hides the outside sky (its sun, moon and stars, its dusk and its night) while in
    /// the level, in a fixed sky blue, eased in and out; Level 10's own sphere is left alone.
    /// </summary>
    private void L52SkySphere(float dt, bool here)
    {
        l52Sky += ((here ? 1f : 0f) - l52Sky) * Math.Min(1f, dt * 2f);
        DefaultShaderUniforms uniforms = capi.Render.ShaderUniforms;
        if (l52Sky < 0.01f)
        {
            if (l52SphereSet) uniforms.FogSphereQuantity = 0;
            l52SphereSet = false;
            return;
        }
        float[] sphere = uniforms.FogSpheres;
        sphere[0] = sphere[1] = sphere[2] = 0;
        sphere[3] = SkySphereRadius;
        sphere[4] = SkySphereDensity * 1.8f * l52Sky;
        sphere[5] = L52SkyBlue[0];
        sphere[6] = L52SkyBlue[1];
        sphere[7] = L52SkyBlue[2];
        uniforms.FogSphereQuantity = 1;
        l52SphereSet = true;
    }
}
