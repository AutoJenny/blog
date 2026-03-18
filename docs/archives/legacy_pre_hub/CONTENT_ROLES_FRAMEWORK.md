# Content Roles Framework

**Date:** 2026-01-23  
**Status:** ✅ **FRAMEWORK DEFINED** - Database schema implemented, implementation incremental  
**Purpose:** Base-level system design reference for automated social media generation, scheduling, and quality control

---

## Overview

The Content Roles Framework separates **what a post is for** (its role/purpose) from **where or how it is published** (platform/channel/format). This enables scale without loss of tone, accuracy, or brand integrity.

**Core Principle:** Every piece of social content must perform **one job only**. That job is called its **Content Role**.

---

## 1. Core Concept

### Fundamental Rules

- **Roles are channel-agnostic**: A role works across Facebook, Instagram, Twitter, etc.
- **Roles are format-agnostic**: A role can be text, image, video, carousel, etc.
- **Roles are mutually exclusive**: One post = one role only
- **Roles are enforced by system logic**: Not editorial habit or suggestion

**If a post appears to do two jobs, it is incorrectly specified.**

### Why This Exists

**Without formal roles:**
- LLM outputs blur reassurance, selling, and authority
- Tone drifts over time
- Automation becomes unsafe
- QA becomes subjective

**With formal roles:**
- Prompts are deterministic
- Scheduling is mechanical
- Validation is possible
- Content scales without dilution

---

## 2. Canonical Content Roles

Roles are implemented as a fixed lookup table (`content_roles`) in the database. Each generated post must reference exactly one role.

### 2.1 REASSURANCE / PERMISSION

**Role Code:** `REASSURANCE`

**Purpose:**  
Reduce anxiety and friction. Give people permission to engage comfortably.

**Primary user questions answered:**
- Is it safe to contact you?
- Will I be pressured or rushed?
- Can I do this in a way that suits me?

**Characteristics:**
- Human, patient, calm
- Mentions availability, time, flexibility
- Often references phone or conversation

**Hard Constraints:**
- ❌ Must not promote products
- ❌ Must not contain sales language
- ❌ Must not provide technical depth

**Typical Length:**  
Short (1–3 short paragraphs, 50-300 words)

**Typical Sources:**
- Service principles
- Customer interaction philosophy
- Reassurance pool (CSV / generator)

**Source Type:** `reassurance_pool`  
**Requires Topic:** ❌ No  
**Requires Source Page:** ❌ No

---

### 2.2 AUTHORITY / CONTEXT (SHORT)

**Role Code:** `AUTHORITY_SHORT`

**Purpose:**  
Establish quiet credibility through factual context or reframing.

**Primary user questions answered:**
- Do these people know what they're talking about?
- Is this more nuanced than I assumed?

**Characteristics:**
- Declarative
- Calm and factual
- Usually avoids first-person ("we")
- Often myth-correcting or context-setting

**Hard Constraints:**
- ❌ No reassurance language
- ❌ No service mentions
- ❌ No calls to action
- ✅ One idea only

**Typical Length:**  
Very short (1–3 lines, 20-150 words)

**Typical Sources:**
- Clan Info Centre (single article/page)
- Historical or practical assertions

**Source Type:** `topic_rota` (can draw from weekly topic)  
**Requires Topic:** ❌ No (optional, but can use weekly topic)  
**Requires Source Page:** ✅ Yes (must reference specific KB article)

---

### 2.3 DEPTH / EXPERTISE (LONG FORM)

**Role Code:** `DEPTH_LONG`

**Purpose:**  
Demonstrate embedded knowledge and judgement.

**Primary user questions answered:**
- How does this actually work?
- Why is this more complex than it looks?
- What does experience teach here?

**Characteristics:**
- Narrow scope
- Explanatory (not summarising)
- Structured with white space
- Reflective close (not a conclusion)

**Hard Constraints:**
- ❌ No selling
- ❌ No service mentions
- ❌ No product mentions
- ✅ Must be grounded in Clan Info Centre source material
- ✅ Must not introduce facts beyond the source

**Typical Length:**  
120–220 words

**Typical Sources:**
- Clan Info Centre (single page or section)
- Weekly topic from KB Topic Rota

**Source Type:** `topic_rota`  
**Requires Topic:** ✅ **YES** (must use active weekly topic)  
**Requires Source Page:** ✅ Yes (must reference specific KB article)

**Critical Rule:**  
Generation should **block** if no active weekly topic is set.

---

### 2.4 CULTURE / TEXTURE

**Role Code:** `CULTURE`

**Purpose:**  
Provide personality, rhythm, and familiarity.

**Primary user questions answered:**
- What kind of place is this?
- Does this feel human and distinctive?

**Characteristics:**
- Light
- Repeatable formats
- Familiar cadence

**Hard Constraints:**
- ❌ No selling
- ❌ No authority claims
- ❌ No deep explanation

**Typical Length:**  
Very short (10-100 words)

**Typical Sources:**
- Word / Phrase / Insult formats
- Fixed pools

**Source Type:** `pool`  
**Requires Topic:** ❌ No  
**Requires Source Page:** ❌ No

---

### 2.5 COMMERCE / VISIBILITY

**Role Code:** `COMMERCE`

**Purpose:**  
Make products visible and concrete.

**Primary user questions answered:**
- What do you sell?
- What does this look like in practice?

**Characteristics:**
- Visual or descriptive
- Straightforward
- Non-educational

**Hard Constraints:**
- ❌ No deep heritage explanation
- ❌ No reassurance language
- ❌ No long-form content

**Typical Length:**  
Short to medium (50-200 words)

**Typical Sources:**
- Product catalogue

**Source Type:** `product_catalogue`  
**Requires Topic:** ❌ No  
**Requires Source Page:** ❌ No

---

## 3. Global Rules (Non-Negotiable)

1. **One post = one role only**
2. **Roles must never be mixed**
3. **Roles are mandatory metadata** (once framework is fully implemented)
4. **Scheduling logic operates on roles**
5. **QA logic validates against role constraints**

---

## 4. Database Schema

### Tables

#### `content_roles`
Stores the canonical role definitions.

**Key Fields:**
- `role_code` (VARCHAR(50), PRIMARY KEY) - Role identifier
- `role_name` (VARCHAR(100)) - Human-readable name
- `description` (TEXT) - Full description
- `purpose` (TEXT) - What this role is for
- `characteristics` (TEXT) - How content in this role should feel
- `hard_constraints` (JSONB) - Structured validation rules
- `typical_length_min/max` (INTEGER) - Word count ranges
- `source_type` (VARCHAR(50)) - Where content comes from
- `requires_topic` (BOOLEAN) - Must use weekly topic?
- `requires_source_page` (BOOLEAN) - Must reference KB article?

#### `posting_queue` (Extended)
New columns added for role framework:

- `role` (VARCHAR(50)) - References `content_roles.role_code`
- `topic_id` (INTEGER) - References `kb_topics.id` (for topic-bound roles)
- `source_page_id` (INTEGER) - References specific KB article (for AUTHORITY_SHORT, DEPTH_LONG)
- `rota_year` (INTEGER) - Year of rota week when post was generated
- `rota_week` (INTEGER) - ISO week number when post was generated

**Important:** All new columns are **nullable** to support existing posts. Framework will be implemented incrementally.

---

## 5. Relationship to KB Topic Rota System

### Weekly Topic Rules

- **Exactly one active topic per week** (from `kb_topic_rota`)
- **Topic applies only to topic-bound roles:**
  - `DEPTH_LONG` - **MUST** use weekly topic
  - `AUTHORITY_SHORT` - **CAN** use weekly topic (optional)
- **Non-topic roles are independent:**
  - `CULTURE` - Fixed pools (words/phrases/insults)
  - `COMMERCE` - Product catalogue
  - `REASSURANCE` - Reassurance pool

### Topic Changes Mid-Week

- **Allowed** - Topics can change mid-week
- **Warning Required** - If `DEPTH_LONG` post already exists, warn user
- **Existing Posts Not Invalidated** - Posts keep their original topic reference (`rota_year`, `rota_week`, `topic_id`)

---

## 6. Facebook Content Matrix (v1 - LOCKED)

### 6.1 Canonical Facebook Schedule Rails

Fixed schedule unless explicitly changed:

| Day | Time (UK) | Role | Notes |
|-----|-----------|------|-------|
| Monday | 09:00 | CULTURE | Word |
| Tuesday | 17:00 | COMMERCE | Product |
| Wednesday | 09:00 | CULTURE | Phrase |
| Thursday | 17:00 | COMMERCE | Product |
| Friday | 11:07 | CULTURE | Insult |
| Saturday | 14:30 | REASSURANCE | Message |
| Sunday | 15:00 | DEPTH_LONG | Long-form |

**Rules:**
- One post per day max
- No role substitution by default
- Scheduler requests role, not topic

### 6.2 Role → Topic Binding Rules (Facebook)

| Role | Topic Required? | Source |
|------|----------------|--------|
| CULTURE | ❌ No | Fixed pools / formats |
| COMMERCE | ❌ No | Product catalogue |
| REASSURANCE | ❌ No | Reassurance pool (CSV / generator) |
| DEPTH_LONG | ✅ **Yes** | Weekly topic (Info Centre / cluster) |

**Hard Rule:**  
`DEPTH_LONG` must reference the active weekly topic. Generation should **block** if no topic is set.

### 6.3 Facebook Role Quotas (Soft Constraints)

Used for validation and warnings only:

| Role | Target / Week |
|------|---------------|
| CULTURE | 3 |
| COMMERCE | 2 |
| REASSURANCE | 1 |
| DEPTH_LONG | 1 |

**If drift occurs:**
- Show warning in UI
- Do not block scheduling

### 6.4 Facebook Formatting Constraints (per role)

**CULTURE:**
- Very short
- No links
- No images required
- Fixed format allowed

**COMMERCE:**
- Image or product reference allowed
- No long heritage explanation
- No reassurance language

**REASSURANCE:**
- Text-led
- Calm, human
- No products
- No CTA
- Line breaks encouraged

**DEPTH_LONG:**
- 120–220 words
- White space (short paragraphs)
- No selling
- No service mentions
- Grounded in Info Centre source
- No links or CTAs

### 6.5 Facebook Scheduler Logic

**Pseudo-logic:**

```
For each upcoming Facebook schedule slot:
    role = slot.required_role
    if role requires topic:
        assert active_topic exists
        source = active_topic.source
    else:
        source = role_pool

    post = select or generate post(role, source)
    validate(post, role)
    schedule(post, slot.time)
```

**The scheduler never asks:** "What should we post today?"  
**It asks:** "It's Saturday — do we have a REASSURANCE post?"

---

## 7. LLM Generation Architecture

### Prompt Structure

Roles must be enforced via **system prompts**, not user prompts.

Each generation job should include:

1. **Global system prompt** (role separation rule)
2. **Role-specific system prompt** (constraints, tone, length)
3. **Source content** (if applicable - from KB Topic Rota or pools)
4. **Platform/channel adaptation** (formatting only)
5. **Task instruction**

**The LLM must never infer or select its own role.**

### Role-Specific Prompts

Each role has distinct prompt templates that enforce:
- Tone and style
- Length constraints
- Forbidden phrases/elements
- Required elements
- Source grounding (for AUTHORITY_SHORT, DEPTH_LONG)

---

## 8. Validation / QA System

Post-generation validation should include:

### Per-Role Validation

- **Word count checks** (role-specific ranges)
- **Forbidden phrase detection** (role-specific)
- **Source presence checks** (AUTHORITY_SHORT, DEPTH_LONG)
- **Structural checks** (paragraphs, length)
- **Role constraint checks** (no selling in REASSURANCE, etc.)

**Failures should trigger regeneration or review.**

### Validation Rules by Role

**REASSURANCE:**
- ✅ Check: No product mentions, no sales language
- ✅ Check: Mentions availability/flexibility
- ✅ Check: Length 50-300 words

**AUTHORITY_SHORT:**
- ✅ Check: Has source_page_id
- ✅ Check: No "we"/"our" language
- ✅ Check: No CTAs
- ✅ Check: Length 20-150 words
- ✅ Check: One idea only

**DEPTH_LONG:**
- ✅ Check: Has topic_id (weekly topic)
- ✅ Check: Has source_page_id
- ✅ Check: No selling/service mentions
- ✅ Check: Length 120-220 words
- ✅ Check: Structured paragraphs with white space

**CULTURE:**
- ✅ Check: No selling/authority claims
- ✅ Check: Length 10-100 words

**COMMERCE:**
- ✅ Check: No deep heritage explanation
- ✅ Check: Length 50-200 words

---

## 9. Implementation Strategy (Incremental)

### Phase 1: Foundation ✅ **COMPLETE**
- ✅ Define role enum/table (`content_roles`)
- ✅ Add role field to post records (`posting_queue.role`)
- ✅ Add topic linking (`posting_queue.topic_id`, `rota_year`, `rota_week`)
- ✅ Add source page linking (`posting_queue.source_page_id`)
- ✅ Document framework

### Phase 2: Facebook Sunday DEPTH_LONG (Proof of Concept) ✅ **PARTIALLY COMPLETE**
**Status:** Core implementation complete, publishing integration pending

**Completed:**
- ✅ Schedule rail definition (Sunday 15:00 DEPTH_LONG) - `config/content_roles_schedule_rails.py`
- ✅ Topic requirement enforcement (blocks generation if missing)
- ✅ Generation pipeline (`utils/content_roles/depth_long_generator.py`)
  - Fetches KB article text (bounded to ~2000 words)
  - Calls LLM with role-specific prompts
  - Enforces DEPTH_LONG constraints
- ✅ Validation system (`utils/content_roles/validator.py`)
  - Word count (120-220)
  - Paragraph count (≥3)
  - Forbidden phrase detection
  - Source page presence verification
- ✅ API endpoints (`blueprints/content_roles_api.py`)
  - Generate, validate, approve, schedule
- ✅ Manual approval & scheduling workflow
- ✅ Topic Rota Editor UI (Sunday slot panel)
- ✅ Content Control Board UI (read-only weekly matrix)
- ✅ Roles Reference page

**Pending:**
- ⏳ Publishing integration (scheduled posts don't publish automatically yet)
  - Need to extend `publish_to_facebook()` to handle `role='DEPTH_LONG'`
  - Need to ensure `scheduled_posting_executor.py` picks up role-based posts
- ⏳ Content Control Board actions (currently read-only, needs generate/approve actions)
- ⏳ Source article selection UX improvements

**Next Steps:**
- Implement publishing integration to complete end-to-end flow
- Add Control Board actions for Sunday Deep Dive
- Test complete workflow: Generate → Validate → Approve → Schedule → Publish

### Phase 3: Topic Integration
- ⏳ Link KB Topic Rota to DEPTH_LONG generation
- ⏳ Build topic → role mapping logic
- ⏳ Update KB Topic Rota API to support role selection
- ⏳ Handle topic changes mid-week (warnings)

### Phase 4: Other Channels
- ⏳ X/Twitter matrix (AUTHORITY_SHORT only)
- ⏳ Instagram matrix
- ⏳ Other platforms

### Phase 5: Full Automation
- ⏳ Automated role-based generation
- ⏳ Automated validation and QA
- ⏳ Role diversity in scheduling
- ⏳ Full integration with existing post creation processes

---

## 10. Migration Notes

**Important:** This framework is implemented **incrementally**. Existing post creation processes are **NOT changed** by the initial migration.

**Backward Compatibility:**
- All new columns are **nullable**
- Existing posts will have `role = NULL` initially
- Framework can be adopted gradually

**Future Migration Path:**
- Once all posts have roles assigned, `role` can be made `NOT NULL`
- Existing `content_type` can be phased out if desired (or kept for compatibility)

---

## 11. Summary

The Content Roles Framework is the **control system** for automated social content.

It ensures:
- ✅ Clarity of purpose
- ✅ Tone consistency
- ✅ Safe LLM usage
- ✅ Long-term scalability

**Roles are not editorial suggestions. They are system-level constraints.**

---

## 12. Related Documentation

- [KB Topic Rota System](./KB_TOPIC_ROTA_SYSTEM.md) - Weekly topic discovery and scheduling
- [Facebook Content Matrix](./FACEBOOK_CONTENT_MATRIX.md) - Facebook-specific implementation (when created)
- [Posting Queue Schema](../blog-launchpad/docs/database/posting_queue_schema.md) - Database reference

---

## Related Systems

### Angles Layer (Phase 3)

The **Angles Layer** provides an editorial interpretation layer between Topics and Roles. It enables reuse of storylines across channels and post types.

**Key Relationship:**
- **Topics** provide factual/semantic domains
- **Angles** provide editorial interpretations of topics
- **Roles** define post purposes (DEPTH_LONG, REASSURANCE, etc.)
- **Angles feed Roles** - An angle can generate multiple role-specific outputs

**Documentation:**
- `docs/ANGLES_LAYER_IMPLEMENTATION.md` - Full technical documentation
- `docs/ANGLES_LAYER_QUICK_REFERENCE.md` - Quick reference guide
- `docs/ANGLES_LAYER_IMPLEMENTATION_DESIGN.md` - Design document

**Current Status:** ✅ Implemented for Sunday Deep Dive (Facebook) only

---

**Last Updated:** 2026-01-25  
**Status:** Framework defined, database schema implemented, Phase 2 (Sunday DEPTH_LONG PoC) complete, Phase 3 (Angles Layer) implemented
