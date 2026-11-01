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
    private int basementFloorDryId, basementFloorDampId, basementFloorPatchId, basementCeilingId, basementCeilingStainedId, basementJoistsId, basementFaintId, basementJoistsFaintId, basementShaftId;
    private int basementWallId, basementWallStainedId, basementWallTideId, basementSlimeWallId, basementSlimeBedId;
    private int basementLampOnId, basementLampOffId, basementLampFlickerId, basementLampDimId, basementLampBrightId, basementPumpId;
    private int basementCarpetOliveId, basementCarpetBrownId, basementPanelId, basementPanelStainedId, basementBrickId;
    private int basementDuctWeId, basementDuctNsId;
    private int basementWireId, basementRopeHangId, basementRopeEndId, basementLobbyCarpetId, basementLobbyWallId, basementLobbyCeilingId, basementLobbyLightId;
    private readonly int[] basementStepIds = new int[4], basementBrickStepIds = new int[4], basementLadderIds = new int[4];
    /// <summary>[state (closed, open, jammed), hinge (w, e), part (lower, upper), facing].</summary>
    private readonly int[,,,] basementDoorIds = new int[3, 2, 2, 4];
    private readonly int[,] basementDebrisIds = new int[2, 4], basementJunkIds = new int[4, 4];
    /// <summary>[part (lower, upper, dial), leaf (l, r), facing].</summary>
    private readonly int[,,] basementLiftIds = new int[3, 2, 4];

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitBasement()
    {
        basementFloorDryId = Id("basement-floor-dry");
        basementFloorDampId = Id("basement-floor-damp");
        basementFloorPatchId = Id("basement-floor-patch");
        basementCeilingId = Id("basement-ceiling-plain");
        basementCeilingStainedId = Id("basement-ceiling-stained");
        basementJoistsId = Id("basement-ceiling-joists");
        basementFaintId = Id("basement-ceiling-faint");
        basementJoistsFaintId = Id("basement-ceiling-joistsfaint");
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
        basementDuctWeId = Id("basement-duct-we");
        basementDuctNsId = Id("basement-duct-ns");
        basementRopeHangId = Id("basement-rope-hang");
        basementRopeEndId = Id("basement-rope-end");
        basementLobbyCarpetId = Id("carpet-soaked");
        basementLobbyWallId = Id("wallpaper-chevron-upper");
        basementLobbyCeilingId = Id("ceilingtile");
        basementLobbyLightId = Id("fluorescentlight-on");
        string[] states = { "closed", "open", "jammed" }, hinges = { "w", "e" }, parts = { "lower", "upper" };
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
        // The way in, in other levels (WorldGenerator.Basement.Links.cs)
        InitBasementLinks();
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int LevelBasementBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int ceiling = WorldGeometry.RoomHeight + 1;
        if (t.Detail == WorldLayout.BasementTower) return BasementTowerBlock(t, rel);
        if (rel > ceiling) return BasementAbove(t, rel);
        if (rel < -2) return concreteId;
        if (t.Kind == TileKind.Wall)
        {
            if (rel == ceiling) return concreteId;
            if (rel <= 0) return basementSlimeWallId; // (only ever seen from the water)
            return t.Pattern switch
            {
                WallPattern.BasementPillar => pillarId,
                WallPattern.BasementFloodWall => rel == 1 ? basementWallTideId : basementWallStainedId,
                WallPattern.BasementStained => basementWallStainedId,
                WallPattern.BasementPanel => (gx * 7 + gz * 13) % 5 == 0 ? basementPanelStainedId : basementPanelId,
                WallPattern.BasementLift => basementLiftIds[rel - 1, t.Stack & 1, Facing(t.Pier)],
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
            return t.Pattern == WallPattern.BasementPanel ? basementPanelId : t.Pattern == WallPattern.BasementStained ? basementWallStainedId : basementWallId;
        }
        if (rel == ceiling)
        {
            if (t.Ceiling == CeilingKind.BasementOpen) return 0;
            // About one ceiling block in seven gives off a faint light, looking like every other: "a light which has no
            // determined source" (Fandom)
            bool faint = ((gx * 3 + gz * 5) % 7 + 7) % 7 == 0;
            return t.Ceiling switch
            {
                CeilingKind.BasementStained => basementCeilingStainedId,
                CeilingKind.BasementJoists => faint ? basementJoistsFaintId : basementJoistsId,
                _ => faint ? basementFaintId : basementCeilingId,
            };
        }
        if (rel == ceiling - 1)
        {
            // What hangs in the top block of air: a bulb, pipes or a duct, a dead wire
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
            if (t.Overhead == Overheads.BasementWire && t.Kind == TileKind.Floor) return basementWireId;
            return t.Pipe switch
            {
                Pipes.BasementPipeWE => pipeRunXId,
                Pipes.BasementPipeNS => pipeRunZId,
                Pipes.BasementLeakWE => pipeLeakXId,
                Pipes.BasementLeakNS => pipeLeakZId,
                Pipes.BasementDuctWE => basementDuctWeId,
                Pipes.BasementDuctNS => basementDuctNsId,
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
            if (rel <= 0) { fluid = waterId; return 0; }
            return 0;
        }
        // The dry floor (the Cellar, the Dry Patch, a doorway), and what stands on it
        if (rel < 0) return concreteId;
        if (rel == 0)
            return t.Floor switch
            {
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
        if (rel != 1) return 0;
        int facing = Facing(t.Pier);
        return t.Variant switch
        {
            Props.BasementBoiler => boilerIds[facing],
            Props.BasementDrum => drumId,
            Props.BasementShelf => shelfIds[facing],
            Props.BasementPump => basementPumpId,
            Props.BasementCabinet => cabinetIds[facing],
            Props.BasementDebris => basementDebrisIds[t.Stack & 1, facing],
            Props.BasementJunk => basementJunkIds[t.Stack & 3, facing],
            // (A body is an entity, laid down by Regions.BasementSystem; nothing of it is a block)
            Props.BasementBody => 0,
            // (Props of the other levels', reused: Level 0-11's furniture, bones, signs)
            _ => t.Variant >= 40 && t.Variant < Props.RunFirst ? PropBlock(t) : 0,
        };
    }

    /// <summary>A part of a Basement door: <paramref name="part"/> 0 the lower block, 1 the upper.</summary>
    private int BasementDoorPart(in Tile t, int part, int state = -1)
    {
        int st = state >= 0 ? state : t.Stack & 3;
        return basementDoorIds[st > 2 ? 0 : st, (t.Stack >> 2) & 1, part, Facing(t.Pier)];
    }

    /// <summary>
    /// Over the ceiling: solid, but for the crack (open to its top, the Lobby's lit ceiling there, its torn carpet round the
    /// hole, its wallpaper round that) and the rope's frayed end hanging in it, out of reach.
    /// </summary>
    private int BasementAbove(in Tile t, int rel)
    {
        const int top = WorldLayout.BasementCrackTop;
        if (rel > top) return concreteId;
        if (t.Ceiling == CeilingKind.BasementOpen && t.Kind != TileKind.Water)
        {
            if (rel == top) return t.Detail == WorldLayout.BasementCrackMiddle ? basementLobbyLightId : basementLobbyCeilingId;
            if (t.Overhead == Overheads.BasementRope && rel >= top - 8 && rel <= top - 4) return rel == top - 8 ? basementRopeEndId : basementRopeHangId;
            return 0;
        }
        if (t.Overhead == Overheads.BasementCrackRim)
        {
            if (rel == top) return basementLobbyCeilingId;
            if (rel > top - 4) return 0;
            if (rel == top - 4) return basementLobbyCarpetId;
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
        return 0;
    }
}
