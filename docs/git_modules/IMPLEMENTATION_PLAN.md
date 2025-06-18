# Modular Branch Transition: Implementation Plan

This plan outlines every step required to transition to the new modular branch architecture. Use the checkboxes to track progress. Each stage includes explicit verification steps (backend commands, curl checks) before it can be marked complete.

---

## 1. Branch Preparation
- [x] Backup current definitive branch (`NEW_HUB`)
- [x] Create `base-framework` branch from `NEW_HUB` (not `main`)
- [x] Create `workflow-navigation` branch from `NEW_HUB`
- [x] Create `workflow-llm-actions` branch from `NEW_HUB`
- [x] Create `workflow-sections` branch from `NEW_HUB`
- [x] Create `hub` integration branch from `NEW_HUB`
- [ ] Protect all module branches and `hub` branch (branch protection rules)

**Important:**
- Each new module branch must be reduced to an empty state, retaining only the code strictly required for that module. All unrelated code must be removed. Only the code for the specific module should exist in its branch.

---

## 2. Base Framework Setup (`base-framework` branch)
- [x] Remove all workflow-specific code (navigation, LLM, sections) from base framework
- [x] Retain only header, footer, technical modules, docs, and site-wide CSS/config
- [x] Move all shared CSS and config to appropriate locations
- [x] Verify only base framework code remains
- [x] Backend: `git status` and `git diff` show no workflow code
- [x] Curl: Check all base framework endpoints (/, /posts, /settings, /docs, etc.)

---

## 3. Workflow Navigation Module (`workflow-navigation` branch)
- [x] Remove all code except navigation UI, logic, and assets
- [x] Ensure no LLM or sections code present
- [x] Place navigation templates, JS, and CSS in branch
- [x] Backend: `git status` and `git diff` show only navigation code
- [x] Curl: Check navigation rendering on all relevant workflow pages

---

## 4. LLM-Actions Module (`workflow-llm-actions` branch)
- [x] **llm-actions branch** — DONE. Branch is now reproducible and merged into NEW_HUB. All dependencies and Tailwind CSS build verified as of latest commit.
- [x] Remove all code except LLM input/prompt/output UI, logic, and assets
- [x] Ensure no navigation or sections code present
- [x] Place LLM templates, JS, and backend logic in branch
- [x] Backend: `git status` and `git diff` show only LLM-actions code
- [x] Curl: Check LLM endpoints and UI on all relevant workflow pages

---

## 5. Sections Module (`workflow-sections` branch)
- [x] Remove all code except sections UI, drag & drop, and assets
- [x] Ensure no navigation or LLM code present
- [x] Place sections templates, JS, and config in branch
- [x] Backend: `git status` and `git diff` show only sections code
- [x] Curl: Check sections UI and endpoints on all relevant workflow pages

---

## 6. Shared Data/API Layer
- [ ] For each module merge, audit for direct imports or cross-module code using `git grep` (e.g., navigation importing LLM code, etc.)
- [ ] Remove or refactor any direct imports or cross-module code found
- [ ] Confirm all modules interact only via the data/API layer (database or API endpoints)
- [ ] Move any shared config to the base-framework branch if needed
- [ ] After each merge, use curl to test all API endpoints for data access and correct interoperation
- [ ] Document each audit and test in the changelog

**Checklist:**
- [ ] Audit for direct imports/cross-module code after each merge
- [ ] Test all API endpoints with curl after each merge
- [ ] Fix/document any issues before proceeding to the next merge

---

## 7. Integration: Hub Branch (MAIN_HUB)
- [ ] Create the `MAIN_HUB` branch as a clean base (done)
- [ ] Sequentially merge each module branch into `MAIN_HUB` in the following order:
    1. `base-framework`
    2. `workflow-navigation`
    3. `workflow-llm-actions`
    4. `workflow-sections`
- [ ] After each merge:
    - [ ] Resolve any conflicts explicitly
    - [ ] Use `git diff` and `git log` to verify only intended changes are present
    - [ ] Audit for cross-module code (see Stage 6)
    - [ ] Test all site endpoints and workflow pages with curl and browser for correct integration and UI layout
    - [ ] Document results in the changelog
- [ ] Once all modules are merged and verified, lock down the `MAIN_HUB` branch with branch protection rules
- [ ] Require review for all future merges

**Checklist:**
- [ ] Merge each module branch in order
- [ ] Audit and test after each merge
- [ ] Document all results and issues
- [ ] Lock down `MAIN_HUB` after successful integration

---

## 8. Final Verification & Lockdown
- [ ] Backend: Run all tests (unit, integration, lint)
- [ ] Curl: Test every page and API endpoint (/, /posts, /settings, /docs, /workflow/*, /llm/*, etc.)
- [ ] Confirm no cross-module code contamination
- [ ] Lock down `hub` branch with strict protection rules
- [ ] Document final state in CHANGELOG and code_mapping.md

---

## 9. Ongoing Maintenance
- [x] Update code_mapping.md and ORIENTATION.md with every change
- [ ] Require review for all merges into `hub`
- [ ] Periodically audit branches for cross-contamination

---

## UI Integration Principle
- The base-framework module provides the header and footer, always visible on every page.
- The workflow-navigation module is always rendered immediately below the header, above the footer.
- Workflow modules (LLM-Actions, Sections, etc.) are rendered as independent panels below navigation, with layout determined by the workflow stage.
- All modules must appear as a seamless whole in the UI, despite technical separation at the code and branch level.

**No stage is complete until all backend and curl checks are passed and documented.** 