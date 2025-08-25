# LLM Images Mini-Project

> **NOTE:** This plan is now superseded by [`llm_images_implementation_plan.md`](llm_images_implementation_plan.md). See that file for the current status and roadmap. All major features described below are now implemented and in production use.

## Overview
This mini-project aims to build a robust, extensible image management system for LLM-powered image generation, selection, and refinement. The system will support prompt creation, image generation via OpenAI and other APIs, previewing, and systematic storage, with future-proofing for more advanced workflows.

## Goals
- [x] Simple, user-friendly UI for creating and testing image prompts
- [x] Support for prompt parts: description, style, format
- [x] Import prompt text from blog post fields
- [x] Generate images via OpenAI (DALL·E) API (MVP)
- [x] Preview and manage generated images
- [x] Store images systematically (test and post-based)
- [x] Watermarking as a post-generation action
- [x] Extensible for future LLMs, workflows, and approval/refinement

## MVP Features
- [x] Prompt creation form (description, style, format)
- [x] Import prompt from post field
- [x] Test prompt (send to OpenAI, view result)
- [x] Image preview gallery (filterable)
- [x] Systematic file storage (test dir, post dir)
- [x] Post-generation watermarking action
- [x] Models/schema for prompts and images
- [x] API endpoints for prompt creation, image generation, image listing

## Extensibility Notes
- [x] Support for prompt templates and batch operations
- [x] Multiple LLM/image generation backends (OpenAI, local SD, etc.)
- [x] Image refinement, approval, and assignment workflows
- [x] Bulk operations and cloud storage options

## Implementation Steps

### 1. Data Models & Schema
- [x] Design and implement models for ImagePrompt and ImageOutput
- [x] Add DB migrations

### 2. Prompt Creation UI
- [x] Build form for manual prompt creation (description, style, format)  
  _UI implemented and visually verified._
- [x] Add option to import prompt from post field

### 3. Prompt Testing & OpenAI Integration
- [x] Implement test button to send prompt to OpenAI and receive image
- [x] Store test images in test directory with datestamps

### 4. Image Preview Gallery
- [x] Build gallery UI for previews, filterable by prompt, post, date
- [x] Show image details and metadata

### 5. File Storage & Organization
- [x] Implement systematic file storage for test and post images
- [x] Store metadata in DB (and optionally as JSON sidecar)

### 6. Post-Generation Watermarking
- [x] Add watermarking action (not part of LLM prompt)
- [x] Allow user to apply watermark to any image

### 7. API Endpoints
- [x] Create endpoints for prompt creation, image generation, image listing

### 8. ImageStyle CRUD API endpoints
- [x] Implement CRUD API endpoints for ImageStyle (list, get, create, update, delete) in app/api/routes.py. Endpoints are ready for UI integration.

### 9. Dynamic Style Dropdown in Prompt Creation UI
- [x] Style dropdown in image prompt creation UI is now dynamic, fetching from the API, and supports adding new styles via modal dialog.

### 10. Edit/Delete Style Functionality in Prompt Creation UI
- [x] Users can now edit or delete image styles directly from the dropdown in the image prompt creation UI (images_prompts.html).

---

**This document is now archived. For current status and future work, see [`llm_images_implementation_plan.md`](llm_images_implementation_plan.md).** 