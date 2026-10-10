using System;
using System.Collections.Generic;
using Part = Backrooms.Worldgen.WorldLayout.L188Part;
using WState = Backrooms.Worldgen.WorldLayout.L188WindowState;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 188, "The Courtyard of Windows" (kept as level 20), laid out in WorldLayout.Level188.cs, from its own
/// floor (<see cref="WorldGeometry.FloorFor"/>). Every block of the building is worked out from its building-local position
/// (<see cref="WorldLayout.L188CellAt"/>) and its height: the storey (rel / 4) and the height within it (rel % 4, 0 the
/// slab). A slab block is both a storey's ceiling (its underside) and the floor of the storey above (its top), so a
/// downlight costs no extra block. The windows are drawn in the state the world gives them now
/// (<see cref="WorldLayout.L188StateAt"/>); Regions.L188System keeps them so afterwards.
///
/// Every block is looked up softly (<see cref="L188Block"/>): until the level's assets exist, what is missing is drawn as
/// concrete (structure) or left out (furniture), logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L188WindowStates = { "closed", "glow", "open", "lit", "figure", "beckon" };
    private static readonly string[] L188Scenes = { "l0", "l1", "l2", "l4", "l5", "l6", "l9", "l37", "l94", "hub", "fun", "end", "void" };
    private static readonly string[] L188WinParts = { "ll", "lr", "ul", "ur" };
    private static readonly string[] L188SlabKinds = { "corridor", "room", "lobby", "stair", "bath", "roof" };
    private static readonly string[] L188LightKinds = { "corridor", "room", "lobby", "stair", "roof" };
    private static readonly string[] L188DoorStates = { "closed", "open", "locked", "sealed" };
    private static readonly string[] L188Hosts = { "l0", "l1", "fun" };
    private const int SlabCorridor = 0, SlabRoom = 1, SlabLobby = 2, SlabStair = 3, SlabBath = 4, SlabRoof = 5;

    private int l188Nothing, l188Sky, l188Shaft, l188Moss, l188Deck, l188WallRoom, l188WallStair, l188Gravel, l188Drain, l188Bollard,
        l188Vent, l188RoundTable;
    private readonly int[] l188Paver = new int[3], l188Turf = new int[2], l188DeckRound = new int[4], l188Hatch = new int[4], l188Slab = new int[6];
    private readonly int[,] l188Light = new int[5, 3], l188Cladding = new int[3, 4], l188WallCorr = new int[2, 4], l188Lift = new int[3, 4];
    private readonly int[] l188Edging = new int[4], l188Sill = new int[4], l188Coping = new int[4], l188Feature = new int[4], l188ExitSign = new int[4],
        l188StairStep = new int[4], l188Downpipe = new int[4], l188Bench = new int[4];
    private readonly int[,,] l188Window = new int[6, 4, 4], l188Scene = new int[13, 4, 4], l188OuterWindow = new int[2, 4, 4],
        l188GuestDoor = new int[4, 2, 4], l188StairDoor = new int[2, 2, 4], l188FrontDoor = new int[2, 2, 4], l188Entry = new int[3, 4, 4];
    private readonly int[,] l188StairWindow = new int[4, 4], l188FireDoor = new int[2, 4], l188FloorSign = new int[6, 4], l188EntrySill = new int[3, 4];
    private readonly int[,,,] l188CourtDoor = new int[2, 2, 2, 4]; // state, leaf (l, r), part, side
    private readonly int[,,] l188Bed = new int[2, 2, 4]; // half (l, r), part (head, feet), side
    private readonly int[,] l188Headboard = new int[2, 4], l188Nightstand = new int[2, 4], l188Wardrobe = new int[2, 4],
        l188Reception = new int[2, 4];
    private readonly Dictionary<string, int[]> l188Faced = new();
    private readonly HashSet<string> l188Missing = new();

    /// <summary>A block of the level's, or <paramref name="fallback"/> if its asset is not there (logged once).</summary>
    private int L188Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l188Missing.Add(code) && l188Missing.Count <= 40) api.Logger.Warning("[backrooms] Level 188: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>Four facings of a block (north, east, south, west), looked up once by its code without the side.</summary>
    private int[] L188Sided(string code, int fallback = 0)
    {
        if (l188Faced.TryGetValue(code, out int[] ids)) return ids;
        ids = new int[4];
        for (int f = 0; f < 4; f++) ids[f] = L188Block($"{code}-{Sides[f]}", fallback);
        return l188Faced[code] = ids;
    }

    /// <summary>Looks up the level's blocks (called from the constructor).</summary>
    private void InitL188()
    {
        int wall = concreteId;
        l188Nothing = L188Block("l188-nothing", concreteId);
        l188Sky = L188Block("l188-sky", l188Nothing);
        l188Shaft = L188Block("l188-shaft", l188Nothing);
        string[] pavers = { "plain", "moss", "cracked" };
        for (int i = 0; i < 3; i++) l188Paver[i] = L188Block("l188-paver-" + pavers[i], floorIds[(int)FloorKind.Concrete]);
        l188Turf[0] = L188Block("l188-turf-a", BlockId("game:soil-medium-normal"));
        l188Turf[1] = L188Block("l188-turf-b", l188Turf[0]);
        l188Moss = L188Block("l188-mosstuft");
        l188Deck = L188Block("l188-deck", floorIds[(int)FloorKind.Wood]);
        string[] corners = { "ne", "se", "sw", "nw" };
        for (int i = 0; i < 4; i++)
        {
            l188DeckRound[i] = L188Block("l188-deck-round-" + corners[i], l188Deck);
        }
        string[] quarters = { "nw", "ne", "sw", "se" };
        for (int i = 0; i < 4; i++) l188Hatch[i] = L188Block("l188-hatch-closed-" + quarters[i], l188Deck);
        for (int i = 0; i < 6; i++) l188Slab[i] = L188Block("l188-slab-" + L188SlabKinds[i], wall);
        string[] lightStates = { "on", "off", "flicker" };
        for (int k = 0; k < 5; k++)
            for (int st = 0; st < 3; st++)
            {
                int slab = l188Slab[k == 4 ? SlabRoof : k];
                l188Light[k, st] = L188Block($"l188-downlight-{L188LightKinds[k]}-{lightStates[st]}", slab);
            }
        for (int k = 0; k < 5; k++) if (l188Light[k, 2] != l188Slab[k == 4 ? SlabRoof : k]) flickerIds.Add(l188Light[k, 2]);
        l188WallRoom = L188Block("l188-wall-room", wall);
        l188WallStair = L188Block("l188-wall-stair", wall);
        l188Gravel = L188Block("l188-roofgravel");
        l188Drain = L188Block("l188-drain");
        l188Bollard = L188Block("l188-bollard");
        l188Vent = L188Block("l188-ventstack");
        l188RoundTable = L188Block("l188-roundtable");
        string[] cladding = { "plain", "band", "streak" };
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            for (int i = 0; i < 3; i++) l188Cladding[i, f] = L188Block($"l188-cladding-{cladding[i]}-{side}", wall);
            l188WallCorr[0, f] = L188Block("l188-wall-corridor-plain-" + side, l188WallRoom);
            l188WallCorr[1, f] = L188Block("l188-wall-corridor-base-" + side, l188WallCorr[0, f]);
            l188Feature[f] = L188Block("l188-wall-room-feature-" + side, l188WallRoom);
            l188Edging[f] = L188Block("l188-edging-" + side);
            l188Sill[f] = L188Block("l188-sill-" + side, l188Cladding[0, f]);
            l188Coping[f] = L188Block("l188-coping-" + side, l188Cladding[0, f]);
            l188ExitSign[f] = L188Block("l188-exitsign-" + side);
            l188StairStep[f] = L188Block("l188-stair-" + side, stairIds[f]);
            l188Downpipe[f] = L188Block("l188-downpipe-" + side);
            l188Bench[f] = L188Block("l188-bench-" + side);
            for (int p = 0; p < 4; p++)
            {
                for (int s = 0; s < 6; s++) l188Window[s, p, f] = L188Block($"l188-window-{L188WindowStates[s]}-{L188WinParts[p]}-{side}", l188Cladding[0, f]);
                for (int s = 0; s < 13; s++) l188Scene[s, p, f] = L188Block($"l188-window-scene-{L188Scenes[s]}-{L188WinParts[p]}-{side}", l188Window[2, p, f]);
                l188StairWindow[p, f] = L188Block($"l188-stairwindow-{L188WinParts[p]}-{side}", l188Window[2, p, f]);
                l188OuterWindow[0, p, f] = L188Block($"l188-outerwindow-closed-{L188WinParts[p]}-{side}", l188WallRoom);
                l188OuterWindow[1, p, f] = L188Block($"l188-outerwindow-open-{L188WinParts[p]}-{side}", l188OuterWindow[0, p, f]);
                for (int h = 0; h < 3; h++) l188Entry[h, p, f] = L188Block($"l188-entrywindow-{L188Hosts[h]}-{L188WinParts[p]}-{side}");
            }
            for (int h = 0; h < 3; h++) l188EntrySill[h, f] = L188Block($"l188-entrysill-{L188Hosts[h]}-{side}", concreteId);
            string[] parts = { "lower", "upper" }, leaves = { "l", "r" };
            for (int part = 0; part < 2; part++)
            {
                for (int st = 0; st < 4; st++) l188GuestDoor[st, part, f] = L188Block($"l188-guestdoor-{L188DoorStates[st]}-{parts[part]}-{side}", officeDoorLowerId);
                for (int st = 0; st < 2; st++) l188StairDoor[st, part, f] = L188Block($"l188-stairdoor-{L188DoorStates[st]}-{parts[part]}-{side}", metalDoorLowerId);
                for (int lf = 0; lf < 2; lf++)
                {
                    l188FrontDoor[lf, part, f] = L188Block($"l188-frontdoor-{leaves[lf]}-{parts[part]}-{side}", l188WallRoom);
                    for (int st = 0; st < 2; st++)
                        l188CourtDoor[st, lf, part, f] = L188Block($"l188-courtyarddoor-{L188DoorStates[st]}-{leaves[lf]}-{parts[part]}-{side}", 0);
                    l188Bed[lf, part, f] = L188Block($"l188-bed-{leaves[lf]}-{(part == 0 ? "head" : "feet")}-{side}");
                }
                l188FireDoor[part, f] = L188Block($"l188-firedoor-{parts[part]}-{side}", metalDoorLowerId);
                l188Wardrobe[part, f] = L188Block($"l188-wardrobe-{parts[part]}-{side}");
            }
            for (int lf = 0; lf < 2; lf++)
            {
                l188Headboard[lf, f] = L188Block($"l188-headboard-{leaves[lf]}-{side}");
            }
            l188Nightstand[0, f] = L188Block("l188-nightstand-on-" + side);
            l188Nightstand[1, f] = L188Block("l188-nightstand-off-" + side, l188Nightstand[0, f]);
            l188Reception[0, f] = L188Block("l188-reception-straight-" + side);
            l188Reception[1, f] = L188Block("l188-reception-end-" + side, l188Reception[0, f]);
            string[] signs = { "1", "2", "3", "4", "5", "roof" };
            for (int i = 0; i < 6; i++) l188FloorSign[i, f] = L188Block($"l188-floorsign-{signs[i]}-{side}");
            for (int part = 0; part < 3; part++) l188Lift[part, f] = liftIds[0, part, 0, f];
        }
        // Looked up now, so the generator's threads only ever read the table
        foreach (string code in new[] { "suitcase", "toilet", "roomservicetray", "icemachine", "snackvending", "laundrycart", "acunit",
                     "l188-armchair", "l188-desk", "l188-minibar", "l188-shower", "l188-poddoor", "l188-sink", "l188-housekeepingcart", "l188-linenshelf",
                     "l188-keyrack", "l188-cerealdispenser-3", "l188-juicedispenser-3", "l188-loungechair" })
            L188Sided(code);
    }

    // ================= The column =================

    /// <summary>
    /// The block at <paramref name="rel"/> above the level's floor in a column of one of its tiles (0 for air); solid
    /// wherever nothing is.
    /// </summary>
    private int Level188Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        int bx = gx - layout.L188BuildX0, bz = gz - layout.L188BuildZ0;
        WorldLayout.L188Cell c = WorldLayout.L188CellAt(bx, bz);
        if (c.Part == Part.Void) return l188Nothing;
        if (rel >= WorldLayout.L188SkyRel) return l188Sky;
        if (rel < 0) return L188Below(bx, bz, rel);
        if (rel > WorldLayout.L188RoofRel) return L188Roof(c, bx, bz, rel);
        if (c.Part == Part.Court) return L188Court(t, bx, bz, rel);
        int s = rel / 4, r = rel % 4;
        ArchPier toward = WorldLayout.L188Toward(c.Wing);
        if (rel == WorldLayout.L188RoofRel)
        {
            // The roof slab, over everything but the courtyard; the façades' floor band
            if (c.Part == Part.Facade) return l188Cladding[1, Facing(toward)];
            if (c.Part == Part.OuterFacade) return l188WallRoom;
            if (c.Part == Part.Stair) return L188Stair(bx, bz, rel);
            return L188Slab(c, bx, bz, s);
        }
        switch (c.Part)
        {
            case Part.Facade: return L188Facade(c, bx, bz, s, r, toward);
            case Part.OuterFacade: return L188OuterFacade(c, bx, bz, s, r, toward);
            case Part.Stair: return L188Stair(bx, bz, rel);
            case Part.Partition:
                if (s == 0 && WorldLayout.L188IsLobby(bx, bz)) return r == 0 ? l188Slab[SlabLobby] : L188Lobby(bx, bz, r);
                // The two dead lifts, in the lift lobby's west wall (left leaf as seen from the lobby: the south one)
                if (bx == 71 && bz is 12 or 13 && r >= 1) return liftIds[0, r - 1, bz == 13 ? 0 : 1, Facing(ArchPier.East)];
                return L188Partition(c, r);
            case Part.WallIn:
            case Part.WallOut:
                return L188CorridorWall(c, bx, bz, s, r, toward);
        }
        if (r == 0) return L188Slab(c, bx, bz, s);
        switch (c.Part)
        {
            case Part.Room:
                return L188Furniture(c.Wing, c.K, false, c.U, c.V, s, r, gx, gz);
            case Part.OuterRoom:
                if (s == 0 && WorldLayout.L188IsLobby(bx, bz)) return L188Lobby(bx, bz, r);
                return L188Furniture(c.Wing, c.K, true, c.U, c.V, s, r, gx, gz);
            case Part.Suite:
                if (c.U >= 0) return L188Furniture(c.Wing, c.K, true, c.U, c.V, s, r, gx, gz);
                return L188SuiteCorner(bx, bz, r);
            case Part.Corridor:
                return L188Corridor(c, bx, bz, s, r, gx, gz);
            case Part.Lifts:
            case Part.Housekeeping:
            case Part.Linen:
                return L188Service(c, bx, bz, r);
        }
        return 0;
    }

    /// <summary>Under the floor: solid, but for the hatch's black shaft.</summary>
    private int L188Below(int bx, int bz, int rel)
    {
        if (bx >= 42 && bx <= 45 && bz >= 27 && bz <= 30)
        {
            if (WorldLayout.L188IsHatch(bx, bz)) return rel <= -WorldGeometry.L188BandDepth ? l188Shaft : 0;
            return l188Shaft;
        }
        return concreteId;
    }

    // ---- The courtyard ----

    private int L188Court(in Tile t, int bx, int bz, int rel)
    {
        bool hatch = WorldLayout.L188IsHatch(bx, bz), deck = WorldLayout.L188IsDeck(bx, bz);
        if (rel == 0)
        {
            if (hatch) return 0; // the hatch lies over the shaft
            if (t.Floor == FloorKind.L188Turf) return l188Turf[(bx < 44 ? 0 : 1) ^ (bz < 29 ? 0 : 1)];
            if (deck) return l188Paver[0];
            ulong h = Hashing.Hash(seed, bx, bz, 0x2030);
            double u = Hashing.Unit(h);
            return u < 0.05 ? l188Paver[2] : u < 0.25 ? l188Paver[1] : l188Paver[0];
        }
        if (rel == 1)
        {
            if (hatch) return l188Hatch[(bx == 43 ? 0 : 1) + (bz == 28 ? 0 : 2)];
            if (deck)
            {
                int sx = bx + 0.5 > 44 ? 1 : -1, sz = bz + 0.5 > 29 ? 1 : -1;
                if (!WorldLayout.L188IsDeck(bx + sx, bz) && !WorldLayout.L188IsDeck(bx, bz + sz))
                    return l188DeckRound[sx > 0 ? (sz < 0 ? 0 : 1) : (sz > 0 ? 2 : 3)];
                return l188Deck;
            }
            switch (t.Variant)
            {
                case Props.L188Bench: return l188Bench[Facing(t.Pier)];
                case Props.L188Bollard: return l188Bollard;
                case Props.L188Drain: return l188Drain;
                case Props.L188MossTuft: return l188Moss;
            }
            if (t.Floor == FloorKind.L188Turf)
            {
                // Timber edging where the lawn meets the paving
                foreach (var (dx, dz, p) in new[] { (0, -1, ArchPier.North), (1, 0, ArchPier.East), (0, 1, ArchPier.South), (-1, 0, ArchPier.West) })
                {
                    int nx = bx + dx, nz = bz + dz;
                    if (!WorldLayout.L188IsLawn(nx, nz) && !WorldLayout.L188IsDeck(nx, nz)) return l188Edging[Facing(p)];
                }
            }
            return 0;
        }
        // The downpipe on the north façade, from the gutter to the drain
        if (bx == WorldLayout.L188PipeBx && bz == WorldLayout.L188PipeBz && rel <= WorldLayout.L188RoofRel) return l188Downpipe[Facing(ArchPier.South)];
        return 0;
    }

    // ---- Façades ----

    /// <summary>A window part: lower-left, lower-right, upper-left, upper-right as seen from its front.</summary>
    private static int L188Part(bool upper, bool left) => (upper ? 2 : 0) + (left ? 0 : 1);

    private int L188Facade(in WorldLayout.L188Cell c, int bx, int bz, int s, int r, ArchPier toward)
    {
        int f = Facing(toward);
        if (r == 0) return l188Cladding[1, f];
        int wi = WorldLayout.L188WindowAt(bx, bz);
        if (wi < 0)
            return Hashing.Unit(Hashing.Hash(seed, bx * 8 + r, bz * 8 + s, 0x2031)) < 0.06 ? l188Cladding[2, f] : l188Cladding[0, f];
        bool left = WorldLayout.L188IsLeft(c.U, toward);
        if (wi == WorldLayout.L188StairWindow)
        {
            if (s == 0)
            {
                // The courtyard's one door
                if (r == 3) return l188Cladding[0, f];
                int door = l188CourtDoor[0, left ? 0 : 1, r - 1, f];
                return door != 0 ? door : (r == 1 ? 0 : 0);
            }
            if (r == 1) return l188Sill[f];
            return l188StairWindow[L188Part(r == 3, left), f];
        }
        if (r == 1) return l188Sill[f];
        int part = L188Part(r == 3, left);
        WState state = layout.L188StateAt(wi, s, L188Hours, L188Day);
        if (state == WState.Scene) return l188Scene[Array.IndexOf(L188Scenes, WorldLayout.L188SceneOf(layout.L188LinkLevel(wi))), part, f];
        return l188Window[(int)state, part, f];
    }

    /// <summary>The in-game hour and day the windows are drawn for (the system keeps them in step afterwards).</summary>
    private double L188Hours => api.World.Calendar?.TotalHours ?? 0;
    private long L188Day => (long)Math.Floor(api.World.Calendar?.TotalDays ?? 0);

    private int L188OuterFacade(in WorldLayout.L188Cell c, int bx, int bz, int s, int r, ArchPier toward)
    {
        if (s == 0 && WorldLayout.L188IsFrontDoor(bx, bz))
        {
            if (r is 1 or 2) return l188FrontDoor[bx == 44 ? 0 : 1, r - 1, Facing(ArchPier.North)];
            return l188WallRoom;
        }
        if (r < 2 || c.U is not (1 or 2)) return l188WallRoom;
        // Windows onto nothing, for the outer rooms (and the suites' room ends); not in the corner squares
        bool room = c.Wing is 0 or 2 ? c.A is >= 7 and <= 80 : c.A is >= 7 and <= 50;
        if (!room || s == 0 && c.Wing == 2 && WorldLayout.L188IsLobby(bx, bz - 1)) return l188WallRoom;
        int open = Hashing.Unit(Hashing.Hash(seed, c.Wing * 128 + (c.A - c.U) , s, 0x2032)) < 0.3 ? 1 : 0;
        return l188OuterWindow[open, L188Part(r == 3, WorldLayout.L188IsLeft(c.U, toward)), Facing(toward)];
    }

    // ---- Walls ----

    private int L188Partition(in WorldLayout.L188Cell c, int r)
    {
        if (r == 0) return l188WallRoom;
        // The headboard wall: the face toward the room whose beds' heads are against it
        bool inner = c.D <= 5;
        bool roomNext = inner ? c.Wing is 0 or 2 ? c.A is >= 16 and <= 66 : c.A is >= 21 and <= 36 || c.Wing == 1 && c.A == 16
            : c.Wing is 0 or 2 ? c.A is >= 11 and <= 76 : c.A is >= 6 and <= 46;
        if (!roomNext) return l188WallRoom;
        ArchPier dirU = c.Wing is 0 or 2 ? ArchPier.East : ArchPier.South;
        return l188Feature[Facing(dirU)];
    }

    private int L188CorridorWall(in WorldLayout.L188Cell c, int bx, int bz, int s, int r, ArchPier toward)
    {
        ArchPier corridor = c.Part == Part.WallIn ? Opposite(toward) : toward;
        int f = Facing(corridor);
        int plain = r == 1 ? l188WallCorr[1, f] : l188WallCorr[0, f];
        if (WorldLayout.L188IsServiceOpening(bx, bz) || s == 0 && WorldLayout.L188IsLobbyOpening(bx, bz))
            return r == 0 ? l188Slab[SlabCorridor] : 0;
        if (r == 0) return l188WallRoom;
        if (WorldLayout.L188IsStairDoor(bx, bz))
            return r is 1 or 2 ? l188StairDoor[0, r - 1, Facing(ArchPier.West)] : plain;
        int fire = WorldLayout.L188FireDoorAt(bx, bz);
        if (fire > 0) return fire == s && r is 1 or 2 ? l188FireDoor[r - 1, f] : plain;
        if (!WorldLayout.L188IsRoomDoor(c) || r == 3) return plain;
        bool outer = c.Part == Part.WallOut;
        if (outer && s == 0 && c.Wing == 2 && c.A is >= 12 and <= 75) return plain; // the lobby has no doors
        int k = outer ? (c.Wing is 0 or 2 && c.A >= 77 ? 14 : (c.A - 7) / 5) : (c.A - 17) / 5;
        int state = 0;
        if (!outer && s == 0 && layout.L188LinkLevel(WorldLayout.L188WindowIndex(c.Wing, k)) >= 0) state = 3;
        else if (layout.L188IsLocked(c.Wing, k, outer, s)) state = 2;
        return l188GuestDoor[state, r - 1, f];
    }

    // ---- Slabs and lights ----

    /// <summary>
    /// The slab at storey <paramref name="s"/>'s floor: its top is that storey's floor, its underside the ceiling of the
    /// storey below (with a downlight where the storey below has one).
    /// </summary>
    private int L188Slab(in WorldLayout.L188Cell c, int bx, int bz, int s)
    {
        bool roof = s >= WorldLayout.L188Storeys;
        int kind = roof ? SlabRoof : c.Part switch
        {
            Part.Corridor or Part.WallIn or Part.WallOut or Part.Lifts or Part.Housekeeping or Part.Linen => SlabCorridor,
            Part.Stair => SlabStair,
            _ when s == 0 && WorldLayout.L188IsLobby(bx, bz) => SlabLobby,
            Part.Room or Part.OuterRoom or Part.Suite when c.U is 0 or 1 && c.V is 3 or 4 => SlabBath,
            _ => SlabRoom,
        };
        if (s == 0) return l188Slab[kind];
        // A light in the ceiling of the storey below?
        int below = s - 1;
        int light = -1, state = 1; // state: on, off, flicker
        ulong h = Hashing.Hash(seed, bx, bz * 8 + below, 0x2033);
        double u = Hashing.Unit(h);
        switch (c.Part)
        {
            case Part.Corridor:
                if (c.D == 8 && ((c.A % 4) + 4) % 4 == 0) { light = 0; state = u < 0.80 ? 0 : u < 0.97 ? 1 : 2; }
                break;
            case Part.Room or Part.OuterRoom or Part.Suite:
                if (below == 0 && WorldLayout.L188IsLobby(bx, bz))
                {
                    if (bz == 54 && bx % 3 == 0) { light = 2; state = u < 0.85 ? 0 : 2; }
                }
                else if (c.U == 1 && c.V == 2) { light = 1; state = 1; }
                break;
            case Part.Lifts or Part.Housekeeping or Part.Linen:
                if (bx is 13 or 74 && bz is 13 or 44) { light = 0; state = u < 0.7 ? 0 : 2; }
                break;
        }
        if (light < 0) return roof ? l188Slab[SlabRoof] : l188Slab[kind];
        // The light's top is the floor above it
        int top = roof ? 4 : kind switch { SlabCorridor => 0, SlabLobby => 2, SlabStair => 3, _ => 1 };
        return l188Light[top, state];
    }

    // ---- The stair ----

    /// <summary>
    /// The scissor stair (X 11-15, Z 11-20): flight A (X 11-12) climbs north for storeys 0, 2 and 4, flight B (X 14-15)
    /// south for 1 and 3, four steps a storey, round a core wall (X 13); landings at both ends at every storey.
    /// </summary>
    private int L188Stair(int bx, int bz, int rel)
    {
        bool flight = bz is >= 13 and <= 16;
        if (bx == 13 && flight) return l188WallStair;
        int s = rel / 4, r = rel % 4;
        if (!flight)
        {
            if (r == 0) return L188StairLanding(bx, bz, s);
            // Signs by the corridor doors: the floor number beside, a green EXIT over
            if (bx == 11 && (bz == 11 || bz == 18))
                return r == 3 ? l188ExitSign[Facing(ArchPier.East)] : 0;
            if (bx == 11 && (bz == 12 || bz == 19) && r == 2) return l188FloorSign[Math.Min(s, 4), Facing(ArchPier.East)];
            return 0;
        }
        if (rel == 0) return l188Slab[SlabStair];
        bool a = bx is 11 or 12;
        int sf = (rel - 1) / 4, k = rel - 4 * sf; // the flight's storey, and the step height within it (1-4)
        if (rel == WorldLayout.L188RoofRel && !a) return l188Slab[SlabStair]; // the floor over flight B's well, on the roof
        if (sf >= WorldLayout.L188Storeys) return 0;
        bool here = a ? sf % 2 == 0 : sf % 2 == 1;
        if (!here) return 0;
        int step = a ? 17 - bz : bz - 12;
        if (k == step) return l188StairStep[Facing(a ? ArchPier.North : ArchPier.South)];
        return k < step ? l188WallStair : 0;
    }

    private int L188StairLanding(int bx, int bz, int s)
    {
        if (s == 0) return l188Slab[SlabStair];
        if (bx == 13 && (bz == 11 || bz == 18)) return l188Light[3, 0];
        return l188Slab[SlabStair];
    }

    // ---- Rooms ----

    /// <summary>
    /// A guest room's furniture (the same plan for every room, turned to its wing): U along the wing, V from the window.
    /// The bed (a double, head against the slate-blue wall) and the nightstand by the window, the desk, minibar and
    /// wardrobe down the far side, the bathroom pod in the corner by the door, a path down the middle to the window.
    /// </summary>
    private int L188Furniture(int wing, int k, bool outer, int u, int v, int s, int r, int gx, int gz)
    {
        if (u < 0 || v < 0) return 0;
        ArchPier toward = WorldLayout.L188Toward(wing);
        ArchPier dirU = wing is 0 or 2 ? ArchPier.East : ArchPier.South;
        ArchPier dirV = outer ? toward : Opposite(toward);
        ArchPier backU = Opposite(dirU), backV = Opposite(dirV);
        var leftOfU = WorldLayout.L188LeftOf(dirU);
        var stepV = WorldLayout.L188Step(dirV);
        ulong h = Hashing.Hash(seed, wing * 64 + k * 2 + (outer ? 1 : 0), s, 0x2034);
        bool lamp;
        if (outer) lamp = Hashing.Unit(Hashing.Mix(h)) < 0.2;
        else
        {
            WState st = layout.L188StateAt(WorldLayout.L188WindowIndex(wing, k), s, L188Hours, L188Day);
            lamp = st is WState.Glow or WState.Lit or WState.Figure or WState.Beckon;
        }
        switch ((u, v))
        {
            case (0, 0): return r == 1 ? l188Nightstand[lamp ? 0 : 1, Facing(dirU)] : 0;
            case (1, 0): return r == 1 && Hashing.Unit(Hashing.Mix(h + 3)) < 0.35 ? L188Sided("suitcase")[Facing(backV)] : 0;
            case (3, 0):
                if (r != 1) return 0;
                if (Hashing.Unit(Hashing.Mix(h + 6)) < 1 / 12.0) return Hashing.Unit(Hashing.Mix(h + 9)) < 0.3 ? boxTornId : boxId;
                return L188Sided("l188-armchair")[Facing(backU)];
            case (0, 1) or (0, 2) or (1, 1) or (1, 2):
            {
                bool vIsLeft = (leftOfU.X, leftOfU.Z) == stepV;
                if (r == 1) return l188Bed[(v == 2) == vIsLeft ? 0 : 1, u, Facing(dirU)];
                // The headboard's halves as seen from in front of it (the other way round from the bed's)
                if (r == 2 && u == 0) return l188Headboard[(v == 2) == vIsLeft ? 1 : 0, Facing(dirU)];
                return 0;
            }
            case (3, 1): return r == 1 ? L188Sided("l188-desk")[Facing(backU)] : 0;
            case (3, 2): return r == 1 && Hashing.Unit(Hashing.Mix(h + 12)) < 0.6 ? L188Sided("l188-minibar")[Facing(backU)] : 0;
            case (3, 3): return r <= 2 ? l188Wardrobe[r - 1, Facing(backU)] : 0;
            case (0, 3): return r == 1 ? L188Sided("l188-shower")[Facing(backV)] : 0;
            // The pod's door, toward the path (its glass is on its right, toward the bed in rooms turned that way)
            case (1, 3): return r == 1 ? L188Sided("l188-poddoor")[Facing(dirU)] : 0;
            case (0, 4): return r == 1 ? L188Sided("toilet")[Facing(dirU)] : 0;
            case (1, 4): return r == 1 ? L188Sided("l188-sink")[Facing(dirU)] : 0;
        }
        return 0;
    }

    /// <summary>A corner suite's sitting room: a round table between two armchairs.</summary>
    private int L188SuiteCorner(int bx, int bz, int r)
    {
        if (r != 1) return 0;
        int cx = bx <= 5 ? 3 : 84, cz = bz <= 5 ? 3 : 54;
        if (bx == cx && bz == cz) return l188RoundTable;
        if (bz == cz && bx == cx - 1) return L188Sided("l188-armchair")[Facing(ArchPier.East)];
        if (bz == cz && bx == cx + 1) return L188Sided("l188-armchair")[Facing(ArchPier.West)];
        return 0;
    }

    /// <summary>The lobby (ground storey): the reception desk and its key rack, the breakfast tables, the lounge.</summary>
    private int L188Lobby(int bx, int bz, int r)
    {
        int south = Facing(ArchPier.South);
        if (bz == 53 && bx is >= 40 and <= 47) return r == 1 ? l188Reception[bx is 40 or 47 ? 1 : 0, south] : 0;
        if (bz == 52 && bx is >= 41 and <= 46 && r == 2) return L188Sided("l188-keyrack")[south];
        if (r != 1) return 0;
        if (bz == 52 && bx == 14) return L188Sided("l188-cerealdispenser-3")[south];
        if (bz == 52 && bx == 15) return L188Sided("l188-juicedispenser-3")[south];
        if (bz == 54 && bx is 18 or 23 or 28 or 33) return l188RoundTable;
        if (bz == 54 && bx is 57 or 65) return l188RoundTable;
        if (bz == 54 && bx is 56 or 64) return L188Sided("l188-loungechair")[Facing(ArchPier.East)];
        if (bz == 54 && bx is 58 or 66) return L188Sided("l188-loungechair")[Facing(ArchPier.West)];
        return 0;
    }

    // ---- The corridor and the service corners ----

    private int L188Corridor(in WorldLayout.L188Cell c, int bx, int bz, int s, int r, int gx, int gz)
    {
        // The green EXIT sign over this storey's fire door
        foreach (var (fx, fz, fs) in WorldLayout.L188FireDoors)
        {
            if (fs != s || r != 3) continue;
            int dx = bx - fx, dz = bz - fz;
            if (Math.Abs(dx) + Math.Abs(dz) == 1)
                return l188ExitSign[Facing(dx > 0 ? ArchPier.East : dx < 0 ? ArchPier.West : dz > 0 ? ArchPier.South : ArchPier.North)];
        }
        if (bx == 9 && bz is 11 or 18 && r == 3) return l188ExitSign[Facing(ArchPier.West)];
        if (r != 1) return 0;
        ArchPier toward = WorldLayout.L188Toward(c.Wing);
        ulong h = Hashing.Hash(seed, c.Wing, s, 0x2035);
        int cartAt = c.Wing is 0 or 2 ? 33 : 29, trayAt = c.Wing is 0 or 2 ? 46 : 26;
        if (c.D == 9 && c.A == cartAt && Hashing.Unit(h) < 0.5) return L188Sided("l188-housekeepingcart")[Facing(toward)];
        if (c.D == 7 && c.A == trayAt && Hashing.Unit(Hashing.Mix(h + 8)) < 0.25) return L188Sided("roomservicetray")[Facing(Opposite(toward))];
        return 0;
    }

    private int L188Service(in WorldLayout.L188Cell c, int bx, int bz, int r)
    {
        switch (c.Part)
        {
            case Part.Lifts:
                if (r == 1 && bx == 76 && bz == 11) return L188Sided("icemachine")[Facing(ArchPier.South)];
                if (r == 1 && bx == 76 && bz == 15) return L188Sided("snackvending")[Facing(ArchPier.North)];
                return 0;
            case Part.Housekeeping:
                if (r == 1 && bx == 72) return L188Sided("l188-linenshelf")[Facing(ArchPier.East)];
                if (r == 1 && bx == 74 && bz is 43 or 45) return L188Sided("laundrycart")[Facing(ArchPier.East)];
                return 0;
            default:
                if (r == 1 && bx == 15) return L188Sided("l188-linenshelf")[Facing(ArchPier.West)];
                return 0;
        }
    }

    // ---- The roof ----

    private int L188Roof(in WorldLayout.L188Cell c, int bx, int bz, int rel)
    {
        if (c.Part == Part.Court) return 0;
        // The stair's bulkhead, with its door onto the roof
        if (bx >= 10 && bx <= 16 && bz >= 10 && bz <= 21 && rel <= 25)
        {
            bool edge = bx is 10 or 16 || bz is 10 or 21;
            if (rel == 25) return l188Slab[SlabRoof];
            if (!edge) return 0;
            if (bx == 16 && bz == 11 && rel is 21 or 22) return l188StairDoor[0, rel - 21, Facing(ArchPier.East)];
            return l188WallStair;
        }
        if (rel != 21) return 0;
        ArchPier toward = WorldLayout.L188Toward(c.Wing);
        if (c.Part == Part.Facade) return l188Coping[Facing(toward)];
        if (c.Part == Part.OuterFacade) return l188Coping[Facing(Opposite(toward))];
        if (c.D == 8 && ((c.A % 12) + 12) % 12 == 6) return L188Sided("acunit")[Facing(toward)];
        if (c.D == 12 && ((c.A % 16) + 16) % 16 == 3) return l188Vent;
        return Hashing.Unit(Hashing.Hash(seed, bx, bz, 0x2036)) < 0.12 ? l188Gravel : 0;
    }

    // ================= Windows into 188 in other levels =================

    /// <summary>
    /// A window into 188 in another level's wall (<see cref="Unders.L188Entrance"/>): its sill at rel 1, its two halves
    /// at 2 and 3. -1 for every other height (the level draws its own wall).
    /// </summary>
    internal int L188EntranceBlock(in Tile t, int rel, out int fluid)
    {
        fluid = 0;
        if (t.Under != Unders.L188Entrance || rel is < 1 or > 3) return -1;
        int host = t.Detail & 15;
        int h = host == 3 ? 2 : Math.Min(host, 1);
        int f = Facing((ArchPier)((t.Detail >> 4) & 3));
        bool left = (t.Detail & 64) != 0;
        if (rel == 1) return l188EntrySill[h, f];
        int id = l188Entry[h, L188Part(rel == 3, left), f];
        return id != 0 ? id : -1;
    }
}
