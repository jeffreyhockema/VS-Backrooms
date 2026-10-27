using System;
using System.Globalization;
using System.Linq;
using System.Reflection;
using Vintagestory.API.Common;
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
                .WithDescription("Client test rig helpers: equip <set> (wear game:armor-head/body/legs-<set>, e.g. sewn-leather), sleep (put a hotel bed beside you if there is none and lie down in it), face <text> (reports the heading and pitch to the nearest block whose code contains text, within 16 blocks), walk <blocks> (moves you that far along the way you face, one block at a time, over a floor and through free air), hurt <amount> (a blow from nothing in particular), classdrops <block> (the drops of a block such as supplybox rolled 400 times as if it stood where you do)")
                .RequiresPlayer()
                .WithArgs(parsers.Word("what"), parsers.OptionalWord("arg"))
                .HandleWith(Handle)
            .EndSubCommand()
            .BeginSubCommand("growtree")
                .WithDescription("Dev: plants game:sapling-<wood>-free at x y z (the air block above the ground), makes it due and runs the sapling's own growth check until it turns into a tree; reports the tree generators the world has, the ground under it and the logs and leaves that came of it (from the console too)")
                .WithArgs(parsers.Int("x"), parsers.Int("y"), parsers.Int("z"), parsers.OptionalWord("wood"))
                .HandleWith(GrowTree)
            .EndSubCommand();
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
            case "classdrops":
            {
                var at = player.Entity.Pos.AsBlockPos;
                var r = Backrooms.Salvage.ScarcitySystem.ClassDrops(sapi, arg ?? "supplybox", at.X, at.Z, 400);
                return r.Status == EnumCommandStatus.Success ? TextCommandResult.Success("rig-classdrops " + r.StatusMessage) : r;
            }
            default: return TextCommandResult.Error("rig-error: equip, sleep, face, walk, hurt or classdrops");
        }
    }

    TextCommandResult Equip(IServerPlayer player, string set)
    {
        if (string.IsNullOrEmpty(set)) return TextCommandResult.Error("rig-error: equip <set>");
        IInventory worn = player.InventoryManager.GetOwnInventory("character");
        if (worn == null) return TextCommandResult.Error("rig-error: no character inventory");
        int put = 0;
        foreach (string zone in new[] { "head", "body", "legs" })
        {
            Item item = sapi.World.GetItem(new AssetLocation("game:armor-" + zone + "-" + set));
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
