---
title: Project Charter: BlogForge CMS
doc_class: overview
domain: project
status: active
summary: Strategic North Star for the Blog automation project.
updated: 2026-03-18
---

# PROJECT_CHARTER.md: BlogForge CMS (blog)

## 1. Project Identity
* **Project Name**: BlogForge CMS (Blog Automation)
* **Project ID**: `blog`
* **Repository Path**: `/Users/autojenny/Documents/projects/blog`

## 2. Core Mission & "The Why"
* **Primary Objective**: To achieve full automation parity for complex blog posts (themed, recipes, profiles) with the existing "Weekly Content" automation.
* **Goal State**: Posts reach 'ready' status one week before publication with zero manual intervention unless a "Review Gate" is triggered.

## 3. Operational Persona & Tone
* **Role**: A Full-Stack Flask Architect specializing in AI-driven content pipelines and multi-platform syndication.
* **Tone**: Highly technical, focused on state consistency, and strictly observant of database-driven workflow stages.

## 4. Hard Architectural Constraints
* **Unified Flask Design**: All logic must reside within the Blueprint-based structure in `unified_app.py`.
* **500-Line Rule**: All new or refactored modules must strictly adhere to the 500-line limit.
* **State Management**: Post progression must be governed by the `post_workflow_stage` and `post_workflow_sub_stage` tables.
* **Archival Isolation**: No legacy documentation (pre-hub) is considered authoritative. Only `docs/system/` and `docs/project/` are active knowledge.
* **Lean Root Rule**: The root directory must remain 'Lean'. No new documentation or one-off scripts are permitted at the root; they must be placed in `docs/` or `scripts/` respectively.

## 5. The Total Awareness Constraint
**Constraint**: No code shall be written, no tables created, and no files moved until a comprehensive audit of existing assets (Code, Database, and Archives) is completed and documented. Redundancy is a system failure; 100% leverage of existing 'Jigsaw' pieces is mandatory.

