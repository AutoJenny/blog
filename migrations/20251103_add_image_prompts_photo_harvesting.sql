-- Migration: Add Image Prompts Generation (Photo-harvesting)
-- Purpose: Seed a distinct prompt tuned for image searching (not image generation)
-- Notes:
--  - No fallbacks. If this prompt is missing, the UI should surface a 404 from the API.
--  - This script is idempotent: it updates if present, inserts if missing.

-- Ensure table exists before proceeding (safe guard for partial environments)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping seed for Image Prompts Generation (Photo-harvesting).';
        RETURN;
    END IF;
END$$;

-- Define prompt content
-- System prompt is explicitly for PHOTO SEARCH / HARVESTING workflows
-- Absolutely no instructions about "generate an image" should appear here
WITH payload AS (
    SELECT 
        'Image Prompts Generation (Photo-harvesting)'::text AS name,
        $sys$
You are an expert photo-researcher and visual librarian.
Your task is to craft a concise, highly searchable, human-readable photo search query that will be used to find existing photographs or illustrations on the web and stock libraries.

Rules:
- Focus on searchability, not image generation.
- Use concrete entities, periods, locations, and materials where known.
- Prefer canonical terms and synonyms commonly used by photo archives.
- Include 5–12 high-signal keywords and short phrases, separated by commas.
- Include constraints and negatives when relevant (e.g., "no text overlay, no watermark").
- Respect the post''s section context and tone.
- Avoid meta commentary; output only the final search query.
$sys$::text AS system_prompt,
        $usr$
Compose a single-line photo search query for this section.

Context
Title: [data:title]
Subtitle/Description: [data:subtitle]
Section text (if any): [data:section_text]
Selected concept (if any): [data:selected_concept]
Topics (if any):
[data:topics]

Style guidelines (if any):
[data:style]

Output
Respond ONLY with the final search query text (no quotes, no markdown), suitable for web and stock-photo searches. Use comma-separated keywords/phrases.
$usr$::text AS prompt_text
)
-- Upsert by name (portable: update-then-insert)
UPDATE llm_prompt p
SET system_prompt = payload.system_prompt,
    system_prompt_template = payload.system_prompt, -- store template version equivalently
    prompt_text = payload.prompt_text,
    updated_at = NOW()
FROM payload
WHERE p.name = payload.name;

INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
SELECT payload.name,
       'Photo-harvesting search query prompt for Image Prompts stage',
       payload.prompt_text,
       payload.system_prompt,
       payload.system_prompt,
       NOW(), NOW()
FROM payload
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = payload.name
);


