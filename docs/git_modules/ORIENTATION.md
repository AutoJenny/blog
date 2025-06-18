# Modular Branch Architecture Orientation

## Purpose
This document defines the strict modular branch architecture for BlogForge workflow development. Its primary goal is to ensure robust, reviewable, and technically enforced separation between major UI modules, preventing accidental or unauthorized code changes across module boundaries—especially by AI automation. This orientation is the canonical reference for all contributors and AI agents to stay on track and avoid cross-contamination.

---

## What We Are Trying to Accomplish

- **Absolute separation** of UI modules (Base Framework, Navigation, LLM-Actions, Sections) into distinct, clean git branches.
- **No code for other modules** present in any module branch—only the code for that module exists in its branch.
- **Only shared code:** site-wide CSS (and possibly minimal config), which lives in the base-framework branch.
- **No shared templates, JS, or Python files** between modules. Only CSS and config may be shared.
- **Explicit, reviewable integration**: The only way to combine modules is via explicit, protected merges into a central `hub` branch.
- **Impossible for AI or developers to change other modules** without explicit branch switching and reviewable merges.
- **All inter-module communication** must be via the data layer (database/API) or a minimal, explicit shared API defined in the base framework.

---

## Branch Structure

- `base-framework`: Contains only the base framework code (header, footer, technical modules, docs, site-wide CSS/config).
- `workflow-navigation`: Contains only the navigation module code.
- `workflow-llm-actions`: Contains only the LLM-Actions module code.
- `workflow-sections`: Contains only the Sections module code.
- `hub`: The integration branch. Only updated by merging in the latest from each module branch. This is the only branch deployed as the live site.

---

## Directory Structure (per branch)
- Each branch has its own `templates/`, `static/`, and Python code for that module only.
- Only the base-framework branch contains the shared CSS and config.

---

## Integration/Deployment
- When a module is ready, its branch is merged into the `hub` branch.
- The `hub` branch is the only branch deployed/run as the live site.
- Merges are explicit, reviewable, and can be protected with branch protection rules.

---

## Inter-Module Communication
- All modules interact only via the data layer (database/API).
- No direct imports or code dependencies between module branches.
- If needed, a minimal shared API or event system can be defined in the base framework.

---

## AI/Automation Safeguards
- The AI can only work in one module branch at a time.
- The AI cannot change code in other modules without an explicit branch switch and merge.
- Branch protection rules can require human review for merges into the `hub` branch.

---

## Early Steps
1. Create the clean branches for each module.
2. Set up the base-framework branch with shared CSS/config.
3. Outline the process for merging into the `hub` branch.
4. Design the minimal API for inter-module communication if needed.

---

## Key Principle
**This architecture is designed to make it technically impossible for the AI (or anyone) to accidentally or implicitly change code in other modules. All integration is explicit, reviewable, and controlled.** 