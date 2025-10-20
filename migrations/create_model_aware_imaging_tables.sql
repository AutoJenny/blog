-- Migration: Create Model-Aware Imaging Tables
-- Purpose: Add tables for model specifications, parameter defaults, prompt overrides, and generation events

-- Table for model parameter defaults
CREATE TABLE IF NOT EXISTS model_param_default (
    id SERIAL PRIMARY KEY,
    model_key VARCHAR(128) NOT NULL,
    param_key VARCHAR(128) NOT NULL,
    default_value TEXT,
    param_type VARCHAR(64) DEFAULT 'string',
    min_value NUMERIC,
    max_value NUMERIC,
    options JSONB, -- For dropdown options
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_key, param_key)
);

-- Table for image prompt overrides (per-model custom prompts)
CREATE TABLE IF NOT EXISTS image_prompt_override (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    section_id INTEGER REFERENCES post_section(id) ON DELETE CASCADE,
    model_key VARCHAR(128) NOT NULL,
    prompt_text TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, section_id, model_key)
);

-- Table for image generation events (audit trail)
CREATE TABLE IF NOT EXISTS image_generation_event (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    section_id INTEGER REFERENCES post_section(id) ON DELETE CASCADE,
    model_key VARCHAR(128) NOT NULL,
    params_json JSONB NOT NULL,
    prompt_text TEXT NOT NULL,
    rendered_prompt TEXT, -- The actual prompt sent to the model
    result_path VARCHAR(500),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    generation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_model_param_default_model_key ON model_param_default(model_key);
CREATE INDEX IF NOT EXISTS idx_image_prompt_override_post_section ON image_prompt_override(post_id, section_id);
CREATE INDEX IF NOT EXISTS idx_image_prompt_override_model_key ON image_prompt_override(model_key);
CREATE INDEX IF NOT EXISTS idx_image_generation_event_post_section ON image_generation_event(post_id, section_id);
CREATE INDEX IF NOT EXISTS idx_image_generation_event_model_key ON image_generation_event(model_key);
CREATE INDEX IF NOT EXISTS idx_image_generation_event_created_at ON image_generation_event(created_at);

-- Seed model parameter defaults for existing models
INSERT INTO model_param_default (model_key, param_key, default_value, param_type, min_value, max_value) VALUES
-- SDXL LoRA parameters
('sdxl-lora', 'width', '1792', 'integer', 512, 2048),
('sdxl-lora', 'height', '1024', 'integer', 512, 2048),
('sdxl-lora', 'steps', '20', 'integer', 1, 50),
('sdxl-lora', 'cfg_scale', '7.0', 'decimal', 1.0, 20.0),
('sdxl-lora', 'lora_scale', '0.85', 'decimal', 0.0, 2.0),
('sdxl-lora', 'seed', '-1', 'integer', -1, 2147483647),

-- DALL-E 3 parameters
('dall-e-3', 'size', '1792x1024', 'string', NULL, NULL),
('dall-e-3', 'quality', 'standard', 'string', NULL, NULL),
('dall-e-3', 'style', 'natural', 'string', NULL, NULL),

-- DALL-E 2 parameters
('dall-e-2', 'size', '1024x1024', 'string', NULL, NULL),
('dall-e-2', 'quality', 'standard', 'string', NULL, NULL)

ON CONFLICT (model_key, param_key) DO NOTHING;

-- Add options for dropdown parameters
UPDATE model_param_default SET options = '["1024x1024", "1024x1792", "1792x1024"]' WHERE model_key = 'dall-e-3' AND param_key = 'size';
UPDATE model_param_default SET options = '["standard", "hd"]' WHERE model_key = 'dall-e-3' AND param_key = 'quality';
UPDATE model_param_default SET options = '["natural", "vivid"]' WHERE model_key = 'dall-e-3' AND param_key = 'style';
UPDATE model_param_default SET options = '["1024x1024", "512x512", "256x256"]' WHERE model_key = 'dall-e-2' AND param_key = 'size';
UPDATE model_param_default SET options = '["standard"]' WHERE model_key = 'dall-e-2' AND param_key = 'quality';
