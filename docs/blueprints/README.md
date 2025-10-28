# Blueprint Inventory & Status

## Overview

This document tracks all blueprints in the unified blog application, their purpose, routes, and modularity status.

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

## Modularization Progress

### Completed Refactoring
- ✅ Utilities extracted to `launchpad_utils.py`

### In Progress
- 🚧 Launchpad blueprint - ~30% extracted
  - Created modular files but not activated
  - Still using monolithic `launchpad_old.py` in production

### Pending
- ⏳ Extract remaining syndication routes from launchpad
- ⏳ Create specialized modules for publishing operations
- ⏳ Document blueprint dependencies

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

