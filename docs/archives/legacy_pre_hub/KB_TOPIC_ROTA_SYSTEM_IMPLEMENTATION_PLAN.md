# KB Topic Rota System - Implementation Plan

**Date:** 2026-01-22  
**Status:** ✅ **COMPLETED** - System fully implemented and operational  
**Purpose:** Create a perpetual system for discovering topics from KB data and scheduling them weekly for social media production

**Related Documentation:**
- `docs/KB_TOPIC_ROTA_SYSTEM.md` - Complete technical documentation
- `docs/KB_TOPIC_EXTRACTION_FEASIBILITY.md` - Feasibility analysis

---

## System Overview

### Goal

Create a **perpetual, data-driven system** that:
1. **Discovers new angles** in KB content through unsupervised clustering
2. **Generates weekly theme schedule** with diversity and non-repetition
3. **Feeds social media production** processes that format content for different channels
4. **Self-updates** as new KB content is added

### Key Principles

- **Unsupervised Discovery:** No manual topic lists - themes emerge from data
- **Perpetual Operation:** System runs continuously, discovering new topics
- **Diversity First:** Ensures interesting, non-repetitive schedule
- **Channel Agnostic:** Topics are abstract - formatting happens downstream
- **Data-Driven:** All decisions based on actual KB content, not assumptions

---

## Architecture

### System Components

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

## Phase 1: Database Schema

### 1.1 Topic Discovery Tables

```sql
-- Stores discovered topics from KB clustering
CREATE TABLE kb_topics (
    id SERIAL PRIMARY KEY,
    topic_name TEXT NOT NULL,
    topic_description TEXT,
    topic_keywords TEXT[],  -- Array of keywords extracted from cluster
    cluster_id INTEGER,  -- Original cluster ID from clustering run
    embedding_vector REAL[],  -- Topic centroid embedding (1024 dims)
    article_ids INTEGER[],  -- Articles that belong to this topic
    category_ids INTEGER[],  -- Categories this topic spans
    topic_type VARCHAR(50),  -- 'practical', 'historical', 'cultural', 'design', etc.
    priority INTEGER DEFAULT 0,  -- For rota ordering
    is_active BOOLEAN DEFAULT TRUE,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT  -- Manual notes/refinements
);

CREATE INDEX idx_kb_topics_active ON kb_topics(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_kb_topics_priority ON kb_topics(priority, is_active);
CREATE INDEX idx_kb_topics_article_ids ON kb_topics USING GIN(article_ids);
CREATE INDEX idx_kb_topics_category_ids ON kb_topics USING GIN(category_ids);
```

### 1.2 Topic Similarity Matrix

```sql
-- Pre-computed similarity between topics (for diversity)
CREATE TABLE kb_topic_similarity (
    topic1_id INTEGER REFERENCES kb_topics(id) ON DELETE CASCADE,
    topic2_id INTEGER REFERENCES kb_topics(id) ON DELETE CASCADE,
    similarity_score DECIMAL(4,3) NOT NULL,  -- 0.0 to 1.0
    distance DECIMAL(8,4),  -- L2 distance between embeddings
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (topic1_id, topic2_id),
    CHECK (topic1_id < topic2_id)  -- Ensure one direction only
);

CREATE INDEX idx_topic_similarity_score ON kb_topic_similarity(similarity_score);
```

### 1.3 Weekly Rota Schedule

```sql
-- Weekly schedule of topics
CREATE TABLE kb_topic_rota (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES kb_topics(id) ON DELETE SET NULL,
    scheduled_week INTEGER NOT NULL,  -- ISO week number
    scheduled_year INTEGER NOT NULL,
    scheduled_date DATE,  -- First day of week (Monday)
    diversity_score DECIMAL(4,3),  -- How diverse from recent topics
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled, ready, published, skipped
    content_summary TEXT,  -- Aggregated content preview
    source_article_ids INTEGER[],  -- Which articles were aggregated
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scheduled_year, scheduled_week)
);

CREATE INDEX idx_rota_year_week ON kb_topic_rota(scheduled_year, scheduled_week);
CREATE INDEX idx_rota_status ON kb_topic_rota(status);
CREATE INDEX idx_rota_date ON kb_topic_rota(scheduled_date);
```

### 1.4 Rota History (for diversity tracking)

```sql
-- Track what's been posted for diversity calculations
CREATE TABLE kb_rota_history (
    id SERIAL PRIMARY KEY,
    rota_id INTEGER REFERENCES kb_topic_rota(id),
    topic_id INTEGER REFERENCES kb_topics(id),
    posted_date DATE,
    diversity_score DECIMAL(4,3),
    similarity_to_previous DECIMAL(4,3),  -- Similarity to previous week
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rota_history_date ON kb_rota_history(posted_date DESC);
CREATE INDEX idx_rota_history_topic ON kb_rota_history(topic_id);
```

### 1.5 Topic Content Aggregation

```sql
-- Stores aggregated content for each topic (for social media production)
CREATE TABLE kb_topic_content (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES kb_topics(id) ON DELETE CASCADE,
    rota_id INTEGER REFERENCES kb_topic_rota(id) ON DELETE CASCADE,
    aggregated_text TEXT NOT NULL,  -- Combined content from multiple articles
    source_article_ids INTEGER[] NOT NULL,  -- Which articles contributed
    source_chunk_ids INTEGER[],  -- Specific chunks used
    content_hash TEXT,  -- Hash for change detection
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_topic_content_topic ON kb_topic_content(topic_id);
CREATE INDEX idx_topic_content_rota ON kb_topic_content(rota_id);
```

---

## Phase 2: Topic Discovery Engine

### 2.1 Clustering Implementation

**File:** `utils/kb_topic_discovery/clustering.py`

```python
class KBTopicClusterer:
    """
    Clusters KB articles by semantic similarity to discover topics.
    """
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator('intfloat/e5-large-v2')
        self.faiss_manager = FAISSIndexManager()
    
    def discover_topics(self, 
                       method='kmeans',
                       n_clusters=None,  # Auto-detect if None
                       min_cluster_size=3,
                       similarity_threshold=0.7) -> List[Dict]:
        """
        Discover topics by clustering KB articles.
        
        Returns:
            List of topic dictionaries with:
            - cluster_id
            - article_ids
            - centroid_embedding
            - keywords
            - suggested_name
        """
        # 1. Load all KB chunk embeddings
        kb_embeddings = self._load_kb_embeddings()
        
        # 2. Apply clustering algorithm
        if method == 'kmeans':
            clusters = self._kmeans_cluster(kb_embeddings, n_clusters)
        elif method == 'dbscan':
            clusters = self._dbscan_cluster(kb_embeddings, min_cluster_size)
        elif method == 'hierarchical':
            clusters = self._hierarchical_cluster(kb_embeddings, similarity_threshold)
        
        # 3. Extract topic information from clusters
        topics = []
        for cluster_id, cluster_data in enumerate(clusters):
            topic = self._extract_topic_info(cluster_id, cluster_data)
            topics.append(topic)
        
        return topics
    
    def _extract_topic_info(self, cluster_id, cluster_data) -> Dict:
        """
        Extract topic name, keywords, and metadata from cluster.
        """
        # Get article texts from cluster
        article_texts = self._get_cluster_article_texts(cluster_data['article_ids'])
        
        # Extract keywords (TF-IDF or LLM)
        keywords = self._extract_keywords(article_texts)
        
        # Generate topic name (LLM or keyword-based)
        topic_name = self._generate_topic_name(article_texts, keywords)
        
        # Calculate centroid embedding
        centroid = self._calculate_centroid(cluster_data['embeddings'])
        
        return {
            'cluster_id': cluster_id,
            'topic_name': topic_name,
            'keywords': keywords,
            'article_ids': cluster_data['article_ids'],
            'category_ids': cluster_data['category_ids'],
            'centroid_embedding': centroid,
            'topic_type': self._classify_topic_type(article_texts),
            'article_count': len(cluster_data['article_ids'])
        }
```

### 2.2 Topic Naming

**Options:**
1. **LLM-based:** Use Ollama to generate topic names from cluster content
2. **Keyword-based:** Extract most common meaningful keywords
3. **Hybrid:** LLM generates, keywords validate

**Recommended:** LLM-based for better abstraction

```python
def _generate_topic_name(self, article_texts: List[str], keywords: List[str]) -> str:
    """
    Generate abstract topic name from cluster content.
    """
    # Combine article titles and summaries
    context = "\n".join([
        f"Article: {title}\nSummary: {summary[:200]}"
        for title, summary in article_texts[:10]  # Top 10 articles
    ])
    
    prompt = f"""
    Based on these Knowledge Base articles, suggest a concise, abstract topic name 
    that captures the recurring theme. The topic should be broad enough to cover 
    multiple articles but specific enough to be meaningful.
    
    Articles:
    {context}
    
    Keywords: {', '.join(keywords[:10])}
    
    Suggest a topic name (2-5 words, no quotes):
    """
    
    topic_name = llm_generate(prompt, model='llama3.2')
    return topic_name.strip()
```

### 2.3 Topic Type Classification

```python
def _classify_topic_type(self, article_texts: List[str]) -> str:
    """
    Classify topic type: practical, historical, cultural, design, etc.
    """
    # Analyze article titles and content
    # Use simple keyword matching or LLM classification
    
    types = {
        'practical': ['how', 'guide', 'measure', 'fit', 'care', 'maintain'],
        'historical': ['history', 'origin', 'evolution', 'century', 'tradition'],
        'cultural': ['heritage', 'tradition', 'significance', 'meaning', 'identity'],
        'design': ['design', 'create', 'custom', 'pattern', 'color', 'style'],
        'product': ['product', 'fabric', 'material', 'quality', 'specification']
    }
    
    # Score each type based on content
    # Return highest scoring type
```

---

## Phase 3: Diversity & Rota Generation

### 3.1 Topic Similarity Calculation

**File:** `utils/kb_topic_discovery/similarity.py`

```python
class TopicSimilarityCalculator:
    """
    Calculates similarity between topics for diversity scheduling.
    """
    
    def compute_similarity_matrix(self, topics: List[Dict]) -> Dict[Tuple[int, int], float]:
        """
        Compute pairwise similarity between all topics.
        Stores in kb_topic_similarity table.
        """
        similarities = {}
        
        for i, topic1 in enumerate(topics):
            for j, topic2 in enumerate(topics[i+1:], start=i+1):
                # Calculate cosine similarity between embeddings
                similarity = cosine_similarity(
                    topic1['centroid_embedding'],
                    topic2['centroid_embedding']
                )
                
                similarities[(topic1['id'], topic2['id'])] = similarity
                
                # Store in database
                self._store_similarity(topic1['id'], topic2['id'], similarity)
        
        return similarities
```

### 3.2 Rota Generator with Diversity

**File:** `utils/kb_topic_discovery/rota_generator.py`

```python
class RotaGenerator:
    """
    Generates diverse weekly rota ensuring non-repetition and variety.
    """
    
    def __init__(self):
        self.similarity_calculator = TopicSimilarityCalculator()
        self.diversity_manager = DiversityManager()
    
    def generate_rota(self, 
                     start_date: date,
                     weeks: int = 52,
                     lookback_weeks: int = 6,
                     min_similarity_gap: float = 0.7) -> List[Dict]:
        """
        Generate weekly rota with diversity constraints.
        
        Args:
            start_date: First Monday of rota
            weeks: Number of weeks to schedule
            lookback_weeks: How many recent weeks to check for diversity
            min_similarity_gap: Minimum similarity threshold to avoid (0.0-1.0)
        
        Returns:
            List of rota entries
        """
        # Get active topics
        topics = self._get_active_topics()
        
        # Get recent rota history
        recent_topics = self._get_recent_topics(lookback_weeks)
        
        rota = []
        current_date = start_date
        
        for week_num in range(weeks):
            # Calculate diversity scores for all candidates
            candidates = []
            for topic in topics:
                # Skip if topic was used recently
                if self._was_used_recently(topic['id'], recent_topics, lookback_weeks):
                    continue
                
                # Calculate diversity score
                diversity_score = self.diversity_manager.calculate_diversity(
                    topic, 
                    recent_topics,
                    min_similarity_gap
                )
                
                candidates.append({
                    'topic': topic,
                    'diversity_score': diversity_score
                })
            
            if not candidates:
                # Fallback: reset recent topics if no candidates
                recent_topics = []
                candidates = [{'topic': t, 'diversity_score': 1.0} for t in topics]
            
            # Select topic (weighted random favoring diversity)
            selected = self._select_topic(candidates)
            
            # Create rota entry
            rota_entry = {
                'topic_id': selected['topic']['id'],
                'scheduled_year': current_date.isocalendar()[0],
                'scheduled_week': current_date.isocalendar()[1],
                'scheduled_date': current_date,
                'diversity_score': selected['diversity_score'],
                'status': 'scheduled'
            }
            
            rota.append(rota_entry)
            
            # Update recent topics
            recent_topics.append(selected['topic'])
            if len(recent_topics) > lookback_weeks:
                recent_topics.pop(0)
            
            # Move to next week (Monday)
            current_date += timedelta(days=7)
        
        return rota
```

### 3.3 Diversity Manager

**File:** `utils/kb_topic_discovery/diversity.py`

```python
class DiversityManager:
    """
    Manages diversity calculations for rota generation.
    """
    
    def calculate_diversity(self, 
                           topic: Dict,
                           recent_topics: List[Dict],
                           min_similarity_gap: float = 0.7) -> float:
        """
        Calculate how diverse this topic is from recent topics.
        Higher score = more diverse.
        """
        if not recent_topics:
            return 1.0  # No recent topics = maximum diversity
        
        # Get similarity scores to recent topics
        similarities = []
        for recent in recent_topics:
            similarity = self._get_topic_similarity(topic['id'], recent['id'])
            similarities.append(similarity)
        
        # Minimum similarity (worst case)
        min_similarity = min(similarities) if similarities else 1.0
        
        # Diversity score: lower similarity = higher diversity
        diversity_score = 1.0 - min_similarity
        
        # Bonus for different topic type
        recent_types = {r.get('topic_type') for r in recent_topics}
        if topic.get('topic_type') not in recent_types:
            diversity_score += 0.15
        
        # Bonus for different category areas
        recent_categories = set()
        for r in recent_topics:
            recent_categories.update(r.get('category_ids', []))
        
        topic_categories = set(topic.get('category_ids', []))
        category_overlap = len(recent_categories & topic_categories) / max(len(topic_categories), 1)
        category_bonus = (1.0 - category_overlap) * 0.1
        diversity_score += category_bonus
        
        # Penalty if too similar
        if min_similarity > min_similarity_gap:
            diversity_score *= 0.5  # Reduce score if too similar
        
        return min(diversity_score, 1.0)  # Cap at 1.0
```

---

## Phase 4: Content Aggregation

### 4.1 Content Aggregator

**File:** `utils/kb_topic_discovery/content_aggregator.py`

```python
class TopicContentAggregator:
    """
    Aggregates relevant content from multiple KB articles for a topic.
    """
    
    def aggregate_content(self, topic_id: int, limit: int = 5) -> Dict:
        """
        Aggregate content from articles belonging to this topic.
        
        Returns:
            Dictionary with:
            - aggregated_text: Combined content
            - source_article_ids: Which articles were used
            - source_chunk_ids: Specific chunks used
            - word_count
        """
        # Get topic
        topic = self._get_topic(topic_id)
        
        # Get articles for this topic
        article_ids = topic['article_ids']
        
        # Retrieve chunks for these articles
        chunks = self._get_article_chunks(article_ids)
        
        # Rank chunks by relevance to topic centroid
        ranked_chunks = self._rank_chunks_by_relevance(
            chunks, 
            topic['centroid_embedding']
        )
        
        # Select top N chunks
        selected_chunks = ranked_chunks[:limit]
        
        # Aggregate content
        aggregated_text = self._combine_chunks(selected_chunks)
        
        return {
            'aggregated_text': aggregated_text,
            'source_article_ids': list(set(c['article_id'] for c in selected_chunks)),
            'source_chunk_ids': [c['chunk_id'] for c in selected_chunks],
            'word_count': len(aggregated_text.split())
        }
    
    def _rank_chunks_by_relevance(self, chunks, topic_embedding):
        """
        Rank chunks by similarity to topic centroid.
        """
        ranked = []
        for chunk in chunks:
            chunk_embedding = self._get_chunk_embedding(chunk['chunk_id'])
            similarity = cosine_similarity(topic_embedding, chunk_embedding)
            ranked.append({
                **chunk,
                'relevance_score': similarity
            })
        
        return sorted(ranked, key=lambda x: x['relevance_score'], reverse=True)
```

---

## Phase 5: Social Media Production Interface

### 5.1 API Endpoints

**File:** `blueprints/kb_topic_rota_api.py`

```python
@bp.route('/api/kb-topics/rota')
def get_rota(year=None, week=None):
    """
    Get weekly rota schedule.
    
    Returns topics scheduled for specified week (or current week).
    """
    # Get rota entry for week
    # Return topic + aggregated content
    pass

@bp.route('/api/kb-topics/<int:topic_id>/content')
def get_topic_content(topic_id):
    """
    Get aggregated content for a topic.
    
    Returns:
    - Topic metadata
    - Aggregated text
    - Source articles
    - Ready for social media formatting
    """
    pass

@bp.route('/api/kb-topics/discover')
def discover_topics():
    """
    Trigger topic discovery (clustering) process.
    
    Returns:
    - New topics discovered
    - Updated topic list
    """
    pass

@bp.route('/api/kb-topics/regenerate-rota')
def regenerate_rota(start_date, weeks=52):
    """
    Regenerate rota with diversity constraints.
    """
    pass
```

### 5.2 Social Media Production Integration

**Interface Contract:**

```python
# For social media production processes
{
    "topic": {
        "id": 5,
        "name": "Tartan Design Principles",
        "description": "Recurring theme about tartan design...",
        "keywords": ["design", "tartan", "pattern", "color"],
        "topic_type": "design"
    },
    "content": {
        "aggregated_text": "Combined content from multiple articles...",
        "source_articles": [
            {"id": 12, "name": "Four ways to start your tartan design"},
            {"id": 45, "name": "Adding colour lines to your design"}
        ],
        "word_count": 1250
    },
    "schedule": {
        "year": 2026,
        "week": 5,
        "date": "2026-01-26"
    }
}
```

**Channel-Specific Formatting:**
- **Facebook:** Can extract key points, create engaging posts
- **Instagram:** Can create image concepts, captions
- **Twitter:** Can create thread topics, key quotes
- **Blog:** Can create full articles from aggregated content

---

## Phase 6: Perpetual Operation

### 6.1 Automatic Topic Discovery

**File:** `scripts/kb_topic_discovery_runner.py`

```python
def run_topic_discovery():
    """
    Periodic job to discover new topics from KB.
    Runs when:
    - New KB articles added
    - KB articles updated
    - Manual trigger
    """
    # 1. Check for new/updated KB articles
    new_articles = check_for_new_kb_articles()
    
    if new_articles:
        # 2. Re-cluster (or incremental clustering)
        clusterer = KBTopicClusterer()
        new_topics = clusterer.discover_topics()
        
        # 3. Compare with existing topics
        existing_topics = get_existing_topics()
        
        # 4. Add new topics, merge similar, update existing
        update_topic_database(new_topics, existing_topics)
        
        # 5. Regenerate rota if needed
        if should_regenerate_rota():
            regenerate_rota()
```

### 6.2 Rota Maintenance

```python
def maintain_rota():
    """
    Periodic maintenance of rota schedule.
    """
    # 1. Check for upcoming weeks without topics
    upcoming_gaps = find_rota_gaps(weeks_ahead=4)
    
    if upcoming_gaps:
        # 2. Fill gaps with diverse topics
        fill_rota_gaps(upcoming_gaps)
    
    # 3. Recalculate diversity scores
    recalculate_diversity_scores()
    
    # 4. Flag topics that need content aggregation
    flag_topics_for_aggregation()
```

### 6.3 Integration with Background Monitor

**File:** `scripts/background_posting_monitor.sh`

Add steps:
1. Run topic discovery (weekly or on KB updates)
2. Maintain rota schedule (weekly)
3. Aggregate content for upcoming topics (weekly)

---

## Phase 7: Implementation Steps

### Step 1: Database Schema (Week 1)

- [ ] Create migration file: `migrations/create_kb_topic_rota_tables.sql`
- [ ] Create all 5 tables (topics, similarity, rota, history, content)
- [ ] Add indexes
- [ ] Test schema

### Step 2: Clustering Engine (Week 1-2)

- [ ] Create `utils/kb_topic_discovery/` directory
- [ ] Implement `KBTopicClusterer` class
- [ ] Add clustering methods (K-means, DBSCAN, hierarchical)
- [ ] Implement topic extraction (keywords, naming)
- [ ] Test with sample KB articles

### Step 3: Topic Discovery Script (Week 2)

- [ ] Create `scripts/discover_kb_topics.py`
- [ ] Implement full discovery pipeline
- [ ] Add topic naming (LLM-based)
- [ ] Store topics in database
- [ ] Test end-to-end discovery

### Step 4: Similarity Calculation (Week 2)

- [ ] Implement `TopicSimilarityCalculator`
- [ ] Calculate pairwise similarities
- [ ] Store in `kb_topic_similarity` table
- [ ] Test similarity accuracy

### Step 5: Rota Generator (Week 3)

- [ ] Implement `RotaGenerator` class
- [ ] Implement `DiversityManager`
- [ ] Create rota generation algorithm
- [ ] Test diversity constraints
- [ ] Generate initial 52-week rota

### Step 6: Content Aggregation (Week 3)

- [ ] Implement `TopicContentAggregator`
- [ ] Add chunk ranking by relevance
- [ ] Test content aggregation
- [ ] Store aggregated content

### Step 7: API Endpoints (Week 4)

- [ ] Create `blueprints/kb_topic_rota_api.py`
- [ ] Implement all API endpoints
- [ ] Add authentication/authorization
- [ ] Test API responses

### Step 8: Social Media Interface (Week 4)

- [ ] Design interface contract
- [ ] Create example integrations
- [ ] Document for social media production team
- [ ] Test with sample topics

### Step 9: Perpetual Operation (Week 5)

- [ ] Create `scripts/kb_topic_discovery_runner.py`
- [ ] Add to background monitor
- [ ] Implement rota maintenance
- [ ] Test automatic updates

### Step 10: UI for Management (Week 5-6)

- [ ] Create topic management interface
- [ ] Rota visualization/editing
- [ ] Topic review/refinement tools
- [ ] Content preview interface

---

## Technical Details

### Clustering Algorithm Selection

**Recommended: Hybrid Approach**

1. **Initial Discovery:** K-means with auto-k detection
   - Use elbow method or silhouette score
   - Start with k=20-50 clusters

2. **Refinement:** Hierarchical clustering
   - Merge similar clusters
   - Split overly broad clusters

3. **Ongoing Updates:** Incremental clustering
   - Add new articles to existing clusters
   - Create new clusters for truly new topics

### Topic Naming Strategy

**LLM-Based (Recommended):**
```python
prompt = """
Analyze these Knowledge Base articles and suggest a concise topic name 
(2-5 words) that captures the recurring theme:

Articles:
{article_summaries}

The topic name should be:
- Abstract (not just a category name)
- Broad enough to cover multiple articles
- Specific enough to be meaningful
- Suitable for social media content

Topic name:
"""
```

### Diversity Constraints

**Rules:**
1. **Minimum Gap:** Topics with similarity >0.7 can't be within 4 weeks
2. **Category Rotation:** Different category areas every 2-3 weeks
3. **Topic Type Variety:** Mix practical, historical, cultural, design
4. **Similarity Threshold:** Reject topics with similarity >0.85 to recent

### Content Aggregation Strategy

**Selection:**
1. Rank all chunks by similarity to topic centroid
2. Select top 5-10 chunks
3. Ensure chunks come from different articles (diversity)
4. Combine with clear section breaks
5. Preserve source attribution

---

## Integration Points

### 1. Social Media Production

**Interface:**
```python
# Social media production process calls:
GET /api/kb-topics/rota?year=2026&week=5

# Returns:
{
    "topic": {...},
    "content": {...},
    "schedule": {...}
}

# Production process then:
# - Formats for Facebook (key points, engaging)
# - Creates Instagram content (images, captions)
# - Generates Twitter threads
# - Creates blog posts
```

### 2. Calendar Integration

- Topics can appear in calendar views
- Link to rota schedule
- Show upcoming topics

### 3. Content Generation

- Use topics as prompts for LLM content generation
- Aggregate KB content as context
- Generate channel-specific formats

---

## Testing Strategy

### Unit Tests

1. **Clustering:** Test with known article sets
2. **Diversity:** Test diversity scoring with mock topics
3. **Rota Generation:** Test with various constraints
4. **Content Aggregation:** Test chunk selection and combination

### Integration Tests

1. **End-to-End Discovery:** Full pipeline from KB to topics
2. **Rota Generation:** Generate 52-week rota, verify diversity
3. **API Endpoints:** Test all endpoints with real data
4. **Perpetual Operation:** Test automatic updates

### Validation

1. **Topic Quality:** Manual review of discovered topics
2. **Rota Diversity:** Verify no repetitive topics
3. **Content Quality:** Review aggregated content
4. **Performance:** Ensure clustering completes in reasonable time

---

## Success Metrics

### Discovery Quality

- **Topic Coverage:** % of KB articles assigned to topics
- **Topic Uniqueness:** Average similarity between topics (lower = better)
- **Cross-Category Topics:** % of topics spanning multiple categories

### Rota Quality

- **Diversity Score:** Average diversity score (higher = better)
- **Repetition Rate:** % of weeks with similar topics (lower = better)
- **Category Balance:** Distribution across category areas

### Content Quality

- **Aggregation Coverage:** % of topics with aggregated content
- **Source Diversity:** Average articles per topic
- **Content Length:** Appropriate for social media (500-2000 words)

---

## Future Enhancements

### Phase 2 Features

1. **Topic Evolution:** Track how topics change over time
2. **Seasonal Topics:** Identify time-sensitive topics
3. **Topic Performance:** Track engagement by topic
4. **Auto-Refinement:** LLM-based topic refinement
5. **Multi-Language:** Support for different languages

### Advanced Features

1. **Topic Relationships:** Graph of topic connections
2. **Topic Trends:** Identify emerging/declining topics
3. **A/B Testing:** Test different topic angles
4. **Audience Segmentation:** Different rotas for different audiences

---

## Documentation Requirements

### User Documentation

- [ ] Topic discovery process explanation
- [ ] Rota management guide
- [ ] Content aggregation overview
- [ ] Social media production integration guide

### Technical Documentation

- [ ] Clustering algorithm details
- [ ] Diversity algorithm explanation
- [ ] API reference
- [ ] Database schema documentation

### Knowledge Base Updates

- [ ] Add KB page for Topic Rota System
- [ ] Document in Backend Systems section
- [ ] Link to social media production workflows

---

## Estimated Timeline

**Total: 5-6 weeks**

- **Week 1:** Database schema + clustering engine
- **Week 2:** Topic discovery + similarity calculation
- **Week 3:** Rota generator + content aggregation
- **Week 4:** API endpoints + social media interface
- **Week 5:** Perpetual operation + UI
- **Week 6:** Testing, refinement, documentation

---

## Dependencies

### Python Packages

- `scikit-learn` - Clustering algorithms
- `numpy` - Vector operations
- `faiss-cpu` - Vector similarity (already installed)
- `sentence-transformers` - Embeddings (already installed)

### Existing Infrastructure

- ✅ Vector search system (FAISS, embeddings)
- ✅ KB articles in database
- ✅ Content chunks with embeddings
- ✅ LLM integration (Ollama)

### New Infrastructure Needed

- ⚠️ Clustering algorithms
- ⚠️ Topic management database
- ⚠️ Rota scheduling system
- ⚠️ Content aggregation logic

---

## Risk Mitigation

### Risk 1: Poor Topic Quality

**Mitigation:**
- Manual review step after discovery
- LLM-based topic naming validation
- Keyword extraction as fallback
- Iterative refinement process

### Risk 2: Rota Repetition

**Mitigation:**
- Strict diversity constraints
- Similarity threshold enforcement
- Lookback window (6+ weeks)
- Manual override capability

### Risk 3: Performance Issues

**Mitigation:**
- Incremental clustering for updates
- Cache similarity calculations
- Batch processing for large datasets
- Background job processing

---

**Status:** Ready for implementation  
**Priority:** High - Enables data-driven social media content strategy  
**Dependencies:** Vector search infrastructure (✅ Complete)
