#!/usr/bin/env python3
"""
vignelli_system.py — Generate a Vignelli-Canon-compliant design-token sheet.

Massimo Vignelli's discipline reduced to machine-emittable tokens: a primary
palette used as *identifier* (not decoration), a two-size type scale where the
heading is ~2x the body, the five canonical grids, ruler weights, and the
signage panel module logic from the Grandi Stazioni railway program.

This is a deterministic generator — no network, no credentials. It exists so the
"discipline" of the Canon can be applied consistently across artifacts (web
pages, signage specs, design-system docs) instead of being re-derived by hand
each time.

Usage:
  python3 vignelli_system.py                      # default: Helvetica, Vignelli vermilion
  python3 vignelli_system.py --primary "#F04E23"  # set the identifier color
  python3 vignelli_system.py --base 16 --format css
  python3 vignelli_system.py --format json
  python3 vignelli_system.py --grid 4x8           # print one grid's column/module map
  python3 vignelli_system.py --signage            # print railway signage panel module table

Formats: css (default) | json | scss

RENDERING NOTE (hard-won): Helvetica is the house face, but it is NOT installed in
most headless environments. If you rasterize SVG/HTML (cairosvg, headless Chromium)
with a `Helvetica`/`Arial`/`sans-serif` stack, the renderer silently falls back to
Noto Sans — a rounded humanist face that reads like Calibri and breaks the Vignelli
grotesque. For any artwork you will rasterize (or feed to an image model), render in
a true Helvetica/Arial-metric grotesque: `Liberation Sans` (usually installed) or an
embedded Helvetica/Arimo TTF. The CSS emitted here lists "Liberation Sans" before the
generic fallback for exactly this reason. Always eyeball one render before trusting it.
"""

# Rasterization-safe Helvetica substitute (Arial/Helvetica-metric grotesque).
RASTER_FONT = "Liberation Sans"
import argparse, json, sys

# --- The Canon's fixed constants --------------------------------------------

# The six basic typefaces Vignelli said you can live a whole career on.
BASIC_TYPEFACES = [
    ("Garamond", 1532, "serif"),
    ("Bodoni", 1788, "serif"),
    ("Century Expanded", 1900, "serif"),
    ("Futura", 1930, "sans-serif"),
    ("Times", 1931, "serif"),
    ("Helvetica", 1957, "sans-serif"),
]
# plus, by his own admission: Optima, Univers, Caslon, Baskerville.

# Primary palette — color as Signifier / Identifier ("Chromotype"), not pictorial.
# Vignelli vermilion is the Canon cover; signal blue is the NYC subway / station blue.
PALETTE = {
    "vermilion": "#F04E23",   # the Canon cover red — primary identifier
    "blue":      "#0039A6",   # NYC subway / Grandi Stazioni signage blue
    "yellow":    "#FFCC00",   # signal yellow
    "ink":       "#0A0A0A",   # near-black text
    "paper":     "#F4F1EA",   # warm paper
    "white":     "#FFFFFF",
    "rule":      "#0A0A0A",
}

# The five grids Vignelli specimens in the Canon: (columns, modules).
GRIDS = {
    "2x4": (2, 4),
    "5x4": (5, 4),
    "3x6": (3, 6),
    "6x6": (6, 6),
    "4x8": (4, 8),
}

# Ruler weights — type ALWAYS hangs from the ruler.
RULERS = {"major_pt": 2.0, "minor_pt": 1.0, "hair_pt": 0.5}

# Column-width -> size/leading pairs (pt on pt), straight from the Canon.
TYPE_BY_COLUMN = [
    ("<=70mm",  [(8, 9), (9, 10), (10, 11)]),
    ("<=140mm", [(12, 13), (14, 16)]),
    (">140mm",  [(16, 18), (18, 20)]),
]


def type_scale(base_px: float) -> dict:
    """Two living sizes per page, heading ~2x body. Everything else is a weight."""
    body = base_px
    return {
        "caption": round(body * 0.75, 2),   # the small print / specs
        "body":    round(body, 2),          # one of the two sizes
        "lead":    round(body * 1.5, 2),     # standfirst / intro (use sparingly)
        "heading": round(body * 2.0, 2),     # the OTHER size — 2x the body
        "display": round(body * 4.0, 2),     # scale-as-visual-power (covers, hero)
        "mega":    round(body * 8.0, 2),     # "Books"-spread scale contrast
        "leading_body": round(body * 1.2, 2),
        "leading_tight": round(body * 1.05, 2),
    }


def emit_css(primary: str, base: float) -> str:
    ts = type_scale(base)
    lines = [":root {",
             "  /* Vignelli Canon tokens — color as identifier, two sizes, hard grid */"]
    pal = dict(PALETTE); pal["vermilion"] = primary
    for k, v in pal.items():
        lines.append(f"  --v-{k}: {v};")
    lines.append(f"  --v-primary: {primary};")
    lines.append("")
    for k, v in ts.items():
        unit = "px"
        lines.append(f"  --v-{k.replace('_','-')}: {v}{unit};")
    lines.append("")
    for name, pt in RULERS.items():
        lines.append(f"  --v-rule-{name.split('_')[0]}: {pt}px;")
    lines.append("  --v-gutter: 1rem;            /* gutters tight — ~one line of type */")
    lines.append("  --v-margin: clamp(16px, 4vw, 64px);")
    # 'Liberation Sans' before the generic fallback so headless renderers don't drift to Noto/Calibri
    lines.append("  --v-face: 'Helvetica Neue', Helvetica, Arial, 'Liberation Sans', sans-serif;")
    lines.append("}")
    lines.append("")
    lines.append("/* Type hangs FROM the ruler */")
    lines.append(".v-rule { border-top: var(--v-rule-major) solid var(--v-ink); }")
    lines.append(".v-rule--minor { border-top: var(--v-rule-minor) solid var(--v-ink); }")
    lines.append(".v-flush-left { text-align: left; } /* the default; never justify */")
    lines.append("")
    for name, (cols, mods) in GRIDS.items():
        lines.append(f".v-grid-{name} {{ display:grid; "
                     f"grid-template-columns: repeat({cols}, 1fr); "
                     f"grid-template-rows: repeat({mods}, 1fr); gap: var(--v-gutter); }}")
    return "\n".join(lines)


def emit_scss(primary: str, base: float) -> str:
    css = emit_css(primary, base)
    return "// Vignelli Canon tokens (SCSS map)\n" + css.replace("--v-", "$v-").replace(":root {", "")


def emit_json(primary: str, base: float) -> str:
    pal = dict(PALETTE); pal["vermilion"] = primary; pal["primary"] = primary
    payload = {
        "palette": pal,
        "typefaces_basic": [{"name": n, "year": y, "kind": k} for n, y, k in BASIC_TYPEFACES],
        "house_face": "Helvetica",
        "type_scale_px": type_scale(base),
        "type_by_column": {k: v for k, v in TYPE_BY_COLUMN},
        "grids": {k: {"columns": c, "modules": m} for k, (c, m) in GRIDS.items()},
        "rulers_pt": RULERS,
        "rules": [
            "Search the meaning before the form (semantics first).",
            "Max two type sizes per page; heading is ~2x the body.",
            "Flush left, never justified.",
            "Color is an identifier, not decoration — primary palette.",
            "White space makes the black sing — protect the silence.",
            "If you can see the layout, it is a bad layout.",
            "Refine equity, don't replace it.",
            "When rasterizing or feeding art to image models, render Helvetica via Liberation Sans / an embedded TTF — never the bare sans-serif fallback (it becomes Noto/Calibri).",
        ],
    }
    return json.dumps(payload, indent=2)


def print_grid(name: str):
    if name not in GRIDS:
        print(f"Unknown grid '{name}'. Options: {', '.join(GRIDS)}"); return
    cols, mods = GRIDS[name]
    print(f"{name} grid — {cols} columns x {mods} modules")
    for r in range(mods):
        print("  " + "  ".join("[]" for _ in range(cols)))


def print_signage():
    """Railway station signage panel module table (Grandi Stazioni logic).
    Cap-heights scale by a fixed module; arrows and pictograms share the cap box."""
    print("Railway signage — panel hierarchy (white Helvetica on signal blue)")
    print(f"  Identifier color: {PALETTE['blue']}   Text/Pictograms: {PALETTE['white']}")
    rows = [
        ("Station identification (building)", 600, 100, "Cap height 100mm, internally lit"),
        ("Directional (overhead)",            300, 75,  "Arrow shares the cap box; flush left"),
        ("Information / regulatory",          150, 25,  "Hangs from a 2pt rule"),
        ("Platform number (flag)",            250, 250, "Numeral in a square, double-sided"),
    ]
    print(f"  {'Panel':36} {'Panel mm':>9} {'Cap mm':>7}  Note")
    for name, panel, cap, note in rows:
        print(f"  {name:36} {panel:>9} {cap:>7}  {note}")


def main():
    ap = argparse.ArgumentParser(description="Generate Vignelli-Canon design tokens.")
    ap.add_argument("--primary", default=PALETTE["vermilion"], help="identifier color hex")
    ap.add_argument("--base", type=float, default=16.0, help="base body size in px")
    ap.add_argument("--format", choices=["css", "scss", "json"], default="css")
    ap.add_argument("--grid", help="print one grid map, e.g. 4x8")
    ap.add_argument("--signage", action="store_true", help="print railway signage module table")
    a = ap.parse_args()

    if a.grid:
        print_grid(a.grid); return
    if a.signage:
        print_signage(); return
    if a.format == "css":
        print(emit_css(a.primary, a.base))
    elif a.format == "scss":
        print(emit_scss(a.primary, a.base))
    else:
        print(emit_json(a.primary, a.base))


if __name__ == "__main__":
    main()

