using System;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 11, the Endless City. Its streets lie <see cref="WorldGeometry.CityDrop"/> blocks below the
/// other levels' floor, so that the towers have room to rise almost to the top of the world; the subway runs seven
/// blocks under the avenues.
///
/// A building tile knows its height (<see cref="Tile.Depth"/>), the height of the set-back it steps in at
/// (<see cref="Tile.Roof"/>), how far in from its edge it lies (<see cref="Tile.Pipe"/>) and its façade flags
/// (<see cref="Tile.Detail"/>). Its walls are drawn storey by storey, four blocks to a storey: a band at each floor,
/// and windows in the style of the building (curtain glass, mirror glass, brick, stone, concrete). Only the ground
/// floor of a building is ever fitted out; the floors above are dark behind their windows, and nobody has been up to
/// them.
/// </summary>
public sealed partial class WorldGenerator
{
    private const int PartWall = 0, PartWindow = 1, PartLit = 2, PartBlinds = 3, PartBand = 4;
    private static readonly string[] FacadeStyles = { "glass", "mirror", "brick", "brickdark", "stone", "concrete" };
    private static readonly string[] FacadeParts = { "wall", "window", "lit", "blinds", "band" };

    private readonly int[,,] facadeIds = new int[6, 5, 4];
    private readonly int[] cityPierIds = new int[6];
    private readonly int[] fasciaIds = new int[4];
    private int glassPaneId, cityRoofId, cityPlasterId, stainedGlassId, subwayTileId, subwayCeilingId, fountainRimId, poolCopingId;
    private int cityHumId, subwayRumbleId, subwayLightId, noclipBarnId;
    private int rowhouseDoorLowerId, rowhouseDoorUpperId, basementDoorLowerId, basementDoorUpperId;
    private int substationDoorLowerId, substationDoorUpperId, maintenanceDoorLowerId, maintenanceDoorUpperId, kitchenDoorLowerId, kitchenDoorUpperId;
    private readonly int[] subwayFloorIds = new int[5]; // bed, left rail, right rail, platform, edge

    private void InitCity()
    {
        for (int s = 0; s < FacadeStyles.Length; s++)
        {
            for (int p = 0; p < FacadeParts.Length; p++)
                for (int f = 0; f < 4; f++) facadeIds[s, p, f] = Id($"cityfacade-{FacadeStyles[s]}-{FacadeParts[p]}-{Sides[f]}");
            cityPierIds[s] = Id($"citypier-{FacadeStyles[s]}");
        }
        for (int f = 0; f < 4; f++) fasciaIds[f] = Id($"cityfascia-{Sides[f]}");
        glassPaneId = GameId("game:glass-plain", "game:glass-quartz");
        cityRoofId = Id("cityroof-gravel");
        cityPlasterId = Id("cityplaster-plain");
        stainedGlassId = Id("stainedglass-plain");
        subwayTileId = Id("subwaywall-tile");
        subwayCeilingId = Id("subwaywall-ceiling");
        subwayLightId = BlockId("backrooms:officelight-on");
        fountainRimId = Id("fountainrim-stone");
        poolCopingId = Id("pool-coping");
        cityHumId = Id("cityhum");
        subwayRumbleId = Id("subwayrumble");
        noclipBarnId = Id("noclipwall-barn");
        rowhouseDoorLowerId = Id("rowhousedoor-lower");
        rowhouseDoorUpperId = Id("rowhousedoor-upper");
        basementDoorLowerId = Id("basementdoor-lower");
        basementDoorUpperId = Id("basementdoor-upper");
        substationDoorLowerId = Id("substationdoor-lower");
        substationDoorUpperId = Id("substationdoor-upper");
        maintenanceDoorLowerId = Id("maintenancedoor-lower");
        maintenanceDoorUpperId = Id("maintenancedoor-upper");
        kitchenDoorLowerId = Id("kitchendoor-lower");
        kitchenDoorUpperId = Id("kitchendoor-upper");
        lampRedId = BlockId("backrooms:fluorescentlight-red");
        ceilingFanId = Id("ceilingfan");
        almondSeepId = Id("almondseep");
        tunnelDoorLowerId = Id("tunneldoor-lower");
        tunnelDoorUpperId = Id("tunneldoor-upper");
        string[] subway = { "bed", "raill", "railr", "platform", "edge" };
        for (int i = 0; i < subway.Length; i++) subwayFloorIds[i] = Id($"subwayfloor-{subway[i]}");

        floorIds[(int)FloorKind.CityMarble] = Id("cityfloor-marble");
        floorIds[(int)FloorKind.CityPlaza] = Id("cityfloor-plaza");
        floorIds[(int)FloorKind.CityGarage] = Id("cityfloor-garage");
        floorIds[(int)FloorKind.AsphaltDoubleNS] = Id("asphalt-doublens");
        floorIds[(int)FloorKind.AsphaltDoubleWE] = Id("asphalt-doublewe");
        floorIds[(int)FloorKind.AsphaltBayNS] = Id("asphalt-bayns");
        floorIds[(int)FloorKind.AsphaltBayWE] = Id("asphalt-baywe");
        floorIds[(int)FloorKind.AsphaltCracked] = Id("asphalt-cracked");
        floorIds[(int)FloorKind.ParkPath] = GameId("game:gravel-granite", "game:gravel-andesite");
        floorIds[(int)FloorKind.SubwayBed] = subwayFloorIds[0];
        floorIds[(int)FloorKind.SubwayRailL] = subwayFloorIds[1];
        floorIds[(int)FloorKind.SubwayRailR] = subwayFloorIds[2];
        floorIds[(int)FloorKind.SubwayPlatform] = subwayFloorIds[3];
        floorIds[(int)FloorKind.SubwayEdge] = subwayFloorIds[4];
        // Floors borrowed from the levels they belong to: lobby carpets, diner tiles, the church's flagstones
        floorIds[(int)FloorKind.L3Stone] = floorIds[(int)FloorKind.L3Stone] != 0 ? floorIds[(int)FloorKind.L3Stone] : sanctumStoneId;
    }

    private static int StyleIndex(WallPattern p) => p switch
    {
        WallPattern.CityGlass => 0,
        WallPattern.CityMirror => 1,
        WallPattern.CityBrick => 2,
        WallPattern.CityBrickDark => 3,
        WallPattern.CityStone => 4,
        _ => 5,
    };

    // ---- Level 11 ----

    private int Level11Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        // The city's edge: black glass from deep underground to the top of the sky
        if (t.Zone == (byte)CityKind.Rim) return cityPierIds[1];
        if (t.Depth > 0 && t.Kind != TileKind.Water) return BuildingBlock(t, gx, gz, rel);

        // The stairs down into the subway, and the subway itself
        if (t.Under is Unders.Subway or Unders.Station && rel < 0 || t.Stair > 0 && t.Under == Unders.Station && rel <= 0)
            return SubwayBlock(t, gx, gz, rel);
        if (rel < 0)
        {
            if (t.Kind == TileKind.Pit)
            {
                // An open manhole drops into the dark; the broken street falls away much further
                int depth = t.Under == Unders.Collapse ? 22 : 12;
                if (rel > -depth) return 0;
                return rel == -depth ? gravelId : concreteId;
            }
            if (t.Kind == TileKind.Water)
            {
                if (rel > -t.Depth) { fluid = waterId; return 0; }
                return rel == -t.Depth ? poolFloorId : concreteId;
            }
            if (StationWall(gx, gz, rel, out int wall)) return wall;
            // Under the middle of the streets, the hum of traffic that isn't there
            if (rel == -1 && t.Floor == FloorKind.AsphaltDoubleWE && Hashing.Mod(gx, 24) == 0) return cityHumId;
            return t.Floor is FloorKind.Lawn or FloorKind.Field && rel >= -2 ? bareSoilId : concreteId;
        }
        if (rel == 0)
        {
            if (t.Kind == TileKind.Pit) return 0;
            if (t.Kind == TileKind.Water) { fluid = waterId; return 0; }
            if (t.Kind == TileKind.Wall && t.Pattern == WallPattern.FountainRim) return poolCopingId;
            return floorIds[(int)t.Floor];
        }
        switch (t.Kind)
        {
            case TileKind.Pit or TileKind.Water: return 0;
            case TileKind.Wall when t.Pattern == WallPattern.FountainRim: return rel == 1 ? fountainRimId : 0;
            case TileKind.Bars: return rel == 1 ? BarsBlock(t) : 0;
        }
        // A sidewalk that has come loose and runs on up into the sky, a block at a time
        if (t.Roof > 0 && rel == t.Roof) return floorIds[(int)FloorKind.Sidewalk];
        return TreeOrProp(t, rel, trunk: 4);
    }

    /// <summary>A building: foundations, the ground floor, the storeys above, the roof and what stands on it.</summary>
    private int BuildingBlock(in Tile t, int gx, int gz, int rel)
    {
        int top = t.Roof > 0 && t.Pipe < 2 ? t.Roof : t.Depth;
        bool edge = t.Pipe == 0;
        bool tower = (t.Detail & CityDetail.Setback) != 0;
        var kind = (CityKind)t.Zone;

        if (rel < 0)
        {
            // The ramp down to the basement of a parking garage, which is somewhere else
            if (t.Under == Unders.GarageRamp && t.Stair > 0)
            {
                if (rel == -t.Stair) return stairIds[Facing(t.Pier)];
                if (rel > -t.Stair) return 0;
            }
            if (StationWall(gx, gz, rel, out int wall)) return wall;
            return concreteId;
        }
        if (rel == 0)
        {
            if (t.Under == Unders.GarageRamp && t.Stair > 0) return 0;
            if (edge && t.Kind is TileKind.Wall) return cityPierIds[StyleIndex(t.Pattern)];
            return floorIds[(int)t.Floor];
        }
        if (rel > top + 1) return 0;
        if (rel == top + 1)
        {
            // A parapet round the roof (and round the terrace where a tower steps back)
            if (edge || tower && top == t.Depth) return cityPierIds[StyleIndex(t.Pattern)];
            return t.Overhead switch
            {
                Props.AcUnit => propIds[Props.AcUnit, 0, Facing(t.Pier)],
                Props.WaterTank => propIds[Props.WaterTank, 0, 0],
                Props.Antenna => propIds[Props.Antenna, 0, 0],
                _ => 0,
            };
        }
        if (edge) return Facade(t, gx, gz, rel, t.Pier, kind);
        if (tower && rel > t.Roof) return Facade(t, gx, gz, rel, (ArchPier)(t.Detail & CityDetail.FacingMask), kind);
        if (rel == top) return kind == CityKind.Garage ? floorIds[(int)FloorKind.CityGarage] : cityRoofId;
        return Inside(t, gx, gz, rel, kind);
    }

    /// <summary>One block of a building's outside wall, storey by storey.</summary>
    private int Facade(in Tile t, int gx, int gz, int rel, ArchPier facing, CityKind kind)
    {
        int style = StyleIndex(t.Pattern), side = Facing(facing);
        byte detail = t.Detail;
        // The ground floor: doors, the way in, plate glass and the fascia over it with the store's sign
        if (rel <= 4 && t.Pipe == 0)
        {
            if (t.Kind == TileKind.Doorway)
            {
                if (rel <= 2) return 0;
                if (rel == 3) return Sign(t, side) is int sign and not 0 ? sign : (detail & CityDetail.Open) != 0 || kind is CityKind.Office or CityKind.Hotel
                    ? facadeIds[style, PartBand, side] : fasciaIds[side];
            }
            if (t.Kind == TileKind.Door && rel <= 2)
            {
                return kind switch
                {
                    CityKind.Substation => rel == 1 ? substationDoorLowerId : substationDoorUpperId,
                    _ => rel == 1 ? rowhouseDoorLowerId : rowhouseDoorUpperId,
                };
            }
            if ((detail & CityDetail.Storefront) != 0)
            {
                if (rel <= 2) return glassPaneId;
                if (rel == 3) return Sign(t, side) is int sign and not 0 ? sign : fasciaIds[side];
            }
        }
        if ((detail & CityDetail.Corner) != 0) return cityPierIds[style];
        int storey = rel & 3;
        if ((detail & CityDetail.Open) != 0)
        {
            // An open-sided garage deck: a low wall at each level, then open air
            return storey == 0 ? facadeIds[style, PartBand, side] : storey == 1 ? facadeIds[style, PartWall, side] : 0;
        }
        if ((detail & CityDetail.Party) != 0) return storey == 0 && style != 1 ? facadeIds[style, PartBand, side] : facadeIds[style, PartWall, side];
        // A church's tall windows of coloured glass
        if (kind == CityKind.Church)
        {
            int at = facing is ArchPier.North or ArchPier.South ? gx : gz;
            return rel >= 2 && rel <= 7 && Hashing.Mod(at, 3) == 1 ? stainedGlassId : facadeIds[style, rel % 8 == 0 ? PartBand : PartWall, side];
        }
        if (storey == 0) return facadeIds[style, PartBand, side];
        int along = facing is ArchPier.North or ArchPier.South ? gx : gz;
        bool window = style switch
        {
            0 or 1 => true,                                           // curtain glass, mirror glass: all window
            2 or 3 => Hashing.Mod(along, 2) == 1 && storey >= 2,       // brick: tall sash windows, a sill below
            4 => Hashing.Mod(along, 3) != 0 && storey <= 2,            // stone: pairs of windows between piers, a lintel above
            _ => storey == 2,                                          // concrete: ribbon windows
        };
        if (!window) return facadeIds[style, PartWall, side];
        if (style == 1) return facadeIds[style, PartWindow, side];
        // The window's room: lights left on, blinds drawn, or dark. The same for the whole of a window's storey and bay
        double r = Hashing.Unit(Hashing.Hash(seed, gx * 31 + rel / 4, gz, 0xC1A1));
        int part = r < 0.09 ? PartLit : r < 0.32 ? PartBlinds : PartWindow;
        return facadeIds[style, part, side];
    }

    private int Sign(in Tile t, int side) =>
        t.Variant >= Decor.First ? decorIds[(int)WallPattern.CityStorefront, t.Variant, 3, side] : 0;

    /// <summary>
    /// Inside a building. Only the ground floor of a building that can be entered is fitted out: floor, walls with
    /// what hangs on them, the things in the room and the ceiling over it. The floors above are dark and empty, and
    /// the sealed buildings are empty all the way up. A garage has a deck at every level, with cars on them.
    /// </summary>
    private int Inside(in Tile t, int gx, int gz, int rel, CityKind kind)
    {
        if (kind == CityKind.Garage)
        {
            if (t.Kind == TileKind.Wall) return cityPierIds[5]; // a column
            int storey = rel & 3;
            if (storey == 0) return t.Under == Unders.GarageRamp && rel == 0 ? 0 : floorIds[(int)FloorKind.CityGarage];
            if (storey == 3 && t.Ceiling is CeilingKind.LightWarm or CeilingKind.LightFlicker) return rel == 3 ? bulbOnId : bulbOffId;
            if (rel == 1)
            {
                if (t.Kind == TileKind.Bars) return BarsBlock(t);
                return AnyProp(t, rel);
            }
            // Cars on the decks above, in most of the bays
            if (storey == 1 && t.Overhead is >= 1 and <= 4 && Hashing.Unit(Hashing.Hash(seed, gx, gz, 0xC1A2 + (ulong)rel)) < 0.6)
                return carIds[(t.Overhead - 1) % 4, CarFacing(t.Pier)];
            return 0;
        }
        if (!WorldLayout.CityEnterable(kind)) return 0;
        // (Kept within the band the city is lit in, which reaches 9 above the street)
        int ceiling = kind is CityKind.Church or CityKind.Museum ? 8 : 4;
        if (rel > ceiling) return 0;
        if (rel == ceiling) return CityCeiling(t, kind);
        switch (t.Kind)
        {
            case TileKind.Wall:
            {
                int decor = Decorated(t, rel);
                if (decor != 0) return decor;
                return InnerWall(t.Pattern, rel);
            }
            case TileKind.Door:
                if (t.Pattern == WallPattern.Elevator)
                {
                    if (rel <= 3) return LiftPart(liftIds, kind == CityKind.Hotel ? 1 : 0, rel - 1, t);
                    return InnerWall(kind == CityKind.Hotel ? WallPattern.Hotel : kind == CityKind.Office ? WallPattern.Drywall : WallPattern.CityPlaster, rel);
                }
                if (rel <= 2)
                {
                    return kind == CityKind.Diner ? (rel == 1 ? kitchenDoorLowerId : kitchenDoorUpperId)
                        : rel == 1 ? basementDoorLowerId : basementDoorUpperId;
                }
                return InnerWall(t.Pattern, rel);
            case TileKind.Doorway:
                return rel <= 2 ? 0 : InnerWall(t.Pattern, rel);
            case TileKind.Bars:
                return rel == 1 ? BarsBlock(t) : 0;
        }
        // Stairs that climb into the ceiling and stop
        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? InnerWall(WallPattern.CityPlaster, rel) : stairIds[Facing(t.Pier)];
        if (rel == ceiling - 1 && t.Ceiling == CeilingKind.Chandelier) return chandelierId;
        return rel == 1 ? AnyProp(t, rel) : 0;
    }

    /// <summary>The walls inside a ground floor, in the material of what it is: an office's drywall, a hotel's panelling, a diner's pastel.</summary>
    private int InnerWall(WallPattern pattern, int rel) => pattern switch
    {
        WallPattern.Drywall => rel == 1 ? officeWallBaseId : officeWallId,
        WallPattern.Hotel => HotelWall(Math.Min(rel, 3)),
        WallPattern.SnackMall => snackWallIds[WallPattern.SnackMall],
        WallPattern.InteriorBeige => interiorIds[WallPattern.InteriorBeige],
        WallPattern.CityConcrete => cityPierIds[5],
        _ => cityPlasterId,
    };

    private int CityCeiling(in Tile t, CityKind kind)
    {
        if (kind is CityKind.Hotel or CityKind.Church)
        {
            return t.Ceiling switch
            {
                CeilingKind.LightOn or CeilingKind.LightLit => domeIds[0],
                CeilingKind.LightOff => domeIds[1],
                CeilingKind.LightFlicker => domeIds[2],
                _ => creamCeilingId,
            };
        }
        if (kind == CityKind.Diner && t.Ceiling == CeilingKind.Tile) return snackCeilingId;
        return t.Ceiling switch
        {
            CeilingKind.LightOn => officeLightIds[0],
            CeilingKind.LightLit => officeLightIds[1],
            CeilingKind.LightOff => officeLightIds[2],
            CeilingKind.LightFlicker => officeLightIds[3],
            _ => officeCeilingId,
        };
    }

    // ---- The subway ----

    /// <summary>
    /// Under an avenue (<see cref="Tile.Pipe"/> is the offset across it): a tunnel with two tracks and a walkway
    /// either side, or at a station, platforms along both sides under tiled walls, with stairs up to the sidewalks.
    /// </summary>
    private int SubwayBlock(in Tile t, int gx, int gz, int rel)
    {
        int ax = t.Pipe;
        bool station = t.Under == Unders.Station;
        if (t.Stair > 0)
        {
            // The stairs down from the sidewalk
            if (rel == -t.Stair) return stairIds[Facing(t.Pier)];
            if (rel > -t.Stair) return 0;
            return rel >= -6 ? subwayFloorIds[3] : concreteId;
        }
        if (rel <= -8) return rel == -8 && ax == 8 && Hashing.Mod(gz, 40) == 0 ? subwayRumbleId : concreteId;
        int along = gz - layout.CityOriginZ;
        bool inside = station || ax >= 4 && ax <= 12;
        bool wall = !station && (ax == 3 || ax == 13);
        if (wall)
        {
            int local = rel + 7; // height above the track bed
            ArchPier into = ax == 3 ? ArchPier.East : ArchPier.West;
            // A door in the tunnel wall now and then, marked for maintenance. It opens onto the pipes of Level 2
            if (Hashing.Mod(along, 151) == 75 && ax == 3)
            {
                if (local == 1) return maintenanceDoorLowerId;
                if (local == 2) return maintenanceDoorUpperId;
            }
            if (local == 3 && Hashing.Mod(along, 12) == 6) return decorIds[(int)WallPattern.SubwayTile, Decor.SubwayLamp, 3, Facing(into)];
            return subwayTileId;
        }
        if (!inside) return concreteId;
        bool platform = station && (ax <= 4 || ax >= 12);
        if (rel == -1)
        {
            // The ceiling: fluorescent tubes over the platforms
            if (platform && (ax == 2 || ax == 14) && Hashing.Mod(gz, 4) == 0) return subwayLightId;
            return subwayCeilingId;
        }
        if (platform)
        {
            if (rel == -7) return concreteId;
            if (rel == -6) return ax is 4 or 12 ? subwayFloorIds[4] : subwayFloorIds[3];
            if (rel == -5)
            {
                // Benches facing the tracks, an Almond Water machine, a bin
                int k = Hashing.Mod(along, 9);
                if ((ax == 2 || ax == 14) && k == 0) return propIds[Props.Bench, 0, Facing(ax == 2 ? ArchPier.East : ArchPier.West)];
                if ((ax == 1 || ax == 15) && Hashing.Mod(along, 17) == 8) return vendingIds[Facing(ax == 1 ? ArchPier.East : ArchPier.West)];
                if ((ax == 3 || ax == 13) && k == 4) return propIds[Props.TrashCan, 0, 0];
            }
            return 0;
        }
        // The tracks: two rails on their sleepers, ballast between; columns down the middle
        if (rel == -7)
        {
            return ax switch
            {
                5 or 10 => subwayFloorIds[1],
                6 or 11 => subwayFloorIds[2],
                _ => subwayFloorIds[0],
            };
        }
        if (ax == 8 && Hashing.Mod(gz, 6) == 0) return subwayTileId;
        return 0;
    }

    /// <summary>The tiled walls of a station, in the ground beside the avenue: signs naming the station, maps, advertisements.</summary>
    private bool StationWall(int gx, int gz, int rel, out int block)
    {
        block = 0;
        if (rel < -7 || rel > -1) return false;
        int ux = gx - layout.CityOriginX, uz = gz - layout.CityOriginZ;
        int ax = Hashing.Mod(ux, WorldLayout.AvePitch);
        if (ax != WorldLayout.AveWidth && ax != WorldLayout.AvePitch - 1) return false;
        if (Hashing.Mod(uz + WorldLayout.StationReach, WorldLayout.StreetPitch * WorldLayout.StationEvery) >= WorldLayout.StationLength) return false;
        int local = rel + 6; // height above the platform
        int facing = Facing(ax == WorldLayout.AveWidth ? ArchPier.West : ArchPier.East);
        int k = Hashing.Mod(uz, 13);
        byte decor = local switch
        {
            3 when k == 3 => Decor.StationSign,
            2 when k == 9 => Hashing.Mod(uz, 26) < 13 ? Decor.SubwayMap : Decor.SubwayAd,
            3 when k == 9 => Decor.SubwayLamp,
            _ => 0,
        };
        block = decor != 0 ? decorIds[(int)WallPattern.SubwayTile, decor, local, facing] : 0;
        if (block == 0) block = subwayTileId;
        return true;
    }

    /// <summary>Which of the four car blocks faces a way.</summary>
    private static int CarFacing(ArchPier p) => p switch { ArchPier.North => 0, ArchPier.South => 1, ArchPier.East => 2, _ => 3 };
}
