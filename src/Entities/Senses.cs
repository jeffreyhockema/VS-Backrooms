using System;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;

namespace Backrooms.Entities;

/// <summary>
/// What entities can tell about the world and the people in it: light (the world's and what a player carries), who
/// can see whom, whether someone is running or looking straight at something, and where the fires are.
/// </summary>
public static class Senses
{
    /// <summary>Light at or above this keeps Smilers back: a torch, a lantern, a fire, a working lamp. A candle is not enough.</summary>
    public const int LitLevel = 8;

    /// <summary>How bright the light a player carries is (0 to about 20; a candle is 7, a torch 14, a lantern 18).</summary>
    public static int HeldLight(Entity entity)
    {
        if (entity is not EntityAgent agent) return 0;
        // (Players also glow for a while after respawning; only what is in the hands counts here)
        return Math.Max(LightOf(entity.World, RightHand(agent)), LightOf(entity.World, LeftHand(agent)));
    }

    /// <summary>
    /// What an agent holds in its right hand, or nothing. A player entity whose player is not attached (still joining,
    /// or just gone) throws on its hand slots, so it counts as empty-handed here.
    /// </summary>
    public static ItemSlot RightHand(EntityAgent agent) => agent is EntityPlayer { Player: null } ? null : agent.RightHandItemSlot;

    /// <summary>What an agent holds in its left hand, or nothing (see <see cref="RightHand"/>).</summary>
    public static ItemSlot LeftHand(EntityAgent agent) => agent is EntityPlayer { Player: null } ? null : agent.LeftHandItemSlot;

    /// <summary>How bright what lies in a slot burns (0 for nothing, or nothing alight).</summary>
    private static int LightOf(IWorldAccessor world, ItemSlot slot)
    {
        ItemStack stack = slot?.Itemstack;
        if (stack?.Collectible == null) return 0;
        return stack.Collectible.GetLightHsv(world.BlockAccessor, null, stack)?[2] ?? 0;
    }

    /// <summary>
    /// Whether a Reality Shift has the lights out. The blocks still glow (the Shift is drawn on the client), so the
    /// world's light is taken as gone and only what people carry counts: which is what makes a torch matter then.
    /// Set by the director each tick.
    /// </summary>
    public static bool LightsOut;

    /// <summary>The world's own light at a position (lamps and fires, and daylight where there is sky); none while the lights are out.</summary>
    public static int WorldLight(IWorldAccessor world, Vec3d pos) => LightsOut ? 0 :
        world.BlockAccessor.GetLightLevel((int)Math.Floor(pos.X), (int)Math.Floor(pos.Y), (int)Math.Floor(pos.Z), EnumLightLevelType.MaxTimeOfDayLight);

    /// <summary>
    /// How bright a position is, counting the light the given people carry: carried light falls off by a level a
    /// block, as block light does.
    /// </summary>
    public static int LightAt(IWorldAccessor world, Vec3d pos, Entity[] carriers)
    {
        int light = WorldLight(world, pos);
        foreach (Entity carrier in carriers) light = WithCarried(light, carrier, pos);
        return light;
    }

    /// <summary>How bright a position is, counting the light one person carries.</summary>
    public static int LightAt(IWorldAccessor world, Vec3d pos, Entity carrier) => WithCarried(WorldLight(world, pos), carrier, pos);

    private static int WithCarried(int light, Entity carrier, Vec3d pos)
    {
        int held = HeldLight(carrier);
        if (held <= light) return light;
        double distance = carrier.Pos.DistanceTo(pos);
        return Math.Max(light, held - (int)Math.Ceiling(distance));
    }

    /// <summary>Whether a player stands in the dark: no light worth the name around them or in their hands.</summary>
    public static bool InDark(Entity player)
    {
        Vec3d eyes = player.Pos.XYZ.Add(0, player.LocalEyePos.Y, 0);
        return HeldLight(player) < LitLevel && WorldLight(player.World, eyes) < LitLevel;
    }

    /// <summary>
    /// How much the light a player carries draws Deathmoths: an open flame most, a candle a little, a closed lantern
    /// not at all.
    /// </summary>
    public static double MothDraw(EntityAgent player) =>
        Math.Max(MothDraw(player.World, RightHand(player)), MothDraw(player.World, LeftHand(player)));

    private static double MothDraw(IWorldAccessor world, ItemSlot slot)
    {
        string path = slot?.Itemstack?.Collectible?.Code?.Path;
        if (path == null || LightOf(world, slot) == 0) return 0;
        return path.StartsWith("torch") ? 1.0 : path.StartsWith("oillamp") ? 0.5 : path.StartsWith("candle") ? 0.3 : path.StartsWith("lantern") ? 0 : 0.6;
    }

    /// <summary>The floor height (the y an entity stands at) of a column near a height, or int.MinValue.</summary>
    public static int FindFloor(IWorldAccessor world, int x, int nearY, int z, int headroom = 2, int reach = 10)
    {
        IBlockAccessor ba = world.BlockAccessor;
        var pos = new BlockPos(0);
        for (int dy = 0; dy <= reach; dy++)
        {
            for (int sign = dy == 0 ? 1 : -1; sign <= 1; sign += 2)
            {
                int y = nearY + sign * dy;
                // (Never far up: that would be the floor of something above)
                if (sign > 0 && dy > 6) continue;
                if (!ba.GetBlock(pos.Set(x, y - 1, z)).SideSolid[BlockFacing.UP.Index]) continue;
                bool open = true;
                for (int h = 0; h < headroom && open; h++) open = Open(ba, pos.Set(x, y + h, z));
                if (open) return y;
            }
        }
        return int.MinValue;
    }

    /// <summary>Whether a block can be walked or flown through: nothing to collide with, and no water.</summary>
    public static bool Open(IBlockAccessor ba, BlockPos pos)
    {
        Block block = ba.GetBlock(pos);
        if (block.CollisionBoxes != null && block.CollisionBoxes.Length > 0) return false;
        return ba.GetBlock(pos, BlockLayersAccess.Fluid).BlockId == 0;
    }

    /// <summary>Whether a player is running (sprinting while moving).</summary>
    public static bool Running(EntityAgent player) => player.ServerControls.Sprint && player.ServerControls.TriesToMove;

    /// <summary>A player's Reality Stability (1 is steady, 0 is coming apart).</summary>
    public static double Stability(Entity player) => player.WatchedAttributes.GetDouble("temporalStability", 1);

    /// <summary>The middle of an entity, where eyes are drawn to and rays are cast at.</summary>
    public static Vec3d Centre(Entity entity) => entity.Pos.XYZ.Add(0, entity.SelectionBox.Y2 * 0.6, 0);

    public static Vec3d Eyes(Entity entity) => entity.Pos.XYZ.Add(0, entity.LocalEyePos.Y, 0);

    /// <summary>Whether nothing solid lies on the straight line between two points.</summary>
    public static bool ClearLine(IWorldAccessor world, Vec3d from, Vec3d to)
    {
        BlockSelection blockSel = null;
        EntitySelection entitySel = null;
        world.RayTraceForSelection(from, to, ref blockSel, ref entitySel, (pos, block) => block.CollisionBoxes != null && block.CollisionBoxes.Length > 0 && block.Replaceable < 6000, e => false);
        return blockSel == null;
    }

    /// <summary>Whether a player could see an entity right now: in front of them, within range, nothing in the way.</summary>
    public static bool Sees(Entity player, Entity entity, double range = 48, double halfAngleDeg = 55)
    {
        Vec3d eyes = Eyes(player), centre = Centre(entity);
        double distance = eyes.DistanceTo(centre);
        if (distance > range) return false;
        if (distance > 1.5 && AngleTo(player, centre) > halfAngleDeg) return false;
        return ClearLine(player.World, eyes, centre);
    }

    /// <summary>Whether a player is looking more or less straight at a point (within a few degrees, for a stare).</summary>
    public static bool LooksAt(Entity player, Vec3d point, double halfAngleDeg = 12) => AngleTo(player, point) <= halfAngleDeg;

    /// <summary>The angle, in degrees, between where a player looks and the direction to a point.</summary>
    public static double AngleTo(Entity player, Vec3d point)
    {
        Vec3f view = player.Pos.GetViewVector();
        Vec3d eyes = Eyes(player);
        double dx = point.X - eyes.X, dy = point.Y - eyes.Y, dz = point.Z - eyes.Z;
        double length = Math.Sqrt(dx * dx + dy * dy + dz * dz) * Math.Sqrt(view.X * view.X + view.Y * view.Y + view.Z * view.Z);
        if (length < 1e-6) return 0;
        double cos = (dx * view.X + dy * view.Y + dz * view.Z) / length;
        return Math.Acos(Math.Clamp(cos, -1, 1)) * 180 / Math.PI;
    }
}

/// <summary>
/// Things that keep the hunters off: a lit firepit, a handful of burning Firesalt, an angel statue. A small cache keeps
/// the block scans cheap when several entities ask about the same place.
/// </summary>
public static class Wards
{
    /// <summary>How far a ward reaches.</summary>
    public const int Radius = 8;

    private static readonly Dictionary<(int, int, int), (long At, Vec3d[] Wards)> Cache = new();

    /// <summary>Whether a block is a ward.</summary>
    public static bool IsWard(Block block)
    {
        if (block?.Code == null) return false;
        string path = block.Code.Path;
        if (block.Code.Domain == "game") return path == "firepit-lit";
        return block.Code.Domain == "backrooms" && (path.StartsWith("firesalt") || path.StartsWith("angelstatue"));
    }

    /// <summary>The nearest ward within reach of a position, or null.</summary>
    public static Vec3d Near(IWorldAccessor world, Vec3d pos)
    {
        Vec3d best = null;
        double bestDistance = double.MaxValue;
        foreach (Vec3d ward in Around(world, pos))
        {
            double d = ward.SquareDistanceTo(pos);
            if (d < bestDistance) { bestDistance = d; best = ward; }
        }
        return best;
    }

    private static readonly Vec3d[] NoWards = Array.Empty<Vec3d>();

    /// <summary>Every ward within reach of the 4-block cell a position lies in.</summary>
    private static Vec3d[] Around(IWorldAccessor world, Vec3d pos)
    {
        int cx = (int)Math.Floor(pos.X) >> 2, cy = (int)Math.Floor(pos.Y) >> 2, cz = (int)Math.Floor(pos.Z) >> 2;
        long now = world.ElapsedMilliseconds;
        lock (Cache)
        {
            // (A time in the future is one left from an earlier server in this process)
            if (Cache.TryGetValue((cx, cy, cz), out var hit) && now - hit.At < 2500 && hit.At <= now) return hit.Wards;
            if (Cache.Count > 4096) Cache.Clear();
        }

        // Scan around the middle of the 4-block cell, a little further than a ward reaches, so the answer holds anywhere in it
        int x0 = (cx << 2) + 2, y0 = (cy << 2) + 2, z0 = (cz << 2) + 2, r = Radius + 2;
        IBlockAccessor ba = world.BlockAccessor;
        var at = new BlockPos(0);
        List<Vec3d> found = null;
        for (int y = y0 - 5; y <= y0 + 4; y++)
        {
            for (int z = z0 - r; z <= z0 + r; z++)
            {
                for (int x = x0 - r; x <= x0 + r; x++)
                {
                    at.Set(x, y, z);
                    if (!IsWard(ba.GetBlock(at))) continue;
                    (found ??= new List<Vec3d>()).Add(new Vec3d(x + 0.5, y + 0.5, z + 0.5));
                }
            }
        }
        Vec3d[] wards = found?.ToArray() ?? NoWards;
        lock (Cache) Cache[(cx, cy, cz)] = (now, wards);
        return wards;
    }

    /// <summary>Whether a position lies within reach of a ward.</summary>
    public static bool Warded(IWorldAccessor world, Vec3d pos, double radius = Radius)
    {
        foreach (Vec3d ward in Around(world, pos))
            if (ward.HorizontalSquareDistanceTo(pos.X, pos.Z) <= radius * radius && Math.Abs(ward.Y - pos.Y) < 4) return true;
        return false;
    }

    /// <summary>Forgets what is cached around a position (a fire was lit or put out there).</summary>
    public static void Invalidate() { lock (Cache) Cache.Clear(); }
}
