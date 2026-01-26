# Final Angles Specification – Editorial Layer (Phase 3 Greenlight)

**Date:** 2026-01-25  
**Status:** ✅ **APPROVED FOR IMPLEMENTATION DESIGN** (no coding yet)  
**Audience:** Engineering (lead + implementers)  
**Purpose:** Lock the Angles concept definitively, confirm discovery conclusions, and green-light the next phase (design → implementation) without ambiguity.

---

## 1. Confirmation of Discovery Findings

The Angles Layer Discovery Report is accepted in full.

**Key confirmations:**
- No existing system already implements Angles as defined.
- Several systems provide infrastructure (topics, vectors, aggregation, prompts), but none provide the editorial interpretation layer required.
- Attempting to repurpose blog themes, post planning, or transient brainstorming would create conceptual and architectural confusion.

**Conclusion:** Angles must be implemented as a new first-class object, reusing infrastructure but not semantics from existing systems.

This document now locks the conceptual decisions required to proceed.

---

## 2. What an Angle Is (Definitive)

An Angle is a reusable editorial interpretation of a Topic.

It represents:
- a specific narrative
- a coherent story
- a particular way of explaining, contextualising, or framing a topic

An Angle answers the question:

**"What story are we telling about this topic?"**

**Examples:**
- "What 'official tartan' really means (and why it's often modern)"
- "How people without a known clan can choose a tartan responsibly"
- "Common misconceptions about clan tartans and registries"

**Angles are not:**
- factual topic discovery (that is Topics)
- purpose/job definitions (that is Roles)
- channel formatting (that is Channels)
- post drafts or outputs

---

## 3. What an Angle Is Not (Equally Important)

An Angle is not:
- bound to a specific week
- bound to a specific channel
- bound to a specific role
- ephemeral or transient
- automatically published

**Angles are editorial assets, not scheduling artefacts.**

---

## 4. Locked Conceptual Hierarchy

The system hierarchy is now formally defined as:

```
TOPIC  →  ANGLE  →  ROLE  →  CHANNEL / FORMAT  →  POST OUTPUT
```

**Where:**
- **Topic** = factual / semantic domain (from KB clustering)
- **Angle** = editorial interpretation / storyline
- **Role** = purpose the post performs (Deep Dive, Quiet Authority, etc.)
- **Channel** = platform-specific expression (Facebook, X, etc.)

This hierarchy must be preserved in design and implementation.

---

## 5. Persistence & Reuse Rules (Locked)

### 5.1 Persistence
- Angles are persistent objects.
- Once selected/created, an Angle is stored and reusable.

### 5.2 Topic relationship
- Each Angle is linked to one primary Topic.
- A Topic may have multiple Angles.

### 5.3 Reuse across weeks
- Angles are topic-bound, not week-bound.
- An Angle may be reused across weeks deliberately.
- Reuse must be visible and trackable (to avoid accidental repetition).

### 5.4 Reuse across roles/channels
- The same Angle may feed:
  - multiple Roles
  - multiple Channels
- Each usage produces a distinct output, but the storyline remains consistent.

---

## 6. Relationship to Existing Systems (Locked Decisions)

### 6.1 Topics (kb_topics)
- Remain factual and semantic.
- Provide source grounding and vector centroids.
- Angles reference Topics; Topics do not absorb Angles.

### 6.2 Calendar Themes (calendar_themes)
- Remain blog-focused and unchanged.
- Not reused for Angles.
- No migration or refactor required.

### 6.3 Role Framework (content_roles)
- Remains unchanged.
- Angles feed roles; roles do not define angles.

### 6.4 Prompt Templates (llm_prompt)
- Role prompts remain authoritative for tone and constraints.
- Angle-specific prompts may be added as compositional inputs, not replacements.

### 6.5 Posting Queue (posting_queue)
- Continues to store generated outputs.
- May optionally reference an Angle.
- Must remain backward compatible with posts that have no angle.

---

## 7. Editorial Control Model (Human-in-the-Loop)

Angles formalise editorial intent without automating editorial judgement.

**The system must:**
- propose Angle candidates
- never auto-select an Angle
- require explicit human selection or confirmation

This is deliberate and non-negotiable for Phase 3.

---

## 8. Scope Lock for Phase 3

To prevent uncontrolled expansion, the following scope is locked:

### 8.1 Included
- Angles implemented only for Sunday Deep Dive (Facebook) initially
- Angle proposal (multiple candidates)
- Angle selection and persistence
- Angle-aware generation for DEPTH_LONG role

### 8.2 Explicitly Excluded (for now)
- Multi-channel orchestration
- Bulk generation across channels
- Automatic angle reuse
- Automatic publishing
- Hard database constraints

These may be revisited in later phases, but are out of scope for initial implementation.

---

## 9. UI Expectations (Conceptual, Not Prescriptive)

Angles must be:
- reviewable in context (slot drill-down)
- selectable from multiple candidates
- visible once selected (e.g. displayed in slot details)

**The main planning matrix must remain clean and scannable.**

Angle intelligence belongs one interaction deeper.

---

## 10. Acceptance Criteria for Moving to Implementation Instructions

The next phase (implementation instructions) may proceed once:
- Engineering confirms agreement with this spec
- Any remaining uncertainties are explicitly raised
- A proposed implementation plan aligns with:
  - this hierarchy
  - persistence rules
  - scope lock

**No code should be written until this spec is acknowledged.**

---

## 11. Formal Green Light

This document formally:
- Accepts the Angles Layer Discovery Report
- Locks the Angles concept and hierarchy
- Authorises engineering to proceed to implementation design

**Phase 3 (Angles) is now green-lit for design and build.**

---

**End of Final Angles Specification**
