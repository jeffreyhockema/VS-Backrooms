using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.Datastructures;
using Vintagestory.API.MathTools;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>
/// How a Faceling goes about the halls (in place of vanilla's wander, which walks a straight line at a random point
/// up to thirty blocks off, through whatever wall is in the way, and stands pressed against it until it gives up).
/// <list type="bullet">
/// <item>It picks somewhere it can actually walk to: a search over the floor (<see cref="FloorSearch"/>) from where it
/// stands, a dozen or so steps out along the corridors, never through a wall, never off a drop it could not climb back.</item>
/// <item>The way there keeps to the middle of a hall where it can: floor beside a wall costs more to cross.</item>
/// <item>It mostly carries on the way it was going, so it walks a corridor to its end rather than pacing back and
/// forth, and turns where the corridor turns or ends.</item>
/// <item>It turns on the spot to face the way before it sets off, walks slowly, and at the end turns to look down the
/// most open way (not at the wall), and stands a while before it moves on.</item>
/// <item>It keeps within <c>maxDistanceToSpawn</c> of where it was first put down (the spawn position vanilla's wander
/// kept, under the same attribute keys).</item>
/// </list>
/// </summary>
public class AiTaskAmble : AiTaskBase
{
    private enum Step { Turn, Walk, Look }

    private readonly float moveSpeed, minWalk, maxWalk, maxDistanceToSpawn;
    private readonly string walkAnim;
    private readonly double bodyHeight;
    private EntityBehaviorMenace menace;
    private MenaceSystem director;

    private List<Vec3d> route;
    private Step step;
    private float stepTime, lookFor, speed;
    private float lookYaw;
    private bool done, stuck, animOn;
    private int failures;
    /// <summary>The way it was last walking (x, z, unit length), to carry on along a corridor.</summary>
    private double headingX, headingZ;
    private Vec3d spawn;

    public AiTaskAmble(EntityAgent entity, JsonObject taskConfig, JsonObject aiConfig) : base(entity, taskConfig, aiConfig)
    {
        moveSpeed = taskConfig["movespeed"].AsFloat(0.01f);
        minWalk = taskConfig["minWalk"].AsFloat(5);
        maxWalk = taskConfig["maxWalk"].AsFloat(16);
        maxDistanceToSpawn = taskConfig["maxDistanceToSpawn"].AsFloat(24);
        walkAnim = taskConfig["walkAnimation"].AsString("walk")?.ToLowerInvariant();
        bodyHeight = entity.Properties.CollisionBoxSize?.Y ?? 1.85f;
    }

    // ---- Where it was put down (vanilla wander's keys, so a Faceling from before keeps its home) ----

    public override void OnEntitySpawn() => KeepSpawn(true);

    public override void OnEntityLoaded() => KeepSpawn(false);

    private void KeepSpawn(bool fresh)
    {
        ITreeAttribute a = entity.Attributes;
        if (fresh || !a.HasAttribute("spawnX"))
        {
            a.SetDouble("spawnX", entity.Pos.X);
            a.SetDouble("spawnY", entity.Pos.Y);
            a.SetDouble("spawnZ", entity.Pos.Z);
        }
        spawn = new Vec3d(a.GetDouble("spawnX"), a.GetDouble("spawnY"), a.GetDouble("spawnZ"));
    }

    // ---- Deciding ----

    public override bool ShouldExecute()
    {
        long now = entity.World.ElapsedMilliseconds;
        if (now < cooldownUntilMs || !entity.Alive || !PreconditionsSatisfied()) return false;
        menace ??= entity.GetBehavior<EntityBehaviorMenace>();
        if (menace != null && menace.Kind != Encounter.Ambient) return false;
        if (entity.Pos.Motion.Y < -0.1) return false; // (falling)
        director ??= entity.Api.ModLoader.GetModSystem<MenaceSystem>();
        if (spawn == null) KeepSpawn(false);

        route = Plan(out string why);
        if (route == null)
        {
            // Nowhere to go from here just now (boxed in, or in mid-air): stand and look again in a while
            cooldownUntilMs = now + 3000 + entity.World.Rand.Next(4000);
            Log("stays put: {0}", why);
            return false;
        }
        return true;
    }

    private List<Vec3d> Plan(out string why, bool quiet = false)
    {
        var search = new FloorSearch(entity.World.BlockAccessor, bodyHeight);
        if (!search.Run(entity.Pos.X, entity.Pos.Y, entity.Pos.Z, maxWalk + 2, 1400))
        {
            why = "no floor under it";
            return null;
        }
        double hereSpawn = spawn == null ? 0 : Math.Sqrt(entity.Pos.SquareHorDistanceTo(spawn));
        Random rand = entity.World.Rand;
        bool heading = headingX != 0 || headingZ != 0;

        double total = 0;
        var weights = new List<(int Node, double W)>();
        for (int i = 1; i < search.Count; i++)
        {
            double cost = search.Cost(i);
            if (cost < minWalk || cost > maxWalk) continue;
            (double x, double z) = search.Centre(i);
            double dx = x - entity.Pos.X, dz = z - entity.Pos.Z, len = Math.Sqrt(dx * dx + dz * dz);
            if (len < 2) continue;
            double w = 1;
            // The middle of a hall rather than its edges, and never a pocket hemmed in on three sides
            int walls = search.WallsBeside(i);
            w *= walls switch { 0 => 3, 1 => 1.5, 2 => 1, 3 => 0.25, _ => 0.05 };
            // On the way it was going, mostly: along a corridor to its end, not to and fro
            if (heading) w *= Math.Exp(1.3 * (dx * headingX + dz * headingZ) / len);
            // A good walk rather than a shuffle
            w *= 0.5 + cost / maxWalk;
            // Home: within its range of where it was put down, and back toward it when it has strayed
            if (spawn != null)
            {
                double fromSpawn = Math.Sqrt((x - spawn.X) * (x - spawn.X) + (z - spawn.Z) * (z - spawn.Z));
                if (fromSpawn > maxDistanceToSpawn) w *= hereSpawn > maxDistanceToSpawn && fromSpawn < hereSpawn - 2 ? 1 : 0.03;
                else if (hereSpawn > maxDistanceToSpawn) w *= 4;
            }
            weights.Add((i, w));
            total += w;
        }
        if (weights.Count == 0)
        {
            why = $"nowhere {minWalk:0}-{maxWalk:0} steps off ({search.Count} cells of floor reached)";
            return null;
        }
        double pick = rand.NextDouble() * total;
        int chosen = weights[^1].Node;
        foreach ((int node, double w) in weights)
        {
            pick -= w;
            if (pick <= 0) { chosen = node; break; }
        }
        List<Vec3d> path = search.PathTo(chosen);
        (double cx, double cz) = search.Centre(chosen);
        why = null;
        if (!quiet) Log("ambles to {0:0.0},{1:0.0}: {2:0.0} steps, {3} legs, {4} walls beside it ({5} cells reached, {6} to choose from)",
            cx, cz, search.Cost(chosen), path.Count, search.WallsBeside(chosen), search.Count, weights.Count);
        return path;
    }

    /// <summary>
    /// For /backrooms facelingtest: where it would walk next from here, as the legs of the way, and how many of them
    /// cross anything solid at knee or chest height (none should).
    /// </summary>
    public string DryRun()
    {
        if (spawn == null) KeepSpawn(false);
        List<Vec3d> path = Plan(out string why, quiet: true);
        if (path == null) return "would stay put: " + why;
        var legs = new System.Text.StringBuilder();
        Vec3d from = entity.Pos.XYZ;
        int blocked = 0;
        foreach (Vec3d to in path)
        {
            if (!Senses.ClearLine(entity.World, from.AddCopy(0, 0.5, 0), to.AddCopy(0, 0.5, 0)) || !Senses.ClearLine(entity.World, from.AddCopy(0, 1.4, 0), to.AddCopy(0, 1.4, 0))) blocked++;
            legs.AppendFormat(" {0:0.0},{1:0.0}", to.X, to.Z);
            from = to;
        }
        return $"would walk {path.Count} legs ({blocked} through anything solid):{legs}";
    }

    // ---- Doing ----

    public override void StartExecute()
    {
        base.StartExecute();
        done = stuck = animOn = false;
        speed = moveSpeed * (0.85f + 0.3f * (float)entity.World.Rand.NextDouble());
        pathTraverser.Stop();
        Go(Step.Turn);
    }

    private void Go(Step next)
    {
        step = next;
        stepTime = 0;
    }

    public override bool ContinueExecute(float dt)
    {
        if (!entity.Alive || route == null || route.Count == 0) return false;
        if (menace != null && menace.Kind != Encounter.Ambient) return false;
        stepTime += dt;
        switch (step)
        {
            case Step.Turn:
                // Face the way first, then set off: no walking off in an arc into the wall beside it
                if (Turn(YawTo(route[0]), 2.4f, dt) < 0.2f || stepTime > 2)
                {
                    SetWalking(true);
                    pathTraverser.FollowRoute(route, speed, 0.3f, () => done = true, () => { done = true; stuck = true; });
                    Go(Step.Walk);
                }
                return true;

            case Step.Walk:
                if (!done && pathTraverser.Active) return true;
                SetWalking(false);
                pathTraverser.Stop();
                Vec3d last = route[^1];
                double hx = last.X - (route.Count > 1 ? route[^2].X : entity.Pos.X), hz = last.Z - (route.Count > 1 ? route[^2].Z : entity.Pos.Z);
                double len = Math.Sqrt(hx * hx + hz * hz);
                if (stuck)
                {
                    // Something in the way it did not know of (a door shut, someone standing there): try the other way
                    failures++;
                    if (len > 0) (headingX, headingZ) = (-hx / len, -hz / len);
                    Log("stuck on the way, {0} times running", failures);
                    return false;
                }
                failures = 0;
                if (len > 0) (headingX, headingZ) = (hx / len, hz / len);
                lookYaw = LookYaw();
                lookFor = 0.8f + 2.2f * (float)entity.World.Rand.NextDouble();
                Go(Step.Look);
                return true;

            case Step.Look:
                // At the end of the walk, it turns to look down the most open way, slowly, and stands a moment
                Turn(lookYaw, 1.2f, dt);
                return stepTime < lookFor;
        }
        return false;
    }

    /// <summary>The way to look at the end of a walk: down the longest stretch of floor, not back the way it came unless that is all there is.</summary>
    private float LookYaw()
    {
        var search = new FloorSearch(entity.World.BlockAccessor, bodyHeight);
        double best = -1;
        float yaw = entity.Pos.Yaw;
        for (int d = 0; d < 8; d++)
        {
            double angle = d * Math.PI / 4;
            double dx = Math.Sin(angle), dz = Math.Cos(angle);
            int run = search.OpenRun(entity.Pos.X, entity.Pos.Y, entity.Pos.Z, dx, dz, 10);
            double score = run;
            if (dx * headingX + dz * headingZ < -0.5) score *= 0.3; // (back the way it came)
            score += entity.World.Rand.NextDouble() * 1.5;
            if (score > best) { best = score; yaw = (float)angle; }
        }
        return yaw;
    }

    private float YawTo(Vec3d point) => (float)Math.Atan2(point.X - entity.Pos.X, point.Z - entity.Pos.Z);

    /// <summary>Turns toward a yaw at no more than <paramref name="ratePerSecond"/>; returns how far there is still to turn.</summary>
    private float Turn(float desired, float ratePerSecond, float dt)
    {
        float delta = GameMath.AngleRadDistance(entity.Pos.Yaw, desired);
        float stepBy = GameMath.Clamp(delta, -ratePerSecond * dt, ratePerSecond * dt);
        entity.Pos.Yaw = GameMath.Mod(entity.Pos.Yaw + stepBy, GameMath.TWOPI);
        return Math.Abs(delta - stepBy);
    }

    private void SetWalking(bool on)
    {
        if (walkAnim == null || animOn == on) return;
        animOn = on;
        if (on) entity.AnimManager.StartAnimation(walkAnim);
        else entity.AnimManager.StopAnimation(walkAnim);
    }

    public override void FinishExecute(bool cancelled)
    {
        base.FinishExecute(cancelled);
        pathTraverser.Stop();
        SetWalking(false);
        // (After getting stuck, think again soon, the other way; otherwise stand a while, as people do)
        if (stuck && failures < 4) cooldownUntilMs = entity.World.ElapsedMilliseconds + 600;
        route = null;
    }

    private void Log(string format, params object[] args)
    {
        if (director?.Logging == true) Strike.Log(entity, format, args);
    }
}

/// <summary>
/// A search over the floor round an entity, block by block: which cells it can stand in (floor below, nothing in the
/// way for its height, no water), which it can step between (up or down one block at most, never cutting a corner),
/// and the cheapest way to each, where floor beside a wall costs more to cross than floor in the open.
/// </summary>
internal sealed class FloorSearch
{
    private readonly IBlockAccessor ba;
    private readonly double height;
    private readonly BlockPos pos = new(0);
    private readonly Dictionary<long, double> footing = new();

    private readonly List<(int X, int Z, double Y)> cells = new();
    private readonly List<double> costs = new();
    private readonly List<int> parents = new();
    private readonly Dictionary<long, int> index = new();

    private static readonly (int X, int Z)[] Around = { (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1) };

    public FloorSearch(IBlockAccessor ba, double height)
    {
        this.ba = ba;
        this.height = height;
    }

    public int Count => cells.Count;

    public double Cost(int node) => costs[node];

    public (double X, double Z) Centre(int node) => (cells[node].X + 0.5, cells[node].Z + 0.5);

    private static long Key(int x, int y, int z) => ((long)(x & 0xFFFFFF) << 40) | ((long)(z & 0xFFFFFF) << 16) | (long)(y & 0xFFFF);

    private static long Key(int x, int z) => ((long)(x & 0xFFFFFFF) << 28) | (long)(z & 0xFFFFFFF);

    /// <summary>Searches outward from a position, up to a walking cost and a number of cells. False if it stands on no floor.</summary>
    public bool Run(double fx, double fy, double fz, double maxCost, int maxCells)
    {
        int sx = (int)Math.Floor(fx), sz = (int)Math.Floor(fz);
        double sy = StandNear(sx, fy, sz);
        if (double.IsNaN(sy)) return false;
        var open = new PriorityQueue<int, double>();
        Add(sx, sz, sy, 0, -1);
        open.Enqueue(0, 0);
        var closed = new HashSet<int>();
        while (open.TryDequeue(out int node, out double cost))
        {
            if (!closed.Add(node) || cost > costs[node] + 1e-9) continue;
            if (closed.Count > maxCells) break;
            (int x, int z, double y) = cells[node];
            for (int d = 0; d < Around.Length; d++)
            {
                (int dx, int dz) = Around[d];
                double ny = Step(x, z, y, x + dx, z + dz);
                if (double.IsNaN(ny)) continue;
                bool diagonal = dx != 0 && dz != 0;
                // A diagonal step only where both squares beside it are open too: no cutting a wall's corner
                if (diagonal && (double.IsNaN(Step(x, z, y, x + dx, z)) || double.IsNaN(Step(x, z, y, x, z + dz)))) continue;
                double stepCost = (diagonal ? 1.414 : 1) * (1 + 0.5 * WallsBeside(x + dx, z + dz, ny)) + Math.Abs(ny - y) * 0.5;
                double next = cost + stepCost;
                if (next > maxCost) continue;
                long key = Key(x + dx, z + dz);
                if (index.TryGetValue(key, out int existing))
                {
                    if (next >= costs[existing] - 1e-9) continue;
                    costs[existing] = next;
                    parents[existing] = node;
                    cells[existing] = (x + dx, z + dz, ny);
                    open.Enqueue(existing, next);
                }
                else
                {
                    open.Enqueue(Add(x + dx, z + dz, ny, next, node), next);
                }
            }
        }
        return true;
    }

    private int Add(int x, int z, double y, double cost, int parent)
    {
        cells.Add((x, z, y));
        costs.Add(cost);
        parents.Add(parent);
        index[Key(x, z)] = cells.Count - 1;
        return cells.Count - 1;
    }

    /// <summary>The way to a cell, as points to walk to (the start left out), with straight runs merged.</summary>
    public List<Vec3d> PathTo(int node)
    {
        var chain = new List<int>();
        for (int n = node; n > 0; n = parents[n]) chain.Add(n);
        chain.Reverse();
        var points = new List<Vec3d>();
        int lastDx = int.MinValue, lastDz = int.MinValue, prev = 0;
        for (int i = 0; i < chain.Count; i++)
        {
            int n = chain[i];
            int dx = cells[n].X - cells[prev].X, dz = cells[n].Z - cells[prev].Z;
            bool flat = Math.Abs(cells[n].Y - cells[prev].Y) < 0.01;
            // (A point in the middle of a straight, level run says nothing: the next one replaces it)
            if (points.Count > 0 && dx == lastDx && dz == lastDz && flat) points.RemoveAt(points.Count - 1);
            points.Add(new Vec3d(cells[n].X + 0.5, cells[n].Y, cells[n].Z + 0.5));
            lastDx = dx;
            lastDz = dz;
            prev = n;
        }
        return points;
    }

    /// <summary>How many of the eight squares round a reached cell cannot be stood in from it.</summary>
    public int WallsBeside(int node) => WallsBeside(cells[node].X, cells[node].Z, cells[node].Y);

    private int WallsBeside(int x, int z, double y)
    {
        int walls = 0;
        for (int d = 0; d < 4; d++)
            if (double.IsNaN(Step(x, z, y, x + Around[d].X, z + Around[d].Z))) walls++;
        return walls;
    }

    /// <summary>How many squares of floor run straight out from a position in a direction, up to a limit.</summary>
    public int OpenRun(double fx, double fy, double fz, double dx, double dz, int limit)
    {
        int x = (int)Math.Floor(fx), z = (int)Math.Floor(fz);
        double y = StandNear(x, fy, z);
        if (double.IsNaN(y)) return 0;
        for (int i = 1; i <= limit; i++)
        {
            int nx = (int)Math.Floor(fx + dx * i), nz = (int)Math.Floor(fz + dz * i);
            if (nx == x && nz == z) continue;
            double ny = Step(x, z, y, nx, nz);
            if (double.IsNaN(ny)) return i - 1;
            (x, z, y) = (nx, nz, ny);
        }
        return limit;
    }

    /// <summary>The height it would stand at stepping from one square to the next (up or down a block at most), or NaN.</summary>
    private double Step(int x, int z, double y, int nx, int nz)
    {
        if (Math.Abs(nx - x) > 1 || Math.Abs(nz - z) > 1) return double.NaN;
        int by = (int)Math.Floor(y + 0.01);
        // Level first; then a step up or down, whichever is nearer
        double s = Stand(nx, by, nz);
        if (Reach(s, y)) return s;
        double up = Stand(nx, by + 1, nz), down = Stand(nx, by - 1, nz);
        bool canUp = Reach(up, y), canDown = Reach(down, y);
        if (canUp && canDown) return Math.Abs(up - y) <= Math.Abs(down - y) ? up : down;
        return canUp ? up : canDown ? down : double.NaN;
    }

    /// <summary>Whether a height can be stepped to from another (a block up or down at most, as its step height allows).</summary>
    private static bool Reach(double to, double from) => !double.IsNaN(to) && Math.Abs(to - from) <= 1.05;

    private double StandNear(int x, double fy, int z)
    {
        int by = (int)Math.Floor(fy + 0.01);
        double s = Stand(x, by, z);
        if (double.IsNaN(s)) s = Stand(x, by - 1, z);
        if (double.IsNaN(s)) s = Stand(x, by + 1, z);
        return s;
    }

    /// <summary>
    /// The height an entity would stand at with its feet in block y of a column, or NaN: something underfoot (a
    /// floor, or a low thing in the block itself, like a slab or a carpet), nothing in the way for its whole height,
    /// and no water.
    /// </summary>
    private double Stand(int x, int y, int z)
    {
        long key = Key(x, y, z);
        if (footing.TryGetValue(key, out double known)) return known;
        double s = double.NaN;
        double feetTop = Top(x, y, z);
        if (feetTop <= 0.55)
        {
            if (feetTop > 0) s = y + feetTop;
            else
            {
                double below = Top(x, y - 1, z);
                if (below >= 0.45) s = y - 1 + below;
            }
            if (!double.IsNaN(s) && (!Clear(x, z, s, s + height) || Wet(x, (int)Math.Floor(s + 0.1), z))) s = double.NaN;
        }
        footing[key] = s;
        return s;
    }

    /// <summary>The top of what can be collided with in a block (0 for nothing; above 1 for a fence).</summary>
    private double Top(int x, int y, int z)
    {
        Cuboidf[] boxes = ba.GetBlock(pos.Set(x, y, z)).GetCollisionBoxes(ba, pos);
        if (boxes == null || boxes.Length == 0) return 0;
        double top = 0;
        foreach (Cuboidf box in boxes) top = Math.Max(top, box.Y2);
        return top;
    }

    /// <summary>Whether nothing collidable lies in a column between two heights.</summary>
    private bool Clear(int x, int z, double from, double to)
    {
        for (int by = (int)Math.Floor(from); by <= (int)Math.Floor(to - 0.001); by++)
        {
            Cuboidf[] boxes = ba.GetBlock(pos.Set(x, by, z)).GetCollisionBoxes(ba, pos);
            if (boxes == null) continue;
            foreach (Cuboidf box in boxes)
                if (by + box.Y2 > from + 0.02 && by + box.Y1 < to) return false;
        }
        return true;
    }

    private bool Wet(int x, int y, int z) => ba.GetBlock(pos.Set(x, y, z), BlockLayersAccess.Fluid).BlockId != 0;
}
