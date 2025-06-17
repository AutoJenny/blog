# LLM-Actions Module: Implementation Checklist

## Phase 1: Setup
- [ ] Copy all required templates, JS, and backend files (see LLM_ACTIONS_IMPLEMENTATION.md)
- [ ] Verify directory structure and permissions
- [ ] Document structure in README

## Phase 2: Core Components
- [ ] Inputs Accordion: field selector, value display, validation, save
- [ ] Prompt Accordion: template display/edit, save, preview
- [ ] Settings Accordion: model/provider/parameter controls
- [ ] Outputs Accordion: field selector, output display, save

## Phase 3: API Integration
- [ ] Fetch actions, prompts, field mappings, and post data via API
- [ ] Run LLM action and display output
- [ ] Save output to selected field
- [ ] Update prompt/settings via API

## Phase 4: Testing
- [ ] Test all UI components in browser
- [ ] Test all API endpoints with curl
- [ ] Validate DB updates for input/output fields
- [ ] Document all test results

## Phase 5: Documentation
- [ ] Update README and LLM_ACTIONS_IMPLEMENTATION.md for any changes
- [ ] Document all endpoints and data flows

---

**No step is complete until tested and documented.** 