using System;
using System.Globalization;
using System.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;
using Vintagestory.GameContent;

namespace Backrooms.Props;

/// <summary>
/// /backrooms prop: tests of the working props (tools/aitest/run.py, the props cases), from the console too. Each answers
/// with one line starting "prop-".
/// </summary>
public partial class PropSystem
{
    private void RegisterCommands(ICoreServerAPI api)
    {
        var parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("prop")
                .WithDescription("Working props: find firealarm|valve|breaker|car|radio (takes you to the nearest; then x y z may be \"last\"), use x y z [fuse] (as if right-clicked there, with a fuse in hand), ring firealarm|caralarm|alarmclock|radio x y z (rings with no block), " +
                                 "light x y z (the light level there), block x y z, health x y z (the nearest creature or dummy there), status, " +
                                 "scene sprinkler|steam|breaker|clock x y z (builds a test: a sprinkler head over x y z with a lit firepit and torch under it and an alarm beside; " +
                                 "a leaking pipe over x y z with a valve beside; a lamp over x y z with a breaker beside; an alarm clock at x y z, wound)")
                .WithArgs(parsers.Word("action"), parsers.OptionalAll("args"))
                .HandleWith(OnPropCommand)
            .EndSubCommand();
    }

    private TextCommandResult OnPropCommand(TextCommandCallingArgs args)
    {
        string action = ((string)args[0]).Trim().ToLowerInvariant();
        string[] rest = ((args[1] as string) ?? "").Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(s => s.Trim()).Where(s => s.Length > 0).ToArray();
        IBlockAccessor ba = sapi.World.BlockAccessor;
        bool Pos(int at, out BlockPos pos)
        {
            pos = null;
            // "last": the prop the caller was last taken to (find) or the scene's prop; "here": five blocks ahead of the caller, on the
            // level they stand on; "me": where the caller stands
            if (rest.Length > at && rest[at] == "last") return lastFound.TryGetValue(args.Caller.Player?.PlayerUID ?? "", out pos);
            if (rest.Length > at && rest[at] == "me" && args.Caller.Entity is { } self)
            {
                pos = self.Pos.AsBlockPos;
                return true;
            }
            if (rest.Length > at && rest[at] == "here" && args.Caller.Entity is { } me)
            {
                BlockFacing ahead = BlockFacing.HorizontalFromYaw(me.Pos.Yaw);
                pos = me.Pos.AsBlockPos.AddCopy(ahead.Normali.X * 5, 0, ahead.Normali.Z * 5);
                return true;
            }
            if (rest.Length < at + 3) return false;
            if (!int.TryParse(rest[at], out int x) || !int.TryParse(rest[at + 1], out int y) || !int.TryParse(rest[at + 2], out int z)) return false;
            pos = new BlockPos(x, y, z);
            return true;
        }
        switch (action)
        {
            case "find":
            {
                if (rest.Length < 1 || args.Caller.Player is not IServerPlayer finder) return TextCommandResult.Error("prop-error: find firealarm|valve|breaker|car|radio (a player only)");
                return Find(finder, rest[0]);
            }
            case "status":
                return TextCommandResult.Success(string.Format("prop-status rings {0}, sprays {1}, jets {2}, tripped breakers {3} ({4} lights dark)",
                    rings.Count, sprays.Count, jets.Count, dark.Count, dark.Sum(s => s.Lights.Count)));
            case "use":
            {
                if (!Pos(0, out BlockPos pos)) return TextCommandResult.Error("prop-error: use x y z [fuse]");
                if (ba.GetChunkAtBlockPos(pos) == null) return TextCommandResult.Error("prop-error: not loaded");
                Block block = ba.GetBlock(pos);
                IPlayer player = args.Caller.Player;
                switch (BehaviorFor(block))
                {
                    case BlockBehaviorFireAlarm: PullAlarm(pos, player); break;
                    case BlockBehaviorSteamValve: TurnValve(pos, player); break;
                    case BlockBehaviorBreaker: UseBreaker(pos, player, rest.Contains("fuse")); break;
                    case BlockBehaviorCarAlarm: StrikeCar(pos, player); break;
                    case BlockBehaviorRadio: SwitchRadio(pos, block, player); break;
                    default:
                        if (ba.GetBlockEntity(pos) is BlockEntityAlarmClock clock) clock.Wind(player);
                        else return TextCommandResult.Error("prop-error: " + block.Code + " is not a working prop");
                        break;
                }
                return TextCommandResult.Success("prop-used " + block.Code + " at " + pos.X + " " + pos.Y + " " + pos.Z);
            }
            case "ring":
            {
                if (rest.Length < 1 || !Pos(1, out BlockPos pos)) return TextCommandResult.Error("prop-error: ring <kind> x y z");
                return StartRing(rest[0], pos, args.Caller.Entity is EntityPlayer ep ? ep : null)
                    ? TextCommandResult.Success("prop-ringing " + rest[0] + " at " + pos.X + " " + pos.Y + " " + pos.Z)
                    : TextCommandResult.Error("prop-error: no such kind " + rest[0]);
            }
            case "light":
            {
                if (!Pos(0, out BlockPos pos)) return TextCommandResult.Error("prop-error: light x y z");
                int light = ba.GetLightLevel(pos, EnumLightLevelType.MaxTimeOfDayLight);
                int blockLight = ba.GetLightLevel(pos, EnumLightLevelType.OnlyBlockLight);
                return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "prop-light {0} {1} {2} = {3} (block light {4})", pos.X, pos.Y, pos.Z, light, blockLight));
            }
            case "block":
            {
                if (!Pos(0, out BlockPos pos)) return TextCommandResult.Error("prop-error: block x y z");
                return TextCommandResult.Success(string.Format("prop-block {0} {1} {2} = {3}", pos.X, pos.Y, pos.Z, ba.GetBlock(pos).Code));
            }
            case "health":
            {
                if (!Pos(0, out BlockPos pos)) return TextCommandResult.Error("prop-error: health x y z");
                Entity e = sapi.World.GetNearestEntity(Centre(pos), 4, 4, en => en is EntityAgent { Alive: true });
                if (e == null) return TextCommandResult.Error("prop-error: nothing alive there");
                var health = e.WatchedAttributes.GetTreeAttribute("health");
                return TextCommandResult.Success(string.Format(CultureInfo.InvariantCulture, "prop-health {0}#{1} = {2:0.##} of {3:0.##}", e.Code.Path, e.EntityId,
                    health?.GetFloat("currenthealth") ?? -1, health?.GetFloat("maxhealth") ?? -1));
            }
            case "scene":
            {
                if (rest.Length < 1 || !Pos(1, out BlockPos pos)) return TextCommandResult.Error("prop-error: scene sprinkler|steam|breaker x y z");
                if (ba.GetChunkAtBlockPos(pos) == null) return TextCommandResult.Error("prop-error: not loaded");
                TextCommandResult made = Scene(rest[0], pos);
                // (What to use in the scene, for "use last": the alarm, the valve, the breaker, the clock)
                if (made.Status == EnumCommandStatus.Success && args.Caller.Player is { } builder)
                    lastFound[builder.PlayerUID] = rest[0] switch { "sprinkler" => pos.AddCopy(0, 0, 2), "steam" or "breaker" => pos.AddCopy(0, 0, 3), _ => pos.Copy() };
                return made;
            }
        }
        return TextCommandResult.Error("prop-error: unknown action " + action);
    }

    private readonly System.Collections.Generic.Dictionary<string, BlockPos> lastFound = new();

    /// <summary>Takes a player to the nearest working prop of a kind (a fire alarm with sprinkler heads near, if there is one), 3 blocks in front of it.</summary>
    private TextCommandResult Find(IServerPlayer player, string kind)
    {
        Type type = kind switch
        {
            "firealarm" => typeof(BlockBehaviorFireAlarm), "valve" => typeof(BlockBehaviorSteamValve), "breaker" => typeof(BlockBehaviorBreaker),
            "car" => typeof(BlockBehaviorCarAlarm), "radio" => typeof(BlockBehaviorRadio), _ => null,
        };
        if (type == null) return TextCommandResult.Error("prop-error: no such kind " + kind);
        IBlockAccessor ba = sapi.World.BlockAccessor;
        BlockPos me = player.Entity.Pos.AsBlockPos;
        var found = new System.Collections.Generic.List<(BlockPos Pos, int D)>();
        var p = new BlockPos(me.dimension);
        var verdict = new System.Collections.Generic.Dictionary<int, bool>();
        for (int dy = -8; dy <= 8; dy++)
            for (int dz = -96; dz <= 96; dz++)
                for (int dx = -96; dx <= 96; dx++)
                {
                    p.Set(me.X + dx, me.Y + dy, me.Z + dz);
                    Block b = ba.GetBlock(p);
                    if (b == null || b.Id == 0) continue;
                    if (!verdict.TryGetValue(b.Id, out bool yes)) verdict[b.Id] = yes = BehaviorFor(b)?.GetType() == type && b.Code.Path != "carcollider";
                    if (yes) found.Add((p.Copy(), dx * dx + dy * dy + dz * dz));
                }
        if (found.Count == 0) return TextCommandResult.Error("prop-error: no " + kind + " within 96 blocks");
        // (A breaker panel before a power box: the shots look for "breaker")
        var nearest = found.OrderBy(f => kind == "breaker" && !ba.GetBlock(f.Pos).Code.Path.Contains("breaker") ? 1 : 0).ThenBy(f => f.D).Select(f => f.Pos).Take(16).ToList();
        BlockPos best = nearest[0];
        int heads = 0;
        if (kind == "firealarm")
            foreach (BlockPos c in nearest)
                if ((heads = FindHeads(c).Count) > 0) { best = c; break; }
        lastFound[player.PlayerUID] = best;
        BlockFacing side = ValveFacing(ba.GetBlock(best));
        if (side == null || !side.IsHorizontal) side = BlockFacing.HORIZONTALS.FirstOrDefault(f => Passable(ba, best.AddCopy(f))) ?? BlockFacing.NORTH;
        int sx = best.X + side.Normali.X * 3, sz = best.Z + side.Normali.Z * 3;
        int y = Entities.Senses.FindFloor(sapi.World, sx, best.Y, sz, 2, 6);
        player.Entity.TeleportToDouble(sx + 0.5, y == int.MinValue ? best.Y : y, sz + 0.5);
        return TextCommandResult.Success(string.Format("prop-found {0} at {1} {2} {3} ({4} sprinkler heads near)", ba.GetBlock(best).Code, best.X, best.Y, best.Z, heads));
    }

    private int Id(string code) => sapi.World.GetBlock(new AssetLocation(code))?.Id ?? 0;

    /// <summary>A test scene round a spot where something can stand (air at y, a floor under it).</summary>
    private TextCommandResult Scene(string kind, BlockPos at)
    {
        IBlockAccessor ba = sapi.World.BlockAccessor;
        // (Clears a box round the spot so the scene stands the same wherever it is put: air from y to y+2, a ceiling at y+3)
        var p = new BlockPos(at.dimension);
        void Set(int dx, int dy, int dz, string code)
        {
            p.Set(at.X + dx, at.Y + dy, at.Z + dz);
            ba.SetBlock(code == null ? 0 : Id(code), p);
        }
        for (int dx = -3; dx <= 3; dx++)
            for (int dz = -3; dz <= 3; dz++)
            {
                Set(dx, -1, dz, "backrooms:concretefloor-plain");
                for (int dy = 0; dy <= 2; dy++) Set(dx, dy, dz, null);
                Set(dx, 3, dz, "backrooms:concreteceiling");
            }
        switch (kind)
        {
            case "sprinkler":
            {
                Set(0, 3, 0, "backrooms:officeceilingalt-sprinkler");
                Set(1, 0, 0, "game:firepit-lit");
                p.Set(at.X + 1, at.Y, at.Z);
                if (ba.GetBlockEntity(p) is BlockEntityFirepit pit)
                {
                    pit.fuelBurnTime = pit.maxFuelBurnTime = 600;
                    pit.MarkDirty(true);
                }
                Set(-1, 0, 0, "game:torch-basic-lit-up");
                Set(0, 0, 2, "backrooms:officedeco-alarm-north");
                return TextCommandResult.Success(string.Format("prop-scene sprinkler: head {0} {1} {2}, firepit {3} {1} {4}, torch {5} {6} {4}, alarm {0} {6} {7}",
                    at.X, at.Y + 3, at.Z, at.X + 1, at.Z, at.X - 1, at.Y, at.Z + 2));
            }
            case "steam":
                Set(0, 2, 0, "backrooms:pipes-leak-we");
                Set(0, 0, 3, "backrooms:gaugeframe-valve-north");
                return TextCommandResult.Success(string.Format("prop-scene steam: pipe {0} {1} {2}, valve {0} {3} {4}", at.X, at.Y + 2, at.Z, at.Y, at.Z + 3));
            case "clock":
            {
                Set(0, 0, 0, "backrooms:alarmclock-north");
                p.Set(at.X, at.Y, at.Z);
                if (ba.GetBlockEntity(p) is not BlockEntityAlarmClock clock) return TextCommandResult.Error("prop-error: the clock has no block entity");
                clock.Wind(null);
                return TextCommandResult.Success(string.Format("prop-scene clock: wound at {0} {1} {2}, rings in {3} s", at.X, at.Y, at.Z, BlockAlarmClock.DelaySeconds));
            }
            case "breaker":
                Set(0, 2, 0, "backrooms:hanginglight-on-we");
                Set(2, 0, 2, "backrooms:hanginglight-on-ns");
                Set(0, 0, 3, "backrooms:l1deco-breaker-north");
                return TextCommandResult.Success(string.Format("prop-scene breaker: lamps {0} {1} {2} and {3} {1} {4}, breaker {0} {5} {6}", at.X, at.Y + 2, at.Z, at.X + 2, at.Z + 2, at.Y, at.Z + 3));
        }
        return TextCommandResult.Error("prop-error: no such scene " + kind);
    }
}
