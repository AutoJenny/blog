# W2 Section structure contract (8.3)

## Model

Sections are stored in **post_section** (existing table). Structure is deterministic: generated from required ideas only; initially one section per required idea; user can merge, split, reorder.

---

## Table (existing)

`post_section` columns include: `id`, `post_id`, `section_order`, `section_heading`, `section_description`, `draft`, `ideas_to_include`, etc. (see schema).

---

## Rules

- **Generated from required ideas only:** Section generation uses `post_required_idea` (or equivalent source); no silent injection from week/theme.
- **Initial shape:** 1 section per required idea (when generating structure).
- **User actions:** Merge, split, reorder sections allowed.
- **Hard requirement to advance (structure → titling):** `COUNT(post_section WHERE post_id = ?) >= 3`.

---

## Enforcement

- In `advance_post_stage(post_id)`, transition **structure → titling** requires `_count_sections(post_id) >= 3` (see `utils/posts/early_stage.py`).
