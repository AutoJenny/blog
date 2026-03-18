# Planning Area Roadmap

## Overview

This document outlines the roadmap for the new Planning area in BlogForge CMS, designed to replace the current linear workflow with a collaborative, iterative development process that supports human-AI collaboration at every step.

## Current State Analysis

### Existing Planning Structure (Legacy)
The current planning area follows a rigid, linear approach:
- **Overview** - General post information
- **Idea** - Basic concept development
- **Research** - Fact gathering
- **Structure** - Content organization
- **Old Interface** - Legacy workflow access

### Problems with Current Approach
- **Too Linear**: Rigid step-by-step progression doesn't match creative process
- **One-Shot Generation**: LLM generates final output without human refinement
- **Limited Collaboration**: Minimal human input and iteration
- **Artificial Steps**: Granular steps that don't reflect real workflow
- **No Strategic Planning**: Missing content calendar and strategic oversight

## New Planning Area Structure

### Level 1: Main Planning Stages

#### 1. Content Calendar
**Purpose**: Strategic content planning and idea generation
**Focus**: When to post, what topics to cover, seasonal relevance
**Output**: Scheduled posts with idea seeds

#### 2. Concept Development
**Purpose**: Develop core idea and content structure
**Focus**: Refine ideas, organize topics, plan sections
**Output**: Detailed content blueprint ready for authoring

#### 3. Research & Resources
**Purpose**: Gather knowledge and visual assets
**Focus**: Find sources, plan images, verify facts
**Output**: Research materials and visual concepts

### Level 2: Sub-stages for Each Main Stage

#### Content Calendar Sub-stages:
- **Calendar View** - Monthly/weekly planning interface
- **Idea Generation** - LLM suggests topics based on season/trends
- **Content Gaps** - Identify missing topics and opportunities
- **Schedule Management** - Plan publishing timeline

#### Concept Development Sub-stages:
- **Basic Proposal** - LLM expands idea seed into focused concept
- **Topic Brainstorming** - Generate 50+ topic ideas for curation
- **Section Planning** - Organize topics into 6-8 thematic sections
- **Content Outline** - Structure sections with themes and flow

#### Research & Resources Sub-stages:
- **Source Research** - Find authoritative resources for each section
- **Visual Planning** - Conceptualize distinct images per section
- **Image Prompts** - Generate specific image generation instructions
- **Fact Verification** - Cross-check key information

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Establish new planning structure and basic functionality

#### Database Schema Updates
- Create new planning stage tables
- Migrate existing workflow data
- Add content calendar tables
- Update field mappings

#### New Planning Blueprint
- Create `blueprints/planning.py` with new structure
- Implement main stage routes
- Add sub-stage navigation
- Create basic templates

#### Content Calendar MVP
- Monthly/weekly calendar view
- Basic post scheduling
- LLM-powered idea generation
- Simple drag-and-drop interface

### Phase 2: Concept Development (Weeks 3-4)
**Goal**: Implement collaborative concept development workflow

#### Basic Proposal System
- LLM prompt for expanding idea seeds
- Human editing and refinement interface
- Save/load proposal drafts
- Version control for iterations

#### Topic Brainstorming
- LLM generates 50+ topic ideas
- Human curation interface (select/delete/add)
- Batch operations for efficiency
- Topic categorization and tagging

#### Section Planning
- LLM groups topics into thematic sections
- Human reorganization interface
- Section title and description editing
- Theme overlap detection and suggestions

### Phase 3: Research & Resources (Weeks 5-6)
**Goal**: Implement research and visual planning capabilities

#### Source Research
- Web search integration for authoritative sources
- Source quality scoring and filtering
- Quote extraction and organization
- Link categorization and management

#### Visual Planning
- Image concept generation for each section
- Style consistency checking
- Layout variation suggestions
- Color palette coordination

#### Image Prompt Generation
- Specific prompts for image generation LLMs
- Style and composition guidelines
- Text integration planning
- Batch prompt generation

### Phase 4: Integration & Polish (Weeks 7-8)
**Goal**: Integrate with existing systems and add polish

#### Authoring Integration
- Seamless handoff to authoring stage
- Export planning data for content creation
- Progress tracking across stages
- Quality assurance checks

#### User Experience
- Intuitive navigation between stages
- Progress indicators and status tracking
- Quick actions and shortcuts
- Mobile-responsive design

#### Performance & Reliability
- Optimize LLM API calls
- Implement caching for generated content
- Error handling and recovery
- Performance monitoring

## Technical Implementation

### Database Schema

#### New Tables
```sql
-- Content Calendar
content_calendar (
    id, post_id, scheduled_date, status, idea_seed, 
    seasonal_context, priority, notes
)

-- Planning Stages
planning_stage (
    id, name, description, stage_order, is_active
)

planning_substage (
    id, stage_id, name, description, substage_order, is_active
)

-- Concept Development
concept_proposal (
    id, post_id, basic_proposal, target_audience, 
    value_proposition, working_titles, status
)

topic_ideas (
    id, post_id, idea_text, category, rating, 
    is_selected, created_at
)

section_planning (
    id, post_id, section_name, theme_description, 
    topics_included, topics_avoided, order_index
)

-- Research & Resources
research_sources (
    id, post_id, section_id, source_url, title, 
    credibility_score, quote_text, category
)

visual_concepts (
    id, post_id, section_id, concept_description, 
    style_notes, layout_suggestions, color_palette
)

image_prompts (
    id, post_id, section_id, prompt_text, 
    style_guidelines, composition_notes
)
```

### API Endpoints

#### Content Calendar
- `GET /planning/calendar` - Calendar view
- `POST /planning/calendar/generate-ideas` - LLM idea generation
- `PUT /planning/calendar/schedule` - Update post schedule

#### Concept Development
- `POST /planning/concept/proposal` - Generate basic proposal
- `POST /planning/concept/brainstorm` - Generate topic ideas
- `PUT /planning/concept/curate` - Update topic selection
- `POST /planning/concept/sections` - Generate section planning

#### Research & Resources
- `POST /planning/research/sources` - Find research sources
- `POST /planning/research/visuals` - Generate visual concepts
- `POST /planning/research/prompts` - Create image prompts

### Frontend Components

#### Calendar Interface
- Monthly/weekly calendar grid
- Drag-and-drop post scheduling
- LLM idea generation panel
- Content gap analysis display

#### Concept Development
- Collaborative editing interface
- Topic curation with batch operations
- Section planning with reorganization
- Real-time collaboration features

#### Research Interface
- Source discovery and management
- Visual concept planning
- Image prompt generation
- Fact verification tools

## Success Metrics

### User Experience
- **Reduced Time to First Draft**: 50% reduction in time from idea to structured content
- **Increased Collaboration**: 80% of posts involve human refinement at each step
- **Improved Content Quality**: Measurable improvement in content structure and depth

### Technical Performance
- **Response Time**: <2 seconds for LLM generation requests
- **Reliability**: 99% uptime for planning area
- **Scalability**: Support for 100+ concurrent planning sessions

### Content Strategy
- **Consistent Posting**: 95% adherence to content calendar
- **Seasonal Relevance**: 80% of posts align with seasonal events
- **Content Diversity**: Balanced coverage across topic categories

## Future Enhancements

### Advanced Features (Post-MVP)
- **Scoring System**: Rate and train LLM suggestions
- **Template Learning**: LLM learns from user preferences
- **Collaboration Tools**: Multi-user planning sessions
- **Analytics Integration**: Track planning effectiveness
- **AI Assistant**: Proactive suggestions and recommendations

### Integration Opportunities
- **Social Media Planning**: Extend to social content calendar
- **SEO Integration**: Factor in search trends and keywords
- **Performance Tracking**: Connect planning to post performance
- **Content Series**: Plan multi-part content series

## Migration Strategy

### Data Migration
1. **Preserve Existing Data**: Migrate all current workflow data
2. **Map Old to New**: Create mapping from old steps to new stages
3. **Gradual Transition**: Allow access to both old and new systems
4. **User Training**: Provide documentation and training materials

### Rollout Plan
1. **Internal Testing**: Test with core team members
2. **Beta Release**: Limited release to select users
3. **Full Migration**: Complete transition to new system
4. **Legacy Cleanup**: Remove old workflow system

## Conclusion

The new Planning area represents a fundamental shift from linear, one-shot content generation to a collaborative, iterative development process. This approach better reflects how content creators actually work while leveraging AI as a creative partner rather than a replacement for human judgment.

The phased implementation approach ensures we can deliver value incrementally while building toward a comprehensive content planning and development system that supports both strategic content planning and detailed content development.
