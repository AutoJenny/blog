# TECH_STANDARDS.md (Tech Stack v2)

**Generated:** 2026-03-19
**Owner:** Sole Operator (BlogForge / Unified Cockpit)

This document codifies the "Gold Standard" technology framework so multi-domain projects do not drift into ad-hoc architecture, schema leakage, or UI fragmentation.

## 1. Platform Logic Layer (Governed Multi-Domain Architecture)

**Standard:** Domain backends are modular and registry-driven.

**Rules:**
1. Project identity (`project_id`) is the canonical partition key for retrieval, memory, threads, and orchestration.
2. Every project must be explicitly registered in the platform project registry before it is selectable in AI Hub.
3. Domain services must remain modular (Blueprints/modules per domain) and avoid cross-domain table coupling.
4. Avoid direct logic edits in root entry files beyond service/module registration and configuration wiring.

## 2. UI Layer (Consistency Across Domains)

**Standard:** Tailwind CSS (utility-first) is the baseline UI standard for new interfaces.

**Rules:**
1. Prefer Tailwind utility classes for layout, spacing, typography, colors, and responsive behavior in newly built screens.
2. Existing legacy CSS may be retained for stability, but new work should trend toward utility-first patterns.
3. Custom CSS should be minimal and reserved for edge cases that cannot be expressed cleanly via utility classes.
4. New styles must remain compatible with shared theme variables and avoid one-off widget-specific drift.

## 3. Template Layer (Semantic Composition)

**Standard:** Semantic templating with strict inheritance and predictable block contracts.

**Rules:**
1. For Flask/Jinja domains, follow `base.html` -> `layout.html` -> `page.html`.
2. For non-Jinja domains, enforce equivalent parent/child layout contracts.
3. Pages should override only semantically relevant blocks.
4. Keep includes and block naming consistent so templates compose predictably across domains.

## 4. Global Navigation Anchor

**Rule:** All project UIs must feature the AI Hub logo at the far-left of the primary header, linking back to the Unified Cockpit root `http://localhost:9000/`.

**Why:** This provides a universal "Home" state and reduces UI fragmentation for the sole operator.

**Constraint:** The anchor must be a hard-link (single navigation target) and must not depend on the selected project state.

## 5. Data and Recovery Standards (Post-Renaissance)

**Database Standard:** PostgreSQL @17 is the canonical operational target.

**Rules:**
1. No SQLite adoption for production workflows.
2. Schema additions require explicit approval before implementation.
3. Backups must use custom binary dumps (`pg_dump -Fc`) as the default recovery artifact.
4. Recovery operations must produce verifiable row-count audits for critical tables.

## 6. Future-Proofing: AI Hub as Research Facility

**Position:** AI Hub is not only a chat surface; it is the project-aware research control plane.

**Rules:**
1. AI Hub must expose both System Knowledge and Domain Knowledge lanes.
2. Research outputs should be evidence-backed, traceable, and reusable by downstream lifecycle phases.
3. Project switching must preserve strict context isolation and deterministic retrieval boundaries.
4. Architecture and standards docs must be updated whenever platform behavior changes materially.

