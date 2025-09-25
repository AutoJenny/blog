# Phase 2.1: Database Table Designs for State Persistence

**APPROACH**: Specialized tables for different types of state (Option B)

---

## **TABLE 1: `ui_selection_state`**

**Purpose**: Manage all selection states (products, blog posts, sections)

### **Schema Design**:
```sql
CREATE TABLE ui_selection_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id) ON DELETE CASCADE,
    selection_type VARCHAR(50) NOT NULL,  -- 'product', 'blog_post', 'section'
    selected_id INTEGER NOT NULL,  -- ID of selected item
    selected_data JSONB,  -- Additional selection data (name, details, etc.)
    context_data JSONB,  -- Context information (post_id, workflow stage, etc.)
    is_active BOOLEAN DEFAULT TRUE,  -- Whether this is the current selection
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, selection_type),  -- One active selection per type per user
    CHECK (selection_type IN ('product', 'blog_post', 'section'))
);

-- Indexes for performance
CREATE INDEX idx_ui_selection_state_user_type ON ui_selection_state(user_id, selection_type);
CREATE INDEX idx_ui_selection_state_active ON ui_selection_state(is_active) WHERE is_active = TRUE;
```

### **Usage Examples**:
```sql
-- Set selected product
INSERT INTO ui_selection_state (user_id, selection_type, selected_id, selected_data, context_data)
VALUES (1, 'product', 12345, '{"name": "Tartan Leggings", "sku": "TL001"}', '{"workflow_stage": "content_generation"}')
ON CONFLICT (user_id, selection_type) 
DO UPDATE SET selected_id = EXCLUDED.selected_id, selected_data = EXCLUDED.selected_data, updated_at = NOW();

-- Get current selections for user
SELECT * FROM ui_selection_state WHERE user_id = 1 AND is_active = TRUE;

-- Clear selection
UPDATE ui_selection_state SET is_active = FALSE WHERE user_id = 1 AND selection_type = 'product';
```

---

## **TABLE 2: `ui_ui_state`**

**Purpose**: Manage UI state (accordions, tabs, checkboxes, element order)

### **Schema Design**:
```sql
CREATE TABLE ui_ui_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id) ON DELETE CASCADE,
    state_category VARCHAR(50) NOT NULL,  -- 'accordion', 'tabs', 'checkboxes', 'element_order'
    state_key VARCHAR(100) NOT NULL,  -- Unique key for this state
    state_value JSONB NOT NULL,  -- State data as JSON
    entity_id INTEGER,  -- ID of related entity (post_id, product_id, etc.)
    entity_type VARCHAR(50),  -- Type of related entity ('post', 'product', 'section')
    expires_at TIMESTAMP,  -- Optional expiration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, state_category, state_key),
    CHECK (state_category IN ('accordion', 'tabs', 'checkboxes', 'element_order'))
);

-- Indexes for performance
CREATE INDEX idx_ui_ui_state_user_category ON ui_ui_state(user_id, state_category);
CREATE INDEX idx_ui_ui_state_entity ON ui_ui_state(entity_type, entity_id);
CREATE INDEX idx_ui_ui_state_expires ON ui_ui_state(expires_at) WHERE expires_at IS NOT NULL;
```

### **Usage Examples**:
```sql
-- Save accordion state for a post
INSERT INTO ui_ui_state (user_id, state_category, state_key, state_value, entity_id, entity_type)
VALUES (1, 'accordion', 'sections_accordion_post_53', '{"section_1": true, "section_2": false}', 53, 'post')
ON CONFLICT (user_id, state_category, state_key)
DO UPDATE SET state_value = EXCLUDED.state_value, updated_at = NOW();

-- Save checkbox selections for a post
INSERT INTO ui_ui_state (user_id, state_category, state_key, state_value, entity_id, entity_type)
VALUES (1, 'checkboxes', 'sections_selection_post_53', '{"710": true, "711": false, "712": true}', 53, 'post')
ON CONFLICT (user_id, state_category, state_key)
DO UPDATE SET state_value = EXCLUDED.state_value, updated_at = NOW();

-- Get all UI state for a user
SELECT * FROM ui_ui_state WHERE user_id = 1;
```

---

## **TABLE 3: `ui_workflow_state`**

**Purpose**: Manage workflow state (LLM_STATE.context, processing state, module state)

### **Schema Design**:
```sql
CREATE TABLE ui_workflow_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL,  -- 'llm_context', 'processing', 'module_registry'
    state_key VARCHAR(100) NOT NULL,  -- Unique key for this state
    state_value JSONB NOT NULL,  -- State data as JSON
    entity_id INTEGER,  -- ID of related entity (post_id, etc.)
    entity_type VARCHAR(50),  -- Type of related entity
    expires_at TIMESTAMP,  -- Optional expiration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, workflow_type, state_key),
    CHECK (workflow_type IN ('llm_context', 'processing', 'module_registry'))
);

-- Indexes for performance
CREATE INDEX idx_ui_workflow_state_user_type ON ui_workflow_state(user_id, workflow_type);
CREATE INDEX idx_ui_workflow_state_entity ON ui_workflow_state(entity_type, entity_id);
```

### **Usage Examples**:
```sql
-- Save LLM workflow context
INSERT INTO ui_workflow_state (user_id, workflow_type, state_key, state_value, entity_id, entity_type)
VALUES (1, 'llm_context', 'workflow_context', '{"post_id": 53, "stage": "planning", "substage": "idea", "step": "initial_concept"}', 53, 'post')
ON CONFLICT (user_id, workflow_type, state_key)
DO UPDATE SET state_value = EXCLUDED.state_value, updated_at = NOW();

-- Save processing state
INSERT INTO ui_workflow_state (user_id, workflow_type, state_key, state_value)
VALUES (1, 'processing', 'llm_processing', '{"processing": false, "current_step": "content_generation"}')
ON CONFLICT (user_id, workflow_type, state_key)
DO UPDATE SET state_value = EXCLUDED.state_value, updated_at = NOW();
```

---

## **TABLE 4: `ui_queue_state`**

**Purpose**: Manage queue state (queueData, queue preferences, queue filters)

### **Schema Design**:
```sql
CREATE TABLE ui_queue_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id) ON DELETE CASCADE,
    queue_type VARCHAR(50) NOT NULL,  -- 'posting_queue', 'content_queue', 'workflow_queue'
    state_key VARCHAR(100) NOT NULL,  -- Unique key for this state
    state_value JSONB NOT NULL,  -- State data as JSON
    entity_id INTEGER,  -- ID of related entity
    entity_type VARCHAR(50),  -- Type of related entity
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, queue_type, state_key),
    CHECK (queue_type IN ('posting_queue', 'content_queue', 'workflow_queue'))
);

-- Indexes for performance
CREATE INDEX idx_ui_queue_state_user_type ON ui_queue_state(user_id, queue_type);
```

---

## **MIGRATION FROM EXISTING TABLES**

### **From `ui_session_state`**:
```sql
-- Migrate session state to new tables
INSERT INTO ui_selection_state (user_id, selection_type, selected_id, selected_data, context_data)
SELECT 
    COALESCE(user_id, 1) as user_id,  -- Default to user 1 if null
    'product' as selection_type,
    state_value::INTEGER as selected_id,
    '{}' as selected_data,
    '{}' as context_data
FROM ui_session_state 
WHERE state_key = 'selected_product_id' 
AND state_value IS NOT NULL;

-- Migrate UI state
INSERT INTO ui_ui_state (user_id, state_category, state_key, state_value, entity_id, entity_type)
SELECT 
    COALESCE(user_id, 1) as user_id,
    'accordion' as state_category,
    state_key,
    state_value::JSONB as state_value,
    NULL as entity_id,
    'global' as entity_type
FROM ui_session_state 
WHERE state_key LIKE '%accordion%' 
AND state_value IS NOT NULL;
```

---

## **DATA TYPE MAPPINGS**

### **localStorage to Database**:
| **localStorage Key Pattern** | **New Table** | **state_key** | **state_value** |
|------------------------------|---------------|---------------|-----------------|
| `selectedBlogPostId` | `ui_selection_state` | `blog_post` | `{"selected_id": 53}` |
| `sections_selection_post_${postId}` | `ui_ui_state` | `sections_selection_post_${postId}` | `{"710": true, "711": false}` |
| `sections_accordion_post_${postId}` | `ui_ui_state` | `sections_accordion_post_${postId}` | `{"section_1": true}` |
| `sections_tabs_post_${postId}` | `ui_ui_state` | `sections_tabs_post_${postId}` | `{"tab_1": "active"}` |

### **Session State to Database**:
| **Current Usage** | **New Table** | **state_key** | **state_value** |
|-------------------|---------------|---------------|-----------------|
| `selected_product_id` | `ui_selection_state` | `product` | `{"selected_id": 12345}` |
| `accordion_state` | `ui_ui_state` | `global_accordion_state` | `{"platform_config": "expanded"}` |
| `filter_preferences` | `ui_ui_state` | `global_filter_preferences` | `{"show_active_only": true}` |

### **In-Memory State to Database**:
| **Current Usage** | **New Table** | **state_key** | **state_value** |
|-------------------|---------------|---------------|-----------------|
| `LLM_STATE.context` | `ui_workflow_state` | `workflow_context` | `{"post_id": 53, "stage": "planning"}` |
| `queueData` | `ui_queue_state` | `posting_queue_data` | `[{"id": 1, "title": "Post 1"}]` |
| `selectedData` | `ui_selection_state` | `ai_content_selection` | `{"type": "product", "id": 12345}` |

---

## **PERFORMANCE CONSIDERATIONS**

### **Indexing Strategy**:
1. **Primary indexes** on `(user_id, selection_type)` for selections
2. **Composite indexes** on `(user_id, state_category, state_key)` for UI state
3. **Entity indexes** on `(entity_type, entity_id)` for related data
4. **Expiration indexes** for cleanup

### **Cleanup Strategy**:
1. **Automatic cleanup** of expired states
2. **User-specific cleanup** when user is deleted
3. **Entity-specific cleanup** when entities are deleted
4. **Periodic cleanup** of old, unused states

---

## **NEXT STEPS**

1. **Review and approve** table designs
2. **Create migration scripts** for existing data
3. **Design API endpoints** for state management
4. **Create JavaScript utilities** for database state management
5. **Implement gradual migration** from unauthorized storage

---

**Status**: ✅ COMPLETED
**Date**: 2025-09-25
**Next**: Phase 2.2 - API Endpoint Design
