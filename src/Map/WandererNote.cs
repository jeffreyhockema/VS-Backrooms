using System.Linq;
using System.Text;
using Backrooms.Notes;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
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
/// Fun's); the folded note (wanderernote-folded) has none and is the rare kind. A note is kept when read and remembers
/// who has read it (<see cref="ReadersKey"/>, their player UIDs), so it can be handed on: one paper gives each player
/// one read. A fresh note carries no attribute and stacks as before; read notes stack with those read by the same
/// players, and are named "(read)" to whoever has read them.
/// </summary>
public class ItemWandererNote : Item
{
    /// <summary>The stack attribute that holds the UIDs of the players who have read the note (absent until someone has).</summary>
    public const string ReadersKey = "readers";

    /// <summary>The paper: door, way, cache, refuge, altered, or folded.</summary>
    public string Kind => Variant["kind"] ?? (Code.Path.EndsWith("folded", System.StringComparison.Ordinal) ? "folded" : "door");

    /// <summary>Who has read a note (empty for a fresh one).</summary>
    public static string[] ReadersOf(ItemStack stack) => (stack?.Attributes?[ReadersKey] as StringArrayAttribute)?.value ?? System.Array.Empty<string>();

    public static bool ReadBy(ItemStack stack, string uid) => uid != null && ReadersOf(stack).Contains(uid);

    /// <summary>Whether anyone has read it (a fresh note stacks with fresh ones; a read one is a keepsake to its readers).</summary>
    public static bool IsRead(ItemStack stack) => ReadersOf(stack).Length > 0;

    public static void MarkRead(ItemStack stack, string uid)
    {
        if (ReadBy(stack, uid)) return;
        stack.Attributes[ReadersKey] = new StringArrayAttribute(ReadersOf(stack).Concat(new[] { uid }).ToArray());
    }

    /// <summary>Forgets a reader (a directions note that told them nothing: they may read it elsewhere); fresh again if no one is left.</summary>
    public static void Unread(ItemStack stack, string uid)
    {
        string[] left = ReadersOf(stack).Where(r => r != uid).ToArray();
        if (left.Length == 0) stack.Attributes.RemoveAttribute(ReadersKey);
        else stack.Attributes[ReadersKey] = new StringArrayAttribute(left);
    }

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
        api.ModLoader.GetModSystem<NoteSystem>()?.ReadHeld(player, slot);
    }

    public override string GetHeldItemName(ItemStack itemStack)
    {
        string name = base.GetHeldItemName(itemStack);
        // (To the player looking at it: a note someone else has read is still fresh to them)
        return ReadBy(itemStack, (api as ICoreClientAPI)?.World?.Player?.PlayerUID) ? Lang.Get("backrooms:note-name-read", name) : name;
    }

    public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
        string[] readers = ReadersOf(inSlot.Itemstack);
        if (readers.Length == 0) return;
        string uid = (world.Api as ICoreClientAPI)?.World?.Player?.PlayerUID;
        bool mine = uid != null && readers.Contains(uid);
        int others = readers.Length - (mine ? 1 : 0);
        if (mine) dsc.AppendLine(Lang.Get("backrooms:note-info-read"));
        if (others > 0) dsc.AppendLine(Lang.Get(others == 1 ? "backrooms:note-info-read-other" : "backrooms:note-info-read-others", others));
    }

    public override WorldInteraction[] GetHeldInteractionHelp(ItemSlot inSlot) => new[]
    {
        new WorldInteraction { ActionLangCode = "backrooms:heldhelp-readnote", MouseButton = EnumMouseButton.Right },
    }.Append(base.GetHeldInteractionHelp(inSlot));
}
