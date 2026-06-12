---
name: nyc-subway-campaign
description: >-
  End-to-end method to visualize a full NYC subway (MTA) out-of-home ad campaign for any
  brand: lock a vivid brand identity, create a canonical logo asset FIRST and reuse it
  across every image-gen run for brand consistency, render the ads photoreally in real
  subway placements with GPT Image 2, and assemble an agency-grade single-page case
  study. Use when someone wants to mock up / pitch / visualize a brand's subway campaign.
  Use when: When the user wants to visualize, mock up, pitch, or art-direct a NYC subway
  (or transit OOH) advertising campaign for a brand — real or fictional — and wants a
  cohesive agency-grade deliverable (brand identity + ads rendered in real subway
  settings + a webpage). Also a strong reference for any transit/OOH campaign
  visualization where brand-mark consistency across many generated images matters.
---

# NYC Subway Campaign Visualizer

Turn a brand (real or fictional) into a complete, agency-grade visualization of a New York City subway out-of-home campaign: a vivid brand identity, the ads rendered photoreally inside real subway placements, and a single polished case-study webpage. Validated end-to-end on the "Brightleaf" finance-app build.

The output shape is one **scrolling case-study webpage**: masthead → brief → idea/manifesto → brand book (logo, palette, type, voice) → the work in real subway context → the copy lines → a media run plan → footer.

---

## THE NON-NEGOTIABLE: brand consistency via a locked logo asset

The single biggest quality lever — and the easiest thing to get wrong — is keeping the **wordmark/logo identical across every rendered ad**. Text-to-image alone will redraw the logo slightly differently in every frame (different letterforms, spacing, leaf shape). The fix is a two-step lock:

**Step A — Create ONE canonical logo asset before generating any scene.** Pick whichever is more faithful for the brand:
- **Code-drawn SVG → PNG (most type-faithful).** Draw the wordmark + mark as crisp SVG in the *correct* font, rasterize to PNG. Render real grotesque/serif metrics — in this sandbox `Helvetica`/`Arial`/`sans-serif` silently falls back to Noto Sans (rounded, Calibri-like); use **Liberation Sans** (installed) or an embedded Arimo/real TTF for Helvetica-style marks, or load the brand's actual display font. Rasterize with the bundled headless Chrome (`--headless=new --force-device-scale-factor=3 --screenshot=out.png file:///lockup.html`) since cairosvg has no Helvetica.
- **GPT Image 2 logo plate.** Generate the lockup on a plain background ("the lowercase wordmark 'brand' in [font/style] beside a simple [symbol], centered on a flat off-white card, no other elements"). GPT Image 2 has best-in-class short-text rendering. Re-roll until letterforms are clean, then treat that PNG as the master.

Optionally generate 2-3 logo options and let the user choose before committing — the chosen plate becomes canonical.

**Step B — Pass the canonical logo PNG as `inputImages` into EVERY scene generation**, with an explicit instruction: *"Reproduce the provided brand logo artwork EXACTLY as shown — same letterforms, spacing and symbol; do not redraw, restyle, translate or re-letter it. Place it as a printed/applied graphic in the scene."* This pins the mark across the whole campaign. (GPT Image 2 accepts input images for edit/composition. Nano Banana 2 supports up to 14 reference images + subject consistency — use it if you need the mark plus several product/character refs held together, accepting slightly weaker text rendering.)

**Also lock the palette in words, every prompt.** Models don't read hex reliably, so keep a reusable **BRAND KIT** sentence appended to every prompt naming the colors descriptively (e.g. "fresh spring-leaf green, deep evergreen ink, warm off-white, with marigold-yellow and soft-coral accents"), the personality, and `Spell every word exactly; no invented or garbled text, no extra logos.`

> NOTE on the validated Brightleaf run: that first pass rendered the wordmark from *text instructions only* (no logo reference) and drew the page's own logo in HTML/SVG. It worked because the headline+wordmark were short and GPT Image 2 is strong, but the mark drifted subtly between frames. The locked-logo-asset method above is the upgrade — always prefer it for a real deliverable.

---

## Phase 0 — Lock the brand identity

Decide and write down (this becomes the brand-book section):
- **Name + one-line positioning** (e.g. "personal finance, made human").
- **Campaign idea / brand line** — one ownable line the whole campaign hangs on (Brightleaf: *"Money, in plain language."*).
- **Palette** — 5 tokens: ink, accent, paper, + two pops. Make it *vivid and distinct*.
- **Type** — a display + text pairing matched to the brief (Brightleaf used Fraunces soft serif + Plus Jakarta Sans). Invest in real Google Fonts.
- **Voice** — 3-4 principles + 5-6 headlines (one per placement).

**Anti-default rules (hard-won):**
- **NEVER blue/purple gradients**, incl. the indigo→cyan→magenta "aurora"/AI-native mesh look — reads as generic AI slop. Reach for warm/botanical/hi-vis/claymorphic/chrome instead. Warm-sunset and acid gradients are fine.
- Avoid the over-trained **"Claude look"** (warm cream + burnt-orange/terracotta + serif) and generic film-noir.
- Diverge hard and pick a register that actually fits the brand; don't ship a house style.

---

## Phase 1 — Research real subway placements

`SearchImages` for ground-truth realism before prompting. Useful queries:
- "New York City subway platform advertising real photo"
- "MTA subway interior car card ads"
- "subway station backlit diorama advertising"
- "subway station domination takeover campaign" / "subway staircase ad wrap"
- "subway digital LED platform screen ad"

You usually **don't** need these as `inputImages` (GPT Image 2 knows the subway well); use them to enrich the environmental description (white tile, steel columns, fluorescent + LED light, yellow tactile platform edge, motion-blurred train, third rail, scratched windows, commuters in coats, grime/reflections).

## The canonical NYC placement archetypes

Generate one render per archetype (6-7 makes a full campaign):
1. **Platform wall takeover** — wide hero; large headline + leaves/imagery on the tiled wall, train blur. `16:9`.
2. **Interior car cards** — overhead horizontal strip ads inside a train car, passengers seated. `16:9`.
3. **Platform 2-sheet poster** — vertical poster in a stainless steel frame on the platform wall. `3:4`.
4. **Backlit diorama** — glowing lightbox set into a tiled transfer corridor. `3:4`.
5. **Station domination** — stairs/columns/wall fully wrapped; commuter descending. `16:9`.
6. **Digital platform screen** — slim black-framed vertical LCD with the ad + an app-UI moment. `9:16`.
7. **In-app payoff** — a hand holding the phone showing the app on the train (personal software in the user's environment); the product speaks the same language as the ads. `3:4`.

---

## Phase 2 — Generate the renders (GPT Image 2)

`GenerateImage({ model:"openai/gpt-image-2", quality:"high", aspectRatio:<per archetype>, inputImages:[CANONICAL_LOGO_URL], prompt:<scene> + <BRAND KIT> })`

- **GPT Image 2** because crisp legible type is the whole game here. (Nano Banana 2 only if you need 4K or many reference images.)
- **Prompt recipe per scene:** `[real subway environment, detailed] + [the ad creative: exact short headline in quotes, brand colors, imagery, where the wordmark sits] + [reproduce the provided logo exactly] + [BRAND KIT]`.
- Keep headlines **short** (they render best). One headline per placement.
- Fire all 6-7 generations in parallel (multiple GenerateImage calls in one message).

### Verify type fidelity (do not skip on a real deliverable)
For the most text-heavy renders: `FetchStoredFile(fileId)` → `Read(localPath)` and actually look. Confirm the headline + wordmark are spelled right and the mark matches the canonical logo. Re-roll any frame that drifted.

### Avoid video when type must stay crisp
Veo drifts letterforms frame-to-frame. For a typography-led hero, screen-capture an interactive/animated webpage instead of generating video. Reserve Veo for non-text-critical motion (e.g. a train rushing past behind a static plate).

---

## Phase 3 — Publish images for the webpage

The published webpage runs in a **sandboxed iframe that cannot authenticate to thread-scoped `/api/files/...` URLs** — those embed as broken images. So:

`PublishFilePublicly({ fileId: <shortId> })` for EACH render → use the returned `pub.hyperagent.com` `shareUrl` in the HTML. (pub.hyperagent.com images load fine in the sandbox.)

---

## Phase 4 — Build the case-study webpage

Use `campaign_page_template.html` (bundled with this skill). It's the genericized version of the validated Brightleaf page. Edit only:
1. `<title>`, `.brandmark` text, masthead tail (season/year).
2. `:root` palette tokens + the Google Fonts `<link>`.
3. All copy — brief headline, manifesto, captions (format label + headline + one-line rationale), the 6 line cards, the media-run table.
4. The **7 image `src=`** → the `pub.hyperagent.com` URLs.
5. The inline `<symbol id="mark">` SVG → the brand's own simple symbol (or drop it for a pure wordmark).

Layout that works: feature (car cards, full width) → two-up (poster + diorama) → feature (domination) → two-up (digital + in-app). Reveal-on-scroll via IntersectionObserver is built in.

Then `PublishWebpage({ filePath, title })` and surface the `[[ARTIFACT_xxx]]` placeholder.

**Webpage craft notes:** overlay text on photos = white with `text-shadow` (survives image swaps); don't stack a competing big headline over an ad image that already has its own headline; generous whitespace; sentence-case display; keep the canvas keyed to the brand, never a default.

---

## Optional — pitch/Kanban bracket (Zeitgeist only)
If running as Zeitgeist in an execution thread: set the Pitches record to `wip` as the FIRST action and `review` (with artifact URL) as the LAST. Not part of the generic skill.

---

## Quick checklist
1. Lock identity (name, line, palette, type, voice, 6 headlines). No blue/purple.
2. Create ONE canonical logo asset (SVG→PNG or GPT Image 2 plate).
3. SearchImages for subway realism cues.
4. Generate 6-7 placement renders with GPT Image 2 — logo PNG as inputImages + BRAND KIT in every prompt.
5. Spot-check type fidelity (FetchStoredFile → Read); re-roll drifts.
6. PublishFilePublicly each render → pub URLs.
7. Fill campaign_page_template.html; PublishWebpage; return the placeholder.
