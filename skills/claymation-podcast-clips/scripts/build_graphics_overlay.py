#!/usr/bin/env python3
"""
build_graphics_overlay.py — Cut a transparent-center overlay PNG from a still.

This is the workaround for the Veo SAFETY-FILTER GOTCHA: the video model refuses to
animate a frame that reads as a real person inside a news/broadcast layout (chyron +
ticker + likeness => "deepfake/synthetic news" => job returns "No video URL in
completed response", repeatedly, in both fast and standard modes).

The fix: animate a GRAPHICS-FREE clean plate (just the clay character talking — which
the model allows), then composite the broadcast graphics back on in code. This script
builds the overlay: it takes the APPROVED graphics still, keeps ONLY the edge graphics
(clock, logos, lower-third banner, ticker, corner bug) and makes everything else
transparent so the live animation shows through.

Seam rule (important): keep-rectangles must either (a) sit over STATIC background
(e.g. corner badges over a non-moving backdrop) or (b) have their inner edge land
exactly on a HARD graphic edge (e.g. the top edge of an opaque lower-third banner).
Anything frozen UNDER an opaque banner is invisible, so generous bottom bands are safe.
Never let a keep-rect's inner edge cross the moving subject in open air — that freezes
a moving body part and shows a seam.

Usage:
    python3 build_graphics_overlay.py \
        --still approved_graphics_still.png \
        --out tv_overlay.png \
        --width 1920 --height 1080 \
        --rect 0,0,285,128 \           # clock badge (top-left)
        --rect 1580,0,1920,142 \       # logo (top-right)
        --rect 0,760,1920,1080 \       # lower-third banner + ticker (full width)
        --rect 0,678,275,760           # corner bug above banner

Each --rect is x1,y1,x2,y2 in the OUTPUT (width x height) coordinate space.
Tune the rects by compositing a single test frame and viewing it (see skill docs).
"""
import argparse
from PIL import Image, ImageDraw

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", required=True, help="approved still WITH graphics baked in")
    ap.add_argument("--out", default="tv_overlay.png")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--rect", action="append", default=[],
                    help="keep-region x1,y1,x2,y2 (output coords); repeatable")
    a = ap.parse_args()

    if not a.rect:
        raise SystemExit("provide at least one --rect x1,y1,x2,y2")

    base = Image.open(a.still).convert("RGB").resize((a.width, a.height), Image.LANCZOS)
    mask = Image.new("L", (a.width, a.height), 0)
    d = ImageDraw.Draw(mask)
    for r in a.rect:
        x1, y1, x2, y2 = [int(v) for v in r.split(",")]
        d.rectangle([x1, y1, x2, y2], fill=255)
    base.putalpha(mask)
    base.save(a.out)
    print(f"wrote {a.out} ({a.width}x{a.height}), {len(a.rect)} keep-regions")

if __name__ == "__main__":
    main()

