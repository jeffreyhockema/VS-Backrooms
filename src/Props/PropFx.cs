using System;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Props;

/// <summary>
/// The clients' side of the props: the water falling from sprinkler heads, a jet of steam, a breaker's sparks. The server
/// says what and where once (<see cref="PropFxPacket"/>); each client draws it for as long as it lasts, on the particle
/// thread.
/// </summary>
public partial class PropSystem
{
    private void OnFx(PropFxPacket fx)
    {
        if (capi == null || fx?.Xyz == null || fx.Xyz.Length < 3) return;
        switch (fx.Kind)
        {
            case PropFxPacket.Spray: StartSpray(fx); break;
            case PropFxPacket.Steam: StartSteam(fx); break;
            case PropFxPacket.Sparks: Sparks(fx); break;
        }
    }

    private void StartSpray(PropFxPacket fx)
    {
        int heads = fx.Xyz.Length / 3;
        var at = new Vec3d[heads];
        for (int i = 0; i < heads; i++) at[i] = new Vec3d(fx.Xyz[i * 3] + 0.5, fx.Xyz[i * 3 + 1] + 0.1, fx.Xyz[i * 3 + 2] + 0.5);
        var drops = new SimpleParticleProperties
        {
            MinQuantity = 2, AddQuantity = 2,
            Color = ColorUtil.ToRgba(190, 200, 215, 235),
            AddPos = new Vec3d(0.3, 0, 0.3),
            MinVelocity = new Vec3f(-1.6f, -1.2f, -1.6f), AddVelocity = new Vec3f(3.2f, 0.6f, 3.2f),
            LifeLength = 1.1f, GravityEffect = 0.9f,
            MinSize = 0.18f, MaxSize = 0.32f,
            ParticleModel = EnumParticleModel.Quad,
            ShouldDieInLiquid = true,
            WithTerrainCollision = true,
        };
        var mist = new SimpleParticleProperties
        {
            MinQuantity = 0, AddQuantity = 1,
            Color = ColorUtil.ToRgba(60, 220, 225, 235),
            AddPos = new Vec3d(1.6, 0.4, 1.6),
            MinVelocity = new Vec3f(-0.2f, -0.5f, -0.2f), AddVelocity = new Vec3f(0.4f, 0.3f, 0.4f),
            LifeLength = 2.2f, GravityEffect = 0.02f,
            MinSize = 0.8f, MaxSize = 1.4f,
            ParticleModel = EnumParticleModel.Quad,
            SizeEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, 1.5f),
            OpacityEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, -40f),
        };
        float left = fx.DurationMs / 1000f;
        Random rand = new();
        capi.Event.RegisterAsyncParticleSpawner((dt, manager) =>
        {
            left -= dt;
            if (left <= 0) return false;
            // (About thirty a second from each head, fewer when there are many)
            double chance = Math.Min(1, dt * 30 / Math.Max(1, heads / 8.0));
            foreach (Vec3d head in at)
            {
                if (rand.NextDouble() > chance) continue;
                drops.MinPos = head.AddCopy(-0.15, 0, -0.15);
                manager.Spawn(drops);
                if (rand.NextDouble() < 0.08)
                {
                    mist.MinPos = head.AddCopy(-0.8, -1.5, -0.8);
                    manager.Spawn(mist);
                }
            }
            return true;
        });
    }

    private void StartSteam(PropFxPacket fx)
    {
        Vec3d source = new(fx.Xyz[0] + 0.5, fx.Xyz[1] + 0.5, fx.Xyz[2] + 0.5);
        BlockFacing dir = fx.Dir >= 0 && fx.Dir < BlockFacing.ALLFACES.Length ? BlockFacing.ALLFACES[fx.Dir] : BlockFacing.DOWN;
        Vec3f n = new(dir.Normalf.X, dir.Normalf.Y, dir.Normalf.Z);
        float speed = Math.Max(4f, fx.Length * 1.6f);
        source.Add(n.X * 0.5, n.Y * 0.5, n.Z * 0.5);
        var steam = new SimpleParticleProperties
        {
            MinQuantity = 3, AddQuantity = 3,
            Color = ColorUtil.ToRgba(170, 235, 235, 240),
            AddPos = new Vec3d(0.3, 0.3, 0.3),
            MinVelocity = new Vec3f(n.X * speed - 1.2f, n.Y * speed - 1.2f, n.Z * speed - 1.2f), AddVelocity = new Vec3f(2.4f, 2.4f, 2.4f),
            LifeLength = 0.9f, GravityEffect = -0.04f,
            MinSize = 0.5f, MaxSize = 0.9f,
            ParticleModel = EnumParticleModel.Quad,
            SizeEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, 2.5f),
            OpacityEvolve = EvolvingNatFloat.create(EnumTransformFunction.LINEAR, -160f),
            WithTerrainCollision = true,
        };
        steam.MinPos = source.AddCopy(-0.15, -0.15, -0.15);
        float left = fx.DurationMs / 1000f;
        capi.Event.RegisterAsyncParticleSpawner((dt, manager) =>
        {
            left -= dt;
            if (left <= 0) return false;
            int bursts = Math.Max(1, (int)(dt * 60));
            for (int i = 0; i < bursts; i++) manager.Spawn(steam);
            return true;
        });
    }

    private void Sparks(PropFxPacket fx)
    {
        BlockFacing face = fx.Dir >= 0 && fx.Dir < BlockFacing.ALLFACES.Length ? BlockFacing.ALLFACES[fx.Dir] : BlockFacing.UP;
        Vec3d at = new(fx.Xyz[0] + 0.5 + face.Normalf.X * 0.6, fx.Xyz[1] + 0.6, fx.Xyz[2] + 0.5 + face.Normalf.Z * 0.6);
        var sparks = new SimpleParticleProperties
        {
            MinQuantity = 30, AddQuantity = 20,
            Color = ColorUtil.ToRgba(255, 255, 190, 70),
            MinPos = at.AddCopy(-0.2, -0.2, -0.2), AddPos = new Vec3d(0.4, 0.4, 0.4),
            MinVelocity = new Vec3f(face.Normalf.X * 2 - 2, 0.5f, face.Normalf.Z * 2 - 2), AddVelocity = new Vec3f(4, 3, 4),
            LifeLength = 0.5f, GravityEffect = 1f,
            MinSize = 0.08f, MaxSize = 0.16f,
            ParticleModel = EnumParticleModel.Cube,
            VertexFlags = 255,
        };
        capi.World.SpawnParticles(sparks);
    }
}
