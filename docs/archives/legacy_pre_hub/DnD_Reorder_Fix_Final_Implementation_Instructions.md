# Drag & Drop Reordering – Final Implementation Instructions

A complete, clarified, unified specification for how the frontend and backend must implement correct drag-and-drop reordering in the JSON-backed calendar scheduling system.

-------------------------------------------------------------------------------

# 1. Overview

The existing drag-and-drop behaviour is incorrect because it always moves an item by **+1 position**, ignoring the target week where the user drops the item. The system must instead compute the **correct sequence position** for the drop target using the same cyclic logic the backend uses for weekly scheduling.

This document defines the full corrected behaviour, required backend changes, required frontend logic, edge-case handling, and implementation instructions for the coder.

-------------------------------------------------------------------------------

# 2. The Only Correct Formula (standardised)

**The system uses "week-only" mode** — not year-aware absolute weeks.

Backend, JSON builder, and frontend must all use:

```
absolute_week = week

position = ((absolute_week - cycle_start_week) % list_length + list_length) % list_length + 1
```

This produces stable, predictable, repeatable sequences every year, unless modified by a reorder or manual edit.

-------------------------------------------------------------------------------

# 3. What Drag & Drop Must Do

When a user drags an item from Week A → drops it onto Week B:

1. Determine the week number the user dropped onto (`targetWeek`).

2. Fetch list metadata for that category:

   - `list_length`

   - `cycle_start_week`

   - `items[]` (the full list with positions)

3. Compute the target position:

   ```
   targetPosition =
     ((targetWeek - cycle_start_week) % list_length + list_length) % list_length + 1
   ```

4. Call the **existing reorder API**:

   ```
   POST /planning/api/calendar/list/reorder
   {
       "category": "theme",
       "item_id": draggedItemId,
       "new_position": targetPosition
   }
   ```

5. Backend updates the list permanently.

6. JSON rebuild occurs (immediately or queued).

7. UI reloads the schedule.

-------------------------------------------------------------------------------

# 4. Required Backend Changes

## 4.1 Extend `/list/get` (preferred)  

Instead of creating a new endpoint, the existing endpoint that returns list items must be extended to also return the metadata needed for drag-and-drop.

### REQUIRED Response Structure:

```json
{
  "success": true,
  "category": "theme",
  "items": [
    { "id": 101, "position": 1, "title": "Theme 1" },
    { "id": 102, "position": 2, "title": "Theme 2" }
  ],
  "meta": {
    "list_length": 52,
    "cycle_start_week": 1
  }
}
```

### Backend responsibilities:

- `list_length` = count of items in the DB for that category.

- `cycle_start_week`:

  - from `calendar_category_cycles.cycle_start_week`

  - if missing, return **1**

- Always include a `meta` object with exactly those keys.

This ensures the frontend always has the required inputs to compute correct positions.

-------------------------------------------------------------------------------

# 5. Required Frontend Changes

## 5.1 Stop using hardcoded `currentPos + 1`

This line must be deleted:

```javascript
newPosition = currentPos + 1;
```

It is the root cause of incorrect behaviour.

## 5.2 On drop, fetch category metadata

Inside `moveItemToWeek(category, itemId, targetYear, targetWeek)` call:

```
GET /planning/api/calendar/list/get?category=<category>
```

Use the returned:

- `meta.list_length`

- `meta.cycle_start_week`

- `items[]` (if needed)

## 5.3 Compute the correct target position

Use:

```javascript
const listLength = meta.list_length;
const cycleStartWeek = meta.cycle_start_week || 1;

const targetPosition =
   ((targetWeek - cycleStartWeek) % listLength + listLength) % listLength + 1;
```

## 5.4 Issue reorder request

Call:

```javascript
POST /planning/api/calendar/list/reorder
{
  category,
  item_id: itemId,
  new_position: targetPosition
}
```

## 5.5 Reload UI

After success, use your standard page reload or re-fetch.

-------------------------------------------------------------------------------

# 6. Edge Cases

## 6.1 Missing or NULL `cycle_start_week`

Backend:

- If no row in `calendar_category_cycles` or value is null → return `1`.

Frontend:

- If missing or falsy → treat as `1`.

## 6.2 Empty list (`list_length == 0`)

Frontend:

- Disable drag & drop for that category, or:

- On drop, alert: "Cannot reorder; list is empty."

Backend:

- `/list/reorder` should reject reorders when `list_length == 0`.

## 6.3 Out-of-range positions

The cyclic position formula always yields a valid 1–N position if N ≥ 1.  

Still, add a safety check before calling reorder.

## 6.4 Year does not influence position

- `year` is only used to pick the correct JSON file.

- Position is always computed based on **week-only** mode.

-------------------------------------------------------------------------------

# 7. Behavioural Summary (must match implementation)

### Dragging an item onto a week:

- Computes where that week sits in the cyclic sequence.

- Moves the dragged item **into that position**.

- Permanently updates the base sequence in the DB.

- JSON for affected years is rebuilt.

- Display updates accordingly.

### No temporary overrides  

Everything is **permanent** after reorder.

-------------------------------------------------------------------------------

# 8. What the Coder Must Implement (checklist)

### Backend

- [ ] Extend `/list/get` to return `meta.list_length` and `meta.cycle_start_week`.

- [ ] Ensure `cycle_start_week` defaults to `1` if missing.

- [ ] Ensure reorder updates DB and triggers JSON rebuild.

### Frontend

- [ ] Replace incorrect `currentPos + 1` logic.

- [ ] Fetch metadata via `/list/get`.

- [ ] Compute `targetPosition` using the standard formula.

- [ ] Call reorder API with computed target position.

- [ ] Reload schedule.

### After implementation

- Drag & drop moves items accurately.

- No overrides.

- Permanent sequence changes.

- Backend and frontend use identical logic.

-------------------------------------------------------------------------------

# 9. End of Document

