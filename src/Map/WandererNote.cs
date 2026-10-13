using Backrooms.Notes;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Server;
using Vintagestory.API.Util;

namespace Backrooms.Map;

/// <summary>
/// Registers the wanderer's note. What a note says and marks is decided by <see cref="NoteSystem"/> when it is read
/// (docs/design/notes-plan.md): its kind is only the paper, and decides what it marks on the map.
/// </summary>
public class WayfindingSystem : ModSystem
{
    public override void Start(ICoreAPI api)
    {
        api.RegisterItemClass("BackroomsWandererNote", typeof(ItemWandererNote));
    }
}

/// <summary>
/// A wanderer's note: right-click to read it. Its kind is its variant (door, way, cache, refuge; altered for Level
/// Fun's); the folded note (wanderernote-folded) has none and is the rare kind.
/// </summary>
public class ItemWandererNote : Item
{
    /// <summary>The paper: door, way, cache, refuge, altered, or folded.</summary>
    public string Kind => Variant["kind"] ?? (Code.Path.EndsWith("folded") ? "folded" : "door");

    public override void OnHeldInteractStart(ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, bool firstEvent, ref EnumHandHandling handling)
    {
        if (blockSel != null && byEntity.Controls.ShiftKey)
        {
            // Shift + right-click on the floor sets the note down (its GroundStorable behaviour) instead of reading it
            base.OnHeldInteractStart(slot, byEntity, blockSel, entitySel, firstEvent, ref handling);
            if (handling != EnumHandHandling.NotHandled) return;
        }
        if (!firstEvent) return;
        handling = EnumHandHandling.PreventDefault;
        if (api.Side != EnumAppSide.Server || (byEntity as EntityPlayer)?.Player is not IServerPlayer player) return;
        if (api.ModLoader.GetModSystem<NoteSystem>()?.Read(player, Kind) != true) return;
        slot.TakeOut(1);
        slot.MarkDirty();
    }

    public override WorldInteraction[] GetHeldInteractionHelp(ItemSlot inSlot) => new[]
    {
        new WorldInteraction { ActionLangCode = "backrooms:heldhelp-readnote", MouseButton = EnumMouseButton.Right },
    }.Append(base.GetHeldInteractionHelp(inSlot));
}
