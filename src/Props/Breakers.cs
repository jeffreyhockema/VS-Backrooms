using System;
using System.Collections.Generic;
using System.Linq;
using ProtoBuf;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Util;

namespace Backrooms.Props;

/// <summary>
/// Breakers. Throwing a breaker box's (or an electrical panel's, or a knife switch's) main switch blows its fuse with a bang:
/// every working light of its section (within <see cref="BreakerReach"/> blocks of it, <see cref="BreakerDown"/> below to
/// <see cref="BreakerUp"/> above) is swapped for the same light dead, so the light level really falls, and what minds the
/// light knows it: Smilers come into the dark, a player in it is harder to see and draws more attention
/// (<see cref="Entities.Senses.InDark"/>). EXIT signs are on their own batteries and stay lit. A fuse
/// (<c>backrooms:fuse</c>) fitted to the same box brings every light that is still there back as it was; left alone, the
/// power comes back by itself after <see cref="BreakerHours"/> in-game hours. What was switched off is kept in the world's
/// save data, so a restart does not lose it.
/// </summary>
public partial class PropSystem
{
    public const int BreakerReach = 14, BreakerDown = 2, BreakerUp = 6;
    /// <summary>In-game hours before a tripped section's power comes back by itself.</summary>
    public const double BreakerHours = 24;
    public const string FuseCode = "backrooms:fuse";
    private const string BreakerSaveKey = "backrooms:props-breakers";

    [ProtoContract]
    public class DarkLight
    {
        [ProtoMember(1)] public int X;
        [ProtoMember(2)] public int Y;
        [ProtoMember(3)] public int Z;
        [ProtoMember(4)] public string Lit;
        [ProtoMember(5)] public string Dark;
    }

    [ProtoContract]
    public class DarkSection
    {
        [ProtoMember(1)] public int X;
        [ProtoMember(2)] public int Y;
        [ProtoMember(3)] public int Z;
        /// <summary>When it was tripped (Calendar.TotalHours).</summary>
        [ProtoMember(4)] public double AtHours;
        [ProtoMember(5)] public List<DarkLight> Lights = new();
        /// <summary>Restoring: the power is back, but some of its lights are in chunks not loaded yet.</summary>
        [ProtoMember(6)] public bool Restoring;

        public BlockPos Pos => new(X, Y, Z);
    }

    private List<DarkSection> dark = new();
    private bool darkDirty;

    /// <summary>The light block each lit light of ours goes dark as (0: not one, or none to go dark as), by block id.</summary>
    private readonly Dictionary<int, int> darkIds = new();

    /// <summary>The dead light a working one is swapped for, or 0.</summary>
    internal int DarkIdOf(Block block)
    {
        if (block == null || block.Id == 0) return 0;
        if (darkIds.TryGetValue(block.Id, out int id)) return id;
        id = 0;
        if (block.Code?.Domain == "backrooms")
        {
            string first = block.FirstCodePart();
            string state = block.Variant?["state"];
            if (first == "pillarlight") id = sapi.World.GetBlock(new AssetLocation("backrooms:pillarlightdead"))?.Id ?? 0;
            // (The EXIT signs are battery-backed: lore and the way out alike)
            else if (state != null && state is not ("off" or "dead") && (block.LightHsv[2] > 0 || state is "lit" or "flicker" or "on")
                     && !first.StartsWith("exit", StringComparison.Ordinal))
            {
                foreach (string off in new[] { "off", "dead" })
                {
                    Block dead = sapi.World.GetBlock(BlockCodes.WithVariant(block, "state", off));
                    if (dead != null && dead.Id != 0 && dead.Id != block.Id) { id = dead.Id; break; }
                }
            }
        }
        darkIds[block.Id] = id;
        return id;
    }

    internal DarkSection SectionAt(BlockPos breaker) => dark.FirstOrDefault(s => s.X == breaker.X && s.Y == breaker.Y && s.Z == breaker.Z && !s.Restoring);

    /// <summary>A breaker used: tripped if its section is lit; if tripped, a fuse in hand brings the lights back.</summary>
    internal void UseBreaker(BlockPos pos, IPlayer byPlayer, bool withFuse)
    {
        DarkSection section = SectionAt(pos);
        if (section != null)
        {
            ItemSlot hand = byPlayer?.InventoryManager?.ActiveHotbarSlot;
            bool fuseInHand = hand?.Itemstack?.Collectible?.Code?.ToString() == FuseCode;
            if (!withFuse && !fuseInHand)
            {
                Play("game:sounds/effect/latch", pos, 12, 0.6f);
                Tell(byPlayer, "props-breaker-dark");
                return;
            }
            if (fuseInHand && byPlayer.WorldData?.CurrentGameMode != EnumGameMode.Creative)
            {
                hand.TakeOut(1);
                hand.MarkDirty();
            }
            Play("game:sounds/effect/latch", pos, 16);
            Play("backrooms:sounds/effect/powerdown", pos, 24, 0.5f);
            int back = Restore(section);
            Note(byPlayer, "props-breaker-restored");
            sapi.Logger.Notification("[backrooms] props: breaker at {0} {1} {2}: a fuse fitted, {3} lights back on", pos.X, pos.Y, pos.Z, back);
            return;
        }
        Trip(pos, byPlayer);
    }

    private void Trip(BlockPos pos, IPlayer byPlayer)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        // (A light already dark in another tripped section is that section's)
        var taken = new HashSet<long>(dark.SelectMany(s => s.Lights).Select(l => Key(new BlockPos(l.X, l.Y, l.Z))));
        var section = new DarkSection { X = pos.X, Y = pos.Y, Z = pos.Z, AtHours = sapi.World.Calendar.TotalHours };
        var p = new BlockPos(pos.dimension);
        for (int dy = -BreakerDown; dy <= BreakerUp; dy++)
            for (int dz = -BreakerReach; dz <= BreakerReach; dz++)
                for (int dx = -BreakerReach; dx <= BreakerReach; dx++)
                {
                    p.Set(pos.X + dx, pos.Y + dy, pos.Z + dz);
                    Block block = ba.GetBlock(p);
                    int deadId = DarkIdOf(block);
                    if (deadId == 0 || taken.Contains(Key(p))) continue;
                    Block deadBlock = sapi.World.GetBlock(deadId);
                    section.Lights.Add(new DarkLight { X = p.X, Y = p.Y, Z = p.Z, Lit = block.Code.ToString(), Dark = deadBlock.Code.ToString() });
                    ba.SetBlock(deadId, p);
                }
        Play("game:sounds/effect/latch", pos, 16);
        if (section.Lights.Count == 0)
        {
            Tell(byPlayer, "props-breaker-nolights");
            return;
        }
        dark.Add(section);
        darkDirty = true;
        Play("backrooms:sounds/effect/props/fusepop", pos, 48);
        Play("backrooms:sounds/effect/powerdown", pos, 32, 0.8f);
        SendFx(new PropFxPacket { Kind = PropFxPacket.Sparks, Xyz = new[] { pos.X, pos.Y, pos.Z }, DurationMs = 600, Dir = ValveFacing(ba.GetBlock(pos))?.Index ?? -1 }, Centre(pos));
        // The bang carries; whoever threw the switch is heard by what hunts them
        if (byPlayer?.Entity != null) director?.MakeNoise(byPlayer.Entity, 0.3, Centre(pos), 0.8, "breaker");
        else director?.RaiseNoise(Centre(pos), 0.8, "breaker", null);
        Note(byPlayer, "props-breaker-tripped");
        sapi.Logger.Notification("[backrooms] props: breaker at {0} {1} {2} tripped: {3} lights off", pos.X, pos.Y, pos.Z, section.Lights.Count);
    }

    /// <summary>
    /// Brings back every light of a section that is still the dead light it was made (one broken or changed since is left
    /// alone). Lights in chunks not loaded now are left for later (<see cref="CheckBreakers"/>). Returns how many came back.
    /// </summary>
    private int Restore(DarkSection section)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        int back = 0;
        var p = new BlockPos(0);
        section.Restoring = true;
        section.Lights.RemoveAll(l =>
        {
            p.Set(l.X, l.Y, l.Z);
            if (ba.GetChunkAtBlockPos(p) == null) return false;
            Block now = ba.GetBlock(p);
            Block lit = sapi.World.GetBlock(new AssetLocation(l.Lit));
            if (lit != null && now?.Code?.ToString() == l.Dark)
            {
                ba.SetBlock(lit.Id, p);
                back++;
            }
            return true;
        });
        if (section.Lights.Count == 0) dark.Remove(section);
        darkDirty = true;
        return back;
    }

    /// <summary>Every few seconds: sections whose day is up come back on, and those still restoring finish when their chunks load.</summary>
    private void CheckBreakers()
    {
        if (dark.Count == 0) return;
        double hours = sapi.World.Calendar.TotalHours;
        foreach (DarkSection s in dark.ToArray())
        {
            if (!s.Restoring && hours - s.AtHours < BreakerHours) continue;
            int back = Restore(s);
            if (back > 0) sapi.Logger.Notification("[backrooms] props: the power of the breaker at {0} {1} {2} came back: {3} lights on", s.X, s.Y, s.Z, back);
        }
    }

    /// <summary>In-game hours until a tripped breaker's power comes back by itself, or -1 if it is not tripped.</summary>
    internal double HoursLeft(BlockPos breaker) =>
        SectionAt(breaker) is { } s ? Math.Max(0, BreakerHours - (sapi.World.Calendar.TotalHours - s.AtHours)) : -1;

    private void LoadBreakers()
    {
        try
        {
            byte[] data = sapi.WorldManager.SaveGame.GetData(BreakerSaveKey);
            dark = data == null ? new() : SerializerUtil.Deserialize<List<DarkSection>>(data) ?? new();
            foreach (DarkSection s in dark) s.Lights ??= new();
            if (dark.Count > 0) sapi.Logger.Notification("[backrooms] props: {0} tripped breakers ({1} lights dark)", dark.Count, dark.Sum(s => s.Lights.Count));
        }
        catch (Exception ex)
        {
            sapi.Logger.Error("[backrooms] props: could not read the tripped breakers; their lights stay dark: {0}", ex);
            // (One copy of what would not parse is kept, so the next save does not destroy it)
            try
            {
                byte[] raw = sapi.WorldManager.SaveGame.GetData(BreakerSaveKey);
                if (raw != null && sapi.WorldManager.SaveGame.GetData(BreakerSaveKey + "-unreadable") == null)
                    sapi.WorldManager.SaveGame.StoreData(BreakerSaveKey + "-unreadable", raw);
            }
            catch (Exception) { }
            dark = new();
        }
    }

    private void SaveBreakers()
    {
        if (!darkDirty) return;
        darkDirty = false;
        sapi.WorldManager.SaveGame.StoreData(BreakerSaveKey, SerializerUtil.Serialize(dark));
    }
}
