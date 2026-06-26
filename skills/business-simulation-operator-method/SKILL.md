---
name: business-simulation-operator-method
description: >-
  A battle-tested methodology for running ANY business in real-time simulation as an
  autonomous operator agent on Hyperagent. Pick a venture — a shop, restaurant, SaaS
  product, boutique, fund, agency, nonprofit, or creator business — and the agent
  operates it day by day: calendar discipline, real-world grounding, source-of-truth
  locking, delegated authority, an operational tracker, a named persona team, finance
  honesty, risk/cadence management, and self-correction. Includes a Day-0 setup on-ramp
  and a configurable sim-clock script. Use when: Use to set up or run any sustained,
  real-time business/project simulation where an agent acts as operator and reports to a
  founder/investor — opening a shop, launching a product, running a fund or agency,
  growing a creator business, standing up a nonprofit. Start here on Day 0 to stand up a
  new simulation, and return to it whenever a running sim shows the symptoms this method
  fixes: calendar drift, fabricated entities, decisions lost after context compaction,
  asking permission for routine work, or a tracker that drifts out of sync with the
  narrative.
---

## Business Simulation Operator Method

Run a business that doesn't exist yet — in real time, as its operator. You pick the venture (a coffee shop, a restaurant, a SaaS product, a boutique, a fund, an agency, a nonprofit, a creator business), and the agent runs it day by day: making decisions, hiring a team, managing money, shipping work, and reporting to you as the founder/investor. Sim days elapse 1:1 with real days, so the business keeps moving whether or not you check in.

This is a methodology, not a fixed script — it adapts to whatever business you point it at. Every rule below was paid for by a real failure running these simulations; following them is what keeps a months-long run coherent, grounded, and trustworthy instead of drifting into fiction.

### The loop
- **You set the premise** — what the business is, where, the starting capital, and the goal with its target date.
- **The agent operates** within an agreed authority threshold: deciding and executing routine work, escalating the big calls.
- **One tracker holds the truth** — tasks, hires, finances, content, and a media library (Airtable works well).
- **The agent reports** on a cadence you choose: every check-in, or autonomously on a schedule (Hyperagent scheduled runs) so the sim advances unattended.

### Day 0 — standing up a new simulation
Do these once, before any operating happens:
1. **Define the venture & constraints.** Business type, location/market, starting capital, and the goal with a target date — "open in 130 days," "$10K MRR in 6 months," "raise and deploy a $1M fund in a year." Write them into working memory as the brief.
2. **Anchor the clock.** Pick the calendar date that is sim Day 1 and lock it in `simclock.py` (set `DAY_ONE` + your milestones). Never re-derive it later. (§1)
3. **Stand up the tracker.** Create the operational record of truth with functional tables: project mgmt, hiring, finance, content, plus a media library. (§5)
4. **Agree the autonomy threshold.** What can the agent decide and execute alone vs. escalate? Put a number on it. (§4)
5. **Staff the persona team.** Name the specialist roles this business needs and attribute work to them. (§6)
6. **Lock initial sources of truth.** Any approved location, brand, or plan becomes canonical; everything downstream conforms. (§3)
7. **Set the cadence.** How often you'll check in, and whether the agent runs autonomously between check-ins. (§9)

Then operate. Open every status update with `Day X of N · Weekday, Month D, Year` and a one-line state of the business.

### 1. Calendar discipline — the #1 failure mode
Real days elapse 1:1 with sim days, and **day-number drift is the most persistent bug** (it recurs until you fix it structurally).
- Anchor **Day 1 to a calendar date once**; always compute `sim_day = (today − day_one) + 1`. NEVER re-derive the anchor from a milestone ("Day 47 = May 14" style anchors rot when the milestone moves or was itself miscounted).
- Codify the math in a **script** (`simclock.py`), not prose. Run it at the top of every check-in.
- Record **user-confirmed checkpoints** ("today is Day X") in the script's self-test; run `--check` to catch corruption.
- When the user has been away N days, **narrate the gap** using the tracker as ground truth, then continue. The simulation advances whether or not anyone checks in.
- Open every status update with `Day X of N · Weekday, Month D, Year`.

### 2. Real-world grounding + self-audit
Fabricated addresses, vendors, and prices destroy trust and compound.
- Every named entity (location, vendor, supplier, contractor, hire, price) must be **verified against a real source** (listings, supplier/dealer pages, firm sites, market rates) before it enters the record. Search first; never invent.
- End updates with a short **self-audit**: sim-day verified, entities real, no drift, constraints honored.
- When an error is found, **log a correction entry** (what was wrong, what's right, source) — corrections are part of the record, not embarrassments to hide. When the user asks for a "clean" update, present current truth without re-litigating old errors.
- Vet entities for **fit, not just existence** (e.g. a real employment lawyer who only represents employees is the wrong real lawyer for an employer).

### 3. Source-of-truth locking
Visual and factual assets multiply; without locks they contradict each other.
- When the user approves an artifact (floor plan, exterior render, brand system, product spec, pitch deck), declare it **canonical** in working memory. Everything downstream conforms; deviations only by explicit user instruction ("don't deviate unless I say update the blueprint").
- When two truths conflict (approved plan vs. newly-found real-world data), **surface the conflict and let the user designate** which wins; record the designation.
- Maintain a hierarchy: user designation > approved artifact > verified real-world data > generated content.

### 4. Delegated authority — decide, execute, document
- Agree an explicit **autonomy threshold** scaled to the business (e.g. ≤$10K: decide and execute; above: escalate with options + a recommendation; capital injections and strategy pivots: always escalate).
- Within authority: **make the call, log it, report it in the next update** — don't ask. "You have founder power, I'm just checking in" is the model working.
- Exception: identity/branding/legal/irreversible commitments require explicit affirmative confirmation — never infer approval from ambiguous replies.

### 5. Operational record of truth (tracker)
- Keep one structured tracker (Airtable works well) with **functional tables**: project management, hiring, finance, content/social, plus **resource + media libraries** indexing every deliverable.
- **Moment-of-creation logging**: a deliverable doesn't ship until indexed; statuses move Todo → In progress → Done in the same turn as the narration. Never batch-cleanup later.
- **Integration durability**: OAuth/MCP connections can drop in long-running threads. Where possible, drive the tracker through a **REST API skill with a stored token** (via RunWithCredentials) — it survives session churn. Write payloads to JSON files and batch them.
- Mark superseded assets `Replaced`/`Archived` rather than deleting; any backfilled history should follow **realistic real-world timelines** (e.g. permit reviews, hiring cycles, sales ramps).

### 6. Persona team
- Staff the simulation with **named specialist subagent personas** sized to the business, and attribute work to them in every update — it keeps the narrative legible and maps cleanly to real dispatched subagents for research/drafting. (A café: GM, head barista, social, web, HR. A SaaS: PM, growth lead, support, eng. A fund: analyst, IR, ops. An agency: ECD, account lead, producer.)
- Operating principle: **AI handles volume; humans handle stakes** — in-sim, the high-stakes calls (terminations, legal sign-off, the craft itself) stay with "real" people/services; budget for them.

### 7. Working memory + learning hygiene
- Maintain a **thread context doc** (decisions, corrections, numbers, plan tasks) updated as things happen — it's what survives context compaction. Re-read it at the start of every check-in.
- **Memory bloat is dangerous, not just messy**: an auto-saved memory duplicating a wrong fact (a bad calendar anchor) re-injects the error every turn even after you fix it in-conversation. Fix canonical facts at **all roots**: the brief/system prompt, the one canonical memory, and the script. Disable auto-save memories; prune duplicates.
- Codify recurring procedures as **skills** (sim clock, API client, media pipeline) so they're drift-proof and reusable.

### 8. Finance honesty
- Build projections from **verified real costs**; when reality lands (true payroll burden, equipment or CAC overruns), **re-baseline publicly** and show the variance ledger (what ran over, what absorbed it).
- Distinguish **planned losses** (funded, expected) from surprises. Track cash position at every update. Name future decision points (bridge/runway triggers) before they arrive.

### 9. Risk + cadence
- Actively scan for **sequencing risks** (inspection scheduled 1 day before launch = zero buffer) and fix them by re-sequencing early, not by hoping.
- For unattended/live runs (Hyperagent scheduled invocations): check the tracker for overdue + due-soon items, apply a **repetition guard** (only alert on material change), and report all-clear silently.
- Surface immediately only what crosses materiality (cash impact, launch timing, strategy); stay quiet on routine days.

### 10. Media discipline
- **No speculative media** — generate images/video only when requested or when the sim timeline puts that production at the current moment; otherwise log content as task records (concept, owner, deadline).
- For published webpage artifacts: external image URLs can fail — **compress (≤1600px JPEG) and inline as base64**; fetch generated assets via pre-signed URLs.

### Helper script
`simclock.py` — a generic real-time sim-clock template. Configure `DAY_ONE`, `MILESTONES`, and `CHECKPOINTS` for your venture, then run `--check` to self-test the anchor against user-confirmed days. This is the structural fix for the #1 failure mode (calendar drift).
