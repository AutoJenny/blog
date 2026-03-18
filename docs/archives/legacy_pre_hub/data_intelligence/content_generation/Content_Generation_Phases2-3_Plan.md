# Phases 2-3: Content Generation & UI Integration
**Date:** 2025-01-10  
**Status:** Planning  
**Dependencies:** Phase 1 (Vector Search) must be complete

---

## Phase 2: Content Generation Engine

### Overview
Build LLM-driven content generation that uses vector search results to create blog posts about products/categories.

---

### 2.1 Retrieval Integration

**Reuse Phase 1 API:**
- Use `POST /api/content/search` from Phase 1
- Query vector index for relevant chunks
- Get top-K results with metadata

**Implementation:**
```python
from utils.vector_search.retrieval import ContentRetriever

retriever = ContentRetriever()
results = retriever.search(
    query="Scottish tartan scarves",
    chunk_types=["product", "category"],
    limit=5
)
```

---

### 2.2 Prompt Templates

**Location:** Store in `llm_prompt` table (existing system)

**Template Types:**

#### A. Product Deep-Dive Template
**Name:** `product_content_generation`

**Purpose:** Generate blog post about a specific product

**Template Structure:**
```
You are writing a blog post about a Scottish product for CLAN.com.

Product Information:
{product_context}

Related Products/Categories:
{related_chunks}

Write a blog post that:
1. Introduces the product with cultural/historical context
2. Describes the craftsmanship and materials
3. Explains its significance in Scottish culture
4. Includes practical information (sizing, care, etc.)
5. Maintains CLAN's warm, professional Scottish tone

Generate:
- Headline (engaging, SEO-friendly)
- Standfirst (one-sentence summary)
- 3-5 content sections with headings
- Each section should be 150-300 words
```

**Variables:**
- `{product_context}` - Retrieved chunk for the selected product
- `{related_chunks}` - Additional relevant chunks (similar products, category info)

#### B. Category Feature Template
**Name:** `category_content_generation`

**Purpose:** Generate blog post about a product category

**Template Structure:**
```
You are writing a blog post about a Scottish product category for CLAN.com.

Category Information:
{category_context}

Representative Products:
{product_chunks}

Write a blog post that:
1. Explores the category's historical origins
2. Describes traditional methods and materials
3. Highlights cultural significance
4. Features representative products
5. Maintains CLAN's warm, professional Scottish tone

Generate:
- Headline
- Standfirst
- 4-6 content sections
- Include product recommendations section
```

#### C. Product Comparison Template
**Name:** `product_comparison_generation`

**Purpose:** Compare products within a category

**Template Structure:**
```
Compare these Scottish products for a CLAN.com blog post:

Products:
{product_chunks}

Category Context:
{category_context}

Write a comparison that:
1. Highlights similarities and differences
2. Explains when to choose each product
3. Maintains CLAN's warm, professional Scottish tone

Generate:
- Headline
- Standfirst
- Comparison sections
```

**Implementation:**
- Store templates in `llm_prompt` table
- Use existing `LLMService` from `modules/llm_service.py`
- Follow existing prompt selection pattern (like Profiles system)

---

### 2.3 LLM Integration

**Use Existing Infrastructure:**
- `modules/llm_service.py` - `LLMService` class
- Supports Ollama (local) and OpenAI (cloud)
- Already integrated with prompt system

**Generation Function:**
```python
from modules.llm_service import LLMService

llm = LLMService()

# Generate content using template
result = llm.generate(
    prompt_template_id=prompt_id,
    variables={
        'product_context': product_chunk['chunk_text'],
        'related_chunks': format_related_chunks(related_chunks)
    },
    model='ollama',  # or 'openai'
    temperature=0.7
)
```

**Follow Existing Patterns:**
- See `blueprints/header.py` for title generation examples
- See `blueprints/authoring_api_content.py` for section generation examples
- Use same error handling and retry logic

---

### 2.4 Content Generation Pipeline

**Step-by-Step Process:**

1. **Select Product/Category**
   - User selects product or category
   - Get source ID (product_id or category_id)

2. **Retrieve Context**
   - Query vector index for selected item's chunk
   - Query for related chunks (similar products, category info)
   - Combine into context

3. **Generate Headline**
   - Use product/category name + LLM
   - Template: "Generate an engaging headline for a blog post about: {product_name}"
   - Store in `post.title`

4. **Generate Standfirst**
   - Use headline + context
   - Template: "Generate a one-sentence standfirst for: {headline}"
   - Store in `post.summary`

5. **Generate Post Structure**
   - Use context + template
   - Generate outline with section headings
   - Determine section types (intro, body, conclusion, etc.)

6. **Generate Sections**
   - For each section in outline:
     - Retrieve relevant chunks if needed
     - Generate section content using template
     - Create `post_section` record
     - Store in `post_section.polished` or `post_section.draft`

7. **Pull Product Images**
   - If product selected: get `image_url` from `clan_products`
   - Create `post_images` record linked to header section
   - Store as header image

8. **Create Post Record**
   - Insert into `post` table:
     - `title` - Generated headline
     - `summary` - Generated standfirst
     - `status` - 'draft'
     - `slug` - Generated from title
   - Insert into `post_development`:
     - `idea_seed` - "Generated from product/category: {name}"
     - `expanded_idea` - Generated outline

**API Endpoint:**
```python
POST /api/content/generate
{
  "source_type": "product",  // or "category"
  "source_id": 123,
  "generation_type": "deep_dive",  // or "comparison", "feature"
  "tone": "warm",  // optional
  "length": "medium"  // optional: short, medium, long
}

Response:
{
  "success": true,
  "post_id": 456,
  "title": "Generated headline",
  "sections": [
    {"section_id": 1, "heading": "Section 1", "content": "..."}
  ]
}
```

---

### 2.5 Integration with Blog Post Workflow

**Follow Existing Patterns:**
- Post creation: See `blueprints/automation_core.py` `create_post()` function
- Post development: See `blueprints/planning_api_post_specific.py` patterns
- Section creation: See `blueprints/authoring_api_sections.py` patterns

**Post Creation:**
```python
# Create post record
cursor.execute("""
    INSERT INTO post (title, slug, summary, status, created_at, updated_at)
    VALUES (%s, %s, %s, 'draft', NOW(), NOW())
    RETURNING id
""", (title, slug, standfirst))

post_id = cursor.fetchone()['id']

# Create post_development record
cursor.execute("""
    INSERT INTO post_development (post_id, idea_seed, expanded_idea)
    VALUES (%s, %s, %s)
""", (post_id, idea_seed, expanded_idea))
```

**Section Creation:**
```python
# For each generated section
cursor.execute("""
    INSERT INTO post_section (post_id, section_type, section_heading, polished, section_order)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
""", (post_id, section_type, heading, content, order))
```

**Image Integration:**
```python
# Get product image
product = get_product(product_id)
if product and product.get('image_url'):
    cursor.execute("""
        INSERT INTO post_images (post_id, section_id, image_url, is_header_image)
        VALUES (%s, %s, %s, true)
    """, (post_id, header_section_id, product['image_url']))
```

---

## Phase 3: User Interface

### Overview
Add UI for content generation integrated into existing calendar/blog workflow.

---

### 3.1 Calendar Integration

**Add "Content Generator" Row:**
- Location: `templates/planning/calendar/week_view.html`
- Pattern: Follow Profiles row pattern exactly

**HTML Structure:**
```html
<div class="row-section" data-filter="content-generator">
    <div class="row-header">
        <span>Content Generator</span>
        <button class="row-add-btn" onclick="getContentGeneratorModal().openNew()">
            <i class="fas fa-plus"></i> Generate Post
        </button>
    </div>
    <div class="row-grid" id="content-generator-row"></div>
</div>
```

**Filter Pill:**
```html
<label class="filter-pill filter-content-generator active">
    <input type="checkbox" id="toggle-content-generator" checked> Content Generator
</label>
```

**JavaScript Integration:**
- File: `static/js/planning/calendar-week-view.js`
- Add to `loadWeek()` function:
  ```javascript
  const contentGenPromise = fetchJSON(`/planning/api/calendar/content-generator/${year}/${weekNumber}`);
  ```
- Add rendering in `renderItems()` function
- Add filter toggle

**Backend API:**
```python
GET /planning/api/calendar/content-generator/<year>/<week_number>
# Returns generated posts for that week
```

---

### 3.2 Generation Modal

**Template:** `templates/planning/calendar/content_generator_modal.html`

**Pattern:** Follow `profile_modal.html` structure

**Features:**
1. **Source Type Selector**
   - Radio buttons: "Product" / "Category"
   - Changes available options

2. **Product/Category Selector**
   - Product: Search input (reuse product search from profile modal)
   - Category: Dropdown (reuse category selector)
   - Preview: Show selected item details

3. **Generation Type**
   - Dropdown: "Deep Dive" / "Category Feature" / "Comparison"
   - Changes which template is used

4. **Generation Options**
   - Tone: "Warm" / "Professional" / "Casual"
   - Length: "Short" / "Medium" / "Long"
   - Focus areas: Checkboxes (optional)

5. **Action Buttons**
   - "Generate Post" - Starts generation
   - "Cancel" - Closes modal
   - Loading state during generation

**JavaScript:**
- File: `static/js/planning/content-generator-modal-core.js`
- Class: `ContentGeneratorModal`
- Methods:
  - `openNew(week, year)` - Open for new generation
  - `searchProducts(query)` - Search products
  - `selectProduct(productId)` - Select product
  - `selectCategory(categoryId)` - Select category
  - `generate()` - Call generation API
  - `preview()` - Preview before saving

**CSS:**
- File: `static/css/planning/content-generator-modal.css`
- Follow `profile-modal.css` styling

---

### 3.3 Idea Suggestion Panel

**Purpose:** Query vector index to suggest interesting products/categories

**API Endpoint:**
```python
POST /api/content/suggest-ideas
{
  "query": "interesting Scottish products",  // optional
  "limit": 10
}

Response:
{
  "suggestions": [
    {
      "type": "product",
      "id": 123,
      "name": "Lambswool Scarf",
      "reason": "Rich heritage and craftsmanship details",
      "score": 0.89
    }
  ]
}
```

**UI Component:**
- Panel in generation modal
- Shows suggested products/categories
- Click to select
- Updates preview

**Implementation:**
- Query vector index with broad queries
- Return top results with metadata
- Format as clickable suggestions

---

### 3.4 Generation Controls

**In Modal:**
- Tone selector (dropdown)
- Length selector (dropdown)
- Focus areas (checkboxes, optional)
- Advanced options (collapsible):
  - Temperature (LLM)
  - Max tokens
  - Custom prompt override

**Stored in:**
- Generation parameters stored in `post_development` JSONB field
- Or new `content_generation_metadata` JSONB in `post` table

---

### 3.5 Preview/Edit Before Saving

**Workflow:**
1. User clicks "Generate Post"
2. Modal shows loading state
3. Generation completes
4. Modal shows preview:
   - Headline
   - Standfirst
   - Section outline
   - Section previews (first 200 chars)
5. User can:
   - Edit headline/standfirst
   - Regenerate sections
   - Add/remove sections
   - Adjust tone/length
6. User clicks "Save Post"
7. Post created in database
8. Modal closes, post appears in calendar

**Preview API:**
```python
POST /api/content/preview
# Same as generate, but doesn't save to DB
# Returns preview data
```

**Edit API:**
```python
PUT /api/content/generate/<post_id>
# Regenerate specific sections
```

---

### 3.6 Product Image Integration

**Automatic:**
- When product selected, pull `image_url` from `clan_products`
- Set as header image automatically
- User can change in preview

**Manual:**
- User can select different product image
- User can upload custom image
- User can remove image

**Implementation:**
- Use existing `post_images` table
- Link to header section
- Follow existing image handling patterns

---

## API Endpoints Summary

### Phase 2 Endpoints

1. `POST /api/content/generate`
   - Generate blog post from product/category
   - Returns post_id and generated content

2. `POST /api/content/preview`
   - Preview generation without saving
   - Returns preview data

3. `PUT /api/content/generate/<post_id>`
   - Regenerate sections of existing post

### Phase 3 Endpoints

4. `GET /planning/api/calendar/content-generator/<year>/<week>`
   - Get generated posts for calendar week

5. `POST /api/content/suggest-ideas`
   - Get suggested products/categories for generation

---

## File Structure

```
blueprints/
├── content_generation_api.py      # Generation endpoints
└── planning_api_calendar_content_generator.py  # Calendar integration

templates/
└── planning/calendar/
    └── content_generator_modal.html

static/
├── js/planning/
│   └── content-generator-modal-core.js
└── css/planning/
    └── content-generator-modal.css

migrations/
└── (none needed - uses existing post/post_section tables)
```

---

## Integration Checklist

### Phase 2
- [ ] Create prompt templates in `llm_prompt` table
- [ ] Build generation pipeline function
- [ ] Create generation API endpoint
- [ ] Test with sample products/categories
- [ ] Verify post creation works
- [ ] Verify section creation works
- [ ] Verify image integration works

### Phase 3
- [ ] Add Content Generator row to calendar
- [ ] Create generation modal template
- [ ] Create modal JavaScript class
- [ ] Create modal CSS
- [ ] Add calendar API endpoint
- [ ] Add idea suggestion API
- [ ] Test full workflow
- [ ] Verify preview/edit works
- [ ] Verify post appears in calendar

---

## Testing Strategy

1. **Unit Tests:**
   - Generation pipeline functions
   - Prompt template rendering
   - Post/section creation

2. **Integration Tests:**
   - Full generation workflow
   - Calendar integration
   - Modal interactions

3. **User Testing:**
   - Generate posts from various products
   - Generate posts from categories
   - Edit generated content
   - Verify quality of generated content

---

**Status:** Ready to implement after Phase 1  
**Dependencies:** Phase 1 vector search must be working  
**Estimated Time:** 3-4 days for Phases 2-3 combined

