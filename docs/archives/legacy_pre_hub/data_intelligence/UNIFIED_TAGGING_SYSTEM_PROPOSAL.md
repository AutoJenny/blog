# Unified Tagging System Proposal
**Date:** 2025-11-12  
**Status:** Discussion  
**Goal:** Replace explicit cross-linking with unified tag-based system using vector relevance scoring

---

## Core Concept

Instead of maintaining explicit links between products, KB articles, and blog posts, use a **unified tagging system** where:

1. **All content types** (products, KB articles, blog posts) share the same tag vocabulary
2. **Tags are constrained** to a finite, managed list (materials, patterns, decorations, product types, etc.)
3. **Content is automatically scored** using vector search for relevance to each tag
4. **High-relevance items** are displayed as cross-linking tags
5. **Tags act as navigation** - clicking a tag shows all relevant content

---

## Why This Approach?

### Problems with Explicit Linking
- **Maintenance burden**: Need to create and maintain links manually or with complex rules
- **Rigidity**: Links are binary (linked or not), no partial relevance
- **Scalability**: Junction tables grow large, complex queries
- **Discovery**: Hard to find "everything about pewter" across all content types
- **Emergence**: New topics require manual link creation

### Benefits of Unified Tagging
- **Single system**: One tagging mechanism for all content
- **Automatic discovery**: Vector search finds relevance automatically
- **Flexible relevance**: Scores show strength of relationship (0.0-1.0)
- **Simple queries**: "Show all content with tag 'pewter'" works across all types
- **Emergent tags**: New topics can be added to vocabulary and automatically scored
- **Leverages existing infrastructure**: Uses vector search already built

---

## System Design

### 1. Tag Vocabulary (Constrained List)

**Tag Categories:**
- **Materials**: pewter, silver, wool, tartan, leather, cashmere, etc.
- **Patterns**: tartan patterns, checks, plaids, etc.
- **Decorations**: clan crests, thistles, Celtic knots, etc.
- **Product Types**: kilt, shirt, sporran, quaich, etc.
- **Styles**: traditional, modern, luxury, essential, etc.
- **Occasions**: formal, casual, wedding, etc.
- **Regions**: Scottish, Highland, etc.
- **Techniques**: handcrafted, machine-made, etc.

**Tag Management:**
- Centralized tag vocabulary table
- Tags can be added/removed/merged
- Tags have categories for organization
- Tags can have synonyms/aliases

### 2. Content-Tag Relevance Scoring

**For each piece of content (product/KB/blog):**
- Score relevance to each tag in vocabulary using vector search
- Store scores in `content_tag_relevance` table
- Only store scores above threshold (e.g., >0.6)
- Re-score when content is updated

**Scoring Process:**
1. For each tag, generate query: "What is [tag]?" or use tag name directly
2. Vector search content against tag query
3. Store similarity score as relevance
4. Display tags where relevance > threshold

### 3. Database Structure

```sql
-- Tag Vocabulary
CREATE TABLE content_tags (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL UNIQUE,
    tag_category VARCHAR(50),  -- 'material', 'pattern', 'decoration', etc.
    description TEXT,
    synonyms TEXT[],  -- Array of alternative names
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content-Tag Relevance Scores
CREATE TABLE content_tag_relevance (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('product', 'kb_article', 'blog_post')),
    content_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL REFERENCES content_tags(id) ON DELETE CASCADE,
    relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0 AND relevance_score <= 1),
    scoring_method VARCHAR(20) DEFAULT 'vector',  -- 'vector', 'exact_match', 'manual'
    last_scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_type, content_id, tag_id)
);

CREATE INDEX idx_content_tag_relevance_content ON content_tag_relevance(content_type, content_id);
CREATE INDEX idx_content_tag_relevance_tag ON content_tag_relevance(tag_id, relevance_score);
CREATE INDEX idx_content_tag_relevance_score ON content_tag_relevance(relevance_score DESC);
```

### 4. Tag Display Logic

**Thresholds:**
- **Primary tags**: relevance > 0.75 (strong relationship)
- **Secondary tags**: relevance > 0.60 (moderate relationship)
- **Hidden**: relevance < 0.60 (not displayed)

**Display Priority:**
1. Primary tags first (highest relevance)
2. Secondary tags second
3. Within each group, sort by relevance score

---

## Example: Pewter Implementation

### Step 1: Create Tag
```sql
INSERT INTO content_tags (tag_name, tag_category, description)
VALUES ('pewter', 'material', 'A malleable metal alloy traditionally used in Scottish wares');
```

### Step 2: Score All Content
For each product/KB article/blog post:
- Vector search query: "pewter"
- Store score in `content_tag_relevance`

**Results:**
- 71 products: scores 0.85-0.95 (exact material match)
- "Historical Scottish pewter wares" (KB): score 0.92
- "What is pewter?" (KB): score 0.88
- "How do I care for pewter objects?" (KB): score 0.81
- Various blog posts: scores 0.65-0.78 (if any exist)

### Step 3: Display Tags
**On Product Page:**
- Shows "pewter" tag (relevance 0.90)
- Clicking tag → shows all content with pewter tag
- Shows related tags (e.g., "metal", "alloy", "antique")

**On KB Article Page:**
- Shows "pewter" tag (relevance 0.92)
- Shows related products (71 products with pewter tag)
- Shows related blog posts (if any)

**On Blog Post Page:**
- Shows "pewter" tag (if relevant)
- Shows related products and KB articles

---

## Advantages

### 1. Simplicity
- **One system** instead of multiple junction tables
- **Automatic scoring** - no manual link creation
- **Consistent interface** across all content types

### 2. Flexibility
- **Partial relevance** - scores show strength, not just binary
- **Easy to add new tags** - just add to vocabulary and re-score
- **Emergent relationships** - vector search finds unexpected connections

### 3. Scalability
- **Efficient queries** - index on tag_id and relevance_score
- **Batch scoring** - can process all content in background
- **Incremental updates** - only re-score changed content

### 4. User Experience
- **Tag navigation** - click any tag to see all related content
- **Related content discovery** - "You might also like" based on shared tags
- **Tag clouds** - visualize popular topics

### 5. Leverages Existing Infrastructure
- **Vector search** already built and working
- **FAISS index** can be used for tag scoring
- **No new complex systems** needed

---

## Challenges & Solutions

### Challenge 1: Tag Vocabulary Management
**Problem**: Need to maintain finite, controlled list of tags

**Solution**:
- Start with existing product_type_data values (materials, patterns, etc.)
- Use LLM to extract and normalize tags from content
- Manual review/approval process for new tags
- Tag merging/aliasing for synonyms

### Challenge 2: Scoring Performance
**Problem**: Scoring all content against all tags could be slow

**Solution**:
- **Batch processing**: Score in background jobs
- **Incremental updates**: Only re-score when content changes
- **Caching**: Cache tag scores, invalidate on content update
- **Selective scoring**: Only score against relevant tag categories (e.g., materials only for products)

### Challenge 3: Relevance Threshold
**Problem**: What score threshold to use for display?

**Solution**:
- **Configurable thresholds**: Different thresholds for different content types
- **Adaptive thresholds**: Use percentile-based (top 10 tags per content)
- **Manual override**: Allow manual tag addition/removal

### Challenge 4: Tag Extraction
**Problem**: How to extract tags from content automatically?

**Solution**:
- **Existing data**: Use product_type_data (materials, patterns, etc.)
- **LLM extraction**: Use LLM to extract topics from KB articles and blog posts
- **Vector search**: Use semantic search to find relevant tags
- **Hybrid approach**: Combine exact matches with semantic discovery

### Challenge 5: Tag Quality
**Problem**: Ensuring tags are meaningful and not noise

**Solution**:
- **Minimum relevance threshold**: Only show tags above 0.6
- **Tag frequency**: Hide tags that appear on too many items (too generic)
- **Tag specificity**: Prefer specific tags over generic ones
- **Manual curation**: Review and approve tag assignments

---

## Comparison: Explicit Links vs. Unified Tags

| Aspect | Explicit Links | Unified Tags |
|--------|---------------|--------------|
| **Setup Complexity** | High (junction tables, linking rules) | Medium (tag vocabulary, scoring) |
| **Maintenance** | High (manual link management) | Low (automatic scoring) |
| **Flexibility** | Low (binary links) | High (relevance scores) |
| **Discovery** | Hard (need to query multiple tables) | Easy (single tag query) |
| **Scalability** | Medium (grows with links) | High (efficient indexing) |
| **Emergence** | Manual (create links) | Automatic (vector search) |
| **User Experience** | Good (explicit relationships) | Excellent (tag navigation) |

---

## Implementation Strategy

### Phase 1: Tag Vocabulary (Week 1)
1. Create `content_tags` table
2. Populate with existing materials, patterns, decorations from `product_type_data`
3. Add common topics (pewter, tartan, kilt, etc.)
4. Create tag management interface

### Phase 2: Scoring Infrastructure (Week 1-2)
1. Create `content_tag_relevance` table
2. Build scoring script:
   - For each tag, generate query
   - Vector search all content
   - Store scores above threshold
3. Test with pewter example

### Phase 3: Tag Extraction (Week 2)
1. Extract tags from products (use product_type_data)
2. Extract tags from KB articles (LLM + vector search)
3. Extract tags from blog posts (LLM + vector search)
4. Normalize and merge tags

### Phase 4: UI Integration (Week 3)
1. Add tag display to product browser
2. Add tag display to KB browser
3. Add tag display to blog posts
4. Create tag navigation pages ("Show all content tagged 'pewter'")

### Phase 5: Optimization (Week 4)
1. Performance tuning (indexing, caching)
2. Threshold optimization
3. Tag quality review
4. User testing

---

## Example Queries

### "Show all content about pewter"
```sql
SELECT 
    content_type,
    content_id,
    relevance_score
FROM content_tag_relevance
WHERE tag_id = (SELECT id FROM content_tags WHERE tag_name = 'pewter')
  AND relevance_score > 0.6
ORDER BY relevance_score DESC;
```

### "Show related content for a product"
```sql
-- Get product's tags
SELECT tag_id, relevance_score
FROM content_tag_relevance
WHERE content_type = 'product' AND content_id = 123
  AND relevance_score > 0.7
ORDER BY relevance_score DESC
LIMIT 10;

-- Find other content with same tags
SELECT content_type, content_id, COUNT(*) as shared_tags, AVG(relevance_score) as avg_relevance
FROM content_tag_relevance
WHERE tag_id IN (SELECT tag_id FROM ...)
  AND NOT (content_type = 'product' AND content_id = 123)
GROUP BY content_type, content_id
HAVING COUNT(*) >= 2
ORDER BY shared_tags DESC, avg_relevance DESC;
```

---

## Key Design Decisions

### 1. Tag Vocabulary Constraint
**Decision**: Maintain finite, curated list
**Rationale**: 
- Ensures consistency (no "pewter" vs "Pewter" vs "pewter metal")
- Enables tag merging/aliasing
- Prevents tag explosion
- Makes queries efficient

### 2. Relevance Scoring Method
**Decision**: Vector search for all tags
**Rationale**:
- Leverages existing infrastructure
- Finds semantic relationships, not just exact matches
- Handles synonyms and related concepts
- Consistent scoring across all content types

### 3. Threshold Strategy
**Decision**: Configurable thresholds (0.6 for display, 0.75 for primary)
**Rationale**:
- Balances relevance with coverage
- Allows fine-tuning per content type
- Can be adjusted based on user feedback

### 4. Tag Categories
**Decision**: Organize tags by category (material, pattern, etc.)
**Rationale**:
- Helps with tag management
- Enables category-specific queries
- Improves UI organization

---

## Potential Enhancements

### 1. Tag Hierarchies
- Parent-child relationships (e.g., "metal" → "pewter", "silver")
- Enables broader queries ("show all metal products")

### 2. Tag Synonyms
- "pewter" = "pewter metal" = "tin alloy"
- Automatic synonym expansion in queries

### 3. Tag Confidence
- Track how confident we are in tag assignment
- Use for display priority

### 4. Tag Analytics
- Track which tags are most popular
- Identify content gaps (tags with few items)
- Suggest new tags based on content

### 5. User-Generated Tags
- Allow users to suggest tags
- Community validation

---

## Risks & Mitigations

### Risk 1: Tag Vocabulary Becomes Too Large
**Mitigation**: 
- Regular tag review and merging
- Tag usage analytics (hide unused tags)
- Category-based organization

### Risk 2: Scoring Performance Degrades
**Mitigation**:
- Efficient indexing
- Batch processing in background
- Incremental updates only
- Cache frequently accessed tags

### Risk 3: Low-Quality Tags Appear
**Mitigation**:
- Minimum relevance threshold
- Manual review queue for new tags
- Tag quality metrics (specificity, frequency)

### Risk 4: Tag Extraction Misses Important Topics
**Mitigation**:
- Hybrid approach (exact match + semantic)
- Manual tag addition
- Regular review of untagged content

---

## Recommendation

**This unified tagging approach is superior to explicit linking because:**

1. **Simpler architecture**: One system instead of multiple junction tables
2. **Automatic discovery**: Vector search finds relationships automatically
3. **Better UX**: Tag navigation is intuitive and powerful
4. **Leverages existing work**: Uses vector search infrastructure already built
5. **More flexible**: Relevance scores allow nuanced relationships
6. **Easier maintenance**: Automatic scoring, less manual work

**The constrained vocabulary is key** - it ensures consistency while allowing automatic discovery through vector search.

**Start with existing data** (product_type_data materials/patterns) and expand iteratively.

---

## Next Steps

1. **Review and approve** this approach
2. **Design tag vocabulary** (start with materials, patterns, decorations)
3. **Create database schema** (content_tags, content_tag_relevance)
4. **Build scoring infrastructure**
5. **Test with pewter example**
6. **Expand to all content types**
7. **Add UI components**

---

**Last Updated:** 2025-11-12

