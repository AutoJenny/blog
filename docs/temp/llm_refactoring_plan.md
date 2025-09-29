# LLM Module Refactoring - Technical Documentation

## Project Overview
Refactor the LLM functionality from the ideas and brainstorm pages into reusable components while maintaining full functionality.

## Current State Analysis

### Pages to Refactor
1. `/planning/posts/60/calendar/ideas` - Idea Generation page
2. `/planning/posts/60/concept/brainstorm` - Topic Brainstorming page

### Current LLM Functionality
Both pages have similar LLM components:
- LLM prompt display with provider info
- Editable prompt functionality
- Content generation with loading states
- Results display
- Error handling

## Phase 1: Research & Understanding

### Step 1: Analyze Current Template Structure
- [ ] Document base template blocks
- [ ] Understand how JavaScript is loaded
- [ ] Map current LLM functionality in both pages

### Step 2: API Endpoint Analysis
- [ ] Document existing LLM API endpoints
- [ ] Understand response formats
- [ ] Test all endpoints work correctly

### Step 3: Current Functionality Documentation
- [ ] Document what each page does
- [ ] Understand the user workflow
- [ ] Identify shared vs page-specific functionality

## Phase 2: Design & Planning

### Step 1: Component Design
- [ ] Design shared HTML structure
- [ ] Plan CSS organization
- [ ] Design JavaScript module architecture

### Step 2: Integration Planning
- [ ] Plan how pages will use shared components
- [ ] Design configuration system
- [ ] Plan rollback strategy

## Phase 3: Implementation

### Step 1: Create Shared Components
- [ ] Create shared HTML template
- [ ] Create shared CSS
- [ ] Create shared JavaScript module

### Step 2: Refactor Ideas Page
- [ ] Update ideas page to use shared components
- [ ] Test thoroughly
- [ ] Verify all functionality works

### Step 3: Refactor Brainstorm Page
- [ ] Update brainstorm page to use shared components
- [ ] Test thoroughly
- [ ] Verify all functionality works

## Phase 4: Verification

### Step 1: Full Testing
- [ ] Test all functionality on both pages
- [ ] Check for regressions
- [ ] Performance verification

### Step 2: Documentation
- [ ] Update technical documentation
- [ ] Document any changes made
- [ ] Create rollback instructions

## Rollback Strategy
- Each phase will be committed separately
- Can rollback to any previous phase
- Full system restore available at any time

## Testing Requirements
- Every change must be tested before proceeding
- No "should work" statements - must verify functionality
- Test both pages after each change
- Verify API endpoints work correctly
- Check browser console for errors

## Success Criteria
- Both pages work identically to before refactoring
- No regressions in functionality
- Code is more maintainable
- Shared components are reusable
- Full rollback capability maintained
