-- Migration: Add Recipe Image Style & Prompt Generation
-- Purpose: Combined step for defining style guidelines and generating prompts for all 3 recipe images
-- Date: 2025-11-06

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping recipe image style prompt.';
        RETURN;
    END IF;
END$$;

-- Recipe Image Style & Prompt Generation (Combined Step)
DO $$
DECLARE
    v_name TEXT := 'Recipe Image Style & Prompts (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are an expert visual designer specializing in authentic, warm, lived-in photography for Scottish recipe blog posts.

Your task is to:
1. Define consistent style guidelines for all three recipe images
2. Generate detailed image generation prompts for each of the three images

The three images are:
1. HERO IMAGE: Finished dish served in a traditional Scottish setting
2. INGREDIENTS IMAGE: Ingredients arranged in a similarly styled kitchen setting
3. METHOD IMAGE: A key stage of the cooking method in the same style

CRITICAL REQUIREMENTS FOR ALL IMAGES:
- Consistent style across all three images
- Warm, authentic, lived-in aesthetic (NOT stock photography)
- Traditional Scottish kitchen elements
- Natural, warm lighting (like a Scottish kitchen in afternoon light)
- Wooden surfaces, worn utensils, traditional crockery
- Photorealistic, high-resolution quality
- Evokes nostalgia, warmth, tradition, authenticity

Output format: STRICT JSON with style guidelines and three prompts.
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
  "ingredients_image_prompt": "Detailed prompt for ingredients in similarly styled kitchen",
  "method_image_prompt": "Detailed prompt for key cooking step in same style"
}

REQUIREMENTS:
- Style guidelines must be consistent across all three images
- All prompts must reference the same style guidelines
- Hero: Finished dish, traditional setting
- Ingredients: Ingredients arranged, same style cues
- Method: Key cooking step, same style cues
- Output ONLY the JSON object, no other text
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Combined style guidelines and image prompts for all 3 images',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Combined style guidelines and image prompts for all 3 images',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

