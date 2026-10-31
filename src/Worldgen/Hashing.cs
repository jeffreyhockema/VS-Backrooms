namespace Backrooms.Worldgen;

/// <summary>Stateless hashing so any part of the world can be recomputed independently from the seed.</summary>
public static class Hashing
{
    /// <summary>A 64-bit hash of a seed, two integer coordinates and a salt (each feature has its own salt); the same on every machine.</summary>
    public static ulong Hash(ulong seed, int a, int b, ulong salt)
    {
        ulong h = seed ^ (salt * 0x9E3779B97F4A7C15UL);
        h = Mix(h ^ (uint)a);
        h = Mix(h ^ ((ulong)(uint)b << 32));
        return h;
    }

    /// <summary>Uniform double in [0, 1).</summary>
    public static double Unit(ulong h) => (h >> 11) * (1.0 / (1UL << 53));

    /// <summary>One round of the SplitMix64 finaliser: spreads every bit of the input over the output.</summary>
    public static ulong Mix(ulong z)
    {
        z += 0x9E3779B97F4A7C15UL;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
        return z ^ (z >> 31);
    }

    /// <summary>Integer division rounding toward negative infinity (so cell indices step evenly across zero); right only for <paramref name="b"/> &gt; 0.</summary>
    public static int FloorDiv(int a, int b) => a >= 0 ? a / b : (a - b + 1) / b;

    /// <summary>The remainder of <see cref="FloorDiv"/>: never negative for a positive <paramref name="b"/>.</summary>
    public static int Mod(int a, int b) => ((a % b) + b) % b;
}

/// <summary>Small deterministic random sequence (SplitMix64).</summary>
public struct Rng
{
    private ulong state;

    public Rng(ulong seed) { state = seed; }

    public ulong NextULong()
    {
        state += 0x9E3779B97F4A7C15UL;
        ulong z = state;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
        return z ^ (z >> 31);
    }

    public double NextDouble() => Hashing.Unit(NextULong());

    /// <summary>Uniform int in [min, maxInclusive]. Returns min if the range is empty or inverted (max below min).</summary>
    public int Range(int min, int maxInclusive) => maxInclusive <= min ? min : min + (int)(NextULong() % (ulong)(maxInclusive - min + 1));

    public bool Chance(double p) => NextDouble() < p;
}
