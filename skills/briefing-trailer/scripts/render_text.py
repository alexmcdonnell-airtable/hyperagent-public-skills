#!/usr/bin/env python3
"""
render_text.py — Render trailer text as PNGs (Pillow), driven by a JSON spec.

WHY THIS EXISTS: many ffmpeg builds in sandboxed environments are compiled
WITHOUT libfreetype, so the `drawtext` filter is unavailable. Rendering text to
PNGs and compositing with `overlay` is the reliable, portable path. It also gives
you true letter-spacing (tracking) and translucent caption plates, which
drawtext does poorly.

Two kinds of text assets:
  * "statement" / "data" cards  -> full-frame OPAQUE PNG (used as its own shot)
  * "caption"                   -> full-frame TRANSPARENT PNG (overlaid on footage)

USAGE:
  python3 render_text.py textspec.json
  (relative output paths are written next to the spec file unless --outdir given)

SPEC SCHEMA (see make_example_spec() at bottom for a full example):
{
  "width":1920, "height":1080,
  "ink":"#f4f1ea", "dim":"#8a857a", "accent":"#c1392b", "bg":"#0a0908",
  "caption_center_y":862,            # vertical center of caption plate (sits above bottom letterbox)
  "fonts":{"serif":"<path>", "sans":"<path>", "sans_bold":"<path>", "mono":"<path>"},  # all optional; auto-detected
  "items":[
    {"out":"card1.png","style":"statement","font":"serif","size":104,"tracking":6,
       "lines":["ONE FOUNDER.","ONE THURSDAY."]},
    {"out":"card_cal.png","style":"data","font":"mono","size":62,"kicker":"THE DAY AHEAD",
       "lines":["11:00   RENEWAL CALL","1:00    BOARD PREP","4:30    ALL-HANDS"]},
    {"out":"cap2.png","style":"caption","font":"sans","size":48,
       "text":"5:58 AM   —   the alarm wasn't what woke him."}
  ]
}
"""
import json, os, sys, glob

from PIL import Image, ImageDraw, ImageFont

FONT_HINTS = {
    "serif":     ["LiberationSerif-Bold", "DejaVuSerif-Bold", "TimesNewRoman", "Georgia"],
    "sans":      ["LiberationSans-Regular", "DejaVuSans", "Arial", "Helvetica"],
    "sans_bold": ["LiberationSans-Bold", "DejaVuSans-Bold", "Arial-Bold"],
    "mono":      ["LiberationMono-Regular", "DejaVuSansMono", "JetBrainsMono", "Courier"],
}
FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts"),
             "/Library/Fonts", "/System/Library/Fonts"]

def find_font(name_hints):
    cands = []
    for d in FONT_DIRS:
        if os.path.isdir(d):
            cands += glob.glob(os.path.join(d, "**", "*.ttf"), recursive=True)
            cands += glob.glob(os.path.join(d, "**", "*.otf"), recursive=True)
    for hint in name_hints:
        for c in cands:
            if hint.lower() in os.path.basename(c).lower():
                return c
    return cands[0] if cands else None

def hex2rgba(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16), a)

def text_w(draw, s, font, tracking=0):
    if not s: return 0
    if tracking == 0:
        return draw.textbbox((0,0), s, font=font)[2]
    w = 0
    for ch in s:
        w += draw.textbbox((0,0), ch, font=font)[2] + tracking
    return w - tracking

def draw_tracked(draw, x, y, s, font, fill, tracking=0):
    if tracking == 0:
        draw.text((x,y), s, font=font, fill=fill); return
    cx = x
    for ch in s:
        draw.text((cx,y), ch, font=font, fill=fill)
        cx += draw.textbbox((0,0), ch, font=font)[2] + tracking

def line_h(font):
    a,d = font.getmetrics(); return a+d

def main():
    if len(sys.argv) < 2:
        print("usage: render_text.py textspec.json [--outdir DIR]"); sys.exit(2)
    spec_path = sys.argv[1]
    outdir = None
    if "--outdir" in sys.argv:
        outdir = sys.argv[sys.argv.index("--outdir")+1]
    spec = json.load(open(spec_path))
    base = outdir or os.path.dirname(os.path.abspath(spec_path))

    W = spec.get("width",1920); H = spec.get("height",1080)
    INK   = hex2rgba(spec.get("ink","#f4f1ea"))
    DIM   = hex2rgba(spec.get("dim","#8a857a"))
    ACC   = hex2rgba(spec.get("accent","#c1392b"))
    BG    = hex2rgba(spec.get("bg","#0a0908"))
    CAP_CY= spec.get("caption_center_y", int(H*0.80))

    fonts = spec.get("fonts", {})
    resolved = {}
    for key, hints in FONT_HINTS.items():
        p = fonts.get(key) or find_font(hints)
        if not p:
            raise SystemExit(f"No font found for '{key}'. Install fonts or set fonts.{key} in spec.")
        resolved[key] = p
    print("fonts:", {k: os.path.basename(v) for k,v in resolved.items()})
    def F(key, size): return ImageFont.truetype(resolved.get(key, resolved["sans"]), size)

    for it in spec["items"]:
        out = it["out"] if os.path.isabs(it["out"]) else os.path.join(base, it["out"])
        style = it.get("style","caption")
        fkey  = it.get("font","sans")
        size  = it.get("size",48)
        tracking = it.get("tracking",0)

        if style in ("statement","data"):
            img = Image.new("RGBA",(W,H),BG); d = ImageDraw.Draw(img)
            y_off = 0
            if style == "data" and it.get("kicker"):
                kf = F("sans_bold", max(26,int(size*0.42)))
                ks = "   ".join(list(it["kicker"].upper().replace(" "," ")))  # spaced kicker
                ks = it["kicker"].upper()
                # apply tracking on kicker
                kw = text_w(d, ks, kf, 8)
                draw_tracked(d, (W-kw)//2, int(H*0.28), ks, kf, DIM, 8)
                y_off = 40
            lines = it["lines"]
            f = F(fkey, size); lh = line_h(f); gap = it.get("gap", 24)
            total = len(lines)*lh + (len(lines)-1)*gap
            y = (H-total)//2 + y_off
            for ln in lines:
                w = text_w(d, ln, f, tracking)
                draw_tracked(d, (W-w)//2, y, ln, f, INK, tracking)
                y += lh + gap
            img.convert("RGB").save(out)

        else:  # caption (transparent lower-third plate)
            img = Image.new("RGBA",(W,H),(0,0,0,0)); d = ImageDraw.Draw(img)
            f = F(fkey, size); tw = text_w(d, it["text"], f, tracking); lh = line_h(f)
            padx, pady = it.get("padx",40), it.get("pady",24)
            bw, bh = tw + padx*2, lh + pady*2
            bx, by = (W-bw)//2, CAP_CY - bh//2
            d.rounded_rectangle([bx,by,bx+bw,by+bh], radius=10, fill=(8,7,6,150))
            d.rectangle([bx,by,bx+5,by+bh], fill=ACC)  # accent tick
            draw_tracked(d, (W-tw)//2, by+pady-2, it["text"], f, INK, tracking)
            img.save(out)
        print("wrote", out)

if __name__ == "__main__":
    main()

