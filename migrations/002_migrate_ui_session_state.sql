-- Migration: Migrate data from ui_session_state
-- Date: 2025-09-25
-- Description: Migrate existing data to new state tables

BEGIN;

-- Migrate selected_product_id to ui_selection_state
INSERT INTO ui_selection_state (user_id, page_type, selection_type, selected_id, selected_data, created_at)
SELECT 
    COALESCE(user_id, 1) as user_id,
    'product_post' as page_type,
    'product' as selection_type,
    (state_value::json->>'product_id')::integer as selected_id,
    state_value::json as selected_data,
    created_at
FROM ui_session_state
WHERE state_key = 'selected_product_id' 
AND state_value IS NOT NULL
AND state_value != 'null'
ON CONFLICT (user_id, page_type, selection_type) 
DO UPDATE SET 
    selected_id = EXCLUDED.selected_id,
    selected_data = EXCLUDED.selected_data,
    updated_at = CURRENT_TIMESTAMP;

-- Migrate accordion states to ui_ui_state
INSERT INTO ui_ui_state (user_id, page_type, state_key, state_data, created_at)
SELECT 
    COALESCE(user_id, 1) as user_id,
    'product_post' as page_type,
    state_key,
    state_value::json as state_data,
    created_at
FROM ui_session_state
WHERE state_key LIKE 'accordion_%' 
AND state_value IS NOT NULL
AND state_value != 'null'
ON CONFLICT (user_id, page_type, state_key) 
DO UPDATE SET 
    state_data = EXCLUDED.state_data,
    updated_at = CURRENT_TIMESTAMP;

-- Migrate tab states to ui_ui_state
INSERT INTO ui_ui_state (user_id, page_type, state_key, state_data, created_at)
SELECT 
    COALESCE(user_id, 1) as user_id,
    'product_post' as page_type,
    state_key,
    state_value::json as state_data,
    created_at
FROM ui_session_state
WHERE state_key LIKE 'tab_%' 
AND state_value IS NOT NULL
AND state_value != 'null'
ON CONFLICT (user_id, page_type, state_key) 
DO UPDATE SET 
    state_data = EXCLUDED.state_data,
    updated_at = CURRENT_TIMESTAMP;

-- Migrate LLM states to ui_workflow_state
INSERT INTO ui_workflow_state (user_id, page_type, workflow_id, state_data, created_at)
SELECT 
    COALESCE(user_id, 1) as user_id,
    'product_post' as page_type,
    REPLACE(state_key, 'llm_', '') as workflow_id,
    state_value::json as state_data,
    created_at
FROM ui_session_state
WHERE state_key LIKE 'llm_%' 
AND state_value IS NOT NULL
AND state_value != 'null'
ON CONFLICT (user_id, page_type, workflow_id) 
DO UPDATE SET 
    state_data = EXCLUDED.state_data,
    updated_at = CURRENT_TIMESTAMP;

-- Migrate generation states to ui_workflow_state
INSERT INTO ui_workflow_state (user_id, page_type, workflow_id, state_data, created_at)
SELECT 
    COALESCE(user_id, 1) as user_id,
    'product_post' as page_type,
    REPLACE(state_key, 'generation_', '') as workflow_id,
    state_value::json as state_data,
    created_at
FROM ui_session_state
WHERE state_key LIKE 'generation_%' 
AND state_value IS NOT NULL
AND state_value != 'null'
ON CONFLICT (user_id, page_type, workflow_id) 
DO UPDATE SET 
    state_data = EXCLUDED.state_data,
    updated_at = CURRENT_TIMESTAMP;

-- Migrate queue states to ui_queue_state
INSERT INTO ui_queue_state (user_id, page_type, queue_type, state_data, created_at)
SELECT 
    COALESCE(user_id, 1) as user_id,
    'product_post' as page_type,
    REPLACE(state_key, 'queue_', '') as queue_type,
    state_value::json as state_data,
    created_at
FROM ui_session_state
WHERE state_key LIKE 'queue_%' 
AND state_value IS NOT NULL
AND state_value != 'null'
ON CONFLICT (user_id, page_type, queue_type) 
DO UPDATE SET 
    state_data = EXCLUDED.state_data,
    updated_at = CURRENT_TIMESTAMP;

COMMIT;
