using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level 52, "The Greenfield Campus"'s thresholds in the game (experimental, kept as level 23; its ways in
/// and back are ThresholdNetwork.L52.cs's): someone who comes in by a campus door faces into the building, as if just come
/// through it; anyone else faces into the open. This file is the level's own.
/// </summary>
public partial class ThresholdSystem
{
    /// <summary>Someone is about to be put down in the level at <paramref name="link"/>.</summary>
    private void L52Arriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    /// <summary>
    /// The way someone put down in the level at (x, z) faces: away from a campus door they are put down just inside (they
    /// came in by it); else the cardinal heading with the longest clear run (up to 40 blocks), so a corridor is looked along
    /// and a lawn across, never a wall point-blank; null where nothing is open.
    /// </summary>
    private float? L52ArrivalYaw(int x, int z)
    {
        int best = 0;
        float yaw = 0;
        Tile here = layout.TileAt(x, z);
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
            if (layout.TileAt(x + dx, z + dz).Under is Unders.L52QuadDoor or Unders.L52WingDoor && here.Depth > 0)
                return (float)System.Math.Atan2(-dx, -dz);
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            int run = 0;
            while (run < 40)
            {
                Tile t = layout.TileAt(x + dx * (run + 1), z + dz * (run + 1));
                if (t.Level != WorldLayout.Level52 || t.Kind is not (TileKind.Floor or TileKind.Doorway) || t.Variant != 0 || t.Height > here.Height + 1) break;
                run++;
            }
            // A player looks along (sin yaw, cos yaw)
            if (run > best) { best = run; yaw = (float)System.Math.Atan2(dx, dz); }
        }
        return best > 0 ? yaw : null;
    }

    /// <summary>Just before any arrival anywhere: somewhere else to send them, or null.</summary>
    private Link? L52Redirect(IServerPlayer player, Passage passage, Link destination) => null;

    /// <summary>Whether a threshold someone has walked into lets them through now.</summary>
    private bool L52MayPass(IServerPlayer player, Passage passage) => true;

    /// <summary>
    /// (Dev test, <c>/backrooms l52 waytest school|exit|x z</c>, Regions.L52System) Goes in by a way into Level 52 as someone
    /// standing in front of it would (the high school nearest spawn, the EMERGENCY EXIT nearest spawn, or the door at x z),
    /// then out again through the campus door beside the arrival as someone walking through it would, and says where each
    /// leads, whether the way back is home, and what blocks stand at the way in and at the door out (run it twice: the first
    /// time may only load the chunks).
    /// </summary>
    internal string L52WayTest(string what, int x, int z)
    {
        if (network == null || layout == null) return "Not a Backrooms world";
        if (what == "school" && layout.L52NearestSchools(1) is { Count: > 0 } schools) (x, z) = (schools[0].DoorX, schools[0].DoorZ);
        else if (what == "exit" && layout.L52NearestExits(1) is { Count: > 0 } exits) (x, z) = (exits[0].X, exits[0].Z);
        Tile here = layout.TileAt(x, z);
        var sb = new System.Text.StringBuilder($"way in at {x},{z} (level {here.Level}, under {here.Under}): ");
        var a = sapi.World.BlockAccessor;
        int loading = 0;
        string Column(int cx, int cz, int level)
        {
            int floor = geometry.FloorFor(level);
            if (a.GetChunk(cx / Vintagestory.API.Config.GlobalConstants.ChunkSize, floor / Vintagestory.API.Config.GlobalConstants.ChunkSize,
                    cz / Vintagestory.API.Config.GlobalConstants.ChunkSize) == null)
            {
                loading++;
                sapi.WorldManager.LoadChunkColumnPriority(cx / Vintagestory.API.Config.GlobalConstants.ChunkSize, cz / Vintagestory.API.Config.GlobalConstants.ChunkSize);
                return "(loading: run again)";
            }
            var parts = new System.Collections.Generic.List<string>();
            for (int rel = 0; rel <= 3; rel++)
                parts.Add(a.GetBlock(new Vintagestory.API.MathTools.BlockPos(cx, floor + rel, cz))?.Code?.Path ?? "unloaded");
            return string.Join(" / ", parts);
        }
        sb.Append($"blocks rel 0-3 {Column(x, z, here.Level)}; ");
        Passage passage = network.Used(x, z, "l52-door", out string refusal);
        if (passage == null) return sb.Append($"leads nowhere ({refusal})").ToString();
        Link home = network.HomeBeside(passage.Source) ?? new Link(x + 0.5, geometry.FloorFor(here.Level) + 1.05, z + 0.5, false);
        if (network.Take(passage, home) is not { } to) return sb.Append("found nowhere to lead").ToString();
        int ax = (int)System.Math.Floor(to.X), az = (int)System.Math.Floor(to.Z);
        Tile at = layout.TileAt(ax, az);
        sb.Append($"leads to {to.X:0.0},{to.Y:0.0},{to.Z:0.0} (level {at.Level}, zone {at.Zone}{(to.Marker ? ", a thin spot" : "")}); arrival rel 0-3 {Column(ax, az, at.Level)}; ");
        // Out through the campus door beside the arrival, as someone walking through it
        foreach (var (dx, dz) in new[] { (0, 1), (1, 0), (0, -1), (-1, 0) })
        {
            Tile d = layout.TileAt(ax + dx, az + dz);
            if (d.Under is not (Unders.L52QuadDoor or Unders.L52WingDoor)) continue;
            Passage back = network.Walked(ax + dx, az + dz, d, 1.0);
            if (back == null) return sb.Append($"the door at {ax + dx},{az + dz} does NOT lead back").ToString();
            Link? there = network.Take(back, network.HomeFor(back));
            bool homeOk = there is { } t && System.Math.Abs(t.X - home.X) < 0.01 && System.Math.Abs(t.Z - home.Z) < 0.01;
            return sb.Append($"out through the door at {ax + dx},{az + dz} (rel 0-3 {Column(ax + dx, az + dz, at.Level)}): leads to {(there is { } lt ? $"{lt.X:0.0},{lt.Y:0.0},{lt.Z:0.0}" : "nowhere")} ({back.Message}), "
                + (homeOk ? "home, beside the way in" : "NOT home")).ToString();
        }
        return sb.Append("no campus door beside the arrival").ToString();
    }
}
