using L = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// The blocks of Level 14's ways in and out (WorldLayout.Level14.Links.cs; the level's own file; tools/gen_14_links.py). In
/// Level 0: the EMERGENCY EXIT door (<c>l14-exitdoor-lower/upper</c>: grey steel, a push bar, the green running man lit over
/// it; kind <c>l14-exit</c>) in a Lobby wall, the Lobby's wall over it, and the M.E.G. placard (<c>l14-placard-&lt;side&gt;</c>)
/// beside it. In Level 15: the door marked MEDICAL CENTER (<c>l14-meddoor</c>, kind <c>l14-medical</c>) in a medical bay's
/// wall, under Level 15's lit lintel. In Level 14: the futuristic door (<c>l14-futuredoor</c>, kind <c>l14-future</c>) and the
/// red exit door (<c>l14-reddoor</c>, kind <c>l14-red</c>) in a wall under a steel lintel, and the floor that gives way
/// (<c>l14-floor-sagging</c>) with the cracked tiles round it (<c>l14-floor-cracked</c>).
/// </summary>
public sealed partial class WorldGenerator
{
    private readonly int[] l14ExitDoor = new int[2], l14MedDoor = new int[2], l14FutureDoor = new int[2], l14RedDoor = new int[2], l14Placard = new int[4];

    /// <summary>The ids of the ways' blocks (from <see cref="InitL14"/>).</summary>
    partial void InitL14Links()
    {
        string[] parts = { "lower", "upper" };
        for (int i = 0; i < 2; i++)
        {
            l14ExitDoor[i] = L14Block("l14-exitdoor-" + parts[i], BlockId("backrooms:officedoor-" + parts[i]));
            l14MedDoor[i] = L14Block("l14-meddoor-" + parts[i], l14ExitDoor[i]);
            l14FutureDoor[i] = L14Block("l14-futuredoor-" + parts[i], l14MedDoor[i]);
            l14RedDoor[i] = L14Block("l14-reddoor-" + parts[i], l14ExitDoor[i]);
        }
        for (int f = 0; f < 4; f++) l14Placard[f] = L14Block("l14-placard-" + Sides[f]);
    }

    /// <summary>The scaffold's hook (WorldGenerator.ExpLinks.cs): the EMERGENCY EXIT door and its placard in Level 0; -1 elsewhere.</summary>
    partial void L14EntranceBlock(in Tile t, int gx, int gz, int rel, ref int id, ref int fluid)
    {
        switch (t.Under)
        {
            case Unders.L14ExitDoor when t.Level == 0 && t.Kind == TileKind.Wall && rel is 1 or 2:
                id = l14ExitDoor[rel - 1];
                break;
            case Unders.L14Placard when t.Level == 0 && t.Kind == TileKind.Floor && rel == 1:
                if (l14Placard[Facing(t.Pier)] != 0) id = l14Placard[Facing(t.Pier)];
                break;
        }
    }

    /// <summary>The level's ways out at a tile of Level 14 (WorldGenerator.L14.cs calls it for any tile with an Under): -1 where it has none.</summary>
    partial void L14LinkBlock(in Tile t, int gx, int gz, int rel, ref int id)
    {
        switch (t.Under)
        {
            case Unders.L14FutureDoor or Unders.L14RedDoor when t.Kind == TileKind.Wall:
                if (rel is 1 or 2) id = (t.Under == Unders.L14FutureDoor ? l14FutureDoor : l14RedDoor)[rel - 1];
                else if (rel == 3) id = l14Wall[L14WLintel];
                break;
            case Unders.L14Collapse when t.Kind == TileKind.Floor && rel == 0:
                id = l14Floor[L.L14FSagging];
                break;
            case Unders.L14Cracks when t.Kind == TileKind.Floor && rel == 0:
                id = l14Floor[L.L14FCracked];
                break;
        }
    }

    /// <summary>
    /// The door marked MEDICAL CENTER in a wall of Level 15 (WorldGenerator.L15.cs asks for any Level 15 tile with one of
    /// Level 14's Unders), <paramref name="rel"/> above the floor: the door, Level 15's lintel over it, or -1 for the wall.
    /// </summary>
    private int L14InL15Block(in Tile t, int rel)
    {
        if (t.Under != Unders.L14MedDoor || t.Kind != TileKind.Wall) return -1;
        if (rel is 1 or 2) return l14MedDoor[rel - 1];
        if (rel == 3) return l15Wall[L.L15IsDark(t) ? L15WLintelDead : L15WLintel];
        return -1;
    }
}
