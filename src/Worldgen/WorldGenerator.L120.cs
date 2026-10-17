using System.Collections.Generic;
using Zone = Backrooms.Worldgen.WorldLayout.L120Zone;

namespace Backrooms.Worldgen;

/// <summary>
/// Blocks for Level 120, "Server Room" (experimental, kept as level 26), laid out in WorldLayout.Level120.cs, from its own floor
/// (<see cref="WorldGeometry.FloorFor"/>). Rooms are three blocks high (a great hall six) on raised-floor panels
/// (<c>l120-floor</c>) under Level 4's office ceiling tiles, nearly every fitting dead; walls are dirty yellow wallpaper over
/// rotting boards (<c>l120-wall</c>). Server racks (<c>l120-rack</c>, lower and upper block) stand in rows, their LEDs the
/// light (a lit rack's upper block gives a little green, amber or cyan light); cable trays (<c>l120-tray</c>) hang over the
/// cold aisles, Level 2's ducts along the corridors; control rooms have terminals (<c>l120-terminal</c>) and office
/// chairs. Everything above the rooms is solid to the top of the band.
///
/// Every block of the level's own is looked up softly (<see cref="L120Block"/>): until its asset exists, what is missing is
/// drawn as the nearest existing block (walls, floors, the serverrack prop) or left out, logged once.
/// </summary>
public sealed partial class WorldGenerator
{
    private static readonly string[] L120RackStates = { "off", "leda", "ledb", "both", "gutted" };
    private readonly int[] l120Wall = new int[3], l120Floor = new int[4], l120Tray = new int[4];
    private readonly int[,,] l120Rack = new int[2, 5, 4];
    private readonly int[,] l120Terminal = new int[2, 4];
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
        string[] walls = { "base", "stained", "rot" };
        int wallpaper = BlockId("backrooms:concretewall-plain");
        for (int i = 0; i < 3; i++) l120Wall[i] = L120Block("l120-wall-" + walls[i], wallpaper);
        string[] panels = { "clean", "dirty", "vent", "hole" };
        int concrete = BlockId("backrooms:concretefloor-plain");
        for (int i = 0; i < 4; i++) l120Floor[i] = L120Block("l120-floor-" + panels[i], concrete);
        string[] trays = { "we", "ns", "rodwe", "rodns" };
        for (int i = 0; i < 4; i++) l120Tray[i] = L120Block("l120-tray-" + trays[i]);
        for (int f = 0; f < 4; f++)
        {
            int old = L120Block("serverrack-" + Sides[f]);
            for (int s = 0; s < 5; s++)
            {
                l120Rack[0, s, f] = L120Block($"l120-rack-lower-{L120RackStates[s]}-{Sides[f]}", old);
                l120Rack[1, s, f] = L120Block($"l120-rack-upper-{L120RackStates[s]}-{Sides[f]}");
            }
            l120Terminal[0, f] = L120Block("l120-terminal-dead-" + Sides[f]);
            l120Terminal[1, f] = L120Block("l120-terminal-lit-" + Sides[f], l120Terminal[0, f]);
        }
    }

    /// <summary>One block of a column of the level, <paramref name="rel"/> above its floor.</summary>
    private int Level120Block(in Tile t, int gx, int gz, int rel, out int fluid)
    {
        fluid = 0;
        const int top = 7; // a great hall's ceiling; walls are dressed up to it everywhere
        if (rel < 0 || rel > top) return concreteId;
        if (t.Kind != TileKind.Floor)
        {
            if (rel == 0) return t.Kind == TileKind.Doorway ? l120Floor[WorldLayout.L120PanelDirty] : concreteId;
            if (t.Kind == TileKind.Doorway && rel <= 2) return 0;
            // The paper: mostly yellowed, here and there stained, now and then torn off down to the rotting boards
            double r = Hashing.Unit(Hashing.Hash(seed, gx, gz * 8 + rel, 0x2620));
            return l120Wall[r < 0.72 ? 0 : r < 0.92 ? 1 : 2];
        }
        int air = t.Height is >= 3 and <= 6 ? t.Height : 3;
        if (rel == 0) return l120Floor[t.Depth & 3];
        if (rel == air + 1)
            return t.Ceiling switch
            {
                CeilingKind.LightOn => lightOnId,
                CeilingKind.LightLit => lightLitId,
                CeilingKind.LightOff => lightOffId,
                CeilingKind.LightFlicker => lightFlickerId,
                WorldLayout.L120Dim => lampDimId,
                _ => officeCeilingId,
            };
        if (rel > air) return concreteId;

        // Trays and ducts under the ceiling
        if (rel >= 3 && t.Overhead != 0)
        {
            int low = t.Overhead - WorldLayout.L120TrayX, high = t.Overhead - WorldLayout.L120HighTrayX;
            if (rel == 3 && low is 0 or 1) return l120Tray[low];
            if (rel > 3 && low is 0 or 1) return l120Tray[2 + low]; // a great hall's lower trays hang on rods from its ceiling
            if (rel == 6 && high is 0 or 1) return l120Tray[high];
        }
        if (rel == 3)
            switch (t.Pipe)
            {
                case WorldLayout.L120DuctX: return pipeRunXId;
                case WorldLayout.L120DuctZ: return pipeRunZId;
                case WorldLayout.L120DuctHub: return pipeHubId;
            }

        int facing = Facing(t.Pier);
        if (t.Variant == WorldLayout.L120Rack)
            return rel <= 2 ? l120Rack[rel - 1, t.Detail <= 4 ? t.Detail : 0, facing] : 0;
        if (rel != 1)
            return t.Variant == 0 && t.Stack > 0 && rel <= t.Stack ? crateId : 0;
        return t.Variant switch
        {
            0 => t.Stack > 0 ? crateId : 0,
            WorldLayout.L120Terminal => l120Terminal[t.Detail == 1 ? 1 : 0, facing],
            WorldLayout.L120Chair => chairIds[facing],
            Props.Cabinet => cabinetIds[facing],
            Props.Drum => drumId,
            >= 40 and < Props.Limit => PropBlock(t),
            _ => 0,
        };
    }
}
