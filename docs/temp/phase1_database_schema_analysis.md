# Phase 1.4: Database Schema Analysis for State Storage

**ANALYSIS COMPLETE**: Identified existing tables and fields that can be used for proper state persistence

---

## **EXISTING STATE MANAGEMENT TABLES**

### **1. `ui_session_state` (CURRENT - PROBLEMATIC)**

**Purpose**: Session-based state storage (VIOLATES REQUIREMENTS)
**Status**: ❌ **MUST BE REPLACED** - Session-based, not persistent

**Schema**:
- `id`: integer (PK)
- `session_id`: varchar (NOT NULL) - Session identifier
- `user_id`: integer (nullable) - User identifier  
- `state_key`: varchar (NOT NULL) - State key
- `state_value`: text (nullable) - State value
- `state_type`: varchar (NOT NULL) - Data type
- `expires_at`: timestamp (nullable) - Expiration
- `created_at`: timestamp (nullable)
- `updated_at`: timestamp (nullable)

**Issues**:
- Session-based (data lost when session expires)
- Constraint violations (missing required fields)
- Inconsistent data types
- Not suitable for persistent state

---

### **2. `ui_user_preferences` (EXISTING - GOOD FOUNDATION)**

**Purpose**: User-specific preferences and settings
**Status**: ✅ **CAN BE USED** - Proper persistent storage

**Schema**:
- `id`: integer (PK)
- `user_id`: integer (NOT NULL) - User identifier
- `preference_key`: varchar (NOT NULL) - Preference key
- `preference_value`: text (nullable) - Preference value
- `preference_type`: varchar (NOT NULL) - Data type
- `category`: varchar (nullable) - Preference category
- `is_global`: boolean (nullable) - Global vs user-specific
- `created_at`: timestamp (nullable)
- `updated_at`: timestamp (nullable)

**Usage Potential**:
- UI state preferences (accordion states, tab states)
- User-specific settings
- Global system preferences

---

## **EXISTING CONTENT TABLES (CAN BE EXTENDED)**

### **3. `posting_queue` (EXISTING - GOOD FOR QUEUE STATE)**

**Purpose**: Posting queue management
**Status**: ✅ **ALREADY USED** - Proper persistent storage

**Schema**:
- `id`: integer (PK)
- `product_id`: integer (nullable) - Product reference
- `section_id`: integer (nullable) - Section reference
- `post_id`: integer (nullable) - Post reference
- `content_type`: varchar (nullable) - Content type
- `status`: varchar (nullable) - Queue status
- `generated_content`: text (nullable) - Generated content
- `scheduled_date`: date (nullable) - Scheduled date
- `scheduled_time`: time (nullable) - Scheduled time
- `platform`: varchar (nullable) - Target platform
- `channel_type`: varchar (nullable) - Channel type
- `product_name`: varchar (nullable) - Product name
- `post_title`: varchar (nullable) - Post title
- `section_title`: varchar (nullable) - Section title
- `created_at`: timestamp (nullable)
- `updated_at`: timestamp (nullable)

**Usage**: Already properly used for queue state

---

### **4. `post` (EXISTING - CAN BE EXTENDED)**

**Purpose**: Blog post management
**Status**: ✅ **CAN BE EXTENDED** - Good foundation

**Schema**:
- `id`: integer (PK)
- `title`: varchar (NOT NULL) - Post title
- `slug`: varchar (NOT NULL) - URL slug
- `status`: enum (NOT NULL) - Post status
- `substage_id`: integer (nullable) - Workflow substage
- `created_at`: timestamp (nullable)
- `updated_at`: timestamp (nullable)
- **Plus many other fields...**

**Usage Potential**:
- Post selection state
- Workflow state tracking
- Content generation state

---

### **5. `post_section` (EXISTING - CAN BE EXTENDED)**

**Purpose**: Blog post section management
**Status**: ✅ **CAN BE EXTENDED** - Good foundation

**Schema**:
- `id`: integer (PK)
- `post_id`: integer (NOT NULL) - Post reference
- `section_order`: integer (nullable) - Section order
- `section_heading`: text (nullable) - Section title
- `status`: text (nullable) - Section status
- `polished`: text (nullable) - Polished content
- `draft`: text (nullable) - Draft content
- `image_filename`: varchar (nullable) - Image filename
- `created_at`: timestamp (nullable)
- `updated_at`: timestamp (nullable)

**Usage Potential**:
- Section selection state
- Section generation state
- Section content state

---

## **WORKFLOW TABLES (CAN BE USED FOR STATE)**

### **6. `workflow_stage_entity` (EXISTING)**

**Purpose**: Workflow stage definitions
**Status**: ✅ **CAN BE USED** - For workflow state

**Schema**:
- `id`: integer (PK)
- `name`: varchar (NOT NULL) - Stage name
- `description`: text (nullable) - Stage description
- `stage_order`: integer (NOT NULL) - Stage order

### **7. `workflow_sub_stage_entity` (EXISTING)**

**Purpose**: Workflow substage definitions
**Status**: ✅ **CAN BE USED** - For workflow state

**Schema**:
- `id`: integer (PK)
- `stage_id`: integer (nullable) - Stage reference
- `name`: varchar (NOT NULL) - Substage name
- `description`: text (nullable) - Substage description
- `sub_stage_order`: integer (NOT NULL) - Substage order

### **8. `workflow_step_entity` (EXISTING)**

**Purpose**: Workflow step definitions
**Status**: ✅ **CAN BE USED** - For workflow state

**Schema**:
- `id`: integer (PK)
- `sub_stage_id`: integer (nullable) - Substage reference
- `name`: varchar (NOT NULL) - Step name
- `description`: text (nullable) - Step description
- `step_order`: integer (NOT NULL) - Step order
- `config`: jsonb (nullable) - Step configuration

### **9. `post_workflow_stage` (EXISTING)**

**Purpose**: Post-specific workflow state
**Status**: ✅ **CAN BE USED** - For post workflow state

**Schema**:
- `id`: integer (PK)
- `post_id`: integer (nullable) - Post reference
- `stage_id`: integer (nullable) - Stage reference
- `started_at`: timestamp (nullable) - Stage start time
- `completed_at`: timestamp (nullable) - Stage completion time
- `status`: varchar (nullable) - Stage status
- `input_field`: varchar (nullable) - Input field
- `output_field`: varchar (nullable) - Output field

---

## **MISSING TABLES NEEDED FOR STATE PERSISTENCE**

### **1. `ui_state_persistence` (NEEDED)**

**Purpose**: Persistent UI state storage
**Status**: ❌ **MUST BE CREATED**

**Proposed Schema**:
```sql
CREATE TABLE ui_state_persistence (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    state_type VARCHAR(50) NOT NULL,  -- 'selection', 'ui_state', 'workflow'
    state_category VARCHAR(50) NOT NULL,  -- 'product', 'blog_post', 'queue', 'accordion'
    state_key VARCHAR(100) NOT NULL,  -- Unique key for this state
    state_value JSONB NOT NULL,  -- State data as JSON
    entity_id INTEGER,  -- ID of related entity (post_id, product_id, etc.)
    entity_type VARCHAR(50),  -- Type of related entity
    expires_at TIMESTAMP,  -- Optional expiration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, state_type, state_category, state_key)
);
```

**Usage**:
- Product selections
- Blog post selections
- UI state (accordions, tabs)
- Workflow state
- Queue state

### **2. `ui_selection_state` (NEEDED)**

**Purpose**: Selection state management
**Status**: ❌ **MUST BE CREATED**

**Proposed Schema**:
```sql
CREATE TABLE ui_selection_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    selection_type VARCHAR(50) NOT NULL,  -- 'product', 'blog_post', 'section'
    selected_id INTEGER NOT NULL,  -- ID of selected item
    selected_data JSONB,  -- Additional selection data
    context_data JSONB,  -- Context information
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, selection_type)
);
```

**Usage**:
- Currently selected product
- Currently selected blog post
- Currently selected section
- Selection context and metadata

---

## **MAPPING UNAUTHORIZED STORAGE TO DATABASE FIELDS**

### **localStorage Replacements**:

| **localStorage Key** | **Current Usage** | **Proposed Database Field** | **Table** |
|---------------------|-------------------|------------------------------|-----------|
| `selectedBlogPostId` | Blog post selection | `selected_id` | `ui_selection_state` |
| `sections_selection_post_${postId}` | Section selections | `state_value` | `ui_state_persistence` |
| `sections_accordion_post_${postId}` | Accordion states | `state_value` | `ui_state_persistence` |
| `sections_tabs_post_${postId}` | Tab states | `state_value` | `ui_state_persistence` |
| `accordion_state_${postId}_${sectionId}` | Accordion states | `state_value` | `ui_state_persistence` |
| `element_order_${postId}` | Element order | `state_value` | `ui_state_persistence` |

### **Session State Replacements**:

| **Current Usage** | **Proposed Database Field** | **Table** |
|-------------------|------------------------------|-----------|
| `selected_product_id` | `selected_id` | `ui_selection_state` |
| `last_visited_platform` | `state_value` | `ui_user_preferences` |
| `accordion_state` | `state_value` | `ui_state_persistence` |
| `selected_channel` | `state_value` | `ui_user_preferences` |
| `filter_preferences` | `state_value` | `ui_user_preferences` |

### **In-Memory State Replacements**:

| **Current Usage** | **Proposed Database Field** | **Table** |
|-------------------|------------------------------|-----------|
| `LLM_STATE.context` | `state_value` | `ui_state_persistence` |
| `queueData` | `state_value` | `ui_state_persistence` |
| `selectedData` | `selected_data` | `ui_selection_state` |
| `selectedProduct` | `selected_data` | `ui_selection_state` |
| `selectedSection` | `selected_data` | `ui_selection_state` |

---

## **IMPLEMENTATION STRATEGY**

### **Phase 1**: Create new tables
- `ui_state_persistence` for general state
- `ui_selection_state` for selections

### **Phase 2**: Migrate existing data
- Move `ui_session_state` data to new tables
- Preserve existing functionality

### **Phase 3**: Update application code
- Replace localStorage with database calls
- Replace session state with persistent state
- Replace in-memory state with database state

### **Phase 4**: Remove old tables
- Drop `ui_session_state` table
- Clean up unused code

---

## **BENEFITS OF NEW APPROACH**

1. **True Persistence**: Data survives page refreshes and sessions
2. **Multi-User Support**: User-specific state management
3. **Data Integrity**: Proper foreign key relationships
4. **Scalability**: Can handle large amounts of state data
5. **Consistency**: Single source of truth for all state
6. **Recovery**: State can be restored after errors
7. **Audit Trail**: Track state changes over time

---

**Status**: ✅ COMPLETED
**Date**: 2025-09-25
**Next**: Phase 2 - Design Replacement Strategies
