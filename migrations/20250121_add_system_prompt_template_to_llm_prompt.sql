-- Add system_prompt_template field to llm_prompt table
-- This will store the template version without JSON format instructions

ALTER TABLE llm_prompt ADD COLUMN system_prompt_template TEXT;

-- Update existing Image Prompts Generation record to split the system prompt
UPDATE llm_prompt 
SET system_prompt_template = 'You are an expert image prompt engineer. Create highly specific, visually rich prompts for AI image generation. Include: subject, setting, historical period and locality, 2–3 key elements, composition/framing, lighting, color palette, texture/materials, mood, vantage/time. When Style Guidelines are provided, explicitly incorporate ≥4 distinct cues; prefer exact phrases. Target up to 2000 characters. Create comprehensive, detailed descriptions that fully utilize the character limit. If the draft exceeds the character limit, rewrite until it fits without losing key style cues.'
WHERE name = 'Image Prompts Generation';
