# Authoring LLM Module Modularization Plan

## Current State Analysis
- **Working system**: `llm_module_authoring.html` is functional but has HTML/JS duplication
- **Problem**: JavaScript overwrites static HTML content (title changes from "Prompt (Authoring)" to "Prompt")
- **Goal**: Eliminate duplication while preserving all existing functionality

## Root Cause
The LLM module JavaScript dynamically updates the `#prompt-title` element, overwriting static HTML changes. This creates confusion about what controls what.

## Implementation Strategy: Minimal Intervention

### Phase 1: Preserve Existing Structure (LOW RISK)
**Goal**: Keep the working accordion system intact

1. **Keep the original HTML structure** - don't change the accordion system
2. **Keep the original CSS classes** - maintain existing styling
3. **Keep the original JavaScript integration** - maintain existing functionality
4. **Only fix the title duplication issue**

### Phase 2: Fix HTML/JS Duplication (LOW RISK)
**Goal**: Make the title persistent without breaking functionality

**Option A: CSS-Only Solution**
- Use CSS `::before` or `::after` pseudo-elements to add "(Authoring)" text
- Keep original "Prompt: Loading..." text intact
- JavaScript can update the base text, CSS adds the suffix

**Option B: JavaScript Modification**
- Modify the JavaScript that updates the title to preserve "(Authoring)"
- Find the specific function that overwrites the title
- Add logic to append "(Authoring)" to any title updates

**Option C: Template Variable**
- Pass a template variable from Flask to control the title
- JavaScript uses the template variable instead of hardcoded text

### Phase 3: Validation (LOW RISK)
**Goal**: Ensure no functionality is broken

1. **Test accordion functionality** - open/close works
2. **Test prompt loading** - data loads correctly
3. **Test generation** - generate button works
4. **Test edit functionality** - edit prompts work
5. **Test section selection** - persistence works

## Recommended Approach: Option A (CSS-Only)

### Why CSS-Only is Best:
- **Zero risk** of breaking JavaScript functionality
- **No changes** to existing JavaScript code
- **Simple implementation** - just CSS
- **Easy to revert** if issues arise
- **Preserves all existing behavior**

### Implementation Steps:
1. **Add CSS rule** to append "(Authoring)" to the prompt title
2. **Test thoroughly** to ensure no visual issues
3. **Verify functionality** remains intact

### CSS Implementation:
```css
#prompt-title::after {
    content: " (Authoring)";
}
```

## Risk Assessment
- **Phase 1**: ZERO RISK - no changes to working system
- **Phase 2**: LOW RISK - CSS-only solution, no JavaScript changes
- **Phase 3**: ZERO RISK - testing only

## Success Criteria
- ✅ Title shows "Prompt (Authoring): Loading..." and persists
- ✅ All existing functionality works unchanged
- ✅ No JavaScript errors or broken features
- ✅ Accordion system works perfectly
- ✅ Prompt loading and generation work
- ✅ Section selection persistence works

## Rollback Plan
If any issues arise:
1. **Remove CSS rule** - instant revert
2. **Git reset** - back to working state
3. **No JavaScript changes** - nothing to break

## Timeline
- **Phase 1**: 0 minutes (no changes)
- **Phase 2**: 5 minutes (CSS addition)
- **Phase 3**: 10 minutes (testing)
- **Total**: 15 minutes maximum

## Key Principles
1. **Minimal intervention** - fix only the duplication issue
2. **Preserve functionality** - don't break what works
3. **CSS-first approach** - avoid JavaScript changes
4. **Easy rollback** - simple to undo if needed
5. **Test thoroughly** - verify everything works

## What NOT to Do
- ❌ Don't copy imaging functionality
- ❌ Don't change the accordion system
- ❌ Don't modify JavaScript unless absolutely necessary
- ❌ Don't add new features or complexity
- ❌ Don't break existing functionality

## Next Steps
1. Implement CSS-only solution
2. Test thoroughly
3. Document results
4. Commit if successful
