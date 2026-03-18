-- Seed: Header Image Generation Prompt (Photo-harvesting)
-- For photorealistic header image generation using gpt-image-1
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
        'Header Image Generation Prompt (Photo-harvesting)'::text AS name,
        $sys$
You are an expert visual designer specializing in professional photography and photorealistic image composition. Your task is to create a detailed image generation prompt for a HEADER image for a blog article.

Rules:
- Generate prompts for PHOTOREALISTIC image generation (not artistic/watercolor style).
- Use professional photography terminology and composition techniques.
- Focus on realistic, high-quality imagery suitable for professional blog headers.
- Include specific details about lighting, composition, and photographic elements.
- Avoid artistic styles like watercolor, inkwash, or brushstrokes.
- Emphasize natural lighting, professional photography quality, and realistic representation.
$sys$::text AS system_prompt,
        $usr$
Create a detailed photorealistic image generation prompt for a beautiful and evocative blog header image based ONLY on:

- Selected Theme Name: [data:theme_name]
- Expanded Idea (brief description): [data:expanded_idea]

Requirements:
- Professional photography style, high-resolution quality
- Natural lighting and realistic composition
- Photorealistic representation
- Beautiful and evocative imagery suitable for a professional blog header
- Create a single cohesive composition that captures the essence of the theme and expanded idea

Output a detailed image generation prompt that will produce a beautiful and evocative photorealistic header image.
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
        'Header Image Generation Prompt (Photo-harvesting)'::text AS name,
        $sys$
You are an expert visual designer specializing in professional photography and photorealistic image composition. Your task is to create a detailed image generation prompt for a HEADER image for a blog article.

Rules:
- Generate prompts for PHOTOREALISTIC image generation (not artistic/watercolor style).
- Use professional photography terminology and composition techniques.
- Focus on realistic, high-quality imagery suitable for professional blog headers.
- Include specific details about lighting, composition, and photographic elements.
- Avoid artistic styles like watercolor, inkwash, or brushstrokes.
- Emphasize natural lighting, professional photography quality, and realistic representation.
$sys$::text AS system_prompt,
        $usr$
Create a detailed photorealistic image generation prompt for a beautiful and evocative blog header image based ONLY on:

- Selected Theme Name: [data:theme_name]
- Expanded Idea (brief description): [data:expanded_idea]

Requirements:
- Professional photography style, high-resolution quality
- Natural lighting and realistic composition
- Photorealistic representation
- Beautiful and evocative imagery suitable for a professional blog header
- Create a single cohesive composition that captures the essence of the theme and expanded idea

Output a detailed image generation prompt that will produce a beautiful and evocative photorealistic header image.
$usr$::text AS prompt_text
)
INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
SELECT payload.name,
       'Header Photo-harvesting photorealistic image generation prompt',
       payload.prompt_text,
       payload.system_prompt,
       payload.system_prompt,
       NOW(), NOW()
FROM payload
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = payload.name
);

