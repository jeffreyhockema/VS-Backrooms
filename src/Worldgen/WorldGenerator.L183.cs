using Part = Backrooms.Worldgen.WorldLayout.L183Part;
using Space = Backrooms.Worldgen.WorldLayout.L183Space;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 183, "Clean Sewers" (experimental, kept as level 27), laid out in WorldLayout.Level183.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>; rel 0 is the walkways' floor). Walls are glazed sewer brick with a clean waterline
/// one block up; walkways pale scored concrete; a curb is one block lower, its top at the water's surface; a channel's or a
/// basin's bed is at rel -2 under one block of vanilla still water (rel -1); a gutter's bed at rel -1 under water level with
/// the walkways (rel 0); a grate sits at rel 0 over a block of water. Above, air up to the tile's <see cref="Tile.Height"/>,
/// then the brick vault (flat in the side tunnels, ringed over the mains, domed over chambers and halls). Wall lamps hang
/// against their wall at rel 3 (rel 4 in chambers and halls), pipes in the top block of air. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l183WallId, l183WallStainedId, l183WallTideId, l183WalkId, l183CurbId, l183BedId, l183GrateId;
    private int l183CeilingFlatId, l183CeilingArchId, l183CeilingDomeId;
    private readonly int[,] l183LampIds = new int[3, 4]; // on, bright, flicker x north, east, south, west

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL183()
    {
        l183WallId = Id("l183-wall-plain");
        l183WallStainedId = Id("l183-wall-stained");
        l183WallTideId = Id("l183-wall-tide");
        l183WalkId = Id("l183-floor-walkway");
        l183CurbId = Id("l183-floor-curb");
        l183BedId = Id("l183-floor-bed");
        l183GrateId = Id("l183-grate");
        l183CeilingFlatId = Id("l183-ceiling-flat");
        l183CeilingArchId = Id("l183-ceiling-arch");
        l183CeilingDomeId = Id("l183-ceiling-dome");
        string[] states = { "on", "bright", "flicker" };
        for (int s = 0; s < 3; s++)
            for (int f = 0; f < 4; f++)
                l183LampIds[s, f] = Id("l183-lamp-" + states[s] + "-" + Sides[f]);
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level183Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < -3 || rel > 8) return concreteId;
        if (t.Kind != TileKind.Floor && t.Kind != TileKind.Water)
        {
            // Walls (the rim's too) and the halls' pillars, solid all the way up into the vault
            if (rel == 8) return concreteId;
            if (t.Detail == WorldLayout.L183WallPillar) return rel is >= 1 and <= 6 ? pillarId : rel > 6 ? l183CeilingDomeId : l183WallId;
            if (rel == 1) return l183WallTideId;
            return t.Detail == WorldLayout.L183WallStained && rel >= 2 ? l183WallStainedId : l183WallId;
        }
        var part = (Part)t.Detail;
        int top = t.Height;
        // Below the air: the floor of each kind
        switch (part)
        {
            case Part.Channel:
                if (rel == -2) return l183BedId;
                if (rel == -1) { fluid = waterId; return 0; }
                if (rel < -2) return concreteId;
                break;
            case Part.Grate:
                if (rel == -2) return l183BedId;
                if (rel == -1) { fluid = waterId; return 0; }
                if (rel == 0) return l183GrateId;
                if (rel < -2) return concreteId;
                break;
            case Part.Gutter:
                if (rel == -1) return l183BedId;
                if (rel == 0) { fluid = waterId; return 0; }
                if (rel < -1) return l183WallId;
                break;
            case Part.Curb:
                if (rel == -1) return l183CurbId;
                if (rel < -1) return l183WallId;
                break;
            default:
                if (rel == 0) return l183WalkId;
                if (rel < 0) return l183WallId; // (seen from a channel's end)
                break;
        }
        if (rel > top)
        {
            Space space = WorldLayout.L183SpaceOf(t);
            return space is Space.Chamber or Space.Hall ? l183CeilingDomeId : space == Space.Main ? l183CeilingArchId : l183CeilingFlatId;
        }
        // The air, a wall lamp in it or pipes along its top
        if (t.Ceiling is CeilingKind.L183LampOn or CeilingKind.L183LampBright or CeilingKind.L183LampFlicker)
        {
            int lampRel = top < 4 ? top : 4;
            if (rel == lampRel)
                return l183LampIds[t.Ceiling == CeilingKind.L183LampOn ? 0 : t.Ceiling == CeilingKind.L183LampBright ? 1 : 2, Facing(Opposite(t.Pier))]; // (facing away from its wall)
            return 0;
        }
        if (rel == top && t.Pipe != 0)
            return t.Pipe switch
            {
                Pipes.L183PipeWE => pipeRunXId,
                Pipes.L183PipeNS => pipeRunZId,
                Pipes.L183LeakWE => pipeLeakXId,
                Pipes.L183LeakNS => pipeLeakZId,
                _ => 0,
            };
        return 0;
    }
}
