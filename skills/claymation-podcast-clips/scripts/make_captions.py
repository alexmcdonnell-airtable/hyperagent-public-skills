#!/usr/bin/env python3
"""
make_captions.py — Build an expert-captioner ASS subtitle file from a transcript.

Designed for the claymation-podcast-clips skill. Reads a TranscribeAudio-style
JSON (segments each with a "timestamp" "MM:SS"/"HH:MM:SS" and "text"), splits each
segment into readable cue chunks, distributes timing PROPORTIONALLY by character
length inside the known segment window, balances each cue onto <=2 lines, and emits
white text on a 50%-transparent black box (ASS BorderStyle=3).

Usage:
    python3 make_captions.py --transcript transcript.json --total 66.432 --out captions.ass
    # optional overrides:
    #   --fontsize 52  --max-cue 64  --max-line 36  --font "Liberation Sans"
    #   --marginv 90   --box-alpha 80   (ASS alpha hex: 00=opaque..FF=transparent)

WHY proportional timing: TranscribeAudio only gives per-SEGMENT start times, not
per-word. Splitting a segment into N cues and allocating each cue a slice of the
segment's [start,end) window proportional to its character count keeps captions
locked to speech without needing word-level timestamps.

GOTCHA baked in: the ASS "Dialogue:" line MUST have exactly the fields declared in
the "Format:" header (Layer,Start,End,Style,MarginL,MarginR,Effect,Text). An extra
field leaks visible junk like "0,," into the on-screen text. This script emits the
matching 8-field line.
"""
import argparse, json, re, sys

def parse_ts(ts):
    """'MM:SS' or 'HH:MM:SS' (optionally with .ms) -> seconds (float)."""
    ts = str(ts).strip()
    parts = ts.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0.0, parts[0], parts[1]
    else:
        h, m, s = 0.0, 0.0, parts[0]
    return h * 3600 + m * 60 + s

def fmt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

def split_into_cues(text, max_cue):
    words = text.split()
    cues, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) > max_cue and cur:
            cues.append(cur); cur = w
        else:
            cur = cand
    if cur:
        cues.append(cur)
    return cues

def wrap_two_lines(text, max_line):
    if len(text) <= max_line:
        return text
    words = text.split()
    best = None
    for k in range(1, len(words)):
        l1 = " ".join(words[:k]); l2 = " ".join(words[k:])
        if len(l1) <= max_line and len(l2) <= max_line:
            score = abs(len(l1) - len(l2))
            if best is None or score < best[0]:
                best = (score, l1, l2)
    if best:
        return best[1] + "\\N" + best[2]
    mid = len(words) // 2
    return " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])

def build(transcript_path, total, out_path, fontsize, max_cue, max_line, font,
          marginv, box_alpha):
    data = json.load(open(transcript_path))
    raw = data["segments"] if isinstance(data, dict) else data
    segs = []
    for i, seg in enumerate(raw):
        st = parse_ts(seg["timestamp"])
        en = parse_ts(raw[i + 1]["timestamp"]) if i + 1 < len(raw) else float(total)
        txt = " ".join(seg["text"].split()).strip()
        if txt:
            segs.append((st, en, txt))

    MIN_DUR = 0.7
    events = []
    for (st, en, txt) in segs:
        cues = split_into_cues(txt, max_cue)
        total_chars = sum(len(c) for c in cues) or 1
        span = max(en - st, 0.01)
        t = st
        for j, c in enumerate(cues):
            ce = en if j == len(cues) - 1 else t + span * (len(c) / total_chars)
            if ce - t < MIN_DUR and ce < en:
                ce = min(t + MIN_DUR, en)
            events.append((t, ce, wrap_two_lines(c, max_line)))
            t = ce

    box = f"&H{box_alpha:02X}000000"  # AABBGGRR, black with given alpha
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{fontsize},&H00FFFFFF,&H00FFFFFF,{box},{box},1,0,0,0,100,100,0,0,3,14,0,2,160,160,{marginv},1

[Events]
Format: Layer, Start, End, Style, MarginL, MarginR, Effect, Text
"""
    lines = [header]
    for (s, e, txt) in events:
        # 8 fields exactly matching the Format header above (Effect empty before Text)
        lines.append(f"Dialogue: 0,{fmt(s)},{fmt(e)},Cap,0,0,,{txt}")
    open(out_path, "w").write("\n".join(lines) + "\n")
    print(f"wrote {out_path}: {len(events)} cues across {len(segs)} segments, total={total}s")
    for (s, e, txt) in events:
        print(f"  {s:6.2f} -> {e:6.2f}  {txt.replace(chr(92)+'N', ' / ')}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--total", required=True, type=float, help="total audio duration (s)")
    ap.add_argument("--out", default="captions.ass")
    ap.add_argument("--fontsize", type=int, default=52)
    ap.add_argument("--max-cue", type=int, default=64)
    ap.add_argument("--max-line", type=int, default=36)
    ap.add_argument("--font", default="Liberation Sans")
    ap.add_argument("--marginv", type=int, default=90)
    ap.add_argument("--box-alpha", type=int, default=0x80, help="0=opaque..255=transparent")
    a = ap.parse_args()
    build(a.transcript, a.total, a.out, a.fontsize, a.max_cue, a.max_line,
          a.font, a.marginv, a.box_alpha)

