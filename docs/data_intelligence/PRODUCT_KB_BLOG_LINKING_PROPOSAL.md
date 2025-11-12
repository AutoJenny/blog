# Product-KB-Blog Linking System Proposal
**Date:** 2025-11-12  
**Status:** Proposal  
**Goal:** Connect product catalogue to Knowledge Base articles and blog posts

---

## Problem Statement

Currently:
- Products have materials, patterns, decorations, and other attributes (e.g., "Material: pewter")
- KB articles exist about these topics (e.g., 4 articles about pewter)
- **No linking mechanism** between products and KB articles
- **No primary/secondary designation** for KB articles
- **No blog post integration** for related content
- Products cannot surface relevant educational or contextual content

**Example:** Products with "Material: pewter" should link to:
- **Primary KB article**: Comprehensive overview of pewter (history, properties, care)
- **Secondary KB articles**: Deep-dive topics (e.g., "Pewter care", "Pewter history")
- **Blog posts**: Related articles (e.g., "Caring for your pewter collection")

---

## Current State Analysis

### Products with Pewter
- **71 products** have "pewter" in `product_type_data.materials` array
- **20+ products** have "pewter" in descriptions or additional_data
- Material is 4th most common material (after tartan, wool, polyester)
- Examples: Celtic Banded Pewter Quaich, various kilt pins, brooches, buckles

### KB Articles about Pewter
- **12 articles** found with "pewter" in name or content
- **4 core pewter articles** in "Pewter" category:
  1. **"What is pewter?"** (ID: 589) - 2,256 chars - Overview article
  2. **"Historical Scottish pewter wares"** (ID: 590) - 5,794 chars - Historical context
  3. **"How do I care for pewter objects?"** (ID: 592) - 2,423 chars - Care guide
  4. **"Is pewter safe to use for food and drink items?"** (ID: 591) - 1,980 chars - Safety info
- **8 related articles** mention pewter (quaichs, kilt accessories, etc.)
- **None marked as primary**
- **None linked to products**

### Semantic Search Results
- Vector search successfully finds pewter-related content:
  - **14 products** with high similarity (0.71-0.72)
  - **4 KB articles** with high similarity (0.71-0.74)
  - **2 categories** (Quaichs, Cufflinks/Tie Pins)
- **"What is pewter?"** has highest semantic relevance (0.744-0.778 depending on query)
- **"Historical Scottish pewter wares"** has best content length (5,794 chars) and good relevance
- **"How do I care for pewter objects?"** has excellent relevance for care queries (0.809)

### Blog Posts
- `post` table exists with content fields
- Need to check for pewter-related posts
- Posts have `profile_product_id`, `profile_category_id` fields for direct product links

---

## Proposed Solution

### Phase 1: KB Article Classification

#### 1.1 Primary/Secondary Designation

**Add to `clan_kb_articles` table:**
```sql
ALTER TABLE clan_kb_articles 
ADD COLUMN is_primary BOOLEAN DEFAULT FALSE,
ADD COLUMN primary_topic VARCHAR(100),  -- e.g., 'pewter', 'tartan', 'kilt'
ADD COLUMN related_topics TEXT[];       -- Array of related topics
```

**Primary Article Criteria:**
- Comprehensive coverage of the topic
- Substantial content length (>3000-5000 chars)
- High quality (good rating, multiple votes)
- Broad scope (not too specialized)
- Suitable as "main" reference

**Secondary Articles:**
- Specialized topics
- Deep-dive content
- How-to guides
- Specific use cases

#### 1.2 Topic Extraction

**Use LLM to analyze KB articles and extract:**
- Primary topic (single main topic)
- Related topics (array of related concepts)
- Article type (overview, guide, history, care, etc.)

**Example:**
- Article: "What is Pewter?"
  - Primary topic: `pewter`
  - Related topics: `['metal', 'alloy', 'tin', 'antique', 'care']`
  - Type: `overview`

### Phase 2: Product-KB Linking

#### 2.1 Automatic Linking System

**Link products to KB articles based on:**
1. **Material matches**: `product_type_data.materials` → KB `primary_topic` or `related_topics`
2. **Pattern matches**: `product_type_data.patterns` → KB topics
3. **Core type matches**: `product_type_data.core_type` → KB topics
4. **Semantic similarity**: Vector search to find relevant KB articles

**Linking Rules:**
- **Primary link**: Product material/pattern matches KB `primary_topic`
- **Secondary links**: Product attribute matches KB `related_topics`
- **Semantic links**: High similarity score from vector search (>0.7)

#### 2.2 Database Structure

**Option A: Junction Table (Recommended)**
```sql
CREATE TABLE product_kb_links (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES clan_products(id) ON DELETE CASCADE,
    kb_article_id INTEGER NOT NULL REFERENCES clan_kb_articles(id) ON DELETE CASCADE,
    link_type VARCHAR(20) NOT NULL CHECK (link_type IN ('primary', 'secondary', 'semantic')),
    link_reason TEXT,  -- e.g., "Material: pewter", "Pattern: tartan"
    confidence_score FLOAT,  -- For semantic links
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, kb_article_id)
);

CREATE INDEX idx_product_kb_links_product ON product_kb_links(product_id);
CREATE INDEX idx_product_kb_links_kb ON product_kb_links(kb_article_id);
CREATE INDEX idx_product_kb_links_type ON product_kb_links(link_type);
```

**Option B: JSONB Column in Products**
```sql
ALTER TABLE clan_products
ADD COLUMN kb_links JSONB DEFAULT '{}';

-- Structure:
-- {
--   "primary": [123, 456],  -- Primary KB article IDs
--   "secondary": [789, 101],  -- Secondary KB article IDs
--   "by_topic": {
--     "pewter": {"primary": 123, "secondary": [789]},
--     "tartan": {"primary": 456, "secondary": [101]}
--   }
-- }
```

**Recommendation:** Option A (Junction Table) - more flexible, easier to query, supports metadata

### Phase 3: Blog Post Integration

#### 3.1 Blog Post Topic Extraction

**Extract topics from blog posts:**
- Use vector search to identify relevant topics
- Extract materials, patterns, product types mentioned
- Store in `post` table or separate `post_topics` table

#### 3.2 Product-Blog Linking

**Link products to blog posts based on:**
1. **Direct mentions**: Product name/SKU in post content
2. **Topic matches**: Post topics match product attributes
3. **Semantic similarity**: Vector search similarity

**Database Structure:**
```sql
CREATE TABLE product_blog_links (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES clan_products(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    link_type VARCHAR(20) NOT NULL CHECK (link_type IN ('direct', 'topic', 'semantic')),
    link_reason TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, post_id)
);
```

### Phase 4: UI Integration

#### 4.1 Product Browser Display

**Add to product data display:**
- **"Related Knowledge"** section showing:
  - Primary KB article (prominent, at top)
  - Secondary KB articles (smaller, below)
  - Related blog posts (if any)

**Example Layout:**
```
Related Knowledge
├─ Primary Article: "What is Pewter?" [Read More]
├─ Secondary Articles:
│  ├─ "Caring for Pewter Items"
│  └─ "History of Pewter in Scotland"
└─ Blog Posts:
   └─ "Maintaining Your Pewter Collection"
```

#### 4.2 KB Article Display

**Add to KB browser:**
- **"Related Products"** section showing products that link to this article
- Filter by link type (primary vs secondary)

#### 4.3 Blog Post Display

**Add to blog posts:**
- **"Featured Products"** section showing related products
- Auto-suggest products when writing posts

---

## Implementation Plan

### Step 1: KB Article Classification (Week 1)
1. Add `is_primary`, `primary_topic`, `related_topics` columns
2. Create LLM-based classification script
3. Classify all KB articles
4. Manual review of primary designations

### Step 2: Topic Extraction (Week 1-2)
1. Extract topics from all KB articles
2. Build topic taxonomy
3. Create topic → KB article mapping

### Step 3: Product-KB Linking (Week 2)
1. Create `product_kb_links` table
2. Build automatic linking script:
   - Material/pattern matching
   - Semantic search for additional links
3. Run linking for all products
4. Review and refine linking rules

### Step 4: Blog Post Integration (Week 3)
1. Analyze blog post structure
2. Extract topics from posts
3. Create `product_blog_links` table
4. Build linking script
5. Link existing posts

### Step 5: UI Integration (Week 3-4)
1. Add "Related Knowledge" to product browser
2. Add "Related Products" to KB browser
3. Add "Featured Products" to blog posts
4. Create admin interface for manual link management

---

## Technical Considerations

### Semantic Search Integration
- Use existing vector search infrastructure
- Set similarity threshold (e.g., >0.7 for automatic links)
- Allow manual override for edge cases

### Performance
- Index all linking tables
- Cache popular links
- Lazy-load related content in UI

### Maintenance
- Periodic re-linking when products/KB articles updated
- Confidence scoring for automatic links
- Manual review queue for low-confidence links

### Scalability
- Batch processing for initial linking
- Incremental updates for new products/articles
- Background jobs for semantic search

---

## Example: Pewter Implementation

### Current State
- **Products**: 71 products with "pewter" material
- **KB Articles**: 4 core pewter articles + 8 related articles
- **Links**: None
- **Primary Article**: None designated

### Recommended Classification

**Primary Article:**
- **"Historical Scottish pewter wares"** (ID: 590)
  - **Rationale**: Longest content (5,794 chars), comprehensive historical coverage
  - **Alternative**: "What is pewter?" (ID: 589) - Good overview, but shorter
  - **Decision**: Use "Historical Scottish pewter wares" as primary (more comprehensive)

**Secondary Articles:**
- **"What is pewter?"** (ID: 589) - Overview/introduction
- **"How do I care for pewter objects?"** (ID: 592) - Care guide
- **"Is pewter safe to use for food and drink items?"** (ID: 591) - Safety information

**Related Articles** (mention pewter but not primarily about it):
- "About the Quaich" (ID: 230) - Mentions pewter quaichs
- "Kilt Pins" (ID: 233) - Some pewter kilt pins
- Other kilt accessory articles

### After Implementation

**Step 1: Classify KB Articles**
- "Historical Scottish pewter wares" → **Primary** (`is_primary = TRUE`, `primary_topic = 'pewter'`)
- "What is pewter?" → Secondary (`primary_topic = 'pewter'`, `related_topics = ['overview', 'introduction']`)
- "How do I care for pewter objects?" → Secondary (`primary_topic = 'pewter'`, `related_topics = ['care', 'maintenance']`)
- "Is pewter safe to use for food and drink items?" → Secondary (`primary_topic = 'pewter'`, `related_topics = ['safety', 'food']`)

**Step 2: Link Products**
- **All 71 products** with `materials: ['pewter']` → Primary link to "Historical Scottish pewter wares" (ID: 590)
- **All 71 products** → Secondary link to "What is pewter?" (ID: 589) - Overview
- **All 71 products** → Secondary link to "How do I care for pewter objects?" (ID: 592) - Care
- **Food/drink products** (quaichs, cups) → Secondary link to "Is pewter safe to use for food and drink items?" (ID: 591)
- **Quaich products** → Additional link to "About the Quaich" (ID: 230)

**Step 3: Display in UI**
- Product browser shows "Historical Scottish pewter wares" prominently as primary
- Secondary articles in expandable "Learn More" section:
  - "What is pewter?" (overview)
  - "How do I care for pewter objects?" (care)
  - "Is pewter safe to use for food and drink items?" (safety, if applicable)
- Blog posts (if any) at bottom

### Expected Impact
- **71 products** will have immediate KB links
- Users can learn about pewter directly from product pages
- Care instructions easily accessible
- Historical context provided automatically

---

## Key Findings from Analysis

### Pewter-Specific Findings
- **71 products** use pewter material (4th most common material)
- **4 core pewter KB articles** exist but none are primary
- **"Historical Scottish pewter wares"** (5,794 chars) is best candidate for primary
- **Semantic search works well** - finds relevant articles with 0.71-0.81 similarity scores
- **No blog posts** currently about pewter (opportunity for content creation)

### Material Distribution
Top materials by product count:
- Tartan: 274 products
- Wool: 97 products  
- Polyester: 83 products
- **Pewter: 71 products** ← Good test case
- Leather: 57 products
- Cashmere: 47 products

### KB Article Quality
- Articles in "Pewter" category are well-organized
- Content lengths vary (1,980 - 5,794 chars)
- Semantic search identifies relevant articles accurately
- No current linking mechanism

## Questions to Resolve

1. **Primary Article Selection**: Should there be only ONE primary article per topic, or multiple?
   - **Recommendation**: One primary per topic, but allow multiple if articles cover different aspects
   - **Pewter Example**: "Historical Scottish pewter wares" as primary (comprehensive), others as secondary

2. **Link Confidence Threshold**: What similarity score threshold for automatic semantic links?
   - **Recommendation**: 0.7 for automatic, 0.6-0.7 for review queue
   - **Pewter Example**: All 4 core articles score 0.71-0.81, so all would auto-link

3. **Manual Override**: Should users be able to manually add/remove links?
   - **Recommendation**: Yes, with admin interface

4. **Link Display Priority**: How to order multiple links?
   - **Recommendation**: Primary first, then by confidence score, then alphabetical
   - **Pewter Example**: Primary → "What is pewter?" → "How do I care?" → "Is pewter safe?"

5. **Topic Taxonomy**: Should we create a formal topic taxonomy or use free-form topics?
   - **Recommendation**: Start free-form, build taxonomy iteratively
   - **Pewter Example**: Use "pewter" as primary_topic, extract related topics from content

---

## Next Steps

1. **Review and approve** this proposal
2. **Create database migrations** for new tables/columns
3. **Build classification script** for KB articles
4. **Implement linking logic** (matching + semantic)
5. **Test with pewter example**
6. **Expand to all materials/patterns**
7. **Add UI components**

---

**Last Updated:** 2025-11-12

