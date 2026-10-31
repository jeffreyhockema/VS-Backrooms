using Backrooms.Worldgen;

/// <summary>
/// The harness modes of the levels kept as 14-27, each written in the level's own file (RunStats.cs, FunStats.cs,
/// EndStats.cs, HubStats.cs, L974Stats.cs, L3999Stats.cs, L188Stats.cs, L73Stats.cs, BasementStats.cs, L52Stats.cs,
/// L31Stats.cs and L120Stats.cs): <c>mapgen &lt;seed&gt; &lt;cells&gt; runstats [args...]</c> and so on.
/// A level adds more modes of its own by answering more names in its own Modes method.
/// </summary>
static partial class LevelModes
{
    /// <summary>Runs the mode args[2] names, if one of the seven levels has it; false if none does.</summary>
    public static bool Run(WorldLayout layout, string[] args) =>
        RunModes(layout, args[2], args) || FunModes(layout, args[2], args) || EndModes(layout, args[2], args)
        || HubModes(layout, args[2], args) || L974Modes(layout, args[2], args) || L3999Modes(layout, args[2], args)
        || L188Modes(layout, args[2], args)
        || L73Modes(layout, args[2], args) || BasementModes(layout, args[2], args) || L52Modes(layout, args[2], args)
        || L31Modes(layout, args[2], args) || L120Modes(layout, args[2], args);

    /// <summary>For the links mode: what to call a threshold of one of the seven that is walked into, by its tile; null if it is none of theirs.</summary>
    public static string LinkLabel(Tile t) => RunLinkLabel(t) ?? FunLinkLabel(t) ?? EndLinkLabel(t) ?? HubLinkLabel(t) ?? L974LinkLabel(t)
        ?? L3999LinkLabel(t) ?? L188LinkLabel(t) ?? L73LinkLabel(t) ?? BasementLinkLabel(t) ?? L52LinkLabel(t)
        ?? L31LinkLabel(t) ?? L120LinkLabel(t);

    /// <summary>For the links mode: the threshold kind (as its block's behaviour gives it) of a tile one of the seven uses; null if none.</summary>
    public static string UseKind(Tile t) => RunUseKind(t) ?? FunUseKind(t) ?? EndUseKind(t) ?? HubUseKind(t) ?? L974UseKind(t) ?? L3999UseKind(t)
        ?? L188UseKind(t) ?? L73UseKind(t) ?? BasementUseKind(t) ?? L52UseKind(t)
        ?? L31UseKind(t) ?? L120UseKind(t);
}
