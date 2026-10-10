using Backrooms.Worldgen;

/// <summary>
/// The harness modes of the levels kept as 14-20, each written in the level's own file (RunStats.cs, FunStats.cs,
/// EndStats.cs, HubStats.cs, L974Stats.cs, L3999Stats.cs and L188Stats.cs): <c>mapgen &lt;seed&gt; &lt;cells&gt; runstats [args...]</c> and so on.
/// A level adds more modes of its own by answering more names in its own Modes method.
/// </summary>
static partial class LevelModes
{
    /// <summary>Runs the mode args[2] names, if one of the five levels has it; false if none does.</summary>
    public static bool Run(WorldLayout layout, string[] args) =>
        RunModes(layout, args[2], args) || FunModes(layout, args[2], args) || EndModes(layout, args[2], args)
        || HubModes(layout, args[2], args) || L974Modes(layout, args[2], args) || L3999Modes(layout, args[2], args)
        || L188Modes(layout, args[2], args);

    /// <summary>For the links mode: what to call a threshold of one of the five that is walked into, by its tile; null if it is none of theirs.</summary>
    public static string LinkLabel(Tile t) => RunLinkLabel(t) ?? FunLinkLabel(t) ?? EndLinkLabel(t) ?? HubLinkLabel(t) ?? L974LinkLabel(t)
        ?? L3999LinkLabel(t) ?? L188LinkLabel(t);

    /// <summary>For the links mode: the threshold kind (as its block's behaviour gives it) of a tile one of the five uses; null if none.</summary>
    public static string UseKind(Tile t) => RunUseKind(t) ?? FunUseKind(t) ?? EndUseKind(t) ?? HubUseKind(t) ?? L974UseKind(t) ?? L3999UseKind(t)
        ?? L188UseKind(t);
}
