# Format System Guide

## Overview 
This guide documents the format specification system that works alongside the workflow prompt system. The format system ensures consistent data structures for both input and output across workflow stages.

## Format Components

### 1. Format Templates
Format templates define the structure and validation rules for data at each workflow step. They can be either input formats (defining expected input structure) or output formats (defining required output structure).

Example format template for blog section structure:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Section title"
    },
    "content": {
      "type": "string",
      "description": "Main section content"
    },
    "key_points": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of key points covered in the section"
    }
  },
  "required": ["title", "content"]
}
```

## Format Structure

### Input Formats
Input formats define the expected structure of data before processing:

- **Type Information**: Clear specification of data types (string, number, boolean, object, array)
- **Field Requirements**: Which fields are required vs optional
- **Validation Rules**: Length limits, numeric ranges, pattern matching
- **Field References**: Support for [data:field_name] dynamic references
- **Documentation**: Clear descriptions of each field's purpose

Example input format:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "The main title for this section",
      "minLength": 10,
      "maxLength": 100
    },
    "keywords": {
      "type": "array",
      "description": "Key topics to cover",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "maxItems": 5
    },
    "reference_data": {
      "type": "string",
      "description": "Reference content from previous step",
      "pattern": "^\\[data:[a-z_]+\\]$"
    }
  },
  "required": ["title", "keywords"]
}
```

### Output Formats
Output formats define the required structure for processed results:

- **Strict Structure**: Exact specification of expected output fields
- **Type Enforcement**: Strong typing for consistent output
- **Nested Objects**: Support for complex data structures
- **Array Handling**: Clear specification of list structures
- **Format Instructions**: Additional formatting requirements

Example output format:
```json
{
  "type": "object",
  "properties": {
    "sections": {
      "type": "array",
      "description": "Generated content sections",
      "items": {
        "type": "object",
        "properties": {
          "heading": {
            "type": "string",
            "description": "Section heading"
          },
          "content": {
            "type": "string",
            "description": "Main content",
            "minLength": 100
          },
          "key_points": {
            "type": "array",
            "description": "Key takeaways",
            "items": {
              "type": "string"
            },
            "minItems": 2
          }
        },
        "required": ["heading", "content", "key_points"]
      },
      "minItems": 1
    },
    "summary": {
      "type": "string",
      "description": "Brief overview of all sections",
      "maxLength": 500
    }
  },
  "required": ["sections", "summary"]
}
```

### Format Validation
The format system uses JSON Schema Draft 7 for validation:

1. **Type Validation**
   - Ensures correct data types
   - Validates nested structures
   - Checks array contents

2. **Constraint Validation**
   - String lengths (minLength, maxLength)
   - Numeric ranges (minimum, maximum)
   - Array sizes (minItems, maxItems)
   - Pattern matching (regex patterns)

3. **Structural Validation**
   - Required fields presence
   - Object property names
   - Array item formats

4. **Error Reporting**
   - Clear error messages
   - Field path identification
   - Validation suggestions

## Integration with Workflow Steps

### Format Configuration
Each workflow step can have associated input and output formats. This configuration determines how data is structured and validated during step processing.

### Applying Formats
1. Input Validation
   - Before processing, input data is validated against the input format
   - Field references are resolved
   - Data is transformed if needed

2. Output Validation
   - LLM output is validated against the output format
   - Output is transformed to match required structure
   - Validation errors trigger reprocessing

## Best Practices

1. **Format Design**
   - Keep formats simple and focused
   - Use clear field names and descriptions
   - Include validation rules where needed
   - Document format requirements clearly

2. **Field References**
   - Use consistent naming patterns
   - Document reference sources
   - Validate reference existence
   - Handle missing references gracefully

3. **Validation**
   - Implement comprehensive validation
   - Provide clear error messages
   - Include validation suggestions
   - Handle edge cases appropriately

4. **Integration**
   - Test format compatibility
   - Validate data transformations
   - Monitor validation performance
   - Log validation failures 