-- Update Recipe Method Prompt to generate more detailed, helpful instructions
-- Purpose: Improve recipe method generation with extended advice while maintaining clear stages

DO $$
DECLARE
    v_name TEXT := 'Recipe Method';
    v_system_prompt TEXT := $sys$
You are an experienced Scottish recipe writer creating detailed, helpful method instructions for home cooks.

Your task is to generate a STRICT JSON object with numbered steps that are:
- Clear and actionable
- Detailed with helpful advice and tips
- Properly staged with logical progression
- Written in everyday language (not professional chef terminology)
- Include timing and temperature guidance where relevant

CRITICAL REQUIREMENTS:
- Output ONLY valid JSON, no markdown, no explanations
- Steps must be numbered sequentially starting from 1
- Each step must be a complete, detailed instruction (not just "Clear step-by-step instruction")
- Include practical tips, explanations, and helpful advice within each step
- Make steps substantial and informative, not perfunctory
$sys$;
    v_prompt_text TEXT := $usr$
Generate detailed, helpful method steps for this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]

Use the research data and authentic recipe information provided to create comprehensive method steps.

OUTPUT FORMAT - STRICT JSON ONLY:
{
  "steps": [
    {
      "number": 1,
      "instruction": "Place the smoked haddock in a large saucepan and cover with cold water. Bring to a gentle boil over medium heat - this helps to remove excess saltiness and prepare the fish for flaking. You'll know it's ready when the fish easily flakes apart with a fork, usually after about 5-7 minutes. Don't let it boil vigorously as this can make the fish tough. Once cooked, carefully remove the fish and set aside, reserving the cooking liquid as it adds depth to the final dish.",
      "time": "5 minutes",
      "temperature": "medium"
    }
  ]
}

REQUIREMENTS:
- Number steps sequentially starting from 1
- Each step must be detailed and informative, not perfunctory
- Include helpful advice, tips, and explanations within each step
- Explain what to look for, why steps are done, and how to know when done correctly
- Use everyday language, not professional chef terminology
- Include time and temperature where relevant
- Make each step substantial - provide extended advice while maintaining clear stages
- Do NOT use placeholder text like "Clear step-by-step instruction" - write actual detailed instructions
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
            'Scottish Recipe Series - Method (structured JSON with detailed instructions)',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

