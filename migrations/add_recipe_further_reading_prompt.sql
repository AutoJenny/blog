-- Migration: Add LLM Prompt for Recipe Further Reading Section
-- Purpose: Create prompt template for generating further reading sources
-- Date: 2025-11-06

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping recipe further reading prompt.';
        RETURN;
    END IF;
END$$;

-- Recipe Further Reading Prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Further Reading';
    v_system_prompt TEXT := $sys$
You are a Scottish food heritage researcher specializing in finding authoritative sources for background information about Scottish recipes.

Your task is to search for and identify 2-5 authoritative sources that provide background information about the recipe. These sources should support the recipe's Background, Ingredients, Variations, and Serving Suggestions sections.

SOURCE CRITERIA:
- Focus on: cultural/heritage sites, Wikipedia articles, historical sources, ingredient provenance sites, tourism/heritage organizations
- AVOID: competing recipe sites or cooking blogs
- Prioritize: official heritage organizations, cultural sites, tourism boards, historical archives, ingredient-specific provenance information

OUTPUT FORMAT:
For each source, provide:
1. Title & Link (full URL)
2. Why It's Good (brief explanation of the source's value and authority)
3. Use Case in Your Content (how to reference this source in the recipe sections above)

Format as a numbered list with clear headings for each section.
$sys$;
    v_prompt_text TEXT := $usr$
Search for 2-5 authoritative sources for background information about this Scottish recipe.

Recipe: [data:title]
Description: [data:subtitle]
Seasonal Context: [data:seasonal_context]

FOCUS ON:
- Cultural/heritage sites (e.g., National Trust for Scotland, local heritage organizations)
- Wikipedia articles (for overview and etymology)
- Historical sources and archives
- Ingredient provenance sites (for key ingredients like smoked haddock, oats, etc.)
- Tourism/heritage organizations (e.g., VisitScotland, Discover Scotland)

AVOID:
- Competing recipe sites (e.g., BBC Food, AllRecipes, etc.)
- Cooking blogs or personal recipe sites
- Commercial food sites focused on recipes

FOR EACH SOURCE, PROVIDE:
1. Title & Link (full URL)
2. Why It's Good (brief explanation of the source's value - e.g., "Provides broad overview of origin in the town of Cullen, ingredients, etymology")
3. Use Case in Your Content (how to reference this source in other recipe sections - e.g., "Use in the Background section as a general background link when mentioning the place of origin")

OUTPUT FORMAT:
Format as a numbered list (1-5) with three subsections for each source:
- Title & Link
- Why It's Good
- Use Case in Your Content

Example format:
1. "Recipe Name" — Source Name
   Title & Link: [full URL]
   Why It's Good: [brief explanation]
   Use Case in Your Content: [how to use in recipe sections]
$usr$;
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            prompt_text = v_prompt_text,
            description = 'Scottish Recipe Series - Further Reading sources',
            updated_at = NOW()
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, description, prompt_text, system_prompt, system_prompt_template, created_at, updated_at)
        VALUES (
            v_name,
            'Scottish Recipe Series - Further Reading sources',
            v_prompt_text,
            v_system_prompt,
            v_system_prompt,
            NOW(), NOW()
        );
    END IF;
END$$;

