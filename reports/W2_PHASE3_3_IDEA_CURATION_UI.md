# W2 Phase 3.3 — Idea curation UI (selection + category)

## Screenshot placeholder

- `reports/screenshots/W2_PHASE3_IDEA_CURATION.png` — Ideas page showing the required-ideas editor with:
  - Checkbox, text input, category dropdown, and delete button per row.
  - Selected / category counters and Select all / Select none controls.

---

## Backend: required-ideas API extensions

File: `blueprints/planning_api_post_metadata.py`

### GET `/planning/api/posts/<post_id>/required-ideas`

Now returns full metadata for each idea:

```sql
SELECT id,
       post_id,
       text,
       sort_order,
       category,
       rationale,
       source_urls,
       rank,
       is_selected
FROM post_required_idea
WHERE post_id = %s
ORDER BY sort_order ASC, id ASC;
```

Mapped to JSON:

```json
{
  "success": true,
  "required_ideas": [
    {
      "id": 221,
      "text": "Idea 1",
      "sort_order": 0,
      "category": "history_timeline",
      "rationale": "Rationale 1",
      "source_urls": [],
      "rank": 1,
      "is_selected": true
    },
    ...
  ]
}
```

Verbatim curl for post 729:

```bash
curl -s http://localhost:5000/planning/api/posts/729/required-ideas | jq
```

Output (excerpt):

```json
{
  "required_ideas": [
    {
      "category": "history_timeline",
      "id": 221,
      "is_selected": true,
      "rank": 1,
      "rationale": "Rationale 1",
      "sort_order": 0,
      "source_urls": [],
      "text": "Idea 1"
    },
    {
      "category": "definitions_differences",
      "id": 222,
      "is_selected": true,
      "rank": 2,
      "rationale": "Rationale 2",
      "sort_order": 1,
      "source_urls": [],
      "text": "Idea 2"
    },
    ...
  ],
  "success": true
}
```

### PATCH `/planning/api/posts/<post_id>/required-ideas/items/<item_id>`

Now supports updating:

- `text`
- `category`
- `is_selected`
- `rank`
- `rationale` (optional)
- `source_urls` (optional)
- `sort_order` (already supported)

Implementation sketch (final code in file):

```python
data = request.get_json() or {}
text = data.get('text')
sort_order = data.get('sort_order')
category = data.get('category')
is_selected = data.get('is_selected')
rank = data.get('rank')
rationale = data.get('rationale')
source_urls = data.get('source_urls')

# Start from current values
new_text = row.get('text') or ''
new_sort_order = row.get('sort_order', 0)
new_category = row.get('category')
new_is_selected = row.get('is_selected', True)
new_rank = row.get('rank')
new_rationale = row.get('rationale')
new_source_urls = row.get('source_urls')

...  # override with provided fields

cursor.execute(
    """
    UPDATE post_required_idea
       SET text = %s,
           sort_order = %s,
           category = %s,
           rationale = %s,
           source_urls = %s,
           rank = %s,
           is_selected = %s
     WHERE post_id = %s AND id = %s
    """,
    (...),
)
```

Example PATCH for post 729, idea 221:

```bash
curl -s -X PATCH \
  http://localhost:5000/planning/api/posts/729/required-ideas/items/221 \
  -H "Content-Type: application/json" \
  -d '{"is_selected":false,"category":"modern_revival"}' | jq
```

Response:

```json
{
  "required_idea": {
    "category": "modern_revival",
    "id": 221,
    "is_selected": false,
    "rank": 1,
    "rationale": "Rationale 1",
    "sort_order": 0,
    "source_urls": [],
    "text": "Idea 1"
  },
  "success": true
}
```

---

## Frontend: structured curation editor (ideas.html)

File: `templates/planning/calendar/ideas.html`

### Summary of UI changes

- **Per row**:
  - Checkbox → `is_selected` (PATCH on change).
  - Text input → `text` (PATCH on blur).
  - Category dropdown → controlled list (`IDEA_CATEGORY_OPTIONS`) plus “custom…” entry with companion input.
  - Delete button → DELETE item.
- **Page-level controls**:
  - “Select all” / “Select none” buttons (issue per-row PATCHes).
  - Live counters:
    - `Selected: X (min 10)` — based on `is_selected`.
    - `Categories: Y (min 3)` — distinct categories among selected.

### Key JS additions

Controlled category list:

```javascript
const IDEA_CATEGORY_OPTIONS = [
  'history_timeline',
  'definitions_differences',
  'material_craft',
  'regional_variation',
  'myths_misconceptions',
  'notable_examples',
  'modern_revival',
  'how_to_practical',
  'sources_further_reading'
];
```

Rendering rows (excerpt):

```javascript
ideasList.innerHTML = requiredIdeas.map((idea) => {
  const id = idea.id;
  const text = escapeHtml(getIdeaText(idea));
  const category = idea.category || '';
  const isSelected = idea.is_selected !== false;
  const categoryOptions = IDEA_CATEGORY_OPTIONS.map(cat => `
      <option value="${cat}" ${cat === category ? 'selected' : ''}>${cat}</option>
  `).join('');
  const customSelected = category && !IDEA_CATEGORY_OPTIONS.includes(category) ? 'selected' : '';
  const customValue = !IDEA_CATEGORY_OPTIONS.includes(category || '') ? escapeHtml(category || '') : '';
  return `
  <div class="idea-item" ...>
      <input type="checkbox"
             ${isSelected ? 'checked' : ''}
             onchange="updateIdeaSelected(${id}, this.checked)">
      <input type="text"
             value="${text}"
             onblur="updateIdeaText(${id}, this.value)"
             ...>
      <select onchange="updateIdeaCategory(${id}, this.value, this.nextElementSibling)" ...>
          <option value="">(uncategorised)</option>
          ${categoryOptions}
          <option value="__custom__" ${customSelected}>custom…</option>
      </select>
      <input type="text"
             placeholder="Custom category"
             value="${customValue}"
             onblur="updateIdeaCustomCategory(${id}, this.value)"
             ...>
      <button type="button"
              onclick="deleteRequiredIdea(${id})">...</button>
  </div>
  `;
}).join('');
updateRequiredIdeasCounters();
```

Update helpers:

```javascript
async function patchRequiredIdea(id, payload) { ... }  // calls PATCH endpoint and refreshes row

function updateIdeaSelected(id, isSelected) {
  patchRequiredIdea(id, { is_selected: isSelected });
}

function updateIdeaText(id, text) {
  patchRequiredIdea(id, { text: text });
}

function updateIdeaCategory(id, value, customInput) {
  if (value === '__custom__') {
    if (customInput) customInput.focus();
    return;
  }
  patchRequiredIdea(id, { category: value || null });
}

function updateIdeaCustomCategory(id, value) {
  const trimmed = value.trim();
  if (!trimmed) {
    patchRequiredIdea(id, { category: null });
  } else {
    patchRequiredIdea(id, { category: trimmed });
  }
}
```

Counters:

```javascript
function updateRequiredIdeasCounters() {
  const selected = requiredIdeas.filter(idea => idea.is_selected !== false);
  const categories = new Set(
      selected
          .map(idea => idea.category)
          .filter(cat => typeof cat === 'string' && cat.trim().length > 0)
  );
  document.getElementById('required-ideas-selected-count').textContent = String(selected.length);
  document.getElementById('required-ideas-category-count').textContent = String(categories.size);
}
```

Select all / none:

```javascript
function selectAllRequiredIdeas() {
  const updates = requiredIdeas
      .filter(idea => idea.is_selected === false)
      .map(idea => patchRequiredIdea(idea.id, { is_selected: true }));
  Promise.all(updates);
}

function selectNoneRequiredIdeas() {
  const updates = requiredIdeas
      .filter(idea => idea.is_selected !== false)
      .map(idea => patchRequiredIdea(idea.id, { is_selected: false }));
  Promise.all(updates);
}
```

All changes are persisted immediately via the API; there is no local-only state beyond the `requiredIdeas` array mirrored from responses.

---

## SQL proof after manual edits

After toggling `is_selected` to `false` and setting `category = 'modern_revival'` for idea `id = 221`:

```bash
psql -d blog -c "
SELECT post_id,
       COUNT(*) FILTER (WHERE is_selected) AS selected,
       COUNT(DISTINCT category) AS categories
FROM post_required_idea
WHERE post_id = 729
GROUP BY post_id;
"
```

Output:

```text
 post_id | selected | categories 
---------+----------+------------
     729 |       29 |          6
(1 row)
```

This confirms:

- Selection changes (`is_selected`) are persisted.
- Category changes are persisted and reflected in the distinct category count.

---

## Confirmation line

Post 729 curation UI allows toggling selection and category; counters update live; persisted values match DB.

