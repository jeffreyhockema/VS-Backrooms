using System.Collections.Generic;
using Zone = Backrooms.Worldgen.WorldLayout.L120Zone;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 120, "Broken Servos" (experimental, kept as level 26), laid out in WorldLayout.Level120.cs, from its own
/// floor (<see cref="WorldGeometry.FloorFor"/>). Server rooms three blocks high on a dirty white floor (<c>l120-floor</c>,
/// raised-floor vents and lifted panels among the racks) under office ceiling tiles (<c>l120-ceiling</c>: plain, stained,
/// broken through), their fittings dead or smashed; walls of dirty yellow paper on rotting boards (<c>l120-wall</c>; soot
/// black in the hallways). Server racks (<c>l120-rack</c>, lower and upper block), wrecks (<c>l120-wreck</c>: toppled, or
/// torn open two high), cables spilled over the floor (<c>l120-spill</c>), cable trays (<c>l120-tray</c>), Level 2's ducts
/// along the passages, terminals (<c>l120-terminal</c>: dead, smashed, or whole and glowing) and office chairs. The White
/// Voids are <c>l120-void</c> (white floor, walls and ceiling, a glowing panel every third block, black fill round them),
/// with black doors standing open (<c>l120-voiddoor</c>); every pocket's way out is a broken window (<c>l120-window</c>).
/// Everything above the rooms is solid to the top of the band.
///
/// Every block of the level's own is looked up softly (<see cref="L120Block"/>): until its asset exists, what is missing is
/// drawn as the nearest existing block or left out, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L120RackStates = { "off", "leda", "ledb", "both", "gutted" };
    private readonly int[] l120Wall = new int[6], l120Floor = new int[4], l120Tray = new int[2], l120Ceil = new int[3], l120Spill = new int[2];
    private readonly int[,,] l120Rack = new int[2, 5, 4];
    private readonly int[,] l120Terminal = new int[3, 4], l120Window = new int[2, 4], l120VoidDoor = new int[2, 2];
    private readonly int[] l120Toppled = new int[4];
    private readonly int[,] l120Torn = new int[2, 4];
    private int l120Smashed, l120VoidFloor, l120VoidWall, l120VoidCeiling, l120VoidPanel, l120Black;
    private readonly HashSet<string> l120Missing = new();

    /// <summary>A block of the level's, or <paramref name="fallback"/> if its asset is not there (logged once).</summary>
    private int L120Block(string code, int fallback = 0)
    {
        if (modBlocks.TryGetValue(code, out int id)) return id;
        if (l120Missing.Add(code) && l120Missing.Count <= 20) api.Logger.Warning("[backrooms] Level 120: missing block backrooms:{0}", code);
        return fallback;
    }

    /// <summary>The level's block ids (called from the constructor).</summary>
    private void InitL120()
    {
        string[] walls = { "base", "stained", "rot", "soot", "rot2", "rot3" };
        int wallpaper = BlockId("backrooms:concretewall-plain");
        for (int i = 0; i < 6; i++) l120Wall[i] = L120Block("l120-wall-" + walls[i], i >= 4 ? 0 : wallpaper);
        if (l120Wall[4] == 0) l120Wall[4] = l120Wall[2];
        if (l120Wall[5] == 0) l120Wall[5] = l120Wall[2];
        string[] panels = { "clean", "dirty", "vent", "hole" };
        int concrete = BlockId("backrooms:concretefloor-plain");
        for (int i = 0; i < 4; i++) l120Floor[i] = L120Block("l120-floor-" + panels[i], concrete);
        l120Tray[0] = L120Block("l120-tray-we");
        l120Tray[1] = L120Block("l120-tray-ns");
        string[] ceilings = { "tile", "stained", "broken" };
        for (int i = 0; i < 3; i++) l120Ceil[i] = L120Block("l120-ceiling-" + ceilings[i], officeCeilingId);
        l120Smashed = L120Block("l120-ceiling-smashed", lightOffId);
        l120Spill[0] = L120Block("l120-spill-a");
        l120Spill[1] = L120Block("l120-spill-b", l120Spill[0]);
        l120VoidFloor = L120Block("l120-void-floor", concrete);
        l120VoidWall = L120Block("l120-void-wall", wallpaper);
        l120VoidCeiling = L120Block("l120-void-ceiling", officeCeilingId);
        l120VoidPanel = L120Block("l120-void-panel", lightOnId);
        l120Black = L120Block("l120-void-black", concreteId);
        for (int f = 0; f < 4; f++)
        {
            int old = L120Block("serverrack-" + Sides[f]);
            for (int s = 0; s < 5; s++)
            {
                l120Rack[0, s, f] = L120Block($"l120-rack-lower-{L120RackStates[s]}-{Sides[f]}", old);
                l120Rack[1, s, f] = L120Block($"l120-rack-upper-{L120RackStates[s]}-{Sides[f]}");
            }
            l120Terminal[0, f] = L120Block("l120-terminal-dead-" + Sides[f]);
            l120Terminal[1, f] = L120Block("l120-terminal-boot-" + Sides[f], l120Terminal[0, f]);
            l120Terminal[2, f] = L120Block("l120-terminal-smashed-" + Sides[f], l120Terminal[0, f]);
            l120Window[0, f] = L120Block("l120-window-lower-" + Sides[f]);
            l120Window[1, f] = L120Block("l120-window-upper-" + Sides[f]);
            l120Toppled[f] = L120Block("l120-wreck-toppled-" + Sides[f], l120Rack[0, 4, f]);
            l120Torn[0, f] = L120Block("l120-wreck-tornlower-" + Sides[f], l120Rack[0, 4, f]);
            l120Torn[1, f] = L120Block("l120-wreck-tornupper-" + Sides[f], l120Rack[1, 4, f]);
        }
        string[] ways = { "we", "ns" };
        for (int w = 0; w < 2; w++)
        {
            l120VoidDoor[0, w] = L120Block($"l120-voiddoor-lower-{ways[w]}");
            l120VoidDoor[1, w] = L120Block($"l120-voiddoor-upper-{ways[w]}");
        }
        // The ways in and out (WorldGenerator.L120.Links.cs)
        InitL120Links();
    }

    /// <summary>The material of a wall of the level: white in a void, soot black in a hallway, otherwise yellow paper (mostly yellowed, here and there stained, now and then torn off down to the rotting boards, in one of three tears).</summary>
    private int L120WallBlock(in Tile t, int gx, int gz, int rel)
    {
        switch (t.Zone)
        {
            case (byte)Zone.Void or (byte)Zone.VoidWall: return l120VoidWall;
            case (byte)Zone.Hallway or (byte)Zone.HallWall: return l120Wall[3];
        }
        double r = Hashing.Unit(Hashing.Hash(seed, gx, gz * 8 + rel, 0x2620));
        return l120Wall[r < 0.72 ? 0 : r < 0.91 ? 1 : r < 0.94 ? 2 : r < 0.97 ? 4 : 5];
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level120Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int top = 7; // walls are dressed up to here everywhere
        if (rel < 0 || rel > top) return concreteId;
        bool voidZone = t.Zone == (byte)Zone.Void;
        if (t.Kind != TileKind.Floor)
        {
            // The solid round a pocket's rooms is black, so a broken window looks out on nothing
            if (t.Zone == (byte)Zone.Fill) return l120Black;
            // A door back to the offices (WorldLayout.Level120.Links.cs)
            if (t.Kind == TileKind.Door && t.Under == Unders.L120ExitDoor && L120ExitDoorBlock(t, rel) is int exit and >= 0) return exit;
            if (t.Kind == TileKind.Doorway)
            {
                if (rel == 0) return voidZone ? l120VoidFloor : l120Floor[WorldLayout.L120PanelDirty];
                if (rel <= 2) return t.Variant == WorldLayout.L120VoidDoor ? l120VoidDoor[rel - 1, t.Detail & 1] : 0;
            }
            return L120WallBlock(t, gx, gz, rel);
        }
        int air = t.Height is >= 3 and <= 6 ? t.Height : 3;
        if (rel == 0) return voidZone ? l120VoidFloor : l120Floor[t.Depth & 3];

        // A broken window, in the line of a wall: the frame two high, the wall going on above it
        if (t.Variant == WorldLayout.L120Window)
            return rel <= 2 ? l120Window[rel - 1, Facing(t.Pier)] : L120WallBlock(t, gx, gz, rel);

        if (rel == air + 1)
        {
            if (voidZone) return t.Ceiling == CeilingKind.L120VoidPanel ? l120VoidPanel : l120VoidCeiling;
            switch (t.Ceiling)
            {
                case CeilingKind.LightOn: return lightOnId;
                case CeilingKind.LightLit: return lightLitId;
                case CeilingKind.LightOff: return lightOffId;
                case CeilingKind.LightFlicker: return lightFlickerId;
                case WorldLayout.L120Dim: return lampDimId;
                case WorldLayout.L120SmashedLamp: return l120Smashed;
            }
            // Office tiles, a few water-stained, now and then one fallen through
            double c = Hashing.Unit(Hashing.Hash(seed, gx, gz, 0x2621));
            return l120Ceil[c < 0.8 ? 0 : c < 0.95 ? 1 : 2];
        }
        if (rel > air) return voidZone ? l120Black : concreteId;

        // Trays and ducts under the ceiling
        if (rel == 3 && t.Overhead != 0)
        {
            int tray = t.Overhead - WorldLayout.L120TrayX;
            if (tray is 0 or 1) return l120Tray[tray];
        }
        if (rel == 3)
            switch (t.Pipe)
            {
                case WorldLayout.L120DuctX: return pipeRunXId;
                case WorldLayout.L120DuctZ: return pipeRunZId;
                case WorldLayout.L120DuctHub: return pipeHubId;
            }

        int facing = Facing(t.Pier);
        switch (t.Variant)
        {
            case WorldLayout.L120Rack:
                return rel <= 2 ? l120Rack[rel - 1, t.Detail <= 4 ? t.Detail : 0, facing] : 0;
            case WorldLayout.L120Wreck:
                if (t.Detail == WorldLayout.L120WreckTorn) return rel <= 2 ? l120Torn[rel - 1, facing] : 0;
                return rel == 1 ? l120Toppled[facing] : 0;
        }
        if (rel != 1)
            return t.Variant == 0 && t.Stack > 0 && rel <= t.Stack ? crateId : 0;
        return t.Variant switch
        {
            0 => t.SupplyBox ? BoxOf(t) : t.Stack > 0 ? crateId : 0,
            WorldLayout.L120Terminal => l120Terminal[t.Detail <= 2 ? t.Detail : 0, facing],
            WorldLayout.L120Chair => chairIds[facing],
            WorldLayout.L120Spill => l120Spill[(int)(Hashing.Hash(seed, gx, gz, 0x2622) & 1)],
            Props.Cabinet => cabinetIds[facing],
            Props.Drum => drumId,
            >= 40 and < Props.Limit => PropBlock(t),
            _ => 0,
        };
    }
}
