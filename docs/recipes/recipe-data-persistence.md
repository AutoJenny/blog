# Recipe Data Persistence Architecture

## Overview

Recipe posts use a two-level association system to ensure data integrity and flexibility:

1. **Perpetual Recipe Definition** (`calendar_recipes.week_number` → `post.recipe_week_number`)
2. **Calendar Week Scheduling** (`calendar_week_posts(year, week_number, post_id)`)

## Data Model

### Recipe Definition (Perpetual)
- `calendar_recipes` table stores recipe definitions with:
  - `id` (PRIMARY KEY) - **Unique, immutable recipe identifier**
  - `week_number` (1-52) - Position in the calendar (can change when reordering)
- `post.recipe_id` links a post to its recipe definition via `calendar_recipes.id`
- **This association NEVER changes** - a recipe post always points to the same recipe definition, even if recipes are reordered
- `post.recipe_week_number` is kept for backward compatibility but should NOT be used for joins

### Calendar Week Scheduling (Flexible)
- `calendar_week_posts` table stores when/where a post is scheduled
- Can have multiple entries if a post is rescheduled (historical tracking)
- **This can change** - a recipe post can be scheduled for different calendar weeks

## Key Principles

### 1. Recipe Definition is Immutable
- `post.recipe_id` points to `calendar_recipes.id` (the unique recipe definition ID)
- This link defines **which recipe** the post is about
- **This link NEVER changes**, even if:
  - Recipes are reordered (week_number changes)
  - Recipe is rescheduled to a different calendar week
- Example: "Cullen Skink" post (recipe_id = 1) can be reordered to week 5 or scheduled for week 45, but it's always "Cullen Skink"
- `post.recipe_week_number` is maintained for backward compatibility but should NOT be used for data integrity

### 2. Calendar Scheduling is Flexible
- `calendar_week_posts(year, week_number, post_id)` stores when the post is scheduled
- Recipe posts can be rescheduled to any calendar week
- The system calculates which calendar week a recipe should map to based on current week, but manual scheduling overrides this

### 3. Data Integrity
- Recipe content (ingredients, method, etc.) is stored in `post` and `post_section` tables
- These are linked to the post via `post_id`, not calendar week
- Rescheduling does NOT affect recipe content
- The recipe definition (`calendar_recipes`) is separate from scheduling (`calendar_week_posts`)

## Example Scenario

**Initial State:**
- Recipe "Cullen Skink" is recipe week 1 (perpetual)
- Current week is 45
- Recipe posts are auto-scheduled: recipe week 1 → calendar week 45

**Post Created:**
- Post ID 82 created with `recipe_week_number = 1`
- Scheduled in `calendar_week_posts(2025, 45, 82)`

**Rescheduling:**
- User moves post 82 to calendar week 46
- `calendar_week_posts` updated: `(2025, 46, 82)`
- `post.recipe_week_number` stays `1` (still "Cullen Skink")
- Recipe content unchanged

**Result:**
- Post 82 is still "Cullen Skink" (recipe week 1)
- Now scheduled for calendar week 46 instead of 45
- All recipe sections and content remain intact

## Safety Guarantees

1. **Recipe Definition Persistence**: `post.recipe_week_number` never changes after post creation
2. **Content Persistence**: Recipe sections and content are linked to `post_id`, not calendar week
3. **Flexible Scheduling**: Posts can be moved between calendar weeks without data loss
4. **No Data Loss**: Rescheduling only affects `calendar_week_posts`, not recipe content or definition

## Potential Issues and Mitigations

### Issue: Manual Rescheduling vs. Auto-Calculation
- **Problem**: System calculates calendar week from recipe week, but user can manually schedule differently
- **Mitigation**: Manual scheduling in `calendar_week_posts` takes precedence. The calculation is only used when no schedule exists.

### Issue: Recipe Week Reordering
- **Problem**: If recipes are reordered (drag-and-drop), `calendar_recipes.week_number` changes
- **Mitigation**: This is handled by the reorder API which updates both `calendar_recipes.week_number` AND `post.recipe_week_number` atomically

### Issue: Multiple Posts for Same Recipe
- **Problem**: Could theoretically create multiple posts for the same recipe_week_number
- **Mitigation**: Recipe creation API checks for existing posts and prevents duplicates

## Recommendations

1. **Always Use `post.recipe_week_number` for Recipe Lookups**: Don't calculate calendar week to find recipe definition
2. **Use `calendar_week_posts` for Scheduling**: Check this table for when/where posts are scheduled
3. **Preserve `recipe_week_number` on Reschedule**: When moving a recipe post, update `calendar_week_posts` but keep `post.recipe_week_number` unchanged
4. **Document Recipe Content Dependencies**: Recipe sections reference `post_id`, ensuring content moves with the post

