# Phase 1: Core Functionality Checklist

## Pre-Implementation Analysis

### Current State Assessment
- [ ] **File Status**: `templates/launchpad/social_media_command_center.html` has duplicate functions
- [ ] **Function Count**: 19 functions present (same as old system)
- [ ] **API Endpoints**: Updated to `/launchpad/api/queue` (correct)
- [ ] **Critical Issue**: Functions exist but implemented incorrectly

### Risk Assessment
- [ ] **High Risk**: Removing duplicates could break existing functionality
- [ ] **Medium Risk**: Changing function implementations could affect other parts of system
- [ ] **Low Risk**: Adding missing features (status validation, content previews)

## 1.1 Remove Duplicate Functions

### Pre-Analysis Checklist:
- [x] **Identify all duplicate functions** (use grep to find duplicates)
- [x] **Map function locations** (line numbers for each duplicate)
- [x] **Determine which implementation to keep** (compare old vs new)

### Implementation Analysis:
**Keep Second Set (lines 1143-1404)**:
- `addQueueParams` (line 1143) - Same implementation
- `getModuleUrl` (line 1152) - Same implementation  
- `reschedulePost` (line 1261) - Same implementation
- `postNow` (line 1278) - **BETTER** - uses `item.generated_content` vs `item.content`
- `postNowConfirmed` (line 1296) - Same implementation
- `cancelPost` (line 1392) - Same implementation
- `cancelPostConfirmed` (line 1404) - Same implementation

**Remove First Set (lines 725-1035)**:
- All functions in this range are duplicates with inferior implementations
- [x] **Check for dependencies** (other functions calling duplicates)

### Dependency Analysis:
**HTML onclick calls use `id` parameter**:
- `onclick="reschedulePost(${item.id})"`
- `onclick="postNow(${item.id})"`
- `onclick="cancelPost(${item.id})"`

**Function signatures need to match**:
- Old system: `function postNow(id)`
- New system: `function postNow(itemId)` ❌ MISMATCH

**Resolution**: Change second set functions to use `id` parameter instead of `itemId`
- [ ] **Backup current file** (create backup before changes)

### Duplicate Function Analysis:
**Duplicates Found**:
- `addQueueParams` (lines 937 and 1143)
- `getModuleUrl` (lines 946 and 1152)
- `reschedulePost` (lines 725 and 1261)
- `postNow` (lines 742 and 1278)
- `postNowConfirmed` (lines 760 and 1296)
- `cancelPost` (lines 865 and 1392)
- `cancelPostConfirmed` (lines 877 and 1404)

**Missing from first set**:
- `editPost` (only exists at line 1244)

**Total functions**: 26 (should be 19)

### Implementation Checklist:
- [ ] **Create backup**: `cp templates/launchpad/social_media_command_center.html templates/launchpad/social_media_command_center.html.backup`
- [ ] **Remove first set of duplicates** (lines ~937-1035)
- [ ] **Remove second set of duplicates** (lines ~1143-1404)
- [ ] **Keep only correct implementations** (lines ~1143-1404)
- [ ] **Test file syntax** (check for JavaScript errors)
- [ ] **Verify function count** (should still be 19 functions)

### Validation Checklist:
- [ ] **No duplicate function names** (grep should show each function once)
- [ ] **File loads without errors** (check browser console)
- [ ] **All functions accessible** (test function calls in console)

## 1.2 Fix Function Implementations

### Function-by-Function Analysis:

#### editPost(itemId)
- [ ] **Current**: Uses hardcoded URL `/launchpad/syndication/facebook/product_post`
- [ ] **Required**: Use `getModuleUrl()` for dynamic routing
- [ ] **Current**: Uses `window.location.href` (same window)
- [ ] **Required**: Use `window.open(urlWithParams, '_blank')` (new tab)
- [ ] **Current**: Basic error handling
- [ ] **Required**: Platform-specific error messages

#### reschedulePost(itemId)
- [ ] **Current**: Placeholder implementation
- [ ] **Required**: Use `getModuleUrl()` + `addQueueParams()` + `window.open()`
- [ ] **Current**: Generic error message
- [ ] **Required**: Platform-specific error messages

#### postNow(itemId)
- [ ] **Current**: Missing status validation
- [ ] **Required**: Add `if (item.status !== 'ready')` check
- [ ] **Current**: Basic confirmation dialog
- [ ] **Required**: Add content preview and warning message
- [ ] **Current**: Generic error handling
- [ ] **Required**: Better error handling and status updates

#### cancelPost(itemId)
- [ ] **Current**: Basic confirmation dialog
- [ ] **Required**: Add content preview and platform-specific messaging
- [ ] **Current**: Generic error handling
- [ ] **Required**: Better error handling and status updates

### Implementation Checklist:
- [ ] **Fix editPost()** (use getModuleUrl, window.open, better errors)
- [ ] **Fix reschedulePost()** (implement proper routing)
- [ ] **Fix postNow()** (add status validation, content preview)
- [ ] **Fix cancelPost()** (add content preview, better messaging)
- [ ] **Verify getModuleUrl()** (check all URL mappings)
- [ ] **Test addQueueParams()** (verify URL parameter handling)

### Validation Checklist:
- [ ] **Edit button opens correct page in new tab**
- [ ] **Reschedule button opens correct page in new tab**
- [ ] **Post now shows status validation**
- [ ] **Post now shows content preview in confirmation**
- [ ] **Cancel shows content preview in confirmation**
- [ ] **All error messages are platform-specific**

## Success Criteria

### Phase 1 Success:
- [ ] **No duplicate functions**
- [ ] **All functions work correctly**
- [ ] **Navigation behavior is correct**
- [ ] **No JavaScript errors**

## Rollback Plan

### If Phase 1 Fails:
- [ ] **Restore from backup**: `cp templates/launchpad/social_media_command_center.html.backup templates/launchpad/social_media_command_center.html`
- [ ] **Test basic functionality**
- [ ] **Analyze what went wrong**
- [ ] **Revise approach**
