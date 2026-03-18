-- Seed: Header Image Search Prompt (Photo-harvesting)
-- No fallbacks: API must 404 if this prompt is missing

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'llm_prompt table missing; skipping header prompt seed.';
        RETURN;
    END IF;
END$$;

-- Upsert by name (portable: update-then-insert)
WITH payload AS (
    SELECT 
        'Header Image Search Prompt (Photo-harvesting)'::text AS name,
        $sys$
You are an expert photo-researcher and visual curator. Your task is to create a concise, high-signal photo search query for sourcing a suitable HEADER image for a blog article.

Rules:
- This is for PHOTO SEARCH, not image generation.
- Use canonical entities, locations, eras, and materials common in stock libraries.
- Prefer objective descriptors (scene, subject, time of day, composition) over abstract themes.
- Include 5–12 keywords/short phrases, comma-separated.
- Include constraints/negatives if relevant (e.g., "no text overlay, no watermark").
- The query must be realistic and likely to produce existing photographs.
$sys$::text AS system_prompt,
        $usr$
Compose a single-line photo search query for the blog header image based ONLY on:
- Selected Theme Name: [data:theme_name]
- Expanded Idea (brief description): [data:expanded_idea]

Output
Respond ONLY with the final search query text (no quotes, no markdown). Use comma-separated keywords/phrases.
$usr$::text AS prompt_text
)
UPDATE llm_prompt p
SET system_prompt = payload.system_prompt,
    system_prompt_template = payload.system_prompt,
    prompt_text = payload.prompt_text,
    updated_at = NOW()
FROM payload
WHERE p.name = payload.name;

WITH payload AS (
    SELECT 
        'Header Image Search Prompt (Photo-harvesting)'::text AS name,
        $sys$
You are an expert photo-researcher and visual curator. Your task is to create a concise, high-signal photo search query for sourcing a suitable HEADER image for a blog article.

Rules:
- This is for PHOTO SEARCH, not image generation.
- Use canonical entities, locations, eras, and materials common in stock libraries.
- Prefer objective descriptors (scene, subject, time of day, composition) over abstract themes.
- Include 5–12 keywords/short phrases, comma-separated.
- Include constraints/negatives if relevant (e.g., "no text overlay, no watermark").
- The query must be realistic and likely to produce existing photographs.
$sys$::text AS system_prompt,
        $usr$
Compose a single-line photo search query for the blog header image based ONLY on:
- Selected Theme Name: [data:theme_name]
- Expanded Idea (brief description): [data:expanded_idea]

Output
Respond ONLY with the final search query text (no quotes, no markdown). Use comma-separated keywords/phrases.
$usr$::text AS prompt_text
)
INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
SELECT payload.name,
       'Header Photo-harvesting search query prompt',
       payload.prompt_text,
       payload.system_prompt,
       payload.system_prompt,
       NOW(), NOW()
FROM payload
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = payload.name
);


