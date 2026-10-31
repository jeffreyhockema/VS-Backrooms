using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Server;

namespace Backrooms;

/// <summary>
/// Text for a player, in that player's own language. On a server a plain <c>Lang.Get</c> resolves in the server's
/// language, so every player would read chat, ingame errors and waypoint titles in the host's language; the mod ships
/// English and two Spanish files, so a message sent to a player goes through here.
/// </summary>
public static class Say
{
    /// <summary>The lang entry <paramref name="key"/> with <paramref name="args"/>, in <paramref name="player"/>'s language.</summary>
    public static string T(IServerPlayer player, string key, params object[] args) => Lang.GetL(player.LanguageCode, key, args);
}
