using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Needs.Water;

/// <summary>What drinking a body of water does (docs/design/needs/README.md section 3).</summary>
public enum WaterKind
{
    /// <summary>+600 hydration.</summary>
    Clean,
    /// <summary>+300, a stability hit and a chance of gut rot. The default for any water nobody has vouched for.</summary>
    Tainted,
    /// <summary>-300: the sea.</summary>
    Salt,
    /// <summary>Boiling water: 2 damage and nothing else.</summary>
    Scalding,
}

/// <summary>Which class a block of water belongs to, by the block and by the level it lies in.</summary>
public static class WaterClass
{
    /// <summary>Hydration for one litre drunk from the world, by class.</summary>
    public const float CleanHydration = 600f, TaintedHydration = 300f, SaltHydration = -300f;

    /// <summary>The stability a mouthful of tainted water costs, and the odds (in a quarter) that it brings gut rot for ten game hours.</summary>
    public const double TaintedStability = -0.05, SickChance = 0.25, SickHours = 10;

    /// <summary>How near a town fountain's rim or spout (blocks, sideways and up or down) water must lie to count as its basin.</summary>
    private const int FountainReach = 3;

    /// <summary>Whether the block is a liquid a person can drink from (water, salt water or boiling water).</summary>
    public static bool IsDrinkable(Block block) =>
        block != null && block.LiquidCode is "water" or "saltwater" or "boilingwater";

    /// <summary>The class of the water in the fluid layer at <paramref name="pos"/>. <paramref name="layout"/> may be null (a world that is not ours: plain water is clean).</summary>
    public static WaterKind At(IWorldAccessor world, WorldLayout layout, BlockPos pos)
    {
        Block fluid = world.BlockAccessor.GetBlock(pos, BlockLayersAccess.Fluid);
        if (fluid == null || fluid.Id == 0) return WaterKind.Tainted;
        return Of(world, layout, fluid, pos);
    }

    /// <summary>The class of a water block lying at <paramref name="pos"/>.</summary>
    public static WaterKind Of(IWorldAccessor world, WorldLayout layout, Block fluid, BlockPos pos)
    {
        switch (fluid.LiquidCode)
        {
            case "boilingwater": return WaterKind.Scalding;
            case "saltwater": return WaterKind.Salt;
        }
        if (layout == null) return WaterKind.Clean;
        int level = layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z));
        switch (level)
        {
            case 8: case 10: case WorldLayout.Poolrooms: case WorldLayout.Level974:
                return WaterKind.Clean;
            case 7: case WorldLayout.FunLevel:
                return WaterKind.Salt;
            case WorldLayout.Motion:
                return NearFountain(world, pos) ? WaterKind.Clean : WaterKind.Tainted;
            default:
                return WaterKind.Tainted;
        }
    }

    /// <summary>Level 94's town fountain: its basin is five by five tiles of rim round three by three of water and a spout, so the
    /// basin's water lies within a block or two of the rim. The flooded houses are far from any fountain.</summary>
    private static bool NearFountain(IWorldAccessor world, BlockPos pos)
    {
        BlockPos at = pos.Copy();
        for (int dx = -FountainReach; dx <= FountainReach; dx++)
            for (int dz = -FountainReach; dz <= FountainReach; dz++)
                for (int dy = -FountainReach; dy <= FountainReach; dy++)
                {
                    at.Set(pos.X + dx, pos.Y + dy, pos.Z + dz);
                    string path = world.BlockAccessor.GetBlock(at, BlockLayersAccess.SolidBlocks)?.Code?.Path;
                    if (path != null && path.StartsWith("almondfountain-")) return true;
                }
        return false;
    }

    /// <summary>The code of the bottle a clean/murky/salt fill gives.</summary>
    public static string BottleCode(WaterKind kind) => kind switch
    {
        WaterKind.Clean or WaterKind.Scalding => "backrooms:bottledwater-clean",
        WaterKind.Salt => "backrooms:bottledwater-salt",
        _ => "backrooms:bottledwater-murky",
    };
}
