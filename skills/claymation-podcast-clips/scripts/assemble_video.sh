#!/usr/bin/env bash
# assemble_video.sh — normalize clips, concat, burn captions, mux original audio.
#
# Part of the claymation-podcast-clips skill. Encapsulates the ffmpeg gotchas:
#   - ALL segments must be normalized to an IDENTICAL spec (size/fps/pixfmt/timescale)
#     or the concat demuxer with "-c copy" produces broken/again-encoded output.
#   - Drop Veo per-clip audio (-an); the FINAL audio is ONLY the original VO track.
#   - Burn ASS captions onto the silent montage BEFORE muxing audio (so caption time
#     == audio time, both starting at 0).
#
# Layout expected:
#   $SEGDIR/seg01.mp4 .. segNN.mp4   (raw Veo/clean clips OR already-normalized)
#   $AUDIO                            original VO (m4a/aac), the ground-truth timeline
#   $ASS                              captions.ass from make_captions.py
#
# Usage:
#   bash assemble_video.sh \
#       --segdir segs --audio howie_audio.m4a --ass captions.ass \
#       --durfile durations.txt --out final.mp4 [--normalize]
#
#   durations.txt: one line per segment "NN DURATION" e.g. "01 3.0" ... "22 3.44"
#                  (only needed with --normalize; the sum should equal audio length)
#
# Canonical normalize spec: 1920x1080, 30fps, yuv420p, libx264 crf18, no audio.
set -euo pipefail

SEGDIR=segs; AUDIO=""; ASS=""; OUT=final.mp4; DURFILE=""; DONORM=0
W=1920; H=1080; FPS=30
while [ $# -gt 0 ]; do
  case "$1" in
    --segdir) SEGDIR="$2"; shift 2;;
    --audio) AUDIO="$2"; shift 2;;
    --ass) ASS="$2"; shift 2;;
    --out) OUT="$2"; shift 2;;
    --durfile) DURFILE="$2"; shift 2;;
    --normalize) DONORM=1; shift;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done

if [ "$DONORM" = "1" ]; then
  [ -n "$DURFILE" ] || { echo "--normalize needs --durfile"; exit 1; }
  mkdir -p "$SEGDIR/norm"
  while read -r idx dur; do
    [ -z "$idx" ] && continue
    src="$SEGDIR/seg$idx.mp4"
    out="$SEGDIR/norm/seg$idx.mp4"
    ffmpeg -y -loglevel error -i "$src" -t "$dur" -an \
      -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},fps=${FPS},format=yuv420p" \
      -c:v libx264 -preset medium -crf 18 -video_track_timescale 30000 "$out"
  done < "$DURFILE"
  SEGDIR="$SEGDIR/norm"
fi

# Build concat list in sorted order
LIST="$(mktemp)"
for f in $(ls "$SEGDIR"/seg*.mp4 | sort); do echo "file '$PWD/$f'"; done > "$LIST"
echo "=== concat list ==="; cat "$LIST"

ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c copy silent_montage.mp4
echo "montage: $(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 silent_montage.mp4)s"

VIDEO=silent_montage.mp4
if [ -n "$ASS" ]; then
  ffmpeg -y -loglevel error -i silent_montage.mp4 -vf "ass=${ASS}" \
    -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p captioned_montage.mp4
  VIDEO=captioned_montage.mp4
fi

if [ -n "$AUDIO" ]; then
  ffmpeg -y -loglevel error -i "$VIDEO" -i "$AUDIO" \
    -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "$OUT"
else
  cp "$VIDEO" "$OUT"
fi

echo "=== output ==="
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name -of default=nw=1 "$OUT"
echo "wrote $OUT"
rm -f "$LIST"

