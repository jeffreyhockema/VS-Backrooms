using System.Collections.Generic;
using Zone = Backrooms.Worldgen.WorldLayout.L31Zone;
using L31 = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 31, "Roller Rink" (experimental, kept as level 24), laid out in WorldLayout.Level31.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Every floor tile carries its air height (<see cref="Tile.Height"/>: halls and the
/// lobby 5, rooms and the corridor 4, the cinema 6, the rink 7 or 5) with its ceiling just above; walls are dressed to
/// their own height and solid above. The level's own blocks (tools/gen_31.py) are the rink boards, the rink's walls and
/// barrier, the mirror panels and the disco ball, the coloured tubes and the glowing carpet; the rest is borrowed: Level
/// 3999's neon, carpets, ceilings, counters and arcade machines, Level Fun's carpet, vinyl and cinema screen, Level 52's
/// lockers, Level 3's glazed tile, the shared detail props (benches, café tables, snack counters, toilets, machinery).
///
/// Every block is looked up softly (<see cref="L31Block"/>): what is missing is drawn as its stand-in, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private int l31Galaxy, l31Cosmic, l31Marble, l31Retro, l31Vinyl, l31CheckerA, l31CheckerB, l31Maroon, l31Glow, l31ConcFloor, l31ConcWet,
        l31ConcDark, l31Stripe, l31Plain, l31Blue, l31Chart, l31Dasher, l31Glazed, l31Dark, l31Ball, l31CeilBlack, l31CeilAcoustic, l31Bin;
    private readonly int[] l31Board = new int[4], l31Mirror = new int[4], l31NeonDead = new int[2], l31DeadCab = new int[4], l31Pinball = new int[4],
        l31Claw = new int[4], l31SkeeLane = new int[4], l31SkeeTarget = new int[4], l31Prize = new int[4], l31DjScreen = new int[4];
    private readonly int[,] l31Tube = new int[6, 4], l31Locker = new int[2, 4], l31Neon = new int[6, 2], l31Rail = new int[6, 4], l31Cabinet = new int[6, 4],
        l31Counter = new int[3, 4], l31Vending = new int[2, 4], l31Couch = new int[2, 4], l31Screen = new int[3, 4];
    private readonly HashSet<string> l31Missing = new();

    /// <summary>A block of this mod's, or <paramref name="fallback"/> if it is not there (logged once).</summary>
    private int L31Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l31Missing.Add(code) && l31Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 31: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>The level's block ids (called from the constructor, after Level 3999's and Level 52's).</summary>
    private void InitL31()
    {
        l31ConcFloor = L31Block("concretefloor-plain", concreteId);
        l31ConcWet = L31Block("concretefloor-wet", l31ConcFloor);
        l31ConcDark = L31Block("concretefloor-dark", l31ConcFloor);
        l31Galaxy = L31Block("l3999-carpet-galaxy", l31ConcFloor);
        l31Cosmic = L31Block("l3999-carpet-cosmic", l31Galaxy);
        l31Marble = L31Block("l3999-marble-black", l31ConcFloor);
        l31Retro = L31Block("fun-retrocarpet", l31Cosmic);
        l31Vinyl = L31Block("fun-vinyl-a", l31ConcFloor);
        l31CheckerA = L31Block("fun-checkermat-a", l31Vinyl);
        l31CheckerB = L31Block("fun-checkermat-b", l31Vinyl);
        l31Maroon = L31Block("hotelcarpet-maroon", l31Retro);
        l31Glow = L31Block("l31-glowcarpet-plain", l31Cosmic);
        string[] boards = { "plain", "stripens", "stripewe", "centre" };
        for (int i = 0; i < 4; i++) l31Board[i] = L31Block("l31-rinkwood-" + boards[i], i == 0 ? L31Block("hotelwood", l31ConcFloor) : l31Board[0]);
        l31Plain = L31Block("l31-skatewall-plain", concreteWallId);
        l31Stripe = L31Block("l31-skatewall-stripe", l31Plain);
        l31Blue = L31Block("l31-skatewall-blue", l31Plain);
        l31Chart = L31Block("l31-skatewall-chart", l31Blue);
        l31Dasher = L31Block("l31-skatewall-dasher", l31Plain);
        l31Glazed = L31Block("l3wall-glazed", l31Plain);
        l31Dark = L31Block("l3999-wall-midnight", l31Plain);
        l31Ball = L31Block("l31-mirror-ball");
        l31CeilBlack = L31Block("l3999-ceiling-black", concreteCeilingId);
        l31CeilAcoustic = L31Block("l3999-ceiling-acoustic", ceilingTileId);
        l31Bin = L31Block("l3999-trashbin");
        string[] hues = { "magenta", "cyan", "amber", "green", "violet", "white" }, states = { "on", "lit", "flicker", "off" };
        int[] fallbacks = { lightOnId, lightLitId, lightFlickerId, lightOffId };
        for (int h = 0; h < 6; h++)
            for (int s = 0; s < 4; s++) l31Tube[h, s] = L31Block($"l31-tube-{hues[h]}-{states[s]}", fallbacks[s]);
        string[] colours = WorldLayout.L3999Colours, games = { "a", "b", "c", "d", "e", "f" }, desk = { "left", "mid", "right" }, screens = { "l", "m", "r" };
        l31NeonDead[0] = L31Block("l3999-neondead-ns");
        l31NeonDead[1] = L31Block("l3999-neondead-we");
        for (int c = 0; c < 6; c++)
        {
            l31Neon[c, 0] = L31Block($"l3999-neonceiling-{colours[c]}-ns");
            l31Neon[c, 1] = L31Block($"l3999-neonceiling-{colours[c]}-we");
        }
        for (int f = 0; f < 4; f++)
        {
            string side = Sides[f];
            l31Mirror[f] = L31Block("l31-mirror-" + side, l31Plain);
            l31Locker[0, f] = L31Block($"l52-locker-lower-{side}", l31Stripe);
            l31Locker[1, f] = L31Block($"l52-locker-upper-{side}", l31Plain);
            for (int c = 0; c < 6; c++)
            {
                l31Rail[c, f] = L31Block($"l3999-neonrail-{colours[c]}-{side}");
                l31Cabinet[c, f] = L31Block($"l3999-cabinet-{games[c]}-{side}");
            }
            l31DeadCab[f] = L31Block($"l3999-cabinet-dead-{side}");
            l31Pinball[f] = L31Block($"l3999-pinball-{side}");
            l31Claw[f] = L31Block($"l3999-claw-{side}");
            l31SkeeLane[f] = L31Block($"l3999-skeeball-lane-{side}");
            l31SkeeTarget[f] = L31Block($"l3999-skeeball-target-{side}");
            l31Prize[f] = L31Block($"l3999-prizecounter-{side}");
            l31DjScreen[f] = L31Block($"l3999-dance-screen-{side}");
            for (int k = 0; k < 3; k++)
            {
                l31Counter[k, f] = L31Block($"l3999-reception-{desk[k]}-{side}");
                l31Screen[k, f] = L31Block($"fun-screen-{screens[k]}-{side}");
            }
            l31Vending[0, f] = L31Block($"l3999-vending-snack-{side}");
            l31Vending[1, f] = L31Block($"l3999-vending-drink-{side}");
            l31Couch[0, f] = L31Block($"l3999-couch-left-{side}");
            l31Couch[1, f] = L31Block($"l3999-couch-right-{side}");
        }
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level31Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        if (rel < 0) return concreteId;
        if (t.Kind != TileKind.Floor)
        {
            int high = t.Height > 0 ? t.Height : 4;
            if (rel > high) return concreteId;
            if (rel == 0) return t.Kind == TileKind.Doorway ? L31Floor(t, gx, gz) : concreteId;
            if (t.Kind == TileKind.Doorway && rel <= 3) return 0;
            return L31WallBlock(t, rel, high);
        }
        int air = t.Height > 0 ? t.Height : 4;
        if (rel == 0) return L31Floor(t, gx, gz);
        if (rel == air + 1) return L31Ceiling(t);
        if (rel > air) return concreteId;
        if (rel == air)
        {
            switch (t.Overhead)
            {
                case L31.L31Overhead.NeonNS: return l31Neon[(t.Detail & L31.L31HueMask) % 6, 0];
                case L31.L31Overhead.NeonWE: return l31Neon[(t.Detail & L31.L31HueMask) % 6, 1];
                case L31.L31Overhead.DeadNS: return l31NeonDead[0];
                case L31.L31Overhead.DeadWE: return l31NeonDead[1];
                case L31.L31Overhead.DiscoBall: return l31Ball;
            }
            if (t.Zone == (byte)Zone.Corridor)
            {
                int pipe = (t.Detail & L31.L31SubMask) >> L31.L31SubShift;
                if (pipe == L31.L31PipeX) return pipeRunXId;
                if (pipe == L31.L31PipeZ) return pipeRunZId;
            }
        }
        if (t.Variant == L31.L31Props.Screen) return rel == air ? l31Screen[System.Math.Min((int)t.Stack, 2), Facing(t.Pier)] : 0;
        if (rel != 1) return 0;
        if (t.Variant != 0) return L31Prop(t);
        if ((t.Detail & L31.L31RailBit) != 0 && t.Zone == (byte)Zone.Hall) return l31Rail[(t.Detail & L31.L31HueMask) % 6, Facing(t.Pier)];
        return 0;
    }

    private int L31WallBlock(in Tile t, int rel, int high)
    {
        if ((t.Detail & L31.L31MirrorBit) != 0 && (high >= 7 ? rel is >= 3 and <= 5 : rel is 2 or 3)) return l31Mirror[Facing(t.Pier)];
        int skate = rel == 1 ? l31Stripe : l31Plain;
        return ((t.Detail & L31.L31SubMask) >> L31.L31SubShift) switch
        {
            L31.L31Wall.Concrete => concreteWallId,
            L31.L31Wall.Blue => l31Blue,
            L31.L31Wall.Glazed => l31Glazed,
            L31.L31Wall.Dark => l31Dark,
            L31.L31Wall.Chart => rel == 2 ? l31Chart : skate,
            L31.L31Wall.Locker => rel <= 2 ? l31Locker[rel - 1, Facing(t.Pier)] : l31Plain,
            _ => skate,
        };
    }

    private int L31Floor(in Tile t, int gx, int gz) => t.Zone switch
    {
        (byte)Zone.Hall => l31Galaxy,
        (byte)Zone.Crossing => l31Marble,
        (byte)Zone.Lobby or (byte)Zone.Skirt or (byte)Zone.Lounge => l31Retro,
        (byte)Zone.Rink => t.Variant == L31.L31Props.Dasher ? l31Board[0] : l31Board[System.Math.Min(3, (t.Detail & L31.L31SubMask) >> L31.L31SubShift)],
        (byte)Zone.Snack => l31Vinyl,
        (byte)Zone.Rental => l31CheckerA,
        (byte)Zone.Bath => l31CheckerB,
        (byte)Zone.Arcade => l31Cosmic,
        (byte)Zone.Cinema => l31Maroon,
        (byte)Zone.CarpetRoom => l31Glow,
        (byte)Zone.Empty => l31ConcDark,
        // Puddles where the HVAC leaks
        (byte)Zone.Hvac => (uint)(gx * 73856093 ^ gz * 19349663) % 5 < 2 ? l31ConcWet : l31ConcFloor,
        _ => l31ConcFloor,
    };

    private int L31Ceiling(in Tile t)
    {
        int state = t.Ceiling switch
        {
            CeilingKind.LightOn => 0,
            CeilingKind.LightLit => 1,
            CeilingKind.LightFlicker => 2,
            CeilingKind.LightOff => 3,
            _ => -1,
        };
        if (state >= 0)
        {
            int hue = t.Detail & L31.L31HueMask;
            if (hue < 6) return l31Tube[hue, state];
            return state switch { 0 => lightOnId, 1 => lightLitId, 2 => lightFlickerId, _ => lightOffId };
        }
        return t.Zone switch
        {
            (byte)Zone.Rink or (byte)Zone.Skirt or (byte)Zone.Hall or (byte)Zone.Crossing or (byte)Zone.Arcade or (byte)Zone.Cinema
                or (byte)Zone.CarpetRoom => l31CeilBlack,
            (byte)Zone.Lobby or (byte)Zone.Snack or (byte)Zone.Rental or (byte)Zone.Lounge or (byte)Zone.Bath => l31CeilAcoustic,
            _ => concreteCeilingId,
        };
    }

    private int L31Prop(in Tile t)
    {
        int f = Facing(t.Pier);
        return t.Variant switch
        {
            L31.L31Props.Dasher => l31Dasher,
            L31.L31Props.Cabinet => l31Cabinet[t.Stack % 6, f],
            L31.L31Props.DeadCabinet => l31DeadCab[f],
            L31.L31Props.Pinball => l31Pinball[f],
            L31.L31Props.Claw => l31Claw[f],
            L31.L31Props.SkeeLane => l31SkeeLane[f],
            L31.L31Props.SkeeTarget => l31SkeeTarget[f],
            L31.L31Props.PrizeCounter => l31Prize[f],
            L31.L31Props.Counter => l31Counter[System.Math.Min((int)t.Stack, 2), f],
            L31.L31Props.DjScreen => l31DjScreen[f],
            L31.L31Props.Vending => l31Vending[t.Stack & 1, f],
            L31.L31Props.Bin => l31Bin,
            L31.L31Props.Couch => l31Couch[t.Stack & 1, f],
            Props.Shelf => shelfIds[Facing(Opposite(t.Pier))],
            >= 40 and < Props.Limit => PropBlock(t),
            _ => 0,
        };
    }
}
