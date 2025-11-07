-- Migration: Add UK-British English spelling guidance to all recipe prompts
-- Purpose: Ensure all recipe content uses UK-British English spellings, not US-English
-- Date: 2025-11-XX

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping UK English guidance updates.';
        RETURN;
    END IF;
END$$;

-- UK English guidance text to add to all recipe prompts
-- This will be appended to system_prompt for all recipe-related prompts
DO $$
DECLARE
    uk_english_guidance TEXT := $guidance$

CRITICAL: LANGUAGE REQUIREMENTS - UK-BRITISH ENGLISH ONLY
You MUST use UK-British English spellings throughout. NEVER use US-English spellings.

Common examples (UK-British → US-English - DO NOT USE US VERSIONS):
- flavour → flavor (WRONG - use "flavour")
- colour → color (WRONG - use "colour")
- organise → organize (WRONG - use "organise")
- centre → center (WRONG - use "centre")
- realise → realize (WRONG - use "realise")
- optimise → optimize (WRONG - use "optimise")
- analyse → analyze (WRONG - use "analyse")
- defence → defense (WRONG - use "defence")
- licence (noun) → license (WRONG - use "licence" for noun, "license" for verb)
- programme → program (WRONG - use "programme" for schedule/show, "program" only for computer software)
- traveller → traveler (WRONG - use "traveller")
- jewellery → jewelry (WRONG - use "jewellery")
- grey → gray (WRONG - use "grey")
- pyjamas → pajamas (WRONG - use "pyjamas")
- yoghurt → yogurt (WRONG - use "yoghurt")
- doughnut → donut (WRONG - use "doughnut")
- cosy → cozy (WRONG - use "cosy")
- skilful → skillful (WRONG - use "skilful")
- fulfil → fulfill (WRONG - use "fulfil")
- enrol → enroll (WRONG - use "enrol")
- instal → install (WRONG - use "instal")
- distil → distill (WRONG - use "distil")
- marvellous → marvelous (WRONG - use "marvellous")
- cancelled → canceled (WRONG - use "cancelled")
- labelled → labeled (WRONG - use "labelled")
- travelled → traveled (WRONG - use "travelled")
- modelling → modeling (WRONG - use "modelling")
- fuelled → fueled (WRONG - use "fuelled")
- woollen → woolen (WRONG - use "woollen")
- moustache → mustache (WRONG - use "moustache")
- manoeuvre → maneuver (WRONG - use "manoeuvre")
- oesophagus → esophagus (WRONG - use "oesophagus")
- paediatric → pediatric (WRONG - use "paediatric")
- aesthetic → esthetic (WRONG - use "aesthetic")
- mediaeval → medieval (WRONG - use "mediaeval" or "medieval" - both acceptable in UK)
- storey (building level) → story (WRONG - use "storey" for building, "story" for narrative)

This is a Scottish recipe blog - UK-British English is essential for authenticity and audience expectations.
Review every word carefully and ensure NO US-English spellings are used.
$guidance$;

BEGIN
    -- Update all recipe-related prompts
    UPDATE llm_prompt
    SET system_prompt = system_prompt || E'\n\n' || uk_english_guidance,
        system_prompt_template = system_prompt_template || E'\n\n' || uk_english_guidance,
        updated_at = NOW()
    WHERE name IN (
        'Recipe Background (Scottish Recipes)',
        'Recipe Ingredients (Scottish Recipes)',
        'Recipe Method',
        'Recipe Method (Scottish Recipes)',
        'Recipe Variants',
        'Recipe Serving Suggestions',
        'Recipe Further Reading',
        'Recipe Research (Scottish Recipes)',
        'Recipe Image Style & Prompts (Scottish Recipes)',
        'Recipe Hero Image Generation (Scottish Recipes)',
        'Recipe Making Process Image Generation (Scottish Recipes)'
    )
    AND (system_prompt NOT LIKE '%UK-British English%' OR system_prompt_template NOT LIKE '%UK-British English%');
    
    RAISE NOTICE 'Updated recipe prompts with UK-British English guidance.';
END $$;

