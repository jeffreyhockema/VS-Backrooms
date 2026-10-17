using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 94, Motion. The ground is clay under a skin of clay turf mown in stripes, <see cref="Tile.Height"/>
/// above the valley floor; on it the houses are the Suburbs' houses, drawn from the ground up. The mountain is a shell
/// of glass; the castle on it is white stone outside and a funhouse inside; the edge is a painted backdrop.
/// </summary>
public sealed partial class WorldGenerator
{
    private int turfLightId, turfDarkId, claySoilId, fireClayId, backdropHillsId, backdropSkyId, glassMountainId;
    /// <summary>Seams of fire clay under the hills: the Backrooms' only fire clay, so the bloomery and the kilns are possible.</summary>
    private const ulong SaltFireClay = 0x9431;
    private int castleWallId, castleRoofId, funWallId, castleCeilingId, funLightId, funBrightId;
    private int towerLegId, towerTankId, towerRoofId, towerTapId, almondRimId, almondSpoutId;
    /// <summary>The rebuilt water tower's blocks (D3), by level, row and column of its five by five tiles; 0 where it has nothing.</summary>
    private readonly int[] towerFrameIds = new int[TowerLevels * 25];
    private bool towerFrame;
    private const int TowerLevels = 14;
    private readonly int[] cinemaScreenIds = new int[4], picketIds = new int[16];
    private int ballFillId, whiteWallId;
    private int dollDoorLowerId, dollDoorUpperId, floodDoorLowerId, floodDoorUpperId, throneDoorLowerId, throneDoorUpperId;

    private void InitMotion()
    {
        turfLightId = Id("clayturf-light");
        turfDarkId = Id("clayturf-dark");
        claySoilId = Id("claysoil");
        fireClayId = GameId("game:rawclay-fire-none");
        backdropHillsId = Id("backdrop-hills");
        backdropSkyId = Id("backdrop-sky");
        glassMountainId = Id("glassmountain");
        castleWallId = Id("castleblock-wall");
        castleRoofId = Id("castleblock-roof");
        funWallId = Id("castleblock-funwall");
        castleCeilingId = Id("castleblock-ceiling");
        funLightId = Id("funlight-warm");
        funBrightId = Id("funlight-blinding");
        towerLegId = Id("watertower-leg");
        towerTankId = Id("watertower-tank");
        towerRoofId = Id("watertower-roof");
        towerTapId = Id("watertower-tap");
        for (int c = 1; c <= TowerLevels; c++)
            for (int j = 0; j < 5; j++)
                for (int i = 0; i < 5; i++)
                {
                    modBlocks.TryGetValue($"watertowerframe-x{i}z{j}y{c:00}", out int id);
                    towerFrameIds[((c - 1) * 5 + j) * 5 + i] = id;
                    towerFrame |= id != 0;
                }
        almondRimId = Id("almondfountain-rim");
        almondSpoutId = Id("almondfountain-spout");
        dollDoorLowerId = Id("dolldoor-lower");
        dollDoorUpperId = Id("dolldoor-upper");
        floodDoorLowerId = Id("flooddoor-lower");
        floodDoorUpperId = Id("flooddoor-upper");
        throneDoorLowerId = Id("thronedoor-lower");
        throneDoorUpperId = Id("thronedoor-upper");
        for (int f = 0; f < 4; f++) cinemaScreenIds[f] = Id($"cinemascreen-{Sides[f]}");
        for (int m = 0; m < 16; m++) picketIds[m] = Id($"picketfence-{m}");
        ballFillId = Id("ballpitfill");
        whiteWallId = Id("castleblock-white");
        floorIds[(int)FloorKind.TurfLight] = turfLightId;
        floorIds[(int)FloorKind.TurfDark] = turfDarkId;
        floorIds[(int)FloorKind.ClaySoil] = claySoilId;
        floorIds[(int)FloorKind.MotionPath] = Id("motionground-path");
        floorIds[(int)FloorKind.MotionConcrete] = Id("motionground-concrete");
        floorIds[(int)FloorKind.MotionAsphalt] = Id("motionground-asphalt");
        floorIds[(int)FloorKind.MotionKerb] = Id("motionground-kerb");
        floorIds[(int)FloorKind.Checker] = Id("funfloor-checker");
        floorIds[(int)FloorKind.FunCarpet] = Id("funfloor-carpet");
        floorIds[(int)FloorKind.StarFloor] = Id("funfloor-star");
    }

    /// <summary>The block at <paramref name="rel"/> above the valley floor of a Level 94 column.</summary>
    private int Level94Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        int ground = t.Height;

        // The edge of the set: a painted backdrop, hills along the bottom and sky above
        if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.Backdrop)
            return rel <= 0 ? concreteId : rel <= 9 ? backdropHillsId : rel <= 50 ? backdropSkyId : 0;

        // The glass mountain: a shell two blocks thick, dark and hollow inside
        if (t.Zone == 2)
        {
            if (rel <= 0) return claySoilId;
            if (rel > ground) return 0;
            return rel >= ground - 1 ? glassMountainId : 0;
        }
        if (t.Zone is 3 or 4) return CastleBlock(t, gx, gz, rel, ground);

        // The ground: clay, with a layer of real clay a little way down, under the turf, the road or the floor, and
        // seams of fire clay five blocks thick (3 to 7 under the turf) over about half the hills (measured 57%)
        if (rel < ground - 2)
        {
            if (fireClayId != 0 && rel >= ground - 7 && Noise2(gx / 20.0, gz / 20.0, SaltFireClay) > 0.15) return fireClayId;
            return claySoilId;
        }
        if (rel == ground - 2) return clayId != 0 ? clayId : claySoilId;
        if (rel == ground - 1) return claySoilId;
        if (rel == ground) return floorIds[(int)t.Floor] != 0 ? floorIds[(int)t.Floor] : turfLightId;

        int c = rel - ground;
        // A staircase going nowhere, of white-painted concrete, among the heaps
        if (t.Under == Unders.Nowhere && t.Stair > 0) return c < t.Stair ? whiteWallId : c == t.Stair ? stairIds[Facing(t.Pier)] : 0;
        // The steps of a path down a hill
        if (t.Stair > 0) return c == 1 ? stairIds[Facing(t.Pier)] : 0;
        switch (t.Variant)
        {
            case Props.WaterTower:
                int tower = towerFrame ? WaterTowerFrameBlock(t, c) : WaterTowerBlock(t.Stack, c);
                return tower == 0 && c == 1 ? UnderTowerGrass(t, gx, gz) : tower; // long grass round its legs
            case Props.AlmondFountain: return FountainBlock(t.Stack, c, out fluid);
        }
        // The doors that lead elsewhere: a doll's house's, and a flooded house's (held shut on the water)
        if (t.Kind == TileKind.Door && t.Under is Unders.DollHouse or Unders.FloodedHouse && c <= 2)
        {
            bool flooded = t.Under == Unders.FloodedHouse;
            return c == 1 ? (flooded ? floodDoorLowerId : dollDoorLowerId) : (flooded ? floodDoorUpperId : dollDoorUpperId);
        }
        // White picket fences
        if (t.Kind == TileKind.Bars && t.Pattern == WallPattern.Fence && c == 1) return picketIds[t.Stack & 15];
        // The houses here have two storeys, like the ones in the pictures: a second storey of siding and windows over
        // the first, its rooms shut off above the ceiling, and the roof over that
        if (RoofBits.IsSloped(t.Roof) && !RoofBits.IsLowered(t.Roof) && c >= 5)
        {
            if (c >= 9) return Level9Block(t, gx, gz, c - 4, t.Detail - 1);
            if (t.Kind == TileKind.Floor) return c == 8 ? houseCeilingId : 0;
            Tile upper = t;
            if (t.Kind is TileKind.Door or TileKind.Doorway)
            {
                // Over a door: a window, if this is an outside wall
                upper.Kind = TileKind.Wall;
                upper.Variant = (byte)(t.Pattern is >= WallPattern.SidingWhite and <= WallPattern.Brick ? 1 : 0);
                upper.Under = 0;
            }
            return Level9Block(upper, gx, gz, c - 4, t.Detail - 1);
        }
        int block = Level9Block(t, gx, gz, c, t.Detail - 1);
        // A house full of water to its ceiling
        if (t.Under == Unders.FloodedHouse && t.Kind == TileKind.Floor && c is >= 1 and <= 3) fluid = waterId;
        return block;
    }

    /// <summary>
    /// A water tower on a hilltop, over five by five tiles: four steel legs, a white tank, a pointed roof, and a tap at
    /// the foot of the middle that runs with Almond Water.
    /// </summary>
    private int WaterTowerBlock(int part, int c)
    {
        int du = part % 5 - 2, dv = part / 5 - 2;
        bool corner = Math.Abs(du) == 2 && Math.Abs(dv) == 2, inner = Math.Abs(du) <= 1 && Math.Abs(dv) <= 1;
        if (c >= 1 && c <= 8) return corner ? towerLegId : du == 0 && dv == 0 && c == 1 ? towerTapId : 0;
        if (c >= 9 && c <= 12) return corner ? 0 : towerTankId;
        if (c == 13) return inner ? towerRoofId : 0;
        if (c == 14) return du == 0 && dv == 0 ? towerRoofId : 0;
        return 0;
    }

    /// <summary>
    /// The water tower of the pictures (graphics pass D3), over the same five by five tiles and fourteen levels: four
    /// braced legs on footings, a riser over the tap, a plain round white tank with a catwalk and a cone of a roof. One
    /// block per tile and level (watertowerframe-x{i}z{j}y{level}, cut from one model by
    /// tools/gen_motion.py); the tap at the foot of the riser is the old tower's. Placed in every world, since its tiles
    /// are where the old tower stood: chunks generated before keep the old one.
    /// </summary>
    private int WaterTowerFrameBlock(in Tile t, int c)
    {
        if (c < 1 || c > TowerLevels) return 0;
        // (Stack is the tile's place in the tower, column and row as the world runs: a hill lot laid out mirrored
        // north to south mirrors the rows back, WorldLayout.PlanHill)
        int i = t.Stack % 5, j = t.Stack / 5;
        if (i == 2 && j == 2 && c == 1) return towerTapId;
        return towerFrameIds[((c - 1) * 5 + j) * 5 + i];
    }

    /// <summary>The town fountain, over five by five tiles: a stone rim round a basin of water, a spout in the middle.</summary>
    private int FountainBlock(int part, int c, out int fluid)
    {
        fluid = 0;
        int du = part % 5 - 2, dv = part / 5 - 2;
        bool rim = Math.Abs(du) == 2 || Math.Abs(dv) == 2;
        if (c != 1 && !(du == 0 && dv == 0 && c == 2)) return 0;
        if (rim) return c == 1 ? almondRimId : 0;
        if (du == 0 && dv == 0) return almondSpoutId;
        fluid = waterId;
        return 0;
    }

    /// <summary>
    /// The castle on the mountain. Its floor stands <see cref="WorldLayout.MountainHeight"/> above the valleys, on the
    /// glass. White walls eight high with battlements, a tower on each corner with a red roof; inside, a single storey
    /// of funhouse under a lit ceiling, the blinding halls lit almost white.
    /// </summary>
    private int CastleBlock(in Tile t, int gx, int gz, int rel, int floor)
    {
        if (rel <= 0) return claySoilId;
        int c = rel - floor;
        // The ball pit is sunk a block into the floor, full of balls you wade through
        if (t.Variant == Props.BallPit && t.Kind == TileKind.Floor && c is >= -1 and <= 7)
            return c == 0 ? ballFillId : c == -1 ? floorIds[(int)FloorKind.Checker] : c < 6 ? 0
                : c == 6 ? (t.Ceiling == CeilingKind.LightOn ? funLightId : castleCeilingId) : castleRoofId;
        if (rel < floor - 1) return 0;
        if (rel < floor) return glassMountainId;
        int cu = gx - layout.MotionOriginX + WorldLayout.CastleSize / 2, cv = gz - layout.MotionOriginZ + WorldLayout.CastleSize / 2;
        bool outer = cu < 2 || cv < 2 || cu >= WorldLayout.CastleSize - 2 || cv >= WorldLayout.CastleSize - 2;
        bool tower = (cu < 7 || cu >= WorldLayout.CastleSize - 7) && (cv < 7 || cv >= WorldLayout.CastleSize - 7);
        // (Inside, nothing is animated: the blinding halls' floor is plain white, no thumbprints in it)
        if (c == 0) return t.Kind != TileKind.Floor ? castleWallId : t.Zone == 4 ? whiteWallId : floorIds[(int)t.Floor];

        if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.CastleWall)
        {
            if (tower)
            {
                // A round-ish tower, its red roof stepping in to a point
                int tu = cu < 7 ? cu : WorldLayout.CastleSize - 1 - cu, tv = cv < 7 ? cv : WorldLayout.CastleSize - 1 - cv;
                int ring = Math.Min(Math.Min(tu, 6 - tu), Math.Min(tv, 6 - tv)); // 0 at the tower's edge, 3 in its middle
                if (c <= 13) return castleWallId;
                return c <= 15 + 2 * ring ? castleRoofId : 0;
            }
            if (c <= 8) return castleWallId;
            // Battlements along the top of the outer walls
            return outer && c == 9 && (cu + cv) % 2 == 0 ? castleWallId : 0;
        }
        if (t.Kind == TileKind.Door) return c == 1 ? throneDoorLowerId : c == 2 ? throneDoorUpperId : c <= 6 ? funWallId : c == 7 ? castleRoofId : 0;
        // The throne room's dark panelling, a frieze under its ceiling
        if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.Hotel) return c == 1 ? wainscotId : c <= 4 ? panelId : c <= 6 ? friezeId : c == 7 ? castleRoofId : 0;
        // In the blinding halls even the walls are white
        if (t.Kind == TileKind.Wall) return c <= 6 ? (t.Zone == 4 || BesideBlinding(gx, gz) ? whiteWallId : funWallId) : c == 7 ? castleRoofId : 0;

        // Inside: the funhouse under its ceiling, the roof over that; the gate's opening is open to the sky
        if (outer) return c <= 4 ? 0 : c <= 8 ? castleWallId : 0;
        if (c == 6) return t.Ceiling switch
        {
            CeilingKind.LightOn => t.Zone == 4 ? funBrightId : funLightId,
            CeilingKind.Chandelier => chandelierId,
            _ => castleCeilingId,
        };
        if (c == 7) return castleRoofId;
        if (c > 7) return 0;
        if (c == 1) return t.Variant != 0 ? PropBlock(t) : 0;
        // The King stands two blocks tall
        return 0;
    }

    /// <summary>Whether a castle wall faces into one of the blinding halls (so it is white on that side too).</summary>
    private bool BesideBlinding(int gx, int gz)
    {
        foreach (var (dx, dz) in Neighbours4)
            if (layout.TileAt(gx + dx, gz + dz) is { Zone: 4, Kind: TileKind.Floor }) return true;
        return false;
    }
}
