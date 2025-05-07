# LLM Images Mini-Project

## Overview
This mini-project aims to build a robust, extensible image management system for LLM-powered image generation, selection, and refinement. The system will support prompt creation, image generation via OpenAI and other APIs, previewing, and systematic storage, with future-proofing for more advanced workflows.

## Goals
- Simple, user-friendly UI for creating and testing image prompts
- Support for prompt parts: description, style, format
- Import prompt text from blog post fields
- Generate images via OpenAI (DALL·E) API (MVP)
- Preview and manage generated images
- Store images systematically (test and post-based)
- Watermarking as a post-generation action
- Extensible for future LLMs, workflows, and approval/refinement

## MVP Features
- [ ] Prompt creation form (description, style, format)
- [ ] Import prompt from post field
- [ ] Test prompt (send to OpenAI, view result)
- [ ] Image preview gallery (filterable)
- [ ] Systematic file storage (test dir, post dir)
- [ ] Post-generation watermarking action
- [ ] Models/schema for prompts and images
- [ ] API endpoints for prompt creation, image generation, image listing

## Extensibility Notes
- Support for prompt templates and batch operations
- Multiple LLM/image generation backends (OpenAI, local SD, etc.)
- Image refinement, approval, and assignment workflows
- Bulk operations and cloud storage options

## Implementation Steps

### 1. Data Models & Schema
- [ ] Design and implement models for ImagePrompt and ImageOutput
- [ ] Add DB migrations

### 2. Prompt Creation UI
- [ ] Build form for manual prompt creation (description, style, format)
- [ ] Add option to import prompt from post field

### 3. Prompt Testing & OpenAI Integration
- [ ] Implement test button to send prompt to OpenAI and receive image
- [ ] Store test images in test directory with datestamps

### 4. Image Preview Gallery
- [ ] Build gallery UI for previews, filterable by prompt, post, date
- [ ] Show image details and metadata

### 5. File Storage & Organization
- [ ] Implement systematic file storage for test and post images
- [ ] Store metadata in DB (and optionally as JSON sidecar)

### 6. Post-Generation Watermarking
- [ ] Add watermarking action (not part of LLM prompt)
- [ ] Allow user to apply watermark to any image

### 7. API Endpoints
- [ ] Create endpoints for prompt creation, image generation, image listing

---

**This document will be updated as each step is completed. Checkboxes will be ticked and progress committed to git after verification (e.g., with curl).** 