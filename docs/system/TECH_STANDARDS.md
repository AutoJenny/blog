# TECH_STANDARDS.md (Tech Stack v1)

**Generated:** 2026-03-18
**Owner:** Sole Operator (BlogForge / Unified Cockpit)

This document codifies the "Gold Standard" technology framework so new projects do not drift into ad-hoc port + UI + template patterns.

## 1. Logic Layer (Governed Backend Architecture)

**Standard:** Unified Flask using the **Application Factory Pattern** and **Blueprints**.

**Rules:**
1. All request logic for a project must live in a self-contained Blueprint (or a small set of Blueprints) registered into `unified_app.py`.
2. Every new project (e.g., Legal Advice, Civil Law) must be implemented as a self-contained Blueprint so it can be enabled/disabled without cross-project coupling.
3. Avoid direct logic edits in the root `unified_app.py` beyond Blueprint registration.

## 2. Styling Layer (UI Consistency)

**Standard:** **Tailwind CSS** (utility-first) is mandatory for layout and branding.

**Rules:**
1. Prefer Tailwind utility classes for layout, spacing, typography, colors, and responsive behavior.
2. Custom CSS should be minimal and only for edge cases that cannot be expressed cleanly via Tailwind utilities.
3. New styles must remain compatible with existing theme variables and avoid introducing one-off “widget CSS”.

## 3. Template Layer (Semantic Jinja2)

**Standard:** Semantic Jinja2 with a strict inheritance model:
`base.html` -> `layout.html` -> `page.html`

**Rules:**
1. Page templates must extend `layout.html` (not `base.html`) unless a framework-wide exception is approved.
2. Pages should override only semantically relevant blocks (content/body/title/etc).
3. Keep includes and blocks consistent so templates compose predictably across domains.

## 4. Global Navigation Anchor

**Rule:** All project UIs must feature the AI Hub logo at the far-left of the primary header, linking back to the Unified Cockpit root `http://localhost:9000/`.

**Why:** This provides a universal "Home" state and reduces UI fragmentation for the sole operator.

**Constraint:** The anchor must be a hard-link (single navigation target) and must not depend on the selected project state.

