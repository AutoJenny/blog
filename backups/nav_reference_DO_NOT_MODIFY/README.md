# PROTECTED NAVIGATION REFERENCE - DO NOT MODIFY

This directory contains the WORKING reference implementation of the blog's navigation structure as of June 2024. This includes:

## Core Navigation Components
- Complete nav module structure from `modules/nav/`
- Workflow navigation template (`_workflow_nav.html`)
- Navigation logic (`navigation.py`)
- Homepage implementation with working stage/substage structure (`index.html`)

## Critical URL Structure
The navigation system uses the following URL patterns that MUST be preserved:
- Workflow stages: `/workflow/posts/<post_id>/<stage>`
- Workflow substages: `/workflow/posts/<post_id>/<stage>/<substage>`

## Stage Structure
1. Planning
   - Idea
   - Research 
   - Structure

2. Authoring
   - Content
   - Meta Info
   - Images

3. Publishing
   - Preflight
   - Launch
   - Syndication

## WARNING
This is a reference implementation that MUST NOT be modified. If the navigation system breaks in the main codebase:

1. Use this as your reference for the correct structure
2. You can also restore from git tag: `workflow-nav-restore-v1`
3. DO NOT modify files in this directory - they serve as a permanent reference

Created: June 2024 