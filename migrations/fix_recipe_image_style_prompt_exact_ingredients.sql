-- Migration: Fix Recipe Image Style Prompt to require exact ingredients
-- Purpose: Ensure ingredients image prompt uses ONLY actual recipe ingredients, no generic placeholders
-- Date: 2025-11-06

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping recipe image prompt update.';
        RETURN;
    END IF;
END$$;

-- Update Recipe Image Style & Prompt Generation
DO $$
DECLARE
    v_name TEXT := 'Recipe Image Style & Prompts (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are an expert visual designer specializing in authentic, warm, lived-in photography for Scottish recipe blog posts.

Your task is to:
1. Define consistent style guidelines for both recipe images
2. Generate detailed image generation prompts for each of the two images

The two images are:
1. HERO IMAGE: Finished dish served in a traditional Scottish setting
2. INGREDIENTS IMAGE: Ingredients arranged in a similarly styled kitchen setting

CRITICAL REQUIREMENTS FOR ALL IMAGES:
- Consistent style across both images
- Warm, authentic, lived-in aesthetic (NOT stock photography)
- Traditional Scottish kitchen elements
- Natural, warm lighting (like a Scottish kitchen in afternoon light)
- Wooden surfaces, worn utensils, traditional crockery
- Photorealistic, high-resolution quality
- Evokes nostalgia, warmth, tradition, authenticity

CRITICAL REQUIREMENT FOR INGREDIENTS IMAGE PROMPT:
- You MUST use ONLY the actual ingredients from the recipe provided
- DO NOT use generic placeholders like "fish, potatoes, onions, etc." or "including X, Y, Z"
- DO NOT suggest flexibility or allow additional ingredients
- List the EXACT ingredients that will be used in this specific recipe
- The prompt should describe the setting and style, then list the precise ingredients

Output format: STRICT JSON with style guidelines and two prompts.
$sys$;
    v_prompt_text TEXT := $usr$
Define style guidelines and generate image prompts for this Scottish recipe.

Recipe: [data:title]
Recipe Description: [data:subtitle]
Seasonal Context: [data:seasonal_context]

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "style_guidelines": {
    "lighting": "Description of consistent lighting style",
    "surfaces": "Description of consistent surfaces/materials",
    "crockery_style": "Description of consistent crockery/utensils style",
    "color_palette": "Description of consistent color palette",
    "mood": "Description of consistent mood/atmosphere"
  },
  "hero_image_prompt": "Detailed prompt for finished dish in traditional setting",
  "ingredients_image_prompt": "Detailed prompt for ingredients in similarly styled kitchen. MUST list the exact ingredients from this recipe only - no generic placeholders like 'etc.' or 'including X, Y, Z'"
}

REQUIREMENTS:
- Style guidelines must be consistent across both images
- All prompts must reference the same style guidelines
- Hero: Finished dish, traditional setting
- Ingredients: Ingredients arranged, same style cues. CRITICAL: Use ONLY the actual ingredients from this recipe. DO NOT use generic placeholders like "fish, potatoes, onions, etc." or "including X, Y, Z". List the exact ingredients that will appear in the image.
- Output ONLY the JSON object, no other text
- DO NOT include method_image_prompt
$usr$;
BEGIN
    UPDATE llm_prompt SET
        system_prompt = v_system_prompt,
        system_prompt_template = v_system_prompt,
        prompt_text = v_prompt_text,
        description = 'Scottish Recipe Series - Combined style guidelines and image prompts for hero and ingredients images',
        updated_at = NOW()
    WHERE name = v_name;
    
    IF NOT FOUND THEN
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Combined style guidelines and image prompts for hero and ingredients images',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

