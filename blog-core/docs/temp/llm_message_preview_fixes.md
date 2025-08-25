# LLM Message Preview System Fixes

## Overview

This document details the issues identified in the LLM message preview system and provides implementation guidance for fixes. The core issue is that context inputs (basic_idea and idea_scope) are not appearing in the preview despite being selected in the left panel.

## 1. Field Detection Issues

### Problem
In `enhanced_llm_message_manager.js`, the `detectAvailableFields()` method has inconsistent handling of different field types:

1. `basic_idea` is only updating accordion content but not being added to `fields.inputs`
2. `idea_scope` has correct push to `fields.inputs` but may have visibility check issues
3. `section_headings` may be incorrectly filtered by display check

### Implementation Fix

```javascript
// In detectAvailableFields():

// 1. Add basic_idea to fields.inputs (missing)
if (basicIdeaTextarea) {
    const basicIdeaContent = basicIdeaTextarea.value || '';
    this.updateAccordionContent('basic_idea', basicIdeaContent);
    if (basicIdeaContent.trim()) {
        fields.inputs.push({
            id: 'basic_idea',
            name: this.mapFieldToDisplayName('basic_idea'),
            content: basicIdeaContent,
            source: 'purple_module'
        });
    }
}

// 2. Remove display check for idea_scope
if (ideaScopeTextarea) {
    const ideaScopeContent = ideaScopeTextarea.value || '';
    this.updateAccordionContent('idea_scope', ideaScopeContent);
    if (ideaScopeContent.trim()) {
        fields.inputs.push({
            id: 'idea_scope',
            name: this.mapFieldToDisplayName('idea_scope'),
            content: ideaScopeContent,
            source: 'purple_module'
        });
    }
}

// 3. Keep display check only for optional fields like section_headings
if (sectionHeadingsTextarea && sectionHeadingsTextarea.style.display !== 'none') {
    // Existing section_headings handling
}
```

## 2. Field Mapping Issues

### Problem
The `mapFieldToDisplayName` function may not be consistently used across all field types, leading to mismatched field names in the preview.

### Implementation Fix

1. Audit all field name mappings
2. Ensure consistent use of `mapFieldToDisplayName`
3. Update field name mapping table in database if needed

## Testing Protocol

### 1. Basic Context Fields Test
```bash
# Test basic idea and idea scope always included
curl -X POST http://localhost:5000/api/workflow/llm/direct \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test prompt",
    "post_id": 1,
    "step": "idea",
    "fields": {
      "basic_idea": "Test basic idea",
      "idea_scope": "Test idea scope"
    }
  }' | jq
```

Expected: Both fields should appear in preview regardless of display state

### 2. Optional Fields Test
```bash
# Test section headings when visible
curl -X POST http://localhost:5000/api/workflow/llm/direct \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test prompt",
    "post_id": 1,
    "step": "idea",
    "fields": {
      "basic_idea": "Test basic idea",
      "idea_scope": "Test idea scope",
      "section_headings": [{"title": "Test Section", "description": "Test Description"}]
    }
  }' | jq
```

Expected: Section headings should only appear when display !== 'none'

### 3. Field Order Test
```bash
# Test field ordering in preview
curl -X POST http://localhost:5000/api/workflow/llm/direct \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test prompt with all fields",
    "post_id": 1,
    "step": "idea",
    "fields": {
      "basic_idea": "Test basic idea",
      "idea_scope": "Test idea scope",
      "section_headings": [{"title": "Test Section", "description": "Test Description"}],
      "custom_field": "Test custom field"
    }
  }' | jq
```

Expected: Fields should appear in correct order with proper display names

## Implementation Steps

1. Back up current state:
   ```bash
   git stash push -m "Pre-LLM-preview-fix backup"
   ```

2. Apply JavaScript fixes:
   - Update `detectAvailableFields()`
   - Verify field mapping consistency
   - Test with browser console logging

3. Verify database field mappings:
   ```sql
   SELECT * FROM field_mappings WHERE field_type IN ('basic_idea', 'idea_scope', 'section_headings');
   ```

4. Run all test cases above

5. Verify UI behavior:
   - Check accordion updates
   - Verify preview content
   - Test field selection/deselection

## Rollback Plan

If issues occur:
```bash
git stash pop  # Restore pre-fix state
./scripts/dev/restart_flask_dev.sh  # Restart server
```

## Related Documentation

- [LLM Message System Reference](../reference/workflow/llm_message_system.md)
- [LLM Panel Documentation](../reference/workflow/llm_panel.md)
- [Workflow API Endpoints](../reference/workflow/endpoints.md) 