using System.Collections.Generic;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level Fun (kept as level 15), laid out in WorldLayout.LevelFun.cs: vinyl and carpet underfoot, painted
/// walls with white skirting, the promenades' cream, a drop ceiling and its humming lights; and everything a party
/// leaves: tables in their cloths, chairs, cakes, gifts, balloons against the ceiling, streamers, bunting, string
/// lights, posters. Its floor is <see cref="WorldGeometry.FloorFor"/>; an open deck's sea lies below it.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] FunPaints = { "orange", "sky", "lime", "pink", "yellow", "lilac" };
    private static readonly string[] FunCloths = { "blue", "greenstripe", "pink", "yellow", "redcheck" };
    private static readonly string[] FunColours = { "red", "yellow", "blue", "green", "pink" };
    private static readonly string[] FunChairColours = { "white", "orange", "lime", "red", "black" };
    private static readonly string[] FunGiftColours = { "red", "blue", "green", "yellow", "purple" };
    private static readonly string[] FunMurals = { "mouse", "hotdog", "cheese", "stork" };
    private static readonly string[] FunQuadrants = { "tl", "tr", "bl", "br" };
    private static readonly string[] FunStreamers = { "redyellow", "bluegreen", "pinkpurple" };
    private static readonly string[] FunBalloonSets = { "mixed", "pastel", "red" };

    /// <summary>The level's props: block code, oriented, kinds (picked by Stack).</summary>
    private static readonly (ushort Prop, string Code, bool Oriented, string[] Kinds)[] FunPropTable =
    {
        (Props.FunTable, "fun-table", true, Kinds2(FunCloths, "a", "b")),
        (Props.FunChair, "fun-chair", true, FunChairColours),
        (Props.FunChairTipped, "fun-chairtipped", true, FunChairColours),
        (Props.FunGift, "fun-gift", false, Kinds2(FunGiftColours, "small", "tall")),
        (Props.FunBalloonsFloor, "fun-balloons-floor", false, new[] { "mixed", "pastel" }),
        (Props.FunBalloonTied, "fun-balloon-tied", false, FunColours),
        (Props.FunArchL, "fun-balloonarch-l", true, null),
        (Props.FunArchR, "fun-balloonarch-r", true, null),
        (Props.FunConfetti, "fun-confetti", false, null),
        (Props.FunInflatableTower, "fun-inflatable-tower", false, new[] { "yellow", "blue", "red" }),
        (Props.FunInflatableArch, "fun-inflatable-arch", true, null),
        (Props.FunBlower, "fun-blower", true, null),
        (Props.FunCord, "fun-extensioncord", true, new[] { "straight", "corner", "plug" }),
        (Props.FunFoam, "fun-foam", false, new[] { "red", "blue", "yellow", "green" }),
        (Props.FunNet, "fun-net", true, null),
        (Props.FunAirHockey, "fun-airhockey", true, new[] { "a", "b" }),
        (Props.FunPopcornCart, "fun-popcorncart", true, null),
        (Props.FunCounter, "fun-counter", true, null),
        (Props.FunOven, "fun-oven", true, null),
        (Props.FunCakeTins, "fun-caketins", true, null),
        (Props.FunWaitingChair, "fun-waitingchair", true, null),
        (Props.FunReception, "fun-reception", true, null),
        (Props.FunMagazineTable, "fun-magazinetable", false, null),
        (Props.FunShipRail, "fun-shiprail", true, null),
        (Props.FunDeckChair, "fun-deckchair", true, new[] { "a", "b" }),
        (Props.FunLinenCart, "fun-linencart", false, null),
        (Props.FunSupplyShelf, "fun-supplyshelf", true, null),
        (Props.FunCBalloon, "fun-cballoon", false, FunColours),
        (Props.FunPosterTrap, "fun-poster-trap", true, null),
        (Props.FunSmiley, "fun-smiley", true, new[] { "1", "2", "3", "4" }),
    };

    private static string[] Kinds2(string[] a, string b0, string b1)
    {
        var kinds = new string[a.Length * 2];
        for (int i = 0; i < a.Length; i++) { kinds[i * 2] = a[i] + "-" + b0; kinds[i * 2 + 1] = a[i] + "-" + b1; }
        return kinds;
    }

    private readonly int[,,] funPropIds = new int[Props.FunLast - Props.FunFirst + 1, 10, 4];
    private readonly byte[] funPropKinds = new byte[Props.FunLast - Props.FunFirst + 1];
    private readonly int[] funPaintIds = new int[6], funPromBandIds = new int[4], funPortholeIds = new int[4], funCrewSignIds = new int[4];
    private readonly int[,] funSkirtIds = new int[6, 4], funInflatableIds = new int[3, 4], funFunDoorIds = new int[3, 2];
    private readonly int[,,] funMuralIds = new int[4, 4, 4], funElevatorIds = new int[2, 2, 4];
    private readonly int[,] funItemIds = new int[32, 4];
    private readonly int[] funTopIds = new int[6], funBalloonIds = new int[3], funExitDoorIds = new int[2];
    private readonly int[,] funMascotDoorIds = new int[2, 2];
    private readonly int[,] funStreamerIds = new int[3, 2];
    private int funPromwallId, funHullId, funSteelId, funVoidId, funPitFillId, funRoofId, funPumpkinId;
    private readonly List<string> funMissing = new();

    /// <summary>A block of this mod by code path, or a stand-in while the level's assets are still being made (listed once in the log).</summary>
    private int FunId(string path, int fallback)
    {
        if (modBlocks.TryGetValue(path, out int id)) return id;
        funMissing.Add(path);
        return fallback;
    }

    /// <summary>Looks up the level's blocks, once, when the generator is made (see <see cref="Id"/> for this mod's blocks).</summary>
    private void InitFun()
    {
        int carpet = floorIds[(int)FloorKind.Carpet], wall = concreteWallId != 0 ? concreteWallId : concreteId;
        string[] vinyl = { "a", "b", "c", "d" };
        for (int i = 0; i < 4; i++) floorIds[(int)FloorKind.FunFloor + i] = FunId($"fun-vinyl-{vinyl[i]}", carpet);
        floorIds[(int)FloorKind.FunRaceCarpet] = FunId("fun-racecarpet", carpet);
        floorIds[(int)FloorKind.FunRetroCarpet] = FunId("fun-retrocarpet", carpet);
        floorIds[(int)FloorKind.FunCheckerA] = FunId("fun-checkermat-a", carpet);
        floorIds[(int)FloorKind.FunCheckerB] = FunId("fun-checkermat-b", carpet);
        floorIds[(int)FloorKind.FunDeck] = FunId("fun-deckplank", floorIds[(int)FloorKind.Wood]);
        floorIds[(int)FloorKind.FunParquet] = FunId("fun-parquet", floorIds[(int)FloorKind.Wood]);
        floorIds[(int)FloorKind.FunLobbyCarpet] = FunId("fun-lobbycarpet", carpet);
        floorIds[(int)FloorKind.FunInflatableFloor] = FunId("fun-inflatable-floor", carpet);

        for (int c = 0; c < 6; c++)
        {
            funPaintIds[c] = FunId($"fun-paint-{FunPaints[c]}", wall);
            for (int f = 0; f < 4; f++) funSkirtIds[c, f] = FunId($"fun-paint-{FunPaints[c]}-skirted-{Sides[f]}", funPaintIds[c]);
        }
        funPromwallId = FunId("fun-promwall", wall);
        funHullId = FunId("fun-hull", wall);
        funSteelId = FunId("fun-steel", wall);
        funVoidId = FunId("fun-nightvoid", mantleId);
        funPitFillId = FunId("ballpitfill", 0);
        funRoofId = FunId("fun-inflatable-floor", carpet);
        for (int f = 0; f < 4; f++)
        {
            funPromBandIds[f] = FunId($"fun-promwall-band-{Sides[f]}", funPromwallId);
            funPortholeIds[f] = FunId($"fun-hull-porthole-{Sides[f]}", funHullId);
            funCrewSignIds[f] = FunId($"fun-steel-sign-crewonly-{Sides[f]}", funSteelId);
            for (int c = 0; c < 3; c++) funInflatableIds[c, f] = FunId($"fun-inflatable-wall-{FunBalloonColour(c)}-{Sides[f]}", wall);
            for (int m = 0; m < 4; m++)
                for (int q = 0; q < 4; q++) funMuralIds[m, q, f] = FunId($"fun-mural-{FunMurals[m]}-{FunQuadrants[q]}-{Sides[f]}", funPaintIds[4]);
            for (int lr = 0; lr < 2; lr++)
                for (int part = 0; part < 2; part++)
                    funElevatorIds[lr, part, f] = FunId($"fun-elevator-{(lr == 0 ? "l" : "r")}-{(part == 0 ? "lower" : "upper")}-{Sides[f]}", funPromwallId);
        }
        string[] leaves = { "l", "r", "single" };
        for (int l = 0; l < 3; l++)
            for (int part = 0; part < 2; part++)
                funFunDoorIds[l, part] = FunId($"fun-door-fun-{leaves[l]}-{(part == 0 ? "lower" : "upper")}", wall);
        funExitDoorIds[0] = FunId("fun-door-exit-lower", wall);
        funExitDoorIds[1] = FunId("fun-door-exit-upper", wall);
        for (int l = 0; l < 2; l++)
            for (int part = 0; part < 2; part++)
                funMascotDoorIds[l, part] = FunId($"fun-door-mascot-{(l == 0 ? "l" : "r")}-{(part == 0 ? "lower" : "upper")}", wall);

        // What hangs on the walls, by item number
        var items = new Dictionary<byte, string>
        {
            [FunWallItems.PosterTime4Fun] = "fun-poster-time4fun", [FunWallItems.PosterHappyBday] = "fun-poster-happybday",
            [FunWallItems.PosterComeJoin] = "fun-poster-comejoin", [FunWallItems.PosterReversed] = "fun-poster-reversed",
            [FunWallItems.SpeakerOn] = "fun-speaker-on", [FunWallItems.SpeakerOff] = "fun-speaker-off",
            [FunWallItems.StringLights] = "fun-stringlights", [FunWallItems.DeckSign] = "fun-decksign",
            [FunWallItems.LifeRing] = "fun-lifering", [FunWallItems.DeckLamp] = "fun-decklamp",
            [FunWallItems.ScreenL] = "fun-screen-l", [FunWallItems.ScreenM] = "fun-screen-m", [FunWallItems.ScreenR] = "fun-screen-r",
        };
        for (int i = 0; i < 4; i++) items[(byte)(FunWallItems.Smiley1 + i)] = $"fun-smiley-{i + 1}";
        string letters = "hapybirtd";
        for (int i = 0; i < 10; i++) items[(byte)(FunWallItems.BuntingFirst + i)] = i < 9 ? $"fun-bunting-{letters[i]}" : "fun-bunting-blank";
        foreach (var (item, code) in items)
            for (int f = 0; f < 4; f++) funItemIds[item, f] = FunId($"{code}-{Sides[f]}", 0);

        string[] tops = { "fun-tableware-plates", "fun-tableware-cups", "fun-tableware-mess", "fun-cake-birthday-4", "fun-cake-velvet-4", "fun-cookieplate-3" };
        for (int i = 0; i < tops.Length; i++) funTopIds[i] = FunId(tops[i], 0);
        for (int i = 0; i < 3; i++)
        {
            funBalloonIds[i] = FunId($"fun-balloons-ceiling-{FunBalloonSets[i]}", 0);
            funStreamerIds[i, 0] = FunId($"fun-streamer-{FunStreamers[i]}-ns", 0);
            funStreamerIds[i, 1] = FunId($"fun-streamer-{FunStreamers[i]}-ew", 0);
        }

        foreach (var (prop, code, oriented, kinds) in FunPropTable)
        {
            int index = prop - Props.FunFirst;
            funPropKinds[index] = (byte)(kinds?.Length ?? 1);
            for (int k = 0; k < (kinds?.Length ?? 1); k++)
            {
                string kind = kinds != null ? "-" + kinds[k] : "";
                for (int f = 0; f < 4; f++) funPropIds[index, k, f] = FunId(oriented ? $"{code}{kind}-{Sides[f]}" : $"{code}{kind}", 0);
            }
        }
        Vintagestory.API.Common.Block pumpkin = api.World.GetBlock(new Vintagestory.API.Common.AssetLocation("game:pumpkin-fruit-4"));
        funPumpkinId = pumpkin?.BlockId ?? 0;

        if (funMissing.Count > 0)
            api.Logger.Warning("[backrooms] Level Fun: {0} blocks are not made yet (stand-ins used), e.g. {1}", funMissing.Count,
                string.Join(", ", funMissing.GetRange(0, System.Math.Min(6, funMissing.Count))));
    }

    private static string FunBalloonColour(int c) => c switch { 0 => "yellow", 1 => "blue", _ => "red" };

    /// <summary>The tallest wall: an open deck's sky is one higher than its air.</summary>
    private const int FunWallTop = 15;

    /// <summary>The block (and fluid) at <paramref name="rel"/> above the level's floor in the column of tile <paramref name="t"/>.</summary>
    private int LevelFunBlock(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        switch (t.Kind)
        {
            case TileKind.Wall:
                if (t.Pattern == WallPattern.FunVoid) return rel >= -WorldLayout.FunSeaDepth && rel <= FunWallTop ? funVoidId : concreteId;
                if (t.Height > 0)
                {
                    // A low wall standing in a room (a bounce house's side), the room's air over it
                    if (rel < 0) return concreteId;
                    if (rel == 0) return FunFloorBlock(t.Floor);
                    if (rel <= t.Height) return FunWallFace(t, gx, gz, rel);
                    if (rel <= WorldLayoutFunBounce) return 0;
                    return rel == WorldLayoutFunBounce + 1 ? ceilingTileId : concreteId;
                }
                if (rel < 0 || rel > FunWallTop) return concreteId;
                return FunWallFace(t, gx, gz, rel);
            case TileKind.Door:
                if (rel < 0 || rel > FunWallTop) return concreteId;
                if (rel == 0) return FunFloorBlock(t.Floor);
                if (rel <= 2)
                {
                    if (t.Pattern == WallPattern.FunExitDoor) return funExitDoorIds[rel - 1];
                    return funFunDoorIds[t.Variant == 1 ? 1 : 0, rel - 1];
                }
                return FunPaintFace(t.Detail, rel, t.Pier);
            case TileKind.Doorway:
                if (rel < 0 || rel > FunWallTop) return concreteId;
                if (rel == 0) return FunFloorBlock(t.Floor);
                if (rel <= 2) return 0;
                return FunWallFace(t, gx, gz, rel);
        }

        int height = t.Height == 0 ? 3 : t.Height;
        if (t.Zone == (byte)FunZone.Sea)
        {
            // Black water far below, under a black sky
            if (rel < -WorldLayout.FunSeaDepth) return concreteId;
            if (rel == -WorldLayout.FunSeaDepth) return funVoidId;
            if (rel <= WorldLayout.FunSeaSurface) { fluid = waterId; return 0; }
            if (rel <= height) return 0;
            return rel == height + 1 ? funVoidId : concreteId;
        }

        int bed = -t.Depth;
        if (rel < bed) return t.Zone == (byte)FunZone.Deck ? funHullId : concreteId;
        if (rel == bed) return FunFloorBlock(t.Floor);
        if (rel <= 0) return funPitFillId; // a ball pit, full to the brim

        if (t.Ceiling == CeilingKind.FunInflatableRoof)
        {
            // Inside a bounce house: its puffy roof, then the hall's air over it
            if (rel == height + 1) return funRoofId;
            if (rel > height + 1)
            {
                if (rel <= WorldLayoutFunBounce) return 0;
                return rel == WorldLayoutFunBounce + 1 ? ceilingTileId : concreteId;
            }
        }
        else
        {
            if (rel == height + 1) return t.Ceiling == CeilingKind.FunCeiling ? funVoidId : CeilingBlock0(t.Ceiling);
            if (rel > height + 1) return concreteId;
        }

        // Stairs into the ceiling: solid under each step
        if (t.Stair > 0 && rel <= t.Stair) return rel < t.Stair ? concreteId : stairIds[Facing(t.Pier)];

        // What hangs on the wall beside it
        byte item = FunWallItems.Item(t.Roof);
        if (item != 0)
        {
            int at = FunWallItems.Rel(item);
            if (rel == (at == 0 ? height : at)) return funItemIds[item, Facing(FunWallItems.Facing(t.Roof))];
        }

        ushort prop = t.Variant;
        if (rel == 1)
        {
            if (prop == Props.FunCBalloon) return 0; // it floats at chest height
            if (prop == Props.FunPumpkin) return funPumpkinId;
            return FunProp(t);
        }
        if (prop == Props.FunInflatableTower && rel <= 3 || prop == Props.FunNet && rel < height) return FunProp(t);
        if (rel == 2)
        {
            if (prop == Props.FunCBalloon) return FunProp(t);
            if (t.Pipe is >= Pipes.FunPlates and <= Pipes.FunCookies) return funTopIds[t.Pipe - Pipes.FunPlates];
        }
        if (rel == height)
        {
            int set = t.Detail >> 6 & 3, colour = (t.Detail & 7) % 3;
            switch (t.Overhead)
            {
                case Overheads.FunBalloons: return funBalloonIds[System.Math.Min(set, 2)];
                case Overheads.FunStreamerNS: return funStreamerIds[colour, 0];
                case Overheads.FunStreamerWE: return funStreamerIds[colour, 1];
            }
        }
        return 0;
    }

    private const int WorldLayoutFunBounce = 8;

    private int FunFloorBlock(FloorKind floor)
    {
        int id = floorIds[(int)floor];
        return id != 0 ? id : floorIds[(int)FloorKind.Carpet];
    }

    /// <summary>One of the level's props (or one of the castle's, the slide and the arcade cabinet, by the shared table).</summary>
    private int FunProp(in Tile t)
    {
        if (t.Variant < Props.FunFirst || t.Variant > Props.FunLast) return PropBlock(t);
        int index = t.Variant - Props.FunFirst;
        int kind = System.Math.Min(t.Stack, funPropKinds[index] - 1);
        return funPropIds[index, System.Math.Max(0, kind), Facing(t.Pier)];
    }

    private int FunPaintFace(byte detail, int rel, ArchPier facing)
    {
        int colour = System.Math.Min(detail & 7, 5);
        return rel == 1 ? funSkirtIds[colour, Facing(facing)] : funPaintIds[colour];
    }

    /// <summary>A wall's block at a height: its material, and what is on its face toward <see cref="Tile.Pier"/>.</summary>
    private int FunWallFace(in Tile t, int gx, int gz, int rel)
    {
        int facing = Facing(t.Pier);
        switch (t.Pattern)
        {
            case WallPattern.FunPaint:
                return FunPaintFace(t.Detail, rel, t.Pier);
            case WallPattern.FunPromenade:
                return rel == 1 ? funPromBandIds[facing] : funPromwallId;
            case WallPattern.FunMural:
                if (t.Variant > 0 && rel is 2 or 3)
                {
                    int m = (t.Variant - 1) / 2 % 4, half = (t.Variant - 1) % 2;
                    return funMuralIds[m, (rel == 3 ? 0 : 2) + half, facing];
                }
                return FunPaintFace(4, rel, t.Pier);
            case WallPattern.FunSteel:
                return rel == 2 && Hashing.Mod(gx * 3 + gz * 5, 11) == 0 ? funCrewSignIds[facing] : funSteelId;
            case WallPattern.FunInflatable:
                return funInflatableIds[t.Detail % 3, facing];
            case WallPattern.FunElevator:
                return rel is 1 or 2 ? funElevatorIds[t.Variant == 1 ? 1 : 0, rel - 1, facing] : funPromwallId;
            case WallPattern.FunWall:
                return rel == 2 && Hashing.Mod(gx + gz, 4) == 0 ? funPortholeIds[facing] : funHullId;
            case WallPattern.FunVoid:
                return funVoidId;
            default:
                return concreteId;
        }
    }
}
