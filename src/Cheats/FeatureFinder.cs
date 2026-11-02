using System;
using System.Collections.Generic;
using System.Linq;
using Backrooms.Worldgen;

namespace Backrooms.Cheats;

/// <summary>
/// Finds the nearest of a kind of place round a position, from the layout alone (no blocks, no game): the searches
/// behind <c>/backrooms nearest</c> and <c>/backrooms feature</c> (the cheat menu's "Go to feature" list,
/// <see cref="FeatureCatalog"/>). Pure, so the layout harness (tools/mapgen, mode featurecheck) runs the very same
/// finders. A miss leaves <see cref="Error"/> set when the search cannot be made here (the wrong level), and
/// <see cref="Stopped"/> when a tile scan ran out of time.
/// </summary>
public sealed class FeatureFinder
{
    /// <summary>What a search found.</summary>
    public sealed class Hit
    {
        /// <summary>The place found (the distance and position reported are to it).</summary>
        public int X, Z;
        /// <summary>Where to stand, when the finder chose it; else the nearest open floor to the place (<see cref="Resolve"/>).</summary>
        public (int X, int Z)? Stand;
        /// <summary>An exact height for the feet, when standing on the floor at the arrival height is not right (afloat, down a shaft).</summary>
        public double? FeetY;
        /// <summary>Said after the name: which way to look, how many guests...</summary>
        public string Detail = "";
        /// <summary>The whole reply, when the finder words it itself.</summary>
        public string Message;
        /// <summary>Nothing was near: this one is somewhere else in the level.</summary>
        public bool Elsewhere;
    }

    /// <summary>The furthest a tile scan reaches, whatever radius was asked for: it builds every tile of every cell.</summary>
    public const int TileScanMaxRadius = 1024;
    /// <summary>The longest a tile scan runs, in seconds (on the server's main thread).</summary>
    public const int TileScanSeconds = 2;

    private readonly WorldLayout layout;
    private readonly WorldGeometry geometry;

    /// <summary>Why the last search could not be made here (e.g. the wrong level), or null.</summary>
    public string Error;
    /// <summary>Whether the last tile scan gave up on the time limit (a miss is then "stopped", not "none there").</summary>
    public bool Stopped;
    /// <summary>How long a tile scan may run, in milliseconds (the harness lets it run longer).</summary>
    public int TileScanMillis = TileScanSeconds * 1000;

    public FeatureFinder(WorldLayout layout, WorldGeometry geometry)
    {
        this.layout = layout;
        this.geometry = geometry;
    }

    // ================================ The features of the menu ================================

    /// <summary>
    /// The nearest of a catalogue feature to a position in a level, within the radius; null if none (or if it cannot be
    /// looked for here: <see cref="Error"/>). For the kinds <c>/backrooms find</c> used to look for anywhere in a level,
    /// a miss nearby settles for one elsewhere (picked by <paramref name="key"/>).
    /// </summary>
    public Hit Feature(string code, int gx, int gz, int radius, int level, ulong key)
    {
        Error = null;
        Stopped = false;
        int lv = level;
        Hit TileHit(Func<Tile, bool> match) => At(NearestTile(gx, gz, radius, lv, match, out _));
        Hit TileAtHit(Func<Tile, int, int, bool> match) => At(NearestTileAt(gx, gz, radius, lv, match, out _));
        Hit CellHit(Func<int, int, bool> match) => At(NearestCell(gx, gz, radius, (mx, mz) => layout.LevelAt(mx, mz) == lv && match(mx, mz)));
        Hit Float(Func<Tile, bool> match) =>
            NearestTile(gx, gz, radius, lv, match, out _) is { } w ? new Hit { X = w.X, Z = w.Z, Stand = w, FeetY = geometry.FloorFor(lv) + 0.2, Detail = " (afloat over it: dive)" } : null;
        Hit Points(IEnumerable<(int X, int Z)> points) => At(Closest(gx, gz, radius, points));
        Hit Room(Func<FunRoom, bool> want) => Points(layout.FunRoomsNear(gx, gz, radius).Where(want).Select(r => ((r.X0 + r.X1) / 2, (r.Z0 + r.Z1) / 2)));
        Hit Unit(Func<WorldLayout.L3999Unit, bool> want) => At(layout.L3999UnitsNear(gx, gz, want, radius) is { Count: > 0 } units ? units[0] : null);
        Hit Dept(Func<int, int, bool> want) => At(EndDept(gx, gz, radius, want));
        Hit Hill(string top) => At(NearestHill(gx, gz, radius, top));
        Hit PoolRoom(string kind) => At(NearestPoolRoom(gx, gz, radius, kind));
        Hit Fixed(int x, int z) => new() { X = x, Z = z };
        // A miss nearby settles for one anywhere in the level, as /backrooms find did
        Hit OrAnywhere(Hit near, Func<Tile, bool> anchor)
        {
            if (near != null || Error != null) return near;
            for (int attempt = 0; attempt < 4; attempt++, key = Hashing.Mix(key))
                if (layout.FindArrival(lv, key, anchor) is { } spot && Beside(spot.X, spot.Z, anchor))
                    return new Hit { X = spot.X, Z = spot.Z, Stand = spot, Elsewhere = true };
            return null;
        }

        switch (code)
        {
            // ----- Shared by several levels -----
            case "elevator":
            {
                Func<Tile, bool> anchor = t => t.Kind == TileKind.Door && t.Pattern == WallPattern.Elevator;
                return OrAnywhere(TileHit(anchor), anchor);
            }
            case "stairs":
            {
                // (Level 1's stair cores, Level 4's stairwells; not Level 1's flights to nowhere or to Level Fun)
                Func<Tile, bool> anchor = t => t.Stair > 0 && t.Under == 0 && !t.Grand && (t.Level != 1 || t.Zone is WorldLayout.FlightZoneUp or WorldLayout.FlightZoneDown);
                return OrAnywhere(TileHit(anchor), anchor);
            }
            case "pit" when level == WorldLayout.Poolrooms:
                return PoolRoom("StairPit");
            case "pit":
            {
                Func<Tile, bool> anchor = t => t.Kind == TileKind.Pit && t.Under == 0;
                return OrAnywhere(TileHit(anchor), anchor);
            }
            case "tent":
                return Target("tent", gx, gz, radius, level, "Camp tent");

            // ----- Level 0 -----
            case "manila": return CellHit(layout.IsManilaMacro);
            case "l0blackout": return CellHit((mx, mz) => layout.ZoneAt(mx, mz) == ZoneKind.Blackout);
            case "l0arches": return CellHit((mx, mz) => layout.ZoneAt(mx, mz) == ZoneKind.Arches);
            case "l0pillars": return CellHit((mx, mz) => layout.ZoneAt(mx, mz) == ZoneKind.PillarHall);
            case "l0office": return CellHit((mx, mz) => layout.ZoneAt(mx, mz) == ZoneKind.OpenOffice);
            case "l0party": return CellHit(layout.IsFunPartyCell);
            case "l0window": return TileHit(t => t.Under == Unders.L188Entrance && (t.Detail & 15) == 0);

            // ----- Level 1 -----
            case "l1nowhere": return TileHit(t => t.Zone == WorldLayout.FlightZoneNowhere && t.Stair > 0);
            case "l1funstairs": return TileHit(t => t.Zone == WorldLayout.FlightZoneFun && t.Stair > 0);
            case "l1halls": return TileHit(t => t.Kind == TileKind.Floor && t.Floor == FloorKind.L1Hall);
            case "l1firstaid": return TileHit(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.HospitalBed);
            case "l1hubdoor":
            case "l2hubdoor":
                return At(layout.NearestHubEntrance(gx, gz, level, radius));
            case "l1enddoor": return TileHit(t => t.Under == Unders.EndExitL1);
            case "l1rundoor": return CellThenTile(gx, gz, radius, lv, layout.CheatIsRunEntranceCellL1, t => t.Under == Unders.RunEntrance);
            case "l1window": return CellThenTile(gx, gz, radius, lv, layout.IsL188WindowCellL1, t => WorldLayout.IsL188Entrance(t, 1));

            // ----- Level 2 -----
            case "l2gallery": return Points(layout.CheatL2Galleries(gx, gz, radius / 64 + 1));
            case "l2runwall": return TileHit(t => t.Under == Unders.RunFalseWall);

            // ----- Level 3 -----
            case "l3sanctum": return CellHit(layout.CheatIsL3Sanctum);
            case "l3transformer":
            case "l3assembly":
            {
                int want = code == "l3transformer" ? 1 : 2;
                if (NearestCell(gx, gz, radius, (mx, mz) => layout.CheatL3Hall(mx, mz).Kind == want) is not { } cell) return null;
                var hall = layout.CheatL3Hall(WorldLayout.MacroOf(cell.X), WorldLayout.MacroOf(cell.Z));
                return Fixed((hall.X0 + 1) * WorldLayout.MacroSize, (hall.Z0 + 1) * WorldLayout.MacroSize);
            }
            case "l3shrine":
                return TileAtHit((t, x, z) => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.AngelStatue && !layout.CheatIsL3Sanctum(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)));
            case "l3window": return TileHit(t => t.Variant == Worldgen.Props.WindowGlow);
            case "l3sludge": return TileHit(t => t.Floor == FloorKind.Tar);

            // ----- Level 4 -----
            case "l4camp": return TileHit(t => t.Detail == WorldLayout.L4CampSite);
            case "l4endframe": return TileHit(t => t.Under == Unders.EndFrame);

            // ----- Level 5 -----
            case "l5grand":
            {
                // The front hall's view looks at the desk and the grand staircases behind it
                if (NearestSpot(gx, gz, radius, layout.FrontHallView) is not { } v) return null;
                var (fx, fz) = PierStep(v.Facing);
                return new Hit { X = v.X + 9 * fx, Z = v.Z + 9 * fz, Detail = $" (heading {PierHeading(v.Facing, false)} looks up them)" };
            }
            case "l5beverly": return CellHit((mx, mz) => layout.IsBeverlyMacro(mx, mz));
            case "l5dining": return CellHit(layout.CheatIsL5Dining);
            case "l5boiler": return CellHit((mx, mz) => layout.IsHotelBoilerHall(mx * WorldLayout.MacroSize + 16, mz * WorldLayout.MacroSize + 16));
            case "l5staff": return TileHit(t => t.Stair > 0 && !t.Grand && t.Under == 0);
            case "l5fundoor": return TileHit(t => t.Kind == TileKind.Door && t.Pattern == WallPattern.FunDoor);

            // ----- Level 6 -----
            case "descent":
            {
                Func<Tile, bool> anchor = t => t.Under is >= Unders.Descent1 and <= Unders.Descent3;
                return OrAnywhere(TileHit(anchor), anchor);
            }
            case "l6tripwire": return TileHit(t => t.Variant == Worldgen.Props.Tripwire && t.Kind == TileKind.Floor);
            case "snackrooms":
            {
                Hit near = CellHit(layout.IsSnackrooms);
                if (near != null || Error != null) return near;
                for (int attempt = 0; attempt < 4; attempt++, key = Hashing.Mix(key))
                    if (layout.FindSnackroomsArrival(key) is { } s) return new Hit { X = s.X, Z = s.Z, Stand = s, Elsewhere = true };
                return null;
            }
            case "l6snackexit": return TileHit(t => t.Kind == TileKind.Door && t.Pattern == WallPattern.SnackMall);

            // ----- Level 7 -----
            case "entryroom":
            {
                Func<Tile, bool> foot = t => t.Zone == WorldLayout.L7ZoneRoom && t.Detail == WorldLayout.L7EntryFoot;
                if (NearestTile(gx, gz, radius, lv, foot, out _) is { } f) return new Hit { X = f.X, Z = f.Z, Stand = f };
                if (Error != null) return null;
                return layout.FindEntryRoomArrival(key) is { } e ? new Hit { X = e.X, Z = e.Z, Stand = e, Elsewhere = true } : null;
            }
            case "l7island": return TileHit(t => t.Kind == TileKind.Floor && t.Floor == FloorKind.Seabed && t.Depth == 0 && t.Height >= 1);
            case "l7jetty": return TileHit(t => t.Floor == FloorKind.Jetty);
            case "l7circle": return Float(t => t.Under == Unders.Circle);
            case "l7cave": return Float(t => t.Under == Unders.Cave);
            case "l7tiled": return Float(t => t.Under == Unders.TiledSeabed);

            // ----- Level 8 -----
            case "l8road": return TileAtHit((t, x, z) => t.Kind == TileKind.Floor && layout.IsNinthRoad(x, z));
            case "l8camp": return TileHit(t => t.Kind == TileKind.Floor && t.Variant is Worldgen.Props.CampTent or Worldgen.Props.BurnBarrel);
            case "l8seep": return TileHit(t => t.Variant == Worldgen.Props.AlmondSeep && t.IsWallLike);
            case "l8vent": return TileHit(t => t.Kind == TileKind.Wall && t.Variant == Worldgen.Props.CaveVent);
            case "l8rockfall": return TileHit(t => t.Kind == TileKind.Wall && t.Zone > WorldLayout.L8ZoneRubble);
            case "l8nest":
            {
                // The heart is in the rock, off the road: stand on the nearest floor to it
                if (CellHit((mx, mz) => layout.DenAt(mx, mz) == DenKind.Nest) is not { } nest) return null;
                nest.Stand = NearestTile(nest.X, nest.Z, 128, lv, t => t.Kind == TileKind.Floor && t.Variant == 0 && t.Stack == 0, out _);
                return nest;
            }

            // ----- Level 9 -----
            case "l9pool": return TileHit(t => t.Floor == FloorKind.PoolDeep && t.Under == 0);
            case "l9fullpool": return TileHit(t => t.Under == Unders.FullPool);
            case "l9dollhouse":
            case "l94dollhouse":
                return TileHit(t => t.Kind == TileKind.Door && t.Under == Unders.DollHouse);
            case "l9fieldgate": return TileHit(t => t.Variant == Worldgen.Props.FieldGate);
            case "l9shed": return TileHit(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.SeedSacks);
            case "l9swings": return TileHit(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.SwingSet);
            case "l9veg": return TileHit(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.Vegetable);

            // ----- Level 10 -----
            case "l10scarecrow": return TileHit(t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.Scarecrow);
            case "l10farm": return TileHit(t => t.Kind == TileKind.Wall && t.Pattern == WallPattern.BarnRed);
            case "l10noclip": return TileHit(t => t.Under == Unders.Noclip);
            case "l10pond": return TileHit(t => t.Under == Unders.LakeRim);
            case "l10pasture": return TileAtHit((t, x, z) => t.Kind == TileKind.Floor && layout.IsPasture(x, z));
            case "l10arcade": return Points(Arcades(gx, gz, radius));
            case "l10windmill": return Points(ArcadeSites(gx, gz, radius).SelectMany(site => site.Mills));

            // ----- Level 11 (a building's kind is in its ground floor's Zone) -----
            case "l11station": return TileHit(t => t.Under == Unders.Station && t.Stair > 0);
            case "l11church": return CityDoor(gx, gz, radius, CityKind.Church);
            case "l11museum": return CityDoor(gx, gz, radius, CityKind.Museum);
            case "l11diner": return CityDoor(gx, gz, radius, CityKind.Diner);
            case "l11hotel": return CityDoor(gx, gz, radius, CityKind.Hotel);
            case "l11office": return CityDoor(gx, gz, radius, CityKind.Office);
            case "l11cinema": return CityDoor(gx, gz, radius, CityKind.Cinema);
            case "l11baths": return CityDoor(gx, gz, radius, CityKind.Baths);
            case "l11substation": return CityDoor(gx, gz, radius, CityKind.Substation);
            case "l11bookstore": return TileHit(t => t.Under == Unders.EndBookstore);
            case "l11garage": return TileHit(t => t.Under == Unders.GarageRamp);
            case "l11mascot": return TileHit(t => t.Under == Unders.FunMascotDoor);
            case "l11manhole": return TileHit(t => t.Under == Unders.OpenManhole);
            case "l11collapse": return TileHit(t => t.Under == Unders.Collapse);
            case "l11alley": return TileHit(t => t.Under == Unders.DarkPassage);
            case "l11fountain": return TileHit(t => t.Under == Unders.FountainDeep);
            case "l11wheat": return TileHit(t => t.Under == Unders.WheatPatch);
            case "l11glitch": return TileHit(t => t.Under == Unders.L3999GlitchWall);

            // ----- Level 37 -----
            case "l37rotunda": return PoolRoom("Rotunda");
            case "l37natatorium": return PoolRoom("Natatorium");
            case "l37pillars": return PoolRoom("PillarHall");
            case "l37serpentine": return PoolRoom("Serpentine");
            case "l37pitbottom": return TileHit(t => t.Under == Unders.PitBottom);
            case "l37door": return TileHit(t => t.Kind == TileKind.Door && t.Pattern == WallPattern.PoolDoor);
            case "l37hole": return TileHit(t => t.Under == Unders.PoolHole);
            case "l37tunnel": return TileHit(t => t.Under == Unders.TunnelMouth);
            case "l37carpet": return TileHit(t => t.Under == Unders.PoolCarpet);
            case "l37run": return TileHit(t => t.Under == Unders.RunRedCorridor);
            case "l37asphalt": return TileHit(t => t.Under == Unders.PoolAsphalt);
            case "l37magenta": return Float(t => t.Under == Unders.L3999MagentaTiles);
            case "l37reservoir": return At(layout.NearestReservoir(gx, gz, radius));

            // ----- Level 94 -----
            case "l94castle":
                // The gate is in the castle's south wall, up on the mountain's top
                return new Hit { X = layout.MotionOriginX, Z = layout.MotionOriginZ + WorldLayout.CastleSize / 2, Stand = StandNear(layout.MotionOriginX, layout.MotionOriginZ + WorldLayout.CastleSize / 2 + 3, lv), Detail = " (heading 0 looks at the gate)" };
            case "l94mountain":
                return new Hit { X = layout.MotionOriginX, Z = layout.MotionOriginZ, Stand = StandNear(layout.MotionOriginX, layout.MotionOriginZ + WorldLayout.MountainRadius + 6, lv), Detail = " (heading 0 looks up at it)" };
            case "l94town": return TileHit(t => t.Variant == Worldgen.Props.AlmondFountain && t.Stack == 12);
            case "l94siren": return At(layout.NearestSirenPole(gx, gz, radius));
            case "l94house": return Hill("House");
            case "l94kitchen": return Hill("Kitchen");
            case "l94bedroom": return Hill("Bedroom");
            case "l94parlour": return Hill("Parlour");
            case "l94pile": return Hill("Pile");
            case "l94tower": return Hill("WaterTower");
            case "l94car": return Hill("Car");
            case "l94gate": return Hill("Gate");
            case "l94nowhere": return TileHit(t => t.Under == Unders.Nowhere);
            case "l94flooded": return TileHit(t => t.Kind == TileKind.Door && t.Under == Unders.FloodedHouse);

            // ----- Level ! (the lane you are in) -----
            case "runstart":
            case "runsafe":
            case "runfake":
            case "runhole":
            case "runexit":
            {
                int here = level == WorldLayout.RunLevel ? layout.RunLaneAt(gx, gz) : -1;
                if (here < 0) { Error = "That is in a lane of Level ! (/backrooms goto !)"; return null; }
                // Your own lane, or for what only some lanes have, the nearest lane that has it
                int lane = Enumerable.Range(0, WorldLayout.RunLanes).OrderBy(l => Math.Abs(l - here))
                    .FirstOrDefault(l => code switch { "runsafe" => layout.RunPlan(l).HasSafe, "runhole" => layout.RunPlan(l).HasHole, _ => l == here }, -1);
                if (lane < 0) { Error = $"No lane of Level ! has {(code == "runsafe" ? "a Safe Zone" : "a hole")} in this world"; return null; }
                WorldLayout.RunLane plan = layout.RunPlan(lane);
                (int X, int Z) W((int X, int Z) p) => layout.RunWorld(lane, p.X, p.Z);
                switch (code)
                {
                    case "runstart":
                        return new Hit { X = W(plan.Arrival).X, Z = W(plan.Arrival).Z, Stand = W(plan.Arrival) };
                    case "runsafe":
                        return At(W(plan.LineAt(plan.SafeFrom)));
                    case "runfake":
                        return Points(plan.FakeExits.Select(f => W((f.FrontX, f.FrontZ))));
                    case "runhole":
                        int i = Array.FindIndex(plan.Tiles, t => t.Under == Unders.RunHole);
                        return i < 0 ? null : At(W((i % WorldLayout.RunLane.Width, i / WorldLayout.RunLane.Width)));
                    default:
                        return new Hit { X = W(plan.ExitDoor).X, Z = W(plan.ExitDoor).Z, Stand = W(plan.LineAt(plan.ExitS - 2)), Detail = $" (to {LevelName(plan.Destination)})" };
                }
            }

            // ----- Level Fun -----
            case "funover": return Room(r => r.Kind == FunZone.Party && r.Guests == 0);
            case "funmural": return Room(r => r.Kind == FunZone.Mural);
            case "funthemed": return Room(r => r.Kind == FunZone.Themed);
            case "funplay": return Room(r => r.Kind == FunZone.Play);
            case "funbounce": return Room(r => r.Kind == FunZone.Bounce);
            case "funarcade": return Room(r => r.Kind == FunZone.Arcade);
            case "funkitchen": return Room(r => r.Kind == FunZone.Kitchen);
            case "fungifts": return Room(r => r.Kind == FunZone.Gifts);
            case "fundeck": return Room(r => r.Kind == FunZone.Deck);
            case "funwaiting": return Room(r => r.Kind == FunZone.Waiting);
            case "funvestibule": return Room(r => r.Kind == FunZone.Vestibule);
            case "funstairs": return Room(r => r.Kind == FunZone.Stair);
            case "funclone": return Room(r => r.Kind == FunZone.Clone);

            // ----- The End -----
            case "endcentral": return At(layout.EndDeptCentre(0, 0));
            case "enddesk": return Dept((di, dj) => layout.EndKindAt(di, dj) == WorldLayout.EndKind.Desk);
            case "endreading": return Dept((di, dj) => layout.EndKindAt(di, dj) == WorldLayout.EndKind.Reading);
            case "endatrium": return Dept((di, dj) => layout.EndKindAt(di, dj) == WorldLayout.EndKind.Atrium);
            case "endstock": return Dept((di, dj) => layout.EndKindAt(di, dj) == WorldLayout.EndKind.Stock);
            case "endloop": return Dept((di, dj) => layout.EndKindAt(di, dj) is WorldLayout.EndKind.LongLeft or WorldLayout.EndKind.LongRight);
            case "endcollapse": return Dept((di, dj) => layout.EndKindAt(di, dj) == WorldLayout.EndKind.Collapse);
            case "endfake": return Dept((di, dj) => layout.EndKindAt(di, dj) == WorldLayout.EndKind.Fake);

            // ----- The Hub -----
            case "hubtower":
                return new Hit { X = layout.HubOriginX, Z = layout.HubOriginZ, Stand = StandNear(layout.HubOriginX, layout.HubOriginZ + 34, lv), Detail = " (heading 0 looks at it)" };
            case "hubmeg": return At(layout.HubMegSite());
            case "hubcamp": return At(layout.CheatHubCampSite());
            case "hubdoor":
            {
                var doors = Enumerable.Range(0, WorldLayout.LevelCount).Append(WorldLayout.HubSnackroomsDoor)
                    .Select(l => (Level: l, Door: layout.HubDoorOf(l))).Where(d => d.Door != null).ToList();
                var best = doors.OrderBy(d => Sq(d.Door.Value.X - gx, d.Door.Value.Z - gz)).FirstOrDefault();
                if (best.Door is not { } door || Sq(door.X - gx, door.Z - gz) > (long)radius * radius) return null;
                var (fx, fz) = PierStep(door.Facing);
                return new Hit { X = door.X, Z = door.Z, Stand = StandNear(door.X + 2 * fx, door.Z + 2 * fz, lv),
                    Detail = $" (to {(best.Level == WorldLayout.HubSnackroomsDoor ? "Level 6.1" : LevelName(best.Level))}{(WorldLayout.HubDoorOpen(best.Level) ? ", open" : ", needs its key")})" };
            }
            case "hubwindow":
            {
                if (layout.HubWindowOf() is not { } w) return null;
                var (fx, fz) = PierStep(w.Facing);
                return new Hit { X = w.Left.X, Z = w.Left.Z, Stand = StandNear(w.Left.X + 2 * fx, w.Left.Z + 2 * fz, lv) };
            }
            case "hubtileend":
                return Points(Enumerable.Range(0, 5).Select(k => layout.HubTileEndArrival((ulong)k)).Where(p => p != null).Select(p => p.Value).Distinct());
            case "hubhole": return TileHit(t => t.Under == Unders.HubHole);
            case "hubfalsewall": return TileHit(t => t.Under == Unders.HubFalseWall);
            case "hubfar": return TileHit(t => t.Zone == WorldLayout.HubZoneFar && t.Kind == TileKind.Floor);

            // ----- Level 974 (a room's kind is in its tiles' Zone) -----
            case "l974living": return TileHit(t => t.Kind == TileKind.Floor && t.Zone == (byte)WorldLayout.L974Room.Living);
            case "l974kitchen": return TileHit(t => t.Kind == TileKind.Floor && t.Zone == (byte)WorldLayout.L974Room.Kitchen);
            case "l974master": return TileHit(t => t.Kind == TileKind.Floor && t.Zone == (byte)WorldLayout.L974Room.Master);
            case "l974bedroom": return TileHit(t => t.Kind == TileKind.Floor && t.Zone == (byte)WorldLayout.L974Room.Bedroom);
            case "l974bath": return TileHit(t => t.Kind == TileKind.Floor && t.Zone is (byte)WorldLayout.L974Room.Bath or (byte)WorldLayout.L974Room.HalfBath);
            case "l974hall": return TileHit(t => t.Kind == TileKind.Floor && t.Zone == (byte)WorldLayout.L974Room.Hall);

            // ----- Level 3999 -----
            case "l3999lobby": return Unit(u => u.Kind == WorldLayout.L3999Kind.Lobby);
            case "l3999game": return Unit(u => u.Kind == WorldLayout.L3999Kind.Game && !u.Mini);
            case "l3999hall": return Unit(u => u.Kind == WorldLayout.L3999Kind.GameHall);
            case "l3999lanes": return Unit(u => u.Kind == WorldLayout.L3999Kind.Lanes);
            case "l3999natatorium": return Unit(u => u.Kind == WorldLayout.L3999Kind.Natatorium);
            case "l3999shuttered": return Unit(u => u.Kind == WorldLayout.L3999Kind.Shuttered);
            case "l3999mini": return Unit(u => u.Mini);
            case "l3999junction": return TileHit(t => t.Kind == TileKind.Floor && t.Zone == (byte)WorldLayout.L3999Zone.Junction);
            case "l3999drain":
            {
                // One natatorium in three has a drain: the nearest of those
                foreach (var nat in layout.L3999UnitsNear(gx, gz, u => u.Kind == WorldLayout.L3999Kind.Natatorium, radius, 12))
                    if (NearestTile(nat.X, nat.Z, 64, lv, t => t.Under == Unders.L3999Drain, out _) is { } drain) return At(drain);
                return null;
            }
            case "l3999blackout": return At(NearestBlackout(gx, gz, radius));

            // ----- Level 188 (one building: its places are fixed) -----
            case "l188deck": return Fixed(layout.L188BuildX0 + 40, layout.L188BuildZ0 + 29);
            case "l188hatch": return TileHit(t => t.Under == Unders.L188Hatch);
            case "l188window":
            {
                if (NearestTile(gx, gz, radius, lv, t => t.Under == Unders.L188LinkWindow, out Tile window) is not { } wf) return null;
                return new Hit { X = wf.X, Z = wf.Z, Detail = $" (shows {LevelName(window.Detail)})" };
            }
            case "l188lobby": return Fixed(layout.L188BuildX0 + 44, layout.L188BuildZ0 + 54);
            case "l188stairs": return Fixed(layout.L188BuildX0 + 10, layout.L188BuildZ0 + 14);
            case "l188firedoor": return TileHit(t => t.Under == Unders.L188FireDoor);

            // ----- The rest are /backrooms nearest's own targets -----
            default:
                if (Targets.Any(t => t.Code == code)) return Target(code, gx, gz, radius, level, null);
                Error = $"No finder for {code}";
                return null;
        }
    }

    /// <summary>The nearest building of a Level 11 kind: its door if it has one in reach of the street, else any of its tiles.</summary>
    private Hit CityDoor(int gx, int gz, int radius, CityKind kind) =>
        At(NearestTile(gx, gz, radius, 11, t => t.Zone == (byte)kind && t.Kind is TileKind.Door or TileKind.Doorway, out _)
            ?? NearestTile(gx, gz, radius, 11, t => t.Zone == (byte)kind, out _));

    /// <summary>
    /// The nearest tile that matches in the nearest cells that can hold one (a cheap test of the cell first, for what
    /// is too rare for a tile scan to reach): the first such cell outward, ring by ring, that really has one.
    /// </summary>
    private Hit CellThenTile(int gx, int gz, int radius, int level, Func<int, int, bool> cell, Func<Tile, bool> match)
    {
        int mx0 = WorldLayout.MacroOf(gx), mz0 = WorldLayout.MacroOf(gz), rings = radius / WorldLayout.MacroSize + 1, tried = 0;
        for (int r = 0; r <= rings && tried < 64; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    int mx = mx0 + dx, mz = mz0 + dz;
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || layout.LevelAt(mx, mz) != level || !cell(mx, mz)) continue;
                    tried++;
                    for (int i = 0; i < WorldLayout.MacroSize * WorldLayout.MacroSize; i++)
                    {
                        int x = mx * WorldLayout.MacroSize + i % WorldLayout.MacroSize, z = mz * WorldLayout.MacroSize + i / WorldLayout.MacroSize;
                        if (layout.TileAt(x, z) is var t && t.Level == level && match(t)) return new Hit { X = x, Z = z };
                    }
                }
        return null;
    }

    private static Hit At((int X, int Z)? found) => found is { } f ? new Hit { X = f.X, Z = f.Z } : null;

    private static long Sq(long dx, long dz) => dx * dx + dz * dz;

    private static (int X, int Z)? Closest(int gx, int gz, int radius, IEnumerable<(int X, int Z)> points)
    {
        (int X, int Z)? best = null;
        long bestD = (long)radius * radius;
        foreach (var p in points)
        {
            long d = Sq(p.X - gx, p.Z - gz);
            if (d <= bestD) (best, bestD) = (p, d);
        }
        return best;
    }

    private static string LevelName(int level) => level is WorldLayout.TheEnd or WorldLayout.Hub
        ? "The " + WorldLayout.DisplayNumber(level) : "Level " + WorldLayout.DisplayNumber(level);

    /// <summary>
    /// The nearest of the places a lattice of plan squares (<paramref name="pitch"/> blocks apart, the position in square
    /// i0, j0) holds, searching ring by ring outward and stopping once no farther ring can hold a nearer one: planning a
    /// square can be slow (a Level 37 block), and most kinds are found in the first rings.
    /// </summary>
    private static (int X, int Z)? RingNearest(int gx, int gz, int radius, int pitch, int i0, int j0, Func<int, int, IEnumerable<(int X, int Z)>> places)
    {
        int reach = radius / pitch + 1;
        (int X, int Z)? best = null;
        long bestD = (long)radius * radius;
        for (int r = 0; r <= reach; r++)
        {
            // (Two squares of slack: a place may stand a little outside its square, as a hill does)
            long near = (long)Math.Max(0, r - 2) * pitch;
            if (best != null && near * near > bestD) break;
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    foreach (var p in places(i0 + di, j0 + dj))
                    {
                        long d = Sq(p.X - gx, p.Z - gz);
                        if (d <= bestD) (best, bestD) = (p, d);
                    }
                }
        }
        return best;
    }

    private static IEnumerable<(int X, int Z)> One((int X, int Z)? p) => p is { } q ? new[] { q } : Array.Empty<(int X, int Z)>();

    private bool InLevel(int x, int z, int level) => layout.LevelAt(WorldLayout.MacroOf(x), WorldLayout.MacroOf(z)) == level;

    /// <summary>The middle of the nearest of The End's departments of a kind within the radius.</summary>
    private (int X, int Z)? EndDept(int gx, int gz, int radius, Func<int, int, bool> want)
    {
        var (di0, dj0) = layout.EndDeptOf(gx, gz);
        return RingNearest(gx, gz, radius, WorldLayout.EndDept, di0, dj0, (di, dj) =>
            One(layout.EndDeptCentre(di, dj) is var c && InLevel(c.X, c.Z, WorldLayout.TheEnd) && want(di, dj) ? c : null));
    }

    /// <summary>The middle of the nearest of Level 94's hills with something of a kind on it, within the radius.</summary>
    private (int X, int Z)? NearestHill(int gx, int gz, int radius, string top)
    {
        int hi0 = Hashing.FloorDiv(gx - layout.MotionOriginX, WorldLayout.HillPitch), hj0 = Hashing.FloorDiv(gz - layout.MotionOriginZ, WorldLayout.HillPitch);
        return RingNearest(gx, gz, radius, WorldLayout.HillPitch, hi0, hj0, (hi, hj) =>
            One(layout.CheatHillAt(hi, hj) is var hill && hill.Top == top && InLevel(hill.X, hill.Z, WorldLayout.Motion) ? (hill.X, hill.Z) : null));
    }

    /// <summary>The middle of the nearest of Level 37's rooms of a kind within the radius.</summary>
    private (int X, int Z)? NearestPoolRoom(int gx, int gz, int radius, string kind)
    {
        var (bi0, bj0) = layout.CheatPoolBlockOf(gx, gz);
        return RingNearest(gx, gz, radius, WorldLayout.PoolBlock, bi0, bj0, (bi, bj) =>
            // (A block outside the level is never planned: it is rim or another level)
            !InLevel(layout.PoolOriginX + bi * WorldLayout.PoolBlock + 48, layout.PoolOriginZ + bj * WorldLayout.PoolBlock + 48, WorldLayout.Poolrooms)
                ? Array.Empty<(int X, int Z)>()
                : layout.CheatPoolRooms(bi, bj).Where(room => room.Kind == kind && InLevel(room.X, room.Z, WorldLayout.Poolrooms)).Select(room => (room.X, room.Z)));
    }

    /// <summary>The middle of the nearest of Level 3999's blackout blocks (3999.1) within the radius.</summary>
    private (int X, int Z)? NearestBlackout(int gx, int gz, int radius)
    {
        var (bi0, bj0) = layout.L3999BlockOf(gx, gz);
        return RingNearest(gx, gz, radius, 128, bi0, bj0, (bi, bj) =>
            One(layout.L3999BlackoutBlock(bi, bj) && layout.L3999BlockCentre(bi, bj) is var c && InLevel(c.X, c.Z, WorldLayout.Level3999) ? c : null));
    }

    /// <summary>The car parks in front of Level 10's lone arcades within the radius.</summary>
    private IEnumerable<(int X, int Z)> Arcades(int gx, int gz, int radius) => ArcadeSites(gx, gz, radius).Select(site =>
    {
        var (fx, fz) = PierStep(site.Facing);
        return (site.X + 6 * fx, site.Z + 6 * fz);
    });

    /// <summary>Level 10's lone arcades whose squares lie within the radius.</summary>
    private IEnumerable<WorldLayout.L3999ArcadeSite> ArcadeSites(int gx, int gz, int radius)
    {
        const int lattice = 2048;
        int i0 = Hashing.FloorDiv(gx, lattice), j0 = Hashing.FloorDiv(gz, lattice), reach = radius / lattice + 1;
        for (int dj = -reach; dj <= reach; dj++)
            for (int di = -reach; di <= reach; di++)
            {
                var site = layout.L3999ArcadeAt(i0 + di, j0 + dj);
                if (site.Valid && layout.LevelAt(WorldLayout.MacroOf(site.X), WorldLayout.MacroOf(site.Z)) == 10) yield return site;
            }
    }

    /// <summary>Fills in where to stand (the nearest open floor to the place, if the finder did not choose); false if there is nowhere.</summary>
    public bool Resolve(Hit hit, int level)
    {
        hit.Stand ??= StandNear(hit.X, hit.Z, level);
        return hit.Stand != null;
    }

    /// <summary>The compass heading (0 north, 90 east) from one spot to another.</summary>
    public static int Heading(int fromX, int fromZ, int toX, int toZ) => (int)Math.Round((Math.Atan2(toX - fromX, fromZ - toZ) * 180 / Math.PI + 360) % 360) % 360;

    private bool Beside(int x, int z, Func<Tile, bool> anchor) =>
        anchor(layout.TileAt(x - 1, z)) || anchor(layout.TileAt(x + 1, z)) || anchor(layout.TileAt(x, z - 1)) || anchor(layout.TileAt(x, z + 1));

    // ================================ /backrooms nearest's targets ================================

    /// <summary>
    /// What <c>/backrooms nearest</c> looks for round you, in your own level, and how far by default. The searches that
    /// look at every tile (ways out, caches) build each cell they pass, so they reach less far.
    /// </summary>
    public static readonly (string Code, string Name, int Radius, int MaxRadius)[] Targets =
    {
        ("gate", "Gate", 1024, 4096),
        ("threshold", "Way out", 384, 768),
        ("cache", "Unopened cache", 384, 768),
        ("refuge", "Refuge", 2048, 4096),
        ("den", "Den", 2048, 4096),
        ("redroom", "Red Room", 4096, 8192),
        // (For photographs: Level !'s hallway, the radius blocks down your lane's course from the start room's hall door;
        // a Level Fun party room with guests, from its north-west corner)
        ("runhall", "Level ! hallway", 36, 600),
        ("funparty", "Fun party room", 256, 1024),
        // (The End's partition walls, layout version 5: in front of the nearest, looking at it; and the central hall's
        // north-west EXIT vestibule, looking into it)
        ("endwall", "End partition wall", 512, 2048),
        ("endexit", "End central EXIT", 16384, 16384),
        // (A Level 3999 food court, from its middle; Level 188's courtyard door, from the courtyard looking at it)
        ("foodcourt", "3999 food court", 512, 2048),
        ("courtdoor", "188 courtyard door", 4096, 4096),
        // (Layout version 5: Level 2's dead tram, from the rails three blocks ahead of it, looking back at its front; a
        // purpified thing in a Level 3 wall, from two blocks in front of it, looking at it)
        ("tram", "Level 2 dead tram", 384, 1024),
        ("purpified", "Level 3 purpified", 384, 1024),
        // (Down a Level 3 manhole: at the foot of the rungs, looking at them, to test the ladder; in the flooded tunnel in
        // worlds of layout versions 1-8, on the dry landing from 9)
        ("manhole", "Level 3 manhole ladder", 384, 1024),
        // (Layout version 5: a Level 10 field's shed, trough or fallen gate, from four blocks south of it; a Level 11
        // billboard, from the street in front of its building; an advertising pillar, from three blocks south-east of
        // it; Level 94's castle, from the radius blocks south of it, looking north at it on the horizon)
        ("fieldthing", "Level 10 field shed, trough or gate", 512, 2048),
        ("billboard", "Level 11 billboard", 384, 1024),
        ("adpillar", "Level 11 advertising pillar", 384, 1024),
        ("castle", "Level 94 castle on the horizon", 450, 2000),
        // (Layout version 5: a Level 5 lobby's front hall, from its axis looking at the desk and the grand staircases; a
        // guest-room door with 666 on its plaque, from across the corridor)
        ("fronthall", "Level 5 front hall", 2048, 4096),
        ("door666", "Level 5 door 666", 768, 1536),
        // (Level 4 where its carpet starts turning to hotel red, looking on toward the hotel)
        ("hotelturn", "Level 4 turning to hotel", 512, 2048),
        // (Layout version 5: a rock pillar on a Level 7 island, a camp's shelter of furniture and tar, a Level 6.1 vending
        // machine room from the hall in front of it, and blood-red glowcaps beside Level 8's road; from the nearest spot
        // to stand, with the heading that looks at it)
        ("seapillar", "Level 7 rock pillar", 512, 2048),
        ("shelter", "Level 7 shelter", 768, 2048),
        ("vendingroom", "Level 6.1 vending room", 96, 256),
        ("glowcaps", "Level 8 glowcaps", 384, 1024),
        // (Layout version 9: inside a room on Level 7's seabed with air under its roof, beside the hatch)
        ("sunkenroom", "Level 7 sunken room", 768, 4096),
        // (Layout version 5's Suburbs: a two-storey house, from the street in front of it looking at its porch and
        // windows; the foot of its stairs, looking up them; a street-name sign and a DOWNTOWN sign, from across the corner)
        ("l9house", "Level 9 two-storey house", 384, 1024),
        ("l9stairs", "Level 9 house stairs", 384, 1024),
        ("streetname", "Level 9 street sign", 256, 1024),
        ("citysign", "Level 9 DOWNTOWN sign", 768, 2048),
        // (Runs that turn corners and end, from a few blocks off with the heading that looks at it: Levels 2 and 3's wall
        // pipes in an inner corner and round an outer one, an overhead bundle ending with open space beyond, a Level 3999
        // unit's neon base strip in a corner, and the hopper head on Level 188's downpipe)
        ("pipecorner", "Level 2/3 wall pipes, inner corner", 256, 1024),
        ("pipewrap", "Level 2/3 wall pipes, outer corner", 256, 1024),
        ("pipeend", "Level 1/2/3 overhead pipes ending", 256, 1024),
        ("neoncorner", "3999 neon strip corner", 512, 2048),
        ("downpipe", "188 downpipe head", 4096, 4096),
        // (Layout version 6: a camp tent two blocks by two, from three blocks out in front of its door, looking back at it;
        // a sleeping bag two blocks long, from the nearest place to stand; in any level)
        ("tent", "Camp tent", 1024, 4096),
        ("sleepingbag", "Sleeping bag", 1024, 4096),
    };

    /// <summary>The targets that are part of play; the rest are camera spots for the screenshots, and the manhole test.</summary>
    public static readonly string[] GameplayTargets = { "gate", "threshold", "cache", "refuge", "den", "redroom" };

    /// <summary>
    /// The nearest of one of <c>/backrooms nearest</c>'s targets (<see cref="Targets"/>) in a level, within the
    /// radius; null if none, or if it cannot be looked for here (<see cref="Error"/> says why).
    /// </summary>
    public Hit Target(string code, int gx, int gz, int radius, int level, string name)
    {
        Error = null;
        Stopped = false;
        name ??= Targets.First(t => t.Code == code).Name;
        string detail = "";
        (int X, int Z)? found;
        Hit Fail(string error)
        {
            Error = error;
            return null;
        }
        switch (code)
        {
            case "gate":
                var gate = layout.NearestGate(gx, gz, level, radius);
                found = gate is { } g ? (g.X, g.Z) : null;
                if (gate != null) detail = $" to Level {WorldLayout.DisplayNumber(gate.Value.To)}";
                break;
            case "threshold": found = layout.NearestThreshold(gx, gz, level, radius); break;
            case "cache": found = layout.NearestCache(gx, gz, level, radius); break;
            case "refuge": found = layout.NearestRefuge(gx, gz, level, radius); break;
            case "den":
                found = NearestCell(gx, gz, radius, (mx, mz) => layout.LevelAt(mx, mz) == level && layout.DenAt(mx, mz) != DenKind.None);
                if (found is { } d) detail = $" ({layout.DenAt(WorldLayout.MacroOf(d.X), WorldLayout.MacroOf(d.Z))})";
                break;
            case "runhall":
                int lane = level == WorldLayout.RunLevel ? layout.RunLaneAt(gx, gz) : -1;
                if (lane < 0) return Fail("The hallway is in Level ! (/backrooms goto !)");
                WorldLayout.RunLane plan = layout.RunPlan(lane);
                var (hx, hz) = plan.LineAt(radius);
                var (ax, az) = plan.LineAt(radius + 4);
                found = layout.RunWorld(lane, hx, hz);
                // The way on down the hall, as a compass heading (0 north, 90 east)
                detail = $" ({radius} blocks down; looking on down it is heading {(Math.Atan2(ax - hx, hz - az) * 180 / Math.PI + 360) % 360:0})";
                break;
            case "funparty":
                if (level != WorldLayout.FunLevel) return Fail("Party rooms are in Level Fun");
                FunRoom party = null;
                long partyDistance = long.MaxValue;
                foreach (FunRoom room in layout.FunRoomsNear(gx, gz, radius))
                {
                    if (room.Kind != FunZone.Party || room.Guests == 0) continue;
                    long dx = (room.X0 + room.X1) / 2 - gx, dz = (room.Z0 + room.Z1) / 2 - gz;
                    if (dx * dx + dz * dz < partyDistance) (party, partyDistance) = (room, dx * dx + dz * dz);
                }
                found = party != null ? (party.X0, party.Z0) : null;
                if (party != null) detail = $" ({party.Guests} guests; from its north-west corner, heading 135 looks across it)";
                break;
            case "foodcourt":
                if (level != WorldLayout.Level3999) return Fail("Food courts are in Level 3999");
                var courts = layout.L3999UnitsNear(gx, gz, u => u.Kind == WorldLayout.L3999Kind.FoodCourt, radius);
                found = courts.Count > 0 ? courts[0] : null;
                break;
            case "courtdoor":
                if (level != WorldLayout.Level188) return Fail("The courtyard door is in Level 188");
                // Eight blocks out into the courtyard from the door, facing it (the door is in the west façade)
                found = (layout.L188BuildX0 + 24, layout.L188BuildZ0 + 19);
                detail = " (heading 270 looks at the door and its EXIT sign)";
                break;
            case "tram":
                if (level != 2) return Fail("The tramway is in Level 2");
                found = NearestTile(gx, gz, radius, level, t => t.Variant == Worldgen.Props.Tram && t.Stack == 0, out var tram);
                if (found is { } tf)
                {
                    var (fdx, fdz) = PierStep(tram.Pier);
                    found = (tf.X + 3 * fdx, tf.Z + 3 * fdz);
                    detail = $" (heading {PierHeading(tram.Pier, true)} looks back at it)";
                }
                break;
            case "tent":
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.CampTent && t.Stack == 0, out var tent);
                if (found is { } tentAt)
                {
                    // (The front-left part: the door is half a block to its right, out toward Pier)
                    var (tdx, tdz) = PierStep(tent.Pier);
                    found = (tentAt.X + 3 * tdx, tentAt.Z + 3 * tdz);
                    detail = $" (heading {PierHeading(tent.Pier, true)} looks back at its door)";
                }
                break;
            case "sleepingbag":
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Floor && t.Variant == Worldgen.Props.SleepingBag && t.Stack == 0, out _);
                if (found is { } bagAt && StandNear(bagAt.X, bagAt.Z, level) is { } bs)
                {
                    found = bs;
                    detail = $" (heading {(Math.Atan2(bagAt.X - bs.X, bs.Z - bagAt.Z) * 180 / Math.PI + 360) % 360:0} looks at its head, {bagAt.X - bs.X}, {bagAt.Z - bs.Z} away)";
                }
                break;
            case "purpified":
                if (level != 3) return Fail("Purpified things are in Level 3");
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Wall && t.Variant == Decor.Purpified, out var wall);
                if (found is { } pf)
                {
                    var (pdx, pdz) = PierStep(wall.Pier);
                    found = (pf.X + 2 * pdx, pf.Z + 2 * pdz);
                    detail = $" (heading {PierHeading(wall.Pier, true)} looks at it)";
                }
                break;
            case "manhole":
            {
                if (level != 3) return Fail("Manholes are in Level 3");
                if (layout.NearestManhole(gx, gz, radius) is not { } m) { found = null; break; }
                // Down in the shaft itself (WorldGenerator.BelowFloor), the rungs in front of you: walk forward to climb.
                // Layout versions 1-8: on the tunnel's clay floor (rel -5) in its knee-deep water, the rungs on the
                // shaft's north side; from 9, on the dry landing (rel -4) at the foot of the ladder, on the tile's Pier side
                int md = (int)Math.Sqrt((double)(m.X - gx) * (m.X - gx) + (double)(m.Z - gz) * (m.Z - gz));
                Tile shaft = layout.TileAt(m.X, m.Z);
                bool ladder = shaft.Zone != 0;
                int heading = ladder ? PierHeading(shaft.Pier, false) : 0;
                return new Hit
                {
                    X = m.X, Z = m.Z, Stand = (m.X, m.Z), FeetY = geometry.FloorFor(level) - (ladder ? 3 : 4) + 0.05,
                    Detail = $" (heading {heading} looks at the {(ladder ? "ladder" : "rungs")})",
                    Message = $"{name} (heading {heading} looks at the {(ladder ? "ladder" : "rungs")}), {md} blocks from where you were",
                };
            }
            case "fieldthing":
                if (level != 10) return Fail("That is in Level 10");
                found = NearestTile(gx, gz, radius, level, t => t.Variant is Worldgen.Props.WaterTrough or Worldgen.Props.FallenGate
                    || t.Kind == TileKind.Wall && t.Pattern == WallPattern.BarnGrey, out _);
                if (found is { } ff) found = (ff.X, ff.Z + 4);
                detail = " (heading 0 looks at it)";
                break;
            case "billboard":
                if (level != 11) return Fail("That is in Level 11");
                found = NearestTile(gx, gz, radius, level, t => t.Overhead == Worldgen.Props.Billboard, out _);
                if (found is { } bf)
                {
                    bool north = layout.CityLotFront(bf.X, bf.Z) == ArchPier.North;
                    found = (bf.X, bf.Z + (north ? -14 : 14));
                    detail = $" (on the roof; heading {(north ? 180 : 0)} looks back up at it)";
                }
                break;
            case "adpillar":
                if (level != 11) return Fail("That is in Level 11");
                found = NearestTile(gx, gz, radius, level, t => t.Variant == Worldgen.Props.AdPillar, out _);
                if (found is { } af) found = (af.X + 3, af.Z + 3);
                detail = " (heading 315 looks at it)";
                break;
            case "l9house":
            case "l9stairs":
                if (level != 9) return Fail("That is in Level 9");
                found = NearestTile(gx, gz, radius, level, t => t.Stair == 4 && t.Height != 0, out var top);
                if (found is { } stairTop)
                {
                    // The stairs climb away from the street: their foot is four back from the top, the street fifteen
                    var (cdx, cdz) = PierStep(top.Pier);
                    int back = code == "l9house" ? 16 : 4;
                    found = (stairTop.X - back * cdx, stairTop.Z - back * cdz);
                    detail = $" (heading {PierHeading(top.Pier, false)} looks {(back == 4 ? "up the stairs" : "at the house")})";
                }
                break;
            case "streetname":
            case "citysign":
                if (level != 9) return Fail("That is in Level 9");
                bool guide = code == "citysign";
                found = NearestTile(gx, gz, radius, level, t => t.Variant == (guide ? Worldgen.Props.CitySign : Worldgen.Props.SuburbSign), out var sign);
                if (found is { } nf)
                {
                    // Out in the junction, three blocks off: the guide sign's face is side-on to its arrow
                    bool sideways = guide && sign.Pier is ArchPier.East or ArchPier.West;
                    found = sideways ? (nf.X, nf.Z - 3) : guide ? (nf.X + 3, nf.Z) : (nf.X - 3, nf.Z + 3);
                    detail = $" (heading {(sideways ? 180 : guide ? 270 : 45)} looks at it)";
                }
                break;
            case "castle":
                if (level != WorldLayout.Motion) return Fail("The castle is in Level 94");
                found = (layout.MotionOriginX, layout.MotionOriginZ + radius);
                detail = " (heading 0 looks at it)";
                break;
            case "endwall":
            case "endexit":
                if (level != WorldLayout.TheEnd) return Fail("That is in The End (/backrooms goto end)");
                found = code == "endexit" ? NearestEndExitVestibule(out detail) : NearestEndPartition(gx, gz, radius, out detail);
                break;
            case "hotelturn":
            {
                if (level != 4) return Fail("That is in Level 4");
                found = NearestTile(gx, gz, radius, level, t => t.Kind == TileKind.Floor && t.Floor == FloorKind.HotelCarpet, out _);
                if (found is { } turn)
                {
                    var (ox, oz) = layout.Outward(turn.X, turn.Z);
                    detail = $" (heading {(Math.Atan2(ox, -oz) * 180 / Math.PI + 360) % 360:0} looks on toward the hotel)";
                }
                break;
            }
            case "fronthall":
            case "door666":
            {
                if (level != 5) return Fail("That is in Level 5");
                var view = code == "fronthall"
                    ? NearestSpot(gx, gz, radius, layout.FrontHallView)
                    : NearestSpot(gx, gz, radius, layout.Door666View);
                found = view is { } v ? (v.X, v.Z) : null;
                if (view is { } w) detail = $" (heading {PierHeading(w.Facing, false)} looks at it)";
                break;
            }
            case "pipecorner":
            case "pipewrap":
            case "pipeend":
            case "neoncorner":
            {
                if (code == "neoncorner" ? level != WorldLayout.Level3999 : code == "pipeend" ? level is not (1 or 2 or 3) : level is not (2 or 3))
                    return Fail(code == "neoncorner" ? "That is in Level 3999" : code == "pipeend" ? "That is in Levels 1, 2 and 3" : "That is in Levels 2 and 3");
                (int Dx, int Dz) toward = default;
                Func<Tile, int, int, bool> match = code switch
                {
                    "pipecorner" => (t, x, z) => t.Kind == TileKind.Floor && RunCorner(x, z, inner: true, out toward),
                    "pipewrap" => (t, x, z) => CarriesWallPipes(t) && RunCorner(x, z, inner: false, out toward),
                    "pipeend" => (t, x, z) => OverheadEnd(t, x, z, out toward),
                    _ => (t, x, z) => NeonCorner(t, x, z, out toward),
                };
                if (NearestTileAt(gx, gz, radius, level, match, out _) is not { } it) { found = null; break; }
                // Back from it the way it looks (three blocks, or as near as there is floor), looking at it
                (int X, int Z)? spot = null;
                for (int back = 3; back >= 1 && spot == null; back--)
                {
                    int sx = it.X - back * toward.Dx, sz = it.Z - back * toward.Dz;
                    if (layout.TileAt(sx, sz) is { Kind: TileKind.Floor or TileKind.Doorway } st && st.Level == level) spot = (sx, sz);
                }
                found = spot ?? StandNear(it.X, it.Z, level) ?? it;
                if (found is { } rf) detail = $" (heading {(Math.Atan2(it.X - rf.X, rf.Z - it.Z) * 180 / Math.PI + 360) % 360:0} looks at it, {it.X - rf.X}, {it.Z - rf.Z} away)";
                break;
            }
            case "downpipe":
                if (level != WorldLayout.Level188) return Fail("The downpipe is in Level 188");
                // On the courtyard's north façade (courtyard block 55, 17): from five blocks out, looking north and up
                found = (layout.L188BuildX0 + WorldLayout.L188PipeBx, layout.L188BuildZ0 + WorldLayout.L188PipeBz + 5);
                detail = " (heading 0 looks at it; its head is under the parapet, 21 blocks up)";
                break;
            case "sunkenroom":
            {
                if (level != 7) return Fail("Sunken rooms are in Level 7 (worlds from layout version 9)");
                if (NearestTile(gx, gz, radius, level, t => t.Zone == WorldLayout.L7ZoneBellHatch, out _) is not { } hatch)
                    return Fail($"No sunken room within {radius} blocks");
                // On the floor in the middle of the room, a tile in from the hatch, in the air under its roof
                Tile ht = layout.TileAt(hatch.X, hatch.Z);
                (int stepX, int stepZ) = ht.Pier switch { ArchPier.North => (0, -1), ArchPier.East => (1, 0), ArchPier.South => (0, 1), _ => (-1, 0) };
                int rx = hatch.X - stepX, rz = hatch.Z - stepZ;
                int far = (int)Math.Sqrt((double)(rx - gx) * (rx - gx) + (double)(rz - gz) * (rz - gz));
                return new Hit
                {
                    X = rx, Z = rz, Stand = (rx, rz), FeetY = geometry.FloorFor(7) - ht.Height + 4.05,
                    Detail = $", {ht.Height} deep",
                    Message = $"{name}, {ht.Height} deep, {far} blocks from where you were",
                };
            }
            case "seapillar":
            case "shelter":
            case "vendingroom":
            case "glowcaps":
            {
                int want = code switch { "vendingroom" => 6, "glowcaps" => 8, _ => 7 };
                if (level != want) return Fail($"That is in Level {(want == 6 ? "6.1 (/backrooms find snackrooms)" : want.ToString())}");
                Func<Tile, bool> match = code switch
                {
                    "seapillar" => t => t.Detail == WorldLayout.L7Pillar && t.Depth == 0,
                    "shelter" => t => t.Kind == TileKind.Floor && t.Detail == WorldLayout.L7TarUnder,
                    "vendingroom" => t => t.Zone == 1 && t.Kind == TileKind.Doorway && t.Detail == WorldLayout.SnackVendingFront,
                    _ => t => t.Variant is Worldgen.Props.GlowcapRed or Worldgen.Props.GlowcapMixed,
                };
                if (NearestTile(gx, gz, radius, level, match, out _) is not { } it) { found = null; break; }
                found = StandNear(it.X, it.Z, level) ?? it;
                if (found is { } sf) detail = $" (heading {(Math.Atan2(it.X - sf.X, sf.Z - it.Z) * 180 / Math.PI + 360) % 360:0} looks at it, {it.X - sf.X}, {it.Z - sf.Z} away)";
                break;
            }
            default:
                if (level != 0) return Fail("Red Rooms are only in Level 0");
                found = NearestCell(gx, gz, radius, layout.IsRedRoom);
                break;
        }
        return found is { } f ? new Hit { X = f.X, Z = f.Z, Detail = detail } : null;
    }

    /// <summary>
    /// A spot four blocks in front of the middle of the nearest partition wall of The End's (layout version 5), and the
    /// compass heading that looks at it.
    /// </summary>
    private (int X, int Z)? NearestEndPartition(int gx, int gz, int radius, out string detail)
    {
        detail = "";
        var (di0, dj0) = layout.EndDeptOf(gx, gz);
        for (int r = 0; r <= radius / WorldLayout.EndDept + 1; r++)
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Max(Math.Abs(di), Math.Abs(dj)) != r) continue;
                    for (int side = 0; side < 4; side++)
                    {
                        if (!layout.EndPartitionAt(di0 + di, dj0 + dj, side, out _)) continue;
                        var (cx, cz) = layout.EndDeptCentre(di0 + di, dj0 + dj);
                        // The wall stands on the department's inner edge, 25 or 26 blocks out from its middle
                        var (x, z, heading) = side switch { 0 => (cx - 22, cz, 270), 1 => (cx + 21, cz, 90), 2 => (cx, cz - 22, 0), _ => (cx, cz + 21, 180) };
                        detail = $" (heading {heading} looks at it)";
                        return (x, z);
                    }
                }
        return null;
    }

    /// <summary>A spot in front of the central hall's north-west EXIT vestibule of The End's, and the heading that looks into it.</summary>
    private (int X, int Z)? NearestEndExitVestibule(out string detail)
    {
        var (cx, cz) = layout.EndDeptCentre(0, 0);
        detail = " (heading 0 looks into the vestibule at the door)";
        // The door is at department-local (12, 10), facing south; stand five blocks in front of it
        return (cx - 32 + 12, cz - 32 + 15);
    }

    // ================================ Searches ================================

    /// <summary>The middle of the nearest cell that matches, searching outward ring by ring.</summary>
    public static (int X, int Z)? NearestCell(int gx, int gz, int radius, Func<int, int, bool> match)
    {
        int mx0 = WorldLayout.MacroOf(gx), mz0 = WorldLayout.MacroOf(gz), rings = radius / WorldLayout.MacroSize + 1;
        (int X, int Z)? best = null;
        long bestDistance = long.MaxValue;
        for (int r = 0; r <= rings && best == null; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || !match(mx0 + dx, mz0 + dz)) continue;
                    int x = (mx0 + dx) * WorldLayout.MacroSize + WorldLayout.MacroSize / 2, z = (mz0 + dz) * WorldLayout.MacroSize + WorldLayout.MacroSize / 2;
                    long distance = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                    if (distance < bestDistance && distance <= (long)radius * radius) (best, bestDistance) = ((x, z), distance);
                }
        return best;
    }

    /// <summary>The nearest tile of a level that matches, searching cell by cell outward, and the tile itself.</summary>
    public (int X, int Z)? NearestTile(int gx, int gz, int radius, int level, Func<Tile, bool> match, out Tile tile) =>
        NearestTileAt(gx, gz, radius, level, (t, x, z) => match(t), out tile);

    /// <summary>
    /// As <see cref="NearestTile"/>, the match also given the tile's position. Reaches at most <see cref="TileScanMaxRadius"/>
    /// blocks and stops after <see cref="TileScanMillis"/>, so a miss cannot stall the server for minutes.
    /// </summary>
    public (int X, int Z)? NearestTileAt(int gx, int gz, int radius, int level, Func<Tile, int, int, bool> match, out Tile tile)
    {
        tile = default;
        radius = Math.Min(radius, TileScanMaxRadius);
        long deadline = Environment.TickCount64 + TileScanMillis;
        int mx0 = WorldLayout.MacroOf(gx), mz0 = WorldLayout.MacroOf(gz), rings = radius / WorldLayout.MacroSize + 1;
        (int X, int Z)? best = null;
        long bestDistance = long.MaxValue;
        for (int r = 0; r <= rings && best == null; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || layout.LevelAt(mx0 + dx, mz0 + dz) != level) continue;
                    if (Environment.TickCount64 > deadline) { Stopped = true; return best; }
                    for (int i = 0; i < WorldLayout.MacroSize * WorldLayout.MacroSize; i++)
                    {
                        int x = (mx0 + dx) * WorldLayout.MacroSize + i % WorldLayout.MacroSize, z = (mz0 + dz) * WorldLayout.MacroSize + i / WorldLayout.MacroSize;
                        Tile t = layout.TileAt(x, z);
                        if (t.Level != level || !match(t, x, z)) continue;
                        long distance = (long)(x - gx) * (x - gx) + (long)(z - gz) * (z - gz);
                        if (distance < bestDistance && distance <= (long)radius * radius) (best, bestDistance, tile) = ((x, z), distance, t);
                    }
                }
        return best;
    }

    /// <summary>The nearest of the views that cells give (looking from the nearest cell outward, ring by ring), within the radius.</summary>
    public static (int X, int Z, ArchPier Facing)? NearestSpot(int gx, int gz, int radius, Func<int, int, (int X, int Z, ArchPier Facing)?> spot)
    {
        int mx0 = WorldLayout.MacroOf(gx), mz0 = WorldLayout.MacroOf(gz), rings = radius / WorldLayout.MacroSize + 1;
        (int X, int Z, ArchPier Facing)? best = null;
        long bestDistance = long.MaxValue;
        for (int r = 0; r <= rings && best == null; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r || spot(mx0 + dx, mz0 + dz) is not { } s) continue;
                    long distance = (long)(s.X - gx) * (s.X - gx) + (long)(s.Z - gz) * (s.Z - gz);
                    if (distance < bestDistance && distance <= (long)radius * radius) (best, bestDistance) = (s, distance);
                }
        return best;
    }

    /// <summary>
    /// The nearest open floor (or doorway) to a spot, within 8 blocks, in the same level; failing that within 16, and
    /// failing that the nearest within 16 even behind a locked door (a Level 5 den's heart can lie among locked rooms;
    /// this is a cheat, and whoever is put there can pry their way out).
    /// </summary>
    public (int X, int Z)? StandNear(int x, int z, int level) =>
        StandNear(x, z, level, 8, false) ?? StandNear(x, z, level, 16, false) ?? StandNear(x, z, level, 16, true);

    private (int X, int Z)? StandNear(int x, int z, int level, int radius, bool locked)
    {
        for (int r = 0; r <= radius; r++)
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;
                    Tile t = layout.TileAt(x + dx, z + dz);
                    if (t.Level == level && t.Kind is TileKind.Floor or TileKind.Doorway && (locked || !t.Sealed) && t.Stack == 0 && t.Stair == 0
                        && t.Under == 0 && !t.SupplyBox && (t.Kind == TileKind.Doorway || t.Variant == 0)) return (x + dx, z + dz);
                }
        return null;
    }

    private static readonly (int Dx, int Dz)[] Sides4 = { (0, -1), (1, 0), (0, 1), (-1, 0) };

    /// <summary>Whether a wall carries Levels 2 and 3's wall pipes (as WorldGenerator draws them).</summary>
    private static bool CarriesWallPipes(in Tile t) => t.Kind == TileKind.Wall && (t.Level == 2 && t.Pattern == WallPattern.Tunnel
        && t.Variant is Worldgen.Props.WallPipes or Worldgen.Props.WallRiser or Worldgen.Props.WallValve
        || t.Level == 3 && t.Variant == Worldgen.Props.WallPipes && t.Pattern != WallPattern.Stone);

    private static bool OpenAtPipes(in Tile t) => t.Kind is TileKind.Floor or TileKind.Doorway or TileKind.Pit or TileKind.Bars or TileKind.Water or TileKind.ArchDoor;

    /// <summary>
    /// An inner corner of piped walls (a floor with piped walls on two sides that meet, <paramref name="toward"/> the way
    /// into the corner), or an outer one (a piped wall open on two sides that meet, <paramref name="toward"/> the way from
    /// the open toward it).
    /// </summary>
    private bool RunCorner(int x, int z, bool inner, out (int Dx, int Dz) toward)
    {
        toward = default;
        for (int c = 0; c < 4; c++)
        {
            var (ax, az) = Sides4[c];
            var (bx, bz) = Sides4[(c + 1) & 3];
            Tile a = layout.TileAt(x + ax, z + az), b = layout.TileAt(x + bx, z + bz);
            bool hit = inner ? CarriesWallPipes(a) && CarriesWallPipes(b) && !OpenAtPipes(layout.TileAt(x + ax + bx, z + az + bz))
                : OpenAtPipes(a) && OpenAtPipes(b) && OpenAtPipes(layout.TileAt(x + ax + bx, z + az + bz));
            if (!hit) continue;
            toward = inner ? (ax + bx, az + bz) : (-(ax + bx), -(az + bz));
            return true;
        }
        return false;
    }

    /// <summary>An overhead bundle (Levels 1-3) whose next tile on is open with nothing overhead, <paramref name="toward"/> that way.</summary>
    private bool OverheadEnd(in Tile t, int x, int z, out (int Dx, int Dz) toward)
    {
        toward = default;
        bool alongX = t.Pipe is Pipes.RunX or Pipes.LeakX, alongZ = t.Pipe is Pipes.RunZ or Pipes.LeakZ;
        if (t.Kind != TileKind.Floor || !(alongX || alongZ) || t.Ceiling != CeilingKind.Tile) return false;
        for (int dir = -1; dir <= 1; dir += 2)
        {
            var (dx, dz) = alongX ? (dir, 0) : (0, dir);
            Tile n = layout.TileAt(x + dx, z + dz);
            if (n.Kind != TileKind.Floor || n.Pipe != Pipes.None || n.Beam || n.Grand != t.Grand || n.Low != t.Low) continue;
            toward = (dx, dz);
            return true;
        }
        return false;
    }

    /// <summary>A Level 3999 unit's corner where the neon base strip turns along the side wall (as WorldGenerator draws it).</summary>
    private bool NeonCorner(in Tile t, int x, int z, out (int Dx, int Dz) toward)
    {
        toward = default;
        if ((t.Roof & WorldLayout.L3999BaseBit) == 0 || t.Variant != 0) return false;
        var (fx, fz) = PierStep(t.Pier);
        Tile next = layout.TileAt(x + fx, z + fz);
        if ((next.Roof & WorldLayout.L3999BaseBit) == 0 || next.Variant != 0) return false;
        var (nx, nz) = PierStep(next.Pier);
        // The next one along faces away from a side wall beside this one
        if (layout.TileAt(x - nx, z - nz).Kind != TileKind.Wall || nx * fx + nz * fz != 0) return false;
        toward = (-fx - nx, -fz - nz);
        return true;
    }

    /// <summary>One block the way a tile faces.</summary>
    public static (int Dx, int Dz) PierStep(ArchPier pier) => pier switch
    {
        ArchPier.North => (0, -1),
        ArchPier.South => (0, 1),
        ArchPier.East => (1, 0),
        _ => (-1, 0),
    };

    /// <summary>The compass heading (0 north, 90 east) of the way a tile faces, or of the way back.</summary>
    public static int PierHeading(ArchPier pier, bool back)
    {
        int heading = pier switch { ArchPier.North => 0, ArchPier.East => 90, ArchPier.South => 180, _ => 270 };
        return back ? (heading + 180) % 360 : heading;
    }
}
