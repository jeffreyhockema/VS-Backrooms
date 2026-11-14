namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for The Basement (experimental, kept as level 22), laid out in WorldLayout.LevelBasement.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>; rel 0 is the Cellar's floor slab). Every tile has the low ceiling at rel 4
/// (concrete, or bare joists over a finished room). The Cellar and the Dry Patch stand on rel 0 with three blocks of air;
/// the Flood's bed is at rel -2 under water at rel -1 and 0 (vanilla still water, as in Level 7), its steps stair blocks in
/// the water at rel 0 (upper) and -1 (lower). Walls are slimed concrete up to the waterline and damp cinder block (or old
/// pine panelling) above it, the Flood's with a tide line just over the water. Caged bulbs hang in the top block of air
/// (rel 3), and so do the Flood's pipes and the Cellar's dead wires. Doors are two blocks of door under a block of wall.
///
/// Two things reach above the ceiling: a crack someone fell through (open to <see cref="WorldLayout.BasementCrackTop"/>,
/// where the lit ceiling of the room above shows, its torn carpet round the edge, its wallpaper beyond) and an Escherian
/// stairwell (a brick tower from rel -9 to 24, its steps repeating every <see cref="WorldLayout.BasementEscherRise"/>
/// blocks, a jammed door on its wall a turn above and below the real one, so that a turn up or down looks the same).
/// This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private int basementFloorDryId, basementFloorDampId, basementFloorPatchId, basementCeilingId, basementCeilingStainedId, basementFaintId, basementShaftId;
    private int basementWallId, basementWallStainedId, basementWallTideId, basementSlimeWallId, basementSlimeBedId;
    private int basementLampOnId, basementLampOffId, basementLampFlickerId, basementLampDimId, basementLampBrightId, basementPumpId;
    private int basementCarpetOliveId, basementCarpetBrownId, basementPanelId, basementPanelStainedId, basementBrickId;
    /// <summary>Round 4: the hall's duct with the mains beside it, [fit (plain, valve, gauge), axis (we, ns)].</summary>
    private readonly int[,] basementDuctIds = new int[3, 2];
    private int basementWireId, basementRopeHangId, basementRopeEndId, basementLobbyCarpetId, basementLobbyWallId, basementLobbyCeilingId, basementLobbyLightId;
    private readonly int[] basementStepIds = new int[4], basementBrickStepIds = new int[4], basementLadderIds = new int[4];
    /// <summary>[state (closed, open, jammed), hinge (w, e), part (lower, upper, bare: layout 16's upper half of a swollen door without its board), facing].</summary>
    private readonly int[,,,] basementDoorIds = new int[3, 2, 3, 4];
    private readonly int[,] basementDebrisIds = new int[2, 4], basementJunkIds = new int[4, 4];
    /// <summary>[part (lower, upper, dial), leaf (l, r), facing].</summary>
    private readonly int[,,] basementLiftIds = new int[3, 2, 4];
    // Round 3: the house's things of several blocks, and what hangs on its walls and from its joists
    private int basementEarthId, basementRugId;
    /// <summary>[part (lower, upper, top), facing].</summary>
    private readonly int[,] basementFurnaceIds = new int[3, 4], basementHeaterIds = new int[3, 4];
    /// <summary>[half (l, r), facing].</summary>
    private readonly int[,] basementBenchIds = new int[2, 4], basementPoolIds = new int[2, 4];
    /// <summary>[load or label, part (lower, upper), facing].</summary>
    private readonly int[,,] basementShelvingIds = new int[4, 2, 4], basementBoxesIds = new int[4, 2, 4];
    private readonly int[,] basementWineIds = new int[2, 4];
    /// <summary>[thing (BasementWallThings), facing]; [hang (line, shirt, sheet, towel, cobweb), facing].</summary>
    private readonly int[,] basementWallThingIds = new int[9, 4], basementOverheadIds = new int[5, 4];
    private readonly int[] basementPoolLampIds = new int[4], basementFallenIds = new int[4];
    // Round 4: the basement's own appliances and furniture (similar to the shared props, made for this house), the joists
    // as a model, the stairs' rail, the crack's broken edge, the Flood's scum, the stud wall's plates
    /// <summary>[kind (washer, dryer, tub), part (lower, upper), facing].</summary>
    private readonly int[,,] basementLaundryIds = new int[3, 2, 4];
    /// <summary>[half (l, r) or part (lower, upper), facing].</summary>
    private readonly int[,] basementSofaIds = new int[2, 4], basementTvIds = new int[2, 4], basementRailIds = new int[2, 4], basementSlabEdgeIds = new int[2, 4];
    private readonly int[] basementCueRackIds = new int[4], basementShopLightIds = new int[4], basementWallRailIds = new int[4], basementSumpIds = new int[4];
    /// <summary>[part (low, high), facing].</summary>
    private readonly int[,] basementSumpPipeIds = new int[2, 4], basementBoilerIds = new int[2, 4];
    /// <summary>[half (l, r), part (lower, upper), facing].</summary>
    private readonly int[,,] basementBarIds = new int[2, 2, 4];
    private readonly int[] basementStoolIds = new int[4];
    /// <summary>[part (low, mid, top), axis (we, ns)].</summary>
    private readonly int[,] basementStudIds = new int[3, 2];
    /// <summary>[kind (plain, cable, box, bridge), axis (we, ns), light (dark, faint)].</summary>
    private readonly int[,,] basementJoistIds = new int[4, 2, 2];
    /// <summary>[what (a, b, c films, board, box, bottle, chair, laptop), facing].</summary>
    private readonly int[,] basementScumIds = new int[8, 4];
    private static readonly string[] BasementWallThings = { "pegboard-a", "pegboard-b", "fusebox", "conduit", "sign-caution", "sign-head", "sign-water", "calendar", "chute" };

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitBasement()
    {
        basementFloorDryId = Id("basement-floor-dry");
        basementFloorDampId = Id("basement-floor-damp");
        basementFloorPatchId = Id("basement-floor-patch");
        basementCeilingId = Id("basement-ceiling-plain");
        basementCeilingStainedId = Id("basement-ceiling-stained");
        basementFaintId = Id("basement-ceiling-faint");
        basementShaftId = Id("basement-ceiling-shaft");
        basementWallId = Id("basement-wall-plain");
        basementWallStainedId = Id("basement-wall-stained");
        basementWallTideId = Id("basement-wall-tide");
        basementSlimeWallId = Id("basement-slime-wall");
        basementSlimeBedId = Id("basement-slime-bed");
        basementLampOnId = Id("basement-lamp-on");
        basementLampOffId = Id("basement-lamp-off");
        basementLampFlickerId = Id("basement-lamp-flicker");
        basementLampDimId = Id("basement-lamp-dim");
        basementLampBrightId = Id("basement-lamp-bright");
        basementPumpId = Id("waterpump");
        basementCarpetOliveId = Id("basement-carpet-olive");
        basementCarpetBrownId = Id("basement-carpet-brown");
        basementPanelId = Id("basement-panel-plain");
        basementPanelStainedId = Id("basement-panel-stained");
        basementBrickId = Id("basement-brick-plain");
        basementWireId = Id("wiredroop");
        string[] fits = { "plain", "valve", "gauge" }, axes = { "we", "ns" };
        for (int k = 0; k < 3; k++)
            for (int a = 0; a < 2; a++)
                basementDuctIds[k, a] = Id($"basement-ductrun-{fits[k]}-{axes[a]}");
        basementRopeHangId = Id("basement-rope-hang");
        basementRopeEndId = Id("basement-rope-end");
        basementLobbyCarpetId = Id("carpet-soaked");
        basementLobbyWallId = Id("wallpaper-chevron-upper");
        basementLobbyCeilingId = Id("ceilingtile");
        basementLobbyLightId = Id("fluorescentlight-on");
        string[] states = { "closed", "open", "jammed" }, hinges = { "w", "e" }, parts = { "lower", "upper", "bare" };
        string[] debris = { "boards", "chunks" }, junk = { "rope", "crowbar", "bottle", "jar" }, lift = { "lower", "upper", "dial" }, leaves = { "l", "r" };
        for (int f = 0; f < 4; f++)
        {
            basementStepIds[f] = Id("basement-steps-" + Sides[f]);
            basementBrickStepIds[f] = Id("basement-bricksteps-" + Sides[f]);
            basementLadderIds[f] = BlockId("game:ladder-wood-aged-" + Sides[f]);
            for (int s = 0; s < 3; s++)
                for (int h = 0; h < 2; h++)
                    for (int p = 0; p < 2; p++)
                        basementDoorIds[s, h, p, f] = Id($"basement-door-{states[s]}-{hinges[h]}-{parts[p]}-{Sides[f]}");
            for (int k = 0; k < 2; k++) basementDebrisIds[k, f] = Id($"basement-debris-{debris[k]}-{Sides[f]}");
            for (int k = 0; k < 4; k++) basementJunkIds[k, f] = Id($"basement-junk-{junk[k]}-{Sides[f]}");
            for (int p = 0; p < 3; p++)
                for (int l = 0; l < 2; l++)
                    basementLiftIds[p, l, f] = Id($"basement-lift-{lift[p]}-{leaves[l]}-{Sides[f]}");
        }
        string[] studParts = { "low", "mid", "top" };
        for (int k = 0; k < 3; k++)
            for (int a = 0; a < 2; a++)
                basementStudIds[k, a] = Id($"basement-studs-{studParts[k]}-{axes[a]}");
        string[] joistKinds = { "plain", "cable", "box", "bridge" }, lights = { "dark", "faint" };
        for (int k = 0; k < 4; k++)
            for (int a = 0; a < 2; a++)
                for (int l = 0; l < 2; l++)
                    basementJoistIds[k, a, l] = Id($"basement-joists-{joistKinds[k]}-{axes[a]}-{lights[l]}");
        string[] laundry = { "washer", "dryer", "tub" }, scums = { "a", "b", "c", "board", "box", "bottle", "chair", "laptop" };
        for (int f = 0; f < 4; f++)
        {
            for (int k = 0; k < 3; k++)
                for (int p = 0; p < 2; p++)
                    basementLaundryIds[k, p, f] = Id($"basement-laundry-{laundry[k]}-{(p == 0 ? "lower" : "upper")}-{Sides[f]}");
            for (int p = 0; p < 2; p++)
            {
                basementSofaIds[p, f] = Id($"basement-sofa-{(p == 0 ? "l" : "r")}-{Sides[f]}");
                basementTvIds[p, f] = Id($"basement-tv-{(p == 0 ? "lower" : "upper")}-{Sides[f]}");
                basementRailIds[p, f] = Id($"basement-rail-{(p == 0 ? "l" : "r")}-{Sides[f]}");
                basementSlabEdgeIds[p, f] = Id($"basement-slabedge-{(p == 0 ? "a" : "b")}-{Sides[f]}");
            }
            for (int k = 0; k < scums.Length; k++) basementScumIds[k, f] = Id($"basement-scum-{scums[k]}-{Sides[f]}");
            basementCueRackIds[f] = Id("basement-cuerack-" + Sides[f]);
            basementShopLightIds[f] = Id("basement-shoplight-" + Sides[f]);
            basementWallRailIds[f] = Id("basement-wallrail-" + Sides[f]);
            basementSumpIds[f] = Id("basement-sump-" + Sides[f]);
            basementSumpPipeIds[0, f] = Id("basement-sumppipe-low-" + Sides[f]);
            basementSumpPipeIds[1, f] = Id("basement-sumppipe-high-" + Sides[f]);
            basementBoilerIds[0, f] = Id("basement-boiler-lower-" + Sides[f]);
            basementBoilerIds[1, f] = Id("basement-boiler-upper-" + Sides[f]);
            basementStoolIds[f] = Id("basement-stool-" + Sides[f]);
            for (int h = 0; h < 2; h++)
                for (int p = 0; p < 2; p++)
                    basementBarIds[h, p, f] = Id($"basement-bar-{(h == 0 ? "l" : "r")}-{(p == 0 ? "lower" : "upper")}-{Sides[f]}");
        }
        basementEarthId = Id("basement-earth");
        basementRugId = Id("basement-rug");
        string[] three = { "lower", "upper", "top" }, two = { "lower", "upper" }, halves = { "l", "r" };
        string[] loads = { "boxes", "jars", "paint", "odds" }, labels = { "xmas", "taxes", "moms", "keep" }, hangs = { "line", "shirt", "sheet", "towel", "cobweb" };
        for (int f = 0; f < 4; f++)
        {
            for (int p = 0; p < 3; p++)
            {
                basementFurnaceIds[p, f] = Id($"basement-furnace-{three[p]}-{Sides[f]}");
                basementHeaterIds[p, f] = Id($"basement-heater-{three[p]}-{Sides[f]}");
            }
            for (int p = 0; p < 2; p++)
            {
                basementBenchIds[p, f] = Id($"basement-bench-{halves[p]}-{Sides[f]}");
                basementPoolIds[p, f] = Id($"basement-pooltable-{halves[p]}-{Sides[f]}");
                basementWineIds[p, f] = Id($"basement-winerack-{two[p]}-{Sides[f]}");
                for (int k = 0; k < 4; k++)
                {
                    basementShelvingIds[k, p, f] = Id($"basement-shelving-{loads[k]}-{two[p]}-{Sides[f]}");
                    basementBoxesIds[k, p, f] = Id($"basement-boxes-{labels[k]}-{two[p]}-{Sides[f]}");
                }
            }
            for (int k = 0; k < BasementWallThings.Length; k++) basementWallThingIds[k, f] = Id($"basement-wallthing-{BasementWallThings[k]}-{Sides[f]}");
            for (int k = 0; k < hangs.Length; k++) basementOverheadIds[k, f] = Id($"basement-overhead-{hangs[k]}-{Sides[f]}");
            basementPoolLampIds[f] = Id($"basement-poollamp-{Sides[f]}");
            basementFallenIds[f] = Id($"basement-fallen-{Sides[f]}");
        }
        // The way in, in other levels (WorldGenerator.Basement.Links.cs)
        InitBasementLinks();
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int LevelBasementBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int ceiling = WorldGeometry.RoomHeight + 1;
        if (t.Detail == WorldLayout.BasementTower) return BasementTowerBlock(t, rel);
        if (rel > ceiling) return BasementAbove(t, rel, gx, gz);
        if (rel < -2) return concreteId;
        if (t.Kind == TileKind.Wall)
        {
            if (rel == ceiling) return concreteId;
            // (only ever seen from the water; under a stud wall, which can be seen through, the floor)
            if (rel <= 0) return t.Pattern == WallPattern.BasementStuds ? (rel == 0 ? basementFloorDryId : concreteId) : basementSlimeWallId;
            return t.Pattern switch
            {
                WallPattern.BasementPillar => pillarId,
                WallPattern.BasementFloodWall => rel == 1 ? basementWallTideId : basementWallStainedId,
                WallPattern.BasementStained => basementWallStainedId,
                WallPattern.BasementPanel => (gx * 7 + gz * 13) % 5 == 0 ? basementPanelStainedId : basementPanelId,
                WallPattern.BasementLift => basementLiftIds[rel - 1, t.Stack & 1, Facing(t.Pier)],
                WallPattern.BasementStuds => basementStudIds[rel == 1 ? 0 : rel == WorldGeometry.RoomHeight ? 2 : 1, BasementStudAxis(gx, gz)],
                _ => basementWallId,
            };
        }
        if (t.Kind == TileKind.Doorway)
        {
            // A wooden door, two blocks of it, under a block of the wall it is in
            if (rel <= 0) return rel == 0 ? basementFloorDryId : concreteId;
            if (rel == ceiling) return concreteId;
            if (rel <= 2 && t.Variant == Props.BasementDoor) return BasementDoorPart(t, rel - 1);
            if (rel <= 2) return 0;
            return t.Pattern switch
            {
                WallPattern.BasementPanel => basementPanelId,
                WallPattern.BasementStained => basementWallStainedId,
                WallPattern.BasementStuds => basementStudIds[2, BasementStudAxis(gx, gz)],
                _ => basementWallId,
            };
        }
        // (a long ladder, from the floor up through the crack's opening: the shaft's part is in BasementAbove)
        if (rel >= 1 && rel <= ceiling && t.Kind == TileKind.Floor && t.Variant == Props.BasementLadder && t.Stack == WorldLayout.BasementLongLadder
            && t.Ceiling == CeilingKind.BasementOpen) return basementLadderIds[Facing(Opposite(t.Pier))];
        if (rel == ceiling)
        {
            if (t.Ceiling == CeilingKind.BasementOpen) return 0;
            // (Round 4: the slab broken back round the crack, its rebar bent down into the hole)
            if (t.Overhead == Overheads.BasementCrackRim && BasementSlabEdge(gx, gz) is var edge and not 0) return edge;
            // About one ceiling block in seven gives off a faint light, looking like every other: "a light which has no
            // determined source" (Fandom)
            bool faint = ((gx * 3 + gz * 5) % 7 + 7) % 7 == 0;
            return t.Ceiling switch
            {
                CeilingKind.BasementStained => basementCeilingStainedId,
                CeilingKind.BasementJoists => BasementJoists(gx, gz, faint),
                _ => faint ? basementFaintId : basementCeilingId,
            };
        }
        if (rel == ceiling - 1)
        {
            // What hangs in the top block of air: a furnace's or a heater's ducts and pipes going up, a bulb, pipes or a duct,
            // what hangs from the joists (the pool table's lamp, a clothesline, a cobweb, the fuse box's conduit), a dead wire
            if (t.Kind == TileKind.Floor && t.Variant == Props.BasementFurnace) return basementFurnaceIds[2, Facing(t.Pier)];
            if (t.Kind == TileKind.Floor && t.Variant == Props.BasementHeater) return basementHeaterIds[2, Facing(t.Pier)];
            int lamp = t.Ceiling switch
            {
                CeilingKind.BasementBulbOn => basementLampOnId,
                CeilingKind.BasementBulbOff => basementLampOffId,
                CeilingKind.BasementBulbFlicker => basementLampFlickerId,
                CeilingKind.BasementBulbDim => basementLampDimId,
                CeilingKind.BasementBulbBright => basementLampBrightId,
                _ => 0,
            };
            if (lamp != 0) return lamp;
            // (Round 4: the shop light over the workbench, hung from the left half's joists, along the bench)
            if (t.Kind == TileKind.Floor && t.Variant == Props.BasementBench && (t.Stack & 1) == 0 && t.Pipe == 0)
                return basementShopLightIds[Facing(t.Pier)];
            if (t.Kind == TileKind.Floor && t.Pipe == 0)
                switch (t.Overhead)
                {
                    case Overheads.BasementPoolLamp: return basementPoolLampIds[Facing(t.Pier)];
                    case >= Overheads.BasementCobweb and <= Overheads.BasementCobwebLast: return basementOverheadIds[4, t.Overhead - Overheads.BasementCobweb];
                    case Overheads.BasementLineWE: return basementOverheadIds[BasementHash(gx, gz) % 4, 0];
                    case Overheads.BasementLineNS: return basementOverheadIds[BasementHash(gx, gz) % 4, 1];
                    case Overheads.BasementFuseBox: return basementWallThingIds[3, Facing(t.Pier)];
                }
            if (t.Overhead == Overheads.BasementWire && t.Kind == TileKind.Floor) return basementWireId;
            return t.Pipe switch
            {
                Pipes.BasementPipeWE => pipeRunXId,
                Pipes.BasementPipeNS => pipeRunZId,
                Pipes.BasementLeakWE => pipeLeakXId,
                Pipes.BasementLeakNS => pipeLeakZId,
                Pipes.BasementDuctWE => basementDuctIds[BasementDuctFit(gx, gz), 0],
                Pipes.BasementDuctNS => basementDuctIds[BasementDuctFit(gx, gz), 1],
                _ => 0,
            };
        }
        if (t.Kind == TileKind.Water)
        {
            // The Flood: the bed at rel -2, water over it to the dry floor's height; a step is a stair block in the water
            int stepRel = t.Height - 2;
            if (t.Height > 0)
            {
                if (rel < stepRel) return concreteId;
                if (rel == stepRel) { fluid = waterId; return basementStepIds[Facing(t.Pier)]; }
            }
            if (rel == -2) return basementSlimeBedId;
            // (Round 3: sodden boxes drifted into a dead end, awash, their tops just out of the water)
            if (t.Variant == Props.BasementBoxes && rel == 0) { fluid = waterId; return basementBoxesIds[t.Stack & 3, 0, Facing(t.Pier)]; }
            // (Round 4: under some of the sodden boxes, on the bed, a laptop: the clipping's, lost to the water)
            if (t.Variant == Props.BasementBoxes && rel == -1 && BasementHash(gx, gz) % 3 == 0) { fluid = waterId; return basementScumIds[7, Facing(t.Pier)]; }
            // (Round 4: scum on the surface, now and then something floating in it)
            if (rel == 0 && t.Height == 0) { fluid = waterId; return BasementScum(gx, gz); }
            if (rel <= 0) { fluid = waterId; return 0; }
            // (Round 4: the upper step's handrail, on the side with a wall)
            if (rel == 1 && t.Height == 2) return BasementRail(t, gx, gz);
            return 0;
        }
        // The dry floor (the Cellar, the Dry Patch, a doorway), and what stands on it
        if (rel < 0) return concreteId;
        if (rel == 0)
            return t.Kind == TileKind.Floor && t.Variant == Props.BasementSump ? basementSumpIds[BasementSumpCorner(gx, gz)] : t.Floor switch
            {
                FloorKind.BasementEarth => basementEarthId,
                FloorKind.BasementRug => basementRugId,
                FloorKind.BasementDamp => basementFloorDampId,
                FloorKind.BasementPatch => basementFloorPatchId,
                FloorKind.BasementCarpet => basementCarpetOliveId,
                FloorKind.BasementCarpetWorn => basementCarpetBrownId,
                _ => basementFloorDryId,
            };
        if (t.Kind != TileKind.Floor) return 0;
        if (t.SupplyBox) return rel == 1 ? BoxOf(t) : 0;
        if (t.Variant == 0 && t.Stack > 0) return rel <= t.Stack ? CrateOf(t) : 0;
        if (t.Variant == Props.BasementLadder) return rel <= 2 ? basementLadderIds[Facing(Opposite(t.Pier))] : 0;
        int facing = Facing(t.Pier);
        // Round 3: the things two blocks high, and what hangs on the wall over whatever stands there
        if (rel <= 2)
        {
            int part = rel - 1;
            switch (t.Variant)
            {
                case Props.BasementFurnace: return basementFurnaceIds[part, facing];
                case Props.BasementHeater: return basementHeaterIds[part, facing];
                case Props.BasementShelving: return basementShelvingIds[t.Stack & 3, part, facing];
                case Props.BasementBoxes: return basementBoxesIds[t.Stack & 3, part, facing];
                case Props.BasementWineRack: return basementWineIds[part, facing];
                case Props.BasementBoiler when part == 0 || t.Overhead == 0: return basementBoilerIds[part, facing];
                case Props.BasementBar when part == 0 || t.Overhead == 0: return basementBarIds[t.Stack & 1, part, facing];
                case Props.BasementSump when part == 1 && t.Overhead == 0: return basementSumpPipeIds[1, BasementSumpCorner(gx, gz)];
                // (Round 4: the house's own washer, dryer and tub, its TV; their upper part is the wall or the lid over them)
                case Props.Laundry when part == 0 || t.Overhead == 0: return basementLaundryIds[t.Stack & 1, part, facing];
                case Props.KitchenCounter when t.Stack == 1 && (part == 0 || t.Overhead == 0): return basementLaundryIds[2, part, facing];
                case Props.Tv when part == 0 || t.Overhead == 0: return basementTvIds[part, facing];
            }
        }
        if (rel == 2)
        {
            int thing = t.Overhead switch
            {
                Overheads.BasementPegboard => BasementHash(gx, gz) % 2,
                Overheads.BasementFuseBox => 2,
                Overheads.BasementCaution => 4,
                Overheads.BasementWatchHead => 5,
                Overheads.BasementDeepWater => 6,
                Overheads.BasementCalendar => 7,
                Overheads.BasementChute => 8,
                _ => -1,
            };
            return thing >= 0 ? basementWallThingIds[thing, facing] : 0;
        }
        if (rel != 1) return 0;
        // (Layout 16's balance, in every world (ExpVersion): the pantry shelves, iceboxes, shelves and boxes others went through are drawn stripped)
        return Stripped(t, t.Variant switch
        {
            Props.BasementBoiler => boilerIds[facing],
            Props.BasementDrum => drumId,
            Props.BasementShelf => shelfIds[facing],
            Props.BasementPump => basementPumpId,
            Props.BasementCabinet => cabinetIds[facing],
            Props.BasementDebris => basementDebrisIds[t.Stack & 1, facing],
            Props.BasementJunk => basementJunkIds[t.Stack & 3, facing],
            Props.BasementBench => basementBenchIds[t.Stack & 1, facing],
            Props.BasementPoolTable => basementPoolIds[t.Stack & 1, facing],
            Props.BasementSump => basementSumpPipeIds[0, BasementSumpCorner(gx, gz)],
            Props.BasementFallen => basementFallenIds[facing],
            Props.LongSofa => basementSofaIds[t.Stack & 1, facing],
            Props.BasementCueRack => basementCueRackIds[facing],
            Props.BasementStool => basementStoolIds[facing],
            // (A body is an entity, laid down by Regions.BasementSystem; nothing of it is a block)
            Props.BasementBody => 0,
            // (Props of the other levels', reused: Level 0-11's furniture, bones, signs)
            _ => t.Variant >= 40 && t.Variant < Props.RunFirst ? PropBlock(t) : 0,
        });
    }

    /// <summary>A small hash of a column, for picking among looks that do not matter to the layout.</summary>
    private static int BasementHash(int gx, int gz) => (int)((uint)(gx * 73856093 ^ gz * 19349663) >> 7);

    /// <summary>
    /// Round 4: a joist ceiling's block. The joists run one way across a cell and the other way in the next; a whole joist
    /// line in a cell carries the cable or not, now and then a junction box on it; bridging between bare joists here and there.
    /// </summary>
    private int BasementJoists(int gx, int gz, bool faint)
    {
        int axis = ((gx >> 5) + (gz >> 5)) & 1;
        int across = axis == 0 ? gz : gx, along = axis == 0 ? gx : gz;
        int kind = BasementHash(across * 5 + 1, (along >> 5) * 11 + 7) % 10 < 3 ? 1 : 0;
        if (kind == 1 && BasementHash(gx * 3 + 2, gz * 7 + 1) % 7 == 0) kind = 2;
        else if (kind == 0 && BasementHash(gx * 5 + 3, gz * 3 + 2) % 9 == 0) kind = 3;
        return basementJoistIds[kind, axis, faint ? 1 : 0];
    }

    /// <summary>Round 4: which way a stud wall runs (1 north-south where the wall goes on north or south of it), so its studs face the room.</summary>
    private int BasementStudAxis(int gx, int gz) =>
        layout.TileAt(gx, gz - 1).Kind is TileKind.Wall or TileKind.Doorway || layout.TileAt(gx, gz + 1).Kind is TileKind.Wall or TileKind.Doorway ? 1 : 0;

    /// <summary>
    /// Round 4: which way the sump's model turns: its walls are to the north and west of the north variant, so the corner
    /// between walls north and east is the east variant, south and east the south, south and west the west.
    /// </summary>
    private int BasementSumpCorner(int gx, int gz)
    {
        bool n = layout.TileAt(gx, gz - 1).Kind == TileKind.Wall, s = layout.TileAt(gx, gz + 1).Kind == TileKind.Wall;
        bool e = layout.TileAt(gx + 1, gz).Kind == TileKind.Wall, w = layout.TileAt(gx - 1, gz).Kind == TileKind.Wall;
        ArchPier p = n && e ? ArchPier.East : s && e ? ArchPier.South : s && w ? ArchPier.West : ArchPier.North;
        return Facing(p);
    }

    /// <summary>Round 4: what a block of the hall's duct and mains carries: mostly nothing, now and then a valve or a gauge.</summary>
    private static int BasementDuctFit(int gx, int gz) => (BasementHash(gx * 7 + 5, gz * 13 + 3) % 18) switch { 0 => 1, 1 => 2, _ => 0 };

    /// <summary>Round 4: the Flood's surface over a tile: scum on about a quarter, rarely a board, a sodden box or a bottle.</summary>
    private int BasementScum(int gx, int gz)
    {
        int h = BasementHash(gx * 3 + 1, gz * 5 + 2) % 100, f = BasementHash(gx + 9, gz + 4) & 3;
        return h switch
        {
            < 27 => basementScumIds[h % 3, f],
            27 => basementScumIds[3, f],
            28 => basementScumIds[4, f],
            29 => basementScumIds[5, f],
            30 => basementScumIds[6, f],
            _ => 0,
        };
    }

    /// <summary>
    /// Round 4: the upper step of a stair down into the Flood (climbing toward Pier) gets a handrail on its left, or its
    /// right, where a wall is beside it.
    /// </summary>
    private int BasementRail(in Tile t, int gx, int gz)
    {
        var (dx, dz) = t.Pier switch { ArchPier.North => (0, -1), ArchPier.South => (0, 1), ArchPier.East => (1, 0), _ => (-1, 0) };
        int lx = dz, lz = -dx; // (to the left, facing up the stair)
        if (layout.TileAt(gx + lx, gz + lz).Kind == TileKind.Wall) return basementRailIds[0, Facing(t.Pier)];
        if (layout.TileAt(gx - lx, gz - lz).Kind == TileKind.Wall) return basementRailIds[1, Facing(t.Pier)];
        return 0;
    }

    /// <summary>Round 4: a ring tile of the crack beside its hole: the broken slab facing the hole, or 0 at a corner.</summary>
    private int BasementSlabEdge(int gx, int gz)
    {
        foreach (var (dx, dz, toward) in new[] { (0, -1, ArchPier.North), (1, 0, ArchPier.East), (0, 1, ArchPier.South), (-1, 0, ArchPier.West) })
        {
            Tile n = layout.TileAt(gx + dx, gz + dz);
            if (n.Ceiling == CeilingKind.BasementOpen && n.Kind != TileKind.Water) return basementSlabEdgeIds[BasementHash(gx, gz) & 1, Facing(toward)];
        }
        return 0;
    }

    /// <summary>A part of a Basement door: <paramref name="part"/> 0 the lower block, 1 the upper.</summary>
    private int BasementDoorPart(in Tile t, int part, int state = -1)
    {
        int st = state >= 0 ? state : t.Stack & 3;
        // (layout 16: a swollen door's upper half without the DO NOT ENTER board is its own block)
        if (part == 1 && st == 2 && state < 0 && (t.Stack & WorldLayout.BasementDoorBare) != 0) part = 2;
        return basementDoorIds[st > 2 ? 0 : st, (t.Stack >> 2) & 1, part, Facing(t.Pier)];
    }

    /// <summary>
    /// Over the ceiling: solid, but for the crack (open to its top, the Lobby's lit ceiling there, its torn carpet round the
    /// hole, its wallpaper round that) and the rope's frayed end hanging in it, out of reach.
    /// </summary>
    private int BasementAbove(in Tile t, int rel, int gx, int gz)
    {
        const int top = WorldLayout.BasementCrackTop;
        if (rel > top) return concreteId;
        if (t.Ceiling == CeilingKind.BasementOpen && t.Kind != TileKind.Water)
        {
            if (rel == top) return t.Detail == WorldLayout.BasementCrackMiddle ? basementLobbyLightId : basementLobbyCeilingId;
            // (a long ladder, up the shaft's side to the room above)
            if (t.Variant == Props.BasementLadder && t.Stack == WorldLayout.BasementLongLadder && rel <= top - 4) return basementLadderIds[Facing(Opposite(t.Pier))];
            if (t.Overhead == Overheads.BasementRope && rel >= top - 8 && rel <= top - 4) return rel == top - 8 ? basementRopeEndId : basementRopeHangId;
            return 0;
        }
        if (t.Overhead == Overheads.BasementCrackRim)
        {
            if (rel == top) return basementLobbyCeilingId;
            if (rel > top - 4) return 0;
            if (rel == top - 4) return basementLobbyCarpetId;
            // (Round 4: the slab's broken edge a block up too, so the break is two blocks deep)
            if (rel == WorldGeometry.RoomHeight + 2 && BasementSlabEdge(gx, gz) is var edge and not 0) return edge;
            // (The broken slab lining the crack, lit by the room above: the light comes down it to the floor)
            if (rel > WorldGeometry.RoomHeight + 1) return basementShaftId;
        }
        if (t.Overhead == Overheads.BasementCrackWall && rel > top - 4 && rel < top) return basementLobbyWallId;
        return concreteId;
    }

    /// <summary>
    /// An Escherian stairwell's tower (WorldLayout.BasementTowerAt): brick walls and core from rel -9 to 24,
    /// the steps round the core repeating every turn, their landing level with the floor by the door, a dim bulb under
    /// every turn's fifth step, and on the door's line a jammed door a turn above and a turn below the real one.
    /// </summary>
    private int BasementTowerBlock(in Tile t, int rel)
    {
        const int rise = WorldLayout.BasementEscherRise, low = WorldLayout.BasementEscherLow, high = WorldLayout.BasementEscherHigh;
        if (rel < low - 1 || rel > high + 1) return concreteId;
        if (t.Kind == TileKind.Doorway)
        {
            int turn = (int)System.Math.Floor((rel - 1) / (double)rise), within = rel - 1 - turn * rise;
            if (within <= 1 && t.Variant == Props.BasementDoor) return turn == 0 ? BasementDoorPart(t, within) : BasementDoorPart(t, within, 2);
            return rel == 0 ? basementFloorDryId : basementBrickId;
        }
        if (t.Kind == TileKind.Wall) return basementBrickId;
        if (t.Variant != Props.BasementEscher || t.Stair == 0)
        {
            // (The cell's other tiles inside the tower: none; the floor as a fallback)
            return rel == 0 ? basementFloorDryId : rel < 0 || rel > WorldGeometry.RoomHeight ? concreteId : 0;
        }
        if (rel == low - 1 || rel == high + 1) return basementBrickId; // the pit's floor, the shaft's cap
        int place = t.Stair - 1;
        int m = ((rel - place) % rise + rise) % rise;
        // (Every place a step, the landing by the door too: a full block there would be a whole block up from the step before it)
        if (m == 0) return basementBrickStepIds[Facing(t.Pier)];
        if (place == 4 && m == rise - 1) return basementLampDimId;
        // (Round 4: a handrail on the outer wall, to the left of the way up, over every step but the landing by the door)
        if (m == 1 && place != 0) return basementWallRailIds[Facing(t.Pier)];
        return 0;
    }
}
