namespace Backrooms.Worldgen;

/// <summary>
/// The flights of the stairwells of Levels 1 and 4 from layout version 4 (see <see cref="WorldLayout.StairwellSteps"/>
/// and <see cref="WorldLayout.StampStairwellV4"/>): one climbs through an opening in the ceiling into a dark shaft,
/// the other descends through an opening in the floor into one. A flight's steps rise (or fall) a block a step; every
/// step has solid concrete under its tread and the headroom both of its neighbours need, so the flights can be walked
/// either way without a bump or a drop. The shafts are cut out of the solid concrete over the ceiling and in the
/// foundations, so the stairwell's walls go on as concrete round them and they open into nothing else: the shaft up
/// stays under the band's top (the mantle is just over its roof) and, in Level 4, out of the void over the drop
/// ceiling; the shaft down stays above the foundations' bottom, where the ground begins (<see cref="FoundationDepth"/>).
/// Nothing in them gives light, and the trip up comes two steps into the dark, the trip down on the last step under
/// the wall, where the light from the landing has died away.
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>Level 1's painted floor markings, P5 to B3 (see <see cref="WorldLayout.L1FloorLabel"/>), by floor and facing.</summary>
    private readonly int[,] floorSignIds = new int[WorldLayout.L1Floors, 4];

    private void InitStairwells()
    {
        for (int floor = 0; floor < WorldLayout.L1Floors; floor++)
            for (int f = 0; f < 4; f++)
                floorSignIds[floor, f] = Id($"l1deco-levelsign{WorldLayout.L1FloorLabel(floor).ToLowerInvariant()}-{Sides[f]}");
    }

    /// <summary>
    /// The painted floor marking on a wall of a Level 1 stairwell's landing (from layout version 4), or 0 to paint the
    /// plain P2 of every stairwell before it.
    /// </summary>
    private int FloorSign(in Tile t, int rel)
    {
        int floor = WorldLayout.L1FloorOf(t);
        if (floor < 0 || rel != 2) return 0;
        return floorSignIds[floor, Facing(t.Pier)];
    }

    /// <summary>The block at <paramref name="rel"/> above the floor in the column of a step of a stairwell's flight.</summary>
    private int FlightBlock(in Tile t, int rel)
    {
        bool office = t.Level == 4;
        int room = office ? WorldGeometry.RoomHeight : WorldGeometry.Level1RoomHeight;
        // Under the stairwell's far wall (the last steps of each flight), the wall goes on as ever over the floor
        bool walled = t.Kind == TileKind.Wall;
        bool hotel = t.Pattern == WallPattern.Hotel;
        int Wall(int r) => office ? (hotel ? HotelWall(r) : r == 1 ? officeWallBaseId : officeWallId)
            : r == 1 ? whiteBaseId : whiteUpperId;
        if (t.Zone == WorldLayout.FlightZoneDown)
        {
            // Step n's tread is the top of a stair block n-1 below the floor block: solid under it, open over it
            int tread = 1 - t.Stair;
            if (rel < tread) return concreteId;
            if (rel == tread) return stairIds[Facing(t.Pier)];
            if (rel < 0) return 0;
            // The floor is open over the first four steps, and roofs the rest
            if (rel == 0) return walled ? concreteId : 0;
            if (walled) return rel <= room ? Wall(rel) : concreteId;
            if (rel <= room) return 0;
            if (rel == room + 1) return office ? officeCeilingId : concreteCeilingId;
            // (the void over Level 4's drop ceiling runs on over it, as over the rest of the room)
            return office && rel == room + 2 ? 0 : concreteId;
        }

        // A flight up (into the shaft, or into Level Fun's service stairs)
        if (rel < 0) return concreteId;
        if (rel == 0) return floorIds[(int)t.Floor];
        if (rel < t.Stair) return walled && rel <= room ? Wall(rel) : office && rel <= room ? officeWallId : concreteId;
        if (rel == t.Stair) return stairIds[Facing(t.Pier)];
        if (rel <= room) return 0;
        // The ceiling is open over the flight from its second step (in Level 4, the low one, from its first), and the
        // shaft over it is roofed under the band's top. (In Level 4 the first step's opening is only the ceiling tile's
        // height: the void over the ceiling beside it is walled off.)
        int shaftTop = Geometry.BandTop - Geometry.FloorY - 1;
        if (office && t.Stair == 1) return rel == room + 1 ? 0 : concreteId;
        if (t.Stair >= 2 && rel <= shaftTop) return 0;
        return rel == room + 1 && !walled && t.Stair < 2 ? concreteCeilingId : concreteId;
    }
}
