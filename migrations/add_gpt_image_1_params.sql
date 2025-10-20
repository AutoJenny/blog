-- Migration: Add GPT-Image-1 Parameter Defaults
-- Purpose: Add parameter defaults for OpenAI's gpt-image-1 model

-- Add parameter defaults for gpt-image-1
INSERT INTO model_param_default (model_key, param_key, default_value, param_type, min_value, max_value, options) VALUES
-- GPT-Image-1 parameters
('gpt-image-1', 'size', '1024x1024', 'string', NULL, NULL, '["1024x1024", "512x512", "256x256", "1792x1024", "1024x1792"]'),
('gpt-image-1', 'quality', 'standard', 'string', NULL, NULL, '["standard", "hd"]'),
('gpt-image-1', 'style', 'natural', 'string', NULL, NULL, '["natural", "vivid"]'),
('gpt-image-1', 'n', '1', 'integer', 1, 10, NULL),
('gpt-image-1', 'seed', NULL, 'integer', NULL, NULL, NULL),
('gpt-image-1', 'background', NULL, 'string', NULL, NULL, '["", "transparent", "white"]'),
('gpt-image-1', 'response_format', 'url', 'string', NULL, NULL, '["url", "b64_json"]')

ON CONFLICT (model_key, param_key) DO NOTHING;
