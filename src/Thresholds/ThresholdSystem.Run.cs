using Backrooms.Regions;
using Backrooms.Worldgen;
using Vintagestory.API.Server;

namespace Backrooms.Thresholds;

/// <summary>
/// What happens round Level !'s thresholds in the game (kept as level 14):
/// <list type="bullet">
/// <item>Each runner gets a hallway of their own: a way in leads to one lane's start room, but if someone is already
/// running that lane (or someone came through just before, together), they are put in the next free one ("when
/// multiple people enter the level at the same time, they will be forced to separate").</item>
/// <item>Whoever has escaped once is never taken again: every way in "will only reach another location in the level he
/// was in".</item>
/// <item>Whoever goes out through a true exit leaves a red door where they come out (<see cref="RunSystem.NoteEscape"/>).</item>
/// </list>
/// </summary>
public partial class ThresholdSystem
{
    private void RunArriving(IServerPlayer player, Link link, ref double drop)
    {
    }

    private Link? RunRedirect(IServerPlayer player, Passage passage, Link destination)
    {
        var run = sapi.ModLoader.GetModSystem<RunSystem>();
        if (run == null || layout == null) return null;
        int fromLevel = layout.LevelAt(WorldLayout.MacroOf(passage.Source.X), WorldLayout.MacroOf(passage.Source.Z));
        int toLevel = layout.LevelAt(WorldLayout.MacroOf((int)System.Math.Floor(destination.X)), WorldLayout.MacroOf((int)System.Math.Floor(destination.Z)));

        if (fromLevel == WorldLayout.RunLevel && toLevel != WorldLayout.RunLevel)
        {
            // Only the true exit is an escape (and leaves its red door); falling down a hole is not
            if (layout.TileAt(passage.Source.X, passage.Source.Z).Pattern != WallPattern.RunTrueExit) return null;
            // They come out in front of an ordinary door, which becomes the red one
            Link out_ = run.NoteEscape(player, destination);
            return out_ == destination ? null : out_;
        }
        if (toLevel != WorldLayout.RunLevel || fromLevel == WorldLayout.RunLevel) return null;

        if (RunSystem.HasRanOut(player.Entity))
        {
            // Never again: somewhere else in the level they were in, the same place every time for this door
            int here = layout.LevelAt(WorldLayout.MacroOf((int)System.Math.Floor(player.Entity.Pos.X)), WorldLayout.MacroOf((int)System.Math.Floor(player.Entity.Pos.Z)));
            passage.Message = "backrooms:run-ranout";
            passage.Sound = null;
            if (layout.FindArrival(here, passage.Key) is not { } elsewhere) return new Link(player.Entity.Pos.X, player.Entity.Pos.Y, player.Entity.Pos.Z, false);
            return new Link(elsewhere.X + 0.5, geometry.FloorFor(here) + layout.ArrivalHeight(elsewhere.X, elsewhere.Z), elsewhere.Z + 0.5, false);
        }

        int lane = layout.RunLaneAt((int)System.Math.Floor(destination.X), (int)System.Math.Floor(destination.Z));
        int claimed = run.ClaimLane(player, lane);
        if (claimed == lane || claimed < 0) return null;
        var (ax, az) = layout.RunWorld(claimed, layout.RunPlan(claimed).Arrival.X, layout.RunPlan(claimed).Arrival.Z);
        return new Link(ax + 0.5, geometry.FloorFor(WorldLayout.RunLevel) + layout.ArrivalHeight(ax, az), az + 0.5, false);
    }

    private bool RunMayPass(IServerPlayer player, Passage passage) => true;

    /// <summary>Level !'s doors that are not ways anywhere: handled by <see cref="RunSystem.UseDoor"/>. True if this was one.</summary>
    private bool RunUse(IServerPlayer player, Vintagestory.API.MathTools.BlockPos pos, string kind)
    {
        if (kind is not ("runhall" or "runchained" or "runmarked" or "runside" or "runlocked" or "runfake")) return false;
        busyUntilMs[player.PlayerUID] = sapi.World.ElapsedMilliseconds + 400;
        sapi.ModLoader.GetModSystem<RunSystem>()?.UseDoor(player, pos, kind);
        return true;
    }
}
