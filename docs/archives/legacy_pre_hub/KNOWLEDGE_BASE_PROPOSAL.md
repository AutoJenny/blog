# Knowledge Base Operations Manual - Proposal

**Date:** 2026-01-18  
**Purpose:** Design a comprehensive, navigable Knowledge Base for the blog application system

---

## Overview

A web-based Knowledge Base accessible at `http://localhost:5000/kb` that provides:
- **Indexed navigation** - Permanent left sidebar with hierarchical structure
- **Cross-referenced content** - Links between related sections and to UI views
- **Development status** - Clear indicators of what's complete, in progress, or planned
- **System relationships** - Shows how post types, channels, interfaces, and backend systems connect

---

## Proposed Structure

### Left Sidebar Index (Hierarchical)

```
📚 Knowledge Base
├── 🏠 Getting Started
│   ├── System Overview
│   ├── Quick Navigation Guide
│   ├── Development Status Dashboard
│   └── Common Tasks
│
├── 📝 Content Types
│   ├── Post Types Overview
│   ├── Themed Posts
│   ├── Recipe Posts
│   ├── Profile Posts
│   ├── Weekly Content
│   │   ├── Weekly Words
│   │   ├── Weekly Phrases
│   │   └── Weekly Insults
│   └── Generated Posts
│
├── 📤 Output Channels
│   ├── Channels Overview
│   ├── Blog
│   ├── Facebook
│   ├── Instagram
│   ├── Twitter
│   └── Newsletter
│
├── 🎯 Management Interfaces
│   ├── Interfaces Overview
│   ├── Planning Interface
│   │   ├── Calendar View
│   │   ├── Week View
│   │   ├── Ideas Management
│   │   └── Taxonomy
│   ├── Authoring Interface
│   │   ├── Drafting
│   │   ├── Image Concepts
│   │   ├── Image Prompts
│   │   └── Image Captions
│   ├── Imaging Interface
│   │   ├── Image Generation
│   │   └── Image Optimization
│   ├── Header Interface
│   │   ├── Title & Summary
│   │   ├── Header Image
│   │   ├── SEO Meta
│   │   └── Final Review
│   ├── Publication Dashboard
│   ├── Monitoring System
│   └── Launchpad
│       ├── One-Click Publication
│       ├── Instagram Carousel
│       └── Cross-Promotion
│
├── ⚙️ Workflows & Automation
│   ├── Workflow Overview
│   ├── Stage System
│   │   ├── Calendar Stage
│   │   ├── Planning Stage
│   │   ├── Research Stage
│   │   ├── Authoring Stage
│   │   ├── Imaging Stage
│   │   └── Header Stage
│   ├── Automation Systems
│   │   ├── Weekly Content Automation
│   │   ├── Product Post Automation
│   │   └── Background Monitor
│   └── Posting Queue System
│
├── 🔧 Backend Systems
│   ├── Database Architecture
│   │   ├── Core Tables
│   │   ├── Posting Queue
│   │   ├── Calendar System
│   │   └── Platform Credentials
│   ├── API Endpoints
│   │   ├── Automation API
│   │   ├── Planning API
│   │   ├── Authoring API
│   │   └── Publication API
│   ├── Services & Utilities
│   │   ├── LLM Integration (Ollama)
│   │   ├── ImageMagick Integration
│   │   ├── Facebook API
│   │   └── Data Extractors
│   └── Configuration Files
│
├── 📊 Data Models
│   ├── Post Type Configuration
│   ├── Channel Configuration
│   ├── Content Format Mapping
│   └── Workflow Configuration
│
└── 📖 Technical Reference
    ├── File Structure
    ├── Blueprint Organization
    ├── Template System
    ├── JavaScript Architecture
    └── Deployment & Operations
```

---

## Content Organization Principles

### 1. **Hierarchical Navigation**
- **Left Sidebar**: Always visible, collapsible sections, shows current location
- **Breadcrumbs**: Top of content area showing full path
- **Search**: Quick search across all KB content

### 2. **Cross-Referencing**
Each page includes:
- **Related Sections**: Links to related KB pages
- **UI Links**: Direct links to relevant interface pages (e.g., `/planning/posts/123/calendar/view`)
- **Technical Docs**: Links to detailed technical docs in `/docs`
- **Status Indicators**: Visual badges showing development status

### 3. **Status Indicators**
Visual badges throughout:
- ✅ **Complete** - Fully implemented and tested
- 🟡 **In Progress** - Partially implemented
- 🔴 **Planned** - Designed but not implemented
- ⚠️ **Deprecated** - Old system, being replaced

### 4. **Relationship Diagrams**
Key pages include visual diagrams showing:
- Post Type → Channel → Content Format relationships
- Workflow Stage → Substage → UI Interface flow
- Automation System → Script → Log file connections

---

## Page Structure Template

Each KB page follows this structure:

```markdown
# [Page Title]

**Status:** ✅ Complete | 🟡 In Progress | 🔴 Planned  
**Last Updated:** 2026-01-18  
**Related:** [Links to related sections]

---

## Overview
[Brief description of what this is]

## How It Works
[Explanation of functionality]

## UI Access
- **Primary Interface:** [Link to main UI page]
- **Related Interfaces:** [Links to related UI pages]

## Configuration
[Configuration details if applicable]

## Development Status
- ✅ Feature X - Complete
- 🟡 Feature Y - In Progress
- 🔴 Feature Z - Planned

## Related Systems
- [Link to related KB section]
- [Link to technical doc]

## Technical Details
[Link to detailed technical reference in /docs]
```

---

## Implementation Approach

### Phase 1: Structure & Navigation
1. Create KB blueprint (`blueprints/knowledge_base.py`)
2. Create base template with left sidebar
3. Implement hierarchical navigation system
4. Create index page with system overview

### Phase 2: Core Content Pages
1. **Content Types Section**
   - Post Types Overview
   - Individual post type pages
   - Cross-references to channels

2. **Output Channels Section**
   - Channel overview
   - Individual channel pages
   - Post type → channel mappings

3. **Management Interfaces Section**
   - Interface overview
   - Individual interface pages
   - Workflow stage connections

### Phase 3: Advanced Content
1. **Workflows & Automation**
   - Workflow system documentation
   - Automation system details
   - Status tracking

2. **Backend Systems**
   - Database architecture
   - API documentation
   - Service integration

3. **Data Models**
   - Configuration system
   - Relationship diagrams

### Phase 4: Enhancement
1. Search functionality
2. Relationship diagrams (visual)
3. Development status dashboard
4. Quick reference cards

---

## Technical Implementation

### File Structure
```
blueprints/
└── knowledge_base.py          # KB routes and logic

templates/
└── knowledge_base/
    ├── base.html              # Base template with sidebar
    ├── index.html             # Home page
    ├── content_types/
    │   ├── overview.html
    │   ├── themed.html
    │   ├── recipe.html
    │   └── ...
    ├── channels/
    │   ├── overview.html
    │   ├── blog.html
    │   ├── facebook.html
    │   └── ...
    └── interfaces/
        ├── overview.html
        ├── planning.html
        └── ...

static/
└── css/
    └── knowledge_base.css      # KB-specific styles

static/
└── js/
    └── knowledge_base.js      # Navigation, search, etc.
```

### Data Source
- **Primary**: Parse existing `/docs` markdown files
- **Secondary**: Extract from codebase (blueprints, configs)
- **Status**: Maintain status indicators in KB content files

### Navigation System
- **JavaScript-based**: Collapsible sidebar, active state tracking
- **URL-based**: `/kb/content-types/themed` for deep linking
- **Breadcrumbs**: Auto-generated from URL path

---

## Example Pages

### 1. Post Types Overview
**URL:** `/kb/content-types/overview`

**Content:**
- Table of all post types with status
- Quick links to each type
- Post type → Channel matrix
- Development status summary

**Links:**
- Individual post type pages
- Channel pages
- Workflow pages

### 2. Weekly Content (Word/Phrase/Insult)
**URL:** `/kb/content-types/weekly-content`

**Content:**
- Overview of weekly content system
- Three subtypes (word, phrase, insult)
- Automation workflow diagram
- Calendar integration
- Facebook posting process

**Links:**
- `/kb/channels/facebook` - Facebook channel details
- `/kb/interfaces/monitoring` - Monitoring system
- `/kb/workflows/weekly-automation` - Automation details
- `/docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md` - Technical docs

**UI Links:**
- `/planning/posts/{id}/calendar/view` - Calendar interface
- `/monitoring/report` - Monitoring dashboard

### 3. Management Interfaces Overview
**URL:** `/kb/interfaces/overview`

**Content:**
- Table of all interfaces
- Interface → Post Type matrix
- Interface → Workflow Stage mapping
- Quick access links

---

## Benefits

1. **Discoverability**: Easy to find what you're looking for
2. **Context**: See how everything connects
3. **Status**: Know what's complete vs. in progress
4. **Navigation**: Quick access to related systems
5. **Onboarding**: New developers can understand the system quickly
6. **Reference**: Quick lookup for common tasks

---

## Next Steps

1. **Review & Refine**: Review this proposal and refine structure
2. **Prioritize**: Decide which sections to build first
3. **Implement**: Start with Phase 1 (structure & navigation)
4. **Populate**: Add content progressively
5. **Iterate**: Refine based on usage

---

## Questions for Discussion

1. **Structure**: Does this hierarchy make sense? Any missing sections?
2. **Navigation**: Is the left sidebar + content area the right approach?
3. **Content Depth**: How detailed should each page be?
4. **Status Tracking**: How should we maintain status indicators?
5. **Integration**: Should KB pages be editable through the UI?
6. **Search**: Should search be full-text or tag-based?
