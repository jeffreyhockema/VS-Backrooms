using System;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;

namespace Backrooms.Reality;

/// <summary>
/// Heat: the hot levels cost food. Vintage Story has no harm from heat and thirst was left out, so the heat of Pipe
/// Dreams (38 °C), the Electrical Station (35 °C) and the boiler halls (42 °C) works through hunger instead, with
/// the game's own "hungerrate" stat: from 30 °C up, you burn through food faster, up to half again as fast. Crossing
/// them means carrying rations, or finding a way round.
/// </summary>
public class HeatSystem : ModSystem
{
    private const string StatCode = "backrooms:heat";

    /// <summary>Where the heat starts to tell, and how much faster hunger runs per degree above it (at most <see cref="MaxExtra"/>).</summary>
    private const float From = 30f, PerDegree = 0.06f, MaxExtra = 0.5f;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            api.Event.RegisterGameTickListener(OnTick, 3000, 1500);
        });
    }

    private void OnTick(float dt)
    {
        foreach (IPlayer online in sapi.World.AllOnlinePlayers)
        {
            if (online.Entity is not { } entity) continue;
            int x = (int)Math.Floor(entity.Pos.X), y = (int)Math.Floor(entity.Pos.Y), z = (int)Math.Floor(entity.Pos.Z);
            int level = layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z));
            float temperature = layout.TemperatureAt(x, y, z, geometry.FloorFor(level));
            float extra = Math.Clamp((temperature - From) * PerDegree, 0, MaxExtra);
            // Only touch the stat when it changes: it is synced to the client
            if (Math.Abs(Current(entity) - extra) < 0.001f) continue;
            if (extra <= 0) entity.Stats.Remove("hungerrate", StatCode);
            else entity.Stats.Set("hungerrate", StatCode, extra, false);
        }
    }

    private static float Current(Entity entity) =>
        entity.Stats["hungerrate"].ValuesByKey.TryGetValue(StatCode, out var value) ? value.Value : 0f;
}
