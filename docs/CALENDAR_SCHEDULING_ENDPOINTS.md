# Calendar Scheduling System - All Endpoints

## Frontend Calls (from `templates/planning/calendar/scheduling.html`)

### 1. GET `/planning/api/calendar/scheduling/all`
- **Purpose**: Fetch all scheduling data for all 52 weeks
- **Method**: GET
- **Query Params**: `_t={timestamp}` (cache busting)
- **Response**: JSON with weeks array containing schedule items
- **Handler**: `blueprints/planning_api_calendar_scheduling_cache.py::api_calendar_scheduling_all()`
- **Route**: Defined in `blueprints/planning.py` line 291

### 2. POST `/planning/api/calendar/override/set`
- **Purpose**: Set a manual override for a specific week
- **Method**: POST
- **Request Body**:
  ```json
  {
    "category": "theme|recipe|profile_product|profile_surname|weekly_word|weekly_phrase",
    "item_id": 42,
    "year": 2025,
    "week": 49
  }
  ```
- **Response**: `{"success": true, "message": "Override set for week 2025-W49"}`
- **Handler**: `blueprints/planning_api_calendar_cyclic.py::api_override_set()`
- **Route**: `/planning/api/calendar/override/set` (defined in `planning_api_calendar_cyclic.py` line 226)

### 3. POST `/planning/api/calendar/override/remove`
- **Purpose**: Remove a manual override for a specific week
- **Method**: POST
- **Request Body**:
  ```json
  {
    "category": "theme|recipe|profile_product|profile_surname|weekly_word|weekly_phrase",
    "year": 2025,
    "week": 49
  }
  ```
- **Response**: `{"success": true, "message": "Override removed for week 2025-W49"}`
- **Handler**: `blueprints/planning_api_calendar_cyclic.py::api_override_remove()`
- **Route**: `/planning/api/calendar/override/remove` (defined in `planning_api_calendar_cyclic.py` line 294)

---

## Backend Endpoints (Available but NOT currently used by frontend)

### 4. POST `/planning/api/calendar/list/reorder`
- **Purpose**: Reorder an item in a cyclic list
- **Method**: POST
- **Request Body**:
  ```json
  {
    "category": "theme|recipe|profile_product|profile_surname|weekly_word|weekly_phrase",
    "item_id": 42,
    "new_pos": 7
  }
  ```
- **Response**: `{"success": true, "message": "Item reordered"}`
- **Handler**: `blueprints/planning_api_calendar_cyclic.py::api_list_reorder()`
- **Route**: `/planning/api/calendar/list/reorder` (defined in `planning_api_calendar_cyclic.py` line 38)
- **Status**: ✅ Implemented but NOT called by frontend

### 5. POST `/planning/api/calendar/list/add`
- **Purpose**: Add an item to a cyclic list
- **Method**: POST
- **Request Body**:
  ```json
  {
    "category": "theme|recipe|profile_product|profile_surname|weekly_word|weekly_phrase",
    "item_id": 42,
    "insert_pos": 7  // Optional, defaults to end
  }
  ```
- **Response**: `{"success": true, "message": "Item added"}`
- **Handler**: `blueprints/planning_api_calendar_cyclic.py::api_list_add()`
- **Route**: `/planning/api/calendar/list/add` (defined in `planning_api_calendar_cyclic.py` line 118)
- **Status**: ✅ Implemented but NOT called by frontend

### 6. POST `/planning/api/calendar/list/delete`
- **Purpose**: Delete an item from a cyclic list
- **Method**: POST
- **Request Body**:
  ```json
  {
    "category": "theme|recipe|profile_product|profile_surname|weekly_word|weekly_phrase",
    "item_id": 42
  }
  ```
- **Response**: `{"success": true, "message": "Item deleted"}`
- **Handler**: `blueprints/planning_api_calendar_cyclic.py::api_list_delete()`
- **Route**: `/planning/api/calendar/list/delete` (defined in `planning_api_calendar_cyclic.py` line 173)
- **Status**: ✅ Implemented but NOT called by frontend

---

## Blueprint Registration

### Main Blueprint
- **File**: `blueprints/planning_api_calendar_cyclic.py`
- **Blueprint Name**: `planning_api_calendar_cyclic`
- **URL Prefix**: `/planning`
- **Registered In**: `unified_app.py` line 133-134

### Route Structure
All routes are prefixed with `/planning` because:
1. The blueprint has `url_prefix='/planning'`
2. The blueprint is registered in `unified_app.py` without an additional prefix

**Full URLs**:
- `/planning/api/calendar/list/reorder`
- `/planning/api/calendar/list/add`
- `/planning/api/calendar/list/delete`
- `/planning/api/calendar/override/set`
- `/planning/api/calendar/override/remove`
- `/planning/api/calendar/scheduling/all`

---

## Currently Active Endpoints (Used by Frontend)

1. ✅ **GET** `/planning/api/calendar/scheduling/all` - Load scheduling data
2. ✅ **POST** `/planning/api/calendar/override/set` - Set override (called when reassigning)
3. ✅ **POST** `/planning/api/calendar/override/remove` - Remove override (called when reassigning)

---

## Old/Unused Endpoints (Still Exist but NOT Used)

These endpoints exist but are NOT called by the scheduling page:

- `POST /planning/api/calendar/reorder` (old reorder system)
- `GET /planning/api/calendar/position-for-week` (old position calculation)
- `POST /planning/api/calendar/reassign` (old reassign system)

These are defined in:
- `blueprints/planning_api_calendar_reorder.py`
- `blueprints/planning_api_calendar_reassign.py`

---

## Summary

**Frontend is calling**:
- ✅ `/planning/api/calendar/scheduling/all` (GET)
- ✅ `/planning/api/calendar/override/set` (POST)
- ✅ `/planning/api/calendar/override/remove` (POST)

**Backend has available** (but frontend doesn't use):
- `/planning/api/calendar/list/reorder` (POST)
- `/planning/api/calendar/list/add` (POST)
- `/planning/api/calendar/list/delete` (POST)

**Issue**: The frontend is calling the correct endpoints, but the button click handler may not be firing.

