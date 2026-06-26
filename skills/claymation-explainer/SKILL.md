---
name: claymation-explainer
description: >-
  End-to-end workflow for producing a playful claymation-style explainer/ad video:
  storyboard → character reference images → scene stills → Veo image-to-video clips →
  single TTS voiceover → FFmpeg fast-cut assembly → webpage artifact. Captures the proven
  pipeline (and its gotchas) for character/scene-consistent multi-shot animated shorts.
  Use when the user wants a short animated/claymation (or any stylized, non-photoreal)
  explainer or ad video built from multiple consistent shots with a voiceover —
  especially "humans + agents collaborating" sizzle pieces, founder/brand explainers, or
  product ads. Also use whenever a multi-scene Veo production needs locked
  character/scene consistency and a single clean VO track.
---

# Claymation Explainer — Reusable Workflow

Produces a playful, stylized (claymation / stop-motion / non-photoreal) explainer or ad video built from multiple shots that stay character- and scene-consistent, scored by ONE clean voiceover track, assembled with FFmpeg, and surfaced as the hero of a webpage artifact.

This skill encodes the exact pipeline (and the failure modes that cost time) so future runs go end-to-end without re-discovering them.

## Aesthetic register
Claymation / stop-motion: handcrafted, slightly imperfect, tactile clay surfaces with visible thumbprints, soft studio lighting, shallow depth of field, warm paper-craft palette. Push the surreal/fictional — humans and clay "agent" characters collaborating in an oversized whimsical workshop. Non-photoreal is the point (taste pattern: "should feel made, not filmed").

## Operational Procedure

### 1. Plan first (Thread Context Doc)
Before generating anything, write into the Thread Context Doc:
- **Plan Overview**: the concept, the subject/brand (use FICTIONAL brand names — e.g. Halftide Candle Co.), the emotional beat.
- **Plan Tasks**: checkbox list (storyboard, cast refs, scene stills, clips, VO, assembly, webpage).
- A **storyboard**: numbered shots, each with a one-line visual description + the VO line it covers.
- A **VO script**: short, warm, conversational. ~2.5–3 words/sec → a 24s cut ≈ 60–70 words. Write it as ONE continuous read.

Keep shots SHORT for energy: 8 shots × 3s ≈ 24s. More shots + faster cuts read as "alive."

### 2. Cast — generate character reference images
For each recurring character (founder, and each clay "agent"), generate ONE clean reference portrait:
- Tool: `GenerateImage`, model `gemini-3-pro-image-preview` (Nano Banana Pro — best fidelity, typography, multi-subject consistency).
- `aspectRatio: "1:1"`, neutral seamless background, full body or 3/4, consistent lighting.
- Give each agent a distinct silhouette + signal color (e.g. Marlow = orange round with one blue eye; Hazel = mint tall with clipboard; Beacon = navy with amber chest glow). Distinct shapes are what make consistency read on screen.
- **Pronoun rule for any agent character in copy/VO: always "it"/"its" — never gendered, even with human-style names.**
- Save the returned image URLs/placeholders; these are the canonical refs for the whole project.

### 3. Generate scene stills (16:9) — the consistency anchor
For EACH storyboard shot, generate a still:
- `GenerateImage`, model `gemini-3-pro-image-preview`, `aspectRatio: "16:9"`.
- **Always pass the character reference images as `inputImages`.** This is what locks character consistency across scenes. Pass earlier scene stills too when you want lighting/atmosphere continuity.
- To put a brand name "inside the world," generate a still where the name is a physical clay object (a glowing nameplate, an engraved tile) — Nano Banana Pro renders in-scene typography well.
- For "agents at scale / multiplying," compose a grid or a clone-fan wide shot of the same agent character.

### 4. Generate clips — Veo image-to-video
- Tool: `GenerateVideo` (Veo 3.1). For each shot, pass the scene still as **`firstFrameImage` ONLY**.
- **CRITICAL GOTCHA:** Do NOT combine `firstFrameImage` + `referenceImages` + custom `durationSeconds` → returns 400 INVALID_ARGUMENT. Use `firstFrameImage` alone; accept the default 8s / 720p / 16:9. Consistency already comes from the stills, so referenceImages are unnecessary.
- Prompt the motion only (camera push, character action, clay-wobble), since the look is fixed by the first frame.
- **On 503 UNAVAILABLE: just retry the same call once** — it's transient.
- Clips come back ~8s; we trim them at assembly time for fast cuts.

### 5. Voiceover — ONE track, Gemini TTS
- Tool: `GenerateAudio`, single-speaker (`mode: "speech"`), voice `Aoede` (warm, breezy, friendly). Pass the full VO script as one read.
- Generate ONE VO file for the whole piece. Do not voice clips individually.

### 6. Pull assets into the container
- Use `FetchStoredFile` with the **FULL artifactId** (e.g. `cmpor0t1e00lv08adva2ezw1v`), NOT the 8-char shortId (shortIds 404).
- Files land in `/agent/stored_files/`. `cp` them to short working names (s1.mp4 … sN.mp4, vo.wav).
- **Do NOT curl/wget the media URLs** — sandbox egress hits an Okta SSO gate and returns HTML, not media bytes. `FetchStoredFile` is the only reliable path. (`file` cmd may be absent; use `od -c` / `head -c` to inspect bytes.)

### 7. Assemble with FFmpeg — single VO, no clip audio
Use the bundled `assemble.py` (preferred) or the raw command below.
- **The #1 rule: concat video-only (`a=0`) and map ONLY the single VO.** Playing both the Veo clips' on-clip audio AND the VO is duplicative and was explicitly rejected by the user.
- Trim each clip (skip its slow intro, e.g. `trim=start=1:duration=3`) for faster cuts; `setpts=PTS-STARTPTS`.
- Normalize every clip to a common `fps=24`, `scale=1280:720`, `setsar=1` before concat (prevents glitches).
- Add a video fade-out and a VO fade-out near the end; small VO `adelay` so it lands after the first frame.

Helper:
```
python3 skills/claymation-explainer/assemble.py \
  --clips s1.mp4 s2.mp4 s6.mp4 s7.mp4 s3.mp4 s8.mp4 s4.mp4 s5.mp4 \
  --vo vo.wav --out final.mp4 \
  --per-clip 3.0 --trim-start 1.0 --vo-delay 0.3
```

Raw reference command (8 clips → 24s, single VO only, NO clip audio):
```
ffmpeg -y -i s1.mp4 -i s2.mp4 -i s6.mp4 -i s7.mp4 -i s3.mp4 -i s8.mp4 -i s4.mp4 -i s5.mp4 -i vo.wav -filter_complex \
"[0:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v0]; \
 [1:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v1]; \
 [2:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v2]; \
 [3:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v3]; \
 [4:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v4]; \
 [5:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v5]; \
 [6:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v6]; \
 [7:v]trim=start=1:duration=3,setpts=PTS-STARTPTS,fps=24,scale=1280:720,setsar=1[v7]; \
 [v0][v1][v2][v3][v4][v5][v6][v7]concat=n=8:v=1:a=0[vall]; \
 [vall]fade=t=out:st=23.4:d=0.6[vout]; \
 [8:a]adelay=300|300,afade=t=out:st=22.8:d=0.9[aout]" \
-map "[vout]" -map "[aout]" -t 24 \
-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
-c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart final.mp4
```

(If a deliberate, NON-duplicative ambient bed is desired, duck the concatenated clip audio to ~0.18 and `amix` with the VO — but default is VO only.)

### 8. Deliver
- `SaveFile` the MP4 → returns a `[[VIDEO_xxx]]` placeholder; include it on its own line.
- Build/refresh a webpage with `PublishWebpage` (pass `artifactId` to update in place): claymation aesthetic (Fraunces + Inter, warm cream palette), hero = the assembled video (poster = scene-1 still), plus storyboard, cast refs, and the VO script. Keep prior cuts as comparison links when iterating.

## Iteration notes (v1→v2 lessons)
- "More shots, faster cuts" = add shots AND halve per-shot screen time.
- Reuse the SAME character refs across versions for continuity.
- "Agents at scale" reads best as a grid + a clone/multiplication wide shot.
- Put the brand name in-world as a physical clay object, not an overlay.
- Always end on a human+agent "together" beat (e.g. hands meeting on a tile).

## Quick checklist
1. Plan + storyboard + VO script in Thread Context Doc.
2. Character refs (gemini-3-pro-image-preview, 1:1, neutral bg, distinct shapes).
3. Scene stills (16:9) with character refs as inputImages.
4. Veo clips: firstFrameImage ONLY (no referenceImages/durationSeconds); retry once on 503.
5. ONE VO (Gemini TTS, Aoede).
6. FetchStoredFile (FULL artifactId) → container.
7. FFmpeg: concat a=0 + map ONLY the VO; trim/normalize/fade (use assemble.py).
8. SaveFile + PublishWebpage hero.
