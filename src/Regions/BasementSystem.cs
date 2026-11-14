using System;
using System.Collections.Generic;
using Backrooms.Corpse;
using Backrooms.Worldgen;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Regions;

/// <summary>
/// The Basement's rules on the server (experimental, kept as level 22; docs/design/experimental-levels/basement-plan.md):
/// <list type="bullet">
/// <item><b>Escherian stairwells</b> (Fandom: "brick stairwells … going up or down them will lead back to the same
/// floor"): stepping onto a stairwell's landing a turn above or below the door puts you back on the landing by the door,
/// <see cref="WorldLayout.BasementEscherRise"/> blocks down or up. The tower repeats every turn, so it looks the same.</item>
/// <item><b>The dead</b>: the bodies of the level (<see cref="WorldLayout.BasementBodies"/>) are laid down as corpses the
/// first time anyone comes near their cell, and never again (the cells done are kept in the save): old bones in the
/// Cellar, drowned bodies in the Flood's dead ends, and now and then the man the newspaper named. They hold a little
/// of what they had; emptied, they crumble, as every body does (<see cref="CorpseSystem"/>).</item>
/// <item><b>The smell</b> (Fandom: "the smell of the corpses … can suffocate one if it is inhaled for long enough"):
/// with two or more of the dead within four blocks, it builds; a warning at a quarter of a minute, then from three
/// quarters of a minute a little suffocation every few seconds until you get away. It eases twice as fast as it builds.
/// A hazmat hood's filter lets it build at a quarter of the pace (Wear/HazmatSystem.cs).</item>
/// <item><b>The cracked floor of Level 2</b>: the walked thresholds leave Level 2 alone, so whoever is there is looked at
/// here, and stepping onto the middle of one of the Basement's cracked patches drops them in as anywhere else
/// (ThresholdSystem.Basement.cs).</item>
/// </list>
/// The doors (<see cref="BlockBehaviorBasementDoor"/>) are registered here too.
/// </summary>
public class BasementSystem : ModSystem
{
    private const string SaveKey = "backrooms-basement-bodies";
    private const string DeadOwner = "backrooms-basement-dead";
    /// <summary>Seconds of breathing the dead before the warning, and before it chokes.</summary>
    private const float WarnAfter = 15, ChokeAfter = 45, ChokeEvery = 5, ChokeDamage = 0.5f;

    private ICoreServerAPI sapi;
    private WorldLayout layout;
    private WorldGeometry geometry;
    private Thresholds.ThresholdSystem thresholds;
    private readonly HashSet<long> bodiesDone = new();
    private readonly Dictionary<string, float> exposure = new();
    /// <summary>Seconds of filtering not yet worn off the hood (a hazmat hood wears 1 for every few seconds it filters).</summary>
    private readonly Dictionary<string, float> filtered = new();
    private readonly Dictionary<string, long> lastLoopMs = new();
    private readonly Random rand = new();
    private bool dirty;

    public override void Start(ICoreAPI api)
    {
        api.RegisterBlockBehaviorClass("BackroomsBasementDoor", typeof(BlockBehaviorBasementDoor));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Event.ServerRunPhase(EnumServerRunPhase.ModsAndConfigReady, () =>
        {
            if (api.WorldManager.SaveGame.WorldType != BackroomsWorld.WorldTypeCode) return;
            layout = BackroomsWorld.CreateLayout(api.World);
            geometry = BackroomsWorld.CreateGeometry(api.World);
            byte[] data = api.WorldManager.SaveGame.GetData(SaveKey);
            if (data != null)
                for (int i = 0; i + 8 <= data.Length; i += 8) bodiesDone.Add(BitConverter.ToInt64(data, i));
            api.Event.GameWorldSave += OnSave;
            api.Event.RegisterGameTickListener(OnLoopTick, 200);
            api.Event.RegisterGameTickListener(OnDeadTick, 1000, 500);
            thresholds = api.ModLoader.GetModSystem<Thresholds.ThresholdSystem>();
            api.Event.RegisterGameTickListener(OnLevel2Tick, 250, 100);
            api.Event.PlayerDisconnect += p => { exposure.Remove(p.PlayerUID); lastLoopMs.Remove(p.PlayerUID); };
        });
        // Dev test, console-safe (a console line's trailing carriage return is taken and ignored): lays down the bodies of
        // the cells round x z now, as a player coming near would, and says how many corpses lie there
        api.ChatCommands.Create("basementbodies")
            .WithDescription("Dev test: lays down the Basement's bodies in the nine cells round x z (as a player coming near would) and counts the corpses there")
            .RequiresPrivilege(Privilege.controlserver)
            .WithArgs(api.ChatCommands.Parsers.Int("x"), api.ChatCommands.Parsers.Int("z"), api.ChatCommands.Parsers.OptionalWord("ignored"))
            .HandleWith(args =>
            {
                if (layout == null) return TextCommandResult.Error("Not a Backrooms world");
                int x = (int)args[0], z = (int)args[1], mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z), planned = 0;
                for (int dz = -1; dz <= 1; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        planned += layout.BasementBodies(mx + dx, mz + dz).Count;
                        LayDown(mx + dx, mz + dz);
                    }
                int floor = geometry.FloorFor(WorldLayout.Basement);
                Entity[] found = sapi.World.GetEntitiesAround(new Vec3d(mx * WorldLayout.MacroSize + 16, floor, mz * WorldLayout.MacroSize + 16), 56, 8, e => e is EntityCorpse);
                string summary = $"basementbodies: {planned} planned in the nine cells, {found.Length} corpses lie within 56 blocks of the middle one";
                sapi.Logger.Notification("[backrooms] " + summary);
                return TextCommandResult.Success(summary);
            });
    }

    private void OnSave()
    {
        if (!dirty) return;
        var data = new byte[bodiesDone.Count * 8];
        int i = 0;
        foreach (long cell in bodiesDone) { BitConverter.GetBytes(cell).CopyTo(data, i); i += 8; }
        sapi.WorldManager.SaveGame.StoreData(SaveKey, data);
        dirty = false;
    }

    private bool InBasement(EntityPos pos) =>
        layout.LevelAt(WorldLayout.MacroOf((int)Math.Floor(pos.X)), WorldLayout.MacroOf((int)Math.Floor(pos.Z))) == WorldLayout.Basement;

    // ================= The cracked floor of Level 2 =================

    /// <summary>Whoever is in Level 2 and on one of the Basement's cracked patches goes through it (ThresholdSystem.Basement.cs).</summary>
    private void OnLevel2Tick(float dt)
    {
        if (layout == null || thresholds == null) return;
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
        {
            if (p is not IServerPlayer sp || sp.Entity == null) continue;
            int x = (int)Math.Floor(sp.Entity.Pos.X), z = (int)Math.Floor(sp.Entity.Pos.Z);
            if (layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) != 2 || !WorldLayout.IsBasementCrack(layout.TileAt(x, z))) continue;
            thresholds.BasementCrackInLevel2(sp);
        }
    }

    // ================= The stairwells =================

    /// <summary>Back to the landing by the door, from the landing a turn above or below it.</summary>
    private void OnLoopTick(float dt)
    {
        if (layout == null) return;
        int floor = geometry.FloorFor(WorldLayout.Basement);
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
        {
            EntityPlayer e = p.Entity;
            if (e == null || !e.Alive || !InBasement(e.Pos)) continue;
            int x = (int)Math.Floor(e.Pos.X), z = (int)Math.Floor(e.Pos.Z);
            Tile t = layout.TileAt(x, z);
            if (t.Variant != Worldgen.Props.BasementEscher || t.Stair != 1) continue;
            double rel = e.Pos.Y - floor;
            // (On the landing's step a turn up, either half of it: feet 8.5 or 9 over the floor; a turn down, -7.5 or -7)
            int shift = rel > WorldLayout.BasementEscherRise + 0.4 && rel < WorldLayout.BasementEscherRise + 2 ? -WorldLayout.BasementEscherRise
                : rel > WorldLayout.BasementEscherLow + 0.4 && rel < WorldLayout.BasementEscherLow + 1.5 ? WorldLayout.BasementEscherRise : 0;
            if (shift == 0) continue;
            long now = sapi.World.ElapsedMilliseconds;
            if (lastLoopMs.TryGetValue(p.PlayerUID, out long last) && now - last < 1000) continue;
            lastLoopMs[p.PlayerUID] = now;
            e.TeleportToDouble(e.Pos.X, e.Pos.Y + shift, e.Pos.Z);
        }
    }

    // ================= The dead =================

    private void OnDeadTick(float dt)
    {
        if (layout == null) return;
        foreach (IPlayer p in sapi.World.AllOnlinePlayers)
        {
            EntityPlayer e = p.Entity;
            if (e == null || !InBasement(e.Pos)) { if (p.PlayerUID != null) exposure.Remove(p.PlayerUID); continue; }
            int x = (int)Math.Floor(e.Pos.X), z = (int)Math.Floor(e.Pos.Z);
            int mx = WorldLayout.MacroOf(x), mz = WorldLayout.MacroOf(z);
            for (int dz = -1; dz <= 1; dz++)
                for (int dx = -1; dx <= 1; dx++) LayDown(mx + dx, mz + dz);
            if (e.Alive && p is IServerPlayer sp && p.WorldData.CurrentGameMode == EnumGameMode.Survival) Breathe(sp, x, z, dt);
        }
    }

    /// <summary>Lays a cell's bodies down, once, when every one of their chunks is loaded.</summary>
    private void LayDown(int mx, int mz)
    {
        long key = ((long)mx << 32) | (uint)mz;
        if (bodiesDone.Contains(key) || layout.LevelAt(mx, mz) != WorldLayout.Basement) return;
        var bodies = layout.BasementBodies(mx, mz);
        int floor = geometry.FloorFor(WorldLayout.Basement);
        IBlockAccessor ba = sapi.World.BlockAccessor;
        foreach (var (lx, lz, _, _) in bodies)
            if (ba.GetChunkAtBlockPos(new BlockPos(mx * WorldLayout.MacroSize + lx, floor, mz * WorldLayout.MacroSize + lz)) == null) return;
        bodiesDone.Add(key);
        dirty = true;
        foreach (var (lx, lz, kind, pier) in bodies)
        {
            double x = mx * WorldLayout.MacroSize + lx + 0.5, z = mz * WorldLayout.MacroSize + lz + 0.5;
            // The bones on the dry floor; the drowned on the bed of the Flood, under the water
            double y = kind == 0 ? floor + 1 : floor - 1;
            try { Spawn(kind, x, y, z, pier); }
            catch (Exception ex) { sapi.Logger.Error("[backrooms] basement: could not lay a body down at {0:0} {1:0} {2:0}: {3}", x, y, z, ex.Message); }
        }
    }

    private void Spawn(int kind, double x, double y, double z, ArchPier pier)
    {
        var at = new Vec3d(x, y, z);
        if (sapi.World.GetEntitiesAround(at, 1.5f, 2f, en => en is EntityCorpse).Length > 0) return;
        string code = kind == 0 ? CorpseSystem.BonesCode : CorpseSystem.FreshCode;
        EntityProperties type = sapi.World.GetEntityType(new AssetLocation(code));
        if (type == null) return;
        if (sapi.World.ClassRegistry.CreateEntity(type) is not EntityCorpse body) return;
        body.Pos.SetPos(x, y, z);
        body.Pos.Yaw = pier switch { ArchPier.North => 0f, ArchPier.East => GameMath.PIHALF, ArchPier.South => GameMath.PI, _ => -GameMath.PIHALF };
        ITreeAttribute wa = body.WatchedAttributes;
        wa.SetString(EntityCorpse.OwnerKey, DeadOwner);
        wa.SetString(EntityCorpse.OwnerNameKey, Lang.Get(kind switch { 0 => "backrooms:basement-dead-bones", 1 => "backrooms:basement-dead-drowned", _ => "backrooms:basement-dead-named" }));
        // (Old: they never lay down fresh; the drowned have been in the water a week, the bones far longer)
        double days = sapi.World.Calendar.TotalDays;
        wa.SetDouble(EntityCorpse.DiedKey, kind == 0 ? days - 60 : days - 0.5);
        wa[EntityBehaviorCorpseContents.TreeKey] = Pack(Belongings(kind));
        sapi.World.SpawnEntity(body);
    }

    /// <summary>What the dead still have on them: not much (Fandom: "Lack of Needed Resources").</summary>
    private List<ItemStack> Belongings(int kind)
    {
        var stacks = new List<ItemStack>();
        void Add(string code, int count)
        {
            if (count <= 0) return;
            CollectibleObject thing = (CollectibleObject)sapi.World.GetItem(new AssetLocation(code)) ?? sapi.World.GetBlock(new AssetLocation(code));
            if (thing != null) stacks.Add(new ItemStack(thing, count));
        }
        switch (kind)
        {
            case 0:
                Add("backrooms:carpetfibre", rand.Next(1, 3));
                if (rand.NextDouble() < 0.5) Add("backrooms:glassshard", 1);
                if (rand.NextDouble() < 0.3) Add("game:candle", 1);
                if (rand.NextDouble() < 0.2) Add("backrooms:emptybottle", 1);
                if (rand.NextDouble() < 0.12) Add("backrooms:wanderernote-way", 1);
                if (rand.NextDouble() < 0.1) Add("game:gear-rusty", 1);
                break;
            case 1:
                Add("game:rot", rand.Next(1, 3));
                if (rand.NextDouble() < 0.3) Add("game:gear-rusty", 1);
                break;
            default:
                // A bar worker's: his last wages, and what the water left of the rest
                Add("game:gear-rusty", rand.Next(2, 5));
                Add("game:rot", 1);
                break;
        }
        if (stacks.Count == 0) Add("game:rot", 1);
        return stacks;
    }

    private ITreeAttribute Pack(List<ItemStack> stacks)
    {
        int slots = Math.Max(4, (stacks.Count + 3) / 4 * 4);
        var inventory = new InventoryGeneric(slots, "corpse-basement", sapi, null);
        for (int i = 0; i < stacks.Count; i++) inventory[i].Itemstack = stacks[i];
        var tree = new TreeAttribute();
        inventory.ToTreeAttributes(tree);
        return tree;
    }

    /// <summary>The smell: building near the dead, easing away from them.</summary>
    private void Breathe(IServerPlayer player, int x, int z, float dt)
    {
        int dead = 0;
        for (int dz = -4; dz <= 4; dz++)
            for (int dx = -4; dx <= 4; dx++)
            {
                Tile t = layout.TileAt(x + dx, z + dz);
                if (t.Level == WorldLayout.Basement && t.Variant is Worldgen.Props.BasementBody or Worldgen.Props.BonePile or Worldgen.Props.Ribcage or Worldgen.Props.JawSkeleton) dead++;
            }
        exposure.TryGetValue(player.PlayerUID, out float was);
        // A hazmat hood's filter slows it, and wears for it (Wear/HazmatSystem.cs)
        float filter = 1f;
        if (dead >= 2 && Backrooms.Wear.HazmatSystem.Worn(player.Entity, "hood") != null)
        {
            filtered.TryGetValue(player.PlayerUID, out float since);
            since += dt;
            int wear = (int)(since / Backrooms.Wear.HazmatSystem.SmellWearSeconds);
            filtered[player.PlayerUID] = since - wear * Backrooms.Wear.HazmatSystem.SmellWearSeconds;
            filter = Backrooms.Wear.HazmatSystem.Through(player.Entity, "hood", 1f - Backrooms.Wear.HazmatSystem.HoodSmell, wear);
        }
        float now = dead >= 2 ? was + dt * filter : Math.Max(0, was - 2 * dt);
        exposure[player.PlayerUID] = now;
        if (was < WarnAfter && now >= WarnAfter)
            player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:basement-smell"), EnumChatType.Notification);
        if (was < ChokeAfter && now >= ChokeAfter)
            player.SendMessage(GlobalConstants.GeneralChatGroup, Say.T(player, "backrooms:basement-smell-choke"), EnumChatType.Notification);
        if (now >= ChokeAfter && (int)(now / ChokeEvery) != (int)(was / ChokeEvery))
            player.Entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Internal, Type = EnumDamageType.Suffocation }, ChokeDamage);
    }
}

/// <summary>
/// A Basement door (<c>basement-door-{closed|open|jammed}-{hinge}-{lower|upper}-{side}</c>, tools/gen_basement.py):
/// right-click either half to open or shut both, swinging on its hinges. A jammed one is swollen shut in its frame and
/// will not move; a pry bar (the old crowbar some leave lying about) forces it open, for good. (Hyphen-safe, unlike the
/// Suburbs' door: <see cref="BlockCodes.WithVariant"/>.)
/// </summary>
public class BlockBehaviorBasementDoor : BlockBehavior
{
    private WorldInteraction[] help;

    public BlockBehaviorBasementDoor(Block block) : base(block)
    {
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        help ??= new[] { new WorldInteraction { ActionLangCode = block.Variant["state"] == "jammed" ? "backrooms:blockhelp-basementdoor-force" : "backrooms:blockhelp-basementdoor", MouseButton = EnumMouseButton.Right } };
        return help;
    }

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        handling = EnumHandling.PreventDefault;
        if (world.Side != EnumAppSide.Server) return true;
        BlockPos pos = blockSel.Position;
        string state = block.Variant["state"], part = block.Variant["part"];
        if (state == "jammed")
        {
            ItemSlot hand = byPlayer?.InventoryManager?.ActiveHotbarSlot;
            if (hand?.Itemstack?.Collectible?.Code?.Path != "prybar")
            {
                (byPlayer as IServerPlayer)?.SendIngameError("backrooms-basementdoor", Lang.Get("backrooms:basementdoor-jammed"));
                world.PlaySoundAt(new AssetLocation("game:sounds/effect/latch"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 8);
                return true;
            }
            // Forced: the bar takes the wear, and everything near hears it
            hand.Itemstack.Collectible.DamageItem(world, byPlayer.Entity, hand, 1);
            hand.MarkDirty();
            world.PlaySoundAt(new AssetLocation("game:sounds/block/planks"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 24);
        }
        string next = state == "open" ? "closed" : "open";
        Swap(world, pos, next);
        BlockPos other = part == "lower" ? pos.UpCopy() : pos.DownCopy();
        Block half = world.BlockAccessor.GetBlock(other);
        if (half.Code?.Path is { } path && path.StartsWith("basement-door-") && half.Variant["part"] != part) Swap(world, other, next);
        world.PlaySoundAt(new AssetLocation("game:sounds/block/door"), pos.X + 0.5, pos.Y + 0.5, pos.Z + 0.5, null, true, 12);
        return true;
    }

    /// <summary>Puts the door at a position into another state, keeping its hinge, half and side.</summary>
    private static void Swap(IWorldAccessor world, BlockPos pos, string state)
    {
        Block here = world.BlockAccessor.GetBlock(pos);
        Block to = world.GetBlock(BlockCodes.WithVariant(here, "state", state));
        if (to == null || to.Id == 0) return;
        world.BlockAccessor.ExchangeBlock(to.BlockId, pos);
        world.BlockAccessor.MarkBlockDirty(pos);
    }
}
