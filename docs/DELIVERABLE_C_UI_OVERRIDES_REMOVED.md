# Deliverable C — UI-only overrides removed

**Step 3:** Remove JS that overwrites `primaryRole` for product/message/language/depth_long so the UI shows the role actually stored on the item (or "UNSET_ROLE") plus content_type/category.

---

## Removed overrides

| Location | What was removed |
|----------|------------------|
| `static/js/planning/calendar-week-view.js`, inside `renderItems()` (approx lines 185–231) | For `weekly-word` / `weekly-phrase` / `weekly-insult`: **removed** `primaryRole = primaryRole \|\| 'CULTURE'`. Display now uses `displayRole = item.role \|\| 'UNSET_ROLE'` and typeName is e.g. `"UNSET_ROLE — Language: Word"`. |
| Same block | For `product`: **removed** `primaryRole = primaryRole \|\| 'COMMERCE'`. TypeName is now `"<displayRole> — Product"` with displayRole = item.role or 'UNSET_ROLE'. |
| Same block | For `message`: **removed** `primaryRole = primaryRole \|\| 'REASSURANCE'`. TypeName is now `"<displayRole> — Message"`. |
| Same block | For `depth_long`: **removed** `primaryRole = primaryRole \|\| 'DEPTH_LONG'`. TypeName is now `"<displayRole> — Deep Dive"`. |

---

## Current behaviour

- **primaryRole** is never overwritten; it stays `item.role || null`.
- **displayRole** = `primaryRole || 'UNSET_ROLE'` is used only for the visible label.
- **typeName** for Social Posts row items is built as `"<displayRole> — <angleLabel>"` (e.g. "UNSET_ROLE — Product", "UNSET_ROLE — Message", "DEPTH_LONG — Deep Dive" when role is set).

Items that are not yet scheduled with the correct Matrix role will show "UNSET_ROLE" in the label until scheduling is fixed (Step 4/5).
