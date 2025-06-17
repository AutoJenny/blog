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
- [ ] Remove all code except LLM input/prompt/output UI, logic, and assets
- [ ] Ensure no navigation or sections code present
- [ ] Place LLM templates, JS, and backend logic in branch
- [ ] Backend: `git status` and `git diff` show only LLM-actions code
- [ ] Curl: Check LLM endpoints and UI on all relevant workflow pages

---

## 5. Sections Module (`workflow-sections` branch)
- [ ] Remove all code except sections UI, drag & drop, and assets
- [ ] Ensure no navigation or LLM code present
- [ ] Place sections templates, JS, and config in branch
- [ ] Backend: `git status` and `git diff` show only sections code
- [ ] Curl: Check sections UI and endpoints on all relevant workflow pages

---

## 6. Shared Data/API Layer
- [ ] Ensure all modules interact only via the data/API layer
- [ ] Move any shared config to base-framework branch
- [ ] Backend: `git grep` for direct imports between modules (should be none)
- [ ] Curl: Test all API endpoints for data access

---

## 7. Integration: Hub Branch
- [ ] Merge each module branch into `hub` branch (one at a time, review each merge)
- [ ] Resolve any merge conflicts explicitly
- [ ] Backend: `git log` and `git diff` show only intended merges
- [ ] Curl: Test all site endpoints and workflow pages for correct integration

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

**No stage is complete until all backend and curl checks are passed and documented.** 