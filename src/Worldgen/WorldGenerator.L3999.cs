using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 3999, "The Neon Paradise" (kept as level 19), laid out in WorldLayout.Level3999.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>, 20 below the others'), lit over a band from 4 below it, so its 18-high atria
/// are lit to the top. Blocks are the asset manifest's (docs/new-levels/3999-plan.md, section 6, made by tools/gen_3999.py),
/// with stand-ins until they exist.
///
/// A floor tile has its floor at rel 0 (a walkway's tread there instead), its ceiling at <see cref="Tile.Height"/> (the
/// open black ceiling, or the service corridors' acoustic tile and white tubes), and over a gallery the slab at rel 7
/// with its balustrade at rel 8. Neon: tubes just under a ceiling or a slab, up the walls and along their feet, pillars;
/// all of it dead where the Blackout has reached. Walls run to 18: glass shopfronts (glass to rel 5, then the fascia),
/// painted plaster, concrete, windows painted with a car park at night; round a lobby, a band of black marble at rel 6-7.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l3CeilingId, l3AcousticId, l3LanewoodId, l3MagentaId, l3GlitchId, l3Sign3999Id, l3ConcreteWallId, l3ConcreteFloorId,
        l3GlassId, l3GlassDarkId, l3StuccoId, l3BrickId, l3BandId, l3CoffeeTableId, l3PlanterId, l3TrashBinId, l3TableId, l3TicketPileId,
        l3DebrisId, l3DrainId, l3PoleId, l3BeaconRedId, l3MillWallId, l3MillCapId, l3PoolEdgeId;
    private readonly int[] l3CarpetIds = new int[3], l3MarbleIds = new int[2], l3PaintIds = new int[3], l3AsphaltIds = new int[3], l3PoolIds = new int[2],
        l3PillarIds = new int[6], l3DeadTubeIds = new int[2], l3PoolLedIds = new int[4], l3LampHeadIds = new int[4], l3RustedIds = new int[4],
        l3DeadCabinetIds = new int[4], l3PinballIds = new int[4], l3ClawIds = new int[4], l3PrizeCounterIds = new int[4], l3PrizeWallIds = new int[4],
        l3PrizeCaseIds = new int[4], l3LostFoundIds = new int[4], l3BenchIds = new int[4], l3BoothIds = new int[4], l3MenuIds = new int[4],
        l3DirectoryIds = new int[4], l3WalkwayIds = new int[4], l3WalkwayEndIds = new int[4], l3WalkwayRailIds = new int[4], l3EscalatorIds = new int[4],
        l3BalustradeIds = new int[4], l3KeypadIds = new int[4], l3LoungerIds = new int[4], l3SailsIds = new int[4], l3GeneratorIds = new int[4];
    /// <summary>The neon base strip in a unit's corner (colour, side wall on the left or right, facing).</summary>
    private readonly int[,,] l3RailCornerIds = new int[6, 2, 4];
    private readonly int[,] l3TubeIds = new int[6, 2], l3WallTubeIds = new int[6, 4], l3RailIds = new int[6, 4], l3SignIds = new int[8, 4], l3StallSignIds = new int[6, 4],
        l3CabinetIds = new int[6, 4], l3ThemedIds = new int[12, 4], l3RacerIds = new int[2, 4], l3DanceIds = new int[2, 4], l3SkeeIds = new int[2, 4],
        l3AirHockeyIds = new int[2, 4], l3PlushIds = new int[4, 4], l3ReceptionIds = new int[3, 4], l3CouchIds = new int[2, 4], l3ChairIds = new int[3, 4],
        l3StallIds = new int[6, 4], l3VendingIds = new int[2, 4], l3ShutterIds = new int[2, 4], l3RevolvingIds = new int[3, 4], l3StaffDoorIds = new int[2, 4],
        l3ElevatorIds = new int[2, 4];
    /// <summary>The neon signs drawn half a block off their block: [words, shift (left, right as seen from in front), facing].</summary>
    private readonly int[,,] l3SignShiftIds = new int[8, 2, 4];
    /// <summary>The painted car park in the windows: column, row, facing (the way the painting looks out).</summary>
    private readonly int[,,] l3WindowIds = new int[4, 3, 4];

    /// <summary>Level 3999's blocks that the asset script has not made yet (looked up once; logged once).</summary>
    private readonly List<string> l3999Missing = new();

    /// <summary>One of Level 3999's blocks by its path, or a stand-in until the asset exists.</summary>
    private int L3999Block(string path, int fallback)
    {
        if (modBlocks.TryGetValue(path, out int id)) return id;
        l3999Missing.Add(path);
        return fallback;
    }

    /// <summary>Looks up the level's blocks (called from the constructor).</summary>
    private void InitL3999()
    {
        string[] colours = WorldLayout.L3999Colours, foods = WorldLayout.L3999Foods, two = { "lower", "upper" };
        int carpet = floorIds[(int)FloorKind.Carpet], concrete = concreteId;
        string[] carpets = { "cosmic", "galaxy", "rotten" };
        for (int i = 0; i < 3; i++) l3CarpetIds[i] = L3999Block("l3999-carpet-" + carpets[i], carpet);
        l3MarbleIds[0] = L3999Block("l3999-marble-white", concrete);
        l3MarbleIds[1] = L3999Block("l3999-marble-black", concrete);
        l3ConcreteWallId = L3999Block("l3999-concrete-wall", concreteWallId);
        l3ConcreteFloorId = L3999Block("l3999-concrete-floor", floorIds[(int)FloorKind.Concrete]);
        string[] paints = { "violet", "midnight", "teal" };
        for (int i = 0; i < 3; i++) l3PaintIds[i] = L3999Block("l3999-wall-" + paints[i], concreteWallId);
        l3CeilingId = L3999Block("l3999-ceiling-black", concreteCeilingId);
        l3AcousticId = L3999Block("l3999-ceiling-acoustic", ceilingTileId);
        l3LanewoodId = L3999Block("l3999-lanewood", carpet);
        l3AsphaltIds[0] = L3999Block("l3999-asphalt-plain", concrete);
        l3AsphaltIds[1] = L3999Block("l3999-asphalt-line-ns", l3AsphaltIds[0]);
        l3AsphaltIds[2] = L3999Block("l3999-asphalt-line-we", l3AsphaltIds[0]);
        l3PoolIds[0] = L3999Block("l3999-pooltile-violet", concrete);
        l3PoolIds[1] = L3999Block("l3999-pooltile-lilac", concrete);
        l3PoolEdgeId = L3999Block("l3999-pooltile-edge", concrete);
        l3StuccoId = L3999Block("l3999-facade-stucco", concreteWallId);
        l3BrickId = L3999Block("l3999-facade-brick", concreteWallId);
        l3BandId = L3999Block("l3999-facade-band", concreteWallId);
        l3GlassId = L3999Block("l3999-glass-clear", BlockId("game:glass-plain"));
        l3GlassDarkId = L3999Block("l3999-glass-dark", l3GlassId);
        l3MagentaId = L3999Block("l3999-magentatile", concrete);
        l3GlitchId = L3999Block("l3999-glitchwall", 0);
        l3Sign3999Id = L3999Block("l3999-sign3999", 0);
        l3CoffeeTableId = L3999Block("l3999-coffeetable", 0);
        l3PlanterId = L3999Block("l3999-planter", 0);
        l3TrashBinId = L3999Block("l3999-trashbin", 0);
        l3TableId = L3999Block("l3999-table", 0);
        l3TicketPileId = L3999Block("l3999-ticketpile", 0);
        l3DebrisId = L3999Block("l3999-ceilingdebris", 0);
        l3DrainId = L3999Block("l3999-drain", l3PoolIds[0]);
        l3PoleId = L3999Block("l3999-lamppost-pole", 0);
        l3BeaconRedId = L3999Block("l3999-beacon-red", 0);
        l3MillWallId = L3999Block("l3999-windmill-wall", concreteWallId);
        l3MillCapId = L3999Block("l3999-windmill-cap", l3MillWallId);
        l3DeadTubeIds[0] = L3999Block("l3999-neondead-ns", 0);
        l3DeadTubeIds[1] = L3999Block("l3999-neondead-we", 0);
        for (int c = 0; c < 6; c++)
        {
            l3PillarIds[c] = L3999Block($"l3999-pillar-{colours[c]}", 0);
            l3TubeIds[c, 0] = L3999Block($"l3999-neonceiling-{colours[c]}-ns", 0);
            l3TubeIds[c, 1] = L3999Block($"l3999-neonceiling-{colours[c]}-we", 0);
        }
        string[] themes = WorldLayout.L3999Themes, signs = WorldLayout.L3999Signs, games = { "a", "b", "c", "d", "e", "f" }, flow = { "n", "e", "s", "w" };
        string[] plush = { "bear", "cat", "alien", "smiley" }, desk = { "left", "mid", "right" }, chairs = { "white", "pink", "cyan" }, door = { "side", "center", "top" };
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            for (int c = 0; c < 6; c++)
            {
                l3WallTubeIds[c, f] = L3999Block($"l3999-neonwall-{colours[c]}-{side}", 0);
                l3RailIds[c, f] = L3999Block($"l3999-neonrail-{colours[c]}-{side}", 0);
                l3RailCornerIds[c, 0, f] = L3999Block($"l3999-neonrailcorner-{colours[c]}-l-{side}", l3RailIds[c, f]);
                l3RailCornerIds[c, 1, f] = L3999Block($"l3999-neonrailcorner-{colours[c]}-r-{side}", l3RailIds[c, f]);
                l3CabinetIds[c, f] = L3999Block($"l3999-cabinet-{games[c]}-{side}", 0);
                l3StallSignIds[c, f] = L3999Block($"l3999-stallsign-{foods[c]}-{side}", 0);
                l3StallIds[c, f] = L3999Block($"l3999-stallcounter-{foods[c]}-{side}", 0);
            }
            for (int s = 1; s < signs.Length; s++)
            {
                l3SignIds[s, f] = L3999Block($"l3999-neonsign-{signs[s]}-{side}", 0);
                l3SignShiftIds[s, 0, f] = L3999Block($"l3999-neonsignshift-{signs[s]}-left-{side}", l3SignIds[s, f]);
                l3SignShiftIds[s, 1, f] = L3999Block($"l3999-neonsignshift-{signs[s]}-right-{side}", l3SignIds[s, f]);
            }
            for (int k = 0; k < themes.Length; k++) l3ThemedIds[k, f] = L3999Block($"l3999-themed-{themes[k]}-{side}", l3CabinetIds[k % 6, f]);
            l3RustedIds[f] = L3999Block($"l3999-cabinet-rusted-{side}", 0);
            l3DeadCabinetIds[f] = L3999Block($"l3999-cabinet-dead-{side}", 0);
            l3RacerIds[0, f] = L3999Block($"l3999-racer-seat-{side}", 0);
            l3RacerIds[1, f] = L3999Block($"l3999-racer-screen-{side}", 0);
            l3DanceIds[0, f] = L3999Block($"l3999-dance-pad-{side}", 0);
            l3DanceIds[1, f] = L3999Block($"l3999-dance-screen-{side}", 0);
            l3SkeeIds[0, f] = L3999Block($"l3999-skeeball-lane-{side}", 0);
            l3SkeeIds[1, f] = L3999Block($"l3999-skeeball-target-{side}", 0);
            l3AirHockeyIds[0, f] = L3999Block($"l3999-airhockey-a-{side}", 0);
            l3AirHockeyIds[1, f] = L3999Block($"l3999-airhockey-b-{side}", 0);
            l3PinballIds[f] = L3999Block($"l3999-pinball-{side}", 0);
            l3ClawIds[f] = L3999Block($"l3999-claw-{side}", 0);
            l3PrizeCounterIds[f] = L3999Block($"l3999-prizecounter-{side}", 0);
            l3PrizeWallIds[f] = L3999Block($"l3999-prizewall-{side}", 0);
            l3PrizeCaseIds[f] = L3999Block($"l3999-prizecase-{side}", 0);
            for (int k = 0; k < 4; k++) l3PlushIds[k, f] = L3999Block($"l3999-plush-{plush[k]}-{side}", 0);
            for (int k = 0; k < 3; k++) l3ReceptionIds[k, f] = L3999Block($"l3999-reception-{desk[k]}-{side}", 0);
            l3CouchIds[0, f] = L3999Block($"l3999-couch-left-{side}", 0);
            l3CouchIds[1, f] = L3999Block($"l3999-couch-right-{side}", 0);
            l3LostFoundIds[f] = L3999Block($"l3999-lostfound-{side}", 0);
            l3BenchIds[f] = L3999Block($"l3999-bench-{side}", 0);
            for (int k = 0; k < 3; k++) l3ChairIds[k, f] = L3999Block($"l3999-chair-{chairs[k]}-{side}", 0);
            l3BoothIds[f] = L3999Block($"l3999-booth-{side}", 0);
            l3MenuIds[f] = L3999Block($"l3999-menuboard-{side}", 0);
            l3VendingIds[0, f] = L3999Block($"l3999-vending-snack-{side}", 0);
            l3VendingIds[1, f] = L3999Block($"l3999-vending-drink-{side}", 0);
            l3DirectoryIds[f] = L3999Block($"l3999-directory-{side}", 0);
            l3WalkwayIds[f] = L3999Block($"l3999-walkway-{flow[f]}", l3MarbleIds[1]);
            l3WalkwayEndIds[f] = L3999Block($"l3999-walkwayend-{flow[f]}", l3MarbleIds[1]);
            l3WalkwayRailIds[f] = L3999Block($"l3999-walkwayrail-{side}", 0);
            l3EscalatorIds[f] = L3999Block($"l3999-escalator-{side}", l3ConcreteWallId);
            l3BalustradeIds[f] = L3999Block($"l3999-balustrade-{side}", 0);
            for (int k = 0; k < 2; k++)
            {
                l3ShutterIds[k, f] = L3999Block($"l3999-shutter-{two[k]}-{side}", concreteWallId);
                l3StaffDoorIds[k, f] = L3999Block($"l3999-staffdoor-{two[k]}-{side}", k == 0 ? metalDoorLowerId : metalDoorUpperId);
                l3ElevatorIds[k, f] = L3999Block($"l3999-elevator-{two[k]}-{side}", k == 0 ? elevatorLowerId : elevatorUpperId);
            }
            for (int k = 0; k < 3; k++) l3RevolvingIds[k, f] = L3999Block($"l3999-revolvingdoor-{door[k]}-{side}", k == 1 ? l3GlassId : 0);
            l3KeypadIds[f] = L3999Block($"l3999-keypad-{side}", 0);
            l3LoungerIds[f] = L3999Block($"l3999-lounger-{side}", 0);
            l3PoolLedIds[f] = L3999Block($"l3999-poolled-{side}", 0);
            l3LampHeadIds[f] = L3999Block($"l3999-lamppost-head-{side}", 0);
            l3SailsIds[f] = L3999Block($"l3999-windmillsails-{side}", 0);
            l3GeneratorIds[f] = L3999Block($"l3999-generator-off-{side}", 0);
            for (int col = 0; col < 4; col++)
                for (int row = 0; row < 3; row++)
                    l3WindowIds[col, row, f] = modBlocks.TryGetValue($"l3999-window-{col}-{row}-{side}", out int turned) ? turned
                        : L3999Block($"l3999-window-{col}-{row}", l3GlassDarkId);
        }

        floorIds[(int)FloorKind.L3999Floor] = l3CarpetIds[0];
        floorIds[(int)FloorKind.L3999Galaxy] = l3CarpetIds[1];
        floorIds[(int)FloorKind.L3999Rotten] = l3CarpetIds[2];
        floorIds[(int)FloorKind.L3999Marble] = l3MarbleIds[0];
        floorIds[(int)FloorKind.L3999MarbleBlack] = l3MarbleIds[1];
        floorIds[(int)FloorKind.L3999Concrete] = l3ConcreteFloorId;
        floorIds[(int)FloorKind.L3999Lanewood] = l3LanewoodId;
        floorIds[(int)FloorKind.L3999PoolViolet] = l3PoolIds[0];
        floorIds[(int)FloorKind.L3999PoolLilac] = l3PoolIds[1];
        floorIds[(int)FloorKind.L3999PoolEdge] = l3PoolEdgeId;
        floorIds[(int)FloorKind.L3999Asphalt] = l3AsphaltIds[0];
        floorIds[(int)FloorKind.L3999AsphaltLine] = l3AsphaltIds[1];

        if (l3999Missing.Count > 0)
            api.Logger.Warning("[backrooms] Level 3999: {0} blocks are not made yet (stand-ins used), e.g. {1}", l3999Missing.Count, l3999Missing[0]);
    }

    /// <summary>
    /// The block at <paramref name="rel"/> above the level's floor in a column of one of its tiles (0 for air); solid
    /// (concrete) wherever nothing is.
    /// </summary>
    private int Level3999Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        int colour = WorldLayout.L3999Colour(t) % 6, facing = Facing(t.Pier);
        bool dead = WorldLayout.L3999LightsDead(t);
        switch (t.Kind)
        {
            case TileKind.Wall:
            case TileKind.Door:
            case TileKind.Doorway:
                if (rel < 0) return concreteId;
                if (rel == 0) return t.Floor != 0 && floorIds[(int)t.Floor] != 0 ? floorIds[(int)t.Floor] : l3ConcreteFloorId;
                if (rel > WorldLayout.L3999AtriumHeight) return concreteId;
                if (t.Kind == TileKind.Doorway && rel <= t.Height) return 0;
                if (t.Kind == TileKind.Door)
                {
                    int part = L3999DoorPart(t, rel, facing);
                    if (part >= 0) return part;
                }
                return L3999WallBlock(t, rel, facing, colour);
            case TileKind.Water:
            {
                int depth = t.Depth;
                if (rel < -depth) return concreteId;
                if (rel == -depth) return t.Under == Unders.L3999Drain ? l3DrainId : floorIds[(int)t.Floor] is int f and not 0 ? f : l3PoolIds[0];
                if (rel <= 0) { fluid = waterId; return 0; }
                int top = t.Height == 0 ? WorldLayout.L3999AtriumHeight : t.Height;
                if (rel > top) return concreteId;
                return rel == top ? l3CeilingId : 0;
            }
        }

        // A floor tile
        int height = t.Height == 0 ? WorldLayout.L3999HallHeight : t.Height;
        if (rel < 0) return concreteId;
        if (t.Variant == Props.L3999Escalator)
        {
            // Solid under the step, the step, then air up to the ceiling
            if (rel > height) return concreteId;
            if (rel == height) return l3CeilingId;
            if (rel == 0) return floorIds[(int)t.Floor];
            return rel < t.Stair ? l3ConcreteWallId : rel == t.Stair ? l3EscalatorIds[facing] : 0;
        }
        if (rel == 0)
        {
            // (a combplate ramps up toward the floor beyond it: the way the walkway runs at its far end, back at its start)
            if (t.Variant == Props.L3999Walkway) return (t.Stack & 1) == 0 ? l3WalkwayIds[facing] : l3WalkwayEndIds[(t.Stack & 8) != 0 ? Facing(Opposite(t.Pier)) : facing];
            if (t.Floor == FloorKind.L3999PoolEdge && t.Variant == 0) return l3PoolLedIds[facing];
            return floorIds[(int)t.Floor] is int floor and not 0 ? floor : l3CarpetIds[0];
        }
        if (rel > height) return concreteId;
        if (rel == height)
        {
            return t.Ceiling switch
            {
                CeilingKind.L3999Acoustic => l3AcousticId,
                CeilingKind.L3999Fluoro => lightOnId,
                CeilingKind.L3999FluoroOff => lightOffId,
                _ => l3CeilingId,
            };
        }
        bool slab = WorldLayout.L3999HasSlab(t) && height > WorldLayout.L3999SlabRel + 1;
        if (slab && rel == WorldLayout.L3999SlabRel) return t.Zone is (byte)WorldLayout.L3999Zone.Concourse or (byte)WorldLayout.L3999Zone.Junction ? l3MarbleIds[0] : l3CarpetIds[1];
        if (slab && rel == WorldLayout.L3999SlabRel + 1)
        {
            if (WorldLayout.L3999Rail(t) is { } rail) return l3BalustradeIds[Facing(rail)];
            if (t.Pipe is >= Pipes.L3999UpperCabinet and < Pipes.L3999UpperCabinet + 4)
                return dead ? l3DeadCabinetIds[t.Pipe - Pipes.L3999UpperCabinet] : l3CabinetIds[(int)((uint)(gx * 7 + gz * 13) % 6), t.Pipe - Pipes.L3999UpperCabinet];
            if (t.Pipe is >= Pipes.L3999UpperBench and < Pipes.L3999UpperBench + 4) return l3BenchIds[t.Pipe - Pipes.L3999UpperBench];
            if (t.Pipe == Pipes.L3999UpperPlanter) return l3PlanterId;
        }
        // Neon: under the slab, just under the ceiling, the junction's sign, a unit's sign, up the wall, along its foot
        if (slab && rel == WorldLayout.L3999SlabRel - 1 && (t.Roof & WorldLayout.L3999TubeBit) != 0)
        {
            int axis = (t.Roof & WorldLayout.L3999TubeNSBit) != 0 ? 0 : 1;
            return dead ? l3DeadTubeIds[axis] : l3TubeIds[colour, axis];
        }
        if (rel == height - 1 && t.Overhead is >= Overheads.L3999TubeWE and <= Overheads.L3999DeadNS)
        {
            int axis = t.Overhead is Overheads.L3999TubeNS or Overheads.L3999DeadNS ? 0 : 1;
            return dead || t.Overhead >= Overheads.L3999DeadWE ? l3DeadTubeIds[axis] : l3TubeIds[colour, axis];
        }
        if (t.Overhead == Overheads.L3999Sign3999 && rel == 14) return WorldLayout.L3999IsDark(t) ? 0 : l3Sign3999Id;
        if (t.Overhead == Overheads.L3999Sign && rel == 5 && t.Depth is > 0 and < 8)
            return (WorldLayout.L3999IsDark(t) || dead) && t.Depth != 7 ? 0 : NeonSign(t, gx, gz, facing);
        if ((t.Roof & WorldLayout.L3999ArchBit) != 0 && rel >= 1 && rel < height && !(slab && rel == WorldLayout.L3999SlabRel)) return dead ? 0 : l3WallTubeIds[colour, facing];
        if ((t.Roof & WorldLayout.L3999BaseBit) != 0 && rel == 1 && t.Variant == 0) return dead ? 0 : NeonBaseStrip(t, gx, gz, colour, facing);
        if (t.SupplyBox) return rel == 1 ? BoxOf(t) : 0;
        if (slab && rel >= WorldLayout.L3999SlabRel && rel <= WorldLayout.L3999SlabRel + 1) return 0;
        return L3999PropBlock(t, rel, facing, colour, dead);
    }

    /// <summary>
    /// The neon strip along the foot of a unit's wall; in a corner it carries on along the side wall to meet the strip
    /// coming down that wall (the layout gives the corner tile the wall behind it only).
    /// </summary>
    private int NeonBaseStrip(in Tile t, int gx, int gz, int colour, int facing)
    {
        Tile next = TileAt(gx + PipeFaces[facing].Dx, gz + PipeFaces[facing].Dz);
        if ((next.Roof & WorldLayout.L3999BaseBit) == 0 || next.Variant != 0 || next.Level != t.Level) return l3RailIds[colour, facing];
        for (int hand = 0; hand < 2; hand++)
        {
            int side = (facing + (hand == 0 ? 3 : 1)) & 3;
            if (TileAt(gx + PipeFaces[side].Dx, gz + PipeFaces[side].Dz).Kind == TileKind.Wall && Facing(next.Pier) == ((side + 2) & 3))
                return l3RailCornerIds[colour, hand, facing];
        }
        return l3RailIds[colour, facing];
    }

    /// <summary>What stands on a floor tile at a height.</summary>
    private int L3999PropBlock(in Tile t, int rel, int facing, int colour, bool dead)
    {
        int height = t.Height == 0 ? WorldLayout.L3999HallHeight : t.Height;
        int stack = t.Stack;
        switch (t.Variant)
        {
            case 0: return 0;
            case Props.L3999Pillar: return rel < height - 1 && !(WorldLayout.L3999HasSlab(t) && rel == WorldLayout.L3999SlabRel) ? l3PillarIds[colour] : 0;
            case Props.L3999Keypad: return rel == 2 ? l3KeypadIds[facing] : 0;
            case Props.L3999TicketPile: return rel == 1 ? l3TableId : rel == 2 ? l3TicketPileId : 0;
            case Props.L3999MenuBoard: return rel == 3 ? l3MenuIds[facing] : rel == 5 && !dead ? l3StallSignIds[(stack & 7) % 6, facing] : 0;
            case Props.L3999StallCounter: return rel == 1 ? l3StallIds[(stack & 7) % 6, facing] : 0;
            case Props.L3999LampPost: return rel <= 3 ? l3PoleId : rel == 4 ? l3LampHeadIds[facing] : 0;
            case Props.L3999Generator: return rel == 2 ? l3GeneratorIds[facing] : rel == 6 ? l3SailsIds[facing] : 0;
            case Props.L3999Walkway:
                if (rel != 1 || (stack & 6) == 0) return 0;
                // The glass rail along the walkway's side (facing out from the tread)
                ArchPier dir = t.Pier, side = (stack & 4) != 0 ? WorldLayout.L3999Right(dir) : WorldLayout.L3999Opp(WorldLayout.L3999Right(dir));
                return l3WalkwayRailIds[Facing(side)];
        }
        if (rel != 1) return 0;
        return t.Variant switch
        {
            Props.L3999Cabinet => l3CabinetIds[stack % 6, facing],
            Props.L3999Themed => l3ThemedIds[stack % 12, facing],
            Props.L3999Rusted => l3RustedIds[facing],
            Props.L3999DeadCabinet => l3DeadCabinetIds[facing],
            Props.L3999RacerSeat => l3RacerIds[0, facing],
            Props.L3999RacerScreen => l3RacerIds[1, facing],
            Props.L3999DancePad => l3DanceIds[0, facing],
            Props.L3999DanceScreen => l3DanceIds[1, facing],
            Props.L3999Pinball => l3PinballIds[facing],
            Props.L3999Claw => l3ClawIds[facing],
            Props.L3999SkeeLane => l3SkeeIds[0, facing],
            Props.L3999SkeeTarget => l3SkeeIds[1, facing],
            Props.L3999AirHockey => l3AirHockeyIds[stack & 1, facing],
            Props.L3999PrizeCounter => l3PrizeCounterIds[facing],
            Props.L3999PrizeWall => l3PrizeWallIds[facing],
            Props.L3999PrizeCase => l3PrizeCaseIds[facing],
            Props.L3999Plush => l3PlushIds[stack & 3, facing],
            Props.L3999Reception => l3ReceptionIds[stack % 3, facing],
            Props.L3999Couch => l3CouchIds[stack & 1, facing],
            Props.L3999CoffeeTable => l3CoffeeTableId,
            Props.L3999LostFound => l3LostFoundIds[facing],
            Props.L3999Planter => l3PlanterId,
            Props.L3999Bench => l3BenchIds[facing],
            Props.L3999TrashBin => l3TrashBinId,
            Props.L3999Table => l3TableId,
            Props.L3999Chair => l3ChairIds[stack % 3, facing],
            Props.L3999Booth => l3BoothIds[facing],
            Props.L3999Vending => l3VendingIds[stack & 1, facing],
            Props.L3999Directory => l3DirectoryIds[facing],
            Props.L3999Lounger => l3LoungerIds[facing],
            Props.L3999Debris => l3DebrisId,
            _ => 0,
        };
    }

    /// <summary>A door of the level's at a height: a revolving door's drum and its fillers, a STAFF ONLY door, the elevator; -1 above them.</summary>
    private int L3999DoorPart(in Tile t, int rel, int facing)
    {
        switch (t.Pattern)
        {
            case WallPattern.L3999Revolving:
                if (rel > 3) return -1;
                // The middle tile draws the whole drum at its foot; the rest is invisible collision
                return rel > 1 ? l3RevolvingIds[2, facing] : t.Stack == 1 ? l3RevolvingIds[1, facing] : l3RevolvingIds[0, facing];
            case WallPattern.L3999Staff: return rel <= 2 ? l3StaffDoorIds[rel - 1, facing] : -1;
            case WallPattern.L3999Elevator: return rel <= 2 ? l3ElevatorIds[rel - 1, facing] : -1;
        }
        return -1;
    }

    /// <summary>A wall of the level's at a height (rel 1-18).</summary>
    private int L3999WallBlock(in Tile t, int rel, int facing, int colour)
    {
        int paint = l3PaintIds[colour % 3];
        // Layout version 5 on: a storey line round a lobby, a band of black marble at rel 6-7 (over the shopfront's glass too)
        if (layout.Version >= 5 && rel is 6 or 7 && t.Zone == (byte)WorldLayout.L3999Zone.Lobby && t.Pattern != WallPattern.L3999Window) return l3MarbleIds[1];
        switch (t.Pattern)
        {
            case WallPattern.L3999Concrete: return l3ConcreteWallId;
            case WallPattern.L3999PoolWall: return l3PoolIds[0];
            case WallPattern.L3999Shopfront: return rel <= 5 ? l3GlassId : rel == 6 ? l3PaintIds[1] : paint;
            case WallPattern.L3999Shutter:
                if (rel <= t.Height) return l3ShutterIds[rel == 1 ? 0 : 1, facing];
                return rel == 6 ? l3PaintIds[1] : paint;
            case WallPattern.L3999Window:
            {
                // The rim's windows at eye level; a food court's on its gallery
                int bottom = t.Zone == (byte)WorldLayout.L3999Zone.Rim ? 2 : 9;
                if (rel >= bottom && rel <= bottom + 2) return l3WindowIds[t.Variant & 3, bottom + 2 - rel, facing];
                return paint;
            }
        }
        return paint;
    }

    /// <summary>
    /// Level 3999's ways in, drawn in the levels they stand in (the tile's <see cref="Tile.Under"/> is one of the level's):
    /// Level 10's lone arcade, its car park and its windmills; Level 11's glitching stretch of alley wall; Level 37's
    /// magenta tiles. -1 where the level draws the column itself.
    /// </summary>
    private int L3999EntranceBlock(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        int facing = Facing(t.Pier);
        switch (t.Under)
        {
            case Unders.L3999GlitchWall: return rel is >= 1 and <= 3 ? l3GlitchId : -1;
            case Unders.L3999MagentaTiles: return rel == -t.Depth ? l3MagentaId : -1;
            case Unders.L3999Arcade:
            {
                if (rel <= 0) return -1;
                if (rel > 6) return 0;
                if (t.Kind == TileKind.Door && t.Pattern == WallPattern.L3999Revolving && L3999DoorPart(t, rel, facing) is int part and >= 0) return part;
                if (rel == 6) return l3BandId;
                if (rel == 1) return l3BrickId;
                return t.Variant == 1 && rel <= 4 ? l3GlassDarkId : l3StuccoId;
            }
            case Unders.L3999Lot:
            {
                if (rel < 0) return -1;
                if (rel == 0) return t.Floor == FloorKind.L3999AsphaltLine ? l3AsphaltIds[t.Pier is ArchPier.North or ArchPier.South ? 1 : 2] : l3AsphaltIds[0];
                if (t.Overhead == Overheads.L3999Sign && rel == 5) return l3SignIds[6, facing];
                return t.Variant == Props.L3999LampPost ? (rel <= 3 ? l3PoleId : rel == 4 ? l3LampHeadIds[facing] : 0) : 0;
            }
            case Unders.L3999Windmill:
            {
                if (rel <= 0) return -1;
                if (t.Kind == TileKind.Floor) return rel == 2 ? l3GeneratorIds[facing] : rel == 6 ? l3SailsIds[facing] : 0;
                if (rel <= 7) return l3MillWallId;
                if (rel == 8) return l3MillCapId;
                return rel == 9 && t.Variant == 1 ? l3BeaconRedId : 0;
            }
        }
        return -1;
    }
}
