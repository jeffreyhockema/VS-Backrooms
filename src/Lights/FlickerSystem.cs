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
    // The lights within Range of the player as of the last refresh: only these are visited at the animation rate
    private readonly List<BlockEntityFlickerLight> near = new();
    private readonly List<BlockEntityFlickerLight> scratch = new();
    private long nextRefreshMs;
    private const int RefreshMs = 250;
    private ICoreClientAPI capi;
    private long tickListener;
    private Backrooms.Reality.RealitySystem reality;

    /// <summary>
    /// The dead look of each kind of failing light, tesselated once per world: keyed by the lit block's id. Used from
    /// the tesselation threads, so always locked.
    /// </summary>
    internal readonly Dictionary<int, MeshData> OffMeshes = new();

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockEntityClass("BackroomsFlicker", typeof(BlockEntityFlickerLight));
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        tickListener = api.Event.RegisterGameTickListener(OnTick, 30);
    }

    public void Register(BlockEntityFlickerLight light) => lights.Add(light);

    public override void Dispose()
    {
        if (capi != null) capi.Event.UnregisterGameTickListener(tickListener);
        lock (OffMeshes) OffMeshes.Clear();
        lights.Clear();
        near.Clear();
        base.Dispose();
    }

    public void Unregister(BlockEntityFlickerLight light)
    {
        lights.Remove(light);
        near.Remove(light);
    }

    private void OnTick(float dt)
    {
        EntityPos pos = capi.World.Player?.Entity?.Pos;
        if (pos == null || lights.Count == 0) return;

        reality ??= capi.ModLoader.GetModSystem<Backrooms.Reality.RealitySystem>();
        bool realityShift = reality?.ShiftStrength > 0.3;
        // Finding which lights are near is the costly part (every loaded light in a lit level), so it is done a few
        // times a second; the animation of the few dozen near ones runs at the full rate
        long now = capi.World.ElapsedMilliseconds;
        if (now >= nextRefreshMs)
        {
            nextRefreshMs = now + RefreshMs;
            scratch.Clear();
            near.Clear();
            foreach (BlockEntityFlickerLight light in lights)
            {
                if (IsNear(light.Pos, pos)) near.Add(light);
                else scratch.Add(light);
            }
            // Distant ones are shown lit (a light that has just left the range may have been mid-flicker)
            foreach (BlockEntityFlickerLight light in scratch) light.SetLit(true);
            scratch.Clear();
        }
        foreach (BlockEntityFlickerLight light in near) light.Animate(dt, realityShift);
    }

    private static bool IsNear(BlockPos p, EntityPos pos)
    {
        double dx = p.X + 0.5 - pos.X, dy = p.Y - pos.Y, dz = p.Z + 0.5 - pos.Z;
        return dx * dx + dy * dy + dz * dz < Range * Range;
    }
}
