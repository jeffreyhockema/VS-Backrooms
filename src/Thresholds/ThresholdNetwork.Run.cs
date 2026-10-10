using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// Level !'s thresholds (kept as level 14): the ways into it from other levels, and the ways out of it. Every way in is
/// taken, not walked (the door slams and locks behind you; canon's "!" on its inside), so every one is one-way; and so is
/// the way out ("the Backrooms will never send you there again"). Salts 0x14C0-0x14FF.
///
/// <list type="bullet">
/// <item>Level 1: a red EXIT door where no door should be (<see cref="Unders.RunEntrance"/>), kind <c>runentry</c>.</item>
/// <item>Level 2: a dead end that wasn't there a moment ago (<see cref="Unders.RunFalseWall"/>): walk into it, kind
/// <c>runfalsewall</c> (the runtime notices someone standing in the block, since walked thresholds are not looked for
/// in Level 2).</item>
/// <item>Level 37: the red corridor's EXIT door, kind <c>runentry</c>; and the door left at every exit's arrival.</item>
/// <item>Out: the true exit at the end of a lane (kind <c>runexit</c>) to Level 1, Level 4 or The End, fixed per lane;
/// a hole in the dark last stretch, down into Level 8.</item>
/// </list>
/// Which lane a way in leads to, and the runner who has escaped once, are settled just before arrival
/// (<c>ThresholdSystem.RunRedirect</c>).
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here.</summary>
    private const ulong SaltRunThreshold = 0x14C0;

    /// <summary>The sound of the door you came in by slamming shut behind you.</summary>
    public const string RunSlamSound = "backrooms:sounds/effect/run/slam";

    private Passage RunWalked(int x, int z, in Tile tile, double rel)
    {
        if (tile.Level == WorldLayout.RunLevel && tile.Kind == TileKind.Pit && tile.Under == Unders.RunHole && rel < -1.5)
        {
            // Through the hole and down through dust and rubble into the caves
            var hole = layout.FeatureOrigin(x, z, t => t.Level == WorldLayout.RunLevel && t.Under == Unders.RunHole);
            return new Passage { Source = hole, Key = KeyOf(hole, SaltRunThreshold + 1), Find = In(8), Message = "backrooms:run-fell" };
        }
        return null;
    }

    private Passage RunUsed(int x, int z, int level, string kind, ref string refusal)
    {
        switch (kind)
        {
            case "runentry":
            case "runfalsewall":
                // Into a start room of Level ! (the lane is settled on arrival); the door slams behind you
                return new Passage
                {
                    Source = (x, z), Key = KeyOf((x, z), SaltRunThreshold + (kind == "runentry" ? 2UL : 3UL)), Find = IntoRun(),
                    Message = "backrooms:run-arrive", Sound = RunSlamSound,
                };
            case "runexit":
            {
                // The true exit: where it leads is fixed for the lane, and there is no coming back
                int lane = layout.RunLaneAt(x, z);
                if (lane < 0) { refusal = "nowhere"; return null; }
                int to = layout.RunPlan(lane).Destination;
                bool BesideWall(Tile t) => t.Kind == TileKind.Wall;
                return new Passage
                {
                    Source = (x, z), Key = KeyOf((x, z), SaltRunThreshold + 4),
                    Find = to == WorldLayout.TheEnd ? IntoEnd() : In(to, BesideWall),
                    Message = "backrooms:run-escaped", Sound = "game:sounds/block/door",
                };
            }
        }
        return null;
    }

    /// <summary>Somewhere to arrive in the level for a key: always a start room (beside the bed, the chained door ahead).</summary>
    private System.Func<ulong, (int X, int Z, double Height)?> IntoRun(System.Func<Tile, bool> beside = null) => In(WorldLayout.RunLevel, beside);
}
