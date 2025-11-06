-- Migration: Update recipe prompts to generate structured JSON
-- Purpose: Ensure recipe sections generate strict JSON formats
-- Date: 2025-11-06

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping recipe prompt updates.';
        RETURN;
    END IF;
END$$;

-- Update Recipe Ingredients Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Ingredients (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are a recipe writer creating a structured ingredients list for a Scottish recipe.

Your task is to generate a STRICT JSON object with ingredients listed in WEIGHT ORDER (heaviest first).

CRITICAL REQUIREMENTS:
- Output ONLY valid JSON, no markdown, no explanations
- Ingredients must be sorted by weight (heaviest first)
- Convert all weights to grams for sorting
- Include both imperial and metric measurements
- Each ingredient must have: item, amount_imperial, amount_metric, notes (optional)
$sys$;
    v_prompt_text TEXT := $usr$
Generate a structured ingredients list for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "serves": 4,
  "prep_time": "15 minutes",
  "cook_time": "30 minutes",
  "ingredients": [
    {
      "item": "ingredient name",
      "amount_imperial": "500g",
      "amount_metric": "500g",
      "notes": "optional preparation notes"
    }
  ]
}

REQUIREMENTS:
- List ingredients in WEIGHT ORDER (heaviest first)
- Convert all weights to grams for sorting
- Include both imperial and metric (use same value if metric)
- If no weight, use alphabetical order
- Output ONLY the JSON object, no other text
$usr$;
BEGIN
    UPDATE llm_prompt SET
        system_prompt = v_system_prompt,
        system_prompt_template = v_system_prompt,
        prompt_text = v_prompt_text,
        updated_at = NOW()
    WHERE name = v_name;
    
    IF NOT FOUND THEN
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Ingredients (structured JSON)',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

-- Update Recipe Method Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Method';
    v_system_prompt TEXT := $sys$
You are a recipe writer creating structured method steps for a Scottish recipe.

Your task is to generate a STRICT JSON object with numbered steps.

CRITICAL REQUIREMENTS:
- Output ONLY valid JSON, no markdown, no explanations
- Steps must be numbered sequentially
- Each step must have: number, instruction, time (optional), temperature (optional)
$sys$;
    v_prompt_text TEXT := $usr$
Generate structured method steps for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "steps": [
    {
      "number": 1,
      "instruction": "Clear step-by-step instruction",
      "time": "5 minutes",
      "temperature": "medium"
    }
  ]
}

REQUIREMENTS:
- Number steps sequentially starting from 1
- Each step must be clear and actionable
- Include time and temperature where relevant
- Output ONLY the JSON object, no other text
$usr$;
BEGIN
    UPDATE llm_prompt SET
        system_prompt = v_system_prompt,
        system_prompt_template = v_system_prompt,
        prompt_text = v_prompt_text,
        updated_at = NOW()
    WHERE name = v_name;
    
    IF NOT FOUND THEN
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Method (structured JSON)',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

-- Update Recipe Variants Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Variants';
    v_system_prompt TEXT := $sys$
You are a recipe writer creating structured recipe variations.

Your task is to generate a STRICT JSON object with variations.

CRITICAL REQUIREMENTS:
- Output ONLY valid JSON, no markdown, no explanations
- Each variant must have: name, description, changes (array)
$sys$;
    v_prompt_text TEXT := $usr$
Generate structured variations for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "variants": [
    {
      "name": "Variant Name",
      "description": "Brief description of the variation",
      "changes": [
        "Specific change 1",
        "Specific change 2"
      ]
    }
  ]
}

REQUIREMENTS:
- Include 1-2 variations if applicable
- Each variation should be distinct and meaningful
- Changes should be specific and actionable
- Output ONLY the JSON object, no other text
- If no variations are appropriate, return {"variants": []}
$usr$;
BEGIN
    UPDATE llm_prompt SET
        system_prompt = v_system_prompt,
        system_prompt_template = v_system_prompt,
        prompt_text = v_prompt_text,
        updated_at = NOW()
    WHERE name = v_name;
    
    IF NOT FOUND THEN
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Variants (structured JSON)',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

-- Update Recipe Serving Suggestions Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Serving Suggestions';
    v_system_prompt TEXT := $sys$
You are a recipe writer creating structured serving suggestions for a Scottish recipe.

Your task is to generate a STRICT JSON object with serving information.

CRITICAL REQUIREMENTS:
- Output ONLY valid JSON, no markdown, no explanations
- Include traditional serving suggestions and accompaniments
$sys$;
    v_prompt_text TEXT := $usr$
Generate structured serving suggestions for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "serving_suggestions": [
    {
      "type": "traditional",
      "description": "How Scots traditionally serve this dish",
      "accompaniments": [
        "Item 1",
        "Item 2"
      ]
    },
    {
      "type": "drinks",
      "description": "Recommended drinks",
      "accompaniments": [
        "Drink 1",
        "Drink 2"
      ]
    }
  ],
}

REQUIREMENTS:
- Include traditional serving methods
- Include drink pairings if appropriate
- Output ONLY the JSON object, no other text
$usr$;
BEGIN
    UPDATE llm_prompt SET
        system_prompt = v_system_prompt,
        system_prompt_template = v_system_prompt,
        prompt_text = v_prompt_text,
        updated_at = NOW()
    WHERE name = v_name;
    
    IF NOT FOUND THEN
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Serving Suggestions (structured JSON)',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

-- Update Recipe Further Reading Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Further Reading';
    v_system_prompt TEXT := $sys$
You are a Scottish food heritage researcher specializing in finding authoritative sources.

Your task is to generate a STRICT JSON object with sources.

CRITICAL REQUIREMENTS:
- Output ONLY valid JSON, no markdown, no explanations
- Each source must have: title, url, why_good, use_case
$sys$;
    v_prompt_text TEXT := $usr$
Search for 2-5 authoritative sources for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "sources": [
    {
      "title": "Source Title",
      "url": "https://example.com/page",
      "why_good": "Brief explanation of the source's value",
      "use_case": "How to reference this source in recipe sections"
    }
  ]
}

REQUIREMENTS:
- Focus on: cultural/heritage sites, Wikipedia, historical sources, ingredient provenance sites, tourism/heritage organizations
- AVOID: competing recipe sites or cooking blogs
- Include 2-5 sources
- Output ONLY the JSON object, no other text
$usr$;
BEGIN
    UPDATE llm_prompt SET
        system_prompt = v_system_prompt,
        system_prompt_template = v_system_prompt,
        prompt_text = v_prompt_text,
        updated_at = NOW()
    WHERE name = v_name;
    
    IF NOT FOUND THEN
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Further Reading (structured JSON)',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

