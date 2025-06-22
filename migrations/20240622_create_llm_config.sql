-- Create llm_config table
CREATE TABLE llm_config (
    id SERIAL PRIMARY KEY,
    provider_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    api_base VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add initial configuration
INSERT INTO llm_config (provider_type, model_name, api_base)
VALUES ('ollama', 'llama3.1:70b', 'http://localhost:11434'); 