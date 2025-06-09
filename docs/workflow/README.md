# Workflow System Documentation

## Overview

The workflow system is a structured content creation pipeline that guides users through the process of creating blog posts from initial idea to final publication. The system is divided into three main stages:

1. **Planning Stage**
   - Idea Generation
   - Research & Fact Gathering
   - Structure Planning

2. **Authoring Stage**
   - Content Drafting
   - Content Refinement
   - Content Review

3. **Publishing Stage**
   - Final Review
   - SEO Optimization
   - Publication

Each stage consists of multiple substages, each with its own specific purpose, inputs, outputs, and LLM actions. The system uses a combination of database fields, LLM actions, and prompt templates to guide the content creation process.

## Documentation Structure

This documentation is organized as follows:

1. [Workflow Overview](overview.md) - Detailed explanation of the entire workflow system
2. [Planning Stage](planning/README.md) - Documentation for the planning stage
   - [Idea Generation](planning/idea.md)
   - [Research & Facts](planning/research.md)
   - [Structure Planning](planning/structure.md)
3. [Authoring Stage](authoring/README.md) - Documentation for the authoring stage
4. [Publishing Stage](publishing/README.md) - Documentation for the publishing stage

## Key Components

Each workflow stage documentation includes:

- Purpose and goals
- Input/Output specifications
- Database fields used
- LLM actions available
- Prompt templates and their components
- Special scripts or utilities
- Error handling and validation
- Integration points with other stages

## Database Integration

The workflow system uses the following key database tables:

- `post_development` - Stores the main content and metadata
- `llm_action` - Defines available LLM actions
- `prompt_template` - Stores prompt templates
- `prompt_part` - Stores reusable prompt components

## LLM Integration

The system uses Ollama for LLM operations, with a focus on:

- Structured prompt templates
- Consistent output formats
- Error handling and retry logic
- Action-specific processing

## Recent Updates

- 2024-06-14: Universal Modular LLM Workflow Panel implementation
- 2024-06-07: Fixed substage handling in post_substage_action
- 2024-05-29: Updated LLM actions to use canonical prompt structure 