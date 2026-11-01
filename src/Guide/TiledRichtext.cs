using System;
using System.Collections.Generic;
using Cairo;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.GameContent;

namespace Backrooms;

/// <summary>
/// A rich text element that renders its text in horizontal tiles instead of one texture as tall as the page.
/// The vanilla element draws the whole page into a single Cairo surface and GL texture; our handbook pages are long
/// (the entity guide is about 11,500 px tall at GUI scale 1, more when scaled up), and many Linux GL drivers cap
/// textures at 16384 px (Cairo surfaces at 32767), so the texture fails and the page shows black with only the
/// links, which draw themselves, visible. Tiles of at most TileHeight px stay far below every limit.
/// The element keeps the vanilla layout (CalcHeightAndPositions, the same bounds and links); only the drawing differs.
/// The handbook finds it by the key "richtext", moves Bounds.fixedY to scroll it and sizes the scrollbar from its fixedHeight.
/// </summary>
public class TiledRichtext : GuiElementRichtext
{
    public const int TileHeight = 2048;

    private readonly List<LoadedTexture> tiles = new();

    public TiledRichtext(ICoreClientAPI capi, RichTextComponentBase[] components, ElementBounds bounds)
        : base(capi, components, bounds) { }

    public override void ComposeElements(Context ctxStatic, ImageSurface surfaceStatic)
    {
        ComposeTiles();
    }

    private void ComposeTiles()
    {
        DisposeTiles();
        ElementBounds forText = Bounds.CopyOnlySize();
        forText.fixedPaddingX = 0;
        forText.fixedPaddingY = 0;
        Bounds.CalcWorldBounds();
        int width = Math.Max(1, (int)Bounds.InnerWidth);
        int height = Math.Max(1, (int)Bounds.InnerHeight);
        for (int top = 0; top < height; top += TileHeight)
        {
            int h = Math.Min(TileHeight, height - top);
            var tile = new LoadedTexture(api);
            using (var surface = new ImageSurface(Format.Argb32, width, h))
            using (var ctx = new Context(surface))
            {
                ctx.SetSourceRGBA(0, 0, 0, 0);
                ctx.Paint();
                ctx.Translate(0, -top);
                ComposeFor(forText, ctx, surface);
                generateTexture(surface, ref tile);
            }
            tiles.Add(tile);
        }
    }

    public override void RenderInteractiveElements(float deltaTime)
    {
        double y = Bounds.renderY;
        foreach (LoadedTexture tile in tiles)
        {
            if (tile.TextureId != 0) Render2DTexture(tile.TextureId, (int)Bounds.renderX, (int)y, tile.Width, tile.Height, zPos, RenderColor);
            y += tile.Height;
        }
        MouseOverCursor = null;
        for (int i = 0; i < Components.Length; i++)
        {
            RichTextComponentBase comp = Components[i];
            comp.RenderColor = RenderColor;
            comp.RenderInteractiveElements(deltaTime, Bounds.renderX, Bounds.renderY, zPos);
            if (comp.UseMouseOverCursor(Bounds)) MouseOverCursor = comp.MouseOverCursor;
        }
    }

    private void DisposeTiles()
    {
        foreach (LoadedTexture tile in tiles) tile.Dispose();
        tiles.Clear();
    }

    public override void Dispose()
    {
        DisposeTiles();
        base.Dispose();
    }
}

/// <summary>
/// A handbook text page whose text is drawn by TiledRichtext. Replaces GuiHandbookTextPage for every page we add or
/// rewrite; page code, title, text, category and visibility are the same, so links, search and order do not change.
/// </summary>
public class TiledHandbookTextPage : GuiHandbookTextPage
{
    private ICoreClientAPI api;

    /// <summary>The page that replaces a vanilla text page: same code, title, text, category and visibility.</summary>
    public static TiledHandbookTextPage From(GuiHandbookTextPage old)
    {
        var page = new TiledHandbookTextPage
        {
            pageCode = old.pageCode,
            Title = old.Title,
            Text = old.Text,
            categoryCode = old.categoryCode,
            PageNumber = old.PageNumber,
            Visible = old.Visible,
        };
        return page;
    }

    public new void Init(ICoreClientAPI capi)
    {
        api = capi;
        base.Init(capi);   // localises Text (when it is a lang key) and caches the search title
    }

    public override void ComposePage(GuiComposer detailViewGui, ElementBounds textBounds, ItemStack[] allstacks, ActionConsumable<string> openDetailPageFor)
    {
        RichTextComponentBase[] comps = VtmlUtil.Richtextify(api, Text, CairoFont.WhiteSmallText().WithLineHeightMultiplier(1.2), null);
        detailViewGui.AddInteractiveElement(new TiledRichtext(api, comps, textBounds), "richtext");
    }
}
