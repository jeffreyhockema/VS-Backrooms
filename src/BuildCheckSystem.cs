using System;
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

    public override void Start(ICoreAPI api)
    {
        api.Network.RegisterChannel(Channel).RegisterMessageType<BuildInfo>();
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        sapi = api;
        api.Network.GetChannel(Channel).SetMessageHandler<BuildInfo>(OnClientBuild);
    }

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        api.Network.GetChannel(Channel).SetMessageHandler<BuildInfo>(OnServerBuild);
        // Introduce ourselves once the world is ready
        api.Event.LevelFinalize += () => api.Network.GetChannel(Channel).SendPacket(Own(api));
    }

    /// <summary>This side's fingerprint: the mod's version, its compiled code, and the names of its assets.</summary>
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
        BuildInfo mine = Own(sapi);
        // The server always answers, so the client can say whether all is well
        sapi.Network.GetChannel(Channel).SendPacket(mine, player);
        if (theirs.Fingerprint == mine.Fingerprint) return;
        sapi.Logger.Warning("[backrooms] {0} joined with a different copy of the mod: {1} build {2} ({3} assets); the server has {4} build {5} ({6} assets)",
            player.PlayerName, theirs.Version, theirs.Fingerprint, theirs.AssetCount, mine.Version, mine.Fingerprint, mine.AssetCount);
        sapi.BroadcastMessageToAllGroups(
            $"<font color=\"#ff9060\">{player.PlayerName}'s copy of The Backrooms differs from the server's (theirs: {theirs.Version}, {theirs.AssetCount} files; server: {mine.Version}, {mine.AssetCount} files). "
            + "They may not see entities or other new content until they install the server's copy.</font>", EnumChatType.Notification);
    }

    private void OnServerBuild(BuildInfo servers)
    {
        BuildInfo mine = Own(capi);
        if (servers.Fingerprint == mine.Fingerprint) return;
        string message = $"Your copy of The Backrooms differs from this server's (yours: {mine.Version}, {mine.AssetCount} files; server: {servers.Version}, {servers.AssetCount} files). "
            + "Entities and other new content may be missing or broken for you. Ask the host for their copy of the mod and replace yours with it.";
        capi.ShowChatMessage($"<font color=\"#ff9060\">{message}</font>");
        capi.TriggerIngameError(this, "backrooms-mismatch", message);
    }
}
