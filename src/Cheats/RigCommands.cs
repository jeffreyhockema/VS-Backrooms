using System;
using System.Globalization;
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
                .WithDescription("Client test rig helpers: equip <set> (wear game:armor-head/body/legs-<set>, e.g. sewn-leather), sleep (put a hotel bed beside you if there is none and lie down in it), face <text> (reports the heading and pitch to the nearest block whose code contains text, within 16 blocks), walk <blocks> (moves you that far along the way you face), classdrops <block> (the drops of a block such as supplybox rolled 400 times as if it stood where you do)")
                .RequiresPlayer()
                .WithArgs(parsers.Word("what"), parsers.OptionalWord("arg"))
                .HandleWith(Handle)
            .EndSubCommand();
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
            case "classdrops":
            {
                var at = player.Entity.Pos.AsBlockPos;
                var r = Backrooms.Salvage.ScarcitySystem.ClassDrops(sapi, arg ?? "supplybox", at.X, at.Z, 400);
                return r.Status == EnumCommandStatus.Success ? TextCommandResult.Success("rig-classdrops " + r.StatusMessage) : r;
            }
            default: return TextCommandResult.Error("rig-error: equip, sleep, face, walk or classdrops");
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
        double ox = best.X + 0.5 - eye.X, oy = best.Y + 0.5 - eye.Y, oz = best.Z + 0.5 - eye.Z;
        double heading = (Math.Atan2(ox, -oz) * 180 / Math.PI + 360) % 360;
        double pitch = Math.Atan2(oy, Math.Sqrt(ox * ox + oz * oz)) * 180 / Math.PI;
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-face {0} at {1} {2} {3} dist {4:0.0} look {5:0} {6:0}",
            blocks.GetBlock(best).Code.Path, best.X, best.Y, best.Z, Math.Sqrt(bestD), heading, -pitch));
    }

    TextCommandResult Walk(IServerPlayer player, string arg)
    {
        if (!double.TryParse(arg, NumberStyles.Float, CultureInfo.InvariantCulture, out double dist)) return TextCommandResult.Error("rig-error: walk <blocks>");
        var e = player.Entity;
        double yaw = e.Pos.Yaw;
        // (Compass heading h is yaw pi - h; the way ahead is (sin yaw, cos yaw): north -z, east +x)
        double x = e.Pos.X + Math.Sin(yaw) * dist, z = e.Pos.Z + Math.Cos(yaw) * dist;
        e.TeleportToDouble(x, e.Pos.Y, z);
        return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "rig-walk to {0:0.0} {1:0.0}", x, z));
    }
}
