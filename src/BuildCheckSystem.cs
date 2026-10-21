using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using ProtoBuf;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Server;

namespace Backrooms;

/// <summary>
/// Makes sure everyone in a multiplayer game runs the same copy of the mod. Vintage Story only compares the version
/// number in modinfo.json, so a player with an older build of the same version joins without complaint and simply
/// never sees what is new (entities, blocks), with no error anywhere. On joining, the client sends a fingerprint of its
/// copy (the compiled code and the names of the textures, shapes, sounds and other assets both sides load); if it
/// differs from the server's, the player is told
/// plainly, and so is everyone already playing.
/// </summary>
public class BuildCheckSystem : ModSystem
{
    private const string Channel = "backrooms-build";

    [ProtoContract]
    public class BuildInfo
    {
        [ProtoMember(1)] public string Version;
        [ProtoMember(2)] public string Fingerprint;
        [ProtoMember(3)] public int AssetCount;
    }

    private ICoreServerAPI sapi;
    private ICoreClientAPI capi;
    private BuildInfo own;

    /// <summary>Players whose build has been checked this session: a client only introduces itself once per join.</summary>
    private readonly HashSet<string> checkedPlayers = new();

    public override void Start(ICoreAPI api)
    {
        api.Network.RegisterChannel(Channel).RegisterMessageType<BuildInfo>();
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Network.GetChannel(Channel).SetMessageHandler<BuildInfo>(OnClientBuild);
        api.Event.PlayerDisconnect += player => checkedPlayers.Remove(player.PlayerUID);
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        IClientNetworkChannel channel = api.Network.GetChannel(Channel);
        channel.SetMessageHandler<BuildInfo>(OnServerBuild);
        // Introduce ourselves once the world is ready. A server whose copy has no build check has no such channel,
        // and sending on it would throw
        api.Event.LevelFinalize += () =>
        {
            if (channel.Connected) channel.SendPacket(Own(api));
            else api.Logger.Warning("[backrooms] The server's copy of the mod has no build check: it is an older build than this one");
        };
    }

    /// <summary>
    /// This side's build: the version (shown in the warning), and a fingerprint of its compiled code (the module id) and
    /// the names of its client-visible assets. The client's asset list also holds any resource pack's assets in the
    /// backrooms domain, so a pack that adds or renames one makes that client's fingerprint differ and triggers the warning.
    /// </summary>
    private BuildInfo Own(ICoreAPI api)
    {
        if (own != null) return own;
        // (Only the kinds of asset both sides load: block, item, entity and recipe definitions are server-only)
        string[] names = api.Assets.AllAssets.Keys.Where(a => a.Domain == "backrooms" && a.Category?.SideType == EnumAppSide.Universal)
            .Select(a => a.Path).OrderBy(p => p, StringComparer.Ordinal).ToArray();
        var text = new StringBuilder(GetType().Assembly.ManifestModule.ModuleVersionId.ToString());
        foreach (string name in names) text.Append('\n').Append(name);
        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(text.ToString()));
        own = new BuildInfo
        {
            Version = Mod.Info.Version,
            Fingerprint = Convert.ToHexString(hash, 0, 6),
            AssetCount = names.Length,
        };
        return own;
    }

    private void OnClientBuild(IServerPlayer player, BuildInfo theirs)
    {
        // Once per join: the packet comes from the client, and each mismatch is announced to everyone
        if (theirs == null || !checkedPlayers.Add(player.PlayerUID)) return;
        BuildInfo mine = Own(sapi);
        // The server always answers, so the client can say whether all is well
        sapi.Network.GetChannel(Channel).SendPacket(mine, player);
        if (theirs.Fingerprint == mine.Fingerprint) return;
        // (What the client says it is goes into chat markup, so keep it short and plain)
        string version = Plain(theirs.Version), fingerprint = Plain(theirs.Fingerprint);
        theirs = new BuildInfo { Version = version, Fingerprint = fingerprint, AssetCount = theirs.AssetCount };
        sapi.Logger.Warning("[backrooms] {0} joined with a different copy of the mod: {1} build {2} ({3} assets); the server has {4} build {5} ({6} assets)",
            player.PlayerName, theirs.Version, theirs.Fingerprint, theirs.AssetCount, mine.Version, mine.Fingerprint, mine.AssetCount);
        sapi.BroadcastMessageToAllGroups(
            $"<font color=\"#ff9060\">{player.PlayerName}'s copy of Backrooms: Survival Story differs from the server's (theirs: {theirs.Version}, {theirs.AssetCount} files; server: {mine.Version}, {mine.AssetCount} files). "
            + "They may not see entities or other new content until they install the server's copy.</font>", EnumChatType.Notification);
    }

    /// <summary>A client-sent string cut to 24 letters, digits and version punctuation.</summary>
    private static string Plain(string text)
    {
        if (string.IsNullOrEmpty(text)) return "?";
        var sb = new StringBuilder();
        foreach (char c in text)
        {
            if (sb.Length == 24) break;
            if (char.IsAsciiLetterOrDigit(c) || c is '.' or '-' or '+' or '_') sb.Append(c);
        }
        return sb.Length > 0 ? sb.ToString() : "?";
    }

    private void OnServerBuild(BuildInfo servers)
    {
        BuildInfo mine = Own(capi);
        if (servers.Fingerprint == mine.Fingerprint) return;
        string message = $"Your copy of Backrooms: Survival Story differs from this server's (yours: {mine.Version}, {mine.AssetCount} files; server: {servers.Version}, {servers.AssetCount} files). "
            + "Entities and other new content may be missing or broken for you. Ask the host for their copy of the mod and replace yours with it.";
        capi.ShowChatMessage($"<font color=\"#ff9060\">{message}</font>");
        capi.TriggerIngameError(this, "backrooms-mismatch", message);
    }
}
