---
name: airtable-kanban-work-tracker
description: >-
  Track your work as records on an Airtable Kanban board: one thread per record, flipping
  each record from an in-progress status to a ready-for-review status as you work, and
  creating new task records when asked. A general, reusable workflow for any base or
  table using the connected Airtable integration. Use when the user wants you to track
  your tasks or deliverables in an Airtable table used as a Kanban board — pick up a
  record, mark it in-progress while you work in a thread, and flip it to ready-for-review
  (with links) when you finish. Also use when they ask you to create new task records on
  that board, or to set up such a board for the first time. Triggers: "track this in
  Airtable", "update the board", "move it to review", "log this as a task", "one thread
  per card".
---

# Airtable Kanban Work Tracker

Track your own work as rows on an Airtable table used as a Kanban board. Each task or deliverable is **one record**, each record maps to **one conversation thread**, and you advance each record's **Status** as you work — from an *in-progress* state when you start to a *ready-for-review* state when you finish. Optionally create new task records when the user hands you work.

This skill is integration-driven: it uses the user's connected **Airtable** integration via `ExecuteIntegration({ action, params })`. There are no scripts and no API keys to manage — if Airtable is connected, the actions below are available.

---

## The mental model

A spreadsheet row becomes a Kanban card. You are one of the workers on the board. Your job is to keep the board **honest and current** so a human glancing at it always knows what is in flight and what is waiting on them.

Three rules carry the whole workflow:

1. **One thread per record.** A single record represents one unit of work, and all the work for it happens in one thread. Link the record to its thread so the row deep-links back to the conversation.
2. **Status is a handoff signal, not decoration.** Two statuses do the real work:
   - an **in-progress** status — set it the moment you *start* working in a turn;
   - a **ready-for-review** status — set it as the *last* action of a turn, once the deliverable is ready for a human.
3. **Bracket every work turn.** First action of a turn: find the record, set it in-progress. Last action: set it ready-for-review with links filled in. Do the actual work in between. This bracketing is what makes the board trustworthy.

> **You own the lane from in-progress → ready-for-review. The human owns everything downstream** (Approved, Shipped, Done, Archived, Won't-do, etc.). Never set a downstream status unless the user explicitly tells you to. The point of the review status is to hand control back to them.

---

## Prerequisites

- The user has connected **Airtable** (Settings → Integrations). If actions fail with an unreachable / not-linked error, ask them to toggle the Airtable integration off and back on to re-link it, then retry.
- You know — or will ask the user for — the target **base** and **table**. If they only describe it in words ("my content board"), discover it (see *Discovering IDs* below) and confirm with them before writing.

---

## Step 0 — Confirm the available actions

Action names depend on how the integration is connected. Run `SearchIntegrations({ query: "airtable" })` once to confirm. (The payload is large and usually spills to a file — grep the file for action names rather than reading it whole.) With the native Airtable MCP integration the actions are prefixed `airtable__`:

| Purpose | Action |
|---|---|
| Find a base | `airtable__list_bases`, `airtable__search_bases` |
| List tables + fields in a base | `airtable__list_tables_for_base` |
| Detailed field config (e.g. select choices) | `airtable__get_table_schema` |
| Free-text search for a record | `airtable__search_records` |
| List / filter / sort records | `airtable__list_records_for_table` |
| Create records | `airtable__create_records_for_table` |
| Update records (and upsert) | `airtable__update_records_for_table` |
| Delete records | `airtable__delete_records_for_table` |
| Add a field (needs schema-write scope) | `airtable__create_field` |
| Create a table (needs schema-write scope) | `airtable__create_table` |

Call any of them as `ExecuteIntegration({ action: "airtable__...", params: { ... } })`. If the workspace exposes a different prefix, use whatever `SearchIntegrations` reports — the parameter shapes are the same.

---

## Step 1 — Learn the board (do this once, then remember it)

You must never **guess** base IDs, table IDs, field IDs, or single-select option names. Discover them:

1. **Base** → `airtable__list_bases` (or `airtable__search_bases` with a name) → grab the `app...` ID.
2. **Table + fields** → `airtable__list_tables_for_base` with `{ baseId }`. This returns every table with its fields (name, type, and field ID). This is your primary tool for learning **field IDs**.
3. **Select options** → if you need the exact option names/IDs of a single-select Status field, call `airtable__get_table_schema` with `{ baseId, tables: [{ tableId, fieldIds: ["fld..."] }] }` (note: `fieldIds` is required, minItems 1 — pass the Status field's ID).

A usable board needs at minimum:

| Field | Type | Why |
|---|---|---|
| **Title / Name** (the table's primary field) | single line text | what the task is |
| **Status** | single select | the Kanban lane; must include an in-progress option and a ready-for-review option |
| **Thread URL** | url (or single line text) | links the record to its thread (one thread per record) |
| *Artifact / Output URL* (recommended) | url | the finished deliverable |
| *Notes* (optional) | long text | short progress note / blockers |

**Persist the mapping.** Once you've learned the baseId, tableId, the Status field ID + its exact option names, and the Thread-URL / Artifact-URL field IDs, save them (propose a memory, or record them in your working notes) so you don't re-discover the schema every turn. Re-confirm only if a write fails because an ID or option name changed.

### If the board doesn't exist yet

- If you have schema-write scope, you can `airtable__create_table` and/or `airtable__create_field`. Create a single-select Status like:
  `ExecuteIntegration({ action: "airtable__create_field", params: { baseId, tableId, field: { name: "Status", type: "singleSelect", options: { choices: [{ name: "Backlog" }, { name: "In Progress" }, { name: "Ready for Review" }, { name: "Done" }] } } } })`
  and a url field: `{ name: "Thread URL", type: "url" }`.
- **If `create_field` / `create_table` returns 403**, the connected token lacks schema-write scope. Don't fight it. Ask the user to add the Status / Thread URL / Artifact URL fields in the Airtable UI (or grant schema-write scope), then continue. **Record create/read/update — everything this skill actually needs at runtime — works without schema-write scope.**

### Choosing status names

The option names are the user's choice — adapt to whatever already exists on their board. Common shapes:
- Minimal: **In Progress** → **Ready for Review**
- Fuller: **Backlog** → **In Progress** → **Ready for Review** → **Done**

If the board's status options are unclear or you'd be inventing them, **ask the user which option means "I'm working on it" and which means "ready for your review"** rather than guessing. You only ever set those two.

---

## Step 2 — The work loop (every execution turn)

### A. Start of turn → set IN PROGRESS

1. **Find the record for this thread.** Two reliable ways:
   - *By thread link* (preferred when the record already exists): list records filtered on the Thread URL field equals this thread's URL — `airtable__list_records_for_table` with `filters`.
   - *By title*: `airtable__search_records` with a free-text query of the task name (fuzzy, word-order independent).
   In most ongoing workflows the record **already exists** — search first; only create if it's genuinely missing (and the user wants it tracked).
2. **Set Status → in-progress** and write the thread link if not already set:
   ```
   ExecuteIntegration({ action: "airtable__update_records_for_table", params: {
     baseId, tableId,
     records: [{ id: "recXXXXXXXXXXXXXX", fields: {
       "fldStatusId": "In Progress",
       "fldThreadUrlId": "https://hyperagent.com/thread/<THIS_THREAD_ID>"
     }}]
   }})
   ```
   Use **this thread's** ID/URL (available in your context) so the row deep-links back here.

> Flip to in-progress **before** doing research, generation, or build work — not after. On a revision pass, flip back to in-progress first, then work, then back to review.

### B. Do the work

Complete the actual task in this thread.

### C. End of turn → set READY FOR REVIEW (last action)

As the **final** action of the turn, update the record:
```
ExecuteIntegration({ action: "airtable__update_records_for_table", params: {
  baseId, tableId,
  records: [{ id: "recXXXXXXXXXXXXXX", fields: {
    "fldStatusId": "Ready for Review",
    "fldArtifactUrlId": "<link to the deliverable>",
    "fldNotesId": "One-line summary of what's ready / any open question"
  }}]
}})
```
Setting ready-for-review is the signal that you're handing the work back. Stop there — let the human take it onward.

---

## Creating records

When the user hands you new work to track (or you discover the record is missing), create it:
```
ExecuteIntegration({ action: "airtable__create_records_for_table", params: {
  baseId, tableId,
  records: [{ fields: {
    "fldTitleId": "Short task title",
    "fldStatusId": "In Progress",
    "fldThreadUrlId": "https://hyperagent.com/thread/<THIS_THREAD_ID>"
  }}],
  fieldIds: ["fldTitleId", "fldStatusId"]   // optional: also return these in the response
}})
```
- Up to **50 records per request**; batch larger sets across multiple calls.
- New work you're about to start → create at the in-progress status. Work the user is queuing for later → create at a backlog status if one exists.
- Don't create duplicates: search by title / thread URL first.

### Find-or-create in one call (upsert)

If your board has a **unique** field to merge on (e.g. Thread URL), `update_records_for_table` supports upsert — it updates a match or creates a new record if none exists:
```
ExecuteIntegration({ action: "airtable__update_records_for_table", params: {
  baseId, tableId,
  performUpsert: { fieldIdsToMergeOn: ["fldThreadUrlId"] },
  records: [{ fields: {
    "fldThreadUrlId": "https://hyperagent.com/thread/<THIS_THREAD_ID>",
    "fldTitleId": "Short task title",
    "fldStatusId": "In Progress"
  }}]
}})
```
The merge field must be unique and non-computed; multiple matches make the request fail. This is the cleanest way to guarantee one record per thread.

---

## Airtable action reference & gotchas

**Always pass `baseId` (camelCase).** IDs follow fixed shapes: base `app...`, table `tbl...`, field `fld...`, record `rec...`. Never substitute user-facing names where an ID is required.

- **`list_tables_for_base`** `{ baseId }` → all tables with field names, types, and IDs. Your go-to for discovering field IDs.
- **`get_table_schema`** `{ baseId, tables: [{ tableId, fieldIds: ["fld..."] }] }` → detailed config for the named fields. `fieldIds` is **required** (≥1). Use it to read a single-select field's exact choices.
- **`search_records`** `{ baseId, table, query, fields }` → fuzzy full-text search; `table` accepts an ID or name; `fields` is an array of field IDs/names or the literal `"ALL_SEARCHABLE_FIELDS"`. Note: date, rating, checkbox, and button fields aren't indexed — filter those with `list_records_for_table` instead. (Param key here is **`table`**.)
- **`list_records_for_table`** `{ baseId, tableId, fieldIds?, pageSize?, cursor?, sort?, filters?, recordIds? }`:
  - `tableId` accepts an ID or a table name. (Param key here is **`tableId`**, not `table` — the two read actions differ.)
  - **Sorting** uses `sort: [{ fieldId, direction: "asc"|"desc" }]` — the key is **`fieldId`**, not `field`.
  - **Filtering** uses a structured `filters` object: `{ operator: "and"|"or", operands: [{ fieldId, operator: "=", value }, ...] }`. Do **not** pass `filterByFormula`. For single-select equality use `=` / `!=` / `isAnyOf`.
  - **Pagination**: send `cursor` (omit on the first page); read `nextCursor` from the response to fetch the next page. Keep `pageSize` modest (25–50) for wide tables — large pages can exceed the tool result limit and spill to a file (then parse the JSON with Node/Python).
- **`create_records_for_table`** / **`update_records_for_table`** `{ baseId, tableId, records: [{ id?, fields: { "fldXXX": value } }] }`:
  - Field keys are **field IDs** (stable across renames); names also work but IDs are safer.
  - `update` requires each record's `id` (unless using `performUpsert`). `create` never takes an `id`.
  - Up to **50 records per request**.
  - Optional `fieldIds: [...]` controls which fields are echoed back; `typecast: true` enables best-effort string→type coercion.

### Single-select values: read vs write are asymmetric

When you **read** a single-select (or multi-select) value it comes back as an **object** — `{ "id": "sel...", "name": "In Progress", "color": "blue" }` (or an array of them). When you **write** it, use the **plain option-name string** — `"In Progress"` — never the object, and never the `sel...` id. The option name must already exist on the field (unless you have schema-write scope and add it).

---

## Pitfalls

- **Guessing IDs or option names.** A wrong field ID can write to the wrong column; a wrong record ID can clobber a different row. Discover via `list_tables_for_base`; persist the mapping.
- **Forgetting to bracket the turn.** If you do the work but never flip to in-progress at the start and review at the end, the board lies. The status changes are not optional polish — they're the deliverable's metadata.
- **Setting downstream statuses.** Don't mark anything Approved / Shipped / Done unless told. Ready-for-review is your stop line.
- **Creating duplicate records.** Search by title or thread URL (or upsert on a unique field) before creating.
- **`field` vs `fieldId` vs `table` vs `tableId`.** Sorting uses `fieldId`; `search_records` uses `table`; `list/create/update` use `tableId`. Mixing them up returns validation errors.
- **Schema-write 403.** Adding fields/tables needs schema-write scope; record CRUD does not. If field creation 403s, ask the user to add fields in the UI and proceed with CRUD.
- **Integration unreachable.** If Airtable actions fail as not-linked/unreachable, have the user toggle the Airtable integration off and on to re-link, then retry — don't silently substitute a different base or table.
