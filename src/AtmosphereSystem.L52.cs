using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Zone = Backrooms.Worldgen.WorldLayout.L52Zone;

namespace Backrooms;

/// <summary>
/// Level 52, "School Halls"'s air and sound on the client (experimental, kept as level 23). Its base fog (its entry in
/// <see cref="Levels"/>) is a light grey-beige haze down the halls; the dark classrooms have a closer, darker air of their
/// own, the gym and the canteen their titles. The halls' buzz is the panels' own (fluorescentlight's ambient hum); a
/// classroom has a faint room tone, and now and then a school bell rings somewhere far off. This file is the level's own.
/// </summary>
public partial class AtmosphereSystem
{
    private static readonly Atmosphere L52Classroom = new(0.010f, 0.30f, 0.29f, 0.27f, 0f);
    private static readonly Atmosphere L52Gym = new(0.004f, 0.74f, 0.72f, 0.66f, 0f);
    private ILoadedSound l52Room;
    private float l52NextBell = 40;

    private Tile L52TileAt(EntityPos pos) => layout.TileAt((int)Math.Floor(pos.X), (int)Math.Floor(pos.Z));

    private void L52Air(float dt, EntityPos pos, ref Atmosphere target, ref int titleKey)
    {
        switch (L52TileAt(pos).Zone)
        {
            case (byte)Zone.Classroom or (byte)Zone.Store: target = L52Classroom; break;
            case (byte)Zone.Gym: target = L52Gym; titleKey = 2301; break;
            case (byte)Zone.Canteen: titleKey = 2302; break;
        }
    }

    private void L52Sounds(float dt, EntityPos pos, bool here)
    {
        bool room = here && L52TileAt(pos).Zone is (byte)Zone.Classroom or (byte)Zone.Store;
        if (room && l52Room == null)
        {
            l52Room = capi.World.LoadSound(new SoundParams
            {
                Location = new AssetLocation("backrooms:sounds/ambient/end/roomtone"), ShouldLoop = true, RelativePosition = true,
                DisposeOnFinish = false, Volume = 0.18f, SoundType = EnumSoundType.Ambient,
            });
            l52Room?.Start();
        }
        else if (!room && l52Room != null)
        {
            l52Room.Stop();
            l52Room.Dispose();
            l52Room = null;
        }
        if (!here) return;

        // A bell, far off down the halls: once every few minutes
        l52NextBell -= dt;
        if (l52NextBell <= 0)
        {
            l52NextBell = 150 + (float)rand.NextDouble() * 240;
            double yaw = rand.NextDouble() * Math.PI * 2;
            capi.World.PlaySoundAt(new AssetLocation("backrooms:sounds/ambient/52/bell"), pos.X + Math.Sin(yaw) * 40, pos.Y + 2, pos.Z + Math.Cos(yaw) * 40,
                null, false, 96, 0.55f);
        }
    }
}
