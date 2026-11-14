using System;
using System.Collections.Generic;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Props;

/// <summary>
/// Fire alarms. Pulled, a station's bell rings for <see cref="FireAlarmMs"/>, and the sprinkler heads of its section (within
/// <see cref="SprinklerReach"/> blocks of it) spray for as long: fires, firepits, lit torches (held ones too) and candles under
/// them go out, the female Deathmoths scatter from the water and the males come to drink it (<see cref="WaterNear"/>,
/// read by AiTaskMoth). A station that has been pulled is reset ten minutes later; one with no heads near still rings.
/// </summary>
public partial class PropSystem
{
    /// <summary>How far round a fire alarm its sprinkler heads are (blocks, each way), and how far up and down.</summary>
    public const int SprinklerReach = 12, SprinklerUp = 6, SprinklerDown = 2;

    /// <summary>How far round a head (blocks) and how far below it the water falls.</summary>
    public const int SprayRadius = 2, SprayDepth = 7;

    /// <summary>How long (ms) before a pulled station can be pulled again.</summary>
    public const long AlarmResetMs = 600_000;

    /// <summary>The most heads one alarm sets going (the nearest).</summary>
    private const int MaxHeads = 32;

    private sealed class Spray
    {
        public BlockPos Alarm;
        public List<BlockPos> Heads;
        public long EndMs, NextWetMs;
        public int PutOut;
    }

    private readonly List<Spray> sprays = new();
    private readonly Dictionary<long, long> alarmResetMs = new();

    /// <summary>
    /// Where water is falling now (a head of a spraying sprinkler), and until when: what the Deathmoths react to. Swapped
    /// whole (never changed in place), so the AI reads it without a lock.
    /// </summary>
    public static (Vec3d At, long EndMs)[] Waters { get; private set; } = Array.Empty<(Vec3d, long)>();

    /// <summary>The nearest falling water within range of a position, or null (sprinklers spraying).</summary>
    public static Vec3d WaterNear(IWorldAccessor world, Vec3d pos, double range)
    {
        (Vec3d At, long EndMs)[] waters = Waters;
        if (waters.Length == 0) return null;
        long now = world.ElapsedMilliseconds;
        Vec3d best = null;
        double bestD = range * range;
        foreach (var (at, end) in waters)
        {
            if (end < now) continue;
            double d = at.SquareDistanceTo(pos);
            if (d < bestD) { bestD = d; best = at; }
        }
        return best;
    }

    private static bool IsSprinklerHead(Block block) =>
        block?.Code?.Domain == "backrooms" && (block.FirstCodePart() == "sprinkler" || block.Code.Path == "officeceilingalt-sprinkler");

    /// <summary>A fire alarm pulled (or its test button pressed): the bell, and the sprinklers of its section.</summary>
    internal void PullAlarm(BlockPos pos, IPlayer byPlayer)
    {
        long now = sapi.World.ElapsedMilliseconds;
        if (RingingAt(pos) != null)
        {
            Tell(byPlayer, "props-alarm-ringing");
            return;
        }
        if (alarmResetMs.TryGetValue(Key(pos), out long reset) && now < reset)
        {
            Tell(byPlayer, "props-alarm-reset", Math.Max(1, (int)Math.Ceiling((reset - now) / 60000.0)));
            return;
        }
        alarmResetMs[Key(pos)] = now + FireAlarmMs + AlarmResetMs;
        Play("game:sounds/effect/latch", pos, 16);
        StartRing("firealarm", pos, byPlayer?.Entity);

        List<BlockPos> heads = FindHeads(pos);
        if (heads.Count == 0) return;
        var spray = new Spray { Alarm = pos.Copy(), Heads = heads, EndMs = now + FireAlarmMs, NextWetMs = now + 1500 };
        sprays.Add(spray);
        UpdateWaters(now);
        int[] xyz = new int[heads.Count * 3];
        for (int i = 0; i < heads.Count; i++) { xyz[i * 3] = heads[i].X; xyz[i * 3 + 1] = heads[i].Y; xyz[i * 3 + 2] = heads[i].Z; }
        SendFx(new PropFxPacket { Kind = PropFxPacket.Spray, Xyz = xyz, DurationMs = FireAlarmMs }, Centre(pos));
        // The hiss of the water, from a few of the heads
        foreach (BlockPos head in heads.Take(4)) Play("game:sounds/effect/watering-loop", head, 24, 0.7f);
    }

    /// <summary>The sprinkler heads of an alarm's section, nearest first.</summary>
    private List<BlockPos> FindHeads(BlockPos alarm)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var found = new List<(BlockPos Pos, int D)>();
        var p = new BlockPos(alarm.dimension);
        for (int dy = -SprinklerDown; dy <= SprinklerUp; dy++)
            for (int dz = -SprinklerReach; dz <= SprinklerReach; dz++)
                for (int dx = -SprinklerReach; dx <= SprinklerReach; dx++)
                {
                    p.Set(alarm.X + dx, alarm.Y + dy, alarm.Z + dz);
                    if (IsSprinklerHead(ba.GetBlock(p))) found.Add((p.Copy(), dx * dx + dy * dy + dz * dz));
                }
        return found.OrderBy(f => f.D).Take(MaxHeads).Select(f => f.Pos).ToList();
    }

    private void UpdateWaters(long now)
    {
        Waters = sprays.Where(s => s.EndMs > now).SelectMany(s => s.Heads.Select(h => (new Vec3d(h.X + 0.5, h.Y, h.Z + 0.5), s.EndMs))).ToArray();
    }

    private void TickSprays(long now)
    {
        if (sprays.Count == 0) return;
        bool ended = false;
        for (int i = sprays.Count - 1; i >= 0; i--)
        {
            Spray s = sprays[i];
            if (now >= s.EndMs)
            {
                sapi.Logger.Notification("[backrooms] props: the sprinklers of the fire alarm at {0} {1} {2} stop: {3} heads sprayed, {4} fires put out",
                    s.Alarm.X, s.Alarm.Y, s.Alarm.Z, s.Heads.Count, s.PutOut);
                sprays.RemoveAt(i);
                ended = true;
                continue;
            }
            if (now < s.NextWetMs) continue;
            s.NextWetMs = now + 1000;
            s.PutOut += Wet(s.Heads);
        }
        if (ended) UpdateWaters(now);
    }

    /// <summary>Puts out what burns under the heads (once a second while they spray). Returns how many went out.</summary>
    private int Wet(List<BlockPos> heads)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        var seen = new HashSet<long>();
        var p = new BlockPos(heads[0].dimension);
        int putOut = 0;
        // (Nothing is put out under a spray nobody is near: the chunks round it are not ticking)
        bool near = false;
        foreach (IPlayer pl in sapi.World.AllOnlinePlayers)
            if (pl.Entity != null && pl.Entity.Pos.Dimension == heads[0].dimension && pl.Entity.Pos.SquareDistanceTo(heads[0].X + 0.5, heads[0].Y, heads[0].Z + 0.5) <= 64 * 64) { near = true; break; }
        if (!near) return 0;
        foreach (BlockPos head in heads)
            for (int dz = -SprayRadius; dz <= SprayRadius; dz++)
                for (int dx = -SprayRadius; dx <= SprayRadius; dx++)
                    for (int dy = 0; dy >= -SprayDepth; dy--)
                    {
                        p.Set(head.X + dx, head.Y + dy, head.Z + dz);
                        if (!seen.Add(Key(p))) continue;
                        if (Douse(ba, p)) putOut++;
                    }
        // Lit torches in the hand of anyone standing under them
        foreach (BlockPos head in heads)
        {
            Vec3d at = new(head.X + 0.5, head.Y - SprayDepth / 2.0, head.Z + 0.5);
            foreach (Entity e in sapi.World.GetEntitiesAround(at, SprayRadius + 0.5f, SprayDepth / 2f + 0.5f, e => e is EntityAgent { Alive: true }))
                putOut += DouseHeld((EntityAgent)e);
        }
        if (putOut > 0) Entities.Wards.Invalidate();
        return putOut;
    }

    /// <summary>Puts out one block if it burns: a fire, a firepit or a torch (anything hot that the rain would cool), a candle.</summary>
    private bool Douse(IBlockAccessor ba, BlockPos p)
    {
        Block block = ba.GetBlock(p);
        if (block == null || block.Id == 0) return false;
        string path = block.Code?.Path;
        if (block.Code?.Domain == "game")
        {
            if (path == "fire")
            {
                ba.SetBlock(0, p);
                Play("game:sounds/effect/extinguish", p, 16, 0.8f);
                return true;
            }
            // Candles have no unlit state: knocked down by the water, they drop as candles
            if (path == "candle" || path.StartsWith("bunchocandles", StringComparison.Ordinal))
            {
                sapi.World.BlockAccessor.BreakBlock(p, null);
                Play("game:sounds/effect/extinguish", p, 16, 0.5f);
                return true;
            }
        }
        if (ba.GetBlockEntity(p) is ITemperatureSensitive hot && hot.IsHot)
        {
            hot.CoolNow(25f, (slot, at, temp, sizzle) => ITemperatureSensitive.CoolStack(sapi, slot, at, 25f, temp, sizzle));
            return true;
        }
        return false;
    }

    /// <summary>Puts out a lit torch in either hand. Returns how many.</summary>
    private int DouseHeld(EntityAgent agent)
    {
        int n = 0;
        foreach (ItemSlot slot in new[] { Entities.Senses.RightHand(agent), Entities.Senses.LeftHand(agent) })
        {
            if (slot?.Itemstack?.Block is not { } torch || torch.Code?.Domain != "game" || torch.FirstCodePart() != "torch" || torch.Variant?["state"] != "lit") continue;
            Block extinct = sapi.World.GetBlock(torch.CodeWithVariant("state", "extinct"));
            if (extinct == null) continue;
            slot.Itemstack = new ItemStack(extinct, slot.Itemstack.StackSize);
            slot.MarkDirty();
            sapi.World.PlaySoundAt(new AssetLocation("game:sounds/effect/extinguish"), agent, null, true, 16, 0.6f);
            n++;
        }
        return n;
    }
}
