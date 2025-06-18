-- LLM Provider
INSERT INTO llm_provider (id, name, type, api_url, auth_token, description, created_at, updated_at)
VALUES (1, 'Ollama (local)', 'local', 'http://localhost:11434', NULL, 'Local Ollama server for fast, private inference.', NOW(), NOW());

-- LLM Model
INSERT INTO llm_model (id, name, provider_id, description, strengths, weaknesses, api_params, created_at, updated_at)
VALUES (1, 'mistral', 1, 'Mistral 7B (local)', 'Fast, low resource, good for general tasks', 'Not as strong as GPT-4 for reasoning', '{"max_tokens": 8192}', NOW(), NOW());

-- LLM Prompt
INSERT INTO llm_prompt (id, name, description, prompt_text, system_prompt, parameters, "order", created_at, updated_at)
VALUES (1, 'TestPrompt', 'A test prompt', '[system] You are an expert in Scottish history and culture.', NULL, NULL, 0, NOW(), NOW());

-- LLM Action
INSERT INTO llm_action (id, field_name, description, provider_id, llm_model, prompt_template_id, temperature, max_tokens, "order", created_at, updated_at, input_field, output_field)
VALUES (1, 'TestField', 'Test action', 1, 'mistral', 1, 0.7, 1000, 0, NOW(), NOW(), 'input', 'output'); 