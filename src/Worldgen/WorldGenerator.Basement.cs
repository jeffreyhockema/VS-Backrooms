namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for The Basement (experimental, kept as level 22), laid out in WorldLayout.LevelBasement.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>; rel 0 is the Cellar's floor slab). Every tile has the low concrete ceiling at
/// rel 4. The Cellar and the Dry Patch stand on rel 0 with three blocks of air; the Flood's bed is at rel -2 under water
/// at rel -1 and 0 (vanilla still water, as in Level 7), its steps stair blocks in the water at rel 0 (upper) and -1
/// (lower). Walls are slimed concrete up to the waterline and damp cinder block above it, the Flood's with a tide line
/// just over the water. Caged bulbs hang in the top block of air (rel 3), and so do the Flood's pipes. This file is the
/// level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private int basementFloorDryId, basementFloorDampId, basementFloorPatchId, basementCeilingId, basementCeilingStainedId;
    private int basementWallId, basementWallStainedId, basementWallTideId, basementSlimeWallId, basementSlimeBedId;
    private int basementLampOnId, basementLampOffId, basementLampFlickerId, basementLampDimId, basementLampBrightId, basementPumpId;
    private readonly int[] basementStepIds = new int[4];

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitBasement()
    {
        basementFloorDryId = Id("basement-floor-dry");
        basementFloorDampId = Id("basement-floor-damp");
        basementFloorPatchId = Id("basement-floor-patch");
        basementCeilingId = Id("basement-ceiling-plain");
        basementCeilingStainedId = Id("basement-ceiling-stained");
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
        for (int i = 0; i < 4; i++) basementStepIds[i] = Id("basement-steps-" + Sides[i]);
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int LevelBasementBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int ceiling = WorldGeometry.RoomHeight + 1;
        if (rel > ceiling || rel < -2) return concreteId;
        if (t.Kind == TileKind.Wall)
        {
            if (rel == ceiling) return concreteId;
            if (rel <= 0) return basementSlimeWallId; // (only ever seen from the water)
            return t.Pattern switch
            {
                WallPattern.BasementPillar => pillarId,
                WallPattern.BasementFloodWall => rel == 1 ? basementWallTideId : basementWallStainedId,
                WallPattern.BasementStained => basementWallStainedId,
                _ => basementWallId,
            };
        }
        if (rel == ceiling) return t.Ceiling == CeilingKind.BasementStained ? basementCeilingStainedId : basementCeilingId;
        if (rel == ceiling - 1)
        {
            // What hangs in the top block of air: a bulb, or the Flood's pipes
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
            return t.Pipe switch
            {
                Pipes.BasementPipeWE => pipeRunXId,
                Pipes.BasementPipeNS => pipeRunZId,
                Pipes.BasementLeakWE => pipeLeakXId,
                Pipes.BasementLeakNS => pipeLeakZId,
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
                _ => basementFloorDryId,
            };
        if (t.Kind != TileKind.Floor) return 0;
        if (t.Variant == 0 && t.Stack > 0) return rel <= t.Stack ? CrateOf(t) : 0;
        if (rel != 1) return 0;
        int facing = Facing(t.Pier);
        return t.Variant switch
        {
            Props.BasementBoiler => boilerIds[facing],
            Props.BasementDrum => drumId,
            Props.BasementShelf => shelfIds[facing],
            Props.BasementPump => basementPumpId,
            Props.BasementCabinet => cabinetIds[facing],
            _ => 0,
        };
    }
}
