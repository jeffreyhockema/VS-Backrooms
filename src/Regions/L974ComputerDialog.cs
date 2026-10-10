using Vintagestory.API.Client;
using Vintagestory.API.Config;

namespace Backrooms.Regions;

/// <summary>
/// The old computer in Kitty's House, logged in as Guest: the one e-mail waiting in Mail (how the house works and how
/// to leave it), the Internet's answer (marked on the map, server side), DreamSleep's loading screen, and the Owner's
/// account, which wants a password nobody knows.
/// </summary>
public class L974ComputerDialog : GuiDialog
{
    public override string ToggleKeyCombinationCode => null;

    public L974ComputerDialog(ICoreClientAPI capi) : base(capi)
    {
        Compose();
    }

    private void Compose()
    {
        string body =
            "<font weight=\"bold\">" + Lang.Get("backrooms:l974-pc-mail") + "</font><br>" + Lang.Get("backrooms:l974-mail-from") + "<br><br>"
            + Lang.Get("backrooms:l974-mail-body") + "<br><br>"
            + "<font weight=\"bold\">" + Lang.Get("backrooms:l974-pc-dreamsleep") + "</font><br>" + Lang.Get("backrooms:l974-dreamsleep") + "<br><br>"
            + "<font weight=\"bold\">" + Lang.Get("backrooms:l974-pc-internet") + "</font><br>" + Lang.Get("backrooms:l974-internet-searching") + "<br><br>"
            + "<i>" + Lang.Get("backrooms:l974-pc-owner") + "</i>";
        ElementBounds text = ElementBounds.Fixed(0, 30, 520, 440);
        ElementBounds bg = ElementBounds.Fill.WithFixedPadding(GuiStyle.ElementToDialogPadding);
        bg.BothSizing = ElementSizing.FitToChildren;
        bg.WithChildren(text);
        ElementBounds dialog = ElementStdBounds.AutosizedMainDialog.WithAlignment(EnumDialogArea.CenterMiddle);
        SingleComposer = capi.Gui.CreateCompo("backrooms-l974-computer", dialog)
            .AddShadedDialogBG(bg)
            .AddDialogTitleBar(Lang.Get("backrooms:l974-pc-title"), () => TryClose())
            .AddRichtext(body, CairoFont.WhiteSmallText(), text)
            .Compose();
    }
}
