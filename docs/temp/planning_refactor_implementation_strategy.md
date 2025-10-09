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

### Current State Analysis
- **File**: `blueprints/planning.py` (1,279 lines)
- **Routes**: 44 routes (too many for one file)
- **Functions**: 48 functions (too many for one file)
- **Code Lines**: 1,030 lines (exceeds 300-line guideline)

### Proposed File Structure
- **`planning_views.py`** - All `@bp.route` view functions (~400 lines)
- **`planning_api.py`** - All API endpoints (~400 lines)
- **`planning_calendar.py`** - Calendar-specific functionality (~200 lines)
- **`planning_concept.py`** - Concept development functionality (~200 lines)
- **`planning_llm.py`** - LLM service and prompt handling (~100 lines)

### Implementation Protocol

#### Step 1: Audit and Categorize
- [ ] Map all 44 routes to their logical groupings
- [ ] Identify dependencies between functions
- [ ] Document shared imports and utilities
- [ ] Plan file boundaries to minimize dependencies

#### Step 2: Create New Files
- [ ] Create each new file with appropriate imports
- [ ] Move functions maintaining exact signatures
- [ ] Ensure all dependencies are properly imported
- [ ] Test that each file can be imported independently

#### Step 3: Update Main File
- [ ] Replace moved functions with imports from new files
- [ ] Maintain all existing route registrations
- [ ] Ensure blueprint registration still works
- [ ] **TEST**: Verify application starts successfully

#### Step 4: Test Functionality
- [ ] Test all routes and endpoints
- [ ] Verify no functionality is lost
- [ ] Check for any import or dependency issues
- [ ] **IF SUCCESS**: Proceed to Phase 3
- [ ] **IF FAILURE**: Rollback changes, investigate issues

#### Rollback Procedure
If any step fails:
1. Restore original `blueprints/planning.py`
2. Delete new files
3. Test that application works as before
4. Document failure point and lessons learned
5. Consult before proceeding with alternative approach

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
- [ ] Main planning.py file under 300 lines
- [ ] All functionality distributed across logical files
- [ ] Application works identically to before
- [ ] No functionality lost

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
