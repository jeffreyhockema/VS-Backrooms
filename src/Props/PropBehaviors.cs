using System.Linq;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Datastructures;

namespace Backrooms.Props;

/// <summary>
/// The behaviour of a prop that is used with {rightmouse}: the client says yes (so the use goes to the server) and the server
/// does it (<see cref="PropSystem"/>). Added at load time to the old blocks (<see cref="PropSystem.AssetsFinalize"/>).
/// </summary>
public abstract class BlockBehaviorProp : BlockBehavior
{
    protected BlockBehaviorProp(Block block) : base(block) { }

    /// <summary>The interaction help lines: (lang key, the item to hold or null).</summary>
    protected abstract (string Key, string Item)[] Help { get; }

    /// <summary>On the server: does it.</summary>
    protected abstract void Use(PropSystem props, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel);

    public override bool OnBlockInteractStart(IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel, ref EnumHandling handling)
    {
        // (Sneaking past it: a block placed against it, or whatever else the hand would do)
        if (byPlayer?.Entity?.Controls.ShiftKey == true || !OnItsFace(blockSel)) return false;
        handling = EnumHandling.PreventSubsequent;
        if (world.Side == EnumAppSide.Server && PropSystem.Server is { } props) Use(props, world, byPlayer, blockSel);
        return true;
    }

    /// <summary>
    /// Whether the use is on the prop: a wall decoration is one face of a whole wall block (its side variant), and the other
    /// faces are plain wall, where the hand does what it always did (places a block against it).
    /// </summary>
    private bool OnItsFace(BlockSelection sel)
    {
        string side = block.Variant?["side"];
        if (side == null || !block.FirstCodePart().Contains("deco")) return true;
        return sel?.Face == null || sel.Face.Code == side;
    }

    public override WorldInteraction[] GetPlacedBlockInteractionHelp(IWorldAccessor world, BlockSelection selection, IPlayer forPlayer, ref EnumHandling handling)
    {
        if (!OnItsFace(selection)) return System.Array.Empty<WorldInteraction>();
        return Help.Select(h => new WorldInteraction
        {
            ActionLangCode = "backrooms:" + h.Key,
            MouseButton = EnumMouseButton.Right,
            Itemstacks = h.Item == null || world.GetItem(new AssetLocation(h.Item)) is not { } item ? null : new[] { new ItemStack(item) },
        }).ToArray();
    }
}

/// <summary>A fire alarm pull station (or alarm bell, or the hotel's fire-hose cabinet): pulled, it rings and the sprinklers spray.</summary>
public class BlockBehaviorFireAlarm : BlockBehaviorProp
{
    public BlockBehaviorFireAlarm(Block block) : base(block) { }

    protected override (string, string)[] Help => new[] { (block.Variant?["decor"] == "alarmbell" ? "blockhelp-testbell" : "blockhelp-pullalarm", (string)null) };

    protected override void Use(PropSystem props, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel) => props.PullAlarm(blockSel.Position, byPlayer);
}

/// <summary>A steam valve: turned, the nearest steam pipe blasts a scalding jet across the passage.</summary>
public class BlockBehaviorSteamValve : BlockBehaviorProp
{
    public BlockBehaviorSteamValve(Block block) : base(block) { }

    protected override (string, string)[] Help => new[] { ("blockhelp-turnvalve", (string)null) };

    protected override void Use(PropSystem props, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel) => props.TurnValve(blockSel.Position, byPlayer);
}

/// <summary>A breaker box, an electrical panel or a knife switch: thrown, the lights round it die; a fuse brings them back.</summary>
public class BlockBehaviorBreaker : BlockBehaviorProp
{
    public BlockBehaviorBreaker(Block block) : base(block) { }

    protected override (string, string)[] Help => new[] { ("blockhelp-tripbreaker", (string)null), ("blockhelp-fitfuse", PropSystem.FuseCode) };

    protected override void Use(PropSystem props, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel) => props.UseBreaker(blockSel.Position, byPlayer, false);
}

/// <summary>A car (its drawn corner or a collider of it): struck, its alarm blares.</summary>
public class BlockBehaviorCarAlarm : BlockBehaviorProp
{
    public BlockBehaviorCarAlarm(Block block) : base(block) { }

    protected override (string, string)[] Help => new[] { ("blockhelp-strikecar", (string)null) };

    protected override void Use(PropSystem props, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel) => props.StrikeCar(blockSel.Position, byPlayer);
}

/// <summary>A radio or a turntable: switched on, it plays for a while; switched again, off.</summary>
public class BlockBehaviorRadio : BlockBehaviorProp
{
    public BlockBehaviorRadio(Block block) : base(block) { }

    protected override (string, string)[] Help => new[] { ("blockhelp-radioon", (string)null) };

    protected override void Use(PropSystem props, IWorldAccessor world, IPlayer byPlayer, BlockSelection blockSel) => props.SwitchRadio(blockSel.Position, block, byPlayer);
}
