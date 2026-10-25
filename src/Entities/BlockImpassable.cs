using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>
/// A block taller than anything a creature can step onto, that the game's pathfinder would still plan a way over. Its
/// step test lifts the creature's box by the step height plus the block's height above one (a 1.5 high partition: 1.6251 up
/// for a Duller stepping 1.1251), finds that clear, and calls the cell passable; the creature then walks into the block
/// and stands there. Costing the cell as impassable (above 10000, as deep water is) sends the search round instead.
/// </summary>
public class BlockImpassable : Block
{
    private const float Impassable = 20000f;

    public override float GetTraversalCost(BlockPos pos, EnumAICreatureType creatureType) => Impassable;
}
