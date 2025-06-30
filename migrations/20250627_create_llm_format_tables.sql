-- Create LLM format template table
CREATE TABLE llm_format_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('bidirectional', 'input_only', 'output_only')),
    input_format VARCHAR(20),
    input_schema JSONB,
    input_instructions TEXT,
    output_format VARCHAR(20) NOT NULL,
    output_schema JSONB,
    output_rules JSONB,
    examples JSONB,
    notes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create workflow step format mapping table
CREATE TABLE workflow_step_format (
    step_id INTEGER REFERENCES workflow_step_entity(id),
    format_template_id INTEGER REFERENCES llm_format_template(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (step_id)
);

-- Add indexes for performance
CREATE INDEX idx_llm_format_template_name ON llm_format_template(name);
CREATE INDEX idx_llm_format_template_type ON llm_format_template(type);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_llm_format_template_updated_at
    BEFORE UPDATE ON llm_format_template
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_step_format_updated_at
    BEFORE UPDATE ON workflow_step_format
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add some basic format templates
INSERT INTO llm_format_template (name, description, version, type, input_format, output_format, input_schema, output_schema, output_rules, examples)
VALUES 
(
    'uk_english_prose',
    'Standard UK English prose format with proper spelling and grammar',
    '1.0',
    'output_only',
    'text',
    'text',
    '{"type": "string"}',
    '{"type": "string"}',
    '["Use UK English spelling", "Use proper grammar and punctuation", "Write in clear, professional prose"]',
    '{"input": "Write about Scottish history", "output": "The rich tapestry of Scottish history spans many centuries..."}'
),
(
    'blog_section_structure',
    'Format for blog post section structuring',
    '1.0',
    'bidirectional',
    'json',
    'json',
    '{
        "type": "object",
        "properties": {
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            },
            "themes": {
                "type": "array",
                "items": {"type": "string"}
            },
            "target_length": {"type": "number"}
        }
    }',
    '{
        "type": "object",
        "properties": {
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "word_count": {"type": "number"},
                        "key_facts": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "main_theme": {"type": "string"}
                    }
                }
            },
            "total_words": {"type": "number"}
        }
    }',
    '["Use UK English spelling", "Section titles in title case", "Facts distributed evenly"]',
    '{
        "input": {
            "facts": [
                {
                    "topic": "history",
                    "content": "The quaich dates back to 16th century Scotland"
                }
            ],
            "themes": ["hospitality"],
            "target_length": 1500
        },
        "output": {
            "sections": [
                {
                    "title": "The Ancient Origins of the Quaich",
                    "word_count": 300,
                    "key_facts": ["16th century origin"],
                    "main_theme": "history"
                }
            ],
            "total_words": 300
        }
    }'
); 