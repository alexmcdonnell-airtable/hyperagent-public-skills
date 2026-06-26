---
name: landscaping-design-and-quote
description: >-
  Turns a customer's backyard photo + address into an interactive design-and-quote
  package: a clean "before", multiple AI design concepts rendered from the same photo,
  best-guess measurements, a style-switching before/after hero, and a live-recalculating
  itemized quote with financing. Includes working code and the real-world integration
  points a landscaping company needs to run it in production. Use when: When building a
  customer-facing landscaping (or any exterior/renovation) design + quote deliverable
  from a submitted photo and an address — proposals, lead-response packages, before/after
  pitch tools, or sizzle demos of an estimating agent. Also the reference for the "switch
  between N design styles on the same yard" hero and the live-recalculating quote builder.
---

# Landscaping Photo-to-Quote Package

A repeatable way to turn **one customer photo + one address** into a polished, interactive **design + quote** package a landscaping company can send back the same day:

> "Here's what's possible in your yard" → 3 design styles rendered on *their* yard → drag-to-compare before/after → an itemized, live-recalculating quote with financing → measurements on demand.

This doc captures the approach, the principles that made it land, the working code, and — critically — the **connection points you need to wire up for this to run for real** (not just as a demo).

---

## 1. The pipeline (end to end)

```
Intake          Ground truth         Design                  Package
────────        ─────────────        ──────────              ─────────────────────
photo  ─┐                            concept A (entertainer)  ┌─ style-switch hero
        ├─►  clean "before"  ─►  ┬─► concept B (garden)    ─► ├─ before/after slider
address ┘    satellite top-down │   concept C (low-water)     ├─ live itemized quote
             measurements ◄──────┘                            └─ measurements (on demand)
```

1. **Intake** — customer uploads a yard photo and gives the service address.
2. **Establish a clean "before"** — the before image is the *basis of every after*, so it must be straight, level, and good quality. If the submitted photo is crooked/cluttered, regenerate a clean plate first (see §3).
3. **Top-down + measurements** — pull satellite/aerial of the lot; estimate yard envelope, lawn area, fence run, slab, tree. Always framed as *estimates*.
4. **Design concepts** — render N styles **from the same before photo** so the before/after stays honest (§4).
5. **Build the interactive package** — style-switcher hero, drag-to-compare, live quote, demoted measurements (§6–§9).

---

## 2. Principles that made it work

- **One before, many afters.** Every concept is generated from the *same* before plate, with the *same camera vantage / fence line / existing tree* locked in the prompt. This is what makes the before/after honest instead of a bait-and-switch.
- **The before photo is load-bearing.** A crooked or messy intake photo poisons every render. Regenerate a clean, level plate first — it costs one image and saves the whole deliverable.
- **The style switch IS the hero.** The single most compelling beat is clicking between styles and watching the *same yard* re-render. Put it at the very top, make the transform visible (blur → sweep → resolve), and let it drive everything below it.
- **Preload all renders.** Switches must feel instant. Lazy-loading makes the previous style's bitmap linger ~1s during a swap and reads as laggy.
- **Live recalculation = trust.** Toggling a line item and watching the total, tax, and monthly payment re-tween in real time is the "this is a real tool" moment. Never snap numbers — tween them.
- **Lean hero, deep details on demand.** Lead with the visual + the few numbers that matter. Push the full measurement breakdown and "how we analyzed it" into a collapsible disclosure so the top of the page breathes.
- **Be honest in the copy.** Renders are AI visualizations from one photo; measurements carry a ±margin until confirmed on site; pricing is an estimate, not a contract. Say so plainly. It builds trust and keeps you out of legal trouble.
- **Fictional everything in demos.** Fictional company, address, proposal #, prices. Never put a real company into a fabricated scenario.

---

## 3. Step 1 — Establish a clean "before"

If the intake photo is usable as-is, skip this. If it's crooked/cluttered, regenerate a clean plate (for a demo, generate the "submitted" photo outright). Keep the features that give the design room: open lawn, a fence, one tree, a small slab.

```
GenerateImage({
  model: "gemini-3-pro-image",          // Pro for the basis plate; afters can use Flash
  aspectRatio: "4:3",
  prompt: "A clean, good-quality photo of an empty suburban backyard, shot straight-on at
  level eye-height. Composition is well-framed and LEVEL — horizon and fence line perfectly
  horizontal, NOT tilted. Flat open green lawn fills most of the frame. Simple wood privacy
  fence runs straight across the back. One mature shade tree in the back-right corner. A
  modest concrete patio slab in the foreground. Soft even natural daylight, sharp, well-
  exposed. No people, no furniture, no clutter — a blank-canvas yard ready to landscape."
})
```

Key prompt words that fix the common failure: **"LEVEL — horizon and fence line perfectly horizontal, NOT tilted."**

---

## 4. Step 3 — Concept afters from the SAME before (consistency lock)

Generate each style by passing the before plate as `inputImages` and **explicitly preserving the vantage and fixed features**. Flash (Nano Banana 2) is fine here and fast; it supports the input-image edit and multi-subject consistency.

```
GenerateImage({
  model: "gemini-3.1-flash-image",
  aspectRatio: "4:3",
  inputImages: [BEFORE_URL],            // ← the SAME clean before for every concept
  prompt: "Redesign this exact backyard into a modern outdoor entertainer's space. Keep the
  SAME straight-on level camera vantage, the SAME wood privacy fence line, the SAME back-right
  shade tree, the SAME foreground patio position and yard proportions, so it reads as a true
  before/after of THIS yard. Add: a gray-and-tan paver patio extending from the slab, a cedar
  pergola with a dining set, a linear gas fire pit with a sofa lounge, an outdoor kitchen island,
  bistro string lights, a center lawn strip, ornamental grass borders. Warm golden-hour light,
  photoreal, level horizon."
})
```

Repeat with different style bodies (e.g. *lush garden retreat*, *low-water modern xeriscape*). The invariant clause — **"keep the SAME vantage / fence / tree / proportions"** — is what makes the set feel like one yard, three futures.

**Top-down / measurements:** for a demo, generate an overhead "satellite" plate; in production pull the real tile (see §10). Annotate measurements as an **SVG overlay in the page** (crisp HTML text over the photo) — never bake dimension text into the image.

---

## 5. Step 4 — Publish images before embedding (sandbox gotcha)

A published webpage runs in a **sandboxed iframe that cannot authenticate to thread-scoped URLs** — those images render broken. Always run each render through `PublishFilePublicly` first and embed the returned `pub.hyperagent.com` URL.

```
PublishFilePublicly({ fileId: "<shortId from GenerateImage>" })
// → use the returned shareUrl in the HTML <img src>
```

---

## 6. Step 5a — The style-switcher hero (the star)

Tabs select a style; clicking one runs a visible "re-render" transform on the after image. Make this the most prominent section on the page.

```html
<div class="ba" id="ba">
  <img class="layer" id="beforeImg" src="">           <!-- before -->
  <div class="after-clip" id="afterClip"><img id="afterImg" src=""></div>  <!-- after, clipped -->
  <div class="sweep" id="sweep"></div>                 <!-- light sweep during swap -->
  <div class="rendering-note" id="rnote">Rendering your yard…</div>
  <div class="handle" id="handle">…</div>              <!-- drag divider -->
</div>
```

```js
const IMG = { before:"…", A:"…", B:"…", C:"…" };
// PRELOAD so switches are instant — do this on load:
Object.values(IMG).forEach(u => { const i = new Image(); i.src = u; });

function selectConcept(k){
  if (k === current) return;
  current = k;
  // …update tab active state, quote, summary, value bar…
  const ai = document.getElementById('afterImg'),
        sweep = document.getElementById('sweep'),
        rnote = document.getElementById('rnote');
  gsap.killTweensOf([ai, sweep, rnote]);
  gsap.to(rnote, { opacity:1, duration:.12 });
  gsap.timeline()
    .to(ai, { filter:'blur(16px) saturate(1.25)', scale:1.05, opacity:.45, duration:.22, ease:"power2.in" })
    .add(() => { ai.src = IMG[k]; })                                   // swap mid-blur
    .fromTo(sweep, { opacity:0, xPercent:-12 }, { opacity:1, xPercent:12, duration:.42, ease:"power1.inOut" }, "<")
    .to(ai, { filter:'blur(0px) saturate(1)', scale:1, opacity:1, duration:.46, ease:"power2.out" }, ">-0.1")
    .to(sweep, { opacity:0, duration:.18 }, "<")
    .to(rnote, { opacity:0, duration:.2 }, ">-0.05");
  renderItems();   // re-skin the quote below to match the selected style
}
```

The blur-out → src swap → light-sweep → blur-in sequence reads like the agent re-rendering the yard live. Tune total duration ~0.8–1.1s.

---

## 7. Step 5b — Before/after drag slider (pointer gotchas)

Drive the drag from **window-level** pointer listeners and **never call `setPointerCapture`** — capture retargets the gesture and steals taps from overlay controls. Re-fit the after image to the container so it doesn't squish inside the clip.

```js
(function(){
  const ba=document.getElementById('ba'), clip=document.getElementById('afterClip'),
        handle=document.getElementById('handle'), ai=document.getElementById('afterImg');
  let dragging=false;
  function fit(){ const r=ba.getBoundingClientRect(); ai.style.width=r.width+'px'; ai.style.height=r.height+'px'; }
  function setPct(px){
    const r=ba.getBoundingClientRect();
    let pct=Math.max(0,Math.min(1,(px-r.left)/r.width));
    clip.style.width=(pct*100)+'%'; handle.style.left=(pct*100)+'%'; fit();
  }
  const xy=e=>e.touches?e.touches[0].clientX:e.clientX;
  ba.addEventListener('pointerdown',e=>{dragging=true;setPct(xy(e));e.preventDefault();});
  window.addEventListener('pointermove',e=>{if(dragging)setPct(xy(e));});
  window.addEventListener('pointerup',()=>dragging=false);
  function init(){ fit(); clip.style.width='55%'; handle.style.left='55%'; }
  window.addEventListener('load',init); window.addEventListener('resize',init);
  setTimeout(init,250); setTimeout(init,800);   // re-fit after fonts/images settle
})();
```

---

## 8. Step 5c — Live-recalculating quote + financing

Model each style as a list of line items grouped by phase. Some are **locked** (foundations every build needs), the rest **toggle**. Recompute on every toggle and **tween** the numbers.

```js
// item: { g:"Hardscape", lock?:true, on?:true, nm, ds, qty, price }
const TAX=0.0825, DESIGN_CREDIT=450, APR=0.0799, MONTHS=60;

function recompute(){
  const c=CONCEPTS[current]; let sub=0,count=0;
  c.items.forEach(i=>{ if(i.lock||i._sel){ sub+=i.price; count++; } });
  const tax   = Math.round((sub-DESIGN_CREDIT)*TAX);
  const total = sub - DESIGN_CREDIT + tax;
  const r = APR/12;                                         // monthly financing payment
  const mon = Math.round(total * (r*Math.pow(1+r,MONTHS)) / (Math.pow(1+r,MONTHS)-1));
  animateNum('subNum','sub',sub); animateNum('taxNum','tax',tax);
  animateNum('totalNum','total',total); animateNum('monNum','mon',mon);
}
function animateNum(id,key,target){
  const el=document.getElementById(id), obj={v:tweenState[key]};
  gsap.to(obj,{ v:target, duration:.5, ease:"power2.out",
    onUpdate:()=>el.textContent=Math.round(obj.v).toLocaleString('en-US'),
    onComplete:()=>tweenState[key]=target });
}
```

Lock pattern in the row: a disabled toggle + an "Included" badge so it's clear *why* it can't be removed.

---

## 9. Step 5d — Demote the details

Put the satellite scan, submitted photo, and full measurement grid inside a `<details>` disclosure under the quote — present but not competing with the hero.

```html
<details class="disclose">
  <summary>Measurements &amp; how we analyzed your yard</summary>
  <div class="inner"><!-- annotated satellite SVG, submitted photo, measurement cards, ±note --></div>
</details>
```

Annotate the satellite with an SVG overlay (dashed boundary, dimension lines, labels) rather than baking text into the image — it stays crisp and editable.

---

## 10. Connection points — running this for REAL

The demo uses on-platform image gen + a hardcoded price book. To run it as a live estimating agent for a landscaping company, wire these up:

| Need | What to connect | Notes |
|---|---|---|
| **Lead intake / photo upload** | Field-service CRM: **Jobber, ServiceTitan, HousecallPro, Yardbook**, or a web form (Typeform/Jotform) → webhook | The trigger. Photo + address + customer contact land here. |
| **Address → coordinates** | **Google Geocoding API** | Address string → lat/lng to fetch imagery & parcel. |
| **Top-down imagery** | **Google Maps Static API** or **Mapbox Static Images**; premium: **Nearmap, EagleView** | Static API gives a clean overhead tile by lat/lng/zoom. Nearmap/EagleView give higher-res + oblique for real measuring. |
| **Real lot measurements** | Parcel/GIS: **Regrid** (parcel boundaries + area), county GIS, or **EagleView/Nearmap measurement APIs** | This replaces "best-guess" with surveyed lot area and setbacks. Still confirm hardscape sf on site. |
| **Design renders** | Image model API: **Gemini (Nano Banana) / OpenAI GPT Image** | Same consistency-lock prompt pattern as §4. Cache renders per job. |
| **Price book / estimating engine** | Company cost data in **Airtable / Google Sheets / Postgres**; or estimating tools (**Arborgold, LMN, SingleOps**) | Drive line-item prices from $/sf, labor rates, and regional multipliers instead of hardcoding. This is the part each company customizes most. |
| **Financing** | Home-improvement lenders: **Wisetack, Hearth, Sunbit, GreenSky** | Real APR/term offers + prequal link, replacing the static financing math. |
| **Deposit / payment** | **Stripe** (or QuickBooks Payments) | Collect a design deposit or scheduling deposit on approval. |
| **Approval / e-sign** | **DocuSign / Dropbox Sign**, or in-app "Approve" → status webhook | Turns the quote into a signed scope of work. |
| **Delivery** | Email (**SendGrid / Postmark**), SMS (**Twilio**), or a hosted link | Send the package back to the homeowner; track opens/clicks. |
| **Scheduling** | CRM calendar / **Google Calendar / Calendly** | "Schedule build walk" books the on-site confirmation. |

**Minimal viable real version:** web form → Geocoding + Google Static Maps → image model (3 styles) → price book in a Sheet → hosted package link emailed via SendGrid, with a Wisetack prequal button. Everything else (Nearmap, DocuSign, Stripe) is upgrade surface.

**Data shape to pass between steps (one job):**
```json
{
  "job_id": "VC-4471",
  "customer": { "name": "...", "email": "...", "phone": "..." },
  "address": "1042 Sycamore Bend, Round Rock, TX 78664",
  "coords": { "lat": 30.5, "lng": -97.6 },
  "before_url": "https://…",
  "satellite_url": "https://…",
  "measurements": { "yard_sf": 1840, "lawn_sf": 1180, "fence_lf": 132, "slab_sf": 72, "trees": 1 },
  "concepts": [
    { "key": "A", "name": "Modern Entertainer", "render_url": "https://…",
      "items": [ { "phase":"Hardscape", "name":"Paver patio", "qty":"380 sf", "price":9120, "locked":false } ] }
  ],
  "finance": { "apr": 0.0799, "months": 60 }
}
```

---

## 11. Reusable defaults

- **Palette (landscaping):** white/sand canvas, deep evergreen ink (`#17241d` / `#2f6b4f`), fresh leaf accent (`#48a877`), amber for price/CTA pops (`#d98a3d`). Avoid cream+terracotta+serif (over-trained) and any blue/purple gradients.
- **Type:** Fraunces (display) + Inter (UI/body).
- **3 default styles** that diverge meaningfully: *Modern Entertainer* (hosting/hardscape-heavy), *Lush Garden Retreat* (planting/water), *Low-Water Modern* (xeriscape/sustainable). They span budget and lifestyle, so the switch shows real range.
- **Line-item phases:** Foundations (locked) · Hardscape · Planting · Features · Finishing · Systems.
- **Always include:** a design-fee-credited line, est. sales tax, monthly financing, and an est-resale-value/ROI strip.

## 12. Honesty & legal guardrails
- Label renders as AI visualizations generated from a submitted photo.
- Measurements are estimates (±~8%) until confirmed on site; quantities adjust after the build walk.
- Pricing is a good-faith estimate, not a binding contract; final scope is signed separately.
- In demos, all company/customer/address/pricing data is fictional.
