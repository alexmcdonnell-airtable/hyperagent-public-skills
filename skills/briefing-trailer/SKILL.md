---
name: briefing-trailer
description: >-
  Turn a real day — a founder's, an operator's, anyone's — into a cinematic ~30s "coming
  soon" movie trailer where the trailer IS the day's briefing, told entirely in
  text-on-screen over photoreal footage. Pulls the day from connected Gmail, Google
  Calendar, and Slack, casts a consistent on-screen character, generates photoreal scene
  stills and Veo clips, typesets statement/caption cards, and assembles one continuous
  looping video embedded on one editorial webpage. Use when someone wants their day,
  week, launch, or any real timeline rendered as a teaser-trailer sizzle artifact. Use
  when a user wants a real timeline — their day, a launch week, an on-call shift, a
  wedding day, a harvest, a product sprint — rendered as a cinematic ~30s "coming soon"
  movie trailer that doubles as a briefing. Best when the user can connect Gmail / Google
  Calendar / Slack so the trailer is built from REAL events rather than invented ones.
  Triggers: "make my day into a trailer", "turn this into a movie teaser", "cinematic
  briefing", "day-as-a-film sizzle".
---

# Briefing Trailer — a real day, cut as a "coming soon" teaser

Turns a real timeline into a cinematic ~30-second movie trailer where **the trailer IS the briefing**: fast 2-second cuts, no voiceover, the whole story carried by text on screen over photoreal footage. Ends on a title + "coming soon" card. Final deliverable is always **one continuous looping video embedded on one editorial webpage**.

This skill packages a pipeline that has been run end-to-end and debugged in a real sandbox. Follow it in order.

---

## STEP 0 — Connect the user's real life first (DO THIS, OUT LOUD)

The whole point is that the trailer is built from a REAL day, not an invented one. Before generating anything, **nudge the user to connect their tools** so the briefing is real:

> "To make this YOUR Thursday and not a generic one, connect the sources your day actually lives in. The more you connect, the more the trailer reads as true:"
> - **Google Calendar** — the day's spine: meeting titles, times, the stacked-before-a-deadline rhythm
> - **Gmail** — the inbox beats: the term sheet, the customer escalation, the "are we doing this?" subject line
> - **Slack** — the live-fire moments: the SEV-1 thread, the "don't merge anything", the all-hands ping
> - *(optional, if relevant to their world)* **Linear / Jira** (sprint + incident), **GitHub** (the PR that shipped), **PagerDuty** (the page), **Google Drive/Docs** (the board deck), **Stripe** (the MRR number)

Implementation:
1. Call `SearchIntegrations` for each service the user names (e.g. `query: "gmail"`, `"google calendar"`, `"slack"`).
2. If a needed integration is not connected, call `ConnectIntegration({ integration })` and relay the returned setup guidance conversationally — do NOT paste the raw result. Tell the user what to click.
3. Once connected, pull the real day: calendar events for the target date, the 4-6 highest-signal emails, the hottest Slack thread. Reduce to **6-9 beats** with timestamps.
4. If the user declines to connect anything, you can still build it from beats they describe — but say plainly that connecting sources is what makes it feel true, and offer to upgrade it later.

**Never invent real company names for the user's own scenario.** Use fictional brand names for any company/competitor/customer you introduce (Halftide, Sonder, Meridian, Pulsar, Cinder). Only use real names when they are the user's actual, connected data.

---

## STEP 1 — Write the world bible (one short paragraph)

Lock these before generating pixels so every asset is consistent:
- **Title** (one word is strongest: "Thursday", "Launch", "Harvest", "On-Call")
- **Hero**: one named character, age, look, wardrobe, the single location-arc (bed → kitchen → desk → window). Keep it to ONE character and ~4 settings — consistency is the wow.
- **Tone & palette**: e.g. "pre-dawn blue, warm practical lamps, A24 founder drama".
- **The clock**: the deadline that gives the day stakes (offer expires 6 PM, launch at noon, doors open at 7).

---

## STEP 2 — Cast the hero (ONE portrait, then reuse it everywhere)

1. **Hero portrait** with `GenerateImage({ model: "openai/gpt-image-2" })` — GPT Image 2 for the photoreal face. One clean portrait, neutral light. This is your canonical reference.
2. **Scene stills** with `GenerateImage({ model: "gemini-3-pro-image-preview", inputImages: [heroPortraitUrl] })` (Nano Banana Pro) — pass the hero portrait as `inputImages` so the SAME person appears in every scene. Generate one still per location/beat (dawn-in-bed, espresso, typing, at-the-window, at-the-desk).

**Model routing (important):**
- `openai/gpt-image-2` → anything with **legible text or UI**: the email screenshot, the dashboard, the headline/TechCrunch card, the title + end cards. Also best for the photoreal hero portrait. Caps around 1536px.
- `gemini-3-pro-image-preview` → **character-consistent photoreal scene stills** (reuse the hero via inputImages).

---

## STEP 3 — Generate the footage (Veo 3.1)

For each scene still that should move, call `GenerateVideo` (Veo 3.1):
```
GenerateVideo({ prompt: "<subtle motion: steam rising, eyes opening, fingers on keys>",
                firstFrameImage: "<sceneStillUrl>", aspectRatio: "16:9" })
```
- Use **`firstFrameImage` only**. Veo 3.1 outputs an 8s 1920x1080 h264+aac clip.
- **DO NOT combine `referenceImages` with a custom `durationSeconds`** → it returns a 400. firstFrameImage alone is the reliable path.
- You will reslice these 8s clips into multiple ~2s cuts in the cut-sheet (different in/out windows of the same clip = different shots).

**Pulling generated media into the sandbox to edit it:** you cannot curl staging URLs (SSO-walled). Instead:
1. `FetchStoredFile({ fileId })` → returns a local path like `/agent/stored_files/{fileId}_{name}.mp4`.
2. Symlink it into your working dir: `ln -s <localpath> /agent/workspace/trailer/c1.mp4`.

---

## STEP 4 — Render all text as PNGs (NOT ffmpeg drawtext)

**Why:** the sandbox ffmpeg is compiled WITHOUT libfreetype, so the `drawtext` filter is missing ("Filter not found"). Verify with `ffmpeg -filters | grep drawtext`. The portable, reliable path is to render text with Pillow and composite the PNGs with `overlay`.

Use the bundled **`render_text.py`**. Write a `textspec.json` and run:
```
pip install Pillow -q   # if not present
python3 render_text.py textspec.json
```
It auto-detects fonts (Liberation Serif/Sans/Mono, DejaVu) across standard font dirs — no font paths needed. Three styles:
- **`statement`** — opaque full-frame card (e.g. "ONE FOUNDER. / ONE THURSDAY.", "SIGN. SHIP. SURVIVE."). Its own shot.
- **`data`** — opaque card with a spaced kicker + monospace rows (e.g. the calendar: "11:00 RENEWAL CALL …", or the metrics: "4,000 USERS / $42K MRR"). Its own shot.
- **`caption`** — transparent lower-third plate (rounded translucent box + red accent tick) overlaid on footage (e.g. "5:58 AM — the alarm wasn't what woke him.").

Spec example is in the docstring at the bottom of `render_text.py`. Tune `ink/dim/accent/bg/caption_center_y` to match the world bible. Keep captions to one line; place `caption_center_y` just above the bottom letterbox (~862 for 132px bars).

---

## STEP 5 — Write the cut-sheet and assemble (OOM-safe)

**Why per-segment:** a single ffmpeg filtergraph with ~20+ looped 1080p inputs gets OOM-killed (rc -9 / SIGKILL, then "moov atom not found"). The bundled **`build_trailer.py`** renders each shot to its own file, concat-demuxes with `-c copy`, then does ONE light grade+audio pass. Peak memory stays tiny and it's far more debuggable.

Write a `cutsheet.json` (schema in the script docstring). Shot types:
- `card` — opaque statement/data PNG, gentle fade in/out
- `footage` — a trimmed window of a Veo clip (`in`/`out`), cover-cropped, with optional transparent `caption` PNG overlay
- `insert` — a still (email/dashboard screenshot), cover-crop + slow zoompan push, optional caption
- `endcard` — the title + "coming soon" still, slow fade-in, hold

A proven 15-shot rhythm (~30s): statement card → (footage+caption / insert+caption) alternating through the day's beats → mid statement card → … → data card (the day's calendar) → data card (the metrics) → endcard. Durations ~1.6-2.0s per beat, 3.4s hold on the endcard.

```
python3 build_trailer.py cutsheet.json
```
Produces the graded, letterboxed, scored MP4. Knobs in the cut-sheet:
- `grade` — `eq=brightness/saturation` + `vignette`
- `letterbox` — px of black bars (132 for a 2.0:1-ish cinematic frame at 1080p; 0 to disable)
- `audio.mode` — `synth_tension` (sine 55+110 drone with rising volume + tremolo + lowpass, a gated sine-44 boom near the end, `alimiter`) or `none` (silent bed). `audio.ambient_from` can point at one of your clips to fold in real room tone (looped, low-passed, ducked under the drone).

---

## STEP 6 — Ship it: one video, one page

1. `SaveFile({ path: "/agent/workspace/trailer/trailer.mp4" })` → gives `[[VIDEO_xxx]]` placeholder + fileId. Put the placeholder on its own line so it previews.
2. `PublishFilePublicly({ fileId })` → returns a `pub.*` shareUrl. **Webpage embeds MUST use this public shareUrl**, not the internal staging URL (SSO-walled).
3. Write an editorial teaser webpage (dark, Cormorant Garamond + Inter + JetBrains Mono works well): giant title, "Coming Soon" rule, the embedded `<video autoplay loop muted playsinline>` with a "Sound on" toggle, a briefing grid restating the day's beats as text, and a production-notes credits block. `PublishWebpage({ filePath, title })` → include the returned `[[ARTIFACT_xxx]]` placeholder.

The webpage + the single looping video IS the deliverable.

---

## Bundled scripts
- **`render_text.py`** — JSON-driven Pillow text renderer (statement/data/caption styles, font auto-detection, true letter-spacing, translucent caption plates). No credentials.
- **`build_trailer.py`** — JSON-driven, OOM-safe ffmpeg assembler (per-segment render → concat-demux → grade+letterbox+synth audio). No credentials.

Both run with plain `python3` — no API keys. All the API-backed steps (images, video, file publishing, integrations) use platform tools, not the scripts.

## Gotchas checklist (all hit and solved in practice)
- `drawtext` not compiled in → render text as Pillow PNGs, composite with `overlay`+alpha `fade`.
- Single big filtergraph OOMs (rc -9) → per-segment render + concat-demux + one final pass.
- Can't curl staging media (Okta SSO) → `FetchStoredFile` + symlink into the working dir.
- Veo 400 → use `firstFrameImage` alone; don't pair `referenceImages` with custom `durationSeconds`.
- Webpage video won't load → embed the `PublishFilePublicly` `pub.*` shareUrl, not the internal one.
- Use `python3` (not `python`); `pip install Pillow -q` if Pillow is missing.
- Refer to any Hyperagent agent as "it"/"its" in creator-facing copy.
