# Blueprint Inventory & Status

## Overview

This document tracks all blueprints in the unified blog application, their purpose, routes, and modularity status.

Last Updated: 2025-10-28

## Complete Blueprint Inventory

| File | Lines | Blueprint | Prefix | Domain | Status | Refactor Priority |
|------|-------|-----------|--------|--------|--------|-------------------|
| **header.py** | 2,309 | header | /header | Workflow | ✅ Active | 🔴 HIGH - Extract modules |
| **launchpad_old.py** | 2,202 | launchpad | /launchpad | Publishing | ✅ Active | 🔴 HIGH - Extract modules |
| **authoring_old.py** | 2,018 | (legacy) | - | Legacy | ❌ Unused | Archive |
| **imaging.py** | 1,506 | imaging | /imaging | Workflow | ✅ Active | 🔴 HIGH - Extract modules |
| **authoring_api_imaging.py** | 1,134 | authoring_imaging | /authoring | Workflow | ✅ Active | 🟡 MEDIUM |
| **automation_execute.py** | 949 | automation_core | /launchpad | System | ✅ Active | 🟡 MEDIUM |
| **authoring_api_prompts.py** | 890 | authoring_prompts | /authoring | Workflow | ✅ Active | 🟡 MEDIUM |
| **authoring_api_content.py** | 705 | authoring_content | /authoring | Workflow | ✅ Active | ✅ Good |
| **launchpad_content.py** | 636 | launchpad_content | /launchpad | Publishing | ✅ Active | 🟡 MEDIUM |
| **planning_sections.py** | 621 | planning | /planning | Workflow | ✅ Active | 🟡 MEDIUM |
| **launchpad/publishing.py** | 599 | publishing | /launchpad | Publishing | 📦 Ready | 🔵 Available |
| **ui_state.py** | 472 | ui_state | /ui-state | System | ✅ Active | ✅ Good |
| **core.py** | 383 | core | / | System | ✅ Active | ✅ Good |
| **launchpad_scheduling.py** | 376 | (legacy?) | - | Legacy? | ⚠️ Check | Review |
| **planning.py** | 361 | planning | /planning | Workflow | ✅ Active | ✅ Good |
| **automation_calendar.py** | 359 | automation_calendar | /launchpad | System | ✅ Active | ✅ Good |
| **database.py** | 348 | database | /database | System | ✅ Active | ✅ Good |
| **automation_pipeline.py** | 334 | automation_pipeline | /launchpad | System | ✅ Active | ✅ Good |
| **planning_api_post_specific.py** | 328 | planning_api | /planning | Workflow | ✅ Active | ✅ Good |
| **authoring.py** | 320 | authoring | /authoring | Workflow | ✅ Active | ✅ Good |
| **post_sections.py** | 307 | post_sections | /post-sections | Publishing | ✅ Active | ✅ Good |
| **post_info.py** | 295 | post_info | /post-info | Publishing | ✅ Active | ✅ Good |
| **authoring_api_concepts.py** | 285 | authoring_concepts | /authoring | Workflow | ✅ Active | ✅ Good |
| **llm_actions.py** | 265 | llm_actions | /llm-actions | System | ✅ Active | ✅ Good |
| **authoring_api_styles.py** | 255 | authoring_styles | /authoring | Workflow | ✅ Active | ✅ Good |
| **launchpad_core.py** | 229 | (legacy?) | - | Legacy? | ⚠️ Check | Review |
| **automation_core.py** | 222 | automation_core | /launchpad | System | ✅ Active | ✅ Good |
| **images.py** | 213 | images | /images | Publishing | ✅ Active | ✅ Good |
| **planning_api_calendar.py** | 180 | planning_api | /planning | Workflow | ✅ Active | ✅ Good |
| **clan_api.py** | 180 | clan_api | /clan-api | External | ✅ Active | ✅ Good |
| **planning_llm.py** | 173 | (internal) | - | Internal | 🔧 Helper | ✅ Good |
| **automation_settings.py** | 161 | automation_settings | /launchpad | System | ✅ Active | ✅ Good |
| **authoring_api_sections.py** | 143 | authoring_sections | /authoring | Workflow | ✅ Active | ✅ Good |
| **launchpad_utils.py** | 136 | (utility) | - | Shared | ✅ Active | ✅ Good |
| **planning_calendar_clean.py** | 98 | (legacy?) | - | Legacy? | ⚠️ Check | Review |
| **launchpad_queue.py** | 98 | (legacy?) | - | Legacy? | ⚠️ Check | Review |
| **planning_calendar.py** | 89 | (legacy?) | - | Legacy? | ⚠️ Check | Review |
| **planning_data.py** | 85 | (internal) | - | Internal | 🔧 Helper | ✅ Good |
| **planning_api_posts.py** | 76 | planning_api | /planning | Workflow | ✅ Active | ✅ Good |
| **planning_api_brainstorm.py** | 72 | planning_api | /planning | Workflow | ✅ Active | ✅ Good |
| **side_projects.py** | 71 | side_projects | /side | Misc | ✅ Active | ✅ Good |
| **planning_api_prompts.py** | 64 | planning_api | /planning | Workflow | ✅ Active | ✅ Good |
| **planning_concept.py** | 54 | (internal) | - | Internal | 🔧 Helper | ✅ Good |
| **launchpad/cross_promotion.py** | 49 | cross_promotion | /launchpad | Publishing | 📦 Ready | 🔵 Available |
| **planning_views.py** | 42 | (internal) | - | Internal | 🔧 Helper | ✅ Good |
| **launchpad/core.py** | 17 | core | /launchpad | Publishing | 📦 Ready | 🔵 Available |
| **settings.py** | 16 | settings | /settings | System | ✅ Active | ✅ Good |
| **launchpad/one_click_blog.py** | 12 | one_click_blog | /launchpad | Publishing | 📦 Ready | 🔵 Available |
| **launchpad/syndication.py** | 13 | syndication | /launchpad | Publishing | 📦 Placeholder | 🔵 Available |

### Legend
- ✅ Good: Below 500 lines
- 🟡 MEDIUM: 500-1000 lines
- 🔴 HIGH: Over 1000 lines
- 📦 Ready: Modular file created but not active
- ❌ Unused: Legacy/backup file
- ⚠️ Check: Status unclear, needs review
- 🔧 Helper: Internal module, not a blueprint

## Active Blueprints (Main System)

### 1. Core Blueprint
**File**: `blueprints/core.py`  
**URL Prefix**: `/`  
**Status**: ✅ Active  
**Purpose**: Main workflow, post management, calendar  
**Routes**: 
- `/` - Dashboard
- `/posts/<id>` - Post management
- `/workflow/posts/<id>/<stage>/<substage>/<step>` - Workflow navigation

**Notes**: Core functionality, heavily used throughout the app

---

### 2. Launchpad Blueprint
**File**: `blueprints/launchpad_old.py` (2,202 lines)  
**URL Prefix**: `/launchpad`  
**Status**: ⚠️ Active BUT being modularized  
**Purpose**: Content syndication, publishing, social media management  
**Routes**: 40+ routes covering publishing, syndication, cross-promotion, one-click-blog

**Issues**:
- Single monolithic file (2,202 lines)
- Needs refactoring into smaller modules

**Modularization Status**:
- ✅ Extracted `launchpad_utils.py` (136 lines) - shared utilities
- ✅ Created `blueprints/launchpad/core.py` (17 lines) - `/`, `/health`
- ✅ Created `blueprints/launchpad/one_click_blog.py` (12 lines) - `/one-click-blog`
- ✅ Created `blueprints/launchpad/cross_promotion.py` (49 lines) - `/cross-promotion`
- ✅ Created `blueprints/launchpad/publishing.py` (599 lines) - publishing routes
- 🚧 Created `blueprints/launchpad/syndication.py` (13 lines) - placeholder

**Note**: Currently using `launchpad_old.py` passthrough. Modular files exist but not active.

---

### 3. Planning Blueprint
**File**: `blueprints/planning.py`  
**URL Prefix**: `/planning`  
**Status**: ✅ Active  
**Purpose**: Content planning, topic brainstorming, structure design  
**Routes**:
- `/planning/posts/<id>/calendar/ideas` - Calendar ideas
- `/planning/posts/<id>/calendar/section-structure` - Section structure

**Notes**: Part of the planning workflow stage

---

### 4. Authoring Blueprint
**File**: `blueprints/authoring_api_content.py`  
**URL Prefix**: `/authoring`  
**Status**: ✅ Active  
**Purpose**: Section content drafting, LLM-powered content generation  
**Routes**:
- `/authoring/posts/<id>/sections/drafting` - Section drafting
- `/authoring/posts/<id>/sections/image-concepts` - Image concepts

**Notes**: Modular structure, uses sub-modules for API endpoints

---

### 5. Imaging Blueprint
**File**: `blueprints/imaging.py`  
**URL Prefix**: `/imaging`  
**Status**: ✅ Active  
**Purpose**: Image generation, optimization, watermarking  
**Routes**:
- `/imaging/posts/<id>/sections` - Section image generation
- `/imaging/posts/<id>/sections/<section_id>/image` - Specific image generation

**Notes**: Image processing workflow

---

### 6. Header Blueprint
**File**: `blueprints/header.py`  
**URL Prefix**: `/header`  
**Status**: ✅ Active  
**Purpose**: Header image management, SEO/meta data  
**Routes**:
- `/header/posts/<id>/header-image` - Header image generation
- `/header/posts/<id>/seo-meta` - SEO metadata

**Notes**: Header-specific functionality

---

## Blueprint Categories

### Workflow Blueprints (Active)
1. **Core** - Main workflow and post management
2. **Planning** - Content planning phase
3. **Authoring** - Content drafting phase
4. **Imaging** - Image generation phase
5. **Header** - Header image and SEO phase

### Publishing Blueprints (Active)
1. **Launchpad** - Publishing and syndication (needs refactoring)

---

## Refactor Roadmap

### High Priority Files (>1000 lines)
1. **header.py** (2,309 lines) - Extract routes by functionality
   - Header image generation routes
   - SEO/meta management routes
   - Helper functions (image processing, path resolution)

2. **launchpad_old.py** (2,202 lines) - Create publishing/syndication modules
   - Extract to `launchpad/publishing.py` ✅ (599 lines - ready but not active)
   - Extract to `launchpad/syndication.py` (13 lines - placeholder needs work)
   - Keep helper functions shared

3. **authoring_old.py** (2,018 lines) - LEGACY, not in use
   - Archive this file
   
4. **imaging.py** (1,506 lines) - Extract image generation/optimization
   - Split by image type (header vs section images)
   - Extract watermarking/optimization logic

5. **authoring_api_imaging.py** (1,134 lines) - Extract by image type
   - Split into concepts, prompts, generation modules

### Medium Priority Files (500-1000 lines)
- **automation_execute.py** (949 lines)
- **authoring_api_prompts.py** (890 lines)
- **authoring_api_content.py** (705 lines) - ✅ Good size
- **launchpad_content.py** (636 lines)
- **planning_sections.py** (621 lines)

### Modularization Progress

**Completed**:
- ✅ Utilities extracted to `launchpad_utils.py` (136 lines)
- ✅ Launchpad modular files created (publishing.py, core.py, one_click_blog.py, cross_promotion.py)

**In Progress**:
- 🚧 Launchpad blueprint - 30% extracted
  - Created modular files but not activated
  - Still using monolithic `launchpad_old.py` in production
  
**Pending**:
- ⏳ Extract remaining syndication routes from launchpad_old.py
- ⏳ Extract header.py into specialized modules
- ⏳ Extract imaging.py into specialized modules
- ⏳ Archive legacy/backup files

### Suggested Refactoring Order
1. Archive unused legacy files (`authoring_old.py`, `launchpad_monolithic_backup.py`, etc.)
2. Complete launchpad modularization (finish syndication extraction)
3. Refactor header.py (header image + SEO routes)
4. Refactor imaging.py (split by image type)
5. Review and refactor medium-priority files as needed

---

## Blueprint Dependencies

### Utility Modules
- `blueprints/launchpad_utils.py` - Shared utilities (`get_next_posting_slot`, `strip_html_doc`)

### Configuration
- `config/database.py` - Database management
- `config/paths.py` - Path resolution utilities
- `modules/llm_service.py` - LLM service integration

---

## Usage Patterns

### Active Routes
All routes are accessible at their URL prefixes (e.g., `/launchpad/publishing`, `/planning/posts/69/calendar/ideas`)

### Blueprint Registration
Blueprints are registered in `unified_app.py` with their respective URL prefixes.

### Template System
Each blueprint has associated templates in `templates/<blueprint_name>/`

---

## Notes for Future Development

1. **Launchpad Refactoring**: The launchpad blueprint is the largest and most complex. Continue extracting modules incrementally.

2. **Testing Strategy**: When activating modular blueprints, test all routes thoroughly before removing old code.

3. **Documentation**: Keep this file updated as blueprints are refactored.

4. **Backward Compatibility**: The current passthrough to `launchpad_old.py` maintains backward compatibility while allowing gradual migration.

