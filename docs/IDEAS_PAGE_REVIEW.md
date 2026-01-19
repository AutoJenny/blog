# Ideas Page Review - Quick Assessment

**Date:** 2026-01-19  
**Page:** `/planning/posts/705/calendar/ideas?year=2026&week=4`  
**Purpose:** Quick review of current state and missing functionality

---

## Current State Analysis

### Two Different Ideas Pages

#### 1. Post-Based Ideas Page (`ideas.html`)
**Route:** `/planning/posts/<post_id>/calendar/ideas?year=<year>&week=<week>`  
**Template:** `templates/planning/calendar/ideas.html`  
**Blueprint:** `blueprints/planning_calendar_clean.py::planning_calendar_ideas()`

**Current Functionality:**
- ✅ Generates expanded idea from already-selected theme
- ✅ LLM module with prompt editing
- ✅ Week context handling
- ❌ **NO idea/theme selection UI**
- ❌ **NO confirmation flow**
- ❌ **NO navigation to next stage**

**Assumption:** Post already exists with theme selected, so this page is just for generating expanded idea.

---

#### 2. Week-Based Ideas Page (`ideas_week.html`)
**Route:** `/planning/calendar/ideas/week/<week_number>?year=<year>`  
**Template:** `templates/planning/calendar/ideas_week.html`  
**Blueprint:** `blueprints/planning_calendar_clean.py::planning_calendar_ideas_week()`

**Current Functionality:**
- ✅ Shows available themes for week
- ✅ Theme selection UI
- ✅ Selected theme display
- ✅ Confirmation button ("Create Post")
- ✅ Creates post when confirmed
- ❌ **Does NOT generate expanded idea automatically**
- ❌ **Does NOT navigate to next stage automatically**

**Assumption:** This is for creating NEW posts by selecting a theme.

---

## Current Flow (Inferred)

### Manual Flow (Current)
```
1. User visits week-based ideas page
   → Selects theme
   → Clicks "Create Post"
   → Post created with idea_seed set

2. User manually navigates to post-based ideas page
   → Generates expanded idea
   → Manually navigates to next stage (taxonomy/brainstorm)
```

### Expected Flow (From Refinement Points)
```
1. User visits ideas page (post-based)
   → Shows available themes for week
   → User selects theme
   → Confirms selection
   → Post created/updated
   → Expanded idea auto-generated
   → Auto-navigate to next stage
```

---

## Missing Functionality (Post-Based Ideas Page)

### 1. Theme Selection UI
**Missing:**
- Available themes list for the week
- Theme selection interface
- Selected theme display

**Dependencies:**
- Need to query themes for the week
- Use unified calendar resolver or query `calendar_themes` directly
- Display similar to `ideas_week.html`

---

### 2. Confirmation Flow
**Missing:**
- "Confirm & Generate" button
- Post creation/update logic
- Expanded idea auto-generation after confirmation

**Dependencies:**
- Use existing `confirm_calendar_idea()` API endpoint
- Or create new endpoint for post-based flow
- Auto-trigger expanded idea generation

---

### 3. Navigation to Next Stage
**Missing:**
- "Next Stage" button
- Auto-navigation after expanded idea generated
- Progress indicator

**Dependencies:**
- Determine next stage (taxonomy or brainstorm)
- Add navigation JavaScript
- Update workflow tracking

---

## Dependencies Identified

### 1. Calendar Data Source
**Question:** Should we use:
- `calendar_themes` table directly?
- Unified calendar resolver (`resolve_item_for_week()`)?
- `calendar_week_selection_v2` to get selected theme?

**Current:** Post-based page assumes theme already selected (fetches from `calendar_week_selection_v2` via API)

---

### 2. Post Creation Logic
**Question:** If post doesn't exist, should we:
- Create post immediately?
- Or redirect to week-based ideas page?

**Current:** Post must exist (post_id in URL)

---

### 3. Expanded Idea Generation
**Question:** Should expanded idea:
- Auto-generate after theme confirmation?
- Or remain manual (user clicks "Generate")?

**Current:** Manual generation only

---

## Recommendations

### Option A: Enhance Post-Based Page
**Add to `ideas.html`:**
1. Theme selection UI (if theme not yet selected)
2. Confirmation flow
3. Auto-generate expanded idea
4. Auto-navigate to next stage

**Pros:**
- Single entry point
- Consistent with refinement goals
- Better UX

**Cons:**
- More complex page
- Need to handle both "theme selected" and "theme not selected" states

---

### Option B: Keep Separate, Improve Flow
**Keep two pages but:**
1. Week-based page: Auto-generate expanded idea after post creation
2. Week-based page: Auto-navigate to post-based ideas page
3. Post-based page: Add "Next Stage" button

**Pros:**
- Simpler pages
- Clear separation of concerns

**Cons:**
- Two entry points
- More navigation steps

---

### Option C: Hybrid Approach
**Post-based page:**
- If theme not selected: Show selection UI (like week-based page)
- If theme selected: Show expanded idea generation (current)
- After generation: Auto-navigate to next stage

**Pros:**
- Single entry point
- Handles both states
- Progressive enhancement

**Cons:**
- More complex logic
- Need state detection

---

## Next Steps

1. **Decide on approach** (A, B, or C)
2. **Fix calendar sync** (affects theme selection)
3. **Add navigation** (affects all stages)
4. **Implement chosen approach** for ideas page

---

## Critical Dependencies for Ideas Page Refinement

### Must Fix First:
1. ✅ **Calendar sync** - Need unified calendar resolver working
2. ✅ **Navigation system** - Need "Next" button infrastructure

### Can Fix After:
3. Theme selection UI
4. Confirmation flow
5. Auto-generation
6. Auto-navigation

---

**Conclusion:** Ideas page refinement depends on broader fixes (calendar sync, navigation). Should proceed with broader fixes first, then refine ideas page.

---

**Last Updated:** 2026-01-19
