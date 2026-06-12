#!/usr/bin/env python3
"""
Annotation linter — the single biggest delta between a default chart and an
NYT-grade chart is annotation. This module audits a chart spec and returns
specific, actionable fixes.

The NYT discipline:
  1. EVERY chart has a headline (declarative — tell me what to see).
  2. EVERY chart has a subtitle that names the unit and timeframe.
  3. EVERY chart has a source line.
  4. Lines are LABELED DIRECTLY at their endpoints, never via legend.
  5. The "hero" data point is annotated in-place ("peak: 4.2M cases, Jan 2022").
  6. Axis labels are written like English, not like spreadsheet column names.
  7. Y-axis 0 line is bold; gridlines are very pale; no axis spine.
  8. Where the data has a known inflection, ANNOTATE IT ("Lehman collapse",
     "vaccines available," "March 2020 lockdown") — context lives ON the chart.

Input: a dict describing the chart. Output: list of {severity, message, fix}.
"""

REQUIRED_FIELDS = {
    "headline":      "Declarative chart headline (not a label — a sentence: 'COVID deaths fell in 2023')",
    "subtitle":      "Subtitle naming unit + timeframe ('Weekly deaths, U.S., 2020-24')",
    "source":        "Source line ('Source: CDC. Note: ...')",
    "y_axis_unit":   "Y-axis unit ('Deaths per week', 'Share of vote, %')",
}

DISCIPLINE_CHECKS = [
    {
        "name": "direct_labels",
        "test": lambda c: c.get("series_count", 1) > 1 and not c.get("direct_labels"),
        "severity": "high",
        "message": "Multiple series shown via legend instead of direct labels.",
        "fix": "Label each line at its endpoint. Legends force the reader's eye back and forth — direct labels keep it on the data.",
    },
    {
        "name": "hero_color",
        "test": lambda c: c.get("series_count", 1) > 2 and c.get("colored_series", 0) == c.get("series_count"),
        "severity": "high",
        "message": "Every series is colored — no hero series.",
        "fix": "Color ONE series in the accent color. Demote the others to grey. The reader should know in one second which line matters.",
    },
    {
        "name": "annotation_for_inflection",
        "test": lambda c: c.get("has_known_inflection") and not c.get("inflection_annotated"),
        "severity": "high",
        "message": "A known historical inflection point in the data is not annotated.",
        "fix": "Add an inline label at the inflection ('March 2020: lockdowns', 'Sept 2008: Lehman'). Context lives ON the chart.",
    },
    {
        "name": "axis_label_humanized",
        "test": lambda c: c.get("y_axis_label", "").islower() or "_" in c.get("y_axis_label", ""),
        "severity": "medium",
        "message": "Y-axis label looks like a column name, not English.",
        "fix": "Replace 'unemployment_rate' with 'Unemployment rate (%)'. Write like a person, not a database.",
    },
    {
        "name": "zero_baseline",
        "test": lambda c: c.get("chart_type") == "bar" and c.get("y_min", 0) != 0,
        "severity": "high",
        "message": "Bar chart doesn't start at zero.",
        "fix": "Bar chart Y-axis MUST start at 0. Cropping it lies about magnitude. Use a dot plot if you need to crop.",
    },
    {
        "name": "gridline_chartjunk",
        "test": lambda c: c.get("gridlines_dark") or c.get("axis_spine"),
        "severity": "medium",
        "message": "Heavy gridlines or visible axis spines compete with the data.",
        "fix": "Gridlines pale (#e9e9e9). Remove the axis spine entirely. Only the data should carry weight.",
    },
    {
        "name": "color_ramp_choice",
        "test": lambda c: c.get("uses_rainbow") or c.get("uses_jet"),
        "severity": "critical",
        "message": "Rainbow / Jet color ramp detected.",
        "fix": "Replace with a monotonic-luminance ramp (sequential blue, viridis, or ColorBrewer). Rainbow lies about order to colorblind readers and to anyone printing greyscale.",
    },
    {
        "name": "tabular_nums",
        "test": lambda c: c.get("has_animated_values") and not c.get("uses_tabular_nums"),
        "severity": "low",
        "message": "Animated/changing numbers without tabular figures will jitter.",
        "fix": "Add `font-variant-numeric: tabular-nums;` so digit columns line up during transitions.",
    },
    {
        "name": "mobile_check",
        "test": lambda c: not c.get("tested_mobile"),
        "severity": "high",
        "message": "Chart hasn't been verified at 375px width (iPhone).",
        "fix": "NYT default-tests on iPhone first. If your annotations collide on mobile, rewrite them shorter.",
    },
    {
        "name": "interaction_required_for_value",
        "test": lambda c: c.get("requires_hover_for_critical_info"),
        "severity": "critical",
        "message": "Critical information is only visible on hover/click.",
        "fix": "Archie Tse rule: if you make the reader click, you'd better have a good reason. Crucial info MUST be visible without interaction. Use tooltips only for non-essential depth.",
    },
]


def audit(chart_spec):
    """Return a sorted list of issues."""
    issues = []
    for field, description in REQUIRED_FIELDS.items():
        if not chart_spec.get(field):
            issues.append({
                "severity": "high",
                "name": f"missing_{field}",
                "message": f"Missing {field}.",
                "fix": description,
            })
    for check in DISCIPLINE_CHECKS:
        try:
            if check["test"](chart_spec):
                issues.append({k: v for k, v in check.items() if k != "test"})
        except Exception:
            pass
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda i: severity_order.get(i["severity"], 4))
    return issues


def score(chart_spec):
    """0-100 NYT-discipline score for the chart spec."""
    issues = audit(chart_spec)
    penalties = {"critical": 25, "high": 10, "medium": 4, "low": 1}
    deduction = sum(penalties.get(i["severity"], 0) for i in issues)
    return max(0, 100 - deduction)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        # demo
        example = {
            "chart_type": "line",
            "series_count": 4,
            "colored_series": 4,
            "has_known_inflection": True,
            "inflection_annotated": False,
            "y_axis_label": "unemployment_rate",
            "tested_mobile": False,
        }
        print(json.dumps({"score": score(example), "issues": audit(example)}, indent=2))
    else:
        with open(sys.argv[1]) as f:
            spec = json.load(f)
        print(json.dumps({"score": score(spec), "issues": audit(spec)}, indent=2))

