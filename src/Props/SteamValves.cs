using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Props;

/// <summary>
/// Steam valves. Turned, a valve hisses for <see cref="SteamWarnMs"/>, then the nearest steam pipe within
/// <see cref="SteamReach"/> blocks (a leak first, an overhead bundle, a boiler header or riser, a wall pipe; the valve itself
/// if there is none) blasts a jet of scalding steam across the passage for <see cref="SteamMs"/>: down to the floor and a
/// block either side from a pipe overhead, else straight out from the wall for up to <see cref="SteamLength"/> blocks.
/// Anything in it, players too, takes <see cref="SteamDamage"/> (heat) every half second. While it blows, the pathfinder
/// treats its cells as impassable, so creatures plan round it. The valve then needs <see cref="SteamRearmMs"/> to build
/// its pressure again.
/// </summary>
public partial class PropSystem
{
    public const int SteamReach = 6, SteamLength = 6;
    public const long SteamWarnMs = 1000, SteamMs = 5000, SteamRearmMs = 60_000;
    /// <summary>Heat damage every half second to whatever stands in the jet (10 over the whole blast).</summary>
    public const float SteamDamage = 1f;
    public const double SteamLoudness = 0.9;

    private sealed class Jet
    {
        public BlockPos Valve, Source;
        public BlockFacing Dir;
        public List<BlockPos> Cells;
        public long BlowMs, EndMs, NextHurtMs, NextSoundMs;
        public bool Started;
        public long Who = -1;
        public readonly Dictionary<string, float> Hurt = new();
    }

    private readonly List<Jet> jets = new();
    private readonly Dictionary<long, long> valveRearmMs = new();

    internal static readonly HashSet<long> EmptyCells = new();

    /// <summary>The cells of every jet blowing now: read by the pathfinder (any thread), swapped whole.</summary>
    internal static volatile HashSet<long> JetCells = EmptyCells;

    /// <summary>A valve turned: the warning hiss, then the jet.</summary>
    internal void TurnValve(BlockPos pos, IPlayer byPlayer)
    {
        long now = sapi.World.ElapsedMilliseconds;
        if (jets.Any(j => j.Valve.Equals(pos)))
        {
            Tell(byPlayer, "props-valve-venting");
            return;
        }
        if (valveRearmMs.TryGetValue(Key(pos), out long rearm) && now < rearm)
        {
            Play("game:sounds/effect/latch", pos, 12, 0.6f);
            Tell(byPlayer, "props-valve-building", Math.Max(1, (int)Math.Ceiling((rearm - now) / 1000.0)));
            return;
        }
        (BlockPos source, BlockFacing dir, List<BlockPos> cells) = PlanJet(pos);
        valveRearmMs[Key(pos)] = now + SteamWarnMs + SteamMs + SteamRearmMs;
        jets.Add(new Jet
        {
            Valve = pos.Copy(), Source = source, Dir = dir, Cells = cells, BlowMs = now + SteamWarnMs, EndMs = now + SteamWarnMs + SteamMs,
            NextHurtMs = now + SteamWarnMs, NextSoundMs = now + SteamWarnMs, Who = byPlayer?.Entity?.EntityId ?? -1,
        });
        Play("game:sounds/effect/gearbox_turn", pos, 16, 0.8f);
        Play("backrooms:sounds/effect/props/steamwarn", source, 32);
        director?.RaiseNoise(Centre(source), 0.5, "steam", byPlayer?.Entity);
        sapi.Logger.Notification("[backrooms] props: valve at {0} {1} {2} turned: steam from {3} {4} {5} going {6}, {7} cells", pos.X, pos.Y, pos.Z,
            source.X, source.Y, source.Z, dir.Code, cells.Count);
    }

    /// <summary>Which first parts of block codes carry steam (the pipes a valve can blow).</summary>
    private static readonly HashSet<string> SteamPipes = new() { "pipes", "plantheader", "plantriser", "boiler", "feedpipe", "drippipe", "wallpipecorner" };

    private static int SteamScore(Block block)
    {
        if (block?.Code?.Domain != "backrooms") return 0;
        string first = block.FirstCodePart(), path = block.Code.Path;
        if (first == "pipes") return path.StartsWith("pipes-leak", StringComparison.Ordinal) ? 3 : path.Contains("tar") ? 1 : 2;
        if (SteamPipes.Contains(first)) return 2;
        if (first == "tunnelwall" && path is "tunnelwall-pipes" or "tunnelwall-riser" or "tunnelwall-riserjoint" or "tunnelwall-pipesjoint" or "tunnelwall-pipesbracket") return 1;
        if (first == "plasterdeco" && (block.Variant?["decor"]?.StartsWith("pipesv", StringComparison.Ordinal) == true || block.Variant?["decor"] == "pipecluster")) return 1;
        return 0;
    }

    /// <summary>Where the steam comes out, which way it goes and the cells it fills.</summary>
    private (BlockPos Source, BlockFacing Dir, List<BlockPos> Cells) PlanJet(BlockPos valve)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        BlockPos best = null;
        double bestScore = double.MinValue;
        var p = new BlockPos(valve.dimension);
        for (int dy = -SteamReach; dy <= SteamReach; dy++)
            for (int dz = -SteamReach; dz <= SteamReach; dz++)
                for (int dx = -SteamReach; dx <= SteamReach; dx++)
                {
                    if (dx == 0 && dy == 0 && dz == 0) continue;
                    p.Set(valve.X + dx, valve.Y + dy, valve.Z + dz);
                    int kind = SteamScore(ba.GetBlock(p));
                    if (kind == 0 || OpenFace(ba, p, null) == null) continue;
                    // (A leak is worth three blocks of distance, a plain pipe two)
                    double score = kind * 3 - Math.Sqrt(dx * dx + dy * dy + dz * dz);
                    if (score > bestScore) { bestScore = score; best = p.Copy(); }
                }
        BlockPos source = best ?? valve.Copy();
        BlockFacing facing = ValveFacing(ba.GetBlock(valve));
        BlockFacing dir = OpenFace(ba, source, best == null ? facing : null) ?? facing ?? BlockFacing.UP;
        return (source, dir, Cells(ba, source, dir));
    }

    /// <summary>The way a valve's front faces (its side variant), or null.</summary>
    private static BlockFacing ValveFacing(Block block) => block.Variant?["side"] is string side ? BlockFacing.FromCode(side) : null;

    /// <summary>The way out of a block into the open: down if it hangs over air, else a side with air (the preferred side first).</summary>
    private static BlockFacing OpenFace(IBlockAccessor ba, BlockPos pos, BlockFacing prefer)
    {
        if (prefer != null && Passable(ba, pos.AddCopy(prefer))) return prefer;
        if (Passable(ba, pos.DownCopy())) return BlockFacing.DOWN;
        foreach (BlockFacing f in BlockFacing.HORIZONTALS)
            if (Passable(ba, pos.AddCopy(f))) return f;
        return null;
    }

    private static List<BlockPos> Cells(IBlockAccessor ba, BlockPos source, BlockFacing dir)
    {
        var cells = new List<BlockPos>();
        var seen = new HashSet<long>();
        void Add(BlockPos c)
        {
            if (Passable(ba, c) && seen.Add(Key(c))) cells.Add(c.Copy());
        }
        BlockPos at = source.Copy();
        int reach = dir == BlockFacing.DOWN ? 8 : SteamLength;
        for (int i = 0; i < reach; i++)
        {
            at.Add(dir);
            if (!Passable(ba, at)) break;
            Add(at);
            if (dir == BlockFacing.DOWN)
            {
                // Down from a pipe overhead it spreads a block each way as it falls (three by three)
                for (int dx = -1; dx <= 1; dx++)
                    for (int dz = -1; dz <= 1; dz++)
                        if (dx != 0 || dz != 0) Add(at.AddCopy(dx, 0, dz));
            }
            else
            {
                Add(at.UpCopy());
                Add(at.DownCopy());
            }
        }
        return cells;
    }

    private void TickJets(long now)
    {
        if (jets.Count == 0) return;
        bool changed = false;
        for (int i = jets.Count - 1; i >= 0; i--)
        {
            Jet j = jets[i];
            if (now >= j.EndMs)
            {
                Entity near = j.Hurt.Count > 0 ? null : sapi.World.GetNearestEntity(Centre(j.Source), 6, 6, e => e is EntityAgent);
                sapi.Logger.Notification("[backrooms] props: the steam from {0} {1} {2} stops; hurt {3}", j.Source.X, j.Source.Y, j.Source.Z,
                    j.Hurt.Count > 0 ? string.Join(", ", j.Hurt.Select(h => h.Key + " " + h.Value.ToString("0.#") + " HP"))
                    : near == null ? "nothing" : string.Format("nothing (nearest {0} at {1:0.0} {2:0.0} {3:0.0})", near.Code.Path, near.Pos.X, near.Pos.Y, near.Pos.Z));
                jets.RemoveAt(i);
                changed = true;
                continue;
            }
            if (now < j.BlowMs) continue;
            if (!j.Started)
            {
                j.Started = true;
                changed = true;
                int[] xyz = { j.Source.X, j.Source.Y, j.Source.Z };
                SendFx(new PropFxPacket { Kind = PropFxPacket.Steam, Xyz = xyz, DurationMs = (int)(j.EndMs - now), Dir = j.Dir.Index, Length = Math.Max(2, Reach(j)) }, Centre(j.Source));
            }
            if (now >= j.NextSoundMs)
            {
                j.NextSoundMs += 1000;
                Play("backrooms:sounds/effect/props/steamblast", j.Source, 48);
                director?.RaiseNoise(Centre(j.Source), SteamLoudness, "steam", j.Who < 0 ? null : sapi.World.GetEntityById(j.Who));
            }
            if (now >= j.NextHurtMs)
            {
                j.NextHurtMs += 500;
                Scald(j);
            }
        }
        if (changed) JetCells = jets.Any(j => j.Started) ? new HashSet<long>(jets.Where(j => j.Started).SelectMany(j => j.Cells).Select(Key)) : EmptyCells;
    }

    private static int Reach(Jet j)
    {
        int n = 0;
        foreach (BlockPos c in j.Cells)
            n = Math.Max(n, Math.Abs(c.X - j.Source.X) + Math.Abs(c.Y - j.Source.Y) + Math.Abs(c.Z - j.Source.Z));
        return n;
    }

    /// <summary>Hurts everything whose body is in the jet.</summary>
    private void Scald(Jet j)
    {
        if (j.Cells.Count == 0) return;
        var cells = new HashSet<long>(j.Cells.Select(Key));
        Vec3d mid = Centre(j.Source);
        var p = new BlockPos(j.Source.dimension);
        foreach (Entity e in sapi.World.GetEntitiesAround(mid, 10, 10, e => e is EntityAgent { Alive: true }))
        {
            // Its feet or its middle in a cell of the jet
            bool inJet = false;
            foreach (double h in new[] { 0.1, (e.SelectionBox?.Y2 ?? 1.6) * 0.5, (e.SelectionBox?.Y2 ?? 1.6) * 0.9 })
            {
                p.Set((int)Math.Floor(e.Pos.X), (int)Math.Floor(e.Pos.Y + h), (int)Math.Floor(e.Pos.Z));
                if (cells.Contains(Key(p))) { inJet = true; break; }
            }
            if (!inJet) continue;
            var source = new DamageSource { Source = EnumDamageSource.Block, SourceBlock = sapi.World.BlockAccessor.GetBlock(j.Valve), SourcePos = mid, Type = EnumDamageType.Heat, IgnoreInvFrames = true };
            if (!e.ReceiveDamage(source, SteamDamage)) continue;
            string who = e.Code.Path + "#" + e.EntityId;
            j.Hurt[who] = j.Hurt.GetValueOrDefault(who) + SteamDamage;
        }
    }

    // ================= The pathfinder keeps out of a jet =================

    private const string HarmonyId = "backroomsss.steampaths";
    private static readonly object patchLock = new();
    private static int patchUsers;
    private bool patched;

    private void StartSteamPathing(ICoreServerAPI api)
    {
        lock (patchLock)
        {
            patched = true;
            if (patchUsers++ > 0) return;
            try
            {
                var harmony = new Harmony(HarmonyId);
                harmony.UnpatchAll(HarmonyId);
                harmony.Patch(AccessTools.Method(typeof(Block), nameof(Block.GetTraversalCost), new[] { typeof(BlockPos), typeof(EnumAICreatureType) }),
                    postfix: new HarmonyMethod(typeof(PropSystem), nameof(TraversalCostPostfix)));
            }
            catch (Exception e)
            {
                api.Logger.Warning("[backrooms] props: the pathfinder hook for steam jets could not be applied ({0}); creatures will walk into a jet", e.Message);
            }
        }
    }

    private void StopSteamPathing()
    {
        if (!patched) return;
        patched = false;
        lock (patchLock)
            if (--patchUsers == 0) new Harmony(HarmonyId).UnpatchAll(HarmonyId);
    }

    private static void TraversalCostPostfix(BlockPos pos, ref float __result)
    {
        HashSet<long> cells = JetCells;
        if (cells.Count == 0 || pos == null || __result > 10000f) return;
        if (cells.Contains(Key(pos))) __result = 20000f;
    }
}
