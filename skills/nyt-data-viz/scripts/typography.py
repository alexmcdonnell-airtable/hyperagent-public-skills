#!/usr/bin/env python3
"""
NYT-discipline typography for data visualization.

The NYT graphics desk uses a tight stack:
  - Cheltenham (display serif): headlines, dek
  - Franklin (Franklin Gothic, sans): chart labels, annotations, axis text
  - Imperial (text serif): body copy when story-length

Free web-font substitutes that match the proportions and tone:
  - Cheltenham → Playfair Display (Google) or Source Serif 4 (free, closer to NYT body)
  - Franklin Gothic → Libre Franklin (Google, an actual revival of the same metal type)
  - Imperial → Source Serif 4 (Adobe, OFL) or Lora

Discipline:
  - Headline: serif, large, dark — Cheltenham/Playfair, ~32–48px
  - Dek (subhead under headline): sans, gray — Franklin/Libre Franklin, ~16–18px
  - Chart title: sans-bold, ~17px
  - Chart subtitle: sans-regular, ~13px, --text-secondary
  - Axis label: sans-regular, ~12px, --text-secondary
  - Annotation: sans-regular, ~12-13px, dark — directly on the chart, no leader-line clutter
  - Source line: sans-regular, ~11px italic, --text-secondary
  - Numeric labels: tabular-nums, never proportional digits (jitters during transitions)
"""

GOOGLE_FONT_LINK = (
    "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">"
    "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>"
    "<link href=\"https://fonts.googleapis.com/css2?"
    "family=Libre+Franklin:wght@400;500;600;700&"
    "family=Playfair+Display:wght@700;900&"
    "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&"
    "display=swap\" rel=\"stylesheet\">"
)

NYT_CSS = """
:root {
  --nyt-bg: #ffffff;
  --nyt-text: #121212;
  --nyt-text-secondary: #666666;
  --nyt-grid: #e9e9e9;
  --nyt-axis: #cccccc;
  --nyt-accent: #d62728;
  --nyt-blue: #1f77b4;

  --font-display: "Playfair Display", "Cheltenham", Georgia, serif;
  --font-body: "Source Serif 4", "Imperial", Georgia, serif;
  --font-sans: "Libre Franklin", "Franklin Gothic", Helvetica, Arial, sans-serif;
}

body {
  background: var(--nyt-bg);
  color: var(--nyt-text);
  font-family: var(--font-body);
  font-size: 17px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  margin: 0;
}

.container {
  max-width: 680px;
  margin: 0 auto;
  padding: 40px 24px;
}

.chart-wrap {
  /* charts get a wider gutter when story is narrow */
  max-width: 720px;
  margin: 32px auto;
}

h1.story-headline {
  font-family: var(--font-display);
  font-weight: 900;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1.1;
  letter-spacing: -0.01em;
  margin: 0 0 12px;
}

.dek {
  font-family: var(--font-sans);
  font-weight: 400;
  font-size: 17px;
  color: var(--nyt-text-secondary);
  line-height: 1.4;
  margin: 0 0 28px;
}

.chart-title {
  font-family: var(--font-sans);
  font-weight: 700;
  font-size: 17px;
  line-height: 1.25;
  color: var(--nyt-text);
  margin: 0 0 4px;
}

.chart-subtitle {
  font-family: var(--font-sans);
  font-weight: 400;
  font-size: 13px;
  color: var(--nyt-text-secondary);
  margin: 0 0 16px;
}

.chart-source {
  font-family: var(--font-sans);
  font-style: italic;
  font-size: 11px;
  color: var(--nyt-text-secondary);
  margin-top: 8px;
}

.chart-note {
  font-family: var(--font-sans);
  font-size: 11px;
  color: var(--nyt-text-secondary);
  margin-top: 4px;
}

/* axis + chart text */
svg text,
.axis text,
.chart-label {
  font-family: var(--font-sans);
  font-size: 12px;
  fill: var(--nyt-text-secondary);
}

.chart-annotation {
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 500;
  fill: var(--nyt-text);
}

.chart-annotation--hero {
  font-weight: 700;
  fill: var(--nyt-accent);
}

/* numeric values — tabular figures so transitions don't jitter */
.tabular,
.value-label,
.axis text {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
}

/* axis styling — minimal, no chart-junk */
.axis line,
.axis path {
  stroke: var(--nyt-axis);
  shape-rendering: crispEdges;
}
.axis .domain { display: none; }  /* no axis spine */
.gridline {
  stroke: var(--nyt-grid);
  stroke-dasharray: none;
  shape-rendering: crispEdges;
}
"""


def emit_head(title="Chart"):
    """Emit a complete <head> block."""
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{GOOGLE_FONT_LINK}
<style>{NYT_CSS}</style>
</head>"""


if __name__ == "__main__":
    print(emit_head("NYT Chart"))

