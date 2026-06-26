#!/usr/bin/env python3
"""
Render an NYT-discipline chart as a complete, standalone HTML page.

Produces a Times-grade artifact ready to publish via PublishWebpage. Charts
are rendered with Observable Plot (the d3-derived grammar Bostock co-authored
specifically for this kind of explanatory chart) plus the typography and color
discipline encoded in the sibling modules.

Usage:
    python3 render.py spec.json out.html

spec.json:
{
  "headline": "U.S. weekly deaths fell sharply in 2023",
  "subtitle": "Excess mortality, all causes. Source: CDC",
  "source": "Source: CDC Wonder. Chart: Hyperagent",
  "chart_type": "line" | "bar" | "area" | "scatter" | "small_multiples",
  "x_axis_label": "...",
  "y_axis_label": "Deaths per week",
  "data": [{"date": "2020-01-01", "value": 56000, "series": "U.S."}, ...],
  "hero_series": "U.S.",
  "annotations": [
    {"date": "2020-03-15", "value": 65000, "label": "Lockdowns begin"}
  ]
}
"""
import json
import sys
from pathlib import Path

# Import siblings
sys.path.insert(0, str(Path(__file__).parent))
from typography import GOOGLE_FONT_LINK, NYT_CSS  # noqa: E402
from palette import NYT_ACCENT, NYT_GREY_DARK  # noqa: E402


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{fonts}
<style>{css}
.chart-container {{ margin: 24px 0; }}
.chart-container svg {{ max-width: 100%; height: auto; display: block; }}
.annot-line {{ stroke: var(--nyt-text); stroke-width: 1; stroke-dasharray: 2 2; }}
.annot-label {{ fill: var(--nyt-text); font-weight: 500; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6"></script>
</head>
<body>
<div class="container">
  <h1 class="story-headline">{headline}</h1>
  <p class="dek">{subtitle}</p>
  <div class="chart-container" id="chart"></div>
  <div class="chart-source">{source}</div>
</div>
<script>
const spec = {spec_json};
const accent = {accent_json};
const grey = {grey_json};

function render() {{
  const data = spec.data.map(d => ({{
    ...d,
    date: d.date ? new Date(d.date) : d.date,
    value: +d.value,
  }}));

  const heroSeries = spec.hero_series;
  const isMulti = new Set(data.map(d => d.series)).size > 1;

  let marks = [];

  if (spec.chart_type === "line" || !spec.chart_type) {{
    marks.push(Plot.ruleY([0], {{ stroke: "#cccccc", strokeWidth: 1 }}));
    marks.push(Plot.line(data, {{
      x: "date",
      y: "value",
      stroke: isMulti ? "series" : () => accent,
      strokeWidth: d => (d.series === heroSeries ? 2.5 : 1.5),
    }}));
    if (isMulti && heroSeries) {{
      marks.push(Plot.text(
        data.filter(d => d.series === heroSeries),
        Plot.selectLast({{ x: "date", y: "value", text: "series", dx: 6, textAnchor: "start", fill: accent, fontWeight: 700 }})
      ));
    }}
  }} else if (spec.chart_type === "bar") {{
    marks.push(Plot.ruleY([0], {{ stroke: "#cccccc" }}));
    marks.push(Plot.barY(data, {{ x: "label", y: "value", fill: accent, sort: {{x: "-y"}} }}));
  }} else if (spec.chart_type === "scatter") {{
    marks.push(Plot.dot(data, {{ x: "x", y: "y", fill: accent, r: 4, fillOpacity: 0.7 }}));
  }} else if (spec.chart_type === "area") {{
    marks.push(Plot.areaY(data, {{ x: "date", y: "value", fill: accent, fillOpacity: 0.2 }}));
    marks.push(Plot.lineY(data, {{ x: "date", y: "value", stroke: accent, strokeWidth: 2 }}));
  }}

  // Annotations
  if (spec.annotations) {{
    spec.annotations.forEach(a => {{
      const ax = a.date ? new Date(a.date) : a.x;
      marks.push(Plot.ruleX([ax], {{ stroke: "#444", strokeDasharray: "2,2" }}));
      marks.push(Plot.text([{{x: ax, y: a.value, label: a.label}}], {{
        x: "x", y: "y", text: "label",
        dy: -8, fontWeight: 600, fontSize: 12, fill: "#121212",
        textAnchor: "start", dx: 4
      }}));
    }});
  }}

  const chart = Plot.plot({{
    width: 700,
    height: 380,
    marginLeft: 56,
    marginRight: 80,
    marginBottom: 36,
    style: {{
      background: "transparent",
      fontFamily: "Libre Franklin, sans-serif",
      fontSize: 12,
      color: "#666",
    }},
    x: {{ label: spec.x_axis_label || null, grid: false }},
    y: {{ label: spec.y_axis_label || null, grid: true, nice: true }},
    color: {{ legend: false }},
    marks,
  }});

  document.getElementById("chart").appendChild(chart);
}}

render();
</script>
</body>
</html>
"""


def render_html(spec: dict) -> str:
    return HTML_TEMPLATE.format(
        title=spec.get("headline", "Chart"),
        fonts=GOOGLE_FONT_LINK,
        css=NYT_CSS,
        headline=spec.get("headline", ""),
        subtitle=spec.get("subtitle", ""),
        source=spec.get("source", ""),
        spec_json=json.dumps(spec),
        accent_json=json.dumps(NYT_ACCENT),
        grey_json=json.dumps(NYT_GREY_DARK),
    )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render.py spec.json out.html")
        sys.exit(1)
    spec = json.loads(Path(sys.argv[1]).read_text())
    Path(sys.argv[2]).write_text(render_html(spec))
    print(f"Wrote {sys.argv[2]}")

