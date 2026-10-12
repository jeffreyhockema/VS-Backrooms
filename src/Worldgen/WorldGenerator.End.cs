using System;
using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for The End (kept as level 16), laid out in WorldLayout.LevelEnd.cs. Its floor is
/// <see cref="WorldGeometry.FloorFor"/> (<see cref="WorldGeometry.EndDrop"/> below the other levels'), and it is lit over
/// a band from 24 below its floor, so the atrium's pendants and deck, up to rel 10, are lit.
///
/// A wall is the photo's: a vinyl cove at the bottom, off-white to eye level, the yellow band at rel 3, yellow-cream
/// above. A floor tile has its ceiling at <see cref="Tile.Height"/> (acoustic tile, or a troffer where the layout puts a
/// light), and concrete above it; under a soffit, the bulkhead at rel 4; in an atrium, the mezzanine deck at rel 5.
/// The cores of the fake realities are drawn by the levels they imitate (Level 0's, 4's, 5's and 9's own blocks).
/// </summary>
public sealed partial class WorldGenerator
{
    private int endRunwayId, endSoffitId, endPendantId, endSnowId;
    private readonly int[] endCarpetIds = new int[5], endConcreteIds = new int[3], endWallIds = new int[8], endColumnIds = new int[3],
        endCeilingIds = new int[3], endTrofferIds = new int[4], endDeckIds = new int[2], endExitDoorIds = new int[2], endStaffDoorIds = new int[2],
        endStoreDoorIds = new int[2], endRubbleIds = new int[2], endTreeIds = new int[2], endRailingIds = new int[4], endVentIds = new int[4],
        endExitSignIds = new int[4], endHangSignIds = new int[4];
    private readonly int[,,] endShelfIds = new int[5, 2, 4], endTallShelfIds = new int[3, 4, 4], endWallShelfIds = new int[2, 2, 4],
        endLadderIds = new int[2, 2, 4], endLetterIds = new int[2, 10, 4];
    private readonly int[,] endEndcapIds = new int[2, 2], endDeskIds = new int[5, 4], endTerminalIds = new int[5, 4], endFurnitureIds = new int[8, 4],
        endFrameIds = new int[2, 4], endCatalogueIds = new int[2, 4], endStockIds = new int[4, 4], endEscalatorIds = new int[3, 4], endPosterIds = new int[4, 4];

    /// <summary>The End's blocks that the asset script has not made yet (looked up once; logged once).</summary>
    private readonly List<string> endMissing = new();

    /// <summary>One of The End's blocks by its path, or a stand-in until the asset exists.</summary>
    private int EndBlock(string path, int fallback)
    {
        if (modBlocks.TryGetValue(path, out int id)) return id;
        endMissing.Add(path);
        return fallback;
    }

    /// <summary>Looks up the level's blocks, once, when the generator is made.</summary>
    private void InitEnd()
    {
        int carpet = floorIds[(int)FloorKind.OfficeCarpet], wall = officeWallId, ceiling = officeCeilingId;
        string[] carpets = { "plain", "dusty", "worn", "stained", "snowy" };
        for (int i = 0; i < 5; i++) endCarpetIds[i] = EndBlock("end-carpet-" + carpets[i], carpet);
        endRunwayId = EndBlock("end-runway-plain", carpet);
        string[] concrete = { "plain", "line-ns", "line-we" };
        for (int i = 0; i < 3; i++) endConcreteIds[i] = EndBlock("end-concrete-" + concrete[i], concreteId);
        string[] walls = { "base", "lower", "ghost", "cracked", "band", "upper", "uppercracked", "block" };
        for (int i = 0; i < walls.Length; i++) endWallIds[i] = EndBlock("end-wall-" + walls[i], wall);
        string[] columns = { "sage", "slate", "slat" };
        for (int i = 0; i < 3; i++) endColumnIds[i] = EndBlock("end-column-" + columns[i], wall);
        string[] ceilings = { "plain", "stained", "missing" };
        for (int i = 0; i < 3; i++) endCeilingIds[i] = EndBlock("end-ceiling-" + ceilings[i], ceiling);
        endTrofferIds[0] = EndBlock("end-troffer-on", officeLightIds[0]);
        endTrofferIds[1] = EndBlock("end-troffer-lit", officeLightIds[1]);
        endTrofferIds[2] = EndBlock("end-troffer-off", officeLightIds[2]);
        endTrofferIds[3] = EndBlock("end-troffer-flicker", officeLightIds[3]);
        endSoffitId = EndBlock("end-soffit-plain", wall);
        endDeckIds[0] = EndBlock("end-deck-plain", ceiling);
        endDeckIds[1] = EndBlock("end-deck-troffer", officeLightIds[0]);
        endPendantId = EndBlock("end-pendant", 0);
        endSnowId = BlockId("game:snowlayer-1");

        string[] shelfKinds = { "empty", "books", "dusty", "endpanel", "leaning" }, two = { "lower", "upper" };
        string[] tallKinds = { "empty", "books", "rail" }, tallParts = { "base", "mid1", "mid2", "crown" };
        string[] deskKinds = { "straight", "curveout", "curvein", "end", "gate" }, states = { "off", "on", "static", "party", "dead" };
        string[] furniture = { "table", "lamptable", "chair", "wrapped", "armchair", "carrel", "displaytable", "magrack" };
        string[] stock = { "pallet", "trolley", "ladderwrapped", "kit" }, escalator = { "step", "top", "bottom" };
        string[] posters = { "yellow", "pink", "green", "notice" }, families = { "soffit", "wall" };
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            for (int k = 0; k < 5; k++)
                for (int p = 0; p < 2; p++) endShelfIds[k, p, f] = EndBlock($"end-shelf-{shelfKinds[k]}-{two[p]}-{side}", 0);
            for (int k = 0; k < 3; k++)
                for (int p = 0; p < 4; p++) endTallShelfIds[k, p, f] = EndBlock($"end-tallshelf-{tallKinds[k]}-{tallParts[p]}-{side}", 0);
            for (int k = 0; k < 2; k++)
                for (int p = 0; p < 2; p++) endWallShelfIds[k, p, f] = EndBlock($"end-wallshelf-{shelfKinds[k]}-{two[p]}-{side}", 0);
            for (int k = 0; k < 5; k++) endDeskIds[k, f] = EndBlock($"end-desk-{deskKinds[k]}-{side}", 0);
            for (int k = 0; k < 5; k++) endTerminalIds[k, f] = EndBlock($"end-terminal-{states[k]}-{side}", 0);
            for (int k = 0; k < furniture.Length; k++) endFurnitureIds[k, f] = EndBlock($"end-furniture-{furniture[k]}-{side}", 0);
            for (int k = 0; k < 2; k++) endCatalogueIds[k, f] = EndBlock($"end-catalogue-{(k == 0 ? "shut" : "open")}-{side}", 0);
            for (int k = 0; k < 4; k++) endStockIds[k, f] = EndBlock($"end-stock-{stock[k]}-{side}", 0);
            for (int k = 0; k < 3; k++) endEscalatorIds[k, f] = EndBlock($"end-escalator-{escalator[k]}-{side}", 0);
            for (int k = 0; k < 4; k++) endPosterIds[k, f] = EndBlock($"end-poster-{posters[k]}-{side}", 0);
            endLadderIds[0, 0, f] = EndBlock($"end-ladder-rolling-lower-{side}", 0);
            endLadderIds[0, 1, f] = EndBlock($"end-ladder-rolling-upper-{side}", 0);
            endLadderIds[1, 0, f] = endLadderIds[1, 1, f] = EndBlock($"end-ladder-wall-lower-{side}", 0);
            for (int fam = 0; fam < 2; fam++)
                for (int l = 0; l < 10; l++)
                {
                    string letter = l == 0 ? "blank" : WorldLayout.EndLetters[l].ToString();
                    endLetterIds[fam, l, f] = EndBlock($"end-letter-{families[fam]}-{letter}-{side}", fam == 0 ? endSoffitId : endWallIds[4]);
                }
            for (int p = 0; p < 2; p++) endFrameIds[p, f] = EndBlock($"end-frame-{two[p]}-{side}", 0);
            endRailingIds[f] = EndBlock($"end-railing-{side}", 0);
            endVentIds[f] = EndBlock($"end-vent-{side}", endWallIds[7]);
            endExitSignIds[f] = EndBlock($"end-exitsign-lit-{side}", endWallIds[4]);
            endHangSignIds[f] = EndBlock($"end-hangsign-{side}", 0);
        }
        for (int k = 0; k < 2; k++) endEndcapIds[k, 0] = EndBlock($"end-endcap-{(k == 0 ? "plain" : "tagged")}-lower", 0);
        for (int k = 0; k < 2; k++) endEndcapIds[k, 1] = EndBlock($"end-endcap-{(k == 0 ? "plain" : "tagged")}-upper", 0);
        endExitDoorIds[0] = EndBlock("end-exitdoor-lower", metalDoorLowerId);
        endExitDoorIds[1] = EndBlock("end-exitdoor-upper", metalDoorUpperId);
        endStaffDoorIds[0] = EndBlock("end-staffdoor-lower", officeDoorLowerId);
        endStaffDoorIds[1] = EndBlock("end-staffdoor-upper", officeDoorUpperId);
        endStoreDoorIds[0] = EndBlock("end-storedoor-lower", rowhouseDoorLowerId);
        endStoreDoorIds[1] = EndBlock("end-storedoor-upper", rowhouseDoorUpperId);
        endRubbleIds[0] = EndBlock("end-rubble-shelf", 0);
        endRubbleIds[1] = EndBlock("end-rubble-ceiling", 0);
        endTreeIds[0] = EndBlock("end-tree-trunk", 0);
        endTreeIds[1] = EndBlock("end-tree-top", 0);

        floorIds[(int)FloorKind.EndCarpet] = endCarpetIds[0];
        floorIds[(int)FloorKind.EndCarpetDusty] = endCarpetIds[1];
        floorIds[(int)FloorKind.EndCarpetWorn] = endCarpetIds[2];
        floorIds[(int)FloorKind.EndCarpetStained] = endCarpetIds[3];
        floorIds[(int)FloorKind.EndCarpetSnow] = endCarpetIds[4];
        floorIds[(int)FloorKind.EndRunway] = endRunwayId;
        floorIds[(int)FloorKind.EndConcrete] = endConcreteIds[0];
        floorIds[(int)FloorKind.EndConcreteLine] = endConcreteIds[1];

        if (endMissing.Count > 0)
            api.Logger.Warning("[backrooms] The End: {0} blocks are not made yet (stand-ins used), e.g. {1}", endMissing.Count, endMissing[0]);
    }

    /// <summary>The block (and fluid) at <paramref name="rel"/> above the level's floor in the column of tile <paramref name="t"/>.</summary>
    private int LevelEndBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < 0) return concreteId;
        int height = t.Height == 0 ? WorldLayout.EndCeilingHeight : t.Height;
        // The heart of a fake reality is the place it imitates, drawn by that place's own level
        if (t.Zone == 5 && t.Detail is >= 1 and <= 4 or 6) return EndFakeBlock(t, gx, gz, rel, height);
        if (rel == 0)
        {
            if (t.Kind is TileKind.Floor or TileKind.Doorway) return floorIds[(int)t.Floor] is int f and not 0 ? f : endCarpetIds[0];
            return concreteId;
        }
        int facing = Facing(t.Pier);
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (rel > WorldLayout.EndAtriumHeight) return concreteId;
                return EndWallBlock(t, gx, gz, rel, facing);
            case TileKind.Door:
                if (rel > WorldLayout.EndAtriumHeight) return concreteId;
                if (t.Pattern == WallPattern.EndExit)
                {
                    if (rel <= 2) return endExitDoorIds[rel - 1];
                    if (rel == 3) return endExitSignIds[facing];
                }
                else if (t.Pattern == WallPattern.EndStaff && rel <= 2) return endStaffDoorIds[rel - 1];
                else if (t.Zone >= 4 && rel <= 3) return EndFakeDelegate(t, gx, gz, rel);
                return t.Zone == 2 ? endWallIds[7] : rel == 3 ? endWallIds[4] : endWallIds[5];
            case TileKind.Doorway:
                if (rel <= 3) return t.Zone >= 4 && t.Pattern != WallPattern.EndWall && rel == 3 ? EndFakeDelegate(t, gx, gz, rel) : 0;
                if (rel > WorldLayout.EndAtriumHeight) return concreteId;
                return t.Zone == 2 || t.Pattern == WallPattern.EndStockWall ? endWallIds[7] : endWallIds[5];
        }

        // A floor tile: its ceiling, and the plenum above
        if (rel > height) return concreteId;
        if (rel == height)
        {
            if (t.Overhead == Overheads.EndMissingTile) return endCeilingIds[2];
            if (t.Depth == 1 && t.Detail != 0) return EndFakeCeiling(t);
            return t.Ceiling switch
            {
                CeilingKind.LightOn => endTrofferIds[0],
                CeilingKind.LightLit => endTrofferIds[1],
                CeilingKind.LightOff => endTrofferIds[2],
                CeilingKind.LightFlicker => endTrofferIds[3],
                _ => ((gx * 31 + gz * 17) & 15) == 0 ? endCeilingIds[1] : endCeilingIds[0],
            };
        }
        // Overhead: the soffit, the mezzanine deck and its railing, a pendant
        switch (t.Overhead)
        {
            case Overheads.EndSoffit when rel == 4: return endSoffitId;
            case Overheads.EndSoffitLetter when rel == 4: return endLetterIds[0, Math.Min((int)t.Stack, 9), facing];
            case Overheads.EndDeck or Overheads.EndDeckEdge when rel == WorldLayout.EndDeckRel:
                return endDeckIds[t.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit ? 1 : 0];
            case Overheads.EndDeckEdge when rel == WorldLayout.EndDeckRel + 1: return endRailingIds[facing];
            case Overheads.EndPendant when rel == WorldLayout.EndPendantRel: return endPendantId;
        }
        return EndPropBlock(t, rel, facing);
    }

    /// <summary>A wall of The End at a height: the painted wall with its band, a column, the stockroom's block, or an imitated paper.</summary>
    private int EndWallBlock(in Tile t, int gx, int gz, int rel, int facing)
    {
        switch (t.Pattern)
        {
            case WallPattern.EndColumn:
            case WallPattern.EndColumnSlate:
                if (rel == 2 && t.Variant is >= Decor.EndPoster and < Decor.EndPoster + 4) return endPosterIds[t.Variant - Decor.EndPoster, facing];
                return rel <= 2 ? endColumnIds[2] : endColumnIds[t.Pattern == WallPattern.EndColumn ? 0 : 1];
            case WallPattern.EndStockWall:
                if (rel == 3 && t.Under == Unders.EndVentWall) return endVentIds[facing];
                return endWallIds[7];
            case WallPattern.EndWall:
                if (rel == 1) return endWallIds[0];
                if (rel == 2)
                {
                    if (t.Variant is >= Decor.EndPoster and < Decor.EndPoster + 4) return endPosterIds[t.Variant - Decor.EndPoster, facing];
                    return t.Variant == Decor.EndGhost ? endWallIds[2] : t.Variant == Decor.EndCrack ? endWallIds[3] : endWallIds[1];
                }
                if (rel == 3) return t.Variant == Decor.EndLetter ? endLetterIds[1, Math.Min((int)t.Stack, 9), facing] : endWallIds[4];
                return t.Variant == Decor.EndCrack ? endWallIds[6] : endWallIds[5];
        }
        // The paper of a fake reality's blend: drawn by the level it belongs to, its top course carried on up
        return EndFakeDelegate(t, gx, gz, Math.Min(rel, 3));
    }

    /// <summary>What stands on a floor tile at a height: the level's props, tall ones by part.</summary>
    private int EndPropBlock(in Tile t, int rel, int facing)
    {
        // A stopped escalator: solid under the step, the step, then air
        if (t.Variant == Props.EndEscalator)
        {
            if (rel < t.Stair) return endWallIds[7];
            return rel == t.Stair ? endEscalatorIds[Math.Min((int)t.Stack, 2), facing] : 0;
        }
        int part = rel - 1;
        switch (t.Variant)
        {
            case 0: return 0;
            case Props.EndShelf: return part <= 1 ? endShelfIds[Math.Min((int)t.Stack, 4), part, facing] : 0;
            case Props.EndTallShelf: return part <= 3 ? endTallShelfIds[Math.Min((int)t.Stack, 2), part, facing] : 0;
            case Props.EndWallShelf: return part <= 1 ? endWallShelfIds[Math.Min((int)t.Stack, 1), part, facing] : 0;
            case Props.EndEndcap: return part <= 1 ? endEndcapIds[Math.Min((int)t.Stack, 1), part] : 0;
            case Props.EndDesk:
                if (part == 0) return endDeskIds[Math.Min(t.Stack & 7, 4), facing];
                return part == 1 && (t.Stack & 8) != 0 ? endTerminalIds[0, facing] : 0;
            case Props.EndFurniture: return part == 0 ? endFurnitureIds[Math.Min((int)t.Stack, 7), facing] : 0;
            case Props.EndCatalogue: return part == 0 ? endCatalogueIds[Math.Min((int)t.Stack, 1), facing] : 0;
            case Props.EndStock: return part == 0 ? endStockIds[Math.Min((int)t.Stack, 3), facing] : 0;
            case Props.EndRubble: return part == 0 ? endRubbleIds[Math.Min((int)t.Stack, 1)] : 0;
            case Props.EndTree:
                int top = Math.Max(2, (int)t.Stack);
                return rel < top ? endTreeIds[0] : rel == top ? endTreeIds[1] : 0;
            case Props.EndLadder:
                if (t.Stack == 0) return part <= 1 ? endLadderIds[0, part, facing] : 0;
                return part <= 2 ? endLadderIds[1, 0, facing] : 0;
            case Props.EndSnow: return part == 0 ? endSnowId : 0;
            case Props.Cooler: return part == 0 ? coolerIds[facing] : 0;
            case Props.Desk: return part == 0 ? deskIds[facing] : 0;
            case Props.OfficeChair: return part == 0 ? chairIds[facing] : 0;
            case Props.Partition: return part == 0 ? (t.Pier is ArchPier.North or ArchPier.South ? partitionNsId : partitionWeId) : 0;
        }
        return part == 0 ? PropBlock(t) : 0;
    }

    /// <summary>
    /// The heart of a fake reality: the imitated level draws its floor, walls, doors and what stands on the floor (up to
    /// rel 3); The End draws the ceiling in the imitated level's own blocks at <paramref name="height"/>, and solid above.
    /// </summary>
    private int EndFakeBlock(in Tile t, int gx, int gz, int rel, int height)
    {
        if (rel == 0) return t.IsWallLike ? concreteId : floorIds[(int)t.Floor];
        if (rel > height) return concreteId;
        if (rel == height) return t.IsWallLike ? concreteId : EndFakeCeiling(t);
        return EndFakeDelegate(t, gx, gz, Math.Min(rel, 3));
    }

    /// <summary>A block of an imitated level at a height of at most 3, by the fake reality's kind.</summary>
    private int EndFakeDelegate(in Tile t, int gx, int gz, int rel)
    {
        switch ((WorldLayout.EndFake)t.Detail)
        {
            case WorldLayout.EndFake.Lobby:
                return Level0Block(t, rel, out _);
            case WorldLayout.EndFake.Office:
                return Level4Block(t, rel, gx, gz);
            case WorldLayout.EndFake.Hotel:
                return Level5Block(t, rel, gx, gz);
            case WorldLayout.EndFake.House:
            case WorldLayout.EndFake.Home:
                // (No roof: a house's rooms with nothing over them but The End's ceiling)
                if (t.Kind == TileKind.Floor && rel == 1 && t.Variant >= 40) return PropBlock(t);
                return Level9Block(t, gx, gz, rel);
        }
        return t.IsWallLike ? endWallIds[5] : 0;
    }

    /// <summary>The ceiling of an imitated place, with its own light fittings.</summary>
    private int EndFakeCeiling(in Tile t)
    {
        bool on = t.Ceiling is CeilingKind.LightOn or CeilingKind.LightLit;
        switch ((WorldLayout.EndFake)t.Detail)
        {
            case WorldLayout.EndFake.Lobby: return CeilingBlock0(t.Ceiling);
            case WorldLayout.EndFake.Office:
                return t.Ceiling switch
                {
                    CeilingKind.LightOn => officeLightIds[0],
                    CeilingKind.LightLit => officeLightIds[1],
                    CeilingKind.LightOff => officeLightIds[2],
                    CeilingKind.LightFlicker => officeLightIds[3],
                    _ => officeCeilingId,
                };
            case WorldLayout.EndFake.Hotel: return on ? domeIds[0] : creamCeilingId;
            case WorldLayout.EndFake.House:
            case WorldLayout.EndFake.Home: return t.Ceiling == CeilingKind.LightOn ? houseLightIds[1] : houseCeilingId;
        }
        return endCeilingIds[0];
    }

    /// <summary>
    /// The End's ways in, drawn in the levels they stand in (the tile's <see cref="Tile.Under"/> is one of The End's):
    /// Level 1's EXIT door and the sign over it, Level 4's lone wooden doorway, the city bookstore's glass door. -1 where
    /// the level draws the column itself.
    /// </summary>
    private int EndEntranceBlock(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        int facing = Facing(t.Pier);
        switch (t.Under)
        {
            case Unders.EndExitL1 when t.Kind == TileKind.Door:
                return rel is 1 or 2 ? endExitDoorIds[rel - 1] : rel == 3 ? endExitSignIds[facing] : -1;
            case Unders.EndFrame when t.Variant == Props.EndFrame:
                return rel is 1 or 2 ? endFrameIds[rel - 1, facing] : -1;
            case Unders.EndBookstore when t.Kind == TileKind.Door:
                return rel is 1 or 2 ? endStoreDoorIds[rel - 1] : -1;
        }
        return -1;
    }
}
