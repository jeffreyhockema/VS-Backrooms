using System.Collections.Generic;
using Vintagestory.API.Common;

namespace Backrooms.Worldgen;

/// <summary>
/// Layout version 14: the food props of Levels 1 to 5 that others went through before the player (the tile's
/// <see cref="Tile.Looted"/>, WorldLayout.MarkPickedOver) are drawn as their stripped blocks: emptied metal shelving, an
/// open drum, flattened cardboard, a fridge with its door ajar, a bare cupboard and a bare pantry shelf. They give what the
/// prop gives but no food. Worlds made before version 14 never mark a prop, so nothing here changes them.
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>A food prop's block id to its stripped block's (read only once the constructor has filled it).</summary>
    private readonly Dictionary<int, int> strippedIds = new();

    private void InitStripped()
    {
        void Pair(string full, string bare)
        {
            Block a = api.World.GetBlock(new AssetLocation("backrooms", full)), b = api.World.GetBlock(new AssetLocation("backrooms", bare));
            if (a == null || b == null || a.BlockId == 0 || b.BlockId == 0)
            {
                api.Logger.Warning("[backrooms] Missing block {0} or {1}: that prop is never found stripped", full, bare);
                return;
            }
            strippedIds[a.BlockId] = b.BlockId;
        }
        foreach (string side in Sides)
        {
            Pair("metalshelf-" + side, "metalshelfbare-" + side);
            Pair("fridge-" + side, "fridgeajar-" + side);
            Pair("kitchencabinet-" + side, "kitchencabinetbare-" + side);
            Pair("pantryshelf-" + side, "pantryshelfbare-" + side);
            // (Layout version 16: the Basement's icebox, found with its door ajar like a fridge; no block of its own)
            Pair("icebox-" + side, "fridgeajar-" + side);
        }
        Pair("oildrum", "oildrumopen");
        Pair("cardboardboxes", "cardboardflat");
    }

    /// <summary>The block a tile of Levels 1 to 5 shows: its stripped prop if it was picked over (layout version 15 on), else <paramref name="block"/>.</summary>
    private int Stripped(in Tile t, int block) =>
        block != 0 && t.Looted && (t.Level is >= 1 and <= 5 && layout.Version >= 15 || t.Level is WorldLayout.Basement or WorldLayout.Level52 && layout.Version >= 16)
        && strippedIds.TryGetValue(block, out int bare) ? bare : block;

    /// <summary>A food prop's block as its stripped one when <paramref name="strip"/> (Level 52's upper storeys roll their own, layout version 16 on).</summary>
    private int StrippedIf(bool strip, int block) => strip && block != 0 && strippedIds.TryGetValue(block, out int bare) ? bare : block;
}
