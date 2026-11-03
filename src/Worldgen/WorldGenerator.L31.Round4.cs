using Zone = Backrooms.Worldgen.WorldLayout.L31Zone;
using L31 = Backrooms.Worldgen.WorldLayout;

namespace Backrooms.Worldgen;

/// <summary>
/// Level 31, round 4 (tools/gen_31_round4.py): the rink's barrier as a thin padded wall along the boards' outer edge, its
/// piece and facing found from the neighbouring tiles (a straight run, a corner, or the post where two runs meet on the
/// oval's stair-steps), and the gaps' gates (a hinge post with the leaf swung open, or the sill between them).
/// </summary>
public sealed partial class WorldGenerator
{
    /// <summary>The barrier by [piece: straight, corner, post; side] and the gate by [piece: leafl, leafr, sill; side];
    /// the side is the skirt's (the barrier's outside).</summary>
    private readonly int[,] l31Barrier = new int[3, 4], l31RinkGate = new int[3, 4];
    /// <summary>Level 120's CRAC unit by [part: lower, upper, duct; side]; the slushie machine by side.</summary>
    private readonly int[,] l31Crac = new int[3, 4];
    private readonly int[] l31Slushie = new int[4], l31Stanchion = new int[5];
    private readonly int[,] l31Covered = new int[2, 4];
    private readonly int[] l31SkateBench = new int[4], l31Walker = new int[4];

    private void InitL31Round4()
    {
        string[] pieces = { "straight", "corner", "post" }, gate = { "leafl", "leafr", "sill" };
        l31Stanchion[0] = L31Block("l36-stanchion-none");
        for (int f = 0; f < 4; f++) l31Stanchion[1 + f] = L31Block("l36-stanchion-" + Sides[f], l31Stanchion[0]);
        for (int f = 0; f < 4; f++)
        {
            for (int k = 0; k < 3; k++) l31Barrier[k, f] = L31Block($"l31-barrier-{pieces[k]}-{Sides[f]}", k == 0 ? l31Dasher : 0);
            for (int k = 0; k < 3; k++) l31RinkGate[k, f] = L31Block($"l31-rinkgate-{gate[k]}-{Sides[f]}");
            l31Crac[0, f] = L31Block($"l120-crac-lower-{Sides[f]}", propIds[Props.AcUnit, 0, f]);
            l31Crac[1, f] = L31Block($"l120-crac-upper-{Sides[f]}");
            l31Crac[2, f] = L31Block($"l120-crac-duct-{Sides[f]}");
            l31Slushie[f] = L31Block($"l31-slushie-{Sides[f]}", propIds[Props.SnackCounter, 0, f]);
            l31Covered[0, f] = L31Block($"l31-covered-cabinet-{Sides[f]}", propIds[Props.CardboardBoxes, 0, f]);
            l31Covered[1, f] = L31Block($"l31-covered-pinball-{Sides[f]}", l31Covered[0, f]);
            l31SkateBench[f] = L31Block($"l31-skatebench-{Sides[f]}", propIds[Props.Bench, 0, f]);
            l31Walker[f] = L31Block($"l31-walker-{Sides[f]}");
        }
    }

    private bool L31OnRink(int gx, int gz) => layout.TileAt(gx, gz) is { Kind: TileKind.Floor, Zone: (byte)Zone.Rink };

    /// <summary>
    /// The barrier's or a gate's block on a rink tile one above its floor, or -1 where the tile has none. Facings (the side
    /// the skirt is on) are numbered as <see cref="Sides"/>: 0 north, 1 east, 2 south, 3 west. A corner piece is modelled
    /// with walls north and west (so facing k has walls on side k and the one before it), a post fills the north-west square.
    /// </summary>
    private int L31BarrierBlock(in Tile t, int gx, int gz)
    {
        bool n = !L31OnRink(gx, gz - 1), e = !L31OnRink(gx + 1, gz), s = !L31OnRink(gx, gz + 1), w = !L31OnRink(gx - 1, gz);
        int outs = (n ? 1 : 0) + (e ? 1 : 0) + (s ? 1 : 0) + (w ? 1 : 0);
        if (t.Variant == L31.L31Props.Dasher)
        {
            if (outs == 1) return l31Barrier[0, n ? 0 : e ? 1 : s ? 2 : 3];
            if (outs == 2)
            {
                if (n && w) return l31Barrier[1, 0];
                if (n && e) return l31Barrier[1, 1];
                if (e && s) return l31Barrier[1, 2];
                if (s && w) return l31Barrier[1, 3];
            }
            return l31Dasher;
        }
        if (t.Variant == L31.L31Props.Gate)
        {
            if (outs != 1) return -1;
            int k = n ? 0 : e ? 1 : s ? 2 : 3;
            // (the model's left end, seen from the rink, is its west end facing north; turned with it)
            var (lx, lz) = k switch { 0 => (gx - 1, gz), 1 => (gx, gz - 1), 2 => (gx + 1, gz), _ => (gx, gz + 1) };
            var (rx, rz) = k switch { 0 => (gx + 1, gz), 1 => (gx, gz + 1), 2 => (gx - 1, gz), _ => (gx, gz - 1) };
            if (layout.TileAt(lx, lz).Variant == L31.L31Props.Dasher) return l31RinkGate[0, k];
            if (layout.TileAt(rx, rz).Variant == L31.L31Props.Dasher) return l31RinkGate[1, k];
            return l31RinkGate[2, k];
        }
        if (t.Variant != 0 || outs != 0) return -1;
        // A post where two runs meet at this tile's corner (only the diagonal neighbour is off the boards)
        bool nw = !L31OnRink(gx - 1, gz - 1), ne = !L31OnRink(gx + 1, gz - 1), se = !L31OnRink(gx + 1, gz + 1), sw = !L31OnRink(gx - 1, gz + 1);
        if ((nw ? 1 : 0) + (ne ? 1 : 0) + (se ? 1 : 0) + (sw ? 1 : 0) != 1) return -1;
        return l31Barrier[2, nw ? 0 : ne ? 1 : se ? 2 : 3];
    }
}
