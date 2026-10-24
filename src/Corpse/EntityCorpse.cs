using System;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Corpse;

/// <summary>
/// What a dead player leaves where they fell (<see cref="CorpseSystem"/>): the seraph, in their own skin and clothes,
/// lying on the floor, holding everything that would have dropped (<see cref="EntityBehaviorCorpseContents"/>). After a few
/// in-game days the body is bones (the entity "corpse-bones": the same class, a skeleton for a shape). It never despawns;
/// it goes when it is emptied.
/// </summary>
public class EntityCorpse : EntityAgent
{
    public const string OwnerKey = "corpseOwner";
    public const string OwnerNameKey = "corpseOwnerName";
    /// <summary>The calendar's TotalDays when the player died.</summary>
    public const string DiedKey = "corpseDiedDays";

    /// <summary>Set when the body is replaced by its bones, so that its going is not taken for its being emptied.</summary>
    public bool Replaced;

    private float accumulator;
    private long nextClientCheckMs;

    public bool Bones => Code?.Path == "corpse-bones";
    public string OwnerUid => WatchedAttributes.GetString(OwnerKey);
    public string OwnerName => WatchedAttributes.GetString(OwnerNameKey, "?");
    public double DiedDays => WatchedAttributes.GetDouble(DiedKey);

    public override bool ShouldReceiveDamage(DamageSource damageSource, float damage) => false;

    public override bool ReceiveDamage(DamageSource damageSource, float damage) => false;

    public override string GetName() => Lang.Get(Bones ? "backrooms:corpse-bones-name" : "backrooms:corpse-name", OwnerName);

    public override void OnEntitySpawn()
    {
        base.OnEntitySpawn();
        if (World.Side == EnumAppSide.Client) LieDown();
        else Api.ModLoader.GetModSystem<CorpseSystem>()?.Adopt(this);
    }

    public override void OnEntityLoaded()
    {
        base.OnEntityLoaded();
        if (World.Side == EnumAppSide.Client) LieDown();
        else Api.ModLoader.GetModSystem<CorpseSystem>()?.Adopt(this);
    }

    public override void OnEntityDespawn(EntityDespawnData despawn)
    {
        base.OnEntityDespawn(despawn);
        // (A chunk unloading, or the server stopping, only puts it away: it is gone when it is removed, or killed)
        if (World.Side == EnumAppSide.Server && !Replaced && despawn != null && despawn.Reason != EnumDespawnReason.Unload && despawn.Reason != EnumDespawnReason.Disconnect)
            Api.ModLoader.GetModSystem<CorpseSystem>()?.Forget(this);
    }

    public override void OnGameTick(float dt)
    {
        base.OnGameTick(dt);
        if (World.Side == EnumAppSide.Server)
        {
            accumulator += dt;
            if (accumulator < 5f) return;
            accumulator = 0;
            Api.ModLoader.GetModSystem<CorpseSystem>()?.Look(this);
        }
        else if (!Bones && World.ElapsedMilliseconds > nextClientCheckMs)
        {
            // (The pose is held by the animation; if the shape is rebuilt it is started again)
            nextClientCheckMs = World.ElapsedMilliseconds + 2000;
            if (!AnimManager.IsAnimationActive("die")) LieDown();
        }
    }

    /// <summary>On the client: the seraph's death animation, which holds its last frame. A body that is old is there at once.</summary>
    private void LieDown()
    {
        if (Bones || AnimManager == null) return;
        bool fresh = World.Calendar.TotalDays - DiedDays < 0.05;
        AnimManager.StartAnimation(new AnimationMetaData
        {
            Code = "die",
            Animation = "die",
            AnimationSpeed = fresh ? 1.5f : 80f,
            BlendMode = EnumAnimationBlendMode.Average,
            EaseInSpeed = 100f,
            EaseOutSpeed = 10f,
        }.Init());
    }
}

/// <summary>
/// The things a corpse holds, in a chest-like dialog (the game's creature-contents one, as for the Mechanical Helper).
/// Right-click opens it; sneak and right-click takes everything that fits. Empty, the body crumbles. Adapted from the
/// game's openablecontainer behaviour, which needs sneaking to open and has a fixed number of slots; the slots are kept in
/// the entity's watched attributes under <see cref="TreeKey"/> and saved with it.
/// </summary>
public class EntityBehaviorCorpseContents : EntityBehavior
{
    public const string TreeKey = "corpseInv";

    private InventoryGeneric inv;
    private GuiDialogCreatureContents dlg;
    private WorldInteraction[] interactions;
    private bool crumbling;

    public InventoryGeneric Inventory => inv;

    public EntityBehaviorCorpseContents(Entity entity) : base(entity) { }

    public override string PropertyName() => "backrooms-corpsecontents";

    public override void Initialize(EntityProperties properties, JsonObject typeAttributes)
    {
        base.Initialize(properties, typeAttributes);
        ITreeAttribute tree = entity.WatchedAttributes.GetTreeAttribute(TreeKey);
        inv = new InventoryGeneric(Math.Max(4, tree?.GetInt("qslots") ?? 4), "corpse-" + entity.EntityId, entity.Api, null);
        if (tree != null)
        {
            inv.FromTreeAttributes(tree);
            inv.AfterBlocksLoaded(entity.World);
        }
        inv.PutLocked = false;
        if (entity.World.Side == EnumAppSide.Server) inv.SlotModified += OnSlotModified;
    }

    /// <summary>Writes the slots into the attributes (so they are saved with the entity).</summary>
    private void OnSlotModified(int slotId)
    {
        Store();
        if (inv.Empty) Crumble();
    }

    public void Store()
    {
        var tree = new TreeAttribute();
        inv.ToTreeAttributes(tree);
        entity.WatchedAttributes[TreeKey] = tree;
        entity.WatchedAttributes.MarkPathDirty(TreeKey);
    }

    /// <summary>How many stacks are inside, and how many things (for the log and the dev commands).</summary>
    public (int Stacks, int Things) Count()
    {
        int stacks = 0, things = 0;
        if (inv != null)
            foreach (ItemSlot slot in inv)
                if (!slot.Empty) { stacks++; things += slot.StackSize; }
        return (stacks, things);
    }

    /// <summary>Server side: an emptied body crumbles away (a moment after, so the last stack is out of the dialog first).</summary>
    public void Crumble()
    {
        if (crumbling || entity.World.Side != EnumAppSide.Server) return;
        crumbling = true;
        entity.World.RegisterCallback(_ =>
        {
            crumbling = false;
            if (!entity.Alive || !inv.Empty) return;
            Vec3d at = entity.Pos.XYZ;
            entity.World.SpawnParticles(24, ColorUtil.ToRgba(255, 214, 205, 190), at.AddCopy(-0.6, 0.1, -0.6), at.AddCopy(0.6, 0.4, 0.6),
                new Vec3f(-0.4f, 0.2f, -0.4f), new Vec3f(0.4f, 0.8f, 0.4f), 1.4f, 0.02f, 0.6f, EnumParticleModel.Quad);
            entity.World.PlaySoundAt(new AssetLocation("game:sounds/block/gravel"), at.X, at.Y, at.Z, null, true, 24, 0.7f);
            entity.Die(EnumDespawnReason.Removed);
        }, 700);
    }

    public override void OnInteract(EntityAgent byEntity, ItemSlot itemslot, Vec3d hitPosition, EnumInteractMode mode, ref EnumHandling handled)
    {
        if (mode != EnumInteractMode.Interact || byEntity is not EntityPlayer self || inv == null) return;
        handled = EnumHandling.PreventDefault;
        bool client = entity.World.Side == EnumAppSide.Client;
        if (byEntity.Pos.SquareDistanceTo(entity.Pos) > (client ? 36 : 64)) return;
        IPlayer player = entity.World.PlayerByUid(self.PlayerUID);
        if (player == null) return;

        if (byEntity.Controls.ShiftKey)
        {
            if (!client && player is IServerPlayer server) TakeAll(server);
            return;
        }

        player.InventoryManager.OpenInventory(inv);
        if (client && dlg == null && entity.Api is ICoreClientAPI capi)
        {
            dlg = new GuiDialogCreatureContents(inv, entity, capi, "backrooms-corpse", Lang.Get("backrooms:corpse-title", entity is EntityCorpse corpse ? corpse.OwnerName : "?"));
            if (dlg.TryOpen()) capi.Network.SendPacketClient(inv.Open(player));
            dlg.OnClosed += () =>
            {
                dlg?.Dispose();
                dlg = null;
            };
        }
    }

    /// <summary>Everything that fits into the player's own inventory moves there, the way shift-clicking would; the rest stays.</summary>
    private void TakeAll(IServerPlayer player)
    {
        int before = Count().Stacks;
        foreach (ItemSlot slot in inv)
        {
            if (slot.Empty) continue;
            var op = new ItemStackMoveOperation(entity.World, EnumMouseButton.Left, 0, EnumMergePriority.AutoMerge, slot.StackSize);
            player.InventoryManager.TryTransferAway(slot, ref op, true, true);
            slot.MarkDirty();
        }
        int left = Count().Stacks;
        entity.Api.Logger.Notification("[backrooms] corpse #{0}: {1} took everything that fit ({2} of {3} stacks left)", entity.EntityId, player.PlayerName, left, before);
        player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, left == 0 ? "backrooms:corpse-took-all" : "backrooms:corpse-took-some", left), EnumChatType.Notification);
    }

    public override void OnReceivedClientPacket(IServerPlayer player, int packetid, byte[] data, ref EnumHandling handled)
    {
        if (inv == null) return;
        if (packetid < 1000)
        {
            inv.InvNetworkUtil.HandleClientPacket(player, packetid, data);
            handled = EnumHandling.PreventSubsequent;
        }
        else if (packetid == 1012)
        {
            player.InventoryManager.OpenInventory(inv);
        }
    }

    public override WorldInteraction[] GetInteractionHelp(IClientWorldAccessor world, EntitySelection es, IClientPlayer player, ref EnumHandling handled)
    {
        interactions ??= new[]
        {
            new WorldInteraction { ActionLangCode = "backrooms:corpse-help-search", MouseButton = EnumMouseButton.Right },
            new WorldInteraction { ActionLangCode = "backrooms:corpse-help-takeall", MouseButton = EnumMouseButton.Right, HotKeyCode = "shift" },
        };
        return interactions;
    }

    public override void OnEntityDespawn(EntityDespawnData despawn)
    {
        base.OnEntityDespawn(despawn);
        if (dlg != null)
        {
            dlg.TryClose();
            dlg.Dispose();
            dlg = null;
        }
    }
}
