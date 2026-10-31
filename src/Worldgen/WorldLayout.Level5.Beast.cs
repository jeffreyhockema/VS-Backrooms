namespace Backrooms.Worldgen;

public sealed partial class WorldLayout
{
    /// <summary>
    /// Whether a block column lies in one of Level 5's boiler halls, the hotel's hot, deep maintenance halls, where the
    /// Beast of Level 5 keeps (Entities.BeastSystem: he chooses his victims there far more often). A query only: it
    /// changes nothing laid out.
    /// </summary>
    public bool IsHotelBoilerHall(int x, int z)
    {
        int mx = MacroOf(x), mz = MacroOf(z);
        return LevelAt(mx, mz) == 5 && HotelZoneAt(mx, mz) == HotelZone.Boiler;
    }
}
