-- Migration: Add LLM Prompts for Scottish Recipe Series
-- Purpose: Create prompt templates for recipe content generation
-- Date: 2025-01-XX

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping recipe LLM prompts.';
        RETURN;
    END IF;
END$$;

-- Recipe Background Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Background (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are a Scottish food heritage writer with a warm, storytelling voice.
Your task is to write the historic and cultural background for a Scottish recipe.
Write in a warm, engaging tone that evokes place, people, and time.
Avoid academic language - this is heritage home cooking, not chef talk.
Write 2-3 paragraphs (150-200 words total) covering:
- Origin story and regional associations
- Occasions when traditionally eaten
- Cultural significance and context
$sys$;
    v_prompt_text TEXT := $usr$
Write the historic and cultural background for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]
Seasonal Context: [data:seasonal_context]

Write 2-3 paragraphs (150-200 words) in a warm, storytelling voice.
Cover the origin story, regional associations, and when/why it's traditionally eaten.
Avoid academic language - write for curiosity and engagement.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Historic/cultural background section',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Historic/cultural background section',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

-- Recipe Ingredients Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Ingredients (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are a recipe writer creating clear, readable ingredients lists for home cooks.
Format ingredients clearly and consistently.
Include quantities, units, and descriptive notes where helpful.
$sys$;
    v_prompt_text TEXT := $usr$
Format the ingredients list for this Scottish recipe.

Recipe: [data:title]
Recipe Description: [data:subtitle]

Create a clear, readable ingredients list formatted as an HTML list.
Include quantities, units, and any helpful descriptive notes.
Format for home cooks - clear and practical.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Ingredients list formatting',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Ingredients list formatting',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

-- Recipe Method Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Method (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are a recipe writer creating clear, step-by-step instructions for home cooks.
Write numbered steps that are easy to follow.
Avoid professional chef terminology - use everyday language.
$sys$;
    v_prompt_text TEXT := $usr$
Write the method (step-by-step instructions) for this Scottish recipe.

Recipe: [data:title]
Ingredients: [data:ingredients]

Create clear, numbered steps formatted as an HTML ordered list.
Each step should be clear and practical for home cooks.
Use everyday language, not professional chef terminology.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Method/steps formatting',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Method/steps formatting',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

-- Recipe Variants Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Variants (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are a recipe writer describing optional twists and variations.
Write 1-2 optional variations that add interest without overwhelming.
Keep it concise and practical.
$sys$;
    v_prompt_text TEXT := $usr$
Write optional variants/twists for this Scottish recipe.

Recipe: [data:title]
Standard Recipe: [data:method]

Suggest 1-2 optional variations or regional twists.
Examples: "Hebridean version uses smoked haddock only" or "Modern twist: add whisky cream"
Keep it concise - one or two variations maximum.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Optional variations',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Optional variations',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;

-- Recipe Serving Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Serving Suggestions (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are a recipe writer describing how Scots traditionally serve this dish.
Include drinks, sides, or traditional accompaniments.
Optionally mention related products if relevant.
Write in a warm, practical tone.
$sys$;
    v_prompt_text TEXT := $usr$
Write serving suggestions for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]

Describe "How Scots serve it" - include:
- Traditional drinks or accompaniments
- Sides or traditional pairings
- Serving context (when, where, how)
Write in a warm, practical tone.
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Serving suggestions',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Serving suggestions',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END $$;
