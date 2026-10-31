using System;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// Keeps the game's pathfinder from planning a way over tall furniture. Its step test lifts a creature's box by the step height
/// plus the block's height above one, finds that clear, and calls the cell passable: a creature that steps 1.1251 is planned
/// over a 1.5 high cubicle partition, a bookshelf or a server rack, then walks into it and stands there. A postfix on
/// <c>Block.GetTraversalCost</c> (the cost the A* asks of a cell; above 10000 is impassable) makes such blocks of ours impassable.
/// Which block counts is worked out once per block id: a collision box standing on (or near) the floor (it starts at 0.4 or lower)
/// and reaching above <see cref="TallAbove"/>. Left alone: doors and gates (the AI opens them), climbables (ladders), stairs, and
/// anything with no fixed collision box (the ones a block class or behaviour works out).
/// </summary>
public class TallBlockPathing : ModSystem
{
    private const string HarmonyId = "backroomsss.tallpaths";
    private static readonly object patchLock = new();
    private static int patchUsers;
    private bool patched;

    /// <summary>A box reaching above this (blocks) is taller than a step.</summary>
    public const float TallAbove = 1.05f;
    /// <summary>The cost handed back (the game treats above 10000 as impassable).</summary>
    public const float Impassable = 20000f;

    // 0 not looked at, 1 passable as ever, 2 tall. (Written once per id, from any thread: both writers agree)
    private static volatile byte[] verdicts;

    public override bool ShouldLoad(EnumAppSide forSide) => forSide == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        // (A dev switch, to measure the pathfinder without the hook: BACKROOMS_NO_TALLPATHS=1)
        if (Environment.GetEnvironmentVariable("BACKROOMS_NO_TALLPATHS") == "1") return;
        lock (patchLock)
        {
            patched = true;
            if (patchUsers++ == 0)
            {
                try
                {
                    var harmony = new Harmony(HarmonyId);
                    harmony.UnpatchAll(HarmonyId);
                    harmony.Patch(AccessTools.Method(typeof(Block), nameof(Block.GetTraversalCost), new[] { typeof(BlockPos), typeof(EnumAICreatureType) }),
                        postfix: new HarmonyMethod(typeof(TallBlockPathing), nameof(TraversalCostPostfix)));
                }
                catch (Exception e)
                {
                    api.Logger.Warning("[backrooms] tall blocks: the pathfinder hook could not be applied ({0}); creatures that step 1.1251 may plan a way over tall furniture and stand against it", e.Message);
                }
            }
        }
        // (Blocks are all registered by the time the game runs)
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            verdicts = new byte[api.World.Blocks.Count + 64];
            int tall = 0;
            foreach (Block block in api.World.Blocks)
                if (block.Id > 0 && IsTall(block)) tall++;
            api.Logger.Notification("[backrooms] tall blocks: {0} of ours are impassable to the pathfinder", tall);
        });
    }

    public override void Dispose()
    {
        verdicts = null;
        if (!patched) return;
        patched = false;
        lock (patchLock)
            if (--patchUsers == 0) new Harmony(HarmonyId).UnpatchAll(HarmonyId);
    }

    private static void TraversalCostPostfix(Block __instance, ref float __result)
    {
        if (__result > 10000f) return;
        byte[] table = verdicts;
        int id = __instance.Id;
        if (table == null || id <= 0 || id >= table.Length) return;
        byte verdict = table[id];
        if (verdict == 0) table[id] = verdict = (byte)(IsTall(__instance) ? 2 : 1);
        if (verdict == 2) __result = Impassable;
    }

    /// <summary>Whether a block of ours has a fixed collision box on the floor that is taller than a step, and is not meant to be passed.</summary>
    public static bool IsTall(Block block)
    {
        if (block.Code?.Domain != "backrooms") return false;
        if (block is BlockBaseDoor || block.Climbable) return false;
        string path = block.Code.Path;
        if (path.Contains("door") || path.Contains("gate") || path.Contains("stair") || path.Contains("ladder")) return false;
        Cuboidf[] boxes = block.CollisionBoxes;
        if (boxes == null) return false;
        foreach (Cuboidf box in boxes)
            if (box.Y1 <= 0.4f && box.Y2 > TallAbove) return true;
        return false;
    }
}
