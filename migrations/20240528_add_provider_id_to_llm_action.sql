-- Migration: Add provider_id to llm_action
ALTER TABLE llm_action ADD COLUMN provider_id INTEGER;
UPDATE llm_action SET provider_id = 1 WHERE provider_id IS NULL;
ALTER TABLE llm_action ALTER COLUMN provider_id SET NOT NULL;
ALTER TABLE llm_action ADD CONSTRAINT fk_llm_action_provider FOREIGN KEY (provider_id) REFERENCES llm_provider(id); 