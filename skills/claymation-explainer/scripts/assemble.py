#!/usr/bin/env python3
"""
Claymation Explainer — FFmpeg assembly helper.

Concatenates N scene clips into a single fast-cut edit driven by ONE voiceover
track. Critically: the generated Veo clips' own audio is DROPPED (concat a=0)
and only the single VO file is mapped, so there is never duplicative audio.

Usage:
  python3 assemble.py \
      --clips s1.mp4 s2.mp4 s3.mp4 ... \
      --vo vo.wav \
      --out final.mp4 \
      --per-clip 3.0 \      # seconds each clip stays on screen (faster cuts = smaller)
      --trim-start 1.0 \    # skip the first N sec of each clip (Veo intros are slow)
      --vo-delay 0.3        # delay VO start so it lands after the first frame

The script computes total duration = per_clip * len(clips), adds a video
fade-out and a VO fade-out near the end, normalizes every clip to a common
fps/scale/SAR (prevents concat glitches), and renders H.264 yuv420p + AAC.
"""
import argparse
import shlex
import subprocess
import sys


def build_command(clips, vo, out, per_clip, trim_start, vo_delay):
    n = len(clips)
    total = per_clip * n

    inputs = []
    for c in clips:
        inputs += ["-i", c]
    inputs += ["-i", vo]
    vo_idx = n  # voiceover is the last input

    # Per-clip normalization: trim a slow intro, reset PTS, lock fps/scale/SAR.
    parts = []
    labels = []
    for i in range(n):
        lbl = f"v{i}"
        parts.append(
            f"[{i}:v]trim=start={trim_start}:duration={per_clip},"
            f"setpts=PTS-STARTPTS,fps=24,scale=1280:720:force_original_aspect_ratio=decrease,"
            f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[{lbl}]"
        )
        labels.append(f"[{lbl}]")

    # Video-only concat (a=0) → NO clip audio reaches the output.
    concat = f"{''.join(labels)}concat=n={n}:v=1:a=0[vall]"

    fade_st = max(total - 0.6, 0)
    vfade = f"[vall]fade=t=out:st={fade_st:.2f}:d=0.6[vout]"

    # Single VO track: small delay in, fade out near the end.
    afade_st = max(total - 0.6, 0)
    vo_ms = int(vo_delay * 1000)
    afilter = (
        f"[{vo_idx}:a]adelay={vo_ms}|{vo_ms},"
        f"afade=t=out:st={afade_st:.2f}:d=0.9[aout]"
    )

    filtergraph = ";".join(parts + [concat, vfade, afilter])

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + ["-filter_complex", filtergraph,
           "-map", "[vout]", "-map", "[aout]",
           "-t", f"{total:.2f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", out]
    )
    return cmd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", nargs="+", required=True)
    ap.add_argument("--vo", required=True)
    ap.add_argument("--out", default="final.mp4")
    ap.add_argument("--per-clip", type=float, default=3.0)
    ap.add_argument("--trim-start", type=float, default=1.0)
    ap.add_argument("--vo-delay", type=float, default=0.3)
    args = ap.parse_args()

    cmd = build_command(
        args.clips, args.vo, args.out,
        args.per_clip, args.trim_start, args.vo_delay,
    )
    print("Running:\n " + " ".join(shlex.quote(p) for p in cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)
    print(f"Wrote {args.out} ({args.per_clip * len(args.clips):.1f}s, {len(args.clips)} shots)")


if __name__ == "__main__":
    main()

