# Phase 2.2: API Endpoint Designs

## **CLEAN START APPROACH CONFIRMED**

Based on analysis, we're proceeding with new specialized tables rather than extending existing ones:
- `ui_user_preferences` - Keep for user preferences (theme, settings)
- `ui_session_state` - Migrate data to new tables, then deprecate
- `workflow_step_context_config` - Keep for step configuration

## **API ENDPOINT DESIGN**

### **1. Selection State Management**

#### **GET /api/ui/selection-state**
- **Purpose**: Retrieve current selections for a user/page
- **Parameters**: 
  - `user_id` (optional, defaults to 1)
  - `page_type` (e.g., 'product_post', 'blog_post')
  - `selection_type` (e.g., 'product', 'blog_post', 'section')
- **Response**: Array of selection objects
- **Example**:
```json
{
  "selections": [
    {
      "id": 1,
      "user_id": 1,
      "page_type": "product_post",
      "selection_type": "product",
      "selected_id": 123,
      "selected_data": {"name": "Tartan Leggings", "sku": "TLL001"},
      "created_at": "2025-09-25T10:30:00Z"
    }
  ]
}
```

#### **POST /api/ui/selection-state**
- **Purpose**: Set a selection
- **Body**:
```json
{
  "user_id": 1,
  "page_type": "product_post",
  "selection_type": "product",
  "selected_id": 123,
  "selected_data": {"name": "Tartan Leggings", "sku": "TLL001"}
}
```

#### **DELETE /api/ui/selection-state**
- **Purpose**: Clear selections
- **Parameters**: `user_id`, `page_type`, `selection_type` (all optional for filtering)

### **2. UI State Management**

#### **GET /api/ui/ui-state**
- **Purpose**: Retrieve UI state (accordions, tabs, etc.)
- **Parameters**: `user_id`, `page_type`, `state_key`
- **Response**: UI state object
- **Example**:
```json
{
  "ui_states": [
    {
      "id": 1,
      "user_id": 1,
      "page_type": "product_post",
      "state_key": "accordion_states",
      "state_data": {
        "products_browser": "expanded",
        "ai_generation": "collapsed",
        "posting_controls": "expanded"
      },
      "created_at": "2025-09-25T10:30:00Z"
    }
  ]
}
```

#### **POST /api/ui/ui-state**
- **Purpose**: Update UI state
- **Body**:
```json
{
  "user_id": 1,
  "page_type": "product_post",
  "state_key": "accordion_states",
  "state_data": {
    "products_browser": "expanded",
    "ai_generation": "collapsed"
  }
}
```

### **3. Workflow State Management**

#### **GET /api/ui/workflow-state**
- **Purpose**: Retrieve workflow state (LLM context, processing)
- **Parameters**: `user_id`, `page_type`, `workflow_id`
- **Response**: Workflow state object
- **Example**:
```json
{
  "workflow_states": [
    {
      "id": 1,
      "user_id": 1,
      "page_type": "product_post",
      "workflow_id": "content_generation",
      "state_data": {
        "process_id": 1,
        "generated_content": "Amazing tartan leggings...",
        "generation_status": "completed",
        "llm_context": {"model": "mistral", "temperature": 0.7}
      },
      "created_at": "2025-09-25T10:30:00Z"
    }
  ]
}
```

#### **POST /api/ui/workflow-state**
- **Purpose**: Update workflow state
- **Body**:
```json
{
  "user_id": 1,
  "page_type": "product_post",
  "workflow_id": "content_generation",
  "state_data": {
    "process_id": 1,
    "generated_content": "Amazing tartan leggings...",
    "generation_status": "completed"
  }
}
```

### **4. Queue State Management**

#### **GET /api/ui/queue-state**
- **Purpose**: Retrieve queue state and preferences
- **Parameters**: `user_id`, `page_type`, `queue_type`
- **Response**: Queue state object
- **Example**:
```json
{
  "queue_states": [
    {
      "id": 1,
      "user_id": 1,
      "page_type": "product_post",
      "queue_type": "posting_queue",
      "state_data": {
        "queue_data": [...],
        "filter_preferences": {"status": "ready"},
        "display_preferences": {"sort_by": "scheduled_time"}
      },
      "created_at": "2025-09-25T10:30:00Z"
    }
  ]
}
```

#### **POST /api/ui/queue-state**
- **Purpose**: Update queue state
- **Body**:
```json
{
  "user_id": 1,
  "page_type": "product_post",
  "queue_type": "posting_queue",
  "state_data": {
    "queue_data": [...],
    "filter_preferences": {"status": "ready"}
  }
}
```

## **UNIFIED STATE MANAGEMENT**

### **GET /api/ui/state**
- **Purpose**: Get all state for a user/page in one call
- **Parameters**: `user_id`, `page_type`
- **Response**: Combined state object
- **Example**:
```json
{
  "user_id": 1,
  "page_type": "product_post",
  "selections": [...],
  "ui_states": [...],
  "workflow_states": [...],
  "queue_states": [...]
}
```

### **POST /api/ui/state**
- **Purpose**: Update multiple state types in one call
- **Body**:
```json
{
  "user_id": 1,
  "page_type": "product_post",
  "selections": [...],
  "ui_states": [...],
  "workflow_states": [...],
  "queue_states": [...]
}
```

## **ERROR HANDLING**

All endpoints return consistent error responses:
```json
{
  "error": true,
  "message": "Error description",
  "code": "ERROR_CODE",
  "details": {...}
}
```

## **AUTHENTICATION**

- All endpoints require `user_id` (defaults to 1 for single-user system)
- Future: Add proper authentication middleware

## **CACHING STRATEGY**

- No caching initially (ensure data consistency)
- Future: Add Redis caching for frequently accessed state

## **MIGRATION FROM UNAUTHORIZED STORAGE**

### **Phase 1: Create New Tables**
- Create the 4 new tables
- Set up API endpoints

### **Phase 2: Migrate Data**
- Migrate data from `ui_session_state` to new tables
- Update JavaScript to use new API endpoints

### **Phase 3: Remove Unauthorized Storage**
- Remove `localStorage` usage
- Remove `ui_session_state` table
- Remove in-memory state objects

## **NEXT STEPS**

1. Create database migration scripts for new tables
2. Implement API endpoints in Flask blueprints
3. Update JavaScript modules to use new APIs
4. Test migration process
5. Remove unauthorized storage

---

**Status**: Ready for implementation
**Dependencies**: Database table creation (Phase 2.1 completed)
**Next Phase**: Migration strategy design (Phase 2.3)
