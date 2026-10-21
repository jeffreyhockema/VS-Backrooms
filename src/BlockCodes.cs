using System;
using System.Text;
using Vintagestory.API.Common;

namespace Backrooms;

/// <summary>
/// Block codes with one variant swapped. The game's own <c>CodeWithVariant</c> rebuilds a code from its first part, so
/// every code with a hyphen in its base name comes out wrong (fun-supplyshelf-south becomes fun-east, and the game's
/// typed container crashed the block-info HUD looking for it). This keeps the base and swaps the variant in place.
/// </summary>
public static class BlockCodes
{
    public static AssetLocation WithVariant(Block block, string key, string value)
    {
        var variant = block.Variant;
        if (variant == null || variant.Count == 0 || !variant.ContainsKey(key)) return block.Code;
        var suffix = new StringBuilder();
        foreach (var kv in variant) suffix.Append('-').Append(kv.Value);
        string path = block.Code.Path;
        string basePath = path.EndsWith(suffix.ToString(), StringComparison.Ordinal) ? path[..^suffix.Length] : path;
        var sb = new StringBuilder(basePath);
        foreach (var kv in variant) sb.Append('-').Append(kv.Key == key ? value : kv.Value);
        return new AssetLocation(block.Code.Domain, sb.ToString());
    }
}
