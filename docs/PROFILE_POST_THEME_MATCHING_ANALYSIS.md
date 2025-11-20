# Profile Post Theme Matching - Analysis & Recommendations

**Date:** 2025-01-XX  
**Purpose:** Analyze the process for creating profile posts (product/category/supplier) that are semantically matched to weekly theme posts

---

## Executive Summary

Profile posts should be intelligently matched to weekly theme posts using **semantic similarity** (vector embeddings). The system should:

1. **Extract theme content** from the selected theme post for the week
2. **Generate embeddings** for the theme content
3. **Search vector index** to find most relevant products, categories, and suppliers
4. **Intelligently select** the best match type (product vs category vs supplier) based on relevance scores
5. **Create profile post** linked to the selected entity

**Key Finding:** The infrastructure for this already exists (vector search, embeddings, content chunks), but needs extension to:
- Generate embeddings for theme posts
- Add supplier/producer embeddings to the vector index
- Implement intelligent selection logic

---

## Current State Analysis

### ✅ Existing Infrastructure

#### 1. Vector Search System (COMPLETE)
- **Location:** `utils/vector_search/`
- **Components:**
  - `ContentRetriever` - Semantic search using FAISS index
  - `EmbeddingGenerator` - Uses `intfloat/e5-large-v2` model (1024 dimensions)
  - `FAISSIndexManager` - HNSW index for fast similarity search
  - `ContentChunker` - Extracts and normalizes text from products/categories

#### 2. Content Chunks (COMPLETE)
- **Table:** `content_chunks`
- **Current Coverage:**
  - ✅ Products: 1,157 chunks (includes name, description, supplier, specs, additional_data, dimensions, options)
  - ✅ Categories: 259 chunks (includes name, description, heritage_data)
  - ❌ Suppliers/Producers: **NOT YET CHUNKED**

#### 3. Theme Post Data Structure (COMPLETE)
- **Table:** `post_development`
- **Key Fields for Matching:**
  - `expanded_idea` (TEXT) - Rich thematic content
  - `idea_seed` (TEXT) - Core concept
  - `basic_idea` (TEXT) - Initial idea
  - `summary` (TEXT) - Post summary
  - `intro_blurb` (TEXT) - Introduction
  - `topics_to_cover` (TEXT) - Topics list

#### 4. Week-Theme Relationship (COMPLETE)
- **Table:** `calendar_week_selection`
- **Structure:**
  - `year` + `week_number` → `selected_theme_id`
  - Links to `calendar_themes` table
  - Theme posts linked via `calendar_week_posts`

#### 5. Profile Post Structure (COMPLETE)
- **Table:** `post` with profile fields:
  - `profile_type` ('product', 'category', or NULL)
  - `profile_product_id` → `clan_products(id)`
  - `profile_category_id` → `clan_categories(id)`
  - `profile_producer_id` → `producers(id)`
- **Note:** Currently no `profile_type = 'supplier'` - would need to add this

#### 6. Producer/Supplier Data (PARTIAL)
- **Table:** `producers`
- **Fields:**
  - `name`, `description`, `location`, `founding_year`
  - `heritage_details`, `craftsmanship_methods`
  - `website_url`, `web_researched_at`
- **Status:** Table exists, but:
  - ❌ Not yet chunked for vector search
  - ❌ No embeddings generated
  - ❌ Not in FAISS index

---

## Gap Analysis

### Missing Components

#### 1. Theme Post Embeddings
**Status:** ❌ NOT IMPLEMENTED

**What's Needed:**
- Extract theme content from `post_development` for a given week's theme post
- Combine relevant fields (`expanded_idea`, `idea_seed`, `summary`, etc.)
- Generate embedding using same model (`e5-large-v2`)
- Use embedding to search vector index

**Implementation:**
```python
def extract_theme_content(post_id):
    """Extract and combine theme post content for embedding"""
    # Fetch post_development data
    # Combine: expanded_idea + idea_seed + summary + intro_blurb
    # Clean and normalize text
    # Return combined text
```

#### 2. Supplier/Producer Embeddings
**Status:** ❌ NOT IMPLEMENTED

**What's Needed:**
- Extend `ContentChunker` to handle `producers` table
- Create chunks for each producer with:
  - Name, description, location
  - Heritage details, craftsmanship methods
  - Founding year, website info
- Generate embeddings and add to FAISS index
- Store in `content_chunks` with `chunk_type = 'producer'`

**Implementation:**
```python
def chunk_producer(producer: Dict) -> Dict:
    """Create chunk from producer record"""
    # Combine: name + description + location + heritage_details + 
    #          craftsmanship_methods + founding_year
    # Return chunk_text and metadata
```

#### 3. Intelligent Selection Logic
**Status:** ❌ NOT IMPLEMENTED

**What's Needed:**
- Search vector index for products, categories, AND producers
- Get similarity scores for each type
- Implement selection algorithm:
  - Compare top product vs top category vs top producer
  - Consider score thresholds
  - Apply business rules (e.g., prefer products if score > 0.85, categories if 0.75-0.85, etc.)
- Return selected entity with type and score

**Implementation:**
```python
def find_best_profile_match(theme_post_id, year, week_number):
    """Find best matching product/category/supplier for theme"""
    # 1. Extract theme content
    theme_text = extract_theme_content(theme_post_id)
    
    # 2. Generate theme embedding
    theme_embedding = embedding_generator.generate_embedding(theme_text)
    
    # 3. Search each type
    products = retriever.search(theme_text, chunk_types=['product'], limit=5)
    categories = retriever.search(theme_text, chunk_types=['category'], limit=5)
    producers = retriever.search(theme_text, chunk_types=['producer'], limit=5)
    
    # 4. Select best match
    best_match = select_best_match(products, categories, producers)
    
    return best_match
```

#### 4. Profile Type Extension
**Status:** ⚠️ PARTIAL

**Current:** `profile_type` only supports 'product' or 'category'

**What's Needed:**
- Add 'supplier' or 'producer' as valid `profile_type`
- Update database constraint: `CHECK (profile_type IN ('product', 'category', 'supplier'))`
- Add `profile_supplier_id` field (or reuse `profile_producer_id`)

---

## Recommended Architecture

### Phase 1: Extend Vector Search to Include Producers

**Tasks:**
1. **Extend `ContentChunker`:**
   - Add `chunk_producer()` method
   - Combine producer fields into searchable text
   - Store metadata (name, location, founding_year)

2. **Generate Producer Embeddings:**
   - Run embedding generation script for all producers
   - Add to `content_chunks` table with `chunk_type = 'producer'`
   - Rebuild FAISS index to include producers

3. **Update `ContentRetriever`:**
   - Ensure it can search `chunk_type = 'producer'`
   - No code changes needed (already supports multiple chunk types)

**Estimated Time:** 2-3 hours

---

### Phase 2: Theme Post Embedding & Matching

**Tasks:**
1. **Create Theme Content Extractor:**
   - Function to extract theme content from `post_development`
   - Combine: `expanded_idea` + `idea_seed` + `summary` + `intro_blurb`
   - Handle missing fields gracefully
   - Clean and normalize text

2. **Create Matching Service:**
   - `find_profile_match_for_theme(theme_post_id, year, week_number)`
   - Generate theme embedding
   - Search products, categories, producers
   - Return top matches with scores

3. **Selection Algorithm:**
   - Compare top result from each type
   - Apply score thresholds:
     - **Product:** Score > 0.85 → High confidence
     - **Category:** Score 0.75-0.85 → Medium confidence
     - **Producer:** Score > 0.80 → High confidence
   - If multiple types meet thresholds, prefer: Product > Category > Producer
   - Return: `{type: 'product'|'category'|'producer', id: int, score: float, metadata: dict}`

**Estimated Time:** 4-5 hours

---

### Phase 3: Profile Post Creation Integration

**Tasks:**
1. **Extend Profile API:**
   - Add endpoint: `POST /api/profiles/auto-match`
   - Accepts: `year`, `week_number`
   - Returns: Suggested profile match with confidence score
   - Allows user to confirm or override

2. **Update Profile Modal:**
   - Add "Auto-Match to Theme" button
   - Shows suggested match with score
   - User can accept or manually select

3. **Database Updates:**
   - Add 'supplier' to `profile_type` CHECK constraint
   - Ensure `profile_producer_id` can be used for supplier profiles

**Estimated Time:** 3-4 hours

---

## Technical Implementation Details

### Theme Content Extraction

**Strategy:**
```python
def extract_theme_content(post_id: int) -> str:
    """
    Extract theme content from post_development for embedding.
    
    Priority order:
    1. expanded_idea (most comprehensive)
    2. idea_seed (core concept)
    3. summary (condensed version)
    4. intro_blurb (introduction)
    5. basic_idea (fallback)
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT expanded_idea, idea_seed, summary, intro_blurb, basic_idea
            FROM post_development
            WHERE post_id = %s
        """, (post_id,))
        
        data = cursor.fetchone()
        if not data:
            return ""
        
        # Combine fields with priority
        parts = []
        if data['expanded_idea']:
            parts.append(data['expanded_idea'])
        if data['idea_seed']:
            parts.append(f"\n\nCore Concept: {data['idea_seed']}")
        if data['summary']:
            parts.append(f"\n\nSummary: {data['summary']}")
        if data['intro_blurb']:
            parts.append(f"\n\nIntroduction: {data['intro_blurb']}")
        if not parts and data['basic_idea']:
            parts.append(data['basic_idea'])
        
        return "\n".join(parts).strip()
```

### Producer Chunking

**Strategy:**
```python
def chunk_producer(self, producer: Dict) -> Dict:
    """
    Create chunk from producer record.
    
    Combines:
    - Name
    - Description
    - Location
    - Heritage details
    - Craftsmanship methods
    - Founding year (if available)
    """
    parts = []
    
    if producer.get('name'):
        parts.append(f"Producer: {producer['name']}")
    
    if producer.get('description'):
        parts.append("")
        parts.append(self.clean_html(producer['description']))
    
    if producer.get('location'):
        parts.append("")
        parts.append(f"Location: {producer['location']}")
    
    if producer.get('heritage_details'):
        parts.append("")
        parts.append("Heritage:")
        parts.append(self.clean_html(producer['heritage_details']))
    
    if producer.get('craftsmanship_methods'):
        parts.append("")
        parts.append("Craftsmanship Methods:")
        parts.append(self.clean_html(producer['craftsmanship_methods']))
    
    if producer.get('founding_year'):
        parts.append("")
        parts.append(f"Founded: {producer['founding_year']}")
    
    chunk_text = "\n".join(parts).strip()
    
    metadata = {
        'producer_name': producer.get('name'),
        'location': producer.get('location'),
        'founding_year': producer.get('founding_year')
    }
    
    return {
        'chunk_text': chunk_text,
        'metadata': metadata
    }
```

### Selection Algorithm

**Strategy:**
```python
def select_best_match(products: List[Dict], categories: List[Dict], 
                     producers: List[Dict]) -> Dict:
    """
    Select best matching entity type based on relevance scores.
    
    Rules:
    1. If product score > 0.85 → Product (high confidence)
    2. If category score > 0.80 → Category (high confidence)
    3. If producer score > 0.80 → Producer (high confidence)
    4. If multiple meet thresholds, prefer: Product > Category > Producer
    5. If none meet thresholds, return highest score regardless of type
    """
    best_product = products[0] if products else None
    best_category = categories[0] if categories else None
    best_producer = producers[0] if producers else None
    
    # Extract scores
    product_score = best_product['score'] if best_product else 0.0
    category_score = best_category['score'] if best_category else 0.0
    producer_score = best_producer['score'] if best_producer else 0.0
    
    # Apply selection rules
    if product_score > 0.85:
        return {
            'type': 'product',
            'id': best_product['source_id'],
            'score': product_score,
            'metadata': best_product['metadata']
        }
    
    if category_score > 0.80:
        return {
            'type': 'category',
            'id': best_category['source_id'],
            'score': category_score,
            'metadata': best_category['metadata']
        }
    
    if producer_score > 0.80:
        return {
            'type': 'producer',
            'id': best_producer['source_id'],
            'score': producer_score,
            'metadata': best_producer['metadata']
        }
    
    # Fallback: return highest score
    scores = [
        ('product', product_score, best_product),
        ('category', category_score, best_category),
        ('producer', producer_score, best_producer)
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    
    best_type, best_score, best_match = scores[0]
    if best_match:
        return {
            'type': best_type,
            'id': best_match['source_id'],
            'score': best_score,
            'metadata': best_match['metadata']
        }
    
    return None
```

---

## Database Schema Updates

### 1. Extend `content_chunks` Table

**No changes needed** - already supports `chunk_type` with CHECK constraint. Just need to ensure 'producer' is allowed:

```sql
-- Verify constraint allows 'producer'
ALTER TABLE content_chunks 
DROP CONSTRAINT IF EXISTS content_chunks_chunk_type_check;

ALTER TABLE content_chunks 
ADD CONSTRAINT content_chunks_chunk_type_check 
CHECK (chunk_type IN ('product', 'category', 'kb', 'producer'));
```

### 2. Extend `post.profile_type`

**Add 'supplier' or 'producer' as valid type:**

```sql
ALTER TABLE post 
DROP CONSTRAINT IF EXISTS post_profile_type_check;

ALTER TABLE post 
ADD CONSTRAINT post_profile_type_check 
CHECK (profile_type IN ('product', 'category', 'supplier'));
```

**Note:** Use 'supplier' for consistency with existing `clan_products.supplier_name`, or 'producer' to match `producers` table. Recommend 'supplier' for user-facing terminology.

---

## Workflow Integration

### User Flow

1. **User selects week** in calendar view
2. **System identifies theme post** for that week via `calendar_week_selection`
3. **User clicks "Create Profile Post"** → Opens profile modal
4. **User clicks "Auto-Match to Theme"** → System:
   - Extracts theme content
   - Searches vector index
   - Returns suggested match with confidence score
5. **User reviews suggestion:**
   - Accept → Creates profile post with suggested entity
   - Override → Manual selection (existing flow)
6. **Profile post created** with `profile_type` and appropriate `profile_*_id` set

### API Endpoint

```python
@bp.route('/api/profiles/auto-match', methods=['POST'])
def api_auto_match_profile():
    """
    Auto-match profile to theme post for a given week.
    
    Request:
    {
        "year": 2025,
        "week_number": 46
    }
    
    Response:
    {
        "success": true,
        "match": {
            "type": "product",
            "id": 12345,
            "score": 0.87,
            "name": "Lambswool Scarf",
            "producer": "Lochcarron",
            "metadata": {...}
        },
        "theme_post_id": 90,
        "theme_title": "Scottish Textiles"
    }
    """
```

---

## Recommendations Summary

### Immediate Actions

1. ✅ **Extend vector search to producers** (2-3 hours)
   - Add `chunk_producer()` to `ContentChunker`
   - Generate embeddings for all producers
   - Rebuild FAISS index

2. ✅ **Create theme content extractor** (1-2 hours)
   - Function to extract and combine theme post content
   - Handle missing fields gracefully

3. ✅ **Implement matching service** (3-4 hours)
   - Theme embedding generation
   - Multi-type search (products, categories, producers)
   - Selection algorithm with score thresholds

4. ✅ **Extend profile type** (30 minutes)
   - Add 'supplier' to `profile_type` constraint
   - Update API to handle supplier profiles

5. ✅ **Create auto-match API endpoint** (2-3 hours)
   - Endpoint for theme-based matching
   - Integration with profile modal

### Future Enhancements

1. **Score Threshold Tuning:**
   - Monitor match quality
   - Adjust thresholds based on user feedback
   - Consider different thresholds per entity type

2. **Diversity Logic:**
   - Avoid suggesting same product/category/producer multiple times
   - Track what's been profiled recently
   - Prefer entities not yet profiled

3. **Multi-Match Suggestions:**
   - Return top 3 matches instead of just best
   - Let user choose from suggestions
   - Show confidence scores for each

4. **Theme Embedding Caching:**
   - Cache theme embeddings (don't regenerate on every search)
   - Invalidate cache when theme post content changes

---

## Terminology Note

**"LLM encoding"** = **Vector Embeddings** or **Semantic Embeddings**

The process is:
1. **Embedding Generation:** Convert text to numerical vector (1024 dimensions)
2. **Vector Search:** Find similar vectors using cosine similarity or L2 distance
3. **Semantic Matching:** Match based on meaning, not just keywords

The system uses **E5-large-v2** model from HuggingFace, which generates embeddings optimized for semantic search.

---

## Files to Modify/Create

### New Files
- `utils/vector_search/theme_extractor.py` - Theme content extraction
- `utils/profile_matching/matcher.py` - Profile matching service
- `blueprints/planning_api_profile_matching.py` - API endpoints

### Modified Files
- `utils/vector_search/chunking.py` - Add `chunk_producer()` method
- `scripts/generate_embeddings.py` - Include producers in generation
- `blueprints/planning_api_profiles.py` - Add auto-match endpoint
- `static/js/planning/profile-modal-core.js` - Add auto-match button
- `migrations/` - Add migration for profile_type constraint

---

## Estimated Total Time

- **Phase 1 (Producers):** 2-3 hours
- **Phase 2 (Matching):** 4-5 hours
- **Phase 3 (Integration):** 3-4 hours
- **Testing & Refinement:** 2-3 hours

**Total:** 11-15 hours

---

## Questions for User

1. **Terminology:** Use 'supplier' or 'producer' for `profile_type`? (Recommend 'supplier' for consistency)

2. **Score Thresholds:** Are the suggested thresholds (0.85 for products, 0.80 for categories/producers) acceptable, or should they be configurable?

3. **Fallback Behavior:** If no match meets thresholds, should we:
   - Return highest score anyway (even if low)?
   - Return error and require manual selection?
   - Show top 3 matches for user to choose?

4. **Diversity:** Should we implement logic to avoid suggesting entities already profiled recently?

5. **UI Integration:** Should auto-match be:
   - A button in the profile modal?
   - Automatic suggestion when opening modal?
   - Both (auto-suggest with option to re-match)?

