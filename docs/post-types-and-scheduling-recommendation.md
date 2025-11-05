# Post Types & Publication Scheduling - Recommendation

## Executive Summary

The system currently handles multiple post types (themed posts, recipe posts, profile posts, cross-promotion posts) but lacks:
1. **Visual distinction** in the `/posts` UI
2. **Per-post-type publication scheduling** (different days of the week for different types)
3. **Integration** with the one-click blog automation system

## Current State Analysis

### Post Type Identification

Currently, posts are identified by database fields:
- **Recipe Posts**: `post.recipe_week_number IS NOT NULL`
- **Profile Posts**: `post.profile_category_id IS NOT NULL`
- **Cross-Promotion Posts**: `post.cross_promotion_category_id IS NOT NULL`
- **Themed Posts**: Have entries in `calendar_week_posts` or `calendar_schedule` (no specific category field)

### Publication Scheduling

Currently:
- `calendar_week_posts.weekday` field exists (1=Monday, 7=Sunday)
- Default publication day is Wednesday (hardcoded in `automation_calendar.py`)
- No per-post-type scheduling configuration
- One-click blog system doesn't check post type before scheduling

## Recommended Solution

### Phase 1: Post Type Configuration Table

Create a `post_type_config` table to store publication preferences per post type:

```sql
CREATE TABLE post_type_config (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL UNIQUE, -- 'themed', 'recipe', 'profile', 'cross_promotion'
    default_publication_day INTEGER NOT NULL CHECK (default_publication_day BETWEEN 1 AND 7), -- 1=Monday, 7=Sunday
    default_publication_time TIME DEFAULT '14:00:00',
    timezone VARCHAR(50) DEFAULT 'Europe/London',
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Default configuration
INSERT INTO post_type_config (post_type, default_publication_day, default_publication_time, description) VALUES
    ('themed', 3, '14:00:00', 'Regular themed blog posts - Wednesday'),
    ('recipe', 1, '10:00:00', 'Scottish Recipe Series - Monday'),
    ('profile', 4, '14:00:00', 'Product/Category Profiles - Thursday'),
    ('cross_promotion', 5, '14:00:00', 'Cross-Promotion Posts - Friday');
```

### Phase 2: UI Distinction in Posts List

**File**: `templates/posts_list.html`

Add visual indicators:
1. **Type Badge Column**: Show post type with color-coded badges
2. **Filter Toggle**: Allow filtering by post type
3. **Icon Indicators**: Different icons for each type (utensils for recipes, etc.)

**Implementation**:
```html
<th data-key="type" data-type="string" class="sortable">Type</th>
<!-- In tbody -->
<td>
    {% if post.is_recipe %}
        <span class="post-type-badge recipe-badge">
            <i class="fas fa-utensils"></i> Recipe
        </span>
    {% elif post.is_profile %}
        <span class="post-type-badge profile-badge">
            <i class="fas fa-tag"></i> Profile
        </span>
    {% elif post.is_cross_promotion %}
        <span class="post-type-badge cross-promo-badge">
            <i class="fas fa-link"></i> Cross-Promo
        </span>
    {% else %}
        <span class="post-type-badge themed-badge">
            <i class="fas fa-book"></i> Themed
        </span>
    {% endif %}
</td>
```

**CSS Styling**:
```css
.post-type-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.recipe-badge { background: #fef3c7; color: #92400e; }
.themed-badge { background: #dbeafe; color: #1e40af; }
.profile-badge { background: #e0e7ff; color: #4338ca; }
.cross-promo-badge { background: #fce7f3; color: #9f1239; }
```

### Phase 3: Backend Post Type Detection

**File**: `blueprints/posts.py`

Modify the posts list query to include type detection:

```python
cursor.execute("""
    SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
           p.recipe_week_number, p.profile_category_id, p.cross_promotion_category_id,
           cwp.year AS sched_year, cwp.week_number AS sched_week, cwp.scheduled_date, cwp.weekday
    FROM post p
    LEFT JOIN LATERAL (
        SELECT year, week_number, scheduled_date, weekday, updated_at
        FROM calendar_week_posts
        WHERE post_id = p.id
        ORDER BY scheduled_date DESC NULLS LAST, updated_at DESC
        LIMIT 1
    ) cwp ON TRUE
    WHERE p.status != 'deleted'
    ORDER BY p.updated_at DESC, p.id DESC
""")
```

Then in formatting:
```python
formatted_posts.append({
    # ... existing fields ...
    'is_recipe': post.get('recipe_week_number') is not None,
    'is_profile': post.get('profile_category_id') is not None,
    'is_cross_promotion': post.get('cross_promotion_category_id') is not None,
    'post_type': determine_post_type(post),
    'publication_day': get_publication_day(post, cursor)
})
```

### Phase 4: Publication Day Scheduling

**File**: `blueprints/automation_calendar.py` and `blueprints/recipes.py`

Modify scheduling logic to use `post_type_config`:

```python
def get_publication_day_for_post_type(post_type: str, cursor) -> int:
    """Get default publication day for a post type."""
    cursor.execute("""
        SELECT default_publication_day, default_publication_time
        FROM post_type_config
        WHERE post_type = %s AND is_active = TRUE
    """, (post_type,))
    result = cursor.fetchone()
    if result:
        return result['default_publication_day']
    return 3  # Default to Wednesday
```

### Phase 5: One-Click Blog Integration

**File**: `templates/launchpad/one_click_blog_minimal.html` and related automation

1. **Recipe Post Creation**: When creating recipe posts, check `post_type_config` for recipe publication day
2. **Themed Post Creation**: Use themed post publication day
3. **Calendar Integration**: When scheduling, set `weekday` based on post type

**Implementation**:
```javascript
// In runWeekIdeas or recipe creation
async function scheduleRecipePost(postId, weekNumber, year) {
    const response = await fetch('/api/post-type-config/recipe');
    const config = await response.json();
    
    // Calculate publication date based on week and day
    const weekStart = getWeekStart(year, weekNumber);
    const publicationDay = config.default_publication_day; // 1=Monday
    const publicationDate = weekStart + (publicationDay - 1) days;
    
    // Schedule in calendar_week_posts
    await fetch('/planning/api/calendar/week-posts', {
        method: 'POST',
        body: JSON.stringify({
            year, week_number: weekNumber, post_id: postId,
            weekday: publicationDay,
            scheduled_date: publicationDate
        })
    });
}
```

### Phase 6: Automated Recipe Post Publication

**New File**: `blueprints/automation_recipe_publisher.py`

Create automated system to:
1. Check current week's recipe
2. Verify if post exists and is ready
3. Schedule publication on recipe's default day (Monday)
4. Publish at scheduled time

```python
@bp.route('/api/recipes/auto-publish', methods=['POST'])
def auto_publish_recipe():
    """Automated recipe post publication for current week."""
    # Get current week number (1-52)
    current_week = get_current_week_number()
    
    # Get recipe for this week
    recipe = get_recipe_by_week(current_week)
    
    # Check if post exists and is ready
    post = get_post_by_recipe_week(current_week)
    
    if not post or post.status != 'ready':
        return jsonify({'error': 'Recipe post not ready'}), 400
    
    # Get recipe publication day from config
    publication_day = get_publication_day_for_post_type('recipe', cursor)
    
    # Schedule publication
    schedule_recipe_publication(post.id, current_week, publication_day)
    
    return jsonify({'success': True})
```

## Implementation Priority

### High Priority (Immediate)
1. ✅ **UI Distinction**: Add type badges to posts list
2. ✅ **Post Type Detection**: Update backend to identify post types
3. ✅ **Publication Day Config**: Create `post_type_config` table

### Medium Priority (This Sprint)
4. ✅ **Scheduling Logic**: Update automation to use post type config
5. ✅ **One-Click Integration**: Update recipe creation to use correct day

### Low Priority (Future)
6. ✅ **Automated Publishing**: Full automation for recipe posts
7. ✅ **Type Filtering**: Add filter dropdown in UI
8. ✅ **Type Statistics**: Show counts per type in dashboard

## Database Migration

```sql
-- Migration: Add post type configuration
-- File: migrations/create_post_type_config.sql

CREATE TABLE post_type_config (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL UNIQUE,
    default_publication_day INTEGER NOT NULL CHECK (default_publication_day BETWEEN 1 AND 7),
    default_publication_time TIME DEFAULT '14:00:00',
    timezone VARCHAR(50) DEFAULT 'Europe/London',
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_post_type_config_active ON post_type_config(is_active) WHERE is_active = TRUE;

-- Insert defaults
INSERT INTO post_type_config (post_type, default_publication_day, default_publication_time, description) VALUES
    ('themed', 3, '14:00:00', 'Regular themed blog posts - Wednesday'),
    ('recipe', 1, '10:00:00', 'Scottish Recipe Series - Monday mornings'),
    ('profile', 4, '14:00:00', 'Product/Category Profiles - Thursday'),
    ('cross_promotion', 5, '14:00:00', 'Cross-Promotion Posts - Friday');

COMMENT ON TABLE post_type_config IS 'Configuration for post type publication schedules';
COMMENT ON COLUMN post_type_config.post_type IS 'Type identifier: themed, recipe, profile, cross_promotion';
COMMENT ON COLUMN post_type_config.default_publication_day IS 'Day of week (1=Monday, 7=Sunday)';
```

## API Endpoints Needed

```python
# Get post type configuration
GET /api/post-type-config/<post_type>
GET /api/post-type-config

# Update post type configuration
PUT /api/post-type-config/<post_type>

# Get publication day for a post
GET /api/posts/<post_id>/publication-day
```

## Testing Checklist

- [ ] Recipe posts show with recipe badge in posts list
- [ ] Themed posts show with themed badge
- [ ] Recipe posts scheduled on Monday (or configured day)
- [ ] Themed posts scheduled on Wednesday (or configured day)
- [ ] One-click blog creates recipe posts with correct weekday
- [ ] Calendar view shows correct publication days
- [ ] Filter by type works in posts list
- [ ] Automated recipe publisher works correctly

## Benefits

1. **Clear Visual Distinction**: Users can immediately see post types
2. **Flexible Scheduling**: Different post types can publish on different days
3. **Automation Ready**: System can automatically schedule based on post type
4. **Scalable**: Easy to add new post types in the future
5. **User-Friendly**: Clear UI makes content management easier

