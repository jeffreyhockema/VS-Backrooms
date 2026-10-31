using System;
using System.Collections.Generic;
using Backrooms.Cheats;

namespace Backrooms.Worldgen;

public partial class WorldLayout
{
    /// <summary>
    /// The level's showcase spots for the review screenshots (see <see cref="Showcase"/>): its set pieces and the places
    /// its creatures keep to, each a free standing spot with the way to look. Placeholder: the level's builder fills it in.
    /// </summary>
    public IEnumerable<Showcase.Spot> L73ShowcaseSpots(WorldGeometry geometry) => Array.Empty<Showcase.Spot>();
}
