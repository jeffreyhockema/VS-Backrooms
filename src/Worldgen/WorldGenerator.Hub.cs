using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for The Hub (kept as level 17), laid out in WorldLayout.LevelHub.cs. Its floor is
/// <see cref="WorldGeometry.FloorFor"/> (<see cref="WorldGeometry.HubDrop"/> below the other levels').
///
/// A road tunnel: asphalt on rel 0 with the sidewalks' half slabs on rel 1, walls of seamed concrete slabs, a flat
/// concrete ceiling one block over the air (<see cref="Tile.Height"/>), caged amber lamps on the walls, jet fans and lane
/// signals hanging from the ceiling. The doors stand on rel 1-4 with their carved sigil on rel 5. The codes are those of
/// the plan's asset manifest (docs/design/new-levels/hub-plan.md, with its phase 2 changes); where a block is missing the
/// tunnel falls back to plain concrete, so the layout can be looked at before the assets exist.
/// </summary>
public sealed partial class WorldGenerator
{
    private int hubAsphaltId, hubWornId, hubPatchId, hubStudId, hubSidewalkId, hubCeilingId, hubMarbleId, hubAshlarId,
        hubVoidId, hubFalseWallId, hubTileId;
    private readonly int[] hubWallIds = new int[4], hubCrumbIds = new int[3], hubFanIds = new int[2], hubCurbIds = new int[4], hubEdgeLineIds = new int[4],
        hubCurbCornerIds = new int[4], hubCurbInnerIds = new int[4], hubLineIds = new int[8];
    /// <summary>(Layout version 9) the rounded tunnels' vault pieces, by piece index (<see cref="WorldLayout.HubVaultPieces"/>) and facing.</summary>
    private int[,] hubVaultIds;
    private readonly int[,] hubLampIds = new int[2, 4], hubSignalIds = new int[2, 4], hubStencilIds = new int[12, 4],
        hubPlaqueIds = new int[3, 4], hubSigilIds = new int[45, 4], hubSigilSideIds = new int[2, 4], hubServiceIds = new int[2, 4];
    private readonly int[,,] hubDoorIds = new int[3, 4, 4], hubPinkIds = new int[3, 4, 4], hubOrnateIds = new int[2, 3, 4], hubForbiddenIds = new int[2, 3, 4],
        hubPilasterIds = new int[3, 4, 4];
    private readonly int[] hubStairIds = new int[4], hubBalustradeIds = new int[4], hubBannerIds = new int[4], hubCabinetIds = new int[4],
        hubRegisterIds = new int[4], hubDoormatIds = new int[4], hubAmberSignIds = new int[4];
    /// <summary>Level 188's window, as the Hub's tunnel shows it: parts ll, lr, ul, ur by facing.</summary>
    private readonly int[,] hubWindowIds = new int[4, 4];
    private int hubInlayId, hubCentreId, hubDuskId, hubStatueId, hubStatueFillId, hubAshlarWornId;

    /// <summary>A block of the Hub's by code path, or a stand-in while the Hub's assets are missing (logged once per block).</summary>
    private int HubId(string path, int fallback)
    {
        if (modBlocks.TryGetValue(path, out int id)) return id;
        if (hubMissing.Count < 8) hubMissing.Add(path);
        hubMissingCount++;
        return fallback;
    }

    private readonly System.Collections.Generic.List<string> hubMissing = new();
    private int hubMissingCount;

    /// <summary>Looks up the level's blocks, once, when the generator is made.</summary>
    private void InitHub()
    {
        int wall = concreteWallId != 0 ? concreteWallId : concreteId;
        hubAsphaltId = HubId("hub-asphalt-plain", floorIds[(int)FloorKind.Concrete]);
        hubWornId = HubId("hub-asphalt-worn", hubAsphaltId);
        hubPatchId = HubId("hub-asphalt-patch", hubAsphaltId);
        hubStudId = HubId("hub-asphalt-stud", hubAsphaltId);
        hubSidewalkId = HubId("hub-sidewalk", 0);
        hubCeilingId = HubId("hub-ceiling", concreteCeilingId != 0 ? concreteCeilingId : concreteId);
        hubMarbleId = HubId("hub-marble-plain", floorIds[(int)FloorKind.Concrete]);
        hubAshlarId = HubId("hub-ashlar-plain", wall);
        hubAshlarWornId = HubId("hub-ashlar-worn", hubAshlarId);
        hubInlayId = HubId("hub-marble-inlay", hubMarbleId);
        hubCentreId = HubId("hub-marble-centre", hubMarbleId);
        hubDuskId = HubId("hub-dusklight", 0);
        hubStatueId = HubId("hub-statue", hubAshlarId);
        hubStatueFillId = HubId("hub-statuefill", 0);
        hubVoidId = HubId("hub-void", concreteId);
        hubTileId = modBlocks.TryGetValue("pooltile-plain", out int tile) ? tile : wall;
        // (Layout version 11) the road markings: the middle line straight (ns, we) and round a corner (ne, es, sw, wn:
        // joining those two sides' middles), and the give-way line across a narrow tunnel (for traffic running ns, we)
        for (int i = 0; i < HubLineKinds.Length; i++) hubLineIds[i] = HubId($"hub-asphalt-line-{HubLineKinds[i]}", hubAsphaltId);
        string[] seams = { "plain", "left", "bottom", "corner" };
        for (int i = 0; i < 4; i++) hubWallIds[i] = HubId($"hub-wall-{seams[i]}", wall);
        hubFalseWallId = HubId("hub-falsewall", 0);
        for (int i = 1; i <= 2; i++) hubCrumbIds[i] = HubId($"hub-tilecrumb-{i}", hubWallIds[0]);
        hubFanIds[0] = HubId("hub-jetfan-ns", 0);
        hubFanIds[1] = HubId("hub-jetfan-we", 0);
        hubVaultIds = new int[WorldLayout.HubVaultPieces.Length, 4];
        for (int p = 2; p < WorldLayout.HubVaultPieces.Length; p++)
            for (int f = 0; f < 4; f++) hubVaultIds[p, f] = HubId($"hub-vault-{WorldLayout.HubVaultPieces[p]}-{Sides[f]}", hubCeilingId);
        string[] cols = { "l", "c", "r" };
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            hubLampIds[0, f] = HubId($"hub-lamp-on-{side}", hubWallIds[0]);
            hubLampIds[1, f] = HubId($"hub-lamp-dead-{side}", hubWallIds[0]);
            hubCurbIds[f] = HubId($"hub-curb-{side}", hubSidewalkId);
            hubCurbCornerIds[f] = HubId($"hub-curbcorner-{side}", hubCurbIds[f]);
            hubCurbInnerIds[f] = HubId($"hub-curbinner-{side}", hubSidewalkId);
            hubEdgeLineIds[f] = HubId($"hub-asphalt-edge-{side}", hubAsphaltId);
            hubSignalIds[0, f] = HubId($"hub-lanesignal-go-{side}", 0);
            hubSignalIds[1, f] = HubId($"hub-lanesignal-stop-{side}", 0);
            for (int n = 1; n <= 10; n++) hubStencilIds[n, f] = HubId($"hub-stencil-{n}-{side}", hubWallIds[0]);
            hubStencilIds[11, f] = HubId($"hub-stencil-tower-{side}", hubWallIds[0]);
            string[] plaques = { "1", "11", "178" };
            for (int p = 0; p < 3; p++) hubPlaqueIds[p, f] = HubId($"hub-plaque-{plaques[p]}-{side}", hubWallIds[0]);
            for (int s = 0; s <= 44; s++) hubSigilIds[s, f] = HubId($"hub-sigil-{s}-{side}", hubWallIds[0]);
            hubSigilSideIds[0, f] = HubId($"hub-sigilside-l-{side}", hubWallIds[0]);
            hubSigilSideIds[1, f] = HubId($"hub-sigilside-r-{side}", hubWallIds[0]);
            hubServiceIds[0, f] = HubId($"hub-servicedoor-lower-{side}", metalDoorLowerId);
            hubServiceIds[1, f] = HubId($"hub-servicedoor-upper-{side}", metalDoorUpperId);
            for (int c = 0; c < 3; c++)
                for (int row = 0; row < 4; row++)
                {
                    hubDoorIds[c, row, f] = HubId($"hub-door-{cols[c]}-{row + 1}-{side}", concreteId);
                    hubPinkIds[c, row, f] = HubId($"hub-pinkdoor-{cols[c]}-{row + 1}-{side}", hubDoorIds[c, row, f]);
                }
            for (int leaf = 0; leaf < 2; leaf++)
                for (int row = 0; row < 3; row++)
                {
                    hubOrnateIds[leaf, row, f] = HubId($"hub-ornatedoor-entrance-{(leaf == 0 ? "l" : "r")}{row + 1}-{side}", hubAshlarId);
                    hubForbiddenIds[leaf, row, f] = HubId($"hub-ornatedoor-forbidden-{(leaf == 0 ? "l" : "r")}{row + 1}-{side}", hubOrnateIds[leaf, row, f]);
                }
            string[] pilaster = { "base", "shaft", "capital" };
            for (int part = 0; part < 3; part++) hubPilasterIds[part, 0, f] = HubId($"hub-pilaster-{pilaster[part]}-{side}", 0);
            hubStairIds[f] = HubId($"hub-marblestairs-{side}", hubMarbleId);
            hubBalustradeIds[f] = HubId($"hub-balustrade-{side}", 0);
            hubBannerIds[f] = HubId($"hub-megbanner-{side}", 0);
            hubCabinetIds[f] = HubId($"hub-keycabinet-{side}", 0);
            hubRegisterIds[f] = HubId($"hub-whiteboard-{side}", 0);
            hubDoormatIds[f] = HubId($"hub-doormat-{side}", 0);
            hubAmberSignIds[f] = HubId($"hub-ambersign-{side}", 0);
            string[] parts = { "ll", "lr", "ul", "ur" };
            for (int part = 0; part < 4; part++)
                hubWindowIds[part, f] = modBlocks.TryGetValue($"l188-window-lit-{parts[part]}-{side}", out int windowId) ? windowId : 0;
        }
        if (hubMissingCount > 0)
            api.Logger.Warning("[backrooms] {0} of the Hub's blocks are missing (plain concrete stands in for them), e.g. {1}", hubMissingCount, string.Join(", ", hubMissing));

        // Level 1's way into the Hub: the grey door with the Hub's own sigil over it, on Level 1's walls
        foreach (WallPattern pattern in new[] { WallPattern.Concrete, WallPattern.WhiteBlock })
            for (int f = 0; f < 4; f++)
            {
                decorIds[(int)pattern, Decor.HubEntranceDoor, 1, f] = hubServiceIds[0, f];
                decorIds[(int)pattern, Decor.HubEntranceDoor, 2, f] = hubServiceIds[1, f];
                decorIds[(int)pattern, Decor.HubEntranceDoor, 3, f] = hubSigilIds[0, f];
            }
    }

    /// <summary>The block (and fluid) at <paramref name="rel"/> above the level's floor in the column of tile <paramref name="t"/>.</summary>
    private int LevelHubBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        int f = Facing(t.Pier);
        switch (t.Kind)
        {
            // (The roundabout's inner corners lie in the Tower's zone too, and were built as the Tower, with its gallery
            // floors and stair across the road; in layout version 9 they are the tunnel they are, vaulted like the rest)
            case TileKind.Floor or TileKind.Pit when t.Zone is WorldLayout.HubZoneTower or WorldLayout.HubZoneVoid && t.Height > WorldLayout.HubSideHeight
                && !(layout.Version >= 9 && HubVaultAt(gx, gz, out _, out _)):
                return HubTowerBlock(t, gx, gz, rel);
            case TileKind.Floor or TileKind.Pit:
            {
                int height = t.Height == 0 ? WorldLayout.HubMainHeight : t.Height;
                if (t.Kind == TileKind.Pit && rel <= 0)
                {
                    // A rectangular hole in the road, down into black
                    return rel >= -2 ? 0 : rel == -3 ? hubVoidId : concreteId;
                }
                // (Layout version 9) the tunnels are vaulted: straight walls up to rel 6, then the roof curves over
                bool round = false;
                if (layout.Version >= 9 && rel >= WorldLayout.HubVaultFrom)
                {
                    // A false wall stands in the wall's line: above the doorway-high gap it is the wall
                    if (t.Under == Unders.HubFalseWall) return rel <= WorldLayout.HubVaultTop ? HubWallBlock(t, gx, gz, rel) : concreteId;
                    if (HubVaultAt(gx, gz, out byte[] cells, out ArchPier[] dirs))
                    {
                        if (rel > WorldLayout.HubVaultTop) return concreteId;
                        int cell = cells[rel - WorldLayout.HubVaultFrom];
                        if (cell == 1) return t.Floor == FloorKind.PoolTile ? hubTileId : hubCeilingId;
                        if (cell >= 2) return hubVaultIds[cell, Facing(dirs[rel - WorldLayout.HubVaultFrom])];
                        round = true;
                    }
                }
                if (rel < 0 || !round && rel > height + 1) return concreteId;
                if (!round && rel == height + 1) return t.Floor == FloorKind.PoolTile ? hubTileId : t.Zone == WorldLayout.HubZoneTower ? hubAshlarId : hubCeilingId;
                if (rel == 0)
                {
                    // (Layout version 9) the road's white edge line along the kerb
                    if (layout.Version >= 9 && t.Floor is FloorKind.HubAsphalt or FloorKind.HubAsphaltWorn or FloorKind.HubAsphaltPatch
                        && HubEdgeLine(gx, gz) is int edge and >= 0) return edge;
                    return t.Floor switch
                    {
                        FloorKind.HubStud => hubStudId,
                        FloorKind.HubAsphaltWorn => hubWornId,
                        FloorKind.HubAsphaltPatch => hubPatchId,
                        FloorKind.HubMarble or FloorKind.HubMarbleInlay => hubMarbleId,
                        FloorKind.PoolTile => hubTileId,
                        FloorKind.HubLine => hubLineIds[HubLinePiece(t, gx, gz)],
                        FloorKind.HubGiveWay => hubLineIds[t.Pier == ArchPier.East ? 7 : 6],
                        // (Layout version 11) under a sidewalk's rounded corner the road shows round the kerb
                        FloorKind.HubSidewalk => layout.Version >= 11 && HubKerbV11(gx, gz) is var k && k.Kind == KerbCorner ? hubAsphaltId : concreteId,
                        _ => hubAsphaltId,
                    };
                }
                // A stretch of wall that isn't there: it looks like the wall, and you walk into it
                if (t.Under == Unders.HubFalseWall) return hubFalseWallId != 0 ? hubFalseWallId : 0;
                if (rel == 1 && t.Floor == FloorKind.HubSidewalk)
                {
                    if (layout.Version >= 11)
                    {
                        var (kind, facing) = HubKerbV11(gx, gz);
                        return kind switch
                        {
                            KerbStraight => hubCurbIds[Facing(facing)],
                            KerbCorner => hubCurbCornerIds[Facing(facing)],
                            KerbInner => hubCurbInnerIds[Facing(facing)],
                            _ => hubSidewalkId,
                        };
                    }
                    return layout.Version >= 9 ? HubKerb(gx, gz) : hubSidewalkId;
                }
                // What hangs on the wall behind this tile: a lamp, a stencil, a plaque, the M.E.G.'s banner and key cabinet
                if (t.Detail != 0 && rel == t.Depth)
                {
                    int hung = t.Detail switch
                    {
                        WorldLayout.HubWallLamp => hubLampIds[0, f],
                        WorldLayout.HubWallDeadLamp => hubLampIds[1, f],
                        WorldLayout.HubWallStencil => hubStencilIds[Math.Clamp((int)t.Pipe, 1, 11), f],
                        WorldLayout.HubWallPlaque => hubPlaqueIds[t.Pipe switch { 1 => 0, 11 => 1, _ => 2 }, f],
                        WorldLayout.HubWallBanner => hubBannerIds[f],
                        WorldLayout.HubWallCabinet => hubCabinetIds[f],
                        _ => 0,
                    };
                    if (hung != 0) return hung;
                }
                // The outposts' things, standing on the road at the kerb
                if (rel == 1)
                {
                    switch (t.Variant)
                    {
                        case Props.HubRegister: return hubRegisterIds[f];
                        case Props.HubDoormat: return hubDoormatIds[f];
                        case Props.HubAmberSign: return hubAmberSignIds[f];
                    }
                }
                // (Under a vault's flat crown in layout version 9)
                if (rel == (layout.Version >= 9 && t.Overhead != 0 && HubVaultAt(gx, gz, out _, out _) ? WorldLayout.HubVaultTop - 1 : height))
                {
                    switch (t.Overhead)
                    {
                        case Overheads.HubFanNS: return hubFanIds[0];
                        case Overheads.HubFanWE: return hubFanIds[1];
                        case Overheads.HubSignalNS: return hubSignalIds[0, f];
                        case Overheads.HubSignalWE: return hubSignalIds[1, f];
                    }
                }
                return 0;
            }
            case TileKind.Door when t.Pattern == WallPattern.HubDoor:
            {
                if (rel <= 0) return concreteId;
                if (rel <= 4)
                {
                    // The door to Level 974 is pink, tied with a ribbon like a present
                    return (t.Detail == 18 ? hubPinkIds : hubDoorIds)[Math.Min((int)t.Stack, 2), rel - 1, f];
                }
                if (rel == 5) return t.Stack == 1 ? hubSigilIds[Math.Min((int)t.Detail, 44), f] : hubSigilSideIds[t.Stack == 0 ? 0 : 1, f];
                return HubWallBlock(t, gx, gz, rel);
            }
            case TileKind.Door when t.Pattern == WallPattern.HubServiceDoor:
                return rel == 1 ? hubServiceIds[0, f] : rel == 2 ? hubServiceIds[1, f] : HubWallBlock(t, gx, gz, rel);
            case TileKind.Door when t.Pattern == WallPattern.HubOrnate:
                return rel is >= 1 and <= 3 ? hubOrnateIds[Math.Min((int)t.Stack, 1), rel - 1, f] : rel <= 0 ? concreteId : hubAshlarId;
        }
        if (t.Zone == WorldLayout.HubZoneVoid) return hubVoidId; // the storm void's walls: nothing to see
        // The window into Level 188: lit, its blind half up (Level 188's blocks; plain wall until they exist)
        if (t.Under == Unders.HubWindow188 && rel is 2 or 3)
        {
            int part = (rel == 3 ? 2 : 0) + Math.Min((int)t.Stack, 1);
            int window = hubWindowIds[part, Facing(t.Pier)];
            if (window != 0) return window;
        }
        if (t.Pattern == WallPattern.HubAshlar) return HubTowerWall(t, gx, gz, rel);
        if (t.Pattern == WallPattern.PoolTile) return hubTileId;
        return HubWallBlock(t, gx, gz, rel);
    }

    // ---- The Tower ----

    private static ArchPier Cardinal(double x, double z) =>
        Math.Abs(x) >= Math.Abs(z) ? (x > 0 ? ArchPier.East : ArchPier.West) : (z > 0 ? ArchPier.South : ArchPier.North);

    /// <summary>The right hand of someone looking at the front of a thing facing <paramref name="facing"/>.</summary>
    private static (int X, int Z) HubRightOf(ArchPier facing) => facing switch
    {
        ArchPier.North => (-1, 0),
        ArchPier.South => (1, 0),
        ArchPier.East => (0, -1),
        _ => (0, 1),
    };

    /// <summary>How far round the wall (in blocks) a column at an angle lies from the nearest of ten directions, from <paramref name="offset"/> on.</summary>
    private static double OffTen(double angle, double offset, double r, out double nearest)
    {
        double step = Math.PI / 5, turned = angle - offset;
        double k = Math.Round(turned / step);
        nearest = offset + k * step;
        return r * Math.Sin(turned - k * step);
    }

    /// <summary>
    /// A column of the Tower's rotunda or of its balcony and void (see <see cref="WorldLayout.BuildHubTower"/>): the floor,
    /// the statue, the spiral stair up the inside of the wall, the galleries with their balustrades, the meeting hall, the
    /// pilasters, and the dusk light from nowhere.
    /// </summary>
    private int HubTowerBlock(in Tile t, int gx, int gz, int rel)
    {
        int dx = gx - layout.HubOriginX, dz = gz - layout.HubOriginZ;
        double r = Math.Sqrt((double)dx * dx + (double)dz * dz), angle = Math.Atan2(dz, dx), theta0 = layout.HubTheta0;
        if (rel < 0) return concreteId;
        if (t.Zone == WorldLayout.HubZoneVoid)
        {
            // The balcony, out through the meeting hall's wall, and the black void of the storm beyond it
            double tang = -dx * Math.Sin(theta0) + dz * Math.Cos(theta0);
            if (r < WorldLayout.HubTowerRadius + 0.5)
                return rel == WorldLayout.HubTowerHall ? hubMarbleId : rel > WorldLayout.HubTowerHall && rel <= WorldLayout.HubTowerHall + 3 ? 0 : rel == 0 ? concreteId : hubAshlarId;
            if (t.Under != Unders.HubTowerVoid)
            {
                if (rel < WorldLayout.HubTowerHall) return hubVoidId;
                if (rel == WorldLayout.HubTowerHall) return hubMarbleId;
                if (rel == WorldLayout.HubTowerHall + 1 && r >= 26) return hubBalustradeIds[Facing(Cardinal(-dx, -dz))];
                if (rel == WorldLayout.HubTowerHall + 1 && Math.Abs(tang) >= 3.2)
                    return hubBalustradeIds[Facing(Cardinal(-tang * -Math.Sin(theta0), -tang * Math.Cos(theta0)))];
                return rel >= WorldLayout.HubTowerCeiling ? hubVoidId : 0;
            }
            return rel <= 24 || rel >= WorldLayout.HubTowerCeiling ? hubVoidId : 0;
        }

        if (rel == 0) return dx == 0 && dz == 0 ? hubCentreId : t.Floor == FloorKind.HubMarbleInlay ? hubInlayId : hubMarbleId;
        if (rel >= WorldLayout.HubTowerCeiling) return rel == WorldLayout.HubTowerCeiling ? hubAshlarId : concreteId;
        // The headless statue, and over it, from nowhere, the dusk
        if (t.Variant == Props.HubStatue) return rel == 1 ? hubStatueId : rel <= 3 ? hubStatueFillId : rel == 6 ? hubDuskId : 0;

        // The spiral stair, three wide against the wall, on steps of ashlar
        int h = r >= 17.5 ? layout.HubStairHeight(angle) : -1;
        if (h > 0)
        {
            if (rel == h) return hubStairIds[Facing(Cardinal(-Math.Sin(angle), Math.Cos(angle)))];
            if (rel < h && rel >= h - 2) return hubAshlarId;
        }
        int inward = Facing(Cardinal(-dx, -dz));
        // The meeting hall's floor, open where the stair comes up through it
        if (rel == WorldLayout.HubTowerHall) return h >= WorldLayout.HubTowerHall - 3 ? 0 : hubMarbleId;
        // The galleries round the wall, each with a balustrade, and open where the stair passes
        foreach (int g in WorldLayout.HubTowerGalleries)
        {
            if (rel == g && r >= 16.5) return h >= g - 3 && h <= g ? 0 : hubMarbleId;
            if (rel == g + 1 && r >= 16.5 && r < 17.5)
            {
                int hs = layout.HubStairHeight(angle);
                return hs >= g - 3 && hs <= g + 3 ? 0 : hubBalustradeIds[inward];
            }
        }
        if (r >= 19.5)
        {
            bool clear = h < 0 || rel < h - 3 || rel > h + 3;
            // Pilasters between the passages, up to the first gallery
            if (clear && rel <= 7 && Math.Abs(OffTen(angle, theta0, r, out _)) < 0.75)
                return rel == 1 ? hubPilasterIds[0, 0, inward] : rel == 7 ? hubPilasterIds[2, 0, inward] : hubPilasterIds[1, 0, inward];
            // The dusk, from somewhere above each passage and each gallery's doors
            if (clear && rel is 6 or 12 or 18 or 24 or 33 && Math.Abs(OffTen(angle, theta0 + Math.PI / 10, r, out _)) < 0.75) return hubDuskId;
        }
        return 0;
    }

    /// <summary>The floors the Tower's forbidden doors stand on: each gallery's, then the meeting hall's.</summary>
    private static readonly int[] HubDoorStoreys =
    {
        WorldLayout.HubTowerGalleries[0], WorldLayout.HubTowerGalleries[1], WorldLayout.HubTowerGalleries[2], WorldLayout.HubTowerGalleries[3],
        WorldLayout.HubTowerHall,
    };

    /// <summary>The Tower's ashlar: on its inner face, at each gallery and in the meeting hall, ten ornate doors forbidden to wanderers.</summary>
    private int HubTowerWall(in Tile t, int gx, int gz, int rel)
    {
        if (rel <= 0) return concreteId;
        if (rel > WorldLayout.HubTowerCeiling) return concreteId;
        int dx = gx - layout.HubOriginX, dz = gz - layout.HubOriginZ;
        double r = Math.Sqrt((double)dx * dx + (double)dz * dz);
        if (r >= WorldLayout.HubTowerInner + 0.5 && r < WorldLayout.HubTowerInner + 1.5)
        {
            double angle = Math.Atan2(dz, dx);
            double off = OffTen(angle, layout.HubTheta0, r, out double door);
            // (Not in the meeting hall where the balcony goes out)
            bool balcony = Math.Abs(Math.IEEERemainder(door - layout.HubTheta0, 2 * Math.PI)) < 0.01;
            if (Math.Abs(off) <= 1.2)
                foreach (int g in HubDoorStoreys)
                {
                    if (rel <= g || rel > g + 3 || g == WorldLayout.HubTowerHall && balcony) continue;
                    ArchPier facing = Cardinal(-Math.Cos(door), -Math.Sin(door));
                    var (rx, rz) = HubRightOf(facing);
                    bool right = off * (-Math.Sin(door) * rx + Math.Cos(door) * rz) > 0;
                    return hubForbiddenIds[right ? 1 : 0, rel - g - 1, Facing(facing)];
                }
        }
        // (The literal seed is meant: the Tower's worn stones are the same in every world, like the Tower itself)
        return Hashing.Unit(Hashing.Hash(17, gx, gz, (ulong)rel)) < 0.12 ? hubAshlarWornId : hubAshlarId;
    }

    /// <summary>A tunnel wall: concrete slabs two wide and three high with seams between, and whatever hangs on it.</summary>
    private int HubWallBlock(in Tile t, int gx, int gz, int rel)
    {
        // (Up to the vaults' crown in layout version 9, where a tunnel's end wall shows that high)
        if (rel <= 0 || rel > (layout.Version >= 9 ? WorldLayout.HubVaultTop : WorldLayout.HubMainHeight + 1)) return concreteId;
        if (t.Kind == TileKind.Wall && t.Stack is 1 or 2) return hubCrumbIds[t.Stack];
        bool left = Hashing.Mod(gx + gz, 2) == 0, bottom = Hashing.Mod(rel - 1, 3) == 0;
        return hubWallIds[(left ? 1 : 0) + (bottom ? 2 : 0)];
    }

    [ThreadStatic] private static WorldLayout vaultLayout;
    [ThreadStatic] private static int vaultX, vaultZ;
    [ThreadStatic] private static bool vaultHit;
    [ThreadStatic] private static byte[] vaultCells;
    [ThreadStatic] private static ArchPier[] vaultDirs;

    /// <summary>
    /// (Layout version 9) the vault over a tunnel column (<see cref="WorldLayout.HubVault"/>), kept for the column the
    /// thread asked about last, since its blocks are asked for one height at a time.
    /// </summary>
    private bool HubVaultAt(int gx, int gz, out byte[] cells, out ArchPier[] dirs)
    {
        if (vaultCells == null)
        {
            vaultCells = new byte[WorldLayout.HubVaultTop - WorldLayout.HubVaultFrom + 1];
            vaultDirs = new ArchPier[vaultCells.Length];
        }
        if (vaultLayout != layout || vaultX != gx || vaultZ != gz)
        {
            vaultHit = layout.HubVault(gx, gz, vaultCells, vaultDirs);
            vaultLayout = layout;
            vaultX = gx;
            vaultZ = gz;
        }
        cells = vaultCells;
        dirs = vaultDirs;
        return vaultHit;
    }

    /// <summary>
    /// (Layout version 9) the sidewalk's edge: a kerb with a rounded lip toward the road where the sidewalk runs along one
    /// wall (or door) with the road in front of it; the plain slab at corners and at the ends where a junction opens.
    /// </summary>
    private int HubKerb(int gx, int gz)
    {
        int walls = 0, wall = -1;
        for (int i = 0; i < 4; i++)
        {
            var (dx, dz) = Neighbours4[i];
            if (!HubOpen(layout.TileAt(gx + dx, gz + dz))) { walls++; wall = i; }
        }
        if (walls != 1) return hubSidewalkId;
        // The road straight out from the wall (Neighbours4: east, west, south, north)
        var (wx, wz) = Neighbours4[wall];
        Tile road = layout.TileAt(gx - wx, gz - wz);
        if (!HubOpen(road) || road.Floor is FloorKind.HubSidewalk or FloorKind.PoolTile) return hubSidewalkId;
        ArchPier side = wx > 0 ? ArchPier.West : wx < 0 ? ArchPier.East : wz > 0 ? ArchPier.North : ArchPier.South;
        return hubCurbIds[Facing(side)];
    }

    private static readonly string[] HubLineKinds = { "ns", "we", "ne", "es", "sw", "wn", "givewayns", "givewaywe" };

    /// <summary>
    /// (Layout version 11) the piece of the yellow middle line on a tile (an index into <see cref="HubLineKinds"/>):
    /// joined to the line tiles beside it, straight through or round a corner; where it stops or meets more than two,
    /// straight along its own way (<see cref="Tile.Pier"/>).
    /// </summary>
    private int HubLinePiece(in Tile t, int gx, int gz)
    {
        bool Line(int dx, int dz) => layout.TileAt(gx + dx, gz + dz).Floor == FloorKind.HubLine;
        bool n = Line(0, -1), e = Line(1, 0), s = Line(0, 1), w = Line(-1, 0);
        int count = (n ? 1 : 0) + (e ? 1 : 0) + (s ? 1 : 0) + (w ? 1 : 0);
        if (count == 2)
        {
            if (n && s) return 0;
            if (e && w) return 1;
            return n && e ? 2 : e && s ? 3 : s && w ? 4 : 5;
        }
        if (count == 1) return n || s ? 0 : 1;
        return t.Pier == ArchPier.East ? 1 : 0;
    }

    private static readonly (int X, int Z)[] KerbDirs = { (0, -1), (1, 0), (0, 1), (-1, 0) };
    private static readonly ArchPier[] KerbNames = { ArchPier.North, ArchPier.East, ArchPier.South, ArchPier.West };
    private const int KerbNone = 0, KerbStraight = 1, KerbCorner = 2, KerbInner = 3;

    /// <summary>
    /// (Layout version 11) the sidewalk's piece and its turn, from what is round it, so the kerb runs on unbroken round
    /// every corner: a straight kerb (hub-curb) where the road is on one side; a rounded corner (hub-curbcorner, turned
    /// by its first kerbed side going clockwise: north for north and east) where it is on two sides that meet, round a
    /// wall's corner or where the sidewalk ends; in a wall's inside corner, the slab with a kerb post at the corner the
    /// road touches (hub-curbinner, turned by that corner: north for north-east); else the plain slab. "Road" is any
    /// floor that is not sidewalk (asphalt, the Tower's marble, a white-tile end).
    /// </summary>
    private (int Kind, ArchPier Facing) HubKerbV11(int gx, int gz)
    {
        // Clockwise from north: north, east, south, west
        bool Road(int dx, int dz)
        {
            Tile n = layout.TileAt(gx + dx, gz + dz);
            return HubOpen(n) && n.Floor != FloorKind.HubSidewalk;
        }
        bool Walk(int dx, int dz)
        {
            Tile n = layout.TileAt(gx + dx, gz + dz);
            return HubOpen(n) && n.Floor == FloorKind.HubSidewalk;
        }
        var dirs = KerbDirs;
        var names = KerbNames;
        int mask = 0, count = 0;
        for (int i = 0; i < 4; i++)
            if (Road(dirs[i].X, dirs[i].Z)) { mask |= 1 << i; count++; }
        if (count == 1)
            for (int i = 0; i < 4; i++)
                if ((mask & (1 << i)) != 0) return (KerbStraight, names[i]);
        if (count == 2)
            for (int i = 0; i < 4; i++)
                if ((mask & (1 << i)) != 0 && (mask & (1 << ((i + 1) % 4))) != 0) return (KerbCorner, names[i]);
        if (count == 0)
        {
            // A corner the road touches, between two sides of sidewalk
            int found = -1;
            for (int i = 0; i < 4; i++)
            {
                var (ax, az) = dirs[i];
                var (bx, bz) = dirs[(i + 1) % 4];
                if (Walk(ax, az) && Walk(bx, bz) && Road(ax + bx, az + bz))
                {
                    if (found >= 0) return (KerbNone, ArchPier.North);
                    found = i;
                }
            }
            if (found >= 0) return (KerbInner, names[found]);
        }
        return (KerbNone, ArchPier.North);
    }

    private static bool HubOpen(in Tile n) => n.Kind is TileKind.Floor or TileKind.Pit && n.Under != Unders.HubFalseWall;

    /// <summary>
    /// (Layout version 9) a road block beside the sidewalk where it runs along a straight wall (a kerb there): asphalt with
    /// the white edge line on that side, or -1.
    /// </summary>
    private int HubEdgeLine(int gx, int gz)
    {
        int found = -1;
        for (int i = 0; i < 4; i++)
        {
            var (dx, dz) = Neighbours4[i];
            Tile n = layout.TileAt(gx + dx, gz + dz);
            if (!HubOpen(n) || n.Floor != FloorKind.HubSidewalk) continue;
            // The sidewalk's wall straight behind it
            if (HubOpen(layout.TileAt(gx + 2 * dx, gz + 2 * dz))) continue;
            if (found >= 0) return -1; // a corner: no line
            found = i;
        }
        if (found < 0) return -1;
        var (sx, sz) = Neighbours4[found];
        return hubEdgeLineIds[Facing(sx > 0 ? ArchPier.East : sx < 0 ? ArchPier.West : sz > 0 ? ArchPier.South : ArchPier.North)];
    }

    /// <summary>
    /// Level 37: the far end of a dry corridor where the white tile gives way to the Hub's concrete and asphalt (see
    /// <see cref="WorldLayout.PoolCorridorEndKind"/>). <paramref name="rel"/> is from the Poolrooms' water level.
    /// </summary>
    private int HubInPool(in Tile t, int rel)
    {
        if (t.Kind != TileKind.Floor) return rel is >= 1 and <= 4 ? HubWallBlock(t, 0, 0, rel) : concreteId;
        if (rel == 0) return hubAsphaltId;
        if (rel > 0 && rel < Math.Max(3, (int)t.Height)) return 0;
        return rel > 0 ? hubCeilingId : concreteId;
    }
}
