using System;
using System.Collections.Generic;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Entities;

/// <summary>
/// What the deeper levels pay for their danger (see <see cref="Danger"/>):
/// <list type="bullet">
/// <item>A bounty on what you kill: rusty gears, the wanderers' currency, more of them the deeper the level and the
/// worse the thing. A Skin-Stealer also drops what it took from the last person it wore, and a Wretch what it carried
/// when it was a wanderer. Nothing for Facelings.</item>
/// <item>Fuller caches: a box, crate, cupboard or fridge broken open in a deep level may give its contents twice, and
/// may hold something extra besides, better the deeper you are (metal, medicine, rusty gears, very rarely a
/// temporal gear). In Level 7, deeper means down the sea too: a cache on the bottom of the midnight zone pays as one
/// in the city does.</item>
/// </list>
/// </summary>
public class Rewards : ModSystem
{
    private const string Gear = "game:gear-rusty";

    /// <summary>Rusty gears a kill is worth, as (at no danger, extra per unit of danger), by entity code path.</summary>
    private static readonly Dictionary<string, (double Base, double PerDanger)> Bounties = new()
    {
        ["hound"] = (0.25, 1.0),
        ["deathrat"] = (0.05, 0.25),
        ["skinstealer"] = (1.0, 2.5),
        ["duller"] = (0.5, 2.0),
        ["clump"] = (0.5, 2.0),
        ["deathmoth-female"] = (0.05, 0.2),
        ["wretch"] = (0.3, 0.8),
        ["bacteria"] = (1.0, 2.0),
        ["neighborhoodwatch"] = (1.0, 2.5),
        ["partygoer"] = (1.0, 2.5),
        ["partygoer-intern"] = (1.0, 2.5),
    };

    /// <summary>What a Skin-Stealer was carrying: the belongings of someone it wore.</summary>
    private static readonly string[] Belongings =
    {
        "game:bandage-clean", "backrooms:almondwater", "game:candle", "backrooms:crackers", "game:flint", "backrooms:cannedbeans",
        "game:flaxtwine", "game:knife-generic-flint", "backrooms:chalk",
    };

    /// <summary>The extra a deep cache may hold, by how deep: (code, min, max, chance weight).</summary>
    private static readonly (string Code, int Min, int Max, double Weight)[][] Bonus =
    {
        // Levels 1 to 3
        new[] { ("game:bandage-clean", 1, 1, 1.0), ("game:candle", 1, 2, 1.0), ("backrooms:crackers", 1, 2, 1.0), ("game:flaxtwine", 1, 3, 0.8), (Gear, 1, 1, 0.6) },
        // Levels 4 to 6
        new[] { (Gear, 1, 2, 1.2), ("game:metalbit-copper", 2, 4, 1.0), ("game:poultice-linen-horsetail", 1, 1, 0.8), ("backrooms:almondwater", 1, 2, 1.0), ("backrooms:firesalt", 1, 2, 0.6) },
        // Level 7 down
        new[] { (Gear, 2, 3, 1.2), ("game:metalbit-tinbronze", 2, 4, 1.0), ("game:bandage-clean", 2, 3, 0.8), ("game:metalbit-iron", 1, 3, 0.5), ("game:gear-temporal", 1, 1, 0.06) },
    };

    private static ICoreServerAPI sapi;
    private MenaceSystem director;
    private readonly HashSet<int> caches = new();
    /// <summary>The shared floor's height: Level 7's water surface, for how deep a cache on its seabed lay.</summary>
    private int floorY = int.MinValue;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override double ExecuteOrder() => 1.3;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            director = api.ModLoader.GetModSystem<MenaceSystem>();
            floorY = BackroomsWorld.CreateGeometry(api.World).FloorY;
            foreach (Block block in api.World.Blocks)
            {
                if (block?.Code?.Domain == "backrooms" && block.Drops != null && Array.Exists(block.Drops, IsLoot)) caches.Add(block.BlockId);
            }
            api.Logger.Notification("[backrooms] {0} kinds of cache pay more in deeper levels", caches.Count);
            api.Event.DidBreakBlock += OnBrokeBlock;
        });
    }

    /// <summary>Whether a drop is something worth finding (food, medicine, metal, gears), as opposed to the material the thing was made of.</summary>
    private static bool IsLoot(BlockDropItemStack drop)
    {
        AssetLocation code = drop?.Code;
        if (code == null) return false;
        string p = code.Path;
        if (code.Domain == "backrooms")
            return p is "almondwater" or "crackers" or "cannedbeans" or "chips" or "candybar" or "soda" or "waterbottle" or "cashewwater" or "firesalt" or "seedpacket";
        return p.StartsWith("gear-") || p.StartsWith("metalbit-") || p.StartsWith("bandage") || p.StartsWith("poultice") || p.StartsWith("fruit-")
            || p.StartsWith("cheese-") || p.StartsWith("candle") || p.StartsWith("seeds-");
    }

    private void OnBrokeBlock(IServerPlayer byPlayer, int oldblockId, BlockSelection blockSel)
    {
        if (byPlayer?.WorldData.CurrentGameMode != EnumGameMode.Survival || !caches.Contains(oldblockId) || director?.Layout == null) return;
        BlockPos pos = blockSel.Position;
        int level = director.Layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z));
        double d = Danger.OfLevel(level);
        if (d <= 0) return;
        // Level 7's caches pay more the deeper they lie: on the bottom of the midnight zone, as much as the city's
        if (level == 7 && pos.Y < floorY) d = Math.Min(1, d + 0.3 * Math.Clamp((floorY - pos.Y) / (double)WorldLayout.AbyssDepth, 0, 1));
        Random rand = sapi.World.Rand;
        Vec3d at = pos.ToVec3d().Add(0.5, 0.5, 0.5);
        Block block = sapi.World.GetBlock(oldblockId);

        // Less picked over than it looks: its contents again
        if (rand.NextDouble() < 0.7 * d)
        {
            ItemStack[] again = block.GetDrops(sapi.World, pos, byPlayer);
            if (again != null) foreach (ItemStack stack in again) if (stack != null) sapi.World.SpawnItemEntity(stack, at);
        }
        // And something extra
        if (rand.NextDouble() < 0.15 + 0.35 * d)
        {
            var pool = Bonus[d < 0.4 ? 0 : d < 0.7 ? 1 : 2];
            var (code, min, max, _) = Pick(pool, rand);
            ItemStack stack = Make(code, min + rand.Next(max - min + 1));
            if (stack != null) sapi.World.SpawnItemEntity(stack, at);
        }
    }

    private static (string, int, int, double) Pick((string Code, int Min, int Max, double Weight)[] pool, Random rand)
    {
        double total = 0;
        foreach (var e in pool) total += e.Weight;
        double r = rand.NextDouble() * total;
        foreach (var e in pool)
        {
            r -= e.Weight;
            if (r <= 0) return e;
        }
        return pool[^1];
    }

    /// <summary>A stack of an item or block by code, or null if the game has no such thing.</summary>
    private static ItemStack Make(string code, int size)
    {
        var loc = new AssetLocation(code);
        if (sapi.World.GetItem(loc) is { } item) return new ItemStack(item, size);
        if (sapi.World.GetBlock(loc) is { } block && block.Id != 0) return new ItemStack(block, size);
        return null;
    }

    /// <summary>The bounty on something a player has killed: rusty gears by its kind and how deep it was, and a Skin-Stealer's belongings.</summary>
    public static void Bounty(Entity dead, EntityPlayer killer)
    {
        if (sapi == null || !Bounties.TryGetValue(dead.Code.Path, out var bounty)) return;
        // Level !'s horde is endless: killing one of it is worth nothing
        if (dead.Attributes.GetBool(Regions.RunSystem.HordeKey)) return;
        Random rand = dead.World.Rand;
        double d = Danger.Of(dead);
        double expected = bounty.Base + bounty.PerDanger * d;
        // An old Hound is worth twice as much
        if (dead.Code.Path == "hound" && dead.WatchedAttributes.GetInt("textureIndex") == 2) expected *= 2;
        int gears = (int)Math.Floor(expected) + (rand.NextDouble() < expected - Math.Floor(expected) ? 1 : 0);
        Vec3d at = dead.Pos.XYZ.Add(0, 0.4, 0);
        if (gears > 0 && Make(Gear, gears) is { } stack) dead.World.SpawnItemEntity(stack, at);
        // What it carried when it was a wanderer, or what it took from the last one it wore
        if (dead.Code.Path is "skinstealer" or "wretch")
        {
            int things = 1 + rand.Next(2);
            for (int i = 0; i < things; i++)
                if (Make(Belongings[rand.Next(Belongings.Length)], 1) is { } thing) dead.World.SpawnItemEntity(thing, at);
        }
        Strike.Log(dead, "bounty for {0}: {1} rusty gears (danger {2:0.00})", killer.Player?.PlayerName, gears, d);
    }
}
