# Product Tag Editor - Implementation Proposal

## Overview
A new dedicated page for bulk tag editing operations, built incrementally with reusable components.

## URL Structure
- Main page: `/products/tag-editor`
- Can accept query params for initial filtering/search

## Phase 1: Search & Display (MVP)
**Goal**: Find products and display them like Tag Browser

### Components to Reuse:
1. **`product_search_component.html`** - Product search at top
2. **Tag Browser product grid** - Display results in same format
3. **Tag Browser CSS** - Reuse styling

### Features:
- Search products (simple + smart search)
- Display results in grid format (same as Tag Browser)
- Click product to view in Product Browser (new tab)
- Show product count

### Implementation:
- New blueprint: `product_tag_editor.py`
- New template: `templates/products/tag_editor.html`
- Reuse `get_products_by_tag()` logic from Tag Browser
- Add API endpoint for search results

---

## Phase 2: Selection & Group Management
**Goal**: Select products and manage groups

### New Components:
1. **Selection UI** - Checkboxes on product cards
2. **Selected Products Panel** - Sidebar showing selected count
3. **Group Actions** - Add/remove from current group

### Features:
- Checkbox on each product card
- "Select All" / "Deselect All" buttons
- Selected products panel (collapsible sidebar)
- Show selected count
- "Add to Group" / "Remove from Group" buttons
- Save/load product groups (localStorage or session)

### UI Layout:
```
┌─────────────────────────────────────────────────┐
│  Product Search Component                      │
├─────────────────────────────────────────────────┤
│  [Selected: 5] [Select All] [Clear]            │
├──────────────────┬─────────────────────────────┤
│                  │  Products Grid              │
│  Selected Panel  │  (with checkboxes)          │
│  (collapsible)   │                             │
│                  │                             │
│  [5 products]    │                             │
│  [Clear]         │                             │
│                  │                             │
│  [Add to Group]  │                             │
│  [Remove from]   │                             │
└──────────────────┴─────────────────────────────┘
```

---

## Phase 3: Bulk Tag Operations
**Goal**: Apply tags to selected products in bulk

### New Components:
1. **Bulk Tag Editor Panel** - Similar to Tag Editor modal but for bulk
2. **Tag Assignment UI** - Checkboxes for available tags
3. **Preview Changes** - Show what will be applied

### Features:
- "Bulk Edit Tags" button (enabled when products selected)
- Modal/panel showing all available tags
- Checkboxes for each tag category
- Preview: "Will add X tags to Y products"
- Apply button with confirmation
- Progress indicator for bulk operations
- Undo capability (store previous state)

### Tag Operations:
- **Add tags**: Add selected tags to all selected products
- **Remove tags**: Remove selected tags from all selected products
- **Replace tags**: Replace specific tag with another
- **Clear tags**: Remove all tags of a category

---

## Phase 4: Advanced Features
**Goal**: Enhanced filtering and grouping

### Features:
- Filter by multiple tags (AND/OR logic)
- Save filter presets
- Export selected products (CSV/JSON)
- Tag statistics for selected group
- Batch operations history/log
- Tag suggestions based on product attributes

---

## Component Reuse Strategy

### From Tag Browser:
- ✅ Product grid display (`products-grid`, `product-card`)
- ✅ Product card styling
- ✅ Product count display
- ✅ `get_products_by_tag()` function

### From Product Browser:
- ✅ Tag Editor modal (for individual products)
- ✅ Product data structure

### From Product Search Component:
- ✅ Search UI (already standalone)

### New Components Needed:
1. **`product_selection_grid.html`** - Product grid with checkboxes
2. **`selected_products_panel.html`** - Sidebar for selected products
3. **`bulk_tag_editor.html`** - Bulk tag editing interface
4. **`product_group_manager.html`** - Save/load product groups

---

## File Structure

```
blueprints/
  └── product_tag_editor.py          # New blueprint

templates/
  └── products/
      └── tag_editor.html            # Main page template

templates/includes/
  ├── product_search_component.html  # ✅ Already exists
  ├── product_selection_grid.html    # New: Grid with checkboxes
  ├── selected_products_panel.html   # New: Selection sidebar
  ├── bulk_tag_editor.html           # New: Bulk editing UI
  └── product_group_manager.html     # New: Group management

static/css/
  └── products/
      └── tag-editor.css             # New: Styles for editor page

static/js/
  └── products/
      └── tag-editor.js              # New: Selection & bulk operations
```

---

## API Endpoints Needed

### Phase 1:
- `GET /products/tag-editor` - Main page
- `GET /products/tag-editor/api/search` - Search products (reuse existing)

### Phase 2:
- `POST /products/tag-editor/api/group` - Save product group
- `GET /products/tag-editor/api/group/<id>` - Load product group

### Phase 3:
- `POST /products/tag-editor/api/bulk-tags` - Apply bulk tag operations
- `GET /products/tag-editor/api/preview` - Preview bulk changes

---

## Implementation Order

1. **Create basic page** with search component
2. **Add product grid** (reuse Tag Browser display)
3. **Add selection checkboxes** to product cards
4. **Add selected products panel**
5. **Add bulk tag editor** modal/panel
6. **Implement bulk operations** API
7. **Add group management** features
8. **Polish and optimize**

---

## Benefits of This Approach

1. **Incremental**: Build and test each phase
2. **Reusable**: Leverage existing components
3. **Maintainable**: Clear separation of concerns
4. **Extensible**: Easy to add features later
5. **User-friendly**: Familiar UI patterns

---

## Alternative: Enhance Tag Browser

**Pros:**
- Single interface
- Less navigation

**Cons:**
- Mixes browsing and editing concerns
- More complex codebase
- Harder to test incrementally

**Recommendation**: Keep Tag Browser for browsing, create dedicated editor page.

