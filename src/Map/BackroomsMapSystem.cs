using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.GameContent;

namespace Backrooms.Map;

/// <summary>Swaps the vanilla terrain map layer for <see cref="BackroomsMapLayer"/> in Backrooms worlds.</summary>
public class BackroomsMapSystem : ModSystem
{
    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Client;

    // Must start before WorldMapManager (0.1) so our LevelFinalize handler runs before it creates the layers
    public override double ExecuteOrder() => 0.05;

    public override void StartClientSide(ICoreClientAPI api)
    {
        api.Event.LevelFinalize += () =>
        {
            if (!BackroomsWorld.IsBackroomsClimate(api.World.Config)) return;
            api.ModLoader.GetModSystem<WorldMapManager>().MapLayerRegistry["chunks"] = typeof(BackroomsMapLayer);
        };
    }
}
