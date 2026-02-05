# Phase H-5 — Engine Comparison & “Current Output” Selection (Report)

**Phase:** H-5  
**Title:** Engine Comparison & “Current Output” Selection (UI + API integration)  
**Date:** 2026-03-01  
**Preconditions:** Phase H-0, H-1, H-2, H-3, H-4 complete and merged.

---

## 1. Objective

Enable the user to:

1. Run the same prompt through multiple engines
2. View outputs side-by-side
3. Explicitly select which output is current
4. Replace assets selectively and deterministically

After H-5, the system can answer: *“Which prompt, through which engine, produced the asset we are publishing right now?”*

---

## 2. Slot model decision (“primary”)

For blog_post workbench, **slot_identifier** is defined as:

- **slot_identifier = `"primary"`**

Rationale: blog_post currently produces one publishable artifact per run. Slide-level slots are deferred until carousel/image-specific work. This keeps H-5 minimal and correct.

**Current output rule:** For each `(content_ref, platform, channel_type, slot_identifier)` exactly one run is marked as current. “Current” means: the output used by posting_queue, post_now, and scheduling. Changing current output does not delete runs; runs remain immutable.

---

## 3. Storage changes

### 3.1 New table: `workbench_current_outputs`

**Migration:** `migrations/20260301_create_workbench_current_outputs.sql`

| Column             | Type         | Notes                                      |
|--------------------|--------------|--------------------------------------------|
| id                 | SERIAL       | Primary key                                |
| content_ref        | INTEGER      | NOT NULL (e.g. post_id for blog_post)     |
| platform           | TEXT         | NOT NULL                                   |
| channel_type       | TEXT         | NOT NULL                                   |
| slot_identifier    | TEXT         | NOT NULL DEFAULT 'primary'                 |
| run_id             | INTEGER      | NOT NULL (generation_runs.id)              |
| updated_at         | TIMESTAMPTZ  | NOT NULL DEFAULT NOW()                     |

**Constraints:** `UNIQUE(content_ref, platform, channel_type, slot_identifier)`  
**Index:** `idx_workbench_current_outputs_item` on `(content_ref, platform, channel_type, slot_identifier)`  
**Behaviour:** One row per (content_ref, platform, channel_type, slot_identifier). Upsert on selection; no deletes required. Table and column comments document Phase H-5 and slot/run semantics.

**Rationale:** Avoids mutating `generation_runs`; avoids overloading `posting_queue`; keeps “current” separate from “history”.

---

## 4. API list and example payloads

All workbench API routes are under the launchpad blueprint (prefix `/launchpad`).

### 4.1 Engine discovery

**GET** `/launchpad/api/workbench/engines`

**Returns:** Array of `{ "engine_id": string, "label": string }`.

**Example response:**

```json
[
  { "engine_id": "text/ollama-mistral", "label": "Default (Ollama Mistral)" },
  { "engine_id": "text/default", "label": "Default" },
  { "engine_id": "image/image-1", "label": "Image-1" },
  { "engine_id": "image/sdxl", "label": "SDXL" }
]
```

Notes: Static list; no engine-specific UI branching; engines are parameters only.

---

### 4.2 Multi-engine run (extended)

**POST** `/launchpad/api/workbench/run`

**Body:** `content_ref`, `platform`, `channel_type`, `engine_id` (optional, default e.g. `text/ollama-mistral`), `slot_identifier` (optional, default `primary`), `trigger` (optional).

**Example request:**

```json
{
  "content_ref": 123,
  "platform": "instagram",
  "channel_type": "blog_post",
  "engine_id": "image/sdxl",
  "slot_identifier": "primary",
  "trigger": "user"
}
```

Behaviour: Creates a new run in `generation_runs` with the given engine and slot; same prompt, different engine, same slot is allowed. No single-engine assumption.

---

### 4.3 Set current output

**POST** `/launchpad/api/workbench/current-output`

**Body:**

```json
{
  "content_ref": 123,
  "platform": "instagram",
  "channel_type": "blog_post",
  "slot_identifier": "primary",
  "run_id": 456
}
```

Behaviour: Upsert into `workbench_current_outputs`; returns success and current state (`run_id`, `updated_at`).

---

### 4.4 Get current output

**GET** `/launchpad/api/workbench/current-output`

**Query:** `content_ref` (required), `platform`, `channel_type`, `slot_identifier` (default `primary`).

**Example:** `GET /launchpad/api/workbench/current-output?content_ref=123&platform=instagram&channel_type=blog_post&slot_identifier=primary`

**Returns:** Current run and output refs for the slot, e.g.:

```json
{
  "success": true,
  "run_id": 456,
  "run": { "id": 456, "engine_id": "image/sdxl", "output_refs": { "posting_queue_id": 789 }, ... },
  "output_refs": { "posting_queue_id": 789 },
  "updated_at": "2026-03-01T12:00:00Z"
}
```

If no current output is set: `run_id: null`, `run: null`, `output_refs: null`.

---

## 5. UI behaviour walkthrough

### 5.1 Regeneration controls (extended)

- **Engine selector:** Dropdown `#workbench-engine-select` populated from `GET /launchpad/api/workbench/engines`. No hardcoded engine names in template; default engine pre-selected in dropdown.
- **“Run with engine” action:** Button `#workbench-regenerate-btn` sends `POST /launchpad/api/workbench/run` with `content_ref`, `platform`, `channel_type` from `window.pageData`, selected `engine_id`, and `slot_identifier: "primary"`. On success, runs list and current-output state are refreshed.

### 5.2 Asset comparison panel (interactive)

- **Display:** Two columns `#comparison-left`, `#comparison-right`. User selects runs in Generation History; the last two selected fill left and right. Each side shows: engine label, timestamp, generated content (from queue API via run’s `output_refs.posting_queue_id`), and **“Use this output”** button.
- **“Use this output”:** Calls `POST /launchpad/api/workbench/current-output` with `content_ref`, `platform`, `channel_type`, `slot_identifier: "primary"`, and the run’s `run_id`. On success, selection is updated and the UI marks that run as current (e.g. “✓ Current” in History and in comparison cards).

### 5.3 Current output indicator

- **Generation History:** The run that is current for the slot is marked with “✓ Current” in the list (`#generation-history-list`).
- **Prompt Inspector:** When viewing a run’s prompt, if that run is the current output, the label shows “Prompt for current output”; otherwise “Prompt used for this run” or “Current prompt” as in H-4.

### 5.4 Data flow

- On post selection (`postSelected`): load prompt, runs, and current output (`GET current-output`); render history with current marker; comparison uses last two selected runs.
- After “Run with engine” or “Use this output”: reload runs and current output so History and comparison stay in sync.

---

## 6. Proof of persistence

- **Current output:** Stored in `workbench_current_outputs` with `UNIQUE(content_ref, platform, channel_type, slot_identifier)`. Upsert on “Use this output” updates `run_id` and `updated_at`; no delete. Page reload loads current output via `GET /launchpad/api/workbench/current-output` and displays “✓ Current” and “Prompt for current output” accordingly.
- **Runs:** Immutable; new runs appended to `generation_runs`; current-output table only references `run_id`. History remains full; selection is independent of run creation.

---

## 7. Risks and deferrals

- **Posting/scheduling consumption of current output:** The *design* is that the run marked current is the one whose output is used by posting_queue, post_now, and scheduling. Resolution would be: for a given (content_ref, platform, channel_type), read `workbench_current_outputs.run_id` → `generation_runs.output_refs.posting_queue_id` and use that queue item for display and publish. If this wiring is not yet implemented in launchpad post_now/schedule/queue display, it is an explicit follow-up integration step after H-5 sign-off.
- **Slot-level image control (carousel slides), hybrid prompt decomposition, prompt version graphs, batch regeneration, SDXL tuning, UI polish:** Explicitly out of scope for H-5; to be discussed only after H-5 sign-off.

---

## 8. Behavioural guarantees (confirmed)

After H-5:

- Same prompt → two engines → two runs (multi-engine run supported).
- Both outputs visible side-by-side (comparison panel with left/right from History selection).
- User can explicitly select which output is current (“Use this output” → POST current-output).
- Current selection persists across reload (stored in `workbench_current_outputs`; loaded on page load).
- History remains immutable (no delete/retry/edit of runs).
- FB and IG unified (same workbench template and JS; platform from `pageData`).

---

## 9. Stop statement (verbatim)

**Phase H-5 introduced multi-engine comparison and explicit current-output selection in the Unified Channel Workbench. Outputs are now traceable, comparable, and user-selectable. No generator internals, carousel behaviour, or unrelated UI were modified.**
