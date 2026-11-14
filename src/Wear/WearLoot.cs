using System.Collections.Generic;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;

namespace Backrooms.Wear;

/// <summary>
/// Where the item pass's clothes turn up (tools/gen_items_wear.py): extra drops added to these blocks when the assets
/// finalise, after the breakdown rules (Salvage/Breakdown.cs, ProtectionSystem at 1.2) have settled what each block is, so a
/// block that breaks down (a Level 14 locker) still breaks down and gives a coat now and then besides. Drops are rolled when
/// the block breaks, so every world gets them, old ones too. Each figure is the chance of one (vanilla rounds a drop's
/// average at random): rare, a few in a house at most.
/// </summary>
public class WearLootSystem : ModSystem
{
    private const string TeeGrey = "clothes-upperbody-tshirt-grey", TeeRed = "clothes-upperbody-tshirt-red", Jeans = "clothes-lowerbody-jeans",
        Hoodie = "clothes-upperbodyover-hoodie", Jacket = "clothes-upperbodyover-workjacket", Sneakers = "clothes-foot-sneakers",
        Boots = "clothes-foot-workboots", Cap = "clothes-head-baseballcap", LabCoat = "clothes-upperbodyover-labcoat",
        Suit = "clothes-upperbodyover-hazmatsuit", Hood = "clothes-head-hazmathood";

    /// <summary>A block (by its code without the variants, and optionally one variant) and what it may hold.</summary>
    private sealed record Loot(string Type, string Variant, string Value, (string Code, float Chance)[] Drops);

    private static (string, float)[] D(params (string, float)[] drops) => drops;

    private static List<Loot> Build() => new()
    {
        // Level 9's houses: a chest of drawers in the bedrooms
        new("dresser", null, null, D((TeeGrey, 0.07f), (TeeRed, 0.06f), (Jeans, 0.08f), (Hoodie, 0.05f), (Sneakers, 0.04f), (Boots, 0.03f), (Cap, 0.04f))),
        // The hotel's wardrobes (Level 5) and the city's flats
        new("wardrobe", null, null, D((TeeGrey, 0.05f), (TeeRed, 0.04f), (Jeans, 0.06f), (Hoodie, 0.03f), (Jacket, 0.04f), (Sneakers, 0.03f), (Boots, 0.03f), (Cap, 0.02f))),
        // The city's shops
        new("clothesrack", null, null, D((TeeGrey, 0.06f), (TeeRed, 0.06f), (Jeans, 0.07f), (Hoodie, 0.05f), (Jacket, 0.05f), (Cap, 0.04f))),
        // Suitcases (the hotel's rooms, Level 36's halls) and lost luggage on Level 36's carousels
        new("suitcase", null, null, D((TeeGrey, 0.07f), (TeeRed, 0.05f), (Jeans, 0.05f), (Hoodie, 0.03f), (Sneakers, 0.04f), (Cap, 0.03f))),
        new("l36-luggage", "kind", "garment", D((Jacket, 0.08f), (LabCoat, 0.04f), (TeeGrey, 0.04f))),
        new("l36-luggage", null, null, D((TeeGrey, 0.04f), (TeeRed, 0.03f), (Jeans, 0.04f), (Hoodie, 0.03f), (Sneakers, 0.03f), (Cap, 0.02f))),
        // What the lost left: their packs
        new("backpack", null, null, D((TeeGrey, 0.03f), (Hoodie, 0.03f), (Cap, 0.03f), (Sneakers, 0.02f))),
        // Level 14's staff lockers; the T.14.R.G.'s stockpile; Level 15's lockers; Level 120's shelving; Level 2's
        // maintenance cabinets
        new("l14-locker", "part", "lower", D((LabCoat, 0.12f), (TeeGrey, 0.04f), (Sneakers, 0.03f), (Suit, 0.02f), (Hood, 0.02f))),
        new("l14-crate", null, null, D((Suit, 0.04f), (Hood, 0.04f))),
        new("l15-locker", "part", "lower", D((LabCoat, 0.08f), (Boots, 0.03f), (Suit, 0.02f), (Hood, 0.02f))),
        new("l120-shelf", "part", "lower", D((LabCoat, 0.03f), (Suit, 0.015f), (Hood, 0.015f))),
        new("machinecabinet", null, null, D((Suit, 0.015f), (Hood, 0.015f), (Boots, 0.02f), (Jacket, 0.02f))),
    };

    // After ProtectionSystem (1.2), whose Breakdown.Apply decides from the block types' own drops what each block is
    public override double ExecuteOrder() => 1.3;

    public override void AssetsFinalize(ICoreAPI api)
    {
        List<Loot> table = Build();
        int given = 0;
        foreach (Block block in api.World.Blocks)
        {
            if (block?.Code == null || block.Code.Domain != "backrooms") continue;
            // (The first matching entry: a variant entry before the plain one for the same block)
            Loot loot = table.FirstOrDefault(l => TypeOf(block) == l.Type && (l.Variant == null || block.Variant[l.Variant] == l.Value));
            if (loot == null) continue;
            var drops = new List<BlockDropItemStack>(block.Drops ?? System.Array.Empty<BlockDropItemStack>());
            foreach ((string code, float chance) in loot.Drops)
            {
                var drop = new BlockDropItemStack { Type = EnumItemClass.Item, Code = new AssetLocation("backrooms", code), Quantity = NatFloat.createUniform(chance, 0) };
                if (drop.Resolve(api.World, "backrooms wear loot", block.Code)) drops.Add(drop);
            }
            block.Drops = drops.ToArray();
            given++;
        }
        if (api.Side == EnumAppSide.Server) api.Logger.Notification("[backrooms] Wear loot: {0} block types may hold clothes", given);
    }

    /// <summary>The block's code without its variant values (as Breakdown's TypeOf).</summary>
    private static string TypeOf(Block block)
    {
        string path = block.Code.Path;
        if (block.Variant == null || block.Variant.Count == 0) return path;
        string suffix = "-" + string.Join("-", block.Variant.Values);
        return path.Length > suffix.Length && path.EndsWith(suffix, System.StringComparison.Ordinal) ? path[..^suffix.Length] : path;
    }
}
