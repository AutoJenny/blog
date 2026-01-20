# Recipe Research System - Design & Implementation Plan

**Date:** 2026-01-19  
**Purpose:** Design a comprehensive, extensible research system for recipe posts (and eventually all post types) that happens BEFORE drafting

---

## Executive Summary

This system introduces a **Research Stage** that occurs before Authoring/Drafting, providing structured, agent-driven web research that generates factual content for integration into expanded background sections. Initially implemented for recipes, designed to be extensible to all post types.

---

## Research Methodology

### 1. Research Framework Structure

#### For Recipes: Background Research Topics

Each recipe will have a structured background section covering multiple research dimensions:

1. **Origins & Early History**
   - Research focus: "earliest mentions and recorded origins of [recipe name] in Scotland"
   - Key questions: When first documented? Where did it originate? Earliest written records?
   - Source priorities: Academic food history, museum archives, historical cookbooks, heritage sites

2. **Geographic Spread & Regional Variations**
   - Research focus: "geographic distribution and regional variations of [recipe name] across Scotland"
   - Key questions: Which regions claim it? How does it vary by location? Regional names?
   - Source priorities: Regional heritage sites, tourism boards, local history societies

3. **Evolution Over Time**
   - Research focus: "how [recipe name] has evolved from historical to modern versions"
   - Key questions: Original ingredients vs. modern? Cooking methods changed? When did changes occur?
   - Source priorities: Food history journals, historical cookbook comparisons, culinary archives

4. **Cultural Significance & Traditions**
   - Research focus: "cultural significance and traditional occasions for [recipe name] in Scottish culture"
   - Key questions: When traditionally eaten? Associated festivals/events? Cultural meaning?
   - Source priorities: Cultural heritage sites, festival organizations, traditional food societies

5. **Modern Incarnations & Contemporary Use**
   - Research focus: "modern versions and contemporary uses of [recipe name] in Scotland today"
   - Key questions: How is it made today? Restaurant adaptations? Home cooking trends?
   - Source priorities: Contemporary food blogs (reputable), restaurant reviews, modern cookbooks

#### Extensibility to Other Post Types

The framework uses **configurable research topics** per post type:

- **Themed Posts**: Historical context, cultural significance, modern relevance, key figures, events
- **Profile Posts**: Family history, geographic origins, notable members, heraldic traditions
- **Generated Posts**: Product history, manufacturing evolution, cultural associations

### 2. Research Process Flow

#### Sequential Research Execution

1. **Topic Definition** (per research element)
   - Generate specific, narrow research query for each topic
   - Example: "the earliest mentions and recorded origins of the Forfar Bridie foodstuff in Scotland"
   - Include recipe name, specific aspect, geographic context

2. **Source Discovery** (Agent-based)
   - Agent performs web search with academic/reliable source prioritization
   - Filters results by domain authority (edu, gov, org, museum sites)
   - Ranks by relevance and reliability

3. **Content Extraction** (Agent-based)
   - Agent fetches and analyzes page content from top sources
   - Extracts factual claims relevant to the research topic
   - Identifies quotations, dates, locations, key facts

4. **Fact Collation** (LLM-assisted)
   - LLM processes extracted content to identify key factual items
   - Structures facts: dates, locations, people, events, cultural notes
   - Flags uncertainties, conflicts, or legendary claims

5. **Paragraph Synthesis** (LLM-assisted)
   - LLM synthesizes collated facts into coherent paragraph(s)
   - Maintains factual accuracy, cites sources, handles uncertainties
   - Outputs ready-to-integrate content for background section

6. **Source Documentation**
   - Maintains list of sources used with:
     - Title & URL
     - Why it's reliable (domain type, authority)
     - Key facts extracted from it
   - Links to "Further Reading" section

### 3. Source Prioritization Strategy

#### Tier 1: Academic & Institutional (Highest Priority)
- `.edu` domains (university food history departments)
- `.gov` domains (heritage organizations, museums)
- Museum websites (National Museums Scotland, etc.)
- Academic journals (food history, cultural studies)

#### Tier 2: Heritage & Cultural Organizations
- Historic Environment Scotland
- VisitScotland heritage pages
- Local history societies
- Traditional food preservation organizations

#### Tier 3: Authoritative Reference Sites
- Wikipedia (with verification)
- Encyclopedia Britannica
- Specialized food history sites
- Reputable culinary archives

#### Tier 4: Contemporary (Lower Priority, for Modern Incarnations)
- Established food blogs with credentials
- Restaurant reviews from reputable publications
- Modern cookbook references

#### Excluded Sources
- Competing recipe sites (unless historical)
- General cooking blogs
- Social media
- Unverified user-generated content

---

## Technical Implementation

### 1. Workflow Integration

#### Add Research Stage to Recipe Workflow

**Current Recipe Workflow:**
```
Planning (skipped) → Authoring (drafting) → Imaging → Header
```

**New Recipe Workflow:**
```
Planning (skipped) → Research → Authoring (drafting) → Imaging → Header
```

**Implementation:**
- Update `config/post_type_substages.py`:
  ```python
  'recipe': {
      'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
      'research': ['background_research'],  # NEW
      'authoring': ['drafting', 'recipe_image_style_prompt', 'image_captions'],
      ...
  }
  ```

- Create route: `/research/posts/{post_id}/background-research`
- Update navigation to go to research stage instead of drafting for recipes

### 2. Database Schema

#### New Table: `post_research`

```sql
CREATE TABLE post_research (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    research_topic VARCHAR(100) NOT NULL,  -- e.g., 'origins', 'geographic_spread'
    topic_label VARCHAR(200) NOT NULL,      -- e.g., 'Origins & Early History'
    status VARCHAR(50) DEFAULT 'pending',   -- pending, researching, completed, failed
    research_query TEXT,                   -- Generated search query
    sources JSONB,                          -- Array of source objects
    extracted_facts JSONB,                 -- Structured facts extracted
    synthesized_content TEXT,               -- Final paragraph(s) for integration
    error_message TEXT,                       -- Error if research failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    UNIQUE(post_id, research_topic)
);

CREATE INDEX idx_post_research_post_id ON post_research(post_id);
CREATE INDEX idx_post_research_status ON post_research(status);
```

#### Update `post_development` Table

Add field to store research configuration:
```sql
ALTER TABLE post_development 
ADD COLUMN IF NOT EXISTS research_config JSONB;
```

Store per-post-type research topic definitions:
```json
{
  "research_topics": [
    {
      "key": "origins",
      "label": "Origins & Early History",
      "search_template": "earliest mentions and recorded origins of {recipe_name} in Scotland",
      "priority": 1
    },
    {
      "key": "geographic_spread",
      "label": "Geographic Spread & Regional Variations",
      "search_template": "geographic distribution and regional variations of {recipe_name} across Scotland",
      "priority": 2
    }
    // ... etc
  ]
}
```

### 3. Research Agent System

#### Core Module: `utils/research_agents/`

**File Structure:**
```
utils/research_agents/
├── __init__.py
├── web_researcher.py      # Web search and content fetching
├── fact_extractor.py      # Extract facts from content
├── source_evaluator.py    # Evaluate source reliability
├── content_synthesizer.py # Synthesize facts into paragraphs
└── config.py              # Research topic configurations per post type
```

#### Key Components

**1. Web Researcher (`web_researcher.py`)**
```python
class WebResearcher:
    def search(self, query: str, max_results: int = 10) -> List[Dict]
    def fetch_content(self, url: str) -> Optional[str]
    def prioritize_sources(self, results: List[Dict]) -> List[Dict]
    def filter_by_domain_authority(self, results: List[Dict]) -> List[Dict]
```

**2. Fact Extractor (`fact_extractor.py`)**
```python
class FactExtractor:
    def extract_facts(self, content: str, topic: str, recipe_name: str) -> Dict
    def structure_facts(self, raw_facts: List[Dict]) -> Dict
    def identify_uncertainties(self, facts: Dict) -> List[str]
```

**3. Source Evaluator (`source_evaluator.py`)**
```python
class SourceEvaluator:
    def evaluate_reliability(self, url: str, domain: str) -> Dict
    def get_domain_tier(self, domain: str) -> int
    def is_academic_source(self, url: str) -> bool
```

**4. Content Synthesizer (`content_synthesizer.py`)**
```python
class ContentSynthesizer:
    def synthesize_paragraph(self, facts: Dict, topic: str, recipe_name: str) -> str
    def integrate_sources(self, content: str, sources: List[Dict]) -> str
    def handle_uncertainties(self, content: str, uncertainties: List[str]) -> str
```

### 4. Research Topic Configuration

#### File: `config/research_topics.py`

```python
RESEARCH_TOPICS_CONFIG = {
    'recipe': {
        'topics': [
            {
                'key': 'origins',
                'label': 'Origins & Early History',
                'search_template': 'earliest mentions and recorded origins of {item_name} in Scotland',
                'focus_areas': [
                    'first documented appearance',
                    'original location/region',
                    'earliest written records',
                    'historical cookbook references'
                ],
                'source_priorities': ['academic', 'museum', 'heritage'],
                'word_target': 150
            },
            {
                'key': 'geographic_spread',
                'label': 'Geographic Spread & Regional Variations',
                'search_template': 'geographic distribution and regional variations of {item_name} across Scotland',
                'focus_areas': [
                    'regional variations',
                    'different names by region',
                    'local adaptations',
                    'regional popularity'
                ],
                'source_priorities': ['heritage', 'tourism', 'regional_history'],
                'word_target': 150
            },
            {
                'key': 'evolution',
                'label': 'Evolution Over Time',
                'search_template': 'how {item_name} has evolved from historical to modern versions',
                'focus_areas': [
                    'ingredient changes over time',
                    'cooking method evolution',
                    'when changes occurred',
                    'modern vs traditional versions'
                ],
                'source_priorities': ['food_history', 'academic', 'museum'],
                'word_target': 150
            },
            {
                'key': 'cultural_significance',
                'label': 'Cultural Significance & Traditions',
                'search_template': 'cultural significance and traditional occasions for {item_name} in Scottish culture',
                'focus_areas': [
                    'traditional occasions',
                    'festival associations',
                    'cultural meaning',
                    'ceremonial use'
                ],
                'source_priorities': ['cultural_heritage', 'festival_orgs', 'tourism'],
                'word_target': 150
            },
            {
                'key': 'modern_incarnations',
                'label': 'Modern Incarnations & Contemporary Use',
                'search_template': 'modern versions and contemporary uses of {item_name} in Scotland today',
                'focus_areas': [
                    'contemporary preparation',
                    'restaurant adaptations',
                    'home cooking trends',
                    'modern variations'
                ],
                'source_priorities': ['contemporary_food', 'restaurant_reviews', 'modern_cookbooks'],
                'word_target': 100
            }
        ]
    },
    'themed': {
        'topics': [
            # Future: Historical context, key figures, events, etc.
        ]
    },
    'profile': {
        'topics': [
            # Future: Family history, geographic origins, etc.
        ]
    }
}
```

### 5. API Endpoints

#### Research Management API

**File:** `blueprints/research_api.py` (new)

```python
@bp.route('/api/posts/<int:post_id>/research/topics', methods=['GET'])
def get_research_topics(post_id):
    """Get available research topics for this post type"""

@bp.route('/api/posts/<int:post_id>/research/status', methods=['GET'])
def get_research_status(post_id):
    """Get research status for all topics"""

@bp.route('/api/posts/<int:post_id>/research/<topic_key>/start', methods=['POST'])
def start_research(post_id, topic_key):
    """Start research for a specific topic"""

@bp.route('/api/posts/<int:post_id>/research/<topic_key>/status', methods=['GET'])
def get_topic_research_status(post_id, topic_key):
    """Get research status for a specific topic"""

@bp.route('/api/posts/<int:post_id>/research/<topic_key>/results', methods=['GET'])
def get_research_results(post_id, topic_key):
    """Get research results (sources, facts, synthesized content)"""

@bp.route('/api/posts/<int:post_id>/research/<topic_key>/regenerate', methods=['POST'])
def regenerate_research(post_id, topic_key):
    """Regenerate research for a topic (re-run the process)"""

@bp.route('/api/posts/<int:post_id>/research/synthesize-background', methods=['POST'])
def synthesize_background_section(post_id):
    """Combine all research topics into final background section content"""
```

### 6. UI Implementation

#### Research Page Template

**File:** `templates/research/posts/{post_id}/background_research.html`

**Structure:**
- Header with recipe name and status
- Research topics list (accordion or cards)
- For each topic:
  - Status indicator (pending, researching, completed)
  - Research query display
  - Sources found (with reliability indicators)
  - Extracted facts (collapsible)
  - Synthesized paragraph (editable)
  - Action buttons (Start Research, Regenerate, View Details)

#### Research Topic Card Component

Each topic shows:
- Topic label and description
- Status badge
- Progress indicator (if researching)
- Generated search query
- Sources list (with tier indicators)
- Extracted facts summary
- Synthesized content preview
- Actions: Start/View/Regenerate

### 7. Research Execution Flow

#### Step-by-Step Process

1. **User Initiates Research**
   - Clicks "Start Research" on a topic
   - API endpoint: `POST /api/posts/{post_id}/research/{topic_key}/start`

2. **Generate Research Query**
   - Replace `{item_name}` in search template with actual recipe name
   - Example: "earliest mentions and recorded origins of Forfar Bridie in Scotland"

3. **Web Search Phase**
   - Agent performs search using `perform_web_search()`
   - Gets 10-15 initial results
   - Filters and prioritizes by domain authority
   - Returns top 5-7 most reliable sources

4. **Content Fetching Phase**
   - Agent fetches full content from each prioritized source
   - Extracts main text content (removes navigation, ads, etc.)
   - Stores raw content for analysis

5. **Fact Extraction Phase**
   - LLM analyzes each source's content
   - Extracts facts relevant to research topic
   - Structures facts: dates, locations, people, events, cultural notes
   - Flags uncertainties and conflicts

6. **Source Documentation**
   - For each source used:
     - Title, URL, domain type
     - Reliability assessment
     - Key facts extracted from it
   - Stored in `post_research.sources` JSONB

7. **Content Synthesis Phase**
   - LLM synthesizes all extracted facts into coherent paragraph(s)
   - Maintains factual accuracy
   - Handles uncertainties appropriately
   - Integrates source citations naturally
   - Outputs ready-to-use content

8. **Storage & Display**
   - Store in `post_research` table
   - Update status to 'completed'
   - Display synthesized content in UI
   - Make available for integration into background section

### 8. Integration with Drafting

#### Background Section Enhancement

When user reaches drafting stage:
- Research content is available for each topic
- User can:
  - Review synthesized paragraphs
  - Edit/refine content
  - Integrate into `recipe_background` section
  - See source citations

#### Automated Integration Option

- Option to auto-populate background section from research
- Combines all research topics into expanded background
- User can then edit/refine

---

## Implementation Phases

### Phase 1: Core Research Infrastructure
1. Create `utils/research_agents/` module structure
2. Implement `WebResearcher` class
3. Implement `SourceEvaluator` class
4. Create database schema (`post_research` table)
5. Create research topic configuration system

### Phase 2: Research Execution
1. Implement `FactExtractor` class
2. Implement `ContentSynthesizer` class
3. Create research API endpoints
4. Implement sequential research execution
5. Add error handling and retry logic

### Phase 3: UI Development
1. Create research page template
2. Build research topic card components
3. Implement status indicators and progress tracking
4. Add source display with reliability indicators
5. Create content review/editing interface

### Phase 4: Workflow Integration
1. Add research stage to recipe workflow config
2. Create research route and view function
3. Update navigation to include research stage
4. Integrate research content into drafting stage
5. Update documentation

### Phase 5: Testing & Refinement
1. Test with multiple recipes
2. Refine search queries and prompts
3. Improve source prioritization
4. Optimize fact extraction accuracy
5. User testing and feedback

---

## Technical Considerations

### 1. LLM Usage

- **Search Query Generation**: Use LLM to refine search queries
- **Fact Extraction**: Use structured prompts to extract facts as JSON
- **Content Synthesis**: Use narrative generation prompts (similar to family research)
- **Model Selection**: Use `llama3.2:latest` for consistency with existing system

### 2. Rate Limiting & Performance

- **Sequential Execution**: Research topics one at a time (prevents API overload)
- **Caching**: Cache research results to avoid re-running
- **Timeout Handling**: Set timeouts for web requests (15-30 seconds)
- **Progress Tracking**: Real-time status updates via WebSocket or polling

### 3. Error Handling

- **Source Fetching Failures**: Continue with other sources
- **LLM Failures**: Retry with exponential backoff
- **Partial Results**: Allow research to complete with partial data
- **User Notification**: Clear error messages and recovery options

### 4. Source Quality Assurance

- **Domain Verification**: Check domain against whitelist of reliable domains
- **Content Validation**: Verify content is relevant and factual
- **Duplicate Detection**: Avoid using same source multiple times
- **Citation Format**: Standardized citation format for sources

---

## Example Research Flow

### For "Forfar Bridie" Recipe

**Topic 1: Origins & Early History**
1. Query: "earliest mentions and recorded origins of Forfar Bridie in Scotland"
2. Sources found:
   - National Museums Scotland (museum domain)
   - Historic Environment Scotland (gov domain)
   - University of St Andrews food history archive (edu domain)
3. Facts extracted:
   - First documented: 1851 in Forfar
   - Created by: Local bakers
   - Original purpose: Portable meal for farm workers
4. Synthesized paragraph:
   "The Forfar Bridie first appears in historical records in 1851, created by local bakers in the town of Forfar, Angus. Originally designed as a portable meal for farm workers, this savory pastry quickly became a regional specialty..."

**Topic 2: Geographic Spread & Regional Variations**
1. Query: "geographic distribution and regional variations of Forfar Bridie across Scotland"
2. Sources found:
   - VisitScotland heritage pages
   - Regional food history sites
3. Facts extracted:
   - Primarily associated with Angus region
   - Variations in other regions use different names
   - Still most popular in Forfar area
4. Synthesized paragraph:
   "While the Forfar Bridie is most closely associated with the Angus region, particularly the town of Forfar itself, similar pastries exist across Scotland under different names..."

*(Continue for all 5 topics)*

---

## Extensibility Design

### Adding Research to Other Post Types

1. **Define Research Topics** in `config/research_topics.py`
2. **Add Research Stage** to post type workflow in `config/post_type_substages.py`
3. **Create Post-Type-Specific Prompts** (if needed)
4. **UI Automatically Adapts** (uses same research page template)

### Example: Themed Posts Research Topics

```python
'themed': {
    'topics': [
        {
            'key': 'historical_context',
            'label': 'Historical Context',
            'search_template': 'historical context and background of {theme_title} in Scotland',
            ...
        },
        {
            'key': 'cultural_significance',
            'label': 'Cultural Significance',
            'search_template': 'cultural significance of {theme_title} in Scottish culture',
            ...
        }
    ]
}
```

---

## Next Steps

1. **Review & Approve Design**: Review this plan and approve approach
2. **Database Migration**: Create `post_research` table migration
3. **Core Module Development**: Build `utils/research_agents/` infrastructure
4. **API Development**: Create research API endpoints
5. **UI Development**: Build research page interface
6. **Workflow Integration**: Add research stage to recipe workflow
7. **Testing**: Test with sample recipes
8. **Documentation**: Update workflow documentation

---

## Questions for Discussion

1. **Research Completeness**: Should all topics be required, or can users skip some?
2. **Auto-Integration**: Should research auto-populate background section, or require manual review?
3. **Source Citations**: How detailed should source citations be in final content?
4. **Research Timing**: Should research be done automatically when post is created, or manually triggered?
5. **Content Editing**: Should synthesized content be editable before integration, or locked?
