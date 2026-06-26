---
name: brand-book-generator
description: >-
  Generates three radically distinct, on-trend brand concepts for a founder's app and
  ships them as a single NO-SCROLL hero webpage — a bento "brand book" (logo + tagline,
  in-app screen, out-of-home, merch, palette, type, voice) that assembles itself with a
  staggered pop on every toggle. Toggling re-skins the whole canvas (color + fonts) and
  swaps every brand-applied mockup. Concepts are grounded in current-year design trends,
  not safe defaults. HARD RULE baked in: never blue/purple gradients. (Single-screen
  successor to the earlier 'Brand Concept Generator'.) Use when a founder has an
  app/product and wants an agency-grade brand identity they can SEE in one screen across
  several bold directions. Triggers: "build a brand for my app", "brand kit/brand book",
  "brand concepts", "show me a few directions", "make it look like an agency did it".
  Needs only app name + one-line description; optionally audience, positioning, founder
  photos. Prefer this over the older 'Brand Concept Generator' — this is the
  single-screen, no-scroll version.
---

# Brand Book Generator

Turns a one-line app description into a single **no-scroll hero webpage** that presents **three radically distinct brand routes** as a self-assembling **bento brand book**. Everything an agency would show — logo + tagline, in-app screen, out-of-home/billboard, merch, palette, type, voice — sits in one viewport. Toggling a route re-skins the entire canvas (color, fonts, corner radius), swaps every brand-applied mockup, and replays a staggered "assemble" animation. The tagline types itself in with a blinking cursor on each switch.

> Successor to the scroll-based "Brand Concept Generator". Driving brief: the founder should NOT scroll — the full brand book pops into one beautiful hero, and toggling animates each style in.

Taste-forward skill. The template handles all engineering; each run your job is to (a) invent three bold, genuinely different, on-trend brand worlds and (b) generate brand-applied mockups for each.

## Inputs
- **Required:** app name, one-line description.
- **Optional:** audience, positioning/tone, founder photos, brand cues.
Proceed with strong invented directions if only name + one-liner are given.

## Ground the routes in CURRENT design trends (not stale defaults)
Quick-search the current year's trends first (e.g. ExaSearch "2026 brand identity design trends"). Live trends to remix:
- **Claymorphism** — soft inflated 3D, warm saturated color, big squishy forms (tactile, playful).
- **Neo-brutalism + hi-vis** — stark canvas, dopamine acid color, monospace, hard edges, sticker energy.
- **Y2K / liquid chrome / retrofuture** — iridescent metal, holographic pink-cyan, scanlines.
- **Maximalism / structured excess**, **oversized & kinetic variable type**, **bento grids**.

## HARD RULES (do not violate)
- **NEVER use blue or purple gradients** — including the indigo→cyan→magenta "aurora"/AI-native mesh-gradient look. It is THE generic default everyone ships and reads as un-designed. If you want dimension/energy, reach for claymorphism, chrome/iridescent, hi-vis flat color, or maximalist clashing flats. Warm-sunset or acid gradients are acceptable; blue/purple gradients are banned.
- **Avoid other over-trained looks:** warm cream + burnt-orange + serif (the "Claude" look), generic film-noir, flat gray SaaS minimalism.

## The divergence rule
Make the three routes feel like three different companies. Force divergence across: **canvas VALUE** (don't ship three darks — vary light/dark), **font pairing**, **surface texture** (soft-clay-3D vs flat-raw vs glossy-metal), **accent family**, **voice**. Bold > safe. A proven, approved trio: **claymorphism (warm) · neo-brutalist hi-vis (stark light) · Y2K chrome (dark metal)**.

## Workflow

### 1. Define three routes
Per route: name, idx, short tagline (gets typed), one positioning paragraph, 3 tone tags, 4-color palette (name + hex), type spec (display family + one display word + one mono line), one voice line.

### 2. Generate brand-applied mockups — 3 per route (9 total)
Per route: **in-app screen** (1:1), **out-of-home/billboard** (9:16), **merch flatlay** (3:2), art-directed to the route's world. **Render the wordmark INTO the image** (`openai/gpt-image-2`, quality "high"); phrase prompts so the only text is the wordmark. Founder photos → use as `inputImages`.

### 3. Publish every image publicly (CRITICAL)
Sandboxed iframe can't auth thread-scoped `/api/files/...` URLs. Run each image through **PublishFilePublicly**; use the `pub.hyperagent.com` shareUrls.

### 4. Build from `brandbook_template.html` (this skill's script)
Edit only: `<title>` + `.brand` wordmark + `.meta` tail; the three theme token blocks `body[data-route="r1|r2|r3"]` (palette + `--display/--text/--mono` + `--radius`); the Google Fonts `<link>`; toggle labels; `.wordmark-big` text; and the `ROUTES` object (copy + 9 public URLs). Keys must stay `r1/r2/r3`. Then **PublishWebpage**; iterate by editing + re-publishing with the returned `artifactId`. The template ships a clean claymorphism example for r1 (no blue/purple) — keep it clean.

### 5. (Zeitgeist only) Airtable Kanban
Set the pitch record Status `wip` at start, `review` at end with the artifact URL. See "Airtable Pitch Kanban" skill.

## Template mechanics (already built)
- **One 100vh shell, no scroll.** Bento grid: `logo`(big) · `app` · `merch` · `bill`(tall OOH) · `pal` · `type` · `voice`. Collapses to a scrollable stack under 900px.
- **Toggle = full re-skin + assemble replay** via `activate(key)` + the `.go` class.
- **Self-typing tagline** + blinking caret each activation; arrow keys switch; subtle pointer tilt for depth.

## Gotchas
- Public URLs mandatory for images.
- Keep `ROUTES` keys `r1/r2/r3`.
- Fit-on-one-screen is the brief — keep copy tight so nothing overflows the desktop viewport.
- Render only the wordmark in mockups; verify GPT Image 2 spelled the app name correctly, regenerate if glitched.
- Re-check every route against the HARD RULES before publishing — especially no blue/purple gradients.

## Output
One no-scroll page = a full three-route brand book the founder tabs through and screen-records. Follow-ons: expand the chosen route into logo files, social kit, deck, packaging, a Veo/animation OOH spot.
