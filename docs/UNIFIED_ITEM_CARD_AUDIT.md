# Unified Item Card Component - Audit Report

## Current Implementations

### 1. Week-View Tab (`static/js/planning/calendar-week-view.js`)
- **Function:** `buildItemCard(item, options)`
- **Approach:** DOM manipulation
- **Type class:** `type-${type}` (e.g., `type-theme`, `type-recipe`)
- **Status logic:** `postStatus = item.post_status ? item.post_status.toLowerCase() : null`
- **Post exists:** `postExists = !!(postId)` where `postId = item.post_id || item.id`
- **Buttons:** Play (create), Rocket (1-click), Info (modal)
- **Data source:** `/planning/api/calendar/schedule/{year}/{week}`

### 2. Publication-Schedule Tab (`templates/planning/calendar/includes/publication_schedule_scripts.html`)
- **Function:** `setItemCardContent(itemCard, item, options)`
- **Approach:** innerHTML string building
- **Type class:** Missing! Only `item-card` (no type class)
- **Status logic:** `postStatus = options?.postExists ? (item.post_status || 'draft') : (item.post_status || null)`
- **Post exists:** `postExists = item.post_exists === true || (item.post_id !== null && item.post_id !== undefined)`
- **Buttons:** Play (create), Rocket (1-click), Info (modal)
- **Data source:** `/publication/api/dashboard/schedule` (missing year/week params!)
- **Issue:** API defaults to current week, not URL year/week

### 3. Scheduling Tab (`templates/planning/calendar/includes/scheduling_scripts.html`)
- **Function:** Inline card creation in `createCategoryCell()`
- **Approach:** DOM manipulation
- **Type class:** `type-${categoryClass}` (e.g., `type-theme`, `type-profile-product`)
- **Status logic:** Always "Not created" (hardcoded)
- **Post exists:** Not checked
- **Buttons:** Play (modal), Rocket (week-view), Info (modal)
- **Data source:** Various APIs per category

## Type/Category Mappings

### Week-View Types:
- `idea` → `type-theme`
- `recipe` → `type-recipe`
- `profile` → `type-profile`
- `weekly-word` → `type-weekly-word`
- `weekly-phrase` → `type-weekly-phrase`
- `weekly-insult` → `type-weekly-insult`
- `event` → `type-event`
- `scheduled` → `type-scheduled`

### Publication-Schedule Categories:
- `theme` → should be `type-theme`
- `recipe` → should be `type-recipe`
- `profile_product` → should be `type-profile-product`
- `profile_surname` → should be `type-profile-surname`
- `weekly_word` → should be `type-weekly-word`
- `weekly_phrase` → should be `type-weekly-phrase`
- `weekly_insult` → should be `type-weekly-insult`
- `product` → should be `type-product`

### Scheduling Categories:
- `theme` → `type-theme`
- `recipe` → `type-recipe`
- `profile-product` → `type-profile-product`
- `profile-surname` → `type-profile-surname`
- `word` → `type-word`
- `phrase` → `type-phrase`
- `insult` → `type-insult`

## CSS Type Styles Required

From `week_view_styles.html`:
- `.item-card.type-theme`
- `.item-card.type-recipe`
- `.item-card.type-profile`
- `.item-card.type-weekly-word`
- `.item-card.type-weekly-phrase`
- `.item-card.type-weekly-insult`
- `.item-card.type-event`
- `.item-card.type-scheduled`

Missing in publication-schedule styles:
- All type-specific styles

## Data Structure Differences

### Week-View Item:
```javascript
{
  id: number,
  post_id: number | null,
  post_status: string | null,
  title: string,
  theme_title: string,
  recipe_title: string,
  description: string,
  year: number,
  week: number
}
```

### Publication-Schedule Item:
```javascript
{
  category: string,
  item_id: number,
  post_id: number | null,
  post_exists: boolean,
  post_status: string | null,
  title: string,
  description: string,
  year: number,
  week: number,
  channel: string,
  type_name: string
}
```

### Scheduling Item:
```javascript
{
  id: number,
  theme_id: number,
  recipe_id: number,
  post_id: number | null,
  post_status: string | null,
  theme_title: string,
  recipe_title: string,
  post_title: string,
  position: number
}
```

## Action Handlers

### Week-View:
- **Create:** `onCreate` callback or `item._onCreate`
- **Rocket:** Navigate to `/launchpad/one-click-publication?post_id={postId}&output=blog`
- **Info:** `onInfo` callback

### Publication-Schedule:
- **Start (no post):** `createPostFromItem(item, itemCard)` - Creates post and navigates to first workflow stage
- **Pipeline (has post):** `navigateToPipeline(item, postId)` - Navigates to first workflow stage (sitemap icon)
  - Recipes: `/posts/{postId}/sections/drafting`
  - Themes: `/planning/posts/{postId}/calendar/ideas`
  - Profiles: `/planning/posts/{postId}/calendar/taxonomy`
- **Rocket (has post):** `navigateToOneClick(item)` - Navigates to 1-click publication view
- **Info (no post only):** `openItemModal(item)` - Opens item details modal
- **Title (has post):** Clickable - navigates to pipeline
- **Card click:** `openItemModal(item)` (only if no post exists)

### Scheduling:
- **Create/Play:** `openItemModal(item, categoryClass, itemId, position, year, week)`
- **Rocket:** Navigate to `/planning/calendar?year={year}&week={week}&tab=week-view`
- **Info:** `openItemModal(item, categoryClass, itemId, position, year, week)`
- **Card click:** `openItemModal(...)`

## Issues to Fix

1. **Publication-schedule missing year/week in API call**
2. **Publication-schedule missing type CSS classes**
3. **Publication-schedule missing type CSS styles**
4. **Inconsistent status determination logic**
5. **Inconsistent type/category naming**
6. **Scheduling always shows "Not created"**
7. **Different rendering approaches (DOM vs innerHTML)**

## Unified Component Requirements

1. **Single function** that works for all tabs
2. **Consistent type class naming** (normalize category → type)
3. **Consistent status determination** (unified logic)
4. **DOM manipulation** (not innerHTML for better event handling)
5. **Configurable action handlers** (callbacks for different contexts)
6. **Support all data structures** (normalize input)
7. **Include all required CSS classes**
8. **Support optional features** (description, draggable, etc.)

