---
name: veo-hyperframes
description: >-
  End-to-end production pipeline for creating polished launch videos using Veo 3.1 video
  generation and Hyperframes motion graphics overlays. Built around the Text Zone
  Composition principle: every shot reserves a clear 1/3 of the frame as a contrast zone
  for legible text overlays. Covers beat board planning with declared text zones,
  cinematic contrast techniques, hero image generation, Veo prompt construction with zone
  preservation clauses, GSAP-animated typography overlays, and ffmpeg compositing via
  colorkey. Use when producing any video that combines AI-generated footage (Veo) with
  motion graphics text overlays (Hyperframes). The core discipline is Text Zone
  Composition: every shot must reserve a clear 1/3 of the frame with deliberate contrast
  for legible text. Applies to product launch videos, brand hype reels, social clips, and
  any multi-beat video where text must be legible over generated footage.
---

# Veo + Hyperframes

## Purpose

This skill documents the complete production pipeline for creating polished videos that combine Veo 3.1 AI-generated footage with Hyperframes motion graphics overlays. Every technique here was battle-tested across multiple production cycles and iterative feedback.

---

## CORE PRINCIPLE: Text Zone Composition

This is the entire reason Veo + Hyperframes exist together. **Every shot must reserve a clear 1/3 of the frame as a "text zone" — a region with deliberate contrast that makes overlaid text legible by design, not by accident.**

Do NOT generate pretty footage and then try to make text readable with shadows, outlines, or scrims. Instead:

1. **Declare the text zone per beat** — which 1/3 (left, right, or bottom) and what contrast direction (dark zone for white text, or light zone for dark text)
2. **Name the contrast source** in the Veo prompt — what real-world element creates the darkness or lightness in that zone (shadow from a tree, dark ground surface, bright sky, etc.)
3. **Place overlay text exclusively inside the declared zone** — Hyperframes composition aligns to the pre-planned text zone, not placed arbitrarily

### Text Zone Positions

Every beat gets ONE of these three text zones. The zone is a full 1/3 of the frame — not a small corner, not a narrow strip.

For 9:16 portrait (1080×1920), the same principle applies with adjusted pixel counts:

### Contrast Direction

Most beats use **dark zone + white text** — it's easier to prompt Veo for shadow than for brightness. But certain shots naturally provide a light zone:

### Cinematic Techniques for Creating Natural Text Zones

These are real-world lighting and composition techniques that create dark or light zones naturally — use them in your Veo prompts so the contrast looks intentional, not artificial.

**Dark zones (for white text):**

**Light zones (for dark text):**

### The Golden Rule

**If you can't name the contrast source, you haven't designed the shot.**

Bad: "negative space on the left side"
Good: "the left third of frame is deep shadow from the building overhang, near-black"

Bad: "room for text at the bottom"
Good: "dark polished concrete floor fills the bottom third, reflecting only a faint highlight from the product's LED"

---

## PIPELINE OVERVIEW

```
1. Define product + beat board (concept, beats, TEXT ZONES per beat)
2. Generate hero images with text zones composed in (GenerateImage Pro)
3. Dispatch Veo clips using hero images as firstFrameImage
4. Download clips, trim to beat duration, concat
5. Init Hyperframes project, download GSAP locally
6. Write overlay composition (index.html) — text placed in declared zones
7. Lint + render overlay to WebM
8. Composite overlay onto footage via ffmpeg colorkey
9. Save final MP4
```

---

## STEP 1: Beat Board

The beat board is the contract between footage and overlay. Every beat declares its text zone BEFORE any generation happens.

### Beat board format

The "Contrast" column names the specific technique and resulting text color. This is non-negotiable — every row must have it filled in before Veo dispatch.

### Duration catalog

- 10s = 3 beats × 3.33s
- 15s = 3 beats × 5s
- 30s = 5 beats × 6s
- 45s = 6 beats × 7.5s
- 60s = 8 beats × 7.5s

---

## STEP 2: Hero Images With Text Zones

Generate 1 hero image per beat using GenerateImage Pro. These images serve two purposes:

1. Lock the product's visual identity for Veo consistency
2. **Establish the text zones with the declared contrast source**

### Prompting hero images for each text zone position

**Left 1/3 dark (subject right, shadow left):**

```
Product photography of [product]. The machine is positioned in the RIGHT THIRD
of the frame. The LEFT THIRD is [contrast source — e.g. "deep shadow from dramatic
side-lighting from the right" or "dark out-of-focus foliage"]. The dark left zone
should be near-black, creating clear contrast for white text. [Lighting direction].
[Surface/environment]. No text, no logos.
```

**Right 1/3 dark (subject left, shadow right):**

```
Product photography of [product]. The machine is positioned in the LEFT THIRD
of the frame. The RIGHT THIRD is [contrast source — e.g. "deep shadow falling away
from the key light on the left" or "dark architectural shadow from an overhang"].
The dark right zone should be near-black. [Lighting]. [Environment]. No text.
```

**Bottom 1/3 dark (subject upper, dark surface below):**

```
Product photography of [product]. The machine fills the UPPER TWO-THIRDS of frame.
The BOTTOM THIRD is [contrast source — e.g. "dark polished concrete surface" or
"deep shadow on the ground beneath the product"]. The bottom zone should read as
near-black. [Lighting]. No text.
```

**Center dark (for wordmark reveals — product as silhouette):**

```
Dramatic silhouette of [product] against a near-black background. The machine is
a subtle dark shape in the lower-center, barely visible. A single [accent element]
glows faintly. The frame is 90 percent deep black with massive negative space
in the center. Apple keynote final reveal frame energy. No text.
```

### For outdoor products (natural contrast sources):

- **Left dark:** "dramatic golden hour side-lighting from the right, the left third falls into deep landscape shadow"
- **Right dark:** "the right third of frame is deep green shadow from a line of trees"
- **Bottom dark:** "dark wet grass / dark gravel path / shadow on the ground fills the bottom third"
- **Light zone (for dark text):** "bright overcast sky fills the upper-left third"

---

## STEP 3: Veo Clip Generation

### Critical parameters

- `mode: "fast"` — always (iterate fast, quality is excellent)
- `resolution: "1080p"`
- `durationSeconds: 8` — **always 8 at 1080p**. Other values are rejected by the API. Trim to beat duration later.
- `aspectRatio: "16:9"` for landscape, `"9:16"` for portrait
- `firstFrameImage: [hero image viewUrl]` — this is what locks visual consistency AND text zones

### What works for firstFrameImage

- Use the full `viewUrl` returned by GenerateImage (the `https://hyperagent.com/api/files/...` URL)
- Do NOT use artifact IDs — the API rejects them
- Do NOT combine `firstFrameImage` + `referenceImages` at 1080p — this triggers 400 errors

### Prompting Veo to PRESERVE text zones

This is critical. Veo will try to fill dark areas with motion, light shifts, or detail unless you explicitly tell it not to. Always include a text-zone preservation clause:

**Pattern:** Name the zone, name what it is, tell Veo to keep it.

```
"The [left/right/bottom] third of frame is [contrast source — e.g. deep shadow 
from the side-lighting]. This dark area stays dark and empty throughout the shot — 
no light creep, no objects entering, no motion in the shadow zone."
```

**Examples:**

- "The left third of frame is deep shadow from the key light. This shadow zone stays consistently dark and clean throughout — no light shifts, no motion entering the left side."
- "The bottom third is dark ground surface in shadow. It remains dark and still throughout — no light reflections, no objects crossing into the bottom zone."
- "The right third is dark defocused background. It stays uniformly dark and soft throughout the shot."

Without this preservation clause, Veo frequently:

- Adds light sources that creep into your text zone
- Introduces motion or detail into what was a clean dark area
- Shifts the overall exposure, reducing contrast in your text zone

### Dispatch all beats in parallel

Fire all Veo calls in a single message. They generate simultaneously.

### Audio

Veo 3.1 generates synchronized ambient audio natively. Describe the soundscape in your prompt:

- "Soft mechanical servo whir and ambient tone"
- "Evening crickets, faint breeze, quiet electric hum"
- "Deep silence with a faint low electronic hum"

Always preserve this audio through the final composite (`-map 0:a` in ffmpeg).

---

## STEP 4: Trim and Concat

After downloading clips via FetchStoredFile, trim each to the beat duration with consistent encoding:

```bash
ffmpeg -y -ss 0 -t 3.33 -i beatN.mp4 \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -vsync cfr -r 30 -pix_fmt yuv420p \
  tmp/beatN_trimmed.mp4
```

Concat via the demuxer. **Critical:** concat.txt paths are relative to concat.txt's own directory, not cwd:

```bash
cd tmp
printf "file 'beat1_trimmed.mp4'\nfile 'beat2_trimmed.mp4'\nfile 'beat3_trimmed.mp4'\n" > concat.txt
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy base.mp4
```

---

## STEP 5: Hyperframes Project Setup

```bash
npx hyperframes init <slug> --example blank --non-interactive
```

**GSAP must be local.** The render-time browser cannot reach CDN URLs through the proxy:

```bash
curl -s -o <slug>/gsap.min.js "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
```

Reference as `<script src="gsap.min.js"></script>` in index.html.

---

## STEP 6: Overlay Composition

### Text placement MUST align to declared text zones

The beat board declares where text goes. The overlay composition implements exactly that — no improvising.

### Structure

```html
<div id="root" data-composition-id="main"
     data-start="0" data-duration="10"
     data-width="1920" data-height="1080">

  <div class="clip" data-start="0" data-duration="3.33" data-track-index="1">
    <!-- Beat 1 content — text positioned in declared zone -->
  </div>

  <div class="clip" data-start="3.33" data-duration="3.33" data-track-index="1">
    <!-- Beat 2 content — text positioned in declared zone -->
  </div>

  <div class="clip" data-start="6.66" data-duration="3.34" data-track-index="1">
    <!-- Beat 3 content — text positioned in declared zone -->
  </div>
</div>
```

### Text styling

Because the footage provides contrast by design, text needs only a minimal single-layer shadow as insurance:

```css
.txt {
  color: #fff;
  text-shadow: 0 1px 10px rgba(10,12,24,0.6);
}
```

**What to avoid:**

- Multiple shadow layers (creates visible dark halos/"bubbles" after colorkey)
- Pure black shadows `rgba(0,0,0,...)` (colorkey eats them — they become invisible)
- Heavy blur radii over 20px on opaque shadows (creates visible dark blobs)
- Any stroke or outline effects

If you MUST use shadows (footage isn't dark enough), use dark navy `rgba(10,12,24,...)` not pure black. Keep it to 1-2 layers max with moderate opacity.

### Text size minimums

Text that looks fine in a browser at 1920x1080 becomes tiny in a compressed video viewed on a phone or embedded player.

**Font weight matters.** Use weight 400-500 for all HUD/label text. Weight 300 disappears at small sizes in video.

### Built-in Hyperframes fonts

These are available without CDN loading:
EB Garamond, Playfair Display, JetBrains Mono, IBM Plex Mono/Sans/Serif, Outfit, Nunito, Oswald, Lato, Montserrat, Archivo Black, League Gothic, Space Mono, Source Code Pro.

### Recommended type pairings

### GSAP timeline rules

```js
window.__timelines = window.__timelines || {};
var tl = gsap.timeline({ paused: true });
// ... all animations ...
window.__timelines['main'] = tl;
```

- Timeline key must match `data-composition-id` on root
- Do NOT call tl.play() — Hyperframes seeks the timeline
- Build timeline synchronously (no async, no fetch, no timers)
- Only animate visual properties: opacity, x, y, scale, rotation, color, backgroundColor, letterSpacing
- Never animate visibility, display, or call video/audio play()
- No `repeat: -1` — always finite repeats
- No Math.random(), no Date.now()

### Animated counters

Use proxy objects with onUpdate — this works correctly with Hyperframes' frame-by-frame seeking:

```js
var proxy = { v: 0 };
var el = document.getElementById('counter');
tl.to(proxy, {
  v: 96,
  duration: 1.2,
  ease: 'power2.out',
  snap: { v: 1 },
  onUpdate: function() { el.textContent = Math.round(proxy.v) + '°'; }
}, startTime);
```

### Status text changes

Use `tl.call()` to swap text content at specific times:

```js
var statusEl = document.getElementById('status');
tl.call(function() { statusEl.textContent = 'Locked'; }, [], 1.8);
```

### Do NOT use sub-compositions

`data-composition-src` renders as empty content in the current Hyperframes runtime. Always inline everything in index.html.

---

## STEP 7: Lint and Render

```bash
npx hyperframes lint
npx hyperframes render --format webm --output overlays.webm --quality standard --fps 30 --workers 2
```

- Lint must pass with 0 errors. The "file too large" warning is expected for inline compositions — ignore it.
- Render takes ~60-70 seconds for a 10-second composition at 1080p with 2 workers.
- The WebM output has a black background where the page was transparent. This gets keyed out in compositing.

---

## STEP 8: Composite via Colorkey

```bash
ffmpeg -y -i tmp/base.mp4 -i overlays.webm \
  -filter_complex "[1:v]colorkey=color=0x000000:similarity=0.10:blend=0.05,format=rgba[ovl];\
                   [0:v][ovl]overlay=shortest=1,format=yuv420p[v]" \
  -map "[v]" -map 0:a \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -movflags +faststart \
  output.mp4
```

### Colorkey parameters (tuned through iteration)

### What NOT to use

- `blend=all_mode=screen` — causes magenta wash from chroma noise
- similarity &gt; 0.15 — eats too much, including dark footage areas and text shadows
- blend &gt; 0.10 — creates soft fuzzy edges around text

### Always preserve Veo audio

`-map 0:a` maps the audio from the base video (Veo's generated ambient sound) to the final output.

---

## BEAT 1 HUD PATTERNS

The "robot calculating its approach" HUD is a strong opening beat. Reusable elements:

### Structure

- **Status label** (top-left of text zone): "POUR SEQUENCE" / "TERRAIN ANALYSIS" — changes to "LOCKED" mid-beat
- **Primary readout**: Large animated counter (temp, blade height, distance)
- **Secondary readout**: Smaller animated counter (flow rate, noise level, speed)
- **Guide elements**: Crosshair/reticle, scan lines, thin grid — placed WITHIN the text zone
- **Progress bar**: Bottom of text zone, fills across the beat duration
- **Corner metadata**: Serial number, coordinates (smallest text, 14px)

All HUD elements live inside the declared text zone (typically left 1/3), never spilling into the subject area.

### Animation sequence

```
0.0s  Guide lines draw from center of text zone
0.1s  Status label slides in from left
0.2s  Line extends from label
0.3s  Primary counter appears, begins counting
0.5s  Corner metadata fades in
0.7s  Secondary counter appears, begins counting
1.5s  Guide lines fade out (they've served their purpose)
1.8s  Status text changes to "LOCKED"
2.9s  Everything fades out together
```

---

## COMMON PITFALLS

1. **Generating footage before declaring text zones** — leads to endless shadow/legibility fixes. Always fill in the beat board's text zone and contrast columns first.
2. **Saying "negative space" without naming the contrast source** — Veo doesn't know what "negative space" means. Name the real-world element: "deep shadow from the side-light," "dark concrete floor," "twilight sky."
3. **Using referenceImages + firstFrameImage at 1080p** — triggers Veo 400 errors. Use firstFrameImage only.
4. **Using artifact IDs for firstFrameImage** — Veo requires full viewUrl, not IDs.
5. **Not including a text-zone preservation clause** — Veo will fill dark areas with motion/light unless told not to. Always include "this dark area stays dark and empty throughout."
6. **CDN GSAP in Hyperframes** — render browser can't reach CDN through proxy. Always download locally.
7. **Pure black text shadows** — colorkey eats them. Use dark navy (rgba 10,12,24).
8. **Multi-layer heavy shadows** — creates visible "bubble" halos in the composite.
9. **Small text** — anything under 18px becomes illegible in compressed video.
10. **Font weight 300 for labels** — too thin. Use 400-500 minimum.
11. **Placing text outside the declared zone** — defeats the entire pipeline. If your text isn't in the zone, the contrast isn't there.
12. **concat.txt relative paths** — paths resolve relative to concat.txt's directory, not cwd.
13. **durationSeconds != 8 at 1080p** — Veo rejects all other values at 1080p. Always generate 8s and trim.

---

## SOURCES

- Hyperframes pipeline docs: https://hyperframes.mintlify.app/guides/pipeline
- Veo 3.1 API docs: https://ai.google.dev/gemini-api/docs/video
- GSAP docs: https://gsap.com/docs/v3/
- Learned through iterative production: POUR (coffee robot) and TERRA (lawnmower) launch videos, multiple revision cycles covering shadow approaches, text sizing, compositional contrast, colorkey tuning.
