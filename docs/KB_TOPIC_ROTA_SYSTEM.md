# KB Topic Rota System - Technical Documentation

**Date:** 2026-01-22  
**Status:** ✅ **IMPLEMENTED** - System fully operational  
**Purpose:** Comprehensive technical documentation for the KB Topic Rota System

---

## Overview

The KB Topic Rota System is a **perpetual, data-driven system** that:
1. **Discovers topics** from Knowledge Base articles using unsupervised clustering
2. **Generates diverse weekly schedules** ensuring non-repetitive content
3. **Aggregates content** from multiple KB articles for each topic
4. **Feeds social media production** processes for channel-specific formatting
5. **Self-updates** automatically as new KB content is added

---

## System Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    KB Topic Discovery System                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Topic Clustering Engine                                  │
│     └─> Discovers themes from KB embeddings                  │
│                                                               │
│  2. Topic Management Database                                │
│     └─> Stores discovered topics, relationships, metadata  │
│                                                               │
│  3. Rota Generator                                           │
│     └─> Creates diverse weekly schedule                      │
│                                                               │
│  4. Content Aggregator                                       │
│     └─> Pulls relevant KB content for each topic             │
│                                                               │
│  5. Social Media Production Interface                        │
│     └─> Exposes topics + content for channel-specific format │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Social Media    │
                    │  Production     │
                    │  (Separate)     │
                    └──────────────────┘
```

---

## Database Schema

### Tables

#### 1. `kb_topics`
Stores discovered topics from KB clustering.

**Key Fields:**
- `id` - Primary key
- `topic_name` - Abstract topic name (e.g., "Tartan Design Principles")
- `topic_keywords` - Array of keywords extracted from cluster
- `embedding_vector` - Topic centroid embedding (1024 dimensions)
- `article_ids` - Array of KB article IDs belonging to this topic
- `category_ids` - Array of category IDs this topic spans
- `topic_type` - Classification: 'practical', 'historical', 'cultural', 'design', 'product', etc.
- `is_active` - Whether topic is active in rota

**Indexes:**
- `idx_kb_topics_active` - On `is_active` (partial, where active)
- `idx_kb_topics_priority` - On `priority, is_active`
- `idx_kb_topics_article_ids` - GIN index on `article_ids`
- `idx_kb_topics_category_ids` - GIN index on `category_ids`

#### 2. `kb_topic_similarity`
Pre-computed similarity between topics for diversity scheduling.

**Key Fields:**
- `topic1_id`, `topic2_id` - Topic pair (with constraint topic1_id < topic2_id)
- `similarity_score` - Cosine similarity (0.0 to 1.0)
- `distance` - L2 distance between embeddings

**Indexes:**
- Primary key on `(topic1_id, topic2_id)`
- `idx_topic_similarity_score` - On `similarity_score`

#### 3. `kb_topic_rota`
Weekly schedule of topics.

**Key Fields:**
- `id` - Primary key
- `topic_id` - Foreign key to `kb_topics`
- `scheduled_year`, `scheduled_week` - ISO week identifiers
- `scheduled_date` - First day of week (Monday)
- `diversity_score` - How diverse from recent topics (0.0 to 1.0)
- `status` - 'scheduled', 'ready', 'published', 'skipped'

**Constraints:**
- Unique on `(scheduled_year, scheduled_week)`

#### 4. `kb_rota_history`
History of posted topics for diversity tracking.

**Key Fields:**
- `rota_id` - Foreign key to `kb_topic_rota`
- `topic_id` - Foreign key to `kb_topics`
- `posted_date` - Date when topic was posted
- `similarity_to_previous` - Similarity to previous week topic

#### 5. `kb_topic_content`
Aggregated content from multiple KB articles for each topic.

**Key Fields:**
- `id` - Primary key
- `topic_id` - Foreign key to `kb_topics`
- `rota_id` - Foreign key to `kb_topic_rota` (optional)
- `aggregated_text` - Combined text content
- `source_article_ids` - Array of KB article IDs that contributed
- `source_chunk_ids` - Array of `content_chunks.id` used
- `content_hash` - MD5 hash for change detection
- `word_count` - Word count of aggregated text

---

## Core Modules

### 1. Clustering Engine (`utils/kb_topic_discovery/clustering.py`)

**Class:** `KBTopicClusterer`

**Methods:**
- `discover_topics()` - Main discovery method
  - Supports: 'kmeans', 'dbscan', 'hierarchical' clustering
  - Auto-detects optimal cluster count for K-means
  - Returns list of topic dictionaries

**Clustering Algorithms:**
- **K-means:** Auto-detects optimal k using silhouette score
- **DBSCAN:** Density-based clustering (eps=0.5, min_samples=3)
- **Hierarchical:** Agglomerative clustering with cosine distance

**Topic Extraction:**
- Keyword extraction using frequency analysis
- Topic naming from keywords or article titles
- Topic type classification (practical, historical, cultural, design, product)
- Category ID extraction from articles

### 2. Similarity Calculator (`utils/kb_topic_discovery/similarity.py`)

**Class:** `TopicSimilarityCalculator`

**Methods:**
- `compute_similarity_matrix()` - Calculate pairwise similarities
- `get_similarity()` - Retrieve similarity from database

**Similarity Metric:**
- Cosine similarity between topic centroid embeddings
- Stored in `kb_topic_similarity` table

### 3. Diversity Manager (`utils/kb_topic_discovery/diversity.py`)

**Class:** `DiversityManager`

**Methods:**
- `calculate_diversity()` - Calculate diversity score for a topic
  - Considers similarity to recent topics
  - Bonuses for different topic types
  - Bonuses for different category areas
  - Penalties for too-similar topics

**Diversity Scoring:**
- Base score: `1.0 - min_similarity` (lower similarity = higher diversity)
- Type bonus: +0.15 if different topic type
- Category bonus: +0.1 * (1 - category_overlap)
- Penalty: *0.5 if similarity > threshold

### 4. Rota Generator (`utils/kb_topic_discovery/rota_generator.py`)

**Class:** `RotaGenerator`

**Methods:**
- `generate_rota()` - Generate weekly rota with diversity constraints
  - Parameters: start_date, weeks, lookback_weeks, min_similarity_gap
  - Returns list of rota entry dictionaries
- `save_rota()` - Save rota entries to database

**Rota Generation Algorithm:**
1. Get active topics
2. Get recent topics (lookback window)
3. For each week:
   - Filter candidates (exclude recently used)
   - Calculate diversity scores
   - Select topic (weighted random favoring diversity)
   - Update recent topics list
4. Save to database

### 5. Content Aggregator (`utils/kb_topic_discovery/content_aggregator.py`)

**Class:** `TopicContentAggregator`

**Methods:**
- `aggregate_content()` - Aggregate content from topic articles
  - Ranks chunks by relevance to topic centroid
  - Selects top N chunks
  - Combines with clear separators
- `save_aggregated_content()` - Save to database

**Aggregation Process:**
1. Get articles for topic
2. Retrieve chunks for articles
3. Generate embeddings for chunks
4. Rank by similarity to topic centroid
5. Select top N chunks
6. Combine with article structure preserved

---

## API Endpoints

### Base URL: `/api/kb-topics`

#### `GET /api/kb-topics/rota`
Get weekly rota schedule.

**Query Parameters:**
- `year` (optional) - Year (default: current year)
- `week` (optional) - ISO week number (default: current week)

**Response:**
```json
{
  "success": true,
  "topic": {
    "id": 5,
    "name": "Tartan Design Principles",
    "description": "...",
    "keywords": ["design", "tartan", "pattern"],
    "type": "design",
    "article_ids": [12, 45],
    "category_ids": [3, 7]
  },
  "content": {
    "aggregated_text": "...",
    "source_article_ids": [12, 45],
    "word_count": 1250
  },
  "schedule": {
    "year": 2026,
    "week": 5,
    "date": "2026-01-26",
    "diversity_score": 0.85,
    "status": "scheduled"
  }
}
```

#### `GET /api/kb-topics/<topic_id>/content`
Get aggregated content for a topic.

**Response:**
```json
{
  "success": true,
  "topic": { ... },
  "content": {
    "aggregated_text": "...",
    "source_article_ids": [12, 45],
    "source_chunk_ids": [101, 102, 103],
    "word_count": 1250
  }
}
```

#### `POST /api/kb-topics/discover`
Trigger topic discovery (clustering) process.

**Request Body:**
```json
{
  "method": "kmeans",
  "n_clusters": 20,
  "min_cluster_size": 3,
  "similarity_threshold": 0.7,
  "compute_similarity": true
}
```

**Response:**
```json
{
  "success": true,
  "topics_discovered": 15,
  "topics": [
    {
      "id": 5,
      "name": "Tartan Design Principles",
      "type": "design",
      "article_count": 8,
      "keywords": ["design", "tartan", "pattern"]
    }
  ]
}
```

#### `POST /api/kb-topics/regenerate-rota`
Regenerate rota with diversity constraints.

**Request Body:**
```json
{
  "start_date": "2026-01-26",
  "weeks": 52,
  "lookback_weeks": 6,
  "min_similarity_gap": 0.7
}
```

#### `GET /api/kb-topics/topics`
List all topics.

**Query Parameters:**
- `active_only` (optional) - Only return active topics (default: true)

---

## Scripts

### 1. `scripts/discover_kb_topics.py`
Manual topic discovery script.

**Usage:**
```bash
python scripts/discover_kb_topics.py \
  --method kmeans \
  --n-clusters 20 \
  --min-cluster-size 3 \
  --compute-similarity
```

**Options:**
- `--method` - Clustering method: 'kmeans', 'dbscan', 'hierarchical'
- `--n-clusters` - Number of clusters (auto-detect if not specified)
- `--min-cluster-size` - Minimum cluster size (default: 3)
- `--similarity-threshold` - Similarity threshold for hierarchical (default: 0.7)
- `--compute-similarity` - Compute and store similarity matrix

### 2. `scripts/kb_topic_discovery_runner.py`
Automated runner for perpetual operation.

**Features:**
- Checks for new/updated KB articles
- Runs topic discovery if new articles found
- Maintains rota schedule (fills gaps)
- Aggregates content for upcoming topics
- Regenerates rota if incomplete

**Integration:**
- Runs weekly on Mondays via `background_posting_monitor.sh`

---

## Usage Workflow

### Initial Setup

1. **Run Database Migration:**
   ```bash
   psql -d your_database -f migrations/20260122_create_kb_topic_rota_tables.sql
   ```

2. **Initial Topic Discovery:**
   ```bash
   python scripts/discover_kb_topics.py --method kmeans --compute-similarity
   ```

3. **Generate Initial Rota:**
   ```bash
   # Via API
   curl -X POST http://localhost:5000/api/kb-topics/regenerate-rota \
     -H "Content-Type: application/json" \
     -d '{"weeks": 52}'
   ```

### Ongoing Operation

The system runs automatically:
- **Weekly Discovery:** Runs every Monday via background monitor
- **Rota Maintenance:** Automatically fills gaps and aggregates content
- **Manual Triggers:** Use API endpoints for manual discovery/regeneration

### Social Media Production Integration

1. **Get Weekly Topic:**
   ```bash
   curl http://localhost:5000/api/kb-topics/rota?year=2026&week=5
   ```

2. **Format for Channel:**
   - Extract topic and aggregated content
   - Format for Facebook, Instagram, Twitter, Blog
   - Use topic keywords and type for context

3. **Track Usage:**
   - Update rota status to 'published' when posted
   - System tracks history for diversity calculations

---

## Technical Details

### Embedding Model
- **Model:** `intfloat/e5-large-v2`
- **Dimensions:** 1024
- **Normalization:** Yes (L2 normalized)

### Clustering Parameters

**K-means:**
- Auto-detection: Tests k=5 to k=50 (or len/10)
- Uses silhouette score for optimization
- Random state: 42

**DBSCAN:**
- eps: 0.5 (cosine distance)
- min_samples: 3 (configurable)

**Hierarchical:**
- Linkage: 'average'
- Metric: 'cosine'
- Distance threshold: 1.0 - similarity_threshold

### Diversity Constraints

- **Minimum Similarity Gap:** 0.7 (configurable)
- **Lookback Window:** 6 weeks (configurable)
- **Type Bonus:** +0.15 for different topic type
- **Category Bonus:** +0.1 * (1 - overlap) for different categories

### Content Aggregation

- **Chunk Selection:** Top 5 chunks by relevance (configurable)
- **Ranking:** Cosine similarity to topic centroid
- **Combination:** Preserves article structure with separators

---

## Maintenance

### Regenerating Embeddings

If KB articles are updated, embeddings are regenerated automatically when:
- Topic discovery runs (weekly)
- New articles detected
- Articles updated since last discovery

### Updating Topics

Topics can be manually updated:
```sql
UPDATE kb_topics
SET topic_name = 'New Name',
    priority = 10,
    is_active = TRUE
WHERE id = 5;
```

### Regenerating Rota

Rota can be regenerated:
- Via API: `POST /api/kb-topics/regenerate-rota`
- Automatically: If rota has gaps (< 48 weeks scheduled)

---

## Related Documentation

- `docs/KB_TOPIC_EXTRACTION_FEASIBILITY.md` - Feasibility analysis
- `docs/KB_TOPIC_ROTA_SYSTEM_IMPLEMENTATION_PLAN.md` - Implementation plan
- `docs/VECTOR_TABLES_SUMMARY.md` - Vector infrastructure overview
- `templates/knowledge_base/backend/vector_search.html` - Vector search KB page

---

## Status

✅ **FULLY IMPLEMENTED**

- Database schema: ✅ Complete
- Clustering engine: ✅ Complete
- Similarity calculation: ✅ Complete
- Diversity management: ✅ Complete
- Rota generation: ✅ Complete
- Content aggregation: ✅ Complete
- API endpoints: ✅ Complete
- Perpetual operation: ✅ Complete
- Integration: ✅ Complete

**Ready for production use.**
