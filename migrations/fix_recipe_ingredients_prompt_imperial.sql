-- Fix Recipe Ingredients Prompt to prevent duplicate metric/imperial values
-- Purpose: Update prompt to ensure imperial values are properly converted, not duplicated

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
- IMPORTANT: amount_imperial must be a proper imperial conversion (oz, lb, fl oz, cups, etc.), NOT the same as metric
- DO NOT include "(approx.)" or "approx" in any values
- DO NOT use metric values (g, ml, kg, l) for amount_imperial
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
      "amount_metric": "500g",
      "amount_imperial": "18oz",
      "notes": "optional preparation notes"
    }
  ]
}

REQUIREMENTS:
- List ingredients in WEIGHT ORDER (heaviest first)
- Convert all weights to grams for sorting
- amount_metric: Use metric units (g, kg, ml, l)
- amount_imperial: Use imperial units (oz, lb, fl oz, cups, pt) - MUST be different from metric
- Convert properly: 500g = ~18oz, 300ml = ~10fl oz, etc.
- DO NOT use the same value for both metric and imperial
- DO NOT include "(approx.)" or "approx" in any field
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
            'Scottish Recipe Series - Ingredients list formatting',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

