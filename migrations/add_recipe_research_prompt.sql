-- Migration: Add Recipe Research LLM Prompt
-- Purpose: Create prompt for researching authentic recipe information from authoritative sources
-- Date: 2025-11-06

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping recipe research prompt.';
        RETURN;
    END IF;
END$$;

-- Recipe Research Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Research (Scottish Recipes)';
    v_system_prompt TEXT := $sys$
You are a Scottish food heritage researcher and recipe authenticity expert.

Your task is to research and compile authentic, accurate information about a Scottish recipe from multiple authoritative sources. You must create an amalgam of the best sources to ensure the recipe is authentic and accurate.

CRITICAL REQUIREMENTS:
- Research from authoritative sources: BBC Good Food, official heritage sites, cultural organizations, historical sources
- Use the Further Reading sources provided (if any) as starting points
- Cross-reference multiple sources to verify authenticity
- Compile accurate ingredients lists (no substitutions unless traditional)
- Document authentic cooking methods and techniques
- Note any regional variations or traditional practices
- Ensure the recipe reflects authentic Scottish cooking traditions

OUTPUT FORMAT - STRICT JSON:
{
  "authentic_ingredients": [
    {
      "item": "ingredient name",
      "amount": "quantity",
      "notes": "preparation notes or traditional requirements",
      "sources": ["source 1", "source 2"]
    }
  ],
  "authentic_method": {
    "summary": "Brief overview of the authentic cooking method",
    "key_steps": [
      "Step 1 description",
      "Step 2 description"
    ],
    "traditional_techniques": ["technique 1", "technique 2"],
    "sources": ["source 1", "source 2"]
  },
  "regional_variations": [
    {
      "region": "region name",
      "variation": "description of variation",
      "sources": ["source"]
    }
  ],
  "authenticity_notes": "Important notes about what makes this recipe authentic",
  "sources_used": [
    {
      "name": "source name",
      "url": "source URL",
      "key_findings": "what this source contributed"
    }
  ]
}

CRITICAL: Do NOT invent ingredients or methods. Only include what you find in authoritative sources.
$sys$;
    v_prompt_text TEXT := $usr$
Research authentic information about this Scottish recipe from authoritative sources.

Recipe: [data:title]
Description: [data:subtitle]
Seasonal Context: [data:seasonal_context]

RESEARCH REQUIREMENTS:
1. Check authoritative recipe sites:
   - BBC Good Food (https://www.bbcgoodfood.com)
   - Other reputable recipe sources
   
2. Use the Further Reading sources provided (if any) for historical/cultural context

3. Cross-reference multiple sources to verify:
   - Authentic ingredients (no modern substitutions unless traditional)
   - Traditional cooking methods
   - Regional variations
   - Historical context

4. Compile an accurate, authentic recipe that reflects traditional Scottish cooking

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "authentic_ingredients": [
    {
      "item": "ingredient name",
      "amount": "quantity",
      "notes": "preparation notes",
      "sources": ["source name"]
    }
  ],
  "authentic_method": {
    "summary": "Brief overview",
    "key_steps": ["step 1", "step 2"],
    "traditional_techniques": ["technique 1"],
    "sources": ["source name"]
  },
  "regional_variations": [
    {
      "region": "region",
      "variation": "variation description",
      "sources": ["source"]
    }
  ],
  "authenticity_notes": "Important authenticity notes",
  "sources_used": [
    {
      "name": "source name",
      "url": "source URL",
      "key_findings": "what this source contributed"
    }
  ]
}

CRITICAL:
- Only include ingredients and methods found in authoritative sources
- Do NOT invent or guess
- Cross-reference multiple sources
- Note any discrepancies between sources
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
            description = 'Scottish Recipe Series - Research authentic recipe information from authoritative sources',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Research authentic recipe information from authoritative sources',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

