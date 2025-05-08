# LLM Image Generation Implementation Plan

## Overview
This plan covers the implementation of a robust, production-ready system for generating images via multiple LLM providers (e.g., Stable Diffusion/ComfyUI, OpenAI DALL·E), supporting both testing/comparison and automated blog post workflows. It includes structured settings for SD, extensible provider support, and a UI for managing prompt examples and results.

---

## Implementation Steps

### 1. Data Model Updates
- [ ] Add structured fields to `ImageSetting` for SD/ComfyUI (width, height, steps, guidance_scale, extra_settings)
- [ ] Update or create migration scripts to move from freeform to structured settings
- [ ] Add `provider` field to prompt examples and/or image generation requests
- [ ] Add `ImagePromptExample` model for reusable prompt+style+format+provider combos
- [ ] (Optional) Add `ImageGenerationResult` model for history/comparison

### 2. UI Changes
- [ ] Add "Provider" dropdown to the image prompt form
- [ ] Update ImageSetting create/edit UI to include structured SD settings (width, height, etc.)
- [ ] Add UI for saving/loading prompt examples (library)
- [ ] Allow batch/multi-provider testing and comparison in the preview area
- [ ] Update preview area to show results grid with provider/source labels

### 3. API/Backend Changes
- [ ] Update `/api/v1/images/generate` to accept `provider` and structured settings, and route to correct backend
- [ ] Implement backend logic for SD/ComfyUI (using structured settings)
- [ ] Implement backend logic for OpenAI DALL·E (mapping settings as needed)
- [ ] Add CRUD endpoints for prompt examples
- [ ] (Optional) Add endpoints for batch generation and result history

### 4. Production Workflow Integration
- [ ] Enable linking of prompt examples/settings to blog posts and sections
- [ ] Add backend endpoints to generate images for all sections of a post using stored settings
- [ ] Ensure generated images and metadata are stored and retrievable for blog display

### 5. Migration & Data Integrity
- [ ] Write migration scripts to parse existing freeform settings into structured fields
- [ ] Test migration and update legacy data as needed

### 6. Documentation & Testing
- [ ] Update `/docs/sd_integration.md` and related docs as features are implemented
- [ ] Add usage/testing instructions for each provider and workflow
- [ ] Document troubleshooting and extensibility notes

---

## Progress Tracking
- [ ] Data model changes complete
- [ ] UI changes complete
- [ ] Backend/API changes complete
- [ ] Production workflow integration complete
- [ ] Migration and data integrity verified
- [ ] Documentation and testing complete

---

_Refer to this plan throughout the implementation. Check off each item as it is completed._ 