-- Migration: Create UI State Management Tables
-- Date: 2025-09-25
-- Description: Create tables for persistent state management to replace unauthorized storage

BEGIN;

-- Create ui_selection_state table
CREATE TABLE IF NOT EXISTS ui_selection_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    selection_type VARCHAR(50) NOT NULL,
    selected_id INTEGER,
    selected_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, selection_type)
);

-- Create ui_ui_state table
CREATE TABLE IF NOT EXISTS ui_ui_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    state_key VARCHAR(100) NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, state_key)
);

-- Create ui_workflow_state table
CREATE TABLE IF NOT EXISTS ui_workflow_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    workflow_id VARCHAR(100) NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, workflow_id)
);

-- Create ui_queue_state table
CREATE TABLE IF NOT EXISTS ui_queue_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    queue_type VARCHAR(50) NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, queue_type)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ui_selection_state_user_page ON ui_selection_state(user_id, page_type);
CREATE INDEX IF NOT EXISTS idx_ui_ui_state_user_page ON ui_ui_state(user_id, page_type);
CREATE INDEX IF NOT EXISTS idx_ui_workflow_state_user_page ON ui_workflow_state(user_id, page_type);
CREATE INDEX IF NOT EXISTS idx_ui_queue_state_user_page ON ui_queue_state(user_id, page_type);

-- Add comments for documentation
COMMENT ON TABLE ui_selection_state IS 'Stores user selections (products, blog posts, sections)';
COMMENT ON TABLE ui_ui_state IS 'Stores UI state (accordions, tabs, checkboxes)';
COMMENT ON TABLE ui_workflow_state IS 'Stores workflow state (LLM context, processing)';
COMMENT ON TABLE ui_queue_state IS 'Stores queue state and preferences';

COMMIT;
