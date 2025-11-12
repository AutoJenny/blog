# Knowledge Base Table Structure Proposal

**Date:** 2025-11-11  
**Status:** ✅ Approved - Ready for Implementation  
**Purpose:** Design database schema for storing CLAN Knowledge Base data locally

**All design decisions resolved** - See "Design Decisions - Resolved" section below.

---

## API Overview

### Endpoints Available

1. **`/getKnowledgebaseCategories`** - Returns all KB categories
2. **`/getKnowledgebaseArticles?category_id=<id>`** - Returns articles for a specific category

### API Response Structures

#### Knowledge Base Categories
```json
{
  "success": true,
  "data": [
    {
      "category_id": "22",
      "name": "Terms & conditions",
      "url_key": "terms-and-conditions",
      "meta_title": "",
      "meta_keywords": null,
      "meta_description": null,
      "is_active": "1",
      "sort_order": "0",
      "parent_id": "1",
      "path": "1/22",
      "level": "3",
      "position": "1",
      "children_count": "0"
    }
  ]
}
```

#### Knowledge Base Articles
```json
{
  "success": true,
  "data": [
    {
      "article_id": "246",
      "name": "How to measure: Trousers",
      "feature_image": null,
      "short_text": null,
      "text": "<p>HTML content...</p>",
      "url_key": "measuring-trousers",
      "meta_title": "",
      "meta_keywords": null,
      "meta_description": null,
      "is_active": "1",
      "user_id": "1",
      "votes_sum": null,
      "votes_num": "0",
      "created_at": "2017-11-01 14:01:15",
      "updated_at": "2023-03-14 11:16:40",
      "position": "35",
      "user_name": "Admin User",
      "rating": null
    }
  ]
}
```

---

## Proposed Table Structure

### `clan_kb_categories`

Stores Knowledge Base category hierarchy (similar to `clan_categories`).

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Category ID from clan.com API (`category_id`) |
| `name` | TEXT | NOT NULL | Category name |
| `url_key` | TEXT | | URL-friendly key for category |
| `meta_title` | TEXT | | SEO meta title |
| `meta_keywords` | TEXT | | SEO meta keywords (comma-separated or JSON) |
| `meta_description` | TEXT | | SEO meta description |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether category is active |
| `sort_order` | INTEGER | DEFAULT 0 | Sort order within parent |
| `parent_id` | INTEGER | | Parent category ID (NULL for root) |
| `path` | TEXT | | Full category path showing all parent IDs<br>Format: slash-separated (e.g., "1/58/188/72/194/196/215")<br>Shows complete ancestry from root to current category |
| `level` | INTEGER | DEFAULT 0 | Position in hierarchy (not tree depth)<br>Level 4 = Main category<br>Level 5 = Sub-category<br>Level 6+ = Sub-sub-category |
| `position` | INTEGER | DEFAULT 0 | Sort order within parent category |
| `children_count` | INTEGER | DEFAULT 0 | Number of child categories |
| `clan_created_at` | TIMESTAMP | | Creation date from clan.com (if available) |
| `clan_updated_at` | TIMESTAMP | | Last update date from clan.com |
| `first_seen_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When category was first discovered |
| `last_updated` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last time our record was modified |

#### Indexes
- Primary key on `id`
- Index on `parent_id` for hierarchy queries
- Index on `url_key` for URL lookups
- Index on `is_active` for filtering active categories
- Index on `path` for path-based queries

#### Notes
- Similar structure to `clan_categories` for consistency
- `path` field allows efficient hierarchy queries
- `children_count` cached for performance (updated when children change)

---

### `clan_kb_articles`

Stores Knowledge Base articles (similar to `clan_products`).

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Article ID from clan.com API (`article_id`) |
| `category_id` | INTEGER | REFERENCES clan_kb_categories(id) | Category this article belongs to |
| `name` | TEXT | NOT NULL | Article title/name |
| `url_key` | TEXT | | URL-friendly key for article |
| `feature_image` | TEXT | | URL to feature image (if any) |
| `short_text` | TEXT | | Short summary/excerpt (if available) |
| `text` | TEXT | | Full article content (HTML) |
| `meta_title` | TEXT | | SEO meta title |
| `meta_keywords` | TEXT | | SEO meta keywords |
| `meta_description` | TEXT | | SEO meta description |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether article is active |
| `user_id` | INTEGER | | Author user ID from clan.com |
| `user_name` | TEXT | | Author name (cached for display) |
| `votes_sum` | DECIMAL(10,2) | | Sum of all votes |
| `votes_num` | INTEGER | DEFAULT 0 | Number of votes |
| `rating` | DECIMAL(3,2) | | Calculated rating (votes_sum / votes_num) |
| `position` | INTEGER | DEFAULT 0 | Sort order within category |
| `clan_created_at` | TIMESTAMP | | Creation date from clan.com |
| `clan_updated_at` | TIMESTAMP | | Last update date from clan.com |
| `first_seen_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When article was first discovered |
| `last_updated` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last time our record was modified |
| `article_content_hash` | TEXT | | SHA-256 hash of content fields (for change detection) |
| `last_content_change_at` | TIMESTAMP | | When article content actually changed (detected via hash comparison) |
| `feature_image_local` | TEXT | | Local path to cached feature image (if downloaded) |

#### Indexes
- Primary key on `id`
- Index on `category_id` for category-based queries
- Index on `url_key` for URL lookups
- Index on `is_active` for filtering active articles
- Index on `clan_updated_at` for finding recently updated articles
- Index on `position` for sorting within categories
- GIN index on `text` for full-text search (if using PostgreSQL full-text search)

#### Notes
- `article_content_hash` computed from: `name`, `url_key`, `text`, `short_text`, `feature_image` (for change detection)
- `last_content_change_at` set when hash changes (indicates actual content modification)
- `feature_image_local` stores local path after downloading from `feature_image` URL
- `rating` can be calculated on-the-fly or cached (stored for convenience: `votes_sum / votes_num`)
- `user_name` cached to avoid needing user lookup table
- Similar structure to `clan_products` for consistency
- HTML content stored as-is; cleaned during chunking for vector search (same as products/categories)

---

## Database Schema SQL

```sql
-- Knowledge Base Categories Table
CREATE TABLE IF NOT EXISTS clan_kb_categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    url_key TEXT,
    meta_title TEXT,
    meta_keywords TEXT,
    meta_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    parent_id INTEGER REFERENCES clan_kb_categories(id) ON DELETE SET NULL,
    path TEXT,
    level INTEGER DEFAULT 0,
    position INTEGER DEFAULT 0,
    children_count INTEGER DEFAULT 0,
    clan_created_at TIMESTAMP,
    clan_updated_at TIMESTAMP,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for clan_kb_categories
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_parent_id ON clan_kb_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_url_key ON clan_kb_categories(url_key);
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_is_active ON clan_kb_categories(is_active);
CREATE INDEX IF NOT EXISTS idx_clan_kb_categories_path ON clan_kb_categories(path);

-- Knowledge Base Articles Table
CREATE TABLE IF NOT EXISTS clan_kb_articles (
    id INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES clan_kb_categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    url_key TEXT,
    feature_image TEXT,
    short_text TEXT,
    text TEXT,
    meta_title TEXT,
    meta_keywords TEXT,
    meta_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    user_id INTEGER,
    user_name TEXT,
    votes_sum DECIMAL(10,2),
    votes_num INTEGER DEFAULT 0,
    rating DECIMAL(3,2),
    position INTEGER DEFAULT 0,
    clan_created_at TIMESTAMP,
    clan_updated_at TIMESTAMP,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_content_change_at TIMESTAMP,
    article_content_hash TEXT,
    feature_image_local TEXT
);

-- Indexes for clan_kb_articles
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_category_id ON clan_kb_articles(category_id);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_url_key ON clan_kb_articles(url_key);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_is_active ON clan_kb_articles(is_active);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_updated_at ON clan_kb_articles(clan_updated_at);
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_position ON clan_kb_articles(category_id, position);

-- Full-text search index (for PostgreSQL full-text search - available as alternative to vector search)
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_text_fts ON clan_kb_articles USING GIN(to_tsvector('english', text));

-- Index for change detection queries
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_content_change 
ON clan_kb_articles(last_content_change_at) 
WHERE last_content_change_at IS NOT NULL;
```

---

## Design Decisions

### 1. Consistency with Existing Tables
- Follows same patterns as `clan_products` and `clan_categories`
- Uses `id` as primary key (from API)
- Includes `first_seen_at` and `last_updated` for tracking
- Uses hash-based change detection for articles

### 2. Hierarchy Support
- `clan_kb_categories` supports multi-level hierarchy via `parent_id` and `path`
- `path` field enables efficient "find all descendants" queries
- `level` field for filtering by depth

### 3. Content Storage
- `text` field stores full HTML content (similar to `clan_products.description`)
- `short_text` for excerpts/summaries (if available)
- `article_content_hash` for detecting content changes

### 4. Metadata Fields
- SEO fields (`meta_title`, `meta_keywords`, `meta_description`) stored for future use
- User information cached (`user_id`, `user_name`) to avoid additional lookups

### 5. Voting/Rating System
- Stores `votes_sum`, `votes_num`, and calculated `rating`
- Allows filtering/sorting by popularity

### 6. Active/Inactive Status
- `is_active` boolean for soft-delete functionality
- Allows keeping historical data while hiding inactive items

---

## Integration with Existing Systems

### Vector Search Integration
- Articles will be chunked and added to `content_chunks` table
- `chunk_type` will be `'kb'` for Knowledge Base articles
- Similar chunking strategy as products/categories

### Content Generation
- KB articles can be used as context in blog post generation
- Articles can be referenced in product/category profiles
- Can generate blog posts from KB articles

### Cache Management
- Similar to `clan_cache.py` for products/categories
- Will need `clan_kb_cache.py` or extend existing cache system
- Track sync status in `clan_cache_metadata` table
- **On-demand sync**: No scheduled sync, triggered by user action
- **Change detection**: Compare `article_content_hash` to detect updates
- **Image caching**: Download and store feature images locally

---

## Migration Strategy

### Phase 1: Table Creation
1. Create `clan_kb_categories` table
2. Create `clan_kb_articles` table
3. Add indexes

### Phase 2: Data Population
1. Fetch all KB categories via `/getKnowledgebaseCategories`
2. For each category, fetch articles via `/getKnowledgebaseArticles`
3. Store categories and articles in database
4. Update `clan_cache_metadata` with sync timestamp

### Phase 3: Integration
1. Add KB articles to vector search index
2. Update content generation to use KB context
3. Add KB search to content generator modal

---

## Design Decisions - Resolved

### 1. Sync Frequency: **ON DEMAND**
- KB data will be synced on-demand (not scheduled)
- Similar to heritage research regeneration
- Users can trigger sync via UI button or API endpoint
- Track last sync time in `clan_cache_metadata` table

### 2. Change Detection: **YES**
- Track which articles changed using `article_content_hash`
- Compare hash on sync to detect changes
- Store change history or notify users of updates
- Add `last_content_change_at` timestamp field to track when content actually changed

### 3. Image Storage: **YES**
- `feature_image` URLs will be cached/downloaded locally
- Store local path in database (add `feature_image_local` field)
- Download images to `static/images/kb/` or similar
- Update image URLs in HTML content to point to local copies

### 4. Full-Text Search: **BOTH (Vector by Default)**
- **Vector search** (default): Use existing FAISS index for semantic search
- **PostgreSQL full-text search**: Available as fallback/alternative
- Full-text search index already included in schema (GIN index on `text`)
- Both methods available, vector search preferred for semantic understanding

### 5. User Table: **KEEP IT SIMPLE**
- Store `user_id` and `user_name` directly in `clan_kb_articles` table
- No separate `clan_kb_users` table needed
- User information cached for display purposes only

### 6. Article Relationships: **MAY ADD LATER**
- No `related_articles` field in initial implementation
- Schema designed to allow adding this feature later
- Can add `related_article_ids` JSONB field when needed
- For now, relationships can be inferred from categories/keywords

### 7. Content Cleaning: **CLEAN DURING CHUNKING, NOT STORAGE**

**What content cleaning means:**
- **For storage**: Keep original HTML in `text` field (for display)
- **For vector search**: Clean HTML when chunking (extract plain text, decode entities, normalize whitespace)
- **For full-text search**: PostgreSQL handles HTML automatically, or we clean on-the-fly

**Current approach (same as products/categories):**
- Store original HTML in database
- Use `ContentChunker.clean_html()` method when creating chunks for vector search
- Cleaning process:
  1. Parse HTML with BeautifulSoup
  2. Extract plain text (removes tags)
  3. Decode HTML entities (`&amp;` → `&`, etc.)
  4. Normalize whitespace (multiple spaces → single space)
  5. Strip leading/trailing whitespace

**No additional fields needed** - cleaning happens during chunking, not storage.

**Note:** The schema already includes `feature_image_local` and `last_content_change_at` fields in the main CREATE TABLE statement above.

---

## Next Steps

1. ✅ **Review this proposal** - COMPLETE
2. ✅ **Resolve questions** - COMPLETE
3. **Create migration file** (`migrations/create_clan_kb_tables.sql`)
4. **Create cache module** (`blog-launchpad/clan_kb_cache.py` or extend existing)
5. **Test API endpoints** and data structure
6. **Implement data population script**
7. **Add image download functionality** for feature images
8. **Implement change detection** logic

---

**Last Updated:** 2025-11-11

