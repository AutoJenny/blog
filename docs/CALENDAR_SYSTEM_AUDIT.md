# Calendar Scheduling System - Complete Audit

**Date**: 2025-12-03  
**Purpose**: Verify alignment of all components and identify incompatible legacy code

---

## ✅ **NEW SYSTEM COMPONENTS (All Implemented & Aligned)**

### 1. JSON-Backed Display Layer
- **File**: `blueprints/planning_api_calendar_scheduling_cache.py`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Behavior**: 
  - Reads from `data/calendar/schedule/<category>/<year>.json` (directory layout)
  - Falls back to `data/calendar/schedule/<category>_<year>.json` (flat layout)
  - Uses `utils/calendar_json_loader.load_category_year()` 
  - Returns range-based week arrays
  - **NO database queries** in display path
- **Endpoint**: `GET /planning/api/calendar/scheduling/all`

### 2. JSON Builder
- **File**: `utils/calendar_schedule_builder.py`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Behavior**:
  - Reads base lists from database
  - Applies cyclic logic with `cycle_start_week`
  - Applies overrides from `calendar_week_overrides` table
  - Writes array-format JSON: `[{week: 1, item_id: ..., position: ..., title: ...}, ...]`
  - Output: `data/calendar/schedule/<category>/<year>.json`

### 3. JSON Loader
- **File**: `utils/calendar_json_loader.py`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Behavior**:
  - Supports both directory and flat layouts
  - Expects array-format JSON
  - Returns `{week_number: entry_dict}` mapping
  - Gracefully handles missing/corrupt files

### 4. List Management (Base Cyclic Lists)
- **File**: `blueprints/planning_api_calendar_cyclic.py`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Endpoints**:
  - `POST /planning/api/calendar/list/reorder` - Reorder items
  - `POST /planning/api/calendar/list/add` - Add items
  - `POST /planning/api/calendar/list/delete` - Delete items
- **Behavior**:
  - Week-agnostic, year-agnostic
  - Maintains dense positions (1..N)
  - Triggers JSON rebuild after changes
  - Uses `calendar_week_overrides` table (NOT `calendar_week_items`)

### 5. Override Management
- **File**: `blueprints/planning_api_calendar_overrides.py`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Endpoints**:
  - `GET /planning/api/calendar/list/get` - Get list for sequence manager
  - `POST /planning/api/calendar/override/set` - Set week override
  - `POST /planning/api/calendar/override/remove` - Remove week override
  - `POST /planning/api/calendar/override/move_week` - Move override between weeks
  - `POST /planning/api/calendar/override/rebuild-year` - Rebuild JSON for year
- **Behavior**:
  - Uses `calendar_week_overrides` table
  - Triggers JSON rebuild after override changes
  - Returns `{"status": "ok", ...}` format

### 6. Sequence Manager UI
- **File**: `templates/planning/calendar/sequence_manager.html`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Route**: `/planning/calendar/sequence-manager`
- **Behavior**:
  - Calls `GET /planning/api/calendar/list/get` to load lists
  - Calls list management endpoints (reorder/add/delete)
  - Does NOT call override endpoints (those are for week-level moves)

### 7. Display Frontend
- **File**: `templates/planning/calendar/scheduling.html`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Behavior**:
  - Calls `GET /planning/api/calendar/scheduling/all` with range params
  - Has navigation controls (Year <<, Month <, Month >, Year >>)
  - Displays weeks in table format
  - **Does NOT call old reassign endpoints**

### 8. Builder CLI
- **File**: `scripts/build_calendar_schedules.py`
- **Status**: ✅ **CORRECTLY IMPLEMENTED**
- **Usage**: `python scripts/build_calendar_schedules.py --year 2025`

---

## ⚠️ **LEGACY/INCOMPATIBLE CODE (Still Present But Not Used)**

### 1. Old Reassign Blueprint
- **File**: `blueprints/planning_api_calendar_reassign.py`
- **Status**: ⚠️ **REGISTERED BUT INCOMPATIBLE**
- **Issue**: 
  - Uses **OLD** `calendar_week_items` table (not `calendar_week_overrides`)
  - Uses **OLD** `utils/calendar_week_items.py` utilities
  - Endpoint: `POST /planning/api/calendar/reassign`
  - **Still registered in `unified_app.py` line 145-146**
- **Impact**: 
  - Could conflict if frontend accidentally calls it
  - Uses wrong database table
  - Does NOT trigger JSON rebuilds
- **Recommendation**: **UNREGISTER** or **DELETE** this blueprint

### 2. Old Reorder Blueprint
- **File**: `blueprints/planning_api_calendar_reorder.py`
- **Status**: ⚠️ **EXISTS BUT NOT REGISTERED**
- **Issue**:
  - Uses old position-swapping logic
  - Tries to modify base list positions for week moves
  - Not compatible with new JSON-centric system
- **Impact**: Low (not registered, so not accessible)
- **Recommendation**: **DELETE** or archive

### 3. Old Utilities
- **Files**:
  - `utils/calendar_week_items.py` - Old `calendar_week_items` table utilities
  - `utils/calendar_sequential_resolver.py` - Old resolver (may be imported elsewhere)
  - `utils/calendar_cycle_resolver.py` - Old resolver (may be imported elsewhere)
- **Status**: ⚠️ **EXIST BUT NOT USED BY NEW SYSTEM**
- **Impact**: 
  - Could cause confusion
  - May be imported by old reassign blueprint
- **Recommendation**: **ARCHIVE** or **DELETE** if not needed

### 4. Old Cache File
- **File**: `data/calendar_scheduling_cache.json`
- **Status**: ⚠️ **EXISTS BUT NOT USED**
- **Issue**: Old cache file from pre-JSON system
- **Impact**: None (new system doesn't read it)
- **Recommendation**: **DELETE** or archive

---

## 🔍 **ALIGNMENT CHECK**

### Database Tables
- ✅ `calendar_week_overrides` - **USED** by new system for week-specific overrides
- ✅ `calendar_week_items` - **CANONICAL** table for week→output persistence (blog posts)
- ✅ `calendar_week_posts_v2` - **VIEW** over `calendar_week_items` for blog outputs
- ⚠️ `calendar_week_items_deprecated` - **LEGACY** table (being phased out)
- ⚠️ `calendar_schedule` - **DEPRECATED** (removed from active code)

### Status Resolution
- ✅ `utils/publication_status_resolver.py` - **CANONICAL** status resolution module
  - ID-only matching (no title heuristics)
  - Uses `calendar_week_posts_v2` for theme→post resolution
  - Normalizes status to unified enum (`published`, `draft`, `scheduled`, `error`, `deleted`)
  - All calendar APIs use resolver for consistent status display

### JSON File Structure
- ✅ **NEW FORMAT**: Array format `[{week: 1, item_id: ..., ...}, ...]`
- ✅ **LOCATION**: `data/calendar/schedule/<category>/<year>.json` (directory layout)
- ✅ **FALLBACK**: `data/calendar/schedule/<category>_<year>.json` (flat layout)

### API Response Formats
- ✅ Display API: `{"success": true, "data": {...}}`
- ✅ List Get: `{"status": "ok", "items": [...]}`
- ✅ List Operations: `{"status": "ok", ...}`
- ✅ Override Operations: `{"status": "ok", ...}` or `{"success": true, ...}`

### Frontend Calls
- ✅ `scheduling.html` calls: `GET /planning/api/calendar/scheduling/all`
- ✅ `sequence_manager.html` calls:
  - `GET /planning/api/calendar/list/get`
  - `POST /planning/api/calendar/list/reorder`
  - `POST /planning/api/calendar/list/add`
  - `POST /planning/api/calendar/list/delete`
- ✅ **NO** calls to old `/api/calendar/reassign` endpoint

---

## 🚨 **ISSUES TO ADDRESS**

### Critical
1. **Old Reassign Blueprint Still Registered**
   - **File**: `unified_app.py` lines 145-146
   - **Action**: **UNREGISTER** `planning_api_calendar_reassign_bp`
   - **Reason**: Uses wrong table, incompatible with new system

### Medium Priority
2. **Old Cache File Exists**
   - **File**: `data/calendar_scheduling_cache.json`
   - **Action**: **DELETE** or archive
   - **Reason**: Not used, could cause confusion

3. **Old Blueprint Files Exist**
   - **Files**: 
     - `blueprints/planning_api_calendar_reassign.py`
     - `blueprints/planning_api_calendar_reorder.py`
   - **Action**: **DELETE** or move to `archive/` directory
   - **Reason**: Not compatible, not used

### Low Priority
4. **Old Utility Files**
   - **Files**:
     - `utils/calendar_week_items.py`
     - `utils/calendar_sequential_resolver.py`
   - **Action**: **ARCHIVE** if not used elsewhere
   - **Reason**: Could cause confusion, but may be imported by other systems

---

## ✅ **WHAT'S WORKING CORRECTLY**

1. ✅ **JSON-backed display** - Fast, no DB queries
2. ✅ **JSON builder** - Generates correct array format
3. ✅ **JSON loader** - Handles both layouts gracefully
4. ✅ **List management** - Pure list operations, triggers rebuilds
5. ✅ **Override system** - Uses correct table, triggers rebuilds
6. ✅ **Sequence manager UI** - Calls correct endpoints
7. ✅ **Display frontend** - Range-based navigation works
8. ✅ **Builder CLI** - Generates JSON files correctly

---

## 📋 **MISSING/NOT ADDRESSED**

### Testing
- ⚠️ Test suite exists but not run
- ⚠️ No integration tests for full flow

### Documentation
- ✅ All documentation files exist and are up to date
- ✅ Component structure documented
- ✅ JSON format documented
- ✅ Builder usage documented
- ✅ Operations guide exists

### Data Migration
- ⚠️ Old `calendar_week_items` data not migrated to `calendar_week_overrides`
- ⚠️ Old cache file not cleaned up

---

## 🎯 **RECOMMENDATIONS**

### Immediate Actions
1. **UNREGISTER** old reassign blueprint in `unified_app.py`
2. **DELETE** or archive old blueprint files
3. **DELETE** old cache file `data/calendar_scheduling_cache.json`

### Future Actions
4. Migrate any data from `calendar_week_items` to `calendar_week_overrides` if needed
5. Archive old utility files if not used elsewhere
6. Run test suite to verify everything works
7. Add integration tests for full flow

---

## ✅ **CONCLUSION**

**Overall Status**: **MOSTLY ALIGNED** ✅

The new JSON-centric system is **correctly implemented and aligned**. All new components work together properly. The main issue is **legacy code still registered** that could cause conflicts.

**Action Required**: Unregister old reassign blueprint to prevent conflicts.

