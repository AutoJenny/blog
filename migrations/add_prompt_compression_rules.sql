-- Add prompt compression rules table for SDXL and other models
CREATE TABLE prompt_compression_rules (
    id SERIAL PRIMARY KEY,
    model_key VARCHAR(128) NOT NULL,
    rule_type VARCHAR(64) NOT NULL, -- 'abbreviation', 'priority', 'template'
    rule_key VARCHAR(128),
    rule_value JSONB,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient lookups
CREATE INDEX idx_compression_rules_model_type ON prompt_compression_rules(model_key, rule_type);

-- Seed SDXL compression rules
INSERT INTO prompt_compression_rules (model_key, rule_type, rule_key, rule_value) VALUES
-- Abbreviations for common terms
('sdxl-lora', 'abbreviation', 'watercolor', '{"short": "wc", "priority": 1}'),
('sdxl-lora', 'abbreviation', 'visible brushstrokes', '{"short": "brush", "priority": 2}'),
('sdxl-lora', 'abbreviation', 'pastel colors', '{"short": "pastel", "priority": 1}'),
('sdxl-lora', 'abbreviation', 'white margins', '{"short": "margins", "priority": 3}'),
('sdxl-lora', 'abbreviation', 'ink wash', '{"short": "ink", "priority": 2}'),
('sdxl-lora', 'abbreviation', 'composition', '{"short": "comp", "priority": 3}'),
('sdxl-lora', 'abbreviation', 'lighting', '{"short": "light", "priority": 3}'),

-- Priority order for style elements (what to drop first)
('sdxl-lora', 'priority', 'style_elements', '{"order": ["palette", "brushwork", "margins", "composition", "lighting"]}'),

-- Template patterns for different styles
('sdxl-lora', 'template', 'watercolor', '{"base": "[SUBJECT], wc, pastel, [MOOD]", "fallback": "[SUBJECT], wc"}'),
('sdxl-lora', 'template', 'ink_wash', '{"base": "[SUBJECT], ink, [MOOD]", "fallback": "[SUBJECT], ink"}'),
('sdxl-lora', 'template', 'default', '{"base": "[SUBJECT], [STYLE], [MOOD]", "fallback": "[SUBJECT]"}'),

-- Character limits for different compression levels
('sdxl-lora', 'limit', 'level_1', '{"max_chars": 400}'),
('sdxl-lora', 'limit', 'level_2', '{"max_chars": 300}'),
('sdxl-lora', 'limit', 'level_3', '{"max_chars": 200}'),
('sdxl-lora', 'limit', 'level_4', '{"max_chars": 100}');

-- Add compression rules for other models if needed
INSERT INTO prompt_compression_rules (model_key, rule_type, rule_key, rule_value) VALUES
-- GPT-Image-1 doesn't need compression but we can add style templates
('gpt-image-1', 'template', 'watercolor', '{"base": "[SUBJECT] rendered in watercolor style with [PALETTE] color palette and [BRUSHWORK] brushwork, conveying [MOOD] mood"}'),
('gpt-image-1', 'template', 'ink_wash', '{"base": "[SUBJECT] in ink wash technique with [PALETTE] tones, conveying [MOOD] atmosphere"}'),
('gpt-image-1', 'template', 'default', '{"base": "[SUBJECT] in [STYLE] style, [COMPOSITION] composition, conveying [MOOD] mood with [LIGHTING] lighting"}');
