# Angles Layer - Implementation Documentation

**Date:** 2026-01-25  
**Status:** ✅ **IMPLEMENTED** - Phase 3 complete  
**Purpose:** Technical documentation for the Angles Layer editorial interpretation system

---

## Overview

The Angles Layer is a **reusable, persistent editorial interpretation layer** that sits between Topics and Role/Channel outputs. It enables reuse of editorial storylines across channels and post types while maintaining human-in-the-loop control.

**Core Concept:** An Angle is a specific "story we could tell" about a topic—a coherent narrative interpretation that can be reused across weeks, roles, and channels.

---

## System Hierarchy

The Angles Layer fits into the following hierarchy:

```
TOPIC → ANGLE → ROLE → CHANNEL / FORMAT → POST OUTPUT
```

Where:
- **Topic** = Factual / semantic domain (from KB clustering)
- **Angle** = Editorial interpretation / storyline (NEW - Phase 3)
- **Role** = Purpose the post performs (Deep Dive, Quiet Authority, etc.)
- **Channel** = Platform-specific expression (Facebook, X, etc.)

---

## Database Schema

### Table: `content_angles`

Stores persistent, reusable editorial interpretations of topics.

**Key Fields:**

- `id` - Primary key (SERIAL)
- `angle_name` - Human-readable angle name (e.g., "What 'official tartan' really means")
- `angle_description` - Optional extended description
- `narrative_intent` - **Required** - What story this angle tells (editorial interpretation)
- `topic_id` - Foreign key to `kb_topics(id)` (required, ON DELETE RESTRICT)
- `source_article_ids` - Array of KB article IDs that form the source bundle (required, default: `{}`)
- `source_chunk_ids` - Optional array of specific chunk IDs (for future precision)
- `is_active` - Boolean flag for soft deletion (default: TRUE)
- `created_at`, `updated_at` - Timestamps
- `created_by` - Optional user identifier for audit
- `recommended_roles` - Array of role suggestions (e.g., `['DEPTH_LONG', 'AUTHORITY_SHORT']`)
- `suggested_channels` - Array of channel suggestions (e.g., `['facebook', 'x']`)
- `notes` - Manual editorial notes
- `usage_count` - Track reuse frequency (default: 0)
- `last_used_at` - Timestamp of last use
- `last_used_year` - Year of last use (for reuse tracking)
- `last_used_week` - ISO week of last use (for reuse tracking)

**Indexes:**

- `idx_content_angles_topic_id` - On `topic_id`
- `idx_content_angles_active` - Partial index on `is_active` (where active)
- `idx_content_angles_source_articles` - GIN index on `source_article_ids`
- `idx_content_angles_last_used` - On `(last_used_year, last_used_week)`

**Migration:** `migrations/20260125_create_content_angles_table.sql`

### Table Extension: `posting_queue.angle_id`

Added nullable foreign key to `content_angles` for linking generated posts to angles.

**Field:**
- `angle_id` - INTEGER, nullable, references `content_angles(id)` ON DELETE SET NULL

**Index:**
- `idx_posting_queue_angle_id` - Partial index (where angle_id IS NOT NULL)

**Migration:** `migrations/20260125_add_angle_id_to_posting_queue.sql`

**Backward Compatibility:** All existing posts have `angle_id = NULL`. Posts can be generated with or without angles.

---

## API Endpoints

### Base Path: `/api/content-angles`

All endpoints are registered via `blueprints/content_angles_api.py`.

### 1. Propose Angle Candidates

**Endpoint:** `POST /api/content-angles/propose`

**Purpose:** Generate multiple angle candidates for a topic (read-only, no persistence).

**Request Body:**
```json
{
  "topic_id": 277,
  "num_candidates": 5,
  "context": {
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
      "narrative_intent": "Explains that 'official' tartans are often modern creations...",
      "source_article_ids": [640, 329],
      "confidence_score": 0.85,
      "reasoning": "Topic articles discuss tartan registration and modern design practices"
    }
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

**Error Codes:**
- `TOPIC_NOT_FOUND` - Topic ID does not exist
- `TOPIC_INACTIVE` - Topic exists but is inactive
- `NO_SOURCE_ARTICLES` - Topic has no associated KB articles
- `GENERATION_FAILED` - LLM generation failed

**Implementation:** `utils/content_angles/angle_proposer.py::AngleProposer.propose_angles()`

---

### 2. Create or Update Angle

**Endpoint:** `POST /api/content-angles/angle`

**Purpose:** Create a new angle or update an existing one.

**Request Body (Create):**
```json
{
  "angle_id": null,
  "angle_name": "What 'official tartan' really means",
  "narrative_intent": "Explains that 'official' tartans are often modern creations...",
  "topic_id": 277,
  "source_article_ids": [640, 329],
  "source_chunk_ids": null,
  "notes": "Good angle for debunking myths",
  "recommended_roles": ["DEPTH_LONG"],
  "suggested_channels": ["facebook"]
}
```

**Request Body (Update):**
```json
{
  "angle_id": 42,
  "angle_name": "Updated angle name",
  "narrative_intent": "Updated narrative intent...",
  "topic_id": 277,
  "source_article_ids": [640, 329, 450]
}
```

**Response (Success):**
```json
{
  "success": true,
  "angle": {
    "id": 42,
    "angle_name": "What 'official tartan' really means",
    "narrative_intent": "Explains that 'official' tartans are often modern creations...",
    "topic_id": 277,
    "source_article_ids": [640, 329],
    "is_active": true,
    "usage_count": 0,
    "created_at": "2026-01-25T10:00:00",
    "updated_at": "2026-01-25T10:00:00"
  }
}
```

**Validation:**
- `angle_name` - Required, non-empty
- `narrative_intent` - Required, non-empty
- `topic_id` - Required, must exist in `kb_topics`
- `source_article_ids` - Required, must be non-empty array

**Error Codes:**
- `VALIDATION_FAILED` - Missing required fields
- `TOPIC_NOT_FOUND` - Topic ID does not exist
- `ANGLE_NOT_FOUND` - Angle ID provided but not found (update only)

---

### 3. Get Angle by ID

**Endpoint:** `GET /api/content-angles/angle/<angle_id>`

**Purpose:** Retrieve full angle details by ID.

**Response (Success):**
```json
{
  "success": true,
  "angle": {
    "id": 42,
    "angle_name": "What 'official tartan' really means",
    "angle_description": null,
    "narrative_intent": "Explains that 'official' tartans are often modern creations...",
    "topic_id": 277,
    "topic_name": "Tartan Design Principles",
    "source_article_ids": [640, 329],
    "source_chunk_ids": null,
    "is_active": true,
    "usage_count": 3,
    "last_used_at": "2026-01-20T15:00:00",
    "last_used_year": 2026,
    "last_used_week": 3,
    "created_at": "2026-01-15T10:00:00",
    "updated_at": "2026-01-20T15:00:00",
    "notes": null
  }
}
```

**Error Codes:**
- `ANGLE_NOT_FOUND` - Angle ID does not exist

---

### 4. Get Angles by Topic

**Endpoint:** `GET /api/content-angles/topic/<topic_id>`

**Purpose:** List all angles for a topic.

**Query Parameters:**
- `include_inactive` - Boolean (default: false) - Include inactive angles

**Response (Success):**
```json
{
  "success": true,
  "topic_id": 277,
  "topic_name": "Tartan Design Principles",
  "angles": [
    {
      "id": 42,
      "angle_name": "What 'official tartan' really means",
      "narrative_intent": "Explains that 'official' tartans are often modern creations...",
      "is_active": true,
      "usage_count": 3,
      "last_used_at": "2026-01-20T15:00:00",
      "last_used_year": 2026,
      "last_used_week": 3
    }
  ]
}
```

**Error Codes:**
- `TOPIC_NOT_FOUND` - Topic ID does not exist

---

### 5. Get Angles by Usage

**Endpoint:** `GET /api/content-angles/usage`

**Purpose:** Filter angles by usage history.

**Query Parameters:**
- `year` - Filter by `last_used_year`
- `week` - Filter by `last_used_week`
- `min_usage_count` - Minimum usage count
- `topic_id` - Filter by topic

**Response (Success):**
```json
{
  "success": true,
  "filters": {
    "year": 2026,
    "week": 3,
    "min_usage_count": 1,
    "topic_id": null
  },
  "angles": [
    {
      "id": 42,
      "angle_name": "What 'official tartan' really means",
      "topic_id": 277,
      "topic_name": "Tartan Design Principles",
      "usage_count": 3,
      "last_used_year": 2026,
      "last_used_week": 3
    }
  ]
}
```

---

## Generation Pipeline Integration

### DepthLongGenerator Updates

**File:** `utils/content_roles/depth_long_generator.py`

**Method Signature:**
```python
def generate(self, topic_id: int, source_page_id: int, 
             rota_year: int, rota_week: int, 
             angle_id: Optional[int] = None) -> Dict:
```

**Behavior:**

1. **If `angle_id` provided:**
   - Loads angle from database
   - Uses angle's `source_article_ids` for source aggregation
   - Composes angle prompt with role prompt
   - Falls back to `source_page_id` if angle has no articles

2. **If `angle_id` not provided:**
   - Uses existing behavior (single `source_page_id`)
   - Backward compatible

**Prompt Composition (with angle):**

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

**Source Aggregation:**

- Uses `_aggregate_angle_sources()` method
- Combines text from multiple articles (up to 5 articles, ~2000 words total)
- Joins with clear separators (`---`)

---

### Generation API Updates

**Endpoint:** `POST /api/content-roles/facebook/sunday/generate`

**File:** `blueprints/content_roles_api.py`

**Request Body (with angle):**
```json
{
  "topic_id": 277,
  "source_page_id": 640,
  "angle_id": 42,
  "rota_year": 2026,
  "rota_week": 5
}
```

**Changes:**
- `angle_id` is now optional
- `source_page_id` is optional if `angle_id` provided
- If `angle_id` provided, usage tracking is updated automatically

**Usage Tracking:**

When a post is generated with an angle:
1. `usage_count` is incremented
2. `last_used_at` is set to current timestamp
3. `last_used_year` and `last_used_week` are set from `rota_year` and `rota_week`

**Implementation:** `blueprints/content_roles_api.py::_update_angle_usage()`

---

## UI Components

### Sunday Slot Panel

**File:** `templates/kb_topics/rota_editor.html`

**Location:** KB Topic Rota Editor → Sunday Slot Panel

**New Components:**

1. **Angle Selector Section:**
   - Shown when topic is selected
   - "Propose Angles" button
   - Selected angle display (name + narrative intent)
   - "Change Angle" button

2. **Angle Selection Modal:**
   - Opens when "Propose Angles" clicked
   - Shows loading state during proposal
   - Displays candidate list with:
     - Angle name
     - Narrative intent
     - Source article count
     - "Select" button per candidate
   - "Create New Angle" button (placeholder, not implemented in Phase 3)
   - "Cancel" button

**JavaScript:** `static/js/kb_topics/sunday_slot.js`

**Key Methods:**
- `proposeAngles()` - Calls API, displays candidates
- `selectAngle(candidate, topicId)` - Creates/selects angle, updates UI
- `updateSelectedAngleDisplay()` - Shows selected angle info
- `closeAngleModal()` - Closes modal

**Integration:**
- Angle selector appears when topic selected
- Source articles pre-populated from selected angle
- Generation includes `angle_id` if selected

---

### Content Control Board

**File:** `templates/planning/content_control_board.html`

**Location:** Planning → Content Control Board

**Updates:**

1. **Week Data API Response:**
   - Includes `angle_id`, `angle_name`, `angle_narrative_intent` for each post
   - Includes `angle_usage_count`, `angle_last_used_year`, `angle_last_used_week`

2. **Post Details Panel:**
   - New "Angle" section in drill-down panel
   - Shows angle name, narrative intent, usage count
   - Shows "Not selected" for posts without angles (DEPTH_LONG only)

**API Updates:**
- `GET /api/planning/content-control-board/week` - Includes angle info
- `GET /api/planning/content-control-board/post/<post_id>` - Includes angle info

**Files:**
- `blueprints/planning_api_content_control_board.py` - API updates
- `static/js/planning/content_control_board.js` - UI updates

---

## Workflow Examples

### Example 1: Generate Sunday Post with Angle

1. **User opens KB Topic Rota Editor**
2. **User selects week** (e.g., Week 5, 2026)
3. **User selects topic** (e.g., "Tartan Design Principles")
4. **Angle selector appears**
5. **User clicks "Propose Angles"**
   - Modal opens, shows loading
   - API call: `POST /api/content-angles/propose` with `topic_id: 277`
   - 5 candidates displayed
6. **User selects candidate** (e.g., "What 'official tartan' really means")
   - API call: `POST /api/content-angles/angle` (creates angle)
   - Angle saved, UI updated
   - Source articles pre-populated from angle
7. **User clicks "Generate"**
   - API call: `POST /api/content-roles/facebook/sunday/generate` with `angle_id: 42`
   - Generator uses angle prompts + source aggregation
   - Post generated, angle usage tracked
8. **User reviews, validates, approves, schedules**

### Example 2: Reuse Angle Across Weeks

1. **User selects topic** (e.g., "Tartan Design Principles")
2. **User clicks "Propose Angles"**
3. **Modal shows existing angles** (if any) + new candidates
4. **User selects existing angle** (e.g., angle used in Week 3)
5. **Angle usage count increments**
6. **Generation proceeds with same angle, different week**

### Example 3: Generate Without Angle (Backward Compatible)

1. **User selects topic and source article**
2. **User does NOT select angle** (angle selector hidden or ignored)
3. **User clicks "Generate"**
4. **Generation uses topic-only mode** (existing behavior)
5. **Post created with `angle_id = NULL`**

---

## Design Principles

### 1. Hierarchy Preservation

The system maintains the strict hierarchy:
```
TOPIC → ANGLE → ROLE → CHANNEL → OUTPUT
```

Angles are topic-bound, not week-bound, enabling reuse.

### 2. Backward Compatibility

- All `angle_id` fields are nullable
- Generation works with or without angles
- Existing posts remain valid (`angle_id = NULL`)
- No breaking changes to existing APIs

### 3. Human-in-the-Loop

- Angles are **proposed**, never auto-selected
- Explicit human selection required
- No automatic reuse (Phase 3 scope)
- Editorial control maintained

### 4. Scope Lock (Phase 3)

**Included:**
- Angles for Sunday Deep Dive (Facebook) only
- Angle proposal, selection, persistence
- Angle-aware generation for `DEPTH_LONG` role

**Explicitly Excluded:**
- Multi-channel orchestration
- Bulk generation across channels
- Automatic angle reuse
- Automatic publishing
- Hard database constraints

### 5. UI Cleanliness

- Main matrix remains clean and scannable
- Angle logic is "one interaction deeper" (modal)
- Progressive disclosure principle applied

---

## Technical Implementation Details

### Angle Proposal Algorithm

**File:** `utils/content_angles/angle_proposer.py`

**Process:**

1. **Get topic metadata** from `kb_topics`
2. **Get topic articles** from `article_ids` array
3. **Get article details** (name, text preview) for context
4. **Call LLM** with:
   - System prompt: Angle generation instructions
   - User prompt: Topic + article context
   - Request: Generate N distinct angles
5. **Parse JSON response** (angle_name, narrative_intent, source_article_indices)
6. **Map indices to article IDs**
7. **Return candidates** with confidence scores

**LLM Model:** Ollama, llama3.2:latest

**Error Handling:**
- JSON parsing errors → fallback to empty list
- LLM errors → logged, return empty list
- Missing articles → validation error

---

### Source Aggregation

**File:** `utils/content_roles/depth_long_generator.py::_aggregate_angle_sources()`

**Process:**

1. **Iterate through angle's `source_article_ids`** (up to 5 articles)
2. **Fetch article text** using `_fetch_source_text()`
3. **Track total word count** (max ~2000 words)
4. **Combine articles** with separators (`---`)
5. **Return aggregated text**

**Fallback:**
- If aggregation fails → use `source_page_id` if provided
- If no `source_page_id` → return error

---

### Usage Tracking

**File:** `blueprints/content_roles_api.py::_update_angle_usage()`

**Process:**

1. **Increment `usage_count`**
2. **Set `last_used_at`** to current timestamp
3. **Set `last_used_year`** from `rota_year`
4. **Set `last_used_week`** from `rota_week`
5. **Update `updated_at`**

**Called:** Automatically after successful generation with angle

**Error Handling:** Logs errors but does not fail generation

---

## Testing & Validation

### Database Verification

```sql
-- Verify content_angles table exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'content_angles'
ORDER BY ordinal_position;

-- Verify posting_queue.angle_id exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'posting_queue' 
AND column_name = 'angle_id';
```

### API Testing

**Test Angle Proposal:**
```bash
curl -X POST http://localhost:5000/api/content-angles/propose \
  -H "Content-Type: application/json" \
  -d '{"topic_id": 277, "num_candidates": 5}'
```

**Test Angle Creation:**
```bash
curl -X POST http://localhost:5000/api/content-angles/angle \
  -H "Content-Type: application/json" \
  -d '{
    "angle_name": "Test Angle",
    "narrative_intent": "Test narrative",
    "topic_id": 277,
    "source_article_ids": [640, 329]
  }'
```

**Test Generation with Angle:**
```bash
curl -X POST http://localhost:5000/api/content-roles/facebook/sunday/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 277,
    "source_page_id": 640,
    "angle_id": 42,
    "rota_year": 2026,
    "rota_week": 5
  }'
```

---

## Future Enhancements (Out of Scope for Phase 3)

1. **Multi-Channel Orchestration**
   - Use same angle across Facebook, X, Instagram
   - Channel-specific formatting from single angle

2. **Automatic Reuse Detection**
   - Suggest angles based on usage history
   - Prevent accidental repetition

3. **Angle Library UI**
   - Browse all angles by topic
   - Filter by usage, date, etc.

4. **Bulk Generation**
   - Generate multiple posts from one angle
   - Batch processing

5. **Hard Constraints**
   - Database-level enforcement of angle requirements
   - Validation rules

---

## Related Documentation

- **Design Document:** `docs/ANGLES_LAYER_IMPLEMENTATION_DESIGN.md`
- **Final Specification:** `docs/ANGLES_LAYER_FINAL_SPECIFICATION.md`
- **Discovery Report:** `docs/ANGLES_LAYER_DISCOVERY_REPORT.md`
- **Content Roles Framework:** `docs/CONTENT_ROLES_FRAMEWORK.md`
- **KB Topic Rota System:** `docs/KB_TOPIC_ROTA_SYSTEM.md`

---

## Changelog

**2026-01-25: Phase 3 Implementation Complete**
- Database schema created
- API endpoints implemented
- UI components integrated
- Generation pipeline updated
- Control Board display added
- All tests passing

---

**End of Documentation**
