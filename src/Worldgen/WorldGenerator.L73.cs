using Atp = Backrooms.Worldgen.WorldLayout.L73AtticPart;
using Layer = Backrooms.Worldgen.WorldLayout.L73Layer;
using Part = Backrooms.Worldgen.WorldLayout.L73Part;
using Room = Backrooms.Worldgen.WorldLayout.L73Room;
using Thing = Backrooms.Worldgen.WorldLayout.L73Thing;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 73, "The Redlands" (experimental, kept as level 21), laid out in WorldLayout.Level73.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>), which is the sea's surface. The island is crimson earth over basalt, black rock on
/// its outcrops and hilltops, ash sand on the beach and blood-red mud in the gullies, old bones strewn over it; the seabed is
/// basalt sand and gravel under still water. The Silver Castle is pale silver ashlar: curtain walls seven high with
/// battlements, towers ten, banners of a silver heart with ram's horns on black hung inside and out; the keep three storeys
/// under a flat roof with turrets and a chimney stack, and on the roof the attic under slate with its balcony. Inside,
/// carpet, damask, tiles and boards, the Level 5 hotel's furniture, iron sconces, a hearth of embers, the mahogany table
/// with a place set at every seat, the bathrooms' barrels of warm water, paintings of the Frontrooms, and red velvet
/// curtains over boarded windows. The keep's door is a pair of studded leaves that open only to banging
/// (Regions.L73System). The rim of the region is a cliff of basalt. This file is the level's own.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l73Earth, l73Rock, l73Ash, l73Mud, l73Silver, l73Basalt, l73Sand, l73Gravel, l73Ashlar, l73Carpet, l73Damask, l73TileFloor,
        l73Boards, l73Ember, l73Slate, l73Bath, l73WindowBoards, l73Note, l73Burnt, l73Crust, l73Bone;
    private readonly int[] l73Grass = new int[4];
    /// <summary>The keep's lined walls: [0 panelling (floor height), 1 damask above], by the face lined (north, east, south, west, 4 all round).</summary>
    private readonly int[,] l73Lined = new int[2, 5];
    private readonly int[] l73Sconce = new int[4], l73Banner = new int[4], l73Door = new int[6], l73AtticDoor = new int[4];
    private readonly int[,] l73Curtain = new int[3, 4], l73Table = new int[2, 4], l73Painting = new int[WorldLayout.L73Paintings, 4];
    // Round 3 (2026-11-01): fireplaces, canopies, rugs, floors and ceilings, beams, balustrades, hangings, plates and notes, the
    // kitchen's and the rooms' furniture; the Hound's thin bones, dead trees, boulders, the tracks and the darker path
    private int l73FloorBoards, l73TileCeil, l73Flags, l73PathFlags, l73Trodden, l73PotRack, l73Well, l73Barrel;
    private readonly int[,] l73Carcass = new int[2, 4];
    private readonly int[] l73Cart = new int[4], l73Larder = new int[4], l73Sacks = new int[4];
    private readonly int[,] l73Sheeted = new int[2, 4];
    private readonly int[] l73Lime = new int[5];
    private int l73HookMeat;
    private readonly int[] l73Mantel = new int[4], l73Beam = new int[2], l73StairRail = new int[2], l73Rail = new int[4], l73Chest = new int[4],
        l73Washstand = new int[4], l73Lectern = new int[4], l73Linen = new int[4], l73MegPlacard = new int[4], l73BoneJoint = new int[64],
        l73DeadWood = new int[3], l73Cornice = new int[5];
    private readonly int[,] l73Fire = new int[3, 4], l73Rug = new int[2, 9], l73Sampler = new int[2, 4], l73Plate = new int[13, 4],
        l73Notice = new int[4, 4], l73Worktable = new int[2, 4], l73DeadBranch = new int[2, 4], l73Boulder = new int[2, 4];
    private readonly int[,,] l73Canopy = new int[4, 2, 4], l73Tapestry = new int[2, 4, 4];

    /// <summary>The plates' and notes' codes, in step with gen_73_interior.py (and WorldLayout's L73Plate* and L73Notice*).</summary>
    private static readonly string[] L73PlateCodes = { "i", "ii", "iii", "iv", "v", "vi", "bath", "kitchen", "library", "pantry", "solar", "dining", "laundry" },
        L73NoticeCodes = { "outside", "attic", "bang", "count" };

    /// <summary>How high the cliff round the sea rises above it.</summary>
    private const int L73RimTop = 16;

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL73()
    {
        l73Basalt = GameId("game:rock-basalt", "game:rock-granite");
        l73Earth = Id("l73-redearth");
        l73Rock = Id("l73-blackrock");
        l73Ash = Id("l73-ash-sand");
        l73Mud = Id("l73-bloodmud");
        l73Burnt = Id("l73-burnt");
        l73Crust = Id("l73-crust");
        l73Bone = Id("l73-bone");
        string[] lined = { "north", "east", "south", "west", "all" };
        for (int f = 0; f < 5; f++)
        {
            l73Lined[0, f] = Id("l73-wainscot-" + lined[f]);
            l73Lined[1, f] = Id("l73-damask-" + lined[f]);
        }
        l73Grass[1] = Id("l73-deadgrass-short");
        l73Grass[2] = Id("l73-deadgrass-mid");
        l73Grass[3] = Id("l73-deadgrass-tall");
        l73Silver = Id("l73-silverwall");
        l73Slate = Id("l73-slate");
        l73Bath = Id("l73-bath");
        l73WindowBoards = Id("l73-boards");
        l73Note = Id("loosenote-refuge");
        string[] curtainParts = { "top", "mid", "low" }, doorParts = { "lb", "rb", "lm", "rm", "lt", "rt" };
        for (int f = 0; f < 4; f++)
        {
            l73Sconce[f] = Id("l73-sconce-" + Sides[f]);
            l73Banner[f] = Id("l73-banner-" + Sides[f]);
            for (int p = 0; p < 3; p++) l73Curtain[p, f] = Id($"l73-curtain-{curtainParts[p]}-{Sides[f]}");
            l73Table[0, f] = Id("l73-table-set-" + Sides[f]);
            l73Table[1, f] = Id("l73-table-bare-" + Sides[f]);
            for (int k = 0; k < WorldLayout.L73Paintings; k++) l73Painting[k, f] = Id($"l73-painting-{k + 1}-{Sides[f]}");
        }
        for (int p = 0; p < 6; p++) l73Door[p] = Id("l73-door-shut-" + doorParts[p]);
        InitL73Round3();
        string[] atticParts = { "lb", "rb", "lt", "rt" };
        for (int p = 0; p < 4; p++) l73AtticDoor[p] = Id("l73-atticdoor-" + atticParts[p]);
        l73Sand = GameId("game:sand-basalt", "game:sand-granite");
        l73Gravel = GameId("game:gravel-basalt", "game:gravel-granite");
        l73Ashlar = Id("hub-ashlar-worn");
        l73Carpet = BlockId("backrooms:hotelcarpet-maroon");
        l73Damask = BlockId("backrooms:hotelcarpet-damask");
        l73TileFloor = Id("l188-tile-bath");
        l73Boards = BlockId("game:planks-aged-ud");
        l73Ember = GameId("game:ember");
        floorIds[(int)FloorKind.L73Floor] = l73Earth;
        floorIds[(int)FloorKind.L73Rock] = l73Rock;
        floorIds[(int)FloorKind.L73Ash] = l73Ash;
        floorIds[(int)FloorKind.L73Mud] = l73Mud;
        floorIds[(int)FloorKind.L73Tor] = l73Rock;
        floorIds[(int)FloorKind.L73Burnt] = l73Burnt;
        floorIds[(int)FloorKind.L73Crust] = l73Crust;
        floorIds[(int)FloorKind.L73Seabed] = l73Sand;
        floorIds[(int)FloorKind.L73Gravel] = l73Gravel;
        floorIds[(int)FloorKind.L73Court] = l73Rock;
        floorIds[(int)FloorKind.L73Path] = l73PathFlags;
        floorIds[(int)FloorKind.L73Track] = l73Trodden;
        floorIds[(int)FloorKind.L73Carpet] = l73Carpet;
        floorIds[(int)FloorKind.L73Boards] = l73Boards;
        floorIds[(int)FloorKind.L73Tile] = l73TileFloor;
        floorIds[(int)FloorKind.L73Damask] = l73Damask;
        // The ways in and out (WorldGenerator.L73.Links.cs)
        InitL73Links();
    }

    private void InitL73Round3()
    {
        string[] canopyParts = { "h0", "h1", "f0", "f1" }, cloths = { "red", "black" }, tapestries = { "hunt", "castle" },
            tparts = { "bl", "br", "tl", "tr" }, rugParts = { "c", "n", "e", "s", "w", "nw", "ne", "se", "sw" }, fires = { "logs", "cauldron", "spit" };
        l73FloorBoards = Id("l73-floorboards");
        l73TileCeil = Id("l73-tileceil");
        l73Flags = Id("l73-flags");
        l73PathFlags = Id("l73-pathflags");
        l73Trodden = Id("l73-trodden");
        l73PotRack = Id("l73-potrack");
        l73Well = Id("l73-well");
        l73Barrel = Id("l73-barrel");
        l73Beam[0] = Id("l73-beam-ns");
        l73Beam[1] = Id("l73-beam-ew");
        l73StairRail[0] = Id("l73-stairrail-east");
        l73StairRail[1] = Id("l73-stairrail-west");
        for (int p = 0; p < 3; p++) l73DeadWood[p] = Id("l73-deadwood-" + new[] { "root", "trunk", "top" }[p]);
        string[] lined = { "north", "east", "south", "west", "all" };
        for (int k = 0; k < 5; k++) l73Cornice[k] = Id("l73-cornice-" + lined[k]);
        for (int k = 0; k < 5; k++) l73Lime[k] = Id("l73-lime-" + lined[k]);
        l73HookMeat = Id("l73-hookmeat");
        for (int m = 0; m < 64; m++) l73BoneJoint[m] = Id("l73-bonejoint-c" + m);
        for (int k = 0; k < 2; k++)
            for (int p = 0; p < 9; p++) l73Rug[k, p] = Id($"l73-rug-{(k == 0 ? "red" : "blue")}-{rugParts[p]}");
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            l73Mantel[f] = Id("l73-mantel-" + side);
            l73Rail[f] = Id("l73-rail-" + side);
            l73Chest[f] = Id("l73-chest-" + side);
            l73Washstand[f] = Id("l73-washstand-" + side);
            l73Lectern[f] = Id("l73-lectern-" + side);
            l73Linen[f] = Id("l73-linen-" + side);
            l73MegPlacard[f] = Id("l73-megplacard-" + side);
            l73Cart[f] = Id("l73-cart-" + side);
            l73Larder[f] = Id("l73-larder-" + side);
            l73Sheeted[0, f] = Id("l73-sheeted-a-" + side);
            l73Sheeted[1, f] = Id("l73-sheeted-b-" + side);
            l73Sacks[f] = Id("l73-sacks-" + side);
            l73Carcass[0, f] = Id("l73-carcass-a-" + side);
            l73Carcass[1, f] = Id("l73-carcass-b-" + side);
            for (int k = 0; k < 3; k++) l73Fire[k, f] = Id($"l73-fire-{fires[k]}-{side}");
            for (int k = 0; k < 2; k++)
            {
                l73Sampler[k, f] = Id($"l73-sampler-{(k == 0 ? "l" : "r")}-{side}");
                l73Worktable[k, f] = Id($"l73-worktable-{(k == 0 ? "pots" : "meat")}-{side}");
                l73DeadBranch[k, f] = Id($"l73-deadbranch-{(k == 0 ? "a" : "b")}-{side}");
                l73Boulder[k, f] = Id($"l73-boulder-{(k == 0 ? "a" : "b")}-{side}");
                for (int p = 0; p < 4; p++) l73Tapestry[k, p, f] = Id($"l73-tapestry-{tapestries[k]}-{tparts[p]}-{side}");
            }
            for (int k = 0; k < L73PlateCodes.Length; k++) l73Plate[k, f] = Id($"l73-plate-{L73PlateCodes[k]}-{side}");
            for (int k = 0; k < L73NoticeCodes.Length; k++) l73Notice[k, f] = Id($"l73-notice-{L73NoticeCodes[k]}-{side}");
            for (int p = 0; p < 4; p++)
                for (int c = 0; c < 2; c++) l73Canopy[p, c, f] = Id($"l73-canopy-{canopyParts[p]}-{cloths[c]}-{side}");
        }
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above the sea's surface.</summary>
    private int Level73Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        // The rim: a cliff of basalt round the sea
        if (t.Zone == WorldLayout.L73RimZone) return rel < -12 ? concreteId : rel <= L73RimTop ? l73Basalt : 0;
        if (t.Zone is WorldLayout.L73Court or WorldLayout.L73Keep or WorldLayout.L73Walls) return L73CastleBlock(gx, gz, rel);

        // The island and the sea
        int g = t.Depth > 0 ? -t.Depth : t.Height;
        // The Great Hound's bones (sunk into the ground where it rises): the skull solid, the rest thin bones joined up
        if (t.Sealed && t.Zone == WorldLayout.L73Land && rel > 0 && layout.L73HoundBoneMask(gx, gz, rel) is int bone and >= 0)
            return bone == 64 ? l73Bone : l73BoneJoint[bone];
        if (rel > g)
        {
            // A dead tree (its trunk on this column, or a branch reaching over it from the trunk beside), a boulder (round 3)
            if (rel > g && t.Zone == WorldLayout.L73Land && L73IslandThing(t, gx, gz, g, rel) is int thing and > 0) return thing;
            if (rel <= 0) fluid = waterId;
            if (rel == g + 1 && t.Variant != 0) return PropBlock(t);
            if (rel == g + 1 && t.Detail == 1) return l73Note;
            // Dead grass on the fields
            if (rel == g + 1 && g > 0 && !t.Sealed && layout.L73GrassAt(gx, gz, t.Floor) is int grass and > 0) return l73Grass[grass];
            // The banners on the castle's outer walls hang over the ground just outside them
            if (g == WorldLayout.L73Plateau && WorldLayout.L73BannerAt(gx - layout.L73CastleX0, gz - layout.L73CastleZ0) is { } banner
                && rel == WorldLayout.L73Plateau + banner.Top)
                return l73Banner[Facing(banner.Facing)];
            // The M.E.G.'s plate on the gatehouse, beside the gate, facing the run
            if (g == WorldLayout.L73Plateau && rel == WorldLayout.L73Plateau + 2 && gx - layout.L73CastleX0 == 21 && gz - layout.L73CastleZ0 == WorldLayout.L73CastleD)
                return l73MegPlacard[Facing(ArchPier.South)];
            return 0;
        }
        if (rel < System.Math.Min(g - 4, -8)) return concreteId; // (the ground below, as vanilla laid it)
        if (rel == g) return floorIds[(int)t.Floor] is int top and not 0 ? top : l73Earth;
        // A tor is black rock right down into the ground
        if (t.Floor == FloorKind.L73Tor && rel > g - 10) return l73Rock;
        if (rel >= g - 2)
            return t.Floor switch
            {
                FloorKind.L73Ash => l73Ash,
                FloorKind.L73Seabed => l73Sand,
                FloorKind.L73Gravel => l73Gravel,
                FloorKind.L73Rock => l73Rock,
                _ => rel == g - 1 ? l73Earth : l73Basalt,
            };
        return l73Basalt;
    }

    /// <summary>
    /// A dead tree's or a boulder's block at a land column above its ground (0 none): the trunk (its root, its length, its
    /// forked top) on the trunk's column, a branch on a column beside it reaching out from it, at the branch's height over
    /// the trunk's ground; a boulder of one or two blocks.
    /// </summary>
    private int L73IslandThing(in Tile t, int gx, int gz, int g, int rel)
    {
        if (rel > g + 9) return 0; // (no tree stands higher; and this is asked for every block of a column)
        if (t.Sealed && layout.L73BoulderAt(gx, gz) is { } boulder)
        {
            int b = rel - g;
            if (b > boulder.Height) return 0;
            return b < boulder.Height ? l73Rock : l73Boulder[boulder.Kind, Facing(boulder.Turn)];
        }
        if (layout.L73TreeNear(gx, gz) is not { } tree) return 0;
        int tg = tree.X == gx && tree.Z == gz ? g : layout.L73Ground(tree.X, tree.Z, out _);
        int up = rel - tg;
        if (tree.X == gx && tree.Z == gz)
            return up == 1 ? l73DeadWood[0] : up > 1 && up < tree.Height ? l73DeadWood[1] : up == tree.Height ? l73DeadWood[2] : 0;
        int dx = gx - tree.X, dz = gz - tree.Z;
        if (System.Math.Abs(dx) + System.Math.Abs(dz) != 1 || rel <= g + 1) return 0;
        int side = dz < 0 ? 0 : dx > 0 ? 1 : dz > 0 ? 2 : 3;
        var (level, kind) = WorldLayout.L73Branch(tree.Height, tree.H, side);
        return level > 0 && up == level ? l73DeadBranch[kind, side] : 0;
    }

    /// <summary>The Silver Castle, from its castle-local position and the height above its floor (the summit plateau).</summary>
    private int L73CastleBlock(int gx, int gz, int rel)
    {
        int u = gx - layout.L73CastleX0, v = gz - layout.L73CastleZ0;
        Part part = WorldLayout.L73CastleAt(u, v);
        int c = rel - WorldLayout.L73Plateau;
        if (c < 0 && c >= -WorldLayout.L73CellarDepth && part == Part.Keep)
            return L73CellarBlock(u - WorldLayout.L73KeepU0, v - WorldLayout.L73KeepV0, c);
        if (c < 0) return rel < -8 ? concreteId : l73Basalt;
        const int w = WorldLayout.L73CastleW, d = WorldLayout.L73CastleD;
        bool Merlon(int a, int b) => ((a + b) & 1) == 0;
        switch (part)
        {
            case Part.Court:
            case Part.Path:
                if (c == 0) return part == Part.Court ? (L73CourtWalk(u, v) ? l73Flags : l73Rock) : l73PathFlags;
                if (part == Part.Court && L73CourtThing(u, v, c) is int yard and > 0) return yard;
                // The M.E.G.'s plate beside the keep's door, the door that opens to banging
                if (c == 2 && v == WorldLayout.L73KeepV0 + WorldLayout.L73KeepD && u - WorldLayout.L73KeepU0 == 19) return l73MegPlacard[Facing(ArchPier.South)];
                // Buttresses against the keep's walls, between its windows, capped in slate
                if (L73Buttress(u, v) && c <= 12) return c <= 11 ? l73Silver : l73Slate;
                // A little slate canopy over the keep's door, pointed
                if (v == WorldLayout.L73KeepV0 + WorldLayout.L73KeepD && u - WorldLayout.L73KeepU0 is >= 16 and <= 19
                    && (c == 4 || c == 5 && u - WorldLayout.L73KeepU0 is 17 or 18))
                    return l73Slate;
                return WorldLayout.L73BannerAt(u, v) is { } banner && c == banner.Top ? l73Banner[Facing(banner.Facing)] : 0;
            case Part.Gate:
                // The gateway, four wide and four high, under the wall-walk
                if (c == 0) return l73PathFlags;
                if (c <= 4) return 0;
                if (c <= 7) return l73Silver;
                return c == 8 && v == d - 1 && Merlon(u, v) ? l73Silver : 0;
            case Part.Curtain:
                // The north door Coran opens, and the dark behind it (WorldGenerator.L73.Links.cs)
                if (L73PosternBlock(u, v, c) is int postern and >= 0) return postern;
                if (c <= 7) return l73Silver;
                return c == 8 && (u == 0 || v == 0 || u == w - 1 || v == d - 1) && Merlon(u, v) ? l73Silver : 0;
            case Part.Tower:
            {
                if (c <= 10) return l73Silver;
                int tu = u < 6 ? u : w - 1 - u, tv = v < 6 ? v : d - 1 - v;
                // A steep pointed slate roof from the eaves, tapering to a spire (the castle's gothic outline from afar)
                if (c == 11) return l73Slate;
                if (c <= 13 && tu is >= 1 and <= 4 && tv is >= 1 and <= 4) return l73Slate;
                return c <= 17 && tu is 2 or 3 && tv is 2 or 3 ? l73Slate : 0;
            }
            case Part.GateTower:
                if (c <= 10) return l73Silver;
                if (c == 11 && (u is 22 or 25 or 30 or 33 || v is d - 5 or d - 1)) return Merlon(u, v) ? l73Silver : 0;
                // A slate cap and a spire on each gate tower
                if (c == 11) return l73Slate;
                return c <= 15 && u is 23 or 24 or 31 or 32 && v == d - 3 ? l73Slate : 0;
        }
        return L73KeepBlock(u - WorldLayout.L73KeepU0, v - WorldLayout.L73KeepV0, c);
    }

    /// <summary>Whether a castle-local courtyard position is on the flagged walk round the keep (one wide, against its walls).</summary>
    private static bool L73CourtWalk(int u, int v)
    {
        int ku = u - WorldLayout.L73KeepU0, kv = v - WorldLayout.L73KeepV0;
        bool alongNS = ku is >= -1 and <= WorldLayout.L73KeepW && (kv == -1 || kv == WorldLayout.L73KeepD);
        bool alongWE = kv is >= -1 and <= WorldLayout.L73KeepD && (ku == -1 || ku == WorldLayout.L73KeepW);
        return alongNS || alongWE;
    }

    /// <summary>
    /// What stands in the courtyard at a castle-local position (round 3; inv.): the well, boarded over, in the south-west;
    /// by the kitchen's side of the keep the yard where the dead are heaped for the fire ("Hound is the fuel") with a hand
    /// cart and barrels; barrels against the west wall.
    /// </summary>
    private int L73CourtThing(int u, int v, int c)
    {
        if (c != 1) return 0;
        return (u, v) switch
        {
            (16, 38) => l73Well,
            (48, 9) or (49, 11) => l73Carcass[0, Facing(ArchPier.North)],
            (49, 9) => l73Carcass[1, Facing(ArchPier.East)],
            (48, 10) => l73Carcass[1, Facing(ArchPier.South)],
            (51, 13) => l73Cart[Facing(ArchPier.North)],
            (51, 8) or (52, 8) or (52, 9) or (6, 20) or (6, 21) or (7, 20) => l73Barrel,
            _ => 0,
        };
    }

    /// <summary>
    /// Whether a castle-local courtyard position holds a buttress against the keep's outer wall: on the long faces at keep
    /// columns 4, 8, 15, 20, 27 and 31 (15 and 20 flank the door's path), on the ends at rows 4, 8, 15 and 19, so never
    /// in front of a window (every fourth, from 2) or a banner.
    /// </summary>
    private static bool L73Buttress(int u, int v)
    {
        int ku = u - WorldLayout.L73KeepU0, kv = v - WorldLayout.L73KeepV0;
        bool longFace = (kv == -1 || kv == WorldLayout.L73KeepD) && ku is 4 or 8 or 15 or 20 or 27 or 31;
        bool endFace = (ku == -1 || ku == WorldLayout.L73KeepW) && kv is 4 or 8 or 15 or 19;
        return longFace || endFace;
    }

    /// <summary>The keep, keep-local, <paramref name="c"/> above its floor: three storeys, the slabs between, the roof above.</summary>
    private int L73KeepBlock(int ku, int kv, int c)
    {
        if (c > WorldLayout.L73Terrace) return L73KeepTop(ku, kv, c);
        bool ring = WorldLayout.L73KeepRing(ku, kv);
        const int storey = WorldLayout.L73Storey;
        if (c == 0)
        {
            if (WorldLayout.L73MainDoor(ku, kv)) return l73Ashlar;
            if (WorldLayout.L73CellarStep(ku, kv) > 0) return 0; // (the stairwell down to the cellar)
            if (ku == 34 && kv == 9) return hotelStairIds[0, Facing(ArchPier.East)]; // (its head: the first half step down)
            if (ring || WorldLayout.L73HearthAt(ku, kv) > 0) return l73Silver;
            return L73FloorOf(ku, kv, 0, WorldLayout.L73RoomAt(ku, kv, 0));
        }
        if (c % storey == 0)
        {
            // A slab: the ceiling of the storey below, the floor of the one above (open over the flight below it)
            int below = c / storey - 1, above = below + 1;
            if (ring) return l73Ashlar; // (a string course of smooth stone round the outside at every floor)
            int step = WorldLayout.L73StairStep(ku, kv, below);
            if (step == 5) return hotelStairIds[0, Facing(WorldLayout.L73StairRise(below))];
            // (the balustrade's last length, over the flight's top step, stands in the hole at the floor above)
            if (step == 4) return kv == 13 ? l73StairRail[WorldLayout.L73StairRise(below) == ArchPier.East ? 0 : 1] : 0;
            if (step > 0) return 0;
            if (above <= 2)
            {
                Room room = WorldLayout.L73RoomAt(ku, kv, above);
                return room == Room.Wall ? l73Silver : L73FloorOf(ku, kv, above, room);
            }
            // The roof terrace: the attic's boards in it, stone paving round it
            return WorldLayout.L73AtticAt(ku, kv) switch
            {
                Atp.Inside or Atp.LockedDoor or Atp.BalconyDoor => l73FloorBoards,
                Atp.Wall or Atp.StairWall => l73Silver,
                _ => l73Ashlar,
            };
        }

        int s = c / storey, h = c - s * storey; // h 1 to 4 over the storey's floor
        if (ring)
        {
            if (s == 0 && WorldLayout.L73MainDoor(ku, kv)) return h <= 3 ? l73Door[ku - 17 + 2 * (h - 1)] : l73Silver;
            // Windows, boarded up (the curtains hang inside)
            if (h is 2 or 3 && WorldLayout.L73Window(ku, kv, s)) return l73WindowBoards;
            // Silver ashlar outside; inside, panelling to the chair rail, red damask over it ("lavishly decorated"), a carved
            // cornice at the ceiling
            int lined = kv == 0 && ku is > 0 and < WorldLayout.L73KeepW - 1 ? 2 : kv == WorldLayout.L73KeepD - 1 && ku is > 0 and < WorldLayout.L73KeepW - 1 ? 0
                : ku == 0 && kv is > 0 and < WorldLayout.L73KeepD - 1 ? 1 : ku == WorldLayout.L73KeepW - 1 && kv is > 0 and < WorldLayout.L73KeepD - 1 ? 3 : -1;
            if (lined < 0) return l73Silver;
            int iu = ku == 0 ? 1 : ku == WorldLayout.L73KeepW - 1 ? WorldLayout.L73KeepW - 2 : ku, iv = kv == 0 ? 1 : kv == WorldLayout.L73KeepD - 1 ? WorldLayout.L73KeepD - 2 : kv;
            return L73Service(WorldLayout.L73RoomAt(iu, iv, s)) ? l73Lime[lined] : L73Lining(h, lined);
        }
        // The dining hall's hearth: a great open fire three high under its mantel, between stone jambs
        if (s == 0 && WorldLayout.L73HearthAt(ku, kv) is int hearth and > 0)
        {
            if (h == 4) return l73Mantel[Facing(ArchPier.South)];
            if (hearth == 1) return l73Silver;
            return h == 1 ? l73Fire[0, Facing(ArchPier.South)] : 0;
        }

        if (WorldLayout.L73RoomAt(ku, kv, s) == Room.Wall)
        {
            if (WorldLayout.L73Doorway(ku, kv, s) && h <= 2) return 0;
            // The chimney rising through the upper storeys stays stone, with a fireplace in it on each (the sitting room's,
            // the solar's); the partitions are panelled and papered both sides
            bool chimney = s > 0 && kv == 1 && ku is >= 16 and <= 19;
            if (chimney)
            {
                bool fire = ku is 17 or 18;
                return h == 1 ? (fire ? l73Fire[0, Facing(ArchPier.South)] : l73Silver) : h == 2 ? l73Mantel[Facing(ArchPier.South)] : l73Silver;
            }
            // (the wall between the kitchen and the pantry is limewashed both sides)
            if (s == 0 && kv == 7 && ku > 26) return l73Lime[4];
            return L73Lining(h, 4);
        }
        int st = WorldLayout.L73StairStep(ku, kv, s);
        if (st > 0)
        {
            // The flight: panelled under its treads, a balustrade along its open side (south)
            if (h < st) return l73Lined[0, 4];
            if (h == st) return hotelStairIds[0, Facing(WorldLayout.L73StairRise(s))];
            if (h == st + 1 && kv == 13) return l73StairRail[WorldLayout.L73StairRise(s) == ArchPier.East ? 0 : 1];
            return 0;
        }
        if (WorldLayout.L73CurtainAt(ku, kv, s) is ArchPier curtain) return l73Curtain[h == 4 ? 0 : h == 1 ? 2 : 1, Facing(curtain)];
        // A rail round the stairwell of the flight below, on this storey's floor (and round the cellar's in the pantry)
        if (h == 1 && s > 0 && L73WellRail(ku, kv, s - 1) is ArchPier rail) return l73Rail[Facing(rail)];
        if (h == 1 && s == 0 && L73CellarRail(ku, kv) is ArchPier cellarRail) return l73Rail[Facing(cellarRail)];
        int thing = L73Furnishing(ku, kv, s, h, 3);
        if (thing != 0 || h != 4) return thing;
        return L73Beam(ku, kv, s);
    }

    /// <summary>The rail round the cellar's stairwell in the pantry (its back on the well), or null: along both its sides and
    /// across its low (west) end; the top (east) end is the way down.</summary>
    private static ArchPier? L73CellarRail(int ku, int kv)
    {
        if (ku is >= 30 and <= 33 && kv == 8) return ArchPier.North;
        if (ku is >= 30 and <= 33 && kv == 10) return ArchPier.South;
        return ku == 29 && kv == 9 ? ArchPier.West : null;
    }

    /// <summary>
    /// The cellar under the kitchen and the pantry (round 3), keep-local, <paramref name="c"/> under the ground floor (-5 its
    /// floor of flags): ashlar walls round it, the stair down from the pantry (panelled under its treads), and what is kept
    /// there: barrels, crates, heaps of the hordes' dead (the fuel), bones; two sconces, and dark between them.
    /// </summary>
    private int L73CellarBlock(int ku, int kv, int c)
    {
        if (!WorldLayout.InL73Cellar(ku, kv)) return ku is >= 26 and <= 35 && kv is >= 0 and <= 11 ? l73Silver : l73Basalt;
        if (c == -WorldLayout.L73CellarDepth) return l73Flags;
        int h = c + WorldLayout.L73CellarDepth; // 1 to 4 over the cellar's floor
        int step = WorldLayout.L73CellarStep(ku, kv);
        if (step > 0)
        {
            int tread = -step; // (the step's block lies this far under the ground floor's slab)
            return c < tread ? l73Lined[0, 4] : c == tread ? hotelStairIds[0, Facing(ArchPier.East)] : 0;
        }
        if (h == 1)
        {
            return (ku, kv) switch
            {
                (27, 1) or (28, 1) or (29, 1) or (27, 2) or (27, 3) or (27, 4) or (33, 1) or (34, 1) or (32, 1) => l73Barrel,
                (34, 3) or (34, 4) => l73Carcass[0, Facing(ArchPier.West)],
                (33, 4) or (34, 5) => l73Carcass[1, Facing(ArchPier.North)],
                (27, 7) or (27, 8) or (28, 10) => PropBlock(new Tile { Variant = Props.WreckCrate, Pier = ArchPier.East }),
                (31, 5) => PropBlock(new Tile { Variant = Props.BonePile, Pier = ArchPier.North }),
                (27, 10) => l73Sacks[Facing(ArchPier.East)],
                _ => 0,
            };
        }
        if (h == 2 && (ku, kv) is (27, 1) or (28, 1) or (27, 2) or (29, 1) or (33, 1)) return l73Barrel; // (stacked)
        if (h == 3) return (ku, kv) switch
        {
            (27, 5) => l73Sconce[Facing(ArchPier.East)], (34, 8) => l73Sconce[Facing(ArchPier.West)], (31, 1) => l73Sconce[Facing(ArchPier.South)],
            (31, 10) => l73Sconce[Facing(ArchPier.North)],
            _ => 0,
        };
        // Carcasses hung by their heels from hooks in two rows (the Hound meat that feeds the castle's fires)
        if (h == 4 && ku is 30 or 32 && kv is 3 or 5 or 7) return l73HookMeat;
        return 0;
    }

    /// <summary>The service rooms, limewashed rather than panelled and papered: the kitchen and the pantry.</summary>
    private static bool L73Service(Room room) => room is Room.Kitchen or Room.Pantry;

    /// <summary>A lined wall's block at a height over the floor: the panelling (1), the damask (2, 3), the cornice (4).</summary>
    private int L73Lining(int h, int face) => h == 1 ? l73Lined[0, face] : h == 4 ? l73Cornice[face] : l73Lined[1, face];

    /// <summary>A storey's floor in a room (its top face; its underside is the ceiling of the storey below): a rug where one
    /// lies, flagstones in the hall, the kitchen and the pantry, tiles in the bath and the laundry, boards elsewhere.</summary>
    private int L73FloorOf(int ku, int kv, int s, Room room)
    {
        if (WorldLayout.L73RugAt(ku, kv, s) is { } rug) return l73Rug[rug.Pattern, rug.Part];
        return room switch
        {
            Room.Hall or Room.Kitchen or Room.Pantry => l73Flags,
            Room.Bath or Room.Laundry => s == 0 ? l73TileFloor : l73TileCeil,
            _ => l73FloorBoards,
        };
    }

    /// <summary>
    /// Whether a room position on the storey over a flight's stairwell (the hole over steps 1 to 4 of storey
    /// <paramref name="below"/>'s flight) gets a rail, and which way it faces (its back on the hole): along the well's open
    /// side (kv 14) and across its low end.
    /// </summary>
    private static ArchPier? L73WellRail(int ku, int kv, int below)
    {
        if (below > 1) return null;
        if (kv == 14 && WorldLayout.L73StairHole(ku, 13, below)) return ArchPier.South;
        if (kv is 12 or 13)
        {
            bool east = WorldLayout.L73StairRise(below) == ArchPier.East;
            int low = east ? ku + 1 : ku - 1; // the first step lies just past this position
            if (WorldLayout.L73StairStep(low, kv, below) == 1 && !WorldLayout.L73StairHole(ku, kv, below) && WorldLayout.L73StairStep(ku, kv, below + 1) == 0)
                return east ? ArchPier.West : ArchPier.East;
        }
        return null;
    }

    /// <summary>
    /// The dark oak beams under the ceilings (h 4): across the end rooms east to west every third row, across the middle
    /// rooms north to south every third column; none over a flight (head room) or where something else hangs.
    /// </summary>
    private int L73Beam(int ku, int kv, int s)
    {
        if (WorldLayout.L73StairStep(ku, kv, s) > 0) return 0;
        bool middle = ku is > 9 and < 26;
        if (middle) return ku % 3 == 0 ? l73Beam[0] : 0;
        return kv % 3 == 2 ? l73Beam[1] : 0;
    }

    /// <summary>
    /// Over the roof terrace: the parapet, the corner turrets, the chimney stacks (the hearth's in the middle of the north
    /// side, the guest rooms' at both ends, the kitchen's), the attic (its walls three high, its locked door and its balcony
    /// door, what is kept in it) under a stepped slate roof, and the balcony's rail.
    /// </summary>
    private int L73KeepTop(int ku, int kv, int c)
    {
        const int kw = WorldLayout.L73KeepW, kd = WorldLayout.L73KeepD;
        bool merlon = ((ku + kv) & 1) == 0;
        if ((ku < 3 || ku >= kw - 3) && (kv < 3 || kv >= kd - 3))
        {
            if (c <= 19) return l73Silver;
            // A slate cap and a needle spire on each turret, its top one under the band's (as the attic's ridge)
            if (c == 20) return l73Slate;
            return c <= WorldLayout.L73AtticTop && ku is 1 or kw - 2 && kv is 1 or kd - 2 ? l73Slate : 0;
        }
        if (ku is >= 16 and <= 19 && kv <= 1) return c <= 18 ? l73Silver : 0; // the hearth's chimney stack
        // The stacks over the guest rooms' fireplaces at both ends, and over the kitchen's (with a slate cap)
        bool endStack = (ku is 1 or 2 or kw - 2 or kw - 3) && kv is >= 16 and <= 19 || ku is kw - 2 or kw - 3 && kv is >= 3 and <= 5;
        if (endStack) return c <= 18 ? l73Silver : c == 19 ? l73Slate : 0;
        if (WorldLayout.L73KeepRing(ku, kv)) return c == 16 && merlon ? l73Silver : 0;
        // The attic's roof, stepping up from its eaves to the ridge (with an overhang at the gable ends)
        if (ku is >= 8 and <= 27 && kv is >= 4 and <= 15 && c >= 19)
        {
            int r = System.Math.Min(4, System.Math.Min(kv - 4, 15 - kv));
            int low = r == 0 ? 19 : 18 + r, high = 19 + r;
            if (c >= low && c <= high) return l73Slate;
            return c < low && ku is 9 or 26 ? l73Silver : 0;
        }
        int h = c - WorldLayout.L73Terrace;
        switch (WorldLayout.L73AtticAt(ku, kv))
        {
            case Atp.Wall:
            case Atp.StairWall:
                return l73Silver;
            case Atp.LockedDoor:
                return h <= 2 ? l73AtticDoor[ku - 23 + 2 * (h - 1)] : l73Silver;
            case Atp.BalconyDoor:
                return h <= 2 ? l73AtticDoor[ku - 17 + 2 * (h - 1)] : l73Silver;
            case Atp.Rail:
                return h == 1 ? l73Silver : 0;
            case Atp.Inside:
                return L73Furnishing(ku, kv, 3, h, 3);
        }
        return 0;
    }

    /// <summary>
    /// What stands at a keep-local position on a storey at <paramref name="h"/> above its floor: furniture on the floor (1;
    /// a fireplace runs up its four, a bed's canopy hangs at 3), plates and pinned notes at eye height (2), sconces,
    /// paintings and samplers on the walls at <paramref name="wallAt"/> (banners hang from the row above, down over it;
    /// tapestries from it down over the row below), chandeliers and pot racks under the ceiling (4); air elsewhere.
    /// </summary>
    private int L73Furnishing(int ku, int kv, int storey, int h, int wallAt)
    {
        var floor = WorldLayout.L73FurnishingAt(ku, kv, storey, Layer.Floor);
        if (floor.Thing is Thing.Fire or Thing.Jamb)
        {
            int f = Facing(floor.Facing);
            if (h == 1) return floor.Thing == Thing.Fire ? l73Fire[System.Math.Min(2, (int)floor.Kind), f] : l73Silver;
            // A cooking hearth (a cauldron, a spit) stands open two high under its mantel; a room's fire one
            bool tall = floor.Kind > 0;
            if (tall && h == 2) return floor.Thing == Thing.Fire ? 0 : l73Silver;
            return h == (tall ? 3 : 2) ? l73Mantel[f] : l73Silver; // (the chimney breast over the mantel)
        }
        if (h == 1 && floor.Thing != Thing.None) return L73FloorThing(floor.Thing, floor.Facing, floor.Kind);
        if (h == 3 && floor.Thing is Thing.BedHead or Thing.BedFoot && (floor.Kind & WorldLayout.L73Canopy) != 0)
        {
            int part = (floor.Thing == Thing.BedHead ? 0 : 2) + ((floor.Kind & WorldLayout.L73CanopyRight) != 0 ? 1 : 0);
            return l73Canopy[part, (floor.Kind & WorldLayout.L73CanopyBlack) != 0 ? 1 : 0, Facing(floor.Facing)];
        }
        if (h == 2 && WorldLayout.L73FurnishingAt(ku, kv, storey, Layer.Low) is { Thing: not Thing.None } low)
            return low.Thing == Thing.Plate ? l73Plate[System.Math.Min(low.Kind, (byte)12), Facing(low.Facing)]
                : l73Notice[System.Math.Min(low.Kind, (byte)3), Facing(low.Facing)];
        var wall = WorldLayout.L73FurnishingAt(ku, kv, storey, Layer.Wall);
        if (wall.Thing == Thing.Banner && h == wallAt + 1) return l73Banner[Facing(wall.Facing)];
        if (wall.Thing is Thing.TapestryL or Thing.TapestryR && (h == wallAt || h == wallAt - 1))
        {
            int part = (h == wallAt ? 2 : 0) + (wall.Thing == Thing.TapestryR ? 1 : 0); // bl br tl tr
            return l73Tapestry[System.Math.Min(wall.Kind, (byte)1), part, Facing(wall.Facing)];
        }
        if (wall.Thing is Thing.SamplerL or Thing.SamplerR && h == wallAt)
            return l73Sampler[wall.Thing == Thing.SamplerL ? 0 : 1, Facing(wall.Facing)];
        if (wall.Thing is Thing.Sconce or Thing.Painting && h == wallAt)
            return wall.Thing == Thing.Sconce ? l73Sconce[Facing(wall.Facing)] : l73Painting[wall.Kind, Facing(wall.Facing)];
        if (h == 4)
        {
            var ceiling = WorldLayout.L73FurnishingAt(ku, kv, storey, Layer.Ceiling).Thing;
            if (ceiling == Thing.Chandelier) return chandelierId;
            if (ceiling == Thing.PotRack) return l73PotRack;
        }
        return 0;
    }

    private int L73FloorThing(Thing thing, ArchPier facing, byte kind = 0)
    {
        int Prop(ushort variant, byte stack = 0) => PropBlock(new Tile { Variant = variant, Pier = facing, Stack = stack });
        int f = Facing(facing);
        return thing switch
        {
            Thing.Bookshelf => Prop(Props.HotelBookshelf),
            Thing.Clock => Prop(Props.GrandfatherClock),
            Thing.Candelabra => Prop(Props.Candelabra),
            Thing.Chair => Prop(Props.HotelChair),
            Thing.Toilet => Prop(Props.Toilet),
            Thing.Dresser => Prop(Props.Dresser),
            Thing.Desk => Prop(Props.WritingDesk),
            Thing.RoundTable => Prop(Props.DiningTable),
            Thing.SofaLeft => Prop(Props.LongSofa, 0),
            Thing.SofaRight => Prop(Props.LongSofa, 1),
            Thing.Crate => Prop(Props.WreckCrate),
            Thing.Bones => Prop(Props.BonePile),
            Thing.Ribcage => Prop(Props.Ribcage),
            Thing.Skull => Prop(Props.JawSkeleton),
            Thing.Pack => Prop(Props.Backpack),
            Thing.WingChair => Prop(Props.WingChair),
            Thing.CoffeeTable => Prop(Props.CoffeeTable),
            Thing.ConsoleTable => Prop(Props.ConsoleTable),
            // (the castle's own shelves and sacks, fixed and empty: the food is the table's)
            Thing.PantryShelf => l73Larder[f],
            Thing.Sacks => l73Sacks[f],
            Thing.Box => boxId,
            Thing.Note => l73Note,
            Thing.Table => l73Table[0, f],
            Thing.Bath => l73Bath,
            Thing.Chest => l73Chest[f],
            Thing.Washstand => l73Washstand[f],
            Thing.Worktable => l73Worktable[System.Math.Min((int)kind, 1), f],
            Thing.Lectern => l73Lectern[f],
            Thing.Linen => l73Linen[f],
            Thing.Sheeted => l73Sheeted[System.Math.Min((int)kind, 1), f],
            // Beds are modelled head to the north; the facing points from the head toward the foot
            Thing.BedHead => bedHeadIds[Facing(Opposite(facing))],
            Thing.BedFoot => bedFootIds[Facing(Opposite(facing))],
            Thing.Nightstand => nightstandIds[f],
            Thing.Wardrobe => wardrobeIds[f],
            _ => 0,
        };
    }
}
