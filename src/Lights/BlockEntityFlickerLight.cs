using System;
using System.Collections.Generic;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Lights;

/// <summary>
/// A failing light panel. It never emits block light (changing real light levels is far too expensive to do
/// several times a second); instead the client swaps its look between the lit and the dead panel, and now and then
/// crackles. Animation only runs near the player, driven by <see cref="FlickerSystem"/>.
/// </summary>
public class BlockEntityFlickerLight : BlockEntity
{
    private enum Mode { Stutter, Dying, Buzzing }

    private Mode mode;
    private Random rand;
    private float timer;
    private int burstLeft;

    public bool Lit { get; private set; } = true;

    public override void Initialize(ICoreAPI api)
    {
        base.Initialize(api);
        if (api.Side != EnumAppSide.Client) return;

        int hash = Pos.GetHashCode();
        rand = new Random(hash);
        mode = (Mode)(int)(Math.Abs((long)hash) % 3);
        timer = (float)rand.NextDouble() * 4f;
        api.ModLoader.GetModSystem<FlickerSystem>()?.Register(this);
    }

    public override void OnBlockRemoved()
    {
        base.OnBlockRemoved();
        Api?.ModLoader.GetModSystem<FlickerSystem>()?.Unregister(this);
    }

    public override void OnBlockUnloaded()
    {
        base.OnBlockUnloaded();
        Api?.ModLoader.GetModSystem<FlickerSystem>()?.Unregister(this);
    }

    /// <summary>Advances the flicker pattern. Client only. During a Reality Shift every failing light is all but dead.</summary>
    public void Animate(float dt, bool realityShift)
    {
        timer -= dt;
        if (timer > 0) return;

        switch (realityShift ? Mode.Dying : mode)
        {
            case Mode.Stutter:
                // Mostly on, with a short burst of stuttering every few seconds
                if (burstLeft > 0)
                {
                    SetLit(!Lit);
                    burstLeft--;
                    timer = Range(0.04f, 0.15f);
                }
                else
                {
                    SetLit(true);
                    burstLeft = rand.Next(2, 8) * 2;
                    timer = Range(2f, 9f);
                }
                break;

            case Mode.Dying:
                // Mostly dead, with brief flashes
                SetLit(!Lit);
                timer = Lit ? Range(0.05f, 0.4f) : Range(1.5f, 8f);
                break;

            default:
                // Erratic buzzing (each change redraws the chunk, so not too erratic)
                SetLit(rand.NextDouble() < 0.7);
                timer = Range(0.12f, 0.45f);
                break;
        }
    }

    public void SetLit(bool lit)
    {
        if (Lit == lit) return;
        Lit = lit;
        MarkDirty(redrawOnClient: true);

        if (lit && rand.NextDouble() < 0.25)
        {
            var sound = new AssetLocation("backrooms", "sounds/effect/flicker" + rand.Next(1, 4));
            Api.World.PlaySoundAt(sound, Pos.X + 0.5, Pos.Y, Pos.Z + 0.5, null, randomizePitch: true, range: 14, volume: 0.3f);
        }
    }

    public override bool OnTesselation(ITerrainMeshPool mesher, ITesselatorAPI tessThreadTesselator)
    {
        if (Lit) return false;
        MeshData mesh = GetOffMesh(tessThreadTesselator);
        // (Without a dead look to show, draw the block as it is)
        if (mesh == null) return false;
        mesher.AddMeshData(mesh);
        return true;
    }

    /// <summary>The dead panel's mesh (the block named by the "offBlock" attribute), tesselated once per kind of light.</summary>
    private MeshData GetOffMesh(ITesselatorAPI tesselator)
    {
        // The meshes are cached per world (block ids and the texture atlas differ from one world to the next), keyed by
        // this block's id, so the off block is only looked up the first time
        Dictionary<int, MeshData> cache = Api.ModLoader.GetModSystem<FlickerSystem>()?.OffMeshes;
        if (cache == null) return null;
        lock (cache)
        {
            if (!cache.TryGetValue(Block.BlockId, out MeshData mesh))
            {
                string offCode = Block.Attributes?["offBlock"].AsString();
                Block offBlock = offCode == null ? Block : Api.World.GetBlock(new AssetLocation(offCode)) ?? Block;
                tesselator.TesselateBlock(offBlock, out mesh);
                cache[Block.BlockId] = mesh;
            }
            return mesh;
        }
    }

    private float Range(float min, float max) => min + (float)rand.NextDouble() * (max - min);
}
