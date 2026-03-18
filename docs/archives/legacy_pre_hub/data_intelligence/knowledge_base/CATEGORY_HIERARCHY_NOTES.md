# Knowledge Base Category Hierarchy Notes

**Source:** CLAN.com Tech Team  
**Date:** 2025-11-11

---

## Key Points

### Category Structure
- Categories are **not sorted into a tree structure**
- The `level` field represents the **position in the hierarchy**, not a tree depth

### Level Meanings
- **Level 4**: Main category
- **Level 5**: Sub-category
- **Level 6+**: Sub-sub-category

### Field Definitions

#### `level` (INTEGER)
- Position in the hierarchy
- Not a tree depth indicator
- Use with `parent_id` and `path` to understand relationships

#### `position` (INTEGER)
- Sort order within its parent category
- Determines display order for siblings

#### `path` (TEXT)
- Full category path showing all parent categories
- Format: Slash-separated list of category IDs
- Example: `"1/58/188/72/194/196/215"`
  - This shows the complete ancestry from root (1) to current category (215)
- Useful for:
  - Building breadcrumbs
  - Finding all ancestors
  - Understanding full category context

#### `parent_id` (INTEGER)
- Direct parent category ID
- Self-referential foreign key to `clan_kb_categories.id`
- NULL for root-level categories

#### `children_count` (INTEGER)
- Number of direct child categories
- Updated by CLAN.com system

---

## Usage Examples

### Building a Category Tree
```sql
-- Get all categories with their hierarchy info
SELECT 
    id,
    name,
    level,
    parent_id,
    path,
    position,
    children_count
FROM clan_kb_categories
ORDER BY level, position;
```

### Finding All Ancestors
```sql
-- For a category with path "1/58/188/72"
-- Get all ancestor IDs
SELECT unnest(string_to_array(path, '/')::int[]) as ancestor_id
FROM clan_kb_categories
WHERE id = 72;
```

### Getting Siblings
```sql
-- Get all categories at the same level with the same parent
SELECT *
FROM clan_kb_categories
WHERE parent_id = 58
ORDER BY position;
```

### Building Breadcrumbs
```python
def get_breadcrumbs(category_id):
    """Build breadcrumb trail from path"""
    cursor.execute("SELECT path FROM clan_kb_categories WHERE id = %s", (category_id,))
    path = cursor.fetchone()[0]
    
    if not path:
        return []
    
    ancestor_ids = [int(id) for id in path.split('/')]
    cursor.execute("""
        SELECT id, name FROM clan_kb_categories 
        WHERE id = ANY(%s)
        ORDER BY array_position(%s, id)
    """, (ancestor_ids, ancestor_ids))
    
    return cursor.fetchall()
```

---

## Implementation Notes

Our current implementation:
- ✅ Stores `level`, `parent_id`, `path`, `position`, `children_count`
- ✅ Sorts categories by `level` when storing (parents before children)
- ✅ Handles missing parent categories gracefully (sets `parent_id` to NULL)
- ✅ Uses `path` field for understanding full hierarchy

**Future Enhancements:**
- Could add a helper function to parse `path` and build breadcrumbs
- Could add a view or function to get category tree structure
- Could add UI component to display category hierarchy

---

**Last Updated:** 2025-11-11

