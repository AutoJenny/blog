# Phase 3 — Angles: Implementation Design Brief

**Date:** 2026-01-25  
**Status:** ✅ **DESIGN PHASE** (no coding yet)  
**Audience:** Engineering (lead + implementers)  
**Purpose:** Complete, reviewable implementation design for the Angles layer, strictly aligned with `docs/ANGLES_LAYER_FINAL_SPECIFICATION.md`

---

## Design Principles

**Strict Alignment:**
- All design decisions must preserve the hierarchy: `TOPIC → ANGLE → ROLE → CHANNEL → OUTPUT`
- Angles are persistent, reusable, topic-bound (not week-bound)
- Human-in-the-loop required (no auto-selection)
- Backward compatible (existing posts work without angles)
- Scope locked to Sunday Deep Dive (Facebook) only

**Key Constraints:**
- No changes to existing systems (topics, themes, roles, posting_queue structure)
- Angle logic must be additive, not replacement
- UI must remain clean and scannable (angle intelligence one interaction deeper)

---

## 1. Data Model Design

### 1.1 `content_angles` Table Schema

**Purpose:** Store persistent, reusable editorial interpretations of topics.

**Proposed Schema:**
```sql
CREATE TABLE content_angles (
    id SERIAL PRIMARY KEY,
    
    -- Core Identity
    angle_name TEXT NOT NULL,  -- "What 'official tartan' really means (and why it's often modern)"
    angle_description TEXT,    -- Optional: Extended description of the angle
    
    -- Narrative Intent (Editorial Layer)
    narrative_intent TEXT NOT NULL,  -- What story this angle tells (editorial interpretation)
    
    -- Topic Relationship (Many-to-One)
    topic_id INTEGER NOT NULL REFERENCES kb_topics(id) ON DELETE RESTRICT,
    
    -- Source Bundle (KB Articles)
    source_article_ids INTEGER[] NOT NULL DEFAULT '{}',  -- KB articles in bundle
    source_chunk_ids INTEGER[],  -- Optional: Specific chunks (for future precision)
    
    -- Reuse Tracking (Logical, Not DB-Enforced)
    is_active BOOLEAN DEFAULT TRUE,  -- Can be deactivated without deletion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),  -- Optional: Track who created (for audit)
    
    -- Optional Metadata (Future Extensibility)
    recommended_roles TEXT[],  -- ['DEPTH_LONG', 'AUTHORITY_SHORT'] (suggestions only)
    suggested_channels TEXT[],  -- ['facebook', 'x'] (suggestions only)
    notes TEXT,  -- Manual editorial notes
    
    -- Lifecycle Flags
    usage_count INTEGER DEFAULT 0,  -- Track how many times used (for reuse visibility)
    last_used_at TIMESTAMP,  -- Last time this angle was used for generation
    last_used_year INTEGER,  -- Year of last use (for reuse tracking)
    last_used_week INTEGER   -- ISO week of last use (for reuse tracking)
);
```

**Indexes:**
```sql
CREATE INDEX idx_content_angles_topic_id ON content_angles(topic_id);
CREATE INDEX idx_content_angles_active ON content_angles(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_content_angles_source_articles ON content_angles USING GIN(source_article_ids);
CREATE INDEX idx_content_angles_last_used ON content_angles(last_used_year, last_used_week);
```

**Comments:**
```sql
COMMENT ON TABLE content_angles IS 'Reusable editorial interpretations of topics. Angles are topic-bound, not week-bound, and can be reused across roles and channels.';
COMMENT ON COLUMN content_angles.angle_name IS 'Human-readable angle name (e.g., "What official tartan really means")';
COMMENT ON COLUMN content_angles.narrative_intent IS 'Editorial interpretation: what story this angle tells about the topic';
COMMENT ON COLUMN content_angles.topic_id IS 'FK to kb_topics - each angle belongs to one topic, topics can have multiple angles';
COMMENT ON COLUMN content_angles.source_article_ids IS 'Array of KB article IDs that form the source bundle for this angle';
COMMENT ON COLUMN content_angles.is_active IS 'Can be deactivated without deletion (soft delete)';
COMMENT ON COLUMN content_angles.usage_count IS 'Track reuse frequency (for visibility, not enforcement)';
COMMENT ON COLUMN content_angles.last_used_year IS 'Year of last use (for reuse tracking across weeks)';
COMMENT ON COLUMN content_angles.last_used_week IS 'ISO week of last use (for reuse tracking)';
```

### 1.2 Relationship to `kb_topics`

**Relationship:** Many-to-One (Multiple Angles per Topic)

**Foreign Key:**
- `content_angles.topic_id` → `kb_topics.id`
- `ON DELETE RESTRICT` - Prevents deleting topics that have angles

**Query Pattern:**
```sql
-- Get all angles for a topic
SELECT * FROM content_angles WHERE topic_id = ? AND is_active = TRUE;

-- Get topic with its angles
SELECT t.*, 
       array_agg(a.id) as angle_ids,
       array_agg(a.angle_name) as angle_names
FROM kb_topics t
LEFT JOIN content_angles a ON t.id = a.topic_id AND a.is_active = TRUE
WHERE t.id = ?
GROUP BY t.id;
```

**Rationale:**
- Topics remain factual/semantic (unchanged)
- Angles add editorial layer on top
- One topic can have multiple angles (different storylines)
- Clear separation of concerns

### 1.3 Relationship to `posting_queue`

**Relationship:** Optional Reference (Backward Compatible)

**Proposed Extension:**
```sql
-- Add nullable angle_id column to posting_queue
ALTER TABLE posting_queue 
ADD COLUMN angle_id INTEGER REFERENCES content_angles(id) ON DELETE SET NULL;
```

**Index:**
```sql
CREATE INDEX idx_posting_queue_angle_id ON posting_queue(angle_id) WHERE angle_id IS NOT NULL;
```

**Rationale:**
- **Nullable** - Existing posts have `angle_id = NULL` (backward compatible)
- **Optional** - Posts can be generated without angles (fallback to topic-only)
- **Reference** - Links generated output to the angle that informed it
- **ON DELETE SET NULL** - If angle is deleted, posts remain (orphaned but valid)

**Query Pattern:**
```sql
-- Get post with angle info
SELECT pq.*, 
       a.angle_name,
       a.narrative_intent,
       a.topic_id
FROM posting_queue pq
LEFT JOIN content_angles a ON pq.angle_id = a.id
WHERE pq.id = ?;

-- Get all posts using a specific angle
SELECT * FROM posting_queue WHERE angle_id = ?;
```

### 1.4 Reuse Tracking (Logical, Not DB-Enforced)

**Fields:**
- `usage_count` - Incremented each time angle is used
- `last_used_at` - Timestamp of last use
- `last_used_year` - Year of last use
- `last_used_week` - ISO week of last use

**Purpose:**
- **Visibility** - Show when angle was last used (not enforcement)
- **Reuse Awareness** - Help editors avoid accidental repetition
- **No Hard Constraints** - System does not prevent reuse (editorial decision)

**Update Logic (Application-Level):**
```python
# When angle is selected for generation:
UPDATE content_angles 
SET usage_count = usage_count + 1,
    last_used_at = CURRENT_TIMESTAMP,
    last_used_year = ?,
    last_used_week = ?
WHERE id = ?;
```

**Rationale:**
- Tracking is informational, not restrictive
- Editors can see reuse history but are not blocked
- Supports "deliberate reuse" requirement from spec

### 1.5 Lifecycle Flags

**`is_active` (Boolean):**
- `TRUE` - Angle is available for selection
- `FALSE` - Angle is deactivated (soft delete)
- **Rationale:** Preserve history, allow reactivation, no hard deletes

**No Hard Constraints:**
- No UNIQUE constraints on angle_name (multiple angles can have similar names)
- No CHECK constraints on usage_count (no limits)
- No triggers preventing reuse
- **Rationale:** Spec explicitly excludes "hard database constraints" for Phase 3

### 1.6 Backward Compatibility

**Existing Posts:**
- All existing `posting_queue` rows have `angle_id = NULL`
- Generation logic must handle `angle_id IS NULL` gracefully
- **Fallback:** If no angle, use topic-only generation (current behavior)

**Existing Systems:**
- No changes to `kb_topics` table
- No changes to `content_roles` table
- No changes to `calendar_themes` table
- **Rationale:** Angles are additive layer, not replacement

---

## 2. API Design

### 2.1 Base URL

**Blueprint:** `blueprints/content_angles_api.py`  
**URL Prefix:** `/api/content-angles`

### 2.2 Endpoint: Propose Angle Candidates

**Route:** `POST /api/content-angles/propose`

**Purpose:** Generate multiple angle candidates for a topic (read-only, no persistence).

**Request:**
```json
{
  "topic_id": 277,
  "num_candidates": 5,  // Optional, default: 5
  "context": {  // Optional: Additional context
    "rota_year": 2026,
    "rota_week": 5
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "topic_id": 277,
  "topic_name": "Tartan Design Principles",
  "candidates": [
    {
      "angle_name": "What 'official tartan' really means (and why it's often modern)",
      "narrative_intent": "Explains that 'official' tartans are often modern creations, not ancient designs. Demystifies the concept of official registration.",
      "source_article_ids": [640, 329],
      "confidence_score": 0.85,  // Optional: LLM confidence
      "reasoning": "Topic articles discuss tartan registration and modern design practices"
    },
    {
      "angle_name": "How people without a known clan can choose a tartan responsibly",
      "narrative_intent": "Provides guidance for choosing tartans when clan heritage is unknown. Emphasizes personal connection over strict rules.",
      "source_article_ids": [641, 350],
      "confidence_score": 0.78
    }
    // ... more candidates
  ]
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Topic not found",
  "error_code": "TOPIC_NOT_FOUND"
}
```

**Error Conditions:**
- `TOPIC_NOT_FOUND` - Topic ID does not exist
- `TOPIC_INACTIVE` - Topic exists but is inactive
- `NO_SOURCE_ARTICLES` - Topic has no associated KB articles
- `GENERATION_FAILED` - LLM failed to generate candidates

**Implementation Notes:**
- Uses vector search on topic articles to propose relevant sources
- Calls LLM to generate angle names and narrative intent
- Returns candidates only (does not persist)
- Human must explicitly select/confirm before persistence

**Permissions:**
- No authentication required (Phase 3 scope)
- All users can propose angles (editorial control is in selection step)

### 2.3 Endpoint: Create/Update Angle

**Route:** `POST /api/content-angles/angle`

**Purpose:** Persist a selected or edited angle.

**Request:**
```json
{
  "angle_id": null,  // null = create new, integer = update existing
  "angle_name": "What 'official tartan' really means (and why it's often modern)",
  "narrative_intent": "Explains that 'official' tartans are often modern creations...",
  "topic_id": 277,
  "source_article_ids": [640, 329],
  "source_chunk_ids": null,  // Optional
  "notes": "Good angle for demystifying tartan registration"
}
```

**Response (Success - Create):**
```json
{
  "success": true,
  "angle": {
    "id": 42,
    "angle_name": "What 'official tartan' really means...",
    "narrative_intent": "...",
    "topic_id": 277,
    "source_article_ids": [640, 329],
    "is_active": true,
    "created_at": "2026-01-25T10:30:00Z",
    "usage_count": 0
  }
}
```

**Response (Success - Update):**
```json
{
  "success": true,
  "angle": {
    "id": 42,
    "angle_name": "Updated angle name",
    "narrative_intent": "Updated narrative...",
    "updated_at": "2026-01-25T11:00:00Z"
  }
}
```

**Error Conditions:**
- `TOPIC_NOT_FOUND` - Topic ID does not exist
- `INVALID_SOURCE_ARTICLES` - Source article IDs do not exist
- `VALIDATION_FAILED` - Required fields missing
- `ANGLE_NOT_FOUND` - Update requested but angle_id does not exist

**Validation Rules:**
- `angle_name` - Required, non-empty
- `narrative_intent` - Required, non-empty
- `topic_id` - Required, must exist in `kb_topics`
- `source_article_ids` - Required, non-empty array, all IDs must exist

**Permissions:**
- No authentication required (Phase 3 scope)
- All users can create/edit angles

### 2.4 Endpoint: Get Angle by ID

**Route:** `GET /api/content-angles/angle/<angle_id>`

**Purpose:** Retrieve a specific angle with full details.

**Response:**
```json
{
  "success": true,
  "angle": {
    "id": 42,
    "angle_name": "What 'official tartan' really means...",
    "angle_description": null,
    "narrative_intent": "Explains that 'official' tartans...",
    "topic_id": 277,
    "topic_name": "Tartan Design Principles",
    "source_article_ids": [640, 329],
    "source_chunk_ids": null,
    "is_active": true,
    "usage_count": 2,
    "last_used_at": "2026-01-20T15:00:00Z",
    "last_used_year": 2026,
    "last_used_week": 3,
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-01-20T15:00:00Z",
    "notes": "Good angle for demystifying tartan registration"
  }
}
```

**Error Conditions:**
- `ANGLE_NOT_FOUND` - Angle ID does not exist

### 2.5 Endpoint: Get Angles by Topic

**Route:** `GET /api/content-angles/topic/<topic_id>`

**Query Parameters:**
- `include_inactive` (boolean, default: false) - Include deactivated angles

**Purpose:** Retrieve all angles for a topic.

**Response:**
```json
{
  "success": true,
  "topic_id": 277,
  "topic_name": "Tartan Design Principles",
  "angles": [
    {
      "id": 42,
      "angle_name": "What 'official tartan' really means...",
      "narrative_intent": "...",
      "is_active": true,
      "usage_count": 2,
      "last_used_week": 3
    },
    {
      "id": 43,
      "angle_name": "How people without a known clan can choose...",
      "narrative_intent": "...",
      "is_active": true,
      "usage_count": 0,
      "last_used_week": null
    }
  ]
}
```

**Error Conditions:**
- `TOPIC_NOT_FOUND` - Topic ID does not exist

### 2.6 Endpoint: Get Angles by Usage

**Route:** `GET /api/content-angles/usage`

**Query Parameters:**
- `year` (integer, optional) - Filter by last used year
- `week` (integer, optional) - Filter by last used week
- `min_usage_count` (integer, optional) - Minimum usage count
- `topic_id` (integer, optional) - Filter by topic

**Purpose:** Retrieve angles filtered by usage history (for reuse visibility).

**Response:**
```json
{
  "success": true,
  "filters": {
    "year": 2026,
    "week": 3
  },
  "angles": [
    {
      "id": 42,
      "angle_name": "...",
      "topic_id": 277,
      "topic_name": "Tartan Design Principles",
      "usage_count": 2,
      "last_used_year": 2026,
      "last_used_week": 3
    }
  ]
}
```

**Use Case:** Show "recently used angles" to help editors avoid accidental repetition.

### 2.7 Error Response Format

**Standard Error Response:**
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {}  // Optional: Additional error context
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found (topic/angle not found)
- `500` - Internal Server Error

---

## 3. UI Flow Design

### 3.1 KB Topic Rota Editor Integration

**Current Flow (Without Angles):**
1. User opens Sunday slot panel
2. Selects week (year/week)
3. Selects topic from dropdown
4. Selects source article from dropdown (populated from topic articles)
5. Clicks "Generate" → Calls `/api/content-roles/facebook/sunday/generate`
6. Reviews generated content
7. Approves and schedules

**New Flow (With Angles - Phase 3):**

**Step 1: Topic Selection (Unchanged)**
- User selects topic from dropdown
- System loads topic articles (existing behavior)

**Step 2: Angle Proposal (NEW)**
- After topic selection, show "Propose Angles" button
- Button appears below topic selector, before source selector
- Clicking button calls `POST /api/content-angles/propose` with `topic_id`
- Shows loading state: "Generating angle candidates..."

**Step 3: Angle Selection Modal (NEW)**
- Modal appears with 3-5 angle candidates
- Each candidate shows:
  - Angle name (prominent)
  - Narrative intent (1-2 sentences)
  - Source articles count (e.g., "2 articles")
  - "Select" button
- Additional options:
  - "Edit" button (allows editing before selection)
  - "Create New" button (allows manual angle creation)
- Modal has "Cancel" button (returns to topic selection)

**Step 4: Angle Confirmation (NEW)**
- After selection, selected angle is displayed in slot panel
- Shows: "Selected Angle: [angle name]" (read-only display)
- "Change Angle" button (reopens selection modal)
- Source article selector is now **pre-populated** with angle's source articles
- User can still modify source selection (but defaults to angle's sources)

**Step 5: Generation (Modified)**
- "Generate" button now includes `angle_id` in request
- Calls `POST /api/content-roles/facebook/sunday/generate` with:
  - `topic_id` (existing)
  - `source_page_id` (existing, but can be from angle's sources)
  - `angle_id` (NEW)
- Generation uses angle's narrative intent + sources

**Step 6: Review & Schedule (Unchanged)**
- Review generated content
- Approve and schedule
- Angle usage tracking updated automatically

**UI Components Required:**
1. **"Propose Angles" button** - In Sunday slot panel, below topic selector
2. **Angle selection modal** - New modal component
3. **Selected angle display** - Read-only display in slot panel
4. **"Change Angle" button** - Reopens selection modal

**Preservation of Clean UI:**
- Angle logic is **one interaction deeper** (modal, not always visible)
- Main slot panel remains clean (angle shown only after selection)
- No angle information in main rota grid (keeps it scannable)

### 3.2 Content Control Board Integration

**Current Flow (Without Angles):**
1. User views weekly matrix (Days × Channels)
2. Clicks Sunday Facebook cell
3. Drill-down panel opens showing:
   - Role badge (DEPTH_LONG)
   - Topic information
   - Post status
   - Generated content preview
   - Action buttons

**New Flow (With Angles - Phase 3):**

**Drill-Down Panel Enhancement:**
- If post exists and has `angle_id`:
  - Show "Angle" section above "Topic" section
  - Display: "Angle: [angle name]"
  - Display: "[narrative intent]" (1-2 sentences, collapsible)
  - Show reuse info: "Used 2 times, last used Week 3"
- If post exists but has no `angle_id`:
  - Show "Angle: Not selected" (informational only)
  - No action required (backward compatible)
- If slot is empty:
  - No angle information shown (angle selection happens in Rota Editor)

**No Angle Selection in Control Board (Phase 3):**
- Control Board remains **read-only** for angles
- Angle selection happens in KB Topic Rota Editor only
- Control Board shows angle information for visibility only

**Preservation of Clean Matrix:**
- Matrix cells remain unchanged (no angle badges)
- Angle information only in drill-down panel
- No new buttons or actions in matrix view

### 3.3 UI Flow Diagrams

**KB Topic Rota Editor - Angle Selection Flow:**

```
┌─────────────────────────────────────┐
│  Sunday Slot Panel                  │
├─────────────────────────────────────┤
│  [Week Selector]                     │
│  [Topic Selector] ← User selects     │
│  [Propose Angles] ← NEW button       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Angle Selection Modal       │   │
│  │ (Opens when button clicked)  │   │
│  ├─────────────────────────────┤   │
│  │ Candidate 1: [Select]        │   │
│  │ Candidate 2: [Select]        │   │
│  │ Candidate 3: [Select]        │   │
│  │ [Edit] [Create New] [Cancel] │   │
│  └─────────────────────────────┘   │
│                                     │
│  Selected Angle: [angle name]      │
│  [Change Angle]                     │
│  [Source Article Selector]           │
│  [Generate]                         │
└─────────────────────────────────────┘
```

**Content Control Board - Drill-Down Panel:**

```
┌─────────────────────────────────────┐
│  Post Details Panel                 │
├─────────────────────────────────────┤
│  Role: DEPTH_LONG                   │
│  Channel: Facebook                  │
│  Day: Sunday 15:00                  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Angle: [angle name]         │   │
│  │ [narrative intent]          │   │
│  │ Used 2x, last: Week 3       │   │
│  └─────────────────────────────┘   │
│                                     │
│  Topic: [topic name]                │
│  Source: [article name]             │
│  Status: [status badge]             │
│  [Generated content preview]        │
└─────────────────────────────────────┘
```

### 3.4 Step-by-Step User Journey

**Scenario: User wants to generate Sunday Deep Dive with angle**

1. **Navigate to KB Topic Rota Editor**
   - URL: `/kb-topics/editor`
   - Click "Sunday Slot" button

2. **Select Week**
   - Enter year/week or use "Load Week"
   - System loads week data

3. **Select Topic**
   - Choose topic from dropdown
   - System loads topic articles

4. **Propose Angles** (NEW)
   - Click "Propose Angles" button
   - System calls API, shows loading
   - Modal appears with 3-5 candidates

5. **Review Candidates**
   - Read angle names and narrative intents
   - Consider source articles for each

6. **Select Angle**
   - Click "Select" on preferred candidate
   - OR click "Edit" to modify before selecting
   - OR click "Create New" for manual angle

7. **Confirm Selection**
   - Selected angle displayed in panel
   - Source articles pre-populated
   - Can modify source selection if needed

8. **Generate Post**
   - Click "Generate" button
   - System uses angle + topic + source
   - Generated content appears

9. **Review & Approve**
   - Review generated content
   - Approve if satisfied
   - Schedule for Sunday 15:00

**Key Points:**
- Angle selection is **explicit** (human-in-the-loop)
- Angle is **visible** once selected
- Source articles are **pre-populated** but **editable**
- No automatic angle reuse (editorial decision)

---

## 4. Generation Pipeline Integration

### 4.1 Current DEPTH_LONG Generation Flow

**Current Implementation (`utils/content_roles/depth_long_generator.py`):**

```
Input: topic_id, source_page_id, rota_year, rota_week
  ↓
1. Fetch source text from KB article (source_page_id)
  ↓
2. Get topic metadata (topic_id)
  ↓
3. Call LLM with:
   - Global system prompt (role separation)
   - Role system prompt (DEPTH_LONG constraints)
   - Source text
   - Task instruction (topic name)
  ↓
4. Return generated content
```

**Current Prompt Structure:**
- Global prompt: Role separation rule
- Role prompt: DEPTH_LONG constraints (120-220 words, no selling, etc.)
- Task instruction: Topic name + source text

### 4.2 Angle-Aware Generation Flow (Proposed)

**Modified Implementation:**

```
Input: topic_id, source_page_id, angle_id (optional), rota_year, rota_week
  ↓
1. Get topic metadata (topic_id)
  ↓
2. IF angle_id provided:
    2a. Load angle (narrative_intent, source_article_ids)
    2b. Use angle's source articles (or allow override with source_page_id)
    2c. Fetch source text from angle's articles (aggregated)
   ELSE:
    2d. Fallback to current behavior (single source_page_id)
  ↓
3. Call LLM with:
   - Global system prompt (role separation)
   - Role system prompt (DEPTH_LONG constraints)
   - Angle prompt (NEW - if angle_id provided):
     * Narrative intent
     * Storyline guidance
   - Source text (from angle bundle OR single article)
   - Task instruction (topic name + angle context)
  ↓
4. Return generated content
```

### 4.3 Prompt Composition (Design Only)

**Without Angle (Fallback):**
```
[Global System Prompt]
[Role System Prompt: DEPTH_LONG]
[Task Instruction: Write about {topic_name} using source material]
[Source Text]
```

**With Angle (New):**
```
[Global System Prompt]
[Role System Prompt: DEPTH_LONG]
[Angle Prompt: NEW]
  - Narrative intent: {angle.narrative_intent}
  - Storyline: {angle.angle_name}
  - Context: This post should tell the story: "{angle.narrative_intent}"
[Task Instruction: Write about {topic_name} from the angle: {angle.angle_name}]
[Source Text: Aggregated from angle's source_article_ids]
```

**Angle Prompt Structure (Conceptual):**
```
You are writing a Facebook post that tells a specific story about this topic.

The story you are telling is: {angle.narrative_intent}

This means:
- Focus on: {angle.angle_name}
- Tell the story: {angle.narrative_intent}
- Use the source material to support this narrative

The role constraints (DEPTH_LONG) still apply:
- 120-220 words
- No selling, no service mentions
- Explanatory, not summarising
- Reflective close

Combine the narrative intent with the role constraints to write the post.
```

**Rationale:**
- Angle prompt is **additive** (composes with role prompt)
- Role prompt remains **authoritative** for constraints
- Angle prompt provides **narrative direction**
- Source text comes from **angle's bundle** (not single article)

### 4.4 Source Text Aggregation (With Angle)

**Current:** Single article text (bounded to 2000 words)

**With Angle:** Aggregated text from multiple articles

**Implementation:**
- Use existing `TopicContentAggregator` logic
- Filter to angle's `source_article_ids`
- Aggregate chunks, rank by relevance
- Combine with clear separators
- Bound to ~2000 words total

**Fallback:**
- If angle has no source articles, fall back to `source_page_id`
- If aggregation fails, use single article

### 4.5 Generation API Modification

**Current Endpoint:** `POST /api/content-roles/facebook/sunday/generate`

**Current Request:**
```json
{
  "topic_id": 277,
  "source_page_id": 640,
  "rota_year": 2026,
  "rota_week": 5
}
```

**Modified Request (Backward Compatible):**
```json
{
  "topic_id": 277,
  "source_page_id": 640,  // Optional if angle_id provided
  "angle_id": 42,  // NEW: Optional
  "rota_year": 2026,
  "rota_week": 5
}
```

**Logic:**
```python
if angle_id:
    # Use angle-aware generation
    angle = get_angle(angle_id)
    source_text = aggregate_angle_sources(angle)
    narrative_intent = angle.narrative_intent
else:
    # Fallback to current behavior
    source_text = fetch_single_article(source_page_id)
    narrative_intent = None
```

**Response (Unchanged):**
- Same response format
- Generated content
- Validation results
- Word count, etc.

### 4.6 Usage Tracking Update

**When angle is used for generation:**
```python
# After successful generation, update angle usage
UPDATE content_angles 
SET usage_count = usage_count + 1,
    last_used_at = CURRENT_TIMESTAMP,
    last_used_year = rota_year,
    last_used_week = rota_week
WHERE id = angle_id;
```

**When post is stored:**
```python
# Store post with angle reference
INSERT INTO posting_queue (
    role, topic_id, source_page_id, angle_id,  # NEW: angle_id
    rota_year, rota_week, ...
) VALUES (...);
```

### 4.7 Fallback Behavior

**Scenario 1: No angle_id provided**
- Use current generation logic (single article)
- Post stored with `angle_id = NULL`
- **Rationale:** Backward compatible, existing workflow continues

**Scenario 2: angle_id provided but angle not found**
- Return error: "Angle not found"
- Do not fall back to topic-only
- **Rationale:** Explicit angle selection should be valid

**Scenario 3: angle_id provided but angle has no source articles**
- Fall back to `source_page_id` if provided
- OR return error: "Angle has no source articles"
- **Rationale:** Angle should have valid source bundle

**Scenario 4: angle_id provided but aggregation fails**
- Fall back to first article in angle's `source_article_ids`
- OR return error
- **Rationale:** Graceful degradation

---

## 5. Rollout & Dependency Order

### 5.1 Build Order (Sequential Dependencies)

**Phase 3.1: Database Foundation**
1. Create `content_angles` table migration
2. Add `angle_id` column to `posting_queue` (nullable)
3. Create indexes
4. Run migrations
5. **Test:** Verify tables exist, columns nullable

**Phase 3.2: Angle Proposal System**
1. Create `utils/content_angles/angle_proposer.py`
   - Vector search on topic articles
   - LLM call to generate candidates
   - Similarity checking (avoid duplicates)
2. Create API endpoint: `POST /api/content-angles/propose`
3. **Test:** Can propose angles for a topic

**Phase 3.3: Angle Persistence**
1. Create API endpoints:
   - `POST /api/content-angles/angle` (create/update)
   - `GET /api/content-angles/angle/<id>`
   - `GET /api/content-angles/topic/<topic_id>`
   - `GET /api/content-angles/usage`
2. **Test:** Can create, read, update angles

**Phase 3.4: UI - Angle Selection**
1. Add "Propose Angles" button to Sunday slot panel
2. Create angle selection modal component
3. Integrate with Sunday slot manager
4. **Test:** Can propose and select angles in UI

**Phase 3.5: Generation Integration**
1. Modify `DepthLongGenerator` to accept `angle_id`
2. Add angle prompt composition logic
3. Add source aggregation for angles
4. Modify generation API to accept `angle_id`
5. Update usage tracking
6. **Test:** Can generate posts with angles

**Phase 3.6: Control Board Display**
1. Modify drill-down panel to show angle info
2. Add angle display when `angle_id` exists
3. **Test:** Angle visible in Control Board

**Phase 3.7: Integration Testing**
1. End-to-end test: Topic → Angle → Generation → Post
2. Test fallback: Generation without angle
3. Test reuse: Same angle across weeks
4. **Test:** Complete workflow functions

### 5.2 Test Order

**Unit Tests:**
1. Angle proposer (vector search, LLM calls)
2. Angle CRUD operations
3. Angle-aware generator (prompt composition)
4. Source aggregation logic

**Integration Tests:**
1. API endpoints (propose, create, retrieve)
2. Generation with angle
3. Generation without angle (fallback)
4. Usage tracking updates

**UI Tests:**
1. Angle selection modal
2. Selected angle display
3. Generation with selected angle
4. Control Board angle display

**End-to-End Tests:**
1. Complete flow: Topic → Propose → Select → Generate → Approve → Schedule
2. Reuse flow: Select existing angle → Generate
3. Fallback flow: Generate without angle (current behavior)

### 5.3 Feature Flags (If Any)

**Proposed Flag:** `ENABLE_ANGLES` (environment variable)

**Default:** `False` (angles disabled)

**When Enabled:**
- Angle proposal button appears
- Angle selection modal available
- Angle-aware generation active
- Angle display in Control Board

**When Disabled:**
- No angle UI elements
- Generation uses current logic (topic-only)
- Backward compatible behavior

**Rationale:**
- Allows gradual rollout
- Can disable if issues arise
- No breaking changes when disabled

### 5.4 Coexistence with Current Sunday Workflow

**Current Sunday Workflow (Without Angles):**
- User selects topic
- User selects source article
- Generates post
- Approves and schedules

**New Sunday Workflow (With Angles - Optional):**
- User selects topic
- **User can optionally propose/select angle** (NEW)
- User selects source article (pre-populated if angle selected)
- Generates post (angle-aware if angle selected)
- Approves and schedules

**Coexistence Strategy:**
- **Backward Compatible:** Existing workflow continues to work
- **Optional Enhancement:** Angle selection is optional step
- **No Breaking Changes:** Posts without angles work identically
- **Gradual Adoption:** Users can adopt angles incrementally

**Migration Path:**
1. Deploy Phase 3 with feature flag OFF
2. Test angle functionality internally
3. Enable feature flag for testing
4. Monitor usage, gather feedback
5. Full rollout when stable

**Rollback Plan:**
- Disable feature flag
- Existing posts continue to work (angle_id nullable)
- No data loss (angles remain in database)
- Can re-enable when ready

---

## 6. Open Questions

### 6.1 Resolved Questions

**Q: Should angles be week-bound or topic-bound?**  
**A:** Topic-bound (locked in spec). Angles can be reused across weeks.

**Q: Should angle selection be mandatory?**  
**A:** No (locked in spec). Angles are optional enhancement. Fallback to topic-only.

**Q: Should angles have hard database constraints?**  
**A:** No (locked in spec). Phase 3 excludes hard constraints. Tracking is informational.

**Q: Should angles be visible in main matrix?**  
**A:** No (locked in spec). Angle intelligence belongs one interaction deeper.

### 6.2 Remaining Questions (If Any)

**Q1: Angle Name Uniqueness**
- **Question:** Should angle names be unique per topic, or globally unique, or not unique at all?
- **Current Design:** No UNIQUE constraint (multiple angles can have similar names)
- **Rationale:** Spec excludes hard constraints. Editorial decision if names are too similar.
- **Recommendation:** No uniqueness constraint. Rely on human review.

**Q2: Source Article Validation**
- **Question:** Should we validate that angle's `source_article_ids` actually belong to the topic's `article_ids`?
- **Current Design:** No validation (angle can reference any KB articles)
- **Rationale:** Flexibility allows cross-topic angles if needed
- **Recommendation:** No validation. Trust editorial judgment.

**Q3: Angle Deletion**
- **Question:** What happens to posts that reference a deleted angle?
- **Current Design:** `ON DELETE SET NULL` - Posts become orphaned but remain valid
- **Rationale:** Preserve post history, allow angle deletion
- **Recommendation:** Keep current design. Orphaned posts show "Angle: [deleted]" in UI.

**Q4: Angle Editing After Use**
- **Question:** Can angles be edited after they've been used for generation?
- **Current Design:** Yes, angles can be updated at any time
- **Rationale:** Editorial refinement is allowed
- **Recommendation:** Keep current design. Track `updated_at` for audit.

**Q5: Maximum Candidates**
- **Question:** How many angle candidates should be proposed?
- **Current Design:** Default 5, configurable
- **Rationale:** Balance between options and cognitive load
- **Recommendation:** Start with 5, adjust based on feedback.

**Q6: Angle Proposal Performance**
- **Question:** How long should angle proposal take? What if LLM is slow?
- **Current Design:** Async not required for Phase 3 (synchronous)
- **Rationale:** Keep Phase 3 simple
- **Recommendation:** Show loading state, timeout after 30 seconds, show error if fails.

### 6.3 Design Decisions Made

**Decision 1: Angle Name Not Unique**
- **Rationale:** Spec excludes hard constraints
- **Impact:** Multiple angles can have similar names (editorial review needed)

**Decision 2: Source Articles Not Validated**
- **Rationale:** Flexibility for cross-topic angles
- **Impact:** Angles can reference articles outside topic (trust editorial judgment)

**Decision 3: Angle Deletion Sets NULL**
- **Rationale:** Preserve post history
- **Impact:** Orphaned posts remain valid (show "Angle: [deleted]")

**Decision 4: Angles Can Be Edited Anytime**
- **Rationale:** Allow editorial refinement
- **Impact:** Historical posts may reference old angle version (track `updated_at`)

**Decision 5: Default 5 Candidates**
- **Rationale:** Balance options vs. cognitive load
- **Impact:** Can be adjusted based on feedback

**Decision 6: Synchronous Proposal**
- **Rationale:** Keep Phase 3 simple
- **Impact:** UI must show loading state, handle timeouts

---

## 7. Design Validation

### 7.1 Alignment Check

**✅ Hierarchy Preserved:**
- `TOPIC → ANGLE → ROLE → CHANNEL → OUTPUT` maintained in data model and flow

**✅ Persistence Rules:**
- Angles are persistent objects (stored in `content_angles` table)
- Topic-bound (not week-bound) via `topic_id` FK
- Reusable across weeks (tracked but not restricted)

**✅ Human-in-the-Loop:**
- Angle proposal is read-only (no auto-selection)
- Explicit selection required (modal with "Select" button)
- No automatic reuse (editorial decision)

**✅ Backward Compatibility:**
- `angle_id` is nullable in `posting_queue`
- Generation falls back to topic-only if no angle
- Existing posts work unchanged

**✅ Scope Lock:**
- Sunday Deep Dive (Facebook) only
- No multi-channel orchestration
- No bulk generation
- No automatic publishing

**✅ UI Cleanliness:**
- Angle logic one interaction deeper (modal, drill-down)
- Main matrix remains scannable
- No angle badges in cells

### 7.2 Scope Creep Check

**❌ No Hidden Scope:**
- Design is limited to Sunday Deep Dive
- No multi-channel logic
- No bulk operations
- No automation beyond proposal

**❌ No Confusion Reintroduced:**
- Clear separation: Topics (factual) vs. Angles (editorial)
- No overlap with calendar_themes (blog-focused)
- No mixing with post_development (post-specific)

**✅ Clean Boundaries:**
- Angles are additive layer
- Existing systems unchanged
- Clear data model relationships

### 7.3 Implementation Feasibility

**✅ Database:**
- Simple table structure
- Standard relationships (FKs, indexes)
- No complex constraints

**✅ API:**
- Standard REST endpoints
- Clear request/response shapes
- Straightforward error handling

**✅ UI:**
- Modal component (reusable pattern)
- Integration points identified
- No major UI refactor required

**✅ Generation:**
- Additive prompt composition
- Reuses existing aggregation logic
- Fallback behavior clear

---

## 8. Implementation Readiness

### 8.1 Design Completeness

**✅ Data Model:** Complete schema with rationale  
**✅ API Design:** All endpoints specified with request/response  
**✅ UI Flows:** Step-by-step user journeys documented  
**✅ Generation Pipeline:** Integration points and flow described  
**✅ Rollout Plan:** Build order and dependencies defined  
**✅ Open Questions:** All questions raised and decisions documented

### 8.2 Risk Assessment

**Low Risk:**
- Database changes are additive (nullable columns)
- API endpoints are new (no breaking changes)
- UI changes are additive (new modal, no refactor)

**Medium Risk:**
- LLM proposal performance (mitigated by loading states, timeouts)
- Source aggregation complexity (reuses existing logic)

**Mitigation:**
- Feature flag allows gradual rollout
- Fallback behavior ensures backward compatibility
- Clear error handling at each step

### 8.3 Next Steps

**Ready for Implementation When:**
1. ✅ This design is reviewed and approved
2. ✅ Any open questions are resolved
3. ✅ Engineering confirms feasibility
4. ✅ Implementation sequence is agreed

**Implementation Will:**
1. Create database migrations
2. Implement API endpoints
3. Build UI components
4. Integrate generation pipeline
5. Test end-to-end workflow

**No Code Until:**
- Design approval confirmed
- All questions resolved
- Implementation plan agreed

---

## 9. Summary

This design document provides:

1. **Complete Data Model** - `content_angles` table with relationships
2. **Full API Specification** - 6 endpoints with request/response shapes
3. **Detailed UI Flows** - Step-by-step user journeys for both UIs
4. **Generation Integration** - Angle-aware prompt composition and source aggregation
5. **Rollout Plan** - Sequential build order with testing strategy
6. **Open Questions** - All ambiguities raised and decisions documented

**Design Principles Maintained:**
- ✅ Hierarchy: `TOPIC → ANGLE → ROLE → CHANNEL → OUTPUT`
- ✅ Persistence: Topic-bound, reusable, persistent
- ✅ Human-in-the-Loop: No auto-selection
- ✅ Backward Compatible: Existing posts work unchanged
- ✅ Scope Locked: Sunday Deep Dive only

**Design is ready for engineering review and implementation approval.**

---

**End of Implementation Design Brief**
