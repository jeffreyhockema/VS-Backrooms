using System.Collections.Concurrent;
using System.Collections.Generic;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace Backrooms.Worldgen;

/// <summary>
/// Writes the Backrooms into freshly generated chunk columns. All levels share one floor height. Vertically:
/// mantle, concrete, the floor, the walkable space of the level (3 blocks on Levels 0 and 2, 4 on Level 1), its
/// ceiling, then concrete (with a dusty crawlspace above the Level 0 tiles) up to a mantle cap.
/// </summary>
public sealed class WorldGenerator
{
    private static readonly string[] PatternCodes = { "chevron", "dotted", "cream", "manila" };
    private static readonly string[] PierCodes = { "west", "east", "north", "south" };
    private static readonly string[] Sides = { "north", "east", "south", "west" };
    private static readonly string[] Letters = { "a", "b", "c", "d", "e", "f" };

    private const int PartUpper = 0, PartPlain = 1, PartBaseboard = 2, PartRail = 3, PartOutlet = 4;
    private static readonly string[] PartCodes = { "upper", "plain", "baseboard", "rail", "outlet" };

    private readonly ICoreServerAPI api;
    private readonly int chunkSize;
    private readonly WorldLayout layout;
    private readonly WorldLighting lighting;
    public readonly WorldGeometry Geometry;

    // Shared
    private readonly int mantleId, concreteId, waterId, boxId;
    private readonly int[] floorIds = new int[17];
    private readonly HashSet<int> flickerIds = new();

    // Level 0
    private readonly int ceilingTileId, lightOnId, lightLitId, lightOffId, lampDimId, lightFlickerId;
    private readonly int[,] wallIds = new int[4, 5];
    private readonly int[] archIds = new int[4];

    // Level 1
    private readonly int concreteWallId, concreteWallDamagedId, pillarId, pillarLightId, concreteCeilingId, exitSignId, crateId;
    private readonly int[] pillarLetterIds = new int[6];
    private readonly int[,] hangingLightIds = new int[3, 2]; // state (on, off, flicker) x axis (we, ns)
    private readonly int bulbOnId, conduitXId, conduitZId;
    private readonly int[] shelfIds = new int[4];
    private readonly int[] stairIds = new int[4];
    private readonly int wheelStopId, carColliderId;
    private readonly int[,] carIds = new int[4, 2]; // colour x facing (north, south)

    // Level 2
    private readonly int tunnelFloorId, tunnelCeilingId, drumId;
    private readonly int pipeRunXId, pipeRunZId, pipeHubId, pipeLeakXId, pipeLeakZId;
    private readonly int[,] tunnelLightIds = new int[4, 4]; // state (white, warm, off, flicker) x pipes alongside (we, ns, hub, none)
    private readonly int[] cabinetIds = new int[4];
    private readonly Dictionary<string, int> tunnelWallIds = new();

    // Level 3
    private readonly int dustyFloorId, plasterCeilingId, transformerId, windowGlowId, manholeId, rungsId;
    private readonly Dictionary<WallPattern, int> l3WallIds = new();
    private readonly Dictionary<(WallPattern, byte), int> l3FixtureIds = new();
    private readonly int cableXId, cableZId, cableHubId;
    private readonly int[,] cableLightIds = new int[3, 2]; // state (warm, off, flicker) x axis (we, ns)
    private readonly int[] roomSignIds = new int[8];
    private readonly int barsWeId, barsNsId;

    // Level 4
    private readonly int officeWallId, officeWindowId, officeGlassId, officeCeilingId, confTableId, elevatorLowerId, elevatorUpperId;
    private readonly int[] officeLightIds = new int[4]; // on, lit, off, flicker
    private readonly int partitionWeId, partitionNsId;
    private readonly int[] deskIds = new int[4], chairIds = new int[4], filingIds = new int[4], vendingIds = new int[4], coolerIds = new int[4];

    // Level 5
    private readonly int wainscotId, panelId, friezeId, marbleId, plasterId, beamCeilingId, creamCeilingId, chandelierId;
    private readonly int sconceId, portraitId, beverlyId, staffSignId, doorLowerId, cageLowerId, cageUpperId, palmId, mahjongId, turntableId;
    private readonly int bulbOffId;
    private readonly int[] doorUpperIds = new int[8];
    private readonly int[] domeIds = new int[3]; // on, off, flicker
    private readonly int[] bedHeadIds = new int[4], bedFootIds = new int[4], nightstandIds = new int[4], wardrobeIds = new int[4];
    private readonly int[] wingChairIds = new int[4], sofaIds = new int[4], boilerIds = new int[4], furnaceIds = new int[4];

    /// <summary>Block entities to spawn for blocks placed by the terrain pass (flickering lights, dispensers).</summary>
    private readonly ConcurrentDictionary<long, List<(BlockPos Pos, string EntityClass)>> pendingEntities = new();

    public WorldGenerator(ICoreServerAPI api, WorldLayout layout)
    {
        this.api = api;
        this.layout = layout;
        chunkSize = api.WorldManager.ChunkSize;
        Geometry = new WorldGeometry(api.WorldManager.MapSizeY);

        mantleId = BlockId("game:mantle");
        concreteId = BlockId("backrooms:concrete");
        waterId = BlockId("game:water-still-7");
        boxId = BlockId("backrooms:supplybox");

        floorIds[(int)FloorKind.Carpet] = BlockId("backrooms:carpet-normal");
        floorIds[(int)FloorKind.Stained] = BlockId("backrooms:carpet-stained");
        floorIds[(int)FloorKind.Soaked] = BlockId("backrooms:carpet-soaked");
        floorIds[(int)FloorKind.Wood] = BlockId("game:planks-aged-ud");
        floorIds[(int)FloorKind.Concrete] = BlockId("backrooms:concretefloor-plain");
        floorIds[(int)FloorKind.ConcreteWet] = BlockId("backrooms:concretefloor-wet");
        floorIds[(int)FloorKind.ConcreteLineNS] = BlockId("backrooms:concretefloor-linens");
        floorIds[(int)FloorKind.ConcreteLineWE] = BlockId("backrooms:concretefloor-linewe");
        floorIds[(int)FloorKind.ConcreteDashWE] = BlockId("backrooms:concretefloor-dashwe");
        floorIds[(int)FloorKind.ConcreteDashNS] = BlockId("backrooms:concretefloor-dashns");
        floorIds[(int)FloorKind.Dusty] = BlockId("backrooms:dustyfloor");
        floorIds[(int)FloorKind.OfficeCarpet] = BlockId("backrooms:officecarpet-plain");
        floorIds[(int)FloorKind.OfficeCarpetGhost] = BlockId("backrooms:officecarpet-ghost");
        floorIds[(int)FloorKind.HotelCarpet] = BlockId("backrooms:hotelcarpet-damask");
        floorIds[(int)FloorKind.HotelMaroon] = BlockId("backrooms:hotelcarpet-maroon");
        floorIds[(int)FloorKind.HotelLobby] = BlockId("backrooms:hotelcarpet-lobby");
        floorIds[(int)FloorKind.HotelWood] = BlockId("backrooms:hotelwood");

        ceilingTileId = BlockId("backrooms:ceilingtile");
        lightOnId = BlockId("backrooms:fluorescentlight-on");
        lightLitId = BlockId("backrooms:fluorescentlight-lit");
        lightOffId = BlockId("backrooms:fluorescentlight-off");
        lampDimId = BlockId("backrooms:fluorescentlight-dim");
        lightFlickerId = BlockId("backrooms:fluorescentlight-flicker");
        for (int p = 0; p < PatternCodes.Length; p++)
            for (int part = 0; part < PartCodes.Length; part++)
                wallIds[p, part] = BlockId($"backrooms:wallpaper-{PatternCodes[p]}-{PartCodes[part]}");
        for (int i = 0; i < PierCodes.Length; i++) archIds[i] = BlockId($"backrooms:archheader-{PierCodes[i]}");

        concreteWallId = BlockId("backrooms:concretewall-plain");
        concreteWallDamagedId = BlockId("backrooms:concretewall-damaged");
        pillarId = BlockId("backrooms:concretepillar-plain");
        for (int i = 0; i < Letters.Length; i++) pillarLetterIds[i] = BlockId($"backrooms:concretepillar-{Letters[i]}");
        pillarLightId = BlockId("backrooms:pillarlight");
        concreteCeilingId = BlockId("backrooms:concreteceiling");
        exitSignId = BlockId("backrooms:exitsign");
        crateId = BlockId("backrooms:crate");
        string[] lightStates = { "on", "off", "flicker" }, axes = { "we", "ns" };
        for (int st = 0; st < 3; st++)
            for (int a = 0; a < 2; a++)
                hangingLightIds[st, a] = BlockId($"backrooms:hanginglight-{lightStates[st]}-{axes[a]}");
        bulbOnId = BlockId("backrooms:hangingbulb-on");
        conduitXId = BlockId("backrooms:conduit-we");
        conduitZId = BlockId("backrooms:conduit-ns");
        wheelStopId = BlockId("backrooms:wheelstop");
        carColliderId = BlockId("backrooms:carcollider");
        string[] colours = { "red", "blue", "white", "black" };
        for (int c = 0; c < 4; c++)
        {
            carIds[c, 0] = BlockId($"backrooms:car-{colours[c]}-north");
            carIds[c, 1] = BlockId($"backrooms:car-{colours[c]}-south");
        }
        for (int i = 0; i < Sides.Length; i++)
        {
            shelfIds[i] = BlockId($"backrooms:metalshelf-{Sides[i]}");
            stairIds[i] = BlockId($"backrooms:concretestairs-{Sides[i]}");
            cabinetIds[i] = BlockId($"backrooms:machinecabinet-{Sides[i]}");
        }

        tunnelFloorId = BlockId("backrooms:concretefloor-dark");
        tunnelCeilingId = BlockId("backrooms:tunnelceiling");
        foreach (string type in new[] { "plain", "machinery", "brick", "warning", "pipes", "riser", "riserjoint", "valve" })
            tunnelWallIds[type] = BlockId($"backrooms:tunnelwall-{type}");
        drumId = BlockId("backrooms:oildrum");
        pipeRunXId = BlockId("backrooms:pipes-run-we");
        pipeRunZId = BlockId("backrooms:pipes-run-ns");
        pipeHubId = BlockId("backrooms:pipes-hub");
        pipeLeakXId = BlockId("backrooms:pipes-leak-we");
        pipeLeakZId = BlockId("backrooms:pipes-leak-ns");
        string[] tunnelStates = { "white", "warm", "off", "flicker" }, tunnelAxes = { "we", "ns", "hub", "none" };
        for (int st = 0; st < 4; st++)
            for (int a = 0; a < 4; a++)
                tunnelLightIds[st, a] = BlockId($"backrooms:tunnellight-{tunnelStates[st]}-{tunnelAxes[a]}");

        // Level 3
        dustyFloorId = BlockId("backrooms:dustyfloor");
        plasterCeilingId = BlockId("backrooms:plasterceiling");
        transformerId = BlockId("backrooms:transformer");
        windowGlowId = BlockId("backrooms:windowglow");
        manholeId = BlockId("backrooms:manhole");
        rungsId = BlockId("backrooms:rungs");
        foreach ((WallPattern pattern, string code) in new[] { (WallPattern.GlazedTile, "glazed"), (WallPattern.RedBrick, "brick"), (WallPattern.Cinder, "cinder") })
        {
            l3WallIds[pattern] = BlockId($"backrooms:l3wall-{code}");
            l3FixtureIds[(pattern, Props.WallPipes)] = BlockId($"backrooms:l3wallfixture-{code}-pipes");
            l3FixtureIds[(pattern, Props.WallPanel)] = BlockId($"backrooms:l3wallfixture-{code}-panel");
            l3FixtureIds[(pattern, Props.WallFan)] = BlockId($"backrooms:l3wallfixture-{code}-fan");
        }
        cableXId = BlockId("backrooms:cables-run-we");
        cableZId = BlockId("backrooms:cables-run-ns");
        cableHubId = BlockId("backrooms:cables-hub");
        string[] cableStates = { "warm", "off", "flicker" };
        for (int st = 0; st < 3; st++)
            for (int a = 0; a < 2; a++)
                cableLightIds[st, a] = BlockId($"backrooms:cablelight-{cableStates[st]}-{axes[a]}");
        for (int i = 0; i < 8; i++) roomSignIds[i] = BlockId($"backrooms:roomsign-{i}");
        barsWeId = BlockId("backrooms:ironbars-we");
        barsNsId = BlockId("backrooms:ironbars-ns");

        // Level 4
        officeWallId = BlockId("backrooms:officewall");
        officeWindowId = BlockId("backrooms:officewindow");
        officeGlassId = BlockId("backrooms:officeglass");
        officeCeilingId = BlockId("backrooms:officeceiling");
        confTableId = BlockId("backrooms:conferencetable");
        elevatorLowerId = BlockId("backrooms:elevatordoor-lower");
        elevatorUpperId = BlockId("backrooms:elevatordoor-upper");
        string[] officeLightStates = { "on", "lit", "off", "flicker" };
        for (int st = 0; st < 4; st++) officeLightIds[st] = BlockId($"backrooms:officelight-{officeLightStates[st]}");
        partitionWeId = BlockId("backrooms:partition-we");
        partitionNsId = BlockId("backrooms:partition-ns");

        // Level 5
        wainscotId = BlockId("backrooms:hotelwall-wainscot");
        panelId = BlockId("backrooms:hotelwall-panel");
        friezeId = BlockId("backrooms:hotelwall-frieze");
        marbleId = BlockId("backrooms:marblecolumn");
        plasterId = BlockId("backrooms:plasterwall");
        beamCeilingId = BlockId("backrooms:hotelceiling-beams");
        creamCeilingId = BlockId("backrooms:hotelceiling-cream");
        chandelierId = BlockId("backrooms:chandelier");
        sconceId = BlockId("backrooms:hotelfixture-sconce");
        portraitId = BlockId("backrooms:hotelfixture-portrait");
        beverlyId = BlockId("backrooms:hotelfixture-beverly");
        staffSignId = BlockId("backrooms:staffsign");
        doorLowerId = BlockId("backrooms:hoteldoor-lower");
        for (int i = 0; i < 8; i++) doorUpperIds[i] = BlockId($"backrooms:hoteldoor-upper{i}");
        cageLowerId = BlockId("backrooms:cagedoor-lower");
        cageUpperId = BlockId("backrooms:cagedoor-upper");
        palmId = BlockId("backrooms:pottedpalm");
        mahjongId = BlockId("backrooms:mahjongtable");
        turntableId = BlockId("backrooms:turntable");
        bulbOffId = BlockId("backrooms:hangingbulb-off");
        string[] domeStates = { "on", "off", "flicker" };
        for (int st = 0; st < 3; st++) domeIds[st] = BlockId($"backrooms:domelight-{domeStates[st]}");

        for (int i = 0; i < Sides.Length; i++)
        {
            deskIds[i] = BlockId($"backrooms:desk-{Sides[i]}");
            chairIds[i] = BlockId($"backrooms:officechair-{Sides[i]}");
            filingIds[i] = BlockId($"backrooms:filingcabinet-{Sides[i]}");
            vendingIds[i] = BlockId($"backrooms:vendingmachine-{Sides[i]}");
            coolerIds[i] = BlockId($"backrooms:watercooler-{Sides[i]}");
            bedHeadIds[i] = BlockId($"backrooms:bed-head-{Sides[i]}");
            bedFootIds[i] = BlockId($"backrooms:bed-foot-{Sides[i]}");
            nightstandIds[i] = BlockId($"backrooms:nightstand-{Sides[i]}");
            wardrobeIds[i] = BlockId($"backrooms:wardrobe-{Sides[i]}");
            wingChairIds[i] = BlockId($"backrooms:wingchair-{Sides[i]}");
            sofaIds[i] = BlockId($"backrooms:sofa-{Sides[i]}");
            boilerIds[i] = BlockId($"backrooms:boiler-{Sides[i]}");
            furnaceIds[i] = BlockId($"backrooms:furnace-{Sides[i]}");
        }

        flickerIds.Add(lightFlickerId);
        flickerIds.Add(hangingLightIds[2, 0]);
        flickerIds.Add(hangingLightIds[2, 1]);
        for (int a = 0; a < 4; a++) flickerIds.Add(tunnelLightIds[3, a]);

        lighting = new WorldLighting(api, this, chunkSize);
    }

    public WorldLayout Layout => layout;

    public void Generate(IChunkColumnGenerateRequest request)
    {
        IServerChunk[] chunks = request.Chunks;
        foreach (IServerChunk chunk in chunks) chunk.Data.ClearBlocksAndPrepare();

        WorldGeometry g = Geometry;
        FillLayer(chunks, 0, mantleId);
        for (int y = 1; y < g.BandBottom; y++) FillLayer(chunks, y, concreteId);
        FillLayer(chunks, g.CapY, mantleId);

        Tile[] tiles = layout.BuildMacro(request.ChunkX, request.ChunkZ);
        IMapChunk mapChunk = chunks[0].MapChunk;
        var entities = new List<(BlockPos, string)>();

        for (int lz = 0; lz < chunkSize; lz++)
        {
            for (int lx = 0; lx < chunkSize; lx++)
            {
                Tile t = tiles[WorldLayout.TileIndex(lx, lz)];
                for (int y = g.BandBottom; y <= g.BandTop; y++)
                {
                    int block = ColumnBlock(t, y, out int fluid);
                    if (block != 0) SetBlock(chunks, lx, y, lz, block);
                    if (fluid != 0) SetFluid(chunks, lx, y, lz, fluid);
                    string entityClass = block != 0 ? api.World.Blocks[block].EntityClass : null;
                    if (entityClass != null) entities.Add((new BlockPos(request.ChunkX * chunkSize + lx, y, request.ChunkZ * chunkSize + lz), entityClass));
                }
                if (t.Kind == TileKind.Pit) LineShaft(chunks, tiles, lx, lz);

                int column = lz * chunkSize + lx;
                mapChunk.RainHeightMap[column] = (ushort)g.CapY;
                mapChunk.WorldGenTerrainHeightMap[column] = (ushort)g.FloorY;
            }
        }

        mapChunk.YMax = (ushort)g.CapY;
        lighting.Light(chunks, request.ChunkX, request.ChunkZ);
        if (entities.Count > 0) pendingEntities[ChunkKey(request.ChunkX, request.ChunkZ)] = entities;
    }

    /// <summary>Spawns the block entities for a column generated earlier (flickering lights, dispensers).</summary>
    public void SpawnBlockEntities(IChunkColumnGenerateRequest request, IBlockAccessor blockAccessor)
    {
        if (!pendingEntities.TryRemove(ChunkKey(request.ChunkX, request.ChunkZ), out var entities)) return;
        foreach ((BlockPos pos, string entityClass) in entities) blockAccessor.SpawnBlockEntity(entityClass, pos);
    }

    private static long ChunkKey(int chunkX, int chunkZ) => ((long)chunkX << 32) | (uint)chunkZ;

    /// <summary>
    /// The block (and fluid) at height <paramref name="y"/> of a column, within
    /// [<see cref="WorldGeometry.BandBottom"/>, <see cref="WorldGeometry.BandTop"/>]. Shaft lining, which
    /// depends on neighbouring columns, is left out; it absorbs light exactly like the concrete it replaces.
    /// </summary>
    public int ColumnBlock(in Tile t, int y, out int fluid)
    {
        fluid = 0;
        int rel = y - Geometry.FloorY;
        if (rel < 0) return BelowFloor(t, rel, out fluid);

        // Walls between levels (or around grand rooms) run solid up to the top of the tallest space next to them
        int room = t.Level == 1 || t.Grand ? WorldGeometry.MaxRoomHeight : WorldGeometry.RoomHeight;
        if (t.Tall && t.IsWallLike && rel > room && rel <= WorldGeometry.MaxRoomHeight + 1 && t.Level != 0) return concreteId;

        return t.Level switch
        {
            0 => Level0Block(t, rel, out fluid),
            1 => Level1Block(t, rel),
            2 => Level2Block(t, rel),
            3 => Level3Block(t, rel),
            4 => Level4Block(t, rel),
            _ => Level5Block(t, rel),
        };
    }

    private int BelowFloor(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        if (t.Under > 0 && rel >= -5)
        {
            // Level 3's flooded utility tunnel: 3 high, knee-deep freezing water, reached down a manhole shaft
            if (rel == -5) return concreteId;
            if (rel == -4) fluid = waterId;
            if (rel == -1) return t.Under == 2 ? rungsId : concreteId;
            return t.Under == 2 ? rungsId : 0;
        }
        if (t.Kind == TileKind.Pit)
        {
            if (rel > -WorldGeometry.ShaftDepth) return 0;
            if (rel == -WorldGeometry.ShaftDepth) return floorIds[(int)FloorKind.Carpet];
        }
        if (t.Kind == TileKind.Water && rel == -1) return floorIds[(int)FloorKind.Soaked];
        return concreteId;
    }

    // ---- Level 0: wallpaper, carpet, drop ceiling ----

    private int Level0Block(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        const int room = WorldGeometry.RoomHeight;
        if (t.Tall && t.IsWallLike && rel > room) return concreteId; // seals the crawlspace off from taller levels
        if (rel > room + 1 + WorldGeometry.CrawlspaceHeight) return concreteId;
        if (rel > room + 1) return 0; // crawlspace
        if (rel == room + 1) return t.Worn ? 0 : CeilingBlock0(t.Ceiling);

        if (rel == 0)
        {
            if (t.Kind == TileKind.Pit) return 0;
            if (t.Kind == TileKind.Water)
            {
                // Recessed one block and flooded
                fluid = waterId;
                return 0;
            }
            return floorIds[(int)t.Floor];
        }

        bool bottom = rel == 1, top = rel == room;
        int pattern = (int)t.Pattern;
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (t.Pattern > WallPattern.Manila) return concreteId;
                return wallIds[pattern, bottom ? (t.Outlet ? PartOutlet : BasePart(t.Base)) : PartUpper];
            case TileKind.Doorway:
                return top ? (t.Pattern > WallPattern.Manila ? concreteId : wallIds[pattern, PartUpper]) : 0;
            case TileKind.ArchWindow:
                return bottom ? wallIds[pattern, BasePart(t.Base)] : top ? archIds[(int)t.Pier] : 0;
            case TileKind.ArchDoor:
                return top ? archIds[(int)t.Pier] : 0;
            default:
                return bottom && t.SupplyBox ? boxId : 0;
        }
    }

    private int CeilingBlock0(CeilingKind ceiling) => ceiling switch
    {
        CeilingKind.LightOn => lightOnId,
        CeilingKind.LightLit => lightLitId,
        CeilingKind.LightOff => lightOffId,
        CeilingKind.LampDim => lampDimId,
        CeilingKind.LightFlicker => lightFlickerId,
        _ => ceilingTileId,
    };

    // ---- Level 1: concrete car park ----

    private int Level1Block(in Tile t, int rel)
    {
        const int room = WorldGeometry.Level1RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return floorIds[(int)t.Floor];
        if (rel == room + 1) return t.IsWallLike ? concreteId : concreteCeilingId;

        switch (t.Kind)
        {
            case TileKind.Wall:
                if (t.Pattern == WallPattern.Pillar)
                {
                    if (rel == 2) return pillarLetterIds[(t.Variant & 7) % pillarLetterIds.Length];
                    if (rel == 3 && (t.Variant & 8) != 0) return pillarLightId;
                    return pillarId;
                }
                if (t.Pattern <= WallPattern.Manila && rel <= WorldGeometry.RoomHeight) return wallIds[(int)t.Pattern, rel == 1 ? BasePart(t.Base) : PartUpper];
                return t.Variant == 1 ? concreteWallDamagedId : concreteWallId;
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                return rel == 3 && t.ExitSign ? exitSignId : concreteWallId;
        }

        // Stairs to nowhere: solid under the step, then the step itself
        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? concreteId : stairIds[Facing(t.Pier)];

        if (rel == room)
        {
            // Beams between the columns, hanging fixtures and overhead pipework just below the slab
            if (t.Beam) return concreteWallId;
            int axis = t.Pier is ArchPier.North or ArchPier.South ? 1 : 0;
            switch (t.Ceiling)
            {
                case CeilingKind.LightOn or CeilingKind.LightLit: return hangingLightIds[0, axis];
                case CeilingKind.LightOff: return hangingLightIds[1, axis];
                case CeilingKind.LightFlicker: return hangingLightIds[2, axis];
                case CeilingKind.LightWarm: return bulbOnId;
            }
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.ConduitX => conduitXId,
                Pipes.ConduitZ => conduitZId,
                _ => 0,
            };
        }

        if (t.Variant == Props.Shelf && rel <= 2) return shelfIds[Facing(Opposite(t.Pier))];
        if (t.Variant == Props.Car) return rel == 1 ? carIds[t.Stack % 4, t.Pier == ArchPier.North ? 0 : 1] : 0;
        if (t.Variant == Props.CarPart) return rel == 1 ? carColliderId : 0;
        if (t.Variant == Props.WheelStop && rel == 1) return wheelStopId;
        if (rel <= t.Stack) return crateId;
        if (rel == 1 && t.SupplyBox) return boxId;
        return 0;
    }

    // ---- Level 2: utility tunnels ----

    private int Level2Block(in Tile t, int rel)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return tunnelFloorId;
        if (rel == room + 1) return t.IsWallLike ? concreteId : tunnelCeilingId;

        switch (t.Kind)
        {
            case TileKind.Wall:
                return TunnelWall(t.Pattern == WallPattern.Tunnel ? t.Variant : Props.WallPlain, rel);
            case TileKind.Doorway:
                return rel <= 2 ? 0 : tunnelWallIds["plain"];
        }

        if (rel == room)
        {
            // The top block of a tunnel, above head height: fixtures and pipe bundles
            int axis = t.Pipe is Pipes.RunX or Pipes.LeakX ? 0 : t.Pipe is Pipes.RunZ or Pipes.LeakZ ? 1 : t.Pipe == Pipes.Hub ? 2 : 3;
            switch (t.Ceiling)
            {
                case CeilingKind.LightOn or CeilingKind.LightLit: return tunnelLightIds[0, axis];
                case CeilingKind.LightWarm: return tunnelLightIds[1, axis];
                case CeilingKind.LightOff: return tunnelLightIds[2, axis];
                case CeilingKind.LightFlicker: return tunnelLightIds[3, axis];
            }
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.Hub => pipeHubId,
                Pipes.LeakX => pipeLeakXId,
                Pipes.LeakZ => pipeLeakZId,
                _ => 0,
            };
        }

        if (rel == 1)
        {
            if (t.Variant == Props.Drum) return drumId;
            if (t.Variant == Props.Cabinet) return cabinetIds[Facing(Opposite(t.Pier))];
            if (t.SupplyBox) return boxId;
        }
        return 0;
    }

    /// <summary>Tunnel walls: plain at the top, with pipework, valves or machinery at body height.</summary>
    private int TunnelWall(byte variant, int rel) => variant switch
    {
        Props.WallPipes => tunnelWallIds[rel == 2 ? "pipes" : "plain"],
        Props.WallRiser => tunnelWallIds[rel == 2 ? "riserjoint" : "riser"],
        Props.WallValve => tunnelWallIds[rel == 1 ? "valve" : rel == 2 ? "pipes" : "plain"],
        Props.WallMachinery => tunnelWallIds[rel <= 2 ? "machinery" : "plain"],
        Props.WallBrick => tunnelWallIds["brick"],
        Props.WallWarning => tunnelWallIds[rel == 2 ? "warning" : "plain"],
        _ => tunnelWallIds["plain"],
    };

    /// <summary>Index into the north/east/south/west block variants for a direction.</summary>
    private static int Facing(ArchPier dir) => dir switch
    {
        ArchPier.North => 0,
        ArchPier.East => 1,
        ArchPier.South => 2,
        _ => 3,
    };

    private static ArchPier Opposite(ArchPier dir) => dir switch
    {
        ArchPier.North => ArchPier.South,
        ArchPier.South => ArchPier.North,
        ArchPier.East => ArchPier.West,
        _ => ArchPier.East,
    };

    // ---- Level 3: electrical station ----

    private int Level3Block(in Tile t, int rel)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return t.Under == 2 ? manholeId : dustyFloorId;
        if (rel == room + 1) return t.IsWallLike ? concreteId : plasterCeilingId;

        int wall = l3WallIds.TryGetValue(t.Pattern, out int id) ? id : l3WallIds[WallPattern.GlazedTile];
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (rel == 2 && l3FixtureIds.TryGetValue((l3WallIds.ContainsKey(t.Pattern) ? t.Pattern : WallPattern.GlazedTile, t.Variant), out int fixture)) return fixture;
                return wall;
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                return t.Variant == Props.WallSign ? roomSignIds[t.Stack % 8] : wall;
            case TileKind.Bars:
                return BarsBlock(t);
            case TileKind.Door:
                return rel == 1 ? elevatorLowerId : rel == 2 ? elevatorUpperId : wall;
        }

        if (t.Variant == Props.WindowGlow) return windowGlowId;
        if (rel == room)
        {
            int axis = t.Pipe is Pipes.RunX or Pipes.CableX ? 0 : 1;
            switch (t.Ceiling)
            {
                case CeilingKind.LightWarm or CeilingKind.LightOn: return cableLightIds[0, axis];
                case CeilingKind.LightOff: return cableLightIds[1, axis];
                case CeilingKind.LightFlicker: return cableLightIds[2, axis];
            }
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.Hub => pipeHubId,
                Pipes.CableX => cableXId,
                Pipes.CableZ => cableZId,
                Pipes.CableHub => cableHubId,
                _ => 0,
            };
        }
        if (rel == 1)
        {
            if (t.Variant == Props.Transformer) return transformerId;
            if (t.SupplyBox) return boxId;
        }
        if (rel <= t.Stack) return crateId;
        return 0;
    }

    private int BarsBlock(in Tile t) => t.Pier is ArchPier.North or ArchPier.South ? barsNsId : barsWeId;

    // ---- Level 4: abandoned office ----

    private int Level4Block(in Tile t, int rel)
    {
        const int room = WorldGeometry.RoomHeight;
        if (rel > room + 2) return concreteId;
        if (rel == room + 2) return t.IsWallLike ? concreteId : 0; // void above the drop ceiling
        if (rel == 0) return floorIds[(int)t.Floor];
        if (rel == room + 1)
        {
            if (t.IsWallLike) return concreteId;
            if (t.Worn) return 0;
            return t.Ceiling switch
            {
                CeilingKind.LightOn => officeLightIds[0],
                CeilingKind.LightLit => officeLightIds[1],
                CeilingKind.LightOff => officeLightIds[2],
                CeilingKind.LightFlicker => officeLightIds[3],
                _ => officeCeilingId,
            };
        }

        switch (t.Kind)
        {
            case TileKind.Wall:
                return t.Pattern switch
                {
                    WallPattern.OfficeWindow => rel == 1 ? officeWallId : officeWindowId,
                    WallPattern.OfficeGlass => officeGlassId,
                    WallPattern.Hotel => rel == 1 ? wainscotId : rel == 2 ? panelId : friezeId,
                    _ => officeWallId,
                };
            case TileKind.Door:
                return rel == 1 ? elevatorLowerId : rel == 2 ? elevatorUpperId : officeWallId;
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                return t.ExitSign ? exitSignId : t.Pattern == WallPattern.OfficeGlass ? officeGlassId : officeWallId;
        }

        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? officeWallId : stairIds[Facing(t.Pier)];
        if (rel != 1) return 0;
        int facing = Facing(t.Pier);
        return t.Variant switch
        {
            Props.Desk => deskIds[facing],
            Props.OfficeChair => chairIds[facing],
            Props.FilingCabinet => filingIds[facing],
            Props.Vending => vendingIds[facing],
            Props.Cooler => coolerIds[facing],
            Props.ConferenceTable => confTableId,
            Props.Partition => t.Pier is ArchPier.North or ArchPier.South ? partitionNsId : partitionWeId,
            _ => t.SupplyBox ? boxId : 0,
        };
    }

    // ---- Level 5: terror hotel ----

    private int Level5Block(in Tile t, int rel)
    {
        int room = t.Grand ? WorldGeometry.MaxRoomHeight : WorldGeometry.RoomHeight;
        bool boiler = t.Floor == FloorKind.Dusty;
        if (rel > room + 1) return concreteId;
        if (rel == 0) return boiler ? dustyFloorId : floorIds[(int)t.Floor];
        if (rel == room + 1)
        {
            if (t.IsWallLike) return concreteId;
            if (!t.Grand)
            {
                return t.Ceiling switch
                {
                    CeilingKind.LightOn or CeilingKind.LightLit => domeIds[0],
                    CeilingKind.LightOff => domeIds[1],
                    CeilingKind.LightFlicker => domeIds[2],
                    _ => creamCeilingId,
                };
            }
            return boiler ? plasterCeilingId : beamCeilingId;
        }

        switch (t.Kind)
        {
            case TileKind.Wall:
                if (t.Pattern == WallPattern.Marble) return marbleId;
                if (t.Pattern == WallPattern.Plaster) return plasterId;
                if (rel == 2)
                {
                    if (t.Variant == Props.WallSconce) return sconceId;
                    if (t.Variant == Props.WallPortrait) return portraitId;
                    if (t.Variant == Props.WallBeverly) return beverlyId;
                }
                return HotelWall(rel);
            case TileKind.Door:
                if (t.Pattern == WallPattern.Elevator) return rel == 1 ? cageLowerId : rel == 2 ? cageUpperId : HotelWall(rel);
                return rel == 1 ? doorLowerId : rel == 2 ? doorUpperIds[t.Variant % 8] : HotelWall(rel);
            case TileKind.Doorway:
                if (rel <= 2) return 0;
                if (rel == 3 && t.ExitSign) return staffSignId;
                return t.Pattern == WallPattern.Plaster ? plasterId : HotelWall(rel);
            case TileKind.Bars:
                return BarsBlock(t);
        }

        if (rel == room)
        {
            if (t.Ceiling == CeilingKind.Chandelier) return chandelierId;
            if (boiler && t.Ceiling == CeilingKind.LightWarm) return bulbOnId;
            if (boiler && t.Ceiling == CeilingKind.LightOff) return bulbOffId;
            return t.Pipe switch
            {
                Pipes.RunX => pipeRunXId,
                Pipes.RunZ => pipeRunZId,
                Pipes.LeakX => pipeLeakXId,
                Pipes.LeakZ => pipeLeakZId,
                _ => 0,
            };
        }
        if (rel != 1) return 0;
        int facing = Facing(t.Pier);
        return t.Variant switch
        {
            Props.Bed => t.Stack == 0 ? bedHeadIds[facing] : bedFootIds[facing],
            Props.Nightstand => nightstandIds[facing],
            Props.Wardrobe => wardrobeIds[facing],
            Props.WingChair => wingChairIds[facing],
            Props.Sofa => sofaIds[facing],
            Props.Palm => palmId,
            Props.MahjongTable => mahjongId,
            Props.Turntable => turntableId,
            Props.Boiler => boilerIds[facing],
            Props.Furnace => furnaceIds[facing],
            _ => t.SupplyBox ? boxId : 0,
        };
    }

    /// <summary>Hotel walls: mahogany wainscot, then a red panel in a gilt frame, then a cream frieze.</summary>
    private int HotelWall(int rel) => rel == 1 ? wainscotId : rel == 2 ? panelId : friezeId;

    /// <summary>Shafts are lined with the same carpet as the room, all the way down.</summary>
    private void LineShaft(IServerChunk[] chunks, Tile[] tiles, int lx, int lz)
    {
        int bottom = Geometry.FloorY - WorldGeometry.ShaftDepth;
        foreach ((int dx, int dz) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
        {
            int nx = lx + dx, nz = lz + dz;
            if (nx < 0 || nz < 0 || nx >= chunkSize || nz >= chunkSize) continue;
            if (tiles[WorldLayout.TileIndex(nx, nz)].Kind == TileKind.Pit) continue;
            for (int y = bottom + 1; y < Geometry.FloorY; y++) SetBlock(chunks, nx, y, nz, floorIds[(int)FloorKind.Carpet]);
        }
    }

    private static int BasePart(BaseStyle style) => style switch
    {
        BaseStyle.Baseboard => PartBaseboard,
        BaseStyle.Rail => PartRail,
        _ => PartPlain,
    };

    private void FillLayer(IServerChunk[] chunks, int y, int blockId)
    {
        chunks[y / chunkSize].Data.SetBlockBulk((y % chunkSize) * chunkSize * chunkSize, chunkSize, chunkSize, blockId);
    }

    private int Index3d(int lx, int y, int lz) => ((y % chunkSize) * chunkSize + lz) * chunkSize + lx;

    private void SetBlock(IServerChunk[] chunks, int lx, int y, int lz, int blockId)
    {
        chunks[y / chunkSize].Data.SetBlockUnsafe(Index3d(lx, y, lz), blockId);
    }

    private void SetFluid(IServerChunk[] chunks, int lx, int y, int lz, int blockId)
    {
        chunks[y / chunkSize].Data.SetFluid(Index3d(lx, y, lz), blockId);
    }

    private int BlockId(string code)
    {
        Block block = api.World.GetBlock(new AssetLocation(code));
        if (block == null || block.BlockId == 0)
        {
            api.Logger.Error("[backrooms] Missing block {0}, the Backrooms will have holes", code);
            return 0;
        }
        return block.BlockId;
    }
}
