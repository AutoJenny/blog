# Angles Layer - Quick Reference Guide

**Date:** 2026-01-25  
**Status:** ✅ Implemented  
**Purpose:** Quick reference for using the Angles Layer system

---

## What is an Angle?

An **Angle** is a reusable, editorially meaningful interpretation of a Topic. It represents a specific "story we could tell" about a topic.

**Example:**
- **Topic:** "Can anyone design a tartan?"
- **Angle:** "What 'official tartan' really means (and why it's often modern)"
- **Role Output:** Facebook Sunday Deep Dive post

---

## System Hierarchy

```
TOPIC → ANGLE → ROLE → CHANNEL → POST OUTPUT
```

Angles sit between Topics (factual domains) and Roles (post purposes).

---

## How to Use Angles

### 1. Generate Sunday Deep Dive Post with Angle

**Location:** KB Topic Rota Editor → Sunday Slot Panel

**Steps:**
1. Select week (year + ISO week number)
2. Select topic from dropdown
3. **Angle selector appears automatically**
4. Click **"Propose Angles"** button
5. Review 3-5 angle candidates in modal
6. Click **"Select"** on desired angle
7. Angle is saved, source articles pre-populated
8. Click **"Generate"** to create post
9. Post uses angle's narrative intent + source bundle

### 2. Generate Without Angle (Backward Compatible)

**Steps:**
1. Select week and topic
2. **Skip angle selection** (or don't click "Propose Angles")
3. Select source article manually
4. Click **"Generate"**
5. Post generated using topic-only mode (existing behavior)

### 3. View Angle in Control Board

**Location:** Planning → Content Control Board

**Steps:**
1. Navigate to week view
2. Click on Sunday cell (or any post with angle)
3. Drill-down panel opens
4. **"Angle" section** shows:
   - Angle name
   - Narrative intent
   - Usage count
   - Last used date

---

## API Quick Reference

### Propose Angles
```bash
POST /api/content-angles/propose
{
  "topic_id": 277,
  "num_candidates": 5
}
```

### Create Angle
```bash
POST /api/content-angles/angle
{
  "angle_name": "Angle name",
  "narrative_intent": "Story this tells...",
  "topic_id": 277,
  "source_article_ids": [640, 329]
}
```

### Generate with Angle
```bash
POST /api/content-roles/facebook/sunday/generate
{
  "topic_id": 277,
  "source_page_id": 640,
  "angle_id": 42,
  "rota_year": 2026,
  "rota_week": 5
}
```

---

## Key Features

✅ **Reusable** - Angles can be used across weeks  
✅ **Topic-bound** - Each angle belongs to one topic  
✅ **Human-selected** - No automatic selection  
✅ **Backward compatible** - Works with or without angles  
✅ **Usage tracked** - See how often angles are reused  

---

## Design Principles

1. **Hierarchy preserved:** TOPIC → ANGLE → ROLE → CHANNEL
2. **Backward compatible:** All fields nullable, fallback behavior
3. **Human-in-the-loop:** Explicit selection required
4. **Scope locked:** Sunday Deep Dive only (Phase 3)
5. **UI clean:** Angle logic one interaction deeper (modal)

---

## Related Documentation

- **Full Implementation Docs:** `docs/ANGLES_LAYER_IMPLEMENTATION.md`
- **Design Document:** `docs/ANGLES_LAYER_IMPLEMENTATION_DESIGN.md`
- **Final Specification:** `docs/ANGLES_LAYER_FINAL_SPECIFICATION.md`

---

**End of Quick Reference**
