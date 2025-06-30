# LLM Format System Implementation Plan

## Overview 
This document outlines the implementation plan for adding format specifications to the LLM prompt system. The format system will handle both input and output formats, providing clear data contracts for LLM interactions.

## Current Architecture
- System Prompts: Define LLM role and context
- Task Prompts: Provide specific instructions
- Basic text/JSON handling embedded in prompts

## Proposed Architecture

### 1. Three-Component Prompt Structure

```plaintext
Prompt Components:
1. System Prompt (Role/Context)
   - Who the LLM is
   - General expertise/tone
   - Universal constraints

2. Task Prompt (Instructions)
   - Specific task requirements
   - Input data references
   - Task-specific constraints

3. Format Specification (Data Contract)
   - Input format and parsing rules
   - Output format and requirements
   - Examples and validation rules
```

### 2. Format Template System

#### Format Template Structure
```json
{
  "name": "string",
  "description": "string",
  "version": "string",
  "type": "bidirectional|input_only|output_only",
  "input": {
    "format": "json|text|structured",
    "schema": {},
    "parsing_instructions": "string",
    "example": {},
    "validation_rules": []
  },
  "output": {
    "format": "json|text|structured",
    "schema": {},
    "formatting_rules": [],
    "example": {},
    "validation_rules": []
  },
  "notes": {
    "usage": "string",
    "limitations": "string",
    "compatibility": []
  }
}
```

#### Example Format Template
```json
{
  "name": "blog_section_structure",
  "description": "Format for blog post section structuring",
  "version": "1.0",
  "type": "bidirectional",
  "input": {
    "format": "json",
    "schema": {
      "facts": [
        {
          "topic": "string",
          "content": "string"
        }
      ],
      "themes": ["string"],
      "target_length": "number"
    },
    "parsing_instructions": "Facts array contains topic-content pairs. Themes are primary article themes.",
    "example": {
      "facts": [
        {
          "topic": "history",
          "content": "The quaich dates back to 16th century Scotland"
        }
      ],
      "themes": ["hospitality"],
      "target_length": 1500
    }
  },
  "output": {
    "format": "json",
    "schema": {
      "sections": [
        {
          "title": "string",
          "word_count": "number",
          "key_facts": ["string"],
          "main_theme": "string"
        }
      ],
      "total_words": "number"
    },
    "formatting_rules": [
      "Use UK English spelling",
      "Section titles in title case",
      "Facts distributed evenly"
    ],
    "example": {
      "sections": [
        {
          "title": "The Ancient Origins of the Quaich",
          "word_count": 300,
          "key_facts": ["16th century origin"],
          "main_theme": "history"
        }
      ],
      "total_words": 300
    }
  }
}
```

### 3. Database Schema

```sql
CREATE TABLE llm_format_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL,
    type VARCHAR(20) NOT NULL,
    input_format VARCHAR(20),
    input_schema JSONB,
    input_instructions TEXT,
    output_format VARCHAR(20) NOT NULL,
    output_schema JSONB,
    output_rules JSONB,
    examples JSONB,
    notes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workflow_step_format (
    step_id INTEGER REFERENCES workflow_step_entity(id),
    format_template_id INTEGER REFERENCES llm_format_template(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (step_id)
);
```

### 4. UI Components

#### Format Panel
- Format type selector (default: UK English Prose)
- Input format display (if applicable)
- Output format display
- Format preview with examples
- Validation status indicator

#### Format Management
- Format template library
- Format version control
- Format compatibility checker
- Format validation tools

### 5. Implementation Phases

#### Phase 1: Core Format System
1. Create database tables
2. Implement basic format templates
3. Add format panel to UI
4. Basic format validation

#### Phase 2: Enhanced Features
1. Format version control
2. Format compatibility checking
3. Advanced validation rules
4. Format template library

#### Phase 3: Workflow Integration
1. Chain-aware format compatibility
2. Multi-step format validation
3. Format-based error handling
4. Format analytics

### 6. Benefits

1. **Data Quality**
   - Clear data contracts
   - Consistent formats
   - Better validation

2. **Workflow Efficiency**
   - Reliable task chaining
   - Reduced errors
   - Better debugging

3. **Maintainability**
   - Centralized format management
   - Version control
   - Clear documentation

4. **Extensibility**
   - Support for new formats
   - Multi-modal ready
   - Provider agnostic

### 7. Future Considerations

1. **Multi-modal Support**
   - Image format specifications
   - Diagram generation rules
   - Mixed-media formats

2. **Advanced Features**
   - Format conversion tools
   - Format analytics
   - Format optimization

3. **Integration Points**
   - External API formats
   - Third-party validators
   - Format marketplaces

## Next Steps

1. Review and approve database schema
2. Create initial format templates
3. Implement UI components
4. Develop validation system
5. Test with existing workflow 