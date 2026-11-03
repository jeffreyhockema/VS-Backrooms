namespace Backrooms.Worldgen;

/// <summary>
/// Level 23's skin (round 4, 2026-11-02): the generator's side of <c>WorldLayout.Level23.Skin.cs</c>. The trunks' outer bark
/// near eye height becomes relief blocks (<c>l23-barkface</c>), their feet get root flares (<c>l23-flare</c>) and their sides
/// broken limbs (<c>l23-limb</c>); fallen logs, stone mushroom caps and boulders get their rounded pieces
/// (<c>l23-logpart</c>, <c>l23-caprim</c>, <c>l23-boulderpart</c>). Models from tools/gen_23_r4.py.
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>Relief bark by bark (grey, red, pale, dark, green, aspen, moss), pattern (2) and facing.</summary>
    private readonly int[,,] l23BarkFace = new int[7, 2, 4];
    /// <summary>Root flares by kind (moss, green), form (full, root) and facing.</summary>
    private readonly int[,,] l23Flare = new int[2, 2, 4];
    /// <summary>Limbs by bark (grey, red, pale, dark, aspen), kind (stub, limb) and facing.</summary>
    private readonly int[,,] l23Limb = new int[5, 2, 4];
    /// <summary>Fallen logs' pieces by bark (as limbs), part (WorldLayout.L23LogPiece) and axis (x, z).</summary>
    private readonly int[,,] l23LogPart = new int[5, 11, 2];
    private readonly int[,] l23CapRim = new int[4, 4], l23BoulderPart = new int[3, 4];

    private void InitL23Skin()
    {
        string[] faceBarks = { "grey", "red", "pale", "dark", "green", "aspen", "moss" };
        string[] logBarks = { "grey", "red", "pale", "dark", "aspen" };
        string[] logParts = { "s1", "s2a", "s2b", "s2c", "s2d", "s3a", "s3b", "s3c", "s3d", "s3e", "s3f" };
        string[] capParts = { "side", "corner", "upper", "uppercorner" };
        string[] boulderParts = { "cap", "edge", "corner" };
        for (int f = 0; f < 4; f++)
        {
            for (int b = 0; b < 7; b++)
                for (int p = 0; p < 2; p++)
                    l23BarkFace[b, p, f] = Id($"l23-barkface-{faceBarks[b]}-{(p == 0 ? "a" : "b")}-{Sides[f]}");
            for (int k = 0; k < 2; k++)
                for (int form = 0; form < 2; form++)
                    l23Flare[k, form, f] = Id($"l23-flare-{(k == 0 ? "moss" : "green")}-{(form == 0 ? "full" : "root")}-{Sides[f]}");
            for (int b = 0; b < 5; b++)
                for (int k = 0; k < 2; k++)
                    l23Limb[b, k, f] = Id($"l23-limb-{logBarks[b]}-{(k == 0 ? "stub" : "limb")}-{Sides[f]}");
            for (int p = 0; p < 4; p++) l23CapRim[p, f] = Id($"l23-caprim-{capParts[p]}-{Sides[f]}");
            for (int p = 0; p < 3; p++) l23BoulderPart[p, f] = Id($"l23-boulderpart-{boulderParts[p]}-{Sides[f]}");
        }
        for (int b = 0; b < 5; b++)
            for (int p = 0; p < logParts.Length; p++)
                for (int a = 0; a < 2; a++)
                    l23LogPart[b, p, a] = Id($"l23-logpart-{logBarks[b]}-{logParts[p]}-{(a == 0 ? "x" : "z")}");
    }

    /// <summary>The index of a wood kind's bark among the relief barks (-1: not a trunk's bark).</summary>
    private static int L23FaceBark(byte w) => w switch
    {
        WorldLayout.L23BarkGrey => 0, WorldLayout.L23BarkRed => 1, WorldLayout.L23BarkPale => 2, WorldLayout.L23BarkDark => 3,
        WorldLayout.L23BarkGreen => 4, WorldLayout.L23BarkAspen => 5, _ => -1,
    };

    /// <summary>The index of a log's or limb's bark (grey, red, pale, dark, aspen).</summary>
    private static int L23LogBark(byte bark) => bark == WorldLayout.L23BarkAspen ? 4 : bark - 1;

    /// <summary>
    /// Dresses the wood of a column (after it is placed, before the caverns and tunnels cut into it): the trunks' outer bark
    /// over the ground in relief, the fallen logs', mushroom caps' and boulders' rounded pieces.
    /// </summary>
    private void L23DressWood(L23Column c, int gx, int gz, int ground)
    {
        int[] b = c.Blocks;
        for (int i = 0; i < L23Height; i++)
        {
            byte w = c.Wood[i];
            if (w == 0) continue;
            int rel = i + L23Low;
            if (rel <= ground) continue;
            if (w >= WorldLayout.L23LogFirst)
            {
                if (b[i] != l23Bark[w]) continue;
                int p = layout.L23LogPiece(gx, gz, rel);
                if (p >= 0) b[i] = l23LogPart[L23LogBark((byte)((w - WorldLayout.L23LogFirst) / 2)), p, (w - WorldLayout.L23LogFirst) & 1];
                continue;
            }
            if (w == WorldLayout.L23MushCap)
            {
                if (b[i] == l23Bark[w] && layout.L23CapPiece(gx, gz, rel, out int part, out ArchPier f)) b[i] = l23CapRim[part, Facing(f)];
                continue;
            }
            if (w == WorldLayout.L23Boulder)
            {
                if (b[i] == l23Bark[w] && layout.L23BoulderPiece(gx, gz, rel, out int part, out ArchPier f)) b[i] = l23BoulderPart[part, Facing(f)];
                continue;
            }
            if (rel > ground + WorldLayout.L23SkinHeight) continue;
            int bark = L23FaceBark(w);
            if (bark < 0) continue;
            if (b[i] == l23MossBark) bark = 6;
            else if (b[i] != l23Bark[w]) continue;
            if (!layout.L23SkinFace(gx, gz, rel, out ArchPier facing)) continue;
            int pattern = (int)(L23Hash(gx, gz * 31 + rel, 40) & 1);
            b[i] = l23BarkFace[bark, pattern, Facing(facing)];
        }
    }

    /// <summary>The air of a column at the end (after the tunnels): a root flare at a trunk's foot, a limb out of a trunk's side.</summary>
    private void L23DressAir(L23Column c, int gx, int gz, int ground, bool inTunnel)
    {
        int[] b = c.Blocks;
        int on = ground + 1 - L23Low;
        if (!inTunnel && on > 0 && on < L23Height && b[on] == 0 && !c.Water[on] && b[on - 1] != 0 && !c.Water[on - 1]
            && layout.L23FlareAt(gx, gz, ground + 1, out ArchPier facing, out bool giant, out int form))
            b[on] = l23Flare[giant ? 1 : 0, form, Facing(facing)];
        if (layout.L23LimbAt(gx, gz, out int rel, out ArchPier lf, out byte bark, out bool longLimb) && rel - L23Low is > 0 and < L23Height
            && b[rel - L23Low] == 0 && c.Wood[rel - L23Low] == 0)
            b[rel - L23Low] = l23Limb[L23LogBark(bark), longLimb ? 1 : 0, Facing(lf)];
    }
}
