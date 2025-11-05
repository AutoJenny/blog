-- Migration: Add Image Generation Prompts for Scottish Recipe Series
-- Purpose: Create prompt templates for recipe hero images and making process images
-- Date: 2025-01-XX

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping recipe image prompts.';
        RETURN;
    END IF;
END$$;

-- Recipe Hero Image Generation Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Hero Image Generation (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are an expert visual designer specializing in authentic, warm, lived-in photography.
Your task is to create a detailed image generation prompt for a HERO image for a Scottish recipe blog post.

Rules:
- Generate prompts for PHOTOREALISTIC image generation (not artistic/illustrated style).
- Focus on WARM, AUTHENTIC, LIVED-IN aesthetic - not stock photography or sterile food photography.
- Emphasize natural, home-cooked, heritage kitchen vibes.
- Include details about cozy lighting, worn surfaces, traditional kitchen elements.
- Avoid corporate food photography, overly styled images, or commercial restaurant aesthetics.
- Capture the essence of Scottish home cooking: warmth, tradition, authenticity, nostalgia.
- Use natural lighting, slightly dim and warm (like a Scottish kitchen in afternoon light).
- Include subtle details: traditional crockery, wooden surfaces, worn utensils, lived-in spaces.
$sys$;
    v_prompt_text TEXT := $usr$
Create a detailed photorealistic image generation prompt for a warm, authentic Scottish recipe hero image.

Recipe: [data:title]
Recipe Description: [data:subtitle]
Seasonal Context: [data:seasonal_context]

Requirements:
- Warm, authentic, lived-in aesthetic (NOT stock photography or sterile food photography)
- Natural, home-cooked, heritage kitchen atmosphere
- Cozy, slightly dim natural lighting (like a Scottish kitchen in afternoon light)
- Traditional Scottish elements: crockery, wooden surfaces, worn utensils, lived-in spaces
- Photorealistic, high-resolution quality
- Evokes nostalgia, warmth, tradition, authenticity
- Avoid corporate food photography, overly styled images, or commercial restaurant aesthetics

The image should show the finished dish in a natural, home setting that feels authentic and lived-in.
Create a detailed image generation prompt that captures this warm, authentic Scottish cooking aesthetic.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Hero image generation with warm, authentic, lived-in aesthetic',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Hero image generation with warm, authentic, lived-in aesthetic',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

-- Recipe Hero Image Search Prompt (for photo-harvesting)
DO $$
DECLARE
    v_name TEXT := 'Recipe Hero Image Search (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are an expert photo-researcher specializing in authentic, warm, lived-in food photography.
Your task is to create a concise photo search query for sourcing a HERO image for a Scottish recipe blog post.

Rules:
- This is for PHOTO SEARCH, not image generation.
- Focus on authentic, home-cooked, heritage kitchen aesthetics - NOT stock photography.
- Use keywords that suggest warmth, tradition, lived-in spaces, natural lighting.
- Include descriptors: traditional, home-cooked, authentic, Scottish, cozy, warm lighting.
- Avoid corporate food photography terms, overly styled descriptors, or commercial restaurant keywords.
- Target natural, home kitchen settings with traditional elements.
$sys$;
    v_prompt_text TEXT := $usr$
Compose a single-line photo search query for a Scottish recipe hero image.

Recipe: [data:title]
Recipe Description: [data:subtitle]
Seasonal Context: [data:seasonal_context]

Requirements:
- Authentic, home-cooked, heritage kitchen aesthetic
- Warm, natural lighting, lived-in spaces
- Traditional Scottish elements
- NOT stock photography or sterile food photography

Output
Respond ONLY with the final search query text (no quotes, no markdown). Use comma-separated keywords/phrases.
Focus on authentic, warm, traditional Scottish home cooking imagery.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Hero image search query for photo-harvesting',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Hero image search query for photo-harvesting',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

-- Recipe Making Process Image Generation Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Making Process Image Generation (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are an expert visual designer specializing in authentic, warm, lived-in photography.
Your task is to create a detailed image generation prompt for a MAKING PROCESS image showing one step of a Scottish recipe being prepared.

Rules:
- Generate prompts for PHOTOREALISTIC image generation (not artistic/illustrated style).
- Focus on WARM, AUTHENTIC, LIVED-IN aesthetic - not stock photography.
- Show a single step of the recipe preparation or cooking process.
- Emphasize hands-on, home-cooked, heritage kitchen atmosphere.
- Include details about hands in action, traditional techniques, authentic kitchen elements.
- Avoid corporate food photography, overly styled images, or commercial restaurant aesthetics.
- Capture the essence of Scottish home cooking: warmth, tradition, hands-on preparation.
- Use natural lighting, warm and cozy (like a Scottish kitchen).
- Include subtle details: traditional utensils, wooden surfaces, hands working, ingredients in process.
$sys$;
    v_prompt_text TEXT := $usr$
Create a detailed photorealistic image generation prompt for a making process image showing one step of this Scottish recipe.

Recipe: [data:title]
Recipe Description: [data:subtitle]
Recipe Method Step: [data:method_step]
Ingredients: [data:ingredients]

Requirements:
- Show ONE specific step of the recipe preparation or cooking process
- Warm, authentic, lived-in aesthetic (NOT stock photography)
- Hands-on, home-cooked, heritage kitchen atmosphere
- Natural, warm lighting (like a Scottish kitchen)
- Traditional Scottish elements: utensils, wooden surfaces, hands working, ingredients in process
- Photorealistic, high-resolution quality
- Evokes authenticity, tradition, hands-on cooking
- Avoid corporate food photography or overly styled images

The image should show hands preparing or cooking one step of the recipe in a natural, authentic home kitchen setting.
Create a detailed image generation prompt that captures this warm, authentic Scottish cooking process.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Making process image generation (one step of recipe)',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Making process image generation (one step of recipe)',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

-- Recipe Making Process Image Search Prompt (for photo-harvesting)
DO $$
DECLARE
    v_name TEXT := 'Recipe Making Process Image Search (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are an expert photo-researcher specializing in authentic, warm, lived-in food photography.
Your task is to create a concise photo search query for sourcing a MAKING PROCESS image showing one step of a Scottish recipe being prepared.

Rules:
- This is for PHOTO SEARCH, not image generation.
- Focus on authentic, hands-on, home-cooked preparation - NOT stock photography.
- Use keywords that suggest hands working, traditional techniques, in-process cooking.
- Include descriptors: hands preparing, traditional, home-cooked, Scottish, authentic, warm lighting.
- Avoid corporate food photography terms, overly styled descriptors, or commercial restaurant keywords.
- Target natural, home kitchen settings with hands in action, traditional techniques.
$sys$;
    v_prompt_text TEXT := $usr$
Compose a single-line photo search query for a Scottish recipe making process image (one step of preparation).

Recipe: [data:title]
Recipe Method Step: [data:method_step]
Ingredients: [data:ingredients]

Requirements:
- Show one step of the recipe preparation or cooking process
- Authentic, hands-on, home-cooked aesthetic
- Hands working, traditional techniques, in-process cooking
- Warm, natural lighting, lived-in spaces
- NOT stock photography or sterile food photography

Output
Respond ONLY with the final search query text (no quotes, no markdown). Use comma-separated keywords/phrases.
Focus on authentic, warm, traditional Scottish home cooking process imagery.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Making process image search query for photo-harvesting',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Making process image search query for photo-harvesting',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

