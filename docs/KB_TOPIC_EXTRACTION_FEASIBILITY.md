# KB Topic Extraction for Weekly Social Media Rota - Feasibility Analysis

**Date:** 2026-01-22  
**Purpose:** Assess whether current vectorized KB data can support topic extraction and cross-category content aggregation for weekly social media posts

---

## User Goal

Create a **rota of weekly social media posts** about "topics we're expert in" by:
1. **Analyzing existing KB** to identify recurring topics across different sections
2. **Creating abstract topic list** (not category-based, but theme-based)
3. **Aggregating content** from multiple KB sections for each topic
4. **Avoiding random selection** - topics should be data-driven from actual KB content

**Topics of interest:**
- Kilts
- Tartans
- Tartan design
- Scottish genealogy
- Customer service skills
- And more (to be discovered from KB analysis)

---

## Current Data Structure Assessment

### ✅ What We Have

**1. Vectorized KB Articles:**
- **696 chunks** from **629 articles**
- All chunks have **1024-dimensional embeddings** (E5-large-v2 model)
- Chunks include:
  - Article title/name
  - Full cleaned text content
  - Category context
  - Metadata (article_id, category_id, url_key)

**2. Semantic Search Capability:**
- Can find similar articles by meaning (not just keywords)
- Can search across all KB chunks
- Can filter by category if needed
- Returns similarity scores

**3. Cross-Category Data:**
- Articles span multiple categories:
  - Scottish Clans & Families
  - Tartans
  - Kilts
  - Customer Service/Help
  - Navigation/Search
  - And more
- Category hierarchy stored in `clan_kb_categories` with `path` field

**4. Rich Content:**
- Article titles (e.g., "What is tartan? What makes it unique?")
- Full HTML content (cleaned for chunking)
- Short summaries (when available)
- Category context

---

## What's Needed for Topic Extraction

### ✅ Already Possible

**1. Semantic Clustering:**
- **Vector embeddings** can be used for clustering
- Similar articles will have similar embeddings
- Can group articles by semantic similarity, not just category

**2. Topic Discovery:**
- Can search for articles about a topic (e.g., "tartan design")
- Will find articles across multiple categories
- Can aggregate results from different sections

**3. Content Aggregation:**
- Can retrieve multiple relevant chunks for a topic
- Can combine content from different articles
- Metadata includes article_id and category_id for tracking sources

### ⚠️ What Needs to Be Added

**1. Topic Clustering Algorithm:**
- Need to implement clustering on embeddings (e.g., K-means, DBSCAN, or hierarchical clustering)
- Group similar articles into topic clusters
- Identify cluster centroids as "abstract topics"

**2. Topic Extraction/Naming:**
- Need to extract or generate topic names from clusters
- Could use:
  - LLM to summarize cluster content into topic name
  - Most common keywords in cluster
  - Article title patterns

**3. Cross-Category Topic Identification:**
- Current category structure is hierarchical but topic-based
- Need to identify topics that span categories
- Vector similarity already enables this (articles with similar embeddings = same topic)

**4. Topic Rota System:**
- Need database table to store:
  - Abstract topics (extracted from KB)
  - Related article IDs (from clustering)
  - Rota schedule (which topic when)
  - Content aggregation rules

---

## Recommended Approach

### Phase 1: Topic Discovery (Analysis)

**1. Clustering KB Articles:**
```python
# Pseudo-code approach
1. Load all KB chunk embeddings from FAISS
2. Apply clustering algorithm (e.g., K-means with k=20-50)
3. Identify clusters with high similarity
4. For each cluster:
   - Get all articles in cluster
   - Extract common themes/keywords
   - Generate topic name (LLM or keyword extraction)
```

**2. Topic Validation:**
- Review clusters manually
- Merge similar clusters
- Split clusters that are too broad
- Create abstract topic names

**3. Cross-Category Mapping:**
- For each topic, list which categories it spans
- Identify articles from different categories that belong to same topic
- Document content sources for each topic

### Phase 2: Topic Rota Creation

**1. Topic Database:**
```sql
CREATE TABLE kb_topics (
    id SERIAL PRIMARY KEY,
    topic_name TEXT NOT NULL,
    topic_description TEXT,
    keywords TEXT[],  -- Array of keywords
    category_ids INTEGER[],  -- Categories this topic spans
    article_ids INTEGER[],  -- Articles that cover this topic
    priority INTEGER DEFAULT 0,  -- For rota ordering
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. Rota Schedule:**
```sql
CREATE TABLE kb_topic_rota (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES kb_topics(id),
    scheduled_date DATE,
    scheduled_time TIME,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, ready, published
    content_summary TEXT,  -- Aggregated content from multiple articles
    source_article_ids INTEGER[],  -- Which articles were used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Phase 3: Content Aggregation

**1. For Each Topic:**
- Query vector search for topic keywords
- Retrieve top-N relevant articles (across all categories)
- Aggregate content from multiple articles
- Use LLM to synthesize into coherent post

**2. Content Sources:**
- Primary article (highest similarity)
- Supporting articles (from same topic cluster)
- Cross-reference information from different categories

---

## Implementation Feasibility

### ✅ YES - Current Data Structure Supports This

**Reasons:**

1. **Vector Embeddings Enable Clustering:**
   - All KB chunks have embeddings
   - Can calculate similarity between any two articles
   - Can group articles by semantic similarity

2. **Cross-Category Content Available:**
   - Articles span multiple categories
   - Category information stored but not restrictive
   - Can aggregate content from different categories

3. **Rich Metadata:**
   - Article IDs, category IDs, URLs all stored
   - Can track which articles belong to which topics
   - Can aggregate content from multiple sources

4. **Semantic Search Works:**
   - Can find articles about a topic across categories
   - Similarity scores help identify most relevant content
   - Can retrieve multiple relevant chunks

### What Needs to Be Built

**1. Clustering Script:**
- Load embeddings from FAISS
- Apply clustering algorithm
- Generate topic clusters
- Extract topic names

**2. Topic Management:**
- Database tables for topics and rota
- UI for reviewing/editing topics
- Content aggregation logic

**3. Content Synthesis:**
- Aggregate content from multiple articles
- Use LLM to create coherent posts
- Maintain source attribution

---

## Example Workflow

### Step 1: Discover Topics

```python
# Cluster KB articles by embedding similarity
clusters = cluster_kb_articles(k=30)  # 30 topics

# Example cluster:
Cluster 5:
  - Articles: [2, 45, 123, 234]  # Across multiple categories
  - Categories: [66, 135, 160]  # Scottish clans, Tartans, Find tartans
  - Common keywords: ["tartan", "family", "clan", "heritage"]
  - Topic Name: "Tartan and Family Heritage"
```

### Step 2: Create Rota

```python
# Schedule topics weekly
rota = [
    Week 1: "Tartan and Family Heritage"
    Week 2: "Kilt Fitting and Measurements"
    Week 3: "Scottish Genealogy Research"
    # etc.
]
```

### Step 3: Generate Post Content

```python
# For each scheduled topic
topic = "Tartan and Family Heritage"
articles = get_topic_articles(topic_id)  # [2, 45, 123, 234]

# Aggregate content
content = aggregate_kb_content(articles)
# Combines relevant sections from multiple articles

# Generate post
post = llm_synthesize(content, format="social_media")
```

---

## Technical Implementation

### Clustering Options

**1. K-Means Clustering:**
- Simple, fast
- Need to specify number of clusters (k)
- Good for well-separated topics

**2. DBSCAN:**
- Automatic cluster detection
- Handles outliers
- Good for varying topic sizes

**3. Hierarchical Clustering:**
- Creates topic hierarchy
- Can merge/split clusters
- Good for understanding relationships

**4. Topic Modeling (LDA/BERTopic):**
- Extracts topics from text
- Can identify latent topics
- More sophisticated but slower

### Recommended: Hybrid Approach

1. **Initial Clustering:** Use K-means or DBSCAN on embeddings
2. **Topic Naming:** Use LLM to generate topic names from cluster content
3. **Manual Review:** Review and refine topics
4. **Rota Creation:** Schedule topics for weekly posts
5. **Content Aggregation:** Use vector search to find relevant articles for each topic

---

## Conclusion

### ✅ **YES - The current data structure CAN support this**

**What's Available:**
- ✅ Vector embeddings for all KB articles
- ✅ Semantic search across categories
- ✅ Rich metadata (articles, categories, content)
- ✅ Cross-category content available

**What Needs to Be Built:**
- ⚠️ Clustering algorithm to group articles by topic
- ⚠️ Topic extraction/naming system
- ⚠️ Topic management database tables
- ⚠️ Content aggregation logic
- ⚠️ Rota scheduling system

**Recommended Next Steps:**
1. Create clustering script to analyze KB articles
2. Generate initial topic clusters
3. Review and refine topics manually
4. Create topic management system
5. Build content aggregation for rota posts

The vectorized KB data is **perfectly suited** for this use case - it enables semantic topic discovery across categories, which is exactly what's needed for identifying recurring themes that span different KB sections.

---

## Key Questions Answered

### Q1: Will this discover unexpected themes without being influenced by examples?

**✅ YES - Completely Unsupervised Discovery**

**How it works:**
1. **Clustering is data-driven** - No keywords or examples needed
2. **Embeddings capture semantic meaning** - Articles with similar concepts cluster together automatically
3. **No bias from examples** - The algorithm doesn't know about "kilts" or "tartans" - it just finds patterns in the data
4. **Discovers latent themes** - Will find topics you might not have thought of

**Example:**
- You might discover a cluster about "measurement and fitting" that spans:
  - Kilt measurements
  - Shirt sizing
  - Fabric lengths
  - Custom fitting advice
- This emerges naturally from content similarity, not from you specifying it

**What you'll discover:**
- Recurring themes across categories (e.g., "heritage and tradition" appears in both tartan and clan articles)
- Unexpected connections (e.g., "customer service" and "product care" might cluster together)
- Sub-topics within broad categories (e.g., "tartan design" vs "tartan history" vs "tartan occasions")

### Q2: Can it create an interesting, non-repetitive weekly schedule?

**✅ YES - Diversity Algorithms Ensure Variety**

**Approach:**

**1. Topic Diversity Scoring:**
```python
def calculate_diversity_score(topic, recent_topics):
    """
    Score how different this topic is from recently posted topics.
    Higher score = more diverse/interesting
    """
    # Check embedding similarity to recent topics
    similarity_to_recent = max([
        cosine_similarity(topic.embedding, recent.embedding)
        for recent in recent_topics
    ])
    
    # Lower similarity = higher diversity score
    diversity_score = 1.0 - similarity_to_recent
    
    # Bonus for different category
    if topic.category not in [r.category for r in recent_topics]:
        diversity_score += 0.2
    
    return diversity_score
```

**2. Rota Generation Algorithm:**
```python
def generate_diverse_rota(topics, weeks=52):
    """
    Generate weekly rota ensuring variety and avoiding repetition.
    """
    rota = []
    recent_topics = []  # Track last N weeks
    
    for week in range(weeks):
        # Calculate diversity scores for all remaining topics
        candidates = [
            (topic, calculate_diversity_score(topic, recent_topics))
            for topic in topics
            if topic not in [r['topic'] for r in rota[-4:]]  # Not in last 4 weeks
        ]
        
        # Select topic with highest diversity score
        # (or weighted random selection favoring diversity)
        selected = weighted_select(candidates, favor_high_scores=True)
        
        rota.append({
            'week': week + 1,
            'topic': selected,
            'diversity_score': selected.diversity_score
        })
        
        # Update recent topics (keep last 4-6 weeks)
        recent_topics.append(selected)
        if len(recent_topics) > 6:
            recent_topics.pop(0)
    
    return rota
```

**3. Anti-Repetition Rules:**
- **Minimum gap:** Same topic category can't appear within N weeks (e.g., 4-6 weeks)
- **Similarity threshold:** Topics with similarity >0.8 can't be consecutive
- **Category rotation:** Ensure different category areas are represented
- **Topic variety:** Track topic "families" and ensure rotation

**4. Interest Factors:**
- **Variety in topic types:** Mix practical (how-to), historical, cultural, product-focused
- **Seasonal relevance:** Consider time of year (e.g., wedding topics in spring/summer)
- **Depth variation:** Mix deep-dive topics with lighter content
- **Cross-topic connections:** Sometimes highlight how topics relate

---

## Example: Discovering Unexpected Themes

**What clustering might find (unexpected):**

1. **"Measurement and Sizing"** - Spans:
   - Kilt measurements
   - Shirt sizing conversions
   - Fabric minimums
   - Custom fitting advice
   - (Not obvious from category structure!)

2. **"Heritage and Identity"** - Spans:
   - Clan history
   - Tartan meanings
   - Family traditions
   - Cultural significance
   - (Crosses multiple category boundaries)

3. **"Care and Maintenance"** - Spans:
   - Kilt care
   - Fabric care
   - Travel tips
   - Storage advice
   - (Practical theme across products)

4. **"Design and Customization"** - Spans:
   - Tartan design
   - Custom tartans
   - Color selection
   - Pattern adaptation
   - (Creative/design theme)

**These emerge from content similarity, not from you specifying them!**

---

## Rota Diversity Example

**Week 1-6 (ensuring variety):**
- Week 1: "Tartan Design Principles" (design/creative)
- Week 2: "Scottish Genealogy Research" (research/historical) ← Different from Week 1
- Week 3: "Kilt Fitting Guide" (practical/how-to) ← Different from Weeks 1-2
- Week 4: "Heritage and Family Traditions" (cultural/historical) ← Similar to Week 2 but different angle
- Week 5: "Fabric Care and Maintenance" (practical/care) ← Different from previous
- Week 6: "Tartan in Fashion History" (historical/fashion) ← Different from all previous

**Diversity checks:**
- ✅ No two "kilt" topics in a row
- ✅ Mix of practical, historical, cultural
- ✅ Different category areas represented
- ✅ Similarity scores ensure variety

---

## Implementation: Diversity System

### Database Schema Addition

```sql
-- Track topic diversity relationships
CREATE TABLE kb_topic_similarity (
    topic1_id INTEGER REFERENCES kb_topics(id),
    topic2_id INTEGER REFERENCES kb_topics(id),
    similarity_score DECIMAL(4,3),  -- 0.0 to 1.0
    PRIMARY KEY (topic1_id, topic2_id)
);

-- Track rota history for diversity
CREATE TABLE kb_rota_history (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES kb_topics(id),
    posted_date DATE,
    diversity_score DECIMAL(4,3),  -- How diverse this was from previous posts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Diversity Algorithm

```python
class RotaDiversityManager:
    def __init__(self):
        self.recent_topics = []  # Last N weeks
        self.topic_similarities = {}  # Pre-computed similarities
    
    def select_next_topic(self, available_topics, lookback_weeks=6):
        """
        Select next topic ensuring diversity from recent posts.
        """
        # Get recent topics (last N weeks)
        recent = self.recent_topics[-lookback_weeks:]
        
        # Score each candidate
        candidates = []
        for topic in available_topics:
            # Calculate minimum similarity to recent topics
            min_similarity = min([
                self.topic_similarities.get((topic.id, r.id), 0.0)
                for r in recent
            ]) if recent else 1.0
            
            # Diversity score (lower similarity = more diverse)
            diversity = 1.0 - min_similarity
            
            # Bonus for different category
            category_bonus = 0.2 if topic.category not in [r.category for r in recent] else 0.0
            
            total_score = diversity + category_bonus
            candidates.append((topic, total_score))
        
        # Select topic with highest diversity score
        # (or use weighted random to add some variety)
        return max(candidates, key=lambda x: x[1])[0]
```

---

## Benefits

### 1. Unbiased Discovery
- ✅ Finds themes you didn't expect
- ✅ No influence from examples you give
- ✅ Pure data-driven clustering
- ✅ Discovers latent patterns

### 2. Intelligent Scheduling
- ✅ Avoids repetition (similar topics spaced out)
- ✅ Ensures variety (different categories, angles)
- ✅ Maintains interest (mix of practical, historical, cultural)
- ✅ Prevents topic fatigue (no "kilt week" followed by "kilt care week")

### 3. Cross-Category Insights
- ✅ Finds connections between categories
- ✅ Identifies recurring themes across sections
- ✅ Discovers expertise areas you might not have realized

---

## Next Steps

1. **Run clustering** to discover topics (unsupervised, no examples needed)
2. **Review clusters** to understand what themes emerged
3. **Implement diversity algorithm** for rota generation
4. **Test rota** to ensure variety and interest
5. **Iterate** based on results

**The system will discover themes organically from your KB content, not from examples you provide!**
