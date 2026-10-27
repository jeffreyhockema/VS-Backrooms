using Vintagestory.API.Common;
using Vintagestory.API.Server;
using Vintagestory.ServerMods;

namespace Backrooms.Worldgen;

/// <summary>
/// Gives a Backrooms world the game's tree generators. A sapling (<c>game:sapling-*</c>, grown from a planted tree seed)
/// turns into a tree by asking the world's tree generator registry for its <c>treeGen</c> (oak: <c>englishoak</c>). Vanilla
/// fills that registry from the files in <c>worldgen/treegen</c> when its vegetation generator starts up, and that
/// generator only starts for the "standard" and "superflat" world types, so in a Backrooms world the registry held the
/// fruit trees and the bamboo and nothing else, and every sapling stopped growing for good as it came due. The
/// vegetation itself is still not borrowed (<see cref="UndergroundSystem"/>): only the generators the saplings use.
/// </summary>
public class TreeGeneratorSystem : ModSystem
{
    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        // The same moment vanilla loads them for its own world types
        api.Event.InitWorldGenerator(() =>
        {
            new TreeGeneratorsUtil(api).LoadTreeGenerators();
        }, BackroomsWorld.WorldTypeCode);
    }
}
