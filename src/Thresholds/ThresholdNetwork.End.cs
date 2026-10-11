using System;
using Backrooms.Worldgen;

namespace Backrooms.Thresholds;

/// <summary>
/// The End's thresholds (kept as level 16): the ways out of it, and the ways into it from any other level
/// (docs/new-levels/end-plan.md, as reconciled in LINKS.md). Walked through, two-way; fell, dived or taken, one-way.
///
/// In: a locked door under a glowing EXIT sign in Level 1's halls, and the closed-down bookstore's door in the city
/// (both two-way, out beside one of The End's EXIT doors, which becomes the way back); a lone wooden doorway in Level 4
/// (one-way: it is gone once you are through). Level ! and the Hub send people in beside an EXIT door
/// (<see cref="EndExitArrival"/>), one-way.
///
/// Out: The End's EXIT doors (two in three never open; each that does always leads to the same place: Level 1, the
/// Hub beside a service door, the city's bookstore, the Office or the hotel); a fake reality's real door (to the level
/// it imitates); a stockroom's vent (Level 94, falling from the sky); a computer that says "=)" (Level Fun, taken);
/// walking into a wall during a distortion (the scene it showed).
/// </summary>
public sealed partial class ThresholdNetwork
{
    /// <summary>Hash salts for the level's thresholds start here.</summary>
    private const ulong SaltEndThreshold = 0x16C0;

    /// <summary>One of The End's EXIT doors.</summary>
    public static readonly Func<Tile, bool> EndExitDoor = WorldLayout.IsEndExitDoor;

    /// <summary>Level 1's locked door under an EXIT sign that opens onto The End.</summary>
    private static readonly Func<Tile, bool> EndLevel1Door = t => t.Kind == TileKind.Door && t.Under == Unders.EndExitL1;

    /// <summary>The city bookstore's glass door.</summary>
    private static readonly Func<Tile, bool> EndStoreDoor = t => t.Kind == TileKind.Door && t.Under == Unders.EndBookstore;

    /// <summary>A grey service door in the Hub (its way back to wherever came in beside it).</summary>
    private static readonly Func<Tile, bool> EndHubServiceDoor = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.HubServiceDoor;

    /// <summary>
    /// Somewhere to arrive in the level for a key, beside a tile matching <paramref name="beside"/> where one can be found;
    /// by default beside one of its EXIT doors (LINKS.md: Level ! and the Hub send people in that way).
    /// </summary>
    private Func<ulong, (int X, int Z, double Height)?> IntoEnd(Func<Tile, bool> beside = null) => In(WorldLayout.TheEnd, beside ?? EndExitDoor);

    /// <summary>Arriving in The End beside one of its EXIT doors (for Level ! and the Hub's End door, which send people in that way).</summary>
    internal Func<ulong, (int X, int Z, double Height)?> EndExitArrival() => IntoEnd(EndExitDoor);

    /// <summary>Whether an EXIT door of The End opens: one in three does, and any that something has come back through.</summary>
    public bool EndExitOpens(int x, int z)
    {
        var door = layout.FeatureOrigin(x, z, EndExitDoor);
        return TryGet(door, out _) || Hashing.Unit(KeyOf(door, SaltEndThreshold + 1)) < 1 / 3.0;
    }

    private Passage EndWalked(int x, int z, in Tile tile, double rel)
    {
        int level = tile.Level;
        if (level == WorldLayout.TheEnd && tile.Under == Unders.EndFakeDoor && tile.Kind == TileKind.Doorway && rel < 2)
        {
            // A fake reality's real door: out into the level it imitates, and back the same way
            var door = layout.FeatureOrigin(x, z, t => t.Under == Unders.EndFakeDoor);
            ulong key = KeyOf(door, SaltEndThreshold + 2);
            (int target, Func<Tile, bool> partner) = (WorldLayout.EndFake)tile.Detail switch
            {
                WorldLayout.EndFake.Office => (4, (Func<Tile, bool>)null),
                WorldLayout.EndFake.Hotel => (5, PlainDoor),
                WorldLayout.EndFake.House => (9, PlainDoor),
                _ => (0, null),
            };
            Passage passage = BothWays(door, key, target, partner);
            passage.Message = "backrooms:endfake-door";
            return passage;
        }
        if (level == 4 && tile.Under == Unders.EndFrame && rel > -0.5 && rel < 2)
        {
            // Through the lone wooden doorway: it is not there behind you
            var frame = layout.FeatureOrigin(x, z, t => t.Under == Unders.EndFrame);
            Passage passage = OneWay(frame, KeyOf(frame, SaltEndThreshold + 3), WorldLayout.TheEnd);
            passage.Message = "backrooms:endframe";
            passage.Sound = "game:sounds/effect/translocate-breakdimension";
            return passage;
        }
        return null;
    }

    private Passage EndUsed(int x, int z, int level, string kind, ref string refusal)
    {
        Tile here = layout.TileAt(x, z);
        // Our doors in other levels, whatever kind their block says
        if (level == 1 && EndLevel1Door(here) || kind == "endexit" && level != WorldLayout.TheEnd)
        {
            var door = layout.FeatureOrigin(x, z, EndLevel1Door);
            Passage passage = BothWays(door, KeyOf(door, SaltEndThreshold + 4), WorldLayout.TheEnd, EndExitDoor);
            passage.Message = "backrooms:endexit-arrive";
            return WithSound(passage, "game:sounds/block/door");
        }
        if (level == 11 && EndStoreDoor(here) || kind == "endbookstore")
        {
            var door = layout.FeatureOrigin(x, z, EndStoreDoor);
            Passage passage = BothWays(door, KeyOf(door, SaltEndThreshold + 5), WorldLayout.TheEnd, EndExitDoor);
            passage.Message = "backrooms:endbookstore";
            return WithSound(passage, "game:sounds/block/door");
        }
        if (level != WorldLayout.TheEnd) return null;
        switch (kind)
        {
            case "endexit":
            {
                var door = layout.FeatureOrigin(x, z, EndExitDoor);
                if (!EndExitOpens(door.X, door.Z))
                {
                    refusal = "endexit";
                    return null;
                }
                ulong key = KeyOf(door, SaltEndThreshold + 6);
                double r = Hashing.Unit(Hashing.Mix(key));
                (int target, Func<Tile, bool> partner) = r switch
                {
                    < 0.40 => (1, EndLevel1Door),
                    < 0.65 => (WorldLayout.Hub, EndHubServiceDoor),
                    < 0.80 => (11, EndStoreDoor),
                    < 0.90 => (4, (Func<Tile, bool>)null),
                    _ => (5, PlainDoor),
                };
                Passage passage = BothWays(door, key, target, partner);
                passage.Message = "backrooms:endexit-out";
                return WithSound(passage, "game:sounds/block/door");
            }
            case "endvent":
            {
                // Up the ladder and into the vent: it ends in open air over the hills of Level 94
                Passage passage = BothWays((x, z), KeyOf((x, z), SaltEndThreshold + 7), WorldLayout.Motion);
                passage.Message = "backrooms:endvent";
                return WithSound(passage, "game:sounds/block/heavymetal-hit");
            }
        }
        // Every other door here is a fake reality's that does not work (Zone 4 and up, as the generator draws them),
        // or the staff door, and none leads anywhere: without this they would fall through to the hotel doors'
        // rule and might open onto Level 5. (Nothing ever arrives in The End beside one, so none is a way back.)
        if (here.Kind == TileKind.Door)
        {
            refusal = here.Zone >= 4 ? "endfake" : "locked";
            return null;
        }
        return null;
    }

    /// <summary>A computer that says "=)": whoever turned it on is taken to Level Fun, one-way. Null for an ordinary computer.</summary>
    public Passage EndTerminal(int x, int z, bool central)
    {
        if (central) return null;
        // (A few of the rest run TRUEEND.EXE instead: Level 3999's, with its own salt, ThresholdNetwork.L3999.cs)
        if (Hashing.Unit(KeyOf((x, z), SaltEndThreshold + 8)) >= 0.25) return L3999TrueEnd(x, z, central);
        return new Passage { Source = (x, z), Key = KeyOf((x, z), SaltEndThreshold + 9), Find = In(WorldLayout.FunLevel), Message = "backrooms:endparty-taken" };
    }

    /// <summary>
    /// Walking into a wall during a distortion: through into the scene it showed, the same for every wall of the
    /// department (the threshold is the department). Two-way: a thin spot leads back. Null where the scene is nowhere.
    /// </summary>
    public Passage EndDistortion(int di, int dj)
    {
        int scene = layout.EndDistortionScene(di, dj);
        if (scene < 0) return null;
        var anchor = layout.EndDeptCentre(di, dj);
        Passage passage = BothWays(anchor, KeyOf(anchor, SaltEndThreshold + 10), scene);
        passage.Message = "backrooms:enddistortion-through";
        passage.Sound = "game:sounds/effect/translocate-breakdimension";
        return passage;
    }
}
