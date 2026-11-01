using Backrooms.Thresholds;
using Vintagestory.API.Common;
using Vintagestory.API.Server;

namespace Backrooms.Regions;

/// <summary>
/// Level 23, "The Petrified Garden" (experimental, kept as level 28): the dev test of its ways in and out, which are all
/// walked into (a hollow tree in Level 37, Base Seedling's hollow tree, the Heart of Water's well), so a headless server
/// with no player can go through them: <c>/backrooms l23walk x z [rel]</c> (ThresholdSystem.L23.cs). This file is the
/// level's own.
/// </summary>
public class L23System : ModSystem
{
    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    // After CheatSystem (1.2), which has made /backrooms
    public override double ExecuteOrder() => 1.3;

    public override void StartServerSide(ICoreServerAPI api)
    {
        var parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Get("backrooms")?
            .BeginSubCommand("l23walk")
                .WithDescription("(Dev test) Goes through Level 23's walked way at x z (a hollow tree in Level 37, Base Seedling's hollow tree, the Heart of Water's well) "
                    + "as someone standing there would (rel: height over the level's floor; by default on the tile's floor): where it leads, its way back, and the blocks where it comes out")
                .WithArgs(parsers.Int("x"), parsers.Int("z"), parsers.OptionalDouble("rel"))
                .HandleWith(args =>
                {
                    int x = (int)args[0], z = (int)args[1];
                    double? rel = args.Parsers[2].IsMissing ? null : (double)args[2];
                    IServerPlayer player = args.Caller.Player as IServerPlayer;
                    int group = args.Caller.FromChatGroupId;
                    ThresholdSystem thresholds = api.ModLoader.GetModSystem<ThresholdSystem>();
                    thresholds?.L23WalkTest(x, z, rel, text =>
                    {
                        api.Logger.Notification("[backrooms] l23walk {0} {1}: {2}", x, z, text);
                        player?.SendMessage(group, text, EnumChatType.CommandSuccess);
                    });
                    return TextCommandResult.Success();
                })
            .EndSubCommand();
    }
}
