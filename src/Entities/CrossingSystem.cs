using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// The fourth voice of the climb (progression revision, decision 23): when a player's level changes to one of a higher
/// survival class (<see cref="WorldLayout.SurvivalClass"/>), and the new class is 3 or more, a line in the chat says what the
/// place is like (lang keys <c>crossing-class3</c> to <c>-class5</c>) and what their armour will do about it
/// (<c>crossing-armour-none</c>, <c>-light</c>, <c>-metal</c>, chosen from the best piece they wear). Once per level per
/// player per session, so walking back and forth over a gate does not nag.
/// </summary>
public class CrossingSystem : ModSystem
{
    private ICoreServerAPI sapi;
    private WorldLayout layout;

    /// <summary>Per player (by uid): the level they were in at the last look, and the levels already spoken of.</summary>
    private readonly Dictionary<string, int> lastLevel = new();
    private readonly Dictionary<string, HashSet<int>> told = new();

    /// <summary>What a piece of armour is made of, by its code, for "metal" (vanilla's tiers do not follow the material: linen is tier 2, copper lamellar tier 1).</summary>
    private static readonly string[] Metals = { "copper", "bronze", "iron", "steel", "silver", "gold", "brass", "lead", "chain", "plate", "lamellar", "scale", "brigandine" };

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            api.Event.RegisterGameTickListener(OnTick, e => api.Logger.Error("[backrooms] crossing: {0}", e), 1000, 700);
        });
        api.Event.PlayerDisconnect += player =>
        {
            lastLevel.Remove(player.PlayerUID);
            told.Remove(player.PlayerUID);
        };
    }

    private void OnTick(float dt)
    {
        foreach (IServerPlayer player in sapi.World.AllOnlinePlayers.OfType<IServerPlayer>())
        {
            if (player.ConnectionState != EnumClientState.Playing || player.Entity is not { Alive: true } entity) continue;
            if (player.WorldData.CurrentGameMode != EnumGameMode.Survival) continue;
            int level = layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(entity.Pos.X)), WorldLayout.MacroOf((int)Math.Floor(entity.Pos.Z)));
            if (!lastLevel.TryGetValue(player.PlayerUID, out int before))
            {
                // (First look this session: where they stand is where they were; nothing to say about it)
                lastLevel[player.PlayerUID] = level;
                continue;
            }
            if (level == before) continue;
            lastLevel[player.PlayerUID] = level;
            if (Speaks(before, level) && Tell(player, level)) SayCrossing(player, level);
        }
    }

    /// <summary>Whether a change of level is a crossing into a higher survival class of 3 or more.</summary>
    public static bool Speaks(int from, int to)
    {
        int now = WorldLayout.SurvivalClass(to);
        // (Level 94 is deliberately abundant and gentle by day: no line for it, as with the scarcity)
        return now >= 3 && now > WorldLayout.SurvivalClass(from) && to != WorldLayout.Motion;
    }

    /// <summary>True the first time this player is told about this level.</summary>
    private bool Tell(IServerPlayer player, int level)
    {
        if (!told.TryGetValue(player.PlayerUID, out HashSet<int> levels)) told[player.PlayerUID] = levels = new HashSet<int>();
        return levels.Add(level);
    }

    private static void SayCrossing(IServerPlayer player, int level)
    {
        int cls = WorldLayout.SurvivalClass(level);
        string number = WorldLayout.DisplayNumber(level);
        string line = Say.T(player, "backrooms:crossing-class" + cls, number) + " " + Say.T(player, "backrooms:crossing-armour-" + ArmourTier(player));
        player.SendMessage(GlobalConstants.GeneralChatGroup, line, EnumChatType.Notification);
    }

    /// <summary>What the player wears, by its best piece: <c>none</c>, <c>light</c> (leather, pleather) or <c>metal</c>.</summary>
    public static string ArmourTier(IServerPlayer player)
    {
        bool any = false, metal = false;
        if (player.InventoryManager.GetOwnInventory(GlobalConstants.characterInvClassName) is { } worn)
            foreach (ItemSlot slot in worn)
            {
                if (slot?.Itemstack?.Collectible is not { } thing) continue;
                ProtectionModifiers p = thing.GetCollectibleInterface<IWearableStatsSupplier>()?.GetProtectionModifiers(slot);
                if (p == null || p.FlatDamageReduction <= 0 && p.RelativeProtection <= 0) continue;
                any = true;
                string path = thing.Code.Path;
                if (Metals.Any(m => path.Contains(m))) metal = true;
            }
        return !any ? "none" : metal ? "metal" : "light";
    }
}
