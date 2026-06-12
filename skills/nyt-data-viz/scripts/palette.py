#!/usr/bin/env python3
"""
NYT-discipline color palettes for data visualization.

Principles distilled from NYT Graphics + Upshot practice (Bostock, Aisch, Cox,
Quealy, Pearce) and from ColorBrewer (Cynthia Brewer, Penn State), which the
NYT graphics desk has used as a basis for choropleths for over a decade:

1. NEVER use rainbow / HSV-equidistant ramps. Luminance must be monotonic
   on sequential ramps so colorblind and print-greyscale readers see the same
   order.
2. Diverging palettes are anchored on a meaningful zero/midpoint. Use them
   when "above vs. below" is the story (Republican vs. Democrat margin,
   profit vs. loss, hotter vs. colder than normal). Never use diverging
   when there is no natural midpoint.
3. Categorical palettes max out at ~7 distinguishable hues. Beyond 7,
   small-multiple by category instead of stuffing more colors in.
4. ONE accent color per chart for the "hero" series, with the rest at
   subdued gray. Don't color every line — color the one that matters.
5. Print-safe + colorblind-safe by default. Always test against deuteranopia
   simulation (red-green is the most common form).

Usage:
    from palette import nyt_palette
    nyt_palette("sequential", "blue", 7)
    nyt_palette("diverging", "red-blue", 9)
    nyt_palette("categorical", n=5)
    nyt_palette("hero", series_count=4)  # one accent + grays
"""

# Sequential ramps — ColorBrewer-derived, NYT-tuned.
# Light → dark, monotonic luminance, colorblind-safe.
SEQUENTIAL = {
    "blue":   ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"],
    "red":    ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"],
    "green":  ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#006d2c", "#00441b"],
    "purple": ["#fcfbfd", "#efedf5", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#54278f", "#3f007d"],
    "orange": ["#fff5eb", "#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c", "#f16913", "#d94801", "#a63603", "#7f2704"],
    "grey":   ["#ffffff", "#f0f0f0", "#d9d9d9", "#bdbdbd", "#969696", "#737373", "#525252", "#252525", "#000000"],
}

# Diverging palettes — anchored, perceptually balanced ends.
DIVERGING = {
    "red-blue":     ["#67001f", "#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7", "#d1e5f0", "#92c5de", "#4393c3", "#2166ac", "#053061"],
    "brown-teal":   ["#543005", "#8c510a", "#bf812d", "#dfc27d", "#f6e8c3", "#f5f5f5", "#c7eae5", "#80cdc1", "#35978f", "#01665e", "#003c30"],
    "purple-green": ["#40004b", "#762a83", "#9970ab", "#c2a5cf", "#e7d4e8", "#f7f7f7", "#d9f0d3", "#a6dba0", "#5aae61", "#1b7837", "#00441b"],
    "pink-yellow":  ["#8e0152", "#c51b7d", "#de77ae", "#f1b6da", "#fde0ef", "#f7f7f7", "#e6f5d0", "#b8e186", "#7fbc41", "#4d9221", "#276419"],
}

# Categorical — distinguishable up to 7 hues. Beyond, small-multiple.
# Tuned for the NYT "muted but distinct" feel, not the Tableau saturated default.
CATEGORICAL = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1"]

# NYT-house accent palette. The "hero" color paired with neutral grays.
NYT_ACCENT = "#d62728"  # signature NYT red — the "this is what matters" color
NYT_BLUE = "#1f77b4"
NYT_GREY_FAINT = "#bdbdbd"
NYT_GREY_DARK = "#525252"
NYT_BG = "#ffffff"
NYT_GRID = "#e9e9e9"
NYT_AXIS = "#cccccc"
NYT_TEXT = "#121212"
NYT_TEXT_SECONDARY = "#666666"


def _sample(ramp, n):
    """Pick n evenly-spaced colors from a 9-step ramp."""
    if n <= 1:
        return [ramp[len(ramp) // 2]]
    step = (len(ramp) - 1) / (n - 1)
    return [ramp[round(i * step)] for i in range(n)]


def nyt_palette(kind, name=None, n=5, series_count=None):
    """
    Return a list of hex colors following NYT discipline.

    kind: 'sequential' | 'diverging' | 'categorical' | 'hero'
    name: ramp name (for sequential/diverging)
    n: number of colors requested
    series_count: for 'hero' mode, total series count (one accent + grays)
    """
    if kind == "sequential":
        ramp = SEQUENTIAL.get(name or "blue")
        if ramp is None:
            raise ValueError(f"Unknown sequential ramp '{name}'. Choose from {list(SEQUENTIAL)}")
        return _sample(ramp, n)

    if kind == "diverging":
        ramp = DIVERGING.get(name or "red-blue")
        if ramp is None:
            raise ValueError(f"Unknown diverging ramp '{name}'. Choose from {list(DIVERGING)}")
        # diverging palettes should have an odd count so a neutral midpoint exists
        if n % 2 == 0:
            n += 1
        return _sample(ramp, n)

    if kind == "categorical":
        if n > 7:
            raise ValueError(
                "Categorical palettes max out at 7. With more categories, "
                "use small multiples (one chart per category) instead of more colors."
            )
        return CATEGORICAL[:n]

    if kind == "hero":
        total = series_count or n
        if total < 1:
            raise ValueError("Need at least 1 series.")
        # one accent + (total-1) shades of gray, lightest in the back
        accents = [NYT_ACCENT]
        greys = ["#cccccc", "#aaaaaa", "#888888", "#666666", "#444444"]
        return accents + greys[: total - 1]

    raise ValueError(f"Unknown palette kind '{kind}'.")


def css_variables():
    """Emit the NYT house colors as CSS custom properties."""
    return f""":root {{
  --nyt-bg: {NYT_BG};
  --nyt-text: {NYT_TEXT};
  --nyt-text-secondary: {NYT_TEXT_SECONDARY};
  --nyt-grid: {NYT_GRID};
  --nyt-axis: {NYT_AXIS};
  --nyt-accent: {NYT_ACCENT};
  --nyt-blue: {NYT_BLUE};
  --nyt-grey-faint: {NYT_GREY_FAINT};
  --nyt-grey-dark: {NYT_GREY_DARK};
}}"""


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: palette.py <kind> [name] [n]")
        print("  kinds: sequential, diverging, categorical, hero")
        sys.exit(1)
    kind = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    print(json.dumps(nyt_palette(kind, name, n)))

