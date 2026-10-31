using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Config;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Entities;

/// <summary>
/// Moth jelly (docs/design/entity-ai-overhaul/README.md section 7): a found item, never crafted. Right-click and it
/// is set down in front of you as an item on the floor; for <see cref="BaitSystem.Seconds"/> it is bait: every male
/// Deathmoth (<see cref="AiTaskMoth"/>'s bait branch) and Death Rat (<see cref="AiTaskBait"/>, a task of its own that
/// outranks the rat's menace task) within <see cref="BaitSystem.Range"/> blocks goes to it and feeds. Then it is gone.
/// Picking it up again ends it.
/// </summary>
public class ItemMothJelly : Item
{
    public override void OnHeldInteractStart(ItemSlot slot, EntityAgent byEntity, BlockSelection blockSel, EntitySelection entitySel, bool firstEvent, ref EnumHandHandling handling)
    {
        if (!firstEvent || byEntity == null) return;
        handling = EnumHandHandling.PreventDefault;
        if (api.Side != EnumAppSide.Server) return;
        BaitSystem system = api.ModLoader.GetModSystem<BaitSystem>();
        if (system == null) return;

        // Where it goes: in front of the feet, a little over the floor, to fall the rest of the way
        var flat = new Vec3d(Math.Sin(byEntity.Pos.Yaw), 0, Math.Cos(byEntity.Pos.Yaw));
        Vec3d at = byEntity.Pos.XYZ.Add(flat.X * 1.4, 1.0, flat.Z * 1.4);
        if (blockSel != null && api.World.BlockAccessor.GetBlock(blockSel.Position).CollisionBoxes != null)
            at = blockSel.Position.ToVec3d().Add(blockSel.HitPosition.X, 0, blockSel.HitPosition.Z).Add(0, 1.0, 0);

        Entity dropped = api.World.SpawnItemEntity(new ItemStack(this), at, new Vec3d(flat.X * 0.04, 0.02, flat.Z * 0.04));
        if (dropped == null) return;
        system.Place(dropped);
        api.World.PlaySoundAt(new AssetLocation("game:sounds/effect/squish1"), at.X, at.Y, at.Z, null, true, 12, 0.5f);
        if (byEntity is not EntityPlayer { Player.WorldData.CurrentGameMode: EnumGameMode.Creative })
        {
            slot.TakeOut(1);
            slot.MarkDirty();
        }
    }
}

/// <summary>The jellies set down and still fresh, on the server; what the moths and rats ask where the nearest is.</summary>
public class BaitSystem : ModSystem
{
    /// <summary>How far it draws, and for how long (real seconds).</summary>
    public const double Range = 24;
    public const int Seconds = 60;

    private ICoreServerAPI sapi;
    private readonly List<(Entity Item, long UntilMs)> baits = new();

    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After the BackroomsModSystem that creates the /backrooms command this adds to
    public override double ExecuteOrder() => 1.2;

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("baittest")
                .WithDescription("Dev test: sets a moth jelly down 6 blocks ahead as bait and puts a Death Rat and a male Deathmoth 12 blocks behind you (from the console: at the world spawn), reporting in the log how far each is from it every 2 seconds for 20 seconds")
                .HandleWith(args => OnBaitTest(api, args))
            .EndSubCommand();
    }

    /// <summary>Marks a dropped jelly as bait for a minute; it is removed when the time is up.</summary>
    public void Place(Entity item)
    {
        baits.Add((item, sapi.World.ElapsedMilliseconds + Seconds * 1000L));
        sapi.Logger.Notification("[backrooms] moth jelly set down at {0:0},{1:0},{2:0}", item.Pos.X, item.Pos.Y, item.Pos.Z);
        sapi.World.RegisterCallback(_ =>
        {
            baits.RemoveAll(b => b.Item == item);
            if (item.Alive) item.Die(EnumDespawnReason.Expire);
        }, Seconds * 1000);
    }

    /// <summary>The nearest fresh bait within a range of a position, or null.</summary>
    public Entity NearestBait(Vec3d from, double range)
    {
        long now = sapi.World.ElapsedMilliseconds;
        Entity best = null;
        double bestDistance = range;
        for (int i = baits.Count - 1; i >= 0; i--)
        {
            (Entity item, long until) = baits[i];
            if (!item.Alive || item.ShouldDespawn || item.World.GetEntityById(item.EntityId) == null || now > until)
            {
                baits.RemoveAt(i);
                continue;
            }
            double d = item.Pos.XYZ.DistanceTo(from);
            if (d <= bestDistance)
            {
                best = item;
                bestDistance = d;
            }
        }
        return best;
    }

    /// <summary>The nearest fresh bait within a range of an entity (server side), or null.</summary>
    public static Entity Nearest(Entity from, double range) =>
        from.Api.ModLoader.GetModSystem<BaitSystem>()?.NearestBait(from.Pos.XYZ, range);

    private TextCommandResult OnBaitTest(ICoreServerAPI api, TextCommandCallingArgs args)
    {
        Entity who = args.Caller.Entity;
        // (From the console there is no one: the jelly itself stands in as the creatures' owner, flagged as a test target)
        Vec3d origin = who?.Pos.XYZ ?? api.World.DefaultSpawnPosition.XYZ;
        double yaw = who?.Pos.Yaw ?? 0;
        var dir = new Vec3d(Math.Sin(yaw), 0, Math.Cos(yaw));
        Item jelly = api.World.GetItem(new AssetLocation("backrooms:mothjelly"));
        Vec3d at = origin.AddCopy(dir.X * 6, 0.5, dir.Z * 6);
        Entity bait = api.World.SpawnItemEntity(new ItemStack(jelly), at);
        if (bait == null) return TextCommandResult.Error("Could not set the jelly down");
        Place(bait);
        if (who == null)
        {
            who = bait;
            bait.WatchedAttributes.SetBool(Senses.TestTargetKey, true);
        }

        var watched = new List<Entity>();
        foreach (string code in new[] { "backrooms:deathrat", "backrooms:deathmoth-male" })
        {
            EntityProperties type = api.World.GetEntityType(new AssetLocation(code));
            if (type == null) continue;
            Entity e = api.World.ClassRegistry.CreateEntity(type);
            e.Pos.SetPos(origin.X - dir.X * 6, origin.Y + (code.Contains("moth") ? 1.5 : 0), origin.Z - dir.Z * 6);
            EntityBehaviorMenace.Prepare(e, who, Encounter.Ambient, passive: true, api.World.ElapsedMilliseconds);
            api.World.SpawnEntity(e);
            watched.Add(e);
        }
        int n = 0;
        void Report(float dt)
        {
            api.Logger.Notification("[backrooms] baittest t={0}s: {1}", n * 2, string.Join(", ", watched.ConvertAll(e => $"{e.Code.Path} #{e.EntityId} alive={e.Alive} {e.Pos.XYZ.DistanceTo(bait.Pos.XYZ):0.0} from the jelly")));
            if (++n <= 10) api.World.RegisterCallback(Report, 2000);
        }
        api.World.RegisterCallback(Report, 2000);
        return TextCommandResult.Success($"Jelly down at {at.X:0},{at.Y:0},{at.Z:0}; {watched.Count} creatures put 12 blocks off; watch the log");
    }
}

/// <summary>
/// A Death Rat drawn to moth jelly: goes to the nearest fresh one within <see cref="BaitSystem.Range"/> and eats there
/// until it is gone. Its priority is above the menace task's, so a rat that was stalking or hunting somebody turns
/// from them to it.
/// </summary>
public class AiTaskBait : AiTaskBase
{
    private readonly float speed;
    private Entity bait;
    private long nextLookMs, lastPathMs;
    private bool eating, stuck;

    public AiTaskBait(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        speed = taskConfig["speed"].AsFloat(0.04f);
    }

    public override bool ShouldExecute()
    {
        if (!entity.Alive || entity.Attributes.GetBool(AiTaskMenace.FrenzyKey)) return false;
        long now = entity.World.ElapsedMilliseconds;
        if (now < nextLookMs) return false;
        nextLookMs = now + 500;
        bait = BaitSystem.Nearest(entity, BaitSystem.Range);
        return bait != null;
    }

    public override void StartExecute()
    {
        base.StartExecute();
        eating = stuck = false;
        Go();
    }

    private void Go()
    {
        lastPathMs = entity.World.ElapsedMilliseconds;
        pathTraverser.NavigateTo_Async(bait.Pos.XYZ.Clone(), speed, 0.9f, () => { }, () => stuck = true, () => stuck = true, 1500, 1);
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || stuck) return false;
        if (bait == null || !bait.Alive || BaitSystem.Nearest(entity, BaitSystem.Range) != bait) return false;
        double d = entity.Pos.DistanceTo(bait.Pos);
        if (d < 1.4)
        {
            if (!eating)
            {
                eating = true;
                pathTraverser.Stop();
                entity.AnimManager.StartAnimation("eat");
            }
            entity.Pos.Yaw = (float)Math.Atan2(bait.Pos.X - entity.Pos.X, bait.Pos.Z - entity.Pos.Z);
            return true;
        }
        if (!pathTraverser.Active && entity.World.ElapsedMilliseconds - lastPathMs > 1500) Go();
        return true;
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        pathTraverser.Stop();
        entity.AnimManager.StopAnimation("eat");
        // (Gave up, or it was gone: look again in a few seconds rather than at once)
        nextLookMs = entity.World.ElapsedMilliseconds + (stuck ? 4000 : 500);
    }
}
