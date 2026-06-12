#!/usr/bin/env python3
"""
NYT-discipline chart-type selector.

Given the SHAPE of the data and the QUESTION being asked, recommend a chart
type with a one-line rationale and an "anti-pattern" warning. This encodes
the choices the NYT graphics desk makes again and again — gleaned from
Gregor Aisch's portfolio retrospective (line > choropleth > small multiples
> bar > scatter), Amanda Cox's talks, Archie Tse's scrollytelling rules,
and the published Upshot back-catalog.

Inputs (loose dict):
  data_shape: {
    "n_rows": int,
    "n_series": int,             # number of distinct lines/categories
    "x_type": "time" | "ordinal" | "quantitative" | "geo",
    "y_type": "quantitative" | "ordinal" | "categorical",
    "has_parts_of_whole": bool,
    "has_geography": bool,
  }
  question: free text or one of the canonical question types:
    "change_over_time" | "compare_categories" | "show_distribution"
    "show_correlation"  | "show_composition"   | "rank_items"
    "where_is_it"       | "how_likely"

Output: dict with `recommended`, `why`, `avoid`, `nyt_examples`.

Discipline embedded:
  - Default to LINE for time-series. Anything else needs a reason.
  - Default to SMALL MULTIPLES when n_series > 5 with a shared x-axis.
  - NEVER pie. Use bar or stacked-bar instead (Aisch, Cox both on record).
  - For ranked lists: bar (horizontal) NOT lollipop unless the dots carry value.
  - For "where," use a locator map FIRST, choropleth only if values vary geographically AND matter.
  - For correlation: scatter with annotated outliers, not just a cloud.
  - Diverging color requires a meaningful zero. If you can't name the zero, use sequential.
"""

NYT_PATTERNS = {
    "change_over_time": {
        "single_series": {
            "recommended": "line chart",
            "why": "One line, one accent color, direct end-of-line label. The dominant NYT chart.",
            "avoid": "Don't use an area chart unless the magnitude (filled space) is the point. Areas exaggerate.",
            "nyt_examples": ["Daily COVID cases tracker (2020-23)", "U.S. unemployment rate"],
        },
        "few_series": {
            "recommended": "line chart with one hero series in accent + rest in grey",
            "why": "Color the line the story is about. Demote the rest to context.",
            "avoid": "Don't color every line — readers can only follow one or two simultaneously.",
            "nyt_examples": ["Excess mortality by country", "Inflation: U.S. vs. peers"],
        },
        "many_series": {
            "recommended": "small multiples (one panel per series, shared axes)",
            "why": "Past ~5 lines, a single chart becomes spaghetti. NYT defaults to small multiples here.",
            "avoid": "Don't pile 12 lines on one axis. Don't use a 12-color legend.",
            "nyt_examples": ["State-by-state COVID waves", "Country GDP growth trajectories"],
        },
    },
    "compare_categories": {
        "few": {
            "recommended": "horizontal bar chart, sorted by value",
            "why": "Labels fit horizontally; readers compare bar lengths effortlessly.",
            "avoid": "Vertical bars force label rotation. Don't.",
            "nyt_examples": ["Most-watched shows", "Highest-grossing films"],
        },
        "many": {
            "recommended": "dot plot or small bar chart with named outliers",
            "why": "Annotate the head and tail; leave the middle as context.",
            "avoid": "Don't show all 50 states with 50 tiny bars when only 6 matter.",
            "nyt_examples": ["State teacher pay rankings"],
        },
    },
    "show_distribution": {
        "default": {
            "recommended": "histogram or strip-plot (jittered dots)",
            "why": "A density curve hides the actual observations; dots show them.",
            "avoid": "Don't use box plots in journalism — general readers don't read them.",
            "nyt_examples": ["How rich is your school district?"],
        },
    },
    "show_correlation": {
        "default": {
            "recommended": "scatter plot with annotated outliers and a reference line",
            "why": "A naked cloud of dots tells the reader nothing. Annotate 3-5 named points.",
            "avoid": "Don't add a regression line without labeling its R² or saying what it means.",
            "nyt_examples": ["Income vs. life expectancy by country"],
        },
    },
    "show_composition": {
        "default": {
            "recommended": "stacked bar (one bar per time-period or category)",
            "why": "Stacks read fast. Pies don't — and they fail completely with >4 slices.",
            "avoid": "NEVER pie chart. NEVER 3D pie. NEVER donut unless the hole shows a total.",
            "nyt_examples": ["Federal budget composition over time"],
        },
        "over_time": {
            "recommended": "stacked area chart with the most-changing component on top",
            "why": "Put the volatile category where the eye lands — the upper baseline.",
            "avoid": "Streamgraphs are pretty but unreadable. Use only for vibes, never for numbers.",
            "nyt_examples": ["Sources of U.S. electricity generation"],
        },
    },
    "rank_items": {
        "default": {
            "recommended": "ranked horizontal bar chart, sorted descending",
            "why": "Sort by the variable being compared, not alphabetical. Length = value.",
            "avoid": "Don't sort alphabetically — readers can't compare. Don't use lollipops for ranks.",
            "nyt_examples": ["Highest-paid CEOs"],
        },
    },
    "where_is_it": {
        "single_point": {
            "recommended": "locator map (zoom in, label nearby cities/landmarks)",
            "why": "Where is it relative to things readers know? That's the question.",
            "avoid": "Don't drop a point on a world map — there's no reference.",
            "nyt_examples": ["Locator maps for breaking news"],
        },
        "many_values": {
            "recommended": "choropleth (sequential ramp) or hex-binned dot map",
            "why": "Choropleth when geography matters AND values vary. Hex-bin when raw density matters.",
            "avoid": "Don't choropleth when the story is about absolute counts in dense areas — use circles sized by value.",
            "nyt_examples": ["County-level election maps", "Heat map of U.S. extreme heat days"],
        },
    },
    "how_likely": {
        "default": {
            "recommended": "probability bar / Needle-style gauge / 100-icon array",
            "why": "Conveys uncertainty visually. The Needle's jitter literally animated uncertainty.",
            "avoid": "Don't show a single point estimate without showing the range around it.",
            "nyt_examples": ["The Election Needle (2016, 2020, 2024)", "Senate forecast gauges"],
        },
    },
}


def select_chart(question_type, data_shape):
    """Return the NYT-style recommendation for this data + question."""
    rules = NYT_PATTERNS.get(question_type)
    if not rules:
        return {
            "recommended": "line chart (default)",
            "why": "When unsure, start with a line chart on a time x-axis. It's the NYT default.",
            "avoid": "Don't reach for novelty (sankey, chord, radial) until line/bar fail.",
            "nyt_examples": [],
        }

    n_series = data_shape.get("n_series", 1)
    has_time = data_shape.get("x_type") == "time"

    if question_type == "change_over_time":
        if n_series == 1:
            return rules["single_series"]
        if n_series <= 5:
            return rules["few_series"]
        return rules["many_series"]

    if question_type == "compare_categories":
        return rules["few"] if data_shape.get("n_rows", 0) < 15 else rules["many"]

    if question_type == "where_is_it":
        return rules["many_values"] if n_series > 1 else rules["single_point"]

    if question_type == "show_composition":
        return rules["over_time"] if has_time else rules["default"]

    return rules.get("default", list(rules.values())[0])


CANONICAL_QUESTIONS = list(NYT_PATTERNS.keys())


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: chart_selector.py <question_type> [json_data_shape]")
        print(f"  question_types: {CANONICAL_QUESTIONS}")
        sys.exit(1)
    q = sys.argv[1]
    shape = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    print(json.dumps(select_chart(q, shape), indent=2))

