using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Common.Entities;

namespace Backrooms.Lights;

/// <summary>Animates the flickering lights near the player. Distant ones are left alone (and shown lit).</summary>
public class FlickerSystem : ModSystem
{
    private const float Range = 24f;

    private readonly HashSet<BlockEntityFlickerLight> lights = new();
    private readonly List<BlockEntityFlickerLight> scratch = new();
    private ICoreClientAPI capi;
    private Backrooms.Reality.RealitySystem reality;

    /// <summary>The dead look of each kind of failing light, tesselated once per world.</summary>
    internal readonly Dictionary<int, MeshData> OffMeshes = new();

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockEntityClass("BackroomsFlicker", typeof(BlockEntityFlickerLight));
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Event.RegisterGameTickListener(OnTick, 30);
    }

    public void Register(BlockEntityFlickerLight light) => lights.Add(light);

    public override void Dispose()
    {
        lock (OffMeshes) OffMeshes.Clear();
        lights.Clear();
        base.Dispose();
    }

    public void Unregister(BlockEntityFlickerLight light) => lights.Remove(light);

    private void OnTick(float dt)
    {
        EntityPos pos = capi.World.Player?.Entity?.Pos;
        if (pos == null || lights.Count == 0) return;

        reality ??= capi.ModLoader.GetModSystem<Backrooms.Reality.RealitySystem>();
        bool realityShift = reality?.ShiftStrength > 0.3;
        scratch.Clear();
        scratch.AddRange(lights);
        foreach (BlockEntityFlickerLight light in scratch)
        {
            BlockPos p = light.Pos;
            double dx = p.X + 0.5 - pos.X, dy = p.Y - pos.Y, dz = p.Z + 0.5 - pos.Z;
            if (dx * dx + dy * dy + dz * dz < Range * Range) light.Animate(dt, realityShift);
            else light.SetLit(true);
        }
    }
}
