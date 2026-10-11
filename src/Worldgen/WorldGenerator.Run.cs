using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level ! (kept as level 14), laid out in WorldLayout.LevelRun.cs, and for its ways in from other levels (a
/// red EXIT door in a Level 1 wall, a Level 2 dead end that isn't there, the red end of a Level 37 dry corridor).
///
/// A lane's hall is 5 wide with four blocks of air: floor at rel 0, the hanging EXIT signs in the top block of air
/// (rel 4), the ceiling at rel 5, solid above. Walls carry the wooden crash rail at rel 1, doors at rel 1-2, a beacon or a
/// wall-mounted EXIT sign at rel 3. Codes are the plan's (docs/new-levels/run-plan.md, "Manifest changes (phase 2)").
/// Until the level's assets exist, every missing block falls back to something of the mod's own that looks the part,
/// so the level is never full of holes.
/// </summary>
public sealed partial class WorldGenerator
{
    private int runWallId, runVoidId, runSafeWallId, runCeilingId, runPanelDeadId, runVentId, runSafeLightId, runFalseWallId,
        runFalseWallUpperId, runFloorId, runScuffedId, runCrackedId, runSafeFloorId, runRubbleId, runRedLightId;
    /// <summary>The crash rail round an outer corner (on a face and the next clockwise), and stopped short in an inner corner.</summary>
    private readonly int[] runRailCornerIds = new int[4], runRailShortIds = new int[4];
    private readonly int[] runRailIds = new int[4], runBeaconIds = new int[4], runCabinetIds = new int[4], runBorderIds = new int[4],
        runSignIds = new int[2], runSignDimIds = new int[4], runSignBrightIds = new int[4], runSignConcreteIds = new int[4], runSignLitIds = new int[4];
    private readonly int[,] runSafeSignIds = new int[2, 4], runShelfIds = new int[2, 4], runCurtainIds = new int[4, 2], runDecorIds = new int[3, 4];
    /// <summary>Door blocks by pattern (lower, upper; facing).</summary>
    private readonly Dictionary<WallPattern, int[,]> runDoorIds = new();
    private readonly List<string> runMissing = new();

    /// <summary>A block of the level's by code, or the fallback if the level's assets don't have it (yet).</summary>
    private int RunId(string path, int fallback)
    {
        if (modBlocks.TryGetValue(path, out int id)) return id;
        runMissing.Add(path);
        return fallback;
    }

    /// <summary>
    /// The crash rail on a wall (its <see cref="Tile.Pier"/> face). Where the wall ends in an outer corner of the same
    /// floor the rail goes on round it; where its clockwise end runs into an inner corner whose other wall carries the
    /// rail too, it stops against that rail's front (the other one runs on into the corner).
    /// </summary>
    private int RunRail(in Tile t, int gx, int gz)
    {
        int face = Facing(t.Pier), next = (face + 1) & 3, prev = (face + 3) & 3;
        int faces = RunRailFaces(t, gx, gz);
        if ((faces >> next & 1) != 0) return runRailCornerIds[face];
        if ((faces >> prev & 1) != 0) return runRailCornerIds[prev];
        Tile along = TileAt(gx + PipeFaces[next].Dx, gz + PipeFaces[next].Dz);
        int bx = gx + PipeFaces[face].Dx + PipeFaces[next].Dx, bz = gz + PipeFaces[face].Dz + PipeFaces[next].Dz;
        if (along.Kind == TileKind.Wall && (RunRailFaces(TileAt(bx, bz), bx, bz) >> ((next + 2) & 3) & 1) != 0) return runRailShortIds[face];
        return runRailIds[face];
    }

    /// <summary>The faces of a Level ! wall that carry the crash rail (as bits by <see cref="Facing"/>): its own, and
    /// round an outer corner the next one onto the same floor.</summary>
    private int RunRailFaces(in Tile t, int gx, int gz)
    {
        if (t.Level != WorldLayout.RunLevel || t.Kind != TileKind.Wall
            || !(t.Pattern == WallPattern.RunWallRail || t.Pattern == WallPattern.RunMedCabinet && layout.Version >= 5)) return 0;
        int face = Facing(t.Pier);
        Tile front = TileAt(gx + PipeFaces[face].Dx, gz + PipeFaces[face].Dz);
        int faces = 1 << face;
        if (t.Pattern != WallPattern.RunWallRail) return faces;
        for (int turn = 1; turn <= 3; turn += 2)
        {
            int side = (face + turn) & 3;
            Tile n = TileAt(gx + PipeFaces[side].Dx, gz + PipeFaces[side].Dz);
            if (n.Kind == TileKind.Floor && n.Zone == front.Zone) return faces | 1 << side;
        }
        return faces;
    }

    /// <summary>Looks up the level's blocks, once, when the generator is made.</summary>
    private void InitRun()
    {
        int wallFallback = BlockId("backrooms:concretewall-plain"), lightFallback = BlockId("backrooms:fluorescentlight-red");
        runWallId = RunId("run-wall-plain", wallFallback);
        runVoidId = RunId("run-wall-void", BlockId("backrooms:concrete"));
        runSafeWallId = RunId("run-safewall-plain", wallFallback);
        runCeilingId = RunId("run-ceiling-tile", BlockId("backrooms:ceilingtile"));
        runPanelDeadId = RunId("run-ceiling-panel-dead", BlockId("backrooms:fluorescentlight-off"));
        runVentId = RunId("run-ceiling-vent", runCeilingId);
        runSafeLightId = RunId("run-safelight", BlockId("backrooms:fluorescentlight-on"));
        runRedLightId = RunId("run-redlight", lightFallback);
        runFalseWallId = RunId("run-falsewall-lower", 0);
        runFalseWallUpperId = RunId("run-falsewall-upper", runFalseWallId);
        runFloorId = RunId("run-floor-vinyl", BlockId("backrooms:concretefloor-plain"));
        runScuffedId = RunId("run-floor-scuffed", runFloorId);
        runCrackedId = RunId("run-floor-cracked", runFloorId);
        runSafeFloorId = RunId("run-floor-safe", runFloorId);
        runRubbleId = BlockId("backrooms:concrete");
        floorIds[(int)FloorKind.RunFloor] = runFloorId;
        floorIds[(int)FloorKind.RunScuffed] = runScuffedId;
        floorIds[(int)FloorKind.RunCracked] = runCrackedId;
        floorIds[(int)FloorKind.RunSafeFloor] = runSafeFloorId;
        floorIds[(int)FloorKind.RunBorder] = runFloorId;
        runSignIds[0] = RunId("run-exitsign-lit-ns", BlockId("backrooms:exithanging-we"));
        runSignIds[1] = RunId("run-exitsign-lit-we", BlockId("backrooms:exithanging-ns"));
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            runRailIds[f] = RunId($"run-wall-rail-{side}", runWallId);
            runRailCornerIds[f] = RunId($"run-wall-railcorner-{side}", runRailIds[f]);
            runRailShortIds[f] = RunId($"run-wall-railshort-{side}", runRailIds[f]);
            runBeaconIds[f] = RunId($"run-wall-beacon-lit-{side}", runWallId);
            runCabinetIds[f] = RunId($"run-medcabinet-{side}", runWallId);
            runBorderIds[f] = RunId($"run-floor-border-{side}", runFloorId);
            runSignDimIds[f] = RunId($"run-exitsign-wall-dim-{side}", lightFallback);
            runSignBrightIds[f] = RunId($"run-exitsign-wall-bright-{side}", lightFallback);
            runSignLitIds[f] = RunId($"run-exitsign-wall-lit-{side}", runSignBrightIds[f]);
            runSignConcreteIds[f] = RunId($"run-exitsign-wall-concrete-{side}", runSignBrightIds[f]);
            runSafeSignIds[0, f] = RunId($"run-safewall-sign-{side}-l", runSafeWallId);
            runSafeSignIds[1, f] = RunId($"run-safewall-sign-{side}-r", runSafeWallId);
            runShelfIds[0, f] = RunId($"run-shelf-standing-lower-{side}", 0);
            runShelfIds[1, f] = RunId($"run-shelf-standing-upper-{side}", 0);
            runDecorIds[0, f] = RunId($"run-walldecor-handwash-{side}", runWallId);
            runDecorIds[1, f] = RunId($"run-walldecor-visiting-{side}", runWallId);
            runDecorIds[2, f] = RunId($"run-walldecor-sanitiser-{side}", runWallId);

        }
        string[] curtain = { "lower", "middle", "upper", "top" };
        for (int part = 0; part < 4; part++)
        {
            runCurtainIds[part, 0] = RunId($"run-curtain-{curtain[part]}-ns", 0);
            runCurtainIds[part, 1] = RunId($"run-curtain-{curtain[part]}-we", 0);
        }
        int tunnelLower = tunnelDoorLowerId, tunnelUpper = tunnelDoorUpperId;
        void Door(WallPattern pattern, string code)
        {
            var ids = new int[2, 4];
            for (int f = 0; f < 4; f++)
            {
                ids[0, f] = RunId($"{code}-lower-{Sides[f]}", tunnelLower != 0 ? tunnelLower : runWallId);
                ids[1, f] = RunId($"{code}-upper-{Sides[f]}", tunnelUpper != 0 ? tunnelUpper : runWallId);
            }
            runDoorIds[pattern] = ids;
        }
        Door(WallPattern.RunSideDoor, "run-sidedoor-closed");
        Door(WallPattern.RunSwingDoor, "run-sidedoor-closed");
        Door(WallPattern.RunDentedDoor, "run-sidedoor-dented");
        Door(WallPattern.RunFakeExit, "run-exitdoor-fake");
        Door(WallPattern.RunTrueExit, "run-exitdoor-true");
        Door(WallPattern.RunMarkedDoor, "run-exitdoor-marked");
        Door(WallPattern.RunEntryDoor, "run-exitdoor-entry");
        Door(WallPattern.RunChainedDoor, "run-chaineddoor-intact");
        Door(WallPattern.RunHallDoor, "run-halldoor-closed");
        if (runMissing.Count > 0)
            api.Logger.Warning("[backrooms] Level ! is missing {0} of its blocks (first: {1}); stand-ins are used until its assets are built",
                runMissing.Count, runMissing[0]);
    }

    /// <summary>The block (and fluid) at <paramref name="rel"/> above the level's floor in the column of tile <paramref name="t"/>.</summary>
    private int LevelRunBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int ceiling = 5;
        if (t.Kind == TileKind.Pit)
        {
            // A hole down into the dark, rubble at the bottom: fall in and you are somewhere else (Level 8)
            if (rel <= -8) return concreteId;
            if (rel == -7) return runRubbleId;
            if (rel < ceiling) return 0;
            return rel == ceiling ? runCeilingId : concreteId;
        }
        if (rel < 0 || rel > ceiling) return concreteId;
        int face = Facing(t.Pier);
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (rel == 0 || rel == ceiling) return concreteId;
                return t.Pattern switch
                {
                    WallPattern.RunVoid => runVoidId,
                    WallPattern.RunSafeWall when rel == 2 && (t.Detail & WorldLayout.RunSafeSign) != 0 =>
                        runSafeSignIds[(t.Detail & WorldLayout.RunSafeSignRight) != 0 ? 1 : 0, face],
                    WallPattern.RunSafeWall => runSafeWallId,
                    WallPattern.RunWallRail when rel == 1 => RunRail(t, gx, gz),
                    // The start room's notices and dispenser (layout version 5), and the rail under its cabinet
                    WallPattern.RunWall or WallPattern.RunWallRail when rel == 2 && t.Detail >= WorldLayout.RunWallDecor =>
                        runDecorIds[t.Detail / WorldLayout.RunWallDecor - 1, face],
                    WallPattern.RunMedCabinet when rel == 2 => runCabinetIds[face],
                    WallPattern.RunMedCabinet when rel == 1 && layout.Version >= 5 => runRailIds[face],
                    _ => runWallId,
                };
            case TileKind.Door:
            case TileKind.Doorway:
                if (rel == 0) return t.Kind == TileKind.Doorway ? FloorOf(t) : concreteId;
                if (rel == ceiling) return t.Kind == TileKind.Doorway ? runCeilingId : concreteId;
                if (t.Pattern == WallPattern.RunSafeDoor) return rel <= 2 ? 0 : runSafeWallId;
                if (rel <= 2 && runDoorIds.TryGetValue(t.Pattern, out int[,] door)) return door[rel - 1, face];
                if (rel == 3)
                {
                    if (t.Pattern == WallPattern.RunTrueExit) return runSignBrightIds[face];
                    if (t.Pattern == WallPattern.RunFakeExit) return runSignDimIds[face];
                    // Over the start room's door to the hall, on the room's side: the room's red light, the bright sign so
                    // that it lights the whole room (the lit one, [0,7,9], left the bed and the "!" door in the dark)
                    if (t.Pattern == WallPattern.RunHallDoor) return runSignBrightIds[Facing(Opposite(t.Pier))];
                    if ((t.Detail & WorldLayout.RunBeacon) != 0) return runBeaconIds[face];
                }
                return runWallId;
        }

        // Floor
        if (rel == 0) return FloorOf(t);
        if (rel == ceiling)
            return t.Ceiling switch
            {
                CeilingKind.RunPanelDead => runPanelDeadId,
                CeilingKind.RunVent => runVentId,
                CeilingKind.RunSafeLight => runSafeLightId,
                CeilingKind.LampRed => runRedLightId, // the start room's own red panel (brighter than the Red Rooms' lamp)
                _ => runCeilingId,
            };
        if (rel == 4) return t.Ceiling == CeilingKind.RunExitSign ? runSignIds[(t.Detail & WorldLayout.RunSignWE) != 0 ? 1 : 0] : 0;
        if (t.Variant == Props.RunShelfStanding && rel <= 2) return runShelfIds[rel - 1, face];
        if (t.Variant == Props.RunCurtain && rel <= 4) return runCurtainIds[rel - 1, t.Pier is ArchPier.North or ArchPier.South ? 1 : 0];
        return rel == 1 ? PropBlock(t) : 0;
    }

    private int FloorOf(in Tile t)
    {
        if (t.Floor == FloorKind.RunBorder) return runBorderIds[(t.Detail & WorldLayout.RunBorderEast) != 0 ? 1 : 3];
        int id = floorIds[(int)t.Floor];
        return id != 0 ? id : runFloorId;
    }

    /// <summary>
    /// Level !'s ways in, drawn in another level's columns (a tile there with an <see cref="Unders"/> value from Level !'s
    /// block): the block at <paramref name="rel"/> above that level's floor, or -1 to leave the column to its own level.
    /// </summary>
    internal int RunEntranceBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        int face = Facing(t.Pier);
        switch (t.Under)
        {
            case Unders.RunEntrance:
                // Level 1: a red steel fire door where no door should be, a bright EXIT sign over it
                if (rel is 1 or 2) return runDoorIds[WallPattern.RunEntryDoor][rel - 1, face];
                if (rel == 3) return runSignConcreteIds[face];
                return -1;
            case Unders.RunFalseWall:
                // Level 2: a smooth new concrete wall across the end of the tunnel, that you can walk into
                if (rel is >= 1 and <= 3) return rel == 1 ? runFalseWallId : runFalseWallUpperId;
                return -1;
            case Unders.RunRedCorridor:
                // Level 37: hospital vinyl lit red, hospital walls, an EXIT door in the far wall
                // (A Level 37 corridor: dry, its ceiling Height above the floor)
                if (t.Kind == TileKind.Door)
                {
                    if (rel is 1 or 2) return runDoorIds[WallPattern.RunEntryDoor][rel - 1, face];
                    if (rel == 3) return runSignBrightIds[face];
                    return -1;
                }
                if (t.Kind == TileKind.Wall) return rel is >= 1 and <= 3 ? (rel == 1 ? runRailIds[face] : runWallId) : -1;
                if (rel == 0) return runFloorId;
                if (rel == t.Height - 1 && t.Ceiling == CeilingKind.RunExitSign) return runSignIds[(t.Detail & WorldLayout.RunSignWE) != 0 ? 1 : 0];
                if (rel == t.Height) return runCeilingId;
                return -1;
        }
        return -1;
    }
}
