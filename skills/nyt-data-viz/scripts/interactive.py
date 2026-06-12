#!/usr/bin/env python3
"""
NYT-discipline INTERACTIVE dashboards (hand-built D3).

The sibling modules (palette / typography / chart_selector / annotate / render)
encode the discipline for *static* Observable Plot charts. This module covers the
case render.py does not: a hand-built, multi-panel **interactive** dashboard in raw
D3 — where almost every craft failure actually happens.

It provides:
  1. INTERACTIVE_CSS  — the NYT chrome (paper bg, type stack, annotation HALO,
     gliding tooltip, panel / kpi / craft-note styling).
  2. HELPER_JS        — the two interaction primitives every panel shares:
     `tipAtNode()` (a gliding, object-anchored tooltip) and `voronoiHover()`
     (proximity hit-testing, so the cursor only has to get *close*).
  3. scaffold()       — emits the complete <head>, CDN d3, CSS, tooltip node and
     helper JS, so a dashboard starts from the correct base.
  4. A documented checklist of the bug-lessons that this skill exists to prevent.

Design rules distilled from four NYT graphics (study these before building):
  - Connected scatterplot — "Driving Shifts Into Reverse" (a connected scatter ONLY
    works when BOTH axes move monotonically; if either axis repeats values, use a line).
    http://steveharoz.com/research/connected_scatterplot/
  - Small multiples — "How Different Groups Spend Their Day" (Carter, Cox, Quealy,
    Schoenfeld, 2009): direct labels on each panel, shared axes, no legend.
    https://www.nytimes.com/interactive/2009/07/31/business/20080801-metrics-graphic.html
  - Beeswarm / distribution — the COVID vaccination beeswarm + "hottest year" scatter:
    one dot per record, a single muted hue, mark only the summary; let the cloud argue.
    https://www.nytimes.com/interactive/2017/01/18/science/earth/2016-hottest-year-on-record.html
  - Bump / ranking — one accent for the leader, grey for the chase (palette.py "hero" rule,
    applied to motion).

CARDINAL INTERACTION RULES (each prevents a real, observed bug):
  A. The hover hit-layer (transparent <rect>) MUST be appended to the SAME translated
     <g> as the marks. Appending it to the SVG root while marks sit in a margin-translated
     group makes delaunay.find() search N px to the side and highlight the WRONG mark.
  B. Hit-test with a Voronoi/Delaunay (`d3.Delaunay.from(pts).find(mx,my)`), never bare dot
     targets — 2-3px circles are impossible to hover.
  C. Anchor the tooltip to the hovered mark's getBoundingClientRect() and CSS-transition
     left/top (~200ms) so it GLIDES into place. Never pin it to the raw cursor.
  D. The value scale domain must cover d3.max(data) — a hand-typed round cap pushes outliers
     off the canvas. Compute the max; add its tick.
  E. Give annotation text a paper-colored HALO (paint-order: stroke fill) and lift labels off
     the data with a short leader line; never let a label share a column with an axis tick.
"""

# ---------------------------------------------------------------------------
# 1. CSS — the NYT chrome for an interactive dashboard
# ---------------------------------------------------------------------------
INTERACTIVE_CSS = """
:root {
  --bg:#faf8f4; --panel:#ffffff; --ink:#1a1a1a; --ink2:#56524b; --ink3:#8a857c;
  --rule:#e6e0d5; --grid:#eee9de; --hero:#b5232e; --hero-soft:#e7aab0;
  --grey-line:#c3bdb2; --grey-dark:#76716a;
  --font-display:"Playfair Display",Georgia,serif;
  --font-body:"Source Serif 4",Georgia,serif;
  --font-sans:"Libre Franklin",Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box} html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:var(--font-body);font-size:17px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:40px 28px 80px}
h1{font-family:var(--font-display);font-weight:900;font-size:clamp(34px,6vw,62px);line-height:1.02;letter-spacing:-.02em;margin:0 0 14px}
h2{font-family:var(--font-display);font-weight:700;font-size:clamp(23px,3.2vw,32px);line-height:1.12;margin:0 0 8px;max-width:760px}
h2 em{font-style:italic;color:var(--hero)}
.dek,.panel-dek{font-family:var(--font-body);color:var(--ink2);line-height:1.55;max-width:620px}
.chartcard{background:var(--panel);border:1px solid var(--rule);border-radius:5px;padding:22px 24px 16px}
svg{display:block;max-width:100%;height:auto;overflow:visible} text{font-family:var(--font-sans)}
.axis text{font-size:11.5px;fill:var(--ink2);font-variant-numeric:tabular-nums}
.axis line,.axis path{stroke:var(--rule);shape-rendering:crispEdges}.axis .domain{display:none}
.grid line{stroke:var(--grid);shape-rendering:crispEdges}.grid .domain{display:none}
.axis-title{font-size:11.5px;fill:var(--ink3);font-weight:500}
/* RULE E: annotation halo so labels never fight the data */
.anno,.anno-sub{paint-order:stroke fill;stroke:var(--panel);stroke-width:3px;stroke-linejoin:round}
.anno{font-size:11.5px;fill:var(--ink);font-weight:600}
.anno-sub{font-size:10.5px;fill:var(--ink2);font-weight:400}
.anno-line{stroke:var(--ink3);stroke-width:.8}
/* RULE C: gliding, object-anchored tooltip */
.tooltip{position:fixed;pointer-events:none;z-index:999;left:0;top:0;background:rgba(20,20,20,.95);color:#fff;
  padding:8px 11px;font-family:var(--font-sans);font-size:12px;line-height:1.45;border-radius:4px;
  transform:translate(-50%,calc(-100% - 12px));opacity:0;white-space:nowrap;max-width:300px;
  transition:opacity 140ms ease,left 200ms cubic-bezier(.22,.61,.36,1),top 200ms cubic-bezier(.22,.61,.36,1)}
.tooltip .t-hd{font-weight:700;margin-bottom:1px}.tooltip .t-accent{color:var(--hero-soft);font-variant-numeric:tabular-nums}
.craftnote{margin-top:12px;padding-top:10px;border-top:1px dashed var(--rule);font-family:var(--font-sans);
  font-size:11.5px;line-height:1.55;color:var(--ink2);max-width:760px}
.craftnote .tag{display:inline-block;font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--hero);margin-right:8px;border:1px solid var(--hero-soft);border-radius:3px;padding:1px 6px}
.craftnote a{color:var(--ink);text-decoration:underline;text-underline-offset:2px}.craftnote a:hover{color:var(--hero)}
"""

GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Libre+Franklin:wght@400;500;600;700&'
    'family=Playfair+Display:ital,wght@0,700;0,900;1,700&'
    'family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">'
)

# ---------------------------------------------------------------------------
# 2. JS — the two shared interaction primitives (RULES A, B, C)
# ---------------------------------------------------------------------------
HELPER_JS = r"""
// --- gliding, object-anchored tooltip (RULE C) ---
const tip = document.getElementById("tooltip");
function tipAtNode(node, html){
  const r = node.getBoundingClientRect();
  tip.innerHTML = html;
  tip.style.left = (r.left + r.width/2) + "px";
  tip.style.top  = r.top + "px";
  tip.style.opacity = 1;
}
function hideTip(){ tip.style.opacity = 0; }

// --- proximity hover (RULES A + B) ---
// g            : the margin-translated <g> that ALSO holds the marks
// pts          : [[x,y,datum], ...] in g-space
// nodes        : the on-screen mark nodes, SAME order as pts (for highlight + anchor)
// w,h          : inner width/height of the plot area
// onEnter(d,i,node), onLeave()  : caller-supplied highlight + tooltip
function voronoiHover(g, pts, nodes, w, h, onEnter, onLeave){
  const del = d3.Delaunay.from(pts, p=>p[0], p=>p[1]);
  g.append("rect")               // RULE A: rect is a child of g, so pointer == mark space
    .attr("width", w).attr("height", h).attr("fill","transparent")
    .on("mousemove", function(ev){
      const [mx,my] = d3.pointer(ev, this);   // same coordinate space as pts
      const i = del.find(mx, my);
      onEnter(pts[i][2], i, nodes ? nodes[i] : null);
    })
    .on("mouseleave", onLeave);
}
"""


def scaffold(title, body_html, extra_js=""):
    """Return a complete, self-contained interactive dashboard HTML string.

    body_html : the <div class="wrap"> ... </div> markup (header + panels).
    extra_js  : the per-build render functions that draw each panel and wire
                voronoiHover()/tipAtNode(). Runs after d3 + HELPER_JS are loaded.
    """
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{GOOGLE_FONTS}
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>{INTERACTIVE_CSS}</style>
</head><body>
<div id="tooltip" class="tooltip"></div>
{body_html}
<script>
{HELPER_JS}
{extra_js}
</script>
</body></html>"""


# ---------------------------------------------------------------------------
# 3. Pre-publish validation checklist (RULE D + general)
# ---------------------------------------------------------------------------
PREPUBLISH_CHECKLIST = [
    "Value-scale domain set from d3.max(data, ...), not a hand-typed round cap (RULE D).",
    "Every panel's hover <rect> is appended to the marks' translated <g> (RULE A).",
    "Hover uses d3.Delaunay proximity, not bare dot targets (RULE B).",
    "Tooltip anchored to the mark via getBoundingClientRect() + CSS transition (RULE C).",
    "Annotation text has a paper halo; trough/edge labels use a leader line (RULE E).",
    "Connected scatter ONLY if both axes move monotonically; else a line.",
    "Extract the inline <script>, run `node --check`, and JSON.parse the embedded data blob.",
    "If a headless browser is reachable, screenshot at desktop + 375px and confirm every panel paints.",
    "Editorial text is ~half a first draft: headline + one-line dek + source + a short craft note.",
]


def print_checklist():
    print("NYT interactive dashboard — pre-publish checklist:")
    for i, item in enumerate(PREPUBLISH_CHECKLIST, 1):
        print(f"  {i}. {item}")


if __name__ == "__main__":
    # Prove the scaffold assembles and writes a runnable shell.
    demo_body = (
        '<div class="wrap">'
        '<h1>Scaffold demo</h1>'
        '<p class="dek">Replace this body and pass per-panel render JS via extra_js.</p>'
        '<div class="chartcard"><div id="c-demo"></div></div>'
        '</div>'
    )
    demo_js = r"""
const host=document.getElementById("c-demo");
const W=host.clientWidth||900,H=300,m={top:20,right:20,bottom:30,left:40};
const iw=W-m.left-m.right,ih=H-m.top-m.bottom;
const data=d3.range(20).map(i=>({x:i,y:Math.sin(i/3)*10+20}));
const svg=d3.select(host).append("svg").attr("viewBox",`0 0 ${W} ${H}`);
const g=svg.append("g").attr("transform",`translate(${m.left},${m.top})`);
const x=d3.scaleLinear().domain(d3.extent(data,d=>d.x)).range([0,iw]);
const y=d3.scaleLinear().domain([0,d3.max(data,d=>d.y)]).range([ih,0]);  // RULE D
g.append("path").datum(data).attr("fill","none").attr("stroke","#b5232e").attr("stroke-width",2)
  .attr("d",d3.line().x(d=>x(d.x)).y(d=>y(d.y)));
const dots=g.selectAll("circle").data(data).join("circle").attr("cx",d=>x(d.x)).attr("cy",d=>y(d.y))
  .attr("r",3).attr("fill","#fff").attr("stroke","#b5232e");
const pts=data.map(d=>[x(d.x),y(d.y),d]);
voronoiHover(g, pts, dots.nodes(), iw, ih,
  (d,i,node)=>{ dots.attr("r",3); d3.select(node).attr("r",6).attr("fill","#b5232e");
    tipAtNode(node,`<div class="t-hd">x ${d.x}</div><span class="t-accent">${d.y.toFixed(1)}</span>`); },
  ()=>{ dots.attr("r",3).attr("fill","#fff"); hideTip(); });
"""
    html = scaffold("Scaffold demo", demo_body, demo_js)
    out = "interactive_scaffold_demo.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"Wrote {out} ({len(html)} bytes)")
    print_checklist()

