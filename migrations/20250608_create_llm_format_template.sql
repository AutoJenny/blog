-- Create llm_format_template table
CREATE TABLE llm_format_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    format_type VARCHAR(32) NOT NULL CHECK (format_type IN ('input', 'output')),
    format_spec TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Set proper ownership
ALTER TABLE llm_format_template OWNER TO nickfiddes;

-- Add indexes
CREATE INDEX idx_format_template_type ON llm_format_template(format_type);
CREATE INDEX idx_format_template_name ON llm_format_template(name);

-- Rollback
-- DROP TABLE IF EXISTS llm_format_template; 