---
name: nyt-data-viz
description: >-
  NYT-discipline data visualization. Applies the design rules of The New York Times
  graphics desk + Upshot — color, typography, annotation, chart-type selection — to make
  any chart render at Times grade. Use whenever generating charts, dashboards, reports,
  or data-driven webpages. Use whenever the agent generates a chart, dashboard, data-viz
  webpage, slide with data, or any artifact that contains charts. The skill encodes
  house-style rules that lift default Plotly/Chart.js output to NYT-grade.
---

## NYT-discipline Data Visualization

Produce New York Times / Upshot–grade charts and dashboards: the typography, color restraint, chart-type judgment, and annotation discipline of the NYT graphics desk — for **both** static charts (Observable Plot via `render.py`) and hand-built **interactive** D3 dashboards (via `interactive.py`).

### When to use
Any time you generate a chart, graph, dashboard, or data visualization and want it to read as editorial, trustworthy, and crafted — not a default library chart. Single charts, multi-panel dashboards, and scrollable data stories destined for PublishWebpage.

---

### The five core rules (every chart)
1. **Color.** One hero accent for the series that matters; everything else grey. Monotonic-luminance sequential ramps only — never rainbow/jet/HSV-equidistant. Diverging only with a meaningful zero. Categorical caps at ~7 hues; beyond that, small-multiple by category. (`palette.py`)
2. **Typography.** Playfair Display (display serif) + Libre Franklin (sans labels/annotation) + Source Serif 4 (body). `tabular-nums` on ALL numeric labels so digits don't jitter. (`typography.py`)
3. **Chart choice.** Line first for time; bar second; never pie; never dual y-axes; bars start at zero. Past ~5 series → small multiples. (`chart_selector.py`)
4. **Annotation.** Declarative headline (a sentence, not a label) + subtitle naming unit & timeframe + source line. Label series DIRECTLY at endpoints (no legends). Annotate inflections in place. Humanized axis labels. (`annotate.py`)
5. **Archie Tse rule.** Crucial info visible without interaction; mobile-test at 375px first.

### Scripts
- `palette.py`, `typography.py`, `chart_selector.py`, `annotate.py` — discipline helpers/linters.
- `render.py` — renders a STATIC chart as a standalone Observable Plot HTML page.
- `interactive.py` — **NYT chrome + interaction primitives** for hand-built D3 dashboards: `INTERACTIVE_CSS`, `HELPER_JS` (gliding tooltip + Voronoi hover), `scaffold(title, body_html, extra_js)`, and `PREPUBLISH_CHECKLIST`. Import it and build per-build render functions on top of `scaffold()`.

---

## Interactive dashboards — source material to study first
Map each panel to one real NYT graphic before building:
- **Connected scatterplot** — *"Driving Shifts Into Reverse"* (NYT, 2010). Works ONLY when BOTH axes move monotonically. http://steveharoz.com/research/connected_scatterplot/ · archive: https://archive.nytimes.com/www.nytimes.com/imagepages/2010/05/02/business/02metrics.html
- **Small multiples** — *"How Different Groups Spend Their Day"* (Carter, Cox, Quealy & Schoenfeld, 2009): direct labels per panel, shared axes, no legend. https://www.nytimes.com/interactive/2009/07/31/business/20080801-metrics-graphic.html
- **Beeswarm / distribution** — the COVID *vaccination beeswarm* (https://www.nytimes.com/interactive/2021/world/covid-vaccinations-tracker.html) and *"How 2016 Became Earth's Hottest Year"* scatter (https://www.nytimes.com/interactive/2017/01/18/science/earth/2016-hottest-year-on-record.html): one dot per record, one muted hue, mark only the summary; let the cloud argue.
- **Bump / ranking** — one accent for the leader, grey for the chase (palette.py "hero" rule applied to motion).

---

## Cardinal interaction rules (each prevents a bug observed and fixed in the field)

**Rule A — Hit-layer coordinate space.** The transparent hover `<rect>` MUST be appended to the SAME margin-translated `<g>` as the marks. Append it to the SVG root and `d3.pointer()` returns root coords while marks live in g-space, so `delaunay.find()` searches by the left-margin offset and highlights the WRONG mark / next clump over.
```js
// WRONG — overlay on svg root, marks in g(translate(m.left,m.top)) → off-by-margin
svg.append("rect").attr("x", m.left).attr("y", m.top) /* ... */;
// RIGHT — overlay in the same g as the marks; pointer == mark space
g.append("rect").attr("width", iw).attr("height", ih).attr("fill","transparent")
  .on("mousemove", function(ev){ const [mx,my] = d3.pointer(ev, this); /* find */ });
```

**Rule B — Proximity, not pixels.** Never make the user hover a 2–3px dot. Build a Delaunay over the marks and snap to the nearest.
```js
const pts = data.map(d => [x(d.k), y(d.v), d]);
const del = d3.Delaunay.from(pts, p=>p[0], p=>p[1]);
// inside mousemove: const i = del.find(mx, my); const d = pts[i][2];
```

**Rule C — Gliding, anchored tooltip.** Anchor the tooltip to the hovered mark's on-screen box and CSS-transition `left/top` so it slides between marks instead of teleporting under the cursor.
```css
.tooltip{position:fixed;opacity:0;transform:translate(-50%,calc(-100% - 12px));
  transition:opacity 140ms ease, left 200ms cubic-bezier(.22,.61,.36,1), top 200ms cubic-bezier(.22,.61,.36,1);}
```
```js
function tipAtNode(node, html){
  const r = node.getBoundingClientRect();
  tip.innerHTML = html; tip.style.left = (r.left+r.width/2)+"px"; tip.style.top = r.top+"px"; tip.style.opacity = 1;
}
```
For line/bump charts with no per-point node, move ONE highlight marker to the nearest point and anchor the tooltip to it:
```js
const hl = g.append("circle").attr("r",5).attr("fill","none").attr("stroke",INK).attr("opacity",0);
// on hover: hl.attr("cx",p[0]).attr("cy",p[1]).attr("opacity",1); tipAtNode(hl.node(), html);
```

**Rule D — Domain covers the max.** A hand-typed round cap pushes outliers off-canvas. (Real bug: a goals axis capped at 10 hid the 12-goal Switzerland 5–7 Austria 1954 match.)
```js
// WRONG: const x = d3.scaleLinear().domain([0,10]);
const maxTotal = d3.max(data, d=>d.total);
const x = d3.scaleLinear().domain([0, maxTotal]).range([0, iw]);  // add the maxTotal tick too
```

**Rule E — Legible annotations.** Give annotation text a paper-colored HALO and lift trough/edge labels off the data with a short leader line; never share a column with an axis tick.
```css
.anno,.anno-sub{paint-order:stroke fill;stroke:var(--panel);stroke-width:3px;stroke-linejoin:round}
```
```js
// leader line lifts a trough label clear of the axis + the curve
g.append("line").attr("class","anno-line").attr("x1",x(yr)).attr("y1",y(v)-7).attr("x2",x(yr)).attr("y2",y(v)-42);
g.append("text").attr("class","anno").attr("x",x(yr)).attr("y",y(v)-54).attr("text-anchor","middle").text("1990 · 2.2");
```

### Reusable hover helper (from `interactive.py`)
```js
function voronoiHover(g, pts, nodes, w, h, onEnter, onLeave){
  const del = d3.Delaunay.from(pts, p=>p[0], p=>p[1]);
  g.append("rect").attr("width",w).attr("height",h).attr("fill","transparent")   // Rule A
    .on("mousemove", function(ev){ const [mx,my]=d3.pointer(ev,this);            // Rule B
      const i = del.find(mx,my); onEnter(pts[i][2], i, nodes ? nodes[i] : null); })
    .on("mouseleave", onLeave);
}
```

### Panel patterns (condensed, from the worked example)
**Time-series line** — single hero line, dots, two haloed annotations, voronoi hover:
```js
g.append("path").datum(ed).attr("fill","none").attr("stroke",HERO).attr("stroke-width",2.4)
  .attr("d", d3.line().x(d=>x(d.year)).y(d=>y(d.gpg)).curve(d3.curveMonotoneX));
```
**Small multiples** — one `<svg>` per group in a CSS grid, shared y-domain, champion years as filled dots, nation label set directly on the panel (no legend).
**Beeswarm** — force layout per category band, single muted hue, era-average diamond:
```js
const sim = d3.forceSimulation(nodes)
  .force("x", d3.forceX(d=>x(d.total)).strength(1))
  .force("y", d3.forceY(d=>bandY[d.era]).strength(0.07))
  .force("collide", d3.forceCollide(3.2)).stop();
for (let i=0;i<180;i++) sim.tick();
```
**Bump** — `d3.scalePoint` over editions × rank scale; color top finishers, grey the rest; direct end-of-line nation labels; moving highlight marker for hover.

### Pre-publish checklist
1. Domain from `d3.max` (D). 2. Every hover rect in the marks' `<g>` (A). 3. Voronoi proximity (B). 4. Gliding anchored tooltip (C). 5. Halo + leader annotations (E). 6. Connected-scatter only if both axes monotonic. 7. Extract the inline `<script>`, run `node --check`, and `JSON.parse` the embedded data blob. 8. If a headless browser is reachable, screenshot at desktop + 375px and confirm every panel paints. 9. Cut editorial text to ~half the first-draft instinct.

### Worked example — "The World Cup, in four charts" (May 2026)
Four-panel dashboard from the **martj42 international football results** dataset (964 World Cup matches, 1930–2022): time-series (goals/game per edition), small multiples (eight nations' goal difference, champion years marked), beeswarm (every match by total goals, banded by era), and a bump chart (cumulative all-time points table). Each panel modeled on one of the four NYT references above and carried a one-line "craft note" citing its source. Rules A–E were all derived from bugs caught and fixed during that build.

### Output
Self-contained HTML for PublishWebpage. Publish embedded media (images/video) publicly first and reference the public URL in the HTML.
