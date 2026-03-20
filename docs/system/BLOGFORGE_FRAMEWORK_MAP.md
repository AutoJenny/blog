# 🗺️ BLOGFORGE_FRAMEWORK_MAP (v1.1)
**Role**: Master Architectural Guide for Sole Human Operator
**Philosophy**: Management by Exception | Continuous Enrichment | Modular Intelligence

## 0. Constitutional Bridge (v3 Alignment)
- Global Constitution: `docs/SYSTEM_ARCHITECTURE_v3.md`
- Local Standards: `docs/system/TECH_STANDARDS.md`
- This document maps the global multi-domain architecture into the concrete BlogForge implementation.
- BlogForge must remain compliant with v3 for:
  1. Project identity isolation (`project_id=blog`)
  2. Knowledge Vault boundaries
  3. The 5-Phase Lifecycle contract

## I. The Strategic Core (Domain 0)
- **The Director**: Governed by `docs/project/BRAND_DNA.md`.
- **The Scout**: `scripts/market_scout.py` (Future) - Monitors trends.
- **Goal**: Every post must have a `marketing_intent` (Brand, Soft-Sell, or Conversion).

Tech Standards (Gold Standard): `docs/system/TECH_STANDARDS.md`

## II. The Production Domains (The Factory Floor)
1. **The Clock (Scheduling)**: `utils/calendar_resolver.py`. Resolves ideas 1 year out.
2. **The Library (Research)**: `modules/research_orchestrator.py`. Fetches facts before writing.
   - Uses SQL full-text search over `clan_kb_articles` (FAISS + vectors are for semantic augmentation) and FAISS-backed `utils.vector_search.retrieval.ContentRetriever` as primary internal sources.
   - Local `blog` database bootstrap is operationally verified: KB (clan_kb_* tables), FAISS substrate (`content_chunks`), and Identity (`families`) migrations are in place, and the Research Gate runs successfully to prioritize internal intelligence.
   - BlogForge Knowledge Vault mapping (v3):
     - `vault.blog.families` -> `families`, `family_designs`
     - `vault.blog.kb` -> `clan_kb_categories`, `clan_kb_articles`
     - `vault.blog.calendar` -> `calendar_ideas`, week controls/overrides, scheduling layers
3. **The Eye (Imaging)**: `environments/sdxl/` & `blueprints/images.py`. Generates assets during downtime.
4. **The Brain (Writing)**: `blueprints/llm_actions.py`. Compiles DNA + Research + Idea into text.

## III. The Nervous System (Workflow & Governance)
- **State Engine**: Managed via `post_workflow_stage` and `post_workflow_sub_stage` tables.
- **The Governor**: `scripts/system_governor.py` (Future) - Manages CPU/GPU/API capacity.
- **The Mouth**: `blueprints/launchpad.py` - Syndicates to external channels (FB, IG, Web).

## IV. Operational Constraints
1. **Pre-Flight Dependency**: No post is written (Domain 4) until Research (Domain 2) is flagged 'Complete'.
2. **Lean Root Rule**: No new scripts/docs at root. Operational files only.
3. **500-Line Limit**: All modules must remain under 500 lines to ensure maintainability.

## V. The Discovery-First Protocol

### Mandatory Discovery Steps

1. **Database Audit**: Identify all relevant tables, including those in migrations or isolated "Data Intelligence" layers.
2. **Infrastructure Audit**: Check for installed packages (e.g., faiss, sentence-transformers) that indicate existing, hidden capabilities.
3. **Logic Trace**: Follow the data flow of existing scripts (e.g., research_family_web.py) to the storage layer (FAISS/PostgreSQL).
4. **Existing Asset Map**: Present a report to the Human Supervisor verifying what is already available before proposing new code.

### New Operational Rule
"From this point forward, every new Phase or Task must begin with an Investigation Report verifying what currently exists in the blog repository (including all archives/ folders)".

## VI. BlogForge 5-Phase Lifecycle Mapping (v3)
1. **Research & Synthesis**  
   AI Hub + Domain 2 Library gather and rank internal truth first.
2. **Strategic Planning**  
   Calendar and workflow stages convert research into scheduled intent.
3. **Generation**  
   Draft assembly in writing modules using templates + governed context.
4. **Media & Refinement**  
   Visual assets, formatting, and tone polishing are aligned before publish.
5. **Deployment**  
   Launchpad and posting routines execute publication with auditable state transitions.

## VIII. Domain 8: Infrastructure
- `docs/system/INFRASTRUCTURE_MAP.md` (Unified Cockpit baseline: ports, routing, and current “ghost” footprint).
- Post-Renaissance standard is enforced by `docs/SYSTEM_ARCHITECTURE_v3.md`:
  - PostgreSQL@17 as canonical runtime
  - Binary `pg_dump -Fc` backups for surgical recovery

