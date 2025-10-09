# Planning Refactor Implementation Strategy

## Overview
This document outlines a robust, failsafe process to refactor the planning system by:
1. Deprecating the backup file and extracting its functionality
2. Breaking up the oversized main planning.py file
3. Addressing hardcoded content contamination

## Core Principles
- **NEVER proceed on hunches** - Always consult before continuing when predicted results fail
- **Always test at each step** - Verify functionality before proceeding
- **Always have rollback capability** - Maintain ability to restore working state
- **Document everything** - Record all changes and decisions

---

## PHASE 1: DEPRECATE BACKUP FILE

### Current State Analysis
- **File**: `blueprints/planning_original_backup.py` (5,112 lines)
- **Status**: Still actively imported and used
- **Active Imports**: 4 functions imported into `blueprints/planning.py`:
  - `api_sections_title` (lines 4064-4594, 530 lines)
  - `api_save_sections` (lines 4595-5094, 499 lines) 
  - `get_post_data` (lines 371-1093, 722 lines)
  - `api_design_section_structure` (lines 1094-4063, 2,969 lines)

### Contamination Status
- **CONFIRMED CONTAMINATED**: `api_design_section_structure` (uses "Section Structure Design" prompt with hardcoded "Scottish autumn folklore")
- **CLEAN**: `api_sections_title`, `api_save_sections`, `get_post_data` (no contamination)

### Implementation Protocol

#### Step 1: Audit and Record
- [ ] Document exact function signatures and dependencies
- [ ] Identify all database queries and external dependencies
- [ ] Map all API endpoints that call these functions
- [ ] Record current functionality and expected behavior

#### Step 2: Extract Functions
- [ ] Create `blueprints/planning_sections.py` for section-related functions
- [ ] Create `blueprints/planning_data.py` for data retrieval functions
- [ ] Copy functions with exact same signatures and logic
- [ ] Ensure all imports and dependencies are included

#### Step 3: Test Extraction
- [ ] Verify new files can be imported without errors
- [ ] Test that functions work identically to originals
- [ ] Document any differences or issues found

#### Step 4: Rename Backup File
- [ ] Rename `blueprints/planning_original_backup.py` to `blueprints/planning_original_backup_deprecated.py`
- [ ] **EXPECTED RESULT**: Application should break (import errors)
- [ ] **TEST**: Verify application fails to start
- [ ] **IF SUCCESS**: Proceed to Step 5
- [ ] **IF FAILURE**: Investigate why application still works, document findings

#### Step 5: Update Import Links
- [ ] Update `blueprints/planning.py` to import from new files instead of backup
- [ ] Update all function calls to use new imports
- [ ] **TEST**: Verify application starts successfully
- [ ] **TEST**: Verify all affected endpoints work correctly
- [ ] **IF SUCCESS**: Proceed to Step 6
- [ ] **IF FAILURE**: Rollback imports, restore backup filename, investigate issues

#### Step 6: Final Verification
- [ ] Test all affected endpoints thoroughly
- [ ] Verify no functionality is lost
- [ ] Document any issues or differences found
- [ ] **IF SUCCESS**: Proceed to Phase 2
- [ ] **IF FAILURE**: Rollback to working state, reassess approach

#### Rollback Procedure
If any step fails:
1. Restore `blueprints/planning_original_backup.py` filename
2. Restore original imports in `blueprints/planning.py`
3. Test that application works as before
4. Document failure point and lessons learned
5. Consult before proceeding with alternative approach

---

## PHASE 2: BREAK UP MAIN PLANNING FILE

### Current State Analysis (UPDATED)
- **File**: `blueprints/planning.py` (222 lines) ✅ **REDUCED FROM 1,279 LINES**
- **Routes**: 22 routes (reduced from 44)
- **Functions**: 22 functions (reduced from 48)
- **Code Lines**: 222 lines ✅ **UNDER 300-LINE TARGET**

### Current Micro-File Structure (PARTIALLY IMPLEMENTED)
- ✅ **`planning_views.py`** - View functions (created)
- ✅ **`planning_calendar_clean.py`** - Calendar views (created)
- ✅ **`planning_concept.py`** - Concept views (created)
- ✅ **`planning_api_calendar.py`** - Calendar APIs (created)
- ✅ **`planning_api_posts.py`** - Basic post APIs (created)
- ✅ **`planning_api_post_specific.py`** - Post-specific APIs (created)
- ✅ **`planning_api_brainstorm.py`** - Brainstorm APIs (created)
- ✅ **`planning_api_prompts.py`** - Prompt APIs (created)
- ✅ **`planning_llm.py`** - LLM service (created)
- ✅ **`planning_sections.py`** - Section APIs (created)
- ✅ **`planning_data.py`** - Data retrieval (created)

### CRITICAL ISSUES IDENTIFIED

#### Missing API Endpoints (CAUSING PAGE FAILURES)
The section-structure page requires these endpoints that are **MISSING** from current `planning.py`:

1. **`/api/sections/design-structure` (POST)** - Generate section structure
2. **`/api/sections/design-structure/<post_id>` (GET)** - Get existing structure
3. **`/api/sections/title` (POST)** - Generate section titles
4. **`/api/sections/save` (POST)** - Save sections
5. **`/api/sections/allocate-topics` (POST)** - Allocate topics to sections
6. **`/api/sections/allocate-topics/<post_id>` (GET)** - Get existing allocation

#### Files Still Referencing Deprecated Backup
- `blueprints/planning_minimal_modular.py` - Line 243
- `blueprints/planning_working_modular.py` - Line 160  
- `blueprints/planning_modular_simple.py` - Line 20

#### Import Errors in Current Structure
- Missing `ideas_week_func` import in `planning.py` line 84
- Incomplete import on line 23 (missing function name)

### CORRECTED IMPLEMENTATION PROTOCOL

#### Step 1: Fix Current Import Errors
- [ ] Fix incomplete import on line 23 of `planning.py`
- [ ] Fix missing `ideas_week_func` import on line 84
- [ ] **TEST**: Verify application starts without errors

#### Step 2: Add Missing API Endpoints
- [ ] Add `/api/sections/design-structure` (POST) endpoint
- [ ] Add `/api/sections/design-structure/<post_id>` (GET) endpoint  
- [ ] Add `/api/sections/title` (POST) endpoint
- [ ] Add `/api/sections/save` (POST) endpoint
- [ ] Add `/api/sections/allocate-topics` (POST) endpoint
- [ ] Add `/api/sections/allocate-topics/<post_id>` (GET) endpoint
- [ ] **TEST**: Verify section-structure page works completely

#### Step 3: Clean Up Deprecated References
- [ ] Remove references to `planning_original_backup` from modular files
- [ ] Delete unused modular files that still reference deprecated backup
- [ ] **TEST**: Verify no files reference deprecated backup

#### Step 4: Final Verification
- [ ] Test all planning pages work correctly
- [ ] Verify section-structure page generates proper content (not hardcoded)
- [ ] Test all API endpoints respond correctly
- [ ] **IF SUCCESS**: Proceed to Phase 3
- [ ] **IF FAILURE**: Rollback changes, investigate issues

#### Rollback Procedure
If any step fails:
1. Restore `blueprints/planning_backup_before_phase2.py` as `planning.py`
2. Delete all micro-files created during Phase 2
3. Test that application works as before Phase 2
4. Document failure point and lessons learned
5. Consult before proceeding with alternative approach

---

## DETAILED AUDIT RESULTS

### Phase 1 Status: ✅ COMPLETED SUCCESSFULLY
- **Backup file**: `planning_original_backup.py` → `planning_original_backup_deprecated.py` ✅
- **Functions extracted**: All 4 functions moved to micro-files ✅
- **No active imports**: Main `planning.py` no longer imports from backup ✅
- **Application works**: All functionality preserved ✅

### Phase 2 Status: ⚠️ PARTIALLY COMPLETED WITH CRITICAL ISSUES

#### ✅ SUCCESSES
- **File size reduced**: 1,279 lines → 222 lines (under 300-line target)
- **Micro-files created**: 11 micro-files successfully created
- **Routes reduced**: 44 routes → 22 routes
- **Functions reduced**: 48 functions → 22 functions

#### ❌ CRITICAL FAILURES
1. **Missing API Endpoints**: 6 critical endpoints missing from `planning.py`
2. **Import Errors**: 2 import errors preventing clean startup
3. **Deprecated References**: 3 files still reference deprecated backup
4. **Page Failures**: Section-structure page cannot function without missing endpoints

#### 🔍 SPECIFIC ISSUES IDENTIFIED

**Missing API Endpoints** (from template analysis):
```javascript
// These calls in section_structure.html will FAIL:
fetch('/planning/api/sections/design-structure', {method: 'POST'})  // MISSING
fetch('/planning/api/sections/design-structure/${postId}')           // MISSING

// These calls in topic_allocation.html will FAIL:
fetch('/planning/api/sections/allocate-topics/${postId}')            // MISSING
```

**Import Errors** (from current planning.py):
```python
# Line 23: Incomplete import
from blueprints.planning_api_brainstorm import  # MISSING FUNCTION NAME

# Line 84: Missing function
return ideas_week_func(week_number)  # ideas_week_func NOT IMPORTED
```

**Files with Deprecated References**:
- `planning_minimal_modular.py:243` - Dynamic import from backup
- `planning_working_modular.py:160` - Dynamic import from backup  
- `planning_modular_simple.py:20` - Direct import from backup

### ROOT CAUSE ANALYSIS
**Phase 2 was executed sloppily** because:
1. **Insufficient template analysis** - Didn't identify all required API endpoints
2. **Incomplete import verification** - Didn't verify all imports work
3. **Inadequate cleanup** - Left references to deprecated files
4. **Reactive fixing** - Fixed issues as they appeared instead of preventing them

### RECOMMENDED APPROACH
**Complete Phase 2 properly** before proceeding to Phase 3:
1. Fix import errors first
2. Add all missing API endpoints
3. Clean up deprecated references
4. Verify section-structure page works completely
5. Then proceed to Phase 3 (hardcoded content)

---

## PHASE 3: ADDRESS HARDCODED CONTENT

### Current State Analysis
- **CONFIRMED CONTAMINATED**: "Section Structure Design" prompt
- **Location**: Database table `llm_prompt` 
- **Contamination**: Hardcoded "Scottish autumn folklore" content
- **Impact**: Forces specific content instead of using user input

### Implementation Protocol

#### Step 1: Consult on Approach
- [ ] Present detailed analysis of contamination
- [ ] Propose specific remediation approach
- [ ] Get explicit approval before proceeding
- [ ] Document agreed approach

#### Step 2: Implement Fix
- [ ] Update contaminated prompt in database
- [ ] Test that new prompt works correctly
- [ ] Verify no other functionality is affected
- [ ] **TEST**: Verify section structure generation uses user input

#### Step 3: Final Verification
- [ ] Test affected functionality thoroughly
- [ ] Verify contamination is eliminated
- [ ] Document changes made
- [ ] **IF SUCCESS**: Mark phase complete
- [ ] **IF FAILURE**: Rollback changes, investigate issues

#### Rollback Procedure
If any step fails:
1. Restore original prompt in database
2. Test that functionality works as before
3. Document failure point and lessons learned
4. Consult before proceeding with alternative approach

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Backup file renamed to `_deprecated`
- [ ] All functionality extracted to new files
- [ ] Application works identically to before
- [ ] No active imports from backup file

### Phase 2 Complete When:
- [ ] Main planning.py file under 300 lines ✅ **ACHIEVED (222 lines)**
- [ ] All functionality distributed across logical files ✅ **ACHIEVED (11 micro-files)**
- [ ] Application works identically to before ❌ **FAILED (missing endpoints)**
- [ ] No functionality lost ❌ **FAILED (section-structure page broken)**
- [ ] **NEW**: All required API endpoints present and working
- [ ] **NEW**: No import errors in main planning.py
- [ ] **NEW**: No references to deprecated backup file

### Phase 3 Complete When:
- [ ] Hardcoded content contamination eliminated
- [ ] Section structure generation uses user input
- [ ] No other functionality affected
- [ ] Contamination cannot recur

---

## Risk Mitigation

### Before Each Phase:
- [ ] Create git commit checkpoint
- [ ] Document current working state
- [ ] Identify rollback procedures

### During Each Phase:
- [ ] Test after each significant change
- [ ] Document any issues or unexpected behavior
- [ ] Consult before proceeding when predicted results fail

### After Each Phase:
- [ ] Verify all functionality works
- [ ] Create git commit checkpoint
- [ ] Document lessons learned

---

## Notes
- This process prioritizes safety over speed
- Each phase must be completely successful before proceeding
- Consultation is required when any predicted result fails
- Rollback capability must be maintained at all times
