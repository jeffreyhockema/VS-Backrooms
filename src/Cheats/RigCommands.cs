using System;
using System.Globalization;
using System.Linq;
using System.Reflection;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Backrooms.Worldgen;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Backrooms.Needs.Beds;

namespace Backrooms.Cheats;

/// <summary>
/// Test-rig helpers (tools/clientrig): /backrooms rig equip|sleep|face|walk. Each answers with one line starting "rig-" that the
/// rig driver reads out of the client's chat.
/// </summary>
public class RigCommands : ModSystem
{
    ICoreServerAPI sapi;

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After CheatSystem (1.2), which has made /backrooms
    public override double ExecuteOrder() => 1.3;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        var parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("rig")
                .WithDescription("Client test rig helpers: equip <set> (wear game:armor-head/body/legs-<set>, e.g. sewn-leather; or a comma list of item codes with their domain, each put on in a slot that takes it; or none, to take everything off), sleep (put a hotel bed beside you if there is none and lie down in it), face <text> (reports the heading and pitch to the nearest block whose code contains text, within 16 blocks), walk <blocks> (moves you that far along the way you face, one block at a time, over a floor and through free air), hurt <amount> (a blow from nothing in particular), classdrops <block> (the drops of a block such as supplybox rolled 400 times as if it stood where you do), place <code@dx,dz> (sets a block at your feet height dx, dz off, clearing the one above), use <text> (right-clicks the nearest block whose code contains text, within 16 blocks, as you would: its own behaviours run, so a door opens or takes you through), pry <text> (leans a pry bar on the nearest such block: says whether it gave, or why not), itemshow <code> [n] (the item in your selected hotbar slot and one at rest on the floor 2 blocks ahead, for item shots), worn (what you wear, with durability, and your health, stability and thirst rate)")
                .RequiresPlayer()
                .WithArgs(parsers.Word("what"), parsers.OptionalWord("arg"))
                .HandleWith(Handle)
            .EndSubCommand()
            .BeginSubCommand("stash")
                .WithDescription("Dev (feedback round 2026-11, the pleather conversion test; from the console too): 'put' sets a chest near the world's spawn and fills it with pleather, a worn and a fresh pleather piece; 'read' lists what is in it")
                .WithArgs(parsers.Word("what"))
                .HandleWith(Stash)
            .EndSubCommand()
            .BeginSubCommand("bal")
                .WithDescription("Dev (balance fixes 2026-11, tools/aitest BAL_CASES; from the console too): table <entityId> <x> <y> <z> (a straw dummy eats at a Level 73 place set there), hour, load <x> <z>, ent <id>, coranhound (a Hound beside Coran), cache <level> <block> <rolls> (a cache's extras, as Rewards rolls them), water (the class of the water by the Heart, Base Seedling and elsewhere in Level 23), dispenser <x> <y> <z> (a snack machine there, emptied for eight days: does it restock)")
                .WithArgs(parsers.Word("what"), parsers.OptionalWord("a"), parsers.OptionalWord("b"), parsers.OptionalWord("c"), parsers.OptionalWord("d"))
                .HandleWith(Bal)
            .EndSubCommand()
            .BeginSubCommand("growtree")
                .WithDescription("Dev: plants game:sapling-<wood>-free at x y z (the air block above the ground), makes it due and runs the sapling's own growth check until it turns into a tree; reports the tree generators the world has, the ground under it and the logs and leaves that came of it (from the console too)")
                .WithArgs(parsers.Int("x"), parsers.Int("y"), parsers.Int("z"), parsers.OptionalWord("wood"))
                .HandleWith(GrowTree)
            .EndSubCommand();
    }

    static int I(object o) => int.TryParse(o as string, NumberStyles.Integer, CultureInfo.InvariantCulture, out int v) ? v : 0;

    TextCommandResult Bal(TextCommandCallingArgs args)
    {
        string what = ((string)args[0]).Trim(), a = args[1] as string, b = args[2] as string, c = args[3] as string, d = args[4] as string;
        var menace = sapi.ModLoader.GetModSystem<Backrooms.Entities.MenaceSystem>();
        var layout = menace?.Layout;
        if (layout == null) return TextCommandResult.Error("rig-error: not a Backrooms world");
        var ic = CultureInfo.InvariantCulture;
        switch (what)
        {
            case "hour": return TextCommandResult.Success("rig-bal hour " + sapi.World.Calendar.TotalHours.ToString("0.00", ic));
            case "load":
            {
                int x = I(a), z = I(b);
                for (int dz = -2; dz <= 2; dz++)
                    for (int dx = -2; dx <= 2; dx++) sapi.WorldManager.LoadChunkColumn((x >> 5) + dx, (z >> 5) + dz, true);
                return TextCommandResult.Success("rig-bal load " + (sapi.World.BlockAccessor.GetChunkAtBlockPos(x, 1, z) != null ? "ok" : "loading"));
            }
            case "ent":
            {
                Entity e = sapi.World.GetEntityById(I(a));
                return TextCommandResult.Success($"rig-bal ent {I(a)} " + (e == null ? "gone" : e.Alive ? "alive" : "dead-body") + $" loaded {sapi.World.LoadedEntities.Count}");
            }
            case "table":
            {
                Entity e = sapi.World.GetEntityById(I(a));
                if (e == null) return TextCommandResult.Error("rig-error: no entity " + a);
                var pos = new BlockPos(I(b), I(c), I(d));
                if (sapi.World.BlockAccessor.GetChunkAtBlockPos(pos) == null) return TextCommandResult.Error("rig-error: table chunk not loaded");
                if (sapi.World.BlockAccessor.GetBlock(pos) is not Backrooms.Regions.BlockL73Table)
                {
                    Block set = sapi.World.GetBlock(new AssetLocation("backrooms:l73-table-set-north"));
                    if (set == null) return TextCommandResult.Error("rig-error: no block l73-table-set-north");
                    sapi.World.BlockAccessor.SetBlock(set.BlockId, pos);
                }
                if (sapi.World.BlockAccessor.GetBlockEntity(pos) is not Backrooms.Regions.BlockEntityL73Table table)
                {
                    sapi.World.BlockAccessor.SpawnBlockEntity("BackroomsL73Table", pos);
                    table = sapi.World.BlockAccessor.GetBlockEntity(pos) as Backrooms.Regions.BlockEntityL73Table;
                }
                if (table == null) return TextCommandResult.Error("rig-error: no table block entity");
                // (A straw dummy has no hunger: give it the behaviour, so what the meal does to satiety can be read)
                var hunger = e.GetBehavior<Vintagestory.GameContent.EntityBehaviorHunger>();
                if (hunger == null)
                {
                    hunger = new Vintagestory.GameContent.EntityBehaviorHunger(e);
                    e.AddBehavior(hunger);
                    hunger.Initialize(e.Properties, Vintagestory.API.Datastructures.JsonObject.FromJson("{}"));
                    hunger.Saturation = 100;
                    Backrooms.Needs.Needs.SetHydration(e, 200);
                }
                float sat0 = hunger.Saturation, hyd0 = Backrooms.Needs.Needs.Hydration(e);
                string result = !table.IsSet ? "cleared" : table.Feed(e) ? "fed" : "refused";
                return TextCommandResult.Success($"rig-bal table {e.EntityId} {result} satiety {sat0:0}->{hunger.Saturation:0} hydration {hyd0:0}->{Backrooms.Needs.Needs.Hydration(e):0} hour {sapi.World.Calendar.TotalHours.ToString("0.00", ic)}");
            }
            case "coranhound":
            {
                Entity coran = Backrooms.Regions.L73System.Server?.Coran;
                if (coran == null)
                {
                    // (He is put down outside the gate once its ground is loaded, a few seconds after a dummy is in the level)
                    for (int dz = -2; dz <= 2; dz++)
                        for (int dx = -2; dx <= 2; dx++) sapi.WorldManager.LoadChunkColumn((layout.L73Gate.X >> 5) + dx, (layout.L73Gate.Z >> 5) + dz, true);
                    return TextCommandResult.Error("rig-error: Coran is not about (loading the gate's ground), try again");
                }
                EntityProperties type = sapi.World.GetEntityType(new AssetLocation("backrooms:hound"));
                if (type == null) return TextCommandResult.Error("rig-error: no hound");
                Entity hound = sapi.World.ClassRegistry.CreateEntity(type);
                hound.Pos.SetPos(coran.Pos.X + 2, coran.Pos.Y, coran.Pos.Z);
                // (As /backrooms perceive puts a thing down: prepared for a dummy and always active, or the director's rules take a Hound nobody asked for away at once; its own tasks held still)
                // (The dummy it is prepared for stands by Coran: a Hound far from its target is taken away)
                if (menace.LivingDummies.FirstOrDefault() is { } dummy) dummy.TeleportToDouble(coran.Pos.X - 6, coran.Pos.Y, coran.Pos.Z);
                if (menace.LivingDummies.FirstOrDefault() is { } dummy2) Backrooms.Entities.EntityBehaviorMenace.Prepare(hound, dummy2, Backrooms.Entities.Encounter.Ambient, passive: true, sapi.World.ElapsedMilliseconds);
                hound.AlwaysActive = true;
                sapi.World.SpawnEntity(hound);
                if (hound.GetBehavior<Vintagestory.GameContent.EntityBehaviorTaskAI>()?.TaskManager is { } tasks)
                {
                    tasks.OnShouldExecuteTask += _ => false;
                    tasks.StopTasks();
                }
                return TextCommandResult.Success($"rig-bal coranhound {hound.EntityId} coran {coran.EntityId} at {coran.Pos.X:0} {coran.Pos.Y:0} {coran.Pos.Z:0}");
            }
            case "cache":
            {
                int level = WorldLayout.FromDisplayName(a);
                Block block = sapi.World.GetBlock(new AssetLocation("backrooms", b ?? "supplybox"));
                if (level < 0 || block == null) return TextCommandResult.Error("rig-error: cache <level> <block> <rolls>");
                int rolls = Math.Clamp(I(c) == 0 ? 200 : I(c), 1, 100000);
                var rewards = sapi.ModLoader.GetModSystem<Backrooms.Entities.Rewards>();
                var extras = new System.Collections.Generic.SortedDictionary<string, int>();
                var again = new System.Collections.Generic.SortedDictionary<string, int>();
                var pos = new BlockPos(0, 1, 0);
                for (int i = 0; i < rolls; i++)
                    rewards.RollCache(null, level, pos, block, (stack, extra) =>
                    {
                        var into = extra ? extras : again;
                        string code = stack.Collectible.Code.ToShortString();
                        into[code] = (into.TryGetValue(code, out int had) ? had : 0) + stack.StackSize;
                    });
                return TextCommandResult.Success($"rig-bal cache level {a} block {block.Code.Path} rolls {rolls}; extras: " + string.Join(", ", extras.Select(t => t.Key + " " + t.Value))
                    + "; contents again: " + string.Join(", ", again.Select(t => t.Key + " " + t.Value)));
            }
            case "dispenser":
            {
                var pos = new BlockPos(I(a), I(b), I(c));
                if (sapi.World.BlockAccessor.GetChunkAtBlockPos(pos) == null) return TextCommandResult.Error("rig-error: dispenser chunk not loaded");
                Block machine = sapi.World.GetBlock(new AssetLocation("backrooms:snackvending-north"));
                if (machine == null) return TextCommandResult.Error("rig-error: no block snackvending-north");
                sapi.World.BlockAccessor.SetBlock(machine.BlockId, pos);
                if (sapi.World.BlockAccessor.GetBlockEntity(pos) == null) sapi.World.BlockAccessor.SpawnBlockEntity("BackroomsDispenser", pos);
                if (sapi.World.BlockAccessor.GetBlockEntity(pos) is not Backrooms.Props.BlockEntityDispenser be) return TextCommandResult.Error("rig-error: no dispenser block entity");
                return TextCommandResult.Success($"rig-bal dispenser at {pos.X} {pos.Y} {pos.Z} level {WorldLayout.DisplayNumber(layout.LevelAt(WorldLayout.MacroOf(pos.X), WorldLayout.MacroOf(pos.Z)))}: " + be.TestRestock());
            }
            case "water": return Water(layout);
            default: return TextCommandResult.Error("rig-error: bal hour, load, ent, table, coranhound, cache, water or dispenser");
        }
    }

    /// <summary>The Level 23 water test: the class of every water block within 40 of the Heart, within Base Seedling's cavern, and in patches of the forest and glow rooms farther out.</summary>
    TextCommandResult Water(WorldLayout layout)
    {
        var geometry = BackroomsWorld.CreateGeometry(sapi.World);
        int floor = geometry.FloorFor(WorldLayout.Level23);
        var (sx, sz, sr) = layout.L23SeedlingAt;
        var spots = new System.Collections.Generic.List<(string Name, int X, int Z, int R)> { ("heart", layout.L23MidX, layout.L23MidZ, 40), ("seedling", sx, sz, sr) };
        for (int i = 0; i < 6; i++)
        {
            double ang = i * Math.PI / 3 + 0.3;
            spots.Add(("forest" + i, layout.L23MidX + (int)(Math.Cos(ang) * 110), layout.L23MidZ + (int)(Math.Sin(ang) * 110), 40));
        }
        int missing = 0;
        foreach (var (_, x, z, r) in spots)
            for (int cz = (z - r) >> 5; cz <= (z + r) >> 5; cz++)
                for (int cx = (x - r) >> 5; cx <= (x + r) >> 5; cx++)
                {
                    sapi.WorldManager.LoadChunkColumn(cx, cz, true);
                    if (sapi.World.BlockAccessor.GetChunkAtBlockPos(cx * 32, floor, cz * 32) == null) missing++;
                }
        if (missing > 0) return TextCommandResult.Error($"rig-error: loading the chunks of the Level 23 spots ({missing} missing), try again");
        var text = new System.Text.StringBuilder("rig-bal water");
        var pos = new BlockPos(0, 0, 0);
        foreach (var (name, x, z, r) in spots)
        {
            int clean = 0, tainted = 0, other = 0;
            double farthestClean = 0;
            for (int gz = z - r; gz <= z + r; gz++)
                for (int gx = x - r; gx <= x + r; gx++)
                {
                    if ((gx - x) * (gx - x) + (gz - z) * (gz - z) > r * r) continue;
                    for (int y = floor - 30; y <= floor + WorldLayout.L23Top; y++)
                    {
                        pos.Set(gx, y, gz);
                        Block fluid = sapi.World.BlockAccessor.GetBlock(pos, BlockLayersAccess.Fluid);
                        if (fluid == null || fluid.Id == 0 || fluid.LiquidCode != "water") continue;
                        switch (Backrooms.Needs.Water.WaterClass.Of(sapi.World, layout, fluid, pos))
                        {
                            case Backrooms.Needs.Water.WaterKind.Clean:
                                clean++;
                                farthestClean = Math.Max(farthestClean, name == "seedling" ? Math.Sqrt((gx - sx) * (double)(gx - sx) + (gz - sz) * (double)(gz - sz)) : layout.L23FromMid(gx, gz));
                                break;
                            case Backrooms.Needs.Water.WaterKind.Tainted: tainted++; break;
                            default: other++; break;
                        }
                    }
                }
            text.Append($" [{name} clean {clean} tainted {tainted} other {other} cleanmaxdist {farthestClean:0}];");
        }
        text.Append($" coreRadius {WorldLayout.L23CoreRadius} poolRadius {WorldLayout.L23PoolRadius}");
        return TextCommandResult.Success(text.ToString());
    }

    TextCommandResult Stash(TextCommandCallingArgs args)
    {
        BlockPos pos = sapi.World.DefaultSpawnPosition.AsBlockPos.AddCopy(2, 0, 2);
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        if (blocks.GetChunkAtBlockPos(pos) == null) return TextCommandResult.Error("rig-error: the spawn chunk is not loaded");
        if (((string)args[0]).Trim() == "put")
        {
            Block chest = sapi.World.GetBlock(new AssetLocation("game:chest-east"));
            blocks.SetBlock(chest.Id, pos);
            var be = blocks.GetBlockEntity(pos) as Vintagestory.GameContent.BlockEntityGenericTypedContainer;
            if (be == null) return TextCommandResult.Error("rig-error: no chest block entity");
            ItemStack Stack(string code, int size, int durability = -1)
            {
                Item item = sapi.World.GetItem(new AssetLocation(code));
                if (item == null) return null;
                var s = new ItemStack(item, size);
                if (durability >= 0) s.Attributes.SetInt("durability", durability);
                return s;
            }
            ItemStack[] put =
            {
                Stack("backrooms:pleather", 7), Stack("backrooms:armor-pleather-body", 1, 100), Stack("backrooms:armor-pleather-head", 1),
                Stack("backrooms:armor-pleather-legs", 1, 40), Stack("backrooms" + ":carpetsquare", 3), Stack("game:armor-body-sewn-leather", 1, 500),
            };
            for (int i = 0; i < put.Length; i++) be.Inventory[i].Itemstack = put[i]; // (null where an item is not in this version)
            be.MarkDirty(true);
            return TextCommandResult.Success($"rig-stash put at {pos.X} {pos.Y} {pos.Z}");
        }
        if (blocks.GetBlockEntity(pos) is not Vintagestory.GameContent.BlockEntityGenericTypedContainer chestBe) return TextCommandResult.Error("rig-error: no chest at " + pos);
        var text = new System.Text.StringBuilder($"rig-stash read at {pos.X} {pos.Y} {pos.Z}:");
        foreach (ItemSlot slot in chestBe.Inventory)
            if (slot.Itemstack is { } s) text.Append($" {s.Collectible.Code} x{s.StackSize} dur {s.Attributes.GetInt("durability", -1)};");
        return TextCommandResult.Success(text.ToString());
    }

    TextCommandResult GrowTree(TextCommandCallingArgs args)
    {
        var pos = new BlockPos((int)args[0], (int)args[1], (int)args[2]);
        string wood = (args[3] as string)?.Trim();
        if (string.IsNullOrEmpty(wood)) wood = "oak";
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        if (blocks.GetChunkAtBlockPos(pos) == null) return TextCommandResult.Error("rig-error: that column is not loaded");
        Block sapling = sapi.World.GetBlock(new AssetLocation("game:sapling-" + wood + "-free"));
        if (sapling == null) return TextCommandResult.Error("rig-error: no block sapling-" + wood + "-free");
        string under = blocks.GetBlock(pos.DownCopy()).Code?.ToString() ?? "?";
        int generators = sapi.World.TreeGenerators.Count;
        // A box round the sapling: what stood there before, so only the tree is counted
        int Count(string what)
        {
            int n = 0;
            var p = new BlockPos(0, 0, 0);
            for (int dx = -12; dx <= 12; dx++)
                for (int dz = -12; dz <= 12; dz++)
                    for (int dy = 0; dy <= 40; dy++)
                    {
                        p.Set(pos.X + dx, pos.Y + dy, pos.Z + dz);
                        if (p.Y < sapi.WorldManager.MapSizeY && (blocks.GetBlock(p).Code?.Path.Contains(what) ?? false)) n++;
                    }
            return n;
        }
        // What the sapling's own check looks at before it grows anything (BlockEntitySapling.CheckGrow): the ground 32 blocks
        // out each way has to be loaded. A player has loaded it; here ask for it and let the caller try again
        string why = "";
        int cs = sapi.WorldManager.ChunkSize;
        foreach (BlockFacing f in BlockFacing.HORIZONTALS)
        {
            var far = new BlockPos(pos.X + f.Normali.X * 32, pos.Y, pos.Z + f.Normali.Z * 32);
            if (!blocks.IsValidPos(far) || blocks.GetChunkAtBlockPos(far) != null) continue;
            why += " chunk-32-" + f.Code + "-not-loaded";
            sapi.WorldManager.LoadChunkColumnPriority(far.X / cs, far.Z / cs, new ChunkLoadOptions { KeepLoaded = true });
        }
        if (why != "") return TextCommandResult.Error("rig-error: loading the chunks round the sapling, try again:" + why);
        int logs0 = Count("log-"), leaves0 = Count("leaves");
        blocks.SetBlock(sapling.Id, pos);
        var be = blocks.GetBlockEntity(pos);
        if (be == null || be.GetType().Name != "BlockEntitySapling") return TextCommandResult.Error("rig-error: no sapling block entity came of it (" + be?.GetType().Name + ")");
        var type = be.GetType();
        const BindingFlags any = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
        var stage = type.GetField("stage", any);
        var due = type.GetField("totalHoursTillGrowth", any);
        var check = type.GetMethod("CheckGrow", any);
        if (stage == null || due == null || check == null) return TextCommandResult.Error("rig-error: BlockEntitySapling changed shape");
        stage.SetValue(be, Enum.ToObject(stage.FieldType, 1)); // Sapling: the seed stage only waits one sprout time
        string temp = blocks.GetClimateAt(pos, EnumGetClimateMode.ForSuppliedDate_TemperatureOnly, sapi.World.Calendar.TotalDays)?.Temperature.ToString("0.#", CultureInfo.InvariantCulture) ?? "?";
        string treeGen = sapling.Attributes?["treeGen"].AsString();
        if (treeGen == null) why += " no-treeGen-attribute";
        else if (!sapi.World.TreeGenerators.ContainsKey(new AssetLocation(treeGen))) why += " generator-" + treeGen + "-not-registered";
        bool grew = false;
        for (int i = 0; i < 3 && !grew; i++)
        {
            due.SetValue(be, 0.0);
            check.Invoke(be, new object[] { 0f });
            grew = blocks.GetBlock(pos).Id != sapling.Id;
        }
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture,
            "rig-growtree {0} at {1} {2} {3} on {4}: tree generators {5}, temperature {6}, grew {7}, logs {8}, leaves {9}, blocked by:{10}",
            sapling.Code.Path, pos.X, pos.Y, pos.Z, under, generators + (sapi.World.TreeGenerators.ContainsKey(new AssetLocation("englishoak")) ? " (with englishoak)" : " (no englishoak)"), temp, grew ? "yes" : "no", Count("log-") - logs0, Count("leaves") - leaves0, why == "" ? " nothing found" : why));
    }

    TextCommandResult Handle(TextCommandCallingArgs args)
    {
        var player = (IServerPlayer)args.Caller.Player;
        string arg = (args[1] as string)?.Trim();
        switch (((string)args[0]).Trim())
        {
            case "equip": return Equip(player, arg);
            case "sleep": return Sleep(player);
            case "face": return Face(player, arg);
            case "walk": return Walk(player, arg);
            case "hurt":
            {
                float amount = float.TryParse(arg, NumberStyles.Float, CultureInfo.InvariantCulture, out float a) ? a : 2f;
                player.Entity.ReceiveDamage(new DamageSource { Source = EnumDamageSource.Void, Type = EnumDamageType.BluntAttack }, amount);
                return TextCommandResult.Success("rig-hurt " + amount.ToString(CultureInfo.InvariantCulture));
            }
            case "chalk": return Chalk(player, arg);
            case "classdrops":
            {
                var at = player.Entity.Pos.AsBlockPos;
                var r = Backrooms.Salvage.ScarcitySystem.ClassDrops(sapi, arg ?? "supplybox", at.X, at.Z, 400);
                return r.Status == EnumCommandStatus.Success ? TextCommandResult.Success("rig-classdrops " + r.StatusMessage) : r;
            }
            case "place": return Place(player, arg);
            case "use": return Use(player, arg);
            case "pry": return PryAt(player, arg);
            case "cut": return Cut(player, arg);
            case "have": return Have(player);
            case "craft": return Craft(player, arg);
            case "tooltip": return Tooltip(player, arg);
            case "itemshow": return ItemShow(player, arg);
            case "worn": return Worn(player);
            default: return TextCommandResult.Error("rig-error: equip, sleep, face, walk, hurt, classdrops, place, use, pry, cut, have, craft, tooltip, itemshow or worn");
        }
    }

    /// <summary>
    /// cut [sneak]: right-clicks the block under your feet with what is in your active hand, as a player would (crouched with
    /// <c>sneak</c>), and reports the block before and after and what the cut gave (feedback round 2026-11: carpet squares).
    /// </summary>
    TextCommandResult Cut(IServerPlayer player, string arg)
    {
        bool sneak = arg == "sneak";
        for (int i = 0; i < 10; i++)
            if (player.InventoryManager.GetHotbarInventory()[i]?.Itemstack?.Collectible?.Code?.Path is "scraper" or "glassshiv")
            {
                player.InventoryManager.ActiveHotbarSlotNumber = i;
                break;
            }
        BlockPos pos = player.Entity.Pos.AsBlockPos.DownCopy();
        Block before = sapi.World.BlockAccessor.GetBlock(pos);
        int Count(string code) { int n = 0; foreach (var inv in player.InventoryManager.Inventories.Values.Where(i => i.ClassName != "creative")) foreach (ItemSlot s in inv) if (s?.Itemstack?.Collectible?.Code?.ToString() == code) n += s.Itemstack.StackSize; return n; }
        int squares = Count("backrooms" + ":carpetsquare"), fibre = Count("backrooms" + ":carpetfibre");
        bool was = player.Entity.Controls.ShiftKey;
        player.Entity.Controls.ShiftKey = sneak;
        var sel = new BlockSelection { Position = pos, Face = BlockFacing.UP, HitPosition = new Vec3d(0.5, 1, 0.5) };
        bool handled = before.OnBlockInteractStart(sapi.World, player, sel);
        player.Entity.Controls.ShiftKey = was;
        Block after = sapi.World.BlockAccessor.GetBlock(pos);
        return TextCommandResult.Success($"rig-cut {(sneak ? "crouched" : "standing")}: {before.Code} -> {after.Code}, handled {handled}, squares +{Count("backrooms" + ":carpetsquare") - squares}, fibre +{Count("backrooms" + ":carpetfibre") - fibre}");
    }

    /// <summary>
    /// craft code: finds the grid recipes that make an item or block (backrooms code, or domain:code) and checks each by the game's own
    /// matching: laid out with exactly what it asks, it matches; with one fewer of its biggest ingredient, it does not.
    /// </summary>
    TextCommandResult Craft(IServerPlayer player, string arg)
    {
        string want = arg != null && arg.Contains(':') ? arg : "backrooms:" + arg;
        var text = new System.Text.StringBuilder("rig-craft " + want);
        int found = 0, bad = 0;
        foreach (GridRecipe recipe in sapi.World.GridRecipes)
        {
            if (recipe.Output?.Code?.ToString() != want) continue;
            found++;
            var ingredients = recipe.ResolvedIngredients;
            ItemSlot[] Lay(int short1)
            {
                var grid = new ItemSlot[9];
                for (int i = 0; i < 9; i++) grid[i] = new DummySlot(null);
                int biggest = -1;
                for (int i = 0; i < ingredients.Length; i++) if (ingredients[i] != null && (biggest < 0 || ingredients[i].Quantity > ingredients[biggest].Quantity)) biggest = i;
                for (int i = 0; i < ingredients.Length; i++)
                {
                    var ing = ingredients[i];
                    if (ing?.ResolvedItemStack == null) continue;
                    var stack = ing.ResolvedItemStack.Clone();
                    stack.StackSize = ing.Quantity - (i == biggest ? short1 : 0);
                    if (stack.StackSize <= 0) continue;
                    grid[(i / recipe.Width) * 3 + i % recipe.Width] = new DummySlot(stack);
                }
                return grid;
            }
            bool exact = recipe.Matches(player, sapi.World, Lay(0), 3), one = recipe.Matches(player, sapi.World, Lay(1), 3);
            string asks = string.Join("+", ingredients.Where(i => i != null).GroupBy(i => i.Code.ToString()).Select(g => g.Sum(i => i.Quantity) + " " + g.Key));
            text.Append($" [{recipe.Width}x{recipe.Height} {asks}: exact {(exact ? "matches" : "NO MATCH")}, one short {(one ? "STILL MATCHES" : "no match")}]");
            if (!exact || one && ingredients.Any(i => i != null && i.Quantity > 1)) bad++;
        }
        if (found == 0) return TextCommandResult.Error("rig-error: no grid recipe makes " + want);
        text.Append(bad == 0 ? " ok" : " PROBLEM");
        return bad == 0 ? TextCommandResult.Success(text.ToString()) : TextCommandResult.Error(text.ToString());
    }

    BlockPos itemStage;

    /// <summary>
    /// The item stage: once per spot, a flat 15 x 15 pad of plain stone under the player's feet with the air above it cleared to 4 blocks (crops,
    /// grass and the like), so an item on the floor can be seen and the third-person camera has nothing behind it.
    /// </summary>
    void Stage(IServerPlayer player)
    {
        BlockPos at = player.Entity.Pos.AsBlockPos;
        if (itemStage != null && itemStage.X == at.X && itemStage.Y == at.Y && itemStage.Z == at.Z) return;
        Block stone = sapi.World.GetBlock(new AssetLocation("game:rock-granite"));
        var blocks = sapi.World.BlockAccessor;
        for (int dx = -7; dx <= 7; dx++)
            for (int dz = -7; dz <= 7; dz++)
            {
                if (stone != null && stone.Id != 0) blocks.SetBlock(stone.Id, new BlockPos(at.X + dx, at.Y - 1, at.Z + dz));
                for (int dy = 0; dy < 5; dy++)
                {
                    var pos = new BlockPos(at.X + dx, at.Y + dy, at.Z + dz);
                    if (dx == 0 && dz == 0 && dy < 2) continue;
                    if (blocks.GetBlock(pos).Id != 0) blocks.SetBlock(0, pos);
                }
            }
        itemStage = at.Copy();
    }

    long itemShowEntity = -1;

    /// <summary>
    /// itemshow code [n]: item shots for the item pass. Puts n (default 1) of the item (backrooms code, or domain:code) in the selected
    /// hotbar slot and sets one on the floor about 2 blocks ahead, at rest (the one shown before is despawned).
    /// </summary>
    TextCommandResult ItemShow(IServerPlayer player, string arg)
    {
        string[] parts = (arg ?? "").Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length == 0) return TextCommandResult.Error("rig-error: itemshow <code> [n]");
        string code = parts[0];
        int n = parts.Length > 1 && int.TryParse(parts[1], out int k) && k > 0 ? k : 1;
        var loc = new AssetLocation(code.Contains(':') ? code : "backrooms:" + code);
        CollectibleObject co = (CollectibleObject)sapi.World.GetItem(loc) ?? sapi.World.GetBlock(loc);
        if (co == null || co.Id == 0) return TextCommandResult.Error("rig-error: no item " + loc);
        ItemSlot slot = player.InventoryManager.ActiveHotbarSlot;
        if (slot == null) return TextCommandResult.Error("rig-error: no active hotbar slot");
        Stage(player);
        var held = new ItemStack(co, n);
        slot.Itemstack = held;
        slot.MarkDirty();
        if (itemShowEntity >= 0)
        {
            sapi.World.GetEntityById(itemShowEntity)?.Die(EnumDespawnReason.Removed);
            itemShowEntity = -1;
        }
        var e = player.Entity;
        double yaw = e.Pos.Yaw, x = e.Pos.X + Math.Sin(yaw) * 2, z = e.Pos.Z + Math.Cos(yaw) * 2;
        var ground = sapi.World.SpawnItemEntity(new ItemStack(co, 1), new Vec3d(x, e.Pos.Y + 0.05, z), new Vec3d(0, 0, 0));
        if (ground != null)
        {
            ground.Pos.Motion.Set(0, 0, 0);
            itemShowEntity = ground.EntityId;
        }
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-itemshow {0} x{1} in slot {2}, on the floor at {3:0.0} {4:0.0}", co.Code, n, player.InventoryManager.ActiveHotbarSlotNumber, x, z));
    }

    /// <summary>tooltip code: the info lines the game builds for an item (what the hover tooltip shows), as this server's collectible says them.</summary>
    TextCommandResult Tooltip(IServerPlayer player, string arg)
    {
        Item item = sapi.World.GetItem(new AssetLocation(arg != null && arg.Contains(':') ? arg : "game:" + arg));
        if (item == null) return TextCommandResult.Error("rig-error: no item " + arg);
        var sb = new System.Text.StringBuilder();
        item.GetHeldItemInfo(new DummySlot(new ItemStack(item)), sb, sapi.World, false);
        return TextCommandResult.Success("rig-tooltip " + item.Code + ": " + sb.ToString().Replace("\r", "").Replace("\n", " | "));
    }

    /// <summary>have: every stack of ours or armour in every inventory of the player, by inventory (the conversion test reads it).</summary>
    TextCommandResult Have(IServerPlayer player)
    {
        var text = new System.Text.StringBuilder("rig-have");
        foreach (var inv in player.InventoryManager.Inventories.Values.Where(i => i.ClassName != "creative"))
            foreach (ItemSlot s in inv)
                if (s?.Itemstack?.Collectible?.Code is { } code && (code.Path.Contains("pleather") || code.Path.Contains("carpet")))
                    text.Append($" [{inv.ClassName}] {code.Path} x{s.Itemstack.StackSize} dur {(s.Itemstack.Attributes?.GetInt("durability", -1) ?? -1)};");
        return TextCommandResult.Success(text.ToString());
    }

    /// <summary>
    /// place code@dx,dz: sets the block backrooms:code (or a domain:code) at the player's feet height, dx and dz blocks off
    /// (east and south), clearing the block above it, so a prop and its stripped twin can be photographed side by side.
    /// </summary>
    TextCommandResult Place(IServerPlayer player, string arg)
    {
        string[] parts = arg?.Split('@') ?? Array.Empty<string>();
        string[] off = parts.Length == 2 ? parts[1].Split(',') : Array.Empty<string>();
        if (off.Length != 2 || !int.TryParse(off[0], out int dx) || !int.TryParse(off[1], out int dz)) return TextCommandResult.Error("rig-error: place code@dx,dz");
        Block block = sapi.World.GetBlock(new AssetLocation(parts[0].Contains(':') ? parts[0] : "backrooms:" + parts[0]));
        if (block == null || block.Id == 0) return TextCommandResult.Error("rig-error: no block " + parts[0]);
        BlockPos pos = player.Entity.Pos.AsBlockPos.AddCopy(dx, 0, dz);
        sapi.World.BlockAccessor.SetBlock(block.Id, pos);
        sapi.World.BlockAccessor.SetBlock(0, pos.UpCopy());
        return TextCommandResult.Success($"rig-place {block.Code} at {pos.X} {pos.Y} {pos.Z}");
    }

    /// <summary>The nearest block (within 16 blocks of the player, 4 down to 6 up) whose code contains the text, or null.</summary>
    BlockPos Nearest(IServerPlayer player, string text)
    {
        var blocks = sapi.World.BlockAccessor;
        BlockPos at = player.Entity.Pos.AsBlockPos, best = null;
        double bestD = 1e9;
        for (int dx = -16; dx <= 16; dx++)
            for (int dz = -16; dz <= 16; dz++)
                for (int dy = -4; dy <= 6; dy++)
                {
                    var p = at.AddCopy(dx, dy, dz);
                    if (blocks.GetBlock(p).Code?.Path is not { } code || !code.Contains(text)) continue;
                    double d = dx * dx + dz * dz + dy * dy;
                    if (d < bestD) { bestD = d; best = p; }
                }
        return best;
    }

    /// <summary>use &lt;text&gt;: right-clicks the nearest block whose code contains the text, through the block's own interaction (its behaviours, on the server), as the player would.</summary>
    TextCommandResult Use(IServerPlayer player, string text)
    {
        if (string.IsNullOrEmpty(text)) return TextCommandResult.Error("rig-error: use <text>");
        if (Nearest(player, text) is not { } pos) return TextCommandResult.Error("rig-use none " + text);
        Block block = sapi.World.BlockAccessor.GetBlock(pos);
        var sel = new BlockSelection { Position = pos, Face = BlockFacing.UP, HitPosition = new Vec3d(0.5, 0.5, 0.5) };
        bool handled = block.OnBlockInteractStart(sapi.World, player, sel);
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-use {0} at {1} {2} {3}: {4}", block.Code.Path, pos.X, pos.Y, pos.Z, handled ? "used" : "nothing"));
    }

    /// <summary>pry &lt;text&gt;: a full lean of a pry bar on the nearest block whose code contains the text (PrySystem.Pry), and what came of it.</summary>
    TextCommandResult PryAt(IServerPlayer player, string text)
    {
        if (string.IsNullOrEmpty(text)) return TextCommandResult.Error("rig-error: pry <text>");
        if (Nearest(player, text) is not { } pos) return TextCommandResult.Error("rig-pry none " + text);
        var pry = sapi.ModLoader.GetModSystem<Backrooms.Salvage.PrySystem>();
        string code = sapi.World.BlockAccessor.GetBlock(pos).Code.Path, why = pry?.Refusal(pos);
        bool gave = pry?.Pry(player, pos, player.InventoryManager.ActiveHotbarSlot) == true;
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-pry {0} at {1} {2} {3}: {4}", code, pos.X, pos.Y, pos.Z,
            gave ? "it gave (" + sapi.World.BlockAccessor.GetBlock(pos).Code?.Path + " there now)" : "refused, " + (why ?? "not a locked door")));
    }

    /// <summary>chalk [colour]: gives the four coloured sticks (hotbar), and puts the four marks of the colour (white by default) on the wall ahead.</summary>
    TextCommandResult Chalk(IServerPlayer player, string colour)
    {
        foreach (string c in new[] { "red", "blue", "yellow", "green" })
        {
            Item stick = sapi.World.GetItem(new AssetLocation("backrooms", "chalk-" + c));
            if (stick == null) return TextCommandResult.Error("rig-error: no item chalk-" + c);
            player.InventoryManager.TryGiveItemstack(new ItemStack(stick), true);
        }
        string prefix = string.IsNullOrEmpty(colour) || colour == "white" ? "" : colour + "-";
        IBlockAccessor blocks = sapi.World.BlockAccessor;
        BlockFacing travel = BlockFacing.HorizontalFromYaw(player.Entity.Pos.Yaw);
        BlockFacing side = travel.Opposite;
        BlockFacing across = travel.GetCW();
        BlockPos pos = player.Entity.Pos.AsBlockPos.Copy();
        pos.Y += 1;
        for (int d = 1; d <= 10; d++)
        {
            BlockPos wall = pos.AddCopy(travel, d);
            if (!blocks.GetBlock(wall).SideSolid[side.Index]) continue;
            int placed = 0;
            string[] symbols = { "left", "right", "cross", "circle" };
            for (int i = 0; i < 4; i++)
            {
                BlockPos wallI = wall.AddCopy(across, i % 2).UpCopy(i / 2);
                BlockPos air = wallI.AddCopy(side);
                Block mark = sapi.World.GetBlock(new AssetLocation("backrooms", $"chalkmark-{prefix}{symbols[i]}-{side.Code}"));
                if (mark == null) return TextCommandResult.Error("rig-error: no block chalkmark-" + prefix + symbols[i] + "-" + side.Code);
                if (!blocks.GetBlock(wallI).SideSolid[side.Index]) continue;
                blocks.SetBlock(mark.BlockId, air);
                placed++;
            }
            return TextCommandResult.Success($"rig-chalk {prefix}marks {placed} at {wall.X} {wall.Y} {wall.Z}");
        }
        return TextCommandResult.Error("rig-error: no wall within 10 blocks ahead");
    }

    /// <summary>What the player wears (with each piece's durability where it has one), their health and stability: one line.</summary>
    TextCommandResult Worn(IServerPlayer player)
    {
        IInventory worn = player.InventoryManager.GetOwnInventory("character");
        var parts = new System.Collections.Generic.List<string>();
        if (worn == null) return TextCommandResult.Error("rig-error: no character inventory");
        foreach (ItemSlot slot in worn)
        {
            if (slot.Empty) continue;
            ItemStack s = slot.Itemstack;
            int max = s.Collectible.GetMaxDurability(s);
            parts.Add(s.Collectible.Code.Path + (max > 0 ? $" {s.Collectible.GetRemainingDurability(s)}/{max}" : ""));
        }
        float health = player.Entity.WatchedAttributes.GetTreeAttribute("health")?.GetFloat("currenthealth") ?? -1;
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-worn health {0:0.00} stability {1:0.000} thirstrate {2:0.00}: {3}",
            health, Backrooms.Entities.Senses.Stability(player.Entity), player.Entity.Stats.GetBlended("thirstrate"), parts.Count > 0 ? string.Join(", ", parts) : "nothing"));
    }

    TextCommandResult Equip(IServerPlayer player, string set)
    {
        if (string.IsNullOrEmpty(set)) return TextCommandResult.Error("rig-error: equip <set>");
        IInventory worn = player.InventoryManager.GetOwnInventory("character");
        if (worn == null) return TextCommandResult.Error("rig-error: no character inventory");
        int put = 0;
        // "none" takes everything off; a comma list of item codes (backrooms:clothes-head-baseballcap,...) puts each on
        if (set == "none")
        {
            foreach (ItemSlot slot in worn)
                if (!slot.Empty && slot.GetType().Name == "ItemSlotCharacter") { slot.Itemstack = null; slot.MarkDirty(); put++; }
            return TextCommandResult.Success($"rig-equip none: took off {put}");
        }
        if (set.Contains(':'))
        {
            var missing = new System.Collections.Generic.List<string>();
            foreach (string code in set.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            {
                Item item = sapi.World.GetItem(new AssetLocation(code));
                if (item == null) { missing.Add(code); continue; }
                var stack = new ItemStack(item);
                bool on = false;
                foreach (ItemSlot slot in worn)
                {
                    if (slot.GetType().Name != "ItemSlotCharacter" || !slot.CanHold(new DummySlot(stack))) continue;
                    slot.Itemstack = stack;
                    slot.MarkDirty();
                    on = true;
                    break;
                }
                if (on) put++; else missing.Add(code);
            }
            return put > 0 ? TextCommandResult.Success($"rig-equip pieces {put}" + (missing.Count > 0 ? "; not worn: " + string.Join(", ", missing) : ""))
                : TextCommandResult.Error("rig-error: none of " + set + " could be worn");
        }
        foreach (string zone in new[] { "head", "body", "legs" })
        {
            Item item = sapi.World.GetItem(new AssetLocation(set == "carpet" ? "backrooms:armor-carpet-" + zone : "game:armor-" + zone + "-" + set));
            if (item == null) continue;
            var stack = new ItemStack(item);
            foreach (ItemSlot slot in worn)
            {
                if (!slot.Empty || slot.GetType().Name != "ItemSlotCharacter") continue;
                if (!slot.CanHold(new DummySlot(stack))) continue;
                slot.Itemstack = stack;
                slot.MarkDirty();
                put++;
                break;
            }
        }
        return put > 0 ? TextCommandResult.Success($"rig-equip {set} pieces {put}") : TextCommandResult.Error($"rig-error: no piece of {set} could be worn");
    }

    TextCommandResult Sleep(IServerPlayer player)
    {
        var blocks = sapi.World.BlockAccessor;
        BlockPos at = player.Entity.Pos.AsBlockPos.Copy();
        BlockPos found = null;
        for (int dx = -6; dx <= 6 && found == null; dx++)
            for (int dz = -6; dz <= 6 && found == null; dz++)
                for (int dy = -2; dy <= 2; dy++)
                {
                    var p = at.AddCopy(dx, dy, dz);
                    if (blocks.GetBlock(p) is BlockBackroomsBed { IsHead: true }) { found = p; break; }
                }
        if (found == null)
        {
            Block head = sapi.World.GetBlock(new AssetLocation("backrooms:bed-head-north"));
            Block foot = sapi.World.GetBlock(new AssetLocation("backrooms:bed-foot-north"));
            if (head is not BlockBackroomsBed bed || foot == null) return TextCommandResult.Error("rig-error: no hotel bed blocks");
            found = at.AddCopy(2, 0, 0);
            blocks.SetBlock(head.Id, found);
            if (bed.PartnerPos(found) is { } footPos) blocks.SetBlock(foot.Id, footPos);
        }
        var sel = new BlockSelection { Position = found.Copy(), Face = BlockFacing.UP, HitPosition = new Vec3d(0.5, 0.5, 0.5) };
        bool ok = blocks.GetBlock(found).OnBlockInteractStart(sapi.World, player, sel);
        return ok ? TextCommandResult.Success($"rig-sleep ok bed {found.X} {found.Y} {found.Z}") : TextCommandResult.Error($"rig-sleep refused bed {found.X} {found.Y} {found.Z} (tired enough? try /backrooms stat rest 0.1)");
    }

    TextCommandResult Face(IServerPlayer player, string text)
    {
        if (string.IsNullOrEmpty(text)) return TextCommandResult.Error("rig-error: face <text>");
        var blocks = sapi.World.BlockAccessor;
        Vec3d eye = player.Entity.Pos.XYZ.Add(0, player.Entity.LocalEyePos.Y, 0);
        BlockPos at = player.Entity.Pos.AsBlockPos;
        BlockPos best = null; double bestD = 1e9;
        for (int dx = -16; dx <= 16; dx++)
            for (int dz = -16; dz <= 16; dz++)
                for (int dy = -4; dy <= 6; dy++)
                {
                    var p = at.AddCopy(dx, dy, dz);
                    string code = blocks.GetBlock(p).Code?.Path;
                    if (code == null || !code.Contains(text)) continue;
                    double d = dx * dx + dz * dz + dy * dy;
                    if (d < bestD) { bestD = d; best = p; }
                }
        if (best == null) return TextCommandResult.Error($"rig-face none {text}");
        // A wall plate (a code ending in the side it faces): stand three blocks in front of it, at its own height, so the shot shows it
        string path = blocks.GetBlock(best).Code.Path;
        BlockFacing side = BlockFacing.FromCode(path.Substring(path.LastIndexOf('-') + 1));
        if (side != null && side.IsHorizontal)
        {
            double sx = best.X + 0.5 + side.Normali.X * 3.0, sz = best.Z + 0.5 + side.Normali.Z * 3.0, sy = best.Y - 0.6;
            player.Entity.TeleportToDouble(sx, Math.Max(sy, player.Entity.Pos.Y - 1), sz);
            eye = new Vec3d(sx, Math.Max(sy, player.Entity.Pos.Y - 1) + player.Entity.LocalEyePos.Y, sz);
        }
        double ox = best.X + 0.5 - eye.X, oy = best.Y + 0.5 - eye.Y, oz = best.Z + 0.5 - eye.Z;
        double heading = (Math.Atan2(ox, -oz) * 180 / Math.PI + 360) % 360;
        double pitch = Math.Atan2(oy, Math.Sqrt(ox * ox + oz * oz)) * 180 / Math.PI;
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-face {0} at {1} {2} {3} dist {4:0.0} look {5:0} {6:0}",
            blocks.GetBlock(best).Code.Path, best.X, best.Y, best.Z, Math.Sqrt(bestD), heading, pitch));
    }

    TextCommandResult Walk(IServerPlayer player, string arg)
    {
        if (!double.TryParse(arg, NumberStyles.Float, CultureInfo.InvariantCulture, out double dist)) return TextCommandResult.Error("rig-error: walk <blocks>");
        var e = player.Entity;
        var blocks = sapi.World.BlockAccessor;
        double yaw = e.Pos.Yaw;
        // (Compass heading h is yaw pi - h; the way ahead is (sin yaw, cos yaw): north -z, east +x)
        double dx = Math.Sin(yaw), dz = Math.Cos(yaw), x = e.Pos.X, z = e.Pos.Z;
        int y = (int)Math.Floor(e.Pos.Y + 0.01), steps = 0;
        // One block at a time, through free air over a floor only: stop at a wall, a drop, water or fire
        for (int i = 1; i <= (int)dist; i++)
        {
            double nx = e.Pos.X + dx * i, nz = e.Pos.Z + dz * i;
            var feet = new BlockPos((int)Math.Floor(nx), y, (int)Math.Floor(nz));
            Block b0 = blocks.GetBlock(feet), b1 = blocks.GetBlock(feet.UpCopy()), floor = blocks.GetBlock(feet.DownCopy());
            bool free(Block b) => b.Id == 0 || (b.CollisionBoxes == null || b.CollisionBoxes.Length == 0) && !b.IsLiquid() && !(b.Code?.Path.Contains("fire") ?? false) && !(b.Code?.Path.Contains("lava") ?? false);
            if (!free(b0) || !free(b1) || floor.CollisionBoxes == null || floor.CollisionBoxes.Length == 0 || floor.IsLiquid()) break;
            x = nx; z = nz; steps = i;
        }
        if (steps > 0) e.TeleportToDouble(x, e.Pos.Y, z);
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-walk {0} of {1} blocks to {2:0.0} {3:0.0}", steps, (int)dist, x, z));
    }
}
