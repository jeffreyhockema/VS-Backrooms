using System;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.API.Util;
using Vintagestory.GameContent;

namespace Backrooms.Reality;

/// <summary>
/// The anchor: you only ever wake up in Level 0. It is where you noclipped in, the one place the Backrooms still has a
/// loose thread back to you; the deeper levels do not remember you.
///
/// Vintage Story's own way of moving your spawn point still works, but only there: a temporal gear used in Level 0
/// makes that spot home, and anywhere else it will not take hold (and is not used up). A spawn point that somehow lies
/// outside Level 0 (an older world, a command) is cleared when the player joins or dies, so the next waking is at
/// the world's spawn.
/// </summary>
public class AnchorSystem : ModSystem
{
    private WorldLayout layout;

    /// <summary>Whether this is a Backrooms world (so the rule applies).</summary>
    public bool Active => layout != null;

    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsTemporalGear", typeof(ItemBackroomsTemporalGear));
    }

    public override void StartServerSide(ICoreServerAPI sapi)
    {
        sapi.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (sapi.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(sapi.World);
            sapi.Event.PlayerNowPlaying += KeepHomeInLevel0;
            sapi.Event.PlayerDeath += (player, _) => KeepHomeInLevel0(player);
        });
    }

    public override void StartClientSide(ICoreClientAPI capi)
    {
        capi.Event.LevelFinalize += () =>
        {
            if (BackroomsWorld.IsBackroomsClimate(capi.World.Config)) layout = BackroomsWorld.CreateLayout(capi.World);
        };
    }

    /// <summary>Whether a position lies in Level 0, where a spawn point can be set. Always true outside Backrooms worlds.</summary>
    public bool CanAnchorAt(Vec3d pos)
    {
        if (layout == null) return true;
        return layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(pos.X)), WorldLayout.MacroOf((int)Math.Floor(pos.Z))) == 0;
    }

    private void KeepHomeInLevel0(IServerPlayer player)
    {
        FuzzyEntityPos spawn = player.GetSpawnPosition(false);
        if (spawn == null || CanAnchorAt(new Vec3d(spawn.X, spawn.Y, spawn.Z))) return;
        player.ClearSpawnPosition();
        player.SendMessage(GlobalConstants.GeneralChatGroup, Lang.Get("backrooms:anchor-lost"), EnumChatType.Notification);
    }
}

/// <summary>The vanilla temporal gear, which will only set a spawn point in Level 0 of a Backrooms world.</summary>
public class ItemBackroomsTemporalGear : ItemTemporalGear
{
    private bool Refuses(EntityAgent byEntity) =>
        api.ModLoader.GetModSystem<AnchorSystem>() is { Active: true } anchor && !anchor.CanAnchorAt(byEntity.Pos.XYZ);

    public override void OnHeldInteractStart(ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, bool firstEvent, ref EnumHandHandling handHandling)
    {
        if (blockSel != null && Refuses(byEntity))
        {
            (api as ICoreClientAPI)?.TriggerIngameError(this, "backrooms-anchor", Lang.Get("backrooms:anchor-refused"));
            return;
        }
        base.OnHeldInteractStart(slot, byEntity, blockSel, entitySel, firstEvent, ref handHandling);
    }

    public override void OnHeldInteractStop(float secondsUsed, ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel)
    {
        // The server has the last word: a gear that would not take hold is not used up (someone who stepped out of
        // Level 0 while it turned). Its whirring still stops, as the vanilla stop would have seen to
        if (Refuses(byEntity))
        {
            if (byEntity.World.Side == EnumAppSide.Client && ObjectCacheUtil.TryGet<ILoadedSound>(api, "temporalGearSound") is { } sound)
            {
                sound.Stop();
                sound.Dispose();
            }
            return;
        }
        base.OnHeldInteractStop(secondsUsed, slot, byEntity, blockSel, entitySel);
    }
}
