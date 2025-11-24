-- Migration: Update all section content generation prompts to explicitly forbid H2 headings
-- Purpose: Prevent LLMs from generating H2 headings in section content
-- Date: 2025-01-XX

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping prompt updates.';
        RETURN;
    END IF;
END$$;

-- Update Section Drafting prompt
DO $$
DECLARE
    v_name TEXT := 'Section Drafting';
    v_h2_instruction TEXT := '

CRITICAL OUTPUT REQUIREMENT:
- Do NOT include any H2 headings (<h2> tags) in your output. The section heading is managed separately and will be added automatically.
- Only use paragraph tags (<p>) and other appropriate HTML elements (e.g., <ul>, <ol>, <li>, <strong>, <em>).
- Never include section titles or headings in your content - they are handled separately.';
BEGIN
    UPDATE llm_prompt
    SET prompt_text = prompt_text || v_h2_instruction,
        updated_at = NOW()
    WHERE name = v_name
      AND (prompt_text NOT LIKE '%Do NOT include any H2 headings%' 
           AND prompt_text NOT LIKE '%<h2> tags%');
    
    IF FOUND THEN
        RAISE NOTICE 'Updated Section Drafting prompt to forbid H2 headings';
    ELSE
        RAISE NOTICE 'Section Drafting prompt already updated or not found';
    END IF;
END $$;

-- Update Recipe Background prompt
DO $$
DECLARE
    v_name TEXT := 'Recipe Background (Scottish Recipes)';
    v_h2_instruction TEXT := '

CRITICAL OUTPUT REQUIREMENT:
- Do NOT include any H2 headings (<h2> tags) in your output. The section heading is managed separately.
- Only use paragraph tags (<p>) for your content.
- Never include section titles or headings in your content.';
BEGIN
    UPDATE llm_prompt
    SET prompt_text = prompt_text || v_h2_instruction,
        updated_at = NOW()
    WHERE name = v_name
      AND (prompt_text NOT LIKE '%Do NOT include any H2 headings%' 
           AND prompt_text NOT LIKE '%<h2> tags%');
    
    IF FOUND THEN
        RAISE NOTICE 'Updated Recipe Background prompt to forbid H2 headings';
    ELSE
        RAISE NOTICE 'Recipe Background prompt already updated or not found';
    END IF;
END $$;

-- Update all other recipe prompts (they should already be generating JSON, but add defensive instruction)
DO $$
DECLARE
    v_prompt_names TEXT[] := ARRAY[
        'Recipe Ingredients (Scottish Recipes)',
        'Recipe Method (Scottish Recipes)',
        'Recipe Variants (Scottish Recipes)',
        'Recipe Serving Suggestions (Scottish Recipes)',
        'Recipe Further Reading (Scottish Recipes)',
        'Recipe Ingredients',
        'Recipe Method',
        'Recipe Variants',
        'Recipe Serving Suggestions',
        'Recipe Further Reading'
    ];
    v_h2_instruction TEXT := '

CRITICAL OUTPUT REQUIREMENT:
- Do NOT include any H2 headings (<h2> tags) in your output. The section heading is managed separately.
- Return ONLY valid JSON as specified.';
    v_prompt_name TEXT;
BEGIN
    FOREACH v_prompt_name IN ARRAY v_prompt_names
    LOOP
        UPDATE llm_prompt
        SET prompt_text = prompt_text || v_h2_instruction,
            updated_at = NOW()
        WHERE name = v_prompt_name
          AND (prompt_text NOT LIKE '%Do NOT include any H2 headings%' 
               AND prompt_text NOT LIKE '%<h2> tags%');
        
        IF FOUND THEN
            RAISE NOTICE 'Updated % prompt to forbid H2 headings', v_prompt_name;
        END IF;
    END LOOP;
END $$;

-- Update Author First Drafts prompt if it exists
DO $$
DECLARE
    v_name TEXT := 'Author First Drafts';
    v_h2_instruction TEXT := '

CRITICAL OUTPUT REQUIREMENT:
- Do NOT include any H2 headings (<h2> tags) in your output. The section heading is managed separately and will be added automatically.
- Only use paragraph tags (<p>) and other appropriate HTML elements.
- Never include section titles or headings in your content.';
BEGIN
    UPDATE llm_prompt
    SET prompt_text = prompt_text || v_h2_instruction,
        updated_at = NOW()
    WHERE name = v_name
      AND (prompt_text NOT LIKE '%Do NOT include any H2 headings%' 
           AND prompt_text NOT LIKE '%<h2> tags%');
    
    IF FOUND THEN
        RAISE NOTICE 'Updated Author First Drafts prompt to forbid H2 headings';
    ELSE
        RAISE NOTICE 'Author First Drafts prompt not found or already updated';
    END IF;
END $$;









